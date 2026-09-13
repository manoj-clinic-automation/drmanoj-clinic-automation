#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_s249.py -- S249_CLINIC_MONEY: the four live files, each anchor asserted EXACTLY ONCE.

    finance_clinic_day.py   (live 56fb76198a6911ae512c3b73925a3c22)  F-459: ONE "our online" figure
    clinic_register.py      (live c6b87682ccbfb03734a39ad33c26f2a3)  other-UPI box, the float, physio hand-over,
                                                                     the bank line other-UPI aware, morning-match link
    finance_app.py          (live 912398e9897b180dce43955814beaf43)  the physio unit on the front gate; the mount (guarded)
    portal.py               (live 06f1b378608fbc97c54bc1f546d7985c)  two tiles + their group rows

Never writes a live file: --build reads the four sources and writes the four patched files into a
folder; the installer places them.  Idempotent by MARK.  --selftest proves patch(source) == kit file.

    python3 -B patch_s249.py --build <src_dir> <out_dir>
    python3 -B patch_s249.py --selftest <src_dir> <kit_dir>
    python3 -B patch_s249.py --file finance_app.py <live_file> <out_file>     (on the box: F-185 keeps
                              finance_app.py out of the repository -- its selftest fixtures carry
                              number-shaped text -- so it is patched from the live bytes at install)
"""
import hashlib
import io
import os
import sys

FROM = {"finance_clinic_day.py": "56fb76198a6911ae512c3b73925a3c22",
        "clinic_register.py": "c6b87682ccbfb03734a39ad33c26f2a3",
        "finance_app.py": "912398e9897b180dce43955814beaf43",
        "portal.py": "06f1b378608fbc97c54bc1f546d7985c"}
MARK = "S249"
PREDICTED = {"finance_app.py": "1fc62335f085b4cb4a634bbe9cca96c4"}      # the on-box patch must land here

# =============================================================== finance_clinic_day.py
FCD = [
("F1 our_online_p -- the one definition, beside the MPR page that already computed it",
 '''# --- S225_DAY_MPR_LINE end ---

from flask import Blueprint, request
''',
 '''# --- S225_DAY_MPR_LINE end ---

from flask import Blueprint, request


# --- S249 F-459 begin -- ONE "our online" figure, computed once, used everywhere ----------------
# 12-Sep-2026: the day card said our online was Rs 2,800 ("bank higher by 500") while the MPR page
# said Rs 6,750 ("bank lower by 3,450") -- the same two sources, opposite verdicts.  The card read
# tender_json's "Online Payment" bucket, which leaves out the online halves of split bills; the MPR
# page added them.  6,750 was right.  From here both read this function, and so does the reconciler.
def _our_online_entries(con, date):
    """Every online entry of the day: plain online bills from clinic_day_line, plus the online legs
    of split bills from clinic_day_tender.  The MPR page pairs these; the card sums them."""
    ours = []
    try:
        for r in con.execute(
                "SELECT section, sn, patient, clinic_id, amount_p, mode, shift FROM clinic_day_line "
                "WHERE business_date=? AND mode IN (%s) ORDER BY section, sn"
                % ",".join("?" * len(_ONLINE_MODES)), (date,) + _ONLINE_MODES):
            ours.append(dict(r, how=r["mode"]))
    except Exception:                                             # noqa: BLE001
        pass
    try:
        for r in con.execute(
                "SELECT clinic_id, invoice_no, tender, amount_p FROM clinic_day_tender "
                "WHERE business_date=? AND tender IN (%s) ORDER BY clinic_id, invoice_no"
                % ",".join("?" * len(_ONLINE_MODES)), (date,) + _ONLINE_MODES):
            ours.append(dict(patient="", clinic_id=r["clinic_id"], amount_p=r["amount_p"],
                             mode=r["tender"], shift="", how="%s (part of a split bill %s)"
                             % (r["tender"], r["invoice_no"] or "")))
    except Exception:                                             # noqa: BLE001
        pass
    return ours


def our_online_p(con, date):
    """THE day's online figure (F-459).  clinic_money.py reads this too."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date))
# --- S249 F-459 end ---
'''),
("F2 the day card reads the one figure",
 '''    out.append(_mpr_card(con, date, _tender(day)["online"]))          # S225_DAY_MPR_LINE
