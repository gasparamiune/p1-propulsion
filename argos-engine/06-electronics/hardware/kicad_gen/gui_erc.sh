#!/bin/bash
# gui_erc.sh v1 (2026-10-12) - run the KiCad 7 eeschema Electrical Rules Checker headless and save its report.
# usage: gui_erc.sh <root.kicad_sch> <report.rpt> <screenshot_dir>
# Why: KiCad 7.0 kicad-cli has no 'sch erc' (added in KiCad 8). This drives the real ERC engine through the GUI
# (Xvfb virtual display + xdotool clicks), saves KiCad's own .rpt and screenshots of the dialog as evidence.
# Coordinates are relative to the ERC dialog's bottom-right corner (KiCad 7.0.11, GTK3, no window manager).
set -u
SCH=$(readlink -f "$1"); RPT=$(readlink -m "$2"); SHOTS=$(readlink -m "$3")
mkdir -p "$SHOTS" "$(dirname "$RPT")"
export DISPLAY=:99
if ! xdotool getdisplaygeometry >/dev/null 2>&1; then
  (Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp >/dev/null 2>&1 &)
  sleep 2
fi
rm -f "$RPT"
eeschema "$SCH" >"$SHOTS/eeschema.log" 2>&1 &
EPID=$!
shot() { import -window root "$SHOTS/$1.png" 2>/dev/null; }
win_by_name() {  # substring match on window names (handles the UTF-8 em dash in KiCad titles)
  for w in $(xdotool search --name "" 2>/dev/null); do
    n=$(xdotool getwindowname "$w" 2>/dev/null)
    case "$n" in *"$1"*) echo "$w"; return 0;; esac
  done
  return 1
}
finish() { kill "$EPID" 2>/dev/null; sleep 1; kill -9 "$EPID" 2>/dev/null; rm -f "$(dirname "$SCH")"/~*.lck; }
MAIN=""
for i in $(seq 1 90); do MAIN=$(win_by_name "Schematic Editor") && break; sleep 1; done
[ -z "$MAIN" ] && { echo "ERROR: eeschema main window not found"; shot 00_fail; finish; exit 2; }
sleep 4
shot 01_loaded
# Inspect menu -> Electrical Rules Checker (menu bar at the top-left of the 1280x720 main window)
xdotool mousemove 206 12 click 1; sleep 1.5
xdotool mousemove 283 37 click 1
DLG=""
for i in $(seq 1 20); do DLG=$(win_by_name "Electrical Rules Checker") && break; sleep 0.5; done
[ -z "$DLG" ] && { echo "ERROR: ERC dialog not found"; shot 02_fail; finish; exit 3; }
sleep 1
eval "$(xdotool getwindowgeometry --shell "$DLG")"
BRX=$((X + WIDTH)); BRY=$((Y + HEIGHT))
xdotool mousemove $((BRX - 63)) $((BRY - 23)) click 1      # Run ERC
sleep "${ERC_WAIT:-25}"
shot 03_erc_result
xdotool mousemove $((BRX - 63)) $((BRY - 72)) click 1      # Save...
SAVE=""
for i in $(seq 1 20); do SAVE=$(win_by_name "Save Report to File") && break; sleep 0.5; done
[ -z "$SAVE" ] && { echo "ERROR: save dialog not found"; shot 04_fail; finish; exit 4; }
sleep 1
xdotool key --window "$SAVE" ctrl+a
xdotool type --delay 15 "$RPT"
sleep 0.5; xdotool key Return; sleep 2
xdotool mousemove $((X + 186)) $((Y + 28)) click 1; sleep 1   # 'Ignored Tests' tab, for the record
shot 05_ignored_tests
finish
[ -f "$RPT" ] && { echo "report: $RPT"; tail -2 "$RPT"; exit 0; }
echo "ERROR: report not written"; exit 5
