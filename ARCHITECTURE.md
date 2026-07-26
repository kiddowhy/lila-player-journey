# ARCHITECTURE

## Overview

The Player Journey Visualization Tool is a full-stack web application that transforms raw player telemetry stored in Parquet files into an interactive replay and analytics experience for level designers.

The backend processes telemetry, classifies players, maps world coordinates onto minimap coordinates, and exposes REST APIs. The frontend consumes these APIs to provide match browsing, replay controls, timeline playback, player filtering, and interactive heatmap visualizations.

---

# Technology Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Frontend | HTML5, CSS3, Vanilla JavaScript | Lightweight, framework-free, fast loading and simple deployment |
| Rendering | HTML5 Canvas | Efficient rendering of thousands of player positions during replay |
| Backend | Python + FastAPI | High-performance REST APIs with automatic Swagger documentation |
| Data Processing | Pandas | Efficient filtering, grouping and telemetry analysis |
| Parquet Reader | PyArrow | Native support for Parquet datasets |
| Numerical Processing | NumPy | Efficient heatmap generation |
| Deployment | Cloudflare Pages | Static frontend hosting with global CDN |
| Deployment | Render | Simple deployment for FastAPI backend |

---

# System Architecture

```
                        Parquet Files
                               │
                               ▼
                    Telemetry Loader (PyArrow)
                               │
                               ▼
                     Pandas DataFrame Cache
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   Player Classification   Coordinate Mapping   Match Index
            │                  │                  │
            └──────────────┬───┴──────────────────┘
                           ▼
                    Match Service Layer
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
    Replay API                      Analytics API
          │                                 │
          └────────────────┬────────────────┘
                           ▼
                     REST Endpoints
                           │
                     HTTP / JSON API
                           │
                           ▼
              HTML / JavaScript Frontend
                           │
                           ▼
          Canvas Replay + Heatmaps + Dashboard
```

---

# Data Flow

## 1. Telemetry Loading

At application startup, telemetry data is loaded from all available Parquet files.

The loader:

- Reads every telemetry file
- Combines them into one Pandas DataFrame
- Classifies players as Human or Bot
- Converts world coordinates into minimap coordinates
- Builds a match index

The processed dataset is cached in memory, avoiding repeated file reads for subsequent API requests.

---

## 2. Backend Processing

The Match Service provides:

- Match listing
- Match replay data
- Player information
- Timeline generation

The Analytics Service computes:

- Movement heatmaps
- Combat heatmaps
- Loot heatmaps
- Death heatmaps
- Storm death heatmaps
- Sector statistics
- Overall gameplay summaries

These services expose JSON APIs consumed directly by the frontend.

---

## 3. Frontend Visualization

The frontend communicates with the backend using the Fetch API.

Users can:

- Select a date
- Select a map
- Select a match
- auto play on match select
- Play or pause the replay
- zoom in and out for convenient
- Scrub through the timeline
- Toggle heatmap layers
- Inspect player statistics

Replay rendering is performed using the HTML5 Canvas API for smooth animation.

---

# Coordinate Mapping

One of the main challenges was converting raw world-space coordinates into minimap positions.

Each telemetry event contains:

- World X
- World Y
- World Z

These values cannot be drawn directly onto the minimap.

The mapping pipeline is:

```
World Coordinates

        │

        ▼

Normalize using map boundaries

        │

        ▼

Scale into minimap resolution

        │

        ▼

Generate pixel_x and pixel_y

        │

        ▼

Canvas Rendering
```

Each supported map uses predefined calibration values to normalize coordinates before scaling them to the minimap image.

This transformation allows player movement, combat events, loot pickups, and deaths to align correctly with the displayed map.

---


# Major Tradeoffs

| Considered | Chosen | Reason |
|------------|--------|--------|
| React | Vanilla JavaScript | Simpler architecture with zero framework overhead |
| Database | In-memory Pandas DataFrame | Dataset size is small enough to avoid database complexity |
| Leaflet/OpenLayers | HTML5 Canvas | Better rendering performance for animated player movement |
| Server-side rendering | Client-side rendering | Reduces backend workload and simplifies deployment |
| Dynamic analytics | On-demand analytics | Simpler implementation while maintaining acceptable performance |

---

# Scalability

The current implementation loads the dataset into memory once and serves subsequent requests from the cached DataFrame.

This approach works well for the provided dataset.

For significantly larger datasets, future improvements could include:

- Precomputed analytics
- Background processing jobs
- Redis caching
- Spatial indexing
- Database-backed telemetry storage
- WebSocket streaming for live telemetry

---

## Future Optimization: Match-Level Lazy Loading

### Observation

While building the replay system, I noticed that the telemetry files are already partitioned by player, and the **match ID is encoded in each filename**.

Example:

```
user1_MATCH123.nakama-0
user2_MATCH123.nakama-0
user3_MATCH123.nakama-0
user4_MATCH456.nakama-0
```

### Current Approach

The current implementation loads all telemetry files into memory during startup and builds an in-memory index for fast querying.

```
All Parquet Files
        │
        ▼
Load into DataFrame
        │
        ▼
Filter by Match ID
        │
        ▼
Replay
```

This provides fast replay once the application is initialized, but it requires loading the complete dataset upfront.

### Alternative Approach

Because the match ID is embedded in the filename, the replay loader could instead scan filenames first and only load the files belonging to the requested match.

```
Scan filenames

        │
        ▼
user1_MATCH123.nakama-0
user2_MATCH123.nakama-0
user3_MATCH123.nakama-0
user4_MATCH456.nakama-0

        │
        ▼
Read only MATCH123 files

        │
        ▼
Return Match DataFrame
```

### Benefits

If a typical match contains around **15 players**, the loader would:

- Read approximately **15 files instead of all 1,243 files**
- Allocate memory only for the requested match
- Reduce application startup time
- Scale better as the telemetry dataset grows
- Improve responsiveness for on-demand replay requests

### Tradeoff

For the assignment dataset, I chose to preload the data because the entire dataset comfortably fits in memory and provides very fast replay after initialization. For a production-scale telemetry pipeline with millions of events, lazy loading based on the match ID encoded in filenames would be a more scalable design.
