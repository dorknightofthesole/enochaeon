"""Speak one Enochian word with espeak-ng."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from enochaeon.audio import normalize, resample, trim_silence
from enochaeon.errors import EnochaeonError

SPEED = 110
_CACHE: dict[tuple[str, int], np.ndarray] = {}


def espeak_binary() -> str:
    found = shutil.which("espeak-ng")
    if found:
        return found
    for candidate in ("/opt/homebrew/bin/espeak-ng", "/usr/local/bin/espeak-ng"):
        if Path(candidate).is_file():
            return candidate
    raise EnochaeonError("espeak-ng is required. Install it with: brew install espeak-ng")


def speak(phonemes: str, speed: int = SPEED) -> np.ndarray:
    """Return one espeak phoneme string as 16 kHz mono audio."""
    cached = _CACHE.get((phonemes, speed))
    if cached is not None:
        return cached
    binary = espeak_binary()
    fd, name = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    path = Path(name)
    try:
        completed = subprocess.run(
            [binary, "-v", "en", "-s", str(speed), "-w", str(path), f"[[{phonemes}]]"],
            check=False,
            capture_output=True,
            text=True,
        )
        stderr = (completed.stderr or "").strip()
        if completed.returncode != 0:
            raise EnochaeonError(stderr or f"espeak-ng failed on [[{phonemes}]]")
        if "unknown phoneme" in stderr.lower():
            raise EnochaeonError(stderr)
        audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    finally:
        path.unlink(missing_ok=True)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio[:, 0]
    audio = normalize(trim_silence(resample(audio, sample_rate)))
    if audio.size < 16_000 * 0.04:
        raise EnochaeonError(f"[[{phonemes}]] produced no speech")
    _CACHE[(phonemes, speed)] = audio
    return audio
