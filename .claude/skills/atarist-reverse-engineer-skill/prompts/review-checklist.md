# Review Checklist

Spawn these as parallel reviewer agents after generating the deliverables.

---

## Reviewer 1: SOURCE.txt Verification

```
You are a reviewer agent. Cross-check the SOURCE.txt disassembly against the raw binary.

IMPORTANT: Stay within the working directory.

Perform these checks:

1. **TRAP annotations**: Grep for ">>> GEMDOS" and ">>> BIOS" in SOURCE.txt.
   For 5+ TRAP locations, verify the bytes at those offsets in the binary match
   TRAP instructions: 0x4E41 (TRAP #1), 0x4E4D (TRAP #13), 0x4E4E (TRAP #14).
   Run: xxd -s $((0x1C + offset)) -l 2 BINARY_FILE

2. **String references**: Check that string annotations (lines with '-> "...')
   point to actual strings. Verify 3+ by reading hex at the referenced offsets.

3. **RTS boundaries**: Verify that 5+ subroutine ends align with RTS (0x4E75).
   Run: xxd -s $((0x1C + offset)) -l 2 BINARY_FILE

4. **Section boundaries**: Verify 2+ section headers are at reasonable locations.
   Check that font data regions actually contain non-code bitmap patterns.

5. **Line-A calls**: Verify 3+ Line-A annotations (0xA000-0xA00F) match actual bytes.

6. **Data regions**: Verify that areas marked as data (font, strings) are NOT
   being mis-disassembled as code instructions.

Report: what checks passed, what issues found, suggested fixes.
```

## Reviewer 2: ANALYSIS.md Verification

```
You are a reviewer agent. Verify claims in ANALYSIS.md against the raw binary.

IMPORTANT: Stay within the working directory.

Perform these checks:

1. **Header claims**: Verify file size, magic number, segment sizes by reading the
   28-byte header: xxd -l 28 BINARY_FILE

2. **System call count**: Grep SOURCE.txt for ">>> GEMDOS", ">>> BIOS", ">>> XBIOS",
   and ">>> Line-A". Count them. Do they match the analysis claims?

3. **Error/warning messages**: If the analysis lists error messages, verify at least
   5 exist in the binary by searching SOURCE.txt.

4. **Version string**: If the analysis mentions a version string, verify it exists.

5. **Memory layout**: Verify 3+ section boundaries make sense by checking what's at
   those offsets (code vs data vs strings).

6. **Subroutine signatures**: For 3+ documented subroutines, verify the handler
   addresses correspond to actual code (not data regions).

7. **Pseudocode accuracy**: For each pseudocode block in the analysis:
   - Verify the referenced SOURCE.txt offsets exist and contain the described routine
   - Check that control flow (branches, loops) in pseudocode matches the actual Bcc/BRA/DBcc structure
   - Verify variable names map to the correct registers as documented in the subroutine signature
   - Confirm edge cases mentioned in the pseudocode (error paths, boundary checks) have corresponding code

Report: what checks passed, what issues found, suggested corrections.
```

## Reviewer 3: MANUAL.md Verification

```
You are a reviewer agent. Cross-check MANUAL.md against the binary and other deliverables.

IMPORTANT: Stay within the working directory.

Perform these checks:

1. **Key bindings / commands**: If the manual documents key bindings or commands,
   verify they match what's in SOURCE.txt (look for CMPI.B scancode comparisons
   or command dispatch tables).

2. **Error messages**: Verify all error messages listed in the manual actually exist
   in the binary. Grep SOURCE.txt for each one.

3. **Feature claims**: For 3+ features described in the manual, verify the underlying
   code exists in SOURCE.txt (find the handler/routine).

4. **String accuracy**: Check that quoted strings in the manual match the exact
   binary content (including typos like "adress" — preserve original spelling).

5. **Consistency**: Cross-reference the manual against ANALYSIS.md. Do system call
   counts, command lists, and error message counts agree?

Report: what checks passed, what discrepancies found, suggested corrections.
```
