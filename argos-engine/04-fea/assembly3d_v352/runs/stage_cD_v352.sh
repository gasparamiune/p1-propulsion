#!/bin/bash
# cD stage (FEA3D-2, written 2026-10-21T02:24:34Z (date -u)).  Lead 2026-10-21T02:01:34Z (C): GO for cD after js5b, on the FINAL TC-01
# parts/ENG-TC-01.step fcb3b5b93bebdb01 (cD-only copy scripts/jfwd_sub_cD.py 0422fa6a9910bef2; production jfwd_sub.py cbc4c2ae2a1b61fd
# untouched).  Run folder in /dev/shm, a runner change for cD only: "The posts read it there. The frd is gzipped losslessly into the disk
# run folder, with the raw = decompressed sha check. Then remove the /dev/shm folder. Track its RAM in the WATCH lines. prlimit --as 8 GB,
# nice 19, 2 threads, and it starts only after js5b's post is done (one ccx of yours)."  Lead (after 02:13:58Z): "cD setup ACCEPTED as you
# describe it (... RAM run folder; gate 2.011 GiB on the disk part only)".
# 0. waits until tail_F.sh's own end line is in runs/tail_F.log (js5b, the last tail F stage, ended rc 0 incl. its posts and frd gzip);
#    tail_F.sh's own stop line there -> no start, exit 1.  The stage's own lines never contain either marker (tail_watch_F.py exits on them);
# 1. pins: runner, watcher, meta.json, runs/disk_peak_jfwd.json; no DONE; the deck in RAM (a file, not a link) with sha16 d7771451a7369dc1;
#    the disk .inp / .frd symlinks into the RAM folder; no ccx of mine (cwd in my work tree or under /dev/shm/fea3d2_cD); MemAvailable
#    >= 8.5 GiB (the RSS estimate with its 10 %, 7.41, + 1.0 GiB; else HELD, polled every 30 s);
# 2. watch_cD_v352.py JOB (background, nice 19): WATCH / ALERT / PEAK lines in runs/tail_F.log;
# 3. the solve: jfwd_cD_run_v352.py JOB expect=7.4 cap=8.0 timeout_h=4.0 (ccxrun own slot; < 2 ccx machine-wide, other RSS + 7.4 <= 9 GB;
#    disk gate 2.011 GiB from runs/disk_peak_jfwd.json, no held credit; no hold file; prlimit --as=8 GiB nice -n 19 ccx -i JOB, 2 threads,
#    VmHWM cap 8.0 GiB with own-PID kill); ccx rc 0 -> DONE;
# 4. posts as runs/post_seat_generic.sh (seatforce, shank, seat_cmp gref seat_s5L12_mu0_go, histcheck, runcmp vs js5; histcheck + runcmp
#    vs (b2) seat_s6L12_mu0 and (b2') seat_s9L12_mu0) + jfwd_patch_judge.py vs both + jfwd_lig_station.py, nice 10, 1 thread; any failure:
#    the frd stays in RAM, exit 1;
# 5. cite_guard on the frd; frd gzipped from RAM into the disk folder (gzip -6 -n, nice 19; raw sha256 = decompressed sha256), the disk
#    .frd symlink replaced by .frd.gz (COMPRESSED.txt); the deck xz'd into the disk folder (xz -6 -T1, nice 19; raw = decompressed, the
#    full raw sha in DECK_XZ.txt), its symlink removed; the small ccx outputs copied to the disk folder (cmp checked);
# 6. /dev/shm/fea3d2_cD removed; '<job> stage end' line.
# No cd; absolute paths only.  Launch: setsid nohup bash runs/stage_cD_v352.sh >> runs/tail_F.log 2>&1 &
W=/home/claude/work/fea3d
J=seat_sDL12_mu0
RAMROOT=/dev/shm/fea3d2_cD
RAM=$RAMROOT/runs/$J
DISK=$W/jfwd/runs/$J
TL=$W/runs/tail_F.log
PL=$W/runs/post_cD.log
PY="/opt/engine-venv/bin/python -I -B -u"
export FEA3D_CAD=v352
say() { echo "$(date -u +%FT%TZ) cD $J: $*"; }
stop() { echo "$(date -u +%FT%TZ) cD $J: stage stops: $* (tell the lead)"; exit 1; }
say "stage armed (pid $$); waits for the tail F end line in runs/tail_F.log (js5b's stage and posts done), then the checks and the solve"
# 0
while true; do
  grep -qE '^[0-9T:-]+Z tail_F done \(' $TL && break
  grep -qE '^[0-9T:-]+Z tail_F: stage [a-z0-9]+ FAILED: tail ST' $TL && stop "the tail F stopped (a stage failed) before js5b's post was done: cD not started"
  sleep 30
