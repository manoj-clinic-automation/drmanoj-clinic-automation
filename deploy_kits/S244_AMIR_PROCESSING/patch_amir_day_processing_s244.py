#!/usr/bin/env python3
"""S244_AMIR_PROCESSING -- amir_day.py: processing / processing done / still to make.

Every replacement is an exact, unique, asserted string swap.  If the source file
is not the live one, or any anchor has moved, this refuses and writes nothing.
"""
import hashlib
import io
import os
import sys

SRC_MD5 = "bf7d9826119edab48652fd959e1e8da5"          # live /root/finance/amir_day.py, S243

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


# ---------------------------------------------------------------- 1. docstring
edit(
    "docstring",
    '''  * "Amir's visit -- what was done": one readable summary for the owner, as JSON at
    /finance/amir/day/api/visit-summary (checker only) and as a collapsed block on
    /finance/amir/day and on the hub's Marg card.
"""''',
    '''  * "Amir's visit -- what was done": one readable summary for the owner, as JSON at
    /finance/amir/day/api/visit-summary (checker only) and as a collapsed block on
    /finance/amir/day and on the hub's Marg card.

S244_AMIR_PROCESSING (owner ruling 13-Sep-2026):
  * A report he has just exported is PROCESSING, not missing.  Saying "aaj ki nahi
    aayi" while a fresh file is still in transit is what made him export the same
    report three times on 13-Sep.  Step 4 now says: ban rahi hai -> jaanch poori ->
    and only then names what still has to be generated.
  * Processing never holds him up.  While a report is on its way step 4 is skipped
    by the "where did I leave off" jump and carries a button straight to step 5, so
    he starts his next task and the server keeps checking on its own.
  * Step 3 prints the two dates he must type into Marg, so the TO date cannot be
    yesterday's by habit.
"""''',
)

# ---------------------------------------------------------------- 2. constants
edit(
    "constants",
    '''_STAMP14 = re.compile(r"^(\\d{4})(\\d{2})(\\d{2})-(\\d{2})(\\d{2})(\\d{2})$")
_STAMP_IN_NAME = re.compile(r"__(\\d{8}-\\d{6})__")''',
    '''_STAMP14 = re.compile(r"^(\\d{4})(\\d{2})(\\d{2})-(\\d{2})(\\d{2})(\\d{2})$")
_STAMP_IN_NAME = re.compile(r"__(\\d{8}-\\d{6})__")

# S244: how long a freshly exported report is allowed to be in transit before the
# screen stops saying "ban rahi hai" and starts saying "dobara banaiye".  Marg writes
# the file, MargPull picks it up and the door takes it in; ~5 minutes end to end on a
# normal day.  The clock starts when HE says he has exported (the step 3 tick, which
# is rewritten every time he asks for another look), never when the page is opened.
try:
    EXPORT_GRACE_MIN = int(os.environ.get("AMIR_EXPORT_GRACE_MIN") or 6)
except (TypeError, ValueError):
    EXPORT_GRACE_MIN = 6
if EXPORT_GRACE_MIN < 1 or EXPORT_GRACE_MIN > 60:
    EXPORT_GRACE_MIN = 6

# How often the step 4 screen re-checks itself while a report is in transit.
EXPORT_POLL_SEC = 20''',
)

# ---------------------------------------------------------------- 3. helpers
edit(
    "helpers",
    '''def _esc(v):
    return html.escape("" if v is None else str(v))''',
    '''def _mins_since(ts):
    """Whole minutes from a stored stamp to now, or None if it cannot be read."""
    t = _norm_ts(ts)
    if not t:
        return None
    try:
        d = datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
    except (TypeError, ValueError):
        return None
    return max(0, int((_now() - d).total_seconds() // 60))


def _ddmmyyyy(day):
    """'2026-09-13' -> '13-09-2026' -- the shape Marg's own date boxes use."""
    d = str(day or "")
    if len(d) != 10:
        return d
    return "%s-%s-%s" % (d[8:10], d[5:7], d[:4])


def _month_first(day):
    return (str(day or "")[:8] + "01") if len(str(day or "")) == 10 else ""


def _esc(v):
    return html.escape("" if v is None else str(v))''',
)

