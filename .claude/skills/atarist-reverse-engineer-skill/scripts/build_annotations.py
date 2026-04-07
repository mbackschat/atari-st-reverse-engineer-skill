#!/usr/bin/env python3
"""
Build annotations.py from analysis.json scaffold + annotation fragment files.

This script:
1. Reads analysis.json to generate scaffold entries (block comment skeletons
   for every subroutine, inline comments for TRAP/Line-A/string-ref calls)
2. Reads all annot_frag_*.py fragment files written by analysis agents
3. Merges them: fragment entries override scaffold entries for the same offset
4. Writes the final annotations.py with all dicts

Usage:
  cd tools && uv run python build_annotations.py [--stats] [--scaffold-only]

Options:
  --stats          Print density statistics after building
  --scaffold-only  Only generate scaffold from analysis.json (skip fragments)
"""

import json
import os
import sys
from glob import glob


def load_analysis_json(path='analysis.json'):
    """Load analysis.json and return the parsed data."""
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run disasm_atari.py first.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def parse_hex(s):
    """Parse a hex string like '0x01234' to an integer."""
    return int(s, 16)


def generate_scaffold(analysis):
    """Generate scaffold annotation dicts from analysis.json data."""
    block_comments = {}
    inline_comments = {}
    known_subs = {}
    sections = []
    data_regions = []

    # BLOCK_COMMENTS: skeleton for every subroutine
    for sub in analysis.get('subroutines', []):
        offset = parse_hex(sub['offset'])
        name = sub['name']
        block_comments[offset] = (
            f"; -------------------------------------------------------\n"
            f"; {name}\n"
            f"; TODO: Describe algorithm and purpose\n"
            f";\n"
            f"; Entry: TODO\n"
            f"; Exit:  TODO\n"
            f"; Trashes: TODO\n"
            f"; -------------------------------------------------------"
        )
        known_subs[offset] = name

    # INLINE_COMMENTS: TRAP calls
    trap_type_names = {1: 'GEMDOS', 13: 'BIOS', 14: 'XBIOS', 2: 'GEM'}
    for tc in analysis.get('trap_calls', []):
        offset = parse_hex(tc['offset'])
        trap_num = tc['trap']
        trap_type = trap_type_names.get(trap_num, f'TRAP#{trap_num}')
        func = tc['func'] if isinstance(tc['func'], int) else parse_hex(tc['func'])
        inline_comments[offset] = (
            f">>> {trap_type} {tc['name']} (${func:02X}) - {tc['desc']}"
        )

    # INLINE_COMMENTS: indirect syscalls (via wrappers)
    for ic in analysis.get('indirect_syscalls', []):
        offset = parse_hex(ic['caller'])
        trap_num = ic['trap']
        trap_type = trap_type_names.get(trap_num, f'TRAP#{trap_num}')
        func = ic['func'] if isinstance(ic['func'], int) else parse_hex(ic['func'])
        inline_comments[offset] = (
            f"indirect {trap_type} {ic['name']} (${func:02X}) via wrapper at {ic['wrapper']}"
        )

    # INLINE_COMMENTS: Line-A calls
    for la in analysis.get('linea_calls', []):
        offset = parse_hex(la['offset'])
        inline_comments[offset] = (
            f">>> Line-A ${la['num']:04X} - {la['name']} - {la['desc']}"
        )

    # INLINE_COMMENTS: LEA PC-relative string references
    for ref in analysis.get('lea_pc_refs', []):
        if ref.get('string'):
            offset = parse_hex(ref['offset'])
            # Don't override TRAP/Line-A comments
            if offset not in inline_comments:
                s = ref['string'][:60].replace('\n', '\\n').replace('\r', '\\r')
                inline_comments[offset] = f'LEA -> "{s}"'

    return block_comments, inline_comments, known_subs, sections, data_regions


