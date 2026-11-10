"""Turn a document into a WAV of Enochian words."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet
from enochaeon.audio import Gaps, silence, write_wav
from enochaeon.synthesize import speak


def render(text: str, alphabet: Alphabet, gaps: Gaps | None = None) -> np.ndarray:
    gaps = gaps or Gaps()
    pieces: list[np.ndarray] = []
    for item in alphabet.atom_ids(text):
        if isinstance(item, str):
            pieces.append(silence(gaps.nl_ms if item == "\n" else gaps.word_ms))
            continue
        phonemes = alphabet.pronounce_atoms(tuple(alphabet.atoms[atom_id] for atom_id in item))
        pieces.append(speak(phonemes))
    if not pieces:
        return silence(gaps.word_ms)
    return np.concatenate(pieces)


def write_traces(source: Path, text: str, alphabet: Alphabet) -> list[Path]:
    """Write the Hebrew, Enochian, and phonetic stages beside the source file.

    The files live in a hidden directory next to the source, named with its stem:
    ``.enochaeon/notes-test-hebrew.txt``.
    """
    folder = source.parent / ".enochaeon"
    folder.mkdir(parents=True, exist_ok=True)
    stages = (
        ("hebrew", alphabet.hebrew(text)),
        ("enochian", alphabet.enochian_text(text)),
        ("phonetic", alphabet.phonetic_text(text)),
    )
    written: list[Path] = []
    for kind, content in stages:
        if content and not content.endswith("\n"):
            content += "\n"
        path = folder / f"{source.stem}-{kind}.txt"
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def write_document(text: str, dest: Path, alphabet: Alphabet, gaps: Gaps | None = None) -> None:
    gaps = gaps or Gaps()
    audio = render(text, alphabet, gaps)
    write_wav(dest, audio, comment=gaps.comment())
