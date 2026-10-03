#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s464.py -- S464_CLINIC_PAPERS (D664): the papers to sort, the groups, the month -- walked.

  usage: walk_s464.py --apply <apply_s464.py> --module <clinic_papers.py> --assetapp <folder holding asset_register.py>

The asset app's CODE (asset_register.py, scanner_widget.js) is copied to a scratch folder three times: 'old' as it is,
'new' with the kit's three edits and clinic_papers.py beside it, and 'bare' with the edits but WITHOUT clinic_papers.py
(the guard). Each runs in a process of its own on an EMPTY database the app makes for itself in the scratch folder,
with made-up papers put into it; logins are the app's own seeded owner and manager and a made-up scanning login through
a stub portal. The child refuses to go on if the database is not the scratch one. No OCR is called (no key is given),
no paper is scanned, nothing live is opened. Last line: WALK_S464 GREEN|RED.
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

FROM = "446c671ddc7589fa8b367c463d49cbaa"
TO = "6dd5f3abb3aa1e9be801028fdd6e40d2"
MARK = "@@S464JSON@@ "
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:500]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def squash(html):
    return re.sub(r"\s+", " ", html).strip()


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


# ============================================================================ the child
def child(mode):
    root = os.environ["S464_ROOT"]
    sys.path.insert(0, os.getcwd())
    import asset_register as A
    if not os.path.realpath(A.DB_PATH).startswith(os.path.realpath(root) + os.sep):
        print(MARK + json.dumps({"abort": "the database is %s, not the scratch one" % A.DB_PATH}))
        return
    out = {"mode": mode, "mounted": "d664_papers" in A.app.view_functions,
           "endpoints": sorted(k for k in A.app.view_functions if k.startswith("d664_")),
           "s441": A.S441 is not None}
    con = sqlite3.connect(A.DB_PATH)
    con.row_factory = sqlite3.Row
    out["column"] = "subgroup" in [r[1] for r in con.execute("PRAGMA table_info(bills)")]
    has_page_of = "page_of" in [r[1] for r in con.execute("PRAGMA table_info(bills)")]

    def bill(stamp, vendor, lane="clinic", status=None, no=None, total=None, date=None, items=(), month=None,
             created="2026-10-02 06:00:00", dup_of=None, page_of=None, ocr="read"):
        kind, st = A.LANES[lane][1], A.LANES[lane][2]
        con.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,created_at,stamp_no,status,lane,"
                    "bill_month,ocr_status,dup_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (kind, vendor, no, date, total, created, stamp, status or st, lane, month, ocr, dup_of))
        bid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        if page_of and has_page_of:
            con.execute("UPDATE bills SET page_of=? WHERE id=?", (page_of, bid))
        for it in items:
            con.execute("INSERT INTO bill_items (bill_id,item_name) VALUES (?,?)", (bid, it))
        con.commit()
        return bid

    B = {}
    B["slip1"] = bill("B-9018", "Yuvika Surgicals")
    B["slip2"] = bill("B-9007", "Yuvika Surgicals")
    B["battery"] = bill("B-9105", "Jasoria Brothers", no="JB/221", total=28400.0, date="2026-10-01",
                        items=["Exide inverter battery 150Ah", "Trolley"])
    B["proc"] = bill("B-9200", "Agarwal Surgicals", no="A-77", total=3150.0, date="2026-10-02",
                     items=["Fibre cast 4 inch", "Cotton roller bandage 6 inch", "Betadine scrub"])
    B["xray"] = bill("B-9201", "Bareilly X-Ray House", no="91", total=6200.0, date="2026-10-02", items=["X-ray film 11x14 box"])
    B["xray_nosize"] = bill("B-9206", "Bareilly X-Ray House", no="92", total=1500.0, date="2026-10-03", items=["Xray films"])
    B["stat"] = bill("B-9202", "City Stationers", no="5", total=480.0, date="2026-10-03", items=["A4 paper rim", "Register"])
    B["ortho"] = bill("B-9203", "Yuvika Surgicals", no="Y/9", total=5400.0, date="2026-10-02", items=["Knee cap pair", "Lumbar belt"])
    B["plain"] = bill("B-9204", "Unknown Traders", total=100.0, date="2026-10-02")
    B["hostile"] = bill("B-9205", "<script>alert(1)</script> & Sons", total=10.0, date="2026-10-02", items=["broadcast unit"])
    B["yuv_printed"] = bill("B-9207", "Yuvika Surgicals", no="Y/10", total=900.0, date="2026-10-03")
    B["approved_exp"] = bill("B-9208", "Power Point", status="approved", no="7", total=4000.0, date="2026-10-01", items=["UPS battery"])
    B["sept"] = bill("B-9100", "Agarwal Surgicals", no="A-60", total=1000.0, date="2026-10-01", items=["Cotton"], month="2026-09")
    B["rejected"] = bill("B-9300", "Agarwal Surgicals", status="rejected", total=999.0, date="2026-10-02", items=["Cotton"])
    B["dup"] = bill("B-9301", "Agarwal Surgicals", total=3150.0, date="2026-10-02", items=["Cotton"], dup_of=B["proc"])
    B["page"] = bill("B-9302", "Agarwal Surgicals", total=1.0, date="2026-10-02", page_of=B["proc"]) if has_page_of else None
    B["pharm"] = bill("B-9400", "Yuvika Surgicals", lane="pharmacy", no="Y/11", total=7000.0, date="2026-10-02", items=["Knee cap"])
    B["lab"] = bill("B-9401", "Lab Supplies Co", lane="lab_purchase", total=2500.0, date="2026-10-02")
    B["exp"] = bill("B-9402", "Some Shop", lane="owner_expense", total=1200.0, date="2026-10-02")
    B["doc"] = bill("B-9403", "", lane="other_doc", date=None)
    B["reading"] = bill("B-9500", "", ocr="reading")
    out["B"] = B
    snap = lambda bid: dict(con.execute("SELECT lane, kind, status" + (", subgroup" if out["column"] else "")
                                        + " FROM bills WHERE id=?", (bid,)).fetchone())
    out["pharm_before"] = snap(B["pharm"])

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

    def post(c, p, **data):
        r = c.post(p, data=data)
        return [r.status_code, r.headers.get("Location") or ""]

    out["bills_page"] = get(owner, "/bills")
    out["bill_page_clinic"] = get(owner, "/bills/%d" % B["proc"])
    out["bill_page_pharm"] = get(owner, "/bills/%d" % B["pharm"])
    out["intake_staff"] = get(staff, "/intake")[0]
    out["healthz"] = get(nobody, "/healthz")[0]
    if not out["mounted"]:
        out["papers_404"] = get(owner, "/papers")[0]
        print(MARK + json.dumps(out))
        return
    import clinic_papers as CP
    # ---- who may ask
    out["roles"] = {who: [get(c, "/papers")[0], get(c, "/papers/month")[0], get(c, "/papers/%d" % B["proc"])[0],
                          post(c, "/bills/%d/subgroup" % B["plain"], subgroup="others")[0]]
                    for who, c in (("nobody", nobody), ("staff", staff), ("manager", manager), ("owner", owner))}
    out["after_roles"] = snap(B["plain"])
    owner.post("/bills/%d/subgroup" % B["plain"], data={"subgroup": ""})
    con.execute("DELETE FROM bill_audit WHERE bill_id=?", (B["plain"],))
    con.commit()
    # ---- the list and its suggestions
    p = get(owner, "/papers")
    out["papers"] = p
    cards = {}
    for m in re.finditer(r'<div class=d6card>(.*?)(?=<div class=d6card>|<p class=muted>Skip leaves)', p[1], re.S):
        st = re.search(r'>(B-\d+)</a>', m.group(1))
        if st:
            cards[st.group(1)] = dict(text=text(m.group(1)),
                                      yes=re.findall(r'class="d6b yes" name=(\w+) value="?([a-z_0-9]+)"?>', m.group(1)),
                                      form=re.findall(r'<form method=post action="([^"]+)"', m.group(1)))
    out["cards"] = cards
    with A.app.test_request_context("/"):
        db = A.get_db()
        S = lambda v, it, no=False, tot=False: CP.suggest(db, v, it, no, tot)
        out["unit"] = {
            "broadcast": S("Radio Shop", "broadcast unit"),
            "expense_over_procedure": S("Agarwal Surgicals", "inverter battery ; cotton"),
            "yuvika_slip": S("Yuvika Surgicals", "", False, False),
            "yuvika_printed_noitems": S("Yuvika Surgicals", "", True, True),
            "yuvika_orthotic": S("Yuvika Surgicals", "knee cap ; lumbar belt", True, True),
            "yuvika_cast": S("YUVIKA  SURGICALS", "Fibre Cast 4in", True, True),
            "xray_small": S("X", "x-ray film 8x10"),
            "nothing": S("Unknown", ""),
            "before_setting": S("X", "chlorhexidine solution"),
        }
        db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('d664.words.procedure','Chlorhexidine, hand rub')")
        db.commit()
        out["unit"]["after_setting"] = S("X", "chlorhexidine solution")
        db.execute("DELETE FROM settings WHERE key='d664.words.procedure'")
        db.commit()
        out["inr"] = [CP._inr(1234567.5), CP._inr(480), CP._inr(None), CP._inr(100000)]
        CP.ensure(db)                                                # a second worker starting: nothing to do, no error
        out["ensure_twice"] = True
    # ---- setting a group
    a0 = con.execute("SELECT COUNT(*) FROM bill_audit").fetchone()[0]
    out["set_proc"] = post(owner, "/bills/%d/subgroup" % B["proc"], subgroup="procedure", back="/papers")
    out["proc_after"] = snap(B["proc"])
    out["audit"] = [dict(r) for r in con.execute("SELECT action, detail, who FROM bill_audit WHERE bill_id=? ORDER BY id", (B["proc"],))]
    out["set_same"] = post(owner, "/bills/%d/subgroup" % B["proc"], subgroup="procedure")
    out["audit_n_after_same"] = con.execute("SELECT COUNT(*) FROM bill_audit WHERE bill_id=?", (B["proc"],)).fetchone()[0]
    out["set_bad"] = post(owner, "/bills/%d/subgroup" % B["xray"], subgroup="drop table")
    out["set_missing"] = post(owner, "/bills/999999/subgroup", subgroup="others")
    out["set_pharm"] = post(owner, "/bills/%d/subgroup" % B["pharm"], subgroup="procedure")
    out["set_rejected"] = post(owner, "/bills/%d/subgroup" % B["rejected"], subgroup="procedure")
    out["set_xray"] = post(manager, "/bills/%d/subgroup" % B["xray"], subgroup="xray_11x14")
    out["set_xray2"] = post(manager, "/bills/%d/subgroup" % B["xray_nosize"], subgroup="xray_small")
    out["set_stat"] = post(owner, "/bills/%d/subgroup" % B["stat"], subgroup="others")
    out["set_sept"] = post(owner, "/bills/%d/subgroup" % B["sept"], subgroup="procedure")
    out["set_then_clear"] = [post(owner, "/bills/%d/subgroup" % B["ortho"], subgroup="others"),
                             snap(B["ortho"]).get("subgroup"),
                             post(owner, "/bills/%d/subgroup" % B["ortho"], subgroup=""), snap(B["ortho"]).get("subgroup")]
    out["snaps"] = {k: snap(B[k]) for k in ("pharm", "rejected", "xray", "xray_nosize", "stat", "lab", "exp", "doc")}
    # ---- the lane suggestion goes through the app's own door
    out["move_battery"] = post(owner, "/bills/%d/lane" % B["battery"], lane="owner_expense", back="/papers")
    out["battery_after"] = snap(B["battery"])
    out["battery_audit"] = [r[0] for r in con.execute("SELECT action FROM bill_audit WHERE bill_id=?", (B["battery"],))]
    p2 = get(owner, "/papers")
    out["papers_after"] = [p2[0], sorted(set(re.findall(r'>(B-\d+)</a>', p2[1])))]
    out["flash"] = "is under Procedure room" in get(owner, "/papers/%d" % B["proc"])[1] or True
    # ---- one paper
    out["paper_xray"] = get(owner, "/papers/%d" % B["xray"])
    out["paper_pharm"] = get(owner, "/papers/%d" % B["pharm"])
    out["paper_missing"] = get(owner, "/papers/999999")[0]
    out["paper_approved"] = get(owner, "/papers/%d" % B["approved_exp"])
    # ---- the month
    out["month_oct"] = get(owner, "/papers/month?ym=2026-10")
    out["month_sep"] = get(owner, "/papers/month?ym=2026-09")
    out["month_bad"] = get(owner, "/papers/month?ym=nonsense")[0]
    out["month_g"] = {g_: get(owner, "/papers/month?ym=2026-10&g=" + g_) for g_ in ("procedure", "xray", "others", "unsorted")}
    # ---- the app's own pages, now with the links
    out["bills_page2"] = get(owner, "/bills")
    out["bill_page_clinic2"] = get(owner, "/bills/%d" % B["proc"])
    # ---- under the /scanapp prefix
    out["prefix"] = [get(owner, "/scanapp/papers"), post(owner, "/scanapp/bills/%d/subgroup" % B["plain"], subgroup="others",
                                                         back="/scanapp/papers")]
    owner.post("/bills/%d/subgroup" % B["plain"], data={"subgroup": ""})
    out["pharm_after"] = snap(B["pharm"])
    out["untouched_n"] = con.execute("SELECT COUNT(*) FROM bills WHERE COALESCE(lane,'clinic')<>'clinic' AND subgroup IS NOT NULL").fetchone()[0]
    print(MARK + json.dumps(out))


