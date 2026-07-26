import os
import re
import sys
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


MINIMAP_SIZE = 1024
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

REQUIRED_COLUMNS = ["user_id", "player_type", "match_id", "map_id", "event", "ts", "x", "y", "z"]


# ---------------------------------------
# Decode event bytes into readable strings
# Example: b'Position' -> 'Position'
# ---------------------------------------
def decode_events(df):
    if "event" in df.columns:
        df["event"] = df["event"].apply(
            lambda x: x.decode("utf-8") if isinstance(x, bytes) else x
        )
    return df


# ---------------------------------------
# Classify Human / Bot / Unknown
# ---------------------------------------
def classify_players(df):
    def c(uid):
        if uid is None or (isinstance(uid, float) and pd.isna(uid)):
            return "Unknown"
        if isinstance(uid, bytes):
            uid = uid.decode("utf-8")
        uid = str(uid).strip()
        if uid == "":
            return "Unknown"
        return "Bot" if re.fullmatch(r"\d+", uid) else "Human"

    df["player_type"] = df["user_id"].apply(c)
    return df


# ---------------------------------------
# Load all telemetry files for one day.
# Every file in these folders is parquet
# regardless of extension/naming, so no
# extension filtering is applied. Files
# that fail to parse are logged and
# skipped rather than silently dropped.
# ---------------------------------------
def load_day(folder):
    frames = []
    failed = []

    for file in sorted(os.listdir(folder)):
        p = os.path.join(folder, file)
        if not os.path.isfile(p):
            continue

        try:
            d = pq.read_table(p).to_pandas()
            frames.append(classify_players(decode_events(d)))
        except Exception as e:
            print(f"Failed to load: {file}")
            print(f"  Error: {e}")
            failed.append(file)

    if not frames:
        raise RuntimeError(f"No telemetry could be loaded from {folder}")

    if failed:
        total = len(failed) + len(frames)
        print(f"\nWARNING: {len(failed)} of {total} file(s) failed to load: {failed}")

    combined = pd.concat(frames, ignore_index=True)

    missing = [col for col in REQUIRED_COLUMNS if col not in combined.columns]
    if missing:
        raise RuntimeError(
            f"Loaded data is missing required column(s): {missing}. "
            f"Cannot safely compute minimap coordinates or export JSON."
        )

    return combined


# ---------------------------------------
# Convert world x/z to minimap pixel coordinates.
# Vectorized over the whole dataframe rather than
# calling a per-row Python function, since a single
# day of telemetry can be hundreds of thousands to
# millions of rows.
#
# NOTE: the z-axis is flipped (1 - v) but x is not.
# This is intentional -- it converts from a world
# space where +z is "up/north" to pixel space where
# +y is "down", which is the standard image-coordinate
# convention. x needs no flip since world +x and pixel
# +x both point the same direction. If minimap output
# ever looks mirrored top-to-bottom, check this first.
# ---------------------------------------
def add_coords(df):
    scale = df["map_id"].map(lambda m: MAP_CONFIG.get(m, {}).get("scale"))
    origin_x = df["map_id"].map(lambda m: MAP_CONFIG.get(m, {}).get("origin_x"))
    origin_z = df["map_id"].map(lambda m: MAP_CONFIG.get(m, {}).get("origin_z"))

    unknown_maps = df.loc[scale.isna(), "map_id"].unique()
    if len(unknown_maps) > 0:
        print(f"WARNING: no MAP_CONFIG entry for map(s) {list(unknown_maps)}. "
              f"pixel_x/pixel_y will be null for these rows.")

    u = (df["x"] - origin_x) / scale
    v = (df["z"] - origin_z) / scale

    px = np.clip(u * MINIMAP_SIZE, 0, MINIMAP_SIZE).round(2)
    py = np.clip((1 - v) * MINIMAP_SIZE, 0, MINIMAP_SIZE).round(2)

    # Rows with unknown maps had NaN scale/origin, which propagates
    # NaN through the arithmetic above -- keep them as null rather
    # than a bogus clamped number.
    df["pixel_x"] = px.where(scale.notna())
    df["pixel_y"] = py.where(scale.notna())

    return df


# ---------------------------------------
# Export to JSON. NaN is not valid JSON per spec
# (Python's json module will still write literal
# NaN by default, which most non-Python JSON parsers,
# e.g. in a browser, will reject) -- so NaN values are
# explicitly converted to None before serializing.
# Built as a list of dicts up front (vectorized-ish)
# rather than df.iterrows(), which is one of the
# slowest ways to walk a large dataframe.
# ---------------------------------------
def export_json(df, name):
    export_df = df[[
        "user_id", "player_type", "match_id", "map_id",
        "event", "ts", "x", "y", "z", "pixel_x", "pixel_y"
    ]].copy()

    export_df["ts"] = export_df["ts"].astype(str)

    records = export_df.to_dict("records")

    for r in records:
        r["timestamp"] = r.pop("ts")
        r["world_x"] = None if pd.isna(r["x"]) else float(r.pop("x"))
        r["world_y"] = None if pd.isna(r["y"]) else float(r.pop("y"))
        r["world_z"] = None if pd.isna(r["z"]) else float(r.pop("z"))
        r["pixel_x"] = None if pd.isna(r["pixel_x"]) else float(r["pixel_x"])
        r["pixel_y"] = None if pd.isna(r["pixel_y"]) else float(r["pixel_y"])

    with open(name, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "player_data/February_10"
    day_label = os.path.basename(os.path.normpath(folder))

    print("Loading", folder)
    df = add_coords(load_day(folder))

    print(df[["map_id", "user_id", "player_type", "event", "x", "z", "pixel_x", "pixel_y"]].head(30))

    # Output filenames include the day label so runs for
    # different days don't silently overwrite each other.
    csv_name = f"telemetry_with_minimap_coordinates_{day_label}.csv"
    json_name = f"telemetry_with_minimap_coordinates_{day_label}.json"

    df.to_csv(csv_name, index=False)
    export_json(df, json_name)

    print(f"Done. Wrote {csv_name} and {json_name}")


if __name__ == "__main__":
    main()
