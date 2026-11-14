#!/usr/bin/env python3
"""walk_s822.py -- kit S822_PC_KITS_CURRENT_NEW_FILES (S456, the parent, 14-Nov-2026). Made-up repositories, mirrors, pins
and a made-up 'PC folder' standing in for the medical PC's share. Nothing live is touched.

  python walk_s822.py <pc_kits_current.py>             the new tool: every check must pass (GREEN)
  python walk_s822.py <pc_kits_current.py> --control   the OLD tool (S723+S794): the S822 checks must FAIL (RED as it must be)

What S822 adds: a program file at the top of the medical mirror that the kit does not carry is ADDED to the kit when the PC's
own folder lists it tonight and its bytes are its newest live pin; otherwise it is reported and never packed."""
import hashlib, os, re, shutil, subprocess, sys, tempfile, time, zipfile

tool = os.path.abspath(sys.argv[1]); control = "--control" in sys.argv
md5 = lambda b: hashlib.md5(b).hexdigest()
oks, fails = [], []
S822_CHECKS = []          # the checks the old tool must fail


def ck(n, c, s822=False):
    (oks if c else fails).append(n); print(("  ok   " if c else "  FAIL ") + n)
    if s822:
        S822_CHECKS.append((n, c))


def build(t, sums_crlf=False, pc_files=(), mirror_extra=None, pin_rows=(), live_watch=b"watch v1\n", trailing_nl=True):
    kits = os.path.join(t, "repo", "deploy_kits", "PC_KITS"); canon = os.path.join(t, "repo", "deploy_kits", "KB_canon_all")
    os.makedirs(os.path.join(kits, "medical")); os.makedirs(os.path.join(kits, "reception")); os.makedirs(canon)
    mem = {"README.txt": b"read me\n", "setup_pc.py": b"print(1)\n", "payload/marg_watch.py": b"watch v1\n",
           "payload/marg_txt.py": b"txt v1\n", "payload/xlrd/book.py": b"book\n"}
    nl = "\r\n" if sums_crlf else "\n"
    sums = nl.join("%s  %s" % (md5(b), n) for n, b in mem.items()) + (nl if trailing_nl else "")
    z = os.path.join(kits, "medical", "kit.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zo:
        zo.writestr(zipfile.ZipInfo("MD5SUMS.txt", (2026, 10, 11, 12, 0, 0)), sums)
        for n, b in mem.items():
            zo.writestr(zipfile.ZipInfo(n, (2026, 10, 3, 12, 0, 0)), b)
    open(os.path.join(kits, "medical", "KIT_INFO.txt"), "w").write(
        "# medical\nversion=installer S458.1 (agent S499.1)\npacked=11-Oct-2026\nkit_md5=%s\npython_file=p.zip\n" % md5(open(z, "rb").read()))
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
    for n, b in (mirror_extra or {}).items():
        open(os.path.join(mir, n), "wb").write(b)
    pc = os.path.join(t, "pc_share"); os.makedirs(pc)
    for n in pc_files:
        open(os.path.join(pc, n), "wb").write(b"")
    rows = ["VPS\t%s\tmedical PC D:\\SendToClinic\\marg_watch.py\tS679" % md5(live_watch),
            "VPS\t%s\tmedical PC D:\\SendToClinic\\marg_txt.py\tx" % md5(b"txt v1\n"),
            "VPS\t%s\treceptionpc C:\\ClinicAgent\\reception_agent.py\tS456.1" % md5(b"agent A\n")] + list(pin_rows)
    open(os.path.join(canon, "live_pins_S453close.txt"), "w").write("\n".join(rows) + "\n")
    tools = os.path.join(t, "tools"); os.makedirs(tools)
    open(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt"), "w").write("GREEN\n")
    return kits, mir, tools, pc


def run(t, mir, tools, pc, *extra):
    args = [sys.executable, "-B", tool, "--tools", tools, "--repo", os.path.join(t, "repo"), "--mirror", mir]
    extra = [e for e in extra if not (control and e == "--no-share")]   # the OLD tool knows no --share / --no-share
    if pc is not None and not control:
        args += ["--share", pc]
    p = subprocess.run(args + list(extra), capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def zipmap(z):
    with zipfile.ZipFile(z) as a:
        return a.namelist(), {n: a.read(n) for n in a.namelist()}


GUARD = b"print('guard')\n"
PIN_GUARD = "VPS\t%s\tmedical PC D:\\SendToClinic\\guard.py\tS9xx NEW" % md5(GUARD)

# ---- A1: a new program file on the PC, pinned equal -> ADDED -----------------------------------------------------
for crlf in (False, True):
    tag = "A1 %s" % ("CRLF sums" if crlf else "LF sums")
    t = tempfile.mkdtemp(prefix="s822a_")
    kits, mir, tools, pc = build(t, sums_crlf=crlf, pc_files=("guard.py", "marg_watch.py", "marg_txt.py"), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,))
    z = os.path.join(kits, "medical", "kit.zip"); bn, bd = zipmap(z)
    rc, out = run(t, mir, tools, pc)
    an, ad = zipmap(z)
    ck("%s: REPACKED, rc 0, the line says NEW guard.py" % tag, rc == 0 and "REPACKED" in out and "guard.py NEW" in out, s822=True)
    ck("%s: payload/guard.py is in the kit with the PC's bytes" % tag, ad.get("payload/guard.py") == GUARD, s822=True)
    ck("%s: every old member byte-identical, same order, the new one after them" % tag,
       an[:len(bn)] == bn and all(ad[n] == bd[n] for n in bn if n != "MD5SUMS.txt") and an[len(bn):] == ["payload/guard.py"], s822=True)
    s = ad["MD5SUMS.txt"].decode()
    rows = [l for l in s.splitlines() if l]
    ck("%s: MD5SUMS has a row for the new member, proves every member, keeps its line ending and its final newline" % tag,
       any(l == "%s  payload/guard.py" % md5(GUARD) for l in rows) and all(md5(ad[l[34:]]) == l[:32] for l in rows)
       and (("\r\n" in s) == crlf) and s.endswith("\r\n" if crlf else "\n"), s822=True)
    info = open(os.path.join(kits, "medical", "KIT_INFO.txt")).read()
    ck("%s: KIT_INFO kit_md5 = the new zip, version says 'added guard.py'" % tag,
       ("kit_md5=" + md5(open(z, "rb").read())) in info and "added guard.py" in info and "packed=" in info, s822=True)
    ck("%s: the new zip proves itself as a kit (setup_pc reads payload from MD5SUMS rows)" % tag,
       sorted(n for n in an if n.startswith("payload/")) == sorted(l[34:] for l in rows if l[34:].startswith("payload/")))
    ck("%s: token.txt and push_state.json never packed" % tag, not any("token" in n or "push_state" in n for n in an))
    ck("%s: the rehearsal report moved aside; the report written" % tag,
       not os.path.exists(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt")) and os.path.isfile(os.path.join(tools, "PC_KITS_CURRENT_LATEST.txt")))
    zb1 = open(z, "rb").read()
    rc2, out2 = run(t, mir, tools, pc)
    ck("%s: a second night says CURRENT and writes nothing" % tag, "medical    CURRENT" in out2 and open(z, "rb").read() == zb1)
    ck("%s: the report header names the PC's folder as read" % tag, "the PC : its SendToClinic folder listed" in out, s822=True)
    shutil.rmtree(t, ignore_errors=True)

# ---- A2: on the PC, no pin -> reported, not packed --------------------------------------------------------------------
t = tempfile.mkdtemp(prefix="s822b_")
kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": GUARD})
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read(); i0 = open(os.path.join(kits, "medical", "KIT_INFO.txt")).read()
rc, out = run(t, mir, tools, pc)
ck("A2: a new file on the PC with no live pin -> 'NEW guard.py: on the PC, no live pin' and the kit untouched",
   "NEW guard.py: on the PC, no live pin" in out and open(z, "rb").read() == b0 and open(os.path.join(kits, "medical", "KIT_INFO.txt")).read() == i0, s822=True)
ck("A2: the medical line is still CURRENT (nothing behind), the note beside it", "medical    CURRENT" in out and "not packed" in out)
shutil.rmtree(t, ignore_errors=True)

# ---- A3: on the PC, pinned, but the mirror's bytes are not the pin -> not packed ---------------------------------------
t = tempfile.mkdtemp(prefix="s822c_")
kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": b"print('other')\n"}, pin_rows=(PIN_GUARD,))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc)
ck("A3: the mirror's copy is not its newest pin -> 'is not its newest pin', not packed", "NEW guard.py: on the PC, the mirror" in out and "not its newest pin" in out and open(z, "rb").read() == b0, s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A4: in the mirror only (the PC no longer has it) -> mirror-only, not packed -------------------------------------
t = tempfile.mkdtemp(prefix="s822d_")
kits, mir, tools, pc = build(t, pc_files=("marg_watch.py",), mirror_extra={"guard.py": GUARD, "START_OLD.bat": b"@echo off\n"}, pin_rows=(PIN_GUARD,))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc)
ck("A4: a pinned file the PC no longer has -> 'mirror-only (that PC no longer has it)', not packed",
   "NEW guard.py: mirror-only" in out and "NEW START_OLD.bat: mirror-only" in out and open(z, "rb").read() == b0, s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A5: the PC unreachable (--no-share, and a share path that does not exist) -> unknown, not packed -------------------
for mode in ("--no-share", "missing"):
    t = tempfile.mkdtemp(prefix="s822e_")
    kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,))
    z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
    if mode == "--no-share":
        rc, out = run(t, mir, tools, None, "--no-share")
        ck("A5 --no-share: the header says the PC was not asked; NEW guard.py 'on the PC unknown tonight'; not packed",
           "the PC : not asked" in out and "on the PC unknown tonight" in out and open(z, "rb").read() == b0, s822=True)
    else:
        rc, out = run(t, mir, tools, os.path.join(t, "no_such_share"))
        ck("A5 unreachable share: the header says 'could NOT be listed tonight'; the note says why; 'on the PC unknown tonight'; not packed; still CURRENT",
           "the PC : could NOT be listed tonight" in out and "could not be listed tonight (" in out and "on the PC unknown tonight" in out and open(z, "rb").read() == b0 and "medical    CURRENT" in out, s822=True)
    shutil.rmtree(t, ignore_errors=True)

# ---- A6: leftovers and non-program files are never looked at ---------------------------------------------------------
t = tempfile.mkdtemp(prefix="s822f_")
extra = {"guard.py.bak": GUARD, "marg_watch.py.before_12345678": GUARD, "medical_agent_S499_1_RETIRED.py.txt": GUARD, "old.py.superseded_S229": GUARD,
         "agent.log": b"log\n", "heartbeat.txt": b"hb\n", "notes.md": b"n\n", "kit.zip": b"PK"}
kits, mir, tools, pc = build(t, pc_files=tuple(extra), mirror_extra=extra, pin_rows=tuple("VPS\t%s\tmedical PC D:\\SendToClinic\\%s\tx" % (md5(GUARD), n) for n in extra))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc)
ck("A6: backups, leftovers, logs, text and zips are never looked at -> CURRENT, no NEW line, the kit untouched",
   "medical    CURRENT" in out and "NEW " not in out and open(z, "rb").read() == b0)
shutil.rmtree(t, ignore_errors=True)

# ---- A7: a changed member AND a new file the same night -> one repack with both --------------------------------------
t = tempfile.mkdtemp(prefix="s822g_")
kits, mir, tools, pc = build(t, sums_crlf=True, pc_files=("guard.py", "marg_watch.py"), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,), live_watch=b"watch v2\n")
z = os.path.join(kits, "medical", "kit.zip"); bn, bd = zipmap(z)
rc, out = run(t, mir, tools, pc)
an, ad = zipmap(z); s = ad["MD5SUMS.txt"].decode()
ck("A7: changed marg_watch.py repacked AND guard.py added in one repack; MD5SUMS CRLF kept; both rows right",
   "REPACKED" in out and "marg_watch.py" in out and "guard.py NEW" in out and ad["payload/marg_watch.py"] == b"watch v2\n" and ad["payload/guard.py"] == GUARD
   and "\r\n" in s and all(md5(ad[l[34:]]) == l[:32] for l in s.splitlines() if l), s822=True)
info = open(os.path.join(kits, "medical", "KIT_INFO.txt")).read()
ck("A7: KIT_INFO's version names the changed file and 'added guard.py'", "marg_watch.py; added guard.py" in info, s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A8: --dry with a new file -> BEHIND (dry run) names it; nothing written --------------------------------------------
t = tempfile.mkdtemp(prefix="s822h_")
kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc, "--dry")
ck("A8: --dry says BEHIND (dry run) with 'guard.py NEW', writes nothing (no report, the rehearsal report stays)",
   "BEHIND (dry run)" in out and "guard.py NEW" in out and open(z, "rb").read() == b0
   and not os.path.exists(os.path.join(tools, "PC_KITS_CURRENT_LATEST.txt")) and os.path.exists(os.path.join(tools, "PC_KITS_REHEARSAL_LATEST.txt")), s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A9: a MD5SUMS without a final newline -> the new row still lands, no final newline added -----------------------------
t = tempfile.mkdtemp(prefix="s822i_")
kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,), trailing_nl=False)
z = os.path.join(kits, "medical", "kit.zip")
rc, out = run(t, mir, tools, pc)
an, ad = zipmap(z); s = ad["MD5SUMS.txt"].decode()
ck("A9: MD5SUMS with no final newline keeps that shape; the row is the last line and proves the member",
   "REPACKED" in out and not s.endswith("\n") and s.splitlines()[-1] == "%s  payload/guard.py" % md5(GUARD) and all(md5(ad[l[34:]]) == l[:32] for l in s.splitlines() if l), s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A10: a new file whose name differs only in case from a member -> not added twice ----------------------------------
t = tempfile.mkdtemp(prefix="s822j_")
kits, mir, tools, pc = build(t, pc_files=("MARG_WATCH.PY",), mirror_extra={"MARG_WATCH.PY": b"watch v1\n"}, pin_rows=("VPS\t%s\tmedical PC D:\\SendToClinic\\MARG_WATCH.PY\tx" % md5(b"watch v1\n"),))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc)
ck("A10: a name that is a member's in another case is not a new file (Windows names) -> CURRENT, untouched", "medical    CURRENT" in out and open(z, "rb").read() == b0)
shutil.rmtree(t, ignore_errors=True)

