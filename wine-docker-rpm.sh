#!/usr/bin/sh
read -p "Wine ARM64EC Docker build script. Fedora 42 required. Press enter to continue."
PACKAGE=wine
VERSION=10.6.arm64ec
RELEASE=4
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
dnf builddep --define "VERSION $VERSION" --define "PACKAGE $PACKAGE" --define "RELEASE $RELEASE" -y "${BUILD_DIR}/SPECS/${TARGET}.spec" --allowerasing

spectool -g -R "${BUILD_DIR}/SPECS/${TARGET}.spec"
rpmbuild --nodebuginfo --define "VERSION $VERSION" --define "PACKAGE $PACKAGE" --define "RELEASE $RELEASE" -ba "${BUILD_DIR}/SPECS/${TARGET}.spec"
cp -r ${BUILD_DIR}/RPMS/aarch64/* /out/
cp -r ${BUILD_DIR}/RPMS/noarch/* /out/
exit
EOF
chmod +x "$TMP_SCRIPT"

# Create wine RPM spec patch to build ARM64EC
cat > "${TARGET}-spec.patch" <<'EOF'
--- SPECS/wine.spec	2025-04-01 08:00:00.000000000 +0800
+++ SPECS/wine-arm64ec.spec	2025-05-12 03:54:23.763128130 +0800
@@ -24,0 +25 @@
+%global arm64ec 1
@@ -29 +30 @@
-%global wine_staging 1
+%global wine_staging 0
@@ -34,2 +35,2 @@
-Version:        10.4
-Release:        2%{?dist}
+Version:        10.6.arm64ec
+Release:        4%{?dist}
@@ -39,0 +41,5 @@
+
+%if %{?arm64ec}
+Source0:        https://github.com/bylaws/wine/archive/refs/heads/upstream-arm64ec.tar.gz
+Source10:       https://dl.winehq.org/wine/source/10.x/wine-10.6.tar.xz.sign
+%else
@@ -41,0 +48,2 @@
+%endif
+
@@ -77,0 +86,5 @@
+%if %{?arm64ec}
+#mingw LLVM fork for building arm64ec
+Source800: https://github.com/bylaws/llvm-mingw/releases/download/20250305/llvm-mingw-20250305-ucrt-ubuntu-20.04-aarch64.tar.xz
+%endif
+
@@ -87 +101 @@
-ExclusiveArch:  %{ix86} x86_64
+ExclusiveArch:  %{ix86} x86_64 aarch64
@@ -91,0 +106,9 @@
+%if %{?arm64ec}
+BuildRequires:  llvm-devel
+BuildRequires:  gcc
+BuildRequires:  libnetapi-devel
+BuildRequires:  libxkbcommon-devel
+BuildRequires:  wayland-devel
+BuildRequires:  ffmpeg-free-devel
+%endif
+
@@ -97,2 +119,0 @@
-%else
-BuildRequires:  gcc
@@ -166 +187 @@
-%ifarch %{ix86} x86_64
+%ifarch %{ix86} x86_64 aarch64
@@ -661 +682 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -669,0 +691,3 @@
+%if %{?arm64ec}
+%setup -qn wine-upstream-arm64ec
+%else
@@ -670,0 +695 @@
+%endif
@@ -672 +697,3 @@
-
+%if %{?arm64ec}
+tar -xJf %{SOURCE800} -C %{_builddir}
+%endif
@@ -682,0 +710,6 @@
+%if %{?arm64ec}
+unset toolchain
+export CC=gcc CXX=g++
+export PATH="%{_builddir}/llvm-mingw-20250305-ucrt-ubuntu-20.04-aarch64/bin:$PATH"
+
+%endif
@@ -724,0 +759,5 @@
+%if %{?arm64ec}
+ --enable-archs=arm64ec,aarch64,i386 \
+ --with-mingw=clang \
+ --with-wayland \
+%endif
@@ -766 +805 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -1065,0 +1105,4 @@
+%if %{?arm64ec}
+%{_libdir}/wine/%{winepedir}/xtajit64.dll
+%endif
+
@@ -1091 +1134 @@
-%ifarch %{ix86} x86_64
+%ifarch %{ix86} x86_64 aarch64
@@ -1650 +1693 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -1684 +1726,0 @@
-%if 0%{?wine_staging}
@@ -1686 +1727,0 @@
-%endif
@@ -1716 +1756,0 @@
-%if 0%{?wine_staging}
@@ -1719 +1758,0 @@
-%endif
@@ -2107 +2146 @@
-%ifarch %{ix86} x86_64
+%ifarch %{ix86} x86_64 aarch64
@@ -2132 +2171 @@
-%ifarch x86_64
+%ifarch x86_64 aarch64
@@ -2138,0 +2178,3 @@
+* Sat May 10 2025 Lachlan Marie <lchlnm@pm.me> - 10.6.arm64ec-4
+- Added conditional variables to adjust build process based on aarch64 architecture
+
@@ -2430 +2471,0 @@
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
