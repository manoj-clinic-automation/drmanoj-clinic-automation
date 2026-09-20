#!/root/wa/venv/bin/python3
# =============================================================================
#  selftest_s347.py  ·  S347_SPINE_BACKUP  ·  v1
#
#  Proves BOTH patches on COPIES of the two live files against a FAKE ROOT in
#  /tmp shaped like the real box: a spine folder with its seven .py, the two
#  rule files, the state file, the witness text, a real sqlite spine.db (plus a
#  .tmp and a .failed beside it, which must never be taken), readings/ with
#  md5-named json, and orders/ + expiry/ nightly outputs that must stay OUT of
#  both stores by design.
#
#  It never touches /root/state_backup, never reaches Drive, never encrypts
#  anything: the code bundle is built with ROOT=<fake> (so systemctl is skipped
#  by the file's own design) and the state backup's gather() is pointed at the
#  fake tree by rewriting its two source lists in memory, AFTER asserting the
#  exact literals the patch wrote.
#
#  NEGATIVE CONTROLS, each of which must turn a green check red:
#    code bundle  · the new entry removed        -> nothing of the spine is carried
#                 · the entry made RECURSIVE     -> readings/ leak into the code bundle
#    state backup · the two rows removed         -> no spine.db, no readings in data/
#                 · a corrupt spine.db           -> the gather REFUSES (FATAL 40), and
#                                                   with the fatal switch off it skips
#                                                   that one file and says so
# =============================================================================
import hashlib
import importlib.util
import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE_CB = "/root/state_backup/code_bundle.py"
LIVE_SB = "/root/state_backup/clinic_state_backup.py"
OK, BAD = [], []

SPINE_PY = ("marg_read.py", "spine_evidence.py", "spine_build.py", "spine_read.py",
            "spine_compare.py", "selftest_spine.py", "order_rehearsal.py", "near_expiry.py")
