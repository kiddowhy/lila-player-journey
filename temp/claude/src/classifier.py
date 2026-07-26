"""
Classifies user_id values as Human, Bot, or Unknown.

Per the dataset README, user_id is a plain string column (not bytes) --
numeric IDs are bots, UUIDs are human players. The bytes-handling below
is kept as a defensive fallback in case that assumption ever stops
holding for some future data source, but it is not expected to trigger
against the current dataset.
"""

import re

import pandas as pd

BOT_PATTERN = re.compile(r"\d+")
UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def classify_user_id(uid) -> str:
    """Classify a single user_id as 'Bot', 'Human', or 'Unknown'."""
    if uid is None:
        return "Unknown"
    if isinstance(uid, float) and pd.isna(uid):
        return "Unknown"

    if isinstance(uid, bytes):
        uid = uid.decode("utf-8")

    uid = str(uid).strip()
    if uid == "":
        return "Unknown"

    if BOT_PATTERN.fullmatch(uid):
        return "Bot"
    if UUID_PATTERN.fullmatch(uid):
        return "Human"
    return "Unknown"


def classify_players(df: pd.DataFrame) -> pd.DataFrame:
    """Add a player_type column ('Bot' / 'Human' / 'Unknown') to df."""
    df = df.copy()
    df["player_type"] = df["user_id"].apply(classify_user_id)
    return df
