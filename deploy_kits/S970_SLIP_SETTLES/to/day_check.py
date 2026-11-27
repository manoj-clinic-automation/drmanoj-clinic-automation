#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""day_check.py -- kit S636_DAY_CHECK (session S347, 24-Oct-2026; D776 stage 1; F-1017, F-1018). PARENT.
Mounted by clinic_register.init() and lives beside it. Flask and the standard library only.

THE OWNER, 23/24-Oct-2026 (D776): "It should analyse properly, give the missing money details, and Docterz and parchi
required corrections ... for shivani alisha, shavez and myself, becomes available as soon as the morning entry is done,
and the Docterz differs becomes a clickable button" · "All 3 should be able to do Docterz corrections" ·
"1300 not billed - means Docterz entry is missing" · "is clarity here better ?" · "Here we also write which ones ?"

WHAT IT DOES. One day, patient by patient, across four records:
    the parchi    (slip / slip_item -- what was DONE)
    Docterz       (clinic_day_line / clinic_day_tender -- what was BILLED)
    the register  (clinic_register_day -- what was COLLECTED, section x cash/UPI/card; counted from the handwritten book:
                   THE REFEREE, his fact of 24-Oct)
    the bank      (upi_txn -- UPI, when the statement arrives)
and it names every correction as one line, with the buttons of the person who makes it:
    Docterz (Shivani, Alisha, Shavez):  Rs X -- Docterz entry missing      [Added] [Not paid] [Free]
                                        Payment mode wrong                 [Changed] [Not right]
                                        Rs X -- patient not found          [Found it]
    Parchi (Shavez):                    [Fix] (opens the parchi again, its number and day filled) · [Remove duplicate]
The rule (the owner's, S343): register = Docterz != parchi -> the parchi is wrong; register = parchi != Docterz -> Docterz
is short; nothing explains it -> check by hand.

IT IS WORKED OUT EVERY TIME IT IS READ. Nothing is computed ahead and stored: the register's Save, a Docterz re-export
(docterz_ingest.upsert_lines replaces the day wholesale) or a corrected parchi changes the answer the next time the page
or the owner's line is read. A TICK IS STORED, NEVER TAKEN AS PROOF: a line clears only when the next export or the
parchi shows it. "Free" and "Not paid" are the existing chhoot / radd entries of slip_adjust.py (his Approve / Reject).

ONE TABLE OF ITS OWN, created on first request (F-303):
    day_check_tick  id, day, key, act, reason, pick, who, at, state (live | undone)
It reads clinic_day_line, clinic_day_tender, clinic_day_revenue, clinic_register_day, upi_txn, slip, slip_item,
slip_adjust; it writes slip / slip_item / slip_adjust only through the three parchi buttons (Fix, Remove duplicate,
Fix the ID) and slip_adjust's own add_discount / add_cancel, every write audited.
No patient name, no number, no secret in this file (F-185).

S962 (session S529, 26-Nov-2026; D1080, the Morning Match kit C part 1; F-1678, F-1679) -- his ok of 12:58 on the
mock-up v2.1: a radd after billing is MATCHED both ways (Docterz kept the bill: 'billed . refunded' / 'billed . money
never taken'; Docterz cancelled it too: 'cancelled . refunded') -- never a false parchi card, never subtracted twice;
a slip whose patient Docterz does not carry goes to HIS back-date list by itself (no 'Added' for any staff login --
only his login can back-date); the staff see that list with 'Paise liye hi nahi' (nid_mark 'free', theirs) and
'Dr sahab ko yaad dilayein' (a push to his login, once in three hours); the day in one line on top (register = Docterz
+ slips not in Docterz - refunded / never taken + not explained); his console line reads '<day>: all matched' or the
counts. A staff 'free' answer is named as theirs, never as his.
"""
import datetime as dt
import os

from flask import Blueprint, redirect, request

bp = Blueprint("day_check", __name__)
_db = _require = _audit = None
UNIT = "clinic"
SLIP_UNIT = "slips"
_done = False

DOCTERZ_USERS = ("shivani", "alisha", "shavez")          # D776: "All 3 should be able to do Docterz corrections"
PARCHI_USERS = ("shavez", "bhati")                      # slip_log.REPORT_USERS: Bhati does the slip work as Shavez does
TENDERS = ("cash", "upi", "card")
T_EN = {"cash": "cash", "upi": "UPI", "card": "card"}
T_HI = {"cash": "cash", "upi": "UPI", "card": "card"}
SEC_EN = {"consult": "consultation", "xray": "X-ray", "proc": "procedure"}
SEC_HI = {"consult": "consultation", "xray": "X-ray", "proc": "procedure"}
NOT_RIGHT = (("docterz_right", "Docterz sahi hai", "Docterz is right"),
             ("other", "Kuch aur", "something else"))      # never the words "split payment" (the owner, 13-Oct)
NOT_RIGHT_EN = {k: e for k, _h, e in NOT_RIGHT}
NOT_RIGHT_HI = {k: h for k, h, _e in NOT_RIGHT}

SCHEMA = """
CREATE TABLE IF NOT EXISTS day_check_tick (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  day     TEXT NOT NULL,
  key     TEXT NOT NULL,
  act     TEXT NOT NULL,
  reason  TEXT NOT NULL DEFAULT '',
  pick    TEXT NOT NULL DEFAULT '',
  who     TEXT NOT NULL,
  at      TEXT NOT NULL,
  state   TEXT NOT NULL DEFAULT 'live' CHECK (state IN ('live','undone'))
);
CREATE INDEX IF NOT EXISTS day_check_tick_day ON day_check_tick(day, key);
"""


def init(app, db_getter, require_fn, audit_fn=None, unit="clinic"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    try:                                                  # S846: his 'Slips not in Docterz' page, beside this file
        import not_in_docterz as _s846_nid                # noqa: PLC0415
        _s846_nid.init(app, db_getter, require_fn, audit_fn)
    except Exception as _ex_s846:                         # noqa: BLE001 -- the day check works without it
        import sys as _sys                                # noqa: PLC0415
        print("not_in_docterz NOT mounted: %s" % _ex_s846, file=_sys.stderr)
    return bp


def ensure(con):
    global _done
    if _done:
        return
    con.executescript(SCHEMA)
    con.commit()
    _done = True


# ---------------------------------------------------------------- small helpers
def _now():
    return dt.datetime.now().replace(microsecond=0)


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def rs(p):
    return "Rs {:,}".format(int(round((p or 0) / 100.0)))


def _iso_ok(s):
    try:
        return dt.date.fromisoformat(s).isoformat() == s
    except (ValueError, TypeError):
        return False


def dm(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%d-%b")
    except (ValueError, TypeError):
        return iso or ""


def tender_of(mode):
    m = (mode or "").strip()
    if m == "Cash":
        return "cash"
    if m in ("Debit Card", "Credit Card"):
        return "card"
    if m in ("Online Payment", "Net Banking", "Patient APP", "Wallet"):
        return "upi"
    if m == "Split Payment":
        return "split"
    return "other" if m else ""


def _SL():
    try:
        import slip_log                                  # noqa: PLC0415
        return slip_log
    except Exception:                                    # noqa: BLE001
        return None


def _SA():
    try:
        import slip_adjust                               # noqa: PLC0415
        return slip_adjust
    except Exception:                                    # noqa: BLE001
        return None


def _CR():
    import clinic_register                               # noqa: PLC0415
    return clinic_register


def _has(con, table):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


# ---------------------------------------------------------------- reading the four records
def _docterz(con, d):
    """(lines, legs) -- lines: every Docterz line of the day with its tender; legs: {clinic_id: [(mode, paise)]} of the
    bills paid two ways (clinic_day_tender)."""
    lines, legs = [], {}
    if not _has(con, "clinic_day_line"):
        return lines, legs
    if _has(con, "clinic_day_tender"):
        for r in con.execute("SELECT clinic_id, tender, amount_p FROM clinic_day_tender WHERE business_date=? ORDER BY rowid", (d,)):
            legs.setdefault(str(r["clinic_id"] or ""), []).append(((r["tender"] or "").strip(), int(r["amount_p"] or 0)))
    for r in con.execute("SELECT section, sn, patient, clinic_id, amount_p, mode FROM clinic_day_line WHERE business_date=? "
                         "ORDER BY section, sn", (d,)):
        cid = str(r["clinic_id"] or "")
        t = "legs" if cid in legs else tender_of(r["mode"])
        lines.append(dict(section=r["section"], sn=r["sn"], patient=(r["patient"] or "").strip(), cid=cid,
                          amount_p=int(r["amount_p"] or 0), mode=r["mode"] or "", tender=t))
    return lines, legs


def _units(paid_lines, legs):
    """Every payment as it was recorded: one unit per Docterz line, and for a bill paid two ways one unit per way, placed
    on its head the owner's way (13-Oct: "the 600 is the consultation and the rest is ... X-ray or procedure"). A
    'Wallet' unit is an online booking paid through Razorpay to another bank (12-Oct): it is UPI for the register and is
    never looked for in the clinic merchant's bank feed."""
    units = []
    for ln in paid_lines:
        if ln["tender"] != "legs":
            units.append(dict(ln, wallet=(ln["mode"].strip() == "Wallet")))
    for cid, lg in legs.items():
        mine = [ln for ln in paid_lines if ln["cid"] == cid and ln["amount_p"] > 0]
        mine.sort(key=lambda x: (x["section"] != "consult", x["sn"]))
        free = list(mine)
        for mode, amt in lg:
            hit = next((ln for ln in free if ln["amount_p"] == amt), None)
            if hit is None:
                hit = free[0] if free else (mine[0] if mine else None)
            if hit is not None and hit in free:
                free.remove(hit)
            base = hit or dict(section="consult", sn=0, patient="", cid=cid)
            units.append(dict(section=base["section"], sn=base["sn"], patient=base["patient"], cid=cid, amount_p=amt,
                              mode=mode, tender=tender_of(mode), wallet=(mode == "Wallet")))
    return units


def _register(con, d):
    """{(section, tender): paise} with dressing clubbed into procedures (the owner's ruling), or None."""
    if not _has(con, "clinic_register_day"):
        return None
    r = con.execute("SELECT * FROM clinic_register_day WHERE business_date=?", (d,)).fetchone()
    if r is None:
        return None
    out = {}
    for sec, col in (("consult", "cons"), ("xray", "xray"), ("proc", "proc"), ("proc", "dress")):
        for t in TENDERS:
            try:
                v = int(r["%s_%s_p" % (col, t)] or 0)
            except (IndexError, KeyError):
                v = 0
            out[(sec, t)] = out.get((sec, t), 0) + v
    return out


def _bank(con, d):
    """(total, [amounts], known, other_upi) -- the clinic merchant's UPI for the day; other UPI (a personal phone,
    clinic_money channel 5) is never in the bank and is taken out of the register's side before comparing."""
    try:
        total, known = _CR().bank_upi(con, d)
    except Exception:                                    # noqa: BLE001
        total, known = None, False
    amts = []
    if known:
        try:
            amts = [int(r[0] or 0) for r in con.execute("SELECT amount_p FROM upi_txn WHERE unit='clinic' AND txn_date=?", (d,))]
        except Exception:                                # noqa: BLE001
            amts = []
    oth = 0
    try:
        cm = _CR()._cm
        if cm is not None:
            oth = int(cm.other_upi_total_p(con, d) or 0)
    except Exception:                                    # noqa: BLE001
        oth = 0
    return total, amts, known, oth


def _parchi(con, d):
    """The day's parchis that count: state 'ok', with each X-ray / procedure line's expected money (rate - chhoot; a
    REJECTED chhoot puts the full rate back) and any radd (cancel) entry. Uses slip_log.day_slips when it is there."""
    if not _has(con, "slip"):
        return []
    SL = _SL()
    if SL is not None:
        rows = SL.day_slips(con, d)
    else:
        rows = [dict(r) for r in con.execute("SELECT * FROM slip WHERE day=? AND state<>'void' ORDER BY series, slip_no", (d,))]
        for r in rows:
            r["items"] = [dict(i) for i in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (r["id"],))]
    adj, canc = {}, {}
    if _has(con, "slip_adjust"):
        ids = [it["id"] for r in rows for it in r.get("items", [])]
        if ids:
            for a in con.execute("SELECT * FROM slip_adjust WHERE item_id IN (%s) AND state<>'replaced' ORDER BY id"
                                 % ",".join("?" * len(ids)), ids):
                adj[a["item_id"]] = dict(a)
        for a in con.execute("SELECT * FROM slip_adjust WHERE kind='cancel' AND day=? AND state IN ('pending','approved') "
                             "ORDER BY id", (d,)):
            canc[a["slip_id"]] = dict(a)
    out = []
    for r in rows:
        if r["state"] != "ok":
            continue
        r["cancel"] = canc.get(r["id"])
        for it in r.get("items", []):
            a = adj.get(it["id"])
            disc = int(it.get("discount_p") or 0)
            if a and a["state"] == "rejected":
                disc = 0
            it["adjust"] = a
            it["expect_p"] = max(0, int(it.get("price_p") or 0) - disc)
        out.append(r)
    return out


def _name(con, cid, lines, slip=None):
    for ln in lines:
        if ln["cid"] == cid and ln["patient"]:
            return ln["patient"]
    if slip is not None:
        if slip.get("no_id_name"):
            return slip["no_id_name"]
        if slip.get("name_seen"):
            return slip["name_seen"]
    SL = _SL()
    if SL is not None and cid:
        try:
            p = SL.patient(con, cid)
            if p:
                return p[0]
        except Exception:                                # noqa: BLE001
            pass
    return ""


def _item_word(it):
    return (it.get("name") or "") + ((" " + it["side"]) if it.get("side") else "")


# ---------------------------------------------------------------- the check
S846_WORDS = {"entered": ("entered in Docterz back-dated by Dr Manoj (not in this day's export yet)",
                          "Dr Manoj ne Docterz mein purani tareekh se daal diya"),
              "outside": ("kept outside Docterz by Dr Manoj", "Dr Manoj: Docterz ke bahar"),
              "free": ("free / staff / home (Dr Manoj)", "free / staff / ghar (Dr Manoj)"),
              "wrong": ("wrong slip (Dr Manoj)", "galat parchi (Dr Manoj)")}


def _s846_marks(con, d):
    """S846 (the owner, 16-Nov-2026): his answers on 'Slips not in Docterz' -- {(slip_id, kind): act}. {} when absent."""
    try:
        import not_in_docterz                         # noqa: PLC0415
        return not_in_docterz.marks_for_day(con, d)
    except Exception:                                    # noqa: BLE001 -- the day check stands without it
        return {}


def _s846_act(marks, w):
    s = w.get("slip") or {}
    if not marks or not s.get("id") or w.get("partial"):          # S474 review: a part-billed line is never his
        return None
    return marks.get((s["id"], "opd" if w.get("opd") else w.get("section")))


def _s846_note(w, act, who=""):
    en, hi = S846_WORDS.get(act, (act, act))
    wl = (who or "").strip().lower()
    if wl == "auto" and act == "outside":                 # S970: answered by itself -- the slip is made, the register holds it
        en, hi = "kept outside Docterz automatically (the slip was made)", "Docterz ke bahar, apne aap (parchi bani)"
    elif wl and wl != "manoj":                            # S962: a staff login's answer is named as theirs, never as his
        if act == "free":
            en, hi = "money never taken (%s)" % wl.title(), "paise liye hi nahi (%s)" % wl.title()
        else:
            en, hi = en.replace("Dr Manoj", wl.title()), hi.replace("Dr Manoj", wl.title())
    return ("%s %s · %s — %s" % (rs(w["amount"]), w["what_en"], _who_en(w["name"], w["cid"]), en),
            "%s %s · %s — %s" % (rs(w["amount"]), w["what_hi"], _who_en(w["name"], w["cid"]), hi))


# ---------------------------------------------------------------- S962 (D1080): the Morning Match
S962 = "S962.1"
REMIND_GAP_H = 3                                         # "Dr sahab ko yaad dilayein": once in three hours, across the days
NID_PAGE = "/finance/clinic/not-in-docterz"
LIVE_DB = os.environ.get("EVCHK_LIVE_DB", "/root/finance/finance.db")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
PUSHER = None                                            # the walk hands in a stub: (who, title, body, url, tag) -> (sent, why)
REFUND_EN = {"billed_ret": "billed · refunded", "billed_nt": "billed · money never taken", "cancelled_ret": "cancelled · refunded"}
REFUND_HI = {"billed_ret": "bill raha · paise lautaye", "billed_nt": "bill raha · paise liye hi nahi",
             "cancelled_ret": "bill bhi cancel · paise lautaye"}


def _s962_items(con, slip_id):
    """[(kind, expected paise, word)] of one slip's X-ray / procedure lines (a REJECTED chhoot puts the full rate back)."""
    try:
        its = [dict(r) for r in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (slip_id,))]
    except Exception:                                    # noqa: BLE001
        return []
    rej = set()
    if its and _has(con, "slip_adjust"):
        try:
            rej = {r[0] for r in con.execute("SELECT item_id FROM slip_adjust WHERE state='rejected' AND item_id IN (%s)"
                                             % ",".join("?" * len(its)), [i["id"] for i in its])}
        except Exception:                                # noqa: BLE001
            rej = set()
    out = []
    for it in its:
        if it.get("kind") in ("xray", "proc"):
            disc = 0 if it["id"] in rej else int(it.get("discount_p") or 0)
            out.append((it["kind"], max(0, int(it.get("price_p") or 0) - disc), _item_word(it)))
    return out