# ---------------------------------------------------------------- 4. _export_state
edit(
    "export_state_sig",
    '''def _export_state(cx, day):
    """Did today's pair arrive, and is each one verified?

    Read from purchase_export, which the ingest already fills.  Nothing here
    asks Amir anything -- it reports.  A report counts for today only if its
    export stamp falls on today AND it covers the 1st of the month to date.
    """
    out = []
    if not _table_exists(cx, "purchase_export"):
        for kind, label in PAIR:
            out.append({"kind": kind, "label": label, "have": False,
                        "reason": "purchase_export table not present yet"})
        return out

    first = day[:8] + "01"''',
    '''def _export_state(cx, day, wait_since=None):
    """Did today's pair arrive, is each one verified -- and is one still on its way?

    Read from purchase_export, which the ingest already fills.  Nothing here
    asks Amir anything -- it reports.  A report counts for today only if its
    export stamp falls on today AND it covers the 1st of the month to date.

    S244: every entry also carries a `state`, and `have` stays exactly what it
    always was (state == "ok"), so every gate built on it is unchanged.

        ok    verified -- arrived, today's stamp, 1st to date
        wait  he has exported and the grace window has not run out yet
        bad   the window ran out, or a file of his DID arrive and is wrong
        none  he has not said he exported yet -- nothing is expected

    `wait_since` is the step 3 tick: the moment he last said the export was taken.
    """
    waited = _mins_since(wait_since) if wait_since else None
    within = (waited is not None) and (waited < EXPORT_GRACE_MIN)
    ws = _norm_ts(wait_since) if wait_since else None

    out = []
    if not _table_exists(cx, "purchase_export"):
        for kind, label in PAIR:
            out.append({"kind": kind, "label": label, "have": False, "state": "bad",
                        "waited": waited,
                        "reason": "purchase_export table not present yet"})
        return out

    first = day[:8] + "01"''',
)

edit(
    "export_state_missing",
    '''        if row is None:
            out.append({"kind": kind, "label": label, "have": False,
                        "reason": "aaj ki nahi aayi"})
            continue''',
    '''        if row is None:
            if wait_since is None:
                state, why = "none", "abhi nikaali nahi gayi"
            elif within:
                state, why = "wait", "file ban gayi hai, server tak pahunch rahi hai"
            else:
                state, why = "bad", "aaj ki nahi aayi"
            out.append({"kind": kind, "label": label, "have": False,
                        "state": state, "waited": waited, "reason": why})
            continue''',
)

edit(
    "export_state_period",
    '''        if not (ok_from and ok_to):
            out.append({"kind": kind, "label": label, "have": False,
                        "rows": d.get("n_rows"),
                        "at": _hhmm(d.get("export_stamp") or d.get("received_at")),
                        "reason": "tareekh galat hai -- 1 tareekh se aaj tak chahiye"})
            continue
        out.append({"kind": kind, "label": label, "have": True,
                    "rows": d.get("n_rows"),
                    "period": "%s se %s" % ((d.get("period_from") or "")[:10], (d.get("period_to") or "")[:10]),
                    "at": _hhmm(d.get("export_stamp") or d.get("received_at"))})
    return out''',
    '''        if not (ok_from and ok_to):
            # A file with the wrong period IS his file, so it is news, not silence.
            # If it landed after he last said "exported", tell him now -- waiting on a
            # file that has already arrived wrong is what wasted his morning.  If it is
            # older than that tick, his newer one may still be in transit.
            arrived = _norm_ts(d.get("export_stamp") or d.get("received_at"))
            fresh = bool(arrived and ws and arrived >= ws)
            if fresh or not within:
                state = "bad"
                why = "tareekh galat hai -- 1 tareekh se aaj tak chahiye"
            else:
                state = "wait"
                why = "file ban gayi hai, server tak pahunch rahi hai"
            out.append({"kind": kind, "label": label, "have": False,
                        "state": state, "waited": waited,
                        "rows": d.get("n_rows"),
                        "at": _hhmm(d.get("export_stamp") or d.get("received_at")),
                        "reason": why})
            continue
        out.append({"kind": kind, "label": label, "have": True, "state": "ok",
                    "waited": waited,
                    "rows": d.get("n_rows"),
                    "period": "%s se %s" % ((d.get("period_from") or "")[:10], (d.get("period_to") or "")[:10]),
                    "at": _hhmm(d.get("export_stamp") or d.get("received_at"))})
    return out''',
)

