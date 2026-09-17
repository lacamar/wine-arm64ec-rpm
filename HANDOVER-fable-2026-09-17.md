# Handover: wine-arm64ec + FEX on Asahi, session of 2026-09-16/17

Companion to `fex-emu-wine/HANDOVER-fable.md`, which covers the original 16K-page
investigation. **That document's central open problem is now solved** — see "SMC detection"
below. Everything here is built, installed and pushed unless it says otherwise.

## Host

- Asahi Linux aarch64, **16K kernel pages** (`getconf PAGE_SIZE` = 16384)
- Compositor: **niri** (tiling, Wayland). Two outputs: `eDP-1` 1512x982@2x at logical (0,100),
  `DP-1` 1920x1080@2x at logical (1512,0).
- Installed now: `wine-11.17-ec6`, `fex-emu-wine-2609-3`, both from COPR `lacamar/wine-arm64ec`.
- Repo `~/.local/src/wine-arm64ec-rpm`, branch `main`, HEAD `d3bb1d3`, tag `wine-arm64ec-v0.1.7`.

## Working tree and tooling

Everything lives in `~/.cache/wine-arm64ec-dev/` (not in the repo):

- `full/` — RPM-equivalent source (wine 11.17 + staging + bylaws + our patches, in spec order)
- `build-full/` — configured for `arm64ec,aarch64`; `make -j8 dlls/<x>/<x>.so` then copy into `shadow/`
- `shadow/` — a complete Wine install used for testing without touching `/usr`. Run
  `shadow/bin/wine`. **Its FEX DLLs are a copy** — re-sync them from `/usr` after rebuilding
  fex-emu-wine or you will test against stale FEX (this cost an hour once).
- `orig-full/` — pristine per-file backups used to regenerate patches with `diff -u`
- `fexsrc/FEX-FEX-2609/` — FEX source with `host-page-size` + `smc-untrap-host-page` applied

Launchers: `launch.sh` (Lightroom on shadow), `lr-system.sh` (Lightroom on system wine),
`ds2.sh`/`ds2-shadow.sh`, `ds3.sh`/`ds3-shadow.sh`, `tboi.sh`. Helpers: `wkill.sh` (kills by
argv[0] — **never use bare `pkill -f <game>`, it matches and kills your own shell**),
`wshot.sh`, `wtool.exe` (`list`, `children`, `monitors`, `modes`, `click`, `vk`, `ctrlvk`,
`shift`, `redraw`, `printscan`). Test programs: `smctest32.exe`, `xtest32.exe`, `gltest2-32.exe`,
`d2dtest.exe`, `gbtest.exe` — sources alongside.

### Gotchas that will waste your time

- `niri msg action screenshot-window` **fails silently whenever niri reports no focused window**
  (`niri msg -j focused-window` → `null`). This looks exactly like a broken compositor. Focus any
  window and captures work again. Always pass an absolute `--path`.
- Screenshots go through `wshot.sh` per CLAUDE.md — never `grim` on a whole output, never
  `focus-window`, because that grabs whatever the user is actually looking at.
- `TRACE` is compiled out in these builds. Use `ERR()` for instrumentation.
- comctl32 v6 loads from `shadow/lib64/wine/aarch64-windows/comctl32_v6.dll`, **not** from the
  prefix's winsxs copy, despite what the loaddll trace says.
- `wtool printscan` cannot work cross-process: GDI handles are per-process in Wine.
- Interactive `cp`/`mv`/`rm` aliases hang background jobs — use `\cp -f`, `\mv -f`, `\rm`.
- `grep` on this host is **ugrep**: `-P`-style lookaheads and some `-E` syntax fail with
  "error at position N", and when it dies inside a pipeline it takes `make` with it (SIGPIPE) —
  send build output to a file first. `cd` also prints a directory listing (shell hook), so use
  absolute paths in one-liners.
- `make -C build-full dlls/d2d1` is a no-op ("Nothing to be done"); build the real target,
  `dlls/d2d1/aarch64-windows/d2d1.dll`, which is the ARM64X image both ARM64 and ARM64EC code load.
  The shadow's d2d1 now comes from `build-full` (pristine copy in `orig-full/d2d1-geometry.c`).
- Lightroom's main window does not always come up at the origin, so `openprefs.sh`'s menu click
  can miss. `wtool click <somewhere on the window>` then `wtool ctrlvk 188` (Ctrl+,) opens
  Preferences regardless; Cancel is at the dialog's bottom right.
- `wkill.sh` prints harmless "null byte in input" warnings from reading `/proc/*/cmdline`.
- `wtool` mouse coords are virtual-screen coords; the virtual screen now starts at y=-200, and
  `wtool` compensates. If you change monitor layout, re-check that.

## What shipped

