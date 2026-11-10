# Enochaeon

Enochaeon is a spoken cipher. A text file is transliterated, letter by letter, from English into Hebrew and then into Enochian. Each English word is spoken as one breath of the sounds assigned to those Enochian letters. A phone recognizer hears the breath, the same key turns the letters back into English, and a word list corrects a reading that is not an English word.

Every word is spelled the same way. The reference is the pangram in [`example/pangram.txt`](example/pangram.txt), and `fox` is one word from it:

- `f` is peh without a dagesh, פ. Its Enochian letter is Mals.
- `o` is vav with a cholam, וֹ. Its Enochian letter is Vau.
- `x` is kuf plus samekh, קס. Those letters are Ger and Pal.

In Latin letters that spelling is `PVQS`. O counts as a vowel, so fox is one breath of syllables, not letter-names. A vowel left open is long, a vowel closed by a consonant is short, and a doubled consonant is spoken twice. `Hello` is `HELLV`. Capitals are folded to lowercase.

## Two alphabets

English and the Calls do not use the same table.

English goes through Hebrew on purpose. Dee's own table pairs each of the 21 Enochian characters with one Elizabethan letter, so `fox` would be Orth, Med, Pal: F, O, X. That table has one letter for `u` and `v`, and one letter for `c` and `k`. `w` is two Vans. `th` and `sh` are two letters each, so `the` is Gisg, Na-hath, Graph. The way back cannot spell a distinction that was never spoken. A word list can prefer `over` to `ouer` only when one of them is a word.

The Hebrew key keeps those distinctions. `u` and `v` are different letters, and so are `c` and `k`. `th` and `sh` are one letter each, which is why `the` and `she` are a consonant plus a vowel. `x` is two letters, Ger and Pal, and that is the same pair a written `k` followed by `s` becomes.

Those pairs are traditional, not a table invented here. Each Enochian name answers to a Hebrew letter, the correspondence the Golden Dawn used and the one Leitch records. An English word is spelled with those Hebrew letters, and the names are read off. Aleph is Un, so `a` could be written as a two-column row. Hebrew is what makes the other rows: bet with a dagesh is `b` and bet without one is `v`, yod is `i` and `y`, vav is `o` and `u`, and `w` is two vavs. A Latin table of different pairs would be a different cipher. The Hebrew column stays so this tradition stays visible. The speech and the round trip use the Enochian letters that row chose.

The Calls use Dee's Latin table, not this key. A file in `calls/` is already Enochian written in Latin letters, and `src/enochaeon/enochian.py` speaks those letters directly. `C` and `K` are both the k sound. A word-initial `I` before a vowel is `Y`, which is how Dee said `Iad`. Nothing in a call is transliterated into Hebrew or into the English cipher.

## How it works

The key is `src/enochaeon/data/alphabet.json`. Matching is longest-first, so `ch`, `sh`, `th`, `ts`, and `x` are one row each. `tz` is the same Hebrew and the same Enochian letters as `ts`, and it comes back as `ts`. A written `k` followed by `s` is the same letters as `x`, so `foks` comes back as `fox`.

An English word is always those in-word syllables, including a word with no vowel. The espeak phones in the key are this project's, chosen so a recognizer can tell the letters apart. They are not a historical pronunciation.

A call uses the same length rule inside a word. A call word with no vowel is spoken as letter-names. A comma stays on the line, and a period starts a new line.

