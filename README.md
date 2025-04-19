# wine-aarch64-rpm-builder
Script for building Wine RPM packages on aarch64 with ARM64EC suppport


This is a bash script that utilises docker instance to build Fedora42 RPMs on aarch64 for Wine that include ARM64EC support.
Additionally, the script automatically installs these Wine RPMs and the necessary DLLs from the FEX project for ARM64EC support before setting the necessary registry keys to use Wine with ARM64EC support.