### FEX: thread suspension of JIT threads — `fex-emu-wine-interrupt-fault-page.patch` (2609-3)

Second half of "general 16K support" after the SMC fix. `suspendtest32.exe` (source alongside)
spins a thread in `while (!stop) counter++` and calls `SuspendThread` on it from another thread.
Before this patch `SuspendThread` **never returned** on this host. Two independent causes:

1. **Fault page shared its host page.** WOW64 suspends a JIT thread by making
   `InternalThreadState::InterruptFaultPage` read-only and waiting for the JIT's block-entry
   store to fault. The page was a 4K member of a 4K-aligned struct, so under Wine's
   most-permissive-wins union the host page stayed writable. COFF caps `alignas` at 8K, so the
   fix allocates the object 16K-aligned through its own `operator new`, over-sizes the member,
   and derives the page address / JIT store offset as constants (`INTERRUPT_FAULT_PAGE_OFFSET`,
   `GetInterruptFaultPage()`). 64K hosts are explicitly not covered (store offset range).
2. **`DEF_OP(CondJump)` never emitted the suspend check for a backward true target** — only the
   pending fall-through branch got one. Any rotated `while` loop therefore never stored to the
   page at all. This is an upstream bug on every host (checked upstream `main`, still there).

Verified in isolation: with (2) alone on the original layout the test still fails on 16K; with
both, 20/20 suspend/resume cycles, worst latency 14 ms. `smctest32.exe` unaffected. ARM64EC uses
a doorbell + `brk` instead of the fault page, so 64-bit apps were never affected.

**FEX inner loop, now set up** (do not use rpmbuild to iterate): `fexsrc/FEX-FEX-2609/` has the
bundled externals unpacked and `fexsrc/llvm-mingw-20250920-.../bin` is bylaws' toolchain from the
RPM sources. `build-wow64/` and `build-arm64ec/` inside it are configured exactly like the spec;
`ninja` there is incremental (a header touch is ~5 min, a `.cpp` ~1 min). Copy `Bin/libwow64fex.dll`
/ `Bin/libarm64ecfex.dll` into `shadow/lib64/wine/aarch64-windows/`. Pristine copies of the files
this patch touches are in `fexsrc/orig-102/` (flat names). `FEX_SILENTLOG=0` makes FEX log through
`__wine_dbg_output`, so its `D`/`E` lines appear on stderr even with `WINEDEBUG=-all` — this is
how you see "Suspending thread … polling for interrupt" / "Resumed from suspend".

**Audited and left alone** (guest-semantic or already host-page-aware): `InvalidationTracker`
intervals, `CallRetStack` guards (already host-page), `JITGuardPage`, `OvercommitTracker`,
`SHMStats` (mmap of a 4K-grown file at 16K granularity is fine, page containing EOF stays
accessible), pool allocators (`IntrusiveArenaAllocator`, `atomic_segmented_bitmap_allocator`,
`memory_resource`) which only do bookkeeping at 4K, `LookupCache`/`CodeCache` (guest pages).
ARM64EC's `ResetToConsistentState` runs `HandleRWXAccessViolation` for faults from native code
too, so the handover's item 4 theory (native write into a trapped page reaching nobody) does not
hold as stated; it still needs a repro.

### FEX: SMC detection on >4K page hosts — `fex-emu-wine-smc-untrap-host-page.patch`

**This is the big one and it closes the open problem in the older handover.**

Wine applies memory protections at host-page granularity using the *union* (most permissive) of
the four 4K guest pages that share one 16K host page. FEX's SMC detection was defeated in both
directions by that:

- `ProtectRWXIntervalsInternal` re-armed the write trap over only the compiled range (often a
  few bytes), and
- `HandleRWXAccessViolation` untrapped only the faulting guest page (`TmpSize = 1`).

Either way the protection change had no effect in hardware while any neighbour in the same host
page was untrapped. Guest self-modifying writes never faulted, FEX never invalidated, and it kept
executing **stale translations** until control flow branched into memory that was never
executable — surfacing as `Unhandled page fault on execute access`.

The fix widens both the trap and the untrap to whole host pages, clipped to the RWX intervals so
nothing gains permissions the guest never requested. The existing `host-page-size` patch had
already widened the *invalidation* in that handler but left the untrap next to it at 4K.

Diagnosed with `smctest32.exe`, which patches `mov eax,imm32; ret` in place and calls it, page by
page. The signature was unmistakable:

```
page 0,1,2 after in-place patch   STALE
page 3     after in-place patch   OK
page 4,5,6 after in-place patch   STALE
page 7     after in-place patch   OK
```

Only the last 4K page of each 16K host page worked — because by then its three siblings had also
been trapped, so the union finally made the page read-only. **22/22 pass now; 10 were stale
before.** Dead Space 2 (packed 32-bit D3D9) went from dying at a fixed address every run to real
gameplay at 1920x1080 with zero page faults, **natively, no muvm**.

