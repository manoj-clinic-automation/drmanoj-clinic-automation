# ---- S228 LOSS DESK -----------------------------------------------------------
# The owner, 06-Sep-2026, at the S227 close: "a real assessment of the loss of
# pharmacy from my side, item and qty wise, for my record -- I do the play here."
# HIS page, nobody else's. He ticks the lines he accepts as a real loss; the page
# carries the loss at MRP and at cost; the high-value and high-volume lines sit on
# top so the play starts where the money is. When he is done he SHARES the ticked
# list with Darpan: an A4 portrait sheet of core data only -- item, shortage, MRP,
# loss at MRP, and a total -- frozen the moment it is made, kept on the server as
# the copy that was shared, and never editable afterwards. Darpan's answers may
# recover some of it; each recovery is logged against that shared list and the
# logs feed the next stock check.
# Darpan's lists in turns move here from Amir's board (the owner: "move from here
# to a place where I own it and get it done from Darpan"); the tranche engine
# itself is untouched -- this page drives the same endpoints.
LOSS_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_loss_tick (
  count_id INTEGER NOT NULL,
  item     TEXT NOT NULL,
  on_      INTEGER NOT NULL DEFAULT 1,
  by_user  TEXT,
  at       TEXT NOT NULL,
  PRIMARY KEY (count_id, item)
);
CREATE TABLE IF NOT EXISTS stock_loss_share (
  id       INTEGER PRIMARY KEY,
  count_id INTEGER NOT NULL,
  no       INTEGER NOT NULL,
  made_at  TEXT NOT NULL,
  made_by  TEXT,
  to_whom  TEXT NOT NULL DEFAULT 'Darpan',
  lines    TEXT NOT NULL,          -- FROZEN JSON, never rewritten
  total_p  INTEGER NOT NULL,
  unpriced INTEGER NOT NULL DEFAULT 0,
  md5      TEXT NOT NULL,
  pdf      TEXT
);
CREATE TABLE IF NOT EXISTS stock_loss_recovery (
  id       INTEGER PRIMARY KEY,
  share_id INTEGER NOT NULL,
  count_id INTEGER NOT NULL,
  item     TEXT NOT NULL,
  kind     TEXT NOT NULL,          -- FOUND | MONEY | ACCEPTED
  units    INTEGER,
  amount_p INTEGER,
  note     TEXT,
  by_user  TEXT,
  at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_loss_rec ON stock_loss_recovery(share_id);
"""

LOSS_HIGH_VOLUME_PACKS = 10        # 10 strips (or 10 pcs on a pack-1 item) short = a high-volume line


def _loss_rs(p_):
    """Money the way this page and its sheet print it: Indian grouping, and the
    paise only when there are paise -- the same words the PDF uses, so a figure
    never changes shape between the screen, the message and the print."""
    s = _r_rupees(p_)
    return s[:-3] if s.endswith(".00") else s


def _loss_ensure(con):
    con.executescript(LOSS_SCHEMA)


def _loss_ticks(con, cid):
    """The items the owner has ticked on THIS count, as a set."""
    return {r[0] for r in con.execute(
        "SELECT item FROM stock_loss_tick WHERE count_id=? AND on_=1", (cid,))}


def _loss_row(con, x, st):
    """One shortage, priced both ways, with the per-unit prices the print needs."""
    short = -int(x["diff"])
    mrp_u, msrc = _price_p(con, x["item"], st)
    cost_u = _rate_p(con, x["item"])
    loss_mrp = (-int(x["mrp_p"]) if (x["mrp_p"] is not None and x["mrp_p"] < 0) else None)
    loss_cost = (-int(x["cost_p"]) if (x["cost_p"] is not None and x["cost_p"] < 0) else None)
    return dict(item=x["item"], packing=x["packing"], pack=x["pack"], marg=x["marg"],
                counted=x["counted"], diff=x["diff"], short_units=short,
                short_text=_qw(short, x["pack"]), mrp_unit_p=mrp_u, mrp_source=msrc,
                cost_unit_p=cost_u, loss_mrp_p=loss_mrp, loss_cost_p=loss_cost,
                lane=x["lane"], lane_title=x["lane_title"], why=x["why"],
                word=(x["word"]["label"] if x.get("word") else ""),
                answer=((x["answer"] or {}).get("label") if x.get("answer") else ""),
                sold_fy=x.get("sold_fy"), last_sale=x.get("last_sale"),
                last_purchase=x.get("last_purchase"), salt=x.get("salt") or "",
                consumable=bool(x.get("consumable")), family=x.get("family"),
                life=x.get("life"))


def _loss_sections(rows, st):
    """HIGH VALUE first (the money), HIGH VOLUME next (the quantity), then the rest
    -- the owner: 'high-cost / high-volume on top'. A line appears once only."""
    major = int(st.get("major_p") or 100000)
    hv = [r for r in rows if r["loss_mrp_p"] is not None and r["loss_mrp_p"] >= major]
    seen = {r["item"] for r in hv}
    vol = [r for r in rows if r["item"] not in seen
           and r["short_units"] >= LOSS_HIGH_VOLUME_PACKS * max(1, int(r["pack"] or 1))]
    seen |= {r["item"] for r in vol}
    rest = [r for r in rows if r["item"] not in seen]
    hv.sort(key=lambda r: (-(r["loss_mrp_p"] or 0), r["item"]))
    vol.sort(key=lambda r: (-(r["short_units"] * 1.0 / max(1, int(r["pack"] or 1))), r["item"]))
    rest.sort(key=lambda r: (r["loss_mrp_p"] is None, -(r["loss_mrp_p"] or 0),
                             -(r["short_units"] * 1.0 / max(1, int(r["pack"] or 1))), r["item"]))
    return [dict(key="value", title="Where the money is",
                 blurb="Every shortage worth %s or more at MRP." % _loss_rs(major), rows=hv),
            dict(key="volume", title="Where the quantity is",
                 blurb="%d or more short, and not already above." % LOSS_HIGH_VOLUME_PACKS, rows=vol),
            dict(key="rest", title="The rest of the shortages",
                 blurb="Smaller lines, largest value first.", rows=rest)]


def _loss_recoveries(con, cid):
    out = {}
    for r in con.execute("SELECT id, share_id, item, kind, units, amount_p, note, by_user, at "
                         "FROM stock_loss_recovery WHERE count_id=? ORDER BY id", (cid,)):
        out.setdefault(int(r[1]), []).append(
            dict(id=r[0], item=r[2], kind=r[3], units=r[4], amount_p=r[5], note=r[6] or "",
                 by=r[7] or "", at=r[8], at_text=_r_stamp(r[8])))
    return out


def _loss_share_value(lines, recs):
    """What a shared list has recovered so far: money logged, plus stock found
    valued at the MRP that was ON the shared sheet -- never a fresh price."""
    unit = {l["item"]: (l.get("mrp_unit_p") or 0) for l in lines}
    money = sum(int(r["amount_p"] or 0) for r in recs if r["kind"] == "MONEY")
    found_u = sum(int(r["units"] or 0) for r in recs if r["kind"] == "FOUND")
    found_p = sum(int(r["units"] or 0) * unit.get(r["item"], 0) for r in recs if r["kind"] == "FOUND")
    return dict(money_p=money, found_units=found_u, found_p=found_p,
                recovered_p=money + found_p,
                answered=len({r["item"] for r in recs}))


def _loss_shares(con, cid):
    recs = _loss_recoveries(con, cid)
    out = []
    for r in con.execute("SELECT id, no, made_at, made_by, to_whom, lines, total_p, unpriced, md5 "
                         "FROM stock_loss_share WHERE count_id=? ORDER BY no", (cid,)):
        lines = json.loads(r[5])
        mine = recs.get(int(r[0]), [])
        out.append(dict(id=r[0], no=r[1], made_at=r[2], made_text=_r_stamp(r[2]), made_by=r[3] or "",
                        to_whom=r[4], lines=lines, items=len(lines), total_p=r[6], unpriced=r[7],
                        md5=r[8], recoveries=mine, got=_loss_share_value(lines, mine),
                        pdf="/finance/stock/api/loss/share/%d.pdf" % r[0]))
    return out


def _loss_board(con, cid):
    d = _pad_report_data(con, cid)
    if d is None:
        return None
    _loss_ensure(con)
    st = d["settings"]
    rows = [_loss_row(con, x, st) for x in d["differences"] if x["diff"] < 0]
    ticks = _loss_ticks(con, cid)
    for r in rows:
        r["ticked"] = r["item"] in ticks
    shares = _loss_shares(con, cid)
    onsheet = {}
    for sh in shares:
        for l in sh["lines"]:
            onsheet.setdefault(l["item"], (sh["no"], l))
    for r in rows:
        r["shared"] = r["item"] in onsheet
        if r["shared"]:
            no, l = onsheet[r["item"]]
            r["sheet_no"] = no
            r.update(short_units=l["short_units"], short_text=l["short_text"],
                     mrp_unit_p=l["mrp_unit_p"], loss_mrp_p=l["loss_mrp_p"],
                     cost_unit_p=l["cost_unit_p"], loss_cost_p=l["loss_cost_p"], frozen=True)
            # what has already come back ON THIS LINE, so a row never reads gross
            # while the top of the page reads net
            back = 0
            for sh in shares:
                for rec in sh["recoveries"]:
                    if rec["item"] != r["item"]:
                        continue
                    if rec["kind"] == "MONEY":
                        back += int(rec["amount_p"] or 0)
                    elif rec["kind"] == "FOUND":
                        back += int(rec["units"] or 0) * (l.get("mrp_unit_p") or 0)
            r["back_p"] = back or None
    # what is still IN HIS HANDS: never a line already handed over
    live = [r for r in rows if not r["shared"]]
    picked = [r for r in live if r["ticked"]]
    tot = dict(lines=len(rows), open_lines=len(live), ticked=len(picked),
               mrp_p=sum(r["loss_mrp_p"] or 0 for r in picked),
               cost_p=sum(r["loss_cost_p"] or 0 for r in picked),
               unpriced=sum(1 for r in picked if r["loss_mrp_p"] is None),
               all_mrp_p=sum(r["loss_mrp_p"] or 0 for r in live),
               all_cost_p=sum(r["loss_cost_p"] or 0 for r in live),
               all_unpriced=sum(1 for r in live if r["loss_mrp_p"] is None),
               whole_mrp_p=sum(r["loss_mrp_p"] or 0 for r in rows),
               recovered_p=sum(sh["got"]["recovered_p"] for sh in shares),
               shared_p=sum(sh["total_p"] for sh in shares))
    tot["standing_p"] = tot["shared_p"] - tot["recovered_p"]
    tr = _tranches(con, cid)
    taken = {i for t in tr for i in t["items"]}
    pool = dict(med=len([x for x in _tranche_pool(d, "med") if x["item"] not in taken]),
                ortho=len([x for x in _tranche_pool(d, "ortho") if x["item"] not in taken]))
    return dict(count_id=d["count_id"], day=d["day"], when=d["when"], as_on=d["as_on"],
                closed=d.get("closed"), sections=_loss_sections(rows, st), totals=tot,
                shares=shares, tranches=tr, pool=pool,
                reasons=[dict(n=i + 1, key=k, en=REASON_ENGLISH[k], hi=STAFF_REASONS.get(k, ""))
                         for i, k in enumerate(REASON_NUMBERS)],
                differences=[dict(item=x["item"], pack=x["pack"], marg=x["marg"], counted=x["counted"],
                                  answer=((x["answer"] or {}).get("label") if x.get("answer") else ""))
                             for x in d["differences"]],
                links=dict(desk="/finance/stock/page/desk?count=%d" % d["count_id"],
                           report="/finance/stock/page/report?count=%d" % d["count_id"],
                           amir=d["links"]["amir_page"]))


@bp.route("/page/loss")
def page_loss():
    """THE OWNER'S LOSS DESK (D389). His page: he ticks, the totals follow, the
    shared sheet is frozen. The checker only -- no staff eye on this."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    from flask import Response                                # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _loss_ensure(con)
    cid = request.args.get("count", "").strip()
    if not cid.isdigit():
        r = con.execute("SELECT id FROM stock_count WHERE unit=? AND id NOT IN "
                        "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1", (_unit,)).fetchone()
        cid = str(r[0]) if r else "0"
    try:
        with io.open(PAGE_LOSS, "r", encoding="utf-8") as fh:
            html = fh.read()
    except IOError:
        return jsonify(ok=False, error="missing", message="stock_loss.html is not beside stock_app.py"), 503
    boot = json.dumps(dict(count_id=int(cid), user=(u or {}).get("user") or "", checker=True))
    return Response(html.replace("/*__BOOT__*/", "window.BOOT=" + boot + ";"), mimetype="text/html")


@bp.route("/api/loss/<int:cid>")
def api_loss_board(cid):
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    d = _loss_board(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    return jsonify(ok=True, **d)


@bp.route("/api/loss/<int:cid>/tick", methods=["POST"])
def api_loss_tick(cid):
    """{items:[...], on:true|false}. A tick is the owner's, and only his."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _loss_ensure(con)
    b = request.get_json(silent=True) or {}
    on = 1 if b.get("on", True) else 0
    items = [str(i).strip() for i in (b.get("items") or []) if str(i).strip()]
    if not items:
        return jsonify(ok=False, error="empty", message="No item named."), 400
    who, at = (u or {}).get("user") or "", now_iso()
    for it in items:
        con.execute("INSERT INTO stock_loss_tick (count_id, item, on_, by_user, at) VALUES (?,?,?,?,?) "
                    "ON CONFLICT(count_id, item) DO UPDATE SET on_=excluded.on_, by_user=excluded.by_user, at=excluded.at",
                    (cid, it, on, who, at))
    con.commit()
    d = _loss_board(con, cid)
    return jsonify(ok=True, totals=(d or {}).get("totals"),
                   message="%d line%s %s." % (len(items), "" if len(items) == 1 else "s",
                                              "ticked" if on else "un-ticked"))


@bp.route("/api/loss/<int:cid>/share", methods=["POST"])
def api_loss_share(cid):
    """FREEZE the ticked lines into the sheet shared with Darpan: the JSON is
    written once and never rewritten, the PDF is built from it and kept on the
    server, and the md5 of the frozen JSON is the sheet's fingerprint."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    import hashlib                                            # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _loss_ensure(con)
    d = _loss_board(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    picked = [r for s in d["sections"] for r in s["rows"] if r["ticked"] and not r["shared"]]
    if not picked:
        already = any(r["ticked"] for s in d["sections"] for r in s["rows"])
        return jsonify(ok=False, error="empty",
                       message=("Every line you have marked is already on a sheet with him."
                                if already else
                                "Mark the lines you want on the sheet first.")), 400
    lines = [dict(item=r["item"], packing=r["packing"], pack=r["pack"], marg=r["marg"],
                  counted=r["counted"], short_units=r["short_units"], short_text=r["short_text"],
                  mrp_unit_p=r["mrp_unit_p"], mrp_source=r["mrp_source"],
                  loss_mrp_p=r["loss_mrp_p"], cost_unit_p=r["cost_unit_p"],
                  loss_cost_p=r["loss_cost_p"]) for r in picked]
    frozen = json.dumps(lines, sort_keys=True, separators=(",", ":"))
    md5 = hashlib.md5(frozen.encode("utf-8")).hexdigest()
    total = sum(l["loss_mrp_p"] or 0 for l in lines)
    unpriced = sum(1 for l in lines if l["loss_mrp_p"] is None)
    no = 1 + int(con.execute("SELECT COALESCE(MAX(no),0) FROM stock_loss_share WHERE count_id=?",
                             (cid,)).fetchone()[0])
    to_whom = (request.get_json(silent=True) or {}).get("to") or "Darpan"
    cur = con.execute("INSERT INTO stock_loss_share (count_id, no, made_at, made_by, to_whom, lines, "
                      "total_p, unpriced, md5) VALUES (?,?,?,?,?,?,?,?,?)",
                      (cid, no, now_iso(), (u or {}).get("user") or "", str(to_whom)[:40],
                       frozen, total, unpriced, md5))
    sid = int(cur.lastrowid)
    con.commit()
    kept = _loss_share_write(con, cid, sid)
    return jsonify(ok=True, share_id=sid, no=no, md5=md5[:8], kept=bool(kept),
                   pdf="/finance/stock/api/loss/share/%d.pdf" % sid,
                   message="Sheet %d made and frozen: %d item%s, %s at MRP. Print it for %s."
                           % (no, len(lines), "" if len(lines) == 1 else "s", _loss_rs(total), to_whom))


def _loss_share_row(con, sid):
    r = con.execute("SELECT id, count_id, no, made_at, made_by, to_whom, lines, total_p, unpriced, md5, pdf "
                    "FROM stock_loss_share WHERE id=?", (sid,)).fetchone()
    if not r:
        return None
    return dict(id=r[0], count_id=r[1], no=r[2], made_at=r[3], made_text=_r_stamp(r[3]),
                made_by=r[4] or "", to_whom=r[5], lines=json.loads(r[6]), total_p=r[7],
                unpriced=r[8], md5=r[9], pdf=r[10])


def _loss_share_pdf(con, sid):
    """The bytes of a shared sheet: the kept copy if it is on disk, else built
    from the FROZEN json and kept now. Never from live prices."""
    s = _loss_share_row(con, sid)
    if s is None:
        return None, None
    d = os.path.join(_pad_archive_dir(con), "loss_shares")
    path = os.path.join(d, "%s.pdf" % s["md5"])
    if os.path.exists(path):
        try:
            with io.open(path, "rb") as fh:
                return fh.read(), s
        except IOError:
            pass
    import pad_receipt                                        # noqa: PLC0415
    pdf = pad_receipt.render_loss_share(s)
    try:
        os.makedirs(d, exist_ok=True)
        with io.open(path, "wb") as fh:
            fh.write(pdf)
        con.execute("UPDATE stock_loss_share SET pdf=? WHERE id=? AND pdf IS NULL",
                    ("%s.pdf" % s["md5"], sid))
        con.commit()
    except (IOError, OSError, sqlite3.Error):
        pass
    return pdf, s


def _loss_share_write(con, cid, sid):
    try:
        pdf, _s = _loss_share_pdf(con, sid)
        return bool(pdf)
    except Exception:                                         # noqa: BLE001
        return False


@bp.route("/api/loss/share/<int:sid>.pdf")
def api_loss_share_pdf(sid):
    """The A4 PORTRAIT sheet for Darpan: item, shortage, MRP, loss at MRP, total.
    Core data only -- the owner: 'a page he can hold and answer'."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    from flask import Response                                # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    _loss_ensure(con)
    pdf, s = _loss_share_pdf(con, sid)
    if pdf is None:
        return jsonify(ok=False, error="not_found", message="No such sheet."), 404
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="LOSS_SHEET_%d_count%d.pdf"'
                                                    % (s["no"], s["count_id"])})


@bp.route("/api/loss/<int:cid>/recovery", methods=["POST"])
def api_loss_recovery(cid):
    """{share_id, item, kind: FOUND|MONEY|ACCEPTED, units, amount, note} -- what
    came back after the sheet was shared. Append-only; the sheet never changes."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    con = _db()
    ensure_schema(con)
    _loss_ensure(con)
    b = request.get_json(silent=True) or {}
    sid = int(b.get("share_id") or 0)
    s = _loss_share_row(con, sid)
    if s is None or int(s["count_id"]) != cid:
        return jsonify(ok=False, error="not_found", message="No such sheet."), 404
    item = (b.get("item") or "").strip()
    kind = (b.get("kind") or "").strip().upper()
    if kind not in ("FOUND", "MONEY", "ACCEPTED"):
        return jsonify(ok=False, error="bad_kind", message="Found, recovered or accepted."), 400
    if item not in {l["item"] for l in s["lines"]}:
        return jsonify(ok=False, error="not_on_sheet", message="That item is not on this sheet."), 400
    units = amount_p = None
    if kind == "FOUND":
        try:
            units = int(round(float(b.get("units") or 0)))
        except (TypeError, ValueError):
            units = 0
        if units <= 0:
            return jsonify(ok=False, error="bad_units", message="How many were found?"), 400
    if kind == "MONEY":
        try:
            amount_p = int(round(float(b.get("amount") or 0) * 100))
        except (TypeError, ValueError):
            amount_p = 0
        if amount_p <= 0:
            return jsonify(ok=False, error="bad_amount", message="How much was recovered?"), 400
    con.execute("INSERT INTO stock_loss_recovery (share_id, count_id, item, kind, units, amount_p, "
                "note, by_user, at) VALUES (?,?,?,?,?,?,?,?,?)",
                (sid, cid, item, kind, units, amount_p, (b.get("note") or "").strip()[:300] or None,
                 (u or {}).get("user") or "", now_iso()))
    con.commit()
    d = _loss_board(con, cid)
    word = {"FOUND": "Found on the shelf", "MONEY": "Recovered", "ACCEPTED": "Accepted as lost"}[kind]
    return jsonify(ok=True, totals=(d or {}).get("totals"),
                   shares=(d or {}).get("shares"), message="%s: %s." % (word, item))
# ---- end S228 LOSS DESK -------------------------------------------------------
