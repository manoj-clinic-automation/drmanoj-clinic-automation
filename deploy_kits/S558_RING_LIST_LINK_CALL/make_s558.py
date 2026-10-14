#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s558.py -- S558_RING_LIST_LINK_CALL: the two edited programs rebuilt from the pinned live bytes (BUILD_NORM_v1).

    python3 -B make_s558.py <dir with the live ring_outcome.py and ring_common.py> <out dir>     build, check in memory, write
    python3 -B make_s558.py --check <live dir> <kit dir>    rebuild in memory and compare with the kit's files; writes nothing
    python3 -B make_s558.py --pins                          the FROM and TO md5 of each file, one line each

Exact counted edits: refuses when an input is not at its FROM pin, or an anchor is not found exactly the counted number of
times. Every byte of the result is the live file plus the edits below. The result must compile, and must be at its TO pin.
"""
import hashlib
import os
import sys

FROM = {"ring_outcome.py": "7cb60aad2df80f87fdc4a674ebe7ee45",
        "ring_common.py": "4344b59277d94b2d11d8d7cc23328677"}
TO = {"ring_outcome.py": "25a169bfe280e16b4b39585d827cc36e",
      "ring_common.py": "ce428b2c52582d4a30d460612a6da968"}

# ============================================================================================ ring_common.py
RC_HEAD_OLD = ("# (finance_patient_match.fingerprint; salt at /root/finance/patient_fp.env) -- finance.db holds no\n"
               "# raw mobile (S279 finding: patient_ref.mobile is empty on the VPS; mobile_fp is filled).\n")
RC_HEAD_NEW = RC_HEAD_OLD + (
    "#\n"
    "# S558_RING_LIST_LINK_CALL (14-Oct-2026, D726 (2) -- the owner: \"the second number is remembered for future calls\"):\n"
    "# lookup_caller also reads the after-call list's links (ring_outcomes.db, table appt_link, READ-ONLY, its own path\n"
    "# constant RING_STORE). A patient a person linked to this 10-digit number ('Haan, yahi hai') is added once, with\n"
    "# \"linked\": True -- so the next call from that number shows the patient and offers the known list. Only while the\n"
    "# owner's switch link_on is on; an undone link is not read; any error is ignored. Nothing else in this file changed.\n")

RC_CONST_OLD = 'FINANCE_DIR = os.environ.get("FINANCE_DIR", "/root/finance")\n'
RC_CONST_NEW = RC_CONST_OLD + (
    'RING_STORE = os.environ.get("RING_OUTCOME_DB", os.path.join(PORTAL_DIR, "ring_outcomes.db"))   # S558: the links, read-only\n')

RC_LOOKUP_OLD = '''def lookup_caller(phone, db_path=None):
    """Everything the pop-up says about a number: full number (owner ruling 21-Sep-2026), the patients on it
    (name, clinic id, last visit, visit count, whether a procedure), newest first. Read-only; never raises."""
    m10 = mobile10(phone)
    out = {"mobile": m10 or str(phone or ""), "patients": [], "fp_ok": False}
    if not m10:
        return out
    fp = _fp(m10)
    if not fp:
        return out
    out["fp_ok"] = True
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (db_path or FINANCE_DB), uri=True, timeout=3)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT clinic_id, name, patient_uid, last_seen, first_seen FROM patient_ref "
            "WHERE mobile_fp=? AND (merged_into IS NULL OR merged_into='') "
            "ORDER BY COALESCE(last_seen,'') DESC, id DESC LIMIT 6", (fp,)).fetchall()
        for r in rows:
'''
RC_LOOKUP_NEW = '''def _linked_ids(m10, store=None):
    """S558 (D726 (2)): the clinic IDs a person on the after-call list linked to this 10-digit number ('Haan, yahi hai'),
    newest first. ring_outcomes.db opened READ-ONLY; only while the owner's switch link_on is on; an undone link is
    not read; any error (no store, no table yet) -> none."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (store or RING_STORE), uri=True, timeout=3)
    except Exception:
        return []
    try:
        on = con.execute("SELECT v FROM kv WHERE k='link_on'").fetchone()
        if not on or str(on[0]) != "1":
            return []
        out = []
        for (cid,) in con.execute("SELECT clinic_id FROM appt_link WHERE mobile=? AND COALESCE(undone_at,'')='' "
                                  "ORDER BY linked_at DESC, id DESC", (m10,)):
            cid = str(cid or "").strip()
            if cid and cid not in out:
                out.append(cid)
        return out
    except Exception:
        return []
    finally:
        con.close()


def lookup_caller(phone, db_path=None, store=None):
    """Everything the pop-up says about a number: full number (owner ruling 21-Sep-2026), the patients on it
    (name, clinic id, last visit, visit count, whether a procedure), newest first. Read-only; never raises.
    S558: then each patient linked to this number on the after-call list, once, with "linked": True (by the 10 digits,
    so a number whose fingerprint cannot be made still reads its links)."""
    m10 = mobile10(phone)
    out = {"mobile": m10 or str(phone or ""), "patients": [], "fp_ok": False}
    if not m10:
        return out
    fp = _fp(m10)
    links = _linked_ids(m10, store)                              # S558
    if not fp and not links:
        return out
    out["fp_ok"] = bool(fp)
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (db_path or FINANCE_DB), uri=True, timeout=3)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT clinic_id, name, patient_uid, last_seen, first_seen FROM patient_ref "
            "WHERE mobile_fp=? AND (merged_into IS NULL OR merged_into='') "
            "ORDER BY COALESCE(last_seen,'') DESC, id DESC LIMIT 6", (fp,)).fetchall() if fp else []
        for r in rows:
'''
RC_TAIL_OLD = '''                "procedure": bool(v and str(v["had_procedure"] or "").strip().lower() in ("1", "y", "yes", "true", "p"))})
        con.close()
    except Exception:
        pass
    return out
