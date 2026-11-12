#!/bin/sh
# Cut the film strips that hold the 48 Claves (PDF pages 2 to 4) into single
# manuscript pages. Columns: name, strip, left edge, width (pixels in the strip).
# Usage: sh tools/sloane/sloane-crop.sh     (writes scratch/sloane-pages/ms/)
cd "$(dirname "$0")/../../scratch/sloane-pages" || exit 1
mkdir -p ms
while read -r name strip left width; do
  [ -z "$name" ] && continue
  height=$(sips -g pixelHeight "$strip" | awk '/pixelHeight/ {print $2}')
  sips -c "$height" "$width" --cropOffset 0 "$left" "$strip" --out "ms/$name.jpg" >/dev/null 2>&1
  echo "$name $strip $left $width"
done <<'TABLE'
s02-f2r page-02.jpg 8100 2100
s02-f3l page-02.jpg 10400 2000
s02-f3r page-02.jpg 12200 2100
s02-f4l page-02.jpg 14480 2000
s02-f4r page-02.jpg 16280 2100
s02-f5l page-02.jpg 18520 2000
s02-f5r page-02.jpg 20320 2047
s03-f1l page-03.jpg 40 2000
s03-f1r page-03.jpg 1860 2050
s03-f2l page-03.jpg 4130 2000
s03-f2r page-03.jpg 5940 2050
s03-f3l page-03.jpg 8230 2000
s03-f3r page-03.jpg 10040 2050
s03-f4l page-03.jpg 12310 2000
s03-f4r page-03.jpg 14140 2050
s03-f5l page-03.jpg 16400 2000
s03-f5r page-03.jpg 18220 2050
s03-f6l page-03.jpg 20460 2000
s03-f6r page-03.jpg 22270 2100
s04-f1l page-04.jpg 150 1800
s04-f1r page-04.jpg 1850 1900
TABLE
