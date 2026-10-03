#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s462.py -- S462_ADVANCE_POST_ONCE (session 292, 03-Oct-2026): a salary advance reaches the Staff Ledger ONCE.

Built from the real file (/root/finance/finance_app.py at 26a532a6, as S461 left it). F-706, proven on a scratch copy
with the box's own staff_ledger.py before a line was written:
  (a) approving a day with two salary advances whose second fails left the first in the Staff Ledger with its stamp
      rolled back -- and every retry posted the first again;
  (b) an APPROVED day that is corrected lost its stamps (the save deletes and re-inserts the expense rows), so the
      re-approval posted the advance a second time.

  api_approve   every row is checked -- and the ledger's own month ceiling asked for the day's total -- BEFORE any
                row is posted; if a post still fails part-way, the rows the ledger already took keep their stamp.
  api_save_day  a posted advance keeps its stamp through a correction (same amount); changing or removing one that
                the ledger still holds is refused, with words that say what to do.
staff_ledger.py is not touched. Each anchor must be found exactly once; anything else leaves the file as it was.
usage: apply_s462.py <path to finance_app.py>
"""
import hashlib
import sys

FROM = "26a532a6ec212ac66e6cfb41b37844eb"
EDITS = []


def ed(name, old, new):
    EDITS.append((name, old, new))


# ------------------------------------------------------------------ api_save_day: the stamp survives a correction
ed("save: before the old rows are deleted",
   '            eid = existing["id"]\n'
   '            for t in ("day_line", "day_expense", "cash_movement", "day_noncash_bill"):\n',
   '            eid = existing["id"]\n'
   '            # S462 (F-706): the rows below are deleted and re-inserted, which used to wipe ledger_posted -- so a\n'
   '            # corrected day posted its salary advance to the Staff Ledger a SECOND time at re-approval. An advance\n'
   '            # the ledger already holds keeps its stamp when it is still here at the same amount; one that was\n'
   '            # changed or removed is refused unless the ledger itself has reversed it.\n'
   '            _s462_new = [x for x in expenses if x["category_fixed"] == "salary_advance"]\n'
   '            for _s462_o in [dict(r) for r in con.execute(\n'
   '                    "SELECT amount_p, ledger_posted_at, ledger_ref, expense_uid FROM day_expense "\n'
   '                    "WHERE day_entry_id=? AND category_fixed=\'salary_advance\' AND ledger_posted=1 "\n'
   '                    "ORDER BY id", (eid,))]:\n'
   '                _s462_m = ([x for x in _s462_new if "_s462" not in x and x["amount_p"] == _s462_o["amount_p"]\n'
   '                            and x["uid"] and x["uid"] == _s462_o["expense_uid"]]\n'
   '                           or [x for x in _s462_new if "_s462" not in x\n'
   '                               and x["amount_p"] == _s462_o["amount_p"]])\n'
   '                if _s462_m:\n'
   '                    _s462_m[0]["_s462"] = _s462_o\n'
   '                elif not _s462_reversed(_s462_o["ledger_ref"]):\n'
   '                    con.execute("ROLLBACK")\n'
   '                    return jsonify(ok=False, error="advance_already_posted",\n'
   '                                   message="The salary advance of %s on this day is already in the Staff "\n'
   '                                           "Ledger. It cannot be changed or removed here. Leave it as it was, "\n'
   '                                           "or reverse it in the Staff Ledger first and then save again."\n'
   '                                           % rupees(_s462_o["amount_p"])), 409\n'
   '            for t in ("day_line", "day_expense", "cash_movement", "day_noncash_bill"):\n')
ed("save: the re-inserted row keeps its stamp",
   '                        (eid, e["amount_p"], e["category_fixed"], e["kind"], _sid,\n'
   '                         e["category_text"], e["uid"]))\n',
   '                        (eid, e["amount_p"], e["category_fixed"], e["kind"], _sid,\n'
   '                         e["category_text"], e["uid"]))\n'
   '            if e.get("_s462"):                 # S462: already in the Staff Ledger -- never posted again\n'
   '                con.execute("UPDATE day_expense SET ledger_posted=1, ledger_posted_at=?, ledger_ref=? "\n'
   '                            "WHERE id=(SELECT MAX(id) FROM day_expense WHERE day_entry_id=?)",\n'
   '                            (e["_s462"]["ledger_posted_at"], e["_s462"]["ledger_ref"], eid))\n')

# ------------------------------------------------------------------ the ledger's own word on a posting
ed("helper: has the ledger reversed it",
   '    import staff_ledger\n    return staff_ledger\n',
   '    import staff_ledger\n    return staff_ledger\n'
   '\n\n'
   'def _s462_reversed(ledger_ref):\n'
   '    """S462: True only when the Staff Ledger itself says this posting is no longer live -- the row was rejected,\n'
   '    or an approved contra of the same amount stands against it. A ledger that cannot be read, or a row that\n'
   '    cannot be found, is False: an advance the ledger may still hold is never opened for a second posting."""\n'
   '    if not ledger_ref:\n'
   '        return False\n'
   '    try:\n'
   '        rows = _staff_ledger_module().load_ledger()\n'
   '    except Exception:                                             # noqa: BLE001\n'
   '        return False\n'
   '    for r in rows:\n'
   '        if r.get("id") != ledger_ref:\n'
   '            continue\n'
   '        if r.get("status") == "REJECTED":\n'
   '            return True\n'
   '        return any(x.get("contra_of") == ledger_ref and x.get("category") == r.get("category")\n'
   '                   and x.get("amount") == -r.get("amount", 0) and x.get("status") == "APPROVED"\n'
   '                   for x in rows)\n'
   '    return False\n')

