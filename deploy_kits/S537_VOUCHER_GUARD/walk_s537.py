#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s537.py -- kit S537_VOUCHER_GUARD: the walk (the brief's section 4), on the server, on scratch copies only.

    python3 -B walk_s537.py --kit DIR --work /tmp/... --run DIR --por DIR --db finance.db --adb assets.db --spine spine.db
                            --map-old DUTY_MAP.json(v11) --map-new DUTY_MAP.json(v12, built)

  run       the installer's scratch layout: <run>/new/finance (the five built files), <run>/old/finance (the box as it is), each with
            marg_ingest beside it.
  por       a scratch copy of /root/portal's code; the walk writes its OWN secret and user store there (never the live ones).
  db/adb    backup-API copies of finance.db and assets.db; spine: of the LIVE spine.db.  Every probe works on its own further copies.
Probes run as fresh processes per side (NEW / OLD), signed in through the walk-only portal as amir and as the owner, with ORDER_PUSH_STUB,
a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a phone.  The walk's own rows are found by key (W537 names, the made-up
count 9537001, the made-up round = the live newest round + 1), never by counting.  Every named control is the same probe on the OLD files and
is printed red.  The stage-C release case (c4) uses a proof stand-in for count #1's orthotic batches (answers "done" once every one is
entered) -- the walk tests the release, not the spine proof (S524/S528 walked it).  Scratch-only constructions (a DELETE of round 6 on a
copy for the settle case) are said where they are made; the live database is never opened by this file.
No person, phone or account number is in this file."""
import argparse
import datetime as dt
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
import traceback

TAG = "W537JSON "
USERS = {"amir": "staff", "manoj": "doctor"}
BASE_URL = "https://followup.dr-manoj.in"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ITEM = "ANKLE BINDER BAMBOO L"
RID = 9537001
VENDOR = "W537 VENDOR"
NORT = (2, "ISSUE", 10)
G = dict(A="W537 GUARD A TAB", B="W537 GUARD B TAB", C="W537 GUARD C TAB", R="W537 GUARD R TAB", DL="W537 ANKLE BINDER BAMBOO L",
         DM="W537 ANKLE BINDER BAMBOO M", E="W537 GUARD E TAB", X="W537 GUARD X TAB")
FIX_VOID = ("CREATE TABLE IF NOT EXISTS stock_voucher_void (id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL, round_no INTEGER NOT NULL, "
            "kind TEXT NOT NULL, batch_no INTEGER NOT NULL, by_user TEXT, at TEXT NOT NULL, reason TEXT)")
FIX_SETTLE = ("CREATE TABLE IF NOT EXISTS stock_voucher_settle (id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL, item TEXT NOT NULL, "
              "by_user TEXT, at TEXT NOT NULL, note TEXT)")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:1500] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def red(label, cond, got=None):
    """A control: the same probe on the OLD files must show the fault (printed RED)."""
    N[0] += 1
    print(("  RED  control: " if cond else "  FAIL control did not go red: ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append("control: " + label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def dmy_iso(s):
    m = re.match(r"^(\d\d)-(\d\d)-(\d{4})$", str(s or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else str(s or "")[:10]


def K(x):
    return [int(x[0]), str(x[1]), int(x[2])]


# ============================================================================================================== the probe (one per side)
def probe():
    SIDE, FIN, POR = os.environ["SIDE"], os.environ["FINDIR"], os.environ["PORDIR"]
    DB, ADB, BASE, ADB0 = os.environ["FINANCE_DB"], os.environ["ASSETS_DB"], os.environ["W537_BASE"], os.environ["W537_ADB0"]
    AFTER, MAP_OLD, MAP_NEW = os.environ.get("W537_AFTER", ""), os.environ["W537_MAP_OLD"], os.environ["W537_MAP_NEW"]
    NEW = SIDE == "new"
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    import shelf_figure as SF                                           # noqa: E402
    import loss_piles as LP                                             # noqa: E402
    import aaj_kaam as AK                                               # noqa: E402
    for m_ in (AD, SA, SW, SF, LP, AK):
        assert m_.__file__.startswith(FIN), m_.__file__
    assert NEW == hasattr(SA, "_void_sql"), "side %s: stock_app is not the expected one" % SIDE
    R = dict(side=SIDE)
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W537J"])["pw"]
    ck = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE_URL, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
    R["signed_in"] = {w: bool(ck[w]["Cookie"][len("clinic_sso="):]) for w in USERS}
    now = dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)
    TODAY = now.date().isoformat()

    def iso(d):
        return d.strftime("%Y-%m-%dT%H:%M:%S")

    def clear_caches():
        for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE"):
            if hasattr(SA, nm):
                getattr(SA, nm).clear()

    def load(src=None):
        copydb(src or BASE, DB)
        copydb(ADB0, ADB)
        clear_caches()

    def C():
        c = sqlite3.connect(DB, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def cols(c, t):
        return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t).fetchall()]

    def ins(c, table, row):
        row = dict(row)
        for _cid, name, typ, notnull, dflt, pk in c.execute("PRAGMA table_info(%s)" % table).fetchall():
            if notnull and dflt is None and not pk and name not in row:
                row[name] = 0 if "INT" in (typ or "").upper() else ""
        ks = [k for k in row if k in cols(c, table)]
        return c.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(ks), ", ".join("?" * len(ks))), [row[k] for k in ks]).lastrowid

    def GET(path, who):
        t0 = time.perf_counter()
        r = fc.get(path, base_url=BASE_URL, headers=ck[who])
        return r.status_code, r.get_data(), int((time.perf_counter() - t0) * 1000)

    def board(who):
        code, body, ms = GET("/finance/stock/api/pad/amir/1", who)
        try:
            j = json.loads(body.decode("utf-8"))
        except ValueError:
            j = {}
        return dict(code=code, bytes=len(body), ms=ms, keys=[[v.get("round_no"), v.get("kind"), v.get("batch_no")] for v in (j.get("vouchers") or [])],
                    stage=(j.get("stage") or {}), proof=(j.get("proof") or {}).get("hi"))

    def rep(c):
        clear_caches()
        d = SA._pad_report_data(c, 1)
        if c.in_transaction:
            c.commit()
        return d

    def block(name, fn):
        try:
            R[name] = fn()
        except Exception as e:                                          # noqa: BLE001
            R[name] = dict(error="%s: %s" % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-1500:])

    def map_sql(path):
        j = json.load(open(path, encoding="utf-8"))
        return [x for x in j["duties"] if x.get("id") == "amir.count_vouchers"][0]["due_sql"]

    def aaj_n(path):
        AK.DUTY_MAP = path
        rd = AK.build_all(DB)
        it = [x for x in rd.get("items") or [] if x.get("id") == "amir.count_vouchers"]
        return (it[0].get("n"), it[0].get("err")) if it else (None, "absent")

    def ensure_tables(c):
        if NEW:
            SA._voucher_ensure(c)
        else:
            c.execute(FIX_VOID)
            c.execute(FIX_SETTLE)
        c.commit()

    def void(c, k, who="W537"):
        if NEW:
            ok, w = SA._voucher_void(c, 1, k[0], k[1], k[2], who, "W537 walk")
        else:
            c.execute("INSERT INTO stock_voucher_void (count_id, round_no, kind, batch_no, by_user, at, reason) VALUES (1,?,?,?,?,?,?)",
                      (k[0], k[1], k[2], who, iso(now), "W537 walk"))
            ok, w = True, "raw"
        c.commit()
        return ok, w

    # ---------------------------------------------------------------------------------------------------- 1. the void
    def b1():
        load()
        c = C()
        mx = int(c.execute("SELECT MAX(round_no) FROM stock_voucher_line WHERE count_id=1").fetchone()[0] or 0)
        k7 = (mx + 1, "ISSUE", 1)
        ins(c, "stock_voucher_line", dict(count_id=1, round_no=k7[0], kind="ISSUE", batch_no=1, batches_n=1, line_no=1, section="Orthotics", family="",
                                          item=ITEM, packing="1*1", pack=1, marg_from=0, change=-1, marg_to=-1, counted=0, reason="W537 made-up round",
                                          made_by="W537", made_at=iso(now)))
        c.commit()
        ensure_tables(c)
        out = dict(k7=K(k7), live_max=mx)
        seq0 = SA._voucher_seq(c, 1)
        out["seq_k7"] = (seq0.get(k7) or (None,))[0]
        out["v11_pre"] = c.execute(map_sql(MAP_OLD)).fetchone()[0]
        out["v12_pre"] = c.execute(map_sql(MAP_NEW)).fetchone()[0]
        out["aaj12_pre"], out["aaj11_pre"] = aaj_n(MAP_NEW), aaj_n(MAP_OLD)
        st0 = SA.amir_stage(c, 1) or {}
        out["visible_pre"] = K(k7) in [K(k) for k in st0.get("visible") or []]
        out["board_pre"] = {w: (K(k7) in board(w)["keys"]) for w in ("amir", "manoj")}
        out["void"] = void(c, k7)
        out["void_rows"] = c.execute("SELECT COUNT(*) FROM stock_voucher_void WHERE count_id=1 AND round_no=? AND kind='ISSUE' AND batch_no=1", (k7[0],)).fetchone()[0]
        d = rep(c)
        vs = SA._voucher_state(c, d)
        out["state_rounds"] = [r["round_no"] for r in vs["rounds"]]
        out["state_flat"] = [[v.get("round_no"), v.get("kind"), v.get("batch_no")] for v in vs.get("vouchers_flat") or []]
        out["batches_has"] = k7 in SA._s446_batches(c, 1)
        ao = [o for o in SA.amir_vouchers_open(c) if int(o["count_id"]) == 1]
        out["open"] = dict(made=ao[0]["made"], open=ao[0]["open"], ortho=ao[0]["ortho"]) if ao else None
        st = SA.amir_stage(c, 1) or {}
        out["visible_has"] = K(k7) in [K(k) for k in st.get("visible") or []]
        out["A_total"] = (st.get("A") or {}).get("total")
        out["numbers_L"] = SA._voucher_numbers(c, 1).get(ITEM)
        seq1 = SA._voucher_seq(c, 1)
        out["seq_same"] = seq1 == seq0
        out["v11_post"] = c.execute(map_sql(MAP_OLD)).fetchone()[0]
        out["v12_post"] = c.execute(map_sql(MAP_NEW)).fetchone()[0]
        out["aaj12_post"], out["aaj11_post"] = aaj_n(MAP_NEW), aaj_n(MAP_OLD)
        out["board"] = {w: board(w) for w in ("amir", "manoj")}
        out["board_has"] = {w: (K(k7) in out["board"][w]["keys"]) for w in ("amir", "manoj")}
        out["xlsx"] = GET("/finance/stock/api/pad/vouchers/1/%d.xlsx" % k7[0], "manoj")[0]
        code, body, _ms = GET("/finance/stock/api/statement/1", "manoj")
        txt = body.decode("utf-8", "replace")
        lab = "STOCK ISSUE voucher %s" % out["seq_k7"]
        out["statement"] = dict(code=code, has=(lab in txt), lab=lab)
        if NEW:
            n0 = c.execute("SELECT COUNT(*) FROM stock_voucher_void").fetchone()[0]
            ent = sorted(SA._s446_entered(c, 1))
            out["void_entered"] = SA._voucher_void(c, 1, ent[0][0], ent[0][1], ent[0][2], "W537", "walk") if ent else None
            out["void_entered_key"] = K(ent[0]) if ent else None
            out["void_none"] = SA._voucher_void(c, 1, 999, "ISSUE", 1, "W537", "walk")
            out["void_twice"] = SA._voucher_void(c, 1, k7[0], "ISSUE", 1, "W537", "walk")
            c.commit()
            out["void_rows_delta"] = c.execute("SELECT COUNT(*) FROM stock_voucher_void").fetchone()[0] - n0
        rr = fc.post("/finance/stock/api/pad/vouchers/1/entered", base_url=BASE_URL, headers=ck["manoj"],
                     json=dict(round=k7[0], kind="ISSUE", batch=1, marg_voucher_no="W537-%d" % k7[0]))
        jj = rr.get_json(silent=True) or {}
        out["enter"] = dict(code=rr.status_code, message=jj.get("message"), error=jj.get("error"))
        c.close()
        return out
    block("b1", b1)

    # ---------------------------------------------------------------------------------------------------- 2. settled stays settled
    def b2():
        load()
        c = C()
        n6 = c.execute("SELECT COUNT(*) FROM stock_voucher_line WHERE count_id=1 AND round_no=6").fetchone()[0]
        c.execute("DELETE FROM stock_voucher_line WHERE count_id=1 AND round_no=6")        # SCRATCH COPY ONLY: the state before round 6
        c.commit()
        ensure_tables(c)
        d = rep(c)
        out = dict(round6_lines=n6)
        out["pend_L"] = [[p["item"], p["change"]] for p in SA._voucher_pending(c, d, section="Orthotics") if p["item"] == ITEM]
        if NEW:
            out["held_L"] = [[h["item"], h["change"], h.get("marg_now")] for h in SA._voucher_held(c, d, section="Orthotics") if h["item"] == ITEM]
            c.execute("INSERT INTO stock_voucher_settle (count_id, item, by_user, at, note) VALUES (1,?,?,?,?)", (ITEM, "W537", iso(now), "W537 walk"))
            c.commit()
            d = rep(c)
            out["pend_L_settled"] = [[p["item"], p["change"]] for p in SA._voucher_pending(c, d, section="Orthotics") if p["item"] == ITEM]
            out["held_L_settled"] = [[h["item"], h["change"]] for h in SA._voucher_held(c, d, section="Orthotics") if h["item"] == ITEM]
        c.close()
        return out
    block("b2", b2)

    # ---------------------------------------------------------------------------------------------------- 3. the guard
    real_word, real_swap = SA._word_vouchers, SA._swap_vouchers
    NEED = {}

    def word_v(d):
        if int(d.get("count_id") or 0) == RID:
            return [dict(item=n, change=v, word=dict(label="W537 word")) for n, v in NEED.items()]
        return real_word(d)

    def swap_v(d):
        return [] if int(d.get("count_id") or 0) == RID else real_swap(d)
    SA._word_vouchers, SA._swap_vouchers = word_v, swap_v

    def newest(c):
        ds = [r[0] for r in c.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
        return max(ds, key=dmy_iso)

    def snap(c, as_on, item, qty):
        ins(c, "stock_snapshot", dict(as_on=as_on, item=item, qty=qty, packing="1*10", pack_size=10, loaded_at=iso(now), source="W537"))

    def synth(c, need, marg=None):
        NEED.clear()
        NEED.update(need)
        return dict(count_id=RID, day="W537", differences=[dict(item=n, marg=(marg or {}).get(n, 0), packing="1*10", pack=10, counted=0,
                                                                 diff=v, mrp_p=None) for n, v in need.items()])

    def lines(c, d):
        if NEW:
            o, h, u = SA._voucher_lines(c, d)
            return ([[x["item"], x["change"]] for x in o], [[x["item"], x["change"], x.get("marg_now"), x.get("as_on")] for x in h],
                    [x["item"] for x in u], (o, h, u))
        o = SA._voucher_pending(c, d)
        return [[x["item"], x["change"]] for x in o], None, None, (o, [], [])

    def b3():
        load()
        c = C()
        N_ = newest(c)
        out = dict(newest=N_)
        for k, q in (("A", 0), ("B", 2), ("C", 1), ("R", -34), ("DL", 0), ("DM", 1)):
            snap(c, N_, G[k], q)
        ins(c, "stock_voucher_line", dict(count_id=RID, round_no=1, kind="ISSUE", batch_no=1, batches_n=1, line_no=1, section="Medicines", family="",
                                          item=G["C"], packing="1*10", pack=10, marg_from=1, change=-1, marg_to=0, counted=0, reason="W537 frozen",
                                          made_by="W537", made_at=iso(now)))
        c.commit()
        ensure_tables(c)
        d = synth(c, {G["A"]: -1, G["B"]: -1, G["C"]: -2, G["R"]: 7, G["DL"]: -1, G["E"]: -1})
        rows0 = {t: c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("stock_voucher_line", "stock_voucher_void", "stock_voucher_settle",
                                                                                     "stock_stage_event", "stock_watch_ask")}
        tc0 = c.total_changes
        off, held, unread, raw = lines(c, d)
        out["writes"] = c.total_changes - tc0
        out["rows_same"] = rows0 == {t: c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in rows0}
        out.update(offered=off, held=held, unread=unread)
        out["clip_same"] = G["DL"][:20] == G["DM"][:20]
        try:
            sp = SW.Spine()
            out["spine_key_same"] = sp.key(G["DL"]) == sp.key(G["DM"])
        except Exception as e:                                          # noqa: BLE001
            out["spine_key_same"] = "n/a: %s" % e
        if NEW:
            stf = dict(count_id=RID, stage="A", A=dict(total=1, entered=0, open=1, pending=len(raw[0]), held=raw[1], unread=len(raw[2]), proof=None),
                       renames_visible=False)
            out["owner_lines"] = [l["text"] for l in SA._s521_stage_words(c, stf).get("owner_lines") or [] if "W537" in l["text"] or "not readable" in l["text"]]
        rno, n = SA._voucher_make(c, d, dict(user="W537"))
        out["made"] = dict(round=rno, lines=n, items=sorted(r[0] for r in c.execute("SELECT item FROM stock_voucher_line WHERE count_id=? AND round_no=?", (RID, rno or -1))))
        c.close()
        return out
    block("b3", b3)

    def b3c():
        """(c3) the newest closing by its real date, never MAX(as_on); a partial newest day reads 'not readable', never an older figure."""
        load()
        c = C()
        N_ = newest(c)
        snap(c, "30-09-2026", G["X"], 5)
        snap(c, N_, G["X"], 0)
        c.commit()
        ensure_tables(c)
        out = dict(newest=N_, max_text=c.execute("SELECT MAX(as_on) FROM stock_snapshot").fetchone()[0], latest=SF.latest_snapshot(c)[0])
        d = synth(c, {G["X"]: -1})
        out["whole"] = lines(c, d)[:3]
        snap(c, "31-12-2026", "W537 DUMMY", 1)
        c.commit()
        out["latest_partial"] = SF.latest_snapshot(c)[0]
        out["partial"] = lines(c, d)[:3]
        c.close()
        return out
    block("b3c", b3c)

    # ---------------------------------------------------------------------------------------------------- 3 (c4). the stage-C release
    def b3r():
        load()
        c = C()
        real_proof = SA._s446_proof

        def proof(con, root, keys, ent, batches):
            if int(root) == 1 and keys and all("Orthotics" in (batches.get(k) or {}).get("secs", set()) for k in keys):
                if any(k not in ent for k in keys):
                    return dict(state="wait", rows=[], text="")
                return dict(state="done", rows=[], unseen=[], as_before="", as_after="W537 stand-in", last_at=iso(now), items=len(keys), proven_on={}, text="")
            return real_proof(con, root, keys, ent, batches)
        SA._s446_proof = proof
        try:
            ensure_tables(c)
            rel0 = c.execute("SELECT COUNT(*) FROM stock_stage_event WHERE count_id=1 AND stage='C' AND event='release'").fetchone()[0]
            if NEW:                                                     # the data step's two rows, through the door
                out = dict(void=void(c, (6, "ISSUE", 1)))
                c.execute("INSERT INTO stock_voucher_settle (count_id, item, by_user, at, note) VALUES (1,?,?,?,?)", (ITEM, "W537", iso(now), "W537 walk"))
            else:                                                       # the old files cannot void: round 6 entered on the copy, so A clears too
                out = dict(entered6=ins(c, "stock_voucher_entered", dict(count_id=1, round_no=6, kind="ISSUE", batch_no=1, marg_voucher_no="W537-6",
                                                                         entered_on=TODAY, by_user="amir", at=iso(now))))
            c.commit()
            clear_caches()
            st = SA.amir_stage(c, 1) or {}
            A, Cc = st.get("A") or {}, st.get("C") or {}
            refs = [r[0] for r in c.execute("SELECT ref FROM stock_stage_event WHERE count_id=1 AND stage='C' AND event='release' ORDER BY id").fetchall()]
            out.update(rel_before=rel0, stage=st.get("stage"), A=dict(open=A.get("open"), pending=A.get("pending"), held=len(A.get("held") or [])),
                       lot1=[K(SA._s446_unkey(x)) for x in (refs[0] if refs else "").split(",") if x], n_lots=len(refs),
                       unreleased=Cc.get("unreleased"), per=Cc.get("per"))
            batches = SA._s446_batches(c, 1)
            med = [k for k, b in batches.items() if "Orthotics" not in b["secs"]]
            out["med"] = len(med)
            out["med_order"] = [K(k) for k in sorted(med, key=lambda k: (k[0], k[1] != "ISSUE", k[2]))]
            out["entered_med"] = [K(k) for k in SA._s446_entered(c, 1) if k in set(med)]
            if NEW:
                out["held"] = [[K(h["key"]), h["item"], h["change"], h.get("marg_now"), h.get("seq"), h.get("as_on")] for h in Cc.get("held") or [] if h.get("key")]
                out["held_pending"] = [[h["item"], h["change"], h.get("marg_now")] for h in Cc.get("held") or [] if not h.get("key")]
                hb, un = SA._voucher_held_batches(c, 1, med, batches)
                out["all_med_held"] = sorted(K(k) for k in hb)
                out["all_med_unread"] = len(un)
                out["owner_lines"] = [l["text"] for l in SA._s521_stage_words(c, st).get("owner_lines") or [] if "not given to Amir" in l["text"] or "not readable" in l["text"]]
                out["owner_en"] = SA._s521_stage_words(c, st).get("owner_en")
            more = []
            for _i in range(8):
                n = SA._s452_release(c, 1, "W537", "walk")
                more.append(n)
                if not n:
                    break
            rel = set()
            for r in c.execute("SELECT ref FROM stock_stage_event WHERE count_id=1 AND stage='C' AND event='release'").fetchall():
                rel.update(SA._s446_unkey(x) for x in (r[0] or "").split(",") if x)
            out["more"] = more
            out["nort_released"] = NORT in rel
            clear_caches()
            st2 = SA.amir_stage(c, 1) or {}
            out["unreleased_after"] = (st2.get("C") or {}).get("unreleased")
            out["stage_after"] = st2.get("stage")
            out["board_more"] = board("amir")["stage"]
        finally:
            SA._s446_proof = real_proof
        c.close()
        return out
    block("b3r", b3r)

    # ---------------------------------------------------------------------------------------------------- 4. the arrival tied to its bill
    def b4():
        load()
        c = C()
        oid = ins(c, "purchase_order", dict(created_at=iso(now - dt.timedelta(days=6)), created_by="W537", vendor=VENDOR, status="sent"))
        lid = ins(c, "purchase_order_line", dict(order_id=oid, item="W537 ITEM", packs=1, pack_size=1, units=1, supplied=1, arrived_by="W537",
                                                 arrived_at=iso(now - dt.timedelta(days=5)), billed_bill_no="W537-B1", billed_date=TODAY))
        c.commit()
        out = {}

        def look(tag):
            L = SW.bill_pending_lines(c)
            ny = [l.get("text") or "" for l in AD.needs_you_lines(c)]
            out[tag] = dict(rows=[x.get("vendor") for x in L if x.get("vendor") == VENDOR], yuvika=[x.get("text") for x in L if "YUVIKA" in str(x.get("vendor")).upper()],
                            owner=[t for t in ny if VENDOR in t], owner_yuvika=[t for t in ny if "YUVIKA" in t.upper()])
        look("tied")
        c.execute("UPDATE purchase_order_line SET billed_bill_no=NULL WHERE id=?", (lid,))
        c.commit()
        look("untied")
        c.close()
        return out
    block("b4", b4)

    # ---------------------------------------------------------------------------------------------------- 5. not broken (after the data step)
    def b5():
        if not NEW or not AFTER:
            return dict(skipped=True)
        load(AFTER)
        c = C()
        st = SA.amir_stage(c, 1) or {}
        A = st.get("A") or {}
        out = dict(stage=st.get("stage"), A=dict(total=A.get("total"), entered=A.get("entered"), open=A.get("open"), pending=A.get("pending"),
                                                 held=len(A.get("held") or []), proof=(A.get("proof") or {}).get("state")))
        out["board"] = {w: board(w) for w in ("amir", "manoj")}
        out["hub_api"] = GET("/finance/stock/api/pad/hub/1", "manoj")[0]
        out["hub_page"] = GET("/finance/stock/page/hub?count=1", "manoj")[0]
        code, body, ms = GET("/finance/sanjeevni/api/needs-you", "manoj")
        try:
            j = json.loads(body.decode("utf-8"))
        except ValueError:
            j = {}
        ls = [l for l in (j.get("lines") or []) if isinstance(l, dict)]
        out["needs"] = dict(code=code, n=len(ls), shapes_ok=all(isinstance(l.get("text"), str) and l.get("text") for l in ls),
                            keys=sorted({k for l in ls for k in l}), mine=[l.get("text") for l in ls if re.search(r"Count #|not given to Amir|YUVIKA|not readable", str(l.get("text")))])
        out["steps"] = {n: GET("/finance/amir/step/%d" % n, "amir")[0] for n in range(1, 8)}
        out["xlsx6"] = GET("/finance/stock/api/pad/vouchers/1/6.xlsx", "manoj")[0]
        out["xlsx5"] = GET("/finance/stock/api/pad/vouchers/1/5.xlsx", "manoj")[0]
        out["xlsx_amir"] = GET("/finance/stock/api/pad/amir/1.xlsx", "manoj")[0]
        tc0 = c.total_changes
        r1 = LP.receive_close(c, 1, "W537")
        tc1 = c.total_changes
        r2 = LP.receive_close(c, 1, "W537")
        tc2 = c.total_changes
        out["loss"] = dict(first=(r1 or {}).get("round_no") if r1 else None, first_writes=tc1 - tc0, second=r2, second_writes=tc2 - tc1)
        c.close()
        return out
    block("b5", b5)

    print(TAG + json.dumps(R, default=str))


# ============================================================================================================== the walk
def run_probe(a, side, Wd, store, secret, pw, after):
    fin = os.path.join(a.run, side, "finance")
    ing = os.path.join(a.run, side, "marg_ingest")
    wd = os.path.join(Wd, "probe_%s" % side)
    for sub in ("noring", "nomarg"):
        os.makedirs(os.path.join(wd, sub))
    dbp, adbp, spp = [os.path.join(wd, "w537_%s.db" % x) for x in ("app", "assets", "spine")]
    copydb(a.db, dbp)
    copydb(a.adb, adbp)
    copydb(a.spine, spp)
    env = dict(os.environ, SIDE=side, FINDIR=fin, INGDIR=ing, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp,
               W537_BASE=a.db, W537_ADB0=a.adb, W537_AFTER=after or "", W537_MAP_OLD=a.map_old, W537_MAP_NEW=a.map_new,
               DUTY_MAP_JSON=(a.map_new if side == "new" else a.map_old),
               FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store,
               TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W537J=json.dumps(dict(pw=pw)),
               MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"),
               ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"),
               ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
               CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
    for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE",
              "FINANCE_CRON_TOKEN", "AMIR_BILLS_FROM"):
        env.pop(k, None)
    t0 = time.time()
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True, timeout=3000)
    js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
    print("   the %s probe ran %d s (exit %s)" % (side, int(time.time() - t0), p.returncode))
    if not js:
        print("-- the %s probe did not finish; its last lines:" % side)
        for l in p.stdout.splitlines()[-40:]:
            print("   " + mask(l)[:300])
        return None
    return json.loads(js[-1][len(TAG):])


def errs(R):
    return {k: v.get("error") for k, v in R.items() if isinstance(v, dict) and v.get("error")}


def counts(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    out = {}
    for t in ("stock_voucher_void", "stock_voucher_settle", "stock_watch_ask", "stock_stage_event", "audit_log"):
        try:
            out[t] = c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        except sqlite3.Error:
            out[t] = None
    out["_tables"] = sorted(r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'"))
    c.close()
    return out


def data_step(a, fin, db, spine, *extra):
    env = dict(os.environ, SPINE_DB=spine, FINANCE_DB=db, ORDER_PUSH_STUB=os.path.join(os.path.dirname(db), "pushes.jsonl"),
               RING_PORTAL_DIR=os.path.join(os.path.dirname(db), "noring"))
    os.makedirs(env["RING_PORTAL_DIR"], exist_ok=True)
    p = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "data_s537.py"), "--db", db, "--finance", fin] + list(extra), env=env, cwd=fin,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=1800)
    return p.returncode, p.stdout


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe":
        return probe()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--run", "--por", "--db", "--adb", "--spine", "--map-old", "--map-new"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/") and os.path.abspath(a.db).startswith("/tmp/"), "refusing a non-scratch path"
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W537 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for role in ("staff", "doctor"):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])
    fin_new, fin_old = os.path.join(a.run, "new", "finance"), os.path.join(a.run, "old", "finance")

    # ------------------------------------------------------------------------------------------------------------ 6. the greps
    print("-- 6 every FROM stock_voucher_line site in finance (and spine) and the portal, NEW bytes, with its decision (OLD: the control)")
    BY_DESIGN = (
        ("SELECT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=? GROUP BY round_no, kind, batch_no", "_voucher_seq: the numbering never shifts (R1-10)"),
        ("rno = int((con.execute(\"SELECT MAX(round_no) FROM stock_voucher_line WHERE count_id=?\"", "_voucher_make: the next round's number (a voided number is never reused)"),
        ("one(\"SELECT MAX(round_no) FROM stock_voucher_line WHERE count_id=?\", int(root))", "_report_cached's stamp: reads no voucher table for the report (R1-14)"),
        ("SELECT MAX(count_id) FROM stock_voucher_line", "_s446_root: the newest count with lines"),
        ("SELECT 1 FROM stock_voucher_line WHERE count_id=? AND round_no=? AND kind=? AND batch_no=? LIMIT 1", "_voucher_void: the void door's own existence check"),
        ("FROM stock_voucher_line l GROUP BY l.count_id, l.round_no, l.kind, l.batch_no) b WHERE substr(b.made_at", "aaj_seed 470 (the parent's SQL): left for later, by the brief"),
    )

    def sites(folders):
        out = []
        for fo in folders:
            if not os.path.isdir(fo):
                continue
            for fn in sorted(os.listdir(fo)):
                if not (fn.endswith(".py") or fn.endswith(".html")):
                    continue
                ls = io.open(os.path.join(fo, fn), encoding="utf-8", errors="replace").read().split("\n")
                for i, l in enumerate(ls):
                    if "FROM stock_voucher_line" in l:
                        win = "\n".join(ls[i:i + 2])
                        if "_void_sql(" in win:
                            dec = "filtered (_void_sql)"
                        elif "+ vf" in l and "_void_sql(" in "\n".join(ls[max(0, i - 5):i]):
                            dec = "filtered (_void_sql, through vf)"
                        else:
                            dec = next((w for s, w in BY_DESIGN if s in l), None)
                        out.append((fn, i + 1, dec, l.strip()[:110]))
        return out
    sn = sites([fin_new, os.path.join(fin_new, "spine"), a.por])
    so = sites([fin_old, os.path.join(fin_old, "spine"), a.por])
    for fn, ln, dec, l in sn:
        print("   %-20s %5d  %-62s %s" % (fn, ln, (dec or "!! UNDECIDED")[:62], l[:70]))
    def filt(s):
        return bool(s[2]) and s[2].startswith("filtered")
    check("6: every FROM stock_voucher_line site has a decision (%d sites: %d filtered, %d not by design)" % (
        len(sn), sum(1 for s in sn if filt(s)), sum(1 for s in sn if s[2] and not filt(s))), all(s[2] for s in sn), [s for s in sn if not s[2]])
    nf = {s[0] for s in sn if filt(s)}
    check("6: the brief's eight sites are filtered -- stock_app's six (_voucher_frozen, _voucher_state, the entered door, _voucher_numbers, "
          "amir_vouchers_open, _s446_batches) + the guard's own read, shelf_figure, stock_statement: %d filtered in %s" % (sum(1 for s in sn if filt(s)), sorted(nf)),
          sum(1 for s in sn if s[0] == "stock_app.py" and filt(s)) == 7 and "shelf_figure.py" in nf and "stock_statement.py" in nf)
    red("6 OLD: no site honours a void (%d filtered of %d)" % (sum(1 for s in so if filt(s)), len(so)), sum(1 for s in so if filt(s)) == 0 and len(so) > 0)
    sw_new = io.open(os.path.join(fin_new, "stock_watch.py"), encoding="utf-8").read()
    sw_old = io.open(os.path.join(fin_old, "stock_watch.py"), encoding="utf-8").read()
    check("6: stock_watch.bill_pending_lines carries COALESCE(l.billed_bill_no,'') = '' once", sw_new.count("COALESCE(l.billed_bill_no,'') = ''") == 1)
    red("6 OLD: it does not", sw_old.count("COALESCE(l.billed_bill_no,'') = ''") == 0)
    jm = json.load(open(a.map_new, encoding="utf-8"))
    jo = json.load(open(a.map_old, encoding="utf-8"))
    sq = [x for x in jm["duties"] if x["id"] == "amir.count_vouchers"][0]["due_sql"]
    check("6: DUTY_MAP v12 (kit %s): amir.count_vouchers' due_sql names stock_voucher_void once, one line, no ';'" % jm.get("kit"),
          jm.get("version") == 12 and sq.count("stock_voucher_void") == 1 and ";" not in sq and "\n" not in sq)
    red("6 OLD: the v11 map (version %s) does not" % jo.get("version"), jo.get("version") == 11 and "stock_voucher_void" not in json.dumps(jo))

    # ------------------------------------------------------------------------------------------------------------ 5. the data step
    print("-- 5 the data step on scratch copies (NEW finance folder; the scratch spine for the spot count)")
    dsw = os.path.join(Wd, "data")
    os.makedirs(dsw)
    dry_db = os.path.join(dsw, "dry.db")
    copydb(a.db, dry_db)
    c0 = counts(dry_db)
    rc, outp = data_step(a, fin_new, dry_db, a.spine, "--dry")
    for l in outp.splitlines():
        if l.startswith("DATA_S537"):
            print("   " + mask(l)[:300])
    c1 = counts(dry_db)
    check("5: --dry exits 0, says DRY, skips step 3, and writes nothing (row counts of the void, settle, ask, stage-event and audit tables; the table "
          "list) %s" % {k: v for k, v in c0.items() if k != "_tables"}, rc == 0 and "DATA_S537: DRY -- rolled back" in outp and "3 skipped" in outp and c0 == c1,
          dict(rc=rc, before={k: v for k, v in c0.items() if k != "_tables"}, after={k: v for k, v in c1.items() if k != "_tables"},
               tables_moved=sorted(set(c1["_tables"]) ^ set(c0["_tables"]))))
    check("5: --dry's step 4 (on its own scratch copy): round 6 absent from the batches, the orthotic pending lines 0",
          "round 6 in the batches: False" in outp and "orthotic pending lines: 0 " in outp, [l for l in outp.splitlines() if "DATA_S537: 4" in l][:6])
    real_db = os.path.join(dsw, "after.db")
    copydb(a.db, real_db)
    rcs, outs = data_step(a, fin_new, real_db, a.spine, "--schema-only")
    print("   " + mask(outs.strip().splitlines()[-1] if outs.strip() else "")[:200])
    cs = counts(real_db)
    check("5: --schema-only lays the two tables (and writes no row)", rcs == 0 and "stock_voucher_void" in cs["_tables"] and "stock_voucher_settle" in cs["_tables"]
          and cs["stock_voucher_void"] == 0 and cs["stock_voucher_settle"] == 0, (rcs, outs[-300:]))
    rcr, outr = data_step(a, fin_new, real_db, a.spine)
    for l in outr.splitlines():
        if l.startswith("DATA_S537"):
            print("   " + mask(l)[:300])
    cr = counts(real_db)
    rr = sqlite3.connect("file:%s?mode=ro" % real_db, uri=True)
    vrow = rr.execute("SELECT count_id, round_no, kind, batch_no, by_user, reason FROM stock_voucher_void").fetchall()
    srow = rr.execute("SELECT count_id, item, by_user, note FROM stock_voucher_settle").fetchall()
    arow = rr.execute("SELECT item, by FROM stock_watch_ask WHERE done_at IS NULL AND by = 'S537 owner 12-Oct'").fetchall()   # ask() names it as the spine does
    rr.close()
    check("5: the data step commits: one void row (count 1, round 6, ISSUE, batch 1, by manoj), one settle row (%s), one open spot-count ask %s"
          % (ITEM, [tuple(x) for x in arow]), rcr == 0 and "DATA_S537: committed" in outr and [tuple(x[:5]) for x in vrow] == [(1, 6, "ISSUE", 1, "manoj")]
          and [tuple(x[:3]) for x in srow] == [(1, ITEM, "manoj")] and len(arow) == 1, dict(rc=rcr, v=vrow, s=srow, a=arow))
    check("5: step 4 after the data step: round 6 absent, %s not held (settled), orthotic pending 0" % ITEM,
          "round 6 in the batches: False" in outr and "orthotic pending lines: 0 " in outr and ("%s held: False" % ITEM) in outr,
          [l for l in outr.splitlines() if "DATA_S537: 4" in l][:8])
    rc2, out2 = data_step(a, fin_new, real_db, a.spine)
    cr2 = counts(real_db)
    check("5: a second run is idempotent (void and settle skipped, the ask already listed; no row added)", rc2 == 0 and "already voided -- skipped" in out2
          and "already settled" in out2 and {k: v for k, v in cr2.items() if k not in ("stock_stage_event", "audit_log")} == {k: v for k, v in cr.items() if k not in ("stock_stage_event", "audit_log")},
          [l for l in out2.splitlines() if l.startswith("DATA_S537: 1") or l.startswith("DATA_S537: 2") or l.startswith("DATA_S537: 3")])
    ent_db = os.path.join(dsw, "entered.db")
    copydb(a.db, ent_db)
    ce = sqlite3.connect(ent_db)
    ce.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (1,6,'ISSUE',1,'W537-6',?, 'amir', ?)",
               (dt.date.today().isoformat(), dt.datetime.now().isoformat(timespec="seconds")))
    ce.commit()
    ce.close()
    ce0 = counts(ent_db)
    rce, oute = data_step(a, fin_new, ent_db, a.spine)
    check("5: voucher 29 ENTERED (a copy) -> DATA_S537: STOP, exit 2, no void, no settle, no ask", rce == 2 and "DATA_S537: STOP" in oute and "ENTERED" in oute
          and counts(ent_db)["stock_voucher_void"] in (0, None) and counts(ent_db)["stock_voucher_settle"] in (0, None)
          and counts(ent_db)["stock_watch_ask"] == ce0["stock_watch_ask"], (rce, [l for l in oute.splitlines() if "STOP" in l][:2]))
    x_db = os.path.join(dsw, "extra.db")
    copydb(a.db, x_db)
    cx = sqlite3.connect(x_db)
    cx.execute("INSERT INTO stock_voucher_line (count_id, round_no, kind, batch_no, batches_n, line_no, section, family, item, packing, pack, marg_from, change, "
               "marg_to, counted, reason, made_by, made_at) VALUES (1,7,'ISSUE',1,1,1,'Orthotics','','W537 OTHER','1*1',1,0,-1,-1,0,'W537','W537',?)",
               (dt.datetime.now().isoformat(timespec="seconds"),))
    cx.commit()
    cx.close()
    rcx, outx = data_step(a, fin_new, x_db, a.spine)
    check("5: anything else in round >= 6 (a copy with a made-up round 7) -> DATA_S537: STOP, exit 2, nothing written", rcx == 2 and "DATA_S537: STOP" in outx
          and counts(x_db)["stock_voucher_void"] in (0, None), (rcx, [l for l in outx.splitlines() if "STOP" in l][:2]))
    rco, outo = data_step(a, fin_old, os.path.join(dsw, "dry.db"), a.spine, "--dry")
    check("5: the data step refuses the OLD finance folder (no _void_sql) -- nothing done", rco == 2 and "not the kit's stock_app" in outo, (rco, outo[-200:]))

    # ------------------------------------------------------------------------------------------------------------ the probes
    print("-- the probes (fresh processes, the walk-only portal session, each case on its own copy)")
    RN = run_probe(a, "new", Wd, store, secret, pw, real_db)
    RO = run_probe(a, "old", Wd, store, secret, pw, "")
    if RN is None or RO is None:
        check("both probes finished", False)
        return finish()
    check("both probes finished, no block raised", not errs(RN) and not errs(RO), dict(new=errs(RN), old=errs(RO)))
    for k, v in list(errs(RN).items()) + list(errs(RO).items()):
        print("   %s tb: %s" % (k, mask((RN.get(k) or RO.get(k) or {}).get("tb"))[-900:]))
    check("signed in as amir and the owner through the walk-only portal (both sides)", all(RN.get("signed_in", {}).values()) and all(RO.get("signed_in", {}).values()))

    # 1 -- the void
    n1, o1 = RN.get("b1") or {}, RO.get("b1") or {}
    k7 = n1.get("k7")
    print("-- 1 the void: a made-up unentered newest round on count #1 (round %s, ISSUE batch 1, %s -1; STOCK ISSUE voucher %s), then voided"
          % ((k7 or [None])[0], ITEM, n1.get("seq_k7")))
    check("1: before the void the made-up batch is on the board (amir, owner) and visible to the stage (NEW)", n1.get("visible_pre") and all((n1.get("board_pre") or {}).values()),
          (n1.get("visible_pre"), n1.get("board_pre")))
    check("1: the void door voided it (%s); one void row" % (n1.get("void"),), (n1.get("void") or [None])[0] is True and n1.get("void_rows") == 1)
    check("1: absent from _voucher_state (rounds %s) and its flat list" % n1.get("state_rounds"), k7 and k7[0] not in (n1.get("state_rounds") or [])
          and k7 not in (n1.get("state_flat") or []))
    red("1 OLD: _voucher_state still lists round %s" % (k7 or [None])[0], k7 and k7[0] in (o1.get("state_rounds") or []))
    check("1: absent from _s446_batches, the stage's visible (A total %s) and so the proof" % n1.get("A_total"), n1.get("batches_has") is False and n1.get("visible_has") is False)
    red("1 OLD: _s446_batches and the stage still carry it (A total %s)" % o1.get("A_total"), o1.get("batches_has") is True and o1.get("visible_has") is True
        and int(o1.get("A_total") or 0) == int(n1.get("A_total") or 0) + 1)
    check("1: amir_vouchers_open counts one batch fewer than the old (made %s / open %s vs %s / %s)" % ((n1.get("open") or {}).get("made"), (n1.get("open") or {}).get("open"),
          (o1.get("open") or {}).get("made"), (o1.get("open") or {}).get("open")), n1.get("open") and o1.get("open")
          and n1["open"]["made"] == o1["open"]["made"] - 1 and n1["open"]["open"] == o1["open"]["open"] - 1)
    for w in ("amir", "manoj"):
        bn, bo = (n1.get("board") or {}).get(w) or {}, (o1.get("board") or {}).get(w) or {}
        check("1 %s: the board answers 200 without the voided batch (%d vouchers, %s bytes)" % (w, len(bn.get("keys") or []), bn.get("bytes")),
              bn.get("code") == 200 and not (n1.get("board_has") or {}).get(w))
        red("1 OLD %s: the board shows it" % w, bo.get("code") == 200 and (o1.get("board_has") or {}).get(w))
    check("1: its round's xlsx is gone (%s)" % n1.get("xlsx"), n1.get("xlsx") == 404)
    red("1 OLD: the xlsx is served (%s)" % o1.get("xlsx"), o1.get("xlsx") == 200)
    check("1: the statement (200) carries no '%s'; _voucher_numbers for %s: %s" % ((n1.get("statement") or {}).get("lab"), ITEM, n1.get("numbers_L")),
          (n1.get("statement") or {}).get("code") == 200 and not (n1.get("statement") or {}).get("has")
          and ("STOCK ISSUE voucher %s" % n1.get("seq_k7")) not in (n1.get("numbers_L") or []))
    red("1 OLD: the statement names it", (o1.get("statement") or {}).get("has") is True and ("STOCK ISSUE voucher %s" % o1.get("seq_k7")) in (o1.get("numbers_L") or []))
    check("1: _voucher_seq unchanged for every batch (the voided one keeps its number, never shown)", n1.get("seq_same") is True)
    check("1: amir.count_vouchers v12 does not count it (v12 %s -> %s), v11 does (v11 %s -> %s)" % (n1.get("v12_pre"), n1.get("v12_post"), n1.get("v11_pre"), n1.get("v11_post")),
          n1.get("v12_pre") == n1.get("v11_pre") and n1.get("v12_post") == n1.get("v12_pre") - 1 and n1.get("v11_post") == n1.get("v11_pre"))
    a12p, a12q, a11q = n1.get("aaj12_pre") or [None], n1.get("aaj12_post") or [None], n1.get("aaj11_post") or [None]
    check("1: Amir's Aaj-ka-kaam build (aaj_kaam.build_all) with the v12 map counts it no longer (%s -> %s); with v11 %s" % (a12p[0], a12q[0], a11q[0]),
          a12p[0] is not None and a12q[0] == a12p[0] - 1 and a11q[0] == a12p[0], (a12p, a12q, a11q))
    en, eo = n1.get("enter") or {}, o1.get("enter") or {}
    check("1: entering the voided batch -> 400 'Yeh voucher ab nahi hai.' (%s)" % en, en.get("code") == 400 and en.get("message") == "Yeh voucher ab nahi hai.")
    red("1 OLD: the entry is accepted (%s)" % eo, eo.get("code") == 200)
    check("1: voiding an ENTERED batch %s -> refused %s; a batch that does not exist -> %s; a second void -> %s; no void row added by them (%s)"
          % (n1.get("void_entered_key"), n1.get("void_entered"), n1.get("void_none"), n1.get("void_twice"), n1.get("void_rows_delta")),
          n1.get("void_entered") == [False, "entered"] and n1.get("void_none") == [False, "no_such_batch"] and n1.get("void_twice") == [True, "already"]
          and n1.get("void_rows_delta") == 0)

    # 2 -- settle
    n2, o2 = RN.get("b2") or {}, RO.get("b2") or {}
    print("-- 2 settled stays settled (a copy before round 6: its %s line(s) removed on the scratch copy)" % n2.get("round6_lines"))
    red("2 OLD: the count-day rule raises %s again: %s" % (ITEM, o2.get("pend_L")), o2.get("pend_L") == [[ITEM, -1]])
    check("2: NEW before the settle row: not offered (%s), held by the guard (%s -- Marg 0)" % (n2.get("pend_L"), n2.get("held_L")),
          n2.get("pend_L") == [] and n2.get("held_L") == [[ITEM, -1, 0]])
    check("2: NEW with the settle row: nothing for %s -- not offered %s, not held %s" % (ITEM, n2.get("pend_L_settled"), n2.get("held_L_settled")),
          n2.get("pend_L_settled") == [] and n2.get("held_L_settled") == [])

    # 3 -- the guard
    n3, o3 = RN.get("b3") or {}, RO.get("b3") or {}
    print("-- 3 the guard (made-up items on the newest closing %s, a made-up count %d)" % (n3.get("newest"), RID))
    off = {x[0]: x[1] for x in n3.get("offered") or []}
    hel = {x[0]: x for x in n3.get("held") or []}
    unr = n3.get("unread") or []
    oof = {x[0]: x[1] for x in o3.get("offered") or []}
    check("3a: closing 0, sum -1 -> held (Marg 0), not offered", G["A"] in hel and G["A"] not in off and hel[G["A"]][2] == 0, hel.get(G["A"]))
    check("3b: closing 2, sum -1 -> offered", off.get(G["B"]) == -1)
    check("3c (R1-5): closing 1 with an unentered frozen -1 already, sum -1 more -> held", G["C"] in hel and G["C"] not in off, hel.get(G["C"]))
    check("3c2 (R2-3): a RECEIVE +7 on an item whose closing is -34 -> offered", off.get(G["R"]) == 7)
    check("3d (R1-2): two names on one 20-letter key (clip same %s; spine key same %s), L 0 / M 1, sum -1 on L -> held" % (n3.get("clip_same"), n3.get("spine_key_same")),
          n3.get("clip_same") is True and G["DL"] in hel and G["DL"] not in off)
    check("3e: no closing row for the name -> offered, listed unread (one summary line)", off.get(G["E"]) == -1 and unr == [G["E"]])
    ol = n3.get("owner_lines") or []
    print("   3 the owner's lines (NEW):")
    for t in ol:
        print("      %s" % mask(t)[:240])
    check("3: one owner line per held item (%d) in the brief's words, and ONE summary line 'closing not readable for 1 item(s) — guard not applied'" % len(hel),
          sum(1 for t in ol if "not given to Amir" in t and "the count-day sum asks" in t and "Marg's closing of" in t) == len(hel) == 3
          and sum(1 for t in ol if "closing not readable for 1 item(s) — guard not applied" in t) == 1
          and any(t.startswith("Count #%d: %s —" % (RID, G["A"])) for t in ol))
    check("3: the guard writes nothing (%s row changes; the five tables' counts the same)" % n3.get("writes"), n3.get("writes") == 0 and n3.get("rows_same") is True)
    mk = n3.get("made") or {}
    check("3a: _voucher_make freezes no held line (round %s froze %s)" % (mk.get("round"), mk.get("items")),
          not (set(mk.get("items") or []) & {G["A"], G["C"], G["DL"]}) and set(mk.get("items") or []) == {G["B"], G["R"], G["E"]})
    red("3 OLD: (a), (c), (d) offered: %s" % {k: oof.get(G[k]) for k in ("A", "C", "DL")}, all(oof.get(G[k]) == -1 for k in ("A", "C", "DL")))
    red("3a OLD: _voucher_make freezes the held line (%s)" % (o3.get("made") or {}).get("items"), G["A"] in ((o3.get("made") or {}).get("items") or []))
    n3c = RN.get("b3c") or {}
    w_, p_ = n3c.get("whole") or [[], [], []], n3c.get("partial") or [[], [], []]
    print("   3c3: MAX(as_on) as text = %s; the newest closing by its real date = %s; with a partial newer day = %s" % (n3c.get("max_text"), n3c.get("latest"), n3c.get("latest_partial")))
    check("3c3 (R2-1): the newest whole closing chosen by real date (%s), not MAX(as_on) (%s): X (30-09: 5, newest: 0) sum -1 -> held on Marg 0"
          % (n3c.get("latest"), n3c.get("max_text")), n3c.get("latest") == dmy_iso(n3c.get("newest")) and dmy_iso(n3c.get("max_text")) != n3c.get("latest")
          and [x[0] for x in w_[1] or []] == [G["X"]] and (w_[1] or [[None, None, None]])[0][2] == 0, w_)
    check("3c3: a partial newest day not printing X -> 'not readable' (offered, listed unread), never an older figure", n3c.get("latest_partial") == "2026-12-31"
          and [x[0] for x in p_[0] or []] == [G["X"]] and (p_[1] or []) == [] and (p_[2] or []) == [G["X"]], p_)
    nr, orr = RN.get("b3r") or {}, RO.get("b3r") or {}
    print("-- 3c4 the stage-C release on the install-day copy (NEW: the data step's void + settle; OLD: round 6 entered on the copy; both: the orthotic proof stand-in)")
    print("   NEW stage %s, A %s, %s med batches, first lot %d: %s" % (nr.get("stage"), nr.get("A"), nr.get("med"), len(nr.get("lot1") or []), nr.get("lot1")))
    print("   OLD stage %s, first lot %d: %s" % (orr.get("stage"), len(orr.get("lot1") or []), orr.get("lot1")))
    for t in nr.get("owner_lines") or []:
        print("      NEW owner line: %s" % mask(t)[:240])
    nk = K(NORT)
    held_keys = [h[0] for h in nr.get("held") or []]
    check("3c4 (R2-2): stage C reached; the first lot skips round 2 ISSUE batch 10 (NORTIMER TAB) and is still %s batches (the next passing one took its place)"
          % nr.get("per"), nr.get("stage") == "C" and nr.get("rel_before") == 0 and nk not in (nr.get("lot1") or [])
          and len(nr.get("lot1") or []) == len(orr.get("lot1") or []) and len(nr.get("lot1") or []) > 0)
    exp_next = [k for k in (nr.get("med_order") or []) if k not in (nr.get("entered_med") or []) and k != nk][:len(nr.get("lot1") or [])]
    check("3c4: the NEW lot = the old order less batch 10, with the next batch at its end", (nr.get("lot1") or []) == exp_next, dict(new=nr.get("lot1"), want=exp_next))
    red("3c4 OLD: the old release hands batch 10 to Amir", nk in (orr.get("lot1") or []), orr.get("lot1"))
    check("3c4: C['held'] holds exactly that batch by key -- NORTIMER TAB -10, Marg's closing holds 3 (%s)" % nr.get("held"),
          held_keys == [nk] and (nr.get("held") or [[None, None, None, None]])[0][1:4] == ["NORTIMER TAB", -10, 3])
    check("3c4: over EVERY medicine batch of the count, the guard fails exactly one: %s" % nr.get("all_med_held"), nr.get("all_med_held") == [nk])
    check("3c4: the owner's line names it with its voucher number (STOCK ISSUE voucher %s)" % ((nr.get("held") or [[None] * 5])[0][4]),
          any(t.startswith("Count #1: NORTIMER TAB (STOCK ISSUE voucher %s) — the count-day sum asks" % ((nr.get("held") or [[None] * 5])[0][4])) and "not given to Amir" in t
              for t in nr.get("owner_lines") or []))
    check("3c4: 'Aur voucher kholiye' (_s452_release) never releases it (%s) and the board's 'more' count leaves it out (unreleased after: %s; board %s)"
          % (nr.get("more"), nr.get("unreleased_after"), nr.get("board_more")), nr.get("nort_released") is False and nr.get("unreleased_after") == 0
          and int((nr.get("board_more") or {}).get("more") or 0) == 0)
    red("3c4 OLD: 'Aur voucher kholiye' releases it", orr.get("nort_released") is True)

    # 4 -- the arrival
    n4, o4 = RN.get("b4") or {}, RO.get("b4") or {}
    print("-- 4 an arrival tied to its bill (billed_bill_no set, tapped 5 days ago, the item missing from the spine)")
    check("4: tied -> not in bill_pending_lines, no D712 owner line", (n4.get("tied") or {}).get("rows") == [] and (n4.get("tied") or {}).get("owner") == [], n4.get("tied"))
    check("4: the same unset -> listed and the owner's D712 line", (n4.get("untied") or {}).get("rows") == [VENDOR] and len((n4.get("untied") or {}).get("owner") or []) == 1, n4.get("untied"))
    red("4 OLD: the tied line is listed (%s)" % (o4.get("tied") or {}).get("rows"), (o4.get("tied") or {}).get("rows") == [VENDOR])
    print("   4 install-day copy: YUVIKA rows NEW %s / OLD %s; owner lines NEW %s / OLD %s" % ((n4.get("tied") or {}).get("yuvika"), (o4.get("tied") or {}).get("yuvika"),
          (n4.get("tied") or {}).get("owner_yuvika"), (o4.get("tied") or {}).get("owner_yuvika")))
    check("4: the Yuvika arrival (tied to bill 672) is not listed on the install-day copy", (n4.get("tied") or {}).get("yuvika") == [] and (n4.get("tied") or {}).get("owner_yuvika") == [])

    # 5 -- not broken
    n5 = RN.get("b5") or {}
    print("-- 5 not broken: the install-day copy after the data step (NEW files)")
    print("   stage %s, A %s" % (n5.get("stage"), n5.get("A")))
    A5 = n5.get("A") or {}
    check("5: stage A open 0, pending 0 (A entered %s of %s; proof %s)" % (A5.get("entered"), A5.get("total"), A5.get("proof")), A5.get("open") == 0 and A5.get("pending") == 0)
    for w in ("amir", "manoj"):
        b = (n5.get("board") or {}).get(w) or {}
        check("5 %s: the board 200, round 6 absent (%d vouchers), payload %s bytes < 100 KB (%s ms)" % (w, len(b.get("keys") or []), b.get("bytes"), b.get("ms")),
              b.get("code") == 200 and not any(k[0] == 6 for k in b.get("keys") or []) and 0 < (b.get("bytes") or 0) < 100 * 1024)
    check("5: the hub (api, page) as the owner 200", n5.get("hub_api") == 200 and n5.get("hub_page") == 200, (n5.get("hub_api"), n5.get("hub_page")))
    nd = n5.get("needs") or {}
    for t in nd.get("mine") or []:
        print("      Needs-you: %s" % mask(t)[:240])
    check("5: Needs-you 200, every line has its text (%d lines; keys %s)" % (nd.get("n") or 0, nd.get("keys")), nd.get("code") == 200 and nd.get("shapes_ok"))
    check("5: Amir's steps 1-7 as amir 200", all(int(v) == 200 for v in (n5.get("steps") or {}).values()) and len(n5.get("steps") or {}) == 7, n5.get("steps"))
    check("5: the xlsx: round 6's 404 (voided), round 5's 200, Amir's board xlsx 200", n5.get("xlsx6") == 404 and n5.get("xlsx5") == 200 and n5.get("xlsx_amir") == 200,
          (n5.get("xlsx6"), n5.get("xlsx5"), n5.get("xlsx_amir")))
    lo = n5.get("loss") or {}
    check("5: loss_piles.receive_close twice -- the second run writes nothing (first: round %s, %s writes; second: %s, %s writes)" % (lo.get("first"), lo.get("first_writes"),
          lo.get("second"), lo.get("second_writes")), lo.get("second") is None and lo.get("second_writes") == 0)

    # selftest_spine
    sp_new = os.path.join(fin_new, "spine")
    p = subprocess.run([sys.executable, "-B", os.path.join(sp_new, "selftest_spine.py")], cwd=sp_new, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=900)
    check("5: selftest_spine.py is green on the scratch spine folder", p.returncode == 0 and "SELFTEST OK" in p.stdout, p.stdout.strip().splitlines()[-1:])
    return finish()


def finish():
    if FAILS:
        print("WALK_S537 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:260])
        return 1
    print("WALK_S537 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
