#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s528.py -- kit S528_AMIR_PAGE: the walk (the brief's section 6), on the server, on scratch copies only.

    python3 -B walk_s528.py --kit DIR --work /tmp/... --run DIR --por DIR --db finance.db --adb assets.db --spine spine.db --duty-map FILE

  run       the scratch layout the installer made: <run>/new/{finance,marg_ingest}, <run>/old/{finance,marg_ingest}; NEW carries the built
            stock_app.py, item_alias.py, amir_day.py and the new stock_amir.html; OLD is the box as it is.
  por       a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there (never the live ones).
  db / adb  backup-API copies of finance.db and assets.db; every probe works on its OWN further copy.
  spine     a backup-API copy of the LIVE spine.db (R3-8); every probe copies it and points SPINE_DB at its copy for the whole process (R2-30).

Probes run as fresh processes per side ("fn": the functions on their own copies; "api": the routes through the walk-only portal, signed in as
amir and as the owner), every one with ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a phone. Every
control is the same probe on the OLD files and must go red there. Rows are found by key, never by counting. No person, phone or account
number is in this file; item names only."""
import argparse
import datetime as dt
import hashlib
import html as _html
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

TAG = "W528JSON "
USERS = {"amir": "staff", "manoj": "doctor"}
TYNOR = "TYNOR WRIST SPLINT RT M ELAST"
BAD_WORDS = ("jaanch", "dekh lijiye", "wapas", "theek karna hai", "theek karke", "sahi nahi", "hona chahiye", "Marg = shelf", "Server ko bhejo",
             "Voucher kholiye", "abhi nahi dikhe")
KHOLIYE_OK = (r"board kholiye", r"kaam kholiye", r"Aur voucher kholiye", r"Internet dekh kar phir kholiye", r"Sunday chuniye (&mdash;|—|—) kholiye",
              r"bill baaki: \d+ (&mdash;|—|—) kholiye", r"sudhar: \d+ (&mdash;|—|—) kholiye", r"daalna hai (&mdash;|—|—) kholiye")
RETIRED = ("_s436_board_extra", "_s452_board_roman", "_s446_board_filter", "_s521_stage_proof", "_s521_wrong_hi", "_s521_export_hi", "S521_EXPORT_HI",
           "S488_TAIL_HI", "_s488_tail_hi", "S452_REASONS_ROMAN", "_s446_wrong_lines")
RETIRED_EXEMPT = {"amir_day.py": ("S488_TAIL_HI", "_s488_tail_hi")}       # amir_day's own copies: dead, left for Kit 3 (R3-6b), named in the README
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:1400] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def ins(con, table, row):
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    return con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols))), [row[c] for c in cols]).lastrowid


def texts(h):
    return [_html.unescape(x).strip() for x in re.findall(r">([^<]{3,400})<", h or "")]


def dmy(iso):
    s = str(iso or "")
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if len(s) >= 10 else s


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def keyset(ks):
    return sorted("%d|%s|%d" % (int(k[0]), k[1], int(k[2])) for k in ks or [])


def events(c, root):
    return [list(r) for r in c.execute("SELECT stage, event, ref, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]


def bad_hits(text, exempt=()):
    t = _html.unescape(str(text or ""))
    low = t.lower()
    hits = []
    for w in BAD_WORDS:
        if w in exempt:
            continue
        i = -1
        while True:
            i = low.find(w.lower(), i + 1)
            if i < 0:
                break
            if w == "Voucher kholiye" and low[max(0, i - 4):i] == "aur ":        # 'Aur voucher kholiye' is the door's own verb (S452), allowed
                continue
            hits.append((w, t[max(0, i - 40):i + len(w) + 20].replace("\n", " ")))
            break
    return hits


def kholiye_hits(text):
    t = _html.unescape(str(text or ""))
    out = []
    for m in re.finditer(r"kholiye", t):
        ctx = t[max(0, m.start() - 60):m.end()]
        ok = any(re.search(p, ctx) for p in KHOLIYE_OK)
        out.append((ok, ctx[-70:].replace("\n", " ")))
    return out


def add_ortho_batch(c, root, rno=9):
    """One un-entered orthotic batch of the root, by key (round rno, ISSUE, batch 1) -- the walk's own row."""
    ins(c, "stock_voucher_line", dict(count_id=root, round_no=rno, kind="ISSUE", batch_no=1, batches_n=1, line_no=1, section="Orthotics", family="w528",
                                      item="W528 ORTHO ITEM", packing="1*1", pack=1, marg_from=1, change=-1, marg_to=0, counted=0, reason="W528 walk",
                                      made_by="W528", made_at=now_iso()))
    c.commit()
    return (rno, "ISSUE", 1)


def as_before_takeback(c, root):
    """The copy as it stood before any take-back: for every batch entered now, the rows after its FIRST non-empty entry are set aside (the
    walk's own copy only). The live count carries one real take-back and re-entry (3|RECEIVE|2, 11-Oct); the OLD file's controls need the
    plain case, the NEW file reads the same either way (the window)."""
    ent = c.execute("SELECT id, round_no, kind, batch_no, marg_voucher_no FROM stock_voucher_entered WHERE count_id=? ORDER BY id", (root,)).fetchall()
    first, later = {}, []
    for r in ent:
        k = (r[1], r[2], r[3])
        if (r[4] or "").strip() and k not in first:
            first[k] = r[0]
        elif k in first and r[0] > first[k]:
            later.append(r[0])
    if later:
        c.execute("DELETE FROM stock_voucher_entered WHERE id IN (%s)" % ",".join("?" * len(later)), later)
        c.commit()
    return len(later)


def clear_pending(c, SA, root, item):
    """The pending orthotic line cleared by a correcting shelf figure (S524's walk did the same): counted = Marg - 2 nets the line to its vouchers."""
    d_ = SA._pad_report_data(c, root)
    x = [y for y in d_["differences"] if y["item"] == item]
    if x:
        ins(c, "stock_shelf_fix", dict(count_id=root, item=item, qty=int(x[0]["marg"]) - 2, source="accept_back", note="W528 walk", by_user="W528", at=now_iso()))
        c.commit()
    if hasattr(SA, "_S524_REPORT_CACHE"):
        SA._S524_REPORT_CACHE.clear()
    return bool(x)


