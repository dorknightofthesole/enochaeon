"""List the words of calls/journal/ that need a second look.

Writes two lists to scratch/journal-lists.txt:

  uncertain     every word whose status is not `printed` or `corrected`
  note differs  every `printed` or `corrected` word whose letters are not
                spelled out in Dee's note beside it. The test is mechanical:
                the note is cut at its punctuation, and the word passes if its
                letters equal some run of whole words in one piece of the note,
                with J read as I, Y as I, V as U, and 'zod' as Z. A note can
                respell a word for sound, so a word on this list is not shown
                to be wrong; it is a word where the printing gives two
                spellings, or a note that does not spell the word at all.

The same two functions are imported by the docs builder so the lists in
docs/call-texts.md are the ones printed here.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "calls" / "journal"
OUT = ROOT / "scratch" / "journal-lists.txt"
SURE = {"printed", "corrected"}
_MARGIN = re.compile(r"\[margin[^\]]*\]")
_BREAK = re.compile(r"[;.,:()\[\]-]")


def stems() -> list[str]:
    return [f"{number:02d}" for number in range(1, 19)] + ["aethyrs"]


def load(stem: str) -> dict:
    return json.loads((JOURNAL / f"{stem}.json").read_text(encoding="utf-8"))


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text).upper()
    text = "".join(char for char in text if "A" <= char <= "Z")
    return text.replace("J", "I").replace("Y", "I").replace("V", "U")


def note_letters(entry: dict) -> str:
    return fold(_MARGIN.sub(" ", entry["note"]))


def note_spellings(entry: dict) -> set[str]:
    """Every run of whole words in the note, folded, with 'zod' read as Z."""
    found: set[str] = set()
    for piece in _BREAK.split(_MARGIN.sub(" ", entry["note"])):
        words = [fold(word) for word in piece.split()]
        words = ["Z" if word == "ZOD" else word for word in words]
        for first in range(len(words)):
            for last in range(first + 1, len(words) + 1):
                found.add("".join(words[first:last]))
    found.discard("")
    return found


def note_differs(entry: dict) -> bool:
    if entry["status"] not in SURE or entry.get("repeat_of"):
        return False
    if not note_letters(entry):
        return False
    return fold(entry["letters"]) not in note_spellings(entry)


def uncertain(entry: dict) -> bool:
    return entry["status"] not in SURE


def where(entry: dict) -> str:
    return f"p. {entry['page']}" if entry.get("page") else "not printed"


def rows():
    """Yield (call label, word number, entry) for every word and Aethyr name."""
    for stem in stems():
        data = load(stem)
        label = "Aethyr call" if stem == "aethyrs" else f"Call {int(stem)}"
        for number, entry in enumerate(data["words"], start=1):
            yield label, number, entry
        for number, entry in enumerate(data.get("names", []), start=1):
            yield "Aethyr name", number, entry


def main() -> int:
    lines = ["UNCERTAIN: status is not printed or corrected", ""]
    counts: dict[str, int] = {}
    for label, number, entry in rows():
        if not uncertain(entry):
            continue
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        extra = []
        if entry.get("column"):
            extra.append(f"column {entry['column']!r}")
        if entry.get("other"):
            extra.append(f"other {entry['other']}")
        if entry.get("repeat_of"):
            extra.append(f"repeats Call {entry['repeat_of']['call']} word {entry['repeat_of']['word']}")
        if entry["note"]:
            extra.append(f"note {entry['note']!r}")
        lines.append(f"{label} word {number:3d}  {where(entry):12s} {entry['status']:11s} {entry['letters']:14s} "
                     + "; ".join(extra))
    lines += ["", f"counts: {counts}", "", "", "NOTE DIFFERS: printed or corrected, but Dee's note does not spell the same letters", ""]
    total = 0
    for label, number, entry in rows():
        if not note_differs(entry):
            continue
        total += 1
        lines.append(f"{label} word {number:3d}  {where(entry):12s} {entry['letters']:14s} "
                     f"column {entry.get('column', entry['letters'])!r}; note {entry['note']!r}")
    lines += ["", f"count: {total}"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: uncertain {sum(counts.values())} {counts}, note differs {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
