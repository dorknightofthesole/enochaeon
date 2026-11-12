"""How long the first sound of a word lasts before its vowel opens.

A y-glide is the mouth shape of "ee" held for a moment. Held long enough it
is heard as a syllable of its own. This trial measures that hold.

    PYTHONPATH=src python3 tools/trials/word-onset.py speak IPA [IPA ...]
    PYTHONPATH=src python3 tools/trials/word-onset.py takes IPA [IPA ...]
    PYTHONPATH=src python3 tools/trials/word-onset.py call calls/01.txt WORD

speak   Piper says each IPA string alone at speed 1.0 and at the speed in
        enochaeon.json. Each take is written to scratch/word-onset/.
takes   Piper says each IPA string five times at the speed in
        enochaeon.json, because no two takes are the same. The takes are
        written to scratch/word-onset/takes/.
call    The takes of WORD are cut out of the recording beside the call file
        and measured. The recording is not made again.

The measure is the strongest frequency between 150 and 1200 Hz, taken every
10 ms. It sits low (near 300 Hz) while the mouth is closed for "ee" or "y"
and rises (above 500 Hz) when the mouth opens for a vowel like the a in
"bad". "closed" is the time before it first stays above 500 Hz.

It is a measure of the sound. It is not a judgement of what a listener hears.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from enochaeon.audio import SAMPLE_RATE, read_wav, write_wav
from enochaeon.config import load_call_voice
from enochaeon.enochian import _readings, _spelling, audible, call_gaps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scratch" / "word-onset"
FRAME_MS = 30
STEP_MS = 10
OPEN_HZ = 500
QUIET = 0.05
TAKES = 5


def track(audio: np.ndarray, rate: int) -> list[tuple[int, int]]:
    """(time in ms, strongest frequency 150-1200 Hz) for each loud frame."""
    frame = int(rate * FRAME_MS / 1000)
    step = int(rate * STEP_MS / 1000)
    size = 4096
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs >= 150) & (freqs <= 1200)
    window = np.hanning(frame)
    loudest = max(float(np.sqrt(np.mean(audio[i : i + frame] ** 2))) for i in range(0, len(audio) - frame, step))
    points: list[tuple[int, int]] = []
    for start in range(0, len(audio) - frame, step):
        piece = audio[start : start + frame]
        if float(np.sqrt(np.mean(piece**2))) < QUIET * loudest:
            continue
        spectrum = np.abs(np.fft.rfft(piece * window, size))
        points.append((int(start * 1000 / rate), int(freqs[band][np.argmax(spectrum[band])])))
    return points


def closed_ms(points: list[tuple[int, int]]) -> int:
    """Time from the first loud frame until the frequency stays above OPEN_HZ for 30 ms."""
    for index in range(len(points) - 2):
        if all(hz > OPEN_HZ for _ms, hz in points[index : index + 3]):
            return points[index][0] - points[0][0]
    return points[-1][0] - points[0][0]


def describe(name: str, audio: np.ndarray, rate: int) -> str:
    points = track(audio, rate)
    length = points[-1][0] - points[0][0] + FRAME_MS
    line = f"{name:<28} length {length:>4} ms   closed {closed_ms(points):>4} ms"
    trail = " ".join(str(hz) for _ms, hz in points)
    return f"{line}\n    Hz every {STEP_MS} ms: {trail}"


def speak(strings: list[str]) -> list[str]:
    from piper import PiperVoice, SynthesisConfig

    from enochaeon.piper_voice import _speak

    voice = load_call_voice(ROOT / "enochaeon.json")
    speaker = PiperVoice.load(ROOT / voice.piper_voice)
    lines = [f"voice {Path(voice.piper_voice).name}"]
    for ipa in strings:
        for scale in (1.0, voice.length_scale):
            audio = _speak(speaker, SynthesisConfig, ipa, scale)
            name = f"{ipa}-{scale}"
            write_wav(OUT / f"{name}.wav", audio)
            lines.append(describe(f"[[{ipa}]] speed {scale}", audio, SAMPLE_RATE))
    return lines


def takes(strings: list[str]) -> list[str]:
    """Several takes of each string at the speed in enochaeon.json. Piper differs from take to take."""
    from piper import PiperVoice, SynthesisConfig

    from enochaeon.piper_voice import _speak

    voice = load_call_voice(ROOT / "enochaeon.json")
    speaker = PiperVoice.load(ROOT / voice.piper_voice)
    lines = [
        f"voice {Path(voice.piper_voice).name}, speed {voice.length_scale}, {TAKES} takes each",
        "top: the frequency the vowel reaches. open: how long it stays above 550 Hz.",
        "hum: how long the voice hums low (under 300 Hz) after the vowel, before the last sound is let go.",
        "",
        f"{'string':<14}{'length':>8}{'top':>8}{'open':>8}{'hum':>8}",
    ]
    for ipa in strings:
        rows = []
        for take in range(1, TAKES + 1):
            audio = _speak(speaker, SynthesisConfig, ipa, voice.length_scale)
            write_wav(OUT / "takes" / f"{ipa}-{take}.wav", audio)
            rows.append(vowel_and_hum(track(audio, SAMPLE_RATE)))
            lines.append(f"{'[[' + ipa + ']]':<14}" + "".join(f"{value:>8}" for value in rows[-1]))
        middle = [int(np.median([row[column] for row in rows])) for column in range(4)]
        lines.append(f"{'  middle take':<14}" + "".join(f"{value:>8}" for value in middle))
        lines.append("")
    return lines


def vowel_and_hum(points: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    """(length, top Hz, ms above 550 Hz, ms of low hum after the last frame above 550 Hz)."""
    length = points[-1][0] - points[0][0] + FRAME_MS
    opened = [index for index, (_ms, hz) in enumerate(points) if hz > 550]
    top = int(np.percentile([hz for _ms, hz in points], 90))
    if not opened:
        return length, top, 0, 0
    hum = 0
    for _ms, hz in points[opened[-1] + 1 :]:
        if hz >= 300:
            break
        hum += STEP_MS
    return length, top, len(opened) * STEP_MS, hum


def word_takes(call: Path, word: str) -> list[str]:
    voice = load_call_voice(ROOT / "enochaeon.json")
    gaps = call_gaps(voice)
    segments, _dropped = audible(call.read_text(encoding="utf-8"), _readings(voice))
    spoken = [_spelling(segment) for segment in segments if not isinstance(segment, str)]
    audio, rate = read_wav(call.with_suffix(".wav"))
    takes = silent_cuts(audio, int(rate * gaps.word_ms / 1000 * 0.9))
    if len(takes) != len(spoken):
        raise SystemExit(f"{call.name} has {len(spoken)} spoken words and the recording has {len(takes)} takes.")
    lines = [f"{call.with_suffix('.wav').name}: {len(takes)} takes"]
    for number, (name, (start, end)) in enumerate(zip(spoken, takes), start=1):
        if name != word.lower():
            continue
        write_wav(OUT / f"{call.stem}-word{number}-{name}.wav", audio[start:end], rate)
        lines.append(describe(f"{call.stem} word {number} {name}", audio[start:end], rate))
    return lines


def silent_cuts(audio: np.ndarray, least: int) -> list[tuple[int, int]]:
    """The stretches of sound between runs of at least `least` zero samples."""
    sounding = np.flatnonzero(audio != 0)
    if not len(sounding):
        return []
    breaks = np.flatnonzero(np.diff(sounding) > least)
    starts = [sounding[0], *(sounding[index + 1] for index in breaks)]
    ends = [*(sounding[index] + 1 for index in breaks), sounding[-1] + 1]
    return [(int(start), int(end)) for start, end in zip(starts, ends)]


def main(arguments: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if len(arguments) >= 2 and arguments[0] == "speak":
        lines, report = speak(arguments[1:]), "speak.txt"
    elif len(arguments) >= 2 and arguments[0] == "takes":
        (OUT / "takes").mkdir(exist_ok=True)
        lines, report = takes(arguments[1:]), "takes.txt"
    elif len(arguments) == 3 and arguments[0] == "call":
        lines, report = word_takes(ROOT / arguments[1], arguments[2]), f"call-{Path(arguments[1]).stem}-{arguments[2]}.txt"
    else:
        raise SystemExit(__doc__)
    (OUT / report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {OUT.relative_to(ROOT) / report}")


if __name__ == "__main__":
    main(sys.argv[1:])
