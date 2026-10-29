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
sudo dnf install fex-emu-wine wine            # latest releases
sudo dnf install fex-emu-wine-git wine-git   # or follow upstream HEAD
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
sudo pacman -Sy wine-git wine-dxvk-git wine-vkd3d-proton-git
```

To build locally, run `arch/build.sh fex-emu-wine-git wine-mono wine-gecko wine-git wine-dxvk-git wine-vkd3d-proton-git wine-d7vk-git` (expects the repo at `/src`). The -git PKGBUILDs read commit, refs and patch lists from the RPM specs, so they follow spec bumps; checksums are skipped.

Maintainers: `arch/publish.sh` rebuilds stale packages and updates the release.

## Development

Each package has `<name>.spec` (latest release) and `<name>-git.spec` (upstream HEAD).

```
just lint          # rpmlint staged specs
just test          # precheck specs changed since upstream
tools/bump SPEC    # move a spec to upstream's latest release / HEAD
just ci [SPEC]     # bump, build, A/B-test against the shipped build (report only)
just ci-timer      # daily CI run via a systemd user timer
```

The CI runs on an Asahi machine (aarch64, 16K pages): Wine's winetest modules, FEX's ASM suites
through the shipped FEX DLLs, vkd3d-proton's d3d12 suite and `ci/tests/hostpage.c` (4K guest pages
on 16K host pages), comparing each candidate with the build currently on COPR.
