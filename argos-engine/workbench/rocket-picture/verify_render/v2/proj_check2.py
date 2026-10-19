import json, math, numpy as np
from PIL import Image
D='/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/render/'
M=json.load(open(D+'render_meta.json')); c=M['camera']; W,H=1000,1800
Mw=np.array(c['matrix_world']); R=Mw[:3,:3]; C=Mw[:3,3]; f=c['lens_mm']/c['sensor_height_mm']*H; sy=c['shift_y']
def P(p):
    q=R.T@(np.asarray(p,float)-C); return np.array([W/2+f*q[0]/(-q[2]), H/2-f*q[1]/(-q[2])+sy*max(W,H)])
cut=np.asarray(Image.open(D+'rocket_cutaway.jpg').convert('L'),float)
def circ(r,z,n=720):
    a=np.linspace(0,2*np.pi,n,endpoint=False); return np.array([P((r*math.cos(t),r*math.sin(t),z)) for t in a])
print('-- cutaway: tank silhouette (r 0.0508 m = 101.6 mm OD) row profiles')
for z in (0.70,0.83,0.95):
    pc=circ(0.0508,z); i0,i1=pc[:,0].argmin(),pc[:,0].argmax(); row=int(round((pc[i0,1]+pc[i1,1])/2))
    r=cut[row]
    # gradient extrema near the projected edges
    g=np.diff(r)
    wl=slice(int(pc[i0,0])-6,int(pc[i0,0])+7); wr=slice(int(pc[i1,0])-6,int(pc[i1,0])+7)
    xl=wl.start+np.argmax(np.abs(g[wl]))+0.5; xr=wr.start+np.argmax(np.abs(g[wr]))+0.5
    print(' z %.2f row %d: projected %.1f..%.1f (w %.1f) | strongest edges %.1f..%.1f (w %.1f)' % (z,row,pc[i0,0],pc[i1,0],pc[i1,0]-pc[i0,0],xl,xr,xr-xl))
    print('   profile L:', ' '.join('%d'%v for v in r[wl]), ' | R:', ' '.join('%d'%v for v in r[wr]))
# tank ends at the camera side (front generator az 90) and the engine top
for nm,p in (('tank bottom front (r .0508, z .58)',(0,0.0508,0.58)),('tank bottom axis z .58',(0,0,0.58)),('tank top front (r .0508, z 1.08)',(0,0.0508,1.08)),('tank top back (r .0508 az 270, z 1.08)',(0,-0.0508,1.08)),('engine top axis z .5582',(0,0,0.5582)),('nozzle exit axis z -.0351',(0,0,-0.0351)),('body aft rim front z 0',(0,0.073,0)),('body top z 1.70 front',(0,0.073,1.70))):
    print(' %-40s -> %s' % (nm,np.round(P(p),1)))
col=cut[:,495:506].mean(1)
print('-- column x 495-505 luminance, rows 1070..1110:'); print(' '.join('%d:%d'%(y,col[y]) for y in range(1070,1110)))
print('-- column x 495-505 luminance, rows 755..790:'); print(' '.join('%d:%d'%(y,col[y]) for y in range(755,790)))
print('-- column rows 1425..1470 (nozzle exit region):'); print(' '.join('%d:%d'%(y,col[y]) for y in range(1425,1470)))
# recommended fin anchor candidates: distance to the az-45 damper rod and main tube lines in the image
def seg_dist(p,a,b):
    a,b,p=map(np.asarray,(a,b,p)); t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1); return np.linalg.norm(p-(a+t*(b-a)))
a45=math.radians(45); Hh=np.array([0.08*math.cos(a45),0.08*math.sin(a45),0.16]); F=np.array([0.4*math.cos(a45),0.4*math.sin(a45),-0.25])
B=np.array([0.0835*math.cos(a45),0.0835*math.sin(a45),0.40]); Pd=Hh+(F-Hh)*0.55
for nm,pt in (('author fin anchor',(0.12797,0.0015,0.0755)),('cand r .175 z .05',(0.175,0.0015,0.05)),('cand r .17 z .08',(0.17,0.0015,0.08)),('cand r .185 z .03',(0.185,0.0015,0.03))):
    pp=P(pt); print(' %-20s px %s  dist to damper line %.1f px, to main tube line %.1f px' % (nm,np.round(pp,1),seg_dist(pp,P(B),P(Pd)),seg_dist(pp,P(Hh),P(F))))
