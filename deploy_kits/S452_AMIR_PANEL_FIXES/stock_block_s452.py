# ---- S452_AMIR_PANEL_FIXES begin (02-Oct-2026): Amir's board in Roman Hindi; "Rate daalo" on his card; medicine vouchers 12 a visit ----
# The owner, 02-Oct: "Make it 10, 12 vouchers for each visit so that the work is done quickly and it does not stall ... He can optionally
# add and enter even more vouchers if he has time."
#   * Stage C releases amir.vouchers_per_visit (12) a visit; "Aur voucher kholiye" (POST /api/pad/amir/<count>/more) opens the next lot
#     at once, as often as he taps, until none is left -- each tap audited in stock_stage_event (who, when, how many). D649's order stays:
#     nothing of Stage C before Stage B is verified. The proof no longer holds a lot back: every closing-stock export checks whatever he
#     has entered so far and names any item still wrong, with its voucher; an unverified lot stays listed and the next visit opens 12 more.
#   * amir_rate_due(con): the orthotic short lines of the newest close-by-rule run with no selling rate, less those that now have one --
#     in Marg's own item export (the spine, S331: the newest s_rate or MRP above 0) or in the server's rate table (stock_rate). What the
#     spine says is kept in finance.db (stock_rate_marg, refreshed whenever the list is read) so DUTY_MAP's amir.rate_entry, one SELECT
#     on finance.db, reads the same thing. The card's "N item ka rate Marg mein daalna hai"; the board's (b).
#   * The board's words are Roman Hindi (the reasons, an answer's label); a salt line Marg already shows leaves block (a).
S452_REASONS_ROMAN = {"count_error": "Ginti mein galti", "not_billed": "Bill nahi bana", "breakage": "Toot / kharab", "expiry": "Expiry mein gaya",
                      "sample": "Sample / doctor ko diya", "return": "Wapsi ka maal", "dont_know": "Pata nahi"}
S452_RATE_DDL = ("CREATE TABLE IF NOT EXISTS stock_rate_marg (item TEXT PRIMARY KEY, s_rate TEXT, mrp TEXT, as_on TEXT, seen_at TEXT NOT NULL)")


def _s452_pos(v):
    try:
        return float(v) > 0
    except (TypeError, ValueError):
        return False


def _s452_marg_rates(con, items):
    """{item: (s_rate, mrp, as_on)} -- the newest S.RATE / MRP facts of Marg's item export (the spine, read only), mirrored into
    stock_rate_marg (a row rewritten only when Marg's figure moved)."""
    out = {}
    if not items or not STOCK_STATEMENT_OK:
        return out
    try:
        P = _ss.Prices(dt.date.today().isoformat())
    except Exception:                                          # noqa: BLE001
        return out
    if not P.ok:
        return out
    try:
        for it in items:
            names = P._names.get(P.key(it)) or [it]
            q = ",".join("?" * len(names))
            r = P.con.execute("SELECT MAX(as_on) FROM sp_item_fact WHERE name IN (%s) AND fact IN ('s_rate','mrp')" % q, names).fetchone()
            if not r or not r[0]:
                continue
            f = {k: v for k, v in P.con.execute("SELECT fact, value FROM sp_item_fact WHERE name IN (%s) AND fact IN ('s_rate','mrp') AND as_on=?" % q,
                                                names + [r[0]])}
            out[it] = (f.get("s_rate"), f.get("mrp"), r[0])
    except Exception:                                          # noqa: BLE001
        pass
    finally:
        try:
            P.con.close()
        except Exception:                                      # noqa: BLE001
            pass
    try:
        con.execute(S452_RATE_DDL)
        moved = 0
        for it, (sr, mrp, as_on) in out.items():
            old = con.execute("SELECT s_rate, mrp, as_on FROM stock_rate_marg WHERE item=?", (it,)).fetchone()
            if old is None or (old[0], old[1], old[2]) != (sr, mrp, as_on):
                con.execute("INSERT OR REPLACE INTO stock_rate_marg (item, s_rate, mrp, as_on, seen_at) VALUES (?,?,?,?,?)", (it, sr, mrp, as_on, now_iso()))
                moved += 1
        if moved:
            con.commit()
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _s452_rates_open(con, tasks):
    """The (b) Rate daalo list less every item that now has a rate -- Marg's own (the spine) or the server's (stock_rate) -- sorted."""
    try:
        have = {str(r[0]) for r in con.execute("SELECT item FROM stock_rate WHERE COALESCE(rate_p, 0) > 0")}
    except Exception:                                          # noqa: BLE001
        have = set()
    marg = _s452_marg_rates(con, [t.get("item") for t in tasks if t.get("item") and t.get("item") not in have])
    have |= {it for it, (sr, mrp, _a) in marg.items() if _s452_pos(sr) or _s452_pos(mrp)}
    return sorted([t for t in tasks if t.get("item") not in have], key=lambda r: r["item"])


