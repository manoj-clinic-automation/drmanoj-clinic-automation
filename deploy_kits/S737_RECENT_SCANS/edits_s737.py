# -*- coding: utf-8 -*-
"""edits_s737.py -- S737_RECENT_SCANS: the counted edits on /root/assetapp/asset_register.py (FROM 5f44f65e, S731's TO = live).

D845 item 2, built on the owner's FINAL (20:24 IST 06-Nov-2026) of the mock-up https://claude.ai/artifact/KfzGHJFyPdnMsgqEmC8EdD
(unchanged by him -- the mock-up is the specification):
  * the scan app's home page (the owner and Shavez): three counts (on the desk · scanned today · read failed) and the card
    "Recent scans" -- newest scan first, grouped by the IST day it was scanned whatever date is printed on the paper; 7 / 14 / 30
    days (14 first); All · Needs someone · Clinic · NK · Dr MK · Pharmacy; each row: time · stamp · supplier · kind · lane ·
    where it sits now · Open (the paper's own door, s559_href);
  * All papers: newest scan first, with a Scanned column and a Where it sits column; "Bill date" (today's order) one tap away.
Installed SWITCHED OFF: settings `recent.on` (absent = off), the owner's switch on /admin. Off = both pages exactly as before.
The scan time is created_at (SQLite UTC) + 330 minutes, the rule clinic_papers.MONTH_OF already uses. Shavez never sees a
Personal paper (All papers' own rule). Read only: no table, no column, no write except the switch.

Each edit is (name, (old, new)): `old` must occur EXACTLY ONCE in the FROM bytes, or make_s737.py refuses and writes nothing.
"""

KIT = "S737_RECENT_SCANS"

