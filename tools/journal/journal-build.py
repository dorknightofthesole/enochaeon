"""Build calls/journal/ from the keyed transcription of Casaubon's 1659 printing.

Reads docs/casaubon-1659-true-and-faithful-relation.xml through
tools/journal/casaubon-dump.py, which numbers every table row of the transcription.
Each call below names the rows it is made of. Everything that is not read
straight off a row is written out here by hand with the reason beside it.

Rules, the same for every call:

  letters   the spelling column. In a call given backwards the column is read
            from its last letter to its first. Dee's note never changes a
            spelling column that can be read.
  column    the spelling column exactly as printed, kept whenever it is not the
            same string as `letters`.
  note      Dee's note as printed. A margin note is written [margin: ...].
  english   Dee's English where the journal pairs it with the word.
  status    printed      the spelling column can be read
            from_note    the spelling column has dots or is empty; the missing
                         letters are read from Dee's note
            gap          the keyers marked something in the column unreadable
            corrected    the journal changes the word; correction_page says where
            conflict     two places in the printing give different letters
            not_printed  the 1659 printing does not have this word; the spelling
                         is the one the call file had before, which has no source

Pages 132 and 133 are not in the keyed transcription. Their words were read
from the page images of the same printing and carry read_from. Every page of
the calls was also compared with its page image; where the keyers miskeyed a
word or left a gap that the image shows, IMAGE_READINGS has both readings and
the word carries read_from.

Writes calls/journal/01.json to 18.json and calls/journal/aethyrs.json.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEST = ROOT / "calls" / "journal"
BEFORE = HERE / "calls-before"

_spec = importlib.util.spec_from_file_location("casaubon_dump", HERE / "casaubon-dump.py")
_dump = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dump)
ROWS = {row["row"]: row for row in _dump.flatten().rows}

IMAGE = "page image, Internet Archive scan truefaithfulrela00deej"

# Places where the keyed transcription is wrong or has a gap and the page image of
# the same printing can be read. row: [(as keyed, as the page image prints it)].
IMAGE_READINGS = {
    85: [("as [gap:1 word] yew", "as we pronounce yew")],
    117: [("a point [gap:1 word].", "a point here.")],
    213: [("Gobia.", "Gohia.")],
    214: [("[gap:1 word].", "Casarmg.")],
    223: [("Gobus.", "Gohus.")],
    227: [("Od vooaen.", "Od vooan.")],
    281: [("Com [gap:1 word]", "Com Selh")],
    319: [("Lors I qua.", "Lors l qua.")],
    338: [("the sons of [gap:1 word]", "the sons of men")],
    352: [("IHASARQRON", "IHASAVQRON")],
    358: [("NOAMIPAG", "NOAMIPAC")],
    389: [("O thll", "O thil")],
    392: [("L. [gap:1 word].", "L. Lasky.")],
    555: [("[gap:1 word] BAZMELO", "BAZMELO")],
    566: [("Bal to ba.", "Bal to ha.")],
    573: [("He [gap:1 word] his feet", "He putteth his feet")],
    611: [("[gap:1 word] MICAOLI", "MICAOLI")],
    619: [("O L a [gap:1 word].", "O L a ni.")],
    628: [("TANAN", "TRANAN")],
    630: [("[gap:1 word] LAR", "ALAR")],
    650: [("ADRID", ".ADRID")],
    688: [("[gap:1 word] I Cors ca.", "Ka I Cors ca.")],
    732: [("Salman. [gap:1 word].", "Sal man.")],
    745: [("Ab ramg. g, not us dg. Nonsp.", "Ab ramg. g, not as dg.")],
    845: [("[gap:1 word].", "quu.")],
    1356: [("{note: [gap:1 word].}", "{note: Ile.}")],
    1372: [("{note: [gap:1 word].}", "{note: O or A.}")],
    1382: [("Ca of gi.", "Ca os gi.")],
    1404: [("let her be [gap:1 word]", "let her be governed")],
    1405: [("by her [gap:1 word]", "by her parts")],
    1407: [("let [gap:1 word] he", "let there be")],
    1470: [("for [gap:2 words] of the field", "for the beasts of the field")],
    1473: [("OMPTILE", "OMPTILB")],
    1480: [("Od ca co cash.", "Od ca có casb.")],
}
IMAGE_REMARKS = {
    555: "In the page image a small mark stands before the word, and the word itself is whole.",
    611: "In the page image a small mark stands before the word, and the word itself is whole.",
    650: "In the page image a dot stands where the first letter should be.",
    1473: "In the page image the last letter is clogged with ink. It has the two closed bowls of a B, and the note "
          "prints 'Omp tilb.'",
}
for _row, _pairs in IMAGE_READINGS.items():
    for _keyed, _printed in _pairs:
        if not any(_keyed in cell for cell in ROWS[_row]["cells"]):
            raise ValueError(f"row {_row}: the transcription does not have {_keyed!r}")
        ROWS[_row]["cells"] = [cell.replace(_keyed, _printed) for cell in ROWS[_row]["cells"]]


def mark_image_readings(words: list[dict]) -> None:
    """Say on each word which part of it was read from the page image."""
    for entry in words:
        row_id = entry.get("row")
        if row_id not in IMAGE_READINGS:
            continue
        told = [f"The keyed transcription has '{keyed}' where the page image prints '{printed}'."
                for keyed, printed in IMAGE_READINGS[row_id]]
        if row_id in IMAGE_REMARKS:
            told.append(IMAGE_REMARKS[row_id])
        entry["remark"] = " ".join(part for part in [entry.get("remark", "")] + told if part)
        entry["read_from"] = IMAGE
MARGIN = re.compile(r"\{note:\s*(.*?)\s*\}")
BRACKET = re.compile(r"\[[^\]]*\]")


def clean(text: str) -> str:
    """A cell as printed, with margin notes marked."""
    return " ".join(MARGIN.sub(lambda found: f"[margin: {found.group(1)}]", text).split())


def without_margin(text: str) -> str:
    return " ".join(MARGIN.sub(" ", text).split())


def letters_of(text: str) -> str:
    """The letters A to Z of a string, without accents, brackets or margin notes."""
    text = BRACKET.sub(" ", MARGIN.sub(" ", text))
    text = unicodedata.normalize("NFD", text)
    return "".join(char for char in text.upper() if "A" <= char <= "Z")


def word(page, letters, note="", english="", status="printed", **extra) -> dict:
    entry = {"page": page, "letters": letters, "note": note, "english": english, "status": status}
    for key, value in extra.items():
        if value not in ("", None):
            entry[key] = value
    return entry


def join(parts) -> str:
    return "; ".join(part for part in parts if part)


# --- reading one spelling column -------------------------------------------------

_WILD = re.compile(r"(?:\[gap:[^\]]*\]|[.:—Δ\s])+")


def read_column(column: str, notes: list[str]) -> tuple[str, str, str]:
    """Return (letters, status, remark) for a forward spelling column."""
    raw = column.strip()
    has_gap = "[gap" in raw
    core = raw[:-1] if raw.endswith(".") and not raw.endswith("..") else raw
    if re.fullmatch(r"[A-Za-z]+", core):
        plain = core.upper()
        if raw != core:
            # One final dot: a full stop, or one unreadable letter.
            for note in reversed(notes):
                spelled = letters_of(note)
                if spelled == plain:
                    return plain, "printed", ""
            for note in reversed(notes):
                spelled = letters_of(note)
                if spelled.startswith(plain) and len(spelled) > len(plain):
                    return spelled, "from_note", (
                        f"The letter column prints '{raw}'. The dot is read as a missing letter "
                        "because the note has one more letter there."
                    )
        return plain, "printed", ""
    pieces = [piece for piece in _WILD.split(raw) if piece]
    if not all(re.fullmatch(r"[A-Za-z]+", piece) for piece in pieces):
        raise ValueError(f"column needs a hand entry: {column!r}")
    pattern = ""
    position = 0
    for found in _WILD.finditer(raw):
        pattern += re.escape(raw[position:found.start()].upper()) + "(.*)"
        position = found.end()
    pattern += re.escape(raw[position:].upper())
    visible = "".join(pieces).upper()
    for zod in (False, True):
        for note in reversed(notes):
            spelled = letters_of(note)
            if zod:
                spelled = spelled.replace("ZOD", "Z")
            if spelled and re.fullmatch(pattern, spelled):
                if has_gap:
                    remark = f"The keyers marked part of the letter column unreadable: '{raw}'."
                    if spelled != visible:
                        remark += " The missing letters are read from the note."
                    return spelled, "gap", remark
                if spelled == visible and not re.search(r"[.:—Δ]", raw):
                    return spelled, "printed", f"The letter column prints '{raw}' with a space."
                remark = f"The letter column prints '{raw}'. The missing letters are read from the note."
                if spelled == visible:
                    remark = f"The letter column prints '{raw}'. The note has no letter where the dots are."
                if zod:
                    remark += " 'zod' in the note is taken as the letter Z."
                return spelled, "from_note", remark
    raise ValueError(f"column needs a hand entry: {column!r} notes {notes!r}")


# --- builders --------------------------------------------------------------------

def backward(first: int, last: int, *, attach_next=(), skip=(), split=None, continuation=()) -> list[dict]:
    """A call given backwards in rows of number | reversed letters | English | note."""
    words: list[dict] = []
    pending: list[str] = []
    for row_id in range(first, last + 1):
        if row_id in skip:
            continue
        row = ROWS[row_id]
        cells = row["cells"] + [""] * 6
        column = without_margin(cells[1])
        notes = [clean(cell) for cell in cells[3:] if cell.strip()]
        margins = [f"[margin: {text}]" for cell in cells[:3] for text in MARGIN.findall(cell)]
        if not column or row_id in continuation:
            text = join(notes + margins)
            if row_id in attach_next:
                pending.append(text)
            elif words:
                words[-1]["note"] = join([words[-1]["note"], text])
            continue
        page = int(row["page"])
        number = cells[0].strip().rstrip(".")
        english = without_margin(cells[2])
        if split and row_id in split:
            parts = split[row_id]
            made = []
            for index, (part_column, remark) in enumerate(parts):
                made.append(word(page, letters_of(part_column)[::-1], join(pending + notes + margins),
                                 english if index == len(parts) - 1 else "", "printed",
                                 column=column, number=number, row=row_id, remark=remark))
            # The row is read backwards, so its last piece is the first word.
            words.extend(made)
            pending = []
            continue
        if "[gap" in column:
            entry = word(page, "", join(pending + notes + margins), english, "gap",
                         column=column, number=number, row=row_id)
        else:
            entry = word(page, letters_of(column)[::-1], join(pending + notes + margins), english, "printed",
                         column=column, number=number, row=row_id)
        pending = []
        words.append(entry)
    words.reverse()
    return words


def forward_items(first: int, last: int, *, skip=()) -> list[dict]:
    items = []
    for row_id in range(first, last + 1):
        if row_id in skip:
            continue
        row = ROWS[row_id]
        cells = row["cells"]
        column = without_margin(cells[0])
        english = ""
        note_cells = cells[1:]
        if len(cells) >= 3:
            english = without_margin(cells[1])
            note_cells = [cell if index else " ".join(f"{{note: {text}}}" for text in MARGIN.findall(cell))
                          for index, cell in enumerate(cells[1:])]
        notes = [clean(cell) for cell in note_cells if cell.strip()]
        notes = [f"[margin: {text}]" for text in MARGIN.findall(cells[0])] + notes
        items.append({"row": row_id, "page": int(row["page"]), "column": column, "english": english, "notes": notes})
    return items


def image_items(page: int, entries) -> list[dict]:
    return [{"row": None, "page": page, "column": column, "english": "", "notes": list(notes), "read_from": IMAGE}
            for column, notes in entries]


def forward(items: list[dict], *, attach_next=(), attach="previous", as_word=(), hand=None) -> list[dict]:
    """A call given forwards in rows of letters | note, or letters | English | note."""
    hand = hand or {}
    # First gather each word row with the note rows that belong to it.
    groups: list[dict] = []
    pending: list[str] = []
    pending_english: list[str] = []
    for item in items:
        row_id = item["row"]
        if not item["column"] and row_id not in as_word:
            goes_next = (attach == "next") != (row_id in attach_next)
            if goes_next:
                pending.extend(item["notes"])
                if item["english"]:
                    pending_english.append(item["english"])
            elif groups:
                groups[-1]["notes"].extend(item["notes"])
                if item["english"]:
                    groups[-1]["english"].append(item["english"])
            continue
        groups.append({"item": item, "notes": pending + item["notes"],
                       "english": pending_english + [item["english"]]})
        pending, pending_english = [], []
    words: list[dict] = []
    for group in groups:
        item = group["item"]
        row_id = item["row"]
        column = item["column"]
        notes = group["notes"]
        english = join(group["english"])
        if row_id in hand:
            fields = dict(hand[row_id])
            entry = word(item["page"], fields.pop("letters"), fields.pop("note", join(notes)),
                         fields.pop("english", english), fields.pop("status"), row=row_id, **fields)
            if "column" not in entry and column and column.upper().rstrip(".") != entry["letters"]:
                entry["column"] = column
        else:
            letters, status, remark = read_column(column, notes)
            entry = word(item["page"], letters, join(notes), english, status, row=row_id, remark=remark)
            if column.upper() != letters and column.upper().rstrip(".") != letters:
                entry["column"] = column
        if item.get("read_from"):
            entry["read_from"] = item["read_from"]
        words.append(entry)
    return words


def at(words: list[dict], row_id: int) -> int:
    for index, entry in enumerate(words):
        if entry.get("row") == row_id:
            return index
    raise KeyError(row_id)


def old_words(stem: str) -> list[str]:
    return re.findall(r"[A-Za-z]+", (BEFORE / f"{stem}.txt").read_text(encoding="utf-8"))


def not_printed(tokens: list[str], remark: str) -> list[dict]:
    return [word(None, token.upper(), "", "", "not_printed", remark=remark) for token in tokens]


# --- Call 1, pp. 79 to 86 --------------------------------------------------------

def call_1() -> tuple[list[dict], list[str]]:
    # Words 48 to 1 stand in a table: number | reversed letters | English | forward.
    table = backward(98, 147, skip={103, 141})
    for entry in table:
        spelled = letters_of(entry["note"])
        if entry["letters"] not in spelled:
            entry["status"] = "conflict"
    # 43: the letters come in two rows, GSN first and then ERNOZ.
    index = at(table, 104)
    table[index]["column"] = "GSN, ERNOZ"
    table[index]["letters"] = "ZONRENSG"
    table[index]["status"] = "printed"
    table[index]["remark"] = (
        "The letters are printed in two rows, GSN and then 43 ERNOZ. Read backwards together they are ZONRENSG, "
        "which is also what the forward column prints."
    )
    index = at(table, 144)
    table[index]["other"] = "GOTTO"
    table[index]["remark"] = "The reversed column prints OHOG, which read backwards is GOHO. The forward column prints GOTTO."

    hand = [
        word(85, "ZNRZA", "Call it Zurza. Δ. As... Znurza.", "", "conflict", column="AZRNZ", number="49", row=97,
             other="ZURZA",
             remark="The reversed column prints AZRNZ, which read backwards is ZNRZA. The journal says 'Call it Zurza' "
                    "and on p. 90 writes Zurza."),
        word(84, "ADNA", "Call it ADNA.", "", "printed", column="ANDA", number="50", row=96),
        word(84, "GONO", "Call it Gono.", "", "printed", column="ONOG", number="51", row=95),
        word(84, "IADPIL", "Call it IADPIL accent ad.", "", "printed", column="LIPDAI", number="52", row=94),
        word(84, "DS", "DS.", "", "printed", column="SD", number="53", row=93),
        word(84, "HOM", "HOM.", "", "printed", column="MOH", number="54", row=92),
        word(84, "TOH", "TOH. [margin: There is a point, shewing a stroke, called Virgula.]", "", "printed",
             column="HOT", number="55", row=91),
        word(84, "SOBA", "SOBA.", "", "conflict", column="ABOS", row=90,
             remark="Before this row the journal says: 'I am deceived from Ipam. OD the next is false, and so are the "
                    "rest: And so is that that followeth.' It then prints ABOS, SOBA. The printing does not show "
                    "whether SOBA is the word that stands or part of what is false."),
        word(84, "IPAM",
             "[margin: Labiis clausis, [Span] [um um] ... He hummed twice, signifying two words more, which were not "
             "to be pronounced till they were read in practise.] E. K. It seemeth to be an e.",
             "", "printed", column="MAPI", number="57", row=86, read_from=IMAGE,
             remark="The keyed transcription has 'claufis', 'bummed' and 'F. K.' in the note; the page image prints "
                    "'clausis', 'hummed' and 'E. K.'"),
        word(83, "UL", "Call it UL. Δ, With such sound to U. as we pronounce yew, whereof bows are made.", "", "printed",
             column="LU", number="58", row=85),
        word(83, "IPAMIS", "Pronownce it IPAMIS. [margin: Make a point at S. the A pronounced short.]", "", "printed",
             column="SIMAPI", number="59", row=84),
        word(83, "DS", "It is the uppermost of [margin: Call it DS.]", "", "printed", column="SD", number="60", row=83),
        word(83, "LOHOLO", "[margin: Call it Loholo.] Long, the first syllable accented.", "", "printed",
             column="OLOHOL", number="61", row=81),
        word(83, "VEP", "[margin: It is called Vep.] Make a point there. Δ. A full point? [margin: Nal. .... No, no, a stroke.]",
             "", "printed", column="PEV", number="62", row=79),
        word(83, "ZOMDV",
             "[margin: Call it Zome.] With great difficulty this Letter was discerned: Nalvage himself said, he knew it "
             "not yet; but it seemed to E. K. to be an X. Nalvage denied it to be an X. and said he knew not yet the "
             "mystery: say the Lords prayer, for I cannot open it. Although my power be multiplied, yet I know not this "
             "Letter. At length he said it was V.",
             "", "conflict", column="XVDMOZ", number="63", row=78, other="ZOMDVX, ZOME",
             remark="The reversed column prints XVDMOZ. The journal says the letter first taken for X was V, so the X is "
                    "left out here and the letters read backwards are ZOMDV. The margin says 'Call it Zome'."),
        word(83, "POAMAL",
             "[margin: Poamal Od. put out the S.] Make it two words. ..... It may be all one word with S. or T. but it "
             "would be hard for your understanding. Make a point between Poamal and Od.",
             "", "printed", column="LAMAOP", number="64", row=77),
        word(83, "OD", "DOS. He pointed beyond him in the upper Circle, it seemeth [margin: Also T] like a Roman C.",
             "", "corrected", column="DOS", correction_page=83,
             remark="The letters given are DOS. The journal says to put out the S and to make Poamal and Od two words. "
                    "On p. 90 Dee asks whether 'Poamalzod' is one word; the printed answer is 'Set down'."),
        word(83, "BOGPA", "[margin: Call it Bogpa.]", "", "printed", column="APGOB", number="65", row=76),
        word(83, "AAI", "AAI. [margin: The first A may be an A an O or an E.] [margin: Those are two words.]", "", "conflict",
             column="I, A, A", number="66", row=74, other="OAI, EAI", read_from=IMAGE,
             remark="The page image names three letters, I, A, A, and then writes the word AAI. The keyed transcription "
                    "has two of the three. The journal says the first A may be an A, an O or an E."),
        word(83, "TA", "TA. [margin: The numbers after.]", "", "printed", column="A, T", number="67", row=72),
        word(83, "PIAP", "68 PIAP.", "", "printed", column="P, A, I, P", number="68", row=68),
        word(81, "PIAMOL",
             "this O must be sounded as A. T must be instead of M. [margin: Aversed.] Call it Piamo el. It is Piatel "
             "Baltale to be sounded.",
             "", "conflict", column="L, O, M, A, I, P", number="69", other="PIATOL, PIATEL",
             remark="The letters named are L, O, M, A, I, P, which read backwards are PIAMOL, and the journal says 'Call "
                    "it Piamo el'. It also says 'T must be instead of M' and 'It is Piatel Baltale to be sounded'. On p. 82 "
                    "Dee reads the word back as 'Piamo el'."),
        word(80, "OD", "call it OD. [Δ. drawing the O long.]", "", "printed", column="D, O", number="70"),
        word(80, "VOOAN",
             "It is Vooan. It may be sounded Vaoan. Vooan is spoken with them that fall, but Vaoan with them that are, "
             "and are glorified. The devils have lost the dignity of their sounds.",
             "", "printed", column="N, A, O, O, V", number="71", row=56),
        word(80, "ZACARE", "[margin: E must come after R: but without number, and so, it is Zacare.] [margin: Call it Zacar.]",
             "", "corrected", column="R, A, C, A, Z", number="72", row=51, correction_page=80,
             remark="The letters named spell ZACAR. The margin says E must come after R, 'and so, it is Zacare'."),
        word(80, "CA", "[margin: Call it CA, [Δ. two syllables.]]", "", "printed", column="A, C", number="73", row=49),
        word(80, "OD", "[margin: This may be T or D.] Call it OD [margin: or OT.]", "", "conflict", column="T, O",
             number="74", row=46, other="OT",
             remark="The first letter named is T, with the margin 'This may be T or D'. The journal says 'Call it OD' "
                    "with the margin 'or OT'."),
        word(80, "ZAMRAN",
             "[margin: This A may be an A or an O.] [margin: be corrected it M. Zamran.] [margin: Call it Zanran.]",
             "", "corrected", column="N, A, R, N, A, Z", number="75", row=40, correction_page=80,
             remark="The letters named spell ZANRAN. The margin corrects the N to M: Zamran."),
        word(79, "ODO", "Call it O D O.", "", "printed", column="O, D, O", number="76"),
        word(79, "CICLE", "[That C. is called C Minor.] [margin: 7877.] Call it Cicle.", "", "printed",
             column="E, L, C, I, C",
             remark="The journal prints no number beside this word; the margin has 7877."),
        word(79, "QAA", "Call it QAA. [Three syllables with accent on the last A.]", "", "printed", column="A, A, Q",
             number="79"),
        word(79, "ZORGE", "Call it Zorge. [Of one syllable.]", "", "printed", column="E, G, R, O, Z", number="80"),
        word(79, "LAP", "Call it Lap.", "", "printed", column="P, A, L", number="81"),
        word(79, "ZIRDO", "Call it Zirdo.", "", "from_note", column="O, D, R, I", number="82",
             remark="The journal names four letters, O, D, R, I. The line for the fifth has a number and a table but no "
                    "letter. The Z is read from the note, 'Call it Zirdo'."),
        word(79, "NOCO", "Call it Noco.", "", "printed", column="O, C, O, N", number="83"),
        word(79, "MAD", "Call it Mad.", "", "printed", column="D, A, M", number="84"),
        word(79, "HOATH", "call it Hoath.", "", "printed", column="H, T, A, O, H", number="85"),
        word(79, "IAIDA",
             "A word, Jaida you shall understand, what that word is before the Sun go down. Jaida is the last word of "
             "the call.",
             "of the Highest", "printed", column="A, D, I, A, I", number="86",
             remark="The English is from p. 81: 'It signifieth, of the Highest.'"),
    ]
    notes = [
        "The call was given backwards, from word 86 to word 1. Words 86 to 66 were given one letter at a time; the "
        "column field lists the letters in the order the journal names them.",
        "p. 84: after 57 the journal prints OD, 56 BALTOH and PIAP, then says 'I am deceived from Ipam. OD the next is "
        "false, and so are the rest'. Those three are left out.",
        "p. 84: a DS pointed out between 51 Gono and 50 ADNA 'was corrected on Monday following to be too much'. p. 90: "
        "'You have Zurza ds Gono in the Call: the sd is too much.' It is left out.",
        "p. 90: Nalvage gives the number of words allowed as 86. The words here count 86 with Poamal and Od as two.",
    ]
    return table + hand, notes


# --- Calls 2 to 4, given backwards ----------------------------------------------

def call_2():
    words = backward(286, 337)
    return words, ["The call was given backwards, from word 52 to word 1."]


def call_3():
    words = backward(205, 285, continuation={278}, split={269: [("SOMQ", "The row prints 'HELP SOMQ' with the note 'as two words'."),
                                            ("HELP", "The row prints 'HELP SOMQ' with the note 'as two words'.")]})
    # backward() reverses the list, so the two halves of row 269 are now PLEH, QMOS. Put them in reading order.
    index = at(words, 269)
    words[index], words[index + 1] = words[index + 1], words[index]
    words[index]["english"], words[index + 1]["english"] = words[index + 1]["english"], ""
    index = at(words, 239)
    words[index]["note"] = join([words[index]["note"], "Nal. ..... It may be called Mi moag or Diuph", "Diuf"])
    index = at(words, 218)
    words[index]["note"] = join([words[index]["note"], "Od is and [margin: it must be sounded with one breath.]"])
    index = at(words, 272)
    words[index]["note"] = join([words[index]["note"], "[margin: it may be Vd L or Vnd L]"])
    index = at(words, 227)
    words[index]["remark"] = "The journal numbers this row 38. It stands between 59 and 57."
    index = at(words, 236)
    words[index]["remark"] = "The journal numbers this row 46. It stands between 50 and 48."
    return words, ["The call was given backwards, from word 80 to word 1."]


def call_4():
    words = backward(338, 389, attach_next={379})
    index = at(words, 375)
    words[index]["letters"] = letters_of(words[index]["note"])
    words[index]["remark"] = (
        "The keyers could not read the reversed column. In the page image it is LAO with a broken letter before it. "
        "The letters are read from the note 'O a li'."
    )
    return words, ["The call was given backwards, from word 47 to word 1."]


# --- Calls 5 to 18, given forwards ----------------------------------------------

def call_5():
    words = forward(
        forward_items(390, 452, skip={411, 419, 450}),
        as_word={452},
        hand={
            397: {"letters": "ADROCH", "status": "printed", "english": "", "note": "as otch; Ad roch."},
            443: {"letters": "FETHARZI", "status": "conflict", "column": "S. FETHARZI", "other": "SFETHARZI",
                  "remark": "The letter column prints 'S. FETHARZI'. The note has 'Feth ár zi' with no S."},
            452: {"letters": "IL", "status": "from_note",
                  "remark": "The letter column is empty. The note prints 'i l.'; the printing does not show whether "
                            "that is one word or two."},
        },
    )
    index = at(words, 412)
    words[index]["note"] = join(["Zod lida.", "It is a Word and a Letter.", words[index]["note"]])
    index = at(words, 417)
    del words[index]
    index = at(words, 418)
    words[index]["status"] = "corrected"
    words[index]["correction_page"] = 120
    words[index]["note"] = join([words[index]["note"], clean(ROWS[419]["cells"][0])])
    words[index]["remark"] = (
        "The journal gives ZIZOP and then ZCHIS, and says Zod-chis 'is better to be used'. ZIZOP is left out."
    )
    index = at(words, 451)
    words[index]["note"] = join([clean(ROWS[450]["cells"][1]), words[index]["note"]])
    words[index]["remark"] = (
        "Two rows have only dots in the letter column. The first has the note 'ie in as ien tle iad-as iade', which is "
        "taken as a note on the sound and not as a word. The letters are read from the second note, 'Ge jad'."
    )
    return words, ["p. 120: ZIZOP before ZCHIS is left out; the journal says Zod-chis is better to be used."]


def call_6():
    words = forward(forward_items(453, 501), attach_next={463})
    del words[at(words, 466)]
    index = at(words, 479)
    words[index].update({"letters": "FBLIARD", "status": "corrected", "column": "TBLIARD", "correction_page": 122})
    words[index]["note"] = join([words[index]["note"], "It is better if the T be made an F, and pronounced F bli ard."])
    words[index]["remark"] = "The letter column prints TBLIARD. The journal says it is better if the T be made an F."
    return words, ["p. 122: 'Put out the last Pilgin.' PIZIN after MIR is left out."]


def call_7():
    words = forward(
        forward_items(502, 554),
        attach_next={507, 518, 529, 537},
        hand={502: {"letters": "RAAS", "status": "printed", "column": "frac37; RAAS",
                    "remark": "The keyers put a fraction sign before the word."}},
    )
    return words, []


def call_8():
    words = forward(
        forward_items(555, 610),
        hand={562: {"letters": "VRAN", "status": "conflict", "column": "G or V RAN", "other": "GRAN",
                    "remark": "The letter column prints 'G or V RAN'. The note has 'V rán'."}},
    )
    return words, []


def call_9():
    words = forward(
        forward_items(611, 690),
        hand={615: {"letters": "IALPOR", "status": "printed", "english": "", "note": "Yal; I AL por.",
                    "read_from": IMAGE,
                    "remark": "The keyers could not read the first line of the note; the page image has 'Yal'."}},
    )
    index = at(words, 617)
    words.insert(index + 1, word(
        128, "P", "...... You must after E fa fa fe, put a P. [margin: Δ. This word is the 25 word backward.]", "",
        "corrected", correction_page=128,
        remark="The journal adds this after the call is given. p. 191 puts it against 'eight' in the English: 'That is P.'",
    ))
    return words, ["p. 128: 'You must after E fa fa fe, put a P.'"]


PAGE_132 = [
    ("OL", ["Ol."]), ("OANIO", ["O áni o"]), ("YOR", ["Yor."]), ("VOHIM", ["Vóh im."]), ("OL", ["Ol"]),
    ("GIZYAX", ["Giz y ax"]), ("OD", ["Od."]), ("EORS", ["E órs."]), ("COC......", ["gao.", "dg.", "Co Casg."]),
    ("PLOS...", ["Plo si."]), ("M.....I", ["Mol ui."]), ("DS", ["ds"]), ("PAGEIP", ["Pa ge ip."]),
    ("LARAG", ["La rag."]), ("OM", ["Om."]), ("DROLN", ["droln"]), ("COCASB", ["Co casb."]), ("EMNA", ["Em na"]),
    ("LPATRALX", ["El.", "L pá tralx."]), ("YOLCI", ["Yol Ci."]),
    ("MATORB", ["Ma torb.", "This word must come next after Om droln.", "Δ. This Om droln is before four words."]),
    ("NOMIG", ["big.", "No mig."]), ("MONONS", ["Mo nons."]), ("OLORA", ["O lo ra."]), ("GNAY", ["Gnay."]),
    ("ANGELARD", ["An ge lard."]), ("OHIO", ["O hi o."]), ("OHIO", ["O hio."]), ("OHIO", ["O hi o."]),
    ("OHIO", ["O hi o."]), ("OHIO", ["O hi o."]),
]
PAGE_133_CALL_10 = [
    ("OHIO", ["O hi o."]), ("NOIB", ["No ib."]), ("OHIO", ["O hi o."]), ("CAO..GON", ["Ca ós gon."]),
    ("BAGLE", ["Bagle."]), ("MADRID", ["Ma drid."]), ("I", ["I."]), ("ZIROP", ["Zi róp."]), ("CHISO", ["K", "Chi so."]),
    ("DRILPA", ["Dril pa."]), ("NIISO", ["Ni i so."]), ("CRIP", ["Crip."]), ("IP", ["Ip."]), ("NIDALI", ["Ni da li."]),
]
PAGE_133_CALL_11 = [
    ("OXIAYAL", ["Ox i Ay al."]), ("HOLDO", ["Hol do."]), ("OD", ["Od."]), (".IROM", ["Zir om."]), ("O", ["O."]),
    ("CORAXO", ["Co ráx o."]), ("DS", ["Ds."]), ("ZILDAR", ["Zil dar."]), ("RAASY", ["Ra a sy."]), ("OD", ["Od."]),
    ("VABZIR", ["Vab zir."]), ("CAMLIAX", ["Cam li ax."]), ("OD", ["Od."]), ("BAHAL", ["Ba hal."]),
    ("NIISO", ["Ni i so."]),
]


def call_10():
    items = forward_items(691, 731) + image_items(132, PAGE_132) + image_items(133, PAGE_133_CALL_10)
    words = forward(items)
    index = at(words, 702)
    words.insert(index, word(131, "OP", "Between Chis and Virq, you must put in Op a word.", "", "corrected",
                             correction_page=131))
    moved = next(index for index, entry in enumerate(words) if entry["letters"] == "MATORB")
    entry = words.pop(moved)
    entry["status"] = "corrected"
    entry["correction_page"] = 132
    entry["remark"] = (
        "The printing has MATORB after YOLCI and says 'This word must come next after Om droln'. It is placed after DROLN."
    )
    target = next(index for index, item in enumerate(words) if item["letters"] == "DROLN")
    words.insert(target + 1, entry)
    for item in words:
        if item.get("column") == "COC......":
            item["remark"] += " The first line of the note is hard to read in the image; it may be 'g as'."
    return words, [
        "p. 131: 'Between Chis and Virq, you must put in Op a word.'",
        "p. 132: MATORB 'must come next after Om droln'.",
        "pp. 132 and 133 are missing from the keyed transcription. Their words were read from the page images.",
        "p. 192: against 'a thousand' in the English the margin says 'Math. you have it not.' The printing does not "
        "say where in the call the word goes, so nothing is added.",
    ]


def repeat_of_call_1(start_letters: str, page: int, said: str) -> list[dict]:
    first, _ = CALLS[1]
    start = max(index for index, entry in enumerate(first) if entry["letters"] == start_letters)
    made = []
    for offset, entry in enumerate(first[start:]):
        made.append(word(
            page, entry["letters"], "", "", entry["status"],
            repeat_of={"call": 1, "word": start + offset + 1},
            remark=f"Not spelled here. The journal says '{said}' (p. {page}); the word is taken from the end of Call 1.",
        ))
    return made


def call_11():
    items = image_items(133, PAGE_133_CALL_11) + forward_items(732, 746)
    words = forward(items)
    index = at(words, 733)
    words[index]["note"] = join(["hotch.", words[index]["note"]])
    words[index]["read_from"] = IMAGE
    words[index]["remark"] = join([words[index].get("remark", ""),
                                   "The keyers could not read 'hotch.', which the page image prints above 'Te loch.'"])
    index = at(words, 746)
    words[index]["note"] = join(["Nonsp.", words[index]["note"]])
    words[index]["read_from"] = IMAGE
    words[index]["remark"] = join([words[index].get("remark", ""),
                                   "The keyed transcription puts 'Nonsp.' with the row above. The page image prints it "
                                   "above 'Noncp.', in the place where other rows have a note on the sound."])
    words += repeat_of_call_1("ZACARE", 193, "Then begin at the first Call, Move, as before.")
    return words, [
        "p. 133 is missing from the keyed transcription. Its words were read from the page image.",
        "p. 193: 'Then begin at the first Call, Move, as before.' The last 14 words are those of Call 1 from ZACARE.",
    ]


SCATTERED = (
    "On pp. 134 to 137 the printing runs pieces of several calls together. The pieces are put under their calls here "
    "by the first words Dee lists on p. 200, by his margin notes against the English on pp. 193 and 194, and by the "
    "order of the English there. The printing itself does not mark where each piece belongs."
)


def call_12():
    body = forward(forward_items(747, 768))
    ending = forward(
        forward_items(806, 811),
        hand={807: {"letters": "GOHUS", "status": "from_note", "column": "...............", "note": "Go hus.",
                    "read_from": IMAGE,
                    "remark": "The letter column has only dots. The keyed transcription has 'Go bus.' for the note; "
                              "the page image has 'Go hus.'"}},
    )
    words = body + ending + repeat_of_call_1(
        "ZORGE", 193, "Here must words in the end of the first Call, follow at Move, &c.")
    return words, [
        SCATTERED,
        "The six words ZACAR to QAA are printed on p. 136 after 'That is the Twelfth' and are followed by 'That is a call'.",
        "p. 193: 'Here must words in the end of the first Call, follow at Move, &c.' and 'But this Call, it differeth "
        "a little expresly.' The printing spells the ending as far as QAA; the seven words after QAA are those of Call 1.",
    ]


def call_13():
    start = forward(forward_items(812, 819))
    index = at(start, 816)
    start[index]["note"] = "O O Ao na."
    start.insert(index, word(
        136, "VX", "V x.", "", "from_note", read_from=IMAGE,
        remark="The letter column has no entry for this word. 'V x.' is printed in the note column on the line above "
               "the note of OOAONA; the keyed transcription has 'Ux.' p. 193 has '42 — Ux.' in the English.",
    ))
    middle = forward(forward_items(780, 792))
    old = old_words("13")
    tail = not_printed(old[old.index("aai"):old.index("Zacar")], "The 1659 printing does not have this word.")
    words = start + middle + tail + repeat_of_call_1("ZACARE", 193, "Move, as before, &c.")
    return words, [
        SCATTERED,
        "NAPEAI to VONPH are printed on pp. 136 and 137 after 'This is the eighth'. DOALIM to JUMD are printed on "
        "pp. 135 and 136.",
        "After JUMD the printing goes straight on to LUSDAN, which belongs to another call. The two words the call file "
        "had after it, AAI GROSB, are not in the printing.",
    ]


def call_whole_not_printed(stem: str, page: int, said: str, first_words: str):
    old = old_words(stem)
    last = max(index for index, token in enumerate(old) if token.lower() in {"zacar", "zacare"})
    body = not_printed(old[:last], "The 1659 printing does not have this call.")
    body[0]["remark"] += f" p. 200 lists its first words as '{first_words}'."
    words = body + repeat_of_call_1("ZACARE", page, said)
    return words, [
        f"The 1659 printing does not have the words of this call. p. 200 lists its first words as '{first_words}' and "
        f"pp. 193 and 194 give its English. The words here are the ones the call file had before and have no source.",
    ]


def call_14():
    return call_whole_not_printed("14", 193, "Move, as before.", "No Romi.")


def call_15():
    return call_whole_not_printed("15", 193, "Then move as before, &c.", "Ils Tabaam.")


def call_16():
    old = old_words("16")
    head = not_printed(old[:old.index("lusdan")], "The 1659 printing does not have this word.")
    head[0]["remark"] += " p. 200 lists the first words of the call as 'Ils [gap:1 word] a purt.'"
    tail = forward(forward_items(793, 803))
    words = head + tail + repeat_of_call_1("ZACARE", 194, "Move, &c.")
    return words, [
        SCATTERED,
        "Only the last nine words, LUSDAN to MADZILODARP, are printed (p. 136, before 'That is the Twelfth'). They are "
        "put here because the margin on p. 194 sets 'Emod' against 8763 in the English of the second flame.",
        "The words before LUSDAN are the ones the call file had before and have no source.",
    ]


def call_17():
    start = forward(forward_items(804, 805))
    middle = forward(
        forward_items(769, 779),
        hand={777: {"letters": "HUBARO", "status": "from_note", "column": "H.....", "note": "Hu ba ro.",
                    "read_from": IMAGE,
                    "remark": "The letter column prints 'H.....'. The keyers could not read the middle of the note; the "
                              "page image has 'Hu ba ro.'"}},
    )
    index = at(middle, 776)
    middle[index]["note"] = join([middle[index]["note"],
                                  "[margin, p. 194: Faxs — Faxes or Faxis to be sounded. I find in the Call Taxs. I finde "
                                  "also in some words T or F indifferently used.]"])
    end = forward(forward_items(820, 825))
    words = start + middle + end + repeat_of_call_1("ZACARE", 194, "Move, as before, &c.")
    return words, [
        SCATTERED,
        "ILS and DIALPERT are printed on p. 136 after 'That is the Twelfth'. SOBA to YLSI are printed on p. 135. SOBAIAD "
        "to TOATAR are printed on p. 137 before 'That is the thirteenth'.",
    ]


def call_18():
    words = forward(
        forward_items(826, 853),
        hand={827: {"letters": "MICAOLZ", "status": "from_note", "column": ".........",
                    "remark": "The letter column has only dots. The note has 'Mi ca ol zod.'; 'zod' is taken as the "
                              "letter Z, as in OMICAOLZ on p. 125, whose note is 'O mi ca ol zod.'"}},
    )
    words += repeat_of_call_1("ZACARE", 194, "Move as before.")
    return words, []


# --- The Call of the Thirty Aethyrs, pp. 201 to 209 ------------------------------

AETHYR_NAMES = [
    "Lil", "Arn", "Zom", "Paz", "Lit", "Maz", "Deo", "Zid", "Zip", "Zax", "Ich", "Loe", "Zim", "Uta", "Oxo",
    "Lea", "Tan", "Zen", "Pop", "Chr", "Asp", "Lin", "Tor", "Nia", "Uti", "Des", "Zaa", "Bag", "Rii", "Tex",
]
AETHYR_NAME_NOTES = {11: "ik.", 20: "kar in palato very much. ...."}


def aethyrs():
    words = forward(
        forward_items(1351, 1537, skip={1425}),
        attach="next",
        attach_next={1396, 1397, 1439, 1450},
        hand={
            1395: {"letters": "IDOIGO", "status": "corrected", "column": "ID*UIGO", "correction_page": 203,
                   "english": "",
                   "note": "[margin: *O] Δ. Note the wicked power dazeled so the eyes of E. K. that he could not well "
                           "discern this O, but staying at it a while concluded it to be an V: which afterward, and by "
                           "and by, he corrected.",
                   "remark": "The letter column prints ID*UIGO with *O beside it. The journal says the letter taken "
                             "for V was corrected to O, and Dee writes 'It must be then I doigo?'"},
            1515: {"letters": "OD", "status": "printed", "note": ""},
        },
    )
    index = at(words, 1395)
    words[index]["english"] = "of him that sitteth on the holy Thrana."
    words[index]["note"] = words[index]["note"].replace("; of him that sitteth on the holy Thrana.", "")
    index = at(words, 1516)
    words[index]["note"] = join(["Pur", words[index]["note"]])
    index = at(words, 1438)
    words[index]["english"] = words[index]["english"].replace("; ", " ")
    slot = at(words, 1353)
    names = []
    for number, name in enumerate(AETHYR_NAMES, start=1):
        names.append(word(209, name.upper(), AETHYR_NAME_NOTES.get(number, ""), "", "printed", number=str(number)))
    return words, slot, names


# --- writing ---------------------------------------------------------------------

BUILDERS = {
    1: (call_1, "pp. 79 to 86"), 2: (call_2, "pp. 99 and 100"), 3: (call_3, "pp. 94 to 98"),
    4: (call_4, "pp. 109 to 111"), 5: (call_5, "pp. 119 to 121"), 6: (call_6, "pp. 121 to 123"),
    7: (call_7, "pp. 123 to 125"), 8: (call_8, "pp. 125 to 127"), 9: (call_9, "pp. 127 to 130"),
    10: (call_10, "pp. 130 to 133"), 11: (call_11, "pp. 133 and 134, and p. 193"),
    12: (call_12, "pp. 134 to 136, and p. 193"), 13: (call_13, "pp. 135 to 137, and p. 193"),
    14: (call_14, "not printed; p. 193 for the ending"), 15: (call_15, "not printed; p. 193 for the ending"),
    16: (call_16, "p. 136, and p. 194"), 17: (call_17, "pp. 135 to 137, and p. 194"),
    18: (call_18, "pp. 137 and 138, and p. 194"),
}
DIRECTION = {1: "backward", 2: "backward", 3: "backward", 4: "backward"}
CALLS: dict[int, tuple[list[dict], list[str]]] = {}

PRINTING = "Meric Casaubon, A True & Faithful Relation (London, 1659)"


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for number, (builder, pages) in BUILDERS.items():
        CALLS[number] = builder()
        words, notes = CALLS[number]
        mark_image_readings(words)
        for entry in words:
            if not entry["letters"]:
                raise ValueError(f"call {number}: a word has no letters: {entry}")
            counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        data = {
            "call": number,
            "printing": PRINTING,
            "pages": pages,
            "direction": DIRECTION.get(number, "forward"),
            "notes": notes,
            "words": words,
        }
        (DEST / f"{number:02d}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{number:02d}: {len(words)} words")
    words, slot, names = aethyrs()
    mark_image_readings(words)
    data = {
        "call": "aethyrs",
        "printing": PRINTING,
        "pages": "pp. 201 to 209",
        "direction": "forward",
        "notes": [
            "One call serves all thirty Aethyrs. p. 209: 'Now change the name, and the Call is all one.'",
            "name_word is the place of the name in words, counted from 0. The call as dictated has LIL there.",
            "names are the thirty names as p. 209 prints them, in order.",
        ],
        "name_word": slot,
        "words": words,
        "names": names,
    }
    (DEST / "aethyrs.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for entry in words:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    print(f"aethyrs: {len(words)} words, name at word {slot}, {len(names)} names")
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
