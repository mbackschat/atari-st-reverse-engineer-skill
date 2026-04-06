# Reverse-Engineering Playbook for Atari ST Binaries

This is the step-by-step procedure for producing a fully annotated disassembly, technical analysis, and user manual from an Atari ST binary.

---

## Phase 1: Setup and Initial Reconnaissance

### 1.1 Identify the target
- Determine: which file is the main binary? (Some tools use a launcher .PRG that loads a separate payload file)
- Note the file size, date, any version info visible in `strings` output
- Run `file` command to confirm it's a 68000 executable
- **Verify the header**: Check for the `$601A` magic at file offset 0. If not present:
  - The file may be a raw binary (headerless) — set HEADER_SIZE=0 and determine the load address from the loader or documentation
  - It may use a non-standard packer — check for ICE!, LZ77, XPK signatures
  - .ACC desk accessories have a TOS header but different startup (look for `appl_init` AES call)
  - .TTP files have a normal header but accept command-line arguments

### 1.2 Set up the Python environment
```bash
mkdir -p tools
cp ${CLAUDE_SKILL_DIR}/scripts/disasm_atari.py tools/
cd tools
uv init --name re-tools
uv add capstone
```

### 1.3 Run initial scan
```bash
uv run python disasm_atari.py ../TARGET_BINARY --prefix TOOLNAME
```

This produces:
- Console output with statistics (TRAP count, string count, subroutine count)
- `analysis.json` with structured data
- `../SOURCE.txt` with raw disassembly (no annotations yet)

### 1.4 Extract and review strings
```bash
uv run python disasm_atari.py ../TARGET_BINARY --prefix TOOLNAME --strings-only
```

Or read the `significant_strings` section of `analysis.json`. Strings reveal:
- **Version info**: "V1.0", company names, dates
- **Error messages**: "?syntax error", "file not found"
- **UI prompts**: "SEARCH FOR:", "SAVE FILENAME:"
- **Command names**: Menu items, key labels
- **Assembler mnemonics**: If it's a dev tool

### 1.5 Review system call inventory and determine program type
From the console output, note which TOS calls are used AND what they reveal about the program type:

| System Call Profile | Program Type |
|---|---|
| AES evnt_multi + wind_create + menu_bar + rsrc_load | **GEM desktop application** |
| BIOS Bconin + Kbshift + CMPI dispatch table | **Command-driven tool** (monitor, editor, shell) |
| XBIOS Vsync/Setscreen + Line-A drawing + VBL handler | **Graphics demo or game** |
| XBIOS Giaccess/Dosound + timer interrupt setup | **Music/sound player** |
| GEMDOS Fsfirst/Fsnext + sector read/write | **Disk utility** |
| GEMDOS Ptermres + vector installation only | **TSR / AUTO folder program** |
| XBIOS Initmous + IKBD reads | **Game with joystick/mouse** |
| No main loop, sequential Fopen→process→Fclose | **Batch converter/tool** |

The program type determines which analysis templates to use in Phase 3.

Also note:
- **GEMDOS file ops** (Fcreate, Fopen, Fread, Fwrite, Fclose) → file I/O subsystem
- **GEMDOS console** (Cconout, Crawcin, Cprnout) → user interface
- **GEMDOS memory** (Mshrink, Malloc, Mfree) → memory management
- **BIOS Bconin/Bconout/Bconstat** → direct keyboard/screen I/O
- **BIOS Kbshift** → modifier key detection
- **BIOS Setexc** → exception vector installation (debugger/monitor)
- **AES** (wind_create, form_alert, menu_bar, rsrc_load) → GEM windowed application
- **VDI** (v_opnvwk, v_pline, v_gtext, vs_clip) → GEM graphics output
- **Line-A** → graphics (mouse cursor, drawing primitives)
- **XBIOS** → hardware access (screen mode, sound, floppy)

### 1.6 Identify GEMDOS/BIOS wrapper subroutines
Many programs route all system calls through a single wrapper subroutine. Look for this pattern:
```
MOVE.W #$func, -(SP)   ; push function code
[push parameters]
BSR.W  wrapper_sub      ; call centralized wrapper
ADDQ.L #N, SP           ; clean stack
```
If a wrapper is found: identify all BSR callers of that wrapper and extract their pushed function codes. This reveals indirect system calls the TRAP scanner missed.

---