HELPERS = r'''RECENT_S737 = "S737"          # S737_RECENT_SCANS (D845 item 2): recent scans by scan date -- the owner's mock-up, 'final' 06-Nov
S737_NOW = None               # a walk sets a made-up 'now' (UTC, SQLite form) here; None = the clock
S737_RANGES = (7, 14, 30)
S737_FILTERS = (("all", "All"), ("need", "Needs someone"), ("clinic", "Clinic"), ("lab_purchase", "NK"), ("owner_expense", "Dr MK"),
                ("pharmacy", "Pharmacy"))
S737_LANE = {"clinic": "Clinic", "pharmacy": "Pharmacy", "lab_purchase": "NK", "owner_expense": "Dr MK", "other_doc": "Other document"}
S737_TONE = {"desk": "background:#fdf0d5;color:#7a4a00", "ok": "background:#e3f1e6;color:#1e5b2c", "page": "background:#e4ecf7;color:#1d4f86",
             "bad": "background:#fbe4e1;color:#8a2116", "off": "background:#eceef1;color:#3e4a57"}
S737_ON_BTN = ("display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:8px;border:1px solid #20364f;"
               "background:#20364f;color:#ffffff;font-size:14px;text-decoration:none;box-sizing:border-box")
S737_OFF_BTN = ("display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:8px;border:1px solid #c3cbd5;"
                "background:#ffffff;color:#1f2933;font-size:14px;text-decoration:none;box-sizing:border-box")


def _s737_on():
    """S737: the owner's switch on /admin (settings recent.on), installed OFF."""
    try:
        return (setting_or("recent.on", "off") or "").strip().lower() == "on"
    except Exception:                                             # noqa: BLE001
        return False


def _s737_lane(b):
    ln = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
    if ln == "owner_expense":
        try:
            return (b["pe_who"] or "").strip() or "Dr MK"
        except (IndexError, KeyError):
            return "Dr MK"
    return S737_LANE.get(ln, ln or "Clinic")


def _s737_scan(b):
    """The scan's IST time as dd-mm-yyyy HH:MM (created_at is SQLite UTC; +330 minutes, clinic_papers.MONTH_OF's rule)."""
    try:
        s = b["s737_ist"] or ""
    except (IndexError, KeyError):
        s = ""
    return ("%s-%s-%s %s" % (s[8:10], s[5:7], s[:4], s[11:16])) if len(s) >= 16 else "\u2014"


def _s737_wait(db, owner):
    """The ids on the desk's own list (sorting_desk.waiting: (paper, why) pairs), built once per request."""
    try:
        c = g.get("_s737_wait")
        if c is not None and c[0] == owner:
            return c[1]
    except Exception:                                             # noqa: BLE001
        c = None
    sd = _s559_desk_mod()
    try:
        wait = {(x[0] if isinstance(x, tuple) else x)["id"] for x in sd.waiting(db, owner)} if sd is not None else set()
    except Exception as _ex:                                      # noqa: BLE001
        print("S737 desk list: %s" % _ex, file=_sys.stderr)
        wait = set()
    try:
        g._s737_wait = (owner, wait)
    except Exception:                                             # noqa: BLE001
        pass
    return wait


def _s737_where_fn(db, owner):
    """One request's 'where it sits': (words, tone) for a paper. The desk's own list (sorting_desk.waiting) once per request."""
    sd = _s559_desk_mod()
    wait = _s737_wait(db, owner)
    names = dict(getattr(sd, "DEST_NAME", {}) or {})
    names["patient_paper"] = "Surgical case pack"
    stm = _sys.modules.get("stationery")
    try:
        keys = set(stm.suppliers(db)) if stm is not None else set()      # read once per page, not once per row
    except Exception:                                             # noqa: BLE001
        keys = set()

    def listed(b):
        try:
            return bool(keys) and bool(b["vendor"]) and stm._skey(b["vendor"]) in keys
        except Exception:                                         # noqa: BLE001
            return False

    def where(b):
        st = b["status"] or ""
        ln = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
        sg = b["subgroup"] or ""
        unread = (b["ocr_status"] or "") in ("failed", "empty") and not (b["vendor"] or "").strip()
        if b["id"] in wait:                                       # the desk's own list first: it names what needs a person
            return ("Read failed \u2014 scan again", "bad") if unread else ("On the desk \u2014 waiting", "desk")
        if b["dup_of"]:
            return "Second scan", "off"
        if st == "rejected":
            return "Set aside", "off"
        if unread:
            return "Read failed \u2014 scan again", "bad"
        if ln == "pharmacy":
            return ("Filed (pharmacy)", "ok") if st in ("captured", "approved") else ("Pharmacy \u2014 not filed yet", "desk")
        if listed(b):
            return "Stationery page", "page"
        if sg:
            return names.get(sg, sg.replace("_", " ").capitalize()), ("ok" if st in ("approved", "captured") else "page")
        if st == "approved":
            return "Accepted", "ok"
        if st == "captured":
            return "Filed", "ok"
        return "Not accepted yet", "desk"
    return where


def _s737_esc(s):
    from markupsafe import escape as _e
    return _e(s)


def _s737_pill(w):
    return Markup('<span style="%s;padding:3px 8px;border-radius:999px;font-size:13px;white-space:nowrap">%s</span>'
                  % (S737_TONE.get(w[1], S737_TONE["off"]), _s737_esc(w[0])))


def _s737_recent(db, owner, days, filt):
    """The last <days> IST days of scans, newest first, grouped by IST scan day; the counts for the three tiles."""
    ref = S737_NOW or "now"
    have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    po = " AND b.page_of IS NULL" if "page_of" in have else ""
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    today = db.execute("SELECT date(?,'+330 minutes')", (ref,)).fetchone()[0]
    yday = db.execute("SELECT date(?,'+330 minutes','-1 day')", (ref,)).fetchone()[0]
    rows = db.execute("SELECT b.*, datetime(b.created_at,'+330 minutes') AS s737_ist FROM bills b "
                      "WHERE date(b.created_at,'+330 minutes') >= date(?,'+330 minutes',?) AND date(b.created_at,'+330 minutes') <= ?"
                      + po + pers + " ORDER BY b.created_at DESC, b.id DESC LIMIT 3000", (ref, "-%d days" % (days - 1), today)).fetchall()
    where = _s737_where_fn(db, owner)
    out, groups, today_n, bad_n = [], {}, 0, 0
    for b in rows:
        w = where(b)
        day = (b["s737_ist"] or "")[:10]
        if day == today:
            today_n += 1
        if w[1] == "bad":
            bad_n += 1
        ln = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
        if filt == "need" and w[1] not in ("desk", "bad"):
            continue
        if filt not in ("all", "need") and ln != filt:
            continue
        if day not in groups:
            try:
                d = datetime.date(int(day[:4]), int(day[5:7]), int(day[8:10]))
                lab = d.strftime("%a %d-%b")
            except ValueError:
                lab = day or "\u2014"
            if day == today:
                lab = "Today \u00b7 " + lab
            elif day == yday:
                lab = "Yesterday \u00b7 " + lab
            groups[day] = {"label": lab, "rows": []}
            out.append(groups[day])
        unread = w[1] == "bad"
        groups[day]["rows"].append({"time": (b["s737_ist"] or "")[11:16], "stamp": b["stamp_no"] or ("#%d" % b["id"]),
                                    "supplier": (b["vendor"] or "").strip() or "(not read)",
                                    "kind": "\u2014" if unread else ("Document" if (ln == "other_doc" and not b["doc_kind"]) else (b["doc_kind"] or "bill").replace("_", " ").capitalize()),
                                    "lane": _s737_lane(b), "where": w[0], "wstyle": S737_TONE.get(w[1], S737_TONE["off"]),
                                    "href": _s559_paper_href(b)})
    for g_ in out:
        n = len(g_["rows"])
        g_["count"] = "%d scan%s" % (n, "" if n == 1 else "s")
    return {"days": out, "today_n": today_n, "bad_n": bad_n}


_S737_HOME_TPL = """<div id=s737home style="display:flex;flex-direction:column;gap:14px;margin:0 0 16px">
<div style="display:flex;flex-wrap:wrap;gap:12px">
{% if desk is not none %}<a href="{{url_for('s551_desk')}}" class=card style="flex:1 1 220px;margin:0;text-decoration:none;color:inherit"><div class=muted>On the desk</div><b style="font-size:24px">{{desk}} waiting</b></a>{% endif %}
<div class=card style="flex:1 1 220px;margin:0"><div class=muted>Scanned today</div><b style="font-size:24px">{{r.today_n}} paper{{'' if r.today_n == 1 else 's'}}</b></div>
<div class=card style="flex:1 1 220px;margin:0"><div class=muted>Read failed — scan again</div><b style="font-size:24px">{{r.bad_n}} paper{{'' if r.bad_n == 1 else 's'}}</b></div>
</div>
<div class=card id=s737recent style="margin:0">
<div style="display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;justify-content:space-between">
<div><h3 style="margin:0">Recent scans</h3><div class=muted>Newest scan first, by the day it was scanned — whatever date is printed on the paper.</div></div>
<div style="display:flex;gap:6px" role=group aria-label="How many days">{% for n in ranges %}<a href="{{n.href}}" style="{{n.style}}">{{n.label}}</a>{% endfor %}</div>
</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px" role=group aria-label="Show">{% for f in filters %}<a href="{{f.href}}" style="{{f.style}}">{{f.label}}</a>{% endfor %}</div>
{% for d in r.days %}<div style="margin-top:12px"><div style="display:flex;justify-content:space-between;align-items:baseline;padding:8px 2px;border-bottom:2px solid #20364f"><b>{{d.label}}</b><span class=muted>{{d.count}}</span></div>
<div style="overflow-x:auto"><div style="min-width:760px">{% for p in d.rows %}<a href="{{p.href}}" class=s737row style="display:grid;grid-template-columns:64px 84px minmax(0,2fr) 96px 110px minmax(0,1.6fr) 56px;gap:10px;align-items:center;padding:10px 2px;border-bottom:1px solid #e6e9ee;text-decoration:none;color:inherit;min-height:44px;box-sizing:border-box"><span class=muted>{{p.time}}</span><b>{{p.stamp}}</b><span>{{p.supplier}}</span><span>{{p.kind}}</span><span>{{p.lane}}</span><span><span style="{{p.wstyle}};padding:3px 8px;border-radius:999px;font-size:13px">{{p.where}}</span></span><span style="color:#1d4f86;text-align:right">Open</span></a>{% endfor %}</div></div></div>{% endfor %}
{% if not r.days %}<p class=muted>No scans of this kind in these days.</p>{% endif %}
<p class=muted style="margin:10px 0 0">Columns: time scanned · stamp · supplier · kind · lane · where it sits now. Older scans: <a href="{{url_for('bills_list')}}">All papers</a>.</p>
</div></div>"""


def _s737_home(u):
    """S737: the home page's Recent scans for the owner and Shavez; '' when the switch is off or the login is another's."""
    try:
        role = _s559_role(u)
        if not _s737_on() or role not in ("owner", "manager"):
            return Markup("")
        db = get_db()
        try:
            days = int(request.args.get("rs", "14"))
        except (TypeError, ValueError):
            days = 14
        days = days if days in S737_RANGES else 14
        filt = request.args.get("rf", "all")
        filt = filt if filt in dict(S737_FILTERS) else "all"
        r = _s737_recent(db, role == "owner", days, filt)
        ranges = [{"label": "%d days" % n, "style": S737_ON_BTN if n == days else S737_OFF_BTN,
                   "href": url_for("dashboard", rs=n, rf=(filt if filt != "all" else None)) + "#s737recent"} for n in S737_RANGES]
        filters = [{"label": l, "style": S737_ON_BTN if k == filt else S737_OFF_BTN,
                    "href": url_for("dashboard", rs=(days if days != 14 else None), rf=(k if k != "all" else None)) + "#s737recent"}
                   for k, l in S737_FILTERS]
        return Markup(render_template_string(_S737_HOME_TPL, r=r, ranges=ranges, filters=filters, desk=(len(_s737_wait(db, role == "owner")) if _s559_desk_open(u) else None)))
    except Exception as _ex:                                      # noqa: BLE001
        print("S737 home card: %s" % _ex, file=_sys.stderr)
        return Markup("")


'''

