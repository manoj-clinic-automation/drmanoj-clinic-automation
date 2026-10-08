#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s500.py -- the builder of kit S500_REPORT_CHECK (08-Oct-2026, D694, F-799, F-788).

    python3 -B make_s500.py --finance /root/finance --out DIR

Reads THREE live files, refuses anything but their FROM pins, makes anchored edits (every anchor must occur
exactly once, every replaced span must hash to its pin -- else NOTHING is written), compiles each result and
refuses anything but its TO pin:

    reports_tile.py   the morning pair judged right / wrong with tries; the guide and picture routes; a short
                      or not-whole closing is WRONG; F-788; the bill-gap card floored for a staff login
    stock_app.py      ONE guard in /api/snapshot: a SHORT closing is refused (409), never loaded; and the stock-voucher proof
                      reads the NEWEST closing after the vouchers, not the first (F-801)
    order_rules.py    ONE guarded call in tick(): the reports watch rides the ten-minute job

The three NEW files of the kit (reports_watch.py, reports_guide.py, reports_guide_pics.py) are not made here:
they are shipped beside this builder and placed as they are.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import os
import sys

PINS = {   # file: (FROM md5, TO md5)
    "reports_tile.py": ("6f7cf490c949495e3e714b7dd688b7af", "1d8843ee6b61c0e8edaaa8cf4a552232"),
    "stock_app.py": ("cc06dac9e3ab60a85d76e2409815b5af", "bfc2a40bff0d8f0050078ea49f990eda"),
    "order_rules.py": ("ee17c1872acd0c440868a915fa5014df", "79f21c1ee1f763b1ac06b370e3d77b79"),
}


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise Stop("anchor '%s' occurs %d times (must be exactly 1)" % (what, n))
    return text.replace(old, new)


def after(text, anchor, add, what):
    return one(text, anchor, anchor + add, what)


def before(text, anchor, add, what):
    return one(text, anchor, add + anchor, what)


def span(text, start, end, new, pin, what):
    """Replace everything from `start` up to (not including) `end`; the replaced bytes must hash to `pin`."""
    if text.count(start) != 1 or text.count(end) != 1:
        raise Stop("span '%s': start occurs %d times, end %d times (each must be exactly 1)" % (what, text.count(start), text.count(end)))
    i, j = text.index(start), text.index(end)
    if not i < j:
        raise Stop("span '%s': its end is not after its start" % what)
    got = md5(text[i:j].encode("utf-8"))
    if got != pin:
        raise Stop("span '%s' is not the bytes this builder was written on (%s, expected %s)" % (what, got, pin))
    return text[:i] + new + text[j:]


# =====================================================================================================================
# reports_tile.py
# =====================================================================================================================
RT_DOC = r'''THE OWNER'S RULING, 08-Oct-2026 (S500_REPORT_CHECK, D694; F-799, F-788).  The two morning reports are made from
Marg's REPORT login (only these two reports open there) by whoever is on morning duty, by the steps of his
counter card.  This page now:
  * carries those steps, with Marg's own screens, behind "Kaise banayein" on each of the two rows
    (/finance/reports/aaj/kaise/sale and /stock -- their own pages, never refreshed; reports_guide.py);
  * says of each of the two RIGHT ("Sahi hai") or WRONG ("Galat hai") and, when wrong, WHICH STEP to do
    again with that step's picture.  Every file for the due day is one of his TRIES; files of one report
    within reports.try_gap_min minutes are one try; a right copy, whenever it comes, wins;
  * F-799: a closing stock is right only when it is the WHOLE STORES totals list AND is not SHORT -- fewer
    items than reports.closing_min_share percent of the median of the last seven closings (reports_watch.closing_short:
    on 07-Oct a list of 250 items, every zero-stock item left out, was ticked "250 items");
  * at reports.tries wrong tries it stops asking and says the owner has been told.  THE MESSAGE IS NOT SENT
    FROM HERE: reports_watch.tick, on the ten-minute job, reads this page's own status() and sends it.  This
    page still writes nothing;
  * F-788: a refused file that is not a one-day report for the due day (a range report; a file the medical
    PC refused before its dates were known) is shown under the row as "ek report manzoor nahi hui" -- not as
    that day's report refused, and it is not a try;
  * the bill-gap card is floored for a staff login (aaj_floor.floor_for -- the parent's rule of 07-Oct:
    nothing dated before the lists' floor on a staff page; the owner's line stays whole).

'''

