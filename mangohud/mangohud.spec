%global appname MangoHud
%global forgeurl https://github.com/flightlessmango/MangoHud

%global imgui_ver 1.91.6
%global imgui_wrap_ver 2
%global vulkan_headers_ver 1.3.283
%global vulkan_headers_wrap_ver 2
%global implot_ver 0.16
%global implot_wrap_ver 2

%global tarball_version %%(echo %{version} | tr '~' '-')

# TODO: try to fix amdgpu tests
%bcond_with tests

Name:           mangohud
Version:        0.8.3~rc1
%forgemeta
Release:        3.ec1%{?dist}
Summary:        Vulkan and OpenGL overlay for monitoring FPS, temperatures, CPU/GPU load

License:        MIT
URL:            %{forgeurl}
Source0:        %{url}/archive/v%{tarball_version}/%{name}-%{tarball_version}.tar.gz
# imgui
Source1:        https://github.com/ocornut/imgui/archive/v%{imgui_ver}/imgui-%{imgui_ver}.tar.gz
Source2:        https://wrapdb.mesonbuild.com/v%{imgui_wrap_ver}/imgui_%{imgui_ver}-1/get_patch#/imgui-%{imgui_ver}-wrap.zip
# Vulkan-Headers
Source3:        https://github.com/KhronosGroup/Vulkan-Headers/archive/v%{vulkan_headers_ver}/Vulkan-Headers-%{vulkan_headers_ver}.tar.gz
Source4:        https://wrapdb.mesonbuild.com/v%{vulkan_headers_wrap_ver}/vulkan-headers_%{vulkan_headers_ver}-1/get_patch#/vulkan-headers-%{vulkan_headers_ver}-wrap.zip
# implot
Source5:        https://github.com/epezent/implot/archive/v%{implot_ver}/implot-%{implot_ver}.tar.gz
Source6:        https://wrapdb.mesonbuild.com/v%{implot_wrap_ver}/implot_%{implot_ver}-1/get_patch#/implot-%{implot_ver}-wrap.zip
Source20:       README.Fedora.md

Patch100:       mangohud-align-right.patch

# MangoHud switched to bundled vulkan-headers since 0.6.9 version. This rebased
# upstream patch which reverts this change.
# https://github.com/flightlessmango/MangoHud/commit/bc282cf300ed5b6831177cf3e6753bc20f48e942
# Patch0:         mangohud-0.6.9-use-system-vulkan-headers.patch

BuildRequires:  vulkan-headers
BuildRequires:  appstream
BuildRequires:  dbus-devel
BuildRequires:  gcc-c++
BuildRequires:  git-core
BuildRequires:  libappstream-glib
BuildRequires:  libstdc++-static
BuildRequires:  meson >= 0.60
BuildRequires:  python3-mako
BuildRequires:  pkgconfig(dri)
BuildRequires:  pkgconfig(glfw3)
BuildRequires:  pkgconfig(glslang)
BuildRequires:  pkgconfig(nlohmann_json)
BuildRequires:  pkgconfig(spdlog)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xkbcommon)
# Tip and memo if upstream decide to unbundle vulkan-headers
# BuildRequires:  pkgconfig(vulkan) < 1.3.241


%if %{with tests}
BuildRequires:  libcmocka-devel
%endif

Requires:       hicolor-icon-theme
Requires:       vulkan-loader%{?_isa}

Recommends:     (mangohud(x86-32) if glibc(x86-32))

Suggests:       %{name}-mangoplot
Suggests:       goverlay

Provides:       bundled(imgui) = %{imgui_ver}
Provides:       bundled(vulkan-headers) = %{vulkan_headers_ver}

%global _description %{expand:
A Vulkan and OpenGL overlay for monitoring FPS, temperatures, CPU/GPU load and
more.}

%description %{_description}


%package        mangoplot
Summary:        Local visualization "mangoplot" for %{name}
BuildArch:      noarch

Requires:       %{name} = %{version}-%{release}
Requires:       python3-matplotlib
Requires:       python3-numpy

%description    mangoplot
Local visualization "mangoplot" for %{name}.


%prep
%autosetup -n %{appname}-%{tarball_version} -p1
%setup -qn %{appname}-%{tarball_version} -D -T -a1
%setup -qn %{appname}-%{tarball_version} -D -T -a2
%setup -qn %{appname}-%{tarball_version} -D -T -a3
%setup -qn %{appname}-%{tarball_version} -D -T -a4
%setup -qn %{appname}-%{tarball_version} -D -T -a5
%setup -qn %{appname}-%{tarball_version} -D -T -a6