done
say "the tail F ended rc 0 (js5b's stage and posts done): checks"
# 1
[ -f $DISK/DONE ] && { say "has a DONE marker: not re-run"; echo "$(date -u +%FT%TZ) $J stage end (DONE before)"; exit 0; }
for pin in "$W/scripts/jfwd_cD_run_v352.py 535ed012b58d1567" "$W/scripts/watch_cD_v352.py c02749d5180388f1" \
           "$DISK/meta.json 675917103538c9b3" "$W/runs/disk_peak_jfwd.json edc5ce2c2ea0dec0"; do
  set -- $pin
  s=$(sha256sum $1 2>/dev/null | cut -c1-16)
  [ "$s" = "$2" ] || stop "$1 sha16 '$s' is not the pinned $2: not run"
done
[ -f $RAM/$J.inp ] && [ ! -L $RAM/$J.inp ] || stop "no deck file in the RAM folder $RAM: not run"
d=$(sha256sum $RAM/$J.inp | cut -c1-16)
[ "$d" = d7771451a7369dc1 ] || stop "deck sha16 $d is not d7771451a7369dc1: not run"
[ "$(readlink $DISK/$J.inp)" = "$RAM/$J.inp" ] && [ "$(readlink $DISK/$J.frd)" = "$RAM/$J.frd" ] || stop "disk .inp / .frd symlinks not into the RAM folder: not run"
[ -e $RAM/$J.frd ] && stop "an frd is in the RAM folder already: not run"
for p in $(pgrep -x ccx); do
  c=$(readlink /proc/$p/cwd 2>/dev/null)
  case "$c" in $W*|$RAMROOT*) stop "a ccx of mine runs (pid $p, cwd $c): not started (one ccx of mine)";; esac
done
held=0
while true; do
  m=$(awk '/^MemAvailable:/ {printf "%.2f", $2 / 1048576}' /proc/meminfo)
  awk -v x="$m" 'BEGIN{exit !(x >= 8.5)}' && break
  [ $held = 0 ] && say "start HELD: MemAvailable $m GiB < 8.5 GiB (the RSS estimate with its 10 %, 7.41, + 1.0); polled every 30 s"
  held=1; sleep 30
done
say "checks passed (deck $d, MemAvailable $m GiB, free $(df --output=avail -BM / | tail -1 | tr -d ' '), ccx: $(pgrep -a ccx | tr '\n' ';'))"
# 2
nice -n 19 $PY $W/scripts/watch_cD_v352.py $J > /dev/null 2>&1 &
# 3
nice -n 10 $PY $W/scripts/jfwd_cD_run_v352.py $J expect=7.4 cap=8.0 timeout_h=4.0 >> $W/runs/jfwdA.log 2>&1
rc=$?
grep -q '"returncode": 0' $DISK/ccx_run.json 2>/dev/null && [ $rc = 0 ] && touch $DISK/DONE
[ -f $DISK/DONE ] || stop "ccx did not end with rc 0 (runner rc $rc; see $DISK/ccx_run.json, $RAM/$J.log): the RAM folder is kept"
say "ccx rc 0, DONE; posts (runs/post_cD.log)"
# 4
export OMP_NUM_THREADS=1
: > $PL
CMDS=("jfwd_seatforce.py $J" "jfwd_shank.py $J" "jfwd_seat_cmp.py $J - gref=seat_s5L12_mu0_go" "jfwd_histcheck.py $J" "jfwd_runcmp.py $J js5_mu0_T3750_g078 x_lo=26.5")
for c in seat_s6L12_mu0 seat_s9L12_mu0; do CMDS+=("jfwd_histcheck.py $J $c" "jfwd_runcmp.py $J $c x_lo=26.5" "jfwd_patch_judge.py $J $c"); done
CMDS+=("jfwd_lig_station.py $J")
for c in "${CMDS[@]}"; do
  echo "$(date -u +%FT%TZ) [post $c]" >> $PL
  nice -n 10 $PY $W/scripts/$c 2>&1 | grep -v "^\s*\[" | cut -c1-500 >> $PL
  r=${PIPESTATUS[0]}
  echo "$(date -u +%FT%TZ) [post $c] rc $r" >> $PL
  [ $r = 0 ] || stop "post '$c' failed with rc $r (runs/post_cD.log): the frd stays in the RAM folder"