## Phase 2: Section Identification

### 2.1 Locate the entry point
The first instructions are at offset $0000 (after the 28-byte header). Typical patterns:
- `LEA (PC),An` — establish base register for PIC
- `BRA.W $xxxx` — jump to main initialization
- Zero-filled padding between entry and first real code

### 2.2 Map code regions by string locations
Strings are stored near the code that uses them. Use LEA PC-relative cross-references from `analysis.json` to map:
- Error strings near error handler code
- UI prompts near editor/UI code
- Mnemonic tables near assembler code (if applicable)
- Exception messages near exception handlers
- Version string near initialization code

### 2.3 Identify major subsystems
Look for these patterns. Which ones are present determines the program type and which analysis templates to use:

**Universal patterns (any program):**

| Pattern | Indicates |
|---|---|
| GEMDOS Fsfirst/Fsnext/Fsetdta | Directory listing / file manager |
| GEMDOS Fcreate/Fwrite/Fclose | File save operations |
| GEMDOS Mshrink at startup | Standard TOS memory initialization |
| Line-A $A000 | Graphics initialization |
| Line-A $A009/$A00A pairs | Mouse cursor show/hide around screen updates |
| MOVEM.L at routine entry/exit | Register save/restore (calling convention) |

**Command-driven tools (editors, monitors, shells):**

| Pattern | Indicates |
|---|---|
| Multiple BIOS Bconin + Kbshift calls | Keyboard input handling |
| Large CMPI.B/BEQ tables | Command dispatch or key handler |
| BIOS Setexc calls | Exception handler installation (debugger) |
| `$4AFC` opcode | Breakpoint markers (debugger) |
| `ORI.W #$8000,(SP); RTE` | Trace/single-step mechanism |

**GEM applications:**

| Pattern | Indicates |
|---|---|
| AES appl_init + wind_create + evnt_multi | GEM windowed application main loop |
| AES form_alert / form_do | Dialog box / alert interaction |
| AES rsrc_load + rsrc_gaddr | Resource file (menus, dialogs, icons) |
| VDI v_opnvwk / vs_clip / v_pline / v_gtext | GEM graphics output |

**Games and demos:**

| Pattern | Indicates |
|---|---|
| XBIOS Vsync / Setscreen / Physbase | Frame synchronization, double buffering |
| XBIOS Setpalette / Setcolor | Palette manipulation / color cycling |
| Direct writes to $FF8240-$FF825E | Hardware palette registers |
| Timer-B ($120) or VBL ($70) interrupt setup | Raster effects / music timing |
| XBIOS Giaccess / Dosound | YM2149 sound chip access |
| Joystick IKBD packet reading | Game input |
| Line-A $A00C/$A00D | Sprite drawing |

**TSR / interrupt-driven programs:**

| Pattern | Indicates |
|---|---|
| GEMDOS Ptermres | Terminate and stay resident |
| Writes to exception vectors ($00-$3FF) | Vector installation |
| XBIOS Xbtimer / Mfpint | Timer interrupt setup |

### 2.4 Build the section map
Create a table of offset ranges and their purposes. Start rough, refine as analysis deepens.

---

## Phase 3: Deep Code Analysis

### 3.1 Launch parallel analysis agents
For each identified section, launch an Explore agent with a focused prompt. Use the templates in `${CLAUDE_SKILL_DIR}/prompts/analysis-sections.md`.

**Priority order depends on program type:**

**Command-driven tool** (editor, monitor, shell):
1. Entry + utility routines → 2. Command dispatch / main loop → 3. Key subsystems → 4. I/O wrappers → 5. Screen rendering

**Game or demo:**
1. Entry + init → 2. Main frame loop (vsync/render cycle) → 3. Graphics rendering → 4. Input handling → 5. Sound/music

**GEM application:**
1. Entry + AES init → 2. Event loop (evnt_multi) → 3. Window/menu handlers → 4. VDI drawing → 5. File I/O

**TSR / interrupt handler:**
1. Entry + vector installation → 2. Interrupt handler body → 3. Communication mechanism → 4. Cleanup/uninstall

**Batch tool:**
1. Entry + argument parsing → 2. Main processing loop → 3. File I/O → 4. Output formatting

