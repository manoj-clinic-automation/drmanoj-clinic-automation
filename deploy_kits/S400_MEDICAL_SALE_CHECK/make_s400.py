#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s400.py -- builds the six patched live files of kit S400_MEDICAL_SALE_CHECK from the LIVE bytes by
anchored edits. Every anchor must occur exactly once, and every source must be at its FROM pin, or the
build stops with nothing written. Nothing is re-typed.

  finance_app.py             the front gate learns the unit 'salecheck' (/finance/salecheck/...); the module is mounted
  sanjeevni_day.py           the owner's day panel: Checks gain Bhati's verdict, galti list, cash entry (fail-soft)
  sanjeevni_approvals.py     the days API carries Bhati's mark per day; Needs you gains "Bhati found mistakes on N day(s)"
  finance_approvals.html     one small line per day row (Bhati ✓ 09:40 / Bhati: 2 mistakes, tap -> the list; the cash
                             entry with the person/date change for the owner)
  portal.py                  the tile 'Medical sale check' (roles ['doctor']; granted by name)
  tile_grants.json           v25 -> v26: the tile to bhati

Usage: make_s400.py --finance /root/finance --portal /root/portal --out DIR
Writes DIR/finance_app.py, DIR/sanjeevni_day.py, DIR/sanjeevni_approvals.py, DIR/finance_approvals.html,
DIR/portal.py, DIR/tile_grants.json and prints each md5.
"""
import hashlib
import json
import os
import sys

FROM = {
    "finance_app.py": "70cff4981c2ebf554308545fb071f0d4",
    "sanjeevni_day.py": "5d16eff5b6e2f0fd561e22d91e4794ab",
    "sanjeevni_approvals.py": "7ab5fec63db83af3e11c6ac08599be93",
    "finance_approvals.html": "750f89e008a89a372af25cf7898a7d17",
    "portal.py": "80d6dc44acc07ebb0b974fb792507fee",
    "tile_grants.json": "7d1954760181b4e36e732a974599fd35",
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
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:70]))
    return s.replace(old, new)


# ---------------------------------------------------------------- finance_app.py
def build_finance_app(s):
    s = rep(s, '''    if path == "/finance/checks" or path.startswith("/finance/checks/"):
        return "checks"      # S340: reception's "Check karein" queue for patient records (owner, 20-Sep-2026).
''', '''    if path == "/finance/checks" or path.startswith("/finance/checks/"):
        return "checks"      # S340: reception's "Check karein" queue for patient records (owner, 20-Sep-2026).
    if path == "/finance/salecheck" or path.startswith("/finance/salecheck/"):
        return "salecheck"   # S400: Bhati checks the pharmacy days (owner, 25-Sep-2026, D616). No medical row for him.
''', "finance_app _unit_for_path")
    s = rep(s, '''# --- S349_WATCHER_FRESHNESS end ---
''', '''# --- S349_WATCHER_FRESHNESS end ---


# --- S400_MEDICAL_SALE_CHECK begin -- Bhati checks the pharmacy days not yet approved (owner, 25-Sep-2026, D616) ---
# Its own unit 'salecheck' (maker = bhati, checker = the owner); its own three sale_check_* tables, created on first
# request. Reads the owner's day panel's figures (sanjeevni_day) and lands Bhati's cash through darpan_kal's own path.
# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import sale_check                                          # noqa: E402
    sale_check.init(app, db, require, unit=UNIT)
except Exception as _ex_sc:                                    # noqa: BLE001
    print("sale_check NOT mounted: %s" % _ex_sc, file=sys.stderr)
# --- S400_MEDICAL_SALE_CHECK end ---
''', "finance_app mount")
    return s


# ---------------------------------------------------------------- sanjeevni_day.py
def build_day(s):
    s = rep(s, '''#  sanjeevni_day.py  ·  v1.1  ·  kit S367_DAY_TRUTH_4  ·  Session 281 (Sanjeevni)
''', '''#  sanjeevni_day.py  ·  v1.2  ·  kit S400_MEDICAL_SALE_CHECK  ·  Session 283 (Sanjeevni)
#  v1.2 (S400, D616, 25-Sep-2026): the Checks also say what Bhati found when he checked the day against
#  the paper copy and Marg -- his verdict, his galti list, the cash he entered (sale_check.owner_checks,
#  fail-soft). v1.1 was kit S367_DAY_TRUTH_4, Session 281.
''', "day header")
    s = rep(s, '''VERSION = "1.1"
''', '''VERSION = "1.2"
''', "day version")
    s = rep(s, '''    return dict(ok=True, date=iso, weekday=wd, filed=True, status=status, approved_by=e[2],
''', '''    try:                                                     # S400: Bhati's check of this day, in words
        import sale_check
        checks.extend(sale_check.owner_checks(con, iso))
    except Exception:                                         # noqa: BLE001 -- words only; never breaks the panel
        pass
    return dict(ok=True, date=iso, weekday=wd, filed=True, status=status, approved_by=e[2],
''', "day checks")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.0  ·  kit S368_APPROVALS_TREE  ·  Session 281 (Sanjeevni)
''', '''#  sanjeevni_approvals.py  ·  v1.4  ·  kit S400_MEDICAL_SALE_CHECK  ·  Session 283 (Sanjeevni)
#
#  v1.4 (S400, D616, 25-Sep-2026): each day line carries Bhati's mark (his verdict and time, his galti list, the cash
#  he entered) read from sale_check, fail-soft; Needs you gains "Bhati found mistakes on N day(s)" for unapproved days.
#  Nothing else moves. v1.0 was kit S368_APPROVALS_TREE, Session 281.
''', "approvals header")
    s = rep(s, '''VERSION = "1.3"
''', '''VERSION = "1.4"
''', "approvals version")
    s = rep(s, '''PARTY = {"dr_bhawna": "Dr Bhawna", "dr_manoj": "you", "pool": "the pool", "bank": "the bank"}
''', '''PARTY = {"dr_bhawna": "Dr Bhawna", "dr_manoj": "you", "pool": "the pool", "bank": "the bank"}


def _bhati_marks(con):
    """S400: business_date -> Bhati's mark (verdict, time, galti list, cash entry); {} when the module or its
    tables are not there."""
    try:
        import sale_check  # noqa: PLC0415
        return sale_check.owner_marks(con) or {}
    except Exception:  # noqa: BLE001
        return {}
''', "approvals helper")
    s = rep(s, '''    kal = _kal_rows(con)
    out = []
''', '''    kal = _kal_rows(con)
    bhati = _bhati_marks(con)                                   # S400
    out = []
''', "approvals marks")
    s = rep(s, '''                        waiting_approval=bool(x["waiting_approval"])))
''', '''                        waiting_approval=bool(x["waiting_approval"]), bhati=bhati.get(d)))
''', "approvals day dict")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 8 · S400: Bhati's check of the pharmacy days -- mistakes he marked on days still to approve
    try:
        import sale_check  # noqa: PLC0415
        nb = int(sale_check.days_with_mistakes(con) or 0)
        if nb:
            lines.append(dict(cls="warn", target="days", text="Bhati found mistakes on %d day%s" % (nb, "" if nb == 1 else "s")))
    except Exception:  # noqa: BLE001
        pass
    # 7 · the statement's age (a word, not a fault)
''', "approvals needs-you")
    return s


# ---------------------------------------------------------------- finance_approvals.html
def build_html(s):
    s = rep(s, '''      (d.banked||[]).forEach(function(b){st+=' <span class="pill ok">'+esc(b.amount)+' banked'+(b.place?' · '+esc(b.place):'')+'</span>'});
''', '''      (d.banked||[]).forEach(function(b){st+=' <span class="pill ok">'+esc(b.amount)+' banked'+(b.place?' · '+esc(b.place):'')+'</span>'});
      if(d.bhati) st+=bhatiLine(d);                                    /* S400: Bhati's mark, one small line */
''', "html day line")
    s = rep(s, '''/* ---- Bank: pharmacy UPI by day; the Yes Bank statement and its cash deposits ---- */
''', '''/* ---- S400_MEDICAL_SALE_CHECK (25-Sep-2026, D616): Bhati's mark on a day row -- "Bhati ✓ 09:40" or
   "Bhati: 2 mistakes" (tap -> bill, problem, note) -- and the cash he entered; the owner may change its
   person or move it to another unapproved day here. Everything else on the row is as before. ---- */
var bhatiOpen={};
function bhatiLine(d){
  var b=d.bhati, h='<div class="sub" style="margin-top:3px">';
  if(b.n) h+='<a href="#" onclick="event.stopPropagation();bhatiOpen[\\''+d.date+'\\']=!bhatiOpen[\\''+d.date+'\\'];renderDays();return false"><b>'+esc(b.text)+'</b> ▸</a>';
  else if(b.verdict==='ok') h+='<span class="ok">'+esc(b.text)+'</span>';
  if(b.cash) h+=(b.n||b.verdict==='ok'?' · ':'')+'cash '+esc(b.cash.amount)+' to '+esc(b.cash.to)+' (Bhati, '+esc(b.cash.at)+')'+
      (b.cash.diff_p?' <span class="bad">Darpan had '+esc(b.cash.darpan)+'</span>':'')+
      (!d.approved?' <a href="#" onclick="event.stopPropagation();bhatiMove(\\''+d.date+'\\');return false">change</a>':'');
  h+='</div>';
  if(b.n&&bhatiOpen[d.date]) h+='<div class="sub">'+b.issues.map(function(i){return esc(i.bill)+' — '+esc(i.problem)+(i.note?' — '+esc(i.note):'')}).join('<br>')+'</div>';
  return h;
}
function bhatiMove(d){
  dayOpen[d]=true; renderDays();
  var box=$("logbox-"+d); if(!box||!DAYS)return;
  var opts=DAYS.days.filter(function(x){return !x.approved&&x.date!==d}).map(function(x){return '<option value="'+x.date+'">'+esc(x.day)+' '+esc(x.weekday)+'</option>'}).join("");
  box.innerHTML='<div class="logbox"><b>Bhati\\'s cash entry of '+esc(d)+'</b> to '+
    '<button onclick="bhatiSend(\\''+d+'\\',{party:\\'dr_manoj\\'})">me</button><button onclick="bhatiSend(\\''+d+'\\',{party:\\'dr_bhawna\\'})">Dr Bhawna</button>'+
    (opts?' · move to <select id="bhmv-'+d+'">'+opts+'</select><button onclick="bhatiSend(\\''+d+'\\',{new_date:$(\\'bhmv-'+d+'\\').value})">move</button>':'')+
    '<button class="ghost" onclick="$(\\'logbox-'+d+'\\').innerHTML=\\'\\'">cancel</button><span class="mut">The amount is changed with Log cash, as today.</span></div>';
}
function bhatiSend(d,body){
  body.date=d;
  fetch("/finance/salecheck/api/owner/move",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
    .then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"could not change");return} loadDays(); loadCashPos(); loadNeeds();})
    .catch(function(e){alert("nothing was changed — the server could not be reached ("+e+")")});
}

/* ---- Bank: pharmacy UPI by day; the Yes Bank statement and its cash deposits ---- */
''', "html functions")
    return s


# ---------------------------------------------------------------- portal.py
def build_portal(s):
    s = rep(s, '''    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', '''    {"icon": "\\U0001F50D", "name": "Medical sale check",
     # S400 NEW (owner, 25-Sep-2026, D616). Bhati checks the Sanjeevni days not yet approved against Darpan's
     # paper copy and the Marg sheet: Sahi hai / Galti hai (drop-downs), and the cash Darpan handed (Dr Bhawna
     # by default, one tap for Dr Manoj; date = the sale date). Its own server unit ('salecheck'); he holds no
     # medical row. Granted by name in tile_grants.json v26 to bhati; the doctor holds it by role.
     "desc": "Sanjeevni ke din \\u00b7 jaanch aur cash",
     "live": True,
     "url": "/finance/salecheck",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', "portal tile")
    s = rep(s, '''    "Kal ka hisaab": "Money & Accounts",
''', '''    "Kal ka hisaab": "Money & Accounts",
    "Medical sale check": "Money & Accounts",
''', "portal section")
    return s


# ---------------------------------------------------------------- tile_grants.json
def build_grants(raw):
    d = json.loads(raw)
    if json.dumps(d, indent=2, ensure_ascii=False) != raw:          # the live file has no trailing newline
        sys.exit("REFUSED: tile_grants.json does not round-trip through json.dumps(indent=2) -- build by hand")
    if d.get("version") != 25:
        sys.exit("REFUSED: tile_grants.json is v%r, expected v25" % d.get("version"))
    ex = d["users"].setdefault("bhati", {}).setdefault("extra", [])
    if "Medical sale check" not in ex:
        ex.append("Medical sale check")
    d["version"] = 26
    d["_note"] += (" | v26 (S400, 25-Sep-2026): the NEW tile 'Medical sale check' (/finance/salecheck) to bhati -- he checks the "
                   "Sanjeevni days not yet approved against Darpan's paper copy and the Marg sheet, and enters the cash Darpan "
                   "handed; the doctor holds it by role. Its gate is a NEW server unit 'salecheck' (bhati holds NO medical row); "
                   "nothing else in this file moves.")
    return json.dumps(d, indent=2, ensure_ascii=False)


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    fin, por, out = a.get("--finance"), a.get("--portal"), a.get("--out")
    if not (fin and por and out):
        print(__doc__)
        return 2
    os.makedirs(out, exist_ok=True)
    built = {
        "finance_app.py": build_finance_app(load(os.path.join(fin, "finance_app.py"), "finance_app.py")),
        "sanjeevni_day.py": build_day(load(os.path.join(fin, "sanjeevni_day.py"), "sanjeevni_day.py")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "finance_approvals.html": build_html(load(os.path.join(fin, "finance_ui", "finance_approvals.html"), "finance_approvals.html")),
        "portal.py": build_portal(load(os.path.join(por, "portal.py"), "portal.py")),
        "tile_grants.json": build_grants(load(os.path.join(por, "tile_grants.json"), "tile_grants.json")),
    }
    for name, text in built.items():
        data = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(data)
        print("%s  %s" % (md5(data), name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
