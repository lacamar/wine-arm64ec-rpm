#!/usr/bin/sh
read -p "Wine ARM64EC Docker build script. Fedora 42 required. Press enter to continue."
PACKAGE=wine
VERSION=10.6.arm64ec
RELEASE=3
TARGET="${PACKAGE}-${VERSION}-${RELEASE}"
SCRIPT_DIR="${PWD}/${TARGET}"
mkdir -p $SCRIPT_DIR

set -eouv
#-----------------------------------#
#   Wine ARM64EC RPM build script   #
#-----------------------------------#


#   Create temporary nested script to run inside docker   #
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

cp "${BUILD_DIR}/SPECS/${PACKAGE}.spec" "${BUILD_DIR}/SPECS/${TARGET}.spec"
mv -f "/host/${TARGET}-spec.patch" "${BUILD_DIR}"
patch "${BUILD_DIR}/SPECS/${TARGET}.spec" "${BUILD_DIR}/${TARGET}-spec.patch"

# Wine core source prep
cd "${BUILD_DIR}/SOURCES"
curl -L https://github.com/bylaws/wine/archive/refs/heads/upstream-arm64ec.tar.gz | tar --transform="s/^wine-upstream-arm64ec/${PACKAGE}-${VERSION}/" -xzf -
tar -czvf upstream-arm64ec.tar.gz "${PACKAGE}-${VERSION}"
rm -rf "${PACKAGE}-${VERSION}"

# Wine staging patches prep
# tar -xvf wine-staging-*.tar.gz
# rm wine-staging-*.tar.gz
# mv wine-staging-* "wine-staging-${VERSION}"
# tar -czvf "wine-staging-${VERSION}.tar.gz" "wine-staging-${VERSION}"
# rm -r "wine-staging-${VERSION}"
cd "${BUILD_DIR}"

wget -v -c -nc https://github.com/bylaws/llvm-mingw/releases/download/20240929/llvm-mingw-20240929-ucrt-aarch64.zip
unzip -n llvm-mingw-20240929-ucrt-aarch64.zip
export PATH="${BUILD_DIR}/llvm-mingw-20240929-ucrt-aarch64/bin:$PATH"
dnf builddep --define "VERSION $VERSION" --define "PACKAGE $PACKAGE" --define "RELEASE $RELEASE" -y "${BUILD_DIR}/SPECS/${TARGET}.spec" --allowerasing

