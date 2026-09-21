#!/bin/bash
# kills Wine processes whose argv[0] basename is the given exe; pkill -f would match the calling shell
[ -n "$1" ] || { echo "usage: wkill.sh <exe name>"; exit 1; }
for p in $(pgrep -f -- "$1"); do
    name=$(tr '\0' '\n' < /proc/$p/cmdline 2>/dev/null | head -1 | sed 's,.*[/\\],,')
    [ "$name" = "$1" ] && kill "$p"
done
exit 0
