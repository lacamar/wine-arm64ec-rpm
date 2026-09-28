#!/usr/bin/env bash
# gbeswap.sh <appid> <dll path> [exe]
C=/home/lm/.steam/steam/steamapps/common
G=/home/lm/Software/gaming/GBE_fork/windows_release/regular
appid=$1 dll="$C/$2" exe=${3:+$C/$3}
dir=$(dirname "$dll") base=$(basename "$dll" .dll)
case $base in steam_api64) src=$G/x64/steam_api64.dll;; steam_api) src=$G/x32/steam_api.dll;; *) echo "bad $dll"; exit 1;; esac
orig="$dir/$base#.dll"
[ -e "$orig" ] || command mv -n "$dll" "$orig"
command cp -f "$src" "$dll"
[ -e "$dir/steam_interfaces.txt" ] || cat "$orig" ${exe:+"$exe"} | grep -a -o -E 'STEAM[A-Z]*_INTERFACE_VERSION[0-9]+|Steam(Client|User|Friends|Utils|MatchMaking|MatchMakingServers|Networking|Apps|GameServer|GameServerStats|Controller|Input|Video|Parties)[0-9]{3}' | sort -u > "$dir/steam_interfaces.txt"
[ -e "$dir/steam_appid.txt" ] || echo "$appid" > "$dir/steam_appid.txt"
echo "$2: $(wc -l < "$dir/steam_interfaces.txt") interfaces, appid $(cat "$dir/steam_appid.txt")"
