"""Enochian call text is spoken as Enochian, not as English."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from enochaeon.alphabet import Alphabet
from enochaeon.enochian import call_files, parse, phonetic_text
from enochaeon.errors import EnochaeonError


class CallPronunciationTest(unittest.TestCase):
    def test_a_closed_vowel_stays_short(self) -> None:
        self.assertEqual(phonetic_text("Ol"), "Q l")
        self.assertEqual(phonetic_text("sonf"), "s Q n f")

    def test_a_leading_i_before_a_vowel_is_y(self) -> None:
        # Dee read Iad as Yad. The A is closed by D, so it stays short.
        self.assertEqual(phonetic_text("Iad"), "j a d")

    def test_an_open_vowel_is_long(self) -> None:
        self.assertEqual(phonetic_text("goho"), "g Q h oU")

    def test_a_word_with_no_vowel_is_letter_names(self) -> None:
        self.assertEqual(phonetic_text("ds"), "d'i: 'Es")

    def test_punctuation_breaks_the_line(self) -> None:
        self.assertEqual(phonetic_text("Ol sonf, goho. Iad"), "Q l s Q n f g Q h oU\nj a d")

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


if __name__ == "__main__":
    unittest.main()
