#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s691.py -- kit S691_LISTS_FILM_STUDY (session 374, 01-Nov-2026, the parent). Counted edits on the three FROM files.
    python3 make_s691.py <from_dir> <to_dir>
Every edit names its anchor and must find it EXACTLY once (else exit, nothing written). The installer re-runs this on the
box's live files and must get the same bytes as TO_PINS.md5. No patient name, no number, no secret (F-185)."""
import hashlib
import os
import sys

FROM = {"owner_sheets.py": "baa7ccc405a78bdbbd8b2485c00dc9a0",
        "xray_film.py": "c08a10163295d5ab5919472e01977c12",
        "clinic_lists.py": "6118ef4da88ada966752a8c0340828a7"}
EDITS = {k: [] for k in FROM}


def E(f, old, new, tag):
    EDITS[f].append((old, new, tag))


def between(text, a, b, tag):
    i = text.find(a)
    if i < 0 or text.find(a, i + 1) >= 0:
        sys.exit("make_s691: %s start anchor found %d times" % (tag, text.count(a)))
    j = text.find(b, i)
    if j < 0:
        sys.exit("make_s691: %s end anchor missing" % tag)
    return text[i:j + len(b)]


# ===================================================================================== xray_film.py
X = "xray_film.py"
E(X, 'VERSION = "S688-XRAY-FILM-1.0"', 'VERSION = "S691-XRAY-FILM-1.1"', "x-version")
E(X, "the films on that day's PAID X-ray slips per\n",
  "the films on that day's X-ray slips (S691: every 'ok' slip -- billed is done, D775) per\n", "x-doc4")
E(X, "every paid X-ray slip line, day by day", "every X-ray slip line, day by day", "x-doc8a")
E(X, "study, film size, films, paid mode. Month picker",
  "study, film size, films, Paid as Docterz shows it (S691). Month picker", "x-doc8b")
