import json, numpy as np, math
M=json.load(open('/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/render/render_meta.json'))
c=M['camera']
Mw=np.array(c['matrix_world']); R=Mw[:3,:3]; C=Mw[:3,3]
W,H=1000,1800
f=c['lens_mm']/c['sensor_height_mm']*H
sx,sy=c['shift_x'],c['shift_y']
def P(p):
    q=R.T@(np.array(p,float)-C)
    return (W/2+f*q[0]/(-q[2])-sx*max(W,H), H/2-f*q[1]/(-q[2])+sy*max(W,H), -q[2])
