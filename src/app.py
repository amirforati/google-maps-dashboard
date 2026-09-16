from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from data import (
    combine_reviews,
    load_manual_reviews,
    load_takeout_file,
    parse_takeout_reviews,
    save_manual_review,
)

st.set_page_config(page_title="My Google Maps Reviews", page_icon="🗺️", layout="wide")

RAW_REVIEWS = Path("data/raw/Reviews.json")
CARTO_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"


@st.cache_data(show_spinner=False)
def load_takeout_cached(path_string: str):
    return load_takeout_file(Path(path_string))


def get_data():
    takeout = load_takeout_cached(str(RAW_REVIEWS)) if RAW_REVIEWS.exists() else pd.DataFrame()
    manual = load_manual_reviews()
    return combine_reviews(takeout, manual)


def save_uploaded_reviews(uploaded_file):
    RAW_REVIEWS.parent.mkdir(parents=True, exist_ok=True)
    RAW_REVIEWS.write_bytes(uploaded_file.getvalue())
    load_takeout_cached.clear()


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    st.sidebar.header("Filters")

    if filtered.empty:
        return filtered

    rating_options = [5, 4, 3, 2, 1]
    selected_ratings = st.sidebar.multiselect(
        "My rating",
        rating_options,
        default=rating_options,
        format_func=lambda x: f"{x} ★",
        help="Select only 5 ★ here to show five-star reviews on every page.",
    )
    if selected_ratings:
        filtered = filtered[filtered["rating"].isin(selected_ratings)]
    else:
        filtered = filtered.iloc[0:0]

    states = sorted([x for x in filtered["state"].dropna().unique() if x])
    selected_states = st.sidebar.multiselect("State", states)
    if selected_states:
        filtered = filtered[filtered["state"].isin(selected_states)]

    cities = sorted([x for x in filtered["city"].dropna().unique() if x])
    selected_cities = st.sidebar.multiselect("City", cities)
    if selected_cities:
        filtered = filtered[filtered["city"].isin(selected_cities)]

    place_categories = sorted([x for x in filtered["category"].dropna().unique() if x])
    selected_categories = st.sidebar.multiselect("Place category", place_categories)
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]

    cuisines = sorted([x for x in filtered["cuisine"].dropna().unique() if x])
    selected_cuisines = st.sidebar.multiselect("Cuisine / type", cuisines)
    if selected_cuisines:
        filtered = filtered[filtered["cuisine"].isin(selected_cuisines)]

    written_only = st.sidebar.checkbox("Written reviews only")
    if written_only:
        filtered = filtered[filtered["has_written_review"]]

    years = sorted([int(x) for x in filtered["year"].dropna().unique()])
    selected_years = st.sidebar.multiselect("Year", years)
    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]

    search = st.sidebar.text_input("Search place or review")
    if search.strip():
        q = search.strip().lower()
        mask = (
            filtered["place_name"].str.lower().str.contains(q, na=False)
            | filtered["review_text"].str.lower().str.contains(q, na=False)
            | filtered["address"].str.lower().str.contains(q, na=False)
            | filtered["cuisine"].str.lower().str.contains(q, na=False)
        )
        filtered = filtered[mask]

    return filtered


def metrics(df: pd.DataFrame):
    cols = st.columns(5)
    cols[0].metric("Reviews", f"{len(df):,}")
    cols[1].metric("Average rating", f"{df['rating'].mean():.2f}" if len(df) else "—")
    cols[2].metric("5-star", f"{(df['rating'].eq(5).mean() * 100):.0f}%" if len(df) else "—")
    cols[3].metric("States", int(df["state"].replace("", pd.NA).nunique()))
    cols[4].metric("Cities", int(df["city"].replace("", pd.NA).nunique()))


