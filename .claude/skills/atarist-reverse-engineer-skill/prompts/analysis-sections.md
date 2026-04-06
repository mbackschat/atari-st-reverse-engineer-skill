# Section Analysis Prompt Templates

Use these templates when launching Explore agents to analyze specific code sections. Replace `{SOURCE}` with the path to the SOURCE.txt file and `{LINES}` with the line range.

**IMPORTANT — every agent MUST also output:**
1. All base-register offsets accessed (e.g., "$663C(A5) = long, current address") — for the Global Variable Map
2. All structure field accesses (e.g., "$0A6C(A3) = word, insert mode flag") — for State Structure Maps
3. All scancodes, command codes, or dispatch values with handler addresses — for dispatch tables
4. All magic numbers decoded (ASCII codes, flag bits, hardware registers, TOS constants)
5. Step-by-step algorithm description for any non-trivial logic (not just "this routine parses input")

**Explain for non-experts**: Where a code pattern depends on Atari ST or 68000-specific knowledge, include a brief explanation. Common things to explain:
- Basepage fields: +$08=text_start, +$0C=text_size, +$10=data_start, +$14=data_size, +$18=bss_start, +$1C=bss_size
- DTA fields: +$15=attributes, +$1A=file_size(long), +$1E=filename(14 bytes)
- Hardware registers: $FF8240-$FF825E=palette, $FF8260=resolution, $FFFC00=keyboard ACIA
- PEA packed params: e.g., PEA $000BFFFF pushes BIOS func $0B (Kbshift) + param $FFFF as one longword
- SWAP for 32-bit math: 68000 MULU is 16x16 only, so 32-bit multiply requires split operations
- Line-A mouse bracketing: must hide mouse before writing screen RAM to avoid artifacts

---

## Template: Entry Point and Utility Routines

```
Read {SOURCE} lines {LINES} (Entry Point and Utility Routines section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How is the base register established? (LEA (PC),An pattern)
- What utility routines are present? (whitespace skip, hex parse, multiply, divide, expression eval)
- What is the error handling mechanism? (error code in register, jump to handler)
- What calling convention is used? (which regs are scratch vs callee-saved)

For each subroutine, reconstruct:
- Name, purpose, algorithm
- Entry registers and their types
- Exit registers and return values
- Which registers are trashed
```

## Template: System I/O Wrappers

```
Read {SOURCE} lines {LINES} (System I/O Wrappers section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How does character output work? (direct screen write vs BIOS Bconout)
- How does hex printing work? (nibble extraction, ASCII conversion)
- How does keyboard input work? (Bconstat poll, Bconin read, Kbshift modifiers)
- How does the error message system work? (indexed table, string display)
- What GEMDOS/BIOS calling conventions are used? (stack layout, cleanup)
- How do file operations work? (Fcreate, Fopen, Fread, Fwrite, Fclose patterns)

Explain all 68000 tricks: ROL for nibble rotation, PEA packed params, MOVEM for register save/restore.
```

## Template: Exception Handlers

```
Read {SOURCE} lines {LINES} (CPU Exception Handlers section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- What exception types are handled? (Bus Error, Address Error, Illegal, Div0, CHK, TRAPV, Privilege)
- How is the exception stack frame parsed? (68000 pushes SR+PC; Bus/Addr errors add more)
- How is the faulting address displayed?
- How does it distinguish read vs write access for bus/address errors?
- What message strings are used and where?
- How does control return to the monitor after displaying the exception?
```

## Template: Main Initialization and Command Loop

```
Read {SOURCE} lines {LINES} (Main Initialization and Command Dispatch section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- What is the startup sequence? (basepage save, vector install, table init, screen setup)
- Which exception vectors are installed and where are the handlers?
- How is the main loop structured? (prompt, read char, dispatch)
- What is the command dispatch mechanism? (CMPI.B/BEQ table)
- Map every command character to its handler address and likely function
- How does mode switching work (editor ↔ assembler ↔ debugger)?

For exception vector installation: document which vector (address $XX) gets which handler, and what the original vector is saved to.
```

## Template: Command/Key Dispatch

```
Read {SOURCE} lines {LINES} (Keyboard I/O and Input Processing section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How does the keyboard polling loop work? (Kbshift + Bconstat + Bconin)
- What Atari ST scancodes are checked? (F1=$3B..F10=$44, SF1=$54..SF10=$5D, etc.)
- How are two-key sequences implemented? (read first key → sub-dispatch on second key)
- What does each key/command do? (map scancode → handler → function name)
- How does the UNDO handler work?
- How does search/replace work?

Document the full dispatch table: scancode → handler address → function.
```

## Template: Assembler / Compiler

```
Read {SOURCE} lines {LINES} (Assembler/Compiler section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How many passes? What does each pass do?
- How is the opcode table structured? (entry format: mnemonic + base opcode + mask)
- How are directives detected? (packed ASCII comparison technique)
- How are labels stored? (entry size, fields: name, value, section, flags)
- How is the relocation table built?
- How is the executable header generated? ($601A magic, segment sizes)
- What is the expression parser? (operators, precedence, operand types)
- How are addressing modes encoded?
- What error/warning messages are produced?
```

## Template: Screen Rendering

```
Read {SOURCE} lines {LINES} (Screen Rendering / Display section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How is the video mode detected? (hardware register reads)
- How are screen coordinates converted to memory addresses? (bitplane layout)
- How are characters rendered? (font lookup, pixel writing)
- What is the difference between normal and inverse video?
- How does scrolling work?
- How is the frame buffer cleared?
- Are there multiple font sets for different resolutions?
```

