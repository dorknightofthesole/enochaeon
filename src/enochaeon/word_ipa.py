"""Turn a lexicon IPA string into the phones a Call voice speaks.

The cipher does not come here. A variant wears the IPA stored on its root.
Stress sits on the vowel, and a syllable dot is not a sound. Piper's r is the
English ɹ.
"""

from __future__ import annotations

from enochaeon.errors import EnochaeonError

# Longest symbol first. Bare ɑ is spoken long because espeak's bare A is silent.
_SYMBOLS = (
    ("ɑː", "A:"),
    ("iː", "i:"),
    ("uː", "u:"),
    ("ɔː", "O:"),
    ("ɜː", "3:"),
    ("oʊ", "oU"),
    ("eɪ", "eI"),
    ("aɪ", "aI"),
    ("æ", "a"),
    ("ɑ", "A:"),
    ("ɒ", "Q"),
    ("ɔ", "O"),
    ("ə", "@"),
    ("ɪ", "I"),
    ("ʊ", "U"),
    ("ɛ", "E"),
    ("ʌ", "V"),
    ("ɜ", "3:"),
    ("ʃ", "S"),
    ("θ", "T"),
    ("ŋ", "N"),
    ("ɡ", "g"),
    ("a", "a"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),
    ("b", "b"),
    ("d", "d"),
    ("f", "f"),
    ("h", "h"),
    ("j", "j"),
    ("k", "k"),
    ("l", "l"),
    ("m", "m"),
    ("n", "n"),
    ("p", "p"),
    ("r", "r"),
    ("s", "s"),
    ("t", "t"),
    ("v", "v"),
    ("w", "w"),
    ("z", "z"),
)
_VOWELS = {
    "A:",
    "a",
    "Q",
    "O:",
    "O",
    "I",
    "i:",
    "i",
    "U",
    "u:",
    "u",
    "E",
    "e",
    "eI",
    "oU",
    "aI",
    "V",
    "3:",
    "@",
}
_PIPER_VOWELS = set("ɑæɒɔəɚɛɜɪʊʌaeiou")


def espeak_phones(ipa: str) -> str:
    """One lexicon reading as the espeak phonemes inside [[]]."""
    return " ".join(_tokens(ipa))


def piper_phones(ipa: str) -> str:
    """One lexicon reading as the IPA characters Piper speaks."""
    pieces: list[str] = []
    for token in _tokens(ipa):
        mark = ""
        if token[0] in "',":
            mark = "ˈ" if token[0] == "'" else "ˌ"
            token = token[1:]
        spoken = _piper_token(token)
        if mark:
            vowel_at = next(index for index, piece in enumerate(spoken) if piece in _PIPER_VOWELS)
            spoken = spoken[:vowel_at] + mark + spoken[vowel_at:]
        pieces.append(spoken)
    return "".join(pieces)


def _tokens(ipa: str) -> list[str]:
    body = ipa.strip()
    if body.startswith("/") and body.endswith("/") and len(body) >= 2:
        body = body[1:-1]
    tokens: list[str] = []
    stress = ""
    index = 0
    while index < len(body):
        mark = body[index]
        if mark in "/.":
            index += 1
            continue
        if mark == "ˈ":
            stress = "'"
            index += 1
            continue
        if mark == "ˌ":
            stress = ","
            index += 1
            continue
        pair = next(((src, dst) for src, dst in _SYMBOLS if body.startswith(src, index)), None)
        if pair is None:
            raise EnochaeonError(f"No phoneme for {body[index]!r} in {ipa!r}.")
        src, dst = pair
        index += len(src)
        if stress and dst in _VOWELS:
            tokens.append(stress + dst)
            stress = ""
        else:
            tokens.append(dst)
    if stress:
        raise EnochaeonError(f"Stress with no vowel in {ipa!r}.")
    if not tokens:
        raise EnochaeonError(f"Empty phonemes for {ipa!r}.")
    return tokens


def _piper_token(token: str) -> str:
    pieces: list[str] = []
    index = 0
    while index < len(token):
        if token.startswith("A:", index):
            pieces.append("ɑː")
            index += 2
            continue
        if token.startswith("i:", index):
            pieces.append("iː")
            index += 2
            continue
        if token.startswith("u:", index):
            pieces.append("uː")
            index += 2
            continue
        if token.startswith("O:", index):
            pieces.append("ɔː")
            index += 2
            continue
        if token.startswith("3:", index):
            pieces.append("ɜː")
            index += 2
            continue
        if token.startswith("oU", index):
            pieces.append("oʊ")
            index += 2
            continue
        if token.startswith("eI", index):
            pieces.append("eɪ")
            index += 2
            continue
        if token.startswith("aI", index):
            pieces.append("aɪ")
            index += 2
            continue
        piece = {
            "a": "æ",
            "Q": "ɒ",
            "O": "ɔ",
            "@": "ə",
            "I": "ɪ",
            "U": "ʊ",
            "E": "ɛ",
            "V": "ʌ",
            "S": "ʃ",
            "T": "θ",
            "N": "ŋ",
            "g": "ɡ",
            "r": "ɹ",
        }.get(token[index], token[index])
        pieces.append(piece)
        index += 1
    return "".join(pieces)
