# Atari ST Reverse-Engineering Skill

A Claude Code skill that guides the reverse-engineering of Atari ST (Motorola 68000) binaries, producing three deliverables:

- **`SOURCE.txt`** — Fully annotated 68000 disassembly listing
- **`ANALYSIS.md`** — Technical analysis document
- **`MANUAL.md`** — User manual (adapted to program type)

The methodology, prompts, Python tooling, and reference material are generalized to work with any Atari ST binary — not just development tools, but also games, demos, GEM applications, TSRs, and utilities.

---

## Installation

This repo already contains the `.claude/skills/` directory structure. Copy it into your project:

```bash
# Clone the repo
git clone https://github.com/mbackschat/atarist-reverse-engineer-skill.git

# Copy the .claude directory into your project
cp -r atarist-reverse-engineer-skill/.claude your-project/
```

Or, to keep it updatable, add it as a Git submodule at the project root and symlink:

```bash
cd your-project/
git submodule add https://github.com/mbackschat/atarist-reverse-engineer-skill.git vendor/atarist-reverse-engineer-skill
mkdir -p .claude/skills
ln -s ../../vendor/atarist-reverse-engineer-skill/.claude/skills/atarist-reverse-engineer-skill .claude/skills/atarist-reverse-engineer-skill
```

Claude Code automatically discovers `SKILL.md` files under `.claude/skills/` — no additional configuration needed.

Once installed, the skill appears as the `/atari-st-reverse-engineer` slash command.

---

## Quick Start

### As a Claude Code skill

```
/atari-st-reverse-engineer path/to/BINARY.PRG
```

Claude will follow the 7-phase playbook automatically: scan the binary, determine program type, identify sections, analyze code with parallel agents, build annotations, generate all deliverables, review them, and add pseudocode.

### Manual workflow

If you prefer step-by-step control, follow [plan.md](.claude/skills/atarist-reverse-engineer-skill/plan.md) — the full reverse-engineering playbook.

---

## What It Does

The skill orchestrates a complete reverse-engineering pipeline:

```
Binary File (.PRG / .TOS / .ACC / raw)
    │
    ├─ Phase 1: Setup ──────── Copy disassembler, install capstone via uv
    │
    ├─ Phase 2: Initial Scan ── Parse header, extract strings, find system calls,
    │                            map subroutines, auto-detect data regions,
    │                            determine program type (tool/game/demo/GEM/TSR)
    │
    ├─ Phase 3: Deep Analysis ─ Launch parallel agents to analyze each section:
    │                            trace logic, identify algorithms, document
    │                            subroutine signatures (entry/exit registers)
    │
    ├─ Phase 4: Annotate ────── Build annotations.py with block comments
    │                            (routine headers) and inline comments
    │                            (per-instruction explanations), regenerate listing
    │
    ├─ Phase 5: Document ────── Write ANALYSIS.md (technical, with global variable
    │                            maps, utility catalog, design patterns, background
    │                            primer) and MANUAL.md (adapted to program type)
    │
    ├─ Phase 6: Review ──────── Cross-check all deliverables against raw binary
    │                            with parallel reviewer agents; verify annotation
    │                            coverage (target ≥50% of instructions commented)
    │
    └─ Phase 7: Pseudocode ─── Write pseudocode for key algorithms and main logic,
                                 insert into ANALYSIS.md subsystem sections
```

---

## File Structure

```
your-project/
├── .claude/
│   └── skills/
│       └── atarist-reverse-engineer-skill/
│           ├── SKILL.md                           Skill definition (YAML frontmatter + instructions)
│           ├── plan.md                            Step-by-step RE playbook (6 phases, 10 tips)
│           │
│           ├── prompts/
│           │   ├── analysis-sections.md           14 template prompts for code section analysis
│           │   │                                  (generic + tool + GEM + game/demo + sound + TSR)
│           │   ├── annotation-guide.md            Style guide with mandatory decode rules and
│           │   │                                  structure field reference (basepage, DTA, Line-A)
│           │   └── review-checklist.md            4 reviewer agent prompts including coverage check
│           │
│           ├── scripts/
│           │   ├── disasm_atari.py                68000 disassembler & analyzer (Capstone-based)
│           │   ├── annotations_template.py        Starter annotation file with format examples
│           │   └── requirements.txt               Python dependency: capstone>=5.0.7
│           │
│           └── reference/
│               ├── tos-quick-ref.md               Condensed TOS reference (327 lines)
│               ├── TOS.TXT                        Complete TOS system call reference
│               ├── GEMDOS.TXT                     Full GEMDOS reference
│               ├── BIOS.TXT                       BIOS quick reference
│               ├── BIOS_Calls _Trap_13.TXT        BIOS Trap #13 detailed reference
│               ├── XBIOS.TXT                      XBIOS reference
│               ├── AES.md                         AES reference
│               ├── AES_CALL.TXT                   AES function calls (detailed)
│               ├── GDOS_INF.TXT                   GDOS reference
│               ├── SALAD.TXT                      System Assembly Language documentation
│               ├── 68000_Assembly_Language.txt     68000 instruction set reference
│               ├── INTRO68K.txt                   Introduction to 68000 programming
│               └── atari.s                        Atari ST hardware register definitions
│
└── README.md                          This file
```

