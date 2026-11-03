#!/bin/bash
# Rebuild PKGBUILDs whose packages are missing from the repo, then sync the arch-repo release.
set -e
R=~/.cache/wine-arm64ec-dev/arch/repo
A=~/.cache/wine-arm64ec-dev/arch
c() { podman exec -u "$(id -u)" -w "/src/arch/$1" alarm-build bash -c "$2"; }
if ! podman container exists alarm-build; then
  mkdir -p $R $A/{pkgs,build,src}
  podman run -d --name alarm-build --userns=keep-id --security-opt label=disable -v "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)":/src:ro \
    -v $R:/a/repo -v $A/pkgs:/a/pkgs -v $A/build:/a/build -v $A/src:/a/src \
    docker.io/menci/archlinuxarm:latest sleep infinity
  podman exec -u 0 alarm-build bash -c 'sed -i "/^\[options\]/a DisableSandbox" /etc/pacman.conf; pacman-key --init >/dev/null && pacman-key --populate archlinuxarm >/dev/null
    pacman -Syu --noconfirm --needed base-devel git sudo >/dev/null
    echo "'"$(id -un)"' ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/b
    printf "PKGDEST=/a/pkgs\nBUILDDIR=/a/build\nSRCDEST=/a/src\n" >>/etc/makepkg.conf'
fi
podman start alarm-build >/dev/null
for d in fex-emu-wine-git wine-mono wine-gecko wine-git wine-dxvk-git wine-vkd3d-proton-git wine-d7vk-git; do
  new=$(for p in $(c $d 'makepkg --packagelist'); do [ -e "$R/${p##*/}" ] || echo "${p##*/}"; done)
  [ -n "$new" ] || continue
  echo "== $d"
  c $d 'sudo pacman -Sy >/dev/null && makepkg -Ccsf --noconfirm --needed && f=$(makepkg --packagelist) && cp $f /a/repo/ && cd /a/repo && repo-add -R wine-arm64ec.db.tar.gz ${f//\/a\/pkgs\//}'
  (cd $R && gh release upload arch-repo --repo lacamar/wine-arm64ec-rpm --clobber $new wine-arm64ec.{db,files}{,.tar.gz})
done
gh release view arch-repo --repo lacamar/wine-arm64ec-rpm --json assets -q '.assets[].name' | while read -r a; do
  [ -e "$R/$a" ] || gh release delete-asset arch-repo "$a" --repo lacamar/wine-arm64ec-rpm -y
done
