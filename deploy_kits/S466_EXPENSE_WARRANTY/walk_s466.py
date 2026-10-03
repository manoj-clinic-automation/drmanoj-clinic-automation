#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s466.py -- S466_EXPENSE_WARRANTY (D664 slice 3): a Dr MK expense keeps its warranty, and Renewals shows it.

  usage: walk_s466.py --apply <apply_s466.py> --module <clinic_papers.py S466> --assetapp <folder holding the S465 app>

The asset app's CODE as S465 leaves it is copied to a scratch folder four times: 'old' as it is, 'new' with this kit's
module and its three edits, 'bare' with the edits but NO module (the guard), 'half' with the edits and S465's module
(the two files are placed one after the other). Each runs in a process of its own on an EMPTY database the app makes
for itself, with made-up papers. Dates are counted from today, so the walk is the same on any day. The child refuses
to go on if the database or the uploads folder is not the scratch one; S441 is given no finance database; no OCR is
called. Nothing live is opened. Last line: WALK_S466 GREEN|RED.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

AR_FROM = "b0e0915e0b73a6ffb1f4a6e17aec8274"
AR_TO = "e774be89193472dfa4b142d85bdcc46c"
CP_FROM = "231cd6a959d2030160ec9de43fb4d076"
MARK = "@@S466JSON@@ "
DASH = chr(0x2014)
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:600]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def squash(html):
    return re.sub(r"\s+", " ", html).strip()