def _cancels(con, d):
    """S962: the day's radd after billing (slip_adjust kind 'cancel', pending or approved -- an approved one has taken its slip
    out of the day's parchis), each with its slip's own money. [] when anything cannot be read."""
    if not (_has(con, "slip_adjust") and _has(con, "slip")):
        return []
    try:
        rows = [dict(r) for r in con.execute("SELECT * FROM slip_adjust WHERE kind='cancel' AND day=? AND state IN "
                                             "('pending','approved') ORDER BY id", (d,))]
    except Exception:                                    # noqa: BLE001
        return []
    out, fee, seen = [], None, set()
    for a in rows:
        if a["slip_id"] in seen:
            continue
        s = con.execute("SELECT * FROM slip WHERE id=?", (a["slip_id"],)).fetchone()
        if s is None:
            continue
        seen.add(a["slip_id"])
        s = dict(s)
        if s["series"] == "opd":
            if fee is None:
                try:
                    fee = int(_SL().usual_fee(con, d) or 0) if _SL() is not None else 0
                except Exception:                        # noqa: BLE001
                    fee = 0
            items = [("consult", fee, "")]
        else:
            items = _s962_items(con, s["id"])
        how = (a.get("cancel_how") or "").strip()
        out.append(dict(slip_id=s["id"], series=s["series"], slip_no=s["slip_no"],
                        cid=str(a.get("clinic_id") or s.get("clinic_id") or "").strip(), how=how,
                        tender=((a.get("refund_t") or "").strip().lower() if how == "returned" else ""), state=a["state"],
                        made_by=a.get("made_by") or "", made_at=a.get("made_at") or "",
                        paid=(s.get("paid_mode") or "").strip().lower(), items=items, amount=sum(x[1] for x in items),
                        name=(s.get("name_seen") or s.get("no_id_name") or "").strip()))
    return out


def _s962_hold(lines, slips, cancels):
    """S962 (F-1678): the Docterz lines each radd covers. As clinic_money's S442 takes an approved radd's line out: an OPD radd
    covers one consultation of its ID; an X-ray/procedure radd that ID's X-ray and procedure lines -- unless the ID has another
    live parchi of that kind that day, when only lines of the radd's own amounts are taken.
    The register's book is written NET of a refund (read on the 23-Oct database: a refunded fee was never written), so a
    radd's line Docterz still bills is taken out of Docterz's side -- refunded or never taken alike, as clinic_money's S442
    takes it out of the expected cash / UPI; a radd Docterz cancelled too moves nothing. -> (held {(section, sn): cancel},
    refunds [the matched radds])."""
    held, refunds = {}, []
    live_opd, live_xp, live_it = {}, set(), {}
    for s in slips:
        if s.get("cancel") or not s.get("clinic_id"):
            continue
        if s["series"] == "opd":
            live_opd[s["clinic_id"]] = live_opd.get(s["clinic_id"], 0) + 1
        else:
            live_xp.add(s["clinic_id"])
            for it in s.get("items", []):
                k = (s["clinic_id"], it.get("kind"), int(it.get("expect_p") or 0))
                live_it[k] = live_it.get(k, 0) + 1
    for c in cancels:
        cid = c["cid"]
        mine = [ln for ln in lines if cid and ln["cid"] == cid and ln["amount_p"] > 0 and (ln["section"], ln["sn"]) not in held]
        take = []
        if c["series"] == "opd":
            cons = [ln for ln in mine if ln["section"] == "consult"]
            if len(cons) > live_opd.get(cid, 0):
                take = cons[:1]
        else:
            xp = [ln for ln in mine if ln["section"] in ("xray", "proc")]
            if cid in live_xp:                           # cold review: a line only while Docterz has more of that kind and
                for kind, amt, _w in c["items"]:         # amount than the live parchis of the ID carry
                    same = [ln for ln in xp if ln["section"] == kind and ln["amount_p"] == amt and ln not in take]
                    if len(same) > live_it.get((cid, kind, amt), 0):
                        take.append(same[0])
            else:
                take = xp
        for ln in take:
            held[(ln["section"], ln["sn"])] = c
        if c["how"] != "returned" and not take:
            continue                                     # money never taken and no Docterz bill: nothing to match
        t_back = c["tender"] if c["tender"] in TENDERS else ""
        word = ("billed_ret" if c["how"] == "returned" else "billed_nt") if take else "cancelled_ret"
        refunds.append(dict(c, kept=bool(take), billed=sum(ln["amount_p"] for ln in take), t_back=t_back, word=word,
                            shown=(sum(ln["amount_p"] for ln in take) if take else c["amount"]),
                            pname=(take[0]["patient"] if take and take[0]["patient"] else c["name"])))
    return held, refunds


def _s962_legs(legs, held_lines, paid_lines):
    """Cold review (S962): a bill paid two ways (clinic_day_tender) whose radd's line is out of Docterz's side -- that line's
    amount comes off the ID's legs -- a leg of the same amount in the refund's own tender first, then any leg of that amount,
    else the legs reduced, the refund's tender first, then the largest -- and an ID with no live line of any amount left loses its
    legs altogether. held_lines: [(line, its radd)]."""
    out = {k: list(v) for k, v in legs.items()}
    for ln, c in held_lines:
        lg = out.get(ln["cid"])
        if not lg:
            continue
        due = int(ln["amount_p"] or 0)
        tb = c.get("tender") if c.get("how") == "returned" else ""
        i = next((j for j, (m, a) in enumerate(lg) if a == due and tb and tender_of(m) == tb), None)
        if i is None:
            i = next((j for j, (_m, a) in enumerate(lg) if a == due), None)
        if i is not None:
            lg.pop(i)
            continue
        for j in sorted(range(len(lg)), key=lambda x: (0 if (tb and tender_of(lg[x][0]) == tb) else 1, -lg[x][1])):
            if due <= 0:
                break
            m, a = lg[j]
            cut = min(a, due)
            lg[j] = (m, a - cut)
            due -= cut
        out[ln["cid"]] = [(m, a) for m, a in lg if a > 0]
    return {k: v for k, v in out.items() if v and any(ln["cid"] == k and ln["amount_p"] > 0 for ln in paid_lines)}


