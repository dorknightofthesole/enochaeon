# The Dee reading

`dee_ipa` is stored in [`calls/lexicon.json`](../calls/lexicon.json) for every spelling, and the stored string is what is spoken. The lexicon is the one place that says how a word is said. Each string was first made by the letter rule in [src/enochaeon/enochian.py](../src/enochaeon/enochian.py) and [src/enochaeon/alphabet.py](../src/enochaeon/alphabet.py), written as the slash IPA that [src/enochaeon/word_ipa.py](../src/enochaeon/word_ipa.py) reads. The speech code does not run that rule. It is not a transcription of the syllables Dee wrote beside the words. Those notes, as the 1659 printing has them, are in [`calls/journal/`](../calls/journal), and this rule does not read them. Two entries are the exception, and they are described under [Where Dee's note is used](#where-dees-note-is-used). It is not Aaron Leitch's dictionary, and it is not the Golden Dawn reading.

`golden_dawn_ipa` is an empty string on every entry. The strings that used to be there were not one published rule. A later reading can fill that column from Aleister Crowley's *Liber LXXXIV vel Chanokh* as printed in *The Equinox* I:7 (March 1912) and I:8 (September 1912). That printing is in the public domain in the United States and the United Kingdom. A later transcription or added note is not that printing. Israel Regardie's *The Golden Dawn* is not the source. Until that reading is done, a call set to `golden_dawn_ipa` has nothing to speak.

## The letter rule

The rule is how a spelling gets its first `dee_ipa`. [tools/lexicon/letter-readings.py](../tools/lexicon/letter-readings.py) runs it for any spelling in the lexicon that has no string, and leaves a spelling that has one alone. The table of sounds below is [src/enochaeon/data/call_letters.json](../src/enochaeon/data/call_letters.json).

`phonetic_text` reads Dee's Latin letters. A word-initial `I` before a vowel is `Y`, so `Iad` is `j a d`. `J` is the vowel `I`. `C` and `K` are both `k`. `V` is the consonant `v`. This is the call alphabet, not the English cipher, where `V` is the vowel `o`.

`syllable_forms` then chooses the sound of each vowel. A vowel with a consonant before the next vowel is short. Any other vowel is long. A word with no vowel is the letter-names, joined.

| Letter | In a word | Letter-name | Long vowel |
| --- | --- | --- | --- |
| A | a | A: | A: |
| E | E | eI | eI |
| I | I | i: | i: |
| J | I | i: | i: |
| O | Q | oU | oU |
| U | U | u: | u: |
| B | b | b'i: | |
| C | k | k'i: | |
| D | d | d'i: | |
| F | f | 'Ef | |
| G | g | g'i: | |
| H | h | h'eI | |
| K | k | k'eI | |
| L | l | 'El | |
| M | m | 'Em | |
| N | n | 'En | |
| P | p | p'i: | |
| Q | kw | kw'A: | |
| R | r | 'Ar | |
| S | s | 'Es | |
| T | t | t'i: | |
| V | v | v'i: | |
| W | w | w'i: | |
| X | ks | 'Eks | |
| Y | j | j'i: | |
| Z | z | z'i: | |

`letter_ipa` turns that espeak string into slash IPA. Each space-separated token is one piece, joined to the next with a dot. An apostrophe is stress on the vowel of that token. The symbol map is the reverse of the one `espeak_phones` already uses:

| Espeak | IPA |
| --- | --- |
| A: | ɑː |
| A | ɑ |
| i: | iː |
| u: | uː |
| O: | ɔː |
| 3: | ɜː |
| oU | oʊ |
| eI | eɪ |
| aI | aɪ |
| a | æ |
| Q | ɒ |
| O | ɔ |
| @ | ə |
| I | ɪ |
| U | ʊ |
| E | ɛ |
| V | ʌ |
| S | ʃ |
| T | θ |
| N | ŋ |
| g | ɡ |

The other espeak letters, `b d e f h i j k l m n o p r s t u v w z`, stay themselves. `balt` is `b a l t`, stored `/b.æ.l.t/`. `iad` is `j a d`, stored `/j.æ.d/`. `prge` is `p r g eI`, stored `/p.r.ɡ.eɪ/`.

A variant does not wear the root's string. `balzizras` is `/b.æ.l.z.ɪ.z.r.æ.s/`, the letter rule of those letters. The `dee_ipa` field on an entry lists a string for each of its spellings:

```json
"dee_ipa": {
  "IAD": "/j.æ.d/",
  "IADO": "/j.æ.d.oʊ/"
}
```

`load_readings("dee_ipa")` returns those strings as the file has them. A spelling the field does not list has no reading and is left out of a recording. A string changed by hand in the lexicon is the one spoken.

## The check

On the day the strings were stored for every spelling, all 1,019 were compared with what the letter rule says, and they were the same. That was a check of the stored strings against the rule. It is not evidence that a word is said that way.

The tests no longer hold the lexicon to the rule, so a string can be corrected by hand. The inventory test checks that every spelling of every entry has a stored `dee_ipa`, and that every word in a call file has one.

## Where Dee's note is used

A lexicon entry may have `dee_says`: the letters Dee wrote in a note to say how the word sounds. When `letter-readings.py` makes the first string for that entry's root, it applies the letter rule to those letters and not to the spelling. A variant gets the letter rule of its own letters. The note itself is kept in `dee_note`, and where it is printed in `dee_note_source`. The speech code reads none of the three: it reads the stored `dee_ipa`.

Two entries have it. Both are names of Aethyrs, and both notes stand beside the name in the list of the thirty on page 209 of the 1659 printing. They are the only two names in that list with a note.

| Name | Dee's note | `dee_says` | `dee_ipa` now | `dee_ipa` before |
| --- | --- | --- | --- | --- |
| `ICH` | "ik." | `ik` | `/ɪ.k/` | `/ɪ.k.h/` |
| `CHR` | "kar in palato very much. ...." | `kar` | `/k.æ.r/` | `/kˈiː.hˈeɪ.ˈɑr/` |

What the notes settle is small. `ICH` has no sound for the h. `CHR` has a vowel between the k and the r, and is not three letter-names.

What they do not settle:

- **The vowels:** the short `ɪ` of `ik` and the short `æ` of `kar` come from the letter rule. Dee's note does not say which a or which i he meant.
- **"in palato very much":** Dee says `kar` is made far back in the mouth. The stored string does not express that.
- **Whether the note is read rightly:** taking "ik." and "kar" as the whole sound of the name is a reading of the note. Nothing else here confirms it.
- **The manuscript:** the notes are from the printing of the journal. The list of names in Sloane 3191 was read for its letters only, and was not searched for notes.

The other 28 names have no note in that list. Their `dee_ipa` is the letter rule and their pronunciation is unknown. `VTA` and `VTI` are `/v.t.ɑː/` and `/v.t.iː/` because the manuscript writes them with V. Dee writes V for a capital U and the printing has `UTA` and `UTI`, so the v sound in those two strings has no evidence behind it. They were left as they are until a rule for u and v is chosen.

No test covers `dee_says` now. The two stored strings are the ones made from the notes, and nothing checks that the notes are read the way Dee meant them.

## What the Piper voice is sent

The lexicon is the one place that says how a word is said. An entry has a second field, `dee_ipa_piper_john`, that lists the string the Piper voice John is given for each spelling of the entry:

```json
"dee_ipa": "/j.æ.d/",
"dee_ipa_piper_john": {
  "IAD": "/jˈaːd/",
  "IADO": "/jadoʊ/"
}
```

`enochaeon.json` names that field in `calls.piper.ipa`. The speech code sends what stands between the slashes and changes nothing. It then adds the mark in `calls.piper.word_end`, a full stop, because each word is one breath and the voice was taught on sentences that end with a stop. A spelling with no string in the field is left out of the recording and named on the screen.

To change how John says a word, change its string in the lexicon. `dee_ipa` stays the reading that says which sounds are meant, and the espeak voice still speaks it.

### How the field was first filled

[tools/lexicon/voice-readings.py](../tools/lexicon/voice-readings.py) wrote the field from `dee_ipa`, following the method typed in [tools/lexicon/piper-john.json](../tools/lexicon/piper-john.json). A spelling that already has a string keeps it, so a string corrected by ear stays corrected. A new lexicon entry has no string until the script is run again.

| The method | Applies to | Why |
| --- | --- | --- |
| Short a is written `a`, where the reading has `æ` | every word | The voice's own English writes the vowel of "bad" as `a`. Given `æ` after `y`, `m` or `b`, it did not open the mouth for the vowel. |
| The vowel has a stress mark | a word with one vowel | The voice shrinks a vowel with no stress. A word with one vowel has nowhere else to put it. |
| A short vowel has a length mark | a word with one vowel | Without the hold the voice clips the vowel, and a final `d` is heard as `t`. |

`iad` was first sent as `[[jæd]]`, and Eddie heard "eead". He heard `[[jˈad]]` as "yet", and `[[jˈaːd.]]` as right.

What rests on what:

- **One word was judged by ear:** `iad`. Every other string in the field is the method's, and no one has listened to it yet.
- **The measure:** [tools/trials/word-onset.py](../tools/trials/word-onset.py) follows the strongest frequency between 150 and 1200 Hz, which is low while the mouth is nearly closed and high when it opens. On `mad`, `zol`, `balt`, `cab` and `toh` the stress mark, the `a` and the full stop made the vowel last longer on all five and open further on four, taking the middle take of five. The length mark added between 30 and 150 ms more on four of the five. It is a measure of the sound and not of what a listener hears.
- **The length mark is for this voice:** it does not say that Dee's vowel was long. `dee_ipa` still has the short vowel.
- **Piper is not the same twice:** five takes of one string differed by up to 270 ms in length.

A word with more than one vowel has the `a` and no stress mark. Where its stress falls is not known, and Dee's accents mark only some words. Given with no stress, its vowels are the shrunk ones. [tools/trials/long-word-weight.py](../tools/trials/long-word-weight.py) says such words with a stress mark on every vowel, which picks no syllable. Eddie listened to the first twelve longer words of Call 1 in three forms: as the lexicon has them, with a stress mark on every vowel, and with the short vowels also held. He kept the lexicon's form for now. That is a choice of what to use, made on twelve words. It does not say the longer words are pronounced correctly: where their stress falls is still unknown.

### What the code works out

Nothing about how a word is said. Every reading a voice speaks is a string in the lexicon. The code still does two things to a stored string, and neither adds a sound:

- **For espeak:** `espeak_phones` rewrites a `dee_ipa` string in the letters espeak takes, one for one.
- **For a Piper voice with no field of its own:** `piper_phones` rewrites it in the letters Piper takes, one for one. John has a field, so this is not used for John.

The letter rule and its table are still in the package, and only the scripts in `tools/` run them.

## Where the pronunciation can still be wrong

The rule closes a vowel when any consonant stands before the next vowel. Dee's margins divide the syllables, and a different break changes the length. `balt` is short `æ` here because `l` follows the `a`. A margin that put the break after the `a` would make that vowel long. This column does not have those breaks, so it does not claim to be his.

The English files in `calls/english` are not paired with the Enochian words. Call 1 has 86 Enochian words and 168 English words, and calls 1 through 19 are split the same way. The spellings that were missing from the lexicon have an empty `english_glosses` list. No meaning was filled in.

A spelling that contains `A`, `E`, `I`, `J`, `O`, or `U` is spoken as syllables. `Y` is a consonant. The vowel lengths are the letter rule. The rule does not read Dee's notes, so those lengths are unknown.

A spelling with none of those six letters is spoken as the letter-names in the table above, joined. Those names are the English alphabet names: `D` is `d'i:` ("dee") and `S` is `'Es` ("ess"). In the first call `ds` occurs five times, and the recording says "dee ess." The pronunciation of a spelling with no vowel is unknown. The recording spells English letter-names because the table has no vowel to speak.

The spellings in the call files are the ones in Dee's manuscript Sloane 3191, as it was read. [call-texts.md](call-texts.md) describes them, and lists Dee's notes from the 1659 printing of his journal beside each word where the printing has one. Apart from the two names above, those notes are not used by this rule.

The name of `R` is `'Ar`. That `A` is stored as bare `ɑ`. espeak does not voice bare `A`: `[[A]]` is silent, and `[['A r]]` comes out as `r`. An espeak recording of a vowelless spelling that contains `R` loses the vowel of that letter-name. Piper speaks the same `ɑ`, and holds it when `R` is the whole word. The stored string matches the letter rule. That match is a check of the code.

## Confidence

Every stored `dee_ipa` was the letter rule's string when it was stored, applied to the spelling or, for `ICH` and `CHR`, to the letters of Dee's note. That is a check of the strings against the rule.

The pronunciation is unknown. Apart from `ICH` and `CHR`, this rule does not use Dee's notes, and a number without them would be a guess. For those two names the note gives the consonants and no more. A spelling with no vowel is unknown for the further reason above: it is spoken as English letter-names.
