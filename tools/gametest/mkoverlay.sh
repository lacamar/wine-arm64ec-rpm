#!/usr/bin/env bash
# mkoverlay.sh <dir> [relpath=src ...]  wine tree of symlinks to /usr with real copies of the loader, ntdll.so and overrides
set -eu
X=$1; shift
command rm -rf "$X"
mkdir -p "$X/bin" "$X/lib64/wine" "$X/share"
for f in /usr/bin/wine* /usr/bin/msidb; do [ -e "$f" ] && ln -sf "$f" "$X/bin/$(basename "$f")"; done
command rm -f "$X/bin/wine"
cp -L /usr/bin/wine "$X/bin/wine"
ln -s /usr/share/wine "$X/share/wine"
for d in /usr/lib64/wine/*; do
    n=$(basename "$d")
    case $n in
    aarch64-unix|aarch64-windows|i386-windows)
        mkdir -p "$X/lib64/wine/$n"
        for f in "$d"/*; do ln -sf "$f" "$X/lib64/wine/$n/$(basename "$f")"; done ;;
    *) ln -s "$d" "$X/lib64/wine/$n" ;;
    esac
done
for f in wine wine-preloader ntdll.so; do command rm -f "$X/lib64/wine/aarch64-unix/$f"; cp -L "/usr/lib64/wine/aarch64-unix/$f" "$X/lib64/wine/aarch64-unix/$f"; done
for spec in "$@"; do
    dst=${spec%%=*} src=${spec#*=}
    command rm -f "$X/$dst"
    cp -L "$src" "$X/$dst"
done
