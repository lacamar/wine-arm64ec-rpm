# Lutris installers

Tested on Fedora Asahi Remix (Apple Silicon).

```
lutris -i dark-souls-iii.yml
```

- Installs/upgrades the tested packages from COPR `lacamar/arm64-misc` and `lacamar/wine-arm64ec` (polkit prompt). Replaces Fedora `wine` with `wine-git` and Asahi Mesa with mesa-git.
- Asks for the game's exe; the prefix goes in the install dir.
- Steam games: Steam in the prefix, or Steamless + Goldberg. Not automated.
- Ratings and per-game notes are shown by the installer.
- Regenerate after a package bump: edit `PACKAGES` in `mk.py`, run it.
