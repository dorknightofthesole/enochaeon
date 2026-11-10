"""Speak every letter form in a short carrier and store what the model hears."""

from __future__ import annotations

import json
import sys

from enochaeon.alphabet import CALIBRATION_PATH, Alphabet
from enochaeon.match import fold_phones, phone_distance
from enochaeon.recognize import transcribe
from enochaeon.synthesize import speak

# A syllable that is not one of the letters. It trails each form so the letter
# is heard the way it is heard at the start of a word, and then it is cut off.
# kwah keeps its w in front of f, and loses it in front of k.
TRAILER = "k'A:m"
KWAH_TRAILER = "f'A:m"


def calibrate(alphabet: Alphabet | None = None) -> int:
    alphabet = alphabet or Alphabet.load()
    trailers = {
        TRAILER: _tokens(transcribe(speak(TRAILER))),
        KWAH_TRAILER: _tokens(transcribe(speak(KWAH_TRAILER))),
    }
    if not all(trailers.values()):
        print("A calibration trailer produced no phones", file=sys.stderr)
        return 1
    heard: dict[str, dict[str, str]] = {}
    owners: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []
    silent: list[str] = []
    jobs = [
        (atom.id, form, phonemes)
        for atom in alphabet.atoms.values()
        for form, phonemes in atom.forms().items()
    ]
    total = len(jobs)
    for number, (atom_id, form, phonemes) in enumerate(jobs, start=1):
        print(f"[{number}/{total}] {atom_id}.{form}", file=sys.stderr)
        trailer_name = KWAH_TRAILER if phonemes.replace(" ", "").startswith("kw") else TRAILER
        framed = _tokens(transcribe(speak(f"{phonemes} {trailer_name}")))
        phones = " ".join(_strip_trailer(framed, trailers[trailer_name]))
        label = f"{atom_id}.{form}"
        if not phones:
            silent.append(label)
            continue
        # The matcher treats aː and ɑ as a, so two hearings that differ only
        # there are the same syllable.
        identity = " ".join(fold_phones(phones))
        previous = owners.get(identity)
        if previous is not None:
            collisions.append((previous, label, identity))
        else:
            owners[identity] = label
        heard.setdefault(atom_id, {})[form] = phones
    if silent or collisions:
        for label in silent:
            print(f"{label} produced no phones", file=sys.stderr)
        for first, second, phones in collisions:
            print(f"{first} and {second} were both heard as {phones!r}", file=sys.stderr)
        return 1
    CALIBRATION_PATH.write_text(
        json.dumps({"version": 3, "atoms": heard}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Calibrated {total} letter sounds into {CALIBRATION_PATH}", file=sys.stderr)
    return 0


def _tokens(phones: str) -> tuple[str, ...]:
    return tuple(phones.split())


def _strip_trailer(framed: tuple[str, ...], trailer: tuple[str, ...]) -> tuple[str, ...]:
    """Drop the trailing carrier when it still sounds like the trailer."""
    if not framed or not trailer:
        return framed
    target = max(0, len(framed) - len(trailer))
    best_cut: int | None = None
    best_key: tuple[int, int] | None = None
    latest = max(0, len(framed) - len(trailer) - 2)
    limit = max(3, len(trailer) // 2)
    for cut in range(latest, len(framed)):
        distance = phone_distance(framed[cut:], trailer)
        if distance > limit:
            continue
        key = (distance, abs(cut - target))
        if best_key is None or key < best_key:
            best_key = key
            best_cut = cut
    if best_cut is None or best_cut == 0:
        return framed
    return framed[:best_cut]
