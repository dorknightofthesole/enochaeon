"""Where real paraphrases and nonsense words sit against the gloss list."""

from enochaeon.roots import load_roots
from enochaeon.translate import MiniLM

roots = load_roots()
glosses = []
seen = set()
for root in roots:
    for gloss in root.glosses:
        if gloss not in seen:
            seen.add(gloss)
            glosses.append(gloss)

model = MiniLM()
words = [
    "harmony",
    "fairness",
    "goddess",
    "foobar",
    "xyzzy",
    "asdf",
    "qwerty",
    "blargh",
    "into",
    "the",
]
lines = []
for word in words:
    ranked = sorted(
        ((float(model.similarity(word, gloss)), gloss) for gloss in glosses),
        reverse=True,
    )
    best, second = ranked[0], ranked[1]
    lines.append(
        f"{word:10} {best[0]:.3f} {best[1]:24}  next {second[0]:.3f} {second[1]}"
    )

text = "\n".join(lines) + "\n"
print(text, end="")
open("scratch/gloss-floor.txt", "w", encoding="utf-8").write(text)
