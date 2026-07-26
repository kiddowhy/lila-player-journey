from src.classifier import classify_user


def test_bot():

    assert classify_user("123456") == "Bot"


def test_human():

    assert classify_user(
        "550e8400-e29b-41d4-a716-446655440000"
    ) == "Human"


def test_unknown():

    assert classify_user("") == "Unknown"
    assert classify_user(None) == "Unknown"