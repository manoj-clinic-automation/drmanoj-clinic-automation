#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s409.py -- builds the three patched live files of kit S409_SCAN_LANES from the LIVE bytes by anchored edits.
Every anchor must occur exactly once, and every source must be at its FROM pin, or the build stops with nothing written.

  asset_register.py  (PARENT -- the asset app)  five lanes (bills.lane, backfilled), the per-user default lane
                     (user_lane_default; the owner's /lanes card), the duplicate guard at capture (a perceptual dHash of
                     the flattened first page through pdftoppm / ImageMagick, hashed in pure Python -- the app's python
                     has no Pillow; then the OCR triple), the stamp slip in Hindi, the amber near-miss with two taps,
                     approve refused on a triple already approved, re-lane one tap (audited), late bills (late_for),
                     the monthly count per lane on /purchases
  purchase_app.py    (Sanjeevni, declared)  _scans() skips rejected rows; the scan-links page counts bills from
                     setting porders.scan_from
  porders.py         (Sanjeevni, declared)  'Bill scan karo' counts bills from porders.scan_from

Usage: make_s409.py --assets /root/assetapp --finance /root/finance --out DIR
"""
import hashlib
import os
import sys

FROM = {
    "asset_register.py": "30b26d280c6cdf373774a94aae59f339",
    "purchase_app.py": "fdec7ec01d2ceb449aaa0a62956a7a0f",
    "porders.py": "78d1712a69324a06c2894c19158cd834",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


HELPERS = r'''# ---------------------------------------------------------------- S409 (D625, 26-Sep-2026): five lanes, the duplicate guard, late bills
# THE OWNER: "whoever holds the paper scans it at once and writes the number on it; a paper already carrying a B-number is
# never scanned again; each person's drop-down opens on their own head; the server catches duplicates; late bills file by
# their own date." Ownership: PARENT (the asset app). The pharmacy lane keeps its S219 meaning; S403's pre-fill still lands.
LANES = {
    "clinic":        ("Clinic bill \u2014 asset or consumable", "Consumable", "draft"),
    "pharmacy":      ("Pharmacy purchase \u2014 Sanjeevni", "Pharmacy", "captured"),
    "lab_purchase":  ("Lab purchase \u2014 NK Pathology", "Lab", "captured"),
    "owner_expense": ("Dr MK expense", "Expense", "captured"),
    "other_doc":     ("Other document \u2014 not a bill", "Document", "captured"),
}
LANE_ORDER = ("clinic", "pharmacy", "lab_purchase", "owner_expense", "other_doc")
LANE_DEFAULTS = {"sukhveer": "lab_purchase", "awdhesh": "clinic", "darpan": "pharmacy", "manoj": "owner_expense"}
KIND_LANE = {"Pharmacy": "pharmacy", "Lab": "lab_purchase", "Expense": "owner_expense", "Document": "other_doc"}
FP_GRID = (17, 16)       # the fine dHash grid: 16 rows x 16 differences = 256 bits (64 hex) -- bills.fp
FPC_GRID = (9, 8)        # the coarse dHash grid: 8 rows x 8 differences = 64 bits (16 hex) -- bills.fpc
DUP_EXACT = 8            # fine bits of 256: the same capture again (a double tap, the same file) -> rejected at once
DUP_NEAR = 6             # coarse bits of 64: a straight re-scan / re-crop of the same paper (a PDF of it, a second flatten) -> amber,
#                          the checker's two taps. Measured on the box (26-Sep): a re-crop 2-3, a PDF re-scan 3-5, unrelated papers 9+;
#                          a re-shot with a visible TILT lands at 9-13 -- the image layer does not see it; the OCR triple does.
DUP_WINDOW_DAYS = 90
LANE_SLIP_HI = "Yeh bill pehle %s par scan ho chuka hai \u2014 wahi number likho"


def _lane_key(lane):
    k = (lane or "").strip().lower()
    return k if k in LANES else "clinic"


def _lane_kind_status(lane_key):
    _label, kind, status = LANES[_lane_key(lane_key)]
    return kind, status


def _lane_for_user(db, username):
    """The lane the select opens on for this login: user_lane_default, else the seed list, else clinic."""
    u = (username or "").strip().lower()
    try:
        r = db.execute("SELECT lane FROM user_lane_default WHERE lower(username)=?", (u,)).fetchone()
        if r and r[0] in LANES:
            return r[0]
    except sqlite3.Error:
        pass
    return LANE_DEFAULTS.get(u, "clinic")


def _audit_bill(db, bid, action, detail=None):
    who = ""
    try:
        who = g.user["display_name"] if getattr(g, "user", None) else ""
    except Exception:
        who = ""
    db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
               (bid, _now_ist(), who, action, json.dumps(detail or {}, ensure_ascii=False)[:500]))


def _pgm_gray(raw):
    """A binary PGM (P5, maxval 255) -> (width, height, bytes). None when it is not one."""
    try:
        if not raw.startswith(b"P5"):
            return None
        parts, i, fields = [], 2, []
        while len(fields) < 3:
            while i < len(raw) and raw[i:i + 1].isspace():
                i += 1
            if raw[i:i + 1] == b"#":
                while raw[i:i + 1] not in (b"\n", b""):
                    i += 1
                continue
            j = i
            while j < len(raw) and not raw[j:j + 1].isspace():
                j += 1
            fields.append(int(raw[i:j]))
            i = j
        i += 1
        w, h, mx = fields
        px = raw[i:i + w * h]
        if mx != 255 or len(px) < w * h:
            return None
        return w, h, px
    except Exception:
        return None


def _dhash_from_gray(w, h, px, grid=None):
    """Area-average the grey page to the grid (FP_GRID 17x16 -> 256 bits; FPC_GRID 9x8 -> 64 bits), then the difference hash, hex."""
    gw, gh = grid or FP_GRID
    cells = []
    for gy in range(gh):
        y0, y1 = gy * h // gh, max(gy * h // gh + 1, (gy + 1) * h // gh)
        row = []
        for gx in range(gw):
            x0, x1 = gx * w // gw, max(gx * w // gw + 1, (gx + 1) * w // gw)
            s = n = 0
            for y in range(y0, y1):
                base = y * w
                seg = px[base + x0:base + x1]
                s += sum(seg)
                n += len(seg)
            row.append(s / n if n else 0)
        cells.append(row)
    bits = 0
    for gy in range(gh):
        for gx in range(gw - 1):
            bits = (bits << 1) | (1 if cells[gy][gx] < cells[gy][gx + 1] else 0)
    return "%0*x" % ((gw - 1) * gh // 4, bits)


def _fingerprint(path, ext):
    """The perceptual fingerprints (fine, coarse) of the flattened FIRST page: pdftoppm for a PDF, ImageMagick for an image,
    both to a small grey PGM, hashed here in pure Python (the app's python has no Pillow). (None, None) when the tools cannot
    read it -- the OCR triple is then the only guard, and the bill says so (fp NULL)."""
    tmp = None
    try:
        if ext == "pdf":
            tmp = tempfile.mkdtemp(prefix="fp409_")
            root = os.path.join(tmp, "p")
            subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-gray", "-scale-to", "96", "-singlefile", path, root],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            with open(root + ".pgm", "rb") as fh:
                raw = fh.read()
        else:
            p = subprocess.run(["convert", path + "[0]", "-colorspace", "Gray", "-resize", "96x96!", "-depth", "8", "pgm:-"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
            raw = p.stdout
        g_ = _pgm_gray(raw)
        if not g_:
            return None, None
        return _dhash_from_gray(*g_), _dhash_from_gray(*g_, grid=FPC_GRID)
    except Exception:
        return None, None
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def _hamming(a, b):
    try:
        if len(a) != len(b):
            return 256
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except (TypeError, ValueError):
        return 256


def _dup_by_fp(db, bid, fp, fpc):
    """(the nearest earlier bill of the last 90 days, not rejected; its fine distance; its coarse distance) -- the nearest by
    the coarse hash among those within DUP_NEAR coarse bits or DUP_EXACT fine bits; (None, None, None) when none."""
    if not fp or not fpc:
        return None, None, None
    since = (datetime.date.today() - datetime.timedelta(days=DUP_WINDOW_DAYS)).isoformat()
    best = None
    for r in db.execute("SELECT id, stamp_no, fp, fpc FROM bills WHERE id<>? AND fp IS NOT NULL AND status<>'rejected' "
                        "AND substr(created_at,1,10)>=? ORDER BY id DESC LIMIT 2000", (bid, since)):
        df = _hamming(fp, r["fp"])
        dc = _hamming(fpc, r["fpc"] or "") if r["fpc"] else 64
        if (df <= DUP_EXACT or dc <= DUP_NEAR) and (best is None or (dc, df) < (best[2], best[1])):
            best = (r, df, dc)
    return best if best else (None, None, None)


def _triple(b):
    v = " ".join((b["vendor"] or "").upper().split())
    n = re.sub(r"[^A-Z0-9]", "", (b["bill_no"] or "").upper())
    t = b["total_amount"]
    return v, n, (round(float(t), 2) if t not in (None, "") else None)


def _dup_by_triple(db, bid, approved_only=False):
    """(exact, near): exact = an earlier bill with the same vendor + bill no + total; near = same vendor + total with
    the bill number unreadable on either side. Last 90 days, not rejected, never itself."""
    b = db.execute("SELECT id, vendor, bill_no, total_amount FROM bills WHERE id=?", (bid,)).fetchone()
    if not b:
        return None, None
    v, n, t = _triple(b)
    if not v or t is None:
        return None, None
    since = (datetime.date.today() - datetime.timedelta(days=DUP_WINDOW_DAYS)).isoformat()
    exact = near = None
    sql = ("SELECT id, stamp_no, vendor, bill_no, total_amount, status FROM bills WHERE id<>? AND status<>'rejected' "
           "AND substr(created_at,1,10)>=? " + ("AND status='approved' " if approved_only else "") + "ORDER BY id ASC LIMIT 2000")   # the oldest = the original
    for r in db.execute(sql, (bid, since)):
        v2, n2, t2 = _triple(r)
        if v2 != v or t2 != t:
            continue
        if n and n2 and n == n2:
            exact = exact or r
        elif not n or not n2:
            near = near or r
    return exact, near


def _mark_dup(db, bid, first, how):
    """The new bill is rejected as a duplicate of `first`; its stamp stays (void-pair). The paper carries the first number."""
    db.execute("UPDATE bills SET status='rejected', dup_of=?, dup_flag='yes', dup_why=?, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",
               (first["id"], how, "duplicate of %s" % (first["stamp_no"] or ("#%d" % first["id"])), "server (duplicate guard)", _now_ist(), bid))
    _audit_bill(db, bid, "duplicate", {"of": first["id"], "of_stamp": first["stamp_no"], "how": how})


def _mark_maybe(db, bid, cand, how):
    """Amber for the checker: two taps decide. Never overwrites a decision already taken."""
    db.execute("UPDATE bills SET dup_flag='maybe', dup_cand=?, dup_why=? WHERE id=? AND (dup_flag IS NULL OR dup_flag='')", (cand["id"], how, bid))
    _audit_bill(db, bid, "maybe_duplicate", {"cand": cand["id"], "cand_stamp": cand["stamp_no"], "how": how})


def _dup_after_ocr(db, bid):
    """Layer (b), after the OCR has filled the header: the triple -> rejected; a near-miss -> amber 'maybe' for the checker;
    an image amber whose bill number the OCR now reads as DIFFERENT from its candidate's is cleared by itself (a second bill on
    the same printed form is not a duplicate)."""
    b = db.execute("SELECT id, status, dup_of, dup_flag, dup_cand, dup_why, vendor, bill_no, total_amount FROM bills WHERE id=?", (bid,)).fetchone()
    if not b or b["status"] == "rejected" or b["dup_flag"] in ("yes", "no"):
        return
    exact, near = _dup_by_triple(db, bid)
    if exact:
        _mark_dup(db, bid, exact, "vendor+bill+amount")
        return
    if b["dup_flag"] == "maybe" and (b["dup_why"] or "").startswith("image") and b["dup_cand"]:
        c = db.execute("SELECT id, vendor, bill_no, total_amount FROM bills WHERE id=?", (b["dup_cand"],)).fetchone()
        if c:
            v1, n1, t1 = _triple(b)
            v2, n2, t2 = _triple(c)
            if n1 and n2 and (n1 != n2 or v1 != v2):
                db.execute("UPDATE bills SET dup_flag='no', dup_why=? WHERE id=?", ("ocr: a different bill (%s vs %s)" % (n1, n2), bid))
                _audit_bill(db, bid, "not_duplicate", {"cand": c["id"], "how": "ocr: different bill number"})
                return
    if near and b["dup_flag"] != "maybe":
        _mark_maybe(db, bid, near, "vendor+amount, bill number unread")


def _set_late(db, bid):
    """A bill scanned in a later month than its bill_date carries late_for=<YYYY-MM> (S408 files it under 'Late')."""
    b = db.execute("SELECT bill_date, created_at FROM bills WHERE id=?", (bid,)).fetchone()
    if not b:
        return
    bd = _norm_date(b["bill_date"]) if b["bill_date"] else None
    late = None
    if bd and re.match(r"^\d{4}-\d{2}-\d{2}$", bd) and bd[:7] < (b["created_at"] or "")[:7]:
        late = bd[:7]
    db.execute("UPDATE bills SET late_for=? WHERE id=?", (late, bid))


def _lane_month_line(db):
    """One line for the owner's /purchases page: this month's scans per lane (plus the late ones)."""
    ym = datetime.date.today().strftime("%Y-%m")
    counts = {k: 0 for k in LANE_ORDER}
    late = 0
    for lane, n in db.execute("SELECT COALESCE(lane,'clinic'), COUNT(*) FROM bills WHERE stamp_no IS NOT NULL "
                              "AND substr(created_at,1,7)=? AND status<>'rejected' GROUP BY 1", (ym,)):
        counts[lane if lane in counts else "clinic"] += n
    late = db.execute("SELECT COUNT(*) FROM bills WHERE stamp_no IS NOT NULL AND substr(created_at,1,7)=? AND late_for IS NOT NULL "
                      "AND status<>'rejected'", (ym,)).fetchone()[0]
    dups = db.execute("SELECT COUNT(*) FROM bills WHERE substr(created_at,1,7)=? AND dup_of IS NOT NULL", (ym,)).fetchone()[0]
    return "Scans this month \u2014 clinic %d \u00b7 pharmacy %d \u00b7 lab %d \u00b7 expense %d \u00b7 other %d (late %d, duplicates caught %d)" % (
        counts["clinic"], counts["pharmacy"], counts["lab_purchase"], counts["owner_expense"], counts["other_doc"], late, dups)


'''

LANE_ROUTES = r'''# ---------------------------------------------------------------- S409: re-lane, the duplicate taps, the owner's lane defaults
@app.route("/bills/<int:bid>/lane", methods=["POST"])
@checker_required
def bill_lane(bid):
    """Re-lane, one tap (owner / manager). Into clinic = a draft for approval; out of it = captured. An approved bill
    never leaves clinic. Audited (who, when, from -> to)."""
    db = get_db()
    b = _bill_or_404(bid)
    to = _lane_key(request.form.get("lane"))
    frm = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
    if to == frm:
        flash("Already on that lane.")
        return redirect(request.form.get("back") or url_for("bill_view", bid=bid))
    if b["status"] == "approved" and to != "clinic":
        flash("%s is approved on the clinic lane; an approved bill cannot leave it." % (b["stamp_no"] or ("#%d" % bid)))
        return redirect(request.form.get("back") or url_for("bill_view", bid=bid))
    if b["status"] == "rejected":
        flash("A rejected bill stays where it is.")
        return redirect(request.form.get("back") or url_for("bill_view", bid=bid))
    kind, status = _lane_kind_status(to)
    if b["status"] == "approved":
        status = "approved"
    db.execute("UPDATE bills SET lane=?, kind=?, status=? WHERE id=?", (to, kind, status, bid))
    _audit_bill(db, bid, "relane", {"from": frm, "to": to, "status": status})
    db.commit()
    flash("%s moved to %s." % (b["stamp_no"] or ("#%d" % bid), LANES[to][0]))
    return redirect(request.form.get("back") or url_for("bill_view", bid=bid))


@app.route("/bills/<int:bid>/dup", methods=["POST"])
@checker_required
def bill_dup(bid):
    """The checker's two taps on an amber near-miss: Duplicate (rejected, dup_of the candidate) / Not duplicate."""
    db = get_db()
    b = _bill_or_404(bid)
    what = (request.form.get("what") or "").strip()
    if b["dup_flag"] != "maybe":
        flash("Nothing to decide on %s." % (b["stamp_no"] or ("#%d" % bid)))
        return redirect(request.form.get("back") or url_for("bill_view", bid=bid))
    if what == "yes":
        first = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["dup_cand"],)).fetchone()
        if not first:
            flash("The other bill is gone; nothing changed.")
            return redirect(request.form.get("back") or url_for("bill_view", bid=bid))
        _mark_dup(db, bid, first, "checker")
        db.commit()
        flash("%s marked a duplicate of %s." % (b["stamp_no"] or ("#%d" % bid), first["stamp_no"] or ("#%d" % first["id"])))
    elif what == "no":
        db.execute("UPDATE bills SET dup_flag='no' WHERE id=?", (bid,))
        _audit_bill(db, bid, "not_duplicate", {"cand": b["dup_cand"]})
        db.commit()
        flash("%s kept — not a duplicate." % (b["stamp_no"] or ("#%d" % bid)))
    else:
        flash("Duplicate or Not duplicate.")
    return redirect(request.form.get("back") or url_for("bill_view", bid=bid))


