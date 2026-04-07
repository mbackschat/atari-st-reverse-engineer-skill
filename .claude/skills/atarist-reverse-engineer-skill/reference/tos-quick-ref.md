# Atari ST TOS Quick Reference

Condensed reference for system calls, vectors, and hardware used in Atari ST binary analysis.

---

## GEMDOS Functions (TRAP #1)

Call convention: push parameters right-to-left, push function number, `TRAP #1`, clean stack.

| Func# | Name | Parameters | Returns | Stack Clean |
|---|---|---|---|---|
| $00 | Pterm0 | (none) | never returns | — |
| $01 | Cconin | (none) | D0.L = char | 2 |
| $02 | Cconout | char.W | (void) | 4 |
| $03 | Cauxin | (none) | D0.L = char | 2 |
| $04 | Cauxout | char.W | (void) | 4 |
| $05 | Cprnout | char.W | D0.W = status | 4 |
| $06 | Crawio | char.W | D0.L = char or 0 | 4 |
| $07 | Crawcin | (none) | D0.L = char (no echo) | 2 |
| $08 | Cnecin | (none) | D0.L = char (no echo, waits) | 2 |
| $09 | Cconws | string.L | (void) | 6 |
| $0A | Cconrs | buffer.L | (void) | 6 |
| $0B | Cconis | (none) | D0.W = -1/0 | 2 |
| $0E | Dsetdrv | drive.W | D0.L = drive map | 4 |
| $19 | Dgetdrv | (none) | D0.W = drive# | 2 |
| $1A | Fsetdta | addr.L | (void) | 6 |
| $20 | Super | stack.L | D0.L = old SSP | 6 |
| $2F | Fgetdta | (none) | D0.L = DTA addr | 2 |
| $30 | Sversion | (none) | D0.W = version | 2 |
| $36 | Dfree | buf.L, drive.W | D0.L = error | 8 |
| $39 | Dcreate | path.L | D0.L = error | 6 |
| $3A | Ddelete | path.L | D0.L = error | 6 |
| $3B | Dsetpath | path.L | D0.L = error | 6 |
| $3C | Fcreate | name.L, attr.W | D0.W = handle | 8 |
| $3D | Fopen | name.L, mode.W | D0.W = handle | 8 |
| $3E | Fclose | handle.W | D0.W = error | 4 |
| $3F | Fread | handle.W, count.L, buf.L | D0.L = bytes read | 12 |
| $40 | Fwrite | handle.W, count.L, buf.L | D0.L = bytes written | 12 |
| $41 | Fdelete | name.L | D0.L = error | 6 |
| $42 | Fseek | offset.L, handle.W, mode.W | D0.L = position | 10 |
| $43 | Fattrib | name.L, flag.W, attr.W | D0.W = attr | 10 |
| $47 | Dgetpath | buf.L, drive.W | D0.W = error | 8 |
| $48 | Malloc | size.L | D0.L = addr | 6 |
| $49 | Mfree | addr.L | D0.L = error | 6 |
| $4A | Mshrink | 0.W, addr.L, size.L | D0.L = error | 12 |
| $4B | Pexec | mode.W, name.L, cmd.L, env.L | D0.L = error | 16 |
| $4C | Pterm | code.W | never returns | — |
| $4E | Fsfirst | name.L, attr.W | D0.L = error | 8 |
| $4F | Fsnext | (none) | D0.L = error | 2 |
| $56 | Frename | 0.W, old.L, new.L | D0.L = error | 12 |
| $57 | Fdatime | buf.L, handle.W, flag.W | D0.L = error | 10 |

### GEMDOS Error Codes
| Code | Meaning |
|---|---|
| -1 | General error |
| -33 | File not found |
| -34 | Path not found |
| -35 | Too many open files |
| -36 | Access denied |
| -39 | Insufficient memory |
| -46 | Invalid drive |

---

## BIOS Functions (TRAP #13)

