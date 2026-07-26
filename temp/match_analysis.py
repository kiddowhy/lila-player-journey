import os
import re
import sys

import pandas as pd
import pyarrow.parquet as pq


# ---------------------------------------
# Decode event bytes into readable strings
# Example: b'Position' -> 'Position'
# ---------------------------------------
def decode_events(df):
    if "event" in df.columns:
        df["event"] = df["event"].apply(
            lambda x: x.decode("utf-8")
            if isinstance(x, bytes)
            else x
        )

    return df


# ---------------------------------------
# Classify Human / Bot / Unknown
# Numeric user_id -> Bot
# UUID user_id    -> Human
# None/NaN/empty  -> Unknown
# Handles byte-encoded user_ids (e.g. b'12345')
# so numeric bot IDs aren't misclassified as Human.
# ---------------------------------------
def classify_players(df):
    def _classify(user_id):
        if user_id is None or (isinstance(user_id, float) and pd.isna(user_id)):
            return "Unknown"

        if isinstance(user_id, bytes):
            user_id = user_id.decode("utf-8")

        user_id = str(user_id).strip()

        if user_id == "":
            return "Unknown"

        return "Bot" if re.fullmatch(r"\d+", user_id) else "Human"

    df["player_type"] = df["user_id"].apply(_classify)

    return df


# ---------------------------------------
# Load all telemetry files from one day
# Only reads .parquet files (skips .crc,
# .json, .DS_Store, and other stray files
# instead of silently attempting and failing
# to parse them).
# ---------------------------------------
def load_day(folder):
    frames = []
    failed = []

    for file in sorted(os.listdir(folder)):

        filepath = os.path.join(folder, file)

        if not os.path.isfile(filepath):
            continue

        try:
            table = pq.read_table(filepath)

            player_df = table.to_pandas()

            player_df = decode_events(player_df)
            player_df = classify_players(player_df)

            frames.append(player_df)

        except Exception as e:
            print(f"Failed to load: {file}")
            print(e)
            failed.append(file)

    if not frames:
        raise RuntimeError(
            f"No parquet files could be loaded from {folder}"
        )

    if failed:
        print(f"\nWARNING: {len(failed)} file(s) failed to load out of "
              f"{len(failed) + len(frames)} total: {failed}")

    return pd.concat(frames, ignore_index=True)


# ---------------------------------------
# MAIN
# ---------------------------------------

# Show full tables instead of letting pandas truncate
# large player/event summaries.
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)

# Allow the folder to be passed as a CLI arg so this
# script isn't hardcoded to a single day.
folder = sys.argv[1] if len(sys.argv) > 1 else "player_data/February_10"

print(f"\nLoading {folder}...")

df = load_day(folder)

print(f"Loaded {len(df):,} rows")

# Normalize ts to a proper sortable dtype if it isn't already.
# (If ts arrives as a string column, sorting would otherwise be
# lexicographic rather than chronological.)
if not pd.api.types.is_numeric_dtype(df["ts"]) and not pd.api.types.is_datetime64_any_dtype(df["ts"]):
    try:
        df["ts"] = pd.to_datetime(df["ts"])
    except Exception as e:
        print(f"WARNING: could not convert ts to datetime, sort order may be incorrect: {e}")


# ---------------------------------------
# Find player count for every match
# ---------------------------------------

match_summary = (
    df.groupby("match_id")
      .agg(
          players=("user_id", "nunique"),
          rows=("user_id", "count"),
          map=("map_id", "first")
      )
      .sort_values("players", ascending=False)
)

print("\n========================================")
print("TOP 20 MATCHES BY PLAYER COUNT")
print("========================================")

print(match_summary.head(20))


# ---------------------------------------
# Pick the biggest match automatically
# NOTE: if multiple matches tie for the most
# players, this picks whichever is first after
# sort_values (a stable sort, so ties resolve by
# original row order in match_summary -- arbitrary
# but deterministic across runs of the same data).
# ---------------------------------------

match_id = match_summary.index[0]

print("\n========================================")
print("SELECTED MATCH")
print("========================================")

print(match_id)


# ---------------------------------------
# Build complete match
# ---------------------------------------

match_df = (
    df[df["match_id"] == match_id]
    .sort_values("ts")
    .reset_index(drop=True)
)


# ---------------------------------------
# Match Summary
# ---------------------------------------

print("\n========================================")
print("MATCH SUMMARY")
print("========================================")

print(f"Rows           : {len(match_df):,}")

print(f"Map            : {match_df['map_id'].iloc[0]}")

print(f"Unique Players : {match_df['user_id'].nunique()}")

print(f"Unique Humans  : {match_df[match_df['player_type']=='Human']['user_id'].nunique()}")

print(f"Unique Bots    : {match_df[match_df['player_type']=='Bot']['user_id'].nunique()}")

unknown_count = match_df[match_df['player_type'] == 'Unknown']['user_id'].nunique()
if unknown_count:
    print(f"Unique Unknown : {unknown_count}")


# ---------------------------------------
# Event counts
# ---------------------------------------

print("\n========================================")
print("EVENT DISTRIBUTION")
print("========================================")

print(match_df["event"].value_counts())


# ---------------------------------------
# Player summary
# ---------------------------------------

print("\n========================================")
print("PLAYERS")
print("========================================")

player_summary = (
    match_df.groupby(["user_id", "player_type"])
            .agg(
                events=("event", "count"),
                first_event=("ts", "min"),
                last_event=("ts", "max")
            )
            .sort_values("events", ascending=False)
)

print(player_summary)


# ---------------------------------------
# First 30 chronological events
# ---------------------------------------

print("\n========================================")
print("FIRST 30 EVENTS")
print("========================================")

print(
    match_df[
        [
            "ts",
            "user_id",
            "player_type",
            "event",
            "map_id",
            "x",
            "z"
        ]
    ].head(30)
)


# ---------------------------------------
# Last 30 chronological events
# ---------------------------------------

print("\n========================================")
print("LAST 30 EVENTS")
print("========================================")

print(
    match_df[
        [
            "ts",
            "user_id",
            "player_type",
            "event",
            "map_id",
            "x",
            "z"
        ]].tail(30)
)


print("\nAnalysis Complete.")