@app.route("/lanes", methods=["GET", "POST"])
@owner_required
def lanes_admin():
    """The owner's card: which lane each login's drop-down opens on."""
    db = get_db()
    if request.method == "POST":
        u = (request.form.get("username") or "").strip().lower()
        lane = _lane_key(request.form.get("lane"))
        if u:
            db.execute("INSERT INTO user_lane_default(username, lane, set_by, set_at) VALUES(?,?,?,?) "
                       "ON CONFLICT(username) DO UPDATE SET lane=excluded.lane, set_by=excluded.set_by, set_at=excluded.set_at",
                       (u, lane, g.user["display_name"], _now_ist()))
            db.commit()
            flash("%s opens on %s." % (u, LANES[lane][0]))
        return redirect(url_for("lanes_admin"))
    rows = db.execute("SELECT username, lane, set_by, set_at FROM user_lane_default ORDER BY username").fetchall()
    known = {r["username"] for r in rows}
    seeded = [(u, l) for u, l in LANE_DEFAULTS.items() if u not in known]
    return page("""<h2>Scan lanes \u2014 who opens on what</h2>
<p><a class="btn small" href="{{url_for('bills_list')}}">\u2190 Purchases</a></p>
<div class=card><p class=muted>Whoever holds the paper scans it and writes the number on it. Each login's drop-down opens on their own lane; the server catches a paper scanned twice.</p>
<table><tr><th>Login</th><th>Opens on</th><th>Set by</th></tr>
{% for r in rows %}<tr><td>{{r['username']}}</td><td>{{lanes[r['lane']][0]}}</td><td class=muted>{{r['set_by'] or ''}} {{(r['set_at'] or '')[:16]}}</td></tr>{% endfor %}
{% for u,l in seeded %}<tr><td>{{u}}</td><td>{{lanes[l][0]}}</td><td class=muted>seed (S409)</td></tr>{% endfor %}
<tr><td colspan=3 class=muted>everyone else opens on {{lanes['clinic'][0]}}</td></tr></table>
<form method=post style="margin-top:10px"><input name=username placeholder="login (e.g. shavez)" style="max-width:180px">
<select name=lane style="width:auto">{% for k in order %}<option value="{{k}}">{{lanes[k][0]}}</option>{% endfor %}</select>
<button class="btn small">Save</button></form></div>""", rows=rows, seeded=seeded, lanes=LANES, order=LANE_ORDER)


