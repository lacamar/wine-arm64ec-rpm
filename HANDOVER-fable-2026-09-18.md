# Handover: Limbo and Dark Souls PTDE still crash under wow64 (2026-09-18)

Companion to `HANDOVER-fable-2026-09-17.md` (host, tree layout, tooling, everything that shipped).
This file is only about the two unfixed 32-bit crashes and what a new session needs to attack them.

## State right now

- Installed: `wine-11.17-ec7`, `fex-emu-wine-2609-3`. COPR build 10998030 (`wine-11.17-ec9`) was
  running at the end of the session; if it succeeded, install it:
  `sudo dnf upgrade --refresh --allow-vendor-change --exclude=winetricks 'wine*'`
  ec8 = patches 617/618 (windows follow their output, all monitors' modes everywhere),
  ec9 = patch 619 (HLSL lexer accepts `linear` in state blocks). Repo HEAD `062831a`, clean, pushed.
- Shadow install (`~/.cache/wine-arm64ec-dev/shadow`) already has all of ec9 plus FEX 2609-3.
  Its `lib64/wine/i386-windows/` is a **link farm** to `/usr/lib64/wine/i386-windows` with two real
  files, `wined3d.dll` and `d3dcompiler_43.dll`, built in `build-i386/`
  (`--enable-archs=aarch64,i386`). Rebuild 32-bit PE DLLs there:
  `make -C build-i386 dlls/<x>/i386-windows/<x>.dll`, then copy over the link.
- The HLSL compiler used by 32-bit games is the vkd3d-shader **bundled in wined3d.dll**, not the
  mingw vkd3d packages the spec BuildRequires (the packaged wined3d imports no vkd3d DLL).

## Reproducing

Both games: Lutris ids 49 (Limbo) and 17 (DS PTDE), prefix `~/.local/share/wine-prefixes/11.17`,
Goldberg/GSE `steam_api.dll` (identical md5 in both game dirs, no `steam_settings`).
Lutris does not write DXVK overrides to the registry; it passes them in the environment:

```
export WINEPREFIX=~/.local/share/wine-prefixes/11.17 DISPLAY= FEX_X87REDUCEDPRECISION=1
export WINEDLLOVERRIDES="d3d9,d3d11,dxgi,d3d8=n;winemenubuilder="
cd ~/.steam/steam/steamapps/common/Limbo
WINEDEBUG=err+all,+seh ~/.cache/wine-arm64ec-dev/shadow/bin/wine ./limbo.exe.unpacked.exe
```

Launchers in the dev cache: `limbo.sh`, `ds1.sh` (host wine, logs `limbo-run.log` / `ds1-run.log`;
extra env goes after the script name, e.g. `ds1.sh env FEX_SMCCHECKS=full`). Neither game has a
niri window rule, so they land on whatever output is focused.

Useful: `FEX_SILENTLOG=0` routes FEX's log through `__wine_dbg_output` (SMC intervals, unaligned
atomic backpatches). Hold a crashed process for gdb by pointing AeDebug at winemine:
`wine reg add 'HKLM\Software\Wow6432Node\Microsoft\Windows NT\CurrentVersion\AeDebug' /v Debugger /t REG_SZ /d 'C:\windows\system32\winemine.exe' /f`
(and the non-Wow6432Node key), restore to `winedbg --auto %ld %ld` afterwards. Note the Limbo crash
path (`NtRaiseException` failing) never starts a debugger, so attach gdb early and poll
`/proc/<pid>/maps` instead. `winedbg --auto` hangs on these processes and killing it kills the game.

## Limbo (Lutris 49) — wild jump after the boot screen

Fixed part: "Pixel shader error: 19:20 syntax error, unexpected ';'" was `MinFilter = linear;`
in a `sampler_state` block; vkd3d-shader lexed `linear` as the interpolation keyword. Patch 619
(`hlsl.l`: return `NEW_IDENTIFIER` when `ctx->in_state_block`). Upstream vkd3d master
(ac39f73, 2026-09-10) still has the bug; worth sending upstream.

Remaining crash, ~2 s after the window appears, on the main thread:

```
dispatch_exception code=c0000096 (EXCEPTION_PRIV_INSTRUCTION) addr=0641428C
eip=0641428c esp=0012fb64 ebp=0012fea8 eax=06419d88 esi=06414288 edi=7bc7e6ec edx=7999e03c
err:seh:NtRaiseException Exception frame is not in stack limits => unable to dispatch exception.
```

- `0x0641428c` = `esi + 4`, and the bytes there are the string `titledata/bootscreen/dot.png`
  followed by `uk.png`. The region `0x06410000` is a `MapViewOfFile` view (call came from a Wine
  DLL at `0x78549a3e`, not the game). So the game jumped into file data while loading the boot
  screen. `eax=06419d88` was all zeros when first mapped.
