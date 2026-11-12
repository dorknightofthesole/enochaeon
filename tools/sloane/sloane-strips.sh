#!/bin/sh
# Cut one manuscript page (scratch/sloane-pages/ms/NAME.jpg) into overlapping
# horizontal strips for reading. Usage: sh tools/sloane/sloane-strips.sh NAME LEFT WIDTH TOP BOTTOM [HEIGHT]
cd "$(dirname "$0")/../../scratch/sloane-pages" || exit 1
name=$1; left=$2; width=$3; top=$4; bottom=$5; height=${6:-560}
mkdir -p strips
step=$((height - 90))
i=0; y=$top
while [ "$y" -lt "$bottom" ]; do
  sips -c "$height" "$width" --cropOffset "$y" "$left" "ms/$name.jpg" --out "strips/$name-$i.jpg" >/dev/null 2>&1
  i=$((i + 1)); y=$((y + step))
done
echo "$name: $i strips"