RT_BLOCK = r'''# ---- S500_REPORT_CHECK (08-Oct-2026, D694, F-799, F-788): the morning pair judged RIGHT or WRONG, with his tries ---------------------
# Every file for the due day is one of his TRIES.  A try is RIGHT (the door verified it AND the spine's certified reader passed it AND,
# for the closing, it is the whole-stores totals list and is not SHORT), WRONG (with the step to redo), or still being checked.  Files
# of one report that arrive within reports.try_gap_min minutes are ONE try (the two exports of 07-Oct, 25 seconds apart, were one act).
# The first wrong try gets the step to redo; at reports.tries wrong tries the page stops asking and says the owner has been told
# (reports_watch.tick sends that message -- this page still writes nothing).  A right copy, whenever it comes, wins.
# F-788: a refused file that is not a ONE-DAY report for the due day (a range report, or one the medical PC refused before its dates
# were known) is shown under the row as "ek report manzoor nahi hui" -- it is not that day's report refused, and it is not a try.
_S500_NOFAM = set()       # md5 of a kept file the certified reader does not take (process lifetime; never a file)


def _s500_watch():
    """reports_watch (the short-closing rule, the settings, the owner's rows), or None -- the page never fails for it."""
    try:
        import reports_watch                                   # noqa: PLC0415
        return reports_watch
    except Exception:                                          # noqa: BLE001
        return None


def _s500_guide():
    """reports_guide (the steps and their pictures), or None."""
    try:
        import reports_guide                                   # noqa: PLC0415
        return reports_guide
    except Exception:                                          # noqa: BLE001
        return None


def _s500_css():
    g = _s500_guide()
    return getattr(g, "CSS", "") if g is not None else ""


def _s500_cfg(cx):
    """(tries before the owner is told, minutes that make one try, is his message on) -- reports_watch's own readers."""
    w = _s500_watch()
    try:
        return w.tries_max(cx), w.try_gap_min(cx), (w.alert_on(cx) and not w.is_off())
    except Exception:                                          # noqa: BLE001
        return 2, 3, False


def _s500_minutes(a, b):
    """Minutes from stamp a to stamp b ('YYYY-MM-DD HH:MM:SS'); a large number when either does not read."""
    try:
        return (datetime.strptime(b[:19], "%Y-%m-%d %H:%M:%S") - datetime.strptime(a[:19], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60.0
    except (ValueError, TypeError):
        return 1e9


def _s500_groups(files, gap_min):
    """His tries: the files in the order they were exported (the capture stamp: a file the door held back BUSY keeps its own
    time), a new try whenever `gap_min` minutes or more passed since the file before.
    A try is right when any of its files is right; else still being checked when any is; else wrong (its newest file says why)."""
    out = []
    for f in sorted(files, key=lambda f: f.get("t") or f.get("when") or ""):
        if out and _s500_minutes(out[-1]["files"][-1].get("t") or "", f.get("t") or "") < gap_min:
            out[-1]["files"].append(f)
        else:
            out.append({"files": [f]})
    for g in out:
        right = [f for f in g["files"] if f["j"] == "right"]
        pend = [f for f in g["files"] if f["j"] == "pending"]
        g["j"] = "right" if right else ("pending" if pend else "wrong")
        g["pick"] = (right or pend or g["files"])[-1]
    return out


def _s500_reading(md5, server_name):
    """-> ('rec', reading) · ('nofam', None): a reading exists and the certified reader does not take the file (for a closing: it is
    not the WHOLE STORES totals list) · ('none', None): no reading yet."""
    if not md5:
        return "none", None
    try:
        with open(os.path.join(SPINE_READINGS, md5 + ".json"), "r", encoding="utf-8") as fh:
            rec = json.load(fh)
        if not isinstance(rec, dict) or not isinstance(rec.get("data") or {}, dict):
            return "none", None
        if not rec.get("family"):
            return "nofam", None
        rec["_source"] = "spine"
        return "rec", rec
    except (OSError, ValueError):
        pass
    if md5 in _READ_CACHE:
        return "rec", _READ_CACHE[md5]
    if md5 in _S500_NOFAM:
        return "nofam", None
    p = _kept_path(server_name)
    if not p:
        return "none", None
    try:
        if SPINE_DIR not in sys.path:
            sys.path.insert(0, SPINE_DIR)
        import marg_read                                        # noqa: PLC0415
        rec = marg_read.reading_record(p, os.path.basename(p))
    except Exception:                                           # noqa: BLE001
        return "none", None
    if not isinstance(rec, dict) or not rec.get("family"):
        _S500_NOFAM.add(md5)
        return "nofam", None
    rec["_source"] = "local"
    _READ_CACHE[md5] = rec
    return "rec", rec


def _s500_one_day(r, day_iso):
    """Is this file a ONE-DAY report for exactly `day_iso`?"""
    df, dto = (r.get("date_from") or "")[:10], (r.get("date_to") or "")[:10]
    return bool(df) and df == dto == day_iso


def _s500_refusal(r):
    reason = r.get("reason") or ""
    if not reason and (r.get("pc_verdict") or "").upper() not in ("", "VERIFIED"):
        reason = "the medical PC refused it (%s)" % r.get("pc_verdict")
    return reason


def _s500_loose(r, what):
    """F-788: a refused file shown under no day."""
    reason = _s500_refusal(r)
    df, dto = (r.get("date_from") or "")[:10], (r.get("date_to") or "")[:10]
    rng = ("%s se %s" % (_ddmm(df), _ddmm(dto))) if (df and dto and df != dto) else (_ddmm(df) if df else "")
    return {"at": _hhmm(r.get("received_at")), "lead": "Aaj %s baje ek %s manzoor nahi hui" % (_hhmm(r.get("received_at")), what),
            "range": rng, "reason": reason, "reason_hi": hindi_reason(reason, r.get("verdict") or ""), "today": True}


def _s500_file(r):
    """`when` = received by the server (what the page shows); `t` = the export's own capture stamp, else `when` (what makes a try)."""
    when = _norm_ts(r.get("received_at"))
    t = _norm_ts(r.get("stamp"))
    try:                                                        # only a whole stamp (date and time to the second) is used
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        t = when
    return {"when": when, "t": t, "at": _hhmm(r.get("received_at")), "md5": r.get("md5") or ""}


def _s500_sale_file(r):
    """One file for the due day's sale report -> its judgement."""
    f = _s500_file(r)
    if r.get("verdict") != "VERIFIED":
        reason = _s500_refusal(r)
        low = reason.lower()
        fix = "sale3" if ("no item detail" in low or "item deta" in low) else ("sale2" if ("date" in low or "period" in low) else "")
        f.update(j="wrong", door=True, verdict=r.get("verdict") or "", reason=reason, why_hi=hindi_reason(reason, r.get("verdict") or ""),
                 why_en="the server refused it (%s)" % (reason[:120] or "no reason given"), fix=fix)
        return f
    if (r.get("variant") or "DETAIL") == "SUMMARY1":            # S480: the short statement lands, and never ticks
        f.update(j="wrong", door=True, verdict="REFUSED", fix="sale3",
                 reason="no item detail -- the short Bill Wise statement (BILL VALUE), not Report Type DETAIL",
                 why_hi="Dawaiyon ki lines nahi hain -- sirf bill aur rakam aayi hai.",
                 why_en="no medicine lines (Report Type Detail and With Item Detail Yes were not chosen)")
        return f
    try:
        c = certify(r.get("md5"), r.get("server_name"), r.get("type")) if r.get("md5") else None
    except Exception:                                           # noqa: BLE001 -- a reading of an odd shape is no reading, never a 500
        c = None
    if c is None:
        f.update(j="pending")
    elif c["ok"]:
        f.update(j="right", cert=c["source"], count=c["count"])
    else:
        f.update(j="wrong", cert=c["source"], count=c["count"], failed=c["failed"], reason=", ".join(c["failed"])[:300],
                 why_hi=hindi_failed(c["failed"]), why_en="it failed its check (%s)" % ", ".join(c["failed"])[:120], fix="")
    return f


def _s500_stock_file(cx, r):
    """One file for the due day's closing stock -> its judgement (F-799: whole stores, totals, and not short)."""
    f = _s500_file(r)
    if r.get("verdict") != "VERIFIED":
        reason = _s500_refusal(r)
        f.update(j="wrong", door=True, verdict=r.get("verdict") or "", reason=reason, why_hi=hindi_reason(reason, r.get("verdict") or ""),
                 why_en="the server refused it (%s)" % (reason[:120] or "no reason given"), fix="stock25")
        return f
    v = (r.get("variant") or "").upper()
    if v == "DEFAULT":
        f.update(j="wrong", fix="stock4", reason="the door filed it as the batch-wise layout, not the totals list",
                 why_hi="Yeh total wali report nahi hai.", why_en="not the totals list (ONLY TOTAL STOCK was not chosen)")
        return f
    if v == "SUBSET":
        f.update(j="wrong", fix="stock25", reason="the door filed it as a part of the item list (SUBSET)",
                 why_hi="Report adhoori hai -- poore store ke item nahi hain.", why_en="a part of the item list only")
        return f
    kind, rec = _s500_reading(r.get("md5"), r.get("server_name"))
    if kind == "none":
        f.update(j="pending")
        return f
    if kind == "nofam":
        f.update(j="wrong", fix="stock25", reason="the certified reader does not take it: not WHOLE STORES CLOSING STOCK with the Total Stock column",
                 why_hi="Yeh poore store (WHOLE) ki total report nahi hai.", why_en="not the whole-stores totals list")
        return f
    failed = [str(x) for x in (rec.get("failed") or [])] if isinstance(rec.get("failed"), list) else []
    items = (rec.get("data") or {}).get("items") or []
    items = items if isinstance(items, list) else []
    n = len(items)
    f.update(cert=rec.get("_source", ""), count="%d items" % n)
    if not rec.get("ok"):
        f.update(j="wrong", failed=failed, reason=", ".join(failed)[:300], why_hi=hindi_failed(failed),
                 why_en="it failed its check (%s)" % ", ".join(failed)[:120], fix="stock25")
        return f
    zero = sum(1 for it in items if isinstance(it, dict) and not it.get("units"))
    short = None
    w = _s500_watch()
    if w is not None:
        try:
            short = w.closing_short(cx, (r.get("date_from") or "")[:10], n)
        except Exception:                                       # noqa: BLE001 -- no judgement, never a wrong one
            short = None
    if short:
        f.update(j="wrong", fix="stock25",
                 reason="short: %d items; recent closings list %d (the median of the last seven)" % (n, short["ref"]),
                 why_hi=("Report adhoori hai. Khali stock wale item nahi aaye." if zero == 0 else "Report adhoori hai. Item kam hain."),
                 small_hi="%d item aaye. Pichhli poori report mein %d the." % (n, short["ref"]),
                 why_en="%s (%d items came; recent closings list %d)"
                        % ("zero-stock items are missing" if zero == 0 else "items are missing", n, short["ref"]))
        return f
    f.update(j="right", zero=zero)
    return f


def _s500_pick(cx, files, proofs, loose, today_iso, what="report"):
    """The state of one of the two rows from his tries.  `files` are judged files (an md5, or a dated refusal); `proofs` prove arrival
    only (the snapshot feed, the older pushed-report door) and matter only when no file is held; `loose` are F-788's lines.
    THE TRIES ARE THIS MORNING'S: a WRONG file exported before today (the due day's afternoon, the night before) is not a try -- it is
    said under the row while nothing right has come.  A right or still-checked file of the night before counts as it always has."""
    tries_max, gap, alert = _s500_cfg(cx)
    loose = list(loose)
    if today_iso:                                               # "before today" by the server's own clock (when it was received)
        old = [f for f in files if f["j"] == "wrong" and (f.get("when") or "")[:10] < today_iso]
        files = [f for f in files if f not in old]
        for f in sorted(old, key=lambda f: f.get("when") or "")[-1:]:     # the newest of them is said
            loose.append({"at": f.get("at", ""), "lead": "%s %s baje wali %s sahi nahi thi" % (_ddmm((f.get("when") or "")[:10])[:5],
                                                                                              f.get("at", ""), what),
                          "range": "", "reason": f.get("reason", ""), "reason_hi": f.get("why_hi", ""), "today": False})
    groups = _s500_groups(files, gap)
    right = [g for g in groups if g["j"] == "right"]
    pend = [g for g in groups if g["j"] == "pending"]
    wrong = [g for g in groups if g["j"] == "wrong"]
    info = {"tries": len(groups), "wrong": len(wrong), "max": tries_max, "alert": bool(alert), "told": False,
            "why_hi": "", "small_hi": "", "why_en": "", "fix": ""}

    def base(f):
        when = f.get("when") or ""
        return {"at": f.get("at") or _hhmm(when), "when": when, "night_before": bool(today_iso) and bool(when) and when[:10] < today_iso}
    if right:
        f = right[-1]["pick"]
        st = dict(base(f), state="ok", cert=f.get("cert", ""), count=f.get("count", ""), zero=f.get("zero"))
    elif pend:
        st = dict(base(pend[-1]["pick"]), state="arrived", cert="pending", count="")
    elif wrong:
        f = wrong[-1]["pick"]
        st = dict(base(f), state=("refused" if f.get("door") else "bad"), cert=f.get("cert", ""), count=f.get("count", ""),
                  failed=f.get("failed") or [], verdict=f.get("verdict", ""), reason=f.get("reason", ""), reason_hi=f.get("why_hi", ""))
        info.update(why_hi=f.get("why_hi", ""), small_hi=f.get("small_hi", ""), why_en=f.get("why_en", ""), fix=f.get("fix", ""))
    elif proofs:
        st = dict(base(max(proofs, key=lambda p: p.get("when") or "")), state="arrived", cert="pending", count="")
    else:
        st = {"state": "due"}
    st["s500"] = info
    st["loose"] = loose[:3]
    st["loose_today"] = sum(1 for l in loose if l.get("today"))
    return st


def _s500_told(cx, day_iso):
    w = _s500_watch()
    try:
        return w.told(cx, day_iso) if w is not None else {}
    except Exception:                                           # noqa: BLE001
        return {}


def _s500_floor(cx, u):
    """The parent's rule (S495, D687): the day before which a STAFF login is shown nothing; None for the owner, a doctor, or while the
    lists are not started.  Never fails the page."""
    try:
        import aaj_floor                                        # noqa: PLC0415
        return aaj_floor.floor_for(cx, _require, u)
    except Exception:                                           # noqa: BLE001
        return None


def _s500_row_html(r):
    """One of the two morning rows: baaki · aa gayi, jaanch ho rahi hai · Sahi hai · Galat hai with the step to redo."""
    w = r.get("s500") or {}
    kind = "sale" if r["key"] == "SALE_BILLWISE" else "stock"
    at = _esc(r.get("at", ""))
    when = ("kal raat %s baje" % at) if r.get("night_before") else ("%s baje" % at)
    link = "<a class=kb href='/finance/reports/aaj/kaise/%s'>%%s &#9656;</a>" % kind
    st = r["state"]
    if st == "ok":
        extra = (r.get("count") or "").replace(" items", " item").replace(" bills", " bill")
        if kind == "stock" and r.get("zero"):
            extra += ", khali stock wale bhi"
        state = ("<span class='state good'>&#10003; Sahi hai <span class=small>%s%s</span></span>"
                 % (when, (" &middot; " + _esc(extra)) if extra else ""))
    elif st == "arrived":
        state = ("<span class='state wait'>&#8987; aa gayi <span class=small>%s</span> &middot; jaanch ho rahi hai&hellip;"
                 "<br><span class=small>Server file ko padh kar jaanch raha hai. Aap doosri report shuru kar sakte hain.</span></span>" % when)
    elif st in ("bad", "refused") and w.get("wrong"):
        n, mx = int(w["wrong"]), int(w.get("max") or 2)
        g = _s500_guide()
        why = "<b>%s</b>" % _esc(w.get("why_hi") or r.get("reason_hi") or "Jaanch me galti mili.")
        if w.get("small_hi"):
            why += "<br><span class=small>%s</span>" % _esc(w["small_hi"])
        if n < mx:
            left = mx - n
            redo = g.redo(w.get("fix") or "", r.get("due_ddmm") or "") if g is not None else ""
            eng = ("<br><span class=small>%s</span>" % _esc(r.get("reason"))) if r.get("reason") else ""
            state = ("<span class='state bad'>&#10007; Galat hai <span class=small>%s &middot; koshish %d / %d</span></span>"
                     "<span class=why>%s%s%s<br>%s<span class=try>%s</span></span>"
                     % (when, n, mx, why, redo, eng, link % "Poore steps dekhiye",
                        "Ek koshish aur hai" if left == 1 else "%d koshish aur hain" % left))
        else:
            head = "Galat hai" if n == 1 else ("Doosri baar bhi galat" if n == 2 else "%d baar galat" % n)
            tell = ("Doctor sahab ko khabar chali gayi hai." if w.get("told")
                    else ("Doctor sahab ko khabar ja rahi hai." if w.get("alert") else "Doctor sahab ko bataiye."))
            state = ("<span class='state bad'>&#10007; %s <span class=small>%s &middot; koshish %d / %d</span></span>"
                     "<span class=stop><b>%s</b><br>Ab unse baat kijiye.<br><span class=small>%s</span></span>%s"
                     % (head, when, n, mx, tell, _esc(" ".join(x for x in (w.get("why_hi"), w.get("small_hi")) if x)),
                        link % "Poore steps dekhiye"))
    else:
        state = "<span class='state due'>&#9675; baaki</span>" + (link % "Kaise banayein")
    if st != "ok":
        for l in r.get("loose") or []:                          # F-788: a refused file that is not this day's report; an earlier wrong file
            state += ("<span class=why>%s%s.<br>%s<br><span class=small>%s</span></span>"
                      % (_esc(l.get("lead", "")), (" (%s)" % _esc(l["range"])) if l.get("range") else "",
                         _esc(l.get("reason_hi", "")), _esc(l.get("reason", ""))))
    return ("<div class=line><span class=big>%s</span> <span class=small>%s</span>%s</div>"
            % (_esc(r.get("label_hi") or r["label"]), _esc(r.get("hint", "")), state))
# ---- S500 end ------------------------------------------------------------------------------------------------------------------------


def _sale_row(cx, y_iso, today_iso):
    # S480 (A.2) stands: the day's sale report is SALE_BILLWISE with variant DETAIL only; the short statement (SUMMARY1 -- BILL VALUE,
    # no item lines) lands and is archived, and is a WRONG try with the tile's own "Item detail" words.
    # S500 (D694, F-788): every file for the due day is a try (_s500_pick); a refused file that is not a one-day report for the due day
    # is shown under no day (loose).
    files, proofs, loose = [], [], []
    for r in _mi_rows(cx, ("SALE_BILLWISE",), day_from=y_iso, day_to=y_iso):
        if r["verdict"] == "VERIFIED":
            if (r.get("variant") or "DETAIL") in ("DETAIL", "SUMMARY1"):
                f = _s500_sale_file(r)
                if f["j"] != "wrong" or _s500_one_day(r, y_iso):  # a range report covering the day can tick it; a wrong one is not his try
                    files.append(f)
        elif _s500_one_day(r, y_iso):
            files.append(_s500_sale_file(r))
    for r in _mi_rows(cx, ("SALE_BILLWISE",), received_day=today_iso):
        if r["verdict"] != "VERIFIED" and not _s500_one_day(r, y_iso):
            loose.append(_s500_loose(r, "bikri report"))
    if _table_exists(cx, "marg_push_staging"):
        # the pushed-report door (the older route the medical PC still uses): it proves arrival only -- no md5, never a tick
        for r in cx.execute("SELECT received_at FROM marg_push_staging WHERE status<>'rejected' "
                            "AND survey_json LIKE ? ORDER BY received_at DESC LIMIT 1",
                            ('%"' + y_iso + '"%',)).fetchall():
            proofs.append({"when": _norm_ts(r["received_at"])})
        if not files and not loose:
            for r in cx.execute("SELECT received_at, survey_json, filename_hint FROM marg_push_staging "
                                "WHERE status='rejected' AND substr(received_at,1,10)=? "
                                "ORDER BY received_at DESC LIMIT 1", (today_iso,)).fetchall():
                why = ""
                try:
                    why = (json.loads(r["survey_json"] or "{}") or {}).get("error") or ""
                except Exception:                              # noqa: BLE001
                    why = ""
                loose.append({"at": _hhmm(r["received_at"]), "lead": "Aaj %s baje ek bikri report manzoor nahi hui" % _hhmm(r["received_at"]),
                              "range": "", "reason": why, "reason_hi": hindi_reason(why, "REFUSED"), "today": True})
    st = _s500_pick(cx, files, proofs, loose, today_iso, "bikri report")
    st.update(key="SALE_BILLWISE", label="Bill-wise sale report", label_hi="1 · Bikri report", pair=True, due_ddmm=_ddmm(y_iso),
              hint="DAILY SALES · %s" % _ddmm(y_iso))
    return st


def _stock_row(cx, y_iso, today_iso):
    # Marg's "as on" is date_from.  Yesterday's close = as on the due day, or any later day up to this
    # morning (a closing taken before the counter opens); export_watch's rule.
    # S500 (D694, F-799): each such file is a try, RIGHT only when it is the whole-stores totals list and not short.
    files, proofs, loose = [], [], []
    for r in _mi_rows(cx, ("STOCK_CLOSING",)):
        d = (r.get("date_from") or "")[:10]
        got = (r.get("received_at") or "")[:10]
        if r["verdict"] == "VERIFIED":
            if y_iso <= d <= today_iso and got >= y_iso:
                files.append(_s500_stock_file(cx, r))
        elif got == today_iso:
            if d and y_iso <= d <= today_iso:
                files.append(_s500_stock_file(cx, r))
            else:
                loose.append(_s500_loose(r, "closing stock report"))
    if _table_exists(cx, "stock_feed"):
        for as_on in (date.fromisoformat(y_iso).strftime("%d-%m-%Y"), date.fromisoformat(today_iso).strftime("%d-%m-%Y")):
            r = cx.execute("SELECT MIN(received_at) AS at, COUNT(*) AS n FROM stock_feed WHERE as_on=? "
                           "AND source LIKE 'push_snapshot%'", (as_on,)).fetchone()
            if r and r["n"] and (r["at"] or "")[:10] >= y_iso:
                proofs.append({"when": _norm_ts(r["at"])})
    st = _s500_pick(cx, files, proofs, loose, today_iso, "closing stock report")
    st.update(key="STOCK_CLOSING", label="Closing stock report", label_hi="2 · Closing stock", pair=True, due_ddmm=_ddmm(y_iso),
              hint="Stock Status · %s" % _ddmm(y_iso))
    return st


'''

