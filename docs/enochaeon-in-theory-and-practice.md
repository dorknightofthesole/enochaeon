# How Enochaeon works

Enochaeon has three paths. They do not share a pronunciation.

The cipher turns an English text file into Hebrew, then into Enochian letters, speaks those letters, and can read the recording back into English. Translate speaks an English phrase as Call words by matching it to the lexicon. A Call file is already Enochian, and each spelling is spoken from the pronunciation stored for it.

## The cipher

English goes through Hebrew on purpose. Dee's own table pairs each of the 21 Enochian characters with one Elizabethan letter, so `fox` would be Orth, Med, Pal: F, O, X. That table has one letter for `u` and `v`, and one letter for `c` and `k`. `w` is two Vans. `th` and `sh` are two letters each, so `the` is Gisg, Na-hath, Graph. The way back cannot spell a distinction that was never spoken. A word list can prefer `over` to `ouer` only when one of them is a word.

The Hebrew key keeps those distinctions. `u` and `v` are different letters, and so are `c` and `k`. `th` and `sh` are one letter each, which is why `the` and `she` are a consonant plus a vowel. `x` is two letters, Ger and Pal, and that is the same pair a written `k` followed by `s` becomes.

Those pairs are traditional, not a table invented here. Each Enochian name answers to a Hebrew letter, the correspondence the Golden Dawn used and the one Leitch records. An English word is spelled with those Hebrew letters, and the names are read off. Aleph is Un, so `a` could be written as a two-column row. Hebrew is what makes the other rows: bet with a dagesh is `b` and bet without one is `v`, yod is `i` and `y`, vav is `o` and `u`, and `w` is two vavs. A Latin table of different pairs would be a different cipher. The Hebrew column stays so this tradition stays visible. The speech and the round trip use the Enochian letters that row chose.

Every word is spelled the same way. The reference is the pangram in [`example/pangram.txt`](../example/pangram.txt), and `fox` is one word from it:

- `f` is peh without a dagesh, פ. Its Enochian letter is Mals.
- `o` is vav with a cholam, וֹ. Its Enochian letter is Vau.
- `x` is kuf plus samekh, קס. Those letters are Ger and Pal.

In Latin letters that spelling is `PVQS`. O counts as a vowel, so fox is spoken as in-word letter sounds, not letter-names. A vowel left open is long, a vowel closed by a consonant is short, and a doubled consonant is spoken twice. `Hello` is `HELLV`. Capitals are folded to lowercase.

The key is [`src/enochaeon/data/alphabet.json`](../src/enochaeon/data/alphabet.json). Matching is longest-first, so `ch`, `sh`, `th`, `ts`, and `x` are one row each. `tz` is the same Hebrew and the same Enochian letters as `ts`, and it comes back as `ts`. A written `k` followed by `s` is the same letters as `x`, so `foks` comes back as `fox`. The joined letter `æ` is the row for `a` and `e`, and it comes back as `ae`. An accent is not read, so `è` is `e` and comes back as `e`.

An English word is always those in-word sounds, including a word with no vowel. The sounds in the key are this project's, chosen so a recognizer can tell the letters apart. They are not a historical pronunciation. Each is written the espeak way in `phone` and `long`. What a voice is given for a sound is a field of its own on the same row: `piper_john` is what the Piper voice John is given, and `cipher.sounds` in `enochaeon.json` names that field. A comma stays on the line, and a period starts a new line. A hyphen or a dash is a space between two words. Quotes and brackets are skipped.

Any other character has no row in the key: `&`, a digit, a Greek or a Hebrew letter. The cipher leaves such a character out and goes on. It prints every one that was left out, with the lines it is on. The recording does not have them, so the text comes back without them: `my heart & my tongue` comes back as `my heart my tongue`.

`enochaeon notes.txt` writes three stage files in `.enochaeon/` beside the source, then `notes.wav`. Hebrew is the pointed transliteration. Enochian is the letter names. Phonetic is the letter sounds of each English word, written the espeak way. The wav carries a short comment with its three silences and a name for the voice that spoke it, and no plaintext. Encoding refuses to run until there is a calibration made with that voice, and decoding refuses a wav whose voice the calibration was not made with.

