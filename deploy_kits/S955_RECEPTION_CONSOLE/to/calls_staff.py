#!/usr/bin/env python3
"""
calls_staff.py -- S948_STAFF_CONSOLE (the parent, S515, 24-Nov-2026): the STAFF's own Call Console, built to the screens
the owner approved (v5.1, his "ok" at 18:05 IST 24-Nov: https://claude.ai/artifact/V7zF7d79tCF9FS9H1HiNHq; D1059 the
Callback Tracker's own words; D1060 FULL mobile numbers on this page, "Call verdict" in place of "AI reading").

ONE PAGE, SIX TABS, for the phone staff (setting PORTAL_PHONE_STAFF) and the logins of PORTAL_STAFF_CONSOLE_EXTRA
(default "shavez") -- and, from S955 (D1068, his word 17:05 IST 25-Nov "Reception mobile required"), the reception
mobile's login (PORTAL_RECEPTION_AGENT, default "reception"; PORTAL_STAFF_CONSOLE_RECEPTION=0 keeps it out). Its
"Handled today" is the reception mobile's own calls of today, whoever the owner's page credits them to, with the Call
verdict, without "Wrong?" or the recording (both belong to a person's card; the recording route serves her own calls):
  1 Follow-ups due   the open follow-up rows nobody has tried today, in the Tracker's calling order (sent back by the
                     doctor, Due Today, Grace Period, Actionable Missed Follow-Up, Probable Dropout, Procedure call-back,
                     then the rest); from 16:00 the untried Grace Period rows move to Evening calls.
  2 Call again       one unanswered attempt today; due 2 hours after it (PORTAL_STAFF_CALL_AGAIN_H), lit once due.
  3 Evening calls    two unanswered attempts today, then (from 16:00) the untried Grace Period rows. A third unanswered
                     attempt ends the day for that number (no fourth try). The count shows from 16:00
                     (PORTAL_STAFF_EVENING_FROM); before that the tab still lists who is waiting for the evening.
  4 Incoming missed  a missed incoming call with no connected call after it and nobody has tried yet. One try moves it to
                     Call again, two to Evening calls. A number that rang in AND is on the follow-up list shows once, on the
                     missed-call path.
                     S951 (D1063, his word 10:02 25-Nov): EVERY missed call of yesterday still unresolved -- no
                     connected call, no WhatsApp from him, no Docterz visit since -- is on today's lists on this path
                     ("Missed after hours" from 21:00, else "Missed yesterday, not reached"); today is a fresh day for
                     tries, yesterday's are said on the line.
  5 WhatsApp         the chats awaiting a reply -- calls_console.wa_awaiting(), the owner's own rule (S818), one line per chat.
  6 Handled today    HER OWN calls only (her card, calls_console.card_for), with the Call verdict, the recording, and "Wrong?":
                     one line that questions the verdict of one of her answered calls; it reaches the owner's card as Disputed
                     (fig "verdict"), where he answers Accept / It stands, as every other dispute.
A patient reached today (an answered call either way) or who wrote on WhatsApp today leaves the call lists by himself;
nobody presses done. "Switched off" is said of an unanswered attempt on which the phone never rang (ring 0 s); every other
unanswered attempt is "No answer" (console.db keeps only bridged / missed).

NOTHING NEW IS DECIDED HERE: every list is a transform of what the owner's page already reads -- wa_load, build_people,
followup_list, wa_awaiting, card_for (calls_console.py) over console.db, the inbox and finance.db, all read-only. The page
writes two things only: a click-to-call (calls_console.ivr_call, her own MyOperator agent, one call per number per minute;
only a number this page has listed in the last hour) and a dispute row in the owner's review store (call_review.db).

Routes (registered from the END of calls_console.register(); a fault here never takes the owner's page down):
  GET  /portal/console/staff                  the page (staff gate; the doctor: a picker, or ?as=<login> to see hers)
  GET  /portal/console/staff/api/lists        the same lists as JSON (no-store)
  POST /portal/console/staff/api/call         {"phone10"} -> the IVR call (header X-Staff-Console: 1)
  POST /portal/console/staff/api/dispute      {"ref", "text"} -> "Wrong?" on her own call's verdict (header X-Staff-Console: 1)
The tile "My Call Console" is added to the portal's tile list at register time, beside "Call Console", granted by name in
tile_grants.json (v48) to the phone staff and Shavez -- side by side with the Callback Tracker.
"""

import datetime as _dt
import re
import sys
import time

from flask import request, jsonify, make_response, render_template_string, abort

KIT = "S948_STAFF_CONSOLE"
VERSION = "S951 1.1"           # S948 1.0 + S951_YESTERDAY_CARRY (D1063, his word 10:02 25-Nov)
TILE_NAME = "My Call Console"
TILE_AFTER = "Call Console"
CALL_AGAIN_H_DEFAULT = 2.0
EVENING_FROM_DEFAULT = "16:00"
EVENING_TO_DEFAULT = "18:00"
AFTER_HOURS_FROM_DEFAULT = "21:00"   # S951: a miss from this time reads "Missed after hours" (his word 10:02 25-Nov)
MAX_TRIES = 3                  # a third unanswered attempt ends the day for the number
STALE_MIN = 30                 # the bar's time turns amber past this
OFFER_KEEP_S = 3600            # the call route dials only a number a list showed in the last hour
EXTRA_DEFAULT = "shavez"
RECEPTION_ON_DEFAULT = "1"     # S955 (D1068): the reception mobile's login is admitted unless the setting says 0
KIT_S955 = "S955_RECEPTION_CONSOLE"
SECTION_ORDER = ("due today", "grace period", "actionable missed follow-up", "probable dropout", "procedure call-back")
ROWS_MAX = 150                 # rows drawn per tab (the count is always the whole)
FIG = "verdict"

CC = None                      # calls_console, handed in by register()
_CFG = None
_OFFERED = {}                  # phone -> when a list last showed it
_REBUILT = [0.0]               # when the call route last re-read the lists on this worker (at most once a minute)
REBUILD_GAP_S = 60


# ---------------------------------------------------------------------------------------------- small helpers
def _cfg(key, default):
    try:
        return CC._cfg_path(key, default)
    except Exception:
        return default


def _hm_cfg(key, default):
    v = str(_cfg(key, default) or default).strip()
    try:
        return _dt.datetime.strptime(v, "%H:%M").time()
    except Exception:
        return _dt.datetime.strptime(default, "%H:%M").time()


