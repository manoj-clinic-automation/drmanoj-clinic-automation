#!/usr/bin/env python3
"""
staff_ledger.py  v1 (S154, D255/D257)  —  Staff Ledger: maker-checker adjustments
=================================================================================
A small standalone web app for the clinic VPS. Makers enter staff money/leave
events; checkers (the doctors) approve by phone tap. Approved rows are
APPEND-ONLY; corrections happen by CONTRA entry. Monthly close emits one
approved-adjustments CSV for the salary workbook.

Frozen attendance core untouched (additive, same pattern as att_month_report).
Data lives ONLY on the VPS (F-31): /root/staff_ledger/ .

Commands
--------
  /root/wa/venv/bin/python3 staff_ledger.py serve                 # run web app (systemd)
  /root/wa/venv/bin/python3 staff_ledger.py adduser               # interactive: add/replace a login
  /root/wa/venv/bin/python3 staff_ledger.py deluser NAME          # disable a login
  /root/wa/venv/bin/python3 staff_ledger.py listusers
  /root/wa/venv/bin/python3 staff_ledger.py close 2026-08         # monthly close -> CSV
  /root/wa/venv/bin/python3 staff_ledger.py --selftest            # synthetic end-to-end test

Environment (all optional):
  LEDGER_DIR   data directory        (default /root/staff_ledger)
  LEDGER_PORT  port                  (default 8043)
  STAFF_CSV    staff master path     (default /root/staff_master.csv)
  NTFY_URL     e.g. https://ntfy.sh/yourtopic  — pinged on new PENDING entry
"""

import os, sys, json, csv, hashlib, secrets, datetime, tempfile, getpass, urllib.request

# ---------------------------------------------------------------- constants --
APP_VERSION = "1.2-S154"
LEDGER_DIR  = os.environ.get("LEDGER_DIR", "/root/staff_ledger")
STAFF_CSV   = os.environ.get("STAFF_CSV", "/root/staff_master.csv")
PORT        = int(os.environ.get("LEDGER_PORT", "8043"))
NTFY_URL    = os.environ.get("NTFY_URL", "").strip()
URL_PREFIX  = "/ledger"

# Rate card (owner-ruled S154). Amounts in Rs. sign: +1 credit to staff, -1 debit.
CATEGORIES = {
    #  key                label                    rate  per_day  sign  narr_req
    "NIGHT_DUTY":        ("Night duty",             200,  True,   +1,  False),
    "FINE_UNIFORM":      ("Uniform fine",            20,  True,   -1,  False),
    "FINE_ICARD":        ("I-card fine",             20,  True,   -1,  False),
    "LEAVE_APPROVED":    ("Approved leave (record)",  0,  True,    0,  False),
    "ICARD_REPLACEMENT": ("I-card replacement",     100,  False,  -1,  False),
    "ADVANCE_ISSUE":     ("Advance issued",        None,  False,  +1,  False),
    "FINE_ADHOC":        ("Ad-hoc fine (doctors)", None,  False,  -1,  True),
    "OTHER":             ("Other adjustment",      None,  False,  None,True),
}
ROLE_CATS = {
    "maker_full":    ["NIGHT_DUTY","FINE_UNIFORM","FINE_ICARD","LEAVE_APPROVED",
                      "ICARD_REPLACEMENT","ADVANCE_ISSUE"],
    "maker_limited": ["LEAVE_APPROVED","FINE_UNIFORM","FINE_ICARD"],
    "checker":       list(CATEGORIES.keys()),
}

# ------------------------------------------------------------------ storage --
def _p(name): return os.path.join(LEDGER_DIR, name)