'''
RC_TAIL_NEW = '''                "procedure": bool(v and str(v["had_procedure"] or "").strip().lower() in ("1", "y", "yes", "true", "p"))})
        for cid in links:                                        # S558: linked on the after-call list ('Haan, yahi hai')
            if any(p["clinic_id"] == cid for p in out["patients"]):
                continue
            r = con.execute(
                "SELECT clinic_id, name, patient_uid, last_seen FROM patient_ref WHERE clinic_id=? "
                "ORDER BY (merged_into IS NULL OR merged_into='') DESC, id DESC LIMIT 1", (cid,)).fetchone()
            uid = (r["patient_uid"] if r else "") or ""
            v = con.execute(
                "SELECT visit_date, had_procedure, COUNT(*) OVER () n FROM patient_visit "
                "WHERE (patient_uid=? AND ?<>'') OR (clinic_id=? AND ?<>'') "
                "ORDER BY visit_date DESC LIMIT 1", (uid, uid, cid, cid)).fetchone()
            out["patients"].append({
                "name": ((r["name"] if r else "") or "").strip(), "clinic_id": cid,
                "last_visit": (v["visit_date"] if v else ((r["last_seen"] if r else "") or ""))[:10],
                "visits": int(v["n"]) if v else 0,
                "procedure": bool(v and str(v["had_procedure"] or "").strip().lower() in ("1", "y", "yes", "true", "p")),
                "linked": True})
        con.close()
    except Exception:
        pass
    return out
'''
RC_EDITS = [(RC_HEAD_OLD, RC_HEAD_NEW, 1), (RC_CONST_OLD, RC_CONST_NEW, 1), (RC_LOOKUP_OLD, RC_LOOKUP_NEW, 1),
            (RC_TAIL_OLD, RC_TAIL_NEW, 1)]

# ============================================================================================ ring_outcome.py
RO_HEAD_OLD = "# It also mends F-797 (a name with the letters S-I-D was broken on the tap's page) -- see _page().\n"
RO_HEAD_NEW = RO_HEAD_OLD + (
    "#\n"
    "# S558_RING_LIST_LINK_CALL (session 317, 14-Oct-2026) -- D726, F-896. The owner, 14-Oct: \"the patients, they call from a\n"
    "# different number. The new ones. And then they register themselves with a different number ... Secondly, there should be\n"
    "# a click to call link to IVR number as the callback tracker does. For the no shows\"; then \"1 any staff . 2 yes\".\n"
    "#   link       on a new number's line (Nahi aaye / Aane baaki): the fold 'Shayad yeh aaye?' -- the new patients whose first\n"
    "#              visit falls in the line's window, and a search -- and 'Haan, yahi hai'. The link (table appt_link) supplies\n"
    "#              the visit; THE RULE (appt_state) is not changed. 'Galat link -- hatao' undoes it (never deletes).\n"
    "#   remember   ring_common.lookup_caller reads the links, so the next call from that number shows the patient.\n"
    "#   IVR call   'IVR se call karein' on each Nahi aaye line: call_api.py rings the staff member's own phone, then joins\n"
    "#              the patient. The key is read fresh from /root/wa/.env and never reaches a page or a log.\n"
    "#   switches   kv link_on / call_on, installed OFF; the owner turns them on in his box. Off = nothing renders, acts refused.\n"
    "# Not changed: THE RULE, the tap, the mirror into the Google tracker (a link is not mirrored), the sweeper, WhatsApp.\n")

RO_INIT_OLD = '''    CREATE INDEX IF NOT EXISTS ix_appt_event_outcome ON appt_event(outcome_id);
    """)
'''
RO_INIT_NEW = '''    CREATE INDEX IF NOT EXISTS ix_appt_event_outcome ON appt_event(outcome_id);
    CREATE TABLE IF NOT EXISTS appt_link (
      id INTEGER PRIMARY KEY AUTOINCREMENT, outcome_id INTEGER NOT NULL UNIQUE, clinic_id TEXT NOT NULL, mobile TEXT,
      linked_by TEXT, linked_name TEXT, linked_at TEXT, undone_by TEXT, undone_at TEXT);
    CREATE INDEX IF NOT EXISTS ix_appt_link_mobile ON appt_link(mobile);
    """)
'''

RO_IDS_OLD = '''            if c and c not in ids:
                ids.append(c)
    except Exception:
        pass
    return ids
'''
RO_IDS_NEW = '''            if c and c not in ids:
                ids.append(c)
    except Exception:
        pass
    c = str((row.get("s558_link") or {}).get("clinic_id") or "").strip()      # S558: a live link is an ID on the call
    if c and c not in ids:
        ids.append(c)
    return ids
'''

RO_OUT_OLD = '''           "store_ok": True, "visits_ok": True, "visits_through": None, "noshow": [], "due": [], "came": []}
'''
RO_OUT_NEW = RO_OUT_OLD + '''    out["link_on"], out["call_on"] = feature_on("link", path), feature_on("call", path)      # S558: the owner's two switches
'''

RO_THROUGH_OLD = '''    through = v["through"] if v["ok"] else None
'''
RO_THROUGH_NEW = RO_THROUGH_OLD + '''    links = _s558_links(path) if out["link_on"] else {}         # S558: a live link supplies the visit (never THE RULE)
    for r in rows:
        r["s558_link"] = links.get(r["id"])
'''

RO_END_OLD = '''            out["came"].append(r)
    return out
'''
RO_END_NEW = '''            out["came"].append(r)
    if out["link_on"] and not everything:
        _s558_list(out, rows, v, fps, today, wait, links, finance_db)     # S558: the linked lines' words; the suggestions
    return out
