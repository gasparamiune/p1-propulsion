"""Reviewer write guard: run a script with an audit hook that refuses any filesystem write outside the scratch area."""
import os, sys, runpy
ALLOW = [os.path.realpath(os.environ["RV_ALLOW"])] + ["/dev/null", "/proc/self"]
WFLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
def _ok(p):
    if isinstance(p, int): return True
    if isinstance(p, bytes): p = p.decode(errors="replace")
    rp = os.path.realpath(os.path.abspath(p))
    return any(rp == a or rp.startswith(a + "/") for a in ALLOW)
def hook(ev, args):
    if ev == "open":
        path, mode, flags = args
        w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (mode is None and isinstance(flags, int) and (flags & WFLAGS))
        if w and not _ok(path):
            raise PermissionError(f"RV guard: write refused outside scratch: {path} ({mode})")
    elif ev in ("os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime", "os.truncate", "shutil.rmtree", "os.unlink"):
        if args and not _ok(args[0]):
            raise PermissionError(f"RV guard: {ev} refused outside scratch: {args[0]}")
    elif ev in ("os.rename", "os.replace", "os.symlink", "os.link", "shutil.copyfile", "shutil.copytree", "shutil.move"):
        if len(args) > 1 and not _ok(args[1]):
            raise PermissionError(f"RV guard: {ev} refused outside scratch: {args[1]}")
sys.addaudithook(hook)
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
