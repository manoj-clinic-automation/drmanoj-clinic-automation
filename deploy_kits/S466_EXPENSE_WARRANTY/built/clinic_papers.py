#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clinic_papers.py -- S464_CLINIC_PAPERS + S465_PAPERS_JOIN + S466_EXPENSE_WARRANTY (D664, the owner 03-Oct-2026).

THE OWNER'S RULING
    Papers scanned at reception that are not pharmacy purchases need their own home. CLINIC CONSUMABLES is the main
    group, with three sub-groups: Procedure room, X-ray films (two sizes) and Others (stationery and the rest). The
    sub-group is OPTIONAL at scanning; Shavez or he sets it later, and it must be easy: the system suggests it from
    the supplier AND the items, one tap to confirm or skip. The supplier alone never decides -- Yuvika sells orthotics
    to the pharmacy on printed bills and procedure-room goods on handwritten slips. Goods like the inverter battery
    belong to the "Dr MK expense" lane.

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded import at its foot: if this file cannot load,
    the asset app runs exactly as before. It adds ONE column, bills.subgroup, and four addresses:
        GET  /papers               the papers to sort, each with a suggestion: Yes / Change / Skip
        GET  /papers/<id>          one paper and its group
        POST /bills/<id>/subgroup  set or clear the group (audited)
        GET  /papers/month         clinic consumables for a month, by group
    S465 -- ONE PURCHASE = ONE PDF (his ruling: the bill and its warranty cards together). For papers that were
    scanned separately:
        GET  /papers/<id>/join     the papers scanned beside this one; the blank ones after it come ticked
        POST /papers/<id>/join     joins the ticked papers into this one: one PDF under THIS number
        POST /papers/<id>/unjoin   undoes the last join of this paper
    A joined paper keeps its number and reads "a page of B-xxxx" -- the shape the app's own forgotten-page check
    (S441) already uses: status 'rejected' + page_of, both original files kept on disk, the merged PDF a new file.
    The merge itself is S441's (one PDF writer in the estate); what was joined is kept in d664_join so it can be undone.
    S466 -- A DR MK EXPENSE KEEPS ITS WARRANTY (his ruling: the inverter battery is a Dr MK expense, and the renewals
    list must remind him of the warranty date):
        POST /papers/<id>/warranty  what it is, warranty till, remind 30 days / 7 days before / never; or remove it
    The card is on the paper's own page, on the Dr MK expense lane only. What is saved lives in d664_warranty and
    shows, to the OWNER only, on the asset app's own "Renewals & warranties" page (one hook there, behind
    'is defined'): inside its reminder window by default, every warranty under "show all upcoming". A warranty that
    has ended is never "overdue" -- nothing is owed -- and drops off 60 days after its date. /api/due is NOT touched,
    so nothing about a warranty goes out on WhatsApp. The date is typed from the card: no scan reads it today.
    Owner and manager only (the asset app's own checker_required). Staff are asked nothing new and see nothing new.

WHAT IT DELIBERATELY DOES NOT DO
    It adds no lane, changes no lane's meaning and never touches a scan that is ON the pharmacy lane (it is neither
    grouped nor joined): a move between lanes goes through the asset app's own /bills/<id>/lane, with its rules and
    its audit line. A suggestion is worked out when the page
    is shown and stored nowhere; nothing is sorted until a person taps. Standard library and Flask only.
