#!/usr/bin/env python3
"""make_s724.py -- kit S724 (session 390, the parent, 06-Nov-2026), F-1128.
   python make_s724.py <live staff_register.py> <out> [--expect <md5 of out>]
Applies the kit's COUNTED edits to the live bytes (each must match exactly once) and writes the result.
  1  the month-end flow opens on the month just ended -- the lock desk's own default (_default_salary_ym) -- not on the
     running calendar month (F-1128: October's sheets read 'approved 2026-10-05 20:49', pressed on a flow page that had
     opened on October while September was being closed).
  2  a Sheet 1 / Sheet 2 approval keeps a fingerprint of the month's computed figures (pack_approval.fig_hash); an
     approval whose figures have changed since -- or that has no fingerprint -- no longer counts: the approve button
     comes back with the reason, and the lock refuses it."""
import hashlib, sys

EDITS = [
# 1 the flow's default month
('''def _flow_ym():
    ym = (request.args.get("ym") or _today()[:7]).strip()
    return ym if _valid_ym(ym) else _today()[:7]''',
'''def _flow_ym():
    # S724 (F-1128): the month just ended, as the lock desk opens -- never the running month by default
    ym = (request.args.get("ym") or _default_salary_ym()).strip()
    return ym if _valid_ym(ym) else _default_salary_ym()'''),
# 2a the table and the fingerprint
('''def _pack_table(con):
    con.execute("CREATE TABLE IF NOT EXISTS pack_approval ("
                "ym TEXT NOT NULL, sheet TEXT NOT NULL, approved_by TEXT, "
                "approved_ts TEXT, PRIMARY KEY (ym, sheet))")


def pack_status(ym):
    con = get_db(); _pack_table(con)
    rows = {r["sheet"]: dict(r) for r in con.execute(
        "SELECT * FROM pack_approval WHERE ym=?", (ym,))}
    con.close()
    return rows''',
'''def _pack_table(con):
    con.execute("CREATE TABLE IF NOT EXISTS pack_approval ("
                "ym TEXT NOT NULL, sheet TEXT NOT NULL, approved_by TEXT, "
                "approved_ts TEXT, PRIMARY KEY (ym, sheet))")
    # S724 (F-1128): the fingerprint of the figures an approval was given on
    if "fig_hash" not in [r[1] for r in con.execute("PRAGMA table_info(pack_approval)")]:
        con.execute("ALTER TABLE pack_approval ADD COLUMN fig_hash TEXT")
        con.commit()


def _fig_default(o):
    if isinstance(o, (set, frozenset)):
        return sorted(o, key=str)
    return str(o)


def _fig_hash(staff):
    """S724: one fingerprint of every computed figure of the month, staff by staff (compute()['staff'])."""
    return hashlib.sha256(json.dumps(staff, sort_keys=True, default=_fig_default,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def pack_status(ym, staff=None):
    """The month's two approvals. S724: given the month's computed staff rows, an approval whose fingerprint is not
    theirs (the figures changed after it, or it was given before fingerprints) is left out and named in '_stale'."""
    con = get_db(); _pack_table(con)
    rows = {r["sheet"]: dict(r) for r in con.execute(
        "SELECT * FROM pack_approval WHERE ym=?", (ym,))}
    con.close()
    if staff is not None:
        h = _fig_hash(staff)
        stale = {k: v for k, v in rows.items() if (v.get("fig_hash") or "") != h}
        for k in stale:
            rows.pop(k, None)
        rows["_stale"] = stale
    return rows


def _stale_note(st):
    """S724: one line naming an approval that no longer holds, or ''."""
    s = st.get("_stale") or {}
    if not s:
        return ""
    return ("%s approved by %s on %s, but the month's figures have changed since (or it was given before figures were "
            "recorded with an approval) \\u2014 open it and approve again." % (
                " and ".join({"sheet1": "Sheet 1", "sheet2": "Sheet 2"}.get(k, k) for k in sorted(s)),
                ", ".join(sorted(set((v.get("approved_by") or "?") for v in s.values()))),
                ", ".join(sorted(set((v.get("approved_ts") or "")[:16] for v in s.values())))))'''),
# 2b the flow page (home)
('''def salary_flow():
    ym = _flow_ym()
    st = pack_status(ym)''',
'''def salary_flow():
    ym = _flow_ym()
    st = pack_status(ym)
    try:                                   # S724: an approval holds only on the figures it was given on
        _Pf, _ = _policy_module()
        if _Pf is not None:
            os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
            st = pack_status(ym, _Pf.compute(ym)["staff"])
    except Exception:
        st = {k: v for k, v in st.items() if (v.get("fig_hash") or "")} if isinstance(st, dict) else st'''),
('''    return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym, v0=v0,
                                  s1=st.get("sheet1"), s2=st.get("sheet2"), remarks=remarks,
                                  msg=request.args.get("msg", ""), err="")''',
'''    return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym, v0=v0,
                                  s1=st.get("sheet1"), s2=st.get("sheet2"), remarks=remarks,
                                  msg=request.args.get("msg", ""), err=_stale_note(st))'''),
# 2c the approve press keeps the fingerprint
('''    if not _valid_ym(ym) or sheet not in ("sheet1", "sheet2"):
        return redirect(APP_PREFIX + "/salary/flow?ym=" + (ym or _today()[:7]))
    con = get_db(); _pack_table(con)
    con.execute("INSERT OR REPLACE INTO pack_approval (ym, sheet, approved_by, "
                "approved_ts) VALUES (?,?,?,?)", (ym, sheet, u["user"], _now()))''',
'''    if not _valid_ym(ym) or sheet not in ("sheet1", "sheet2"):
        return redirect(APP_PREFIX + "/salary/flow?ym=" + (ym if _valid_ym(ym) else _default_salary_ym()))
    P, perr = _policy_module()             # S724: the approval keeps the fingerprint of the figures it was given on
    try:
        if P is None:
            raise RuntimeError(perr)
        os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
        fig = _fig_hash(P.compute(ym)["staff"])
    except Exception as e:
        return redirect(APP_PREFIX + "/salary/flow?ym=%s&msg=%s" % (
            ym, "NOT approved: the month's figures could not be worked out (%s)" % type(e).__name__))
    con = get_db(); _pack_table(con)
    con.execute("INSERT OR REPLACE INTO pack_approval (ym, sheet, approved_by, "
                "approved_ts, fig_hash) VALUES (?,?,?,?,?)", (ym, sheet, u["user"], _now(), fig))'''),
# 2d the sheet pages: the stale approval shows its approve strip again, with the reason
('''        back = "%s/salary/flow?ym=%s" % (APP_PREFIX, ym)
        st = pack_status(ym)

        def _apv(sheet, label):''',
'''        back = "%s/salary/flow?ym=%s" % (APP_PREFIX, ym)
        st = pack_status(ym, res["staff"])      # S724: only an approval of these very figures counts

        def _apv(sheet, label):'''),
('''            return ('<div class="apvbar"><span>&#9997; %s — reviewed and correct?</span>'
                    '<form method="POST" action="%s/salary/flow/approve">\'''',
'''            if sheet in (st.get("_stale") or {}):
                _o = st["_stale"][sheet]
                label = "%s (the approval by %s on %s no longer holds: the figures changed after it)" % (
                    label, html.escape(_o.get("approved_by") or "?"), html.escape((_o.get("approved_ts") or "")[:16]))
            return ('<div class="apvbar"><span>&#9997; %s — reviewed and correct?</span>'
                    '<form method="POST" action="%s/salary/flow/approve">\''''),
# 2e the lock desk shows what holds
('''    st_pack = pack_status(ym)
    lr = dict(lr) if lr else None''',
'''    st_pack = pack_status(ym, res_staff if res_staff else None)     # S724
    if not msg and st_pack.get("_stale"):
        msg = _stale_note(st_pack)
    lr = dict(lr) if lr else None'''),
# 2f the lock refuses an approval that is not of these figures
('''    if not res.get("ledger_closed", False):
        return _render_salary(ym, u,
            "The staff ledger has not been closed for this month''',
'''    if int(P.load_settings().get("require_pack_approval", 1)):        # S724 (F-1128)
        _st2 = pack_status(ym, res["staff"])
        if not (_st2.get("sheet1") and _st2.get("sheet2")):
            return _render_salary(ym, u, _stale_note(_st2) or
                "Sheet 1 / Sheet 2 of the month-end flow are not approved yet "
                "\\u2014 review and approve the pack, then lock.")
    if not res.get("ledger_closed", False):
        return _render_salary(ym, u,
            "The staff ledger has not been closed for this month'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    s = open(src, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS, 1):
        n = s.count(a)
        if n != 1:
            print("make_s724: edit %d matches %d times (must be 1) -- nothing written" % (i, n))
            return 2
        s = s.replace(a, b)
    data = s.encode("utf-8")
    if "--expect" in sys.argv:
        want = sys.argv[sys.argv.index("--expect") + 1]
        if hashlib.md5(data).hexdigest() != want:
            print("make_s724: the result is %s, not the expected %s -- nothing written" % (hashlib.md5(data).hexdigest(), want))
            return 3
    open(out, "wb").write(data)
    print("make_s724: %d edits applied -> %s (%s)" % (len(EDITS), out, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