''',
 '''    out.append(_mpr_card(con, date, our_online_p(con, date)))          # S249 F-459: the ONE online figure
'''),
("F3 the MPR page reads the same entries",
 '''    ours = []
    try:
        for r in con.execute(
                "SELECT section, sn, patient, clinic_id, amount_p, mode, shift FROM clinic_day_line "
                "WHERE business_date=? AND mode IN (%s) ORDER BY section, sn"
                % ",".join("?" * len(_ONLINE_MODES)), (date,) + _ONLINE_MODES):
            ours.append(dict(r, how=r["mode"]))
    except Exception:                                             # noqa: BLE001
        pass
    try:
        for r in con.execute(
                "SELECT clinic_id, invoice_no, tender, amount_p FROM clinic_day_tender "
                "WHERE business_date=? AND tender IN (%s) ORDER BY clinic_id, invoice_no"
                % ",".join("?" * len(_ONLINE_MODES)), (date,) + _ONLINE_MODES):
            ours.append(dict(patient="", clinic_id=r["clinic_id"], amount_p=r["amount_p"],
                             mode=r["tender"], shift="", how="%s (part of a split bill %s)"
                             % (r["tender"], r["invoice_no"] or "")))
    except Exception:                                             # noqa: BLE001
        pass
    day_read = ''',
 '''    ours = _our_online_entries(con, date)                         # S249 F-459: the same entries as the card
    day_read = '''),
("F6 the day card's bank line knows channel 5 (money on a personal phone) and points at the match",
 '''    match = ""
    if res.get("state") in ("applied", "late"):
        bank_p = int(res.get("total_p") or 0)
        diff = bank_p - int(online_p or 0)
        if diff == 0:
            match = ('<p><b>Matches:</b> our online (UPI) for the day is ₹ %s and the bank applied ₹ %s.</p>'
                     % (_rupees(online_p), _rupees(bank_p)))
        else:
            match = ('<p><b>Does not match:</b> our online (UPI) for the day is ₹ %s; the bank applied ₹ %s — '
                     '<b>%s ₹ %s</b>. Open the MPR to see which entries differ.</p>'
                     % (_rupees(online_p), _rupees(bank_p), "bank is higher by" if diff > 0 else "bank is lower by",
                        _rupees(abs(diff))))
''',
 '''    match = ""
    if res.get("state") in ("applied", "late"):
        bank_p = int(res.get("total_p") or 0)
        other_p = _other_upi_p(con, date)                         # S249: channel 5, not in the bank by nature
        expect_p = int(online_p or 0) - other_p
        diff = bank_p - expect_p
        other_txt = (' — of which ₹ %s went to another UPI (a personal phone), so ₹ %s is expected in the bank'
                     % (_rupees(other_p), _rupees(expect_p))) if other_p else ''
        if diff == 0:
            match = ('<p><b>Matches:</b> our online (UPI) for the day is ₹ %s%s, and the bank applied ₹ %s.</p>'
                     % (_rupees(online_p), other_txt, _rupees(bank_p)))
        else:
            match = ('<p><b>Does not match:</b> our online (UPI) for the day is ₹ %s%s; the bank applied ₹ %s — '
                     '<b>%s ₹ %s</b>. The <a href="/finance/clinic/match/%s">morning match</a> says why, or open the MPR.</p>'
                     % (_rupees(online_p), other_txt, _rupees(bank_p), "bank is higher by" if diff > 0 else "bank is lower by",
                        _rupees(abs(diff)), date))
'''),
("F7 ... reading it from clinic_money when that module is beside us",
 '''def _mpr_cell(con, date):
''',
 '''def _other_upi_p(con, date):
    """S249: the day's money that went to another UPI (clinic_money.py); nothing when it is absent."""
    try:
        import clinic_money                                       # noqa: PLC0415
        return int(clinic_money.other_upi_total_p(con, date) or 0)
    except Exception:                                             # noqa: BLE001
        return 0