# ============================================================================================================== the "fn" probe
def probe_fn():
    FIN, WORK, SIDE, DB0, SP0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W528_DB0", "W528_SPINE0"))
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402,F401 -- the app, so stock_app is the side's own file
    import stock_app as SA                                              # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import stockmatch as SM                                             # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    import item_alias as IA                                             # noqa: E402
    assert SA.__file__.startswith(FIN) and IA.__file__.startswith(FIN) and AD.__file__.startswith(FIN), (SA.__file__, IA.__file__, AD.__file__)
    NEW = hasattr(SA, "_s521_stage_words")
    out = dict(side=SIDE, new=NEW, spine_db=SW.SPINE_DB)
    U_AMIR = dict(user="amir", role="staff", roles=["viewer"])
    U_OWNER = dict(user="manoj", role="doctor", roles=["checker"])

    def mk(name, spine=True):
        p = os.path.join(WORK, "w528_%s.db" % name)
        copydb(DB0, p)
        sp = None
        if spine:
            sp = os.path.join(WORK, "w528_%s_spine.db" % name)
            copydb(SP0, sp)
            SW.SPINE_DB = sp                                            # the proof opens _sw.Spine() -> this copy
            os.environ["SPINE_DB"] = sp
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        SA._voucher_ensure(c)
        SA._feed_ensure(c)
        SA._s446_ensure(c)
        IA.ensure(c)
        SA._S446_PROOF_CACHE.clear()
        if hasattr(SA, "_S524_REPORT_CACHE"):
            SA._S524_REPORT_CACHE.clear()
        SA._S444_RENAMES_CACHE.clear()
        return c, sp

    def proof(c, root):
        SA._S446_PROOF_CACHE.clear()
        b = SA._s446_batches(c, root)
        e = SA._s446_entered(c, root)
        ortho = SA._s446_order([k for k, bb in b.items() if "Orthotics" in bb["secs"]])
        return SA._s446_proof(c, root, ortho, e, b), b, e, ortho

    def view(pr):
        return dict(state=pr.get("state"), why=pr.get("why"), as_before=pr.get("as_before"), as_after=pr.get("as_after"), closing_day=pr.get("closing_day"),
                    rows=[(r["item"], r.get("ok"), r.get("closing_day"), r.get("moved_hi"), r.get("need_hi"), r.get("key")) for r in pr.get("rows") or []],
                    unseen=[(r["item"], r.get("why")) for r in pr.get("unseen") or []], proven_on=sorted((pr.get("proven_on") or {}).keys()))

    def words(c, root, d=None):
        SA._S446_PROOF_CACHE.clear()
        st = SA.amir_stage(c, root, d=d)
        sw = SA._s521_stage_words(c, st) if NEW else None
        return st, sw

    def sw_view(sw):
        if not sw:
            return None
        return dict(state=sw.get("state"), card_hi=sw.get("card_hi"), owner_en=sw.get("owner_en"), lines=sw.get("lines"),
                    owner_lines=[l.get("text") for l in sw.get("owner_lines") or []], questions=len(sw.get("questions") or []))

    # ---- 0. the live state on the plain copy, by key
    c, sp = mk("plain")
    root = SA._s446_root(c)
    spc = sqlite3.connect("file:%s?mode=ro" % sp, uri=True)
    out["root"] = root
    out["built"] = spc.execute("SELECT value FROM sp_meta WHERE key='built'").fetchone()[0]
    out["newest_close"] = spc.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    spc.close()
    out["roles"] = [list(r) for r in c.execute("SELECT unit, role, username FROM unit_role WHERE lower(username) IN ('amir','manoj') AND active=1 AND unit='medical'")]
    rows0 = IA.rows(c)
    out["renames0"] = [(r["old_name"], r["state"], (r["done_at"] or "")[:19]) for r in rows0]
    out["ev0"] = events(c, root)
    st0, sw0 = words(c, root)
    A0 = (st0 or {}).get("A") or {}
    out["stage0"] = dict(stage=(st0 or {}).get("stage"), open=A0.get("open"), entered=A0.get("entered"), total=A0.get("total"), pending=A0.get("pending"),
                         proof=((A0.get("proof") or {}).get("state")), why=((A0.get("proof") or {}).get("why")), as_after=((A0.get("proof") or {}).get("as_after")),
                         renames_visible=(st0 or {}).get("renames_visible"), B=(st0 or {}).get("B"), visible=keyset((st0 or {}).get("visible")))
    out["ev1"] = events(c, root)
    SA.amir_stage(c, root)
    out["ev2"] = events(c, root)
    out["words0"] = sw_view(sw0)
    out["reg"] = view(A0.get("proof") or {})
    pr0, b0, e0, ortho0 = proof(c, root)
    out["entered0"] = {"%d|%s|%d" % k: (v[1], (v[2] if len(v) > 2 else None)) for k, v in e0.items()}
    if NEW:
        win = SA._s446_window(c, root)
        out["window0"] = {"%d|%s|%d" % k: v for k, v in win.items()}
        spx = SA._s524_spine()
        at_of = {k: str(win.get(k) or e0[k][1]) for k in e0}
        T = SA._s524_table(c, spx, root, e0, b0, min(at_of[k] for k in ortho0)[:19], max(at_of[k] for k in ortho0)[:19], at_of)
        out["T0"] = dict(R=({k: T["R"][k] for k in ("as_on", "stamp", "end_day")} if T["R"] else None), after=[(x["as_on"], x["stamp"]) for x in T["after"]],
                         tries=[(x["as_on"], x["stamp"]) for x in T["tries"]], N=((T.get("N") or {}).get("as_on"), (T.get("N") or {}).get("stamp"), T.get("N_short")),
                         reach=T["reach"], tynor=[(t["X"]["as_on"], t.get("ok"), t.get("why"), t.get("marg_move"), t.get("spine_move"), t.get("need"))
                                                 for t in ((T["keys"].get(T["kof"].get(TYNOR)) or {}).get("tries") or [])],
                         tynor_flags={k: (T["keys"].get(T["kof"].get(TYNOR)) or {}).get(k) for k in ("proven", "wrong", "pending_reach")})
        spx.con.close()
    # the hub, the card and the board on the plain copy say the same words (three reads, one string)
    if NEW:
        d0 = SA._report_cached(c, root)
        hub0 = SA._s524_hub_proof(c, root, d0)
        card0 = AD._s446_card(dict(s446=dict(stage=st0, stage_words=sw0)))
        board0 = SA._amir_board_light(c, root, U_AMIR, st0)
        boardo = SA._amir_board_light(c, root, U_OWNER, st0)
        out["three"] = dict(hub_text=hub0.get("text"), hub_state=hub0.get("state"), hub_lines=[l.get("text") for l in hub0.get("lines") or []],
                            card_has=[(l["hi"] in _html.unescape(card0)) for l in sw0["lines"]], board_hi=board0["proof"]["hi"], board_state=board0["proof"]["state"],
                            owner_board_hi=boardo["proof"]["hi"], card_bad=bad_hits(card0), card_khol=kholiye_hits(card0))
        jb = json.dumps(board0, ensure_ascii=False)
        out["light"] = dict(bytes=len(jb.encode("utf-8")), keys=sorted(board0.keys()), vouchers=len(board0["vouchers"]), owner_vouchers=len(boardo["vouchers"]),
                            renames=dict(ready=board0["renames"]["ready"], rows=len(board0["renames"]["rows"]), done_hi=board0["renames"]["done_hi"], total=board0["renames"]["total"],
                                         verified=board0["renames"]["verified"], questions=len(board0["renames"]["questions"]), owner_rows=len(boardo["renames"]["rows"])),
                            last_closing=board0.get("last_closing"), stage=board0.get("stage"), owner_stage=boardo.get("stage"), bad=bad_hits(jb), khol=kholiye_hits(jb),
                            owner_bad=bad_hits(json.dumps(boardo, ensure_ascii=False), exempt=("wapas",)), seq_3I1=[v["seq"] for v in board0["vouchers"] if (v["round_no"], v["kind"], v["batch_no"]) == (3, "ISSUE", 1)],
                            owner_seq_3I1=[v["seq"] for v in boardo["vouchers"] if (v["round_no"], v["kind"], v["batch_no"]) == (3, "ISSUE", 1)],
                            clear_amir=sum(1 for v in board0["vouchers"] if v.get("can_clear") or v.get("clear_hi")), clear_owner=sum(1 for v in boardo["vouchers"] if v.get("can_clear")),
                            field_shapes=dict(v=sorted(board0["vouchers"][0].keys()) if board0["vouchers"] else [], line=sorted(board0["vouchers"][0]["lines"][0].keys()) if board0["vouchers"] and board0["vouchers"][0]["lines"] else []))
        # one number: _voucher_seq = _voucher_numbers = _s437_flat (the xlsx prints batch n of m, not seq) = the light payload
        seqs = SA._voucher_seq(c, root)
        vn = SA._voucher_numbers(c, root)
        vs = SA._voucher_state(c, d0)
        flat = {(v["round_no"], v["kind"], v["batch_no"]): v["seq"] for v in vs["vouchers_flat"]}
        items_3I1 = [r[0] for r in c.execute("SELECT item FROM stock_voucher_line WHERE count_id=? AND round_no=3 AND kind='ISSUE' AND batch_no=1", (root,))]
        s3 = (seqs.get((3, "ISSUE", 1)) or (0,))[0]
        out["numbers"] = dict(seq_3I1=seqs.get((3, "ISSUE", 1)), flat_3I1=flat.get((3, "ISSUE", 1)), numbers_3I1=sorted({x for it in items_3I1 for x in vn.get(it, []) if "ISSUE" in x}),
                              numbers_every_item=all(("STOCK ISSUE voucher %d" % s3) in vn.get(it, []) for it in items_3I1),
                              flat_eq=all(flat.get(k) == v[0] for k, v in seqs.items()) and len(flat) == len(seqs), n=len(seqs),
                              stage_numbers=dict(st0["numbers"]) if st0 else None,
                              stage_numbers_eq=all(st0["numbers"].get("%d|%s|%d" % k) in (None, seqs[k][0]) for k in seqs) if st0 else None)
    else:
        b_old = SA._amir_board(c, root)
        b_old["you"] = dict(user="amir")
        b_old = SA._s446_board_filter(c, b_old, U_AMIR)
        b_old = SA._s521_stage_proof(c, b_old)
        b_old = SA._s452_board_roman(b_old)
        jb = json.dumps(b_old, ensure_ascii=False, default=str)
        card0 = AD._s446_card(dict(s446=dict(stage=st0)))
        out["light"] = dict(bytes=len(jb.encode("utf-8")), proof_hi=b_old.get("proof_hi"), bad=bad_hits(jb), khol=kholiye_hits(jb), seq_3I1=[v["seq"] for v in ((b_old.get("made") or {}).get("vouchers_flat") or []) if (v["round_no"], v["kind"], v["batch_no"]) == (3, "ISSUE", 1)])
        out["three"] = dict(card_bad=bad_hits(card0), card_khol=kholiye_hits(card0), board_hi=b_old.get("proof_hi"))
        out["numbers"] = dict(seq_3I1=None)
    c.close()

    # ---- 1. F-851: the TYNOR case replayed on a copy of the LIVE spine -- the reach set back to the brief's day (the purchase exports after
    #         08-Oct 09:04 marked not-ok on the COPY; the sale export's capture set after the newest closing so that only the purchase side is short)
    res = {}
    try:
        c, sp = mk("f851")
        res["set_aside"] = as_before_takeback(c, root)                  # the plain case for both sides (the OLD control needs it)
        spw = sqlite3.connect(sp)
        newest_sale = spw.execute("SELECT stamp FROM sp_export WHERE family='SALE_BILLWISE' AND ok=1 ORDER BY stamp DESC LIMIT 1").fetchone()[0]
        spw.execute("UPDATE sp_export SET stamp='20261011-120000' WHERE family='SALE_BILLWISE' AND stamp=?", (newest_sale,))
        spw.execute("UPDATE sp_export SET ok=0 WHERE family LIKE 'PURCHASE%' AND stamp > '20261008-100000'")
        spw.execute("UPDATE sp_meta SET value='2026-10-11T16:00:00+05:30 W528a' WHERE key='built'")
        spw.commit()
        pr1, b1, e1, o1 = proof(c, root)
        res["short"] = view(pr1)
        if NEW:
            st1, sw1 = words(c, root)
            res["short_words"] = sw_view(sw1)
        # the purchase reach restored by a synthetic export covering 10-Oct (the moves of the real exports are already in sp_move)
        for fam, m5 in (("PURCHASE_BILLWISE", "W528PUR1"), ("PURCHASE_ITEMWISE", "W528PUR2")):
            spw.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (m5, "W528 synthetic %s" % fam, fam, "20261011-123000", "2026-10-01", "2026-10-10", "", 1, "", "", "W528 walk"))
        spw.execute("UPDATE sp_meta SET value='2026-10-11T16:01:00+05:30 W528b' WHERE key='built'")
        spw.commit()
        pr2, _b, _e, _o = proof(c, root)
        res["covered"] = view(pr2)
        if NEW:
            st2, sw2 = words(c, root)
            res["covered_words"] = sw_view(sw2)
            # R1-C2: the key absent at N keeps its own why
            spx = SA._s524_spine()
            kT = SA._s524_key_of(spx, TYNOR, {})
            spx.con.close()
            spw.execute("DELETE FROM sp_close WHERE k20=? AND as_on=(SELECT MAX(as_on) FROM sp_close)", (kT,))
            spw.execute("UPDATE sp_meta SET value='2026-10-11T16:02:00+05:30 W528c' WHERE key='built'")
            spw.commit()
            pr3, _b, _e, _o = proof(c, root)
            res["absent_at_N"] = view(pr3)
        spw.close()
        c.close()
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["f851"] = res

    # ---- 2. the window (R3-1): on a copy taken BEFORE any take-back (the real re-entry of the live row set aside on the copy), the earliest key
    #         cleared by the owner and entered again by amir after a clean closing captured between its first entry and the next key's
    res = {}
    try:
        c, sp = mk("win")
        res["set_aside"] = as_before_takeback(c, root)
        pr_a, b_a, e_a, o_a = proof(c, root)
        res["before"] = view(pr_a)
        k1 = min(o_a, key=lambda k: e_a[k][1])
        t1 = e_a[k1][1]
        nxt = min([e_a[k][1] for k in o_a if k != k1])
        last_at = max(e_a[k][1] for k in o_a)[:19]
        cap = (dt.datetime.fromisoformat(t1[:19]) + (dt.datetime.fromisoformat(nxt[:19]) - dt.datetime.fromisoformat(t1[:19])) / 2).strftime("%Y%m%d-%H%M%S")
        # the re-entry falls just after the FIRST clean closing captured after the entries, so a later closing can still judge the old file's window
        spx = SA._s524_spine()
        after0 = sorted([x for x in SA._s524_closings(spx) if x["end_day"] and x["stamp_iso"] > last_at], key=lambda x: x["stamp_iso"])[0]
        spx.con.close()
        re_clear = (dt.datetime.fromisoformat(after0["stamp_iso"]) + dt.timedelta(hours=1)).isoformat(timespec="seconds")
        re_entry = (dt.datetime.fromisoformat(after0["stamp_iso"]) + dt.timedelta(hours=1, minutes=5)).isoformat(timespec="seconds")
        res["setup"] = dict(k1="%d|%s|%d" % k1, t1=t1, next=nxt, closing_stamp=cap, after0=(after0["as_on"], after0["stamp"]), re_clear=re_clear, re_entry=re_entry)
        spw = sqlite3.connect(sp)
        src = spw.execute("SELECT as_on FROM sp_close WHERE as_on > ? ORDER BY as_on LIMIT 1", (t1[:10],)).fetchone()[0]   # the first closing after the entries: it carries every voucher
        day_before = (dt.date.fromisoformat(t1[:10]) - dt.timedelta(days=1)).isoformat()
        spw.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    ("W528CLOSE1", "W528 synthetic closing", "STOCK_CLOSING", cap, day_before, "", day_before, 1, "", "", "W528 walk"))
        spw.execute("INSERT INTO sp_close (as_on, k20, units, source_md5) SELECT ?, k20, units, 'W528CLOSE1' FROM sp_close WHERE as_on=?", (day_before, src))
        spw.execute("UPDATE sp_meta SET value='2026-10-11T16:03:00+05:30 W528w' WHERE key='built'")
        spw.commit()
        spw.close()
        ins(c, "stock_voucher_entered", dict(count_id=root, round_no=k1[0], kind=k1[1], batch_no=k1[2], marg_voucher_no="", entered_on=None, by_user="manoj", at=re_clear))
        ins(c, "stock_voucher_entered", dict(count_id=root, round_no=k1[0], kind=k1[1], batch_no=k1[2], marg_voucher_no="W528RE", entered_on=re_entry[:10], by_user="amir", at=re_entry))
        c.commit()
        pr_b, b_b, e_b, o_b = proof(c, root)
        res["after"] = view(pr_b)
        if NEW:
            w = SA._s446_window(c, root)
            res["window_k1"] = w.get(k1)
        c.close()
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["win"] = res

    # ---- 3. F-854 / D709: the renames by identity on copies
    res = {}
    try:
        c, _sp = mk("f854", spine=False)
        rows = IA.rows(c)
        ticked = [r for r in rows if r["done_at"] and not r["verified_at"] and not r.get("undone_at")]
        olds = [r["old_name"] for r in ticked]
        day_row, base = None, []
        news = {IA.pad_norm(r["new_name"]) for r in ticked}
        for (d_,) in c.execute("SELECT as_on FROM stock_snapshot GROUP BY as_on ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC"):
            names_d = {r[0] for r in c.execute("SELECT item FROM stock_snapshot WHERE as_on=?", (d_,))}
            # the newest day that lists every OLD name and none of the NEW spellings (the 10-Oct snapshot already carries Amir's renamed names)
            if all(o in names_d for o in olds) and not any(IA.pad_norm(n) in news or any(IA.pad_norm(n).startswith(x) or x.startswith(IA.pad_norm(n)) for x in news if min(len(x), len(IA.pad_norm(n))) >= 20) for n in names_d if n not in olds):
                day_row, base = d_, sorted(names_d)
                break
        tick_max = max(str(r["done_at"])[:19] for r in ticked)
        cap = (dt.datetime.fromisoformat(tick_max) + dt.timedelta(hours=1)).isoformat(timespec="seconds")
        as_on = (dt.date.fromisoformat(tick_max[:10]) - dt.timedelta(days=1)).isoformat()
        keep_old = ticked[-1]["old_name"]
        ren = {r["old_name"]: r["new_name"] for r in ticked if r["old_name"] != keep_old}
        main = [ren.get(n, n) for n in base]
        res["setup"] = dict(snapshot_day=day_row, names=len(base), ticked=len(ticked), tick_max=tick_max, captured=cap, as_on=as_on, kept_old=keep_old)
        if NEW:
            r1 = IA.verify_closing(c, main, as_on, "W528MAIN", "W528", captured=cap)
            c.commit()
            after = {r["old_name"]: r for r in IA.rows(c)}
            res["main"] = dict(verified=len(r1["verified"]), seen=len(r1["seen"]), questions=r1.get("questions"), read_back=r1.get("read_back"),
                               kept_state=after[keep_old]["state"], kept_seen_n=after[keep_old]["seen_n"], states={k: v["state"] for k, v in after.items() if k in olds},
                               B=SA._s524_stage_b(c, root), events=[tuple(r) for r in c.execute("SELECT event, COUNT(*) FROM marg_item_rename_event GROUP BY event ORDER BY event")],
                               k20_sample=[(after[o]["new_name"], after[o]["verified_k20"], after[o]["verified_captured"]) for o in olds[:2]],
                               collisions=c.execute("SELECT COUNT(*) FROM marg_item_rename_event WHERE event='collision'").fetchone()[0])
            # a second identical sighting judges nothing twice
            r1b = IA.verify_closing(c, main, as_on, "W528MAIN", "W528", captured=cap)
            res["main_again"] = dict(verified=len(r1b["verified"]), seen=len(r1b["seen"]), kept_seen_n=[r["seen_n"] for r in IA.rows(c) if r["old_name"] == keep_old][0])
            c.close()
            # variants, each on a fresh copy of its own (never a second copy onto a path a connection still holds: the backup API would wait forever)
            fresh_n = [0]

            def fresh():
                fresh_n[0] += 1
                cc, _s = mk("f854v%d" % fresh_n[0], spine=False)
                return cc
            # (i) a double space and a trailing dot
            cc = fresh()
            o1, o2 = olds[0], olds[1]
            n1, n2 = ren.get(o1) or [r["new_name"] for r in ticked if r["old_name"] == o1][0], ren.get(o2) or [r["new_name"] for r in ticked if r["old_name"] == o2][0]
            lst = [x for x in base if x not in (o1, o2)] + [n1.replace(" ", "  ", 1), n2 + "."]
            rv = IA.verify_closing(cc, lst, as_on, "W528V1", "W528", captured=cap)
            res["fold"] = dict(verified=sorted(rv["verified"]), expect=sorted([o1, o2]))
            cc.close()
            # (ii) an inner dot -> question; the owner's Accept -> verified; the chain
            cc = fresh()
            sh = [r for r in ticked if r["new_name"].startswith("SHOULDER IMMOB ")]
            if sh:
                so, sn = sh[0]["old_name"], sh[0]["new_name"]
                dotted = sn.replace("SHOULDER IMMOB ", "SHOULDER IMMOB. ", 1)
                lst = [x for x in base if x != so] + [dotted]
                rv = IA.verify_closing(cc, lst, as_on, "W528V2", "W528", captured=cap)
                st_q = [r for r in IA.rows(cc) if r["old_name"] == so][0]
                qs = IA.questions(cc)
                ok_a, msg_a, row_a = IA.accept(cc, st_q["id"], dotted, "manoj")
                chain = [r[0] for r in cc.execute("SELECT event FROM marg_item_rename_event WHERE rename_id=? ORDER BY id", (st_q["id"],))]
                res["dot"] = dict(seen_name=dotted, state=st_q["state"], q=[(q["seen_name"], q["event"]) for q in qs if q["rename_id"] == st_q["id"]],
                                  accept=[ok_a, msg_a, (row_a or {}).get("state"), (row_a or {}).get("verified_k20")], chain=chain,
                                  summary_q=IA.summary(cc).get("question"), both_refused=None)
                # a second closing with the exact name supersedes a question (R3-14) -- on another fresh copy
                cc2 = fresh()
                IA.verify_closing(cc2, lst, as_on, "W528V2", "W528", captured=cap)
                rv2 = IA.verify_closing(cc2, [x for x in base if x != so] + [sn], as_on, "W528V2b", "W528", captured=(dt.datetime.fromisoformat(cap) + dt.timedelta(hours=1)).isoformat(timespec="seconds"))
                res["dot"]["supersede"] = dict(verified=rv2["verified"], state=[r["state"] for r in IA.rows(cc2) if r["old_name"] == so][0],
                                              chain=[r[0] for r in cc2.execute("SELECT event FROM marg_item_rename_event WHERE rename_id=? ORDER BY id", (st_q["id"],))])
                cc2.close()
            cc.close()
            # (iii) both names listed -> both / question; Accept refused
            cc = fresh()
            o3 = olds[2]
            n3 = [r["new_name"] for r in ticked if r["old_name"] == o3][0]
            rv = IA.verify_closing(cc, base + [n3], as_on, "W528V3", "W528", captured=cap)
            r3 = [r for r in IA.rows(cc) if r["old_name"] == o3][0]
            ok_b, msg_b, _row_b = IA.accept(cc, r3["id"], n3, "manoj")
            res["both"] = dict(state=r3["state"], event=(r3.get("question") or {}).get("event"), accept=[ok_b, msg_b[:60]])
            cc.close()
            # (iv) a planned row (never ticked) whose new name appears -> read_back
            cc = fresh()
            ins(cc, "marg_item_rename", dict(old_name="W528 OLD NAME ITEM", new_name="W528 NEW NAME ITEM", old20="W528 OLD NAME ITEM", old27="W528 OLD NAME ITEM", new20="W528 NEW NAME ITEM",
                                             new27="W528 NEW NAME ITEM", family="W528", planned_by="W528", planned_at="2026-10-01T10:00:00", seen_n=0))
            cc.commit()
            rv = IA.verify_closing(cc, base + ["W528 NEW NAME ITEM"], as_on, "W528V4", "W528", captured=cap)
            r4 = [r for r in IA.rows(cc) if r["old_name"] == "W528 OLD NAME ITEM"][0]
            res["read_back"] = dict(read_back=rv["read_back"], state=r4["state"], done_by=r4["done_by"], done_at=r4["done_at"], staff_hi=r4.get("state_staff_hi"))
            cc.close()
            # (v) captured before the tick -> nothing
            cc = fresh()
            before = (dt.datetime.fromisoformat(min(str(r["done_at"])[:19] for r in ticked)) - dt.timedelta(minutes=5)).isoformat(timespec="seconds")
            rv = IA.verify_closing(cc, main, as_on, "W528V5", "W528", captured=before)
            res["before_tick"] = dict(verified=len(rv["verified"]), seen=len(rv["seen"]), events=cc.execute("SELECT COUNT(*) FROM marg_item_rename_event").fetchone()[0])
            cc.close()
            # (v b) no capture given -> refused with a line
            cc = fresh()
            rv = IA.verify_closing(cc, main, as_on, "W528V5b", "W528")
            res["no_capture"] = dict(skipped=rv.get("skipped"), verified=len(rv["verified"]))
            cc.close()
            # (vi) a short list through sight_closing -> skipped
            cc = fresh()
            rv = IA.sight_closing(cc, main[: max(1, int(len(main) * 0.3))], dmy(as_on), "W528V6", "20261011-105200")
            res["short"] = dict(skipped=rv.get("skipped"), need=(rv.get("short") or {}).get("need"), verified=len(rv["verified"]))
            rv2 = IA.sight_closing(cc, main, dmy(as_on), "W528V6b", (dt.datetime.fromisoformat(cap)).strftime("%Y%m%d-%H%M%S"))
            res["short"]["whole"] = len(rv2["verified"])
            cc.close()
            # (vii) a collision: another listed name with the same 20-letter key, neither old nor new -> collision, a question
            cc = fresh()
            o7 = [r for r in ticked if r["new_name"].startswith("KNEE SUPPORT L ")][0]
            lst = [ren.get(n, n) for n in base] + [o7["new_name"] + " X"]
            rv = IA.verify_closing(cc, lst, as_on, "W528V7", "W528", captured=cap)
            r7 = [r for r in IA.rows(cc) if r["old_name"] == o7["old_name"]][0]
            res["collision"] = dict(state=r7["state"], event=(r7.get("question") or {}).get("event"), seen=(r7.get("question") or {}).get("seen_name"))
            cc.close()
            # (viii) a printed spelling that is a prefix of the new name (the 10-10 closing's own shape) -> question, never 'not seen'
            cc = fresh()
            o8 = [r for r in ticked if r["new_name"].startswith("TYNOR WRIST SPL RT L")][0]
            lst = [x for x in base if x != o8["old_name"]] + [o8["new_name"][:-1]]
            rv = IA.verify_closing(cc, lst, as_on, "W528V8", "W528", captured=cap)
            r8 = [r for r in IA.rows(cc) if r["old_name"] == o8["old_name"]][0]
            res["prefix"] = dict(printed=o8["new_name"][:-1], state=r8["state"], seen=(r8.get("question") or {}).get("seen_name"))
            cc.close()
            # re-tick after a take-back (R2-17): untick as checker -> planned (undone_at), tick again -> done, events tick/untick/tick
            cc = fresh()
            o9 = olds[3]
            ok_u, msg_u, _ = IA.untick(cc, o9, "manoj")
            s_u = [r for r in IA.rows(cc) if r["old_name"] == o9][0]
            ok_t, msg_t, _ = IA.tick(cc, o9, "amir")
            s_t = [r for r in IA.rows(cc) if r["old_name"] == o9][0]
            res["retick"] = dict(untick=[ok_u, msg_u, s_u["state"], bool(s_u.get("undone_at")), bool(s_u["done_at"])], tick=[ok_t, msg_t, s_t["state"], s_t.get("undone_at")],
                                 chain=[r[0] for r in cc.execute("SELECT event FROM marg_item_rename_event WHERE rename_id=? ORDER BY id", (s_t["id"],))])
            cc.close()
            # stockmatch.section_state on a copy holding a question row (R1-B4 / R2-27c): summary must not raise
            cc, _s = mk("f854sm")
            if sh:
                IA.verify_closing(cc, [x for x in base if x != so] + [dotted], as_on, "W528V2", "W528", captured=cap)
                cc.commit()
            try:
                d_ = SA._pad_report_data(cc, root)
                sst = SM.section_state(cc, d_)
                res["section_state"] = dict(ok=True, renames_cond=[x.get("en") for x in sst["conds"] if x.get("key") == "renames"], summary=IA.summary(cc))
            except Exception as ex:                                     # noqa: BLE001
                res["section_state"] = dict(ok=False, error="%s: %s" % (type(ex).__name__, str(ex)[:200]))
            cc.close()
        else:
            # the OLD module on the same copy: the day rule throws the closing away (printed for the day before the tick)
            r1 = IA.verify_closing(c, main, as_on, "W528MAIN", "W528", captured=cap)
            c.commit()
            res["main"] = dict(verified=len(r1["verified"]), seen=len(r1["seen"]))
            c.close()
        # api_snapshot no longer tells the rename memory (grep the side's file)
        t = io.open(os.path.join(FIN, "stock_app.py"), encoding="utf-8").read()
        res["snapshot_calls"] = t.count("item_alias.verify_closing(")
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["f854"] = res

    # ---- 4. the stage words, one row of the table at a time (NEW); the OLD card/board words in the wrong state are the control
    res = {}

    def inverse_copy(name):
        """A copy where the TYNOR key is WRONG by the newest closing: the sale export's capture set after the newest closing (so N is inside the
        reach), the key's closing moved by +7 at every after-closing (a figure no late purchase explains)."""
        c, sp = mk(name)
        as_before_takeback(c, root)
        spw = sqlite3.connect(sp)
        for fam in ("SALE_BILLWISE", "PURCHASE_BILLWISE", "PURCHASE_ITEMWISE"):               # every reach captured after the newest closing: N is tryable
            newest = spw.execute("SELECT stamp FROM sp_export WHERE family=? AND ok=1 ORDER BY date_to DESC, stamp DESC LIMIT 1", (fam,)).fetchone()[0]
            spw.execute("UPDATE sp_export SET stamp='20261011-120000' WHERE family=? AND stamp=?", (fam, newest))
        spw.execute("UPDATE sp_meta SET value='2026-10-11T16:04:00+05:30 W528x' WHERE key='built'")
        spw.commit()
        pr_, b_, e_, o_ = proof(c, root)
        spx = SA._s524_spine()
        T = SA._s524_table(c, spx, root, e_, b_, min(e_[k][1] for k in o_)[:19], max(e_[k][1] for k in o_)[:19])
        kT = T["kof"].get(TYNOR)
        spx.con.close()
        for x in T["after"]:
            spw.execute("UPDATE sp_close SET units = units + 7 WHERE k20=? AND as_on=?", (kT, x["as_on"]))
        spw.execute("UPDATE sp_meta SET value='2026-10-11T16:04:30+05:30 W528y' WHERE key='built'")
        spw.commit()
        spw.close()
        SA._S446_PROOF_CACHE.clear()
        return c, sp
    if not NEW:
        try:
            c, sp = inverse_copy("w_awrong_old")
            st = SA.amir_stage(c, root)
            card = AD._s446_card(dict(s446=dict(stage=st)))
            b = SA._s521_stage_proof(c, dict(count_id=root, proof_state="x", proof_hi="x", renames_ready=None, renames_wait_hi="x", made=dict(vouchers_flat=[])))
            res["a_wrong_old"] = dict(proof=((st.get("A") or {}).get("proof") or {}).get("state"), card_bad=bad_hits(card), card_khol=kholiye_hits(card), board_hi=b.get("proof_hi"),
                                      card_text=[x for x in texts(card) if x][:8])
            c.close()
        except Exception as ex:                                         # noqa: BLE001
            res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:400])
    if NEW:
        try:
            # A open
            c, sp = mk("w_aopen")
            kb = add_ortho_batch(c, root)
            st, sw = words(c, root)
            res["a_open"] = sw_view(sw)
            res["a_open"]["card"] = AD._s446_card(dict(s446=dict(stage=st, stage_words=sw)))
            c.close()
            # A wrong: the inverse case -- the newest closing inside the reach, the key's closing moved by a figure nothing explains
            c, sp = inverse_copy("w_awrong")
            st, sw = words(c, root)
            res["a_wrong"] = sw_view(sw)
            res["a_wrong"]["proof"] = view((st["A"].get("proof") or {}))
            d_ = SA._report_cached(c, root)
            hub = SA._s524_hub_proof(c, root, d_)
            res["a_wrong"]["hub"] = dict(state=hub["state"], text=hub["text"], rows=[(r["item"], r["why"]) for r in hub["rows"]], lines=[l["text"] for l in hub["lines"]])
            res["a_wrong"]["needs_you"] = [l for l in AD._s446_owner_lines(c) if l.get("target") == "stock"]
            res["a_wrong"]["card"] = AD._s446_card(dict(s446=dict(stage=st, stage_words=sw)))
            c.close()
            # a Marg number typed on two keys -> the owner's line
            c, sp = mk("w_dup")
            kb = add_ortho_batch(c, root)
            no0 = c.execute("SELECT marg_voucher_no FROM stock_voucher_entered WHERE count_id=? AND TRIM(marg_voucher_no)<>'' ORDER BY id LIMIT 1", (root,)).fetchone()[0]
            ins(c, "stock_voucher_entered", dict(count_id=root, round_no=kb[0], kind=kb[1], batch_no=kb[2], marg_voucher_no=no0, entered_on="2026-10-11", by_user="amir", at=now_iso()))
            c.commit()
            st, sw = words(c, root)
            res["dup"] = [l["text"] for l in sw["owner_lines"] if l["text"].startswith("Marg voucher number")]
            c.close()
            # B open / B all ticked: the pending line cleared, the proof must be done
            c, sp = mk("w_b")
            pend_item = c.execute("SELECT item FROM stock_voucher_line WHERE count_id=? AND section='Orthotics' AND item LIKE 'ANKLE BINDER BAMBOO L%' LIMIT 1", (root,)).fetchone()
            cleared = clear_pending(c, SA, root, pend_item[0]) if pend_item else False
            st, sw = words(c, root)
            res["b_all"] = sw_view(sw)
            res["b_all"]["stage"] = st.get("stage")
            res["b_all"]["pending"] = (st.get("A") or {}).get("pending")
            res["b_all"]["cleared"] = cleared
            res["b_all"]["proof"] = ((st.get("A") or {}).get("proof") or {}).get("state")
            o_b = [r for r in IA.rows(c) if r["done_at"] and not r["verified_at"]][0]["old_name"]
            IA.untick(c, o_b, "manoj")
            c.commit()
            st, sw = words(c, root)
            res["b_open"] = sw_view(sw)
            res["b_open"]["stage"] = st.get("stage")
            res["b_open"]["extra_hi"] = AD._s452_extra_hi(dict(s446=dict(stage=st, stage_words=sw)))
            res["b_open"]["left"] = AD._s446_left(dict(s446=dict(stage=st, stage_words=sw)))
            # C: the renames verified by event -> the first lot released
            ins(c, "stock_stage_event", dict(count_id=root, stage="B", event="verified", ref="", at=now_iso(), detail="W528"))
            c.commit()
            st, sw = words(c, root)
            res["c_open"] = sw_view(sw)
            res["c_open"]["stage"] = st.get("stage")
            res["c_open"]["C"] = {k: (st.get("C") or {}).get(k) for k in ("open", "released", "lots", "entered", "total", "per", "unreleased")}
            lot_keys = [k for l in c.execute("SELECT ref FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release' ORDER BY id LIMIT 1", (root,)) for k in (l[0] or "").split(",") if k]
            # C waiting: the lot entered now -> no closing after it
            for ks in lot_keys:
                k = SA._s446_unkey(ks)
                ins(c, "stock_voucher_entered", dict(count_id=root, round_no=k[0], kind=k[1], batch_no=k[2], marg_voucher_no="W528C%d" % k[2], entered_on="2026-10-11", by_user="amir", at=now_iso()))
            c.commit()
            st, sw = words(c, root)
            res["c_wait"] = sw_view(sw)
            res["c_wait"]["stage"] = st.get("stage")
            res["c_wait"]["C"] = dict(waiting=len((st.get("C") or {}).get("waiting_export") or []), wrong=len((st.get("C") or {}).get("wrong") or []), open=(st.get("C") or {}).get("open"))
            # C wrong: the same lot entered INSIDE the window (04-Oct, after the orthotic entries) -> judged by the real closings; the medicine vouchers were never keyed in Marg
            for ks in lot_keys:
                k = SA._s446_unkey(ks)
                ins(c, "stock_voucher_entered", dict(count_id=root, round_no=k[0], kind=k[1], batch_no=k[2], marg_voucher_no="", entered_on=None, by_user="manoj", at=now_iso()))
            c.commit()
            c.execute("DELETE FROM stock_voucher_entered WHERE count_id=? AND by_user IN ('amir','manoj') AND marg_voucher_no LIKE 'W528C%'", (root,))
            c.execute("DELETE FROM stock_voucher_entered WHERE count_id=? AND marg_voucher_no='' AND at >= ?", (root, now_iso()[:10]))
            for ks in lot_keys:
                k = SA._s446_unkey(ks)
                ins(c, "stock_voucher_entered", dict(count_id=root, round_no=k[0], kind=k[1], batch_no=k[2], marg_voucher_no="W528C%d" % k[2], entered_on="04-10-2026", by_user="amir", at="2026-10-04T10:30:00"))
            c.commit()
            st, sw = words(c, root)
            res["c_judged"] = sw_view(sw)
            res["c_judged"]["stage"] = st.get("stage")
            res["c_judged"]["C"] = dict(waiting=len((st.get("C") or {}).get("waiting_export") or []), wrong=len((st.get("C") or {}).get("wrong") or []), open=(st.get("C") or {}).get("open"),
                                        lot_state=[(l.get("proof") or {}).get("state") for l in []])
            d_ = SA._report_cached(c, root)
            hub = SA._s524_hub_proof(c, root, d_)
            res["c_judged"]["hub"] = dict(state=hub["state"], text=hub["text"], rows=len(hub["rows"]))
            c.close()
            # done: no medicine batch at all (moved aside on the copy), the pending line cleared, B verified
            c, sp = mk("w_done")
            if pend_item:
                clear_pending(c, SA, root, pend_item[0])
            c.execute("UPDATE stock_voucher_line SET count_id = count_id + 9000000 WHERE count_id=? AND section <> 'Orthotics'", (root,))
            ins(c, "stock_stage_event", dict(count_id=root, stage="B", event="verified", ref="", at=now_iso(), detail="W528"))
            c.commit()
            st, sw = words(c, root)
            res["done"] = sw_view(sw)
            res["done"]["stage"] = st.get("stage")
            res["done"]["card"] = AD._s446_card(dict(s446=dict(stage=st, stage_words=sw)))
            res["done"]["hub_text"] = SA._s524_hub_proof(c, root, SA._report_cached(c, root))["text"]
            c.close()
            # st None -> empty words; no stage object
            res["none"] = sw_view(SA._s521_stage_words(None, None))
        except Exception as ex:                                         # noqa: BLE001
            res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:400])
    out["words"] = res

    # ---- 5. not broken: Needs-you's shape; the jobs card byte-equal (the same jobs input); amir_salts untouched (route-level in the api probe)
    res = {}
    try:
        c, sp = mk("nb")
        ny = AD.needs_you_lines(c)
        res["needs_you"] = dict(n=len(ny), shapes=sorted({tuple(sorted(k for k in l.keys() if k in ("cls", "target", "text", "duty"))) for l in ny}),
                                stock=[l["text"] for l in ny if l.get("target") == "stock"][:4], bad=bad_hits(json.dumps(ny, ensure_ascii=False), exempt=("jaanch", "wapas", "sahi nahi")))
        jobs = [dict(id=1, kind="category", subject="W528 ITEM", label="ORTHOTIC"), dict(id=2, kind="vendor_bill", subject="W528 VENDOR", bill=None)]
        res["jobs_html"] = hashlib.md5("".join(AD._s494_lines(jobs)).encode("utf-8")).hexdigest()
        c.close()
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["nb"] = res

    # ---- 6. timing (reported) and the once-only events
    c, sp = mk("tm")
    SA.amir_stage(c, root)
    t0 = time.perf_counter()
    st = SA.amir_stage(c, root)
    out["ms_stage_warm"] = int((time.perf_counter() - t0) * 1000)
    if NEW:
        t0 = time.perf_counter()
        SA._amir_board_light(c, root, U_AMIR, st)
        out["ms_light_fn"] = int((time.perf_counter() - t0) * 1000)
    c.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "api" probe