def _float_cfg(key, default):
    try:
        return float(str(_cfg(key, str(default)) or default))
    except Exception:
        return default


def allowed_keys():
    """The card keys this page serves: the phone staff and the extra logins (first names, small letters)."""
    out = []
    for part in (str(_cfg("PORTAL_PHONE_STAFF", "shivani,alisha") or "") + "," +
                 str(_cfg("PORTAL_STAFF_CONSOLE_EXTRA", EXTRA_DEFAULT) or "")).split(","):
        k = re.sub(r"[^a-z]", "", part.strip().lower().split()[0]) if part.strip() else ""
        if k and k not in out and k not in CC.OWNER_FIRST:
            out.append(k)
    rec = reception_key()                              # S955 (D1068): the reception mobile's login
    if rec and rec not in out and rec not in CC.OWNER_FIRST and reception_on():
        out.append(rec)
    elif rec and rec in out and not reception_on() and is_reception(rec):
        out.remove(rec)                                # the switch off wins over EXTRA (a phone staff key is a person)
    return out


def reception_key():
    """S955: the reception mobile's card key -- its MyOperator agent's first name as calls_console reads it
    (PORTAL_RECEPTION_AGENT, default 'reception'), which is also its portal login. '' when it cannot be read."""
    try:
        v = str(_cfg("PORTAL_RECEPTION_AGENT", CC.RECEPTION_DEFAULT) or "").strip().lower() or CC.RECEPTION_DEFAULT
        return re.sub(r"[^a-z]", "", v.split()[0])
    except Exception:
        return ""


def reception_on():
    """S955: PORTAL_STAFF_CONSOLE_RECEPTION (default 1); "0" / "false" / "no" / "off" keeps the reception mobile off this page.
    Write it as a STRING in portal_config.py: the portal's own reader (portal._cfg_get) treats an int 0 / False as unset."""
    try:
        v = CC._CFG("PORTAL_STAFF_CONSOLE_RECEPTION", None) if CC._CFG else None
    except Exception:
        v = None
    if v is None or str(v).strip() == "":
        v = RECEPTION_ON_DEFAULT
    return str(v).strip().lower() not in ("0", "false", "no", "off")


def is_reception(key):
    """S955: this card key is the reception mobile -- and not one of the phone staff (calls_console's own rule)."""
    phone = [re.sub(r"[^a-z]", "", p.strip().lower().split()[0]) for p in str(_cfg("PORTAL_PHONE_STAFF", "shivani,alisha") or "").split(",") if p.strip()]
    return bool(key) and key == reception_key() and key not in phone


def reception_calls(conn, now):
    """S955: today's calls on the reception mobile exactly as the owner's page reads them -- every card's calls marked
    'reception mobile' (credited to the one phone staff member on duty, or kept on the Reception mobile card), each once,
    newest first. None when the cards cannot be made. Read-only."""
    d_from, d_to, _m = CC.span_bounds("today", "", now)
    L = CC.wa_load(conn, d_from, d_to, now, CC._cfg_path("PORTAL_INBOX_DB", CC.INBOX_DB_DEFAULT))
    people, _i, _n = CC.build_people(conn, d_from, d_to, now, wa=L["span"], ctx=L["ctx"], dz=L["dz"])
    cards = CC._safe_cards(conn, people, d_from, d_to, now, CC._cfg_path("SR_STAFF_MASTER", CC.STAFF_MASTER_DEFAULT),
                           CC._cfg_path("SR_PUNCH_CSV", CC.PUNCH_CSV_DEFAULT))
    if cards is None:
        return None
    seen, rows = set(), []
    for c in cards:
        if c.get("both"):
            continue
        for r in CC.card_json(c).get("calls") or []:
            if r.get("rec") and r.get("ref") not in seen:
                seen.add(r.get("ref"))
                rows.append(r)
    return sorted(rows, key=lambda r: r["sort"], reverse=True)


def section_rank(section, sent_back=False):
    if sent_back:
        return 0
    s = str(section or "").split("·")[0].strip().lower()
    if "doctor" in s or "sent back" in s:
        return 0
    for i, name in enumerate(SECTION_ORDER):
        if s == name:
            return i + 1
    return len(SECTION_ORDER) + 1


def section_label(r):
    s = str(r.get("section") or "").split("·")[0].strip()
    if s:
        return s
    return {"today": "Due Today", "grace": "Grace Period"}.get(CC.fu_band(r.get("age", 0)), "Overdue")


def _plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def _att_word(it):
    """What one unanswered attempt came to: the phone never rang -> Switched off; else No answer."""
    return "Switched off" if (not it.get("answered") and int(it.get("ring") or 0) <= 0) else "No answer"


def _dur_words(dur_h):
    """'3:12' -> '3 min 12 s' (the screens' words)."""
    m = re.match(r"^(\d+):(\d\d)$", str(dur_h or ""))
    if not m:
        return ""
    mi, se = int(m.group(1)), int(m.group(2))
    return ("%d min %02d s" % (mi, se)) if mi else ("%d s" % se)


def _day_h(iso):
    try:
        return _dt.date.fromisoformat(str(iso or "")[:10]).strftime("%d-%b")
    except Exception:
        return ""


def _pats(conn):
    out = {}
    try:
        for r in conn.execute(CC._PAT_SQL):
            out[r[0]] = {"name": (r[1] or "").strip(), "dx": (r[2] or "").strip(), "cid": (r[5] or "").strip(),
                         "last_visit": (r[6] or "").strip()}
    except Exception:
        pass
    return out


def _sent_back_phones():
    """The numbers the doctor sent back to staff (the old console's open send-backs), first in the calling order."""
    try:
        _disp, sb = CC._H["reviews_maps"]() if CC._H.get("reviews_maps") else ({}, {})
    except Exception:
        return set()
    out = set()
    for jk in (sb or {}):
        m = CC._JK.match(jk or "")
        if m:
            out.add(m.group(1))
    return out


