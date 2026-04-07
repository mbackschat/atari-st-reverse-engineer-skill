# GEM (AES/VDI) Quick Reference for Annotation

Condensed reference for annotating GEM application binaries. For full details see `AES.md` and `include/VDI.H`.

---

## GEM Call Mechanism (TRAP #2)

Both AES and VDI use TRAP #2 but with different D0 selectors:

```asm
; AES call pattern:
    move.l  #aes_params, d1     ; pointer to parameter block
    move.w  #200, d0            ; 200 = AES selector
    trap    #2

; VDI call pattern:
    move.l  #vdi_params, d1     ; pointer to parameter block
    move.w  #115, d0            ; 115 = VDI selector ($73)
    trap    #2
```

No stack cleanup needed — all parameters pass through arrays, not the stack.

---

## AES Parameter Block

```
AES_Params:  dc.l  Control, Global, Int_In, Int_Out, Addr_In, Addr_Out

Control:     ds.w  5     ; [0]=function#, [1]=#intin, [2]=#intout, [3]=#addrin, [4]=#addrout
Global:      ds.w  14    ; [0]=AES version, [1]=max apps, [2]=ap_id, ...
Int_In:      ds.w  16    ; input integer parameters
Int_Out:     ds.w  7     ; output integer results (Int_Out[0] = return value)
Addr_In:     ds.l  3     ; input pointers (strings, object trees, etc.)
Addr_Out:    ds.l  1     ; output pointer
```

