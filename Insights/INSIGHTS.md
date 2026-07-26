then the match ID is already encoded in the filename.

load_match() can do:

Scan filenames

        │
        ▼
user1_MATCH123.nakama-0
user2_MATCH123.nakama-0
user3_MATCH123.nakama-0
user4_MATCH456.nakama-0

        │
        ▼
Read only MATCH123 files

        │
        ▼
Return match dataframe

If a typical match has 15 players:

Read ~15 files instead of 1,243.
Only allocate memory for that match.
Much faster response time.


The README's claim that "a match with 10 humans and 40 bots produces 50 files" is not representative of this dataset at all — the real average is roughly 1–2 files per match, not 50.