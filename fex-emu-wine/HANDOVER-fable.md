# Handover: running Lightroom under wine-arm64ec + FEX on a 16K-page host

## Why this matters

The goal is to run Adobe Lightroom Classic (a 64-bit x64 Windows binary) on Asahi Linux
through **wine-arm64ec + fex-emu-wine only**. Upstream FEX-Emu's answer to this problem is
"run it inside muvm" — a KVM microVM with a 4K-page guest kernel. That answer is rejected
here: the whole point is to make it work natively, without a VM layer. box64 is also out —
upstream documents it as specifically broken with wine.

So this is deliberately unsupported territory. Upstream has declined general non-4K host
support for years (FEX-Emu/FEX issues #1921, #3496, and as recently as May 2026 #5517:
*"FEX doesn't support 16KB page size kernels"*). Any fix is out-of-tree and we are authoring it.

## The host

- Asahi Linux aarch64, **16K kernel pages** (`getconf PAGE_SIZE` = 16384), kernel `7.1.9-3.fairydust.fc44.aarch64+16k`
- wine-staging `11.17-ec1` (ARM64EC), `fex-emu-wine-2609`
- FEX's ARM64EC/WOW64 path is the one in play: `libarm64ecfex.dll` / `libwow64fex.dll`
  under `/usr/lib64/wine/aarch64-windows/`, with unix-side `.so` counterparts in `aarch64-unix/`.

## Where things stand

A patch is **written, built, installed, and verified present in the shipped binaries**. It did
not fix the problem, but it did change the failure mode. Details below, including the parts
that are unverified — please treat the unverified parts as genuinely open.

### What the patch does

`fex-emu-wine-host-page-size.patch` (15 files, applies cleanly to FEX tag `FEX-2609` =
`395b132f346b1a45def246d10c52245edba1ef02`).

FEX hardcodes `FEX_PAGE_SIZE = 4096` in `FEXCore/include/FEXCore/Utils/TypeDefines.h` and uses
it for two different things that only coincide on a 4K host: **guest page semantics** (correct at
4096 regardless of host — it's the x86 ISA page size, and it's baked into the on-disk code-cache
format) and **real host mprotect/VirtualAlloc boundaries** (wrong at 4096 on a 16K host).

The patch adds a runtime `FEXCore::Utils::GetHostPageSize()` — `sysconf(_SC_PAGESIZE)`, cached,
plumbed into the mingw-built WOW64/ARM64EC DLLs through a new wine unix-call appended to
`FEXUnixLib` plus a new `HookPtrs::GetHostPageSize` — and switches only the second category of
call site to it: the JIT code-buffer guard page (`SharedCodeBufferManager`), the pooled-allocator
guard (`ThreadPoolAllocator.h`), the host-protection boundaries in
`Source/Windows/Common/InvalidationTracker.cpp`, and the ARM64EC `X64ReturnInstr` trampoline.
Guest-semantic bookkeeping was deliberately left at 4096, with comments saying why.

The theory behind it: a 4K "guard page" that is supposed to sit alone on a real page so a
deliberate access faults will, on a 16K host, share its real page with live differently-protected
memory — so the intended fault never fires and corruption goes undetected.

### What is NOT done, and is the most likely remaining hole

