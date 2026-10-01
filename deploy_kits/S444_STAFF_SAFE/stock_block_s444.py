


# ---- S444_STAFF_SAFE begin (01-Oct-2026, F-672 / D647): Amir's one door -- what he owes on the count, read for "Amir ka kaam" ----
# The Marg vouchers of a count wait on his board (/finance/stock/page/amir); until S444 nothing on his own page said so. amir_day
# reads amir_duties() for its step 6 "Marg sudhar" card; his visits to the board are remembered (the owner's Needs-you line d);
# the board carries a BACK bar to /finance/amir and the signed-in name. Read-only but for the board-open row.
_S444_RENAMES_CACHE = {}                                       # count_id -> (time, ready, open) -- the proof costs a full report read


def _s444_board_ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS stock_board_open (id INTEGER PRIMARY KEY, at TEXT NOT NULL, by_user TEXT, "
                "count_id INTEGER, checker INTEGER NOT NULL DEFAULT 0)")


def _s444_board_opened(con, cid, u):
    """One row per opening of Amir's board: who, when, which count (the checker's own look is marked and never counts as his)."""
    try:
        _s444_board_ensure(con)
        con.execute("INSERT INTO stock_board_open (at, by_user, count_id, checker) VALUES (?,?,?,?)",
                    (now_iso(), (u or {}).get("user") or "", int(cid), 1 if _has_role(u, "checker") else 0))
        con.commit()
    except Exception:                                          # noqa: BLE001 -- the board never waits for its own record
        pass


def amir_vouchers_open(con):
    """[{count_id, made, open, ortho, dawa, issue, receive, made_first, last_touch, url}] -- per count, the Marg vouchers MADE and
    not yet marked entered (the newest stock_voucher_entered row of a batch wins; an empty number clears it -- _voucher_state's
    rule). Orthotic = a voucher carrying an Orthotics line. Two cheap queries, no report read."""
    _voucher_ensure(con)
    _s444_board_ensure(con)
    out = []
    batches = {}
    for cid, rno, kind, bno, sec, made in con.execute("SELECT count_id, round_no, kind, batch_no, section, made_at FROM stock_voucher_line"):
        b = batches.setdefault((cid, rno, kind, bno), {"secs": set(), "made": made})
        b["secs"].add(sec or "")
        if made and (not b["made"] or made < b["made"]):
            b["made"] = made
    entered, last_ent = {}, {}
    for cid, rno, kind, bno, no, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered ORDER BY id"):
        entered[(cid, rno, kind, bno)] = bool((no or "").strip())
        if at and (not last_ent.get(cid) or at > last_ent[cid]):
            last_ent[cid] = at
    opened = {r[0]: r[1] for r in con.execute("SELECT count_id, MAX(at) FROM stock_board_open WHERE checker=0 GROUP BY count_id")}
    for cid in sorted({k[0] for k in batches}):
        mine = [(k, v) for k, v in batches.items() if k[0] == cid]
        op = [(k, v) for k, v in mine if not entered.get(k)]
        ortho = sum(1 for _k, v in op if "Orthotics" in v["secs"])
        touched = [x for x in (last_ent.get(cid), opened.get(cid)) if x]
        out.append(dict(count_id=cid, made=len(mine), open=len(op), ortho=ortho, dawa=len(op) - ortho,
                        issue=sum(1 for k, _v in op if k[2] == "ISSUE"), receive=sum(1 for k, _v in op if k[2] == "RECEIVE"),
                        made_first=min((v["made"] for _k, v in op if v["made"]), default=None),
                        last_touch=max(touched) if touched else None,
                        url="/finance/stock/page/amir?count=%d#vouchers" % cid))
    return out


def _s444_renames(con, cid):
    """(ready, open) for the newest count: the renames show ONLY once the proof is green (S437 gate, _proof_state 'done'). The proof
    reads the whole report (~3 s), so it is asked only when no voucher of the count is still open, and kept 10 minutes."""
    now = dt.datetime.now().timestamp()
    hit = _S444_RENAMES_CACHE.get(cid)
    if hit and now - hit[0] < 600:
        return hit[1], hit[2]
    ready, n_open = False, 0
    try:
        d = _pad_report_data(con, cid)
        if d is not None:
            ready = (_proof_state(con, d).get("state") == "done")
        if ready:
            import item_alias                                  # noqa: PLC0415
            n_open = sum(1 for r in item_alias.rows(con) if r.get("state") in ("planned", "amber"))
    except Exception:                                          # noqa: BLE001
        ready, n_open = False, 0
    _S444_RENAMES_CACHE[cid] = (now, ready, n_open)
    return ready, n_open


def amir_duties(con):
    """What "Amir ka kaam" step 6 shows: {counts: amir_vouchers_open(), renames: {count_id, ready, open, url} | None}."""
    counts = amir_vouchers_open(con)
    renames = None
    try:
        root = _newest_root(con)
        if root and not any(c["count_id"] == root and c["open"] for c in counts):
            ready, n_open = _s444_renames(con, int(root))
            renames = dict(count_id=int(root), ready=ready, open=n_open, url="/finance/stock/page/amir?count=%d#renames" % int(root))
    except Exception:                                          # noqa: BLE001
        renames = None
    return dict(counts=counts, renames=renames)


def _s444_board_html(html, user):
    """The board's BACK bar to "Amir ka kaam" and the signed-in name; the page is reached only through his step 6 (no tile)."""
    bar = ('<div id="s444bar" style="position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;background:#1f3864;color:#fff;'
           'padding:6px 10px;margin:0 0 10px;border-radius:0 0 8px 8px"><a id="s444back" href="/finance/amir" style="display:flex;align-items:center;'
           'justify-content:center;min-height:44px;padding:0 20px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;'
           'text-decoration:none">&larr; BACK</a><span style="margin-left:auto;font-size:13px;opacity:.9">Signed in: %s</span></div>'
           % (str(user or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")))
    anchor = '<body><div class="wrap">'
    if html.count(anchor) != 1:
        return html
    return html.replace(anchor, anchor + bar, 1)
# ---- S444_STAFF_SAFE end ------------------------------------------------------------------------------------------------------------------
