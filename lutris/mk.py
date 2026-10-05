#!/usr/bin/python3
import pathlib
import yaml

PACKAGES = {
    "lutris": "0.5.22-6",
    "mangohud": "0.8.3~rc1-7",
    "mesa-vulkan-drivers": "26.3.0~git20261003.888a19e2-2",
    "wine-git": "11.19^0.git.455e350-ec.10",
    "fex-emu-wine-git": "2609.1^5.git.79a7afe-8",
    "wine-dxvk": "3.1.1-ec3",
    "wine-vkd3d-proton": "3.0.1-ec5",
}

DEPS = """set -e
old=$(while read p v; do
  h=$(rpm -q --qf '%{version}-%{release}' "$p" 2>/dev/null) &&
    [ "$(rpm --eval "%{lua:print(rpm.vercmp('$h','$v'))}")" -ge 0 ] || echo "$p"
done <<'EOF'
""" + "".join(f"{p} {v}\n" for p, v in PACKAGES.items()) + """EOF
)
[ -z "$old" ] && exit 0
pkexec sh -c "dnf -y copr enable lacamar/arm64-misc &&
  dnf -y copr enable lacamar/wine-arm64ec &&
  dnf -y --refresh --allow-vendor-change --allowerasing install $(echo $old) &&
  dnf -y --allow-vendor-change upgrade 'mesa*' $(echo $old)"
"""

STEAM = "Steam DRM: run with Steam in the prefix, or Steamless + Goldberg (GBE)."

# slug, name, rating, exe hint, extra
GAMES = [
    ("alien-isolation", "Alien: Isolation", "Platinum", "Alien Isolation/AI.exe", {}),
    ("amnesia-the-dark-descent", "Amnesia: The Dark Descent", "Platinum", "Amnesia The Dark Descent/Amnesia_NoSteam.exe", {}),
    ("amnesia-a-machine-for-pigs", "Amnesia: A Machine for Pigs", "Silver", "Machine for Pigs/aamfp_NoSteam.exe",
     {"notes": "Starts at 1024x768: set Screen in Documents/Amnesia/Pig/main_settings.cfg."}),
    ("balatro", "Balatro", "Platinum", "Balatro/Balatro.exe", {}),
    ("binding-of-isaac-rebirth", "The Binding of Isaac: Repentance+", "Platinum", "The Binding of Isaac Rebirth/isaac-ng.exe", {"drm": True}),
    ("bioshock-remastered", "BioShock Remastered", "Gold", "BioShock Remastered/Build/Final/BioshockHD.exe",
     {"drm": True, "notes": "GBE: set offline=1 under [main::connectivity] in configs.main.ini (2K SSO crash). Menus need the keyboard."}),
    ("crysis-2-remastered", "Crysis 2 Remastered", "Silver", "Crysis2Remastered/Bin64/Crysis2Remastered.exe",
     {"drm": True, "args": "+r_VkContext 0 +sys_rendervulkan 0 +sys_spec 1",
      "overrides": {"d3d12": "disabled", "d3d12core": "disabled"}, "notes": "Keep sys_spec 1; higher specs exit on level load."}),
    ("dark-souls-ptde", "Dark Souls: Prepare to Die Edition", "Gold", "Dark Souls Prepare to Die Edition/DATA/DARKSOULS.exe",
     {"overrides": {"d3dcompiler_42": "n,b", "d3dcompiler_43": "n,b", "d3dx9_42": "n,b", "d3dx9_43": "n,b", "dinput8": "n,b"},
      "d3d_extras": True, "env": {"DXVK_CONFIG": "d3d9.presentInterval = 1"},
      "notes": "Tested with DSfix (4K, unlockFPS, SMAA), DSIC, FPSFix+ and DS1LadderFix; in-game AA off."}),
    ("dark-souls-ii-sotfs", "Dark Souls II: Scholar of the First Sin", "Gold", "Dark Souls II Scholar of the First Sin/Game/DarkSoulsII.exe",
     {"drm": True, "env": {"LIBVA_DRIVER_NAME": "none"}, "notes": "Scroll the EULA to the end; play offline."}),
    ("dark-souls-iii", "Dark Souls III", "Silver", "DARK SOULS III/Game/DarkSoulsIII.exe",
     {"drm": True, "notes": "Scroll the EULA to the end; play offline. CPU-bound, ~35 fps."}),
    ("dead-space", "Dead Space", "Gold", "Dead Space/Dead Space.exe",
     {"drm": True, "env": {"DXVK_CONFIG": "d3d9.presentInterval = 1"},
      "notes": "Settings don't persist: edit AppData/Local/Electronic Arts/Dead Space/settings.txt (resolution, VSync=false)."}),
    ("dead-space-2", "Dead Space 2", "Gold", "Dead Space 2/deadspace2.exe",
     {"drm": True, "notes": "Settings don't stick: edit AppData/Local/EA Games/Dead Space 2/settings.txt (resolution, Window.VSync = false)."}),
    ("deus-ex-hr", "Deus Ex: Human Revolution", "Platinum", "Deus Ex - Human Revolution/dxhr.exe",
     {"drm": True, "notes": "GBE needs steam_interfaces.txt and steam_appid.txt."}),
    ("deus-ex-hr-missing-link", "Deus Ex: HR - The Missing Link", "Platinum", "DXHRML/dxhrml.exe", {"drm": True}),
    ("dishonored", "Dishonored", "Gold", "Dishonored/Binaries/Win32/Dishonored.exe",
     {"drm": True, "args": "-ResX=$RESOLUTION_WIDTH -ResY=$RESOLUTION_HEIGHT"}),
    ("ddlc", "Doki Doki Literature Club", "Platinum", "Doki Doki Literature Club/DDLC.exe", {}),
    ("elden-ring", "Elden Ring", "Silver", "ELDEN RING/Game/start_protected_game.exe",
     {"drm": True, "notes": "Offline only (no EAC). ~40 fps at 1080p High."}),
    ("fallout-new-vegas", "Fallout: New Vegas", "Gold", "Fallout New Vegas/FalloutNV.exe",
     {"drm": True, "notes": "Run FalloutNVLauncher.exe once to write prefs. If it exits silently, set sD3DDevice=\"AMD Radeon RX 6700 XT\" in FalloutPrefs.ini."}),
    ("fear-and-hunger", "Fear & Hunger", "Gold", "Game.exe", {"args": "--in-process-gpu --disable-direct-composition"}),
    ("killing-floor", "Killing Floor", "Silver", "KillingFloor/System/KillingFloor.exe", {"drm": True, "x87": "0"}),
    ("limbo", "Limbo", "Platinum", "Limbo/limbo.exe", {"drm": True}),
    ("metal-garden", "Metal Garden", "Gold", "MetalGarden.exe", {}),
    ("mirrors-edge", "Mirror's Edge", "Gold", "mirrors edge/Binaries/MirrorsEdge.exe",
     {"drm": True, "notes": "Starts at 800x600: set ResX/ResY in Documents/EA Games/Mirror's Edge/TdGame/Config/TdEngine.ini."}),
    ("naissancee", "NaissanceE", "Gold", "NaissanceE/Binaries/Win32/UDK.exe",
     {"args": "-ResX=$RESOLUTION_WIDTH -ResY=$RESOLUTION_HEIGHT -fullscreen", "notes": "Accept the UDK EULA once."}),
    ("nubbys-number-factory", "Nubby's Number Factory", "Platinum", "Nubby's Number Factory/NNF_FULLVERSION.exe", {}),
    ("portal-2", "Portal 2", "Platinum", "Portal 2/portal2.exe", {"drm": True}),
    ("prison-of-husks-demo", "Prison of Husks Demo", "Platinum", "PRISON OF HUSKS Demo/PRISON OF HUSKS -Demo-.exe", {}),
    ("psychopomp", "Psychopomp", "Platinum", "Psychopomp/Psychopomp.exe", {}),
    ("road-to-vostok", "Road to Vostok", "Silver", "Road to Vostok/RTV.exe", {"args": "--rendering-driver vulkan"}),
    ("road-to-vostok-demo", "Road to Vostok Demo", "Silver", "Road to Vostok Demo/RTV.exe", {"args": "--rendering-driver vulkan"}),
    ("routine", "Routine", "Silver", "Routine/Routine/Binaries/Win64/Routine-Win64-Shipping.exe", {"drm": True}),
    ("signalis", "SIGNALIS", "Platinum", "SIGNALIS/SIGNALIS.exe", {}),
    ("slay-the-princess", "Slay the Princess", "Platinum", "Slay the Princess/SlaythePrincess.exe",
     {"notes": "First start takes ~90 s."}),
    ("soma", "SOMA", "Platinum", "SOMA/Soma_NoSteam.exe", {}),
    ("terraformental", "Terraformental", "Platinum", "Terraformental.exe", {}),
    ("the-swapper", "The Swapper", "Gold", "The Swapper/TheSwapper.exe", {}),
    ("the-witcher-3", "The Witcher 3 (DX12)", "Bronze", "The Witcher 3/bin/x64_dx12/witcher3.exe",
     {"drm": True, "notes": "~10 fps; GPU submit stalls."}),
    ("tomb-raider", "Tomb Raider", "Gold", "Tomb Raider/TombRaider.exe", {"drm": True}),
    ("valheim", "Valheim", "Gold", "Valheim/valheim.exe",
     {"drm": True, "args": "-force-vulkan -screen-fullscreen 1 -window-mode borderless -monitor 1",
      "notes": "~30 fps at 4K, 50-60 at 1080p. Online login fails under GBE; local worlds fine."}),
]


