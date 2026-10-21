import json, sys
a = json.load(open(sys.argv[1], encoding='utf-8')); b = json.load(open(sys.argv[2], encoding='utf-8'))
la = a.get('limits_v2p11', []); lb = b.get('limits_v2p11', [])
print('v4.1 limits', len(la), 'v4.2 limits', len(lb))
na = {json.dumps(x.get('limit'), ensure_ascii=False) for x in la}
new = [x for x in lb if json.dumps(x.get('limit'), ensure_ascii=False) not in na]
print('new rows', len(new))
for x in new:
    v = x.get('value')
    print(' -', str(x.get('limit'))[:70], '|', json.dumps(v, ensure_ascii=False)[:150])
print('log_v13:', json.dumps(b.get('log_v13'), ensure_ascii=False)[:1500])
print('v4.2 version/date', b.get('version'), b.get('date'), '| v4.1', a.get('version'))
for i in (4, 7, 14):
    print('limits[%d]' % i, json.dumps(lb[i], ensure_ascii=False)[:600])
