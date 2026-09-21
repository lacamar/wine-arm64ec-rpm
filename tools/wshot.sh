#!/bin/bash
# usage: wshot.sh <niri window id | exact title> <out.png>; keeps the clipboard and does not take focus
[ -n "$2" ] || { echo "usage: wshot.sh <window id | exact title> <out.png>"; exit 1; }
out=$(realpath -m "$2")
id=$(niri msg -j windows | python3 -c '
import json, sys
key = sys.argv[1]
wins = json.load(sys.stdin)
m = [w["id"] for w in wins if str(w["id"]) == key or w.get("title") == key]
print(m[0] if m else "")' "$1")
[ -n "$id" ] || { echo "no window $1"; exit 1; }
niri msg -j focused-window | grep -q '"id"' || echo "warning: no focused window, niri may skip the screenshot" >&2

clip=$(mktemp)
timeout 3 wl-paste --no-newline > "$clip" 2>/dev/null; had=$?
rm -f "$out"
timeout 10 niri msg action screenshot-window --id "$id" --write-to-disk true --path "$out" >/dev/null
last=-1
for _ in $(seq 40); do
    size=$(stat -c %s "$out" 2>/dev/null || echo 0)
    [ "$size" -gt 0 ] && [ "$size" = "$last" ] && break
    last=$size
    sleep 0.5
done
[ $had = 0 ] && [ -s "$clip" ] && timeout 3 wl-copy < "$clip"
rm -f "$clip"
[ -s "$out" ] || { echo "screenshot failed"; exit 1; }
python3 -c "from PIL import Image; print(Image.open('$out').size)" 2>/dev/null
