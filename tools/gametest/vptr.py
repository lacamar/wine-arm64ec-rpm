#!/usr/bin/env python3
# vptr.py <fifo>  virtual pointer + keyboard daemon; fifo commands:
#   move X Y | rel DX DY | click [left|right] | down [btn] | up [btn] | scroll N
#   key K[+K...] [...] (e.g. key Return, key ctrl+s) | keydown K | keyup K | type TEXT
import ctypes, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pywayland.client import Display
from proto.wayland import WlSeat
from proto.wlr_virtual_pointer_unstable_v1 import ZwlrVirtualPointerManagerV1
from proto.virtual_keyboard_unstable_v1 import ZwpVirtualKeyboardManagerV1

W, H = int(os.environ.get("VW", 1920)), int(os.environ.get("VH", 1080))
BTN = {"left": 0x110, "right": 0x111, "middle": 0x112}

# evdev keycodes (linux/input-event-codes.h)
KEYS = {"escape": 1, "minus": 12, "equal": 13, "backspace": 14, "tab": 15, "return": 28, "enter": 28,
        "ctrl": 29, "control_l": 29, "shift": 42, "shift_l": 42, "shift_r": 54, "alt": 56, "alt_l": 56,
        "space": 57, "capslock": 58, "control_r": 97, "alt_r": 100, "home": 102, "up": 103, "pageup": 104,
        "prior": 104, "left": 105, "right": 106, "end": 107, "down": 108, "pagedown": 109, "next": 109,
        "insert": 110, "delete": 111, "super": 125, "grave": 41, "comma": 51, "period": 52, "slash": 53,
        "semicolon": 39, "apostrophe": 40, "bracketleft": 26, "bracketright": 27, "backslash": 43,
        "f11": 87, "f12": 88}
KEYS.update({str(d): 2 + (d - 1) % 10 for d in range(10)})
KEYS.update({f"f{i}": 58 + i for i in range(1, 11)})
for row, start in (("qwertyuiop", 16), ("asdfghjkl", 30), ("zxcvbnm", 44)):
    KEYS.update({c: start + i for i, c in enumerate(row)})
MODS = {42: 1, 54: 1, 29: 4, 97: 4, 56: 8, 100: 8, 125: 64}
SHIFTED = dict(zip('~!@#$%^&*()_+{}|:"<>?', "`1234567890-=[]\\;',./"))
CHARS = {" ": "space", "-": "minus", "=": "equal", "`": "grave", ",": "comma", ".": "period", "/": "slash",
         ";": "semicolon", "'": "apostrophe", "[": "bracketleft", "]": "bracketright", "\\": "backslash",
         "\t": "tab", "\n": "return"}


def us_keymap():
    xkb = ctypes.CDLL("libxkbcommon.so.0")
    xkb.xkb_context_new.restype = ctypes.c_void_p
    xkb.xkb_keymap_new_from_names.restype = ctypes.c_void_p
    xkb.xkb_keymap_new_from_names.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    xkb.xkb_keymap_get_as_string.restype = ctypes.c_void_p
    xkb.xkb_keymap_get_as_string.argtypes = [ctypes.c_void_p, ctypes.c_int]
    names = (ctypes.c_char_p * 5)(b"evdev", b"pc105", b"us", b"", b"")
    ctx = xkb.xkb_context_new(0)
    km = xkb.xkb_keymap_new_from_names(ctx, ctypes.cast(names, ctypes.c_void_p), 0)
    return ctypes.string_at(xkb.xkb_keymap_get_as_string(km, 1)) + b"\0"


display = Display()
display.connect()
reg = display.get_registry()
globs = {}
reg.dispatcher["global"] = lambda r, name, iface, ver: globs.__setitem__(iface, (name, ver))
display.roundtrip()
seat = reg.bind(globs["wl_seat"][0], WlSeat, 1)
ptr = reg.bind(globs["zwlr_virtual_pointer_manager_v1"][0], ZwlrVirtualPointerManagerV1, 1).create_virtual_pointer(seat)
kbd = reg.bind(globs["zwp_virtual_keyboard_manager_v1"][0], ZwpVirtualKeyboardManagerV1, 1).create_virtual_keyboard(seat)
keymap = us_keymap()
with tempfile.TemporaryFile() as f:
    f.write(keymap)
    f.flush()
    kbd.keymap(1, f.fileno(), len(keymap))
    display.roundtrip()
mods = 0


def ms():
    return int(time.monotonic() * 1000) & 0xffffffff


def button(name, state):
    ptr.button(ms(), BTN[name], state)
    ptr.frame()


def key(code, state):
    global mods
    kbd.key(ms(), code, state)
    if code in MODS:
        mods = mods | MODS[code] if state else mods & ~MODS[code]
        kbd.modifiers(mods, 0, 0, 0)
    display.flush()


def chord(spec):
    codes = [KEYS[k.lower()] for k in spec.split("+")]
    for c in codes:
        key(c, 1)
        time.sleep(0.03)
    time.sleep(0.08)
    for c in reversed(codes):
        key(c, 0)
    time.sleep(0.05)


def type_text(text):
    for ch in text:
        base = SHIFTED.get(ch, ch.lower())
        name = CHARS.get(base, base)
        chord(("shift+" if ch in SHIFTED or ch.isupper() else "") + name)


fifo = sys.argv[1]
if not os.path.exists(fifo):
    os.mkfifo(fifo)
while True:
    with open(fifo) as f:
        for line in f:
            cmd = line.split(" ", 1)[0].strip()
            args = line[len(cmd):].strip()
            a = args.split()
            try:
                if cmd == "move":
                    ptr.motion_absolute(ms(), int(a[0]), int(a[1]), W, H)
                    ptr.frame()
                elif cmd == "rel":
                    ptr.motion(ms(), float(a[0]), float(a[1]))
                    ptr.frame()
                elif cmd == "click":
                    b = a[0] if a else "left"
                    button(b, 1)
                    display.flush()
                    time.sleep(0.08)
                    button(b, 0)
                elif cmd == "down":
                    button(a[0] if a else "left", 1)
                elif cmd == "up":
                    button(a[0] if a else "left", 0)
                elif cmd == "scroll":
                    ptr.axis(ms(), 0, float(a[0]) * 15)
                    ptr.frame()
                elif cmd == "key":
                    for spec in a:
                        chord(spec)
                elif cmd == "keydown":
                    key(KEYS[a[0].lower()], 1)
                elif cmd == "keyup":
                    key(KEYS[a[0].lower()], 0)
                elif cmd == "type":
                    type_text(args)
            except (KeyError, IndexError, ValueError) as e:
                print("bad command:", line.strip(), e, flush=True)
            display.flush()
            display.roundtrip()
