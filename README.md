# My Google Maps Reviews Dashboard

Private Streamlit dashboard for exploring my Google Maps review history.

Live app: https://myreviews.streamlit.app

## What it does

The dashboard loads Google Maps reviews exported through Google Takeout and turns them into an interactive spatial review database.

Main features:

- Interactive map of reviewed places
- Rating-based marker colors
- Pan, zoom, click, box, and lasso selection
- Map selections persist across dashboard pages
- Global filters for rating, state, city, category, cuisine/type, year, and written reviews
- Review text search
- Review-density heatmap
- Rating-weighted heatmap
- 5-star-density and low-rating-density maps
- Cuisine/type summaries such as Persian, Pizza, Burger, Italian, Mexican, Coffee, and more
- Review and rating trends over time
- Full searchable review table
- Manual review entry for restaurants or places that are not yet in Google Takeout

## Pages

### Explorer

The main map view.

It shows reviewed places as points, with color based on my rating. The default map view is centered on New York City.

Map interaction:

- Drag to pan
- Scroll to zoom
- Click a point to select it
- Use the Plotly toolbar for lasso or box selection
- A spatial selection carries over to the Heatmap, Categories, and Reviews & Ratings pages
- Use **Clear map selection** in the sidebar to remove the spatial filter

The table below the map shows the places in the current map selection.

### Heatmap

Spatial concentration of reviews.

Available modes:

- Review density
- Rating weighted
- 5-star density
- Low-rating density

The heat radius is adjustable.

### Categories

Summaries by inferred cuisine or place type.

Examples include:

- Persian
- Pizza
- Burger
- Italian
- Mexican
- Turkish
- Mediterranean
- Japanese
- Chinese
- Indian
- Korean
- Thai
- Vietnamese
- Seafood
- Steakhouse
- Coffee
- Bakery
- Ice Cream
- Brunch / Diner

The current classification is rules-based and uses the place name and review text. It is intended as a first-pass classification and can later be improved with Google Places enrichment or manual overrides.

### Reviews & Ratings

Review-level analysis, including:

- Rating distribution
- Reviews by year
- Rating-specific filtering
- Full review text table
- Cuisine/type, city, state, and review date

## Data source

The primary dataset is:

```text
data/raw/Reviews.json
```

This file comes from:

```text
Google Takeout
→ Maps (your places)
→ Reviews.json
```

The Google Takeout review export contains location coordinates, rating, review text, review date, address, and Google Maps URL for most reviewed places.

Records with missing place names such as `Unknown place` and invalid `0,0` coordinates are excluded from the dashboard.

## Manual reviews

New places can be added from the **Add review manually** form.

Manual reviews are stored separately in:

```text
data/manual_reviews.csv
```

They are then merged with the Google Takeout reviews inside the dashboard.

This keeps the original Google Takeout data unchanged.

The manual form currently asks for:

- Place name
- Rating
- Review date
- Review text
- Category
- Cuisine/type
- Address
- City
- State
- Country
- Latitude
- Longitude
- Optional Google Maps URL

A future improvement is to use Google Places search so the user can select a restaurant and automatically populate its address and coordinates.

## Repository structure

```text
google-maps-dashboard/
├── data/
│   ├── raw/
│   │   └── Reviews.json
│   └── manual_reviews.csv
├── src/
│   ├── app.py
│   └── data.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Local or Codespaces setup

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python -m streamlit run src/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501
```

In GitHub Codespaces, port `8501` can be opened through the forwarded app URL.

## Streamlit Community Cloud deployment

The deployed app uses:

```text
Repository: amirforati/google-maps-dashboard
Branch: main
Main file: src/app.py
```

Live URL:

https://myreviews.streamlit.app

Streamlit Community Cloud automatically redeploys the app after changes are pushed to `main`.

## Private data

This repository is intended to remain private because it contains personal review history and location information.

The committed Google Takeout file can include:

- Reviewed place names
- Ratings
- Review text
- Review dates
- Addresses
- Latitude and longitude
- Google Maps links

Anyone who is granted access to the private repository can also access those files.

Do not make the repository public without first removing personal data.

## Optional GitHub persistence for manual reviews

A deployed Streamlit app has an ephemeral local filesystem. For manual reviews to survive app restarts, the app can write `data/manual_reviews.csv` back to the private GitHub repository.

Add a fine-grained GitHub token to Streamlit secrets:

```toml
GITHUB_TOKEN = "..."
```

The token should be limited to this repository and only have the permissions needed to update repository contents.

Never commit the token to the repository.

## Current design notes

- Google Takeout is the source of truth for imported reviews.
- Manual reviews are stored separately.
- Spatial selections are held in Streamlit session state.
- The default Explorer map is centered on New York City.
- Double-click map reset is disabled.
- Pan is the default map interaction.
- Lasso and box selection remain available from the Plotly toolbar.
- Cuisine classification is currently heuristic rather than authoritative.

## Planned improvements

Possible next steps:

- Google Places enrichment for official categories and cuisine tags
- Automatic place lookup in the manual-review form
- Automatic address and coordinate completion
- Editable manual reviews
- Manual category overrides for imported reviews
- Better cuisine taxonomy
- Duplicate-place detection
- More spatial summaries by metro area and neighborhood
- Export selected reviews to CSV
