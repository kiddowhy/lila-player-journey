"""
match_service.py

Service layer responsible for building match payloads from telemetry.

Responsibilities
----------------
- Load telemetry
- Classify players
- Add minimap coordinates
- Build match index
- Return API-ready match payloads
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

from src.classifier import classify_players
from src.loader import load_day
from src.mapper import add_coords


class MatchService:

    def __init__(self, folder: Union[str, Path]):

        self.folder = Path(folder)

        self.df = None
        self.match_index = None

    # ---------------------------------------------------------
    # Load telemetry once
    # ---------------------------------------------------------

    def load(self):

        if self.df is not None:
            return

        df, _ = load_day(self.folder)

        df = classify_players(df)

        df = add_coords(df)

        self.df = df

        self.match_index = self._build_match_index()

    # ---------------------------------------------------------
    # Build match index
    # ---------------------------------------------------------

    def _build_match_index(self):

        summary = (
            self.df
            .groupby("match_id")
            .agg(
                players=("user_id", "nunique"),
                rows=("user_id", "count"),
                map=("map_id", "first"),
            )
            .sort_values(
                ["players", "rows"],
                ascending=False,
            )
        )

        return summary

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def list_matches(self):

        self.load()

        return self.match_index.reset_index()

    def get_match(self, match_id):

        self.load()

        match = (
            self.df[self.df["match_id"] == match_id]
            .sort_values("ts")
            .copy()
        )

        if match.empty:
            raise RuntimeError(
                f"Match {match_id} not found."
            )

        payload = {
            "match_id": str(match_id),
            "map_id": str(match["map_id"].iloc[0]),
            "player_count": int(
                match["user_id"].nunique()
            ),
            "players": [],
        }

        for uid, player in match.groupby("user_id"):

            player_events = []

            player = player.sort_values("ts")

            for _, row in player.iterrows():

                player_events.append(
                    {
                        "timestamp": str(row["ts"]),
                        "event": row["event"],
                        "world_x": float(row["x"]),
                        "world_y": float(row["y"]),
                        "world_z": float(row["z"]),
                        "pixel_x": (
                            None
                            if pd.isna(row["pixel_x"])
                            else float(row["pixel_x"])
                        ),
                        "pixel_y": (
                            None
                            if pd.isna(row["pixel_y"])
                            else float(row["pixel_y"])
                        ),
                    }
                )

            payload["players"].append(
                {
                    "user_id": str(uid),
                    "player_type": player[
                        "player_type"
                    ].iloc[0],
                    "event_count": len(player_events),
                    "events": player_events,
                }
            )

        return payload

    def get_largest_match(self):

        self.load()

        return self.match_index.index[0]