"""Flatten the keyed transcription of Casaubon's 1659 printing into rows and paragraphs.

Reads docs/casaubon-1659-true-and-faithful-relation.xml and writes
scratch/casaubon-flat.txt. Every table row gets a number that stays the same
between runs, so the journal data can point at the row a word came from.

A character the keyers could not read is written as a gap mark, never dropped:
  [gap:1 letter]   one illegible letter
  [gap:1 word]     one illegible word
  [gap:foreign]    text in another script that was not keyed
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "casaubon-1659-true-and-faithful-relation.xml"
DEST = ROOT / "scratch" / "casaubon-flat.txt"

BLOCKS = {
    "p", "head", "item", "l", "lg", "list", "div", "opener", "closer", "salute",
    "signed", "dateline", "trailer", "label", "q", "floatingText", "body", "front",
    "figure", "desc",
}


def local(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def gap_mark(element: ET.Element) -> str:
    reason = element.get("reason", "")
    extent = element.get("extent", "")
    if reason.startswith("illegible"):
        return f"[gap:{extent or 'unknown'}]"
    return f"[gap:{reason}]"


class Flattener:
    def __init__(self) -> None:
        self.page = "front"
        self.lines: list[str] = []
        self.rows: list[dict] = []
        self.buffer: list[str] = []

    def flush(self) -> None:
        text = " ".join("".join(self.buffer).split())
        self.buffer = []
        if text:
            self.lines.append(f"p{self.page} TXT  {text}")

    def inline(self, element: ET.Element) -> str:
        """Text of one cell or note, with gaps and margin notes marked."""
        parts: list[str] = [element.text or ""]
        for child in element:
            tag = local(child)
            if tag == "gap":
                parts.append(gap_mark(child))
            elif tag == "g":
                ref = child.get("ref", "")
                if ref not in {"char:EOLhyphen", "char:EOLunhyphen"}:
                    parts.append(f"[{ref}]")
            elif tag == "pb":
                self.page = child.get("n") or f"?{child.get('facs', '')}"
                parts.append(f" [page {self.page}] ")
            elif tag == "note":
                parts.append(" {note: " + self.inline(child) + "} ")
            elif tag == "lb":
                parts.append(" / ")
            elif tag == "table":
                parts.append(" {table: " + " ;; ".join(
                    " | ".join(" ".join(self.inline(cell).split()) for cell in row) for row in child if local(row) == "row"
                ) + "} ")
            else:
                parts.append(self.inline(child))
            parts.append(child.tail or "")
        return "".join(parts)

    def table(self, element: ET.Element) -> None:
        self.flush()
        for child in element:
            tag = local(child)
            if tag == "pb":
                self.page = child.get("n") or f"?{child.get('facs', '')}"
                self.lines.append(f"===== page {self.page} ({child.get('facs', '')}) =====")
                continue
            if tag != "row":
                text = " ".join(self.inline(child).split())
                if text:
                    self.lines.append(f"p{self.page} TBL? <{tag}> {text}")
                continue
            page = self.page
            cells = [" ".join(self.inline(cell).split()) for cell in child]
            number = len(self.rows) + 1
            self.rows.append({"row": number, "page": page, "cells": cells})
            self.lines.append(f"p{page} R{number:05d} " + " | ".join(cells))

    def walk(self, element: ET.Element) -> None:
        tag = local(element)
        if tag == "pb":
            self.flush()
            self.page = element.get("n") or f"?{element.get('facs', '')}"
            self.lines.append(f"===== page {self.page} ({element.get('facs', '')}) =====")
            return
        if tag == "table":
            self.table(element)
            return
        if tag == "gap":
            self.buffer.append(gap_mark(element))
            return
        if tag == "g":
            ref = element.get("ref", "")
            if ref not in {"char:EOLhyphen", "char:EOLunhyphen"}:
                self.buffer.append(f"[{ref}]")
            return
        if tag == "lb":
            self.buffer.append(" / ")
            return
        block = tag in BLOCKS
        if block:
            self.flush()
        if tag == "note":
            self.buffer.append(" {note: ")
        self.buffer.append(element.text or "")
        for child in element:
            self.walk(child)
            self.buffer.append(child.tail or "")
        if tag == "note":
            self.buffer.append("} ")
        if block:
            self.flush()


def flatten() -> Flattener:
    tree = ET.parse(SOURCE)
    text = next(element for element in tree.getroot().iter() if local(element) == "text")
    flat = Flattener()
    flat.walk(text)
    flat.flush()
    return flat


def main() -> int:
    flat = flatten()
    DEST.write_text("\n".join(flat.lines) + "\n", encoding="utf-8")
    print(f"{DEST.relative_to(ROOT)}: {len(flat.lines)} lines, {len(flat.rows)} table rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
