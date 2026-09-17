# Handover: Limbo and Dark Souls PTDE (2026-09-18) — both resolved

Companion to `HANDOVER-fable-2026-09-17.md` (host, tree layout, tooling, everything that shipped).

## State

- Installed: `wine-11.17-ec10` (COPR build 10998538; patch 619 now also accepts `point` in state
  blocks), `fex-emu-wine-2609-3`. `sudo` is aliased to `pkexec` on this host (desktop auth dialog),
  and the COPR CDN serves 503s for a few minutes after a build succeeds; wait before `dnf upgrade`.
- Shadow install has ec10's 32-bit `d3dcompiler_43.dll` and `wined3d.dll` (built in `build-i386/`);
  the ec9 copies are `d3dcompiler_43.dll.ec9` / `wined3d.dll.ec9` in the dev cache. Its
  `i386-windows/ntdll.dll` is a link to `/usr` again and `full/dlls/ntdll/signal_i386.c` is pristine.
- AeDebug is back to `winedbg --auto %ld %ld` in both keys.

## Both "crashes" were Goldberg (GSE) configuration, not Wine or FEX

`steam_api.dll` (gbe_fork, VS2022 build) resolves the flat accessors (`SteamUserStats()` etc.) to
the **SDK 1.61 interface layouts** unless `steam_interfaces.txt` says otherwise. Both games are
2010–2012 SDK titles whose exes carry no interface version strings (Steam DRM wrapper), so GSE
cannot auto-detect them. In SDK 1.61 `ISteamUserStats::RequestCurrentStats()` was removed and slot 0
became `GetStat(const char *, int32 *)` — a `__thiscall` with 8 stack bytes.

- **Dark Souls PTDE:** `SteamUserStats()->vtbl[0]()` at `DARKSOULS.exe+0xb91075` ran `GetStat` with
  the caller's saved `edi`/`esi` as arguments → `strlen((char*)-2)`.
- **Limbo:** same call in the ctor at `0x48ba70` (`call edi; ...; call [[eax]]`). `GetStat` returns
  with `ret 8`, the caller's epilog then loads the EH state (2) into `fs:[0]` and `ret` pops the
  `this` of the second base (`esi+4`) → `EXCEPTION_PRIV_INSTRUCTION` at `esi+4` in heap data, and
  `call_seh_handlers` finds frame `2`. Timing had nothing to do with it; the "+relay hides it" note
  was wrong (that run simply hadn't reached the call yet).

Fix, applied to both game dirs next to the exe: `steam_interfaces.txt` generated from the original
Valve DLL the user kept as `steam_api#.dll`:

```
grep -a -o -E 'STEAM[A-Z]*_INTERFACE_VERSION[0-9]+|Steam(Client|User|Friends|Utils|MatchMaking|MatchMakingServers|Networking|Apps|GameServer)[0-9]{3}' steam_api#.dll | sort -u > steam_interfaces.txt
```

Limbo also got `steam_appid.txt` (48000). Any other pre-2014 game with a stripped exe will need the
same treatment; GSE's `generate_interfaces` tool does exactly this against the original DLL.

## Limbo's second problem: another HLSL keyword

After the vtable fix Limbo showed `Pixel shader error: <anonymous>:22:19: E5000: syntax error,
unexpected ';'` (a `MessageBoxA`, then `ExitProcess(1)`) — `MinFilter = point;` in a `sampler_state`
block; vkd3d lexes `point` as the GS primitive keyword. Patch 619 now has a `STATE_VALUE_OR(kw)`
macro used for `linear` and `point`. Upstream vkd3d master still has both bugs; worth sending.

Verified: Dark Souls in-game (Undead Asylum), Limbo in-game, with the shadow install.

## Tooling added this session

- `dumpstack.py <pid> <log>` in the dev cache: parses the last `+seh` `dispatch_exception` context
  from a log and dumps the 32-bit stack from `/proc/<pid>/mem`, tagging words by module. Works on a
  process held by AeDebug=winemine (`ptrace_scope` is 0 here).
- For crash paths that never reach the debugger (invalid SEH frame → `NtRaiseException` fails), the
  trick that worked: add an `ERR` + `for (;;) NtDelayExecution()` in `call_seh_handlers`'s
  invalid-frame branch (`dlls/ntdll/signal_i386.c`), `make -C build-i386 dlls/ntdll/i386-windows/ntdll.dll`,
  copy over the shadow link, then read `/proc/<pid>/{maps,mem}`. Reverted afterwards.
- `limbo-shadow.sh` runs Limbo on the shadow install with Lutris' DXVK overrides.
- `wkill.sh` now matches names longer than 15 chars (it silently missed `limbo.exe.unpacked.exe`,
  which cost a run of debugging a stale window). Never `pkill -f` from the assistant shell: the
  command line matches itself.
- `wshot.sh` can hang in `wl-paste` when a Wine process owns the clipboard; use `timeout 3 wl-paste`.
  niri writes the PNG asynchronously: wait for the file size to settle before reading it.

## Left open

- Nothing for these two games. The 16K SMC hole noted in the previous handover (code page sharing a
  host page with non-RWX writable pages is untrappable) is still a real gap; it just was not this.

## Dark Souls PTDE with DSfix (added 2026-09-18, after the release)

The user installed DSfix (`DATA/DINPUT8.dll`, imports `d3dx9_42`) at 23:30. It crashed at
`DINPUT8.dll+0x6989` using an `ID3DXEffect*` it never checked: every `dsfix/*.fx` fails with Wine's
builtin d3dx9/vkd3d-shader, whose fx_2_0 writer has no `sampler_state` initializers or
`compile`-state assignments (`E5017 ... not implemented`). The native `d3dx9_42/43` and
`d3dcompiler_42/43` DLLs were already in `syswow64` from the game's `REDIST/DirectX` cabs; only the
load order was missing. Set in the prefix registry (`HKCU\Software\Wine\DllOverrides`, all four
`native`), so Lutris launches pick them up. In-game verified.

`fxtest.exe <file.fx>...` (source alongside in the dev cache) compiles effects through whichever
d3dx9_43 the overrides select and prints the compiler messages; run it from the `dsfix/` dir.
DSfix's own defines (`PIXEL_SIZE` etc.) are not passed, so those errors are expected.

DSfix config notes: `presentWidth/Height 0` means "same as render", so with `renderWidth 1920` the
game window must be 1920x1080 or smaller or the frame lands unscaled in the top-left. The game is
configured windowed 2560x1440 (`AppData/Local/NBGI/DarkSouls/DarkSouls.ini`), which stretches fine;
when niri tiled the window to the whole 4K output the quarter-frame appeared. Either set
`renderWidth/Height 3840x2160` (the point of DSfix on this display) or give the game a niri
`open-floating` rule.