RT_TOLD = r'''    _told = _s500_told(cx, today_iso)                           # S500: has the owner been told about a report (reports_watch's row)
    for _r in rows:
        if _r.get("pair") and isinstance(_r.get("s500"), dict):
            _r["s500"]["told"] = bool(_told.get(_r["key"]))
'''

RT_LINE = r'''    for _r in rows:                                             # S500: a report of the pair found wrong, in words, on the owner's card
        _w = _r.get("s500") or {}
        if _r.get("pair") and _r["state"] in ("bad", "refused") and _w.get("wrong"):
            line += " · %s wrong %s: %s" % ("sale report" if _r["key"] == "SALE_BILLWISE" else "closing stock",
                                            "once" if _w["wrong"] == 1 else "%d times" % _w["wrong"], _w.get("why_en") or "see the page")
    _lz = sum(int(_r.get("loose_today") or 0) for _r in rows if _r.get("pair"))
    if _lz:                                                     # F-788: still counted for the owner, though under no day
        line += ", %d refused (not the day's report)" % _lz
'''

RT_HOW = r'''def _how_block(s):
    """What to do, in two lines, for the due day -- the REPORT login's own steps (S500, D694).  The whole walk-through, with Marg's
    screens, is behind "Kaise banayein" on each row.  Shown while the pair is not in; after that the rows say everything."""
    due = _ddmm(s["due_day"])
    return ("<div class=how>"
            "Marg mein <b>REPORT</b> wali ID se login kijiye &mdash; My Menu mein yahi do reports hain.<br>"
            "<b>1.</b> <b>DAILY SALES</b> &middot; tareekh <b>%s</b> &middot; Report Type <b>Detail</b> &middot; With Item Deta. <b>Yes</b> "
            "&rarr; View &rarr; Save.<br>"
            "<b>2.</b> <b>Stock Status</b> &middot; <b>WHOLE</b> &middot; Alt + P &rarr; A Stock Statement &middot; <b>ONLY TOTAL STOCK</b> "
            "&rarr; View &rarr; Save.<br>"
            "<span class=small>Tasveer ke saath poore steps: neeche har report ke &quot;Kaise banayein&quot; mein. "
            "File yahan khud aa jaati hai -- kuch bhejna nahi hai.</span>"
            "</div>" % due)


'''

