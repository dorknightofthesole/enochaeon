"""Speak text and read it back. Requires espeak-ng and the phone model."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from enochaeon.cli import main

# Example sentences. The implementation must not know these strings.
FIXTURE = (
    "The quick brown fox jumps over the lazy dog",
    "Hello world",
    "The black cat kept the key",
    "She sells fish and chips",
)
# Word positions this build already recovers. Losing one fails the test.
# Add a position only after a change recovers that word.
RECOVERED = frozenset({
    (0, 0),
    (0, 1),
    (0, 3),
    (0, 4),
    (0, 6),
    (0, 8),
    (1, 0),
    (1, 1),
    (2, 0),
    (2, 3),
    (2, 4),
    (3, 0),
    (3, 1),
    (3, 3),
})
# Phone distance from what was heard to the source word. A later change fails
# when any of these rises, including a word that was already wrong.
DISTANCE = {
    (0, 0): 1,
    (0, 1): 4,
    (0, 2): 6,
    (0, 3): 0,
    (0, 4): 0,
    (0, 5): 6,
    (0, 6): 1,
    (0, 7): 7,
    (0, 8): 2,
    (1, 0): 4,
    (1, 1): 1,
    (2, 0): 1,
    (2, 1): 3,
    (2, 2): 6,
    (2, 3): 3,
    (2, 4): 0,
    (2, 5): 7,
    (3, 0): 1,
    (3, 1): 0,
    (3, 2): 4,
    (3, 3): 1,
    (3, 4): 3,
}


def _espeak_present() -> bool:
    if shutil.which("espeak-ng"):
        return True
    return Path("/opt/homebrew/bin/espeak-ng").is_file()


@unittest.skipUnless(_espeak_present(), "espeak-ng is not installed")
class AudioRoundtripTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        status = main(["calibrate"])
        if status != 0:
            raise AssertionError("calibration reported two syllables as the same sound")

    def test_fox_survives_speech(self) -> None:
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
            comment = wav.read_bytes()
            self.assertIn(b"enochaeon;v=1", comment)
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

    def test_recovered_words_stay_recovered(self) -> None:
        from enochaeon.alphabet import Alphabet
        from enochaeon.audio import Gaps
        from enochaeon.decode import decode_audio, require_calibration
        from enochaeon.encode import render

        alphabet = Alphabet.load()
        labels = require_calibration(alphabet)
        lost: list[str] = []
        for line_index, line in enumerate(FIXTURE):
            decoded, _unknown = decode_audio(render(line, alphabet), 16000, alphabet, labels, Gaps())
            got = decoded.lower().split()
            for word_index, word in enumerate(line.lower().split()):
                if (line_index, word_index) not in RECOVERED:
                    continue
                heard = got[word_index] if word_index < len(got) else ""
                if heard != word:
                    lost.append(f"{word!r} came back as {heard!r}")
        self.assertEqual(lost, [])

    def test_word_distance_does_not_get_worse(self) -> None:
        from enochaeon.alphabet import Alphabet
        from enochaeon.audio import Gaps, segment_words
        from enochaeon.decode import require_calibration
        from enochaeon.encode import render
        from enochaeon.lexicon import word_phones
        from enochaeon.match import phone_distance
        from enochaeon.recognize import transcribe

        alphabet = Alphabet.load()
        labels = require_calibration(alphabet)
        worse: list[str] = []
        for line_index, line in enumerate(FIXTURE):
            heard_words = [
                transcribe(piece)
                for piece in segment_words(render(line, alphabet), 16000, Gaps())
                if not isinstance(piece, str)
            ]
            for word_index, word in enumerate(line.lower().split()):
                ceiling = DISTANCE[(line_index, word_index)]
                heard = heard_words[word_index] if word_index < len(heard_words) else ""
                phones = word_phones(alphabet, labels, word)
                distance = phone_distance(tuple(heard.split()), phones) if phones else 10**6
                if distance > ceiling:
                    worse.append(f"{word} distance {distance} exceeded {ceiling}")
        self.assertEqual(worse, [])


if __name__ == "__main__":
    unittest.main()