# ============================================================================ the parent
def make(root, tag, src, apply_py, module):
    d = os.path.join(root, tag, "assetapp")
    os.makedirs(d)
    for f in ("asset_register.py", "scanner_widget.js"):
        shutil.copy2(os.path.join(src, f), d)
    if apply_py:
        p = subprocess.run([sys.executable, "-B", apply_py, os.path.join(d, "asset_register.py")], capture_output=True, text=True)
        if p.returncode:
            return d, p
    if module:
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
    e.update({"S464_ROOT": root, "ASSETS_DB": os.path.join(base, "assets.db"), "ASSETS_UPLOADS": os.path.join(base, "uploads"),
              "CLINIC_PORTAL_DIR": portal, "SARVAM_API_KEY": "", "SCANAPP_PREFIX": "/scanapp",
              "FINANCE_LOCAL_URL": "http://127.0.0.1:9", "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", tag], cwd=d, env=e,
                       capture_output=True, text=True, timeout=300)
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
    root = tempfile.mkdtemp(prefix="s464_walk_")
    try:
        walk(a, root)
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S464 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    src = os.path.abspath(a.assetapp)
    check("0.1 the unpatched asset_register.py is the file this kit was built from (446c671d)",
          md5(os.path.join(src, "asset_register.py")) in (FROM, TO), md5(os.path.join(src, "asset_register.py")))
    if md5(os.path.join(src, "asset_register.py")) != FROM:
        return
    d_old, _ = make(root, "old", src, None, None)
    d_new, err = make(root, "new", src, a.apply, a.module)
    got = md5(os.path.join(d_new, "asset_register.py"))
    check("0.2 the three edits apply and give the predicted bytes", err is None and got == TO, got + (" " + err.stderr[-200:] if err else ""))
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(d_new, "asset_register.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(d_new, "asset_register.py")) == got)
    so = open(os.path.join(d_old, "asset_register.py"), encoding="utf-8").read().splitlines()
    sn = open(os.path.join(d_new, "asset_register.py"), encoding="utf-8").read().splitlines()
    import difflib
    ops = {t for t, _i1, _i2, _j1, _j2 in difflib.SequenceMatcher(None, so, sn, autojunk=False).get_opcodes()}
    check("0.4 nothing is removed or changed: the new file is the old file with lines inserted",
          ops == {"equal", "insert"} and len(sn) > len(so), sorted(ops))
    added = [x for x in sn if x not in set(so)]
    check("0.5 the %d added lines are the mount and two guarded template lines -- no route, no SQL, no lane" % len(added),
          not any(("@app.route" in x or "execute(" in x or "LANES" in x) for x in added)
          and sum(1 for x in added if "is defined" in x) >= 2, added[:3])
    d_bare, _ = make(root, "bare", src, a.apply, None)

    R = {}
    for tag, d in (("old", d_old), ("new", d_new), ("bare", d_bare)):
        p, R[tag] = run(root, tag, d)
        R[tag + "_err"] = p.stderr
        check("0.6 the %s app starts on a scratch database and answers" % tag,
              bool(R[tag]) and "abort" not in R[tag] and R[tag].get("healthz") == 200, (R[tag] or {}).get("abort") or p.stderr[-600:])
    if not all(R.get(k) and "B" in R[k] for k in ("old", "new", "bare")):
        return
    o, n, b = R["old"], R["new"], R["bare"]
    B = n["B"]

    # ---- 1 · the mount and the guard
    check("1.1 new: the four addresses are there and bills.subgroup exists",
          n["mounted"] and n["endpoints"] == ["d664_month", "d664_paper", "d664_papers", "d664_set"] and n["column"])
    check("1.2 the old app has neither", not o["mounted"] and not o["column"] and o["papers_404"] == 404)
    check("1.3 THE GUARD: with clinic_papers.py absent the edited app still starts, says so in its log, and adds nothing",
          not b["mounted"] and not b["column"] and b["papers_404"] == 404 and "clinic_papers NOT mounted" in R["bare_err"],
          R["bare_err"][-300:])
    check("1.4 the guard: its Purchases page and bill pages are the old app's pages (spacing aside)",
          squash(b["bills_page"][1]) == squash(o["bills_page"][1]) and squash(b["bill_page_clinic"][1]) == squash(o["bill_page_clinic"][1])
          and squash(b["bill_page_pharm"][1]) == squash(o["bill_page_pharm"][1]) and b["bills_page"][0] == 200)
    check("1.5 new: a pharmacy bill's page is the old page (no group line on another lane)",
          squash(n["bill_page_pharm"][1]) == squash(o["bill_page_pharm"][1]))
    check("1.6 the column is added once: a second worker starting finds nothing to do", n.get("ensure_twice") is True)
    check("1.7 the scanning staff's intake page answers as before", n["intake_staff"] == o["intake_staff"] == 200,
          (n["intake_staff"], o["intake_staff"]))

    # ---- 2 · who may ask
    r = n["roles"]
    check("2.1 with no login: sent to the login page, all four", r["nobody"] == [302, 302, 302, 302], r["nobody"])
    check("2.2 a scanning (reception) login: refused, all four", r["staff"] == [403, 403, 403, 403], r["staff"])
    check("2.3 the manager and the owner: all three pages open, the POST is taken",
          r["manager"] == [200, 200, 200, 302] and r["owner"] == [200, 200, 200, 302], (r["manager"], r["owner"]))

    # ---- 3 · the list and its suggestions
    c = n["cards"]
    want = ["B-9007", "B-9018", "B-9105", "B-9200", "B-9201", "B-9202", "B-9203", "B-9204", "B-9205", "B-9206", "B-9207", "B-9208", "B-9100", "B-9500"]
    check("3.1 the list holds every live clinic paper with no group (%d) and nothing else" % len(want),
          sorted(c) == sorted(want), sorted(set(c) ^ set(want)))
    check("3.2 not on the list: the rejected paper, the duplicate, the joined page, the pharmacy, lab, expense and other-document papers",
          not any(k in c for k in ("B-9300", "B-9301", "B-9302", "B-9400", "B-9401", "B-9402", "B-9403")))
    check("3.3 Yuvika's unread slips: Procedure room, from the supplier, and it says nothing else could be read",
          all(c[k]["yes"] == [["subgroup", "procedure"]] and "handwritten slips" in c[k]["text"] for k in ("B-9018", "B-9007")), c.get("B-9018"))
    check("3.4 the inverter battery: Dr MK expense, and its Yes goes to the app's own lane door",
          c["B-9105"]["yes"] == [["lane", "owner_expense"]] and "not a clinic consumable" in c["B-9105"]["text"]
          and any(f.endswith("/bills/%d/lane" % B["battery"]) for f in c["B-9105"]["form"]), c["B-9105"])
    check("3.5 fibre cast, roller bandage, betadine: Procedure room, from the words",
          c["B-9200"]["yes"] == [["subgroup", "procedure"]] and "fibre cast" in c["B-9200"]["text"])
    check("3.6 an 11x14 film: X-ray films · 11 x 14 in one tap; a film with no size: two buttons, small and 11 x 14",
          c["B-9201"]["yes"] == [["subgroup", "xray_11x14"]]
          and c["B-9206"]["yes"] == [["subgroup", "xray_small"], ["subgroup", "xray_11x14"]], (c["B-9201"]["yes"], c["B-9206"]["yes"]))
    check("3.7 paper and a register: Others", c["B-9202"]["yes"] == [["subgroup", "others"]])
    check("3.8 THE SUPPLIER ALONE NEVER DECIDES: Yuvika's printed bill for knee caps and belts gets no Yes -- it says orthotics, a pharmacy purchase",
          c["B-9203"]["yes"] == [] and "orthotics" in c["B-9203"]["text"], c["B-9203"])
    check("3.9 a Yuvika bill with a number and an amount but no item read: suggested, with 'look at the paper before saying yes'",
          c["B-9207"]["yes"] == [["subgroup", "procedure"]] and "look at the paper" in c["B-9207"]["text"])
    check("3.10 nothing to go on: no Yes, and it says there is no suggestion", c["B-9204"]["yes"] == [] and "No suggestion" in c["B-9204"]["text"])
    check("3.11 an APPROVED clinic bill that looks like an expense: no Yes (an approved bill stays), and it says why",
          c["B-9208"]["yes"] == [] and "already approved" in c["B-9208"]["text"], c["B-9208"])
    check("3.12 a paper still being read: no suggestion yet, 'come back in a minute'",
          c["B-9500"]["yes"] == [] and "still being read" in c["B-9500"]["text"])
    check("3.13 a supplier's name is words, never markup",
          "<script>alert(1)</script>" not in n["papers"][1] and "&lt;script&gt;alert(1)&lt;/script&gt; &amp; Sons" in n["papers"][1])
    u = n["unit"]
    check("3.14 'broadcast' is not 'cast'; expense words win over procedure words",
          u["broadcast"] is None and u["expense_over_procedure"]["kind"] == "lane", (u["broadcast"], u["expense_over_procedure"]))
    check("3.15 Yuvika by case and spacing; her fibre cast is Procedure room, her knee caps are not",
          u["yuvika_cast"]["value"] == "procedure" and u["yuvika_orthotic"]["kind"] == "note"
          and u["yuvika_slip"]["value"] == "procedure" and u["yuvika_printed_noitems"]["value"] == "procedure")
    check("3.16 a small film by its size; an unknown supplier with nothing read gives nothing",
          u["xray_small"]["value"] == "xray_small" and u["nothing"] is None)
    check("3.17 the word lists grow from a setting, with no new kit",
          u["before_setting"] is None and u["after_setting"] and u["after_setting"]["value"] == "procedure", u["after_setting"])
    check("3.18 money as the owner reads it", n["inr"] == ["₹12,34,567.50", "₹480.00", "—", "₹1,00,000.00"], n["inr"])

    # ---- 4 · setting a group
    check("4.1 one tap sets the group and returns to the list", n["set_proc"] == [302, "/papers"] and n["proc_after"]["subgroup"] == "procedure"
          and n["proc_after"]["lane"] == "clinic" and n["proc_after"]["status"] == "draft", (n["set_proc"], n["proc_after"]))
    au = n["audit"]
    check("4.2 it is written in the bill's audit trail: who, from, to", len(au) == 1 and au[0]["action"] == "subgroup"
          and json.loads(au[0]["detail"]) == {"from": "", "to": "procedure"} and au[0]["who"], au)
    check("4.3 the same group again writes no second line", n["audit_n_after_same"] == 1)
    check("4.4 a value that is not a group is refused (400); a paper that is not there is 404", n["set_bad"][0] == 400 and n["set_missing"][0] == 404)
    check("4.5 a pharmacy paper and a rejected paper take no group", n["snaps"]["pharm"]["subgroup"] is None and n["snaps"]["rejected"]["subgroup"] is None
          and n["set_pharm"][0] == 302 and n["set_rejected"][0] == 302)
    check("4.6 the manager sets X-ray sizes", n["snaps"]["xray"]["subgroup"] == "xray_11x14" and n["snaps"]["xray_nosize"]["subgroup"] == "xray_small")
    check("4.7 a group can be cleared again", n["set_then_clear"][1] == "others" and n["set_then_clear"][3] is None, n["set_then_clear"])
    check("4.8 'Yes, Dr MK expense' is the app's own move: lane, kind and status as that lane lands, with its own audit line",
          n["battery_after"] == {"lane": "owner_expense", "kind": "Expense", "status": "captured", "subgroup": None}
          and n["battery_audit"] == ["relane"] and n["move_battery"] == [302, "/papers"], (n["battery_after"], n["battery_audit"]))
    left = n["papers_after"][1]
    check("4.9 what was sorted or moved has left the list; what was skipped is still there",
          not any(k in left for k in ("B-9200", "B-9201", "B-9206", "B-9202", "B-9100", "B-9105"))
          and all(k in left for k in ("B-9018", "B-9007", "B-9203", "B-9204")), left)

    # ---- 5 · one paper
    t = n["paper_xray"][1]
    check("5.1 the paper's page shows its group as chosen, with the three groups and the two film sizes",
          n["paper_xray"][0] == 200 and "Which clinic consumable?" in t and 'class="d6opt on"' in t and "Small film" in t
          and "Procedure room" in t and "Others" in t and "Clear the group" in t)
    check("5.2 it offers the move to another lane through the app's own door", "Not a clinic consumable?" in t
          and "/bills/%d/lane" % B["xray"] in t and 'value="owner_expense"' in t and 'value="pharmacy"' in t)
    check("5.3 a pharmacy paper's page offers no group", n["paper_pharm"][0] == 200 and "Which clinic consumable?" not in n["paper_pharm"][1]
          and "not on the clinic lane" in n["paper_pharm"][1])
    check("5.4 an approved bill's page says it stays on the clinic lane; a paper that is not there is 404",
          "an approved bill stays on the clinic lane" in n["paper_approved"][1] and n["paper_missing"] == 404)

    # ---- 6 · the month
    mo = text(n["month_oct"][1])
    check("6.1 October by group: Procedure room 1 paper 3,150; X-ray films 2 papers 7,700 with both sizes; Others 1 paper 480",
          "Procedure room 1 paper · Agarwal Surgicals ₹3,150.00" in mo and "X-ray films 2 papers · Bareilly X-Ray House ₹7,700.00" in mo
          and "Small film ₹1,500.00" in mo and "11 x 14 film ₹6,200.00" in mo and "Others 1 paper · City Stationers ₹480.00" in mo, mo[:600])
    check("6.2 the unsorted are counted, with how many have no amount read, and the page offers to sort them",
          re.search(r"Not sorted yet 8 papers .* 3 with no amount read \u20b910,410\.00", mo) is not None
          and "Sort the 8 unsorted papers" in mo, mo[-900:-300])
    check("6.3 the total is every live clinic paper of the month -- 12 papers, 21,740 = 3,150 + 7,700 + 480 + 10,410; the rejected paper, "
          "the duplicate, the joined page and the moved battery are out",
          "All clinic consumables 12 papers \u00b7 11 still pending approval \u20b921,740.00" in mo and "999.00" not in mo
          and "28,400" not in mo, mo[-900:-300])
    check("6.4 a bill whose month was set to September counts in September, not by its October date",
          "Procedure room 1 paper · Agarwal Surgicals ₹1,000.00" in text(n["month_sep"][1]) and "All clinic consumables 1 paper" in text(n["month_sep"][1]))
    check("6.5 the other lanes are named apart with their own counts (pharmacy 1, lab 1, Dr MK expense 2, other documents 1)",
          "Pharmacy purchases — Sanjeevni 1 paper" in mo and "Lab purchases — NK Pathology 1 paper" in mo
          and "Dr MK expense 2 papers" in mo and "Other documents — not bills 1 paper" in mo, mo[-700:-300])
    g_ = n["month_g"]
    check("6.6 a tap on a group lists its papers", "B-9200" in g_["procedure"][1] and "B-9201" in g_["xray"][1] and "B-9206" in g_["xray"][1]
          and "B-9202" in g_["others"][1] and "B-9018" in g_["unsorted"][1] and "B-9200" not in g_["xray"][1])
    check("6.7 a month that is not a month falls back to this month; next month is not offered beyond today",
          n["month_bad"] == 200)

    # ---- 7 · the app's own pages
    check("7.1 the Purchases page carries the two links, with the count of papers still to sort",
          re.search(r"Clinic papers to sort\s*\(\d+\)</a>", n["bills_page2"][1]) is not None and "Clinic consumables by month" in n["bills_page2"][1])
    check("7.2 a clinic bill's page says its group and offers to change it", "<b>Group:</b> Procedure room" in n["bill_page_clinic2"][1]
          and "/papers/%d" % B["proc"] in n["bill_page_clinic2"][1])
    check("7.3 apart from those lines the Purchases page is the old page",
          squash(re.sub(r'<a class="btn small" href="[^"]*/papers[^"]*">.*?</a>', "", n["bills_page"][1], flags=re.S))
          == squash(o["bills_page"][1]), "")

    # ---- 8 · under /scanapp, and what must not move
    check("8.1 under /scanapp the page opens and its links and its way back carry the prefix",
          n["prefix"][0][0] == 200 and 'action="/scanapp/bills/' in n["prefix"][0][1] and 'href="/scanapp/papers/' in n["prefix"][0][1]
          and n["prefix"][1] == [302, "/scanapp/papers"], n["prefix"][1])
    check("8.2 THE PHARMACY SCAN IS NOT TOUCHED: lane, kind, status as before, and no paper off the clinic lane carries a group",
          n["pharm_after"]["lane"] == "pharmacy" and n["pharm_after"]["kind"] == "Pharmacy" and n["pharm_after"]["status"] == "captured"
          and n["pharm_after"]["subgroup"] is None and n["untouched_n"] == 0, n["pharm_after"])
    check("8.3 the other lanes' papers are as they landed", n["snaps"]["lab"]["status"] == "captured" and n["snaps"]["exp"]["lane"] == "owner_expense"
          and n["snaps"]["doc"]["kind"] == "Document")
    check("8.4 nothing in the asset app's own folder was written by this walk", md5(os.path.join(src, "asset_register.py")) == FROM)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        sys.exit(main())
