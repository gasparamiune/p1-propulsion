#!/bin/bash
# tail F stage js5b, v2 (written 2026-10-20T20:07:23Z (date -u); supersedes v1 9caccaeed76b996c, lead 19:53:27Z (4)): js5b on IN718 screw
# properties (s5, mu 0, 3750 N, fit 0.078; steps SEAT, PRELOAD, FA1U, FA1D, LC2U, LC2Y, LC2N, LC2M), restricted contact output +
# FREQUENCY=1000 + G.
# Lead 19:09:50Z: "js5b runs restricted: fd5c555220cab427 + the generated N_CFACE *NSET + ', NSET=N_CFACE' on its 7 *CONTACT FILE cards,
# nothing else (checked by diff); G applies."  Lead 19:53:27Z (2): "RULED: FREQUENCY=1000 on js5b's output cards, ONLY after a re-test
# PASS ... On PASS: tail_F_js5b.sh's diff check becomes 'source + the N_CFACE *NSET (14,255 nodes) + ', NSET=N_CFACE' on exactly 7
# *CONTACT FILE lines + ', FREQUENCY=1000' on exactly the output-card lines you list (state the count), nothing else'; the verdict check
# names the new verdict file".  Re-test PASS 20:04:55Z: results/v352/cfile_freq_test_v352.json 9511d24879289007.  The listed lines: the
# 7 '*NODE FILE', 7 '*EL FILE' and 7 '*CONTACT FILE' lines of the 7 output steps = 21 lines.  (3)(a)2: "the stage reads the source deck
# only as a stream (gunzip -c <deck>.inp.gz), checks the stream's full raw sha (fd5c555220cab427...) before the build, and diffs the
# generated deck against that stream ... Any later re-run of the stage reads the stream the same way."
# 1. both verdicts PASS, the verdict files pinned: cfile_nset_test_v352.json aab672303fb8f3ce (TO-VERIFY 1, NSET) and
#    cfile_freq_test_v352.json 9511d24879289007 (TO-VERIFY 2, FREQUENCY); the build / check tools pinned (cfile_freq_v352.py,
#    cfile_nset_v352.py it imports, js5b_deck_check_v352.py);
# 2. waits while any repack_deck_v352 process runs;
# 3. the deck: the stream `gunzip -c jfwd/runs/SRC/SRC.inp.gz` must hash to the full raw sha256 fd5c5552...d36d; cfile_freq_v352.py jsdeck
#    builds the new folder from the stream (N_CFACE generated from the stream's own *CONTACT PAIR surfaces, 14,255 expected) and
#    diff-checks it; js5b_deck_check_v352.py checks it again independently against the stream (21 changed lines, nothing else); nothing
#    reads the raw path jfwd/runs/SRC/SRC.inp;
# 4. G watcher (background, nice 19): once the .sta has a step-1 increment line, repack_deck_v352.py g only=<job>;
# 5. the solve: jfwd_deck.py run <job> expect=6.6 cap=8.0 timeout_h=5.0.  ccxrun's J-FWD gate with no held credit (runs/disk_peak_jfwd.json
#    peak 197.6 MB, 7 blocks; with FREQUENCY a cap): 1.86 + 1.25 x 197.6 MB + 0.10 = 2.190 GiB; below it the start is HELD (ALERT line in
#    runs/disk_alert_E.log, watched: the lead is told), nothing lossy without a ruling;
# 6. after ccx rc 0: jfwd_post.py (then DONE), jfwd_ligament.py, jfwd_midbay.py, jfwd_cells.py (any failure: frd kept, exit 1); then the
#    extra posts; cite_guard on the frd; frd gzipped with sha verification.  The posts pick frd blocks by ccx step number (read_frd_steps:
#    the 1PSTEP step field, last increment of each step) and the .dat N_REF block by total time at the step end (checked 20:05Z).
cd /home/claude/work/fea3d
SRC=js5b_in718_mu0_T3750_g078
J=js5b_in718_mu0_T3750_g078_cf
RAW=fd5c555220cab42719d432cdb6c605220020f9198c734a1845bbd5674ad6d36d
PY="/opt/engine-venv/bin/python -I -B -u"
export FEA3D_NICE=10 FEA3D_CAD=v352
if [ -f jfwd/runs/$J/DONE ]; then echo "$(date -u +%FT%TZ) $J has a DONE marker: not re-run"; echo "$(date -u +%FT%TZ) $J stage end (DONE before)"; exit 0; fi
# 1
for pin in "results/v352/cfile_nset_test_v352.json aab672303fb8f3ce" "results/v352/cfile_freq_test_v352.json 9511d24879289007" \
           "scripts/cfile_freq_v352.py 98932959b93ca8ed" "scripts/cfile_nset_v352.py 9e31e1f71e6094db" "scripts/js5b_deck_check_v352.py 284cb5aaabdebd4a"; do
  set -- $pin
  s=$(sha256sum $1 2>/dev/null | cut -c1-16)
  [ "$s" = "$2" ] || { echo "$(date -u +%FT%TZ) $J: $1 sha16 '$s' is not the pinned $2: not built; tail stops (tell the lead)"; exit 1; }
