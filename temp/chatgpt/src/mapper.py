"""
mapper.py

World coordinate to minimap coordinate conversion.
"""

import numpy as np

from src.config import MAP_CONFIG
from src.config import MINIMAP_SIZE


def world_to_minimap(map_name, x, z):

    if map_name not in MAP_CONFIG:
        return None, None

    cfg = MAP_CONFIG[map_name]

    px = (
        (x - cfg["origin_x"])
        / cfg["scale"]
    ) * MINIMAP_SIZE

    py = (
        1 -
        ((z - cfg["origin_z"])
        / cfg["scale"])
    ) * MINIMAP_SIZE

    px = float(np.clip(px, 0, MINIMAP_SIZE))
    py = float(np.clip(py, 0, MINIMAP_SIZE))

    return px, py


def add_coords(df):

    df = df.copy()

    pixel_x = []
    pixel_y = []

    for _, row in df.iterrows():

        x, y = world_to_minimap(
            row["map_id"],
            row["x"],
            row["z"]
        )

        pixel_x.append(x)
        pixel_y.append(y)

    df["pixel_x"] = pixel_x
    df["pixel_y"] = pixel_y

    return df