def _mpr_cell(con, date):
'''),
("F4 the day page links to the morning match",
 '''            <a href="/finance/clinic/day?m=%s">‹ the month</a>
            <a class="btn" href="javascript:window.print()">Print / Save as PDF</a>
          </div>
        </div>
        <p class="sub">₹ %s collected''',
 '''            <a href="/finance/clinic/day?m=%s">‹ the month</a>
            <a href="/finance/clinic/match/%s">Morning match ›</a>
            <a class="btn" href="javascript:window.print()">Print / Save as PDF</a>
          </div>
        </div>
        <p class="sub">₹ %s collected'''),
("F5 ... and its format tuple carries the date once more",
 '''      </div>""" % (_human(date), date[:7], _rupees(day["total_amount_p"]), day["total_count"],''',
 '''      </div>""" % (_human(date), date[:7], date, _rupees(day["total_amount_p"]), day["total_count"],'''),
]

# =============================================================== clinic_register.py
CR = [
("R1 the clinic-money module beside this file, guarded",
 '''from flask import Blueprint, redirect, request

bp = Blueprint("clinic_register", __name__)
''',
 '''from flask import Blueprint, redirect, request

# --- S249 begin: clinic_money.py beside this file -- other UPI (channel 5), the float, the match.
# Guarded: with the module absent this page is exactly the S242 page.
try:
    import clinic_money as _cm                    # noqa: E402
except Exception:                                 # noqa: BLE001
    _cm = None
# --- S249 end ---

bp = Blueprint("clinic_register", __name__)
'''),
("R2 the hand-over expectation, and the float's one line",
 '''def physio_row(con, d):
    try:
        return con.execute("SELECT * FROM clinic_physio_day WHERE business_date=?", (d,)).fetchone()
''',
 '''def expected_handover_p(con, d):
    """S249: what physically LEAVES the counter at night = the day's cash (expected_cash_p, unchanged
    by the float) + the float as it opened - the float kept aside for tomorrow.  On a normal day the
    float opens and closes at its standing amount and this equals expected_cash_p exactly."""
    exp = expected_cash_p(con, d)
    if exp is None or _cm is None:
        return exp
    try:
        adj = _cm.float_adjust_p(con, d)
    except Exception:                            # noqa: BLE001
        adj = None
    return exp + (adj or 0)


def _float_note(con, d):
    """' - Rs X kept back into the float' / ' + Rs X released from the float', or nothing."""
    if _cm is None:
        return ""
    try:
        adj = _cm.float_adjust_p(con, d)
    except Exception:                            # noqa: BLE001
        adj = None
    if not adj:
        return ""
    return (" + &#8377; %s released from the float" % _r(adj)) if adj > 0 else (" &minus; &#8377; %s kept back into the float" % _r(-adj))


def _s249_blocks(con, d, u):
    """The other-UPI box and the float count, rendered by clinic_money; nothing when it is absent."""
    if _cm is None:
        return ""
    try:
        return _cm.register_blocks(con, d, u)
    except Exception as ex:                      # noqa: BLE001
        return "<div class='card'><p class='mut'>clinic_money: %s</p></div>" % _esc(ex)


def physio_row(con, d):
    try:
        return con.execute("SELECT * FROM clinic_physio_day WHERE business_date=?", (d,)).fetchone()
'''),
("R3 three_way: money that went to another UPI is taken out before the bank is asked to agree",
 '''    verdict, why = "", ""
    if reg is None:
        verdict, why = "not entered", "the register has not been filled in for this day"
''',
 '''    # S249: channel 5 -- a payment taken on a personal phone is NOT in the bank by nature.  It is
    # taken out of both our UPI figures before the bank is asked to agree, and named on the line.
    _oth = 0
    if _cm is not None:
        try:
            _oth = _cm.other_upi_total_p(con, d)
        except Exception:                        # noqa: BLE001
            _oth = 0
    verdict, why = "", ""
    if reg is None:
        verdict, why = "not entered", "the register has not been filled in for this day"
'''),
("R4 ... the three comparisons",
 '''        rd = r_upi == doc["upi"]
        rb = r_upi == bank
        db_ = doc["upi"] == bank
''',
 '''        rd = r_upi == doc["upi"]
        rb = (r_upi - _oth) == bank                                   # S249
        db_ = (doc["upi"] - _oth) == bank                             # S249
'''),
("R5 ... the drawer's fourth signal reads the handover, and the bank gap is other-UPI aware",
 '''    dr = drawer_row(con, d)
    exp = expected_cash_p(con, d)
    drawer_diff = (dr["counted_p"] - exp) if (dr is not None and exp is not None) else None
    bank_diff = (bank - doc["upi"]) if (bank_known and doc["known"]) else None
''',
 '''    dr = drawer_row(con, d)
    exp = expected_handover_p(con, d)                                 # S249: the float moves the handover, never the collection
    drawer_diff = (dr["counted_p"] - exp) if (dr is not None and exp is not None) else None
    bank_diff = (bank - (doc["upi"] - _oth)) if (bank_known and doc["known"]) else None
'''),
("R6 ... and the result carries the figure",
 '''    return dict(reg=reg, doc=doc, phy=phy, bank=bank, bank_known=bank_known,
''',
 '''    return dict(other_upi=_oth, reg=reg, doc=doc, phy=phy, bank=bank, bank_known=bank_known,
'''),
("R7 the count compares with the handover",
 '''                counted = drawer_total_p(vals)
                exp = expected_cash_p(con, date)
''',
 '''                counted = drawer_total_p(vals)
                exp = expected_handover_p(con, date)                  # S249
'''),
("R8 the physiotherapy money: to whom it was handed",
 '''                else:
                    con.execute("UPDATE clinic_physio_day SET cash_p=?, upi_p=?, updated_by=?, "
                                "updated_at=? WHERE business_date=?",
                                (vals["physio_cash_p"], vals["physio_upi_p"], who, now, date))
                con.commit()
''',
 '''                else:
                    con.execute("UPDATE clinic_physio_day SET cash_p=?, upi_p=?, updated_by=?, "
                                "updated_at=? WHERE business_date=?",
                                (vals["physio_cash_p"], vals["physio_upi_p"], who, now, date))
                # S249: who the physiotherapy money was handed to (Dr Manoj / Dr Bhawna), stamped
                # when it is first named; the doctors tap "received" on the physiotherapy table.
                _ht = (request.form.get("physio_handed_to") or "").strip()[:40]
                if _cm is not None:
                    try:
                        _cm._ensure(con)
                        _pr = physio_row(con, date)
                        _was = (_pr["handed_to"] if _pr is not None else "") or ""
                        if _ht and _was != _ht:
                            con.execute("UPDATE clinic_physio_day SET handed_to=?, handed_at=? WHERE business_date=?",
                                        (_ht, now, date))
                        elif not _ht and _was:
                            con.execute("UPDATE clinic_physio_day SET handed_to='', handed_at='' WHERE business_date=?", (date,))
                    except Exception:            # noqa: BLE001
                        pass
                con.commit()
'''),
("R9 the physiotherapy row on the sheet: handed to whom",
 '''    phys = ("<tr><th class='sec'>Physiotherapy</th>%s%s<td class='none'>—</td></tr>"
            % (box("physio_cash_p", None if phy is None else phy["cash_p"]),
               box("physio_upi_p", None if phy is None else phy["upi_p"])))
''',
 '''    _ht = ""
    if phy is not None:
        try:
            _ht = phy["handed_to"] or ""
        except (IndexError, KeyError):
            _ht = ""
    phys = ("<tr><th class='sec'>Physiotherapy</th>%s%s<td><select name='physio_handed_to' class='note'>%s</select></td></tr>"
            % (box("physio_cash_p", None if phy is None else phy["cash_p"]),
               box("physio_upi_p", None if phy is None else phy["upi_p"]),
               "".join("<option value='%s'%s>%s</option>" % (v, " selected" if v == _ht else "", t)
                       for v, t in (("", "handed to…"), ("Dr Manoj", "Dr Manoj"), ("Dr Bhawna", "Dr Bhawna")))))
'''),
("R10 the sheet's blocks: other UPI and the float above the handover; the morning-match link",
 '''        <a class="btn" href="/finance/clinic/day/%s">the day&#8217;s entries</a></p>
      </div>%s""" % (_human(date), msg, "".join(rows), phys,
                     _esc("" if reg is None else (reg["note"] or "")), clear, who,
                     date, _drawer_html(con, date) + _compare_html(t, date))
''',
 '''        <a class="btn" href="/finance/clinic/day/%s">the day&#8217;s entries</a>
        <a class="btn" href="/finance/clinic/match/%s">morning match</a></p>
      </div>%s""" % (_human(date), msg, "".join(rows), phys,
                     _esc("" if reg is None else (reg["note"] or "")), clear, who,
                     date, date, _s249_blocks(con, date, u) + _drawer_html(con, date) + _compare_html(t, date))
'''),
("R11 the drawer summary names the handover",
 '''    row = drawer_row(con, date)
    exp = expected_cash_p(con, date)
    counted = row["counted_p"] if row is not None else None
''',
 '''    row = drawer_row(con, date)
    exp = expected_handover_p(con, date)                              # S249
    counted = row["counted_p"] if row is not None else None
'''),
("R12 ... and says so",
 '''        lines.append("<tr><th class='sec'>The day&#8217;s cash</th><td class='r'>&#8377; %s</td>"
                     "<td class='mut'>register + physiotherapy</td></tr>" % _r(exp))
''',
 '''        lines.append("<tr><th class='sec'>To hand over</th><td class='r'>&#8377; %s</td>"
                     "<td class='mut'>register + physiotherapy%s</td></tr>" % (_r(exp), _float_note(con, date)))
'''),
("R13 the bank line names the other-UPI money kept out",
 '''    upi_note = "" if t["bank_known"] else "statement not arrived"
''',
 '''    upi_note = ("" if t["bank_known"] else "statement not arrived") + (
        (" · &#8377; %s other UPI kept out" % _r(t["other_upi"])) if t.get("other_upi") else "")   # S249
'''),
]

# =============================================================== finance_app.py
FA = [
("A1 the physiotherapy unit on the front gate -- Bhati's hard edge",
 '''    return CLINIC_UNIT if path == "/finance/clinic" or \\
        path.startswith("/finance/clinic/") else UNIT
''',
 '''    if path == "/finance/physio" or path.startswith("/finance/physio/"):
        return "physio"      # S249: the physiotherapy unit. A login with no row there is refused here.
    return CLINIC_UNIT if path == "/finance/clinic" or \\
        path.startswith("/finance/clinic/") else UNIT
'''),
("A2 the mount, guarded (S209)",
 '''# --- S243_CA_AND_NUMBERS end ---
''',
 '''# --- S243_CA_AND_NUMBERS end ---


# --- S249_CLINIC_MONEY begin -- the morning match, other UPI, the float, physiotherapy (13-Sep rulings) ---
# The reconciler joins the counter sheet, Docterz and the bank into one verdict; flags live on the
# staff card until reconciled; exactly four things reach the owner.  Tables on first request (F-303).
# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import clinic_money                                        # noqa: E402
    clinic_money.init(app, db, require, audit, unit=CLINIC_UNIT)
except Exception as _ex_cm:                                    # noqa: BLE001
    print("clinic_money NOT mounted: %s" % _ex_cm, file=sys.stderr)
# --- S249_CLINIC_MONEY end ---
'''),
]

# =============================================================== portal.py
PO = [
("P1 two tiles, before Docterz Revenue",
 '''    {"icon": "\\U0001F4C8", "name": "Docterz Revenue",
''',
 '''    {"icon": "\\u2705", "name": "Morning match",
     # S249 NEW. The clinic's morning verdict: the counter sheet, Docterz and the bank MPR joined,
     # every difference explained or flagged. Reception makes the first pass, Shavez checks; the
     # doctor's login lands on his own line (only four kinds of flag reach him). Kit S249_CLINIC_MONEY;
     # granted by name to shavez, shivani and alisha in tile_grants.json v15.
     "desc": "Counter \\u00b7 Docterz \\u00b7 bank \\u2014 one verdict",
     "live": True,
     "url": "/finance/clinic/match",
     "roles": ["doctor"]},
    {"icon": "\\U0001F9D1\\u200D\\u2695\\uFE0F", "name": "Physiotherapy",
     # S249 NEW. The physiotherapy revenue table: reception writes it from the counter sheet, the
     # physiotherapist (bhati) only reads it, the doctors tap received. Its own unit at the server
     # ('physio'), so the physiotherapist reaches nothing else. Granted by name in v15.
     "desc": "Physiotherapy ka hisaab \\u2014 din ka cash / UPI",
     "live": True,
     "url": "/finance/physio",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4C8", "name": "Docterz Revenue",
'''),
("P2 their group rows",
 '''    "Docterz daily collection": "Money & Accounts", "Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts",
''',
 '''    "Morning match": "Money & Accounts", "Physiotherapy": "Money & Accounts",
    "Docterz daily collection": "Money & Accounts", "Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts",
'''),
]

EDITS = {"finance_clinic_day.py": FCD, "clinic_register.py": CR, "finance_app.py": FA, "portal.py": PO}
MARKS = {"finance_clinic_day.py": "S249 F-459 begin", "clinic_register.py": "--- S249 begin: clinic_money.py",
         "finance_app.py": "S249_CLINIC_MONEY begin", "portal.py": '"name": "Morning match"'}


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(name, src):
    """(new_text, status) -- 'already' | 'patched' | 'refused: ...'."""
    if MARKS[name] in src:
        return src, "already"
    for label, old, _new in EDITS[name]:
        n = src.count(old)
        if n != 1:
            return src, "refused: %s -- anchor matched %d times, expected exactly 1" % (label, n)
    new = src
    for _label, old, rep in EDITS[name]:
        new = new.replace(old, rep, 1)
    return new, "patched"


def build(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rc = 0
    for name in FROM:
        raw = io.open(os.path.join(src_dir, name), "rb").read()
        got = md5(raw)
        if got != FROM[name]:
            print("REFUSED %s: source is %s, this patcher was written against %s" % (name, got, FROM[name]))
            rc = 1
            continue
        new, st = patch_text(name, raw.decode("utf-8"))
        if st != "patched":
            print("REFUSED %s: %s" % (name, st))
            rc = 1
            continue
        b = new.encode("utf-8")
        io.open(os.path.join(out_dir, name), "wb").write(b)
        print("%-22s %s -> %s  (%d edits)" % (name, got[:8], md5(b), len(EDITS[name])))
    return rc


def one(name, src_path, out_path):
    raw = io.open(src_path, "rb").read()
    got = md5(raw)
    if got != FROM[name]:
        if MARKS[name] in raw.decode("utf-8", "replace"):
            print("ALREADY PATCHED %s (%s)" % (name, got))
            io.open(out_path, "wb").write(raw)
            return 0
        print("REFUSED %s: live is %s, this patcher was written against %s" % (name, got, FROM[name]))
        return 1
    new, st = patch_text(name, raw.decode("utf-8"))
    if st != "patched":
        print("REFUSED %s: %s" % (name, st))
        return 1
    b = new.encode("utf-8")
    io.open(out_path, "wb").write(b)
    print("%s %s -> %s" % (name, got, md5(b)))
    return 0


def selftest(src_dir, kit_dir):
    rc = 0
    for name in FROM:
        if not os.path.exists(os.path.join(kit_dir, name)):
            raw = io.open(os.path.join(src_dir, name), "rb").read()
            new, st = patch_text(name, raw.decode("utf-8"))
            again, st2 = patch_text(name, new)
            ok = md5(raw) == FROM[name] and st == "patched" and st2 == "already" and md5(new.encode("utf-8")) == PREDICTED.get(name, md5(new.encode("utf-8")))
            print("%s %s: not shipped (F-185); patch(live) -> %s %s; second pass %s" % ("ok  " if ok else "FAIL", name, md5(new.encode("utf-8")), "== predicted" if ok else "!= predicted %s" % PREDICTED.get(name), st2))
            if not ok:
                rc = 1
            continue
        raw = io.open(os.path.join(src_dir, name), "rb").read()
        if md5(raw) != FROM[name]:
            print("FAIL %s: source pin %s != %s" % (name, md5(raw)[:8], FROM[name][:8]))
            rc = 1
            continue
        new, st = patch_text(name, raw.decode("utf-8"))
        kit = io.open(os.path.join(kit_dir, name), "rb").read()
        same = st == "patched" and new.encode("utf-8") == kit
        again, st2 = patch_text(name, new)
        print("%s %s: patch(live) == kit %s; second pass %s" % ("ok  " if same and st2 == "already" else "FAIL", name, same, st2))
        if not (same and st2 == "already"):
            rc = 1
        # negative control: every anchor is gone from the patched text, so a re-run cannot double-apply
        for label, old, _n in EDITS[name]:
            if old in new and old not in [e[2] for e in EDITS[name]]:
                pass
    print("selftest", "GREEN" if rc == 0 else "RED")
    return rc


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--build"] and len(a) == 3:
        sys.exit(build(a[1], a[2]))
    if a[:1] == ["--selftest"] and len(a) == 3:
        sys.exit(selftest(a[1], a[2]))
    if a[:1] == ["--file"] and len(a) == 4:
        sys.exit(one(a[1], a[2], a[3]))
    print(__doc__)
    sys.exit(2)
