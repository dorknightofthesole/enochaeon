"""Call spellings, and what the lexicon says about each.

The cipher does not read this. Translate reads the English glosses. A variant
shares its root's English. Hebrew is not spoken.

calls/lexicon.json is the one place that says how a word is said. A reading
field lists a string for each spelling of an entry, and load_readings returns
those strings as the file has them. Nothing is worked out here: a spelling
the field does not list has no reading. dee_ipa is the Dee reading. A field
named in enochaeon.json is what one voice is given. golden_dawn_ipa is one
string for the whole entry, and it is empty.

dee_says, dee_note and dee_note_source record a note of Dee's that a stored
reading was made from. This code does not read them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from enochaeon.enochian import _CALL_NAME
from enochaeon.errors import EnochaeonError
from enochaeon.word_ipa import espeak_phones

_WORD = re.compile(r"[A-Za-z]+")
DEE_READING = "dee_ipa"


@dataclass(frozen=True)
class Root:
    """One spelling. phones is its stored Dee reading as espeak phonemes. English words may be empty."""

    spelling: str
    phones: str
    calls: tuple[str, ...]
    glosses: tuple[str, ...]
    pos: str = ""


def load_roots(calls: Path | None = None) -> tuple[Root, ...]:
    """Every spelling in the Calls, with English taken from the dictionary file."""
    folder = calls or _calls_dir()
    glosses, parts = _lexicon(folder / "lexicon.json")
    stored = load_readings(DEE_READING, folder)
    found: dict[str, list[str]] = {}
    for stem, text in _call_texts(folder):
        for spelling in _words(text):
            found.setdefault(spelling, [])
            if stem not in found[spelling]:
                found[spelling].append(stem)
    for spelling in glosses:
        found.setdefault(spelling, [])
    roots = [
        Root(
            spelling=spelling,
            phones=espeak_phones(stored[spelling]) if spelling in stored else "",
            calls=tuple(stems),
            glosses=glosses.get(spelling, ()),
            pos=parts.get(spelling, ""),
        )
        for spelling, stems in sorted(found.items())
    ]
    return tuple(roots)


def load_readings(field: str, calls: Path | None = None) -> dict[str, str]:
    """One reading field of the lexicon, keyed by spelling, as the file has it.

    A field that lists a string for each spelling gives each spelling its own.
    A field that is one string is the reading of every spelling of the entry.
    """
    folder = calls or _calls_dir()
    path = folder / "lexicon.json"
    readings: dict[str, str] = {}
    for index, entry in enumerate(_entries(path), 1):
        listed = entry.get(field)
        if not listed:
            continue
        spellings = _spellings(path, index, entry)
        if isinstance(listed, str):
            listed = {spelling: listed for spelling in spellings} if listed.strip() else {}
        if not isinstance(listed, dict):
            raise EnochaeonError(f"{path.name} entry {index} {field} must list a reading for each spelling.")
        for name, reading in listed.items():
            spelling = name.lower()
            if spelling not in spellings:
                raise EnochaeonError(f"{path.name} entry {index} {field} has {name!r}, which is not a spelling of it.")
            if not isinstance(reading, str) or not reading.strip():
                raise EnochaeonError(f"{path.name} entry {index} {field} {name!r} must be text.")
            readings[spelling] = reading.strip()
    return readings


def _calls_dir() -> Path:
    cwd = Path.cwd() / "calls"
    if (cwd / "01.txt").is_file():
        return cwd
    bundled = Path(__file__).resolve().parents[2] / "calls"
    if (bundled / "01.txt").is_file():
        return bundled
    raise EnochaeonError(f"No calls in {cwd}.")


def _call_texts(folder: Path) -> list[tuple[str, str]]:
    files = sorted(path for path in folder.iterdir() if _CALL_NAME.fullmatch(path.name))
    if not files:
        raise EnochaeonError(f"No call files in {folder}.")
    return [(path.stem, path.read_text(encoding="utf-8")) for path in files]


def _words(text: str) -> list[str]:
    return [word.lower() for word in _WORD.findall(text)]


def _lexicon(path: Path) -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    """The English words and the part of speech of each spelling."""
    found: dict[str, list[str]] = {}
    parts: dict[str, str] = {}
    for index, entry in enumerate(_entries(path), 1):
        glosses = _glosses(path, index, entry.get("english_glosses"))
        spellings = _spellings(path, index, entry)
        part = " ".join(str(entry.get("pos") or "").lower().split())
        root = spellings[0]
        for spelling in spellings:
            bucket = found.setdefault(spelling, [])
            for gloss in glosses:
                if gloss not in bucket:
                    bucket.append(gloss)
            if spelling == root or spelling not in parts:
                if part:
                    parts[spelling] = part
    return {spelling: tuple(glosses) for spelling, glosses in found.items()}, parts


def _entries(path: Path) -> list[dict]:
    if not path.is_file():
        raise EnochaeonError(f"No lexicon at {path}.")
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EnochaeonError(f"{path.name} is not valid JSON.") from exc
    if not isinstance(entries, list):
        raise EnochaeonError(f"{path.name} must be a list of words.")
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            raise EnochaeonError(f"{path.name} entry {index} must be an object.")
    return entries


def _spellings(path: Path, index: int, entry: dict) -> list[str]:
    names = [entry.get("root"), *(entry.get("variants") or [])]
    spellings: list[str] = []
    for name in names:
        if not isinstance(name, str):
            raise EnochaeonError(f"{path.name} entry {index} needs a spelling.")
        spelling = "".join(character for character in name.lower() if character.isalpha())
        if spelling and spelling not in spellings:
            spellings.append(spelling)
    if not spellings:
        raise EnochaeonError(f"{path.name} entry {index} needs a spelling.")
    return spellings


def _glosses(path: Path, index: int, raw: object) -> list[str]:
    if not isinstance(raw, list):
        raise EnochaeonError(f"{path.name} entry {index} needs english_glosses.")
    glosses: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise EnochaeonError(f"{path.name} entry {index} has a gloss that is not text.")
        gloss = " ".join(item.lower().split())
        if gloss and gloss not in glosses:
            glosses.append(gloss)
    if raw and not glosses:
        raise EnochaeonError(f"{path.name} entry {index} needs an English word.")
    return glosses