'''


def build_assets(s):
    s = rep(s, '''import os, re, sqlite3, secrets, functools, datetime, mimetypes
''', '''import os, re, sqlite3, secrets, functools, datetime, mimetypes, subprocess, json, tempfile, shutil
''', "imports")
    s = rep(s, '''APP_VERSION = "1.11.0"  # A-D24:''', '''APP_VERSION = "1.12.0"  # S409 (D625, 26-Sep-2026): five scan lanes (bills.lane), the duplicate guard at capture (a perceptual dHash through pdftoppm/ImageMagick + the OCR triple), the Hindi stamp slip, re-lane one tap, late bills, per-user default lanes. 1.11.0 -- A-D24:''', "version")
    s = rep(s, '''        if _bc not in bcols:
            db.execute(_bddl)
''', '''        if _bc not in bcols:
            db.execute(_bddl)
    # S409 (D625): the lane, the fingerprint, the duplicate marks, the late month; the per-user default lane; the audit
    bcols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    for _bc, _bddl in [
        ("lane",     "ALTER TABLE bills ADD COLUMN lane TEXT"),
        ("fp",       "ALTER TABLE bills ADD COLUMN fp TEXT"),
        ("fpc",      "ALTER TABLE bills ADD COLUMN fpc TEXT"),
        ("dup_of",   "ALTER TABLE bills ADD COLUMN dup_of INTEGER"),
        ("dup_flag", "ALTER TABLE bills ADD COLUMN dup_flag TEXT"),
        ("dup_cand", "ALTER TABLE bills ADD COLUMN dup_cand INTEGER"),
        ("dup_why",  "ALTER TABLE bills ADD COLUMN dup_why TEXT"),
        ("late_for", "ALTER TABLE bills ADD COLUMN late_for TEXT"),
    ]:
        if _bc not in bcols:
            db.execute(_bddl)
    db.execute("UPDATE bills SET lane=CASE WHEN kind='Pharmacy' THEN 'pharmacy' WHEN kind='Lab' THEN 'lab_purchase' "
               "WHEN kind='Expense' THEN 'owner_expense' WHEN kind='Document' THEN 'other_doc' ELSE 'clinic' END WHERE lane IS NULL")
    db.execute("CREATE TABLE IF NOT EXISTS user_lane_default(username TEXT PRIMARY KEY, lane TEXT NOT NULL, set_by TEXT, set_at TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS bill_audit(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, at TEXT NOT NULL, "
               "who TEXT, action TEXT NOT NULL, detail TEXT)")
''', "migrate")
    s = rep(s, '''    if fk in ("Asset", "Consumable", "Pharmacy"):
        where += " AND b.kind=?"
        params.append(fk)
''', '''    if fk in ("Asset", "Consumable", "Pharmacy", "Lab", "Expense", "Document"):    # S409: the lanes' kinds
        where += " AND b.kind=?"
        params.append(fk)
''', "list kind filter")
    s = rep(s, '''<select name=kind onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Kind: all</option><option {{'selected' if fk=='Consumable'}}>Consumable</option><option {{'selected' if fk=='Asset'}}>Asset</option><option {{'selected' if fk=='Pharmacy'}}>Pharmacy</option></select>
''', '''<select name=kind onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Kind: all</option><option {{'selected' if fk=='Consumable'}}>Consumable</option><option {{'selected' if fk=='Asset'}}>Asset</option><option {{'selected' if fk=='Pharmacy'}}>Pharmacy</option><option {{'selected' if fk=='Lab'}}>Lab</option><option {{'selected' if fk=='Expense'}}>Expense</option><option {{'selected' if fk=='Document'}}>Document</option></select>
''', "list kind select")
    s = rep(s, '''<a class="btn small" href="{{url_for('intake')}}">📷 Scan intake</a>
{% if is_owner %}<a class="btn small" href="{{url_for('purchases')}}">\\U0001F4C8 Consumption &amp; rate history</a>{% endif %}</p>
<table><tr><th>Stamp</th><th>Status</th><th>Date</th><th>Vendor</th><th>Bill no</th><th>Kind</th><th>Items</th><th>Total</th></tr>
{% for b in bills %}<tr class="{{'amber' if b['status']=='draft' else ('red' if b['status']=='rejected' else '')}}"><td>{{b['stamp_no'] or '\\u2014'}}</td>
''', '''<a class="btn small" href="{{url_for('intake')}}">📷 Scan intake</a>
{% if is_owner %}<a class="btn small" href="{{url_for('purchases')}}">\\U0001F4C8 Consumption &amp; rate history</a> <a class="btn small" href="{{url_for('lanes_admin')}}">Scan lanes</a>{% endif %}</p>
<table><tr><th>Stamp</th><th>Status</th><th>Date</th><th>Vendor</th><th>Bill no</th><th>Kind</th><th>Lane</th><th>Items</th><th>Total</th></tr>
{% for b in bills %}<tr class="{{'amber' if (b['status']=='draft' or b['dup_flag']=='maybe') else ('red' if b['status']=='rejected' else '')}}"><td>{{b['stamp_no'] or '\\u2014'}}{% if b['dup_of'] %} <span class="badge red" title="duplicate">dup</span>{% endif %}{% if b['late_for'] %} <span class="badge amber" title="belongs to {{b['late_for']}}">late</span>{% endif %}</td>
''', "list header + stamp cell")
    s = rep(s, '''<td>{{b['bill_no'] or '\\u2014'}}</td><td>{{b['kind']}}</td><td>{{b['nitems']}}</td>
<td>{{'\\u20b9%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '\\u2014'}}</td></tr>{% endfor %}</table>
''', '''<td>{{b['bill_no'] or '\\u2014'}}</td><td>{{b['kind']}}</td>
<td>{% if b['dup_flag']=='maybe' %}<span class="badge amber" title="{{b['dup_why'] or ''}}">second scan of {{dupstamp.get(b['dup_cand']) or ('#'~b['dup_cand'])}}? ({{b['dup_why'] or ''}})</span>
<form method=post action="{{url_for('bill_dup',bid=b['id'])}}" style="display:inline"><input type=hidden name=back value="{{url_for('bills_list')}}"><button class="btn small" name=what value=yes>Duplicate</button> <button class="btn small" name=what value=no>Not duplicate</button></form>
{% elif b['status']=='rejected' %}<span class=muted>{{lanes[b['lane'] or 'clinic'][0].split(' ')[0]}}</span>
{% else %}<form method=post action="{{url_for('bill_lane',bid=b['id'])}}" style="display:inline"><input type=hidden name=back value="{{url_for('bills_list')}}"><select name=lane style="width:auto;max-width:130px" onchange="this.form.submit()">{% for k in lane_order %}<option value="{{k}}" {{'selected' if (b['lane'] or 'clinic')==k}}>{{lanes[k][0].split(' \\u2014 ')[0]}}</option>{% endfor %}</select></form>{% endif %}</td>
<td>{{b['nitems']}}</td>
<td>{{'\\u20b9%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '\\u2014'}}</td></tr>{% endfor %}</table>
''', "list row lane cell")
    s = rep(s, '''        bills=bills, q=q, fk=fk, fs=fs, npend=npend)
''', '''        bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES, lane_order=LANE_ORDER,
        dupstamp={r["id"]: r["stamp_no"] for r in db.execute("SELECT id, stamp_no FROM bills WHERE id IN (SELECT dup_cand FROM bills WHERE dup_flag='maybe')")})
''', "list kwargs")
    s = rep(s, '''<b>Date:</b> {{b['bill_date'] or '—'}}<br><b>Kind:</b> {{b['kind']}}<br>
''', '''<b>Date:</b> {{b['bill_date'] or '—'}}{% if b['late_for'] %} <span class="badge amber">late — belongs to {{b['late_for']}}</span>{% endif %}<br><b>Kind:</b> {{b['kind']}}<br>
<b>Lane:</b> {{lanes[b['lane'] or 'clinic'][0]}}{% if b['status']!='rejected' %} <form method=post action="{{url_for('bill_lane',bid=b['id'])}}" style="display:inline"><select name=lane style="width:auto;max-width:190px">{% for k in lane_order %}<option value="{{k}}" {{'selected' if (b['lane'] or 'clinic')==k}}>{{lanes[k][0]}}</option>{% endfor %}</select> <button class="btn small">move</button></form>{% endif %}<br>
{% if b['dup_of'] %}<span class="badge red">duplicate of {{dupstamp or ('#'~b['dup_of'])}}</span><br>{% endif %}
{% if b['dup_flag']=='maybe' %}<span class="badge amber">second scan of {{candstamp or ('#'~b['dup_cand'])}}? — {{b['dup_why'] or ''}}</span>
<form method=post action="{{url_for('bill_dup',bid=b['id'])}}" style="display:inline"><button class="btn small" name=what value=yes>Duplicate</button> <button class="btn small" name=what value=no>Not duplicate</button></form><br>{% endif %}
''', "view lane line")
    s = rep(s, '''        b=b, items=items, sarvam_on=_sarvam_on(), blank=blank)
''', '''        b=b, items=items, sarvam_on=_sarvam_on(), blank=blank, lanes=LANES, lane_order=LANE_ORDER,
        dupstamp=(db.execute("SELECT stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone() or [None])[0] if b["dup_of"] else None,
        candstamp=(db.execute("SELECT stamp_no FROM bills WHERE id=?", (b["dup_cand"],)).fetchone() or [None])[0] if b["dup_cand"] else None)
''', "view kwargs")
    s = rep(s, '''INTAKE_PREFILL = ("lane", "vendor", "bill_no", "bill_date", "amount")
''', HELPERS + '''INTAKE_PREFILL = ("lane", "vendor", "bill_no", "bill_date", "amount")
''', "helpers")
    s = rep(s, '''    if out.get("lane") not in ("pharmacy", "clinic"):
        out.pop("lane", None)
''', '''    if out.get("lane") not in LANES:                          # S409: the five lanes
        out.pop("lane", None)
''', "prefill lanes")
    s = rep(s, '''    widget_url = url_for("scanner_widget_js") + "?v=" + str(_widget_version())
    return page("""<h2>🧾 Scan a new purchase bill</h2>
''', '''    widget_url = url_for("scanner_widget_js") + "?v=" + str(_widget_version())
    _lane_default = _lane_for_user(db, g.user["username"])      # S409: each person's drop-down opens on their own head
    scan_cfg["uploadFields"].setdefault("lane", _lane_default)
    return page("""<h2>🧾 Scan a new purchase bill</h2>
''', "intake default lane")
    s = rep(s, '''<option value="clinic">Clinic bill — asset or consumable</option>
<option value="pharmacy">Pharmacy purchase — Sanjeevni</option>
</select>
<p class=muted style="margin:4px 0 0">A pharmacy bill is filed as a scan and a stamp only.
It does not go into the clinic approval list.</p>
''', '''{% for k in lane_order %}<option value="{{k}}" {{'selected' if k==lane_default}}>{{lanes[k][0]}}</option>{% endfor %}
</select>
<p class=muted style="margin:4px 0 0">Only a clinic bill goes to the approval list. Pharmacy, lab, expense and other documents are
filed as a scan and a stamp. A paper that already carries a B-number is never scanned again — the server catches a double scan.</p>
''', "intake select")
    s = rep(s, '''<input type=hidden name=lane id=lane_basic value="clinic">
''', '''<input type=hidden name=lane id=lane_basic value="{{lane_default}}">
''', "basic lane default")
    s = rep(s, '''        mine=mine, scan_cfg=scan_cfg, widget_url=widget_url)
''', '''        mine=mine, scan_cfg=scan_cfg, widget_url=widget_url, lanes=LANES, lane_order=LANE_ORDER, lane_default=_lane_default)
''', "intake kwargs")
    s = rep(s, '''    _pharma = (lane or "").strip().lower() == "pharmacy"
    pf = prefill or {}                                       # S403: the Purchase orders link's vendor / bill no / date / amount
    cur = db.execute(
        "INSERT INTO bills(kind,notes,source_stored,source_orig,stamp_no,status,"
        "submitted_by,submitted_at,vendor,bill_no,bill_date,total_amount) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("Pharmacy" if _pharma else "Consumable", note, stored,
         secure_filename(fobj.filename), stamp,
         "captured" if _pharma else "draft",
         g.user["display_name"], _now_ist(),
         (pf.get("vendor") or None), (pf.get("bill_no") or None),
         (_norm_date(pf.get("bill_date")) if pf.get("bill_date") else None),
         (_num(pf.get("amount")) if pf.get("amount") else None)))
    bid = cur.lastrowid
    db.commit()
''', '''    _lane = _lane_key(lane)                                  # S409 (D625): five lanes; an unknown value is the clinic lane, as before
    _kind, _status = _lane_kind_status(_lane)
    pf = prefill or {}                                       # S403: the Purchase orders link's vendor / bill no / date / amount
    cur = db.execute(
        "INSERT INTO bills(kind,notes,source_stored,source_orig,stamp_no,status,"
        "submitted_by,submitted_at,vendor,bill_no,bill_date,total_amount,lane) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (_kind, note, stored,
         secure_filename(fobj.filename), stamp,
         _status,
         g.user["display_name"], _now_ist(),
         (pf.get("vendor") or None), (pf.get("bill_no") or None),
         (_norm_date(pf.get("bill_date")) if pf.get("bill_date") else None),
         (_num(pf.get("amount")) if pf.get("amount") else None), _lane))
    bid = cur.lastrowid
    db.commit()
    # S409: the duplicate guard, layer (a) -- the image fingerprint of the flattened first page, at capture.
    # Within DUP_EXACT bits = the same capture again -> rejected on the spot, the slip names the first stamp.
    # Within DUP_NEAR = a re-shot of the same paper OR a different bill on the same printed form -> amber, the checker's two taps
    # (a genuine second bill must never be thrown away by a layout match); the OCR triple then settles most of these by itself.
    _fp, _fpc = _fingerprint(path, ext)
    if _fp:
        db.execute("UPDATE bills SET fp=?, fpc=? WHERE id=?", (_fp, _fpc, bid))
        _first, _df, _dc = _dup_by_fp(db, bid, _fp, _fpc)
        if _first is not None and _df <= DUP_EXACT:
            _mark_dup(db, bid, _first, "image (the same capture, %d bits)" % _df)
        elif _first is not None:
            _mark_maybe(db, bid, _first, "image (a re-scan of the same paper? %d bits)" % _dc)
    _set_late(db, bid)
    db.commit()
''', "create intake bill")
    s = rep(s, '''            db.execute("UPDATE bills SET ocr_status=? WHERE id=?", (status, bid))
            db.commit()
            return status
''', '''            db.execute("UPDATE bills SET ocr_status=? WHERE id=?", (status, bid))
            _set_late(db, bid)                               # S409: the OCR's bill_date decides the month it belongs to
            _dup_after_ocr(db, bid)                          # S409: layer (b) -- the triple, or the amber near-miss
            db.commit()
            return status
''', "after ocr")
    s = rep(s, '''    return page("""<div class=card style="max-width:430px;margin:26px auto;text-align:center">
<p class=muted>Write this number on the paper bill:</p>
<div style="font-size:64px;font-weight:800;letter-spacing:3px;color:#1f3864">{{b['stamp_no']}}</div>
<p><b>{{b['submitted_by']}}</b> · {{b['submitted_at']}}</p>
<p class=muted>The bill has been sent for checking. You can hand the paper back now.</p>
<a class=btn href="{{url_for('intake')}}">Scan another</a></div>""", b=b)
''', '''    first = None
    if b["dup_of"]:
        first = get_db().execute("SELECT stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()
    first_stamp = (first["stamp_no"] if first else None) or ("#%d" % (b["dup_of"] or 0))
    if request.args.get("json"):                            # S409: the slip polls for the OCR's duplicate verdict
        return jsonify(id=b["id"], stamp=b["stamp_no"], status=b["status"], dup_of=b["dup_of"], first_stamp=(first_stamp if b["dup_of"] else None),
                       message=(LANE_SLIP_HI % first_stamp) if b["dup_of"] else None, lane=b["lane"], ocr_status=b["ocr_status"])
    return page("""<div class=card style="max-width:430px;margin:26px auto;text-align:center" id=slipcard>
{% if b['dup_of'] %}<p style="font-size:20px;font-weight:700;color:#b23b3b">{{dup_msg}}</p>
<div style="font-size:64px;font-weight:800;letter-spacing:3px;color:#1f3864">{{first_stamp}}</div>
<p class=muted>Is scan ka number {{b['stamp_no']}} khaali chhod diya gaya (void). Kaagaz par <b>{{first_stamp}}</b> hi likhein.</p>
{% else %}<p class=muted>Write this number on the paper bill:</p>
<div style="font-size:64px;font-weight:800;letter-spacing:3px;color:#1f3864" id=slipstamp>{{b['stamp_no']}}</div>
<p><b>{{b['submitted_by']}}</b> · {{b['submitted_at']}}</p>
<p class=muted id=slipnote>{{'The bill has been sent for checking. You can hand the paper back now.' if b['lane'] in (None,'clinic') else 'Filed as a scan and a stamp (' ~ lanes[b['lane']][0] ~ '). You can hand the paper back now.'}}</p>
<script>(function(){var n=0,t=setInterval(function(){n++;fetch('{{url_for('intake_slip',bid=b['id'])}}?json=1',{cache:'no-store'}).then(function(r){return r.json()}).then(function(j){
 if(j.dup_of){clearInterval(t);var c=document.getElementById('slipcard');if(c){c.innerHTML='<p style="font-size:20px;font-weight:700;color:#b23b3b">'+j.message+'</p><div style="font-size:64px;font-weight:800;letter-spacing:3px;color:#1f3864">'+j.first_stamp+'</div><p class=muted>Is scan ka number '+j.stamp+' khaali chhod diya gaya (void). Kaagaz par <b>'+j.first_stamp+'</b> hi likhein.</p><a class=btn href="{{url_for('intake')}}">Scan another</a>';}}
 else if(j.ocr_status&&j.ocr_status!=='reading'){clearInterval(t);}
 if(n>=12)clearInterval(t);}).catch(function(){});},2500);})();</script>
{% endif %}<a class=btn href="{{url_for('intake')}}">Scan another</a></div>""", b=b, lanes=LANES, first_stamp=first_stamp,
        dup_msg=(LANE_SLIP_HI % first_stamp))
''', "the slip")
    s = rep(s, '''        # 'Pharmacy' MUST be in this whitelist: it is a fall-through to
        # "Consumable", so without it any edit of a pharmacy bill would silently
        # move it into the clinic lane -- and silently is how it would happen.
        kind = f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy") else "Consumable"
''', '''        # 'Pharmacy' MUST be in this whitelist: it is a fall-through to
        # "Consumable", so without it any edit of a pharmacy bill would silently
        # move it into the clinic lane -- and silently is how it would happen.
        # S409: the lanes' kinds join it; an edit never moves a bill off its lane (re-lane is its own tap).
        kind = f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy", "Lab", "Expense", "Document") else (b["kind"] if b["kind"] in ("Lab", "Expense", "Document") else "Consumable")
''', "edit kind")
    s = rep(s, '''        db.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))   # draft: no asset links yet
''', '''        _set_late(db, bid)                                   # S409: the checker's corrected date decides the month
        db.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))   # draft: no asset links yet
''', "edit late")
    s = rep(s, '''    # A-D21 lane guard, enforced SERVER-SIDE independent of the UI:
    # Consumable -> manager or owner; Asset-kind -> owner (doctor) ONLY.
    if b["kind"] == "Asset" and not is_owner():
        abort(403)
''', '''    # A-D21 lane guard, enforced SERVER-SIDE independent of the UI:
    # Consumable -> manager or owner; Asset-kind -> owner (doctor) ONLY.
    if b["kind"] == "Asset" and not is_owner():
        abort(403)
    # S409 (D625): a bill whose vendor + bill number + amount are already APPROVED is refused, naming the stamp
    _exact, _near = _dup_by_triple(db, bid, approved_only=True)
    if _exact:
        flash("Not approved: the same vendor, bill number and amount are already approved as %s. Mark this one Duplicate, or correct it."
              % (_exact["stamp_no"] or ("#%d" % _exact["id"])))
        _mark_maybe(db, bid, _exact, "vendor+bill+amount already approved")
        db.commit()
        return redirect(url_for("bill_view", bid=bid))
''', "approve guard")
    s = rep(s, '''# ---------------------------------------------------------------- A-D21: vendor directory
''', LANE_ROUTES + '''# ---------------------------------------------------------------- A-D21: vendor directory
''', "lane routes")
    s = rep(s, '''    # A-D24: spend analytics — approved bills only, Indian-format ₹, dependency-free bars
''', '''    lane_line = _lane_month_line(db)                         # S409: this month's scans per lane, one line
    # A-D24: spend analytics — approved bills only, Indian-format ₹, dependency-free bars
''', "purchases lane line compute")
    s = rep(s, '''    return page("""<h2>💰 Consumption &amp; spend</h2>
<p><a class="btn small" href="{{url_for('bills_list')}}">\\u2190 Purchases</a></p>
''', '''    return page("""<h2>💰 Consumption &amp; spend</h2>
<p><a class="btn small" href="{{url_for('bills_list')}}">\\u2190 Purchases</a></p>
<p class=muted id=lane_line>{{lane_line}}</p>
''', "purchases lane line")
    s = rep(s, '''        soon=soon, items=items, total_spend=total_spend, month_spend=month_spend,
        this_month=_ym_human(this_ym), spend=spend, vends=vends)
''', '''        soon=soon, items=items, total_spend=total_spend, month_spend=month_spend,
        this_month=_ym_human(this_ym), spend=spend, vends=vends, lane_line=lane_line)
''', "purchases kwargs")
    return s