- Timing-dependent: never reproduces under `WINEDEBUG=+relay` even though that run reaches the
  boot screen (13 `bootscreen` file accesses). Reproduces every time at normal speed and with
  `taskset -c 0`.
- Ruled out: `FEX_MULTIBLOCK=0`, `FEX_STRICTINPROCESSSPLITLOCKS=1`, `FEX_SMCCHECKS=full` (crash
  only comes later, ~5 s), d3dx9 "Unhandled filter 0x3/0x80004" (falls back to point sampling,
  no error path).
- Leads not followed to the end:
  1. FEX logs ~60 `Handled unaligned atomic` backpatches in those 2 s (59 on the main thread).
     The HalfBarrier backpatch is non-atomic for RMW; strict split locks did not help, but the
     `Handled` path itself (backpatched instruction sequence) was not inspected.
  2. FEX re-adds `SMC interval 8AB000-8AC000` 26 times in 2 s. `0x8AB000` is limbo.exe's
     `.idata` (RW section) which the game *executes* (Wine DEP emulation makes it RWX on the exec
     fault). It is the last 4K of the 16K host page `8A8000-8AC000`; the other three pages are
     plain RW `.dataa`, so FEX's write trap (RX on the code page only) can never take effect under
     Wine's most-permissive-wins union. That is a genuine 16K hole: code pages sharing a host page
     with non-RWX writable pages are untrappable. `FEX_SMCCHECKS=full` should have masked it and
     did not, so it is probably not *this* crash, but it must be fixed anyway. Sketch: trap the
     whole host page including non-RWX neighbours, and on a write fault in a neighbour untrap the
     whole host page and invalidate the code pages in it (they re-trap on next JIT). Watch for
     native/unix-side writes into such pages (`read()` into a trapped page returns EFAULT).
  3. Find who jumps: attach gdb after the window appears and set a hardware watchpoint on
     `0x06419d88` (the zeroed object), or dump the 32-bit stack at `0x0012fb64` from the exception
     context before the process dies. `WINEDEBUG=+relay` hides the bug, so use `+seh` only.

## Dark Souls PTDE (Lutris 17) — Goldberg crash

```
wine: Unhandled page fault on read access to FFFFFFFE at address 77C35560 (thread 0024|0148)
eip=77c35560 esp=0012fdf4 ebp=0012fe5c eax=00000000 ebx=00000001 ecx=fffffffe esi=ffffffff edi=015f8cb0
```

- `77C35560` = `steam_api.dll` (GSE fork, loaded at `77B30000`, SizeOfImage `0x4d5000`) RVA
  `0x105560`: a `strlen` loop inside a `std::string(const char *)` construction whose argument
  (`[ebp+8]`) is `(char*)-2`. Return addresses on the stack: `77B4F7FA` (RVA `0x1F7FA`, right after
  a `call edi` that pushed `"STEAMUSERSTATS_INTERFACE_VERSION013"`, `hSteamPipe` global, and a
  byte-truncated `SteamAPI_GetHSteamUser()` result — i.e. `ISteamClient::GetISteamUserStats`) and
  `77BCBA9D` (RVA `0x9BA9D`, a `std::map::find` on `this+0x148`).
- Deterministic; the crashing thread alternates between the main thread and Goldberg's own
  `CreateThread(77e6c745)` worker.
- Unchanged by: `FEX_MULTIBLOCK=0`, `FEX_X87REDUCEDPRECISION=0`, `FEX_TSOENABLED=0`,
  `FEX_STRICTINPROCESSSPLITLOCKS=1`, `FEX_SMCCHECKS=full`, `taskset -c 0`, GSE
  `disable_networking=1`, a `steam_appid.txt` (211420). The last 32-bit API calls before the
  crash are Goldberg enumerating network adapters (the docker `br-*`/`veth*` names), then
  `QueryPerformanceCounter`, `GetModuleHandleExW`, `CreateThread`.
- Same DLL initialises fine in Limbo, which never requests ISteamUserStats.
- Next: get the frame with the AeDebug=winemine trick and `x/16wx 0x0012fe58` for the caller and
  the real argument; disassemble `0x1001F700..0x1001F800` and `0x1009BA80..` in the DLL
  (`x86_64-w64-mingw32-objdump -d -M intel --start-address=...`) to identify the GSE function; or
  swap in a different Goldberg build to see whether it is DLL-specific. Nothing so far points at
  Wine or FEX.

## Everything else from this session that is done

Wine patches 615–619 and FEX 2609-3 are shipped and described in the 09-17 handover. Elden Ring's
windowed-mode swapchain storm is fixed (616); its one-off startup hang was never reproduced.