# ---- A11: installer-shaped names on the PC, even pinned, are reported and never packed --------------------------------
t = tempfile.mkdtemp(prefix="s822m_")
inst = {"install_s9xx.py": b"i\n", "SETUP_CHECK.bat": b"s\n", "_kit_marg_watch.py": b"k\n"}
kits, mir, tools, pc = build(t, pc_files=tuple(inst), mirror_extra=inst, pin_rows=tuple("VPS\t%s\tmedical PC D:\\SendToClinic\\%s\tx" % (md5(b), n) for n, b in inst.items()))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc)
ck("A11: an installer or checker by its name (install_*, setup_check*, _kit_*), on the PC and pinned -> reported 'never packed', the kit untouched",
   out.count("an installer or checker by its name") == 3 and open(z, "rb").read() == b0 and "medical    CURRENT" in out, s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A12: Drive's manifest names another md5 for the new file -> not packed (--manifest is the walk's hook) --------------
t = tempfile.mkdtemp(prefix="s822n_")
kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,))
mf = os.path.join(t, "KIT_MANIFEST.txt"); open(mf, "w").write("guard.py | 1 | %s\nmarg_watch.py | 1 | %s\n" % (md5(b"print('elsewhere')\n"), md5(b"watch v1\n")))
z = os.path.join(kits, "medical", "kit.zip"); b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc, "--manifest", mf)
ck("A12: the Drive manifest disagreeing with the mirror's new file -> 'KIT_MANIFEST names', not packed; the header says the manifest was read",
   "NEW guard.py: Drive's KIT_MANIFEST names" in out and "drive  : ToMedical KIT_MANIFEST read" in out and open(z, "rb").read() == b0, s822=True)
