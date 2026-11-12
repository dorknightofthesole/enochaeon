"""Write a checking sheet per call for reading against the Sloane 3191 scan.

Reads calls/journal/. Writes scratch/sloane-check/01.txt to 18.txt and
aethyrs.txt: one journal word per line with its number, its status, Dee's
English where the journal gives it by word, and a star on every word whose
status is not `printed` or `corrected`.

If tools/sloane/sloane-reading.json exists, each line also gets the reading of
the manuscript at that place and a mark, and docs/sloane-diff.txt lists every
word that differs or could not be read. The reading file is typed by hand from
the page images in scratch/sloane-pages/; this script only lines it up with the
journal words and compares letters. It decides nothing about which is right,
and it changes no call file.

Reading file, per call: "where" (which image), "words" (the words in the order
the manuscript writes them, with its own word breaks, as one string or a list).
A space is a clear gap. A hyphen is a stroke Dee draws to tie two parts
together, so the parts are one word. An underscore is a small gap with no tie:
the eye cannot say whether it is a word break. It is taken as a break where
its width on the page shows one (tools/sloane/sloane-gaps.py measures it and
says when), or where the journal has a break at that very letter, and
otherwise as none. A '?' after a letter means that letter was not read with
certainty; "[?]" is a word not read at all.

Marks:
  agrees           the same letters as one word (capitals and accents ignored)
  differs          the letters are not the same, or the word is divided
                   differently, or it is missing; the kind is named
  could not read   the reading has a '?' at this place
  not checked      the reading file has nothing for this call
"""

from __future__ import annotations

import difflib
import importlib.util
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "calls" / "journal"
SHEETS = ROOT / "scratch" / "sloane-check"
READING = Path(__file__).resolve().parent / "sloane-reading.json"
DIFF = ROOT / "docs" / "sloane-diff.txt"
SURE = {"printed", "corrected"}


def plain(text: str) -> str:
    """Lower-case letters only: accents, marks and '?' removed."""
    text = unicodedata.normalize("NFD", text).lower()
    return "".join(char for char in text if "a" <= char <= "z")


def same_letter_forms(text: str) -> str:
    """Read v as u, and j and y as i, the way one hand writes one letter two ways."""
    return text.replace("v", "u").replace("j", "i").replace("y", "i")


def letter_places(journal: list[str], letters: str) -> tuple[list[int | None], list[int]]:
    """For each letter of the reading, the journal word it stands in, if any.

    Also returns, for each letter, the journal word that comes before it.
    """
    journal_owner = [index for index, word in enumerate(journal) for _ in word]
    a, b = letters, "".join(journal)
    blocks = difflib.SequenceMatcher(a=same_letter_forms(a), b=same_letter_forms(b), autojunk=False).get_opcodes()
    letter_to_journal: list[int | None] = [None] * len(a)
    before: list[int] = [-1] * len(a)
    for tag, a0, a1, b0, b1 in blocks:
        for position in range(a0, a1):
            before[position] = journal_owner[b0 - 1] if b0 > 0 else -1
            if tag == "equal":
                letter_to_journal[position] = journal_owner[b0 + position - a0]
            elif tag == "replace":
                share = (position - a0) / (a1 - a0)
                letter_to_journal[position] = journal_owner[min(b1 - 1, b0 + int(share * (b1 - b0)))]
    return letter_to_journal, before


def settle_small_gaps(journal: list[str], reading: list[str], measured: list[bool] | None = None) -> list[str]:
    """Decide each underscore: a word break where the page or the journal has one.

    `measured` says, for each underscore in order, whether its width on the
    page shows a word break. Where it does not, the underscore is a break only
    if the letters on each side of it stand in two different journal words.
    Anywhere else the underscore stays inside the word, so a small gap never
    counts as a difference by itself.
    """
    in_journal = journal_breaks(journal, reading)
    on_page = measured if measured is not None else [False] * len(in_journal)
    if len(on_page) != len(in_journal):
        raise ValueError(f"{len(in_journal)} small gaps in the reading, {len(on_page)} measured")
    breaks = (page or printed for page, printed in zip(on_page, in_journal))
    settled: list[str] = []
    for word in reading:
        pieces = word.split("_")
        current = pieces[0]
        for piece in pieces[1:]:
            if next(breaks):
                settled.append(current)
                current = piece
            else:
                current += "_" + piece
        settled.append(current)
    return settled


