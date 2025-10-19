# Frontend - LIVASG

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
- [Authors](#authors)

## Overview

A react-based web application for exploring Singapore property with interactive maps, search functionality, compare functionality, detailed area information and many more!

## Features and Views

### Views 
- **MapView**: Main exploration view with interactive Singapore map
- **SearchView**: Advanced search with filters and location results
- **SpecificView**: Zoomed-in view of individual areas with action buttons
- **DetailsView**: Detailed information including price trends and facilities
- **CompareLocations**: Area rating comparison with visual score breakdowns using radar chart
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
| ├── BookmarkView.tsx
| ├── CompareLocations.tsx 
| ├── ComparisonView.tsx
| ├── DetailsView.tsx 
│ ├── MapView.tsx 
| ├── PolygonDetailsView.tsx
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
2. **Click Areas**: Select any polygon (planning area) to see basic information, further click "View properties" to view more details
3. **View Details**: Click "Details" for comprehensive area analysis
4. **View Ratings**: Click "Ratings" for breakdown of categories scores
5. **Compare**: Use comparison tools to evaluate multiple areas

### Advanced Search
1. **Access Search Function**: Use search bar at explore page
2. **Apply Filters**:
   - Set budget range with sliders
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


## Authors
### Contributors names
- Calvin Kuan Jiahui (U2421466L)
- Jet Hee Fong
- Lee Loong Kiat (U2420557J)
- Samrath Bose (U2423924F)
- Thum Mun Kuan (U2422906L)
- Tok Xi Quan (U2421678G)