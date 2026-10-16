#!/usr/bin/env python3
"""make_s566.py -- S566_SCANAPP_LAST_FIXES: the three edited files rebuilt from the pinned live bytes.

    python3 make_s566.py <dir with the live sorting_desk.py, clinic_papers.py, asset_register.py> <out dir>
    python3 make_s566.py --cp-on <S563's item-3-only clinic_papers.py> <out file>     (S563's tidy fetch, re-run)

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. Every byte of each built file comes from the live file plus these edits. No new file on the box,
no new column, no data step. asset_machine.py and scanner_widget.js are not edited (pinned read-only by the installer)."""
import hashlib, os, sys

FROM = {"sorting_desk.py": "062ac43cf71b52faa16d0feee25126c5",
        "clinic_papers.py": "9a59f977226f901e06d91c312cd116b7",
        "asset_register.py": "0828fbc307d400feff2fbc0872fef686"}

# ============================================================================================ sorting_desk.py
SD_EDITS = [
    # SD1 -- the mark
    (r'''TIDY = "S563"                 # S563_SCANAPP_TIDY: Restore a set-aside paper (F-902), never straight to accepted, the statement's order
''',
     r'''TIDY = "S563"                 # S563_SCANAPP_TIDY: Restore a set-aside paper (F-902), never straight to accepted, the statement's order
LAST = "S566"                 # S566_SCANAPP_LAST_FIXES: a restore checks for a double first; every waiting paper reachable; one count
''', 1),
    # SD2 (item 1) -- the desk's marks read the two restores
    (r'''    acts = ("desk_saved", "d710_not_accepted", "desk_dup_same", "desk_dup_restored")
    sql = "SELECT bill_id, action, MAX(id) FROM bill_audit WHERE action IN (?,?,?,?)"
''',
     r'''    acts = ("desk_saved", "d710_not_accepted", "desk_dup_same", "desk_dup_restored", "desk_restored", "desk_blank_restored",
            "desk_closed_kept")                               # S566: + the restores; + a closed challan kept as a record (FIX1)
    sql = "SELECT bill_id, action, MAX(id) FROM bill_audit WHERE action IN (?,?,?,?,?,?,?)"
''', 1),
    # SD3 (items 1, 3) -- waiting(): a draft and a restored paper are selected whatever their scan day
    (r'''        "AND COALESCE(b.subgroup,'')='') OR substr(b.created_at,1,10)>=?)) "
''',
     r'''        "AND COALESCE(b.subgroup,'')='') OR substr(b.created_at,1,10)>=? "
        "OR b.status='draft' OR b.id IN (SELECT a.bill_id FROM bill_audit a WHERE a.action IN ('desk_restored','desk_blank_restored')))) "      # S566 items 1, 3
''', 1),
    (r'''            if held(b, mk):
                why.append("hold")
        if after and not live and s441_aside(b, today, days):
''',
     r'''            if held(b, mk):
                why.append("hold")
        if live and _s566_restored(mk.get(b["id"], {})):            # S566 item 1: restored, not saved on the desk since
            why.append("restored")
        if live and not why and _s566_waits(b, owner, mk.get(b["id"], {})):    # S566 item 3: a waiting paper no other list shows
            why.append("waiting")
        if after and not live and s441_aside(b, today, days):
''', 1),
    # SD3b (FIX1, K1 CORRECTION 2) -- a desk Save of a closed challan keeps it as a record (no Bills-awaited line), audited
    (r'''    b = _row(db, bid)
    if accept and _lane(b) == "clinic" and b["status"] == "draft":
        if _challan_waits(b):
            msgs.append("A challan: filed, waiting for its bill (Bills awaited).")
''',
     r'''    b = _row(db, bid)
    if (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "") == "closed" and b["status"] == "draft":   # S566 FIX1
        AR._audit_bill(db, bid, "desk_closed_kept", {"via": "desk"})
        msgs.append("%s is a closed challan — kept as a record; no bill will come." % st)
    elif accept and _lane(b) == "clinic" and b["status"] == "draft":
        if _challan_waits(b):
            msgs.append("A challan: filed, waiting for its bill (Bills awaited).")
''', 1),
    # SD4 (items 1, 3) -- the two reasons' words in the list
    (r'''    fx = _s560_fix_hint(db, b, why)                                 # S560 item 7: the reason, in the list
    if fx:
        return fx
''',
     r'''    fx = _s560_fix_hint(db, b, why)                                 # S560 item 7: the reason, in the list
    if fx:
        return fx
    if "restored" in why:                                           # S566 item 1
        return "restored — sort it"
    if why == ["waiting"]:                                          # S566 item 3
        return ("challan — supplier not read" if ((b["doc_kind"] or "") == "challan" and not _key(b["vendor"]))
                else "not accepted yet — check")
''', 1),
    # SD5 (item 4) -- the one list Bills awaited shows and the menu counts
    (r'''def reading(db, bid):
    """Claude's reading of the paper (S550): rows with ok=1 only; None when there is none or the table is absent."""
''',
     r'''def awaited_open(db, owner):
    """S566 item 4: the open challans the Bills awaited page lists for this viewer -- every awaiting_challans row; a challan
    whose supplier is not read is in its own card ('Supplier not read'), never dropped. The menu's count is len() of this."""
    return list(awaiting_challans(db, owner))


def reading(db, bid):
    """Claude's reading of the paper (S550): rows with ok=1 only; None when there is none or the table is absent."""
''', 1),
    (r'''            cards[key] = {"key": key, "name": names.get(key) or vendor or key, "mode": md.get(key, ""), "rows": [],
                          "unpaid": [], "what": set(), "n_wait": 0}
''',
     r'''            cards[key] = {"key": key, "name": (names.get(key) or vendor or key) if key else "Supplier not read",
                          "mode": md.get(key, "") if key else "", "rows": [],
                          "unpaid": [], "what": set(), "n_wait": 0, "noread": not key}      # S566 item 4: its own card
''', 1),
    (r'''    for c in awaiting_challans(db, owner):
        key = _key(c["vendor"])
        if not key:
            continue
        cd = card(key, c["vendor"])
''',
     r'''    for c in awaited_open(db, owner):                               # S566 item 4: the list the menu counts
        key = _key(c["vendor"])                                     # '' = supplier not read: its own card, never dropped
        cd = card(key, c["vendor"])
''', 1),
    (r'''            foot = "%d open challan%s · set how this supplier bills" % (n, "" if n == 1 else "s")
        cd["foot"] = foot
''',
     r'''            foot = "%d open challan%s · set how this supplier bills" % (n, "" if n == 1 else "s")
        if cd["noread"]:                                            # S566 item 4
            foot = "%d challan%s with no supplier read · open each on the desk and type the supplier" % (n, "" if n == 1 else "s")
        cd["foot"] = foot
''', 1),
    (r'''    out.sort(key=lambda c: c["name"].lower())
    return out, amber_days
''',
     r'''    out.sort(key=lambda c: (c["noread"], c["name"].lower()))      # S566: 'Supplier not read' last
    return out, amber_days
''', 1),
    (r'''<div style="display:flex;flex-direction:column;gap:6px"><span class="muted small">How they bill</span>
''',
     r'''{% if not s.noread %}<div style="display:flex;flex-direction:column;gap:6px"><span class="muted small">How they bill</span>
''', 1),
    (r'''<span style="font-size:13px;color:#3d4a57;background:#f3f5f8;border-radius:8px;padding:8px 10px">{{s.rule}}</span></div>
''',
     r'''<span style="font-size:13px;color:#3d4a57;background:#f3f5f8;border-radius:8px;padding:8px 10px">{{s.rule}}</span></div>
{% else %}<span id=s566noread style="font-size:13px;color:#3d4a57;background:#f3f5f8;border-radius:8px;padding:8px 10px">The supplier is not read on these challans. Open each on the sorting desk and type the supplier; it then joins that supplier's card.</span>{% endif %}
''', 1),
    # SD6 (item 6) -- The month's money selection factored out, so the home card reads the same rows and the same sum
    (r'''        ph = ",".join("?" * len(subs))
        if key == "construction":
            live = CP._live_sections(db)
            lanes = "COALESCE(b.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND b.status IN ('draft','approved','captured')"
        else:
            live = CP._live(db)
            lanes = "COALESCE(b.lane,'clinic')='clinic' AND b.status IN ('draft','approved')"
        money = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                           subs + (ym,)).fetchall()
        finals = db.execute("SELECT b.* FROM bills b WHERE " + lanes + " AND b.dup_of IS NULL AND b.page_of IS NULL AND b.doc_kind='challan' "
                            "AND b.challan_state='final' AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.id", subs + (ym,)).fetchall()
''',
     r'''        ph = ",".join("?" * len(subs))
        lanes = _s566_lanes(key)
        money, finals = _s566_paid_rows(db, key, subs, ym)           # S566 item 6: the one selection month_total reads too
''', 1),
    (r'''        total = sum((b["total_amount"] or 0) for b in paid_rows)
''',
     r'''        total = _s566_total(paid_rows)                               # S566 item 6: the one sum
''', 1),
    # SD7 (item 8) -- /desk?open= takes the stamp in any common form; an unknown or refused value says so
    (r'''    """S559 item 3: (the paper's id, False) when /desk?open= names a paper this person may open on the desk -- by id, or by
    its stamp (B-0125); (0, True) when it names one that is unknown or refused (never pharmacy; Personal only for the owner);
    (0, False) when nothing is named. The same rule as picking it in the list (_visible)."""
    v = re.sub(r"\s+", "", str(v or ""))[:20]
    if not v:
        return 0, False
    try:
        b = _row(db, int(v)) if v.isdigit() else _by_stamp(db, v)
    except (ValueError, OverflowError, sqlite3.Error):
        b = None
    if b is None or _visible(b, owner):
        return 0, True
    return b["id"], False
''',
     r'''    """S559 item 3: (the paper's id, '') when /desk?open= names a paper this person may open on the desk -- by id, or by
    its stamp; (0, the line) when it names one that is unknown ('No paper <typed>') or refused (_visible's reason: never
    pharmacy; Personal only for the owner); (0, '') when nothing is named. S566 item 8: a bare number stays the record id
    (every link the app makes carries it); a stamp is read as B-0162, b-0162, B-162, B162 or b162 (_s566_stamp_form)."""
    v = re.sub(r"\s+", "", str(v or ""))[:20]
    if not v:
        return 0, ""
    try:
        b = _row(db, int(v)) if v.isdigit() else _by_stamp(db, _s566_stamp_form(v))
    except (ValueError, OverflowError, sqlite3.Error):
        b = None
    if b is None:
        return 0, "No paper %s" % v
    err = _visible(b, owner)
    if err:
        return 0, err
    return b["id"], ""
''', 1),
    (r'''{% if cant %}<span id=s559cant style="font-size:13px;color:#6b7785">That paper can't be opened here</span>{% endif %}''',
     r'''{% if cant %}<span id=s559cant style="font-size:13px;color:#6b7785">{{cant}}</span>{% endif %}''', 1),
    # SD8 (item 1) -- the blank fix's restore says a refusal plainly (DeskError), not as a failure
    (r'''        AR._audit_bill(db, bid, "desk_fix_answered", {"answer": ans, "fix": f[0], "via": "desk"})
        db.commit()
    except Exception as e:                                           # noqa: BLE001
''',
     r'''        AR._audit_bill(db, bid, "desk_fix_answered", {"answer": ans, "fix": f[0], "via": "desk"})
        db.commit()
    except DeskError as e:                                           # S566 item 1: 'This looks like B-xxxx — open it instead.'
        db.rollback()
        return jsonify(ok=False, error=str(e)), e.code
    except Exception as e:                                           # noqa: BLE001
''', 1),
    # SD9 (item 1) -- the one restore runs the duplicate check first, on every lane
    (r'''    back = AR._lane_kind_status(_lane(b))[1]
    db.execute("UPDATE bills SET status=?, reject_reason=NULL, approved_by=NULL, approved_at=NULL WHERE id=? AND status='rejected'",
''',
     r'''    hit = _s566_restore_dup(db, b)                                 # S566 item 1 (N5): never counted twice blind, on every lane
    if hit is not None:
        raise DeskError("This looks like %s — open it instead." % _stamp(hit))
    back = AR._lane_kind_status(_lane(b))[1]
    db.execute("UPDATE bills SET status=?, reject_reason=NULL, approved_by=NULL, approved_at=NULL WHERE id=? AND status='rejected'",
''', 1),
    # SD10 -- the S566 helpers
    (r'''# --- S563_SCANAPP_TIDY end ---
''',
     r'''# --- S563_SCANAPP_TIDY end ---


# ---------------------------------------------------------------------------------------------- S566_SCANAPP_LAST_FIXES
def _s566_restore_dup(db, b):
    """S566 item 1 (S563-K1-N5): before a set-aside paper is restored, on every lane, the live paper (not rejected, any
    status) it would be a second count of -- (a) AR._dup_by_triple's exact match on the row; (b) when the row has no supplier
    or no amount, the same exact triple built from Claude's reading (supplier, number, amount; AR._triple's normalisation)
    against the bills of the last AR.DUP_WINDOW_DAYS; (c) the same capture again (AR._dup_by_fp, fine distance at most
    AR.DUP_EXACT). The row found, else None. Reads only."""
    bid = b["id"]
    try:
        exact, _near = AR._dup_by_triple(db, bid)
    except Exception:                                                # noqa: BLE001
        exact = None
    if exact is not None:
        return exact
    if not (b["vendor"] or "").strip() or b["total_amount"] is None:
        rd = reading(db, bid)
        if rd and (rd.get("supplier") or "").strip() and (rd.get("number") or "").strip() and rd.get("amount") is not None:
            v, n, t = AR._triple({"vendor": rd["supplier"], "bill_no": rd["number"], "total_amount": rd["amount"]})
            since = (datetime.date.today() - datetime.timedelta(days=AR.DUP_WINDOW_DAYS)).isoformat()
            for r in db.execute("SELECT id, stamp_no, vendor, bill_no, total_amount FROM bills WHERE id<>? AND status<>'rejected' "
                                "AND substr(created_at,1,10)>=? ORDER BY id ASC LIMIT 2000", (bid, since)):
                if AR._triple(r) == (v, n, t) and v and n:
                    return r
    fp, fpc = _col(b, "fp"), _col(b, "fpc")
    if fp and fpc:
        try:
            r, df, _dc = AR._dup_by_fp(db, bid, fp, fpc)
        except Exception:                                            # noqa: BLE001
            r, df = None, None
        if r is not None and df is not None and df <= AR.DUP_EXACT:
            return r
    return None


def _s566_restored(m):
    """S566 item 1: the newest desk_restored / desk_blank_restored mark is newer than the newest desk_saved (from _marks)."""
    r = max(m.get("desk_restored", 0) or 0, m.get("desk_blank_restored", 0) or 0)
    return bool(r and r > (m.get("desk_saved", 0) or 0))


def _s566_waits(b, owner, m=None):
    """S566 item 3: a paper whose status reads 'Waiting' (draft) that no other list shows -- not a double scan, not a page,
    not the pharmacy lane, not a patient's paper, Personal only for the owner; EXCEPT an awaiting challan whose supplier is
    read (it is on Bills awaited), a clinic_equipment paper for anyone but the owner (it waits on Dr Manoj's Save), and
    (FIX1, K1 CORRECTION 2) a closed challan a desk Save has kept as a record (its desk_closed_kept mark in `m`, from _marks).
    Whatever its scan day and whether or not it was saved on the desk before. Nothing is written (D664)."""
    if b["status"] != "draft" or b["dup_of"] or b["page_of"] or _lane(b) == "pharmacy":
        return False
    if (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "") == "closed" and (m or {}).get("desk_closed_kept"):
        return False
    sg = b["subgroup"] or ""
    if sg == PATIENT or (sg == "personal" and not owner):
        return False
    if (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "awaiting") == "awaiting" and _key(b["vendor"]):
        return False
    if sg == "clinic_equipment" and not owner:
        return False
    return True


def _s566_stamp_form(v):
    """S566 item 8: B-0162, b-0162, B-162, B162, b162 -> 'B-0162'; anything else as typed (_by_stamp reads it as before)."""
    m = re.fullmatch(r"[Bb]-?0*(\d{1,6})", v or "")
    return ("B-%04d" % int(m.group(1))) if m else v


def _s566_lanes(key):
    """S566 item 6: the lanes / statuses a section's challans are read from (month_data's own two strings)."""
    if key == "construction":
        return "COALESCE(b.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND b.status IN ('draft','approved','captured')"
    return "COALESCE(b.lane,'clinic')='clinic' AND b.status IN ('draft','approved')"


# FIX1 (K1 BLOCKER 1): the SQL twin of held() -- a D710-held double (a clinic draft whose d710_not_accepted is newer than its
# last desk_saved, not yet answered) is never money: it drops out of The month and the home card until someone answers it.
_S566_NOT_HELD = (" AND NOT (b.status='draft' AND COALESCE(b.lane,'clinic')='clinic' AND COALESCE(b.dup_flag,'')='' "
                  "AND EXISTS (SELECT 1 FROM bill_audit h WHERE h.bill_id=b.id AND h.action='d710_not_accepted' AND h.id > "
                  "COALESCE((SELECT MAX(s.id) FROM bill_audit s WHERE s.bill_id=b.id AND s.action='desk_saved'),0)))")


def _s566_paid_rows(db, key, subs, ym):
    """S566 item 6: (money, finals) -- month_data's own two queries for one section, now shared; FIX1: both leave out a
    D710-held double (_S566_NOT_HELD), so the accepted original counts once."""
    ph = ",".join("?" * len(subs))
    live = CP._live_sections(db) if key == "construction" else CP._live(db)
    lanes = _s566_lanes(key)
    money = db.execute("SELECT b.* FROM bills b WHERE " + live + _S566_NOT_HELD + " AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                       subs + (ym,)).fetchall()
    finals = db.execute("SELECT b.* FROM bills b WHERE " + lanes + " AND b.dup_of IS NULL AND b.page_of IS NULL" + _S566_NOT_HELD + " AND b.doc_kind='challan' "
                        "AND b.challan_state='final' AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.id", subs + (ym,)).fetchall()
    return money, finals


def _s566_total(paid_rows):
    """S566 item 6: a section's total -- the one sum, month_data's and month_total's."""
    return sum((b["total_amount"] or 0) for b in paid_rows)


def month_total(db, ym, owner=True):
    """S566 item 6: The month's grand total -- the sum of its section totals (the same rows, the same sum; no items loop).
    The home card's 'Spend this month' reads this. `owner` kept for the caller's clarity (no section is Personal)."""
    tot = 0
    for key, _nm, subs in MONTH_SECTIONS:
        money, finals = _s566_paid_rows(db, key, subs, ym)
        tot += _s566_total(list(money) + list(finals))
    return tot


# --- S566_SCANAPP_LAST_FIXES end ---
''', 1),
]