def _s962_add(rows, r):
    """One back-date row per (slip, kind), as his list and its answers work (re-look): two lines of one slip's kind are joined;
    the row counts as in the register when any part of it is; 'allp' (S970) only when every part is."""
    for x in rows:
        if x["slip_id"] == r["slip_id"] and x["kind"] == r["kind"]:
            x["amount"] += r["amount"]
            x["what_en"] = "%s + %s" % (x["what_en"], r["what_en"])
            x["what_hi"] = "%s + %s" % (x["what_hi"], r["what_hi"])
            x["placed"] = x["placed"] or r["placed"]
            x["allp"] = x.get("allp", x["placed"]) and bool(r["placed"])
            x["tender"] = x["tender"] or r["tender"]
            return
    r["allp"] = bool(r["placed"])
    rows.append(r)


def _s962_nid_keys(con, d):
    """{(slip_id, kind)} -- the day's rows of his 'Slips not in Docterz' list (answered or not). set() when it cannot be read:
    then every slip keeps its staff card, as before S962."""
    try:
        import not_in_docterz                            # noqa: PLC0415
        return {(r["slip_id"], r["kind"]) for r in not_in_docterz.rows(con, d, d)}
    except Exception:                                    # noqa: BLE001
        return set()


def _s962_mark_who(con, d):
    """{(slip_id, kind): who} -- who gave each live answer of the day on the 'not in Docterz' list. {} when absent."""
    try:
        if not _has(con, "nid_mark"):
            return {}
        return {(m[0], m[1]): (m[2] or "") for m in con.execute("SELECT slip_id, kind, who FROM nid_mark WHERE day=? AND state='live'", (d,))}
    except Exception:                                    # noqa: BLE001
        return {}


def _s962_mkey(w):
    s = w.get("slip") or {}
    return (s.get("id"), "opd" if w.get("opd") else w.get("section"))


def _s962_live(con):
    try:
        path = con.execute("PRAGMA database_list").fetchone()[2]
        return bool(path) and os.path.realpath(path) == os.path.realpath(LIVE_DB)
    except Exception:                                    # noqa: BLE001
        return False


def _s962_push(con, who, title, body, url, tag):
    """(sent, why) through the call-back clock's own Web Push to his own devices (never the staff ntfy topic) -- only from
    the live database: a walk or a copy pushes nothing (A-D147)."""
    if PUSHER is not None:
        return PUSHER(who, title, body, url, tag)
    if not _s962_live(con):
        return 0, "not the live database"
    try:
        import sys                                       # noqa: PLC0415
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import callback_clock as cc                      # noqa: PLC0415
        pusher = cc.get_pusher(None)
        if pusher is None:
            return 0, "no push road"
        s, _f = cc.push(pusher, list(who), title, body, url, tag)   # his own devices only: never the staff topic
        return s, ("" if s else "no device of his took it")
    except Exception as ex:                              # noqa: BLE001
        return 0, "send: %s" % str(ex)[:80]


def _s962_last_remind(con):
    try:
        r = con.execute("SELECT who, at FROM day_check_tick WHERE act='remind' AND state='live' AND reason IN ('sent','sending') "
                        "ORDER BY at DESC, id DESC LIMIT 1").fetchone()
        return dict(r) if r else None
    except Exception:                                    # noqa: BLE001
        return None


