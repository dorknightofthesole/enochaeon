"""Turn a document into a WAV of Enochian letter sounds."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet, syllable_forms
from enochaeon.audio import silence, write_wav
from enochaeon.cipher_voice import Speaker, mark_of
from enochaeon.config import CipherVoice


def render(text: str, alphabet: Alphabet, voice: CipherVoice, speaker: Speaker) -> np.ndarray:
    """Each letter sound alone, with the silence that says what follows it.

    The silence after a letter is the shortest. The one between two words is
    longer, and the one between two lines is longer again. Those three lengths
    are all that tells a letter, a word and a line apart on the way back.
    """
    pieces: list[np.ndarray] = []
    gap = voice.word_ms
    for item in alphabet.atom_ids(text):
        if isinstance(item, str):
            gap = voice.line_ms if item == "\n" else voice.word_ms
            continue
        atoms = tuple(alphabet.atoms[atom_id] for atom_id in item)
        for index, (atom, form) in enumerate(syllable_forms(atoms)):
            if pieces:
                pieces.append(silence(voice.letter_ms if index else gap))
            pieces.append(speaker.sound(atom, form))
    if not pieces:
        return silence(voice.word_ms)
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


def write_document(text: str, dest: Path, alphabet: Alphabet, voice: CipherVoice, speaker: Speaker) -> None:
    audio = render(text, alphabet, voice, speaker)
    write_wav(dest, audio, comment=mark_of(voice, speaker.name).comment())
