#!/bin/bash
# usage: run_serial.sh <case_dir>   (serial rhoCentralFoam, 1 core, logs inside the case)
source /usr/share/openfoam/etc/bashrc 2>/dev/null
cd "$1" || exit 1
blockMesh > log.blockMesh 2>&1 || exit 2
checkMesh > log.checkMesh 2>&1
date +%s > t_start
rhoCentralFoam > log.rhoCentralFoam 2>&1
echo $? > exit_code
date +%s > t_end