# ---------------------------------------------------------------------------------------------- the lists
def build_lists(conn, key, now=None, inbox_path=None, fin_db=None):
    """Everything the page shows, for the card key `key` (her own Handled today). Read-only. Never raises past the
    caller: a part that cannot be made says so in its own tab ("failed")."""
    now = CC.now_ist(now)
    today = now.date()
    d = today.isoformat()
    ev_from = _dt.datetime.combine(today, _hm_cfg("PORTAL_STAFF_EVENING_FROM", EVENING_FROM_DEFAULT))
    ev_to = _dt.datetime.combine(today, _hm_cfg("PORTAL_STAFF_EVENING_TO", EVENING_TO_DEFAULT))
    again_h = _float_cfg("PORTAL_STAFF_CALL_AGAIN_H", CALL_AGAIN_H_DEFAULT)
    evening = now >= ev_from
    cut = time.time() - OFFER_KEEP_S
    for k_ in [k_ for k_, v_ in _OFFERED.items() if v_ < cut]:
        _OFFERED.pop(k_, None)                           # the call route's memory holds the last hour only
    out = {"kit": VERSION, "key": key, "now": now.strftime("%Y-%m-%d %H:%M"), "evening": evening,
           "ev_from_h": ev_from.strftime("%-I %p").lower().replace(" ", ""), "ev_to_h": ev_to.strftime("%-I %p").lower().replace(" ", ""),
           "tabs": {}, "fu_ok": True, "wa_ok": True, "card_ok": True}
    L = CC.wa_load(conn, d, d, now, inbox_path)
    people, _items, _nn = CC.build_people(conn, d, d, now, wa=L["span"], ctx=L["ctx"], dz=L["dz"])
    pats = _pats(conn)
    byp = {p["phone"]: p for p in people}
    mids = {}
    for w in L.get("all") or []:
        if w.get("mid"):
            mids[w["phone"]] = w["mid"]            # the newest message of the number (the list is in time order)
    sent_back = _sent_back_phones()

    def calls_of(ph):
        p = byp.get(ph)
        return [x for x in (p["calls"] if p else []) if x.get("ch") != "wa"], p

    def row(ph, name, unknown, sub, hi=False, kind="", sort=None, dx=""):
        if ph:
            _OFFERED[ph] = time.time()
        return {"phone": ph, "phone_h": CC.fmt_num(ph), "name": name or ("New number" if unknown else "Patient"),
                "sub": sub, "hi": bool(hi), "kind": kind, "mid": mids.get(ph, ""), "sort": sort or "", "dx": dx}

    due, again, eve, missed = [], [], [], []

    # -- the missed-call path (it wins over the follow-up path for the same number)
    missed_phones = set()
    for p in people:
        if p.get("spam") or p.get("not_patient") or not p["phone"]:
            continue
        calls = [x for x in p["calls"] if x.get("ch") != "wa"]
        misses = [x for x in calls if x["kind"] == "in_miss"]
        if not misses:
            continue
        ans_t = [x["t"] for x in calls if x["answered"] and x["t"] is not None]
        last_ans = max(ans_t) if ans_t else None
        open_ = [m for m in misses if last_ans is None or (m["t"] is not None and m["t"] > last_ans)]
        missed_phones.add(p["phone"])
        if not open_:
            continue                                     # reached after the missed call: off every list
        first = open_[0]
        if first["t"] is not None and any(x.get("kind") == "wa_in" and x.get("t") is not None and x["t"] > first["t"] for x in p["calls"]):
            continue                                     # he wrote after the missed call: the WhatsApp tab has him
        atts = [x for x in calls if x["direction"] == "Out" and not x["answered"] and x["t"] is not None
                and first["t"] is not None and x["t"] > first["t"]]
        n = len(atts)
        pt = pats.get(p["phone"]) or {}
        name = p["name"] or pt.get("name", "")
        unknown = p["unknown"]
        dx = p.get("dx") or pt.get("dx", "")
        times = ", ".join(m["t_h"] for m in open_ if m["t_h"])
        head = ("Incoming missed (%s)" % times) if len(open_) == 1 else ("Incoming missed %d (%s)" % (len(open_), times))
        tail = "not an existing patient" if unknown else dx
        if n == 0:
            wait = CC.wait_words(CC.wait_h(first["t"], now)) if first["t"] is not None else ""
            sub = " · ".join(x for x in (head, wait if len(open_) == 1 else "", tail) if x)
            missed.append(row(p["phone"], name, unknown, sub, hi=True, kind="missed",
                              sort=first["t"].strftime("%H:%M:%S") if first["t"] else "", dx=dx))
        elif n == 1:
            a = atts[0]
            due_t = a["t"] + _dt.timedelta(hours=again_h)
            sub = "%s · call back %s %s" % (head, a["t_h"], _att_word(a))
            again.append(row(p["phone"], name, unknown, sub, hi=(now >= due_t), kind="missed",
                             sort=due_t.strftime("%H:%M:%S"), dx=dx))
        elif n < MAX_TRIES:
            sub = "%s · 2 attempts (%s) · last attempt today" % (head, ", ".join(a["t_h"] for a in atts))
            eve.append(row(p["phone"], name, unknown, sub, hi=evening, kind="missed",
                           sort="0" + atts[-1]["t"].strftime("%H:%M:%S"), dx=dx))

    # -- S951_YESTERDAY_CARRY (the parent, S517, 25-Nov-2026; D1063 his "yes" 20:43 24-Nov, widened by his word 10:02 IST
    # 25-Nov): EVERY missed call of yesterday still unresolved comes onto today's lists, on the missed-call path.
    # Unresolved = no connected call after it (that day or today), no WhatsApp from him after it (the WhatsApp tab has
    # him then), and no Docterz visit from yesterday on (finance.db patient_visit, read-only, by clinic ID or by the
    # mobile's fingerprint -- a patient on another mobile is caught once Docterz holds that mobile). Today is a fresh day
    # for tries: none -> Incoming missed, one -> Call again, two -> Evening calls, a third ends it; yesterday's tries are
    # said on the line. A miss from 21:00 on (PORTAL_STAFF_AFTER_HOURS_FROM) reads "Missed after hours", any other
    # "Missed yesterday, not reached". Today's own missed call for the number wins (that row already stands). Read-only;
    # a fault here costs the carry only ("carry_ok": False), never the page.
    out["carry_ok"], out["carry_visits_ok"] = True, None
    try:
        yday = today - _dt.timedelta(days=1)
        y = yday.isoformat()
        ah_from = _dt.datetime.combine(yday, _hm_cfg("PORTAL_STAFF_AFTER_HOURS_FROM", AFTER_HOURS_FROM_DEFAULT))
        Ly = CC.wa_load(conn, y, y, now, inbox_path)
        people_y, _iy, _ny = CC.build_people(conn, y, y, now, wa=Ly["span"], ctx=Ly["ctx"], dz=Ly["dz"])
        cand = []
        for py in people_y:
            ph = py.get("phone") or ""
            if py.get("spam") or py.get("not_patient") or not ph or ph in missed_phones:
                continue
            p_t = byp.get(ph)
            if p_t is not None and (p_t.get("spam") or p_t.get("not_patient")):
                continue
            ycalls = [x for x in py["calls"] if x.get("ch") != "wa"]
            ymiss = sorted((x for x in ycalls if x["kind"] == "in_miss" and x["t"] is not None), key=lambda x: x["t"])
            if not ymiss:
                continue
            yans = [x["t"] for x in ycalls if x["answered"] and x["t"] is not None]
            last_ans = max(yans) if yans else None
            open_ = [m for m in ymiss if last_ans is None or m["t"] > last_ans]
            if not open_:
                continue                                 # reached after it the same day
            first = open_[0]
            if any(x.get("kind") == "wa_in" and x.get("t") is not None and x["t"] > first["t"] for x in py["calls"]):
                continue                                 # he wrote after the missed call: the WhatsApp tab has him
            tcalls = [x for x in (p_t["calls"] if p_t else []) if x.get("ch") != "wa"]
            if any(x["answered"] for x in tcalls):
                continue                                 # reached today: off the lists by himself
            if p_t is not None and any(x.get("kind") == "wa_in" for x in p_t["calls"]):
                continue                                 # he wrote today: the WhatsApp tab has him
            cand.append((py, ph, ycalls, open_, first, tcalls))
        visits, R = {"ok": False, "by_id": {}, "by_fp": {}}, None
        if cand:
            try:
                R = CC._ro()
                visits = R.visits_since(y, today, fin_db)
            except Exception:
                R, visits = None, {"ok": False, "by_id": {}, "by_fp": {}}
            thr = visits.get("through")
            out["carry_visits_ok"] = bool(visits.get("ok") and thr is not None and thr >= yday)   # yesterday's export in
        ids_n = {}
        for k_, v_ in (visits.get("by_id") or {}).items():
            ids_n.setdefault(CC._cid_key(k_), []).extend(v_)
        for py, ph, ycalls, open_, first, tcalls in cand:
            pt = pats.get(ph) or {}
            cid = CC._cid_key(py.get("cid") or pt.get("cid") or "")
            came = bool(cid and any(d >= yday for d in ids_n.get(cid, ())))
            if not came and R is not None and visits.get("ok"):
                try:
                    fp = R._mobile_fp(ph)
                except Exception:
                    fp = ""
                came = bool(fp and any(d >= yday for d, _c in visits["by_fp"].get(fp, ())))
            if came:
                continue                                 # a Docterz visit since: resolved
            atts = sorted((x for x in tcalls if x["direction"] == "Out" and not x["answered"] and x["t"] is not None),
                          key=lambda x: x["t"])
            n = len(atts)
            if n >= MAX_TRIES:
                continue                                 # a third unanswered try today ends it (the follow-up path keeps him)
            missed_phones.add(ph)
            out["carry_n"] = out.get("carry_n", 0) + 1
            ytries = sum(1 for x in ycalls if x["direction"] == "Out" and not x["answered"] and x["t"] is not None
                         and x["t"] > first["t"])
            name = py.get("name") or pt.get("name", "")
            unknown = py.get("unknown")
            dx = py.get("dx") or pt.get("dx", "")
            times = ", ".join(m["t_h"] for m in open_ if m["t_h"])
            word = "Missed after hours" if all(m["t"] >= ah_from for m in open_) else "Missed yesterday, not reached"
            head = ("%s (%s)" % (word, times)) if len(open_) == 1 else ("%s %d (%s)" % (word, len(open_), times))
            bits = [head]
            if ytries:
                bits.append("tried %d time%s yesterday" % (ytries, "" if ytries == 1 else "s"))
            tail = "new number - may be a patient on another mobile" if unknown else dx
            if n == 0:
                if len(open_) == 1:
                    bits.append(CC.wait_words(CC.wait_h(first["t"], now)))
                bits.append(tail)
                missed.append(row(ph, name, unknown, " · ".join(b for b in bits if b), hi=True, kind="missed",
                                  sort=" " + first["t"].strftime("%H:%M:%S"), dx=dx))
            elif n == 1:
                a = atts[0]
                due_t = a["t"] + _dt.timedelta(hours=again_h)
                bits += ["call back %s %s" % (a["t_h"], _att_word(a)), tail]
                again.append(row(ph, name, unknown, " · ".join(b for b in bits if b), hi=(now >= due_t), kind="missed",
                                 sort=due_t.strftime("%H:%M:%S"), dx=dx))
            else:
                bits += ["2 attempts (%s) · last attempt today" % ", ".join(a["t_h"] for a in atts), tail]
                eve.append(row(ph, name, unknown, " · ".join(b for b in bits if b), hi=evening, kind="missed",
                               sort="0" + atts[-1]["t"].strftime("%H:%M:%S"), dx=dx))
    except Exception as _e_s951:                                 # noqa: BLE001
        out["carry_ok"] = False
        print("calls_staff: the yesterday carry failed: %r" % (_e_s951,), file=sys.stderr)

    # -- the follow-up path
    try:
        fu = CC.followup_list(conn, now, fin_db=fin_db, inbox_path=inbox_path)
    except Exception:
        fu = {"found": False, "bands": []}
    out["fu_ok"] = bool(fu.get("found"))
    fu_phones = set()
    seen_rows = set()
    for band in fu.get("bands") or []:
        for r in band[3]:
            ph = r.get("phone") or ""
            g = ph or ("n:" + (r.get("name") or "").lower())
            if g in seen_rows:
                continue
            seen_rows.add(g)
            if ph:
                fu_phones.add(ph)
            if ph in missed_phones:
                continue
            calls, p = calls_of(ph) if ph else ([], None)
            if any(x["answered"] for x in calls):
                continue                                 # reached today: off the lists by himself
            if p is not None and any(x.get("kind") == "wa_in" for x in p["calls"]):
                continue                                 # he wrote today: the WhatsApp tab has him
            atts = [x for x in calls if x["direction"] == "Out" and not x["answered"]]
            n = len(atts)
            pt = pats.get(ph) or {}
            name = r.get("name") or pt.get("name", "")
            dx = r.get("dx") or pt.get("dx", "")
            lab = section_label(r)
            age = int(r.get("age") or 0)
            rank = section_rank(r.get("section"), ph in sent_back)
            srt = "%d %s %s" % (rank, r["dd"].isoformat() if r.get("dd") else "", name.lower())
            if n == 0:
                bits = [lab if rank else "Sent back by doctor · " + lab]
                if age > 0:
                    bits.append(_plural(age, "day"))
                if dx:
                    bits.append(dx)
                lv = _day_h(pt.get("last_visit"))
                if lv and age <= 0:
                    bits.append("last visit " + lv)
                if not ph:
                    bits.append("no mobile on the list")
                sub = " · ".join(bits)
                rr = row(ph, name, False, sub, kind="fu", sort=srt, dx=dx)
                if evening and CC.fu_band(age) == "grace":
                    eve.append(dict(rr, sort="1" + srt))
                else:
                    due.append(rr)
            elif n == 1:
                a = atts[0]
                due_t = a["t"] + _dt.timedelta(hours=again_h) if a["t"] else now
                sub = "1 attempt · %s %s · follow-up" % (a["t_h"], _att_word(a))
                again.append(row(ph, name, False, sub, hi=(now >= due_t), kind="fu", sort=due_t.strftime("%H:%M:%S"), dx=dx))
            elif n < MAX_TRIES:
                sub = "2 attempts (%s) · last attempt today" % ", ".join(a["t_h"] for a in atts)
                eve.append(row(ph, name, False, sub, hi=evening, kind="fu",
                               sort="0" + (atts[-1]["t"].strftime("%H:%M:%S") if atts[-1]["t"] else ""), dx=dx))

    due.sort(key=lambda x: x["sort"])
    again.sort(key=lambda x: (not x["hi"], x["sort"]))
    eve.sort(key=lambda x: x["sort"])
    missed.sort(key=lambda x: x["sort"])

    # -- WhatsApp: the chats awaiting a reply (the owner's rule)
    wa_rows = []
    try:
        aw = CC.wa_awaiting(conn, L, now)
    except Exception:
        aw = {"failed": True}
    if aw.get("failed") or not L.get("ok"):
        out["wa_ok"] = False
    for c in aw.get("chats") or []:
        pt = pats.get(c["phone"]) or {}
        known = bool(c.get("name") or c.get("cid") or pt)
        dx = pt.get("dx", "")
        sub = " · ".join(x for x in (c.get("last_h", ""), "existing patient" if known else "not an existing patient", dx,
                                         "waiting " + c.get("wait_h", "")) if x)
        rr = row(c["phone"], c.get("name") or pt.get("name", ""), not known, sub, hi=(c.get("tone") == "rose"), kind="wa", dx=dx)
        rr["mid"] = c.get("mid") or rr["mid"]
        rr["msg"] = " · ".join(x for x in (c.get("media", ""), (u"“" + c["text"] + u"”") if c.get("text") else "") if x)
        rr["n"] = c.get("n", 1)
        wa_rows.append(rr)

    # -- Handled today: her own calls
    mine = []
    rec_view = is_reception(key)                       # S955: the reception mobile's own calls, whoever was credited
    try:
        if rec_view:
            rc = reception_calls(conn, now)
            out["card_ok"] = rc is not None
            cj = {"calls": rc or [], "disputes": []}
        else:
            c, _handler, _mode, made = CC.card_for(conn, key, "today", now=now)
            out["card_ok"] = bool(made)
            cj = CC.card_json(c) if c else {"calls": [], "disputes": []}
    except Exception:
        out["card_ok"], cj = False, {"calls": [], "disputes": []}
    if rec_view:
        out["reception"] = True
    asked, open_ref = {}, set()
    for x in cj.get("disputes") or []:
        if x.get("fig") == FIG:
            asked[x.get("ref")] = x
        if not x.get("answer"):
            open_ref.add(x.get("ref"))                   # any open dispute on the call: one at a time, as the store's own rule
    for r in cj.get("calls") or []:
        if r["kind"] not in ("in_ok", "out_ok"):
            continue                                     # handled = spoken to; an unanswered attempt shows in Call again
        how = "incoming" if r["kind"] == "in_ok" else ("follow-up" if r["phone"] in fu_phones else "outgoing")
        bits = [r["t"], _dur_words(r["dur"]), how]
        pt = pats.get(r["phone"]) or {}
        d_ = asked.get(r["ref"])
        st = ""
        if d_ is not None:
            st = {"accept": "Doctor agreed: the verdict was wrong", "stands": "Doctor: the verdict stands"}.get(
                d_.get("answer") or "", "Sent to the doctor")
        mine.append({"ref": r["ref"], "phone": r["phone"], "phone_h": CC.fmt_num(r["phone"]),
                     "name": r["name"] or pt.get("name") or ("Patient" if pt else "New number"),
                     "sub": " · ".join(x for x in bits if x),
                     "verdict": (r["ai"][:1].upper() + r["ai"][1:]) if r["ai"] else "",
                     "can_dispute": bool(r["ai"]) and d_ is None and r["ref"] not in open_ref and not rec_view,
                     "disputed": st, "jk": r["jk"] if (r["has_rec"] and not rec_view) else "", "sort": r["sort"]})

    m = CC.read_meta(now)
    out["built_h"] = m["built"].strftime("%H:%M") if m.get("built") else ""
    out["age_min"] = m.get("age")
    out["old"] = bool(m.get("built")) and m.get("in_window") and (m.get("age") is None or m["age"] > STALE_MIN)
    out["tabs"] = {"due": due, "again": again, "eve": eve, "missed": missed, "wa": wa_rows, "mine": mine}
    out["counts"] = {k: len(v) for k, v in out["tabs"].items()}
    return out


