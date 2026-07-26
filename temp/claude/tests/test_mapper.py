import math

import pandas as pd

from src.mapper import world_to_minimap, add_coords


def test_matches_readme_worked_example():
    # README: AmbroseValley, x=-301.45, z=-355.55 -> pixel_x=78, pixel_y=890
    px, py = world_to_minimap("AmbroseValley", -301.45, -355.55)
    assert math.isclose(px, 78, abs_tol=1)
    assert math.isclose(py, 890, abs_tol=1)


def test_unknown_map_returns_none():
    px, py = world_to_minimap("NotARealMap", 0, 0)
    assert px is None
    assert py is None


def test_clamps_out_of_bounds_coordinates():
    px, py = world_to_minimap("AmbroseValley", -100_000, -100_000)
    assert 0 <= px <= 1024
    assert 0 <= py <= 1024

    px, py = world_to_minimap("AmbroseValley", 100_000, 100_000)
    assert 0 <= px <= 1024
    assert 0 <= py <= 1024


def test_add_coords_matches_scalar_function_for_known_map():
    df = pd.DataFrame({
        "map_id": ["AmbroseValley"],
        "x": [-301.45],
        "z": [-355.55],
    })
    result = add_coords(df)

    expected_px, expected_py = world_to_minimap("AmbroseValley", -301.45, -355.55)
    assert math.isclose(result["pixel_x"].iloc[0], expected_px, abs_tol=0.01)
    assert math.isclose(result["pixel_y"].iloc[0], expected_py, abs_tol=0.01)


def test_add_coords_multiple_maps_in_one_dataframe():
    df = pd.DataFrame({
        "map_id": ["AmbroseValley", "GrandRift", "Lockdown"],
        "x": [-301.45, -280.0, -480.0],
        "z": [-355.55, -270.0, -490.0],
    })
    result = add_coords(df)

    for i, row in result.iterrows():
        expected_px, expected_py = world_to_minimap(row["map_id"], row["x"], row["z"])
        assert math.isclose(row["pixel_x"], expected_px, abs_tol=0.01)
        assert math.isclose(row["pixel_y"], expected_py, abs_tol=0.01)


def test_add_coords_unknown_map_is_null_not_error():
    df = pd.DataFrame({
        "map_id": ["NotARealMap"],
        "x": [0.0],
        "z": [0.0],
    })
    result = add_coords(df)
    assert pd.isna(result["pixel_x"].iloc[0])
    assert pd.isna(result["pixel_y"].iloc[0])