open(mf, "w").write("guard.py | 1 | %s\n" % md5(GUARD))
rc, out = run(t, mir, tools, pc, "--manifest", mf)
an, ad = zipmap(z)
ck("A12b: the manifest agreeing -> ADDED", "REPACKED" in out and ad.get("payload/guard.py") == GUARD, s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- A13: a kit with no MD5SUMS.txt cannot prove a new member -> reported, not packed ----------------------------------
t = tempfile.mkdtemp(prefix="s822o_")
kits, mir, tools, pc = build(t, pc_files=("guard.py",), mirror_extra={"guard.py": GUARD}, pin_rows=(PIN_GUARD,))
z = os.path.join(kits, "medical", "kit.zip")
with zipfile.ZipFile(z) as a:
    mem = {n: a.read(n) for n in a.namelist() if n != "MD5SUMS.txt"}
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zo:
    for n, b in mem.items():
        zo.writestr(zipfile.ZipInfo(n, (2026, 10, 3, 12, 0, 0)), b)
inf = os.path.join(kits, "medical", "KIT_INFO.txt"); txt = open(inf).read()
open(inf, "w").write(re.sub(r"kit_md5=.*", "kit_md5=" + md5(open(z, "rb").read()), txt))
b0 = open(z, "rb").read()
rc, out = run(t, mir, tools, pc)
ck("A13: a kit without MD5SUMS.txt -> 'cannot be proved', nothing packed, the kit untouched", "a new member cannot be proved" in out and open(z, "rb").read() == b0, s822=True)
shutil.rmtree(t, ignore_errors=True)

# ---- the S723/S794 behaviour unchanged by S822 (spot checks) -----------------------------------------------------------
t = tempfile.mkdtemp(prefix="s822k_")
kits, mir, tools, pc = build(t, pc_files=("marg_watch.py",), live_watch=b"watch v2\n")
z = os.path.join(kits, "medical", "kit.zip")
rc, out = run(t, mir, tools, pc)
an, ad = zipmap(z)
ck("S723 kept: a changed member alone is repacked as before; the line says REPACKED", "REPACKED" in out and ad["payload/marg_watch.py"] == b"watch v2\n" and "NEW" not in out)
shutil.rmtree(t, ignore_errors=True)
t = tempfile.mkdtemp(prefix="s822l_")
kits, mir, tools, pc = build(t, pc_files=())
os.utime(os.path.join(mir, "push_state.json"), (time.time() - 30 * 3600, time.time() - 30 * 3600))
rc, out = run(t, mir, tools, pc)
ck("S723 kept: a mirror 30 hours old -> REFUSED before anything is looked at", "REFUSED" in out and "hours old" in out)
shutil.rmtree(t, ignore_errors=True)

n_all = len(oks) + len(fails)
if control:
    red = [n for n, c in S822_CHECKS if not c]
    if len(red) >= 14:
        print("CONTROL S822 RED as it must be: %d of %d S822 checks fail on the old tool (%d of %d checks pass overall)" % (len(red), len(S822_CHECKS), len(oks), n_all))
        sys.exit(0)
    print("CONTROL S822 NOT RED: only %d of %d S822 checks fail on the old tool -- the walk cannot tell old from new" % (len(red), len(S822_CHECKS)))
    sys.exit(1)
print(("WALK S822 GREEN: %d/%d" % (len(oks), n_all)) if not fails else ("WALK S822 RED: %d of %d failed" % (len(fails), n_all)))
sys.exit(1 if fails else 0)
