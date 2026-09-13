#!/usr/bin/env python3
"""S245_AMIR_BILLTAP -- step 5: one tap per bill, the reasons hidden until they are needed.

Every replacement is an exact, unique, asserted string swap against the S244 live file.
If the source is not that file, or any anchor has moved, this refuses and writes nothing.
"""
import hashlib
import io
import os
import sys

SRC_MD5 = "aad400fa9c4b7804229c9f175c86533b"          # live /root/finance/amir_day.py, S244

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


# ---------------------------------------------------------------- 1. docstring
edit(
    "docstring",
    '''  * Step 3 prints the two dates he must type into Marg, so the TO date cannot be
    yesterday's by habit.
"""''',
    '''  * Step 3 prints the two dates he must type into Marg, so the TO date cannot be
    yesterday's by habit.

S245_AMIR_BILLTAP (owner ruling 13-Sep-2026):
  * Step 5 was five radio buttons on every bill, all open at once -- forty choices on
    one phone screen for a normal day.  It is now ONE tap per bill: "Theek hai", or
    "Theek nahi", and the four reasons appear only when he says it is not right.
  * The reasons live in a <details>, so this is still a page with no JavaScript, and
    the answer is still one radio group per bill -- the form the server reads is
    unchanged, byte for byte.
  * `required` is gone from the radios ON PURPOSE: a required control inside a closed
    <details> cannot be focused, and the browser then refuses the whole submit without
    saying why.  The forcing was never the browser's job -- an unanswered bill is
    simply not written and comes straight back on the list, which is stronger.
  * WHAT THE LIST HOLDS, also his ruling of the same day: purchase bills dated on or
    after BILLS_FROM only -- everything before that is settled and is never shown --
    and a bill he marked NOT ok STAYS on the list until he marks it Theek hai.  It sits
    in its own band, never holds the day open, and marking it Theek hai settles the
    claim Darpan was chasing.
  * A bill rides in every cumulative 1st-to-date export after the one that first
    carried it, so the rows are grouped by the bill itself.  Without that, the moment
    there is more than one export a single unanswered bill is listed once per export.
"""''',
)

# ---------------------------------------------------------------- 2. CSS
edit(
    "css",
    '''.opts label{display:block;padding:11px 10px;border:1px solid var(--line);
            border-radius:8px;margin:0 0 7px;font-size:16px}
.opts input{margin-right:9px;transform:scale(1.25)}''',
    '''.opts label{display:block;padding:11px 10px;border:1px solid var(--line);
            border-radius:8px;margin:0 0 7px;font-size:16px}
.opts input{margin-right:9px;transform:scale(1.25)}
/* S245: one tap per bill; the reasons stay shut until he says it is not right */
.bill .tap{display:block;padding:15px 13px;border:1px solid #bfe0c6;border-radius:10px;
           background:#f2f9f4;color:var(--ok);font-size:17px;font-weight:600;margin:0 0 8px}
.bill .tap input{margin-right:11px;transform:scale(1.35);vertical-align:-2px}
.bill details.notok{border:1px solid var(--line);border-radius:10px;background:#fff}
.bill details.notok summary{padding:15px 13px;font-size:17px;font-weight:600;
            color:var(--bad);cursor:pointer;list-style:none}
.bill details.notok summary::-webkit-details-marker{display:none}
.bill details.notok summary::after{content:" \\25BE";color:var(--soft);float:right}
.bill details.notok[open] summary{border-bottom:1px solid var(--line)}
.bill details.notok[open] summary::after{content:" \\25B4"}
.why{padding:4px 13px 13px}
.why label{display:block;padding:13px 11px;border:1px solid var(--line);border-radius:8px;
           margin:9px 0 0;font-size:16px}
.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}
.bill:has(input:checked){border-color:var(--ok);box-shadow:0 0 0 1px var(--ok) inset}
.bill:has(details input:checked){border-color:var(--bad);box-shadow:0 0 0 1px var(--bad) inset}
.savebar{position:sticky;bottom:0;background:var(--bg);padding:10px 0 4px;
         border-top:1px solid var(--line);margin:14px 0 0}
.savebar .btn{margin:0}''',
)

