"""Cut images out of the manuscript pages of the Sloane 3191 scan.

  python3 tools/sloane/sloane-cut.py calls
      One image per call, with its margins, in docs/imgs/sloane-calls/. The
      Aethyr call is on two pages; they are put one above the other.

  python3 tools/sloane/sloane-cut.py places
      One full-size image for every place where the reading of the manuscript
      and the journal data do not agree, in docs/imgs/sloane-places/, and
      index.md there, which shows each image beside the two spellings.

  python3 tools/sloane/sloane-cut.py proof
      The places of each call one above the other in a single image, in the
      order of sloane-places.json, in scratch/sloane-places-proof/. This is
      for looking over the boxes after they are typed.

  python3 tools/sloane/sloane-cut.py grid CALL
      The page of one call with a numbered grid drawn over it, in
      scratch/sloane-grid/. A grid line is drawn every 100 pixels and its label
      is the pixel count divided by 100. This is how a box in
      sloane-places.json is found.

The pages are scratch/sloane-pages/ms/NAME.jpg, made by sloane-extract.py and
sloane-crop.sh. Where each call stands on its page is in
sloane-call-regions.txt. Where each place stands is in sloane-places.json,
typed by hand: the page, and a box [left, top, width, height] in pixels of
that page. The image is cut 30 pixels wider than the box on every side, so a
box drawn close around a word still shows the strokes above and below it. A
place names the journal words it shows by number, counted from 1
as in docs/sloane-diff.txt, and with "after" the journal word a word that is
only in the manuscript follows.

A place is needed for every word that differs in letters or in word division,
every word that is not in the manuscript, every word only in the manuscript,
and every word that could not be read. A word that differs only in u/v or
i/j/y is not given a place. `places` says which needed places are missing.

This script cuts images and lays them beside the two spellings. It reads
nothing and decides nothing about which spelling is right.
"""

from __future__ import annotations

import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JOURNAL = ROOT / "calls" / "journal"
PAGES = ROOT / "scratch" / "sloane-pages" / "ms"
REGIONS = HERE / "sloane-call-regions.txt"
PLACES = HERE / "sloane-places.json"
READING = HERE / "sloane-reading.json"
CALLS_OUT = ROOT / "docs" / "imgs" / "sloane-calls"
PLACES_OUT = ROOT / "docs" / "imgs" / "sloane-places"
GRID_OUT = ROOT / "scratch" / "sloane-grid"
PROOF_OUT = ROOT / "scratch" / "sloane-places-proof"

# How much of the page around the written lines goes into a call's image.
MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM = 260, 260, 220, 140

# How much wider than its box, on every side, a place is cut.
PLACE_PAD = 30

DIGITS = {
    "0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
    "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
    "8": "111101111101111", "9": "111101111001111",
}


def _sips(*arguments: str) -> None:
    subprocess.run(["sips", *arguments], check=True, capture_output=True)


def load(page: str) -> np.ndarray:
    """One manuscript page as rows of pixels (height, width, 3)."""
    source = PAGES / f"{page}.jpg"
    if not source.exists():
        raise FileNotFoundError(f"{source.relative_to(ROOT)} is missing: run sloane-extract.py and sloane-crop.sh")
    bitmap = PAGES / f"{page}.bmp"
    _sips("-s", "format", "bmp", str(source), "--out", str(bitmap))
    raw = bitmap.read_bytes()
    bitmap.unlink()
    start = struct.unpack_from("<I", raw, 10)[0]
    width, height, _, bits = struct.unpack_from("<iiHH", raw, 18)
    if bits != 24:
        raise ValueError(f"{page}: {bits} bits per pixel, expected 24")
    stride = (width * 3 + 3) // 4 * 4
    rows = np.frombuffer(raw, dtype=np.uint8, count=stride * abs(height), offset=start)
    rows = rows.reshape(abs(height), stride)[:, : width * 3].reshape(abs(height), width, 3)
    return (rows if height < 0 else rows[::-1]).copy()


def save(image: np.ndarray, dest: Path) -> None:
    height, width, _ = image.shape
    stride = (width * 3 + 3) // 4 * 4
    body = np.zeros((height, stride), dtype=np.uint8)
    body[:, : width * 3] = image.reshape(height, width * 3)
    header = (b"BM" + struct.pack("<IHHI", 54 + body.size, 0, 0, 54)
              + struct.pack("<IiiHHIIiiII", 40, width, -height, 1, 24, 0, body.size, 2835, 2835, 0, 0))
    bitmap = dest.with_suffix(".bmp")
    bitmap.write_bytes(header + body.tobytes())
    _sips("-s", "format", "jpeg", "-s", "formatOptions", "92", str(bitmap), "--out", str(dest))
    bitmap.unlink()


def regions() -> dict[str, list[tuple[str, int, int, int, int]]]:
    """For each call: (page, left, width, top, bottom) of its written lines."""
    found: dict[str, list[tuple[str, int, int, int, int]]] = {}
    for line in REGIONS.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            page, call, left, width, top, bottom = line.split()
            found.setdefault(call, []).append((page, int(left), int(width), int(top), int(bottom)))
    return found


