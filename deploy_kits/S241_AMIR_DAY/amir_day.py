"""
amir_day.py -- Amir's day, as seven steps on a phone.  (S241, D472)

One page, one thing at a time, a 1 -> 7 banner at the top, a confirmation after
each step, and a DAY CLOSED screen at the end.  The owner's design is in
claude/S240_AMIR_DAY_FLOW.md; the rulings behind it are D468-D477.

Principles this file is built to, and must keep:

  * He is never asked whether a report arrived.  The server reads the exports it
    already holds and TELLS him.  (D469, and "never let him certify what the
    system can verify".)
  * The bill list fills itself from the bill-wise export.  He types no bill
    number, ever.
  * The disposition of a bill is FORCED, not optional -- an optional flag is the
    one a hurried person walks past.
  * A day he leaves half-done stays OPEN, never failed.  Everything done is kept
    and the remainder comes back as "pichhla baaki".
  * Attendance never blocks his work.  Step 1 nudges; it does not gate.
  * He raises a claim; he never chases one.  Chasing is Darpan's queue.

No JavaScript.  Server-rendered HTML, phone first.  Amir's screens are Hinglish
in Latin script; the owner's view of the same day is English.

Schema is additive and lazy (F-303): created on first request, never at import.
"""

import html
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, redirect, url_for

bp = Blueprint("amir_day", __name__)

_db = None
_require = None
_unit = "medical"
_roles = ("maker", "checker")

IST = timezone(timedelta(hours=5, minutes=30))

# The two reports that make up the daily pair (D469).  One carries the supplier
# and what was supplied; the other carries the bill number and its details.
PAIR = (
    ("ITEMWISE", "Item-detail purchase report"),
    ("BILLWISE", "Bill-wise purchase report"),
)

REASONS = (
    ("ok",        "Theek hai"),
    ("short",     "Kam maal aaya"),
    ("nodeal",    "Deal nahi mili"),
    ("discount",  "Discount kam"),
    ("other",     "Aur koi baat"),
)
REASON_MAP = dict(REASONS)

# A disposition that is not "ok" raises a claim for Darpan to chase (D471).
CLAIM_REASONS = ("short", "nodeal", "discount", "other")

STEPS = (
    (1, "Punch"),
    (2, "Bill entry"),
    (3, "Export"),
    (4, "Check"),
    (5, "Bills"),
    (6, "Salt/naam"),
    (7, "Band"),
)

# Steps that decide whether a day is finished (correction 4).  Step 1 is a
# nudge, step 3 is an instruction, step 7 is the close itself.
GATE_STEPS = (2, 4, 5, 6)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _now():
    return datetime.now(IST)


def _today():
    return _now().strftime("%Y-%m-%d")


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _hhmm(s):
    """Show a stored timestamp as HH:MM, whatever shape it arrived in."""
    if not s:
        return ""
    s = str(s).replace("T", " ")
    return s[11:16] if len(s) >= 16 else s


def _esc(v):
    return html.escape("" if v is None else str(v))


def _rupees(paise):
    try:
        p = int(paise or 0)
    except (TypeError, ValueError):
        return ""
    return "{:,}".format(round(p / 100.0))


def _ensure(cx):
    """Additive, lazy, idempotent (F-303)."""
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_day(
        day        TEXT PRIMARY KEY,
        opened_at  TEXT,
        closed_at  TEXT,
        closed_by  TEXT
    )""")
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_step(
        day        TEXT NOT NULL,
        step       INTEGER NOT NULL,
        done_at    TEXT,
        by_user    TEXT,
        PRIMARY KEY(day, step)
    )""")
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_bill_disposition(
        supplier_norm TEXT NOT NULL,
        bill_no       TEXT NOT NULL,
        bill_date     TEXT NOT NULL,
        day           TEXT,
        reason        TEXT NOT NULL,
        by_user       TEXT,
        at            TEXT,
        PRIMARY KEY(supplier_norm, bill_no, bill_date)
    )""")
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_claim(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier      TEXT,
        supplier_norm TEXT,
        bill_no       TEXT,
        bill_date     TEXT,
        amount_p      INTEGER,
        reason        TEXT,
        raised_by     TEXT,
        raised_at     TEXT,
        state         TEXT NOT NULL DEFAULT 'open',
        contacted_note TEXT,
        settled_outcome TEXT,
        settled_at    TEXT,
        settled_by    TEXT,
        closed_auto   INTEGER NOT NULL DEFAULT 0
    )""")
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_claim_state ON amir_claim(state, raised_at)")
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_disp_day ON amir_bill_disposition(day)")


