#!/bin/bash
# usage: build2.sh tag [name]   -> fixed design (system_fix.xdl) + BIOS, or + name.asm test bootstrap
set -e
S=$(cd "$(dirname "$0")" && pwd); T=$1; B=$2; P=/home/ubuntu/Desktop/spartan3a_next186
scp -q -P 2222 $S/patch_gen.py ubuntu@127.0.0.1:/tmp/patch_gen.py; scp -q -P 2222 $S/stub8.bin $S/stubsz.bin $S/bios/orig.com ubuntu@127.0.0.1:$P/; ssh -p 2222 ubuntu@127.0.0.1 "cp $P/orig.com $P/bios_orig.bin"
ARG=""
if [ -n "$B" ]; then nasm -f bin $S/$B.asm -o $S/$B.bin; scp -q -P 2222 $S/$B.bin ubuntu@127.0.0.1:$P/bootstrap_$B.bin; ARG="bootstrap_$B.bin"; fi
ssh -p 2222 ubuntu@127.0.0.1 "cd $P && python /tmp/patch_gen.py ${BASE:-system_fix.xdl} system_$T.xdl $ARG $OPTS && sed -e 's/system_v8.bit/system_$T.bit/' /tmp/prog_v8.cmd > /tmp/prog_$T.cmd && source /opt/Xilinx/14.7/ISE_DS/settings64.sh >/dev/null && xdl -xdl2ncd -force system_$T.xdl system_$T.ncd >/dev/null 2>&1; bitgen -w system_$T.ncd system_$T.bit >/dev/null 2>&1; ls -la system_$T.bit && impact -batch /tmp/prog_$T.cmd 2>&1 | grep -i -E 'Programmed successfully|fail' "