E(X, '''FILM_SUBS = ("xray_small", "xray_11x14", "xray")                    # the Scan App's X-ray film groups (sorting_desk "xray")''',
  '''FILM_SUBS = ("xray_small", "xray_11x14", "xray")                    # the Scan App's X-ray film groups (sorting_desk "xray")
FILMS_MAX = 6                                                       # S691: films per study, 1..6 (was 1..4)
GLUCO_P = 5000                                                      # Rs 50: Docterz bills the glucometer under X-ray (clinic_lists)
DZ_MODE = {"cash": "Cash", "online payment": "UPI", "upi": "UPI", "debit card": "Card", "credit card": "Card", "card": "Card",
           "split payment": "Paid (two ways)"}                    # his ruling of 13-Oct: never the words "split payment"
SCANAPP_XRAY = "/scanapp/xray"                                      # the Scan App's own X-ray costs page (every film bill)''', "x-consts")
E(X, '''        out[r[0]] = (r[1] or "", int(r[2] or 1), int(r[3] or 0))
    return out
''', '''        out[r[0]] = (r[1] or "", int(r[2] or 1), int(r[3] or 0))
    return out


def set_study(con, sid, size, films, both_one, who):
    """S691 (the owner, 06:55 IST 01-Nov): one study's film size and films. His X-rays & procedures page (owner_sheets.py) --
    the Add row and each X-ray line -- writes through here; so does this module's own owner form. A new row each time (the
    newest row wins; nothing is overwritten). ValueError on anything else."""
    _ensure(con)
    try:
        sid, films, both_one = int(sid), int(films), int(both_one)
    except (TypeError, ValueError):
        raise ValueError("film size 8x10 or 11x14, films 1 to %d" % FILMS_MAX)
    ok = con.execute("SELECT 1 FROM owner_service WHERE id=? AND kind='xray'", (sid,)).fetchone()
    if not ok:
        raise ValueError("no such X-ray on the list")
    if size not in SIZE_KEYS + ("",) or not (1 <= films <= FILMS_MAX) or both_one not in (0, 1):
        raise ValueError("film size 8x10 or 11x14, films 1 to %d" % FILMS_MAX)
    rid = con.execute("INSERT INTO xf_study (service_id, size, films, both_one, set_at, set_by) VALUES (?,?,?,?,?,?)",
                      (sid, size, films, both_one, _stamp(), who)).lastrowid
    con.commit()
    _audit_safe(con, "xf_study", rid, "set", None, dict(service_id=sid, size=size, films=films, both_one=both_one), who)
    return rid


def fy_start(day):
    """1 April of the financial year the day falls in."""
    return dt.date(day.year if day.month >= 4 else day.year - 1, 4, 1)


def docterz_paid(con, d0, d1):
    """S691 (the owner, 06:32-06:43 IST 01-Nov; D775): Paid is read from Docterz, never from a room tick (the room's ticks were
    retired on 24-Oct). Per patient, day and kind (xray | proc): the total of the 'ok' X-ray/Proc slip lines (rate - discount)
    against that day's Docterz charges of the same section -- a Docterz X-ray charge of Rs 50 is the glucometer and counts under
    procedures when that patient has a Rs 50 procedure line that day (clinic_lists' rule). {(day, clinic_id, kind): (code,
    mode, docterz_p)}: 'ok' (equal; mode is Docterz's -- Cash, UPI, Card, or "Paid (two ways)"), 'differ' (Docterz charged
    docterz_p for that patient that day, all lines of the kind together),
    'none' (that day's Docterz report is in, this patient's charge is not), 'wait' (no Docterz report for that day yet),
    'free' (the slip's total is 0). A line with no clinic ID matches nothing: 'none' or 'wait'. Reads only."""
    slip, gl = {}, set()
    for r in con.execute("SELECT s.day, s.clinic_id, i.kind, COALESCE(i.price_p, 0), COALESCE(i.discount_p, 0) FROM slip s "
                         "JOIN slip_item i ON i.slip_id = s.id AND i.kind IN ('xray', 'proc') "
                         "WHERE s.series = 'xp' AND s.state = 'ok' AND s.day >= ? AND s.day <= ?", (str(d0), str(d1))):
        k = (r[0], str(r[1] or "").strip(), r[2])
        slip[k] = slip.get(k, 0) + int(r[3] or 0) - int(r[4] or 0)
        if r[2] == "proc" and int(r[3] or 0) == GLUCO_P:
            gl.add(k[:2])
    dz, days = {}, set()
    try:
        for r in con.execute("SELECT business_date, clinic_id, section, amount_p, mode FROM clinic_day_line "
                             "WHERE business_date >= ? AND business_date <= ?", (str(d0), str(d1))):
            days.add(r[0])
            a = int(r[3] or 0)
            if r[2] not in ("xray", "proc") or a <= 0:
                continue
            cid = str(r[1] or "").strip()
            sec = "proc" if (r[2] == "xray" and a == GLUCO_P and (r[0], cid) in gl) else r[2]
            t = dz.setdefault((r[0], cid, sec), [0, []])
            t[0] += a
            m = (r[4] or "").strip()
            m = DZ_MODE.get(m.lower(), m.title())
            if m and m not in t[1]:
                t[1].append(m)
    except sqlite3.Error:
        pass
    out = {}
    for k, tot in slip.items():
        if tot <= 0:
            out[k] = ("free", "", 0)
        elif k[1] and k in dz and dz[k][0] == tot:
            out[k] = ("ok", " + ".join(dz[k][1]), tot)
        elif k[1] and k in dz:
            out[k] = ("differ", "", dz[k][0])
        elif k[0] in days:
            out[k] = ("none", "", 0)
        else:
            out[k] = ("wait", "", 0)
    return out


def paid_words(mark, net_p, lang="en"):
    """The Paid cell for one slip line: Free when the line itself is 0, else Docterz's word (docterz_paid)."""
    if net_p <= 0:
        return "Free"
    code, mode, p = mark or ("wait", "", 0)
    hi = lang == "hi"
    if code == "ok":
        return mode or "Docterz"
    if code == "free":
        return "Free"
    if code == "differ":
        return "Docterz mein alag raqam" if hi else "Docterz Rs %s for the day" % "{:,}".format(int(p) // 100)
    if code == "none":
        return "Docterz mein nahi" if hi else "Not in Docterz"
    return "Docterz abhi nahi aaya" if hi else "Docterz not in yet"


def films_w(n):
    """'1 film', '14 films'."""
    return "%d film" % n if n == 1 else "%d films" % n
''', "x-funcs")
E(X, '''def slip_lines(con, d0, d1, names=False):
    """Every X-ray line of a PAID X-ray slip (series xp, state ok, paid cash or UPI) from day d0 to d1: [{day, slip_id, no, cid,
    name, study, size, films, paid}] (the name only when asked: the X-ray list).''',
  '''def slip_lines(con, d0, d1, names=False, lang="en", paid=True):
    """Every X-ray line of an X-ray slip (series xp, state ok -- S691: billed is done, D775; the room's Paid tick is no longer
    asked for, so it no longer gates the count) from day d0 to d1: [{day, slip_id, no, cid, name, study, size, films, paid}]
    (the name only when asked: the X-ray list; paid is Docterz's word, docterz_paid, read only when paid=True).''', "x-sl-doc")