# ---------------------------------------------------------------- 5. _work
edit(
    "work",
    '''def _work(cx, day):
    """Everything the day needs, gathered once."""
    exports = _export_state(cx, day)
    today_bills, carry_bills = _bills(cx, day)
    ticks = {
        int(r["step"]): dict(r)
        for r in cx.execute("SELECT step, done_at, by_user FROM amir_step WHERE day=?", (day,)).fetchall()
    }
    closed = cx.execute("SELECT closed_at, closed_by FROM amir_day WHERE day=?", (day,)).fetchone()''',
    '''def _work(cx, day):
    """Everything the day needs, gathered once."""
    ticks = {
        int(r["step"]): dict(r)
        for r in cx.execute("SELECT step, done_at, by_user FROM amir_step WHERE day=?", (day,)).fetchall()
    }
    # S244: the step 3 tick is the transit clock.  It is rewritten every time he asks
    # for another look, so "dobara banai" restarts the window instead of inheriting it.
    wait_since = (ticks.get(3) or {}).get("done_at")
    exports = _export_state(cx, day, wait_since)
    today_bills, carry_bills = _bills(cx, day)
    closed = cx.execute("SELECT closed_at, closed_by FROM amir_day WHERE day=?", (day,)).fetchone()''',
)

edit(
    "work_return",
    '''    return {
        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "ticks": ticks, "done": done,
        "closed": dict(closed) if closed else None,
        "salt_list": _salt_list_state(cx, day),           # S243: a prompt, not a gate
    }''',
    '''    waited = _mins_since(wait_since) if wait_since else None
    return {
        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "ticks": ticks, "done": done,
        "closed": dict(closed) if closed else None,
        "salt_list": _salt_list_state(cx, day),           # S243: a prompt, not a gate
        # S244: the three plain facts every screen asks about the pair
        "wait_since": wait_since,
        "waited_min": waited,
        "wait_left_min": (max(1, EXPORT_GRACE_MIN - waited) if waited is not None else None),
        "export_wait": any(e.get("state") == "wait" for e in exports),
        "export_bad": any(e.get("state") == "bad" for e in exports),
        "export_none": any(e.get("state") == "none" for e in exports),
    }''',
)

# ---------------------------------------------------------------- 6. _next_step
edit(
    "next_step",
    '''def _next_step(w):
    for n, _label in STEPS:
        if n == 7:
            continue
        if not w["done"].get(n):
            return n
    return 7''',
    '''def _next_step(w):
    for n, _label in STEPS:
        if n == 7:
            continue
        # S244: a report still in transit must not park him on step 4.  The server is
        # doing the waiting; he goes on to the next thing and the banner stays amber.
        if n == 4 and w.get("export_wait") and not w["done"].get(4):
            continue
        if not w["done"].get(n):
            return n
    return 7''',
)

# ---------------------------------------------------------------- 7. _left
edit(
    "left",
    '''    missing = [e["label"] for e in w["exports"] if not e["have"]]
    if missing:
        out.append("%s not verified" % " and ".join(missing))''',
    '''    waiting = [e["label"] for e in w["exports"] if e.get("state") == "wait"]
    missing = [e["label"] for e in w["exports"]
               if not e["have"] and e.get("state") != "wait"]
    if waiting:
        out.append("%s still arriving" % " and ".join(waiting))
    if missing:
        out.append("%s not verified" % " and ".join(missing))''',
)

