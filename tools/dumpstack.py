#!/usr/bin/env python3
import re
import struct
import sys

if len(sys.argv) < 3:
    sys.exit("usage: dumpstack.py <pid> <wine +seh log> [words above ebp]")

pid, log = int(sys.argv[1]), sys.argv[2]
above = int(sys.argv[3]) if len(sys.argv) > 3 else 64

text = open(log, errors="replace").read()
matches = list(re.finditer(r"(\w+):trace:seh:dispatch_exception code=(\w+)[^\n]*\n(?:[^\n]*\n){0,4}?"
                           r"[^\n]*eip=(\w+) esp=(\w+) ebp=(\w+)", text))
if not matches:
    sys.exit("no 32-bit dispatch_exception context in log")
tid, code, eip, esp, ebp = matches[-1].groups()
print(f"tid={tid} code={code} eip={eip} esp={esp} ebp={ebp}")
esp, ebp = int(esp, 16), int(ebp, 16)

maps = []
for line in open(f"/proc/{pid}/maps"):
    fields = line.split()
    lo, hi = (int(x, 16) for x in fields[0].split("-"))
    maps.append((lo, hi, fields[5] if len(fields) > 5 else "anon"))


def module(addr):
    for lo, hi, name in maps:
        if lo <= addr < hi:
            return f"{name.rsplit('/', 1)[-1]}+{addr - lo:#x}"
    return "?"


start = esp - 0x40
end = max(ebp, esp) + above * 4
with open(f"/proc/{pid}/mem", "rb") as mem:
    mem.seek(start)
    data = mem.read(end - start)

for i in range(0, len(data) - 3, 4):
    addr = start + i
    value = struct.unpack_from("<I", data, i)[0]
    tag = "<-esp" if addr == esp else "<-ebp" if addr == ebp else ""
    where = module(value) if 0x10000 <= value < 0x80000000 else ""
    print(f"{addr:08x}: {value:08x}  {where} {tag}")