E_HELPERS = ('FP_GRID = (17, 16)', HELPERS + 'FP_GRID = (17, 16)')

E_DASH = ('return page("""{{s559home}}<h2>Dashboard</h2>', 'return page("""{{s559home}}{{s737home}}<h2>Dashboard</h2>')
E_DASHKW = ('due=due, counts=counts, month_spend=month_spend, s559home=_s559_home(g.user))',
            'due=due, counts=counts, month_spend=month_spend, s559home=_s559_home(g.user), s737home=_s737_home(g.user))')

E_SEL = ('"SELECT b.*, u.display_name entered_by, "\n        "(SELECT COUNT(*) FROM bill_items bi WHERE bi.bill_id=b.id) nitems "',
         '"SELECT b.*, u.display_name entered_by, datetime(b.created_at,\'+330 minutes\') s737_ist, "      # S737\n'
         '        "(SELECT COUNT(*) FROM bill_items bi WHERE bi.bill_id=b.id) nitems "')
E_ORDER = ('"WHERE " + where + " ORDER BY (b.status=\'draft\') DESC, b.bill_date DESC, b.id DESC LIMIT 300",',
           '"WHERE " + where + (" ORDER BY b.created_at DESC, b.id DESC LIMIT 300" if _s737_by_scan else      # S737: newest scan first\n'
           '        " ORDER BY (b.status=\'draft\') DESC, b.bill_date DESC, b.id DESC LIMIT 300"),')
