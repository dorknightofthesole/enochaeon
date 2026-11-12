# Notes on the analysis of the calls

Written on November 11, 2026, at the end of the pass that rewrote the call files from Dee's journal. These are the notes of that analysis as they were reported. The full lists are in [call-texts.md](call-texts.md).

All the to-dos in the plan are done. Nothing is committed, no wav was regenerated, and the plan file is untouched. The tests pass (60, including the new one that checks every call file against `calls/journal/`).

The one thing that needs your decision before any recording: by my unconfirmed reading of Sloane 3191, Dee's manuscript disagrees with the 1659 printing in about 30 spellings. In most of those the manuscript has the spelling the call files had before this rewrite.

## Uncertain words

Of 1,103 words in the journal data (counting the thirty names), 143 are uncertain. The full list is in `docs/call-texts.md`.

| Status | Count | What it means |
| --- | --- | --- |
| `from_note` | 70 | The printed letter column has dots or is empty; letters come from Dee's note |
| `not_printed` | 56 | The printing does not have the word; the spelling is the old call file's and has no source |
| `conflict` | 16 | Two places in the printing give different letters |
| `gap` | 1 | The column is unreadable; letters come from Dee's note (`OALI`, Call 4) |

The 56 `not_printed` words are all of calls 14 and 15, the first twelve words of call 16, and `AAI GROSB` in call 13.

A second list in the same doc has 38 words where the column is readable but Dee's note spells different letters. The call files follow the column there.

## Sloane 3191 against the journal data

The scan is the whole manuscript, including calls 14, 15 and 16 in full. I read all eighteen calls, the Aethyr call and the thirty names: 1,027 words agree, 74 differ, 2 have a letter I could not settle. Of the 74, 24 are only u/v or i/j/y, 9 are only word division, and the rest are below.

| Call | Journal data | Sloane, as I read it |
| --- | --- | --- |
| 1 | `UL`, `ZOMDV` | Lu, zomd |
| 2 | `IALPURG` | ialprg |
| 3 | `TAPVIN`, `HAALA`, `VOMZARG` | tapuim, aala, vomsarg |
| 4 | `DO`, `FGAOSGA`, `RESTIL` | od, F caosga, rest-el |
| 5 | `DUIV`, `TAQANIS`, `PIRIPSOL` | duib, taquanis, peripsol |
| 6 | `MALPURG`, `FBLIARD` | malprg, tbliard with "f-bliard" written beneath |
| 7 | `PARADIZ`, `ZONAR` | paradizod, zonac |
| 8 | `AZIAGIAR` | aziagier |
| 9 | `PURGEL`, `ASOBAMA` | prgel, a sobam |
| 10 | `OP VIRQ`; nothing after `YOLCI` | virq op; "matb" after yolci, with 1000 above it |
| 12 | `GOHUS ZAMRAN` | gohus od ZAMRAN |
| 13–18 | ending `ZACARE CA OD ZAMRAN` | ZACAR od ZAMRAN |
| 15 | `VPHAAI`, `DSOCIDO` | vpaahi; "dsocido" or "dsoado", not settled |
| 17 | `DIALPERT`, `TAXS` | dialprt, Faxs |
| 18 | `QZMOZ` | MOZ |
| Aethyrs | `MADRIIAX` (first word), `CHI`, `PIRIPSOL`, `PIRIPSAX`, `AGLTOLTORN` | Madriax, chis, peripsol, perip sax, Ag L tor torn |

- **No-source words:** the other 54 `not_printed` words agree with the manuscript as I read it; only `VPHAAI` and `DSOCIDO` do not.
- **Dee's notes:** several manuscript spellings match Dee's note in the printing where the note and the column disagree (aala, vomsarg, od, rest-el, taquanis, aziagier, a sobam, chis, peripsol).
- **How far to trust it:** this is one reading by eye of handwriting on microfilm. I re-examined at full size only the words that differ, so the agreeing words may be helped by my knowing what to expect. Word division is the least certain part.
- **Not read:** the second copy of the thirty names, in the circle diagram.
- **Where it is:** [`sloane-diff.txt`](sloane-diff.txt), with a sheet per call in `scratch/sloane-check/`. It changed no call file and added no `sloane` field.

## Where I departed from the plan

