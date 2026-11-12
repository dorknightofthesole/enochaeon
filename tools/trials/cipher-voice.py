"""Speak the cipher with John and see how well it comes back. Nothing shipped was changed.

This trial was run against the cipher as espeak spoke it, one breath for each word. The cipher is now
spoken by John one letter at a time, and this script does not run against it.
Its results are what the switch was decided on: scratch/cipher-voice/results.txt, letters.txt and hearing.txt.
tools/trials/cipher-roundtrip.py is the same count for the cipher as it is now.

  PYTHONPATH=src python3 tools/trials/cipher-voice.py letters
      Speaks every letter sound of the key alone, at each noise level, speed
      and ending in cipher-voice.json, and writes scratch/cipher-voice/letters.txt:
      which sounds the recognizer hears as nothing, which come out in more
      than one piece, which two letters it hears as the same, and how often a
      second take is taken for its own letter. One wav of the letters is
      written for each setting.

  PYTHONPATH=src python3 tools/trials/cipher-voice.py hearing
      Asks why a letter sound alone is heard badly. Each sound is spoken by
      espeak and by John and heard close, with wide silence round it, and
      between two other letter sounds. Then later takes are matched to
      templates by the phones written and by what the recognizer gives frame
      by frame. Writes scratch/cipher-voice/hearing.txt.

  PYTHONPATH=src python3 tools/trials/cipher-voice.py texts [RUN...] [TEXT...]
      Encodes and decodes each text of cipher-voice.json for each run named
      there (or only the runs and texts named on the command line), and writes
      scratch/cipher-voice/results.txt, with one wav and one decoded text for
      each text and run.

  PYTHONPATH=src python3 tools/trials/cipher-voice.py why RUN TEXT
      Lists every letter of one text in one letters run: what was sent, what
      was heard, and which letter each way of telling took it for. Writes
      scratch/cipher-voice/why-<text>-<run>.txt.

Three ways of speaking are compared:

  espeak    the cipher as shipped: one espeak breath for each word
  breath    John, one breath for each word, read with templates John made
  letters   John, each letter sound alone, with a fixed silence after a
            letter, a longer one between words and a longer one between lines

A decoded text is scored against what the key gives back from the text with
no audio at all, so only what speech and hearing lose is counted.

With both noise settings at zero John makes the same sound every time he is
given the same letter. The templates and the recording are then the same
sounds, read from the same file. A good score there says the letters can be
told apart. It does not say the recording survives being played and recorded
again.
"""

from __future__ import annotations

import difflib
import functools
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np

from enochaeon.alphabet import Alphabet, syllable_forms
from enochaeon.audio import SAMPLE_RATE, Gaps, normalize, read_wav, resample, silence, trim_silence, voiced_regions, write_wav
from enochaeon.calibrate import KWAH_TRAILER, TRAILER, _strip_trailer, _tokens
from enochaeon.decode import decode_audio, require_calibration
from enochaeon.encode import render as render_espeak
from enochaeon.lexicon import choose
from enochaeon import match
from enochaeon.match import fold_phones, phone_distance
from enochaeon.piper_voice import _IPA
from enochaeon.recognize import _SKIP, _load, transcribe
from enochaeon.synthesize import speak as speak_espeak

# The word list is searched with these two for every phone of every word, and each
# gives the same answer for the same phone. Kept answers make a long text take
# minutes, not hours. Only this process has them: the files of the cipher are as they were.
match._fold = functools.lru_cache(maxsize=None)(match._fold)
match._is_vowel = functools.lru_cache(maxsize=None)(match._is_vowel)
_fold, _is_vowel = match._fold, match._is_vowel

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SETTINGS = json.loads((HERE / "cipher-voice.json").read_text(encoding="utf-8"))
OUT = ROOT / "scratch" / "cipher-voice"
RUNS = OUT / "runs"
NOT_HEARD = "?"

Labels = dict[str, dict[str, str]]
Templates = list[tuple[str, str, tuple[str, ...]]]
Frames = list[tuple[str, np.ndarray]]


