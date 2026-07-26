import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.loader import (
    decode_events,
    validate_schema,
    load_day,
    load_files,
    parse_filename,
    build_match_index,
)
from src.models import REQUIRED_COLUMNS


def _make_sample_table():
    return pa.table({
        "user_id": ["f4e072fa-b7af-4761-b567-1d95b7ad0108"],
        "match_id": ["abc.nakama-0"],
        "map_id": ["AmbroseValley"],
        "x": [1.0],
        "y": [2.0],
        "z": [3.0],
        "ts": pd.to_datetime(["2026-02-10 11:52:00"]),
        "event": [b"Position"],
    })


def test_decode_events_converts_bytes_to_string():
    df = pd.DataFrame({"event": [b"Position", "AlreadyStr"]})
    result = decode_events(df)
    assert list(result["event"]) == ["Position", "AlreadyStr"]


def test_validate_schema_raises_on_missing_column():
    df = pd.DataFrame({"user_id": ["1"]})
    with pytest.raises(ValueError):
        validate_schema(df)


def test_validate_schema_passes_with_all_required_columns():
    df = pd.DataFrame({col: [None] for col in REQUIRED_COLUMNS})
    validate_schema(df)  # should not raise


def test_load_day_reads_valid_file_and_reports_success(tmp_path):
    pq.write_table(_make_sample_table(), tmp_path / "sample.nakama-0")

    df, report = load_day(str(tmp_path))

    assert len(df) == 1
    assert report.files_loaded == 1
    assert report.files_failed == 0
    assert df["event"].iloc[0] == "Position"
    assert df["player_type"].iloc[0] == "Human"


def test_load_day_reports_failed_files_without_crashing(tmp_path):
    bad_table = pa.table({"user_id": ["1"]})  # missing required columns
    pq.write_table(bad_table, tmp_path / "bad.nakama-0")
    pq.write_table(_make_sample_table(), tmp_path / "good.nakama-0")

    df, report = load_day(str(tmp_path))

    assert len(df) == 1
    assert report.files_loaded == 1
    assert report.files_failed == 1
    assert "bad.nakama-0" in report.failed_files


def test_load_day_raises_if_no_files_load(tmp_path):
    bad_table = pa.table({"user_id": ["1"]})
    pq.write_table(bad_table, tmp_path / "bad.nakama-0")

    with pytest.raises(RuntimeError):
        load_day(str(tmp_path))


def test_load_files_reads_only_given_paths(tmp_path):
    path_a = tmp_path / "a.nakama-0"
    path_b = tmp_path / "b.nakama-0"
    pq.write_table(_make_sample_table(), path_a)
    pq.write_table(_make_sample_table(), path_b)

    df, report = load_files([str(path_a)])

    assert report.files_loaded == 1
    assert len(df) == 1


def test_parse_filename_splits_user_id_and_match_id():
    user_id, match_id = parse_filename(
        "f4e072fa-b7af-4761-b567-1d95b7ad0108_b71aaad8-aa62-4b3a-8534-927d4de18f22.nakama-0"
    )
    assert user_id == "f4e072fa-b7af-4761-b567-1d95b7ad0108"
    assert match_id == "b71aaad8-aa62-4b3a-8534-927d4de18f22.nakama-0"


def test_parse_filename_handles_bot_ids():
    user_id, match_id = parse_filename("1440_d7e50fad-fb7a-4ed4-932f-e4ca9ff0c97b.nakama-0")
    assert user_id == "1440"
    assert match_id == "d7e50fad-fb7a-4ed4-932f-e4ca9ff0c97b.nakama-0"


def test_parse_filename_raises_on_unexpected_format():
    with pytest.raises(ValueError):
        parse_filename("nounderscoreatall.nakama-0")


def test_build_match_index_groups_files_by_match_id(tmp_path):
    (tmp_path / "f4e072fa-b7af-4761-b567-1d95b7ad0108_match1.nakama-0").touch()
    (tmp_path / "1440_match1.nakama-0").touch()
    (tmp_path / "9999_match2.nakama-0").touch()

    index = build_match_index(str(tmp_path))

    assert set(index.keys()) == {"match1.nakama-0", "match2.nakama-0"}
    assert len(index["match1.nakama-0"]) == 2
    assert len(index["match2.nakama-0"]) == 1
