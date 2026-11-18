# ---------------------------------------------------------------------------------------------------------------------
# S878 (the parent, S484, 18-Nov-2026, F-1466): the patient's page rebuilt on patient_events.events() -- the ONE reader
# (the Sanjeevni chat's S876) -- as his mock-up v6: a folded page; the banner with the full mobile, the diagnosis and a
# quiet money chip; one folded line per day; the Docterz clinical line folded under the day; the Hub's bill-line table
# folded under each bill; X-rays and reports opening in place; Expand all / Collapse all / Top. English, no dialog.
# The old page stays as _patient_html_s834 and is served when patient_events cannot be imported.
# ---------------------------------------------------------------------------------------------------------------------
S878_VERSION = "1.0"
_S878_CLIN_CACHE = {}                                                  # export path -> (mtime, {cid: [row dicts]})


def _s878_mobiles(cid):
    try:
        import not_in_docterz                                           # noqa: PLC0415 -- the parent's own mirror reader
        return list((not_in_docterz.mobiles({cid}) or {}).get(cid) or [])
    except Exception:                                                   # noqa: BLE001
        return []


def _s878_dx(con, cid):
    """dx_visit rows for this ID, newest first: [{day, dx, raw, category, priority, follow_up}]."""
    if not _has_table(con, "dx_visit"):
        return []
    out = []
    for r in _rows(con, "SELECT visit_date d, diagnosis_raw, std_dx, category, priority, follow_up_date FROM dx_visit "
                        "WHERE clinic_id=? ORDER BY visit_date DESC", (cid,)):
        dx = (r["std_dx"] or "").strip()
        raw = (r["diagnosis_raw"] or "").strip()
        if dx.lower().startswith("other") and raw:
            dx = raw
        out.append(dict(day=str(r["d"])[:10], dx=dx or raw, raw=raw, category=r["category"] or "", priority=r["priority"] or "",
                        follow_up=str(r["follow_up_date"] or "")[:10]))
    return out


def _has_table(con, name):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None
    except Exception:                                                   # noqa: BLE001
        return False


def _s878_clinical(con, cid):
    """{day: {purpose, time, drugs, dosage, instructions, tests, procedures}} from the kept clinical data reports
    (docterz_export kind 'clinical', status 'current'; the bytes stay on the box). Parsed once per file, cached."""
    import csv                                                          # noqa: PLC0415
    import io                                                           # noqa: PLC0415
    out = {}
    if not _has_table(con, "docterz_export"):
        return out
    paths = [r["stored"] for r in _rows(con, "SELECT stored FROM docterz_export WHERE kind='clinical' AND status='current' "
                                            "AND stored<>'' ORDER BY business_date, id")]
    want = {"drugs": "drug", "dosage": "dosage", "instructions": "instruction", "tests": "test", "procedures": "procedure",
            "purpose": "purpose", "time": "time"}
    for p in paths:
        try:
            mt = os.path.getmtime(p)
        except OSError:
            continue
        hit = _S878_CLIN_CACHE.get(p)
        if hit is None or hit[0] != mt:
            by = {}
            try:
                with open(p, "rb") as fh:
                    raw = fh.read()
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = raw.decode("cp1252", errors="replace")
                rows = list(csv.reader(io.StringIO(text)))
                head = [h.strip() for h in rows[0]] if rows else []
                idx = {h: i for i, h in enumerate(head)}
                col = {}
                for k, word in want.items():
                    for h in head:
                        hl = h.lower()
                        if word in hl and not (k == "time" and "date" in hl):
                            col[k] = idx[h]
                            break
                ci, di = idx.get("Clinic Specific Id"), idx.get("Consultation Date")
                if ci is not None and di is not None:
                    for r in rows[1:]:
                        if len(r) <= max(ci, di):
                            continue
                        c = r[ci].strip()
                        if re.match(r"^\d+\.0$", c):
                            c = c[:-2]
                        day = _s878_day(r[di])
                        if not c or not day:
                            continue
                        rec = {"day": day}
                        for k, i in col.items():
                            rec[k] = r[i].strip() if len(r) > i else ""
                        by.setdefault(c, []).append(rec)
            except (OSError, csv.Error, IndexError):
                by = {}
            _S878_CLIN_CACHE[p] = (mt, by)
            hit = _S878_CLIN_CACHE[p]
        for rec in hit[1].get(str(cid), []):
            cur = out.setdefault(rec["day"], {})
            for k, v in rec.items():
                if k != "day" and v and not cur.get(k):
                    cur[k] = v
    return out