def check_day(con, d):
    """The day's corrections. Pure read (the tick table aside). Returns a dict the page and the owner's line render."""
    ensure(con)
    lines, legs = _docterz(con, d)
    reg = _register(con, d)
    bank, bank_amts, bank_known, other_upi = _bank(con, d)
    slips = _parchi(con, d)
    cancels = _cancels(con, d)                           # S962 (F-1678): every radd of the day
    paid_lines = [ln for ln in lines if ln["section"] in ("consult", "xray", "proc")]
    out = dict(day=d, docterz=bool(lines), register=reg is not None, bank_known=bank_known, cards=[], notes=[])
    if not lines or reg is None:
        out["state"] = "no_docterz" if not lines else "no_register"
        out["counts"] = _counts([])
        return out

    # S962 (D1080, F-1678): each radd matched -- Docterz kept the bill, or cancelled it too; never subtracted twice
    held, refunds = _s962_hold(lines, slips, cancels)
    nt_billed = sum(ln["amount_p"] for ln in paid_lines if (ln["section"], ln["sn"]) in held)
    paid_lines = [ln for ln in paid_lines if (ln["section"], ln["sn"]) not in held]   # the book is net of a radd
    if held:                                             # a bill paid two ways: the radd's part comes off its legs
        legs = _s962_legs(legs, [(ln, held[(ln["section"], ln["sn"])]) for ln in lines if (ln["section"], ln["sn"]) in held], paid_lines)
    # --- the totals: register - Docterz, by tender and by section x tender
    units = _units(paid_lines, legs)
    doc_t = dict.fromkeys(TENDERS, 0)
    doc_st = {}
    other_p = 0
    for un in units:
        if un["tender"] in TENDERS:
            doc_t[un["tender"]] += un["amount_p"]
            doc_st[(un["section"], un["tender"])] = doc_st.get((un["section"], un["tender"]), 0) + un["amount_p"]
        elif un["amount_p"]:
            other_p += un["amount_p"]
    reg_t = {t: sum(v for (s, tt), v in reg.items() if tt == t) for t in TENDERS}
    delta = {t: reg_t[t] - doc_t[t] for t in TENDERS}
    sdelta = {k: reg.get(k, 0) - doc_st.get(k, 0) for k in set(reg) | set(doc_st)}
    if other_p:
        out["notes"].append(("%s in Docterz under a payment mode this page does not know" % rs(other_p),
                             "%s Docterz mein anjaan mode mein" % rs(other_p)))

    cards = []
    by_cid = {}
    for ln in lines:
        by_cid.setdefault(ln["cid"], []).append(ln)
    opd = [s for s in slips if s["series"] == "opd"]
    xp = [s for s in slips if s["series"] == "xp"]

    # --- 1 · patient by patient: the parchi against Docterz
    want = []          # money the parchi says was done and Docterz has not billed: (amount, tender guess, card base)
    parchi_side = []   # parchi lines Docterz does not support (decided after the money is placed)
    xp_by = {}
    for s in xp:
        if s.get("no_id_name") or not s.get("clinic_id"):
            cards.append(_card("hand", "noid:%d" % s["id"], 0, d,
                               en="Parchi %d has no clinic ID (%s) — match it by hand" % (s["slip_no"], s.get("no_id_name") or "—"),
                               hi="Parchi %d par clinic ID nahi (%s) — haath se milayein" % (s["slip_no"], s.get("no_id_name") or "—")))
            continue
        if s.get("cancel"):
            st = s["cancel"]["state"]
            out["notes"].append(("Parchi %d: not paid — %s" % (s["slip_no"], "approved" if st == "approved" else "waiting for your approval"),
                                 "Parchi %d: paise nahi liye — %s" % (s["slip_no"], "manzoor" if st == "approved" else "manzoori baaki")))
            continue
        xp_by.setdefault(s["clinic_id"], []).append(s)
    for cid, ss in xp_by.items():
        mine = [ln for ln in by_cid.get(cid, []) if (ln["section"], ln["sn"]) not in held]   # S962: a radd's lines are matched
        name = _name(con, cid, lines, ss[0])
        for kind in ("xray", "proc"):
            its = [(s, it) for s in ss for it in s.get("items", []) if it["kind"] == kind]
            dl = [ln for ln in mine if ln["section"] == kind]
            if not its and not dl:
                continue
            p_sum = sum(it["expect_p"] for _s, it in its)
            d_sum = sum(ln["amount_p"] for ln in dl)
            if p_sum == d_sum:
                continue
            if not dl:                                   # nothing billed: each parchi line is wanted money
                for s, it in its:
                    if it["expect_p"] <= 0:
                        continue
                    want.append(dict(amount=it["expect_p"], tick=s.get("paid_mode") or "", section=kind, cid=cid, name=name,
                                     slip=s, item=it, key="add:%d" % it["id"],
                                     what_en="%s %s" % (SEC_EN[kind], _item_word(it)), what_hi="%s %s" % (SEC_HI[kind], _item_word(it))))
                continue
            if not its:                                  # Docterz billed, no parchi line
                parchi_side.append(dict(kind="parchi_missing", cid=cid, name=name, section=kind, amount=d_sum,
                                        key="pmiss:%s:%s" % (cid, kind), slip=ss[0]))
                continue
            dup = _duplicate(its, p_sum - d_sum)
            if dup is not None:
                parchi_side.append(dict(kind="dup_item", cid=cid, name=name, section=kind, amount=p_sum - d_sum, slip=dup[0],
                                        items=dup[1], key="pdup:%s" % "-".join(str(i["id"]) for i in dup[1])))
            elif p_sum > d_sum:                          # the parchi has more than Docterz: money the register may hold
                s0, it0 = its[0]
                want.append(dict(amount=p_sum - d_sum, tick=s0.get("paid_mode") or "", section=kind, cid=cid, name=name,
                                 slip=s0, item=None, key="part:%s:%s" % (cid, kind), partial=(p_sum, d_sum),
                                 what_en="%s (parchi %s, Docterz %s)" % (SEC_EN[kind], rs(p_sum), rs(d_sum)),
                                 what_hi="%s (parchi %s, Docterz %s)" % (SEC_HI[kind], rs(p_sum), rs(d_sum))))
            else:                                        # Docterz has more than the parchi
                parchi_side.append(dict(kind="parchi_short", cid=cid, name=name, section=kind, amount=d_sum - p_sum,
                                        slip=its[0][0], key="pshort:%s:%s" % (cid, kind), sums=(p_sum, d_sum)))
    # Docterz X-ray / procedure lines whose patient has no X-ray/Proc parchi at all
    for ln in paid_lines:
        if (ln["section"] in ("xray", "proc") and ln["amount_p"] > 0 and ln["cid"] not in xp_by
                and (ln["section"], ln["sn"]) not in held):   # S962 (F-1678): a radd's bill is no missing parchi
            k = "pmiss:%s:%s" % (ln["cid"], ln["section"])
            if not any(p["key"] == k for p in parchi_side):
                parchi_side.append(dict(kind="parchi_missing", cid=ln["cid"], name=ln["patient"], section=ln["section"],
                                        amount=sum(x["amount_p"] for x in by_cid.get(ln["cid"], []) if x["section"] == ln["section"]
                                                   and (x["section"], x["sn"]) not in held),
                                        key=k, slip=None))
    # OPD: a consultation billed with no OPD parchi; an OPD parchi with nothing in Docterz; the same ID twice
    opd_ids = {}
    for s in opd:
        if s.get("no_id_name") or not s.get("clinic_id"):
            cards.append(_card("hand", "noid:%d" % s["id"], 0, d,
                               en="OPD parchi %d has no clinic ID (%s) — match it by hand" % (s["slip_no"], s.get("no_id_name") or "—"),
                               hi="OPD parchi %d par clinic ID nahi (%s) — haath se milayein" % (s["slip_no"], s.get("no_id_name") or "—")))
            continue
        if s.get("cancel"):
            continue
        opd_ids.setdefault(s["clinic_id"], []).append(s)
    orphan_cons = [ln for ln in paid_lines if ln["section"] == "consult" and ln["amount_p"] > 0 and ln["cid"] not in opd_ids
                   and (ln["section"], ln["sn"]) not in held]          # S962 (F-1678)
    dups = [(cid, ss) for cid, ss in opd_ids.items() if len(ss) > 1]
    paired = set()
    if len(dups) == 1 and len(orphan_cons) == 1:         # one ID written twice and one billed patient with no parchi:
        cid, ss = dups[0]                                # the second parchi is almost certainly that patient's
        ln = orphan_cons[0]
        parchi_side.append(dict(kind="opd_wrong_id", cid=cid, name=_name(con, cid, lines), slip=ss[-1], to_cid=ln["cid"],
                                to_name=ln["patient"], amount=ln["amount_p"], key="pid:%d" % ss[-1]["id"]))
        paired.add(ln["cid"])
    else:
        for cid, ss in dups:
            parchi_side.append(dict(kind="opd_dup", cid=cid, name=_name(con, cid, lines), slip=ss[-1], amount=0,
                                    key="podup:%d" % ss[-1]["id"]))
    for ln in orphan_cons:
        if ln["cid"] in paired:
            continue
        parchi_side.append(dict(kind="opd_missing", cid=ln["cid"], name=ln["patient"], amount=ln["amount_p"],
                                key="pomiss:%s" % ln["cid"], slip=None))
    try:
        fee = _SL().usual_fee(con, d) if _SL() is not None else 0
    except Exception:                                    # noqa: BLE001
        fee = 0
    for cid, ss in opd_ids.items():
        if not by_cid.get(cid):                          # the patient is nowhere in Docterz -- not even free
            s = ss[0]
            want.append(dict(amount=fee or 0, tick="", section="consult", cid=cid, name=_name(con, cid, lines, s), slip=s,
                             item=None, key="addopd:%d" % s["id"], opd=True,
                             what_en="consultation (OPD parchi %d)" % s["slip_no"], what_hi="consultation (OPD parchi %d)" % s["slip_no"]))

    # --- 2 · the money: wanted lines are placed while the register holds room for them (the referee)
    # S962 (D1080, F-1679): a slip whose patient Docterz does not carry is HIS to back-date -- it goes to his back-date list by
    # itself (the same rows as his 'Slips not in Docterz' page), never to a staff 'Added'. Its money is still placed.
    room = sum(delta.values())
    want.sort(key=lambda w: (0 if w["tick"] else 1, -w["amount"]))
    _s846 = _s846_marks(con, d)                           # S846: his answers on his 'Slips not in Docterz' page
    _s962w = _s962_mark_who(con, d)                       # S962: who answered
    _nid = _s962_nid_keys(con, d)                         # second look: only rows his own list carries go to it
    backdate, nid_placed = [], 0
    for w in want:
        _sa = _s846_act(_s846, w)
        if _sa == "outside" and _s962_mkey(w) not in _nid:   # S970 review: his list no longer carries it (Docterz's clinical
            _sa = None                                    # report knows the visit) -- an old answer hides no staff card
        _by = _s962w.get(_s962_mkey(w), "")
        if _sa in ("free", "wrong"):                 # nothing collected: nothing for the staff to do
            out["notes"].append(_s846_note(w, _sa, _by))
            continue
        if w["amount"] > 0 and room >= w["amount"]:
            t = w["tick"] if w["tick"] in TENDERS else max(TENDERS, key=lambda x: delta[x])
            delta[t] -= w["amount"]
            sdelta[(w["section"], t)] = sdelta.get((w["section"], t), 0) - w["amount"]
            room -= w["amount"]
            if _sa:                                       # S846: entered back-dated / kept outside -- the money is placed, no card
                nid_placed += w["amount"]
                out["notes"].append(_s846_note(w, _sa, _by))
                continue
            if not w.get("partial") and _s962_mkey(w) in _nid:   # S962: his back-date list, with the money placed
                nid_placed += w["amount"]
                _s962_add(backdate, dict(key=w["key"], slip_id=(w.get("slip") or {}).get("id"), kind=_s962_mkey(w)[1], cid=w["cid"],
                                         name=w["name"], what_en=w["what_en"], what_hi=w["what_hi"], amount=w["amount"], tender=t,
                                         placed=True))
                continue
            cards.append(_card("missing", w["key"], w["amount"], d, who="docterz", tender=t, cid=w["cid"], name=w["name"],
                               slip=w["slip"], item=w["item"], section=w["section"],
                               en="%s — Docterz entry missing · %s · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"], T_EN[t]),
                               hi="%s — Docterz mein entry nahi · %s · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"], T_HI[t])))
        elif w.get("partial"):
            # register = Docterz != parchi, and Docterz has the line: the parchi carries too much
            ps, ds = w["partial"]
            parchi_side.append(dict(kind="parchi_over", cid=w["cid"], name=w["name"], section=w["section"], amount=ps - ds,
                                    slip=w["slip"], key="pover:%s:%s" % (w["cid"], w["section"]), sums=(ps, ds)))
        elif _sa:
            # S962: his answer says the money was taken (entered / kept outside), but the register does not hold it
            n_en, n_hi = _s846_note(w, _sa, _by)
            cards.append(_card("hand", "s962ans:%s" % w["key"], w["amount"], d,
                               en="%s — but the register does not hold it; check by hand" % n_en,
                               hi="%s — par register mein nahi; haath se dekhein" % n_hi))
        elif _s962_mkey(w) in _nid:
            # S962: register = Docterz != parchi -- not billed and not collected; his list, the staff can say 'money never taken'
            _s962_add(backdate, dict(key=w["key"], slip_id=(w.get("slip") or {}).get("id"), kind=_s962_mkey(w)[1], cid=w["cid"],
                                     name=w["name"], what_en=w["what_en"], what_hi=w["what_hi"], amount=w["amount"], tender="",
                                     placed=False))
        else:
            # not on his list (Docterz's clinical report knows the visit, an ID his list cannot read): the staff card, as before
            cards.append(_card("notbilled", w["key"], w["amount"], d, who="docterz", cid=w["cid"], name=w["name"],
                               slip=w["slip"], item=w["item"], section=w["section"],
                               en="%s on the parchi — not billed, not in the register · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"]),
                               hi="%s parchi par — na bill hua, na register mein · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"])))

    # --- 3 · payment modes: money in one tender of Docterz that the register holds in another
    bank_left = list(bank_amts)
    for un in units:
        if un["tender"] == "upi" and not un["wallet"] and un["amount_p"] in bank_left:
            bank_left.remove(un["amount_p"])
    tick_of = {}
    for s in xp:
        if s.get("clinic_id") and s.get("paid_mode"):
            tick_of[s["clinic_id"]] = s["paid_mode"]

    def tick_for(un):
        return tick_of.get(un["cid"], "") if un["section"] in ("xray", "proc") else ""

    # S653 (D788, F-1022 -- the owner, 25-Oct-2026: "Reception staff wrongly chooses the debit card option most of the times
    # when the payment is through UPI. The debit card option is very, very rare. And if at all there is a debit card used, then it
    # will reflect in the next day's bank MDR report"): when the move below takes a Docterz 'Debit Card' payment to UPI -- the
    # register does not hold it as card -- and the bank shows its exact amount as UPI, it IS UPI: counted so, no correction
    # asked; one plain note says so. Every other move, and its words, is exactly as before.
    as_upi = []
    moved = set()
    for _guard in range(12):
        neg = [t for t in TENDERS if delta[t] < 0]
        pos = [t for t in TENDERS if delta[t] > 0]
        if not neg or not pos:
            break
        found = []                                   # (score, (unit indexes), a, b)
        for a in neg:
            for b in pos:
                lim = min(-delta[a], delta[b])
                cand = [i for i, un in enumerate(units) if i not in moved and un["tender"] == a and 0 < un["amount_p"] <= lim
                        and tick_for(un) != a]       # a line the room saw paid that way never moves
                for i in cand:
                    un = units[i]
                    if un["amount_p"] == lim or tick_for(un) == b:
                        found.append((_score(un, a, b, lim, delta, sdelta, tick_for(un), bank_left), (i,), a, b))
                if not any(f[2] == a and f[3] == b and units[f[1][0]]["amount_p"] == lim for f in found):
                    for combo in _combos(cand, units, lim):  # two or three lines that come to it exactly
                        sc = sum(_score(units[i], a, b, lim, delta, sdelta, tick_for(units[i]), bank_left) for i in combo) / len(combo)
                        found.append((sc - 1, combo, a, b))
        if not found:
            break
        found.sort(key=lambda x: -x[0])
        top = [x for x in found if x[0] == found[0][0]]
        shapes = {(x[2], x[3], tuple(sorted(units[i]["amount_p"] for i in x[1]))) for x in top}
        if len(top) > 1 and len(shapes) == 1:        # several patients fit equally: name them, decide nothing
            sc, ix, a, b = top[0]
            amt = sum(units[i]["amount_p"] for i in ix)
            who_ = sorted({i for x in top for i in x[1]})
            names = ", ".join(_who_en(units[i]["patient"], units[i]["cid"]) for i in who_[:8]) + ((" and %d more" % (len(who_) - 8)) if len(who_) > 8 else "")
            cards.append(_card("hand", "modeany:%s:%s:%d" % (a, b, amt), amt, d,
                               en="%s paid by %s is written as %s in Docterz — %d line%s among: %s. Check by hand" % (
                                   rs(amt), T_EN[b], T_EN[a], len(ix), "" if len(ix) == 1 else "s", names),
                               hi="%s %s mein aaya, Docterz mein %s likha — inme se %d: %s. Haath se dekhein" % (
                                   rs(amt), T_HI[b], T_HI[a], len(ix), names)))
            delta[a] += amt
            delta[b] -= amt
            moved.update(who_)
            continue
        sc, ix, a, b = top[0]
        for i in ix:
            un = units[i]
            moved.add(i)
            delta[a] += un["amount_p"]
            delta[b] -= un["amount_p"]
            sdelta[(un["section"], a)] = sdelta.get((un["section"], a), 0) + un["amount_p"]
            sdelta[(un["section"], b)] = sdelta.get((un["section"], b), 0) - un["amount_p"]
            in_bank = b == "upi" and un["amount_p"] in bank_left
            if in_bank:
                bank_left.remove(un["amount_p"])
            if (a == "card" and b == "upi" and in_bank and not un["wallet"]
                    and (un.get("mode") or "").strip() == "Debit Card"):
                as_upi.append(un["amount_p"])                # S653 (D788): UPI, not a correction
                continue
            cards.append(_card("mode", "mode:%s:%s:%d:%s:%s" % (un["cid"], un["section"], un["amount_p"], a, b), un["amount_p"], d,
                               who="docterz", cid=un["cid"], name=un["patient"], section=un["section"], tender=b,
                               en="Payment mode wrong · %s · %s %s · Docterz %s, paid by %s" % (
                                   _who_en(un["patient"], un["cid"]), SEC_EN[un["section"]], rs(un["amount_p"]), un["mode"], T_EN[b]),
                               hi="Payment mode galat · %s · %s %s · Docterz mein %s, asal mein %s" % (
                                   _who_en(un["patient"], un["cid"]), SEC_HI[un["section"]], rs(un["amount_p"]), un["mode"], T_HI[b])))

    if as_upi:                                       # S653 (D788)
        out["notes"].append((
            "%s written as Debit Card in Docterz was paid by UPI (the bank has it) -- counted as UPI, nothing to change "
            "(%d bill%s). For UPI, Online Payment is the right choice in Docterz." % (rs(sum(as_upi)), len(as_upi),
                                                                                   "" if len(as_upi) == 1 else "s"),
            "%s Docterz mein Debit Card likha tha, paisa UPI se aaya (bank mein hai) -- UPI maana gaya, kuch badalna nahin "
            "(%d bill). UPI ke liye Docterz mein Online Payment chuniye." % (rs(sum(as_upi)), len(as_upi))))
    # --- 4 · what is left
    # money one tender of the register holds that another tender of Docterz has, with no patient to move: by hand
    for a in TENDERS:
        for b in TENDERS:
            if delta[a] < 0 < delta[b]:
                m = min(-delta[a], delta[b])
                ticked = [un for un in units if un["tender"] == a and tick_for(un) == a and un["amount_p"] <= m]
                why_en = (" (the room ticked %s for %s)" % (T_EN[a], ", ".join(_who_en(u_["patient"], u_["cid"]) for u_ in ticked[:4]))) if ticked else ""
                why_hi = (" (room ne %s tick kiya: %s)" % (T_HI[a], ", ".join(_who_en(u_["patient"], u_["cid"]) for u_ in ticked[:4]))) if ticked else ""
                cards.append(_card("hand", "swap:%s:%s:%d" % (a, b, m), m, d,
                                   en="%s is %s in the register and %s in Docterz — check by hand%s" % (rs(m), T_EN[b], T_EN[a], why_en),
                                   hi="%s register mein %s, Docterz mein %s — haath se dekhein%s" % (rs(m), T_HI[b], T_HI[a], why_hi)))
                delta[a] += m
                delta[b] -= m
    r_upi = reg_t["upi"] - other_upi
    for t in TENDERS:
        if delta[t] > 0:
            secs = sorted(((v, s) for (s, tt), v in sdelta.items() if tt == t and v > 0), reverse=True)
            sec = secs[0][1] if secs else "consult"
            if t == "upi" and bank_known and bank is not None and bank == r_upi - delta[t]:
                # Docterz and the bank agree; the register alone holds it: the register was most likely written wrong
                cards.append(_card("hand", "regupi:%d" % delta[t], delta[t], d,
                                   en="The register's UPI is %s more than Docterz and the bank — the register is most likely wrong" % rs(delta[t]),
                                   hi="Register ka UPI Docterz aur bank se %s zyada — register shayad galat" % rs(delta[t])))
                continue
            cards.append(_card("notfound", "nf:%s:%s:%d" % (t, sec, delta[t]), delta[t], d, who="docterz", tender=t, section=sec,
                               en="%s — Docterz entry missing, patient not found · %s · %s — find the patient: enter it in "
                                  "Docterz, and make the parchi if there is none" % (rs(delta[t]), SEC_EN[sec], T_EN[t]),   # S968
                               hi="%s — Docterz mein entry nahi, mareez nahi mila · %s · %s — mareez dhoondein: Docterz mein entry "
                                  "kijiye, parchi na ho to parchi bhi banaiye" % (rs(delta[t]), SEC_HI[sec], T_HI[t])))
        elif delta[t] < 0:
            cards.append(_card("hand", "over:%s:%d" % (t, -delta[t]), -delta[t], d,
                               en="Docterz has %s more %s than the register — check by hand" % (rs(-delta[t]), T_EN[t]),
                               hi="Docterz mein register se %s zyada %s — haath se dekhein" % (rs(-delta[t]), T_HI[t])))
    if bank_known and bank is not None and r_upi != bank and not any(c["key"].startswith("regupi:") for c in cards):
        cards.append(_card("hand", "bank:%d:%d" % (r_upi, bank), abs(r_upi - bank), d,
                           en="Bank UPI %s, register UPI %s — %s apart; check by hand" % (rs(bank), rs(r_upi), rs(abs(r_upi - bank))),
                           hi="Bank UPI %s, register UPI %s — %s ka fark; haath se dekhein" % (rs(bank), rs(r_upi), rs(abs(r_upi - bank)))))

    # --- 5 · the parchi lines (the register sides with Docterz)
    for p in parchi_side:
        cards.append(_parchi_card(p, d))

    ticks = _ticks(con, d)
    exported = _export_at(con, d)                        # S640 (D776 stage 3): when Docterz's file for the day last came in
    for c in cards:
        t = ticks.get(c["key"])
        c["tick"], c["not_fixed"] = t, None
        if t and exported and str(t["at"]) < str(exported):
            c["tick"], c["not_fixed"] = None, t          # the export after the tick still shows the line: back to staff
    dcs = [c for c in cards if c["who"] == "docterz"]
    out["reexport"] = bool(dcs) and all(c["tick"] for c in dcs) and any(c["tick"]["act"] in ("added", "changed", "found") for c in dcs)
    out["notright"] = sum(1 for c in dcs if c["tick"] and c["tick"]["act"] == "notright")
    out["not_fixed"] = sum(1 for c in cards if c.get("not_fixed"))
    # S962 (D1080): the day in one line -- register (written net of refunds) = Docterz + slips not in Docterz - refunded / never
    # taken (bills Docterz still carries) + Docterz entries still missing (staff) + not explained
    top = dict(reg=sum(reg.values()), doc=sum(doc_t.values()) + nt_billed, nid=nid_placed, back=nt_billed,
               missing=sum(c["amount"] for c in cards if c["kind"] == "missing"))
    top["left"] = top["reg"] - (top["doc"] + top["nid"] - top["back"] + top["missing"])
    issue = {str(c.get("cid") or "") for c in cards} | {b["cid"] for b in backdate} | {r["cid"] for r in refunds}
    pts = {ln["cid"] for ln in lines if ln["cid"] and ln["amount_p"] > 0}
    out["top"], out["backdate"], out["refunds"] = top, backdate, refunds
    out["matched_n"] = len(pts - issue)
    out["state"] = "checked"
    out["cards"] = cards
    out["counts"] = _counts(cards)
    out["counts"]["back_n"] = len(backdate)
    out["counts"]["back_p"] = sum(b["amount"] for b in backdate)
    out["totals"] = dict(reg=reg_t, doc=doc_t, bank=bank, other_upi=other_upi)
    return out


