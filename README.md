# Enochaeon

Enochaeon is a spoken cipher. A text file is transliterated, letter by letter, from English into Hebrew and then into Enochian. Those Enochian letters are what get spoken. Speech-to-text hears the syllables and the same key writes the English again.

The name is a pun on Hebrew *chol*: sand, the date palm, and the phoenix. The Phoenicians made the first phonetic alphabet. This is a small, whole-language version of that idea: one alphabet written through two others, then read aloud.

`fox` is the pattern for every word.

- `f` is peh without a dagesh, פ. Its Enochian letter is Mals.
- `o` is vav with a cholam, וֹ. Its Enochian letter is Vau.
- `x` is kuf plus samekh, קס. Those letters are Ger and Pal.

The Enochian values of that spelling are `PVQS`. O counts as a vowel, so fox is one breath of syllables, not letter-names. A vowel left open is long, a vowel closed by a consonant is short, and a doubled consonant is spoken twice. `Hello` is `HELLV`. A call is the other case: a call word with no vowel is letter-names. The Calls lexicon in *The Angelical Language* is not in this program. The syllable rules are. The Calls will use this same speaker.

Hearing Ger and then Pal is the row for `x`, so the audio of `fox` comes back as `fox`. The same two letters are what a written `k` followed by `s` becomes, so `foks` comes back as `fox` as well. `tz` is the same spelling as `ts` and comes back as `ts`. Capitals are folded to lowercase.

## Setup

```bash
brew install espeak-ng
pip install -e .
enochaeon calibrate
```

Calibration speaks every letter sound once, in a short carrier, downloads `facebook/wav2vec2-lv-60-espeak-cv-ft`, and writes what that model actually hears. Encoding and decoding both refuse to run until that file exists. Two hearings are the same when they match after length, the a/ɑ difference, and a few recognizer spellings of the same phone are ignored. If that happens, change the `phone` or `long` string for one of them in `src/enochaeon/data/alphabet.json` and calibrate again.

## Use

```bash
enochaeon notes.txt    # writes notes.wav and the three stage files
enochaeon notes.wav    # prints the text and writes notes.decoded.txt
enochaeon calls        # speaks every .txt in ./calls
enochaeon calls calls/01.txt
```

`calls` reads letters that are already Enochian. It does not run them through the English cipher. A comma stays on the line, and a period starts a new line. One file is one call. `calls/` holds the forty-eight calls in Dee's spelling: `01.txt` through `18.txt` are the first eighteen Keys, and `19-lil.txt` through `48-tex.txt` are the Call of the Aethyrs, the same words with that aethyr's name. Add your own by putting another `.txt` in that folder, or pass its path. Each file gets a sibling `.wav` and a phonetic trace in `.enochaeon`.

The stage files go in a hidden folder next to the source. For `notes-test.txt` they are:

```text
.enochaeon/notes-test-hebrew.txt
.enochaeon/notes-test-enochian.txt
.enochaeon/notes-test-phonetic.txt
```

Hebrew is the pointed transliteration. Enochian is the letter names. Phonetic is one espeak string per English word, the breath espeak speaks.

An output that is already there is left alone unless you pass `--force`. A WAV made here carries a short comment with the gap lengths and no plaintext. A WAV without that comment is still decoded, with a warning.

The first real check is `fox`:

```bash
printf 'fox\n' > /tmp/fox.txt
enochaeon /tmp/fox.txt
enochaeon /tmp/fox.wav
```
