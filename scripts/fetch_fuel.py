#!/usr/bin/env python3
"""Weekly fuel prices from the Statistical Office (STATdata cube sp0207ts) into feed/v1/feed.json.

Python 3 stdlib only. Reads the cube's public JSON (POST with an empty query = the default view, the newest ~20 weeks),
merges new weeks into `fuelPrices` (kept: the last 26), prints a Markdown note for the pull request body to stdout.
Prices outside 0,001-9,999 EUR/l are left out and named in the note. Exit 0 whether or not anything changed;
the workflow checks `git diff`.
"""
import json, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://statdata.statistics.sk/public/api/dc/public/sp0207ts/sk"
FEED = Path(__file__).resolve().parent.parent / "feed" / "v1" / "feed.json"
KEEP_WEEKS = 26
# COICOP code -> feed key. CNG (07202107) is priced per kg in the cube, the app's price is per litre: not taken.
FUELS = {"07202102": "petrol", "07202105": "diesel", "07202104": "lpg"}


def fetch() -> dict:
    req = urllib.request.Request(API, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "triplog-data-check/1 (+https://github.com/Bobrokus/triplog-data)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def weeks_from(cube: dict, notes: list):
    found = {}
    for cell in cube["data"]:
        d = cell["dimensions"]
        m = re.match(r"(\d{8})\b", d.get("e_coicop", ""))
        key = FUELS.get(m.group(1)) if m else None
        if key is None or d.get("e_unit") != "Eur / l" or cell.get("value") is None:
            continue
        w = re.match(r"(\d+)\.", d["e_week"])
        year = int(d["e_year"])
        if not w:
            continue
        value = round(float(cell["value"]), 3)
        slot = found.setdefault((year, int(w.group(1))), {})
        if not 0.001 <= value <= 9.999:
            notes.append(f"- {year}/{w.group(1)} {key}: {value} is outside 0,001-9,999 EUR/l, left out")
            continue
        slot[key] = value
    return found


def main() -> int:
    notes: list = []
    cube = fetch()
    found = weeks_from(cube, notes)
    if not found:
        print("No fuel weeks found: the cube's layout changed?", file=sys.stderr)
        return 1
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    weeks = {(w["year"], w["week"]): w for w in feed.get("fuelPrices", [])}
    added = []
    for (year, week), prices in sorted(found.items()):
        if not prices:
            continue
        entry = {"year": year, "week": week, **{k: prices[k] for k in ("petrol", "diesel", "lpg") if k in prices}}
        if weeks.get((year, week)) != entry:
            added.append(f"- {year}/{week}: " + ", ".join(f"{k} {prices[k]}" for k in prices))
            weeks[(year, week)] = entry
    if not added:
        return 0
    feed["fuelPrices"] = [weeks[k] for k in sorted(weeks)][-KEEP_WEEKS:]
    feed["published"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    FEED.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Weekly average fuel prices from the Statistical Office (cube sp0207ts), EUR/l:\n")
    print("\n".join(added))
    if notes:
        print("\nNot taken:\n" + "\n".join(notes))
    print("\nCNG is not proposed: the cube prices it per kg. Merge to publish; nothing reaches the app before.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