rpmbuild --nodebuginfo --define "VERSION $VERSION" --define "PACKAGE $PACKAGE" --define "RELEASE $RELEASE" -ba "${BUILD_DIR}/SPECS/${TARGET}.spec"
cp -r ${BUILD_DIR}/RPMS/aarch64/* /out/
cp -r ${BUILD_DIR}/RPMS/noarch/* /out/
exit
EOF
chmod +x "$TMP_SCRIPT"

# Create wine RPM spec patch to build ARM64EC
cat > "${TARGET}-spec.patch" <<'EOF'
--- SPECS/wine.spec	2025-04-01 08:00:00.000000000 +0800
+++ SPECS/wine-arm64ec.spec	2025-05-03 20:05:20.587428329 +0800
@@ -29 +29 @@
-%global wine_staging 1
+%global wine_staging 0
@@ -33,3 +33,3 @@
-Name:           wine
-Version:        10.4
-Release:        2%{?dist}
+Name:           %{PACKAGE}
+Version:        %{VERSION}
+Release:        %{RELEASE}%{?dist}
@@ -40,2 +40,2 @@
-Source0:        https://dl.winehq.org/wine/source/10.x/wine-%{version}.tar.xz
-Source10:       https://dl.winehq.org/wine/source/10.x/wine-%{version}.tar.xz.sign
+Source0:        https://github.com/bylaws/wine/archive/refs/heads/upstream-arm64ec.tar.gz
+
@@ -87 +87 @@
-ExclusiveArch:  %{ix86} x86_64
+ExclusiveArch:  %{ix86} x86_64 aarch64
@@ -91,0 +92,7 @@
+BuildRequires:  llvm-devel
+BuildRequires:  gcc
+BuildRequires:  libnetapi-devel
+BuildRequires:  libxkbcommon-devel
+BuildRequires:  wayland-devel
+BuildRequires:  ffmpeg-free-devel
+
@@ -97,2 +103,0 @@
-%else
-BuildRequires:  gcc
@@ -166 +171 @@
-%ifarch %{ix86} x86_64
+%ifarch %{ix86} x86_64 aarch64
@@ -661 +666 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -682,0 +688,4 @@
+%ifarch aarch64
+unset toolchain
+export CC=gcc CXX=g++
+%endif
@@ -698 +707 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -720 +729 @@
- --enable-win64 \
+ --enable-win64 --enable-archs=arm64ec,aarch64,i386,arm --with-mingw=clang --with-wayland \
@@ -766 +775 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -1065,0 +1075,3 @@
+%{_libdir}/wine/%{winepedir}/xtajit64.dll
+%{_libdir}/wine/arm-windows/*
+
@@ -1091 +1102 @@
-%ifarch %{ix86} x86_64
+%ifarch %{ix86} x86_64 aarch64
@@ -1650 +1661 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -1684 +1694,0 @@
-%if 0%{?wine_staging}
@@ -1686 +1695,0 @@
-%endif
@@ -1716 +1724,0 @@
-%if 0%{?wine_staging}
@@ -1719 +1726,0 @@
-%endif
@@ -2107 +2114 @@
-%ifarch %{ix86} x86_64
+%ifarch %{ix86} x86_64 aarch64
@@ -2132 +2139 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -2430 +2436,0 @@
-
EOF

#   Create registry files for Wine to use ARM64EC and Wayland   #
cat > "wayland.reg" <<'EOF'
Windows Registry Editor Version 5.00
[HKEY_CURRENT_USER\Software\Wine\Drivers]
"Graphics"="x11,wayland"
EOF

cat > "fex-override.reg" <<'EOF'
Windows Registry Editor Version 5.00
[HKEY_LOCAL_MACHINE\Software\Microsoft\Wow64\amd64]
@="libarm64ecfex.dll"
EOF

#   Create setup script for installing the Wine ARM64EC build, installing the FEX DLLs, and importing the registry entries.   #
cat > "setup-wine.sh" <<'EOF'
sudo dnf install ./*.rpm --skip-unavailable
sudo cp -v libarm64ecfex.dll /usr/lib64/wine/aarch64-windows/libarm64ecfex.dll
sudo cp -v libwow64fex.dll /usr/lib64/wine/aarch64-windows/libwow64fex.dll
wine reg import fex-override.reg
wine reg import wayland.reg
EOF

#   Starting docker   #
docker run -e PACKAGE=${PACKAGE} -e VERSION=${VERSION} -e RELEASE=${RELEASE} -e TARGET=${TARGET} -it --rm -v "$PWD:/out:z" -v "$PWD:/host:z" fedora:42 ./host/$TMP_SCRIPT

#   Exiting to host   #
rm "$TMP_SCRIPT"
cd ..

sudo dnf install ar wget

#   Downloading and extracting FEX arm64ec dlls   #
cd "${SCRIPT_DIR}"
wget -v -c -nc https://launchpad.net/~fex-emu/+archive/ubuntu/fex/+build/30613070/+files/fex-emu-wine_2504~j_arm64.deb
ar xv "${SCRIPT_DIR}/fex-emu-wine_2504~j_arm64.deb"
tar -xvf "${SCRIPT_DIR}/data.tar.zst"
cp -v "${SCRIPT_DIR}/usr/lib/wine/aarch64-windows/libarm64ecfex.dll" "${SCRIPT_DIR}/libarm64ecfex.dll"
cp -v "${SCRIPT_DIR}/usr/lib/wine/aarch64-windows/libwow64fex.dll" "${SCRIPT_DIR}/libwow64fex.dll"
rm "${SCRIPT_DIR}/fex-emu-wine_2504~j_arm64.deb"
rm "${SCRIPT_DIR}/debian-binary"
rm "${SCRIPT_DIR}/data.tar.zst"
rm "${SCRIPT_DIR}/control.tar.zst"
rm -r "${SCRIPT_DIR}/usr"


#   Execute setup script   #
chmod +x setup-wine.sh
./setup-wine.sh

#   Done!   #