SPINE_JSON = ("spine_rules.json", "order_rules.json", "spine_state.json")
SPINE_TXT = ("spine_compare_latest.txt",)


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def load(path, root=None):
    if root is not None:
        os.environ["ROOT"] = root
    spec = importlib.util.spec_from_file_location("s347_%d" % len(sys.modules), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_sqlite(path, rows=3):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE sp_item (id INTEGER PRIMARY KEY, name TEXT)")
    c.executemany("INSERT INTO sp_item (name) VALUES (?)", [("item %d" % i,) for i in range(rows)])
    c.commit()
    c.close()


def fake_tree(base):
    fin = os.path.join(base, "root", "finance")
    sp = os.path.join(fin, "spine")
    for d in (sp, os.path.join(sp, "readings"), os.path.join(sp, "orders"), os.path.join(sp, "expiry"),
              os.path.join(base, "root", "state_backup"), os.path.join(base, "root", "portal")):
        os.makedirs(d, exist_ok=True)
    with open(os.path.join(fin, "finance_app.py"), "w") as fh:
        fh.write("# a stand-in for the real thing\nprint('hello')\n")
    with open(os.path.join(fin, "freshness_legs.json"), "w") as fh:
        fh.write('{"legs": []}\n')
    for n in SPINE_PY:
        with open(os.path.join(sp, n), "w") as fh:
            fh.write("# %s -- stand-in\nX = 1\n" % n)
    for n in SPINE_JSON:
        with open(os.path.join(sp, n), "w") as fh:
            fh.write('{"version": "1", "note": "stand-in %s"}\n' % n)
    for n in SPINE_TXT:
        with open(os.path.join(sp, n), "w") as fh:
            fh.write("compare written -- stand-in\n")
    make_sqlite(os.path.join(sp, "spine.db"))
    make_sqlite(os.path.join(sp, "spine.db.tmp"))
    with open(os.path.join(sp, "spine.db.failed"), "wb") as fh:
        fh.write(b"SQLite format 3\x00" + b"\x00" * 100)
    for i in range(3):
        h = hashlib.md5(("reading %d" % i).encode()).hexdigest()
        with open(os.path.join(sp, "readings", h + ".json"), "w") as fh:
            fh.write('{"family": "SALE_BILLWISE", "data": {"n": %d}}\n' % i)
    with open(os.path.join(sp, "orders", "order_rehearsal_2026-09-20.json"), "w") as fh:
        fh.write('{"lines": []}\n')
    with open(os.path.join(sp, "orders", "order_rehearsal_latest.txt"), "w") as fh:
        fh.write("47 lines\n")
    with open(os.path.join(sp, "expiry", "near_expiry_2026-09-20.json"), "w") as fh:
        fh.write('{"batches": []}\n')
    # the unit dir the code bundle's unit-state capture expects
    ud = os.path.join(base, "etc", "systemd", "system")
    os.makedirs(os.path.join(ud, "multi-user.target.wants"), exist_ok=True)
    with open(os.path.join(ud, "clinic-alpha.service"), "w") as fh:
        fh.write("[Unit]\nDescription=alpha\n")
    os.symlink(os.path.join(ud, "clinic-alpha.service"),
               os.path.join(ud, "multi-user.target.wants", "clinic-alpha.service"))
    return sp


def members(path):
    with tarfile.open(path, "r:gz") as tf:
        return {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}


def build_in(path, base):
    mod = load(path, base)
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        out, _summary = mod.build()
    return mod, members(out), out


def write_variant(tmp, name, text):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p


def before_and_after(P, text):
    """The (plain, patched) pair for a file. A live file that ALREADY carries
    the change is un-patched by reversing the exact replacements, so a re-run
    of the installer proves the same 49 things instead of going red on
    'nothing to apply'."""
    new, msgs = P.apply_to_text(text)
    if new is not None and new == text and P.MARK in text:
        plain = text
        for anchor, repl in P.EDITS:
            if plain.count(repl) != 1:
                return None, None, ["ALREADY, but the S347 text is not there exactly once -- cannot reverse it"]
            plain = plain.replace(repl, anchor, 1)
        again, _ = P.apply_to_text(plain)
        if again != text:
            return None, None, ["ALREADY, but reversing and re-applying does not give the live bytes back"]
        return plain, text, ["ALREADY -- the live file carries S347; proved on its reversal"]
    return text, new, msgs


# ---------------------------------------------------------------- code bundle
def test_code_bundle(src, tmp):
    print("-- the 01:35 code bundle (%s)" % src)
    import patch_code_bundle_s347 as P
    with open(src, "r", encoding="utf-8") as fh:
        live = fh.read()
    text, new, msgs = before_and_after(P, live)
    check("the patch applies to this file (or is already there and reverses cleanly)",
          new is not None and text is not None and new != text)
    if new is None:
        print("   " + "; ".join(msgs))
        return
    if text != live:
        print("   " + msgs[0])
    plain = write_variant(tmp, "cb_plain.py", text)
    patched = write_variant(tmp, "cb_patched.py", new)
    check("the patched file compiles",
          subprocess.run([sys.executable, "-B", "-m", "py_compile", patched],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    check("every entry that was in SOURCES before is still there, unchanged",
          text.split("SOURCES = [")[1].split("]\n")[0] in new)
    check("applying twice is a no-op (idempotent)", P.apply_to_text(new)[0] == new)

    base_a, base_b = os.path.join(tmp, "A"), os.path.join(tmp, "B")
    fake_tree(base_a)
    fake_tree(base_b)
    _ma, ma, _oa = build_in(plain, base_a)
    mod_b, mb, out_b = build_in(patched, base_b)
    pre = "root/finance/spine/"
    for n in SPINE_PY + SPINE_JSON + SPINE_TXT:
        check("NOT carried before, carried now: %s" % n, (pre + n) not in ma and (pre + n) in mb)
    check("spine.db is NOT in the code bundle (\"*.db*\" is a hard exclude)",
          not any(k.startswith(pre + "spine.db") for k in mb))
    check("readings/ are NOT in the code bundle (non-recursive, by design)",
          not any(k.startswith(pre + "readings/") for k in mb))
    check("orders/ and expiry/ are NOT in the code bundle",
          not any(k.startswith(pre + "orders/") or k.startswith(pre + "expiry/") for k in mb))
    check("no member the old build carried was dropped", not (set(ma) - set(mb)))
    check("the two files above the spine folder are still carried (finance_app.py, freshness_legs.json)",
          "root/finance/finance_app.py" in mb and "root/finance/freshness_legs.json" in mb)
    check("the tarball still verifies against its own manifest", not mod_b.verify_tarball(out_b))
    n_new = len(SPINE_PY) + len(SPINE_JSON) + len(SPINE_TXT)
    check("the bundle grew by exactly the %d spine files" % n_new, len(mb) - len(ma) == n_new)

    # negative control 1: the entry removed
    entry = '    ("root/finance/spine",           ("*.py", "*.json", "*.txt"),                   False, ()),\n'
    check("NEGATIVE CONTROL -- the new entry can be removed from the text", entry in new)
    p_rev = write_variant(tmp, "cb_rev.py", new.replace(entry, ""))
    base_c = os.path.join(tmp, "C")
    fake_tree(base_c)
    _mc, mc, _oc = build_in(p_rev, base_c)
    check("NEGATIVE CONTROL -- without the entry nothing of the spine is carried",
          not any(k.startswith(pre) for k in mc))
    # negative control 2: recursion on -> the data folders leak in
    p_rec = write_variant(tmp, "cb_rec.py", new.replace(entry, entry.replace("False, ()", "True,  ()")))
    base_d = os.path.join(tmp, "D")
    fake_tree(base_d)
    _md, md_, _od = build_in(p_rec, base_d)
    check("NEGATIVE CONTROL -- made recursive, readings/ WOULD leak into the code bundle "
          "(so the non-recursive flag is what keeps data out)",
          any(k.startswith(pre + "readings/") for k in md_))


# --------------------------------------------------------------- state backup
def point_at(mod, base):
    """Rewrite the two source lists onto the fake tree, keeping every literal."""
    mod.SRC_FILES = [os.path.join(base, p.lstrip("/")) for p in mod.SRC_FILES]
    mod.SRC_DIRS = [os.path.join(base, p.lstrip("/")) for p in mod.SRC_DIRS]


def gather_quiet(mod, base, dest, fatal=True):
    conf = {"SYSTEMD_DIR": os.path.join(base, "etc", "systemd", "system"), "UNIT_MATCH": "clinic-"}
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        try:
            g = mod.gather(conf, dest, integrity_fatal=fatal)
            return g, None, buf.getvalue()
        except SystemExit as ex:
            return None, ex.code, buf.getvalue()


def test_state_backup(src, tmp):
    print("-- the 01:50 encrypted state backup (%s)" % src)
    import patch_state_backup_s347 as P
    with open(src, "r", encoding="utf-8") as fh:
        live = fh.read()
    text, new, msgs = before_and_after(P, live)
    check("the patch applies to this file (or is already there and reverses cleanly)",
          new is not None and text is not None and new != text)
    if new is None:
        print("   " + "; ".join(msgs))
        return
    if text != live:
        print("   " + msgs[0])
    patched = write_variant(tmp, "sb_patched.py", new)
    plain = write_variant(tmp, "sb_plain.py", text)
    check("the patched file compiles",
          subprocess.run([sys.executable, "-B", "-m", "py_compile", patched],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    check("applying twice is a no-op (idempotent)", P.apply_to_text(new)[0] == new)

    m_plain = load(plain)
    m_new = load(patched)
    check("the exact literal /root/finance/spine/spine.db is in SRC_FILES",
          "/root/finance/spine/spine.db" in m_new.SRC_FILES)
    check("the exact literal /root/finance/spine/readings is in SRC_DIRS",
          "/root/finance/spine/readings" in m_new.SRC_DIRS)
    check("every source the file named before is still named (nothing dropped)",
          all(p in m_new.SRC_FILES for p in m_plain.SRC_FILES)
          and all(p in m_new.SRC_DIRS for p in m_plain.SRC_DIRS))
    check("exactly two rows were added", len(m_new.SRC_FILES) == len(m_plain.SRC_FILES) + 1
          and len(m_new.SRC_DIRS) == len(m_plain.SRC_DIRS) + 1)
    check("the whole spine folder is NOT a store (orders/ and expiry/ stay out by design)",
          "/root/finance/spine" not in m_new.SRC_DIRS)

    base = os.path.join(tmp, "S")
    sp = fake_tree(base)
    # the fake box also needs the stores the file already names, or they count as missing
    for p in m_plain.SRC_FILES:
        fp = os.path.join(base, p.lstrip("/"))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w") as fh:
            fh.write("stand-in\n")
    for d in m_plain.SRC_DIRS:
        os.makedirs(os.path.join(base, d.lstrip("/")), exist_ok=True)

    point_at(m_plain, base)
    point_at(m_new, base)
    dest_p, dest_n = os.path.join(tmp, "out_plain"), os.path.join(tmp, "out_new")
    gp, code_p, _ = gather_quiet(m_plain, base, dest_p)
    gn, code_n, log_n = gather_quiet(m_new, base, dest_n)
    check("the unpatched gather runs on the fake box", gp is not None)
    check("the patched gather runs on the fake box", gn is not None)
    if gn is None:
        print("   exit", code_n, "\n   ", log_n[-600:])
        return
    dp, dn = os.path.join(dest_p, "data"), os.path.join(dest_n, "data")
    check("NOT carried before, carried now: spine.db",
          not os.path.exists(os.path.join(dp, "spine.db")) and os.path.isfile(os.path.join(dn, "spine.db")))
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(dn, "spine.db"), uri=True)
    n_rows = c.execute("SELECT count(*) FROM sp_item").fetchone()[0]
    c.close()
    check("the carried spine.db is a real, readable copy (online-backup api; 3 rows)", n_rows == 3)
    check("its schema was dumped beside the shape", any(f.startswith("spine.db") and f.endswith(".schema.sql")
          for f in os.listdir(os.path.join(dest_n, "shape", "schema"))))
    check("spine.db was integrity-checked and said ok",
          any(s.endswith("spine.db") and a == "ok" for s, a in gn.databases))
    rd = os.path.join(dn, "readings")
    check("NOT carried before, carried now: readings/ (3 md5-named json)",
          not os.path.isdir(os.path.join(dp, "readings")) and os.path.isdir(rd)
          and len([f for f in os.listdir(rd) if f.endswith(".json")]) == 3)
    check("spine.db.tmp and spine.db.failed are NOT carried",
          not os.path.exists(os.path.join(dn, "spine.db.tmp")) and not os.path.exists(os.path.join(dn, "spine.db.failed")))
    check("orders/ and expiry/ are NOT carried",
          not os.path.exists(os.path.join(dn, "orders")) and not os.path.exists(os.path.join(dn, "expiry")))
    check("no entry the old gather carried was dropped",
          set(e[0] for e in gp.entries) <= set(e[0] for e in gn.entries))
    check("the gather grew by exactly 5 entries (spine.db, its schema dump, 3 readings)",
          len(gn.entries) - len(gp.entries) == 5)
    check("no source is reported missing on the fake box", not gn.sources_missing)

    # negative control 1: the two rows removed
    m_rev = load(write_variant(tmp, "sb_rev.py",
                               new.replace('    "/root/finance/spine/spine.db",\n', "")
                                  .replace('    "/root/finance/spine/readings",\n', "")))
    point_at(m_rev, base)
    gr, _cr, _ = gather_quiet(m_rev, base, os.path.join(tmp, "out_rev"))
    check("NEGATIVE CONTROL -- with the two rows removed, neither spine.db nor readings/ is carried",
          gr is not None and not os.path.exists(os.path.join(tmp, "out_rev", "data", "spine.db"))
          and not os.path.exists(os.path.join(tmp, "out_rev", "data", "readings")))
    # negative control 2: a corrupt spine.db refuses the whole gather (FATAL 40)
    with open(os.path.join(sp, "spine.db"), "r+b") as fh:
        size = fh.seek(0, 2)
        fh.seek(100)                      # keep the 100-byte header: still "a database"
        fh.write(b"\xff" * (size - 100))  # every page body torn
    m_bad = load(patched)
    point_at(m_bad, base)
    gb, code_b, log_b = gather_quiet(m_bad, base, os.path.join(tmp, "out_bad"), fatal=True)
    check("NEGATIVE CONTROL -- a corrupt spine.db makes the gather REFUSE (exit %d), nothing shipped"
          % m_bad.EXIT_INTEGRITY, gb is None and code_b == m_bad.EXIT_INTEGRITY)
    m_bad2 = load(patched)
    point_at(m_bad2, base)
    gb2, _c2, log_b2 = gather_quiet(m_bad2, base, os.path.join(tmp, "out_bad2"), fatal=False)
    check("NEGATIVE CONTROL -- with the fatal switch off it skips that one file and says INTEGRITY FAIL",
          gb2 is not None and "INTEGRITY FAIL" in log_b2
          and not os.path.exists(os.path.join(tmp, "out_bad2", "data", "spine.db"))
          and os.path.isdir(os.path.join(tmp, "out_bad2", "data", "readings")))


def main(argv):
    cb, sb = LIVE_CB, LIVE_SB
    for a in argv[1:]:
        if a.startswith("--code-bundle="):
            cb = a.split("=", 1)[1]
        if a.startswith("--state-backup="):
            sb = a.split("=", 1)[1]
    for p in (cb, sb):
        if not os.path.isfile(p):
            print("RED -- %s is not there" % p)
            return 3
    sys.path.insert(0, HERE)
    tmp = tempfile.mkdtemp(prefix="s347_")
    try:
        test_code_bundle(cb, tmp)
        test_state_backup(sb, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("SELFTEST OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
