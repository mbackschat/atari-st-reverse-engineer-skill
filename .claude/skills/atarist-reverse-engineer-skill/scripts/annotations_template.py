"""
Annotation Database Template for Atari ST Binary Disassembly

Copy this file to your tools/ directory as annotations.py, then populate
the dictionaries with comments discovered during code analysis.

BLOCK_COMMENTS: Multi-line comments inserted BEFORE the instruction at the offset.
                Used for subroutine headers, algorithm descriptions, section intros.
                EVERY subroutine must have a block comment — be detailed about the
                algorithm, data structures, arguments, and return values.

INLINE_COMMENTS: Single-line comments appended to the instruction at the offset.
                 Used for per-instruction explanations.
                 CRITICAL: Maintain >=60% comment density from start to finish.
                 Do NOT let density drop off after the first few hundred lines.
                 Every section of the binary must be annotated to the same standard.

DATA_REGIONS:   Regions that contain data (not code) — fonts, string tables, bitmaps,
                lookup tables. These will be rendered as hex dumps instead of
                disassembled instructions.
                CONSERVATIVE: Only add regions you are certain are data. It is far
                worse to mark code as data than to leave data as code.

All dictionaries are keyed by CODE OFFSET (not file offset).
Code offset = file offset - 28 (the 28-byte Atari ST header).
"""

# ============================================================================
# BLOCK COMMENTS — multi-line explanations before subroutines/blocks
# ============================================================================

BLOCK_COMMENTS = {

    # Example: subroutine header with register documentation
    # 0x00020: """; -------------------------------------------------------
    # ; skip_whitespace - Skip whitespace characters in input
    # ; Scans the input string, skipping space, tab, LF, and
    # ; the CP/M end-of-file marker ($1A).
    # ;
    # ; Entry: A0 = pointer into source text
    # ; Exit:  D0.B = next non-whitespace character
    # ;        A0 = advanced past the character
    # ;        Z flag set if end-of-input
    # ; Trashes: (none — all regs preserved except D0/A0)
    # ; -------------------------------------------------------""",

    # Example: logic block explanation
    # 0x00132: """; --- begin: addition handler ---
    # ; Reads the right operand and adds it to the running total
    # ; on the stack. The expression parser loops back here for
    # ; each '+' operator encountered.
    # ; --- end at $013E ---""",

}


# ============================================================================
# INLINE COMMENTS — appended to instruction lines
# ============================================================================

INLINE_COMMENTS = {

    # Example entries showing the expected style:
    # 0x00020: "Read next byte from source string into D0, advance A0 past it",
    # 0x00022: "If byte is zero (null terminator) → jump to return-null handler",
    # 0x00024: "Is it a space ($20)?",
    # 0x00028: "Yes → skip it, loop back to read next byte",
    # 0x00048: "Convert lowercase→uppercase (ASCII trick: 'a'-'A' = $20)",
    # 0x00086: "SWAP D3: move high word to low for 16-bit MULU (68000 trick)",
    # 0x00B12: "PEA $00010002: packed BIOS Bconstat(console) — poll keyboard",
    # 0x00F64: "Save original vector $10 (Illegal Instruction) to save area",

}


# ============================================================================
# DATA REGIONS — areas to render as hex data instead of disassembly
# ============================================================================

DATA_REGIONS = [

    # Format: (start_offset, end_offset, "description")
    # Example:
    # (0x05000, 0x05800, "Font bitmap data - high resolution"),
    # (0x0A000, 0x0A800, "Font bitmap data - medium resolution"),
    # (0x09A00, 0x09D00, "UI string table and help screen text"),

]
