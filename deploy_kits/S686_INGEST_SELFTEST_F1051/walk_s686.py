#!/usr/bin/env python3
"""walk_s686.py -- kit S686_INGEST_SELFTEST_F1051 (31-Oct-2026, the parent, S372).

    --new  <dir>  --lib <root> --db <copy> --scratch <dir> [--old-root <root>]
          every check on the BUILT file: the behaviour checks (B1-B7), the
          builder and the untouched-above-the-selftest proof (when --old-root
          is given), and the mutants. Last line: "N of N green".
    --old  <root> --lib <root> --db <copy> --scratch <dir>
          the CONTROL: the behaviour checks only, on the LIVE file. Last line:
          "X S686 check(s) red . Y green".

<dir>/<root> hold finance/finance_ingest.py. --lib supplies finance_patient_match.py
(the ladder's helper) so the copy runs as it does on the box. --db is a COPY of
finance.db; it is hashed before and after and must not change. Every selftest
run gets its own empty temp folder, so a throwaway copy left behind is SEEN.
Writes only under --scratch. Never touches a live file.
"""
import argparse
import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys

F = "finance/finance_ingest.py"
FROM = "ce01a9e1f8acd82370477a7468a6412b"
START = "# ----------------------------------------------------------------- selftest\n"
NEW_ONLY = {"_one", "_selftest_db", "selftest"}
HERE = os.path.dirname(os.path.abspath(__file__))

results = []


def check(name, cond, note=""):
    results.append((name, bool(cond), note))
    print("  %s  %s%s" % ("ok " if cond else "RED", name, ("  -- " + note) if note and not cond else ""))


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def stage(src_file, lib, dst_dir):
    """A runnable copy: the module + the ladder's helper, in its own folder."""
    shutil.rmtree(dst_dir, ignore_errors=True)
    os.makedirs(dst_dir)
    shutil.copyfile(src_file, os.path.join(dst_dir, "finance_ingest.py"))
    h = os.path.join(lib, "finance", "finance_patient_match.py")
    if os.path.isfile(h):
        shutil.copyfile(h, os.path.join(dst_dir, "finance_patient_match.py"))
    return os.path.join(dst_dir, "finance_ingest.py")


def run_selftest(mod, db, tmpdir):
    """Run `python -B finance_ingest.py <db>` with its own TMPDIR. Returns
    (exit code, output, files left in tmpdir)."""
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)
    env = dict(os.environ, TMPDIR=tmpdir, TEMP=tmpdir, TMP=tmpdir, PYTHONDONTWRITEBYTECODE="1")
    args = [sys.executable, "-B", os.path.basename(mod)] + ([db] if db else ["/nonexistent/finance.db"])
    p = subprocess.run(args, cwd=os.path.dirname(mod), env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=600)
    out = p.stdout.decode("utf-8", "replace")
    left = sorted(os.listdir(tmpdir))
    return p.returncode, out, left


def score(out):
    m = re.search(r"^INGEST (\d+)/(\d+) passed", out, re.M)
    return (int(m.group(1)), int(m.group(2))) if m else None