done
for vf in results/v352/cfile_nset_test_v352.json results/v352/cfile_freq_test_v352.json; do
  v=$(/opt/engine-venv/bin/python -I -B -c "import json; print(json.load(open('$vf')).get('verdict'))" 2>&1)
  [ "$v" = PASS ] || { echo "$(date -u +%FT%TZ) $J: $vf verdict '$v' is not PASS: not built; tail stops (tell the lead)"; exit 1; }
done
# 2
n=0
while pgrep -f "scripts/repack_deck_v352.py" > /dev/null; do
  [ $n = 0 ] && echo "$(date -u +%FT%TZ) $J: waiting for the running repack_deck_v352 process(es) to end (lead 18:50:09Z (3)): $(pgrep -af scripts/repack_deck_v352.py | tr '\n' ';')"
  n=1; sleep 30
done
# 3
if [ -e jfwd/runs/$J ]; then echo "$(date -u +%FT%TZ) $J: folder exists already (no DONE): not rebuilt or re-run; tail stops (tell the lead)"; exit 1; fi
s=$(gunzip -c jfwd/runs/$SRC/$SRC.inp.gz | sha256sum | cut -d' ' -f1)
[ "$s" = "$RAW" ] || { echo "$(date -u +%FT%TZ) $J: source stream sha256 '$s' is not $RAW: not built; tail stops (tell the lead)"; exit 1; }
echo "$(date -u +%FT%TZ) $J: source stream gunzip -c jfwd/runs/$SRC/$SRC.inp.gz sha256 $s (= the raw sha)"
nice -n 10 $PY scripts/cfile_freq_v352.py jsdeck $SRC $J freq=1000 raw_sha=$RAW || { echo "$(date -u +%FT%TZ) $J: jsdeck failed: not run; tail stops (tell the lead)"; exit 1; }
nice -n 10 $PY scripts/js5b_deck_check_v352.py jfwd/runs/$SRC/$SRC.inp.gz jfwd/runs/$J $J
[ $? = 0 ] || { echo "$(date -u +%FT%TZ) $J: restricted + FREQUENCY deck check failed: not run; tail stops (tell the lead)"; exit 1; }
# 4
(
  st=jfwd/runs/$J/$J.sta
  while true; do
    if [ -f $st ] && grep -qE '^\s*1\s+[0-9]+\s+[0-9]+\s+[0-9]+\s+\S+' $st; then
      echo "$(date -u +%FT%TZ) G: $J.sta shows a step-1 increment: repack_deck_v352 g (lead 18:50:09Z (2))"
      nice -n 19 $PY scripts/repack_deck_v352.py g only=$J >> runs/repack_lzma.log 2>&1
      echo "$(date -u +%FT%TZ) G: repack_deck_v352 g rc $? (runs/repack_lzma.log, runs/REPACKED_deck_v352.txt)"
      break
    fi
    if [ -f jfwd/runs/$J/ccx_run.json ]; then echo "$(date -u +%FT%TZ) G: the solve ended with no step-1 line in the .sta: deck not gzipped"; break; fi
    sleep 20
  done
) &
GW=$!
# 5
echo "$(date -u +%FT%TZ) run $J expect=6.6 cap=8.0 timeout_h=5.0 post=jfwd keepfrd=0 (tail_F v2; df $(df --output=avail -BM / | tail -1); ccx: $(pgrep -a ccx | tr '\n' ';'))" >> runs/jfwdA.log
nice -n 10 $PY scripts/jfwd_deck.py run $J expect=6.6 cap=8.0 timeout_h=5.0 >> runs/jfwdA.log 2>&1
rc=$?
echo "$(date -u +%FT%TZ) end $J rc=$rc" >> runs/jfwdA.log
wait $GW
grep -q '"returncode": 0' jfwd/runs/$J/ccx_run.json 2>/dev/null || { echo "$(date -u +%FT%TZ) $J: ccx did not end with rc 0 (see jfwd/runs/$J/ccx_run.json): tail stops"; exit 1; }
# 6
export OMP_NUM_THREADS=1
: > runs/post_js5b.log
for c in "jfwd_post.py $J" "jfwd_ligament.py $J" "jfwd_midbay.py $J" "jfwd_cells.py $J"; do
  echo "$(date -u +%FT%TZ) [post $c]" >> runs/post_js5b.log
  nice -n 15 $PY scripts/$c >> runs/post_js5b.log 2>&1
  r=$?
  echo "$(date -u +%FT%TZ) [post $c] rc $r"
  [ $r = 0 ] || { echo "$(date -u +%FT%TZ) $J: post $c failed (runs/post_js5b.log): frd kept, tail stops"; exit 1; }
  [ "$c" = "jfwd_post.py $J" ] && touch jfwd/runs/$J/DONE
