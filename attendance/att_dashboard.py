"""
att_dashboard.py  —  live, password-protected, mobile-friendly attendance page.

Read-only: it only reads punches.csv + staff_master.csv.  Uses each person's own
weekday/Sunday shift to judge late and early.  Runs as the systemd service
'attendance-dashboard'.

Access:  https://attendance.dr-manoj.in   (also http://93.127.195.49:8042 fallback)

AUTH (Session 59): cookie-based session login so an iPhone Home-Screen icon stays
logged in.  A signed cookie is set after /login.  HTTP Basic Auth is still accepted
as a fallback (old IP URL / saved-password bookmarks keep working). Same username &
password from att_config.py.
"""
import datetime
import hmac
import hashlib
import base64
from flask import Flask, request, Response, redirect
import att_config as cfg
import att_core as core

app = Flask(__name__)

# ---- session cookie (signed, no external library) -------------------------
COOKIE_NAME = "att_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _sign(msg):
    key = cfg.SECRET_KEY.encode() if isinstance(cfg.SECRET_KEY, str) else cfg.SECRET_KEY
    return hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()


def make_token():
    # payload = username ; token = payload.signature(payload)
    payload = cfg.DASHBOARD_USER
    return payload + "." + _sign(payload)


def token_valid(token):
    if not token or "." not in token:
        return False
    payload, sig = token.rsplit(".", 1)
    if payload != cfg.DASHBOARD_USER:
        return False
    return hmac.compare_digest(sig, _sign(payload))


def basic_ok():
    a = request.authorization
    return bool(a and a.username == cfg.DASHBOARD_USER
                and a.password == cfg.DASHBOARD_PASSWORD)


def authed():
    # accept EITHER a valid session cookie OR HTTP Basic Auth (fallback)
    if token_valid(request.cookies.get(COOKIE_NAME)):
        return True
    return basic_ok()


LOGIN_CSS = """
* { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { margin:0; font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;
       background:#f3f5f7; color:#1d2733; font-size:16px; }
.wrap { max-width:400px; margin:0 auto; padding:40px 18px; }
.card { background:#fff; border-radius:16px; padding:26px 22px; box-shadow:0 2px 10px rgba(0,0,0,.07); }
h1 { margin:0 0 4px; font-size:20px; color:#1f4e79; }
.sub { color:#6b7785; font-size:14px; margin:0 0 22px; }
label { display:block; font-size:13px; color:#6b7785; margin:14px 0 5px; font-weight:600; }
input { width:100%; padding:13px; font-size:16px; border:1px solid #cfd6dd; border-radius:10px; background:#fff; color:#1d2733; }
button { width:100%; margin-top:22px; padding:14px; font-size:16px; font-weight:700; color:#fff;
         background:#1f4e79; border:none; border-radius:10px; cursor:pointer; }
.err { background:#ffe0e0; color:#c0392b; font-size:14px; padding:10px 12px; border-radius:9px; margin:14px 0 0; }
.foot { text-align:center; color:#9aa4af; font-size:12px; margin-top:22px; }
"""


def login_page(error=""):
    err_html = f'<div class="err">{error}</div>' if error else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance Login</title><style>{LOGIN_CSS}</style></head>
<body><div class="wrap"><div class="card">
<h1>Clinic Attendance</h1>
<p class="sub">Please sign in to continue</p>
<form method="post" action="/login">
<label>Username</label>
<input name="username" autocomplete="username" autocapitalize="none" autocorrect="off" required>
<label>Password</label>
<input name="password" type="password" autocomplete="current-password" required>
<button type="submit">Sign in</button>
{err_html}
</form>
<div class="foot">Dr. Manoj Agarwal Clinic</div>
</div></div></body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if authed():
            return redirect("/")
        return login_page()
    # POST
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if u == cfg.DASHBOARD_USER and p == cfg.DASHBOARD_PASSWORD:
        resp = redirect("/")
        resp.set_cookie(COOKIE_NAME, make_token(), max_age=COOKIE_MAX_AGE,
                        secure=True, httponly=True, samesite="Lax")
        return resp
    return login_page("Wrong username or password. Please try again.")


@app.route("/logout")
def logout():
    resp = redirect("/login")
    resp.delete_cookie(COOKIE_NAME)
    return resp