def probe_api():
    FIN, POR, DB, SIDE, WORK = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE", "WORKDIR"))
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import item_alias as IA                                             # noqa: E402
    assert SA.__file__.startswith(FIN), SA.__file__
    NEW = hasattr(SA, "_s521_stage_words")
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    W = json.loads(os.environ["W528J"])
    pw = W["pw"]
    c = sqlite3.connect(DB, timeout=60)
    root = SA._s446_root(c)
    out = dict(side=SIDE, new=NEW, root=root)
    ck = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
    calls = [0]
    real_stage = SA.amir_stage

    def counted(*a, **k):
        calls[0] += 1
        return real_stage(*a, **k)
    SA.amir_stage = counted

    def board(who):
        calls[0] = 0
        t0 = time.perf_counter()
        rr = fc.get("/finance/stock/api/pad/amir/%d" % root, base_url=BASE, headers=ck[who])
        ms = int((time.perf_counter() - t0) * 1000)
        raw = rr.get_data(as_text=True)
        j = rr.get_json(silent=True) or {}
        flat = (j.get("vouchers") if NEW else ((j.get("made") or {}).get("vouchers_flat"))) or []
        return dict(code=rr.status_code, bytes=len(raw.encode("utf-8")), ms=ms, stage_calls=calls[0], keys=sorted(j.keys()),
                    proof=(j.get("proof") if NEW else dict(state=j.get("proof_state"), hi=j.get("proof_hi"))),
                    flat=sorted("%d|%s|%d" % (v["round_no"], v["kind"], v["batch_no"]) for v in flat), n=len(flat),
                    renames=dict(ready=(j.get("renames") or {}).get("ready") if NEW else j.get("renames_ready"), rows=len(((j.get("renames") or {}).get("rows") or [])),
                                 questions=len(((j.get("renames") or {}).get("questions") or [])), done_hi=(j.get("renames") or {}).get("done_hi")),
                    last_closing=bool(j.get("last_closing")), stage=(j.get("stage") or {}).get("stage") if isinstance(j.get("stage"), dict) else None,
                    bad=bad_hits(raw), khol=kholiye_hits(raw), clear=sum(1 for v in flat if v.get("can_clear") or v.get("clear_hi")),
                    field_check=dict(v=sorted(flat[0].keys()) if flat else [], rest=sorted((j.get("rest") or {}).keys()), salt=len(j.get("salt_fix") or []), rate=len(j.get("rate_tasks") or [])))

    def page(who):
        rr = fc.get("/finance/stock/page/amir?count=%d" % root, base_url=BASE, headers=ck[who])
        h = rr.get_data(as_text=True)
        return dict(code=rr.status_code, bytes=len(h.encode("utf-8")), file_input=('type="file"' in h), marg_answer=("marg_answer" in h), bar=('id="s444bar"' in h), rest=('id="rest"' in h),
                    boot=("window.BOOT=" in h), bad=bad_hits(h), khol=kholiye_hits(h), card4=('<span class="n">4</span>' in h))

    def post(who, k, clear=False, no=None):
        body = dict(round=k[0], kind=k[1], batch=k[2])
        body.update(dict(clear=True) if clear else dict(marg_voucher_no=(no or "W528V%d" % k[0])))
        rr = fc.post("/finance/stock/api/pad/vouchers/%d/entered" % root, base_url=BASE, headers=ck[who], json=body)
        j = rr.get_json(silent=True) or {}
        return [rr.status_code, j.get("error"), j.get("message")]

    out["ev0"] = events(c, root)
    out["board_amir_1"] = board("amir")
    out["ev1"] = events(c, root)
    out["board_amir_2"] = board("amir")
    out["ev2"] = events(c, root)
    out["board_owner"] = board("manoj")
    out["page_amir"] = page("amir")
    out["page_owner"] = page("manoj")
    # the door (F-852)
    ent = SA._s446_entered(c, root)
    vis = [tuple(k) for k in ((real_stage(c, root) or {}).get("visible") or [])]
    ent_vis = [k for k in vis if k in ent]
    med = c.execute("SELECT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=? AND section='Medicines' ORDER BY round_no, kind, batch_no LIMIT 1", (root,)).fetchone()
    med = tuple(med)
    kb = add_ortho_batch(c, root)
    SA._S446_PROOF_CACHE.clear()
    # the staff-eye read while the walk's batch is open (the duty due): his home, the tiles, every due duty's door marker
    r1 = pc.get("/portal", base_url=BASE, headers=ck["amir"])
    r3 = pc.get("/portal?all=1", base_url=BASE, headers=ck["amir"])
    tiles = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r3.get_data(as_text=True) or "")]
    dm = json.load(open(os.environ["W528_DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    duties = []
    for du in dm.get("duties") or []:
        if du.get("person") != "amir":
            continue
        row = dict(id=du["id"], tile=du.get("tile"), tile_seen=(du.get("tile") in tiles) if du.get("tile") else None, due_n=None, door_seen=None)
        try:
            rr = ro.execute(str(du.get("due_sql") or "").rstrip(";")).fetchone()
            row["due_n"] = int((rr[0] if rr else 0) or 0)
        except Exception as e:                                          # noqa: BLE001
            row["due_n"] = "ERR " + str(e)[:80]
        door, mark = du.get("door"), du.get("door_marker")
        if door and mark and isinstance(row["due_n"], int) and row["due_n"] > 0 and str(door).startswith("/finance/"):
            path, body = str(door), ""
            for _hop in range(4):
                r = fc.get(path, base_url=BASE, headers=ck["amir"])
                if r.status_code in (301, 302, 303) and r.headers.get("Location", "").startswith(("/finance/", BASE + "/finance/")):
                    path = r.headers["Location"].replace(BASE, "")
                    continue
                body = r.get_data(as_text=True)
                break
            row["door_seen"] = mark in body
        duties.append(row)
    ro.close()
    out["eye"] = dict(first=[r1.status_code, r1.headers.get("Location", "")], tiles=tiles, duties=duties, version=dm.get("version"))
    P = dict(key_entered="%d|%s|%d" % ent_vis[0] if ent_vis else None, med="%d|%s|%d" % med, walk="%d|%s|%d" % kb)
    P["amir_clear_entered"] = post("amir", ent_vis[0], clear=True) if ent_vis else None
    P["amir_reenter_entered"] = post("amir", ent_vis[0]) if ent_vis else None
    P["amir_med"] = post("amir", med)
    P["amir_open"] = post("amir", kb)
    P["amir_open_again"] = post("amir", kb)
    P["owner_clear_walk"] = post("manoj", kb, clear=True)
    P["amir_fresh"] = post("amir", kb, no="W528FRESH")
    P["owner_clear_walk_2"] = post("manoj", kb, clear=True)
    P["amir_fresh_dup"] = post("amir", kb, no=ent[ent_vis[0]][0] if ent_vis else "X")        # the same Marg number as an existing voucher -> the owner's line
    rr = fc.post("/finance/stock/api/pad/rename/tick", base_url=BASE, headers=ck["amir"], json=dict(old=[r["old_name"] for r in IA.rows(c) if r["done_at"] and not r["verified_at"]][0], clear=True))
    P["amir_rename_clear"] = [rr.status_code, (rr.get_json(silent=True) or {}).get("error")]
    rr = fc.post("/finance/stock/api/pad/rename/accept", base_url=BASE, headers=ck["amir"], json=dict(rename_id=1, seen_name="X"))
    P["amir_accept"] = [rr.status_code, (rr.get_json(silent=True) or {}).get("error")]
    rr = fc.post("/finance/stock/api/pad/rename/accept", base_url=BASE, headers=ck["manoj"], json=dict(rename_id=1, seen_name="X"))
    P["owner_accept_none"] = [rr.status_code, (rr.get_json(silent=True) or {}).get("error")]
    out["post"] = P
    if NEW:
        SA._S446_PROOF_CACHE.clear()
        sw = SA._s521_stage_words(c, real_stage(c, root))
        out["dup_line"] = [l["text"] for l in sw["owner_lines"] if l["text"].startswith("Marg voucher number")]
        out["entered_on_new"] = c.execute("SELECT entered_on FROM stock_voucher_entered WHERE count_id=? AND marg_voucher_no='W528FRESH'", (root,)).fetchone()
        bl = SA._amir_board_light(c, root, dict(user="manoj", role="doctor", roles=["checker"]), real_stage(c, root))
        out["on_rendered"] = [v["entered"]["on"] for v in bl["vouchers"] if v["entered"]][:3]
    # F-853: the upload door
    data = {"file": (io.BytesIO(b"W528 walk text\n"), "w528.txt"), "item": "", "note": "W528"}
    rr = fc.post("/finance/stock/api/pad/marg_answer/%d" % root, base_url=BASE, headers=ck["amir"], data=data, content_type="multipart/form-data")
    out["marg_answer_amir"] = [rr.status_code, (rr.get_json(silent=True) or {}).get("error")]
    data = {"file": (io.BytesIO(b"W528 walk text\n"), "w528b.txt"), "item": "", "note": "W528"}
    rr = fc.post("/finance/stock/api/pad/marg_answer/%d" % root, base_url=BASE, headers=ck["manoj"], data=data, content_type="multipart/form-data")
    out["marg_answer_owner"] = [rr.status_code, (rr.get_json(silent=True) or {}).get("error")]
    # the staff pages: steps 1-7, his home, the board (words listed; the kit's strings asserted); the staff-eye duties
    steps = {}
    for n in range(1, 8):
        rr = fc.get("/finance/amir/step/%d" % n, base_url=BASE, headers=ck["amir"])
        h = rr.get_data(as_text=True)
        steps[n] = dict(code=rr.status_code, bad=bad_hits(h), khol=kholiye_hits(h), marker=("Marg sudhar" in h), card=("s444duty" in h))
    out["steps"] = steps
    rr = fc.get("/finance/amir/salts", base_url=BASE, headers=ck["amir"])
    out["salts_page"] = rr.status_code
    # the owner's pages: the hub, the orthotic section, the statement, Needs-you, the visit summary
    rr = fc.get("/finance/stock/api/pad/hub/%d" % root, base_url=BASE, headers=ck["manoj"])
    j = rr.get_json(silent=True) or {}
    Pp = j.get("proof") or {}
    O = j.get("ortho") or {}
    out["hub"] = dict(code=rr.status_code, state=Pp.get("state"), text=Pp.get("text"), rows=[(r.get("item"), r.get("why")) for r in (Pp.get("rows") or [])][:6],
                      lines=[l.get("text") for l in (Pp.get("lines") or [])][:6], ortho_ok=O.get("ok"), ortho_proof=[(x.get("ok"), x.get("en")) for x in (O.get("conds") or []) if x.get("key") == "proof"])
    out["hub_page"] = fc.get("/finance/stock/page/hub?count=%d" % root, base_url=BASE, headers=ck["manoj"]).status_code
    out["sm_page"] = fc.get("/finance/stockmatch", base_url=BASE, headers=ck["manoj"]).status_code
    rr = fc.get("/finance/stockmatch/api/state", base_url=BASE, headers=ck["manoj"])
    out["sm_api"] = rr.status_code
    out["statement_page"] = fc.get("/finance/stock/page/statement?count=%d" % root, base_url=BASE, headers=ck["manoj"]).status_code
    rr = fc.get("/finance/stock/api/statement/%d" % root, base_url=BASE, headers=ck["manoj"])
    out["statement_api"] = rr.status_code
    rr = fc.get("/finance/sanjeevni/api/needs-you", base_url=BASE, headers=ck["manoj"])
    j = rr.get_json(silent=True) or {}
    out["needs_you"] = dict(code=rr.status_code, n=len(j.get("lines") or []), bad_shape=[l for l in (j.get("lines") or []) if not (isinstance(l, dict) and "cls" in l and "target" in l and "text" in l)][:3],
                            stock=[l.get("text") for l in (j.get("lines") or []) if l.get("target") == "stock"][:5])
    rr = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE, headers=ck["manoj"])
    j = rr.get_json(silent=True) or {}
    out["visit"] = dict(code=rr.status_code, keys=sorted(j.keys()), states=sorted({s.get("state") for s in (j.get("steps") or [])}), left=j.get("left"))
    if NEW:
        SA._S446_PROOF_CACHE.clear()
        sw = SA._s521_stage_words(c, real_stage(c, root))
        out["sw_now"] = dict(card_hi=sw["card_hi"], owner_en=sw["owner_en"], lines_bad=bad_hits(json.dumps(sw["lines"], ensure_ascii=False)), lines_khol=kholiye_hits(json.dumps(sw["lines"], ensure_ascii=False)))
    out["ev_end"] = events(c, root)
    out["ms_board_amir"] = board("amir")["ms"]
    out["ms_board_owner"] = board("manoj")["ms"]
    c.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def run_probe(a, mode, side, Wd, store, secret, pw):
    fin = os.path.join(a.run, side, "finance")
    ing = os.path.join(a.run, side, "marg_ingest")
    wd = os.path.join(Wd, "%s_%s" % (mode, side))
    for sub in ("nosso", "noring", "nomarg"):
        os.makedirs(os.path.join(wd, sub))
    dbp, adbp, spp = [os.path.join(wd, "w528_%s.db" % x) for x in ("app", "assets", "spine")]
    copydb(a.db, dbp)
    copydb(a.adb, adbp)
    copydb(a.spine, spp)
    env = dict(os.environ, SIDE=side, FINDIR=fin, INGDIR=ing, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W528_DB0=a.db, W528_SPINE0=a.spine,
               FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "api" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
               CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W528J=json.dumps(dict(pw=pw)),
               W528_DUTY_MAP=os.path.abspath(a.duty_map), MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"),
               ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"), ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"),
               SR_DB_PATH=os.path.join(wd, "no_staff_register.db"), CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
    for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE", "FINANCE_CRON_TOKEN"):
        env.pop(k, None)
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True, timeout=2400)
    js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
    if not js:
        print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
        for l in p.stdout.splitlines()[-40:]:
            print("   " + mask(l)[:300])
        return None
    return json.loads(js[-1][len(TAG):])


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-api"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_api()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--run", "--por", "--db", "--adb", "--spine", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W528 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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

    # ------------------------------------------------------------------------------------------------------------------------------- greps
    print("-- 10 the greps over the NEW finance folder (every retired name; amir_day's own S488 tail is Kit 3's dead code, named), selftest")
    fin_new = os.path.join(a.run, "new", "finance")
    hits = []
    for fn in sorted(os.listdir(fin_new)):
        if fn.endswith((".py", ".html")) and ".bak_" not in fn:
            t = io.open(os.path.join(fin_new, fn), encoding="utf-8", errors="replace").read()
            for bad in RETIRED:
                if bad in RETIRED_EXEMPT.get(fn, ()):
                    continue
                if re.search(r"(^|[^A-Za-z0-9_])" + re.escape(bad) + r"($|[^A-Za-z0-9_])", t):
                    hits.append((fn, bad))
            if re.search(r"(^|[^A-Za-z0-9_])_amir_board\(", t) or "def _amir_board(" in t:
                hits.append((fn, "_amir_board("))
    check("every retired name is gone from the NEW finance folder (comments included): %s" % ", ".join(RETIRED + ("_amir_board",)), not hits, hits)
    t_ad = io.open(os.path.join(fin_new, "amir_day.py"), encoding="utf-8").read()
    check("amir_day's own code writes no stock_stage_event (grep)", "stock_stage_event" not in t_ad)
    check("amir_day no longer carries the stage branch tree: no 'Voucher kholiye', no 'Theek karke', no '_s446_wrong_lines', no 'Marg mein yeh abhi sahi nahi'",
          not any(x in t_ad for x in ("Voucher kholiye", "Theek karke", "_s446_wrong_lines", "Marg mein yeh abhi sahi nahi hain")))
    t_html = io.open(os.path.join(fin_new, "stock_amir.html"), encoding="utf-8").read()
    check("stock_amir.html keeps the three strings the server depends on, and carries no upload box, no 'Wapas', no 'Server ko bhejo', no 'Marg = shelf', no 'theek karna hai'",
          all(s in t_html for s in ('<body><div class="wrap">', "/*__BOOT__*/", '<div class="card"><h2><span class="n">4</span>', '"Aur voucher kholiye', "Internet dekh kar phir kholiye"))
          and not any(s in t_html for s in ('type="file"', "marg_answer", "Wapas", "Server ko bhejo", "Marg = shelf", "theek karna hai", "abhi nahi dikhe")), bad_hits(t_html))
    kh = kholiye_hits(t_html)
    check("every 'kholiye' in the new page is a door's verb (%d hits)" % len(kh), kh and all(ok for ok, _ in kh), kh)
    sp_new = os.path.join(fin_new, "spine")
    p = subprocess.run([sys.executable, "-B", os.path.join(sp_new, "selftest_spine.py")], cwd=sp_new, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=900)
    check("selftest_spine.py is green on the scratch spine folder", p.returncode == 0 and "SELFTEST OK" in p.stdout, p.stdout.strip().splitlines()[-1:])

    # ------------------------------------------------------------------------------------------------------------------------------- fn
    print("-- 0-6 the functions on their own copies (NEW), the same on the OLD files (controls)")
    FN = run_probe(a, "fn", "new", Wd, store, secret, pw)
    if not check("the NEW function probe ran to the end and the file carries _s521_stage_words", FN is not None and FN.get("new")):
        return finish()
    FO = run_probe(a, "fn", "old", Wd, store, secret, pw)
    if not check("the OLD function probe ran to the end", FO is not None):
        return finish()
    print("   root %s; spine built %s; newest sp_close %s; roles %s" % (FN["root"], FN["built"], FN["newest_close"], FN["roles"]))
    print("   stage on the plain copy (NEW): %s" % mask(FN["stage0"]))
    print("   the 23 rename rows (state, tick): %s" % mask(FN["renames0"]))
    print("   the window (FIRST entry per key): %s" % mask(FN.get("window0")))
    print("   newest entries per key: %s" % mask(FN.get("entered0")))
    print("   the table: %s" % mask(FN.get("T0")))
    print("   proof on the plain copy NEW: %s" % mask(FN["reg"]))
    print("   proof on the plain copy OLD: %s" % mask(FO["reg"]))
    print("   the words on the plain copy (install-day state): %s" % mask(FN["words0"]))
    print("   OLD card/board words on the plain copy: %s" % mask(FO["three"]))
    roles = FN["roles"]
    check("walk 0: the copy's roles -- 'checker' is not among amir's and is among the owner's (else the door checks are void) %s" % roles,
          not any(r[1] == "checker" and r[2] == "amir" for r in roles) and any(r[1] == "checker" and r[2] == "manoj" for r in roles), roles)
    check("walk 0: a stage-A root exists on the copy (stage %s); the 22 ticked rows exist by old_name (%d ticked, %d verified)" % (FN["stage0"]["stage"], sum(1 for r in FN["renames0"] if r[1] in ("done", "amber", "question")), sum(1 for r in FN["renames0"] if r[1] == "verified")),
          FN["stage0"]["stage"] == "A" and sum(1 for r in FN["renames0"] if r[1] in ("done", "amber", "question")) == 22, FN["renames0"])
    check("walk 10: a second identical read writes no stage event (once-only): %d -> %d -> %d" % (len(FN["ev0"]), len(FN["ev1"]), len(FN["ev2"])), FN["ev1"] == FN["ev2"], (FN["ev1"], FN["ev2"]))
    # F-851
    f = FN["f851"]
    fo = FO["f851"]
    print("   F-851 NEW short reach: %s" % mask(f.get("short")))
    print("   F-851 NEW words then: %s" % mask(f.get("short_words")))
    print("   F-851 NEW covered: %s" % mask(f.get("covered")))
    print("   F-851 NEW absent at N: %s" % mask(f.get("absent_at_N")))
    print("   F-851 OLD short reach: %s" % mask(fo.get("short")))
    s = f.get("short") or {}
    check("F-851: with the purchase reach short of the newest capture, the TYNOR key is 'waiting' -- state export, why pur_behind, the key in unseen (reach_pur), no rows",
          s.get("state") == "export" and s.get("why") == "pur_behind" and not s.get("rows") and any(u[0] == TYNOR and u[1] == "reach_pur" for u in s.get("unseen") or []), s)
    sw1 = f.get("short_words") or {}
    check("F-851: his card then reads 'Orthotic voucher daal diye ✓ · Purchase report nikaaliye' (+ the B line) and the owner's English says 'waiting'",
          str(sw1.get("card_hi") or "").startswith("Orthotic voucher daal diye ✓ · Purchase report nikaaliye") and "waiting" in str(sw1.get("owner_en")) and "do not agree" not in str(sw1.get("owner_en")), sw1)
    check("control OLD F-851: the same copy -> 'wrong' with the TYNOR row", (fo.get("short") or {}).get("state") == "wrong" and any(r[0] == TYNOR for r in (fo.get("short") or {}).get("rows") or []), fo.get("short"))
    cv = f.get("covered") or {}
    check("F-851: a purchase export reaching 10-Oct (a later stamp, sp_meta.built bumped) -> the proof judges at the newest capture: state %s, TYNOR proven %s" % (cv.get("state"), TYNOR in (cv.get("proven_on") or [])),
          cv.get("state") in ("done", "wrong") and TYNOR in (cv.get("proven_on") or []) and not any(u[0] == TYNOR for u in cv.get("unseen") or []), cv)
    ab = f.get("absent_at_N") or {}
    check("R1-C2: the key absent from the newest closing keeps its own why (absent_at_try), never 'wrong', never 'reach'",
          any(u[0] == TYNOR and u[1] == "absent_at_try" for u in ab.get("unseen") or []) and not any(r[0] == TYNOR for r in ab.get("rows") or []), ab)
    # the window
    w = FN["win"]
    wo = FO["win"]
    print("   window NEW: %s" % mask(w))
    print("   window OLD: %s" % mask(wo))
    check("R3-1: the earliest key cleared by the owner and entered again after a clean closing captured between its first entry and the next key's -> _s446_window keeps the first time (%s), the verdict unchanged (%s -> %s), R unchanged"
          % (w.get("window_k1"), (w.get("before") or {}).get("state"), (w.get("after") or {}).get("state")),
          w.get("window_k1") == (w.get("setup") or {}).get("t1") and (w.get("after") or {}).get("state") == (w.get("before") or {}).get("state") and (w.get("after") or {}).get("as_before") == (w.get("before") or {}).get("as_before")
          and (w.get("after") or {}).get("rows") == (w.get("before") or {}).get("rows"), w)
    check("control OLD R3-1: the same copies -> the proof's window moves to the re-entry and the verdict is lost: 'wrong' (R = the closing that already carries the voucher) (%s -> %s)" % ((wo.get("before") or {}).get("state"), (wo.get("after") or {}).get("state")),
          (wo.get("after") or {}).get("state") == "wrong" and (wo.get("after") or {}).get("state") != (wo.get("before") or {}).get("state"), wo)
    # F-854
    f = FN["f854"]
    fo = FO["f854"]
    print("   F-854 setup: %s" % mask(f.get("setup")))
    print("   F-854 NEW main: %s" % mask({k: v for k, v in (f.get("main") or {}).items() if k != "states"}))
    print("   F-854 NEW states: %s" % mask((f.get("main") or {}).get("states")))
    for k in ("main_again", "fold", "dot", "both", "read_back", "before_tick", "no_capture", "short", "collision", "prefix", "retick", "section_state", "snapshot_calls"):
        print("   F-854 NEW %-14s %s" % (k, mask(f.get(k))))
    print("   F-854 OLD main: %s (snapshot calls %s)" % (mask(fo.get("main")), fo.get("snapshot_calls")))
    m = f.get("main") or {}
    check("F-854: a closing printed for the day BEFORE the tick, captured an hour after it, with the new names (one old kept) -> 21 verified, the kept one not seen (seen_n 1), B.verified 22 of 23, no question, no collision",
          m.get("verified") == 21 and m.get("kept_state") in ("done",) and m.get("kept_seen_n") == 1 and (m.get("B") or {}).get("verified") == 22 and not m.get("questions") and m.get("collisions") == 0, m)
    check("F-854: the events are written (seen + verified per row) and verified_k20 / verified_captured carry the key and the capture", dict(m.get("events") or []).get("verified") == 21 and all(x[1] and x[2] for x in m.get("k20_sample") or []), m.get("events"))
    check("F-854: the same closing sighted again judges nothing twice (0 verified, seen_n unchanged)", (f.get("main_again") or {}).get("verified") == 0 and (f.get("main_again") or {}).get("kept_seen_n") == 1, f.get("main_again"))
    check("control OLD F-854: the day rule throws that closing away -> 0 verified", (fo.get("main") or {}).get("verified") == 0, fo.get("main"))
    fd = f.get("fold") or {}
    check("F-854 folds: a double space and a trailing dot still verify", fd.get("verified") == fd.get("expect"), fd)
    dq = f.get("dot") or {}
    check("F-854 near-miss: an inner dot -> state question with the seen name; the owner's Accept -> verified; the chain question -> accepted (the live ticks predate the event table); a later exact sighting supersedes a question",
          dq.get("state") == "question" and dq.get("q") and (dq.get("accept") or [None])[0] is True and (dq.get("accept") or [0, 0, None])[2] == "verified" and (dq.get("chain") or [])[-2:] == ["question", "accepted"]
          and (dq.get("supersede") or {}).get("state") == "verified" and ((dq.get("supersede") or {}).get("chain") or [])[-3:] == ["question", "seen", "verified"], dq)
    bq = f.get("both") or {}
    check("F-854 both: old and new both printed -> state question, event both, Accept refused", bq.get("state") == "question" and bq.get("event") == "both" and (bq.get("accept") or [None])[0] is False, bq)
    rb = f.get("read_back") or {}
    check("F-854 read-back (B12): a planned row whose new name appears -> read_back, ticked by 'marg', verified, the staff line 'Marg mein dikh gaya'", rb.get("read_back") and rb.get("state") == "verified" and rb.get("done_by") == "marg" and "dikh gaya" in str(rb.get("staff_hi")), rb)
    check("F-854: a closing captured before the tick -> nothing (0 verified, 0 events); no capture given -> refused with a line", (f.get("before_tick") or {}).get("verified") == 0 and (f.get("before_tick") or {}).get("events") == 0 and (f.get("no_capture") or {}).get("skipped") == "no_captured", (f.get("before_tick"), f.get("no_capture")))
    sh = f.get("short") or {}
    check("F-854 sight_closing: a 30%% list is SHORT -> skipped (needs %s); the whole list -> %s verified" % (sh.get("need"), sh.get("whole")), sh.get("skipped") == "short" and sh.get("verified") == 0 and sh.get("whole") == 21, sh)
    co = f.get("collision") or {}
    check("F-854 collision: another listed name with the same 20-letter key (neither old nor new) -> event collision, a question naming it", co.get("state") == "question" and co.get("event") == "collision" and co.get("seen"), co)
    pf = f.get("prefix") or {}
    check("F-854 (the 10-10 closing's own shape): a printed spelling that is a prefix of the new name -> a question for the owner, never 'not seen'", pf.get("state") == "question" and pf.get("seen") == pf.get("printed"), pf)
    rt = f.get("retick") or {}
    check("R2-17: untick (checker) marks undone_at and keeps done_at; a re-tick writes a new tick event and clears undone_at; the chain tick, untick, tick",
          (rt.get("untick") or [None, None, None, False, False])[2] == "planned" and (rt.get("untick") or [0, 0, 0, False])[3] is True and (rt.get("untick") or [0, 0, 0, 0, False])[4] is True
          and (rt.get("tick") or [None, None, None, "x"])[2] == "done" and (rt.get("tick") or [0, 0, 0, "x"])[3] is None and (rt.get("chain") or [])[-2:] == ["untick", "tick"], rt)
    ss = f.get("section_state") or {}
    check("R1-B4 / R2-27c: stockmatch.section_state runs on a copy holding a question row (summary does not raise): %s" % mask(ss.get("renames_cond")), ss.get("ok") is True, ss)
    check("api_snapshot no longer tells the rename memory (0 calls of item_alias.verify_closing in the NEW stock_app; OLD had %s)" % fo.get("snapshot_calls"), f.get("snapshot_calls") == 0 and fo.get("snapshot_calls") == 1, f.get("snapshot_calls"))
    # the words
    W = FN["words"]
    for k in ("a_open", "a_wrong", "dup", "b_all", "b_open", "c_open", "c_wait", "c_judged", "done", "none", "error"):
        if k in W:
            print("   words %-9s %s" % (k, mask({kk: vv for kk, vv in (W[k].items() if isinstance(W[k], dict) else [("v", W[k])]) if kk != "card"})))
    ao = W.get("a_open") or {}
    check("words A open: 'Orthotic ke voucher: 1 baaki — board kholiye' with the vouchers anchor, then the B line 'Naam badal diye ✓'; owner 'Stage A: 7 of 8 entered'; the card prints the same lines",
          (ao.get("lines") or [{}])[0].get("hi") == "Orthotic ke voucher: 1 baaki — board kholiye" and (ao.get("lines") or [{}])[0].get("anchor") == "vouchers"
          and ao.get("card_hi") == "Orthotic ke voucher: 1 baaki — board kholiye · Naam badal diye ✓" and str(ao.get("owner_en")).startswith("Stage A: 7 of 8 entered")
          and "Orthotic ke voucher: 1 baaki" in _html.unescape(ao.get("card") or "") and "board kholiye" in _html.unescape(ao.get("card") or "") and "#vouchers" in (ao.get("card") or ""), ao)
    aw = W.get("a_wrong") or {}
    check("words A wrong: the staff line is only 'Orthotic voucher daal diye ✓' (no verdict); the owner reads 'do not agree with Marg's closing of dd-mm-yyyy' and his lines name the voucher, the item and the words; the hub says the same",
          (aw.get("lines") or [{}])[0].get("hi") == "Orthotic voucher daal diye ✓" and "do not agree with Marg's closing of" in str(aw.get("owner_en")) and aw.get("owner_lines")
          and all(l.startswith("Voucher ") and TYNOR in l and "Marg moved" in l and "the voucher said" in l for l in aw["owner_lines"] if l.startswith("Voucher"))
          and (aw.get("hub") or {}).get("text") == aw.get("owner_en") and (aw.get("hub") or {}).get("state") == "now" and (aw.get("hub") or {}).get("lines") == [l for l in aw["owner_lines"]]
          and any("do not agree" in l.get("text", "") for l in aw.get("needs_you") or []) and sum(1 for l in aw.get("needs_you") or [] if l.get("text", "").startswith("Voucher ")) == len([l for l in aw["owner_lines"] if l.startswith("Voucher")]), aw)
    check("words D708: no staff line of any state carries jaanch / wapas / theek / sahi nahi / hona chahiye / Marg = shelf",
          not any(bad_hits(json.dumps(W[k].get("lines"), ensure_ascii=False)) for k in ("a_open", "a_wrong", "b_all", "b_open", "c_open", "c_wait", "c_judged", "done") if isinstance(W.get(k), dict)),
          {k: bad_hits(json.dumps(W[k].get("lines"), ensure_ascii=False)) for k in ("a_open", "a_wrong", "b_all", "b_open", "c_open", "c_wait", "c_judged", "done") if isinstance(W.get(k), dict)})
    check("words: a Marg voucher number typed on two keys -> the owner's line 'Marg voucher number N is written on vouchers ...'", W.get("dup") and "is written on vouchers" in W["dup"][0] and " and " in W["dup"][0], W.get("dup"))
    ba, bo = W.get("b_all") or {}, W.get("b_open") or {}
    check("words B all ticked (the pending line cleared, proof %s -> stage %s): 'Naam badal diye ✓'; owner 'Stage B: 1 of 23 seen in Marg'" % (ba.get("proof"), ba.get("stage")),
          ba.get("stage") == "B" and ba.get("card_hi") == "Naam badal diye ✓" and str(ba.get("owner_en")).startswith("Stage B: 1 of 23 seen in Marg"), ba)
    check("words B open: one row taken back -> 'Naam badalna: 1 baaki — board kholiye' (anchor renames); owner 'Stage B: 1 of 23 seen in Marg; 1 to tick'; step 7's line and the owner's left line read the same",
          bo.get("card_hi") == "Naam badalna: 1 baaki — board kholiye" and (bo.get("lines") or [{}])[0].get("anchor") == "renames" and bo.get("owner_en") == "Stage B: 1 of 23 seen in Marg; 1 to tick"
          and bo.get("extra_hi") == [bo.get("card_hi")] and bo.get("left") == [bo.get("owner_en")], bo)
    co_ = W.get("c_open") or {}
    check("words C released: 'Dawa ke voucher: 12 — board kholiye' (anchor vouchers); owner 'Stage C: 0 of N entered · 12 released · 0 verified'; no B line once B is verified",
          co_.get("stage") == "C" and co_.get("card_hi") == "Dawa ke voucher: 12 — board kholiye" and re.match(r"^Stage C: 0 of \d+ entered · 12 released · 0 verified$", str(co_.get("owner_en"))), co_)
    cw = W.get("c_wait") or {}
    check("words C waiting: the lot entered, no closing after it -> 'Dawa ke voucher daal diye ✓'; owner 'Stage C: lot 1 entered on dd-mm-yyyy — waiting: ...'",
          cw.get("card_hi") == "Dawa ke voucher daal diye ✓" and re.match(r"^Stage C: lot 1 entered on \d\d-\d\d-\d{4} — waiting: ", str(cw.get("owner_en"))) and (cw.get("C") or {}).get("waiting") == 1, cw)
    cj = W.get("c_judged") or {}
    check("words C judged by the real closings (lot entered 04-Oct; the medicine vouchers never reached Marg): the staff line stays 'Dawa ke voucher daal diye ✓'; the owner's English follows the state (%s); the hub says the same" % ((cj.get("C") or {}).get("wrong") and "wrong" or "waiting/done"),
          cj.get("card_hi") == "Dawa ke voucher daal diye ✓" and ((cj.get("C") or {}).get("wrong") == 0 or "do not agree with Marg's closing of" in str(cj.get("owner_en"))) and (cj.get("hub") or {}).get("text") == cj.get("owner_en"), cj)
    dn = W.get("done") or {}
    check("words done: 'Stock ke voucher poore ✓'; owner 'all vouchers entered and verified'; the card and the hub print the same", dn.get("stage") == "done" and dn.get("card_hi") == "Stock ke voucher poore ✓" and dn.get("owner_en") == "all vouchers entered and verified"
          and "Stock ke voucher poore" in _html.unescape(dn.get("card") or "") and dn.get("hub_text") == dn.get("owner_en"), dn)
    check("words: st None -> empty words (no raise)", (W.get("none") or {}).get("card_hi") == "" and (W.get("none") or {}).get("lines") == [], W.get("none"))
    th = FN["three"]
    check("three reads, one string (the install-day state): the card prints every stage line, the board's proof.hi == the hub's words' board_hi, the owner's board the same, the hub's text == owner_en",
          all(th.get("card_has") or [False]) and th.get("board_hi") == FN["words0"]["card_hi"] and th.get("owner_board_hi") == th.get("board_hi") and th.get("hub_text") == FN["words0"]["owner_en"], th)
    awo = (FO.get("words") or {}).get("a_wrong_old") or {}
    print("   OLD words in the wrong state: %s" % mask(awo))
    check("control OLD: in the wrong state the old card tells Amir to check a voucher and the old board says 'Marg = shelf: N theek karna hai' (proof %s): %s" % (awo.get("proof"), mask(awo.get("card_bad"))),
          awo.get("proof") == "wrong" and bool(awo.get("card_bad")) and "Marg = shelf" in str(awo.get("board_hi")), awo)
    # numbers, light board (fn level)
    nm = FN["numbers"]
    L = FN["light"]
    print("   numbers: %s" % mask(nm))
    print("   light board (fn): %s" % mask({k: v for k, v in L.items() if k not in ("khol",)}))
    print("   OLD board (fn): bytes %s, bad %s, seq_3I1 %s" % (FO["light"].get("bytes"), mask(FO["light"].get("bad")), FO["light"].get("seq_3I1")))
    check("one number: _voucher_seq == _voucher_numbers (every item of 3|ISSUE|1 carries its label) == _s437_flat == amir_stage.numbers == the light payload (amir and the owner) for 3|ISSUE|1 (%s), for every batch (%d)" % (nm.get("seq_3I1"), nm.get("n") or 0),
          nm.get("seq_3I1") and nm.get("flat_3I1") == nm["seq_3I1"][0] and nm.get("numbers_every_item") and nm.get("flat_eq") and nm.get("stage_numbers_eq") and L.get("seq_3I1") == [nm["seq_3I1"][0]] and L.get("owner_seq_3I1") == [nm["seq_3I1"][0]], nm)
    check("control OLD one number: amir's visible subset was renumbered from 1 on the old board (3|ISSUE|1 read %s, the whole count says %s)" % (FO["light"].get("seq_3I1"), nm.get("seq_3I1")),
          FO["light"].get("seq_3I1") == [1] and (nm.get("seq_3I1") or [0])[0] != 1, FO["light"].get("seq_3I1"))
    check("light board (fn): %d bytes as amir (< 100 KB); the fields the page reads present; stage for the checker too; renames.rows empty for amir (all ticked) with done_hi; last_closing filled; no take-back word for amir, can_clear for the owner"
          % L.get("bytes", 0),
          L.get("bytes", 10 ** 9) < 100 * 1024 and set(L.get("keys") or []) >= {"count_id", "day", "you", "stage", "vouchers", "proof", "renames", "salt_fix", "rate_tasks", "rest", "last_closing"}
          and L.get("owner_stage") and (L.get("renames") or {}).get("rows") == 0 and (L.get("renames") or {}).get("done_hi") and (L.get("renames") or {}).get("owner_rows") == 23
          and L.get("last_closing") and L.get("clear_amir") == 0 and L.get("clear_owner") > 0 and not L.get("bad") and not L.get("owner_bad")
          and set((L.get("field_shapes") or {}).get("v") or []) >= {"seq", "kind", "n", "title_hi", "round_no", "batch_no", "entered", "can_clear", "lines"}
          and set((L.get("field_shapes") or {}).get("line") or []) == {"item", "packing", "from_hi", "to_hi", "change_sign", "qty_hi"}, L)
    check("control OLD board: %d bytes (over 100 KB) -- the whole report in Amir's hands" % FO["light"].get("bytes", 0), FO["light"].get("bytes", 0) > 100 * 1024, FO["light"].get("bytes"))
    nb = FN["nb"]
    print("   not broken (fn): %s" % mask(nb))
    check("Needs-you renders; each line dict(cls, target, text[, duty]); the jobs card HTML byte-equal old vs new",
          nb.get("needs_you") and all(set(s) >= {"cls", "target", "text"} for s in nb["needs_you"]["shapes"]) and nb.get("jobs_html") == FO["nb"].get("jobs_html"), (nb.get("needs_you", {}).get("shapes"), nb.get("jobs_html"), FO["nb"].get("jobs_html")))

    # ------------------------------------------------------------------------------------------------------------------------------- api
    print("-- 2,3,7,8,9 the routes on a copy through a walk-only portal as amir and as the owner (the door, the board, the page, the home, the hub)")
    AN = run_probe(a, "api", "new", Wd, store, secret, pw)
    AO = run_probe(a, "api", "old", Wd, store, secret, pw)
    if not check("both route probes ran to the end", AN is not None and AO is not None):
        return finish()
    for k in ("board_amir_1", "board_owner", "page_amir", "page_owner", "post", "dup_line", "entered_on_new", "on_rendered", "marg_answer_amir", "marg_answer_owner", "eye", "hub", "needs_you", "visit", "sw_now", "salts_page", "statement_page", "statement_api", "sm_page", "sm_api", "hub_page"):
        print("   NEW %-16s %s" % (k, mask({kk: vv for kk, vv in AN.get(k).items() if kk != "khol"} if isinstance(AN.get(k), dict) else AN.get(k))))
    for k in ("board_amir_1", "page_amir", "post", "marg_answer_amir", "hub", "visit"):
        print("   OLD %-16s %s" % (k, mask({kk: vv for kk, vv in AO.get(k).items() if kk != "khol"} if isinstance(AO.get(k), dict) else AO.get(k))))
    for n_ in range(1, 8):
        print("   NEW step %d: code %s, marker %s, words listed: %s, kholiye: %s" % (n_, AN["steps"][str(n_)]["code"], AN["steps"][str(n_)]["marker"], mask(AN["steps"][str(n_)]["bad"]), [x for x in AN["steps"][str(n_)]["khol"]]))
    P = AN["post"]
    check("F-852 as amir: clear on an entered visible key -> 403 checker_only; a number on it -> 409 already; an unreleased medicine key -> 403 not_released; the open walk batch -> 200 'Likh liya: ...'; a second entry -> 409",
          (P.get("amir_clear_entered") or [0])[0] == 403 and (P.get("amir_clear_entered") or [0, ""])[1] == "checker_only" and (P.get("amir_reenter_entered") or [0])[0] == 409 and (P.get("amir_reenter_entered") or [0, ""])[1] == "already"
          and P["amir_med"][0] == 403 and P["amir_med"][1] == "not_released" and P["amir_open"][0] == 200 and str(P["amir_open"][2]).startswith("Likh liya: ") and "Marg number" in str(P["amir_open"][2])
          and P["amir_open_again"][0] == 409, P)
    check("F-852 as the owner: clear -> 200 'Wapas le liya.'; amir's fresh entry -> 200; rename clear as amir -> 403; Accept as amir -> 403; the owner's Accept with no question -> 400 refused",
          P["owner_clear_walk"][0] == 200 and P["owner_clear_walk"][2] == "Wapas le liya." and P["amir_fresh"][0] == 200 and P["amir_rename_clear"] == [403, "checker_only"] and P["amir_accept"][0] == 403
          and P["owner_accept_none"][0] == 400, P)
    check("control OLD F-852: amir's clear on an entered key -> 200; his second entry -> 200; his rename clear -> not 403", (AO["post"].get("amir_clear_entered") or [0])[0] == 200 and (AO["post"].get("amir_reenter_entered") or [0])[0] == 200 and AO["post"]["amir_rename_clear"][0] != 403, AO["post"])
    check("R1-C14: a new entry's entered_on is ISO (%s) and every reader prints dd-mm-yyyy (%s); the dup Marg number gives the owner's line" % (AN.get("entered_on_new"), AN.get("on_rendered")),
          re.match(r"^\d{4}-\d\d-\d\d$", str((AN.get("entered_on_new") or [""])[0])) and all(re.match(r"^\d\d-\d\d-\d{4}$", str(x)) for x in AN.get("on_rendered") or []) and AN.get("dup_line"), (AN.get("entered_on_new"), AN.get("on_rendered"), AN.get("dup_line")))
    check("F-853: the board page as amir has no file input and no marg_answer call (the bar and the rest id kept); api_pad_marg_answer as amir -> 403, as the owner -> 200",
          AN["page_amir"]["code"] == 200 and not AN["page_amir"]["file_input"] and not AN["page_amir"]["marg_answer"] and AN["page_amir"]["bar"] and AN["page_amir"]["rest"] and AN["page_amir"]["boot"]
          and AN["marg_answer_amir"][0] == 403 and AN["marg_answer_owner"][0] == 200, (AN["page_amir"], AN["marg_answer_amir"], AN["marg_answer_owner"]))
    check("control OLD F-853: the page carried the upload box and amir could post to marg_answer (200)", AO["page_amir"]["file_input"] and AO["marg_answer_amir"][0] == 200, (AO["page_amir"]["file_input"], AO["marg_answer_amir"]))
    b1 = AN["board_amir_1"]
    check("the light board through the route as amir: 200, %d bytes (< 100 KB), %d ms warm (< 2000; the copy's cold first read %d ms is the stage's report build), amir_stage called once, no take-back word; the owner's board carries the same proof line" % (b1["bytes"], AN["board_amir_2"]["ms"], b1["ms"]),
          b1["code"] == 200 and b1["bytes"] < 100 * 1024 and AN["board_amir_2"]["ms"] < 2000 and b1["stage_calls"] == 1 and b1["clear"] == 0 and not b1["bad"] and AN["board_owner"]["proof"] == b1["proof"] and AN["board_owner"]["stage_calls"] == 1, b1)
    check("control OLD board through the route: %d bytes (> 100 KB)" % AO["board_amir_1"]["bytes"], AO["board_amir_1"]["bytes"] > 100 * 1024, AO["board_amir_1"]["bytes"])
    check("the first board read wrote no new stage event beyond the once-only ones, the second none: %d -> %d -> %d" % (len(AN["ev0"]), len(AN["ev1"]), len(AN["ev2"])), AN["ev2"] == AN["ev1"], (AN["ev1"], AN["ev2"]))
    sw = AN.get("sw_now") or {}
    page_kh = AN["page_amir"]["khol"]
    board_kh = b1["khol"]
    check("words D708 in the strings this kit writes: the board JSON as amir, the board page, the door replies, sw lines -- no forbidden word; every kholiye a door's verb (%d page hits, %d json hits)" % (len(page_kh), len(board_kh)),
          not b1["bad"] and not AN["page_amir"]["bad"] and not sw.get("lines_bad") and all(ok for ok, _ in page_kh) and all(ok for ok, _ in board_kh) and all(ok for ok, _ in (sw.get("lines_khol") or []))
          and not bad_hits(" ".join(str(x) for v in P.values() if isinstance(v, list) for x in v if x), exempt=("wapas",)), (page_kh, board_kh, sw))
    s6 = AN["steps"]["6"]
    check("step 6 as amir: 200, the duty's door marker 'Marg sudhar' present, the card's kholiye hits are doors (%s)" % [x for x in s6["khol"]], s6["code"] == 200 and s6["marker"] and all(ok for ok, _ in s6["khol"]), s6)
    eye = AN["eye"]
    bad_eye = [d for d in eye["duties"] if d["tile"] and not d["tile_seen"]] + [d for d in eye["duties"] if d.get("door_seen") is False] + [d for d in eye["duties"] if isinstance(d["due_n"], str)]
    cv = [d for d in eye["duties"] if d["id"] == "amir.count_vouchers"]
    check("staff-eye: amir's first /portal -> 302 to /finance/amir; the tile 'Amir ka kaam' on his home; with the walk's batch open amir.count_vouchers is due (%s) and its door shows 'Marg sudhar'; every due duty of amir on the v10 map shows its marker (%s)"
          % (cv[0]["due_n"] if cv else "?", ", ".join("%s %s" % (d["id"], d["due_n"]) for d in eye["duties"] if isinstance(d["due_n"], int) and d["due_n"] > 0)),
          eye["first"][0] == 302 and "Amir ka kaam" in eye["tiles"] and eye["duties"] and not bad_eye and eye["version"] == 10 and cv and cv[0]["due_n"] == 1 and cv[0].get("door_seen") is True, (bad_eye, cv))
    H = AN["hub"]
    check("the owner's hub step 7: 200, text == the one owner sentence (%r), the verdict lines carried; the page 200; the orthotic section and /finance/stockmatch 200; the statement 200" % H.get("text"),
          H["code"] == 200 and H.get("text") == sw.get("owner_en") and AN["hub_page"] == 200 and H.get("ortho_ok") is True and AN["sm_page"] == 200 and AN["sm_api"] == 200 and AN["statement_page"] == 200 and AN["statement_api"] == 200, H)
    check("Needs-you (sanjeevni_approvals) renders with each line dict(cls, target, text); the owner's stock line is 'Count #N: <owner_en>'",
          AN["needs_you"]["code"] == 200 and not AN["needs_you"]["bad_shape"] and any(x == "Count #%d: %s" % (AN["root"], sw.get("owner_en")) for x in AN["needs_you"]["stock"]), AN["needs_you"])
    check("the visit summary as the checker: 200, the same keys as the OLD file (%d), the step state literals kept" % len(AN["visit"]["keys"]), AN["visit"]["code"] == 200 and AN["visit"]["keys"] == AO["visit"]["keys"] and len(AN["visit"]["keys"]) >= 16
          and set(AN["visit"]["states"]) <= set(AO["visit"]["states"]) | {"done", "not needed", "open", "not yet"}, (AN["visit"], AO["visit"]["keys"]))
    check("amir_salts' step page renders (200)", AN["salts_page"] == 200, AN["salts_page"])
    print("   timing (reported, not gated): board as amir %d ms, as the owner %d ms (NEW); OLD %d / %d ms; amir_stage warm %d ms; the light builder %s ms" % (AN["ms_board_amir"], AN["ms_board_owner"], AO["ms_board_amir"], AO["ms_board_owner"], FN["ms_stage_warm"], FN.get("ms_light_fn")))
    return finish()


def finish():
    if FAILS:
        print("WALK_S528 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:260])
        return 1
    print("WALK_S528 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