E_PRE = ('    npend = db.execute("SELECT COUNT(*) FROM bills WHERE status=\'draft\'").fetchone()[0]\n    bills = db.execute(',
         '    npend = db.execute("SELECT COUNT(*) FROM bills WHERE status=\'draft\'").fetchone()[0]\n'
         '    _s737_cols = _s737_on()                                       # S737: the switch; off = the page as before\n'
         '    _s737_by_scan = _s737_cols and request.args.get("order", "") != "bill"\n'
         '    bills = db.execute(')
E_FORM = ('<button class="btn small">Search</button>{% if q or fk or fs %} <a class="btn small" href="{{url_for(\'bills_list\')}}">clear</a>{% endif %}</form>',
          '{% if s737 and not s737_scan %}<input type=hidden name=order value=bill>{% endif %}'
          '<button class="btn small">Search</button>{% if q or fk or fs %} <a class="btn small" href="{{url_for(\'bills_list\')}}">clear</a>{% endif %}</form>'
          '{% if s737 %}<div id=s737order style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:-2px 0 10px"><span class=muted>Order</span>'
          '<a href="{{url_for(\'bills_list\', q=q or None, kind=fk or None, status=fs or None)}}" style="{{s737_btn(s737_scan)}}">Newest scan first</a>'
          '<a href="{{url_for(\'bills_list\', q=q or None, kind=fk or None, status=fs or None, order=\'bill\')}}" style="{{s737_btn(not s737_scan)}}">Bill date</a>'
          '<span class=muted style="flex-basis:100%">{% if s737_scan %}Newest scan first (the new default). A wrong printed year or a paper with no date stays where it was scanned.'
          '{% else %}By the date printed on the bill — today’s order. A mistyped year jumps to the top and a paper with no date drops to the bottom.{% endif %}</span></div>{% endif %}')
