#!/usr/bin/env python3
"""S247_LEDGER_LATE_COLLECT -- collect an advance against a month already closed.

Built on the LIVE staff_ledger.py v3.7-S238-CLOSE-GUARD (49b13f42...).

The owner, 13-Sep-2026: Alisha's Rs 5,000 advance of 25-Aug is booked against the
August salary, but August's close had been pressed on the 20th, so the collection
fell to the September close -- and nothing in the app could pull it back.
"I cannot find any flow for that."  There was none.  This is it.

Every replacement is an exact, unique, asserted swap.  If the source file is not the
live one, or any anchor has moved, this refuses and writes nothing.
"""
import hashlib
import io
import os
import sys

SRC_MD5 = "49b13f42d3a923c5bb2e34230c80e6e8"      # live /root/staff_ledger.py, v3.7

_BLOB = r'''
###EDIT versionlog
###OLD
  + A SPECIAL ADVANCE NEEDS A NARRATION (the one row that most needs a reason).

Environment (all optional):
###NEW
  + A SPECIAL ADVANCE NEEDS A NARRATION (the one row that most needs a reason).
v3.8 (S247 -- the owner, 13-Sep-2026, on Alisha's Rs 5,000 of 25-Aug: "which was made
  against the August month, has been marked for September in your salary sheet. I want
  it deducted in the August month salary payment only. I cannot find any flow for that."):
  + COLLECT AN ADVANCE AGAINST A MONTH THAT IS ALREADY CLOSED. August's close was
    pressed on the 20th; an advance entered on the 25th could only ever recover at the
    next close, and DEFER -- the one control on the card -- moves it further away, not
    back. A close can never be repeated (close_month refuses one), so the instrument is
    a single ADVANCE_INSTALMENT row stamped to that month: exactly the row the close
    itself writes, with a person's name and a written reason on it.
    Narrow on purpose: the month must already be CLOSED, never earlier than the month
    the advance counts against, never twice for the same advance and month, never more
    than the balance. Interest, schedules and the capacity gate are the close's
    business and are untouched -- this records a collection the owner has decided.

Environment (all optional):
###EDIT appversion
###OLD
APP_VERSION = "3.7-S238-CLOSE-GUARD"
###NEW
APP_VERSION = "3.8-S247-LATE-COLLECT"
###EDIT record_late_collection
###OLD
    append_ledger(row)
    return row

# THE CAPACITY RULE (F-147): nothing recovers that the salary cannot bear.
###NEW
    append_ledger(row)
    return row


# =============================================================================
#  S247: THE COLLECTION THAT ARRIVED AFTER THE CLOSE
# =============================================================================

def closed_months(rows=None):
    """Every month this ledger has actually closed, newest first."""
    return sorted({r.get("closed_month") for r in (rows or load_ledger())
                   if r.get("closed_month")}, reverse=True)


def late_collect_blocked(issue, month, rows):
    """Why this advance cannot be collected against `month`, or "" if it can.

    Split out from record_late_collection so the page can offer only the months
    that will actually be accepted, rather than letting him find out by failing.
    """
    if not any(r.get("closed_month") == month for r in rows):
        return f"{month} is not closed yet -- its own close will collect this"
    am = advance_against_month(issue)
    if am and month < am:
        return (f"this advance counts against {am} salary -- it cannot be "
                f"collected in {month}")
    if any(r.get("closed_month") == month and r["category"] == "ADVANCE_INSTALMENT"
           and r["contra_of"] == issue["id"] and r["status"] == "APPROVED"
           for r in rows):
        return f"{month} already has a collection for this advance"
    return ""


def record_late_collection(users, checker, issue_id, month, reason, amount=None):
    """Collect an advance against a month whose close has ALREADY been pressed.

    close_month() refuses a re-close, by design -- a month is closed once. So the
    collection that the close would have made, had the advance existed on the day
    it ran, is written here instead: ONE ADVANCE_INSTALMENT row stamped to that
    month, carrying the name of the person who decided it and a written reason.

    It is deliberately narrow:
      * the month must already be CLOSED -- an open month's own close will do it;
      * never earlier than the month the advance is attributed against;
      * never twice for the same advance and month;
      * never more than the balance.

    Interest, schedules and the capacity gate belong to the close and are not
    touched. Nothing is edited: the ledger stays append-only.
    """
    if users[checker]["role"] != "checker":
        raise PermissionError("only checkers record a collection")
    datetime.date.fromisoformat(month + "-01")          # validates YYYY-MM
    if not (reason or "").strip():
        raise ValueError("a late collection needs a written reason")
    rows = load_ledger()
    issue = next((r for r in rows if r["id"] == issue_id), None)
    if not issue or issue["category"] != "ADVANCE_ISSUE" or issue["status"] != "APPROVED":
        raise ValueError("no such approved advance")
    stop = late_collect_blocked(issue, month, rows)
    if stop:
        raise ValueError(stop)
    bal = (issue["amount"] + advance_capitalised(issue_id, rows)
           - advance_recovered(issue_id, rows))
    if bal <= 0:
        raise ValueError("this advance has nothing left to collect")
    raw = "" if amount is None else str(amount).strip()
    if raw:
        try:
            amt = int(float(raw))
        except (TypeError, ValueError):
            raise ValueError("the amount must be a number of rupees")
    else:
        amt = int(bal)
    if amt <= 0 or amt > bal:
        raise ValueError("the amount must be between Rs 1 and the balance of "
                         f"Rs {int(bal)}")
    row = {"id": secrets.token_hex(6), "ts_entry": now(), "maker": checker,
           "staff": issue["staff"], "category": "ADVANCE_INSTALMENT",
           "date_from": month, "date_to": month, "days": 0,
           "amount": -amt, "instalment": None,
           "narration": (f"collected against {month} salary, recorded by {checker} "
                         f"after that month had already been closed -- "
                         f"{reason.strip()}"),
           "self_flag": False, "direct": True, "status": "APPROVED",
           "checker": checker, "ts_decision": now(),
           "contra_of": issue_id, "closed_month": month, "interest": False,
           "late_collection": True}
    append_ledger(row)
    return row


# THE CAPACITY RULE (F-147): nothing recovers that the salary cannot bear.
###EDIT ui_form
###OLD
            _st = a["issue"]["staff"]
            groups.setdefault(_st, []).append(
                     f"<div class='card' style='margin:8px 0'>advance "
                     f"Rs {a['issue']['amount']} ({a['issue']['date_from']}){tag}"
                     f"{am_note}{sp_note}<br>"
                     f"balance <b>Rs {a['balance']}</b> · recovering Rs {a['instalment']}/month"
                     f"{sched_note}{def_band}{defer_form}{skiprow}<br><small>id {iid}</small></div>")
###NEW
            # ---- S247: the months this advance may still be collected against ----
            # Only months whose close has actually run, not earlier than the month the
            # advance counts against, and not already carrying a collection for it. If
            # there are none, the control is not shown at all.
            _cand = [m for m in closed_months(_rows_all)
                     if not late_collect_blocked(a["issue"], m, _rows_all)]
            late_form = ""
            if _cand:
                _opts = "".join(f"<option value='{m}'>{m}</option>" for m in sorted(_cand))
                late_form = f"""<form method="post" action="{URL_PREFIX}/late-collect"
                    style="margin-top:6px;border-top:1px dashed #555;padding-top:6px">
                    <input type="hidden" name="id" value="{iid}">
                    <small>Collect against a month that is already closed — a close is
                    never repeated, so this records the same collection by hand.</small><br>
                    <select name="month" style="width:auto">{_opts}</select>
                    <input name="amount" value="{a['balance']}" style="width:7em"
                           inputmode="numeric">
                    <input name="reason" placeholder="reason (required)" required>
                    <button onclick="return confirm('Record this collection against the month chosen above? It shows on the salary sheet for that month.')">Collect in that month</button>
                    </form>"""
            _st = a["issue"]["staff"]
            groups.setdefault(_st, []).append(
                     f"<div class='card' style='margin:8px 0'>advance "
                     f"Rs {a['issue']['amount']} ({a['issue']['date_from']}){tag}"
                     f"{am_note}{sp_note}<br>"
                     f"balance <b>Rs {a['balance']}</b> · recovering Rs {a['instalment']}/month"
                     f"{sched_note}{def_band}{defer_form}{late_form}{skiprow}"
                     f"<br><small>id {iid}</small></div>")
###EDIT route
###OLD
    @app.route(URL_PREFIX + "/skip", methods=["POST"])
###NEW
    @app.route(URL_PREFIX + "/late-collect", methods=["POST"])
    def late_collect_route():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        try:
            record_late_collection(users, u, request.form["id"].strip(),
                                   request.form["month"].strip(),
                                   request.form.get("reason", ""),
                                   request.form.get("amount"))
        except (PermissionError, ValueError, KeyError) as e:
            return page("Advances",
                        f"<p style='color:red'>NOT recorded: {html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/advances'>back to Advances</a></p>", u)
        return redirect(URL_PREFIX + "/advances")

    @app.route(URL_PREFIX + "/skip", methods=["POST"])
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
N_EDITS = 5


def _read(path):
    return io.open(path, "r", encoding="utf-8", newline="").read()


def build(src):
    if "\r\n" in src:
        raise SystemExit("REFUSED: source has CRLF (F-294)")
    if hashlib.md5(src.encode("utf-8")).hexdigest() != SRC_MD5:
        raise SystemExit("REFUSED: source is not the live v3.7 staff_ledger.py (%s expected)"
                         % SRC_MD5)
    if len(EDITS) != N_EDITS:
        raise SystemExit("REFUSED: parsed %d edits, expected %d" % (len(EDITS), N_EDITS))
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
    raise SystemExit("usage: %s --selftest <live staff_ledger.py> <kit staff_ledger.py>\n"
                     "       %s --build    <live staff_ledger.py> <out staff_ledger.py>"
                     % (argv[0], argv[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
