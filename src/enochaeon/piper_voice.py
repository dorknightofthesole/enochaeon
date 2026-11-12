"""Speak a Call with Piper. The English cipher never comes here.

Piper reads IPA one character at a time. espeak's own IPA dump is not used:
``[[Q]]`` comes out as ɣ, and Q is the vowel in "lot".

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

# Longest match first. kw and ks are two IPA letters and no space: a space
# inside [[ ]] is a Piper word break.
_IPA = {
    "oU": "oʊ",
    "eI": "eɪ",
    "kw": "kw",
    "ks": "ks",
    "Q:": "ɒː",
    "A:": "ɑː",
    "I:": "ɪː",
    "i:": "iː",
    "u:": "uː",
    "E:": "ɛː",
    "a:": "æː",
    "U:": "ʊː",
    "Q": "ɒ",
    "O": "ɔː",
    "A": "ɑ",
    "a": "æ",
    "E": "ɛ",
    "I": "ɪ",
    "U": "ʊ",
    "r": "ɹ",
    "j": "j",
    "b": "b",
    "d": "d",
    "f": "f",
    "g": "ɡ",
    "h": "h",
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "p": "p",
    "s": "s",
    "t": "t",
    "v": "v",
    "w": "w",
    "z": "z",
}
_ORDERED = sorted(_IPA, key=len, reverse=True)


def ipa_of(espeak: str) -> str:
    """The IPA Piper speaks for one espeak word."""
    return "".join(_map_token(token) for token in espeak.split())


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


def _map_token(token: str) -> str:
    """One espeak token. A stress mark lands on the phoneme that follows it."""
    pieces: list[str] = []
    index = 0
    stress = False
    while index < len(token):
        if token[index] == "'":
            stress = True
            index += 1
            continue
        symbol = next((name for name in _ORDERED if token.startswith(name, index)), None)
        if symbol is None:
            raise EnochaeonError(f"No Piper IPA for {token[index:]!r} in {token!r}")
        spoken = _IPA[symbol]
        if stress:
            spoken = "ˈ" + spoken
            stress = False
        pieces.append(spoken)
        index += len(symbol)
    if stress:
        raise EnochaeonError(f"Stress with no phoneme in {token!r}")
    return "".join(pieces)