"""
import datetime
import re
import secrets
import sqlite3

from flask import abort, flash, g, redirect, render_template_string, request, url_for
from markupsafe import Markup

VERSION = "S466.1"
DASH = chr(0x2014)
REMIND = ((30, "30 days before"), (7, "7 days before"), (0, "No reminder"))
ENDED_KEEP_DAYS = 60          # an ended warranty stays under "show all upcoming" this long, then drops off
AR = None                     # the asset app's module, handed in by init()

SUB = {                       # what bills.subgroup may hold, and its words on a page
    "procedure":  "Procedure room",
    "xray":       "X-ray films",
    "xray_small": "X-ray films · small film",
    "xray_11x14": "X-ray films · 11 x 14",
    "others":     "Others",
}
GROUP_OF = {"procedure": "procedure", "xray": "xray", "xray_small": "xray", "xray_11x14": "xray", "others": "others"}
GROUPS = (("procedure", "Procedure room", "fibre cast, roller bandage, cotton, tape, betadine"),
          ("xray", "X-ray films", "small film or 11 x 14"),
          ("others", "Others", "stationery and the rest"))

# The words a suggestion is made from. Each list can be lengthened from the app's settings table without a new kit:
# key d664.words.<name>, a comma-separated list (added to these, never replacing them).
WORDS = {
    "expense":   ["battery", "batteries", "inverter", "invertor", "ups", "exide", "luminous", "amaron", "okaya",
                  "microtek", "warranty card", "warranty"],
    "orthotic":  ["brace", "belt", "knee cap", "kneecap", "cervical collar", "collar", "splint", "support", "sling",
                  "walker", "crutch", "crutches", "heel cup", "insole", "corset", "immobilizer", "immobiliser",
                  "wrist binder", "ankle binder", "abdominal binder"],
    "xray":      ["x-ray", "x ray", "xray", "film", "films", "fuji", "konica", "agfa", "carestream", "developer",
                  "fixer", "dhl", "di-hl", "dihl", "dry film"],      # S465: the clinic's film is billed as "DHL 8*10 150 SH"
    "xray_11x14": ["11x14", "11 x 14", "11*14", "11 by 14", "14x11", "14 x 11"],
    "xray_small": ["8x10", "8 x 10", "8*10", "10x12", "10 x 12", "10*12", "small film"],
    "procedure": ["fibre cast", "fiber cast", "fibrecast", "fibercast", "cast", "plaster of paris", "plaster", "pop",
                  "roller bandage", "bandage", "bandages", "cotton", "zigzag", "zig zag", "gauze", "gamjee",
                  "tape", "micropore", "leukoplast", "betadine", "povidone", "scrub", "lignocaine", "xylocaine",
                  "lox", "syringe", "syringes", "needle", "needles", "gloves", "glove", "spirit", "savlon",
                  "dressing", "crepe", "soft roll", "softroll", "stockinette", "stockinet"],
    "stationery": ["stationery", "stationary", "a4", "paper", "pen", "pens", "register", "file", "files", "folder",
                   "stapler", "staples", "toner", "cartridge", "ink", "envelope", "envelopes", "stamp pad",
                   "letterhead", "letter head", "prescription pad", "visiting card", "printing"],
    "procedure_supplier": ["agarwal surg", "agrawal surg", "aggarwal surg", "yuvika"],
    # S465: medicine bills were found on the clinic lane (four of the first 29 real papers)
    "medicine":  ["tab", "tabs", "tablet", "tablets", "cap", "caps", "capsule", "capsules", "syp", "syrup", "susp",
                  "suspension", "ointment", "oint", "sachet", "sachets"],
    "medicine_supplier": ["pharma", "pharmaceutical", "pharmaceuticals", "drug house", "drugs", "medical agencies",
                          "medical agency", "medicine", "medicines"],
}
PAGE_N = 30


# ---------------------------------------------------------------------------------------------- the database's part
def ensure(db):
    """ONE additive column, idempotent. Two workers start at once, so 'duplicate column' from the second is normal."""
    cols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    if "subgroup" not in cols:
        try:
            db.execute("ALTER TABLE bills ADD COLUMN subgroup TEXT")
        except sqlite3.OperationalError as ex:
            if "duplicate column" not in str(ex).lower():
                raise
    # S466: a Dr MK expense's warranty. One row per paper.
    db.execute("CREATE TABLE IF NOT EXISTS d664_warranty(bill_id INTEGER PRIMARY KEY, what TEXT NOT NULL, "
               "till TEXT NOT NULL, remind_days INTEGER NOT NULL DEFAULT 30, set_by TEXT, set_at TEXT)")
    # S465: what was joined, so it can be undone. One row per page; the rows of one tap share a batch.
    db.execute("CREATE TABLE IF NOT EXISTS d664_join(id INTEGER PRIMARY KEY, batch TEXT NOT NULL, head_id INTEGER NOT NULL, "
               "page_id INTEGER NOT NULL, at TEXT NOT NULL, who TEXT, head_before TEXT, head_after TEXT, "
               "merged INTEGER NOT NULL DEFAULT 0, head_total_before REAL, total_copied INTEGER NOT NULL DEFAULT 0, "
               "page_status TEXT, page_reject_reason TEXT, page_approved_by TEXT, page_approved_at TEXT, "
               "undone_at TEXT, undone_by TEXT)")
    db.commit()


def _cols(db):
    return {r[1] for r in db.execute("PRAGMA table_info(bills)")}


def _live(db, alias="b"):
    """The papers that count: on the clinic lane, not rejected, not a duplicate, not a page joined into another."""
    w = ("COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved') AND %s.dup_of IS NULL"
         % (alias, alias, alias))
    if "page_of" in _cols(db):
        w += " AND %s.page_of IS NULL" % alias
    return w


def _words(db, name):
    out = list(WORDS[name])
    try:
        r = db.execute("SELECT value FROM settings WHERE key=?", ("d664.words." + name,)).fetchone()
        if r and r[0]:
            out += [w.strip().lower() for w in str(r[0]).split(",") if w.strip()]
    except sqlite3.Error:
        pass
    return out


def _hits(text, words, whole=True):
    """The words of the list that stand in the text as whole words (so 'cast' never matches 'broadcast').
    whole=False is for a SUPPLIER's name, where the list holds the start of a word: 'agarwal surg' must find
    'Agarwal Surgicals' (S465 -- as whole words it never did), 'pharma' must find 'Pharmaceuticals'."""
    got = []
    for w in words:
        if re.search(r"(?<![a-z0-9])" + re.escape(w) + (r"(?![a-z0-9])" if whole else ""), text) and w not in got:
            got.append(w)
    return [w for w in got if not any(w != x and w in x for x in got)]      # 'cast' is not said beside 'fibre cast'


# ---------------------------------------------------------------------------------------------- the suggestion
def suggest(db, vendor, items, has_bill_no, has_total):
    """What this paper looks like, from the supplier AND the words read on it.
    -> dict(kind='sub', value=<subgroup>, label, why)   a clinic sub-group, one tap to confirm
       dict(kind='lane', value='owner_expense', label, why)   not a clinic consumable at all
       dict(kind='note', why)                           something worth saying, nothing to tap
       None                                             nothing to suggest -- the person chooses"""
    v = re.sub(r"\s+", " ", (vendor or "").lower()).strip()
    t = re.sub(r"\s+", " ", (items or "").lower()).strip()
    both = (v + " " + t).strip()
    ex = _hits(both, _words(db, "expense"))
    if ex:
        return dict(kind="lane", value="owner_expense", label="Dr MK expense",
                    why="the words read on it: " + ", ".join(ex[:3]))
    orth = _hits(t, _words(db, "orthotic"))
    xr = _hits(t, _words(db, "xray"))
    pr = _hits(t, _words(db, "procedure"))
    st = _hits(t, _words(db, "stationery"))
    med = _hits(t, _words(db, "medicine"))
    medsup = _hits(v, _words(db, "medicine_supplier"), whole=False)
    if not xr and not pr and ((med and medsup) or len(med) >= 2 or (medsup and t and not st and not orth)):
        # S465: medicines are a pharmacy purchase scanned on the wrong lane -- the move is the app's own door
        return dict(kind="lane", value="pharmacy", label="Pharmacy purchase",
                    why=("the words read on it: " + ", ".join(med[:3])) if med else "the supplier's name (" + ", ".join(medsup[:2]) + ")")
    if xr and len(xr) >= len(pr):
        size = ("xray_11x14" if _hits(t, _words(db, "xray_11x14")) else
                "xray_small" if _hits(t, _words(db, "xray_small")) else "xray")
        return dict(kind="sub", value=size, label=SUB[size], why="the words read on it: " + ", ".join(xr[:3]))
    if pr and len(pr) >= len(orth):
        return dict(kind="sub", value="procedure", label=SUB["procedure"],
                    why="the words read on it: " + ", ".join(pr[:3]))
    if orth:
        return dict(kind="note", why="the words read on it (%s) look like orthotics — a pharmacy purchase; "
                                     "open it to move it, if so" % ", ".join(orth[:3]))
    if st:
        return dict(kind="sub", value="others", label=SUB["others"], why="the words read on it: " + ", ".join(st[:3]))
    sup = _hits(v, _words(db, "procedure_supplier"), whole=False)
    if sup:
        if not has_bill_no and not has_total:
            # S465: a handwritten slip is known by what is NOT on it -- no bill number, no amount. Its items often
            # read as garble ("Bandye" for bandage), so the rule no longer waits for the items to be empty.
            return dict(kind="sub", value="procedure", label=SUB["procedure"],
                        why="the supplier, and no bill number or amount on it — this supplier's handwritten "
                            "slips are procedure-room goods")
        return dict(kind="sub", value="procedure", label=SUB["procedure"],
                    why="the supplier (no item on it names a group — look at the paper before saying yes)")
    return None


def _items_text(db, bid):
    return " ; ".join(r[0] for r in db.execute(
        "SELECT item_name FROM bill_items WHERE bill_id=? ORDER BY id", (bid,)) if r[0])


def _paper(db, b):
    """One row for a page: the bill, what was read, and the suggestion."""
    items = _items_text(db, b["id"])
    read_nothing = not (b["bill_no"] or b["total_amount"] is not None or items)
    reading = (b["ocr_status"] or "") == "reading"
    s = None if reading else suggest(db, b["vendor"], items, bool(b["bill_no"]), b["total_amount"] is not None)
    if s and s["kind"] == "lane" and b["status"] == "approved":
        s = dict(kind="note", why="it looks like %s (%s), but it is already approved on the clinic lane, "
                                  "so it stays there — give it a group" % (s["label"], s["why"]))
    blank = _is_blank(b, items)
    after, head = [], None
    if _can_join(db) and not reading and _head_ok(b):
        if blank:
            head = _head_of_blank(db, b)
        else:
            after = _blanks_after(db, b)
    return dict(b=b, words=items, read_nothing=read_nothing, reading=reading, s=s,      # never a key named "items": a page would get the dict's own method
                stamp=b["stamp_no"] or ("#%d" % b["id"]), group=(b["subgroup"] or ""),
                blank=blank, after=after, after_text=_and([_stamp(x) for x in after]), head=head,
                njoined=(len(_joined(db, b["id"])) if _can_join(db) else 0),
                head_stamp=(_stamp(head) if head else ""))


# ---------------------------------------------------------------------------------------------- S465: one purchase, one PDF
NEAR = 6            # how far, in scans, a page may sit from its bill


def _stamp(b):
    return b["stamp_no"] or ("#%d" % b["id"])


def _and(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else (", ".join(xs[:-1]) + " and " + xs[-1]) if xs else ""


def _can_join(db):
    return "page_of" in _cols(db)


def _is_blank(b, items=None):
    """Nothing was read on it: no supplier, no number, no amount, no item -- a warranty card, or one more page."""
    return not ((b["vendor"] or "").strip() or (b["bill_no"] or "").strip() or b["total_amount"] is not None or items)


def _head_ok(b):
    """May other papers be joined INTO this one? Never a pharmacy scan, a rejected paper, a duplicate or a page."""
    return (b["status"] in ("draft", "approved", "captured") and (b["lane"] or "clinic") != "pharmacy"
            and not b["dup_of"] and not b["page_of"])


def _page_ok(db, b, head):
    """May this paper become a page of that one?"""
    if b["id"] == head["id"] or b["status"] not in ("draft", "captured") or (b["lane"] or "clinic") == "pharmacy":
        return False
    if b["dup_of"] or b["page_of"]:
        return False
    return db.execute("SELECT 1 FROM bills WHERE page_of=? LIMIT 1", (b["id"],)).fetchone() is None


def _blanks_after(db, head):
    """The unbroken run of blank scans right after this paper -- B-0106 and B-0107 after B-0105's bill."""
    out = []
    for b in db.execute("SELECT b.* FROM bills b WHERE b.id>? AND b.id<=? AND b.status<>'rejected' ORDER BY b.id",
                        (head["id"], head["id"] + NEAR)):
        if not (_page_ok(db, b, head) and _is_blank(b, _items_text(db, b["id"])) and (b["ocr_status"] or "") != "reading"):
            break
        out.append(b)
    return out


