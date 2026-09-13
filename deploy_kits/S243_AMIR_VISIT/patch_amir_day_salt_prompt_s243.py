#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_amir_day_salt_prompt_s243.py -- S243_AMIR_VISIT: the salt-list prompt and the visit summary.

Builds the kit's amir_day.py FROM the live bytes (S241_AMIR_SALTS pin ae2c8939...) by thirteen
anchored edits, each anchor asserted to occur EXACTLY ONCE, else REFUSED and nothing is
written.  The kit ships the RESULT as a full file; the installer places that full file (never
a hand-edited diff), and this patcher's --selftest proves, on the box, that patch(live) is
byte-for-byte the file being placed.

What it adds (owner ruling 13-Sep-2026):

  (a) the SALT WISE ITEM LIST prompt.  Once his salt tasks are ticked, the server asks HIM to
      generate Marg's SALT WISE ITEM LIST -- red on step 6 and on the close screen -- and keeps it
      raised until the list arrives.  Arrival is read, never asked: the `mi_file` row marg_ingest
      writes the moment the one door takes a SALT_WISE_ITEM_LIST (S240), with salts_refresh.py's
      state file (S243_SALTS_REFRESH) as the "applied to the salts page" detail.  It is a PROMPT,
      not a gate: done[6] and the day's OPEN/CLOSED state never depend on it.
  (b) "Amir's visit -- what was done": /finance/amir/day/api/visit-summary?date= (checker only)
      and a collapsed <details> block of the same on /finance/amir/day (English).  The hub's
      Marg card gets a collapsed block fed by the same API (patch_hub_amir_visit_s243.py).
  (c) FOUND BY THIS KIT'S WALK, fixed here because the file is replaced whole: the live
      _export_state() and _bills() compare substr(export_stamp,1,10) with yyyy-mm-dd, but the
      door (purchase_app STAMP_RE) writes export_stamp as YYYYMMDD-HHMMSS -- so step 4 ("Jaanch")
      could NEVER verify a real export and today's bills always fell under "pichhla baaki".  The
      S241 fixture used a yyyy-mm-dd stamp, which is why 65 green checks missed it.  Both shapes
      are now read (_export_day_sql), and _hhmm() shows the time out of Marg's stamp.

    python3 -B patch_amir_day_salt_prompt_s243.py <live amir_day.py> <out amir_day.py>
    python3 -B patch_amir_day_salt_prompt_s243.py --selftest <live amir_day.py> [<kit amir_day.py>]
"""
import hashlib
import io
import sys

FROM_PIN = "ae2c89398e3c1fa63f9dadcff9e69d84"      # amir_day.py, S241_AMIR_SALTS, live 13-Sep-2026
MARK = "S243_AMIR_VISIT"

# ---------------------------------------------------------------- 1 docstring
A1_OLD = 'Schema is additive and lazy (F-303): created on first request, never at import.\n"""\n'
A1_NEW = ('Schema is additive and lazy (F-303): created on first request, never at import.\n'
          '\n'
          'S243_AMIR_VISIT (owner ruling 13-Sep-2026):\n'
          '  * Once his salt tasks are ticked the server asks HIM for Marg\'s SALT WISE ITEM\n'
          '    LIST and keeps it raised (red to him, amber to the owner) until the list is seen\n'
          '    to arrive -- read from the mi_file row the one door writes, never asked.  It is\n'
          '    a PROMPT, not a gate: the day\'s OPEN/CLOSED state does not depend on it.\n'
          '  * "Amir\'s visit -- what was done": one readable summary for the owner, as JSON at\n'
          '    /finance/amir/day/api/visit-summary (checker only) and as a collapsed block on\n'
          '    /finance/amir/day and on the hub\'s Marg card.\n'
          '"""\n')

# ---------------------------------------------------------------- 2 imports
A2_OLD = 'import html\nfrom datetime import datetime, timedelta, timezone\n'
A2_NEW = 'import html\nimport json\nimport os\nimport re\nfrom datetime import datetime, timedelta, timezone\n'

