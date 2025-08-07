%global srcname FEX
%global forgeurl https://github.com/FEX-Emu/FEX
%undefine _hardened_build
%undefine _auto_set_build_flags

%global fex_ldflags -Wl,--gc-sections -static
%global fex_cflags -O3 -g -pipe -Wall -Wextra

Name:       fex-emu-wine
Version:    2505
Release:    1%{?dist}
Summary:    FEX DLLs for enabling Wine's ARM64EC support

# FEX itself is MIT, see below for the bundled libraries
%global fex_license MIT AND Apache-2.0 AND BSD-3-Clause AND GPL-2.0-only
License:    %{fex_license}
URL:        https://fex-emu.com
%if %{defined commit}
Source0:    %{forgeurl}/commit/%{commit}/%{srcname}-%{commit}.tar.gz
%else
Source0:    %{forgeurl}/archive/%{srcname}-%{version}/%{srcname}-%{srcname}-%{version}.tar.gz
%endif

Source100:  https://github.com/bylaws/llvm-mingw/releases/download/20250305/llvm-mingw-20250305-ucrt-ubuntu-20.04-aarch64.tar.xz

# Bundled dependencies managed as git submodules upstream
# These are too entangled with the build system to unbundle for now
# https://github.com/FEX-Emu/FEX/issues/2996
# https://github.com/FEX-Emu/FEX/issues/4267
%{lua:
local externals = {
  { name="cpp-optparse", ref="9f94388", owner="Sonicadvance1", path="../Source/Common/cpp-optparse", license="MIT" },
  { name="drm-headers", ref="0675d2f", owner="FEX-Emu", package="kernel", version="6.13", license="GPL-2.0-only" },
  { name="jemalloc", ref="02ca52b", owner="FEX-Emu", version="5.3.0", license="MIT" },
  { name="jemalloc", ref="4043539", owner="FEX-Emu", path="jemalloc_glibc", version="5.3.0", license="MIT" },
  { name="robin-map", ref="d5683d9", owner="FEX-Emu", version="1.3.0", license="MIT" },
  { name="Vulkan-Headers", ref="cacef30", owner="KhronosGroup", package="vulkan-headers", version="1.4.310", license="Apache-2.0" },
  { name="xxhash", ref="bbb27a5", owner="Cyan4973", path="xxhash", version="0.8.2",  license="BSD-2-Clause" },
  { name="fmt", ref="1239137", owner="fmtlib", path="fmt" },
}

for i, s in ipairs(externals) do
  si = 100 + i
  print(string.format("Source%d: https://github.com/%s/%s/archive/%s/%s-%s.tar.gz", si, s.owner, s.name, s.ref, s.name, s.ref).."\n")
  if s.bcond and not rpm.isdefined(string.format("with_%s", s.bcond)) then goto continue1 end
  print(string.format("Provides: bundled(%s) = %s", (s.package or s.name), (s.version or "0")).."\n")
  ::continue1::
end

function print_setup_externals()
  for i, s in ipairs(externals) do
    si = 100 + i
    if s.bcond and not rpm.isdefined(string.format("with_%s", s.bcond)) then goto continue2 end
    print(string.format("mkdir -p External/%s", (s.path or s.name)).."\n")
    print(string.format("tar -xzf %s --strip-components=1 -C External/%s", rpm.expand("%{SOURCE"..si.."}"), (s.path or s.name)).."\n")
    ::continue2::
  end
end
}

# LinuxEmulation: Implement custom longjump that is fortification safe
Patch:          %{forgeurl}/commit/a37def2c22e528477f64296747228400ddc40222.patch
# Async: Add run_one interface to enable more fine-grained event loop control
Patch:          %{forgeurl}/commit/8eaf45414c05c9e7ef6f74a323d95fe7e0d883c1.patch
# FEXServer: Don't time out while clients are still connected
Patch:          %{forgeurl}/commit/c326e2d669fd5e9356f6107e188413a449cc1fd7.patch


