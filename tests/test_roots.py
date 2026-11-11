"""A phrase becomes Call words. The cipher is not on this path."""

from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from enochaeon.audio import read_comment
from enochaeon.config import CallVoice
from enochaeon.enochian import call_files, phonetic_text
from enochaeon.errors import EnochaeonError
from enochaeon.roots import Root, load_roots
from enochaeon.page import render_page
from enochaeon.translate import match_phrase, speak_file, speak_phrase


class _Near:
    """harmony is close to justice. Everything else is far."""

    def similarity(self, span: str, gloss: str) -> float:
        if span == "harmony" and gloss == "justice":
            return 0.8
        return 0.0


class _Far:
    def similarity(self, span: str, gloss: str) -> float:
        return 0.0


class _ExactOnly:
    def similarity(self, span: str, gloss: str) -> float:
        raise AssertionError(span)


def _roots() -> tuple[Root, ...]:
    return (
        Root("balt", "b a l t", ("01", "03", "16"), ("justice",)),
        Root("zacar", "z a k a r", ("07", "13"), ("move", "speak")),
        Root("ialprg", "i: a l p r g", ("02", "18"), ("burning", "fire")),
        Root("ca", "k a", ("01",), ("in",)),
        Root("holy", "h oU l i:", ("02",), ("holy one",)),
    )


class DictionaryTest(unittest.TestCase):
    def test_every_call_word_is_inventoried(self) -> None:
        folder = Path(__file__).resolve().parents[1] / "calls"
        roots = {root.spelling: root for root in load_roots(folder)}
        for path in call_files(folder):
            for word in path.read_text(encoding="utf-8").split():
                spelling = "".join(character for character in word.lower() if character.isalpha())
                if not spelling:
                    continue
                self.assertIn(spelling, roots)
                self.assertEqual(roots[spelling].phones, phonetic_text(spelling).strip())
        self.assertEqual(roots["balt"].glosses, ("justice", "righteousness", "judgment"))
        self.assertEqual(roots["iad"].glosses, ("god", "the divine"))
        self.assertEqual(roots["iad"].pos, "noun")
        self.assertEqual(roots["boalua"].pos, "verb")
        self.assertEqual(roots["gohus"].glosses, roots["goho"].glosses)
        self.assertEqual(roots["vorsg"].glosses, ("over you", "over"))
        self.assertEqual(roots["od"].glosses, ("and",))

    def test_a_lexicon_entry_holds_several_english_words(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "01.txt").write_text("Balt.\n", encoding="utf-8")
            (root / "lexicon.json").write_text(
                '[{"root": "BALT", "variants": ["BALTOH"], "english_glosses": ["justice", "fairness"]}]',
                encoding="utf-8",
            )
            glosses = {item.spelling: item.glosses for item in load_roots(root)}
            self.assertEqual(glosses["balt"], ("justice", "fairness"))
            self.assertEqual(glosses["baltoh"], ("justice", "fairness"))

    def test_a_missing_dictionary_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "01.txt").write_text("Ol sonf.\n", encoding="utf-8")
            with self.assertRaises(EnochaeonError):
                load_roots(root)


