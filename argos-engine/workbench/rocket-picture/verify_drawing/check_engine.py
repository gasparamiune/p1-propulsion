# Independent check of the engine silhouette in rocket_side_view.svg against the frozen GLB.
import json, math, re, sys
import numpy as np, trimesh
GLB='/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/assembly/ENGINE_v3.5.1_neutral.glb'
MAN='/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/assembly/assembly_manifest_v3.5.1.json'
SVG=sys.argv[1]
AZ=math.radians(112.0); ca,sa=math.cos(AZ),math.sin(AZ)
sc=trimesh.load(GLB)
man={i['inst']:i for i in json.load(open(MAN))['instances']}
allE=[]; edges_s=[]; edges_l=[]; err=0; groups={}
for inst in sc.graph.nodes_geometry:
    T,g=sc.graph[inst]; m=sc.geometry[g]
    V=trimesh.transformations.transform_points(m.vertices,T)*1000.0
    e=np.c_[V[:,0],-V[:,2],V[:,1]]
    b=np.r_[e.min(0),e.max(0)]
    err=max(err,float(np.abs(b-np.array(man[inst]['bounds_mm'])).max()))
    allE.append(e); groups[man[inst]['group']]=groups.get(man[inst]['group'],0)+1
    s=e[:,2]+203.0; l=e[:,0]*ca+e[:,1]*sa
    ed=m.edges_unique
    a,bb=ed[:,0],ed[:,1]
    # sample each edge every <=0.25 mm in s
    L=np.abs(s[bb]-s[a]); n=np.maximum(1,np.ceil(L/0.25).astype(int))
    for k in np.unique(n):
        sel=n==k; t=np.linspace(0,1,k+1)
        ss=s[a[sel]][:,None]*(1-t)+s[bb[sel]][:,None]*t
        ll=l[a[sel]][:,None]*(1-t)+l[bb[sel]][:,None]*t
        edges_s.append(ss.ravel()); edges_l.append(ll.ravel())
allE=np.vstack(allE); S=np.concatenate(edges_s); Lt=np.concatenate(edges_l)
print('instances',len(sc.graph.nodes_geometry),'groups',groups,'max manifest bound err mm',round(err,3))
print('axial extent engine frame mm',allE[:,2].min().round(2),allE[:,2].max().round(2),'len',(allE[:,2].max()-allE[:,2].min()).round(2))
r=np.hypot(allE[:,0],allE[:,1]); print('r max all az',r.max().round(2),'bbox x',allE[:,0].min().round(2),allE[:,0].max().round(2),'y',allE[:,1].min().round(2),allE[:,1].max().round(2))
print('projected lateral (az112) min/max', Lt.min().round(2), Lt.max().round(2))
# CAD envelope per 1 mm station band
lo=math.floor(S.min()); hi=math.ceil(S.max())
bins=np.arange(lo,hi+1,1.0); idx=np.clip(np.digitize(S,bins)-1,0,len(bins)-2)
top=np.full(len(bins)-1,-1e9); bot=np.full(len(bins)-1,1e9)
np.maximum.at(top,idx,Lt); np.minimum.at(bot,idx,Lt)
# SVG union path: the evenodd filled path
txt=open(SVG).read()
mm=re.search(r'<path d="([^"]+)" fill="[^"]+" fill-opacity="0.24" fill-rule="evenodd"',txt)
d=mm.group(1)
polys=[]
for sub in re.findall(r'M[^M]+',d):
    nums=list(map(float,re.findall(r'-?\d+\.?\d*',sub)))
    P=np.array(nums).reshape(-1,2)
    z=(P[:,0]-56.0)/400.0-0.25; lat=(300.0-P[:,1])/400.0
    polys.append(np.c_[z*1000.0,lat*1000.0])
allp=np.vstack(polys)
print('SVG union loops',len(polys),'station extent mm',allp[:,0].min().round(2),allp[:,0].max().round(2),'lateral',allp[:,1].min().round(2),allp[:,1].max().round(2))
# compare envelope at band centres
diffs=[]
for i in range(len(bins)-1):
    sc_=bins[i]+0.5
    ls=[]
    for P in polys:
        Q=np.vstack([P,P[:1]])
        s1,s2=Q[:-1,0],Q[1:,0]; l1,l2=Q[:-1,1],Q[1:,1]
        sel=(s1-sc_)*(s2-sc_)<0
        if sel.any(): ls.extend(list(l1[sel]+(l2[sel]-l1[sel])*(sc_-s1[sel])/(s2[sel]-s1[sel])))
    if not ls: diffs.append((sc_,None,None,top[i],bot[i])); continue
    diffs.append((sc_,max(ls)-top[i],min(ls)-bot[i],top[i],bot[i]))
dt=np.array([x[1] for x in diffs if x[1] is not None]); db=np.array([x[2] for x in diffs if x[2] is not None])
print('bands',len(diffs),'missing',sum(1 for x in diffs if x[1] is None))
print('top edge SVG-CAD mm: mean %.3f  min %.3f  max %.3f  p99abs %.3f'%(dt.mean(),dt.min(),dt.max(),np.percentile(np.abs(dt),99)))
print('bot edge SVG-CAD mm: mean %.3f  min %.3f  max %.3f  p99abs %.3f'%(db.mean(),db.min(),db.max(),np.percentile(np.abs(db),99)))
worst=sorted(diffs,key=lambda x:-(abs(x[1]) if x[1] is not None else 0))[:5]
for w in worst: print('worst top',[round(v,2) if v is not None else None for v in w])
worst=sorted(diffs,key=lambda x:-(abs(x[2]) if x[2] is not None else 0))[:5]
for w in worst: print('worst bot',[round(v,2) if v is not None else None for v in w])
