#!/usr/bin/env python3
"""
Atari ST 68000 Binary Disassembler and Analyzer
Generalized reverse-engineering tool for any Atari ST executable.

Usage:
  python disasm_atari.py BINARY_FILE [--prefix NAME] [--strings-only]

Approach: byte-pattern scanning for analysis, Capstone for disassembly listing.

Generalized to work with any Atari ST binary.
"""

import struct
import sys
import os
import json
import re
import argparse
from collections import defaultdict

from capstone import *
from capstone.m68k import *

# ============================================================================
# Configuration
# ============================================================================

HEADER_SIZE = 28  # Standard Atari ST executable header size

# ============================================================================
# TOS System Call Database
# ============================================================================

GEMDOS_CALLS = {
    0x00: ("Pterm0", "Terminate program"),
    0x01: ("Cconin", "Read character from console"),
    0x02: ("Cconout", "Write character to console"),
    0x03: ("Cauxin", "Read character from AUX"),
    0x04: ("Cauxout", "Write character to AUX"),
    0x05: ("Cprnout", "Write character to printer"),
    0x06: ("Crawio", "Direct console I/O"),
    0x07: ("Crawcin", "Raw console input without echo"),
    0x08: ("Cnecin", "Console input without echo"),
    0x09: ("Cconws", "Write string to console"),
    0x0A: ("Cconrs", "Read edited string from console"),
    0x0B: ("Cconis", "Check console input status"),
    0x0E: ("Dsetdrv", "Set default drive"),
    0x10: ("Cconos", "Check console output status"),
    0x11: ("Cprnos", "Check printer output status"),
    0x12: ("Cauxis", "Check AUX input status"),
    0x13: ("Cauxos", "Check AUX output status"),
    0x19: ("Dgetdrv", "Get default drive"),
    0x1A: ("Fsetdta", "Set DTA address"),
    0x20: ("Super", "Enter/exit supervisor mode"),
    0x2A: ("Tgetdate", "Get date"),
    0x2B: ("Tsetdate", "Set date"),
    0x2C: ("Tgettime", "Get time"),
    0x2D: ("Tsettime", "Set time"),
    0x2F: ("Fgetdta", "Get DTA address"),
    0x30: ("Sversion", "Get GEMDOS version"),
    0x31: ("Ptermres", "Terminate and stay resident"),
    0x36: ("Dfree", "Get disk free space"),
    0x39: ("Dcreate", "Create directory"),
    0x3A: ("Ddelete", "Delete directory"),
    0x3B: ("Dsetpath", "Set current directory"),
    0x3C: ("Fcreate", "Create file"),
    0x3D: ("Fopen", "Open file"),
    0x3E: ("Fclose", "Close file"),
    0x3F: ("Fread", "Read from file"),
    0x40: ("Fwrite", "Write to file"),
    0x41: ("Fdelete", "Delete file"),
    0x42: ("Fseek", "Seek file position"),
    0x43: ("Fattrib", "Get/set file attributes"),
    0x45: ("Fdup", "Duplicate file handle"),
    0x46: ("Fforce", "Force file handle"),
    0x47: ("Dgetpath", "Get current directory"),
    0x48: ("Malloc", "Allocate memory"),
    0x49: ("Mfree", "Free memory"),
    0x4A: ("Mshrink", "Shrink memory block"),
    0x4B: ("Pexec", "Load/execute program"),
    0x4C: ("Pterm", "Terminate with return code"),
    0x4E: ("Fsfirst", "Search first"),
    0x4F: ("Fsnext", "Search next"),
    0x56: ("Frename", "Rename file"),
    0x57: ("Fdatime", "Get/set file date/time"),
}

BIOS_CALLS = {
    0x00: ("Getmpb", "Get memory parameter block"),
    0x01: ("Bconstat", "Character device input status"),
    0x02: ("Bconin", "Read character from device"),
    0x03: ("Bconout", "Write character to device"),
    0x04: ("Rwabs", "Read/write absolute sectors"),
    0x05: ("Setexc", "Set exception vector"),
    0x06: ("Tickcal", "Get timer calibration"),
    0x07: ("Getbpb", "Get BIOS parameter block"),
    0x08: ("Bcostat", "Character device output status"),
    0x09: ("Mediach", "Check media change"),
    0x0A: ("Drvmap", "Get drive map"),
    0x0B: ("Kbshift", "Get/set keyboard shift state"),
}

XBIOS_CALLS = {
    0x00: ("Initmous", "Initialize mouse"),
    0x01: ("Ssbrk", "Reserve memory"),
    0x02: ("Physbase", "Get physical screen base"),
    0x03: ("Logbase", "Get logical screen base"),
    0x04: ("Getrez", "Get screen resolution"),
    0x05: ("Setscreen", "Set screen addresses/resolution"),
    0x06: ("Setpalette", "Set palette"),
    0x07: ("Setcolor", "Set color register"),
    0x08: ("Floprd", "Read floppy sector"),
    0x09: ("Flopwr", "Write floppy sector"),
    0x0A: ("Flopfmt", "Format floppy track"),
    0x0C: ("Midiws", "Write string to MIDI"),
    0x0D: ("Mfpint", "Set MFP interrupt"),
    0x0E: ("Iorec", "Get I/O record"),
    0x0F: ("Rsconf", "Configure RS-232"),
    0x10: ("Keytbl", "Get/set keyboard tables"),
    0x11: ("Random", "Get random number"),
    0x12: ("Protobt", "Produce boot sector"),
    0x13: ("Flopver", "Verify floppy sector"),
    0x14: ("Scrdmp", "Output screen dump"),
    0x15: ("Cursconf", "Configure cursor"),
    0x16: ("Settime", "Set system time"),
    0x17: ("Gettime", "Get system time"),
    0x18: ("Bioskeys", "Restore default keyboard tables"),
    0x19: ("Ikbdws", "Write to IKBD"),
    0x1A: ("Jdisint", "Disable MFP interrupt"),
    0x1B: ("Jenabint", "Enable MFP interrupt"),
    0x1C: ("Giaccess", "Access sound chip"),
    0x1D: ("Offgibit", "Clear GI port bit"),
    0x1E: ("Ongibit", "Set GI port bit"),
    0x1F: ("Xbtimer", "Set MFP timer"),
    0x20: ("Dosound", "Set sound parameters"),
    0x21: ("Setprt", "Configure dot matrix printer"),
    0x22: ("Kbdvbase", "Get keyboard vectors"),
    0x23: ("Kbrate", "Set key repeat rate"),
    0x24: ("Prtblk", "Print graphics block to printer"),
    0x25: ("Vsync", "Wait for vertical sync"),
    0x26: ("Supexec", "Execute in supervisor mode"),
    0x27: ("Puntaes", "Remove AES from memory"),
}

