#!/usr/bin/env python3
# REV-ELEC-4 reviewer SIL variant (NOT the author's code; never compared with the author's binaries).
# Copies the rebuilt v2.12 tree /dev/shm/rev_elec4/fw to /dev/shm/rev_elec4/fw_rv (without build/) and patches scS13T in
# sil/sc_v212.inc so that environment variables select the cases:
#   RV_COMPS="name:eps:errK[:err_from_s];..."  replaces the four compensation variants (err_from default 0.70 s, as the author's)
#   RV_KS="2,3"  replaces the k list;  RV_STAND_ONLY=1 skips the A1 location;  RV_T0="24" keeps one T0
# Everything else (plant, firmware core, drift model, seat histories) is the author's v2.12 code unchanged.
import hashlib, shutil, sys
SRC = '/dev/shm/rev_elec4/fw'
DST = '/dev/shm/rev_elec4/fw_rv'
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('build'))
p = DST + '/sil/sc_v212.inc'
s = open(p).read()
def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)
rep('struct Comp { const char* name; bool tc; double eps, err_K; };\n'
    '  const Comp comps[] = {{"off", false, 0.0, 0.0}, {"comp", true, 0.0, 0.0}, {"comp_under", true, -0.10, -0.30}, {"comp_over", true, 0.10, 0.30}};',
    'struct Comp { const char* name; bool tc; double eps, err_K, err_from; };\n'
    '  std::vector<Comp> comps = {{"off", false, 0.0, 0.0, 0.70}, {"comp", true, 0.0, 0.0, 0.70}, {"comp_under", true, -0.10, -0.30, 0.70}, {"comp_over", true, 0.10, 0.30, 0.70}};\n'
    '  static std::vector<std::string> rv_names; rv_names.reserve(64);   // REV-ELEC-4 reviewer variant (env RV_*)\n'
    '  if (const char* e = std::getenv("RV_COMPS")) {\n'
    '    comps.clear(); std::string all(e); size_t a = 0;\n'
    '    while (a < all.size()) { size_t b = all.find(\';\', a); if (b == std::string::npos) b = all.size(); std::string it = all.substr(a, b - a); a = b + 1;\n'
    '      if (it.empty()) continue; std::vector<std::string> f; size_t u = 0; while (true) { size_t v = it.find(\':\', u); f.push_back(it.substr(u, v == std::string::npos ? std::string::npos : v - u)); if (v == std::string::npos) break; u = v + 1; }\n'
    '      rv_names.push_back(f[0]); comps.push_back({rv_names.back().c_str(), true, std::atof(f[1].c_str()), std::atof(f[2].c_str()), f.size() > 3 ? std::atof(f[3].c_str()) : 0.70}); } }')
rep('const double ks[] = {1.0, 1.5, 2.0, 3.0};',
    'std::vector<double> ks = {1.0, 1.5, 2.0, 3.0};\n'
    '  if (const char* e = std::getenv("RV_KS")) { ks.clear(); std::string all(e); size_t a = 0; while (a < all.size()) { size_t b = all.find(\',\', a); if (b == std::string::npos) b = all.size(); ks.push_back(std::atof(all.substr(a, b - a).c_str())); a = b + 1; } }\n'
    '  const bool rv_stand_only = std::getenv("RV_STAND_ONLY") != nullptr; const char* rv_t0 = std::getenv("RV_T0");')
rep('  for (const Loc& L : locs)\n    for (double T0 : L.T0C)\n      for (const Comp& cp : comps) {\n        if (cp.eps != 0.0 && T0 != (L.stand ? 24.0 : 20.0)) continue;',
    '  for (const Loc& L : locs)\n    for (double T0 : L.T0C)\n      for (const Comp& cp : comps) {\n        if (rv_stand_only && !L.stand) continue;\n        if (rv_t0 && T0 != std::atof(rv_t0)) continue;\n        if (cp.eps != 0.0 && T0 != (L.stand ? 24.0 : 20.0)) continue;')
rep('c.seat_tc = cp.tc; c.seat_tc_err_K = cp.err_K;', 'c.seat_tc = cp.tc; c.seat_tc_err_K = cp.err_K; c.seat_tc_err_from = cp.err_from;')
open(p, 'w').write(s)
print('patched', p, hashlib.sha256(s.encode()).hexdigest()[:16])
