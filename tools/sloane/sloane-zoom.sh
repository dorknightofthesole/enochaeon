#!/bin/sh
# Cut one piece of a manuscript page at full size for a closer look.
# Usage: sh tools/sloane/sloane-zoom.sh NAME X Y WIDTH HEIGHT OUT   (writes scratch/sloane-pages/zoom/)
cd "$(dirname "$0")/../../scratch/sloane-pages" || exit 1
mkdir -p zoom
sips -c "$5" "$4" --cropOffset "$3" "$2" "ms/$1.jpg" --out "zoom/$6.jpg" >/dev/null 2>&1 && echo "zoom/$6.jpg"
