"""
Serializes telemetry DataFrames to CSV and JSON.

Raw NaN is not valid JSON per spec -- Python's json module will still
write a literal NaN by default, which most non-Python JSON parsers
(e.g. in a browser) will reject. to_json_records() explicitly converts
NaN to None before serializing so the output is safe for non-Python
consumers.
"""

import json
from typing import List

import pandas as pd

EXPORT_COLUMNS = [
    "user_id", "player_type", "match_id", "map_id",
    "event", "ts", "x", "y", "z", "pixel_x", "pixel_y",
]


def to_json_records(df: pd.DataFrame) -> List[dict]:
    """
    Convert a DataFrame to a list of JSON-safe dicts.

    ts is converted to a string (ISO-style) representation. If a
    downstream consumer needs epoch-ms integers instead, do that
    conversion explicitly and deliberately -- do not attempt to convert
    ts via int64 division; a prior attempt at that (double-dividing by
    1_000_000) silently collapsed all ts values in the dataset to a
    single constant. See tests/test_exporter.py and the loader module
    notes for details.
    """
    columns = [c for c in EXPORT_COLUMNS if c in df.columns]
    export_df = df[columns].copy()

    if "ts" in export_df.columns:
        export_df["ts"] = export_df["ts"].astype(str)

    records = export_df.to_dict("records")

    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and pd.isna(value):
                record[key] = None

    return records


def export_json(df: pd.DataFrame, path: str) -> None:
    records = to_json_records(df)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def export_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
