# ---------------------------------------------------------------- S440 (D640, F-662, 30-Sep-2026): the scan flow for staff
# THE OWNER: "Whatever needs to be done should be clearly mentioned in the staff scan app ... a back-to-top float on long
# pages, a prominent BACK button at the top for good navigation, and easy flow. I need this system working properly to
# shift to it." Ownership: PARENT (the asset app); declared in the Sanjeevni brief S440_SCAN_FLOW.
#   * Every page of the scan flow (intake, the stamp slip, the Purchases list, a bill, Scan lanes) carries ONE sticky bar
#     -- "← BACK" on the left (to the page the person came from, ?from=, else the portal's tile hub), the page's name on
#     the right -- and a floating up-arrow once the page has scrolled a screen.
#   * A scanning login (the portal's staff: role 'reception') sees that bar INSTEAD of the register's menu, and may now
#     open, read-only, the list of what it scanned itself and each of those bills -- the rule the intake's "My
#     submissions" and the slip have always kept (A-D21). The IMAGE of a pharmacy scan is open to every scanning login:
#     the Purchase orders screen ("Scan ka kaam") shows it beside the line a person must decide. A scanning login may
#     move a captured pharmacy scan to another lane ("Galat lane") and nothing else. Everything else stays refused.
#   * The status of a scan in staff words comes from finance's read door (/finance/porders/api/scan-status), asked with
#     the person's own portal cookie; when it cannot be asked the list simply says "Scan ho gaya".
S440_HUB_PATH = "/portal"
S440_SITE = "https://followup.dr-manoj.in"
S440_FINANCE = os.environ.get("FINANCE_LOCAL_URL", "http://127.0.0.1:8106")
S440_LIST_PATH = "/finance/porders"
S440_STAFF_LANES = ("clinic", "lab_purchase", "other_doc")     # where "Galat lane" may send a pharmacy scan
S440_PAGE = 25
SCAN_STATUS_FETCH = None      # the walk puts finance's test client here; the service asks finance over the loopback


def _safe_from(v):
    """A way back inside this site: a local path and nothing else (never another host)."""
    v = (v or "").strip()
    if v.startswith("/") and not v.startswith("//") and len(v) <= 300 and not any(c in v for c in "\\\r\n\"'<>"):
        return v
    return None


def _site(path):
    """A path of the followup site: relative when this app is reached under it (/scanapp), absolute from the assets host."""
    return path if (request.script_root or not (request.host or "").startswith("assets.")) else S440_SITE + path


def _flow(name, back=None):
    """The BACK bar of a page: where the person came from (?from=), else `back`, else the portal's tile hub."""
    frm = _safe_from(request.values.get("from"))
    return {"name": name, "back": frm or back or _site(S440_HUB_PATH), "frm": frm}


def _here(full=False):
    """This page's own address inside the site (the /scanapp prefix included): what the next page's BACK returns to."""
    return (request.script_root or "") + (request.full_path.rstrip("?") if full else request.path)


def _intake_name_s440(pf):
    """The intake's name on the BACK bar: the bill it was opened for (a "Scan karo" line), else plain "Scan"."""
    v = " ".join(str(pf.get("vendor") or "").split())
    if not v:
        return "Scan"
    out = v[:28]
    if pf.get("bill_no"):
        out += " " + str(pf["bill_no"])[:20]
    if pf.get("amount"):
        out += " · ₹" + str(pf["amount"])[:12]
    return out


def scan_reader(f):
    """The Purchases list, a bill, its scan and the re-lane: the checkers as before AND a scanning login (role
    'reception'); each route then narrows what that login may see or do. Anyone else is refused."""
    @functools.wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u:
            return redirect(url_for("login", next=request.path))
        if u["role"] not in ("owner", "manager", "reception"):
            abort(403)
        g.user = u
        return f(*a, **k)
    return w


def _staff_may_see(b, image=False):
    """A scanning login sees what it scanned itself. The image of a live pharmacy scan is open to every scanning login."""
    if g.user["role"] != "reception":
        return True
    if b["submitted_by"] and b["submitted_by"] == g.user["display_name"]:
        return True
    return bool(image and (b["lane"] or KIND_LANE.get(b["kind"], "clinic")) == "pharmacy" and b["status"] != "rejected")


