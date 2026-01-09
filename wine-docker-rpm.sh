#!/usr/bin/sh
read -p "Wine ARM64EC Docker build script
Fedora 42+ required

Press enter to continue
"

FEDORA_VERSION=42

WINE_VERSION=git
WINE_TARGET="wine-${WINE_VERSION}"

FEX_VERSION=git
FEX_TARGET="fex-emu-wine-${FEX_VERSION}"

DXVK_VERSION=git
DXVK_TARGET="wine-dxvk-${DXVK_VERSION}"

SCRIPT_DIR="${PWD}/${WINE_TARGET}_${FEX_TARGET}_${DXVK_TARGET}"
mkdir -p $SCRIPT_DIR

set -eu
echo "Building ${WINE_TARGET} and ${FEX_TARGET} (latest release).
"

# Copying needed files to build output directory visible in docker
cp wine/*.patch $SCRIPT_DIR
cp wine/${WINE_TARGET}.spec $SCRIPT_DIR/wine.spec
cp fex-emu-wine/${FEX_TARGET}.spec $SCRIPT_DIR/fex-emu-wine.spec
cp wine-dxvk/${DXVK_TARGET}.spec $SCRIPT_DIR/wine-dxvk.spec
cd $SCRIPT_DIR

#   Create temporary nested script to run inside docker   #
TMP_SCRIPT="docker-${WINE_TARGET}_${FEX_TARGET}.sh"
cat > "$TMP_SCRIPT" <<'EOF'
#!/bin/bash
set -euo pipefail
export BUILD_DIR=~/rpmbuild
echo "max_parallel_downloads=20" >> /etc/dnf/dnf.conf
dnf install rpm-build zip rpmdevtools gcc make wget llvm-devel clang mingw64-gcc mingw32-gcc libnetapi-devel libxkbcommon-devel wayland-devel ffmpeg-free-devel -y
sudo dnf copr enable lacamar/wine-arm64ec -y
rpmdev-setuptree
cd "${BUILD_DIR}"
dnf download --source wine
rpm -ivh wine-*.src.rpm

cp /host/*.patch "${BUILD_DIR}/SOURCES/"
dnf builddep -y "/host/fex-emu-wine.spec" --allowerasing
dnf builddep -y "/host/wine.spec" --allowerasing
dnf builddep -y "/host/wine-dxvk.spec" --allowerasing

spectool -g -R "/host/fex-emu-wine.spec"
spectool -g -R "/host/wine.spec"
spectool -g -R "/host/wine-dxvk.spec"
rpmbuild -ba "/host/fex-emu-wine.spec"
rpmbuild -ba "/host/wine.spec"
rpmbuild -ba "/host/wine-dxvk.spec"
mkdir -p /out/fex-emu-wine
mkdir -p /out/wine
mkdir -p /out/wine-dxvk
mv ${BUILD_DIR}/RPMS/aarch64/wine-dxv* /out/wine-dxvk/
mv ${BUILD_DIR}/RPMS/aarch64/fex-emu-wine* /out/fex-emu-wine/
cp -r ${BUILD_DIR}/RPMS/aarch64/wine* /out/wine/
cp -r ${BUILD_DIR}/RPMS/noarch/wine* /out/wine/
exit
EOF
chmod +x "$TMP_SCRIPT"

#   Create setup script for installing the built packages.   #
cat > "setup-wine.sh" <<'EOF'
read -p "Installing wine and fex-emu-wine packages.
Press enter
"
sudo dnf install \
--skip-broken \
--skip-unavailable \
--allowerasing \
./fex-emu-wine/*.rpm \
./wine-dxvk/*.rpm \
./wine/*.rpm

read -p "
Updating current wine prefix.
Press enter
"
wineboot -u
EOF

echo "Starting docker
"
docker run -e -it --rm -v "$PWD:/out:z" -v "$PWD:/host:z" fedora:${FEDORA_VERSION} ./host/$TMP_SCRIPT

echo "Exiting docker
"
rm "$TMP_SCRIPT"
rm *.patch
rm *.spec

echo "Executing setup script
"
chmod +x setup-wine.sh
./setup-wine.sh

echo "
Done!
"
