#!/usr/bin/env bash
# lt.sh <slug> [secs]  launch a -test-claude Lutris entry headless, summarise
S=${XDG_CACHE_HOME:-$HOME/.cache}/wine-arm64ec-dev/gametest; mkdir -p $S/logs
slug=$1-test-claude secs=${2:-60}
P=/home/lm/.local/share/wine-prefixes/$slug
log=$S/logs/$1.log
start=$(date +%s)
env WAYLAND_DISPLAY=wayland-2 DISPLAY= WINEDEBUG=+fps,err+seh,err+virtual,err+module setsid lutris -d lutris:rungame/$slug > $log 2>&1 < /dev/null &
lp=$!
end=$((start+secs+60))
alive=0 first=0
while [ $(date +%s) -lt $end ]; do
    sleep 5
    if [ $first = 0 ] && grep -q 'approx' $log; then first=$(date +%s); end=$((first+secs)); fi
    grep -q 'Game thread stopped\|Process .* has terminated' $log && break
done
dur=$(( $(date +%s) - start ))
running=$(pgrep -f "wine-prefixes/$slug" >/dev/null || WINEPREFIX=$P wineserver -k0 2>/dev/null; WINEPREFIX=$P timeout 2 wineserver -w 2>/dev/null; echo $?)
exited=no; grep -q 'has terminated with code' $log && exited=$(grep -o 'has terminated with code [0-9-]*' $log | tail -1 | awk '{print $NF}')
WINEPREFIX=$P wineserver -k 2>/dev/null; kill $lp 2>/dev/null; pkill -f "lutris:rungame/$slug" 2>/dev/null; sleep 2
printf '%-28s t=%-4s presents=%-4s exit=%-5s unhandled=%-3s errs=%s\n' "$1" "$dur" "$(grep -c approx $log)" "$exited" \
  "$(grep -ciE 'Unhandled (page fault|exception)|nested exception|abort_thread' $log)" "$(grep -cE 'err:(virtual|module|seh)' $log)"
