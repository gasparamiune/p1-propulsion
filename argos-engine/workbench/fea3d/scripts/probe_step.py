import sys, json
import cadquery as cq
man = json.load(open('/home/claude/work/mechanical/engine/03-cad/assembly/assembly_manifest_v3.5.json'))
mb = {i['inst']: i for i in man['instances']}
for pn in sys.argv[1:]:
    s = cq.importers.importStep(f'/home/claude/work/mechanical/engine/03-cad/parts/{pn}.step')
    sols = s.solids().vals()
    bb = s.val().BoundingBox()
    print(pn, 'nsolids', len(sols), 'vol', round(sum(x.Volume() for x in sols),3), 'bb', [round(v,2) for v in (bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax)])
    for k,v in mb.items():
        if k.startswith(pn+'#'):
            print('   manifest', k, v['group'], v['body'], v['bounds_mm'])
