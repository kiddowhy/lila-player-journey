from src.mapper import world_to_minimap


def test_unknown_map():

    x, y = world_to_minimap(
        "UnknownMap",
        0,
        0,
    )

    assert x is None
    assert y is None


def test_valid_coordinate():

    x, y = world_to_minimap(
        "AmbroseValley",
        0,
        0,
    )

    if x is not None:
        assert 0 <= x <= 1024

    if y is not None:
        assert 0 <= y <= 1024