Keep `smctest32.exe` as the regression test for anything touching FEX protections.

### Wine patches (603–614, in `wine/`, registered in `wine-11.17.spec`)

| # | Patch | What it fixes |
|---|---|---|
| 603 | `msvcrt-idempotent-cxx-unregister` | double C++ unregister |
| 604 | `uxtheme-clip-parent-background` | parent's WM_PRINTCLIENT overwriting siblings in a shared DC |
| 605 | `winewayland-popup-subsurfaces` | popup z-order/placement, on-screen clamp, `Decorated` support, owned layered popups never managed — this is what made Lightroom's hints clickable |
| 606 | `d2d1-layers-primitive-blend` | layer push/pop + primitive blend; histogram fill and thumbnails |
| 607 | `win32u-unclamped-window-sizes` | 16-bit clamp; grid couldn't scroll past 32767px |
| 608 | `win32u-protect-paint-dc` | stale ReleaseDC killing a live paint DC (invisible themed controls) **+ the marker-leak fix, see below** |
| 609 | `winewayland-follow-host-color-scheme` | mirrors the XDG portal `color-scheme` into `Themes\Personalize` |
| 610 | `win32u-monitor-physical-position` | **big one:** single-mode sources lost their position, collapsing every non-primary monitor onto the origin |
| 611 | `comctl32-groupbox-caption-row` | stale pixels beside themed group box titles |
| 612 | `win32u-vulkan-swapchain-pnext` | Wine replaced the app's swapchain `pNext` chain instead of prepending, discarding DXVK's `VkSwapchainPresentModesCreateInfoEXT` and crashing the host Vulkan driver |
| 613 | `winewayland-primary-output` | `PrimaryOutput` setting to choose the Win32 primary monitor |
| 614 | `winewayland-decorations-default` | decoration default follows the compositor |
| 615 | `d2d1-collinear-outline-join` | **histogram fragments:** 25-unit stub emitted for collinear stroke joins |

Two of these deserve detail because they are non-obvious:

**610 — monitor positions.** `add_modes()` builds a source's "physical" mode from the mode list
when there is exactly one mode, which is *always* the case on Wayland, and that mode carries no
position. So DP-1 was reported at `(0,0)-(3840,2160)` instead of `(3024,-200)-(6864,1960)` and the
virtual screen shrank to one display. Lightroom read that and parked its photo grid 3024px
off-screen — which presented as "thumbnails disappear at large zoom". Two lines to carry
`current->dmPosition` across.

**614 — decorations.** `X11 Driver\Decorated` is winecfg's "Allow the window manager to decorate
the windows" checkbox (Graphics tab), and winecfg shows it **ticked** when the value is absent.
The Wayland driver treated absent as N, so a fresh prefix read as "the WM decorates" while Wine
still drew its own frame, and the only way to turn the frame off was to untick and re-tick. Now
an absent value means *follow the compositor*: note whether `zxdg_decoration_manager_v1` is
advertised and hide the Win32 frame only if it is. niri advertises it, so a fresh prefix gets no
Wine caption; an explicit Y or N still wins. Verified on Lightroom's main window and its
Preferences dialog.

**608's second half, found on the last pass.** The guard marks a DCE `in_paint` in `BeginPaint`
and only clears it on a successful release — but the guard *refuses* releases, so a paint whose
`EndPaint` never came left the marker stuck and the DCE pinned at `count == 1` forever. Every
later user of that recycled cache DCE then failed to release it. Lightroom showed 13 per session
as `wined3d_release_dc Failed to release device context`, all `ReleaseDC(NULL, hdc)`. Fixed by
clearing the marker in `NtUserGetDCEx` where the DCE is handed out. **13 → 0.**

### Settings worth knowing

```
# choose the Win32 primary monitor (else the output at the origin wins)
wine reg add 'HKCU\Software\Wine\Wayland Driver' /v PrimaryOutput /t REG_SZ /d DP-1 /f

# force Wine to draw its own frame again (default now follows the compositor)
wine reg add 'HKCU\Software\Wine\X11 Driver' /v Decorated /t REG_SZ /d N /f

# opt out of host light/dark following
wine reg add 'HKCU\Software\Wine\Wayland Driver' /v FollowSystemColorScheme /t REG_SZ /d N /f
```

## Open problems