def with_margins(image: np.ndarray, region: tuple[str, int, int, int, int]) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) of a call's lines and the margins around them."""
    _, left, width, top, bottom = region
    return (max(0, left - MARGIN_LEFT), max(0, top - MARGIN_TOP),
            min(image.shape[1], left + width + MARGIN_RIGHT), min(image.shape[0], bottom + MARGIN_BOTTOM))


def stack(pieces: list[np.ndarray]) -> np.ndarray:
    """Put images one above the other on white, with a white band between."""
    width = max(piece.shape[1] for piece in pieces)
    rows: list[np.ndarray] = []
    for index, piece in enumerate(pieces):
        if index:
            rows.append(np.full((60, width, 3), 255, dtype=np.uint8))
        padded = np.full((piece.shape[0], width, 3), 255, dtype=np.uint8)
        padded[:, : piece.shape[1]] = piece
        rows.append(padded)
    return np.vstack(rows)


def cut_box(image: np.ndarray, box: list[int]) -> np.ndarray:
    left, top, width, height = box
    return image[max(0, top - PLACE_PAD) : top + height + PLACE_PAD, max(0, left - PLACE_PAD) : left + width + PLACE_PAD]


def cut_calls() -> int:
    CALLS_OUT.mkdir(parents=True, exist_ok=True)
    for call, parts in regions().items():
        pieces = []
        for region in parts:
            image = load(region[0])
            left, top, right, bottom = with_margins(image, region)
            pieces.append(image[top:bottom, left:right])
        whole = stack(pieces)
        save(whole, CALLS_OUT / f"{call}.jpg")
        print(f"{call}: {whole.shape[1]} x {whole.shape[0]}, from {', '.join(region[0] for region in parts)}")
    print(f"wrote {len(regions())} images in {CALLS_OUT.relative_to(ROOT)}")
    return 0


