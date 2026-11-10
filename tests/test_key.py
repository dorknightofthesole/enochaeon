"""The letter key, without audio."""

from __future__ import annotations

import unittest

from enochaeon.alphabet import UNKNOWN, Alphabet
from enochaeon.errors import EnochaeonError
from enochaeon.match import fold_phones, phone_distance

PANGRAM = "The quick brown fox jumps over the lazy dog"


class KeyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.alphabet = Alphabet.load()

    def test_fox_letters(self) -> None:
        hebrew = self.alphabet.hebrew("fox")
        self.assertEqual(hebrew, "\u05e4\u05d5\u05b9\u05e7\u05e1")
        self.assertEqual(
            self.alphabet.enochian_names("fox"),
            ["Mals", "Vau", "Ger", "Pal"],
        )
        self.assertEqual(self.alphabet.enochian_text("fox"), "Mals Vau Ger Pal")
        self.assertEqual(self.alphabet.phonetic_text("fox"), "f'a s'i: r'i: s'a")
        self.assertEqual(self.alphabet.spelling("fox"), "PVQS")

    def test_trace_files_use_the_source_name(self) -> None:
        import tempfile
        from pathlib import Path

        from enochaeon.encode import write_traces

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "notes-test.txt"
            source.write_text("fox", encoding="utf-8")
            written = write_traces(source, "fox", self.alphabet)
            folder = Path(directory) / ".enochaeon"
            self.assertEqual(
                written,
                [
                    folder / "notes-test-hebrew.txt",
                    folder / "notes-test-enochian.txt",
                    folder / "notes-test-phonetic.txt",
                ],
            )
            self.assertEqual(
                (folder / "notes-test-hebrew.txt").read_text(encoding="utf-8"),
                "\u05e4\u05d5\u05b9\u05e7\u05e1\n",
            )
            self.assertEqual(
                (folder / "notes-test-enochian.txt").read_text(encoding="utf-8"),
                "Mals Vau Ger Pal\n",
            )
            self.assertEqual(
                (folder / "notes-test-phonetic.txt").read_text(encoding="utf-8"),
                "f'a s'i: r'i: s'a\n",
            )

    def test_hello_world_trace_files(self) -> None:
        import tempfile
        from pathlib import Path

        from enochaeon.encode import write_traces

        # Capitals fold. The space stays one space in every stage.
        # h e l l o / w o r l d
        hebrew = "\u05d7\u05d4\u05dc\u05dc\u05d5\u05b9 \u05d5\u05d5\u05d5\u05b9\u05e8\u05dc\u05d3\n"
        enochian = "Na-hath Graph Ur Ur Vau Vau Vau Don Ur Gal\n"
        # Both words are syllables. O counts as a vowel, so world is not letter-names.
        phonetic = "h'A: p'i: l'a l'a z'u: h'i: s'i: r'a l'a m'i:d\n"

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "hello-world.txt"
            source.write_text("Hello World\n", encoding="utf-8")
            written = write_traces(source, source.read_text(encoding="utf-8"), self.alphabet)
            folder = Path(directory) / ".enochaeon"
            self.assertEqual(
                written,
                [
                    folder / "hello-world-hebrew.txt",
                    folder / "hello-world-enochian.txt",
                    folder / "hello-world-phonetic.txt",
                ],
            )
            self.assertEqual((folder / "hello-world-hebrew.txt").read_text(encoding="utf-8"), hebrew)
            self.assertEqual(
                (folder / "hello-world-enochian.txt").read_text(encoding="utf-8"),
                enochian,
            )
            self.assertEqual(
                (folder / "hello-world-phonetic.txt").read_text(encoding="utf-8"),
                phonetic,
            )
            hello = phonetic.split(" h'i: ")[0]
            self.assertEqual(hello.count("l'a"), 2)
            self.assertNotIn("eI", hello)
            text, unknown = self.alphabet.decode_spoken(
                self.alphabet.canonical_stream("Hello World"),
                self.alphabet.form_labels(),
            )
            self.assertEqual(text, "hello world")
            self.assertFalse(unknown)

    def test_foks_is_the_same_cipher_as_fox(self) -> None:
        fox = self.alphabet.atom_ids("fox")
        foks = self.alphabet.atom_ids("foks")
        self.assertEqual(fox, foks)
        text, unknown = self.alphabet.decode_atoms(foks)
        self.assertEqual(text, "fox")
        self.assertFalse(unknown)

    def test_pangram_roundtrip(self) -> None:
        stream = self.alphabet.atom_ids(PANGRAM)
        text, unknown = self.alphabet.decode_atoms(stream)
        self.assertEqual(text, PANGRAM.lower())
        self.assertFalse(unknown)

    def test_tz_decodes_as_ts(self) -> None:
        text, unknown = self.alphabet.decode_atoms(self.alphabet.atom_ids("tz"))
        self.assertEqual(text, "ts")
        self.assertFalse(unknown)

    def test_fake_recognizer(self) -> None:
        heard = self.alphabet.canonical_stream("fox")
        text, unknown = self.alphabet.decode_spoken(heard, self.alphabet.form_labels())
        self.assertEqual(text, "fox")
        self.assertFalse(unknown)

    def test_open_vowel_is_long_and_closed_vowel_is_short(self) -> None:
        self.assertEqual(self.alphabet.phonetic_text("a"), "d'u:")
        self.assertEqual(self.alphabet.phonetic_text("at"), "b'i: t'a")
        self.assertEqual(self.alphabet.phonetic_text("the"), "t'i: p'u:")

    def test_unknown_character(self) -> None:
        with self.assertRaises(EnochaeonError) as caught:
            self.alphabet.parse("fox!")
        self.assertIn("'!'", str(caught.exception))
        self.assertIn("position 3", str(caught.exception))

    def test_failed_syllable_is_marked(self) -> None:
        text, unknown = self.alphabet.decode_atoms([("no-such-atom",)])
        self.assertEqual(text, UNKNOWN)
        self.assertTrue(unknown)

    def test_o_keeps_a_word_a_neologism(self) -> None:
        self.assertEqual(self.alphabet.phonetic_text("dog"), "m'i:d s'i: g'u:m")
        self.assertEqual(self.alphabet.phonetic_text("my"), "m'a h'u:")
        self.assertNotIn("v'i:", self.alphabet.phonetic_text("dog"))

    def test_folded_phones_ignore_length_and_a_color(self) -> None:
        self.assertEqual(fold_phones("ɑː m"), fold_phones("a m"))
        self.assertEqual(fold_phones("iː"), fold_phones("i"))
        self.assertEqual(fold_phones("ɕ i"), fold_phones("s i"))
        self.assertEqual(fold_phones("s."), fold_phones("s"))
        self.assertEqual(fold_phones("ɡ ʉ"), fold_phones("g u"))
        self.assertEqual(fold_phones("ɑu"), fold_phones("a"))
        self.assertEqual(fold_phones("x a"), fold_phones("h a"))
        self.assertNotEqual(fold_phones("s a"), fold_phones("z a"))

    def test_phone_distance_prefers_vowels(self) -> None:
        self.assertEqual(phone_distance(("p", "iː"), ("p", "iː")), 0)
        self.assertEqual(phone_distance(("p", "iː"), ("p", "ɪ")), 1)
        self.assertEqual(phone_distance(("p", "iː"), ("b", "iː")), 3)

    def test_a_listed_word_is_kept(self) -> None:
        from enochaeon.lexicon import choose, word_phones

        labels = self.alphabet.form_labels()
        phones = word_phones(self.alphabet, labels, "fox")
        self.assertIsNotNone(phones)
        heard = " ".join(phones or ())
        self.assertEqual(choose(heard, "fox", self.alphabet, labels), "fox")

    def test_an_unlisted_reading_can_take_a_nearby_listed_word(self) -> None:
        from enochaeon.lexicon import choose, word_phones

        labels = self.alphabet.form_labels()
        phones = word_phones(self.alphabet, labels, "quick")
        self.assertIsNotNone(phones)
        heard = " ".join(phones or ())
        self.assertEqual(choose(heard, "coicl", self.alphabet, labels), "quick")

    def test_a_distant_reading_stays_unlisted(self) -> None:
        from enochaeon.lexicon import choose

        labels = self.alphabet.form_labels()
        heard = " ".join(["b'a"] * 30)
        self.assertEqual(choose(heard, "qqqqqqqqqq", self.alphabet, labels), "qqqqqqqqqq")


