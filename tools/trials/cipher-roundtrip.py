"""Encode texts with the cipher as shipped, read each wav back from disk, and count what came back.

  PYTHONPATH=src python3 tools/trials/cipher-roundtrip.py TEXT...

For each text it writes scratch/cipher-roundtrip/<stem>.wav and
<stem>.decoded.txt, and a line in scratch/cipher-roundtrip/results.txt.

A decoded text is compared with what the key gives back from the text with no
audio at all, so only what speech and hearing lose is counted.

This reads back a file the tool wrote. It does not say a recording survives
being played through a speaker and recorded again.
"""

from __future__ import annotations

import difflib
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from enochaeon.alphabet import Alphabet
from enochaeon.cipher_voice import Speaker
from enochaeon.config import load_cipher_voice
from enochaeon.decode import decode_file, require_calibration
from enochaeon.encode import write_document

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scratch" / "cipher-roundtrip"


def tokens(text: str) -> list[str]:
    """The words of a text in order, with a line break between two lines."""
    found: list[str] = []
    for line in text.strip().split("\n"):
        if found:
            found.append("\n")
        found += line.split()
    return found


def main(arguments: list[str]) -> int:
    if not arguments:
        print(__doc__)
        return 2
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    alphabet = Alphabet.load()
    voice = load_cipher_voice()
    speaker = Speaker(voice, alphabet)
    calibration = require_calibration(alphabet)
    report = [f"cipher voice {speaker.name}; calibration voice {calibration.voice}",
              "words: words that came back right, of the words the key gives back with no audio.", ""]
    for name in arguments:
        source = ROOT / name
        text = source.read_text(encoding="utf-8")
        expected, _ = alphabet.decode_atoms(alphabet.atom_ids(text))
        wav = OUT / f"{source.stem}.wav"
        started = time.time()
        write_document(text, wav, alphabet, voice, speaker)
        spoken = time.time() - started
        started = time.time()
        decoded, unknown = decode_file(wav, alphabet, calibration)
        read = time.time() - started
        (OUT / f"{source.stem}.decoded.txt").write_text(decoded, encoding="utf-8")
        want, got = tokens(expected), tokens(decoded)
        blocks = difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks()
        same = [token for block in blocks for token in want[block.a : block.a + block.size]]
        breaks = same.count("\n")
        report.append(
            f"{name}: words {len(same) - breaks}/{len(want) - want.count(chr(10))}, "
            f"line breaks {breaks}/{want.count(chr(10))}, the same text: {decoded.strip() == expected.strip()}, "
            f"a sound with no letter: {unknown}, {wav.stat().st_size / 32000:.1f} s of sound, "
            f"{spoken:.0f} s to speak, {read:.0f} s to read back")
        print(report[-1], flush=True)
    (OUT / "results.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
