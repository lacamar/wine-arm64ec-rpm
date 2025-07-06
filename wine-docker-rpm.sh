#!/usr/bin/sh
read -p "Wine ARM64EC Docker build script. Fedora 42 required. Press enter to continue."
PACKAGE=wine
VERSION=10.8
RELEASE=2
TARGET="${PACKAGE}-${VERSION}-${RELEASE}"
SCRIPT_DIR="${PWD}/${TARGET}"
mkdir -p $SCRIPT_DIR

set -eouv
#-----------------------------------#
#   Wine ARM64EC RPM build script   #
#-----------------------------------#


#   Create temporary nested script to run inside docker   #
cp wine-arm64ec-compat.patch $SCRIPT_DIR
cp wine-arm64ec.spec $SCRIPT_DIR/wine.spec
cp fex-emu-wine.spec $SCRIPT_DIR
cd $SCRIPT_DIR

TMP_SCRIPT="docker-${TARGET}.sh"
cat > "$TMP_SCRIPT" <<'EOF'
#!/bin/bash
set -euov pipefail
export BUILD_DIR=~/rpmbuild
echo "max_parallel_downloads=20" >> /etc/dnf/dnf.conf
dnf install rpm-build zip rpmdevtools gcc make wget llvm-devel clang mingw64-gcc mingw32-gcc libnetapi-devel libxkbcommon-devel wayland-devel ffmpeg-free-devel -y
rpmdev-setuptree
cd "${BUILD_DIR}"
dnf download --source ${PACKAGE}
rpm -ivh ${PACKAGE}-*.src.rpm

cp "/host/wine-arm64ec-compat.patch" "${BUILD_DIR}/SOURCES/wine-arm64ec-compat.patch"
dnf builddep -y "/host/${PACKAGE}.spec" --allowerasing
dnf builddep -y "/host/fex-emu-wine.spec" --allowerasing

spectool -g -R "/host/${PACKAGE}.spec"
spectool -g -R "/host/fex-emu-wine.spec"
rpmbuild --nodebuginfo -ba "/host/fex-emu-wine.spec"
rpmbuild --nodebuginfo -ba "/host/${PACKAGE}.spec"
cp -r ${BUILD_DIR}/RPMS/aarch64/* /out/
cp -r ${BUILD_DIR}/RPMS/noarch/* /out/
exit
EOF
chmod +x "$TMP_SCRIPT"

#   Create setup script for installing the Wine ARM64EC build, installing the FEX DLLs, and importing the registry entries.   #
cat > "setup-wine.sh" <<'EOF'
sudo dnf install ./*arch*.rpm --skip-unavailable
wineboot -u
EOF

#   Starting docker   #
docker run -e PACKAGE=${PACKAGE} -e VERSION=${VERSION} -e RELEASE=${RELEASE} -e TARGET=${TARGET} -it --rm -v "$PWD:/out:z" -v "$PWD:/host:z" fedora:42 ./host/$TMP_SCRIPT

#   Exiting to host   #
rm "$TMP_SCRIPT"
rm wine-arm64ec-compat.patch
rm *.spec

#   Execute setup script   #
chmod +x setup-wine.sh
./setup-wine.sh

#   Done!   #
