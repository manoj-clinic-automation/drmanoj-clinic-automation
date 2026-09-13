#!/usr/bin/env python3
"""S246_AMIR_LIST_REOPEN -- what the bill list holds, and a day that can be opened again.

Built on the LIVE S245_AMIR_BILLTAP file (79eb701f...), which is the one-tap bill screen
as installed on 13-Sep.  This kit adds:

  * the settlement line and the standing flag list (owner, 13-Sep), and the grouping fix
    that stops one bill being listed once per export it rides in;
  * a way back into the flow after DIN BAND -- every step in the 1-to-7 banner is a link,
    the closed screen offers the steps by name, and the day can be opened again.

Every replacement is an exact, unique, asserted swap.  If the source file is not the live
one, or any anchor has moved, this refuses and writes nothing.
"""
import hashlib
import io
import os
import sys

SRC_MD5 = "79eb701f2df14e58c77e130a77b972ba"      # live /root/finance/amir_day.py, S245

_BLOB = r'''
###EDIT docstring
###OLD
  * `required` is gone from the radios ON PURPOSE: a required control inside a closed
    <details> cannot be focused, and the browser then refuses the whole submit without
    saying why.  The forcing was never the browser's job -- an unanswered bill is
    simply not written and comes straight back on the list, which is stronger.
"""
###NEW
  * `required` is gone from the radios ON PURPOSE: a required control inside a closed
    <details> cannot be focused, and the browser then refuses the whole submit without
    saying why.  The forcing was never the browser's job -- an unanswered bill is
    simply not written and comes straight back on the list, which is stronger.

S246_AMIR_LIST_REOPEN (owner rulings 13-Sep-2026):
  * WHAT THE LIST HOLDS: purchase bills dated on or after BILLS_FROM only -- everything
    before that is settled and is never shown again -- and a bill he marked NOT ok STAYS
    on the list until he marks it Theek hai.  It sits in its own band, never holds the
    day open (a credit note can take a fortnight), and marking it Theek hai settles the
    claim Darpan was chasing.
  * A bill rides in every cumulative 1st-to-date export after the one that first carried
    it, so the rows are grouped by the bill itself.  Without that, the moment there is
    more than one export a single unanswered bill is listed -- and COUNTED, in the gate
    that decides whether a day can close -- once per export it appears in.
  * DIN BAND IS NOT A DEAD END.  Every step in the banner is a link, the closed screen
    names the places he may want and says when a new bill has arrived since, and the day
    can be opened again -- recorded, never silently.
"""
###EDIT bills_from
###OLD
# How often the step 4 screen re-checks itself while a report is in transit.
EXPORT_POLL_SEC = 20
###NEW
# How often the step 4 screen re-checks itself while a report is in transit.
EXPORT_POLL_SEC = 20

# S246: everything before this date is settled and is never put in front of him again
# (owner, 13-Sep-2026).  Move it the next time a period is settled; env AMIR_BILLS_FROM.
BILLS_FROM = (os.environ.get("AMIR_BILLS_FROM") or "").strip() or "2026-09-01"
if not re.match(r"^\d{4}-\d{2}-\d{2}$", BILLS_FROM):
    BILLS_FROM = "2026-09-01"
###EDIT bills
###OLD
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
                  """ + _export_day_sql("e.") + """ AS seen_day
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
###NEW
def _bills(cx, day):
    """The purchase bills that still want an answer.  (S246)

    Three lists, and only the first two hold the day open:

        today    first seen in an export OF TODAY, no answer yet
        carry    first seen on an earlier day, still no answer   -- pichhla baaki
        flagged  answered NOT ok and not yet put right: it STAYS until he marks it
                 Theek hai (owner, 13-Sep-2026), and it never holds a day open --
                 a supplier's credit note can take a fortnight.

    Bills dated before BILLS_FROM are settled and are never shown.

    The rows are grouped by the bill itself.  A bill rides in every cumulative
    1st-to-date export after the one that first carried it, so without the grouping a
    single unanswered bill is listed once per export it appears in -- and counted that
    many times in the gate that decides whether the day can close.  `seen_day` is the
    EARLIEST export that carried it, which is what makes pichhla baaki mean anything.

    The list still fills itself from the bill-wise export -- he types no bill number.
    """
    if not (_table_exists(cx, "purchase_bill") and _table_exists(cx, "purchase_export")):
        return [], [], []

    rows = cx.execute(
        """SELECT b.supplier_norm AS supplier_norm, b.bill_no AS bill_no,
                  b.bill_date AS bill_date, d.reason AS reason,
                  MAX(b.supplier)  AS supplier,
                  MAX(b.amount_p)  AS amount_p,
                  MAX(d.at)        AS flagged_at,
                  MIN(""" + _export_day_sql("e.") + """) AS seen_day
             FROM purchase_bill b
             JOIN purchase_export e ON e.md5 = b.bw_md5
        LEFT JOIN amir_bill_disposition d
                  ON d.supplier_norm = b.supplier_norm
                 AND d.bill_no       = b.bill_no
                 AND d.bill_date     = b.bill_date
            WHERE (d.reason IS NULL OR d.reason <> 'ok')
              AND e.type = 'BILLWISE'
              AND b.bill_date >= ?
         GROUP BY b.supplier_norm, b.bill_no, b.bill_date, d.reason""",
        (BILLS_FROM,),
    ).fetchall()

    today_rows, carry, flagged = [], [], []
    for r in rows:
        d = dict(r)
        if d.get("reason"):
            flagged.append(d)
        elif d.get("seen_day") == day:
            today_rows.append(d)
        else:
            carry.append(d)
    for lst in (today_rows, carry, flagged):
        lst.sort(key=lambda x: ((x.get("bill_date") or ""), (x.get("supplier") or "")),
                 reverse=True)
    return today_rows, carry, flagged
###EDIT work_bills
###OLD
    exports = _export_state(cx, day, wait_since)
    today_bills, carry_bills = _bills(cx, day)
###NEW
    exports = _export_state(cx, day, wait_since)
    today_bills, carry_bills, flagged_bills = _bills(cx, day)
###EDIT work_closed
###OLD
    closed = cx.execute("SELECT closed_at, closed_by FROM amir_day WHERE day=?", (day,)).fetchone()
###NEW
    closed = cx.execute("SELECT closed_at, closed_by, reopened_at, reopened_by "
                        "FROM amir_day WHERE day=?", (day,)).fetchone()
###EDIT work_return
###OLD
        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "ticks": ticks, "done": done,
###NEW
        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "flagged_bills": flagged_bills,
        "ticks": ticks, "done": done,
###EDIT ensure_reopen
###OLD
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_day(
        day        TEXT PRIMARY KEY,
        opened_at  TEXT,
        closed_at  TEXT,
        closed_by  TEXT
    )""")
###NEW
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_day(
        day        TEXT PRIMARY KEY,
        opened_at  TEXT,
        closed_at  TEXT,
        closed_by  TEXT
    )""")
    # S246: a day that was closed can be opened again, and the record says so rather
    # than pretending it was never closed.  Additive, lazy, idempotent (F-303).
    _cols = {r[1] for r in cx.execute("PRAGMA table_info(amir_day)").fetchall()}
    for _c in ("reopened_at", "reopened_by"):
        if _c not in _cols:
            cx.execute("ALTER TABLE amir_day ADD COLUMN %s TEXT" % _c)
###EDIT css_steps
###OLD
.steps span{flex:1 1 auto;min-width:38px;text-align:center;font-size:12px;
            padding:6px 4px;border-radius:8px;border:1px solid var(--line);
            background:#fff;color:var(--soft)}
###NEW
.steps span,.steps a{flex:1 1 auto;min-width:38px;text-align:center;font-size:12px;
            padding:6px 4px;border-radius:8px;border:1px solid var(--line);
            background:#fff;color:var(--soft);text-decoration:none;display:block}
###EDIT css_was
###OLD
.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}
###NEW
.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}
.bill .was{background:#fff8e1;border:1px solid #f0e0a8;border-radius:8px;
           padding:9px 11px;margin:0 0 10px;font-size:14px;color:var(--warn)}
###EDIT banner
###OLD
        out.append("<span class='%s'>%d<br>%s</span>" % (cls, n, _esc(label)))
###NEW
        # S246: every step is a link.  DIN BAND used to be a dead end -- there was no
        # way back into any step once the day was closed.
        out.append("<a class='%s' href='/finance/amir/step/%d'>%d<br>%s</a>"
                   % (cls, n, n, _esc(label)))
###EDIT bill_block
###OLD
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    ok_label = REASON_MAP.get("ok", "Theek hai")
    why = "".join(
        "<label><input type=radio name='r_%d' value='%s'>%s</label>"
        % (i, _esc(code), _esc(label))
        for code, label in REASONS if code != "ok"
    )
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>"
            "<input type=hidden name='k_%d' value='%s'>"
            "<label class=tap><input type=radio name='r_%d' value='ok'>%s</label>"
            "<details class=notok><summary>Theek nahi</summary>"
            "<div class=why>%s</div></details></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               i, _esc(key), i, _esc(ok_label), why))
###NEW
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    ok_label = REASON_MAP.get("ok", "Theek hai")
    why = "".join(
        "<label><input type=radio name='r_%d' value='%s'>%s</label>"
        % (i, _esc(code), _esc(label))
        for code, label in REASONS if code != "ok"
    )
    was = ""
    if b.get("reason"):
        # S246: a bill he already flagged carries what he wrote and when.  Theek hai
        # is how a flag is cleared -- nothing else on this screen clears one.
        when = _dm_hm(b.get("flagged_at"))
        was = ("<div class=was>Aapne likha tha: <b>%s</b>%s</div>"
               % (_esc(REASON_MAP.get(b["reason"], b["reason"])),
                  (" &middot; %s" % _esc(when)) if when else ""))
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s"
            "<input type=hidden name='k_%d' value='%s'>"
            "<label class=tap><input type=radio name='r_%d' value='ok'>%s</label>"
            "<details class=notok><summary>Theek nahi</summary>"
            "<div class=why>%s</div></details></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               was, i, _esc(key), i, _esc(ok_label), why))
###EDIT step5
###OLD
def _step5(w):
    bills = w["today_bills"]
    carry = w["carry_bills"]
    if not bills and not carry:
        return _page(5, w, "Bills", _export_band(w) + "<div class=card><p class=big good>"
                     "Koi bill baaki nahi hai.</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye"
                     "</button></form>")

    body = [_export_band(w)]
    if carry:
        body.append("<div class=note><b>Pichhla baaki</b> -- %d bill." % len(carry))
        body.append("</div>")
    body.append("<form method=post>")
    i = 0
    for b in carry + bills:
        body.append(_bill_block(i, b))
        i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<div class=savebar><button class=btn name=go value=5>Save kijiye</button>"
                "</div></form>")
    n = len(carry) + len(bills)
    return _page(5, w, "Aaj ke bill", "".join(body),
                 "%d bill. Har bill par ek tap. Kuch gadbad ho to hi "
                 "\"Theek nahi\" kholiye." % n)
###NEW
def _step5(w):
    bills = w["today_bills"]
    carry = w["carry_bills"]
    flagged = w.get("flagged_bills") or []
    if not bills and not carry and not flagged:
        return _page(5, w, "Bills", _export_band(w) + "<div class=card><p class=big good>"
                     "Koi bill baaki nahi hai.</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye"
                     "</button></form>")

    body = [_export_band(w)]
    if carry:
        body.append("<div class=note><b>Pichhla baaki</b> -- %d bill.</div>" % len(carry))
    body.append("<form method=post>")
    i = 0
    for b in carry + bills:
        body.append(_bill_block(i, b))
        i += 1
    if flagged:
        body.append("<div class=card><h2>Flag kiye hue bill -- %d</h2>"
                    "<p class=sub>Yeh tab tak yahin rahenge jab tak theek na ho jayen. "
                    "Theek ho jaye to <b>Theek hai</b> daba dijiye.</p></div>" % len(flagged))
        for b in flagged:
            body.append(_bill_block(i, b))
            i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<div class=savebar><button class=btn name=go value=5>Save kijiye</button>")
    if not bills and not carry:
        body.append("<button class='btn quiet' name=go value=5>Aage badhiye</button>")
    body.append("</div></form>")
    n = len(carry) + len(bills)
    if n:
        sub = ("%d bill. Har bill par ek tap. Kuch gadbad ho to hi "
               "'Theek nahi' kholiye." % n)
    else:
        sub = "Aaj ke sab bill ho gaye. Neeche sirf flag kiye hue bill hain."
    return _page(5, w, "Aaj ke bill", "".join(body), sub)
###EDIT save_bills_settle
###OLD
        written += 1
        if reason in CLAIM_REASONS:
###NEW
        written += 1
        if reason == "ok":
            # S246: Theek hai on a bill he had flagged is the correction being
            # confirmed.  Close what Darpan was chasing rather than leave it open
            # against a bill that is now right -- named, timed and attributed.
            cx.execute(
                """UPDATE amir_claim
                      SET state = 'settled', settled_outcome = 'amir_ok',
                          settled_at = ?, settled_by = ?
                    WHERE supplier_norm = ? AND bill_no = ? AND bill_date = ?
                      AND state <> 'settled'""",
                (_stamp(), user, supplier_norm, bill_no, bill_date),
            )
        if reason in CLAIM_REASONS:
###EDIT step7_closed
###OLD
def _step7(w):
    if w["done"].get(7):
        c = w["closed"] or {}
        body = ("<div class=card><h2 class=good>DIN BAND &#10003;</h2>"
                "<p>%s baje band kiya.</p></div>" % _esc(_hhmm(c.get("closed_at"))))
        body += _summary(w)
        return _page(7, w, "Din band", body)
###NEW
def _step7(w):
    if w["done"].get(7):
        c = w["closed"] or {}
        body = ("<div class=card><h2 class=good>DIN BAND &#10003;</h2>"
                "<p>%s baje band kiya.</p>" % _esc(_hhmm(c.get("closed_at"))))
        if c.get("reopened_at"):
            body += ("<p class=sub>Isse pehle %s baje dobara khola gaya tha.</p>"
                     % _esc(_hhmm(c.get("reopened_at"))))
        body += "</div>"
        waiting = len(w["today_bills"]) + len(w["carry_bills"])
        if waiting:
            body += ("<div class=note><b>%d naya bill aa gaya hai.</b> "
                     "<a href='/finance/amir/step/5'>Kholiye</a></div>" % waiting)
        body += _summary(w)
        # S246: DIN BAND is not a dead end.  The banner above is all links, and these
        # are the three places he actually comes back for.
        nflag = len(w.get("flagged_bills") or [])
        body += ("<div class=card><h2>Kuch aur karna hai?</h2>"
                 "<p><a class='btn plain' href='/finance/amir/step/5'>Bill dekhiye"
                 + ((" -- %d flag" % nflag) if nflag else "") + "</a></p>"
                 "<p><a class='btn plain' href='/finance/amir/step/6'>Salt aur naam</a></p>"
                 "<p><a class='btn plain' href='/finance/amir/step/4'>Report ki jaanch</a></p>"
                 "</div>"
                 "<form method=post><input type=hidden name=reopen value=1>"
                 "<button class='btn quiet' name=go value=7>Din phir se kholiye</button>"
                 "</form>")
        return _page(7, w, "Din band", body)
###EDIT summary_flag
###OLD
    rows.append("<div class=line>Bill baaki: <b>%d</b></div>"
                % (len(w["today_bills"]) + len(w["carry_bills"])))
###NEW
    rows.append("<div class=line>Bill baaki: <b>%d</b></div>"
                % (len(w["today_bills"]) + len(w["carry_bills"])))
    nflag = len(w.get("flagged_bills") or [])
    if nflag:
        rows.append("<div class=line>Flag kiye hue bill: <b>%d</b> "
                    "<span class=sub>(din band karne se nahi rukte)</span></div>" % nflag)
###EDIT route_reopen
###OLD
            w = _work(cx, day)
            if _ready_to_close(w):
###NEW
            w = _work(cx, day)
            if w["done"].get(7) and request.form.get("reopen"):
                # S246: a day closed too early is opened again -- recorded, never
                # silently.  Everything already done stays done; only the close is
                # undone, and the jump takes him to whatever is now unfinished.
                cx.execute("UPDATE amir_day SET closed_at=NULL, closed_by=NULL, "
                           "reopened_at=?, reopened_by=? WHERE day=?",
                           (_stamp(), user, day))
                cx.execute("DELETE FROM amir_step WHERE day=? AND step=7", (day,))
                cx.commit()
                return _go(_next_step(_work(cx, day)))
            if _ready_to_close(w):
###EDIT owner_state
###OLD
    state = ("CLOSED at %s" % _hhmm((w["closed"] or {}).get("closed_at"))) if w["done"].get(7) \
        else ("OPEN -- " + "; ".join(left) if left else "OPEN -- ready to close")
###NEW
    state = ("CLOSED at %s" % _hhmm((w["closed"] or {}).get("closed_at"))) if w["done"].get(7) \
        else ("OPEN -- " + "; ".join(left) if left else "OPEN -- ready to close")
    if (w["closed"] or {}).get("reopened_at"):                  # S246
        state += " (reopened %s by %s)" % (_hhmm(w["closed"]["reopened_at"]),
                                           w["closed"].get("reopened_by") or "?")
###EDIT visit_json
###OLD
        "closed_at": (w["closed"] or {}).get("closed_at") if closed else None,
###NEW
        "closed_at": (w["closed"] or {}).get("closed_at") if closed else None,
        "reopened_at": (w["closed"] or {}).get("reopened_at"),
        "reopened_by": (w["closed"] or {}).get("reopened_by"),
###EDIT visit_head
###OLD
    head = "%s -- %s%s" % (v["day"], v["state"], (" at %s" % _hhmm(v["closed_at"])) if v.get("closed_at") else "")
###NEW
    head = "%s -- %s%s%s" % (v["day"], v["state"],
                             (" at %s" % _hhmm(v["closed_at"])) if v.get("closed_at") else "",
                             (" (reopened %s)" % _hhmm(v["reopened_at"])) if v.get("reopened_at") else "")
###EDIT healthz
###OLD
    return {"ok": True, "kit": "S244_AMIR_PROCESSING", "at": _stamp()}
###NEW
    return {"ok": True, "kit": "S246_AMIR_LIST_REOPEN", "at": _stamp()}
'''


