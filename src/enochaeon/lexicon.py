"""Pick a listed word when a reading is not one and the sound is close.

The list is American SCOWL, size 50: the common band and its inflections.
A reading that is already in the list is kept. Anything else is replaced
only when a listed word is within a few phone edits of what was heard.
"""

from __future__ import annotations

from pathlib import Path

from enochaeon.alphabet import DATA_DIR, UNKNOWN, Alphabet, TransliterationError, syllable_forms
from enochaeon.match import phone_distance

WORDS_PATH = DATA_DIR / "words.txt"
# Three vowel swaps, the distance between a letter and its onset neighbor.
MARGIN = 3
_LENGTH_WINDOW = 4

_CACHE: dict[tuple[tuple[str, tuple[tuple[str, str], ...]], ...], "Lexicon"] = {}


class Lexicon:
    def __init__(
        self,
        words: frozenset[str],
        by_length: dict[int, tuple[tuple[str, tuple[str, ...]], ...]],
    ) -> None:
        self.words = words
        self._by_length = by_length

    def near(self, length: int) -> tuple[tuple[str, tuple[str, ...]], ...]:
        found: list[tuple[str, tuple[str, ...]]] = []
        for size in range(max(1, length - _LENGTH_WINDOW), length + _LENGTH_WINDOW + 1):
            found.extend(self._by_length.get(size, ()))
        return tuple(found)


def load_words(path: Path | None = None) -> frozenset[str]:
    source = path or WORDS_PATH
    words = set()
    for line in source.read_text(encoding="utf-8").splitlines():
        word = line.strip().lower()
        if word.isascii() and word.isalpha():
            words.add(word)
    return frozenset(words)


def lexicon_for(
    alphabet: Alphabet,
    labels: dict[str, dict[str, str]],
) -> Lexicon:
    """Listed words and the calibrated phones of each one. Built once per label set."""
    signature = tuple(
        (atom_id, tuple(sorted(forms.items())))
        for atom_id, forms in sorted(labels.items())
    )
    cached = _CACHE.get(signature)
    if cached is not None:
        return cached
    by_length: dict[int, list[tuple[str, tuple[str, ...]]]] = {}
    words = load_words()
    for word in words:
        phones = word_phones(alphabet, labels, word)
        if phones:
            by_length.setdefault(len(phones), []).append((word, phones))
    frozen = {length: tuple(entries) for length, entries in by_length.items()}
    cached = Lexicon(words, frozen)
    _CACHE[signature] = cached
    return cached


def word_phones(
    alphabet: Alphabet,
    labels: dict[str, dict[str, str]],
    word: str,
) -> tuple[str, ...] | None:
    """What the matcher hears for one word, using the same forms the speaker uses."""
    if UNKNOWN in word:
        return None
    try:
        stream = alphabet.atom_ids(word, strict=True)
    except TransliterationError:
        return None
    if len(stream) != 1 or isinstance(stream[0], str):
        return None
    phones: list[str] = []
    atoms = tuple(alphabet.atoms[atom_id] for atom_id in stream[0])
    for atom, form in syllable_forms(atoms):
        heard = labels.get(atom.id, {}).get(form, "")
        if not heard:
            return None
        phones.extend(heard.split())
    return tuple(phones)


def choose(
    heard: str,
    raw: str,
    alphabet: Alphabet,
    labels: dict[str, dict[str, str]],
) -> str:
    """Keep a listed reading. Replace an unlisted one when a listed word is close."""
    if not raw.isascii() or not raw.isalpha():
        return raw
    listed = lexicon_for(alphabet, labels)
    if raw in listed.words:
        return raw
    raw_phones = word_phones(alphabet, labels, raw)
    heard_phones = tuple(heard.split())
    if not raw_phones or not heard_phones:
        return raw
    limit = phone_distance(heard_phones, raw_phones) + MARGIN
    best: tuple[int, int, str] | None = None
    for word, phones in listed.near(len(heard_phones)):
        cost = phone_distance(heard_phones, phones)
        if cost > limit:
            continue
        key = (cost, len(word), word)
        if best is None or key < best:
            best = key
    if best is None:
        return raw
    return best[2]