done
for c in "jfwd_cells.py $J basis=v352" "jfwd_spotface.py $J" "jfwd_screw_bend.py $J" "jfwd_shank.py $J" "jfwd_seatforce.py $J" "jfwd_lig_station.py $J"; do
  echo "$(date -u +%FT%TZ) [post $c]" >> runs/post_js5b.log
  nice -n 15 $PY scripts/$c >> runs/post_js5b.log 2>&1
  echo "$(date -u +%FT%TZ) [post $c] rc $? (extra post: a failure does not stop the stage)"
done
nice -n 10 /opt/engine-venv/bin/python -I -B scripts/cite_guard.py jfwd/runs/$J/$J.frd >> runs/post_js5b.log 2>&1
grc=$?
echo "$(date -u +%FT%TZ) [cite_guard $J.frd] rc $grc"
[ $grc = 0 ] || { echo "$(date -u +%FT%TZ) $J: frd cited or guard failed: not gzipped, tail stops"; exit 1; }
cd jfwd/runs/$J
f=$J.frd
r=$(sha256sum $f | cut -c1-16)
gzip -c -6 -n $f > $f.gz.tmp && d=$(gzip -dc $f.gz.tmp | sha256sum | cut -c1-16)
if [ -n "$r" ] && [ "$r" = "$d" ]; then
  mv $f.gz.tmp $f.gz && g=$(sha256sum $f.gz | cut -c1-16) && rm $f
  echo "$f gzipped $(date -u +%Y-%m-%dT%H:%M:%SZ) (date -u): raw sha256/16 $r = decompressed sha256/16 $d; gz sha256/16 $g; lossless (lead 11:11Z rule)" > COMPRESSED.txt
  cat COMPRESSED.txt
else
  rm -f $f.gz.tmp
  echo "$(date -u +%FT%TZ) $J: gzip verification failed ($r vs $d): frd kept, tail stops"; exit 1
fi
cd /home/claude/work/fea3d
echo "$(date -u +%FT%TZ) $J stage end: posted, frd gzipped"