# ---------------------------------------------------------------- purchase_app.py (Sanjeevni, declared)
def build_purchase(s):
    s = rep(s, '''    rows = acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' ORDER BY id DESC LIMIT 2000"
                        % sel).fetchall()
''', '''    rows = acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND COALESCE(status,'')<>'rejected' ORDER BY id DESC LIMIT 2000"   # S409: a duplicate never reaches the match
                        % sel).fetchall()
''', "scans skip rejected")
    s = rep(s, '''@bp.route("/page/scans")
def page_scans():
    u, err = _person("checker", "maker", "viewer")
''', '''def _scan_from_s409(con):
    """S409 (D625): the owner's ruling -- pharmacy bill scanning starts from setting porders.scan_from (01-Sep-2026)."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='porders.scan_from'").fetchone()
        v = str(r[0]).strip() if r and r[0] else ""
        return v if re.match(r"^\\d{4}-\\d{2}-\\d{2}$", v) else "2026-09-01"
    except sqlite3.Error:
        return "2026-09-01"


@bp.route("/page/scans")
def page_scans():
    u, err = _person("checker", "maker", "viewer")
''', "scan_from helper (before the route decorator, never between it and its function)")
    s = rep(s, '''    bills = con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL +
                        " ORDER BY b.bill_date DESC, b.supplier").fetchall()
''', '''    bills = con.execute("SELECT b.* FROM purchase_bill b WHERE b.bill_date>=? AND " + EFF_BILL +      # S409: from porders.scan_from
                        " ORDER BY b.bill_date DESC, b.supplier", (_scan_from_s409(con),)).fetchall()
''', "scans page from-date")
    return s