def _parse(blob):
    edits = []
    name = old = None
    mode = None
    buf = []
    for line in blob.split("\n"):
        if line.startswith("###EDIT "):
            if name is not None and mode == "new":
                edits.append((name, old, "\n".join(buf)))
            name = line[len("###EDIT "):].strip()
            old = None
            mode = None
            buf = []
        elif line == "###OLD":
            mode = "old"
            buf = []
        elif line == "###NEW":
            old = "\n".join(buf)
            mode = "new"
            buf = []
        elif mode:
            buf.append(line)
    if name is not None and mode == "new":
        edits.append((name, old, "\n".join(buf)))
    return edits


EDITS = _parse(_BLOB)


def _read(path):
    return io.open(path, "r", encoding="utf-8", newline="").read()


def build(src):
    """The live S245 file in, the S246 file out.  Refuses rather than guesses."""
    if "\r\n" in src:
        raise SystemExit("REFUSED: source has CRLF (F-294)")
    if hashlib.md5(src.encode("utf-8")).hexdigest() != SRC_MD5:
        raise SystemExit("REFUSED: source is not the live S245 amir_day.py (%s expected)" % SRC_MD5)
    if len(EDITS) != 20:
        raise SystemExit("REFUSED: parsed %d edits, expected 20" % len(EDITS))
    text = src
    for name, old, new in EDITS:
        if not old.strip() or not new.strip():
            raise SystemExit("REFUSED: edit %r parsed empty" % name)
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