AES_CALLS = {
    10: ("appl_init", "Register application with AES"),
    11: ("appl_read", "Read message from event buffer"),
    12: ("appl_write", "Write message to application"),
    13: ("appl_find", "Find application ID by filename"),
    14: ("appl_tplay", "Playback recorded user input"),
    15: ("appl_trecord", "Record user input events"),
    18: ("appl_search", "Search for application"),
    19: ("appl_exit", "Deregister application from AES"),
    20: ("evnt_keybd", "Wait for keyboard event"),
    21: ("evnt_button", "Wait for mouse button event"),
    22: ("evnt_mouse", "Wait for mouse enter/leave rectangle"),
    23: ("evnt_mesag", "Wait for message event"),
    24: ("evnt_timer", "Wait for timer event"),
    25: ("evnt_multi", "Wait for multiple events"),
    26: ("evnt_dclick", "Set/read double-click speed"),
    30: ("menu_bar", "Show/hide menu bar"),
    31: ("menu_icheck", "Check/uncheck menu item"),
    32: ("menu_ienable", "Enable/disable menu item"),
    33: ("menu_tnormal", "Set menu title normal/reverse"),
    34: ("menu_text", "Change menu item text"),
    35: ("menu_register", "Register desk accessory menu item"),
    36: ("menu_popup", "Display popup menu"),
    37: ("menu_attach", "Attach submenu to menu item"),
    38: ("menu_istart", "Set submenu start item"),
    39: ("menu_setting", "Set/get menu settings"),
    40: ("objc_add", "Add object to tree"),
    41: ("objc_delete", "Delete object from tree"),
    42: ("objc_draw", "Draw object tree"),
    43: ("objc_find", "Find object under point"),
    44: ("objc_offset", "Get object screen position"),
    45: ("objc_order", "Reorder object among siblings"),
    46: ("objc_edit", "Edit text in object"),
    47: ("objc_change", "Change object state and redraw"),
    48: ("objc_sysvar", "Get/set object system variables"),
    50: ("form_do", "Handle dialog box interaction"),
    51: ("form_dial", "Reserve/release screen for dialog"),
    52: ("form_alert", "Display alert box"),
    53: ("form_error", "Display GEMDOS error dialog"),
    54: ("form_center", "Center dialog on screen"),
    55: ("form_keybd", "Handle keyboard in form dialog"),
    56: ("form_button", "Handle button click in form dialog"),
    70: ("graf_rubberbox", "Rubber-band box with mouse"),
    71: ("graf_dragbox", "Drag box within rectangle"),
    72: ("graf_movebox", "Animate moving box"),
    73: ("graf_growbox", "Animate expanding box"),
    74: ("graf_shrinkbox", "Animate shrinking box"),
    75: ("graf_watchbox", "Watch box for mouse enter/leave"),
    76: ("graf_slidebox", "Slide box within parent"),
    77: ("graf_handle", "Get AES physical workstation handle"),
    78: ("graf_mouse", "Set mouse pointer form"),
    79: ("graf_mkstate", "Get mouse and keyboard state"),
    80: ("scrp_read", "Read scrap directory path"),
    81: ("scrp_write", "Set scrap directory path"),
    90: ("fsel_input", "File selector dialog"),
    91: ("fsel_exinput", "File selector with title"),
    100: ("wind_create", "Create window"),
    101: ("wind_open", "Open/display window"),
    102: ("wind_close", "Close window"),
    103: ("wind_delete", "Delete window"),
    104: ("wind_get", "Get window attributes"),
    105: ("wind_set", "Set window attributes"),
    106: ("wind_find", "Find window at coordinates"),
    107: ("wind_update", "Lock/unlock screen update"),
    108: ("wind_calc", "Calculate window dimensions"),
    109: ("wind_new", "Delete all application windows"),
    110: ("rsrc_load", "Load resource file"),
    111: ("rsrc_free", "Free resource file"),
    112: ("rsrc_gaddr", "Get resource object address"),
    113: ("rsrc_saddr", "Set resource object address"),
    114: ("rsrc_obfix", "Fix resource object coordinates"),
    115: ("rsrc_rcfix", "Fix resource coordinates (extended)"),
    120: ("shel_read", "Read shell command and tail"),
    121: ("shel_write", "Execute shell command"),
    122: ("shel_get", "Read shell buffer"),
    123: ("shel_put", "Write shell buffer"),
    124: ("shel_find", "Find file in shell path"),
    125: ("shel_envrn", "Search environment string"),
    130: ("appl_getinfo", "Get AES information"),
}

VDI_CALLS = {
    1: ("v_opnwk", "Open physical workstation"),
    2: ("v_clswk", "Close physical workstation"),
    3: ("v_clrwk", "Clear workstation"),
    4: ("v_updwk", "Update workstation"),
    5: ("v_escape", "Escape function (sub-opcode in contrl[5])"),
    6: ("v_pline", "Draw polyline"),
    7: ("v_pmarker", "Draw polymarker"),
    8: ("v_gtext", "Draw graphic text"),
    9: ("v_fillarea", "Draw filled area"),
    10: ("v_cellarray", "Draw cell array"),
    11: ("v_gdp", "Generalized drawing primitive"),
    12: ("vst_height", "Set character height"),
    13: ("vst_rotation", "Set character rotation"),
    14: ("vs_color", "Set color representation"),
    15: ("vsl_type", "Set polyline type"),
    16: ("vsl_width", "Set polyline width"),
    17: ("vsl_color", "Set polyline color"),
    18: ("vsm_type", "Set polymarker type"),
    19: ("vsm_height", "Set polymarker height"),
    20: ("vsm_color", "Set polymarker color"),
    21: ("vst_font", "Set text font"),
    22: ("vst_color", "Set text color"),
    23: ("vsf_interior", "Set fill interior style"),
    24: ("vsf_style", "Set fill style index"),
    25: ("vsf_color", "Set fill color"),
    26: ("vq_color", "Query color representation"),
    27: ("vq_cellarray", "Query cell array"),
    28: ("vrq_locator", "Request locator input"),
    29: ("vrq_valuator", "Request valuator input"),
    30: ("vrq_choice", "Request choice input"),
    31: ("vrq_string", "Request string input"),
    32: ("vswr_mode", "Set writing mode"),
    33: ("vsin_mode", "Set input mode"),
    100: ("v_opnvwk", "Open virtual workstation"),
    101: ("v_clsvwk", "Close virtual workstation"),
    102: ("vq_extnd", "Extended inquire"),
    103: ("v_contourfill", "Contour fill"),
    104: ("vsf_perimeter", "Set fill perimeter visibility"),
    105: ("v_get_pixel", "Get pixel value"),
    106: ("vst_effects", "Set text special effects"),
    107: ("vst_point", "Set character cell height by points"),
    108: ("vsl_ends", "Set polyline end styles"),
    109: ("vro_cpyfm", "Copy raster opaque"),
    110: ("vr_trnfm", "Transform raster form"),
    111: ("vsc_form", "Set mouse cursor form"),
    112: ("vsf_udpat", "Set user-defined fill pattern"),
    113: ("vsl_udsty", "Set user-defined line style"),
    114: ("vr_recfl", "Fill rectangle"),
    115: ("vqin_mode", "Query input mode"),
    116: ("vqt_extent", "Query text extent"),
    117: ("vqt_width", "Query character cell width"),
    118: ("vqt_name", "Query font name"),
    119: ("vq_cellarray", "Query cell array (extended)"),
    120: ("vqf_attributes", "Query fill attributes"),
    121: ("vqm_attributes", "Query polymarker attributes"),
    122: ("vql_attributes", "Query polyline attributes"),
    123: ("vqt_attributes", "Query text attributes"),
    124: ("vst_alignment", "Set text alignment"),
    125: ("v_bar", "Draw filled rectangle"),
    126: ("v_arc", "Draw arc"),
    127: ("v_pieslice", "Draw pie slice"),
    128: ("v_circle", "Draw circle"),
    129: ("vs_clip", "Set clipping rectangle"),
    130: ("vqt_fontinfo", "Query font information"),
    131: ("vst_load_fonts", "Load fonts"),
    132: ("vst_unload_fonts", "Unload fonts"),
    134: ("vrt_cpyfm", "Copy raster transparent"),
}

LINEA_NAMES = {
    0: ("linea_init", "Initialize Line-A"),
    1: ("linea_put_pixel", "Put pixel"),
    2: ("linea_get_pixel", "Get pixel"),
    3: ("linea_line", "Draw line"),
    4: ("linea_hline", "Draw horizontal line"),
    5: ("linea_filled_rect", "Draw filled rectangle"),
    6: ("linea_filled_polygon", "Draw filled polygon"),
    7: ("linea_bitblt", "Bit block transfer"),
    8: ("linea_textblt", "Text block transfer"),
    9: ("linea_show_mouse", "Show mouse cursor"),
    10: ("linea_hide_mouse", "Hide mouse cursor"),
    11: ("linea_transform_mouse", "Transform mouse form"),
    12: ("linea_undraw_sprite", "Undraw sprite"),
    13: ("linea_draw_sprite", "Draw sprite"),
    14: ("linea_copy_raster", "Copy raster form"),
    15: ("linea_seedfill", "Seed fill"),
}