# ---------------------------------------------------------------- 3 constants
A3_OLD = 'GATE_STEPS = (2, 4, 5, 6)\n'
A3_NEW = A3_OLD + (
    '\n'
    '# S243_AMIR_VISIT: the Marg export that proves his salt work reached Marg.  marg_ingest\n'
    '# rows every file the one door takes in mi_file with this type; salts_refresh.py (cron,\n'
    '# every 10 min) then applies the newest kept one to the salts page and writes its state.\n'
    'SALT_LIST_TYPE = "SALT_WISE_ITEM_LIST"\n'
    'SALTS_STATE = os.environ.get("SALTS_REFRESH_STATE", "/root/finance/salts_refresh.state.json")\n'
    '_STAMP14 = re.compile(r"^(\\d{4})(\\d{2})(\\d{2})-(\\d{2})(\\d{2})(\\d{2})$")\n'
    '_STAMP_IN_NAME = re.compile(r"__(\\d{8}-\\d{6})__")\n')

# ---------------------------------------------------------------- 4 helpers, after _table_exists
A4_OLD = '    return r is not None\n\n\n'
A4_NEW = A4_OLD + '''def _norm_ts(s):
    """Any stored time -> 'YYYY-MM-DD HH:MM:SS' so three writers' stamps compare as text.

    marg_ingest keeps the capture stamp as YYYYMMDD-HHMMSS and received_at as ISO with
    the zone; purchase_app writes done_at as ISO with a 'T'; amir_salts with a space.
    """
    if not s:
        return None
    s = str(s).strip()
    m = _STAMP14.match(s)
    if m:
        return "%s-%s-%s %s:%s:%s" % m.groups()
    s = s.replace("T", " ")
    if len(s) >= 19:
        return s[:19]
    if len(s) == 16:
        return s + ":00"
    if len(s) == 10:
        return s + " 00:00:00"
    return None


def _dm_hm(ts):
    """'2026-09-13 08:12:00' -> '13-09 08:12' -- day-month and the time, for a phone line."""
    t = _norm_ts(ts)
    if not t:
        return ""
    return "%s-%s %s" % (t[8:10], t[5:7], t[11:16])


def _export_day_sql(p=""):
    """The DAY of a purchase_export row, in SQL, from Marg's own stamp -- both shapes.

    S243 fix: the door writes export_stamp as YYYYMMDD-HHMMSS (purchase_app STAMP_RE), so
    the S241 substr(...,1,10) = 'yyyy-mm-dd' could never match a real export; step 4 could
    never verify and every bill of the day read as carried.  `p` is the table alias prefix.
    """
    s, r = p + "export_stamp", p + "received_at"
    return ("CASE WHEN %s GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-*' "
            "THEN substr(%s,1,4)||'-'||substr(%s,5,2)||'-'||substr(%s,7,2) "
            "ELSE substr(COALESCE(%s, %s), 1, 10) END" % (s, s, s, s, s, r))


def _salt_list_state(cx, day):
    """Marg's SALT WISE ITEM LIST against his salt ticks.  A PROMPT, never a gate (13-Sep ruling).

    pending -- ticks exist (up to the end of `day`) that no list has followed: raise it,
               red to him, amber to the owner, until a newer list is seen.
    fresh   -- a list arrived after the ticks of `day`: green, with the arrival time.
    Everything here is READ: purchase_salt_task (his ticks), mi_file (the door's record of
    every SALT_WISE_ITEM_LIST it took), salts_refresh's state file (applied to the salts page).
    Nothing here changes done[6] or the day's OPEN/CLOSED state.
    """
    end = day + " 23:59:59"
    st = {"ticks_day": 0, "ticked_by": [], "last_tick": None, "since_list": 0,
          "last_list": None, "list_verdict": "", "lists_day": 0,
          "pending": False, "fresh": False,
          "applied_at": None, "applied_file": "", "applied_stamp": None, "applied_as_on": ""}
    ticks = []
    if _table_exists(cx, "purchase_salt_task"):
        for r in cx.execute("SELECT done_at, done_by FROM purchase_salt_task "
                            "WHERE COALESCE(done, 0) = 1 AND done_at IS NOT NULL").fetchall():
            t = _norm_ts(r["done_at"])
            if t and t <= end:
                ticks.append((t, r["done_by"] or ""))
        st["ticks_day"] = sum(1 for t, _b in ticks if t[:10] == day)
        st["ticked_by"] = sorted({b for t, b in ticks if t[:10] == day and b})
        if ticks:
            st["last_tick"] = max(t for t, _b in ticks)
    if _table_exists(cx, "mi_file"):
        lists = []
        for r in cx.execute("SELECT stamp, received_at, verdict FROM mi_file WHERE type = ?",
                            (SALT_LIST_TYPE,)).fetchall():
            t = _norm_ts(r["stamp"]) or _norm_ts(r["received_at"])
            if t:
                lists.append((t, r["verdict"] or ""))
        if lists:
            t, v = max(lists)
            st["last_list"], st["list_verdict"] = t, v
            st["lists_day"] = sum(1 for t2, _v in lists if t2[:10] == day)
    if st["last_tick"]:
        if st["last_list"] is None or st["last_list"] < st["last_tick"]:
            st["pending"] = True
            st["since_list"] = sum(1 for t, _b in ticks
                                   if st["last_list"] is None or t > st["last_list"])
        elif st["ticks_day"]:
            st["fresh"] = True
    try:
        with open(SALTS_STATE, encoding="utf-8") as fh:
            j = json.load(fh)
        if isinstance(j, dict) and j.get("ok"):
            st["applied_at"] = _norm_ts(j.get("applied_at"))
            st["applied_file"] = str(j.get("file") or "")[:100]
            st["applied_as_on"] = str(j.get("as_on") or "")[:10]
            m = _STAMP_IN_NAME.search(st["applied_file"])
            if m:
                st["applied_stamp"] = _norm_ts(m.group(1))
    except (OSError, ValueError, TypeError):
        pass
    return st


def _salt_prompt_amir(w):
    """His line, Hinglish: red until the list is seen, green with the time once it is."""
    s = w.get("salt_list") or {}
    if s.get("pending"):
        when = ("aakhri list %s ki thi" % _dm_hm(s["last_list"])) if s.get("last_list") \\
            else "abhi tak koi list nahi aayi"
        return ("<div class=line><span class='big bad'>Marg se SALT WISE ITEM LIST nikaalo "
                "&mdash; yahan khud tick ho jayegi</span><br>"
                "<span class=sub>%d kaam tick hue, list abhi nahi aayi &middot; %s</span></div>"
                % (int(s.get("since_list") or 0), _esc(when)))
    if s.get("fresh"):
        return ("<div class=line><span class='big good'>SALT WISE ITEM LIST aa gayi &#10003; %s"
                "</span><br><span class=sub>Aaj ke %d tick ke baad. Kuch karna nahi hai.</span></div>"
                % (_esc(_dm_hm(s.get("last_list"))), int(s.get("ticks_day") or 0)))
    return ""


def _salt_owner_line(s):
    """The same fact in English for the owner: (css class, one line)."""
    s = s or {}
    if s.get("pending"):
        last = (" (last list %s)" % _dm_hm(s["last_list"])) if s.get("last_list") else " (no list seen yet)"
        return "warn", ("Waiting for Marg's SALT WISE ITEM LIST -- %d salt task%s ticked since the last list%s. "
                        "Amir is asked for it on his screen." % (int(s.get("since_list") or 0),
                                                                  "" if s.get("since_list") == 1 else "s", last))
    if s.get("fresh"):
        return "good", ("Salt list arrived %s, after the day's %d tick%s."
                        % (_dm_hm(s.get("last_list")), int(s.get("ticks_day") or 0),
                           "" if s.get("ticks_day") == 1 else "s"))
    if s.get("last_list"):
        return "", "No salt ticks on this day. Last list from Marg %s." % _dm_hm(s["last_list"])
    return "", "No salt ticks on this day. No SALT WISE ITEM LIST seen yet."


'''

