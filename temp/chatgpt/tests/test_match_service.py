from pathlib import Path

from src.match_service import MatchService


def test_match_service():

    service = MatchService(
        Path("player_data/February_10")
    )

    matches = service.list_matches()

    assert len(matches) > 0

    first_match = matches.iloc[0]["match_id"]

    payload = service.get_match(first_match)

    assert payload["match_id"] == first_match
    assert len(payload["players"]) > 0