class GapsTest(unittest.TestCase):
    def test_syllable_gap_stays_inside_the_word(self) -> None:
        from enochaeon.audio import SAMPLE_RATE, Gaps, segment_words, silence

        gaps = Gaps()
        tone = _tone(300)
        audio = _join(tone, silence(gaps.syllable_ms), tone, silence(gaps.word_ms), tone)
        words = segment_words(audio, SAMPLE_RATE, gaps)
        self.assertEqual([item for item in words if isinstance(item, str)], [" "])
        self.assertGreater(words[0].shape[0], words[2].shape[0])

    def test_a_stop_closure_does_not_split_a_syllable(self) -> None:
        from enochaeon.audio import SAMPLE_RATE, Gaps, segment_words, silence

        audio = _join(_tone(80), silence(40), _tone(120))
        words = segment_words(audio, SAMPLE_RATE, Gaps())
        self.assertEqual(len(words), 1)


def _tone(ms: int, sample_rate: int = 16_000) -> "object":
    import numpy as np

    count = int(sample_rate * ms / 1000)
    time = np.arange(count, dtype=np.float32)
    return (0.4 * np.sin(2 * np.pi * 220 * time / sample_rate)).astype(np.float32)


def _join(*pieces: object) -> object:
    import numpy as np

    return np.concatenate(list(pieces))


if __name__ == "__main__":
    unittest.main()