def behaviour(mod, db, scr, tag):
    """B1-B7 -- the same checks for the live file (control) and the built one."""
    db_before = md5f(db)
    rc, out, left = run_selftest(mod, db, os.path.join(scr, tag + "_t1"))
    sc = score(out)
    check("B1 [%s] the selftest on the database copy exits 0" % tag, rc == 0, "exit %s" % rc)
    check("B2 [%s] it prints a full score (n/n passed)" % tag, sc is not None and sc[0] == sc[1],
          "score %s; %s" % (sc, " | ".join(l for l in out.splitlines() if "FAIL" in l)[:300]))
    check("B3 [%s] no traceback" % tag, "Traceback" not in out, out.strip().splitlines()[-1][:160] if out.strip() else "")
    check("B4 [%s] no throwaway copy of the database left behind" % tag, left == [], "left: %s" % left)
    check("B5 [%s] the database copy it was given is unchanged" % tag, md5f(db) == db_before)

    # a database the checks cannot use (an empty file): reported, not a crash, cleaned up
    broken = os.path.join(scr, tag + "_broken.db")
    open(broken, "wb").close()
    rc2, out2, left2 = run_selftest(mod, broken, os.path.join(scr, tag + "_t2"))
    check("B6 [%s] an unusable database is ONE failed check, not a crash, and is cleaned up" % tag,
          rc2 == 1 and "Traceback" not in out2 and score(out2) is not None and left2 == []
          and ("the database checks stopped" in out2 or "FAIL" in out2),
          "exit %s, left %s, last: %s" % (rc2, left2, (out2.strip().splitlines() or [""])[-1][:120]))

    # no database at all: the pure checks only, exit 0
    rc3, out3, left3 = run_selftest(mod, None, os.path.join(scr, tag + "_t3"))
    check("B7 [%s] with no database the pure checks pass (db tests skipped)" % tag,
          rc3 == 0 and "db tests skipped" in out3 and left3 == [], "exit %s" % rc3)
    for t in ("_t1", "_t2", "_t3"):                 # a copy left behind holds patients: gone now
        shutil.rmtree(os.path.join(scr, tag + t), ignore_errors=True)
    return out


def top_defs(src):
    """{name: ast.dump} for every top-level statement, keyed by its name."""
    tree = ast.parse(src)
    out = {}
    for i, node in enumerate(tree.body):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            k = node.name
        elif isinstance(node, ast.Assign) and node.targets and isinstance(node.targets[0], ast.Name):
            k = "=" + node.targets[0].id
        else:
            k = "#" + ast.dump(node)      # unnamed statements keyed by their own content, not position
        out.setdefault(k, []).append(ast.dump(node))
    return out