'''

RO_BLOCK_ANCHOR = "# ------------------------------------------------------------------ S497: the screens (the mock-up's own styles)\n"
RO_BLOCK = r'''# ------------------------------------------------------------------ S558: link a different number . the IVR call (D726)
LINK_SLACK = 3                                   # a suggestion's first visit: from the booking day to the last day + 3
LINK_MAX = 8                                     # at most this many suggestions, and search results
CALL_URL = os.environ.get("RING_CALL_URL", "http://127.0.0.1:8097/call")     # call_api.py (the service call-api)
CALL_TIMEOUT = 30
CALL_GAP = 60                                    # one IVR call per line per 60 seconds
S558_SWITCHES = {"link": "link_on", "call": "call_on"}
S558_ACTS = ("link", "unlink", "find", "call")
T_LINK_FOLD = "Shayad yeh aaye?"
T_LINK_YES = "Haan, yahi hai"
T_LINK_FIRST = "pehli visit %s"
T_LINK_NONE = "Is samay mein koi naya mareez nahi mila — neeche naam ya clinic ID se dhoondhein"
T_LINK_SEARCH = "Clinic ID ya naam"
T_LINK_FIND = "Dhoondho"
T_LINK_NOHIT = "Is naam / ID se booking ke baad koi visit nahi mili"
T_LINK_CAME = "doosre number se aaye"
T_LINK_BY = "linked by %s"
T_UNLINK = "Galat link — hatao"
T_LINK_OFF = "Yeh suvidha abhi band hai."
T_LINK_BAD = "Is clinic ID ki booking ke din ya baad ki koi visit nahi mili — link nahi hua."
T_LINK_TAKEN = "Yeh line pehle se ek mareez se judi hai."
T_NOT_OPEN = "Yeh line ab “Nahi aaye” ya “Aane baaki” mein nahi hai. List dobara dekhein."
T_NO_LINK = "Is line par koi link nahi hai."
T_UNLINK_LATE = "Link usi din hataya ja sakta hai jis din joda gaya tha — ab Dr sahab hi hata sakte hain."
T_CALL_BTN = "IVR se call karein"
T_CALL_OK = "Aapka phone baj raha hai — uthaiye, patient se jod diya jayega"
T_CALL_NO = "Call nahi lagi: %s"
T_CALL_NOAGENT = "Aapka phone IVR mein nahi juda — owner se kahein"
T_CALL_OFF = "IVR call abhi band hai."
T_CALL_WAIT = "Is line par abhi call ki gayi thi — ek minute baad dobara dabayein."
T_CALL_NONUM = "Call nahi lagi: is line ka number 10 ank ka mobile nahi hai"
T_CALL_DOWN = "Call nahi lagi: IVR server se jawab nahi aaya"
T_CALL_NOKEY = "Call nahi lagi: IVR server par set nahi hai"
S558_SAID = {"link_on": "Doosre number se link: turned on.", "link_off": "Doosre number se link: turned off.",
             "call_on": "IVR call button: turned on.", "call_off": "IVR call button: turned off."}


def feature_on(name, path=None):
    """S558: is one of the owner's two switches on -- 'link' or 'call'? OFF unless he turned it on; unreadable = OFF."""
    k = S558_SWITCHES.get(name)
    return bool(k) and _kv_get(k, path) == "1"


def set_feature(name, on, by, path=None, now=None):
    k = S558_SWITCHES.get(name)
    if not k:
        return False
    _kv_set(k, "1" if on else "0", by, path, now)
    return True


def _s558_links(path=None):
    """{outcome id: its live link} -- the ring store READ-ONLY; no table yet (the store before S558) answers {}."""
    try:
        con = _ro_db(path)
    except sqlite3.Error:
        return {}
    try:
        return {r["outcome_id"]: dict(r) for r in con.execute("SELECT * FROM appt_link WHERE COALESCE(undone_at,'')=''")}
    except sqlite3.Error:
        return {}
    finally:
        con.close()


def _s558_fin(finance_db=None):
    return sqlite3.connect("file:%s?mode=ro" % (finance_db or rc.FINANCE_DB), uri=True, timeout=3)


def _s558_people(cids, finance_db=None):
    """{clinic id: {name, first, fp}} -- the name and fingerprint Docterz holds, and the FIRST-EVER visit: the earliest
    patient_visit date for that ID or patient_ref.first_seen, whichever is earlier. finance.db READ-ONLY; None when it
    cannot be read."""
    cids = sorted({str(c).strip() for c in cids if str(c or "").strip()})
    out = {c: {"name": "", "first": None, "fp": ""} for c in cids}
    if not cids:
        return out
    try:
        con = _s558_fin(finance_db)
    except sqlite3.Error:
        return None
    try:
        for i in range(0, len(cids), 400):
            part = cids[i:i + 400]
            q = ",".join("?" * len(part))
            for cid, first in con.execute("SELECT clinic_id, MIN(visit_date) FROM patient_visit WHERE clinic_id IN (%s) "
                                          "GROUP BY clinic_id" % q, part):
                p = out.get(str(cid or "").strip())
                if p is not None:
                    p["first"] = _day(first)
            for cid, name, seen, fp in con.execute("SELECT clinic_id, name, first_seen, mobile_fp FROM patient_ref WHERE clinic_id IN (%s) "
                                                   "ORDER BY (merged_into IS NULL OR merged_into='') ASC, id ASC" % q, part):
                p = out.get(str(cid or "").strip())
                if p is None:
                    continue
                p["name"], p["fp"] = (name or "").strip() or p["name"], str(fp or "").strip() or p["fp"]
                s = _day(seen)
                if s is not None and (p["first"] is None or s < p["first"]):
                    p["first"] = s
    except sqlite3.Error:
        return None
    finally:
        con.close()
    return out


