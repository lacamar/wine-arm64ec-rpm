# wine-aarch64-rpm-builder
This is a script for building Wine and FEXEmu Wine DLLs RPMs with experimental ARM64EC support. The script also installs these packages automatically once the build is finished.

This will let you run Windows 32bit and 64bit software on an aarch64 16k Linux host (e.g. Asahi Linux).

Using Wine in this configuration is very prone to bugs, so you should expect most software to not run. This is an area of the Wine and FEX projects that is being actively developed, so support is improving.

This script builds wine by taking mainline wine sources and wine-staging patches then applies patches from the bylaws [upstream-arm64ec branch](https://github.com/bylaws/wine/tree/upstream-arm64ec).

For building FEXEmu Wine DLLs, it uses this LLVM-Mingw toolchain provided by the [bylaws' branch](https://github.com/bylaws/llvm-mingw).

To use this script to generate wine packages, you must have a working docker install on your system. If you haven't set up docker, you can run ```first-time-docker.sh```.

The RPMs built using this script are available on my [Copr repo](https://copr.fedorainfracloud.org/coprs/lacamar/wine-arm64ec/).

Add the Copr repo and install the packages it provides to use Wine without having to build them.

```
sudo dnf copr enable lacamar/wine-arm64ec
sudo dnf install fex-emu-wine "wine-*"
```