def _table_exists(cx, name):
    r = cx.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


# --------------------------------------------------------------------------
# what the server already knows
# --------------------------------------------------------------------------

def _export_state(cx, day):
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

    first = day[:8] + "01"
    for kind, label in PAIR:
        row = cx.execute(
            """SELECT md5, period_from, period_to, export_stamp, n_rows, received_at
                 FROM purchase_export
                WHERE type = ?
                  AND superseded_by IS NULL
                  AND substr(COALESCE(export_stamp, received_at), 1, 10) = ?
             ORDER BY COALESCE(export_stamp, received_at) DESC
                LIMIT 1""",
            (kind, day),
        ).fetchone()
        if row is None:
            out.append({"kind": kind, "label": label, "have": False,
                        "reason": "aaj ki nahi aayi"})
            continue
        d = dict(row)
        ok_from = (d.get("period_from") or "")[:10] <= first
        ok_to = (d.get("period_to") or "")[:10] >= day
        if not (ok_from and ok_to):
            out.append({"kind": kind, "label": label, "have": False,
                        "rows": d.get("n_rows"),
                        "at": _hhmm(d.get("export_stamp") or d.get("received_at")),
                        "reason": "tareekh galat hai -- 1 tareekh se aaj tak chahiye"})
            continue
        out.append({"kind": kind, "label": label, "have": True,
                    "rows": d.get("n_rows"),
                    "period": "%s se %s" % ((d.get("period_from") or "")[:10], (d.get("period_to") or "")[:10]),
                    "at": _hhmm(d.get("export_stamp") or d.get("received_at"))})
    return out


def _bills(cx, day):
    """Today's bills, and anything left undispositioned from earlier days.

    The list fills itself from the bill-wise export -- he types no bill number.
    Returns (today_rows, carry_rows).
    """
    if not (_table_exists(cx, "purchase_bill") and _table_exists(cx, "purchase_export")):
        return [], []

    cutoff = (_now() - timedelta(days=45)).strftime("%Y-%m-%d")
    rows = cx.execute(
        """SELECT b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p,
                  substr(COALESCE(e.export_stamp, e.received_at), 1, 10) AS seen_day
             FROM purchase_bill b
             JOIN purchase_export e ON e.md5 = b.bw_md5
        LEFT JOIN amir_bill_disposition d
                  ON d.supplier_norm = b.supplier_norm
                 AND d.bill_no       = b.bill_no
                 AND d.bill_date     = b.bill_date
            WHERE d.reason IS NULL
              AND e.type = 'BILLWISE'
              AND b.bill_date >= ?
         ORDER BY b.bill_date DESC, b.supplier""",
        (cutoff,),
    ).fetchall()

    today_rows, carry = [], []
    for r in rows:
        d = dict(r)
        (today_rows if d.get("seen_day") == day else carry).append(d)
    return today_rows, carry


def _work(cx, day):
    """Everything the day needs, gathered once."""
    exports = _export_state(cx, day)
    today_bills, carry_bills = _bills(cx, day)
    ticks = {
        int(r["step"]): dict(r)
        for r in cx.execute("SELECT step, done_at, by_user FROM amir_step WHERE day=?", (day,)).fetchall()
    }
    closed = cx.execute("SELECT closed_at, closed_by FROM amir_day WHERE day=?", (day,)).fetchone()

    done = {}
    done[1] = 1 in ticks
    done[2] = 2 in ticks
    done[3] = 3 in ticks
    done[4] = all(e["have"] for e in exports)          # proven, never ticked
    done[5] = (not today_bills) and (not carry_bills)
    done[6] = 6 in ticks
    done[7] = bool(closed and closed["closed_at"])
    return {
        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "ticks": ticks, "done": done,
        "closed": dict(closed) if closed else None,
    }