def _explicit_lane(db, username):
    """The lane a login was GIVEN (the owner's card or the S409 seed); None for everyone who simply opens on clinic."""
    u = (username or "").strip().lower()
    try:
        r = db.execute("SELECT lane FROM user_lane_default WHERE lower(username)=?", (u,)).fetchone()
        if r and r[0] in LANES:
            return r[0]
    except sqlite3.Error:
        pass
    return LANE_DEFAULTS.get(u)


def _scan_words(ids):
    """{scan id: {code, word, first}} from finance's read door, asked as this person. {} when it cannot be asked."""
    ids = [int(i) for i in ids][:400]
    if not ids:
        return {}
    try:
        if SCAN_STATUS_FETCH is not None:
            j = SCAN_STATUS_FETCH(ids, g.user["username"])
        else:
            import urllib.request
            tok = request.cookies.get(_sso.COOKIE_NAME) if _sso else None
            if not tok:
                return {}
            rq = urllib.request.Request(S440_FINANCE + "/finance/porders/api/scan-status?ids=" + ",".join(str(i) for i in ids),
                                        headers={"Cookie": "%s=%s" % (_sso.COOKIE_NAME, tok)})
            with urllib.request.urlopen(rq, timeout=3) as rs:
                j = json.loads(rs.read().decode("utf-8"))
        return {int(k): v for k, v in ((j or {}).get("status") or {}).items()}
    except Exception:
        return {}


def _staff_words(db, rows):
    """{bill id: (the status in staff words, 'you' when the person has something to answer)} for rows of the bills table."""
    words = _scan_words([r["id"] for r in rows if (r["lane"] or KIND_LANE.get(r["kind"], "clinic")) == "pharmacy" and r["status"] != "rejected"])
    need = {r["dup_of"] for r in rows if r["dup_of"]} | {w.get("first") for w in words.values() if w.get("first")}
    stamps = {}
    if need:
        for r in db.execute("SELECT id, stamp_no FROM bills WHERE id IN (%s)" % ",".join(str(int(i)) for i in need)):
            stamps[r["id"]] = r["stamp_no"]
    out = {}
    for r in rows:
        lane = r["lane"] or KIND_LANE.get(r["kind"], "clinic")
        w = words.get(r["id"]) or {}
        if r["dup_of"]:
            out[r["id"]] = ("Doosri baar scan (%s)" % (stamps.get(r["dup_of"]) or ("#%d" % r["dup_of"])), "")
        elif r["status"] == "rejected":
            out[r["id"]] = ("Reject ho gaya", "")
        elif lane == "pharmacy":
            if w.get("code") == "dup":
                out[r["id"]] = ("Doosri baar scan (%s)" % (stamps.get(w.get("first")) or ("#%s" % w.get("first"))), "")
            else:
                out[r["id"]] = (w.get("word") or "Scan ho gaya", w.get("code") or "")
        elif lane == "clinic":
            out[r["id"]] = ("Approve ho gaya" if r["status"] == "approved" else "Manager ke paas", "")
        else:
            out[r["id"]] = ("File ho gaya", "")
    return out


S440_WORD_TPL = """{% if w[1]=='you' %}<a href="{{list_url}}" style="font-weight:700;color:#b3261e">{{w[0]}}</a>{% else %}{{w[0]}}{% endif %}"""


def _today_html(db):
    """Today's stamped papers (a scanning login: its own), each with its status in staff words -- under the intake and the slip."""
    day = datetime.date.today().isoformat()
    if g.user["role"] == "reception":
        rows = db.execute("SELECT * FROM bills WHERE submitted_by=? AND substr(submitted_at,1,10)=? ORDER BY id DESC LIMIT 60",
                          (g.user["display_name"], day)).fetchall()
    else:
        rows = db.execute("SELECT * FROM bills WHERE stamp_no IS NOT NULL AND substr(submitted_at,1,10)=? ORDER BY id DESC LIMIT 60", (day,)).fetchall()
    if not rows:
        return Markup("")
    return Markup(render_template_string("""<div class=card><h4>Aaj ke scan ({{rows|length}})</h4>
<table><tr><th>Stamp</th><th>Kab</th><th>Supplier</th><th>Status</th>{% if not staff %}<th>By</th>{% endif %}</tr>
{% for b in rows %}<tr><td><b>{% if staff and b['submitted_by']!=me %}{{b['stamp_no'] or '—'}}{% else %}<a href="{{url_for('bill_view',bid=b['id'])}}{{fq}}">{{b['stamp_no'] or '—'}}</a>{% endif %}</b></td>
<td>{{(b['submitted_at'] or '')[11:16]}}</td><td>{{b['vendor'] or '—'}}</td>
<td>{% set w=words[b['id']] %}""" + S440_WORD_TPL + """</td>
{% if not staff %}<td>{{b['submitted_by'] or '—'}}</td>{% endif %}</tr>{% endfor %}</table></div>""",
                                         rows=rows, words=_staff_words(db, rows), staff=(g.user["role"] == "reception"), me=g.user["display_name"],
                                         list_url=_site(S440_LIST_PATH), fq=("?from=" + _here())))


