%undefine _auto_set_build_flags
%undefine _hardened_build

%global forgeurl https://github.com/wine-mono/wine-mono
%global tag wine-mono-%{version}

Name:           wine-mono
Version:        11.3.0
Release:        1%{?dist}
Summary:        Mono library required for Wine, built with ARM64EC support

License:        GPL-2.0-or-later AND LGPL-2.1-only AND MIT AND BSD-4-Clause-UC AND MS-PL AND MPL-1.1
URL:            https://github.com/wine-mono/wine-mono

Source0:        %{forgeurl}/archive/%{tag}/%{name}-%{tag}.tar.gz

Patch0:         wine-mono-iconv.patch

%{lua:
local externals = {
  { host="github", owner="wine-mono", name="mono", ref="73610cc7350b7b51dd3bde3323a8ae28eaf5f7fc", path="mono" },
  { host="github", owner="wine-mono", name="FNA", ref="c36487f36ab67f66691132b9b178ed4ed1365d0a", path="FNA" },
  { host="github", owner="wine-mono", name="FNA.NetStub", ref="68c0af20c386bf70c298a8df9154bd22c5f0ff88", path="FNA.NetStub" },
  { host="github", owner="wine-mono", name="winforms", ref="d53511fb4bfd0b9a4e5cbfcf3f77eddcd4a8ecff", path="winforms" },
  { host="github", owner="wine-mono", name="winforms-datavisualization", ref="4e1ff0ff0529382d365e1f1632681febe04efb63", path="winforms-datavisualization" },
  { host="github", owner="wine-mono", name="wpf", ref="9178bf7cb4d5d33dfd36f0611153c9f95a337595", path="wpf" },
  { host="github", owner="wine-mono", name="monoDX", ref="7bf8e8f5ecdc6d920a89916b89db8a39d4de7279", path="monoDX" },
  { host="github", owner="wine-mono", name="monolite-binaries", ref="0938815ce68c8630b1faf21e5735258a5dfc62aa", path="monolite" },

  { host="github", owner="FNA-XNA", name="FAudio", ref="c54eb8f1223fe3b89e46ce929dbc3fd1a0601029", path="FNA/lib/FAudio" },
  { host="github", owner="FNA-XNA", name="FNA3D", ref="32401479a3ab5bd6b2e7f786e87bf4166aa03b0f", path="FNA/lib/FNA3D" },
  { host="github", owner="flibitijibibo", name="SDL2-CS", ref="1eb20e5c690aee9a5188ba9cf06207295c51d935", path="FNA/lib/SDL2-CS" },
  { host="github", owner="flibitijibibo", name="SDL3-CS", ref="9bdcf5de2af86bf764a9ca3c42821c1a099ef150", path="FNA/lib/SDL3-CS" },
  { host="github", owner="FNA-XNA", name="Theorafile", ref="3497e1a3cda1fa1ce79256f20e210fd08aec546f", path="FNA/lib/Theorafile" },
  { host="github", owner="MoonsideGames", name="dav1dfile", ref="a1377b49d6b69097357618bde87b0294e32dc313", path="FNA/lib/dav1dfile" },
  { host="github", owner="icculus", name="mojoshader", ref="6333f74dbd5644789a63e903816441b16c1e8b60", path="FNA/lib/FNA3D/MojoShader" },

  { host="gitlab", name="boringssl", ref="3e6fe145e23d0fc5e9529702fc28f70851b09af4", path="mono/external/boringssl" },
  { host="gitlab", name="bdwgc", ref="17a5cfb1e779798cd597701c5e1571fbe9571162", path="mono/external/bdwgc" },
  { host="github", owner="wine-mono", name="reference-assemblies", ref="eb33e216f039c0edc4f1406266af3ced6f44be1f", path="mono/external/binary-reference-assemblies" },
  { host="github", owner="mono", name="cecil", ref="8021f3fbe75715a1762e725594d8c00cce3679d8", path="mono/external/cecil" },
  { host="github", owner="mono", name="roslyn-binaries", ref="1c6482470cd219dcc7503259a20f26a1723f20ec", path="mono/external/roslyn-binaries" },
  { host="gitlab", name="corefx", ref="290d27ab8adb9f437ceeb82dbd0a36f01efad6ad", path="mono/external/corefx" },

  { host="github", owner="mono", name="aspnetwebstack", ref="e77b12e6cc5ed260a98447f609e887337e44e299", path="mono/external/aspnetwebstack" },
  { host="github", owner="mono", name="Newtonsoft.Json", ref="471c3e0803a9f40a0acc8aeceb31de6ff93a52c4", path="mono/external/Newtonsoft.Json" },
  { host="github", owner="mono", name="rx", ref="b29a4b0fda609e0af33ff54ed13652b6ccf0e05e", path="mono/external/rx" },
  { host="github", owner="mono", name="ikvm-fork", ref="08266ac8c0b620cc929ffaeb1f23ac37629ce825", path="mono/external/ikvm" },
  { host="github", owner="mono", name="ikdasm", ref="f0fd66ea063929ef5d51aafdb10832164835bb0f", path="mono/external/ikdasm" },
  { host="gitlab", name="NUnitLite", ref="b78250c687e8fb34327cb1ce4a44a718677a48ec", path="mono/external/nunit-lite" },
  { host="github", owner="mono", name="NuGet.BuildTasks", ref="99558479578b1d6af0f443bb411bc3520fcbae5c", path="mono/external/nuget-buildtasks" },
  { host="github", owner="mono", name="cecil", ref="33d50b874fd527118bc361d83de3d494e8bb55e1", path="mono/external/cecil-legacy" },
  { host="github", owner="mono", name="bockbuild", ref="1c3bc7a1d43557e47fbc91f38da250ab7506815e", path="mono/external/bockbuild" },
  { host="github", owner="mono", name="linker", ref="ed4a9413489aa29a70e41f94c3dac5621099f734", path="mono/external/linker" },
  { host="github", owner="mono", name="corert", ref="11136ad55767485063226be08cfbd32ed574ca43", path="mono/external/corert" },
  { host="github", owner="mono", name="xunit-binaries", ref="8f6e62e1c016dfb15420852e220e07091923734a", path="mono/external/xunit-binaries" },
  { host="gitlab", name="api-doc-tools", ref="65e455a9436c6290489e8218c10fd15c09c4c777", path="mono/external/api-doc-tools" },
  { host="github", owner="mono", name="api-snapshot", ref="dbe583ec8e5cbc384e41f2e6fd631b01658b783d", path="mono/external/api-snapshot" },
  { host="github", owner="mono", name="illinker-test-assets", ref="ec9eb51af2eb07dbe50a2724db826bf3bfb930a6", path="mono/external/illinker-test-assets" },

  { host="github", owner="Unity-Technologies", name="libatomic_ops", ref="7e44a3b8dcf457207d6394e4e52e327189155e4f", path="mono/external/bdwgc/libatomic_ops" },
}

function external_url(s)
  if s.host == "github" then
    return string.format("https://github.com/%s/%s/archive/%s.tar.gz", s.owner, s.name, s.ref)
  elseif s.host == "gitlab" then
    return string.format("https://gitlab.winehq.org/mono/%s/-/archive/%s/%s-%s.tar.gz", s.name, s.ref, s.name, s.ref)
  elseif s.host == "gitlab-sparse" then
    local slug = s.subpath:gsub("[^%w]+", "-")
    return string.format("https://gitlab.winehq.org/api/v4/projects/mono%%2F%s/repository/archive.tar.gz?sha=%s&path=%s#/%s-%s-%s-sparse.tar.gz", s.name, s.ref, s.subpath, s.name, s.ref, slug)
  end
end

for i, s in ipairs(externals) do
  si = 10 + i
  print(string.format("Source%d: %s", si, external_url(s)).."\n")
end

function print_setup_externals()
  for i, s in ipairs(externals) do
    si = 10 + i
    print(string.format("mkdir -p %s", s.path).."\n")
    print(string.format("tar -xzf %s --strip-components=1 -C %s", rpm.expand("%{SOURCE"..si.."}"), s.path).."\n")
  end
end
}

