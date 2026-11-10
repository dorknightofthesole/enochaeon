"""English text to Hebrew letters, Enochian letters, and the spelling Leitch reads."""

from __future__ import annotations

from enochaeon.alphabet import ALPHABET_PATH, Alphabet, Gap, Segment, Word

__all__ = [
    "ALPHABET_PATH",
    "Alphabet",
    "Gap",
    "Segment",
    "Word",
    "load_alphabet",
]


def load_alphabet() -> Alphabet:
    return Alphabet.load()