RT_ROUTES = r'''@bp.route("/finance/reports/aaj/kaise/<kind>")
def s500_guide_page(kind):
    """S500 (D694): the steps of one report, with Marg's own screens.  Its own page, so the status page's refresh never moves it."""
    u, err = _gate()
    if err:
        return _denied()
    g = _s500_guide()
    if g is None or kind not in ("sale", "stock"):
        return redirect("/finance/reports/aaj", code=302)
    return _shell("Kaise banayein", g.page(kind, _ddmm(_due_day(_today()))), refresh=0)


@bp.route("/finance/reports/aaj/pic/<name>")
def s500_guide_pic(name):
    """S500: one picture of the guide (a JPEG kept as text in reports_guide_pics.py).  Behind the same gate as the page."""
    u, err = _gate()
    if err:
        return _denied()
    g = _s500_guide()
    data = g.pic(name[:-4]) if (g is not None and name.endswith(".jpg")) else None
    if not data:
        return "no such picture", 404
    return Response(data, mimetype="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})


'''

RT_SELFTEST = r'''    # ---- S500 (D694, F-799, F-788): tries, the short closing, the not-whole closing, the refused file under no day
    c5 = sqlite3.connect(":memory:")
    c5.row_factory = sqlite3.Row
    c5.executescript("""
      CREATE TABLE mi_file (md5 TEXT PRIMARY KEY, drive_id TEXT DEFAULT '', drive_name TEXT DEFAULT '', drive_folder TEXT DEFAULT '',
        drive_mtime TEXT DEFAULT '', size INTEGER DEFAULT 0, stamp TEXT DEFAULT '', type TEXT DEFAULT '', variant TEXT DEFAULT '',
        date_from TEXT DEFAULT '', date_to TEXT DEFAULT '', verdict TEXT DEFAULT '', reason TEXT DEFAULT '', server_name TEXT DEFAULT '',
        kept INTEGER DEFAULT 0, lines INTEGER DEFAULT 0, pc_type TEXT DEFAULT '', pc_verdict TEXT DEFAULT '', agree TEXT DEFAULT '',
        received_at TEXT NOT NULL, source TEXT DEFAULT '');
      CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, PRIMARY KEY (as_on, item));
    """)
    c5.executemany("INSERT INTO stock_snapshot VALUES ('13-09-2026',?,0)", [("W%d" % i,) for i in range(379)])

    def mi5(md5, typ, hm, verdict="VERIFIED", variant="", df=y, dto=y, reason="", pc=""):
        c5.execute("INSERT INTO mi_file (md5,type,variant,date_from,date_to,verdict,reason,pc_verdict,server_name,received_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (md5, typ, variant, df, dto, verdict, reason, pc, md5 + ".xls", "2026-09-15T%s+05:30" % hm))
    full = [{"units": 0.0}] * 130 + [{"units": 4.0}] * 250
    mi5("k1", "STOCK_CLOSING", "09:39:05", variant="TOTALS")
    reading("k1", "STOCK_CLOSING", True, items=full[130:])
    mi5("k2", "STOCK_CLOSING", "09:39:30", variant="TOTALS")
    reading("k2", "STOCK_CLOSING", True, items=full[130:])
    s5 = status(c5, today, at(9, 45))
    r5 = s5["rows"][1]
    ck("S500: a closing of 250 items against 379 is WRONG (short), in the words for a list with no zero-stock item",
       r5["state"] == "bad" and "Khali stock" in r5["s500"]["why_hi"] and r5["s500"]["fix"] == "stock25" and "379" in r5["s500"]["small_hi"])
    ck("S500: two exports 25 seconds apart are ONE try", r5["s500"]["tries"] == 1 and r5["s500"]["wrong"] == 1)
    c5.execute("UPDATE mi_file SET stamp='20260915-093902' WHERE md5='k1'")
    c5.execute("UPDATE mi_file SET stamp='20260915-093927', received_at='2026-09-15T09:42:40+05:30' WHERE md5='k2'")
    ck("S500: the export's own stamp decides -- a file the door held back three minutes is still the same try",
       status(c5, today, at(9, 45))["rows"][1]["s500"]["tries"] == 1)
    h5 = render(s5)
    ck("S500: the first wrong try shows the steps to redo and that one try is left",
       "Galat hai" in h5 and "koshish 1 / 2" in h5 and "step 2 se 5" in h5 and "Ek koshish aur hai" in h5 and "/finance/reports/aaj/kaise/stock" in h5)
    mi5("k3", "STOCK_CLOSING", "09:50:00", variant="TOTALS")
    reading("k3", "STOCK_CLOSING", True, items=full[130:])
    s5 = status(c5, today, at(9, 55))
    h5 = render(s5)
    ck("S500: a second short one ten minutes later is the second try; the page stops asking; the owner's line says it in words",
       s5["rows"][1]["s500"]["wrong"] == 2 and "Doosri baar bhi galat" in h5 and "Doctor sahab" in h5 and "Ek koshish aur hai" not in h5
       and "closing stock wrong 2 times: zero-stock items are missing (250 items came" in s5["line"])
    mi5("k4", "STOCK_CLOSING", "09:58:00", variant="TOTALS")
    reading("k4", "STOCK_CLOSING", True, items=full)
    s5 = status(c5, today, at(10, 5))
    ck("S500: a full copy, whenever it comes, wins -- Sahi hai, with its count",
       s5["rows"][1]["state"] == "ok" and s5["rows"][1]["count"] == "380 items" and s5["rows"][1]["zero"] == 130
       and "Sahi hai" in render(s5) and "khali stock wale bhi" in render(s5))
    c5.execute("DELETE FROM mi_file")
    c5.execute("INSERT INTO mi_file (md5,type,variant,date_from,date_to,verdict,server_name,received_at) VALUES "
               "('e1','STOCK_CLOSING','DEFAULT',?,?,'VERIFIED','e1.xls','2026-09-14T15:02:00+05:30')", (y, y))
    r5 = status(c5, today, at(7, 0))["rows"][1]
    ck("S500: a wrong file of the afternoon before is not this morning's try -- said under the row, the row is due",
       r5["state"] == "due" and r5["s500"]["tries"] == 0 and any("sahi nahi thi" in l["lead"] for l in r5["loose"]))
    c5.execute("DELETE FROM mi_file")
    mi5("n1", "STOCK_CLOSING", "08:00:00", variant="DEFAULT")
    r5 = status(c5, today, at(8, 5))["rows"][1]
    ck("S500: a closing that is not the totals list is WRONG, step 4", r5["state"] == "bad" and r5["s500"]["fix"] == "stock4")
    mi5("n2", "STOCK_CLOSING", "08:10:00", variant="TOTALS")
    reading("n2", None, None)
    r5 = status(c5, today, at(8, 15))["rows"][1]
    ck("S500: a totals list the certified reader does not take is not the WHOLE store -- WRONG, and the second try",
       r5["state"] == "bad" and "WHOLE" in r5["s500"]["why_hi"] and r5["s500"]["wrong"] == 2)
    mi5("m1", "SALE_BILLWISE", "09:00:00", variant="SUMMARY1")
    s5 = status(c5, today, at(9, 2))
    ck("S500: the short sale statement is a WRONG try with step 3, and still 'refused' for the banner (S480 stands)",
       s5["rows"][0]["state"] == "refused" and s5["rows"][0]["s500"]["fix"] == "sale3" and "Step 3 dobara" in render(s5))
    mi5("m2", "SALE_BILLWISE", "09:05:00", verdict="REFUSED", df="", dto="", pc="REFUSED", reason="the medical PC refused it: cut short")
    mi5("m3", "SALE_BILLWISE", "09:06:00", verdict="REFUSED", df="2026-08-15", dto=y, reason="deep parse failed: truncated")
    s5 = status(c5, today, at(9, 8))
    ck("F-788: a refused file that is not a one-day report for the due day is not a try and is shown under no day",
       s5["rows"][0]["s500"]["tries"] == 1 and len(s5["rows"][0]["loose"]) == 2 and "manzoor nahi hui" in render(s5)
       and any(l["range"] == "15-08-2026 se 14-09-2026" for l in s5["rows"][0]["loose"])
       and "2 refused (not the day's report)" in s5["line"] and s5["rows"][0]["label"] == "Bill-wise sale report")
    s5["bill_chain"] = {"lines": [{"between": ["2026-09-29", "2026-09-30"], "text_hi": "GAP-SEP"}, {"between": ["2026-09-30", "2026-10-01"], "text_hi": "GAP-OCT"}]}
    ck("the bill-gap card is whole with no floor", "GAP-SEP" in render(s5) and "GAP-OCT" in render(s5))
    s5["chain_floor"] = "2026-10-01"
    ck("S500: with a floor the card shows a staff login nothing dated before it", "GAP-SEP" not in render(s5) and "GAP-OCT" in render(s5))
    g5 = _s500_guide()
    ck("S500: the guide is there -- six steps for each report, the due date in the sale steps, every picture readable",
       g5 is not None and g5.page("sale", "14-09-2026").count("<li>") >= 6 and "14-09-2026" in g5.page("sale", "14-09-2026")
       and g5.page("stock", "14-09-2026").count("<li>") >= 6 and all((g5.pic(n) or b"")[:2] == b"\xff\xd8" for n in g5.PICS))
'''


