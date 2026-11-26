#!/usr/bin/env python3
"""walk_s955.py -- S955_RECEPTION_CONSOLE: the walk of the reception mobile on the staff Call Console, on S948's MADE-UP
console.db + inbox.db (every number 500000xxxx; 'today' 24-Nov 11:30) with four reception-mobile calls added. Nothing here
reads a real store or sends anything; every path is a temp file.

  python walk_s955.py walk <code dir> <tile_grants FROM> <tile_grants TO>
      every check; exit 0 only when all pass (<code dir> holds calls_staff.py, calls_console.py, callback_clock.py,
      ring_outcome.py, ring_common.py; walk_s948.py sits beside this file)
"""
import datetime as _dt
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FAILS = []
N = [0]


def ok(cond, what):
    N[0] += 1
    print(("  PASS  " if cond else "  FAIL  ") + what)
    if not cond:
        FAILS.append(what)


def add_reception_calls(W, con_p):
    """R1 08:02 answered in (only Shivani punched: credited to her) . R2 10:15 answered out with a verdict (both on duty: kept on
    the Reception mobile card) . R3 10:25 unanswered out (not 'handled') . R4 09:50 answered in by Alisha (not the reception)."""
    c = sqlite3.connect(con_p)
    rows = [(2101, "In", 1, "08:02", 5, 70, "Reception Mobile", ""),
            (2102, "Out", 1, "10:15", 6, 130, "Reception Mobile", "coming"),
            (2103, "Out", 0, "10:25", 12, 14, "Reception Mobile", ""),
            (2104, "In", 1, "09:50", 4, 40, "Alisha Test", "")]
    for n, dr, a, hm, ring, dur, agent, ai in rows:
        jk = "%s_%d" % (W.ph(n), W.unix(hm))
        end = (_dt.datetime.strptime(W.TODAY + " " + hm, "%Y-%m-%d %H:%M") + _dt.timedelta(seconds=dur)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO calls (status,direction,answered,total_duration,customer_talk_duration,customer_ring_duration,"
                  "recording_filename,ended_at_ist,phone10,join_key,client_ref_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  ("bridged" if a else "missed", dr, a, str(dur), str(max(0, dur - ring)) if a else "0", str(ring), "",
                   end, W.ph(n), jk, ""))
        c.execute("INSERT INTO call_agent VALUES (?,?)", (jk, agent))
        if ai:
            c.execute("INSERT INTO verdicts (join_key,agent,patient_name,clinic_id,claimed_outcome,ai_outcome,verdict) "
                      "VALUES (?,?,?,?,?,?,?)", (jk, agent, "", "", "", ai, "No claim logged"))
            c.execute("INSERT INTO recordings VALUES (?,?,?,?)", ("r.mp3", jk, "https://example.invalid/r", ""))
    c.commit()
    c.close()


EMPTY = {"tabs": {"mine": [], "due": [], "missed": [], "wa": [], "again": [], "eve": []}}


def J(resp):
    """A response's JSON, or an empty shape (the control: the FROM code refuses reception) -- the walk goes red, never crashes."""
    try:
        j = resp.get_json()
    except Exception:
        j = None
    return j if isinstance(j, dict) and "tabs" in j else dict(EMPTY, status=resp.status_code)


def phones(lst):
    return [r["phone"] for r in lst]