def add_review_form():
    with st.expander("➕ Add review manually", expanded=False):
        st.caption("Manual reviews are kept separate from Google Takeout and appear in the same dashboard.")
        with st.form("manual_review", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            place_name = c1.text_input("Restaurant / place name *")
            rating = c2.selectbox("Rating *", [5, 4, 3, 2, 1])
            review_date = c3.date_input("Visit / review date *", value=date.today())

            review_text = st.text_area("Your review", height=130)

            c4, c5 = st.columns(2)
            category = c4.selectbox(
                "Category",
                ["Restaurant / Food", "Attraction", "Shopping", "Hotel", "Service", "Healthcare", "Other"],
            )
            cuisine = c5.text_input("Cuisine / type", placeholder="Persian, Pizza, Italian, Burger, Coffee …")

            address = st.text_input("Address *")
            c6, c7, c8 = st.columns(3)
            city = c6.text_input("City")
            state = c7.text_input("State", max_chars=2)
            country = c8.text_input("Country code", value="US", max_chars=2)

            c9, c10 = st.columns(2)
            latitude = c9.number_input("Latitude *", value=None, format="%.7f")
            longitude = c10.number_input("Longitude *", value=None, format="%.7f")
            google_maps_url = st.text_input("Google Maps URL", placeholder="Optional")

            submitted = st.form_submit_button("Save review", type="primary")
            if submitted:
                if not place_name.strip() or not address.strip() or latitude is None or longitude is None:
                    st.error("Place name, address, latitude, and longitude are required for now.")
                else:
                    save_manual_review(
                        {
                            "source": "manual",
                            "place_name": place_name.strip(),
                            "rating": rating,
                            "review_text": review_text.strip(),
                            "review_date": review_date.isoformat(),
                            "address": address.strip(),
                            "city": city.strip(),
                            "state": state.strip().upper(),
                            "country": country.strip().upper(),
                            "latitude": latitude,
                            "longitude": longitude,
                            "google_maps_url": google_maps_url.strip(),
                            "category": category,
                            "cuisine": cuisine.strip() or "Other / Unclassified",
                        }
                    )
                    st.success("Review saved.")
                    st.cache_data.clear()
                    st.rerun()


def explorer_page(df: pd.DataFrame):
    st.subheader("🗺️ Explorer")
    metrics(df)

    if df.empty:
        st.info("No reviews match the current filters.")
        return

    map_df = df.dropna(subset=["latitude", "longitude"]).copy()
    map_df["rating_label"] = map_df["rating"].astype(int).astype(str) + " ★"
    map_df["row_id"] = map_df.index.astype(str)

    fig = px.scatter_map(
        map_df,
        lat="latitude",
        lon="longitude",
        color="rating_label",
        hover_name="place_name",
        hover_data={
            "rating_label": True,
            "cuisine": True,
            "city": True,
            "state": True,
            "latitude": False,
            "longitude": False,
        },
        custom_data=["row_id"],
        zoom=3,
        height=610,
        category_orders={"rating_label": ["5 ★", "4 ★", "3 ★", "2 ★", "1 ★"]},
    )
    fig.update_layout(
        map_style="carto-positron",
        margin=dict(l=0, r=0, t=10, b=0),
        legend_title_text="My rating",
        dragmode="lasso",
    )

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key="review_map",
        on_select="rerun",
        selection_mode=("points", "box", "lasso"),
    )

    selected = df
    selected_points = getattr(event, "selection", {}).get("points", []) if event is not None else []
    if selected_points:
        row_ids = []
        for point in selected_points:
            customdata = point.get("customdata")
            if isinstance(customdata, (list, tuple)) and customdata:
                row_ids.append(str(customdata[0]))
        if row_ids:
            selected = df[df.index.astype(str).isin(row_ids)]

    st.markdown(
        f"**Showing {len(selected):,} review(s)**"
        + (" from the map selection" if len(selected) != len(df) else "")
    )

    display = selected[
        ["place_name", "rating", "cuisine", "city", "state", "review_date", "review_text", "google_maps_url"]
    ].copy()
    display["review_date"] = display["review_date"].dt.date
    display = display.rename(
        columns={
            "place_name": "Place",
            "rating": "My rating",
            "cuisine": "Cuisine / type",
            "city": "City",
            "state": "State",
            "review_date": "Date",
            "review_text": "Review",
            "google_maps_url": "Google Maps",
        }
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "My rating": st.column_config.NumberColumn(format="%d ★"),
            "Google Maps": st.column_config.LinkColumn(display_text="Open"),
            "Review": st.column_config.TextColumn(width="large"),
        },
    )

    if len(selected) == 1:
        row = selected.iloc[0]
        st.markdown(f"### {row['place_name']}")
        st.markdown("★" * int(row["rating"]) + "☆" * (5 - int(row["rating"])))
        st.caption(
            " · ".join(
                x for x in [row.get("cuisine", ""), row.get("city", ""), row.get("state", "")] if x
            )
        )
        if row.get("review_text"):
            st.write(row["review_text"])
        if row.get("google_maps_url"):
            st.link_button("Open in Google Maps", row["google_maps_url"])


