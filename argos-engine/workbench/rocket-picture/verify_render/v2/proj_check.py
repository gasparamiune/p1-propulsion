# Verifier: rebuild the camera from its stated parameters, project SOURCE geometry, compare with image edges.
import json, math, numpy as np
from PIL import Image
D='/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/render/'
M=json.load(open(D+'render_meta.json')); c=M['camera']
W,H=1000,1800
# independent camera from az/el/aim/distance (track -Z to aim, Y up)
az,el=math.radians(c['az_deg']),math.radians(c['elev_deg'])
d=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
aim=np.array(c['aim_m']); C=aim+d*c['distance_m']
fwd=-d; right=np.cross(fwd,[0,0,1]); right/=np.linalg.norm(right); up=np.cross(right,fwd)
R=np.column_stack([right,up,-fwd])
Mw=np.array(c['matrix_world'])
print('camera rebuilt vs meta: loc diff %.2e, rot diff %.2e' % (np.abs(C-Mw[:3,3]).max(), np.abs(R-Mw[:3,:3]).max()))
f=c['lens_mm']/c['sensor_height_mm']*H; sx,sy=c['shift_x'],c['shift_y']
def P(p):
    q=R.T@(np.asarray(p,float)-C)
    return np.array([W/2+f*q[0]/(-q[2])-sx*max(W,H), H/2-f*q[1]/(-q[2])+sy*max(W,H)])
def circ(r,z,n=720):
    a=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.array([P((r*math.cos(t),r*math.sin(t),z)) for t in a])
def lum(path):
    return np.asarray(Image.open(path).convert('L'),float)
ext=lum(D+'rocket_exterior.jpg'); cut=lum(D+'rocket_cutaway.jpg')
def edges(img,row,x0=500,thr=None,lo=380,hi=620):
    r=img[int(round(row)),:]
    if thr is None: thr=(r[x0]+np.median(np.r_[r[lo-60:lo],r[hi:hi+60]]))/2
    # walk left/right from x0 until crossing thr; sub-pixel linear interpolation
    xl=x0
    while r[xl-1]>thr: xl-=1
    L=xl-(r[xl]-thr)/(r[xl]-r[xl-1])
    xr=x0
    while r[xr+1]>thr: xr+=1
    Rr=xr+(r[xr]-thr)/(r[xr]-r[xr+1])
    return L,Rr,thr
print('\n-- exterior: body silhouette (r 0.073 m, 146 mm OD)')
for z in (0.70,1.00,1.30,1.60):
    pc=circ(0.073,z); i0,i1=pc[:,0].argmin(),pc[:,0].argmax()
    row=(pc[i0,1]+pc[i1,1])/2
    L,Rr,thr=edges(ext,row)
    print(' z %.2f: projected x %.1f..%.1f (w %.2f px) | image %.1f..%.1f (w %.2f px) | diff L %+.1f R %+.1f' % (z,pc[i0,0],pc[i1,0],pc[i1,0]-pc[i0,0],L,Rr,Rr-L,L-pc[i0,0],Rr-pc[i1,0]))
# nose tip
tip=P((0,0,2.0)); col=ext[:,495:506].max(1); top=np.argmax(col>col[:100].max()+25)
print('\n-- nose tip z 2.00: projected y %.1f | image first bright row %d' % (tip[1],top))
# the vertical scale (px per m) along the axis at several heights
for z0 in (0.0,0.5,1.0,1.45):
    print(' px per 0.5 m on the axis z %.2f-%.2f: %.1f' % (z0,z0+0.5,P((0,0,z0))[1]-P((0,0,z0+0.5))[1]))
print(' scale bar in the meta: %s' % M['projection']['scale_bar']['px_final'])
sb=np.array(M['projection']['scale_bar']['px_final']); print(' scale bar length %.1f px' % np.linalg.norm(sb[0]-sb[1]))
# fins in profile (az 0 at +X -> image left, az 180 -> image right): outer edge r 0.193 between z 0 and 0.10
print('\n-- fins: outer edge r 0.193 m (span 0.12 m), z 0..0.10')
for azf in (0.0,180.0):
    a=math.radians(azf)
    for z in (0.03,0.07):
        p=P((0.193*math.cos(a),0.193*math.sin(a),z)); row=int(round(p[1])); r=ext[row]
        # find the fin outer edge: scan outward from the body side for the transition fin(dark charcoal)->background
        print('  az %3.0f z %.2f: projected x %.1f y %.1f ; row profile x-6..x+6: %s' % (azf,z,p[0],p[1],' '.join('%d'%v for v in r[int(p[0])-6:int(p[0])+7])))
    for z in (0.20,0.10,0.0):
        p=P(((0.073 if z==0.2 else 0.193)*math.cos(a),(0.073 if z==0.2 else 0.193)*math.sin(a),z)); print('   corner z %.2f -> px %.1f, %.1f' % (z,p[0],p[1]))
# feet (foot pad centres r 0.40, z -0.25) and foot fittings
print('\n-- legs: foot pads r 0.40 m, z -0.25; hinge r 0.080 z 0.160')
for azl in (45,135,225,315):
    a=math.radians(azl); F=np.array([0.4*math.cos(a),0.4*math.sin(a),-0.25]); Hh=np.array([0.08*math.cos(a),0.08*math.sin(a),0.16])
    print('  az %d: foot pad centre px %s, hinge px %s' % (azl,np.round(P(F),1),np.round(P(Hh),1)))
json.dump({'f':f}, open('/dev/null','w'))