E(X, '''"i.side, o.name AS oname FROM slip s JOIN slip_item i ON i.slip_id=s.id AND i.kind='xray' LEFT JOIN owner_service o ON o.id=i.service_id "
         "WHERE s.series='xp' AND s.state='ok' AND s.paid_mode IN ('cash','upi') AND s.day>=? AND s.day<=? ORDER BY s.day, s.slip_no, i.sort, i.id")''',
  '''"i.side, o.name AS oname, COALESCE(i.price_p, 0) - COALESCE(i.discount_p, 0) AS net "
         "FROM slip s JOIN slip_item i ON i.slip_id=s.id AND i.kind='xray' LEFT JOIN owner_service o ON o.id=i.service_id "
         "WHERE s.series='xp' AND s.state='ok' AND s.day>=? AND s.day<=? ORDER BY s.day, s.slip_no, i.sort, i.id")
    marks = docterz_paid(con, d0, d1) if paid else {}''', "x-sl-q")
E(X, '''                 side=r["side"] or "", size=size, films=films, paid=r["paid_mode"])''',
  '''                 side=r["side"] or "", size=size, films=films,
                 paid=paid_words(marks.get((r["day"], str(r["clinic_id"] or "").strip(), "xray")), int(r["net"] or 0), lang))''', "x-sl-paid")
E(X, '''    """{size or '': films} on the paid X-ray slips from d0 to d1."""''',
  '''    """{size or '': films} on the X-ray slips from d0 to d1 (every 'ok' slip, S691)."""''', "x-sf-doc")
E(X, '''    for e in slip_lines(con, d0, d1):
        t[e["size"] if e["size"] in SIZE_KEYS else ""] += e["films"]''', '''    for e in slip_lines(con, d0, d1, paid=False):                     # S691: films only -- no Docterz read (review 1)
        t[e["size"] if e["size"] in SIZE_KEYS else ""] += e["films"]''', "x-sf-nopaid")
E(X, "aur paid parchi par jitni film", "aur parchi par jitni film", "x-w1")
E(X, "against films on the paid slips, by size.", "against films on the slips, by size.", "x-w2")
E(X, "us din ki paid X-ray parchi ki film", "us din ki X-ray parchi ki film", "x-w3")
E(X, "films on that day's paid X-ray slips", "films on that day's X-ray slips", "x-w4")
E(X, '''"Har paid X-ray parchi, din ke hisaab se. Purani Excel jaisi hai waisi rahegi."''',
  '''"Har X-ray parchi, din ke hisaab se; Paid Docterz se. Purani Excel jaisi hai waisi rahegi."''', "x-w5")
E(X, '''"Every paid X-ray slip, day by day. It replaces the X-ray Excel; the old Excel stays as it is."''',
  '''"Every X-ray slip, day by day; Paid as Docterz shows it. It replaces the X-ray Excel; the old Excel stays as it is."''', "x-w6")
E(X, '''    lines = slip_lines(con, d0, min(last, today).isoformat(), names=True)''',
  '''    lines = slip_lines(con, d0, min(last, today).isoformat(), names=True, lang=lang)''', "x-list-call")
E(X, '''"<tr class='dh'><td colspan='8'><b>%s</b> · %d X-ray · 8×10: %d film · 11×14: %d film%s</td></tr>" % (
            ddm(day, lang), len(es), tot["8x10"], tot["11x14"],''',
  '''"<tr class='dh'><td colspan='8'><b>%s</b> · %d X-ray · 8×10: %s · 11×14: %s%s</td></tr>" % (
            ddm(day, lang), len(es), films_w(tot["8x10"]), films_w(tot["11x14"]),''', "x-list-chip")
E(X, '''SIZE_LABEL.get(e["size"], "size not set"), e["films"], e["paid"].upper() if e["paid"] == "upi" else e["paid"].title()))''',
  '''SIZE_LABEL.get(e["size"], "size not set"), e["films"], _esc(e["paid"])))''', "x-list-paid")
E(X, '''("Is mahine koi paid X-ray nahi" if hi else "No paid X-ray this month")''',
  '''("Is mahine koi X-ray nahi" if hi else "No X-ray this month")''', "x-w7")