## Template: File I/O and Directory

```
Read {SOURCE} lines {LINES} (File I/O and Directory section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How does file save work? (GEMDOS Fcreate → Fwrite loop → Fclose)
- How does file load work? (GEMDOS Fopen → Fread loop → Fclose)
- How does directory listing work? (Fsetdta → Fsfirst → Fsnext loop)
- What is the DTA (Disk Transfer Area) layout? (filename at +$1E, attrs at +$0B, size at +$1A)
- How are file attributes displayed? (r/o, hidden, system, volume, subdir, archive)
- How are file sizes converted to decimal for display?
- What error handling exists for disk-full, file-not-found, I/O errors?
```

## Template: Debugger / Monitor

```
Read {SOURCE} lines {LINES} (Debugger/Monitor section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How does the register save/restore mechanism work?
- How is the breakpoint mechanism implemented? (opcode replacement + exception catch)
- How does the trace/single-step mechanism work? (SR trace bit)
- How does the built-in disassembler decode instructions?
- How does memory dump display work? (hex + ASCII format)
- How does the memory examine/edit mode work?
- How does "Program tried to escape" detection work? (GEMDOS trap interception)
- What segment information is displayed and where does it come from? (basepage fields)
```

---

## Template: Main Loop (Generic / Adaptive)

```
Read {SOURCE} lines {LINES} (Main Loop section).

Identify the main loop pattern. It will be ONE of these:
- **Command-driven**: prompt → read input → parse → dispatch → loop
- **Frame-driven**: vsync_wait → update_state → render_frame → loop
- **Event-driven**: evnt_multi → switch on event type → handle → loop
- **Interrupt-driven**: install handler → idle loop or Ptermres
- **Sequential**: process data → exit (no loop)

For the identified pattern, determine:
- Where does the loop start and end? (BRA.W back to start)
- What state is reset/initialized at the top of each iteration?
- What is the exit condition?
- What are ALL the dispatched handlers/cases?
  For each: the trigger value (key, event type, timer tick) AND the handler address

List ALL base-register offsets accessed (for the global variable map).
```

## Template: Graphics and Animation

```
Read {SOURCE} lines {LINES} (Graphics/Animation section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- How does the program synchronize with vertical blank?
  (XBIOS Vsync? Polling $FF8209 scanline counter? Timer-B interrupt on specific line?)
- What screen mode is used? How is resolution set/detected?
- Are palette registers ($FF8240-$FF825E) manipulated? What colors/effects?
- Is there double buffering? (Two screen base addresses via Setscreen/Physbase?)
- How are sprites/objects rendered?
  (Shift-and-mask? Pre-shifted lookup tables? Cookie-cut via AND/OR? Line-A $A00C/$A00D?)
- What drawing primitives exist? (Line, circle, fill, bitblit)
- Is there hardware or software scrolling?
- What are the screen address formulas?
  Mono: addr = base + row * 80 + col_byte
  Medium: addr = base + row * 160 + col_word * 4 + plane
  Low: addr = base + row * 160 + col_word * 8 + plane * 2

Explain the Atari ST bitplane layout for non-experts where relevant.
```

## Template: Sound and Music

```
Read {SOURCE} lines {LINES} (Sound/Music section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- Which sound hardware is accessed?
  YM2149 PSG: $FF8800 (register select), $FF8802 (data write)
  DMA sound: $FF8900+ (only on STE/TT/Falcon)
- How are notes/effects sequenced?
  (VBL interrupt? Timer-A/B/C/D? Main loop polling? XBIOS Dosound?)
- What is the music data format? (MOD-like? Custom tracker? MIDI? Dosound command string?)
- How are sound effects triggered? (Direct register writes? Separate effect channel?)
- What YM2149 registers are used? (0-5=tone, 6=noise, 7=mixer, 8-10=volume, 11-13=envelope)
```

## Template: GEM Application

```
Read {SOURCE} lines {LINES} (GEM Application section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- AES initialization: appl_init return value, global[] array contents
- Resource file: rsrc_load filename, rsrc_gaddr for trees/dialogs
- Menu handling: menu_bar setup, menu_tnormal/menu_ienable patterns
- Event loop: evnt_multi mask — which events? (keyboard, button, message, timer)
- Message handling: MN_SELECTED (menu), WM_REDRAW/WM_TOPPED/WM_CLOSED (windows)
- Window management: wind_create flags, wind_set calls, redraw rectangle list handling
- VDI drawing: v_opnvwk parameters, vs_clip setup, drawing calls
- Form/dialog handling: form_center, form_dial, form_do, result processing
- File selector: fsel_input / fsel_exinput usage
```

## Template: Interrupt Handler / TSR

```
Read {SOURCE} lines {LINES} (Interrupt Handler / TSR section).

For EVERY instruction, tell me what it does in context. Format as:
offset | comment

Key things to determine:
- What vectors are installed? Map EACH vector address to its exception type:
  $70 = Level-4 autovector (VBL), $100-$10C = MFP Timer A-D
  $114 = ACIA (keyboard/MIDI), $118 = Timer-C (200 Hz system timer)
  $08 = Bus Error, $84 = TRAP #1 intercept
- How does the handler save/restore all registers? (MOVEM.L at entry/exit)
- What does the handler DO on each invocation?
- How does it chain to the original vector? (saved pointer + JMP/JSR)
- How does it communicate with the main program? (shared variables, semaphore flags)
- Does it use Ptermres ($31) to terminate and stay resident?
- How much memory does it reserve? (Ptermres size parameter)
```