class Literal(str):
    pass


yaml.SafeDumper.add_representer(Literal, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"))


def installer(slug, name, rating, exe, x):
    notes = [f"wine-arm64ec rating: {rating}."]
    if x.get("drm"):
        notes.append(STEAM)
    if "notes" in x:
        notes.append(x["notes"])
    game = {"exe": "$gameexe", "prefix": "$GAMEDIR", "arch": "win64"}
    if "args" in x:
        game["args"] = x["args"]
    wine = {"version": "system", "dxvk": True, "dxvk_version": "system", "vkd3d": True, "vkd3d_version": "system"}
    if "overrides" in x:
        wine["overrides"] = x["overrides"]
    if x.get("d3d_extras"):
        wine["d3d_extras"] = True
    return {
        "name": name,
        "game_slug": slug,
        "version": "wine-arm64ec",
        "slug": f"{slug}-wine-arm64ec",
        "runner": "wine",
        "notes": " ".join(notes),
        "script": {
            "files": [{"gameexe": f"N/A:Select {exe}"}],
            "game": game,
            "installer": [
                {"execute": {"command": Literal(DEPS)}},
                {"task": {"name": "create_prefix", "prefix": "$GAMEDIR", "arch": "win64"}},
            ],
            "system": {"env": {"DISPLAY": "", "FEX_X87REDUCEDPRECISION": x.get("x87", "1"), **x.get("env", {})}},
            "wine": wine,
        },
    }


here = pathlib.Path(__file__).parent
for g in GAMES:
    with open(here / f"{g[0]}.yml", "w") as f:
        yaml.safe_dump(installer(*g), f, sort_keys=False, allow_unicode=True, width=1000)