- **Extra status and fields:** I added `not_printed` and several per-word fields (`column`, `remark`, `read_from`, `repeat_of` and others), all described in the doc.
- **Arrangement of calls 12, 13, 16 and 17:** the printing runs pieces of these together on pp. 134–137. I placed them using Dee's list on p. 200 and his margins on pp. 193–194; that arrangement is my reading.
- **Endings of calls 11–18:** these are repeated from Call 1, because the journal says "Move, as before" and does not spell them. The manuscript writes them differently for 13–18 (see the table).
- **Keying errors:** I corrected 36 places in the keyed transcription from page images of the same printing, and read pp. 132–133 (missing from the transcription) from those images. The XML is unchanged.
- **Punctuation:** carried over mechanically; two commas moved because the journal joins the words they stood between.
- **Renamed files:** `23-lit.txt`, `32-uta.txt`, `43-uti.txt`. The old `23-lat.wav`, `32-vta.wav`, `43-vti.wav` are still on disk, and every call wav is now stale.
- **Lexicon:** 110 entries added with no English and a letter-rule `dee_ipa`, which says nothing about how those words are pronounced. 109 spellings are no longer in any call; their entries are kept and listed in `scratch/lexicon-new-spellings-journal.txt`.
- **`docs/dee-ipa.md`:** besides removing the twenty-spellings section, I corrected three sentences that said Dee's notes are not in the repo.

Should the call files stay on the printing's spelling where the manuscript differs, or wait for your own check of the scan before a recording is made?

## Decision: Sloane 3191 first

Added later on November 11, 2026. Everything above this heading is the report as it was given, and it was written while the journal was the first source.

Eddie decided that Sloane 3191 is the text the call files follow. The journal data stays as the second witness and as the record of Dee's notes and English in the printing. This reverses the earlier order, which was the journal first and Sloane as the check.

The switch was made the same day, and it is described under "What the switch did" below. It was made from the reading as it stands, before Eddie's check of the places that differ. What that check finds is entered afterwards.

### Why Sloane is the better source for spelling

- **Whose hand:** Sloane 3191 is in Dee's own hand. The journal reached us as a typesetter's reading of Dee's working notes, printed in 1659. It was then read here in a transcription keyed from microfilm, in which 36 places had to be corrected from page images.
- **Complete:** the printing lacks 56 words. The manuscript has all of them, and 54 agree with the spelling the call files already had.
- **Where the printing disagrees with itself:** in nine of the words that differ, the manuscript has the spelling of Dee's note in the printing and not the spelling of the printed letter column (`aala`, `vomsarg`, `od`, `rest-el`, `taquanis`, `aziagier`, `a sobam`, `chis`, `peripsol`). That points to the column being the misprint in those nine. It is not proof.
- **The state of the printing:** 70 words had dots or blanks in the column and were read from the note, 16 are printed two ways, and one has a gap.

### What is not certain

This is every doubt known on this date. None of it is settled by the code or by the tests.

**About the reading of the manuscript**

- **One reader, once:** the reading in `tools/sloane/sloane-reading.json` is one reading by eye of handwriting on a microfilm scan. Nobody has confirmed it.
- **Words that agree:** 1,027 words agree with the journal data. They were read once, from strips of the page, by a reader who knew what the journal had. Knowing what to expect may have helped a doubtful letter agree. Only the words that differ were looked at again at full size.
- **Two words not settled:** in Call 10 a small faint letter, e or c, stands before `matorb`. In Call 15 the word is `dsocido` or `dsoado`.
- **Word division leans on the journal:** the reading has 166 small gaps with no tie-stroke, where the eye cannot say if a new word begins. The comparison takes such a gap as a word break only where the journal breaks at that very letter. That happened once. The other 165 were left inside the word, which is the journal's division and not an independent reading of the manuscript. With Sloane first, the word division at those 165 gaps still rests on the journal.
- **Tie-strokes:** 141 strokes were read as Dee tying two parts into one word. A stroke missed or wrongly seen changes a word break.
- **Accents:** accents were typed where they were seen. They were not checked a second time and are not compared with anything.
- **u/v and i/j/y:** 24 words differ only in these. No rule has been chosen for how the call files spell them.
- **Notes above the words:** the manuscript has small notes above some words, such as `Ka`, `zod`, `kil`, `dg` and `s`. Some were read and are in the remarks. Several were not read.
- **Notes in the margins:** these were read only in part. The remarks record margin notes in Calls 8, 11 and 16 as not read. Other margin notes, such as those beside Calls 1 and 10, were not recorded at all.
- **The English in the manuscript:** the manuscript writes English above the words. It was not typed out and was not compared with the English in the journal data.
- **The thirty names:** they were read from the numbered list in the margin. The second copy, in the circle on the page before, was not read.

**About which source is right where they differ**