BuildRequires:  cmake
BuildRequires:  clang
BuildRequires:  git-core
BuildRequires:  lld
BuildRequires:  llvm
BuildRequires:  llvm-devel
BuildRequires:  ninja-build
BuildRequires:  python3
%ifarch %{arm64}
BuildRequires:  python3-setuptools
%endif
BuildRequires:  sed
BuildRequires:  systemd-rpm-macros
%if %{with check}
BuildRequires:  nasm
BuildRequires:  python3-clang
%endif

BuildRequires:  catch2-devel
BuildRequires:  fmt-devel
BuildRequires:  libepoxy-devel
BuildRequires:  SDL2-devel
BuildRequires:  xxhash-devel
%ifarch %{x86_64}
BuildRequires:  xbyak-devel
%endif
BuildRequires:  alsa-lib-devel
BuildRequires:  clang-devel
BuildRequires:  libdrm-devel
BuildRequires:  libglvnd-devel
BuildRequires:  libX11-devel
BuildRequires:  libXrandr-devel
BuildRequires:  llvm-devel
BuildRequires:  openssl-devel
BuildRequires:  wayland-devel
BuildRequires:  zlib-devel

Requires:       systemd-udev


%description
FEX allows you to run x86 and x86-64 binaries on an AArch64 host, similar to
qemu-user and box86. It has native support for a rootfs overlay, so you don't
need to chroot, as well as some thunklibs so it can forward things like GL to
the host. FEX presents a Linux 5.0+ interface to the guest, and supports only
AArch64 as a host. FEX is very much work in progress, so expect things to
change.


%prep
%if %{defined commit}
%setup -q -n %{srcname}-%{commit}
%else
%setup -q -n %{srcname}-%{srcname}-%{version}
%endif

# Unpack bundled libraries
%{lua: print_setup_externals()}



tar -xJf %{SOURCE100} -C %{_builddir}


%build
export CFLAGS="%{fex_cflags}"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="%{fex_ldflags}"
export PATH="%{_builddir}/llvm-mingw-20250305-ucrt-ubuntu-20.04-aarch64/bin:$PATH"

# 4. Build arm64ec thunk set
mkdir build-arm64ec && pushd build-arm64ec

cmake -DCMAKE_C_FLAGS="$CFLAGS" -DCMAKE_CXX_FLAGS="$CFLAGS" \
  -GNinja \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DCMAKE_INSTALL_LIBDIR=%{_libdir}/wine/aarch64-windows \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE=../toolchain_mingw.cmake \
  -DENABLE_LTO=False \
  -DMINGW_TRIPLE=arm64ec-w64-mingw32 \
  -DBUILD_TESTS=False \
  -DENABLE_JEMALLOC_GLIBC_ALLOC=False \
  ..
sed -i 's/arm64ec-w64-mingw32-dlltool/llvm-dlltool -m arm64ec/g' build.ninja
ninja
popd

# 5. Build wow64 thunk set (arm64 host / x86 guest)
mkdir build-wow64 && pushd build-wow64
cmake -DCMAKE_C_FLAGS="$CFLAGS" -DCMAKE_CXX_FLAGS="$CFLAGS" \
  -GNinja \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DCMAKE_INSTALL_LIBDIR=%{_libdir}/wine/aarch64-windows \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE=../toolchain_mingw.cmake \
  -DENABLE_LTO=False \
  -DMINGW_TRIPLE=aarch64-w64-mingw32 \
  -DBUILD_TESTS=False \
  -DENABLE_JEMALLOC_GLIBC_ALLOC=OFF \
  ..
sed -i 's/aarch64-w64-mingw32-dlltool/llvm-dlltool -m arm64/g' build.ninja
ninja
popd

######################################################################
# %install – place files under the staging tree and make them clean
######################################################################
%install
rm -rf %{buildroot}

pushd build-arm64ec
DESTDIR=%{buildroot} ninja install
popd

pushd build-wow64
DESTDIR=%{buildroot} ninja install
popd

rm -rf %{buildroot}/usr/include
rm -rf %{buildroot}/usr/share

%files
%define debug_package %{nil}
%license LICENSE
%doc Readme.md docs

# main runtime bits
%{_libdir}/wine/aarch64-windows/libarm64ecfex.dll
%{_libdir}/wine/aarch64-windows/libwow64fex.dll


%changelog
%autochangelog