def _head_of_blank(db, blank):
    """For a blank scan: the paper it was scanned right after, when only blank scans lie between them."""
    for b in db.execute("SELECT b.* FROM bills b WHERE b.id<? AND b.id>=? AND b.status<>'rejected' ORDER BY b.id DESC",
                        (blank["id"], blank["id"] - NEAR)):
        if _is_blank(b, _items_text(db, b["id"])):
            continue
        return b if (_head_ok(b) and _page_ok(db, blank, b)) else None
    return None


def _joined(db, head_id):
    return db.execute("SELECT id, stamp_no FROM bills WHERE page_of=? ORDER BY id", (head_id,)).fetchall()


def _last_batch(db, head_id):
    r = db.execute("SELECT batch FROM d664_join WHERE head_id=? AND undone_at IS NULL ORDER BY id DESC LIMIT 1",
                   (head_id,)).fetchone()
    return db.execute("SELECT * FROM d664_join WHERE batch=? ORDER BY id", (r[0],)).fetchall() if r else []


def _undo_text(db, head_id):
    """What 'Undo the last join' would take back: the papers of the last tap, by number."""
    rows = _last_batch(db, head_id)
    if not rows:
        return ""
    st = []
    for r in rows:
        b = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (r["page_id"],)).fetchone()
        if b:
            st.append(_stamp(b))
    return _and(st)


def _who():
    try:
        return g.user["display_name"] or g.user["username"]
    except Exception:                                                # noqa: BLE001
        return ""


def join_page(bid):
    db = AR.get_db()
    head = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not head:
        abort(404)
    back = _back("d664_papers")
    here = url_for("d664_paper", bid=bid, back=back)
    if not _can_join(db) or not _head_ok(head):
        flash("%s cannot take pages: it is a pharmacy scan, a rejected paper, a duplicate or itself a page." % _stamp(head))
        return redirect(here)
    if request.method == "POST":
        ids = []
        for x in request.form.getlist("page"):
            if str(x).isdigit() and int(x) not in ids:
                ids.append(int(x))
        also = re.sub(r"\s+", "", request.form.get("also") or "").upper()
        if also:
            if also.isdigit():
                also = "B-%04d" % int(also)
            r = db.execute("SELECT id FROM bills WHERE upper(stamp_no)=?", (also,)).fetchone()
            if not r:
                flash("There is no paper numbered %s." % also)
                return redirect(url_for("d664_join", bid=bid, back=back))
            if r[0] not in ids:
                ids.append(r[0])
        pages, refused = [], []
        for i in sorted(ids):
            b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (i,)).fetchone()
            if b and _page_ok(db, b, head):
                pages.append(b)
            elif b:
                refused.append(_stamp(b))
        if refused:
            flash("%s cannot be joined (a pharmacy scan, an approved or rejected paper, a duplicate, or already joined)."
                  % _and(refused))
        if not pages:
            if not refused:
                flash("Tick at least one paper, or type its number, then press Join.")
            return redirect(url_for("d664_join", bid=bid, back=back))
        batch, who, now = secrets.token_hex(6), _who(), AR._now_ist()
        cur, total_before, copied, loose = head["source_stored"], head["total_amount"], False, []
        for pg in pages:
            merged = None
            if AR.S441 is not None and cur and pg["source_stored"]:
                try:
                    merged = AR.S441._merge_pdf(AR.UPLOAD_DIR, {"source_stored": cur}, {"source_stored": pg["source_stored"]})
                except Exception:                                    # noqa: BLE001
                    merged = None
            copy = (not copied and total_before is None and pg["total_amount"] is not None)
            db.execute("INSERT INTO d664_join(batch, head_id, page_id, at, who, head_before, head_after, merged, "
                       "head_total_before, total_copied, page_status, page_reject_reason, page_approved_by, page_approved_at) "
                       "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (batch, bid, pg["id"], now, who, cur, merged or cur, 1 if merged else 0, total_before,
                        1 if copy else 0, pg["status"], pg["reject_reason"], pg["approved_by"], pg["approved_at"]))
            if merged:
                db.execute("UPDATE bills SET source_stored=? WHERE id=?", (merged, bid))
                cur = merged
            else:
                loose.append(_stamp(pg))
            if copy:                                                 # the total often sits on the last page
                db.execute("UPDATE bills SET total_amount=? WHERE id=?", (pg["total_amount"], bid))
                copied = True
            db.execute("UPDATE bills SET status='rejected', page_of=?, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",
                       (bid, "joined into %s" % _stamp(head), who, now, pg["id"]))
            AR._audit_bill(db, pg["id"], "d664_joined_into", {"to": bid, "to_stamp": head["stamp_no"], "merged": bool(merged)})
        AR._audit_bill(db, bid, "d664_join", {"pages": [_stamp(x) for x in pages], "after": cur, "batch": batch})
        db.commit()
        msg = "%s %s joined into %s." % (_and([_stamp(x) for x in pages]), "is" if len(pages) == 1 else "are", _stamp(head))
        if loose and len(loose) == len(pages):
            msg += " %s linked to it, but could not be put into one PDF (a photo, not a PDF, or the PDF tool did not answer)." % (
                "It is" if len(pages) == 1 else "They are")
        elif loose:
            msg += " One PDF now — except %s, linked to it but not in the file (a photo, not a PDF)." % _and(loose)
        else:
            msg += " One PDF now."
        flash(msg)
        return redirect(here)
    tick = {int(x) for x in request.args.getlist("tick") if str(x).isdigit()}
    tick |= {b["id"] for b in _blanks_after(db, head)}
    cands = []
    for b in db.execute("SELECT b.* FROM bills b WHERE b.id BETWEEN ? AND ? AND b.status<>'rejected' ORDER BY b.id",
                        (bid - NEAR, bid + NEAR)):
        if _page_ok(db, b, head):
            it = _items_text(db, b["id"])
            blank = _is_blank(b, it)
            of = _head_of_blank(db, b) if blank else None
            # "mine": ticked, or a blank scan that follows THIS paper. Everything else waits behind a fold, so a
            # neighbour's own bill is never one stray tap away from being swallowed.
            mine = (b["id"] in tick) or (blank and of is not None and of["id"] == bid)
            cands.append(dict(b=b, stamp=_stamp(b), blank=blank, words=it, ticked=(b["id"] in tick), mine=mine,
                              of=(_stamp(of) if (of is not None and of["id"] != bid) else "")))
    nmine = len([c for c in cands if c["mine"]])
    return AR.page(JOIN_TPL, head=head, hstamp=_stamp(head), cands=cands, nmine=nmine, nother=len(cands) - nmine,
                   joined=_joined(db, bid),
                   can_undo=bool(_last_batch(db, bid)), inr=_inr, back=back, here=here,
                   flow=AR._flow("Join into " + _stamp(head), here))


def unjoin(bid):
    db = AR.get_db()
    head = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not head:
        abort(404)
    back = _back("d664_papers")
    here = url_for("d664_paper", bid=bid, back=back)
    rows = _last_batch(db, bid)
    if not rows:
        flash("There is no join of %s to undo." % _stamp(head))
        return redirect(here)
    if (head["source_stored"] or "") != (rows[-1]["head_after"] or ""):
        flash("%s's file has changed since that join, so it cannot be undone from here." % _stamp(head))
        return redirect(here)
    who, now = _who(), AR._now_ist()
    db.execute("UPDATE bills SET source_stored=? WHERE id=?", (rows[0]["head_before"], bid))
    if any(r["total_copied"] for r in rows):
        db.execute("UPDATE bills SET total_amount=? WHERE id=?", (rows[0]["head_total_before"], bid))
    back_stamps = []
    for r in rows:
        pg = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (r["page_id"],)).fetchone()
        if pg and pg["page_of"] == bid and pg["status"] == "rejected":
            db.execute("UPDATE bills SET status=?, page_of=NULL, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",
                       (r["page_status"], r["page_reject_reason"], r["page_approved_by"], r["page_approved_at"], pg["id"]))
            AR._audit_bill(db, pg["id"], "d664_unjoined", {"from": bid, "from_stamp": head["stamp_no"]})
            back_stamps.append(_stamp(pg))
        db.execute("UPDATE d664_join SET undone_at=?, undone_by=? WHERE id=?", (now, who, r["id"]))
    AR._audit_bill(db, bid, "d664_unjoin", {"pages": back_stamps, "file": rows[0]["head_before"], "batch": rows[0]["batch"]})
    db.commit()
    flash("Undone: %s %s on %s own again, and %s has its own file back."
          % (_and(back_stamps) or "the pages", "is" if len(back_stamps) == 1 else "are",
             "its" if len(back_stamps) == 1 else "their", _stamp(head)))
    return redirect(here)


