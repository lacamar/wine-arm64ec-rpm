#!/usr/bin/env python3
# vptr.py <fifo>  virtual pointer daemon; fifo commands: "move X Y", "click [left|right]", "down", "up", "rel DX DY", "scroll N"
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pywayland.client import Display
from proto.wayland import WlSeat
from proto.wlr_virtual_pointer_unstable_v1 import ZwlrVirtualPointerManagerV1

W, H = int(os.environ.get("VW", 1920)), int(os.environ.get("VH", 1080))
BTN = {"left": 0x110, "right": 0x111}

display = Display()
display.connect()
reg = display.get_registry()
globs = {}
reg.dispatcher["global"] = lambda r, name, iface, ver: globs.__setitem__(iface, (name, ver))
display.roundtrip()
seat = reg.bind(globs["wl_seat"][0], WlSeat, 1)
mgr = reg.bind(globs["zwlr_virtual_pointer_manager_v1"][0], ZwlrVirtualPointerManagerV1, 1)
ptr = mgr.create_virtual_pointer(seat)
display.roundtrip()

def ms():
    return int(time.monotonic() * 1000) & 0xffffffff

def button(name, state):
    ptr.button(ms(), BTN[name], state)
    ptr.frame()

fifo = sys.argv[1]
if not os.path.exists(fifo):
    os.mkfifo(fifo)
while True:
    with open(fifo) as f:
        for line in f:
            cmd = line.split()
            if not cmd:
                continue
            if cmd[0] == "move":
                ptr.motion_absolute(ms(), int(cmd[1]), int(cmd[2]), W, H)
                ptr.frame()
            elif cmd[0] == "rel":
                ptr.motion(ms(), float(cmd[1]), float(cmd[2]))
                ptr.frame()
            elif cmd[0] == "click":
                b = cmd[1] if len(cmd) > 1 else "left"
                button(b, 1)
                display.flush()
                time.sleep(0.08)
                button(b, 0)
            elif cmd[0] == "down":
                button(cmd[1] if len(cmd) > 1 else "left", 1)
            elif cmd[0] == "up":
                button(cmd[1] if len(cmd) > 1 else "left", 0)
            elif cmd[0] == "scroll":
                ptr.axis(ms(), 0, float(cmd[1]) * 15)
                ptr.frame()
            display.flush()
            display.roundtrip()
