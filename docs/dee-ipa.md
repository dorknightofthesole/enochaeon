# The Dee reading

`dee_ipa` is the letter rule in [src/enochaeon/enochian.py](../src/enochaeon/enochian.py) and [src/enochaeon/alphabet.py](../src/enochaeon/alphabet.py), written as the slash IPA that [src/enochaeon/word_ipa.py](../src/enochaeon/word_ipa.py) speaks. It is not a transcription of the syllables Dee wrote in the margins. Those breaks are not in this repo. It is not Aaron Leitch's dictionary, and it is not the Golden Dawn reading.

`golden_dawn_ipa` is an empty string on every entry. The strings that used to be there were not one published rule. A later reading can fill that column from Aleister Crowley's *Liber LXXXIV vel Chanokh* as printed in *The Equinox* I:7 (March 1912) and I:8 (September 1912). That printing is in the public domain in the United States and the United Kingdom. A later transcription or added note is not that printing. Israel Regardie's *The Golden Dawn* is not the source. Until that reading is done, a call set to `golden_dawn_ipa` has nothing to speak.

## The letter rule

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

A variant does not wear the root's string. `balzizras` is `/b.æ.l.z.ɪ.z.r.æ.s/`, the letter rule of those letters. The `dee_ipa` field on an entry is the root. `load_readings("dee_ipa")` builds the reading of each spelling from `letter_ipa`.

## The check

For every spelling, `espeak_phones` of the Dee reading must equal `phonetic_text`, once spaces are removed. Letter-names are written without a space inside the name, and `espeak_phones` puts a space between phonemes, so `n` is stored `/ˈɛn/` and comes back as `'E n`. The sounds are the same token. The inventory test checks this for every call spelling, and it checks that the stored root string is that same reading.

## Where the pronunciation can still be wrong

The rule closes a vowel when any consonant stands before the next vowel. Dee's margins divide the syllables, and a different break changes the length. `balt` is short `æ` here because `l` follows the `a`. A margin that put the break after the `a` would make that vowel long. This column does not have those breaks, so it does not claim to be his.

The English files in `calls/english` are not paired with the Enochian words. Call 1 has 86 Enochian words and 168 English words, and calls 1 through 19 are split the same way. The spellings that were missing from the lexicon have an empty `english_glosses` list. No meaning was filled in.

A spelling that contains `A`, `E`, `I`, `J`, `O`, or `U` is spoken as syllables. `Y` is a consonant. The vowel lengths are the letter rule. Dee's margin breaks are not in this repo, so those lengths are unknown.

A spelling with none of those six letters is spoken as the letter-names in the table above, joined. Those names are the English alphabet names: `D` is `d'i:` ("dee"), `S` is `'Es` ("ess"), `V` is `v'i:` ("vee"), `R` is `'Ar` ("ar"), `B` is `b'i:` ("bee"). Twenty spellings in the Call files are in this group. In the first call, `ds` occurs five times and `vrbs` once. The recording says "dee ess" and "vee ar bee ess."

| Spelling | Calls |
| --- | --- |
| `chr` | 38-chr |
| `crpl` | 04 |
| `d` | 06 |
| `ds` | 01, 05, 08–11, 13–16, 18, and 19-lil through 48-tex |
| `dst` | 03, 04 |
| `f` | 04 |
| `g` | 03, 04, 06 |
| `l` | 02, 05, 10, and 19-lil through 48-tex |
| `n` | 49 |
| `p` | 09 |
| `pd` | 04 |
| `q` | 03, and 19-lil through 48-tex |
| `symp` | 19-lil through 48-tex |
| `vls` | 05 |
| `vml` | 19-lil through 48-tex |
| `vndl` | 03 |
| `vrbs` | 01 |
| `vx` | 13 |
| `yls` | 16 |
| `z` | 09, 11 |

The pronunciation of these twenty spellings is unknown. The published statement this program is using is that a letter standing alone takes its letter-name. Eight of these spellings are one letter: `d`, `f`, `g`, `l`, `n`, `p`, `q`, and `z`. The other twelve are words. Both groups are spoken with the English names in the table. No published pronunciation of these spellings was used, and Dee's margin notes for them are not here.

The name of `R` is `'Ar`. That `A` is stored as bare `ɑ`. espeak does not voice bare `A`: `[[A]]` is silent, and `[['A r]]` comes out as `r`. An espeak recording of a vowelless spelling that contains `R` loses the vowel of that letter-name. Piper speaks the same `ɑ`. The stored string matches the letter rule. That match is a check of the code.

## Confidence

Every `dee_ipa` matches this rule. The check above passed for every root, every variant, and every spelling in the call files. That is a check of the code.

The pronunciation is unknown. The margin syllables are not here, and a number without them would be a guess. The twenty spellings with no vowel are unknown for the further reason above: they are spoken as English letter-names, and no published pronunciation of those spellings was used.
