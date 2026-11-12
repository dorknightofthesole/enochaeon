"""Give every spelling in calls/lexicon.json a dee_ipa of its own.

    PYTHONPATH=src python3 tools/lexicon/letter-readings.py

The speech code reads dee_ipa from the lexicon and works nothing out. This
script is how a spelling gets its first value: the letter rule, applied to
the letters of the spelling. The root of an entry with dee_says is made from
the letters of that note. The rule's table is src/enochaeon/data/call_letters.json.

A spelling that already has a string keeps it. An entry whose dee_ipa is one
string, the older form, keeps that string as the reading of its root.

The field lists every spelling of the entry:

    "dee_ipa": {"IAD": "/j.æ.d/", "IADO": "/j.æ.d.oʊ/"}

A string made here is what the rule says from the letters. It is not
evidence of how the word is pronounced.

The report goes to scratch/letter-readings.txt. A run that makes nothing
leaves the last report alone. Run
tools/lexicon/voice-readings.py after it, so the voice has a string for each
new spelling too.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from enochaeon.enochian import letter_ipa

ROOT = Path(__file__).resolve().parents[2]
LEXICON = ROOT / "calls" / "lexicon.json"
FIELD = "dee_ipa"
NOTE = "dee_says"


def names(entry: dict) -> list[str]:
    """The spellings of an entry as it writes them, each once. The root is first."""
    found: list[str] = []
    for name in [entry["root"], *entry.get("variants", [])]:
        if name.lower() not in [other.lower() for other in found]:
            found.append(name)
    return found


def main(arguments: list[str]) -> None:
    if arguments:
        raise SystemExit(__doc__)
    entries = json.loads(LEXICON.read_text(encoding="utf-8"))
    kept, made = 0, []
    for entry in entries:
        had = entry.get(FIELD) or {}
        if isinstance(had, str):
            had = {entry["root"]: had}
        value: dict[str, str] = {}
        for index, name in enumerate(names(entry)):
            if name in had:
                value[name] = had[name]
                kept += 1
                continue
            letters = entry[NOTE] if index == 0 and entry.get(NOTE) else name
            if not letters.isalpha():
                raise SystemExit(f"{entry['root']}: {letters!r} is not letters.")
            value[name] = letter_ipa(letters)
            made.append(f"  {name:<16} {value[name]:<40} entry {entry['root']}")
        entry[FIELD] = value
    LEXICON.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"{FIELD} for every spelling in {LEXICON.relative_to(ROOT)}",
        f"spellings that had a string and kept it: {kept}",
        f"spellings given the letter rule's string: {len(made)}",
        *made,
    ]
    report = ROOT / "scratch" / "letter-readings.txt"
    report.parent.mkdir(exist_ok=True)
    print("\n".join(lines[:3]))
    if not made and report.exists():
        print(f"\nmade nothing, so {report.relative_to(ROOT)} was left alone")
        return
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {report.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
