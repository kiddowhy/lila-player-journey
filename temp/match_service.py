
import os
import re
import sys
import json
import pandas as pd
import pyarrow.parquet as pq

MINIMAP_SIZE = 1024

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500},
}


def decode_events(df):
    if "event" in df.columns:
        df["event"] = df["event"].apply(
            lambda x: x.decode("utf-8") if isinstance(x, bytes) else x
        )
    return df


def classify_players(df):
    def classify(uid):
        if pd.isna(uid):
            return "Unknown"
        uid = uid.decode("utf-8") if isinstance(uid, bytes) else str(uid)
        return "Bot" if re.fullmatch(r"\d+", uid) else "Human"

    df["player_type"] = df["user_id"].apply(classify)
    return df


def world_to_minimap(map_id, x, z):
    cfg = MAP_CONFIG.get(map_id)
    if cfg is None:
        return None, None

    u = (x - cfg["origin_x"]) / cfg["scale"]
    v = (z - cfg["origin_z"]) / cfg["scale"]

    px = max(0, min(MINIMAP_SIZE, u * MINIMAP_SIZE))
    py = max(0, min(MINIMAP_SIZE, (1 - v) * MINIMAP_SIZE))
    return round(px, 2), round(py, 2)


def load_day(folder):
    frames = []

    for file in sorted(os.listdir(folder)):
        path = os.path.join(folder, file)

        if not os.path.isfile(path):
            continue

        try:
            df = pq.read_table(path).to_pandas()
            df = decode_events(df)
            df = classify_players(df)

            coords = df.apply(
                lambda r: world_to_minimap(r["map_id"], r["x"], r["z"]),
                axis=1,
            )
            df["pixel_x"] = [c[0] for c in coords]
            df["pixel_y"] = [c[1] for c in coords]

            frames.append(df)

        except Exception as e:
            print(f"Skipping {file}: {e}")

    if not frames:
        raise RuntimeError("No telemetry files loaded.")

    return pd.concat(frames, ignore_index=True)


def get_largest_match(df):
    summary = (
        df.groupby("match_id")
        .agg(players=("user_id", "nunique"),
             rows=("user_id", "count"))
        .sort_values(["players", "rows"], ascending=False)
    )
    return summary.index[0]


def build_match(df, match_id):
    match = df[df["match_id"] == match_id].copy()
    if match.empty:
        raise RuntimeError("Match not found")

    match = match.sort_values("ts")

    payload = {
        "match_id": str(match_id),
        "map_id": str(match["map_id"].iloc[0]),
        "players": []
    }

    for uid, player in match.groupby("user_id"):
        events = []
        for _, row in player.sort_values("ts").iterrows():
            events.append({
                "timestamp": str(row["ts"]),
                "event": row["event"],
                "pixel_x": None if pd.isna(row["pixel_x"]) else float(row["pixel_x"]),
                "pixel_y": None if pd.isna(row["pixel_y"]) else float(row["pixel_y"]),
                "world_x": float(row["x"]),
                "world_y": float(row["y"]),
                "world_z": float(row["z"]),
            })

        payload["players"].append({
            "user_id": str(uid),
            "player_type": player["player_type"].iloc[0],
            "event_count": len(events),
            "events": events,
        })

    return payload


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "player_data/February_10"

    print(f"Loading telemetry from {folder}")
    df = load_day(folder)

    match_id = get_largest_match(df)
    print(f"Selected match: {match_id}")

    payload = build_match(df, match_id)

    filename = f'match_{match_id}.json'
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Exported {filename}")
    print(f"Players: {len(payload['players'])}")
    print(f"Map: {payload['map_id']}")


if __name__ == "__main__":
    main()