class PhraseTest(unittest.TestCase):
    def test_an_exact_gloss_does_not_ask_the_model(self) -> None:
        result = match_phrase("justice", _roots(), _ExactOnly())
        self.assertEqual(result.matched, (("justice", "balt"),))

    def test_unmatched_words_are_left_out(self) -> None:
        result = match_phrase("Speak justice into the fire.", _roots(), _Far())
        self.assertEqual(result.matched, (("speak", "zacar"), ("justice", "balt"), ("fire", "ialprg")))
        self.assertEqual(result.left_out, ("into", "the"))
        self.assertEqual(result.call_text, "zacar balt ialprg.")
        self.assertEqual(result.trace, "zacar balt [into] [the] ialprg.")

    def test_a_near_word_can_select_the_gloss(self) -> None:
        result = match_phrase("harmony", _roots(), _Near())
        self.assertEqual(result.matched, (("harmony", "balt"),))
        self.assertEqual(result.left_out, ())

    def test_a_score_under_the_line_is_left_out(self) -> None:
        class _Weak:
            def similarity(self, span: str, gloss: str) -> float:
                return 0.42

        result = match_phrase("noise", _roots(), _Weak())
        self.assertEqual(result.matched, ())
        self.assertEqual(result.left_out, ("noise",))
        self.assertEqual(result.trace, "[noise]")

    def test_the_same_part_of_speech_wins_over_a_higher_score(self) -> None:
        roots = (
            Root("boalua", "b", ("01",), ("worshipped",), "verb"),
            Root("iad", "i", ("01",), ("god", "the divine"), "noun"),
        )

        class _Scores:
            def similarity(self, span: str, gloss: str) -> float:
                return {"worshipped": 0.616, "the divine": 0.554, "god": 0.485}.get(gloss, 0.0)

        result = match_phrase("goddess", roots, _Scores(), lambda words: ["noun"] * len(words))
        self.assertEqual(result.matched, (("goddess", "iad"),))

    def test_a_different_part_wins_when_no_same_part_is_close(self) -> None:
        roots = (
            Root("boalua", "b", ("01",), ("worshipped",), "verb"),
            Root("iad", "i", ("01",), ("god",), "noun"),
        )

        class _Scores:
            def similarity(self, span: str, gloss: str) -> float:
                return {"worshipped": 0.616, "god": 0.2}.get(gloss, 0.0)

        result = match_phrase("goddess", roots, _Scores(), lambda words: ["noun"] * len(words))
        self.assertEqual(result.matched, (("goddess", "boalua"),))

    def test_an_unlisted_word_can_choose_the_nearest_entry(self) -> None:
        roots = (
            Root("iad", "i a d", ("01",), ("god",)),
            Root("balt", "b a l t", ("01",), ("justice",)),
        )

        class _Goddess:
            def similarity(self, span: str, gloss: str) -> float:
                if span == "goddess" and gloss == "god":
                    return 0.8
                return 0.0

        result = match_phrase("goddess", roots, _Goddess())
        self.assertEqual(result.matched, (("goddess", "iad"),))

    def test_a_near_span_stops_before_an_exact_gloss(self) -> None:
        roots = (
            Root("balt", "b a l t", ("01",), ("justice",)),
            Root("gohus", "g o h u s", ("03",), ("say",)),
        )

        class _CloserAsAPair:
            def similarity(self, span: str, gloss: str) -> float:
                if span == "speak justice" and gloss == "justice":
                    return 0.9
                if span == "speak" and gloss == "say":
                    return 0.5
                return 0.0

        result = match_phrase("speak justice", roots, _CloserAsAPair())
        self.assertEqual(result.matched, (("speak", "gohus"), ("justice", "balt")))

    def test_a_longer_near_span_can_still_win(self) -> None:
        roots = (Root("ialprg", "i a l", ("02",), ("burning",)),)

        class _Longer:
            def similarity(self, span: str, gloss: str) -> float:
                if gloss != "burning":
                    return 0.0
                if span == "holy flame":
                    return 0.8
                if span == "holy":
                    return 0.5
                return 0.0

        result = match_phrase("holy flame", roots, _Longer())
        self.assertEqual(result.matched, (("holy flame", "ialprg"),))

    def test_a_longer_exact_gloss_wins(self) -> None:
        result = match_phrase("holy one", _roots(), _ExactOnly())
        self.assertEqual(result.matched, (("holy one", "holy"),))

    def test_a_period_stays_between_call_words(self) -> None:
        result = match_phrase("justice. fire", _roots(), _ExactOnly())
        self.assertEqual(result.call_text, "balt. ialprg")

    def test_nothing_close_writes_no_wav(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "ritual.wav"
            with self.assertRaises(EnochaeonError):
                speak_phrase("into the", dest, _roots(), _Near(), CallVoice())
            self.assertFalse(dest.is_file())

    def test_a_bracketed_word_is_left_off_the_page(self) -> None:
        page = render_page("kavan [jay] w.", "ritual.wav")
        self.assertIn(">cauan<", page)
        self.assertNotIn("jay", page)
        self.assertNotIn("kavan w.", page)
        self.assertIn(">uu<", page)
        self.assertIn("background: white", page)

    def test_a_text_file_names_the_wav_and_writes_the_spoken_words(self) -> None:
        import shutil

        if not shutil.which("espeak-ng") and not Path("/opt/homebrew/bin/espeak-ng").is_file():
            self.skipTest("espeak-ng is not installed")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ritual.txt"
            source.write_text("justice.\n", encoding="utf-8")
            result, trace, dest = speak_file(source, _roots(), _ExactOnly(), CallVoice())
            self.assertEqual(result.call_text, "balt.")
            self.assertEqual(dest, source.with_suffix(".wav"))
            self.assertEqual(trace, source.parent / ".enochaeon" / "ritual-enochian.txt")
            self.assertEqual(trace.read_text(encoding="utf-8"), "balt.\n")
            self.assertFalse((source.parent / ".enochaeon" / "ritual-phonetic.txt").is_file())
            self.assertIsNone(read_comment(dest))
            self.assertGreater(dest.stat().st_size, 44)
            page = dest.with_suffix(".html").read_text(encoding="utf-8")
            self.assertIn("balt", page)
            self.assertIn("@font-face", page)
            self.assertIn("<audio controls", page)
            encoded = base64.b64encode(dest.read_bytes()).decode("ascii")
            self.assertIn(f'src="data:audio/wav;base64,{encoded}"', page)

    def test_an_existing_wav_is_left_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ritual.txt"
            source.write_text("justice\n", encoding="utf-8")
            dest = source.with_suffix(".wav")
            dest.write_bytes(b"kept")
            with self.assertRaises(EnochaeonError):
                speak_file(source, _roots(), _ExactOnly(), CallVoice())
            self.assertEqual(dest.read_bytes(), b"kept")
            self.assertFalse((source.parent / ".enochaeon" / "ritual-enochian.txt").is_file())
            self.assertFalse(dest.with_suffix(".html").is_file())

    def test_nothing_close_in_a_file_writes_no_trace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ritual.txt"
            source.write_text("into the\n", encoding="utf-8")
            with self.assertRaises(EnochaeonError):
                speak_file(source, _roots(), _Near(), CallVoice())
            self.assertFalse(source.with_suffix(".wav").is_file())
            self.assertFalse(source.with_suffix(".html").is_file())
            self.assertFalse((source.parent / ".enochaeon").exists())

    def test_the_wav_has_no_cipher_comment(self) -> None:
        import shutil

        if not shutil.which("espeak-ng") and not Path("/opt/homebrew/bin/espeak-ng").is_file():
            self.skipTest("espeak-ng is not installed")
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "ritual.wav"
            speak_phrase("justice", dest, _roots(), _ExactOnly(), CallVoice())
            self.assertIsNone(read_comment(dest))
            self.assertGreater(dest.stat().st_size, 44)


class CommandTest(unittest.TestCase):
    def test_translate_does_not_take_the_cipher_path(self) -> None:
        from enochaeon.cli import main

        self.assertEqual(main(["translate"]), 1)
        self.assertEqual(main(["translate", "missing-phrase.txt"]), 1)
        self.assertEqual(main(["notes.txt", "extra"]), 1)
        self.assertEqual(main(["translate", "justice", "--engine", "espeak"]), 1)


if __name__ == "__main__":
    unittest.main()
