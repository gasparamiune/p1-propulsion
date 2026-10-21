# Exact per-station silhouette comparison: CAD edges crossing station s* vs SVG union polygon edges crossing s*.
import json, math, re, sys
import numpy as np, trimesh
GLB='/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/assembly/ENGINE_v3.5.1_neutral.glb'
SVG=sys.argv[1]; STEP=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
AZ=math.radians(112.0); ca,sa=math.cos(AZ),math.sin(AZ)
sc=trimesh.load(GLB)
SA=[];SB=[];LA=[];LB=[]
for inst in sc.graph.nodes_geometry:
    T,g=sc.graph[inst]; m=sc.geometry[g]
    V=trimesh.transformations.transform_points(m.vertices,T)*1000.0
    s=V[:,1]+203.0; l=V[:,0]*ca+(-V[:,2])*sa
    ed=m.edges_unique
    SA.append(s[ed[:,0]]);SB.append(s[ed[:,1]]);LA.append(l[ed[:,0]]);LB.append(l[ed[:,1]])
SA=np.concatenate(SA);SB=np.concatenate(SB);LA=np.concatenate(LA);LB=np.concatenate(LB)
smin=np.minimum(SA,SB); smax=np.maximum(SA,SB)
order=np.argsort(smin)
txt=open(SVG).read()
d=re.search(r'<path d="([^"]+)" fill="[^"]+" fill-opacity="0.24" fill-rule="evenodd"',txt).group(1)
polys=[]
for sub in re.findall(r'M[^M]+',d):
    P=np.array(list(map(float,re.findall(r'-?\d+\.?\d*',sub)))).reshape(-1,2)
    polys.append(np.c_[((P[:,0]-56.0)/400.0-0.25)*1000.0,(300.0-P[:,1])/400.0*1000.0])
E=np.vstack([np.c_[P,np.roll(P,-1,0)] for P in polys])
st=np.arange(-35.0+0.013,558.0,STEP)
res=[]
for s0 in st:
    sel=(smin<=s0)&(smax>=s0)&(smax>smin)
    t=(s0-SA[sel])/(SB[sel]-SA[sel]); lc=LA[sel]+t*(LB[sel]-LA[sel])
    cad_top,cad_bot=lc.max(),lc.min()
    s1,l1,s2,l2=E[:,0],E[:,1],E[:,2],E[:,3]
    se=(s1-s0)*(s2-s0)<0
    lv=l1[se]+(l2[se]-l1[se])*(s0-s1[se])/(s2[se]-s1[se])
    res.append((s0,cad_top,lv.max(),cad_bot,lv.min()))
R=np.array(res)
dt=R[:,2]-R[:,1]; db=R[:,4]-R[:,3]
print('stations',len(R))
print('top SVG-CAD mm: min %.3f max %.3f mean %.3f p99|.| %.3f'%(dt.min(),dt.max(),dt.mean(),np.percentile(abs(dt),99)))
print('bot SVG-CAD mm: min %.3f max %.3f mean %.3f p99|.| %.3f'%(db.min(),db.max(),db.mean(),np.percentile(abs(db),99)))
for k in np.argsort(-abs(dt))[:4]: print('worst top s=%.2f cad %.2f svg %.2f'%(R[k,0],R[k,1],R[k,2]))
for k in np.argsort(-abs(db))[:4]: print('worst bot s=%.2f cad %.2f svg %.2f'%(R[k,0],R[k,3],R[k,4]))
# sample of the profile for the record
for s0 in (-30,0,50,103.2,108,150,200,230,300,400,463,495,540,555):
    k=np.argmin(abs(R[:,0]-s0)); print('s %.1f  CAD top/bot %.2f/%.2f  SVG %.2f/%.2f'%(R[k,0],R[k,1],R[k,3],R[k,2],R[k,4]))
