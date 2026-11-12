"""Build calls/sloane/ from the reading of Sloane 3191.

Reads tools/sloane/sloane-reading.json (the manuscript as it was read, typed by
hand) and calls/journal/ (the 1659 printing). Writes calls/sloane/01.json to
18.json and calls/sloane/aethyrs.json. The call files are written from these
by tools/journal/rewrite-calls.py.

The manuscript is the first source. The journal is the second, and it is used
here for three things only:

  small gaps   Where the reading has a small gap with no tie-stroke, the eye
               cannot say whether a new word begins. The gap is a word break
               where its width on the page shows one, by the measure of
               tools/sloane/sloane-gaps.py. Where the width does not show
               one, the gap is a word break only where the journal breaks at
               that very letter. Otherwise the letters on both sides stay one
               word.
  unsure       Where the reading marks a letter as not read with certainty,
               the word takes the journal's letters at that place and its
               status is `unsure`.
  differs      Each word says which journal words stand at its place and how
               the two differ.

Per word:

  letters   the letters the call file has
  written   the word as typed in the reading: accents where they were seen,
            a hyphen for a tie-stroke, an underscore for a small gap, a `?`
            after a letter that was not read with certainty
  status    read     the letters are the reading's
            unsure   the reading has a `?`; the letters are the journal's
  journal   the numbers of the journal words at this place, counted from 1 as
            in docs/sloane-diff.txt. Empty when the word is only in the
            manuscript.
  differs   how this word differs from the journal words at its place, or
            nothing when they are the same letters as one word
  checked   what Eddie saw at this place, copied from sloane-places.json once
            it is filled in there

`journal_only` lists the journal words that are not in the manuscript.

The reading is one reading by eye and has not been confirmed. This script
decides nothing about how any word is pronounced.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JOURNAL = ROOT / "calls" / "journal"
DEST = ROOT / "calls" / "sloane"
READING = HERE / "sloane-reading.json"
PLACES = HERE / "sloane-places.json"
MANUSCRIPT = "British Library MS Sloane 3191, 48 Claves Angelicae, in John Dee's hand"
SCAN = "docs/998222247-Dee-MS-Sloane-3191.pdf"
READ_BY = "tools/sloane/sloane-reading.json: one reading by eye, not confirmed"


def sheets_module():
    spec = importlib.util.spec_from_file_location("sloane_sheets", HERE / "sloane-sheets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(sheets, entries: list[dict], reading: dict, checked: dict[int, str], after_checked: dict[int, str],
          call: str | None = None):
    """Return (words, journal_only) for one list of journal entries and its reading.

    `call` names the call whose measured gaps settle the small gaps of the reading.
    """
    journal = [entry["letters"].lower() for entry in entries]
    words = sheets.reading_words(journal, reading, call)
    places, _ = sheets.line_up(journal, words)
    rows, _ = sheets.compare(journal, words)
    at: list[list[int]] = [[] for _ in words]
    for journal_index, found in enumerate(places):
        for place in found:
            at[place].append(journal_index)

    out: list[dict] = []
    last_journal = -1
    for index, written in enumerate(words):
        here = at[index]
        unsure = "?" in written
        if unsure and here:
            letters = "".join(journal[number] for number in here)
        else:
            letters = sheets.plain(written)
        kinds: list[str] = []
        for number in here:
            mark, kind = rows[number][1], rows[number][2]
            if mark == "differs" and kind not in kinds:
                kinds.append(kind)
        entry = {
            "letters": letters.upper(),
            "written": written,
            "status": "unsure" if unsure else "read",
            "journal": [number + 1 for number in here],
            "differs": "; ".join(kinds) if here else "only in the manuscript",
        }
        seen = [checked[number + 1] for number in here if checked.get(number + 1)]
        if not here and after_checked.get(last_journal + 1):
            seen.append(after_checked[last_journal + 1])
        if seen:
            entry["checked"] = seen[0]
        if here:
            last_journal = here[-1]
        out.append(entry)

    journal_only = [
        {"journal": number + 1, "letters": entries[number]["letters"], "status": entries[number]["status"],
         "page": entries[number].get("page")}
        for number, found in enumerate(places) if not found
    ]
    return out, journal_only


def main() -> int:
    sheets = sheets_module()
    reading = json.loads(READING.read_text(encoding="utf-8"))["calls"]
    places = json.loads(PLACES.read_text(encoding="utf-8"))["places"]
    DEST.mkdir(parents=True, exist_ok=True)
    totals = {"words": 0, "unsure": 0, "differs": 0, "only in the manuscript": 0, "journal only": 0}
    for stem in [f"{number:02d}" for number in range(1, 19)] + ["aethyrs"]:
        journal = json.loads((JOURNAL / f"{stem}.json").read_text(encoding="utf-8"))
        read = reading[stem]
        checked = {number: place["checked"] for place in places if place["call"] == stem
                   for number in place.get("words", [])}
        after_checked = {number: place["checked"] for place in places if place["call"] == stem
                         for number in place.get("after", [])}
        words, journal_only = build(sheets, journal["words"], read, checked, after_checked, stem)
        data = {
            "call": journal["call"],
            "manuscript": MANUSCRIPT,
            "scan": SCAN,
            "where": read["where"],
            "reading": READ_BY,
            "remarks": read.get("remarks", []),
            "words": words,
            "journal_only": journal_only,
        }
        counted = list(words)
        if stem == "aethyrs":
            slots = [index for index, word in enumerate(words) if journal["name_word"] + 1 in word["journal"]]
            if len(slots) != 1:
                raise ValueError(f"the place of the Aethyr's name was found {len(slots)} times")
            names, names_only = build(sheets, journal["names"], {"words": read["names"]}, {}, {})
            if len(names) != len(journal["names"]) or names_only:
                raise ValueError("the thirty names do not line up one for one with the journal's")
            data["name_word"] = slots[0]
            data["names_where"] = read["names_where"]
            data["names"] = names
            counted += names
        (DEST / f"{stem}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        totals["words"] += len(counted)
        totals["unsure"] += sum(1 for word in counted if word["status"] == "unsure")
        totals["differs"] += sum(1 for word in counted if word["differs"] and word["journal"])
        totals["only in the manuscript"] += sum(1 for word in counted if not word["journal"])
        totals["journal only"] += len(journal_only)
    print(f"wrote 19 files in {DEST.relative_to(ROOT)}: " + ", ".join(f"{count} {name}" for name, count in totals.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
