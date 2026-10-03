#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s461.py -- S461_FINANCE_TIDY: the four edits, walked on the app's own files in a scratch folder.

  usage: walk_s461.py --apply <apply_s461.py> --finance <folder holding finance_app.py and its sibling files>

It copies the app's CODE (*.py, *.sql, *.html, finance_ui/) from --finance into a scratch folder twice -- 'old' as it
is, 'new' with the kit's edits applied -- makes an EMPTY database from the app's own schema files, and drives both
through Flask's test client, each run in a process of its own. Nothing in --finance is written, no database there is
opened, no live scan folder is touched: every path the app is given points into the scratch folder, which is removed.
Each fault is first SHOWN on the old file, then shown gone on the new one. Last line: WALK_S461 GREEN|RED.
"""
import argparse
import difflib
import glob
import hashlib
import html as _html
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "40aef4dfe976a596c81be46da1fbb429"
TO = "26a532a6ec212ac66e6cfb41b37844eb"
MARK = "@@S461JSON@@ "
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:300]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


# ============================================================================ the children (one process each)
HOSTILE = [
    dict(key="push", label="Marg <b>report</b>", state="bad",
         detail="<script>alert(1)</script> & co", hint='tap <a href="/finance/approvals">here</a> </a><i>x'),
    dict(key="backup", label="Backup", state="warn", detail="cmdkey /add:<the medical address> /user:X",
         hint='Open <a href="/finance/approvals">the Hub</a> or <a href="https://example.invalid/x">outside</a>'),
    dict(key="reception", label="Reception PC", state="ok", detail="it's fine \"quoted\"", hint=""),
]


def child(mode):
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    out = {"mode": mode}
    c = fa.app.test_client()

    def get(p):
        r = c.get(p)
        return [r.status_code, r.get_data(as_text=True)]

    if mode == "routes":
        for k, p in (("abc", "/finance/api/days?days=abc"), ("huge", "/finance/api/days?days=" + "9" * 24),
                     ("d400", "/finance/api/days?days=400"), ("plain", "/finance/api/days"),
                     ("neg", "/finance/api/days?days=-5"), ("ym", "/finance/api/days?ym=2026-09"),
                     ("c_abc", "/finance/clinic/api/days?days=abc"), ("c_plain", "/finance/clinic/api/days"),
                     ("o_abc", "/finance/api/orthotics?days=abc"), ("o_neg", "/finance/api/orthotics?days=-5"),
                     ("o_plain", "/finance/api/orthotics"), ("o_big", "/finance/api/orthotics?days=5000")):
            out[k] = get(p)
        out["healthz"] = get("/finance/healthz")[0]
    elif mode == "health":
        real = fa._health_state(fa.db.__wrapped__()) if hasattr(fa.db, "__wrapped__") else None
        with fa.app.test_request_context("/finance/health"):
            real = fa._health_state(fa.db())
        out["real_checks"] = [[x["key"], x["state"], x["label"], x["detail"], x["hint"]] for x in real["checks"]]
        out["real_page"] = get("/finance/health")
        keep = fa._health_state
        fa._health_state = lambda con: {"ok": True, "worst": "bad", "checks": [dict(x) for x in HOSTILE],
                                        "culprits": ["Marg <b>report</b>", "Backup"], "as_at": "2026-10-03 12:00"}
        out["hostile_page"] = get("/finance/health")
        out["hostile_api"] = get("/finance/api/health")
        with fa.app.test_request_context("/"):
            out["headline"] = fa._health_headline(None)
        fa._health_state = keep
    elif mode == "mounts":
        out["failed"] = [[n, w] for n, w in fa._MOUNT_FAILED]
        with fa.app.test_request_context("/finance/health"):
            st = fa._health_state(fa.db())
        out["row"] = [x for x in st["checks"] if x["key"] == "mounts"]
        out["page"] = get("/finance/health")
        out["healthz"] = get("/finance/healthz")[0]
    elif mode == "scan":
        live = fa.SCAN_DIR
        try:
            fa.selftest()
            out["selftest"] = "completed"
        except BaseException as ex:                                  # noqa: BLE001
            out["selftest"] = "aborted: %s" % type(ex).__name__
        out["scan_dir_live"], out["scan_dir_now"], out["db_now"] = live, fa.SCAN_DIR, fa.DB_PATH
        import io
        c2 = fa.app.test_client()
        d1 = fa.today().isoformat()
        r = c2.post("/finance/api/day", json={"business_date": d1, "total": "1000", "upi": "300", "action": "draft"})
        out["draft"] = r.status_code
        doc = fa.REQUIRED_DOCS[0]
        rr = c2.post("/finance/api/day/%s/scan/%s" % (d1, doc),
                     data={"file": (io.BytesIO(b"%PDF-1.4 fake scan"), doc + ".pdf")},
                     content_type="multipart/form-data")
        out["scan"] = rr.status_code
        con = sqlite3.connect(fa.DB_PATH)
        row = con.execute("SELECT path FROM attachment ORDER BY id DESC LIMIT 1").fetchone()
        con.close()
        out["row_path"] = row[0] if row else ""
        out["row_file_exists"] = bool(row and os.path.isfile(row[0]))
        if hasattr(fa, "_s461_selftest_cleanup"):
            outside = os.environ["S461_OUTSIDE"]
            fa._s461_selftest_cleanup([outside])
            out["outside_kept"] = os.path.isfile(outside)
    print(MARK + json.dumps(out))


# ============================================================================ the parent
def run_child(appdir, mode, env, script=None, args=None):
    cmd = [sys.executable, "-B"] + ([script] + (args or []) if script else [os.path.abspath(__file__), "--child", mode])
    p = subprocess.run(cmd, cwd=appdir, env=env, capture_output=True, text=True, timeout=240)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def make_app(src, dst):
    os.makedirs(dst)
    n = 0
    for pat in ("*.py", "*.sql", "*.html"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024:
                shutil.copy2(f, dst)
                n += 1
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))
    return n


def make_db(appdir):
    con = sqlite3.connect(os.path.join(appdir, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(appdir, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    # the walk's stand-in for the C2 side table (its migration is not a file beside the app); empty, read only
    con.execute("CREATE TABLE IF NOT EXISTS clinic_line_side (id INTEGER PRIMARY KEY, day_entry_id INTEGER, "
                "tender TEXT, amount_p INTEGER, note TEXT)")
    con.commit()
    con.close()


def env_for(root, tag, appdir):
    e = dict(os.environ)
    tmp = os.path.join(root, "tmp_" + tag)
    os.makedirs(tmp, exist_ok=True)
    e.update({
        "FINANCE_DB": os.path.join(appdir, "finance.db"),
        "FINANCE_SCAN_DIR": os.path.join(root, "livescans_" + tag),
        "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp,
        "FINANCE_ALLOW_HEADER_AUTH": "1", "FINANCE_DEV_USER": "walk", "FINANCE_DEV_ROLE": "checker",
        "FINANCE_RENEWALS_STATE": os.path.join(root, "renewals_" + tag + ".json"),
        "FINANCE_LEDGER_JSONL": os.path.join(root, "ledger_" + tag + ".jsonl"),
        "LEDGER_DIR": os.path.join(root, "ledger_" + tag),
        "FINANCE_BACKUP_DIR": os.path.join(root, "backups"),       # one path for old and new: the row names it
        "FINANCE_AUTOAPPLY_OFF": os.path.join(root, "AUTOAPPLY_OFF_absent"),
        "S461_OUTSIDE": os.path.join(root, "outside_keep_me.txt"),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return e, tmp


def leftovers(tmp):
    return sorted(x for x in os.listdir(tmp)
                  if x.startswith(("finance_smoke_", "smoke_ledger_", "smoke_scans_", "smoke_renewals_")))


def files_under(d):
    return [os.path.join(r, f) for r, _d, fs in os.walk(d) for f in fs] if os.path.isdir(d) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s461_walk_")
    try:
        walk(a, root)
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S461 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    n = make_app(fin, old)
    check("0.1 the app's code is copied to a scratch folder (%d files)" % n, n > 30)
    check("0.2 the unpatched finance_app.py is the file this kit was built from (40aef4df)",
          md5(os.path.join(old, "finance_app.py")) == FROM, md5(os.path.join(old, "finance_app.py")))
    shutil.copytree(old, new)
    p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")],
                       capture_output=True, text=True)
    got = md5(os.path.join(new, "finance_app.py"))
    check("0.3 the edits apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")],
                        capture_output=True, text=True)
    check("0.4 applied twice: refused, the file left byte for byte",
          p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    spec = importlib.util.spec_from_file_location("apply_s461", a.apply)
    apl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apl)
    src_old = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read()
    src_new = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read()
    for nm, broken in (("an anchor that moved", src_old.replace('    DB_PATH = live_db\n    try:', '    DB_PATH = live_db\n    if 1:', 1)),
                       ("thirteen print-only mounts, not fourteen",
                        src_old.replace('    print("packs NOT mounted: %s" % _ex_pk, file=sys.stderr)\n', '    pass\n', 1)),
                       ("an anchor found twice", src_old + '\n    _rn_dir = tempfile.mkdtemp(prefix="smoke_renewals_")\n')):
        try:
            apl.apply(broken)
            check("0.5 the patcher refuses " + nm, False)
        except SystemExit as ex:
            check("0.5 the patcher refuses " + nm, "nothing written" in str(ex), ex)
    dl = list(difflib.unified_diff(src_old.splitlines(), src_new.splitlines(), lineterm="", n=0))
    gone = [x[1:] for x in dl if x.startswith("-") and not x.startswith("---")]
    added = [x[1:] for x in dl if x.startswith("+") and not x.startswith("+++")]
    check("0.6 exactly 8 old lines are replaced, nothing else is removed", len(gone) == 8, len(gone))
    check("0.7 every removed line is one of the eight named edits",
          all(any(k in g for k in ('request.args.get("days"', "global DB_PATH", "The reason is in the journal",
                                   '_delink(c["hint"])', 'c["label"], c["detail"]', 'h.get("culprits") or [])) + '))
              for g in gone), gone)
    check("0.8 %d lines added; no route, no SQL, no require() among them" % len(added),
          not any(("@app.route" in x or "require(" in x or "execute(" in x or "PUBLIC_PATHS" in x) for x in added))
    try:
        compile(src_new, "finance_app.py", "exec")
        check("0.9 the edited file compiles", True)
    except SyntaxError as ex:
        check("0.9 the edited file compiles", False, ex)
    for d in (old, new):
        make_db(d)
    with open(os.path.join(root, "outside_keep_me.txt"), "w") as fh:
        fh.write("not in temp")

    # ------------------------------------------------------------------ 1 · ?days=
    R = {}
    for tag, d in (("old", old), ("new", new)):
        e, _t = env_for(root, "r" + tag, d)
        p, R[tag] = run_child(d, "routes", e)
        check("1.0 the %s app starts and answers in the scratch folder" % tag, bool(R[tag]) and R[tag]["healthz"] == 200,
              p.stderr[-300:])
    if R.get("old") and R.get("new"):
        o, nw = R["old"], R["new"]
        check("1.1 SHOWN on the old file: ?days=abc is a 500 on the day list", o["abc"][0] == 500, o["abc"][0])
        check("1.2 SHOWN on the old file: a huge ?days= is a 500", o["huge"][0] == 500, o["huge"][0])
        check("1.3 new: ?days=abc answers 200 with the default window", nw["abc"][0] == 200 and nw["abc"][1] == nw["plain"][1])
        check("1.4 new: a huge ?days= answers 200", nw["huge"][0] == 200)
        check("1.5 new: a negative ?days= answers 200", nw["neg"][0] == 200)
        check("1.6 unchanged: ?days=400, no ?days= and ?ym= answer the same bytes old and new",
              all(o[k] == nw[k] and nw[k][0] == 200 for k in ("d400", "plain", "ym")))
        check("1.7 SHOWN on the old file: the clinic day list has the same fault", o["c_abc"][0] == 500)
        check("1.8 new: the clinic day list answers 200, and unchanged without ?days=",
              nw["c_abc"][0] == 200 and o["c_plain"] == nw["c_plain"] and nw["c_plain"][0] == 200, nw["c_abc"][0])
        check("1.9 SHOWN on the old file: the orthotics page's ?days=abc is a 500", o["o_abc"][0] == 500)
        check("1.10 new: orthotics answers 200 for abc and for a negative number",
              nw["o_abc"][0] == 200 and nw["o_neg"][0] == 200)
        check("1.11 unchanged: orthotics without ?days= and beyond its cap answer the same old and new",
              o["o_plain"] == nw["o_plain"] and o["o_big"] == nw["o_big"] and nw["o_big"][0] == 200)

    # ------------------------------------------------------------------ 2 · /finance/health
    H = {}
    for tag, d in (("old", old), ("new", new)):
        e, _t = env_for(root, "h" + tag, d)
        p, H[tag] = run_child(d, "health", e)
        check("2.0 the %s health page renders" % tag, bool(H[tag]) and H[tag]["real_page"][0] == 200, p.stderr[-300:])
    if H.get("old") and H.get("new"):
        o, nw = H["old"], H["new"]
        op, npg = o["hostile_page"][1], nw["hostile_page"][1]
        check("2.1 SHOWN on the old file: a row's words reach the page as markup", "<script>alert(1)</script>" in op)
        check("2.2 SHOWN on the old file: '<the medical address>' is swallowed as a tag",
              "<the medical address>" in op and "&lt;the medical address&gt;" not in op)
        check("2.3 new: no row text is markup -- the script tag is words", "<script>alert(1)</script>" not in npg
              and "&lt;script&gt;alert(1)&lt;/script&gt; &amp; co" in npg)
        check("2.4 new: '<the medical address>' is shown", "&lt;the medical address&gt;" in npg)
        check("2.5 new: the label is escaped", "Marg &lt;b&gt;report&lt;/b&gt;" in npg and "Marg <b>report</b>" not in npg)
        check("2.6 new: quotes and apostrophes are escaped", "it&#39;s fine &quot;quoted&quot;" in npg)
        check("2.7 new: a hint keeps a whole link to a page of this site",
              'Open <a href="/finance/approvals">the Hub</a>' in npg)
        check("2.8 new: a link to anywhere else stays words", 'href="https://example.invalid' not in npg
              and "example.invalid" in npg)
        row = npg.split('<a class="row" href="/finance/approvals#margCard">', 1)[-1].split('&#8250;</span></a>', 1)[0]
        check("2.9 new: a row that is itself a link carries no link and no stray tag inside it",
              "<a " not in row and "</a>" not in row and "<i>" not in row and "here" in row, row[:200])
        check("2.10 new: the names beside 'Right now' are escaped", "Marg &lt;b&gt;report&lt;/b&gt; &#183; Backup" in npg)
        check("2.11 unchanged: the JSON the page is built from", o["hostile_api"] == nw["hostile_api"])
        check("2.12 unchanged: the portal tile's line stays plain text (the portal sets it as text)",
              o["headline"] == nw["headline"] and "<script>" in (nw["headline"] or ""), nw["headline"])
        rows_o = [x[:4] for x in o["real_checks"]]
        rows_n = [x[:4] for x in nw["real_checks"]]
        check("2.13 unchanged: the real checks on an empty database -- same rows, states and words (%d rows)" % len(rows_n),
              rows_o == rows_n and len(rows_n) >= 8)
        rp = nw["real_page"][1]
        check("2.14 new: every real row's label and words are on the page",
              all(_html.escape(x[2], quote=True).replace("&#x27;", "&#39;") in rp
                  and _html.escape(x[3], quote=True).replace("&#x27;", "&#39;") in rp for x in nw["real_checks"]))
        check("2.15 unchanged: the page has the same number of rows old and new",
              o["real_page"][1].count('class="row"') == rp.count('class="row"') == len(rows_n),
              (o["real_page"][1].count('class="row"'), rp.count('class="row"'), len(rows_n)))

    # ------------------------------------------------------------------ 3 · the mounts row
    M = {}
    for tag, d in (("old", old), ("new", new)):
        e, _t = env_for(root, "m" + tag, d)
        p, M[tag + "_ok"] = run_child(d, "mounts", e)
        bd = os.path.join(root, "broken_" + tag)
        shutil.copytree(d, bd)
        with open(os.path.join(bd, "packs.py"), "w") as fh:
            fh.write("def init(*a, **k):\n    raise RuntimeError('boom <walk> init')\n")
        with open(os.path.join(bd, "freshness_page.py"), "w") as fh:
            fh.write("raise RuntimeError('boom at import')\n")
        e2, _t = env_for(root, "mb" + tag, bd)
        p, M[tag] = run_child(bd, "mounts", e2)
        check("3.0 the %s app still starts with two parts broken" % tag, bool(M[tag]) and M[tag]["healthz"] == 200,
              p.stderr[-300:])
    if all(M.get(k) for k in ("old", "new", "old_ok", "new_ok")):
        o, nw = M["old"], M["new"]
        orow, nrow = o["row"][0], nw["row"][0]
        check("3.1 SHOWN on the old file: a part whose init() failed is not on the row",
              "packs" not in orow["detail"] and "freshness_page" in orow["detail"], orow["detail"])
        base = [x[0] for x in M["new_ok"]["failed"]]              # parts that do not load in a scratch folder at all
        check("3.2 new: the row is red and names both parts, each once",
              nrow["state"] == "bad" and nrow["detail"].count("packs") == 1
              and nrow["detail"].count("freshness_page") == 1
              and ("%d of 27" % (2 + len(base))) in nrow["detail"], nrow["detail"])
        names = [x[0] for x in nw["failed"]]
        check("3.3 new: both failures are recorded with their reason", "packs" in names and "freshness_page" in names
              and any("boom <walk> init" in x[1] for x in nw["failed"]), nw["failed"])
        check("3.4 new: the row says why", "Why: " in nrow["hint"] and "packs: RuntimeError" in nrow["hint"]
              and "boom at import" in nrow["hint"] and "journal of clinic-finance" in nrow["hint"], nrow["hint"])
        check("3.5 new: the reason reaches the page as words", "boom &lt;walk&gt; init" in nw["page"][1]
              and "boom <walk> init" not in nw["page"][1])
        if base:
            print("  NOTE: in the scratch folder these parts do not load even unbroken: %s" % ", ".join(base))
            check("3.6 with nothing broken by the walk, the new row names exactly the parts that did not load here",
                  all(M["new_ok"]["row"][0]["detail"].count(x) == 1 for x in base), M["new_ok"]["row"])
        else:
            check("3.6 unchanged: with nothing broken the row is the same old and new",
                  M["old_ok"]["row"] == M["new_ok"]["row"] and M["old_ok"]["failed"] == [], M["new_ok"]["row"])

    # ------------------------------------------------------------------ 4 · --selftest
    S = {}
    for tag, d in (("old", old), ("new", new)):
        e, tmp = env_for(root, "s" + tag, d)
        e["FINANCE_ALLOW_HEADER_AUTH"] = ""
        p = subprocess.run([sys.executable, "-B", "finance_app.py", "--selftest"], cwd=d, env=e,
                           capture_output=True, text=True, timeout=240)
        S[tag] = (p.returncode, p.stderr[-400:], leftovers(tmp), files_under(e["FINANCE_SCAN_DIR"]))
    check("4.1 on an empty database --selftest aborts part-way, old and new alike (that is the case being walked)",
          S["old"][0] != 0 and S["new"][0] != 0 and "Error" in S["old"][1] and "Error" in S["new"][1],
          (S["old"][0], S["new"][0]))
    check("4.2 SHOWN on the old file: the abort leaves the database copy and a smoke folder in temp",
          any(x.startswith("finance_smoke_") for x in S["old"][2]) and any(x.startswith("smoke_ledger_") for x in S["old"][2]),
          S["old"][2])
    check("4.3 new: the same abort leaves NOTHING in temp", S["new"][2] == [], S["new"][2])
    C = {}
    for tag, d in (("old", old), ("new", new)):
        e, tmp = env_for(root, "c" + tag, d)
        p, C[tag] = run_child(d, "scan", e)
        C[tag + "_left"], C[tag + "_live"], C[tag + "_tmp"] = leftovers(tmp), files_under(e["FINANCE_SCAN_DIR"]), tmp
        check("4.4 the %s selftest's scan upload goes through the real route" % tag,
              bool(C[tag]) and C[tag]["draft"] == 200 and C[tag]["scan"] == 200 and C[tag]["row_file_exists"],
              p.stderr[-300:])
    if C.get("old") and C.get("new"):
        o, nw = C["old"], C["new"]
        check("4.5 SHOWN on the old file: the fake scan is written into the live scan folder and stays there",
              o["scan_dir_now"] == o["scan_dir_live"] and len(C["old_live"]) == 1, C["old_live"])
        check("4.6 new: during the selftest the scan folder is a throwaway one in temp",
              nw["scan_dir_now"] != nw["scan_dir_live"]
              and os.path.basename(nw["scan_dir_now"]).startswith("smoke_scans_")
              and os.path.dirname(nw["scan_dir_now"]) == C["new_tmp"], nw["scan_dir_now"])
        check("4.7 new: the fake scan and its row's path are inside that throwaway folder",
              nw["row_path"].startswith(nw["scan_dir_now"] + os.sep), nw["row_path"])
        check("4.8 new: the live scan folder is not written at all", C["new_live"] == [], C["new_live"])
        check("4.9 new: after the process ends, nothing of the run is left in temp", C["new_left"] == [], C["new_left"])
        check("4.10 new: the clean-up refuses a path outside temp", nw.get("outside_kept") is True
              and os.path.isfile(os.path.join(root, "outside_keep_me.txt")))
    check("4.11 nothing in the app's own folder was written by this walk",
          md5(os.path.join(fin, "finance_app.py")) in (FROM, TO))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        sys.exit(main())