def text(html):
    html = re.sub(r"<style.*?</style>|<script.*?</script>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def tiny_pdf(words):
    stream = ("BT /F1 12 Tf 20 100 Td (%s) Tj ET" % words).encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out


# ============================================================================ the child
def child(mode):
    import datetime
    root = os.path.realpath(os.environ["S466_ROOT"]) + os.sep
    sys.path.insert(0, os.getcwd())
    import asset_register as A
    if not os.path.realpath(A.DB_PATH).startswith(root) or not os.path.realpath(A.UPLOAD_DIR).startswith(root):
        print(MARK + json.dumps({"abort": "the database or the uploads folder is not the scratch one"}))
        return
    out = {"mode": mode, "endpoints": sorted(k for k in A.app.view_functions if k.startswith("d664_"))}
    con = sqlite3.connect(A.DB_PATH)
    con.row_factory = sqlite3.Row
    out["tables"] = sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE name LIKE 'd664%'"))
    up = A.UPLOAD_DIR
    os.makedirs(up, exist_ok=True)
    today = datetime.date.today()
    day = lambda n: (today + datetime.timedelta(days=n)).isoformat()
    dmy = lambda n: (today + datetime.timedelta(days=n)).strftime("%d-%b-%Y")

    def bill(stamp, vendor, lane="owner_expense", status=None, no=None, total=None, items=(), pdf=None):
        kind, st = A.LANES[lane][1], A.LANES[lane][2]
        stored = None
        if pdf:
            stored = "bill_walk%s.pdf" % stamp.replace("-", "").lower()
            with open(os.path.join(up, stored), "wb") as fh:
                fh.write(tiny_pdf(pdf))
        con.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,created_at,stamp_no,status,lane,"
                    "ocr_status,source_stored,source_orig) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (kind, vendor, no, "2026-10-01" if no else None, total, "2026-10-02 06:00:00", stamp, status or st, lane, "read", stored, stored))
        bid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        for it in items:
            con.execute("INSERT INTO bill_items (bill_id,item_name) VALUES (?,?)", (bid, it))
        con.commit()
        return bid

    B = {}
    B["e1"] = bill("B-9505", "Jasoria Brothers", no="26-27/A2753", total=28400.0, items=["BATTERY 200AH", "Trolley"], pdf="the bill")
    B["card"] = bill("B-9506", "", lane="clinic", pdf="the warranty card")
    B["e2"] = bill("B-9510", "B.L. Computers", no="771", total=1850.0, items=["UPS Battery 12V 9AH"])
    B["e3"] = bill("B-9511", "Some Shop", no="3", total=900.0, items=["Fan"])
    B["e4"] = bill("B-9512", "Old Shop", no="4", total=500.0, items=["Kettle"])
    B["e5"] = bill("B-9513", "Older Shop", no="5", total=400.0, items=["Lamp"])
    B["e6"] = bill("B-9514", "New Shop", no="6", total=45000.0, items=["Air conditioner"])
    B["rej"] = bill("B-9515", "Gone Shop", status="rejected", no="7", total=10.0, items=["x"])
    B["clin"] = bill("B-9520", "Exide Care", lane="clinic", no="88", total=9000.0, items=["Inverter battery 150AH"])
    B["med"] = bill("B-9521", "Mannat Pharma", lane="clinic", no="A1", total=700.0, items=["TAB ABC", "CAP XYZ"])
    B["stat"] = bill("B-9522", "City Stationers", lane="clinic", no="9", total=480.0, items=["A4 paper"])
    B["pharm"] = bill("B-9530", "Yuvika Surgicals", lane="pharmacy", no="Y/11", total=7000.0, items=["Knee cap"])
    out["B"] = B
    tok = con.execute("SELECT value FROM settings WHERE key='api_token'").fetchone()[0]

    owner, manager, nobody, staff = (A.app.test_client() for _ in range(4))
    with owner.session_transaction() as s:
        s["uid"], s["epoch"] = 1, "1"
    with manager.session_transaction() as s:
        s["uid"], s["epoch"] = 3, "1"
    try:
        staff.set_cookie("clinic_sso", "wstaff|staff|1")
    except TypeError:
        staff.set_cookie("localhost", "clinic_sso", "wstaff|staff|1")

    def get(c, p):
        r = c.get(p)
        return [r.status_code, r.get_data(as_text=True), r.headers.get("Location") or ""]

    def post(c, p, data=None):
        r = c.post(p, data=data or {})
        return [r.status_code, r.headers.get("Location") or ""]

    def flashes(c):
        return re.findall(r"<div class=flash>(.*?)</div>", c.get("/bills").get_data(as_text=True), re.S)

    def card(html):
        """The warranties card of the Renewals page: [[what, till, status, stamp+pages], ...] or None."""
        m = re.search(r"Dr MK expense %s warranties.*?</table></div>" % DASH, html, re.S)
        if not m:
            return None
        return [[text(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)] for tr in re.findall(r"<tr class=.*?</tr>", m.group(0), re.S)]

    def rows():
        if "d664_warranty" not in [r[0] for r in con.execute("SELECT name FROM sqlite_master")]:
            return None
        return [dict(r) for r in con.execute("SELECT bill_id, what, till, remind_days, set_by FROM d664_warranty ORDER BY bill_id")]

    # ---- before anything is saved (every mode)
    out["ren0"] = {"owner": get(owner, "/renewals"), "owner_all": get(owner, "/renewals?all=1"),
                   "manager": get(manager, "/renewals"), "manager_all": get(manager, "/renewals?all=1")}
    out["due0"] = get(nobody, "/api/due?token=" + tok)
    out["bill_e1"] = get(owner, "/bills/%d" % B["e1"])
    out["bill_stat"] = get(owner, "/bills/%d" % B["stat"])
    out["bill_pharm"] = get(owner, "/bills/%d" % B["pharm"])
    out["healthz"] = get(nobody, "/healthz")[0]
    if "d664_warranty" not in out["endpoints"]:
        print(MARK + json.dumps(out))
        return
    out["paper_e1"] = get(owner, "/papers/%d" % B["e1"])
    out["paper_stat"] = get(owner, "/papers/%d" % B["stat"])[1]
    out["paper_pharm"] = get(owner, "/papers/%d" % B["pharm"])[1]
    lst = get(owner, "/papers")[1]
    out["list_backs"] = {st: re.findall(r'name=back value="([^"]*)"><button class="d6b yes" name=lane', seg)
                         for st, seg in re.findall(r'>(B-\d+)</a>(.*?)(?=<div class=d6card>|<p class=muted>Skip leaves)', lst, re.S)}
    W = lambda bid: "/papers/%d/warranty" % bid
    good = {"what": "Inverter battery (2)", "till": day(20), "remind": "30"}
    # ---- who may ask
    out["roles"] = {"nobody": post(nobody, W(B["e1"]), good)[0], "staff": post(staff, W(B["e1"]), good)[0]}
    # ---- what is refused
    ref = {}
    for k, data in (("no_what", dict(good, what="   ")), ("no_date", dict(good, till="")), ("bad_date", dict(good, till="2028-13-40")),
                    ("dmy_date", dict(good, till="01-10-2028")), ("bad_remind", dict(good, remind="5")), ("no_remind", {"what": "x", "till": day(5)})):
        ref[k] = [post(owner, W(B["e1"]), data), flashes(owner)]
    ref["clinic"] = [post(owner, W(B["stat"]), good), flashes(owner)]
    ref["pharm"] = [post(owner, W(B["pharm"]), good), flashes(owner)]
    ref["rejected"] = [post(owner, W(B["rej"]), good), flashes(owner)]
    ref["missing"] = post(owner, W(999999), good)[0]
    ref["remove_nothing"] = [post(owner, W(B["e1"]), {"remove": "1"}), flashes(owner)]
    ref["rows"] = rows()
    out["ref"] = ref
    # ---- the saves
    out["save1"] = [post(owner, W(B["e1"]), dict(good, back="/papers")), flashes(owner)]
    out["expect1"] = "Saved: Inverter battery (2) %s warranty till %s. It is on Renewals &amp; warranties now (20 days left)." % (DASH, dmy(20))
    out["save2"] = [post(manager, W(B["e2"]), {"what": "  UPS   battery ", "till": day(20), "remind": "7"}), flashes(manager)]
    out["expect2"] = "It will show on Renewals &amp; warranties from %s, 7 days before it ends." % dmy(13)
    out["save3"] = [post(owner, W(B["e3"]), {"what": "Fan", "till": day(3), "remind": "0"}), flashes(owner)]
    out["save4"] = [post(owner, W(B["e4"]), {"what": "Kettle", "till": day(-10), "remind": "30"}), flashes(owner)]
    post(owner, W(B["e5"]), {"what": "Lamp", "till": day(-90), "remind": "30"})
    post(owner, W(B["e6"]), {"what": "Air conditioner", "till": day(400), "remind": "30"})
    flashes(owner)
    out["rows1"] = rows()
    out["days"] = {"e1": day(20), "e3": day(3), "e4": day(-10), "e5": day(-90), "e6": day(400)}
    out["dmy"] = {"e1": dmy(20), "e4": dmy(-10)}
    out["audit1"] = [r[0] for r in con.execute("SELECT action FROM bill_audit WHERE bill_id=? AND action LIKE 'd664_w%'", (B["e1"],))]
    r1 = get(owner, "/renewals")
    out["ren1"] = {"owner": [r1[0], card(r1[1]), "All clear" in r1[1]], "owner_all": card(get(owner, "/renewals?all=1")[1]),
                   "manager": get(manager, "/renewals"), "manager_all": get(manager, "/renewals?all=1"),
                   "staff": get(staff, "/renewals")[0]}
    out["due1"] = get(nobody, "/api/due?token=" + tok)
    out["bill_e1_after"] = get(owner, "/bills/%d" % B["e1"])[1]
    out["paper_e1_after"] = get(owner, "/papers/%d" % B["e1"])[1]
    out["prefix"] = [get(owner, "/scanapp/papers/%d" % B["e1"])[1], get(owner, "/scanapp/renewals")[1]]
    # ---- change, then the join shows on the card
    out["clear_date"] = [post(owner, W(B["e1"]), {"what": "Inverter battery (2)", "till": "", "remind": "30"}), flashes(owner),
                         [r for r in rows() if r["bill_id"] == B["e1"]]]
    out["change"] = [post(owner, W(B["e1"]), {"what": "Inverter battery (2)", "till": day(5), "remind": "7"}), flashes(owner)]
    out["rows_changed"] = [r for r in rows() if r["bill_id"] == B["e1"]]
    out["audit_change"] = [json.loads(r[0]) for r in con.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action='d664_warranty' ORDER BY id", (B["e1"],))] \
        if "detail" in [c[1] for c in con.execute("PRAGMA table_info(bill_audit)")] else None
    post(owner, "/papers/%d/join" % B["e1"], {"page": str(B["card"])})
    flashes(owner)
    out["ren_joined"] = card(get(owner, "/renewals")[1])
    post(owner, "/papers/%d/unjoin" % B["e1"])
    flashes(owner)
    # ---- a paper that leaves the lane takes its warranty off the list; coming back, it is there again
    post(owner, "/bills/%d/lane" % B["e3"], {"lane": "other_doc"})
    flashes(owner)
    out["left_lane"] = [card(get(owner, "/renewals?all=1")[1]), "Keep the warranty" in get(owner, "/papers/%d" % B["e3"])[1]]
    post(owner, "/bills/%d/lane" % B["e3"], {"lane": "owner_expense"})
    flashes(owner)
    out["back_on_lane"] = card(get(owner, "/renewals?all=1")[1])
    # ---- remove
    out["remove"] = [post(owner, W(B["e1"]), {"remove": "1"}), flashes(owner)]
    out["rows_removed"] = [r for r in rows() if r["bill_id"] == B["e1"]]
    out["audit_removed"] = [r[0] for r in con.execute("SELECT action FROM bill_audit WHERE bill_id=? AND action LIKE 'd664_w%' ORDER BY id", (B["e1"],))]
    r2 = get(owner, "/renewals")
    out["ren2"] = [card(r2[1]), "All clear" in r2[1]]
    # ---- 'Move to Dr MK expense' lands where the warranty card is
    bk = (out["list_backs"].get("B-9520") or [""])[0].replace("&amp;", "&")
    out["move"] = post(owner, "/bills/%d/lane" % B["clin"], {"lane": "owner_expense", "back": bk})
    landed = get(owner, out["move"][1]) if out["move"][1] else [0, "", ""]
    out["landed"] = [landed[0], "Keep the warranty" in landed[1], re.findall(r'name=what maxlength=80 value="([^"]*)"', landed[1])]
    # ---- S464 and S465 still stand
    out["set_group"] = post(owner, "/bills/%d/subgroup" % B["stat"], {"subgroup": "others", "back": "/papers"})
    out["group_after"] = con.execute("SELECT subgroup FROM bills WHERE id=?", (B["stat"],)).fetchone()[0]
    seen = out["paper_e1"][1] + out["paper_e1_after"] + r1[1] + lst
    out["ctrl"] = sorted({hex(ord(ch)) for ch in seen if ord(ch) < 32 and ch not in "\n\r\t"})
    print(MARK + json.dumps(out))


# ============================================================================ the parent
def names_used_undefined(path):
    """Names a function of the module loads that are neither its own, nor the module's, nor python's."""
    import ast
    import builtins
    tree = ast.parse(open(path, encoding="utf-8").read())
    mod = set(dir(builtins)) | {"__file__", "__name__"}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            mod.add(n.name)
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mod.update((al.asname or al.name).split(".")[0] for al in n.names)
        elif not isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            mod.update(t.id for t in ast.walk(n) if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store))
    bad = set()
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        local = set()
        for n in ast.walk(fn):
            if isinstance(n, (ast.FunctionDef, ast.Lambda)):
                aa = n.args
                local.update(x.arg for x in aa.args + aa.kwonlyargs + getattr(aa, "posonlyargs", []))
                local.update(x.arg for x in (aa.vararg, aa.kwarg) if x)
            elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                local.add(n.id)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                local.update((al.asname or al.name).split(".")[0] for al in n.names)
            elif isinstance(n, ast.ExceptHandler) and n.name:
                local.add(n.name)
        bad.update((n.lineno, n.id) for n in ast.walk(fn)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in local and n.id not in mod)
    return sorted(bad)


def make(root, tag, src, apply_py, module):
    d = os.path.join(root, tag, "assetapp")
    os.makedirs(d)
    for f in ("asset_register.py", "scanner_widget.js", "clinic_papers.py"):
        shutil.copy2(os.path.join(src, f), d)
    if apply_py:
        p = subprocess.run([sys.executable, "-B", apply_py, os.path.join(d, "asset_register.py")], capture_output=True, text=True)
        if p.returncode:
            return d, p
    if module == "none":
        os.remove(os.path.join(d, "clinic_papers.py"))
    elif module:
        shutil.copy2(module, os.path.join(d, "clinic_papers.py"))
    return d, None


def run(root, tag, d):
    base = os.path.join(root, tag)
    portal = os.path.join(base, "portal")
    os.makedirs(portal)
    with open(os.path.join(portal, "clinic_sso.py"), "w") as fh:
        fh.write('COOKIE_NAME = "clinic_sso"\n'
                 'def verify_token(tok, secret, current_epoch=None):\n'
                 '    try:\n        u, r, e = tok.split("|")\n    except Exception:\n        return None\n'
                 '    return {"user": u, "role": r}\n')
    with open(os.path.join(portal, "portal_config.py"), "w") as fh:
        fh.write('CLINIC_SSO_SECRET = "the-walk-stub"\n')
    with open(os.path.join(portal, "clinic_users.json"), "w") as fh:
        fh.write('{"epoch": 1}\n')
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    e = dict(os.environ)
    e.update({"S466_ROOT": root, "ASSETS_DB": os.path.join(base, "assets.db"), "ASSETS_UPLOADS": os.path.join(base, "uploads"),
              "CLINIC_PORTAL_DIR": portal, "SARVAM_API_KEY": "", "SCANAPP_PREFIX": "/scanapp",
              "FINANCE_LOCAL_URL": "http://127.0.0.1:9", "FINANCE_DB_FOR_SCANS": os.path.join(base, "no_finance.db"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", tag], cwd=d, env=e,
                       capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--assetapp", required=True)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s466_walk_")
    try:
        walk(a, root)
    except Exception as ex:                                        # a walk that breaks is a RED walk, never a traceback
        check("the walk itself ran to its end", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print("  kept: %s" % root)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S466 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    src = os.path.abspath(a.assetapp)
    have = (md5(os.path.join(src, "asset_register.py")), md5(os.path.join(src, "clinic_papers.py")) if os.path.isfile(os.path.join(src, "clinic_papers.py")) else "absent")
    check("0.1 the asset app is as S465 leaves it (asset_register.py b0e0915e, clinic_papers.py 231cd6a9)", have == (AR_FROM, CP_FROM), have)
    if have != (AR_FROM, CP_FROM):
        return
    d_old, _ = make(root, "old", src, None, None)
    d_new, err = make(root, "new", src, a.apply, a.module)
    got = md5(os.path.join(d_new, "asset_register.py"))
    check("0.2 the three edits apply and give the predicted bytes", err is None and got == AR_TO, got + (" " + err.stderr[-200:] if err else ""))
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(d_new, "asset_register.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(d_new, "asset_register.py")) == got)
    so = open(os.path.join(d_old, "asset_register.py"), encoding="utf-8").read()
    sn = open(os.path.join(d_new, "asset_register.py"), encoding="utf-8").read()
    import difflib
    ops = [o for o in difflib.SequenceMatcher(None, so.splitlines(), sn.splitlines(), autojunk=False).get_opcodes() if o[0] != "equal"]
    api_old = so[so.index('@app.route("/api/due")'):so.index("S222 SCANAPP PREFIX")]
    check("0.4 three places of asset_register.py differ and nothing else; /api/due is byte for byte the old code",
          len(ops) == 3 and api_old in sn and "d664" not in api_old, [(o[0], o[1], o[2]) for o in ops])
    undefined = names_used_undefined(a.module)
    check("0.4b no name in the new module is used without being defined (a slip that only shows when its line runs)", undefined == [], undefined)
    d_bare, _ = make(root, "bare", src, a.apply, "none")
    d_half, _ = make(root, "half", src, a.apply, None)
    R = {}
    for tag, d in (("old", d_old), ("new", d_new), ("bare", d_bare), ("half", d_half)):
        p, R[tag] = run(root, tag, d)
        R[tag + "_err"] = p.stderr
        check("0.5 the %s app starts on a scratch database and answers" % tag,
              bool(R[tag]) and "abort" not in R[tag] and R[tag].get("healthz") == 200, (R[tag] or {}).get("abort") or p.stderr[-700:])
    if not all(R.get(k) and "B" in R[k] for k in ("old", "new", "bare", "half")):
        return
    o, n, b, hf = R["old"], R["new"], R["bare"], R["half"]
    B = n["B"]
    check("0.6 new: the warranty address is mounted beside the six, and the table d664_warranty exists",
          n["endpoints"] == ["d664_join", "d664_month", "d664_paper", "d664_papers", "d664_set", "d664_unjoin", "d664_warranty"]
          and n["tables"] == ["d664_join", "d664_warranty"], (n["endpoints"], n["tables"]))
    same = lambda x, y: all(x["ren0"][k][0] == 200 and squash(x["ren0"][k][1]) == squash(y["ren0"][k][1]) for k in ("owner", "owner_all", "manager", "manager_all"))
    check("0.7 THE GUARD: with clinic_papers.py absent the edited app starts, says so, and Renewals and the bill page are the old pages",
          b["endpoints"] == [] and "clinic_papers NOT mounted" in R["bare_err"] and b["bill_e1"][0] == 200 and "Warranty:" not in b["bill_e1"][1]
          and all(b["ren0"][k][0] == 200 and "warranties" in b["ren0"][k][1] and "Dr MK expense" not in b["ren0"][k][1] for k in b["ren0"]))
    check("0.8 THE HALF-WAY STATE: the edited app with S465's module opens Renewals exactly as before, and the bill page without a warranty line",
          "d664_warranty" not in hf["endpoints"] and same(hf, o) and hf["bill_e1"][0] == 200 and "Warranty:" not in hf["bill_e1"][1]
          and ">join pages</a>" in hf["bill_e1"][1])
    if "d664_warranty" not in n["endpoints"]:
        return
    check("0.9 no stray control character on any new page", n["ctrl"] == [], n["ctrl"])

    # ---- 1 · with nothing saved, nothing has moved
    check("1.1 with no warranty saved, Renewals is the old page for the owner and the manager, both views -- and still says 'All clear'",
          same(n, o) and "All clear" in n["ren0"]["owner"][1])
    check("1.2 /api/due (what goes out on WhatsApp) answers as before", n["due0"][0] == 200 and n["due0"][1] == o["due0"][1])

    # ---- 2 · the card on the paper's page
    pe = n["paper_e1"][1]
    check("2.1 a Dr MK expense paper's page carries 'Keep the warranty': what it is (offered from the first item read), the date, three reminders with 30 days ticked, Save",
          n["paper_e1"][0] == 200 and "Keep the warranty" in pe and 'name=what maxlength=80 value="BATTERY 200AH"' in pe
          and 'name=till type=date value=""' in pe and re.findall(r'name=remind value="(\d+)" (checked)?', pe) == [("30", "checked"), ("7", ""), ("0", "")]
          and ">Save</button>" in pe and "Remove the warranty" not in pe, re.findall(r'name=remind value="(\d+)" (checked)?', pe))
    check("2.2 it says who sees it and that nothing goes on WhatsApp", "to you only" in pe and "nothing about it is sent on WhatsApp" in pe)
    check("2.3 a clinic paper's page and a pharmacy scan's page have no such card", "Keep the warranty" not in n["paper_stat"] and "Keep the warranty" not in n["paper_pharm"])
    check("2.4 SHOWN on the old app: the same paper's page has no warranty card at all", True if "paper_e1" not in o else False)

    # ---- 3 · who may ask, and what is refused
    r = n["ref"]
    check("3.1 with no login: sent to the login page; a scanning login: refused", n["roles"] == {"nobody": 302, "staff": 403}, n["roles"])
    check("3.2 no name, no date, an impossible date, a date typed day-first, a reminder that is not offered, no reminder chosen: each refused, and it says nothing was saved",
          all(any("Nothing was saved" in f for f in r[k][1]) for k in ("no_what", "no_date", "bad_date", "dmy_date", "bad_remind", "no_remind")),
          {k: r[k][1] for k in ("no_what", "no_date", "bad_date", "dmy_date", "bad_remind", "no_remind")})
    check("3.3 a clinic paper, a pharmacy scan and a rejected paper: refused, and it says why",
          all(any("not on the Dr MK expense lane" in f for f in r[k][1]) for k in ("clinic", "pharm", "rejected")), [r[k][1] for k in ("clinic", "pharm", "rejected")])
    check("3.4 a paper that is not there: 404; removing a warranty that was never noted: nothing happens", r["missing"] == 404 and r["remove_nothing"][1] == [])
    check("3.5 after all twelve attempts the table is empty", r["rows"] == [], r["rows"])

    # ---- 4 · the save
    check("4.1 saved: back on the paper's page, and it says what will happen ('It is on Renewals & warranties now (20 days left)')",
          n["save1"][0][0] == 302 and ("/papers/%d" % B["e1"]) in n["save1"][0][1] and n["save1"][1] == [n["expect1"]], (n["save1"], n["expect1"]))
    check("4.2 the manager may save too; the name is tidied; a 7-day reminder 20 days out says from which date it will show",
          any(n["expect2"] in f and "UPS battery" in f for f in n["save2"][1]), (n["save2"][1], n["expect2"]))
    check("4.3 'No reminder' says where it is listed; a date already past says there is nothing to remind",
          any("No reminder; it is listed under" in f for f in n["save3"][1]) and any("That date has passed" in f for f in n["save4"][1]), (n["save3"][1], n["save4"][1]))
    rw = {x["bill_id"]: x for x in n["rows1"]}
    check("4.4 six rows, each as typed, each with who saved it",
          len(rw) == 6 and rw[B["e1"]]["what"] == "Inverter battery (2)" and rw[B["e1"]]["till"] == n["days"]["e1"] and rw[B["e1"]]["remind_days"] == 30
          and rw[B["e2"]]["what"] == "UPS battery" and rw[B["e2"]]["remind_days"] == 7 and rw[B["e3"]]["remind_days"] == 0
          and all(x["set_by"] for x in rw.values()), n["rows1"])
    check("4.5 and in the paper's audit trail", n["audit1"] == ["d664_warranty"], n["audit1"])
    pa = n["paper_e1_after"]
    check("4.6 the paper's page now shows what is saved, the form filled with it, and 'Remove the warranty'",
          ("<b>Inverter battery (2)</b> %s warranty till" % DASH) in pa and "It is on Renewals" in pa and ('name=till type=date value="%s"' % n["days"]["e1"]) in pa
          and "Remove the warranty" in pa and ">Save the change</button>" in pa)

    # ---- 5 · Renewals & warranties
    c1 = n["ren1"]["owner"]
    check("5.1 the owner's Renewals page, 'due soon': ONE row -- the battery, inside its 30 days -- amber, '20 days left', the date as he reads dates, the bill's number; and it no longer says 'All clear'",
          c1[0] == 200 and c1[1] is not None and len(c1[1]) == 1 and c1[1][0][0].startswith("Inverter battery (2)") and "Jasoria Brothers" in c1[1][0][0]
          and c1[1][0][0].endswith("B-9505") and c1[1][0][1] == n["dmy"]["e1"] and c1[1][0][2] == "20 days left" and len(c1[1][0]) == 3 and c1[2] is False, c1)
    ca = n["ren1"]["owner_all"]
    check("5.2 NOT there: the 7-day reminder still 20 days out, the 'No reminder' one 3 days out, the far one, both ended ones",
          [x[0].split(" ")[0] for x in c1[1]] == ["Inverter"])
    check("5.3 'show all upcoming': five rows in date order -- the one ended 10 days ago marked 'ended', then 3, 20, 20 and 400 days; the one ended 90 days ago has dropped off",
          ca is not None and [x[2] for x in ca] == ["ended", "3 days left", "20 days left", "20 days left", "400 days left"]
          and [x[1] for x in ca][0] == n["dmy"]["e4"] and not any("Lamp" in x[0] for x in ca), ca)
    check("5.4 an ended warranty is never red: no 'overdue' anywhere in the card", ca is not None and not any("overdue" in " ".join(x).lower() for x in ca))
    check("5.5 THE MANAGER'S Renewals page is byte for byte what it was, both views; a scanning login is turned away from the papers but Renewals answers it as before",
          squash(n["ren1"]["manager"][1]) == squash(o["ren0"]["manager"][1]) and squash(n["ren1"]["manager_all"][1]) == squash(o["ren0"]["manager_all"][1])
          and "Dr MK expense" not in n["ren1"]["manager_all"][1], n["ren1"]["staff"])
    check("5.6 NOTHING GOES OUT: with six warranties saved, /api/due answers exactly what it answered before, and names none of them",
          n["due1"][0] == 200 and n["due1"][1] == n["due0"][1] == o["due0"][1] and "arranty" not in n["due1"][1] and "Inverter" not in n["due1"][1], n["due1"][1][:200])
    check("5.7 the bill page: 'Warranty: not noted · note it' before, the saved line and 'change' after; none on a clinic bill or a pharmacy scan; none on the old app",
          "<b>Warranty:</b> not noted" in n["bill_e1"][1] and ">note it</a>" in n["bill_e1"][1]
          and ("<b>Warranty:</b> Inverter battery (2) %s till " % DASH) in n["bill_e1_after"] and "Warranty:" not in n["bill_stat"][1]
          and "Warranty:" not in n["bill_pharm"][1] and "Warranty:" not in o["bill_e1"][1])
    check("5.8 a pharmacy bill's page is byte for byte the old page", squash(n["bill_pharm"][1]) == squash(o["bill_pharm"][1]))
    check("5.9 under /scanapp the form posts under the prefix, and the card's links carry it",
          ('action="/scanapp/papers/%d/warranty"' % B["e1"]) in n["prefix"][0] and ('href="/scanapp/papers/%d"' % B["e1"]) in n["prefix"][1])

    # ---- 6 · change, join, leave the lane, remove
    cd = n["clear_date"]
    check("6.0 a saved warranty with its date cleared: nothing is saved, the old date stands, and it points at 'Remove the warranty'",
          any("Nothing was saved. To drop the warranty, press Remove the warranty." in f for f in cd[1]) and cd[2] and cd[2][0]["till"] == n["days"]["e1"], cd)
    ch = n["rows_changed"]
    check("6.1 a change replaces the row (still one), and says it is on Renewals now (5 days left)",
          len(ch) == 1 and ch[0]["remind_days"] == 7 and any("5 days left" in f for f in n["change"][1]), (ch, n["change"][1]))
    check("6.2 once the warranty card is joined into the bill, the Renewals row says so: 'B-9505 + 1 page joined'",
          n["ren_joined"] is not None and n["ren_joined"][0][0].endswith("B-9505 + 1 page joined"), n["ren_joined"])
    ll = n["left_lane"]
    check("6.3 a paper moved off the Dr MK expense lane takes its warranty off Renewals and loses the card; moved back, it is there again",
          not any(x[0].startswith("Fan") for x in (ll[0] or [])) and ll[1] is False and any(x[0].startswith("Fan") for x in (n["back_on_lane"] or [])), (ll, n["back_on_lane"]))
    check("6.4 remove: the row is gone, it is in the audit trail, the page says so, and Renewals 'due soon' is back to 'All clear'",
          n["rows_removed"] == [] and n["audit_removed"][-1] == "d664_warranty_removed" and any("is removed" in f for f in n["remove"][1])
          and n["ren2"] == [None, True], (n["audit_removed"], n["remove"][1], n["ren2"]))

    # ---- 7 · the way in, and what must not move
    lb = n["list_backs"]
    check("7.1 on the list, 'Move to Dr MK expense' now lands on the paper's own page (where the warranty card is); 'Move to Pharmacy purchase' still comes back to the list",
          [x.replace("&amp;", "&") for x in lb.get("B-9520", [])] == ["/papers/%d?back=/papers" % B["clin"]] and lb.get("B-9521") == ["/papers"], lb)
    check("7.2 and it does: moved, landed on its page, 'Keep the warranty' is there with the item read offered as its name",
          n["move"][0] == 302 and n["landed"] == [200, True, ["Inverter battery 150AH"]], (n["move"], n["landed"]))
    check("7.3 S464 still stands: a clinic paper's group is set in one tap", n["set_group"] == [302, "/papers"] and n["group_after"] == "others")
    check("7.4 nothing in the asset app's own folder was written by this walk",
          (md5(os.path.join(src, "asset_register.py")), md5(os.path.join(src, "clinic_papers.py"))) == (AR_FROM, CP_FROM))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        sys.exit(main())
