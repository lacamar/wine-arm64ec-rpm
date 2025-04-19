#!/usr/bin/sh
read -p "Wine ARM64EC Docker build script. Fedora 42 required. Press enter to continue."
VERSION=arm64ec
set -eouv
#-------------------------------------------------#
#   Wine ARM64EC WoW64 Staging RPM build script   #
#-------------------------------------------------#

#   Create temporary nested script to run inside docker   #
SCRIPT_DIR="${PWD}/wine-${VERSION}"
mkdir -p $SCRIPT_DIR
cd $SCRIPT_DIR
TMP_SCRIPT=docker-wine-builder.sh
touch $TMP_SCRIPT
rm $TMP_SCRIPT
touch $TMP_SCRIPT
cat > "$TMP_SCRIPT" <<'EOF'
#!/bin/bash
set -euov pipefail
WINE_RPM_BUILD_DIR="/root/rpmbuild"
VERSION=arm64ec
dnf install rpm-build rpmdevtools gcc make git wget ar llvm-devel clang mingw64-gcc mingw32-gcc lld-link libnetapi-devel libxkbcommon-devel wayland-devel ffmpeg-free-devel -y
rpmdev-setuptree
cd "${WINE_RPM_BUILD_DIR}"
dnf download --source wine
rpm -ivh wine-*.src.rpm
touch "${WINE_RPM_BUILD_DIR}/SPECS/wine-${VERSION}.spec"
rm "${WINE_RPM_BUILD_DIR}/SPECS/wine-${VERSION}.spec"
cp "${WINE_RPM_BUILD_DIR}/SPECS/wine.spec" "${WINE_RPM_BUILD_DIR}/SPECS/wine-${VERSION}.spec"
sed -i -e "34s/.*/Version:        ${VERSION}/" -e\
    '81s/.*/Source900: v10.5.tar.gz/' -e\
    '41s/.*/ /' -e\
    's/%global wine_staging 1/%global wine_staging 0/g' -e\
    '87 s/$/ aarch64/' -e\
    '89 s/$/ aarch64/' -e\
    '719a --enable-archs=arm64ec,aarch64,i386 --with-mingw=clang --with-wayland \\' -e\
    '1065a\
    %{_libdir}/wine/%{winepedir}/dpnsvr.exe \
    %{_libdir}/wine/%{winepedir}/vcruntime140_1.dll \
    %{_libdir}/wine/%{winepedir}/xtajit64.dll \
    %{_libdir}/wine/i386-windows/* \
    %{_libdir}/wine/%{winesodir}/winewayland.so \
    %{_libdir}/wine/%{winepedir}/windows.networking.connectivity.dll \
    %{_libdir}/wine/%{winepedir}/winewayland.drv \
    %{_libdir}/wine/i386-windows/*' \
    "${WINE_RPM_BUILD_DIR}/SPECS/wine-${VERSION}.spec"
cd "${WINE_RPM_BUILD_DIR}/SOURCES"
wget -v -c -nc https://github.com/bylaws/wine/archive/refs/heads/upstream-arm64ec.zip
unzip -n upstream-arm64ec.zip
mv wine-upstream-arm64ec wine-${VERSION}
tar -cJf wine-${VERSION}.tar.xz wine-${VERSION}
rm -rf wine-${VERSION}
rm -rf upstream-arm64ec.zip
# Unused sources for Wine 10.5.
# wget -v -c -nc https://dl.winehq.org/wine/source/10.x/wine-${VERSION}.tar.xz
# wget -v -c -nc https://dl.winehq.org/wine/source/10.x/wine-${VERSION}.tar.xz.sign
# wget -v -c -nc https://github.com/wine-staging/wine-staging/archive/refs/tags/v${VERSION}.tar.gz
cd "${WINE_RPM_BUILD_DIR}"
wget -v -c -nc https://github.com/bylaws/llvm-mingw/releases/download/20240929/llvm-mingw-20240929-ucrt-aarch64.zip
unzip -n llvm-mingw-20240929-ucrt-aarch64.zip
export PATH="${WINE_RPM_BUILD_DIR}/llvm-mingw-20240929-ucrt-aarch64/bin:$PATH"
dnf builddep -y "${WINE_RPM_BUILD_DIR}/SPECS/wine-${VERSION}.spec" --allowerasing
rpmbuild -ba "${WINE_RPM_BUILD_DIR}/SPECS/wine-${VERSION}.spec"
cp -r /root/rpmbuild/RPMS/aarch64/* /out/
cp -r /root/rpmbuild/RPMS/noarch/* /out/
exit
EOF
chmod +x "$TMP_SCRIPT"

#   Installing host dependencies   #
sudo dnf install docker-ce ar wget tar

#   Starting docker   #
sudo systemctl start docker.service
docker pull fedora:42
docker run -it --rm -v "$PWD:/out" -v "$PWD:/host" fedora:42 ./host/$TMP_SCRIPT
rm "$TMP_SCRIPT"
cd ..

#   Install the Wine ARM64EC packages that were built   #
sudo dnf install $SCRIPT_DIR/* --skip-unavailable

#   Downloading FEX arm64ec dlls   #
cd "${SCRIPT_DIR}"
wget -v -c -nc https://launchpad.net/~fex-emu/+archive/ubuntu/fex/+build/30613070/+files/fex-emu-wine_2504~j_arm64.deb

#   Extract FEX dll package   #
ar xv "${SCRIPT_DIR}/fex-emu-wine_2504~j_arm64.deb"
tar -xvf "${SCRIPT_DIR}/data.tar.zst"
rm "${SCRIPT_DIR}/fex-emu-wine_2504~j_arm64.deb"
rm "${SCRIPT_DIR}/debian-binary"
rm "${SCRIPT_DIR}/data.tar.zst"
rm "${SCRIPT_DIR}/control.tar.zst"

#   Move to install location in wine system libraries   #
sudo cp -v "${SCRIPT_DIR}/usr/lib/wine/aarch64-windows/libarm64ecfex.dll" /usr/lib64/wine/aarch64-windows/libarm64ecfex.dll
sudo cp -v "${SCRIPT_DIR}/usr/lib/wine/aarch64-windows/libwow64fex.dll" /usr/lib64/wine/aarch64-windows/libwow64fex.dll

#   Edit registry file in wine to use ARM64EC and Wayland   #
cat > "wayland.reg" <<'EOF'
Windows Registry Editor Version 5.00
[HKEY_CURRENT_USER\Software\Wine\Drivers]
"Graphics"="x11,wayland"
EOF
wine reg add "HKLM\Software\Microsoft\Wow64\amd64" /ve /d "libarm64ecfex.dll" /f
wine reg import wayland.reg

#   Done!   #