E(X, '''"Shavez ki paid parchi se bhari — koi type nahi karta.''', '''"Shavez ki parchi se bhari — koi type nahi karta.''', "x-w8")
E(X, '''else "Filled from the paid slips Shavez enters — nobody types this list.''',
  '''else "Filled from the slips Shavez enters — nobody types this list.''', "x-w9")
E(X, '''SIZE_LABEL.get(e["size"], "size not set"), e["films"], e["paid"].upper()] for e in lines]''',
  '''SIZE_LABEL.get(e["size"], "size not set"), e["films"], e["paid"]] for e in lines]''', "x-xlsx-paid")
E(X, '''rows, [12, 9, 12, 28, 40, 12, 7, 7])])''', '''rows, [12, 9, 12, 28, 40, 12, 7, 18])])''', "x-xlsx-w")
E(X, '''    lines = slip_lines(con, max(first.isoformat(), lo), min(last, today).isoformat(), names=True)''',
  '''    lines = slip_lines(con, max(first.isoformat(), lo), min(last, today).isoformat(), names=True, lang=lang)   # S691 review 2''', "x-xlsx-lang")
E(X, '''    bills = list(con.execute("SELECT * FROM xf_purchase WHERE gone_at='' ORDER BY bill_day DESC, id DESC LIMIT 12"))''',
  '''    fy = fy_start(today)                                               # S691: this financial year only (the owner, 06:51 IST 01-Nov)
    bills = list(con.execute("SELECT * FROM xf_purchase WHERE gone_at='' AND bill_day >= ? ORDER BY bill_day DESC, id DESC",
                             (fy.isoformat(),)))''', "x-bills-q")
E(X, '''    out.append("<div class='card'><h3>FILM BILLS IN THE SCAN APP</h3><p class='mut'>%s</p><ul class='hist'>%s</ul></div>" % (
        _esc(sync_words if ok_sync else "Not read now: " + sync_words), li or "<li>none yet</li>"))''',
  '''    out.append("<div class='card'><h3>FILM BILLS IN THE SCAN APP</h3><p class='mut'>%d film bill%s since %d %s %d (this financial "
               "year)%s</p><ul class='hist'>%s</ul>%s</div>" % (
                   len(bills), "" if len(bills) == 1 else "s", fy.day, MON[fy.month - 1], fy.year,
                   "" if ok_sync else (" · not re-read now: " + _esc(sync_words)), li or "<li>none yet</li>",
                   ("<p class='mut'><a href='%s'>All film bills — Scan App</a></p>" % SCANAPP_XRAY) if own else ""))''', "x-bills-card")
E(X, '''    ok = con.execute("SELECT 1 FROM owner_service WHERE id=? AND kind='xray'", (sid,)).fetchone()
    if not ok or size not in SIZE_KEYS + ("",) or not (1 <= films <= 4) or b1 not in ("0", "1"):
        return redirect(BASE + "/log?msg=bad")
    who = _who(u)
    rid = con.execute("INSERT INTO xf_study (service_id, size, films, both_one, set_at, set_by) VALUES (?,?,?,?,?,?)",
                      (sid, size, films, int(b1), _stamp(), who)).lastrowid
    con.commit()
    _audit_safe(con, "xf_study", rid, "set", None, dict(service_id=sid, size=size, films=films, both_one=int(b1)), who)
    return _owner_post("study")''',
  '''    if b1 not in ("0", "1"):
        return redirect(BASE + "/log?msg=bad")
    try:
        set_study(con, sid, size, films, int(b1), _who(u))
    except ValueError:
        return redirect(BASE + "/log?msg=bad")
    return _owner_post("study")''', "x-route-study")

X_STUDY_END = '''"<table class='grid'><tbody>%s</tbody></table></details>" % "".join(rows))\n'''
X_STUDY_NEW = '''    if own:                                                            # S691: set on his X-rays & procedures page now
        out.append("<div class='card'><h3>FILM SIZE AND FILMS PER STUDY</h3><p class='mut'>Set on your X-rays &amp; procedures page "
                   "&mdash; tap an X-ray there. <a href='/finance/clinic/sheets?kind=xray'>Open it</a></p></div>")
'''

