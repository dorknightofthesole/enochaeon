"""Call spellings, and the English words listed for them in the lexicon.

The cipher does not read this. Translate reads the English glosses.
Calls and translations speak dee_ipa or golden_dawn_ipa. A variant shares
its root's English and its root's pronunciation. Hebrew is not spoken.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from enochaeon.enochian import phonetic_text
from enochaeon.errors import EnochaeonError

_WORD = re.compile(r"[A-Za-z]+")


@dataclass(frozen=True)
class Root:
    """One spelling. English words may be empty."""

    spelling: str
    phones: str
    calls: tuple[str, ...]
    glosses: tuple[str, ...]
    pos: str = ""


def load_roots(calls: Path | None = None) -> tuple[Root, ...]:
    """Every spelling in the Calls, with English taken from the dictionary file."""
    folder = calls or _calls_dir()
    glosses, parts, _readings = _lexicon(folder / "lexicon.json")
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
            phones=phonetic_text(spelling).strip(),
            calls=tuple(stems),
            glosses=glosses.get(spelling, ()),
            pos=parts.get(spelling, ""),
        )
        for spelling, stems in sorted(found.items())
    ]
    return tuple(roots)


def load_readings(field: str, calls: Path | None = None) -> dict[str, str]:
    """The lexicon IPA for one reading, keyed by spelling."""
    if field not in {"dee_ipa", "golden_dawn_ipa"}:
        raise EnochaeonError(f"Call reading must be dee_ipa or golden_dawn_ipa, not {field!r}.")
    folder = calls or _calls_dir()
    _glosses, _parts, readings = _lexicon(folder / "lexicon.json")
    return readings[field]


def _calls_dir() -> Path:
    cwd = Path.cwd() / "calls"
    if (cwd / "01.txt").is_file():
        return cwd
    bundled = Path(__file__).resolve().parents[2] / "calls"
    if (bundled / "01.txt").is_file():
        return bundled
    raise EnochaeonError(f"No calls in {cwd}.")


def _call_texts(folder: Path) -> list[tuple[str, str]]:
    files = sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt" and not path.name.startswith(".")
    )
    if not files:
        raise EnochaeonError(f"No call files in {folder}.")
    return [(path.stem, path.read_text(encoding="utf-8")) for path in files]


def _words(text: str) -> list[str]:
    return [word.lower() for word in _WORD.findall(text)]


def _lexicon(
    path: Path,
) -> tuple[dict[str, tuple[str, ...]], dict[str, str], dict[str, dict[str, str]]]:
    if not path.is_file():
        raise EnochaeonError(f"No lexicon at {path}.")
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EnochaeonError(f"{path.name} is not valid JSON.") from exc
    if not isinstance(entries, list):
        raise EnochaeonError(f"{path.name} must be a list of words.")
    found: dict[str, list[str]] = {}
    parts: dict[str, str] = {}
    readings: dict[str, dict[str, str]] = {"dee_ipa": {}, "golden_dawn_ipa": {}}
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            raise EnochaeonError(f"{path.name} entry {index} must be an object.")
        glosses = _glosses(path, index, entry.get("english_glosses"))
        spellings = _spellings(path, index, entry)
        spoken = {name: _reading(path, index, name, entry.get(name)) for name in readings}
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
            for name, ipa in spoken.items():
                if ipa:
                    readings[name][spelling] = ipa
    return {spelling: tuple(glosses) for spelling, glosses in found.items()}, parts, readings


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


def _reading(path: Path, index: int, name: str, raw: object) -> str:
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise EnochaeonError(f"{path.name} entry {index} {name} must be text.")
    return raw.strip()


def _glosses(path: Path, index: int, raw: object) -> list[str]:
    if not isinstance(raw, list) or not raw:
        raise EnochaeonError(f"{path.name} entry {index} needs english_glosses.")
    glosses: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise EnochaeonError(f"{path.name} entry {index} has a gloss that is not text.")
        gloss = " ".join(item.lower().split())
        if gloss and gloss not in glosses:
            glosses.append(gloss)
    if not glosses:
        raise EnochaeonError(f"{path.name} entry {index} needs an English word.")
    return glosses