done
say "posts rc 0 (${#CMDS[@]} steps, runs/post_cD.log)"
# 5
nice -n 10 /opt/engine-venv/bin/python -I -B $W/scripts/cite_guard.py $DISK/$J.frd >> $PL 2>&1
grc=$?
[ $grc = 0 ] || stop "cite_guard on the frd rc $grc (cited or guard failed): not gzipped, the frd stays in the RAM folder"
f=$RAM/$J.frd
[ -f $f ] && [ ! -L $f ] || stop "no frd file in the RAM folder"
r=$(sha256sum $f | cut -d' ' -f1)
nice -n 19 gzip -c -6 -n $f > $DISK/$J.frd.gz.tmp && d=$(gzip -dc $DISK/$J.frd.gz.tmp | sha256sum | cut -d' ' -f1)
if [ -n "$r" ] && [ "$r" = "$d" ]; then
  mv $DISK/$J.frd.gz.tmp $DISK/$J.frd.gz && [ -L $DISK/$J.frd ] && rm $DISK/$J.frd
  g=$(sha256sum $DISK/$J.frd.gz | cut -c1-16)
  echo "$J.frd gzipped $(date -u +%Y-%m-%dT%H:%M:%SZ) (date -u) from the RAM run folder $RAM into the disk run folder: raw sha256/16 ${r:0:16} = decompressed sha256/16 ${d:0:16}; gz sha256/16 $g; raw $(stat -c %s $f) B -> gz $(stat -c %s $DISK/$J.frd.gz) B; lossless (lead 11:11Z rule; lead 2026-10-21T02:01:34Z (C))" > $DISK/COMPRESSED.txt
  cat $DISK/COMPRESSED.txt
else
  rm -f $DISK/$J.frd.gz.tmp
  stop "frd gzip verification failed (${r:0:16} vs ${d:0:16}): the frd stays in the RAM folder"
fi
i=$RAM/$J.inp
ri=$(sha256sum $i | cut -d' ' -f1)
[ "${ri:0:16}" = d7771451a7369dc1 ] || stop "the RAM deck sha16 ${ri:0:16} is not d7771451a7369dc1: not xz'd, the RAM folder is kept"
nice -n 19 xz -6 -T1 -c $i > $DISK/$J.inp.xz.tmp && di=$(xz -dc $DISK/$J.inp.xz.tmp | sha256sum | cut -d' ' -f1)
if [ "$ri" = "$di" ]; then
  mv $DISK/$J.inp.xz.tmp $DISK/$J.inp.xz && [ -L $DISK/$J.inp ] && rm $DISK/$J.inp
  x=$(sha256sum $DISK/$J.inp.xz | cut -c1-16)
  echo "$J.inp xz'd $(date -u +%Y-%m-%dT%H:%M:%SZ) (date -u) from the RAM run folder into the disk run folder (the deck never sat raw on disk): raw sha256 $ri (= meta.json deck_sha16 d7771451a7369dc1) = decompressed sha256 $di; xz sha256/16 $x; raw $(stat -c %s $i) B -> xz $(stat -c %s $DISK/$J.inp.xz) B; xz -6 -T1, nice 19; lossless" > $DISK/DECK_XZ.txt
  cat $DISK/DECK_XZ.txt
else
  rm -f $DISK/$J.inp.xz.tmp
  stop "deck xz verification failed: the RAM folder is kept"
fi
for s in $RAM/*; do
  b=$(basename $s)
  case "$b" in $J.frd|$J.inp) continue;; esac
  [ $(stat -c %s $s) -le 5000000 ] || stop "RAM file $b is over 5 MB: not copied, the RAM folder is kept"
  cp -p $s $DISK/$b && cmp -s $s $DISK/$b || stop "copy of $b failed: the RAM folder is kept"
done
say "small ccx outputs copied: $(ls $RAM | grep -v -e "^$J.frd$" -e "^$J.inp$" | tr '\n' ' ')"
# 6
[ -f $DISK/$J.frd.gz ] && [ -f $DISK/$J.inp.xz ] && [ -f $DISK/COMPRESSED.txt ] && [ -f $DISK/DECK_XZ.txt ] || stop "disk folder incomplete: the RAM folder is kept"
rm -r $RAMROOT && say "RAM folder $RAMROOT removed (/dev/shm used $(df --output=used -BM /dev/shm | tail -1 | tr -d ' '))"
echo "$(date -u +%FT%TZ) $J stage end: posted, judged vs (b2) and (b2'), frd gzipped and deck xz'd into the disk folder, RAM folder removed (disk folder $(du -sm $DISK | cut -f1) MB, free $(df --output=avail -BM / | tail -1 | tr -d ' '))"
