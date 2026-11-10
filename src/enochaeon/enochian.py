"""Speak a text that is already written in Enochian letters.

A call is not English. The letters are the ones Dee wrote (A, B, C, and the
rest), and the same syllable rule used for a cipher word reads them: an open
vowel is long, a closed vowel is short, and a word with no vowel is letter-names.
A word-initial I before a vowel is Y, which is how Dee said Iad.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from enochaeon.alphabet import PUNCT_BREAKS, PUNCT_SKIP, TransliterationError, pronounce_syllables
from enochaeon.audio import Gaps, silence, write_wav
from enochaeon.errors import EnochaeonError
from enochaeon.synthesize import speak

# A comma stays inside the line. A stop ends it. Digits have no Enochian letter.
_BREAKS = PUNCT_BREAKS
_SKIP = PUNCT_SKIP | set("0123456789")


@dataclass(frozen=True)
class Letter:
    latin: str
    phone: str
    name: str
    long: str = ""

    @property
    def vowel(self) -> bool:
        return self.latin in {"A", "E", "I", "O", "U"}


def _letter(latin: str, phone: str, name: str, long: str = "") -> Letter:
    return Letter(latin=latin, phone=phone, name=name, long=long)


# Dee's alphabet in Latin letters. C and K are both the k sound. Y is the
# consonant used when a word starts with I and the next letter is a vowel.
LETTERS: dict[str, Letter] = {
    "A": _letter("A", "a", "A:", "A:"),
    "E": _letter("E", "E", "eI", "eI"),
    "I": _letter("I", "I", "i:", "i:"),
    "O": _letter("O", "Q", "oU", "oU"),
    "U": _letter("U", "U", "u:", "u:"),
    "B": _letter("B", "b", "b'i:"),
    "C": _letter("C", "k", "k'i:"),
    "D": _letter("D", "d", "d'i:"),
    "F": _letter("F", "f", "'Ef"),
    "G": _letter("G", "g", "g'i:"),
    "H": _letter("H", "h", "h'eI"),
    "K": _letter("K", "k", "k'eI"),
    "L": _letter("L", "l", "'El"),
    "M": _letter("M", "m", "'Em"),
    "N": _letter("N", "n", "'En"),
    "P": _letter("P", "p", "p'i:"),
    "Q": _letter("Q", "kw", "kw'A:"),
    "R": _letter("R", "r", "'Ar"),
    "S": _letter("S", "s", "'Es"),
    "T": _letter("T", "t", "t'i:"),
    "V": _letter("V", "v", "v'i:"),
    "W": _letter("W", "w", "w'i:"),
    "X": _letter("X", "ks", "'Eks"),
    "Y": _letter("Y", "j", "j'i:"),
    "Z": _letter("Z", "z", "z'i:"),
}


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
        segments.append(_initial_i(word))
    return _trim_gaps(segments)


def phonetic_text(text: str) -> str:
    """One espeak string per Enochian word."""
    parts: list[str] = []
    for segment in parse(text):
        if isinstance(segment, str):
            parts.append(segment)
            continue
        parts.append(pronounce_syllables(segment))
    return "".join(parts)


def render(text: str, gaps: Gaps | None = None) -> np.ndarray:
    """One spoken breath per word, with a silence between words and lines."""
    gaps = gaps or Gaps()
    pieces: list[np.ndarray] = []
    for segment in parse(text):
        if isinstance(segment, str):
            pieces.append(silence(gaps.nl_ms if segment == "\n" else gaps.word_ms))
            continue
        pieces.append(speak(pronounce_syllables(segment)))
    if not pieces:
        return silence(gaps.word_ms)
    return np.concatenate(pieces)


def write_call(path: Path, force: bool) -> Path:
    """Write the phonetic line and the WAV for one call file."""
    dest = path.with_suffix(".wav")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    text = path.read_text(encoding="utf-8")
    phonetic = phonetic_text(text)
    if phonetic and not phonetic.endswith("\n"):
        phonetic += "\n"
    folder = path.parent / ".enochaeon"
    folder.mkdir(parents=True, exist_ok=True)
    trace = folder / f"{path.stem}-phonetic.txt"
    trace.write_text(phonetic, encoding="utf-8")
    print(trace)
    write_wav(dest, render(text), comment=Gaps().comment())
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
    files = sorted(
        item
        for item in path.iterdir()
        if item.is_file() and item.suffix.lower() == ".txt" and not item.name.startswith(".")
    )
    if not files:
        raise EnochaeonError(f"No call files in {path}")
    return files


def generate_calls(path: Path, force: bool) -> int:
    files = call_files(path)
    destinations = [item.with_suffix(".wav") for item in files]
    blocked = [dest for dest in destinations if dest.exists() and not force]
    if blocked:
        raise EnochaeonError(f"{blocked[0]} already exists. Pass --force to replace it.")
    for item in files:
        write_call(item, force)
    return 0


def _initial_i(word: list[Letter]) -> list[Letter]:
    """Dee read a word-initial I before a vowel as Y. Iad is Yad."""
    if len(word) >= 2 and word[0].latin == "I" and word[1].vowel:
        return [LETTERS["Y"], *word[1:]]
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
