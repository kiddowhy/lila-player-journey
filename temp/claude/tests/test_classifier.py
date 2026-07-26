import pandas as pd

from src.classifier import classify_user_id, classify_players


def test_numeric_id_is_bot():
    assert classify_user_id("1440") == "Bot"


def test_uuid_id_is_human():
    assert classify_user_id("f4e072fa-b7af-4761-b567-1d95b7ad0108") == "Human"


def test_bytes_numeric_id_is_bot():
    # Defensive case: numeric id arriving as bytes should still classify
    # as Bot, not silently fall through to Human or Unknown.
    assert classify_user_id(b"1440") == "Bot"


def test_bytes_uuid_id_is_human():
    assert classify_user_id(b"f4e072fa-b7af-4761-b567-1d95b7ad0108") == "Human"


def test_none_is_unknown():
    assert classify_user_id(None) == "Unknown"


def test_nan_is_unknown():
    assert classify_user_id(float("nan")) == "Unknown"


def test_empty_string_is_unknown():
    assert classify_user_id("") == "Unknown"


def test_whitespace_only_is_unknown():
    assert classify_user_id("   ") == "Unknown"


def test_malformed_id_is_unknown():
    assert classify_user_id("not-a-valid-id") == "Unknown"


def test_classify_players_adds_expected_column():
    df = pd.DataFrame({
        "user_id": [
            "1440",
            "f4e072fa-b7af-4761-b567-1d95b7ad0108",
            None,
        ]
    })
    result = classify_players(df)
    assert list(result["player_type"]) == ["Bot", "Human", "Unknown"]


def test_classify_players_does_not_mutate_caller_in_place():
    df = pd.DataFrame({"user_id": ["1440"]})
    original_columns = list(df.columns)
    classify_players(df)
    # classify_players returns a copy with the new column; the caller's
    # own reference should be unaffected if they didn't reassign it.
    assert list(df.columns) == original_columns