def _s558_words(cid, p):
    """'Sunita Devi · ID 9917 · pehli visit 06-Oct' -- the way a suggestion and a search result are shown."""
    first = (p or {}).get("first")
    return " · ".join(x for x in (((p or {}).get("name") or ""), "ID " + cid, (T_LINK_FIRST % _dm(first)) if first else "") if x)


def _s558_list(out, rows, v, fps, today, wait, links, finance_db=None):
    """S558, after THE RULE has placed every line (a READ, like list_data): the words of a linked line, and the
    suggestions on every Nahi aaye / Aane baaki line whose call card had no clinic ID (a new number)."""
    linked = [r for r in out["came"] if r.get("s558_link")]
    open_new = [r for r in out["noshow"] + out["due"] if not _ids_on_call(r)]
    if not (linked or open_new) or not v["ok"]:
        return
    taken = {str(x.get("clinic_id") or "").strip() for x in links.values()}
    for r in rows:
        taken.update(_ids_on_call(r))
        if r.get("visit_id"):
            taken.add(r["visit_id"])
    pool = set(v["by_id"]) if open_new else set()
    ppl = _s558_people(pool | {str(r["s558_link"].get("clinic_id") or "").strip() for r in linked}, finance_db)
    if ppl is None:
        return
    for r in linked:
        cid = str(r["s558_link"].get("clinic_id") or "").strip()
        r["s558_name"] = (ppl.get(cid) or {}).get("name") or ""
        if not r["known"]:
            r["dz_name"], r["dz_id"] = r["s558_name"] or r.get("dz_name") or "", cid
    seen_fp = {}
    for fp, lst in v["by_fp"].items():
        for _d, cid in lst:
            seen_fp.setdefault(cid, set()).add(fp)
    for r in open_new:
        last = r["appt"] if r["appt"] is not None else r["booked"] + timedelta(days=wait)
        hi = min(last + timedelta(days=LINK_SLACK), today)
        mine = fps.get(r.get("mobile") or "") or ""
        cands = []
        for cid in pool:
            p = ppl.get(cid) or {}
            if cid in taken or p.get("first") is None or not (r["booked"] <= p["first"] <= hi):
                continue
            if mine and (p.get("fp") == mine or mine in seen_fp.get(cid, ())):
                continue
            cands.append((p["first"], cid, p.get("name") or ""))
        cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
        r["s558_new"] = True
        r["s558_sugg"] = [(cid, _s558_words(cid, ppl.get(cid))) for _f, cid, _n in cands[:LINK_MAX]]


def _s558_line(oid, path=None, now=None, finance_db=None):
    """(the list's own row for ONE line, the part it stands in, '') -- or (None, '', why not)."""
    oid = good_id(oid)
    if oid is None:
        return None, "", T_NO_APPT
    d = list_data(None, path, now, finance_db, everything=True)
    for part in ("noshow", "due", "came"):
        for r in d[part]:
            if r["id"] == oid:
                return r, part, ""
    return None, "", T_NOT_OPEN


def _s558_has_visit(cid, booked, today, finance_db=None):
    """Does Docterz show a visit for this clinic ID on or after the booking day (and not after today)? READ-ONLY."""
    try:
        con = _s558_fin(finance_db)
    except sqlite3.Error:
        return False
    try:
        return con.execute("SELECT 1 FROM patient_visit WHERE clinic_id=? AND visit_date>=? AND visit_date<=? LIMIT 1",
                           (cid, booked.isoformat(), today.isoformat() + "~")).fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        con.close()


def find_people(oid, q, path=None, now=None, finance_db=None):
    """The fold's search: a clinic ID (exact) or a name (contains, case-blind), over the patients with a visit from the
    line's booking day to today; newest first visit first, at most LINK_MAX. Returns (ok, msg, hits)."""
    if not feature_on("link", path):
        return False, T_LINK_OFF, []
    r, part, why = _s558_line(oid, path, now, finance_db)
    if r is None:
        return False, why, []
    if part not in ("noshow", "due"):
        return False, T_NOT_OPEN, []
    q = str(q or "").strip()[:40]
    if not q:
        return True, "ok", []
    today = _ist(now).date()
    v = visits_since(r["booked"].isoformat(), today, finance_db)
    if not v["ok"]:
        return False, T_CANNOT, []
    pool = set(v["by_id"])
    ppl = _s558_people(pool, finance_db)
    if ppl is None:
        return False, T_CANNOT, []
    if q in pool:
        got = [q]
    else:
        low = q.lower()
        got = [c for c in pool if len(low) >= 2 and low in (ppl.get(c) or {}).get("name", "").lower()]
    got.sort(key=lambda c: ((ppl.get(c) or {}).get("first") or r["booked"], c), reverse=True)
    return True, "ok", [{"clinic_id": c, "name": (ppl.get(c) or {}).get("name") or "", "words": _s558_words(c, ppl.get(c))}
                        for c in got[:LINK_MAX]]