# ============================================================================================ clinic_papers.py
CP_EDITS = [
    (r'''TIDY = "S563"                # S563: Bills awaited filters a patient's / Personal challan as the desk does; consolidated
''',
     r'''TIDY = "S563"                # S563: Bills awaited filters a patient's / Personal challan as the desk does; consolidated
LAST = "S566"                # S566: the old challan doors check on the server; a half-read bill date takes no month
''', 1),
    # CP2 (item 5, R1 point 7) -- a bill date that is not yyyy-mm-dd gives no month (the scan month, as for an empty date)
    (r'''MONTH_OF = ("COALESCE(NULLIF(b.bill_month,''), substr(NULLIF(b.bill_date,''),1,7), "
''',
     r'''MONTH_OF = ("COALESCE(NULLIF(b.bill_month,''), CASE WHEN b.bill_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' THEN substr(b.bill_date,1,7) END, "
''', 1),
    # CP3 (item 2) -- the one helper the old challan doors call first
    (r'''def challan_close(bid):
''',
     r'''def _s566_door(db, ids):
    """S566 item 2 (S563-K1-N6): '' when this person may act on every paper in `ids` from the old pages' POST doors; else one
    plain line (nothing is written by the caller). Refused: a challan with subgroup 'patient_paper', for anyone; any paper
    with subgroup 'personal', for anyone but the owner -- the filters S563 put on the page's lists."""
    try:
        owner = bool(AR.is_owner())
    except Exception:                                                # noqa: BLE001
        owner = False
    for i in ids:
        b = db.execute("SELECT id, stamp_no, doc_kind, subgroup FROM bills WHERE id=?", (i,)).fetchone()
        if not b:
            continue
        sg = b["subgroup"] or ""
        if sg == "patient_paper" and (b["doc_kind"] or "") == "challan":
            return "%s is a patient's challan — it is kept apart for the case pack. Nothing was changed." % _stamp(b)
        if sg == "personal" and not owner:
            return "Personal papers are the owner's alone. Nothing was changed."
    return ""


def challan_close(bid):
''', 1),
    (r'''    back = _back("d664_challans")
    if not _has_challans(db) or (b["doc_kind"] or "") != "challan" or (b["challan_state"] or "awaiting") != "awaiting":
''',
     r'''    back = _back("d664_challans")
    err = _s566_door(db, [bid])                                      # S566 item 2
    if err:
        flash(err)
        return redirect(back)
    if not _has_challans(db) or (b["doc_kind"] or "") != "challan" or (b["challan_state"] or "awaiting") != "awaiting":
''', 1),
    (r'''    back = _back("d664_challans")
    if not _has_challans(db) or (c["doc_kind"] or "") != "challan" or (c["challan_state"] or "") != "joined" or not c["challan_of"]:
''',
     r'''    back = _back("d664_challans")
    err = _s566_door(db, [bid])                                      # S566 item 2
    if err:
        flash(err)
        return redirect(back)
    if not _has_challans(db) or (c["doc_kind"] or "") != "challan" or (c["challan_state"] or "") != "joined" or not c["challan_of"]:
''', 1),
    (r'''        pages, refused = [], []
        for i in sorted(ids):
''',
     r'''        err = _s566_door(db, [bid] + ids)                            # S566 item 2: the head, every page and the 'also' paper
        if err:
            flash(err)
            return redirect(url_for("d664_join", bid=bid, back=back))
        pages, refused = [], []
        for i in sorted(ids):
''', 1),
    (r'''    rows = _last_batch(db, bid)
    if not rows:
        flash("There is no join of %s to undo." % _stamp(head))
''',
     r'''    err = _s566_door(db, [bid])                                      # S566 item 2: the head
    if err:
        flash(err)
        return redirect(here)
    rows = _last_batch(db, bid)
    if not rows:
        flash("There is no join of %s to undo." % _stamp(head))
''', 1),
    # CP8, CP9 (R1 note 18, bound by the brief) -- the old pages' warranty and Dr MK / Dr Bhawna POSTs call the same helper
    (r'''    stamp = _stamp(b)
    if not _on_expense(b):
        flash("%s is not a personal expense, so no warranty is kept for it. Move it there first." % stamp)
''',
     r'''    stamp = _stamp(b)
    err = _s566_door(db, [bid])                                      # S566 (R1 note 18): a Personal paper, the owner only
    if err:
        flash(err)
        return redirect(here)
    if not _on_expense(b):
        flash("%s is not a personal expense, so no warranty is kept for it. Move it there first." % stamp)
''', 1),
    (r'''        abort(403)                                                   # F-891: a Personal paper is the owner's alone
    if not _on_expense(b):
        flash("%s is not a personal expense." % _stamp(b))
''',
     r'''        abort(403)                                                   # F-891: a Personal paper is the owner's alone
    err = _s566_door(db, [bid])                                      # S566 (R1 note 18): the same helper as the challan doors
    if err:
        flash(err)
        return redirect(_back())
    if not _on_expense(b):
        flash("%s is not a personal expense." % _stamp(b))
''', 1),
]