def _inr(x):
    """12,34,567.00 -- the Indian grouping, as the owner reads money."""
    if x is None:
        return "—"
    neg = x < 0
    whole, frac = ("%.2f" % abs(x)).split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return ("-" if neg else "") + "₹" + whole + "." + frac


# ---------------------------------------------------------------------------------------------- for the app's own pages
def group_label(b):
    """For the bill page: the group's words, or '' when none is set. Never raises."""
    try:
        return SUB.get((b["subgroup"] or "") if "subgroup" in b.keys() else "", "")
    except Exception:                                                # noqa: BLE001
        return ""


def to_sort_count():
    """For the Purchases page: how many clinic papers have no group yet. Never raises."""
    try:
        db = AR.get_db()
        return db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live(db) + " AND COALESCE(b.subgroup,'')=''"
                          ).fetchone()[0]
    except Exception:                                                # noqa: BLE001
        return 0


# ---------------------------------------------------------------------------------------------- the pages
CSS = """<style>
.d6{max-width:640px;margin:0 auto}
.d6 .lead{color:#5a6b7b;font-size:14px;margin:0 0 12px}
.d6 .muted{color:#5a6b7b}
.d6card{background:#fff;border:1px solid #d5dce8;border-radius:12px;padding:14px;margin:0 0 14px;box-shadow:0 1px 3px rgba(20,40,70,.06)}
.d6top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.d6top b{font-size:16px}
.d6row{display:flex;gap:12px;align-items:flex-start}
.d6row img{width:64px;height:84px;object-fit:cover;border-radius:6px;background:#dfe6f1;flex:none}
.d6say{background:#eef4ff;border-radius:8px;padding:10px;font-size:14px;margin:10px 0}
.d6say.other{background:#fff4e0;color:#5b3a06}
.d6say.none{background:#f2f5f9;color:#5a6b7b}
.d6btns{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.d6btns form{display:inline;margin:0}
.d6b{min-height:44px;padding:0 14px;border-radius:8px;font-size:15px;font-weight:600;font-family:inherit;display:inline-flex;align-items:center;text-decoration:none;cursor:pointer;box-sizing:border-box}
.d6b.yes{background:#3a5a78;color:#fff;border:0}
.d6b.alt{background:#fff;color:#1f3864;border:1px solid #1f3864}
.d6b.skip{background:#fff;color:#5a6b7b;border:1px solid #b7c2d4}
.d6opt{display:block;width:100%;max-width:none;text-align:left;min-height:52px;padding:8px 14px;margin:0 0 8px;border:1px solid #b7c2d4;border-radius:10px;background:#fff;color:#2d3742;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;box-sizing:border-box}
.d6opt.on{border:2px solid #3a5a78;background:#eef4ff}
.d6opt small{display:block;font-weight:400;color:#5a6b7b;font-size:13px}
.d6x summary{list-style:none}.d6x summary::-webkit-details-marker{display:none}
.d6x[open] summary{margin-bottom:6px}
.d6x .in{padding:0 0 4px 16px;display:flex;gap:8px;flex-wrap:wrap}
.d6t{border-radius:0}.d6t td,.d6t th{font-size:14px;border-left:0;border-right:0}.d6t tr:first-child td{border-top:0}.d6t tr:last-child td{border-bottom:0}
.d6line{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-top:1px solid #eef1f5}
.d6mini{display:inline-flex;align-items:center;min-height:36px;padding:0 10px;margin-top:4px;border:1px solid #b7c2d4;border-radius:8px;font-size:14px;text-decoration:none}
.nw{white-space:nowrap}
.d6pick{display:flex;gap:12px;align-items:center;min-height:72px;border-top:1px solid #e3e8f0;padding:10px 0 0;margin:10px 0 0;font-size:inherit;color:inherit}
.d6pick input{width:28px;height:28px;flex:none;margin:0}
.d6radio{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 14px;margin:0;border:1px solid #b7c2d4;border-radius:8px;background:#fff;font-size:15px;font-weight:600;color:#2d3742;cursor:pointer}
.d6radio input{width:20px;height:20px;margin:0;flex:none}
.d6x>summary.d6opt{position:relative;padding-right:40px}
.d6x>summary.d6opt::after{content:"▾";position:absolute;right:16px;top:50%;transform:translateY(-50%);color:#5b6b7f;font-size:18px}
.d6x[open]>summary.d6opt::after{content:"▴"}
.d6pick img{width:56px;height:72px;object-fit:cover;border-radius:6px;background:#dfe6f1;flex:none}
.d6t td.r,.d6t th.r{text-align:right;white-space:nowrap}
.d6t tr.sub td{color:#5a6b7b;padding-left:26px}
.d6nav{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:0 0 10px}
</style>"""

PAPERS_TPL = CSS + """<div class=d6><h2>Clinic papers to sort{% if total %} <span class="badge amber">{{total}} paper{{'' if total==1 else 's'}}</span>{% endif %}</h2>
<p class=lead>For you or Shavez. Staff are asked nothing new when they scan.
 &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a></p>
{% for p in papers %}<div class=d6card>
<div class=d6row><a href="{{url_for('bill_view',bid=p.b['id'])}}">{% if p.b['source_stored'] %}<img loading=lazy alt="the scanned paper" src="{{url_for('bill_thumb',bid=p.b['id'])}}">{% endif %}</a>
<div style="flex:1;min-width:0"><div class=d6top><b><a href="{{url_for('bill_view',bid=p.b['id'])}}" style="text-decoration:none">{{p.stamp}}</a> · {{p.b['vendor'] or 'supplier not read'}}</b>
<span>{% if p.b['total_amount'] is not none %}<b>{{inr(p.b['total_amount'])}}</b>{% else %}<span class=muted>amount not read</span>{% endif %}</span></div>
<div class=muted style="font-size:13px">{% if p.reading %}still being read — a suggestion follows in a minute{% elif p.read_nothing %}No bill number, amount or item could be read.{% else %}{% if p.b['bill_date'] %}Bill dated {{p.b['bill_date']}}{% else %}no date read{% endif %}{% if p.b['bill_no'] %} · no. {{p.b['bill_no']}}{% endif %}{% if p.words %} · {{p.words[:90]}}{% endif %}{% endif %}{% if p.njoined %} · <b class=nw>{{p.njoined}} page{{'' if p.njoined==1 else 's'}} joined</b>{% endif %}</div></div></div>
{% if p.s and p.s.kind=='sub' %}<div class=d6say>Looks like <b>Clinic consumables · {{p.s.label}}</b> — from {{p.s.why}}.{% if p.s.value=='xray' %} Which film?{% endif %}</div>
{% elif p.s and p.s.kind=='lane' %}<div class="d6say other">Looks like <b>{{p.s.label}}</b>, not a clinic consumable — from {{p.s.why}}.</div>
{% elif p.s %}<div class="d6say other">{{p.s.why[0]|upper}}{{p.s.why[1:]}}.</div>
{% elif p.head %}<div class="d6say other">It comes after <b>{{p.head_stamp}}</b>{% if p.head['vendor'] %} ({{p.head['vendor']}}){% endif %} in the scans — it looks like a page or a warranty card of that purchase.</div>
{% elif not p.reading %}<div class="d6say none">No suggestion — nothing on it names a group.</div>{% endif %}
{% if p.after %}<div class="d6say other">The next {{'scan' if p.after|length==1 else (p.after|length)|string ~ ' scans'}}, <b>{{p.after_text}}</b>, {{'has' if p.after|length==1 else 'have'}} nothing read on {{'it' if p.after|length==1 else 'them'}} — {{'it looks like one more page' if p.after|length==1 else 'they look like more pages'}} of this purchase.</div>{% endif %}
<div class=d6btns>
{% if p.head %}<a class="d6b yes" href="{{url_for('d664_join',bid=p.head['id'],tick=p.b['id'],back=url_for('d664_papers'))}}">Join into {{p.head_stamp}}</a>{% endif %}
{% if p.s and p.s.kind=='sub' and p.s.value!='xray' %}<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{url_for('d664_papers')}}"><button class="d6b yes" name=subgroup value="{{p.s.value}}">Yes, {{p.s.label}}</button></form>
{% elif p.s and p.s.kind=='sub' %}<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{url_for('d664_papers')}}"><button class="d6b yes" name=subgroup value="xray_small">X-ray · small film</button> <button class="d6b yes" name=subgroup value="xray_11x14">X-ray · 11 x 14</button></form>
{% elif p.s and p.s.kind=='lane' %}<form method=post action="{{url_for('bill_lane',bid=p.b['id'])}}"><input type=hidden name=back value="{{url_for('d664_paper',bid=p.b['id'],back=url_for('d664_papers')) if p.s.value=='owner_expense' else url_for('d664_papers')}}"><button class="d6b yes" name=lane value="{{p.s.value}}">Move to {{p.s.label}}</button></form>{% endif %}
{% if p.after %}<a class="d6b alt" href="{{url_for('d664_join',bid=p.b['id'],back=url_for('d664_papers'))}}">Join {{p.after_text if p.after|length==1 else 'them'}} into this one</a>{% endif %}
<a class="d6b alt" href="{{url_for('d664_paper',bid=p.b['id'])}}">{{'Change' if (p.s and p.s.kind!='note') else 'Open it'}}</a>
<button type=button class="d6b skip" onclick="this.closest('.d6card').style.display='none'">Skip</button></div></div>
{% endfor %}
{% if not papers %}<div class=d6card><b>Nothing to sort.</b><br><span class=muted>Every clinic paper has its group.</span></div>{% endif %}
{% if more %}<p class=muted>Showing the newest {{papers|length}} of {{total}}. Sort these and the older ones follow.</p>{% endif %}
<p class=muted>Skip leaves the paper here for later. Nothing is lost by not sorting: an unsorted paper still counts under Clinic consumables.</p></div>"""

