"""The cipher's settings, its wav mark, how a recording is cut, and how a letter is told. No voice is needed."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet
from enochaeon.audio import SAMPLE_RATE, Gaps, silence
from enochaeon.cipher_voice import Mark, mark_of, read_mark
from enochaeon.config import load_cipher_voice
from enochaeon.decode import NOT_HEARD, Calibration, apart, letters, lines, tell
from enochaeon.errors import EnochaeonError

CONFIG = Path(__file__).resolve().parents[1] / "enochaeon.json"
# Silences for the cutting tests. The tones have no quiet edge, so edge_ms is 0.
MARK = Mark(letter_ms=100, word_ms=400, line_ms=900, edge_ms=0, voice="test")
BRIDGE_MS = 50
HEAR_MS = 20


def _tone(ms: int) -> np.ndarray:
    count = int(SAMPLE_RATE * ms / 1000)
    time = np.arange(count, dtype=np.float32)
    return (0.4 * np.sin(2 * np.pi * 220 * time / SAMPLE_RATE)).astype(np.float32)


def _frames(*phones: int) -> np.ndarray:
    """Frames that give the whole of each step to one phone."""
    made = np.zeros((len(phones), 4), dtype=np.float32)
    for row, phone in enumerate(phones):
        made[row, phone] = 1.0
    return made


class CipherConfigTest(unittest.TestCase):
    def _settings(self) -> dict:
        return json.loads(CONFIG.read_text(encoding="utf-8"))["cipher"]

    def _load(self, cipher: dict | None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "enochaeon.json"
            path.write_text(json.dumps({} if cipher is None else {"cipher": cipher}), encoding="utf-8")
            return load_cipher_voice(path)

    def test_the_config_has_a_cipher_voice(self) -> None:
        voice = load_cipher_voice(CONFIG)
        self.assertLess(voice.letter_ms, voice.word_ms)
        self.assertLess(voice.word_ms, voice.line_ms)
        self.assertLess(voice.bridge_ms, voice.letter_ms)

    def test_a_config_with_no_cipher_section_says_so(self) -> None:
        with self.assertRaises(EnochaeonError) as raised:
            self._load(None)
        self.assertIn("cipher", str(raised.exception))

    def test_a_missing_setting_is_named(self) -> None:
        for name in self._settings():
            cipher = self._settings()
            del cipher[name]
            with self.assertRaises(EnochaeonError) as raised:
                self._load(cipher)
            self.assertIn(name, str(raised.exception))

    def test_each_silence_must_be_longer_than_the_one_before(self) -> None:
        cipher = self._settings()
        cipher["word_ms"] = cipher["letter_ms"]
        with self.assertRaises(EnochaeonError):
            self._load(cipher)

    def test_the_bridge_must_be_shorter_than_the_letter_silence(self) -> None:
        cipher = self._settings()
        cipher["bridge_ms"] = cipher["letter_ms"]
        with self.assertRaises(EnochaeonError):
            self._load(cipher)

    def test_a_length_must_be_a_whole_number(self) -> None:
        cipher = self._settings()
        cipher["line_ms"] = "long"
        with self.assertRaises(EnochaeonError):
            self._load(cipher)


class KeyVoiceTest(unittest.TestCase):
    def test_every_letter_sound_has_a_string_for_the_cipher_voice(self) -> None:
        alphabet = Alphabet.load()
        field = load_cipher_voice(CONFIG).sounds
        for atom in alphabet.atoms.values():
            for form in atom.forms():
                self.assertTrue(alphabet.voice_sound(field, atom.id, form))

    def test_a_voice_the_key_does_not_have_is_an_error(self) -> None:
        alphabet = Alphabet.load()
        with self.assertRaises(EnochaeonError):
            alphabet.voice_sound("no_such_voice", "un", "phone")


class MarkTest(unittest.TestCase):
    def test_a_mark_is_read_back_as_written(self) -> None:
        self.assertEqual(read_mark(MARK.comment()), MARK)

    def test_the_mark_has_the_silences_of_the_config(self) -> None:
        voice = load_cipher_voice(CONFIG)
        mark = mark_of(voice, "name")
        self.assertEqual(
            (mark.letter_ms, mark.word_ms, mark.line_ms, mark.edge_ms, mark.voice),
            (voice.letter_ms, voice.word_ms, voice.line_ms, voice.edge_ms, "name"),
        )

    def test_the_mark_of_a_call_is_not_a_cipher_mark(self) -> None:
        self.assertIsNone(read_mark(Gaps().comment()))
        self.assertIsNone(read_mark(None))
        self.assertIsNone(read_mark(""))


class CuttingTest(unittest.TestCase):
    def test_the_length_of_a_silence_tells_a_letter_a_word_and_a_line(self) -> None:
        tone = _tone(200)
        audio = np.concatenate([
            tone, silence(MARK.letter_ms), tone, silence(MARK.word_ms), tone, silence(MARK.line_ms), tone,
        ])
        shape = [[len(word) for word in line] for line in lines(audio, MARK, BRIDGE_MS, HEAR_MS)]
        self.assertEqual(shape, [[2, 1], [1]])

    def test_the_quiet_edge_of_a_sound_counts_as_silence(self) -> None:
        mark = Mark(letter_ms=100, word_ms=400, line_ms=900, edge_ms=80, voice="test")
        tone = _tone(200)
        # Two letters of one word: the letter silence with the quiet edge of each sound on both sides of it.
        within = silence(mark.letter_ms + 2 * mark.edge_ms)
        audio = np.concatenate([tone, within, tone])
        self.assertEqual([[len(word) for word in line] for line in lines(audio, mark, BRIDGE_MS, HEAR_MS)], [[2]])

    def test_a_short_silence_stays_inside_one_letter(self) -> None:
        audio = np.concatenate([_tone(80), silence(BRIDGE_MS - 10), _tone(120)])
        self.assertEqual(len(letters(audio, BRIDGE_MS, HEAR_MS)), 1)

    def test_a_letter_is_cut_the_same_wherever_it_stands(self) -> None:
        tone = _tone(200)
        cuts = []
        for shift in (0, 37, 111):
            audio = np.concatenate([np.zeros(shift, dtype=np.float32), tone, silence(MARK.letter_ms), tone])
            cuts.append(letters(audio, BRIDGE_MS, HEAR_MS))
        for found in cuts:
            self.assertEqual(len(found), 2)
            self.assertTrue(np.array_equal(found[0][1], cuts[0][0][1]))
            self.assertTrue(np.array_equal(found[1][1], cuts[0][1][1]))

    def test_silence_has_no_letters(self) -> None:
        self.assertEqual(lines(silence(500), MARK, BRIDGE_MS, HEAR_MS), [])


class TellingTest(unittest.TestCase):
    def test_a_sound_is_no_distance_from_itself(self) -> None:
        heard = _frames(0, 1, 1, 2)
        self.assertEqual(apart(heard, heard), 0.0)

    def test_a_sound_held_longer_is_nearer_than_another_sound(self) -> None:
        heard = _frames(0, 1, 2)
        held = _frames(0, 0, 1, 1, 1, 2)
        other = _frames(3, 1, 2)
        self.assertLess(apart(heard, held), apart(heard, other))

    def test_the_nearest_calibrated_sound_names_the_letter(self) -> None:
        calibration = Calibration("test", BRIDGE_MS, HEAR_MS, (
            ("first", "phone", _frames(0, 1)),
            ("second", "phone", _frames(2, 3)),
            ("second", "long", _frames(2, 2, 1)),
        ))
        self.assertEqual(tell(_frames(0, 0, 1), calibration), "first")
        self.assertEqual(tell(_frames(2, 1, 1), calibration), "second")

    def test_a_sound_too_short_to_hear_is_no_letter(self) -> None:
        calibration = Calibration("test", BRIDGE_MS, HEAR_MS, (("first", "phone", _frames(0, 1)),))
        self.assertEqual(tell(np.zeros((0, 4), dtype=np.float32), calibration), NOT_HEARD)

    def test_a_calibration_knows_the_voice_and_cut_it_was_made_for(self) -> None:
        calibration = Calibration("test", BRIDGE_MS, HEAR_MS, ())
        self.assertTrue(calibration.made_for("test", BRIDGE_MS, HEAR_MS))
        self.assertFalse(calibration.made_for("other", BRIDGE_MS, HEAR_MS))
        self.assertFalse(calibration.made_for("test", BRIDGE_MS + 1, HEAR_MS))


if __name__ == "__main__":
    unittest.main()