def link_appt(oid, clinic_id, by_login, by_name, path=None, now=None, finance_db=None):
    """'Haan, yahi hai': this line's caller registered under that clinic ID. Taken ONLY for a line standing in Nahi aaye
    or Aane baaki this minute, and ONLY when Docterz shows a visit for that ID on or after the booking day. One live link
    per line (outcome_id UNIQUE); a line whose link was undone takes a new one in the same row. Returns (ok, msg)."""
    if not feature_on("link", path):
        return False, T_LINK_OFF
    t = _ist(now)
    cid = str(clinic_id or "").strip()[:40]
    if not cid:
        return False, T_LINK_BAD
    r, part, why = _s558_line(oid, path, now, finance_db)
    if r is None:
        return False, why
    if r.get("s558_link"):
        return False, T_LINK_TAKEN
    if part not in ("noshow", "due"):
        return False, T_NOT_OPEN
    if not _s558_has_visit(cid, r["booked"], t.date(), finance_db):
        return False, T_LINK_BAD
    init_db(path)
    con = db(path)
    try:
        prev = con.execute("SELECT * FROM appt_link WHERE outcome_id=?", (r["id"],)).fetchone()
        mob = str(r.get("mobile") or "")
        if prev is None:
            try:
                con.execute("INSERT INTO appt_link(outcome_id, clinic_id, mobile, linked_by, linked_name, linked_at) VALUES(?,?,?,?,?,?)",
                            (r["id"], cid, mob, by_login or "", by_name or "", _fmt(t)))
            except sqlite3.IntegrityError:
                return False, T_LINK_TAKEN                     # another press linked it in the same moment
            old = ""
        else:
            cur = con.execute("UPDATE appt_link SET clinic_id=?, mobile=?, linked_by=?, linked_name=?, linked_at=?, undone_by=NULL, "
                              "undone_at=NULL WHERE outcome_id=? AND COALESCE(undone_at,'')<>''",
                              (cid, mob, by_login or "", by_name or "", _fmt(t), r["id"]))
            if cur.rowcount != 1:
                return False, T_LINK_TAKEN
            old = prev["clinic_id"] or ""
        _appt_event(con, r["id"], "link", old, cid, by_login, by_name, t)
        con.commit()
        return True, "ok"
    finally:
        con.close()


def unlink_appt(oid, by_login, by_name, owner=False, path=None, now=None):
    """'Galat link — hatao': any staff member on the same India day as the link; the owner any day. Writes undone_by /
    undone_at, never deletes; the line goes back to where THE RULE puts it. Returns (ok, msg)."""
    if not feature_on("link", path):
        return False, T_LINK_OFF
    oid = good_id(oid)
    if oid is None:
        return False, T_NO_APPT
    t = _ist(now)
    init_db(path)
    con = db(path)
    try:
        lk = con.execute("SELECT * FROM appt_link WHERE outcome_id=? AND COALESCE(undone_at,'')=''", (oid,)).fetchone()
        if lk is None:
            return False, T_NO_LINK
        if not owner and str(lk["linked_at"] or "")[:10] != t.date().isoformat():
            return False, T_UNLINK_LATE
        cur = con.execute("UPDATE appt_link SET undone_by=?, undone_at=? WHERE id=? AND COALESCE(undone_at,'')=''",
                          (by_login or "", _fmt(t), lk["id"]))
        if cur.rowcount != 1:
            return False, T_NO_LINK
        _appt_event(con, oid, "unlink", lk["clinic_id"] or "", "", by_login, by_name, t)
        con.commit()
        return True, "ok"
    finally:
        con.close()


def ivr_agent(login, agents=None):
    """The MyOperator name call_api.py knows this login by: ring_agents.json, the entry whose user = login. '' if none."""
    try:
        a = rc.load_agents() if agents is None else agents
        for x in a.values():
            if isinstance(x, dict) and str(x.get("user") or "") == str(login or "") and str(x.get("name") or "").strip():
                return str(x["name"]).strip()
    except Exception:
        pass
    return ""


def _ivr_post(url, body, key, timeout):
    """One POST to call_api.py: (http status, its JSON). The key rides in the X-Call-Key header only. Nothing is logged."""
    import urllib.error
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Call-Key", key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code, raw = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read().decode("utf-8", "replace")
    try:
        j = json.loads(raw)
    except Exception:
        j = {}
    return code, (j if isinstance(j, dict) else {})


def _s558_short(reason):
    """call_api's reason, short, with any long run of digits cut to its last 4."""
    s = re.sub(r"\d{5,}", lambda m: "…" + m.group(0)[-4:], " ".join(str(reason or "").split()))
    return s[:120] or "IVR ne mana kiya"


def ivr_call(oid, login, by_name, path=None, now=None, finance_db=None):
    """'IVR se call karein' on a Nahi aaye line: the staff member's own phone rings first, then MyOperator joins the
    patient (call_api.py). The number is the line's STORED mobile -- never one from the page. One call per line per
    CALL_GAP seconds. Kept as an appt_event 'ivr_call' (who, when, accepted). Returns (ok, msg, http status)."""
    if not feature_on("call", path):
        return False, T_CALL_OFF, 403
    agent = ivr_agent(login)
    if not agent:
        return False, T_CALL_NOAGENT, 400
    t = _ist(now)
    o, why = _noshow_now(oid, path, now, finance_db)
    if o is None:
        return False, why, (404 if why == T_NO_APPT else 409)
    m10 = rc.mobile10(o.get("mobile"))
    if not m10:
        return False, T_CALL_NONUM, 400
    con = db(path)
    con.isolation_level = None
    try:
        con.execute("BEGIN IMMEDIATE")
        last = con.execute("SELECT MAX(created_at) FROM appt_event WHERE outcome_id=? AND kind='ivr_call'", (o["id"],)).fetchone()[0]
        if last is not None and int(time.time()) - int(last) < CALL_GAP:
            con.execute("ROLLBACK")
            return False, T_CALL_WAIT, 429
        _appt_event(con, o["id"], "ivr_call", "", "trying", login, by_name, t)
        eid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.execute("COMMIT")
    finally:
        con.close()
    key = rc.load_env(WA_ENV).get("CALL_API_SECRET", "")
    if not key:
        ok, msg, code, said = False, T_CALL_NOKEY, 502, "refused"
    else:
        try:
            st, j = _ivr_post(CALL_URL, {"agent": agent, "patient_number": m10, "reference_id": "RL%d" % o["id"]}, key, CALL_TIMEOUT)
        except Exception:
            st, j = 0, {}
        if st == 200 and j.get("accepted") is True:
            ok, msg, code, said = True, T_CALL_OK, 200, "accepted"
        elif st == 400 and "agent" in str(j.get("reason") or "").lower():
            ok, msg, code, said = False, T_CALL_NOAGENT, 400, "refused"
        elif st == 0:
            ok, msg, code, said = False, T_CALL_DOWN, 502, "error"
        else:
            ok, msg, code, said = False, T_CALL_NO % _s558_short(j.get("reason") or ("http %s" % st)), 502, "refused"
    con = db(path)
    try:
        con.execute("UPDATE appt_event SET new_value=? WHERE id=?", (said, eid))
        con.commit()
    finally:
        con.close()
    return ok, msg, code