PAPER_TPL = CSS + """<div class=d6><h2>{{p.stamp}} <span class=muted>{{p.b['vendor'] or 'supplier not read'}}</span></h2>
<p class=lead>Lane: {{lanes[p.b['lane'] or 'clinic'][0]}}{% if p.b['total_amount'] is not none %} · {{inr(p.b['total_amount'])}}{% endif %}{% if p.b['bill_date'] %} · {{p.b['bill_date']}}{% endif %}
 · <a href="{{url_for('bill_view',bid=p.b['id'])}}" class=nw>{{'open the scan' if p.blank else 'open the bill'}}</a></p>
{% if p.b['source_stored'] %}<a href="{{url_for('bill_file',bid=p.b['id'])}}"><img alt="the scanned paper" src="{{url_for('bill_thumb',bid=p.b['id'])}}" style="display:block;max-width:100%;max-height:260px;margin:0 auto 14px;border-radius:10px;background:#dfe6f1"></a>{% endif %}
{% if p.head and not p.b['page_of'] %}<div class=d6card><b style="font-size:16px">A page of another purchase?</b>
<p style="margin:6px 0 10px">It comes after <b>{{p.head_stamp}}</b>{% if p.head['vendor'] %} ({{p.head['vendor']}}){% endif %} in the scans, and nothing could be read on it — it looks like a page or a warranty card of that purchase.</p>
<div class=d6btns><a class="d6b yes" href="{{url_for('d664_join',bid=p.head['id'],tick=p.b['id'],back=back)}}">Join into {{p.head_stamp}}</a></div></div>{% endif %}
{% if on_clinic %}<div class=d6card>
{% if p.s and p.s.kind!='sub' %}<div class="d6say other">{% if p.s.kind=='lane' %}Looks like <b>{{p.s.label}}</b>, not a clinic consumable — from {{p.s.why}}.{% else %}{{p.s.why[0]|upper}}{{p.s.why[1:]}}.{% endif %}</div>{% endif %}
{% if p.s and p.s.kind=='lane' %}<form method=post action="{{url_for('bill_lane',bid=p.b['id'])}}" class=d6btns style="display:flex;margin:0 0 12px"><input type=hidden name=back value="{{url_for('d664_paper',bid=p.b['id'],back=back) if p.s.value=='owner_expense' else back}}"><button class="d6b yes" name=lane value="{{p.s.value}}">Move to {{p.s.label}}</button></form>{% endif %}
<b style="font-size:16px">{{'If it is a clinic consumable after all, which one?' if (p.s and p.s.kind=='lane') else 'Which clinic consumable?'}}</b>
<p class=muted style="font-size:13px;margin:4px 0 10px">One tap saves it. Optional — leave it and the paper stays under Clinic consumables, not sorted.</p>
<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{back}}">
<button class="d6opt {{'on' if cur=='procedure'}}" name=subgroup value=procedure>Procedure room{% if sug=='procedure' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>fibre cast, roller bandage, cotton, tape, betadine</small></button>
<details class=d6x {{'open' if (cur.startswith('xray') or sug.startswith('xray'))}}><summary class="d6opt {{'on' if cur.startswith('xray')}}">X-ray films{% if sug.startswith('xray') %} <span style="font-weight:400">— suggested</span>{% endif %}<small>then one more tap: small film or 11 x 14</small></summary>
<div class=in><button class="d6b {{'yes' if cur=='xray_small' else 'alt'}}" name=subgroup value=xray_small>Small film</button>
<button class="d6b {{'yes' if cur=='xray_11x14' else 'alt'}}" name=subgroup value=xray_11x14>11 x 14</button>
<button class="d6b {{'yes' if cur=='xray' else 'skip'}}" name=subgroup value=xray>size not known</button></div></details>
<button class="d6opt {{'on' if cur=='others'}}" name=subgroup value=others>Others{% if sug=='others' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>stationery and the rest</small></button>
{% if cur %}<button class="d6b skip" name=subgroup value="">Clear the group</button>{% endif %}
<a class="d6b skip" href="{{back}}">{{'Done' if cur else 'Skip for now'}}</a></form></div>
{% elif p.b['page_of'] %}<div class=d6card><b>This paper is a page of another paper.</b><br>It was joined into <a href="{{url_for('d664_paper',bid=p.b['page_of'])}}"><b>{{of_stamp or 'its bill'}}</b></a>. To make it a paper of its own again, open {{of_stamp or 'that bill'}} and press “Undo the last join” (joins are undone latest first).</div>
{% else %}<div class=d6card><b>This paper is not on the clinic lane.</b><br><span class=muted>Groups belong to clinic consumables only.</span></div>{% endif %}
{% if on_expense %}<div class=d6card><b style="font-size:16px">Keep the warranty</b>
<p class=muted style="font-size:13px;margin:4px 0 10px">Optional. Type the date from the warranty card.</p>
{% if w %}<div class=d6say><b>{{w['what']}}</b> — warranty till <b class=nw>{{dmy(w['till'])}}</b>. {{wtext.replace('-', nbh)}}</div>{% endif %}
<form method=post action="{{url_for('d664_warranty',bid=p.b['id'])}}"><input type=hidden name=back value="{{back}}">
<label for=w_what>What it is</label>
<input id=w_what name=what maxlength=80 value="{{w['what'] if w else guess}}" placeholder="for example Inverter battery" autocomplete=off>
<label for=w_till style="margin-top:10px">Warranty till</label>
<input id=w_till name=till type=date value="{{w['till'] if w else ''}}" style="max-width:220px">
<div style="margin:12px 0 6px;font-size:14px;font-weight:600;color:#3a5a78">Remind me</div>
<div class=d6btns>{% for d, l in remind %}<label class=d6radio><input type=radio name=remind value="{{d}}" {{'checked' if rd==d}}> {{l}}</label>{% endfor %}</div>
<div class=d6btns style="margin-top:14px"><button class="d6b yes">{{'Save the change' if w else 'Save'}}</button>
{% if w %}<button class="d6b alt" name=remove value=1>Remove the warranty</button>{% endif %}</div></form>
<p class=muted style="font-size:13px;margin:12px 0 0">The reminder shows on <a href="{{url_for('renewals')}}">Renewals &amp; warranties</a>, to you only. Dr MK expense is your own lane: it is kept apart from the clinic's consumables and from the pharmacy, and nothing about it is sent on WhatsApp.</p></div>{% endif %}
{% if can_join and (joined or not p.head) %}<div class=d6card><b style="font-size:16px">One purchase, one PDF</b>
{% if joined %}<p style="margin:6px 0">Joined into this paper: {% for j in joined %}<a href="{{url_for('bill_view',bid=j['id'])}}">{{j['stamp_no'] or ('#'~j['id'])}}</a>{{', ' if not loop.last}}{% endfor %}.</p>{% endif %}
<p class=muted style="font-size:13px;margin:4px 0 10px">A warranty card or another page that was scanned separately can be joined into this paper.</p>
<div class=d6btns><a class="d6b alt" href="{{url_for('d664_join',bid=p.b['id'],back=back)}}">{{'Join more pages' if joined else (('Join ' ~ p.after_text ~ ' into this paper') if p.after else 'Join pages into this paper')}}</a>
{% if can_undo %}<form method=post action="{{url_for('d664_unjoin',bid=p.b['id'])}}"><input type=hidden name=back value="{{back}}"><button class="d6b alt">Undo the last join{% if undo_text %} ({{undo_text}}){% endif %}</button></form>{% endif %}</div></div>{% endif %}
{% if p.b['status']!='rejected' %}<div class=d6card><b>{{'Not a clinic consumable?' if on_clinic else 'On the wrong lane?'}}</b>
<p class=muted style="font-size:13px;margin:4px 0 10px">Move it to its own lane{% if p.b['status']=='approved' %} — but this bill is approved, and an approved bill stays on the clinic lane{% endif %}.</p>
<form method=post action="{{url_for('bill_lane',bid=p.b['id'])}}" class=d6btns style="display:flex"><input type=hidden name=back value="{{back}}">
{% for k in lane_order %}{% if k!=(p.b['lane'] or 'clinic') %}<button class="d6b alt" name=lane value="{{k}}">{{lanes[k][0].split(' — ')[0]}}</button>{% endif %}{% endfor %}</form></div>{% endif %}
{% if on_clinic %}<p class=muted>The suggestion comes from the supplier and the words read on the paper. The supplier alone never decides: Yuvika sells orthotics to the pharmacy too.</p>{% endif %}</div>"""

