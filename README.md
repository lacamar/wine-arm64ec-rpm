# wine-aarch64-rpm-builder
A script for building Wine RPM packages on aarch64 with ARM64EC suppport



This is a bash script that utilises docker to build Fedora42 RPMs on aarch64 for Wine that include ARM64EC support.
Additionally, the script automatically installs these Wine RPMs and the necessary DLLs from the FEX project for ARM64EC before setting the necessary registry keys to use Wine with ARM64EC support.

To use this script to generate wine packages, you must have a working docker install on your system. If you haven't set up docker, you can run first-time-docker.sh.

This script uses this wine branch from bylaws https://github.com/bylaws/wine/tree/upstream-arm64ec

Also this LLVM MinGW branch from bylaws https://github.com/bylaws/llvm-mingw

Source for the FEX arm64ec and wow64 DLLs https://launchpad.net/~fex-emu/+archive/ubuntu/fex/+packages