# ===================================================================================== clinic_lists.py
C = "clinic_lists.py"
E(C, 'VERSION = "S689-CLINIC-LISTS-1.0"', 'VERSION = "S691-CLINIC-LISTS-1.1"', "c-version")
E(C, '''     'ok' -- cancelled, spoilt and void slips never show. Paid shows Cash / UPI; a line whose rate minus discount is 0 shows
     Free; a line on a slip the X-ray room has not marked paid shows "Not marked paid" (built 01-Nov: listed and marked rather
     than hidden, so no procedure done goes missing from his list).''',
  '''     'ok' -- cancelled, spoilt and void slips never show. S691 (the owner, 06:32-06:43 IST 01-Nov; D775): Paid is read from
     Docterz, never from the room's tick (retired 24-Oct): per patient, day and kind, the slip lines' total against that day's
     Docterz charges (xray_film.docterz_paid). Equal -> Docterz's mode (Cash, UPI, Card, "Paid (two ways)" -- never the words
     "split payment", his ruling of 13-Oct); different -> "Docterz Rs X for the day" (amber; that patient's total that day); that day's report in but no charge -> "Not in Docterz" (amber); no report for the day yet -> "Docterz not in
     yet"; a line whose rate minus discount is 0 -> Free. Every line is listed; none is hidden.''', "c-doc6")
E(C, '''PAID_LABEL = {"cash": "Cash", "upi": "UPI", "free": "Free", "unpaid": "Not marked paid"}''',
  '''SHEETS_XRAY = "/finance/clinic/sheets?kind=xray"                    # S691: his rate page, where a study's film size is set''', "c-paidlabel")
E(C, '''def paid_of(paid_mode, net_p):
    if net_p <= 0:
        return "free"
    if paid_mode in ("cash", "upi"):
        return paid_mode
    return "unpaid"
''', '''def _marks(con, d0, d1):
    """Docterz's word per patient, day and kind (xray_film.docterz_paid); None when the film log module cannot be loaded."""
    try:
        import xray_film as XF                                         # noqa: PLC0415 -- the film log beside this app
        return XF.docterz_paid(con, d0, d1)
    except Exception:                                                  # noqa: BLE001
        return None


def _dzmode(m):
    """Docterz's mode in the page's words (xray_film.DZ_MODE): never the words "split payment" (his ruling of 13-Oct)."""
    m = (m or "").strip()
    try:
        import xray_film as XF                                         # noqa: PLC0415
        return XF.DZ_MODE.get(m.lower(), m.title())
    except Exception:                                                  # noqa: BLE001
        return "Paid (two ways)" if m.lower() == "split payment" else m.title()


def paid_of(mark, net_p):
    """(code, mode, docterz_p) for one slip line: 'free' when the line is 0; 'unk' when Docterz could not be read."""
    if net_p <= 0:
        return ("free", "", 0)
    return mark if mark else ("unk", "", 0)


def paid_text(e):
    """The Paid cell's words, and whether they are amber."""
    code, mode, p = e["pd"]
    if code == "ok":
        return mode or "Docterz", False
    if code == "free":
        return "Free", False
    if code == "differ":
        return "Docterz %s for the day" % rs(p), True
    if code == "none":
        return "Not in Docterz", True
    if code == "wait":
        return "Docterz not in yet", False
    return "—", False


def films_w(n):
    return "%d film" % n if n == 1 else "%d films" % n
''', "c-paidof")
E(C, '''    st, _ok = _studies(con) if tab == "xray" else ({}, False)
    nm = _namer(con)''', '''    st, _ok = _studies(con) if tab == "xray" else ({}, False)
    nm = _namer(con)
    mk = _marks(con, d0, d1)''', "c-sr-mk")
E(C, '''                 paid=paid_of(r["paid_mode"] or "", net), mode=r["paid_mode"] or "", dz=False, dmode="")''',
  '''                 dz=False, dmode="")
        e["pd"] = paid_of(None if mk is None else mk.get((r["day"], cid, tab), ("wait", "", 0)), net)
        e["paid"] = e["pd"][0]''', "c-sr-paid")
E(C, '''         "unpaid": sum(1 for e in rows if e["paid"] == "unpaid"), "days": len({e["day"] for e in rows})}''',
  '''         "unpaid": sum(1 for e in rows if e["paid"] in ("differ", "none")), "days": len({e["day"] for e in rows})}''', "c-sum")
E(C, '''        tiles.append("<div><b>%d</b><span>Size not set</span></div>" % s["nosize"])''',
  '''        tiles.append("<div><b>%d</b><span><a href='%s'>Size not set</a></span></div>" % (s["nosize"], SHEETS_XRAY))''', "c-tile")
