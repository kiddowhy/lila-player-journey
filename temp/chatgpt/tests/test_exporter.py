import pandas as pd

from src.exporter import dataframe_to_records


def test_export():

    df = pd.DataFrame({
        "x": [1],
        "y": [2],
        "z": [3],
        "ts": ["today"],
    })

    records = dataframe_to_records(df)

    assert isinstance(records, list)
    assert len(records) == 1

    assert records[0]["world_x"] == 1
    assert records[0]["world_y"] == 2
    assert records[0]["world_z"] == 3