class John:
    """The Piper voice, given one espeak string at a time."""

    def __init__(self) -> None:
        from piper import PiperVoice, SynthesisConfig

        self.speaker = PiperVoice.load(ROOT / SETTINGS["voice"])
        self.config = SynthesisConfig
        self.table = {**_IPA, **SETTINGS["extra_symbols"]}
        self.ordered = sorted(self.table, key=len, reverse=True)
        self.kept: dict[tuple, np.ndarray] = {}

    def ipa(self, espeak: str) -> str:
        """The IPA for one espeak string. A stress mark lands on the phoneme that follows it."""
        return "".join(self.phones(espeak))

    def phones(self, espeak: str) -> list[str]:
        """The IPA phonemes of one espeak string, each with the stress mark that belongs before it."""
        pieces: list[str] = []
        for token in espeak.split():
            index = 0
            stress = ""
            while index < len(token):
                if token[index] == "'":
                    stress = "ˈ"
                    index += 1
                    continue
                symbol = next((name for name in self.ordered if token.startswith(name, index)), None)
                if symbol is None:
                    raise ValueError(f"no IPA for {token[index:]!r} in {token!r}")
                pieces.append(stress + self.table[symbol])
                stress = ""
                index += len(symbol)
        return pieces

    def speak(self, espeak: str, voice: dict) -> np.ndarray:
        """One espeak string as 16 kHz audio with the quiet edges cut."""
        noise = SETTINGS["noise"][voice["noise"]]
        # With no noise the same string is the same sound every time, so it is made once.
        steady = not noise["noise_scale"] and not noise["noise_w_scale"]
        key = (espeak, voice["noise"], voice["speed"], voice["end"])
        if steady and key in self.kept:
            return self.kept[key]
        config = self.config(length_scale=voice["speed"], **noise)
        chunks = list(self.speaker.synthesize(f"[[{self.ipa(espeak)}{voice['end']}]]", syn_config=config))
        audio = np.concatenate([np.asarray(chunk.audio_float_array, dtype=np.float32) for chunk in chunks])
        audio = normalize(trim_silence(resample(audio, chunks[0].sample_rate), pad_ms=SETTINGS["trim_pad_ms"]))
        if steady:
            self.kept[key] = audio
        return audio


def forms(alphabet: Alphabet) -> list[tuple[str, str, str]]:
    """(letter, form, espeak string) for every letter sound of the key."""
    return [(atom.id, form, spoken) for atom in alphabet.atoms.values() for form, spoken in atom.forms().items()]


def pieces(audio: np.ndarray) -> list[tuple[int, int]]:
    """Where there is sound. A silence shorter than bridge_ms does not divide a piece."""
    return voiced_regions(audio, SAMPLE_RATE, bridge_ms=SETTINGS["bridge_ms"])


def cut(audio: np.ndarray, silences: dict) -> list[list[list[np.ndarray]]]:
    """The letters of a recording, as lines of words of letters, told apart by the length of each silence."""
    found = pieces(audio)
    # The quiet kept on each side of a spoken sound adds to every silence.
    kept = 2 * SETTINGS["trim_pad_ms"]
    word_limit = (silences["letter_ms"] + silences["word_ms"]) / 2 + kept
    line_limit = (silences["word_ms"] + silences["line_ms"]) / 2 + kept
    pad = int(SAMPLE_RATE * SETTINGS["hear_pad_ms"] / 1000)
    quiet = silence(SETTINGS["hear_pad_ms"])
    lines: list[list[list[np.ndarray]]] = [[[]]]
    for index, (start, end) in enumerate(found):
        left = 0 if index == 0 else (found[index - 1][1] + start) // 2
        right = audio.shape[0] if index == len(found) - 1 else (end + found[index + 1][0]) // 2
        if index:
            gap_ms = (start - found[index - 1][1]) * 1000 / SAMPLE_RATE
            if gap_ms >= line_limit:
                lines.append([[]])
            elif gap_ms >= word_limit:
                lines[-1].append([])
        # Where a piece begins is found to the nearest 10 ms, and the recognizer hears a sound moved by a
        # few ms differently. So the letter is cut again from its first loud sample to its last, and the
        # same sound is then given to the recognizer from the same sample wherever it stands.
        letter = np.concatenate([quiet, audio[max(left, start - pad) : min(right, end + pad)], quiet])
        lines[-1][-1].append(trim_silence(letter, pad_ms=SETTINGS["hear_pad_ms"]))
    return lines