The cipher is spoken by Piper, with the voice and settings in the `cipher` section of [`enochaeon.json`](../enochaeon.json). Each letter sound is spoken alone. A silence of `letter_ms` follows a letter, one of `word_ms` stands between two words, and one of `line_ms` between two lines. The length of a silence is all that says where a word or a line ends, and that is how line breaks come back. `noise_scale` and `noise_w_scale` are Piper's two kinds of chance, in the sound and in how long each phoneme is held. At zero the voice says a string the same way every time.

Hearing uses `facebook/wav2vec2-lv-60-espeak-cv-ft`, a model that writes the phones it hears. It does not write a lone letter sound reliably. The same sound moved by a few milliseconds can come out as other phones, and several letters come out as the same phones. So a letter is not told by the phones the model writes. It is told by what the model gives at each step of the sound before it picks a phone: a share for every phone it knows. Two sounds are close when their steps give their shares to the same phones, and one sound may be held longer than the other.

`enochaeon calibrate` speaks every letter sound alone with the cipher's voice, cuts it out the way a letter is cut out of a recording, and stores what the model gives for it. [`src/enochaeon/data/calibration.json`](../src/enochaeon/data/calibration.json) lists the sounds and names the voice, and `calibration.npy` beside it has the steps. Before anything is written, every letter sound is spoken in one row and read back. If a letter comes back as another letter, calibration names the two and writes nothing: change the string for one of them in the key and calibrate again. Calibrate again after any change to the `cipher` section.

`enochaeon notes.wav` cuts the recording at its silences into lines, words and letters. Each letter is cut again from its first loud sample to its last, so the same sound reaches the model the same way wherever it stands. It is heard alone and taken for the letter whose calibrated sound is nearest. The key then turns the letters back into English, and the text is written as `notes.decoded.txt`. No word list corrects it. What comes back is what the letters spell, so a name or a word that is not English comes back as it was written.

A wav with no comment is still decoded, with a warning, using the silences in `enochaeon.json`. A wav that carries the comment of a spoken Call or of the earlier espeak cipher is refused.

What has been tried is a wav the tool wrote, read back from disk. The pangram, [`example/the-owl-and-the-cat.txt`](../example/the-owl-and-the-cat.txt) and a third text of 145 words each came back with every word and every line break. A recording played aloud and recorded again has not been tried. Noise in the voice costs words. In a trial with both noise settings at 0.2, 202 of the 226 words of the second text came back, and with John's own settings 101 did.

The cipher reads the `cipher` section of `enochaeon.json`. It does not read the `calls` section, the lexicon, or a Call file, and Calls and translate do not read the `cipher` section.

| File | Role |
| --- | --- |
| `enochaeon.json` | The `cipher` section: the voice, how it is run, the three silences, and how a letter is cut out |
| `src/enochaeon/data/alphabet.json` | Hebrew and Enochian for each English spelling, the letter sounds, and what the voice is given for each sound |
| `src/enochaeon/data/calibration.json` | The letter sounds that were calibrated, and the name of the voice that spoke them. Written by `enochaeon calibrate` |
| `src/enochaeon/data/calibration.npy` | What the recognizer gives for each of those sounds, step by step. Written by `enochaeon calibrate` |
| `tools/cipher/voice-sounds.py` | Writes a voice's field into the key from the method file beside it. A string that is already there is kept |
| `src/enochaeon/alphabet.py` | Loads the key and applies the length rule |
| `src/enochaeon/cipher_voice.py` | Piper, one letter sound at a time, and the comment written into the wav |
| `src/enochaeon/encode.py` | Stage files and the cipher wav |
| `src/enochaeon/decode.py` | Cuts the wav into letters, tells each one, and reads it back into English |
| `src/enochaeon/calibrate.py` | Builds the two calibration files |
| `src/enochaeon/recognize.py` | The phone recognizer |
| `src/enochaeon/config.py` | Reads `enochaeon.json` |

