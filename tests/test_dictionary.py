"""The dictionary is the lexicon written out, and nothing is added to it."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from enochaeon.dictionary import (
    HTML_NAME,
    MARKDOWN_NAME,
    by_english,
    load_dictionary,
    render_html,
    render_markdown,
    write_dictionary,
)
from enochaeon.errors import EnochaeonError

ROOT = Path(__file__).resolve().parents[1]

LISTED = [
    {"root": "ZACAR", "variants": ["ZACARE", "zacar"], "pos": "verb", "english_glosses": ["move", "Come forth"]},
    {"root": "BALT", "variants": ["BALT"], "pos": "noun", "english_glosses": ["justice"]},
    {"root": "WAK", "variants": [], "english_glosses": []},
    {"root": "IAD", "variants": ["IAD"], "pos": "noun", "english_glosses": ["God", "justice", "god"]},
    {"root": "ARP", "variants": ["ARP"], "english_glosses": ["one, two | three <b>"]},
]


def _folder(directory: str, listed: object = LISTED) -> Path:
    folder = Path(directory)
    (folder / "lexicon.json").write_text(json.dumps(listed), encoding="utf-8")
    return folder


def _section(text: str, heading: str) -> str:
    """The lines of a Markdown file under one heading."""
    after = text.split(f"## {heading}\n", 1)[1]
    return after.split("\n## ", 1)[0]


class DictionaryTest(unittest.TestCase):
    def test_a_word_is_kept_as_the_lexicon_writes_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            entries = load_dictionary(_folder(directory))
        self.assertEqual([entry.word for entry in entries], ["ARP", "BALT", "IAD", "WAK", "ZACAR"])
        zacar = entries[-1]
        # The root is the word. A spelling that only repeats it is not another spelling.
        self.assertEqual(zacar.others, ("ZACARE",))
        self.assertEqual(zacar.part, "verb")
        self.assertEqual(zacar.glosses, ("move", "Come forth"))
        iad = entries[2]
        self.assertEqual(iad.others, ())
        # Capitals are kept, and the same gloss in other capitals is not listed twice.
        self.assertEqual(iad.glosses, ("God", "justice"))
        self.assertEqual(entries[3].glosses, ())

    def test_an_english_gloss_lists_every_word_that_has_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            entries = load_dictionary(_folder(directory))
        found = dict(by_english(entries))
        self.assertEqual(found["justice"], ("BALT", "IAD"))
        self.assertEqual(found["God"], ("IAD",))
        self.assertEqual(list(found), sorted(found, key=str.casefold))

    def test_the_markdown_has_both_directions_and_the_words_with_no_english(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = render_markdown(load_dictionary(_folder(directory)))
        to_english = _section(text, "Enochian to English")
        self.assertIn("| ZACAR | ZACARE | verb | move; Come forth |", to_english)
        self.assertNotIn("WAK", to_english)
        self.assertIn("| justice | BALT, IAD |", _section(text, "English to Enochian"))
        self.assertIn("| WAK |  |", _section(text, "Words with no English"))
        self.assertNotIn("BALT", _section(text, "Words with no English"))
        self.assertIn("5 words: 4 with English and 1 with none.", text)
        # A mark Markdown would read as its own is written so that it is not.
        self.assertIn("one, two \\| three \\<b\\>", text)

    def test_the_page_shows_each_word_in_enochian_letters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = render_html(load_dictionary(_folder(directory)))
        self.assertIn("@font-face", page)
        # Dee's alphabet has no W or K: the letters are those the translate page uses.
        self.assertIn('<td class="en">uuac</td><td class="word">WAK</td>', page)
        self.assertIn("one, two | three &lt;b&gt;", page)
        self.assertNotIn("<b>", page)
        self.assertIn("CC BY-SA 3.0", page)

    def test_how_a_word_is_said_is_not_shown(self) -> None:
        listed = [{"root": "IAD", "variants": ["IAD"], "english_glosses": ["God"], "dee_ipa": {"IAD": "/j.æ.d/"}}]
        with tempfile.TemporaryDirectory() as directory:
            entries = load_dictionary(_folder(directory, listed))
        self.assertNotIn("j.æ.d", render_markdown(entries) + render_html(entries))

    def test_a_lexicon_that_is_not_one_is_refused(self) -> None:
        wrong = (
            [{"root": "", "variants": [], "english_glosses": []}],
            [{"root": "IAD", "variants": ["IAD"]}],
            [{"root": "IAD", "variants": ["IAD"], "english_glosses": [3]}],
            [{"root": 3, "variants": [], "english_glosses": []}],
            {"root": "IAD"},
        )
        for listed in wrong:
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(EnochaeonError):
                    load_dictionary(_folder(directory, listed))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(EnochaeonError):
                load_dictionary(Path(directory))

    def test_both_files_are_written_beside_the_lexicon_and_not_replaced_unasked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = _folder(directory)
            markdown, page = write_dictionary(folder)
            self.assertEqual((markdown, page), (folder / MARKDOWN_NAME, folder / HTML_NAME))
            self.assertTrue(markdown.read_text(encoding="utf-8").startswith("# "))
            self.assertTrue(page.read_text(encoding="utf-8").startswith("<!DOCTYPE html>"))
            markdown.write_text("kept", encoding="utf-8")
            with self.assertRaises(EnochaeonError):
                write_dictionary(folder)
            self.assertEqual(markdown.read_text(encoding="utf-8"), "kept")
            write_dictionary(folder, force=True)
            self.assertNotEqual(markdown.read_text(encoding="utf-8"), "kept")

    def test_the_command_writes_the_dictionary(self) -> None:
        from enochaeon.cli import main

        with tempfile.TemporaryDirectory() as directory:
            folder = _folder(directory)
            self.assertEqual(main(["dictionary", str(folder)]), 0)
            self.assertTrue((folder / MARKDOWN_NAME).is_file())
            self.assertTrue((folder / HTML_NAME).is_file())
            self.assertEqual(main(["dictionary", str(folder)]), 1)
            self.assertEqual(main(["dictionary", str(folder), "--force"]), 0)
            self.assertEqual(main(["dictionary", str(folder / "missing")]), 1)

    def test_every_word_of_the_shipped_lexicon_is_in_the_dictionary_once(self) -> None:
        listed = json.loads((ROOT / "calls" / "lexicon.json").read_text(encoding="utf-8"))
        entries = load_dictionary(ROOT / "calls")
        self.assertEqual(sorted(entry.word for entry in entries), sorted(item["root"] for item in listed))
        text = render_markdown(entries)
        known = _section(text, "Enochian to English")
        unknown = _section(text, "Words with no English")
        for entry in entries:
            row = f"| {entry.word} |"
            self.assertEqual((known + unknown).count("\n" + row), 1, entry.word)
            self.assertEqual(("\n" + row) in known, bool(entry.glosses), entry.word)


if __name__ == "__main__":
    unittest.main()