# imgui
mv imgui-%{imgui_ver} subprojects/
# Vulkan-Headers
mv Vulkan-Headers-%{vulkan_headers_ver} subprojects/
# implot
mv implot-%{implot_ver} subprojects/

%if %{with tests}
# Use system cmocka instead of subproject
# https://gitlab.archlinux.org/archlinux/packaging/packages/mangohud/-/blob/0.6.9.1-10/PKGBUILD?ref_type=tags#L32
sed -i "s/  cmocka = subproject('cmocka')//g" meson.build
sed -i "s/cmocka_dep = cmocka.get_variable('cmocka_dep')/cmocka_dep = dependency('cmocka')/g" meson.build
%endif


%build
%meson \
    -Dmangoapp=true \
    -Dmangohudctl=true \
    -Dinclude_doc=true \
    -Duse_system_spdlog=enabled \
    -Dwith_wayland=enabled \
    -Dwith_xnvctrl=disabled \
    %if %{with tests}
    -Dtests=enabled \
    %else
    -Dtests=disabled \
    %endif
    %{nil}
%meson_build


%install
%meson_install

# ERROR: ambiguous python shebang
sed -i "s@#!/usr/bin/env python@#!/usr/bin/python3@" \
    %{buildroot}%{_bindir}/mangoplot

# Install Fedora docs
install -D -p -m 0644 %{SOURCE20} %{buildroot}%{_docdir}/%{name}/README.Fedora.md

rm %{buildroot}%{_libdir}/libimgui.a


%check
# https://github.com/flightlessmango/MangoHud/issues/812
# ? tag-invalid           : stock icon is not valid [io.github.flightlessmango.mangohud]
%dnl appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.xml
%if %{with tests}
%meson_test
%endif