def _next_step(w):
    for n, _label in STEPS:
        if n == 7:
            continue
        if not w["done"].get(n):
            return n
    return 7


def _ready_to_close(w):
    return all(w["done"].get(n) for n in GATE_STEPS)


def _left(w):
    """Plain words for what is still missing -- used on the owner's card too."""
    out = []
    if not w["done"].get(2):
        out.append("bills not confirmed entered")
    missing = [e["label"] for e in w["exports"] if not e["have"]]
    if missing:
        out.append("%s not verified" % " and ".join(missing))
    n = len(w["today_bills"]) + len(w["carry_bills"])
    if n:
        out.append("%d bill%s still to tap" % (n, "" if n == 1 else "s"))
    if not w["done"].get(6):
        out.append("salt and name list not ticked")
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

_CSS = """
:root{--ink:#1b1b1b;--soft:#6b6b6b;--line:#e3e3e3;--ok:#137333;--warn:#8a6d00;
      --bad:#a50e0e;--bg:#fafafa;--accent:#12457a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:720px;margin:0 auto;padding:14px}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:17px;margin:0 0 10px}
p{margin:0 0 10px}
.sub{color:var(--soft);font-size:14px;margin:0 0 14px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
      padding:14px;margin:0 0 14px}
.steps{display:flex;gap:6px;margin:0 0 14px;flex-wrap:wrap}
.steps span{flex:1 1 auto;min-width:38px;text-align:center;font-size:12px;
            padding:6px 4px;border-radius:8px;border:1px solid var(--line);
            background:#fff;color:var(--soft)}
.steps .on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.steps .ok{background:#e7f3e9;border-color:#bfe0c6;color:var(--ok)}
.btn{display:block;width:100%;padding:14px 18px;font-size:17px;font-weight:600;
     border-radius:10px;border:1px solid var(--accent);background:var(--accent);
     color:#fff;text-align:center;text-decoration:none;cursor:pointer;margin:0 0 10px}
.btn.plain{background:#fff;color:var(--accent)}
.btn.quiet{background:#fff;color:var(--soft);border-color:var(--line);font-weight:400;font-size:15px}
.good{color:var(--ok)}
.bad{color:var(--bad)}
.warn{color:var(--warn)}
.line{padding:10px 0;border-bottom:1px solid var(--line)}
.line:last-child{border-bottom:0}
.big{font-size:17px;font-weight:600}
.bill{border:1px solid var(--line);border-radius:10px;padding:12px;margin:0 0 12px}
.bill .who{font-weight:600}
.bill .meta{color:var(--soft);font-size:14px;margin:2px 0 10px}
.opts label{display:block;padding:11px 10px;border:1px solid var(--line);
            border-radius:8px;margin:0 0 7px;font-size:16px}
.opts input{margin-right:9px;transform:scale(1.25)}
.note{background:#fff8e1;border:1px solid #f0e0a8;border-radius:10px;padding:12px;margin:0 0 14px}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--soft);font-weight:600}
.foot{color:var(--soft);font-size:13px;margin:16px 0 0;text-align:center}
"""


def _shell(title, body):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>%s"
            "</div></body></html>" % (_esc(title), _CSS, body))


def _banner(current, w):
    out = ["<div class=steps>"]
    for n, label in STEPS:
        cls = "on" if n == current else ("ok" if w["done"].get(n) else "")
        out.append("<span class='%s'>%d<br>%s</span>" % (cls, n, _esc(label)))
    out.append("</div>")
    return "".join(out)