# ---------------------------------------------------------------- 5 _work
A5_OLD = '        "closed": dict(closed) if closed else None,\n    }\n'
A5_NEW = ('        "closed": dict(closed) if closed else None,\n'
          '        "salt_list": _salt_list_state(cx, day),           # S243: a prompt, not a gate\n'
          '    }\n')

# ---------------------------------------------------------------- 6 css
A6_OLD = '.foot{color:var(--soft);font-size:13px;margin:16px 0 0;text-align:center}\n"""\n'
A6_NEW = ('.foot{color:var(--soft);font-size:13px;margin:16px 0 0;text-align:center}\n'
          'details.visit{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:0 0 14px}\n'
          'details.visit summary{cursor:pointer;font-weight:600;font-size:17px}\n'
          'details.visit .k{color:var(--soft);font-size:13px}\n'
          '"""\n')

# ---------------------------------------------------------------- 7 step 6
A7_OLD = '"</form>")\n    return _page(6, w, "Salt / naam", body)\n'
A7_NEW = ('"</form>")\n'
          '    prompt = _salt_prompt_amir(w)                       # S243: red until Marg\'s list is seen\n'
          '    if prompt:\n'
          '        body += "<div class=card>%s</div>" % prompt\n'
          '    return _page(6, w, "Salt / naam", body)\n')

