"""Measure the gaps between the words Dee wrote in Sloane 3191, in pixels.

  python3 tools/sloane/sloane-gaps.py pages CALL
      Finds the lines of Enochian in one call and writes the page in pieces to
      scratch/sloane-gaps/. Each line has its number at the left, and every
      gap of at least MIN_GAP pixels is marked below the line with its width
      written under the mark. CALL.txt lists each line and its gaps in order.

  python3 tools/sloane/sloane-gaps.py close CALL LINE...
  python3 tools/sloane/sloane-gaps.py closer CALL LINE...
      Writes those lines again for a crowded place: `close` in two parts at
      the size of the scan, `closer` in four parts at twice that size.

  python3 tools/sloane/sloane-gaps.py judge
      Checks sloane-gap-kinds.txt against the page and the reading, and writes
      docs/sloane-gaps.txt: every small gap of the reading, its width, the
      gaps it is compared with, what the comparison says, and whether the
      journal has a word break there.

A page of the manuscript has two kinds of line, one above the other: Dee's
English in a small light hand, and the Enochian below it in a larger dark
hand. A line is found as a band of rows where much of the width is ink. A
band is taken as Enochian when its letters fill more of its height than the
letters of the bands next to it. A line the script does not find is typed in
sloane-gap-lines.txt.

The gaps are measured in that band, where the small letters stand (a, o, n).
A stroke above or below the line does not fill a gap: the tall strokes of d
and l, the English above, and the tie-stroke Dee draws under two parts of one
word. A gap is a run of columns in the band with no ink.

sloane-gap-kinds.txt has one row for each line of a call that has a small gap.
The widths in it are the ones this script measured. The kind after each width
is typed by hand, from the marked page and the reading. The file explains the
kinds.

What the comparison says for each small gap. Two widths are compared with it:
the widest gap inside a word anywhere in the rows (a gap Dee tied, or a gap
between two letters of a word), and the narrowest gap between two words on
the small gap's own line.

  word break                     wider than every gap inside a word, and at
                                 least as wide as a gap between two words on
                                 its line
  between                        wider than every gap inside a word, and
                                 narrower than every gap between two words on
                                 its line
  no wider than inside a word    a gap as wide as this stands inside a word
                                 somewhere, so the width does not show a break
  no gap                         the script found no gap of MIN_GAP pixels
  cannot be measured             a stroke or a point stands in the gap

Only `word break` changes the text: tools/sloane/sloane-sheets.py reads it and
divides the word there. Every other small gap is left to the journal, as
before. No width says that two parts are one word, because the narrowest gaps
between words are narrower than the widest gaps Dee tied.

The script measures and compares. The kinds are one reading by eye.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "scratch" / "sloane-gaps"
JUDGED = ROOT / "docs" / "sloane-gaps.txt"
JOURNAL = ROOT / "calls" / "journal"
KINDS = HERE / "sloane-gap-kinds.txt"
LINES = HERE / "sloane-gap-lines.txt"
READING = HERE / "sloane-reading.json"

# A pixel is ink when it is this much darker than the paper around it.
INK_DARKER = 38
# The paper around a pixel: the median of a square this many pixels wide.
PAPER_SQUARE = 61
# A row belongs to a line when this share of the width is ink.
ROW_SHARE = 0.055
# A line is at least this many rows of such ink.
LINE_ROWS = 14
# A run of rows taller than this is more than one line.
TALLEST_LINE = 41
# How much the share grows each time such a run is looked at again.
SHARE_STEP = 1.15
# The smallest gap that is marked.
MIN_GAP = 12
# A column is empty when it has no more ink pixels than this in the band.
EMPTY_COLUMN = 1
# How many lines of Enochian go into one piece of the page.
LINES_IN_PIECE = 6
# How much of the page is shown above the first line and below the last line of a piece.
ABOVE, BELOW = 85, 45
# How many pixels the two halves of a line seen close have in common.
HALVES_SHARE = 60
# The two commands that show a line close, and how many parts each cuts the line into.
CLOSE = {"close": 2, "closer": 4}

BREAK = "word break"
BETWEEN = "between"
INSIDE = "no wider than inside a word"
NO_GAP = "no gap"
CROSSED = "cannot be measured"
SAYS = (BREAK, BETWEEN, INSIDE, NO_GAP, CROSSED)

# The kinds of sloane-gap-kinds.txt.
BETWEEN_WORDS, SMALL, TIED, LETTERS, CAPITALS, NOT_TEXT = "s", "_", "-", ".", "c", "x"
# The mark for a small gap that a stroke or a point stands in.
CROSSED_MARK = "/" + SMALL


def script(name: str):
    """Another script of this directory, as a module."""
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cutter():
    return script("sloane-cut")


def ink(gray: np.ndarray) -> np.ndarray:
    """True where a pixel is darker than the paper around it."""
    step = 8
    small = gray[::step, ::step]
    pad = PAPER_SQUARE // step // 2
    padded = np.pad(small, pad, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (2 * pad + 1, 2 * pad + 1))
    paper = np.median(windows, axis=(2, 3))
    paper = np.repeat(np.repeat(paper, step, axis=0), step, axis=1)[: gray.shape[0], : gray.shape[1]]
    return gray < paper - INK_DARKER


def runs(smooth: np.ndarray, top: int, bottom: int, share: float) -> list[tuple[int, int]]:
    """(top, bottom) of each run of rows between top and bottom with that share of ink.

    A run taller than a line is two lines that touch. It is looked at again with
    a larger share, until the lines come apart.
    """
    found: list[tuple[int, int]] = []
    start = None
    for row in range(top, bottom + 1):
        value = smooth[row] if row < bottom else 0.0
        if value >= share and start is None:
            start = row
        if value < share and start is not None:
            if row - start > TALLEST_LINE:
                found += runs(smooth, start, row, share * SHARE_STEP)
            elif row - start >= LINE_ROWS:
                found.append((start, row))
            start = None
    return found


def bands(dark: np.ndarray) -> list[tuple[int, int]]:
    """(top, bottom) of each run of rows with enough ink."""
    share = dark.mean(axis=1)
    smooth = np.convolve(share, np.ones(5) / 5, mode="same")
    return runs(smooth, 0, len(smooth), ROW_SHARE)


def fill(dark: np.ndarray, top: int, bottom: int) -> float:
    """How much of the band's height its letters fill: the ink in a column, at the tall end."""
    columns = dark[top:bottom].sum(axis=0)
    columns = columns[columns > 0]
    return float(np.percentile(columns, 90)) if len(columns) else 0.0


