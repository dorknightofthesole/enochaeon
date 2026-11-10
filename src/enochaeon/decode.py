"""Read a Enochaeon WAV back to English."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from enochaeon.alphabet import CALIBRATION_PATH, Alphabet
from enochaeon.audio import SAMPLE_RATE, Gaps, parse_comment, read_comment, read_wav, resample, segment_words
from enochaeon.errors import EnochaeonError
from enochaeon.recognize import transcribe


def load_calibration(path: Path | None = None) -> dict[str, dict[str, str]]:
    source = path or CALIBRATION_PATH
    if not source.is_file():
        raise EnochaeonError("No calibration file. Run: enochaeon calibrate")
    raw = json.loads(source.read_text(encoding="utf-8"))
    if raw.get("version") != 3:
        raise EnochaeonError(f"{source} is an old calibration. Run: enochaeon calibrate")
    atoms = raw.get("atoms")
    if not isinstance(atoms, dict) or not atoms:
        raise EnochaeonError(f"{source} has no letter templates")
    labels: dict[str, dict[str, str]] = {}
    for key, forms in atoms.items():
        if not isinstance(forms, dict):
            raise EnochaeonError(f"{source} is an old calibration. Run: enochaeon calibrate")
        labels[str(key)] = {
            str(form): " ".join(str(phones).split())
            for form, phones in forms.items()
            if phones
        }
    return labels


def require_calibration(alphabet: Alphabet, path: Path | None = None) -> dict[str, dict[str, str]]:
    labels = load_calibration(path)
    missing: list[str] = []
    for atom_id, atom in alphabet.atoms.items():
        heard = labels.get(atom_id, {})
        for form in atom.forms():
            if not heard.get(form):
                missing.append(f"{atom_id}.{form}")
    if missing:
        joined = ", ".join(sorted(missing))
        raise EnochaeonError(f"Calibration is missing {joined}. Run: enochaeon calibrate")
    return labels


def decode_audio(
    audio: np.ndarray,
    sample_rate: int,
    alphabet: Alphabet,
    labels: dict[str, str],
    gaps: Gaps | None = None,
) -> tuple[str, bool]:
    if sample_rate != SAMPLE_RATE:
        audio = resample(audio, sample_rate)
        sample_rate = SAMPLE_RATE
    pieces: list[str] = []
    for item in segment_words(audio, sample_rate, gaps or Gaps()):
        if isinstance(item, str):
            pieces.append(item)
            continue
        pieces.append(transcribe(item, sample_rate))
    return alphabet.decode_spoken(pieces, labels)


def decode_file(path: Path, alphabet: Alphabet, labels: dict[str, str]) -> tuple[str, bool]:
    comment = read_comment(path)
    gaps = parse_comment(comment) or Gaps()
    if comment is None or parse_comment(comment) is None:
        import sys

        print(
            "This WAV has no Enochaeon mark. Decoding it anyway, with the default gaps.",
            file=sys.stderr,
        )
    audio, sample_rate = read_wav(path)
    return decode_audio(audio, sample_rate, alphabet, labels, gaps)