# ---------------------------------------------------------------- 8. CSS
edit(
    "css",
    '''.steps .ok{background:#e7f3e9;border-color:#bfe0c6;color:var(--ok)}''',
    '''.steps .ok{background:#e7f3e9;border-color:#bfe0c6;color:var(--ok)}
.steps .wait{background:#fff8e1;border-color:#f0e0a8;color:var(--warn)}
.band{background:#fff8e1;border:1px solid #f0e0a8;border-radius:10px;padding:11px 12px;
      margin:0 0 14px;font-size:15px}
.band a{color:var(--accent)}
.dates{background:#f3f7fb;border:1px solid #cfe0ef;border-radius:10px;padding:12px;
       margin:10px 0 0}
.dates .d{font-size:21px;font-weight:700;letter-spacing:.5px}''',
)

# ---------------------------------------------------------------- 9. _shell / _page / _banner
edit(
    "shell",
    '''def _shell(title, body):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>%s"
            "</div></body></html>" % (_esc(title), _CSS, body))''',
    '''def _shell(title, body, head_extra=""):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "%s<title>%s</title><style>%s</style></head><body><div class=wrap>%s"
            "</div></body></html>" % (head_extra, _esc(title), _CSS, body))''',
)

edit(
    "banner",
    '''    for n, label in STEPS:
        cls = "on" if n == current else ("ok" if w["done"].get(n) else "")''',
    '''    for n, label in STEPS:
        if n == current:
            cls = "on"
        elif w["done"].get(n):
            cls = "ok"
        elif n == 4 and w.get("export_wait"):
            cls = "wait"                                  # S244: amber while in transit
        else:
            cls = ""''',
)

edit(
    "page",
    '''def _page(step, w, title, body, subtitle=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    return _shell("Amir -- kaam", _banner(step, w) + head + body +
                  "<p class=foot>Step %d of 7</p>" % step)''',
    '''def _page(step, w, title, body, subtitle="", head_extra=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    return _shell("Amir -- kaam", _banner(step, w) + head + body +
                  "<p class=foot>Step %d of 7</p>" % step, head_extra)


def _export_band(w):
    """One amber line carried on the later steps while the pair is not settled.

    It never blocks and never steals the screen -- it is there so a report that
    needs re-making is not forgotten between step 4 and the close.
    """
    if w["done"].get(4):
        return ""
    if w.get("export_bad"):
        return ("<div class=band><b>Ek report dobara banani hai.</b> "
                "<a href='/finance/amir/step/4'>Kholiye</a></div>")
    if w.get("export_wait"):
        return ("<div class=band>Report abhi ban rahi hai -- server dekh raha hai. "
                "<a href='/finance/amir/step/4'>Dekhiye</a></div>")
    return ""''',
)

