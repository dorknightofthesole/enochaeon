"""Speak Call words from lexicon dee_ipa, translated into espeak phonemes.

This trial spoke with espeak-ng. The project no longer has that voice, and this script does not run.

This is a trial. It does not change the letter-by-letter speech path.
The voice is en-us: the lexicon writes American oʊ and ɑː, and the usual
en voice is British, which turns oʊ into əʊ and inserts an r after ɑː
when another vowel follows.

A variant wears its root's dee_ipa. balzizras is stored under balt, so
this reading says /bɑːlt/ for it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from enochaeon.audio import normalize, resample, silence, trim_silence, write_wav
from enochaeon.config import load_call_voice
from enochaeon.enochian import phonetic_text
from enochaeon.piper_voice import _speak, ipa_of
from enochaeon.synthesize import SPEED, espeak_binary

ROOT = Path(__file__).resolve().parents[2]
LEXICON = ROOT / "calls" / "lexicon.json"
OUT = ROOT / "scratch"
VOICE = "en-us"
GAP_MS = 600

# Longest IPA symbol first. ɑ alone is spoken as A: because espeak's bare A is silent.
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
_VOWELS = {"A:", "a", "Q", "O:", "O", "I", "i:", "i", "U", "u:", "u", "E", "e", "eI", "oU", "aI", "V", "3:", "@"}


def espeak_of(ipa: str) -> str:
    """One dee_ipa string as the espeak phonemes inside [[]]."""
    body = ipa.strip()
    if body.startswith("/") and body.endswith("/"):
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
            raise ValueError(f"No espeak phoneme for {body[index]!r} in {ipa}")
        src, dst = pair
        index += len(src)
        if stress and dst in _VOWELS:
            tokens.append(stress + dst)
            stress = ""
        else:
            tokens.append(dst)
    if stress:
        raise ValueError(f"Stress with no vowel in {ipa}")
    if not tokens:
        raise ValueError(f"Empty phonemes for {ipa}")
    return " ".join(tokens)


def speak(phonemes: str) -> np.ndarray:
    binary = espeak_binary()
    path = OUT / "_dee-ipa-word.wav"
    completed = subprocess.run(
        [binary, "-v", VOICE, "-s", str(SPEED), "-w", str(path), f"[[{phonemes}]]"],
        check=False,
        capture_output=True,
        text=True,
    )
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0 or "unknown phoneme" in stderr.lower():
        raise RuntimeError(stderr or f"espeak-ng failed on [[{phonemes}]]")
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    path.unlink(missing_ok=True)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio[:, 0]
    return normalize(trim_silence(resample(audio, sample_rate)))


_PIPER_VOWELS = set("ɑæɒɔəɚɛɜɪʊʌaeiou")


def piper_ipa(ipa: str, phonemes: set[str]) -> str:
    """dee_ipa as the characters John speaks. Stress sits on the vowel."""
    body = ipa.strip()
    if body.startswith("/") and body.endswith("/"):
        body = body[1:-1]
    pieces: list[str] = []
    stress = ""
    for mark in body:
        if mark in "/.":
            continue
        if mark == "ˈ":
            stress = "ˈ"
            continue
        if mark == "ˌ":
            stress = "ˌ"
            continue
        spoken = "ɹ" if mark == "r" else mark
        if spoken not in phonemes:
            raise ValueError(f"John has no phoneme {spoken!r} in {ipa}")
        if stress and spoken in _PIPER_VOWELS:
            pieces.append(stress)
            stress = ""
        pieces.append(spoken)
    if stress:
        raise ValueError(f"Stress with no vowel in {ipa}")
    return "".join(pieces)


def phrase(words: list[str], phones_for: dict[str, str], letter: bool) -> np.ndarray:
    pieces: list[np.ndarray] = []
    gap = silence(GAP_MS)
    for word in words:
        phones = phonetic_text(word).strip() if letter else phones_for[word.lower()]
        pieces.append(speak(phones))
        pieces.append(gap)
    return np.concatenate(pieces)


def main() -> None:
    entries = json.loads(LEXICON.read_text(encoding="utf-8"))
    by_spelling: dict[str, tuple[str, str, str]] = {}
    lines = ["spelling\troot\tletter\tdee_ipa\tespeak\town"]
    borrowed = 0
    for entry in entries:
        root = entry["root"].lower()
        ipa = entry["dee_ipa"][entry["root"]]
        phones = espeak_of(ipa)
        names = [root, *(name.lower() for name in entry.get("variants") or [])]
        seen: list[str] = []
        for name in names:
            spelling = "".join(character for character in name if character.isalpha())
            if spelling and spelling not in seen:
                seen.append(spelling)
        for spelling in seen:
            by_spelling[spelling] = (root, ipa, phones)
            own = "yes" if spelling == root else "no"
            if own == "no":
                borrowed += 1
            letter = phonetic_text(spelling).strip()
            lines.append(f"{spelling}\t{root}\t{letter}\t{ipa}\t{phones}\t{own}")
    report = OUT / "dee-ipa.txt"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    clips = {
        "iad": ["iad"],
        "ritual": ["gohol", "iad", "de", "balzizras"],
        "open": ["ol", "sonf", "vorsg", "goho", "iad", "balt"],
    }
    for name, words in clips.items():
        dee = phrase(words, {word: by_spelling[word][2] for word in words}, letter=False)
        letters = phrase(words, {}, letter=True)
        write_wav(OUT / f"dee-ipa-{name}.wav", dee, comment="")
        write_wav(OUT / f"letter-{name}.wav", letters, comment="")
        print(name)
        for word in words:
            root, ipa, phones = by_spelling[word]
            mark = "" if word == root else f"  (root {root})"
            print(f"  {word:12} {ipa:20} {phones}{mark}")
            print(f"  {'':12} letter {phonetic_text(word).strip()}")
    print(f"{len(entries)} roots, {len(by_spelling)} spellings, {borrowed} variants using a root IPA")
    print(report)
    _render_piper(entries, by_spelling, clips)


def _render_piper(entries: list, by_spelling: dict[str, tuple[str, str, str]], clips: dict[str, list[str]]) -> None:
    voice = load_call_voice(ROOT / "enochaeon.json")
    model = ROOT / voice.piper_voice
    phonemes = set(json.loads(Path(str(model) + ".json").read_text(encoding="utf-8"))["phoneme_id_map"])
    piper_for: dict[str, str] = {}
    for entry in entries:
        spelling = entry["root"].lower()
        piper_for[spelling] = piper_ipa(entry["dee_ipa"][entry["root"]], phonemes)
    from piper import PiperVoice, SynthesisConfig

    speaker = PiperVoice.load(model)
    gap_ms = voice.word_ms if voice.word_ms is not None else GAP_MS
    print(f"piper {model.name} length_scale={voice.length_scale} word_ms={gap_ms}")
    for name, words in clips.items():
        dee_ipa = {word: piper_for[by_spelling[word][0]] for word in words}
        dee = _piper_phrase(words, dee_ipa, False, speaker, SynthesisConfig, voice.length_scale, gap_ms)
        letters = _piper_phrase(words, {}, True, speaker, SynthesisConfig, voice.length_scale, gap_ms)
        write_wav(OUT / f"piper-dee-{name}.wav", dee, comment="")
        write_wav(OUT / f"piper-letter-{name}.wav", letters, comment="")
        print(name)
        for word in words:
            root = by_spelling[word][0]
            mark = "" if word == root else f"  (root {root})"
            print(f"  {word:12} [[{dee_ipa[word]}]]{mark}")
            print(f"  {'':12} letter [[{ipa_of(phonetic_text(word).strip())}]]")


def _piper_phrase(words, ipa_for, letter, speaker, config_type, scale, gap_ms) -> np.ndarray:
    pieces: list[np.ndarray] = []
    gap = silence(gap_ms)
    for word in words:
        ipa = ipa_of(phonetic_text(word).strip()) if letter else ipa_for[word]
        pieces.append(_speak(speaker, config_type, ipa, scale))
        pieces.append(gap)
    return np.concatenate(pieces)


if __name__ == "__main__":
    main()
