import json, math, numpy as np, trimesh
CAD='/home/claude/work/shared-fallback/engine/03-cad/v3.5.1'
sc=trimesh.load(f'{CAD}/assembly/ENGINE_v3.5.1_neutral.glb')
man={i['inst']:i for i in json.load(open(f'{CAD}/assembly/assembly_manifest_v3.5.1.json'))['instances']}
meshes=[]
for inst in sc.graph.nodes_geometry:
    if man[inst]['group']!='engine': continue
    T,g=sc.graph[inst]; m=sc.geometry[g].copy(); m.apply_transform(T)
    V=m.vertices*1000.0; m.vertices=np.c_[V[:,0],-V[:,2],V[:,1]]; meshes.append(m)
M=trimesh.util.concatenate(meshes)
rng=np.random.default_rng(1)
P,_=trimesh.sample.sample_surface(M,400000,seed=1)
P=np.vstack([P,M.vertices])
q=P[P[:,2]<-99.8]
r=np.hypot(q[:,0],q[:,1])
for z0 in (-100,-120,-150,-180,-200,-220,-238):
    sel=(q[:,2]<z0+5)&(q[:,2]>=z0-5)
    if sel.any(): print('engine group r max in z %d+-5: %.2f'%(z0, r[sel].max()))
th=math.radians(8.0); best=0
for phi in np.radians(np.arange(0,360,1.0)):
    ax=np.array([-math.sin(phi),math.cos(phi),0.0]); K=np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])
    R=np.eye(3)+math.sin(th)*K+(1-math.cos(th))*K@K
    rr=np.hypot(*(q@R.T)[:,:2].T); best=max(best,rr.max())
print('dense-sampled 8 deg sweep r max below GM-10 aft face: %.2f mm'%best)