The cipher was first spoken by espeak, one breath for each word, and read back by matching the phones the model wrote and then correcting each word against an English word list. `src/enochaeon/match.py`, `src/enochaeon/lexicon.py` and `src/enochaeon/data/words.txt` are from that way of reading. They are still in the repository and the cipher no longer uses them. `src/enochaeon/synthesize.py` is espeak-ng, and a Call still uses it when `calls.engine` is `espeak`.

## The lexicon

Calls and translation both read [`calls/lexicon.json`](../calls/lexicon.json). The cipher does not. One entry is a root, the other spellings of that root, the English words it answers to, and two pronunciations.

```json
{
  "root": "BALT",
  "variants": ["BALTIM", "BALTOH", "BALZIZRAS"],
  "pos": "noun",
  "english_glosses": ["justice", "righteousness", "judgment"],
  "hebrew_skeleton": "ב-א-ל-ת",
  "dee_ipa": {
    "BALT": "/b.æ.l.t/",
    "BALTIM": "/b.æ.l.t.ɪ.m/",
    "BALTOH": "/b.æ.l.t.ɒ.h/",
    "BALZIZRAS": "/b.æ.l.z.ɪ.z.r.æ.s/"
  },
  "golden_dawn_ipa": "",
  "sources": ["Key 1", "Key 5", "Key 11"]
}
```

`root` and `variants` are the spellings. They share the glosses and the part of speech. `english_glosses` are what translation matches. `pos` is the part of speech used when more than one gloss is close. `dee_ipa` lists the Dee reading of each spelling, and the stored string is what is spoken. Each was first made by the letter rule from the letters of that spelling. An entry also has a field for the Piper voice, named in `calls.piper.ipa`, which lists what that voice is given for each spelling. `golden_dawn_ipa` is empty. `calls.ipa` chooses which reading is spoken. `hebrew_skeleton` and `sources` stay in the file and are not read. How the Dee reading is made is [dee-ipa.md](dee-ipa.md).

A Call looks up the spelling that is written. `Iad` is this entry, and it is spoken `/j.æ.d/`:

```json
{
  "root": "IAD",
  "variants": ["IAD", "IADO"],
  "pos": "noun",
  "english_glosses": ["God", "the Divine"],
  "dee_ipa": {"IAD": "/j.æ.d/", "IADO": "/j.æ.d.oʊ/"},
  "dee_ipa_piper_john": {"IAD": "/jˈaːd/", "IADO": "/jadoʊ/"},
  "golden_dawn_ipa": ""
}
```

`iado` is spoken `/j.æ.d.oʊ/`, the string stored for that spelling. The Piper voice John is given the strings in `dee_ipa_piper_john`. `Mad` is a different entry, `/m.æ.d/`, even though it also lists `God`. A Call that says `Iad` does not become `Mad`.

Translation starts from the English. `justice` is an exact gloss of the `balt` family, so the trace writes `balzizras`, the spelling that appears in the most Call files. The wav speaks `/b.æ.l.z.ɪ.z.r.æ.s/`, the string stored for `balzizras`. `fire` is an exact gloss of `prge`, whose `dee_ipa` is `/p.r.ɡ.eɪ/`.

`Speak foobar into the fire.` is written `camliax [foobar] a manin prge.`

- `speak` is an exact gloss of `camliax`.
- `foobar` scores 0.417 against the nearest gloss, under 0.50, so it stays in brackets and is left out of the wav.
- `into` is nearest to `in`, a gloss of `a`, at 0.761.
- `the` is nearest to `the mind`, a gloss of `manin`, at 0.549.
- `fire` is an exact gloss of `prge`.

## Calls

A file in [`calls/`](../calls) is already Enochian, written in Dee's Latin letters. `01.txt` through `18.txt` are the first eighteen Keys. `19-lil.txt` through `48-tex.txt` are the Call of the Aethyrs, the same words with that aethyr's name. The words of these forty-eight files are the words in [`calls/journal/`](../calls/journal), and [call-texts.md](call-texts.md) says where they come from. Nothing in a Call is transliterated into Hebrew or into the English cipher.

