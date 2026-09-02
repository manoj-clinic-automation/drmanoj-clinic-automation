#!/usr/bin/env python3
"""
patch_marg_autoapply_s219.py -- S219 M1 (Marg auto-apply), FOUR anchored
changes to /root/finance/finance_app.py, every OLD block sliced verbatim from
the live bytes 80c2323a82de81de17093df78b0a3139 (never re-typed -- A0):

  A  the S219 helpers, inserted immediately before _replay_pending_marg_for_day
     (bill-key parse, per-day series, apply summary, continuity check)
  B  the auto-replay reports its summary and any gaps
  C  the checker's apply reports the same summary, from the same helper
  D  the push auto-applies any day that is ALREADY filed, via that same replay

No page changes: the owner's hub is FINAL (S218_CARDS_FINAL_CONTRACT rev 2).
No new module, no schema change, no new table -- the only write that did not
exist before is a MARG_BILL_RANGE_GAP row in data_flag.

SAFETY: exact-once assert on all four anchors, timestamped backup,
compile-with-restore, idempotent via MARK.
USAGE: /root/wa/venv/bin/python3 -B /root/finance/patch_marg_autoapply_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S219 M1 -- MARG AUTO-APPLY"

A_OLD = 'def _replay_pending_marg_for_day(con, iso, by="auto"):\n'

A_NEW = '# ============================================================================\n#  S219 M1 -- MARG AUTO-APPLY: the apply summary, the bill-range continuity\n#  check, and the second order (an export arriving when the day is ALREADY\n#  filed).  THE APPLY ITSELF IS NOT REIMPLEMENTED HERE.  Both existing paths\n#  keep their own guards -- the checker\'s api_marg_push_apply() and the S194\n#  auto-replay below -- and these helpers only READ what an apply has just\n#  landed and say what it did.  One rule, both readers (D349); two copies of a\n#  rule is how two screens come to disagree about the same day, which is the\n#  argument marg_net_sql() above was written out of after 18-08-2026.\n# ============================================================================\n\ndef _marg_bill_key(ref):\n    """A Marg bill number split into (series, number): \'A001988\' -> (\'A\', 1988),\n    \'CN00184\' -> (\'CN\', 184).  None for anything that is not one, so a blank or\n    foreign reference is SKIPPED rather than guessed at.\n\n    The series must be one to three LETTERS.  That rule is not arbitrary: the\n    live database also carries source_refs like \'S186-F104-1332\' left by the\n    S186 backfill, and a looser parser read those as a bill series 3,889\n    numbers deep -- a phantom that drowned the real A and CN series when this\n    was first measured against real history."""\n    s = (ref or "").strip().upper()\n    if not s:\n        return None\n    i = len(s)\n    while i > 0 and s[i - 1].isdigit():\n        i -= 1\n    if i == len(s):\n        return None\n    pre = s[:i]\n    if pre and not (len(pre) <= 3 and pre.isalpha()):\n        return None\n    try:\n        return (pre, int(s[i:]))\n    except ValueError:\n        return None\n\n\ndef _marg_day_series(con, day_entry_id):\n    """{series: (lowest, highest)} over the bills a day ACTUALLY holds, read\n    from sale_item.source_ref -- where finance_ingest puts the Marg bill\n    number.  Never from the pushed payload: a summary must describe what\n    landed, not what was offered."""\n    out = {}\n    for r in con.execute("SELECT source_ref FROM sale_item WHERE day_entry_id=? "\n                         "AND source_ref IS NOT NULL", (day_entry_id,)):\n        k = _marg_bill_key(r["source_ref"])\n        if not k:\n            continue\n        lo, hi = out.get(k[0], (k[1], k[1]))\n        out[k[0]] = (min(lo, k[1]), max(hi, k[1]))\n    return out\n\n\ndef _marg_apply_summary(con, iso):\n    """S219 M1 -- the short summary the owner asked for, computed AFTER the\n    day\'s ingest has committed: bill range per series, the day\'s signed net,\n    UPI as MARG ITSELF labelled it, and the credit-note count.\n\n    \'UPI per Marg\' is deliberately Marg\'s own column and not the bank\'s\n    figure.  The bank statement is the sole truth for what settled (S208); the\n    point of showing Marg\'s label beside it is that the two CAN disagree, and\n    that disagreement is the mis-classification Amir\'s corrections desk exists\n    to fix.  Returns None when the day is not filed."""\n    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",\n                    (UNIT, iso)).fetchone()\n    if not e:\n        return None\n    series = _marg_day_series(con, e["id"])\n    net_p = con.execute("SELECT %s p FROM sale_item WHERE day_entry_id=?"\n                        % marg_net_sql("sale_item"), (e["id"],)).fetchone()["p"]\n    upi_p = con.execute(\n        "SELECT COALESCE(SUM(amount_p),0) p FROM sale_item WHERE day_entry_id=? "\n        "AND LOWER(COALESCE(mode,\'\')) LIKE \'%upi%\'", (e["id"],)).fetchone()["p"]\n    cn = con.execute(\n        "SELECT COUNT(*) c FROM sale_item WHERE day_entry_id=? "\n        "AND COALESCE(service,\'\') LIKE \'%return%\'", (e["id"],)).fetchone()["c"]\n    bills = con.execute("SELECT COUNT(*) c FROM sale_item WHERE day_entry_id=?",\n                        (e["id"],)).fetchone()["c"]\n    rng = ", ".join("%s%d-%s%d" % (k, v[0], k, v[1])\n                    for k, v in sorted(series.items()))\n    return dict(date=iso, bills=bills, cn=cn, net_p=net_p, upi_marg_p=upi_p,\n                series=dict((k, list(v)) for k, v in series.items()),\n                bill_range=(rng or None),\n                line=("%s: bills %s | total Rs %s | UPI per Marg Rs %s | "\n                      "%d credit note(s)"\n                      % (iso, rng or "n/a", rupees(net_p), rupees(upi_p), cn)))\n\n\ndef _marg_continuity_check(con, iso):\n    """S219 M1 -- bill-number continuity against the PREVIOUS export.\n\n    A gap between this day\'s lowest bill and the previous day\'s highest, in\n    the same series, means bills exist in Marg that never reached the books --\n    an export skipped, filtered, or silently truncated.  The books cannot\n    discover that any other way, so it is raised as a flag and the Walk\n    carries it.\n\n    Deliberately conservative, and the threshold is MEASURED rather than\n    guessed.  Walked over all 135 days of real history (2026-04-01 .. 09-01)\n    this raised 47 gaps: 22 of one bill, 18 of two, and the largest in five\n    months was SIX.  Thirty-seven of them fall between consecutive calendar\n    days, which is the ordinary texture of a counter that cancels a bill now\n    and then -- not something anybody can act on.  A flag that fires every\n    other day on an unactionable one-bill gap is an amber nobody reads, so the\n    floor is a SETTING (`marg.bill_gap_min`, default 10) sitting clear of the\n    observed noise: it would have raised zero false alarms over those five\n    months, while a truncated or skipped export -- the thing this exists to\n    catch -- loses far more than ten.  The range itself is always reported in\n    the summary either way, so nothing is ever hidden; only a real\n    discontinuity shouts.\n\n    Also: the nearest earlier day that actually holds that series, only inside\n    14 days (a longer silence is a missing day, which already has its own\n    MARG_DAY_NOT_FILED record), and never a second identical flag for the same\n    day.  Writes flags; the caller commits."""\n    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",\n                    (UNIT, iso)).fetchone()\n    if not e:\n        return []\n    mine = _marg_day_series(con, e["id"])\n    if not mine:\n        return []\n    prev = {}\n    for r in con.execute(\n            "SELECT d.business_date bd, s.source_ref r FROM sale_item s "\n            "JOIN day_entry d ON d.id=s.day_entry_id "\n            "WHERE d.unit=? AND d.business_date<? "\n            "AND d.business_date>=date(?, \'-14 day\') "\n            "AND s.source_ref IS NOT NULL", (UNIT, iso, iso)):\n        k = _marg_bill_key(r["r"])\n        if not k:\n            continue\n        cur = prev.get(k[0])\n        if cur is None or (r["bd"], k[1]) > (cur[0], cur[1]):\n            prev[k[0]] = (r["bd"], k[1])\n    try:\n        floor = int(setting(con, "marg.bill_gap_min", "10") or 10)\n    except (TypeError, ValueError):\n        floor = 10\n    if floor < 1:\n        floor = 1\n    gaps = []\n    for ser, lohi in sorted(mine.items()):\n        p = prev.get(ser)\n        if not p:\n            continue\n        missing = lohi[0] - p[1] - 1\n        if missing < floor:\n            continue\n        detail = ("bill-number gap in series %s: %s ended at %s%d and %s starts "\n                  "at %s%d -- %d bill(s) between them never reached the books. "\n                  "Either that export was truncated, or those bills were "\n                  "issued on a day that was never exported."\n                  % (ser or "(none)", p[0], ser, p[1], iso, ser, lohi[0],\n                     missing))[:400]\n        if con.execute("SELECT 1 FROM data_flag WHERE unit=? AND business_date=? "\n                       "AND code=\'MARG_BILL_RANGE_GAP\' AND detail=?",\n                       (UNIT, iso, detail)).fetchone():\n            continue\n        con.execute("INSERT INTO data_flag (unit, business_date, code, severity, "\n                    "detail) VALUES (?,?,?,?,?)",\n                    (UNIT, iso, "MARG_BILL_RANGE_GAP", "medium", detail))\n        gaps.append(dict(series=ser, prev_date=p[0], prev_high=p[1],\n                         this_low=lohi[0], missing=missing, detail=detail))\n    return gaps\n\n\ndef _marg_after_apply(con, iso):\n    """Summary + continuity for one applied day.  Wrapped so that neither can\n    ever damage an apply that has already committed: on any error the day\n    keeps its books and simply reports no summary."""\n    try:\n        _s = _marg_apply_summary(con, iso)\n        _g = _marg_continuity_check(con, iso)\n        con.commit()\n        return _s, _g\n    except Exception:                                        # noqa: BLE001\n        try:\n            con.rollback()\n        except Exception:                                    # noqa: BLE001\n            pass\n        return None, []\n\n\ndef _replay_pending_marg_for_day(con, iso, by="auto"):\n'

