"""The cipher's voice: one letter sound at a time, spoken by Piper. A Call never comes here.

A letter sound is given to the voice as the key file has it for that voice,
with the ending enochaeon.json gives. Nothing is worked out here.

A recording carries a mark with the silences it was made with and a short
name for its voice. The name is made from everything that shapes a letter
sound, so a recording and a calibration with the same name were spoken the
same way. The mark has no plaintext in it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet, Atom
from enochaeon.audio import normalize, resample, trim_silence
from enochaeon.config import CipherVoice
from enochaeon.errors import EnochaeonError

MARK_PREFIX = "enochaeon;v=2"
_NAME_LENGTH = 12


@dataclass(frozen=True)
class Mark:
    """What a cipher recording says about itself."""

    letter_ms: int
    word_ms: int
    line_ms: int
    edge_ms: int
    voice: str

    def comment(self) -> str:
        return (
            f"{MARK_PREFIX};letter_ms={self.letter_ms};word_ms={self.word_ms};"
            f"line_ms={self.line_ms};edge_ms={self.edge_ms};voice={self.voice}"
        )


def read_mark(comment: str | None) -> Mark | None:
    """The mark in a wav comment, or None when the comment is not a cipher mark."""
    if not comment or not comment.startswith(MARK_PREFIX):
        return None
    fields = dict(piece.split("=", 1) for piece in comment.split(";") if "=" in piece)
    try:
        return Mark(
            letter_ms=int(fields["letter_ms"]),
            word_ms=int(fields["word_ms"]),
            line_ms=int(fields["line_ms"]),
            edge_ms=int(fields["edge_ms"]),
            voice=fields["voice"],
        )
    except (KeyError, ValueError):
        return None


def mark_of(voice: CipherVoice, name: str) -> Mark:
    """The mark for a recording made with these settings by the voice of that name."""
    return Mark(voice.letter_ms, voice.word_ms, voice.line_ms, voice.edge_ms, name)


def voice_name(voice: CipherVoice, alphabet: Alphabet) -> str:
    """A short name for everything that shapes a letter sound: the model, how it is run, and each string it is given."""
    model = Path(voice.model)
    if not voice.model or not model.is_file():
        raise EnochaeonError(
            "cipher.voice in enochaeon.json must be a Piper model file. The README says how to download one."
        )
    shaped = {
        "model": hashlib.sha256(model.read_bytes()).hexdigest(),
        "length_scale": voice.length_scale,
        "noise_scale": voice.noise_scale,
        "noise_w_scale": voice.noise_w_scale,
        "letter_end": voice.letter_end,
        "edge_ms": voice.edge_ms,
        "sounds": {
            f"{atom.id}.{form}": alphabet.voice_sound(voice.sounds, atom.id, form)
            for atom in alphabet.atoms.values()
            for form in atom.forms()
        },
    }
    written = json.dumps(shaped, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(written).hexdigest()[:_NAME_LENGTH]


class Speaker:
    """The Piper voice, run as the cipher section of enochaeon.json says."""

    def __init__(self, voice: CipherVoice, alphabet: Alphabet) -> None:
        self.name = voice_name(voice, alphabet)
        try:
            from piper import PiperVoice, SynthesisConfig
        except ImportError as exc:
            raise EnochaeonError("Speaking with Piper needs piper-tts. It is installed with enochaeon.") from exc
        self._voice = voice
        self._alphabet = alphabet
        self._piper = PiperVoice.load(Path(voice.model))
        self._config = SynthesisConfig(
            length_scale=voice.length_scale,
            noise_scale=voice.noise_scale,
            noise_w_scale=voice.noise_w_scale,
        )
        # With no noise a string is the same sound every time, so it is made once.
        self._steady = not voice.noise_scale and not voice.noise_w_scale
        self._kept: dict[str, np.ndarray] = {}

    def sound(self, atom: Atom, form: str) -> np.ndarray:
        """One letter sound as 16 kHz audio, with edge_ms of quiet kept on each side."""
        spoken = self._alphabet.voice_sound(self._voice.sounds, atom.id, form) + self._voice.letter_end
        if self._steady and spoken in self._kept:
            return self._kept[spoken]
        chunks = list(self._piper.synthesize(f"[[{spoken}]]", syn_config=self._config))
        if not chunks:
            raise EnochaeonError(f"Piper produced no audio for [[{spoken}]]")
        audio = np.concatenate([np.asarray(chunk.audio_float_array, dtype=np.float32) for chunk in chunks])
        audio = trim_silence(resample(audio, chunks[0].sample_rate), pad_ms=self._voice.edge_ms)
        if audio.size <= 1:
            raise EnochaeonError(f"[[{spoken}]] produced no speech")
        audio = normalize(audio)
        if self._steady:
            self._kept[spoken] = audio
        return audio