# ---------------------------------------------------------------- 8 close-screen summary
A8_OLD = ('    rows.append("<div class=line>Salt / naam: <b>%s</b></div>"\n'
          '                % ("ho gaya" if w["done"].get(6) else "baaki"))\n'
          '    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>" % "".join(rows)\n')
A8_NEW = ('    rows.append("<div class=line>Salt / naam: <b>%s</b></div>"\n'
          '                % ("ho gaya" if w["done"].get(6) else "baaki"))\n'
          '    prompt = _salt_prompt_amir(w)                       # S243: stays raised on the close screen too\n'
          '    if prompt:\n'
          '        rows.append(prompt)\n'
          '    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>" % "".join(rows)\n')

# ---------------------------------------------------------------- 9 owner page
A9_OLD = ('               _esc((oldest["o"] or "-") if oldest else "-")))\n'
          '    return _shell("Amir\'s day", body)\n')
A9_NEW = ('               _esc((oldest["o"] or "-") if oldest else "-")))\n'
          '    # S243: the salt list, amber until it arrives; and the visit summary, collapsed\n'
          '    cls, line = _salt_owner_line(w.get("salt_list"))\n'
          '    body += ("<div class=card><h2>Salt list from Marg</h2><p class=\'big %s\'>%s</p>%s</div>"\n'
          '             % (cls, _esc(line), _applied_line(w.get("salt_list"))))\n'
          '    body += _visit_details_html(_visit_summary(cx, day))\n'
          '    return _shell("Amir\'s day", body)\n')

# ---------------------------------------------------------------- 10 the summary + api, before healthz
A10_OLD = ('@bp.route("/finance/amir/api/healthz")\n'
           'def healthz():\n'
           '    return {"ok": True, "kit": "S241_AMIR_DAY", "at": _stamp()}\n')
