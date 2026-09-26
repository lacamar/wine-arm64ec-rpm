# Handover: overnight 16K bug hunt (2026-09-26)

Companion to `HANDOVER-fable-2026-09-17.md` / `-18.md`. Everything here is committed locally;
see "Release state" at the end for what is and isn't on COPR.

## New test tools (`tools/`, `make -C tools`)

- `memtest32/64 [name-filter]` — 35 checks of 4K page semantics that a 16K host can break:
  NOACCESS/READONLY/guard neighbours, decommit/recommit zeroing, sparse commit, VirtualQuery,
  write watch, ReadFile into READONLY, stack growth/overflow, SMC in an RWX page beside an RW
  page. `MT_VERBOSE=1` prints SMC progress. Baseline (stock ec3 + FEX 2609-4): 18/35. Now 21/35.
  The remaining 14 are the host-page union (below) and cannot be fixed without emulating
  sub-page protections.
- `sehtest32/64 [rounds]` — SEH/VEH fault context precision: moffs/disp32/reg faults must report
  the faulting EIP, DIV/IDIV by zero must raise `EXCEPTION_INT_DIVIDE_BY_ZERO`.
- `shtest32/64` + `shdll32/64.dll` — cross-process `IMAGE_SCN_MEM_SHARED` sections.
- `phtest64` (not in the Makefile, needs `-D_WIN32_WINNT=0x0A00`) — placeholder splits.

Testing without touching `/usr`: overlay tree (`scratchpad/mkoverlay.sh <dir> path=src ...`).
**`wine-preloader` must be a real copy too**, otherwise `/proc/self/exe` resolves back to `/usr`
after the preloader exec and every process silently loads `/usr`'s ntdll.so (cost an hour).

## Fixed

### Wine 621 `ntdll-subpage-guard-decommit` (11.18-ec4)

1. **Guard page on a 16K host.** `get_host_page_vprot` ORs the four 4K vprots, and any
   `VPROT_GUARD` makes the whole host page `PROT_NONE`. A write to a *neighbouring* page raised
   `STATUS_GUARD_PAGE_VIOLATION` to the app (fatal without a handler) and cleared the guard.
   Now only an access to the guard page itself raises; a neighbour access disarms the host
   page's trap and retries.
