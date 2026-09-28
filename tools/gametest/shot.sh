#!/usr/bin/env bash
# shot.sh <slug> [secs]  launch headless, screenshot after secs
S=${XDG_CACHE_HOME:-$HOME/.cache}/wine-arm64ec-dev/gametest; mkdir -p $S/logs
slug=$1-test-claude secs=${2:-45}
P=/home/lm/.local/share/wine-prefixes/$slug
env WAYLAND_DISPLAY=wayland-2 DISPLAY= setsid lutris -d lutris:rungame/$slug > $S/logs/$1-shot.log 2>&1 < /dev/null &
sleep $secs
WAYLAND_DISPLAY=wayland-2 grim $S/shot-$1.png
WAYLAND_DISPLAY=wayland-2 swaymsg -t get_tree 2>/dev/null | grep -oE '"name": "[^"]+"' | sort -u | tr '\n' ' '; echo
WINEPREFIX=$P wineserver -k 2>/dev/null; pkill -f "lutris:rungame/$slug"; sleep 2
