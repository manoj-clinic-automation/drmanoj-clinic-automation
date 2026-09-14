# -*- coding: utf-8 -*-
"""S263 LIVE-SHAPE WALK -- run against a COPY of the real database.

It loads BOTH files: the one being replaced and the patched one, each against
its own copy of the database, and proves that the only thing that changed is
the lane of the vendors the owner confirmed -- and that not one account number
moved anywhere.

    python3 walk_s263.py --file <patched purchase_app.py> --before <backup> --db <copy.db>
"""
import argparse
import importlib.machinery
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

OK = BAD = 0

# The owner's confirmations of 14-Sep-2026. The bill name on the left must end
# up on NEFT; nothing else may move.
EXPECT_LINKED = {
    "KEDAR PHARMACEUTICAL", "GUNINA PHARMACEUTICALS PVT LTD", "L.K. DRUG HOUSE",
    "SHRADDHA MEDICOSE", "YOGENDRA AGENCIES", "JUBILEE AGENCIES", "YUVIKA SURGICALS",
    "ESS KAY AGENCIES EXTN", "RADHA MEDICAL & SCIENTIFIC", "DRUG DEAL",
    "RAVI MEDICAL AGENCY", "SAISUN PHARMA PVT. LTD", "VERMA BROS. AND CO",
    "SCIENTIFIC&MEDICAL AID CENTRE",
}
# DAANSHI PHARMA is not linked to anything -- it has its own account, seeded on
# the install line. It counts as moved only when that account is actually there.
SEEDED = "DAANSHI PHARMA"
# and these stay on the cheque lane by his ruling
EXPECT_STAY = {"RAMA MEDICOSE", "AGARWAL SURGICALS AND MEDICALS"}


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("    ok    %s" % name)
    else:
        BAD += 1
        print("    FAIL  %s   %s" % (name, str(detail)[:260]))


def load(path, dbpath, name):
    # the file being replaced is a .bak_* -- name it explicitly, do not guess
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    import flask
    app = flask.Flask(name)
    holder = {}

    def db():
        if "con" not in holder:
            c = sqlite3.connect(dbpath)
            c.row_factory = sqlite3.Row
            holder["con"] = c
        return holder["con"]

    def require(*roles):
        return {"user": "walk", "role": "checker", "roles": ["checker"]}, None

    mod.init(app, db, require, unit="medical", url_prefix="/finance/purchase")
    return mod, app, db


