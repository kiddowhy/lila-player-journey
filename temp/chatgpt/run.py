from pathlib import Path

from src.match_service import MatchService

print("=" * 60)
print("LILA Backend Verification")
print("=" * 60)

service = MatchService(
    Path("player_data/February_10")
)

print("\nLoading dataset...")

matches = service.list_matches()

print(f"✓ Loaded {len(matches)} matches")

largest = service.get_largest_match()

print(f"✓ Largest match: {largest}")

payload = service.get_match(largest)

print(f"✓ Players: {payload['player_count']}")

print("\nBackend verification successful!")