CSS = """
* { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { margin:0; font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;
       background:#f3f5f7; color:#1d2733; font-size:16px; }
.wrap { max-width:640px; margin:0 auto; padding:14px; }
.top { background:#1f4e79; color:#fff; border-radius:14px; padding:16px 18px; }
.top h1 { margin:0 0 2px; font-size:18px; font-weight:700; }
.top .date { font-size:14px; opacity:.85; }
.top .sun { display:inline-block; margin-top:6px; font-size:12px; background:rgba(255,255,255,.18);
            padding:3px 9px; border-radius:20px; }
.nav { display:flex; justify-content:space-between; align-items:center; margin-top:10px; font-size:14px; }
.nav a { color:#fff; text-decoration:none; background:rgba(255,255,255,.16); padding:6px 12px; border-radius:8px; }
.cards { display:flex; gap:10px; margin:14px 0; }
.card { flex:1; background:#fff; border-radius:12px; padding:12px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,.06); }
.card .num { font-size:26px; font-weight:800; line-height:1; }
.card .lbl { font-size:11px; color:#6b7785; margin-top:4px; text-transform:uppercase; letter-spacing:.4px; }
.g .num{color:#1a8a4a;} .r .num{color:#c0392b;} .a .num{color:#c77f00;}
h2 { font-size:14px; color:#6b7785; text-transform:uppercase; letter-spacing:.5px; margin:18px 4px 8px; }
.row { background:#fff; border-radius:12px; padding:12px 14px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,.05);
       display:flex; align-items:center; gap:10px; }
.row .nm { font-weight:600; }
.row .role { font-size:12px; color:#8893a0; }
.row .meta { margin-left:auto; text-align:right; font-size:13px; color:#445; white-space:nowrap; }
.row .meta b { font-size:15px; }
.badge { display:inline-block; font-size:11px; font-weight:700; padding:2px 7px; border-radius:20px; vertical-align:middle; margin-left:4px; }
.late { background:#ffe0c2; color:#9a4b00; }
.early{ background:#ffeab0; color:#8a6400; }
.inq  { background:#d8f0df; color:#1a7a40; }
.out  { background:#eceff2; color:#67727e; }
.absent .nm { color:#c0392b; }
.sunday .absent .nm { color:#67727e; }
.foot { text-align:center; color:#9aa4af; font-size:12px; margin:18px 0 6px; }
.foot a { color:#9aa4af; }
.empty { color:#8893a0; padding:8px 4px; font-size:14px; }
"""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hm(dt):
    return dt.strftime("%H:%M")


def render(data, d, is_today):
    is_sun = data["is_sunday"]
    prev = (d - datetime.timedelta(days=1)).isoformat()
    nxt = (d + datetime.timedelta(days=1)).isoformat()
    refresh = '<meta http-equiv="refresh" content="60">' if is_today else ""
    title = "Today" if is_today else d.strftime("%A")
    sun_tag = '<div class="sun">Sunday &middot; reduced hours</div>' if is_sun else ""
    absent_label = ("Off / not in" if is_sun else ("Not punched yet" if is_today else "Absent"))

    present_rows = ""
    for r in data["present"]:
        badge = ""
        if r["late"]:
            badge += f' <span class="badge late">LATE {r["late_min"]}m</span>'
        if r["early"]:
            badge += ' <span class="badge early">left early</span>'
        if is_today:
            badge += (' <span class="badge inq">in</span>' if r["likely_in"]
                      else ' <span class="badge out">out</span>')
        if r["hours"] is not None:
            meta = (f'<div class="meta"><b>{hm(r["first"])} \u2013 {hm(r["last"])}</b>'
                    f'<br>{r["hours"]} hrs &middot; {r["n"]} punches</div>')
        else:
            meta = f'<div class="meta"><b>{hm(r["first"])}</b><br>single punch</div>'
        present_rows += (f'<div class="row"><div><div class="nm">{esc(r["name"])}{badge}</div>'
                         f'<div class="role">{esc(r["department"])}</div></div>{meta}</div>')
    if not present_rows:
        present_rows = '<div class="empty">No one has punched yet.</div>'

    absent_rows = ""
    for r in data["absent"]:
        absent_rows += (f'<div class="row absent"><div><div class="nm">{esc(r["name"])}</div>'
                        f'<div class="role">{esc(r["department"])}</div></div></div>')
    if not absent_rows:
        absent_rows = '<div class="empty">Everyone is accounted for.</div>'

    body_class = "sunday" if is_sun else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{refresh}
