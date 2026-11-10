"""Command line: English becomes a cipher WAV, a call becomes spoken Enochian, and a WAV becomes text."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from enochaeon.alphabet import Alphabet
from enochaeon.calibrate import calibrate
from enochaeon.decode import decode_file, require_calibration
from enochaeon.encode import write_document, write_traces
from enochaeon.enochian import generate_calls
from enochaeon.errors import EnochaeonError

TEXT_SUFFIXES = {".txt", ".md"}
AUDIO_SUFFIXES = {".wav"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="enochaeon",
        description="Transliterate a text file into Enochian audio, speak a call, or read that audio back.",
    )
    parser.add_argument(
        "target",
        help="A .txt or .md file, a .wav file, 'calibrate', or 'calls'",
    )
    parser.add_argument(
        "calls_path",
        nargs="?",
        help="With 'calls', a .txt file or a directory of them. Defaults to ./calls",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an output file that is already there",
    )
    args = parser.parse_args(argv)
    try:
        if args.target == "calibrate":
            return calibrate()
        if args.target == "calls":
            return generate_calls(Path(args.calls_path or "calls"), args.force)
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


def _encode(path: Path, alphabet: Alphabet, force: bool) -> int:
    dest = path.with_suffix(".wav")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    require_calibration(alphabet)
    text = path.read_text(encoding="utf-8")
    for trace in write_traces(path, text, alphabet):
        print(trace)
    write_document(text, dest, alphabet)
    print(dest)
    return 0


def _decode(path: Path, alphabet: Alphabet, force: bool) -> int:
    dest = path.with_name(f"{path.stem}.decoded.txt")
    if dest.exists() and not force:
        raise EnochaeonError(f"{dest} already exists. Pass --force to replace it.")
    labels = require_calibration(alphabet)
    text, unknown = decode_file(path, alphabet, labels)
    dest.write_text(text, encoding="utf-8")
    if text and not text.endswith("\n"):
        print(text)
    else:
        sys.stdout.write(text)
    if unknown:
        print("Some syllables matched no letter and were written as �.", file=sys.stderr)
        return 2
    return 0