def _score(un, a, b, lim, delta, sdelta, tick, bank_left):
    sc = 0
    if un["amount_p"] == lim:
        sc += 4
    if un["amount_p"] == -delta[a]:
        sc += 2
    if sdelta.get((un["section"], a), 0) < 0 and sdelta.get((un["section"], b), 0) > 0:
        sc += 2
    if tick == b:
        sc += 3
    elif not tick and un["section"] in ("xray", "proc"):
        sc += 1
    if b == "upi" and un["amount_p"] in bank_left and not un["wallet"]:
        sc += 2
    if un.get("wallet") and b != "upi":
        sc += 2                                          # a Wallet the bank cannot have, and the register holds elsewhere
    return sc


def _combos(cand, units, lim, most=3, cap=400):
    """Sets of two or three candidate lines whose money is exactly lim (at most cap sets)."""
    out = []
    n = len(cand)
    for x in range(n):
        for y in range(x + 1, n):
            s2 = units[cand[x]]["amount_p"] + units[cand[y]]["amount_p"]
            if s2 == lim:
                out.append((cand[x], cand[y]))
            elif most >= 3 and s2 < lim:
                for z in range(y + 1, n):
                    if s2 + units[cand[z]]["amount_p"] == lim:
                        out.append((cand[x], cand[y], cand[z]))
                        if len(out) >= cap:
                            return out
            if len(out) >= cap:
                return out
    return out


