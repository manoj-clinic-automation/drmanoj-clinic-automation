#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_marg_autoapply_s243.py -- S243: a pushed SALE_BILLWISE_DETAIL report
applies itself the moment it arrives (owner's ruling, 13-Sep-2026: "Apply must
be automatic").  Newest export wins; an older pending push for the same day is
superseded; a push that carries nothing the books do not already hold is
superseded as "older than applied".  Every automatic act writes audit_log with
actor 'auto' and the rule name.  The manual Apply / Remove buttons are untouched.
OFF switch: the file /root/finance/AUTOAPPLY_OFF -> behaves exactly as today.

FOUR anchored changes to /root/finance/finance_app.py, each asserted to occur
EXACTLY ONCE in the live bytes (else REFUSED, nothing written):

  H  the S243 helpers, inserted immediately before api_marg_push()
  P  the checker's api_marg_push_apply() is split at its prelude: the route
     keeps the login gate and the request body; everything after it becomes
     _marg_apply_core_s243(u, pid) -- the SAME body, byte for byte, so the
     automatic apply and the button run ONE rule (D349).  Every later patch to
     that body (S210 D354 autofile, S219 summary) rides along unchanged.
  L  api_marg_push_list(): each row also carries auto = the S243 facts (rule,
     time) so the hub can say "applied automatically" / "superseded by ...".
  D  api_marg_push(): after the staging row commits, the S243 auto-apply runs
     and answers; when it stands aside (OFF file, modules absent, or an error
     inside it) the code that was there before -- S219 second order, or the
     plain ACCEPTED-FOR-REVIEW -- runs exactly as today.  Both shapes of that
     block are known (S219 present / absent); the patcher refuses if neither
     occurs exactly once.

Designed to run ON THE BOX against the live file, which is not in the repository:

    /root/wa/venv/bin/python3 -B patch_marg_autoapply_s243.py
        reads  FA_PATH (default /root/finance/finance_app.py)
        writes FA_PATH.new  (never the live file itself)
        prints the md5 before and after

Prints ALREADY PATCHED and exits 0 when the S243 marker is already present.
--selftest <finance_app copies...> : patches each copy in memory, compiles it,
proves the marks, proves the second run is a no-op, proves a stranger refuses.
"""
import hashlib
import io
import os
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S243 AUTO-APPLY -- newest export wins"
OFF_FILE_DEFAULT = "/root/finance/AUTOAPPLY_OFF"

# ---------------------------------------------------------------------------
#  H  helpers, inserted before the push route
# ---------------------------------------------------------------------------
H_OLD = '@app.route("/finance/api/marg-push", methods=["POST"])\ndef api_marg_push():\n'

H_NEW = r'''# ============================================================================
#  S243 AUTO-APPLY, newest export wins.  Owner's ruling (13-Sep-2026): a
#  pushed sale report is applied the moment it arrives, filed day or not.
#
#  The apply itself is NOT reimplemented: _marg_autoapply_s243() calls
#  _marg_apply_core_s243(), which is the checker's own Apply with its login
#  gate lifted off -- one rule for the button and for the machine (D349).
#  What is new here is only the ORDER rule around that call:
#    1  a push carrying nothing the books do not already hold for every day
#       it names (fewer-or-equal bills, no later bill number, and -- once an
#       S243 apply has recorded the day's net -- the same net) is put aside
#       as superseded -- "older than applied";
#    2  otherwise it is applied; when that succeeds, every OLDER push still
#       pending whose days all lie inside this one is put aside as superseded
#       -- "superseded by <md5-8>" -- so the S194 day-save replay can never
#       drag an older export back over a newer one.
#  Every automatic act is an audit_log row by 'auto' naming its rule, and the
#  staging row records applied_by='auto' with the facts in apply_result_json.
#  OFF switch: the file named by FINANCE_AUTOAPPLY_OFF (default
#  /root/finance/AUTOAPPLY_OFF) exists -> this code stands aside entirely and
#  the push behaves exactly as it did before S243.  Nothing here can turn a
#  good push into a failed one: on any error the row stays pending and the
#  owner's Apply button works as it always did.
# ============================================================================

def _marg_autoapply_off_s243():
    return os.path.exists(os.environ.get("FINANCE_AUTOAPPLY_OFF", "%(off)s"))


def _marg_staging_cols_s243(con):
    """applied_by exists in the S187 DDL; the live table was born with it.
    Guarded anyway, idempotently, because a column this code writes must
    exist before it is written."""
    cols = [r[1] for r in con.execute("PRAGMA table_info(marg_push_staging)")]
    for c in ("applied_at", "applied_by", "apply_result_json"):
        if c not in cols:
            con.execute("ALTER TABLE marg_push_staging ADD COLUMN %%s TEXT" %% c)


def _marg_a_num_s243(ref):
    """'A001988' -> 1988 for the sale series only (credit notes are their own
    series and say nothing about how far the day's billing had reached)."""
    s = (ref or "").strip().upper()
    if len(s) < 2 or s[0] != "A" or not s[1:].isdigit():
        return None
    return int(s[1:])


def _marg_resp_json_s243(resp):
    r = resp[0] if isinstance(resp, tuple) else resp
    try:
        return r.get_json(silent=True) or {}
    except Exception:                                        # noqa: BLE001
        return {}


def _marg_applied_state_s243(con, iso):
    """What the books ALREADY hold for day iso from an earlier export, or None.
    Prefers the facts an earlier S243 apply recorded (bills counted as the
    ingest counts them -- non-zero bills -- and the highest A-number in the
    file); falls back to the day's current ingest_batch and its sale_item
    bill refs, which is a lower bound for the last bill and never an upper."""
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (UNIT, iso)).fetchone()
    if not e:
        return None
    b = con.execute("SELECT id, rows_read FROM ingest_batch WHERE day_entry_id=? "
                    "AND adapter='marg_export' AND status IN ('ok','partial') "
                    "ORDER BY id DESC LIMIT 1", (e["id"],)).fetchone()
    if not b:
        return None
    bills = int(b["rows_read"] or 0)
    last = None
    net_p = None
    for r in con.execute("SELECT source_ref FROM sale_item WHERE day_entry_id=? "
                         "AND ingest_batch_id=?", (e["id"], b["id"])):
        n = _marg_a_num_s243(r["source_ref"])
        if n is not None and (last is None or n > last):
            last = n
    for r in con.execute("SELECT id, apply_result_json FROM marg_push_staging "
                         "WHERE unit=? AND status='applied' AND apply_result_json "
                         "LIKE '%%\"s243\"%%' ORDER BY id DESC", (UNIT,)):
        try:
            rec = ((json.loads(r["apply_result_json"] or "{}") or {}).get("s243")
                   or {}).get("days") or {}
        except ValueError:
            continue
        d = rec.get(iso)
        if not d:
            continue
        bills = max(bills, int(d.get("bills") or 0))
        if d.get("last_bill") is not None and (last is None or d["last_bill"] > last):
            last = d["last_bill"]
        net_p = d.get("net_p")
        break
    return dict(bills=bills, last_bill=last, net_p=net_p, batch_id=b["id"])


def _marg_put_aside_s243(con, row_id, rule, facts, who="auto"):
    """status 'superseded' -- the word this table's CHECK already allows for a
    push ruled out by a later one (S211 proved 'dismissed' is refused by the
    live table).  Row and audit kept; replay payload cleared so it can never
    be applied by the S194 day-save replay or by a stray click."""
    res = dict(s243=dict(rule=rule, at=now_iso(), by=who, **facts))
    con.execute("UPDATE marg_push_staging SET status='superseded', parsed_json=NULL, "
                "applied_at=?, applied_by=?, apply_result_json=? WHERE id=?",
                (now_iso(), who, json.dumps(res), row_id))
    audit(con, "marg_push_staging", row_id, "auto-dismiss",
          after=dict(rule=rule, **facts), who=who)


def _marg_autoapply_s243(con, pid, days_payload, rep, fname):
    """Returns None when it stands aside (the caller then runs the pre-S243
    code), else a dict(verdict=..., message=...) the push answers with."""
    if _marg_autoapply_off_s243():
        return None
    if finance_ingest is None or finance_returns is None:
        return None
    RULE_APPLY = "S243 newest-wins: applied automatically on arrival"
    RULE_OLDER = "older than applied"
    try:
        _marg_staging_cols_s243(con)
        md5_8 = (con.execute("SELECT file_md5 FROM marg_push_staging WHERE id=?",
                             (pid,)).fetchone() or [""])[0][:8]
        expect = dict((d["date"], int(d.get("expect") or 0)) for d in days_payload)
        nets = dict((d["date"], d.get("net_p")) for d in days_payload)
        mine = {}
        for d in rep.get("days") or []:
            nums = [n for n in (_marg_a_num_s243(b.get("bill_no")) for b in d["bills"])
                    if n is not None]
            mine[d["date"]] = dict(bills=expect.get(d["date"], len(d["bills"])),
                                   all_bills=len(d["bills"]),
                                   last_bill=(max(nums) if nums else None),
                                   net_p=nets.get(d["date"]))
        days = [d["date"] for d in days_payload]

        # ---- rule 1: does this export bring anything the books lack? -------
        fuller, held_by = False, {}
        for iso in days:
            st = _marg_applied_state_s243(con, iso)
            m = mine.get(iso) or dict(bills=expect.get(iso, 0), last_bill=None,
                                      net_p=nets.get(iso))
            if st is None:
                fuller = True
                continue
            # more bills, or a later sale bill, or -- when an earlier S243 apply
            # recorded the day's net -- a different net (a corrected re-export
            # of the same bills is a later export too; newest wins)
            later = (m["last_bill"] is not None and st["last_bill"] is not None
                     and m["last_bill"] > st["last_bill"])
            same_set = (m["bills"] == st["bills"] and (
                m["last_bill"] is None or st["last_bill"] is None
                or m["last_bill"] == st["last_bill"]))
            corrected = (same_set and st.get("net_p") is not None
                         and m.get("net_p") is not None
                         and int(m["net_p"]) != int(st["net_p"]))
            if m["bills"] > st["bills"] or later or corrected:
                fuller = True
            else:
                held_by[iso] = dict(applied_bills=st["bills"],
                                    applied_last_bill=st["last_bill"],
                                    this_bills=m["bills"], this_last_bill=m["last_bill"])
        if not fuller:
            _marg_put_aside_s243(con, pid, RULE_OLDER,
                                 dict(file=(fname or "")[:80], md5=md5_8, days=held_by))
            for iso in days:
                con.execute("DELETE FROM data_flag WHERE unit=? AND code='MARG_DAY_NOT_FILED' "
                            "AND business_date=? AND EXISTS (SELECT 1 FROM day_entry "
                            "WHERE unit=? AND business_date=?)", (UNIT, iso, UNIT, iso))
            con.commit()
            return dict(verdict="SUPERSEDED", rule=RULE_OLDER, days=held_by,
                        message=("Received, and put aside automatically: the books "
                                 "already hold a fuller export for %%s (%%s). Nothing "
                                 "changed. Yeh report purani hai; khaate mein pehle se "
                                 "poori report hai." %% (", ".join(days), RULE_OLDER)))

        # ---- rule 2: apply, through the checker's own Apply -----------------
        j = _marg_resp_json_s243(_marg_apply_core_s243({"user": "auto"}, pid))
        ok = bool(j.get("ok")) and bool(j.get("ingested")) and not j.get("still_not_filed")
        if not ok:
            why = (j.get("aborted") or j.get("error")
                   or ("still not filed: %%s" %% ", ".join(j.get("still_not_filed") or []))
                   or "apply did not complete")
            audit(con, "marg_push_staging", pid, "auto-apply-held",
                  after=dict(rule=RULE_APPLY, why=why, file=(fname or "")[:80], md5=md5_8),
                  who="auto")
            con.commit()
            return dict(verdict="ACCEPTED-FOR-REVIEW", rule=RULE_APPLY, held=why,
                        message=("Received: %%d day(s). Automatic apply could not "
                                 "complete (%%s) -- the report is staged for Dr. Manoj "
                                 "to check and apply on the workbench. Report pahunch "
                                 "gayi hai; abhi khaate mein nahi gayi."
                                 %% (len(days), str(why)[:160])))

        # ---- applied: record the facts, retire older pending pushes --------
        sup = []
        for r in con.execute("SELECT id, file_md5, parsed_json, survey_json FROM "
                             "marg_push_staging WHERE unit=? AND status='pending' "
                             "AND id<? ORDER BY id", (UNIT, pid)).fetchall():
            theirs = []
            try:
                p = json.loads(r["parsed_json"] or "null")
                theirs = [d.get("date") for d in ((p or {}).get("days") or [])]
                if not theirs:
                    sv = json.loads(r["survey_json"] or "{}")
                    theirs = [d.get("date") for d in (sv.get("survey") or [])]
            except ValueError:
                theirs = []
            theirs = [t for t in theirs if t]
            if theirs and set(theirs) <= set(days):
                _marg_put_aside_s243(con, r["id"], "superseded by %%s" %% md5_8,
                                     dict(by_push=pid, by_md5=md5_8, days=theirs,
                                          md5=(r["file_md5"] or "")[:8]))
                sup.append(dict(id=r["id"], md5=(r["file_md5"] or "")[:8], days=theirs))
        flags = 0
        for iso in days:
            flags += con.execute(
                "DELETE FROM data_flag WHERE unit=? AND code='MARG_DAY_NOT_FILED' "
                "AND business_date=? AND EXISTS (SELECT 1 FROM day_entry WHERE unit=? "
                "AND business_date=?)", (UNIT, iso, UNIT, iso)).rowcount
        try:
            cur = json.loads((con.execute("SELECT apply_result_json FROM marg_push_staging "
                                          "WHERE id=?", (pid,)).fetchone() or [None])[0]
                             or "{}") or {}
        except ValueError:
            cur = {}
        cur["s243"] = dict(rule=RULE_APPLY, at=now_iso(), by="auto", days=mine,
                           superseded=[s["id"] for s in sup], flags_cleared=flags)
        con.execute("UPDATE marg_push_staging SET applied_by='auto', apply_result_json=? "
                    "WHERE id=?", (json.dumps(cur), pid))
        audit(con, "marg_push_staging", pid, "auto-apply",
              after=dict(rule=RULE_APPLY, file=(fname or "")[:80], md5=md5_8,
                         days=mine, ingested=[x.get("date") for x in (j.get("ingested") or [])
                                              if isinstance(x, dict)],
                         superseded=[s["id"] for s in sup], flags_cleared=flags),
              who="auto")
        con.commit()
        lines = [x["summary"]["line"] for x in (j.get("ingested") or [])
                 if isinstance(x, dict) and x.get("summary") and x["summary"].get("line")]
        return dict(verdict="APPLIED", rule=RULE_APPLY, applied=j.get("ingested"),
                    summary=lines, superseded=sup, flags_cleared=flags,
                    message=("Applied automatically: %%d day(s), %%d bill(s)%%s. %%s"
                             %% (len(days), sum(m["all_bills"] for m in mine.values()),
                                (" | %%d older pending report(s) superseded" %% len(sup))
                                if sup else "",
                                " ; ".join(lines) if lines else
                                "Report khaate mein chali gayi.")))
    except Exception as ex:                                  # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                    # noqa: BLE001
            pass
        try:
            audit(con, "marg_push_staging", pid, "auto-apply-error",
                  after=dict(rule="S243 newest-wins", error=str(ex)[:300]), who="auto")
            con.commit()
        except Exception:                                    # noqa: BLE001
            pass
        return None


''' % dict(off=OFF_FILE_DEFAULT) + H_OLD

# ---------------------------------------------------------------------------
#  P  the checker's apply, split at its prelude
# ---------------------------------------------------------------------------
P_OLD = ('    pid = (request.get_json(silent=True) or {}).get("id")\n'
         '    if not pid:\n'
         '        return jsonify(ok=False, error="no_id"), 400\n'
         '    con = db()\n'
         '    _marg_staging(con)\n'
         '    row = con.execute("SELECT * FROM marg_push_staging WHERE id=?",\n'
         '                      (pid,)).fetchone()\n')

P_NEW = ('    pid = (request.get_json(silent=True) or {}).get("id")\n'
         '    if not pid:\n'
         '        return jsonify(ok=False, error="no_id"), 400\n'
         '    return _marg_apply_core_s243(u, pid)\n'
         '\n'
         '\n'
         'def _marg_apply_core_s243(u, pid):\n'
         '    """' + MARK + '.  The body of the checker\'s Apply, lifted\n'
         '    off its login gate so the automatic apply on arrival and the button run\n'
         '    the SAME rule (D349).  u is {"user": <who>}; every write below records\n'
         '    that name.  Nothing in this body changed; only its first line did."""\n'
         '    con = db()\n'
         '    _marg_staging(con)\n'
         '    row = con.execute("SELECT * FROM marg_push_staging WHERE id=?",\n'
         '                      (pid,)).fetchone()\n')

# ---------------------------------------------------------------------------
#  L  the list route: hand the hub the S243 facts of each row
# ---------------------------------------------------------------------------
L_OLD = '                        ingested_count=len(_ar.get("ingested") or []),\n'
L_NEW = ('                        ingested_count=len(_ar.get("ingested") or []),\n'
         '                        auto=(_ar.get("s243") or None),\n')

# ---------------------------------------------------------------------------
#  D  the push handler, after the staging row commits.  Two known shapes.
# ---------------------------------------------------------------------------
D_BASE_OLD = ('        con.commit()\n'
              '        return jsonify(ok=True, verdict="ACCEPTED-FOR-REVIEW",\n'
              '                       id=cur.lastrowid, days=survey, not_filed=not_filed,\n'
              '                       bills=sum(len(d["bills"]) for d in rep["days"]),\n'
              '                       item_lines=total_items,\n'
              '                       message="Received: %d day(s), %d bill(s). NOTHING has "\n'
              '                               "entered the books -- Dr. Manoj will check and "\n'
              '                               "apply it on the workbench. Report pahunch "\n'
              '                               "gayi hai; abhi khaate mein nahi gayi."\n'
              '                               % (len(days), sum(len(d["bills"])\n'
              '                                                 for d in rep["days"])))\n')

# the S219 M1 shape: its D_NEW begins with these two lines and this comment
D_S219_HEAD = ('        con.commit()\n'
               '\n'
               '        # ---- S219 M1: THE SECOND ORDER ------------------------------------\n')

D_S243_HEAD = ('        con.commit()\n'
               '\n'
               '        # ---- S243 AUTO-APPLY, newest export wins --------------------------\n'
               '        # Applied the moment it arrives, filed day or not (owner, 13-Sep).\n'
               '        # Stands aside (None) when /root/finance/AUTOAPPLY_OFF exists, and\n'
               '        # then the code below runs exactly as it did before S243.\n'
               '        _a243 = _marg_autoapply_s243(con, cur.lastrowid, days_payload, rep,\n'
               '                                     f.filename)\n'
               '        if _a243 is not None:\n'
               '            return jsonify(ok=True, verdict=_a243["verdict"], id=cur.lastrowid,\n'
               '                           days=survey, not_filed=not_filed,\n'
               '                           bills=sum(len(d["bills"]) for d in rep["days"]),\n'
               '                           item_lines=total_items, auto=_a243,\n'
               '                           message=_a243["message"])\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(src):
    """Returns (new_text, status, shape). status: patched | already | refused:<why>."""
    if MARK in src:
        return src, "already", None
    for nm, old in (("H", H_OLD), ("P", P_OLD), ("L", L_OLD)):
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n), None
    n219, nbase = src.count(D_S219_HEAD), src.count(D_BASE_OLD)
    if n219 == 1 and nbase == 0:
        shape = "S219-present"
        d_old, d_new = D_S219_HEAD, D_S243_HEAD + D_S219_HEAD[len("        con.commit()\n"):]
    elif nbase == 1 and n219 == 0:
        shape = "S219-absent"
        d_old, d_new = D_BASE_OLD, D_S243_HEAD + D_BASE_OLD[len("        con.commit()\n"):]
    else:
        return src, ("refused: the push handler's closing block is neither the S219 "
                     "shape (%d) nor the base shape (%d) exactly once" % (n219, nbase)), None
    if src.count('def api_marg_push_apply():') != 1:
        return src, "refused: api_marg_push_apply is not defined exactly once", None
    if src.count('def _marg_apply_core_s243') != 0:
        return src, "refused: _marg_apply_core_s243 already exists without the mark", None
    out = (src.replace(H_OLD, H_NEW, 1).replace(P_OLD, P_NEW, 1)
           .replace(L_OLD, L_NEW, 1).replace(d_old, d_new, 1))
    return out, "patched", shape


def selftest(paths):
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  PASS ", name)
        else:
            bad += 1
            print("  FAIL ", name)

    for p in paths:
        s = io.open(p, encoding="utf-8").read()
        out, st, shape = patch_text(s)
        tag = os.path.basename(p)
        check("%s: patches (%s, shape %s)" % (tag, st, shape), st == "patched")
        if st != "patched":
            continue
        try:
            compile(out, p, "exec")
            check("  compiles", True)
        except SyntaxError as ex:
            check("  compiles (%s)" % ex, False)
        check("  mark present once", out.count(MARK) == 1)
        check("  core defined once, route calls it once",
              out.count("def _marg_apply_core_s243(u, pid):") == 1
              and out.count("return _marg_apply_core_s243(u, pid)") == 1
              and out.count('_marg_apply_core_s243({"user": "auto"}, pid)') == 1)
        check("  helpers land before the push route",
              out.find("def _marg_autoapply_s243(") < out.find("def api_marg_push():"))
        check("  the push handler calls the auto-apply once",
              out.count("_a243 = _marg_autoapply_s243(con, cur.lastrowid") == 1)
        check("  the pre-S243 closing block survives intact",
              (("# ---- S219 M1: THE SECOND ORDER" in out) if shape == "S219-present"
               else (out.count(D_BASE_OLD[len("        con.commit()\n"):]) == 1)))
        check("  OFF file named", OFF_FILE_DEFAULT in out)
        check("  the list hands the hub the S243 facts once",
              out.count('auto=(_ar.get("s243") or None),') == 1)
        check("  only additions: every original line still present",
              all(ln in out for ln in s.splitlines() if ln.strip()))
        _, st2, _ = patch_text(out)
        check("  second run is a no-op", st2 == "already")
    _, st3, _ = patch_text("x = 1\n")
    check("a stranger file is refused", st3.startswith("refused"))
    _, st4, _ = patch_text(H_OLD + P_OLD + D_BASE_OLD + D_S219_HEAD)
    check("both closing shapes at once is refused", st4.startswith("refused"))
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if argv and argv[0] == "--selftest":
        return selftest(argv[1:])
    out_path = TARGET + ".new"
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (TARGET, md5(raw)))
    new, st, shape = patch_text(src)
    if st == "already":
        print("ALREADY PATCHED -- nothing to do")
        return 0
    if st != "patched":
        print("REFUSED: %s -- nothing written" % st[len("refused: "):])
        return 2
    compile(new, TARGET, "exec")
    io.open(out_path, "w", encoding="utf-8", newline="\n").write(new)
    print("shape  %s" % shape)
    print("wrote %s md5 %s" % (out_path, md5(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
