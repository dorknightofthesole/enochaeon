"""List every difference between the call files and the journal data.

Reads tools/journal/calls-before/ (the call files as they were before the rewrite)
and calls/journal/. Writes scratch/call-text-diff.txt.

A difference is one of:
  spelling     the same place has different letters
  word break   the same letters are divided into words differently
  missing      the journal has a word the call file did not
  extra        the call file had a word the journal does not
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BEFORE = Path(__file__).resolve().parent / "calls-before"
JOURNAL = ROOT / "calls" / "journal"
DEST = ROOT / "scratch" / "call-text-diff.txt"


def old_words(path: Path) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z]+", path.read_text(encoding="utf-8"))]


def describe(entry: dict) -> str:
    parts = [f"p. {entry['page']}" if entry["page"] else "no page", entry["status"]]
    if entry.get("column"):
        parts.append(f"column {entry['column']!r}")
    if entry["note"]:
        parts.append(f"note {entry['note'][:70]!r}")
    return ", ".join(parts)


def compare(title: str, old: list[str], entries: list[dict]) -> tuple[list[str], dict[str, int]]:
    new = [entry["letters"].lower() for entry in entries]
    lines = [f"== {title}: {len(old)} words before, {len(new)} in the journal"]
    counts = {"spelling": 0, "word break": 0, "missing": 0, "extra": 0}
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, a0, a1, b0, b1 in matcher.get_opcodes():
        if tag == "equal":
            continue
        before, after = old[a0:a1], new[b0:b1]
        where = f"word {b0 + 1}" if b1 - b0 <= 1 else f"words {b0 + 1} to {b1}"
        detail = "; ".join(describe(entry) for entry in entries[b0:b1])
        if before and after and "".join(before) == "".join(after):
            kind = "word break"
        elif before and after:
            kind = "spelling"
        elif after:
            kind = "missing"
        else:
            kind = "extra"
        counts[kind] += 1
        lines.append(f"  {kind:10} {where:16} before: {' '.join(before) or '-':28} journal: {' '.join(after) or '-'}")
        if detail:
            lines.append(f"             {detail}")
    if len(lines) == 1:
        lines.append("  no difference")
    return lines, counts


def main() -> int:
    out: list[str] = []
    total = {"spelling": 0, "word break": 0, "missing": 0, "extra": 0}
    for number in range(1, 19):
        data = json.loads((JOURNAL / f"{number:02d}.json").read_text(encoding="utf-8"))
        lines, counts = compare(f"Call {number:02d}", old_words(BEFORE / f"{number:02d}.txt"), data["words"])
        out += lines + [""]
        for kind, count in counts.items():
            total[kind] += count
    aethyrs = json.loads((JOURNAL / "aethyrs.json").read_text(encoding="utf-8"))
    files = sorted(path for path in BEFORE.iterdir() if re.fullmatch(r"(19|[2-4]\d)-[a-z]+\.txt", path.name))
    for index, path in enumerate(files):
        entries = [dict(entry) for entry in aethyrs["words"]]
        entries[aethyrs["name_word"]] = aethyrs["names"][index]
        title = f"Aethyr {index + 1}, {path.name}, journal name {aethyrs['names'][index]['letters']}"
        lines, counts = compare(title, old_words(path), entries)
        if index == 0:
            out += lines + [""]
            for kind, count in counts.items():
                total[kind] += count
        else:
            # The thirty files share one call. After the first, list only the name.
            old_name = old_words(path)[3] if len(old_words(path)) > 3 else "-"
            new_name = aethyrs["names"][index]["letters"].lower()
            mark = "same" if old_name == new_name else "DIFFERENT"
            out.append(f"== {title}: name before {old_name}, journal {new_name}: {mark}; the rest as Aethyr 1")
            if old_name != new_name:
                total["spelling"] += 1
    out.append("")
    out.append("Totals: " + ", ".join(f"{count} {kind}" for kind, count in total.items()))
    DEST.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{DEST.relative_to(ROOT)}: " + ", ".join(f"{count} {kind}" for kind, count in total.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