def _duplicate(its, extra):
    """(slip, [items]) when X-ray / procedure lines are written twice for one patient and the repeats come to exactly the
    extra money (one line twice, or two lines twice -- 14-Oct, ILI knee and ILI shoulder)."""
    seen, rep = set(), []
    for s, it in its:
        k = ((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())
        if k in seen:
            rep.append((s, it))
        seen.add(k)
    if not rep or extra <= 0:
        return None
    for s, it in rep:
        if it["expect_p"] == extra:
            return s, [it]
    if sum(it["expect_p"] for _s, it in rep) == extra:
        return rep[0][0], [it for _s, it in rep]
    return None


def _who_en(name, cid):
    if name and cid:
        return "%s (%s)" % (name, cid)
    return name or (cid and "ID %s" % cid) or "—"


def _card(kind, key, amount, d, who="hand", en="", hi="", **kw):
    c = dict(kind=kind, key=key, amount=int(amount or 0), day=d, who=who, en=en, hi=hi)
    c.update(kw)
    return c


def _parchi_card(p, d):
    k = p["kind"]
    s = p.get("slip")
    no = s["slip_no"] if s else None
    nm = _who_en(p.get("name"), p.get("cid"))
    if k == "parchi_missing":
        en = "No X-ray/Proc parchi · %s · %s %s in Docterz" % (nm, SEC_EN[p["section"]], rs(p["amount"]))
        hi = "X-ray/Proc parchi nahi · %s · Docterz mein %s %s" % (nm, SEC_HI[p["section"]], rs(p["amount"]))
    elif k == "opd_missing":
        en = "No OPD parchi · %s · consultation %s in Docterz" % (nm, rs(p["amount"]))
        hi = "OPD parchi nahi · %s · Docterz mein consultation %s" % (nm, rs(p["amount"]))
    elif k == "dup_item":
        w = " + ".join(_item_word(i) for i in p["items"])
        en = "Parchi %d · %s · %s written twice (%s extra)" % (no, nm, w, rs(p["amount"]))
        hi = "Parchi %d · %s · %s do baar likha (%s zyada)" % (no, nm, w, rs(p["amount"]))
    elif k == "parchi_over":
        ps, ds = p["sums"]
        en = "Parchi %d · %s · %s: parchi %s, Docterz and the register %s" % (no, nm, SEC_EN[p["section"]], rs(ps), rs(ds))
        hi = "Parchi %d · %s · %s: parchi %s, Docterz aur register %s" % (no, nm, SEC_HI[p["section"]], rs(ps), rs(ds))
    elif k == "opd_dup":
        en = "OPD parchi %d · ID %s written twice" % (no, p["cid"])
        hi = "OPD parchi %d · ID %s do baar likha" % (no, p["cid"])
    elif k == "opd_wrong_id":
        en = "OPD parchi %d · ID %s written twice; %s has a bill and no parchi — this parchi is most likely theirs" % (
            no, p["cid"], _who_en(p.get("to_name"), p.get("to_cid")))
        hi = "OPD parchi %d · ID %s do baar likha; %s ka bill hai, parchi nahi — yeh parchi shayad unki hai" % (
            no, p["cid"], _who_en(p.get("to_name"), p.get("to_cid")))
    else:                                                # parchi_short
        ps, ds = p["sums"]
        en = "Parchi %d · %s · %s: parchi %s, Docterz %s" % (no, nm, SEC_EN[p["section"]], rs(ps), rs(ds))
        hi = "Parchi %d · %s · %s: parchi %s, Docterz %s" % (no, nm, SEC_HI[p["section"]], rs(ps), rs(ds))
    return _card("parchi", p["key"], 0, d, who="parchi", en=en, hi=hi, pkind=k, slip=s, items=p.get("items"),
                 cid=p.get("cid"), to_cid=p.get("to_cid"), section=p.get("section"))


def _counts(cards):
    c = dict(missing_p=0, missing_n=0, notfound_p=0, modes=0, parchi=0, notbilled=0, notbilled_p=0, hand=0)
    for x in cards:
        if x["kind"] == "missing":
            c["missing_p"] += x["amount"]
            c["missing_n"] += 1
        elif x["kind"] == "notfound":
            c["missing_p"] += x["amount"]
            c["notfound_p"] += x["amount"]
        elif x["kind"] == "mode":
            c["modes"] += 1
        elif x["kind"] == "parchi":
            c["parchi"] += 1
        elif x["kind"] == "notbilled":
            c["notbilled"] += 1
            c["notbilled_p"] += x["amount"]
        elif x["kind"] == "hand":
            c["hand"] += 1
    return c


def summary_en(chk):
    """His line (S962, the mock-up's artboard 5): '<day>: all matched', else the counts -- to back-date, staff fixing, not
    explained -- every part named, empty parts left out."""
    d = dm(chk["day"])
    if chk.get("state") == "no_docterz":
        return "%s: waiting for the Docterz export" % d
    if chk.get("state") == "no_register":
        return "%s: the register is not filled yet" % d
    c = chk["counts"]
    parts = []
    if chk.get("reexport"):                              # S640: staff have ticked every Docterz line -- his re-export is next
        parts.append("Re-export %s from Docterz" % d)
        if chk.get("notright"):
            parts.append("%d marked not right by staff" % chk["notright"])
    if c.get("back_n"):
        parts.append("%d to back-date" % c["back_n"])
    cs = chk.get("cards") or []
    n_staff = sum(1 for x in cs if x["who"] in ("docterz", "parchi") and not x.get("tick"))
    if n_staff:
        parts.append("staff fixing %d" % n_staff)
    if c["hand"]:
        parts.append("%d to check by hand" % c["hand"])
    left = (chk.get("top") or {}).get("left") or 0
    if left:
        parts.append("%s not explained" % rs(abs(left)) if left > 0 else "%s more in Docterz, not explained" % rs(-left))
    if chk.get("not_fixed"):
        parts.append("%d not fixed after the re-export" % chk["not_fixed"])
    return "%s: %s" % (d, " · ".join(parts) if parts else "all matched")


def summary_hi(chk):
    d = dm(chk["day"])
    if chk.get("state") == "no_docterz":
        return "%s: Docterz export abhi nahi aaya" % d
    if chk.get("state") == "no_register":
        return "%s: register abhi nahi bhara" % d
    c = chk["counts"]
    parts = []
    cs = chk.get("cards") or []
    n_staff = sum(1 for x in cs if x["who"] in ("docterz", "parchi") and not x.get("tick"))
    if n_staff:
        parts.append("%d cheez theek karni" % n_staff if n_staff == 1 else "%d cheezein theek karni" % n_staff)
    if c["hand"]:
        parts.append("%d haath se dekhni" % c["hand"])
    if c.get("back_n"):
        parts.append("%d Dr sahab ke paas" % c["back_n"])
    left = (chk.get("top") or {}).get("left") or 0
    if left:
        parts.append(("%s ka pata nahi" if left > 0 else "%s ka pata nahi (Docterz mein zyada)") % rs(abs(left)))
    return "%s: %s" % (d, " · ".join(parts) if parts else "sab mil gaya")


def is_clean(chk):
    return (chk.get("state") == "checked" and not chk["cards"] and not chk.get("backdate")
            and not (chk.get("top") or {}).get("left"))


# ---------------------------------------------------------------- ticks
def _ticks(con, d):
    out = {}
    for r in con.execute("SELECT * FROM day_check_tick WHERE day=? AND state='live' ORDER BY id", (d,)):
        out[r["key"]] = dict(r)
    return out


def add_tick(con, d, key, act, who, reason="", pick=""):
    ensure(con)
    now = _stamp()
    con.execute("UPDATE day_check_tick SET state='undone' WHERE day=? AND key=? AND state='live'", (d, key))
    cur = con.execute("INSERT INTO day_check_tick (day, key, act, reason, pick, who, at) VALUES (?,?,?,?,?,?,?)",
                      (d, key, act, reason[:40], pick[:40], who, now))
    _audit_safe(con, "day_check_tick", cur.lastrowid, "tick_" + act, None, {"day": d, "key": key, "reason": reason, "pick": pick}, who)
    con.commit()
    return cur.lastrowid


def undo_tick(con, d, key, who):
    ensure(con)
    con.execute("UPDATE day_check_tick SET state='undone' WHERE day=? AND key=? AND state='live'", (d, key))
    _audit_safe(con, "day_check_tick", 0, "tick_undo", None, {"day": d, "key": key}, who)
    con.commit()


def _audit_safe(con, table, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)     # finance_app.audit dumps them itself
    except Exception:                                    # noqa: BLE001 -- the audit never blocks the work
        pass


# ---------------------------------------------------------------- who may do what
def _user(u):
    return ((u or {}).get("user") or "").lower()


def _roles(u):
    return set((u or {}).get("roles") or [])


def _gate():
    """(u, english, err): the register's people (unit clinic) or the parchi's (unit slips); a checker reads English."""
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        u2, err2 = _require("maker", "checker", unit=SLIP_UNIT)
        if err2:
            return None, True, err
        u, err = u2, None
    return u, ("checker" in _roles(u)), None


def can_docterz(u):
    return _user(u) in DOCTERZ_USERS or "checker" in _roles(u)


def can_parchi(u):
    return _user(u) in PARCHI_USERS or "checker" in _roles(u)


# ---------------------------------------------------------------- the page
def cards_html(con, chk, u, english, msg=""):
    """The one-line cards with their buttons. Used on the check page and under the register's three records."""
    d = chk["day"]
    out = []
    if msg:
        out.append(msg)
    head = summary_en(chk) if english else summary_hi(chk)
    cls = "all_agree" if is_clean(chk) else ("waiting_bank" if chk.get("state") != "checked" else "docterz_differs")
    out.append("<p class='verdict %s'>%s</p>" % (cls, _esc(head)))
    if chk.get("state") != "checked":
        out.append("<p class='mut'>%s</p>" % ("The check runs as soon as both the register and the Docterz export of this day are in."
                                              if english else "Register aur Docterz export dono aate hi yeh jaanch apne aap chalti hai."))
        return "".join(out)
    out.append(_s962_html(con, chk, u, english))         # S962 (D1080): the day in one line, what matched, his back-date list
    groups = (("docterz", "Docterz — Shivani, Alisha, Shavez", "Docterz — Shivani, Alisha, Shavez"),
              ("parchi", "Parchi — Shavez", "Parchi — Shavez"),
              ("hand", "Check by hand", "Haath se dekhein"))
    for g, en, hi in groups:
        cs = [c for c in chk["cards"] if c["who"] == g]
        if not cs:
            continue
        out.append("<h3 class='grp'>%s</h3>" % _esc(en if english else hi))
        for c in cs:
            out.append(_one_card(con, c, u, english, d))
    out.append(_bank_html(con, d, u, english))           # S641: the bank part, as Morning match shows it
    for en, hi in chk.get("notes", []):
        out.append("<p class='mut'>%s</p>" % _esc(en if english else hi))
    out.append("<p class='mut'>%s</p>" % (
        "A tick is kept as a note; a line goes away only when the next Docterz export or the parchi shows the change."
        if english else "Tick sirf yaad ke liye hai; line tabhi hategi jab agla Docterz export ya parchi badlav dikhaye."))
    return "".join(out)


def _s962_line(chk, english):
    tp = chk.get("top") or {}
    if not tp:
        return ""
    if english:
        bits = ["Register %s" % rs(tp["reg"]), "= Docterz %s" % rs(tp["doc"])]
        if tp["nid"]:
            bits.append("+ slips not in Docterz %s" % rs(tp["nid"]))
        if tp["back"]:
            bits.append("− refunded / never taken %s" % rs(tp["back"]))
        if tp["missing"]:
            bits.append("+ Docterz entries still missing %s" % rs(tp["missing"]))
        if tp["left"]:
            bits.append(("+ %s not explained" if tp["left"] > 0 else "− %s not explained (more in Docterz)") % rs(abs(tp["left"])))
    else:
        bits = ["Register %s" % rs(tp["reg"]), "= Docterz %s" % rs(tp["doc"])]
        if tp["nid"]:
            bits.append("+ Docterz se bahar parchi %s" % rs(tp["nid"]))
        if tp["back"]:
            bits.append("− lautaye / liye hi nahi %s" % rs(tp["back"]))
        if tp["missing"]:
            bits.append("+ Docterz mein entry baaki %s" % rs(tp["missing"]))
        if tp["left"]:
            bits.append(("+ %s ka pata nahi" if tp["left"] > 0 else "− %s ka pata nahi (Docterz mein zyada)") % rs(abs(tp["left"])))
    return " ".join(bits)


def _s962_html(con, chk, u, english):
    """S962 (D1080, the mock-up's artboards 4 and 5): the day in one line; what matched (folded); his back-date list -- for the
    staff with 'Paise liye hi nahi' and 'Dr sahab ko yaad dilayein', for him a link to his page."""
    d = chk["day"]
    out = ["<p class='s962top'>%s</p>" % _esc(_s962_line(chk, english))]
    rf = chk.get("refunds") or []
    mn = chk.get("matched_n") or 0
    if mn or rf:
        head = (("✓ %d patient%s match" % (mn, "" if mn == 1 else "s")) if english else ("✓ %d mareez mil gaye" % mn))
        if rf:
            head += (" · %d refund / radd matched" % len(rf)) if english else (" · %d refund / radd mil gaya" % len(rf))
        li = []
        for r in rf:
            what = "OPD" if r["series"] == "opd" else "X-ray / procedure"
            tb = (" · %s" % ("cash" if r["t_back"] == "cash" else "UPI")) if r["t_back"] else ""
            li.append("<li>%s · %s %s%s · %s ✓</li>" % (_esc(_who_en(r["pname"], r["cid"])), what, rs(r["shown"]), tb,
                                                         _esc((REFUND_EN if english else REFUND_HI)[r["word"]])))
        out.append("<details class='s962m'><summary>%s</summary><ul>%s</ul></details>" % (_esc(head), "".join(li)))
    rows = chk.get("backdate") or []
    if not rows:
        return "".join(out)
    staff = _user(u) in PARCHI_USERS + DOCTERZ_USERS
    out.append("<h3 class='grp'>%s (%d)</h3>" % ("Your back-date list · slips not in Docterz" if english
                                                  else "Dr sahab ki back-date list · parchi hai, Docterz mein nahi", len(rows)))
    if staff:
        last = _s962_last_remind(con)
        if last:
            out.append("<p class='mut'>Yaad dilaya: %s (%s)</p>" % (_esc(str(last["at"])[5:16]), _esc((last["who"] or "").title())))
        out.append(_btn(d, "remind", "remind", "Dr sahab ko yaad dilayein"))
    for b in rows:
        txt = "%s · %s · %s%s · %s" % (_who_en(b["name"], b["cid"]), b["what_en"] if english else b["what_hi"], rs(b["amount"]),
                                        (" · " + T_EN[b["tender"]]) if (english and b["tender"]) else "",
                                        ("in the register" if b["placed"] else "NOT in the register") if english else
                                        ("Dr sahab entry karenge" if b["placed"] else "register mein bhi nahi"))
        btn = ""
        if staff and b.get("slip_id") and not b["placed"]:   # the register holds a placed row's money: never 'not taken' 
            btn = _btn(d, b["key"], "nidfree", "Paise liye hi nahi", "x",
                       "<input type='hidden' name='slip' value='%d'><input type='hidden' name='kind' value='%s'>" % (b["slip_id"], _esc(b["kind"])))
        out.append("<div class='cline'><span class='ct'>%s</span><span class='cb'>%s</span></div>" % (_esc(txt), btn))
    if english:
        out.append("<p class='navrow'><a class='tb' href='%s'>Open your list (Entered / Not entering / Free / Wrong slip)</a></p>" % NID_PAGE)
    else:
        out.append("<p class='mut'>Yeh apne aap Dr sahab ki list par jaati hain — Cash / UPI kuch nahi bharna (register mein likha hai). "
                   "Sirf jab paise liye hi nahi, ek tap.</p>")
    return "".join(out)


def _s962_act(con, d, chk, a, f, u, who, english):
    """S962: the staff's two taps on his back-date list. -> (ok, err)."""
    if who not in PARCHI_USERS + DOCTERZ_USERS:          # the named staff only (cold review)
        return "", ("Not permitted." if english else "Aapke liye nahi.")
    rows = chk.get("backdate") or []
    if a == "nidfree":
        try:
            sid = int(f.get("slip") or 0)
        except (TypeError, ValueError):
            sid = 0
        kind = (f.get("kind") or "").strip()
        if not any(b.get("slip_id") == sid and b["kind"] == kind and not b["placed"] for b in rows):
            return "", ("This line has already changed — the page is fresh now." if english else "Yeh line badal chuki hai — page naya hai.")
        import not_in_docterz                            # noqa: PLC0415
        try:
            not_in_docterz.mark(con, who, sid, kind, "free")
        except not_in_docterz.MarkError as ex:
            return "", str(ex)
        return ("Noted: money never taken." if english else "Likh liya: paise liye hi nahi."), ""
    if not rows:
        return "", ("The list is empty." if english else "List khaali hai.")
    ensure(con)
    con.commit()
    con.execute("BEGIN IMMEDIATE")                       # cold review: two taps at once -- one push
    last = _s962_last_remind(con)
    now = _now()                                         # the clock add_tick stamps with
    if last:
        try:
            at = dt.datetime.strptime(str(last["at"])[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            at = None
        if at is not None and now - at < dt.timedelta(hours=REMIND_GAP_H):
            con.rollback()
            return "", "Pehle hi yaad dilaya — %s (%s). %d ghante mein ek baar." % (str(last["at"])[11:16], (last["who"] or "").title(), REMIND_GAP_H)
    cur = con.execute("INSERT INTO day_check_tick (day, key, act, reason, pick, who, at) VALUES (?,?,?,?,?,?,?)",
                      (d, "remind", "remind", "sending", str(len(rows)), who, _stamp()))
    tid = cur.lastrowid
    con.commit()
    body = "%s: %d slip%s not in Docterz — your back-date list (a reminder from %s)" % (dm(d), len(rows), "" if len(rows) == 1 else "s",
                                                                                     who.title())   # his phone: English
    sent, why = _s962_push(con, ["manoj"], "Back-date list", body, NID_PAGE, "s962-remind")
    con.execute("UPDATE day_check_tick SET reason=? WHERE id=?", ("sent" if sent else "not sent", tid))
    _audit_safe(con, "day_check_tick", tid, "tick_remind", None, {"day": d, "rows": len(rows), "sent": bool(sent)}, who)
    con.commit()
    return (("Dr sahab ko yaad dila diya." if sent else "Likh liya — push nahi gaya (%s)." % why), "")


def _bank_html(con, d, u, english):
    """S641: Morning match's bank words for the day (clinic_money.bank_part), the same for staff and the owner. Its flags are
    answered where they always were -- on Morning match."""
    try:
        import clinic_money                              # noqa: PLC0415
        b = clinic_money.bank_part(con, d, u)
    except Exception:                                    # noqa: BLE001
        return ""
    if not b:
        return ""
    out = ["<h3 class='grp'>%s</h3><p>%s</p>" % ("Bank" if english else "Bank", _esc(b["line"]))]
    for f in b["flags"]:
        out.append("<div class='cline'><span class='ct'>%s</span><span class='cb'><a class='tb x' href='/finance/clinic/match/%s'>%s</a></span></div>"
                   % (_esc(f["text"]), d, "Answer on Morning match" if english else "Morning match par jawab"))
    if b["waiting"]:
        out.append("<details><summary class='mut'>%s (%d)</summary><ul>%s</ul><p class='mut'>%s</p></details>" % (
            "Waiting for the bank" if english else "Bank ka intezaar", len(b["waiting"]),
            "".join("<li class='mut'>%s</li>" % _esc(n) for n in b["waiting"]),
            "Money still on its way is not a flag; it becomes one only if it has not arrived after two banking days."))
    return "".join(out)


def _btn(d, key, act, label, cls="", extra=""):
    return ("<form method='post' action='/finance/clinic/check/%s/act' class='inline'>"
            "<input type='hidden' name='key' value='%s'><input type='hidden' name='act' value='%s'>%s"
            "<button type='submit' class='tb %s'>%s</button></form>" % (d, _esc(key), act, extra, cls, _esc(label)))


def _one_card(con, c, u, english, d):
    txt = c["en"] if english else c["hi"]
    t = c.get("tick")
    btns = []
    status = ""
    if t:
        who = (t["who"] or "").title()
        word = {"added": ("Added", "Add kar diya"), "changed": ("Changed", "Badal diya"), "notright": ("Not right", "Sahi nahi"),
                "found": ("Found", "Mil gaya"), "regmistake": ("Register mistake", "Register ki galti")}.get(t["act"], (t["act"], t["act"]))
        extra = ""
        if t["act"] == "notright" and t["reason"]:
            extra = " — " + (NOT_RIGHT_EN if english else NOT_RIGHT_HI).get(t["reason"], t["reason"])
        if t["act"] == "found" and t["pick"]:
            extra = " — ID %s" % t["pick"]
        status = "<span class='tk'>✓ %s%s · %s %s · %s</span>" % (
            _esc(word[0] if english else word[1]), _esc(extra), _esc(who), _esc((t["at"] or "")[11:16]),
            "waits for the Docterz export" if english and c["who"] == "docterz" else
            ("Docterz export ka intezaar" if c["who"] == "docterz" else ("waits for the parchi" if english else "parchi ka intezaar")))
        if _user(u) == (t["who"] or "").lower() or "checker" in _roles(u):
            btns.append(_btn(d, c["key"], "undo", "Undo" if english else "Wapas", "x"))
    elif c["who"] == "docterz" and can_docterz(u):
        if c.get("not_fixed"):                           # S640: ticked, re-exported, still there
            nf = c["not_fixed"]
            status = "<span class='tk' style='color:#9c2a20'>%s</span>" % _esc(
                ("Not fixed — the Docterz export after %s's tick (%s) still shows it" if english else
                 "Theek nahi hua — %s ke tick (%s) ke baad ke Docterz export mein bhi hai") % ((nf["who"] or "").title(), (nf["at"] or "")[5:16]))
        if c["kind"] in ("missing", "notbilled"):
            btns.append(_btn(d, c["key"], "added", "Added" if english else "Add kar diya"))
            if c.get("slip") is not None and _SA() is not None:
                btns.append(_btn(d, c["key"], "notpaid", "Not paid" if english else "Paise nahi liye", "x",
                                 "<input type='hidden' name='slip' value='%d'>" % c["slip"]["id"]))
                if c.get("item") is not None and c["item"]["kind"] in ("xray", "proc"):
                    sa = _SA()
                    sel = "".join("<option value='%s'>%s</option>" % (k, _esc(e if english else h)) for k, h, e in sa.REASONS)
                    btns.append(_btn(d, c["key"], "free", "Free", "x",
                                     "<input type='hidden' name='slip' value='%d'><input type='hidden' name='item' value='%d'>"
                                     "<select name='reason' class='rs'>%s</select>" % (c["slip"]["id"], c["item"]["id"], sel)))
        elif c["kind"] == "mode":
            btns.append(_btn(d, c["key"], "changed", "Changed" if english else "Badal diya"))
            sel = "".join("<option value='%s'>%s</option>" % (k, _esc(e if english else h)) for k, h, e in NOT_RIGHT)
            btns.append(_btn(d, c["key"], "notright", "Not right" if english else "Sahi nahi", "x",
                             "<select name='reason' class='rs'>%s</select>" % sel))
        elif c["kind"] == "notfound":
            opts = _day_people(con, d)
            sel = "".join("<option value='%s'>%s</option>" % (_esc(cid), _esc("%s (%s)" % (nm, cid))) for cid, nm in opts)
            btns.append(_btn(d, c["key"], "found", "Found it" if english else "Mil gaya", "",
                             "<select name='pick' class='rs'>%s</select>" % sel))
            btns.append("<a class='tb x' href='/finance/clinic/register/%s'>%s</a>" % (d, "Register mistake" if english else "Register ki galti"))
            if can_parchi(u) and _late_ok(d):                                # S968: money with no parchi -- the parchi too
                btns.append("<a class='tb' href='/finance/slips?s=%s&day=%s'>%s</a>" % (
                    "opd" if c.get("section") == "consult" else "xp", d, "Make the parchi" if english else "Parchi banayein"))
    elif c["who"] == "parchi" and can_parchi(u):
        s = c.get("slip")
        late_ok = _late_ok(d)
        if c.get("pkind") == "dup_item":
            btns.append(_btn(d, c["key"], "dupitem", "Remove duplicate" if english else "Duplicate hatao"))
        elif c.get("pkind") == "opd_wrong_id":
            btns.append(_btn(d, c["key"], "fixid", ("Make it ID %s" if english else "ID %s karein") % c["to_cid"], "",
                             "<input type='hidden' name='slip' value='%d'><input type='hidden' name='to' value='%s'>"
                             % (s["id"], _esc(c["to_cid"]))))
            btns.append(_btn(d, c["key"], "dupslip", "Remove duplicate" if english else "Duplicate hatao", "x",
                             "<input type='hidden' name='slip' value='%d'>" % s["id"]))
        elif c.get("pkind") == "opd_dup":
            btns.append(_btn(d, c["key"], "dupslip", "Remove duplicate" if english else "Duplicate hatao", "",
                             "<input type='hidden' name='slip' value='%d'>" % s["id"]))
        elif c.get("pkind") in ("opd_missing", "parchi_missing"):
            if late_ok:
                series = "opd" if c.get("pkind") == "opd_missing" else "xp"
                btns.append("<a class='tb' href='/finance/slips?s=%s&day=%s'>%s</a>" % (series, d, "Fix" if english else "Theek karein"))
        elif c.get("pkind") in ("parchi_short", "parchi_over") and s is not None and late_ok:
            btns.append(_btn(d, c["key"], "rewrite", "Fix" if english else "Theek karein", "",
                             "<input type='hidden' name='slip' value='%d'>" % s["id"]))
        if not late_ok and c.get("pkind") in ("opd_missing", "parchi_missing", "parchi_short", "parchi_over", "dup_item", "opd_dup", "opd_wrong_id"):
            status = "<span class='mut'>%s</span>" % ("older than 7 days — the parchi can no longer be changed"
                                                      if english else "7 din se purani — parchi ab nahi badal sakti")
    return "<div class='cline'><span class='ct'>%s</span>%s<span class='cb'>%s</span></div>" % (_esc(txt), status, "".join(btns))


def _export_at(con, d):
    try:
        r = con.execute("SELECT taken_at FROM clinic_day_revenue WHERE business_date=?", (d,)).fetchone()
        return (r[0] or "") if r else ""
    except Exception:                                    # noqa: BLE001
        return ""


STAFF_DAYS = 7                                           # the staff see a week of days: the parchi's own late window


def staff_lines(con, u):
    """S640 (D776 stage 3): what one login has to correct, the day before today back STAFF_DAYS days (never before the lists'
    floor): the Docterz lines for Shivani, Alisha, Shavez; the parchi lines for Shavez and Bhati. A line ticked and waiting for
    the re-export is not theirs to do; a line the re-export did not fix is, again. {open, text, days} -- text names them."""
    who = _user(u)
    want = set()
    if who in DOCTERZ_USERS:
        want.add("docterz")
    if who in PARCHI_USERS:
        want.add("parchi")
    if not want:
        return dict(open=0, text="", days=[])
    floor = "2026-10-01"
    try:
        import aaj_floor                                 # noqa: PLC0415 -- the lists' own floor, when it says one
        floor = aaj_floor.floor_for(con, _require, u) or floor
    except Exception:                                    # noqa: BLE001
        pass
    today = dt.date.today()
    n, bits, days = 0, [], []
    for i in range(1, STAFF_DAYS + 1):
        d = (today - dt.timedelta(days=i)).isoformat()
        if d < str(floor):
            break
        chk = check_day(con, d)
        if chk.get("state") != "checked":
            continue
        mine = [c for c in chk["cards"] if c["who"] in want and not c.get("tick")]
        if not mine:
            continue
        days.append(d)
        n += len(mine)
        bits.append("%s: %s" % (dm(d), " | ".join(("Phir se — " if c.get("not_fixed") else "") + c["hi"] for c in mine)))
    text = ""
    if n:
        text = "Din ki galtiyan (%d) — %s" % (n, " ;  ".join(bits))
        if len(text) > 600:
            text = text[:590].rsplit(" ", 1)[0] + " …"
    return dict(open=n, text=text, days=days)


@bp.route("/finance/clinic/check/api/mine")
def api_mine():
    u, english, err = _gate()
    if err:
        return err
    con = _db()
    _CR()._ensure(con)
    ensure(con)
    from flask import jsonify                            # noqa: PLC0415
    return jsonify(ok=True, **staff_lines(con, u))


@bp.route("/finance/clinic/check/mine")
def mine():
    """The page a staff line opens: the oldest day that still has lines for this login (else yesterday)."""
    u, english, err = _gate()
    if err:
        return redirect("/finance/clinic/register", code=302)
    con = _db()
    _CR()._ensure(con)
    ensure(con)
    s = staff_lines(con, u)
    days = s["days"]
    if not days and english:                             # S641: his tile -- every kind of line, the last STAFF_DAYS days
        for i in range(1, STAFF_DAYS + 1):
            dd = (dt.date.today() - dt.timedelta(days=i)).isoformat()
            ck = check_day(con, dd)
            if ck.get("state") == "checked" and ck["cards"]:
                days.append(dd)
    d = days[-1] if days else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/check/%s#check" % d, code=302)


def _late_ok(d):
    SL = _SL()
    if SL is None:
        return False
    try:
        return SL._late_day(d) == d
    except Exception:                                    # noqa: BLE001
        return False


def _day_people(con, d):
    seen, out = set(), []
    for r in con.execute("SELECT clinic_id, patient FROM clinic_day_line WHERE business_date=? ORDER BY section, sn", (d,)):
        cid = str(r["clinic_id"] or "")
        if cid and cid not in seen:
            seen.add(cid)
            out.append((cid, (r["patient"] or "").strip()))
    return out


@bp.route("/finance/clinic/check/<date>")
def page(date):
    u, english, err = _gate()
    CR = _CR()
    if err:
        return CR._shell("Day check", CR._denied())
    if not _iso_ok(date):
        return CR._shell("Day check", "<div class='card'><h2>Not a date.</h2></div>")
    con = _db()
    CR._ensure(con)
    ensure(con)
    chk = check_day(con, date)
    msg = ""
    if request.args.get("ok"):
        msg = "<div class='ok'>%s</div>" % _esc(request.args.get("ok"))
    if request.args.get("err"):
        msg = "<div class='bad'>%s</div>" % _esc(request.args.get("err"))
    t = CR.three_way(con, date)
    body = (CR._compare_html(t, date).replace("<details class=\"card\">", "<details class=\"card\" open>", 1)
            + "<div class='card' id='check'><h2>%s</h2>%s</div>" % (
                ("The day's corrections — %s" if english else "Din ki galtiyan — %s") % dm(date), cards_html(con, chk, u, english, msg))
            + "<p class='navrow noprint'><a class='btn' href='/finance/clinic/register/%s'>%s</a>"
              "<a class='btn' href='/finance/clinic/register/list'>%s</a></p>" % (
                date, "the register of this day" if english else "is din ka register", "all days" if english else "sab din")
            + STYLE)
    return CR._shell(("Day check — %s" if english else "Din ki jaanch — %s") % dm(date), body)


@bp.route("/finance/clinic/check/<date>/act", methods=["POST"])
def act(date):
    u, english, err = _gate()
    if err or not _iso_ok(date):
        return redirect("/finance/clinic/register", code=303)
    con = _db()
    ensure(con)
    f = request.form
    key, a, who = (f.get("key") or "")[:120], f.get("act") or "", _user(u)
    back = "/finance/clinic/check/%s" % date

    def done(ok="", er=""):
        q = ("?ok=" + _q(ok)) if ok else (("?err=" + _q(er)) if er else "")
        return redirect(back + q + "#check", code=303)

    chk = check_day(con, date)
    card = next((c for c in chk["cards"] if c["key"] == key), None)
    if a in ("nidfree", "remind"):                     # S962: the staff's two taps on his back-date list
        try:
            return done(*_s962_act(con, date, chk, a, f, u, who, english))
        except Exception as ex:                          # noqa: BLE001 -- a locked database or a refusal reads as it is
            try:
                con.rollback()
            except Exception:                            # noqa: BLE001
                pass
            return done(er=str(ex)[:200])
    if a == "undo":
        undo_tick(con, date, key, who)
        return done("Undone." if english else "Wapas le liya.")
    if card is None:
        return done(er="This line has already changed — the page is fresh now." if english else "Yeh line badal chuki hai — page naya hai.")
    try:
        if a in ("added", "changed", "notright", "found") and card["who"] == "docterz" and can_docterz(u):
            reason = f.get("reason") or ""
            if a == "notright" and reason not in NOT_RIGHT_EN:
                reason = "other"
            add_tick(con, date, key, a, who, reason=reason, pick=(f.get("pick") or "")[:12])
            return done("Noted. The line goes when the Docterz export shows it." if english
                        else "Likh liya. Docterz export mein dikhte hi line hat jayegi.")
        if a in ("notpaid", "free") and card["who"] == "docterz" and can_docterz(u):
            sa = _SA()
            sid = int(f.get("slip") or 0)
            if a == "free":
                sa.add_discount(con, who, sid, int(f.get("item") or 0), None, True, f.get("reason") or "other", note="day check")
            else:
                sa.add_cancel(con, who, sid, (card.get("cid") or ""), "never_taken", note="day check")
            return done("Sent for approval." if english else "Manzoori ke liye gaya.")
        if card["who"] == "parchi" and can_parchi(u):
            if a == "dupitem":
                return done(*_remove_items(con, card, who, english))
            if a == "dupslip":
                return done(*_void_slip(con, card, int(f.get("slip") or 0), who, english, "duplicate (day check)"))
            if a == "fixid":
                return done(*_fix_id(con, card, int(f.get("slip") or 0), f.get("to") or "", who, english))
            if a == "rewrite":
                ok, er = _void_slip(con, card, int(f.get("slip") or 0), who, english, "written again (day check)")
                if er:
                    return done(er=er)
                s = card["slip"]
                return redirect("/finance/slips?s=xp&day=%s&no=%d" % (date, s["slip_no"]), code=303)
    except Exception as ex:                              # noqa: BLE001 -- slip_adjust's own refusals read as they are
        return done(er=str(ex)[:200])
    return done(er="Not permitted." if english else "Aapke liye nahi.")


def _q(s):
    from urllib.parse import quote                       # noqa: PLC0415
    return quote(str(s), safe="")


def _remove_items(con, card, who, english):
    """Remove the repeated line(s) the check found -- exactly those rows, each audited whole."""
    its = card.get("items") or []
    if not its or not _late_ok(card["day"]):
        return "", ("Not this line." if english else "Yeh line nahi.")
    n = 0
    for it in its:
        row = con.execute("SELECT * FROM slip_item WHERE id=?", (it["id"],)).fetchone()
        if row is None:
            continue
        con.execute("DELETE FROM slip_item WHERE id=?", (it["id"],))
        con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, _stamp(), row["slip_id"]))
        _audit_safe(con, "slip_item", it["id"], "slip_item_removed_duplicate", dict(row), None, who)
        n += 1
    con.commit()
    if not n:
        return "", ("Already removed." if english else "Pehle hi hat chuki.")
    return ("Duplicate removed." if english else "Duplicate hata diya."), ""


def _void_slip(con, card, slip_id, who, english, why):
    s = card.get("slip")
    if s is None or s["id"] != slip_id:
        return "", ("Not this parchi." if english else "Yeh parchi nahi.")
    if not _late_ok(card["day"]):
        return "", ("Older than 7 days." if english else "7 din se purani.")
    row = con.execute("SELECT * FROM slip WHERE id=? AND state='ok'", (slip_id,)).fetchone()
    if row is None:
        return "", ("Already changed." if english else "Pehle hi badal chuki.")
    con.execute("UPDATE slip SET state='void', note=?, updated_by=?, updated_at=? WHERE id=?", (why, who, _stamp(), slip_id))
    _audit_safe(con, "slip", slip_id, "slip_void", {"state": "ok"}, {"state": "void", "why": why}, who)
    con.commit()
    return ("Parchi %d taken off." % row["slip_no"] if english else "Parchi %d hata di." % row["slip_no"]), ""


def _fix_id(con, card, slip_id, to, who, english):
    s = card.get("slip")
    to = "".join(ch for ch in str(to) if ch.isalnum())[:12]
    if s is None or s["id"] != slip_id or not to or to != str(card.get("to_cid") or ""):
        return "", ("Not this parchi." if english else "Yeh parchi nahi.")
    row = con.execute("SELECT * FROM slip WHERE id=? AND state='ok'", (slip_id,)).fetchone()
    if row is None:
        return "", ("Already changed." if english else "Pehle hi badal chuki.")
    con.execute("UPDATE slip SET clinic_id=?, name_seen='', updated_by=?, updated_at=? WHERE id=?", (to, who, _stamp(), slip_id))
    _audit_safe(con, "slip", slip_id, "slip_id_fixed", {"clinic_id": row["clinic_id"]}, {"clinic_id": to, "via": "day check"}, who)
    con.commit()
    return ("Parchi %d now carries ID %s." % (row["slip_no"], to) if english else "Parchi %d par ab ID %s." % (row["slip_no"], to)), ""


STYLE = """<style>
h3.grp{font-size:18px;margin:16px 0 6px;color:var(--accent)}
.cline{border:2px solid var(--line);border-radius:9px;padding:10px 12px;margin:0 0 10px;background:#fff}
.cline .ct{display:block;font-size:18px;line-height:1.45;overflow-wrap:anywhere}
.cline .tk{display:block;color:#2c6e2f;font-size:16px;margin-top:4px}
.cline .cb{display:block;margin-top:6px}
.cline form.inline{display:inline-block;margin:6px 8px 0 0}
button.tb,a.tb{display:inline-block;background:var(--accent);color:#fff;border:0;border-radius:9px;padding:11px 16px;
 font-size:17px;font-weight:600;cursor:pointer;text-decoration:none;min-height:48px}
button.tb.x,a.tb.x{background:var(--paper);color:var(--accent);border:2px solid var(--accent)}
select.rs{display:block;width:100%;font-size:18px;min-height:50px;padding:6px;border:2px solid #5b6b76;border-radius:8px;
 margin:0 0 6px;background:#fff;color:var(--ink)}
.cline form.inline:has(select){display:block;margin-right:0}
.cline a.tb{margin:10px 8px 0 0}
@media (max-width:620px){button.tb,a.tb{padding:11px 12px}}
p.s962top{font-size:18px;font-weight:600;line-height:1.5;margin:8px 0 10px;overflow-wrap:anywhere}
details.s962m{margin:0 0 12px}details.s962m summary{font-size:17px;color:#2c6e2f;cursor:pointer}
</style>"""
