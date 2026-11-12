# The texts of the calls

The words in [`calls/01.txt`](../calls/01.txt) through `18.txt`, and in the thirty Aethyr files, are the words of John Dee's own manuscript of the calls, British Library MS Sloane 3191, as it was read from a scan. Each word is recorded in [`calls/sloane/`](../calls/sloane). The reading is one reading by eye and has not been confirmed.

The second source is Dee's journal as it was printed in 1659. Each of its words is recorded in [`calls/journal/`](../calls/journal) with the page it is printed on, the letters, Dee's note beside it, his English where the journal pairs it with the word, and a status that says how the letters were read. The journal does not decide the spelling of a call file. It is kept for Dee's notes and English, and to show where the two sources differ.

Most of this page describes the journal record, which was made first. The manuscript and the call files are described in the last two sections.

This page is about spelling. It says nothing about how a word is pronounced. The pronunciation of these words is unknown, and [dee-ipa.md](dee-ipa.md) says what the recordings do instead.

## The source

The source is Meric Casaubon, *A True & Faithful Relation of What Passed for Many Yeers Between Dr. John Dee ... and Some Spirits* (London: printed by D. Maxwell for T. Garthwait, 1659). Casaubon printed Dee's journal from the manuscript then in Sir Thomas Cotton's library. The calls are on pages 79 to 138 and 201 to 209. Dee's English for them is on pages 190 to 194 and beside the words of the Aethyr call.

The printing was read in the keyed transcription made by the Text Creation Partnership, EEBO-TCP Phase 1, text A37412. It is saved unchanged as [`casaubon-1659-true-and-faithful-relation.xml`](casaubon-1659-true-and-faithful-relation.xml). The Partnership releases Phase 1 texts under [Creative Commons 0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). The file was downloaded from the Partnership's own repository, [textcreationpartnership/A37412](https://github.com/textcreationpartnership/A37412). The Oxford Text Archive host did not answer.

