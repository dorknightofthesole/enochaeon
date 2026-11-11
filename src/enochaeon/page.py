"""An HTML page of a translation, in Enochian letters, beside its wav."""

from __future__ import annotations

import base64
import html
from pathlib import Path

from enochaeon.alphabet import DATA_DIR
from enochaeon.errors import EnochaeonError

_FONT = DATA_DIR / "enochian.ttf"
# Dee's alphabet has no J, K, V, W, or Y. Only an Enochian word is rewritten.
_FOLD = {"j": "i", "k": "c", "v": "u", "w": "uu", "y": "i"}


def render_page(trace: str, wav_name: str, wav_bytes: bytes | None = None) -> str:
    """The trace in Enochian letters, with the recording embedded in the page."""
    if not _FONT.is_file():
        raise EnochaeonError(f"The Enochian letters are missing: {_FONT}")
    font = base64.b64encode(_FONT.read_bytes()).decode("ascii")
    spoken = _without_brackets(trace)
    title = html.escape(Path(wav_name).stem)
    if wav_bytes is None:
        source = html.escape(wav_name, quote=True)
    else:
        source = "data:audio/wav;base64," + base64.b64encode(wav_bytes).decode("ascii")
    return _PAGE.format(
        font=font,
        title=title,
        glyphs=_glyphs(spoken),
        wav=source,
    )


def _glyphs(trace: str) -> str:
    """Each spoken word, with its mark kept on that word."""
    words: list[str] = []
    pending = ""
    for kind, text in _pieces(trace):
        if kind == "en":
            if pending:
                words.append(f'<span class="word">{pending}</span>')
            pending = f'<span class="en">{html.escape(text)}</span>'
            continue
        mark = text.strip()
        if not mark:
            continue
        pending += f'<span class="plain">{html.escape(mark)}</span>'
    if pending:
        words.append(f'<span class="word">{pending}</span>')
    return "".join(words)


def _without_brackets(trace: str) -> str:
    """The spoken spellings. A bracketed English word is left off the page."""
    kept: list[str] = []
    index = 0
    length = len(trace)
    while index < length:
        if trace[index] == "[":
            end = trace.find("]", index + 1)
            if end < 0:
                kept.append(trace[index:])
                break
            index = end + 1
            continue
        kept.append(trace[index])
        index += 1
    return _tidy("".join(kept))


def _tidy(text: str) -> str:
    pieces: list[str] = []
    previous_space = False
    for character in text:
        if character == " ":
            if previous_space:
                continue
            previous_space = True
        else:
            previous_space = False
        pieces.append(character)
    result = "".join(pieces).strip()
    cleaned: list[str] = []
    for character in result:
        if character in ".,;:!?" and cleaned and cleaned[-1] == " ":
            cleaned.pop()
        cleaned.append(character)
    return "".join(cleaned)


def _pieces(trace: str) -> list[tuple[str, str]]:
    """Enochian words, and the marks that sit between them."""
    pieces: list[tuple[str, str]] = []
    index = 0
    length = len(trace)
    while index < length:
        if trace[index] == "[":
            end = trace.find("]", index + 1)
            if end < 0:
                pieces.append(("plain", trace[index:]))
                break
            pieces.append(("plain", trace[index : end + 1]))
            index = end + 1
            continue
        if trace[index].isalpha():
            end = index + 1
            while end < length and trace[end].isalpha():
                end += 1
            pieces.append(("en", _fold(trace[index:end])))
            index = end
            continue
        end = index + 1
        while end < length and trace[end] != "[" and not trace[end].isalpha():
            end += 1
        pieces.append(("plain", trace[index:end]))
        index = end
    return pieces


def _fold(word: str) -> str:
    letters: list[str] = []
    for character in word:
        folded = _FOLD.get(character.lower())
        if folded:
            letters.append(folded)
        elif character.isalpha():
            letters.append(character.lower())
        else:
            letters.append(character)
    return "".join(letters)


_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
@font-face {{
  font-family: "Enochian";
  src: url("data:font/truetype;base64,{font}") format("truetype");
}}
body {{
  margin: 2.5rem;
  background: white;
  color: #1a1a1a;
}}
.glyphs {{
  font-size: 4.5rem;
  line-height: 1.45;
}}
.word {{
  margin-right: 0.55em;
}}
.word:last-child {{
  margin-right: 0;
}}
.en {{
  font-family: "Enochian", serif;
}}
.plain {{
  font-family: Palatino, "Palatino Linotype", "Times New Roman", serif;
  font-size: 0.42em;
}}
audio {{
  margin-top: 1.5rem;
}}
.credit {{
  margin-top: 2.5rem;
  font-family: Palatino, "Palatino Linotype", "Times New Roman", serif;
  font-size: 0.85rem;
}}
</style>
</head>
<body>
<p class="glyphs">{glyphs}</p>
<audio controls src="{wav}"></audio>
<p class="credit">Letters by Лорд Алекс, <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>.</p>
</body>
</html>
"""
