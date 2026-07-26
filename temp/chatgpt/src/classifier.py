"""
classifier.py

Player classification utilities.
Python 3.9 compatible.
"""

import re
import pandas as pd

UUID_REGEX = re.compile(
    r'^[0-9a-fA-F]{8}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{12}$'
)

BOT_REGEX = re.compile(r'^\d+$')


def classify_user(user_id):
    """
    Returns:
        Human
        Bot
        Unknown
    """

    if pd.isna(user_id):
        return "Unknown"

    if isinstance(user_id, bytes):
        user_id = user_id.decode("utf-8")

    user_id = str(user_id).strip()

    if BOT_REGEX.match(user_id):
        return "Bot"

    if UUID_REGEX.match(user_id):
        return "Human"

    return "Unknown"


def classify_players(df):
    """
    Adds player_type column.
    """

    df = df.copy()

    df["player_type"] = df["user_id"].apply(
        classify_user
    )

    return df