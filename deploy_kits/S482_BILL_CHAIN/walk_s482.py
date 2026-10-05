#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s482.py -- kit S482_BILL_CHAIN: the walk (the brief's section 6). Every section has a negative control on the OLD file.

  python -B walk_s482.py server ...   sections 1, 2, 3, the collector half and the fixture half of 4, and the staff-eye walk (D648) --
                                      on the server, on scratch copies (finance.db by the backup API; its own rows, keyed W482 / w482;
                                      a walk-only login store and secret). Run by the installer before anything is placed.
  python -B walk_s482.py manojz ...   the reader half of 4 and section 5 -- on Dr Manoj's PC, against MargArchive (the real EMPTY sheet
                                      exists only there). The sheets are READ where they lie; nothing of them is printed (verdicts and
                                      counts only) and nothing leaves the PC. The outbox is exercised DRY on scratch copies of its state.

Nothing is imported from inside deploy_kits: every module is copied into the work folder first (CLAUDE.md rule 11). The bill numbers
of the fixtures are invented at run time (they continue the copy's own chain); no sheet line is in this file.
"""
import argparse
import datetime as dt
import hashlib
import html as _html
import importlib.util
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

TAG = "W482JSON "
USERS = {"darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor"}
NEW_DUTY = "shavez.bill_chain_gap"
FAR = dt.date(2031, 3, 3)                 # the walk's own rows live on days the copies hold nothing of
FIX_DAY = "2030-01-02"                    # the made-up sheets' day (S480's own samples)
HEADS = ["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT", "TAX", "DR/CR", "NET AMT.", "CASH"]
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:700] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def md5f(p):
    return md5b(open(p, "rb").read())


def load(name, path):
    """A module from a FILE, under its own name -- two versions of one module side by side."""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def steady(h):
    h = re.sub(r"\b\d{1,2}:\d\d(:\d\d)?\b", "HH:MM", h or "")
    return re.sub(r"\b[0-9a-f]{16,}\b", "HEX", h)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def at_rest(root, md5):
    hits = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if md5f(p) == md5:
                    hits.append(os.path.relpath(p, root))
            except OSError:
                pass
    return hits


def ddmon(iso):
    return "%s-%s" % (iso[8:10], MON[int(iso[5:7]) - 1])


def expand(words):
    """The chain's gap words -> every number they name, as text ('A003481..A003483' is three)."""
    out = []
    for w in words:
        if ".." in w:
            a, b = w.split("..", 1)
            pa, pb = re.match(r"^([A-Z]+)(\d+)$", a), re.match(r"^([A-Z]+)(\d+)$", b)
            out += ["%s%0*d" % (pa.group(1), len(pa.group(2)), n) for n in range(int(pa.group(2)), int(pb.group(2)) + 1)]
        else:
            out.append(w)
    return out


def card_texts(page):
    """The Hindi lines of the tile's gap card, and the page without the card."""
    m = re.search(r"<div class=card id=s482chain>((?:<div class=line><span class='big bad'>[^<]*</span></div>)+)</div>", page or "")
    if not m:
        return [], page or ""
    return [_html.unescape(t) for t in re.findall(r"<span class='big bad'>([^<]*)</span>", m.group(1))], page.replace(m.group(0), "")


# ---- the brief's wording (A.4), written out here a second time: the tile's own lines are compared with these ---------------------------
def want_hi(nos, a, b, via=(), inside=False):
    j = lambda p, w: p[0] if len(p) == 1 else ", ".join(p[:-1]) + " %s " % w + p[-1]
    names = j([x.replace("..", " se ") + (" tak" if ".." in x else "") for x in nos], "aur")
    verb = "nahi mila" if len(expand(nos)) == 1 else "nahi mile"
    if inside:
        return "Bill %s %s (%s ke andar) — %s ki bikri report dobara banaiye." % (names, verb, ddmon(a), ddmon(a))
    if via:
        return ("Bill %s %s (%s se %s ke beech, %s khali tha) — teen dinon ki bikri report dobara banaiye."
                % (names, verb, ddmon(a), ddmon(b), ddmon(via[0])))
    return "Bill %s %s (%s se %s ke beech) — %s aur %s ki bikri report dobara banaiye." % (names, verb, ddmon(a), ddmon(b), ddmon(a), ddmon(b))


def want_en(nos, a, b, via=(), inside=False):
    j = lambda p, w: p[0] if len(p) == 1 else ", ".join(p[:-1]) + " %s " % w + p[-1]
    names = j([x.replace("..", " to ") for x in nos], "and")
    if inside:
        return "Bill chain: %s missing inside %s — re-export that day." % (names, ddmon(a))
    if via:
        return "Bill chain: %s missing between %s and %s (%s was empty) — re-export all three days." % (names, ddmon(a), ddmon(b), ddmon(via[0]))
    return "Bill chain: %s missing between %s and %s — re-export both days." % (names, ddmon(a), ddmon(b))


# ============================================================================================================================ the probes
def far_days():
    d0 = FAR
    while d0.weekday() != 0:
        d0 += dt.timedelta(days=1)
    return [(d0 + dt.timedelta(days=k)).isoformat() for k in range(0, 16)]      # [0] a Monday ... [6] the Sunday ... [14] a Monday


def brute(con, from_day):
    """The chain a second way, straight from mi_sale_line: every number absent from its series, with the day of the nearest number
    below it and of the nearest number above it; and each series' highest bill with its day."""
    per, strs = {}, {}
    for day, bill in con.execute("SELECT DISTINCT bill_date, bill_no FROM mi_sale_line WHERE bill_date >= ?", (from_day,)):
        m = re.match(r"^([A-Z]{1,3})(\d+)$", str(bill or "").strip().upper())
        if m:
            per.setdefault(m.group(1), {})[int(m.group(2))] = min(day, per.get(m.group(1), {}).get(int(m.group(2)), day))
            strs[(m.group(1), int(m.group(2)))] = bill
    gaps, last = [], {}
    for s, nos in per.items():
        w = len(strs[(s, max(nos))]) - len(s)
        for n in range(min(nos), max(nos)):
            if n not in nos:
                below = max(x for x in nos if x < n)
                above = min(x for x in nos if x > n)
                gaps.append([s, "%s%0*d" % (s, w, n), nos[below], nos[above]])
        last[s] = [nos[max(nos)], strs[(s, max(nos))]]
    return dict(gaps=sorted(gaps), last=last)


def flat(state):
    """chain_state's gaps as the brute list: [series, number, day_before, day_after] per missing number."""
    return sorted([g["series"], n, g["between"][0], g["between"][1]] for g in state["gaps"] for n in expand(g["missing"]))


def probe_chain():
    """Sections 1, 2 and the collector half of 4 for ONE side (NEW = the box + S482, OLD = the box as it is)."""
    ING, FIN, WORK, DB, IN = (os.environ[k] for k in ("INGDIR", "FINDIR", "WORKDIR", "FINANCE_DB", "INDIR"))
    sys.path.insert(0, ING)
    import marg_take as MT                                              # noqa: E402
    MI = MT.MI
    assert MI.HERE == ING and MT.__file__.startswith(ING), (MI.HERE, MT.__file__)
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    import reports_tile as RT                                           # noqa: E402
    assert RT.__file__.startswith(FIN), RT.__file__
    out = dict(has_chain=hasattr(MT, "rebuild_chain") and hasattr(MT, "chain_state"), tile_has=hasattr(RT, "_s482_lines"))
    con = MT._connect(DB)
    cx = sqlite3.connect(DB, timeout=60)
    cx.row_factory = sqlite3.Row
    table = lambda: con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='mi_bill_chain'").fetchone()[0]
    days = far_days()
    far_today = dt.date.fromisoformat(days[15])
    far_now = dt.datetime(far_today.year, far_today.month, far_today.day, 8, 0, tzinfo=RT.IST)      # before 10:00: no banner clause

    def tile():
        s = RT.status(cx, far_today, far_now)
        texts, _rest = card_texts(RT.render(s))
        return dict(key="bill_chain" in s, chain=s.get("bill_chain") is not None, line=s["line"], card=texts,
                    lines=[(l["text_hi"], l["text_en"]) for l in ((s.get("bill_chain") or {}).get("lines") or [])])
    out["table_before"] = table()
    if not out["has_chain"]:
        out["tile_old"] = tile()
        out["table_after"] = table()
    else:
        # ---- 1  the chain on the copy of the live table
        out["rows"] = MT.rebuild_chain(con)
        live = MT.chain_state(con)
        out["live"] = live
        out["live_flat"] = flat(live)
        out["brute"] = brute(con, MT.CHAIN_FROM_DAY)
        out["from_day"] = MT.CHAIN_FROM_DAY
        out["first_days"] = dict(con.execute("SELECT series, MIN(day) FROM mi_bill_chain GROUP BY series").fetchall())
        out["empty_days"] = sorted({r[0] for r in con.execute("SELECT day FROM mi_bill_chain WHERE empty = 1")})
        out["tile_live"] = tile()
        # ---- 2  invented fixtures, keyed w482, continuing the copy's own chain on far days
        la = int(re.sub(r"\D", "", live["last"]["A"][1]))
        lc = int(re.sub(r"\D", "", live["last"]["CN"][1]))
        wa, wc = len(live["last"]["A"][1]) - 1, len(live["last"]["CN"][1]) - 2
        A = lambda k: "A%0*d" % (wa, la + k)
        C = lambda k: "CN%0*d" % (wc, lc + k)
        out["names"] = dict(A={str(k): A(k) for k in range(1, 24)}, CN={str(k): C(k) for k in range(1, 4)})

        def bills(day, nos):
            con.executemany("INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name) VALUES (?,?,?,?,?,?)",
                            [("w482" + "a" * 28, day, n, 1 if n.startswith("CN") else 0, q, "W482 ITEM") for n in nos for q in (1, 2)])
            con.commit()

        def empty(day, tag):
            con.execute("INSERT OR REPLACE INTO mi_file (md5, drive_id, drive_name, drive_folder, drive_mtime, size, stamp, type, variant, date_from, "
                        "date_to, verdict, reason, server_name, kept, lines, pc_type, pc_verdict, agree, received_at, source) VALUES "
                        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ("w482e" + tag * 27, "", "W482_EMPTY.XLS", "test", "", 1, day.replace("-", "") + "-090000", "SALE_BILLWISE", "DETAIL", day, day,
                         "VERIFIED", "EMPTY — no sale on %s" % day, "", 0, 0, "", "", "", day + "T09:00:00+05:30", "test"))
            con.commit()

        def step():
            MT.rebuild_chain(con)
            st = MT.chain_state(con)
            return dict(complete=st["complete"], gaps=[g for g in st["gaps"] if g["between"][1] >= days[0]],
                        old_gaps=[g for g in st["gaps"] if g["between"][1] < days[0]], last=st["last"])
        fx = {}
        bills(days[0], [A(1), A(2)])
        bills(days[1], [A(4), A(5)])
        fx["a"] = step()                                                # (a) one more number removed: it is named
        bills(days[5], [A(6), A(7)])
        empty(days[6], "1")
        bills(days[7], [A(8), A(9)])
        fx["b"] = step()                                                # (b) an EMPTY Sunday between two days whose numbers meet
        fx["b_weekday"] = dt.date.fromisoformat(days[6]).weekday()
        bills(days[8], [A(10), C(1)])
        empty(days[9], "2")
        bills(days[10], [A(13), C(3)])
        fx["c"] = step()                                                # (c) an EMPTY day between two days whose numbers do NOT meet
        bills(days[11], [A(14), A(16), A(17)])
        fx["d"] = step()                                                # (d) a gap inside a day
        fx["d_row"] = list(con.execute("SELECT gap_before, gap_inside FROM mi_bill_chain WHERE series='A' AND day=?", (days[11],)).fetchone())
        bills(days[12], [A(18)])
        bills(days[14], [A(23)])
        fx["f"] = step()                                                # a run of four
        fx["tile"] = tile()                                             # (e) the tile's lines for every case at once
        fx["days"] = days
        con.execute("DELETE FROM mi_sale_line WHERE md5 LIKE 'w482%'")
        con.execute("DELETE FROM mi_file WHERE md5 LIKE 'w482%'")
        con.commit()
        MT.rebuild_chain(con)
        fx["after_cleanup_same"] = (MT.chain_state(con) == live)
        out["fx"] = fx
        # (b) again on a table that holds nothing else: COMPLETE, and the tile renders nothing
        bl = MT._connect(os.path.join(WORK, "w482_blank.db"))
        bl.executemany("INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name) VALUES (?,?,?,?,?,?)",
                       [("w482" + "b" * 28, d, "A%06d" % n, 0, 1, "W482 ITEM") for d, ns in ((days[5], (1, 2)), (days[7], (3, 4))) for n in ns])
        bl.execute("INSERT INTO mi_file (md5, type, variant, verdict, lines, reason, date_from, date_to, received_at) VALUES (?,?,?,?,?,?,?,?,?)",
                   ("w482e" + "b" * 27, "SALE_BILLWISE", "DETAIL", "VERIFIED", 0, "EMPTY — no sale on %s" % days[6], days[6], days[6], days[6] + "T09:00:00"))
        bl.commit()
        MT.rebuild_chain(bl, from_day=days[0])
        bs = MT.chain_state(bl)
        bx = sqlite3.connect(os.path.join(WORK, "w482_blank.db"))
        bx.row_factory = sqlite3.Row
        s = RT.status(cx, far_today, far_now)                           # the copy's own page ...
        s["bill_chain"] = RT._s482_chain(bx)                            # ... carrying the COMPLETE chain's state
        out["blank"] = dict(built=bs["built"], complete=bs["complete"], gaps=bs["gaps"], last=bs["last"],
                            empties=[r[0] for r in bl.execute("SELECT series FROM mi_bill_chain WHERE empty = 1 ORDER BY series")],
                            card=card_texts(RT.render(s))[0], lines=(s.get("bill_chain") or {}).get("lines"))
        bx.close()
        bl.close()
    # ---- 4 (collector half)  marg_ingest.run on a scratch source folder holding a SUMMARY1 and an EMPTY sheet
    src = os.path.join(WORK, "drive", "SALE_BILLWISE", "2030-01")
    os.makedirs(src, exist_ok=True)
    raws = {}
    for key, name in (("empty", "empty.XLS"), ("short", "short.XLS")):
        raws[key] = open(os.path.join(IN, name), "rb").read()
        open(os.path.join(src, "W482__20300103-09%s00__%s_TXT.XLS" % ("00" if key == "empty" else "01", key)), "wb").write(raws[key])
    arch = os.path.join(WORK, "coll_archive")
    os.makedirs(MI.WORK, exist_ok=True)
    said = []
    try:
        rc = MI.run(MI.DirSource(os.path.join(WORK, "drive")), DB, archive=arch, out=said.append)
    except Exception as ex:                                             # noqa: BLE001
        rc = "RAISED %s: %s" % (ex.__class__.__name__, str(ex)[:120])
    coll = dict(rc=rc, said=[x[:200] for x in said])
    for key, raw in raws.items():
        m5 = md5b(raw)
        row = cx.execute("SELECT type, variant, verdict, reason, lines, kept, date_from, date_to FROM mi_file WHERE md5=?", (m5,)).fetchone()
        coll[key] = dict(row=dict(row) if row else None, at_rest=at_rest(arch, m5),
                         sale_lines=cx.execute("SELECT COUNT(*) FROM mi_sale_line WHERE md5=?", (m5,)).fetchone()[0])
    coll["chain_rows"] = ([list(r) for r in con.execute("SELECT series, empty, source_md5 FROM mi_bill_chain WHERE day=? ORDER BY series", (FIX_DAY,))]
                          if table() else None)
    coll["empty_md5"] = md5b(raws["empty"])
    out["collector"] = coll
    print(TAG + json.dumps(out, default=str))


def probe_eye():
    """Section 3's list and the staff-eye walk for ONE side. NEW: the box + S482 with the renames applied and the chain built on its
    own copy; OLD: the box as it is, its copy untouched."""
    ING, FIN, POR, DB, SIDE = (os.environ[k] for k in ("INGDIR", "FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    sys.path.insert(0, ING)
    import marg_take as MT                                              # noqa: E402  (this side's door, before the app can find another)
    assert MT.__file__.startswith(ING), MT.__file__
    out = {}
    if SIDE == "new":
        REN = load("renames_s482_walk", os.environ["RENPY"])
        c0 = sqlite3.connect(DB, timeout=60)
        r = REN.apply(c0)
        c0.commit()
        c0.close()
        out["renames_applied"] = dict(updated=r["updated"], stopped=r["stopped"])
        c1 = MT._connect(DB)
        out["chain_rows"] = MT.rebuild_chain(c1)
        c1.close()
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import reports_tile as RT                                           # noqa: E402
    import stock_app as SA                                              # noqa: E402
    assert RT.__file__.startswith(FIN) and SA.__file__.startswith(FIN), (RT.__file__, SA.__file__)
    assert sys.modules["marg_take"].__file__.startswith(ING)
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W482J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    eye, cookies = {}, {}

    def page(path, ck):
        body, code = "", 0
        for _hop in range(4):
            rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
            code = rr2.status_code
            if code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                path = rr2.headers["Location"].replace(BASE, "")
                continue
            body = rr2.get_data(as_text=True)
            break
        return code, body
    for who in ("shavez", "darpan", "amir", "manoj"):
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        home = r.get_data(as_text=True)
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
        ck = cookies[who] = "clinic_sso=" + tok
        pages = {"home": md5b(steady(home.replace(tok, "TOKEN")).encode())}
        rows, doors = [], set()
        mine = {who, (dm.get("shared") or {}).get(who)}
        for du in dm.get("duties") or []:
            if du.get("person") not in mine:
                continue
            row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None}
            sql = str(du.get("due_sql") or "").strip().rstrip(";")
            n = None
            if sql:
                try:
                    rr = ro.execute(sql).fetchone()
                    n = int((rr[0] if rr else 0) or 0)
                    row["since"] = rr[1] if rr and len(rr) > 1 else None
                except Exception as e:                                  # noqa: BLE001
                    n = "ERR " + str(e)[:80]
            row["due_n"] = n
            door, mark = du.get("door"), du.get("door_marker")
            if door and str(door).startswith("/finance/"):
                doors.add(str(door))
                if mark and isinstance(n, int) and n > 0:
                    body = page(str(door), ck)[1]
                    row["door_seen"] = (mark in body) or (mark in _html.unescape(body))
            rows.append(row)
        doors.add("/finance/reports/aaj")
        chain_card = None
        for d in sorted(doors):
            code, body = page(d, ck)
            if d == "/finance/reports/aaj":
                chain_card, body = card_texts(body)                     # the one thing that may differ: taken out, and told apart
            pages[d] = "%s %s" % (code, md5b(steady(body.replace(tok, "TOKEN")).encode()))
        eye[who] = dict(status=r.status_code, n_tiles=len(seen), duties=rows, pages=pages, chain_card=chain_card)
    # the owner's line, as the page's own API gives it
    rj = fc.get("/finance/reports/aaj/api/status", base_url=BASE, headers={"Cookie": cookies["manoj"]})
    try:
        j = rj.get_json() or {}
    except Exception:                                                   # noqa: BLE001
        j = {}
    out["api"] = dict(code=rj.status_code, has_key="bill_chain" in j, line=j.get("line") or "",
                      clauses=[l.get("text_en") for l in ((j.get("bill_chain") or {}).get("lines") or [])])
    # ---- 3  Amir's rename list on this copy: as it is, then with the proof forced green HERE (never on the live database)
    root = SA._newest_root(ro)
    ro.close()
    ids = [int(x) for x in json.loads(os.environ["W482J"])["ids"]]

    def board():
        if not root:
            return dict(code=0, ready=None, n=0, names={}, n20={})
        rb = fc.get("/finance/stock/api/pad/amir/%d" % int(root), base_url=BASE, headers={"Cookie": cookies["amir"]})
        try:
            b = rb.get_json() or {}
        except Exception:                                               # noqa: BLE001
            b = {}
        rws = ((b.get("renames") or {}).get("rows")) or []
        return dict(code=rb.status_code, ready=b.get("renames_ready"), n=len(rws),
                    names={str(x["id"]): x.get("new_name") for x in rws if x.get("id") in ids},
                    n20={str(x["id"]): x.get("new20") for x in rws if x.get("id") in ids})
    out["root"] = root
    out["board_as_is"] = board()
    real_proof, real_stage = SA._proof_state, SA.amir_stage
    SA._proof_state = lambda con, d: dict(real_proof(con, d), state="done")

    def stage(con, cid=None):
        st = real_stage(con, cid)
        return dict(st, renames_visible=True) if st else st
    SA.amir_stage = stage
    SA._S444_RENAMES_CACHE.clear()
    out["board_forced"] = board()
    out["eye"] = eye
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================================ server
def server(a):
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/") and a.por.startswith("/tmp/"), "refusing a non-scratch path: %s %s" % (W, a.por)
    os.makedirs(W, exist_ok=True)
    kp = os.path.join(W, "kitpy")
    os.makedirs(kp, exist_ok=True)
    shutil.copy(os.path.join(a.kit, "renames_s482.py"), kp)
    REN = load("renames_s482", os.path.join(kp, "renames_s482.py"))
    s480 = os.path.join(a.kits, "S480_MARG_TEXT_READERS", "marg_txt.py")
    if not check("the S480 kit's marg_txt.py is reachable (it makes the walk's made-up EMPTY and SUMMARY1 sheets)", os.path.exists(s480), s480):
        return finish("server")
    shutil.copy(s480, os.path.join(kp, "marg_txt_s480.py"))
    MTXT = load("marg_txt_s480", os.path.join(kp, "marg_txt_s480.py"))
    IN = os.path.join(W, "in")
    os.makedirs(IN, exist_ok=True)
    x, info = MTXT.convert(MTXT.EMPTY_DAY_SAMPLE, exported_at=dt.datetime(2030, 1, 3, 9, 0, 0))
    open(os.path.join(IN, "empty.XLS"), "wb").write(x)
    open(os.path.join(IN, "short.XLS"), "wb").write(MTXT.convert(MTXT._s480_samples()["SALE_BILLWISE_SUMMARY1"])[0])

    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W482 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def run(mode, side, ing, fin):
        wd = os.path.join(W, "%s_%s" % (mode, side))
        os.makedirs(wd, exist_ok=True)
        dbp, adbp, spp = [os.path.join(wd, "w482_%s.db" % x) for x in ("fin", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, INGDIR=ing, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, INDIR=IN, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store,
                   TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map,
                   W482J=json.dumps(dict(pw=pw, ids=[r[0] for r in REN.ROWS])), MI_ARCHIVE=os.path.join(ing, "archive"), MARG_INGEST_DIR=ing,
                   RENPY=os.path.join(kp, "renames_s482.py"), ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"),
                   SR_DB_PATH=os.path.join(wd, "no_staff_register.db"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "FINANCE_MARG_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin if mode == "eye" else wd,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])

    # ------------------------------------------------------------------------------------------------------------------ sections 1, 2
    print("-- 1  the chain on the copy of the live table (rebuild_chain -> chain_state)")
    CN_, CO = run("chain", "new", a.ingest_new, a.fin_new), run("chain", "old", a.ingest_old, a.fin_old)
    if not check("both chain probes ran to the end (NEW = the box + S482, OLD = the box as it is)", CN_ is not None and CO is not None):
        return finish("server")
    if not check("NEW marg_take has rebuild_chain and chain_state; NEW reports_tile words the lines", CN_["has_chain"] and CN_["tile_has"]):
        return finish("server")
    live = CN_["live"]
    check("no table before the first rebuild; %d rows written; the chain starts on %s (nothing earlier is read: first day per series %s)"
          % (CN_["rows"], CN_["from_day"], CN_["first_days"]),
          CN_["table_before"] == 0 and CN_["rows"] > 0 and all(d >= CN_["from_day"] for d in CN_["first_days"].values()))
    check("chain_state is the chain worked out a second way, straight from mi_sale_line: the same %d missing number(s), each between the same "
          "two days; the same last bill per series" % len(CN_["brute"]["gaps"]),
          CN_["live_flat"] == CN_["brute"]["gaps"] and live["last"] == CN_["brute"]["last"], (CN_["live_flat"], live["last"]))
    check("complete = %s on the live copy; every gap is between two numbered days of its own series (no gap is 'inside' a day today)"
          % live["complete"], live["complete"] == (not live["gaps"]) and live["built"] is True)
    if a.expect:
        nos, d1, d2 = a.expect.split("|")
        got = sorted(n for g in live["gaps"] for n in expand(g["missing"]))
        check("A.5 -- exactly the one gap the chat measured: %s between %s and %s, and nothing else; complete = False"
              % (" and ".join(sorted(nos.split(","))), d1, d2),
              got == sorted(nos.split(",")) and all(g["between"] == [d1, d2] and not g["via_empty"] for g in live["gaps"]) and live["complete"] is False,
              live["gaps"])
    else:
        print("   (no --expect given: the live gap list is shown, not compared with a measurement)   %s" % live["gaps"])
    check("last = the newest numbered day per series: %s; the copy's EMPTY day(s) %s carry no number and break nothing"
          % (live["last"], CN_["empty_days"]), set(live["last"]) >= {"A", "CN"})
    tl = CN_["tile_live"]
    want_live = []
    seen_pairs = []
    for g in live["gaps"]:
        k = (g["between"][0], g["between"][1], tuple(g["via_empty"]))
        if k not in seen_pairs:
            seen_pairs.append(k)
    for k in seen_pairs:
        nos = [w for g in sorted(live["gaps"], key=lambda g: g["series"]) if (g["between"][0], g["between"][1], tuple(g["via_empty"])) == k for w in g["missing"]]
        want_live.append((want_hi(nos, k[0], k[1], k[2], inside=(k[0] == k[1])), want_en(nos, k[0], k[1], k[2], inside=(k[0] == k[1]))))
    check("the tile on this copy: status() carries bill_chain; ONE line per open gap, worded as A.4 -- Hindi on the card, English in the "
          "owner's line%s" % ("".join("\n         HI  %s\n         EN  %s" % w for w in want_live)),
          tl["chain"] and [tuple(x) for x in tl["lines"]] == want_live and tl["card"] == [w[0] for w in want_live]
          and all((" · " + w[1]) in tl["line"] for w in want_live), (tl["card"], tl["line"][-200:]))
    to = CO.get("tile_old") or {}
    check("negative control, the box as it is (marg_take 3ac9bbe0, reports_tile 406e452b): no rebuild_chain, no chain_state, no table before "
          "or after, no bill_chain in status(), no card, no 'Bill chain' in the owner's line",
          CO["has_chain"] is False and CO["tile_has"] is False and CO["table_before"] == 0 and CO.get("table_after") == 0
          and to.get("key") is False and to.get("card") == [] and "Bill chain" not in (to.get("line") or "x"), (CO["has_chain"], to.get("card")))
    strip = tl["line"]
    for w in want_live:
        strip = strip.replace(" · " + w[1], "")
    check("the owner's line with the gap clause taken out is the OLD line, letter for letter (the same far morning, before 10:00)",
          strip == to.get("line"), (strip[-120:], (to.get("line") or "")[-120:]))

    print("-- 2  invented fixtures (rows keyed w482; the numbers continue the copy's own chain on far days)")
    fx, nm = CN_["fx"], CN_["names"]
    A = lambda k: nm["A"][str(k)]
    C = lambda k: nm["CN"][str(k)]
    d = fx["days"]
    ga = fx["a"]["gaps"]
    check("(a) one more number removed -> it is named: %s between %s and %s, n 1; the copy's own gap list is untouched"
          % (A(3), d[0], d[1]), ga == [dict(series="A", between=[d[0], d[1]], via_empty=[], missing=[A(3)], n=1)]
          and fx["a"]["old_gaps"] == live["gaps"] and fx["a"]["complete"] is False, ga)
    check("(b) an EMPTY row for a Sunday (%s) between two days whose numbers meet -> the gap list unchanged" % d[6],
          fx["b"]["gaps"] == ga and fx["b_weekday"] == 6 and fx["b"]["old_gaps"] == live["gaps"], fx["b"]["gaps"])
    bk = CN_["blank"]
    check("(b) the same three days on a table that holds nothing else: built, COMPLETE, no gap; an EMPTY row per series (%s); the tile "
          "renders NOTHING for a complete chain (no line, no card)" % bk["empties"],
          bk["built"] and bk["complete"] is True and bk["gaps"] == [] and bk["empties"] == ["A", "CN"] and bk["card"] == []
          and bk["lines"] == [], (bk["complete"], bk["gaps"], bk["card"]))
    gc = [g for g in fx["c"]["gaps"] if g not in ga]
    check("(c) an EMPTY row (%s) between two days whose numbers do NOT meet -> one gap per series naming all three dates: %s, %s and %s "
          "between %s and %s via %s" % (d[9], A(11), A(12), C(2), d[8], d[10], d[9]),
          gc == [dict(series="A", between=[d[8], d[10]], via_empty=[d[9]], missing=[A(11), A(12)], n=2),
                 dict(series="CN", between=[d[8], d[10]], via_empty=[d[9]], missing=[C(2)], n=1)], gc)
    gd = [g for g in fx["d"]["gaps"] if g not in fx["c"]["gaps"]]
    check("(d) a gap inside a day -> that day's gap_inside (%s on %s; its gap_before is empty)" % (A(15), d[11]),
          gd == [dict(series="A", between=[d[11], d[11]], via_empty=[], missing=[A(15)], n=1)] and fx["d_row"] == ["", A(15)], (gd, fx["d_row"]))
    gf = [g for g in fx["f"]["gaps"] if g not in fx["d"]["gaps"]]
    check("    a run of four missing numbers is one word, counted as four: %s..%s between %s and %s" % (A(19), A(22), d[12], d[14]),
          gf == [dict(series="A", between=[d[12], d[14]], via_empty=[], missing=["%s..%s" % (A(19), A(22))], n=4)], gf)
    want = want_live + [
        (want_hi([A(3)], d[0], d[1]), want_en([A(3)], d[0], d[1])),
        (want_hi([A(11), A(12), C(2)], d[8], d[10], [d[9]]), want_en([A(11), A(12), C(2)], d[8], d[10], [d[9]])),
        (want_hi([A(15)], d[11], d[11], inside=True), want_en([A(15)], d[11], d[11], inside=True)),
        (want_hi(["%s..%s" % (A(19), A(22))], d[12], d[14]), want_en(["%s..%s" % (A(19), A(22))], d[12], d[14]))]
    ft = fx["tile"]
    check("(e) the tile renders each case's Hindi and English line exactly as A.4 words them, one line per gap, oldest first:%s"
          % "".join("\n         HI  %s\n         EN  %s" % w for w in want[len(want_live):]),
          [tuple(x) for x in ft["lines"]] == want and ft["card"] == [w[0] for w in want] and all((" · " + w[1]) in ft["line"] for w in want),
          ft["card"])
    check("    no calendar word in any line (no Sunday, no Ravivaar, no holiday, no chhutti)",
          not re.search(r"sunday|ravivaar|holiday|chhutti", " ".join(x for w in want for x in w), re.I))
    check("    the fixtures deleted (md5 LIKE 'w482%') and the chain rebuilt: chain_state is the live state again -- a line leaves by itself "
          "when its numbers arrive", fx["after_cleanup_same"] is True)

    # ------------------------------------------------------------------------------------------------------------------ section 4
    print("-- 4  the spine's reader on invented sheets (the real EMPTY sheet is read on manojz), and the Drive collector")
    sys.path.insert(0, a.ingest_new)                                   # the vendored xlrd of the scratch copy
    os.makedirs(os.path.join(W, "rd"), exist_ok=True)
    R = {}
    for side, fin in (("old", a.fin_old), ("new", a.fin_new)):
        shutil.copy(os.path.join(fin, "spine", "marg_read.py"), os.path.join(W, "rd", "marg_read_%s.py" % side))
        R[side] = load("marg_read_" + side, os.path.join(W, "rd", "marg_read_%s.py" % side))
    title = [" " * 18 + "BILL WISE SALES STATEMENT AS ON 02-01-2030"] + [""] * 8
    e3 = [title, HEADS, ["Total No. of", "Bills: 0", "DAY TOTAL :"] + ["0.0"] * 6]
    ro_, rn_ = R["old"].read_sale_detail(e3), R["new"].read_sale_detail(e3)
    check("the invented 3-row EMPTY sheet (title, heads, 'Total No. of | Bills: 0 | DAY TOTAL :'), OLD reader: exactly the two footer checks fail",
          (not ro_.ok) and ro_.failed() == ["GRAND TOTAL = sum of bill GROSS", "footer bill count = bills read"], ro_.failed())
    check("NEW reader: no check fails; empty True; the day is the title's (%s); no bill" % FIX_DAY,
          rn_.ok and rn_.failed() == [] and rn_.data.get("empty") is True and rn_.data["date_from"] == rn_.data["date_to"] == FIX_DAY
          and rn_.data["days"] == [FIX_DAY] and rn_.data["bills"] == [], (rn_.failed(), {k: v for k, v in rn_.data.items() if k != "bills"}))
    rec_o = R["old"].reading_record(os.path.join(IN, "empty.XLS"), "SALE_BILLWISE_DETAIL__2030-01-02__20300103-090000__w482.XLS")
    rec_n = R["new"].reading_record(os.path.join(IN, "empty.XLS"), "SALE_BILLWISE_DETAIL__2030-01-02__20300103-090000__w482.XLS")
    check("the same through the file door (reading_record on the made-up EMPTY .XLS, as spine_evidence calls it): OLD ok False, NEW ok True "
          "-- the certificate the tile reads", rec_o["ok"] is False and len(rec_o["failed"]) == 2 and rec_n["ok"] is True and rec_n["failed"] == []
          and rec_n["data"].get("empty") is True and rec_n["data"]["date_from"] == FIX_DAY, (rec_o["failed"], rec_n["failed"]))
    n2 = [title, HEADS, ["Total No. of", "Bills: 2", "DAY TOTAL :", "150.0"] + ["0.0"] * 5]
    bo, bn = R["old"].read_sale_detail(n2), R["new"].read_sale_detail(n2)
    check("a sheet with no BILL row whose footer is NOT 'Bills: 0' keeps failing, the same on both (%s)" % bn.failed()[:2],
          (not bn.ok) and bn.failed() == bo.failed() and "empty" not in bn.data, (bo.failed(), bn.failed()))
    det = [title, HEADS, ["02-01-2030"] + [""] * 8,
           ["A900001", "W482 TEST", "", "100.0", "0.0", "0.0", "0.0", "100.0", "100.0"],
           ["", "  1    10 W482 ITEM ONE        1*10", "1", "100.00 12/31", "W482B", "", "", "", ""],
           ["", "", "DAY TOTAL :", "100.0", "0.0", "0.0", "0.0", "100.0", "100.0"],
           ["Total No. of", "Bills: 1", "GRAND TOTAL :", "100.0", "0.0", "0.0", "0.0", "100.0", "100.0"]]
    do, dn = R["old"].read_sale_detail(det), R["new"].read_sale_detail(det)
    check("an invented DETAIL sheet (one bill, its own DAY TOTAL row, 'Bills: 1 | GRAND TOTAL :'): the same checks, the same result, no 'empty'",
          do.ok and dn.ok and do.checks == dn.checks and do.data == dn.data and dict(do.classes) == dict(dn.classes) and "empty" not in dn.data,
          (do.failed(), dn.failed(), dict(dn.classes)))
    kn, ko = CN_["collector"], CO["collector"]
    en_, sn_ = kn["empty"], kn["short"]
    check("the collector (marg_ingest.run on a scratch source folder), NEW: the SUMMARY1 sheet lands VERIFIED with lines 0 -- no sale_lines "
          "call -- and is deleted as every sale file is (not at rest)",
          bool(sn_["row"]) and (sn_["row"]["verdict"], sn_["row"]["type"], sn_["row"]["variant"], sn_["row"]["lines"], sn_["row"]["kept"])
          == ("VERIFIED", "SALE_BILLWISE", "SUMMARY1", 0, 0) and sn_["at_rest"] == [] and sn_["sale_lines"] == 0, (kn["rc"], sn_, kn["said"][-3:]))
    check("NEW: the EMPTY sheet lands VERIFIED, lines 0, reason 'EMPTY (em dash) no sale on %s' -- the door's exact words -- and date_from = "
          "date_to = that day" % FIX_DAY,
          bool(en_["row"]) and en_["row"]["verdict"] == "VERIFIED" and en_["row"]["lines"] == 0 and en_["row"]["reason"] == "EMPTY — no sale on %s" % FIX_DAY
          and en_["row"]["date_from"] == en_["row"]["date_to"] == FIX_DAY and en_["at_rest"] == [] and en_["sale_lines"] == 0,
          en_["row"] and dict(en_["row"], reason=en_["row"]["reason"].replace("—", "--")))
    check("NEW: the chain is rebuilt by the collector itself -- %s has an EMPTY row per series, pointing at that sheet" % FIX_DAY,
          kn["chain_rows"] == [["A", 1, kn["empty_md5"]], ["CN", 1, kn["empty_md5"]]], kn["chain_rows"])
    eo, so = ko["empty"], ko["short"]
    check("negative control, marg_ingest as it is (7f6b4dc2): the SUMMARY1 sheet is NOT taken (%s) -- no mi_file row, and the file STAYS AT "
          "REST in the archive (%d file)" % (([x for x in ko["said"] if "FAILED" in x] or ["?"])[0].split(" -- ")[-1][:60].strip(), len(so["at_rest"])),
          so["row"] is None and len(so["at_rest"]) >= 1 and any("FAILED" in x for x in ko["said"]), (ko["rc"], ko["said"][:4]))
    check("negative control: the EMPTY sheet gets no EMPTY reason from the OLD collector (reason %r) and no chain exists"
          % ((eo["row"] or {}).get("reason", "")[:40]), bool(eo["row"]) and not str(eo["row"]["reason"]).startswith("EMPTY") and ko["chain_rows"] is None,
          eo["row"])

    # ------------------------------------------------------------------------------------------------------------------ section 3
    print("-- 3  the renames (D676): finance.db marg_item_rename, on a scratch copy")
    rdb = os.path.join(W, "w482_ren.db")
    copydb(a.db, rdb)
    con = sqlite3.connect(rdb)
    before = REN.table(con)
    cols = [c[1] for c in con.execute("PRAGMA table_info(marg_item_rename)")]
    ix = {c: i for i, c in enumerate(cols)}
    try:
        r = REN.apply(con)
        con.commit()
    except REN.Stop as ex:
        check("the seven rows update on the copy", False, str(ex))
        return finish("server")
    after = REN.table(con)
    ids = [x[0] for x in REN.ROWS]
    check("the seven rows (ids %s) are updated by id AND old_name; none was ticked or seen before (done_by, done_at, verified_* NULL)" % ids,
          r["updated"] == ids and r["stopped"] == [] and r["already"] == [], (r["updated"], r["stopped"], r["already"]))
    check("each carries the brief's spelling, new20 = clip(new_name, 20), new27 = clip(new_name, 27), and the note's S482/D676 words at its end",
          all(after[i][ix["new_name"]] == new and after[i][ix["new20"]] == new[:20].rstrip() and after[i][ix["new27"]] == new[:27].rstrip()
              and after[i][ix["note"]] == (before[i][ix["note"]] or "") + REN.NOTE and after[i][ix["old_name"]] == old for i, old, new in REN.ROWS),
          {i: after[i][ix["new20"]] for i in ids})
    for i, old, new in REN.ROWS:
        print("         %2d  %-29s  %-28s -> %-29s  (20: %s)" % (i, old, before[i][ix["new_name"]], new, after[i][ix["new20"]]))
    n20 = [x[ix["new20"]] for x in after.values()]
    check("no two of the table's %d rows share new20; no new_name is longer than 29; the other %d rows are unchanged cell for cell; of the "
          "seven only new_name, new20, new27 and note moved" % (len(after), len(after) - len(ids)),
          len(set(n20)) == len(n20) and all(len(x[ix["new_name"]]) <= 29 for x in after.values())
          and all(before[i] == after[i] for i in before if i not in ids) and set(before) == set(after)
          and all({c for c in cols if before[i][ix[c]] != after[i][ix[c]]} == {"new_name", "new20", "new27", "note"} for i in ids))
    r2 = REN.apply(con)
    con.commit()
    check("run again: nothing is written twice (7 already so; the note is not appended again)",
          r2["updated"] == [] and r2["already"] == ids and REN.table(con) == after)
    # the walk's own row, found by its key
    base = list(after[ids[0]])
    for c, v in (("id", 9482), ("old_name", "W482 OLD NAME"), ("new_name", "W482 NEW NAME"), ("old20", "W482 OLD NAME"), ("old27", "W482 OLD NAME"),
                 ("new20", "W482 NEW NAME"), ("new27", "W482 NEW NAME"), ("note", "W482")):
        base[ix[c]] = v
    con.execute("INSERT INTO marg_item_rename (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))), base)
    con.commit()
    snap = REN.table(con)
    try:
        REN.apply(con, rows=((9482, "W482 SOME OTHER OLD NAME", "W482 BETTER NAME"),))
        refused = False
    except REN.Stop as ex:
        refused = "no row with this id AND old_name" in str(ex)
    check("negative control (one invented row, id 9482): the keyed update REFUSES a row whose old_name does not match -- nothing is written",
          refused is True and REN.table(con) == snap)
    con.execute("UPDATE marg_item_rename SET done_by='w482', done_at='2031-03-03T09:00:00' WHERE id=9482")
    con.commit()
    snap = REN.table(con)
    r3 = REN.apply(con, rows=((9482, "W482 OLD NAME", "W482 BETTER NAME"),))
    con.commit()
    check("a row already ticked is STOPPED and reported, never renamed under his feet", r3["updated"] == [] and len(r3["stopped"]) == 1
          and r3["stopped"][0][0] == 9482 and REN.table(con) == snap, r3["stopped"])
    con.execute("UPDATE marg_item_rename SET done_by=NULL, done_at=NULL WHERE id=9482")
    con.commit()
    snap = REN.table(con)
    try:
        REN.apply(con, rows=((9482, "W482 OLD NAME", REN.ROWS[0][2][:20] + " W482"),))
        clash = False
    except REN.Stop as ex:
        clash = "share a 20-letter name" in str(ex)
    check("a spelling that would make two rows share their first 20 letters is refused whole (rolled back)", clash is True and REN.table(con) == snap)
    con.close()

    print("-- 3b + staff-eye (D648): shavez, darpan, amir and the owner on scratch copies, a walk-only login store and secret")
    EN, EO = run("eye", "new", a.ingest_new, a.fin_new), run("eye", "old", a.ingest_old, a.fin_old)
    if not check("both staff-eye probes ran to the end (NEW: the renames applied and the chain built on its own copy; OLD: the copy as it is)",
                 EN is not None and EO is not None):
        return finish("server")
    s268 = {str(i): before[i][ix["new_name"]] for i in ids}
    d676 = {str(i): new for i, _old, new in REN.ROWS}
    bf, bo_ = EN["board_forced"], EO["board_forced"]
    check("Amir's rename list (his board, count #%s) with the proof forced green ON THE COPY: the list is open to him and shows the seven "
          "D676 spellings" % EN["root"], bf["code"] == 200 and bf["ready"] is True and bf["names"] == d676
          and bf["n20"] == {k: v[:20].rstrip() for k, v in d676.items()}, bf)
    check("negative control, the copy without the update: the same list shows S268's spellings (LS BELT ..., ... TRACT L BELT)",
          bo_["code"] == 200 and bo_["ready"] is True and bo_["names"] == s268 and bo_["names"] != d676, bo_["names"])
    print("         as the copy is (no forcing): the list is %s for Amir on both sides (renames_ready NEW %s / OLD %s)"
          % ("open" if EN["board_as_is"]["ready"] else "not open yet", EN["board_as_is"]["ready"], EO["board_as_is"]["ready"]))
    hi_live = [w[0] for w in want_live]
    for who in ("shavez", "darpan", "amir", "manoj"):
        n_, o_ = EN["eye"][who], EO["eye"][who]
        can = n_["pages"].get("/finance/reports/aaj", "").startswith("200")
        check("%s signs in; the home is byte-equal before and after (%d tiles); every door page too (%d pages) -- the reports tile compared "
              "with its gap card taken out" % (who, n_["n_tiles"], len(n_["pages"])),
              n_["status"] == 200 and n_["n_tiles"] > 0 and n_["pages"] == o_["pages"], [k for k in n_["pages"] if n_["pages"][k] != o_["pages"].get(k)])
        check("   %s: the reports tile %s; OLD shows no card" % (who, ("shows the gap line -- %s" % n_["chain_card"]) if can else "is not his page (no card)"),
              (n_["chain_card"] == hi_live if can else n_["chain_card"] == []) and o_["chain_card"] == [], (n_["chain_card"], o_["chain_card"]))
        nd = [x for x in n_["duties"] if x["id"] != NEW_DUTY]
        od = [x for x in o_["duties"] if x["id"] != NEW_DUTY]
        due = [x for x in n_["duties"] if isinstance(x.get("due_n"), int) and x["due_n"] > 0]
        hid = [x["id"] for x in due if x.get("tile_seen") is False or x.get("door_seen") is False]
        check("   %s: %d duties in the map, %d due now -- each due one is visible (its tile on the home, its marker on its door); the same on "
              "both sides" % (who, len(n_["duties"]), len(due)), not hid and nd == od, hid)
    nd = [x for x in EN["eye"]["shavez"]["duties"] if x["id"] == NEW_DUTY]
    check("the duty this kit adds to the map (%s): due on the copy (n %s, since %s), its tile 'Aaj ki reports' on Shavez's home, its marker on "
          "the door while due" % (NEW_DUTY, nd and nd[0].get("due_n"), nd and nd[0].get("since")),
          len(nd) == 1 and isinstance(nd[0].get("due_n"), int) and nd[0]["due_n"] >= (1 if live["gaps"] else 0)
          and (not live["gaps"] or (nd[0].get("tile_seen") is True and nd[0].get("door_seen") is True)), nd)
    api_n, api_o = EN["api"], EO["api"]
    check("the owner's English line (the page's own status API, signed in as the owner): %s" % (api_n["clauses"] or "no clause"),
          api_n["code"] == 200 and api_n["has_key"] and api_n["clauses"] == [w[1] for w in want_live]
          and all((" · " + w[1]) in api_n["line"] for w in want_live) and api_o["has_key"] is False and "Bill chain" not in api_o["line"],
          (api_n["line"][-160:], api_o["line"][-80:]))
    return finish("server")


# ============================================================================================================================ manojz
def manojz(a):
    W = os.path.abspath(a.work)
    os.makedirs(W, exist_ok=True)
    sys.path.insert(0, a.pull)                                          # the vendored xlrd beside the pull
    print("-- 4  the spine's reader on the real sheets of MargArchive (verdicts only; no line of a sheet is printed)")
    R = {}
    for side, p in (("old", a.old_read), ("new", a.new_read)):
        shutil.copy(p, os.path.join(W, "marg_read_%s.py" % side))
        R[side] = load("marg_read_" + side, os.path.join(W, "marg_read_%s.py" % side))
    import glob
    emp = sorted(glob.glob(os.path.join(a.archive, "SALE_BILLWISE", "2026-10", "SALE_BILLWISE_DETAIL__2026-10-04__*.XLS")))
    if not check("the real EMPTY sheet of 04-10 is in MargArchive (%d file)" % len(emp), len(emp) >= 1):
        return finish("manojz")
    ro_, rn_ = R["old"].reading_record(emp[-1]), R["new"].reading_record(emp[-1])
    check("OLD reader (7ec9b325) on it: exactly two failed checks -- %s" % ro_["failed"],
          ro_["ok"] is False and ro_["failed"] == ["GRAND TOTAL = sum of bill GROSS", "footer bill count = bills read"])
    check("NEW reader on it: no failed check; empty True; the day from the title (%s); no bill; the same md5 (%s)"
          % (rn_["data"].get("date_from"), rn_["md5"][:8]),
          rn_["ok"] is True and rn_["failed"] == [] and rn_["data"].get("empty") is True and rn_["data"]["date_from"] == rn_["data"]["date_to"] == "2026-10-04"
          and rn_["data"]["bills"] == [] and rn_["md5"] == ro_["md5"], (rn_["failed"], rn_["classes"]))
    det = [p for p in sorted(glob.glob(os.path.join(a.archive, "SALE_BILLWISE", "2026-*", "SALE_BILLWISE_DETAIL__*.XLS"))) if p not in emp]
    same, diff, okn = 0, [], 0
    for p in det:
        o, n = R["old"].reading_record(p), R["new"].reading_record(p)
        if o == n and "empty" not in n["data"]:
            same += 1
            okn += 1 if n["ok"] else 0
        else:
            diff.append(os.path.basename(p)[:50])
    check("every DETAIL sheet in the archive (%d files): the same checks, the same result, record for record (%d of them ok on both)"
          % (len(det), okn), len(det) > 20 and same == len(det) and not diff, diff[:3])

    print("-- 5  the outbox, DRY, on scratch copies of _outbox_state.json and index.csv (the outbox files are empty stand-ins of the same names)")
    G = {}
    for side, p in (("old", a.old_gate), ("new", a.new_gate)):
        shutil.copy(p, os.path.join(W, "marg_gate_%s.py" % side))
        G[side] = load("marg_gate_" + side, os.path.join(W, "marg_gate_%s.py" % side))
    hdr = None
    with io.open(os.path.join(a.archive, "index.csv"), "r", encoding="utf-8", errors="replace", newline="") as fh:
        import csv
        hdr = next(csv.reader(fh))
    E_REAL = [r for r in G["new"].read_index(a.archive) if r.get("type") == "SALE_BILLWISE" and r.get("verdict") == "VERIFIED"
              and r.get("date_to") == "2026-10-04" and G["new"]._s482_empty_sheet(r)]
    if not check("the real EMPTY row is in index.csv: VERIFIED, rows = %s (a string), date 2026-10-04" % (E_REAL and E_REAL[-1]["rows"]),
                 len(E_REAL) >= 1 and E_REAL[-1]["rows"] == "3"):
        return finish("manojz")
    e_md5 = E_REAL[-1]["md5"]
    inv_e = "e482" * 8                                                  # an invented EMPTY weekday
    inv_d = "d482" * 8                                                  # an invented DETAIL day, never sent

    def scratch(name, with_detail):
        S = os.path.join(W, name)
        os.makedirs(os.path.join(S, "_outbox"))                         # a fresh work folder every run: nothing is ever deleted here
        shutil.copy(os.path.join(a.archive, "index.csv"), S)
        shutil.copy(os.path.join(a.archive, "_outbox_state.json"), S)
        for n in os.listdir(os.path.join(a.archive, "_outbox")):
            open(os.path.join(S, "_outbox", n), "wb").close()           # the NAME only: no sheet is copied
        rows = [dict(seen_at="2030-01-04 09:00:00", type="SALE_BILLWISE", variant="DETAIL", date_from="2030-01-03", date_to="2030-01-03",
                     export_stamp="20300104-090000", md5=inv_e, verdict="VERIFIED", rows="3",
                     archived_path=os.path.join(S, "SALE_BILLWISE_DETAIL__2030-01-03__20300104-090000__%s.XLS" % inv_e[:8]))]
        if with_detail:
            rows.append(dict(seen_at="2030-01-05 09:00:00", type="SALE_BILLWISE", variant="DETAIL", date_from="2030-01-04", date_to="2030-01-04",
                             data_from="2030-01-04", data_to="2030-01-04", export_stamp="20300105-090000", md5=inv_d, verdict="VERIFIED", rows="40",
                             archived_path=os.path.join(S, "SALE_BILLWISE_DETAIL__2030-01-04__20300105-090000__%s.XLS" % inv_d[:8])))
        with io.open(os.path.join(S, "index.csv"), "a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            for r in rows:
                w.writerow([r.get(h, "") for h in hdr])
                open(os.path.join(S, "_outbox", os.path.basename(r["archived_path"])), "wb").close()
                open(r["archived_path"], "wb").close()
        with io.open(os.path.join(S, "_coverage_from.txt"), "w", encoding="utf-8") as fh:
            fh.write("2030-01-03\n")
        with io.open(os.path.join(S, "_NEEDS_ATTENTION.txt"), "w", encoding="utf-8") as fh:
            fh.write("W482 stand-in for the note of the last failure\n")
        return S

    def send(side, S, dry=True):
        if not dry:                                                     # a stand-in, never a token: with nothing to send, nothing is posted
            with io.open(os.path.join(S, "no_token.txt"), "w", encoding="utf-8") as fh:
                fh.write("W482-STAND-IN-NOT-A-TOKEN\n")
        p = subprocess.run([sys.executable, "-B", os.path.join(W, "marg_gate_%s.py" % side), "send"] + (["--dry-run"] if dry else [])
                           + ["--archive", S, "--token-file", os.path.join(S, "no_token.txt"), "--token-unc", os.path.join(S, "no_unc.txt"),
                              "--medical-log", os.path.join(S, "no_log.txt"), "--url", "http://127.0.0.1:9/never"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
        o = p.stdout
        tosend = re.findall(r"^\s+([0-9a-f]{8})\s+\S+\s+\(", o, re.M)
        return dict(rc=p.returncode, tosend=tosend, empty=re.findall(r"skipping ([0-9a-f]{8}) \(\S+\) -- an empty day", o),
                    nothing="Nothing to send" in o, state=json.load(io.open(os.path.join(S, "_outbox_state.json"), encoding="utf-8"))["sent"])
    S_old, S_new = scratch("out_old", False), scratch("out_new", False)
    so, sn = send("old", S_old), send("new", S_new)
    check("OLD marg_gate (52f502d1), send --dry-run: the EMPTY file of 04-10 (%s) IS in the send list -- with the invented empty weekday (%s)"
          % (e_md5[:8], inv_e[:8]), sorted(so["tosend"]) == sorted([e_md5[:8], inv_e[:8]]) and so["empty"] == [] and e_md5 not in so["state"], so["tosend"])
    check("NEW marg_gate, the same copies: both are told 'an empty day' and skipped; nothing is left to send",
          sn["tosend"] == [] and sorted(sn["empty"]) == sorted([e_md5[:8], inv_e[:8]]) and sn["nothing"] and sn["rc"] == 0, (sn["tosend"], sn["empty"]))
    ent = sn["state"].get(e_md5) or {}
    check("its outbox entry: result empty_day, http null, business_date 2026-10-04, the export stamp, the brief's note",
          ent.get("result") == "empty_day" and ent.get("http") is None and ent.get("business_date") == "2026-10-04"
          and ent.get("export_stamp") == E_REAL[-1]["export_stamp"]
          and ent.get("note") == "an empty day — nothing for the sale-bill route (F-731); the door already has it", dict(ent, note="..."))
    check("a dry run removes no file: the stand-in _NEEDS_ATTENTION.txt is still there", os.path.exists(os.path.join(S_new, "_NEEDS_ATTENTION.txt")))
    sn2 = send("new", S_new, dry=False)
    check("the same copy, send for real (nothing is left to send, so nothing is posted -- the URL given is a dead local port): exit 0 and "
          "the stale _NEEDS_ATTENTION.txt is gone", sn2["rc"] == 0 and sn2["nothing"] and not os.path.exists(os.path.join(S_new, "_NEEDS_ATTENTION.txt")),
          (sn2["rc"], sn2["tosend"]))
    T = dt.date(2030, 1, 5)
    po_, pn_ = G["old"].build_picture(S_old, os.path.join(S_old, "no_log.txt"), today=T), G["new"].build_picture(S_new, os.path.join(S_new, "no_log.txt"), today=T)
    lo = [l for l in po_["lines"] if l.startswith("2030-01-03")]
    ln = [l for l in pn_["lines"] if l.startswith("2030-01-03")]
    check("status (the picture, as of an invented 05-01-2030): OLD lists the empty weekday as NOT SENT; NEW no longer lists it (on server: yes) "
          "-- so _UPLOAD_NOW is not refilled with it", len(lo) == 1 and "NOT SENT" in lo[0] and [d.isoformat() for d, _m in po_["unsent"]] == ["2030-01-03"]
          and len(ln) == 1 and "NOT SENT" not in ln[0] and pn_["unsent"] == [], (lo, ln))
    up = os.path.join(W, "upload_new")
    placed = G["new"].refresh_upload_folder(S_new, up, pn_)
    check("refresh_upload_folder on the NEW picture copies nothing", placed == [])
    D_old, D_new = scratch("det_old", True), scratch("det_new", True)
    do, dn = send("old", D_old), send("new", D_new)
    check("with an invented DETAIL sheet (%s, 40 rows) waiting: NEW sends exactly that one -- a sheet with bill rows is never touched by the rule; "
          "OLD would send it and the two empty ones" % inv_d[:8],
          dn["tosend"] == [inv_d[:8]] and sorted(dn["empty"]) == sorted([e_md5[:8], inv_e[:8]]) and sorted(do["tosend"]) == sorted([e_md5[:8], inv_e[:8], inv_d[:8]]),
          (dn["tosend"], do["tosend"]))
    ds = G["new"].delivered_stamps({"sent": {e_md5: dict(ent)}}, {e_md5: E_REAL[-1]})
    check("an empty_day entry is NOT a delivery (delivered_stamps ignores it): a later real DETAIL sheet of that date is still sent", ds == {}, ds)
    st = subprocess.run([sys.executable, "-B", os.path.join(W, "marg_gate_new.py"), "selftest"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    so_ = subprocess.run([sys.executable, "-B", os.path.join(W, "marg_gate_old.py"), "selftest"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    check("marg_gate's own selftest: NEW %s (three more checks than OLD %s)" % (st.stdout.strip().splitlines()[-1], so_.stdout.strip().splitlines()[-1]),
          st.returncode == 0 and so_.returncode == 0 and "FAILED" not in st.stdout)
    return finish("manojz")


def finish(where):
    if FAILS:
        print("WALK_S482 %s RED -- %d of %d checks failed:" % (where, len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:200])
        return 1
    print("WALK_S482 %s GREEN -- %d checks" % (where, N[0]))
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe-chain":
        return probe_chain()
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe-eye":
        return probe_eye()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="where", required=True)
    m = sub.add_parser("manojz")
    for k in ("--work", "--archive", "--pull", "--old-read", "--new-read", "--old-gate", "--new-gate"):
        m.add_argument(k, required=True)
    s = sub.add_parser("server")
    for k in ("--kit", "--work", "--kits", "--ingest-new", "--ingest-old", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine", "--duty-map"):
        s.add_argument(k, required=True)
    s.add_argument("--expect", default="")
    a = ap.parse_args()
    return manojz(a) if a.where == "manojz" else server(a)


if __name__ == "__main__":
    sys.exit(main() or 0)