# ============================================================================================ asset_register.py
AR_EDITS = [
    # AR1 (item 6) -- the home card's Spend this month = The month's grand total (one source)
    (r'''    month_spend = 0
    if is_owner():
        _tym = datetime.date.today().strftime("%Y-%m")
        month_spend = db.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM bills WHERE status='approved' "
            "AND substr(bill_date,1,7)=?", (_tym,)).fetchone()[0]
''',
     r'''    month_spend = 0
    if is_owner():
        _sd566 = _s559_desk_mod()                                    # S566 item 6: The month's own grand total, one source
        try:
            month_spend = _sd566.month_total(db, _sd566._today().strftime("%Y-%m"), True) if (_sd566 is not None and hasattr(_sd566, "month_total")) else None
        except Exception as _ex566:                                  # noqa: BLE001
            print("S566 home total: %s" % _ex566, file=_sys.stderr)
            month_spend = None
        if month_spend is None:                                      # the desk not mounted: as before
            _tym = datetime.date.today().strftime("%Y-%m")
            month_spend = db.execute(
                "SELECT COALESCE(SUM(total_amount),0) FROM bills WHERE status='approved' "
                "AND substr(bill_date,1,7)=?", (_tym,)).fetchone()[0]
''', 1),
    # AR2, AR3 (item 7) -- the stored word 'None' (or empty) shows blank on the Machines list and the machine page
    (r'''<td>{{a['contract_type']}}{% set d = due.get(a['id']) %}''',
     r'''<td>{{a['contract_type']|s566_contract}}{% set d = due.get(a['id']) %}''', 1),
    (r'''<b>Contract:</b> {{a['contract_type']}}{% if a['provider'] %}''',
     r'''<b>Contract:</b> {{a['contract_type']|s566_contract}}{% if a['provider'] %}''', 1),
    # AR4 (item 5, R1 point 8) -- 'approved by' only for an approved paper; 'rejected by' as before
    (r'''{% if b['approved_by'] %}<span class=muted>{{'rejected' if b['status']=='rejected' else 'approved'}} by <b>{{b['approved_by']}}</b> {{b['approved_at'] or ''}}</span><br>{% endif %}''',
     r'''{% if b['approved_by'] and b['status'] in ('approved','rejected') %}<span class=muted>{{'rejected' if b['status']=='rejected' else 'approved'}} by <b>{{b['approved_by']}}</b> {{b['approved_at'] or ''}}</span><br>{% endif %}''', 1),
    # AR5 (item 5) -- a stored date that is not yyyy-mm-dd shows as written, with the misread flag
    (r'''<b>Date:</b> {{b['bill_date'] or '—'}}{% if b['late_for'] %}''',
     r'''<b>Date:</b> {{b['bill_date'] or '—'}}{% if s566_bad_date is defined and s566_bad_date(b['bill_date']) %} <span class="badge amber" id=s566date>date looks misread — check</span>{% endif %}{% if b['late_for'] %}''', 1),
    # AR6 (item 5, R1 point 6) -- the reading's fill writes a bill date only as yyyy-mm-dd (the pharmacy lane's fill unchanged)
    (r'''                                 ("bill_date", "bill_date", _norm_date),
''',
     r'''                                 ("bill_date", "bill_date", (_norm_date if _s566_pharm(b) else _s566_full_date)),      # S566 item 5
''', 1),
    # AR7 (item 5) -- the new-bill page refuses a date it cannot read in full (before the stamp is taken)
    (r'''        stamp = next_stamp(db)
        if is_owner() or kind == "Consumable":
''',
     r'''        if _s566_typed_date(f.get("bill_date")) is False:            # S566 item 5: refused, nothing saved
            flash(S566_DATE_LINE % (f.get("bill_date") or "").strip()[:20])
            return redirect(url_for("bill_new"))
        stamp = next_stamp(db)
        if is_owner() or kind == "Consumable":
''', 1),
    # AR8 (item 5) -- the old edit page the same, for a date the person typed (FIX1, K1 CORRECTION 3: a stored value left
    # as it was shown passes, as the desk's typed_date does -- _norm_date writes it back unchanged)
    (r'''    if request.method == "POST":
        f = request.form
        # 'Pharmacy' MUST be in this whitelist: it is a fall-through to
''',
     r'''    if request.method == "POST":
        f = request.form
        if ((f.get("bill_date") or "").strip() != (b["bill_date"] or "").strip()
                and _s566_typed_date(f.get("bill_date")) is False):     # S566 item 5: a newly typed partial date refused, nothing saved
            flash(S566_DATE_LINE % (f.get("bill_date") or "").strip()[:20])
            return redirect(url_for("bill_edit", bid=bid))
        # 'Pharmacy' MUST be in this whitelist: it is a fall-through to
''', 1),
    # AR9 (item 5) -- the intake's prefill: a date not read in full is left empty (the pharmacy lane as before)
    (r'''         (_norm_date(pf.get("bill_date")) if pf.get("bill_date") else None),
''',
     r'''         ((_norm_date(pf.get("bill_date")) if _lane == "pharmacy" else _s566_full_date(pf.get("bill_date"))) if pf.get("bill_date") else None),   # S566 item 5
''', 1),
    # AR10 (item 4) -- the menu's Bills awaited count = len() of the page's own list
    (r'''        return len(sd.awaiting_challans(get_db(), r == "owner"))
''',
     r'''        return len(sd.awaited_open(get_db(), r == "owner") if hasattr(sd, "awaited_open") else sd.awaiting_challans(get_db(), r == "owner"))   # S566 item 4
''', 1),
    # AR11 -- the mark and the S566 helpers
    (r'''# ---------------------------------------------------------------- main
''',
     r'''# --- S566_SCANAPP_LAST_FIXES begin -- a date never stored half-read; 'None' never shown as a contract (16-Oct-2026) ---
LAST_S566 = "S566"
S566_DATE_LINE = "The bill date '%s' is not a full date — type it as dd-mm-yyyy (or leave it empty). Nothing was saved."


def _s566_full_date(s):
    """S566 item 5: _norm_date's answer only when it is a real yyyy-mm-dd; else None (the field is left empty)."""
    v = _norm_date(s)
    if not v or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v)):
        return None
    try:
        datetime.date.fromisoformat(v)
    except ValueError:
        return None
    return v


def _s566_typed_date(s):
    """S566 item 5: a person's typed bill date -- None when empty, the yyyy-mm-dd when it reads in full, False (refuse)."""
    if s is None or not str(s).strip():
        return None
    v = _s566_full_date(s)
    return v if v else False


def _s566_pharm(b):
    """S566 item 5: the pharmacy lane (its fill is the Sanjeevni side's, unchanged byte for byte)."""
    try:
        return (b["lane"] or KIND_LANE.get(b["kind"], "clinic")) == "pharmacy"
    except Exception:                                                # noqa: BLE001
        return False


def _s566_bad_date(s):
    """S566 item 5: a stored bill date that is not yyyy-mm-dd (shown as written, with the misread flag)."""
    s = (s or "").strip() if isinstance(s, str) else s
    if not s:
        return False
    return _s566_full_date(s) != s


def _s566_contract(v):
    """S566 item 7: the stored word 'None' (the column's default and the form's first choice) or an empty value -> blank;
    the same test as asset_machine._old_record. Stored values unchanged."""
    v = (v or "").strip() if isinstance(v, str) else ("" if v is None else str(v))
    return "" if v in ("", "None") else v


app.jinja_env.filters["s566_contract"] = _s566_contract
app.jinja_env.globals.update(s566_bad_date=_s566_bad_date)
# --- S566_SCANAPP_LAST_FIXES end ---


# ---------------------------------------------------------------- main
''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    n = 0
    for i, (old, new, cnt) in enumerate(edits, 1):
        got = text.count(old)
        if got != cnt:
            raise SystemExit("REFUSED: %s edit %d: the anchor is found %d times, not %d:\n  %s" % (name, i, got, cnt, old[:160]))
        text = text.replace(old, new)
        n += 1
    return text, n


def cp_on_item3(src, out):
    """--cp-on: S566's clinic_papers edits on S563's item-3-only clinic_papers.py (make_s563.py --cp-item3-only, pin
    CP_ITEM3), for S563's tidy fetch re-run on the S566 files: with the other files at S566's TO, this file and the S566 TO
    clinic_papers.py must serve the same bytes (the tidy still changes nothing a page serves)."""
    raw = open(src, "rb").read()
    if md5(raw) != CP_ITEM3:
        raise SystemExit("REFUSED: %s is %s, not S563's item-3-only clinic_papers.py %s" % (src, md5(raw)[:8], CP_ITEM3[:8]))
    text, n = apply("clinic_papers.py (item 3 only)", raw.decode("utf-8"), CP_EDITS)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("clinic_papers.py (S563 item 3 only) %s -> %s  (%d counted edits, each anchor exactly once)" % (CP_ITEM3[:8], md5(text.encode("utf-8"))[:8], n))


CP_ITEM3 = "717043418fd39ba2b4574a4bd28efdc6"


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if "--cp-on" in sys.argv and len(a) == 2:
        return cp_on_item3(a[0], a[1])
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    plan = {"sorting_desk.py": SD_EDITS, "clinic_papers.py": CP_EDITS, "asset_register.py": AR_EDITS}
    built = {}
    for f, edits in plan.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5(raw) != FROM[f]:
            raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
        text, n = apply(f, raw.decode("utf-8"), edits)
        built[f] = (text.encode("utf-8"), n)
    for f, (b, n) in built.items():
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("%-18s %s -> %s  (%d counted edit%s, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n, "" if n == 1 else "s"))


if __name__ == "__main__":
    main()