E(C, '''        extra.append("%d not marked paid" % s["unpaid"])''', '''        extra.append("%d line%s not matching Docterz" % (s["unpaid"], "" if s["unpaid"] == 1 else "s"))''', "c-extra")
E(C, '''chips = "".join("<span class='chip'>%s: %d film</span>" % (lab, sum(e["films"] for e in es if not e["dz"] and e["size"] == z))''',
  '''chips = "".join("<span class='chip'>%s: %s</span>" % (lab, films_w(sum(e["films"] for e in es if not e["dz"] and e["size"] == z)))''', "c-chip")
E(C, '''                paid = PAID_LABEL[e["paid"]] if e["paid"] != "unpaid" else "<span class='amb'>Not marked paid</span>"''',
  '''                pw, amber = paid_text(e)
                paid = ("<span class='amb'>%s</span>" % _esc(pw)) if amber else _esc(pw)''', "c-cell")
E(C, '''                cells += ["—" if e["dz"] else SIZE_LABEL.get(e["size"], "size not set"), ("%d" % e["films"]) if not e["dz"] else "—"]''',
  '''                cells += ["—" if e["dz"] else (SIZE_LABEL.get(e["size"]) or "<a href='%s'>size not set</a>" % SHEETS_XRAY),
                          ("%d" % e["films"]) if not e["dz"] else "—"]''', "c-size")
E(C, '''"Docterz: " + (e["dmode"].title() or "-")) if e["dz"] else PAID_LABEL[e["paid"]], e["amount_p"] / 100.0,''',
  '''"Docterz: " + (e["dmode"] or "-")) if e["dz"] else paid_text(e)[0], e["amount_p"] / 100.0,''', "c-xlsx")
E(C, '''disc_p=0, paid="dz", mode="", dz=True, dmode=(r["mode"] or "").strip(),''',
  '''disc_p=0, paid="dz", mode="", dz=True, dmode=_dzmode(r["mode"]),''', "c-dzmode")
E(C, '''                paid = "<span class='amb'>Docterz: %s</span>" % _esc(e["dmode"].title() or "—")''',
  '''                paid = "<span class='amb'>Docterz: %s</span>" % _esc(e["dmode"] or "—")''', "c-dzcell")

# ===================================================================================== owner_sheets.py
O = "owner_sheets.py"
E(O, '''Flask and the standard library only. No patient name, no number, no secret (F-185).
"""''', '''S691 (01-Nov-2026, kit S691_LISTS_FILM_STUDY, the owner 06:55 IST: "When adding x-rays film size option and number of films
for the study are also missing, it's required also"): every X-ray line carries its FILM -- size (8x10 / 11x14), films per
study, and "both sides on one film" -- shown on the line and changed inside it; a NEW X-ray cannot be added without a film
size. Kept in the film log's own table xf_study through xray_film.set_study (one store; the film log and his lists page read
it). The film log's separate per-study setting is retired to a link here.

Flask and the standard library only. No patient name, no number, no secret (F-185).
"""''', "o-doc")
E(O, '''KIND_OF = dict(KINDS)
''', '''KIND_OF = dict(KINDS)
FILM_SIZES = (("8x10", "8×10"), ("11x14", "11×14"))                 # S691
FILM_LABEL = dict(FILM_SIZES)


def _xf():
    """The film log module (xray_film.py, beside this app); None when it cannot be loaded."""
    try:
        import xray_film as XF                                         # noqa: PLC0415
        return XF
    except Exception:                                                  # noqa: BLE001
        return None
''', "o-consts")
E(O, '''def services(con, kind=None):
    ensure(con)
    where, args = ("WHERE kind=?", (kind,)) if kind else ("", ())
    rows = []''', '''def services(con, kind=None):
    ensure(con)
    where, args = ("WHERE kind=?", (kind,)) if kind else ("", ())
    rows = []
    films = None                                                       # S691: {service_id: (size, films, both_one)}
    if kind in (None, "xray"):
        XF = _xf()
        if XF is not None:
            try:
                XF._ensure(con)
                films = XF.studies(con)
            except Exception:                                          # noqa: BLE001
                films = None''', "o-svc-a")
