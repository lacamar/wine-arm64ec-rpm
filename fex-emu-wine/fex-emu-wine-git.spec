%global srcname FEX
%global tag 2605

%global bumpver 37

%global commit 7ae55d73c1cc0fa0c0bf984ec4d43e9a5ae32efc
%{?commit:%global shortcommit %(c=%{commit}; echo ${c:0:7})}

%global forgeurl https://github.com/FEX-Emu/FEX
%undefine _hardened_build
%undefine _auto_set_build_flags

%global fex_ldflags -Wl,--gc-sections -static
%global fex_cflags -O3 -g -pipe -Wall -Wextra

Name:       fex-emu-wine-git
Version:    %{tag}%{?bumpver:^%{bumpver}.git.%{shortcommit}}
Release:    3%{?dist}
Summary:    FEX DLLs for enabling Wine's ARM64EC support

# FEX itself is MIT, see below for the bundled libraries
%global fex_license MIT AND Apache-2.0 AND BSD-3-Clause AND GPL-2.0-only
License:    %{fex_license}
URL:        https://fex-emu.com
Source0:    https://github.com/FEX-Emu/FEX/archive/%{commit}/FEX-%{shortcommit}.tar.gz

Source100:  https://github.com/bylaws/llvm-mingw/releases/download/20250920/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64.tar.xz

