"""Speak text with the cipher's voice and read it back. Requires the Piper model enochaeon.json names and the phone model."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from enochaeon.cli import main
from enochaeon.config import load_cipher_voice
from enochaeon.errors import EnochaeonError

# Example sentences. The implementation must not know these strings.
FIXTURE = (
    "The quick brown fox jumps over the lazy dog",
    "Hello world",
    "The black cat kept the key",
    "She sells fish and chips",
)
# A text whose lines end in three ways: a line break, a full stop, and an empty line.
LINES = "The owl and the cat\nwent to sea. In a boat,\n\nthey took some honey\n"


def _voice_present() -> bool:
    try:
        return Path(load_cipher_voice().model).is_file()
    except EnochaeonError:
        return False


@unittest.skipUnless(_voice_present(), "the Piper model the cipher section of enochaeon.json names is not there")
class AudioRoundtripTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        status = main(["calibrate"])
        if status != 0:
            raise AssertionError("calibration could not tell every letter sound apart")

    def test_fox_survives_speech(self) -> None:
        from enochaeon.audio import read_comment

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fox.txt"
            source.write_text("fox", encoding="utf-8")
            self.assertEqual(main([str(source)]), 0)
            wav = root / "fox.wav"
            self.assertTrue(wav.is_file())
            hidden = root / ".enochaeon"
            self.assertEqual(
                (hidden / "fox-hebrew.txt").read_text(encoding="utf-8").strip(),
                "\u05e4\u05d5\u05b9\u05e7\u05e1",
            )
            self.assertEqual(
                (hidden / "fox-enochian.txt").read_text(encoding="utf-8").strip(),
                "Mals Vau Ger Pal",
            )
            self.assertEqual(
                (hidden / "fox-phonetic.txt").read_text(encoding="utf-8").strip(),
                "f'a s'i: r'i: s'a",
            )
            comment = read_comment(wav)
            self.assertTrue(comment.startswith("enochaeon;v=2"))
            self.assertNotIn("fox", comment)
            self.assertEqual(main([str(wav)]), 0)
            restored = (root / "fox.decoded.txt").read_text(encoding="utf-8")
            self.assertEqual(restored.strip(), "fox")

    def test_hello_world_survives_speech(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "hello-world.txt"
            source.write_text("Hello World\n", encoding="utf-8")
            self.assertEqual(main([str(source)]), 0)
            hidden = root / ".enochaeon"
            phonetic = (hidden / "hello-world-phonetic.txt").read_text(encoding="utf-8").strip()
            self.assertEqual(phonetic, "h'A: p'i: l'a l'a z'u: h'i: s'i: r'a l'a m'i:d")
            hello, world = phonetic.split(" z'u: ", 1)
            self.assertEqual(hello.count("l'a"), 2)
            self.assertEqual(world, "h'i: s'i: r'a l'a m'i:d")
            self.assertEqual(main([str(root / "hello-world.wav")]), 0)
            restored = (root / "hello-world.decoded.txt").read_text(encoding="utf-8")
            self.assertEqual(restored.strip(), "hello world")

    def test_every_word_comes_back(self) -> None:
        from enochaeon.alphabet import Alphabet
        from enochaeon.audio import SAMPLE_RATE
        from enochaeon.cipher_voice import Speaker, mark_of
        from enochaeon.decode import decode_audio, require_calibration
        from enochaeon.encode import render

        alphabet = Alphabet.load()
        voice = load_cipher_voice()
        speaker = Speaker(voice, alphabet)
        calibration = require_calibration(alphabet)
        mark = mark_of(voice, speaker.name)
        for line in FIXTURE:
            # What the key gives back with no audio. Speech and hearing must lose none of it.
            expected, _ = alphabet.decode_atoms(alphabet.atom_ids(line))
            decoded, unknown = decode_audio(
                render(line, alphabet, voice, speaker), SAMPLE_RATE, alphabet, calibration, mark
            )
            self.assertEqual(decoded, expected)
            self.assertFalse(unknown)

    def test_line_breaks_come_back(self) -> None:
        from enochaeon.alphabet import Alphabet

        alphabet = Alphabet.load()
        # What the key gives back with no audio: the same words on the same lines.
        expected, _ = alphabet.decode_atoms(alphabet.atom_ids(LINES))
        self.assertEqual(expected.strip().count("\n"), 3)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "lines.txt"
            source.write_text(LINES, encoding="utf-8")
            self.assertEqual(main([str(source)]), 0)
            self.assertEqual(main([str(root / "lines.wav")]), 0)
            restored = (root / "lines.decoded.txt").read_text(encoding="utf-8")
            self.assertEqual(restored.strip(), expected.strip())

    def test_a_wav_with_no_mark_is_still_read(self) -> None:
        from enochaeon.audio import read_wav, write_wav

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fox.txt"
            source.write_text("fox", encoding="utf-8")
            self.assertEqual(main([str(source)]), 0)
            audio, sample_rate = read_wav(root / "fox.wav")
            bare = root / "bare.wav"
            write_wav(bare, audio, sample_rate)
            self.assertEqual(main([str(bare)]), 0)
            self.assertEqual((root / "bare.decoded.txt").read_text(encoding="utf-8").strip(), "fox")

    def test_a_wav_of_the_earlier_cipher_or_of_a_call_is_refused(self) -> None:
        from enochaeon.audio import Gaps, silence, write_wav

        with tempfile.TemporaryDirectory() as directory:
            wav = Path(directory) / "earlier.wav"
            write_wav(wav, silence(200), comment=Gaps().comment())
            self.assertEqual(main([str(wav)]), 1)
            self.assertFalse((Path(directory) / "earlier.decoded.txt").exists())

    def test_a_wav_of_another_voice_is_refused(self) -> None:
        from enochaeon.audio import silence, write_wav
        from enochaeon.cipher_voice import mark_of

        with tempfile.TemporaryDirectory() as directory:
            wav = Path(directory) / "other.wav"
            write_wav(wav, silence(200), comment=mark_of(load_cipher_voice(), "another-voice").comment())
            self.assertEqual(main([str(wav)]), 1)
            self.assertFalse((Path(directory) / "other.decoded.txt").exists())


if __name__ == "__main__":
    unittest.main()