B_OLD = '            out.append(dict(push=row["id"], date=iso, bills=got, lines=n_lines))\n'

B_NEW = '            _sum, _gaps = _marg_after_apply(con, iso)\n            out.append(dict(push=row["id"], date=iso, bills=got,\n                            lines=n_lines, summary=_sum, gaps=_gaps))\n'

C_OLD = '            done.append(dict(date=iso_d, bills=got, lines=n_lines,\n                             accepted=res.get("accepted"), review=res.get("review")))\n'

C_NEW = '            _sum, _gaps = _marg_after_apply(con, iso_d)\n            done.append(dict(date=iso_d, bills=got, lines=n_lines,\n                             accepted=res.get("accepted"),\n                             review=res.get("review"),\n                             summary=_sum, gaps=_gaps))\n'

D_OLD = '        con.commit()\n        return jsonify(ok=True, verdict="ACCEPTED-FOR-REVIEW",\n                       id=cur.lastrowid, days=survey, not_filed=not_filed,\n                       bills=sum(len(d["bills"]) for d in rep["days"]),\n                       item_lines=total_items,\n                       message="Received: %d day(s), %d bill(s). NOTHING has "\n                               "entered the books -- Dr. Manoj will check and "\n                               "apply it on the workbench. Report pahunch "\n                               "gayi hai; abhi khaate mein nahi gayi."\n                               % (len(days), sum(len(d["bills"])\n                                                 for d in rep["days"])))\n'

