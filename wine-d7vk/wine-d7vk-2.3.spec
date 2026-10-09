%global debug_package %{nil}

%global __brp_llvm_compile_lto_elf %nil
%global __brp_strip_lto %nil
%global __brp_strip_static_archive %nil

Name:           wine-d7vk
Version:        2.3
Release:        ec2%{dist}
Summary:        Vulkan-based implementation of D3D7, 6, 5 and 3 for Wine

License:        zlib AND MIT
URL:            https://github.com/WinterSnowfall/d7vk
Source0:        %{url}/archive/v%{version}/d7vk-%{version}.tar.gz
Source1:        https://github.com/bylaws/llvm-mingw/releases/download/20250920/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64.tar.xz


%{lua:
local externals = {
  { name="dxbc-spirv", ref="bf14419", owner="doitsujin", path="subprojects/dxbc-spirv", license="MIT" },
  { name="SPIRV-Headers", ref="c8ad050", owner="KhronosGroup", path="subprojects/dxbc-spirv/submodules/spirv_headers", version="1.4.328.1", license="CC0" },
  { name="libdisplay-info", ref="275e645", owner="doitsujin", path="subprojects/libdisplay-info",  license="MIT" },
  { name="SPIRV-Headers", ref="04f10f6", owner="KhronosGroup", path="include/spirv", version="1.3.341.0", license="CC0" },
  { name="Vulkan-Headers", ref="8864cdc", owner="KhronosGroup", path="include/vulkan", version="1.4.344.0", license="Apache-2.0" },
  { name="mingw-directx-headers", ref="9df86f2", owner="misyltoad", path="include/native/directx", license="LGPL v2.1" },
}

for i, s in ipairs(externals) do
  si = 100 + i
  print(string.format("Source%d: https://github.com/%s/%s/archive/%s/%s-%s.tar.gz", si, s.owner, s.name, s.ref, s.name, s.ref).."\n")
  print(string.format("Provides: bundled(%s) = %s", (s.package or s.name), (s.version or "0")).."\n")
end

function print_setup_externals()
  for i, s in ipairs(externals) do
    si = 100 + i
    print(string.format("mkdir -p %s", (s.path or s.name)).."\n")
    print(string.format("tar -xzf %s --strip-components=1 -C %s", rpm.expand("%{SOURCE"..si.."}"), (s.path or s.name)).."\n")
  end
end
}


BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  glslang
BuildRequires:  meson

Requires:       vulkan-loader
Requires:       wine-dxvk-d3d9

ExclusiveArch:  aarch64

%description
D7VK proxies Direct3D 7/6/5/3 to DXVK's D3D9 backend on top of Wine's DirectDraw.

Wine's ddraw.dll must stay in place: copy %{_datadir}/d7vk/x32/ddraw.dll
next to the game executable and set a "native, builtin" override for ddraw.
Only 32-bit: the D3D7-era code uses SSE intrinsics that ARM64EC lacks.

%prep
%autosetup -n d7vk-%{version} -a1 -p1
%{lua: print_setup_externals()}

cat << EOF > build-i686.txt
[binaries]
ar = 'i686-w64-mingw32-ar'
c = 'i686-w64-mingw32-gcc'
cpp = 'i686-w64-mingw32-g++'
ld = 'i686-w64-mingw32-ld'
windres = 'i686-w64-mingw32-windres'
strip = 'strip'
widl = 'i686-w64-mingw32-widl'

[host_machine]
system = 'windows'
cpu_family = 'x86'
cpu = 'i686'
endian = 'little'
EOF


%build
%undefine _auto_set_build_flags

export CFLAGS="-DNDEBUG -fPIC -O2 -pthread -fno-strict-aliasing -fno-stack-protector -fno-lto"
export CXXFLAGS="${CFLAGS} -fpermissive"
export LDFLAGS="-fPIC -Wl,--sort-common -Wl,--gc-sections -Wl,-O1 -fno-lto"
export PATH="$PWD/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64/bin:$PATH"
meson setup --cross-file build-i686.txt --buildtype=release -Dbuild_id=true \
    -Denable_dxgi=false -Denable_d3d11=false -Denable_d3d10=false -Denable_d3d8=false \
    build-i686
meson compile -C build-i686 %{?_smp_mflags}


%install
install -Dpm 644 $(find build-i686/src/ddraw -name ddraw.dll) %{buildroot}%{_datadir}/d7vk/x32/ddraw.dll


%files
%license LICENSE
%doc README.md
%{_datadir}/d7vk/

%changelog
* Fri Oct 09 2026 Lachlan Marie <lchlnm@pm.me> - 2.3-ec2
- Require wine-dxvk-d3d9

* Wed Sep 30 2026 Lachlan Marie <lchlnm@pm.me> - 2.3-ec1
- Initial package