%files
%license LICENSE
%doc README.md presets.conf.example README.Fedora.md
%{_bindir}/mangoapp
%{_bindir}/mangohud
%{_bindir}/mangohudctl
%{_datadir}/icons/hicolor/scalable/*/*.svg
%{_datadir}/vulkan/implicit_layer.d/*Mango*.json
%{_docdir}/%{name}/%{appname}.conf.example
%{_libdir}/%{name}/
%{_mandir}/man1/%{name}.1*
%{_mandir}/man1/mangoapp.1*
%{_metainfodir}/*.metainfo.xml

%files mangoplot
%{_bindir}/mangoplot


%changelog
* Wed Sep 30 2026 Lachlan Marie <lchlnm@pm.me> - 0.8.3~rc1-3.ec1
- Add align_right option
- Add resolution_color option
- Add {RRGGBB} colour markup for custom_text and exec

* Fri Jan 23 2026 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.3~rc1-2
- Chores

* Fri Jan 23 2026 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.3~rc1-1
- 0.8.3~rc1

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 0.8.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Thu Dec 11 2025 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.2-2
- build: Remove glew dep

* Thu Dec 11 2025 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.2-1
- chore: Update to 0.8.2

* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.8.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sat Mar 15 2025 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.1-2
- build: Build with libstdc++-static rh#2352676

* Wed Mar 05 2025 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.1-1
- chore: Update to 0.8.1

* Wed Feb 12 2025 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.0-2
- build: Upload all sources

* Wed Feb 12 2025 Artem Polishchuk <ego.cordatus@gmail.com> - 0.8.0-1
- chore: Update to 0.8.0

* Fri Jan 17 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Tue Nov 26 2024 František Zatloukal <fzatlouk@redhat.com> - 0.7.2-4
- Rebuilt for spdlog 1.15.0

* Thu Jul 18 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Sun May 26 2024 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.2-2
- docs: Add README.Fedora.md

* Sun May 26 2024 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.2-1
- build: Update to 0.7.2

* Tue May 21 2024 František Zatloukal <fzatlouk@redhat.com> - 0.7.1-4
- Rebuilt for spdlog 1.14.1

* Sat Mar 02 2024 Neal Gompa <ngompa@fedoraproject.org> - 0.7.1-3
- Build mangoapp to support mangohud in gamescope

* Thu Feb 08 2024 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.1-2
- packit: Update config

* Wed Feb 07 2024 Packit <hello@packit.dev> - 0.7.1-1
- [packit] 0.7.1 upstream release
- Resolves rhbz#2263209

* Wed Feb 07 2024 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-12
- packit: Update config

* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.0-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.0-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Oct 08 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-9
- packit: Add upstream_tag_template: v{version}

* Fri Oct 06 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-8
- build: Add Packit config

* Fri Oct 06 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-7
- build: Use forge macros

* Mon Oct 02 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-6
- build: Fix description about 'mangoplot'

* Mon Oct 02 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-5
- build: mangohud-mangoplot as Suggests

* Thu Sep 28 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-4
- build: Add missed deps for mangoplot

* Thu Sep 28 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-3
- build: Package mangoplot as separate sub-package

* Thu Sep 28 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-2
- build: Upload sources

* Thu Sep 28 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.7.0-1
- build: Update to 0.7.0

* Sun Sep 10 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-11
- build: Backport upstream patch

* Sun Sep 10 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-10
- test: Skip for s390x arch

* Sun Sep 10 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-9
- build: Drop BR: pkgconfig(vulkan)

* Sun Sep 10 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-8
- test: Fix and enable tests

* Sun Sep 10 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-7
- style: Minor Spec file update

* Sun Sep 10 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-6
- build: Bundle vulkan-headers to fix FTBFS

* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.9.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Tue Jul 11 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-4
- build: mangohud relies on old Vulkan-headers < 1.3.241

* Sat Jul 08 2023 Vitaly Zaitsev <vitaly@easycoding.org> - 0.6.9.1-3
- Rebuilt due to spdlog 1.12 update.

* Wed Jun 28 2023 Vitaly Zaitsev <vitaly@easycoding.org> - 0.6.9.1-2
- Rebuilt due to fmt 10 update.

* Wed Apr 19 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9.1-1
- build: Update to 0.6.9-1

* Fri Apr 14 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.9-1
- build: Update to 0.6.9

* Tue Mar 14 2023 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.8-4
- build: Fix FTBFS 38

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Thu Nov 03 2022 Vitaly Zaitsev <vitaly@easycoding.org> - 0.6.8-2
- Rebuilt due to spdlog update.

* Tue Aug 02 2022 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.8-1
- chore(update): 0.6.8

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.7.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Tue Jul 19 2022 Mamoru TASAKA <mtasaka@fedoraproject.org> - 0.6.7.1-3
- Rebuild for fmt-9

* Fri May 13 2022 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.7.1-2
- fix: Upload sources

* Fri May 13 2022 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.7.1-1
- chore(update): 0.6.7-1

* Wed May 04 2022 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.7-1
- chore(update): 0.6.7

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Mon Oct 18 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.6-1
- chore(update): 0.6.6

* Thu Oct 07 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.5-3
- build: Fix multilib dep | rh#1830718

* Thu Jul 22 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Thu Jul 08 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.5-1
- build(update): 0.6.5

* Thu Jun 24 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.4-1
- build(update): 0.6.4

* Sat Jun 12 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.3-1
- build(update): 0.6.3

* Fri Jun 11 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.2-1
- build(update): 0.6.2

* Wed Jan 27 2021 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.1-3
- build: Install 32-bit version automagically if multilib packages already
  installed on end user machine

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sun Nov 29 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.1-1
- build(update): 0.6.1

* Sun Nov 29 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.0-2
- fix: version in HUD | GH-411

* Sat Nov 28 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.6.0-1
- build(update): 0.6.0

* Sun Aug 16 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.5.1-1
- Update to 0.5.1

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sat Jun 13 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.4.1-2
- Add patch which fix F33 build | GH-213

* Thu Jun 11 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.4.1-1
- Update to 0.4.1
- Disable LTO

* Sat May 02 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.3.5-1
- Update to 0.3.5
- Remove ExclusiveArch. Now compiles on all arches, see GitHub#88.

* Thu Mar 26 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.3.1-2
- Add GUI fron-end 'goverlay' as very weak dep

* Wed Mar 18 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.3.1-1
- Update to 0.3.1

* Sun Mar 15 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.3.0-1
- Update to 0.3.0

* Fri Feb 14 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0.2.0-11
- Initial package
- Thanks for help with packaging to:
  gasinvein <gasinvein@gmail.com>
  Vitaly Zaitsev <vitaly@easycoding.org>

