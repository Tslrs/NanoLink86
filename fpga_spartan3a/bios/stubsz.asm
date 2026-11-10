BITS 16
ORG 0xFD60
; SDHC size in 512KB units from CSD v2 C_SIZE (22 bits); the BIOS keeps 16 bits -> saturate instead of wrapping
        mov     cx, [di-10]
        rol     cx, 8
        inc     cx
        jz      .max
        test    byte [di-11], 0x3f
        jz      .ok
.max:   mov     cx, 0xffff
.ok:    ret
