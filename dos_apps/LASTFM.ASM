; =====================================================================
; NanoLink86 - LASTFM.COM (Minimalist Clean Live Audio Player)
; Hardware: Next186 SoC @ 42MHz on Tang Nano 9K (GW1NR-9C)
; Gateway:  ESP32 Xtensa Viper PS/2 Relay
;
; Display:
;   - SOURCE : Last.fm Cloud Audio
;   - PLAYING: Artist - Track
;   - STATUS : [ LIVE STREAMING ]
;
; Features:
;   - 100% Ultra-clean typography, zero graphics clutter
;   - Pure Direct VRAM (0xB800) High-Intensity VGA Text Mode
;   - Non-blocking loop, live track updates via ';' packet
;   - Exit cleanly ONLY on 'Q', 'q', or ESC (27)
; =====================================================================

[org 0x100]
[bits 16]

start:
    ; 1. Set 80x25 16-Color Text Mode (Clears screen)
    mov ax, 0x0003
    int 0x10

    ; 2. Hide hardware cursor (Move off-screen to Row 26)
    mov ah, 0x02
    mov bh, 0x00
    mov dx, 0x1A00
    int 0x10

    ; 3. Parse Command-line arguments from PSP (Offset 0x80)
    mov si, 0x80
    mov cl, [si]
    cmp cl, 1
    jle draw_full_screen

    ; Copy arguments into track_buf
    mov di, track_buf
    xor ch, ch
    inc si
copy_psp_args:
    inc si
    mov al, [si]
    cmp al, 0x0D
    je finish_psp_copy
    mov [di], al
    inc di
    loop copy_psp_args
finish_psp_copy:
    mov byte [di], 0

draw_full_screen:
    ; 4. Draw Clean Minimal Static UI
    call render_static_ui
    call render_track_vram

; ---------------------------------------------------------------------
; 5. Main Non-Blocking Loop
; ---------------------------------------------------------------------
main_loop:
    ; Frame delay (~50ms)
    mov cx, 0x8000
delay_loop:
    loop delay_loop

    ; Non-blocking check for keyboard hit (INT 16h, AH=01h)
    mov ah, 0x01
    int 0x16
    jz main_loop

    ; Key was pressed! Read it (INT 16h, AH=00h)
    mov ah, 0x00
    int 0x16

    ; Exit only on 'Q', 'q', or ESC (27)
    cmp al, 'q'
    je exit_program
    cmp al, 'Q'
    je exit_program
    cmp al, 27
    je exit_program

    ; Live track update packet triggers: ';', Tab (9), or '~'
    cmp al, ';'
    je handle_live_update
    cmp al, 9
    je handle_live_update
    cmp al, '~'
    je handle_live_update

    ; All other random keys are completely ignored!
    jmp main_loop

; ---------------------------------------------------------------------
; Live Track Update Packet Handler (Receives Prefix + TrackName + CR)
; ---------------------------------------------------------------------
handle_live_update:
    mov di, track_buf
    mov cx, 54          ; max 54 chars
read_packet_chars:
    mov ah, 0x00
    int 0x16            ; read next char
    cmp al, 0x0D        ; Carriage return CR
    je finish_packet_read
    cmp al, 0x0A        ; Linefeed LF
    je read_packet_chars
    mov [di], al
    inc di
    loop read_packet_chars
finish_packet_read:
    mov byte [di], 0    ; null terminate
    call render_track_vram
    jmp main_loop

exit_program:
    ; Restore text mode & cursor
    mov ax, 0x0003
    int 0x10

    ; Clean Exit to FreeDOS (INT 21h, AH=4Ch)
    mov ax, 0x4C00
    int 0x21

; ---------------------------------------------------------------------
; Helper: Write a null-terminated string with attribute to VRAM
; Inputs: DS:SI = string, ES:DI = VRAM offset, AH = attribute
; ---------------------------------------------------------------------
write_string_vram:
.next_ch:
    lodsb
    cmp al, 0
    je .str_done
    stosw
    jmp .next_ch
.str_done:
    ret

