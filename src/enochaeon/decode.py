"""Read an Enochaeon WAV back to English.

A recording is cut at its silences into lines, words and letters. Each letter
is heard alone, and is the letter whose calibrated sound is nearest to it.
The key then turns the letters back into English. No word list is used: what
comes back is what the letters spell.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from enochaeon.alphabet import CALIBRATION_PATH, Alphabet
from enochaeon.audio import COMMENT_PREFIX, SAMPLE_RATE, read_comment, read_wav, resample, silence, trim_silence, voiced_regions
from enochaeon.cipher_voice import Mark, mark_of, read_mark
from enochaeon.config import load_cipher_voice
from enochaeon.errors import EnochaeonError
from enochaeon.recognize import frames

CALIBRATION_VERSION = 4
RUN_CALIBRATE = "Run: enochaeon calibrate"
# The letter id given to a sound too short to be heard. The key has no row for it.
NOT_HEARD = "?"


@dataclass(frozen=True)
class Calibration:
    """What the recognizer gives for each letter sound, and how the sounds were made and cut."""

    # The name of the voice that spoke the sounds. A recording carries the same name in its mark.
    voice: str
    bridge_ms: int
    hear_ms: int
    # (letter id, form, frames) for every letter sound.
    sounds: tuple[tuple[str, str, np.ndarray], ...]

    def made_for(self, name: str, bridge_ms: int, hear_ms: int) -> bool:
        """True when these sounds were spoken by the voice of that name and cut with those two lengths."""
        return (self.voice, self.bridge_ms, self.hear_ms) == (name, bridge_ms, hear_ms)


def frames_path(path: Path) -> Path:
    """The file of frames that goes with a calibration file."""
    return path.with_suffix(".npy")


def load_calibration(path: Path | None = None) -> Calibration:
    source = path or CALIBRATION_PATH
    if not source.is_file() or not frames_path(source).is_file():
        raise EnochaeonError(f"No calibration file. {RUN_CALIBRATE}")
    raw = json.loads(source.read_text(encoding="utf-8"))
    if raw.get("version") != CALIBRATION_VERSION:
        raise EnochaeonError(f"{source} is an old calibration. {RUN_CALIBRATE}")
    try:
        every = np.load(frames_path(source))
        sounds = tuple(
            (str(atom_id), str(form), every[int(start) : int(end)])
            for atom_id, forms in raw["sounds"].items()
            for form, (start, end) in forms.items()
        )
        calibration = Calibration(str(raw["voice"]), int(raw["bridge_ms"]), int(raw["hear_ms"]), sounds)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise EnochaeonError(f"{source} cannot be read as a calibration. {RUN_CALIBRATE}") from exc
    if not sounds or any(not heard.shape[0] for _, _, heard in sounds):
        raise EnochaeonError(f"{source} has a letter sound with nothing heard for it. {RUN_CALIBRATE}")
    return calibration


def require_calibration(alphabet: Alphabet, path: Path | None = None) -> Calibration:
    """The calibration, with a sound for every letter sound of the key."""
    calibration = load_calibration(path)
    have = {(atom_id, form) for atom_id, form, _ in calibration.sounds}
    missing = [
        f"{atom_id}.{form}"
        for atom_id, atom in alphabet.atoms.items()
        for form in atom.forms()
        if (atom_id, form) not in have
    ]
    if missing:
        raise EnochaeonError(f"Calibration is missing {', '.join(sorted(missing))}. {RUN_CALIBRATE}")
    return calibration


def letters(audio: np.ndarray, bridge_ms: int, hear_ms: int) -> list[tuple[float, np.ndarray]]:
    """Each stretch of sound in a recording, with the length of the silence before it in milliseconds.

    A silence shorter than ``bridge_ms`` is inside one letter. Where a
    stretch begins is found only to the nearest 10 ms, and the recognizer
    hears a sound moved by a few milliseconds differently. So each letter is
    cut again from its first loud sample to its last, with ``hear_ms`` of
    quiet on each side. The same sound is then given to the recognizer from
    the same sample wherever it stands in a recording.
    """
    found = voiced_regions(audio, SAMPLE_RATE, bridge_ms=bridge_ms)
    pad = int(SAMPLE_RATE * hear_ms / 1000)
    quiet = silence(hear_ms)
    cut: list[tuple[float, np.ndarray]] = []
    for index, (start, end) in enumerate(found):
        # A letter never reaches past the middle of the silence on either side of it.
        left = 0 if index == 0 else (found[index - 1][1] + start) // 2
        right = audio.shape[0] if index == len(found) - 1 else (end + found[index + 1][0]) // 2
        before = (start - found[index - 1][1]) * 1000 / SAMPLE_RATE if index else 0.0
        letter = np.concatenate([quiet, audio[max(left, start - pad) : min(right, end + pad)], quiet])
        cut.append((before, trim_silence(letter, pad_ms=hear_ms)))
    return cut


def lines(audio: np.ndarray, mark: Mark, bridge_ms: int, hear_ms: int) -> list[list[list[np.ndarray]]]:
    """The letters of a recording as lines of words of letters, told apart by the length of each silence."""
    # The quiet kept on each side of a spoken sound is part of every silence.
    kept = 2 * mark.edge_ms
    word_limit = (mark.letter_ms + mark.word_ms) / 2 + kept
    line_limit = (mark.word_ms + mark.line_ms) / 2 + kept
    grouped: list[list[list[np.ndarray]]] = []
    for before, letter in letters(audio, bridge_ms, hear_ms):
        if not grouped or before >= line_limit:
            grouped.append([[]])
        elif before >= word_limit:
            grouped[-1].append([])
        grouped[-1][-1].append(letter)
    return grouped


def apart(one: np.ndarray, two: np.ndarray) -> float:
    """How far apart two sounds are, from the frames of each. The same sound is 0, and a farther one is more.

    Two frames are close when they give their shares to the same phones. The
    sounds are laid along each other so that one may be held longer than the
    other, and the distance is the average along that path.
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