**Key Global[] fields** (set after appl_init):
- Global[0] = AES version (e.g., $0340 = 3.40)
- Global[1] = max concurrent apps
- Global[2] = ap_id (this application's ID)
- Global[3-4] = ap_private (long, private app data)
- Global[5-6] = pointer to object tree of desktop
- Global[7-8] = resource memory size
- Global[9-10] = available memory
- Global[13] = max screen height

---

## AES Function Quick Reference

### Application Management
| Func# | Name | Int_In | Int_Out | Addr_In | Description |
|---|---|---|---|---|---|
| 10 | appl_init | — | [0]=ap_id | — | Register app, fills Global[] |
| 13 | appl_find | — | [0]=ap_id | [0]=name | Find app by 8-char name |
| 19 | appl_exit | — | [0]=status | — | Deregister app |

### Event Handling
| Func# | Name | Key Parameters | Description |
|---|---|---|---|
| 20 | evnt_keybd | — | Wait for key; Int_Out[0]=key |
| 21 | evnt_button | In[0]=clicks, In[1]=mask, In[2]=state | Wait for button event |
| 22 | evnt_mouse | In[0]=enter/leave, In[1-4]=rectangle | Wait for mouse in/out rect |
| 23 | evnt_mesag | Addr_In[0]=msg_buf(8 words) | Wait for message |
| 24 | evnt_timer | In[0]=ms_hi, In[1]=ms_lo | Wait N milliseconds |
| 25 | evnt_multi | See below | Wait for multiple events |
| 26 | evnt_dclick | In[0]=speed, In[1]=set/get | Double-click speed |

**evnt_multi Int_In[] layout** (16 words):
```
[0]  = event flags (MU_KEYBD=1, MU_BUTTON=2, MU_M1=4, MU_M2=8, MU_MESAG=$10, MU_TIMER=$20)
[1]  = bclicks (button click count)
[2]  = bmask (button mask)
[3]  = bstate (desired button state)
[4]  = m1_leave (0=enter, 1=leave)
[5-8]= m1_x, m1_y, m1_w, m1_h (rectangle 1)
[9]  = m2_leave
[10-13]= m2_x, m2_y, m2_w, m2_h (rectangle 2)
[14] = timer_hi (milliseconds high word)
[15] = timer_lo (milliseconds low word)
```

**evnt_multi Int_Out[] layout** (7 words):
```
[0] = events that occurred (same flag bits as input)
[1] = mouse X
[2] = mouse Y
[3] = mouse button state
[4] = keyboard modifier state (shift/ctrl/alt bits)
[5] = key code (scancode<<8 | ASCII)
[6] = number of button clicks
```

### Menu Management
| Func# | Name | Int_In | Addr_In | Description |
|---|---|---|---|---|
| 30 | menu_bar | [0]=show(1)/hide(0) | [0]=tree | Show/hide menu bar |
| 31 | menu_icheck | [0]=item, [1]=check | [0]=tree | Check/uncheck menu item |
| 32 | menu_ienable | [0]=item, [1]=enable | [0]=tree | Enable/disable menu item |
| 33 | menu_tnormal | [0]=title, [1]=normal | [0]=tree | Reverse/normal menu title |
| 34 | menu_text | [0]=item | [0]=tree, [1]=text | Change menu item text |
| 35 | menu_register | [0]=ap_id | [0]=text | Register DA menu entry |

### Object Handling
| Func# | Name | Int_In | Addr_In | Description |
|---|---|---|---|---|
| 42 | objc_draw | [0]=start, [1]=depth, [2-5]=clip rect | [0]=tree | Draw object tree |
| 43 | objc_find | [0]=start, [1]=depth, [2]=mx, [3]=my | [0]=tree | Find object at point |
| 44 | objc_offset | [0]=object | [0]=tree | Get absolute x,y |
| 46 | objc_edit | [0]=obj, [1]=char, [2]=idx, [3]=kind | [0]=tree | Edit text field |
| 47 | objc_change | [0]=obj, [2-5]=clip, [6]=new_state, [7]=redraw | [0]=tree | Change state |

### Form/Dialog
| Func# | Name | Key Parameters | Description |
|---|---|---|---|
| 50 | form_do | In[0]=start_obj; Addr_In[0]=tree | Handle dialog; returns exit obj |
| 51 | form_dial | In[0]=flag(0-3), In[1-8]=rectangles | 0=FMD_START, 1=FMD_GROW, 2=FMD_SHRINK, 3=FMD_FINISH |
| 52 | form_alert | In[0]=default_btn; Addr_In[0]=alert_str | Alert box; returns button# |
| 54 | form_center | Addr_In[0]=tree | Center dialog; Out[1-4]=rect |

**form_alert string format**: `[icon][text][buttons]`
- `[0]` = no icon, `[1]` = note, `[2]` = wait, `[3]` = stop
- Example: `"[1][File not found][OK]"`

### Window Management
| Func# | Name | Int_In | Description |
|---|---|---|---|
| 100 | wind_create | [0]=kind, [1-4]=max rect | Create window; Out[0]=handle |
| 101 | wind_open | [0]=handle, [1-4]=rect | Display window |
| 102 | wind_close | [0]=handle | Remove from screen |
| 103 | wind_delete | [0]=handle | Free window |
| 104 | wind_get | [0]=handle, [1]=field | Get attribute; Out[1-4]=values |
| 105 | wind_set | [0]=handle, [1]=field, [2-5]=values | Set attribute |
| 107 | wind_update | [0]=flag | 1=BEG_UPDATE, 2=END_UPDATE, 3=BEG_MCTRL, 4=END_MCTRL |
| 108 | wind_calc | [0]=type, [1]=kind, [2-5]=rect | Calc work/border rect |

**wind_create kind flags (bit field)**:
```
$0001 = NAME (title bar)        $0002 = CLOSER (close box)
$0004 = FULLER (full box)       $0008 = MOVER (title, drag)
$0010 = INFO (info line)        $0020 = SIZER (resize box)
$0040 = UPARROW                 $0080 = DNARROW
$0100 = VSLIDE (vertical slider) $0200 = LFARROW
$0400 = RTARROW                 $0800 = HSLIDE (horizontal slider)
```

**wind_get/wind_set field codes**:
```
 1 = WF_KIND (component flags)   4 = WF_WORKXYWH (work area rect)
 5 = WF_CURRXYWH (current rect)  6 = WF_PREVXYWH (previous rect)
 7 = WF_FULLXYWH (full extent)  10 = WF_HSLIDE (horiz slider pos 1-1000)
11 = WF_VSLIDE (vert slider pos) 15 = WF_HSLSIZE (horiz slider size)
16 = WF_VSLSIZE (vert slider size)
```

### Resource Management
| Func# | Name | Key Parameters | Description |
|---|---|---|---|
| 110 | rsrc_load | Addr_In[0]=filename | Load .RSC file |
| 111 | rsrc_free | — | Free loaded resource |
| 112 | rsrc_gaddr | In[0]=type, In[1]=index | Get address; Addr_Out[0]=ptr |
| 114 | rsrc_obfix | In[0]=object; Addr_In[0]=tree | Fix char→pixel coords |

**rsrc_gaddr type values**: 0=R_TREE (object tree), 1=R_OBJECT, 5=R_STRING, 6=R_IMAGEDATA, 15=R_FRSTR (free string)

### File Selector
| Func# | Name | Key Parameters | Description |
|---|---|---|---|
| 90 | fsel_input | Addr_In[0]=path, [1]=file | File selector dialog |
| 91 | fsel_exinput | Addr_In[0]=path, [1]=file, [2]=title | Extended (with title) |

### Shell
| Func# | Name | Description |
|---|---|---|
| 120 | shel_read | Read command and command tail |
| 121 | shel_write | Launch program (In[0]=mode: 0=normal, 1=no return, 3=ACC) |

---

## AES Message Types

Received via evnt_mesag or evnt_multi with MU_MESAG flag. Message buffer is 8 words.

| Type | Name | msg[3] | msg[4-7] | Description |
|---|---|---|---|---|
| 10 | MN_SELECTED | title obj | item obj, -, -, - | Menu item clicked |
| 20 | WM_REDRAW | win handle | x, y, w, h | Redraw rectangle |
| 21 | WM_TOPPED | win handle | — | Window needs topping |
| 22 | WM_CLOSED | win handle | — | Close button clicked |
| 23 | WM_FULLED | win handle | — | Full button clicked |
| 24 | WM_ARROWED | win handle | arrow code | Scroll arrow clicked |
| 25 | WM_HSLID | win handle | slider pos (1-1000) | Horiz slider moved |
| 26 | WM_VSLID | win handle | slider pos (1-1000) | Vert slider moved |
| 27 | WM_SIZED | win handle | x, y, w, h | Resize requested |
| 28 | WM_MOVED | win handle | x, y, w, h | Move requested |
| 40 | AC_OPEN | acc menu id | — | Open accessory |
| 41 | AC_CLOSE | acc menu id | — | Close accessory |
| 50 | AP_TERM | — | — | Quit requested |

**Message buffer layout**: `msg[0]`=type, `msg[1]`=sender ap_id, `msg[2]`=overflow count, `msg[3+]`=type-specific

---

## AES Object Tree Structure

Each object is 24 bytes:

```
Offset  Size  Field        Description
+$00    W     ob_next      Next sibling (-1 if last)
+$02    W     ob_head      First child (-1 if none)
+$04    W     ob_tail      Last child (-1 if none)
+$06    W     ob_type      Object type (see below)
+$08    W     ob_flags     Object flags
+$0A    W     ob_state     Object state
+$0C    L     ob_spec      Type-specific pointer or value
+$10    W     ob_x         X position (relative to parent)
+$12    W     ob_y         Y position (relative to parent)
+$14    W     ob_width     Width
+$16    W     ob_height    Height
```

**ob_type values**: 20=G_BOX, 21=G_TEXT, 22=G_BOXTEXT, 23=G_IMAGE, 24=G_USERDEF, 25=G_IBOX, 26=G_BUTTON, 27=G_BOXCHAR, 28=G_STRING, 29=G_FTEXT (editable), 30=G_FBOXTEXT (editable box)

**ob_flags bits**: $01=SELECTABLE, $02=DEFAULT, $04=EXIT, $08=EDITABLE, $10=RBUTTON, $20=LASTOB, $40=TOUCHEXIT, $80=HIDETREE

**ob_state bits**: $01=SELECTED, $02=CROSSED, $04=CHECKED, $08=DISABLED, $10=OUTLINED, $20=SHADOWED

---

## VDI Parameter Block

```
VDI_Params:  dc.l  contrl, intin, ptsin, intout, ptsout

contrl:      ds.w  12    ; [0]=opcode, [1]=#ptsin, [2]=#ptsout, [3]=#intin, [4]=#intout, [5]=sub-opcode, [6]=handle
intin:       ds.w  128   ; input integer parameters
ptsin:       ds.w  128   ; input point coordinates (x,y pairs)
intout:      ds.w  128   ; output integer results
ptsout:      ds.w  128   ; output point coordinates
```

**contrl[6]** = workstation handle (returned by v_opnwk/v_opnvwk)
**contrl[5]** = sub-opcode for v_escape (opcode 5) and v_gdp (opcode 11)

---

## VDI Function Quick Reference

### Workstation Control
| Opcode | Name | Parameters | Description |
|---|---|---|---|
| 1 | v_opnwk | intin[0-10]=work_in | Open physical workstation |
| 2 | v_clswk | handle | Close physical workstation |
| 3 | v_clrwk | handle | Clear workstation |
| 4 | v_updwk | handle | Update workstation |
| 100 | v_opnvwk | intin[0-10]=work_in | Open virtual workstation |
| 101 | v_clsvwk | handle | Close virtual workstation |

**v_opnvwk work_in[] array**:
```
[0] = device ID (usually 1 = current screen)
[1-10] = default attributes: line type, line color, marker type, marker color,
          text font, text color, fill style, fill index, fill color, coordinate type
```

### Drawing Primitives
| Opcode | Name | Parameters | Description |
|---|---|---|---|
| 6 | v_pline | ptsin=vertices | Draw polyline |
| 7 | v_pmarker | ptsin=positions | Draw markers |
| 8 | v_gtext | ptsin[0,1]=x,y; intin=chars | Draw text string |
| 9 | v_fillarea | ptsin=vertices | Draw filled polygon |
| 114 | vr_recfl | ptsin[0-3]=rect | Fill rectangle |
| 125 | v_bar | ptsin[0-3]=rect | Draw bar/filled rectangle |
| 126 | v_arc | ptsin[0,1]=center; ptsin[6,7]=radius; intin[0,1]=angles | Draw arc |
| 127 | v_pieslice | same as arc | Draw pie slice |
| 128 | v_circle | ptsin[0,1]=center; ptsin[4]=radius | Draw circle |

### Attribute Setting
| Opcode | Name | intin[0] | Description |
|---|---|---|---|
| 15 | vsl_type | line style (1-7) | 1=solid, 2=longdash, 3=dot, 4=dashdot, 5=dash, 7=user |
| 16 | vsl_width | width in pixels | Set line width |
| 17 | vsl_color | color index | Set line color |
| 21 | vst_font | font ID | Set text font (1=system) |
| 22 | vst_color | color index | Set text color |
| 23 | vsf_interior | fill type | 0=hollow, 1=solid, 2=pattern, 3=hatch, 4=user |
| 24 | vsf_style | style index | Fill pattern/hatch index |
| 25 | vsf_color | color index | Set fill color |
| 32 | vswr_mode | writing mode | 1=replace, 2=transparent, 3=XOR, 4=reverse transparent |
| 106 | vst_effects | effect bits | bit0=bold, 1=light, 2=italic, 3=underline, 4=outline, 5=shadow |
| 129 | vs_clip | intin[0]=flag; ptsin=rect | 0=clip off, 1=clip on |

### Text
| Opcode | Name | Parameters | Description |
|---|---|---|---|
| 8 | v_gtext | x, y, string | Draw text at position |
| 12 | vst_height | ptsin[1]=height | Set char height in pixels |
| 107 | vst_point | intin[0]=points | Set char height in points |
| 116 | vqt_extent | string | Query text pixel extent |
| 124 | vst_alignment | intin[0]=hor, [1]=vert | 0=left/base, 1=center, 2=right |

### Raster Operations
| Opcode | Name | Parameters | Description |
|---|---|---|---|
| 109 | vro_cpyfm | intin[0]=mode; ptsin[0-7]=src/dst rects; contrl[7-8]=src MFDB, [9-10]=dst MFDB | Copy raster opaque |
| 110 | vr_trnfm | contrl[7-8]=src MFDB, [9-10]=dst MFDB | Transform device↔standard format |
| 134 | vrt_cpyfm | intin[0]=mode, [1-2]=colors; ptsin=rects; MFDBs in contrl | Copy raster transparent |

**MFDB (Memory Form Definition Block)** — 20 bytes:
```
+$00  L  fd_addr    Pointer to raster data (0 = screen)
+$04  W  fd_w       Width in pixels
+$06  W  fd_h       Height in pixels
+$08  W  fd_wdwidth Width in words (fd_w / 16, rounded up)
+$0A  W  fd_stand   0 = device-specific format, 1 = standard format
+$0C  W  fd_nplanes Number of bit planes
+$0E  6  reserved
```

**vro_cpyfm modes** (intin[0]): 0=ALL_WHITE, 3=S_ONLY (source copy), 6=S_XOR_D, 7=S_OR_D, 15=ALL_BLACK

### Inquire
| Opcode | Name | Description |
|---|---|---|
| 102 | vq_extnd | Extended workstation info (intout[0-44]) |
| 26 | vq_color | Query color RGB values |
| 130 | vqt_fontinfo | Query font metrics |
| 131 | vst_load_fonts | Load GDOS fonts |

### Escape Functions (opcode 5, sub-opcode in contrl[5])
| Sub | Name | Description |
|---|---|---|
| 1 | vq_chcells | Query text cell rows/columns |
| 2 | v_exit_cur | Exit alpha mode |
| 3 | v_enter_cur | Enter alpha (text cursor) mode |
| 4-7 | v_cur* | Cursor movement (up/down/right/left) |
| 8 | v_curhome | Cursor home |
| 9 | v_eeos | Erase to end of screen |
| 10 | v_eeol | Erase to end of line |
| 18 | v_hardcopy | Screen hardcopy to printer |
| 19 | v_dspcur | Display cursor at x,y |

### GDP Functions (opcode 11, sub-opcode in contrl[5])
| Sub | Name | Description |
|---|---|---|
| 1 | v_bar | Bar (filled rectangle) |
| 2 | v_arc | Arc |
| 3 | v_pieslice | Pie slice |
| 4 | v_circle | Circle |
| 5 | v_ellipse | Ellipse |
| 6 | v_ellarc | Elliptical arc |
| 7 | v_ellpie | Elliptical pie |
| 8 | v_rbox | Rounded rectangle |
| 9 | v_rfbox | Filled rounded rectangle |
| 10 | v_justified | Justified text |

---

## Typical GEM Application Pattern

```pseudocode
function gem_app_main():
    ap_id = appl_init()               // AES 10: register with AES
    vdi_handle = graf_handle()         // AES 77: get physical VDI handle
    v_opnvwk(work_in, vdi_handle)     // VDI 100: open virtual workstation
    rsrc_load("APP.RSC")              // AES 110: load resource file
    rsrc_gaddr(R_TREE, 0, &menu)      // AES 112: get menu tree address
    menu_bar(menu, 1)                  // AES 30: show menu bar
    wind_handle = wind_create(...)     // AES 100: create window
    wind_open(wind_handle, ...)        // AES 101: open window

    // Main event loop
    while not quit:
        events = evnt_multi(MU_MESAG | MU_KEYBD | MU_BUTTON, ...)  // AES 25

        if events & MU_MESAG:
            switch msg[0]:
                case MN_SELECTED (10):
                    handle_menu(msg[3], msg[4])    // title, item
                    menu_tnormal(menu, msg[3], 1)  // AES 33: restore title
                case WM_REDRAW (20):
                    wind_update(BEG_UPDATE)         // AES 107
                    redraw_window(msg[3], msg[4..7]) // handle, rect
                    wind_update(END_UPDATE)
                case WM_TOPPED (21):
                    wind_set(msg[3], WF_TOP)        // AES 105
                case WM_CLOSED (22):
                    quit = true
                case WM_MOVED (28):
                    wind_set(msg[3], WF_CURRXYWH, msg[4..7])
                case WM_SIZED (27):
                    wind_set(msg[3], WF_CURRXYWH, msg[4..7])

        if events & MU_KEYBD:
            handle_key(key_code)

    // Cleanup
    wind_close(wind_handle)            // AES 102
    wind_delete(wind_handle)           // AES 103
    menu_bar(menu, 0)                  // AES 30: hide menu
    rsrc_free()                        // AES 111
    v_clsvwk(vdi_handle)              // VDI 101: close workstation
    appl_exit()                        // AES 19: deregister
```

### Window Redraw Pattern (rectangle list)
```pseudocode
function redraw_window(handle, dirty_rect):
    wind_update(BEG_UPDATE)            // lock screen
    wind_get(handle, WF_FIRSTXYWH) → rect    // first rectangle
    while rect.w > 0 and rect.h > 0:
        if rectangles_intersect(rect, dirty_rect):
            vs_clip(vdi_handle, 1, intersection)  // VDI 129
            draw_window_contents(intersection)
        wind_get(handle, WF_NEXTXYWH) → rect     // next rectangle
    wind_update(END_UPDATE)
```

### Dialog Box Pattern
```pseudocode
function show_dialog(tree_index):
    rsrc_gaddr(R_TREE, tree_index) → tree
    form_center(tree) → x, y, w, h            // AES 54: center it
    form_dial(FMD_START, 0,0,0,0, x,y,w,h)    // AES 51: reserve screen
    form_dial(FMD_GROW, 0,0,0,0, x,y,w,h)     // animate grow
    objc_draw(tree, ROOT, MAX_DEPTH, x,y,w,h)  // AES 42: draw dialog
    exit_obj = form_do(tree, first_editable)    // AES 50: handle interaction
    form_dial(FMD_SHRINK, 0,0,0,0, x,y,w,h)   // animate shrink
    form_dial(FMD_FINISH, 0,0,0,0, x,y,w,h)    // release screen
    return exit_obj & 0x7FFF                    // mask out double-click bit
```

---

## Desk Accessory Pattern

Accessories differ from apps:
- Registered via `menu_register()` instead of creating their own menu
- Receive `AC_OPEN` (40) / `AC_CLOSE` (41) messages instead of startup/shutdown
- Must not call `menu_bar()`, `rsrc_load()` before AC_OPEN
- Must handle AC_CLOSE by releasing all resources (windows, memory)
- Entry point calls `appl_init()` then enters evnt_multi loop immediately

---

## GEM Detection Patterns in Disassembly

| Pattern | Indicates |
|---|---|
| `MOVE.W #200,D0` before TRAP #2 | AES call |
| `MOVE.W #115,D0` before TRAP #2 | VDI call |
| appl_init + evnt_multi + menu_bar | Full GEM desktop application |
| appl_init + evnt_multi but NO menu_bar | Accessory or minimal GEM app |
| v_opnvwk without appl_init | Direct VDI usage (non-GEM) |
| rsrc_load call | Program uses .RSC resource file |
| Multiple wind_create calls | Multi-window application |
| form_alert without other AES | Simple alert-only program |
