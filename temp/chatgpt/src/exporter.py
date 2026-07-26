"""
exporter.py

Shared export utilities for telemetry datasets.

Supports:
- JSON
- CSV
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple, Union

import pandas as pd


def dataframe_to_records(df: pd.DataFrame) -> List[Dict]:
    """
    Convert a telemetry dataframe into JSON-safe records.

    - Converts timestamps to strings.
    - Converts NaN to None.
    - Renames x/y/z -> world_x/world_y/world_z.
    """

    export_df = df.copy()

    if "ts" in export_df.columns:
        export_df["ts"] = export_df["ts"].astype(str)

    records = export_df.to_dict("records")

    for record in records:

        if "ts" in record:
            record["timestamp"] = record.pop("ts")

        # Rename world coordinates
        if "x" in record:
            value = record.pop("x")
            record["world_x"] = (
                None if pd.isna(value) else float(value)
            )

        if "y" in record:
            value = record.pop("y")
            record["world_y"] = (
                None if pd.isna(value) else float(value)
            )

        if "z" in record:
            value = record.pop("z")
            record["world_z"] = (
                None if pd.isna(value) else float(value)
            )

        # Replace remaining NaN values
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None

    return records


def export_json(
    df: pd.DataFrame,
    filename: Union[str, Path],
) -> None:
    """
    Export telemetry dataframe as JSON.
    """

    filename = Path(filename)

    records = dataframe_to_records(df)

    with filename.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            records,
            f,
            indent=2,
            ensure_ascii=False,
        )


def export_csv(
    df: pd.DataFrame,
    filename: Union[str, Path],
) -> None:
    """
    Export telemetry dataframe as CSV.
    """

    filename = Path(filename)

    df.to_csv(
        filename,
        index=False,
    )


def export_all(
    df: pd.DataFrame,
    output_prefix: Union[str, Path],
) -> Tuple[Path, Path]:
    """
    Export both CSV and JSON.

    Example
    -------
    telemetry
        ->
    telemetry.csv
    telemetry.json
    """

    output_prefix = Path(output_prefix)

    csv_path = output_prefix.with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")

    export_csv(df, csv_path)
    export_json(df, json_path)

    return csv_path, json_path