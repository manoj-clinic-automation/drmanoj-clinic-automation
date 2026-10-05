#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s483.py -- kit S483_SPINE_READS_TEXT: the walk (the brief's section 2). Every section has a negative control on the OLD file.

  python -B walk_s483.py manojz ...   sections 1 and 2 -- on Dr Manoj's PC against MargArchive: the two sheets that froze the spine,
                                      and EVERY sheet the two mended functions can read (purchase lines, salt and category lists).
                                      The sale sheets are not opened. Verdicts and counts only; nothing leaves the PC.
  python -B walk_s483.py server ...   sections 3 and 4 (and the tile's own certificate) -- on the server, on scratch copies: the gate
                                      (spine_build.py on a copy of the readings store), every kept reading re-read, the reader's
                                      source compared function by function. Run by the installer before anything is placed.

Nothing is imported from inside deploy_kits (CLAUDE.md rule 11): the readers are loaded from the copies the caller names.
"""
import argparse
import ast
import datetime as dt
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

DE = "de92f5d5185646d4de563e30d5464f6e"          # the BILL/ITEM WISE purchase sheet the text cutter made (F-734)
F6 = "f62cc9e3d93c692f1795229be9e7cfe1"          # the whole-shop category list (F-735)
G_PUR = "every purchase line of an export that is the authority for its whole period belongs to exactly one bill"
G_SALE = "every sale export passes its own witness"
G_CAT = "every CATEGORY_WISE_ITEM_LIST export passes its own witness"
EDITED = ("read_purchase_lines", "read_grouped_list")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + re.sub(r"\d{10,}", "##########", str(got))[:600] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def core(rec):
    """What must not move in a reading: its family, its verdict, its data (as JSON holds them)."""
    return json.loads(json.dumps(dict(family=rec.get("family"), ok=rec.get("ok"), data=rec.get("data") or {})))


# ---- invented rows (no sheet line): the two rules and their limits ----------------------------------------------------------------------
def pur_rows(date_rows):
    head = ["BILL", "ITEM DESCRIPTION", "PACK", "BATCH", "EXP", "QTY", "FREE", "RATE", "DIS", "NET AMT", "LOOSE", "AMOUNT"]
    item = lambda bill, name: [bill, name, "1*10 W483B", "", "", "2.0", "", "50.00", "", "100.00 50.00", "0 55.00", "100.00"]
    rows = [["BILL/ITEM WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030"] + [""] * 11, head]
    for k, dr in enumerate(date_rows):
        rows += [dr, item(str(101 + k), "W483 ITEM %d" % (k + 1))]
    rows.append(["TOTAL"] + [""] * 8 + ["%d.00" % (100 * len(date_rows)), "", "%d.00" % (100 * len(date_rows))])
    return rows


def cat_rows(heading):
    return [["W483 GROUP A", "0.0", "", "", ""], ["1  W483 ITEM ONE", "1*10", "10.0", "12.0", "15.0"],
            heading, ["1  W483 ITEM TWO", "1*10", "10.0", "12.0", "15.0"], ["2  W483 ITEM THREE", "1*10", "10.0", "12.0", "15.0"]]


def rules_on_invented_rows(OLD, NEW):
    def d(col, also=None):
        """A row of twelve cells with the date in `col` -- and, when asked, a second non-empty cell."""
        r = [""] * 12
        r[col] = "01-01-2030"
        if also is not None:
            r[also] = "W483"
        return r
    ro = OLD.read_purchase_lines(pur_rows([d(1), d(3), d(0)]))
    rn = NEW.read_purchase_lines(pur_rows([d(1), d(3), d(0)]))
    check("E.1 on invented rows: a date-only row is a DATE wherever its one cell sits -- column 1, column 3, column 0: NEW dates all three "
          "lines; OLD dates only the line under the column-0 date",
          [bool(l["date"]) for l in rn.data["lines"]] == [True, True, True] and rn.classes["DATE"] == 3 and rn.ok
          and [bool(l["date"]) for l in ro.data["lines"]] == [False, False, True] and ro.classes["DATE"] == 1,
          ([l["date"] for l in rn.data["lines"]], [l["date"] for l in ro.data["lines"]]))
    two = NEW.read_purchase_lines(pur_rows([d(1, 2)]))
    two_o = OLD.read_purchase_lines(pur_rows([d(1, 2)]))
    check("negative control: a date cell with a second non-empty cell in its row is still NOT a DATE under NEW (the line stays undated, "
          "as under OLD)", two.classes["DATE"] == 0 and [l["date"] for l in two.data["lines"]] == [""]
          and dict(two.classes) == dict(two_o.classes) and two.data == two_o.data, dict(two.classes))
    T = r'CATEGORY\s+WISE\s+ITEM\s+LIST'
    hn = NEW.read_grouped_list(cat_rows(["OTHERS", "0.0", "D98", "", ""]), "CATEGORY_WISE_ITEM_LIST", T)
    ho = OLD.read_grouped_list(cat_rows(["OTHERS", "0.0", "D98", "", ""]), "CATEGORY_WISE_ITEM_LIST", T)
    check("E.2 on invented rows: 'OTHERS | 0.0 | D98' is a HEADING under NEW (ok, two groups, data['code'] = {'OTHERS': 'D98'}); under OLD it "
          "is UNCLASSIFIED and the next serial breaks", hn.ok and hn.classes["HEADING"] == 2 and hn.data.get("code") == {"OTHERS": "D98"}
          and [i["group"] for i in hn.data["items"]] == ["W483 GROUP A", "OTHERS", "OTHERS"]
          and (not ho.ok) and ho.classes["ANOMALY"] == 1 and "code" not in ho.data, (hn.failed(), ho.failed()))
    plain = NEW.read_grouped_list(cat_rows(["W483 GROUP B", "0.0", "", "", ""]), "CATEGORY_WISE_ITEM_LIST", T)
    plain_o = OLD.read_grouped_list(cat_rows(["W483 GROUP B", "0.0", "", "", ""]), "CATEGORY_WISE_ITEM_LIST", T)
    check("a heading with no code reads exactly as before: the same data, key for key (no 'code' key appears)",
          plain.ok and plain.data == plain_o.data and list(plain.data.keys()) == ["items"] and plain.checks == plain_o.checks)
    bad = {}
    for why, row in (("two codes", ["OTHERS", "0.0", "D98", "X1", ""]), ("a rate", ["OTHERS", "0.0", "12.5", "", ""]),
                     ("a packing", ["OTHERS", "1*10", "", "", ""]), ("seven characters", ["OTHERS", "0.0", "TOOLONG", "", ""]),
                     ("a space", ["OTHERS", "0.0", "D 98", "", ""]), ("a bare number", ["OTHERS", "0.0", "98", "", ""])):
        r = NEW.read_grouped_list(cat_rows(row), "CATEGORY_WISE_ITEM_LIST", T)
        o = OLD.read_grouped_list(cat_rows(row), "CATEGORY_WISE_ITEM_LIST", T)
        bad[why] = (not r.ok) and r.classes["ANOMALY"] == 1 and r.failed() == o.failed() and "code" not in r.data
    check("negative controls: a row with two codes, with a rate, with a packing, with a 7-character word, with a space in it, or with a bare "
          "number beside the name is still UNCLASSIFIED under NEW, exactly as under OLD", all(bad.values()), bad)


# ============================================================================================================================ manojz
def manojz(a):
    W = os.path.abspath(a.work)
    os.makedirs(W)
    sys.path.insert(0, a.pull)                                          # the vendored xlrd beside the pull
    R = {}
    for side, p in (("old", a.old_read), ("new", a.new_read)):
        shutil.copy(p, os.path.join(W, "marg_read_%s.py" % side))
        R[side] = load("marg_read_" + side, os.path.join(W, "marg_read_%s.py" % side))
    OLD, NEW = R["old"], R["new"]

    def sheets(folder):
        return sorted(p for p in glob.glob(os.path.join(a.archive, folder, "*", "*")) if p.lower().endswith((".xls", ".xlsx")))

    def one(folder, m8):
        hit = [p for p in sheets(folder) if os.path.splitext(p)[0].endswith("__" + m8)]
        return hit[0] if hit else None
    print("-- 1  read_purchase_lines (E.1, F-734) on MargArchive -- verdicts and counts only")
    p = one("PURCHASE_BILLITEMWISE", DE[:8])
    if not check("the text-made BILL/ITEM WISE sheet %s is in MargArchive, and its md5 is the reading's name" % DE[:8], bool(p) and md5f(p) == DE):
        return finish("manojz")
    o, n = OLD.reading_record(p), NEW.reading_record(p)
    lo, ln = o["data"]["lines"], n["data"]["lines"]
    check("OLD (099d6213): dates on lines: %d of %d -- its %d date rows are read as supplier headings" % (
        sum(1 for l in lo if l["date"]), len(lo), o["classes"].get("SUPPLIER_HEADING", 0)),
        len(lo) == 208 and not any(l["date"] for l in lo) and o["classes"].get("DATE", 0) == 0 and o["classes"].get("SUPPLIER_HEADING", 0) == 27)
    days = sorted({l["date"] for l in ln})
    check("NEW: dates on lines: %d of %d, every one inside %s .. %s (%d days, %s .. %s); ok %s; %d DATE rows, no supplier heading"
          % (sum(1 for l in ln if l["date"]), len(ln), n["data"]["date_from"], n["data"]["date_to"], len(days), days[0], days[-1], n["ok"],
             n["classes"].get("DATE", 0)),
          len(ln) == 208 and all(l["date"] and "2026-09-01" <= l["date"] <= "2026-10-03" for l in ln) and n["ok"] is True
          and (n["data"]["date_from"], n["data"]["date_to"]) == ("2026-09-01", "2026-10-03") and n["classes"].get("DATE") == 27
          and "SUPPLIER_HEADING" not in n["classes"])
    check("nothing else of that sheet moved: the same 208 lines, field for field, but for `date`; the same five checks",
          [dict(l, date="") for l in ln] == [dict(l, date="") for l in lo] and n["checks"] == o["checks"])
    p6 = one("PURCHASE_BILLITEMWISE", "7aab826f")
    o6, n6 = (OLD.reading_record(p6), NEW.reading_record(p6)) if p6 else ({}, None)
    check("Marg's own Excel BILL/ITEM WISE of 06-Sep (7aab826f; the day in column 0): OLD = NEW, the same reading (%s lines, all dated)"
          % (len(o6["data"]["lines"]) if p6 else "?"), bool(p6) and o6 == n6 and all(l["date"] for l in o6["data"]["lines"]))
    same, diff = 0, []
    pl = sheets("PURCHASE_ITEMWISE") + sheets("PURCHASE_BILLITEMWISE")
    for q in pl:
        if md5f(q) == DE:
            continue
        if OLD.reading_record(q) == NEW.reading_record(q):
            same += 1
        else:
            diff.append(os.path.basename(q)[-30:])
    ns = len(sheets("PURCHASE_ITEMWISE"))
    check("every other purchase-lines sheet in the archive -- %d SUPPLIER/ITEM WISE (no date rows) and %d BILL/ITEM WISE: OLD = NEW, "
          "reading for reading" % (ns, len(pl) - ns - 1), same == len(pl) - 1 and not diff and ns >= 20, diff[:4])
    print("-- 2  read_grouped_list (E.2, F-735) on MargArchive")
    p = one("CATEGORY_WISE_ITEM_LIST", F6[:8])
    if not check("the whole-shop category list %s is in MargArchive, and its md5 is the reading's name" % F6[:8], bool(p) and md5f(p) == F6):
        return finish("manojz")
    o, n = OLD.reading_record(p), NEW.reading_record(p)
    check("OLD: ok False -- %s" % o["failed"], o["ok"] is False
          and o["failed"] == ["serial restarts at 1 under every heading and never skips", "UNCLASSIFIED at row 148", "SERIAL at row 149"])
    grp = {}
    for i in n["data"]["items"]:
        grp[i["group"]] = grp.get(i["group"], 0) + 1
    check("NEW: ok True, nothing failed; the group OTHERS with code D98 (data['code'] = %s); %d items read under %d headings %s; serials "
          "clean under every heading" % (n["data"].get("code"), len(n["data"]["items"]), len(grp), grp),
          n["ok"] is True and n["failed"] == [] and n["data"].get("code") == {"OTHERS": "D98"} and len(n["data"]["items"]) == 341
          and grp.get("OTHERS", 0) > 0 and n["classes"].get("HEADING") == 4 and "ANOMALY" not in n["classes"])
    io_, in_ = o["data"]["items"], n["data"]["items"]
    moved = [k for k in range(len(io_)) if io_[k] != in_[k]]
    check("nothing else of that list moved: the same 341 items in the same order; only `group` differs, and only on the %d items after the "
          "OTHERS row (they were filed under the heading before it)" % len(moved),
          len(io_) == len(in_) and all(dict(io_[k], group="") == dict(in_[k], group="") for k in range(len(io_)))
          and len(moved) == grp.get("OTHERS", -1) and all(in_[k]["group"] == "OTHERS" for k in moved))
    same, diff = 0, []
    gl = sheets("CATEGORY_WISE_ITEM_LIST") + sheets("SALT_WISE_ITEM_LIST")
    for q in gl:
        if md5f(q) == F6:
            continue
        ro_, rn_ = OLD.reading_record(q), NEW.reading_record(q)
        if ro_ == rn_ and "code" not in rn_["data"]:
            same += 1
        else:
            diff.append(os.path.basename(q)[-30:])
    names = " ".join(os.path.basename(q) for q in gl)
    check("every other grouped list in the archive -- the two orthotics-only category lists of 18-Sep (f4a3406e, fe483146) and %d salt lists "
          "(235e9643 among them): OLD = NEW, reading for reading" % len(sheets("SALT_WISE_ITEM_LIST")),
          same == len(gl) - 1 and not diff and all(x in names for x in ("f4a3406e", "fe483146", "235e9643")), diff[:4])
    print("-- the two rules on invented rows")
    rules_on_invented_rows(OLD, NEW)
    return finish("manojz")


# ============================================================================================================================ server
def functions(path):
    """{name: source} of every top-level statement of the reader (a def / class by its name; anything else by its own text)."""
    src = open(path, encoding="utf-8").read()
    out = {}
    for node in ast.parse(src).body:
        seg = ast.get_source_segment(src, node)
        out[getattr(node, "name", None) or ("stmt:" + seg[:60])] = seg
    return out


def spine_build(spine_dir, readings, out_db, fin_db):
    p = subprocess.run([sys.executable, "-B", os.path.join(spine_dir, "spine_build.py"), "--readings", readings, "--out", out_db, "--finance-db", fin_db],
                       cwd=spine_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=1500)
    rows, detail = {}, {}
    for l in p.stdout.splitlines():
        m = re.match(r"^  (ok|FAIL|note)\s+(.*?)(  -- .*)?$", l)
        if m:
            rows[m.group(2).strip()] = m.group(1)
            detail[m.group(2).strip()] = (m.group(3) or "")[5:]
    state = {}
    try:
        state = json.load(open(os.path.join(os.path.dirname(out_db), "spine_state.json")))
    except (OSError, ValueError):
        pass
    return dict(rc=p.returncode, rows=rows, detail=detail, fails=sorted(k for k, v in rows.items() if v == "FAIL"), swapped="SPINE BUILT AND SWAPPED" in p.stdout,
                gate_failed="GATE FAILED" in p.stdout, state=state, tail=p.stdout.splitlines()[-1] if p.stdout else "")


def probe_tile():
    """The tile's own certificate of the two KEPT files when the store has no reading for them -- with the reader of SPINE_DIR."""
    sys.path.insert(0, os.environ["FINDIR"])
    os.chdir(os.environ["FINDIR"])
    import reports_tile as RT                                           # noqa: E402  (the live module, read only; nothing is written)
    out = {}
    for m, name in json.loads(os.environ["W483J"]):
        c = RT.certify(m, name, "")
        out[m[:8]] = c and dict(ok=c["ok"], failed=c["failed"], count=c["count"], source=c["source"])
    out["reader"] = sys.modules["marg_read"].__file__
    print("W483JSON " + json.dumps(out))


def server(a):
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/"), "refusing a non-scratch path: %s" % W
    os.makedirs(W)
    sys.path.insert(0, a.ingest)                                        # the vendored xlrd beside the collector
    OLD = load("marg_read_old", os.path.join(a.spine_old, "marg_read.py"))
    NEW = load("marg_read_new", os.path.join(a.spine_new, "marg_read.py"))
    live_db = os.path.join(a.readings, "..", "spine.db")
    db0 = (md5f(live_db), os.path.getmtime(live_db)) if os.path.exists(live_db) else None
    store0 = {fn: md5f(os.path.join(a.readings, fn)) for fn in sorted(os.listdir(a.readings)) if fn.endswith(".json")}
    kept = {}
    for dp, _dn, fn in os.walk(a.archive):
        for f in fn:
            if f.lower().endswith((".xls", ".xlsx")):
                kept.setdefault(md5f(os.path.join(dp, f)), os.path.join(dp, f))
    stored = {fn[:-5]: json.load(open(os.path.join(a.readings, fn))) for fn in store0}
    if not check("the two readings are in the store, and the server keeps both sheets (purchases and lists carry no person's detail)",
                 DE in stored and F6 in stored and DE in kept and F6 in kept):
        return finish("server")

    print("-- 3  the gate: spine_build.py on scratch copies of the readings store (the live spine.db is never the --out)")
    s_old, s_new = os.path.join(W, "store_old"), os.path.join(W, "store_new")
    for s in (s_old, s_new):
        os.makedirs(s)
        for fn in store0:
            shutil.copy(os.path.join(a.readings, fn), os.path.join(s, fn))
    rew = {}
    for m in (DE, F6):
        rec = NEW.reading_record(kept[m], stored[m]["name"])            # as spine_evidence.py writes a reading
        rec["folder"] = stored[m].get("folder", "")
        rec["read_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(s_new, m + ".json"), "w") as fh:
            json.dump(rec, fh)
        rew[m] = rec
    for side in ("old", "new"):
        os.makedirs(os.path.join(W, "build_" + side))
    bo = spine_build(a.spine_old, s_old, os.path.join(W, "build_old", "spine.db"), a.db)
    check("negative control, the store as it is: GATE FAILED (exit 3) on exactly the two lines of this morning -- the purchase lines and "
          "the category list; nothing swapped", bo["rc"] == 3 and bo["gate_failed"] and bo["fails"] == sorted([G_PUR, G_CAT])
          and not os.path.exists(os.path.join(W, "build_old", "spine.db")) and bo["state"].get("passed") is False, (bo["rc"], bo["fails"], bo["tail"]))
    bn = spine_build(a.spine_new, s_new, os.path.join(W, "build_new", "spine.db"), a.db)
    n_old = (re.match(r"^(\d+) lines", bo["detail"].get(G_PUR, "")) or [None, "?"])[1]
    n_new = (re.match(r"^(\d+) lines", bn["detail"].get(G_PUR, "")) or [None, "0"])[1]
    bills = sorted(set(re.findall(r"\.XLS', '([^']*)', '", bn["detail"].get(G_PUR, "").split(" | ")[0])))
    check("with the two readings rewritten by the NEW reader: the category-list line passes, and the sale-exports line (mended by S482) passes",
          bn["rows"].get(G_CAT) == "ok" and bn["rows"].get(G_SALE) == "ok", [bn["rows"].get(g) for g in (G_SALE, G_CAT)])
    check("the purchase-lines line passes -- it failed on %s lines with the old reading; with the new one it %s"
          % (n_old, "passes" if bn["rows"].get(G_PUR) == "ok" else "STILL FAILS, on %s lines, bill number(s) %s" % (n_new, bills)),
          bn["rows"].get(G_PUR) == "ok", bn["detail"].get(G_PUR, "")[:330])
    check("the gate PASSES (%s, exit 0) and the build swaps ON THE SCRATCH COPY -- '%s'" % (bn["state"].get("gate"), bn["tail"][:40]),
          bn["rc"] == 0 and bn["swapped"] and not bn["fails"] and os.path.exists(os.path.join(W, "build_new", "spine.db"))
          and bn["state"].get("passed") is True, (bn["rc"], bn["fails"], bn["tail"][:60]))
    check("every other gate line reads the same in both builds (%d lines)" % len(bn["rows"]),
          set(bn["rows"]) == set(bo["rows"]) and all(bn["rows"][k] == bo["rows"][k] for k in bn["rows"] if k not in (G_PUR, G_CAT)),
          [k for k in bn["rows"] if k not in (G_PUR, G_CAT) and bn["rows"][k] != bo["rows"].get(k)])

    print("-- 4  every reading in the store, re-read by the NEW reader from the sheet the server keeps")
    changed, same, nofam, away = [], 0, 0, {}
    for m, st in sorted(stored.items()):
        if not st.get("family"):
            nofam += 1
            continue
        if m not in kept:
            away.setdefault(st["family"], []).append(m[:8])
            continue
        if core(NEW.reading_record(kept[m], st["name"])) == core(st):
            same += 1
        else:
            changed.append(m)
    check("%d readings re-read from their kept sheets: %d give the same family, the same ok and the same data as the stored one; the ONLY "
          "two that differ are the two mended sheets (%s, %s)" % (same + len(changed), same, DE[:8], F6[:8]),
          sorted(changed) == sorted([DE, F6]) and same > 100, [c[:8] for c in changed])
    so, sn = stored[DE], rew[DE]
    check("   %s: ok %s -> %s; its lines dated %d of %d -> %d of %d; nothing else of it moved (the lines are equal field for field but for `date`)"
          % (DE[:8], so["ok"], sn["ok"], sum(1 for l in so["data"]["lines"] if l["date"]), len(so["data"]["lines"]),
             sum(1 for l in sn["data"]["lines"] if l["date"]), len(sn["data"]["lines"])),
          so["ok"] is True and sn["ok"] is True and not any(l["date"] for l in so["data"]["lines"]) and all(l["date"] for l in sn["data"]["lines"])
          and [dict(l, date="") for l in so["data"]["lines"]] == [dict(l, date="") for l in json.loads(json.dumps(sn["data"]["lines"]))]
          and {k: v for k, v in so["data"].items() if k != "lines"} == {k: v for k, v in sn["data"].items() if k != "lines"})
    so, sn = stored[F6], json.loads(json.dumps(rew[F6]))
    check("   %s: ok %s -> %s (failed %s -> %s); %d items both; data['code'] %s; only `group` moved, on the items after the OTHERS row"
          % (F6[:8], so["ok"], sn["ok"], len(so["failed"]), sn["failed"], len(sn["data"]["items"]), sn["data"].get("code")),
          so["ok"] is False and sn["ok"] is True and sn["failed"] == [] and sn["data"].get("code") == {"OTHERS": "D98"}
          and [dict(i, group="") for i in so["data"]["items"]] == [dict(i, group="") for i in sn["data"]["items"]]
          and all(j["group"] == "OTHERS" for i, j in zip(so["data"]["items"], sn["data"]["items"]) if i != j)
          and so["data"].get("as_on") == sn["data"].get("as_on"))
    fo, fn_ = functions(os.path.join(a.spine_old, "marg_read.py")), functions(os.path.join(a.spine_new, "marg_read.py"))
    moved = sorted(k for k in set(fo) | set(fn_) if fo.get(k) != fn_.get(k))
    check("the reader's source, statement by statement (%d top-level statements): only %s differ -- every other function, the sale reader "
          "and the file door among them, is the same text" % (len(fn_), " and ".join(EDITED)), moved == sorted(EDITED) and list(fo) == list(fn_), moved)
    cat_away = sorted(away.get("CATEGORY_WISE_ITEM_LIST", []))
    check("the readings NOT re-read here, counted: %d of sale sheets (never at rest on the server, S186 -- read_sale_detail is the same text, "
          "so they cannot move); %d category lists the server does not keep (%s -- both read on manojz by this walk: OLD = NEW); %d that the "
          "spine does not use (no family -- identify() is the same text)"
          % (len(away.get("SALE_BILLWISE", [])), len(cat_away), ", ".join(cat_away), nofam),
          set(away) <= {"SALE_BILLWISE", "CATEGORY_WISE_ITEM_LIST"} and cat_away == ["f4a3406e", "fe483146"]
          and same + len(changed) + nofam + sum(len(v) for v in away.values()) == len(stored), {k: len(v) for k, v in away.items()})

    print("-- the tile's own certificate of the two kept sheets while the store has no reading for them (why clinic-finance restarts)")
    empty = os.path.join(W, "no_readings")
    os.makedirs(empty)
    T = {}
    for side, sp in (("old", a.spine_old), ("new", a.spine_new)):
        env = dict(os.environ, FINDIR=a.fin, SPINE_DIR=sp, SPINE_READINGS=empty, MI_ARCHIVE=a.archive,
                   W483J=json.dumps([(m, os.path.basename(kept[m])) for m in (DE, F6)]))
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-tile"], env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
        js = [l for l in p.stdout.splitlines() if l.startswith("W483JSON ")]
        T[side] = json.loads(js[-1][9:]) if js else {"error": p.stdout[-300:]}
    tn, to = T["new"], T["old"]
    check("reports_tile.certify, the reader of the scratch spine folder: NEW -- the category list ok (%s), the purchase sheet ok (%s); OLD -- "
          "the category list NOT ok (%s)" % ((tn.get(F6[:8]) or {}).get("count"), (tn.get(DE[:8]) or {}).get("count"), (to.get(F6[:8]) or {}).get("failed")),
          (tn.get(F6[:8]) or {}).get("ok") is True and (tn.get(DE[:8]) or {}).get("ok") is True and (to.get(F6[:8]) or {}).get("ok") is False
          and str(tn.get("reader", "")).startswith(a.spine_new) and str(to.get("reader", "")).startswith(a.spine_old), (tn, to))

    store1 = {fn: md5f(os.path.join(a.readings, fn)) for fn in sorted(os.listdir(a.readings)) if fn.endswith(".json")}
    db1 = (md5f(live_db), os.path.getmtime(live_db)) if os.path.exists(live_db) else None
    check("the walk wrote nothing live: the readings it read at its start are byte for byte as they were, and spine.db is the same file "
          "(md5 %s) unless the ten-minute job itself swapped it meanwhile" % (db0 and db0[0][:8]),
          all(store1.get(k) == v for k, v in store0.items()) and (db1 == db0 or (db1 and db0 and db1[1] > db0[1])))
    return finish("server")


def finish(where):
    if FAILS:
        print("WALK_S483 %s RED -- %d of %d checks failed:" % (where, len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + f[:200])
        return 1
    print("WALK_S483 %s GREEN -- %d checks" % (where, N[0]))
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe-tile":
        return probe_tile()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="where", required=True)
    m = sub.add_parser("manojz")
    for k in ("--work", "--archive", "--pull", "--old-read", "--new-read"):
        m.add_argument(k, required=True)
    s = sub.add_parser("server")
    for k in ("--work", "--spine-new", "--spine-old", "--readings", "--archive", "--ingest", "--fin", "--db"):
        s.add_argument(k, required=True)
    a = ap.parse_args()
    return manojz(a) if a.where == "manojz" else server(a)


if __name__ == "__main__":
    sys.exit(main() or 0)