def alone(audio: np.ndarray) -> tuple[str, int, float]:
    """One letter sound heard alone: what was heard, how many pieces it came in, and the widest silence inside it."""
    frame = silence(SETTINGS["frame_ms"])
    framed = np.concatenate([frame, audio, frame])
    found = pieces(framed)
    if not found:
        return "", 0, 0.0
    pad = int(SAMPLE_RATE * SETTINGS["hear_pad_ms"] / 1000)
    heard = transcribe(framed[max(0, found[0][0] - pad) : found[-1][1] + pad])
    inside = [(found[index + 1][0] - found[index][1]) * 1000 / SAMPLE_RATE for index in range(len(found) - 1)]
    return heard, len(found), max(inside, default=0.0)


def nearest(heard: str, templates: Templates) -> tuple[str, int]:
    """The letter whose template is the fewest phone edits from what was heard, and that distance."""
    tokens = tuple(heard.split())
    if not tokens:
        return NOT_HEARD, 0
    distance, index = min((phone_distance(tokens, template), index) for index, (_, _, template) in enumerate(templates))
    return templates[index][0], distance


def letter_templates(alphabet: Alphabet, john: John, voice: dict) -> tuple[Labels, Templates, Frames]:
    """What the recognizer hears for each letter sound spoken alone.

    The labels have the first take of each sound. The templates have every
    take, because with noise two takes of one sound are not heard the same.
    The frames are what the recognizer gives frame by frame for each take.
    """
    steady = not any(SETTINGS["noise"][voice["noise"]].values())
    labels: Labels = {}
    templates: Templates = []
    frames: Frames = []
    for atom_id, form, spoken in forms(alphabet):
        for take in range(1 if steady else SETTINGS["takes"]):
            # The sound is cut out of silence the way a letter is cut out of a recording.
            letter = cut(padded(john.speak(spoken, voice), SETTINGS["frame_ms"]), SETTINGS["silences"]["long"])[0][0]
            found, given = timed(np.concatenate(letter))
            heard = " ".join(token for token, _ in found)
            frames.append((atom_id, given))
            if heard:
                templates.append((atom_id, form, tuple(heard.split())))
                labels.setdefault(atom_id, {}).setdefault(form, heard)
    return labels, templates, frames


def breath_labels(alphabet: Alphabet, john: John, voice: dict) -> Labels:
    """What the recognizer hears for each letter sound at the start of a breath, the way `enochaeon calibrate` finds it."""
    trailers = {name: _tokens(transcribe(john.speak(name, voice))) for name in (TRAILER, KWAH_TRAILER)}
    labels: Labels = {}
    for atom_id, form, spoken in forms(alphabet):
        trailer = KWAH_TRAILER if spoken.replace(" ", "").startswith("kw") else TRAILER
        framed = _tokens(transcribe(john.speak(f"{spoken} {trailer}", voice)))
        labels.setdefault(atom_id, {})[form] = " ".join(_strip_trailer(framed, trailers[trailer]))
    return labels


def render_letters(text: str, alphabet: Alphabet, john: John, voice: dict, silences: dict) -> np.ndarray:
    """Each letter sound alone, with the silence that says what follows it."""
    parts: list[np.ndarray] = []
    gap = silences["word_ms"]
    for item in alphabet.atom_ids(text):
        if isinstance(item, str):
            gap = silences["line_ms"] if item == "\n" else silences["word_ms"]
            continue
        atoms = tuple(alphabet.atoms[atom_id] for atom_id in item)
        for index, (atom, form) in enumerate(syllable_forms(atoms)):
            if parts:
                parts.append(silence(silences["letter_ms"] if index else gap))
            parts.append(john.speak(atom.phone if form == "phone" else atom.long, voice))
    return np.concatenate(parts) if parts else silence(silences["word_ms"])


def render_breath(text: str, alphabet: Alphabet, john: John, voice: dict, gaps: Gaps) -> np.ndarray:
    """One breath for each word, with the silences the shipped cipher uses."""
    parts: list[np.ndarray] = []
    for item in alphabet.atom_ids(text):
        if isinstance(item, str):
            parts.append(silence(gaps.nl_ms if item == "\n" else gaps.word_ms))
            continue
        parts.append(john.speak(alphabet.pronounce_atoms(tuple(alphabet.atoms[atom_id] for atom_id in item)), voice))
    return np.concatenate(parts) if parts else silence(gaps.word_ms)


