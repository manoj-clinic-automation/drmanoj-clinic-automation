#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s815.py FINANCE_DIR SPINE_DB FINANCE_DB DUTY_MAP_JSON -- kit S815's walk on COPIES (never the live database): Darpan's own Ask line and
the sale report asked for again, end to end. FINANCE_DIR holds the files under test. The copy is made in TMPDIR and removed at the end.
Last line 'WALK n/m'."""
import datetime as dt, json, os, shutil, sqlite3, sys, tempfile

FIN, SPINE, DB, DMAP = sys.argv[1:5]
sys.path.insert(0, FIN)
os.environ["SPINE_DB"] = SPINE
tmp = tempfile.mkdtemp(prefix="w815_")
db = os.path.join(tmp, "finance.db")
shutil.copy(DB, db)
ok = tot = 0


def check(name, cond):
    global ok, tot
    tot += 1
    ok += bool(cond)
    print("%s  %s" % ("PASS" if cond else "FAIL", name))


try:
    con = sqlite3.connect(db)
    for t in ("billwatch_act", "marg_watch_ask", "marg_watch_ask_row", "marg_watch_report"):   # ON THE COPY ONLY: every move open, no ask yet
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():
            con.execute("DELETE FROM %s" % t + (" WHERE fkey LIKE 'hand:%'" if t == "billwatch_act" else ""))
    con.execute("DELETE FROM setting WHERE key IN ('mwr.since', 'mwr.cluster', 'ask.notice', 'ask.notice_from')")
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_job'").fetchone():
        con.execute("DELETE FROM amir_job WHERE kind='ask'")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('owner_notice.on', 'off')")   # the tick below sends nothing
    con.commit()
    import marg_hand_change as H                                   # noqa: E402
    import marg_billwatch as BW                                    # noqa: E402
    H.refresh(con, SPINE, finance_db=db, force=True)
    BW.ensure(con)
    con.commit()
    check("ensure makes the report table and its two settings (cluster 3)", BW._rpt_table(con) and BW.rpt_cluster(con) == 3
          and BW.setting(con, "mwr.since", "") != "")
    V = BW.hand_view(con)
    rows = V["counted"]
    check("open moves to work with (%d)" % len(rows), len(rows) >= 6)
    # ================================================================== (a) Darpan's own page
    r1, r2, r3 = rows[0], rows[1], rows[2]
    k1, k2, k3 = ("hand:%d" % int(r["id"]) for r in (r1, r2, r3))
    okk, msg, code = BW.ask_send(con, "manoj", [k1], "darpan", True)
    check("asked Darpan on his page (%s)" % msg, okk and msg == "On Darpan's page.")
    a = con.execute("SELECT id, text_hi, staff_ref, codes FROM marg_watch_ask ORDER BY id DESC LIMIT 1").fetchone()
    check("the ask stands on his page (staff_ref darpan:card), no Amir job made", a[2] == "darpan:card"
          and not con.execute("SELECT COUNT(*) FROM amir_job WHERE kind='ask'").fetchone()[0])
    check("the text starts at the matter and ends 'Yahin jawab chuniye.' (no name, no ji)", a[1].startswith("Marg mein stock badla")
          and a[1].endswith("Yahin jawab chuniye.") and " ji" not in a[1] and "Darpan" not in a[1])
    D = BW.ask_for_darpan(con)
    check("his page reads it: one question, three answers", len(D) == 1 and [x["code"] for x in D[0]["answers"]] == ["fixed", "right", "unknown"])
    check("the same row cannot go on his page twice", BW.ask_send(con, "manoj", [k1], "darpan", True)[2] == 409)
    check("... nor onto Amir's card while it stands on Darpan's", BW.ask_send(con, "manoj", [k1], "amir", True)[2] == 409)
    check("the row's chip says Asked · Darpan", "Asked · Darpan" in BW.hand_html(con))
    import darpan_kal as DK                                        # noqa: E402
    check("the payload carries it for his (staff) login and for the owner", len(DK._s815_mw_ask(con, ("staff", None))) == 1
          and len(DK._s815_mw_ask(con, ("owner", None))) == 1)
    check("... and not for a cash recipient", DK._s815_mw_ask(con, ("recipient", "dr_bhawna")) == [])
    aid = D[0]["id"]
    check("an answer not offered on it is refused", BW.ask_answer_darpan(con, "darpan", aid, "supplier", "")[2] == 400)
    check("a made-up answer is refused", BW.ask_answer_darpan(con, "darpan", aid, "hello", "")[2] == 400)
    check("a made-up id is refused, nothing written", BW.ask_answer_darpan(con, "darpan", 999999, "fixed", "")[2] == 409)
    okk, msg, code = BW.ask_answer_darpan(con, "darpan", aid, "right", "shelf  par | sahi hai")
    check("his tap is taken (%s)" % msg, okk and code == 200)
    check("... once (a double tap answers once)", BW.ask_answer_darpan(con, "darpan", aid, "fixed", "")[2] == 409)
    st = BW.ask_state(con).get(k1) or {}
    check("the answer comes back to the row, his line cleaned", st.get("answered") and st.get("kind") == "right" and st.get("line") == "shelf par sahi hai"
          and st.get("by") == "darpan")
    check("it leaves his page", BW.ask_for_darpan(con) == [])
    h = BW.hand_html(con)
    check("the row says Answered · Darpan with his words", "Answered · Darpan" in h and "shelf par sahi hai" in h)
    BW.ask_set_notice(con, "manoj", True)
    BW.ask_send(con, "manoj", [k2], "darpan", True)
    aid2 = BW.ask_for_darpan(con)[0]["id"]
    BW.ask_answer_darpan(con, "darpan", aid2, "unknown", "")
    m = [x for x in BW.ask_messages(con, dt.datetime.now()) if x["key"] == "ask:%d" % aid2]
    check("his answer after the notice was turned on reaches the phone line, as Darpan's", len(m) == 1 and "Darpan answered" in m[0]["title"])
    check("his answer from before the switch is not told", not [x for x in BW.ask_messages(con, dt.datetime.now()) if x["key"] == "ask:%d" % aid])
    # he closes a row -> the question leaves Darpan's page, and after a reopen the row can be asked again (Darpan and Amir alike)
    BW.ask_send(con, "manoj", [k3], "darpan", True)
    okc = BW.hand_close(con, "manoj", int(r3["id"]), "ok", "")
    BW.hand_view(con)
    ref = con.execute("SELECT staff_ref FROM marg_watch_ask WHERE id=(SELECT MAX(ask_id) FROM marg_watch_ask_row WHERE row_key=?)", (k3,)).fetchone()[0]
    check("closing the row withdraws Darpan's question (%s)" % ref, okc[0] and ref == "darpan:withdrawn" and BW.ask_for_darpan(con) == [])
    BW.hand_reopen(con, "manoj", int(r3["id"]))
    check("after a reopen the withdrawn question is not shown as still asked", (BW.ask_state(con).get(k3) is None))
    check("... and the row can be asked again", BW.ask_send(con, "manoj", [k3], "darpan", True)[0])
    r4 = rows[3]
    k4 = "hand:%d" % int(r4["id"])
    BW.ask_send(con, "manoj", [k4], "amir", True)
    BW.hand_close(con, "manoj", int(r4["id"]), "ok", "")
    BW.hand_view(con)
    BW.hand_reopen(con, "manoj", int(r4["id"]))
    check("Amir alike: a withdrawn card question does not block a new one after a reopen", BW.ask_send(con, "manoj", [k4], "amir", True)[0])
    # the door on his page: only his (staff) login answers
    from flask import Flask                                        # noqa: E402
    app = Flask("w815")
    WHO = {"u": {"user": "darpan", "roles": ["maker"]}}

    def req(*roles, **kw):
        return WHO["u"], None

    def getdb():
        c = sqlite3.connect(db)
        c.row_factory = None
        return c
    DK.init(app, getdb, req)
    cl = app.test_client()
    aid3 = BW.ask_for_darpan(con)[0]["id"]
    WHO["u"] = {"user": "manoj", "roles": ["checker"]}
    r = cl.post("/finance/darpan/kal/api/mw-ask-answer", json={"id": aid3, "answer": "fixed"})
    check("the owner's login cannot answer for Darpan (403)", r.status_code == 403)
    WHO["u"] = {"user": "darpan", "roles": ["maker"]}
    r = cl.post("/finance/darpan/kal/api/mw-ask-answer", json={"id": aid3, "answer": "fixed", "note": "theek kiya"})
    check("his login answers through the door (200)", r.status_code == 200 and r.get_json().get("ok"))
    r = cl.post("/finance/darpan/kal/api/mw-ask-answer", json={"id": aid3, "answer": "fixed"})
    check("... once (409)", r.status_code == 409)
    page = open(os.path.join(FIN, "darpan_kal.html"), encoding="utf-8").read()
    check("his page draws the question first", "el(\"body\").innerHTML=mwAskSec(j.mw_ask)+h;" in page and "Doctor sahab ka sawaal" in page)
    # the duty map row
    dm = json.load(open(DMAP, encoding="utf-8"))
    du = next((d for d in dm["duties"] if d.get("id") == "darpan.mw_ask"), None)
    check("the duty map carries darpan.mw_ask (door Kal ka hisaab, marker on the page)", du is not None and du["door"] == "/finance/darpan/kal"
          and du["door_marker"] in page)
    BW.ask_send(con, "manoj", [ "hand:%d" % int(rows[4]["id"])], "darpan", True)
    n = con.execute(du["due_sql"]).fetchone()
    check("its due_sql counts the questions still on his page (%s)" % (n,), n[0] == len(BW.ask_for_darpan(con)) and n[0] >= 1)
    # ================================================================== (b) reports asked for again
    check("history never asks by itself (since = the install)", BW.rpt_auto(con) == 0)
    con.execute("UPDATE setting SET value='2026-01-01 00:00:00' WHERE key='mwr.since'")
    con.commit()
    made = BW.rpt_auto(con)
    asks = con.execute("SELECT ref, day_from, day_to, why, asked_by FROM marg_watch_report ORDER BY id").fetchall()
    c25 = next((x for x in asks if x[0] == "cluster:2026-10-25"), None)
    check("a closing with 3 or more rises asks by itself (made %d): %s" % (made, c25[:3] if c25 else None), c25 is not None and c25[4] == "auto")
    check("... for the days before that closing (22 to 24 Oct)", c25 is not None and c25[1] == "2026-10-22" and c25[2] == "2026-10-24")
    check("... and says why, item by item", c25 is not None and "NORTIMER TAB +90" in c25[3])
    check("again: nothing new", BW.rpt_auto(con) == 0)
    clos = {}
    for r in BW.hand_view(con)["counted"]:
        if int(r.get("shift") or 0) > 0:
            clos.setdefault(r["day_to"], []).append(r)
    check("no closing with fewer rises than the figure asked", all(len(clos.get(x[0][8:], [])) >= 3 for x in asks if x[0].startswith("cluster:")))
    check("his figure: a word is refused", BW.rpt_set_cluster(con, "manoj", "abc")[2] == 400)
    check("his figure: 1 = never by itself", BW.rpt_set_cluster(con, "manoj", "1")[0] and BW.rpt_auto(con) == 0)
    BW.rpt_set_cluster(con, "manoj", "3")
    O = BW.rpt_open(con)
    o25 = next(x for x in O if x["day_from"] == "2026-10-22")
    check("Shavez's list: open, not yet come", not o25["arrived"] and o25["missing"])
    later = (BW.now_ist().replace(tzinfo=None) + dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S+05:30")   # IST, as the door stamps
    for i, day in enumerate(o25["missing"][:-1]):
        con.execute("INSERT INTO mi_file (md5, type, variant, date_from, date_to, verdict, received_at) VALUES (?,?,?,?,?,?,?)",
                    ("w815%028d" % i, "SALE_BILLWISE", "DETAIL", day, day, "VERIFIED", later))
    con.commit()
    o25 = next(x for x in BW.rpt_open(con) if x["day_from"] == "2026-10-22")
    check("one day still missing: not come (%s)" % o25["missing"], not o25["arrived"] and len(o25["missing"]) == 1)
    con.execute("INSERT INTO mi_file (md5, type, variant, date_from, date_to, verdict, received_at) VALUES (?,?,?,?,?,?,?)",
                ("w815r%027d" % 9, "SALE_BILLWISE", "DETAIL", o25["missing"][0], o25["missing"][0], "REFUSED", later))
    con.commit()
    check("a REFUSED file does not count", not next(x for x in BW.rpt_open(con) if x["day_from"] == "2026-10-22")["arrived"])
    con.execute("INSERT INTO mi_file (md5, type, variant, date_from, date_to, verdict, received_at) VALUES (?,?,?,?,?,?,?)",
                ("w815z%027d" % 9, "SALE_BILLWISE", "DETAIL", o25["missing"][0], o25["missing"][0], "VERIFIED", "2026-10-01T09:00:00+05:30"))
    con.commit()
    check("a file received BEFORE the ask does not count", not next(x for x in BW.rpt_open(con) if x["day_from"] == "2026-10-22")["arrived"])
    con.execute("INSERT INTO mi_file (md5, type, variant, date_from, date_to, verdict, received_at) VALUES (?,?,?,?,?,?,?)",
                ("w815y%027d" % 9, "SALE_BILLWISE", "DETAIL", "2026-10-20", "2026-10-26", "VERIFIED", later))
    con.commit()
    check("a range file covering the rest: come", next(x for x in BW.rpt_open(con) if x["day_from"] == "2026-10-22")["arrived"])
    # Shavez's page (read only) before the Marg watch closes it
    import reports_tile as RT                                       # noqa: E402
    ro = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    ro.row_factory = sqlite3.Row                                   # as the page opens it
    s = RT.status(ro)
    check("Shavez's status carries the asks, read only", any(x["day_from"] == "2026-10-22" and x["arrived"] for x in s.get("asked", [])))
    html = RT.render(s)
    check("his page shows the card above the steps card, with the dates and a tick", html.count("id=s815asked") == 1
          and html.index("id=s815asked") < html.index("id=s714flows") and "22-10-2026 se 24-10-2026" in html and "aa gayi, sahi hai" in html)
    import importlib.util as IU                                     # noqa: E402
    spec = IU.spec_from_file_location("rt_base", os.environ.get("BASE_RT", ""))
    if spec and os.environ.get("BASE_RT"):
        RB = IU.module_from_spec(spec)
        spec.loader.exec_module(RB)
        sb = RB.status(ro)
        check("the day's counts and the owner's line are unchanged by the card", all(sb[k] == s[k] for k in
              ("arrived", "certified", "pending", "bad", "refused", "total", "all_in", "line")))
    ro.close()
    # the five-minute tick closes it (the phone off: nothing sent)
    import owner_notice as ON                                       # noqa: E402
    res = ON._tick(con, None)
    c = con.execute("SELECT closed_at, closed_how FROM marg_watch_report WHERE ref='cluster:2026-10-25'").fetchone()
    check("the tick closes the ask whose files have come (%s)" % (res.get("off") or res,), c[0] and str(c[1]).startswith("arrived"))
    ro = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    ro.row_factory = sqlite3.Row
    check("... and it leaves Shavez's page", not any(x["day_from"] == "2026-10-22" for x in RT.status(ro).get("asked", [])))
    ro.close()
    # by him, from a row
    rr = next(r for r in BW.hand_view(con)["counted"] if not BW.rpt_row_map(con).get("hand:%d" % int(r["id"])) and not r.get("ask") and (str(r["day_to"]) < "2026-10-20" or str(r["day_from"]) > "2026-10-26"))   # outside the range file above (S448: rows after it carry the walk's own Asks)
    okk, msg, code = BW.rpt_ask_row(con, "manoj", int(rr["id"]))
    check("he asks from a row (%s)" % msg, okk and code == 200)
    check("... once", BW.rpt_ask_row(con, "manoj", int(rr["id"]))[2] == 409)
    check("a made-up row is refused", BW.rpt_ask_row(con, "manoj", 999999)[2] == 409)
    hh = BW.hand_html(con)
    check("the row says 'Report asked' and names the days", "Report asked" in hh and "is asked for — on Shavez" in hh)
    check("the strip lists it, by you", "Reports asked for" in hh and ">you<" in hh)
    p = BW.page_html(con)
    check("the page renders with the strip, the row buttons and both new script functions", "Reports asked for" in p and "mwRAsk" in p and "mwRCluster" in p
          and "Put on Darpan" in p)
    # ================================================================== S448: the cold review's should-fixes
    con.execute("DELETE FROM marg_watch_report WHERE ref='cluster:2026-10-25'")
    con.execute("INSERT INTO marg_watch_report (ref, kind, day_from, day_to, asked_by, asked_at, closed_at, closed_how) VALUES "
                "('row:walk', 'SALE', '2026-10-22', '2026-10-24', 'manoj', '2026-11-13 09:00:00', '2026-11-13 09:30:00', 'arrived')")
    con.commit()
    check("S1: days already asked (and closed) are never asked again by the cluster rule", BW.rpt_auto(con) == 0
          and not con.execute("SELECT 1 FROM marg_watch_report WHERE ref='cluster:2026-10-25'").fetchone())
    con.execute("DELETE FROM marg_watch_report WHERE ref='row:walk'")
    con.commit()
    check("S1 control: without that ask the cluster asks again", BW.rpt_auto(con) == 1)
    free = next(r for r in BW.hand_view(con)["counted"] if not r.get("ask"))
    okk, msg, code = BW.ask_send(con, "manoj", ["hand:%d" % int(free["id"])], "darpan", True)
    qid = BW.ask_for_darpan(con)[-1]["id"] if okk else None
    lk = sqlite3.connect(db, timeout=1)
    lk.execute("BEGIN IMMEDIATE")
    busy = sqlite3.connect(db, timeout=0.2)
    okb, msgb, codeb = BW.ask_answer_darpan(busy, "darpan", qid, "right", "")
    lk.rollback(); lk.close(); busy.close()
    check("S3: a busy database answers 503 in Hindi, nothing written (%s)" % msgb, codeb == 503 and "vyast" in msgb
          and BW.ask_for_darpan(con) and BW.ask_for_darpan(con)[-1]["id"] == qid)
    check("S3: a made-up answer says so in Hindi, not a code", "nahin hai" in BW.ask_answer_darpan(con, "darpan", qid, "hello", "")[1])
    con.execute("UPDATE marg_watch_ask SET staff_ref='darpan:withdrawn' WHERE id=?", (qid,))
    con.commit()
    m2 = BW.ask_answer_darpan(con, "darpan", qid, "right", "")
    check("S3: a withdrawn question says so, nothing to do (%s)" % m2[1], m2[2] == 409 and "hata diya" in m2[1])
    ro2 = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    ro2.row_factory = sqlite3.Row
    BW.rpt_ask_row(con, "manoj", int(free["id"]))                  # an open ask, so the card stands on his page
    html2 = RT.render(RT.status(ro2))
    ro2.close()
    check("S4: Shavez's asked card stands above the day's done / count line", "id=s815asked" not in html2 or all(
          html2.index("id=s815asked") < html2.index(x) for x in ("card done", "class=foot", "big wait") if x in html2))
except Exception as e:                                             # noqa: BLE001
    import traceback
    traceback.print_exc()
    check("the walk ran to its end (%s)" % e.__class__.__name__, False)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (ok, tot))
sys.exit(0 if ok == tot else 1)