A10_NEW = '''# --------------------------------------------------------------------------
# S243_AMIR_VISIT -- "Amir's visit -- what was done", for the owner
# --------------------------------------------------------------------------

MARK_KIT = "S243_AMIR_VISIT"


def _applied_line(s):
    s = s or {}
    if not s.get("applied_at"):
        return ""
    return ("<p class=sub>Salts page refreshed %s from the list of %s.</p>"
            % (_esc(_dm_hm(s["applied_at"])), _esc(s.get("applied_as_on") or "-")))


def _visit_summary(cx, day):
    """Everything the owner wants to read about one visit, gathered once, JSON-safe.

    Counts only; no bill text beyond supplier-free numbers, no names but the login that
    did the work.  One verdict per step 1-7: done / skipped / not needed / partly / not yet
    / open.  'skipped' means the day moved past a step without its tap.
    """
    w = _work(cx, day)
    s = w["salt_list"]
    nxt = _next_step(w)
    closed = bool(w["done"].get(7))
    ticks = w["ticks"]

    # ---- bills he tapped
    by_reason = {}
    for r in cx.execute("SELECT reason, COUNT(*) AS n FROM amir_bill_disposition WHERE day = ? "
                        "GROUP BY reason", (day,)).fetchall():
        by_reason[r["reason"]] = {"label": REASON_MAP.get(r["reason"], r["reason"]), "n": int(r["n"])}
    tapped = sum(v["n"] for v in by_reason.values())
    remaining = len(w["today_bills"]) + len(w["carry_bills"])
    bills_line = ", ".join("%s %d" % (v["label"], v["n"]) for _k, v in sorted(by_reason.items())) or "none"

    # ---- purchase reports the server received that day
    reports = []
    if _table_exists(cx, "purchase_export"):
        for r in cx.execute(
                """SELECT type, n_rows, grand_amount_p, export_stamp, received_at, period_from, period_to
                     FROM purchase_export
                    WHERE superseded_by IS NULL
                      AND """ + _export_day_sql() + """ = ?
                 ORDER BY COALESCE(export_stamp, received_at)""", (day,)).fetchall():
            d = dict(r)
            reports.append({"type": d.get("type"), "rows": d.get("n_rows"),
                            "amount_p": d.get("grand_amount_p"),
                            "amount": _rupees(d.get("grand_amount_p")) if d.get("grand_amount_p") is not None else "",
                            "at": _hhmm(d.get("export_stamp") or d.get("received_at")),
                            "period": "%s to %s" % ((d.get("period_from") or "")[:10], (d.get("period_to") or "")[:10])})
    bw = [r for r in reports if r["type"] == "BILLWISE"]
    rep_bills = bw[-1]["rows"] if bw else None
    rep_amount_p = bw[-1]["amount_p"] if bw and bw[-1]["amount_p"] is not None else None
    reports_line = ("; ".join("%s %s rows%s at %s" % (r["type"], r["rows"] if r["rows"] is not None else "?",
                                                     (" Rs %s" % r["amount"]) if r["amount"] else "", r["at"])
                              for r in reports) or "none received")

    # ---- salt work
    by_section = {}
    ticked_by = []
    if _table_exists(cx, "purchase_salt_task"):
        for r in cx.execute("SELECT section, done_by, done_at FROM purchase_salt_task "
                            "WHERE COALESCE(done, 0) = 1 AND done_at IS NOT NULL").fetchall():
            t = _norm_ts(r["done_at"])
            if t and t[:10] == day:
                by_section[r["section"]] = by_section.get(r["section"], 0) + 1
                if r["done_by"] and r["done_by"] not in ticked_by:
                    ticked_by.append(r["done_by"])
    salt_ticked = sum(by_section.values())
    uploads = {"n": 0, "ticked": 0}
    if _table_exists(cx, "amir_salt_upload"):
        r = cx.execute("SELECT COUNT(*) AS n, COALESCE(SUM(ticked), 0) AS t FROM amir_salt_upload "
                       "WHERE substr(uploaded_at, 1, 10) = ?", (day,)).fetchone()
        uploads = {"n": int(r["n"] or 0), "ticked": int(r["t"] or 0)}
    salts_line = ("renames %d, new salts %d, salt changes %d, cleanup %d; %d sheet upload%s"
                  % (by_section.get("rename", 0), by_section.get("create", 0), by_section.get("change", 0),
                     by_section.get("cleanup", 0), uploads["n"], "" if uploads["n"] == 1 else "s"))

    # ---- claims he raised
    claims_by = {}
    claims_n = 0
    claims_p = 0
    for r in cx.execute("SELECT reason, COUNT(*) AS n, COALESCE(SUM(amount_p), 0) AS v FROM amir_claim "
                        "WHERE substr(raised_at, 1, 10) = ? GROUP BY reason", (day,)).fetchall():
        claims_by[r["reason"]] = {"label": REASON_MAP.get(r["reason"], r["reason"]), "n": int(r["n"]),
                                  "amount_p": int(r["v"] or 0)}
        claims_n += int(r["n"])
        claims_p += int(r["v"] or 0)

    # ---- one verdict per step
    def tick_note(n):
        t = ticks.get(n) or {}
        who = (" by %s" % t["by_user"]) if t.get("by_user") else ""
        return "%s%s" % (_hhmm(t.get("done_at")), who)

    def tap_step(n, label, skipped_note):
        if n in ticks:
            return {"n": n, "label": label, "state": "done", "note": tick_note(n)}
        if closed or nxt > n:
            return {"n": n, "label": label, "state": "skipped", "note": skipped_note}
        return {"n": n, "label": label, "state": "not yet", "note": ""}

    steps = [tap_step(1, "Punch", "no punch tap recorded"),
             tap_step(2, "Bill entry", "no 'all bills entered' tap")]
    have_all = all(e["have"] for e in w["exports"])
    if 3 in ticks:
        steps.append({"n": 3, "label": "Export", "state": "done", "note": tick_note(3)})
    elif have_all:
        steps.append({"n": 3, "label": "Export", "state": "done",
                      "note": "both reports arrived; the tap itself was not made"})
    elif closed or nxt > 3:
        steps.append({"n": 3, "label": "Export", "state": "skipped", "note": "no export tap"})
    else:
        steps.append({"n": 3, "label": "Export", "state": "not yet", "note": ""})
    if have_all:
        steps.append({"n": 4, "label": "Check", "state": "done",
                      "note": "; ".join("%s %s rows at %s" % (e["label"], e.get("rows", ""), e.get("at", ""))
                                        for e in w["exports"])})
    else:
        missing = [e["label"] for e in w["exports"] if not e["have"]]
        steps.append({"n": 4, "label": "Check", "state": "not done",
                      "note": "%s not verified" % " and ".join(missing)})
    if remaining == 0 and tapped == 0:
        steps.append({"n": 5, "label": "Bills", "state": "not needed", "note": "no bill waited for a tap"})
    elif remaining == 0:
        steps.append({"n": 5, "label": "Bills", "state": "done", "note": "%d tapped (%s)" % (tapped, bills_line)})
    elif tapped:
        steps.append({"n": 5, "label": "Bills", "state": "partly",
                      "note": "%d tapped, %d still to tap" % (tapped, remaining)})
    else:
        steps.append({"n": 5, "label": "Bills", "state": "not yet", "note": "%d to tap" % remaining})
    s6 = tap_step(6, "Salt/naam", "no salt tap")
    if salt_ticked:
        s6["note"] = ("%s; %d task%s ticked" % (s6["note"], salt_ticked, "" if salt_ticked == 1 else "s")).strip("; ")
    steps.append(s6)
    if closed:
        c = w["closed"] or {}
        steps.append({"n": 7, "label": "Band", "state": "done",
                      "note": "%s%s" % (_hhmm(c.get("closed_at")), (" by %s" % c["closed_by"]) if c.get("closed_by") else "")})
    else:
        steps.append({"n": 7, "label": "Band", "state": "open", "note": "; ".join(_left(w)) or "ready to close"})

    cls, owner_line = _salt_owner_line(s)
    sl = dict(s)
    sl["owner_line"] = owner_line
    sl["css"] = cls
    return {
        "ok": True, "kit": MARK_KIT, "day": day,
        "state": "CLOSED" if closed else "OPEN",
        "closed_at": (w["closed"] or {}).get("closed_at") if closed else None,
        "opened_at": (cx.execute("SELECT opened_at FROM amir_day WHERE day = ?", (day,)).fetchone() or {"opened_at": None})["opened_at"],
        "next_step": nxt, "left": _left(w),
        "bills": {"tapped": tapped, "by_reason": by_reason, "remaining_today": len(w["today_bills"]),
                  "carried": len(w["carry_bills"]), "line": bills_line},
        "reports": {"rows": reports, "bills": rep_bills, "amount_p": rep_amount_p,
                    "amount": _rupees(rep_amount_p) if rep_amount_p is not None else "", "line": reports_line},
        "salts": {"ticked": salt_ticked, "by_section": by_section, "renames": by_section.get("rename", 0),
                  "ticked_by": ticked_by, "uploads": uploads, "line": salts_line},
        "claims": {"n": claims_n, "amount_p": claims_p, "amount": _rupees(claims_p), "by_reason": claims_by},
        "salt_list": sl,
        "steps": steps,
        "generated_at": _stamp(),
    }


def _visit_details_html(v):
    """The collapsed block for /finance/amir/day.  Server-rendered, no JavaScript."""
    rows = []
    for st in v["steps"]:
        cls = "good" if st["state"] == "done" else ("" if st["state"] == "not needed" else "warn")
        rows.append("<tr><td>%d</td><td>%s</td><td class='%s'>%s</td><td class=k>%s</td></tr>"
                    % (st["n"], _esc(st["label"]), cls, _esc(st["state"]), _esc(st.get("note", ""))))
    sl = v["salt_list"]
    head = "%s -- %s%s" % (v["day"], v["state"], (" at %s" % _hhmm(v["closed_at"])) if v.get("closed_at") else "")
    return ("<details class=visit><summary>Amir's visit &mdash; what was done</summary>"
            "<p class=sub>%s</p>"
            "<div class=tscroll><table><tr><th>step</th><th></th><th>verdict</th><th>detail</th></tr>%s</table></div>"
            "<div class=line>Bills tapped: <b>%d</b> <span class=k>(%s)</span></div>"
            "<div class=line>Purchase reports received: <span class=k>%s</span></div>"
            "<div class=line>Salt tasks ticked: <b>%d</b> <span class=k>(%s%s)</span></div>"
            "<div class=line>Claims raised for Darpan: <b>%d</b>, worth &#8377;%s</div>"
            "<div class=line>Salt list from Marg: <span class='%s'>%s</span></div>"
            "</details>"
            % (_esc(head), "".join(rows),
               v["bills"]["tapped"], _esc(v["bills"]["line"]),
               _esc(v["reports"]["line"]),
               v["salts"]["ticked"], _esc(v["salts"]["line"]),
               (" by %s" % ", ".join(v["salts"]["ticked_by"])) if v["salts"]["ticked_by"] else "",
               v["claims"]["n"], _esc(v["claims"]["amount"]),
               sl.get("css", ""), _esc(sl.get("owner_line", ""))))


@bp.route("/finance/amir/day/api/visit-summary")
def visit_summary():
    """The owner's summary of one visit.  Checker only -- the hub's block reads this."""
    u, err = _require("checker", unit=_unit)
    if err:
        return {"ok": False, "error": "not_permitted",
                "message": "Only the checker may read the visit summary."}, 403
    day = (request.args.get("date") or request.args.get("d") or _today())[:10]
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", day):
        return {"ok": False, "error": "bad_date", "message": "date must be yyyy-mm-dd"}, 400
    cx = _db()
    _ensure(cx)
    return _visit_summary(cx, day)


@bp.route("/finance/amir/api/healthz")
def healthz():
    return {"ok": True, "kit": "S243_AMIR_VISIT", "at": _stamp()}
'''