- **Correction or slip:** the manuscript being Dee's hand does not make every difference a correction. `MOZ` for `QZMOZ`, `zomd` for `ZOMDV` and `Lu` for `UL` could be Dee correcting the journal or Dee slipping while copying. Nothing here can tell which.
- **Dee's own alternatives:** in Call 6 the manuscript has `tbliard` with `f-bliard` written beneath it, and in Call 4 a small `i` above the e of `rest-el`. In such a place the manuscript itself gives two spellings, and which one to follow is not decided.
- **The Cotton manuscript:** the manuscript Casaubon printed from has not been seen. The shelfmark given for it in conversation, British Library Cotton MS Appendix XLVI, was from memory and was not verified.

**About sound**

- **Unknown:** nothing in this work says how any word is pronounced. Choosing a spelling does not settle a pronunciation.
- **A correction to what was said in conversation:** it was said that Dee's notes in the journal are the only evidence about sound. That was wrong. The manuscript has notes above words too, as listed above, and they have been read only in part.

**About the record of the work**

- **Enlargements made during the reading:** the pieces of the page that were enlarged to settle hard words were cut with coordinates typed at the command line. The coordinates were not saved. On this date one of those images, `scratch/sloane-pages/zoom/ae-madriax.jpg`, was overwritten by a test and no longer shows what it showed during the reading.
- **What replaces them:** `tools/sloane/sloane-places.json` now records where each place that differs stands on its page, so its image can be cut again. Those boxes were found on this date, after the reading. They are not the images the reading was made from.
- **The lexicon list:** `scratch/lexicon-new-spellings-journal.txt` cannot be made again. Running its script now would add nothing and overwrite the list.
- **Page images of the 1659 printing:** they were downloaded by hand. No script in `tools/` fetches them.

### What the switch did

- **The record:** `tools/sloane/sloane-build.py` makes `calls/sloane/` from the reading and the journal record: 1,102 words counting the thirty names. Each word has its letters, the word as it was typed in the reading, and the journal words at its place. `calls/journal/` is unchanged.
- **The call files:** `calls/01.txt` to `18.txt` and the thirty Aethyr files were written again from `calls/sloane/`. In Calls 1 to 18 and one Aethyr file together, 80 word places changed from the files as the journal had them.
- **Renamed files:** `32-uta.txt` and `43-uti.txt` are `32-vta.txt` and `43-vti.txt` again, because the manuscript writes `Vta` and `Vti`. `23-lit.txt` keeps its name.
- **Words that came in:** `op` after `virq` in Call 10 (the journal has it before), `matb` after `yolci` in Call 10, and `od` between `gohus` and `zamran` in Call 12. The journal agrees that a word is missing from its Call 10: page 192 says against "a thousand", "Math. you have it not." The manuscript has `1000` written above `matb`.
- **Words that went out:** `ca` in the endings of Calls 13 to 18, where the manuscript has `ZACAR od ZAMRAN`.
- **The two words not settled:** they have the journal's letters, `matorb` and `dsocido`, and the status `unsure`.
- **u and v:** the call files have the manuscript's letters as read. Dee writes V for a capital U, so the same word is `torzu` in Call 2 and `torzv` in the Aethyr call.
- **Two spellings at one place:** the call file has the one on the line, `tbliard` in Call 6 and `restel` in Call 4.
- **Word division:** 122 words have a small gap inside them in the manuscript and are one word in the call files because the journal has them as one word. Among them are `odmiam`, `chista`, `gohoiad` and `fcaosga`. This is the weakest part of the text. Settling it needs each gap looked at again in the scan, with the English that Dee wrote above the words.
- **Punctuation:** carried over from the files as they were before either source, as on the first pass.
- **Lexicon:** 10 entries added, with no English and a letter-rule `dee_ipa`, which says nothing about how those words are pronounced. They are listed in `scratch/lexicon-new-spellings-sloane.txt`.
- **Test:** the test now checks every call file against `calls/sloane/`. It is a check of the files against the record of the reading. It is not a check of the reading against the manuscript.
- **Not done:** no wav was made again, and nothing is committed.

### The check that comes next

`tools/sloane/sloane-cut.py` makes the images for Eddie's check. They are kept in `docs/imgs/`, and the script makes them again from the scan.

- **One image per call:** [`imgs/sloane-calls/`](imgs/sloane-calls), `01.jpg` to `18.jpg` and `aethyrs.jpg`, each with its margins. The Aethyr call is on two pages, put one above the other.
- **One image per place that differs:** `imgs/sloane-places/`, with [`index.md`](imgs/sloane-places/index.md) showing each image beside the journal's spelling and the reading. There are 46 images for 55 entries in [sloane-diff.txt](sloane-diff.txt): 50 words that differ in letters, in word division or by being absent, 3 words only the manuscript has, and 2 not settled. Words that stand together share an image.
- **Not given an image:** the 24 words that differ only in u/v or i/j/y.
- **Where the result goes:** `checked` in `tools/sloane/sloane-places.json`, one per place.
