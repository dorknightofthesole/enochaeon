"""Fill the field of the cipher's key that says what one voice is given for each letter sound.

    python3 tools/cipher/voice-sounds.py tools/cipher/piper-john.json [--replace]

The cipher gives a voice what src/enochaeon/data/alphabet.json has for it and
works nothing out. This script is how that field gets its first value. It
reads a method file typed by hand:

field       the field to fill, the one enochaeon.json names in cipher.sounds
symbols     each espeak symbol the key's letter sounds are written with, and
            the letters the voice is given for it

Each letter of the key has a short sound, and a vowel has a long one as well.
The field has a string for each:

    "piper_john": {"phone": "bˈiː", "long": "dˈuː"}

A sound that already has a string in the field keeps it, so a string corrected
by ear stays corrected. --replace writes every sound again.

Every other line of the key is written back as it was.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY = ROOT / "src" / "enochaeon" / "data" / "alphabet.json"
FORMS = ("phone", "long")


def voice_sound(espeak: str, symbols: dict[str, str]) -> str:
    """One espeak string as the voice is to be given it. The longest symbol that fits is taken first."""
    ordered = sorted(symbols, key=len, reverse=True)
    pieces: list[str] = []
    index = 0
    while index < len(espeak):
        symbol = next((name for name in ordered if espeak.startswith(name, index)), None)
        if symbol is None:
            raise SystemExit(f"The method file has no symbol for {espeak[index:]!r} in {espeak!r}.")
        pieces.append(symbols[symbol])
        index += len(symbol)
    return "".join(pieces)


def written(key: dict) -> str:
    """The key file as it is laid out: one row to a line."""
    lists = [
        f'  "{name}": [\n' + ",\n".join("    " + json.dumps(row, ensure_ascii=False) for row in rows) + "\n  ]"
        for name, rows in key.items()
    ]
    return "{\n" + ",\n".join(lists) + "\n}\n"


def main(arguments: list[str]) -> int:
    replace = "--replace" in arguments
    paths = [argument for argument in arguments if argument != "--replace"]
    if len(paths) != 1:
        print(__doc__)
        return 2
    method = json.loads(Path(paths[0]).read_text(encoding="utf-8"))
    field = method["field"]
    before = KEY.read_text(encoding="utf-8")
    key = json.loads(before)
    if written(key) != before:
        raise SystemExit(f"{KEY} is not laid out one row to a line, so it is left as it is.")
    filled = kept = 0
    for atom in key["atoms"]:
        have = dict(atom.get(field, {}))
        for form in FORMS:
            if form not in atom:
                continue
            if form in have and not replace:
                kept += 1
                continue
            have[form] = voice_sound(atom[form], method["symbols"])
            filled += 1
        atom[field] = {form: have[form] for form in FORMS if form in have}
        print(f"{atom['id']:12} " + "  ".join(f"{atom[form]} -> {atom[field][form]}" for form in FORMS if form in atom))
    KEY.write_text(written(key), encoding="utf-8")
    print(f"{field}: {filled} written, {kept} kept as they were, in {KEY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
