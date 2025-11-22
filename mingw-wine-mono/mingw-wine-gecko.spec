%?mingw_package_header
# Fedora 36 change
# https://fedoraproject.org/wiki/Changes/SetBuildFlagsBuildCheck
%undefine _auto_set_build_flags

Name:           mingw-wine-gecko
Version:        2.47.4
Release:        9%{?dist}
Summary:        Gecko library required for Wine

# Automatically converted from old format: MPLv1.1 or GPLv2+ or LGPLv2+ - review is highly recommended.
License:        LicenseRef-Callaway-MPLv1.1 OR GPL-2.0-or-later OR LicenseRef-Callaway-LGPLv2+
URL:            http://wiki.winehq.org/Gecko
Source0:        http://dl.winehq.org/wine/wine-gecko/%{version}/wine-gecko-%{version}-src.tar.xz
# https://bugs.winehq.org/show_bug.cgi?id=52455
Source1:        https://github.com/libffi/libffi/releases/download/v3.4.2/libffi-3.4.2.tar.gz
# https://bugs.winehq.org/show_bug.cgi?id=52085
Patch1:       %{name}-gcc11.patch
#Patch2:       %%{name}-python311.patch
# bad hack for mingw header issue
Patch3:       %{name}-header.patch
# https://gitlab.winehq.org/wine/wine-gecko/-/merge_requests/22
Patch4:       22.patch
# https://gitlab.winehq.org/wine/wine-gecko/-/merge_requests/23
Patch5:       23.patch
# https://gitlab.winehq.org/wine/wine-gecko/-/merge_requests/30
Patch6:       30.patch
Patch7:       0001-Hacky-resolve-of-two-or-more-data-types-in-declarati.patch
Patch8:       0001-Nuke-true-false-redefinitions.patch

BuildArch:      noarch

# This project is only useful with wine, and wine doesn't support PPC.
# We will adopt the same arch support that wine does.
ExclusiveArch:  %{ix86} x86_64 aarch64

# 64
BuildRequires:  mingw64-filesystem >= 95
BuildRequires:  mingw64-binutils
BuildRequires:  mingw64-headers
BuildRequires:  mingw64-cpp
BuildRequires:  mingw64-gcc
BuildRequires:  mingw64-gcc-c++
BuildRequires:  mingw64-crt
BuildRequires:  mingw64-winpthreads-static
# 32
BuildRequires:  mingw32-filesystem >= 95
BuildRequires:  mingw32-binutils
BuildRequires:  mingw32-headers
BuildRequires:  mingw32-cpp
BuildRequires:  mingw32-gcc
BuildRequires:  mingw32-gcc-c++
BuildRequires:  mingw32-crt
BuildRequires:  mingw32-winpthreads-static

BuildRequires:  autoconf213
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  git
BuildRequires:  pkgconfig
%if 0%{?fedora} > 36
BuildRequires:  python3.10
%else
BuildRequires:  python3
%endif
BuildRequires:  perl-Getopt-Long
BuildRequires:  yasm
BuildRequires:  zip
BuildRequires:  wine-core
BuildRequires:  wine-devel

%description
Windows Gecko library required for Wine.

%package -n mingw32-wine-gecko
Summary:       Gecko library for 32bit wine
Requires:      wine-common

%description -n mingw32-wine-gecko
Windows Gecko library required for Wine.

%package -n mingw64-wine-gecko
Summary:       Gecko library for 64bit wine
Requires:      wine-common

%description -n mingw64-wine-gecko
Windows Gecko library required for Wine.