JOIN_TPL = CSS + """<div class=d6><h2>Join into one purchase</h2>
<p class=lead>For papers that were scanned separately. One purchase, one PDF.</p>
<form method=post action="{{url_for('d664_join',bid=head['id'])}}"><input type=hidden name=back value="{{back}}">
<div class=d6card>
<div class=d6row>{% if head['source_stored'] %}<img loading=lazy alt="the bill" src="{{url_for('bill_thumb',bid=head['id'])}}">{% endif %}
<div style="flex:1;min-width:0"><b style="font-size:16px">{{hstamp}} — the bill</b><br>
<span class=muted style="font-size:14px">{{head['vendor'] or 'supplier not read'}}{% if head['bill_date'] %} · {{head['bill_date']}}{% endif %}{% if head['total_amount'] is not none %} · {{inr(head['total_amount'])}}{% endif %}</span><br>
<b style="font-size:13px;color:#1f3864">This number stays for the whole purchase</b>{% if joined %}<br><span class=muted style="font-size:13px">already joined: {% for j in joined %}{{j['stamp_no'] or ('#'~j['id'])}}{{', ' if not loop.last}}{% endfor %}</span>{% endif %}</div></div>
{% for c in cands if c.mine %}<label class=d6pick><input type=checkbox name=page value="{{c.b['id']}}" {{'checked' if c.ticked}}>
{% if c.b['source_stored'] %}<img loading=lazy alt="scan {{c.stamp}}" src="{{url_for('bill_thumb',bid=c.b['id'])}}">{% endif %}
<span style="flex:1;min-width:0"><b style="font-size:16px">{{c.stamp}}</b><br>
<span class=muted style="font-size:14px">{% if c.blank %}no supplier, no amount — looks like a warranty card or one more page{% else %}{{c.b['vendor'] or 'supplier not read'}}{% if c.b['total_amount'] is not none %} · {{inr(c.b['total_amount'])}}{% endif %}{% if c.words %} · {{c.words[:60]}}{% endif %}{% endif %}</span></span></label>{% endfor %}
{% if not nmine %}<p class=muted style="margin:12px 0 0">No scan beside this paper looks like one of its pages.</p>{% endif %}
{% if nother %}<details class=d6x style="margin-top:12px"><summary class=d6opt>Other papers scanned near it ({{nother}})<small>open this only if a page of this purchase was read as a bill of its own</small></summary>
<div class=in style="display:block"><p style="font-size:14px;margin:0">A paper with its own supplier and amount is usually a purchase of its own. Tick one only if it is truly a page of {{hstamp}} — its amount is then no longer counted separately. A scan marked “comes after B-…” most likely belongs to that other paper.</p>
{% for c in cands if not c.mine %}<label class=d6pick><input type=checkbox name=page value="{{c.b['id']}}">
{% if c.b['source_stored'] %}<img loading=lazy alt="scan {{c.stamp}}" src="{{url_for('bill_thumb',bid=c.b['id'])}}">{% endif %}
<span style="flex:1;min-width:0"><b style="font-size:16px">{{c.stamp}}</b><br>
<span class=muted style="font-size:14px">{% if c.blank %}no supplier, no amount{% if c.of %} — comes after {{c.of}}{% endif %}{% else %}{{c.b['vendor'] or 'supplier not read'}}{% if c.b['total_amount'] is not none %} · {{inr(c.b['total_amount'])}}{% endif %}{% if c.words %} · {{c.words[:60]}}{% endif %}{% endif %}</span></span></label>{% endfor %}</div></details>{% endif %}
<label for=also style="margin-top:12px">Another paper, by its number</label>
<input id=also name=also placeholder="a number, like B-0123" autocomplete=off style="max-width:220px">
</div>
<button class="d6b yes" style="width:100%;justify-content:center;min-height:52px;font-size:16px">Join the ticked papers into {{hstamp}}</button></form>
<div class=d6card style="margin-top:14px;font-size:14px"><b style="font-size:15px">What joining does</b>
<p style="margin:6px 0">The scans become one PDF: the bill first, then the pages in the order they were scanned.</p>
<p style="margin:6px 0">The joined papers are not deleted. Each joined paper keeps its own number and shows as “a page of {{hstamp}}”, so a number written on a paper still finds the purchase.</p>
<p style="margin:6px 0">It can be undone: open {{hstamp}} and press “Undo the last join”.</p></div>
<p class=muted>This is only for papers already scanned apart. At the scanner, staff add every page of a purchase before pressing Save — the scan screen already works that way.</p>
<p><a class="d6b skip" href="{{here}}">Back without joining</a></p></div>"""

MONTH_TPL = CSS + """<div class=d6><div class=d6nav><a class="d6b alt" href="{{url_for('d664_month',ym=prev)}}">← {{label(prev)}}</a>
{% if nxt %}<a class="d6b alt" href="{{url_for('d664_month',ym=nxt)}}">{{label(nxt)}} →</a>{% else %}<span></span>{% endif %}</div>
<h2>Clinic consumables</h2>
<p class=lead>What the clinic bought in <b>{{label(ym)}}</b>, by group.</p>
{% if g %}<p><a class="d6b alt" href="{{url_for('d664_month',ym=ym)}}">← All groups</a></p>
<div class=d6card><b style="font-size:16px">{{gname}}</b>
{% for b in rows %}<div class=d6line><div style="flex:1;min-width:0"><a href="{{url_for('bill_view',bid=b['id'])}}"><b>{{b['stamp_no'] or ('#'~b['id'])}}</b></a> · {{b['vendor'] or 'supplier not read'}}
<br><span class=muted style="font-size:13px"><span class=nw>{{b['bill_date'] or 'no date read'}}</span>{% if b['subgroup'] in ('xray_small','xray_11x14') %} · <span class=nw>{{sub[b['subgroup']].split(' · ')[1]}}</span>{% endif %}{% if b['status']=='draft' %} · <span class=nw>pending approval</span>{% endif %}</span></div>
<div style="text-align:right;flex:none"><b class=nw>{{inr(b['total_amount']) if b['total_amount'] is not none else 'amount not read'}}</b><br>
<a href="{{url_for('d664_paper',bid=b['id'],back=here)}}" class=d6mini>{{'sort it' if not b['subgroup'] else 'change group'}}</a></div></div>{% endfor %}
{% if not rows %}<p class=muted>No paper in this group this month.</p>{% endif %}</div>
{% else %}<div class=d6card style="padding:2px 14px"><table class=d6t>
{% for r in table %}<tr class="{{'sub' if r.sub else ''}}"><td>{% if r.key %}<a href="{{url_for('d664_month',ym=ym,g=r.key)}}" style="text-decoration:none">{% endif %}{% if not r.sub %}<b>{{r.name}}</b>{% else %}{{r.name}}{% endif %}{% if r.key %}</a>{% endif %}
{% if not r.sub %}<br><span class=muted style="font-size:13px">{{r.n}} paper{{'' if r.n==1 else 's'}}{% if r.vendors %} · {{r.vendors}}{% endif %}{% if r.noamt %} · {{r.noamt}} with no amount read{% endif %}</span>{% endif %}</td>
<td class=r>{% if not r.sub %}<b>{{inr(r.total)}}</b>{% else %}{{inr(r.total)}}{% endif %}</td></tr>{% endfor %}
<tr><td><b>All clinic consumables</b><br><span class=muted>{{alln}} paper{{'' if alln==1 else 's'}}{% if pending %} · {{pending}} still pending approval{% endif %}</span></td><td class=r><b>{{inr(alltotal)}}</b></td></tr></table></div>
{% if unsorted %}<p><a class=btn href="{{url_for('d664_papers')}}">Sort the {{unsorted}} unsorted paper{{'' if unsorted==1 else 's'}}</a></p>{% endif %}
<div class=d6card style="font-size:14px"><b style="font-size:15px">Kept apart, each in its own lane</b>
{% for k, nm, n in apart %}<div class=d6line style="padding:6px 0"><div style="flex:1">{{nm}}</div><div class=nw>{{n}} paper{{'' if n==1 else 's'}}</div></div>{% endfor %}</div>
<p class=muted>Tap a group to see its papers. A paper with no amount read counts as a paper and adds nothing to the total until its amount is typed on the bill.
 A paper counts in the month set on its bill; if none was set, the month of its bill date; if no date was read, the month it was scanned.</p>{% endif %}</div>"""


