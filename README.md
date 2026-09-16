# Google Maps Reviews Dashboard

A Streamlit app for exploring Google Maps review history with interactive maps, spatial filtering, rating analysis, heatmaps, and lightweight cuisine classification.

Hosted app: https://myreviews.streamlit.app

> The hosted app may require access depending on deployment settings.

## Overview

This project turns a Google Takeout `Reviews.json` export into an interactive spatial dashboard.

It is designed for personal review-history analysis, but the code can also be reused as a template for other review datasets with similar fields.

## Features

- Interactive map of reviewed places
- Rating-based marker colors
- Pan, zoom, click, box, and lasso selection
- Spatial selections that persist across dashboard pages
- Global filters for rating, state, city, category, cuisine/type, year, and written reviews
- Full-text search across place names, addresses, and review text
- Review-density heatmap
- Rating-weighted heatmap
- 5-star-density and low-rating-density modes
- Cuisine/type summaries such as Pizza, Persian, Burger, Italian, Mexican, Coffee, and more
- Review and rating trends over time
- Searchable review table
- Manual review entry for places that are not yet present in the imported Takeout file

## Dashboard pages

### Explorer

The main spatial view.

Reviewed places are shown as map points, with marker color based on rating.

Map interaction includes:

- Drag to pan
- Scroll to zoom
- Click a marker to select it
- Lasso selection from the Plotly toolbar
- Box selection from the Plotly toolbar
- Persistent spatial filtering across the rest of the app

The table below the map updates to the active spatial selection.

The current default map view is centered on New York City, but this can be changed in `src/app.py`.

### Heatmap

Shows the spatial concentration of reviewed places.

Available modes:

- Review density
- Rating weighted
- 5-star density
- Low-rating density

Heat radius is adjustable from the app.

### Categories

Summarizes reviews by inferred cuisine or place type.

Current examples include:

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

Classification is currently rules-based and uses place names and review text. It should be treated as a first-pass categorization rather than an authoritative business taxonomy.

A future version can use Google Places or another enrichment source for more reliable place categories.

### Reviews & Ratings

Provides review-level analysis, including:

- Rating distribution
- Reviews by year
- Rating-specific filtering
- Full review text
- Cuisine/type
- City and state
- Review date

## Data source

The app is built around the Google Takeout file:

```text
Maps (your places) / Reviews.json
```

A typical export contains fields such as:

- Place name
- Rating
- Review text
- Review date
- Address
- Latitude and longitude
- Google Maps URL

The app filters out unusable records such as missing place names and invalid `0,0` coordinates.

## Data layout

By default, the app expects:

```text
data/raw/Reviews.json
```

Manual entries are stored separately in:

```text
data/manual_reviews.csv
```

This keeps imported Google Takeout data unchanged while allowing new reviews to be added inside the dashboard.

## Manual review entry

The **Add review manually** form currently supports:

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

A planned improvement is place search/autocomplete so users can select a restaurant and automatically populate its address, coordinates, and metadata.

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

## Setup

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

Then open the local or forwarded Streamlit URL.

## GitHub Codespaces

The app can be developed entirely in GitHub Codespaces.

After the Codespace starts:

```bash
python -m pip install -r requirements.txt
python -m streamlit run src/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501
```

Open forwarded port `8501` in the browser.

## Streamlit Community Cloud

Typical deployment settings are:

```text
Branch: main
Main file: src/app.py
```

Streamlit Community Cloud can redeploy automatically when changes are pushed to the deployment branch.

If the app uses a private repository, access control can remain restricted to authorized users.

## Privacy and public-repository safety

Google Maps review exports can contain sensitive personal information, including location history clues, addresses, review text, and timestamps.

The application code can be public, but personal data should normally not be.

Before making a repository public:

1. Remove `data/raw/Reviews.json` if it contains personal data.
2. Remove `data/manual_reviews.csv` if it contains personal entries.
3. Remove any exported data from Git history if it was previously committed.
4. Replace private data with a small synthetic or anonymized sample dataset if a public demo is needed.
5. Confirm that `.gitignore` excludes local personal-data files.
6. Confirm that no API keys, OAuth secrets, GitHub tokens, or Streamlit secrets are committed.
7. Review the repository history, not only the current working tree, before changing visibility to public.

A public version of this project should ideally use a structure such as:

```text
data/
├── sample/
│   └── Reviews.example.json
└── raw/
    └── .gitkeep
```

with real personal data supplied locally or through a private deployment environment.

## Optional persistence for manual reviews

Streamlit Community Cloud uses an ephemeral local filesystem. If manual entries must survive restarts, they need durable storage.

One supported pattern in this project is to write `data/manual_reviews.csv` back to a private GitHub repository using a fine-grained GitHub token stored in Streamlit secrets.

Example Streamlit secret:

```toml
GITHUB_TOKEN = "..."
```

The token should be restricted to the minimum required repository and permissions.

Never commit the token to Git.

For a fully public repository, a database or another private storage backend is preferable to committing user-specific review data.

## Current implementation notes

- Google Takeout is the source of truth for imported reviews.
- Manual reviews are stored separately from imported data.
- Spatial selections are stored in Streamlit session state.
- The Explorer map defaults to New York City.
- Double-click map reset is disabled.
- Pan is the default map interaction.
- Lasso and box selection remain available from the Plotly toolbar.
- Cuisine classification is heuristic and can be improved with external place metadata.

## Planned improvements

- Google Places enrichment for official categories and cuisine tags
- Automatic place lookup in the manual-review form
- Automatic address and coordinate completion
- Editable manual reviews
- Manual category overrides for imported reviews
- Better cuisine taxonomy
- Duplicate-place detection
- Neighborhood and metro-area summaries
- Export selected reviews to CSV
- Optional sample dataset for public use
- Optional database-backed persistence

## Disclaimer

This project is not affiliated with or endorsed by Google. Google Maps and Google Takeout are trademarks or services of Google LLC.