def amir_rate_due(con):
    """[{item, packing}] -- the newest close-by-rule run's orthotic short lines with no selling rate that Marg still does not carry."""
    try:
        r = con.execute("SELECT groups FROM stock_writeoff_run WHERE kind='ortho_close' ORDER BY id DESC LIMIT 1").fetchone()
        g = json.loads(r[0] or "{}") if r else {}
    except Exception:                                          # noqa: BLE001
        return []
    tasks = [dict(item=x.get("item"), packing=x.get("packing") or "") for x in g.get("ortho_loss", []) if x.get("item") and x.get("mrp_p") is None]
    return _s452_rates_open(con, tasks)


def _s452_board_roman(b):
    """Amir's board JSON in Roman Hindi: the reasons' words and an answer's label; block (a) without the lines Marg already shows."""
    rev = {v: S452_REASONS_ROMAN.get(k, v) for k, v in STAFF_REASONS.items()}
    for x in b.get("reasons") or []:
        x["hi"] = S452_REASONS_ROMAN.get(x.get("key"), x.get("hi"))
    for x in b.get("differences") or []:
        if x.get("answer") in rev:
            x["answer"] = rev[x["answer"]]
    b["salt_fix"] = [s for s in (b.get("salt_fix") or []) if not s.get("marg_done")]
    return b


def _s452_release(con, root, who, why):
    """The next lot of Stage C -- amir.vouchers_per_visit, oldest round first -- audited in stock_stage_event (who, when, how many)."""
    batches = _s446_batches(con, root)
    ent = _s446_entered(con, root)
    ortho = {k for k, b in batches.items() if "Orthotics" in b["secs"]}
    med = sorted([k for k in batches if k not in ortho], key=lambda k: (k[0], k[1] != "ISSUE", k[2]))
    released = set()
    for r in con.execute("SELECT ref FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release'", (root,)):
        released.update(_s446_unkey(x) for x in (r[0] or "").split(",") if x)
    per = max(1, _s446_setting(con, "amir.vouchers_per_visit", 12))
    nxt = [k for k in med if k not in released and k not in ent][:per]
    if not nxt:
        return 0
    _s446_mark(con, root, "C", "release", ",".join(_s446_key(k) for k in nxt), detail=json.dumps(dict(by=who, n=len(nxt), why=why, kit="S452")))
    return len(nxt)


@bp.route("/api/pad/amir/<int:cid>/more", methods=["POST"])
def api_s452_more(cid):
    """'Aur voucher kholiye': the next lot of medicine vouchers at once (Stage C only)."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    _s446_ensure(con)
    st = amir_stage(con, cid)
    if not st or st.get("stage") != "C":
        return jsonify(ok=False, error="not_stage_c", message="Dawa ke voucher abhi nahi -- pehle orthotic ka kaam poora hoga."), 409
    n = _s452_release(con, st["count_id"], (u or {}).get("user") or "", "more")
    if not n:
        return jsonify(ok=False, error="none_left", message="Aur koi voucher baaki nahi."), 409
    return jsonify(ok=True, released=n, message="%d voucher aur khul gaye." % n)
# ---- S452_AMIR_PANEL_FIXES end ------------------------------------------------------------------------------------------------------------
