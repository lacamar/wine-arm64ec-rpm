# wine-aarch64-rpm
RPM specs for Wine and FEXEmu Wine DLLs with experimental ARM64EC support.

This will let you run Windows 32bit and 64bit software on an aarch64 16k Linux host (e.g. Asahi Linux).

Using Wine in this configuration is very prone to bugs, so you should expect most software to not run. This is an area of the Wine and FEX projects that is being actively developed, so support is improving.

Wine is built from mainline wine sources and wine-staging patches with patches from the bylaws [upstream-arm64ec branch](https://github.com/bylaws/wine/tree/upstream-arm64ec).

For building FEXEmu Wine DLLs, it uses this LLVM-Mingw toolchain provided by the [bylaws' branch](https://github.com/bylaws/llvm-mingw).

The RPMs built from these specs are available on my [Copr repo](https://copr.fedorainfracloud.org/coprs/lacamar/wine-arm64ec/).

Add the Copr repo and install the packages it provides to use Wine without having to build them.

```
sudo dnf copr enable lacamar/wine-arm64ec
sudo dnf install fex-emu-wine wine
```

To rebuild the packages locally, use `mock`:

```
dnf download --source fex-emu-wine wine
mock -r fedora-44-aarch64 -a https://download.copr.fedorainfracloud.org/results/lacamar/wine-arm64ec/fedora-44-aarch64/ --rebuild fex-emu-wine-*.src.rpm wine-*.src.rpm
```

## Arch Linux ARM

PKGBUILDs in `arch/`. Prebuilt packages (aarch64) are in the `arch-repo` release. Add to `/etc/pacman.conf`:

```
[wine-arm64ec]
SigLevel = Optional TrustAll
Server = https://github.com/lacamar/wine-arm64ec-rpm/releases/download/arch-repo
```

```
sudo pacman -Sy wine wine-dxvk wine-vkd3d-proton
```

To build locally, run `arch/build.sh fex-emu-wine wine-mono wine-gecko wine wine-dxvk wine-vkd3d-proton wine-d7vk` (expects the repo at `/src`).

Maintainers: `arch/publish.sh` rebuilds stale packages and updates the release.
