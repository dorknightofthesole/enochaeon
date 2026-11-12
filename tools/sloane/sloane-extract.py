"""Write each page image of the Sloane 3191 scan to scratch/sloane-pages/.

The scan stores each page as one JPEG. The JPEG bytes are copied out of the
PDF as they are, so nothing is decoded or re-compressed here.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "998222247-Dee-MS-Sloane-3191.pdf"
DEST = ROOT / "scratch" / "sloane-pages"


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(SOURCE))
    for number, page in enumerate(reader.pages, start=1):
        objects = page["/Resources"].get("/XObject", {})
        images = [objects[name].get_object() for name in objects
                  if objects[name].get_object().get("/Subtype") == "/Image"]
        box = page.mediabox
        print(f"page {number}: {len(images)} image(s), page box {float(box.width):.0f} x {float(box.height):.0f}, "
              f"rotate {page.get('/Rotate', 0)}")
        for index, image in enumerate(images):
            kind = image.get("/Filter")
            print(f"  {image['/Width']} x {image['/Height']}, filter {kind}")
            if kind != "/DCTDecode":
                raise ValueError(f"page {number}: image is not a JPEG ({kind})")
            name = f"page-{number:02d}{'' if len(images) == 1 else f'-{index}'}.jpg"
            (DEST / name).write_bytes(image._data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
