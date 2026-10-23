import csv, sys
p = sys.argv[1]
rows = list(csv.DictReader(open(p, newline='', encoding='utf-8')))
print('n rows', len(rows))
want = set(sys.argv[2].split(','))
for r in rows:
    if r['line'] in want:
        print('=== line', r['line'])
        for k in ['section','refs','qty','spare_recommended','part','description','vendor','vendor_alt','order_key','unit_price','currency','price_basis','price_source','delivered_price_DK6400','tag','owner','note']:
            print('  ', k, ':', r[k][:900])
# count price_basis TO-QUOTE and delivered fields
from collections import Counter
print('price_basis', Counter(r['price_basis'] for r in rows).most_common(6))
print('unit_price nonempty', sum(1 for r in rows if r['unit_price'].strip()))
print('delivered not starting TO-QUOTE', [r['line'] for r in rows if not r['delivered_price_DK6400'].startswith('TO-QUOTE')][:20])
print('Sonderborg spelled', Counter(('Sonderborg' in r['delivered_price_DK6400'], 'Soenderborg' in r['delivered_price_DK6400'], 'DK-6400' in r['delivered_price_DK6400']) for r in rows))