# Exception vector names for Setexc
EXCEPTION_VECTORS = {
    0x02: "Bus Error",
    0x03: "Address Error",
    0x04: "Illegal Instruction",
    0x05: "Division by Zero",
    0x06: "CHK Exception",
    0x07: "TRAPV Exception",
    0x08: "Privilege Violation",
    0x09: "Trace",
    0x0A: "Line-A Emulator",
    0x0B: "Line-F Emulator",
    0x20: "TRAP #0",
    0x21: "TRAP #1",
    0x22: "TRAP #2",
    0x23: "TRAP #3",
    0x24: "TRAP #4",
    0x25: "TRAP #5",
}


# ============================================================================
# Binary Parser
# ============================================================================

class AtariSTBinary:
    def __init__(self, filepath):
        with open(filepath, 'rb') as f:
            self.raw = f.read()

        self.magic = struct.unpack('>H', self.raw[0:2])[0]
        self.text_size = struct.unpack('>I', self.raw[2:6])[0]
        self.data_size = struct.unpack('>I', self.raw[6:10])[0]
        self.bss_size = struct.unpack('>I', self.raw[10:14])[0]
        self.sym_size = struct.unpack('>I', self.raw[14:18])[0]
        self.absflg = struct.unpack('>H', self.raw[26:28])[0]

        self.code = self.raw[HEADER_SIZE:HEADER_SIZE + self.text_size]
        self.image = self.raw[HEADER_SIZE:HEADER_SIZE + self.text_size + self.data_size]

    def word_at(self, offset):
        if 0 <= offset < len(self.code) - 1:
            return struct.unpack('>H', self.code[offset:offset+2])[0]
        return 0

    def sword_at(self, offset):
        if 0 <= offset < len(self.code) - 1:
            return struct.unpack('>h', self.code[offset:offset+2])[0]
        return 0

    def long_at(self, offset):
        if 0 <= offset < len(self.code) - 3:
            return struct.unpack('>I', self.code[offset:offset+4])[0]
        return 0

    def slong_at(self, offset):
        if 0 <= offset < len(self.code) - 3:
            return struct.unpack('>i', self.code[offset:offset+4])[0]
        return 0

    def image_word_at(self, offset):
        """Read word from text+data image (for resolving DATA section references)."""
        if 0 <= offset < len(self.image) - 1:
            return struct.unpack('>H', self.image[offset:offset+2])[0]
        return 0

    def image_long_at(self, offset):
        """Read longword from text+data image (for resolving DATA section references)."""
        if 0 <= offset < len(self.image) - 3:
            return struct.unpack('>I', self.image[offset:offset+4])[0]
        return 0


# ============================================================================
# Byte-pattern based analysis (more reliable than Capstone detail)
# ============================================================================

