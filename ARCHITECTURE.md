# ARCHITECTURE

## Overview

The Player Journey Visualization Tool is a full-stack web application that converts raw player telemetry stored in Parquet files into interactive match replays and gameplay analytics for level designers.

The backend loads telemetry, classifies players, maps world coordinates to minimap coordinates, and exposes REST APIs. The frontend consumes these APIs to provide replay playback, filtering, heatmaps, and gameplay statistics.

---

## Technology Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Frontend | HTML, CSS, Vanilla JavaScript | Lightweight with no framework overhead |
| Rendering | HTML5 Canvas | Efficient replay rendering |
| Backend | FastAPI + Python | High-performance REST APIs |
| Data Processing | Pandas, PyArrow, NumPy | Fast telemetry processing and analytics |
| Deployment | Cloudflare Pages + Render | Simple cloud deployment |

---

## System Architecture

```
Parquet Files
      │
      ▼
Telemetry Loader
      │
      ▼
Pandas DataFrame Cache
      │
 ┌────┴────┐
 ▼         ▼
Match Service   Analytics Service
      │
      ▼
 REST API (FastAPI)
      │
      ▼
HTML / JavaScript Frontend
      │
      ▼
Replay • Heatmaps • Dashboard
```

---

## Data Flow

1. Load all Parquet telemetry into a cached Pandas DataFrame.
2. Classify players as Human or Bot.
3. Convert world coordinates into minimap pixel coordinates.
4. Build match index and analytics.
5. Expose replay and analytics through REST APIs.
6. Frontend renders replay, timeline, filters, and heatmaps using Canvas.

---

## Coordinate Mapping

Telemetry stores positions in world-space (X, Y, Z), which cannot be drawn directly on the minimap.

The mapping pipeline is:

```
World Coordinates
        │
        ▼
Normalize using map bounds
        │
        ▼
Scale to minimap resolution
        │
        ▼
pixel_x / pixel_y
        │
        ▼
Canvas Rendering
```

Each map uses predefined calibration values to accurately align player movement with the minimap.

---

## Major Tradeoffs

| Considered | Chosen | Reason |
|------------|--------|--------|
| React | Vanilla JavaScript | Simpler and lightweight |
| Database | In-memory DataFrame | Dataset comfortably fits in memory |
| Leaflet | Canvas | Better replay performance |
| Server-side rendering | Client-side rendering | Reduced backend complexity |
| Dynamic analytics | On-demand analytics | Simpler implementation |

---

## Scalability & Future Improvements

The current implementation preloads the entire dataset into memory, providing fast replay and analytics for the assignment dataset.

For larger production datasets, I would optimize the replay loader by taking advantage of the filename structure. Since the **match ID is encoded in each player telemetry filename**, the loader could scan filenames first and load only the files belonging to the requested match instead of loading every Parquet file.

```
Scan filenames
        │
        ▼
user1_MATCH123.nakama-0
user2_MATCH123.nakama-0
user3_MATCH123.nakama-0
        │
        ▼
Load only MATCH123 files
        │
        ▼
Build replay
```

For a typical match with ~15 players, this approach would read roughly **15 files instead of 1,243**, significantly reducing startup time, memory usage, and improving scalability while maintaining replay accuracy.