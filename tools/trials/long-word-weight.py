"""Say the longer words of a call three ways, to choose how they are sent to Piper.

    PYTHONPATH=src python3 tools/trials/long-word-weight.py calls/01.txt [COUNT]

A longer word is one whose string for the voice, in the lexicon field that
enochaeon.json names, has more than one vowel and no stress mark. Where its
stress falls is not known, so no form here picks a syllable.

plain       as the lexicon has it now: no stress mark
even        a stress mark on every vowel, so each syllable has full weight
even-held   the same, and every short vowel is also held

The first COUNT longer words of the call (12 when not given) are said in each
form, with half a second between words. One recording per form is written to
scratch/long-word-weight/, with a list of what was sent and how far each
word's vowels opened.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from enochaeon.audio import SAMPLE_RATE, silence, write_wav
from enochaeon.config import load_call_voice
from enochaeon.enochian import _listed, _readings, _spelling, audible
from enochaeon.word_ipa import as_written

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scratch" / "long-word-weight"
GAP_MS = 500
FRAME_MS = 30
STEP_MS = 10
STRESS = "ˈ"
HOLD = "ː"
# The vowel letters of the strings Piper is given, and the glides written with two of them.
VOWELS = set("ɑæɒɔəɛɜɪʊʌaeiou")
GLIDES = ("oʊ", "eɪ", "aɪ")


def vowels(sent: str) -> list[tuple[int, int]]:
    """(start, end) of each vowel: one vowel letter or one glide, with its length mark."""
    found: list[tuple[int, int]] = []
    index = 0
    while index < len(sent):
        if sent[index] not in VOWELS:
            index += 1
            continue
        end = index + (2 if sent.startswith(GLIDES, index) else 1)
        if end < len(sent) and sent[end] == HOLD:
            end += 1
        found.append((index, end))
        index = end
    return found


def plain(sent: str) -> str:
    return sent


def even(sent: str, hold: bool = False) -> str:
    pieces: list[str] = []
    last = 0
    for start, end in vowels(sent):
        vowel = sent[start:end]
        if hold and len(vowel) == 1:
            vowel += HOLD
        pieces += [sent[last:start], STRESS, vowel]
        last = end
    return "".join(pieces) + sent[last:]


def even_held(sent: str) -> str:
    return even(sent, hold=True)


FORMS = {"plain": plain, "even": even, "even-held": even_held}


def longer_words(call: Path, count: int) -> list[tuple[str, str]]:
    """(spelling, what the lexicon has for the voice) of the first `count` different longer words."""
    readings = _readings(load_call_voice(ROOT / "enochaeon.json"))
    segments, _dropped = audible(call.read_text(encoding="utf-8"), readings)
    found: dict[str, str] = {}
    for segment in segments:
        if isinstance(segment, str):
            continue
        sent = as_written(_listed(segment, readings))
        if STRESS not in sent and len(vowels(sent)) > 1:
            found.setdefault(_spelling(segment), sent)
        if len(found) == count:
            break
    return list(found.items())


def open_ms(audio: np.ndarray) -> int:
    """How long the strongest frequency between 150 and 1200 Hz is above 550 Hz."""
    frame = int(SAMPLE_RATE * FRAME_MS / 1000)
    step = int(SAMPLE_RATE * STEP_MS / 1000)
    freqs = np.fft.rfftfreq(4096, 1 / SAMPLE_RATE)
    band = (freqs >= 150) & (freqs <= 1200)
    window = np.hanning(frame)
    frames = [audio[start : start + frame] for start in range(0, len(audio) - frame, step)]
    loudest = max(float(np.sqrt(np.mean(piece**2))) for piece in frames)
    opened = 0
    for piece in frames:
        if float(np.sqrt(np.mean(piece**2))) < 0.05 * loudest:
            continue
        spectrum = np.abs(np.fft.rfft(piece * window, 4096))
        if freqs[band][np.argmax(spectrum[band])] > 550:
            opened += STEP_MS
    return opened


def main(arguments: list[str]) -> None:
    if not arguments or len(arguments) > 2:
        raise SystemExit(__doc__)
    from piper import PiperVoice, SynthesisConfig

    from enochaeon.piper_voice import _speak

    call = ROOT / arguments[0]
    count = int(arguments[1]) if len(arguments) == 2 else 12
    voice = load_call_voice(ROOT / "enochaeon.json")
    speaker = PiperVoice.load(ROOT / voice.piper_voice)
    words = longer_words(call, count)
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"{call.name}: the first {len(words)} longer words, speed {voice.length_scale}", ""]
    lines.append(f"{'word':<12}" + "".join(f"{name + ' (open ms)':<34}" for name in FORMS))
    rows = {spelling: [] for spelling, _reading in words}
    for name, form in FORMS.items():
        pieces: list[np.ndarray] = []
        for spelling, written in words:
            sent = form(written) + voice.word_end
            audio = _speak(speaker, SynthesisConfig, sent, voice.length_scale)
            rows[spelling].append(f"{sent} ({open_ms(audio)})")
            pieces += [audio, silence(GAP_MS)]
        write_wav(OUT / f"{call.stem}-{name}.wav", np.concatenate(pieces))
    for spelling, cells in rows.items():
        lines.append(f"{spelling:<12}" + "".join(f"{cell:<34}" for cell in cells))
    report = OUT / f"{call.stem}.txt"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {report.relative_to(ROOT)} and {len(FORMS)} recordings beside it")


if __name__ == "__main__":
    main(sys.argv[1:])
