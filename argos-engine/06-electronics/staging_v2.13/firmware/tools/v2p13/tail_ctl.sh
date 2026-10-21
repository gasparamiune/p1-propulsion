#!/bin/sh
# v2.13 time box (brief: hand back by about 18:00Z): skip the B-PC-1-shown AS-IS S13T run (s13t13 on sil_bpc1; the as-is artefact is shown on the
# standard build), by killing only my own process by PID, then run post.sh (S12, unit tests) once the chain has ended
O=/dev/shm/elec_v213/out
until [ -f $O/silT/s13t13.start ] || [ -f $O/chain.done ]; do sleep 2; done
if [ ! -f $O/chain.done ]; then
  sleep 1
  P=$(pgrep -f "^/dev/shm/elec_v213/build/sil_bpc1 s13t13 /dev/shm/elec_v213/out/silT$")
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) killing PID $P (sil_bpc1 s13t13, as-is variant skipped for the time box)" > $O/tail_ctl.txt
  [ -n "$P" ] && kill $P
fi
until [ -f $O/chain.done ]; do sleep 2; done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) chain.done; post.sh" >> $O/tail_ctl.txt
sh /dev/shm/elec_v213/tools/post.sh
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) post done" >> $O/tail_ctl.txt