Source200:      https://github.com/mstorsjo/llvm-mingw/releases/download/20260616/llvm-mingw-20260616-ucrt-ubuntu-22.04-aarch64.tar.xz

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  pkgconfig
BuildRequires:  gettext
BuildRequires:  libgdiplus
BuildRequires:  python3
BuildRequires:  dos2unix
BuildRequires:  util-linux
BuildRequires:  wine-core
BuildRequires:  wine-devel

Requires:       wine-filesystem

%description
Windows Mono runtime required for Wine, providing the managed .NET
Framework 4.8.1-and-earlier compatible CLR that Wine's built-in mscoree.dll
loads. Built from source for aarch64 with native ARM64EC support (as well
as x86 support).

%prep
%setup -q -n %{name}-%{tag}

%{lua: print_setup_externals()}

%patch -P 0 -p1

mkdir -p llvm-mingw-20260616-ucrt-ubuntu-22.04-aarch64
tar -xJf %{SOURCE200} --strip-components=1 -C llvm-mingw-20260616-ucrt-ubuntu-22.04-aarch64
touch llvm-mingw-20260616-ucrt-ubuntu-22.04-aarch64/.dir

find . -name '*.py' -exec sed -i '1s@^#!.*python.*@#!%{__python3}@' {} +
sed -i 's/GENMDESC_PRG=python/GENMDESC_PRG=python3/' mono/mono/mini/Makefile.am.in

sed -i 's~cp -n $(IMAGEDIR)/lib/mono/4.8-api/\*.dll $(IMAGEDIR)/lib/mono/4.5/~cp -n $(IMAGEDIR)/lib/mono/4.8-api/\*.dll $(IMAGEDIR)/lib/mono/4.5/ || true~' mono.make

find . -name '*.sh' -exec dos2unix -q {} +

%build
export BTLS_CFLAGS="-fPIC"
export CPPFLAGS_FOR_BTLS="-fPIC"

export MONO_GC_PARAMS="major=marksweep"
export MONO_THREADS_SUSPEND="preemptive"

echo "PREFER_DWARF_SYMBOLS=1" > user-config.make

make -j4 image

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/wine/mono/wine-mono-%{version}/
cp -rp image/* %{buildroot}%{_datadir}/wine/mono/wine-mono-%{version}/

%files
%define debug_package %{nil}
%license COPYING
%doc README.md
%{_datadir}/wine/mono/wine-mono-%{version}/

%changelog
%autochangelog