def do_walk(code, tg_from, tg_to):
    import tempfile
    import walk_s948 as W
    W.CODE = code
    root = tempfile.mkdtemp(prefix="s955w_")
    con_p, inbox_p = W.make_fixture(root)
    add_reception_calls(W, con_p)
    app, cc, pm, _ = W.build_app(root, con_p, inbox_p, W.NOW)
    import calls_staff as CS
    isr = getattr(CS, "is_reception", lambda k: None)
    base = cc._CFG
    over = {}
    cc._CFG = lambda k, d="": over[k] if k in over else base(k, d)
    called = []
    cc.ivr_call = lambda p, login, **k: (called.append((p, login)) or (True, "Your phone is ringing", 200))
    cl = app.test_client()
    H = W.H

    print("[1] the gate -- the reception mobile's login is admitted")
    ok(getattr(CS, "KIT_S955", "") == "S955_RECEPTION_CONSOLE" and CS.VERSION == "S951 1.1", "kit S955 marked; VERSION stays 'S951 1.1' (S951's walk pins it)")
    ok(CS.allowed_keys() == ["shivani", "alisha", "shavez", "reception"], "allowed_keys: the phone staff, Shavez, then reception: %s" % CS.allowed_keys())
    r = cl.get("/portal/console/staff", headers=H("reception"))
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and "Reception" in t, "reception -> 200, its own page")
    ok(cl.get("/portal/console/staff/api/lists", headers=H("reception")).status_code == 200, "reception's data route -> 200")
    ok(cl.get("/portal/console/staff", headers=H("Reception")).status_code == 200, "the login in capitals reads the same key")
    ok(cl.get("/portal/console/staff", headers=H("bhawna")).status_code == 403, "a login not on the list still -> 403")
    ok(cl.get("/portal/console/staff", headers=H("reception2")).status_code == 403, "a near name (reception2) -> 403")
    r = cl.get("/portal/console/staff", headers=H("manoj", "doctor"))
    ok(r.status_code == 200 and "?as=reception" in r.get_data(as_text=True), "the doctor's picker offers reception")
    r = cl.get("/portal/console/staff?as=reception", headers=H("manoj", "doctor"))
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and "Wrong?" not in t, "the doctor ?as=reception -> its page, no Wrong?")
    for v in ("0", "off", "False", "no", 0, False):
        over["PORTAL_STAFF_CONSOLE_RECEPTION"] = v
        ok(cl.get("/portal/console/staff", headers=H("reception")).status_code == 403 and "reception" not in CS.allowed_keys(),
           "PORTAL_STAFF_CONSOLE_RECEPTION=%r -> reception 403, not on the list" % (v,))
    over["PORTAL_STAFF_CONSOLE_RECEPTION"] = "1"
    ok(cl.get("/portal/console/staff", headers=H("reception")).status_code == 200, "=1 -> admitted again")
    over.pop("PORTAL_STAFF_CONSOLE_RECEPTION")
    over["PORTAL_RECEPTION_AGENT"] = "Frontdesk Phone"
    ok(CS.allowed_keys()[-1] == "frontdesk" and cl.get("/portal/console/staff", headers=H("reception")).status_code == 403
       and cl.get("/portal/console/staff", headers=H("frontdesk")).status_code == 200,
       "the reception agent renamed (frontdesk) -> that login is admitted, 'reception' no longer")
    over.pop("PORTAL_RECEPTION_AGENT")
    over["PORTAL_STAFF_CONSOLE_EXTRA"] = "shavez,reception"
    ok(CS.allowed_keys().count("reception") == 1, "reception named in EXTRA too -> listed once")
    over["PORTAL_STAFF_CONSOLE_RECEPTION"] = "0"
    ok("reception" not in CS.allowed_keys() and "shavez" in CS.allowed_keys(), "named in EXTRA but the switch 0 -> off (the switch wins)")
    over.pop("PORTAL_STAFF_CONSOLE_RECEPTION")
    over["PORTAL_STAFF_CONSOLE_RECEPTION"] = ""
    ok("reception" in CS.allowed_keys(), "the switch empty -> the default (admitted)")
    over.pop("PORTAL_STAFF_CONSOLE_RECEPTION")
    over.pop("PORTAL_STAFF_CONSOLE_EXTRA")
    over["PORTAL_PHONE_STAFF"] = "shivani,alisha,reception"
    ok(CS.allowed_keys().count("reception") == 1 and isr("reception") is False,
       "reception made phone staff -> listed once, read as a person's card (calls_console's own rule)")
    over.pop("PORTAL_PHONE_STAFF")
    ok(isr("shivani") is False and isr("") is False and isr("reception") is True, "is_reception: only the reception key")

    print("[2] Handled today -- the reception mobile's own calls, whoever was credited")
    cc._CARD_CACHE.clear()
    d = J(cl.get("/portal/console/staff/api/lists", headers=H("reception")))
    M = d["tabs"]["mine"]
    ok(d.get("reception") is True and d.get("card_ok"), "the lists say reception, its calls were read")
    ok(phones(M) == [W.ph(2102), W.ph(2101)], "Handled = R2 10:15 then R1 08:02 (newest first): %s" % [p[-4:] for p in phones(M)])
    ok(W.ph(2103) not in phones(M) and W.ph(2104) not in phones(M), "not the unanswered try (R3), not Alisha's own call (R4)")
    r2 = next((x for x in M if x["phone"] == W.ph(2102)), {})
    ok(r2.get("verdict") == "Coming" and r2.get("jk") == "" and not r2.get("can_dispute"),
       "R2: the Call verdict; no recording, no Wrong? (both belong to a person's card)")
    ok(all(x["jk"] == "" for x in M), "no recording on any reception row (the recording route serves a person's own calls)")
    ok(all(not x["can_dispute"] for x in M), "no Wrong? on any reception row")
    ok("outgoing" in r2.get("sub", "") and "10:15" in r2.get("sub", ""), "R2's line: time and outgoing")
    ds = J(cl.get("/portal/console/staff/api/lists", headers=H("shivani")))
    ok(W.ph(2101) in phones(ds["tabs"]["mine"]) and W.ph(2102) not in phones(ds["tabs"]["mine"]),
       "Shivani's own Handled keeps R1 (credited to her, on duty alone at 08:02), not R2 -- unchanged")
    ok("reception" not in ds, "Shivani's lists carry no reception mark")
    da = J(cl.get("/portal/console/staff/api/lists", headers=H("alisha")))
    ok(W.ph(2104) in phones(da["tabs"]["mine"]) and W.ph(2102) not in phones(da["tabs"]["mine"]), "Alisha's own Handled: R4, not R2")
    ok(d["tabs"]["due"] == ds["tabs"]["due"] and d["tabs"]["missed"] == ds["tabs"]["missed"] and d["tabs"]["wa"] == ds["tabs"]["wa"],
       "the shared tabs (Follow-ups due, Incoming missed, WhatsApp) are the same lists Shivani sees")
    t = cl.get("/portal/console/staff", headers=H("reception")).get_data(as_text=True)
    ok("Calls on the reception mobile" in t and "Only your own calls" not in t, "the tab's foot says the reception mobile")
    ok(">Recording<" not in t, "no Recording button on its page")
    ok("Wrong?" not in t.split('id="p-mine"')[-1] if 'id="p-mine"' in t else "Wrong?" not in t, "no Wrong? button on its page")
    ts = cl.get("/portal/console/staff", headers=H("shivani")).get_data(as_text=True)
    ok("Only your own calls" in ts and "reception mobile ·" not in ts, "Shivani's page keeps her own words")

    print("[3] a fault never takes the page down")
    real = cc._safe_cards
    cc._safe_cards = lambda *a, **k: None
    d2 = J(cl.get("/portal/console/staff/api/lists", headers=H("reception")))
    ok(d2.get("status") is None and d2.get("card_ok") is False and d2["tabs"]["mine"] == [], "cards unreadable -> card_ok false, empty, page 200")
    t2 = cl.get("/portal/console/staff", headers=H("reception")).get_data(as_text=True)
    ok("could not be read just now" in t2, "... and the tab says so")
    cc._safe_cards = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    d3 = cl.get("/portal/console/staff/api/lists", headers=H("reception"))
    ok(d3.status_code == 200 and J(d3).get("card_ok") is False, "an exception in the cards -> card_ok false, still 200")
    cc._safe_cards = real
    rb = getattr(CS, "reception_calls", None)
    CS.reception_calls = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    d4 = cl.get("/portal/console/staff/api/lists", headers=H("reception"))
    ok(d4.status_code == 200 and J(d4).get("card_ok") is False, "reception_calls itself failing -> card_ok false, still 200")
    if rb is None:
        del CS.reception_calls
    else:
        CS.reception_calls = rb

    print("[4] what reception can do")
    cc._CARD_CACHE.clear()
    rr = cl.post("/portal/console/staff/api/dispute", headers=H("reception", post=True),
                 json={"ref": r2.get("ref", "x"), "text": "wrong"})
    ok(rr.status_code in (403, 409) and not (rr.get_json(silent=True) or {}).get("ok"), "a dispute from reception is refused (%d): a dispute belongs to a person" % rr.status_code)
    cl.get("/portal/console/staff/api/lists", headers=H("reception"))
    rc = cl.post("/portal/console/staff/api/call", headers=H("reception", post=True), json={"phone10": W.ph(1)})
    ok(rc.status_code == 200 and called and called[-1] == (W.ph(1), "reception"), "click-to-call from reception dials with its own login")
    over["PORTAL_STAFF_CONSOLE_RECEPTION"] = "0"
    rc = cl.post("/portal/console/staff/api/call", headers=H("reception", post=True), json={"phone10": W.ph(1)})
    ok(rc.status_code == 403, "with the setting 0 its call route is refused too")
    over.pop("PORTAL_STAFF_CONSOLE_RECEPTION")

    print("[5] the tile grant")
    a, b = json.load(open(tg_from, encoding="utf-8")), json.load(open(tg_to, encoding="utf-8"))
    ok(a["version"] == 48 and b["version"] == 49, "tile_grants v48 -> v49")
    ex = b["users"]["reception"]["extra"]
    ok(ex[:2] == ["Call Tracker", "My Call Console"] and ex.count("My Call Console") == 1, "reception: 'My Call Console' right after 'Call Tracker'")
    ok(ex[2:] == a["users"]["reception"]["extra"][1:] and b["users"]["reception"].keys() == a["users"]["reception"].keys(),
       "reception's other grants unchanged")
    ok({k: v for k, v in a["users"].items() if k != "reception"} == {k: v for k, v in b["users"].items() if k != "reception"}
       and a["defaults"] == b["defaults"], "every other login and the defaults unchanged")
    ok(b["_note"].startswith(a["_note"]) and "S955 v49" in b["_note"], "the note keeps its history and adds v49")

    print("[6] the clock's taps for reception now open the new page")
    import callback_clock as CB
    CB.PORTAL_DIR = code
    adm = CB.admitted()
    land = CB.landing(adm, "/portal/console/staff?tab=missed")
    ok(adm is not None and land("reception") == "/portal/console/staff?tab=missed", "reception's tap -> /portal/console/staff?tab=missed")
    ok(land("shivani") == "/portal/console/staff?tab=missed" and land("bhawna") == CB.OLD_URL, "Shivani the new page; a login not admitted keeps the old")
    over["PORTAL_STAFF_CONSOLE_RECEPTION"] = "0"
    adm0 = CB.admitted()
    ok(adm0 is not None and CB.landing(adm0, "/x")("reception") == CB.OLD_URL, "setting 0 -> reception's tap keeps the old landing")
    over.pop("PORTAL_STAFF_CONSOLE_RECEPTION")
    print("\n%d checks, %d failed" % (N[0], len(FAILS)))
    print("ALL PASS" if not FAILS else "SOME FAILED")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "walk":
        sys.exit(__doc__)
    CODE = os.path.abspath(sys.argv[2])
    os.environ["RING_PORTAL_DIR"] = CODE
    sys.path.insert(0, CODE)
    sys.exit(do_walk(CODE, sys.argv[3], sys.argv[4]))