# ---------------------------------------------------------------- 4. the floor date
edit(
    "bills_from",
    '''# How often the step 4 screen re-checks itself while a report is in transit.
EXPORT_POLL_SEC = 20''',
    '''# How often the step 4 screen re-checks itself while a report is in transit.
EXPORT_POLL_SEC = 20

# S245: everything before this date is settled and is never put in front of him again
# (owner, 13-Sep-2026).  Move it the next time a period is settled; env AMIR_BILLS_FROM.
BILLS_FROM = (os.environ.get("AMIR_BILLS_FROM") or "").strip() or "2026-09-01"
if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", BILLS_FROM):
    BILLS_FROM = "2026-09-01"''',
)

# ---------------------------------------------------------------- 5. _bills
edit(
    "bills",
    '''def _bills(cx, day):
    """Today\'s bills, and anything left undispositioned from earlier days.

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
              AND e.type = \'BILLWISE\'
              AND b.bill_date >= ?
         ORDER BY b.bill_date DESC, b.supplier""",
        (cutoff,),
    ).fetchall()

    today_rows, carry = [], []
    for r in rows:
        d = dict(r)
        (today_rows if d.get("seen_day") == day else carry).append(d)
    return today_rows, carry''',
    '''def _bills(cx, day):
    """The purchase bills that still want an answer.  (S245)

    Three lists, and only the first two hold the day open:

        today    first seen in an export OF TODAY, no answer yet
        carry    first seen on an earlier day, still no answer   -- pichhla baaki
        flagged  answered NOT ok and not yet put right: it STAYS until he marks it
                 Theek hai (owner, 13-Sep-2026), and it never holds a day open --
                 a supplier\'s credit note can take a fortnight.

    Bills dated before BILLS_FROM are settled and are never shown.

    The rows are grouped by the bill itself.  A bill rides in every cumulative
    1st-to-date export after the one that first carried it, so without the grouping a
    single unanswered bill is listed once per export it appears in.  `seen_day` is the
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
            WHERE (d.reason IS NULL OR d.reason <> \'ok\')
              AND e.type = \'BILLWISE\'
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
    return today_rows, carry, flagged''',
)

# ---------------------------------------------------------------- 6. _work
edit(
    "work_bills",
    '''    exports = _export_state(cx, day, wait_since)
    today_bills, carry_bills = _bills(cx, day)''',
    '''    exports = _export_state(cx, day, wait_since)
    today_bills, carry_bills, flagged_bills = _bills(cx, day)''',
)

edit(
    "work_return_bills",
    '''        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "ticks": ticks, "done": done,''',
    '''        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "flagged_bills": flagged_bills,
        "ticks": ticks, "done": done,''',
)

# ---------------------------------------------------------------- 7. _bill_block
edit(
    "bill_block",
    '''def _bill_block(i, b):
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    opts = "".join(
        "<label><input type=radio name=\'r_%s\' value=\'%s\' required>%s</label>"
        % (_esc(str(i)), _esc(code), _esc(label))
        for code, label in REASONS
    )
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>"
            "<input type=hidden name=\'k_%d\' value=\'%s\'>"
            "<div class=opts>%s</div></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               i, _esc(key), opts))''',
    '''def _bill_block(i, b):
    """One bill, one tap.  (S245)

    What he sees is two lines: *Theek hai* and *Theek nahi*.  The four reasons sit
    inside the second one and open only when he taps it -- a <details>, so the page
    still carries no JavaScript.  All five are the same radio group, so picking a
    reason un-picks *theek hai* by itself and the form the server reads is exactly
    the one it read before.

    A bill he has already flagged carries what he wrote and when, and the same two
    taps -- Theek hai is how a flag is cleared.
    """
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    ok_label = REASON_MAP.get("ok", "Theek hai")
    why = "".join(
        "<label><input type=radio name=\'r_%d\' value=\'%s\'>%s</label>"
        % (i, _esc(code), _esc(label))
        for code, label in REASONS if code != "ok"
    )
    was = ""
    if b.get("reason"):
        when = _dm_hm(b.get("flagged_at"))
        was = ("<div class=was>Aapne likha tha: <b>%s</b>%s</div>"
               % (_esc(REASON_MAP.get(b["reason"], b["reason"])),
                  (" &middot; %s" % _esc(when)) if when else ""))
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s"
            "<input type=hidden name=\'k_%d\' value=\'%s\'>"
            "<label class=tap><input type=radio name=\'r_%d\' value=\'ok\'>%s</label>"
            "<details class=notok><summary>Theek nahi</summary>"
            "<div class=why>%s</div></details></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               was, i, _esc(key), i, _esc(ok_label), why))''',
)

