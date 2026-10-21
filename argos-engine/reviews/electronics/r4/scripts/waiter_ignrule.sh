#!/bin/bash
# waits for my orphaned ignrule process (PID 31994) to exit, then releases chain2 (which waits for an 'end' line in the chain1 log)
L=/dev/shm/rev_elec4/run/chain1_log.txt
while kill -0 31994 2>/dev/null; do sleep 5; done
echo "ignrule exited (chain1 parent stopped at 2026-10-21T13:40:00Z to run the MAJOR-class probe first; rc not captured) $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
echo "end (part B steps after ignrule NOT run in chain1; see chain3) $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
