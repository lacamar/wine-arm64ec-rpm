Name:		vkd3d
Version:	1.14
Release:	1.arm64ec%{?dist}
Summary:	D3D12 to Vulkan translation library

# Automatically converted from old format: LGPLv2+ - review is highly recommended.
License:	LicenseRef-Callaway-LGPLv2+
URL:		https://source.winehq.org/git/vkd3d.git
Source0:	https://dl.winehq.org/vkd3d/source/%{name}-%{version}.tar.xz
Source1:	https://dl.winehq.org/vkd3d/source/%{name}-%{version}.tar.xz.sign

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:	make
BuildRequires:	bison
BuildRequires:	flex
BuildRequires:	gcc
BuildRequires:	libxcb-devel
BuildRequires:	spirv-headers-devel
BuildRequires:	spirv-tools-devel
BuildRequires:	vulkan-loader-devel
BuildRequires:	xcb-util-devel
BuildRequires:	xcb-util-keysyms-devel
BuildRequires:	xcb-util-wm-devel

BuildRequires:	mingw32-filesystem >= 95
BuildRequires:	mingw32-gcc
BuildRequires:	mingw32-spirv-headers
BuildRequires:	mingw32-spirv-tools
BuildRequires:	mingw32-vulkan-headers
BuildRequires:	mingw32-vulkan-loader

BuildRequires:	mingw64-filesystem >= 95
BuildRequires:	mingw64-gcc
BuildRequires:	mingw64-spirv-headers
BuildRequires:	mingw64-spirv-tools
BuildRequires:	mingw64-vulkan-headers
BuildRequires:	mingw64-vulkan-loader

ExclusiveArch:	%{ix86} x86_64 %{arm} aarch64

%description
The vkd3d project includes libraries, shaders, utilities, and demos for
translating D3D12 to Vulkan.


%package -n libvkd3d
Summary:	D3D12 to Vulkan translation library


%description -n libvkd3d
libvkd3d is the main component of the vkd3d project. It's a 3D graphics
library built on top of Vulkan with an API very similar to Direct3D 12.


%package -n libvkd3d-devel
Summary:	Development files for vkd3d
Requires:	libvkd3d%{?_isa} = %{version}-%{release}


%description -n libvkd3d-devel
Development files for vkd3d


%package -n vkd3d-compiler
Summary:	Compiler tool for vkd3d


%description -n vkd3d-compiler
Compiler tool for vkd3d


%package -n libvkd3d-shader
Summary:	Shader library for vkd3d


%description -n libvkd3d-shader
Shader library for vkd3d


%package -n libvkd3d-shader-devel
Summary:	Development files for libvkd3d-shader
Requires:	libvkd3d-devel%{?_isa} = %{version}-%{release}
Requires:	libvkd3d-shader%{?_isa} = %{version}-%{release}


%description -n libvkd3d-shader-devel
Development files for libvkd3d-shader


%package -n libvkd3d-utils
Summary:	Utility library for vkd3d


%description -n libvkd3d-utils
libvkd3d-utils contains simple implementations of various functions which
might be useful for source ports of Direct3D 12 applications.


%package -n libvkd3d-utils-devel
Summary:	Development files for libvkd3d-utils
Requires:	libvkd3d-devel%{?_isa} = %{version}-%{release}
Requires:	libvkd3d-utils%{?_isa} = %{version}-%{release}


%description -n libvkd3d-utils-devel
Development files for libvkd3d-utils


%package -n mingw32-%{name}
Summary:	%{summary}
BuildArch:	noarch


%description -n mingw32-%{name}
%{summary}.


%package -n mingw64-%{name}
Summary:	%{summary}
BuildArch:	noarch


%description -n mingw64-%{name}
%{summary}.


%{?mingw_debug_package}


%prep
%autosetup -p1
mkdir ../mingw-build
cp -rp . ../mingw-build


%build
%configure
%make_build

pushd ../mingw-build
export SONAME_LIBVULKAN=lvulkan-1
%mingw_configure
%mingw_make %{?_smp_mflags}
popd


%install
%make_install
pushd ../mingw-build
%mingw_make_install
%mingw_debug_install_post
popd

#Remove libtool files and static libraries
find %{buildroot} -regextype egrep -regex '.*\.a$|.*\.la$' ! -iname '*.dll.a' -delete


%files -n libvkd3d
%doc AUTHORS INSTALL README
%license COPYING LICENSE
%{_libdir}/libvkd3d.so.1
%{_libdir}/libvkd3d.so.1.*


%files -n libvkd3d-devel
%dir %{_includedir}/vkd3d
%{_includedir}/vkd3d/vkd3d.h
%{_includedir}/vkd3d/vkd3d_d3d12.h
%{_includedir}/vkd3d/vkd3d_d3d12sdklayers.h
%{_includedir}/vkd3d/vkd3d_d3d9types.h
%{_includedir}/vkd3d/vkd3d_d3dcommon.h
%{_includedir}/vkd3d/vkd3d_d3dcompiler.h
%{_includedir}/vkd3d/vkd3d_d3dcompiler_types.h
%{_includedir}/vkd3d/vkd3d_d3dx9shader.h
%{_includedir}/vkd3d/vkd3d_d3d12shader.h
%{_includedir}/vkd3d/vkd3d_dxgibase.h
%{_includedir}/vkd3d/vkd3d_dxgiformat.h
%{_includedir}/vkd3d/vkd3d_types.h
%{_includedir}/vkd3d/vkd3d_windows.h
%{_libdir}/libvkd3d.so
%{_libdir}/pkgconfig/libvkd3d.pc


