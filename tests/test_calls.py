"""Enochian call text is spoken as Enochian, not as English."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet
from enochaeon.audio import SAMPLE_RATE, WORD_MS
from enochaeon.config import CallVoice, load_call_voice
from enochaeon.enochian import call_files, call_gaps, parse, phonetic_text, render
from enochaeon.errors import EnochaeonError
from enochaeon.piper_voice import ipa_of
from enochaeon.synthesize import speak


class CallPronunciationTest(unittest.TestCase):
    def test_a_closed_vowel_stays_short(self) -> None:
        self.assertEqual(phonetic_text("Ol"), "Q l")
        self.assertEqual(phonetic_text("sonf"), "s Q n f")

    def test_a_short_one_vowel_word_is_held(self) -> None:
        plain = speak("Q l")
        held = render("Ol")
        self.assertGreaterEqual(held.size / SAMPLE_RATE, 0.40)
        self.assertGreaterEqual(render("od").size / SAMPLE_RATE, 0.40)
        self.assertGreaterEqual(render("ror").size / SAMPLE_RATE, 0.40)
        self.assertGreater(held.size, plain.size)
        self.assertEqual(phonetic_text("Ol"), "Q l")
        self.assertTrue(np.array_equal(render("goho"), speak("g Q h oU")))
        self.assertTrue(np.array_equal(render("Iad"), speak("j a d")))
        self.assertTrue(np.array_equal(render("balt"), speak("b a l t")))
        self.assertTrue(np.array_equal(render("ds"), speak("d'i: 'Es")))

    def test_a_leading_i_before_a_vowel_is_y(self) -> None:
        # Dee read Iad as Yad. The A is closed by D, so it stays short.
        self.assertEqual(phonetic_text("Iad"), "j a d")

    def test_an_open_vowel_is_long(self) -> None:
        self.assertEqual(phonetic_text("goho"), "g Q h oU")

    def test_a_word_with_no_vowel_is_letter_names(self) -> None:
        self.assertEqual(phonetic_text("ds"), "d'i: 'Es")

    def test_punctuation_breaks_the_line(self) -> None:
        self.assertEqual(phonetic_text("Ol sonf, goho. Iad"), "Q l s Q n f g Q h oU\nj a d")

    def test_piper_hears_the_vowel_in_lot(self) -> None:
        self.assertEqual(ipa_of("Q l"), "ɒl")
        self.assertEqual(ipa_of("g Q h oU"), "ɡɒhoʊ")
        self.assertEqual(ipa_of("d'i: 'Es"), "dˈiːˈɛs")

    def test_the_shipped_config_uses_piper(self) -> None:
        root = Path(__file__).resolve().parents[1] / "enochaeon.json"
        voice = load_call_voice(root)
        self.assertEqual(voice.engine, "piper")
        self.assertGreater(voice.length_scale, 1)
        self.assertEqual(voice.word_ms, 400)
        self.assertIn("john", voice.piper_voice)

    def test_a_piper_breath_can_be_shorter(self) -> None:
        shorter = CallVoice(engine="piper", word_ms=400)
        self.assertEqual(call_gaps(shorter).word_ms, 400)
        self.assertEqual(call_gaps(shorter).nl_ms, 1000)
        self.assertEqual(call_gaps(CallVoice(word_ms=400)).word_ms, WORD_MS)
        self.assertEqual(call_gaps(CallVoice(engine="piper")).word_ms, WORD_MS)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "enochaeon.json"
            path.write_text(
                '{"calls": {"engine": "piper", "piper": {"word_ms": 400}}}\n',
                encoding="utf-8",
            )
            self.assertEqual(load_call_voice(path).word_ms, 400)
            path.write_text('{"calls": {"piper": {"word_ms": 0}}}\n', encoding="utf-8")
            with self.assertRaises(EnochaeonError):
                load_call_voice(path)

    def test_the_call_voice_defaults_to_espeak(self) -> None:
        missing = Path("/no/such/enochaeon.json")
        voice = load_call_voice(missing)
        self.assertEqual(voice, CallVoice())
        self.assertEqual(voice.chosen("piper").engine, "piper")
        self.assertEqual(voice.chosen(None).engine, "espeak")
        with self.assertRaises(EnochaeonError):
            voice.chosen("mbrola")

    def test_a_call_is_not_the_english_cipher(self) -> None:
        english = Alphabet.load().phonetic_text("ol")
        self.assertNotEqual(phonetic_text("ol"), english)

    def test_an_unknown_mark_names_itself(self) -> None:
        with self.assertRaises(EnochaeonError) as caught:
            phonetic_text("Ol@")
        self.assertIn("'@'", str(caught.exception))
        self.assertIn("position 2", str(caught.exception))

    def test_the_forty_eight_calls_are_files(self) -> None:
        root = Path(__file__).resolve().parents[1] / "calls"
        files = call_files(root)
        self.assertEqual(len(files), 48)
        first = (root / "01.txt").read_text(encoding="utf-8")
        self.assertTrue(first.startswith("Ol sonf vorsg"))
        lil = (root / "19-lil.txt").read_text(encoding="utf-8")
        tex = (root / "48-tex.txt").read_text(encoding="utf-8")
        self.assertIn("praf LIL", lil)
        self.assertEqual(lil.replace("LIL", "TEX"), tex)
        for path in files:
            parse(path.read_text(encoding="utf-8"))

    def test_calls_command_writes_one_wav_per_file(self) -> None:
        import shutil

        from enochaeon.cli import main

        if not shutil.which("espeak-ng") and not Path("/opt/homebrew/bin/espeak-ng").is_file():
            self.skipTest("espeak-ng is not installed")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "01-ol.txt"
            second = root / "02-iad.txt"
            first.write_text("Ol sonf.\n", encoding="utf-8")
            second.write_text("Iad balt\n", encoding="utf-8")
            self.assertEqual(main(["calls", str(root)]), 0)
            self.assertTrue((root / "01-ol.wav").is_file())
            self.assertTrue((root / "02-iad.wav").is_file())
            phonetic = (root / ".enochaeon" / "01-ol-phonetic.txt").read_text(encoding="utf-8")
            self.assertEqual(phonetic.strip(), "Q l s Q n f")
            self.assertEqual(main(["calls", str(root)]), 1)
            self.assertEqual(main(["calls", str(first), "--force"]), 0)
            self.assertEqual(main(["notes.txt", "--engine", "piper"]), 1)


if __name__ == "__main__":
    unittest.main()
