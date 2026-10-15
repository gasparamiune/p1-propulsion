#!/usr/bin/env python3
"""REV-ELEC-2: generate a C++ program that prints every scalar constexpr in config.h (values as compiled, base build)."""
import re, sys
src = open(sys.argv[1]).read()
names = re.findall(r'constexpr\s+(?:float|double|int|bool|uint16_t)\s+(k\w+)\s*=', src)
seen = []
for n in names:
    if n not in seen:
        seen.append(n)
out = ['#include <cstdio>', '#include "config.h"', 'int main() {']
for n in seen:
    out.append('  std::printf("%%s %%.9g\\n", "%s", static_cast<double>(ecu::cfg::%s));' % (n, n))
out.append('  return 0;\n}')
open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
print(len(seen), 'constants')