### 3.3 Collect base-register offsets
As you analyze each section, maintain a running list of EVERY base-register-relative offset accessed in the code. For each, note:
- The offset value (e.g., $663C(A5) or $0A6C(A3))
- The size (byte/word/long — inferred from instruction size suffix)
- What it appears to store (inferred from context: how it's read, written, compared)
- Which routines read/write it

This list becomes the **Global Variable Map** and **State Structure Maps** in ANALYSIS.md. These are among the most valuable analysis artifacts.

### 3.2 For each section, determine:
- **Purpose**: What does this section do?
- **Entry points**: Which subroutines are called from outside?
- **Register conventions**: What's in each register on entry/exit?
- **Data structures**: What memory layouts are used?
- **Algorithms**: What logic/math does it implement?
- **System calls**: What TOS services does it use?
- **68000 tricks**: What coding idioms are employed?

### 3.3 Reconstruct subroutine signatures
For every identified subroutine, document:
```
name: descriptive_name
offset: $XXXX
purpose: One-line description
entry:
  A0: pointer to input buffer
  D0.B: first character
  D2: radix (10=decimal, 16=hex)
exit:
  D1.L: parsed value
  D0.B: next character after parsed value
  carry flag: set on error
trashes: D3, D4
```

### 3.4 Document call sites
When analyzing code that calls subroutines, annotate the call with what parameters are being passed:
```
; Set up: A0 = filename string, D0.W = open mode (0=read)
  bsr.w  file_open    ; file_open(A0:*filename, D0:mode) → D1:handle
```

---

## Phase 4: Build Annotations

### 4.1 Create annotations.py
Copy `${CLAUDE_SKILL_DIR}/scripts/annotations_template.py` to `tools/annotations.py`. Populate it with findings from Phase 3.

### 4.2 Add BLOCK_COMMENTS for every subroutine
Format:
```python
0x01234: """; -------------------------------------------------------
; routine_name - Brief description
; Longer explanation of algorithm/purpose.
;
; Entry: A0 = input, D0 = character
; Exit:  D1 = result
; Trashes: D2, D3
; -------------------------------------------------------""",
```

### 4.3 Add INLINE_COMMENTS for non-trivial instructions
Prioritize:
- All TRAP/system calls (even if auto-annotated, add the parameter context)
- Branch conditions ("If digit >= radix → invalid")
- Magic numbers ("$61 = 'a', start of lowercase range")
- 68000 idioms ("SWAP for 32-bit multiply — MULU is 16×16 only")
- Loop boundaries ("--- begin: scan digits ---")
- Stack frame operations ("Save D2-D7/A2-A6 per calling convention")

### 4.4 Add KNOWN_SUBS entries
Edit `disasm_atari.py` (or the copy in `tools/`) to add the `KNOWN_SUBS` dict entries for all identified subroutines.

### 4.5 Add SECTIONS entries
Add section boundary definitions with multi-line descriptions.

### 4.6 Add DATA_REGIONS entries
In annotations.py, add DATA_REGIONS entries for any known data areas (font bitmaps, string tables, sprite data, lookup tables). The disassembler also auto-detects some data regions, but manual overrides are more precise.

### 4.7 Regenerate
```bash
cd tools && uv run python disasm_atari.py ../TARGET --prefix NAME
```
Verify the output, iterate.

### 4.8 Annotation coverage targets
Aim for these minimum levels:
- **Inline comments**: ≥60% of instruction lines should have a comment. Every CMPI/branch pair, every TRAP call, every structure field access, every magic number must be explained.
- **Block comments**: Every subroutine must have a block comment with purpose, entry/exit registers, and algorithm description.
- **No unexplained magic numbers**: Every hex literal that isn't self-evident (ASCII codes, structure offsets, hardware addresses, flag bits, scancodes) must be decoded in an inline comment.
- **Explain for non-experts**: Where a code pattern depends on Atari ST or 68000-specific knowledge, add a multi-line explanation. Don't just say "Kbshift(-1)" — say "Read keyboard modifier state: bit 0=RShift, 1=LShift, 2=Ctrl, 3=Alt, 4=CapsLock".

Priority order for inline comments:
1. System calls and their parameters (TRAP, Line-A, AES/VDI)
2. Magic numbers and constants (ASCII codes, structure offsets, flag bits, hardware registers)
3. Branch conditions (what the test means in context, not "branch if equal")
4. Loop boundaries (begin/end markers)
5. Algorithm steps (what this instruction does in the larger logic)

---

## Phase 5: Write Documentation

### 5.1 Write ANALYSIS.md
Structure (adapt based on what the binary actually is — not every section applies to every program):

1. **Overview** — what the program is, version, date, publisher, purpose
2. **Background Primer** — brief explanation of relevant Atari ST concepts for non-expert readers:
   - TOS architecture (GEMDOS/BIOS/XBIOS, basepage structure, memory model)
   - Hardware context if relevant (screen RAM layout, sound chip, interrupt system)
   - 68000 essentials for this codebase (register conventions, MULU limitations, CCR usage)
   - Only include what's needed for THIS binary — a game needs screen/sound context, a file utility doesn't
3. **Binary Structure** — header fields, segment sizes, key observations
4. **Memory Layout** — table of all code regions with sizes and purposes
5. **Global Variable Map** — ALL base-register-relative offsets (A5/PC-relative) with size and purpose. Group by subsystem. This is one of the most valuable artifacts.
6. **State Structure Maps** — for every structure pointer (A3, A4, etc.), document EVERY offset accessed in the code with size and purpose
7. **Execution Flow** — startup → init → main loop, with key addresses
8. **System Call Inventory** — all TRAP/Line-A calls with offsets. Include indirect calls via wrappers.
9. **Shared Utility Routines** — dedicated catalog table: name, offset, one-line purpose, entry/exit registers. Then detailed descriptions of non-obvious ones with code examples.
10. **Subsystem Analysis** — one section per major subsystem, each with:
    - Architecture overview
    - Key data structures and their layouts
    - Step-by-step algorithm descriptions (not just "it does X" — walk through the logic)
    - Command/key dispatch tables WITH scancodes/codes AND handler addresses (if applicable)
    - Screen rendering: formulas, bitplane layout, resolution detection, pipeline steps (if applicable)
    - Pseudocode for complex algorithms
11. **Design Patterns** — named patterns with:
    - Actual code snippets from the binary
    - Explanation of WHY this pattern exists (platform constraints, performance, hardware limitations)
    - Where else in the binary it appears
12. **Statistics** — subroutine count, instruction count, comment density

### 5.2 Write MANUAL.md (adapt to program type)
The MANUAL.md structure depends on what kind of program this is:

**Interactive tool** (editor, monitor, shell):
1. Introduction — 2. Getting Started — 3. Commands/Key Reference (complete tables) — 4. Modes and Workflow — 5. Error Messages — 6. Quick Reference Card

**GEM application:**
1. Introduction — 2. Installation — 3. Menu Reference — 4. Dialog Descriptions — 5. File Operations — 6. Preferences/Settings

**Game:**
1. Introduction — 2. Controls (keyboard/joystick mapping) — 3. Gameplay Mechanics — 4. Levels/Modes — 5. Scoring — 6. Technical Notes

**Demo / music player:**
1. What it does — 2. How to run — 3. System Requirements — 4. Technical Notes (effects used, music format)

**TSR / utility:**
1. Purpose — 2. Installation (AUTO folder, etc.) — 3. Configuration — 4. How to remove/disable

**Batch tool:**
1. Purpose — 2. Command-line syntax — 3. Input/Output formats — 4. Error codes

If the binary has no user interaction (self-running demo, boot sector), MANUAL.md may be minimal or omitted entirely.

### 5.3 Write CONTEXT.md
Capture all accumulated knowledge in a structured document that allows resuming work later. Include:
- Project overview, binary structure, memory map
- All system calls with offsets
- All subroutine signatures
- All data structure layouts
- All global variable locations
- Known gaps and future work

---

## Phase 6: Review and Verification

### 6.1 Launch reviewer agents (in parallel)
Use the prompts in `${CLAUDE_SKILL_DIR}/prompts/review-checklist.md`:
- **SOURCE reviewer**: Verify TRAP bytes, string refs, RTS boundaries
- **ANALYSIS reviewer**: Verify claims against binary data
- **MANUAL reviewer**: Cross-check key bindings, commands, error messages

### 6.2 Annotation coverage check
Count inline comments vs total instructions. If coverage is below 50%, go back to Phase 4 and add more comments, prioritizing:
1. Uncommented TRAP/system calls
2. Uncommented magic numbers (CMPI with hex literals)
3. Uncommented structure field accesses (e.g., `$XX(A5)`, `$XX(A3)`)
4. Uncommented branch conditions
5. Data regions still being disassembled as code

Run: `grep -c ';' SOURCE.txt` vs `grep -cE '^\s+[0-9]' SOURCE.txt`

### 6.3 Fix issues found by reviewers
Common issues:
- TRAP annotation mismatches (data region mis-identified as TRAP)
- String spelling differences (backtick vs apostrophe)
- Section boundary off by a few bytes (code before data region)
- Error message count discrepancies

### 6.3 Final regeneration
After all fixes, run the disassembler one final time and verify the output.

---

## Phase 7: Pseudocode Generation

### 7.1 Identify candidates for pseudocode
Review the annotated SOURCE.txt and ANALYSIS.md to select routines where pseudocode adds clarity. Good candidates:

| Category | Examples |
|---|---|
| **Main logic** | Main loop, command dispatch, mode switching |
| **Parsers** | Expression evaluator, number parser, opcode lookup, directive handler |
| **Algorithms** | Search, sort, hash, pattern matching |
| **State machines** | Editor modes, assembler passes, input state tracking |
| **Math emulation** | 32-bit multiply via SWAP+MULU, division, coordinate transforms |
| **Complex I/O** | Screen rendering loops, file format read/write, DTA traversal |
| **Any routine** where 68000 idioms obscure the underlying logic |

### 7.2 Write pseudocode for each
For each selected routine:

1. **Prose introduction** (2-4 sentences): what the algorithm does, what data structures it operates on, any surprising behavior or edge cases

2. **Pseudocode block** using structured constructs:
```pseudocode
function parse_hex_number(source_ptr) -> (value, next_char):
    value = 0
    char = read_byte(source_ptr)
    
    while is_hex_digit(char):
        if char >= 'a':
            char = char - 0x20          // uppercase (68000 SUBI trick)
        digit = char - '0'
        if digit > 9:
            digit = digit - 7           // 'A'..'F' → 10..15
        value = (value << 4) | digit    // shift-and-add (ROL.L #4 idiom)
        char = read_byte(++source_ptr)
    
    return (value, char)
```

**Rules:**
- Use `if/else`, `while`, `for`, `switch` — no goto unless the original truly has irreducible control flow
- Name variables after purpose (`cursor_x`, `line_count`, `opcode_base`), not registers
- Preserve the actual algorithm — don't idealize away quirks or off-by-one behavior
- Note where 68000 constraints shaped the algorithm (e.g., "16-bit multiply requires split" or "byte rotate instead of shift-and-mask")
- Include error paths and edge cases that exist in the real code
- Mark unclear or ambiguous logic with `// TODO: verify` comments

### 7.3 Insert into ANALYSIS.md
- Place each pseudocode block in the **Subsystem Analysis** section where the routine is discussed
- Use fenced code blocks with ` ```pseudocode ` language tag
- If a subsystem has multiple related algorithms (e.g., assembler's expression parser + opcode encoder), group them together under a shared heading
- Add a "Pseudocode" sub-heading within each subsystem section to make them easy to find

### 7.4 Cross-reference with SOURCE.txt
After inserting pseudocode, add offset cross-references so readers can jump between pseudocode and the actual disassembly:
```
> See SOURCE.txt offsets $0A20–$0A8E for the 68000 implementation.
```

---

## Tips from Experience

1. **Strings are your best friend** — they reveal the program's purpose faster than any code analysis
2. **System calls reveal subsystem boundaries** — cluster of file ops = file manager, cluster of Bconin = keyboard handler
3. **The main loop is always there** — find the BRA.W back to the start, that's your main loop
4. **A5 is usually the base register** — `LEA (PC),A5` at the top means all data is accessed A5-relative
5. **BIOS > GEMDOS for real-time I/O** — tools that need fast keyboard response use BIOS Bconin, not GEMDOS Crawcin
6. **Data regions look like garbage** when disassembled — if you see nonsensical instructions, it's probably font data or string tables
7. **The PEA packed pattern is common** — `PEA $000BFFFF` is Kbshift(-1), not a random address push
8. **Exception vectors live at $00-$3FF** — any writes to absolute low-memory addresses are vector installations
9. **ROL.L #8 cycles through bytes** — used for hex display, hash computation, and byte-level processing
10. **Always check the help text** — many Atari ST tools embed their entire help screen as a string block