`enochaeon calls` speaks every `.txt` in `./calls`. `enochaeon calls calls/01.txt` speaks one file. Each file gets a sibling `.wav`. A spelling is looked up in the lexicon, and the field named by `calls.ipa` is what is spoken. A spelling with no reading is left out of the recording and printed. A file with no readable word writes no wav.

`dee_ipa` is the string the lexicon has for the spelling that is written. [dee-ipa.md](dee-ipa.md) is how that string was made, and where it can still disagree with the syllables Dee wrote in the margins. `golden_dawn_ipa` is empty. Calls 49 and 50 are not part of Dee's forty-eight Keys. Only the 50th call has English for its new spellings, from Crowley's footnote.

Piper speaks the IPA. espeak speaks phonemes derived from that same string. `calls.engine` in [`enochaeon.json`](../enochaeon.json) chooses which one. `--engine espeak` or `--engine piper` overrides that for one Call run. `calls.piper.voice` is John's model, downloaded into `scratch/piper-voices/`. `calls.piper.length_scale` is how long Piper holds each phoneme. `1.0` is conversational, and higher is slower. `calls.piper.word_ms` is the silence between Piper breaths. espeak keeps 600 milliseconds between words. A Call wav carries the same gap comment as a cipher wav.

A comma stays on the line, and a period starts a new line.

| File | Role |
| --- | --- |
| `calls/*.txt` | Dee's Latin spellings |
| `calls/lexicon.json` | Gloss, part of speech, `dee_ipa`, the Piper voice's field, and `golden_dawn_ipa` for each root and variant |
| `enochaeon.json` | Engine, IPA field, Piper voice, length, and the Piper gap |
| `scratch/piper-voices/` | John's voice. The download creates this directory. It is not in git |
| `src/enochaeon/enochian.py` | Reads a Call file and leaves out a spelling with no reading |
| `src/enochaeon/roots.py` | Loads the lexicon |
| `src/enochaeon/word_ipa.py` | Turns the stored IPA into Piper or espeak phonemes |
| `src/enochaeon/piper_voice.py` | Piper |
| `src/enochaeon/config.py` | Reads `enochaeon.json` |

## Translate

`enochaeon translate ritual.txt` speaks an English phrase as Call words. This is not the cipher, and the wav is not read back. The command writes `ritual.wav` beside the source, and `ritual.html` beside that wav, showing the spoken spellings in Enochian letters and playing the recording. `.enochaeon/ritual-enochian.txt` lists the Call words that wav speaks. There is no Hebrew file and no phonetic file. The wav uses the same `calls.ipa` reading as the Calls, and the same voice in `enochaeon.json`.

An exact gloss wins, and it does not ask the model. A gloss may cover up to four English words. Otherwise the phrase is compared with the English glosses in the lexicon by `all-MiniLM-L6-v2`. A score under 0.50 is left unmatched. Among the glosses at or above that line, the one with the same part of speech is spoken. If no gloss of that part clears the line, the highest score is spoken. The part of speech comes from `nltk`.

Several spellings can share one gloss. The spelling that appears in the most Call files is the one written, then the shortest, then alphabetical order. The Dee reading of that spelling is the string stored for it. The lexicon section shows this for `justice` and for `Speak foobar into the fire.`

An English word with nothing close stays in the Enochian file in brackets and is left out of the wav. It is also printed as left out. A file with no Call word writes no wav and no trace. The translation wav carries no gap comment.

| File | Role |
| --- | --- |
| `calls/lexicon.json` | The English glosses and the pronunciation |
| `calls/*.txt` | Counted when several spellings share a gloss |
| `enochaeon.json` | The same voice the Calls use |
| `src/enochaeon/translate.py` | Matches the phrase and writes the Enochian trace |
| `src/enochaeon/roots.py` | Loads the glosses |