def load_fragments(pattern='annot_frag_*.py'):
    """Load all annotation fragment files, returning merged dicts."""
    block_comments = {}
    inline_comments = {}
    known_subs = {}
    sections = []
    data_regions = []

    frag_files = sorted(glob(pattern))
    if not frag_files:
        print("  No fragment files found.")
        return block_comments, inline_comments, known_subs, sections, data_regions

    for frag_path in frag_files:
        ns = {}
        try:
            with open(frag_path) as f:
                exec(f.read(), ns)
        except Exception as e:
            print(f"  WARNING: {frag_path} has errors: {e}")
            continue

        loaded = []
        if 'BLOCK_COMMENTS' in ns and ns['BLOCK_COMMENTS']:
            block_comments.update(ns['BLOCK_COMMENTS'])
            loaded.append(f"{len(ns['BLOCK_COMMENTS'])} block")
        if 'INLINE_COMMENTS' in ns and ns['INLINE_COMMENTS']:
            inline_comments.update(ns['INLINE_COMMENTS'])
            loaded.append(f"{len(ns['INLINE_COMMENTS'])} inline")
        if 'KNOWN_SUBS' in ns and ns['KNOWN_SUBS']:
            known_subs.update(ns['KNOWN_SUBS'])
            loaded.append(f"{len(ns['KNOWN_SUBS'])} subs")
        if 'SECTIONS' in ns and ns['SECTIONS']:
            sections.extend(ns['SECTIONS'])
            loaded.append(f"{len(ns['SECTIONS'])} sections")
        if 'DATA_REGIONS' in ns and ns['DATA_REGIONS']:
            data_regions.extend(ns['DATA_REGIONS'])
            loaded.append(f"{len(ns['DATA_REGIONS'])} data regions")

        print(f"  Loaded {frag_path}: {', '.join(loaded) if loaded else 'empty'}")

    return block_comments, inline_comments, known_subs, sections, data_regions


def merge_data_regions(regions):
    """Sort and merge overlapping data regions."""
    if not regions:
        return []
    # Normalize: ensure (start, end, desc) tuples
    normalized = []
    for r in regions:
        if len(r) >= 3:
            normalized.append((r[0], r[1], r[2]))
        elif len(r) == 2:
            normalized.append((r[0], r[1], ""))
        else:
            continue
    normalized.sort(key=lambda x: x[0])
    merged = [normalized[0]]
    for start, end, desc in normalized[1:]:
        prev_start, prev_end, prev_desc = merged[-1]
        if start <= prev_end + 4:  # merge if within 4 bytes
            merged[-1] = (prev_start, max(prev_end, end),
                          prev_desc if prev_desc else desc)
        else:
            merged.append((start, end, desc))
    return merged


def format_block_comment(text):
    """Format a block comment string for Python source output."""
    # Escape any triple quotes in the text
    safe = text.replace('"""', '""\\"')
    return f'"""{safe}"""'


def write_annotations(path, block_comments, inline_comments, known_subs,
                      sections, data_regions):
    """Write the final annotations.py file."""
    with open(path, 'w') as f:
        f.write('"""\n')
        f.write('Annotation Database for Atari ST Binary Disassembly\n')
        f.write('Generated by build_annotations.py from analysis.json + fragment files.\n')
        f.write('\n')
        f.write('All dictionaries are keyed by CODE OFFSET (not file offset).\n')
        f.write('Code offset = file offset - 28 (the 28-byte Atari ST header).\n')
        f.write('"""\n\n')

        # BLOCK_COMMENTS
        f.write('# ' + '=' * 76 + '\n')
        f.write('# BLOCK COMMENTS\n')
        f.write('# ' + '=' * 76 + '\n\n')
        f.write('BLOCK_COMMENTS = {\n')
        for offset in sorted(block_comments.keys()):
            text = block_comments[offset]
            f.write(f'\n    0x{offset:05X}: {format_block_comment(text)},\n')
        f.write('}\n\n\n')

        # INLINE_COMMENTS
        f.write('# ' + '=' * 76 + '\n')
        f.write('# INLINE COMMENTS\n')
        f.write('# ' + '=' * 76 + '\n\n')
        f.write('INLINE_COMMENTS = {\n')
        for offset in sorted(inline_comments.keys()):
            text = inline_comments[offset]
            # Escape any quotes in the comment
            safe = text.replace('\\', '\\\\').replace('"', '\\"')
            f.write(f'    0x{offset:05X}: "{safe}",\n')
        f.write('}\n\n\n')

        # KNOWN_SUBS
        f.write('# ' + '=' * 76 + '\n')
        f.write('# KNOWN SUBROUTINE NAMES\n')
        f.write('# ' + '=' * 76 + '\n\n')
        f.write('KNOWN_SUBS = {\n')
        for offset in sorted(known_subs.keys()):
            name = known_subs[offset]
            safe = name.replace('"', '\\"')
            f.write(f'    0x{offset:05X}: "{safe}",\n')
        f.write('}\n\n\n')

        # SECTIONS
        f.write('# ' + '=' * 76 + '\n')
        f.write('# SECTION DEFINITIONS\n')
        f.write('# ' + '=' * 76 + '\n\n')
        f.write('SECTIONS = [\n')
        for sec in sorted(sections, key=lambda x: x[0]):
            offset = sec[0]
            # Handle both (offset, name) and (start, end, name) tuple formats
            if len(sec) >= 3 and isinstance(sec[2], str):
                name = sec[2]
            elif len(sec) > 1:
                name = str(sec[1]) if not isinstance(sec[1], str) else sec[1]
            else:
                name = "Unknown"
            safe = name.replace('\\', '\\\\').replace('"', '\\"')
            f.write(f'    (0x{offset:05X}, "{safe}"),\n')
        f.write(']\n\n\n')

        # DATA_REGIONS
        f.write('# ' + '=' * 76 + '\n')
        f.write('# DATA REGIONS\n')
        f.write('# ' + '=' * 76 + '\n\n')
        f.write('DATA_REGIONS = [\n')
        for start, end, desc in data_regions:
            safe = desc.replace('"', '\\"')
            f.write(f'    (0x{start:05X}, 0x{end:05X}, "{safe}"),\n')
        f.write(']\n')


