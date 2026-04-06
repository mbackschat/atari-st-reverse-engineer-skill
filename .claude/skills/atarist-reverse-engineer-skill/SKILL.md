---
name: atari-st-reverse-engineer
description: >
  Reverse-engineer an Atari ST (68000) binary: produce annotated disassembly,
  technical analysis with pseudocode, and user manual. Use for .PRG/.TOS/.APP/.ACC files.
argument-hint: path/to/BINARY.PRG
user-invocable: true
---

# Atari ST Binary Reverse-Engineering

You are performing a deep reverse-engineering analysis of an Atari ST (Motorola 68000) binary.

## Arguments

The target binary is: **`$ARGUMENTS`**

If a launcher .PRG and payload binary are separate files, focus on the payload binary — that's where the actual code lives.

## Deliverables

You will produce three files in the working directory:

1. **`SOURCE.txt`** — Fully annotated 68000 disassembly listing with:
   - Named subroutines with block comments (purpose, entry/exit registers, algorithm)
   - Inline comments on every non-trivial instruction
   - Section headers describing each code region
   - System call annotations (GEMDOS/BIOS/XBIOS/AES/VDI/Line-A)
   - String cross-references
   - Data regions (fonts, tables) properly marked

2. **`ANALYSIS.md`** — Technical analysis document covering:
   - Binary structure (header, segments, sizes)
   - Memory layout map (all code regions identified)
   - Execution flow (startup → initialization → main loop)
   - Complete system call inventory
   - Subroutine signatures (entry/exit registers and types)
   - Data structure layouts discovered
   - 68000 coding techniques and idioms used
   - Key algorithms explained with pseudocode

3. **`MANUAL.md`** — User manual (if the binary is an interactive tool):
   - What the program does
   - How to start it
   - All commands, key bindings, modes
   - Error messages and their meanings
   - Quick reference card

Additionally, write a **`CONTEXT.md`** that captures all accumulated knowledge for future sessions.

## Procedure

Follow the detailed step-by-step procedure in [plan.md](${CLAUDE_SKILL_DIR}/plan.md).

**Summary of phases:**

### Phase 1: Setup and Initial Scan
1. Create a `tools/` directory in the working folder
2. Copy `disasm_atari.py` from `${CLAUDE_SKILL_DIR}/scripts/` into `tools/`
3. Set up Python environment: `cd tools && uv init && uv add capstone`
4. Run initial scan: `uv run python disasm_atari.py ../BINARY_FILE --prefix NAME`
5. Review the console output: system calls found, strings extracted, subroutine count

### Phase 2: String Analysis and Section Mapping
1. Read the extracted strings from `analysis.json` — they reveal the program's purpose
2. Identify error messages, prompts, menu items, version strings
3. Map strings to code regions via the LEA PC-relative cross-references
4. Identify the major sections: initialization, main loop, subsystem boundaries

### Phase 3: Deep Code Analysis (use parallel Explore agents)
1. Launch agents to analyze each identified section in parallel
2. For each section: read the disassembly, trace instruction logic, identify algorithms
3. Document subroutine signatures: entry registers, exit values, side effects
4. Follow the annotation guide in [prompts/annotation-guide.md](${CLAUDE_SKILL_DIR}/prompts/annotation-guide.md)
5. Use the section analysis templates in [prompts/analysis-sections.md](${CLAUDE_SKILL_DIR}/prompts/analysis-sections.md)

### Phase 4: Build Annotations and Regenerate
1. Create `tools/annotations.py` with BLOCK_COMMENTS and INLINE_COMMENTS dicts
2. Add block comments for every identified subroutine (purpose, registers)
3. Add inline comments for non-trivial instructions
4. Add entries to KNOWN_SUBS and SECTIONS in the disassembler
5. Regenerate: `cd tools && uv run python disasm_atari.py ../BINARY --prefix NAME`

### Phase 5: Write Documentation
1. Write `ANALYSIS.md` from the analysis findings
2. Write `MANUAL.md` from strings, key handlers, command dispatch analysis
3. Write `CONTEXT.md` capturing all accumulated knowledge

### Phase 6: Review (use parallel reviewer agents)
1. Cross-check TRAP annotations against actual binary bytes
2. Verify string references point to real strings
3. Ensure all error messages and commands are documented
4. Follow the checklist in [prompts/review-checklist.md](${CLAUDE_SKILL_DIR}/prompts/review-checklist.md)

### Phase 7: Pseudocode Generation
1. Identify algorithms and main logic worth pseudocode treatment:
   - Main loop and command dispatch
   - Parsers (expression, number, opcode, directive)
   - Search/sort/hash algorithms
   - State machines (editor modes, assembler passes)
   - Non-trivial math (multiply/divide emulation, coordinate transforms)
   - Any routine whose 68000 implementation obscures the underlying logic