Call convention: push parameters right-to-left, push function number (word), `TRAP #13`, clean stack.

**Packed PEA pattern**: `PEA $XXXXyyyy` pushes func# (high word) + first param (low word) in one instruction.

| Func# | Name | Parameters | Returns | Description |
|---|---|---|---|---|
| $00 | Getmpb | ptr.L | (void) | Get Memory Parameter Block |
| $01 | Bconstat | dev.W | D0.W = -1/0 | Check device input status |
| $02 | Bconin | dev.W | D0.L = char+scan | Read character from device |
| $03 | Bconout | dev.W, char.W | (void) | Write character to device |
| $04 | Rwabs | flag.W, buf.L, count.W, rec.W, dev.W | D0.L = err | Read/write disk sectors |
| $05 | Setexc | vec#.W, addr.L | D0.L = old addr | Set exception vector |
| $06 | Tickcal | (none) | D0.L = ms/tick | Timer calibration |
| $07 | Getbpb | dev.W | D0.L = BPB ptr | Get BIOS Parameter Block |
| $08 | Bcostat | dev.W | D0.W = -1/0 | Check device output status |
| $09 | Mediach | dev.W | D0.W = status | Check media change |
| $0A | Drvmap | (none) | D0.L = bitmap | Get connected drive bitmap |
| $0B | Kbshift | mode.W | D0.W = state | Get/set keyboard shift state |

### BIOS Device Numbers
| Dev# | Device |
|---|---|
| 0 | Printer (PRT:) |
| 1 | AUX/RS-232 (AUX:) |
| 2 | Console (CON:) |
| 3 | MIDI |
| 4 | Keyboard (IKBD) |
| 5 | Screen (raw) |

### Bconin Return Value (device 2 — console)
```
D0.L = $00 SS 00 AA
         │  │     └── ASCII code (low byte)
         │  └──────── Scancode (high byte of high word)
         └─────────── Always zero
```

### Kbshift Bits
| Bit | Key |
|---|---|
| 0 | Right Shift |
| 1 | Left Shift |
| 2 | Control |
| 3 | Alternate |
| 4 | Caps Lock |
| 5 | Right mouse button (via IKBD) |
| 6 | Left mouse button (via IKBD) |

---

## XBIOS Functions (TRAP #14)

| Func# | Name | Key Parameters | Description |
|---|---|---|---|
| $00 | Initmous | type.W, param.L, vec.L | Initialize mouse |
| $02 | Physbase | (none) | Get physical screen base |
| $03 | Logbase | (none) | Get logical screen base |
| $04 | Getrez | (none) | Get screen resolution (0=low, 1=med, 2=high) |
| $05 | Setscreen | log.L, phys.L, rez.W | Set screen addresses/resolution |
| $06 | Setpalette | pal.L | Set all 16 palette registers |
| $07 | Setcolor | reg.W, color.W | Set one palette register |
| $0F | Rsconf | baud.W, ctrl.W, ucr.W, rsr.W, tsr.W, scr.W | Configure RS-232 |
| $10 | Keytbl | unshift.L, shift.L, caps.L | Get/set key translation tables |
| $11 | Random | (none) | Get 24-bit random number |
| $15 | Cursconf | func.W, rate.W | Configure text cursor |
| $17 | Gettime | (none) | Get system time |
| $22 | Kbdvbase | (none) | Get keyboard vector table |
| $23 | Kbrate | delay.W, rate.W | Set key repeat rate |
| $25 | Vsync | (none) | Wait for vertical sync |
| $26 | Supexec | func.L | Execute function in supervisor mode |

---

## Line-A Functions

Direct opcodes in code (not TRAP-based). The 68000 interprets these as "Line-A emulator" exceptions.

