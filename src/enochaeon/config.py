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
    return CallVoice(engine=engine, ipa=ipa, length_scale=scale, piper_voice=voice, word_ms=word_ms)


def _word_ms(value: object) -> int | None:
    """The Piper breath gap, or None when the config leaves it unset."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"word_ms must be a whole number of milliseconds, not {value!r}")
    return value
