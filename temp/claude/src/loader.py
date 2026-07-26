"""
Loads and validates telemetry parquet files.

load_day() reads every file in a day's folder -- used for validation
scripts and bulk exports. load_files() reads a specific list of file
paths -- used by the match-scoped backend path so a single match lookup
doesn't require reading and parsing an entire day's data.

build_match_index() scans filenames only (no parquet reads) to build a
{match_id: [file_paths]} index, since the filename convention already
encodes both user_id and match_id
(<user_id>_<match_id>.nakama-0). This is what makes load_files()
practical for a backend: given a match_id, look up its files in the
index, then load only those.

Files in this dataset have no .parquet extension but are valid parquet
regardless of naming, so no extension filtering is applied -- every
file is attempted, and failures are logged and skipped rather than
crashing the whole load.
"""

import os
from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import pyarrow.parquet as pq

from .classifier import classify_players
from .models import REQUIRED_COLUMNS, LoadReport


def decode_events(df: pd.DataFrame) -> pd.DataFrame:
    """Decode the event column from bytes to strings, e.g. b'Position' -> 'Position'."""
    if "event" in df.columns:
        df["event"] = df["event"].apply(
            lambda x: x.decode("utf-8", errors="replace")
            if isinstance(x, bytes)
            else x
        )
    return df


def validate_schema(df: pd.DataFrame) -> None:
    """Raise ValueError if df is missing any required column."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")


def _load_one(path: str) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    validate_schema(df)
    df = decode_events(df)
    df = classify_players(df)
    return df


def _load_many(paths: Iterable[str]) -> Tuple[pd.DataFrame, LoadReport]:
    frames = []
    report = LoadReport()

    for path in sorted(paths):
        filename = os.path.basename(path)
        try:
            frames.append(_load_one(path))
            report.files_loaded += 1
        except Exception as e:
            print(f"Skipped {filename}: {e}")
            report.files_failed += 1
            report.failed_files.append(filename)

    if not frames:
        raise RuntimeError("No telemetry files could be loaded")

    return pd.concat(frames, ignore_index=True), report


def load_day(folder: str) -> Tuple[pd.DataFrame, LoadReport]:
    """Load every file in a day's folder. Returns (combined_df, LoadReport)."""
    paths = [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if os.path.isfile(os.path.join(folder, f))
    ]
    if not paths:
        raise RuntimeError(f"No files found in {folder}")

    return _load_many(paths)


def load_files(paths: Iterable[str]) -> Tuple[pd.DataFrame, LoadReport]:
    """Load a specific list of file paths, e.g. the files for one match_id."""
    return _load_many(paths)


def parse_filename(filename: str) -> Tuple[str, str]:
    """
    Split a telemetry filename into (user_id, match_id).

    Filename convention: <user_id>_<match_id>.nakama-0
    match_id already includes the .nakama-0 suffix as part of its value
    (confirmed in the README schema), so this only needs to split on the
    first underscore -- UUIDs use hyphens, never underscores, so this is
    unambiguous for both human (UUID) and bot (numeric) user_ids.
    """
    user_id, _, match_id = filename.partition("_")
    if not match_id:
        raise ValueError(f"Filename does not match <user_id>_<match_id> convention: {filename}")
    return user_id, match_id


def build_match_index(folder: str) -> Dict[str, List[str]]:
    """
    Build a {match_id: [file_paths]} index for a day's folder by parsing
    filenames only -- no parquet files are read. This lets a backend look
    up "which files belong to match X" in O(1) after building the index
    once, instead of loading and filtering an entire day's data per request.
    """
    index: Dict[str, List[str]] = defaultdict(list)

    for filename in sorted(os.listdir(folder)):
        path = os.path.join(folder, filename)
        if not os.path.isfile(path):
            continue
        try:
            _, match_id = parse_filename(filename)
        except ValueError as e:
            print(f"Skipping unindexable file: {e}")
            continue
        index[match_id].append(path)

    return dict(index)