class BytePatternAnalyzer:
    """Analyzes 68000 binary by direct byte-pattern scanning."""

    def __init__(self, binary):
        self.binary = binary
        self.code = binary.code

        # Results
        self.trap_calls = []       # (offset, trap_num, func_num, name, desc)
        self.indirect_syscalls = [] # (caller_off, trap_num, func_num, name, desc, wrapper_off)
        self.linea_calls = []      # (offset, linea_num, name, desc)
        self.bsr_targets = set()
        self.jsr_targets = set()
        self.bra_targets = set()
        self.branch_targets = set()
        self.rts_locations = set()
        self.lea_pc_refs = {}      # code_offset -> target_offset
        self.strings = {}          # offset -> string
        self.string_xrefs = defaultdict(list)  # string_offset -> [code_offsets]

        # Known data regions (not code)
        self.data_regions = []

    def find_last_nonzero(self):
        for i in range(len(self.code) - 1, -1, -1):
            if self.code[i] != 0:
                return i
        return 0

    def is_in_data_region(self, offset):
        for start, end in self.data_regions:
            if start <= offset < end:
                return True
        return False

    def identify_data_regions(self):
        """Identify data regions from the DATA segment and known strings.

        Atari ST executables define TEXT and DATA segment sizes in the header.
        Code lives in TEXT, data in DATA.  If there's a DATA segment, everything
        after text_size is data.

        Within the TEXT segment, strings are embedded inline (accessed via LEA
        PC-relative).  We use extract_strings() to find their exact locations —
        no heuristic window scanning needed.  Only strings that pass the
        _is_meaningful_string quality filter are marked as data.

        Additional regions can be specified in annotations.py via DATA_REGIONS.
        """
        code = self.code
        text_size = self.binary.text_size
        data_size = self.binary.data_size
        regions = []

        # If there's a separate DATA segment, mark it
        if data_size > 0 and text_size < len(code):
            regions.append((text_size, text_size + data_size))

        # Extract strings and mark each one as a data region.
        # Only mark meaningful strings (real text, not code-byte noise).
        strings = {}
        current = []
        start = -1
        for idx, b in enumerate(code):
            if 0x20 <= b <= 0x7E or b in (0x0A, 0x0D, 0x09):
                if not current:
                    start = idx
                current.append(chr(b))
            else:
                if len(current) >= 4:
                    strings[start] = ''.join(current)
                current = []
                start = -1
        if len(current) >= 4:
            strings[start] = ''.join(current)

        for str_off, s in strings.items():
            # Only mark strings >= 20 chars as data regions.
            # Short strings embedded between instructions are common and
            # harmless when disassembled (they show as dc.w with a string
            # annotation).  Marking them as data risks covering adjacent code.
            if len(s) >= 20 and _is_meaningful_string(s):
                # Include null terminator(s) after the string
                str_end = str_off + len(s)
                while str_end < len(code) and code[str_end] == 0:
                    str_end += 1
                regions.append((str_off, str_end))

        # Sort but do NOT merge — each string is a precise data region.
        # Merging risks bridging across code bytes between adjacent strings.
        regions.sort()

        self.data_regions = regions
        return regions

    def scan_all(self):
        """Perform complete byte-pattern scan."""
        code = self.code
        end = self.find_last_nonzero() + 1

        for i in range(0, end - 1, 2):
            if self.is_in_data_region(i):
                continue

            w = struct.unpack('>H', code[i:i+2])[0]

            # RTS (0x4E75)
            if w == 0x4E75:
                self.rts_locations.add(i)

            # RTE (0x4E73)
            elif w == 0x4E73:
                self.rts_locations.add(i)

            # TRAP #n (0x4E40-0x4E4F)
            elif 0x4E40 <= w <= 0x4E4F:
                trap_num = w & 0x0F
                self._identify_trap(i, trap_num)

            # Line-A (0xA000-0xA00F)
            elif 0xA000 <= w <= 0xA00F:
                la_num = w - 0xA000
                name, desc = LINEA_NAMES.get(la_num, (f"linea_{la_num}", "Unknown"))
                self.linea_calls.append((i, la_num, name, desc))

            # BSR.B (0x61xx, xx != 00 and != FF)
            elif (w & 0xFF00) == 0x6100:
                disp_byte = w & 0xFF
                if disp_byte == 0x00:
                    # BSR.W - 16-bit displacement follows
                    if i + 3 < len(code):
                        disp = self.binary.sword_at(i + 2)
                        target = i + 2 + disp
                        if 0 <= target < len(code):
                            self.bsr_targets.add(target)
                elif disp_byte == 0xFF:
                    pass  # BSR.L on 68020+, not on 68000
                else:
                    # BSR.B - 8-bit displacement
                    disp = disp_byte if disp_byte < 0x80 else disp_byte - 256
                    target = i + 2 + disp
                    if 0 <= target < len(code):
                        self.bsr_targets.add(target)

            # JSR abs.W (0x4EB8) or JSR abs.L (0x4EB9) or JSR d(PC) (0x4EBA)
            elif w == 0x4EBA:
                # JSR d(PC)
                if i + 3 < len(code):
                    disp = self.binary.sword_at(i + 2)
                    target = i + 2 + disp
                    if 0 <= target < len(code):
                        self.jsr_targets.add(target)

            # JSR d(An) patterns: 0x4E90-0x4E97 = JSR (An)
            # 0x4EA8-0x4EAF = JSR d(An)

            # BRA.B (0x60xx)
            elif (w & 0xFF00) == 0x6000:
                disp_byte = w & 0xFF
                if disp_byte == 0x00:
                    if i + 3 < len(code):
                        disp = self.binary.sword_at(i + 2)
                        target = i + 2 + disp
                        if 0 <= target < len(code):
                            self.bra_targets.add(target)
                elif disp_byte != 0xFF:
                    disp = disp_byte if disp_byte < 0x80 else disp_byte - 256
                    target = i + 2 + disp
                    if 0 <= target < len(code):
                        self.bra_targets.add(target)

            # Bcc.B/W (0x6200-0x6FFF, excluding 0x6000 BRA and 0x6100 BSR)
            elif 0x6200 <= (w & 0xFF00) <= 0x6F00:
                disp_byte = w & 0xFF
                if disp_byte == 0x00:
                    if i + 3 < len(code):
                        disp = self.binary.sword_at(i + 2)
                        target = i + 2 + disp
                        if 0 <= target < len(code):
                            self.branch_targets.add(target)
                elif disp_byte != 0xFF:
                    disp = disp_byte if disp_byte < 0x80 else disp_byte - 256
                    target = i + 2 + disp
                    if 0 <= target < len(code):
                        self.branch_targets.add(target)

            # LEA d(PC),An: 0100 1rrr 1111 1010 = 0x41FA | (reg << 9)
            elif (w & 0xF1FF) == 0x41FA:
                if i + 3 < len(code):
                    reg = (w >> 9) & 7
                    disp = self.binary.sword_at(i + 2)
                    target = i + 2 + disp
                    self.lea_pc_refs[i] = target

        # Build branch_targets union
        self.branch_targets = self.branch_targets | self.bra_targets

    def _identify_trap(self, offset, trap_num):
        """Identify TRAP system call by scanning backwards for function number."""
        if trap_num == 2:
            return self._identify_gem_trap(offset)

        # Only handle standard TOS traps
        if trap_num not in (1, 13, 14):
            return

        func_num = None
        for back in range(2, 80, 2):
            check = offset - back
            if check < 0:
                break

            w = self.binary.word_at(check)

            # MOVE.W #imm,-(SP) = 0x3F3C xxxx
            if w == 0x3F3C:
                candidate = self.binary.word_at(check + 2)
                db = {1: GEMDOS_CALLS, 13: BIOS_CALLS, 14: XBIOS_CALLS}[trap_num]
                if candidate in db:
                    func_num = candidate
                    break
                elif candidate < 0x100:
                    func_num = candidate
                    break

            # CLR.W -(SP) = 0x4267 -> pushes 0, i.e. function 0
            if w == 0x4267:
                if trap_num == 1:
                    func_num = 0  # Pterm0
                    break

            # MOVE.L #packed,-(SP) = 0x2F3C xxxxxxxx
            if w == 0x2F3C:
                long_val = self.binary.long_at(check + 2)
                hi = (long_val >> 16) & 0xFFFF
                lo = long_val & 0xFFFF
                db = {1: GEMDOS_CALLS, 13: BIOS_CALLS, 14: XBIOS_CALLS}[trap_num]
                # High word is typically the function number (last pushed = top of stack)
                if hi in db:
                    func_num = hi
                    break
                elif lo in db:
                    func_num = lo
                    break
                break

            # PEA abs.L = 0x4879 xxxxxxxx (used for packed BIOS calls)
            if w == 0x4879:
                long_val = self.binary.long_at(check + 2)
                hi = (long_val >> 16) & 0xFFFF
                lo = long_val & 0xFFFF
                db = {1: GEMDOS_CALLS, 13: BIOS_CALLS, 14: XBIOS_CALLS}[trap_num]
                if hi in db:
                    func_num = hi
                    break
                elif lo in db:
                    func_num = lo
                    break
                break

            # Stop at subroutine boundaries
            if w == 0x4E75 or w == 0x4E73:  # RTS or RTE
                break

        if func_num is not None:
            db = {1: GEMDOS_CALLS, 13: BIOS_CALLS, 14: XBIOS_CALLS}[trap_num]
            if func_num in db:
                name, desc = db[func_num]
            else:
                prefix = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}[trap_num]
                name, desc = f"{prefix}_0x{func_num:02X}", "Unknown function"
            self.trap_calls.append((offset, trap_num, func_num, name, desc))
        else:
            # Function number not found locally — this TRAP may be inside a
            # wrapper subroutine where callers push the function code before BSR.
            # Record it with func=-1 so detect_indirect_syscalls can find wrappers.
            prefix = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}.get(trap_num)
            if prefix:
                self.trap_calls.append((offset, trap_num, -1,
                                        f"{prefix}_wrapper", "Wrapper TRAP (callers push func)"))

    def _identify_gem_trap(self, offset):
        """Identify GEM AES/VDI call from TRAP #2.

        Detection strategy:
        - Tier 1: Scan backwards for MOVE.W #200,D0 (AES) or MOVE.W #115,D0 (VDI)
        - Tier 2: Follow MOVE.L #addr,D1 to parameter block, read control[0]
        - Tier 3: Fall back to generic annotation
        """
        gem_type = None  # 'AES' or 'VDI'
        d1_addr = None

        for back in range(2, 40, 2):
            check = offset - back
            if check < 0:
                break

            w = self.binary.word_at(check)

            # MOVE.W #imm,D0 = 0x303C xxxx
            if w == 0x303C and check + 3 < len(self.code):
                imm = self.binary.word_at(check + 2)
                if imm == 200:   # 0xC8 = AES
                    gem_type = 'AES'
                elif imm == 115:  # 0x73 = VDI
                    gem_type = 'VDI'
                # Found D0 load — stop scanning for it
                if gem_type:
                    break

            # MOVE.L #imm,D1 = 0x223C xxxxxxxx
            if w == 0x223C and d1_addr is None and check + 5 < len(self.code):
                d1_addr = self.binary.long_at(check + 2)

            # Stop at subroutine boundaries or other TRAPs
            if w in (0x4E75, 0x4E73) or (0x4E40 <= w <= 0x4E4F):
                break

        # Try to resolve function number from parameter block
        func_num = None
        if d1_addr is not None:
            func_num = self._resolve_gem_func(d1_addr, gem_type)

        # Build the trap_calls entry
        if gem_type == 'AES':
            db = AES_CALLS
            if func_num is not None and func_num in db:
                name, desc = db[func_num]
            elif func_num is not None:
                name, desc = f"AES_{func_num}", "Unknown AES function"
            else:
                name, desc = "AES_call", "AES function (unresolved)"
                func_num = -1
        elif gem_type == 'VDI':
            db = VDI_CALLS
            if func_num is not None and func_num in db:
                name, desc = db[func_num]
            elif func_num is not None:
                name, desc = f"VDI_{func_num}", "Unknown VDI function"
            else:
                name, desc = "VDI_call", "VDI function (unresolved)"
                func_num = -1
        else:
            name, desc = "GEM_call", "GEM TRAP #2 (unresolved)"
            func_num = -1

        self.trap_calls.append((offset, 2, func_num, name, desc))

    def _resolve_gem_func(self, param_addr, gem_type):
        """Try to read function number from GEM parameter block in binary data.

        The parameter block is 6 longwords (AES) or 5 longwords (VDI).
        The first longword points to the control/contrl array.
        control[0] (first word) is the function opcode.
        """
        image_len = len(self.binary.image)

        # param_addr -> first longword = pointer to control array
        if param_addr < 0 or param_addr + 3 >= image_len:
            return None

        control_ptr = self.binary.image_long_at(param_addr)

        # control[0] = function opcode (word)
        if control_ptr < 0 or control_ptr + 1 >= image_len:
            return None

        func_num = self.binary.image_word_at(control_ptr)

        # Sanity check: is this a plausible function number?
        if func_num == 0:
            return None
        if gem_type == 'AES' and 10 <= func_num <= 135:
            return func_num
        elif gem_type == 'VDI' and 1 <= func_num <= 135:
            return func_num
        elif gem_type is None and 1 <= func_num <= 135:
            return func_num

        return None

    def detect_indirect_syscalls(self):
        """Detect system calls made through wrapper subroutines.

        Many Atari ST programs route all GEMDOS/BIOS/XBIOS calls through a
        single wrapper subroutine.  Pattern at each call site:
            MOVE.W #$func, -(SP)    ; push function code
            [push parameters]
            BSR.W  wrapper_sub      ; call centralized wrapper
            ADDQ.L #N, SP           ; clean stack

        This method finds subroutines that contain a TRAP instruction, then
        scans all BSR/JSR callers of those wrappers to extract the pushed
        function codes — yielding the *indirect* system calls that the direct
        TRAP scanner cannot see.
        """
        code = self.code
        all_subs = sorted(self.bsr_targets | self.jsr_targets)
        if not all_subs or not self.trap_calls:
            return

        # Map each TRAP to its containing wrapper subroutine:
        # the nearest subroutine entry point at or before the TRAP offset.
        wrapper_traps = {}  # wrapper_offset -> (trap_num,)
        for trap_off, trap_num, func_num, name, desc in self.trap_calls:
            # Find nearest preceding subroutine entry
            best = None
            for sub in all_subs:
                if sub <= trap_off:
                    best = sub
                else:
                    break
            if best is not None and best != trap_off:
                wrapper_traps[best] = trap_num

        if not wrapper_traps:
            return

        # Build a map of all BSR/JSR call sites -> target
        call_sites = {}  # caller_offset -> target_offset
        end = self.find_last_nonzero() + 1
        for i in range(0, end - 1, 2):
            if self.is_in_data_region(i):
                continue
            w = struct.unpack('>H', code[i:i+2])[0]

            # BSR.W (0x6100 + 16-bit displacement)
            if w == 0x6100 and i + 3 < len(code):
                disp = self.binary.sword_at(i + 2)
                target = i + 2 + disp
                if target in wrapper_traps:
                    call_sites[i] = target

            # BSR.B (0x61xx, xx != 00, xx != FF)
            elif (w & 0xFF00) == 0x6100:
                disp_byte = w & 0xFF
                if disp_byte != 0x00 and disp_byte != 0xFF:
                    disp = disp_byte if disp_byte < 0x80 else disp_byte - 256
                    target = i + 2 + disp
                    if target in wrapper_traps:
                        call_sites[i] = target

            # JSR d(PC) (0x4EBA)
            elif w == 0x4EBA and i + 3 < len(code):
                disp = self.binary.sword_at(i + 2)
                target = i + 2 + disp
                if target in wrapper_traps:
                    call_sites[i] = target

        # Already-known direct TRAP offsets — skip these
        direct_trap_offsets = {t[0] for t in self.trap_calls}

        # For each call site, scan backwards for the pushed function code
        for caller_off, wrapper_off in sorted(call_sites.items()):
            if caller_off in direct_trap_offsets:
                continue

            trap_num = wrapper_traps[wrapper_off]
            # Skip GEM TRAP #2 — has a different calling convention
            if trap_num == 2:
                continue

            db = {1: GEMDOS_CALLS, 13: BIOS_CALLS, 14: XBIOS_CALLS}.get(trap_num)
            if db is None:
                continue

            func_num = None
            for back in range(2, 60, 2):
                check = caller_off - back
                if check < 0:
                    break

                w = self.binary.word_at(check)

                # MOVE.W #imm, -(SP) = 0x3F3C xxxx
                if w == 0x3F3C:
                    candidate = self.binary.word_at(check + 2)
                    if candidate in db or candidate < 0x100:
                        func_num = candidate
                        break

                # CLR.W -(SP) = 0x4267 -> function 0
                if w == 0x4267:
                    if trap_num == 1:
                        func_num = 0  # Pterm0
                        break

                # PEA packed = 0x4879 xxxxxxxx
                if w == 0x4879:
                    long_val = self.binary.long_at(check + 2)
                    hi = (long_val >> 16) & 0xFFFF
                    lo = long_val & 0xFFFF
                    if hi in db:
                        func_num = hi
                    elif lo in db:
                        func_num = lo
                    break

                # MOVE.L #packed, -(SP) = 0x2F3C xxxxxxxx
                if w == 0x2F3C:
                    long_val = self.binary.long_at(check + 2)
                    hi = (long_val >> 16) & 0xFFFF
                    lo = long_val & 0xFFFF
                    if hi in db:
                        func_num = hi
                    elif lo in db:
                        func_num = lo
                    break

                # Stop at subroutine boundaries
                if w == 0x4E75 or w == 0x4E73:  # RTS or RTE
                    break

            if func_num is not None:
                if func_num in db:
                    name, desc = db[func_num]
                else:
                    prefix = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}[trap_num]
                    name, desc = f"{prefix}_0x{func_num:02X}", "Unknown function"
                self.indirect_syscalls.append(
                    (caller_off, trap_num, func_num, name, desc, wrapper_off))

    def extract_strings(self, min_length=4):
        """Extract printable ASCII strings."""
        strings = {}
        current = []
        start = -1

        for i, b in enumerate(self.code):
            if 0x20 <= b <= 0x7E or b in (0x0A, 0x0D, 0x09):
                if not current:
                    start = i
                current.append(chr(b))
            else:
                if len(current) >= min_length:
                    strings[start] = ''.join(current)
                current = []
                start = -1

        if len(current) >= min_length:
            strings[start] = ''.join(current)

        self.strings = strings

        # Build cross-references: find which LEA instructions reference which strings
        for lea_off, target in self.lea_pc_refs.items():
            # Check if target is near a string start
            for str_off in strings:
                if target == str_off or (target >= str_off and target < str_off + len(strings[str_off])):
                    self.string_xrefs[str_off].append(lea_off)
                    break

        return strings


