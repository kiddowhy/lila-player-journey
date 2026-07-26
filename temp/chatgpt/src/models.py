"""
models.py

Shared Pydantic models for the LILA Player Journey API.

These models define the API contract between the backend
and the frontend.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------
# Event
# ---------------------------------------------------------

class EventModel(BaseModel):
    timestamp: str

    event: str

    world_x: float
    world_y: float
    world_z: float

    pixel_x: Optional[float] = None
    pixel_y: Optional[float] = None

    model_config = ConfigDict(
        frozen=True,
    )


# ---------------------------------------------------------
# Player
# ---------------------------------------------------------

class PlayerModel(BaseModel):

    user_id: str

    player_type: str

    event_count: int

    events: List[EventModel]

    model_config = ConfigDict(
        frozen=True,
    )


# ---------------------------------------------------------
# Match
# ---------------------------------------------------------

class MatchModel(BaseModel):

    match_id: str

    map_id: str

    player_count: int

    players: List[PlayerModel]

    model_config = ConfigDict(
        frozen=True,
    )


# ---------------------------------------------------------
# Match Summary
# ---------------------------------------------------------

class MatchSummaryModel(BaseModel):

    match_id: str

    map_id: str

    players: int

    rows: int

    model_config = ConfigDict(
        frozen=True,
    )


# ---------------------------------------------------------
# Player Summary
# ---------------------------------------------------------

class PlayerSummaryModel(BaseModel):

    user_id: str

    player_type: str

    matches: int

    events: int

    model_config = ConfigDict(
        frozen=True,
    )


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

class HealthModel(BaseModel):

    status: str

    service: Optional[str] = None

    model_config = ConfigDict(
        frozen=True,
    )