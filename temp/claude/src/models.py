"""
Shared constants and lightweight data models used across the pipeline.

This is the single source of truth for the dataset's schema, event
vocabulary, and map coordinate config. Other modules import from here
rather than redefining their own copies, since duplicated copies of
these constants have drifted before (e.g. the movement-event list,
the required-columns set).
"""

from dataclasses import dataclass, field
from typing import List

MINIMAP_SIZE = 1024

# Per-map coordinate system for converting world (x, z) to minimap pixels.
# Confirmed against the README's worked example:
#   AmbroseValley, x=-301.45, z=-355.55 -> pixel_x=78, pixel_y=890
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

MOVEMENT_EVENTS = {"Position", "BotPosition"}

# All 8 documented event types. load_day / validation code checks real
# data against this list so an unrecognized event type is surfaced
# instead of silently passing through.
EXPECTED_EVENTS = {
    "Position", "BotPosition",
    "Kill", "Killed", "BotKill", "BotKilled",
    "KilledByStorm", "Loot",
}

REQUIRED_COLUMNS = {
    "user_id", "match_id", "map_id",
    "x", "y", "z", "ts", "event",
}


@dataclass
class LoadReport:
    """
    Result of a load operation: how many files loaded successfully vs.
    failed, and which ones failed. Returned alongside the combined
    DataFrame so callers (scripts, API endpoints, tests) can detect and
    surface partial data-loss instead of it passing silently.
    """
    files_loaded: int = 0
    files_failed: int = 0
    failed_files: List[str] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return self.files_loaded + self.files_failed

    def __str__(self) -> str:
        if self.files_failed == 0:
            return f"{self.files_loaded} file(s) loaded, none failed"
        return (f"{self.files_loaded}/{self.total_files} file(s) loaded "
                f"({self.files_failed} failed: {self.failed_files})")