def s558_act(act, oid, body, who, login, name, path=None, now=None, finance_db=None):
    """The list's four new acts, through ring_list_act. Returns (json, http status)."""
    if act == "call":
        ok, msg, code = ivr_call(oid, login, name, path, now, finance_db)
        return {"ok": ok, "msg": msg}, code
    if not feature_on("link", path):
        return {"ok": False, "msg": T_LINK_OFF}, 403
    if act == "find":
        ok, msg, hits = find_people(oid, (body or {}).get("q"), path, now, finance_db)
        return {"ok": ok, "msg": msg, "hits": hits}, (200 if ok else 409)
    if act == "link":
        ok, msg = link_appt(oid, (body or {}).get("clinic_id"), login, name, path, now, finance_db)
    else:
        ok, msg = unlink_appt(oid, login, name, (who or {}).get("role") == "doctor", path, now)
    code = 200 if ok else {T_LINK_OFF: 403, T_UNLINK_LATE: 403, T_NO_APPT: 404, T_NO_LINK: 404, T_LINK_BAD: 400}.get(msg, 409)
    return {"ok": ok, "msg": msg}, code


# --- S558: what the page draws (only while a switch is on) ---
_S_BTN_CALL = ("min-height: 44px; padding: 0 14px; border: 0; border-radius: 10px; background: #15803d; color: #ffffff; "
               "font-size: 15px; font-weight: 600")
_S_S558_IN = ("min-height: 40px; padding: 0 10px; border: 1px solid #64748b; border-radius: 10px; background: #0f172a; "
              "color: #e5eefb; font-size: 15px; width: 160px")


def _s558_in(td, extra):
    """extra put inside a cell, before its closing tag."""
    return (td[:-5] + extra + "</td>") if (extra and td.endswith("</td>")) else td


def _s558_fold(r):
    """The fold 'Shayad yeh aaye?' on a new number's line: the suggestions, one button each, and a search."""
    item = ('<div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px"><span>%s</span>'
            '<button type="button" data-id="%d" data-cid="%s" data-say="%s" onclick="s558link(this)" style="%s">%s</button></div>')
    rows = "".join(item % (_esc(words), r["id"], _esc(cid), _esc(words), _S_BTN_LINE, T_LINK_YES) for cid, words in r.get("s558_sugg") or [])
    if not rows:
        rows = '<div style="%s; margin-top: 8px">%s</div>' % (_S_SUB, T_LINK_NONE)
    search = ('<div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 10px">'
              '<input type="text" maxlength="40" placeholder="%s" onkeydown="if(event.key===\'Enter\'){s558find(this.nextSibling);}" style="%s">'
              '<button type="button" data-id="%d" data-none="%s" onclick="s558find(this)" style="%s">%s</button>'
              '<div data-s558-hits style="flex-basis: 100%%"></div></div>'
              % (T_LINK_SEARCH, _S_S558_IN, r["id"], T_LINK_NOHIT, _S_BTN_LINE, T_LINK_FIND))
    return ('<details data-s558-fold style="margin-top: 8px; font-weight: 400"><summary style="cursor: pointer; color: #93c5fd; '
            'font-size: 15px; font-weight: 600">%s</summary>%s%s</details>' % (T_LINK_FOLD, rows, search))


def _s558_call_btn(r, agent):
    if agent:
        return '<button type="button" data-id="%d" onclick="s558call(this)" style="%s">%s</button>' % (r["id"], _S_BTN_CALL, T_CALL_BTN)
    return ('<button type="button" disabled style="%s">%s</button><div style="flex-basis: 100%%; font-size: 13px; color: #a8b5c8">%s</div>'
            % (_S_WA_BTN, T_CALL_BTN, T_CALL_NOAGENT))


def _s558_came(r, today, doctor, names):
    lk = r.get("s558_link") or {}
    cid = str(lk.get("clinic_id") or "").strip()
    if not cid:
        return ""
    words = " · ".join(x for x in (T_LINK_CAME, r.get("s558_name") or "", "ID " + cid,
                                   T_LINK_BY % _person(lk.get("linked_by"), lk.get("linked_name"), names)) if x)
    undo = ""
    if doctor or str(lk.get("linked_at") or "")[:10] == today.isoformat():
        undo = ('<div style="margin-top: 6px"><button type="button" data-id="%d" onclick="s558unlink(this)" style="%s">%s</button></div>'
                % (r["id"], _S_BTN_LINE, T_UNLINK))
    return '<div style="font-size: 14px; font-weight: 600; color: #86efac; white-space: normal">%s</div>%s' % (_esc(words), undo)


def _s558_decorate(data, doctor, viewer):
    """S558: the fold, the call button and a linked line's words -- each only while its switch is on."""
    today = data["today"]
    lk, cl = data.get("link_on"), data.get("call_on")
    agent = ivr_agent(viewer) if cl else ""
    names = _agent_names() if lk else {}
    for r in data["noshow"]:
        if lk and r.get("s558_new"):
            r["s558_fold"] = _s558_fold(r)
        if cl:
            r["s558_call"] = _s558_call_btn(r, agent)
    for r in data["due"]:
        if lk and r.get("s558_new"):
            r["s558_fold"] = _s558_fold(r)
    for r in data["came"]:
        if lk and r.get("s558_link"):
            r["s558_came"] = _s558_came(r, today, doctor, names)


