import json

import pandas as pd

from src.exporter import to_json_records, export_json


def _sample_df(x=1.0, pixel_x=10.0):
    return pd.DataFrame({
        "user_id": ["1440"],
        "player_type": ["Bot"],
        "match_id": ["abc.nakama-0"],
        "map_id": ["AmbroseValley"],
        "event": ["BotPosition"],
        "ts": pd.to_datetime(["2026-02-10 11:52:00"]),
        "x": [x],
        "y": [2.0],
        "z": [3.0],
        "pixel_x": [pixel_x],
        "pixel_y": [20.0],
    })


def test_nan_becomes_none_in_records():
    df = _sample_df(x=float("nan"), pixel_x=float("nan"))
    records = to_json_records(df)
    assert records[0]["x"] is None
    assert records[0]["pixel_x"] is None


def test_non_nan_values_are_preserved():
    df = _sample_df()
    records = to_json_records(df)
    assert records[0]["user_id"] == "1440"
    assert records[0]["x"] == 1.0
    assert records[0]["pixel_x"] == 10.0


def test_export_json_writes_parseable_json_even_with_nan(tmp_path):
    df = _sample_df(x=float("nan"), pixel_x=float("nan"))
    out_path = tmp_path / "out.json"

    export_json(df, str(out_path))

    with open(out_path) as f:
        loaded = json.load(f)

    assert loaded[0]["x"] is None
    assert loaded[0]["user_id"] == "1440"


def test_to_json_records_only_includes_known_export_columns():
    df = _sample_df()
    df["extra_column"] = ["should not appear"]
    records = to_json_records(df)
    assert "extra_column" not in records[0]
