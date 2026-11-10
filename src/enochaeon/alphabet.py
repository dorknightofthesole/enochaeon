"""The English–Hebrew–Enochian key.

Transliteration stops at letters. A row is an English spelling, a Hebrew
grapheme, and one or more Enochian letters. An English word is one breath of
in-word syllables, and ``o`` counts as a vowel. A vowel left open is long. A
vowel closed by a consonant is short. A call is separate: a call word with no
vowel is letter-names.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from enochaeon.errors import EnochaeonError

DATA_DIR = Path(__file__).resolve().parent / "data"
ALPHABET_PATH = DATA_DIR / "alphabet.json"
CALIBRATION_PATH = DATA_DIR / "calibration.json"
UNKNOWN = "�"
# V is English o. Its Enochian letter is Vau, and the call alphabet keeps V as
# a consonant of its own.
VOWELS = frozenset({"A", "E", "I", "O", "U", "V"})
# A comma stays in the line. A stop ends it. Marks with no sound are skipped.
PUNCT_BREAKS = {",": " ", ";": " ", ":": " ", "-": " ", ".": "\n", "!": "\n", "?": "\n"}
PUNCT_SKIP = set("()[]{}'’\"“”")


def syllable_forms(syllables: tuple[Atom, ...] | list[Atom]) -> list[tuple[Atom, str]]:
    """The in-word form of each letter: ``phone`` when it is short, ``long`` when it is open."""
    chosen: list[tuple[Atom, str]] = []
    for index, syllable in enumerate(syllables):
        if not syllable.vowel:
            chosen.append((syllable, "phone"))
            continue
        closed = False
        for later in syllables[index + 1 :]:
            if later.vowel:
                break
            closed = True
        chosen.append((syllable, "phone" if closed else "long"))
    return chosen


def pronounce_syllables(syllables: tuple[Atom, ...] | list[Atom], *, names: bool = True) -> str:
    """Speak one word in a single breath.

    A vowel with a consonant before the next vowel is short, and any other
    vowel is long. A doubled consonant is spoken twice. ``names`` is how a call
    reads a word that has no vowel: the letter-names, joined. An English word
    passes ``names=False`` and stays a run of in-word syllables.
    """
    if names and not any(syllable.vowel for syllable in syllables):
        return " ".join(syllable.name for syllable in syllables)
    return " ".join(
        syllable.phone if form == "phone" else syllable.long
        for syllable, form in syllable_forms(syllables)
    )


class TransliterationError(EnochaeonError):
    """A character in the document has no row in the key."""

    def __init__(self, character: str, position: int) -> None:
        self.character = character
        self.position = position
        super().__init__(f"Cannot transliterate {character!r} at position {position}")


@dataclass(frozen=True)
class Atom:
    id: str
    latin: str
    phone: str
    name: str
    long: str = ""

    @property
    def vowel(self) -> bool:
        return self.latin in VOWELS

    def forms(self) -> dict[str, str]:
        """The espeak strings this letter contributes to an English word.

        A vowel contributes its short and long sounds. A consonant contributes
        its in-word phone. Letter-names are not part of an English word, so
        they are not calibrated and not matched on the way back.
        """
        if self.vowel:
            return {"phone": self.phone, "long": self.long}
        return {"phone": self.phone}


@dataclass(frozen=True)
class Entry:
    en: str
    hebrew: str
    enochian: tuple[str, ...]
    atoms: tuple[str, ...]
    decode: bool


@dataclass(frozen=True)
class Word:
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class Gap:
    text: str


Segment = Word | Gap


class Alphabet:
    def __init__(self, atoms: dict[str, Atom], entries: tuple[Entry, ...]) -> None:
        self.atoms = atoms
        self.entries = entries
        self._encode = tuple(sorted(entries, key=lambda item: (-len(item.en), item.en)))
        decoding = [item for item in entries if item.decode]
        self._decode = tuple(sorted(decoding, key=lambda item: (-len(item.atoms), item.en)))
        self._validate()

    @classmethod
    def load(cls, path: Path | None = None) -> Alphabet:
        raw = json.loads((path or ALPHABET_PATH).read_text(encoding="utf-8"))
        atoms = {
            item["id"]: Atom(
                id=item["id"],
                latin=item["latin"],
                phone=item["phone"],
                name=item.get("name", ""),
                long=item.get("long", ""),
            )
            for item in raw["atoms"]
        }
        entries = tuple(
            Entry(
                en=item["en"],
                hebrew=item["hebrew"],
                enochian=tuple(item["enochian"]),
                atoms=tuple(item["atoms"]),
                decode=bool(item.get("decode", True)),
            )
            for item in raw["entries"]
        )
        return cls(atoms, entries)

    def _validate(self) -> None:
        seen_en: set[str] = set()
        seen_latin: dict[str, str] = {}
        seen_spoken: dict[str, str] = {}
        seen_decode: dict[tuple[str, ...], str] = {}
        used: set[str] = set()
        for entry in self.entries:
            if entry.en in seen_en:
                raise EnochaeonError(f"Duplicate English key {entry.en!r}")
            seen_en.add(entry.en)
            if not entry.atoms:
                raise EnochaeonError(f"{entry.en!r} has no Enochian spelling")
            for atom_id in entry.atoms:
                if atom_id not in self.atoms:
                    raise EnochaeonError(f"{entry.en!r} uses unknown atom {atom_id}")
                used.add(atom_id)
            if entry.decode:
                key = entry.atoms
                if key in seen_decode:
                    raise EnochaeonError(
                        f"{entry.en!r} and {seen_decode[key]!r} share the spelling {key}"
                    )
                seen_decode[key] = entry.en
        for atom in self.atoms.values():
            if atom.id not in used:
                raise EnochaeonError(f"Atom {atom.id} is never used")
            if not atom.latin or not atom.phone or not atom.name:
                raise EnochaeonError(f"Atom {atom.id} needs a spelling and a pronunciation")
            if atom.vowel and not atom.long:
                raise EnochaeonError(f"Vowel {atom.latin} needs a long sound")
            previous_latin = seen_latin.get(atom.latin)
            if previous_latin is not None:
                raise EnochaeonError(f"{previous_latin} and {atom.id} share the spelling {atom.latin}")
            seen_latin[atom.latin] = atom.id
            for spoken in set(atom.forms().values()):
                previous = seen_spoken.get(spoken)
                if previous is not None:
                    raise EnochaeonError(
                        f"Atoms {previous} and {atom.id} share the pronunciation {spoken}"
                    )
                seen_spoken[spoken] = atom.id

    def parse(self, text: str) -> list[Segment]:
        """Turn a document into words and the gaps between them.

        Runs of spaces become one space. A run of whitespace that contains a
        newline becomes one newline. A comma, semicolon, colon, or hyphen is a
        space. A period, question mark, or exclamation mark is a newline.
        Quotes and brackets are skipped. Letters are matched longest-first, so
        ``th`` is one row and ``x`` is the row for the two letters kuf and samekh.
        """
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        if cleaned.startswith("\ufeff"):
            cleaned = cleaned[1:]
        segments: list[Segment] = []
        index = 0
        length = len(cleaned)
        while index < length:
            if cleaned[index] in PUNCT_SKIP:
                index += 1
                continue
            if cleaned[index].isspace() or cleaned[index] in PUNCT_BREAKS:
                newline = False
                while index < length and (
                    cleaned[index].isspace()
                    or cleaned[index] in PUNCT_BREAKS
                    or cleaned[index] in PUNCT_SKIP
                ):
                    mark = cleaned[index]
                    newline = newline or mark == "\n" or PUNCT_BREAKS.get(mark) == "\n"
                    index += 1
                segments.append(Gap("\n" if newline else " "))
                continue
            word, index = self._match_word(cleaned, index)
            segments.append(word)
        return segments

    def _match_word(self, text: str, start: int) -> tuple[Word, int]:
        entries: list[Entry] = []
        index = start
        while index < len(text) and not text[index].isspace() and text[index] not in PUNCT_BREAKS and text[index] not in PUNCT_SKIP:
            matched = None
            folded = text[index:].lower()
            for entry in self._encode:
                if folded.startswith(entry.en):
                    matched = entry
                    break
            if matched is None:
                raise TransliterationError(text[index], index)
            entries.append(matched)
            index += len(matched.en)
        return Word(tuple(entries)), index

    def hebrew(self, text: str) -> str:
        parts: list[str] = []
        for segment in self.parse(text):
            if isinstance(segment, Gap):
                parts.append(segment.text)
            else:
                parts.extend(entry.hebrew for entry in segment.entries)
        return "".join(parts)

    def enochian_names(self, text: str) -> list[str]:
        names: list[str] = []
        for segment in self.parse(text):
            if isinstance(segment, Word):
                for entry in segment.entries:
                    names.extend(entry.enochian)
        return names

    def enochian_text(self, text: str) -> str:
        """Enochian letter names, with spaces between letters and the original gaps between words."""
        parts: list[str] = []
        for segment in self.parse(text):
            if isinstance(segment, Gap):
                parts.append(segment.text)
                continue
            names = [name for entry in segment.entries for name in entry.enochian]
            parts.append(" ".join(names))
        return "".join(parts)

    def phonetic_text(self, text: str) -> str:
        """One espeak string per English word, with the original gaps between words."""
        parts: list[str] = []
        for item in self.atom_ids(text):
            if isinstance(item, str):
                parts.append(item)
                continue
            parts.append(self.pronounce_atoms(tuple(self.atoms[atom_id] for atom_id in item)))
        return "".join(parts)

    def pronounce_atoms(self, atoms: tuple[Atom, ...]) -> str:
        """The espeak string for one English word, always in-word syllables."""
        return pronounce_syllables(atoms, names=False)

    def form_labels(self) -> dict[str, dict[str, str]]:
        """Espeak text of each form. A perfect hearing of those strings decodes."""
        return {atom.id: dict(atom.forms()) for atom in self.atoms.values()}

    def spelling(self, text: str) -> str:
        """Latin values of the Enochian letters, the string Leitch reads."""
        parts: list[str] = []
        for segment in self.parse(text):
            if isinstance(segment, Gap):
                parts.append(segment.text)
                continue
            for entry in segment.entries:
                for atom_id in entry.atoms:
                    parts.append(self.atoms[atom_id].latin)
        return "".join(parts)

    def atom_ids(self, text: str) -> list[tuple[str, ...] | str]:
        """Words as atom-id tuples, with ``' '`` or ``'\\n'`` between them."""
        stream: list[tuple[str, ...] | str] = []
        for segment in self.parse(text):
            if isinstance(segment, Gap):
                stream.append(segment.text)
            else:
                ids: list[str] = []
                for entry in segment.entries:
                    ids.extend(entry.atoms)
                stream.append(tuple(ids))
        return stream

    def decode_atoms(self, stream: list[tuple[str, ...] | str]) -> tuple[str, bool]:
        """Invert a stream of atom ids. The flag is true when a marker was used."""
        pieces: list[str] = []
        unknown = False
        for item in stream:
            if isinstance(item, str):
                pieces.append(item)
                continue
            word, failed = self._decode_word(item)
            pieces.append(word)
            unknown = unknown or failed
        return "".join(pieces), unknown

    def _decode_word(self, atoms: tuple[str, ...]) -> tuple[str, bool]:
        pieces: list[str] = []
        unknown = False
        index = 0
        while index < len(atoms):
            matched = None
            for entry in self._decode:
                size = len(entry.atoms)
                if atoms[index : index + size] == entry.atoms:
                    matched = entry
                    break
            if matched is None:
                pieces.append(UNKNOWN)
                unknown = True
                index += 1
                continue
            pieces.append(matched.en)
            index += len(matched.atoms)
        return "".join(pieces), unknown

    def canonical_stream(self, text: str) -> list[str]:
        """One pronounced string per word, with ``' '`` or ``'\\n'`` between them.

        A recognizer that heard every word exactly as espeak was told would
        return this.
        """
        stream: list[str] = []
        for item in self.atom_ids(text):
            if isinstance(item, str):
                stream.append(item)
            else:
                stream.append(self.pronounce_atoms(tuple(self.atoms[atom_id] for atom_id in item)))
        return stream

    def decode_spoken(self, stream: list[str], labels: dict[str, dict[str, str]]) -> tuple[str, bool]:
        """Align each heard word onto letter sounds, then invert the key."""
        from enochaeon.lexicon import choose
        from enochaeon.match import align_word

        converted: list[tuple[str, ...] | str] = []
        forced_unknown = False
        for item in stream:
            if item in (" ", "\n"):
                converted.append(item)
                continue
            atom_ids, _cost = align_word(item, labels)
            if not atom_ids or _cost >= 10**8:
                converted.append(("?",))
                forced_unknown = True
                continue
            word, failed = self._decode_word(atom_ids)

            if failed or UNKNOWN in word:
                converted.append(atom_ids)
                forced_unknown = True
                continue
            chosen = choose(item, word, self, labels)
            if chosen == word:
                converted.append(atom_ids)
                continue
            try:
                replacement = self.atom_ids(chosen)
            except TransliterationError:
                converted.append(atom_ids)
                continue
            if len(replacement) == 1 and not isinstance(replacement[0], str):
                converted.append(replacement[0])
            else:
                converted.append(atom_ids)
        text, unknown = self.decode_atoms(converted)
        return text, unknown or forced_unknown
