"""Fill the lexicon field that says what one voice is given for each spelling.

    PYTHONPATH=src python3 tools/lexicon/voice-readings.py tools/lexicon/piper-john.json [--replace]

The speech code sends a voice what calls/lexicon.json has for it and works
nothing out. This script is how that field gets its first value. It reads a
method file typed by hand:

field       the lexicon field to fill, the one enochaeon.json names for the voice
from        the reading it starts from
symbols     a letter of that reading, and the letter the voice wants in its place
one_vowel   the stress mark and the hold mark given to the vowel of a word that
            has only one. The hold is added only when that vowel is short.

A word with more than one vowel gets the symbols and nothing else. Where its
stress falls is not known, and this script does not choose a syllable.

A spelling that already has a string in the field keeps it, so a string
corrected by ear stays corrected. --replace writes every spelling again.

The field lists every spelling of the entry:

    "dee_ipa_piper_john": {"IAD": "/jˈaːd/", "IADO": "/jadoʊ/"}

The report goes to scratch/voice-readings-FIELD.txt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from enochaeon.roots import load_readings
from enochaeon.word_ipa import _VOWELS, _piper_token, _tokens

ROOT = Path(__file__).resolve().parents[2]
LEXICON = ROOT / "calls" / "lexicon.json"
MARKS = {"'": "ˈ", ",": "ˌ"}


def voice_reading(reading: str, method: dict) -> str:
    """One reading as the voice is to be given it, between slashes."""
    tokens = _tokens(reading)
    vowels = [index for index, token in enumerate(tokens) if token.lstrip("',") in _VOWELS]
    only = vowels[0] if len(vowels) == 1 else None
    pieces: list[str] = []
    for index, token in enumerate(tokens):
        mark = MARKS.get(token[0], "")
        sound = token.lstrip("',")
        spoken = _piper_token(sound)
        for letter, wanted in method["symbols"].items():
            spoken = spoken.replace(letter, wanted)
        if index == only:
            mark = mark or method["one_vowel"]["stress"]
            # A short vowel is one espeak letter. A long vowel or a glide is two.
            if len(sound) == 1:
                spoken += method["one_vowel"]["hold"]
        pieces.append(mark + spoken)
    return "/" + "".join(pieces) + "/"


def names(entry: dict) -> list[str]:
    """The spellings of an entry as it writes them, each once."""
    found: list[str] = []
    for name in [entry["root"], *entry.get("variants", [])]:
        if name.lower() not in [other.lower() for other in found]:
            found.append(name)
    return found


def with_field(entry: dict, field: str, after: str, value: dict) -> dict:
    """The entry with the field standing after the reading it was made from."""
    rebuilt: dict = {}
    for key, kept in entry.items():
        if key == field:
            continue
        rebuilt[key] = kept
        if key == after:
            rebuilt[field] = value
    rebuilt.setdefault(field, value)
    return rebuilt


def main(arguments: list[str]) -> None:
    replace = "--replace" in arguments
    paths = [argument for argument in arguments if argument != "--replace"]
    if len(paths) != 1:
        raise SystemExit(__doc__)
    method = json.loads((ROOT / paths[0]).read_text(encoding="utf-8"))
    field, source = method["field"], method["from"]
    readings = load_readings(source)
    entries = json.loads(LEXICON.read_text(encoding="utf-8"))
    written, kept, differ = 0, 0, []
    for index, entry in enumerate(entries):
        had = entry.get(field) or {}
        value: dict[str, str] = {}
        for name in names(entry):
            made = voice_reading(readings[name.lower()], method)
            if name in had and not replace:
                value[name] = had[name]
                kept += 1
                if had[name] != made:
                    differ.append(f"  {name:<16} lexicon {had[name]:<28} method {made}")
            else:
                value[name] = made
                written += 1
        entries[index] = with_field(entry, field, source, value)
    LEXICON.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"{field}, made from {source} by {paths[0]}",
        f"spellings written: {written}",
        f"spellings that had a string and kept it: {kept}",
        f"kept strings that are not what the method would write: {len(differ)}",
        *differ,
    ]
    report = ROOT / "scratch" / f"voice-readings-{field}.txt"
    report.parent.mkdir(exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {report.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
