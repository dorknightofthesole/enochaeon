"""Speak every letter sound alone with the cipher's voice and store what the recognizer gives for it.

The calibration is two files: a list of the letter sounds with the name of
the voice that spoke them, and the frames of every sound. They are made the
way a recording is read: each sound is cut out with the cutter the decoder
uses, and heard alone.

Before anything is written, every letter sound is spoken in one row with the
letter silence between them, and that row is read back. A letter that comes
back as another letter is named, and nothing is written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from enochaeon.alphabet import CALIBRATION_PATH, Alphabet
from enochaeon.audio import silence
from enochaeon.cipher_voice import Speaker
from enochaeon.config import CipherVoice, load_cipher_voice
from enochaeon.decode import CALIBRATION_VERSION, Calibration, frames_path, letters, tell
from enochaeon.recognize import frames


def calibrate(alphabet: Alphabet | None = None, voice: CipherVoice | None = None, path: Path | None = None) -> int:
    alphabet = alphabet or Alphabet.load()
    voice = voice or load_cipher_voice()
    dest = path or CALIBRATION_PATH
    speaker = Speaker(voice, alphabet)
    jobs = [(atom, form) for atom in alphabet.atoms.values() for form in atom.forms()]
    total = len(jobs)
    heard: list[tuple[str, str, np.ndarray]] = []
    faults: list[str] = []
    for number, (atom, form) in enumerate(jobs, start=1):
        label = f"{atom.id}.{form}"
        print(f"[{number}/{total}] {label}", file=sys.stderr)
        found = letters(speaker.sound(atom, form), voice.bridge_ms, voice.hear_ms)
        if len(found) != 1:
            faults.append(f"{label} came out in {len(found)} pieces, and a letter must be one")
            continue
        given = frames(found[0][1])
        if not given.shape[0]:
            faults.append(f"{label} was too short to be heard")
            continue
        heard.append((atom.id, form, given))
    if not faults:
        calibration = Calibration(speaker.name, voice.bridge_ms, voice.hear_ms, tuple(heard))
        faults = _mistaken(jobs, speaker, voice, calibration)
    if faults:
        for fault in faults:
            print(fault, file=sys.stderr)
        return 1
    index: dict[str, dict[str, list[int]]] = {}
    start = 0
    for atom_id, form, given in heard:
        index.setdefault(atom_id, {})[form] = [start, start + given.shape[0]]
        start += given.shape[0]
    np.save(frames_path(dest), np.concatenate([given for _, _, given in heard]))
    written = {
        "version": CALIBRATION_VERSION,
        "voice": speaker.name,
        "spoken_with": {
            "voice": voice.model,
            "sounds": voice.sounds,
            "length_scale": voice.length_scale,
            "noise_scale": voice.noise_scale,
            "noise_w_scale": voice.noise_w_scale,
            "letter_end": voice.letter_end,
            "edge_ms": voice.edge_ms,
        },
        "bridge_ms": voice.bridge_ms,
        "hear_ms": voice.hear_ms,
        "sounds": index,
    }
    dest.write_text(_laid_out(written), encoding="utf-8")
    print(f"Calibrated {total} letter sounds into {dest} and {frames_path(dest).name}", file=sys.stderr)
    return 0


def _laid_out(written: dict) -> str:
    """The calibration file, with one letter to a line where the sounds are listed."""
    sounds = written["sounds"]
    rows = ",\n".join(f"    {json.dumps(atom_id)}: {json.dumps(forms)}" for atom_id, forms in sounds.items())
    head = json.dumps({key: value for key, value in written.items() if key != "sounds"}, indent=2, ensure_ascii=False)
    return head[: head.rindex("}")].rstrip() + ',\n  "sounds": {\n' + rows + "\n  }\n}\n"


def _mistaken(jobs: list, speaker: Speaker, voice: CipherVoice, calibration: Calibration) -> list[str]:
    """Every letter sound in one row, read back. Names each one that comes back as another letter."""
    row: list[np.ndarray] = []
    for atom, form in jobs:
        if row:
            row.append(silence(voice.letter_ms))
        row.append(speaker.sound(atom, form))
    found = letters(np.concatenate(row), voice.bridge_ms, voice.hear_ms)
    if len(found) != len(jobs):
        return [f"{len(jobs)} letter sounds spoken in a row were cut into {len(found)}"]
    faults: list[str] = []
    for (atom, form), (_, letter) in zip(jobs, found):
        told = tell(frames(letter), calibration)
        if told != atom.id:
            faults.append(f"{atom.id}.{form} spoken in a row was taken for {told}")
    return faults