E(O, '''                     "side": r["side"],                                  # S322
''', '''                     "side": r["side"],                                  # S322
                     "film": (films.get(r["id"], ("", 1, 0)) if films is not None else None) if r["kind"] == "xray" else None,
''', "o-svc-b")
E(O, '''def add_service(con, who, kind, name, price_text, note=""):
    ensure(con)
    kind = (kind or "").strip().lower()
    if kind not in KIND_OF:
        raise ValueError("X-ray or procedure -- nothing else")
    name = " ".join((name or "").split())[:80]
    if not name:
        raise ValueError("a name is needed")
    price_p = _paise(price_text) if (price_text or "").strip() else 0''',
  '''def add_service(con, who, kind, name, price_text, note="", size=None, films=None):
    ensure(con)
    kind = (kind or "").strip().lower()
    if kind not in KIND_OF:
        raise ValueError("X-ray or procedure -- nothing else")
    name = " ".join((name or "").split())[:80]
    if not name:
        raise ValueError("a name is needed")
    price_p = _paise(price_text) if (price_text or "").strip() else 0
    XF = None
    if kind == "xray":                                                 # S691: a new X-ray needs its film size
        size = (size or "").strip()
        if size not in FILM_LABEL:
            raise ValueError("pick the film size, 8x10 or 11x14")
        try:
            films = int(films or 1)
        except ValueError:
            raise ValueError("films per study is a number")
        XF = _xf()
        if XF is None:
            raise ValueError("the film log is not loaded -- the film size cannot be saved now")
        if not (1 <= films <= XF.FILMS_MAX):
            raise ValueError("films per study: 1 to %d" % XF.FILMS_MAX)''', "o-add-a")
E(O, '''                       "X-ray" if kind == "xray" else "", who, _now(), who, _now()))
    con.commit()''', '''                       "X-ray" if kind == "xray" else "", who, _now(), who, _now()))
    con.commit()
    if XF is not None:
        XF.set_study(con, cur.lastrowid, size, films, 0, who)''', "o-add-b")
E(O, '''def set_side(con, who, sid, ask):''', '''def set_film(con, who, sid, size, films, both_one):
    """S691: an X-ray line's film -- size, films per study, both sides on one film -- through xray_film.set_study."""
    XF = _xf()
    if XF is None:
        raise ValueError("the film log is not loaded -- the film size cannot be saved now")
    r = con.execute("SELECT kind, name FROM owner_service WHERE id=?", (sid,)).fetchone()
    if not r or r["kind"] != "xray":
        raise ValueError("film size belongs to an X-ray")
    size = (size or "").strip()
    if size not in FILM_LABEL and size != "":
        raise ValueError("film size 8x10 or 11x14")
    try:
        films, both_one = int(films or 1), int(both_one or 0)
    except ValueError:
        raise ValueError("films per study is a number")
    if (r["name"] or "").strip().lower().startswith("both"):
        both_one = 0                                                   # a 'Both' study never doubles anyway (the film log's rule)
    XF.set_study(con, sid, size, films, both_one, who)


def set_side(con, who, sid, ask):''', "o-setfilm")
E(O, '''    line = ("<summary><span class='nm'>%s</span><span class='pr'>%s</span>%s<span class='chip %s' title='%s'>%s</span></summary>"
            % (_esc(s_["name"]), ("&#8377;" + s_["price"]) if s_["price_p"] else "<span class='tag'>no price</span>",
               "<span class='chip c-side'>R/L</span>" if asks else "", cls, _STATUS_WORD.get(s_["status"], ""), word))''',
  '''    fl = s_.get("film")                                                # S691: (size, films, both_one) or None
    fchip = ""
    if kind == "xray" and fl is not None:
        fchip = ("<span class='chip c-side'>%s &times; %d</span>" % (FILM_LABEL[fl[0]], fl[1]) if fl[0] in FILM_LABEL
                 else "<span class='chip c-wait'>film?</span>")
    line = ("<summary><span class='nm'>%s</span><span class='pr'>%s</span>%s%s<span class='chip %s' title='%s'>%s</span></summary>"
            % (_esc(s_["name"]), ("&#8377;" + s_["price"]) if s_["price_p"] else "<span class='tag'>no price</span>",
               fchip, "<span class='chip c-side'>R/L</span>" if asks else "", cls, _STATUS_WORD.get(s_["status"], ""), word))''', "o-line")