def enochian_bands(dark: np.ndarray) -> list[tuple[int, int]]:
    """The bands whose letters fill more height than the letters of the bands beside them."""
    found = bands(dark)
    fills = [fill(dark, top, bottom) for top, bottom in found]
    chosen: list[tuple[int, int]] = []
    for index, band in enumerate(found):
        beside = [fills[other] for other in (index - 1, index + 1) if 0 <= other < len(found)]
        if beside and fills[index] > sum(beside) / len(beside):
            chosen.append(band)
    return chosen


def gaps(dark: np.ndarray, top: int, bottom: int) -> list[tuple[int, int]]:
    """(left, width) of each run of empty columns between the first and last ink of a band."""
    filled = dark[top:bottom].sum(axis=0) > EMPTY_COLUMN
    columns = np.flatnonzero(filled)
    if not len(columns):
        return []
    found: list[tuple[int, int]] = []
    start = None
    for column in range(columns[0], columns[-1] + 1):
        if not filled[column] and start is None:
            start = column
        if filled[column] and start is not None:
            found.append((start, column - start))
            start = None
    return found


def measure(call: str) -> list[tuple[str, int, int, int, int, list[tuple[int, int]]]]:
    """For each line of Enochian: (page, left, width, band top, band bottom, gaps), in page pixels."""
    cut = cutter()
    found = []
    for page, left, width, top, bottom in cut.regions()[call]:
        image = cut.load(page)
        dark = ink(image[top:bottom, left : left + width].mean(axis=2))
        typed = [(first - top, last - top) for first, last in typed_lines().get((call, page), [])]
        for band_top, band_bottom in sorted(enochian_bands(dark) + typed):
            marked = [(left + x, w) for x, w in gaps(dark, band_top, band_bottom) if w >= MIN_GAP]
            found.append((page, left, width, top + band_top, top + band_bottom, marked))
    return found


def typed_lines() -> dict[tuple[str, str], list[tuple[int, int]]]:
    """For a call and a page: (top, bottom) of each line typed in sloane-gap-lines.txt."""
    found: dict[tuple[str, str], list[tuple[int, int]]] = {}
    for raw in LINES.read_text(encoding="utf-8").split("\n"):
        row = raw.split("#")[0].split()
        if row:
            found.setdefault((row[0], row[1]), []).append((int(row[2]), int(row[3])))
    return found