# ---------------------------------------------------------------- 8. _step5
edit(
    "step5",
    '''def _step5(w):
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
    body.append("<input type=hidden name=n value=\'%d\'>" % i)
    body.append("<button class=btn name=go value=5>Save kijiye</button></form>")
    return _page(5, w, "Aaj ke bill", "".join(body),
                 "Har bill par ek jawab zaroori hai.")''',
    '''def _step5(w):
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
    body.append("<input type=hidden name=n value=\'%d\'>" % i)
    body.append("<div class=savebar><button class=btn name=go value=5>Save kijiye</button>")
    if not bills and not carry:
        body.append("<button class=\'btn quiet\' name=go value=5>Aage badhiye</button>")
    body.append("</div></form>")
    n = len(carry) + len(bills)
    if n:
        sub = ("%d bill. Har bill par ek tap. Kuch gadbad ho to hi "
               "'Theek nahi' kholiye." % n)
    else:
        sub = "Aaj ke sab bill ho gaye. Neeche sirf flag kiye hue bill hain."
    return _page(5, w, "Aaj ke bill", "".join(body), sub)''',
)

# ---------------------------------------------------------------- 9. _save_bills
edit(
    "save_bills_settle",
    '''        written += 1
        if reason in CLAIM_REASONS:''',
    '''        written += 1
        if reason == "ok":
            # S245: Theek hai on a bill he had flagged is the correction being
            # confirmed.  Close what Darpan was chasing rather than leave it open
            # against a bill that is now right -- named, timed and attributed.
            cx.execute(
                """UPDATE amir_claim
                      SET state = \'settled\', settled_outcome = \'amir_ok\',
                          settled_at = ?, settled_by = ?
                    WHERE supplier_norm = ? AND bill_no = ? AND bill_date = ?
                      AND state <> \'settled\'""",
                (_stamp(), user, supplier_norm, bill_no, bill_date),
            )
        if reason in CLAIM_REASONS:''',
)

# ---------------------------------------------------------------- 10. _summary
edit(
    "summary",
    '''    rows.append("<div class=line>Bill baaki: <b>%d</b></div>"
                % (len(w["today_bills"]) + len(w["carry_bills"])))''',
    '''    rows.append("<div class=line>Bill baaki: <b>%d</b></div>"
                % (len(w["today_bills"]) + len(w["carry_bills"])))
    nflag = len(w.get("flagged_bills") or [])
    if nflag:
        rows.append("<div class=line>Flag kiye hue bill: <b>%d</b> "
                    "<span class=sub>(din band karne se nahi rukte)</span></div>" % nflag)''',
)

# ---------------------------------------------------------------- 11. CSS for the flag line
edit(
    "css_was",
    '''.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}''',
    '''.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}
.bill .was{background:#fff8e1;border:1px solid #f0e0a8;border-radius:8px;
           padding:9px 11px;margin:0 0 10px;font-size:14px;color:var(--warn)}''',
)

# ---------------------------------------------------------------- apply


def _read(path):
    return io.open(path, "r", encoding="utf-8", newline="").read()


def build(src):
    """The S244 live file in, the S245 file out.  Refuses rather than guesses."""
    if "\r\n" in src:
        raise SystemExit("REFUSED: source has CRLF (F-294)")
    if hashlib.md5(src.encode("utf-8")).hexdigest() != SRC_MD5:
        raise SystemExit("REFUSED: source is not the S244 live amir_day.py (%s expected)" % SRC_MD5)
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