# ---------------------------------------------------------------- porders.py (Sanjeevni, declared)
def build_porders(s):
    s = rep(s, '''def unscanned_bills(con):
    """Marg purchase bills since 17-Aug with no scan link, oldest first; red after SCAN_RED_DAYS."""
''', '''def _scan_from(con):
    """S409 (D625): the owner's ruling -- pharmacy bill scanning starts from setting porders.scan_from (01-Sep-2026)."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='porders.scan_from'").fetchone()
        v = str(r[0]).strip() if r and r[0] else ""
        return v if re.match(r"^\\d{4}-\\d{2}-\\d{2}$", v) else "2026-09-01"
    except sqlite3.Error:
        return "2026-09-01"


def unscanned_bills(con):
    """Marg purchase bills since porders.scan_from (S409; was 17-Aug) with no scan link, oldest first; red after SCAN_RED_DAYS."""
''', "porders scan_from helper")
    s = rep(s, '''        rows = con.execute("SELECT b.id, b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p, b.month FROM purchase_bill b WHERE b.bill_date>='2026-08-17' AND "
                           + pa.EFF_BILL + " ORDER BY b.bill_date, b.supplier").fetchall()
''', '''        rows = con.execute("SELECT b.id, b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p, b.month FROM purchase_bill b WHERE b.bill_date>=? AND "
                           + pa.EFF_BILL + " ORDER BY b.bill_date, b.supplier", (_scan_from(con),)).fetchall()
''', "porders from-date")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    ast, fin, out = args.get("--assets"), args.get("--finance"), args.get("--out")
    if not (ast and fin and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {
        "asset_register.py": build_assets(load(os.path.join(ast, "asset_register.py"), "asset_register.py")),
        "purchase_app.py": build_purchase(load(os.path.join(fin, "purchase_app.py"), "purchase_app.py")),
        "porders.py": build_porders(load(os.path.join(fin, "porders.py"), "porders.py")),
    }
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