---

## The Disassembler

`scripts/disasm_atari.py` is a standalone Python tool that reads any Atari ST binary and produces an annotated assembly listing.

### Usage

```bash
# Initial reconnaissance — just show extracted strings
python disasm_atari.py BINARY.PRG --strings-only

# Full disassembly with default prefix
python disasm_atari.py BINARY.PRG --prefix TOOLNAME
```

### What it does automatically

- Parses the 28-byte Atari ST executable header ($601A magic)
- Extracts all printable strings with quality filtering (rejects binary noise)
- **Auto-detects data regions** (fonts, string tables, bitmaps) by heuristic: stretches with no code references or high-density ASCII
- Identifies **TRAP #1** (GEMDOS), **TRAP #13** (BIOS), **TRAP #14** (XBIOS) system calls by scanning backwards from each TRAP instruction to find the function number push
- Identifies **TRAP #2** (GEM AES/VDI) calls by detecting `MOVE.W #200,D0` (AES) or `MOVE.W #115,D0` (VDI), with best-effort function resolution from the parameter block
- Identifies **Line-A** graphics calls ($A000–$A00F)
- Maps all **BSR/JSR** call targets (subroutine entry points)
- Maps all **Bcc/BRA** branch targets
- Finds all **RTS/RTE** instructions (subroutine boundaries)
- Resolves **LEA xxx(PC)** string and data references (exported to analysis.json)
- Produces a Capstone-based disassembly with all the above as annotations

### What you add during analysis

- **`KNOWN_SUBS`** dict: map offsets to meaningful subroutine names
- **`SECTIONS`** list: define section boundaries with descriptions
- **`DATA_REGIONS`** list in annotations.py: manually mark font data, string tables, sprite data (supplements auto-detection)
- **`annotations.py`**: block comments, inline comments, and data regions (loaded from working directory)

### Built-in TOS databases

The disassembler includes complete function databases for:

| Database | Coverage |
|---|---|
| GEMDOS | 38 functions ($00–$57): file I/O, memory, process control, console |
| BIOS | 12 functions ($00–$0B): device I/O, vectors, keyboard |
| XBIOS | 32 functions ($00–$27): screen, mouse, timers, sound, serial, floppy |
| AES | 65+ functions (10–130): windows, menus, dialogs, forms, resources |
| VDI | 50+ functions (1–134): graphics, text, raster, input, attributes |
| Line-A | 16 functions ($A000–$A00F): graphics primitives, mouse cursor |

These automatically annotate every system call in the disassembly.

---

## The Annotation System

Annotations live in a separate `annotations.py` file that the disassembler imports at runtime, keeping analysis knowledge separate from the tool. See `scripts/annotations_template.py` for the format and `prompts/annotation-guide.md` for the style guide.

---

## Tips

1. **Start with strings** — `--strings-only` reveals the program's purpose in seconds
2. **System calls reveal structure** — clusters of file ops = file manager, Bconin = keyboard handler
3. **The main loop always exists** — find the `BRA.W` back to the top, that's your main loop
4. **A5 is usually the base register** — `LEA (PC),A5` at entry means all data is A5-relative
5. **Data looks like garbage** when disassembled — nonsensical instructions = font/string/table data
6. **PEA $XXXX is packed** — `PEA $000BFFFF` = Kbshift(-1), not a random address
7. **Low-memory writes = vectors** — anything writing to $00–$3FF is installing exception handlers
8. **ROL.L #8 cycles bytes** — the 68000 idiom for processing each byte of a longword
9. **Check the help text** — many Atari ST tools embed their entire help screen as a string block
10. **Write CONTEXT.md** — future you will thank present you
