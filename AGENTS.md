# wine-arm64ec-rpm

- Spec changes: `tools/precheck wine/<spec>` before COPR (pre-push runs it); release via the wine-arm64ec-release skill. No git tags.
- Game tests: `gt` and helpers in `~/.local/src/wine-arm64ec-tools/gametest/` (wine-game-testing skill).
- Mesa (Asahi/HK patches): `~/.local/src/arm64-misc/specfiles/mesa-git/`, COPR arm64-misc.
- Local spec sources (desktop files, configs, extra patches) live next to the spec in `wine/`.
