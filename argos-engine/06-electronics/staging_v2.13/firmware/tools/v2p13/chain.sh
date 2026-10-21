#!/bin/sh
# v2.13 SIL chain: build sil_bpc1, then the standard build runs, then the B-PC-1-shown build runs (sequential, nice 15)
sh /dev/shm/elec_v213/tools/build.sh silb
/dev/shm/elec_v213/tools/run_sil.sh sil /dev/shm/elec_v213/out/silF s13f a5 s13t13ts s13t13
/dev/shm/elec_v213/tools/run_sil.sh sil_bpc1 /dev/shm/elec_v213/out/silT s13f s13t13ts a5 s13t13
date -u +%Y-%m-%dT%H:%M:%SZ > /dev/shm/elec_v213/out/chain.done
