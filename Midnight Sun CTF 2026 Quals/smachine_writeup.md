# smachine

## Challenge Overview
Name: smachine
Author: @acez
Category: baby_vm, blackbox
Description: Sometimes reversing is just blackbox testing.
Flag format: midnight{...}
Objective: Interact with the blackbox Simple Machine service, discover the available operations, and set a register to the required winning value.

## Files Provided
- N/A

## Solution Plan
1. Connect to the remote service and identify the available commands.
2. Use `help`, `regs`, and `win` to understand the machine state and win condition.
3. Set any register to `0x1337` using allowed arithmetic and bitwise operations, then run `win`.

## Code (Exploit Script)
```bash
nc smachine.play.ctf.se 9189

help
regs
win

add x9 65535
and x9 70455
regs
win
```

## Flag
```txt
midnight{s1MpL3_sT4cK_M4cH1N3}
```

## Notes
The service starts a REPL named Simple Machine. The `help` command lists the supported operations:

```txt
add  and  help  mul  or  regs  sub  win  xor
```

The `win` command reveals the condition:

```txt
Set any register to 0x1337 in order to win.
```

Directly adding `4919` (`0x1337`) returned `Bad Result`, but bitwise operations allowed reaching the target value. Setting `x9` to `0xffff` and applying `and x9 70455` results in `0x1337`, which satisfies the win condition.