E(O, '''    if kind == "xray":
        ed.append("<span class='tag'>%s%s</span>" % (("%d times in the register" % s_["seen"]) if s_["seen"] else "not in the register",''',
  '''    if kind == "xray" and fl is not None:
        both_name = (s_["name"] or "").strip().lower().startswith("both")
        so = "".join("<option value='%s'%s>%s</option>" % (k, " selected" if fl[0] == k else "", v) for k, v in FILM_SIZES)
        if fl[0] not in FILM_LABEL:
            so = "<option value='' selected>film size not set</option>" + so
        fo = "".join("<option%s>%d</option>" % (" selected" if fl[1] == n else "", n) for n in range(1, 7))
        bo = ("" if both_name else "<select name='both_one' aria-label='both sides'>%s</select>" % "".join(
            "<option value='%s'%s>%s</option>" % (k, " selected" if fl[2] == int(k) else "", v)
            for k, v in (("0", "both sides: twice the films"), ("1", "both sides on one film"))))
        ed.append(_form("film", kind, sid, "<span class='tag'>film</span><select name='size' aria-label='film size'>%s</select>"
                        "<select name='films' aria-label='films per study'>%s</select><span class='tag'>films</span>%s"
                        "<button type='submit'>save</button>" % (so, fo, bo)))
    if kind == "xray":
        ed.append("<span class='tag'>%s%s</span>" % (("%d times in the register" % s_["seen"]) if s_["seen"] else "not in the register",''', "o-edfilm")
E(O, '''                "<input class='p' name='price' placeholder='price (optional)' inputmode='decimal'>"
                "<button type='submit'>Add</button></form>"
                "<p class='mut'>Anything you add is approved already — it is your own line.</p></div></details>"
                % ((" selected" if only == "proc" else ""), (" selected" if only == "xray" else "")))''',
  '''                "<input class='p' name='price' placeholder='price (optional)' inputmode='decimal'>"
                "<span id='addfilm'%s><select name='size' aria-label='film size'><option value=''>film size…</option>%s</select>"
                "<select name='films' aria-label='films per study'>%s</select><span class='tag'>films</span></span>"
                "<button type='submit'>Add</button></form>"
                "<p class='mut'>Anything you add is approved already — it is your own line. An X-ray needs its film size.</p></div></details>"
                "<script>(function(){var k=document.querySelector(\\"form[action='add'] select[name='kind']\\"),f=document.getElementById('addfilm');"
                "if(!k||!f)return;function s(){f.style.display=k.value==='xray'?'':'none';}k.addEventListener('change',s);s();})();</script>"
                % ((" selected" if only == "proc" else ""), (" selected" if only == "xray" else ""),
                   "" if only == "xray" else " style='display:none'",
                   "".join("<option value='%s'>%s</option>" % kv for kv in FILM_SIZES),
                   "".join("<option>%d</option>" % n for n in range(1, 7))))''', "o-addform")
E(O, '''        add_service(con, who, request.form.get("kind"), request.form.get("name"),
                    request.form.get("price"), request.form.get("note", ""))''',
  '''        add_service(con, who, request.form.get("kind"), request.form.get("name"),
                    request.form.get("price"), request.form.get("note", ""),
                    request.form.get("size"), request.form.get("films"))''', "o-route-add")
E(O, '''@bp.route("/active", methods=["POST"])''', '''@bp.route("/film", methods=["POST"])
def route_film():
    """S691: an X-ray line's film size, films per study, both sides on one film."""
    who, err = _owner()
    if err:
        return err
    sid = _sid()
    try:
        set_film(_db(), who, sid, request.form.get("size"), request.form.get("films"), request.form.get("both_one", "0"))
    except ValueError as e:
        return _back(str(e), True, sid)
    return _back("Film saved.", False, sid)


@bp.route("/active", methods=["POST"])''', "o-route-film")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    out = {}
    for f, want in FROM.items():
        b = open(os.path.join(src, f), "rb").read()
        if hashlib.md5(b).hexdigest() != want:
            sys.exit("make_s691: %s is not the FROM file (%s)" % (f, hashlib.md5(b).hexdigest()))
        t = b.decode("utf-8")
        for old, new, tag in EDITS[f]:
            n = t.count(old)
            if n != 1:
                sys.exit("make_s691: edit %s found its anchor %d times" % (tag, n))
            t = t.replace(old, new, 1)
        if f == X:
            blk = between(t, "    st = studies(con)\n    rows = []\n", X_STUDY_END, "x-study-card")
            t = t.replace(blk, X_STUDY_NEW, 1)
        out[f] = t.encode("utf-8")
    os.makedirs(dst, exist_ok=True)
    for f, b in out.items():
        with open(os.path.join(dst, f), "wb") as fh:
            fh.write(b)
        print("%s  %s  (%d edits)" % (hashlib.md5(b).hexdigest(), f, len(EDITS[f]) + (1 if f == X else 0)))


if __name__ == "__main__":
    main()