def _page(step, w, title, body, subtitle=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    return _shell("Amir -- kaam", _banner(step, w) + head + body +
                  "<p class=foot>Step %d of 7</p>" % step)


def _denied():
    return _shell("Nahin khul saka",
                  "<div class=card><h2>Yeh page aapke liye nahin hai</h2>"
                  "<p>Apne login se kholiye, ya doctor sahab ko bataiye.</p>"
                  "</div>"), 403


def _go(step):
    return redirect(url_for("amir_day.step", n=step), code=303)


# --------------------------------------------------------------------------
# the steps
# --------------------------------------------------------------------------

def _step1(w):
    body = ("<div class=card><p class=big>Sabse pehle biometric punch kar lijiye.</p>"
            "<p>Punch ho gaya ho to neeche daba dijiye. Kaam yahin se shuru hoga.</p>"
            "<form method=post><input type=hidden name=tick value=1>"
            "<button class=btn name=go value=1>Punch ho gaya</button></form>"
            "<form method=post><input type=hidden name=tick value=1>"
            "<button class='btn quiet' name=go value=1>Punch nahi ho paya -- aage badhiye</button>"
            "</form></div>"
            "<p class=sub>Punch na hone se kaam nahi rukta. Doctor sahab ko dikh jata hai.</p>")
    return _page(1, w, "Punch", body)


def _step2(w):
    body = ("<div class=card><p class=big>Saare purchase aur purchase-return bill "
            "Marg mein daal dijiye -- bilkul jaisa bill par chhapa hai.</p>"
            "<p>Kuch theek mat kijiye, kuch round mat kijiye, kam maal aaya ho to bhi "
            "bill jaisa hai waisa hi daaliye. Kami agli screen par batayenge.</p>"
            "<form method=post><input type=hidden name=tick value=2>"
            "<button class=btn name=go value=2>Sab bill daal diye</button></form></div>")
    return _page(2, w, "Bill entry", body,
                 "Yahi ek niyam hai jis par baaki sab tika hai.")


def _step3(w):
    rows = "".join("<div class=line><span class=big>%d. %s</span><br>"
                   "<span class=sub>1 tareekh se aaj tak</span></div>"
                   % (i + 1, _esc(label)) for i, (_k, label) in enumerate(PAIR))
    body = ("<div class=card><h2>Do report nikaaliye</h2>%s</div>"
            "<div class=note>Counter par bikri shuru hone se pehle. Der ho jaye to "
            "bhi nikaal dijiye -- chhodiye mat.</div>"
            "<form method=post><input type=hidden name=tick value=3>"
            "<button class=btn name=go value=3>Dono report nikaal di -- jaanch kijiye</button>"
            "</form>" % rows)
    return _page(3, w, "Export", body)


def _step4(w):
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
                 "Aapse nahi poochha ja raha. Server ne khud file padhi hai.")


def _bill_block(i, b):
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    opts = "".join(
        "<label><input type=radio name='r_%s' value='%s' required>%s</label>"
        % (_esc(str(i)), _esc(code), _esc(label))
        for code, label in REASONS
    )
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>"
            "<input type=hidden name='k_%d' value='%s'>"
            "<div class=opts>%s</div></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               i, _esc(key), opts))


def _step5(w):
    bills = w["today_bills"]
    carry = w["carry_bills"]
    if not bills and not carry:
        return _page(5, w, "Bills", "<div class=card><p class=big good>"
                     "Koi bill baaki nahi hai.</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye"
                     "</button></form>")

    body = []
    if carry:
        body.append("<div class=note><b>Pichhla baaki</b> -- %d bill." % len(carry))
        body.append("</div>")
    body.append("<form method=post>")
    i = 0
    for b in carry + bills:
        body.append(_bill_block(i, b))
        i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<button class=btn name=go value=5>Save kijiye</button></form>")
    return _page(5, w, "Aaj ke bill", "".join(body),
                 "Har bill par ek jawab zaroori hai.")


def _step6(w):
    body = ("<div class=card><h2>Salt, naye item aur naam</h2>"
            "<p>Apni purani list kholiye, Marg mein theek kijiye, aur yahan tick "
            "kar dijiye. Agli export khud saabit kar degi.</p>"
            "<p><a class='btn plain' href='/finance/purchase/page/salts'>"
            "List kholiye</a></p></div>"
            "<div class=note>Aaj ke bill wale item hi zaroori hain. Poori purani list "
            "aaj khatam karna zaroori nahi.</div>"
            "<form method=post><input type=hidden name=tick value=6>"
            "<button class=btn name=go value=6>Aaj ke item theek kar diye</button>"
            "</form>")
    return _page(6, w, "Salt / naam", body)


