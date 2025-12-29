%global srcname FEX

%global bumpver 13

%global commit b87bb1dec615e42d77bbd4e03f58efd86bedbee0
%{?commit:%global shortcommit %(c=%{commit}; echo ${c:0:7})}

%global forgeurl https://github.com/FEX-Emu/FEX
%undefine _hardened_build
%undefine _auto_set_build_flags

%global fex_ldflags -Wl,--gc-sections -static
%global fex_cflags -O3 -g -pipe -Wall -Wextra

Name:       fex-emu-wine-git
Version:    2512%{?bumpver:^%{bumpver}.git.%{shortcommit}}
Release:    1%{dist}
Summary:    FEX DLLs for enabling Wine's ARM64EC support

# FEX itself is MIT, see below for the bundled libraries
%global fex_license MIT AND Apache-2.0 AND BSD-3-Clause AND GPL-2.0-only
License:    %{fex_license}
URL:        https://fex-emu.com
Source0:    https://github.com/FEX-Emu/FEX/archive/%{commit}/FEX-%{shortcommit}.tar.gz

Source100:  https://github.com/bylaws/llvm-mingw/releases/download/20250920/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64.tar.xz

%{lua:
local externals = {
  { name="Catch2", ref="b3fb4b9", owner="catchorg", version="3.11.0", license="BSL-1.0" },
  { name="cpp-optparse", ref="9f94388", owner="Sonicadvance1", path="../Source/Common/cpp-optparse", license="MIT" },
  { name="Vulkan-Headers", ref="cacef30", owner="KhronosGroup", package="vulkan-headers", version="1.4.310", license="Apache-2.0" },
  { name="drm-headers", ref="3e49836", owner="FEX-Emu", package="kernel", version="6.13", license="GPL-2.0-only" },
  { name="fmt", ref="407c905", owner="fmtlib", path="fmt", version="12.1.0" },
  { name="jemalloc", ref="97d9869", owner="FEX-Emu", version="5.3.0", license="MIT" },
  { name="jemalloc", ref="8436195", owner="FEX-Emu", path="jemalloc_glibc", version="5.3.0", license="MIT" },
  { name="rpmalloc", ref="f1b76e1", owner="FEX-Emu", license="MIT" },
  { name="range-v3", ref="ca1388f", owner="ericniebler", license="MIT" },
  { name="robin-map", ref="d5683d9", owner="FEX-Emu", version="1.3.0", license="Boost-v1" },
  { name="tracy", ref="650c98e", owner="wolfpld", license="BSD-2-Clause" },
  { name="vixl", ref="ed690c9", owner="FEX-Emu", license="BSD-3-Clause" },
  { name="xxhash", ref="e626a72", owner="Cyan4973", path="xxhash", version="0.8.3",  license="BSD-2-Clause" },
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
BuildRequires:  openssl-devel
BuildRequires:  wayland-devel
BuildRequires:  zlib-devel

Requires:       systemd-udev

Conflicts:      fex-emu-wine
Provides:       fex-emu-wine


%description
FEX-Emu DLLs that allow for ARM64EC support on aarch64 hosts running wine.


%prep
%setup -q -n %{srcname}-%{commit}

# Unpack bundled libraries
%{lua: print_setup_externals()}



tar -xJf %{SOURCE100} -C %{_builddir}


%build
export CFLAGS="%{fex_cflags}"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="%{fex_ldflags}"
export PATH="%{_builddir}/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64/bin:$PATH"

mkdir build-arm64ec && pushd build-arm64ec

cmake -DCMAKE_C_FLAGS="$CFLAGS" -DCMAKE_CXX_FLAGS="$CFLAGS" \
  -GNinja \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DCMAKE_INSTALL_LIBDIR=%{_libdir}/wine/aarch64-windows \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE=../Data/CMake/toolchain_mingw.cmake \
  -DENABLE_LTO=False \
  -DTUNE_CPU=none \
  -DMINGW_TRIPLE=arm64ec-w64-mingw32 \
  -DBUILD_TESTING=False \
  -DENABLE_JEMALLOC_GLIBC_ALLOC=False \
  ..
sed -i 's/arm64ec-w64-mingw32-dlltool/llvm-dlltool -m arm64ec/g' build.ninja
ninja
popd

mkdir build-wow64 && pushd build-wow64
cmake -DCMAKE_C_FLAGS="$CFLAGS" -DCMAKE_CXX_FLAGS="$CFLAGS" \
  -GNinja \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DCMAKE_INSTALL_LIBDIR=%{_libdir}/wine/aarch64-windows \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE=../Data/CMake/toolchain_mingw.cmake \
  -DENABLE_LTO=False \
  -DTUNE_CPU=none \
  -DMINGW_TRIPLE=aarch64-w64-mingw32 \
  -DBUILD_TESTING=False \
  -DENABLE_JEMALLOC_GLIBC_ALLOC=OFF \
  ..
sed -i 's/aarch64-w64-mingw32-dlltool/llvm-dlltool -m arm64/g' build.ninja
ninja
popd

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

%{_libdir}/wine/aarch64-windows/libarm64ecfex.dll
%{_libdir}/wine/aarch64-windows/libwow64fex.dll


%changelog
* Tue Dec 30 2025 Lachlan Marie <lchlnm@pm.me> - 2512^13.git.b87bb1d-1
 - Update to commit b87bb1dec615e42d77bbd4e03f58efd86bedbee0

* Mon Dec 29 2025 Lachlan Marie <lchlnm@pm.me> - 2512^12.git.9101e70-1
 - Update to commit 9101e704ce5c343968ba1da57085053a26159770

* Sun Dec 28 2025 Lachlan Marie <lchlnm@pm.me> - 2512^11.git.668e027-1
 - Update to commit 668e0275c39212e7f99af0ef2a64914624b332d8

* Sun Dec 28 2025 Lachlan Marie <lchlnm@pm.me> - 2512^10.git.ce9824a-1
 - Update to commit ce9824a4796a0ff25c022b3d625d37efe6f327f2

* Thu Dec 25 2025 Lachlan Marie <lchlnm@pm.me> - 2512^9.git.b41b967-1
 - Update to commit b41b967ba5892dae6a05dd8acc11bd40f7f3bf58

* Wed Dec 24 2025 Lachlan Marie <lchlnm@pm.me> - 2512^8.git.974ba78-1
 - Update to commit 974ba78a93b80c6258b858c38f23592cf0cc4ee7

* Tue Dec 16 2025 Lachlan Marie <lchlnm@pm.me> - 2512^7.git.d197300-1
 - Update to commit d197300be78c50a8aaacf701922a3d3811c6f0fa

* Tue Dec 16 2025 Lachlan Marie <lchlnm@pm.me> - 2512^6.git.9e8915e-1
 - Update to commit 9e8915ef9ebd7ed8e5b32c39663e4b4d44d06ecb

* Thu Dec 11 2025 Lachlan Marie <lchlnm@pm.me> - 2512^5.git.bf9ab7f-1
 - Update to commit bf9ab7ffbee9bc14f21741fe265d99f4df9a2680

* Wed Dec 10 2025 Lachlan Marie <lchlnm@pm.me> - 2512^4.git.53925dc-1
 - Update to commit 53925dcc3dc0640ac73bcb822811a416a9780f57

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2512^3.git.e859109-1
 - Update to commit e8591090f246c49631c14ef70f32c7df14b5646e

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2512^2.git.2e2563a-1
 - Update to commit 2e2563adc08b5fbf73da22e98cd6498fb567b33b

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2512^1.git.ba1b474-1
 - Update to commit ba1b4744c52c6793cd7506a0bcf66719698fee60

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2512^31.git.ba1b474-1
 - Update to commit ba1b4744c52c6793cd7506a0bcf66719698fee60

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2511^30.git.bd13c02-1
 - Update to commit bd13c024517d738ab1e34b120cc71041f85df618

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2511^29.git.d0e47f9-1
 - Update to commit d0e47f9073744b7cc3d47dbe75513def5ffdd899

* Sat Dec 06 2025 Lachlan Marie <lchlnm@pm.me> - 2511^28.git.c460cf0-1
 - Update to commit c460cf06786315a20aec35fd1286acb7c39e5f51

* Fri Dec 05 2025 Lachlan Marie <lchlnm@pm.me> - 2511^27.git.8bb3398-1
 - Update to commit 8bb33983763c31567b09e650c27a79b99eeaae2e

* Wed Dec 03 2025 Lachlan Marie <lchlnm@pm.me> - 2511^26.git.90c8fcf-1
 - Update to commit 90c8fcf39375fa15c64ebc48f60dd11b8d0d5fa3

* Tue Dec 02 2025 Lachlan Marie <lchlnm@pm.me> - 2511^25.git.e4fa399-1
 - Update to commit e4fa399412dda26ebc07d0371fb6c535da2b1e72

* Tue Dec 02 2025 Lachlan Marie <lchlnm@pm.me> - 2511^24.git.3dd591e-1
 - Update to commit 3dd591e7608f2c2bd5dcf6c144441f1f8675449b

* Sat Nov 29 2025 Lachlan Marie <lchlnm@pm.me> - 2511^23.git.39fb266-1
 - Update to commit 39fb266282dae3cf8c5b18a53ca7424e0458d7b9

* Sat Nov 29 2025 Lachlan Marie <lchlnm@pm.me> - 2511^22.git.3969d0a-1
 - Update to commit 3969d0ac7895241b3340dd0952d2db1d0c8c3684

* Fri Nov 28 2025 Lachlan Marie <lchlnm@pm.me> - 2511^21.git.427b235-1
 - Update to commit 427b235eb5a5edf1f962ab1f520e1896de3619b7

* Fri Nov 28 2025 Lachlan Marie <lchlnm@pm.me> - 2511^20.git.92d5ba5-1
 - Update to commit 92d5ba580fead1610b3e5eb1659d30bae894fe42

* Fri Nov 28 2025 Lachlan Marie <lchlnm@pm.me> - 2511^19.git.57e23b2-1
 - Update to commit 57e23b289a0ae3e1a212bf8ff6b59b5b9c33750c

* Thu Nov 27 2025 Lachlan Marie <lchlnm@pm.me> - 2511^18.git.a27c4b3-1
 - Update to commit a27c4b38606c1c0ca5c7a460c31344a9667ec386

* Tue Nov 25 2025 Lachlan Marie <lchlnm@pm.me> - 2511^17.git.a251e61-1
 - Update to commit a251e618599ec49d45e8a8ff8e4e7e941bfcf89e

* Tue Nov 25 2025 Lachlan Marie <lchlnm@pm.me> - 2511^16.git.6fd471e-1
 - Update to commit 6fd471e652c1b927c7daa32865070446bf883cde

* Mon Nov 24 2025 Lachlan Marie <lchlnm@pm.me> - 2511^15.git.3d69029-1
 - Update to commit 3d69029d335c24bb0548363664d8e3e74e090c03

* Sat Nov 22 2025 Lachlan Marie <lchlnm@pm.me> - 2511^14.git.e2f4065-1
 - Update to commit e2f406537690a0b258fcdde289594dc2be93382d
