# Annotation Style Guide

How to write effective annotations for 68000 Atari ST disassembly listings.

---

## CRITICAL: Maintain Consistent Comment Density Throughout

**The #1 annotation failure mode is starting strong, then tapering off.** The first few hundred lines get rich inline comments, then density drops to near-zero for the rest of the binary. This is unacceptable.

**Rules to prevent density drop-off:**
- Inline comment density MUST remain >=60% of instruction lines from start to finish
- Process the binary in sections/chunks — annotate each chunk to the same standard before moving on
- After generating annotations, VERIFY density by checking comment count in the first 500 lines vs the last 500 lines — they should be comparable
- Every subroutine MUST have a block comment, no matter how late in the binary it appears
- Every TRAP/system call, every magic number, every branch condition MUST have an inline comment — this applies to line 5000 just as much as line 50

**Block comments must be detailed:**
- Don't just name the subroutine — explain the algorithm, its logic, and its inner workings
- Document all data structures the routine operates on
- Explain arguments (what registers carry what meaning) and return values
- If the routine implements a non-trivial algorithm, describe the steps

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

### What to Always Comment (Mandatory Decodes)

These patterns MUST always have inline comments — no exceptions:

| Instruction Type | Comment Should Explain |
|---|---|
| `CMPI.B #$XX, Dn` | What the value represents: ASCII char (`$41`='A'), scancode (`$3B`=F1), error code, flag bit |
| `Bcc` (any branch) | What the condition means in context ("If digit >= radix → invalid"), not just "branch if equal" |
| `TRAP #n` | Which TOS function, its purpose, AND what the pushed parameters mean |
| `PEA $XXXXXXXX` | Unpack: high word = function code, low word = parameter (e.g., "Kbshift(-1): read modifier state") |
| `MOVE.W #$XXXX, SR` | What SR bits are being set: trace ($8000), supervisor ($2000), IPL ($0700) |
| `LEA xxx(PC), An` | What data the target address contains (string? variable? table? structure?) |
| `MOVE.x $NN(An), Dn` | The structure field name when An points to a known structure (basepage, DTA, AES pb, editor state) |
| `MOVEM.L regs, -(SP)` | "Save registers per calling convention" or "Push register state for exception frame" |
| `BSR/JSR target` | Name of callee and what parameters are being passed in which registers |
| `RTS/RTE` | What the return value is (if any) in which register |
| Hardware addresses ($FFxxxx) | Register name and function (e.g., "$FF8240 = palette register 0") |
| Magic numbers | Decode them: `$61`='a', `$3B`=F1 scancode, `$601A`=TOS magic, `$50005`=memory marker |

### Structure Field Reference (for inline comments)

When An points to a known structure, decode the offset:

**TOS Basepage** (from Pexec or at program start):
```
+$00 = low TPA address     +$04 = high TPA address
+$08 = text segment start  +$0C = text segment size
+$10 = data segment start  +$14 = data segment size
+$18 = BSS segment start   +$1C = BSS segment size
+$20 = DTA pointer          +$24 = parent basepage
+$28 = reserved             +$2C = environment string pointer
+$80 = command line (128 bytes)
```

**DTA (Disk Transfer Area)** (from Fsetdta/Fgetdta, after Fsfirst/Fsnext):
```
+$00 = reserved (21 bytes)
+$15 = file attributes (byte): bit 0=r/o, 1=hidden, 2=system, 3=volume, 4=subdir, 5=archive
+$16 = time (word, packed): bits 15-11=hour, 10-5=minute, 4-0=seconds/2
+$18 = date (word, packed): bits 15-9=year-1980, 8-5=month, 4-0=day
+$1A = file size (longword)
+$1E = filename (14 bytes, null-terminated)
```

**Line-A Variables** (from $A000 init, pointer in A0):
```
-$15C = mouse X position    -$15A = mouse Y position
-$3A = font header pointer  -$38 = font first ADE
-$36 = font last ADE        -$34 = font max cell width
+$00 = V_PLANES (number of bitplanes)
+$02 = V_LIN_WR (bytes per screen line)
```

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