def _step7(w):
    if w["done"].get(7):
        c = w["closed"] or {}
        body = ("<div class=card><h2 class=good>DIN BAND &#10003;</h2>"
                "<p>%s baje band kiya.</p></div>" % _esc(_hhmm(c.get("closed_at"))))
        body += _summary(w)
        return _page(7, w, "Din band", body)

    if not _ready_to_close(w):
        body = "<div class=card><h2>Abhi kuch baaki hai</h2><ul>"
        for item in _left(w):
            body += "<li>%s</li>" % _esc(item)
        body += ("</ul><p class=sub>Aaj ka din khula rehta hai. Jo ho gaya hai wo "
                 "bacha hua hai -- dobara nahi karna padega.</p></div>"
                 "<p><a class=btn href='/finance/amir'>Jahan chhoda tha wahan se</a></p>")
        return _page(7, w, "Abhi baaki", body)

    body = (_summary(w) +
            "<form method=post><button class=btn name=go value=7>Din band kijiye</button>"
            "</form>")
    return _page(7, w, "Din band karein?", body)


def _summary(w):
    got = [e["label"] for e in w["exports"] if e["have"]]
    rows = ["<div class=line>Dono report: <b>%s</b></div>"
            % ("mil gayi" if len(got) == len(PAIR) else "%d / %d" % (len(got), len(PAIR)))]
    rows.append("<div class=line>Bill baaki: <b>%d</b></div>"
                % (len(w["today_bills"]) + len(w["carry_bills"])))
    rows.append("<div class=line>Salt / naam: <b>%s</b></div>"
                % ("ho gaya" if w["done"].get(6) else "baaki"))
    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>" % "".join(rows)


_RENDER = {1: _step1, 2: _step2, 3: _step3, 4: _step4, 5: _step5, 6: _step6, 7: _step7}


# --------------------------------------------------------------------------
# writes
# --------------------------------------------------------------------------

def _tick(cx, day, step, user):
    cx.execute("INSERT OR IGNORE INTO amir_day(day, opened_at) VALUES(?,?)", (day, _stamp()))
    cx.execute("INSERT OR REPLACE INTO amir_step(day, step, done_at, by_user) VALUES(?,?,?,?)",
               (day, int(step), _stamp(), user))


def _save_bills(cx, day, user, form):
    """Write one disposition per bill, and raise a claim for each deficiency.

    Forced, not optional: a bill with no answer is simply not written, and the
    step stays unfinished, so the screen comes back with it still on the list.
    """
    try:
        n = int(form.get("n") or 0)
    except (TypeError, ValueError):
        n = 0
    written = 0
    for i in range(n):
        key = form.get("k_%d" % i) or ""
        reason = (form.get("r_%d" % i) or "").strip()
        if reason not in REASON_MAP or key.count("|") != 2:
            continue
        supplier_norm, bill_no, bill_date = key.split("|")
        cx.execute(
            """INSERT OR REPLACE INTO amir_bill_disposition
               (supplier_norm, bill_no, bill_date, day, reason, by_user, at)
               VALUES(?,?,?,?,?,?,?)""",
            (supplier_norm, bill_no, bill_date, day, reason, user, _stamp()),
        )
        written += 1
        if reason in CLAIM_REASONS:
            already = cx.execute(
                """SELECT 1 FROM amir_claim
                    WHERE supplier_norm=? AND bill_no=? AND bill_date=?
                      AND state <> 'settled'""",
                (supplier_norm, bill_no, bill_date),
            ).fetchone()
            if not already:
                b = cx.execute(
                    """SELECT supplier, amount_p FROM purchase_bill
                        WHERE supplier_norm=? AND bill_no=? AND bill_date=?""",
                    (supplier_norm, bill_no, bill_date),
                ).fetchone() if _table_exists(cx, "purchase_bill") else None
                cx.execute(
                    """INSERT INTO amir_claim
                       (supplier, supplier_norm, bill_no, bill_date, amount_p,
                        reason, raised_by, raised_at, state)
                       VALUES(?,?,?,?,?,?,?,?,'open')""",
                    ((b["supplier"] if b else supplier_norm), supplier_norm, bill_no,
                     bill_date, (b["amount_p"] if b else None), reason, user, _stamp()),
                )
    return written


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------

