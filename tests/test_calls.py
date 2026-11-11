"""Enochian call text is spoken as Enochian, not as English."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet
from enochaeon.audio import WORD_MS
from enochaeon.config import CallVoice, load_call_voice
from enochaeon.enochian import call_files, call_gaps, parse, phonetic_text, render
from enochaeon.errors import EnochaeonError
from enochaeon.piper_voice import ipa_of
from enochaeon.roots import load_readings
from enochaeon.synthesize import speak
from enochaeon.word_ipa import espeak_phones, piper_phones


class CallPronunciationTest(unittest.TestCase):
    def test_a_closed_vowel_stays_short(self) -> None:
        self.assertEqual(phonetic_text("Ol"), "Q l")
        self.assertEqual(phonetic_text("sonf"), "s Q n f")

    def test_an_unlisted_word_is_left_out(self) -> None:
        readings = {"iad": "/jɑːd/", "balt": "/bɑːlt/"}
        kept = render("Iad balt", readings=readings)
        self.assertTrue(np.array_equal(render("Iad Ol balt", readings=readings), kept))
        quiet = render("Ol", readings={})
        self.assertLess(float(np.max(np.abs(quiet))), 0.01)

    def test_a_listed_word_is_spoken_from_the_lexicon(self) -> None:
        self.assertEqual(espeak_phones("/jɑːd/"), "j A: d")
        self.assertEqual(espeak_phones("/ˈɡoʊ.hoʊ/"), "g 'oU h oU")
        self.assertEqual(piper_phones("/jɑːd/"), "jɑːd")
        self.assertEqual(piper_phones("/ˈɡoʊ.hoʊ/"), "ɡˈoʊhoʊ")
        self.assertEqual(piper_phones("/bɑːl.tə/"), "bɑːltə")
        self.assertEqual(load_readings("dee_ipa")["iad"], "/jɑːd/")
        self.assertEqual(load_readings("golden_dawn_ipa")["iad"], "/iː.ɑːd/")
        self.assertEqual(load_readings("dee_ipa")["balzizras"], "/bɑːlt/")
        self.assertTrue(np.array_equal(render("Iad", readings={"iad": "/jɑːd/"}), speak("j A: d")))
        self.assertTrue(np.array_equal(render("Iad"), speak("j A: d")))

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
        self.assertEqual(voice.ipa, "dee_ipa")
        self.assertGreater(voice.length_scale, 1)
        self.assertEqual(voice.word_ms, 200)
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
            path.write_text('{"calls": {"ipa": "laycock"}}\n', encoding="utf-8")
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

    def test_the_call_files_are_present(self) -> None:
        root = Path(__file__).resolve().parents[1] / "calls"
        files = call_files(root)
        self.assertEqual(len(files), 50)
        names = {path.name for path in files}
        self.assertIn("49.txt", names)
        self.assertIn("50.txt", names)
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
            self.assertFalse((root / ".enochaeon").exists())
            self.assertEqual(main(["calls", str(root)]), 1)
            self.assertEqual(main(["calls", str(first), "--force"]), 0)
            self.assertEqual(main(["notes.txt", "--engine", "piper"]), 1)


if __name__ == "__main__":
    unittest.main()