def build_reports_tile(t):
    t = before(t, "PRINCIPLES (the same as Amir's page, D469): he is never asked whether a report arrived;", RT_DOC, "docstring: PRINCIPLES")
    t = one(t, "from flask import Blueprint, jsonify, redirect, request\n",
            "from flask import Blueprint, Response, jsonify, redirect, request\n", "the flask import")
    t = span(t, "def _sale_row(cx, y_iso, today_iso):\n", "def _month_rows(cx, today):\n", RT_BLOCK,
             "8211c7f172ba6cc8c747f32c4b0fe898", "_sale_row + _stock_row")
    t = before(t, "    # files the server could not place at all today (no type): said once, at the end\n", RT_TOLD, "status: unknown files comment")
    t = after(t, '    if refused:\n        line += ", %d refused" % refused\n', RT_LINE, "status: the refused clause of the owner's line")
    t = one(t, '</div></body></html>" % (meta, _esc(title), _CSS, body))',
            '</div></body></html>" % (meta, _esc(title), _CSS + _s500_css(), body))', "_shell: the style sheet")
    t = after(t, "def _row_html(r):\n",
              "    if r.get(\"pair\") and isinstance(r.get(\"s500\"), dict):          # S500: the two morning rows have their own wording\n"
              "        return _s500_row_html(r)\n", "_row_html: first line")
    t = span(t, "def _how_block(s):\n", "def render(s, picked_date=False):\n", RT_HOW, "85842189c91ddb08c9486debccd5cf31", "_how_block")
    t = after(t, '    cl = (s.get("bill_chain") or {}).get("lines") or []\n',
              "    _fl = s.get(\"chain_floor\")                                   # S500 (the parent's ask, S495): a staff login sees no gap dated before the floor\n"
              "    if _fl:\n"
              "        cl = [g for g in cl if str((g.get(\"between\") or [\"\", \"\"])[-1]) >= str(_fl)]\n", "render: the chain lines")
    t = one(t, '    s["you"] = str((u or {}).get("user") or "")                # S444 (D647): who is signed in, one quiet line\n    return render(s)\n',
            '    s["you"] = str((u or {}).get("user") or "")                # S444 (D647): who is signed in, one quiet line\n'
            '    s["chain_floor"] = _s500_floor(cx, u)                      # S500: the bill-gap card, floored for a staff login\n    return render(s)\n',
            "page_today")
    t = one(t, '    s["you"] = str((u or {}).get("user") or "")                # S444\n    return render(s, picked_date=(d != _today()))\n',
            '    s["you"] = str((u or {}).get("user") or "")                # S444\n'
            '    s["chain_floor"] = _s500_floor(cx, u)                      # S500\n    return render(s, picked_date=(d != _today()))\n',
            "page_day")
    t = before(t, '@bp.route("/finance/reports/aaj/api/healthz")\n', RT_ROUTES, "routes: healthz")
    t = one(t, '"banner missed" in h2 and "BILL WISE STATEMENT" in h2 and "21-09-2026" in h2)',
            '"banner missed" in h2 and "DAILY SALES" in h2 and "21-09-2026" in h2)', "selftest: the how-to block")
    t = before(t, '    print("reports_tile selftest: %d checks, %d failures" % (n_checks[0], len(fails)))\n', RT_SELFTEST, "selftest: its last line")
    return t


