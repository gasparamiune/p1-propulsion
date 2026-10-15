#!/bin/bash
# run_all.sh v1 (2026-10-12) - regenerate and check the ARGOS engine ECU KiCad project.
# usage: run_all.sh [kicad_dir]   (default ../kicad relative to this script)
# Steps: generate project -> kicad-cli netlist -> independent netlist cross-check -> grouped BOM -> PDF ->
#        KiCad eeschema ERC (GUI, headless via Xvfb; kicad-cli 7 has no 'sch erc').
# WARNING: step 1 overwrites hand edits in the KiCad files. Once the founder edits the schematic in KiCad,
# KiCad is the master: run only steps 2-6 (pass SKIP_GEN=1).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
KDIR=$(readlink -m "${1:-$HERE/../kicad}")
cd "$HERE"
if [ "${SKIP_GEN:-0}" != "1" ]; then
  python3 make_ecu_kicad.py "$KDIR"
fi
mkdir -p "$KDIR/erc"
kicad-cli sch export netlist -o "$KDIR/erc/argos_ecu_exported.net" "$KDIR/argos_ecu.kicad_sch" >/dev/null
python3 check_netlist.py "$KDIR" "$KDIR/erc/argos_ecu_exported.net" "$KDIR/erc/netlist_crosscheck"
python3 make_bom_from_netlist.py "$KDIR/erc/argos_ecu_exported.net" "$KDIR/argos_ecu_bom_grouped.csv"
kicad-cli sch export pdf -o "$KDIR/argos_ecu_schematic.pdf" "$KDIR/argos_ecu.kicad_sch" >/dev/null
./gui_erc.sh "$KDIR/argos_ecu.kicad_sch" "$KDIR/erc/argos_ecu_erc.rpt" "$KDIR/erc/shots"
rm -f "$KDIR"/~*.lck "$KDIR"/*-bak "$KDIR"/fp-info-cache 2>/dev/null || true
echo "done: $KDIR"