# ---------------------------------------------------------------- 10. _step3
edit(
    "step3",
    '''def _step3(w):
    rows = "".join("<div class=line><span class=big>%d. %s</span><br>"
                   "<span class=sub>1 tareekh se aaj tak</span></div>"
                   % (i + 1, _esc(label)) for i, (_k, label) in enumerate(PAIR))
    body = ("<div class=card><h2>Do report nikaaliye</h2>%s</div>"
            "<div class=note>Counter par bikri shuru hone se pehle. Der ho jaye to "
            "bhi nikaal dijiye -- chhodiye mat.</div>"
            "<form method=post><input type=hidden name=tick value=3>"
            "<button class=btn name=go value=3>Dono report nikaal di -- jaanch kijiye</button>"
            "</form>" % rows)
    return _page(3, w, "Export", body)''',
    '''def _dates_block(w):
    """The two dates he must type into Marg, spelled out. (S244)

    Every failure so far has been the same one: the TO box still holding yesterday.
    Printing today's date where he can read it off the phone costs nothing.
    """
    return ("<div class=dates><div class=sub>Marg mein yeh do tareekh daaliye:</div>"
            "<div class=line>FROM &nbsp; <span class=d>%s</span></div>"
            "<div class=line>TO &nbsp;&nbsp;&nbsp;&nbsp; <span class=d>%s</span> "
            "<span class=sub>(aaj)</span></div></div>"
            % (_esc(_ddmmyyyy(_month_first(w["day"]))), _esc(_ddmmyyyy(w["day"]))))


def _step3(w):
    rows = "".join("<div class=line><span class=big>%d. %s</span><br>"
                   "<span class=sub>1 tareekh se aaj tak</span></div>"
                   % (i + 1, _esc(label)) for i, (_k, label) in enumerate(PAIR))
    body = ("<div class=card><h2>Do report nikaaliye</h2>%s%s</div>"
            "<div class=note>Counter par bikri shuru hone se pehle. Der ho jaye to "
            "bhi nikaal dijiye -- chhodiye mat.<br>"
            "<b>TO ki tareekh aaj ki honi chahiye</b> -- kal ki nahi.</div>"
            "<form method=post><input type=hidden name=tick value=3>"
            "<button class=btn name=go value=3>Dono report nikaal di -- jaanch kijiye</button>"
            "</form>" % (rows, _dates_block(w)))
    return _page(3, w, "Export", body)''',
)

