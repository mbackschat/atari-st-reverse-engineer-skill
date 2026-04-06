# Section Analysis Prompt Templates

Use these templates when launching Explore agents to analyze specific code sections. Replace `{SOURCE}` with the path to the SOURCE.txt file and `{LINES}` with the line range.

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
