#!/usr/bin/env python3
"""walk_s723.py -- kit S723. Made-up repositories, mirrors and pins only.  python walk_s723.py <pc_kits_current.py> [--control]
--control runs the checks with the tool replaced by a do-nothing stand-in: it must go RED."""
import datetime as dt, hashlib, os, subprocess, sys, tempfile, time, zipfile

tool = os.path.abspath(sys.argv[1]); control = "--control" in sys.argv
md5 = lambda b: hashlib.md5(b).hexdigest()
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n); print(("  ok   " if c else "  FAIL ") + n)


def build(t, live_watch=b"watch v2\n", pin_watch=None, mirror_age_h=1, pin_txt=True, recep_pin=None, sums_crlf=False):
    kits = os.path.join(t, "repo", "deploy_kits", "PC_KITS"); canon = os.path.join(t, "repo", "deploy_kits", "KB_canon_all")
    os.makedirs(os.path.join(kits, "medical")); os.makedirs(os.path.join(kits, "reception")); os.makedirs(canon)
    mem = {"README.txt": b"read me\n", "setup_pc.py": b"print(1)\n", "payload/marg_watch.py": b"watch v1\n",
           "payload/marg_txt.py": b"txt v1\n", "payload/xlrd/book.py": b"book\n"}
    nl = "\r\n" if sums_crlf else "\n"
    sums = nl.join("%s  %s" % (md5(b), n) for n, b in mem.items()) + nl
    z = os.path.join(kits, "medical", "kit.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zo:
        zo.writestr(zipfile.ZipInfo("MD5SUMS.txt", (2026, 10, 11, 12, 0, 0)), sums)
        for n, b in mem.items():
            zo.writestr(zipfile.ZipInfo(n, (2026, 10, 3, 12, 0, 0)), b)
    open(os.path.join(kits, "medical", "KIT_INFO.txt"), "w").write("# medical\nversion=installer S458.1 (agent S499.1)\npacked=11-Oct-2026\nkit_md5=%s\npython_file=p.zip\n" % md5(open(z, "rb").read()))
    rmem = {"reception_agent.py": b"agent A\n", "config.json": b"{}\n"}
    rz = os.path.join(kits, "reception", "kit.zip")
    with zipfile.ZipFile(rz, "w") as zo:
        zo.writestr("MD5SUMS.txt", "\n".join("%s  %s" % (md5(b), n) for n, b in rmem.items()) + "\n%s  pyportable.zip\n" % ("0" * 32))
        for n, b in rmem.items():
            zo.writestr(n, b)
    open(os.path.join(kits, "reception", "KIT_INFO.txt"), "w").write("kit_md5=%s\n" % md5(open(rz, "rb").read()))
    mir = os.path.join(t, "mirror"); os.makedirs(os.path.join(mir, "xlrd"))
    open(os.path.join(mir, "marg_watch.py"), "wb").write(live_watch)
    open(os.path.join(mir, "marg_txt.py"), "wb").write(b"txt v1\n")
    open(os.path.join(mir, "xlrd", "book.py"), "wb").write(b"book\n")
    open(os.path.join(mir, "token.txt"), "wb").write(b"SECRET\n")
    open(os.path.join(mir, "push_state.json"), "w").write("{}")
    old = time.time() - mirror_age_h * 3600
    os.utime(os.path.join(mir, "push_state.json"), (old, old))
    rows = ["VPS\t%s\tmedical PC D:\\SendToClinic\\marg_watch.py\tS679" % (pin_watch or md5(live_watch)),
            "VPS\t%s\tmedical D:\\SendToClinic\\marg_watch.py\tolder row" % md5(b"watch v0\n"),
            "VPS\t%s\treceptionpc C:\\ClinicAgent\\reception_agent.py\tS456.1" % (recep_pin or md5(b"agent A\n"))]
    if pin_txt:
        rows.append("VPS\t%s\tmedical PC D:\\SendToClinic\\marg_txt.py\tx" % md5(b"txt v1\n"))
    open(os.path.join(canon, "live_pins_S391close.txt"), "w").write("\n".join(rows) + "\n")
    tools = os.path.join(t, "tools"); os.makedirs(tools)
    open(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt"), "w").write("GREEN\n")
    return kits, mir, tools


def run(t, mir, tools, *extra):
    if control:
        return 0, ""
    p = subprocess.run([sys.executable, "-B", tool, "--tools", tools, "--repo", os.path.join(t, "repo"), "--mirror", mir] + list(extra),
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


for crlf in (False, True):
    tag = "CRLF sums" if crlf else "LF sums"
    t = tempfile.mkdtemp(prefix="s723_"); kits, mir, tools = build(t, sums_crlf=crlf)
    z = os.path.join(kits, "medical", "kit.zip"); before = zipfile.ZipFile(z); bnames = before.namelist(); bdata = {n: before.read(n) for n in bnames}; before.close()
    rc, out = run(t, mir, tools)
    a = zipfile.ZipFile(z); an = a.namelist(); ad = {n: a.read(n) for n in an}; a.close()
    ck("%s: REPACKED, rc 0" % tag, rc == 0 and "REPACKED" in out)
    ck("%s: marg_watch.py now the PC's bytes" % tag, ad.get("payload/marg_watch.py") == b"watch v2\n")
    ck("%s: every other member byte-identical, same order" % tag, an == bnames and all(ad[n] == bdata[n] for n in an if n not in ("payload/marg_watch.py", "MD5SUMS.txt")))
    s = ad["MD5SUMS.txt"].decode()
    ck("%s: MD5SUMS proves every member and keeps its line ending" % tag, all(md5(ad[l[34:]]) == l[:32] for l in s.splitlines() if l) and (("\r\n" in s) == crlf))
    info = open(os.path.join(kits, "medical", "KIT_INFO.txt")).read()
    ck("%s: KIT_INFO kit_md5 = the new zip, packed today, version says S723" % tag, ("kit_md5=" + md5(open(z, "rb").read())) in info and "repacked by S723" in info and "packed=" in info and "11-Oct-2026" not in info)
    ck("%s: token.txt is never packed" % tag, not any("token" in n for n in an))
    ck("%s: the rehearsal report moved aside" % tag, not os.path.exists(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt")) and any(n.startswith("PC_KITS_REHEARSAL_before_S723_") for n in os.listdir(tools)))
    ck("%s: the report written" % tag, os.path.isfile(os.path.join(tools, "PC_KITS_CURRENT_LATEST.txt")))
    zb1 = open(z, "rb").read()
    rc2, out2 = run(t, mir, tools)
    ck("%s: a second night says CURRENT and writes nothing" % tag, "medical    CURRENT" in out2 and open(z, "rb").read() == zb1)
    ck("%s: reception CURRENT (the bundled Python beside the zip is not a fault)" % tag, "reception  CURRENT" in out)

cases = [("a mirror 30 hours old", dict(mirror_age_h=30), "REFUSED"),
         ("the mirror's copy is not its newest pin", dict(pin_watch=md5(b"watch v3\n")), "CURRENT"),
         ("a changed member with no pin at all", dict(live_watch=b"watch v2\n"), None)]
for name, kw, want in cases[:2]:
    t = tempfile.mkdtemp(prefix="s723c_"); kits, mir, tools = build(t, **kw)
    z = os.path.join(kits, "medical", "kit.zip"); b = open(z, "rb").read(); inf = open(os.path.join(kits, "medical", "KIT_INFO.txt")).read()
    rc, out = run(t, mir, tools)
    ck("left as packed: %s (%s)" % (name, want), (want in out) and open(z, "rb").read() == b and open(os.path.join(kits, "medical", "KIT_INFO.txt")).read() == inf
       and os.path.exists(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt")))
t = tempfile.mkdtemp(prefix="s723n_"); kits, mir, tools = build(t, pin_txt=False)
open(os.path.join(mir, "marg_txt.py"), "wb").write(b"txt v9\n")
rc, out = run(t, mir, tools)
zz = zipfile.ZipFile(os.path.join(kits, "medical", "kit.zip"))
ck("a member with no live pin is left as packed (and said so)", "has no live pin" in out and zz.read("payload/marg_txt.py") == b"txt v1\n" and zz.read("payload/marg_watch.py") == b"watch v2\n")
t = tempfile.mkdtemp(prefix="s723w_"); kits, mir, tools = build(t)
open(os.path.join(kits, "medical", "KIT_INFO.txt"), "a").write("")
with open(os.path.join(kits, "medical", "kit.zip"), "ab") as fh:
    fh.write(b"x")
rc, out = run(t, mir, tools)
ck("a kit.zip that is not the one KIT_INFO names: REFUSED, nothing touched", "REFUSED" in out and "not whole" in out)
t = tempfile.mkdtemp(prefix="s723d_"); kits, mir, tools = build(t)
z = os.path.join(kits, "medical", "kit.zip"); b = open(z, "rb").read()
rc, out = run(t, mir, tools, "--dry")
ck("--dry: says BEHIND, writes nothing (no report, the rehearsal report stays)", "BEHIND (dry run)" in out and open(z, "rb").read() == b
   and not os.path.exists(os.path.join(tools, "PC_KITS_CURRENT_LATEST.txt")) and os.path.exists(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt")))
t = tempfile.mkdtemp(prefix="s723r_"); kits, mir, tools = build(t, recep_pin=md5(b"agent B\n"))
rz = os.path.join(kits, "reception", "kit.zip"); b = open(rz, "rb").read()
rc, out = run(t, mir, tools)
ck("reception behind its pin: BEHIND, report only, the zip untouched", "reception  BEHIND" in out and open(rz, "rb").read() == b)
print(("WALK OK %d/%d" % (len(oks), len(oks) + len(fails))) if not fails else ("WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails))))
sys.exit(1 if fails else 0)