2. For each, write clear pseudocode that:
   - Uses structured `if/else`, `while`, `for`, `switch` constructs
   - Names variables after their purpose, not registers (`cursor_x` not `D3`)
   - Preserves the algorithm's actual logic — do not idealize or simplify away quirks
   - Explains why the code does things the 68000 way where relevant (e.g., "split into 16-bit halves because MULU is 16x16")
3. Add a brief prose explanation before each pseudocode block:
   - What the algorithm does and why it exists
   - What data structures it operates on
   - Key edge cases or surprising behavior
4. Insert the pseudocode blocks into `ANALYSIS.md`:
   - Place each pseudocode in the subsystem analysis section where the routine is discussed
   - Use fenced code blocks with `pseudocode` language tag
   - If a section has multiple related algorithms, group them together

## Reference Material

All reference documentation is bundled with the skill in `${CLAUDE_SKILL_DIR}/reference/`:

| Path | Content | When to Use |
|---|---|---|
| `${CLAUDE_SKILL_DIR}/reference/tos-quick-ref.md` | Condensed TOS quick-reference (all calls, vectors, memory map) | Most annotation work |
| `${CLAUDE_SKILL_DIR}/reference/TOS.TXT` | Complete TOS system call reference (270 KB) | Deep system call analysis |
| `${CLAUDE_SKILL_DIR}/reference/GEMDOS.TXT` | Full GEMDOS reference (file I/O, memory, console) | Annotating TRAP #1 calls |
| `${CLAUDE_SKILL_DIR}/reference/BIOS.TXT` | BIOS quick reference | TRAP #13 overview |
| `${CLAUDE_SKILL_DIR}/reference/BIOS_Calls _Trap_13.TXT` | BIOS Trap #13 detailed reference | Annotating TRAP #13 calls |
| `${CLAUDE_SKILL_DIR}/reference/XBIOS.TXT` | XBIOS reference (screen, mouse, timers, sound) | Annotating TRAP #14 calls |
| `${CLAUDE_SKILL_DIR}/reference/AES.md` | AES reference | GEM application analysis |
| `${CLAUDE_SKILL_DIR}/reference/AES_CALL.TXT` | AES function calls (detailed) | AES call documentation |
| `${CLAUDE_SKILL_DIR}/reference/GDOS_INF.TXT` | GDOS reference | VDI/GDOS driver analysis |
| `${CLAUDE_SKILL_DIR}/reference/68000_Assembly_Language.txt` | 68000 instruction set reference | Understanding opcodes |
| `${CLAUDE_SKILL_DIR}/reference/INTRO68K.txt` | Introduction to 68000 programming | Architecture overview |
| `${CLAUDE_SKILL_DIR}/reference/atari.s` | Atari ST hardware register definitions | Hardware register analysis |
| `${CLAUDE_SKILL_DIR}/reference/SALAD.TXT` | System Assembly Language documentation | System-level assembly patterns |

## Key Technical Context

### Atari ST Executable Header (28 bytes)
```
Offset  Size  Field
$00     2     Magic ($601A)
$02     4     TEXT segment size (code)
$06     4     DATA segment size
$0A     4     BSS segment size
$0E     4     Symbol table size
$12     4     Reserved
$16     4     Flags
$1A     2     Relocation flag ($0000=relocatable, $FFFF=absolute)
```
Code starts at file offset 28 ($1C).

### 68000 Register Conventions (typical for Atari ST programs)
- **A7/SP**: Stack pointer
- **D0-D1**: Scratch (caller-saved), often used for return values
- **D2-D7/A2-A6**: Callee-saved (pushed/popped via MOVEM)
- **A5**: Often used as global base register (PIC technique via `LEA (PC),A5`)

### System Call Patterns
- **GEMDOS** (TRAP #1): `MOVE.W #func,-(SP); [params]; TRAP #1; ADD/LEA SP`
- **BIOS** (TRAP #13): Same, or packed `PEA $XXXXyyyy` (func in high word, param in low)
- **XBIOS** (TRAP #14): Same pattern as BIOS
- **AES** (TRAP #2): `MOVE.W #200,D0; MOVE.L #aes_params,D1; TRAP #2` — function number in control[0] of parameter block
- **VDI** (TRAP #2): `MOVE.W #115,D0; MOVE.L #vdi_params,D1; TRAP #2` — opcode in contrl[0] of parameter block
- **Line-A**: Direct opcodes `$A000`-`$A00F` (init, draw, mouse show/hide)

### Important Instruction Patterns to Recognize
- `$4E41` = TRAP #1 (GEMDOS)
- `$4E42` = TRAP #2 (GEM AES/VDI)
- `$4E4D` = TRAP #13 (BIOS)
- `$4E4E` = TRAP #14 (XBIOS)
- `$4E75` = RTS (subroutine return)
- `$4E73` = RTE (exception return)
- `$A000`-`$A00F` = Line-A calls
- `$601A` = Atari ST executable magic number
