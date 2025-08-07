#!/usr/bin/sh
read -p "Wine ARM64EC Docker build script
Fedora 42 required
Press enter to continue
"

FEDORA_VERSION=42

WINE_VERSION=10.12
WINE_TARGET="wine-${WINE_VERSION}"

FEX_VERSION=2508.1
FEX_TARGET="fex-emu-wine-${FEX_VERSION}"

DXVK_VERSION=2.7
DXVK_TARGET="wine-dxvk-${DXVK_VERSION}"

SCRIPT_DIR="${PWD}/${WINE_TARGET}_${FEX_TARGET}"
mkdir -p $SCRIPT_DIR

set -eu
echo "Building ${WINE_TARGET} and ${FEX_TARGET}
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
rpmdev-setuptree
cd "${BUILD_DIR}"
dnf download --source wine
rpm -ivh wine-*.src.rpm

cp /host/*.patch "${BUILD_DIR}/SOURCES/"
dnf builddep -y "/host/fex-emu-wine.spec" --allowerasing
dnf builddep -y "/host/wine.spec" --allowerasing
# dnf builddep -y "/host/wine-dxvk.spec" --allowerasing

spectool -g -R "/host/fex-emu-wine.spec"
spectool -g -R "/host/wine.spec"
# spectool -g -R "/host/wine-dxvk.spec"
rpmbuild -ba "/host/fex-emu-wine.spec"
rpmbuild -ba "/host/wine.spec"
# rpmbuild -ba "/host/wine-dvxk.spec"
cp -r ${BUILD_DIR}/RPMS/aarch64/* /out/
cp -r ${BUILD_DIR}/RPMS/noarch/* /out/
exit
EOF
chmod +x "$TMP_SCRIPT"

#   Create setup script for installing the built packages.   #
cat > "setup-wine.sh" <<'EOF'
read -p "Installing wine and fex-emu-wine packages
"
sudo dnf install ./*arch*.rpm --skip-unavailable

read -p "Updating current wine prefix
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