@bp.route("/finance/amir")
def home():
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    _ensure(cx)
    w = _work(cx, _today())
    return _go(_next_step(w))


@bp.route("/finance/amir/step/<int:n>", methods=["GET", "POST"])
def step(n):
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    if n < 1 or n > 7:
        return _go(1)

    cx = _db()
    _ensure(cx)
    day = _today()
    user = (u or {}).get("username") or (u or {}).get("user") or ""

    if request.method == "POST":
        if n == 5:
            _save_bills(cx, day, user, request.form)
        elif n == 7:
            w = _work(cx, day)
            if _ready_to_close(w):
                cx.execute("INSERT OR IGNORE INTO amir_day(day, opened_at) VALUES(?,?)",
                           (day, _stamp()))
                cx.execute("UPDATE amir_day SET closed_at=?, closed_by=? WHERE day=?",
                           (_stamp(), user, day))
                _tick(cx, day, 7, user)
        else:
            tick = request.form.get("tick")
            if tick and tick.isdigit() and int(tick) == n:
                _tick(cx, day, n, user)
        cx.commit()
        w = _work(cx, day)
        if n == 7 and w["done"].get(7):
            return _go(7)
        nxt = _next_step(w)
        return _go(nxt if nxt >= n else n + 1 if n < 7 else 7)

    w = _work(cx, day)
    return _RENDER[n](w)


@bp.route("/finance/amir/day")
def owner_day():
    """The owner's view of the same day, in English."""
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    _ensure(cx)
    day = request.args.get("d") or _today()
    w = _work(cx, day)

    rows = []
    for e in w["exports"]:
        rows.append("<tr><td>%s</td><td class='%s'>%s</td><td>%s</td><td>%s</td></tr>"
                    % (_esc(e["label"]), "good" if e["have"] else "bad",
                       "verified" if e["have"] else "not verified",
                       _esc(e.get("rows", "")), _esc(e.get("at", "") or e.get("reason", ""))))
    left = _left(w)
    state = ("CLOSED at %s" % _hhmm((w["closed"] or {}).get("closed_at"))) if w["done"].get(7) \
        else ("OPEN -- " + "; ".join(left) if left else "OPEN -- ready to close")

    open_claims = cx.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(amount_p),0) AS v FROM amir_claim WHERE state <> 'settled'"
    ).fetchone()
    oldest = cx.execute(
        "SELECT MIN(raised_at) AS o FROM amir_claim WHERE state <> 'settled'"
    ).fetchone()

    body = ("<div class=card><h2>Amir -- %s</h2><p class=big>%s</p></div>"
            "<div class=card><h2>The daily pair</h2><div class=tscroll><table>"
            "<tr><th>report</th><th>state</th><th>rows</th><th>when</th></tr>%s"
            "</table></div></div>"
            "<div class=card><h2>Bills</h2>"
            "<div class=line>Today, still to tap: <b>%d</b></div>"
            "<div class=line>Carried from earlier days: <b>%d</b></div></div>"
            "<div class=card><h2>Claims for Darpan</h2>"
            "<div class=line>Open: <b>%d</b>, worth &#8377;%s</div>"
            "<div class=line>Oldest raised: <b>%s</b></div></div>"
            % (_esc(day), _esc(state), "".join(rows),
               len(w["today_bills"]), len(w["carry_bills"]),
               (open_claims["n"] if open_claims else 0),
               _rupees(open_claims["v"] if open_claims else 0),
               _esc((oldest["o"] or "-") if oldest else "-")))
    return _shell("Amir's day", body)


@bp.route("/finance/amir/api/healthz")
def healthz():
    return {"ok": True, "kit": "S241_AMIR_DAY", "at": _stamp()}


def init(app, db_getter, require_fn, unit="medical", roles=("maker", "checker"), url_prefix=""):
    global _db, _require, _unit, _roles
    _db, _require, _unit, _roles = db_getter, require_fn, unit, tuple(roles)
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp
