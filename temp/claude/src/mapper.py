"""
Converts world (x, z) coordinates to minimap pixel coordinates.

world_to_minimap() is the scalar reference implementation (also used
directly by tests to check against the README's worked example).
add_coords() is the vectorized DataFrame version -- it must always
produce the same result as world_to_minimap() for a single row; see
tests/test_mapper.py for a check that keeps the two in sync.
"""

import numpy as np
import pandas as pd

from .models import MAP_CONFIG, MINIMAP_SIZE


def world_to_minimap(map_id: str, x: float, z: float):
    """
    Convert a single world (x, z) coordinate to minimap pixel coordinates
    (pixel_x, pixel_y). Returns (None, None) if map_id has no known
    MAP_CONFIG entry.

    NOTE: z is flipped (1 - v) but x is not. This is intentional -- it
    converts from a world space where +z is "up/north" to pixel space
    where +y is "down" (standard image-coordinate convention). x needs
    no flip since world +x and pixel +x point the same direction. If
    minimap output ever looks mirrored top-to-bottom, check this first.
    """
    cfg = MAP_CONFIG.get(map_id)
    if cfg is None:
        return None, None

    u = (x - cfg["origin_x"]) / cfg["scale"]
    v = (z - cfg["origin_z"]) / cfg["scale"]

    px = max(0, min(MINIMAP_SIZE, u * MINIMAP_SIZE))
    py = max(0, min(MINIMAP_SIZE, (1 - v) * MINIMAP_SIZE))
    return round(px, 2), round(py, 2)


def add_coords(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized version of world_to_minimap() applied to an entire
    DataFrame. Adds pixel_x / pixel_y columns. Rows with an unrecognized
    map_id get null pixel_x/pixel_y and trigger a printed warning rather
    than failing silently.
    """
    df = df.copy()

    # .astype(float) forces these to numeric dtype even when every row has
    # an unrecognized map_id (all values None) -- without it, pandas infers
    # object dtype for an all-None column, and Series.round() later raises
    # TypeError on object dtype instead of just producing NaN.
    scale = df["map_id"].map(lambda m: MAP_CONFIG.get(m, {}).get("scale")).astype(float)
    origin_x = df["map_id"].map(lambda m: MAP_CONFIG.get(m, {}).get("origin_x")).astype(float)
    origin_z = df["map_id"].map(lambda m: MAP_CONFIG.get(m, {}).get("origin_z")).astype(float)

    unknown_maps = df.loc[scale.isna(), "map_id"].unique()
    if len(unknown_maps) > 0:
        print(f"WARNING: no MAP_CONFIG entry for map(s) {list(unknown_maps)}. "
              f"pixel_x/pixel_y will be null for these rows.")

    u = (df["x"] - origin_x) / scale
    v = (df["z"] - origin_z) / scale

    px = np.clip(u * MINIMAP_SIZE, 0, MINIMAP_SIZE).round(2)
    py = np.clip((1 - v) * MINIMAP_SIZE, 0, MINIMAP_SIZE).round(2)

    # Rows with unknown maps had NaN scale/origin, which propagates NaN
    # through the arithmetic above -- keep them as null rather than a
    # bogus clamped number.
    df["pixel_x"] = px.where(scale.notna())
    df["pixel_y"] = py.where(scale.notna())

    return df
