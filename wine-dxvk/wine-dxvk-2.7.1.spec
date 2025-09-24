%global debug_package %{nil}

%global winepedir aarch64-windows
%global __brp_llvm_compile_lto_elf %nil
%global __brp_strip_lto %nil
%global __brp_strip_static_archive %nil

Name:           wine-dxvk
Version:        2.7.1
Release:        ec.%autorelease
Summary:        Vulkan-based implementation of D3D8, 9, 10 and 11 for Linux / Wine (ARM64EC)

License:        zlib AND MIT
URL:            https://github.com/doitsujin/dxvk
Source0:        %{url}/archive/v%{version}/dxvk-%{version}.tar.gz
Source1:        https://github.com/bylaws/llvm-mingw/releases/download/20250920/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64.tar.xz


%{lua:
local externals = {
  { name="mingw-directx-headers", ref="9df86f2", owner="misyltoad", path="include/native/directx", license="LGPL v2.1" },
  { name="SPIRV-Headers", ref="8b246ff", owner="KhronosGroup", path="include/spirv", version="1.3.280.0", license="CC0" },
  { name="Vulkan-Headers", ref="234c4b7", owner="KhronosGroup", path="include/vulkan", version="1.4.307", license="Apache-2.0" },
  { name="libdisplay-info", ref="275e645", owner="doitsujin", path="subprojects/libdisplay-info",  license="MIT" },
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
    print(string.format("mkdir -p %s", (s.path or s.name)).."\n")
    print(string.format("tar -xzf %s --strip-components=1 -C %s", rpm.expand("%{SOURCE"..si.."}"), (s.path or s.name)).."\n")
    ::continue2::
  end
end
}



BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  glslang
BuildRequires:  meson
BuildRequires:  wine-devel

BuildRequires:  mingw64-filesystem
BuildRequires:  mingw64-binutils
BuildRequires:  mingw64-headers
BuildRequires:  mingw64-cpp
BuildRequires:  mingw64-gcc
BuildRequires:  mingw64-gcc-c++
BuildRequires:  mingw64-winpthreads-static
BuildRequires:  mingw64-vulkan-headers
BuildRequires:  mingw64-spirv-headers

Requires(pre):  vulkan-tools

Requires:       wine-core
Requires:       wine-dxvk-dxgi = %{version}-%{release}
Requires:       vulkan-loader

# We want x86_64 users to always have also 32 bit lib, it's the same what wine does

# Recommend also d3d8, d3d9, and d3d10
Recommends:     wine-dxvk-d3d8  = %{version}-%{release}
Recommends:     wine-dxvk-d3d9  = %{version}-%{release}
Recommends:     wine-dxvk-d3d10 = %{version}-%{release}

Requires(posttrans):   %{_sbindir}/alternatives wine-core
Requires(preun):       %{_sbindir}/alternatives

ExclusiveArch:  aarch64

Provides:       bundled(libdisplay-info) = 0.3.0~dev^git275e645

%description
%{summary}

%package dxgi
Summary:        DXVK DXGI implementation

%description dxgi
%{summary}

This package doesn't enable the use of this DXGI implementation,
it should be installed and overridden per prefix.

%package d3d10
Summary:        DXVK D3D10 implementation

Requires:       wine-dxvk = %{version}-%{release}

%description d3d10
%{summary}

%package d3d9
Summary:        DXVK D3D9 implementation

Requires:       wine-dxvk = %{version}-%{release}

%description d3d9
%{summary}

%package d3d8
Summary:        DXVK D3D8 implementation

Requires:       wine-dxvk = %{version}-%{release}

%description d3d8
%{summary}

%prep
%autosetup -n dxvk-%{version} -a1 -p1
%{lua: print_setup_externals()}

cat << EOF > build-arm64ec.txt
[binaries]
ar = 'arm64ec-w64-mingw32-ar'
c = 'arm64ec-w64-mingw32-gcc'
cpp = 'arm64ec-w64-mingw32-g++'
ld = 'arm64ec-w64-mingw32-ld'
windres = 'arm64ec-w64-mingw32-windres'
strip = 'strip'
widl = 'arm64ec-w64-mingw32-widl'
pkgconfig = 'aarch64-linux-gnu-pkg-config'

[host_machine]
system = 'windows'
cpu_family = 'aarch64'
cpu = 'aarch64'
endian = 'little'
EOF


%build
%undefine __brp_strip_lto
%undefine __brp_strip_static_archive
%undefine _auto_set_build_flags

export CFLAGS="%optflags -DNDEBUG -fPIC -O2 -pthread -fno-strict-aliasing -fuse-linker-plugin -fno-stack-protector -fno-stack-clash-protection -fno-lto"
export CXXFLAGS="${CFLAGS} -fpermissive"
export LDFLAGS="-fPIC -Wl,--sort-common -Wl,--gc-sections -Wl,-O1 -fuse-linker-plugin -fno-lto"
export PATH="$PWD/llvm-mingw-20250920-ucrt-ubuntu-22.04-aarch64/bin:$PATH"
%meson --cross-file build-arm64ec.txt --buildtype=release -Dbuild_id=true
%meson_build


%install
%meson_install
winebuild --builtin %{buildroot}%{_bindir}/dxgi.dll
winebuild --builtin %{buildroot}%{_bindir}/d3d8.dll
winebuild --builtin %{buildroot}%{_bindir}/d3d9.dll
winebuild --builtin %{buildroot}%{_bindir}/d3d10core.dll
winebuild --builtin %{buildroot}%{_bindir}/d3d11.dll

rm -rf %{buildroot}%{_libdir}

mkdir -p %{buildroot}%{_libdir}/wine/%{winepedir}/
install -p -m 644 %{buildroot}%{_bindir}/dxgi.dll %{buildroot}%{_libdir}/wine/%{winepedir}/dxvk-dxgi.dll
install -p -m 644 %{buildroot}%{_bindir}/d3d8.dll %{buildroot}%{_libdir}/wine/%{winepedir}/dxvk-d3d8.dll
install -p -m 644 %{buildroot}%{_bindir}/d3d9.dll %{buildroot}%{_libdir}/wine/%{winepedir}/dxvk-d3d9.dll
install -p -m 644 %{buildroot}%{_bindir}/d3d10core.dll %{buildroot}%{_libdir}/wine/%{winepedir}/dxvk-d3d10core.dll
install -p -m 644 %{buildroot}%{_bindir}/d3d11.dll %{buildroot}%{_libdir}/wine/%{winepedir}/dxvk-d3d11.dll

# Clean-up
rm -rf %{buildroot}%{_bindir}

%posttrans
if vulkaninfo |& grep "ERROR_INITIALIZATION_FAILED\|ERROR_SURFACE_LOST_KHR\|Vulkan support is incomplete" > /dev/null; then
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d11.dll 'wine-d3d11%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d11.dll 5
else
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d11.dll 'wine-d3d11%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d11.dll 20
fi

%posttrans dxgi
if vulkaninfo |& grep "ERROR_INITIALIZATION_FAILED\|ERROR_SURFACE_LOST_KHR\|Vulkan support is incomplete" > /dev/null; then
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/dxgi.dll 'wine-dxgi%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-dxgi.dll 5
else
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/dxgi.dll 'wine-dxgi%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-dxgi.dll 20
fi

%posttrans d3d10
if vulkaninfo |& grep "ERROR_INITIALIZATION_FAILED\|ERROR_SURFACE_LOST_KHR\|Vulkan support is incomplete" > /dev/null; then
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d10core.dll 'wine-d3d10core%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d10core.dll 5
else
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d10core.dll 'wine-d3d10core%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d10core.dll 20
fi

%posttrans d3d9
if vulkaninfo |& grep "ERROR_INITIALIZATION_FAILED\|ERROR_SURFACE_LOST_KHR\|Vulkan support is incomplete" > /dev/null; then
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d9.dll 'wine-d3d9%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d9.dll 5
else
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d9.dll 'wine-d3d9%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d9.dll 20
fi

%posttrans d3d8
if vulkaninfo |& grep "ERROR_INITIALIZATION_FAILED\|ERROR_SURFACE_LOST_KHR\|Vulkan support is incomplete" > /dev/null; then
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d8.dll 'wine-d3d8%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d8.dll 5
else
    %{_sbindir}/alternatives --install %{_libdir}/wine/%{winepedir}/d3d8.dll 'wine-d3d8%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d8.dll 20
fi

%postun
%{_sbindir}/alternatives --remove 'wine-d3d11%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d11.dll

%postun d3d10
%{_sbindir}/alternatives --remove 'wine-d3d10core%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d10core.dll

%postun d3d9
%{_sbindir}/alternatives --remove 'wine-d3d9%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d9.dll

%postun d3d8
%{_sbindir}/alternatives --remove 'wine-d3d8%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-d3d8.dll

%postun dxgi
%{_sbindir}/alternatives --remove 'wine-dxgi%{?_isa}' %{_libdir}/wine/%{winepedir}/dxvk-dxgi.dll

%files
%license LICENSE
%doc README.md
%{_libdir}/wine/%{winepedir}/dxvk-d3d11.dll

%files d3d10
%license LICENSE
%{_libdir}/wine/%{winepedir}/dxvk-d3d10core.dll

%files d3d9
%license LICENSE
%{_libdir}/wine/%{winepedir}/dxvk-d3d9.dll

%files d3d8
%license LICENSE
%{_libdir}/wine/%{winepedir}/dxvk-d3d8.dll

%files dxgi
%license LICENSE
%{_libdir}/wine/%{winepedir}/dxvk-dxgi.dll

%changelog
%autochangelog