def tell(heard: np.ndarray, calibration: Calibration) -> str:
    """The letter whose calibrated sound is nearest to what was heard."""
    if not heard.shape[0]:
        return NOT_HEARD
    return min(calibration.sounds, key=lambda sound: apart(heard, sound[2]))[0]


def decode_audio(
    audio: np.ndarray,
    sample_rate: int,
    alphabet: Alphabet,
    calibration: Calibration,
    mark: Mark,
) -> tuple[str, bool]:
    """The English text of a recording. The flag is true when a sound gave no letter the key can spell."""
    if sample_rate != SAMPLE_RATE:
        audio = resample(audio, sample_rate)
    stream: list[tuple[str, ...] | str] = []
    for line in lines(audio, mark, calibration.bridge_ms, calibration.hear_ms):
        if stream:
            stream.append("\n")
        for index, word in enumerate(line):
            if index:
                stream.append(" ")
            stream.append(tuple(tell(frames(letter), calibration) for letter in word))
    return alphabet.decode_atoms(stream)


def decode_file(path: Path, alphabet: Alphabet, calibration: Calibration) -> tuple[str, bool]:
    comment = read_comment(path)
    mark = read_mark(comment)
    if mark is None and comment and comment.startswith(COMMENT_PREFIX):
        raise EnochaeonError(
            f"{path} carries the mark of a spoken Call or of the earlier cipher voice. Neither can be read back."
        )
    if mark is None:
        print(
            "This WAV has no Enochaeon mark. Decoding it anyway, with the silences in enochaeon.json.",
            file=sys.stderr,
        )
        mark = mark_of(load_cipher_voice(), calibration.voice)
    elif mark.voice != calibration.voice:
        raise EnochaeonError(
            f"{path} was spoken by a voice the calibration was not made with. "
            f"Set the cipher section of enochaeon.json as it was when the wav was made. {RUN_CALIBRATE}"
        )
    audio, sample_rate = read_wav(path)
    return decode_audio(audio, sample_rate, alphabet, calibration, mark)