def heatmap_page(df: pd.DataFrame):
    st.subheader("🔥 Heatmap")
    metrics(df)

    geo = df.dropna(subset=["latitude", "longitude"]).copy()
    if geo.empty:
        st.info("No mapped reviews match the current filters.")
        return

    mode = st.radio(
        "Heatmap mode",
        ["Review density", "Rating weighted", "5-star density", "Low-rating density"],
        horizontal=True,
        help="Rating weighted now strongly emphasizes 5-star reviews instead of using a nearly linear 1–5 weight.",
    )
    radius = st.slider("Heat radius", 15, 80, 35, 5)

    heat = geo[["latitude", "longitude", "rating"]].copy()

    if mode == "Review density":
        heat["weight"] = 1.0
    elif mode == "Rating weighted":
        # Non-linear weights make high-rated clusters visibly different from simple review density.
        rating_weights = {1: 0.01, 2: 0.03, 3: 0.08, 4: 0.25, 5: 1.00}
        heat["weight"] = heat["rating"].map(rating_weights).fillna(0.01)
    elif mode == "5-star density":
        heat = heat[heat["rating"].eq(5)].copy()
        heat["weight"] = 1.0
    else:
        heat = heat[heat["rating"].le(3)].copy()
        low_weights = {1: 1.00, 2: 0.65, 3: 0.35}
        heat["weight"] = heat["rating"].map(low_weights).fillna(0.35)

    if heat.empty:
        st.info("No reviews are available for this heatmap mode after the current filters.")
        return

    layer = pdk.Layer(
        "HeatmapLayer",
        data=heat,
        get_position="[longitude, latitude]",
        get_weight="weight",
        radius_pixels=radius,
        intensity=1.2,
        threshold=0.02,
    )
    view_state = pdk.ViewState(
        latitude=float(heat["latitude"].mean()),
        longitude=float(heat["longitude"].mean()),
        zoom=3,
    )
    st.pydeck_chart(
        pdk.Deck(layers=[layer], initial_view_state=view_state, map_style=CARTO_STYLE),
        use_container_width=True,
    )

    by_state = (
        df[df["state"].ne("")]
        .groupby("state")
        .agg(reviews=("place_name", "size"), average_rating=("rating", "mean"))
        .sort_values("reviews", ascending=False)
        .reset_index()
    )
    st.dataframe(by_state, use_container_width=True, hide_index=True)


def categories_page(df: pd.DataFrame):
    st.subheader("🍽️ Categories")
    st.caption(
        "Cuisine/type is an initial rules-based classification from place names and your review text. "
        "Use the selector below to focus on one or several categories."
    )

    if df.empty:
        st.info("No reviews match the current filters.")
        return

    cuisine_options = sorted([x for x in df["cuisine"].dropna().unique() if x])
    selected = st.multiselect(
        "Filter cuisine / type on this page",
        cuisine_options,
        placeholder="Choose Pizza, Persian, Burger, Italian …",
    )
    view = df[df["cuisine"].isin(selected)].copy() if selected else df.copy()

    metrics(view)

    summary = (
        view.groupby("cuisine", dropna=False)
        .agg(
            reviews=("place_name", "size"),
            average_rating=("rating", "mean"),
            five_star_share=("rating", lambda x: (x == 5).mean()),
        )
        .reset_index()
        .sort_values("reviews", ascending=False)
    )

    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(
            summary.head(20).sort_values("reviews"),
            x="reviews",
            y="cuisine",
            orientation="h",
            title="Most reviewed types",
        ),
        use_container_width=True,
    )
    c2.plotly_chart(
        px.bar(
            summary.head(20).sort_values("average_rating"),
            x="average_rating",
            y="cuisine",
            orientation="h",
            range_x=[1, 5],
            title="Average of my ratings",
        ),
        use_container_width=True,
    )

    st.markdown("### Places in selected categories")
    details = view[
        ["place_name", "rating", "cuisine", "city", "state", "review_date", "review_text"]
    ].sort_values(["cuisine", "rating"], ascending=[True, False])
    details["review_date"] = details["review_date"].dt.date
    st.dataframe(
        details,
        use_container_width=True,
        hide_index=True,
        column_config={"review_text": st.column_config.TextColumn("Review", width="large")},
    )