# ---------------------------------------------------------------- 11-13 the export-stamp fix (found by the walk)
A11_OLD = ('    s = str(s).replace("T", " ")\n'
           '    return s[11:16] if len(s) >= 16 else s\n')
A11_NEW = ('    s = str(s).replace("T", " ")\n'
           '    m = _STAMP14.match(s)                     # S243: Marg\'s own YYYYMMDD-HHMMSS export stamp\n'
           '    if m:\n'
           '        s = "%s-%s-%s %s:%s:%s" % m.groups()\n'
           '    return s[11:16] if len(s) >= 16 else s\n')
A12_OLD = ('                  AND substr(COALESCE(export_stamp, received_at), 1, 10) = ?\n'
           '             ORDER BY COALESCE(export_stamp, received_at) DESC\n')
A12_NEW = ('                  AND """ + _export_day_sql() + """ = ?\n'
           '             ORDER BY COALESCE(export_stamp, received_at) DESC\n')
A13_OLD = '                  substr(COALESCE(e.export_stamp, e.received_at), 1, 10) AS seen_day\n'
A13_NEW = '                  """ + _export_day_sql("e.") + """ AS seen_day\n'

ANCHORS = (("A1 docstring", A1_OLD, A1_NEW), ("A2 imports", A2_OLD, A2_NEW), ("A3 constants", A3_OLD, A3_NEW),
           ("A4 helpers", A4_OLD, A4_NEW), ("A5 _work", A5_OLD, A5_NEW), ("A6 css", A6_OLD, A6_NEW),
           ("A7 step6", A7_OLD, A7_NEW), ("A8 summary", A8_OLD, A8_NEW), ("A9 owner page", A9_OLD, A9_NEW),
           ("A10 api", A10_OLD, A10_NEW), ("A11 _hhmm", A11_OLD, A11_NEW),
           ("A12 _export_state", A12_OLD, A12_NEW), ("A13 _bills", A13_OLD, A13_NEW))


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(src):
    if MARK in src:
        return src, "already"
    for nm, old, _new in ANCHORS:
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n)
    out = src
    for _nm, old, new in ANCHORS:
        out = out.replace(old, new, 1)
    return out, "patched"


