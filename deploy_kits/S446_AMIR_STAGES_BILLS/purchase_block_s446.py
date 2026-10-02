


# ==========================================================================================================================================
# S446_AMIR_STAGES_BILLS (02-Oct-2026, D650 / F-680): the scanned medicine bills as FILES for Marg's own digital entry; Marg overrules
# Sarvam; the earlier month's unfinished work above the payment sheet.
#   * scans_to_enter(con): every captured pharmacy scan not yet linked to a Marg bill, oldest first -- Amir's step 2 lists them.
#   * GET /finance/purchase/api/scan-file/<id>      the stored scan, read only from the asset app's store, named
#                                                    <SUPPLIER>_<billno>_<dd-mm-yyyy>.pdf -- Amir and the owner only (setting
#                                                    purchase.scan_file_users, default 'amir'; the medical checker always)
#   * GET /finance/purchase/api/scan-files/today.zip  today's of them, one zip
#   * The trial (setting purchase.sarvam_trial_until): for every scan LINKED to a Marg bill, field by field -- supplier (alias-aware),
#     bill number (digit tail), date, total (within Rs 1), and the item lines Sarvam read (name, qty, rate, batch, expiry) against
#     Marg's item-wise lines -- kept in purchase_sarvam_check. Wherever they differ Marg's figure is the bill's; this comparison
#     only counts. The owner: one line on the Scan links page, a monthly Needs-you line, the drill-down /page/sarvam?month=.
#   * The payment sheet: "Pichhle mahine ka baaki: N" above the month while an earlier month holds unsent supplier messages
#     or NEFT lines with no NEFT recorded; one tap opens that month.
# ==========================================================================================================================================
S446_SARVAM_DDL = ("CREATE TABLE IF NOT EXISTS purchase_sarvam_check (asset_bill_id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, month TEXT, "
                   "checked_at TEXT NOT NULL, supplier_ok INTEGER, billno_ok INTEGER, date_ok INTEGER, total_ok INTEGER, items_read INTEGER, "
                   "items_wrong INTEGER, all_ok INTEGER, detail TEXT)")


def _s446_setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]) if r and r[0] not in (None, "") else default
    except sqlite3.Error:
        return default


def _s446_uploads():
    return os.environ.get("ASSETS_UPLOADS") or os.path.join(os.path.dirname(os.path.abspath(_assets_db)), "uploads")


