"""
loader.py

Loads parquet telemetry files for the LILA Player Journey project.

Compatible with Python 3.9
"""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from src.config import REQUIRED_COLUMNS


def decode_events(df):
    """
    Decode byte events into UTF-8 strings.
    """

    if "event" not in df.columns:
        return df

    df = df.copy()

    df["event"] = df["event"].apply(
        lambda x: x.decode("utf-8") if isinstance(x, bytes) else x
    )

    return df


def validate_schema(df):
    """
    Ensure all required columns exist.
    """

    missing = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            missing.append(column)

    if missing:
        raise RuntimeError(
            "Missing required columns: {}".format(", ".join(missing))
        )


def load_file(path):
    """
    Load a single parquet telemetry file.
    """

    table = pq.read_table(path)

    df = table.to_pandas()

    validate_schema(df)

    df = decode_events(df)

    return df


def load_day(folder):
    """
    Load every telemetry file inside a folder.

    Returns
    -------
    dataframe, files_loaded
    """

    folder = Path(folder)

    frames = []

    files_loaded = 0

    for file in folder.iterdir():

        if not file.is_file():
            continue

        try:
            frames.append(load_file(file))
            files_loaded += 1

        except Exception as e:
            print("Skipping {} : {}".format(file.name, e))

    if not frames:
        return pd.DataFrame(), 0

    df = pd.concat(
        frames,
        ignore_index=True,
    )

    return df, files_loaded