def accounts(dbpath):
    c = sqlite3.connect(dbpath)
    return {r[0]: (r[1] or "", r[2] or "", r[3] or "") for r in c.execute(
        "SELECT vendor_norm, COALESCE(acct_no,''), COALESCE(ifsc,''), "
        "COALESCE(bank_status,'') FROM purchase_vendor_contact")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args(argv)

    tmp = tempfile.mkdtemp(prefix="s263_")
    db_before = os.path.join(tmp, "before.db")
    db_after = os.path.join(tmp, "after.db")
    db_probe = os.path.join(tmp, "probe.db")
    for d in (db_before, db_after, db_probe):
        shutil.copy(a.db, d)

    acct0 = accounts(db_before)
    # the seeded account is written BEFORE this walk runs, so the file being
    # replaced already sees it -- it must NOT show up as something the patch moved
    seeded = bool((acct0.get(SEEDED) or ("",))[0])
    expect_moved = set(EXPECT_LINKED)
    expect_stay = set(EXPECT_STAY) | (set() if seeded else {SEEDED})

    old, app0, dbf0 = load(a.before, db_before, "pa_before")
    new, app1, dbf1 = load(a.file, db_after, "pa_after")

    with app0.test_request_context("/"):
        before = old._vendor_bank(dbf0())
        months = old._months(dbf0(), 3)
    with app1.test_request_context("/"):
        after = new._vendor_bank(dbf1())

    ck("the database has months of purchases", bool(months), months)

    moved = {k for k in set(before) | set(after)
             if (after.get(k, {}).get("route") == "NEFT")
             and (before.get(k, {}).get("route") != "NEFT")}
    lost = {k for k in before
            if before[k].get("route") == "NEFT" and after.get(k, {}).get("route") != "NEFT"}
    ck("exactly the %d vendors he confirmed moved onto NEFT%s"
       % (len(expect_moved), "" if seeded else "  (DAANSHI PHARMA not seeded -- said out loud)"),
       moved == expect_moved, sorted(moved ^ expect_moved))
    ck("not one vendor LOST its NEFT lane", not lost, sorted(lost))
    ck("the vendors with no account of their own are still on cheques",
       all(after.get(k, {}).get("route", "CHEQUE") != "NEFT" for k in expect_stay),
       {k: after.get(k) for k in expect_stay})
    ck("each moved vendor SAYS whose account row it is using",
       all("on the register as" in (after[k]["why"] or "")
           for k in moved if k != SEEDED),
       [after[k]["why"] for k in sorted(moved)][:3])

    # ---- no account number was copied anywhere -----------------------------
    acct1 = accounts(db_after)
    changed = {k: (acct0.get(k), acct1.get(k)) for k in set(acct0) | set(acct1)
               if acct0.get(k) != acct1.get(k)}
    ck("NOT ONE account row was touched -- the link copies nothing",
       not changed, sorted(changed))
    ck("no linked vendor got a copy of somebody else's account number",
       all(not (acct1.get(k) or ("",))[0] for k in EXPECT_LINKED),
       [k for k in sorted(EXPECT_LINKED) if (acct1.get(k) or ("",))[0]])
    if seeded:
        d = acct1.get(SEEDED)
        ck("%s carries its own account, verified" % SEEDED,
           bool(d) and d[0] and d[2] == "VERIFIED", (d or ("", "", ""))[1:])
        ck("%s is on NEFT by its OWN account, not by a link" % SEEDED,
           before.get(SEEDED, {}).get("route") == "NEFT"
           and after.get(SEEDED, {}).get("route") == "NEFT"
           and "on the register as" not in (after[SEEDED]["why"] or ""),
           after.get(SEEDED))
    else:
        ck("%s has no account yet, so it stays on the cheque lane (said out loud)" % SEEDED,
           after.get(SEEDED, {}).get("route", "CHEQUE") != "NEFT", after.get(SEEDED))

    # ---- the link table -----------------------------------------------------
    con = sqlite3.connect(db_after)
    n = con.execute("SELECT COUNT(*) FROM purchase_vendor_alias").fetchone()[0]
    ck("the link table holds the 14 pairs", n == 14, n)
    with app1.test_request_context("/"):
        new._vendor_bank(dbf1())
        new._vendor_bank(dbf1())
    n2 = sqlite3.connect(db_after).execute(
        "SELECT COUNT(*) FROM purchase_vendor_alias").fetchone()[0]
    ck("running it again adds nothing (it is safe on every request)", n2 == 14, n2)

    # ---- a link cannot INVENT a lane ---------------------------------------
    probe, app2, dbf2 = load(a.file, db_probe, "pa_probe")
    with app2.test_request_context("/"):
        probe._vendor_bank(dbf2())
    cp = sqlite3.connect(db_probe)
    cp.execute("INSERT OR REPLACE INTO purchase_vendor_alias "
               "(bill_norm, register_norm, who, at) VALUES "
               "('ZZ TEST BILL NAME','RAMA MEDICOSE','walk','now')")
    cp.commit()
    with app2.test_request_context("/"):
        pb = probe._vendor_bank(dbf2())
    ck("a link to a row with NO confirmed account gives no NEFT lane",
       pb.get("ZZ TEST BILL NAME", {}).get("route", "CHEQUE") != "NEFT",
       pb.get("ZZ TEST BILL NAME"))

    # ---- the page itself, month by month -----------------------------------
    c1 = app1.test_client()
    for m in months:
        r = c1.get("/finance/purchase/page/pay/" + m)
        ck("%s: the page answers 200" % m, r.status_code == 200, r.status_code)
        h = r.get_data(as_text=True)
        with app1.test_request_context("/"):
            s, groups = new._pay_rows(dbf1(), m)
        ck("%s: the vendor lines still add up to Marg's own total" % m,
           sum(g["total_p"] for g in groups) == s["marg_p"],
           "%s vs %s" % (sum(g["total_p"] for g in groups), s["marg_p"]))
        cheq = sorted(g["norm"] for g in groups if g["route"] != "NEFT")
        ck("%s: the cheque lane is now %s" % (m, cheq or "empty"),
           all(x in expect_stay for x in cheq), cheq)
        ck("%s: every cheque vendor is still named on the page" % m,
           all(new._esc(g["name"]) in h for g in groups if g["route"] != "NEFT"))
    for page in ("hub", "month/" + months[0], "scans", "orders"):
        ck("the existing page /%s still renders" % page,
           c1.get("/finance/purchase/page/" + page).status_code == 200)

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
