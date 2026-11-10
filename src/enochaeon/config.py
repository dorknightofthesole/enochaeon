"""Settings a person can change. The cipher does not read this."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from enochaeon.errors import EnochaeonError

CONFIG_NAME = "enochaeon.json"
ENGINES = frozenset({"espeak", "piper"})


@dataclass(frozen=True)
class CallVoice:
    """How a Call is spoken. English text never uses this."""

    engine: str = "espeak"
    length_scale: float = 1.6
    piper_voice: str = ""

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
        scale = float(piper.get("length_scale", 1.6))
        voice = str(piper.get("voice", ""))
    except (OSError, json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
        raise EnochaeonError(f"{source} is not a Calls config. {exc}") from exc
    if engine not in ENGINES:
        raise EnochaeonError(f"{source} engine must be espeak or piper, not {engine!r}.")
    if scale <= 0:
        raise EnochaeonError(f"{source} calls.piper.length_scale must be positive, not {scale}.")
    return CallVoice(engine=engine, length_scale=scale, piper_voice=voice)
