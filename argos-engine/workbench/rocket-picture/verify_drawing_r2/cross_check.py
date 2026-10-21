# Independent check: any drawn line/path segment (not only callout leaders) crossing a text box, wide (desktop) state.
import re, xml.etree.ElementTree as ET
from PIL import ImageFont
SVG='/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/drawing/rocket_side_view.svg'
FS={'t1':(22,700),'t2':(12.5,400),'key':(15.5,700),'fine':(12,400),'tag':(10,700),'sm':(11,400),'hd':(13,700),'tb':(12.5,400),'tbb':(12.5,700),'tbs':(11.5,400),'big':(27,700)}
fonts={}
def font(sz,w):
    k=(sz,w)
    if k not in fonts:
        p='/usr/share/fonts/opentype/inter/Inter-Bold.otf' if w>=700 else '/usr/share/fonts/opentype/inter/Inter-Regular.otf'
        fonts[k]=ImageFont.truetype(p, size=100)
    return fonts[k]
ns={'s':'http://www.w3.org/2000/svg'}
root=ET.parse(SVG).getroot()
boxes=[]; segs=[]
def walk(el, inh_cls):
    cls=(el.get('class') or '').split()
    state=inh_cls
    if 'nar' in cls: state='nar'
    if 'wide' in cls: state='wide'
    tag=el.tag.split('}')[1]
    if tag=='text' and el.get('transform') is None:
        sz,w=None,400
        for c in cls:
            if c in FS: sz,w=FS[c] if sz is None else (sz,max(w,FS[c][1]))
        st=el.get('style') or ''
        m=re.search(r'font-size:([\d.]+)px',st)
        if m: sz=float(m.group(1))
        sz=sz or 16
        # concatenate text including tspans; tspans with own class (tag) measured separately approx
        x=float(el.get('x')); y=float(el.get('y'))
        total=0.0
        parts=[(el.text or '', sz, w)]
        for t in el:
            tc=(t.get('class') or '').split(); tsz,tw=sz,w
            for c in tc:
                if c in FS: tsz,tw=FS[c]
            dx=float(t.get('dx') or 0)
            parts.append((' '*0, tsz, tw)); total+=dx
            parts.append((t.text or '', tsz, tw)); parts.append((t.tail or '', sz, w))
        for s_,z_,w_ in parts:
            if s_: total+=font(z_,w_).getlength(s_)*z_/100.0
        anc=el.get('text-anchor') or 'start'
        x0={'start':x,'middle':x-total/2,'end':x-total}[anc]
        txt=''.join(el.itertext())
        boxes.append((x0,y-0.73*sz,x0+total,y+0.22*sz,state,txt))
    elif tag=='line':
        segs.append(((float(el.get('x1')),float(el.get('y1'))),(float(el.get('x2')),float(el.get('y2'))),state,el.get('stroke')))
    elif tag=='path':
        st=el.get('stroke') or ''
        if st.lower() in ("#f0a04b","none") or el.get("fill","").lower()=="#f0a04b" or re.search(r"[AaCcQqHhVvSsTt]", el.get("d")): pass
        else:
            nums=re.findall(r'[-\d.]+', el.get('d'))
            pts=[(float(nums[i]),float(nums[i+1])) for i in range(0,len(nums)-1,2)]
            for a,b in zip(pts[:-1],pts[1:]): segs.append((a,b,state,st))
    for ch in el: walk(ch,state)
walk(root,'both')
def seg_box(a,b,bx):
    (x0,y0,x1,y1)=bx
    # Liang-Barsky clip
    dx=b[0]-a[0]; dy=b[1]-a[1]; t0,t1=0.0,1.0
    for p,q in ((-dx,a[0]-x0),(dx,x1-a[0]),(-dy,a[1]-y0),(dy,y1-a[1])):
        if p==0:
            if q<0: return False
        else:
            t=q/p
            if p<0: t0=max(t0,t)
            else: t1=min(t1,t)
    return t0<t1
hits=[]
for st in ('wide','nar'):
    B=[b for b in boxes if b[4] in (st,'both')]; S=[s for s in segs if s[2] in (st,'both')]
    for b in B:
        for s in S:
            if seg_box(s[0],s[1],b[:4]): hits.append((st,b[5][:60],s[0],s[1],s[3]))
seen=set()
for h in hits:
    k=(h[0],h[1],h[4])
    if k in seen: continue
    seen.add(k); print(h)
print('boxes',len(boxes),'segs',len(segs),'hits',len(hits))
oob=[b for b in boxes if b[0]<0 or b[2]>1000 or b[1]<0 or b[3]>872]
print('out of canvas:',[(b[5][:40],round(b[0],1),round(b[2],1)) for b in oob])