**1. Histogram stroke fragments — SOLVED (615, session 2 of 2026-09-17).** It was never the
ignored stroke style. `d2d_geometry_outline_add_join` special-cases an exactly collinear join
(cross product 0) by emitting a 25-geometry-unit rectangle from the vertex along the tangent —
presumably to dodge the undefined mitre there. On a thin polyline with runs of equal slope the
next segment is shorter than 25 units, so the stub pokes out as a stray tangent fragment; the
reversal case leaves a stub past the turning point. The fix emits nothing for that case: the
segment quads already cover what a bevel would. `stroketest.exe` (source alongside) reproduces
it with collinear runs, a reversal, and a histogram-like polyline; compare `stroke1.png` (before)
and `stroke2.png` (after), and `hist-fix.png` for the real histogram. The stroke-style FIXME is
still there and still harmless for Lightroom (it only wants solid lines). **Follow-up worth
knowing:** Wine has no mitre limit at all, so a near-reversal (sharp spike) gets a full mitre of
length ½w/sin(½θ) where D2D would bevel past miterLimit 10. Not visible in Lightroom.

**2. The Binding of Isaac renders black** (Lutris 127, 32-bit OpenGL). Reaches its main menu at
60 FPS but presents nothing. Mesa reports `glUniformMatrix(program not linked)` and
`GL_INVALID_VALUE in glUseProgram`; a `+opengl` trace shows `glUseProgram(-1)` continuously and
only **3** GL programs created for ~20 shader effects. Each effect aborts at
`Failed to load vertex shader shaders/<name>.vs` — and the archives genuinely ship only 4 vertex
shaders against 20 fragment shaders. **Not a Wine bug as far as I got**: a purpose-built 32-bit GL
test (shaders, VBO/VAO, FBO, `glBlitFramebuffer`) through the same WoW64/FEX path renders
correctly. Unchanged by the FEX SMC fix, so it is a separate defect. Next: compare against a
known-good install / Steam file verification, and check whether the `.unpacked.exe` modding setup
is meant to supply the missing vertex shaders.

**3. Dark Souls III blocked on Steam** (Lutris 129, 64-bit). Patch 612 fixed the Vulkan crash that
killed it at startup; it now creates its window, then faults in `steam_api64.dll` +0xBCC74 reading
`0x605` because the Steam client is not running. `steam_appid.txt` does not help — tried. Steam is
installed at `/usr/bin/steam`; I did not launch it because it takes over the user's session.
Not a Wine bug.

**4. Lightroom CEF subprocess dies in Secur32 init (intermittent).** A helper process loading
`libcef.dll`/`chrome_elf.dll` aborts with `"Secur32.dll" failed to initialize` / `c0000005`, raising
a "Wine C++ Runtime Library" dialog. The fault is a **write** to `Secur32.dll+0x34378` from
`ucrtbase.dll+0xFB67C`, immediately after Adobe's `substrate.dll` (a function-hooking library)
loads — so it looks like a detour patching Secur32 and hitting a non-writable page. Seen once,
did not recur across three later launches. **Worth checking against the FEX SMC change**: the
widened traps now actually take effect, so a page that *native* ARM64EC code writes to could fault
where the fault would not reach FEX's emulated-code handler. Unproven; get a repro first.

**5. Preferences after the 608 marker-leak fix — VERIFIED.** Checkboxes, group boxes and
captions all render; no stray pixels beside group titles (`pref-verify.png`).

**6. Lower priority.** `d2d_gradient_create Ignoring gamma`; `NtUserGetPointerInfoList Pointer type
0x3` (PT_PEN — matters for tablet input in a photo editor); `wined3d_guess_card` cannot identify the
Apple GPU (vendor 0000) so DXGI reports a GeForce GTX 470, and `d3d12_get_vk_physical_device` then
cannot match the DXGI adapter to a Vulkan device. That last pair might matter for GPU acceleration
and is probably the most interesting thread here. The `err:trackbar/header/listview unknown msg
0663/0664` spam is an app-private broadcast — noise, ignore it.

## Release workflow

Per the user's CLAUDE.md, offer once; do not run unprompted. COPR project is `wine-arm64ec`
(user `lacamar`, already authenticated). Tags follow `wine-arm64ec-vX.Y.Z` — currently `v0.1.7`.

```
rpmbuild -bs ~/rpmbuild/SPECS/wine-11.17.spec
copr-cli build wine-arm64ec ~/rpmbuild/SRPMS/wine-11.17-ecN.fc44.src.rpm
sudo dnf upgrade --refresh --allow-vendor-change --exclude=winetricks 'wine*'
```

Notes: bump `Release:` (`ecN`) or dnf cannot upgrade. `--allow-vendor-change` is required because
some installed wine packages have vendor `(none)` from an older local build. `~/rpmbuild/SOURCES`
must be populated from Fedora's wine SRPM first (`dnf download --source wine`, `rpm -ivh`) since
the spec uses Fedora's `wine-cjk.patch` and desktop files, then copy `wine/*.patch` over the top.
The FEX build additionally needs `catch2-devel` and `xxhash-devel`.