def print_stats(analysis, block_comments, inline_comments, known_subs,
                sections, data_regions):
    """Print annotation density statistics."""
    # Estimate instruction count from code size
    text_size = analysis.get('header', {}).get('text_size', 0)
    last_nz = analysis.get('statistics', {}).get('last_nonzero', '0x0')
    code_bytes = min(text_size, parse_hex(last_nz)) if text_size else parse_hex(last_nz)
    est_instructions = code_bytes // 3  # 68000 avg instruction ~3 bytes

    num_subs = len(analysis.get('subroutines', []))

    print("\n" + "=" * 60)
    print("ANNOTATION STATISTICS")
    print("=" * 60)
    print(f"  Estimated instructions:  ~{est_instructions}")
    print(f"  Subroutines:             {num_subs}")
    print()
    print(f"  Block comments:          {len(block_comments)}")
    print(f"    Coverage:              {len(block_comments)}/{num_subs} subroutines "
          f"({100*len(block_comments)//max(num_subs,1)}%)")
    print()
    print(f"  Inline comments:         {len(inline_comments)}")
    if est_instructions > 0:
        density = 100 * len(inline_comments) / est_instructions
        print(f"    Estimated density:     {density:.1f}%")
        if density < 60:
            print(f"    WARNING: Below 60% target! Need ~{int(est_instructions*0.6) - len(inline_comments)} more comments")
    print()
    print(f"  Known sub names:         {len(known_subs)}")
    print(f"  Sections:                {len(sections)}")
    print(f"  Data regions:            {len(data_regions)}")
    print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Build annotations.py from scaffold + fragments')
    parser.add_argument('--stats', action='store_true', help='Print density statistics')
    parser.add_argument('--scaffold-only', action='store_true',
                        help='Only generate scaffold from analysis.json')
    args = parser.parse_args()

    print("[1] Loading analysis.json...")
    analysis = load_analysis_json()

    print("[2] Generating scaffold from analysis.json...")
    s_blocks, s_inline, s_subs, s_sections, s_data = generate_scaffold(analysis)
    print(f"    Scaffold: {len(s_blocks)} block comments, {len(s_inline)} inline comments, "
          f"{len(s_subs)} sub names")

    # Start with scaffold
    block_comments = dict(s_blocks)
    inline_comments = dict(s_inline)
    known_subs = dict(s_subs)
    sections = list(s_sections)
    data_regions = list(s_data)

    if not args.scaffold_only:
        print("[3] Loading annotation fragments...")
        f_blocks, f_inline, f_subs, f_sections, f_data = load_fragments()

        # Merge: fragments override scaffold
        block_comments.update(f_blocks)
        inline_comments.update(f_inline)
        known_subs.update(f_subs)
        sections.extend(f_sections)
        data_regions.extend(f_data)

        overrides = sum(1 for k in f_blocks if k in s_blocks)
        overrides += sum(1 for k in f_inline if k in s_inline)
        if overrides:
            print(f"    Fragments overrode {overrides} scaffold entries")

    # Deduplicate and sort sections
    seen_offsets = set()
    unique_sections = []
    for sec in sorted(sections, key=lambda x: x[0]):
        if sec[0] not in seen_offsets:
            seen_offsets.add(sec[0])
            unique_sections.append(sec)
    sections = unique_sections

    # Merge overlapping data regions
    if data_regions:
        data_regions = merge_data_regions(data_regions)

    print(f"[4] Writing annotations.py...")
    write_annotations('annotations.py', block_comments, inline_comments,
                      known_subs, sections, data_regions)
    print(f"    Total: {len(block_comments)} block, {len(inline_comments)} inline, "
          f"{len(known_subs)} subs, {len(sections)} sections, {len(data_regions)} data regions")

    if args.stats:
        print_stats(analysis, block_comments, inline_comments, known_subs,
                    sections, data_regions)

    print("\nDone! annotations.py is ready.")


if __name__ == '__main__':
    main()