def _bills_list_staff():
    """The Purchases list of a scanning login: what it scanned itself -- its own lane, this month, 25 rows, 'aur dikhao'
    for more; each row's status in staff words; rejected rows and older drafts folded away. Read-only."""
    db = get_db()
    me = g.user["display_name"]
    this = datetime.date.today().strftime("%Y-%m")
    q = request.args.get("q", "").strip()
    lane = request.args.get("lane")
    month = request.args.get("month")
    if lane is None:
        lane = _explicit_lane(db, g.user["username"]) or ""
    if lane not in LANES:
        lane = ""
    if month is None or (month and not re.match(r"^\d{4}-\d{2}$", month)):
        month = this
    try:
        n = max(S440_PAGE, min(500, int(request.args.get("n") or S440_PAGE)))
    except ValueError:
        n = S440_PAGE
    where, params = "b.submitted_by=?", [me]
    if q:
        where += " AND (b.vendor LIKE ? OR b.bill_no LIKE ? OR b.stamp_no LIKE ?)"
        params += ["%" + q + "%"] * 3
    if lane:
        where += " AND COALESCE(b.lane,'clinic')=?"
        params.append(lane)
    allrows = db.execute("SELECT b.* FROM bills b WHERE " + where + " ORDER BY b.id DESC LIMIT 800", params).fetchall()
    # folded away, whatever the month: a rejected scan, and a draft left over from an earlier month
    old = [b for b in allrows if b["status"] == "rejected" or (b["status"] == "draft" and (b["submitted_at"] or "")[:7] < this)]
    oldids = {b["id"] for b in old}
    live = [b for b in allrows if b["id"] not in oldids and (not month or (b["submitted_at"] or "")[:7] == month)]
    rows = live[:n]
    return page("""<form method=get style="margin-bottom:10px">
<input name=q value="{{q}}" placeholder="supplier / bill no / stamp" style="max-width:210px">
<select name=lane onchange="this.form.submit()" style="width:auto;max-width:170px"><option value="">Sab lane</option>{% for k in lane_order %}<option value="{{k}}" {{'selected' if lane==k}}>{{lanes[k][0].split(' — ')[0]}}</option>{% endfor %}</select>
<select name=month onchange="this.form.submit()" style="width:auto;max-width:170px">{% for ym in months %}<option value="{{ym}}" {{'selected' if month==ym}}>{{month_label(ym)}}</option>{% endfor %}<option value="" {{'selected' if not month}}>Sab mahine</option></select>
<button class="btn small">Dhoondo</button></form>
<p><a class=btn href="{{url_for('intake')}}?from={{here|urlencode}}">📷 Scan karo</a> <span class=muted>{{'Meri lane' if lane else 'Sab lane'}} · {{month_label(month) if month else 'sab mahine'}} · {{live|length}} scan</span></p>
<table><tr><th>Stamp</th><th>Kab</th><th>Supplier</th><th>Bill no</th><th>Amount</th><th>Lane</th><th>Status</th></tr>
{% for b in rows %}<tr class=s440row><td><b><a href="{{url_for('bill_view',bid=b['id'])}}?from={{here|urlencode}}">{{b['stamp_no'] or '—'}}</a></b></td>
<td>{{(b['submitted_at'] or '')[:16]}}</td><td>{{b['vendor'] or '(padha nahi gaya)'}}</td><td>{{b['bill_no'] or '—'}}</td>
<td>{{'₹'~(b['total_amount']|inr) if b['total_amount'] is not none else '—'}}</td><td>{{lanes[b['lane'] or 'clinic'][0].split(' — ')[0]}}</td>
<td>{% set w=words[b['id']] %}""" + S440_WORD_TPL + """</td></tr>{% endfor %}</table>
{% if not rows %}<p class=muted>Is mahine is lane mein aapka koi scan nahi.</p>{% endif %}
{% if live|length > rows|length %}<p><a class="btn small" href="{{url_for('bills_list')}}?lane={{lane}}&month={{month}}&q={{q|urlencode}}&n={{n+25}}">aur dikhao ({{live|length - rows|length}} aur)</a></p>{% endif %}
{% if old %}<details class=card style="margin-top:12px"><summary style="cursor:pointer;color:#3a5a78;font-weight:600">purane drafts ({{old|length}}) ▾</summary>
<table style="margin-top:8px"><tr><th>Stamp</th><th>Kab</th><th>Supplier</th><th>Status</th></tr>
{% for b in old %}<tr><td>{{b['stamp_no'] or '—'}}</td><td>{{(b['submitted_at'] or '')[:16]}}</td><td>{{b['vendor'] or '—'}}</td><td>{% set w=words[b['id']] %}{{w[0]}}</td></tr>{% endfor %}</table></details>{% endif %}""",
                rows=rows, live=live, old=old, words=_staff_words(db, rows + old), q=q, lane=lane, month=month, n=n, lanes=LANES, lane_order=LANE_ORDER,
                months=_month_choices(), month_label=_month_label, list_url=_site(S440_LIST_PATH), here=_here(full=True),
                flow=_flow("Meri scan list"))


