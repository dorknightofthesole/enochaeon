"""Turn a lexicon IPA string into the phones a Call voice speaks.

The cipher does not come here. A Golden Dawn reading is the string stored
on the root. The Dee reading is the letter rule of the spelling itself.
Stress sits on the vowel, and a syllable dot is not a sound. Piper's r is the
English ɹ.

A lexicon field written for one voice does not pass through that translation.
as_written sends it as the lexicon has it.
"""

from __future__ import annotations

from enochaeon.errors import EnochaeonError

# Longest symbol first. Bare ɑ is the letter-name A in "'Ar". Long ɑː is "A:".
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
    ("ɑ", "A"),
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
    "A",
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
# Espeak symbols the letter rule emits, longest first. Bare ɜ is only a
# spoken form of ɜː, so it is not a source here.
_FROM_ESPEAK = tuple(
    sorted(
        ((espeak, ipa) for ipa, espeak in _SYMBOLS if ipa != "ɜ"),
        key=lambda item: len(item[0]),
        reverse=True,
    )
)


def espeak_phones(ipa: str) -> str:
    """One lexicon reading as the espeak phonemes inside [[]]."""
    return " ".join(_tokens(ipa))


def ipa_of_espeak(phones: str) -> str:
    """Slash IPA for one letter-rule string. Stress stays on the vowel."""
    body = phones.strip()
    if not body:
        raise EnochaeonError("Empty phonemes.")
    return "/" + ".".join(_ipa_token(token) for token in body.split()) + "/"


def _ipa_token(token: str) -> str:
    pieces: list[str] = []
    index = 0
    stress = False
    while index < len(token):
        if token[index] == "'":
            stress = True
            index += 1
            continue
        pair = next((item for item in _FROM_ESPEAK if token.startswith(item[0], index)), None)
        if pair is None:
            raise EnochaeonError(f"No IPA for {token[index:]!r} in {token!r}.")
        espeak, ipa = pair
        if stress and espeak in _VOWELS:
            ipa = "ˈ" + ipa
            stress = False
        pieces.append(ipa)
        index += len(espeak)
    if stress:
        raise EnochaeonError(f"Stress with no vowel in {token!r}.")
    return "".join(pieces)


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


def as_written(reading: str) -> str:
    """A reading the lexicon wrote for one voice: what stands between its slashes, unchanged."""
    body = reading.strip()
    if len(body) < 3 or not (body.startswith("/") and body.endswith("/")):
        raise EnochaeonError(f"A voice reading is written between slashes, not {reading!r}.")
    return body[1:-1]


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
        if token.startswith("A", index):
            pieces.append("ɑ")
            index += 1
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