%{lua:
local externals = {
  { name="cpp-optparse", ref="9f94388", owner="Sonicadvance1", path="../Source/Common/cpp-optparse", license="MIT" },
  { name="Catch2", ref="b3fb4b9", owner="catchorg", version="3.11.0", license="BSL-1.0" },
  { name="Vulkan-Headers", ref="450bd22", owner="KhronosGroup", package="vulkan-headers", version="1.4.337", license="Apache-2.0" },
  { name="drm-headers", ref="3e49836", owner="FEX-Emu", package="kernel", version="6.13", license="GPL-2.0-only" },
  { name="fmt", ref="407c905", owner="fmtlib", path="fmt", version="12.1.0" },
  { name="jemalloc", ref="8436195", owner="FEX-Emu", path="jemalloc_glibc", version="5.3.0", license="MIT" },
  { name="range-v3", ref="ca1388f", owner="ericniebler", license="MIT" },
  { name="rpmalloc", ref="1d85c24", owner="FEX-Emu", license="0BSD" },
  { name="tracy", ref="650c98e", owner="wolfpld", license="BSD-2-Clause" },
  { name="unordered_dense", ref="3234af2", owner="martinus", version="4.8.1", license="MIT" },
  { name="vixl", ref="5f41844", owner="FEX-Emu", license="BSD-3-Clause" },
  { name="xxhash", ref="e626a72", owner="Cyan4973", path="xxhash", version="0.8.3",  license="BSD-2-Clause" },
  { name="zydis", ref="9bfadd6", owner="zyantific", version="4.1.1",  license="MIT" },
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
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
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
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
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
%{_bindir}/FEXOfflineCompiler.exe


%changelog
* Fri Jun 26 2026 Lachlan Marie <lchlnm@pm.me> - 2605^37.git.7ae55d7-3
 - Update to commit 7ae55d73c1cc0fa0c0bf984ec4d43e9a5ae32efc

* Fri Jun 26 2026 Lachlan Marie <lchlnm@pm.me> - 2605^36.git.d5be15c-3
 - Update to commit d5be15c90e8a8f1552cca61a964d8f8411fe73a4

* Fri Jun 26 2026 Lachlan Marie <lchlnm@pm.me> - 2605^35.git.3d66be9-3
 - Update to commit 3d66be9e5ae15403387cf37acd62e240e7722fde

* Thu Jun 25 2026 Lachlan Marie <lchlnm@pm.me> - 2605^34.git.ab4e0f6-3
 - Update to commit ab4e0f653a5859f95087675302709b018d47bd94

* Thu Jun 25 2026 Lachlan Marie <lchlnm@pm.me> - 2605^33.git.ad618be-3
 - Update to commit ad618be979477047a3632111a1fa4cc8077bb850

* Wed Jun 24 2026 Lachlan Marie <lchlnm@pm.me> - 2605^32.git.9f195ff-3
 - Update to commit 9f195ff3771907ae5cea603e93f8104c6a9d62f2

* Wed Jun 24 2026 Lachlan Marie <lchlnm@pm.me> - 2605^31.git.27a5f09-3
 - Update to commit 27a5f09185d3c408a3f565eb6467421635a0cf0a

* Tue Jun 23 2026 Lachlan Marie <lchlnm@pm.me> - 2605^30.git.1619374-3
 - Update to commit 161937425206f32b5e5c6605f682cb49224f9ada

* Tue Jun 23 2026 Lachlan Marie <lchlnm@pm.me> - 2605^29.git.37e32fb-3
 - Update to commit 37e32fbcb96159f826c0ca795bea43a734fd76ff

* Tue Jun 23 2026 Lachlan Marie <lchlnm@pm.me> - 2605^28.git.27acbba-3
 - Update to commit 27acbba52eefb1a293e36044af80bf0b14186534

* Mon Jun 22 2026 Lachlan Marie <lchlnm@pm.me> - 2605^27.git.280568d-3
 - Update to commit 280568df2f5429830b32e456f18610d48a04f8d9

* Sun Jun 21 2026 Lachlan Marie <lchlnm@pm.me> - 2605^26.git.34344e5-3
 - Update to commit 34344e576944fa016c376e7e32a71d5f0d33c707

* Sun Jun 21 2026 Lachlan Marie <lchlnm@pm.me> - 2605^25.git.c5880e7-3
 - Update to commit c5880e76180de1927c81769217a5be996305ad6c

* Sat Jun 20 2026 Lachlan Marie <lchlnm@pm.me> - 2605^24.git.f547703-3
 - Update to commit f5477039fa21d2d5a41027f9c89b1e9ebfc3b1e9

* Thu Jun 18 2026 Lachlan Marie <lchlnm@pm.me> - 2605^23.git.ee4794c-3
 - Update to commit ee4794c99e256bcb4fcfc7f884200007990235dc

* Wed Jun 17 2026 Lachlan Marie <lchlnm@pm.me> - 2605^22.git.adad3c2-3
 - Update to commit adad3c27dd32a9bb01f2a67c12d417db11c50ce1

* Wed Jun 17 2026 Lachlan Marie <lchlnm@pm.me> - 2605^21.git.99662b7-3
 - Update to commit 99662b70ffbf24a9ad50f0317f75166e0822f5a4

 - Added FEXOfflineCompiler to installed files

* Sat Jun 13 2026 Lachlan Marie <lchlnm@pm.me> - 2605^20.git.e12bd27-2
 - Update to commit e12bd2710616db6c65544bed4d4005918c51564d

* Fri Jun 12 2026 Lachlan Marie <lchlnm@pm.me> - 2605^19.git.cb01825-2
 - Update to commit cb018257cf86a4fcd274e918307b95526732ed12

* Thu Jun 04 2026 Lachlan Marie <lchlnm@pm.me> - 2605^18.git.e02953d-2
 - Update to commit e02953dc174531551219712df20355dcf4afc089

* Wed Jun 03 2026 Lachlan Marie <lchlnm@pm.me> - 2605^17.git.d848cbb-2
 - Update to commit d848cbbc0f35c5bb535107022cdbc4dfd8331824

* Tue Jun 02 2026 Lachlan Marie <lchlnm@pm.me> - 2605^16.git.a5c3fc4-2
 - Update to commit a5c3fc475145f269f511e9edce9afe28c188651a

* Sat May 30 2026 Lachlan Marie <lchlnm@pm.me> - 2605^15.git.f5fafa5-2
 - Update to commit f5fafa5b969333f964021b12443ba13fbacd620b

* Sat May 30 2026 Lachlan Marie <lchlnm@pm.me> - 2605^14.git.a1071ec-2
 - Update to commit a1071ec01ac4f5afed700a7b987bf6670ef6e639

* Fri May 29 2026 Lachlan Marie <lchlnm@pm.me> - 2605^13.git.5fd917e-2
 - Update to commit 5fd917ec2f54a1fdf980baa4cdf9a67424710ecb

* Tue May 26 2026 Lachlan Marie <lchlnm@pm.me> - 2605^12.git.cae5da5-2
 - Update to commit cae5da57771bb11a6b21c60307e5241a5d5e47b4

* Sun May 24 2026 Lachlan Marie <lchlnm@pm.me> - 2605^11.git.1240a00-2
 - Update to commit 1240a00fa50b48c1b5e0667e2281ba25e08fbd47

* Sat May 23 2026 Lachlan Marie <lchlnm@pm.me> - 2605^10.git.07f7aa3-2
 - Update to commit 07f7aa3c8fce5dcb7497744adc4b0231a7f070ec

* Fri May 22 2026 Lachlan Marie <lchlnm@pm.me> - 2605^9.git.df73e84-2
 - Update to commit df73e84725eba699446a09f11dcda7e0ca936f1f

* Thu May 21 2026 Lachlan Marie <lchlnm@pm.me> - 2605^8.git.bb0d142-2
 - Update to commit bb0d142a65d8515f13f8adf1f82c25bb35ce31e6

* Wed May 20 2026 Lachlan Marie <lchlnm@pm.me> - 2605^7.git.c98cef0-2
 - Update to commit c98cef0da152bc08574fd9c3d05d9a121ae96d51

* Wed May 20 2026 Lachlan Marie <lchlnm@pm.me> - 2605^6.git.e4daea4-2
 - Update to commit e4daea406ed41cd0857e7413c598905ac8e4cf2d

* Tue May 19 2026 Lachlan Marie <lchlnm@pm.me> - 2605^5.git.d4c80d9-2
 - Update to commit d4c80d9094aa1ae19886fd4279af2a0a9ae841f4

* Mon May 18 2026 Lachlan Marie <lchlnm@pm.me> - 2605^4.git.af4da43-2
 - Update to commit af4da43bb896dcf64ad099470d92bba5b11c9656

* Fri May 15 2026 Lachlan Marie <lchlnm@pm.me> - 2605^3.git.ab9a8c6-2
 - Update to commit ab9a8c62ab5f9156adc306564dc55798713fbf5a

* Wed May 13 2026 Lachlan Marie <lchlnm@pm.me> - 2605^2.git.50f4494-2
 - Update to commit 50f44948750c87a71baea24aadc9346f23a1d157

* Tue May 12 2026 Lachlan Marie <lchlnm@pm.me> - 2605^1.git.0d72890-2
 - Update to commit 0d728904829fc6b8550354cb34cca70ea73b7361

* Sat May 09 2026 Lachlan Marie <lchlnm@pm.me> - 2605^0.git.a04b024-2
 - Update to 2605

* Sat May 09 2026 Lachlan Marie <lchlnm@pm.me> - 2604^19.git.1bfb3ae-2
 - Update to commit 1bfb3aefcc190fc69c28786be8b27dd269a8d89e

* Fri May 08 2026 Lachlan Marie <lchlnm@pm.me> - 2604^18.git.e517f32-2
 - Update to commit e517f3259ca37a809c8eaec7a92e872d288b59a9

* Thu May 07 2026 Lachlan Marie <lchlnm@pm.me> - 2604^17.git.ed216c8-2
 - Update to commit ed216c8d4d84ea2ecb140708b759a84a2080711b

* Wed May 06 2026 Lachlan Marie <lchlnm@pm.me> - 2604^16.git.4db2a98-2
 - Update to commit 4db2a98d7ffb7cd99dd01bdeb02895cf4b6587d9

* Tue May 05 2026 Lachlan Marie <lchlnm@pm.me> - 2604^15.git.694e68b-2
 - Update to commit 694e68b8389de608f2471ba9a023e34e814ace65

* Tue May 05 2026 Lachlan Marie <lchlnm@pm.me> - 2604^14.git.47e173e-2
 - Update to commit 47e173e54921fa4f296b29cf7aefb91060217807

* Mon May 04 2026 Lachlan Marie <lchlnm@pm.me> - 2604^13.git.93015a0-2
 - Update to commit 93015a02667835faa9f6fc5b76a70d64f0c8ebd1

* Sun May 03 2026 Lachlan Marie <lchlnm@pm.me> - 2604^12.git.8577399-2
 - Update to commit 85773995e10070d07d302fa725a0e5de1c1b5ad1

* Fri May 01 2026 Lachlan Marie <lchlnm@pm.me> - 2604^11.git.8ab0075-2
 - Update to commit 8ab00758be7bb6a8530e861958397a629b48ab4e

* Thu Apr 30 2026 Lachlan Marie <lchlnm@pm.me> - 2604^10.git.098c4c5-2
 - Update to commit 098c4c57b4a45a108fda1af19c663398ddf75970

* Wed Apr 29 2026 Lachlan Marie <lchlnm@pm.me> - 2604^9.git.821efab-2
 - Update to commit 821efab8aa0b1f056917ff7605c507c443482928

* Tue Apr 28 2026 Lachlan Marie <lchlnm@pm.me> - 2604^8.git.dd145aa-2
 - Update to commit dd145aaa88f58726e159abe0e2614b19fa0fa2e7

* Sun Apr 26 2026 Lachlan Marie <lchlnm@pm.me> - 2604^7.git.7dc1f54-1
 - Update to commit 7dc1f54fb61a25aa9312cd16c2a859524cb0ce5c

* Sat Apr 25 2026 Lachlan Marie <lchlnm@pm.me> - 2604^6.git.4b02c04-1
 - Update to commit 4b02c04afce5055234e212af206c08abd054375f

* Wed Apr 22 2026 Lachlan Marie <lchlnm@pm.me> - 2604^5.git.701555e-1
 - Update to commit 701555e400e6179a7c0074e9869ca0063d225b98

* Tue Apr 21 2026 Lachlan Marie <lchlnm@pm.me> - 2604^4.git.59755ec-1
 - Update to commit 59755ec11551f6ed689cead9f3f0d3b77e815ddf

* Sat Apr 18 2026 Lachlan Marie <lchlnm@pm.me> - 2604^3.git.d41d52b-1
 - Update to commit d41d52b88914a5c3e9a7137cedb122f2f3a244d4

* Thu Apr 16 2026 Lachlan Marie <lchlnm@pm.me> - 2604^2.git.441116e-1
 - Update to commit 441116e1e67df6d0b8f5d21a14349c12754d1bfd

* Wed Apr 15 2026 Lachlan Marie <lchlnm@pm.me> - 2604^1.git.2ea0de9-1
 - Update to commit 2ea0de92f404f100a5d6c2f29d5398b3f5db507c

* Fri Apr 10 2026 Lachlan Marie <lchlnm@pm.me> - 2604^0.git.9681559-1
 - Update to 2604

* Thu Apr 09 2026 Lachlan Marie <lchlnm@pm.me> - 2603^53.git.ce65f53-1
 - Update to commit ce65f5376f73db94b285caf8562d676ddd23679e

* Wed Apr 08 2026 Lachlan Marie <lchlnm@pm.me> - 2603^52.git.0695249-1
 - Update to commit 0695249fc83b14dff3ae1a045019cb9975a3b694

* Sat Apr 04 2026 Lachlan Marie <lchlnm@pm.me> - 2603^51.git.73ffff7-1
 - Update to commit 73ffff7d22aae4b76a428508bba1343c9dc714a8

* Fri Apr 03 2026 Lachlan Marie <lchlnm@pm.me> - 2603^50.git.dc48a4f-1
 - Update to commit dc48a4f73c651a68203769b07ef19c5ac84990ea

* Thu Apr 02 2026 Lachlan Marie <lchlnm@pm.me> - 2603^49.git.c6d2ce0-1
 - Update to commit c6d2ce043f004dd2fcd3c5dfba3cb5e85811f1ce

* Wed Apr 01 2026 Lachlan Marie <lchlnm@pm.me> - 2603^48.git.34b48c4-1
 - Update to commit 34b48c4069087e92644a882437adad75876b9ac5

* Sun Mar 29 2026 Lachlan Marie <lchlnm@pm.me> - 2603^47.git.5b4a596-1
 - Update to commit 5b4a5969cc81c9ef8e7217778baa3c3d81991fe6

* Fri Mar 27 2026 Lachlan Marie <lchlnm@pm.me> - 2603^46.git.b77ddcf-1
 - Update to commit b77ddcf1a78b18a13963299a98ecc06a863beae0

* Fri Mar 27 2026 Lachlan Marie <lchlnm@pm.me> - 2603^45.git.3ef6775-1
 - Update to commit 3ef677537d1573c85dab4b507f805a1e7babe2af

* Thu Mar 26 2026 Lachlan Marie <lchlnm@pm.me> - 2603^44.git.6bd476f-1
 - Update to commit 6bd476fb035db94988e6f09ff16abe016c44ca60

* Wed Mar 25 2026 Lachlan Marie <lchlnm@pm.me> - 2603^43.git.5149ebc-1
 - Update to commit 5149ebc70e95522707d15df9ba55e481c3ddfb7a

* Tue Mar 24 2026 Lachlan Marie <lchlnm@pm.me> - 2603^42.git.6da963a-1
 - Update to commit 6da963a6954eb66531821165a863668acfadff33

* Mon Mar 23 2026 Lachlan Marie <lchlnm@pm.me> - 2603^41.git.bc533c8-1
 - Update to commit bc533c80500ec1bc138ab68db7154d2bbeb2b99d

* Mon Mar 23 2026 Lachlan Marie <lchlnm@pm.me> - 2603^41.git.bc533c8-1
 - Update to commit bc533c80500ec1bc138ab68db7154d2bbeb2b99d

* Mon Mar 16 2026 Lachlan Marie <lchlnm@pm.me> - 2603^40.git.f894cd9-1
 - Update to commit f894cd90f30c8fcd9d881aaa4a7e04c0e58d8537

* Sun Mar 15 2026 Lachlan Marie <lchlnm@pm.me> - 2603^39.git.6177ab9-1
 - Update to commit 6177ab957b60f3d2e71b4c2d4686b71f39d08eb9

* Thu Mar 12 2026 Lachlan Marie <lchlnm@pm.me> - 2603^38.git.957c1fc-1
 - Update to commit 957c1fc4201e0029c091f36604978d610d968e3a

* Wed Mar 11 2026 Lachlan Marie <lchlnm@pm.me> - 2603^37.git.9d4a71b-1
 - Update to commit 9d4a71b57a6b7d0388df58b2615fb73ad93fdea2

* Thu Mar 05 2026 Lachlan Marie <lchlnm@pm.me> - 2603^36.git.9eb639e-1
 - Update to commit 9eb639e89124b5976501029d886740b0e76c01c9

* Sun Mar 01 2026 Lachlan Marie <lchlnm@pm.me> - 2601^35.git.4968dc4-1
 - Update to commit 4968dc4bab80f3a8b296a59df7b9b42ebf40429e

* Sun Jan 25 2026 Lachlan Marie <lchlnm@pm.me> - 2601^34.git.cc54724-1
 - Update to commit cc54724ff18fc77a2315b119888b5691c5f04c0e

* Wed Jan 21 2026 Lachlan Marie <lchlnm@pm.me> - 2601^31.git.cf61d73-1
 - Update to commit cf61d7349a9de3a97eaa9f04b775ace64db801a4

* Wed Jan 21 2026 Lachlan Marie <lchlnm@pm.me> - 2601^30.git.87de3ec-1
 - Update to commit 87de3ec3e3736a685d49dc285abb743b937ef03d

* Mon Jan 19 2026 Lachlan Marie <lchlnm@pm.me> - 2601^29.git.4428dbf-1
 - Update to commit 4428dbf885ebbbba6806f13c3f9c27a672ad3ccf

* Sat Jan 17 2026 Lachlan Marie <lchlnm@pm.me> - 2601^28.git.78fd9b4-1
 - Update to commit 78fd9b4fe47baaf136ae4a551968f8cf6618bfeb

* Wed Jan 14 2026 Lachlan Marie <lchlnm@pm.me> - 2601^27.git.28c486d-1
 - Update to commit 28c486dad5c746607a3c07378aae63601f8a40b8

* Wed Jan 14 2026 Lachlan Marie <lchlnm@pm.me> - 2601^26.git.bcf5345-1
 - Update to commit bcf53458adeb809fa1550713bb0275a336fca22e

* Wed Jan 14 2026 Lachlan Marie <lchlnm@pm.me> - 2601^25.git.6438a83-1
 - Update to commit 6438a838ce875b1e22cc5154b7d610f43ff6bcac

* Tue Jan 13 2026 Lachlan Marie <lchlnm@pm.me> - 2601^24.git.d7d870c-1
 - Update to commit d7d870cb4caee196595ece036113725ee6678758

* Tue Jan 13 2026 Lachlan Marie <lchlnm@pm.me> - 2601^23.git.251a3ba-1
 - Update to commit 251a3babadcfc4a7f0c13f36fa39c720494ad3e5

* Sat Jan 10 2026 Lachlan Marie <lchlnm@pm.me> - 2601^22.git.4c50a92-1
 - Update to commit 4c50a92e1212b6d8be8f75be0a1f17476de470b2

* Thu Jan 08 2026 Lachlan Marie <lchlnm@pm.me> - 2601^21.git.1188c90-1
 - Update to commit 1188c90c10569ca800d7a99c11e59cfeab5e2cc9

* Tue Jan 06 2026 Lachlan Marie <lchlnm@pm.me> - 2512^20.git.651ef64-1
 - Update to commit 651ef64617b8c13d42e8db9433b876cdc0b09759

* Mon Jan 05 2026 Lachlan Marie <lchlnm@pm.me> - 2512^19.git.e1c6a91-1
 - Update to commit e1c6a910d2820cba28d449f0630e6762243b1c2d

* Mon Jan 05 2026 Lachlan Marie <lchlnm@pm.me> - 2512^18.git.b407688-1
 - Update to commit b40768895d0c875a3f131d4ca5008405918ae3c2

* Sat Jan 03 2026 Lachlan Marie <lchlnm@pm.me> - 2512^17.git.62383a1-1
 - Update to commit 62383a1c72940e0d594740a361634d4949eec9e6

* Fri Jan 02 2026 Lachlan Marie <lchlnm@pm.me> - 2512^16.git.a3779be-1
 - Update to commit a3779be9e1c9874386269fb1c8fe5e53d99778f4

* Thu Jan 01 2026 Lachlan Marie <lchlnm@pm.me> - 2512^15.git.4889596-1
 - Update to commit 488959600e27c31c4b009e2f1f89a43d31171f24

* Tue Dec 30 2025 Lachlan Marie <lchlnm@pm.me> - 2512^14.git.c8d72ea-1
 - Update to commit c8d72eabe589392b962bec94d002c5ffdb7381c2

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