# =====================================================================================================================
# stock_app.py -- ONE guard in /api/snapshot
# =====================================================================================================================
SA_GUARD = r'''    if _kind != "expected":                                   # S500 (F-799): a SHORT closing is never loaded as the day's closing
        _s500 = None
        try:
            import reports_watch                              # noqa: PLC0415
            _s500 = reports_watch.closing_short(con, as_on, len({(it.get("item") or "").strip() for it in items
                                                                  if isinstance(it, dict) and (it.get("item") or "").strip()}))
        except Exception as _ex_s500:                         # noqa: BLE001 -- the guard never breaks a push
            print("reports_watch.closing_short skipped: %s" % _ex_s500, file=sys.stderr)
        if _s500:
            return jsonify(ok=False, error="short_closing", as_on=as_on, items=_s500["items"], reference=_s500["ref"],
                           reference_day=_s500["ref_day"],
                           message="This closing lists %d items; recent closings list %d (the median of the last seven before it). "
                                   "A short list is not loaded (setting reports.closing_min_share = %d percent). Export the WHOLE stock again."
                                   % (_s500["items"], _s500["ref"], _s500["share"])), 409
'''


SA_PROOF_OLD = "        R, L = before[-1], after[0]\n"
SA_PROOF_NEW = ("        R, L = before[-1], after[-1]                              # S500 (F-801): the NEWEST closing after the vouchers -- "
                "a correction made in Marg after a wrong check is seen\n")


