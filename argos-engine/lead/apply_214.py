# GNC rev4 P2 N=1000 band -> CHANGELOG 214 (lead), REQUIREMENTS bullet edit.
import hashlib, shutil
HUB = '/home/claude/work/shared-fallback/engine'
SP = '/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad'
CL = f'{HUB}/interfaces/CHANGELOG.md'
REQ = f'{HUB}/00-requirements/REQUIREMENTS.md'
def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert h16(CL) == '07c70c7d72108fdd', h16(CL)
assert h16(REQ) == '80aaeebe4c2f2585', h16(REQ)
for p in (CL, REQ):
    shutil.copyfile(p, f"{SP}/{p.rsplit('/', 1)[1]}.pre-214")
lines = open(CL).read().split('\n')
if lines[-1] == '':
    lines = lines[:-1]
assert len(lines) == 213, len(lines)
l214 = (
    "2026-10-13 | lead | (decision) | A1 APOGEE TARGET = 210 m. GNC rev4 P2 interim report (agent message 2026-10-13 ~18:47Z; the staged "
    "evidence comes with the rev4 handback and REV-GNC-5's delta re-check, not yet in the hub): line-208 band at N = 1000 per base on massprops "
    "v3.5.1 (488b47f9d55ff91b), main bases A1_none + A1J_pc, runs 0-999 (500-run prefix extended and checked; v3d reference extended the "
    "same way), dip onset fixed at 80 g, pooled exact McNemar, UB95 = d + 1.645 se (Newcombe score bound in brackets). liq|G73: 200 m "
    "-15/+23 UB95 0.11 pp; 205 m UB95 0.29 pp; 210 m P 0.9835 vs 0.9860, -25/+20, p 0.55, deficit +0.25 pp, UB95 0.80 (0.83) pp PASS; "
    "215 m UB95 1.03 (1.05) pp, p 0.25 (fails the 1.0 pp bound by 0.03 pp); 220/225 m significant loss (p 0.040/0.033); 230/235 m p <= 2e-4. "
    "pw|G73: 200-220 m pass (UB95 0.75 pp at 220), 225 m fails the bound (1.17 pp), >= 230 m losses. Decision value = lower state = 210 m "
    "under either reading of the bound (all lower bands or h only). Inside the 200-220 m window of line 213, so no referral to Gaspar. "
    "Caveat recorded: the 210/215 boundary is statistical (0.03 pp at 215 m on liq), not a physical margin. Consequences: 210 m is the A1 "
    "value for gnc.json v3.2 (after REV-GNC-5's delta re-check), ICD-AIRFRAME v2.1 and the datasheet; remaining rev4 arms (A1_pc and "
    "A1J_none, G80 purge, valve target v351t, v3.5.2 8f887d83896aa7dd) run at 210 m and 215 m; then ENG-11 6-DOF at liq|G73|v351|h210 "
    "(S 3133/5353/7406 N m/rad x K_s 58/116, K_s 174, K_s spread) and RE-24. SIM, not physical approval | lead"
)
lines.append(l214)
open(CL, 'w').write('\n'.join(lines) + '\n')
req = open(REQ).read()
old = "exact value is the CHANGELOG 208 band from GNC rev4 N = 1000 on massprops v3.5.1."
assert req.count(old) == 1
req = req.replace(old, "exact value 210 m (CHANGELOG 214: line-208 band at N = 1000 on massprops v3.5.1, liq|G73 UB95 0.80 pp at 210 m; 215 m fails the bound by 0.03 pp, a statistical not physical margin; SIM, evidence staged with the GNC rev4 handback).")
open(REQ, 'w').write(req)
print('CL', len(lines), h16(CL), 'REQ', h16(REQ))
