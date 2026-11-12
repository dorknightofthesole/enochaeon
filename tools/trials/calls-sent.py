"""Write down what Calls and translate give the voice, with no sound made and no file of theirs written.

  PYTHONPATH=src python3 tools/trials/calls-sent.py NAME

Writes scratch/calls-sent/NAME.txt. Run it before a change and after it under
two names, and compare the two files. They must be the same when the change
was not meant to touch Calls or translate.

For every call file in calls/ and for each text in calls-sent.json, the file
lists what enochaeon.json gives for the Call voice, the silences written into
the wav, and then in order each string the voice is given with its speed, and
each silence put between them.

Nothing is spoken. The function that hands a string to Piper is replaced, in
this process only, by one that writes the string down. The audio itself could
not be compared in any case: John's noise makes every take differ.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import piper

from enochaeon import piper_voice
from enochaeon.audio import silence
from enochaeon.config import load_call_voice
from enochaeon.enochian import _readings, audible, call_files, call_gaps, render
from enochaeon.roots import load_roots
from enochaeon.translate import MiniLM, _spoken, match_phrase, part_tags

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SETTINGS = json.loads((HERE / "calls-sent.json").read_text(encoding="utf-8"))
OUT = ROOT / "scratch" / "calls-sent"

SENT: list[str] = []


def _speak(speaker: object, config_type: type, ipa: str, length_scale: float):
    SENT.append(f"  [[{ipa}]] length_scale {length_scale}")
    return silence(1)


def _silence(ms: int, *rest):
    SENT.append(f"  silence {ms}")
    return silence(ms, *rest)


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print(__doc__)
        return 2
    os.chdir(ROOT)
    piper_voice._speak = _speak
    piper_voice.silence = _silence
    # The model is not needed when nothing is spoken.
    piper.PiperVoice.load = staticmethod(lambda model: None)
    voice = load_call_voice()
    report = [f"voice {voice}", ""]
    for path in call_files(ROOT / "calls"):
        gaps = call_gaps(voice)
        text = path.read_text(encoding="utf-8")
        _, dropped = audible(text, _readings(voice))
        del SENT[:]
        render(text, gaps=gaps, voice=voice)
        report += [f"== calls/{path.name}", f"  wav comment {gaps.comment()}", f"  left out {' '.join(dropped) or '-'}", *SENT, ""]
    roots = load_roots()
    scorer = MiniLM()
    for name in SETTINGS["translate"]:
        source = ROOT / name
        result = match_phrase(source.read_text(encoding="utf-8"), roots, scorer, part_tags)
        text = _spoken(result.call_text, voice, source.name)
        del SENT[:]
        render(text, voice=voice)
        report += [f"== translate {name}", f"  left out {' '.join(result.left_out) or '-'}", f"  trace {result.trace!r}", *SENT, ""]
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{arguments[0]}.txt"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {sum(1 for line in report if line.startswith('  [['))} strings, "
          f"{sum(1 for line in report if line.startswith('== '))} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
