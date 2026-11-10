setMode -bs
setCable -port auto
Identify -inferir
identifyMPM
attachflash -position 1 -spi "AT45DB161D"
assignfiletoattachedflash -position 1 -file "/home/ubuntu/Desktop/spartan3a_next186/prom_kb1.mcs"
Program -p 1 -dataWidth 1 -spionly -e -v -loadfpga
quit
