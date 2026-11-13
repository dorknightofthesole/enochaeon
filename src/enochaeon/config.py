"""Settings a person can change. Calls and translate read the calls section. The cipher reads the cipher section."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from enochaeon.errors import EnochaeonError

CONFIG_NAME = "enochaeon.json"
READINGS = frozenset({"dee_ipa", "golden_dawn_ipa"})


@dataclass(frozen=True)
class CallVoice:
    """How Piper speaks a Call. English text never uses this."""

    ipa: str = "dee_ipa"
    length_scale: float = 1.6
    piper_voice: str = ""
    word_ms: int | None = None
    # The lexicon field written for this Piper voice. Empty: Piper is given ipa, turned into its letters.
    piper_ipa: str = ""
    # What ends each word given to Piper. Empty: nothing.
    word_end: str = ""


def load_call_voice(path: Path | None = None) -> CallVoice:
    """The Calls section of enochaeon.json. With no file, no Piper model is named and a Call cannot be spoken."""
    source = Path.cwd() / CONFIG_NAME if path is None else path
    if not source.is_file():
        return CallVoice()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        calls = data.get("calls", {})
        piper = calls.get("piper", {})
        ipa = calls.get("ipa", "dee_ipa")
        scale = float(piper.get("length_scale", 1.6))
        voice = str(piper.get("voice", ""))
        word_ms = _word_ms(piper.get("word_ms"))
        piper_ipa = _text(piper.get("ipa"), "calls.piper.ipa")
        word_end = _text(piper.get("word_end"), "calls.piper.word_end")
    except (OSError, json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
        raise EnochaeonError(f"{source} is not a Calls config. {exc}") from exc
    if ipa not in READINGS:
        raise EnochaeonError(f"{source} ipa must be dee_ipa or golden_dawn_ipa, not {ipa!r}.")
    if scale <= 0:
        raise EnochaeonError(f"{source} calls.piper.length_scale must be positive, not {scale}.")
    if word_ms is not None and word_ms <= 0:
        raise EnochaeonError(f"{source} calls.piper.word_ms must be positive, not {word_ms}.")
    if piper_ipa in READINGS:
        raise EnochaeonError(f"{source} calls.piper.ipa names a field written for the voice, not {piper_ipa}.")
    return CallVoice(
        ipa=ipa,
        length_scale=scale,
        piper_voice=voice,
        word_ms=word_ms,
        piper_ipa=piper_ipa,
        word_end=word_end,
    )


def _text(value: object, name: str) -> str:
    """A setting that is text, or empty when the config leaves it unset."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text, not {value!r}")
    return value.strip()


def _word_ms(value: object) -> int | None:
    """The Piper breath gap, or None when the config leaves it unset."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"word_ms must be a whole number of milliseconds, not {value!r}")
    return value


@dataclass(frozen=True)
class CipherVoice:
    """How the cipher is spoken and cut apart again. A Call never uses this."""

    # The Piper model file.
    model: str
    # The field of the key file that has what this voice is given for each letter sound.
    sounds: str
    length_scale: float
    noise_scale: float
    noise_w_scale: float
    # What ends each letter sound given to the voice.
    letter_end: str
    # The silence after a letter, between two words and between two lines.
    letter_ms: int
    word_ms: int
    line_ms: int
    # The quiet kept on each side of a spoken letter sound.
    edge_ms: int
    # A silence shorter than this is inside one letter.
    bridge_ms: int
    # The quiet on each side of a letter when it is given to the recognizer.
    hear_ms: int


def load_cipher_voice(path: Path | None = None) -> CipherVoice:
    """The cipher section of enochaeon.json. Every setting must be there: the code has none of its own."""
    source = Path.cwd() / CONFIG_NAME if path is None else path
    if not source.is_file():
        raise EnochaeonError(f"The cipher needs {source}, with a cipher section.")
    try:
        cipher = json.loads(source.read_text(encoding="utf-8"))["cipher"]
        voice = CipherVoice(
            model=_needed_text(cipher, "voice"),
            sounds=_needed_text(cipher, "sounds"),
            length_scale=_number(cipher, "length_scale"),
            noise_scale=_number(cipher, "noise_scale"),
            noise_w_scale=_number(cipher, "noise_w_scale"),
            letter_end=_text(cipher["letter_end"], "cipher.letter_end"),
            letter_ms=_ms(cipher, "letter_ms"),
            word_ms=_ms(cipher, "word_ms"),
            line_ms=_ms(cipher, "line_ms"),
            edge_ms=_ms(cipher, "edge_ms"),
            bridge_ms=_ms(cipher, "bridge_ms"),
            hear_ms=_ms(cipher, "hear_ms"),
        )
    except KeyError as exc:
        raise EnochaeonError(f"{source} has no cipher setting {exc.args[0]}.") from exc
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EnochaeonError(f"{source} is not a cipher config. {exc}") from exc
    if voice.length_scale <= 0:
        raise EnochaeonError(f"{source} cipher.length_scale must be positive, not {voice.length_scale}.")
    if voice.noise_scale < 0 or voice.noise_w_scale < 0:
        raise EnochaeonError(f"{source} cipher.noise_scale and cipher.noise_w_scale must not be below zero.")
    if not voice.letter_ms < voice.word_ms < voice.line_ms:
        raise EnochaeonError(
            f"{source} cipher.letter_ms, word_ms and line_ms must each be longer than the one before: "
            "the length of a silence is how a letter, a word and a line are told apart."
        )
    if voice.bridge_ms >= voice.letter_ms:
        raise EnochaeonError(
            f"{source} cipher.bridge_ms must be shorter than cipher.letter_ms, or two letters are taken for one."
        )
    return voice


def _needed_text(section: dict, name: str) -> str:
    """A setting that is text and is not empty."""
    value = _text(section[name], f"cipher.{name}")
    if not value:
        raise ValueError(f"cipher.{name} is empty")
    return value


def _number(section: dict, name: str) -> float:
    value = section[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"cipher.{name} must be a number, not {value!r}")
    return float(value)


def _ms(section: dict, name: str) -> int:
    """A length in milliseconds: a whole number above zero."""
    value = section[name]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"cipher.{name} must be a whole number of milliseconds above zero, not {value!r}")
    return value
