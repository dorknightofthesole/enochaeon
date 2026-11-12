"""Command line: a cipher WAV, a spoken Call, a text file spoken as Call words, or a WAV read back."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from enochaeon.alphabet import Alphabet
from enochaeon.calibrate import calibrate
from enochaeon.config import load_call_voice, load_cipher_voice
from enochaeon.decode import RUN_CALIBRATE, decode_file, require_calibration
from enochaeon.encode import write_document, write_traces
from enochaeon.enochian import generate_calls
from enochaeon.errors import EnochaeonError

TEXT_SUFFIXES = {".txt", ".md"}
AUDIO_SUFFIXES = {".wav"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="enochaeon",
        description="Transliterate a text file, speak a call, speak a text file as Call words, or read a cipher wav back.",
    )
    parser.add_argument(
        "target",
        help="A .txt or .md file, a .wav file, 'calibrate', 'calls', or 'translate'",
    )
    parser.add_argument(
        "calls_path",
        nargs="?",
        help="With 'calls', a .txt file or a directory. With 'translate', a .txt or .md file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an output file that is already there",
    )
    args = parser.parse_args(argv)
    try:
        if args.target == "translate":
            return _translate(args.calls_path, args.force)
        if args.target == "calibrate":
            return calibrate()
        if args.target == "calls":
            return generate_calls(Path(args.calls_path or "calls"), args.force, load_call_voice())
        if args.calls_path is not None:
            raise EnochaeonError("A second path is only used with 'calls'.")
        path = Path(args.target)
        if not path.is_file():
            raise EnochaeonError(f"No such file: {path}")
        suffix = path.suffix.lower()
        alphabet = Alphabet.load()
        if suffix in TEXT_SUFFIXES:
            return _encode(path, alphabet, args.force)
        if suffix in AUDIO_SUFFIXES:
            return _decode(path, alphabet, args.force)
        raise EnochaeonError(f"{path.name} is not a .txt, .md, or .wav file")
    except EnochaeonError as exc:
        print(exc, file=sys.stderr)
        return 1


def _translate(source: str | None, force: bool) -> int:
    if not source:
        raise EnochaeonError("translate needs a .txt or .md file.")
    path = Path(source)
    if not path.is_file():
        raise EnochaeonError(f"No such file: {path}")
    if path.suffix.lower() not in TEXT_SUFFIXES:
        raise EnochaeonError(f"{path.name} is not a .txt or .md file")
    dest = path.with_suffix(".wav")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    from enochaeon.roots import load_roots
    from enochaeon.translate import MiniLM, part_tags, speak_file

    result, trace, dest = speak_file(
        path, load_roots(), MiniLM(), load_call_voice(), force, part_tags
    )
    for english, spelling in result.matched:
        print(f"{english} {spelling}")
    if result.left_out:
        print("left out: " + " ".join(result.left_out))
    print(trace)
    print(dest)
    print(dest.with_suffix(".html"))
    return 0


def _encode(path: Path, alphabet: Alphabet, force: bool) -> int:
    dest = path.with_suffix(".wav")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    from enochaeon.cipher_voice import Speaker

    voice = load_cipher_voice()
    speaker = Speaker(voice, alphabet)
    if not require_calibration(alphabet).made_for(speaker.name, voice.bridge_ms, voice.hear_ms):
        raise EnochaeonError(
            f"The calibration was not made with the cipher section of enochaeon.json as it is now. {RUN_CALIBRATE}"
        )
    text = path.read_text(encoding="utf-8")
    left_out = alphabet.left_out(text)
    if left_out:
        print(left_out, file=sys.stderr)
    for trace in write_traces(path, text, alphabet):
        print(trace)
    write_document(text, dest, alphabet, voice, speaker)
    print(dest)
    return 0


def _decode(path: Path, alphabet: Alphabet, force: bool) -> int:
    dest = path.with_name(f"{path.stem}.decoded.txt")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    text, unknown = decode_file(path, alphabet, require_calibration(alphabet))
    dest.write_text(text, encoding="utf-8")
    if text and not text.endswith("\n"):
        print(text)
    else:
        sys.stdout.write(text)
    if unknown:
        print("Some sounds gave no letter the key can spell and were written as �.", file=sys.stderr)
        return 2
    return 0
