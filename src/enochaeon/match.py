"""Weighted phone-string distance.

A consonant that changes costs more than a vowel that drifts. That is the
closed-set match from the research note: the skeleton of the syllable matters
more than its exact vowel color.
"""

from __future__ import annotations

_CONSONANTS = set("bdfɡghjklmnŋprstvwzʃʒθðɣχħʔɾɹx")


# What this recognizer writes when it means a phone we already have.
_CHAR_ALIASES = str.maketrans({
    "ɡ": "g",
    "ɕ": "s",
    "ʂ": "s",
    "ç": "s",
    "ʑ": "z",
    "ʉ": "u",
    "ɯ": "u",
    "x": "h",
    "χ": "h",
})
_TOKEN_ALIASES = {
    "ph": "p",
    "kh": "k",
    "ts": "t",
}


def _fold(token: str) -> str:
    """Ignore length, stress, and a few recognizer spellings of the same phone.

    a and ɑ are the same vowel color. A dotted ``s.`` is ``s``, the palatal
    fricative ``ɕ`` is ``s``, and a diphthong keeps its first vowel.
    """
    folded = token.rstrip("0123456789").replace("ː", "").replace(".", "")
    folded = folded.replace("ɑ", "a").replace("ɐ", "a").translate(_CHAR_ALIASES)
    folded = _TOKEN_ALIASES.get(folded, folded)
    if len(folded) > 1 and not any(character in _CONSONANTS for character in folded):
        folded = folded[0]
    return folded


def fold_phones(phones: str) -> tuple[str, ...]:
    """The identity of a phone string. Length and a/ɑ do not count."""
    return tuple(_fold(token) for token in phones.split())


def _is_vowel(token: str) -> bool:
    return not any(character in _CONSONANTS for character in _fold(token))


def _substitute(left: str, right: str) -> int:
    if _fold(left) == _fold(right):
        return 0
    if _is_vowel(left) and _is_vowel(right):
        return 1
    return 3


def _indel(token: str) -> int:
    return 1 if _is_vowel(token) else 2


def align_word(heard: str, labels: dict[str, dict[str, str]]) -> tuple[tuple[str, ...], int]:
    """Recover the letter sequence of one spoken word.

    A word is either letter-names or syllabified sounds. Both readings are
    aligned and the cheaper one is kept. The cost is large when the phones
    cannot be covered.
    """
    observed = tuple(heard.split())
    if not observed:
        return (), 10**9
    syllable = _align(observed, _variants(labels, ("phone", "long")))
    names = _align(observed, _variants(labels, ("name",)))
    if names[1] < syllable[1]:
        chosen = names
    else:
        chosen = syllable
    atom_ids, cost = chosen
    if cost > max(8, len(observed)):
        return (), cost
    return atom_ids, cost


def _variants(
    labels: dict[str, dict[str, str]],
    keys: tuple[str, ...],
) -> list[tuple[str, tuple[str, ...]]]:
    variants: list[tuple[str, tuple[str, ...]]] = []
    for atom_id, forms in labels.items():
        for key in keys:
            spoken = forms.get(key, "")
            if spoken:
                variants.append((atom_id, tuple(spoken.split())))
    return variants


def _align(
    observed: tuple[str, ...],
    variants: list[tuple[str, tuple[str, ...]]],
) -> tuple[tuple[str, ...], int]:
    """Best atom sequence covering every phone. Uncovered audio costs 10**9."""
    count = len(observed)
    inf = 10**9
    cost = [inf] * (count + 1)
    path: list[tuple[str, ...]] = [()] * (count + 1)
    cost[0] = 0
    for start in range(count + 1):
        if cost[start] >= inf:
            continue
        for atom_id, template in variants:
            if not template:
                continue
            longest = min(count, start + len(template) + 3)
            shortest = start + max(1, len(template) - 2)
            if shortest > longest:
                continue
            for end in range(shortest, longest + 1):
                span = observed[start:end]
                distance = phone_distance(span, template)
                limit = max(3, max(len(span), len(template)) // 2)
                if distance > limit:
                    continue
                total = cost[start] + distance
                # On a tie, keep the reading with more letters. One syllable
                # should not swallow the next when both readings cost the same.
                if total < cost[end] or (
                    total == cost[end] and len(path[start]) + 1 > len(path[end])
                ):
                    cost[end] = total
                    path[end] = path[start] + (atom_id,)
    return path[count], cost[count]


def phone_distance(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    """Levenshtein distance over phone tokens."""
    if not left:
        return sum(_indel(token) for token in right)
    if not right:
        return sum(_indel(token) for token in left)
    previous = [0]
    running = 0
    for token in right:
        running += _indel(token)
        previous.append(running)
    for left_token in left:
        current = [_indel(left_token) + previous[0]]
        for index, right_token in enumerate(right):
            current.append(
                min(
                    previous[index + 1] + _indel(left_token),
                    current[index] + _indel(right_token),
                    previous[index] + _substitute(left_token, right_token),
                )
            )
        previous = current
    return previous[-1]