<title>Clinic Attendance</title><style>{CSS}</style></head>
<body class="{body_class}"><div class="wrap">
<div class="top"><h1>Clinic Attendance</h1>
<div class="date">{title} &middot; {d.strftime("%d %b %Y")}</div>{sun_tag}
<div class="nav"><a href="/?date={prev}">&larr; Prev</a>
<a href="/">Today</a><a href="/month">Month &#128197;</a><a href="/?date={nxt}">Next &rarr;</a></div></div>
<div class="cards">
<div class="card g"><div class="num">{data['present_count']}</div><div class="lbl">Present</div></div>
<div class="card r"><div class="num">{data['absent_count']}</div><div class="lbl">{esc(absent_label)}</div></div>
<div class="card a"><div class="num">{data['late_count']}</div><div class="lbl">Late</div></div>
</div>
<h2>Present ({data['present_count']})</h2>{present_rows}
<h2>{esc(absent_label)} ({data['absent_count']})</h2>{absent_rows}
<div class="foot">Auto-refreshes every minute &middot; Dr. Manoj Agarwal Clinic &middot; <a href="/logout">Sign out</a></div>
</div></body></html>"""


@app.route("/")
def home():
    if not authed():
        return redirect("/login")
    qd = request.args.get("date")
    today = datetime.date.today()
    try:
        d = datetime.datetime.strptime(qd, "%Y-%m-%d").date() if qd else today
    except ValueError:
        d = today
    data = core.compute_day(d)
    return render(data, d, is_today=(d == today))


MONTH_CSS = """
* { box-sizing:border-box; }
body { margin:0; font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif; color:#1d2733; background:#fff; }
.bar { background:#1f4e79; color:#fff; padding:10px 14px; display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.bar h1 { font-size:16px; margin:0; font-weight:700; }
.bar a, .bar button { color:#fff; background:rgba(255,255,255,.16); border:none; text-decoration:none;
        padding:6px 12px; border-radius:8px; font-size:14px; cursor:pointer; }
.note { padding:8px 14px; font-size:12px; color:#6b7785; }
.tablewrap { padding:0 8px 16px; overflow-x:auto; }
table { border-collapse:collapse; width:100%; table-layout:fixed; }
th, td { border:1px solid #d4d9de; text-align:center; padding:1px 0; font-size:9px; overflow:hidden; }
th { background:#1f4e79; color:#fff; }
th.nm, td.nm { width:62px; text-align:left; padding-left:4px; font-size:9px; white-space:nowrap; }
td.nm { font-weight:600; }
th.tot, td.tot { width:24px; background:#eef2f7; font-weight:700; }
td.abs2 { color:#c0392b; }
.wd { font-size:7px; opacity:.75; }
.sun { background:#e9eef4; }
td.sun { background:#f3f6fa; }
td.abs { color:#c9d0d8; }
td.late { background:#ffe6cf; }
td.fut { background:#fff; border-color:#eceff2; }
.out { color:#8893a0; font-size:8px; }
.mobile-only { display:none; }
.mwrap { padding:10px 12px 24px; }
.mtoggle { display:flex; gap:8px; margin-bottom:12px; }
.mtoggle button { flex:1; padding:10px; border:1px solid #cfd6dd; background:#fff; border-radius:9px; font-size:15px; font-weight:600; color:#445; }
.mtoggle button.on { background:#1f4e79; color:#fff; border-color:#1f4e79; }
.msel { width:100%; padding:11px; font-size:16px; border:1px solid #cfd6dd; border-radius:9px; margin-bottom:12px; background:#fff; color:#1d2733; }
.msum { font-size:13px; color:#6b7785; margin:0 2px 10px; font-weight:600; }
.mcard { background:#fff; border:1px solid #e6e9ec; border-radius:10px; padding:10px 12px; margin-bottom:7px; display:flex; align-items:center; gap:10px; box-shadow:0 1px 2px rgba(0,0,0,.04); }
.mcard .dt { width:66px; font-size:13px; color:#445; font-weight:600; }
.mcard .tm { font-weight:700; font-size:15px; }
.mcard .tm small { font-weight:500; color:#8893a0; font-size:12px; margin-left:6px; }
.mcard .none { color:#c0392b; font-size:14px; }
.mcard.sn { background:#f3f6fa; }
.mcard.sn .none { color:#8893a0; }
.mbadge { margin-left:auto; font-size:11px; font-weight:700; padding:2px 9px; border-radius:20px; }
.b-late { background:#ffe0c2; color:#9a4b00; }
@media (max-width:760px){ .desktop-only{display:none;} .mobile-only{display:block;} .note{display:none;} .bar h1{font-size:15px;} }
@media print {
  .bar a, .bar button { display:none; }
  .bar { background:#1f4e79 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  th { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .note { display:none; }
  .mobile-only { display:none !important; }
  .desktop-only { display:block !important; }
  @page { size:A4 landscape; margin:8mm; }
  body { font-size:8px; }
  th, td { font-size:8px; }
}
"""


@app.route("/month")
def month_view():
    if not authed():
        return redirect("/login")
    import calendar as _cal
    today = datetime.date.today()
    ym = request.args.get("ym")
    try:
        y, m = (int(ym[:4]), int(ym[5:7])) if ym else (today.year, today.month)
        datetime.date(y, m, 1)
    except (ValueError, TypeError):
        y, m = today.year, today.month
    ndays = _cal.monthrange(y, m)[1]
    staff = core.load_staff()
    punches = core.load_punches()
    present_by_day = {}
    for dd in range(1, ndays + 1):
        data = core.compute_day(datetime.date(y, m, dd), staff, punches)
        present_by_day[dd] = {r["uid"]: r for r in data["present"]}

    WD = ["M", "T", "W", "T", "F", "S", "S"]
    day_hdr = ""
    for dd in range(1, ndays + 1):
        wd = datetime.date(y, m, dd).weekday()
        cls = ' class="sun"' if wd == 6 else ""
        day_hdr += f'<th{cls}>{dd}<br><span class="wd">{WD[wd]}</span></th>'

    body = ""
    for uid, info in sorted(staff.items()):
        if uid in cfg.EXCLUDE_IDS or not info["active"]:
            continue
        cells, pres, absent = "", 0, 0
        for dd in range(1, ndays + 1):
            dcur = datetime.date(y, m, dd)
            if dcur > today:
                cells += '<td class="fut"></td>'
                continue
            wd = dcur.weekday()
            sun = wd == 6
            rec = present_by_day[dd].get(uid)
            base = "sun " if sun else ""
            if rec:
                pres += 1
                t = rec["first"].strftime("%H:%M")
                out = rec["last"].strftime("%H:%M") if rec["n"] >= 2 else ""
                late = "late " if rec["late"] else ""
                inner = t + (f'<br><span class="out">{out}</span>' if out else "")
                cells += f'<td class="{base}{late}">{inner}</td>'
            else:
                if not sun:
                    absent += 1
                cells += f'<td class="{base}abs">&middot;</td>'
        body += (f'<tr><td class="nm">{esc(info["name"])}</td>{cells}'
                 f'<td class="tot">{pres}</td><td class="tot abs2">{absent}</td></tr>')

    import json as _json
    WDF = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    mstaff = [{"uid": uid, "name": info["name"]} for uid, info in sorted(staff.items())
              if uid not in cfg.EXCLUDE_IDS and info["active"]]
    uids = [s["uid"] for s in mstaff]
    mdays, mcells = [], {str(u): {} for u in uids}
    for dd in range(1, ndays + 1):
        dcur = datetime.date(y, m, dd)
        wd = dcur.weekday()
        fut = dcur > today
        mdays.append({"d": dd, "wd": WDF[wd], "sun": wd == 6, "future": fut})
        if fut:
            continue
        for uid in uids:
            rec = present_by_day[dd].get(uid)
            if rec:
                mcells[str(uid)][str(dd)] = {
                    "i": rec["first"].strftime("%H:%M"),
                    "o": rec["last"].strftime("%H:%M") if rec["n"] >= 2 else "",
                    "l": 1 if rec["late"] else 0}
    mdata = _json.dumps({"today": today.day if (today.year == y and today.month == m) else 0,
                         "staff": mstaff, "days": mdays, "cells": mcells})

    prevm = datetime.date(y, m, 1) - datetime.timedelta(days=1)
    nextm = (datetime.date(y, m, 28) + datetime.timedelta(days=10)).replace(day=1)
    mname = datetime.date(y, m, 1).strftime("%B %Y")

    MONTH_JS = r"""
let mode='person';
let pid = MD.staff.length ? String(MD.staff[0].uid) : '';
let did = MD.today || (function(){var d=MD.days.filter(function(x){return !x.future;});return d.length?d[d.length-1].d:1;})();
function card(label,c,sun){
  var out = c.o ? '<small>out '+c.o+'</small>' : '';
  var badge = c.l ? '<span class="mbadge b-late">late</span>' : '';
  return '<div class="mcard'+(sun?' sn':'')+'"><div class="dt">'+label+'</div><div class="tm">'+c.i+out+'</div>'+badge+'</div>';
}
function emptyCard(label,sun){
  return '<div class="mcard'+(sun?' sn':'')+'"><div class="dt">'+label+'</div><div class="none">'+(sun?'\u2014':'absent')+'</div></div>';
}
function render(){
  document.getElementById('bP').className = mode==='person'?'on':'';
  document.getElementById('bD').className = mode==='day'?'on':'';
  var sel=document.getElementById('msel'), out=document.getElementById('mout'), html='';
  if(mode==='person'){
    sel.innerHTML = MD.staff.map(function(s){return '<option value="'+s.uid+'"'+(String(s.uid)===pid?' selected':'')+'>'+s.name+'</option>';}).join('');
    var cells = MD.cells[pid]||{}, pres=0, ab=0;
    MD.days.forEach(function(dy){
      if(dy.future) return;
      var c=cells[dy.d];
      if(c){pres++; html+=card(dy.wd+' '+dy.d,c,dy.sun);}
      else { if(!dy.sun) ab++; html+=emptyCard(dy.wd+' '+dy.d,dy.sun); }
    });
    document.getElementById('msum').textContent='Present '+pres+'   \u00b7   Absent '+ab;
  } else {
    sel.innerHTML = MD.days.filter(function(dy){return !dy.future;}).map(function(dy){return '<option value="'+dy.d+'"'+(String(dy.d)===String(did)?' selected':'')+'>'+dy.wd+' '+dy.d+'</option>';}).join('');
    var pres2=0;
    MD.staff.forEach(function(s){
      var c=(MD.cells[String(s.uid)]||{})[did];
      if(c){pres2++; html+=card(s.name,c,false);}
      else html+=emptyCard(s.name,false);
    });
    document.getElementById('msum').textContent='Present '+pres2+' of '+MD.staff.length;
  }
  out.innerHTML = html || '<div class="msum">No punches.</div>';
}
document.getElementById('bP').onclick=function(){mode='person';render();};
document.getElementById('bD').onclick=function(){mode='day';render();};
document.getElementById('msel').onchange=function(e){ if(mode==='person') pid=e.target.value; else did=e.target.value; render(); };
render();
"""

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance Register {mname}</title><style>{MONTH_CSS}</style></head><body>
<div class="bar"><h1>Attendance Register &middot; {mname}</h1>
<a href="/month?ym={prevm:%Y-%m}">&larr; {prevm:%b}</a>
<a href="/month?ym={nextm:%Y-%m}">{nextm:%b} &rarr;</a>
<a href="/">Today</a>
<button onclick="window.print()">Print</button></div>
<div class="note">Each cell shows the day's first punch (arrival); a second line is the last punch (departure).
&middot; = no punch. Shaded = Sunday. Orange = late. "P" = days present, "A" = working-day absences.
Print in Landscape. Dr. Manoj Agarwal Clinic.</div>
<div class="tablewrap desktop-only"><table>
<thead><tr><th class="nm">Name</th>{day_hdr}<th class="tot">P</th><th class="tot">A</th></tr></thead>
<tbody>{body}</tbody></table></div>
<div class="mobile-only mwrap">
<div class="mtoggle"><button id="bP">By person</button><button id="bD">By day</button></div>
<select class="msel" id="msel"></select>
<div class="msum" id="msum"></div>
<div id="mout"></div></div>
<script>const MD = {mdata};
""" + MONTH_JS + """</script>
</body></html>"""
    return page


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg.DASHBOARD_PORT)