# ---------------------------------------------------------------- 11. _step4
edit(
    "step4",
    '''def _step4(w):
    out = []
    for e in w["exports"]:
        if e["have"]:
            out.append("<div class=line><span class='big good'>%s &#10003;</span><br>"
                       "<span class=sub>%s &middot; %s rows &middot; %s baje</span></div>"
                       % (_esc(e["label"]), _esc(e.get("period", "")),
                          _esc(e.get("rows", "")), _esc(e.get("at", ""))))
        else:
            out.append("<div class=line><span class='big bad'>%s &#10007;</span><br>"
                       "<span class=sub>%s</span></div>"
                       % (_esc(e["label"]), _esc(e.get("reason", ""))))
    body = "<div class=card><h2>Server ne file dekhi hai</h2>%s</div>" % "".join(out)

    if all(e["have"] for e in w["exports"]):
        body += ("<form method=post><button class=btn name=go value=4>Aage badhiye</button>"
                 "</form>")
    else:
        body += ("<div class=note><p class=big>Dobara banaiye.</p>"
                 "<p><b>Pehle desktop par khuli Excel band kijiye</b> -- Marg file tab tak "
                 "dobara nahi likh sakta jab tak wo khuli hai.</p></div>"
                 "<form method=post><button class='btn plain' name=go value=4>"
                 "Dobara banai -- phir se dekhiye</button></form>")
    return _page(4, w, "Jaanch", body,
                 "Aapse nahi poochha ja raha. Server ne khud file padhi hai.")''',
    '''def _step4(w):
    """Processing -> processing done -> and only then, what is still to be made.

    S244.  The old screen had one message for two different situations: a file that
    was still crossing the wire read exactly like a file that was never made.  He
    trusted it and exported the same report three times.
    """
    waiting = bool(w.get("export_wait"))
    todo = [e for e in w["exports"] if e.get("state") == "bad"]
    notyet = [e for e in w["exports"] if e.get("state") == "none"]

    out = []
    for e in w["exports"]:
        st = e.get("state") or ("ok" if e.get("have") else "bad")
        if st == "ok":
            out.append("<div class=line><span class='big good'>%s &#10003;</span><br>"
                       "<span class=sub>%s &middot; %s rows &middot; %s baje</span></div>"
                       % (_esc(e["label"]), _esc(e.get("period", "")),
                          _esc(e.get("rows", "")), _esc(e.get("at", ""))))
        elif st == "wait":
            out.append("<div class=line><span class='big warn'>%s &hellip;</span><br>"
                       "<span class=sub>File ban gayi hai, server tak pahunch rahi hai.</span>"
                       "</div>" % _esc(e["label"]))
        elif st == "none":
            out.append("<div class=line><span class=big>%s</span><br>"
                       "<span class=sub>Abhi nikaali nahi gayi.</span></div>"
                       % _esc(e["label"]))
        else:
            out.append("<div class=line><span class='big bad'>%s &#10007;</span><br>"
                       "<span class=sub>%s</span></div>"
                       % (_esc(e["label"]), _esc(e.get("reason", ""))))

    if waiting:
        left = w.get("wait_left_min") or 1
        head = ("<div class=card><h2 class=warn>Report ban rahi hai&hellip;</h2>"
                "<p class=big>Server file le raha hai. Lagbhag <b>%d minute</b> aur.</p>"
                "<p>Aapko kuch nahi karna hai -- yeh screen khud dekhti rahegi.</p>"
                "</div>" % int(left))
    elif notyet and not todo:
        head = ("<div class=card><h2>Abhi report nikaali nahi gayi</h2>"
                "<p>Pehle dono report nikaal dijiye.</p>"
                "<p><a class='btn plain' href='/finance/amir/step/3'>"
                "Report nikaalne ka tarika</a></p></div>")
    else:
        head = ("<div class=card><h2 class=good>Jaanch poori ho gayi &#10003;</h2>"
                "<p>Server ne dono file khud padhi hai. Aapse kuch nahi poochha gaya.</p>"
                "</div>")

    body = head + "<div class=card><h2>Do report</h2>%s</div>" % "".join(out)

    if all(e["have"] for e in w["exports"]):
        body += ("<form method=post><button class=btn name=go value=4>Aage badhiye</button>"
                 "</form>")
    elif waiting:
        body += ("<form method=post><input type=hidden name=skip value=1>"
                 "<button class=btn name=go value=4>Aage ka kaam shuru kijiye</button></form>"
                 "<form method=post><button class='btn quiet' name=go value=4>"
                 "Abhi dobara dekhiye</button></form>"
                 "<p class=sub>Report aate hi yeh khud &#10003; ho jayegi. "
                 "Aap apna agla kaam kar sakte hain.</p>")
    elif todo:
        names = " aur ".join(_esc(e["label"]) for e in todo)
        body += ("<div class=note><p class=big>Dobara banaiye: %s</p>"
                 "<p><b>Pehle desktop par khuli Excel band kijiye</b> -- Marg file tab tak "
                 "dobara nahi likh sakta jab tak wo khuli hai.</p>%s</div>"
                 "<form method=post><input type=hidden name=again value=1>"
                 "<button class=btn name=go value=4>"
                 "Dobara banai -- phir se dekhiye</button></form>"
                 "<form method=post><input type=hidden name=skip value=1>"
                 "<button class='btn quiet' name=go value=4>"
                 "Aage ka kaam shuru kijiye</button></form>"
                 % (names, _dates_block(w)))

    refresh = ("<meta http-equiv=refresh content='%d'>" % EXPORT_POLL_SEC) if waiting else ""
    return _page(4, w, "Jaanch", body,
                 "Aapse nahi poochha ja raha. Server ne khud file padhi hai.",
                 head_extra=refresh)''',
)

# ---------------------------------------------------------------- 12. bands on 5 and 6
edit(
    "step5_band_empty",
    '''    if not bills and not carry:
        return _page(5, w, "Bills", "<div class=card><p class=big good>"
                     "Koi bill baaki nahi hai.</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye"
                     "</button></form>")

    body = []''',
    '''    if not bills and not carry:
        return _page(5, w, "Bills", _export_band(w) + "<div class=card><p class=big good>"
                     "Koi bill baaki nahi hai.</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye"
                     "</button></form>")

    body = [_export_band(w)]''',
)