Hearing uses [espeak-ng](https://github.com/espeak-ng/espeak-ng) and `facebook/wav2vec2-lv-60-espeak-cv-ft`. Calibration speaks every letter sound once, in a short carrier, and stores what the model actually hears. Two hearings are the same when they match after length, the a/ɑ difference, and a few recognizer spellings of the same phone are ignored. Encoding and decoding both refuse to run until that file exists. If two letters collide, change the `phone` or `long` string for one of them and calibrate again.

Decode aligns the heard phones to those calibrated syllables and inverts the key. The raw reading is then checked against an English word list. A reading that is already in the list is kept. A reading that is not is replaced only when a listed word is within a few phone edits. A vowel edit is cheaper than a consonant edit. The list will keep a real word even when it is the wrong one.

## Sources

The syllable rule comes from Aaron Leitch's reading of John Dee's phonetic notes: a vowel followed by a consonant in its syllable is short, a vowel left open is long, and a letter standing alone takes its letter-name. He states that rule in the pronunciation essay ["Angelical Pronunciation"](http://kheph777.tripod.com/art_angelical_pronunciation.pdf) and again in the introduction to *The Angelical Language, Volume II: An Encyclopedic Lexicon of the Tongue of Angels* (Llewellyn, 2010). This program applies it to a whole word. It does not use Dee's syllable divisions, and it does not include the lexicon, the glosses, or Leitch's own phonetic spellings from that book. *Volume I: The Complete History and Mythos of the Tongue of Angels* (Llewellyn, 2010) is the account of the alphabet this key follows: Dee's letter names, the Hebrew letter each one answers to, the correspondence used by the Golden Dawn, and the Latin letters Leitch reads. None of Leitch's prose is copied here.

The texts in `calls/` are Dee's forty-eight Keys. `01.txt` through `18.txt` are the first eighteen, and `19-lil.txt` through `48-tex.txt` are the Call of the Aethyrs, the same words with that aethyr's name. They are not taken from Leitch's lexicon.

The word list is American SCOWL, size 50: the English and American `words` lists through that size, lowercased to ASCII letters. Proper names, abbreviations, contractions, and the uppercase lists are not included. SCOWL is Copyright 2000-2018 by Kevin Atkinson.

> Permission to use, copy, modify, distribute and sell these word lists, the associated scripts, the output created from the scripts, and its documentation for any purpose is hereby granted without fee, provided that the above copyright notice appears in all copies and that both that copyright notice and this permission notice appear in supporting documentation. Kevin Atkinson makes no representations about the suitability of this array for any purpose. It is provided "as is" without express or implied warranty.

The list is built with the inflection data and the American spelling variants, so the WordNet 1.6 notice (Copyright 1997 by Princeton University), the VarCon notices, and Geoff Kuenning's Ispell terms apply as well. Those notices are reproduced in full in `src/enochaeon/data/SCOWL-Copyright.txt`, which is installed with the package. The same permission notice is at the top of `src/enochaeon/data/words.txt`.

## Setup

```bash
brew install espeak-ng
pip install -e .
enochaeon calibrate
```

## Use

```bash
enochaeon notes.txt    # writes notes.wav and the three stage files
enochaeon notes.wav    # prints the text and writes notes.decoded.txt
enochaeon calls        # speaks every .txt in ./calls
enochaeon calls calls/01.txt
```

Add a call by putting another `.txt` in `calls/`, or pass its path. Each file gets a sibling `.wav` and a phonetic trace in `.enochaeon`.

Calls use the voice in `enochaeon.json`. `calls.engine` is `espeak` or `piper`. `--engine espeak` or `--engine piper` overrides that for one run. The English cipher stays on espeak either way.

Piper needs its own install and John's voice:

```bash
pip install piper-tts
python3 -m piper.download_voices --download-dir scratch/piper-voices en_US-john-medium
```

`calls.piper.voice` is the `.onnx` file that command writes. `calls.piper.length_scale` is how long Piper holds each phoneme. `1.0` is conversational, and higher is slower. It does not change espeak.

The stage files go in a hidden folder next to the source. For `notes-test.txt` they are:

```text
.enochaeon/notes-test-hebrew.txt
.enochaeon/notes-test-enochian.txt
.enochaeon/notes-test-phonetic.txt
```

Hebrew is the pointed transliteration. Enochian is the letter names. Phonetic is one espeak string per English word, the breath espeak speaks.

## Example

[`example/pangram.txt`](example/pangram.txt) is the pangram used above. Encoding it writes the WAV and the three stage files.

- [`example/.enochaeon/pangram-hebrew.txt`](example/.enochaeon/pangram-hebrew.txt) is the pointed Hebrew spelling.
- [`example/.enochaeon/pangram-enochian.txt`](example/.enochaeon/pangram-enochian.txt) is the Enochian letter names.
- [`example/.enochaeon/pangram-phonetic.txt`](example/.enochaeon/pangram-phonetic.txt) is the espeak string, one breath per English word.
- [`example/pangram.wav`](example/pangram.wav) is that breath spoken.
- [`example/pangram.decoded.txt`](example/pangram.decoded.txt) is the English recovered from that WAV.

[`example/First Call.wav`](example/First%20Call.wav) is the first Call spoken from the Latin letters in [`calls/01.txt`](calls/01.txt).

An output that is already there is left alone unless you pass `--force`. A WAV made here carries a short comment with the gap lengths and no plaintext. A WAV without that comment is still decoded, with a warning.