| Opcode | Function | Description |
|---|---|---|
| `$A000` | linea_init | Initialize Line-A, get variable block pointer |
| `$A001` | put_pixel | Draw one pixel |
| `$A002` | get_pixel | Read one pixel |
| `$A003` | draw_line | Draw a line |
| `$A004` | horiz_line | Draw horizontal line |
| `$A005` | filled_rect | Draw filled rectangle |
| `$A006` | filled_poly | Draw filled polygon |
| `$A007` | bitblt | Bit block transfer |
| `$A008` | textblt | Text block transfer |
| `$A009` | show_mouse | Show mouse cursor |
| `$A00A` | hide_mouse | Hide mouse cursor |
| `$A00B` | transform_mouse | Change mouse cursor form |
| `$A00C` | undraw_sprite | Remove sprite |
| `$A00D` | draw_sprite | Draw sprite |
| `$A00E` | copy_raster | Copy raster form |
| `$A00F` | seedfill | Flood fill |

---

## GEM AES Functions (TRAP #2, D0=200)

Call convention: `MOVE.L #aes_params,D1; MOVE.W #200,D0; TRAP #2` — no stack cleanup needed.

Parameter block: AES_Params → Control[5], Global[14], Int_In[16], Int_Out[7], Addr_In[3], Addr_Out[1].
Control[0]=function#, Int_Out[0]=return value.

| Func# | Name | Key Parameters | Description |
|---|---|---|---|
| 10 | appl_init | — | Register app; returns ap_id |
| 19 | appl_exit | — | Deregister app |
| 20 | evnt_keybd | — | Wait for key; Out[0]=key |
| 23 | evnt_mesag | Addr_In[0]=msg_buf | Wait for message |
| 25 | evnt_multi | In[0]=event_flags | Wait for multiple events |
| 30 | menu_bar | In[0]=show; Addr_In[0]=tree | Show/hide menu |
| 42 | objc_draw | In[0]=obj, In[1]=depth; Addr_In[0]=tree | Draw object tree |
| 50 | form_do | In[0]=start; Addr_In[0]=tree | Handle dialog |
| 52 | form_alert | In[0]=default; Addr_In[0]=string | Alert box |
| 54 | form_center | Addr_In[0]=tree | Center dialog |
| 77 | graf_handle | — | Get VDI handle |
| 78 | graf_mouse | In[0]=form | Set mouse shape |
| 100 | wind_create | In[0]=kind, In[1-4]=rect | Create window |
| 101 | wind_open | In[0]=handle, In[1-4]=rect | Open window |
| 102 | wind_close | In[0]=handle | Close window |
| 104 | wind_get | In[0]=handle, In[1]=field | Get attribute |
| 105 | wind_set | In[0]=handle, In[1]=field | Set attribute |
| 107 | wind_update | In[0]=flag(1-4) | Lock/unlock screen |
| 110 | rsrc_load | Addr_In[0]=filename | Load .RSC file |
| 112 | rsrc_gaddr | In[0]=type, In[1]=index | Get resource address |

**evnt_multi flags**: MU_KEYBD=1, MU_BUTTON=2, MU_M1=4, MU_M2=8, MU_MESAG=$10, MU_TIMER=$20

**Key messages**: MN_SELECTED=10, WM_REDRAW=20, WM_TOPPED=21, WM_CLOSED=22, WM_FULLED=23, WM_SIZED=27, WM_MOVED=28, AC_OPEN=40, AC_CLOSE=41, AP_TERM=50

For full GEM reference see `gem-quick-ref.md`.

---

## GEM VDI Functions (TRAP #2, D0=115)

Call convention: `MOVE.L #vdi_params,D1; MOVE.W #115,D0; TRAP #2` — no stack cleanup needed.

Parameter block: VDI_Params → contrl[12], intin[128], ptsin[128], intout[128], ptsout[128].
contrl[0]=opcode, contrl[5]=sub-opcode, contrl[6]=handle.

