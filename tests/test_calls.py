"""Enochian call text is spoken as Enochian, not as English."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from enochaeon.alphabet import Alphabet
from enochaeon.audio import WORD_MS
from enochaeon.config import CallVoice, load_call_voice
from enochaeon.enochian import audible, call_files, call_gaps, parse, phonetic_text, render, spoken_text
from enochaeon.errors import EnochaeonError
from enochaeon.piper_voice import _word_ipa
from enochaeon.roots import load_readings
from enochaeon.word_ipa import as_written, piper_phones

ROOT = Path(__file__).resolve().parents[1]
NO_MODEL = "the Piper model the calls section of enochaeon.json names is not there"


def _shipped_voice() -> CallVoice:
    """The Call voice of the repository's enochaeon.json, with the model as a whole path."""
    voice = load_call_voice(ROOT / "enochaeon.json")
    return replace(voice, piper_voice=str(ROOT / voice.piper_voice))


def _model_present() -> bool:
    return Path(_shipped_voice().piper_voice).is_file()


class CallPronunciationTest(unittest.TestCase):
    def test_a_closed_vowel_stays_short(self) -> None:
        self.assertEqual(phonetic_text("Ol"), "Q l")
        self.assertEqual(phonetic_text("sonf"), "s Q n f")

    def test_an_unlisted_word_is_left_out(self) -> None:
        readings = {"iad": "/jɑːd/", "balt": "/bɑːlt/"}
        kept, dropped = audible("Iad Ol balt", readings)
        self.assertEqual(dropped, ("ol",))
        self.assertEqual(kept, audible("Iad balt", readings)[0])
        self.assertEqual(spoken_text(kept), "iad balt")
        self.assertEqual(audible("Ol", {}), ([], ("ol",)))

    @unittest.skipUnless(_model_present(), NO_MODEL)
    def test_a_text_with_no_listed_word_is_silence(self) -> None:
        quiet = render("Ol", voice=_shipped_voice(), readings={})
        self.assertLess(float(np.max(np.abs(quiet))), 0.01)

    def test_a_call_is_not_spoken_without_a_piper_model(self) -> None:
        with self.assertRaises(EnochaeonError) as caught:
            render("Iad", voice=CallVoice(), readings={"iad": "/jæd/"})
        self.assertIn("calls.piper.voice", str(caught.exception))

    def test_a_listed_word_is_spoken_from_the_lexicon(self) -> None:
        self.assertEqual(piper_phones("/jɑːd/"), "jɑːd")
        self.assertEqual(piper_phones("/ˈɡoʊ.hoʊ/"), "ɡˈoʊhoʊ")
        self.assertEqual(piper_phones("/bɑːl.tə/"), "bɑːltə")
        self.assertEqual(piper_phones("/ˈɑr/"), "ˈɑɹ")
        self.assertEqual(load_readings("dee_ipa")["iad"], "/j.æ.d/")
        self.assertNotIn("iad", load_readings("golden_dawn_ipa"))
        self.assertEqual(load_readings("dee_ipa")["balzizras"], "/b.æ.l.z.ɪ.z.r.æ.s/")
        # What Piper is given for the word is the reading the caller handed over.
        self.assertEqual(_word_ipa(parse("Iad")[0], {"iad": "/jɑːd/"}, CallVoice()), "jɑːd")

    def test_a_voice_with_its_own_lexicon_field_is_given_it_as_written(self) -> None:
        word = parse("Iad")[0]
        own = CallVoice(piper_ipa="some_field", word_end=".")
        # Nothing is added but the end mark the config gives.
        self.assertEqual(_word_ipa(word, {"iad": "/jˈaːd/"}, own), "jˈaːd.")
        self.assertEqual(_word_ipa(word, {"iad": "/jæd/"}, replace(own, word_end="")), "jæd")
        with self.assertRaises(EnochaeonError):
            _word_ipa(word, {"iad": "jˈaːd"}, own)
        # With no field of its own, Piper is given the reading turned into its letters.
        self.assertEqual(_word_ipa(word, {"iad": "/j.æ.d/"}, CallVoice()), "jæd")

    def test_the_shipped_voice_field_has_every_call_spelling(self) -> None:
        root = Path(__file__).resolve().parents[1]
        voice = load_call_voice(root / "enochaeon.json")
        self.assertTrue(voice.piper_ipa)
        own = load_readings(voice.piper_ipa, root / "calls")
        self.assertEqual(set(own), set(load_readings("dee_ipa", root / "calls")))
        for reading in own.values():
            as_written(reading)
        # The one string that was judged by ear.
        self.assertEqual(own["iad"], "/jˈaːd/")

    def test_a_leading_i_before_a_vowel_is_y(self) -> None:
        # Dee read Iad as Yad. The A is closed by D, so it stays short.
        self.assertEqual(phonetic_text("Iad"), "j a d")

    def test_an_open_vowel_is_long(self) -> None:
        self.assertEqual(phonetic_text("goho"), "g Q h oU")

    def test_a_word_with_no_vowel_is_letter_names(self) -> None:
        self.assertEqual(phonetic_text("ds"), "d'i: 'Es")

    def test_punctuation_breaks_the_line(self) -> None:
        self.assertEqual(phonetic_text("Ol sonf, goho. Iad"), "Q l s Q n f g Q h oU\nj a d")

    def test_the_shipped_config_names_the_call_voice(self) -> None:
        voice = load_call_voice(ROOT / "enochaeon.json")
        self.assertEqual(voice.ipa, "dee_ipa")
        self.assertGreater(voice.length_scale, 1)
        self.assertEqual(voice.word_ms, 200)
        self.assertIn("john", voice.piper_voice)

    def test_a_piper_breath_can_be_shorter(self) -> None:
        shorter = CallVoice(word_ms=400)
        self.assertEqual(call_gaps(shorter).word_ms, 400)
        self.assertEqual(call_gaps(shorter).nl_ms, 1000)
        self.assertEqual(call_gaps(CallVoice()).word_ms, WORD_MS)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "enochaeon.json"
            path.write_text(
                '{"calls": {"piper": {"word_ms": 400}}}\n',
                encoding="utf-8",
            )
            self.assertEqual(load_call_voice(path).word_ms, 400)
            path.write_text('{"calls": {"piper": {"word_ms": 0}}}\n', encoding="utf-8")
            with self.assertRaises(EnochaeonError):
                load_call_voice(path)
            path.write_text('{"calls": {"ipa": "laycock"}}\n', encoding="utf-8")
            with self.assertRaises(EnochaeonError):
                load_call_voice(path)

    def test_the_config_names_the_lexicon_field_and_the_word_end(self) -> None:
        self.assertEqual(CallVoice().piper_ipa, "")
        self.assertEqual(CallVoice().word_end, "")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "enochaeon.json"
            path.write_text('{"calls": {"piper": {"ipa": "for_a_voice", "word_end": "."}}}\n', encoding="utf-8")
            voice = load_call_voice(path)
            self.assertEqual((voice.piper_ipa, voice.word_end), ("for_a_voice", "."))
            for wrong in ('{"ipa": "dee_ipa"}', '{"ipa": 3}', '{"word_end": 3}'):
                path.write_text('{"calls": {"piper": %s}}\n' % wrong, encoding="utf-8")
                with self.assertRaises(EnochaeonError):
                    load_call_voice(path)

    def test_no_config_file_names_no_piper_model(self) -> None:
        voice = load_call_voice(Path("/no/such/enochaeon.json"))
        self.assertEqual(voice, CallVoice())
        self.assertEqual(voice.piper_voice, "")

    def test_a_call_is_not_the_english_cipher(self) -> None:
        english = Alphabet.load().phonetic_text("ol")
        self.assertNotEqual(phonetic_text("ol"), english)

    def test_an_unknown_mark_names_itself(self) -> None:
        with self.assertRaises(EnochaeonError) as caught:
            phonetic_text("Ol@")
        self.assertIn("'@'", str(caught.exception))
        self.assertIn("line 1", str(caught.exception))

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

    def test_every_call_file_has_the_words_of_its_sloane_record(self) -> None:
        # This checks the files against calls/sloane/, and that each word there
        # points at journal words that exist in calls/journal/. It does not
        # check the reading in calls/sloane/ against Dee's manuscript.
        root = Path(__file__).resolve().parents[1] / "calls"

        def words_of(path: Path) -> list[str]:
            return [word.lower() for word in re.findall(r"[A-Za-z]+", path.read_text(encoding="utf-8"))]

        def record(folder: str, stem: str) -> dict:
            return json.loads((root / folder / f"{stem}.json").read_text(encoding="utf-8"))

        def check(entries: list[dict], journal: list[dict]) -> list[str]:
            for entry in entries:
                self.assertIn(entry["status"], {"read", "unsure"})
                for number in entry["journal"]:
                    self.assertTrue(1 <= number <= len(journal))
            return [entry["letters"].lower() for entry in entries]

        for number in range(1, 19):
            stem = f"{number:02d}"
            words = check(record("sloane", stem)["words"], record("journal", stem)["words"])
            self.assertEqual(words_of(root / f"{stem}.txt"), words)
        aethyrs = record("sloane", "aethyrs")
        journal = record("journal", "aethyrs")
        words = check(aethyrs["words"], journal["words"])
        names = check(aethyrs["names"], journal["names"])
        self.assertEqual(len(names), 30)
        for index, name in enumerate(names):
            expected = list(words)
            expected[aethyrs["name_word"]] = name
            self.assertEqual(words_of(root / f"{19 + index}-{name}.txt"), expected)

    def test_calls_command_writes_one_wav_per_file(self) -> None:
        from enochaeon.cli import main

        # The command reads enochaeon.json in the directory it is run from.
        if not Path(load_call_voice().piper_voice).is_file():
            self.skipTest(NO_MODEL)
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


if __name__ == "__main__":
    unittest.main()
