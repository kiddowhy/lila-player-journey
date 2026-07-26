"""
api.py

REST API for the LILA Player Journey Visualization Tool.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.match_service import MatchService

DATA_FOLDER = Path("player_data/February_10")

service = MatchService(DATA_FOLDER)

app = FastAPI(
    title="LILA Player Journey API",
    description="Backend API for visualizing player telemetry.",
    version="1.0.0",
)

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------
# Health Check
# ----------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "LILA Player Journey API",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ----------------------------------------------------------
# Matches
# ----------------------------------------------------------

@app.get("/matches")
def list_matches():

    matches = service.list_matches()

    return matches.to_dict("records")


@app.get("/matches/largest")
def largest_match():

    return {
        "match_id": service.get_largest_match(),
    }


@app.get("/matches/{match_id}")
def get_match(match_id: str):

    try:
        return service.get_match(match_id)

    except RuntimeError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ----------------------------------------------------------
# Maps
# ----------------------------------------------------------

@app.get("/maps")
def maps():

    service.load()

    return sorted(
        service.df["map_id"].dropna().unique().tolist()
    )


# ----------------------------------------------------------
# Players
# ----------------------------------------------------------

@app.get("/players/{user_id}")
def get_player(user_id: str):

    service.load()

    player = service.df[
        service.df["user_id"].astype(str) == user_id
    ]

    if player.empty:

        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    return {
        "user_id": user_id,
        "player_type": player["player_type"].iloc[0],
        "matches": player["match_id"].nunique(),
        "events": len(player),
    }


# ----------------------------------------------------------
# Timeline
# ----------------------------------------------------------

@app.get("/matches/{match_id}/timeline")
def timeline(match_id: str):

    service.load()

    df = service.df[
        service.df["match_id"] == match_id
    ].sort_values("ts")

    if df.empty:

        raise HTTPException(
            status_code=404,
            detail="Match not found.",
        )

    return df[
        [
            "ts",
            "user_id",
            "player_type",
            "event",
            "pixel_x",
            "pixel_y",
        ]
    ].to_dict("records")