def decode_letters(audio: np.ndarray, alphabet: Alphabet, labels: Labels, templates: Templates,
                   silences: dict, frames: Frames | None = None) -> tuple[str, str]:
    """The text after the word list, and the text as the letters alone give it.

    A letter is the nearest template by the phones written for it, or, when
    frames are given, the nearest by what the recognizer gives frame by frame.
    """
    corrected: list[str] = []
    plain: list[str] = []
    for line in cut(audio, silences):
        words: list[str] = []
        raws: list[str] = []
        for word in line:
            listened = [timed(letter) for letter in word]
            heard = [" ".join(token for token, _ in found) for found, _ in listened]
            if frames is None:
                letters = tuple(nearest(phones, templates)[0] for phones in heard)
            else:
                letters = tuple(min(frames, key=lambda row: frames_apart(given, row[1]))[0] for _, given in listened)
            raw, _ = alphabet.decode_atoms([letters])
            raws.append(raw)
            words.append(choose(" ".join(heard), raw, alphabet, labels))
        corrected.append(" ".join(words))
        plain.append(" ".join(raws))
    return "\n".join(corrected), "\n".join(plain)


def tokens(text: str) -> list[str]:
    """The words of a text in order, with a line break between two lines."""
    found: list[str] = []
    for line in text.strip().split("\n"):
        if found:
            found.append("\n")
        found += line.split()
    return found


def score(expected: str, decoded: str) -> tuple[int, int, int, int]:
    """(words right, words, line breaks kept, line breaks) of a decoded text against the expected one."""
    want, got = tokens(expected), tokens(decoded)
    blocks = difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks()
    same = [token for block in blocks for token in want[block.a : block.a + block.size]]
    breaks = same.count("\n")
    return len(same) - breaks, len(want) - want.count("\n"), breaks, want.count("\n")


def voice_name(voice: dict) -> str:
    return f"{voice['noise']}-{voice['speed']}-{'stop' if voice['end'] else 'bare'}"


def letters() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    alphabet = Alphabet.load()
    john = John()
    report = ["Every letter sound of the key, spoken alone by John and heard by the recognizer.",
              f"voice {SETTINGS['voice']}; a silence under {SETTINGS['bridge_ms']} ms does not divide a sound.", ""]
    for noise in SETTINGS["noise"]:
        for speed in SETTINGS["speeds"]:
            for end in SETTINGS["ends"]:
                voice = {"noise": noise, "speed": speed, "end": end}
                steady = not any(SETTINGS["noise"][noise].values())
                rows: list[tuple[str, str, str, list[tuple[str, int, float]]]] = []
                audio: list[np.ndarray] = []
                lengths: list[float] = []
                for atom_id, form, spoken in forms(alphabet):
                    takes = []
                    for take in range(SETTINGS["takes"]):
                        sound = john.speak(spoken, voice)
                        takes.append(alone(sound))
                        if not take:
                            audio += [sound, silence(SETTINGS["silences"]["long"]["letter_ms"])]
                            lengths.append(sound.shape[0] * 1000 / SAMPLE_RATE)
                    rows.append((atom_id, form, spoken, takes))
                write_wav(OUT / f"letters-{voice_name(voice)}.wav", np.concatenate(audio))
                templates: Templates = [(atom_id, form, tuple(takes[0][0].split())) for atom_id, form, _, takes in rows
                                        if takes[0][0]]
                nothing = [f"{atom_id}.{form}" for atom_id, form, _, takes in rows if not takes[0][0]]
                split = [f"{atom_id}.{form} ({max(take[1] for take in takes)} pieces, {max(take[2] for take in takes):.0f} ms inside)"
                         for atom_id, form, _, takes in rows if max(take[1] for take in takes) > 1]
                owners: dict[tuple[str, ...], str] = {}
                same: list[str] = []
                for atom_id, form, template in templates:
                    other = owners.setdefault(fold_phones(" ".join(template)), atom_id)
                    if other != atom_id:
                        same.append(f"{other} and {atom_id}.{form} ({' '.join(template)})")
                later = [(atom_id, take[0]) for atom_id, _, _, takes in rows for take in takes[1:]]
                own = sum(1 for atom_id, heard in later if nearest(heard, templates)[0] == atom_id)
                close = sorted(
                    (phone_distance(first, second), f"{one}.{form} / {two}.{other}")
                    for index, (one, form, first) in enumerate(templates)
                    for two, other, second in templates[index + 1 :] if one != two
                )
                report += [
                    f"== noise {noise}, speed {speed}, ending {end!r}: {len(rows)} sounds, "
                    f"{sum(lengths) / len(lengths):.0f} ms each on average, longest {max(lengths):.0f} ms",
                    f"   heard as nothing: {', '.join(nothing) or 'none'}",
                    f"   in more than one piece: {', '.join(split) or 'none'}",
                    f"   two letters heard as the same: {'; '.join(same) or 'none'}",
                    f"   later takes taken for their own letter: {own} of {len(later)}"
                    + (" (with no noise every take is the same sound)" if steady else ""),
                    f"   letters fewest phone edits apart: {'; '.join(f'{pair} {distance}' for distance, pair in close[:6])}",
                    "   what was heard, first take: "
                    + "; ".join(f"{atom_id}.{form} [{spoken}] {takes[0][0] or '-'}" for atom_id, form, spoken, takes in rows),
                    "",
                ]
                print("\n".join(report[-8:-2]), flush=True)
    (OUT / "letters.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {(OUT / 'letters.txt').relative_to(ROOT)}")
    return 0


