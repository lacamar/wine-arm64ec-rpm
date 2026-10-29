# wine-arm64ec-rpm

- Each package dir has `<name>.spec` (latest upstream release) and `<name>-git.spec` (HEAD). Patches shared by both are unversioned; a release-only variant carries the version suffix (e.g. `-11.20.patch`). No git tags.
- Bump: `tools/bump <spec>` (version/commit, staging, bundled submodule refs, changelog). Check: `tools/precheck <spec>` (pre-push runs it). Release via the wine-arm64ec-release skill.
- CI: `ci/run --spec <spec>` A/B-tests a bump against the shipped COPR build on this 16K host (stages in `ci/stages/`, results in `$XDG_STATE_HOME/wine-arm64ec-ci/`). Every Wine run must use a headless sway `WAYLAND_DISPLAY`, never the desktop's.
- arch/: -git PKGBUILDs that read commits/patches from the RPM -git specs (`arch/spec.sh`).
- Game tests: `gt` and helpers in `~/.local/src/wine-arm64ec-tools/gametest/` (wine-game-testing skill).
- Mesa (Asahi/HK patches): `~/.local/src/arm64-misc/specfiles/mesa-git/`, COPR arm64-misc.
