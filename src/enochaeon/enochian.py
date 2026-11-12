"""Speak a text that is already written in Enochian letters.

A call is not English. A word is spoken from the reading calls/lexicon.json
has for it: dee_ipa, golden_dawn_ipa, or the field enochaeon.json names for
a Piper voice. A word with no reading is left out. The cipher does not come
here.

The letter rule is here too, and its sounds are in data/call_letters.json.
It is not on the speech path. It is how a new spelling is given a first
reading to store.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import re

import numpy as np

from enochaeon.alphabet import (
    DATA_DIR,
    PUNCT_BREAKS,
    PUNCT_SKIP,
    TransliterationError,
    pronounce_syllables,
)
from enochaeon.audio import Gaps, silence, write_wav
from enochaeon.config import CallVoice
from enochaeon.errors import EnochaeonError
from enochaeon.synthesize import speak

# A comma stays inside the line. A stop ends it. Digits have no Enochian letter.
_BREAKS = PUNCT_BREAKS
_SKIP = PUNCT_SKIP | set("0123456789")
_CALL_NAME = re.compile(r"^\d{2}(?:-[a-z]+)?\.txt$")
LETTERS_PATH = DATA_DIR / "call_letters.json"


@dataclass(frozen=True)
class Letter:
    latin: str
    phone: str
    name: str
    long: str = ""

    @property
    def vowel(self) -> bool:
        # A letter with a long sound is a vowel. J is the vowel I.
        return bool(self.long)


def _load_letters() -> tuple[dict[str, Letter], dict[str, str]]:
    """Dee's alphabet in Latin letters, and the letter that stands for another before a vowel."""
    try:
        data = json.loads(LETTERS_PATH.read_text(encoding="utf-8"))
        letters = {
            row["latin"]: Letter(latin=row["latin"], phone=row["phone"], name=row["name"], long=row.get("long", ""))
            for row in data["letters"]
        }
        initial = dict(data["initial_before_vowel"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise EnochaeonError(f"{LETTERS_PATH.name} is not the table of call letters. {exc}") from exc
    if any(stand_in not in letters for stand_in in initial.values()):
        raise EnochaeonError(f"{LETTERS_PATH.name} initial_before_vowel names a letter that has no row.")
    return letters, initial


# The sounds are in the data file. The speech path uses this table to know
# which characters are letters. Only the letter rule reads the sounds.
LETTERS, _INITIAL_BEFORE_VOWEL = _load_letters()


def parse(text: str) -> list[list[Letter] | str]:
    """Words of Enochian letters, with a space or a newline between them."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    if cleaned.startswith("\ufeff"):
        cleaned = cleaned[1:]
    segments: list[list[Letter] | str] = []
    index = 0
    while index < len(cleaned):
        character = cleaned[index]
        if character in _SKIP:
            index += 1
            continue
        if character.isspace() or character in _BREAKS:
            newline = _BREAKS.get(character) == "\n" or character == "\n"
            while index < len(cleaned) and (
                cleaned[index].isspace() or cleaned[index] in _BREAKS or cleaned[index] in _SKIP
            ):
                mark = cleaned[index]
                newline = newline or _BREAKS.get(mark) == "\n" or mark == "\n"
                index += 1
            segments.append("\n" if newline else " ")
            continue
        if not character.isalpha():
            raise TransliterationError(character, index)
        word: list[Letter] = []
        while index < len(cleaned) and cleaned[index].isalpha():
            letter = LETTERS.get(cleaned[index].upper())
            if letter is None:
                raise TransliterationError(cleaned[index], index)
            word.append(letter)
            index += 1
        segments.append(word)
    return _trim_gaps(segments)


def phonetic_text(text: str) -> str:
    """The letter rule: what the table of call letters says from the letters alone.

    The speech path does not call this. Calls speak the reading stored in the
    lexicon, and leave other words out. tools/lexicon/letter-readings.py uses
    the rule to give a new spelling its first reading.
    """
    parts: list[str] = []
    for segment in parse(text):
        if isinstance(segment, str):
            parts.append(segment)
            continue
        parts.append(pronounce_syllables(_initial_i(segment)))
    return "".join(parts)


def letter_ipa(spelling: str) -> str:
    """The letter rule for one spelling, stored as slash IPA."""
    from enochaeon.word_ipa import ipa_of_espeak

    return ipa_of_espeak(phonetic_text(spelling).strip())


def audible(text: str, readings: dict[str, str]) -> tuple[list[list[Letter] | str], tuple[str, ...]]:
    """Words that have a reading, and the spellings left out.

    A gap is kept only between words that are spoken. A line break wins over a
    space when a dropped word sat between them.
    """
    kept: list[list[Letter] | str] = []
    dropped: list[str] = []
    pending: str | None = None
    for segment in parse(text):
        if isinstance(segment, str):
            pending = "\n" if "\n" in (pending, segment) else segment
            continue
        if not _listed(segment, readings):
            dropped.append(_spelling(segment))
            continue
        if kept and pending:
            kept.append(pending)
        pending = None
        kept.append(segment)
    return kept, tuple(dropped)


def spoken_text(segments: list[list[Letter] | str]) -> str:
    """The spellings that will be spoken, with their gaps."""
    parts: list[str] = []
    for segment in segments:
        if isinstance(segment, str):
            parts.append("\n" if segment == "\n" else " ")
            continue
        parts.append(_spelling(segment))
    return "".join(parts).strip()


def call_gaps(voice: CallVoice | None = None, gaps: Gaps | None = None) -> Gaps:
    """Silences for one Call. Piper may shorten the breath; espeak keeps the shared gap."""
    voice = voice or CallVoice()
    chosen = gaps or Gaps()
    if voice.engine == "piper" and voice.word_ms is not None:
        return replace(chosen, word_ms=voice.word_ms)
    return chosen


def render(
    text: str,
    gaps: Gaps | None = None,
    voice: CallVoice | None = None,
    readings: dict[str, str] | None = None,
) -> np.ndarray:
    """One spoken breath per word, with a silence between words and lines."""
    voice = voice or CallVoice()
    gaps = call_gaps(voice, gaps)
    readings = _readings(voice) if readings is None else readings
    segments, _dropped = audible(text, readings)
    if voice.engine == "piper":
        from enochaeon.piper_voice import render as render_piper

        return render_piper(text, voice, gaps, readings)
    pieces: list[np.ndarray] = []
    for segment in segments:
        if isinstance(segment, str):
            pieces.append(silence(gaps.nl_ms if segment == "\n" else gaps.word_ms))
            continue
        pieces.append(_speak_segment(segment, readings))
    if not pieces:
        return silence(gaps.word_ms)
    return np.concatenate(pieces)


def _readings(voice: CallVoice) -> dict[str, str]:
    """The readings the voice speaks. A Piper voice with its own lexicon field speaks that field."""
    from enochaeon.roots import load_readings

    if voice.engine == "piper" and voice.piper_ipa:
        return load_readings(voice.piper_ipa)
    return load_readings(voice.ipa)


def _speak_segment(word: list[Letter], readings: dict[str, str]) -> np.ndarray:
    from enochaeon.word_ipa import espeak_phones

    return speak(espeak_phones(_listed(word, readings)))


def _listed(word: list[Letter], readings: dict[str, str]) -> str:
    return readings.get(_spelling(word), "")


def _spelling(word: list[Letter]) -> str:
    return "".join(letter.latin for letter in word).lower()


def write_call(path: Path, force: bool, voice: CallVoice | None = None) -> Path:
    """Write the WAV for one call file."""
    dest = path.with_suffix(".wav")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    voice = voice or CallVoice()
    gaps = call_gaps(voice)
    text = path.read_text(encoding="utf-8")
    _segments, dropped = audible(text, _readings(voice))
    if not _segments:
        raise EnochaeonError(f"Nothing in {path.name} has a {voice.ipa} reading.")
    if dropped:
        print("left out: " + " ".join(dropped))
    write_wav(dest, render(text, gaps=gaps, voice=voice), comment=gaps.comment())
    print(dest)
    return dest


def call_files(path: Path) -> list[Path]:
    """The one file, or every .txt sitting in the directory."""
    if path.is_file():
        if path.suffix.lower() != ".txt":
            raise EnochaeonError(f"{path.name} is not a .txt file")
        return [path]
    if not path.is_dir():
        raise EnochaeonError(f"No such file or directory: {path}")
    files = sorted(item for item in path.iterdir() if _CALL_NAME.fullmatch(item.name))
    if not files:
        raise EnochaeonError(f"No call files in {path}")
    return files


def generate_calls(path: Path, force: bool, voice: CallVoice | None = None) -> int:
    files = call_files(path)
    destinations = [item.with_suffix(".wav") for item in files]
    blocked = [dest for dest in destinations if dest.exists() and not force]
    if blocked:
        raise EnochaeonError(f"{blocked[0]} already exists. Pass --force to replace it.")
    for item in files:
        write_call(item, force, voice)
    return 0


def _initial_i(word: list[Letter]) -> list[Letter]:
    """The first letter before a vowel, as the table gives it. Dee read Iad as Yad."""
    if len(word) >= 2 and word[0].latin in _INITIAL_BEFORE_VOWEL and word[1].vowel:
        return [LETTERS[_INITIAL_BEFORE_VOWEL[word[0].latin]], *word[1:]]
    return word


def _trim_gaps(segments: list[list[Letter] | str]) -> list[list[Letter] | str]:
    """Drop pauses that do not sit between words, and fold repeated pauses."""
    trimmed = list(segments)
    while trimmed and isinstance(trimmed[0], str):
        trimmed.pop(0)
    while trimmed and isinstance(trimmed[-1], str):
        trimmed.pop()
    collapsed: list[list[Letter] | str] = []
    for segment in trimmed:
        if isinstance(segment, str) and collapsed and isinstance(collapsed[-1], str):
            collapsed[-1] = "\n" if "\n" in (segment, collapsed[-1]) else " "
            continue
        collapsed.append(segment)
    return collapsed