# ============================================================================
# Capstone-based Listing Generator
# ============================================================================

class ListingGenerator:
    """Generates the annotated assembly listing using Capstone."""

    def __init__(self, binary, analyzer):
        self.binary = binary
        self.analyzer = analyzer
        self.md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)
        self.md.detail = True

        # Build lookup sets for quick annotation
        self.trap_at = {}
        for offset, trap_num, func_num, name, desc in analyzer.trap_calls:
            self.trap_at[offset] = (trap_num, func_num, name, desc)

        self.linea_at = {}
        for offset, la_num, name, desc in analyzer.linea_calls:
            self.linea_at[offset] = (la_num, name, desc)

        # Build subroutine names
        self.subroutines = {}
        self.labels = {}
        self._name_locations()

        # Load annotation database
        self.block_comments = {}
        self.inline_comments = {}
        try:
            from annotations import BLOCK_COMMENTS, INLINE_COMMENTS
            self.block_comments = BLOCK_COMMENTS
            self.inline_comments = INLINE_COMMENTS
            print(f"    Loaded {len(self.block_comments)} block comments, {len(self.inline_comments)} inline comments")
        except ImportError:
            print("    No annotations.py found - generating without inline comments")

        # Load manual data region overrides from annotations
        try:
            from annotations import DATA_REGIONS
            for entry in DATA_REGIONS:
                start, end = entry[0], entry[1]
                self.analyzer.data_regions.append((start, end))
            if DATA_REGIONS:
                # Re-sort and merge after adding manual regions
                regions = sorted(self.analyzer.data_regions)
                merged = [regions[0]]
                for rs, re in regions[1:]:
                    if rs <= merged[-1][1] + 4:
                        merged[-1] = (merged[-1][0], max(merged[-1][1], re))
                    else:
                        merged.append((rs, re))
                self.analyzer.data_regions = merged
                print(f"    Loaded {len(DATA_REGIONS)} manual data regions from annotations")
        except (ImportError, AttributeError):
            pass

    def _name_locations(self):
        """Assign names to all known locations."""
        a = self.analyzer

        # All BSR/JSR targets start as generic names
        all_subs = sorted(a.bsr_targets | a.jsr_targets)
        for addr in all_subs:
            self.subroutines[addr] = f"sub_{addr:05X}"

        # Apply known subroutine names (from code analysis)
        for addr, name in self.KNOWN_SUBS.items():
            self.subroutines[addr] = name

        # Name remaining subroutines that contain TRAP calls
        sorted_subs = sorted(self.subroutines.keys())
        for trap_off, trap_num, func_num, name, desc in a.trap_calls:
            for i, sub_start in enumerate(sorted_subs):
                sub_end = sorted_subs[i+1] if i+1 < len(sorted_subs) else len(self.binary.code)
                if sub_start <= trap_off < sub_end:
                    if self.subroutines[sub_start].startswith('sub_'):
                        prefix = "gem" if trap_num == 2 else "tos"
                        self.subroutines[sub_start] = f"{prefix}_{name}"
                    break

        # Name remaining subroutines based on significant strings they reference
        for lea_off, target in a.lea_pc_refs.items():
            if target in a.strings:
                s = a.strings[target]
                if len(s) >= 6:
                    for i, sub_start in enumerate(sorted_subs):
                        sub_end = sorted_subs[i+1] if i+1 < len(sorted_subs) else len(self.binary.code)
                        if sub_start <= lea_off < sub_end:
                            if self.subroutines[sub_start].startswith('sub_'):
                                clean = re.sub(r'[^a-zA-Z0-9_]', '_', s[:25]).strip('_')[:20]
                                if clean and clean[0].isalpha():
                                    self.subroutines[sub_start] = f"ref_{clean}"
                            break

        # Branch targets as local labels
        for addr in sorted(a.branch_targets):
            if addr not in self.subroutines:
                self.labels[addr] = f"loc_{addr:05X}"

    # Known subroutine names (populated during analysis)
    # Add entries as you identify subroutines: offset -> "name"
    # Example: 0x00020: "skip_whitespace",  # Brief description
    KNOWN_SUBS = {
        0x00000: "entry_point",               # Program entry point
        # Add entries as you identify subroutines during analysis
        # Format: 0xOFFSET: "name",  # Brief description
    }

    # Section definitions for the listing
    # Add entries as you identify code regions during analysis
    # Format: (offset, "Section Name\n";   description line 1\n";   description line 2")
    SECTIONS = [
        (0x0000, "Entry Point"),
    ]

    def generate(self, output_path):
        """Generate the full annotated assembly listing."""
        a = self.analyzer
        last_nonzero = a.find_last_nonzero()
        code = self.binary.code

        with open(output_path, 'w') as f:
            self._write_header(f)

            offset = 0
            prev_section_idx = -1

            while offset <= last_nonzero:
                # Check if we're entering a new section
                prev_section_idx = self._check_section(f, offset, prev_section_idx)

                # Check if this is a data region
                in_data = False
                for ds, de in a.data_regions:
                    if ds <= offset < de:
                        self._write_data_region(f, offset, de)
                        offset = de
                        in_data = True
                        break
                if in_data:
                    continue

                # Write subroutine/label headers
                if offset in self.subroutines:
                    # Block comment goes before the subroutine header if present
                    if offset in self.block_comments:
                        f.write(f"\n{self.block_comments[offset]}\n")
                        f.write(f"{self.subroutines[offset]}:\n")
                    else:
                        f.write(f"\n; ---- {self.subroutines[offset]} ----\n")
                        f.write(f"{self.subroutines[offset]}:\n")
                elif offset in self.labels:
                    # Block comment on labels too
                    if offset in self.block_comments:
                        f.write(f"{self.block_comments[offset]}\n")
                    f.write(f"{self.labels[offset]}:\n")

                # Disassemble one instruction
                try:
                    insns = list(self.md.disasm(code[offset:offset+20], offset, count=1))
                    if insns:
                        insn = insns[0]
                        self._write_instruction(f, insn, offset)
                        offset += insn.size
                    else:
                        # Couldn't disassemble
                        w = self.binary.word_at(offset)
                        comment = self._get_data_comment(offset, w)
                        f.write(f"  {offset:05X}: {code[offset]:02X} {code[offset+1]:02X}               dc.w    ${w:04X}{comment}\n")
                        offset += 2
                except Exception:
                    if offset + 1 < len(code):
                        w = self.binary.word_at(offset)
                        f.write(f"  {offset:05X}: {code[offset]:02X} {code[offset+1]:02X}               dc.w    ${w:04X}\n")
                    offset += 2

            self._write_footer(f, a)

    def _write_header(self, f):
        b = self.binary
        f.write(";=======================================================================\n")
        f.write(f"; Atari ST Binary Disassembly\n")
        f.write(";=======================================================================\n")
        f.write(f"; Header: Magic=${b.magic:04X} Text={b.text_size} Data={b.data_size} "
                f"BSS={b.bss_size} Sym={b.sym_size} Absflg=${b.absflg:04X}\n")
        f.write(f"; Active code ends at: ${ self.analyzer.find_last_nonzero():05X}\n\n")
        f.write("                ORG     $0000\n\n")

    def _check_section(self, f, offset, prev_idx):
        for idx, (sec_off, sec_name) in enumerate(self.SECTIONS):
            if offset == sec_off and idx != prev_idx:
                # Split multi-line section name: first line is the title, rest are description
                lines = sec_name.split('\n')
                f.write(f"\n;{'='*71}\n")
                f.write(f"; Section: {lines[0]} (${sec_off:05X})\n")
                for line in lines[1:]:
                    if not line.startswith(';'):
                        f.write(f"; {line}\n")
                    else:
                        f.write(f"{line}\n")
                f.write(f";{'='*71}\n\n")
                return idx
        return prev_idx

    def _write_instruction(self, f, insn, offset):
        """Write a single disassembled instruction with annotations."""
        # Check for block comment on NON-subroutine offsets
        # (subroutine block comments are handled in the generate() loop)
        if offset in self.block_comments and offset not in self.subroutines:
            for cline in self.block_comments[offset].split('\n'):
                f.write(f"{cline}\n")

        code = self.binary.code
        hex_bytes = ' '.join(f'{b:02X}' for b in code[offset:offset+insn.size])

        if insn.op_str:
            instr = f"{insn.mnemonic:<8s} {insn.op_str}"
        else:
            instr = insn.mnemonic

        comment = ""

        # Priority 1: Manual inline annotation (from annotations database)
        if offset in self.inline_comments:
            comment = f" ; {self.inline_comments[offset]}"

        # Priority 2: TRAP annotation
        elif offset in self.trap_at:
            trap_num, func_num, name, desc = self.trap_at[offset]
            if trap_num == 2:
                # Determine AES/VDI/GEM from the function name
                if name.startswith(("appl_", "evnt_", "menu_", "objc_", "form_",
                                    "graf_", "scrp_", "fsel_", "wind_", "rsrc_",
                                    "shel_", "AES")):
                    trap_type = "AES"
                elif name.startswith(("v_", "vs", "vq", "vr", "VDI")):
                    trap_type = "VDI"
                else:
                    trap_type = "GEM"
                if func_num == -1:
                    comment = f" ; >>> {trap_type} call (function unresolved)"
                else:
                    comment = f" ; >>> {trap_type} {name} ({func_num}) - {desc}"
            else:
                trap_type = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}.get(trap_num, f"TRAP#{trap_num}")
                comment = f" ; >>> {trap_type} {name} (${func_num:02X}) - {desc}"

        # Priority 3: Line-A annotation
        elif offset in self.linea_at:
            la_num, name, desc = self.linea_at[offset]
            comment = f" ; >>> Line-A: {name} - {desc}"

        # Priority 4: LEA PC-relative string reference
        elif offset in self.analyzer.lea_pc_refs:
            target = self.analyzer.lea_pc_refs[offset]
            if target in self.analyzer.strings:
                s = self.analyzer.strings[target][:60].replace('\n', '\\n').replace('\r', '\\r')
                comment = f' ; -> "{s}"'

        # Priority 5: BSR/JSR target name
        elif insn.mnemonic.lower() in ('bsr.b', 'bsr.w', 'bsr', 'jsr'):
            target = self._parse_branch_target(insn)
            if target is not None and target in self.subroutines:
                comment = f" ; call {self.subroutines[target]}"

        f.write(f"  {offset:05X}: {hex_bytes:<24s}  {instr}{comment}\n")

    def _parse_branch_target(self, insn):
        """Parse branch target from Capstone op_str."""
        op = insn.op_str.strip()
        if op.startswith('$'):
            try:
                return int(op[1:], 16)
            except ValueError:
                pass
        if op.startswith('#$'):
            try:
                return int(op[2:], 16)
            except ValueError:
                pass
        return None

    def _write_data_region(self, f, start, end):
        """Write a data region as DC.B/DC.W with string annotations."""
        code = self.binary.code
        a = self.analyzer

        i = start
        while i < end and i < len(code):
            # Check if there's a string at this offset
            if i in a.strings:
                s = a.strings[i]
                # Write as DC.B with string content
                raw_len = len(s)
                safe = s.replace('\n', '\\n').replace('\r', '\\r').replace('"', '\\"')[:60]
                hex_preview = ' '.join(f'{code[j]:02X}' for j in range(i, min(i+8, i+raw_len)))
                f.write(f'  {i:05X}: {hex_preview:<24s}  dc.b    "{safe}"')
                refs = a.string_xrefs.get(i, [])
                if refs:
                    f.write(f'  ; xref: {", ".join(f"${r:05X}" for r in refs[:3])}')
                f.write('\n')
                i += raw_len
                # Skip null terminator
                while i < end and i < len(code) and code[i] == 0:
                    i += 1
            else:
                # Write as hex data
                chunk = min(16, end - i)
                hex_bytes = ' '.join(f'{code[j]:02X}' for j in range(i, i+chunk))
                # Check if it looks like font data
                f.write(f"  {i:05X}: {hex_bytes:<48s}  ; data\n")
                i += chunk

    def _get_data_comment(self, offset, word):
        """Get a comment for a data word."""
        if offset in self.analyzer.strings:
            return f' ; "{self.analyzer.strings[offset][:30]}"'
        return ""

    def _write_footer(self, f, a):
        """Write summary footer."""
        f.write(f"\n\n;{'='*71}\n")
        f.write("; Analysis Summary\n")
        f.write(f";{'='*71}\n\n")
        f.write(f"; Subroutines identified: {len(self.subroutines)}\n")
        f.write(f"; RTS/RTE instructions: {len(a.rts_locations)}\n")
        f.write(f"; BSR targets: {len(a.bsr_targets)}\n")
        f.write(f"; JSR targets: {len(a.jsr_targets)}\n")
        f.write(f"; Branch targets: {len(a.branch_targets)}\n")
        f.write(f"; TRAP system calls: {len(a.trap_calls)}\n")
        f.write(f"; Line-A calls: {len(a.linea_calls)}\n")
        f.write(f"; Strings found: {len(a.strings)}\n\n")

        # String cross-reference table
        f.write(f";{'='*71}\n")
        f.write("; String Cross-Reference Table\n")
        f.write(f";{'='*71}\n\n")
        for str_off in sorted(a.strings.keys()):
            s = a.strings[str_off]
            if len(s) >= 4:
                safe = s.replace('\n', '\\n').replace('\r', '\\r')[:60]
                refs = a.string_xrefs.get(str_off, [])
                ref_str = ', '.join(f'${r:05X}' for r in refs[:5]) if refs else 'no xref'
                f.write(f';  ${str_off:05X}: "{safe}"\n')
                f.write(f';          refs: {ref_str}\n')

        # System call inventory
        f.write(f"\n;{'='*71}\n")
        f.write("; System Call Inventory\n")
        f.write(f";{'='*71}\n\n")

        for trap_off, trap_num, func_num, name, desc in sorted(a.trap_calls):
            if trap_num == 2:
                if name.startswith(("appl_", "evnt_", "menu_", "objc_", "form_",
                                    "graf_", "scrp_", "fsel_", "wind_", "rsrc_",
                                    "shel_", "AES")):
                    trap_type = "AES"
                elif name.startswith(("v_", "vs", "vq", "vr", "VDI")):
                    trap_type = "VDI"
                else:
                    trap_type = "GEM"
                if func_num == -1:
                    f.write(f";  ${trap_off:05X}: {trap_type} call (function unresolved)\n")
                else:
                    f.write(f";  ${trap_off:05X}: {trap_type} {name} ({func_num}) - {desc}\n")
            else:
                trap_type = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}.get(trap_num, f"TRAP#{trap_num}")
                f.write(f";  ${trap_off:05X}: {trap_type} {name} (${func_num:02X}) - {desc}\n")

        for la_off, la_num, name, desc in sorted(a.linea_calls):
            f.write(f";  ${la_off:05X}: Line-A {name} ($A{la_num:03X}) - {desc}\n")

        if a.indirect_syscalls:
            f.write(f"\n;{'-'*71}\n")
            f.write(f"; Indirect System Calls (via wrapper subroutines)\n")
            f.write(f";{'-'*71}\n\n")
            for caller, trap_num, func_num, name, desc, wrapper in sorted(a.indirect_syscalls):
                trap_type = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}.get(trap_num, f"TRAP#{trap_num}")
                f.write(f";  ${caller:05X}: {trap_type} {name} (${func_num:02X}) - {desc}"
                        f"  [via wrapper ${wrapper:05X}]\n")


