import re, sys
src = open(sys.argv[1]).read()
i = 0; bad = 0; n = 0
while True:
    j = src.find('sf("', i)
    if j < 0: break
    k = j + 3  # at the opening quote
    # read the string literal (with possible adjacent literals)
    fmt = ''
    p = k
    while True:
        assert src[p] == '"'
        q = p + 1
        while src[q] != '"' or src[q-1] == '\\': q += 1
        fmt += src[p+1:q]
        p = q + 1
        while src[p] in ' \n\t': p += 1
        if src[p] != '"': break
    # now parse args until the matching close paren
    depth = 1; args = 0; cur = ''; r = p
    while depth > 0:
        ch = src[r]
        if ch in '([{': depth += 1
        elif ch in ')]}': depth -= 1
        if depth == 1 and ch == ',': args += 1
        r += 1
    specs = len(re.findall(r'%(?!%)[-+ #0]*\d*(?:\.\d+)?[a-zA-Z]', fmt.replace('%%', '')))
    n += 1
    line = src.count('\n', 0, j) + 1
    if specs != args or specs > 6:
        bad += 1; print('MISMATCH line', line, 'specs', specs, 'args', args, fmt[:90])
    i = r
print('sf calls', n, 'mismatches', bad)