def selftest(live, kit=None):
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  PASS ", name)
        else:
            bad += 1
            print("  FAIL ", name)

    raw = io.open(live, "rb").read()
    check("live amir_day.py is the pin %s" % FROM_PIN[:8], md5(raw) == FROM_PIN)
    src = raw.decode("utf-8")
    out, st = patch_text(src)
    check("patches (%s)" % st, st == "patched")
    if st == "patched":
        try:
            compile(out, "amir_day.py", "exec")
            check("compiles", True)
        except SyntaxError as ex:
            check("compiles (%s)" % ex, False)
        check("only additions, bar the healthz kit name and the three export-stamp lines",
              all(ln in out for ln in src.splitlines() if ln.strip() and "S241_AMIR_DAY" not in ln
                  and "substr(COALESCE(e" not in ln and "substr(COALESCE(export_stamp" not in ln
                  and ln != "    return s[11:16] if len(s) >= 16 else s"))
        check("the export-stamp fix landed in _export_state, _bills and _hhmm",
              out.count('_export_day_sql() + """ = ?') == 2 and out.count('_export_day_sql("e.")') == 1
              and "m = _STAMP14.match(s)" in out)
        check("healthz names the kit and the route exists once",
              out.count('"kit": "S243_AMIR_VISIT"') == 1 and out.count('/finance/amir/day/api/visit-summary")') == 1)
        check("the gate is untouched: GATE_STEPS and done[6] as before",
              "GATE_STEPS = (2, 4, 5, 6)\n" in out and "done[6] = 6 in ticks\n" in out
              and "salt_list" not in out[out.find("def _ready_to_close"):out.find("def _left")])
        check("the prompt rides on step 6 and the close screen",
              out.count("prompt = _salt_prompt_amir(w)") == 2)
        check("second run is a no-op", patch_text(out)[1] == "already")
        if kit:
            kb = io.open(kit, "rb").read()
            check("patch(live) is byte-for-byte the kit's amir_day.py (%s)" % md5(kb)[:8],
                  kb == out.encode("utf-8"))
    check("a stranger file is refused", patch_text("x = 1\n")[1].startswith("refused"))
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if argv and argv[0] == "--selftest":
        if len(argv) < 2:
            print("usage: --selftest <live amir_day.py> [<kit amir_day.py>]")
            return 2
        return selftest(argv[1], argv[2] if len(argv) > 2 else None)
    if len(argv) != 2:
        print(__doc__)
        return 2
    raw = io.open(argv[0], "rb").read()
    print("source %s md5 %s" % (argv[0], md5(raw)))
    if md5(raw) != FROM_PIN:
        print("REFUSED: source pin is not %s -- the live file moved since this patch was built" % FROM_PIN[:8])
        return 2
    new, st = patch_text(raw.decode("utf-8"))
    if st == "already":
        print("ALREADY PATCHED -- nothing to do")
        return 0
    if st != "patched":
        print("REFUSED: %s -- nothing written" % st[len("refused: "):])
        return 2
    compile(new, argv[1], "exec")
    io.open(argv[1], "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s md5 %s" % (argv[1], md5(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
