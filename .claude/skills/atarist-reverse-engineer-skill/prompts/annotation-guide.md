# Annotation Style Guide

How to write effective annotations for 68000 Atari ST disassembly listings.

---

## Block Comments (Before Subroutines)

Place before every identified subroutine. Include purpose, algorithm description, and register conventions.

```
; -------------------------------------------------------
; routine_name - Brief one-line description
; Longer explanation of what this routine does, the
; algorithm it implements, and why it exists in the
; context of the program.
;
; Entry: A0 = pointer to input buffer
;        D0.B = first character of input
;        D2 = radix (10 for decimal, 16 for hex)
; Exit:  D1.L = parsed numeric value
;        D0.B = next character after the number
;        Carry flag clear = success, set = error
; Trashes: D3, D4
; -------------------------------------------------------
```

**Rules:**
- Always include Entry/Exit if determinable from code analysis
- Always list trashed registers (not saved/restored by the routine)
- Describe the algorithm, not just the effect ("uses repeated division by 16" not "converts to hex")
- Mention any 68000 tricks used ("splits 32-bit multiply via SWAP because MULU is 16-bit only")
- Note if the routine is called from multiple places and what its callers expect

---

## Inline Comments (On Instruction Lines)

Appended to the instruction line, separated by ` ; `.

### Good Comments (explain WHY in context)

```
  01234: 0C 00 00 61  cmpi.b  #$61, d0     ; Is it >= 'a'? (start of lowercase range)
  01238: 04 00 00 20  subi.b  #$20, d0     ; Convert lowercase→uppercase (ASCII distance = $20)
  0123C: 48 43        swap    d3           ; Move high word to low for 16-bit MULU (68000 trick)
  01240: 4E 4D        trap    #$d          ; >>> BIOS Kbshift(-1) — read modifier key state
  01244: 0C 40 00 3B  cmpi.w  #$3b, d0    ; F1 key scancode ($3B)
  01248: 67 22        beq.b   $126c        ; Yes → jump to F1 handler
```

### Bad Comments (just repeat the instruction)

```
  01234: 0C 00 00 61  cmpi.b  #$61, d0     ; compare d0 with $61     ← BAD: says nothing useful
  01238: 04 00 00 20  subi.b  #$20, d0     ; subtract $20 from d0    ← BAD: just repeats mnemonic
  01240: 4E 4D        trap    #$d          ; trap 13                  ← BAD: no function identified
```

### What to Always Comment

| Instruction Type | Comment Should Explain |
|---|---|
| `CMPI.B #$XX, Dn` | What the value represents (ASCII char? scancode? error code?) |
| `Bcc` (any branch) | What the condition means in context ("If digit >= radix → invalid") |
| `TRAP #n` | Which TOS function and its purpose |
| `PEA $XXXXXXXX` | What the packed value means (function + parameter) |
| `MOVE.W #$XXXX, SR` | What SR bits are being set (trace? supervisor? IPL?) |
| `LEA xxx(PC), An` | What data the address points to (string? variable? table?) |
| `MOVEM.L regs, -(SP)` | "Save registers per calling convention" or "Push register state" |
| `BSR/JSR target` | Name of callee and what parameters are being passed |
| `RTS/RTE` | What the return value is (if any) in which register |
| Magic numbers | Decode them: `$61` = 'a', `$3B` = F1 scancode, `$601A` = TOS magic |

---

## Loop and Block Markers

Mark the beginning and end of logical code blocks:

```
; --- begin: scan hex digits until non-digit found ---
  00232: 61 00 FE 3C  bsr.w    $60         ; parse_hex_digit(D0, D2) → D0:value
  00236: 06 41 00 30  addi.w   #$30, d1    ; Accumulate: D1 = D1 * radix + digit
  0023A: 61 00 FE 2E  bsr.w    $20         ; Read next character
  0023E: 65 F2        bcs.b    $232        ; Valid digit? → loop back
; --- end: hex digit scan ---
```

---

## 68000-Specific Explanations

When an instruction uses a 68000-specific technique, explain it for readers who may not be 68000 experts:

```
  00086: 48 43        swap     d3           ; SWAP: exchange high and low 16-bit words of D3
  ; (68000's MULU only multiplies 16×16→32, so to multiply two 32-bit
  ;  numbers, we split them into high/low halves: result = Lo×Lo + Hi×Lo<<16)
```

```
  006D4: E9 19        rol.b    #4, d1       ; Rotate left 4 bits: brings high nibble to low position
  ; (ROL.B #4 is the 68000 idiom for "swap nibbles within a byte" —
  ;  equivalent to (byte >> 4) | (byte << 4), used for hex digit extraction)
```

```
  01350: 00 57 80 00  ori.w    #$8000, (sp) ; Set bit 15 (Trace flag) in the SR on the stack
  ; (When RTE restores this SR, the 68000 enters Trace mode and will
  ;  generate a Trace exception after executing exactly one instruction.
  ;  This is the hardware mechanism for single-stepping in debuggers.)
```

---

## TOS System Call Annotations

For every TRAP instruction, document the full call:

```
  ; Prepare GEMDOS Fcreate: create file for writing
  ; Stack: filename_ptr (4 bytes) + attribute (2 bytes) + func# (2 bytes)
  00A20: 2F 08        move.l   a0, -(sp)    ; Push filename pointer
  00A22: 3F 3C 00 00  move.w   #$0, -(sp)   ; Push attribute = 0 (normal file)
  00A26: 3F 3C 00 3C  move.w   #$3c, -(sp)  ; Push function $3C = Fcreate
  00A2A: 4E 41        trap     #$1          ; >>> GEMDOS Fcreate(name, attr) → D0.W = handle or error
  00A2C: 50 8F        addq.l   #$8, sp      ; Clean 8 bytes from stack (4+2+2)
```

For packed BIOS calls:

```
  00B12: 48 79 00 0B FF FF  pea.l $bffff.l  ; Push packed: func=$000B (Kbshift), param=$FFFF (read-only)
  00B18: 4E 4D        trap     #$d          ; >>> BIOS Kbshift(mode=-1) → D0.W = modifier bits
  00B1A: 58 8F        addq.l   #$4, sp      ; Clean 4 bytes from stack
  ; D0 bit 0=RShift, 1=LShift, 2=Ctrl, 3=Alt, 4=Caps, 5=RMouse, 6=LMouse
```

---

## Call Site Annotations

When a BSR/JSR calls a known routine, document what parameters are being passed:

```
  ; Set up: A0 = source text pointer, D2 = 16 (hex radix)
  01234: 61 00 FE AC  bsr.w    $e2         ; parse_expression(D0:char, A0:*src) → D1:value, D0:next_char
  01238: 4A 2D 00 09  tst.b    $9(a5)      ; Check if expression had relocation-dependent value
```