## Sources

The syllable rule comes from Aaron Leitch's reading of John Dee's phonetic notes: a vowel followed by a consonant in its syllable is short, a vowel left open is long, and a letter standing alone takes its letter-name. He states that rule in the pronunciation essay ["Angelical Pronunciation"](http://kheph777.tripod.com/art_angelical_pronunciation.pdf) and again in the introduction to *The Angelical Language, Volume II: An Encyclopedic Lexicon of the Tongue of Angels* (Llewellyn, 2010). This program applies it to a whole English word on the cipher path. It does not use Dee's syllable divisions. *Volume I: The Complete History and Mythos of the Tongue of Angels* (Llewellyn, 2010) is the account of the alphabet this key follows: Dee's letter names, the Hebrew letter each one answers to, the correspondence used by the Golden Dawn, and the Latin letters Leitch reads. None of Leitch's prose is copied here. The cipher does not include the lexicon, the glosses, or Leitch's own phonetic spellings from that book.

The texts in `calls/` are Dee's forty-eight Keys. Their words are the words of Dee's own manuscript of the Keys, British Library MS Sloane 3191, as it was read from a scan. Each word is in [`calls/sloane/`](../calls/sloane). The reading is one reading by eye and has not been confirmed. The second source is Dee's journal as Meric Casaubon printed it in *A True & Faithful Relation of What Passed for Many Yeers Between Dr. John Dee ... and Some Spirits* (London, 1659). The printing was read in the keyed transcription made by the Text Creation Partnership (EEBO-TCP Phase 1, text A37412), which the Partnership releases under Creative Commons 0 1.0 Universal. It is kept unchanged as [`casaubon-1659-true-and-faithful-relation.xml`](casaubon-1659-true-and-faithful-relation.xml). Each word of the printing, with its page, Dee's note and a status, is in [`calls/journal/`](../calls/journal). The journal does not decide the spelling of a call. It is kept for Dee's notes and to show where the two sources differ. [call-texts.md](call-texts.md) describes both records and lists every uncertain word.

Calls 49 and 50 are not part of those Keys; their new spellings have a `dee_ipa` made by the letter rule, and only the 50th call has English, from Crowley's footnote. The texts are not taken from Leitch's lexicon. The glosses and the two pronunciations used by Calls and translate are [`calls/lexicon.json`](../calls/lexicon.json).

The word list in `src/enochaeon/data/words.txt`, which the cipher no longer uses, is American SCOWL, size 50: the English and American `words` lists through that size, lowercased to ASCII letters. Proper names, abbreviations, contractions, and the uppercase lists are not included. SCOWL is Copyright 2000-2018 by Kevin Atkinson.

> Permission to use, copy, modify, distribute and sell these word lists, the associated scripts, the output created from the scripts, and its documentation for any purpose is hereby granted without fee, provided that the above copyright notice appears in all copies and that both that copyright notice and this permission notice appear in supporting documentation. Kevin Atkinson makes no representations about the suitability of this array for any purpose. It is provided "as is" without express or implied warranty.

The list is built with the inflection data and the American spelling variants, so the WordNet 1.6 notice (Copyright 1997 by Princeton University), the VarCon notices, and Geoff Kuenning's Ispell terms apply as well. Those notices are reproduced in full in `src/enochaeon/data/SCOWL-Copyright.txt`, which is installed with the package. The same permission notice is at the top of `src/enochaeon/data/words.txt`.


## Theory

The 48 Calls also known as Keys are in sympatico with the 50 Gates of Understanding. The term understanding is literally the meaning of the third sephiroth Binah, the Great Mother. She is the Fiftieth Gate. This means that the lower seven sephiroth are the source of the 49 gates, the lower seven multipled by themselves. Thus the first gate is **Malkuth of Malkuth**, the second is **Malkuth of Yesod**, and the 49th is **Chesed of Chesed**. Between the 49th gate and the 50th is the Abyss. Attainment of the 50th is akin to advancement into those Supernal spheres. In the Hermetic Order of the Golden Dawn it was speculated that mortal men and women could not attain to these heights but were the realm of the Secret Chiefs or the Masters. Tradition says that even the 50th Gate was beyond Moses. One question is where is the 49th and the 50th Enochian Key?

Dee recorded the explanation of the 49 Tables of Liber Loagaeth and how they correspond to the 48 practical Angelic Keys (or Calls), explaining that the 49th gate remains completely closed to humanity:

*“I am therefore to instruct and inform you, according to your doctrine delivered, which is contained in 49 Tables. In 49 voices, or callings: which are the Natural Keys to open those, not 49 but 48 (for one is not to be opened) Gates of Understanding; whereby you shall have knowledge to move every Gate...”*

It is my belief that [Aleister Crowley](https://en.wikipedia.org/wiki/Aleister_Crowley) discovered the 49th key during the Amalantrah Working in New York. At the end of this ritual is this barbarous incantation:

> Ol! Altathiera zazare tofaa Miwela rono darala zabaa Re! Re! zacar tofaa marada Ata bewela to rafor rom kalom Bawa! Bawa!
Ol! ata ludu to rafor balong Um -- zala mala tummri charlo (krory) <<?krong>> Upala forlo marana palaa Bewala Rela ra tofor banaa Bawa! Bawa!
Upmara rada tofagile kor Nara dala tofare caralor Mewa topi dodalare tomaa Utta bewale no ropi garaa Bawa! Bawa!
Ol kore kore kunura coralo Bajil ke -- n -- Ol rafutala pilo Mawa bewala radara kolat Mawalado peruba korabat Bawa! Bawa!

There are five words, like zacar, that are found within the Enochian Calls. I am sure it would be controversial amongst Enochian scholars to claim that this verse is Enochian, including new words not found in the original Calls. Just as it would be controversial to Kabbalists to claim that the Enochian *Keys* unlock the 48 *Gates*.

<img src="imgs/Lam.png" alt="Lam" width="320">

Around the time of the Amalantrah Working, Crowley drew the portrait of Lam, who bears a strong resemblence to the Grey aliens of UFO lore. Kenneth Grant speculated that Lam was connected with the Amalantrah Working. I think a key supporting this is the Tibetan letters at the bottom of the Lam portrait that appear to be a stylized rendering of the number 49! Lam I would argue is the key to understanding the cryptic expression from Amalantrah, "It's all in the egg". The solution to this enigma is found in the expression itself. What is in the egg, the All, i.e. Pan. The goat god represented generation and creation. It was the original Goat of Mendes, that replaced, under Greek rule, the Egyptian *ram* god Banebdjedet, who was also a god of procreation, generation. Pan is equivilant of Eros, and also the Orphic god of light Phanes that emerges from the cosmic egg. The shape of Lam's head further alludes to this riddle. The egg is the quintesence, the cosmic egg that proceeds the Big Bang.

The 50th key, the final missing key, I think is found in the vision of the Aethyr of ZAA. In it appears this incantation:

> ARARNAY OBOLO MAHARNA TUTULU NOM LAHARA EN NEDIEZO LO SAD FONUSA SOBANA ARANA BINUF LA LA LA ARPAZNA UOHULU

In a footnote Crowley interprets it to mean:

*Hither, O Holy one/ whose burden pulls at thy spine/ Ho! Ho! Ho! The two-headed God (Janus) ploughs thy back/ sows habitations upon thy back/ thou many-phallused queen/ of princely loves/ which are all sodomies/ so that the holy ones laugh and shake with laughter/ while the lords of mischief/ spend upon thee/ TUTULU (this word cannot be translated. See Liber VII). down bounces from thy back/ the merry mad foetus-faces/ an emission/ Gather ye sun-roses, sun-roses gather ye from the split backside of the Virgin (Earth).*

The only word not translated is **Tutulu**. I refer to this incantation as the Call of [Tutulu](https://www.hplovecraft.com/writings/texts/fiction/cc.aspx). This is the Call of the Abyss, the final Gate to the Beyond.