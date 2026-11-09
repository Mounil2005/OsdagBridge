#!/usr/bin/env bash
# Runs the planned test cases one after another. Usage (Git Bash):
#   bash testing_scripts/run_batch.sh
# Needs the osdagbridge-env python; adds its DLL folders to PATH like `conda activate` does.
E="/c/Users/ASUS/.conda/envs/osdagbridge-env"
export PATH="$E/Library/bin:$E/Library/mingw-w64/bin:$E/Scripts:$E:$PATH"
R="D:/Code/FOSSEE Winter Internship"
OSI="$R/testing/osi_files/TC-baseline_inputs.osi"
OUT="$R/testing/evidence"
RUN="$E/python.exe testing_scripts/run_case.py"
cd "$R/OsdagBridge" || exit 1

# TC-001 (baseline) and TC-002 (span 20) were run separately; uncomment to repeat.
# $RUN TC-002 "$OSI" "$OUT" --set geometry.span=20
$RUN TC-003 "$OSI" "$OUT" --set geometry.span=45 --set geometry.carriageway_width=12
$RUN TC-004 "$OSI" "$OUT" --set geometry.span=19.9
$RUN TC-005 "$OSI" "$OUT" --set geometry.span=45.1
$RUN TC-006 "$OSI" "$OUT" --set geometry.skew_angle=10
$RUN TC-007 "$OSI" "$OUT" --set geometry.include_median=Yes
$RUN TC-008 "$OSI" "$OUT" --set material.girder=Custom --set material.girder.fy=410 --set material.girder.fu=540 --set material.girder.density=78.5 --set material.girder.e=200 --set material.girder.g=76.9 --set material.girder.poisson=0.3 --set material.deck=Custom --set material.deck.density=25 --set material.deck.fck=35 --set material.deck.fctm=2.8 --set material.deck.ecm=32
$RUN TC-009 "$OSI" "$OUT" --fresh --then geometry.span=25 --then geometry.span=35,geometry.carriageway_width=9
echo BATCH-DONE