; ---------------------------------------------------------------------
; Render Track Name directly to Row 10 (Col 23 = 10*160 + 23*2 = 1646)
; ---------------------------------------------------------------------
render_track_vram:
    push es
    push ds
    mov ax, 0xB800
    mov es, ax
    mov di, 1646        ; Row 10, Col 23 = 10*160 + 23*2 = 1646
    mov si, track_buf
    mov cx, 54          ; Clear 54 columns width
.write_chars:
    lodsb
    cmp al, 0
    je .pad_spaces
    mov ah, 0x0F        ; High-Intensity Bright White on Black
    stosw
    dec cx
    jnz .write_chars
    jmp .done_render
.pad_spaces:
    mov al, ' '
    mov ah, 0x07        ; Normal spaces
    rep stosw
.done_render:
    pop ds
    pop es
    ret

; ---------------------------------------------------------------------
; Draw Static UI directly into VRAM (0xB800)
; ---------------------------------------------------------------------
render_static_ui:
    push es
    push ds
    mov ax, 0xB800
    mov es, ax

    ; Row 2: Top Border (Row 2, Col 2: 2*160 + 2*2 = 324)
    mov di, 324
    mov si, str_border
    mov ah, 0x03        ; Cyan
    call write_string_vram

    ; Row 3: Title (Row 3, Col 2: 3*160 + 2*2 = 484)
    mov di, 484
    mov si, str_title
    mov ah, 0x0B        ; Bright Cyan
    call write_string_vram

    ; Row 4: Border (Row 4, Col 2: 4*160 + 2*2 = 644)
    mov di, 644
    mov si, str_border
    mov ah, 0x03        ; Cyan
    call write_string_vram

    ; Row 8: SOURCE label (Row 8, Col 6: 8*160 + 6*2 = 1292)
    mov di, 1292
    mov si, str_lbl_source
    mov ah, 0x07        ; Light Gray
    call write_string_vram

    ; Row 8: SOURCE value (Row 8, Col 23: 8*160 + 23*2 = 1326)
    mov di, 1326
    mov si, str_val_source
    mov ah, 0x0B        ; Bright Cyan
    call write_string_vram

    ; Row 10: PLAYING label (Row 10, Col 6: 10*160 + 6*2 = 1612)
    mov di, 1612
    mov si, str_lbl_playing
    mov ah, 0x0E        ; Bright Yellow
    call write_string_vram

    ; Row 12: STATUS label (Row 12, Col 6: 12*160 + 6*2 = 1932)
    mov di, 1932
    mov si, str_lbl_status
    mov ah, 0x07        ; Light Gray
    call write_string_vram

    ; Row 12: STATUS value (Row 12, Col 23: 12*160 + 23*2 = 1966)
    mov di, 1966
    mov si, str_val_status
    mov ah, 0x0A        ; Bright Green
    call write_string_vram

    ; Row 16: Bottom Border (Row 16, Col 2: 16*160 + 2*2 = 2564)
    mov di, 2564
    mov si, str_border
    mov ah, 0x03        ; Cyan
    call write_string_vram

    ; Row 18: Controls (Row 18, Col 6: 18*160 + 6*2 = 2892)
    mov di, 2892
    mov si, str_ctrl
    mov ah, 0x0E        ; Yellow
    call write_string_vram

    ; Row 20: Bottom Border (Row 20, Col 2: 20*160 + 2*2 = 3204)
    mov di, 3204
    mov si, str_border
    mov ah, 0x03        ; Cyan
    call write_string_vram

    pop ds
    pop es
    ret

; ---------------------------------------------------------------------
; Static Strings
; ---------------------------------------------------------------------
str_border:
    db '============================================================================', 0

str_title:
    db '(( o ))               L A S T . F M   P L A Y E R                   [ v3.0 ]', 0

str_lbl_source:
    db 'SOURCE       : ', 0

str_val_source:
    db 'Last.fm Cloud Audio Scrobbler', 0

str_lbl_playing:
    db 'NOW PLAYING  : ', 0

str_lbl_status:
    db 'STATUS       : ', 0

str_val_status:
    db '[ LIVE STREAMING ]', 0

str_ctrl:
    db '[ Controls : Press Q or ESC to return to FreeDOS prompt ]', 0

; ---------------------------------------------------------------------
; Dynamic Track Buffer
; ---------------------------------------------------------------------
track_buf:
    db 'Ronen - Lights Out', 0
    times 64 db 0
