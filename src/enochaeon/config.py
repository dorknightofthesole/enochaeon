"""Settings a person can change. The cipher does not read this."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from enochaeon.errors import EnochaeonError

CONFIG_NAME = "enochaeon.json"
ENGINES = frozenset({"espeak", "piper"})
READINGS = frozenset({"dee_ipa", "golden_dawn_ipa"})


@dataclass(frozen=True)
class CallVoice:
    """How a Call is spoken. English text never uses this."""

    engine: str = "espeak"
    ipa: str = "dee_ipa"
    length_scale: float = 1.6
    piper_voice: str = ""
    word_ms: int | None = None
    # The lexicon field written for this Piper voice. Empty: Piper is given ipa, turned into its letters.
    piper_ipa: str = ""
    # What ends each word given to Piper. Empty: nothing.
    word_end: str = ""

    def chosen(self, engine: str | None) -> CallVoice:
        """The voice for one run. A command-line engine replaces the file."""
        if engine is None:
            return self
        if engine not in ENGINES:
            raise EnochaeonError(f"Call engine must be espeak or piper, not {engine!r}.")
        return replace(self, engine=engine)


def load_call_voice(path: Path | None = None) -> CallVoice:
    """The Calls section of enochaeon.json, or espeak when that file is absent."""
    source = Path.cwd() / CONFIG_NAME if path is None else path
    if not source.is_file():
        return CallVoice()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        calls = data.get("calls", {})
        piper = calls.get("piper", {})
        engine = calls.get("engine", "espeak")
        ipa = calls.get("ipa", "dee_ipa")
        scale = float(piper.get("length_scale", 1.6))
        voice = str(piper.get("voice", ""))
        word_ms = _word_ms(piper.get("word_ms"))
        piper_ipa = _text(piper.get("ipa"), "calls.piper.ipa")
        word_end = _text(piper.get("word_end"), "calls.piper.word_end")
    except (OSError, json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
        raise EnochaeonError(f"{source} is not a Calls config. {exc}") from exc
    if engine not in ENGINES:
        raise EnochaeonError(f"{source} engine must be espeak or piper, not {engine!r}.")
    if ipa not in READINGS:
        raise EnochaeonError(f"{source} ipa must be dee_ipa or golden_dawn_ipa, not {ipa!r}.")
    if scale <= 0:
        raise EnochaeonError(f"{source} calls.piper.length_scale must be positive, not {scale}.")
    if word_ms is not None and word_ms <= 0:
        raise EnochaeonError(f"{source} calls.piper.word_ms must be positive, not {word_ms}.")
    if piper_ipa in READINGS:
        raise EnochaeonError(f"{source} calls.piper.ipa names a field written for the voice, not {piper_ipa}.")
    return CallVoice(
        engine=engine,
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
