import json, math, numpy as np
from PIL import Image
D='/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/render/'
M=json.load(open(D+'render_meta.json')); c=M['camera']; W,H=1000,1800
Mw=np.array(c['matrix_world']); R=Mw[:3,:3]; C=Mw[:3,3]; f=c['lens_mm']/c['sensor_height_mm']*H; sy=c['shift_y']
def P(p):
    q=R.T@(np.asarray(p,float)-C); return np.array([W/2+f*q[0]/(-q[2]), H/2-f*q[1]/(-q[2])+sy*max(W,H)])
ext=np.asarray(Image.open(D+'rocket_exterior.jpg').convert('L'),float)
cutp=np.asarray(Image.open(D+'rocket_cutaway.jpg').convert('RGB'),float)
lab=np.asarray(Image.open(D+'rocket_cutaway_labelled.jpg').convert('RGB'),float)
# vent hole in the exterior: centre of the dark spot vs projection of (r .073, az 112, z .463)
a=math.radians(112.0); pv=P((0.073*math.cos(a),0.073*math.sin(a),0.463))
win=ext[int(pv[1])-12:int(pv[1])+13,int(pv[0])-12:int(pv[0])+13]; yy,xx=np.unravel_index(np.argmin(win),win.shape)
print('vent hole: projected %s, darkest pixel in 25x25 window at (%d,%d) lum %d (body lum ~%d)' % (np.round(pv,1),int(pv[0])-12+xx,int(pv[1])-12+yy,win.min(),np.median(win)))
# foot fittings (ALU) centre: F - u*0.031
for azl in (45,135,225,315):
    a=math.radians(azl); Hh=np.array([0.08*math.cos(a),0.08*math.sin(a),0.16]); F=np.array([0.4*math.cos(a),0.4*math.sin(a),-0.25]); u=(F-Hh)/np.linalg.norm(F-Hh)
    p=P(F-u*0.031); w=ext[int(p[1])-3:int(p[1])+4,int(p[0])-3:int(p[0])+4]
    print('foot fitting az %d: projected %s, mean lum in 7x7 %.0f (max %.0f)' % (azl,np.round(p,1),w.mean(),w.max()))
# labelled vs plain cutaway outside overlays (rocket column band x 440-560, rows without leaders)
rows=[r for r in range(180,1440) if all(abs(r-y)>14 for y in (370,513,648,852,906,1092,1161,1242,1302,1306,1368,1383))]
dif=np.abs(lab[rows][:,440:560]-cutp[rows][:,440:560]).mean()
print('labelled vs plain cutaway, rocket band outside leader rows: mean abs diff %.2f (0-255)' % dif)
# grain estimate: local std in a flat dark interior patch vs exterior flat patch
def lstd(img,y0,y1,x0,x1):
    p=img[y0:y1,x0:x1]; return float(np.std(p-np.mean(p)))
g=cutp.mean(2)
print('cutaway interior patch std (engine bay wall behind parts, x 525-535, y 1180-1220): %.1f' % lstd(g,1180,1220,525,535))
print('exterior body patch std (x 480-520, y 700-740): %.1f' % lstd(ext,700,740,480,520))