def _s446_linked(con):
    try:
        return {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        return set()


def _s446_name(r):
    sup = re.sub(r"[^A-Z0-9]+", "_", str(r.get("vendor") or "SUPPLIER").upper()).strip("_")[:40] or "SUPPLIER"
    bno = re.sub(r"[^A-Za-z0-9]+", "", str(r.get("bill_no") or "")) or "nobill"
    d = _iso(r.get("bill_date")) or _iso_any(r.get("bill_date")) or ""
    return "%s_%s_%s.pdf" % (sup, bno, (d[8:10] + "-" + d[5:7] + "-" + d[:4]) if len(d) == 10 else "nodate")


def scans_to_enter(con):
    """[{id, stamp, vendor, bill_no, bill_date, created_at, name, today}] -- captured pharmacy scans with no Marg bill linked yet."""
    acon = _assets_con()
    if acon is None:
        return []
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        rows = [dict(r) for r in acon.execute(
            "SELECT id, stamp_no, vendor, bill_no, bill_date, created_at, source_stored%s FROM bills WHERE kind='Pharmacy' AND status='captured' "
            "ORDER BY created_at, id" % (", dup_of" if "dup_of" in cols else ""))]
    finally:
        acon.close()
    linked = _s446_linked(con)
    today = dt.date.today().isoformat()
    out = []
    for r in rows:
        if int(r["id"]) in linked or r.get("dup_of"):
            continue
        out.append(dict(id=int(r["id"]), stamp=r.get("stamp_no") or "", vendor=r.get("vendor") or "", bill_no=r.get("bill_no") or "",
                        bill_date=_iso(r.get("bill_date")) or _iso_any(r.get("bill_date")) or "", created_at=r.get("created_at") or "",
                        name=_s446_name(r), today=str(r.get("created_at") or "")[:10] == today))
    return out


def _s446_files_ok(con, u):
    if _is_doctor(u):
        return True
    who = str((u or {}).get("user") or "").strip().lower()
    allow = {x.strip().lower() for x in _s446_setting(con, "purchase.scan_file_users", "amir").split(",") if x.strip()}
    return bool(who) and who in allow


def _s446_file_bytes(sid):
    """(name, bytes) of one captured pharmacy scan -- read only, from the asset app's store; None when it is not one."""
    acon = _assets_con()
    if acon is None:
        return None
    try:
        r = acon.execute("SELECT id, vendor, bill_no, bill_date, source_stored FROM bills WHERE id=? AND kind='Pharmacy' AND status='captured'",
                         (int(sid),)).fetchone()
    finally:
        acon.close()
    if r is None or not r["source_stored"]:
        return None
    base = os.path.realpath(_s446_uploads())
    p = os.path.realpath(os.path.join(base, os.path.basename(str(r["source_stored"]))))
    if not p.startswith(base + os.sep) or not os.path.isfile(p):
        return None
    with open(p, "rb") as fh:
        return _s446_name(dict(r)), fh.read()


@bp.route("/api/scan-file/<int:sid>")
def api_s446_scan_file(sid):
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    if not _s446_files_ok(con, u):
        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")
    got = _s446_file_bytes(sid)
    if got is None:
        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404
    from flask import Response                                 # noqa: PLC0415
    return Response(got[1], mimetype="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % got[0], "Cache-Control": "no-store"})


@bp.route("/api/scan-files/today.zip")
def api_s446_scan_zip():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    if not _s446_files_ok(con, u):
        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")
    import zipfile                                              # noqa: PLC0415
    from flask import Response                                 # noqa: PLC0415
    buf = io.BytesIO()
    names = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for s in scans_to_enter(con):
            if not s["today"]:
                continue
            got = _s446_file_bytes(s["id"])
            if got is None:
                continue
            n = got[0]
            while n in names:
                n = n[:-4] + "_%d.pdf" % s["id"]
            names.add(n)
            z.writestr(n, got[1])
    return Response(buf.getvalue(), mimetype="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="BILLS_%s.zip"' % dt.date.today().strftime("%d-%m-%Y"), "Cache-Control": "no-store"})


# ---------------------------------------------------------------- the Sarvam trial: Marg overrules
def _s446_digits(s):
    return re.sub(r"\D", "", str(s or "")).lstrip("0")


def _s446_name_norm(s):
    return re.sub(r"[^A-Z0-9]+", " ", str(s or "").upper()).strip()


def _s446_exp(s):
    """An expiry as MM/YY whatever its shape ('01/28', '1-2028', '2028-01', 'JAN-28'), or ''."""
    t = str(s or "").strip().upper()
    if not t:
        return ""
    mons = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}
    m = re.match(r"^([A-Z]{3})\W*(\d{2,4})$", t)
    if m and m.group(1) in mons:
        return "%02d/%s" % (mons[m.group(1)], m.group(2)[-2:])
    m = re.match(r"^(\d{4})\W(\d{1,2})(\W\d{1,2})?$", t)
    if m:
        return "%02d/%s" % (int(m.group(2)), m.group(1)[-2:])
    m = re.match(r"^(\d{1,2})\W(\d{2,4})$", t)
    if m:
        return "%02d/%s" % (int(m.group(1)), m.group(2)[-2:])
    return t


def _s446_supplier_ok(con, scan_vendor, bill):
    if not scan_vendor:
        return False
    if _vendor_match(scan_vendor, bill["supplier"]):
        return True
    k = supplier_key(scan_vendor)
    try:
        r = con.execute("SELECT supplier_norm FROM purchase_scan_alias WHERE ocr_norm=?", (k,)).fetchone()
        if r and r[0] and (r[0] == bill["supplier_norm"] or _vendor_match(r[0], bill["supplier"])):
            return True
    except sqlite3.Error:
        pass
    return False


def _s446_compare_one(con, acon, link):
    import difflib                                              # noqa: PLC0415
    bill = con.execute("SELECT * FROM purchase_bill WHERE id=?", (link["bill_id"],)).fetchone()
    scan = acon.execute("SELECT id, vendor, bill_no, bill_date, total_amount FROM bills WHERE id=?", (link["asset_bill_id"],)).fetchone()
    if bill is None or scan is None:
        return None
    chosen = None
    try:
        r = con.execute("SELECT chosen_vendor FROM purchase_scan_state WHERE asset_bill_id=?", (scan["id"],)).fetchone()
        chosen = r[0] if r else None
    except sqlite3.Error:
        chosen = None
    sup_ok = _s446_supplier_ok(con, scan["vendor"], bill) or (bool(chosen) and chosen == bill["supplier_norm"])
    a, b = _s446_digits(scan["bill_no"]), _s446_digits(bill["bill_no"])
    bno_ok = bool(a and b) and (a == b or (len(b) >= 3 and a.endswith(b)) or (len(a) >= 3 and b.endswith(a)))
    sd = _iso(scan["bill_date"]) or _iso_any(scan["bill_date"])
    date_ok = bool(sd) and sd == bill["bill_date"]
    try:
        st = int(round(float(scan["total_amount"]) * 100)) if scan["total_amount"] not in (None, "") else None
    except (TypeError, ValueError):
        st = None
    total_ok = st is not None and abs(st - int(bill["amount_p"] or 0)) <= 100
    items = [dict(r) for r in acon.execute("SELECT item_name, quantity, rate, batch, expiry FROM bill_items WHERE bill_id=?", (scan["id"],))]
    # Marg's own lines of this bill, from the newest export that carries them
    ml = [dict(r) for r in con.execute("SELECT item, qty, free, rate_p, batch, expiry, source_md5 FROM purchase_line WHERE supplier_norm=? AND bill_no=? "
                                       "AND bill_date=? ORDER BY id", (bill["supplier_norm"], bill["bill_no"], bill["bill_date"]))]
    if ml:
        newest = ml[-1]["source_md5"]
        ml = [x for x in ml if x["source_md5"] == newest]
    detail, wrong = [], 0
    for it in items:
        nm = _s446_name_norm(it.get("item_name"))
        best, score = None, 0.0
        for x in ml:
            sc = difflib.SequenceMatcher(None, nm, _s446_name_norm(x["item"])).ratio()
            if sc > score:
                best, score = x, sc
        row = dict(scan_item=it.get("item_name"), marg_item=(best or {}).get("item"), score=round(score, 2), bad=[])
        if best is None or score < 0.6:
            row["bad"].append("name")
        else:
            try:
                if it.get("quantity") not in (None, "") and abs(float(it["quantity"]) - float(best["qty"] or 0)) > 0.001:
                    row["bad"].append("qty")
            except (TypeError, ValueError):
                row["bad"].append("qty")
            try:
                if it.get("rate") not in (None, "") and best.get("rate_p") is not None:
                    r1, r2 = float(it["rate"]), float(best["rate_p"]) / 100.0
                    if abs(r1 - r2) > max(0.01, 0.01 * r2):
                        row["bad"].append("rate")
            except (TypeError, ValueError):
                row["bad"].append("rate")
            if (it.get("batch") or "").strip() and (best.get("batch") or "").strip() and \
                    re.sub(r"\W", "", str(it["batch"]).upper()) != re.sub(r"\W", "", str(best["batch"]).upper()):
                row["bad"].append("batch")
            if (it.get("expiry") or "").strip() and (best.get("expiry") or "").strip() and _s446_exp(it["expiry"]) != _s446_exp(best["expiry"]):
                row["bad"].append("expiry")
        wrong += bool(row["bad"])
        detail.append(row)
    allok = sup_ok and bno_ok and date_ok and total_ok and wrong == 0
    con.execute("INSERT OR REPLACE INTO purchase_sarvam_check (asset_bill_id, bill_id, month, checked_at, supplier_ok, billno_ok, date_ok, total_ok, "
                "items_read, items_wrong, all_ok, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (scan["id"], bill["id"], bill["bill_date"][:7], now_iso(), int(sup_ok), int(bno_ok), int(date_ok), int(total_ok), len(items), wrong,
                 int(allok), json.dumps(dict(scan=dict(vendor=scan["vendor"], bill_no=scan["bill_no"], date=sd, total_p=st),
                                             marg=dict(supplier=bill["supplier"], bill_no=bill["bill_no"], date=bill["bill_date"], total_p=bill["amount_p"]),
                                             items=detail[:60]))))
    return allok


def sarvam_compare(con):
    """Every linked scan compared once (again when its link moves). Returns how many rows were written."""
    con.execute(S446_SARVAM_DDL)
    acon = _assets_con()
    if acon is None:
        return 0
    n = 0
    try:
        have = {r[0]: r[1] for r in con.execute("SELECT asset_bill_id, bill_id FROM purchase_sarvam_check")}
        for r in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link").fetchall():
            if have.get(r[1]) == r[0]:
                continue
            if _s446_compare_one(con, acon, dict(bill_id=r[0], asset_bill_id=r[1])) is not None:
                n += 1
    finally:
        acon.close()
    if n:
        con.commit()
    return n


def sarvam_summary(con, month):
    con.execute(S446_SARVAM_DDL)
    r = con.execute("SELECT COUNT(*), SUM(all_ok), SUM(1-supplier_ok), SUM(1-billno_ok), SUM(1-date_ok), SUM(1-total_ok), "
                    "SUM(CASE WHEN items_wrong>0 THEN 1 ELSE 0 END), SUM(CASE WHEN items_read>0 THEN 1 ELSE 0 END) FROM purchase_sarvam_check WHERE month=?",
                    (month,)).fetchone()
    k = ("n", "agreed", "supplier_wrong", "billno_wrong", "date_wrong", "total_wrong", "items_wrong", "items_read")
    return {k[i]: int(r[i] or 0) for i in range(len(k))}


def _s446_trial_months(con):
    until = _s446_setting(con, "purchase.sarvam_trial_until", "")
    if not until or dt.date.today().isoformat() > until:
        return [], until
    t = dt.date.today()
    prev = (t.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    return [prev, t.strftime("%Y-%m")], until


def _s446_sarvam_text(month, s):
    return ("%s: %d bill%s · Sarvam agreed fully on %d · supplier wrong %d · bill no. wrong %d · date wrong %d · total wrong %d · items wrong %d (of %d with items read)"
            % (_month_name(month), s["n"], "" if s["n"] == 1 else "s", s["agreed"], s["supplier_wrong"], s["billno_wrong"], s["date_wrong"],
               s["total_wrong"], s["items_wrong"], s["items_read"]))


def sarvam_lines(con):
    """The owner's monthly Needs-you summary while the trial runs (info lines; the drill-down is Marg Purchases -> Scan links)."""
    out = []
    try:
        months, until = _s446_trial_months(con)
        if not months:
            return out
        sarvam_compare(con)
        for m in months:
            s = sarvam_summary(con, m)
            if s["n"]:
                out.append(dict(cls="info", target="porders", text="Sarvam trial (Marg overrules until %s) -- %s" % (until, _s446_sarvam_text(m, s))))
    except Exception:                                          # noqa: BLE001
        return out
    return out


def _s446_sarvam_card(con):
    """One line on the owner's Scan links page."""
    try:
        months, until = _s446_trial_months(con)
        if not months:
            return ""
        sarvam_compare(con)
        prefix = request.script_root + _url_prefix
        parts = []
        for m in months:
            s = sarvam_summary(con, m)
            if s["n"]:
                parts.append('<a href="%s/page/sarvam?month=%s">%s</a>' % (prefix, m, _esc(_s446_sarvam_text(m, s))))
        if not parts:
            return ""
        return ('<div class="card" id="s446sarvam"><h2>Sarvam against Marg (trial until %s: Marg overrules)</h2><div class="muted">%s</div></div>'
                % (_esc(until), "<br>".join(parts)))
    except Exception:                                          # noqa: BLE001
        return ""


@bp.route("/page/sarvam")
def page_s446_sarvam():
    u, err = _person("checker")
    if err:
        return err
    con = _db()
    _ensure(con)
    sarvam_compare(con)
    month = str(request.args.get("month") or dt.date.today().strftime("%Y-%m"))[:7]
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    s = sarvam_summary(con, month)
    rows = []
    for r in con.execute("SELECT asset_bill_id, supplier_ok, billno_ok, date_ok, total_ok, items_read, items_wrong, all_ok, detail FROM purchase_sarvam_check "
                         "WHERE month=? ORDER BY all_ok, asset_bill_id", (month,)):
        d = json.loads(r[8] or "{}")
        sc, mg = d.get("scan") or {}, d.get("marg") or {}
        yn = lambda v: "" if v else ' class="bad"'                  # noqa: E731
        bad_items = "; ".join("%s (%s)" % (x.get("scan_item") or "?", ", ".join(x.get("bad") or [])) for x in (d.get("items") or []) if x.get("bad"))
        rows.append('<tr><td>%d</td><td%s>%s / %s</td><td%s>%s / %s</td><td%s>%s / %s</td><td%s>%s / %s</td><td>%d read, %d wrong%s</td></tr>'
                    % (r[0], yn(r[1]), _esc(sc.get("vendor")), _esc(mg.get("supplier")), yn(r[2]), _esc(sc.get("bill_no")), _esc(mg.get("bill_no")),
                       yn(r[3]), _esc(sc.get("date")), _esc(mg.get("date")), yn(r[4]),
                       _r(sc["total_p"]) if sc.get("total_p") is not None else "-", _r(mg.get("total_p") or 0), r[5], r[6],
                       ("<br><span class=muted>%s</span>" % _esc(bad_items[:400])) if bad_items else ""))
    body = ('<h1>Sarvam against Marg — %s</h1><div class="muted">%s. Each cell: what Sarvam read / what Marg holds. '
            'Marg\'s figure is the bill\'s; this page only counts.</div><div class="card"><div class="scroll"><table>'
            '<tr><th>scan</th><th>supplier</th><th>bill no.</th><th>date</th><th>total</th><th>items</th></tr>%s</table></div></div>'
            % (_esc(_month_name(month)), _esc(_s446_sarvam_text(month, s)), "".join(rows) or "<tr><td colspan=6>none</td></tr>"))
    return _page("Sarvam against Marg — %s" % _month_name(month), body)


# ---------------------------------------------------------------- the payment sheet: an earlier month's unfinished work
def _s446_earlier_card(con, month, prefix):
    try:
        out = []
        for m in [x for x in _months(con, 4) if x < month]:
            unsent = 0
            try:
                unsent = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE month=? AND status IN ('queued','failed')", (m,)).fetchone()[0])
            except sqlite3.Error:
                unsent = 0
            nodone = 0
            try:
                st = con.execute("SELECT status FROM purchase_month WHERE month=?", (m,)).fetchone()
                ev = con.execute("SELECT COUNT(*) FROM purchase_neft_event WHERE month=?", (m,)).fetchone()[0]
                if st and st[0] == "final" and not ev:
                    _s, groups = _pay_rows(con, m)
                    nodone = sum(1 for g in groups if g["route"] == "NEFT" and g["payable_p"] > 0)
            except Exception:                                  # noqa: BLE001
                nodone = 0
            if unsent or nodone:
                bits = []
                if unsent:
                    bits.append("%d supplier message%s not sent" % (unsent, "" if unsent == 1 else "s"))
                if nodone:
                    bits.append("%d NEFT line%s with no NEFT recorded" % (nodone, "" if nodone == 1 else "s"))
                out.append((m, unsent + nodone, " · ".join(bits)))
        if not out:
            return ""
        return ('<div class="card" id="s446earlier" style="border:2px solid #b3261e"><h2>Pichhle mahine ka baaki: %d</h2>%s</div>'
                % (sum(x[1] for x in out), "".join('<div><a class="p" href="%s/page/pay/%s">%s — %s ›</a></div>' % (prefix, m, _esc(_month_name(m)), _esc(t))
                                                   for m, _n, t in out)))
    except Exception:                                          # noqa: BLE001
        return ""
# ---- S446_AMIR_STAGES_BILLS end ---------------------------------------------------------------------------------------------------------