def pages(call: str) -> int:
    cut = cutter()
    OUT.mkdir(parents=True, exist_ok=True)
    lines = measure(call)
    report = [f"Call {call}: the lines of Enochian and the width of each marked gap, left to right, in pixels.", ""]
    images: dict[str, np.ndarray] = {}
    for start in range(0, len(lines), LINES_IN_PIECE):
        group = lines[start : start + LINES_IN_PIECE]
        for page in dict.fromkeys(line[0] for line in group):
            part = [(start + offset + 1, line) for offset, line in enumerate(group) if line[0] == page]
            image = images.setdefault(page, cut.load(page))
            _, left, width, _, _, _ = part[0][1]
            y0 = max(0, part[0][1][3] - ABOVE)
            y1 = min(image.shape[0], part[-1][1][4] + BELOW)
            piece = image[y0:y1, left - 60 : left + width].copy()
            for number, (_, _, _, band_top, band_bottom, marked) in part:
                base = band_bottom - y0
                cut.label(piece, str(number), 0, band_top - y0, scale=4)
                for x, w in marked:
                    piece[base + 6 : base + 10, x - left + 60 : x - left + 60 + w] = (200, 0, 0)
                    cut.label(piece, str(w), x - left + 60 + w // 2 - 10, base + 13, scale=3)
            name = f"{call}-{page}-{part[0][0]:02d}.jpg"
            cut.save(piece, OUT / name)
            report.append(f"{name}: lines {part[0][0]} to {part[-1][0]}")
    report.append("")
    for number, (page, _, _, band_top, band_bottom, marked) in enumerate(lines, 1):
        report.append(f"{call} {number}  " + " ".join(str(w) for _, w in marked) + f"    # {page} rows {band_top}-{band_bottom}")
    (OUT / f"{call}.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


def close(call: str, numbers: list[int], parts: int) -> int:
    """Each of those lines with its gaps marked, in parts that overlap.

    Two parts are at the size of the scan. Four parts are at twice that size.
    """
    cut = cutter()
    OUT.mkdir(parents=True, exist_ok=True)
    lines = measure(call)
    for number in numbers:
        page, left, width, band_top, band_bottom, marked = lines[number - 1]
        image = cut.load(page)
        y0 = max(0, band_top - ABOVE)
        strip = image[y0 : band_bottom + BELOW, left : left + width].copy()
        base = band_bottom - y0
        for x, w in marked:
            strip[base + 6 : base + 10, x - left : x - left + w] = (200, 0, 0)
            cut.label(strip, str(w), x - left + w // 2 - 10, base + 13, scale=3)
        part = width // parts
        for index in range(parts):
            start = max(0, index * part - HALVES_SHARE)
            piece = strip[:, start : (index + 1) * part + HALVES_SHARE]
            name = f"{call}-line-{number:02d}-{'abcdefgh'[index]}.jpg"
            cut.save(np.repeat(np.repeat(piece, parts // 2, axis=0), parts // 2, axis=1), OUT / name)
            print(name)
    return 0


def typed_rows() -> dict[str, list[tuple[int, list[tuple[int | None, str]]]]]:
    """For each call: (line number, [(width, kind)]) of each row typed in sloane-gap-kinds.txt.

    The width is None for a small gap that cannot be measured.
    """
    found: dict[str, list[tuple[int, list[tuple[int | None, str]]]]] = {}
    kinds = BETWEEN_WORDS + SMALL + TIED + LETTERS + CAPITALS + NOT_TEXT
    for raw in KINDS.read_text(encoding="utf-8").split("\n"):
        row = raw.split("#")[0].split()
        if not row:
            continue
        marks: list[tuple[int | None, str]] = []
        for mark in row[2:]:
            if mark == CROSSED_MARK:
                marks.append((None, SMALL))
            elif mark[-1] in kinds and mark[:-1].isdigit():
                marks.append((int(mark[:-1]), mark[-1]))
            else:
                raise ValueError(f"{KINDS.name}: {raw!r} has a mark that is not a width and a kind")
        found.setdefault(row[0], []).append((int(row[1]), marks))
    return found


def widest_inside(rows: dict[str, list[tuple[int, list[tuple[int | None, str]]]]]) -> tuple[int, str, int]:
    """(width, call, line) of the widest gap inside a word in all the rows."""
    return max((width, call, line) for call, lines in rows.items() for line, marks in lines
               for width, kind in marks if kind in TIED + LETTERS)


def small_gaps(call: str) -> list[dict]:
    """Each small gap typed for a call, in the order of the page, with what it is compared with."""
    rows = typed_rows()
    inside = widest_inside(rows)[0]
    found: list[dict] = []
    for line, marks in rows.get(call, []):
        between = min((width for width, kind in marks if kind == BETWEEN_WORDS), default=None)
        for width, kind in marks:
            if kind != SMALL:
                continue
            if width is None:
                says = CROSSED
            elif width == 0:
                says = NO_GAP
            elif width <= inside:
                says = INSIDE
            elif between is not None and width >= between:
                says = BREAK
            else:
                says = BETWEEN
            found.append({"line": line, "width": width, "narrowest_between_words": between, "says": says})
    return found


def breaks(call: str) -> list[bool]:
    """For each small gap of a call's reading, in order: whether the measure shows a word break."""
    return [gap["says"] == BREAK for gap in small_gaps(call)]


def reading_small_gaps(call: str) -> list[tuple[str, bool]]:
    """For each small gap of a call's reading, in order: the word it is in, and whether the journal breaks there."""
    reading = json.loads(READING.read_text(encoding="utf-8"))["calls"][call]
    words = reading["words"].split() if isinstance(reading["words"], str) else list(reading["words"])
    entries = json.loads((JOURNAL / f"{call}.json").read_text(encoding="utf-8"))["words"]
    in_journal = script("sloane-sheets").journal_breaks([entry["letters"].lower() for entry in entries], words)
    return list(zip([word for word in words for _ in range(word.count(SMALL))], in_journal))


def judge() -> int:
    reading = json.loads(READING.read_text(encoding="utf-8"))["calls"]
    rows = typed_rows()
    inside, inside_call, inside_line = widest_inside(rows)
    report = [
        "Every small gap of the reading of Sloane 3191, measured on the page.",
        "Written by tools/sloane/sloane-gaps.py judge, which explains the measure and the comparison.",
        "The kind of each gap on a line was typed by eye in tools/sloane/sloane-gap-kinds.txt. It has not been confirmed.",
        "",
        "line: the line of Enochian in that call, counted from 1 as the script numbers them.",
        "width: the gap, in pixels of the page image. 0: no gap of that size was found. -: a stroke stands in the gap.",
        "between: the narrowest gap between two words on the same line.",
        f"The widest gap inside a word in all the rows is {inside} pixels (call {inside_call}, line {inside_line}).",
        "journal: whether the 1659 printing has one word or two at this place.",
        "Only a gap marked `word break` is divided by its width. Every other gap has the journal's division.",
        "",
    ]
    totals = dict.fromkeys(SAYS, 0)
    wrong = 0
    for call in reading:
        words = reading_small_gaps(call)
        if not words:
            continue
        found = small_gaps(call)
        report.append(f"== {call}: {len(words)} small gaps in the reading, {len(found)} typed")
        if len(found) != len(words):
            wrong += 1
            report.append("   THE COUNTS DO NOT AGREE: the rows for this call are not finished or not right")
        measured = measure(call)
        for line, marks in rows.get(call, []):
            typed = [width for width, _ in marks if width]
            on_page = [width for _, width in measured[line - 1][5]]
            if typed != on_page:
                wrong += 1
                report.append(f"   LINE {line} IS NOT AS MEASURED: typed {typed}, measured {on_page}")
        for (word, in_journal), gap in zip(words, found):
            totals[gap["says"]] += 1
            width = "-" if gap["width"] is None else gap["width"]
            between = gap["narrowest_between_words"] or "-"
            report.append(f"   line {gap['line']:2d}  {word:20} width {width!s:>3}  between {between!s:>3}  "
                          f"{gap['says']:28} journal: {'two words' if in_journal else 'one word'}")
        report.append("")
    report.append("Totals: " + ", ".join(f"{count} {says}" for says, count in totals.items()))
    JUDGED.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[-1:] + [f"wrote {JUDGED.relative_to(ROOT)}"]))
    return 1 if wrong else 0


def main(arguments: list[str]) -> int:
    if len(arguments) == 2 and arguments[0] == "pages":
        return pages(arguments[1])
    if len(arguments) >= 3 and arguments[0] in CLOSE and all(number.isdigit() for number in arguments[2:]):
        return close(arguments[1], [int(number) for number in arguments[2:]], CLOSE[arguments[0]])
    if arguments == ["judge"]:
        return judge()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
