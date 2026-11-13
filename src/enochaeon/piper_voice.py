"""Speak a Call with Piper. The English cipher never comes here.

Piper reads IPA one character at a time.

When enochaeon.json names a lexicon field for the voice, each word is sent as
that field has it, and this code adds no sound of its own. The end of a word
is the mark the config gives.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from enochaeon.audio import SAMPLE_RATE, Gaps, resample, silence
from enochaeon.config import CallVoice
from enochaeon.enochian import audible
from enochaeon.errors import EnochaeonError


def render(text: str, voice: CallVoice, gaps: Gaps, readings: dict[str, str] | None = None) -> np.ndarray:
    """One Piper breath per Call word, with the gaps it is given."""
    model = Path(voice.piper_voice)
    if not voice.piper_voice or not model.is_file():
        raise EnochaeonError(
            "calls.piper.voice in enochaeon.json must be a Piper model file. "
            "Download it with: python3 -m piper.download_voices --download-dir scratch/piper-voices en_US-john-medium"
        )
    try:
        from piper import PiperVoice, SynthesisConfig
    except ImportError as exc:
        raise EnochaeonError(
            "Speaking with Piper needs piper-tts. It is installed with enochaeon."
        ) from exc
    speaker = PiperVoice.load(model)
    pieces: list[np.ndarray] = []
    segments, _dropped = audible(text, readings or {})
    for segment in segments:
        if isinstance(segment, str):
            pieces.append(silence(gaps.nl_ms if segment == "\n" else gaps.word_ms))
            continue
        pieces.append(
            _speak(speaker, SynthesisConfig, _word_ipa(segment, readings or {}, voice), voice.length_scale)
        )
    if not pieces:
        return silence(gaps.word_ms)
    return np.concatenate(pieces)


def _word_ipa(word: list, readings: dict[str, str], voice: CallVoice) -> str:
    """What Piper is given for one word.

    A reading from the voice's own lexicon field is sent as written. A reading
    from dee_ipa or golden_dawn_ipa is turned into Piper's letters.
    """
    from enochaeon.enochian import _listed
    from enochaeon.word_ipa import as_written, piper_phones

    reading = _listed(word, readings)
    spoken = as_written(reading) if voice.piper_ipa else piper_phones(reading)
    return spoken + voice.word_end


def _speak(speaker: object, config_type: type, ipa: str, length_scale: float) -> np.ndarray:
    chunks: list[np.ndarray] = []
    rate = SAMPLE_RATE
    for chunk in speaker.synthesize(f"[[{ipa}]]", syn_config=config_type(length_scale=length_scale)):
        chunks.append(np.asarray(chunk.audio_float_array, dtype=np.float32))
        rate = chunk.sample_rate
    if not chunks:
        raise EnochaeonError(f"Piper produced no audio for [[{ipa}]]")
    audio = np.concatenate(chunks)
    if rate != SAMPLE_RATE:
        audio = resample(audio, rate)
    return audio