def _back(default_endpoint="d664_papers"):
    return AR._safe_from(request.values.get("back")) or url_for(default_endpoint)


def papers():
    db = AR.get_db()
    where = _live(db) + " AND COALESCE(b.subgroup,'')=''"
    total = db.execute("SELECT COUNT(*) FROM bills b WHERE " + where).fetchone()[0]
    rows = db.execute("SELECT b.* FROM bills b WHERE " + where + " ORDER BY b.id DESC LIMIT ?", (PAGE_N,)).fetchall()
    return AR.page(PAPERS_TPL, papers=[_paper(db, b) for b in rows], total=total, more=(total > len(rows)),
                   inr=_inr, flow=AR._flow("Clinic papers to sort", url_for("bills_list")))


def paper(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    p = _paper(db, b)
    w = _warranty(db, bid) if _on_expense(b) else None
    of = None
    if _can_join(db) and b["page_of"]:
        of = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["page_of"],)).fetchone()
    return AR.page(PAPER_TPL, p=p, of_stamp=(_stamp(of) if of else ""), cur=p["group"], sug=(p["s"]["value"] if (p["s"] and p["s"]["kind"] == "sub") else ""),
                   on_clinic=((b["lane"] or "clinic") == "clinic" and b["status"] != "rejected"),
                   on_expense=_on_expense(b), w=w, wtext=(_remind_text(w, AR.today()) if w else ""), dmy=_dmy,
                   nbh=chr(0x2011),                                  # a date in a sentence must not break at its hyphens
                   remind=REMIND, rd=(w["remind_days"] if w else 30),
                   guess=((p["words"].split(" ; ")[0][:80]) if p["words"] else ""),
                   can_join=(_can_join(db) and _head_ok(b)), joined=_joined(db, bid) if _can_join(db) else [],
                   can_undo=bool(_last_batch(db, bid)), undo_text=_undo_text(db, bid),
                   lanes=AR.LANES, lane_order=AR.LANE_ORDER, inr=_inr, back=_back(),
                   flow=AR._flow("Clinic paper " + p["stamp"], _back()))


def set_group(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    to = (request.form.get("subgroup") or "").strip().lower()
    back = _back()
    stamp = b["stamp_no"] or ("#%d" % bid)
    if to and to not in SUB:
        abort(400)
    if (b["lane"] or "clinic") != "clinic" or b["status"] == "rejected":
        flash("%s is not a live paper on the clinic lane — groups belong to clinic consumables only." % stamp)
        return redirect(back)
    frm = b["subgroup"] or ""
    if to != frm:
        db.execute("UPDATE bills SET subgroup=? WHERE id=?", (to or None, bid))
        AR._audit_bill(db, bid, "subgroup", {"from": frm, "to": to})
        db.commit()
    flash(("%s is under %s." % (stamp, SUB[to])) if to else ("%s has no group now." % stamp))
    return redirect(back)


def _ym_ok(ym):
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym or ""))


def _ym_shift(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) + k
    while m < 1:
        y, m = y - 1, m + 12
    while m > 12:
        y, m = y + 1, m - 12
    return "%04d-%02d" % (y, m)


MONTH_OF = ("COALESCE(NULLIF(b.bill_month,''), substr(NULLIF(b.bill_date,''),1,7), "
            "substr(datetime(b.created_at,'+330 minutes'),1,7), substr(b.created_at,1,7))")


def month():
    db = AR.get_db()
    today = datetime.date.today().strftime("%Y-%m")
    ym = request.args.get("ym", "")
    if not _ym_ok(ym):
        ym = today
    g_ = request.args.get("g", "")
    live = _live(db)
    rows = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND " + MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                      (ym,)).fetchall()

    def agg(pred):
        sel = [b for b in rows if pred(b["subgroup"] or "")]
        ven = []
        for b in sel:
            v = (b["vendor"] or "").strip()
            if v and v not in ven:
                ven.append(v)
        return dict(n=len(sel), total=sum(b["total_amount"] or 0 for b in sel),
                    noamt=sum(1 for b in sel if b["total_amount"] is None),
                    vendors=", ".join(ven[:3]) + (" and %d more" % (len(ven) - 3) if len(ven) > 3 else ""), rows=sel)

    if g_ in ("procedure", "xray", "others", "unsorted"):
        a = agg((lambda s: s == "") if g_ == "unsorted" else (lambda s: GROUP_OF.get(s) == g_))
        return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                       label=AR._month_label, inr=_inr, g=g_, rows=a["rows"], sub=SUB,
                       gname=("Not sorted yet" if g_ == "unsorted" else dict((k, n) for k, n, _h in GROUPS)[g_]),
                       here=AR._here(full=True), flow=AR._flow("Clinic consumables", url_for("bills_list")))
    table = []
    for key, name, _hint in GROUPS:
        a = agg(lambda s, key=key: GROUP_OF.get(s) == key)
        table.append(dict(key=key, name=name, sub=False, **{k: a[k] for k in ("n", "total", "noamt", "vendors")}))
        if key == "xray":
            for sk, sn in (("xray_small", "Small film"), ("xray_11x14", "11 x 14 film"), ("xray", "size not known")):
                s2 = agg(lambda s, sk=sk: s == sk)
                if s2["n"]:
                    table.append(dict(key=None, name=sn, sub=True, n=s2["n"], total=s2["total"], noamt=0, vendors=""))
    u = agg(lambda s: s == "")
    table.append(dict(key="unsorted", name="Not sorted yet", sub=False, n=u["n"], total=u["total"], noamt=u["noamt"],
                      vendors=u["vendors"]))
    apart = []
    names = {"pharmacy": "Pharmacy purchases — Sanjeevni", "lab_purchase": "Lab purchases — NK Pathology",
             "owner_expense": "Dr MK expense", "other_doc": "Other documents — not bills"}
    extra = " AND b.page_of IS NULL" if "page_of" in _cols(db) else ""
    for k in ("pharmacy", "lab_purchase", "owner_expense", "other_doc"):
        n = db.execute("SELECT COUNT(*) FROM bills b WHERE b.lane=? AND b.status<>'rejected' AND b.dup_of IS NULL"
                       + extra + " AND " + MONTH_OF + "=?", (k, ym)).fetchone()[0]
        apart.append((k, names[k], n))
    return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                   label=AR._month_label, inr=_inr, g="", table=table, alln=len(rows),
                   alltotal=sum(b["total_amount"] or 0 for b in rows),
                   pending=sum(1 for b in rows if b["status"] == "draft"), unsorted=u["n"], apart=apart,
                   flow=AR._flow("Clinic consumables", url_for("bills_list")))