def timed(audio: np.ndarray) -> tuple[list[tuple[str, float]], np.ndarray]:
    """The phones the recognizer hears with the time of each in ms, and what it gives for every frame of the audio."""
    import torch

    extractor, model, table, pad_id, device = _load()
    inputs = extractor(np.asarray(audio, dtype=np.float32), sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.inference_mode():
        logits = model(inputs.input_values.to(device)).logits[0]
    frames = torch.softmax(logits, dim=-1).cpu().numpy()
    step = audio.shape[0] * 1000 / SAMPLE_RATE / max(1, frames.shape[0])
    found: list[tuple[str, float]] = []
    previous = None
    for frame, index in enumerate(frames.argmax(axis=1).tolist()):
        if index == previous:
            continue
        previous = index
        token = table.get(index, "")
        if index != pad_id and token not in _SKIP:
            found.append((token, (frame + 0.5) * step))
    return found, frames


def padded(sound: np.ndarray, ms: int) -> np.ndarray:
    return np.concatenate([silence(ms), sound, silence(ms)])


def in_row(left: np.ndarray, sound: np.ndarray, right: np.ndarray, silences: dict) -> str:
    """One letter sound heard between two others, with the letter silence on each side of it."""
    gap = silence(silences["letter_ms"])
    clip = np.concatenate([left, gap, sound, gap, right])
    start = (left.shape[0] + gap.shape[0] / 2) * 1000 / SAMPLE_RATE
    end = (left.shape[0] + gap.shape[0] + sound.shape[0] + gap.shape[0] / 2) * 1000 / SAMPLE_RATE
    return " ".join(token for token, at in timed(clip)[0] if start <= at < end)


def frames_apart(one: np.ndarray, two: np.ndarray) -> float:
    """How far apart two sounds are, frame by frame: 0 is the same, 1 is nothing shared.

    Each frame is what the recognizer gives for every phone it knows. The two
    sounds are laid along each other so that one may be held longer than the
    other, and the distance is the average over that path.
    """
    cost = (1.0 - np.sqrt(one) @ np.sqrt(two).T).tolist()
    rows, columns = len(cost), len(cost[0])
    above = [0.0] + [float("inf")] * columns
    for row in range(rows):
        here = [float("inf")]
        line = cost[row]
        for column in range(columns):
            here.append(line[column] + min(above[column + 1], here[column], above[column]))
        above = here
    return above[columns] / (rows + columns)


def skeleton(tokens: list[str]) -> list[str]:
    """The consonants of a sound, with the recognizer's spellings of one phone made the same."""
    return [_fold(token.replace("ˈ", "")) for token in tokens if not _is_vowel(token.replace("ˈ", ""))]


def same_pairs(heard: list[tuple[str, str, str]]) -> list[str]:
    """The letters whose sound is heard as another letter's, from (letter, form, phones)."""
    owners: dict[tuple[str, ...], str] = {}
    same: list[str] = []
    for atom_id, form, phones in heard:
        other = owners.setdefault(fold_phones(phones), f"{atom_id}.{form}")
        if other.split(".")[0] != atom_id:
            same.append(f"{other} = {atom_id}.{form} ({phones or '-'})")
    return same


def hearing() -> int:
    """Is it John or the recognizer, and does it help to hear a letter with more round it?"""
    OUT.mkdir(parents=True, exist_ok=True)
    alphabet = Alphabet.load()
    john = John()
    setup = SETTINGS["hearing"]
    silences = SETTINGS["silences"][setup["row_silences"]]
    sounds = forms(alphabet)
    sent = [skeleton(john.phones(spoken)) for _, _, spoken in sounds]
    speakers = [("espeak", speak_espeak)]
    speakers += [(f"John {voice_name(voice)}", lambda spoken, voice=voice: john.speak(spoken, voice))
                 for voice in setup["voices"]]
    report = [
        "Each letter sound of the key heard in several ways.",
        f"close: with {SETTINGS['hear_pad_ms']} ms of silence on each side. wide: with {setup['wide_ms']} ms.",
        f"row N: between the letter sounds N places before and after it in the key, {silences['letter_ms']} ms apart, "
        "heard as one recording; the phones that fall in its own stretch are its own.",
        "consonants as sent: how many of the sounds were heard with the consonants that were sent. The vowel is not",
        "counted, because the recognizer writes one vowel many ways. It is a rough count of how well a sound is heard.",
        "",
    ]
    count = len(sounds)
    for name, say in speakers:
        begun = len(report)
        audio = [say(spoken) for _, _, spoken in sounds]
        ways = {
            "close": [" ".join(token for token, _ in timed(padded(sound, SETTINGS["hear_pad_ms"]))[0]) for sound in audio],
            "wide": [" ".join(token for token, _ in timed(padded(sound, setup["wide_ms"]))[0]) for sound in audio],
        }
        for shift in setup["row_shifts"]:
            ways[f"row {shift}"] = [
                in_row(audio[(index - shift) % count], audio[index], audio[(index + shift) % count], silences)
                for index in range(count)]
        report.append(f"== {name}")
        for way, heard in ways.items():
            right = sum(1 for index, phones in enumerate(heard) if skeleton(phones.split()) == sent[index])
            same = same_pairs([(atom_id, form, heard[index]) for index, (atom_id, form, _) in enumerate(sounds)])
            report += [
                f"   {way:7} consonants as sent {right:2d} of {count}; heard as another letter: {len(same)}"
                + (f": {'; '.join(same)}" if same else ""),
                "           " + "; ".join(f"[{spoken}] {heard[index] or '-'}" for index, (_, _, spoken) in enumerate(sounds)),
            ]
        rows = [ways[f"row {shift}"] for shift in setup["row_shifts"]]
        agree = sum(1 for index in range(count) if len({fold_phones(row[index]) for row in rows}) == 1)
        report += [f"   the same in every row: {agree} of {count}", ""]
        print("\n".join(line[:200] for line in report[begun:] if not line.startswith("     ")), flush=True)

    first = setup["voices"][0]
    report += [
        "Telling the letters apart by what the recognizer gives frame by frame, and by the phones it writes.",
        f"Templates are one take of each sound at the first noise level. {SETTINGS['takes']} more takes of each sound at the",
        f"second noise level are each given to the nearest template. Speed {first['speed']}, ending {first['end']!r}.",
        "",
    ]
    for template_noise, take_noise in setup["against"]:
        base = {**first, "noise": template_noise}
        other = {**first, "noise": take_noise}
        made = [timed(padded(john.speak(spoken, base), SETTINGS["hear_pad_ms"])) for _, _, spoken in sounds]
        templates: Templates = [(atom_id, form, tuple(token for token, _ in made[index][0]))
                                for index, (atom_id, form, _) in enumerate(sounds) if made[index][0]]
        by_phones = by_frames = tries = 0
        wrong: list[str] = []
        for atom_id, form, spoken in sounds:
            for _ in range(SETTINGS["takes"]):
                # A take is made new each time, so John's own store of sounds is passed by.
                john.kept.pop((spoken, other["noise"], other["speed"], other["end"]), None)
                found, frames = timed(padded(john.speak(spoken, other), SETTINGS["hear_pad_ms"]))
                tries += 1
                by_phones += nearest(" ".join(token for token, _ in found), templates)[0] == atom_id
                closest = min(range(count), key=lambda index: frames_apart(frames, made[index][1]))
                if sounds[closest][0] == atom_id:
                    by_frames += 1
                else:
                    wrong.append(f"{atom_id}.{form} as {sounds[closest][0]}.{sounds[closest][1]}")
        report += [
            f"   templates at noise {template_noise}, takes at noise {take_noise}: "
            f"by phones {by_phones} of {tries}, frame by frame {by_frames} of {tries}",
            f"      frame by frame, taken for another letter: {'; '.join(sorted(set(wrong))) or 'none'}",
        ]
        print(report[-2], flush=True)
        print(report[-1][:300], flush=True)
    (OUT / "hearing.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {(OUT / 'hearing.txt').relative_to(ROOT)}")
    return 0


def texts(names: list[str]) -> int:
    RUNS.mkdir(parents=True, exist_ok=True)
    alphabet = Alphabet.load()
    john = John()
    wanted = [name for name in names if name in SETTINGS["texts"]]
    names = [name for name in names if name not in wanted]
    chosen = [run for run in SETTINGS["runs"] if not names or run["name"] in names]
    for run in chosen:
        started = time.time()
        voice = {key: run[key] for key in ("noise", "speed", "end") if key in run}
        silences = SETTINGS["silences"].get(run.get("silences", ""), {})
        gaps = Gaps()
        if run["scheme"] == "espeak":
            labels = require_calibration(alphabet)
        elif run["scheme"] == "breath":
            labels = breath_labels(alphabet, john, voice)
        else:
            labels, templates, frames = letter_templates(alphabet, john, voice)
        rows = []
        for name in wanted or SETTINGS["texts"]:
            source = ROOT / name
            text = source.read_text(encoding="utf-8")
            expected, _ = alphabet.decode_atoms(alphabet.atom_ids(text))
            plain = None
            if run["scheme"] == "espeak":
                audio = render_espeak(text, alphabet, gaps)
            elif run["scheme"] == "breath":
                audio = render_breath(text, alphabet, john, voice, gaps)
            else:
                audio = render_letters(text, alphabet, john, voice, silences)
            # The recording is written and read back, so what is decoded is the file a person would have.
            write_wav(OUT / f"{source.stem}-{run['name']}.wav", audio)
            audio, _ = read_wav(OUT / f"{source.stem}-{run['name']}.wav")
            if run["scheme"] == "letters":
                decoded, plain = decode_letters(audio, alphabet, labels, templates, silences,
                                                frames if run.get("match") == "frames" else None)
            else:
                decoded, _ = decode_audio(audio, SAMPLE_RATE, alphabet, labels, gaps)
            (OUT / f"{source.stem}-{run['name']}.txt").write_text(decoded.strip() + "\n", encoding="utf-8")
            right, words, kept, breaks = score(expected, decoded)
            row = {"text": name, "words_right": right, "words": words, "breaks_kept": kept, "breaks": breaks,
                   "lines_decoded": tokens(decoded).count("\n") + 1, "lines": breaks + 1,
                   "words_decoded": len(tokens(decoded)) - tokens(decoded).count("\n"),
                   "seconds": round(audio.shape[0] / SAMPLE_RATE, 1)}
            if plain is not None:
                row["words_right_before_word_list"] = score(expected, plain)[0]
            rows.append(row)
            print(f"{run['name']:32} {source.stem:20} words {right}/{words} ({row['words_decoded']} came back)  "
                  f"lines {row['lines_decoded']}/{row['lines']}  {row['seconds']} s", flush=True)
        # A run made again for some of the texts keeps what it has for the others.
        kept = RUNS / f"{run['name']}.json"
        before = json.loads(kept.read_text(encoding="utf-8"))["rows"] if kept.is_file() else []
        rows = [row for row in before if row["text"] not in {new["text"] for new in rows}] + rows
        kept.write_text(
            json.dumps({"run": run, "rows": rows, "took_seconds": round(time.time() - started)}, indent=2) + "\n",
            encoding="utf-8")
    return results()


def why(run_name: str, text_name: str) -> int:
    """Each letter of one text in one letters run: what was sent, and what each way of telling took it for."""
    alphabet = Alphabet.load()
    john = John()
    run = next(run for run in SETTINGS["runs"] if run["name"] == run_name)
    voice = {key: run[key] for key in ("noise", "speed", "end")}
    silences = SETTINGS["silences"][run["silences"]]
    labels, templates, frames = letter_templates(alphabet, john, voice)
    text = (ROOT / text_name).read_text(encoding="utf-8")
    sent = [(atom.id, form) for item in alphabet.atom_ids(text) if not isinstance(item, str)
            for atom, form in syllable_forms(tuple(alphabet.atoms[atom_id] for atom_id in item))]
    found = [letter for line in cut(render_letters(text, alphabet, john, voice, silences), silences)
             for word in line for letter in word]
    report = [f"{run_name}, {text_name}: {len(sent)} letters sent, {len(found)} cut from the recording",
              "sent | heard | nearest by phones (edits) | nearest frame by frame (how far) | how far from its own letter"]
    wrong_phones = wrong_frames = 0
    for (atom_id, form), letter in zip(sent, found):
        heard, given = timed(letter)
        phones = " ".join(token for token, _ in heard)
        by_phones, edits = nearest(phones, templates)
        apart = sorted((frames_apart(given, row[1]), row[0]) for row in frames)
        own = min(distance for distance, name in apart if name == atom_id)
        wrong_phones += by_phones != atom_id
        wrong_frames += apart[0][1] != atom_id
        report.append(f"{atom_id}.{form} | {phones or '-'} | {by_phones} ({edits}) | {apart[0][1]} ({apart[0][0]:.3f}) | {own:.3f}"
                      + ("" if by_phones == atom_id and apart[0][1] == atom_id else "   <--"))
    report.append(f"taken for another letter: by phones {wrong_phones}, frame by frame {wrong_frames}, of {len(found)}")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"why-{Path(text_name).stem}-{run_name}.txt"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


def results() -> int:
    """Write results.txt from every run that has been made, in the order of cipher-voice.json."""
    order = [run["name"] for run in SETTINGS["runs"]]
    made = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.json")}
    report = ["The cipher spoken three ways, and how much of each text came back.",
              "words: words that came back right, of the words the key gives back with no audio.",
              "before: the same count before the word list corrects a word (letters only).",
              "came back: how many words the decoder wrote, right or wrong. lines: how many lines it wrote, of the lines in the text.",
              "length: the recording, in seconds.", ""]
    for name in SETTINGS["texts"]:
        report.append(f"== {name}")
        for run in sorted(made, key=lambda item: order.index(item) if item in order else len(order)):
            row = next((row for row in made[run]["rows"] if row["text"] == name), None)
            if row is None:
                continue
            before = row.get("words_right_before_word_list")
            report.append(
                f"   {run:32} words {row['words_right']:3d}/{row['words']:<3d}  "
                f"before {before if before is not None else '-':>3}  came back {row['words_decoded']:3d}  "
                f"lines {row['lines_decoded']:2d}/{row['lines']:<2d}  length {row['seconds']:7.1f}")
        report.append("")
    report.append("The runs:")
    for run in sorted(made, key=lambda item: order.index(item) if item in order else len(order)):
        report.append(f"   {run}: {json.dumps(made[run]['run'])}")
    (OUT / "results.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {(OUT / 'results.txt').relative_to(ROOT)}")
    return 0


def main(arguments: list[str]) -> int:
    if arguments == ["letters"]:
        return letters()
    if arguments == ["hearing"]:
        return hearing()
    if arguments[:1] == ["why"] and len(arguments) == 3:
        return why(arguments[1], arguments[2])
    if arguments[:1] == ["texts"]:
        return texts(arguments[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