def load_users():
    try:
        with open(_p("users.json"), encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(u):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    tmp = _p("users.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f: json.dump(u, f, indent=1)
    os.replace(tmp, _p("users.json"))
    os.chmod(_p("users.json"), 0o600)

def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200000).hex()

def load_ledger():
    rows = []
    try:
        with open(_p("ledger.jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line: rows.append(json.loads(line))
    except FileNotFoundError:
        pass
    return rows

def append_ledger(row):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    with open(_p("ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if os.path.exists(_p("ledger.jsonl")):
        os.chmod(_p("ledger.jsonl"), 0o600)

def update_row(row_id, patch):
    """Rewrite the file with one row patched. Only ever changes status fields —
    approved economic content is never edited (contra entries do corrections)."""
    rows = load_ledger()
    hit = False
    for r in rows:
        if r["id"] == row_id:
            r.update(patch); hit = True
    if not hit: raise KeyError(row_id)
    tmp = _p("ledger.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, _p("ledger.jsonl"))
    os.chmod(_p("ledger.jsonl"), 0o600)

def staff_names():
    try:
        with open(STAFF_CSV, encoding="utf-8") as f:
            return [r["name"] for r in csv.DictReader(f) if r.get("active","Y").strip().upper()=="Y"]
    except FileNotFoundError:
        return []

def now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ntfy(msg):
    if not NTFY_URL: return
    try:
        req = urllib.request.Request(NTFY_URL, data=msg.encode("utf-8"),
                                     headers={"Title": "Staff Ledger"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # notification is best-effort; the pending list is the truth

# ------------------------------------------------------------ ledger logic ---
def compute_amount(cat, days, manual_amount):
    label, rate, per_day, sign, _ = CATEGORIES[cat]
    if cat == "LEAVE_APPROVED": return 0
    if rate is None:
        amt = abs(int(manual_amount))
        if cat == "OTHER":
            return amt if int(manual_amount) >= 0 else -amt
        return sign * amt
    return sign * rate * (days if per_day else 1)

def make_entry(users, maker, staff, cat, date_from, date_to, days, manual_amount,
               narration, instalment=None, contra_of=None):
    u = users[maker]
    role = u["role"]
    if cat not in ROLE_CATS[role]:
        raise PermissionError(f"{maker} may not enter {cat}")
    _,_,_,_, narr_req = CATEGORIES[cat]
    if narr_req and not narration.strip():
        raise ValueError("narration is required for this category")
    if cat == "ADVANCE_ISSUE":
        amount = abs(int(manual_amount))
        inst = abs(int(instalment)) if instalment not in (None,"","0",0) else amount
    else:
        amount = compute_amount(cat, days, manual_amount)
        inst = None
    direct = (role == "checker")
    row = {
        "id": secrets.token_hex(6),
        "ts_entry": now(),
        "maker": maker,
        "staff": staff,
        "category": cat,
        "date_from": date_from, "date_to": date_to, "days": days,
        "amount": amount,
        "instalment": inst,
        "narration": narration.strip(),
        "self_flag": (u.get("staff_link","").strip().lower() == staff.strip().lower()
                      and staff.strip() != ""),
        "direct": direct,
        "status": "APPROVED" if direct else "PENDING",
        "checker": maker if direct else "",
        "ts_decision": now() if direct else "",
        "contra_of": contra_of or "",
        "closed_month": "",
    }
    append_ledger(row)
    if not direct:
        ntfy(f"PENDING: {maker} -> {staff}: {CATEGORIES[cat][0]} Rs{abs(amount)}"
             + (" [SELF]" if row["self_flag"] else ""))
    return row

def decide(users, checker, row_id, approve: bool):
    if users[checker]["role"] != "checker":
        raise PermissionError("only checkers decide")
    rows = {r["id"]: r for r in load_ledger()}
    r = rows[row_id]
    if r["status"] != "PENDING":
        raise ValueError("row is not pending")
    update_row(row_id, {"status": "APPROVED" if approve else "REJECTED",
                        "checker": checker, "ts_decision": now()})

def make_contra(users, maker, orig_id, narration):
    rows = {r["id"]: r for r in load_ledger()}
    o = rows[orig_id]
    if o["status"] != "APPROVED":
        raise ValueError("contra targets approved rows only")
    if o["category"] == "ADVANCE_ISSUE" and advance_recovered(o["id"]) > 0:
        raise ValueError("advance already part-recovered; adjust instalments instead")
    u = users[maker]
    if u["role"] != "checker" and o["category"] not in ROLE_CATS[u["role"]]:
        raise PermissionError("outside your categories")
    if not narration.strip():
        raise ValueError("contra needs a narration")
    row = {
        "id": secrets.token_hex(6), "ts_entry": now(), "maker": maker,
        "staff": o["staff"], "category": o["category"],
        "date_from": o["date_from"], "date_to": o["date_to"], "days": o["days"],
        "amount": -o["amount"], "instalment": None,
        "narration": "CONTRA of " + orig_id + ": " + narration.strip(),
        "self_flag": False, "direct": u["role"] == "checker",
        "status": "APPROVED" if u["role"] == "checker" else "PENDING",
        "checker": maker if u["role"] == "checker" else "",
        "ts_decision": now() if u["role"] == "checker" else "",
        "contra_of": orig_id, "closed_month": "",
    }
    append_ledger(row)
    if row["status"] == "PENDING":
        ntfy(f"PENDING CONTRA: {maker} reverses {orig_id} ({o['staff']} Rs{abs(o['amount'])})")
    return row

def advance_recovered(issue_id):
    return sum(-r["amount"] for r in load_ledger()
               if r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == issue_id
               and r["status"] == "APPROVED")

def open_advances():
    out = []
    for r in load_ledger():
        if r["category"] != "ADVANCE_ISSUE" or r["status"] != "APPROVED": continue
        reversed_ = any(x["contra_of"] == r["id"] and x["category"] == "ADVANCE_ISSUE"
                        and x["status"] == "APPROVED" and x["amount"] == -r["amount"]
                        for x in load_ledger())
        if reversed_: continue
        bal = r["amount"] - advance_recovered(r["id"])
        if bal > 0:
            out.append({"issue": r, "balance": bal,
                        "instalment": r.get("instalment") or r["amount"]})
    return out

def close_month(users, checker, month):
    """month = 'YYYY-MM'. Generates ADVANCE_INSTALMENT rows, marks rows closed,
    writes approved_adjustments_<month>.csv. Idempotent: refuses a re-close."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only a checker closes the month")
    for r in load_ledger():
        if r.get("closed_month") == month:
            raise ValueError(f"{month} already closed")
    # 1. instalments due this month
    for adv in open_advances():
        due = min(adv["instalment"], adv["balance"])
        append_ledger({
            "id": secrets.token_hex(6), "ts_entry": now(), "maker": "SYSTEM",
            "staff": adv["issue"]["staff"], "category": "ADVANCE_INSTALMENT",
            "date_from": month, "date_to": month, "days": 0,
            "amount": -due, "instalment": None,
            "narration": f"auto instalment for advance {adv['issue']['id']}"
                         f" (balance after: {adv['balance']-due})",
            "self_flag": False, "direct": True, "status": "APPROVED",
            "checker": checker, "ts_decision": now(),
            "contra_of": adv["issue"]["id"], "closed_month": month,
        })
    # 2. collect + stamp every approved, un-closed row
    rows = load_ledger()
    take = [r for r in rows if r["status"] == "APPROVED" and not r["closed_month"]]
    for r in take:
        update_row(r["id"], {"closed_month": month})
    take = [r for r in load_ledger() if r.get("closed_month") == month
            and r["status"] == "APPROVED"]
    # 3. per-staff summary + detail CSV
    out = _p(f"approved_adjustments_{month}.csv")
    per = {}
    for r in take:
        if r["category"] == "ADVANCE_ISSUE":  # paying out the advance is cash, not salary
            continue
        d = per.setdefault(r["staff"], {"credit":0,"debit":0,"leave_days":0})
        if r["category"] == "LEAVE_APPROVED":
            d["leave_days"] += r["days"]
        elif r["amount"] >= 0: d["credit"] += r["amount"]
        else: d["debit"] += -r["amount"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([f"APPROVED ADJUSTMENTS {month}",
                    f"generated {now()} by {checker}", "", "", ""])
        w.writerow(["staff","credits_Rs","debits_Rs","net_Rs","approved_leave_days"])
        for s in sorted(per):
            d = per[s]
            w.writerow([s, d["credit"], d["debit"], d["credit"]-d["debit"], d["leave_days"]])
        w.writerow([]); w.writerow(["-- detail --","","","",""])
        w.writerow(["staff","category","dates","amount_Rs","maker/checker","narration"])
        for r in sorted(take, key=lambda x:(x["staff"], x["ts_entry"])):
            dates = r["date_from"] + ("" if r["date_to"] in ("", r["date_from"])
                                      else " to " + r["date_to"])
            w.writerow([r["staff"], r["category"], dates, r["amount"],
                        f'{r["maker"]}/{r["checker"]}', r["narration"]])
    os.chmod(out, 0o600)
    return out, len(take)

# ------------------------------------------------------------------ web app --
def create_app():
    from flask import Flask, request, redirect, session, abort
    app = Flask(__name__)
    skf = _p("secret_key")
    os.makedirs(LEDGER_DIR, exist_ok=True)
    if not os.path.exists(skf):
        with open(skf, "w") as f: f.write(secrets.token_hex(32))
        os.chmod(skf, 0o600)
    app.secret_key = open(skf).read().strip()

    def user():
        u = session.get("u")
        users = load_users()
        if not u or u not in users or not users[u].get("active", True):
            return None, users
        return u, users

    def page(title, body, u=None):
        nav = ""
        if u:
            users = load_users()
            role = users[u]["role"]
            links = [f'<a href="{URL_PREFIX}/">New entry</a>',
                     f'<a href="{URL_PREFIX}/mine">My entries</a>']
            if role == "checker":
                links += [f'<a href="{URL_PREFIX}/pending"><b>Pending</b></a>',
                          f'<a href="{URL_PREFIX}/book">Full ledger</a>',
                          f'<a href="{URL_PREFIX}/advances">Advances</a>']
            links.append(f'<a href="{URL_PREFIX}/logout">Logout ({u})</a>')
            nav = "<p>" + " · ".join(links) + "</p>"
        return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font-family:Arial,sans-serif;margin:12px;background:#f7f8fa;color:#222}}
h2{{color:#1f3864;margin:6px 0}} a{{color:#2e5395;text-decoration:none}}
table{{border-collapse:collapse;width:100%;background:#fff}}
td,th{{border:1px solid #ccd;padding:6px;font-size:14px;text-align:left}}
th{{background:#d9e2f3}} .self{{background:#ffe0e0}} .direct{{color:#666;font-style:italic}}
input,select,textarea{{font-size:16px;padding:6px;margin:3px 0;width:100%;box-sizing:border-box}}
button{{font-size:16px;padding:8px 18px;margin:4px 2px;border:0;border-radius:6px;cursor:pointer}}
.ok{{background:#2f8f4e;color:#fff}} .no{{background:#c0392b;color:#fff}}
.card{{background:#fff;border:1px solid #ccd;border-radius:8px;padding:10px;margin:8px 0}}
.amt-c{{color:#2f8f4e;font-weight:bold}} .amt-d{{color:#c0392b;font-weight:bold}}
small{{color:#666}}</style></head><body><h2>Staff Ledger</h2>{nav}{body}
<p><small>v{APP_VERSION} · append-only · corrections by contra entry only</small></p>
</body></html>"""

    @app.route(URL_PREFIX + "/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            users = load_users()
            name = request.form.get("u","").strip().lower()
            pw = request.form.get("p","")
            rec = users.get(name)
            if rec and rec.get("active", True) and hash_pw(pw, rec["salt"]) == rec["pw"]:
                session["u"] = name
                return redirect(URL_PREFIX + "/")
            return page("Login", "<p style='color:red'>Wrong username or password.</p>"
                        + LOGIN_FORM)
        return page("Login", LOGIN_FORM)

    LOGIN_FORM = f"""<div class="card"><form method="post">
      <input name="u" placeholder="username" autocomplete="username">
      <input name="p" id="pw" type="password" placeholder="password"
             autocomplete="current-password">
      <label style="font-weight:normal"><input type="checkbox" style="width:auto"
             onclick="document.getElementById('pw').type=this.checked?'text':'password'">
             show password</label>
      <button class="ok">Login</button></form></div>"""

    @app.route(URL_PREFIX + "/logout")
    def logout():
        session.clear(); return redirect(URL_PREFIX + "/login")

    @app.route(URL_PREFIX + "/", methods=["GET","POST"])
    def entry():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        cats = ROLE_CATS[users[u]["role"]]
        msg = ""
        if request.method == "POST":
            try:
                f = request.form
                cat = f["category"]
                if cat not in cats: abort(403)
                d1 = f.get("date_from","").strip()
                d2 = f.get("date_to","").strip() or d1
                days = 0
                if CATEGORIES[cat][2]:  # per-day
                    a = datetime.date.fromisoformat(d1)
                    b = datetime.date.fromisoformat(d2)
                    days = (b - a).days + 1
                    if days < 1: raise ValueError("date range backwards")
                row = make_entry(users, u, f["staff"], cat, d1, d2, days,
                                 f.get("amount","0") or "0", f.get("narration",""),
                                 instalment=f.get("instalment",""))
                amt = row["amount"]
                msg = (f"<p style='color:green'>Saved <b>{row['status']}</b>: "
                       f"{row['staff']} · {CATEGORIES[cat][0]} · Rs {amt}"
                       + (f" · {days} day(s)" if days else "") + "</p>")
            except Exception as e:
                msg = f"<p style='color:red'>NOT saved: {e}</p>"
        opts_staff = "".join(f"<option>{s}</option>" for s in staff_names())
        opts_cat = "".join(f'<option value="{c}">{CATEGORIES[c][0]}'
                           + (f" (Rs {CATEGORIES[c][1]}"
                              + ("/day" if CATEGORIES[c][2] else "") + ")"
                              if CATEGORIES[c][1] else "")
                           + "</option>" for c in cats)
        catmeta = {c: {"rate": CATEGORIES[c][1], "per_day": CATEGORIES[c][2],
                       "sign": CATEGORIES[c][3], "narr_req": CATEGORIES[c][4],
                       "advance": c == "ADVANCE_ISSUE"} for c in cats}
        body = msg + f"""<div class="card"><form method="post" id="ef">
        <label>Staff</label><select name="staff">{opts_staff}</select>
        <label>Category</label><select name="category" id="cat">{opts_cat}</select>
        <div id="f_d1"><label>Date</label><input type="date" name="date_from" required></div>
        <div id="f_d2"><label>Date (to — leave blank for a single day)</label>
          <input type="date" name="date_to"></div>
        <div id="f_amt"><label id="l_amt">Amount Rs</label>
          <input type="number" name="amount" value="0" min="0"></div>
        <div id="f_inst"><label>Instalment Rs/month (blank = recover fully this month)</label>
          <input type="number" name="instalment" min="0"></div>
        <div id="f_narr"><label id="l_narr">Narration (optional)</label>
          <textarea name="narration" rows="2"></textarea></div>
        <div id="preview" style="font-weight:bold;margin:6px 0"></div>
        <button class="ok">Save entry</button></form>
        <small>Rate-card categories compute their own amount — no typing.
        Doctors' entries save as DIRECT (already approved); everything else goes
        PENDING to the doctors' phone.</small></div>
        <script>
        var M = {json.dumps(catmeta)};
        var cat = document.getElementById("cat"), form = document.getElementById("ef");
        function show(id, on) {{ document.getElementById(id).style.display = on ? "" : "none"; }}
        function refresh() {{
          var m = M[cat.value];
          show("f_d2", m.per_day);
          show("f_amt", m.rate === null);
          show("f_inst", !!m.advance);
          var ln = document.getElementById("l_narr");
          ln.textContent = m.narr_req ? "Narration (REQUIRED for this category)"
                                      : "Narration (optional)";
          form.narration.required = !!m.narr_req;
          preview();
        }}
        function preview() {{
          var m = M[cat.value], el = document.getElementById("preview");
          if (m.rate === null) {{ el.textContent = ""; return; }}
          var d1 = form.date_from.value, d2 = form.date_to.value || d1, days = 1;
          if (m.per_day && d1) {{
            days = Math.round((new Date(d2) - new Date(d1)) / 86400000) + 1;
            if (!(days >= 1)) {{ el.textContent = "check the dates"; return; }}
          }}
          if (!d1) {{ el.textContent = ""; return; }}
          var amt = m.rate * (m.per_day ? days : 1) * (m.sign === 0 ? 0 : 1);
          el.textContent = m.sign === 0
            ? ("Records " + days + " approved leave day(s), Rs 0")
            : ((m.sign < 0 ? "Deduction: Rs " : "Payment: Rs ") + amt
               + (m.per_day ? " (" + days + " day(s))" : ""));
          el.style.color = m.sign < 0 ? "#c0392b" : "#2f8f4e";
        }}
        cat.addEventListener("change", refresh);
        form.date_from.addEventListener("input", preview);
        form.date_to.addEventListener("input", preview);
        refresh();
        </script>"""
        return page("New entry", body, u)

    @app.route(URL_PREFIX + "/mine")
    def mine():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        rows = [r for r in load_ledger() if r["maker"] == u][-60:][::-1]
        return page("My entries", _table(rows), u)

    @app.route(URL_PREFIX + "/pending")
    def pending():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        rows = [r for r in load_ledger() if r["status"] == "PENDING"]
        cards = ""
        for r in rows:
            flag = " <b style='color:red'>[SELF ENTRY]</b>" if r["self_flag"] else ""
            cls = "amt-c" if r["amount"] >= 0 else "amt-d"
            cards += f"""<div class="card{' self' if r['self_flag'] else ''}">
            <b>{r['staff']}</b> — {CATEGORIES.get(r['category'],[r['category']])[0]}{flag}<br>
            <span class="{cls}">Rs {r['amount']}</span> · {r['date_from']}{(' to '+r['date_to']) if r['date_to'] not in ('',r['date_from']) else ''}
            {('· '+str(r['days'])+' day(s)') if r['days'] else ''}<br>
            <small>by {r['maker']} at {r['ts_entry']}</small><br>
            {('<i>'+r['narration']+'</i><br>') if r['narration'] else ''}
            <form method="post" action="{URL_PREFIX}/decide" style="display:inline">
              <input type="hidden" name="id" value="{r['id']}">
              <button class="ok" name="d" value="A">Approve</button>
              <button class="no" name="d" value="R">Reject</button></form></div>"""
        if not rows: cards = "<p>Nothing pending. 👍</p>"
        return page("Pending", cards, u)

    @app.route(URL_PREFIX + "/decide", methods=["POST"])
    def do_decide():
        u, users = user()
        if not u or users[u]["role"] != "checker": abort(403)
        decide(users, u, request.form["id"], request.form["d"] == "A")
        return redirect(URL_PREFIX + "/pending")

    @app.route(URL_PREFIX + "/book")
    def book():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        rows = load_ledger()[-200:][::-1]
        extra = f"""<div class="card"><form method="post" action="{URL_PREFIX}/contra">
          <label>Correct a mistake — contra an APPROVED row. Row id:</label>
          <input name="id" placeholder="row id from the table">
          <label>Why:</label><input name="narration" required>
          <button class="no">Create contra (reverses the amount)</button></form></div>"""
        return page("Full ledger", extra + _table(rows, show_id=True), u)

    @app.route(URL_PREFIX + "/contra", methods=["POST"])
    def contra():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        try:
            make_contra(users, u, request.form["id"].strip(), request.form["narration"])
        except Exception as e:
            return page("Contra", f"<p style='color:red'>{e}</p>", u)
        return redirect(URL_PREFIX + "/book")

    @app.route(URL_PREFIX + "/advances")
    def advances():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        body = ""
        for a in open_advances():
            body += (f"<div class='card'><b>{a['issue']['staff']}</b> — advance "
                     f"Rs {a['issue']['amount']} ({a['issue']['date_from']})<br>"
                     f"balance <b>Rs {a['balance']}</b> · recovering Rs {a['instalment']}/month"
                     f"<br><small>id {a['issue']['id']}</small></div>")
        if not body: body = "<p>No open advances.</p>"
        return page("Open advances", body, u)

    def _table(rows, show_id=False):
        h = ("<tr>" + ("<th>id</th>" if show_id else "")
             + "<th>staff</th><th>category</th><th>dates</th><th>Rs</th>"
               "<th>status</th><th>maker→checker</th><th>note</th></tr>")
        b = ""
        for r in rows:
            cls = "amt-c" if r["amount"] >= 0 else "amt-d"
            row_cls = " class='self'" if r.get("self_flag") else ""
            dates = r["date_from"] + ("" if r["date_to"] in ("", r["date_from"])
                                      else "→" + r["date_to"])
            b += (f"<tr{row_cls}>" + (f"<td><small>{r['id']}</small></td>" if show_id else "")
                  + f"<td>{r['staff']}</td>"
                  f"<td>{CATEGORIES.get(r['category'],[r['category']])[0]}"
                  + ("<span class='direct'> ·direct</span>" if r.get("direct") else "") + "</td>"
                  f"<td>{dates}</td><td class='{cls}'>{r['amount']}</td>"
                  f"<td>{r['status']}{('·'+r['closed_month']) if r.get('closed_month') else ''}</td>"
                  f"<td><small>{r['maker']}→{r.get('checker','')}</small></td>"
                  f"<td><small>{r.get('narration','')}</small></td></tr>")
        return f"<table>{h}{b}</table>"

    return app

# ------------------------------------------------------------------ CLI ------
def cli_adduser():
    users = load_users()
    name = input("username (lowercase, e.g. shavez): ").strip().lower()
    role = input("role [maker_full / maker_limited / checker]: ").strip()
    if role not in ROLE_CATS: sys.exit("bad role")
    link = input("staff name this login belongs to (blank if doctor): ").strip()
    pw = getpass.getpass("password: ")
    pw2 = getpass.getpass("repeat  : ")
    if pw != pw2 or len(pw) < 6: sys.exit("passwords differ or too short (<6)")
    salt = secrets.token_hex(16)
    users[name] = {"pw": hash_pw(pw, salt), "salt": salt, "role": role,
                   "staff_link": link, "active": True}
    save_users(users)
    print(f"user '{name}' ({role}) saved. Swap anyone anytime: deluser + adduser.")

def cli_deluser(name):
    users = load_users()
    if name not in users: sys.exit("no such user")
    users[name]["active"] = False
    save_users(users); print(f"user '{name}' disabled (rows they made remain).")

def cli_listusers():
    for n, r in load_users().items():
        print(f"{n:12s} {r['role']:14s} active={r.get('active',True)} link={r.get('staff_link','')}")

# ------------------------------------------------------------- selftest ------
def selftest():
    global LEDGER_DIR, STAFF_CSV
    tmp = tempfile.mkdtemp()
    LEDGER_DIR = tmp
    STAFF_CSV = os.path.join(tmp, "staff.csv")
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["user_id","name","active"])
        for i, n in enumerate(["Alpha","Beta","Gamma"]): w.writerow([i+1, n, "Y"])
    ok = [0]
    def ck(cond, msg):
        ok[0] += 1
        if not cond: raise AssertionError(f"selftest check {ok[0]} FAILED: {msg}")
    # users
    for name, role, link in (("mfull","maker_full","Beta"), ("mlim","maker_limited",""),
                             ("doc","checker",""), ("doc2","checker","")):
        salt = secrets.token_hex(16)
        u = load_users(); u[name] = {"pw": hash_pw("pw", salt), "salt": salt,
                                     "role": role, "staff_link": link, "active": True}
        save_users(u)
    users = load_users()
    ck(len(users) == 4, "4 users")
    ck(hash_pw("pw", users["doc"]["salt"]) == users["doc"]["pw"], "pw roundtrip")
    ck(hash_pw("wrong", users["doc"]["salt"]) != users["doc"]["pw"], "wrong pw rejected")
    # rate card computations
    r = make_entry(users, "mfull", "Alpha", "NIGHT_DUTY", "2026-08-02","2026-08-03",2,"0","")
    ck(r["amount"] == 400 and r["status"] == "PENDING", "night 2d=+400 pending")
    r2 = make_entry(users, "mlim", "Alpha", "FINE_UNIFORM", "2026-08-04","2026-08-06",3,"0","")
    ck(r2["amount"] == -60, "uniform 3d=-60")
    r3 = make_entry(users, "mlim", "Alpha", "FINE_ICARD", "2026-08-04","2026-08-04",1,"0","")
    ck(r3["amount"] == -20, "icard 1d=-20")
    rl = make_entry(users, "mlim", "Beta", "LEAVE_APPROVED", "2026-08-10","2026-08-11",2,"0","")
    ck(rl["amount"] == 0 and rl["days"] == 2, "leave 0Rs 2d")
    # permissions
    try:
        make_entry(users, "mlim", "Alpha", "NIGHT_DUTY", "2026-08-01","2026-08-01",1,"0","")
        ck(False, "mlim night must fail")
    except PermissionError: ck(True, "mlim blocked from night duty")
    try:
        make_entry(users, "mfull", "Alpha", "FINE_ADHOC", "2026-08-01","2026-08-01",0,"500","x")
        ck(False, "mfull adhoc must fail")
    except PermissionError: ck(True, "mfull blocked from ad-hoc")
    try:
        make_entry(users, "doc", "Alpha", "FINE_ADHOC", "2026-08-01","2026-08-01",0,"500","")
        ck(False, "adhoc without narration must fail")
    except ValueError: ck(True, "ad-hoc narration required")
    ra = make_entry(users, "doc", "Alpha", "FINE_ADHOC", "2026-08-01","2026-08-01",0,"500","misbehaviour")
    ck(ra["amount"] == -500 and ra["status"] == "APPROVED" and ra["direct"], "doctor direct adhoc -500")
    # self flag
    rs = make_entry(users, "mfull", "Beta", "NIGHT_DUTY", "2026-08-05","2026-08-05",1,"0","")
    ck(rs["self_flag"] is True, "self entry flagged")
    # replacement + approval flow
    rr = make_entry(users, "mfull", "Gamma", "ICARD_REPLACEMENT", "2026-08-07","2026-08-07",0,"0","lost")
    ck(rr["amount"] == -100, "replacement -100")
    decide(users, "doc", r["id"], True)
    decide(users, "doc2", r2["id"], True)
    decide(users, "doc", r3["id"], False)          # rejected
    decide(users, "doc", rl["id"], True)
    decide(users, "doc", rs["id"], True)
    decide(users, "doc", rr["id"], True)
    got = {x["id"]: x for x in load_ledger()}
    ck(got[r["id"]]["status"] == "APPROVED" and got[r["id"]]["checker"] == "doc", "approve stamps checker")
    ck(got[r3["id"]]["status"] == "REJECTED", "reject works")
    try:
        decide(users, "mfull", rr["id"], True); ck(False, "maker deciding must fail")
    except (PermissionError, ValueError): ck(True, "maker cannot decide")
    try:
        decide(users, "doc", r["id"], True); ck(False, "double-decide must fail")
    except ValueError: ck(True, "no double decision")
    # contra
    c = make_contra(users, "doc", r2["id"], "entered on wrong staff")
    ck(c["amount"] == 60 and c["status"] == "APPROVED" and c["contra_of"] == r2["id"], "doctor contra direct +60")
    c2 = make_contra(users, "mfull", rr["id"], "card was found")
    ck(c2["status"] == "PENDING", "maker contra pends")
    decide(users, "doc2", c2["id"], True)
    try:
        make_contra(users, "doc", r3["id"], "x"); ck(False, "contra of rejected must fail")
    except ValueError: ck(True, "contra only approved rows")
    # advances: default full recovery + instalment mode
    a1 = make_entry(users, "mfull", "Alpha", "ADVANCE_ISSUE", "2026-08-08","2026-08-08",0,"3000","", instalment="")
    ck(a1["amount"] == 3000 and a1["instalment"] == 3000, "advance default=full this month")
    a2 = make_entry(users, "mfull", "Gamma", "ADVANCE_ISSUE", "2026-08-08","2026-08-08",0,"5000","", instalment="2000")
    decide(users, "doc", a1["id"], True); decide(users, "doc", a2["id"], True)
    ck(len(open_advances()) == 2, "two open advances")
    # month close
    out, n = close_month(users, "doc", "2026-08")
    ck(os.path.exists(out), "close writes csv")
    got = load_ledger()
    inst = [x for x in got if x["category"] == "ADVANCE_INSTALMENT"]
    ck(sorted(-x["amount"] for x in inst) == [2000, 3000], "instalments 3000 full + 2000 partial")
    ck(all(x["closed_month"] == "2026-08" for x in got if x["status"] == "APPROVED"), "all approved rows stamped closed")
    try:
        close_month(users, "doc", "2026-08"); ck(False, "re-close must fail")
    except ValueError: ck(True, "close is idempotent-guarded")
    adv_open = open_advances()
    ck(len(adv_open) == 1 and adv_open[0]["balance"] == 3000 and adv_open[0]["issue"]["staff"] == "Gamma",
       "Gamma balance 5000-2000=3000; Alpha closed")
    # Alpha: credits = night 400 + contra 60 = 460; debits = uniform 60 + adhoc 500
    # + instalment 3000 = 3560; net -3100 (contra and original cancel in net).
    with open(out, encoding="utf-8") as f: txt = f.read()
    import re as _re
    m = _re.search(r"^Alpha,(\d+),(\d+),(-?\d+),(\d+)", txt, _re.M)
    ck(m is not None, "Alpha summary row present")
    cred, deb, net, ld = map(int, m.groups())
    ck(cred == 460 and deb == 3560 and net == -3100 and ld == 0,
       f"Alpha money math (got {cred},{deb},{net},{ld})")
    m = _re.search(r"^Beta,(\d+),(\d+),(-?\d+),(\d+)", txt, _re.M)
    cred, deb, net, ld = map(int, m.groups())
    ck(cred == 200 and deb == 0 and net == 200 and ld == 2, f"Beta night200 + 2 leave days (got {cred},{deb},{net},{ld})")
    ck("ADVANCE_ISSUE" not in txt.split("-- detail --")[0], "advance payout not in salary summary")
    # append-only guarantee: economic fields of approved rows never changed
    ck(got and all("amount" in x for x in got), "rows intact")
    # web app smoke: login + entry + pending via test client
    app = create_app()
    cl = app.test_client()
    resp = cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"pw"})
    ck(resp.status_code == 302, "web login ok")
    resp = cl.get(URL_PREFIX + "/pending")
    ck(resp.status_code == 200, "pending page renders")
    resp = cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"WRONG"})
    ck(b"Wrong username" in resp.data, "web rejects bad password")
    cl2 = app.test_client()
    cl2.post(URL_PREFIX + "/login", data={"u":"mlim","p":"pw"})
    ck(cl2.get(URL_PREFIX + "/pending").status_code == 403, "maker blocked from pending page")
    r = cl2.post(URL_PREFIX + "/", data={"staff":"Alpha","category":"FINE_UNIFORM",
                                         "date_from":"2026-09-01","date_to":"2026-09-02",
                                         "narration":""})
    ck(b"Saved" in r.data and b"-40" in r.data.replace(b"Rs ", b"Rs"), "web entry uniform 2d saved")
    r = cl2.post(URL_PREFIX + "/", data={"staff":"Alpha","category":"NIGHT_DUTY",
                                         "date_from":"2026-09-01","date_to":"2026-09-01",
                                         "narration":""})
    ck(b"NOT saved" in r.data or r.status_code == 403, "web blocks out-of-role category")
    # adaptive form: role-scoped metadata + dynamic narration handling
    pg = cl2.get(URL_PREFIX + "/").data.decode()
    ck('"FINE_UNIFORM"' in pg and '"FINE_ADHOC"' not in pg,
       "limited maker's form metadata excludes doctor-only categories")
    ck("Narration (optional)" in pg and "refresh()" in pg, "adaptive form script present")
    pgd = cl.get(URL_PREFIX + "/").data.decode()
    ck('"FINE_ADHOC"' in pgd and '"narr_req": true' in pgd,
       "doctor form carries adhoc with narr_req=true")
    lg = cl.get(URL_PREFIX + "/login").data.decode()
    ck("show password" in lg, "login page has show-password toggle")
    print(f"SELFTEST PASSED — {ok[0]} maker-checker, rate-card, advance, close and web checks OK")

# ------------------------------------------------------------------ main -----
if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print(__doc__); sys.exit(0)
    if args[0] == "--selftest": selftest()
    elif args[0] == "serve":
        create_app().run(host="127.0.0.1", port=PORT)
    elif args[0] == "adduser": cli_adduser()
    elif args[0] == "deluser": cli_deluser(args[1])
    elif args[0] == "listusers": cli_listusers()
    elif args[0] == "close":
        users = load_users()
        checkers = [n for n,r in users.items() if r["role"]=="checker" and r.get("active",True)]
        if not checkers: sys.exit("no checker user exists")
        out, n = close_month(users, checkers[0], args[1])
        print(f"Closed {args[1]}: {n} approved rows -> {out}")
    else:
        sys.exit("unknown command; run with --help")