%prep
%setup -q -c -n wine-gecko-%{version}
cd wine-gecko-%{version}/
pushd js/src/ctypes/libffi
rm -rf ./*
gzip -dc %{SOURCE1} | tar -xf - --strip-components=1
popd
%patch -P 1 -p1
#patch -P 2 -p1
%patch -P 3 -p1
%patch -P 4 -p1
%patch -P 5 -p1
%patch -P 6 -p1
%patch -P 7 -p1
%patch -P 8 -p1

# fix nsprpub cross compile detection
sed -i 's,cross_compiling=.*$,cross_compiling=yes,' nsprpub/configure

# remove blank includes
rm -f media/libstagefright/ports/win32/include/pthread.h

# fix wine cabinet tool
sed -i 's,$WINE cabarc.exe -r -m mszip N $cabfile msi/files,$WINE cabarc.exe -r -m mszip N $cabfile msi/files/*,' wine/make_package

%build
cd wine-gecko-%{version}
# setup build options...
echo "mk_add_options MOZ_MAKE_FLAGS=%{_smp_mflags}" >> wine/mozconfig-common
echo "export CFLAGS=\"$CFLAGS -Wno-error=incompatible-pointer-types -Wno-error=int-conversion -DWINE_GECKO_SRC\"" >> wine/mozconfig-common

cp wine/mozconfig-common wine/mozconfig-common.build

# ... and build

%if 0%{?fedora} > 36
python3.10 -m venv env
source env/bin/activate
%endif

# Make jobserver is broken under Python 3.10
#TOOLCHAIN_PREFIX=i686-w64-mingw32- MAKEOPTS="%%{_smp_mflags}" ./wine/make_package --msi-package -win32
TOOLCHAIN_PREFIX=i686-w64-mingw32- MAKEOPTS="-j1" ./wine/make_package --msi-package -win32

#TOOLCHAIN_PREFIX=x86_64-w64-mingw32- MAKEOPTS="%%{_smp_mflags}" ./wine/make_package --msi-package -win64
TOOLCHAIN_PREFIX=x86_64-w64-mingw32- MAKEOPTS="-j1" ./wine/make_package --msi-package -win64

%install
mkdir -p %{buildroot}%{_datadir}/wine/gecko
install -p -m 0644 wine-gecko-%{version}-x86/dist/wine-gecko-%{version}-x86.msi \
   %{buildroot}%{_datadir}/wine/gecko/wine-gecko-%{version}-x86.msi
install -p -m 0644 wine-gecko-%{version}-x86_64/dist/wine-gecko-%{version}-x86_64.msi \
   %{buildroot}%{_datadir}/wine/gecko/wine-gecko-%{version}-x86_64.msi

%files -n mingw32-wine-gecko
%license wine-gecko-%{version}/LICENSE
%doc wine-gecko-%{version}/LEGAL
%doc wine-gecko-%{version}/README.txt
%{_datadir}/wine/gecko/wine-gecko-%{version}-x86.msi

%files -n mingw64-wine-gecko
%license wine-gecko-%{version}/LICENSE
%doc wine-gecko-%{version}/LEGAL
%doc wine-gecko-%{version}/README.txt
%{_datadir}/wine/gecko/wine-gecko-%{version}-x86_64.msi

%changelog
* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.4-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Tue Jul 22 2025 Frantisek Zatloukal <fzatlouk@redhat.com> - 2.47.4-8
- Build fixes

* Fri Jan 17 2025 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.4-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Mon Sep 02 2024 Miroslav Suchý <msuchy@redhat.com> - 2.47.4-6
- convert license to SPDX

* Thu Jul 18 2024 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.4-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Wed Apr 19 2023 Michael Cronenworth <mike@cchtml.com> - 2.47.4-1
- version upgrade

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Tue Oct 11 2022 Michael Cronenworth <mike@cchtml.com> - 2.47.3-1
- version upgrade

* Fri Mar 25 2022 Sandro Mani <manisandro@gmail.com> - 2.47.2-6
- Rebuild with mingw-gcc-12

* Mon Jan 24 2022 Michael Cronenworth <mike@cchtml.com> - 2.47.2-5
- Fix FTBFS (RHBZ#1987713)

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Thu Jul 22 2021 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Tue Dec 08 2020 Michael Cronenworth <mike@cchtml.com> - 2.47.2-1
- version upgrade

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.1-4
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 2.47.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Dec 30 2019 Michael Cronenworth <mike@cchtml.com> - 2.47.1-1
- version upgrade

* Thu Nov 07 2019 Michael Cronenworth <mike@cchtml.com> - 2.47-10
- Fix cabinet file creation and build options

* Fri Sep 13 2019 Michael Cronenworth <mike@cchtml.com> - 2.47-9
- Fix FTBFS (RHBZ#1675390)

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2.47-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2.47-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.47-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.47-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.47-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.47-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Nov 24 2016 Michael Cronenworth <mike@cchtml.com> - 2.47-2
- Adopt ExclusiveArch from wine package

* Fri Jul 01 2016 Michael Cronenworth <mike@cchtml.com> - 2.47-1
- version upgrade, final

* Tue May 24 2016 Michael Cronenworth <mike@cchtml.com> - 2.47-0.1
- version upgrade, beta1

* Fri Feb 05 2016 Michael Cronenworth <mike@cchtml.com> - 2.44-1
- version upgrade, final

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.44-0.2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 21 2016 Michael Cronenworth <mike@cchtml.com> - 2.44-0.1
- version upgrade, beta 1

* Fri Aug 14 2015 Michael Cronenworth <mike@cchtml.com> - 2.40-1
- version upgrade, final

* Thu Aug 06 2015 Michael Cronenworth <mike@cchtml.com> - 2.40-0.1
- version upgrade, beta 1

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.36-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Mar 06 2015 Michael Cronenworth <mike@cchtml.com> - 2.36-1
- version upgrade

* Tue Jan 06 2015 Michael Cronenworth <mike@cchtml.com> - 2.34-2
- Pass toolchain prefix during build
- Link statically to eliminate winpthreads dep (mozilla bz 1116777)

* Tue Dec 09 2014 Michael Cronenworth <mike@cchtml.com> - 2.34-1
- version upgrade

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.24-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sat Sep 28 2013 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 2.24-1
- version upgrade

* Thu Sep 12 2013 Erik van Pienbroek <epienbro@fedoraproject.org> - 2.21-4
- Fix FTBFS when winpthreads is available (Mozilla bug #893444)

* Sun Aug 18 2013 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 2.21-3
- add BR python
- build with -static-gcc (rhbz#977039)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.21-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu May 30 2013 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 2.21-1
- version upgrade

* Sat Jan 19 2013 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.9-1
- version upgrade

* Mon Oct 15 2012 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.8-1
- version upgrade

* Tue Jul 31 2012 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.7-1
- version upgrade

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jun 24 2012 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.6-1
- version upgrade

* Tue Jun 19 2012 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.5.0-3
- BR mingw{32,64}-filesystem >= 95

* Wed Mar 21 2012 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.5.0-2
- further spec cleanup

* Mon Mar 19 2012 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.5.0-1
- version upgrade
- spec cleanup

* Tue Jun 21 2011 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.2.0-3
- add suggestions from #577951c21

* Mon Jun 20 2011 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.2.0-2
- rework to mingw framework

* Fri Mar 25 2011 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.2.0-1
- version upgrade
- switch to cross framework

* Mon Mar 29 2010 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.0.0-3
- adjust path for latest wine
- requires wine-common for /usr/share/wine

* Tue Nov 24 2009 Andreas Bierfert <andreas.bierfert[AT]lowlatency.de>
- 1.0.0-2
- include version in install dir

* Tue Nov 17 2009 Erik van Pienbroek <epienbro@fedoraproject.org>
- 1.0.0-1
- Initial release