def _s558_owner_box(data):
    """HIS two toggles (English), below his box. Both installed OFF."""
    def one(feat, label, on, what):
        return ('    <form method="post" action="/portal/ring/list/switch" style="margin: 0; display: flex; flex-wrap: wrap; gap: 10px; '
                'align-items: center"><input type="hidden" name="feature" value="%s"><input type="hidden" name="on" value="%s">'
                '<span>%s: <b>%s</b></span><button type="submit" style="%s">%s</button>'
                '<span style="flex-basis: 100%%; font-size: 14px; color: #a8b5c8">%s</span></form>\n'
                % (feat, "0" if on else "1", label, "ON" if on else "OFF", _S_BTN_LINE if on else _S_BTN_BLUE,
                   "Turn off" if on else "Turn on", what))
    return ('  <div style="background: #1e293b; border: 1px dashed #64748b; border-radius: 14px; padding: 14px 18px; font-size: 15px; '
            'color: #dbe5f3; display: flex; flex-direction: column; gap: 10px">\n'
            '    <div><b>Two more tools for staff</b> — each stays hidden until you turn it on.</div>\n'
            + one("link", "Doosre number se link", data.get("link_on"),
                  "On a new number's line: “Shayad yeh aaye?” — the new patients registered in that window, a search, and "
                  "“Haan, yahi hai”. The line then shows as came, and the next call from that number shows the patient.")
            + one("call", "IVR call button", data.get("call_on"),
                  "On each “Nahi aaye” line: “IVR se call karein” — the staff member's own phone rings first, then MyOperator "
                  "joins the patient, as in the Callback Tracker.")
            + '  </div>\n')


'''

RO_JS_OLD = '''function s497close(b){if(confirm(b.textContent+'?')){s497post({id:Number(b.getAttribute('data-id')),act:'closed'});}}
</script>"""'''
RO_JS_NEW = '''function s497close(b){if(confirm(b.textContent+'?')){s497post({id:Number(b.getAttribute('data-id')),act:'closed'});}}
function s558link(b){if(confirm(b.getAttribute('data-say')+' \\u2014 '+b.textContent+'?')){s497post({id:Number(b.getAttribute('data-id')),act:'link',clinic_id:b.getAttribute('data-cid')});}}
function s558unlink(b){if(confirm(b.textContent+'?')){s497post({id:Number(b.getAttribute('data-id')),act:'unlink'});}}
function s558find(b){var box=b.parentNode,i=box.querySelector('input'),out=box.querySelector('[data-s558-hits]'),q=((i&&i.value)||'').trim();
if(!q||!out){return;} out.textContent='...';
fetch('/portal/ring/list/act',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:Number(b.getAttribute('data-id')),act:'find',q:q})})
.then(function(r){return r.json()}).then(function(j){out.textContent=''; if(!j.ok){out.textContent=j.msg||'error';return;}
if(!(j.hits||[]).length){out.textContent=b.getAttribute('data-none')||'\\u2014';return;}
j.hits.forEach(function(h){var d=document.createElement('div'); d.style.cssText='display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:8px';
var s=document.createElement('span'); s.textContent=h.words; var k=document.createElement('button'); k.type='button'; k.textContent='Haan, yahi hai';
k.setAttribute('data-id',b.getAttribute('data-id')); k.setAttribute('data-cid',h.clinic_id); k.setAttribute('data-say',h.words); k.style.cssText=b.style.cssText;
k.onclick=function(){s558link(k);}; d.appendChild(s); d.appendChild(k); out.appendChild(d);});})
.catch(function(){out.textContent='server se jawab nahi';});}
function s558call(b){if(b.disabled){return;} b.disabled=true;
fetch('/portal/ring/list/act',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:Number(b.getAttribute('data-id')),act:'call'})})
.then(function(r){return r.json()}).then(function(j){alert(j.msg||'error'); setTimeout(function(){b.disabled=false;},60000);})
.catch(function(){b.disabled=false; alert('server se jawab nahi');});}
</script>"""'''

RO_NOSHOW_OLD = '''    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today) + _mobile_cell(r.get("mobile"), r.get("unmatchable"))
            + '<td style="%s">%s<div style="font-size: 14px; color: #fdba74; font-weight: 600">%s</div></td>'
'''
RO_NOSHOW_NEW = '''    return ('<tr>' + _booked_cell(r) + _s558_in(_patient_cell(r, today), r.get("s558_fold") or "")
            + _mobile_cell(r.get("mobile"), r.get("unmatchable"))
            + '<td style="%s">%s<div style="font-size: 14px; color: #fdba74; font-weight: 600">%s</div></td>'
'''
RO_BTN_OLD = '''onclick="s497close(this)" style="%s">%s</button></div>\''''
RO_BTN_NEW = '''onclick="s497close(this)" style="%s">%s</button>%s</div>\''''
RO_PICK_OLD = '''T_CLOSE, pick))'''
RO_PICK_NEW = '''T_CLOSE, r.get("s558_call") or "", pick))'''

RO_DUE_OLD = '''    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today) + _mobile_cell(r.get("mobile"), r.get("unmatchable"))
            + '<td style="%s">%s</td>' % (_S_NOWRAP, day)
