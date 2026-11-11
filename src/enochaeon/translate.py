"""Speak an English text file as the nearest dictionary words.

An exact English word wins. Otherwise a local embedding ranks the English
words listed in calls/lexicon.json. This does not cipher the file or read
the wav back. The wav takes the source file's name, and the spoken spellings
are written beside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from enochaeon.audio import write_wav
from enochaeon.config import CallVoice
from enochaeon.enochian import _readings, audible, render, spoken_text
from enochaeon.errors import EnochaeonError
from enochaeon.roots import Root

# Cosine similarity at or above this line may speak a Call word.
# A nearer gloss under the line is left unmatched.
SIMILARITY = 0.50
_MAX_SPAN = 4
_MARKS = {",": ",", ";": ";", ":": ":", ".": ".", "!": ".", "?": "."}
_MODEL = "all-MiniLM-L6-v2"
_PARTS = {
    "NN": "noun",
    "NNS": "noun",
    "NNP": "noun",
    "NNPS": "noun",
    "VB": "verb",
    "VBD": "verb",
    "VBG": "verb",
    "VBN": "verb",
    "VBP": "verb",
    "VBZ": "verb",
    "MD": "verb",
    "JJ": "adjective",
    "JJR": "adjective",
    "JJS": "adjective",
    "RB": "adverb",
    "RBR": "adverb",
    "RBS": "adverb",
    "IN": "preposition",
    "TO": "preposition",
    "CC": "conjunction",
    "PRP": "pronoun",
    "PRP$": "pronoun",
    "WP": "pronoun",
    "WP$": "pronoun",
    "UH": "interjection",
}


@dataclass(frozen=True)
class Translation:
    """What was spoken, and the English that had no close gloss.

    ``call_text`` is the spellings the wav speaks. ``trace`` is the same line
    with each unmatched English word kept in brackets.
    """

    call_text: str
    matched: tuple[tuple[str, str], ...]
    left_out: tuple[str, ...]
    trace: str


def _public_model(sentence_transformer: type) -> object:
    """Load the public model without a saved Hugging Face login.

    An expired login is sent on later file lookups unless implicit tokens are off.
    """
    import huggingface_hub.constants as hf_constants

    previous = hf_constants.HF_HUB_DISABLE_IMPLICIT_TOKEN
    hf_constants.HF_HUB_DISABLE_IMPLICIT_TOKEN = True
    try:
        return sentence_transformer(_MODEL, token=False)
    finally:
        hf_constants.HF_HUB_DISABLE_IMPLICIT_TOKEN = previous


class MiniLM:
    """Ranks glosses the dictionary already has. It does not invent spellings."""

    def __init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EnochaeonError(
                "Translating a phrase needs sentence-transformers. "
                "It is installed with enochaeon."
            ) from exc
        try:
            self._model = _public_model(SentenceTransformer)
        except Exception as exc:
            raise EnochaeonError(f"Could not load the phrase model {_MODEL}. {exc}") from exc
        self._vectors: dict[str, np.ndarray] = {}

    def similarity(self, span: str, gloss: str) -> float:
        return float(np.dot(self._vector(span), self._vector(gloss)))

    def _vector(self, text: str) -> np.ndarray:
        cached = self._vectors.get(text)
        if cached is None:
            cached = np.asarray(self._model.encode(text, normalize_embeddings=True), dtype=np.float32)
            self._vectors[text] = cached
        return cached


def match_phrase(
    phrase: str,
    roots: tuple[Root, ...] | list[Root],
    scorer: object,
    tagger=None,
) -> Translation:
    """Pair the phrase with Call spellings. Exact glosses win before near ones."""
    by_gloss: dict[str, list[Root]] = {}
    for root in roots:
        for gloss in root.glosses:
            by_gloss.setdefault(gloss, []).append(root)
    words, after = _tokens(phrase)
    poses = list(tagger(words)) if tagger else [""] * len(words)
    matched: list[tuple[str, str]] = []
    spans: list[tuple[int, int, str]] = []
    left: list[str] = []
    index = 0
    while index < len(words):
        hit = _exact(words, index, by_gloss) or _nearest(
            words, index, by_gloss, scorer, _room_before_exact(words, index, by_gloss), poses
        )
        if hit is None:
            left.append(words[index])
            index += 1
            continue
        text, length, root = hit
        matched.append((text, root.spelling))
        spans.append((index, index + length, root.spelling))
        index += length
    return Translation(
        _call_text(spans, after),
        tuple(matched),
        tuple(left),
        _trace_text(words, spans, after),
    )


def speak_file(
    source: Path,
    roots: tuple[Root, ...] | list[Root],
    scorer: object,
    voice: CallVoice | None = None,
    force: bool = False,
    tagger=None,
) -> tuple[Translation, Path, Path]:
    """Write the spoken spellings and a wav named from the source."""
    if not source.is_file():
        raise EnochaeonError(f"No such file: {source}")
    if source.suffix.lower() not in {".txt", ".md"}:
        raise EnochaeonError(f"{source.name} is not a .txt or .md file")
    dest = source.with_suffix(".wav")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    result = match_phrase(source.read_text(encoding="utf-8"), roots, scorer, tagger)
    voice = voice or CallVoice()
    text = _spoken(result.call_text, voice, source.name)
    folder = source.parent / ".enochaeon"
    folder.mkdir(parents=True, exist_ok=True)
    enochian = folder / f"{source.stem}-enochian.txt"
    enochian.write_text(_with_newline(result.trace), encoding="utf-8")
    write_wav(dest, render(text, voice=voice), comment="")
    return result, enochian, dest


def speak_phrase(
    phrase: str,
    dest: Path,
    roots: tuple[Root, ...] | list[Root],
    scorer: object,
    voice: CallVoice | None = None,
    force: bool = False,
) -> Translation:
    """Write a Call wav for the phrase. The file carries no cipher comment."""
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    result = match_phrase(phrase, roots, scorer)
    voice = voice or CallVoice()
    text = _spoken(result.call_text, voice, phrase)
    write_wav(dest, render(text, voice=voice), comment="")
    return result


def _spoken(call_text: str, voice: CallVoice, source: str) -> str:
    """The Call words that have a reading. Anything else is left out."""
    if not call_text.strip():
        raise EnochaeonError(f"Nothing in {source} is close to a Call word.")
    segments, dropped = audible(call_text, _readings(voice))
    if not segments:
        raise EnochaeonError(f"Nothing in {source} is close to a Call word.")
    if not dropped:
        return call_text
    return spoken_text(segments)


def _with_newline(text: str) -> str:
    if text and not text.endswith("\n"):
        return text + "\n"
    return text


def _exact(words: list[str], index: int, by_gloss: dict[str, list[Root]]) -> tuple[str, int, Root] | None:
    limit = min(_MAX_SPAN, len(words) - index)
    for length in range(limit, 0, -1):
        text = " ".join(words[index : index + length])
        hits = by_gloss.get(text)
        if hits:
            return text, length, _pick(hits)
    return None


def _room_before_exact(words: list[str], index: int, by_gloss: dict[str, list[Root]]) -> int:
    """How many words a near span may take before the next exact gloss."""
    room = min(_MAX_SPAN, len(words) - index)
    for cursor in range(index + 1, index + room):
        if _exact(words, cursor, by_gloss):
            return cursor - index
    return room


def _nearest(
    words: list[str],
    index: int,
    by_gloss: dict[str, list[Root]],
    scorer: object,
    room: int,
    poses: list[str],
) -> tuple[str, int, Root] | None:
    if not by_gloss:
        return None
    best: tuple[float, int, str, Root] | None = None
    limit = min(_MAX_SPAN, len(words) - index, room)
    for length in range(limit, 0, -1):
        text = " ".join(words[index : index + length])
        gloss, score, root = _closest(text, by_gloss, scorer, _span_pos(poses, index, length))
        if score < SIMILARITY:
            continue
        if best is None or score > best[0]:
            best = (score, length, text, root)
    if best is None:
        return None
    _score, length, text, root = best
    return text, length, root


def _span_pos(poses: list[str], index: int, length: int) -> str:
    for cursor in range(index + length - 1, index - 1, -1):
        if cursor < len(poses) and poses[cursor]:
            return poses[cursor]
    return ""


def _closest(
    text: str,
    by_gloss: dict[str, list[Root]],
    scorer: object,
    pos: str,
) -> tuple[str, float, Root]:
    ranked: list[tuple[float, str, Root]] = []
    for gloss, hits in by_gloss.items():
        score = float(scorer.similarity(text, gloss))
        ranked.append((score, gloss, _pick(hits)))
    eligible = [item for item in ranked if item[0] >= SIMILARITY]
    same = [item for item in eligible if pos and item[2].pos == pos]
    score, gloss, root = max(same or eligible or ranked, key=lambda item: (item[0], item[1]))
    return gloss, score, root


def part_tags(words: list[str]) -> list[str]:
    """Parts of speech for the input words. The similarity model does not tag them."""
    if not words:
        return []
    try:
        from nltk import pos_tag
    except ImportError as exc:
        raise EnochaeonError(
            "Translating a phrase needs nltk. It is installed with enochaeon."
        ) from exc
    try:
        tagged = pos_tag(words)
    except LookupError:
        import nltk

        nltk.download("averaged_perceptron_tagger_eng", quiet=True)
        tagged = pos_tag(words)
    return [_PARTS.get(tag, "") for _word, tag in tagged]


def _pick(roots: list[Root]) -> Root:
    return min(roots, key=lambda root: (-len(root.calls), len(root.spelling), root.spelling))


def _tokens(phrase: str) -> tuple[list[str], list[str]]:
    """Words, and the strongest mark that sits after each word."""
    words: list[str] = []
    after: list[str] = []
    pending = ""
    letters: list[str] = []

    def flush() -> None:
        if not letters:
            return
        words.append("".join(letters).lower())
        after.append("")
        letters.clear()

    for character in phrase:
        if character.isalpha():
            if not letters and pending and words:
                after[-1] = _stronger(after[-1], pending)
                pending = ""
            letters.append(character)
            continue
        flush()
        mark = _MARKS.get(character, "")
        if mark:
            pending = _stronger(pending, mark)
    flush()
    if words and pending:
        after[-1] = _stronger(after[-1], pending)
    return words, after


def _gap(after: list[str], start: int, end: int) -> str:
    found = ""
    for mark in after[start:end]:
        found = _stronger(found, mark)
    return found


def _stronger(left: str, right: str) -> str:
    if "." in (left, right):
        return "."
    return left or right


def _trace_text(words: list[str], spans: list[tuple[int, int, str]], after: list[str]) -> str:
    """Spellings in order, with an unmatched English word written as ``[word]``."""
    by_start = {start: (end, spelling) for start, end, spelling in spans}
    pieces: list[str] = []
    index = 0
    while index < len(words):
        if pieces:
            mark = after[index - 1]
            pieces.append(f"{mark} " if mark else " ")
        if index in by_start:
            end, spelling = by_start[index]
            pieces.append(spelling)
            index = end
            continue
        pieces.append(f"[{words[index]}]")
        index += 1
    if words and after[-1]:
        pieces.append(after[-1])
    return "".join(pieces)


def _call_text(spans: list[tuple[int, int, str]], after: list[str]) -> str:
    pieces: list[str] = []
    for index, (start, end, spelling) in enumerate(spans):
        if index:
            previous = spans[index - 1][1]
            mark = _gap(after, previous - 1, start)
            pieces.append(f"{mark} " if mark else " ")
        pieces.append(spelling)
    if spans:
        trail = _gap(after, spans[-1][1] - 1, len(after))
        if trail:
            pieces.append(trail)
    return "".join(pieces)
