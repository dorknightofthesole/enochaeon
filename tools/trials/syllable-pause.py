"""Speak each syllable alone with a short gap. Compare to one breath.

This trial was run against the cipher as espeak spoke it, one breath for each word. The cipher is now
spoken by John one letter at a time, and this script does not run against it.
The espeak voice it compares against has been taken out of the project.
"""

from __future__ import annotations

import numpy as np

from enochaeon.alphabet import syllable_forms, Alphabet
from enochaeon.audio import Gaps, SAMPLE_RATE, segment_words, silence, voiced_regions
from enochaeon.decode import require_calibration
from enochaeon.encode import render
from enochaeon.lexicon import word_phones
from enochaeon.match import phone_distance
from enochaeon.recognize import transcribe
from enochaeon.synthesize import speak

PAUSE_MS = 60
LINES = (
    "The quick brown fox jumps over the lazy dog",
    "Hello world",
    "The black cat kept the key",
    "She sells fish and chips",
)
ALONE = ("have", "give", "over")
DISTANCE = {
    (0, 0): 1, (0, 1): 4, (0, 2): 6, (0, 3): 0, (0, 4): 0,
    (0, 5): 6, (0, 6): 1, (0, 7): 7, (0, 8): 2,
    (1, 0): 4, (1, 1): 1,
    (2, 0): 1, (2, 1): 3, (2, 2): 6, (2, 3): 3, (2, 4): 0, (2, 5): 7,
    (3, 0): 1, (3, 1): 0, (3, 2): 4, (3, 3): 1, (3, 4): 3,
}


def speak_paused(alphabet: Alphabet, atom_ids: tuple[str, ...]) -> np.ndarray:
    atoms = tuple(alphabet.atoms[atom_id] for atom_id in atom_ids)
    pieces: list[np.ndarray] = []
    forms = syllable_forms(atoms)
    for index, (atom, form) in enumerate(forms):
        pieces.append(speak(atom.phone if form == "phone" else atom.long))
        if index + 1 < len(forms):
            pieces.append(silence(PAUSE_MS))
    if not pieces:
        return silence(PAUSE_MS)
    return np.concatenate(pieces)


def render_paused(alphabet: Alphabet, text: str, gaps: Gaps) -> np.ndarray:
    pieces: list[np.ndarray] = []
    for item in alphabet.atom_ids(text):
        if isinstance(item, str):
            pieces.append(silence(gaps.nl_ms if item == "\n" else gaps.word_ms))
            continue
        pieces.append(speak_paused(alphabet, item))
    return np.concatenate(pieces)


def internal_gaps(audio: np.ndarray) -> list[float]:
    regions = voiced_regions(audio, SAMPLE_RATE)
    gaps: list[float] = []
    for index in range(len(regions) - 1):
        gap_ms = (regions[index + 1][0] - regions[index][1]) * 1000 / SAMPLE_RATE
        gaps.append(gap_ms)
    return gaps


def evaluate(alphabet: Alphabet, labels: dict, audio: np.ndarray, text: str) -> list[tuple[str, str, int]]:
    gaps = Gaps()
    heard: list[str] = []
    for piece in segment_words(audio, SAMPLE_RATE, gaps):
        if isinstance(piece, str):
            heard.append(piece)
        else:
            heard.append(transcribe(piece))
    decoded, _unknown = alphabet.decode_spoken(heard, labels)
    got = decoded.lower().split()
    rows: list[tuple[str, str, int]] = []
    word_index = 0
    for item in heard:
        if item in (" ", "\n"):
            continue
        word = text.lower().split()[word_index]
        phones = word_phones(alphabet, labels, word)
        distance = phone_distance(tuple(item.split()), phones) if phones else -1
        printed = got[word_index] if word_index < len(got) else ""
        rows.append((word, printed, distance))
        word_index += 1
    return rows


def main() -> None:
    alphabet = Alphabet.load()
    labels = require_calibration(alphabet)
    gaps = Gaps()
    print(f"pause={PAUSE_MS}ms word_limit={(gaps.syllable_ms + gaps.word_ms) / 2:.0f}ms", flush=True)
    base_rows: list[tuple[str, str, int]] = []
    paused_rows: list[tuple[str, str, int]] = []
    for line in LINES:
        plain = render(line, alphabet, gaps)
        paused = render_paused(alphabet, line, gaps)
        inside = [gap for gap in internal_gaps(paused) if gap < 400]
        widest = max(inside) if inside else 0
        base = evaluate(alphabet, labels, plain, line)
        trial = evaluate(alphabet, labels, paused, line)
        base_rows.extend(base)
        paused_rows.extend(trial)
        print(
            f"SENT plain  {' '.join(item[1] for item in base)}",
            flush=True,
        )
        print(
            f"SENT paused {' '.join(item[1] for item in trial)}  widest_internal={widest:.0f}ms",
            flush=True,
        )
    print("== MOVES", flush=True)
    worse = []
    for index, (word, printed, distance) in enumerate(paused_rows):
        before = base_rows[index]
        ceiling = list(DISTANCE.values())[index]
        if distance > ceiling or distance > before[2]:
            worse.append(f"{word} {before[2]}->{distance} ceiling {ceiling}")
        if (printed, distance) == (before[1], before[2]):
            continue
        print(
            f"  {word:8} plain {before[1]}/{before[2]}  paused {printed}/{distance}",
            flush=True,
        )
    print("== ALONE", flush=True)
    for word in ALONE:
        plain = evaluate(alphabet, labels, render(word, alphabet, gaps), word)[0]
        paused = evaluate(alphabet, labels, render_paused(alphabet, word, gaps), word)[0]
        print(
            f"  {word:8} plain {plain[1]}/{plain[2]}  paused {paused[1]}/{paused[2]}",
            flush=True,
        )
        if paused[2] > plain[2]:
            worse.append(f"{word} alone {plain[2]}->{paused[2]}")
    print("WORSE", worse or "none", flush=True)


if __name__ == "__main__":
    main()
