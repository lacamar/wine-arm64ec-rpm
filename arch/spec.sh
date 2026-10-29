_g() { sed -n "s/^%global $1 \+//p" "$_spec" | head -1; }
_tag=$(_g tag) _bump=$(_g bumpver) _commit=$(_g commit)
_rel=$(sed -n 's/^Release: *//p' "$_spec")
_rel=${_rel#*-b }
pkgver=$_tag.r$_bump.g${_commit::7}
pkgrel=${_rel//[!0-9]/}
_mingw=llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64
_mingwsrc=https://github.com/bylaws/llvm-mingw/releases/download/20250920/$_mingw.tar.xz

_ext=()
while IFS= read -r _l; do
  [[ $_l =~ name=\"([^\"]+)\".*ref=\"([^\"]+)\".*owner=\"([^\"]+)\" ]] || continue
  _n=${BASH_REMATCH[1]} _r=${BASH_REMATCH[2]} _o=${BASH_REMATCH[3]} _p=${BASH_REMATCH[1]}
  [[ $_l =~ paths?=\{?\"([^\"]+)\" ]] && _p=${BASH_REMATCH[1]}
  _ext+=("$_o/$_n $_r $_p")
done < "$_spec"

_extsrc() {
  local e o r
  for e in "${_ext[@]}"; do
    read -r o r _ <<<"$e"
    echo "${o#*/}-$r.tar.gz::https://github.com/$o/archive/$r.tar.gz"
  done | awk '!s[$0]++'
}

_unpack_ext() {
  local e o r d
  for e in "${_ext[@]}"; do
    read -r o r d <<<"$e"
    mkdir -p "$1$d"
    cp -a "$srcdir"/${o#*/}-$r*/. "$1$d/"
  done
}

_cross() {
  local a c
  for a; do
    c=aarch64; [ $a = i686 ] && c=x86
    printf "[binaries]\nar='$a-w64-mingw32-ar'\nc='$a-w64-mingw32-gcc'\ncpp='$a-w64-mingw32-g++'\nld='$a-w64-mingw32-ld'\nwindres='$a-w64-mingw32-windres'\nwidl='$a-w64-mingw32-widl'\nstrip='$a-w64-mingw32-strip'\n[host_machine]\nsystem='windows'\ncpu_family='$c'\ncpu='${a/arm64ec/aarch64}'\nendian='little'\n" > ../cross-$a.txt
  done
}

_dll() {
  install -Dm644 $(find "$srcdir/$_srcdir/build-$1" -name $3.dll) "$pkgdir/usr/lib/wine/$2-windows/$_name-$3.dll"
  winebuild --builtin "$pkgdir/usr/lib/wine/$2-windows/$_name-$3.dll"
}
