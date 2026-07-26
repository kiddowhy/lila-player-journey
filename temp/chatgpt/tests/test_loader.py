from pathlib import Path

from src.loader import load_day


def test_load_day():

    data_path = Path("player_data/February_10")

    df, files_loaded = load_day(data_path)

    assert files_loaded > 0
    assert len(df) > 0

    required = {
        "user_id",
        "match_id",
        "map_id",
        "x",
        "y",
        "z",
        "ts",
        "event",
    }

    assert required.issubset(df.columns)