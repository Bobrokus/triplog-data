# triplog-data

Public data for the [TripLog](https://github.com/Bobrokus/triplog) desktop app (opt-in online mode). The app reads
only `feed/v1/feed.json` with one plain HTTPS GET; nothing about the user is sent.

- `feed/v1/feed.json` – curated rates, fuel prices and list versions (`formatVersion` 1; sections are added, never changed).
- `centres/v1/` – municipality centres CSV (added with O2).

Values here are proposals: the app applies a new rate period only after the user confirms it, with the source shown.