| Opcode | Name | Description |
|---|---|---|
| 1 | v_opnwk | Open physical workstation |
| 3 | v_clrwk | Clear workstation |
| 6 | v_pline | Draw polyline |
| 8 | v_gtext | Draw text |
| 9 | v_fillarea | Draw filled area |
| 12 | vst_height | Set text height (pixels) |
| 15 | vsl_type | Set line style (1-7) |
| 17 | vsl_color | Set line color |
| 22 | vst_color | Set text color |
| 23 | vsf_interior | Set fill type (0=hollow..4=user) |
| 25 | vsf_color | Set fill color |
| 32 | vswr_mode | Set writing mode (1=replace, 2=transparent, 3=XOR, 4=erase) |
| 100 | v_opnvwk | Open virtual workstation |
| 101 | v_clsvwk | Close virtual workstation |
| 106 | vst_effects | Set text effects (bit field) |
| 109 | vro_cpyfm | Raster copy opaque |
| 114 | vr_recfl | Fill rectangle |
| 125 | v_bar | Draw bar/filled rect |
| 129 | vs_clip | Set clipping (intin[0]=on/off) |
| 134 | vrt_cpyfm | Raster copy transparent |

For full GEM reference see `gem-quick-ref.md`.

---

## 68000 Exception Vector Table

Vectors occupy addresses $000-$3FF in RAM. Each is a 32-bit pointer.

| Address | Vector# | Exception |
|---|---|---|
| $00 | 0 | Reset: Initial SSP |
| $04 | 1 | Reset: Initial PC |
| $08 | 2 | **Bus Error** |
| $0C | 3 | **Address Error** |
| $10 | 4 | **Illegal Instruction** |
| $14 | 5 | **Division by Zero** |
| $18 | 6 | **CHK Instruction** |
| $1C | 7 | **TRAPV Instruction** |
| $20 | 8 | **Privilege Violation** |
| $24 | 9 | **Trace** |
| $28 | 10 | Line-A Emulator |
| $2C | 11 | Line-F Emulator |
| $60 | 24 | Spurious Interrupt |
| $64 | 25 | Level 1 Autovector (TT MFP) |
| $68 | 26 | Level 2 Autovector (HBL) |
| $6C | 27 | Level 3 Autovector |
| $70 | 28 | **Level 4 Autovector** (VBL) |
| $74 | 29 | Level 5 Autovector |
| $78 | 30 | Level 6 Autovector (MFP) |
| $7C | 31 | Level 7 Autovector (NMI) |
| $80 | 32 | TRAP #0 |
| $84 | 33 | **TRAP #1** (GEMDOS) |
| $88 | 34 | TRAP #2 (GEM/AES/VDI) |
| $B4 | 45 | **TRAP #13** (BIOS) |
| $B8 | 46 | **TRAP #14** (XBIOS) |

---

## Atari ST Memory Map (Key Locations)

| Address | Content |
|---|---|
| $000-$3FF | Exception vector table (256 vectors × 4 bytes) |
| $400-$5FF | System variables (TOS) |
| $800+ | TPA (Transient Program Area) — programs load here |
| $FA0000+ | I/O registers (ST MFP, ACIA, etc.) |
| $FF8200+ | Video controller (Shifter) registers |
| $FF8800+ | Sound chip (YM2149/PSG) registers |
| $FFFC00+ | Keyboard/MIDI ACIA registers |

### Key System Variables ($400-$5FF)

| Address | Name | Size | Purpose |
|---|---|---|---|
| $420 | memvalid | L | Memory validity marker ($752019F3) |
| $42E | _bootdev | W | Boot device number |
| $432 | _flock | W | Floppy lock (non-zero = locked) |
| $43E | _fverify | W | Floppy verify flag |
| $44E | _v_bas_ad | L | **Logical screen base address** |
| $462 | _vbclock | L | VBL counter (incremented each VBL) |
| $466 | _frclock | L | Frame counter (free-running) |
| $484 | _conterm | B | Console/keyboard config |
| $4A2 | _phystop | L | Top of physical memory |
| $4A6 | _membot | L | Bottom of free memory |
| $4AA | _memtop | L | Top of free memory |