'''
RO_DUE_NEW = '''    return ('<tr>' + _booked_cell(r) + _s558_in(_patient_cell(r, today), r.get("s558_fold") or "")
            + _mobile_cell(r.get("mobile"), r.get("unmatchable"))
            + '<td style="%s">%s</td>' % (_S_NOWRAP, day)
'''

RO_CAME_OLD = '''    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today, came=True)'''
RO_CAME_NEW = '''    late += r.get("s558_came") or ""                           # S558: 'doosre number se aaye ...' and its undo
    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today, came=True)'''

RO_SAID_OLD = '''"bad": "Not saved — the days must be 1 to 30, and the date not before %s." % hard_words}.get(msg, "")'''
RO_SAID_NEW = '''"bad": "Not saved — the days must be 1 to 30, and the date not before %s." % hard_words}.get(msg, "") or S558_SAID.get(msg, "")'''

RO_RL_OLD = '''def render_list(data, doctor=False, on=False, holders=(), msg=""):'''
RO_RL_NEW = '''def render_list(data, doctor=False, on=False, holders=(), msg="", viewer=""):'''
RO_WHO_OLD = '''            r["who"] = _person(r.get("login"), r.get("handler"), names)
'''
RO_WHO_NEW = RO_WHO_OLD + '''    _s558_decorate(data, doctor, viewer)                       # S558: only while a switch is on
'''
RO_BOX_OLD = '''(_owner_box(data, on, holders, msg) if doctor else "")'''
RO_BOX_NEW = '''((_owner_box(data, on, holders, msg) + _s558_owner_box(data)) if doctor else "")'''

RO_ROUTE_OLD = '''                                      str(request.args.get("m") or "").strip()))
'''
RO_ROUTE_NEW = '''                                      str(request.args.get("m") or "").strip(), viewer=(sso_user(request) or {}).get("user", "")))
'''

RO_SW_OLD = '''        on = str(request.form.get("on") or "") == "1"
        set_list_on(on, who.get("user", ""), path)
'''
RO_SW_NEW = '''        on = str(request.form.get("on") or "") == "1"
        feat = str(request.form.get("feature") or "")
        if feat in S558_SWITCHES:                              # S558: his two toggles -- link, IVR call
            set_feature(feat, on, who.get("user", ""), path)
            return redirect("/portal/ring/list?m=%s_%s" % (feat, "on" if on else "off"))
        set_list_on(on, who.get("user", ""), path)
'''

RO_ACT_OLD = '''        elif act == "closed":
            ok, msg = close_appt(oid, login, name, path)
'''
RO_ACT_NEW = RO_ACT_OLD + '''        elif act in S558_ACTS:                                 # S558: link . unlink . find . call
            j, code = s558_act(act, oid, body, who, login, name, path)
            return jsonify(j), code
'''

RO_EDITS = [(RO_HEAD_OLD, RO_HEAD_NEW, 1), (RO_INIT_OLD, RO_INIT_NEW, 1), (RO_IDS_OLD, RO_IDS_NEW, 1),
            (RO_OUT_OLD, RO_OUT_NEW, 1), (RO_THROUGH_OLD, RO_THROUGH_NEW, 1), (RO_END_OLD, RO_END_NEW, 1),
            (RO_BLOCK_ANCHOR, RO_BLOCK + RO_BLOCK_ANCHOR, 1), (RO_JS_OLD, RO_JS_NEW, 1),
            (RO_NOSHOW_OLD, RO_NOSHOW_NEW, 1), (RO_BTN_OLD, RO_BTN_NEW, 1), (RO_PICK_OLD, RO_PICK_NEW, 1),
            (RO_DUE_OLD, RO_DUE_NEW, 1), (RO_CAME_OLD, RO_CAME_NEW, 1), (RO_SAID_OLD, RO_SAID_NEW, 1),
            (RO_RL_OLD, RO_RL_NEW, 1), (RO_WHO_OLD, RO_WHO_NEW, 1), (RO_BOX_OLD, RO_BOX_NEW, 1),
            (RO_ROUTE_OLD, RO_ROUTE_NEW, 1), (RO_SW_OLD, RO_SW_NEW, 1), (RO_ACT_OLD, RO_ACT_NEW, 1)]

EDITS = {"ring_outcome.py": RO_EDITS, "ring_common.py": RC_EDITS}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(live_dir):
    """{name: new bytes}, or raises SystemExit with the reason. Nothing is written here."""
    out = {}
    for name, edits in EDITS.items():
        p = os.path.join(live_dir, name)
        raw = open(p, "rb").read()
        if md5b(raw) != FROM[name]:
            raise SystemExit("REFUSED: %s is %s, not its FROM pin %s -- nothing written" % (p, md5b(raw), FROM[name]))
        src = raw.decode("utf-8")
        for i, (old, new, n) in enumerate(edits, 1):
            c = src.count(old)
            if c != n:
                raise SystemExit("REFUSED: %s edit %d: its anchor is found %d times, not %d -- nothing written" % (name, i, c, n))
            src = src.replace(old, new)
        b = src.encode("utf-8")
        compile(b, name, "exec")
        out[name] = b
    return out


def main(argv):
    if argv[:1] == ["--pins"]:
        for n in ("ring_outcome.py", "ring_common.py"):
            print(n, FROM[n], TO[n])
        return 0
    if argv[:1] == ["--check"] and len(argv) == 3:
        got = build(argv[1])
        bad = 0
        for n, b in got.items():
            k = open(os.path.join(argv[2], n), "rb").read()
            same = (k == b and md5b(b) == TO[n])
            bad += 0 if same else 1
            print("%s %s %s" % (n, md5b(b), "= the file in the kit, at its TO pin" if same else "DIFFERS from the kit's file / TO pin"))
        return 1 if bad else 0
    if len(argv) == 2:
        got = build(argv[0])
        os.makedirs(argv[1], exist_ok=True)
        for n, b in got.items():
            if "@@" not in TO[n] and md5b(b) != TO[n]:
                raise SystemExit("REFUSED: %s rebuilt to %s, not its TO pin %s -- nothing written" % (n, md5b(b), TO[n]))
        for n, b in got.items():
            with open(os.path.join(argv[1], n), "wb") as fh:
                fh.write(b)
            print("%s %s written" % (n, md5b(b)))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