2. **Decommit left stale data.** `decommit_pages` only remaps fully covered host pages; a 4K
   page sharing a host page kept its contents, so a recommit returned old data (GCs and custom
   allocators assume zero). Partial host pages are now zeroed (protection widened temporarily,
   keeping `PROT_EXEC` so concurrent native code in the page can't fault).

### Wine 622 `ntdll-unaligned-shared-sections` (11.18-ec4)

**Any DLL/EXE with a 4K-aligned `IMAGE_SCN_MEM_SHARED` section failed to load** —
`map_file_into_view: unaligned shared mapping not supported` → `STATUS_INVALID_IMAGE_FORMAT`
(error 193). Typical for hook DLLs, older games, single-instance checks. The section is now copied
privately and the host pages it fully covers are mapped shared; a FIXME names the unshared part.
`shtest`: loads now; the middle of a 64K shared section is shared, a small section is not
(it shares its host page with private sections — unfixable without per-4K mappings).

### FEX 104 `smc-untrappable-host-page` (2609-5)

**Stale code in an RWX page next to a plain RW page** (the SMC hole noted on 09-17/18). The
write trap can't take effect while a writable non-code page shares the host page. Now
`QueryExecutableRange` clips RWX ranges at host page boundaries and flags partially covered
host pages that contain untracked writable memory; blocks decoded there get the existing
`ForceFullSMCDetection` (inline CRC check per instruction). Protection changes that make a
neighbour writable invalidate the host page so older blocks are recompiled with checks.

This exposed a **pre-existing ARM64EC deadlock**: with full SMC checks (also plain
`FEX_SMCCHECKS=full` on stock FEX) the first detected change hung 64-bit apps forever.
`ThreadRemoveCodeEntryFromJit` → `InvalidateAlignedInterval` holds the code invalidation lock
while clearing lookup caches; FEX's own `VirtualFree`s reach the ARM64EC memory notification
hooks, which invalidate again → self-deadlock on the non-recursive lock. Fixed by setting
`InSyscallCallback` around it (what `ScopedCallbackDisable` does elsewhere).

### FEX 105 `precise-faults` (2609-5)

1. **Fault EIP was the block entry for absolute/relocated memory operands.** `CanHaveSideEffects`
   ignored `moffs` (A0–A3, literal operand) and all `*Relocation` operand types, so no RIP marker
   was emitted — i.e. most global-variable accesses in relocated 32-bit DLL code. Handlers that
   decode `ctx->Eip` then skip the wrong bytes.
2. **Integer divide by zero never raised.** ARM `udiv/sdiv` return 0; FEX had no check. Now
   DIV/IDIV branch to a `#DE` break on Windows hosts, mapped to `EXCEPTION_INT_DIVIDE_BY_ZERO`
   (Mono/.NET rely on the hardware trap for `DivideByZeroException`).

3. **A faulting `pop (mem)` had already moved RSP**, so a handler that skips the instruction
   returned through the wrong stack slot (Wine's `ntdll:exception` `dreg_handler` test looped
   forever in the stack). Memory destinations not addressed through RSP now load from RSP, store,
   then update RSP. (First attempt via `Pop(Size, SP)` with an RMW handle broke context
   reconstruction; the plain `_LoadMemGPRAutoTSO` version works.)

All three are upstream FEX bugs on every host, not 16K-specific.

**Regression caught and fixed before install (2609-5 → 2609-6).** The first `#DE` version reused
the divisor SSA value after `CondJump` split the block; FEX IR only allows block-local defs
(`IRValidation.cpp`: "We only allow defs local to a single block", checked in debug builds only).
In release builds some divisions silently got a garbage divisor: Lightroom crashed in
`xerces.dll+0x17f595` reading a non-canonical pointer, 3/3 runs, never on stock. Bisected with
overlay variants (ntdll-only clean, FEX-only crashing, 104-only clean, 105-without-POP and
105-without-RIP-markers crashing). Fix: the check loads its own copy of the divisor and runs
before DIV/IDIV load their operands. 2609-5 (COPR 11036433) and fex-emu-wine-git -2 (11036432)
contain the bug and are superseded by 2609-6 / git -3. `divtest` (multiplication-verified
quotients) and `sehtest`'s `div mem` case do **not** reproduce it; a 90 s Lightroom launch does.

## Found, not fixed

- **Host-page union** (memtest's remaining failures): NOACCESS/READONLY/reserved/decommitted 4K
  pages are accessible when a neighbour is more permissive; write watch reports whole host
  pages; ReadFile/WriteFile into partially protected buffers succeed; guard pages lose their trap
  after a neighbour access. Fundamental without sub-page emulation.
- **Partial `MEM_RELEASE` and placeholder splits at < 16K** fail (`unaligned partial free`,
  ntdll:virtual 2764–2810, `phtest64`). Views must start on a host page. Chromium splits at 2M,
  CoreCLR at 64K, so probably harmless.
- **FEX emulation gaps** exposed once `ntdll:exception` got past the pop fix: trap-flag single
  stepping raises nothing (1188/1247), unmasked SSE and x87 exceptions are never raised
  (1689–1781), far `ljmp`/`iret` to invalid selectors give `c000001d` and then hang (entries
  14/15). Upstream FEX limitations, not 16K.
- `ntdll:info` hangs in `test_query_process_debug_port` (debugger events under WoW64) — not 16K.
- `kernel32:virtual` reports `PAGE_READWRITE` where `PAGE_WRITECOPY` is expected for image/COW
  views (4321/4418, loader.c:1868): pages marked written at host granularity. Cosmetic.
- DS2 flicker/black screen (user report before this session): unchanged by DXVK version, float
  emulation, GPL, x87 precision; an llvmpipe comparison run is set up in its Lutris config
  (`DXVK_FILTER_DEVICE_NAME=llvmpipe`) but hasn't been done.

## Game sweep (16 titles, system wine vs overlay with all patches, display off)

`scratchpad/sweep.sh` — identical results on both, i.e. no regressions from tonight's patches.
Findings along the way:

- **Alien: Isolation** crashed in Goldberg `steam_api.dll` (+0xA6697): no `steam_interfaces.txt`
  (the 09-18 pattern). Generated it from `STEAM_API#.DLL` plus `steam_appid.txt` (214490); runs.
- **Dishonored** crashes on a worker thread reading a NULL global — `SteamAPI_Init() failed;
  unable to locate a running instance of Steam`. It uses the real Steam API; needs Steam or a
  Goldberg setup like the other games. Not a Wine bug.
- Dark Souls II SotFS, DS3, Dead Space 1/2, Limbo, DS PTDE, Signalis, Metal Garden, Nubby's,
  TBOI, The Swapper, Portal 2 all start fine. Fallout NV exits right after D3D9 init (launcher?),
  Spec Ops / Tomb Raider / Routine / DDLC produce no output (launchers / Steam checks).
- **Crysis 3's Lutris config points at a prefix that doesn't exist** (`wine-prefixes/test-crysis3`);
  the sweep created a fresh 2.5 GB prefix there at 04:01. I wasn't allowed to delete it — remove
  it by hand if you don't want it.

## Regression check (final patch set)

i386 conformance units, stock vs overlay, identical results: kernel32 heap, file, virtual,
thread, sync, time; ntdll virtual, rtl, string, sync, threadpool, wow64. Remaining failures there
are WoW64/FEX limits (LDT selectors, FPU control word, xtajit module name), not 16K. Game sweep
identical (above), tools all pass, Lightroom 90 s clean.

## Release state

Pushed to `main`. Built on COPR `wine-arm64ec`, **not installed** (the install needs the desktop
auth prompt):

| Package | Build | Contents |
|---|---|---|
| wine 11.18-ec4 | 11036430 | 621, 622 |
| wine-git 11.18^2.git.df15af3-ec.4 | 11036431 | 621, 622 |
| fex-emu-wine 2609-6 | 11036516 | 104, 105 (fixed) |
| fex-emu-wine-git 2609.1^2.git.e2f973f-3 | 11036514 | 104, 105 (fixed) |

Superseded, contain the divide-check regression: fex-emu-wine 2609-5 (11036433),
fex-emu-wine-git -2 (11036432). To install:

```
sudo dnf upgrade --refresh --allow-vendor-change --exclude=winetricks 'wine*' 'fex-emu-wine*'
```

`wine/wine-git.spec` still has your bot's uncommitted `staging_commit` bump (efba714) — left
alone; the ec.4 SRPM was built from the committed spec.
