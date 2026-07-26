"""
quick_start.py

Validates the LILA telemetry dataset: loads one day's telemetry,
decodes events, classifies humans vs bots, and checks assumptions
about the data against the README.
"""

import os
import re
import pyarrow.parquet as pq
import pandas as pd

DAY_FOLDER = "player_data/February_10"

MOVEMENT_EVENTS = {"Position", "BotPosition"}

EXPECTED_EVENTS = {
    "Position", "BotPosition",
    "Kill", "Killed", "BotKill", "BotKilled",
    "KilledByStorm", "Loot",
}

REQUIRED_COLUMNS = {
    "user_id", "match_id", "map_id",
    "x", "y", "z", "ts", "event",
}


def decode_events(df: pd.DataFrame) -> pd.DataFrame:
    if "event" in df.columns:
        df["event"] = df["event"].apply(
            lambda x: x.decode("utf-8", errors="replace")
            if isinstance(x, bytes)
            else x
        )
    return df


def classify_players(df: pd.DataFrame) -> pd.DataFrame:
    def classify(uid):
        uid = str(uid).strip()
        if re.fullmatch(r"\d+", uid):
            return "Bot"
        if re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            uid,
        ):
            return "Human"
        return "Unknown"

    df["player_type"] = df["user_id"].apply(classify)
    return df


def validate_schema(df):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns: {sorted(missing)}")


def load_day(folder):
    """Load and validate every file in a day's folder. Returns (df, files_loaded)."""
    frames = []

    for filename in sorted(os.listdir(folder)):
        path = os.path.join(folder, filename)

        if not os.path.isfile(path):
            continue

        try:
            df = pq.read_table(path).to_pandas()
            validate_schema(df)
            df = decode_events(df)
            df = classify_players(df)
            frames.append(df)

        except Exception as e:
            print(f"Skipped {filename}")
            print(f"  {e}")

    if not frames:
        raise RuntimeError(f"No telemetry files loaded from {folder}")

    return pd.concat(frames, ignore_index=True), len(frames)


def print_ts_ranges(df, sample_size=3):
    
    match_ids = df["match_id"].drop_duplicates()
    sample = match_ids.sample(min(sample_size, len(match_ids)), random_state=42)

    print("\nSample match ts ranges:")
    for match_id in sample:
        ts = df.loc[df["match_id"] == match_id, "ts"]
        print(f"  {match_id}: {ts.min()} to {ts.max()} (span: {ts.max() - ts.min()})")


def main():
    print(f"Loading {DAY_FOLDER}...\n")
    df, files_loaded = load_day(DAY_FOLDER)

    print("========== DATASET SUMMARY ==========")
    print(f"Rows: {len(df):,}")
    print(f"Players: {df['user_id'].nunique()}")
    print(f"Matches: {df['match_id'].nunique()}")
    print(f"Files loaded: {files_loaded}")
    print(f"Avg files per match: {files_loaded / df['match_id'].nunique():.2f}")

    print_ts_ranges(df)

    print("\nMaps:")
    print(df["map_id"].value_counts())

    print("\nPlayer Types:")
    player_type_counts = df.groupby("player_type")["user_id"].nunique()
    print(player_type_counts)

    if player_type_counts.get("Unknown", 0) > 0:
        print(f"\nWARNING: {player_type_counts['Unknown']} user_id(s) classified "
              f"as Unknown (neither numeric nor a valid UUID) -- worth inspecting.")

    print("\nEvent Counts:")
    print(df["event"].value_counts())

    unknown_events = set(df["event"].unique()) - EXPECTED_EVENTS
    if unknown_events:
        print("\nUnknown Events:")
        print(sorted(unknown_events))
    else:
        print("\nAll events are recognized.")

    gameplay = df[~df["event"].isin(MOVEMENT_EVENTS)]
    print("\nGameplay Events:")
    print(gameplay["event"].value_counts())

    print("\nTimestamp Info:")
    print("dtype :", df["ts"].dtype)
    print("min   :", df["ts"].min())
    print("max   :", df["ts"].max())

    print("\nPreview:")
    print(df.head())

    print("\nQuick start validation completed successfully.")


if __name__ == "__main__":
    main()