D_NEW = '        con.commit()\n\n        # ---- S219 M1: THE SECOND ORDER ------------------------------------\n        # A day already filed when its export arrived used to sit in \'pending\'\n        # until the owner opened the workbench and pressed Apply.  The other\n        # order has been automatic since S194 (the replay on day save, F-155);\n        # this makes the pair symmetrical, which is the whole of M1.\n        #\n        # It calls that SAME replay -- the apply rule is not written twice --\n        # and it can never turn a good push into a failed one: on any error\n        # the staging row is left exactly as it was, pending, and the owner\'s\n        # manual Apply still works as it always did.\n        auto = []\n        try:\n            for _d in days_payload:\n                if _d["date"] in not_filed:\n                    continue\n                auto.extend(_replay_pending_marg_for_day(con, _d["date"],\n                                                         by="auto-push"))\n        except Exception:                                    # noqa: BLE001\n            try:\n                con.rollback()\n            except Exception:                                # noqa: BLE001\n                pass\n            auto = []\n        _lines = [a["summary"]["line"] for a in auto\n                  if a.get("summary") and a["summary"].get("line")]\n        _gapn = sum(len(a.get("gaps") or []) for a in auto)\n        return jsonify(ok=True,\n                       verdict=("APPLIED" if auto else "ACCEPTED-FOR-REVIEW"),\n                       id=cur.lastrowid, days=survey, not_filed=not_filed,\n                       bills=sum(len(d["bills"]) for d in rep["days"]),\n                       item_lines=total_items,\n                       applied=auto, summary=_lines, gaps=_gapn,\n                       message=(("Applied automatically. " + " ; ".join(_lines)\n                                 + ((" | %d bill-range gap(s) flagged."\n                                     % _gapn) if _gapn else ""))\n                                if auto else\n                                ("Received: %d day(s), %d bill(s). NOTHING has "\n                                 "entered the books -- Dr. Manoj will check and "\n                                 "apply it on the workbench. Report pahunch "\n                                 "gayi hai; abhi khaate mein nahi gayi."\n                                 % (len(days), sum(len(d["bills"])\n                                                   for d in rep["days"])))))\n'

PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW),
         ("C", C_OLD, C_NEW), ("D", D_OLD, D_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched (%s) -- nothing to do" % MARK)
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "The live file is not the one this kit was built "
                             "against; nothing has been changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S219_m1_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); restored from %s" % (ex, bak))
    print("patched %s (%s)" % (TARGET, MARK))
    print("backup  %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