The transcription was keyed from microfilm images of the Cambridge University Library copy. Pages 132 and 133 are not in it. Those two pages, and every other page of the calls, were read against page images of the same printing: the Internet Archive scan [`truefaithfulrela00deej`](https://archive.org/details/truefaithfulrela00deej). Where the keyers left a gap or keyed a wrong letter and the page image can be read, the word carries `read_from` and a `remark` that gives both readings. The XML file is not changed.

This is a check against the 1659 printing. It is not a check against Dee's handwriting. The printing has its own mistakes, and the journal data keeps them: a word is recorded the way the printing spells it.

## What a word is

A word is one entry in the journal's spelling column. The journal often prints as one entry what other editions print as two or three: `ODZAMRAN`, `CHISMICAOLZ`, `IRGILCHISDA`. The journal record follows the column. The call files follow the manuscript, which divides some of these differently.

Calls 1 to 4 were given backwards, last word first, each word spelled from its last letter to its first. `letters` is the column read from its last letter to its first, and `column` keeps the letters the way they are printed. Calls 5 to 18 and the Aethyr call were given forwards.

`letters` always comes from the spelling column when the column can be read. Dee's note never changes a column that can be read. Where the note spells different letters, the word is on the second list below and the journal record has the column's spelling.

Each file in `calls/journal/` has these fields.

| Field | Meaning |
| --- | --- |
| `call`, `printing`, `pages`, `direction` | Which call, the printing, the pages it is on, and whether it was given `forward` or `backward` |
| `notes` | What the journal says about the call as a whole, and anything that was left out or moved and why |
| `words` | The words in order |
| `names`, `name_word` | In `aethyrs.json` only: the thirty names as page 209 prints them, and the place of the name in `words`, counted from 0 |

Each word has these fields.

| Field | Meaning |
| --- | --- |
| `page` | The page of the 1659 printing. `null` when the printing does not have the word |
| `letters` | The spelling the journal record gives the word |
| `note` | Dee's note beside the word, as printed. A margin note is written `[margin: ...]` |
| `english` | Dee's English, where the journal pairs it with this word. Empty for most of calls 1 to 18, where the English is printed apart from the words |
| `status` | How the letters were read. See the next section |
| `column` | The spelling column exactly as printed, when it is not the same string as `letters` |
| `number` | The number the journal gives the word |
| `row` | The row of the keyed transcription the word was read from, as numbered by `tools/journal/casaubon-dump.py` |
| `other` | Other letters the printing gives for the same word |
| `correction_page` | The page where the journal makes the correction, for a `corrected` word |
| `repeat_of` | The call and word this word repeats, where the journal says to finish as in the first call and does not spell the words again |
| `read_from` | Set when the word, or part of its note, was read from the page image and not from the keyed transcription |
| `remark` | What was done and why, in a sentence |

## What each status means

<!-- counts:start -->
The journal data has 1103 words, counting the thirty Aethyr names: 937 `printed`, 23 `corrected`, 70 `from_note`, 1 `gap`, 16 `conflict`, 56 `not_printed`. 143 are uncertain.
<!-- counts:end -->

| Status | Meaning |
| --- | --- |
| `printed` | The spelling column can be read, and `letters` is that column |
| `corrected` | The journal itself changes the word, and `letters` is the word after the change. `correction_page` says where |
| `from_note` | The spelling column has dots or is empty. The missing letters are read from Dee's note |
| `gap` | The keyers marked the column unreadable, and the page image did not settle it. The letters are read from Dee's note |
| `conflict` | Two places in the printing give different letters for the word. `letters` is one of them and `other` has the rest |
| `not_printed` | The 1659 printing does not have this word. `letters` is the spelling the call file had before the journal was applied. That spelling has no source in the printing |

Nothing is filled in by judgement. A word that is not `printed` or `corrected` is uncertain, and every such word is listed below. `not_printed` is not one of the statuses the plan for this pass named. It was added because the printing turned out not to have fifty-six of the words.

## What the printing does not have

- Calls 14 and 15 are not in the printing. Page 200 lists their first words, `No Romi.` and `Ils Tabaam.`, and pages 193 and 194 give their English.
- Call 16 has only its last nine words, `LUSDAN` to `MADZILODARP`, on page 136. The twelve words before them are not printed.
- Call 13 lacks the two words the call file had after `JUMD`: `AAI GROSB`.
- On pages 134 to 137 the printing runs pieces of calls 12, 13, 16 and 17 together and does not mark where each piece belongs. The pieces are put under their calls by the first words Dee lists on page 200, by his margin notes against the English on pages 193 and 194, and by the order of the English there. That arrangement is a reading of those pages. Each of the four files says in `notes` which words came from which page.
- Calls 11 to 18 do not spell their endings. The journal says to go on as in the first call ("Move, as before"). The words from `ZACARE` to `IAIDA` are repeated from Call 1 and carry `repeat_of`. Call 12 spells its ending as far as `QAA`, with `GOHUS` in it, and only the seven words after `QAA` are repeated.
- Page 192 says against "a thousand" in the English of Call 10: "Math. you have it not." The printing does not say where in the call the word goes, so the journal record does not have it. The manuscript, as it was read, has `matb` after `yolci` in Call 10 with `1000` written above it, and the call file has it there.

## Uncertain words

Every word whose status is not `printed` or `corrected`. "Column" is the spelling column as printed.

<!-- uncertain:start -->
| Call | Word | Page | Status | Spelling | Column | Dee's note | Other letters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Call 1 | 4 | 86 | `conflict` | `GOHO` | `OHOG` | GOTTO. | GOTTO |
| Call 1 | 49 | 85 | `conflict` | `ZNRZA` | `AZRNZ` | Call it Zurza. Δ. As... Znurza. | ZURZA |
| Call 1 | 56 | 84 | `conflict` | `SOBA` | `ABOS` | SOBA. |  |
| Call 1 | 63 | 83 | `conflict` | `ZOMDV` | `XVDMOZ` | [margin: Call it Zome.] With great difficulty this Letter was discerned: Nalvage himself said, he knew it not yet; but it seemed to E. K. to be an X. Nalvage denied it to be an X. and said he knew not yet the mystery: say the Lords prayer, for I cannot open it. Although my power be multiplied, yet I know not this Letter. At length he said it was V. | ZOMDVX, ZOME |
| Call 1 | 67 | 83 | `conflict` | `AAI` | `I, A, A` | AAI. [margin: The first A may be an A an O or an E.] [margin: Those are two words.] | OAI, EAI |
| Call 1 | 70 | 81 | `conflict` | `PIAMOL` | `L, O, M, A, I, P` | this O must be sounded as A. T must be instead of M. [margin: Aversed.] Call it Piamo el. It is Piatel Baltale to be sounded. | PIATOL, PIATEL |
| Call 1 | 75 | 80 | `conflict` | `OD` | `T, O` | [margin: This may be T or D.] Call it OD [margin: or OT.] | OT |
| Call 1 | 82 | 79 | `from_note` | `ZIRDO` | `O, D, R, I` | Call it Zirdo. |  |
| Call 4 | 14 | 110 | `gap` | `OALI` | `[gap:1 word]` | O a li |  |
| Call 5 | 47 | 121 | `conflict` | `FETHARZI` | `S. FETHARZI` | Feth ár zi. | SFETHARZI |
| Call 5 | 54 | 121 | `from_note` | `GEJAD` | `............` | ie in as ien tle iad-as iade.; Ge jad. |  |
| Call 5 | 55 | 121 | `from_note` | `IL` |  | i l. |  |
| Call 6 | 3 | 121 | `from_note` | `CHIS` | `— HIS` | Chis. |  |
| Call 6 | 35 | 123 | `from_note` | `ZACAM` | `ZAC .. AM` | Za cam. |  |
| Call 7 | 3 | 123 | `from_note` | `PARADIZ` | `PARA .. IZ` | Pa ra di zod. |  |
| Call 7 | 18 | 124 | `from_note` | `ZONAR` | `ZONA ..` | Zo nar. |  |
| Call 7 | 28 | 124 | `from_note` | `VMADEA` | `VM: DEA` | V má de a. |  |
| Call 7 | 38 | 125 | `from_note` | `QADAH` | `QADA:` | Q á dah. |  |
| Call 7 | 49 | 125 | `from_note` | `BIGLIAD` | `BIGLIA ..` | Bigli ad. |  |
| Call 8 | 8 | 125 | `conflict` | `VRAN` | `G or V RAN` | V rán. | GRAN |
| Call 8 | 11 | 125 | `from_note` | `DSABRAMG` | `.. SABRAMG` | Dsábramg. [g not as dg.] |  |
| Call 8 | 51 | 127 | `from_note` | `BLIORS` | `BLI....S` | Bli ors. |  |
| Call 8 | 53 | 127 | `from_note` | `CORSI` | `COR ....` | Cor si. |  |
| Call 9 | 3 | 127 | `from_note` | `PURGEL` | `P.. GEL` | Pur gel. |  |
| Call 9 | 7 | 128 | `from_note` | `EFAFAFE` | `... FAFE` | E fa fa fe. [margin: EFAFAFI] |  |
| Call 9 | 32 | 128 | `from_note` | `LASOLLOR` | `LA. LLOR` | Las ol lor. |  |
| Call 9 | 38 | 129 | `from_note` | `MADRID` | `.ADRID` | Ma drid |  |
| Call 9 | 41 | 129 | `from_note` | `CHIS` | `CHI.` | Chis. |  |
| Call 9 | 50 | 129 | `from_note` | `DAZIS` | `DAZI.` | Daz is. |  |
| Call 9 | 54 | 129 | `from_note` | `MIRC` | `MIR.` | M irk.; M irc. |  |
| Call 9 | 56 | 129 | `from_note` | `CHIS` | `CH..` | Chis. |  |
| Call 9 | 58 | 130 | `from_note` | `COLLAL` | `COLLA..` | Col lal. |  |
| Call 9 | 63 | 130 | `from_note` | `IADBALTOH` | `IA. BALTOH` | I ad bal toh. |  |
| Call 9 | 66 | 130 | `from_note` | `NIISO` | `NII..` | Ni i so. |  |
| Call 9 | 69 | 130 | `from_note` | `OFAFAFE` | `O ... AFE` | O fa fa fe. |  |
| Call 10 | 3 | 130 | `from_note` | `CORMP` | `CORM.` | Cormp. |  |
| Call 10 | 6 | 131 | `from_note` | `LUCAL` | `....U....AL` | Lu cal. |  |
| Call 10 | 7 | 131 | `from_note` | `AZIAZOR` | `AZI........R` | A zi a zor. |  |
| Call 10 | 17 | 131 | `from_note` | `MAASI` | `MA ........` | Ma a si. |  |
| Call 10 | 19 | 131 | `from_note` | `CAOSGI` | `........SGI` | Ca os gi. |  |
| Call 10 | 28 | 131 | `from_note` | `SIATRIS` | `....IATRIS` | Si a tris. |  |
| Call 10 | 32 | 131 | `from_note` | `FABOAN` | `F ....BOAN` | Fa bo an. |  |
| Call 10 | 46 | 132 | `from_note` | `COCASG` | `COC......` | gao.; dg.; Co Casg. |  |
| Call 10 | 47 | 132 | `from_note` | `PLOSI` | `PLOS...` | Plo si. |  |
| Call 10 | 48 | 132 | `from_note` | `MOLUI` | `M.....I` | Mol ui. |  |
| Call 10 | 72 | 133 | `from_note` | `CAOSGON` | `CAO..GON` | Ca ós gon. |  |
| Call 11 | 4 | 133 | `from_note` | `ZIROM` | `.IROM` | Zir om. |  |
| Call 11 | 17 | 134 | `from_note` | `TELOCH` | `TELOC..` | hotch.; Te loch. |  |
| Call 11 | 30 | 134 | `from_note` | `NONCP` | `N. NCP` | Nonsp.; Noncp. |  |
| Call 12 | 23 | 136 | `from_note` | `ZACAR` | `...............` | Za car. |  |
| Call 12 | 24 | 136 | `from_note` | `GOHUS` | `...............` | Go hus. |  |
| Call 12 | 25 | 136 | `from_note` | `ZAMRAN` | `..................` | Zamran. |  |
| Call 12 | 26 | 136 | `from_note` | `ODO` | `.........` | O do. |  |
| Call 12 | 27 | 136 | `from_note` | `CICLE` | `...ICLE` | CICLE. |  |
| Call 13 | 4 | 136 | `from_note` | `VX` |  | V x. |  |
| Call 13 | 8 | 135 | `from_note` | `DOALIM` | `......` | Do a lim. |  |
| Call 13 | 9 | 135 | `from_note` | `EOLIS` | `.....` | E o lis. |  |
| Call 13 | 10 | 135 | `from_note` | `OLLOG` | `.....` | Ol log. |  |
| Call 13 | 11 | 135 | `from_note` | `ORSBA` | `.....` | Ors ba. |  |
| Call 17 | 1 | 136 | `from_note` | `ILS` | `........` | ILS. |  |
| Call 17 | 2 | 136 | `from_note` | `DIALPERT` | `................` | Di alpert. |  |
| Call 17 | 11 | 135 | `from_note` | `HUBARO` | `H.....` | Hu ba ro. |  |
| Call 17 | 12 | 135 | `from_note` | `TASTAX` | `TAST..` | Tas tax. |  |
| Call 17 | 13 | 135 | `from_note` | `YLSI` | `YL..` | Yl si. |  |
| Call 17 | 16 | 137 | `from_note` | `ALDON` | `AL. ON` | Al don. |  |
| Call 18 | 1 | 137 | `from_note` | `ILS` | `...` | Ils. |  |
| Call 18 | 2 | 137 | `from_note` | `MICAOLZ` | `.........` | Mi ca ol zod. |  |
| Call 18 | 3 | 137 | `from_note` | `OLPIRT` | `.L. IRT` | Ol pirt. |  |
| Call 18 | 13 | 137 | `from_note` | `LAIAD` | `LA...` | Là i àd. |  |
| Call 18 | 15 | 137 | `from_note` | `BRINTS` | `.INTS` | Brints. |  |
| Call 18 | 25 | 138 | `from_note` | `COMOBLIORT` | `COMOB .. IORT` | Co mo bli ort. |  |
| Aethyr call | 22 | 202 | `from_note` | `DS` | `Δ S` | Ds. |  |
<!-- uncertain:end -->

### Words repeated from an uncertain word of Call 1

The endings of calls 11 to 18 repeat two words that are uncertain in Call 1, so they are uncertain there too.

<!-- repeats:start -->
| Call | Word | Page | Status | Spelling | Repeats |
| --- | --- | --- | --- | --- | --- |
| Call 11 | 33 | 193 | `conflict` | `OD` | Call 1 word 75 |
| Call 11 | 40 | 193 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 12 | 31 | 193 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 13 | 25 | 193 | `conflict` | `OD` | Call 1 word 75 |
| Call 13 | 32 | 193 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 14 | 28 | 193 | `conflict` | `OD` | Call 1 word 75 |
| Call 14 | 35 | 193 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 15 | 20 | 193 | `conflict` | `OD` | Call 1 word 75 |
| Call 15 | 27 | 193 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 16 | 24 | 194 | `conflict` | `OD` | Call 1 word 75 |
| Call 16 | 31 | 194 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 17 | 22 | 194 | `conflict` | `OD` | Call 1 word 75 |
| Call 17 | 29 | 194 | `from_note` | `ZIRDO` | Call 1 word 82 |
| Call 18 | 29 | 194 | `conflict` | `OD` | Call 1 word 75 |
| Call 18 | 36 | 194 | `from_note` | `ZIRDO` | Call 1 word 82 |
<!-- repeats:end -->

### Words the printing does not have

The spellings are the ones the call files had before the journal was applied. They have no source in the printing. The manuscript has all of these words; as it was read, 54 have the same letters and two do not (`vpaahi` for `VPHAAI`, and `DSOCIDO`, which was not read with certainty).

<!-- not-printed:start -->
| Call | Words | Count | Spellings |
| --- | --- | --- | --- |
| Call 13 | 21 to 22 | 2 | `AAI` `GROSB` |
| Call 14 | 1 to 25 | 25 | `NOROMI` `BAGIE` `PASBS` `OIAD` `DS` `TRINT` `MIRC` `OL` `THIL` `DODS` `TOLHAM` `CAOSGO` `HOMIN` `DS` `BRIN` `OROCH` `QUAR` `MICMA` `BIAL` `OIAD` `AISRO` `TOX` `DSIVM` `AAI` `BALTIM` |
| Call 15 | 1 to 17 | 17 | `ILS` `TABAAN` `LIALPRT` `CASARMAN` `VPHAAI` `CHIS` `DARG` `DSOCIDO` `CAOSGI` `ORSCOR` `DS` `OMAX` `MONASCI` `BAEOUIB` `OD` `EMETGIS` `IAIADIX` |
| Call 16 | 1 to 12 | 12 | `ILS` `VIUIALPRT` `SALMAN` `BALT` `DS` `ACROODZI` `BUSD` `OD` `BLIORAX` `BALIT` `DSINSI` `CAOSG` |
<!-- not-printed:end -->

## Words where Dee's note spells different letters

These words are `printed` or `corrected`, so the journal record has the column's spelling. Dee's note beside the word does not spell the same letters. The test is mechanical: the note is cut at its punctuation, and a word passes when its letters equal some run of whole words in one piece of the note, with J read as I, Y as I, V as U, and "zod" as Z. A note can respell a word for its sound, and some of these notes do not spell the word at all, so a word on this list is not shown to be wrong. It is a place where the printing gives two things and the call file follows the column.

<!-- note-differs:start -->
| Call | Word | Page | Spelling | Column | Dee's note |
| --- | --- | --- | --- | --- | --- |
| Call 1 | 13 | 86 | `I` | `I` | a word by it self. |
| Call 1 | 57 | 84 | `IPAM` | `MAPI` | [margin: Labiis clausis, [Span] [um um] ... He hummed twice, signifying two words more, which were not to be pronounced till they were read in practise.] E. K. It seemeth to be an e. |
| Call 1 | 60 | 83 | `DS` | `SD` | It is the uppermost of [margin: Call it DS.] |
| Call 1 | 61 | 83 | `LOHOLO` | `OLOHOL` | [margin: Call it Loholo.] Long, the first syllable accented. |
| Call 1 | 62 | 83 | `VEP` | `PEV` | [margin: It is called Vep.] Make a point there. Δ. A full point? [margin: Nal. .... No, no, a stroke.] |
| Call 1 | 65 | 83 | `OD` | `DOS` | DOS. He pointed beyond him in the upper Circle, it seemeth [margin: Also T] like a Roman C. |
| Call 2 | 8 | 100 | `L` | `L` | A word. |
| Call 2 | 18 | 100 | `QTA` | `ATQ` | Quu Ta. |
| Call 2 | 19 | 100 | `LORSLQ` | `QLSROL` | Lors l qua. |
| Call 2 | 37 | 99 | `OQ` | `QO` | O qua. |
| Call 2 | 44 | 99 | `CNOQOD` | `DOQONC` | [as C No quod. |
| Call 3 | 14 | 97 | `CHIS` | `SIHC` | as Kis |
| Call 3 | 26 | 96 | `BRGDA` | `ADGRB` | as burgen to bud as Burgda |
| Call 3 | 33 | 96 | `HAALA` | `ALAAH` | AAla |
| Call 3 | 37 | 96 | `VOMZARG` | `GRAZMOV` | arg as in barge Vomsarg |
| Call 4 | 26 | 110 | `CHIS` | `SIHC` | Kis |
| Call 4 | 34 | 109 | `DO` | `OD` | Od. |
| Call 4 | 45 | 109 | `RESTIL` | `LITSER` | Rest el. |
| Call 5 | 6 | 119 | `TAQANIS` |  | Ta qu a nis. |
| Call 5 | 26 | 120 | `ESIASCH` |  | E siach. |
| Call 6 | 36 | 123 | `GMICALZO` |  | G-ni cálzo. |
| Call 8 | 19 | 126 | `AZIAGIAR` |  | A zi á gi er. [margin: He putteth his feet on all these letters.] |
| Call 8 | 24 | 126 | `CAOSGO` |  | Ca, or Ka os go. |
| Call 8 | 28 | 126 | `CACRG` |  | Ca curg. |
| Call 9 | 60 | 130 | `ASOBAMA` |  | A so bam. |
| Call 13 | 2 | 136 | `BABAGEN` |  | jen.; B ba gen |
| Call 13 | 20 | 136 | `JUMD` |  | Jumbd. |
| Call 18 | 4 | 137 | `IALPRG` |  | Yal.; I al purg. |
| Call 18 | 21 | 137 | `QZMOZ` |  | Moz. |
| Aethyr call | 1 | 201 | `MADRIIAX` |  | Δ. I think this word wanteth [margin: Ilemese.] as may appear by Madriax, about 44 words from the end. |
| Aethyr call | 10 | 201 | `IAIDA` |  | Ya; Ia - i da. |
| Aethyr call | 19 | 201 | `CHI` |  | Kis s; Chis. |
| Aethyr call | 21 | 202 | `PIRIPSOL` |  | Pe ripsol. |
| Aethyr call | 38 | 203 | `IDOIGO` | `ID*UIGO` | [margin: \*O] Δ. Note the wicked power dazeled so the eyes of E. K. that he could not well discern this O, but staying at it a while concluded it to be an V: which afterward, and by and by, he corrected. |
| Aethyr call | 59 | 204 | `PIRIPSAX` |  | Pe rip sax. |
| Aethyr call | 80 | 205 | `AGLTOLTORN` |  | Ag l ter torn. |
| Aethyr name | 11 | 209 | `ICH` |  | ik. |
| Aethyr name | 20 | 209 | `CHR` |  | kar in palato very much. .... |
<!-- note-differs:end -->

## Corrections the journal makes

Words with the status `corrected`. Words repeated from Call 1 are not listed again.

<!-- corrected:start -->
| Call | Word | Page | Spelling | Column | What the journal says |
| --- | --- | --- | --- | --- | --- |
| Call 1 | 65 | 83 | `OD` | `DOS` | The letters given are DOS. The journal says to put out the S and to make Poamal and Od two words. On p. 90 Dee asks whether 'Poamalzod' is one word; the printed answer is 'Set down'. |
| Call 1 | 73 | 80 | `ZACARE` | `R, A, C, A, Z` | The letters named spell ZACAR. The margin says E must come after R, 'and so, it is Zacare'. |
| Call 1 | 76 | 80 | `ZAMRAN` | `N, A, R, N, A, Z` | The letters named spell ZANRAN. The margin corrects the N to M: Zamran. |
| Call 5 | 25 | 120 | `ZCHIS` |  | The journal gives ZIZOP and then ZCHIS, and says Zod-chis 'is better to be used'. ZIZOP is left out. |
| Call 6 | 22 | 122 | `FBLIARD` | `TBLIARD` | The letter column prints TBLIARD. The journal says it is better if the T be made an F. |
| Call 9 | 8 | 128 | `P` |  | The journal adds this after the call is given. p. 191 puts it against 'eight' in the English: 'That is P.' |
| Call 10 | 12 | 131 | `OP` |  | Between Chis and Virq, you must put in Op a word. |
| Call 10 | 54 | 132 | `MATORB` |  | The printing has MATORB after YOLCI and says 'This word must come next after Om droln'. It is placed after DROLN. |
| Aethyr call | 38 | 203 | `IDOIGO` | `ID*UIGO` | The letter column prints ID\*UIGO with \*O beside it. The journal says the letter taken for V was corrected to O, and Dee writes 'It must be then I doigo?' |
<!-- corrected:end -->

## Where the keyed transcription was set right from the page image

The transcription keeps a gap wherever the keyers could not read the film, and it has some wrong letters. Each of these places was read from the Internet Archive page image of the same printing.

<!-- keyed:start -->
| Page | As keyed | As the page image prints it |
| --- | --- | --- |
| 83 | `as [gap:1 word] yew` | `as we pronounce yew` |
| 85 | `a point [gap:1 word].` | `a point here.` |
| 94 | `Gobia.` | `Gohia.` |
| 94 | `[gap:1 word].` | `Casarmg.` |
| 95 | `Gobus.` | `Gohus.` |
| 95 | `Od vooaen.` | `Od vooan.` |
| 97 | `Com [gap:1 word]` | `Com Selh` |
| 100 | `Lors I qua.` | `Lors l qua.` |
| 109 | `the sons of [gap:1 word]` | `the sons of men` |
| 109 | `IHASARQRON` | `IHASAVQRON` |
| 109 | `NOAMIPAG` | `NOAMIPAC` |
| 111 | `O thll` | `O thil` |
| 119 | `L. [gap:1 word].` | `L. Lasky.` |
| 125 | `[gap:1 word] BAZMELO` | `BAZMELO` |
| 125 | `Bal to ba.` | `Bal to ha.` |
| 126 | `He [gap:1 word] his feet` | `He putteth his feet` |
| 127 | `[gap:1 word] MICAOLI` | `MICAOLI` |
| 128 | `O L a [gap:1 word].` | `O L a ni.` |
| 128 | `TANAN` | `TRANAN` |
| 128 | `[gap:1 word] LAR` | `ALAR` |
| 129 | `ADRID` | `.ADRID` |
| 130 | `[gap:1 word] I Cors ca.` | `Ka I Cors ca.` |
| 134 | `Salman. [gap:1 word].` | `Sal man.` |
| 134 | `Ab ramg. g, not us dg. Nonsp.` | `Ab ramg. g, not as dg.` |
| 137 | `[gap:1 word].` | `quu.` |
| 201 | `{note: [gap:1 word].}` | `{note: Ile.}` |
| 201 | `{note: [gap:1 word].}` | `{note: O or A.}` |
| 202 | `Ca of gi.` | `Ca os gi.` |
| 203 | `let her be [gap:1 word]` | `let her be governed` |
| 203 | `by her [gap:1 word]` | `by her parts` |
| 203 | `let [gap:1 word] he` | `let there be` |
| 206 | `for [gap:2 words] of the field` | `for the beasts of the field` |
| 206 | `OMPTILE` | `OMPTILB` |
| 207 | `Od ca co cash.` | `Od ca có casb.` |
<!-- keyed:end -->

Other words carry `read_from` as well: every word on pages 132 and 133, and a few whose note was read from the image. Each says what was read in its `remark`.

## Sloane 3191

British Library MS Sloane 3191 has the calls in Dee's own hand, as a fair copy he titled *48 Claves Angelicae*. On November 11, 2026 it was made the source of the call files, with the journal as the second source. The reasons, and everything that is not certain about the reading, are in [call-analysis-notes.md](call-analysis-notes.md#decision-sloane-3191-first).

The manuscript was read from the scan [`998222247-Dee-MS-Sloane-3191.pdf`](998222247-Dee-MS-Sloane-3191.pdf). The reading is typed by hand in [`tools/sloane/sloane-reading.json`](../tools/sloane/sloane-reading.json). It is one reading by eye of handwriting on microfilm, and nobody has confirmed it. `tools/sloane/sloane-build.py` makes `calls/sloane/` from the reading and the journal record.

Each file in `calls/sloane/` has these fields for a word.

| Field | Meaning |
| --- | --- |
| `letters` | The letters the call file has |
| `written` | The word as typed in the reading: accents where they were seen, a hyphen for a stroke Dee draws to tie two parts together, an underscore for a small gap with no tie, a `?` after a letter that was not read with certainty |
| `status` | `read`: the letters are the reading's. `unsure`: the reading has a `?`, and the letters are the journal's |
| `journal` | The numbers of the journal words at this place, counted from 1. Empty when the word is only in the manuscript |
| `differs` | How the word differs from the journal words at its place: `letters`, `u/v or i/j/y only`, `word break`, or `only in the manuscript`. Empty when they are the same letters as one word |
| `checked` | What was seen when the place was checked against the scan. Absent until then |

Each file also has `where` (the page of the scan), `remarks` (what else is written at that call), and `journal_only` (the journal words that are not in the manuscript). `aethyrs.json` has `names`, the thirty names from the numbered list in the margin, and `name_word`, the place of the name in the call.

The journal is used in three ways when `calls/sloane/` is made, and in no other.

- **Small gaps:** Dee often leaves a small gap inside a word, and the eye cannot always tell such a gap from the gap between two words. The reading has 166 small gaps. Each was measured on the page, as described under [The small gaps](#the-small-gaps). One is a word break by its width. One more is a word break because the journal breaks at that very letter. The other 164 are inside 121 words, and the division of those words is the journal's.
- **Letters not read with certainty:** two words have a `?`. They take the journal's letters: `MATORB` in Call 10 and `DSOCIDO` in Call 15.
- **The differences:** every word says which journal words stand at its place and how they differ.

`calls/sloane/` has 1,103 words, counting the thirty names. 72 differ from the journal words at their place, 3 are only in the manuscript, and 2 are `unsure`. 7 journal words are not in the manuscript. The same differences are listed by journal word in [`sloane-diff.txt`](sloane-diff.txt), which `tools/sloane/sloane-sheets.py` writes; it also writes a sheet for each call to `scratch/sloane-check/`, which is not in git.

The letters are the manuscript's as they were read, including u and v. Dee writes V for a capital U, so one word can be spelled two ways: `torzu` in Call 2 and `torzv` in the Aethyr call. No rule has been chosen to make them the same.

Where the manuscript gives two spellings at one place, the call file has the one on the line. In Call 6 that is `tbliard`, with `f-bliard` written beneath it. In Call 4 it is `restel`, with a small `i` above the e. These are in `remarks`.

### The small gaps

The 166 small gaps were measured on the scan to see whether the page itself shows where a word ends. For 165 of them it does not.

- **The measure:** `tools/sloane/sloane-gaps.py` finds each line of Enochian on the page and measures every gap in it of 12 pixels or more. A gap is a run of columns with no ink at the height where the small letters stand. A stroke above or below that height does not fill a gap, so a tie-stroke under the line and the tall stroke of a d are not counted.
- **The kinds:** on each of the 172 lines that were typed, every measured gap was given a kind by eye, in [`tools/sloane/sloane-gap-kinds.txt`](../tools/sloane/sloane-gap-kinds.txt). The kinds are a gap between two words, a small gap, a gap Dee tied with a stroke, a gap between two letters of a word, a gap in a word written in capitals, and a gap that is not a whole gap of the text. The script checks that every width typed there is the width it measures, and that each call has as many small gaps there as in the reading.
- **What the widths are:** 648 gaps between words were measured. The narrowest are 29, 31 and 34 pixels, and 11 are 41 pixels or less. Among the gaps inside a word, the widest that Dee tied is 41 pixels (`z-chis` in Call 5) and the widest between two letters is 33. So a gap of 29 to 41 pixels can be either. The width cannot tell a word break from a gap inside a word in that range, and no width shows that two parts are one word.
- **The rule:** a small gap is a word break when it is wider than every gap measured inside a word, and at least as wide as a gap between two words on its own line.
- **What it found:** one word break, `a chíldáo` in Call 9. Its gap is 60 pixels, and the gap between `chis` and `pidiái` on the same line is 55. The journal prints `ACHILDAO` as one word, with the note `A chil da o`.
- **Wider than inside a word, narrower than between words:** three gaps: `Thiln_os` in Call 3 (50 pixels; the narrowest word gap on its line is 78), `od_lonshin` in Call 4 (45; 88) and `a_sóbam` in Call 9 (44; 116). They are not settled.
- **Not measured:** two gaps have a stroke or a point standing in them: `z_chis` in Call 11, where the tail of the z runs to the c, and `L_nibm` in the Aethyr call.
- **No break shown:** 140 gaps are no wider than a gap that stands inside a word, and at 20 the script found no gap of 12 pixels.

[`sloane-gaps.txt`](sloane-gaps.txt) lists every small gap with its width, the narrowest word gap on its line, what the width shows, and whether the journal has one word or two there. At the one small gap where the journal has two words, `ds_brin` in Call 14, the gap is 23 pixels, which is no wider than a gap inside a word.

What is not certain about this measure:

- **The kinds are one reading by eye.** They were typed from the marked page images and have not been confirmed. A gap typed as inside a word that is in truth a word gap would raise the 41 pixels, and the reverse would lower it.
- **The 41 pixels rests on one gap.** If `z-chis` in Call 5 were left out, the widest gap inside a word would be 38 pixels, and `Q_mos-pleh` in Call 3 (41 pixels) would move to the three that are not settled. Nothing else would change.
- **Faint ink widens a gap.** A letter written lightly can fall below the darkness that counts as ink.
- **The rule is a choice.** It was written for this work. A different rule could divide differently.
- **Dee's English above the words was not used.** It may show the division at some of these places. It has not been typed out.

The images are not in git. `python3 tools/sloane/sloane-gaps.py pages CALL` writes the marked pages of one call to `scratch/sloane-gaps/`.

For checking the reading, `tools/sloane/sloane-cut.py` cuts one image of each call into [`imgs/sloane-calls/`](imgs/sloane-calls), and one full-size image of each place that differs into `imgs/sloane-places/`, where [`index.md`](imgs/sloane-places/index.md) shows each image beside the two spellings. Words that differ only in u/v or i/j/y get no image. Where each place stands on its page is typed in [`tools/sloane/sloane-places.json`](../tools/sloane/sloane-places.json), and what is seen at each place is recorded there in `checked`.

## The call files

`calls/01.txt` to `18.txt` and the thirty Aethyr files have the words of `calls/sloane/`, in order. `tools/journal/rewrite-calls.py sloane` writes them. A test in [`tests/test_calls.py`](../tests/test_calls.py) checks that they match. It is a check of the files against the record of the reading. It does not check the reading against the manuscript.

Neither source record has punctuation. Each mark was carried over from the call file as it was before either source was applied, and put after the word that now holds the letter it used to follow. Two marks moved because the record has as one word what the file had as two: the comma in Call 3 that stood inside `casarmg`, and the comma in Call 8 that stood inside `iadoiasmomar`.

An Aethyr file is named by the manuscript's spelling of the name. `23-lit.txt` was `23-lat.txt` before either source was applied; the manuscript and the printing both have `Lit`. `32-vta.txt` and `43-vti.txt` have the names they had before; while the journal was the source they were `32-uta.txt` and `43-uti.txt`. `49.txt` and `50.txt` are not Dee's and were not touched.

No recording was made from these words. When this was written there was no `.wav` file in `calls/`.

Every spelling in a call file has an entry in [`calls/lexicon.json`](../calls/lexicon.json). A spelling that came in with either source has no English and a `dee_ipa` that was made by the letter rule from its letters. That string is what the rule says from the letters. It is not evidence of how the word is pronounced. Entries whose spelling is no longer in any call file were kept as they were.