# ============================================================================
# Helpers
# ============================================================================

def _is_meaningful_string(s):
    """Score whether a string looks like real text vs binary noise."""
    if len(s) < 6:
        return False
    printable = sum(1 for c in s if c.isalnum() or c in ' .,;:!?()-+*/=<>@#$%&_"\'')
    alpha = sum(1 for c in s if c.isalpha())
    # At least 70% printable, at least 40% alphabetic
    if not ((printable / len(s) >= 0.7) and (alpha / len(s) >= 0.4)):
        return False
    # Filter out strings that look like 68000 instruction byte patterns.
    # Common false positives: "Nu" (RTS=$4E75), "NV" (LINK=$4E56),
    # "N^" (UNLK=$4E5E), "Nq" (NOP=$4E71), "Hn" (MOVEM), "/?" (MOVE to stack)
    noise_patterns = ('NuNV', 'NVH', 'N^Nu', 'NqNu', 'HnNV', 'Nu/', 'NV\x00',
                       'p\x00Nu', '/\x00N')
    for pat in noise_patterns:
        if pat in s:
            return False
    # Reject strings dominated by repeated 2-char fragments (instruction pairs)
    if len(s) >= 8:
        bigrams = [s[i:i+2] for i in range(0, len(s)-1, 2)]
        unique_ratio = len(set(bigrams)) / len(bigrams)
        if unique_ratio < 0.3:
            return False
    return True


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Atari ST 68000 Binary Disassembler and Analyzer"
    )
    parser.add_argument("binary", help="Path to the Atari ST binary file")
    parser.add_argument("--prefix", default="TOOL",
                        help="Output filename prefix (default: TOOL)")
    parser.add_argument("--strings-only", action="store_true",
                        help="Only extract and display strings, then exit")
    args = parser.parse_args()

    print(f"Atari ST Disassembler and Analyzer")
    print("=" * 50)

    binary = AtariSTBinary(args.binary)
    print(f"Loaded: {len(binary.raw)} bytes total, {binary.text_size} bytes code")

    # Phase 1: Byte-pattern analysis
    analyzer = BytePatternAnalyzer(binary)

    # First pass: scan WITHOUT data regions so we discover code references
    print("\n[1] Scanning byte patterns (first pass)...")
    analyzer.scan_all()

    # Now identify data regions using the discovered code references
    print("[2] Identifying data regions...")
    analyzer.identify_data_regions()
    print(f"    {len(analyzer.data_regions)} data regions marked")

    # Second pass: re-scan with data regions excluded to remove false positives
    analyzer.rts_locations.clear()
    analyzer.bsr_targets.clear()
    analyzer.jsr_targets.clear()
    analyzer.branch_targets.clear()
    analyzer.bra_targets.clear()
    analyzer.trap_calls.clear()
    analyzer.linea_calls.clear()
    analyzer.lea_pc_refs.clear()
    analyzer.scan_all()
    print(f"    {len(analyzer.rts_locations)} RTS/RTE instructions")
    print(f"    {len(analyzer.bsr_targets)} BSR targets")
    print(f"    {len(analyzer.jsr_targets)} JSR targets")
    print(f"    {len(analyzer.branch_targets)} branch targets")
    print(f"    {len(analyzer.trap_calls)} TRAP system calls")
    print(f"    {len(analyzer.linea_calls)} Line-A calls")
    print(f"    {len(analyzer.lea_pc_refs)} LEA PC-relative references")

    print("[3] Extracting strings...")
    analyzer.extract_strings()
    print(f"    {len(analyzer.strings)} strings found")

    # Strings-only mode: just show strings and exit
    if args.strings_only:
        print("\n--- Extracted Strings (length >= 6, meaningful) ---")
        for offset in sorted(analyzer.strings.keys()):
            s = analyzer.strings[offset]
            if _is_meaningful_string(s):
                safe = s.replace('\n', '\\n').replace('\r', '\\r')[:80]
                print(f"  ${offset:05X}: \"{safe}\"")
        return

    print("[3b] Detecting indirect system calls through wrappers...")
    analyzer.detect_indirect_syscalls()
    print(f"    {len(analyzer.indirect_syscalls)} indirect system calls found")

    # Print system call summary
    print("\n--- System Call Summary ---")
    gemdos = [(o,n,f,nm,d) for o,n,f,nm,d in analyzer.trap_calls if n == 1 and f >= 0]
    bios = [(o,n,f,nm,d) for o,n,f,nm,d in analyzer.trap_calls if n == 13 and f >= 0]
    xbios = [(o,n,f,nm,d) for o,n,f,nm,d in analyzer.trap_calls if n == 14 and f >= 0]
    gem = [(o,n,f,nm,d) for o,n,f,nm,d in analyzer.trap_calls if n == 2]

    if gemdos:
        print(f"\n  GEMDOS (TRAP #1): {len(gemdos)} calls")
        for off, _, func, name, desc in sorted(gemdos):
            print(f"    ${off:05X}: {name} (${func:02X}) - {desc}")

    if bios:
        print(f"\n  BIOS (TRAP #13): {len(bios)} calls")
        for off, _, func, name, desc in sorted(bios):
            print(f"    ${off:05X}: {name} (${func:02X}) - {desc}")

    if xbios:
        print(f"\n  XBIOS (TRAP #14): {len(xbios)} calls")
        for off, _, func, name, desc in sorted(xbios):
            print(f"    ${off:05X}: {name} (${func:02X}) - {desc}")

    if gem:
        print(f"\n  GEM AES/VDI (TRAP #2): {len(gem)} calls")
        for off, _, func, name, desc in sorted(gem):
            if func == -1:
                print(f"    ${off:05X}: {name} - {desc}")
            else:
                print(f"    ${off:05X}: {name} ({func}) - {desc}")

    print(f"\n  Line-A: {len(analyzer.linea_calls)} calls")
    for off, num, name, desc in sorted(analyzer.linea_calls):
        print(f"    ${off:05X}: {name} ($A{num:03X}) - {desc}")

    if analyzer.indirect_syscalls:
        print(f"\n  Indirect system calls (via wrappers): {len(analyzer.indirect_syscalls)}")
        for caller, trap_num, func_num, name, desc, wrapper in sorted(analyzer.indirect_syscalls):
            trap_type = {1: "GEMDOS", 13: "BIOS", 14: "XBIOS"}.get(trap_num, f"TRAP#{trap_num}")
            print(f"    ${caller:05X}: {trap_type} {name} (${func_num:02X}) - {desc}"
                  f"  [via ${wrapper:05X}]")

    # Phase 2: Generate listing
    output_dir = os.path.join(os.path.dirname(__file__), '..')

    source_filename = "SOURCE.txt"
    print(f"\n[4] Generating {source_filename}...")
    gen = ListingGenerator(binary, analyzer)
    source_path = os.path.join(output_dir, source_filename)
    gen.generate(source_path)
    print(f"    Written to {source_path}")
    print(f"    {len(gen.subroutines)} named subroutines")

    # Phase 3: Save analysis data
    analysis_path = os.path.join(os.path.dirname(__file__), 'analysis.json')
    analysis = {
        'header': {
            'magic': f'0x{binary.magic:04X}',
            'text_size': binary.text_size,
            'data_size': binary.data_size,
            'bss_size': binary.bss_size,
            'sym_size': binary.sym_size,
            'absflg': f'0x{binary.absflg:04X}',
        },
        'statistics': {
            'last_nonzero': f'0x{analyzer.find_last_nonzero():X}',
            'rts_count': len(analyzer.rts_locations),
            'bsr_targets': len(analyzer.bsr_targets),
            'jsr_targets': len(analyzer.jsr_targets),
            'branch_targets': len(analyzer.branch_targets),
            'trap_calls': len(analyzer.trap_calls),
            'indirect_syscalls': len(analyzer.indirect_syscalls),
            'linea_calls': len(analyzer.linea_calls),
            'strings': len(analyzer.strings),
            'subroutines': len(gen.subroutines),
        },
        'trap_calls': [
            {'offset': f'0x{o:05X}', 'trap': n, 'func': f, 'name': nm, 'desc': d}
            for o, n, f, nm, d in sorted(analyzer.trap_calls)
        ],
        'indirect_syscalls': [
            {
                'caller': f'0x{caller:05X}',
                'trap': trap_num,
                'func': func_num,
                'name': nm,
                'desc': d,
                'wrapper': f'0x{wrapper:05X}',
            }
            for caller, trap_num, func_num, nm, d, wrapper
            in sorted(analyzer.indirect_syscalls)
        ],
        'linea_calls': [
            {'offset': f'0x{o:05X}', 'num': n, 'name': nm, 'desc': d}
            for o, n, nm, d in sorted(analyzer.linea_calls)
        ],
        'subroutines': [
            {'offset': f'0x{k:05X}', 'name': v}
            for k, v in sorted(gen.subroutines.items())
        ],
        # lea_pc_refs format: [{"offset": "0xHHHHH", "target": "0xHHHHH", "string": "..."}, ...]
        'lea_pc_refs': [
            {
                'offset': f'0x{off:05X}',
                'target': f'0x{target:05X}',
                'string': analyzer.strings.get(target, '')[:80]
            }
            for off, target in sorted(analyzer.lea_pc_refs.items())
        ],
        'significant_strings': [
            {'offset': f'0x{k:05X}', 'text': v[:80]}
            for k, v in sorted(analyzer.strings.items())
            if _is_meaningful_string(v)
        ],
    }

    print(f"\n[5] Saving analysis.json...")
    with open(analysis_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"    Written to {analysis_path}")

    print("\nDone!")
    return analyzer, gen, analysis


if __name__ == '__main__':
    main()