# ------------------------------------------------------------------ api_approve: check all, then post; keep what was taken
ed("approve: check every row before posting any",
   '            for a in advances:\n'
   '                if not a["staff_name"]:\n'
   '                    raise RuntimeError("salary-advance expense #%s has no staff_ref "\n'
   '                                       "name to post against" % a["id"])\n'
   '                if a["amount_p"] % 100 != 0:\n'
   '                    raise RuntimeError("salary advance #%s is %s -- the Staff Ledger "\n'
   '                                       "records whole rupees" % (a["id"], rupees(a["amount_p"])))\n'
   '                lrow = sl.make_entry(\n',
   '            # S462 (F-706): EVERY row is checked before ANY row is posted. The checks and the post used to share\n'
   '            # one loop, so a second row that failed left the first in the ledger with its stamp rolled back --\n'
   '            # and every retry posted the first again.\n'
   '            for a in advances:\n'
   '                if not a["staff_name"]:\n'
   '                    raise RuntimeError("salary-advance expense #%s has no staff_ref "\n'
   '                                       "name to post against" % a["id"])\n'
   '                if a["amount_p"] % 100 != 0:\n'
   '                    raise RuntimeError("salary advance #%s is %s -- the Staff Ledger "\n'
   '                                       "records whole rupees" % (a["id"], rupees(a["amount_p"])))\n'
   '            # S462: the ledger\'s own month ceiling, asked for the day\'s TOTAL per person with the ledger\'s own\n'
   '            # functions. If it cannot be asked here, the ledger\'s gate inside make_entry still stands.\n'
   '            _s462_need = {}\n'
   '            for a in advances:\n'
   '                _s462_need[a["staff_name"]] = _s462_need.get(a["staff_name"], 0) + a["amount_p"] // 100\n'
   '            for _s462_nm, _s462_amt in sorted(_s462_need.items()):\n'
   '                try:\n'
   '                    _s462_ceil = int(sl.advance_ceiling(_s462_nm))\n'
   '                    _s462_taken = int(sl.advance_month_taken(_s462_nm, iso[:7])) if _s462_ceil > 0 else 0\n'
   '                except Exception:                                 # noqa: BLE001\n'
   '                    _s462_ceil, _s462_taken = 0, 0\n'
   '                if _s462_ceil > 0 and _s462_taken + _s462_amt > _s462_ceil:\n'
   '                    raise RuntimeError(\n'
   '                        "the salary advances for %s on this day total Rs %d; with Rs %d already taken for %s "\n'
   '                        "that is over the Rs %d ceiling. Nothing was written to the Staff Ledger. Above the "\n'
   '                        "ceiling an advance is entered in the Staff Ledger itself, as a SPECIAL advance."\n'
   '                        % (_s462_nm, _s462_amt, _s462_taken, iso[:7], _s462_ceil))\n'
   '            for a in advances:\n'
   '                lrow = sl.make_entry(\n')
ed("approve: a row the ledger took keeps its stamp",
   '        except Exception as _lex:                 # noqa: BLE001 -- fail loud, refuse\n'
   '            con.rollback()\n'
   '            return jsonify(ok=False, error="ledger_post_failed",\n'
   '                           message="The day was NOT approved -- %s" % str(_lex)), 409\n',
   '        except Exception as _lex:                 # noqa: BLE001 -- fail loud, refuse\n'
   '            con.rollback()\n'
   '            # S462 (F-706): the rollback also took the stamps of rows the ledger had ALREADY accepted, so the next\n'
   '            # approval posted them again. The day stays not approved; what the ledger took stays stamped.\n'
   '            _s462_kept = 0\n'
   '            if posted:\n'
   '                try:\n'
   '                    for _s462_p in posted:\n'
   '                        con.execute("UPDATE day_expense SET ledger_posted=1, ledger_posted_at=?, "\n'
   '                                    "ledger_ref=? WHERE id=?",\n'
   '                                    (now_iso(), _s462_p["ledger_ref"], _s462_p["expense_id"]))\n'
   '                    audit(con, "day_entry", e["id"], "advance_posted_day_not_approved",\n'
   '                          after={"date": iso, "kept": posted, "why": str(_lex)[:300]}, who=u["user"])\n'
   '                    con.commit()\n'
   '                    _s462_kept = len(posted)\n'
   '                except Exception:                                 # noqa: BLE001\n'
   '                    con.rollback()\n'
   '            return jsonify(ok=False, error="ledger_post_failed",\n'
   '                           message="The day was NOT approved -- %s" % str(_lex)\n'
   '                                   + ((" (%d salary advance(s) already written to the Staff Ledger are kept "\n'
   '                                       "as posted and will not be written again.)" % _s462_kept)\n'
   '                                      if _s462_kept else ""),\n'
   '                           posted_kept=(posted if _s462_kept else [])), 409\n')


def apply(src):
    for name, old, new in EDITS:
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor '%s' found %d time(s), expected 1 - nothing written" % (name, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s462.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d edits; %+d bytes)"
          % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