# ---------------------------------------------------------------------------------------------- the page
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Call Console · {{ who_h }}</title>
<style>
body{margin:0;background:#f2f4f7;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans Devanagari",sans-serif;color:#14202e}
.wrap{max-width:720px;margin:0 auto;background:#f7f8fa;min-height:100vh}
.bar{background:#1d4f91;color:#fff;padding:10px 14px;font-size:16px;font-weight:600;display:flex;justify-content:space-between;align-items:center;gap:8px;position:sticky;top:0;z-index:2}
.bar a{color:#dfe8f4;font-size:13px;font-weight:500;text-decoration:none}
.upd{font-size:12px;font-weight:500;color:#dfe8f4}
.updold{font-size:12px;font-weight:600;color:#5a3700;background:#ffd98a;border-radius:6px;padding:2px 6px}
.tabs{display:flex;gap:6px;padding:8px 10px;background:#e8edf4;flex-wrap:wrap;position:sticky;top:44px;z-index:1}
.tab{font-size:14px;padding:7px 12px;border-radius:16px;background:#fff;color:#2b3643;border:0;font-family:inherit;min-height:36px;cursor:pointer}
.tab[aria-selected=true]{background:#1d4f91;color:#fff;font-weight:600}
.sec{font-size:13px;font-weight:700;color:#4a5563;padding:10px 12px 4px;margin:0}
.pt{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid #e3e7ec;background:#fff}
.pt.hi{background:#fff7e6}
.pn{font-size:15px;font-weight:600;margin:0}
.ps{font-size:13px;color:#4f5967;margin:2px 0 0}
.ai{font-size:13px;margin:4px 0 0}
.msg{font-size:14px;background:#fff;border:1px solid #d9dee5;border-radius:10px;padding:8px 10px;margin:6px 0 0}
.btns{display:flex;gap:6px;flex-shrink:0}
.bcall{font-size:14px;font-weight:600;color:#fff;background:#1f7a3a;border:0;border-radius:8px;padding:0 14px;min-height:44px;font-family:inherit;cursor:pointer}
.bcall:disabled{background:#8aa596}
.bwa{font-size:14px;font-weight:600;color:#1f6a33;background:#fff;border:1px solid #1f7a3a;border-radius:8px;padding:0 12px;min-height:44px;font-family:inherit;display:inline-flex;align-items:center;text-decoration:none;cursor:pointer}
.bsm{font-size:12px;font-weight:600;color:#8a2a00;background:#fff;border:1px solid #b8582a;border-radius:6px;padding:3px 8px;font-family:inherit;cursor:pointer}
.foot{font-size:12px;color:#4f5967;padding:8px 12px}
.empty{font-size:15px;color:#1f6a33;padding:18px 12px;background:#fff}
.warn{font-size:13px;color:#5a3700;background:#fff3d6;padding:8px 12px}
.toast{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:#14202e;color:#fff;padding:10px 14px;border-radius:10px;font-size:14px;max-width:92%;display:none;z-index:3}
.dq{display:none;margin-top:6px;gap:6px}
.dq input{flex:1;font-size:14px;padding:8px;border:1px solid #c9d0d9;border-radius:8px;font-family:inherit;min-height:28px}
audio{width:100%;margin-top:6px}
.pick{padding:16px;display:flex;flex-direction:column;gap:10px}
.pick a{background:#fff;border:1px solid #d9dee5;border-radius:10px;padding:14px;color:#1d4f91;font-weight:600;text-decoration:none}
</style></head><body><div class="wrap">
{% if picker %}
<div class="bar"><span>Staff Call Console</span><a href="/portal/console">Your console</a></div>
<div class="pick"><p class="ps">See the page as each person sees it:</p>
{% for k in picker %}<a href="/portal/console/staff?as={{ k }}">{{ k|title }}</a>{% endfor %}</div>
{% else %}
<div class="bar"><span>Call Console · {{ who_h }}</span>{% if d.old %}<span class="updold">updated {{ d.built_h }} · {{ d.age_min }} min ago</span>{% elif d.built_h %}<span class="upd">updated {{ d.built_h }}</span>{% else %}<span class="updold">not read yet</span>{% endif %}</div>
{% if as_view %}<div class="warn">You are seeing {{ who_h }}'s page. Call rings your own phone.</div>{% endif %}
<div class="tabs" role="tablist">
{% for t in tabs %}<button type="button" class="tab" role="tab" id="t-{{ t.k }}" aria-controls="p-{{ t.k }}" aria-selected="{{ 'true' if loop.first else 'false' }}" onclick="tab('{{ t.k }}')">{{ t.label }}{% if t.show %} {{ t.n }}{% endif %}</button>{% endfor %}
</div>
{% for t in tabs %}<section id="p-{{ t.k }}" role="tabpanel" aria-labelledby="t-{{ t.k }}"{% if not loop.first %} hidden{% endif %}>
{% if t.title %}<p class="sec">{{ t.title }}</p>{% endif %}
{% if t.warn %}<div class="warn">{{ t.warn }}</div>{% endif %}
{% for r in t.rows[:rows_max] %}
<div class="pt{% if r.hi %} hi{% endif %}"><div style="min-width:0;flex:1">
<p class="pn">{{ r.name }} · {{ r.phone_h }}</p><p class="ps">{{ r.sub }}</p>
{% if r.msg %}<div class="msg">{{ r.msg }}</div>{% endif %}
{% if t.k == 'mine' %}{% if r.verdict %}<p class="ai">Call verdict: {{ r.verdict }}{% if r.can_dispute and can_dispute %} <button type="button" class="bsm" onclick="dOpen(this)">Wrong?</button>{% endif %}{% if r.disputed %} · <i>{{ r.disputed }}</i>{% endif %}</p>
<div class="dq" data-ref="{{ r.ref }}"><input type="text" maxlength="300" placeholder="What is wrong?" aria-label="What is wrong with the call verdict"><button type="button" class="bsm" onclick="dSend(this)">Send</button></div>{% endif %}
<div class="rec" data-jk="{{ r.jk }}"></div>{% endif %}
</div><div class="btns">
{% if t.k == 'mine' %}{% if r.jk and can_rec %}<button type="button" class="bwa" onclick="play(this)">Recording</button>{% endif %}
{% else %}{% if r.phone %}<button type="button" class="bcall" data-ph="{{ r.phone }}" onclick="call(this)">Call</button>{% endif %}
{% if wa_ok_user and r.mid %}<a class="bwa" href="/portal/inbox?m={{ r.mid|urlencode }}">{{ 'Reply' if t.k == 'wa' else 'Chat' }}</a>{% endif %}{% endif %}
</div></div>
{% endfor %}
{% if t.rows|length > rows_max %}<div class="foot">… {{ t.rows|length - rows_max }} more</div>{% endif %}
{% if not t.rows and not t.warn %}<div class="empty">{{ t.empty }}</div>{% endif %}
{% if t.foot %}<div class="foot">{{ t.foot }}</div>{% endif %}
</section>{% endfor %}
{% endif %}
<div class="toast" id="toast" role="status" aria-live="polite"></div>
</div>
<script>
(function(){
var H={"Content-Type":"application/json","X-Staff-Console":"1"};
function toast(s){var t=document.getElementById("toast");t.textContent=s;t.style.display="block";clearTimeout(t._h);t._h=setTimeout(function(){t.style.display="none";},6000);}
window.tab=function(k){var b=document.querySelectorAll(".tab");for(var i=0;i<b.length;i++){var on=b[i].id==="t-"+k;b[i].setAttribute("aria-selected",on?"true":"false");document.getElementById("p-"+b[i].id.slice(2)).hidden=!on;}try{sessionStorage.setItem("s948tab",k);}catch(e){}};
try{var k0=null,q=0;try{k0=new URLSearchParams(location.search).get("tab");q=!!k0;}catch(e){}if(!k0||!document.getElementById("t-"+k0))k0=sessionStorage.getItem("s948tab");if(k0&&document.getElementById("t-"+k0))tab(k0);if(q&&history.replaceState)history.replaceState(null,"",location.pathname);}catch(e){}
window.call=function(b){b.disabled=true;fetch("/portal/console/staff/api/call",{method:"POST",headers:H,body:JSON.stringify({phone10:b.dataset.ph}),credentials:"same-origin"}).then(function(r){return r.json();}).then(function(j){toast(j.msg||"");}).catch(function(){toast("Not sent - check the connection and try again.");}).then(function(){setTimeout(function(){b.disabled=false;},5000);});};
window.play=function(b){var row=b.closest(".pt");var box=row.querySelector(".rec");if(box.firstChild){box.textContent="";return;}var a=document.createElement("audio");a.controls=true;a.preload="none";a.src="/portal/console/api/myrec/"+encodeURIComponent(box.dataset.jk);box.appendChild(a);a.play().catch(function(){});};
window.dOpen=function(b){var q=b.closest(".pt").querySelector(".dq");q.style.display="flex";q.querySelector("input").focus();};
window.dSend=function(b){var q=b.closest(".dq");var tx=q.querySelector("input").value.trim();if(!tx){toast("Write what is wrong first.");return;}b.disabled=true;
fetch("/portal/console/staff/api/dispute",{method:"POST",headers:H,body:JSON.stringify({ref:q.dataset.ref,text:tx}),credentials:"same-origin"}).then(function(r){return r.json();}).then(function(j){toast(j.msg||"");if(j.ok){q.style.display="none";var w=q.parentNode.querySelector(".bsm");if(w)w.remove();}else{b.disabled=false;}}).catch(function(){b.disabled=false;toast("Not sent - try again.");});};
setInterval(function(){if(document.hidden)return;var a=document.querySelector("audio");if(a&&!a.paused)return;if(document.activeElement&&document.activeElement.tagName==="INPUT")return;location.reload();},300000);
})();
</script></body></html>"""


def page_tabs(d):
    c = d["counts"]
    ev = "Evening calls" if d["evening"] else "Evening calls (from %s)" % d["ev_from_h"]
    fu_warn = "" if d["fu_ok"] else "The follow-up list could not be read just now - use the Callback Tracker for follow-ups."
    wa_warn = "" if d["wa_ok"] else "The WhatsApp chats could not be read just now - open the WhatsApp Inbox."
    card_warn = "" if d["card_ok"] else "Your calls could not be read just now - try again in a few minutes."
    clear = "All clear — no callbacks pending."
    if d.get("carry_ok") is False:                    # S951: said, never silent
        missed_warn = "Yesterday's missed calls could not be read just now - try again in a few minutes."
    elif d.get("carry_visits_ok") is False and d.get("carry_n"):    # only when a carried row is on the lists
        missed_warn = "Docterz visits are not up to date - a caller from yesterday may already have come. Check before calling."
    else:
        missed_warn = ""
    return [
        {"k": "due", "label": "Follow-ups due", "n": c["due"], "show": True, "rows": d["tabs"]["due"], "title": "Today's follow-up calls",
         "warn": fu_warn, "empty": clear, "foot": "Answered calls leave this list by themselves"},
        {"k": "again", "label": "Call again", "n": c["again"], "show": True, "rows": d["tabs"]["again"], "title": "",
         "warn": "", "empty": clear, "foot": "Due 2 hours after the last attempt · the 3rd attempt is in Evening calls"},
        {"k": "eve", "label": "Evening calls", "n": c["eve"], "show": d["evening"], "rows": d["tabs"]["eve"],
         "title": "" if d["evening"] else "These are called from %s to %s" % (d["ev_from_h"], d["ev_to_h"]),
         "warn": "", "empty": clear, "foot": "Today's unanswered first, then Grace Period · a 3rd unanswered attempt ends the day"},
        {"k": "missed", "label": "Incoming missed", "n": c["missed"], "show": True, "rows": d["tabs"]["missed"],
         "title": "Needs a callback now", "warn": missed_warn, "empty": clear,
         "foot": "Spoken to either way → leaves this list by itself"},
        {"k": "wa", "label": "WhatsApp", "n": c["wa"], "show": True, "rows": d["tabs"]["wa"], "title": "Recent WhatsApp",
         "warn": wa_warn, "empty": "All clear — no WhatsApp waiting.", "foot": "A reply or a call — either one clears it"},
        {"k": "mine", "label": "Handled today", "n": c["mine"], "show": True, "rows": d["tabs"]["mine"], "title": "",
         "warn": card_warn,
         "empty": "No calls on the reception mobile yet today." if d.get("reception") else "No calls handled by you yet today.",
         "foot": "Calls on the reception mobile · no transcripts" if d.get("reception") else "Only your own calls · no transcripts"},
    ]


# ---------------------------------------------------------------------------------------------- the routes
def register(app, gate, who, cfg_get, cc, staff_gate, sso_user, pm):
    """Called from the END of calls_console.register(). Registers nothing when the staff gate or the signed-in user cannot
    be found (as calls_console's own staff routes)."""
    global CC, _CFG
    CC, _CFG = cc, cfg_get
    if not (callable(staff_gate) and callable(sso_user)):
        return False
    is_doctor = getattr(pm, "_is_doctor", None) if pm is not None else None
    is_wa_user = getattr(pm, "_is_wa_user", None) if pm is not None else None

    def _login():
        try:
            u = sso_user(request) or {}
        except Exception:
            u = {}
        return str(u.get("user") or "").strip()

    def _doc():
        try:
            return bool(callable(is_doctor) and is_doctor(request))
        except Exception:
            return False

    def _viewer():
        """(card key, as_view, doctor) for this request, or abort: 403 for a login this page is not for."""
        doc = _doc()
        if doc:
            as_ = CC.login_key(request.args.get("as") or "")
            if not as_:
                return "", False, True
            if as_ not in allowed_keys():
                abort(404)
            return as_, True, True
        key = CC.login_key(_login())
        if not key or key not in allowed_keys():
            abort(403)
        return key, False, False

    def _data(key):
        conn = CC._H["console_conn"]() if CC._H.get("console_conn") else None
        if conn is None:
            return None
        try:
            return build_lists(conn, key, inbox_path=_cfg("PORTAL_INBOX_DB", CC.INBOX_DB_DEFAULT), fin_db=_cfg("FINANCE_DB_PATH", None))
        finally:
            conn.close()

    @app.route("/portal/console/staff", endpoint="s948_staff_page")
    @staff_gate
    def _staff_page():
        key, as_view, doc = _viewer()
        if doc and not key:
            html = render_template_string(PAGE, picker=allowed_keys(), who_h="")
            resp = make_response(html, 200)
            resp.headers["Cache-Control"] = "no-store"
            return resp
        d = _data(key)
        if d is None:
            return make_response("The call list could not be read just now. Try again in a few minutes.", 503)
        try:
            wa_user = bool(callable(is_wa_user) and is_wa_user(request))
        except Exception:
            wa_user = False
        html = render_template_string(PAGE, picker=None, who_h=key.title(), d=d, tabs=page_tabs(d), rows_max=ROWS_MAX,
                                      as_view=as_view, can_dispute=not doc, can_rec=not doc, wa_ok_user=wa_user)
        resp = make_response(html, 200)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/console/staff/api/lists", endpoint="s948_staff_lists")
    @staff_gate
    def _staff_lists():
        key, _as_view, doc = _viewer()
        if doc and not key:
            return jsonify({"ok": True, "picker": allowed_keys()})
        d = _data(key)
        if d is None:
            return jsonify({"ok": False, "error": "no_console"}), 503
        d = dict(d, ok=True)
        resp = jsonify(d)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/console/staff/api/call", methods=["POST"], endpoint="s948_staff_call")
    @staff_gate
    def _staff_call():
        if request.headers.get("X-Staff-Console") != "1":
            return jsonify({"ok": False, "msg": "bad request"}), 400
        login = _login()
        if not _doc():
            key = CC.login_key(login)
            if not key or key not in allowed_keys():
                return jsonify({"ok": False, "msg": "This page is not open to your login."}), 403
        b = request.get_json(silent=True)
        b = b if isinstance(b, dict) else {}
        ph = re.sub(r"\D", "", str(b.get("phone10") or ""))
        t = _OFFERED.get(ph)
        if ph and (t is None or time.time() - t > OFFER_KEEP_S) and time.time() - _REBUILT[0] >= REBUILD_GAP_S:
            _REBUILT[0] = time.time()                    # another worker drew the page: read the lists here (once a minute)
            try:
                _data((allowed_keys() or [""])[0])
            except Exception:
                pass
            t = _OFFERED.get(ph)
        if not ph or t is None or time.time() - t > OFFER_KEEP_S:
            return jsonify({"ok": False, "msg": "This number is not on your lists now - reload the page."}), 409
        ok, msg, code = CC.ivr_call(ph, login, env_path=_cfg("PORTAL_WA_ENV", CC.WA_ENV_DEFAULT),
                                    call_url=_cfg("RING_CALL_URL", CC.CALL_URL_DEFAULT))
        return jsonify({"ok": ok, "msg": msg}), code

    @app.route("/portal/console/staff/api/dispute", methods=["POST"], endpoint="s948_staff_dispute")
    @staff_gate
    def _staff_dispute():
        if request.headers.get("X-Staff-Console") != "1":
            return jsonify({"ok": False, "msg": "bad request"}), 400
        login = _login()
        key = CC.login_key(login)
        if not login or not key or key in CC.OWNER_FIRST or key not in allowed_keys():
            return jsonify({"ok": False, "msg": "Only the person who handled the call can send this."}), 403
        b = request.get_json(silent=True)
        b = b if isinstance(b, dict) else {}
        ref = str(b.get("ref") or "")
        text = " ".join(str(b.get("text") or "").split())[:300]
        if not CC._REF.match(ref) or not text:
            return jsonify({"ok": False, "msg": "Write what is wrong, then send."}), 400
        conn = CC._H["console_conn"]() if CC._H.get("console_conn") else None
        if conn is None:
            return jsonify({"ok": False, "msg": "Not sent - try again in a few minutes."}), 503
        try:
            c, _h, _m, _made = CC.card_for(conn, key, "7")
        finally:
            conn.close()
        r = next((x for x in (CC.card_json(c)["calls"] if c else []) if x["ref"] == ref), None)
        if r is None or r["kind"] not in ("in_ok", "out_ok") or not r.get("ai"):
            return jsonify({"ok": False, "msg": "This call is not among your calls with a verdict - reload the page."}), 409
        rdb = _cfg("PORTAL_CALL_REVIEW_DB", CC.REVIEW_DB_DEFAULT)
        try:
            _st, ds, _ok = CC.rv_read(rdb)
        except Exception:
            ds = []
        if any(x.get("ref") == ref and x.get("staff") == key and (not x.get("answer") or x.get("fig") == FIG) for x in ds):
            return jsonify({"ok": False, "msg": "Already sent for this call - waiting for the doctor."}), 409
        call_h = " · ".join(x for x in ((r["day"][8:10] + "-" + r["day"][5:7] + " " + r["t"]) if r["day"] else r["t"],
                                            r["name"], r["cid"], CC.fmt_num(r["phone"]),
                                            "Call verdict: " + r["ai"]) if x)
        try:
            CC._rv_write(rdb, "INSERT INTO dispute (ref, staff, fig, text, call_h, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                         (ref, key, FIG, text, call_h, login, CC._stamp()))
        except Exception:
            return jsonify({"ok": False, "msg": "Not sent - try again."}), 503
        return jsonify({"ok": True, "msg": "Sent to the doctor."})

    # the tile, beside the owner's "Call Console" -- display only; granted by name in tile_grants.json
    try:
        tiles = getattr(pm, "TILES", None)
        if isinstance(tiles, list) and not any(t.get("name") == TILE_NAME for t in tiles):
            i = next((n for n, t in enumerate(tiles) if t.get("name") == TILE_AFTER), None)
            if i is not None:
                grp = tiles[i].get("group")
                tiles.insert(i + 1, {"icon": tiles[i].get("icon", "\U0001F3A7"), "name": TILE_NAME,
                                     "desc": "Follow-ups · call again · missed calls · WhatsApp", "live": True,
                                     "url": "/portal/console/staff", "roles": [], "group": grp})
                tg = getattr(pm, "_TILE_GROUP", None)
                if isinstance(tg, dict) and grp:
                    tg[TILE_NAME] = grp
    except Exception:
        pass
    return True