# ---------------------------------------------------------------------------------------------- the mount
# ---------------------------------------------------------------------------------------------- S466: the warranty
def _dmy(iso):
    try:
        return datetime.date.fromisoformat(str(iso)[:10]).strftime("%d-%b-%Y")
    except Exception:                                                # noqa: BLE001
        return str(iso or "")


def _on_expense(b):
    return (b["lane"] or "clinic") == "owner_expense" and b["status"] != "rejected"


def _warranty(db, bid):
    try:
        return db.execute("SELECT * FROM d664_warranty WHERE bill_id=?", (bid,)).fetchone()
    except sqlite3.OperationalError:
        return None


def _remind_text(w, today):
    """What will happen, in the owner's words."""
    try:
        days = (datetime.date.fromisoformat(w["till"]) - today).days
    except Exception:                                                # noqa: BLE001
        return ""
    if days < 0:
        return "That date has passed, so there is nothing to remind."
    if not w["remind_days"]:
        return "No reminder; it is listed under “show all upcoming” on Renewals & warranties."
    if days <= w["remind_days"]:
        return "It is on Renewals & warranties now (%s)." % ("ends today" if days == 0 else "%d day%s left" % (days, "" if days == 1 else "s"))
    return "It will show on Renewals & warranties from %s, %d days before it ends." % (
        _dmy((datetime.date.fromisoformat(w["till"]) - datetime.timedelta(days=w["remind_days"])).isoformat()), w["remind_days"])


def warranty_label(b):
    """For the asset app's own bill page: 'Inverter battery -- till 01-Oct-2028', or '' when none is noted."""
    try:
        w = _warranty(AR.get_db(), b["id"])
        return (Markup('%s %s till <span style="white-space:nowrap">%s</span>') % (w["what"], DASH, _dmy(w["till"]))) if w else ""
    except Exception:                                                # noqa: BLE001
        return ""


def warranty_rows(db, show_all, today):
    """The Dr MK expense warranties for the Renewals page. Default: only those inside their own reminder window.
    show_all: every warranty still running, and those ended in the last ENDED_KEEP_DAYS days (marked ended)."""
    out = []
    for r in db.execute("SELECT w.*, b.vendor, b.stamp_no FROM d664_warranty w JOIN bills b ON b.id=w.bill_id "
                        "WHERE COALESCE(b.lane,'clinic')='owner_expense' AND b.status<>'rejected' ORDER BY w.till, w.bill_id"):
        try:
            days = (datetime.date.fromisoformat(r["till"]) - today).days
        except Exception:                                            # noqa: BLE001
            continue
        due = bool(r["remind_days"]) and 0 <= days <= r["remind_days"]
        if not (due or (show_all and days >= -ENDED_KEEP_DAYS)):
            continue
        out.append(dict(bid=r["bill_id"], what=r["what"], till=_dmy(r["till"]), days=days, due=due, vendor=r["vendor"] or "",
                        stamp=r["stamp_no"] or ("#%d" % r["bill_id"]), njoined=len(_joined(db, r["bill_id"])) if _can_join(db) else 0))
    return out


WARRANTY_CARD_TPL = """<div class=card><h3 style="color:#1f3864">Dr MK expense — warranties <span class=muted>({{rows|length}})</span></h3>
<table><tr><th>What</th><th>Warranty till</th><th>Status</th></tr>
{% for r in rows %}<tr class="{{'amber' if r.due else ''}}">
<td><a href="{{url_for('d664_paper',bid=r.bid)}}">{{r.what}}</a><br><span class=muted>{% if r.vendor %}{{r.vendor}} · {% endif %}</span><a href="{{url_for('bill_file',bid=r.bid)}}" style="white-space:nowrap">{{r.stamp}}</a>{% if r.njoined %} <span class=muted>+ {{r.njoined}} page{{'' if r.njoined==1 else 's'}} joined</span>{% endif %}</td>
<td style="white-space:nowrap">{{r.till}}</td>
<td>{% if r.due %}<span class="badge amber" style="white-space:nowrap">{{'ends today' if r.days==0 else (r.days|string)+(' day left' if r.days==1 else ' days left')}}</span>{% elif r.days<0 %}<span class=muted>ended</span>{% else %}<span class=muted>{{r.days}} days left</span>{% endif %}</td></tr>{% endfor %}</table></div>"""


def warranty_card():
    """For the asset app's 'Renewals & warranties' page (one hook there). The OWNER only; '' when there is nothing to
    show, and '' on any error -- that page must never fail because of this card."""
    try:
        if not AR.is_owner():
            return ""
        rows = warranty_rows(AR.get_db(), bool(request.args.get("all")), AR.today())
        return Markup(render_template_string(WARRANTY_CARD_TPL, rows=rows)) if rows else ""
    except Exception:                                                # noqa: BLE001
        return ""


def set_warranty(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    back = _back()
    here = url_for("d664_paper", bid=bid, back=back)
    stamp = _stamp(b)
    if not _on_expense(b):
        flash("%s is not on the Dr MK expense lane, so no warranty is kept for it. Move it there first." % stamp)
        return redirect(here)
    old = _warranty(db, bid)
    if request.form.get("remove"):
        if old:
            db.execute("DELETE FROM d664_warranty WHERE bill_id=?", (bid,))
            AR._audit_bill(db, bid, "d664_warranty_removed", {"what": old["what"], "till": old["till"], "remind_days": old["remind_days"]})
            db.commit()
            flash("The warranty of %s is removed." % stamp)
        return redirect(here)
    what = re.sub(r"\s+", " ", request.form.get("what") or "").strip()[:80]
    till = (request.form.get("till") or "").strip()
    remind = (request.form.get("remind") or "").strip()
    try:
        d = datetime.date.fromisoformat(till)
        if not (2000 <= d.year <= 2100) or len(till) != 10:
            raise ValueError
    except ValueError:
        flash("Pick the date the warranty runs till. Nothing was saved." + (" To drop the warranty, press Remove the warranty." if old else ""))
        return redirect(here)
    if not what:
        flash("Say what it is %s for example Inverter battery. Nothing was saved." % DASH)
        return redirect(here)
    if remind not in [str(k) for k, _l in REMIND]:
        flash("Choose when to be reminded. Nothing was saved.")
        return redirect(here)
    db.execute("INSERT INTO d664_warranty(bill_id, what, till, remind_days, set_by, set_at) VALUES(?,?,?,?,?,?) "
               "ON CONFLICT(bill_id) DO UPDATE SET what=excluded.what, till=excluded.till, remind_days=excluded.remind_days, "
               "set_by=excluded.set_by, set_at=excluded.set_at", (bid, what, till, int(remind), _who(), AR._now_ist()))
    AR._audit_bill(db, bid, "d664_warranty", {"what": what, "till": till, "remind_days": int(remind),
                                              "was": ({"what": old["what"], "till": old["till"], "remind_days": old["remind_days"]} if old else None)})
    db.commit()
    w = _warranty(db, bid)
    flash("Saved: %s %s warranty till %s. %s" % (what, DASH, _dmy(till), _remind_text(w, AR.today())))
    return redirect(here)


def init(ar):
    """Called once, at the foot of asset_register.py. Adds the column, the four addresses and two helpers the asset
    app's own pages may call (each guarded there by 'is defined', so the pages do not need this file)."""
    global AR
    AR = ar
    db = sqlite3.connect(ar.DB_PATH, timeout=20)
    try:
        ensure(db)
    finally:
        db.close()
    app = ar.app
    app.add_url_rule("/papers", "d664_papers", ar.checker_required(papers))
    app.add_url_rule("/papers/month", "d664_month", ar.checker_required(month))
    app.add_url_rule("/papers/<int:bid>", "d664_paper", ar.checker_required(paper))
    app.add_url_rule("/bills/<int:bid>/subgroup", "d664_set", ar.checker_required(set_group), methods=["POST"])
    app.add_url_rule("/papers/<int:bid>/join", "d664_join", ar.checker_required(join_page), methods=["GET", "POST"])
    app.add_url_rule("/papers/<int:bid>/unjoin", "d664_unjoin", ar.checker_required(unjoin), methods=["POST"])
    app.add_url_rule("/papers/<int:bid>/warranty", "d664_warranty", ar.checker_required(set_warranty), methods=["POST"])
    app.jinja_env.globals.update(d664_group_label=group_label, d664_to_sort=to_sort_count, d664_can_join=True,
                                 d664_warranty_label=warranty_label, d664_warranty_card=warranty_card)
    return VERSION
