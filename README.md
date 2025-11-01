# LIVASG (2006-SCS3-06)

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
git clone https://github.com/softwarelab3/2006-SCS3-06.git

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
- [Project Structure](#project-structure)
- [Installation and setup](#Installation)
- [Run the Backend](#Run)

## Overview

The backend is a FastAPI service responsible for:
• Serving neighbourhood scores, search rankings, and detailed breakdowns
• Integrating OneMap PopAPI to fetch real planning area polygons and names
• Serving data to the React frontend via REST endpoints
• Providing modular architecture using Domain, Repositories, Services, and Controllers (API)

It currently supports:
• /map – Choropleth & score visualization
• /details – Price trends & category breakdown
• /search – Ranked search results
• /onemap – Real Singapore planning areas via OneMap API

## Project Structure

```
LIVASG BACKEND/
└── app/
├── api/  
│ ├── details_controller.py
│ ├── map_controller.py
│ ├── onemap_controller.py
│ └── search_controller.py
│
├── domain/  
│ ├── enums.py
│ └── models.py
│
├── integrations/  
│ └── onemap_client.py
│
├── repositories/  
│ ├── api_planning_repo.py
│ ├── interfaces.py
│ └── memory_impl.py
│
├── services/  
│ ├── rating_engine.py
│ ├── search_service.py
│ └── trend_service.py
│
└── main.py  
│
├── planning_cache.db  
├── onemap_locations.json  
└── requirements.txt
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

```
## Authors

### Contributors names

- Calvin Kuan Jiahui (U2421466L)
- Jet Hee Fong (U2421248C)
- Lee Loong Kiat (U2420557J)
- Samrath Bose (U2423924F)
- Thum Mun Kuan (U2422906L)
- Tok Xi Quan (U2421678G)