def mutant(src, old, new):
    if src.count(old) != 1:
        return None
    return src.replace(old, new)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new")
    g.add_argument("--old")
    ap.add_argument("--old-root")
    ap.add_argument("--lib", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    scr = os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)

    if a.old:
        print("CONTROL -- the behaviour checks on the LIVE file")
        mod = stage(os.path.join(a.old, F), a.lib, os.path.join(scr, "old_mod"))
        behaviour(mod, a.db, scr, "live")
        red = sum(1 for r in results if not r[1])
        print("%d S686 check(s) red . %d green" % (red, len(results) - red))
        return 0

    built = os.path.join(a.new, F)
    nsrc = open(built, encoding="utf-8").read()
    print("THE BUILT FILE -- behaviour")
    mod = stage(built, a.lib, os.path.join(scr, "new_mod"))
    out = behaviour(mod, a.db, scr, "new")
    sc = score(out) or (0, 0)
    check("B8 the score covers the new checks (at least 56)", sc[1] >= 56, "score %s" % (sc,))
    # the new checks exist in the file (a score can be full only if they ran)
    for need in ("setting on: it lands on WALK-IN as a pharmacy_return of 77.00",
                 "setting off: review keeps the return signed",
                 "the made-up clinic IDs are unused in the copy"):
        check("B9 the selftest carries: %s" % need, nsrc.count('"%s"' % need) == 1)

    if a.old_root:
        print("THE BUILDER AND WHAT IT DID NOT TOUCH")
        osrc_p = os.path.join(a.old_root, F)
        check("M1 the old file is FROM ce01a9e1", md5f(osrc_p) == FROM)
        osrc = open(osrc_p, encoding="utf-8").read()
        check("M2 every byte above the selftest rule is unchanged",
              osrc[:osrc.index(START)] == nsrc[:nsrc.index(START)])
        check("M3 the __main__ tail is unchanged",
              osrc[osrc.index('\n\nif __name__ == "__main__":\n'):] == nsrc[nsrc.index('\n\nif __name__ == "__main__":\n'):])
        od, nd = top_defs(osrc), top_defs(nsrc)
        same = [k for k in od if k not in NEW_ONLY and od[k] == nd.get(k)]
        diff = [k for k in od if k not in NEW_ONLY and od[k] != nd.get(k)]
        extra = [k for k in nd if k not in od and k not in NEW_ONLY]
        check("M4 every function and constant except the selftest is identical (AST)",
              not diff and not extra, "differ %s extra %s" % (diff, extra))
        check("M5 ingest_day, resolve_patient and the ladder are among them",
              all(k in same for k in ("ingest_day", "resolve_patient", "ladder_lookup", "=WALK_IN")))
        # the builder refuses a file that is not FROM
        fake = os.path.join(scr, "fake_root")
        shutil.rmtree(fake, ignore_errors=True)
        os.makedirs(os.path.join(fake, "finance"))
        with open(os.path.join(fake, F), "w", encoding="utf-8") as fh:
            fh.write(osrc + "\n# drift\n")
        mk = os.path.join(HERE, "make_s686.py")
        outd = os.path.join(scr, "fake_out")
        shutil.rmtree(outd, ignore_errors=True)
        p = subprocess.run([sys.executable, "-B", mk, fake, outd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check("M6 the builder refuses a live file that is not FROM, and writes nothing",
              p.returncode == 2 and not os.path.exists(os.path.join(outd, F)))
        outd2 = os.path.join(scr, "real_out")
        shutil.rmtree(outd2, ignore_errors=True)
        p2 = subprocess.run([sys.executable, "-B", mk, a.old_root, outd2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check("M7 the builder run again on the old file gives the same bytes",
              p2.returncode == 0 and md5f(os.path.join(outd2, F)) == md5f(built))

    print("MUTANTS -- each must turn the built selftest red")
    muts = [
        ("X1 anonymous lines always parked (the setting ignored)",
         "if low_conf or (anonymous and not (anon_to_walkin and structured)):",
         "if low_conf or anonymous:"),
        ("X2 anonymous lines never parked (the setting ignored)",
         "if low_conf or (anonymous and not (anon_to_walkin and structured)):",
         "if low_conf:"),
        ("X3 a parked return stored unsigned",
         "signed(ln[\"amount_p\"], kind), ln[\"confidence\"],",
         "ln[\"amount_p\"], ln[\"confidence\"],"),
        ("X4 the walk-in patient renamed",
         'WALK_IN = "WALK-IN"', 'WALK_IN = "WALKIN"'),
        ("X5 a return served as a sale",
         'return base + "_return" if kind == KIND_RETURN else base',
         'return base'),
    ]
    for name, old, new in muts:
        m = mutant(nsrc, old, new)
        if m is None:
            check(name + " (anchor found once)", False, "anchor not found once")
            continue
        p = os.path.join(scr, "mut", re.sub(r"\W+", "_", name)[:20])
        mf = os.path.join(p, "finance_ingest.py")
        stage(built, a.lib, p)
        with open(mf, "w", encoding="utf-8") as fh:
            fh.write(m)
        rc, o, left = run_selftest(mf, a.db, os.path.join(p, "t"))
        s = score(o)
        check(name + " -- caught", rc != 0 and s is not None and s[0] < s[1] and left == [],
              "exit %s score %s left %s" % (rc, s, left))
        shutil.rmtree(os.path.join(p, "t"), ignore_errors=True)
    # the clean-up removed: the walk itself must see the copy left behind
    m = mutant(nsrc, "        for p in (tmp_db, tmp_db + \"-journal\", tmp_db + \"-wal\", tmp_db + \"-shm\"):\n",
               "        for p in ():\n")
    if m is None:
        check("X6 the clean-up removed (anchor found once)", False)
    else:
        p = os.path.join(scr, "mut", "X6")
        mf = os.path.join(p, "finance_ingest.py")
        stage(built, a.lib, p)
        with open(mf, "w", encoding="utf-8") as fh:
            fh.write(m)
        rc, o, left = run_selftest(mf, a.db, os.path.join(p, "t"))
        check("X6 the clean-up removed -- the walk sees the copy left behind", len(left) == 1,
              "left %s" % left)
        shutil.rmtree(os.path.join(p, "t"), ignore_errors=True)   # that copy holds patients: gone now

    red = sum(1 for r in results if not r[1])
    if red:
        print("%d check(s) RED of %d" % (red, len(results)))
        return 1
    print("%d of %d green" % (len(results), len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
