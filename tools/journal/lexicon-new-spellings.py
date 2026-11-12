"""Give every spelling in the rewritten call files an entry in calls/lexicon.json.

A new entry has the shape of the generated entries already in the file: the
spelling, itself as its only variant, no English, a dee_ipa made by the letter
rule, an empty golden_dawn_ipa, and the call files that have the spelling. No
entry is removed and no existing reading or English is changed.

The letter-rule dee_ipa is what the rule says from the letters. It is not
evidence of how the word is pronounced. Once stored, the lexicon string is
what is spoken. A new entry has no string for a Piper voice until
tools/lexicon/voice-readings.py is run.

An Aethyr file is named by the spelling of its name, so a pass can rename it.
Where an entry names a file by a name it no longer has, and the entry's
spelling is in the file that now has that number, the name is updated.

Writes scratch/lexicon-new-spellings-PASS.txt: the entries added, the entries
whose spelling was in a call file before either pass and is in none now, and
the generated entries whose spelling is in no call file now. The call files as
they were before either pass are in tools/journal/calls-before/. A run that
adds nothing leaves the list alone. A run that adds entries where a list
already exists writes below it.

Usage: PYTHONPATH=src python3 tools/journal/lexicon-new-spellings.py PASS
PASS names the record the call files were just written from: sloane or journal.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from enochaeon.enochian import call_files, letter_ipa

ROOT = Path(__file__).resolve().parents[2]
CALLS = ROOT / "calls"
BEFORE = Path(__file__).resolve().parent / "calls-before"
LEXICON = CALLS / "lexicon.json"
PASSES = {"sloane": "the reading of Sloane 3191 (calls/sloane/)", "journal": "the journal data (calls/journal/)"}
_WORD = re.compile(r"[A-Za-z]+")


def spelling_of(name: str) -> str:
    return "".join(character for character in name.lower() if character.isalpha())


def spellings_in(folder: Path) -> dict[str, list[str]]:
    """Each spelling in the call files of a folder, with the files that have it."""
    found: dict[str, list[str]] = {}
    for path in call_files(folder):
        for word in _WORD.findall(path.read_text(encoding="utf-8")):
            stems = found.setdefault(word.lower(), [])
            if path.stem not in stems:
                stems.append(path.stem)
    return found


def main(arguments: list[str]) -> int:
    if len(arguments) != 1 or arguments[0] not in PASSES:
        print(__doc__)
        return 2
    report = ROOT / "scratch" / f"lexicon-new-spellings-{arguments[0]}.txt"
    current = {path.stem.split("-")[0]: path.stem for path in call_files(CALLS) if "-" in path.stem}
    entries = json.loads(LEXICON.read_text(encoding="utf-8"))
    now = spellings_in(CALLS)
    before = spellings_in(BEFORE)
    listed: dict[str, dict] = {}
    for entry in entries:
        for name in [entry["root"], *entry["variants"]]:
            listed.setdefault(spelling_of(name), entry)

    renamed = 0
    for entry in entries:
        names = {spelling_of(name) for name in [entry["root"], *entry["variants"]]}
        sources = []
        for source in entry["sources"]:
            new = current.get(source.split("-")[0]) if "-" in source else None
            if new and new != source and any(new in now.get(name, []) for name in names):
                source = new
                renamed += 1
            if source not in sources:
                sources.append(source)
        entry["sources"] = sources

    added = []
    for spelling in sorted(now):
        if spelling in listed:
            continue
        entry = {
            "root": spelling.upper(),
            "variants": [spelling.upper()],
            "english_glosses": [],
            "dee_ipa": {spelling.upper(): letter_ipa(spelling)},
            "golden_dawn_ipa": "",
            "sources": now[spelling],
        }
        place = next((index for index, other in enumerate(entries) if other["root"] > entry["root"]), len(entries))
        entries.insert(place, entry)
        added.append(entry)
    LEXICON.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dropped = sorted(spelling for spelling in before if spelling not in now and spelling in listed)
    unused = sorted(
        spelling_of(entry["root"]) for entry in entries
        if not entry["english_glosses"] and entry["variants"] == [entry["root"]] and not entry["golden_dawn_ipa"]
        and spelling_of(entry["root"]) not in now
    )
    lines = [
        f"Lexicon entries after the call files were rewritten from {PASSES[arguments[0]]}.",
        "",
        f"ADDED: {len(added)} entries, one for each spelling in a call file that had none.",
        "Each has no English, and a dee_ipa that is the letter rule applied to the spelling.",
        "The letter rule is what the code says from the letters. The pronunciation of these words is not known from it.",
        "",
    ]
    for entry in added:
        files = entry["sources"]
        where = f"{files[0]} to {files[-1]} ({len(files)} files)" if len(files) > 4 else ", ".join(files)
        lines.append(f"  {entry['root']:16} {entry['dee_ipa'][entry['root']]:40} {where}")
    lines += [
        "",
        f"NO LONGER USED: {len(dropped)} spellings were in a call file before either pass and are in none now.",
        "Their entries are kept as they were. The files named are the ones that had the spelling before.",
        "",
    ]
    for spelling in dropped:
        entry = listed[spelling]
        role = "entry" if spelling_of(entry["root"]) == spelling else f"variant of {entry['root']}"
        files = before[spelling]
        where = f"{files[0]} to {files[-1]} ({len(files)} files)" if len(files) > 4 else ", ".join(files)
        english = "; ".join(entry["english_glosses"]) or "-"
        lines.append(f"  {spelling.upper():16} {role:24} English: {english:40} was in {where}")
    lines += [
        "",
        f"GENERATED AND NOT USED: {len(unused)} entries have no English, were made from a spelling alone, "
        "and their spelling is in no call file now.",
        "They are kept as they were.",
        "",
    ]
    lines += [f"  {spelling.upper()}" for spelling in unused]
    text = "\n".join(lines) + "\n"
    if not added and report.exists():
        wrote = f"added nothing, so {report.relative_to(ROOT)} was left alone"
    elif report.exists():
        report.write_text(report.read_text(encoding="utf-8") + "\n" + "=" * 72 + "\nA later run:\n\n" + text, encoding="utf-8")
        wrote = f"wrote below the list in {report.relative_to(ROOT)}"
    else:
        report.write_text(text, encoding="utf-8")
        wrote = f"wrote {report.relative_to(ROOT)}"
    print(f"added {len(added)} entries; {len(dropped)} spellings no longer used; {len(unused)} generated entries not used; "
          f"{renamed} file names updated; {len(entries)} entries in {LEXICON.relative_to(ROOT)}; {wrote}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
