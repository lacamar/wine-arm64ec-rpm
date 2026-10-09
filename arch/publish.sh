#!/bin/bash
# Rebuild PKGBUILDs whose packages are missing from the repo, then sync the arch-repo release.
set -e
R=~/.cache/wine-arm64ec-dev/arch/repo
c() { podman exec -w "/src/arch/$1" alarm-build bash -c "$2"; }
podman start alarm-build >/dev/null
for d in fex-emu-wine fex-emu-wine-git wine-mono wine-gecko wine wine-git wine-dxvk wine-vkd3d-proton wine-d7vk; do
  new=$(for p in $(c $d 'makepkg --packagelist'); do [ -e "$R/${p##*/}" ] || echo "${p##*/}"; done)
  [ -n "$new" ] || continue
  echo "== $d"
  c $d 'pacman -Sy >/dev/null && updpkgsums && makepkg -Ccsf --noconfirm --needed && f=$(makepkg --packagelist) && cp $f /a/repo/ && cd /a/repo && repo-add -R wine-arm64ec.db.tar.gz ${f//\/a\/pkgs\//}'
  (cd $R && gh release upload arch-repo --repo lacamar/wine-arm64ec-rpm --clobber $new wine-arm64ec.{db,files}{,.tar.gz})
done
gh release view arch-repo --repo lacamar/wine-arm64ec-rpm --json assets -q '.assets[].name' | while read -r a; do
  [ -e "$R/$a" ] || gh release delete-asset arch-repo "$a" --repo lacamar/wine-arm64ec-rpm -y
done