def ratings_page(df: pd.DataFrame):
    st.subheader("⭐ Reviews & Ratings")

    if df.empty:
        st.info("No reviews match the current filters.")
        return

    available_ratings = sorted([int(x) for x in df["rating"].dropna().unique()], reverse=True)
    selected_ratings = st.multiselect(
        "Ratings to show on this page",
        available_ratings,
        default=available_ratings,
        format_func=lambda x: f"{x} ★",
        help="Select only 5 ★ to show just five-star reviews.",
    )
    view = df[df["rating"].isin(selected_ratings)].copy() if selected_ratings else df.iloc[0:0].copy()

    metrics(view)
    if view.empty:
        st.info("Choose at least one rating.")
        return

    c1, c2 = st.columns(2)
    rating_counts = (
        view["rating"].value_counts().sort_index().rename_axis("rating").reset_index(name="reviews")
    )
    c1.plotly_chart(
        px.bar(rating_counts, x="rating", y="reviews", title="Rating distribution"),
        use_container_width=True,
    )

    trend = (
        view.dropna(subset=["review_date"])
        .assign(year=lambda x: x["review_date"].dt.year)
        .groupby("year")
        .agg(reviews=("place_name", "size"), average_rating=("rating", "mean"))
        .reset_index()
    )
    c2.plotly_chart(
        px.line(trend, x="year", y="reviews", markers=True, title="Reviews by year"),
        use_container_width=True,
    )

    st.markdown("### Review library")
    library = view.sort_values("review_date", ascending=False)[
        ["review_date", "place_name", "rating", "cuisine", "city", "state", "review_text"]
    ].copy()
    library["review_date"] = library["review_date"].dt.date
    st.dataframe(
        library,
        use_container_width=True,
        hide_index=True,
        column_config={"review_text": st.column_config.TextColumn("Review", width="large")},
    )


st.title("My Google Maps Reviews")
st.caption("A private spatial dashboard of places you reviewed.")

if RAW_REVIEWS.exists():
    st.caption(
        "Data note: Reviews.json is stored in this Codespace only. It is excluded from Git, so deleting the Codespace deletes this copy."
    )
else:
    st.warning("Reviews.json is not in data/raw yet.")
    uploaded = st.file_uploader("Upload your Google Takeout Reviews.json", type=["json"])
    if uploaded is not None:
        try:
            preview = parse_takeout_reviews(uploaded)
            uploaded.seek(0)
            save_uploaded_reviews(uploaded)
            st.success(f"Imported {len(preview):,} rated reviews. Reloading…")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not read the Takeout file: {exc}")

add_review_form()

all_reviews = get_data()
if all_reviews.empty:
    st.info("Upload Reviews.json or add a manual review to start.")
    st.stop()

filtered_reviews = apply_filters(all_reviews)
page = st.sidebar.radio("Page", ["🗺️ Explorer", "🔥 Heatmap", "🍽️ Categories", "⭐ Reviews & Ratings"])

if page == "🗺️ Explorer":
    explorer_page(filtered_reviews)
elif page == "🔥 Heatmap":
    heatmap_page(filtered_reviews)
elif page == "🍽️ Categories":
    categories_page(filtered_reviews)
else:
    ratings_page(filtered_reviews)
