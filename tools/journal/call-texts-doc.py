"""Fill the lists in docs/call-texts.md from calls/journal/.

The prose of the doc is written by hand. Each list sits between a pair of
markers, <!-- NAME:start --> and <!-- NAME:end -->, and this script replaces
what is between them. The uncertain and note-differs lists use the same two
functions as tools/journal/journal-lists.py, so the doc and
scratch/journal-lists.txt cannot disagree.

Usage: python3 tools/journal/call-texts-doc.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOC = ROOT / "docs" / "call-texts.md"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lists = load("journal-lists")
build = load("journal-build")


def cell(text: str) -> str:
    """Plain text made safe for a table cell."""
    text = " ".join(str(text).split())
    for mark in "\\|*_<>":
        text = text.replace(mark, "\\" + mark)
    return text


def code(text: str) -> str:
    return f"`{text}`" if text else ""


def table(head: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def counts() -> list[str]:
    found: dict[str, int] = {}
    for _label, _number, entry in lists.rows():
        found[entry["status"]] = found.get(entry["status"], 0) + 1
    total = sum(found.values())
    unsure = sum(count for status, count in found.items() if status not in lists.SURE)
    order = ["printed", "corrected", "from_note", "gap", "conflict", "not_printed"]
    parts = ", ".join(f"{found.get(status, 0)} `{status}`" for status in order)
    return [f"The journal data has {total} words, counting the thirty Aethyr names: {parts}. "
            f"{unsure} are uncertain."]


def uncertain() -> list[str]:
    rows = []
    for label, number, entry in lists.rows():
        if not lists.uncertain(entry) or entry.get("repeat_of") or entry["status"] == "not_printed":
            continue
        rows.append([label, str(number), str(entry["page"]), code(entry["status"]), code(entry["letters"]),
                     code(entry.get("column", "")), cell(entry["note"]), cell(entry.get("other", ""))])
    return table(["Call", "Word", "Page", "Status", "Spelling", "Column", "Dee's note", "Other letters"], rows)


def repeats() -> list[str]:
    rows = []
    for label, number, entry in lists.rows():
        if not lists.uncertain(entry) or not entry.get("repeat_of"):
            continue
        again = entry["repeat_of"]
        rows.append([label, str(number), str(entry["page"]), code(entry["status"]), code(entry["letters"]),
                     f"Call {again['call']} word {again['word']}"])
    return table(["Call", "Word", "Page", "Status", "Spelling", "Repeats"], rows)


def not_printed() -> list[str]:
    runs: dict[str, list[tuple[int, str]]] = {}
    for label, number, entry in lists.rows():
        if entry["status"] == "not_printed":
            runs.setdefault(label, []).append((number, entry["letters"]))
    rows = []
    for label, words in runs.items():
        numbers = f"{words[0][0]} to {words[-1][0]}" if len(words) > 1 else str(words[0][0])
        rows.append([label, numbers, str(len(words)), " ".join(code(letters) for _, letters in words)])
    return table(["Call", "Words", "Count", "Spellings"], rows)


def note_differs() -> list[str]:
    rows = []
    for label, number, entry in lists.rows():
        if not lists.note_differs(entry):
            continue
        rows.append([label, str(number), str(entry["page"]), code(entry["letters"]),
                     code(entry.get("column", "")), cell(entry["note"])])
    return table(["Call", "Word", "Page", "Spelling", "Column", "Dee's note"], rows)


def corrected() -> list[str]:
    rows = []
    for label, number, entry in lists.rows():
        if entry["status"] != "corrected" or entry.get("repeat_of"):
            continue
        said = entry.get("remark") or entry["note"]
        rows.append([label, str(number), str(entry.get("correction_page", entry["page"])), code(entry["letters"]),
                     code(entry.get("column", "")), cell(said)])
    return table(["Call", "Word", "Page", "Spelling", "Column", "What the journal says"], rows)


def keyed() -> list[str]:
    rows = []
    for row_id in sorted(build.IMAGE_READINGS):
        for as_keyed, as_printed in build.IMAGE_READINGS[row_id]:
            rows.append([str(build.ROWS[row_id]["page"]), code(as_keyed), code(as_printed)])
    return table(["Page", "As keyed", "As the page image prints it"], rows)


BLOCKS = {"counts": counts, "uncertain": uncertain, "repeats": repeats, "not-printed": not_printed,
          "note-differs": note_differs, "corrected": corrected, "keyed": keyed}


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    sizes = []
    for name, make in BLOCKS.items():
        pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(<!-- {name}:end -->)", re.S)
        if not pattern.search(text):
            raise SystemExit(f"{DOC.name} has no {name} markers")
        lines = make()
        text = pattern.sub(lambda found: found.group(1) + "\n".join(lines) + "\n" + found.group(2), text)
        sizes.append(f"{name} {len(lines)}")
    DOC.write_text(text, encoding="utf-8")
    print(f"filled {DOC.relative_to(ROOT)}: " + ", ".join(sizes) + " lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
