#!/bin/sh
# Cut every manuscript page of the 48 Claves into reading strips.
# sloane-call-regions.txt has one line per page of a call:
# page crop, call, left, width, top, bottom (pixels in the page crop).
here="$(dirname "$0")"
while read -r name call left width top bottom; do
  [ -z "$name" ] && continue
  sh "$here/sloane-strips.sh" "$name" "$left" "$width" "$top" "$bottom" 620
done < "$here/sloane-call-regions.txt"