def _bill_view_staff(b, items):
    """A bill as a scanning login sees it: what was read, the scan, its status in staff words. No action."""
    db = get_db()
    return page("""<div class=card><div style="font-size:22px;font-weight:800;color:#1f3864">{{b['stamp_no'] or ('#'~b['id'])}}</div>
<p style="margin:6px 0"><b>{% set w=word %}""" + S440_WORD_TPL + """</b></p>
<b>Supplier:</b> {{b['vendor'] or '—'}}<br><b>Bill no:</b> {{b['bill_no'] or '—'}}<br><b>Date:</b> {{b['bill_date'] or '—'}}<br>
<b>Amount:</b> {{'₹'~(b['total_amount']|inr) if b['total_amount'] is not none else '—'}}<br>
<b>Lane:</b> {{lanes[b['lane'] or 'clinic'][0]}}<br>
<span class=muted>{{b['submitted_by'] or '—'}} · {{b['submitted_at'] or ''}}</span>
{% if b['source_stored'] %}<p><a class=btn href="{{url_for('bill_file',bid=b['id'])}}" target=_blank>📄 Scan dekho</a></p>{% endif %}</div>
{% if items %}<div class=card><h4>Items ({{items|length}})</h4><table><tr><th>Item</th><th>Qty</th><th>Amount</th></tr>
{% for it in items %}<tr><td>{{it['item_name']}}</td><td>{{it['quantity'] if it['quantity'] is not none else '—'}}</td>
<td>{{'₹%.2f'|format(it['amount']) if it['amount'] is not none else '—'}}</td></tr>{% endfor %}</table></div>{% endif %}""",
                b=b, items=items, lanes=LANES, word=_staff_words(db, [b])[b["id"]], list_url=_site(S440_LIST_PATH),
                flow=_flow("Bill " + (b["stamp_no"] or ("#%d" % b["id"])), url_for("bills_list")))


@app.route("/bills/<int:bid>/thumb")
@scan_reader
def bill_thumb(bid):
    """A small picture of the scan's first page (pdftoppm for a PDF, ImageMagick for a photo -- the S409 fingerprint's tools)."""
    b = get_db().execute("SELECT id, kind, lane, status, submitted_by, source_stored FROM bills WHERE id=?", (bid,)).fetchone()
    if not b or not b["source_stored"]:
        abort(404)
    if not _staff_may_see(b, image=True):
        abort(403)
    path = os.path.join(UPLOAD_DIR, b["source_stored"])
    if not os.path.exists(path):
        abort(404)
    try:
        if b["source_stored"].rsplit(".", 1)[-1].lower() == "pdf":
            p = subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-png", "-scale-to", "260", path],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=25)
        else:
            p = subprocess.run(["convert", path + "[0]", "-auto-orient", "-thumbnail", "260x260", "png:-"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=25)
        raw = p.stdout
    except Exception:
        raw = b""
    if not raw or raw[:4] != b"\x89PNG":
        abort(404)
    resp = app.response_class(raw, mimetype="image/png")
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