def build_stock_app(t):
    t = one(t, SA_PROOF_OLD, SA_PROOF_NEW, "_s446_proof: the closing it reads")
    return before(t, "    n = 0\n    for it in items:\n        name = (it.get(\"item\") or \"\").strip()\n        if not name:\n            continue\n"
                     "        con.execute(\n            \"INSERT INTO \" + _table + \" (as_on,item,qty,packing,pack_size,loaded_at,source) \"\n",
                  SA_GUARD, "api_snapshot: the insert loop")


# =====================================================================================================================
# order_rules.py -- ONE guarded call in tick()
# =====================================================================================================================
OR_FUNC = r'''def _s500_reports(con, out, now=None):
    """S500 (D694): the morning reports' watch rides the ten-minute tick -- at most one message a day to the owner about each of the two
    reports (wrong on the second try, or not right by the hour).  Never raises; its result is one more key of the tick's own answer."""
    try:
        import reports_watch                                  # noqa: PLC0415
        r = reports_watch.tick(con)
    except Exception as e:                                    # noqa: BLE001
        r = "error: %s" % str(e)[:80]
    if isinstance(out, dict):
        out["reports"] = r
    return out


'''


def build_order_rules(t):
    t = before(t, "def tick(con, now=None):\n", OR_FUNC, "def tick")
    t = after(t, "    s454 = _s454_pass(con)                                    # S454: before the notices, so the reminder names what is still due\n",
              "    _s500_reports(con, s454)                                  # S500: the morning reports' watch (reports_watch.tick)\n",
              "tick: the s454 pass")
    return t


