"""Pair Call words with the English lines where the words line up."""

import re
from collections import defaultdict
from pathlib import Path

folder = Path("calls")
word = re.compile(r"[A-Za-z]+")
split = re.compile(r"[,:;.\n]+")
SKIP = {"the", "a", "an", "of"}


def tokens(text: str) -> list[str]:
    return [item.lower() for item in word.findall(text)]


def pieces(text: str) -> list[list[str]]:
    return [tokens(part) for part in split.split(text) if tokens(part)]


def content(words: list[str]) -> list[str]:
    return [item for item in words if item not in SKIP]


def load_pairs() -> list[tuple[list[str], list[str]]]:
    found = []
    for number in list(range(1, 19)) + [19]:
        stem = f"{number:02d}"
        call_name = f"{stem}.txt" if number < 19 else "19-lil.txt"
        english = [
            tokens(line)
            for line in (folder / "english" / f"{stem}.txt").read_text().splitlines()
            if tokens(line)
        ]
        call = pieces((folder / call_name).read_text())
        found.extend(zip(call, english))
    return found


def add(glosses: dict[str, list[str]], spelling: str, meaning: str) -> None:
    meaning = " ".join(meaning.split())
    if not meaning or meaning in SKIP:
        return
    current = glosses[spelling]
    if meaning not in current:
        current.append(meaning)


def main() -> None:
    pairs = load_pairs()
    glosses: dict[str, list[str]] = defaultdict(list)
    for spellings, english in pairs:
        if len(spellings) == 1:
            add(glosses, spellings[0], " ".join(english))
            continue
        kept = content(english)
        if len(kept) == len(spellings):
            for spelling, meaning in zip(spellings, kept):
                add(glosses, spelling, meaning)

    # A line with one unknown word gives that word the English that is left.
    grew = True
    while grew:
        grew = False
        for spellings, english in pairs:
            unknown = [spelling for spelling in spellings if spelling not in glosses]
            if len(unknown) != 1:
                continue
            rest = [item for item in english]
            consumed = True
            for spelling in spellings:
                if spelling == unknown[0]:
                    continue
                meanings = glosses[spelling]
                if len(meanings) != 1:
                    consumed = False
                    break
                meaning = meanings[0].split()
                placed = False
                for start in range(len(rest)):
                    window = [item for item in rest[start:] if item not in SKIP]
                    if window[: len(meaning)] == meaning:
                        # Drop the skipped words in front of the match, then the match.
                        seen = 0
                        index = start
                        while seen < len(meaning) and index < len(rest):
                            if rest[index] not in SKIP:
                                seen += 1
                            index += 1
                        del rest[start:index]
                        placed = True
                        break
                if not placed:
                    consumed = False
                    break
            if consumed and rest:
                before = len(glosses[unknown[0]])
                add(glosses, unknown[0], " ".join(rest))
                grew = grew or len(glosses[unknown[0]]) != before

    lines = ["# spelling: english, english\n"]
    for spelling, meanings in sorted(glosses.items()):
        lines.append(f"{spelling}: {', '.join(meanings)}\n")
    destination = folder / "dictionary.txt"
    destination.write_text("".join(lines), encoding="utf-8")
    print(f"{len(glosses)} spellings written to {destination}")


if __name__ == "__main__":
    main()
