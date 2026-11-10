BITS 16
ORG 0xFD40
; int 08h pre-handler: force the 8 cache lines out to DDR2 so the VGA scanout sees fresh text
        push    ax
        push    bx
        push    ds
        push    cs
        pop     ds
        mov     bx, 0xC800
.l:     mov     al, [bx]
        dec     bh
        cmp     bh, 0xC0
        jne     .l
        pop     ds
        pop     bx
        pop     ax
        jmp     0xE2EC