def _s878_day(s):
    s = str(s or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    m = re.match(r"^(\d{1,2})[-/ ]([A-Za-z]{3})[-/ ](\d{4})", s)
    if m:
        try:
            return dt.datetime.strptime("%s %s %s" % (m.group(1), m.group(2), m.group(3)), "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            return ""
    return ""


def _s878_words(s):
    return {w for w in re.findall(r"[A-Za-z]{4,}", str(s or "").upper())}


def _s878_bill_lines(con, bill, day):
    """The Hub's own line table of a bill: item as typed, qty, pack, rate, line Rs, batch, expiry."""
    if not _has_table(con, "sale_line_item"):
        return []
    out = []
    for l in _rows(con, "SELECT item_name, pack, qty_raw, amount_p, expiry_ym, batch, is_return FROM sale_line_item "
                        "WHERE bill_no=? AND business_date=? ORDER BY seq, id", (str(bill), day)):
        strips, loose = 0, 0
        m = re.match(r"^\s*(\d+)\s*(?::\s*(\d+))?\s*$", str(l["qty_raw"] or ""))
        if m:
            strips, loose = int(m.group(1)), int(m.group(2) or 0)
        rate = ""
        if l["amount_p"] and strips and not loose:
            rate = "%.2f" % (l["amount_p"] / 100.0 / strips)
        out.append(dict(item=l["item_name"] or "", qty=l["qty_raw"] or "", pack=l["pack"] or "", rate=rate,
                        amount=("%.2f" % (l["amount_p"] / 100.0)) if l["amount_p"] is not None else "",
                        amount_p=l["amount_p"] or 0, batch=l["batch"] or "", exp=l["expiry_ym"] or "", ret=bool(l["is_return"])))
    return out


def _s878_money(con, cid):
    """The patient's money by head and by month (paise): clinic lines by section, pharmacy net of returns, discounts."""
    heads = {"consult": 0, "xray": 0, "proc": 0, "pharmacy": 0}
    counts = {"paid": 0, "free": 0, "concession": 0}
    months, bydays = {}, {}
    if _has_table(con, "clinic_day_line"):
        for r in _rows(con, "SELECT business_date d, section, amount_p FROM clinic_day_line WHERE clinic_id=?", (cid,)):
            amt = int(r["amount_p"] or 0)
            sec = r["section"] or ""
            if sec in ("consult", "revisit", "concession"):
                heads["consult"] += amt
                counts["paid" if sec == "consult" and amt else ("free" if sec == "revisit" or not amt else "concession")] += 1
            elif sec in heads:
                heads[sec] += amt
            else:
                heads["proc"] += amt
            months[str(r["d"])[:7]] = months.get(str(r["d"])[:7], 0) + amt
            bydays[str(r["d"])[:10]] = bydays.get(str(r["d"])[:10], 0) + amt
    disc = 0
    if _has_table(con, "sale_item") and _has_table(con, "patient_ref") and _has_table(con, "day_entry"):
        seen = set()
        for r in _rows(con, """SELECT s.service, s.source_ref bill, s.amount_p, d.business_date day FROM sale_item s
                               JOIN patient_ref p ON p.id = s.patient_ref_id JOIN day_entry d ON d.id = s.day_entry_id
                               WHERE p.clinic_id=? AND s.service IN ('pharmacy','pharmacy_return')
                                 AND ((s.verified_by IS NOT NULL AND s.verified_by <> '') OR s.confidence >= ?)""", (cid, SURE_CONF)):
            k = (str(r["bill"]), r["day"])
            if k in seen:
                continue
            seen.add(k)
            amt = abs(int(r["amount_p"] or 0)) * (-1 if r["service"] == "pharmacy_return" else 1)
            heads["pharmacy"] += amt
            months[str(r["day"])[:7]] = months.get(str(r["day"])[:7], 0) + amt
            bydays[str(r["day"])[:10]] = bydays.get(str(r["day"])[:10], 0) + amt
            if amt > 0:
                lines = sum(l["amount_p"] for l in _s878_bill_lines(con, r["bill"], r["day"]))
                if lines > amt:
                    disc += lines - amt
    total = sum(heads.values())
    return dict(heads=heads, counts=counts, months=sorted(months.items()), days=bydays, total=total, pharmacy_discount=disc)


def _s878_month_name(ym):
    try:
        return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%b-%Y")
    except (ValueError, TypeError):
        return ym


def _s878_viewer(url, kind):
    """The in-place viewer under a line: a picture or a PDF, with a new-tab link and close."""
    return ('<div class="vw"><div class="vh"><span class="sm"></span><span><a href="%s" target="_blank" rel="noopener">Open in a new tab ↗</a> '
            '&nbsp; <button type="button" class="ghost" onclick="rvClose(this)">close ✕</button></span></div>'
            '<div class="vb" data-src="%s" data-kind="%s"></div></div>' % (_esc(url), _esc(url), "pdf" if kind == "pdf" else "img"))


def _s878_file_kind(f):
    mime = (f.get("mime") or "").lower()
    name = (f.get("file_name") or "").lower()
    if "pdf" in mime or name.endswith(".pdf"):
        return "pdf"
    if mime.startswith("image/") or re.search(r"\.(jpe?g|png|gif|bmp|webp)$", name):
        return "img"
    return "pdf"


def _patient_html(con, cid):
    try:
        import patient_events as pe                                     # noqa: PLC0415 -- the one reader (S876, the Sanjeevni chat's)
        rec = pe.events(con, cid)
    except Exception as ex:                                             # noqa: BLE001 -- the old page rather than a blank one; one line, no ID
        import logging                                                  # noqa: PLC0415
        logging.getLogger("records").warning("S878 page fell back to the S834 page: %s", type(ex).__name__)
        return _patient_html_s834(con, cid)
    p = person(con, cid)
    name = (p or {}).get("name") or rec.get("name") or "Name not known yet"
    mobiles = _s878_mobiles(cid)
    dx = _s878_dx(con, cid)
    clin = _s878_clinical(con, cid)
    fl = files(con, cid)
    orders, reports = blood(con, cid)
    money = _s878_money(con, cid)
    evs = events(con, cid)
    waiting = _rows(con, "SELECT kind, day FROM record_upload WHERE clinic_id=? AND state='new' AND event_id IS NULL", (cid,))
    paper_form, event_form = _add_forms(cid)
    days = rec.get("days") or []
    clinic_days = sorted({d["date"] for d in days if any(e["kind"] in ("consult", "visit") for e in d["events"])})
    today = str(_today())[:10]
    # ---- the banner
    h = ['<div class="who"><div class="nm">%s</div><div class="id">ID %s%s</div>' % (
        _esc(name), _esc(cid), (" · <b>" + " · ".join(_esc(m) for m in mobiles) + "</b>") if mobiles else
        ((" · ••••" + _esc(p["last4"])) if p and p.get("last4") else ""))]
    if dx:
        first = dx[0]
        later = []
        seen = {first["dx"].lower()}
        for d in dx[1:]:
            if d["dx"] and d["dx"].lower() not in seen:
                seen.add(d["dx"].lower())
                later.append("%s (%s)" % (_esc(d["dx"]), _dmy(d["day"])))
        h.append('<div class="dx"><b>Diagnosis:</b> %s <span class="sm">(%s%s%s)</span>%s</div>' % (
            _esc(first["dx"] or "not written"), _dmy(first["day"]), (" · " + _esc(first["category"])) if first["category"] else "",
            (" · follow-up priority " + _esc(first["priority"])) if first["priority"] else "",
            ('<br><span class="sm">Earlier: %s</span>' % " · ".join(later[:4])) if later else ""))
    nxt = [dx[0]] if dx and dx[0]["follow_up"] and dx[0]["follow_up"] >= today else []   # the latest visit's advice, if still ahead
    line = []
    if clinic_days:
        line.append("First seen %s · last %s · %d visit day%s" % (_dmy(clinic_days[0]), _dmy(clinic_days[-1]), len(clinic_days), "" if len(clinic_days) == 1 else "s"))
    else:
        line.append("No visit on record yet (Docterz lines start 15-Jun-2026)")
    if nxt:
        line.append("next follow-up advised <b>%s</b>" % _dmy(min(d["follow_up"] for d in nxt)))
    h.append('<div class="sm">%s</div>' % " · ".join(line))
    nx = sum(1 for f in fl if f["kind"] == "xray")
    nb = sum(1 for d in days for e in d["events"] if e["kind"] == "bought")
    npr = sum(1 for d in days for e in d["events"] if e["kind"] == "proc")
    h.append('<div class="chips"><span class="chip">%d X-ray film%s</span><span class="chip">%d report%s</span><span class="chip">%d pharmacy bill%s</span>'
             '<span class="chip">%d procedure%s</span>%s</div>' % (
                 nx, "" if nx == 1 else "s", len(fl) - nx, "" if len(fl) - nx == 1 else "s", nb, "" if nb == 1 else "s",
                 npr, "" if npr == 1 else "s", ('<span class="chip">%d hospital</span>' % len(evs)) if evs else ""))
    # the quiet money chip
    m = money
    heads = m["heads"]
    c = m["counts"]
    mb = ('<b class="t">%s</b> from this patient%s · consultations %s (%d paid · %d free · %d concession) · X-rays %s · procedures %s · pharmacy %s net%s'
          % (_rs(m["total"]), (" since " + _s878_month_name(m["months"][0][0])) if m["months"] else "", _rs(heads["consult"]),
             c["paid"], c["free"], c["concession"], _rs(heads["xray"]), _rs(heads["proc"]), _rs(heads["pharmacy"]),
             (" (bill discounts %s)" % _rs(m["pharmacy_discount"])) if m["pharmacy_discount"] else ""))
    if m["months"]:
        mb += '<table class="mt"><tr>%s</tr><tr>%s</tr></table>' % (
            "".join("<th>%s</th>" % _esc(_s878_month_name(k)) for k, _v in m["months"][-12:]),
            "".join('<td>%s</td>' % _rs(v) for _k, v in m["months"][-12:]))
    h.append('<details class="money"><summary title="more">₹ ···</summary><div class="mb">%s</div></details>' % mb)
    if p and p.get("merged"):
        h.append('<div class="rem">This ID is marked as merged into %s in the patient list.</div>' % _esc(p["merged"]))
    h.append('</div>')
    # ---- on file
    tiles = []
    for f in fl:
        if not f["drive_id"]:
            continue
        url = "%s/file/%d" % (P, f["id"])
        k = _s878_file_kind(f)
        label = "%s · %s" % (KIND_NAME.get(f["kind"], f["kind"]), _dmy(f["day"]))
        tiles.append('<div class="tile%s" onclick="rvFile(this)" data-src="%s" data-kind="%s" data-label="%s"><b>%s</b><span class="sm">%s</span></div>' % (
            " doc" if k == "pdf" else "", _esc(url), k, _esc(label), _esc(label), _esc((f["file_name"] or "")[:40])))
    got = {r["d"] for r in reports}
    filed_days = {f["day"] for f in fl if f["kind"] == "blood"}
    missing = sorted(got - filed_days, reverse=True)
    for d in missing:
        tiles.append('<div class="tile warn"><b>Lab e-mail · %s</b><span class="sm">received, PDF not filed yet</span></div>' % _dmy(d))
    for w in waiting:
        tiles.append('<div class="tile warn"><b>%s · %s</b><span class="sm">on its way to Drive</span></div>' % (_esc(KIND_NAME.get(w["kind"], w["kind"])), _dmy(w["day"])))
    onfile = ('<h2>On file</h2><div class="file">%s</div>' % ("".join(tiles) or '<span class="sm">No photo or paper filed yet.</span>')
              + '<div class="vw" id="rv0"><div class="vh"><b id="rv0t"></b><span><a id="rv0a" href="#" target="_blank" rel="noopener">Open in a new tab ↗</a> '
                '&nbsp; <button type="button" class="ghost" onclick="rvClose(this)">close ✕</button></span></div><div class="vb" id="rv0b"></div></div>'
              + paper_form)
    # ---- the days
    cards = []
    for d in days:
        es = d["events"]
        heads_ = []
        for e in es:
            if e["kind"] == "dx":
                continue
            w = e["head"]
            if e["kind"] == "xray" and e.get("text"):
                w = "X-ray"
            heads_.append(w)
        what = " · ".join(dict.fromkeys(heads_))
        rows = []
        day_total = money["days"].get(d["date"], 0)
        for e in es:
            if e["kind"] == "dx":
                continue
            amt = e.get("money")
            money_txt = ((" · <b>" + ("−" if (e.get("sign") == "−") else ("+" if e.get("sign") == "+" else "")) + "₹" + _esc(amt) + "</b>") if amt else "")
            body = "<b>%s</b>%s%s%s" % (_esc(e["head"]), _esc(e.get("text") or ""), money_txt, (' <span class="sm">· ' + _esc(e["sub"]) + '</span>') if e.get("sub") else "")
            if e.get("flag"):
                body += ' <span class="badge%s">%s</span>' % (" mut" if e["flag"].get("tone") == "mut" else "", _esc(e["flag"].get("text") or ""))
            extra = []
            for o in e.get("opens") or []:
                for fx in o.get("files") or []:
                    if fx.get("url"):
                        kind = "pdf" if ("report" in (fx.get("name") or "").lower() or ".pdf" in (fx.get("name") or "").lower()) else "img"
                        extra.append('<a href="#" class="rvl" onclick="rvIn(this);return false">%s — see here</a>%s' % (
                            _esc(fx.get("name") or "the paper"), _s878_viewer(fx["url"], kind)))
            if e["kind"] in ("bought", "returned", "exchanged"):
                for b in [x.strip() for x in str(e.get("ref") or "").split("·") if x.strip()]:
                    lines = _s878_bill_lines(con, b, d["date"]) or ([] if e["kind"] != "exchanged" else _s878_bill_lines_any(con, b))
                    if lines:
                        extra.append('<details class="bl"><summary>bill %s — %d line%s</summary><table class="bl"><tr><th>item</th><th>qty</th><th>pack</th>'
                                     '<th class="num">rate</th><th class="num">line ₹</th><th>batch</th><th>exp</th></tr>%s</table></details>' % (
                                         _esc(b), len(lines), "" if len(lines) == 1 else "s",
                                         "".join('<tr%s><td>%s</td><td>%s</td><td>%s</td><td class="num">%s</td><td class="num">%s%s</td><td>%s</td><td>%s</td></tr>' % (
                                             ' class="ret"' if l["ret"] else "", _esc(l["item"]), _esc(l["qty"]), _esc(l["pack"]), _esc(l["rate"]),
                                             "−" if l["ret"] else "", _esc(l["amount"]), _esc(l["batch"]), _esc(l["exp"])) for l in lines)))
            rows.append('<div class="ev"><div class="k">%s</div><div class="v">%s%s</div></div>' % (
                _esc(e.get("icon") or ""), body, ("<div>" + "<br>".join(extra) + "</div>") if extra else ""))
        # the Docterz line, folded
        dxr = next((x for x in dx if x["day"] == d["date"]), None)
        cl = clin.get(d["date"]) or {}
        if dxr or cl:
            parts = []
            if dxr and dxr["dx"]:
                parts.append("<b>%s</b>" % _esc(dxr["dx"]))
            drugs = [x.strip() for x in re.split(r"[;,\n|]+", cl.get("drugs") or "") if x.strip()]
            if drugs:
                bought_words = set()
                for e in es:
                    if e["kind"] in ("bought", "exchanged"):
                        for b in [x.strip() for x in str(e.get("ref") or "").split("·") if x.strip()]:
                            for l in _s878_bill_lines(con, b, d["date"]):
                                bought_words |= _s878_words(l["item"])
                hit = sum(1 for g in drugs if _s878_words(g) & bought_words)
                parts.append("prescribed %d, bought %d here%s" % (len(drugs), hit, " ✓" if hit == len(drugs) else ""))
            if dxr and dxr["follow_up"]:
                fu = dxr["follow_up"]
                came = next((c for c in clinic_days if c > d["date"] and c >= _s878_shift(fu, -3)), "")
                if came and came <= _s878_shift(fu, 14):
                    parts.append("follow-up advised %s → <span class=\"ok\">came %s ✓</span>" % (_dmy(fu), _dmy(came)))
                elif came:
                    parts.append("follow-up advised %s → <span class=\"warn\">came %s</span>" % (_dmy(fu), _dmy(came)))
                elif fu < today:
                    parts.append("follow-up advised %s → <span class=\"warn\">not come since</span>" % _dmy(fu))
                else:
                    parts.append("follow-up advised <b>%s</b>" % _dmy(fu))
            inner = []
            if cl.get("drugs"):
                inner.append("<div><b>Prescribed:</b> %s%s</div>" % (_esc(cl["drugs"]), (" — " + _esc(cl["dosage"])) if cl.get("dosage") else ""))
            if cl.get("instructions"):
                inner.append("<div><b>Advised:</b> %s</div>" % _esc(cl["instructions"]))
            if cl.get("tests"):
                inner.append("<div><b>Tests advised:</b> %s</div>" % _esc(cl["tests"]))
            if cl.get("procedures"):
                inner.append("<div><b>Procedures advised:</b> %s</div>" % _esc(cl["procedures"]))
            meta = " · ".join(x for x in ((("<b>Purpose:</b> " + _esc(cl["purpose"])) if cl.get("purpose") else ""),
                                          (_esc(cl["time"]) if cl.get("time") else ""),
                                          (("<b>Taxonomy:</b> %s%s" % (_esc(dxr["category"]), (", priority " + _esc(dxr["priority"])) if dxr["priority"] else "")) if dxr and dxr["category"] else "")) if x)
            if meta:
                inner.append("<div>%s</div>" % meta)
            rows.append('<details class="cl"><summary>Docterz: %s</summary><div class="in">%s</div></details>' % (
                " · ".join(parts) or "the clinical report's line", "".join(inner) or '<div class="sm">nothing more written</div>'))
        cards.append('<details class="day"><summary><div class="dh"><b>%s <span class="what">— %s</span><span class="ar">▶</span></b><span class="sm">%s</span></div></summary>%s'
                     '<div class="dt">This day: %s</div></details>' % (
                         d.get("dmy") or _dmy(d["date"]), _esc(what) or "—", _esc(d.get("dow") or ""), "".join(rows),
                         ("₹" + "{:,}".format(int(round(day_total / 100.0)))) if day_total else "no charge"))
    # ---- hospital events (the doctor's own, with the form)
    hs = event_form
    msg = request.args.get("msg", "")
    body = (('<div class="okb">%s</div>' % _esc(msg)) if msg else "") + "".join(h) + onfile \
        + '<div class="bar"><button type="button" class="ghost" onclick="rvAll(true)">Expand all</button><button type="button" class="ghost" onclick="rvAll(false)">Collapse all</button>' \
          '<button type="button" class="ghost" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">↑ Top</button></div>' \
        + '<h2>What happened, day by day</h2>' + ("".join(cards) or '<p class="sm">Nothing on record yet.</p>') \
        + '<h2>Hospital &amp; surgery</h2>' + hs + S878_CSS + S878_JS
    return _shell("%s · %s" % (name, cid), body, back=P, back_label="← Records")


def _s878_bill_lines_any(con, bill):
    if not _has_table(con, "sale_line_item"):
        return []
    d = _rows(con, "SELECT business_date FROM sale_line_item WHERE bill_no=? ORDER BY business_date DESC LIMIT 1", (str(bill),))
    return _s878_bill_lines(con, bill, d[0]["business_date"]) if d else []


def _s878_shift(iso, days):
    try:
        return (dt.date.fromisoformat(iso[:10]) + dt.timedelta(days=days)).isoformat()
    except (ValueError, TypeError):
        return iso


S878_CSS = """<style>
.who{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:6px}
.who .nm{font-size:22px;font-weight:700}.who .id{color:var(--mut)}.who .sm{font-size:14px}
.dx{margin-top:6px;padding:8px 10px;background:#fff7e8;border-left:3px solid #e2b34b;border-radius:6px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.chip{background:#eef3f8;border-radius:999px;padding:3px 11px;font-size:13px}
.money{margin-top:8px;font-size:14px}.money summary{list-style:none;display:inline-block;color:#9aa7b3;font-size:13px;padding:1px 8px;border:1px solid var(--line);border-radius:999px;cursor:pointer;user-select:none}
.money summary::-webkit-details-marker{display:none}.money[open] summary{color:var(--ok)}.money .mb{margin-top:8px;padding:8px 10px;background:#eef6ee;border-left:3px solid var(--ok);border-radius:6px}
.money b.t{font-size:16px}.mt{border-collapse:collapse;margin-top:6px;font-size:13px}.mt th,.mt td{padding:2px 8px 2px 0;text-align:right}.mt th{color:var(--mut);font-weight:600}
h2{font-size:15px;margin:18px 0 8px;letter-spacing:.04em;text-transform:uppercase;color:#3a5a78}
.file{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;gap:10px;flex-wrap:wrap}
.tile{width:150px;min-height:72px;border-radius:8px;background:linear-gradient(135deg,#2c3e50,#4a6a8a);color:#dbe7f2;padding:8px;cursor:pointer;font-size:13px}
.tile b{display:block;color:#fff}.tile .sm{color:#c5d3e0;font-size:12px;word-break:break-all}.tile.doc{background:#f3f4f6;color:#1f2a36;border:1px solid var(--line)}.tile.doc b{color:#1f2a36}.tile.doc .sm{color:var(--mut)}
.tile.warn{background:#fdf0d5;color:#8a5a00;border:1px solid #e2c48a;cursor:default}.tile.warn b{color:#8a5a00}.tile.on{outline:3px solid var(--accent)}
.vw{display:none;background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin-top:6px}.vw.on{display:block}
.vw .vh{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:14px;margin-bottom:6px}.vw .vh a{color:var(--accent)}
.vb img{max-width:100%;height:auto;border-radius:6px;display:block}.vb iframe{width:100%;height:70vh;border:1px solid var(--line);border-radius:6px}
.ghost{font:inherit;font-size:14px;background:#fff;border:1px solid #b9c7d6;border-radius:999px;padding:4px 12px;color:var(--accent);cursor:pointer;min-height:36px}
.bar{position:sticky;top:52px;z-index:4;display:flex;gap:8px;justify-content:flex-end;align-items:center;padding:6px 0;background:var(--bg)}
details.day{background:#fff;border:1px solid var(--line);border-radius:12px;margin-top:8px;overflow:hidden}
details.day>summary{list-style:none;cursor:pointer}details.day>summary::-webkit-details-marker{display:none}
.dh{display:flex;justify-content:space-between;align-items:baseline;padding:10px 14px;background:#f7f9fb;gap:8px}details.day[open]>summary .dh{border-bottom:1px solid var(--line)}
.dh .what{color:var(--mut);font-size:14px;font-weight:400}.dh .ar{color:#9aa7b3;font-size:12px;margin-left:8px;display:inline-block}details.day[open] .ar{transform:rotate(90deg)}
.ev{display:grid;grid-template-columns:34px 1fr;gap:4px 8px;padding:8px 14px;border-top:1px solid #eef2f6;font-size:15px}.ev .k{font-size:18px;line-height:1.2}
.ev a{color:var(--accent)}.badge{display:inline-block;font-size:12px;padding:1px 7px;border-radius:999px;background:#fdf0d5;color:#8a5a00;margin-left:4px}.badge.mut{background:#eef3f8;color:var(--mut)}
details.bl summary{color:var(--accent);cursor:pointer;font-size:14px}table.bl{border-collapse:collapse;margin-top:4px;font-size:13.5px;width:100%}
table.bl th{text-align:left;color:var(--mut);font-weight:600;border-bottom:1px solid var(--line);padding:3px 8px 3px 0}table.bl td{padding:3px 8px 3px 0;border-bottom:1px solid #f0f3f6}table.bl .num{text-align:right}table.bl tr.ret td{color:#8a3b12}
.cl{margin:6px 14px 8px;background:#fbfcfd;border:1px dashed #cfd8e2;border-radius:8px;padding:6px 10px;font-size:14px}.cl summary{cursor:pointer}.cl .in{padding:6px 0 2px}.cl .in div{margin:3px 0}
.dt{padding:8px 14px;color:var(--mut);font-size:13px;border-top:1px dashed var(--line)}.ok{color:var(--ok)}.warn{color:var(--warn)}
@media (max-width:600px){.tile{width:46%}}
</style>"""

S878_JS = """<script>
function rvShow(box,src,kind){box.innerHTML=kind==='pdf'?'<iframe src="'+src+'" title="the paper"></iframe>':'<img src="'+src+'" alt="the photo">'}
function rvFile(t){var v=document.getElementById('rv0'),b=document.getElementById('rv0b');document.querySelectorAll('.tile.on').forEach(function(x){x.classList.remove('on')});
  if(v.classList.contains('on')&&b.getAttribute('data-cur')===t.getAttribute('data-src')){v.classList.remove('on');b.innerHTML='';b.removeAttribute('data-cur');return}
  t.classList.add('on');document.getElementById('rv0t').textContent=t.getAttribute('data-label');document.getElementById('rv0a').href=t.getAttribute('data-src');
  rvShow(b,t.getAttribute('data-src'),t.getAttribute('data-kind'));b.setAttribute('data-cur',t.getAttribute('data-src'));v.classList.add('on');v.scrollIntoView({block:'nearest',behavior:'smooth'})}
function rvIn(a){var v=a.nextElementSibling;if(!v||!v.classList.contains('vw'))return;if(v.classList.contains('on')){v.classList.remove('on');v.querySelector('.vb').innerHTML='';return}
  var b=v.querySelector('.vb');rvShow(b,b.getAttribute('data-src'),b.getAttribute('data-kind'));v.classList.add('on')}
function rvClose(btn){var v=btn.closest('.vw');v.classList.remove('on');var b=v.querySelector('.vb');b.innerHTML='';b.removeAttribute('data-cur');document.querySelectorAll('.tile.on').forEach(function(x){x.classList.remove('on')})}
function rvAll(o){document.querySelectorAll('details.day').forEach(function(d){d.open=o});if(!o){document.querySelectorAll('details.day details').forEach(function(d){d.open=false})}}
</script>"""
