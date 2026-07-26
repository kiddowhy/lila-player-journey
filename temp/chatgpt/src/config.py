"""
config.py

Global configuration for the LILA Player Journey backend.
Compatible with Python 3.9
"""

# --------------------------------------------------------
# Minimap Settings
# --------------------------------------------------------

MINIMAP_SIZE = 1024

# --------------------------------------------------------
# Map Configuration
#
# IMPORTANT:
# Replace these values with the correct ones from the
# dataset README if they differ.
# --------------------------------------------------------

MAP_CONFIG = {

    "AmbroseValley": {
        "origin_x": -370,
        "origin_z": -473,
        "scale": 740,
    },

    "GrandRift": {
        "origin_x": -512,
        "origin_z": -512,
        "scale": 1024,
    },

    "Lockdown": {
        "origin_x": -512,
        "origin_z": -512,
        "scale": 1024,
    },
}

# --------------------------------------------------------
# Required Columns
# --------------------------------------------------------

REQUIRED_COLUMNS = [
    "user_id",
    "match_id",
    "map_id",
    "x",
    "y",
    "z",
    "ts",
    "event",
]

# --------------------------------------------------------
# Events
# --------------------------------------------------------

MOVEMENT_EVENTS = [
    "Position",
    "BotPosition",
]

COMBAT_EVENTS = [
    "Kill",
    "Killed",
    "BotKill",
    "BotKilled",
]

LOOT_EVENTS = [
    "Loot",
]

SPECIAL_EVENTS = [
    "KilledByStorm",
]

KNOWN_EVENTS = (
    MOVEMENT_EVENTS
    + COMBAT_EVENTS
    + LOOT_EVENTS
    + SPECIAL_EVENTS
)