def journal_breaks(journal: list[str], reading: list[str]) -> list[bool]:
    """For each underscore of the reading, in order: whether the journal has a word break there."""
    letter_to_journal, _ = letter_places(journal, "".join(plain(word) for word in reading))
    found: list[bool] = []
    position = 0
    for word in reading:
        pieces = word.split("_")
        position += len(plain(pieces[0]))
        for piece in pieces[1:]:
            left = letter_to_journal[position - 1] if position > 0 else None
            right = letter_to_journal[position] if position < len(letter_to_journal) and plain(piece) else None
            found.append(left is not None and right is not None and left != right)
            position += len(plain(piece))
    return found


def line_up(journal: list[str], reading: list[str]) -> tuple[list[list[int]], list[tuple[int, int]]]:
    """For each journal word, the reading words that stand in its place.

    Also returns (journal word before, reading word) for each reading word
    that stands in no journal word's place.
    """
    reading_letters = [plain(word) for word in reading]
    letter_to_journal, before = letter_places(journal, "".join(reading_letters))
    places: list[list[int]] = [[] for _ in journal]
    loose: list[tuple[int, int]] = []
    position = 0
    for index, letters in enumerate(reading_letters):
        owners = [letter_to_journal[position + offset] for offset in range(len(letters))]
        found = sorted({owner for owner in owners if owner is not None})
        if found:
            for owner in found:
                places[owner].append(index)
        else:
            loose.append((before[position] if letters else -1, index))
        position += len(letters)
    return places, loose


def judge(journal_word: str, written: list[str], shared: bool) -> tuple[str, str]:
    """Return (mark, kind) for one journal word and the reading words in its place."""
    if not written:
        return "differs", "not in the manuscript at this place"
    if any(word == "[?]" for word in written):
        return "could not read", ""
    if any("?" in word for word in written):
        return "could not read", "a letter is uncertain"
    letters = "".join(plain(word) for word in written)
    if shared:
        return "differs", "word break"
    if letters == journal_word:
        return ("agrees", "") if len(written) == 1 else ("differs", "word break")
    if same_letter_forms(letters) == same_letter_forms(journal_word):
        kind = "u/v or i/j/y only"
        return "differs", kind if len(written) == 1 else kind + ", and word break"
    return "differs", "letters"


