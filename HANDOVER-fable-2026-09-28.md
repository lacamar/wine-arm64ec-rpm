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

## 2026-09-29: what the sweep data says about 16K

Instrumented overlay builds (logging only, nothing installed): Wine `ntdll.so` logs every host page whose
4K pages want different protections (`HP16 mixed ctx=… extra=W/X/R`), sub-host-page decommits and
images with sub-16K section alignment; FEX logs SMC write faults. Scripts: `tools/gametest/` +
scratch `hp16run.sh`/`perfrun.sh` (60 s per game, CPU seconds via `/usr/bin/time`, ~10 % run noise).

### Fixed: thread suspension regressed in fex-emu-wine-git (Release 4)

`fex-emu-wine-interrupt-fault-page.patch` (2609 Patch102) was never carried to the git spec. Upstream
has since moved WOW64 to the doorbell, so only its `CondJump` back-edge hunk still matters, and it
matters on both WOW64 and ARM64EC: without it `SuspendThread` on a thread spinning in a rotated loop
never returns (`suspendtest32/64` hung on the installed build). New
`fex-emu-wine-git-suspend-backedge.patch`: 20/20 cycles, worst 7–8 ms, both bitnesses; smctest32
22/22; Lightroom clean. Psychopomp still hangs, so that is not its cause.

### Measured, not shipped: SMC fault storms on 16K

FEX write-protects code at host-page granularity, so data writes into the other 4K pages of a host
page fault, invalidate the whole host page and wipe the 4 MB call-ret stack
(`VirtualDontNeed` decommit+recommit, ~300/s in Dead Space 2). Per minute: DS3 ~24k faults, DS2 SotFS
~37k (Arxan exes, a few hundred 4K pages each faulting thousands of times), Dead Space 2 ~12k (256
heap pages, slow rate), Dishonored ~500 (one page).

`fex-emu-wine/fex-emu-wine-git-smc-notrap-hot-pages.patch` (not in the spec): after 32 write faults
within 1 s a host page stays writable and its code is compiled with full SMC checks. Faults −85 %
(DS3), −93 % (DS2 SotFS); CPU unchanged on DS3, −11 % on DS2 SotFS, +4 % on Dishonored (its one hot
page flips during a burst). Menu scenes at a 60 fps cap only — needs a gameplay/stutter test before it
is worth shipping.

### Other observations

- Wine heap decommits are 64K-aligned; the frequent `base+0x1000 / 0xf000` and 4 MB decommits are FEX
  `VirtualDontNeed`, each going through the sub-host-page zeroing path of patch 621.
- 60 of 74 sub-16K-aligned images in Dishonored are Wine's own i386 DLLs (ntdll, libwow64fex …): their
  code pages end up writable. Only a W^X hardening issue — FEX does not SMC-track non-RWX code.
- Mixed pages are common everywhere (2–8k per minute per game) but mostly benign unions of
  committed/uncommitted neighbours.
