# Independent check of the drawing's engine silhouette against the frozen GLB (read-only).
import json, math, sys, hashlib
import numpy as np, trimesh
from PIL import Image, ImageDraw
CAD='/home/claude/work/shared-fallback/engine/03-cad/v3.5.1'
GLB=f'{CAD}/assembly/ENGINE_v3.5.1_neutral.glb'
MAN=f'{CAD}/assembly/assembly_manifest_v3.5.1.json'
print('glb sha16', hashlib.sha256(open(GLB,'rb').read()).hexdigest()[:16])
sc=trimesh.load(GLB)
man={i['inst']:i for i in json.load(open(MAN))['instances']}
parts={}
for inst in sc.graph.nodes_geometry:
    T,g=sc.graph[inst]; m=sc.geometry[g]
    V=trimesh.transformations.transform_points(m.vertices,T)*1000.0
    parts[inst]=(V, np.asarray(m.faces))
# try all 6 sign/axis permutations quickly to confirm the mapping independently
cands={'(X,-Z,Y)':lambda V:np.c_[V[:,0],-V[:,2],V[:,1]], '(X,Z,Y)':lambda V:np.c_[V[:,0],V[:,2],V[:,1]], '(-X,Z,Y)':lambda V:np.c_[-V[:,0],V[:,2],V[:,1]], '(Z,X,Y)':lambda V:np.c_[V[:,2],V[:,0],V[:,1]]}
for k,f in cands.items():
    err=0
    for inst,(V,F) in parts.items():
        e=f(V); b=np.r_[e.min(0),e.max(0)]; err=max(err,float(np.abs(b-np.array(man[inst]['bounds_mm'])).max()))
    print('mapping',k,'max bound err mm %.3f'%err)
E={inst:(np.c_[V[:,0],-V[:,2],V[:,1]],F) for inst,(V,F) in parts.items()}
allv=np.vstack([e for e,_ in E.values()])
print('n inst',len(E),'z range mm %.2f..%.2f'%(allv[:,2].min(),allv[:,2].max()), 'x %.2f..%.2f y %.2f..%.2f'%(allv[:,0].min(),allv[:,0].max(),allv[:,1].min(),allv[:,1].max()))
r=np.hypot(allv[:,0],allv[:,1]); print('r max all %.2f'%r.max())
bl6=E['ENG-BL-06#0'][0]; r6=np.hypot(bl6[:,0],bl6[:,1]); i=r6.argmax()
print('BL-06 r max %.2f az %.1f z %.1f..%.1f'%(r6.max(), math.degrees(math.atan2(bl6[i,1],bl6[i,0]))%360, bl6[:,2].min(), bl6[:,2].max()))
for pn in ['ENG-GM-09#0','ENG-GM-10#0','ENG-FD-12F#0']:
    if pn in E:
        e=E[pn][0]; print(pn,'z %.1f..%.1f r max %.2f'%(e[:,2].min(),e[:,2].max(),np.hypot(e[:,0],e[:,1]).max()), man[pn]['group'])
# r max outside the 70 mm bay radius: which parts
for inst,(e,F) in E.items():
    rr=np.hypot(e[:,0],e[:,1]).max()
    if rr>69.9: print('  r>69.9:',inst,'%.2f'%rr,'z %.1f..%.1f'%(e[:,2].min()+203,e[:,2].max()+203))
# projection
a=math.radians(112.0); ca,sa=math.cos(a),math.sin(a)
RES=0.25
S0=-40.0; LT=80.0; W=int((565-S0)/RES)+2; H=int((LT+80)/RES)+2
mask=Image.new('1',(W,H),0); dr=ImageDraw.Draw(mask)
for inst,(e,F) in E.items():
    s=e[:,2]+203.0; l=e[:,0]*ca+e[:,1]*sa
    X=(s-S0)/RES; Y=(LT-l)/RES
    for f in F:
        dr.polygon([(X[f[0]],Y[f[0]]),(X[f[1]],Y[f[1]]),(X[f[2]],Y[f[2]])],fill=1,outline=1)
M=np.array(mask,bool)
# SVG loops -> same grid, even-odd
loops=json.load(open('svg_engine_loops.json'))
acc=np.zeros_like(M)
for lp in loops:
    im=Image.new('1',(W,H),0); d2=ImageDraw.Draw(im)
    pts=[((((x-56)/400-0.25)*1000-S0)/RES, (LT-(300-y)*2.5)/RES) for x,y in lp]
    d2.polygon(pts,fill=1,outline=0)
    acc^=np.array(im,bool)
inter=(M&acc).sum(); uni=(M|acc).sum()
print('pixels CAD %d SVG %d  IoU %.4f  CAD-not-SVG %d  SVG-not-CAD %d'%(M.sum(),acc.sum(),inter/uni,(M&~acc).sum(),(acc&~M).sum()))
# max distance of mismatch pixels from the other mask boundary (scipy optional)
try:
    from scipy import ndimage
    dCAD=ndimage.distance_transform_edt(~M)*RES; dSVG=ndimage.distance_transform_edt(~acc)*RES
    print('max dist of SVG pixel outside CAD mask: %.2f mm'%dCAD[acc].max(), ' max dist of CAD pixel outside SVG: %.2f mm'%dSVG[M].max())
except Exception as ex: print('no scipy',ex)
cols=np.where(M.any(0))[0]; rows=np.where(M.any(1))[0]
print('CAD mask s %.2f..%.2f mm, l %.2f..%.2f mm'%(S0+cols.min()*RES,S0+(cols.max()+1)*RES,LT-(rows.max()+1)*RES,LT-rows.min()*RES))
Image.fromarray(((M.astype(np.uint8)*2+acc.astype(np.uint8))*80).astype(np.uint8)).save('mask_compare.png')