### Key Hardware Registers

| Address | Register | Purpose |
|---|---|---|
| $FF8201 | vid_bas_h | Screen base address (high byte) |
| $FF8203 | vid_bas_m | Screen base address (mid byte) |
| $FF8260 | vid_rez | **Video resolution** (0=low, 1=med, 2=high) |
| $FF8240-$FF825F | vid_color | 16 palette registers (word each) |
| $FFFC00 | kb_acia_ctrl | Keyboard ACIA control |
| $FFFC02 | kb_acia_data | Keyboard ACIA data |
| $FA01 | **MFP GPIP** | General purpose I/O (bit 7 = mono detect) |

### Atari ST Screen Formats

| Mode | Resolution | Colors | Bitplanes | Bytes/line | Total |
|---|---|---|---|---|---|
| 0 (Low) | 320×200 | 16 | 4 | 160 | 32,000 |
| 1 (Med) | 640×200 | 4 | 2 | 160 | 32,000 |
| 2 (High) | 640×400 | 2 | 1 | 80 | 32,000 |

**Bitplane interleaving** (Med/Low): Words alternate between planes.
- Low: W0P0, W0P1, W0P2, W0P3, W1P0, W1P1, W1P2, W1P3, ...
- Med: W0P0, W0P1, W1P0, W1P1, W2P0, W2P1, ...
- High: Simple linear — 1 bit per pixel, 8 pixels per byte

---

## Atari ST Keyboard Scancodes (Function Keys)

| Key | Scancode | Shift+ |
|---|---|---|
| F1 | $3B | $54 |
| F2 | $3C | $55 |
| F3 | $3D | $56 |
| F4 | $3E | $57 |
| F5 | $3F | $58 |
| F6 | $40 | $59 |
| F7 | $41 | $5A |
| F8 | $42 | $5B |
| F9 | $43 | $5C |
| F10 | $44 | $5D |
| Help | $62 | — |
| Undo | $61 | — |
| Cursor Up | $48 | — |
| Cursor Down | $50 | — |
| Cursor Left | $4B | — |
| Cursor Right | $4D | — |
| Return | $1C | — |
| Backspace | $0E | — |
| Delete | $53 | — |
| Tab | $0F | — |
| Escape | $01 | — |
| Space | $39 | — |

---

## DTA (Disk Transfer Area) Structure

Set by GEMDOS Fsetdta ($1A), filled by Fsfirst ($4E) and Fsnext ($4F).

| Offset | Size | Content |
|---|---|---|
| $00-$14 | 21 | Reserved (used by GEMDOS internally) |
| $15 | 1 | File attributes |
| $16 | 2 | Time (packed: hours×2048 + minutes×32 + seconds/2) |
| $18 | 2 | Date (packed: (year-1980)×512 + month×32 + day) |
| $1A | 4 | File size (bytes, big-endian longword) |
| $1E | 14 | Filename (8.3 format, null-terminated) |

### File Attribute Bits
| Bit | Attribute |
|---|---|
| 0 | Read-only |
| 1 | Hidden |
| 2 | System |
| 3 | Volume label |
| 4 | Subdirectory |
| 5 | Archive |

---

## Atari ST Executable (Basepage) Structure

When TOS loads a program, it creates a basepage at the start of the allocated memory:

| Offset | Size | Content |
|---|---|---|
| $00 | L | Pointer to start of TPA (= basepage address) |
| $04 | L | Pointer to end of TPA |
| $08 | L | **Pointer to TEXT segment** |
| $0C | L | TEXT segment size |
| $10 | L | **Pointer to DATA segment** |
| $14 | L | DATA segment size |
| $18 | L | **Pointer to BSS segment** |
| $1C | L | BSS segment size |
| $20 | L | Pointer to DTA (default = basepage+$80) |
| $24 | L | Pointer to parent's basepage |
| $2C | L | **Pointer to environment string** |
| $80 | 128 | Command line (first byte = length) |