def label(image: np.ndarray, text: str, x: int, y: int, scale: int = 4) -> None:
    """Write digits on a white patch with its top-left corner at (x, y)."""
    height, width = 5 * scale + 4, len(text) * 4 * scale + 4
    y = max(0, min(image.shape[0] - height, y))
    x = max(0, min(image.shape[1] - width, x))
    image[y : y + height, x : x + width] = 255
    for place, digit in enumerate(text):
        for cell, bit in enumerate(DIGITS[digit]):
            if bit == "1":
                top = y + 2 + (cell // 3) * scale
                left = x + 2 + place * 4 * scale + (cell % 3) * scale
                image[top : top + scale, left : left + scale] = (0, 0, 160)


def cut_grid(call: str) -> int:
    GRID_OUT.mkdir(parents=True, exist_ok=True)
    for region in regions()[call]:
        page = region[0]
        image = load(page)
        left, top, right, bottom = with_margins(image, region)
        piece_top, number = top, 0
        while piece_top < bottom:
            piece_bottom = min(bottom, piece_top + 1000)
            piece = image[piece_top:piece_bottom, left:right].copy()
            for x in range((left // 100 + 1) * 100, right, 100):
                piece[:, x - left] = (0, 0, 255)
            for y in range((piece_top // 100 + 1) * 100, piece_bottom, 100):
                piece[y - piece_top, :] = (0, 0, 255)
            for x in range((left // 100 + 1) * 100, right, 100):
                label(piece, str(x // 100), x - left + 3, 0)
                label(piece, str(x // 100), x - left + 3, piece.shape[0])
            for y in range((piece_top // 100 + 1) * 100, piece_bottom, 100):
                label(piece, str(y // 100), 0, y - piece_top + 3)
                label(piece, str(y // 100), piece.shape[1], y - piece_top + 3)
            dest = GRID_OUT / f"{call}-{page}-{number}.jpg"
            save(piece, dest)
            print(f"{dest.relative_to(ROOT)}: x {left} to {right}, y {piece_top} to {piece_bottom}")
            if piece_bottom == bottom:
                break
            piece_top, number = piece_top + 900, number + 1
    return 0


def cut_proof() -> int:
    PROOF_OUT.mkdir(parents=True, exist_ok=True)
    places = json.loads(PLACES.read_text(encoding="utf-8"))["places"]
    pages: dict[str, np.ndarray] = {}
    for call in sorted({place["call"] for place in places}):
        pieces = []
        for place in places:
            if place["call"] == call:
                if place["page"] not in pages:
                    pages[place["page"]] = load(place["page"])
                pieces.append(cut_box(pages[place["page"]], place["box"]))
        whole = stack(pieces)
        save(whole, PROOF_OUT / f"{call}.jpg")
        print(f"{call}: {len(pieces)} places, {whole.shape[1]} x {whole.shape[0]}")
    return 0


def sheets_module():
    spec = importlib.util.spec_from_file_location("sloane_sheets", HERE / "sloane-sheets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def numbers(values: list[int]) -> str:
    if len(values) == 1:
        return f"word {values[0]}"
    return "words " + ", ".join(str(value) for value in values[:-1]) + f" and {values[-1]}"


def cut_places() -> int:
    sheets = sheets_module()
    reading = json.loads(READING.read_text(encoding="utf-8"))
    places = json.loads(PLACES.read_text(encoding="utf-8"))["places"]
    PLACES_OUT.mkdir(parents=True, exist_ok=True)
    for old in PLACES_OUT.glob("*.jpg"):
        old.unlink()

    lines = [
        "# Sloane 3191 against the journal data: the places to check",
        "",
        "Each image is cut at full size from the scan of Sloane 3191. Beside it are the spelling in the journal data "
        "(Casaubon's 1659 printing) and the spelling as the manuscript was read. The reading is one reading by eye and "
        "is not confirmed; these are the places where it does not agree with the journal data.",
        "",
        "In a reading, a hyphen is a stroke Dee draws to tie two parts into one word, an underscore is a small gap "
        "with no tie, and a `?` after a letter means that letter was not read with certainty. Accents are typed "
        "where they were seen.",
        "",
        "Words that differ only in u/v or i/j/y have no image here. They are listed in "
        "[sloane-diff.txt](../../sloane-diff.txt).",
        "",
        "To record what you see, fill in `checked` for the place in `tools/sloane/sloane-places.json` and run "
        "`python3 tools/sloane/sloane-cut.py places` again. This page is made by that script, so a change typed here "
        "is lost.",
        "",
    ]
    needed: set[tuple[str, str, int]] = set()
    shown: set[tuple[str, str, int]] = set()
    pages: dict[str, np.ndarray] = {}
    count = 0
    for stem in [f"{number:02d}" for number in range(1, 19)] + ["aethyrs"]:
        data = json.loads((JOURNAL / f"{stem}.json").read_text(encoding="utf-8"))
        entries = data["words"]
        journal = [entry["letters"].lower() for entry in entries]
        read = reading["calls"][stem]
        rows, loose = sheets.compare(journal, sheets.reading_words(journal, read))
        for index, (_, mark, kind) in enumerate(rows):
            if mark != "agrees" and kind != "u/v or i/j/y only":
                needed.add((stem, "word", index + 1))
        for after, _ in loose:
            needed.add((stem, "after", after + 1))

        title = "The call of the thirty Aethyrs" if stem == "aethyrs" else f"Call {int(stem)}"
        mine = [place for place in places if place["call"] == stem]
        if not mine:
            continue
        lines += [f"## {title}", "", f"{read['where']}. The whole call: [{stem}.jpg](../sloane-calls/{stem}.jpg)", ""]
        for remark in read.get("remarks", []):
            lines.append(f"- Remark on the manuscript: {remark}")
        if read.get("remarks"):
            lines.append("")
        for place in mine:
            words, afters = place.get("words", []), place.get("after", [])
            name = f"{stem}-w{words[0]:03d}.jpg" if words else f"{stem}-after{afters[0]:03d}.jpg"
            if place["page"] not in pages:
                pages[place["page"]] = load(place["page"])
            save(cut_box(pages[place["page"]], place["box"]), PLACES_OUT / name)
            count += 1
            head = numbers(words) if words else "after " + numbers(afters)
            lines += [f"### {title}, {head}", ""]
            for number in words:
                entry = entries[number - 1]
                written, mark, kind = rows[number - 1]
                page = f"p. {entry['page']}" if entry.get("page") else "not in the printing"
                lines.append(f"- Word {number}: journal `{entry['letters']}` ({entry['status']}, {page}); "
                             f"Sloane as read `{' '.join(written) or '-'}`; {mark}" + (f": {kind}" if kind else ""))
                shown.add((stem, "word", number))
            for number in afters:
                for after, word in loose:
                    if after + 1 == number:
                        lines.append(f"- After word {number}: Sloane as read `{word}`; only in the manuscript")
                shown.add((stem, "after", number))
            if place.get("note"):
                lines.append(f"- {place['note']}")
            lines += ["", f"![{title}, {head}]({name})", "",
                      f"Checked: {place.get('checked') or 'not yet'}", ""]

    (PLACES_OUT / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {count} images and index.md in {PLACES_OUT.relative_to(ROOT)}")
    missing = sorted(needed - shown)
    print(f"places needed: {len(needed)}; shown: {len(needed & shown)}; missing: {len(missing)}")
    for stem, kind, number in missing:
        print(f"  missing: {stem} {'after ' if kind == 'after' else ''}word {number}")
    for stem, kind, number in sorted(shown - needed):
        print(f"  shown but not needed: {stem} {'after ' if kind == 'after' else ''}word {number}")
    return 0


def main(arguments: list[str]) -> int:
    if arguments == ["calls"]:
        return cut_calls()
    if arguments == ["places"]:
        return cut_places()
    if arguments == ["proof"]:
        return cut_proof()
    if len(arguments) == 2 and arguments[0] == "grid":
        return cut_grid(arguments[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