E_TH = ('<table><tr><th>Stamp</th><th>Status</th><th>Date</th><th>Vendor</th><th>Bill no</th><th>Kind</th><th>Lane</th><th>Items</th><th>Total</th></tr>',
        '<table><tr>{% if s737 %}<th>Scanned</th>{% endif %}<th>Stamp</th><th>Status</th><th>{{\'Bill date\' if s737 else \'Date\'}}</th><th>Vendor</th><th>Bill no</th><th>Kind</th><th>Lane</th>{% if s737 %}<th>Where it sits</th>{% endif %}<th>Items</th><th>Total</th></tr>')
E_ROW = ('"><td>{{b[\'stamp_no\'] or \'\\u2014\'}}{% if b[\'dup_of\'] %}',
         '">{% if s737 %}<td style="white-space:nowrap">{{s737_scanned(b)}}</td>{% endif %}<td>{{b[\'stamp_no\'] or \'\\u2014\'}}{% if b[\'dup_of\'] %}')
E_CELL = ('{% else %}<a href="{{s559_href(b)}}" title="open the paper">{{lane_word(b)}}</a>{% endif %}</td>\n<td>{{b[\'nitems\']}}</td>',
          '{% else %}<a href="{{s559_href(b)}}" title="open the paper">{{lane_word(b)}}</a>{% endif %}</td>\n'
          '{% if s737 %}<td>{{s737_where(b)}}</td>{% endif %}<td>{{b[\'nitems\']}}</td>')
E_KW = ('bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES,',
        'bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES, s737=_s737_cols, s737_scan=_s737_by_scan, s737_scanned=_s737_scan,      # S737\n'
        '        s737_btn=(lambda on: S737_ON_BTN if on else S737_OFF_BTN), s737_where=_s737_where_pill(db) if _s737_cols else None,')
E_PILL = ('def _s737_recent(db, owner, days, filt):',
          'def _s737_where_pill(db):\n'
          '    """All papers\' Where it sits cell: one desk read per page."""\n'
          '    fn = _s737_where_fn(db, is_owner())\n'
          '    return lambda b: _s737_pill(fn(b))\n'
          '\n'
          '\n'
          'def _s737_recent(db, owner, days, filt):')
E_ACT = ('        elif act == "set_scan_lanes5":',
         '        elif act == "set_recent_s737":                                                 # S737 (D845 item 2)\n'
         '            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(\'recent.on\',?)",\n'
         '                       ("on" if request.form.get("on") == "1" else "off",))\n'
         '            flash("Recent scans by scan date is now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))\n'
         '        elif act == "set_scan_lanes5":')
E_CARD = ("<div class=card><h4>Bill intake \\u2014 reception's lane buttons</h4>",
          '<div class=card id=s737switch><h4>Recent scans by scan date</h4>\n'
          '<p class=muted>When ON, your home page and Shavez\\u2019s show <b>Recent scans</b> \\u2014 newest scan first, by the day it was scanned \\u2014 '
          'and All papers lists the newest scan first with a <b>Scanned</b> and a <b>Where it sits</b> column (Bill date order one tap away). '
          'Shavez never sees a Personal paper. When OFF, both pages are as before.</p>\n'
          '<p>Now: <b>{{\'ON\' if recent737 else \'OFF\'}}</b></p>\n'
          '<form method=post><input type=hidden name=action value=set_recent_s737><input type=hidden name=on value="{{\'0\' if recent737 else \'1\'}}">\n'
          '<button class="btn small">{{\'Switch OFF\' if recent737 else \'Switch ON\'}}</button></form></div>\n'
          "<div class=card><h4>Bill intake \\u2014 reception's lane buttons</h4>")
E_ADMKW = ('lanes5=_lanes5_on(),', 'lanes5=_lanes5_on(), recent737=_s737_on(),')

EDITS = [("helpers", E_HELPERS), ("where_pill", E_PILL), ("dashboard", E_DASH), ("dashboard_kw", E_DASHKW), ("list_pre", E_PRE),
         ("list_select", E_SEL), ("list_order", E_ORDER), ("list_form", E_FORM), ("list_head", E_TH), ("list_row", E_ROW),
         ("list_cell", E_CELL), ("list_kw", E_KW), ("admin_action", E_ACT), ("admin_card", E_CARD), ("admin_kw", E_ADMKW)]
