%global debug_package %{nil}

%global winepedir aarch64-windows

%global __brp_llvm_compile_lto_elf %nil
%global __brp_strip_lto %nil
%global __brp_strip_static_archive %nil

Name:           wine-vkd3d-proton
Version:        3.0.1
Release:        ec1%{dist}
Summary:        Vulkan-based implementation of D3D12 for Wine (ARM64EC)

License:        LGPL-2.1-or-later AND MIT
URL:            https://github.com/HansKristian-Work/vkd3d-proton
Source0:        %{url}/archive/v%{version}/vkd3d-proton-%{version}.tar.gz
Source1:        https://github.com/bylaws/llvm-mingw/releases/download/20250920/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64.tar.xz


%{lua:
local externals = {
  { name="SPIRV-Headers", ref="f88a2d7", owner="KhronosGroup", paths={"khronos/SPIRV-Headers", "subprojects/dxil-spirv/third_party/spirv-headers"} },
  { name="Vulkan-Headers", ref="ad9ce12", owner="KhronosGroup", paths={"khronos/Vulkan-Headers"} },
  { name="dxil-spirv", ref="62dbb07", owner="HansKristian-Work", paths={"subprojects/dxil-spirv"} },
  { name="dxbc-spirv", ref="29c93ae", owner="doitsujin", paths={"subprojects/dxil-spirv/subprojects/dxbc-spirv"} },
  { name="SPIRV-Headers", ref="c8ad050", owner="KhronosGroup", paths={"subprojects/dxil-spirv/subprojects/dxbc-spirv/submodules/spirv_headers"} },
}

local seen = {}
for i, s in ipairs(externals) do
  print(string.format("Source%d: https://github.com/%s/%s/archive/%s/%s-%s.tar.gz", 100 + i, s.owner, s.name, s.ref, s.name, s.ref).."\n")
  if not seen[s.name] then
    print(string.format("Provides: bundled(%s) = 0", s.name).."\n")
    seen[s.name] = true
  end
end

function print_setup_externals()
  for i, s in ipairs(externals) do
    for _, path in ipairs(s.paths) do
      print(string.format("mkdir -p %s", path).."\n")
      print(string.format("tar -xzf %s --strip-components=1 -C %s", rpm.expand("%{SOURCE"..(100 + i).."}"), path).."\n")
    end
  end
end
}

BuildRequires:  meson
BuildRequires:  glslang
BuildRequires:  wine-devel

Requires(pre):  vulkan-tools

Requires:       wine-core >= 11.18-ec2
Requires:       wine-dxvk-dxgi
Requires:       vulkan-loader

Requires(posttrans):   %{_sbindir}/alternatives wine-core
Requires(preun):       %{_sbindir}/alternatives

ExclusiveArch:  aarch64

%description
%{summary}

%prep
%autosetup -n vkd3d-proton-%{version} -a1 -p1
%{lua: print_setup_externals()}

cat << EOF > build-arm64ec.txt
[binaries]
ar = 'arm64ec-w64-mingw32-ar'
c = 'arm64ec-w64-mingw32-gcc'
cpp = 'arm64ec-w64-mingw32-g++'
ld = 'arm64ec-w64-mingw32-ld'
windres = 'arm64ec-w64-mingw32-windres'
widl = 'arm64ec-w64-mingw32-widl'
strip = 'arm64ec-w64-mingw32-strip'

[host_machine]
system = 'windows'
cpu_family = 'aarch64'
cpu = 'aarch64'
endian = 'little'
EOF


%build
%undefine _auto_set_build_flags

export CFLAGS="-DNDEBUG -O2 -fno-lto"
export CXXFLAGS="${CFLAGS}"
export LDFLAGS="-Wl,--gc-sections -fno-lto"
export PATH="$PWD/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64/bin:$PATH"
%meson --cross-file build-arm64ec.txt --buildtype=release -Denable_tests=false
%meson_build


%install
mkdir -p %{buildroot}%{_libdir}/wine/%{winepedir}
for dll in d3d12 d3d12core; do
    install -p -m 644 %{_vpath_builddir}/libs/$dll/$dll.dll %{buildroot}%{_libdir}/wine/%{winepedir}/vkd3d-proton-$dll.dll
    winebuild --builtin %{buildroot}%{_libdir}/wine/%{winepedir}/vkd3d-proton-$dll.dll
done

%posttrans
if vulkaninfo |& grep "ERROR_INITIALIZATION_FAILED\|ERROR_SURFACE_LOST_KHR\|Vulkan support is incomplete" > /dev/null; then
    prio=5
else
    prio=20
fi
%{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d12.dll 'wine-d3d12%{?_isa}' %{_libdir}/wine/%{winepedir}/vkd3d-proton-d3d12.dll $prio \
    --slave %{_libdir}/wine/%{winepedir}/d3d12core.dll 'wine-d3d12core%{?_isa}' %{_libdir}/wine/%{winepedir}/vkd3d-proton-d3d12core.dll

%postun
%{_sbindir}/alternatives --remove 'wine-d3d12%{?_isa}' %{_libdir}/wine/%{winepedir}/vkd3d-proton-d3d12.dll

%files
%license LICENSE COPYING
%doc README.md
%{_libdir}/wine/%{winepedir}/vkd3d-proton-d3d12.dll
%{_libdir}/wine/%{winepedir}/vkd3d-proton-d3d12core.dll

%changelog
* Wed Sep 23 2026 Lachlan Marie <lchlnm@pm.me> - 3.0.1-ec1
- Initial ARM64EC build
