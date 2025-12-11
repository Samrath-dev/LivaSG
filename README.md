# LIVASG 

# Frontend:

## Table of Contents

- [Overview](#overview)
- [Features and Views](#features-and-views)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage Guide](#usage-guide)
  - [Exploring Properties](#exploring-properties)
  - [Advanced Search](#advanced-search)
  - [Personalised Recommendations](#personalised-recommendations)
  - [Comparison Features](#comparison-features)
  - [Data Management](#data-management)

## Overview

A react-based web application for exploring Singapore property with interactive maps, search functionality, compare functionality, detailed area information and many more!

## Features and Views

### Views

- **LaunchView**: Launch page to set preference before continuing with application
- **MapView**: Main exploration view with interactive Singapore map and coloured polygons
- **SearchView**: Advanced search with filters and location results
- **SpecificView**: Zoomed-in view of individual areas with action buttons
- **DetailsView**: Detailed information for facilities in the location
- **AnalysisView**: Area rating comparison with visual score breakdowns using radar chart and price trend line
- **CompareView**: Compare between numerous locations, to see price and score diferences
- **PreferenceView**: Rank your preferences for the order of the 5 categories
- **BookmarkView**: Saved locations, for future viewing
- **SettingsView**: Import or export data

## Project Structure

```
src/
├── api
| └── https.ts
├── components/
│ ├── BottomNav.tsx
│ ├── OneMapEmbedded.tsx
| └── OneMapInteractive.tsx
├── Layouts\PageLayout
| └── PageLayout.tsx
├── utils
| └── mapUtils.ts
├── views/
| ├── AnalysisView.tsx
| ├── BookmarkView.tsx
| ├── ComparisonView.tsx
| ├── DetailsView.tsx
| ├── LaunchView.tsx
│ ├── MapView.tsx
| ├── PreferenceView.tsx
│ ├── SearchView.tsx
│ ├── SettingsView.tsx
│ └── SpecificView.tsx
└── App.tsx
```

## Getting Started

### Prequisities

- Node.js 16+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Clone the repository
git clone https://github.com/Samrath-dev/LivaSG.git

# Install dependencies
npm install

# Start development server
npm run dev

```

## Usage Guide

### Exploring Properties

1. **Start with Explore Page**: Open the application to view Singapore map
2. **Click Areas**: Select any polygon (planning area) to see basic information, further click "Analysis" or "Facilities" to view more details
3. **View Facilities**: Click "Facilities" for comprehensive analysis of amenities in that location
4. **View Analysis**: Click "Analysis" for breakdown of categories scores and price trend line
5. **Compare**: Use comparison tools to evaluate multiple areas

### Advanced Search

1. **Access Search Function**: Use search bar at explore page
2. **Apply Filters**:
   - Select preferred amenities
3. **Review Results**: Click on search results for detailed views

### Personalised Recommendations

1. **Set Preferences**: Navigate to Preferred tab on navigation bar
2. **Rank Categories**: Order the 5 evaluation categories by importance
3. **Get Custom Scores**: View personalised area rankings

### Comparison Features

1. **Select Locations**: Choose areas to compare in Compare tab on navigation bar
2. **View Radar Charts**: Visual comparison of category scores
3. **Analyse Differences**: Overlay of price trend and radar chart

### Data Management

1. **Bookmark Locations**: Save interesting areas for quick access
2. **Export Data**: Download your preferences and saved locations
3. **Import Settings**: Restore previous configurations

# Backend:

## Table of Contents

- [Overview](#overview)
- [Supports](#currently-supports-the-following)
- [Project Structure](#project-structure-backend)
- [Installation and setup](#installation-and-setup)
- [Run the Backend](#Run)

## Overview

The backend is a FastAPI service responsible for:
• Serving neighbourhood scores, search rankings, and detailed breakdowns
• Integrating OneMap PopAPI to fetch real planning area polygons and names
• Serving data to the React frontend via REST endpoints
• Providing modular architecture using Domain, Repositories, Services, and Controllers (API)

## Currently supports the following:

- GET / -> Health check (returns {"ok": true})
- GET /test-onemap -> Quick OneMap connectivity test (returns truncated raw response)

- Map

  - GET /map/choropleth -> Return neighbourhood scores (choropleth) for planning areas; accepts query param `weightsId`

- Details

  - GET /details/{area_id}/breakdown -> Category breakdown for an area or a street
  - GET /details/{area_id}/facilities -> Facilities summary for an area
  - GET /details/street/{street_name}/facilities-locations -> Facility locations (markers) near a street (query param `types`)

- OneMap / Planning areas

  - GET /onemap/planning-areas?year=2019 -> GeoJSON for planning areas
  - GET /onemap/planning-area-names?year=2019 -> List of planning area names
  - GET /onemap/planning-area-at?latitude=&longitude=&year=2019 -> Resolve planning area at a lat/lon (501 if not implemented in repo)
  - POST /onemap/renew-token -> Force OneMap token refresh (optional email/password in body)

- Search (mounted under /search)

  - POST /search -> Area-ranking search (body: SearchFilters)
  - POST /search/filter -> Filter locations (body: SearchFilters, query `view_type`)
  - POST /search/filter-polygon -> Filter locations using polygon
  - POST /search/search-and-rank -> Combined search + ranking (returns locations with scores)
  - GET /search/facilities -> List of available facility filters
  - GET /search/onemap?query=&page= -> Search OneMap via backend proxy

- Weights & Ranks

  - GET /weights -> Get active weights profile
  - POST /weights -> Create & activate a weights profile (body: weights)
  - GET /ranks -> Get current rank preferences
  - POST /ranks -> Set rank preferences
  - POST /ranks/reset -> Reset ranks to defaults

- Shortlist

  - GET /shortlist/saved-locations -> Retrieve saved/bookmarked locations
  - POST /shortlist/saved-locations -> Save a location (body: postal_code, address, area)
  - DELETE /shortlist/saved-locations/{postal_code} -> Remove saved location

- Settings / Export & Import

  - GET /settings/export/api -> Export structured data (JSON) via API
  - GET /settings/export/json -> Export JSON (optionally save to disk)
  - GET /settings/export/csv -> Export CSV (optionally save to disk)
  - POST /settings/import -> Import settings/exported data (body: ImportRequest)

- Debug / Transit
  - GET /debug/transit/count -> Count of transit nodes
  - GET /debug/transit/area/{area_id} -> Transit nodes for an area
  - GET /debug/transit/nearest?lat=&lon=&k= -> Nearest transit nodes to a lat/lon

## Project Structure (Backend)

```
LivaSG Backend/
├── .cache/
├── app/
│  ├── __init__.py
│  ├── main.py
│  ├── api/
│  │  ├── __init__.py
│  │  ├── details_controller.py
│  │  ├── map_controller.py
│  │  ├── onemap_controller.py
│  │  ├── ranks_controller.py
│  │  ├── search_controller.py
│  │  ├── settings_controller.py
│  │  ├── shortlist_controller.py
│  │  ├── transit_debug.py
│  │  └── weights_controller.py
│  ├── cache/
│  │  ├── __init__.py
│  │  ├── disk_cache.py
│  │  └── paths.py
│  ├── domain/
│  │  ├── __init__.py
│  │  ├── enums.py
│  │  └── models.py
│  ├── integrations/
│  │  ├── __init__.py
│  │  └── onemap_client.py
│  ├── repositories/
│  │  ├── __init__.py
│  │  ├── api_planning_repo.py
│  │  ├── interfaces.py
│  │  ├── memory_impl.py
│  │  ├── sqlite_rank_repo.py
│  │  └── sqlite_saved_location_repo.py
│  └── services/
│     ├── __init__.py
│     ├── rating_engine.py
│     ├── search_service.py
│     ├── settings_service.py
│     ├── shortlist_service.py
│     └── trend_service.py
├── data/
│  ├── bus_stops.csv
│  └── resale_2017_onwards.csv
├── exports/
├── scripts/
│  ├── add_transit_column.py
│  ├── check_not_found.py
│  ├── check_schema.py
│  ├── delete_planning_area.py
│  ├── extract_streets.py
│  ├── find_offending_serangoon.py
│  ├── generate_street_facilities.py
│  ├── geocode_streets.py
│  ├── get_token.py
│  ├── import_hdb_streets.py
│  ├── inspect_planning_cache.py
│  ├── list_planning_area_facilities.py
│  ├── list_transit_streets.py
│  ├── migrate_add_planning_area.py
│  ├── populate_area_facilities.py
│  ├── populate_missing_facilities.py
│  ├── populate_planning_locations.py
│  ├── populate_street_community.py
│  ├── query_planning_cache.py
│  ├── query_serangoon.py
│  ├── query_street_facilities.py
│  ├── restore_planning_polygon.py
│  ├── retry_geocoding.py
│  ├── scrape_postal_codes.py
│  ├── test_breakdown_async.py
│  ├── test_details_fix.py
│  ├── test_facility_filtering.py
│  ├── test_facility_lookup.py
│  ├── test_nearby_mrt.py
│  ├── test_normalization.py
│  └── test_transit_integration.py
├── .env
├── planning_cache.db
├── street_geocode.db
└── user_cache.db
```

## Installation and setup

```bash
## Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

## Upgrade pip
pip install --upgrade pip

## Install project dependencies
pip install -r requirements.txt

## Run the Backend
uvicorn app.main:app --reload

## Create a .env file
ONEMAP_EMAIL= # your email
ONEMAP_PASSWORD= # your password
PORT=8000
RESALE_CSV_PATH=./resale-flat-prices-based-on-registration-date-from-jan-2017-onwards.csv
BUS_STOPS_CSV_PATH=./bus_stops.csv
ONEMAP_TOKEN= # your token (if have existing)
```

## Authors

### Contributors names

- Calvin Kuan Jiahui 
- Jet Hee Fong 
- Lee Loong Kiat 
- Samrath Bose 
- Thum Mun Kuan 
- Tok Xi Quan 
