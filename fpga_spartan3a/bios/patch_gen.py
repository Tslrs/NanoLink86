# usage: python patch_gen.py base.xdl out.xdl [bootstrap_1k.bin]
# Puts the original Next186 S3AN BIOS (+SPI serializer patches, +flush patch) into u_bios_ram.
# With a 1K bootstrap given, it is overlaid at F000:FC00 (reset vector included) for hardware tests.
import re, sys
base, out = sys.argv[1], sys.argv[2]
args = [x for x in sys.argv[3:] if not x.startswith("--")]
boot = open(args[0], "rb").read() if args else None
xdl = open(base).read()
bios = bytearray(open("bios_orig.bin", "rb").read())            # pristine author BIOS (Spartan3AN, 2013)
assert len(bios) == 8192
def put(off, old, new):
    old = bytearray(old); new = bytearray(new)
    assert bios[off:off+len(old)] == old, "unexpected bytes at %04X" % off
    bios[off:off+len(new)] = new
put(0x1457, [0xE0], [0xC0])                                     # flush(): touch DDR-backed lines, not BRAM
put(0x1451, [0xB7,0x07], [0xB7,0x08])                           # flush(): 8 lines (BIOS code is not in the cache any more)
put(0x148F, [0xB0,0xFF,0xEE,0x03,0xC0], [0xB0,0xFF,0xEE,0xED,0xC3])          # sdrb/sdsb for the byte-wide SPI serializer
put(0x14A9, [0xD1,0xE9,0xAC,0xEE,0x03,0xC0], [0xAC,0xEE,0xED,0xE2,0xFB,0xC3]) # sdwblk
put(0x14DC, [0xB0,0xFF,0xEE,0xD1,0xE9,0xEE,0xEB,0x05,0xEE,0x88], [0xB0,0xFF,0xEE,0xED,0x88,0x25,0x47,0xE2,0xF7,0xC3]) # sdrblk
if "--nanolink" in sys.argv:
    put(0x0162, [0xB9,0x19,0x00], [0xEB,0x44,0x00])             # skip KB reset/ID/scan-set (transmit-only NanoLink86), KB stays flagged present
if boot is None:
    stub = open("stub8.bin", "rb").read()
    assert all(x == 0 for x in bios[0x1D40:0x1D40+len(stub)])
    bios[0x1D40:0x1D40+len(stub)] = stub                            # int 08h pre-handler: periodic cache flush (live screen)
    sz = open("stubsz.bin", "rb").read()
    assert all(x == 0 for x in bios[0x1D60:0x1D60+len(sz)])
    bios[0x1D60:0x1D60+len(sz)] = sz                                # SD size: saturate >32GB-wrap instead of truncating C_SIZE
    rel = (0xFD60 - (0xF6AD + 3)) & 0xFFFF
    put(0x16AD, [0x8B,0x4D,0xF6,0xC1,0xC1,0x08,0x41], [0xE8, rel & 255, rel >> 8, 0x90,0x90,0x90,0x90])
    put(0x00C2, [0xC7,0x06,0x20,0x00,0xEC,0xE2], [0xC7,0x06,0x20,0x00,0x40,0xFD])
if boot is not None:
    assert len(boot) == 1024
    bios[0x1C00:0x2000] = bytearray(boot)
def repl(x, inst, inits):
    m = re.search(r"(inst \"" + re.escape(inst) + r"\" \"RAMB16BWE\"[\s\S]*?;)", x)
    assert m, inst
    blk = m.group(1)
    for k, v in inits.items():
        blk, n = re.subn(r"\b" + k + r"::[0-9A-Fa-f]{64}", k + "::" + v, blk)
        assert n == 1, k
    return x[:m.start(1)] + blk + x[m.end(1):]
for r in range(4):
    sl = bytearray(bios[i*4+r] for i in range(2048))
    inits = {}
    for row in range(0x40):
        ch = sl[row*32:row*32+32]
        inits["INIT_%02X" % row] = "".join("%02X" % b for b in reversed(ch))
    xdl = repl(xdl, "u_bios_ram/Mram_ram%d" % r, inits)
open(out, "w").write(xdl)
print("wrote " + out)
