# Handover 2026-09-28 — wine-git 4e819f0 + fex-emu-wine-git, full Steam library sweep

## Installed

- wine-git 11.18^3.git.4e819f0-ec.1 (COPR 11042264), fex-emu-wine-git 2609.1^3.git.59f85d6-3.
- Swapped in for wine 11.18-ec4 / fex-emu-wine 2609-6 (`dnf install --allowerasing`); wine-dxvk and
  wine-vkd3d-proton stayed. To go back: `sudo dnf install --allowerasing wine fex-emu-wine`.

## Regression checks on wine-git

- tools: memtest 21/35 (same known 16K limits), sehtest/divtest/poptest/smctest all pass, shtest as before.
- Lightroom 90 s ×2 in `lightroom_test`: clean.

## Game sweep

32 `<game>-test-claude` Lutris entries, one prefix each under `~/.local/share/wine-prefixes/`, run
headless in a nested sway (`tools/gametest/`). Steam API: Valve DLL kept as `steam_api#.dll` /
`steam_api64#.dll`, GBE copied in, `steam_interfaces.txt` + `steam_appid.txt` added, in:
Balatro, Crysis 2/3 Remastered, DXHR Missing Link, Dishonored, Fallout NV, NaissanceE,
Nubby's Number Factory, Portal 2, Psychopomp, Slay the Princess, Binding of Isaac, Tomb Raider.

Run fine (40+ frames in 60 s, no faults): Alien Isolation, Balatro, Crysis 3 R, DS3, DS2 SotFS,
Dead Space, Dead Space 2, Dishonored (now works via GBE), DDLC, Elden Ring, Limbo, Nubby's,
Prison of Husks demo, Portal 2, Road to Vostok (+demo), Routine (shipping exe), SIGNALIS,
Slay the Princess, Isaac, The Swapper.

Waiting on a launcher/first-run dialog (not bugs): Tomb Raider, DXHR, DXHR ML (settings launchers),
NaissanceE (UDK EULA).

Not Wine/FEX:
- **Amnesia Rebirth / The Bunker**: `FATAL ERROR: Could not load vertex buffer from mesh
  'core_box.msh'`. The 44 `core/models/*.msh` were regenerated 2026-09-02 from `.dae` as MSH v7; the
  games want v8 (every other mesh is v8). Same date as the OpenHplRebirth work. Verify files in Steam.
- **Spec Ops**: Steam CEG (`.STEAMSTART` files), exit 173; same on stock.
- **Fallout NV**: exits 0 without a frame; same on stock in the 11.17 prefix.
- **DS PTDE**: null read at 0x77F36989 in a fresh prefix; works in `dsptde` (has the DirectX redist
  cab DLLs). Prefix setup.
- **Crysis 2 R**: uncaught C++ exception (0x20474343) right after loading builtin d3d12 during adapter
  enumeration; Crysis 3 R is fine. Not investigated further.
- **Routine.exe** bootstrapper keeps asking for the VC++ runtime even when it is registered; the
  shipping exe runs.
- FEZ, Terraria: Linux FNA builds, dropped. Mirror's Edge: Steamless 3.1.0.5 crashes on its
  SteamStub 2.1 (Step 5), no unpacked exe, not tested.

## Found, not fixed: Psychopomp (.NET 8 CoreCLR, Godot 4.2 mono) hangs at startup

- Main thread at 100 % CPU right after `coreclr.dll`/`clrjit.dll` load, 1 frame presented.
- The endless SIGSEGVs are FEX's call-ret stack guard (x17 underflow → reset in
  `CallRetStack::HandleAccessViolation`), i.e. guest code looping through calls, not a memory bug.
- Pre-existing: same with pre-621/622 ntdll.so (built from this wine-git tree) and with FEX 2609-4.
- `DOTNET_ReadyToRun=0` gets past `hostfxr initialized` but still stalls; HWIntrinsic/AVX/tiering knobs
  change nothing. Next step: find the guest RIP of the loop (winedbg attach hangs; gdb only sees JIT
  code).

## Housekeeping

- Leftover test prefixes you may delete: `fez-test-claude`, `terraria-test-claude`, and still
  `test-crysis3` from the 09-26 sweep.
- `wine/wine-git.spec` now pins wine 4e819f0 (the bot bumped staging to cc193df, which targets it).
