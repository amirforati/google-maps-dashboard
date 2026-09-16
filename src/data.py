from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

RAW_DIR = Path("data/raw")
MANUAL_FILE = Path("data/manual_reviews.csv")

STATE_RE = re.compile(r",\s*([A-Z]{2})\s+\d{5}(?:-\d{4})?(?:,|$)")

CUISINE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Persian", ("persian", "iranian", "kabob", "kebab", "tahchin", "ghormeh", "ash reshteh", "lavashak")),
    ("Pizza", ("pizza", "pizzeria", "neapolitan")),
    ("Burger", ("burger", "hamburger")),
    ("Italian", ("italian", "pasta", "trattoria", "osteria", "ristorante")),
    ("Mexican", ("mexican", "taco", "taqueria", "burrito")),
    ("Turkish", ("turkish", "baklava", "doner")),
    ("Mediterranean", ("mediterranean", "levantine", "middle eastern", "falafel", "hummus")),
    ("Afghan", ("afghan", "kabuli", "naringe")),
    ("Japanese", ("japanese", "sushi", "ramen", "izakaya")),
    ("Chinese", ("chinese", "dim sum", "szechuan", "sichuan")),
    ("Indian", ("indian", "tandoori", "biryani", "masala")),
    ("Korean", ("korean", "kimchi", "bulgogi")),
    ("Thai", ("thai", "pad thai", "tom yum")),
    ("Vietnamese", ("vietnamese", "pho", "banh mi")),
    ("Seafood", ("seafood", "oyster", "lobster", "clam", "chowder")),
    ("Steakhouse", ("steakhouse", "steak")),
    ("Coffee", ("coffee", "cafe", "espresso", "cappuccino")),
    ("Bakery", ("bakery", "pastry", "croissant")),
    ("Ice Cream", ("ice cream", "gelato", "sorbet")),
    ("Brunch / Diner", ("brunch", "breakfast", "diner", "pancake", "french toast")),
    ("American", ("american cuisine", "american restaurant")),
]


def infer_cuisine(name: str | None, review: str | None) -> str:
    text = f"{name or ''} {review or ''}".lower()
    for cuisine, keywords in CUISINE_RULES:
        if any(keyword in text for keyword in keywords):
            return cuisine
    return "Other / Unclassified"


def infer_state(address: str | None) -> str:
    if not address:
        return ""
    match = STATE_RE.search(address)
    return match.group(1) if match else ""


def infer_city(address: str | None) -> str:
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        return parts[-3]
    return ""


def _question_value(questions: Iterable[dict] | None, question_name: str):
    for item in questions or []:
        if item.get("question") == question_name:
            if "rating" in item:
                return item["rating"]
            if "selected_option" in item:
                return item["selected_option"]
            if "selected_options" in item:
                return ", ".join(item["selected_options"])
    return None


def parse_takeout_reviews(source) -> pd.DataFrame:
    payload = json.load(source)
    rows: list[dict] = []

    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [None, None])
        location = props.get("location", {}) or {}

        lon = coords[0] if len(coords) > 0 else None
        lat = coords[1] if len(coords) > 1 else None
        address = location.get("address", "")
        rating = props.get("five_star_rating_published")
        review_text = props.get("review_text_published", "") or ""

        # Google can include activity rows with rating 0. They are not actual rated reviews.
        if rating in (None, 0):
            continue

        rows.append(
            {
                "source": "google_takeout",
                "place_name": location.get("name", "Unknown place"),
                "rating": int(rating),
                "review_text": review_text,
                "review_date": props.get("date"),
                "address": address,
                "city": infer_city(address),
                "state": infer_state(address),
                "country": location.get("country_code", ""),
                "latitude": lat,
                "longitude": lon,
                "google_maps_url": props.get("google_maps_url", ""),
                "category": "Restaurant / Food" if any(
                    _question_value(props.get("questions"), q) is not None
                    for q in ("Food", "Meal type", "Price per person", "Order type")
                ) else "Other",
                "cuisine": infer_cuisine(location.get("name"), review_text),
                "food_rating": _question_value(props.get("questions"), "Food"),
                "service_rating": _question_value(props.get("questions"), "Service"),
                "atmosphere_rating": _question_value(props.get("questions"), "Atmosphere"),
                "price_per_person": _question_value(props.get("questions"), "Price per person"),
                "meal_type": _question_value(props.get("questions"), "Meal type"),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce", utc=True).dt.tz_convert(None)
    return df


def load_takeout_file(path: Path = RAW_DIR / "Reviews.json") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    with path.open("r", encoding="utf-8") as f:
        return parse_takeout_reviews(f)


def load_manual_reviews() -> pd.DataFrame:
    if not MANUAL_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(MANUAL_FILE)
    if "review_date" in df.columns:
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    return df


def save_manual_review(record: dict) -> None:
    MANUAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_row = pd.DataFrame([record])
    if MANUAL_FILE.exists():
        old = pd.read_csv(MANUAL_FILE)
        combined = pd.concat([old, new_row], ignore_index=True)
    else:
        combined = new_row
    combined.to_csv(MANUAL_FILE, index=False)


def combine_reviews(takeout_df: pd.DataFrame, manual_df: pd.DataFrame) -> pd.DataFrame:
    frames = [df for df in (takeout_df, manual_df) if not df.empty]
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True, sort=False)
    for col in [
        "place_name", "review_text", "address", "city", "state", "country",
        "google_maps_url", "category", "cuisine", "source"
    ]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    for col in ["latitude", "longitude", "rating"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df["has_written_review"] = df["review_text"].astype(str).str.strip().ne("")
    df["year"] = df["review_date"].dt.year
    df["month"] = df["review_date"].dt.to_period("M").astype(str)
    return df