edit(
    "step6_band",
    '''def _step6(w):
    body = ("<div class=card><h2>Salt, naye item aur naam</h2>"''',
    '''def _step6(w):
    body = (_export_band(w) +
            "<div class=card><h2>Salt, naye item aur naam</h2>"''',
)

# ---------------------------------------------------------------- 13. routes
edit(
    "route_post",
    '''        else:
            tick = request.form.get("tick")
            if tick and tick.isdigit() and int(tick) == n:
                _tick(cx, day, n, user)
        cx.commit()
        w = _work(cx, day)
        if n == 7 and w["done"].get(7):
            return _go(7)
        nxt = _next_step(w)
        return _go(nxt if nxt >= n else n + 1 if n < 7 else 7)''',
    '''        elif n == 4:
            # S244.  Nothing on step 4 is ever a claim that a report arrived -- the
            # server alone decides that.  "Dobara banai" only restarts the transit
            # clock; "Aage ka kaam" only moves him on.
            if request.form.get("again"):
                _tick(cx, day, 3, user)
            cx.commit()
            if request.form.get("skip"):
                return _go(5)
            return _go(4)
        else:
            tick = request.form.get("tick")
            if tick and tick.isdigit() and int(tick) == n:
                _tick(cx, day, n, user)
        cx.commit()
        w = _work(cx, day)
        if n == 3:
            # He has just said the export was taken: he sees the processing screen
            # once, whatever the jump would otherwise have done with it.
            return _go(4)
        if n == 7 and w["done"].get(7):
            return _go(7)
        nxt = _next_step(w)
        return _go(nxt if nxt >= n else n + 1 if n < 7 else 7)''',
)

# ---------------------------------------------------------------- 14. healthz
edit(
    "healthz",
    '''    return {"ok": True, "kit": "S243_AMIR_VISIT", "at": _stamp()}''',
    '''    return {"ok": True, "kit": "S244_AMIR_PROCESSING", "at": _stamp()}''',
)


# ---------------------------------------------------------------- apply


def _read(path):
    return io.open(path, "r", encoding="utf-8", newline="").read()


def build(src):
    """The S243 live file in, the S244 file out.  Refuses rather than guesses."""
    if "\r\n" in src:
        raise SystemExit("REFUSED: source has CRLF (F-294)")
    if hashlib.md5(src.encode("utf-8")).hexdigest() != SRC_MD5:
        raise SystemExit("REFUSED: source is not the S243 live amir_day.py (%s expected)" % SRC_MD5)
    text = src
    for name, old, new in EDITS:
        c = text.count(old)
        if c != 1:
            raise SystemExit("REFUSED: anchor %r matched %d times (need exactly 1)" % (name, c))
        text = text.replace(old, new, 1)
    if "\r\n" in text:
        raise SystemExit("REFUSED: result has CRLF")
    return text


def main(argv):
    if len(argv) == 4 and argv[1] == "--selftest":
        out = build(_read(argv[2]))
        kit = _read(argv[3])
        if out != kit:
            raise SystemExit("REFUSED: patch(live) is NOT the kit file, byte for byte")
        print("OK  patch(%s) == %s  (%d edits, md5 %s)"
              % (argv[2], argv[3], len(EDITS), hashlib.md5(kit.encode("utf-8")).hexdigest()))
        return 0
    if len(argv) == 4 and argv[1] == "--build":
        text = build(_read(argv[2]))
        d = os.path.dirname(os.path.abspath(argv[3]))
        if d:
            os.makedirs(d, exist_ok=True)
        with io.open(argv[3], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("OK  %d edits applied -> %s  (md5 %s)"
              % (len(EDITS), argv[3], hashlib.md5(text.encode("utf-8")).hexdigest()))
        return 0
    raise SystemExit("usage: %s --selftest <live amir_day.py> <kit amir_day.py>\n"
                     "       %s --build    <live amir_day.py> <out amir_day.py>"
                     % (argv[0], argv[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
