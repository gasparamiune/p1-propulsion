# Independent GLB measurement (verifier). Vehicle frame: x=X_gltf, y=-Z_gltf, z=Y_gltf + 0.203 (pivot station).
import sys, json, numpy as np, trimesh
glb = sys.argv[1]
sc = trimesh.load(glb, force='scene')
rows = []
allv = []
for node in sc.graph.nodes_geometry:
    T, gname = sc.graph[node]
    g = sc.geometry[gname]
    v = trimesh.transformations.transform_points(g.vertices, T)
    veh = np.column_stack([v[:,0], -v[:,2], v[:,1]])
    allv.append(veh)
    r = np.hypot(veh[:,0], veh[:,1])
    i = int(np.argmax(r))
    rows.append(dict(node=node, zmin=float(veh[:,2].min()), zmax=float(veh[:,2].max()), rmax=float(r.max()),
                     az_rmax=float(np.degrees(np.arctan2(veh[i,1], veh[i,0])) % 360), c=[float(x) for x in veh.mean(0)]))
A = np.vstack(allv); rA = np.hypot(A[:,0], A[:,1])
print('instances', len(rows))
print('axial about pivot mm: %.2f .. %.2f' % (A[:,2].min()*1e3, A[:,2].max()*1e3))
print('extent x,y mm: %.2f %.2f' % ((A[:,0].max()-A[:,0].min())*1e3, (A[:,1].max()-A[:,1].min())*1e3))
print('r_max mm %.2f' % (rA.max()*1e3))
rows.sort(key=lambda d: -d['rmax'])
print('top-r parts:')
for d in rows[:8]: print('  %-22s r %.2f mm az %.1f z %.1f..%.1f mm' % (d['node'], d['rmax']*1e3, d['az_rmax'], d['zmin']*1e3, d['zmax']*1e3))
for key in ['ENG-BL-06','ENG-GM-09','ENG-GM-10','ENG-GM-03','ENG-TC-01','ENG-FD-12F','ENG-FS-15']:
    for d in rows:
        if d['node'].startswith(key):
            print('%-22s z %.1f..%.1f mm (pivot) -> vehicle %.4f..%.4f m, rmax %.2f mm, az(rmax) %.1f, centroid %s' % (d['node'], d['zmin']*1e3, d['zmax']*1e3, d['zmin']+0.203, d['zmax']+0.203, d['rmax']*1e3, d['az_rmax'], [round(x,4) for x in d['c']]))
# Top of engine: which part
top = max(rows, key=lambda d: d['zmax']); bot = min(rows, key=lambda d: d['zmin'])
print('top part', top['node'], top['zmax']*1e3, ' bottom part', bot['node'], bot['zmin']*1e3)