BUILD = {"reports_tile.py": build_reports_tile, "stock_app.py": build_stock_app, "order_rules.py": build_order_rules}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True, help="the folder holding the three live files")
    ap.add_argument("--out", required=True, help="where the built files are written (created)")
    a = ap.parse_args(argv)
    built = {}
    try:
        for name, fn in BUILD.items():
            raw = open(os.path.join(a.finance, name), "rb").read()
            frm, to = PINS[name]
            if md5(raw) != frm:
                raise Stop("%s is %s, not the FROM pin %s -- someone changed it since the brief" % (name, md5(raw), frm))
            if b"\r" in raw:
                raise Stop("%s carries carriage returns" % name)
            new = fn(raw.decode("utf-8")).encode("utf-8")
            compile(new, name, "exec")
            if md5(new) != to:
                raise Stop("%s built to %s, not the TO pin %s" % (name, md5(new), to))
            built[name] = new
    except Stop as e:
        print("STOP: %s" % e)
        return 2
    os.makedirs(a.out, exist_ok=True)
    for name, new in built.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(new)
        print("%s  %s -> %s  (+%d lines)" % (name, PINS[name][0][:8], PINS[name][1][:8],
                                             new.count(b"\n") - open(os.path.join(a.finance, name), "rb").read().count(b"\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
