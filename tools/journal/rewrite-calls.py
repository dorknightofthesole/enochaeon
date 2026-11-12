"""Rewrite calls/01.txt to 18.txt and the thirty Aethyr files from a word record.

  python3 tools/journal/rewrite-calls.py sloane
      From calls/sloane/, the reading of Dee's manuscript Sloane 3191. This is
      the source of the call files.

  python3 tools/journal/rewrite-calls.py journal
      From calls/journal/, the 1659 printing. This is how the call files were
      written on the first pass, before Sloane 3191 was made the source. It
      puts the printing's words back, so it is run only to repeat that pass.

The words come from the record named and nothing else. The punctuation is
carried over from the call files as they were before either pass
(tools/journal/calls-before/), because neither record has punctuation: the old
letters and the new letters are lined up, and each old mark is put after the
new word that holds the letter it used to follow. A mark that used to stand
between two words the record has as one lands at the end of that one word;
every such move is listed in scratch/rewrite-calls-SOURCE.txt.

Capitals: the first word, each word after a full stop, question mark or
exclamation mark, and any word that stood in capitals before and still has the
same letters. 49.txt and 50.txt are not touched. No wav is touched.

An Aethyr file is named by the record's spelling of the name. A call file with
the same number and another name is removed.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BEFORE = Path(__file__).resolve().parent / "calls-before"
CALLS = ROOT / "calls"
SOURCES = {"sloane": CALLS / "sloane", "journal": CALLS / "journal"}
_TOKEN = re.compile(r"([A-Za-z]+)([^A-Za-z]*)")
_END = {".", "?", "!"}


def old_tokens(text: str) -> list[tuple[str, str]]:
    """(word, mark after it) for every word of an old call file."""
    return [(word, "".join(tail.split())) for word, tail in _TOKEN.findall(text)]


def spans(words: list[str]) -> list[int]:
    """For every letter of the joined words, the index of the word it is in."""
    owner: list[int] = []
    for index, word in enumerate(words):
        owner += [index] * len(word)
    return owner


def carry(old: list[tuple[str, str]], new: list[str]) -> tuple[list[str], list[bool], list[str]]:
    """Return the mark after each new word, which new words keep capitals, and the moves."""
    old_words = [word.lower() for word, _ in old]
    old_text, new_text = "".join(old_words), "".join(new)
    new_owner = spans(new)
    blocks = difflib.SequenceMatcher(a=old_text, b=new_text, autojunk=False).get_opcodes()

    def to_new(position: int) -> int:
        for tag, a0, a1, b0, b1 in blocks:
            if not a0 <= position < a1:
                continue
            if tag == "equal":
                return b0 + position - a0
            if tag == "replace":
                share = (position - a0 + 1) / (a1 - a0)
                return max(b0, min(b1 - 1, b0 + round(share * (b1 - b0)) - 1))
            return max(0, b0 - 1)
        return len(new_text) - 1

    marks = [""] * len(new)
    capitals = [False] * len(new)
    moves: list[str] = []
    end = 0
    for index, (word, mark) in enumerate(old):
        start, end = end, end + len(word)
        target = new_owner[to_new(end - 1)]
        if word.isupper() and len(word) > 1 and new[new_owner[to_new(start)]] == word.lower():
            capitals[new_owner[to_new(start)]] = True
        if not mark:
            continue
        last_letter = to_new(end - 1)
        at_word_end = last_letter + 1 == len(new_text) or new_owner[last_letter + 1] != target
        if not at_word_end:
            following = old[index + 1][0] if index + 1 < len(old) else ""
            moves.append(f"  {mark!r} stood after '{word}' and before '{following}'; "
                         f"now after '{new[target]}' (word {target + 1})")
        marks[target] = mark
    return marks, capitals, moves


def compose(new: list[str], marks: list[str], capitals: list[bool], name_at: int | None) -> str:
    out: list[str] = []
    sentence_start = True
    for index, word in enumerate(new):
        if capitals[index] or index == name_at:
            shown = word.upper()
        elif sentence_start:
            shown = word.capitalize()
        else:
            shown = word
        out.append(shown + marks[index])
        sentence_start = bool(marks[index]) and marks[index][-1] in _END
    return " ".join(out) + "\n"


def rewrite(source: Path, dest: Path, entries: list[dict], name_at: int | None, report: list[str]) -> None:
    new = [entry["letters"].lower() for entry in entries]
    marks, capitals, moves = carry(old_tokens(source.read_text(encoding="utf-8")), new)
    text = compose(new, marks, capitals, name_at)
    if [token.lower() for token in re.findall(r"[A-Za-z]+", text)] != new:
        raise ValueError(f"{dest.name}: the words written are not the record's words")
    dest.write_text(text, encoding="utf-8")
    report.append(f"== {dest.name}: {len(new)} words" + (f", was {source.name}" if source.name != dest.name else ""))
    report += moves or ["  no mark moved"]
    report.append("")


def main(arguments: list[str]) -> int:
    if len(arguments) != 1 or arguments[0] not in SOURCES:
        print(__doc__)
        return 2
    record = SOURCES[arguments[0]]
    report_path = ROOT / "scratch" / f"rewrite-calls-{arguments[0]}.txt"
    report: list[str] = [f"Call files written from {record.relative_to(ROOT)}/.", ""]
    for number in range(1, 19):
        data = json.loads((record / f"{number:02d}.json").read_text(encoding="utf-8"))
        name = f"{number:02d}.txt"
        rewrite(BEFORE / name, CALLS / name, data["words"], None, report)

    aethyrs = json.loads((record / "aethyrs.json").read_text(encoding="utf-8"))
    before = sorted(path for path in BEFORE.iterdir() if re.fullmatch(r"(19|[2-4]\d)-[a-z]+\.txt", path.name))
    if len(before) != len(aethyrs["names"]):
        raise ValueError(f"{len(before)} Aethyr files before, {len(aethyrs['names'])} names in the record")
    renamed: list[str] = []
    for index, source in enumerate(before):
        entries = list(aethyrs["words"])
        entries[aethyrs["name_word"]] = aethyrs["names"][index]
        number = source.name.split("-")[0]
        dest = CALLS / f"{number}-{aethyrs['names'][index]['letters'].lower()}.txt"
        rewrite(source, dest, entries, aethyrs["name_word"], report)
        for stale in sorted(CALLS.glob(f"{number}-*.txt")):
            if stale.name != dest.name:
                stale.unlink()
                renamed.append(f"{stale.name} -> {dest.name}")
    report.append("Renamed: " + (", ".join(renamed) or "none"))
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote 18 calls and {len(before)} Aethyr files from {record.relative_to(ROOT)}; renamed: {', '.join(renamed) or 'none'}")
    print(f"marks moved: {sum(1 for line in report if line.startswith('  ') and 'stood after' in line)}; see {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