%files -n vkd3d-compiler
%{_bindir}/vkd3d-compiler
%{_bindir}/vkd3d-dxbc


%files -n libvkd3d-shader
%license COPYING LICENSE
%{_libdir}/libvkd3d-shader.so.1
%{_libdir}/libvkd3d-shader.so.1.*


%files -n libvkd3d-shader-devel
%{_includedir}/vkd3d/vkd3d_shader.h
%{_libdir}/libvkd3d-shader.so
%{_libdir}/pkgconfig/libvkd3d-shader.pc


%files -n libvkd3d-utils
%{_libdir}/libvkd3d-utils.so.1
%{_libdir}/libvkd3d-utils.so.1.*


%files -n libvkd3d-utils-devel
%{_includedir}/vkd3d/vkd3d_utils.h
%{_libdir}/libvkd3d-utils.so
%{_libdir}/pkgconfig/libvkd3d-utils.pc


%files -n mingw32-%{name}
%license COPYING LICENSE
%{mingw32_bindir}/libvkd3d-1.dll
%{mingw32_bindir}/libvkd3d-shader-1.dll
%{mingw32_bindir}/libvkd3d-utils-1.dll
%{mingw32_includedir}/%{name}/
%{mingw32_bindir}/vkd3d-compiler.exe
%{mingw32_bindir}/vkd3d-dxbc.exe
%{mingw32_libdir}/pkgconfig/libvkd3d.pc
%{mingw32_libdir}/pkgconfig/libvkd3d-shader.pc
%{mingw32_libdir}/pkgconfig/libvkd3d-utils.pc
%{mingw32_libdir}/libvkd3d.dll.a
%{mingw32_libdir}/libvkd3d-shader.dll.a
%{mingw32_libdir}/libvkd3d-utils.dll.a


%files -n mingw64-%{name}
%license COPYING LICENSE
%{mingw64_bindir}/libvkd3d-1.dll
%{mingw64_bindir}/libvkd3d-shader-1.dll
%{mingw64_bindir}/libvkd3d-utils-1.dll
%{mingw64_bindir}/vkd3d-compiler.exe
%{mingw64_bindir}/vkd3d-dxbc.exe
%{mingw64_includedir}/%{name}/
%{mingw64_libdir}/pkgconfig/libvkd3d.pc
%{mingw64_libdir}/pkgconfig/libvkd3d-shader.pc
%{mingw64_libdir}/pkgconfig/libvkd3d-utils.pc
%{mingw64_libdir}/libvkd3d.dll.a
%{mingw64_libdir}/libvkd3d-shader.dll.a
%{mingw64_libdir}/libvkd3d-utils.dll.a


%changelog
* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.14-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sun Jan 19 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.14-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Fri Dec 06 2024 - Michael Cronenworth <mike@cchtml.com> - 1.14-1
- version update

* Wed Sep 04 2024 Miroslav Suchý <msuchy@redhat.com> - 1.12-2
- convert license to SPDX

* Sat Jul 20 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Mar 28 2024 - Michael Cronenworth <mike@cchtml.com> - 1.11-1
- version update

* Sat Jan 27 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Thu Jan 18 2024 - Michael Cronenworth <mike@cchtml.com> - 1.10-1
- version update

* Mon Dec 18 2023 Florian Weimer <fweimer@redhat.com> - 1.9-2
- Fix C compatibility issue in configure script, run autoconf

* Sun Oct 01 2023 - Michael Cronenworth <mike@cchtml.com> - 1.9-1
- version update

* Sat Jul 22 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Mon Jul 10 2023 - Michael Cronenworth <mike@cchtml.com> - 1.8-1
- version update

* Sat Apr 01 2023 - Michael Cronenworth <mike@cchtml.com> - 1.7-1
- version update

* Sat Jan 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Thu Jan 12 2023 - Michael Cronenworth <mike@cchtml.com> - 1.6-1
- version update

* Mon Oct 24 2022 - Michael Cronenworth <mike@cchtml.com> - 1.5-1
- version update

* Thu Aug 25 2022 - Michael Cronenworth <mike@cchtml.com> - 1.4-3
- Include MinGW debuginfo packages

* Sat Jul 23 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Sat Jun 25 2022 - Michael Cronenworth <mike@cchtml.com> - 1.4-1
- version update
- Initial MinGW package

* Fri Mar 11 2022 - Michael Cronenworth <mike@cchtml.com> - 1.3-1
- version update

* Sat Jan 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Tue Sep 22 2020 - Michael Cronenworth <mike@cchtml.com> - 1.2-1
- version update

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Jan 23 2019 - Michael Cronenworth <mike@cchtml.com> - 1.1-1
- version update

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed May 30 2018 - Michael Cronenworth <mike@cchtml.com> - 1.0-1
- Initial release