def measured_breaks(call: str) -> list[bool]:
    """For each small gap of a call's reading, in order: whether its width on the page shows a word break."""
    spec = importlib.util.spec_from_file_location("sloane_gaps", Path(__file__).resolve().parent / "sloane-gaps.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.breaks(call)


def reading_words(journal: list[str], reading: dict, call: str | None = None) -> list[str]:
    """The words of one reading, with each small gap settled.

    `call` names the call whose measured gaps settle them. Without it, only
    the journal does: the thirty names have no small gap.
    """
    words = reading["words"].split() if isinstance(reading["words"], str) else reading["words"]
    return settle_small_gaps(journal, words, measured_breaks(call) if call else None)


def compare(journal: list[str], words: list[str]) -> tuple[list[tuple[list[str], str, str]], list[tuple[int, str]]]:
    """For each journal word: the reading words in its place, the mark and the kind.

    Also returns (journal word before, reading word) for each reading word
    that stands in no journal word's place.
    """
    places, loose = line_up(journal, words)
    rows: list[tuple[list[str], str, str]] = []
    for index, journal_word in enumerate(journal):
        written = [words[place] for place in places[index]]
        shared = any(len([1 for other in places if place in other]) > 1 for place in places[index])
        rows.append((written, *judge(journal_word, written, shared)))
    return rows, [(after, words[place]) for after, place in loose]


def star(entry: dict) -> str:
    return "" if entry["status"] in SURE else "*"


def sheet(title: str, data: dict, entries: list[dict], reading: dict | None, diff: list[str],
          call: str | None = None) -> list[str]:
    lines = [title, f"Journal: {data['printing']}, {data['pages']}.",
             "A star marks a word whose status is not printed or corrected."]
    journal = [entry["letters"].lower() for entry in entries]
    rows: list[tuple[list[str], str, str]] | None = None
    loose: list[tuple[int, str]] = []
    if reading and reading.get("words"):
        rows, loose = compare(journal, reading_words(journal, reading, call))
        lines.append(f"Sloane 3191: {reading['where']}.")
        for remark in reading.get("remarks", []):
            lines.append(f"Sloane 3191: {remark}")
    else:
        lines.append("Sloane 3191: " + (reading["where"] if reading else "not checked."))
    lines.append("")
    header = f"{'#':>4}  {'':1} {'journal':16} {'status':12} {'page':6} {'Dee\'s English':30}"
    if rows is not None:
        header += f" {'Sloane 3191':22} mark"
    lines += [header, "-" * len(header)]
    counts = {"agrees": 0, "differs": 0, "could not read": 0}
    for index, entry in enumerate(entries):
        page = f"p. {entry['page']}" if entry.get("page") else "-"
        row = (f"{index + 1:>4}  {star(entry):1} {entry['letters']:16} {entry['status']:12} {page:6} "
               f"{entry.get('english', '')[:30]:30}")
        if rows is not None:
            written, mark, kind = rows[index]
            counts[mark] += 1
            shown = " ".join(written) or "-"
            row += f" {shown:22} {mark}" + (f": {kind}" if kind else "")
            if mark != "agrees":
                diff.append(f"  word {index + 1:3d}  {star(entry):1} journal {entry['letters']:16} ({entry['status']}, {page})  "
                            f"Sloane {shown:22} {mark}" + (f": {kind}" if kind else ""))
            for after, word in loose:
                if after == index:
                    row += f"\n{'':>4}    {'':16} {'':12} {'':6} {'':30} {word:22} only in the manuscript"
                    diff.append(f"  after word {index + 1:3d}  Sloane {word:22} only in the manuscript")
        lines.append(row.rstrip())
    if rows is not None:
        for after, word in loose:
            if after == -1:
                lines.insert(len(lines) - len(entries), f"{'':>4}    {'before word 1':66} {word:22} only in the manuscript")
                diff.append(f"  before word 1    Sloane {word:22} only in the manuscript")
        lines += ["", "Marks: " + ", ".join(f"{count} {mark}" for mark, count in counts.items())]
    return lines


def main() -> int:
    SHEETS.mkdir(parents=True, exist_ok=True)
    reading = json.loads(READING.read_text(encoding="utf-8")) if READING.exists() else {"calls": {}}
    diff_all: list[str] = []
    totals = {"agrees": 0, "differs": 0, "could not read": 0}
    not_checked: list[str] = []
    for stem in [f"{number:02d}" for number in range(1, 19)] + ["aethyrs"]:
        data = json.loads((JOURNAL / f"{stem}.json").read_text(encoding="utf-8"))
        title = "The call of the thirty Aethyrs" if stem == "aethyrs" else f"Call {int(stem)}"
        read = reading["calls"].get(stem)
        diff: list[str] = []
        lines = sheet(title, data, data["words"], read, diff, stem)
        if stem == "aethyrs":
            names_read = {"where": read["names_where"], "words": read["names"]} if read and read.get("names") else None
            lines += ["", ""]
            diff.append("  -- the thirty names: " + (names_read["where"] if names_read else "not checked"))
            lines += sheet("The thirty names", data, data["names"], names_read, diff)
        (SHEETS / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if read and read.get("words"):
            for line in lines:
                if line.startswith("Marks: "):
                    for part in line[7:].split(", "):
                        count, mark = part.split(" ", 1)
                        totals[mark] += int(count)
            remarks = [f"  remark: {remark}" for remark in read.get("remarks", [])]
            diff_all += [f"== {title}: {read['where']}"] + (diff or ["  every word agrees"]) + remarks + [""]
        else:
            not_checked.append(title)
    print(f"wrote {len(list(SHEETS.glob('*.txt')))} sheets in {SHEETS.relative_to(ROOT)}")
    if READING.exists():
        head = ["Sloane 3191 against the journal data: every word that differs or could not be read.",
                "The reading is from the page images in scratch/sloane-pages/. It has not been confirmed.",
                "A star marks a word whose journal status is not printed or corrected.",
                "", "Totals: " + ", ".join(f"{count} {mark}" for mark, count in totals.items()),
                "Not checked: " + (", ".join(not_checked) or "none"), ""]
        DIFF.write_text("\n".join(head + diff_all) + "\n", encoding="utf-8")
        print(f"wrote {DIFF.relative_to(ROOT)}: " + ", ".join(f"{count} {mark}" for mark, count in totals.items())
              + f"; not checked: {', '.join(not_checked) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