**`InternalThreadState::InterruptFaultPage` was not relocated.** Its offset from `BaseFrameState`
is baked as an immediate into JIT-generated machine code (`Dispatcher.cpp:280`, `JIT.cpp:771`;
the `<= 65520` static_assert matches AArch64's scaled 12-bit immediate limit). Because the struct
is rpmalloc-allocated with only 4096-byte alignment guaranteed, this trap page will frequently
share a real 16K page with other live `InternalThreadState` fields — which defeats the
cooperative thread-interrupt mechanism the same way the guard pages were defeated. Fixing it
properly means pulling the page out into its own `VirtualAlloc`'d region and changing how the
JIT addresses it. That was judged too risky to guess at without reading the codegen carefully,
so it was left alone deliberately rather than half-done.

`Source/Windows/Common/CallRetStack.h` is the same risk class and is also untouched.

### What changed when the patch went in

**Before:** a flood of `EXCEPTION_ACCESS_VIOLATION` at `rip=0x140BE8F07` (that's
`Lightroom.exe` base `0x140000000` + `0xBE8F07`, i.e. inside the app's own emulated x64 code)
faulting on `0x00007FFFFEAD4000`, then a cascade of uncaught C++ exceptions (`std::bad_alloc`,
`SPLException`) with "no matching catch block found", ending in `raise(22)` — CRT SIGABRT. Dead.
(Full trace: `~/.cache/clog/2026.09.14_184224_interactive.txt`, ~10.8M lines.)

**After:** the process survives startup, loads far more (383 MB RSS), and produces exactly **one**
access violation instead of thousands — at `0x00006FFFF4D06C28`, which is inside
`libarm64ecfex.dll` itself, faulting on `0x00007FFFFE6B0004`. That single AV may well be normal
FEX SMC-trap operation rather than a bug.

**But it now hangs instead of crashing.** Single thread, `State: R`, pinned at 100% of one core,
RSS flat, no window ever appears. The PC sits inside wine's PE-side `ntdll.dll` at RVA ~`0xdac50`
(non-exported), in a stretch of code doing `strh` stores into a structure at 16-byte stride
across offsets 296–408 while loading `q` registers off the stack — that's the x87
`FloatRegisters` area of an x86-64 `CONTEXT`. So it is building CONTEXT structures over and over.

An exception-dispatch loop is the obvious suspect, and it would rhyme with the original failure
(which was also a repeating exception at one address, just one that eventually aborted). It is
not confirmed.

### What is unverified — please don't inherit these as facts

- **The guard-page theory was never confirmed.** FEX already logs
  `"Failed to mprotect last page of code buffer."` on `VirtualProtect` failure, and that message
  never fired in any run. The patch may be correcting something real but not load-bearing.
- **Wine's own side already looked correct.** A `WINEDEBUG=+virtual` trace showed wine's ntdll
  doing clean 16K-aligned sub-page tracking on its own guard pages
  (`0xe10000-0xe13fff -----` / `0xe14000-0xe17fff cgrw-` / `0xe18000-0xf0ffff c-rw-`).
- **Both fault addresses live in `0x7FFFFE…`**, well above where wine maps its builtin DLLs
  (`0x6FFF…`). Nothing was ever established about what is supposed to be mapped there.
- **The premise that FEX 2507/2508 had 16K support that was later removed did not survive
  checking.** A diff of all 250 commits between tags `FEX-2507` and `FEX-2609` found no such
  add-then-revert, and `FEX_PAGE_SIZE` has been 4096 since 2022. Two things may be getting
  conflated: FEX PR #2324 (Jan 2023) really was a jemalloc 16K add-then-revert, and Wine 10.5
  (April 2025) really did add host-page-size-aware allocation — but Asahi's own August 2025
  report scopes that to **32-bit** apps and says 64-bit ones still need muvm.

## A packaging bug worth knowing about, independent of all this

`fex-emu-wine-2609.spec` used `%setup` in `%prep`, which — unlike `%autosetup` — **never applies
`Patch:` entries**. The build log proves `%prep` only untarred the source. That means the three
upstream cherry-picks listed in this spec (`a37def2c…`, `8eaf4541…`, `c326e2d6…`) have been
**inert for as long as they've been listed**, across every version of this spec.

The patch was therefore given an explicit `Patch100:` number and an explicit `%patch -P 100 -p1`
line, so only it applies. The other three were deliberately left inert — switching to
`%autosetup` would have turned on three never-before-applied patches at the same moment as
testing a new one, which would have made the result unreadable. **Whether those three should be
wired up is an open decision, not a settled one.**

## How to reproduce and iterate

Build, install, run — all verified working as written:

```
cd ~/.local/rpm/specs && mx-rpm --no-git-commit fex-emu-wine-2609
sudo dnf reinstall -y --allow-vendor-change ~/.local/rpm/rpms/fex-emu-wine-2609/fex-emu-wine-2609-1.fc44.aarch64.rpm
cd "/home/lm/Software/Adobe.Lightroom.Classic.v15.2/Adobe 2026/products/LTRM/AdobeLightroom-mul/1/Adobe Lightroom Classic"
WINEPREFIX=/home/lm/.local/share/wine-prefixes/lr-test wine Lightroom.exe
```

- `--allow-vendor-change` is required — the installed package comes from a COPR vendor and the
  rebuild has none. Same NEVRA, so `dnf install` silently no-ops; `reinstall` is the one to use.
  Always confirm afterwards that the installed DLL's checksum matches the freshly built one.
- `/home/lm/.local/share/wine-prefixes/lr-test` is a clean prefix made with `wineboot -u`. The
  user's existing `lightroom` prefix and their own `refresh-lightroom` script were left untouched.
- Lightroom runs in place from the extracted installer payload; there is no install step.
- `setsid` returns immediately, so a `timeout … setsid wine …` reads as instant success. Launch
  backgrounded and poll instead.
- `WINEDEBUG=+seh,+virtual` produces ~50M lines in 45 seconds. Filter at the source.
- Windows: `niri msg windows`. Screenshots: `grim`.
- Patch and spec: `/home/lm/.local/src/wine-arm64ec-rpm/fex-emu-wine/`. The patch is also staged
  in `~/.local/rpm/sources/fex-emu-wine-2609/`, which is where mock reads it from — update both.

## What I'd ask of you

Work out why it spins, and get Lightroom to a window. The `InterruptFaultPage` relocation is the
known-unfinished piece and the best-supported lead, but the honest state is that the guard-page
theory is unconfirmed, so treat "is this even the right diagnosis?" as live. If the evidence says
the diagnosis is wrong, say so and change direction rather than finishing the patch for its own sake.

Some things worth being explicit about:

- **Before reporting progress, audit each claim against a tool result from this session.** Only
  report what you can point at evidence for; if something isn't verified, say so. If it still
  hangs, say it still hangs.
- **Don't reach for muvm or box64**, including as a "just to compare" step. If you conclude the
  native path is genuinely unreachable, that conclusion is a valid and useful result — say it
  plainly with the evidence, rather than routing around the constraint.
- **Prefer reversible steps.** Don't touch the user's existing wine prefixes; `lr-test` is yours.
  Full mock rebuilds take a few minutes, so hand-applying inside the existing warm chroot and
  re-running `ninja` is the faster inner loop when iterating on the C++.
- **Delegate independent subtasks to sub-agents and keep working while they run** — reading the
  JIT codegen around `InterruptFaultPage`, and characterizing the ntdll spin, are separable.
- **Scope before you build.** This has already burned one patch cycle on an unconfirmed theory.
  Confirming what the spin actually is, before writing more code, is probably worth the turn.

The user is direct and wants concise answers — no preamble, no restating what was just done, and
minimal code comments (only non-obvious "why"). They know this stack well; you don't need to
explain wine or FEX basics to them.
