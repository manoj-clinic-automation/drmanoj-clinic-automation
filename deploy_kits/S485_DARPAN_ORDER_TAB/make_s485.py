#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s485.py -- kit S485_DARPAN_ORDER_TAB (D677).

Six files of /root/finance are BUILT FROM THE LIVE BYTES by anchored edits: each anchor must occur exactly once, else the build stops
and nothing is written. The two blocks added whole are read from this folder (order_api_s485.py -> the end of darpan_kal.py;
order_tab_s485.js -> darpan_kal.html's script). Nothing here opens a database or the network.

    python3 -B make_s485.py --finance /root/finance --out DIR      -> DIR/<the six files>

  darpan_kal.py          the tab's API (GET api/order, POST hold / qty / add / pakka, GET items)
  darpan_kal_schema.sql  the table order_darpan_edit (every tap, one row)
  darpan_kal.html        the tabs become live: कल का हिसाब | आज का ऑर्डर
  order_sheet.py         order.source takes a third value, darpan: reception's cards read the Pakka'd proposals (status darpan_ok)
  order_rules.py         order.darpan_list_time, the 09:30 notice to Darpan, nightly / day_summary / needs-you / send_proposal on darpan
  porders_s454.py        the heading, the setting's validator and the owner's three-way card
"""
import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = "S485_DARPAN_ORDER_TAB"
FROM = {
    "darpan_kal.py": "911cf637a288fad85c75e54227149633",
    "darpan_kal_schema.sql": "ecc6f0c53db4ea7e48bf8e3b1120e6b4",
    "darpan_kal.html": "c20ab05d8484e37a667ddae32a4c792b",
    "order_sheet.py": "a5408df0fac852391d5845c5ae4d8865",
    "order_rules.py": "dac12be4c4a537d7ad2e4584a3423e6a",
    "porders_s454.py": "3681622b11043116f40bc0d4c3b557ad",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rd(p):
    with io.open(p, "rb") as fh:
        return fh.read()


def block(name):
    return rd(os.path.join(HERE, name)).decode("utf-8").replace("\r\n", "\n")


def edit(name, src, pairs):
    """Anchored edits: every OLD must occur exactly once in what the edits before it left."""
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            raise SystemExit("!! %s: anchor %d occurs %d times, not once -- nothing built (%r)" % (name, i, n, old[:70]))
        src = src.replace(old, new)
    return src


# ----------------------------------------------------------------------------------------------------------------------- darpan_kal.py
def build_darpan_kal_py(src):
    tail = ('        return order_sheet.darpan_card(con)\n'
            '    except Exception as e:                                   # noqa: BLE001\n'
            '        return dict(ok=False, error=str(e)[:80])\n')
    if not src.endswith(tail):
        raise SystemExit("!! darpan_kal.py does not end where the brief read it -- nothing built")
    return edit("darpan_kal.py", src, [(tail, tail + block("order_api_s485.py"))])


# --------------------------------------------------------------------------------------------------------------- darpan_kal_schema.sql
def build_schema(src):
    return edit("darpan_kal_schema.sql", src, [
        ("INSERT OR IGNORE INTO setting (key, value) VALUES ('procedure_customer_name', '');\n",
         "INSERT OR IGNORE INTO setting (key, value) VALUES ('procedure_customer_name', '');\n"
         "\n"
         "-- S485 (D677): every tap Darpan makes on \"आज का ऑर्डर\" -- one row: a line held or taken back, a quantity changed, a medicine added,\n"
         "-- a supplier's list made pakka. Nothing reads it in S485 (the audit; K2's three-holds-in-a-row rule reads it later).\n"
         "CREATE TABLE IF NOT EXISTS order_darpan_edit (\n"
         "    id            INTEGER PRIMARY KEY,\n"
         "    day           TEXT NOT NULL,\n"
         "    supplier_norm TEXT NOT NULL,\n"
         "    item          TEXT NOT NULL DEFAULT '',\n"
         "    action        TEXT NOT NULL CHECK (action IN ('hold','unhold','qty','add','pakka')),\n"
         "    qty           INTEGER,\n"
         "    at            TEXT NOT NULL,\n"
         "    by            TEXT NOT NULL\n"
         ");\n"
         "CREATE INDEX IF NOT EXISTS ix_order_darpan_edit_day ON order_darpan_edit(day, supplier_norm);\n"),
    ])


# --------------------------------------------------------------------------------------------------------------------- darpan_kal.html
CSS = (
    " /* S485 (D677): आज का ऑर्डर */\n"
    " .tab{cursor:pointer}\n"
    " #order{padding-bottom:96px}\n"
    " .ohead{margin:6px 2px 10px}\n"
    " details.osup{background:#fff;border:1px solid #e4e0da;border-radius:10px;margin:10px 0;padding:10px 12px}\n"
    " details.osup>summary{color:#1c1c1c;font-size:16px;padding:4px 0;line-height:1.7}\n"
    " .oln{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #eee}\n"
    " .oln.held .oit{opacity:.55}\n"
    " .oit{flex:1;min-width:0;overflow-wrap:anywhere}\n"
    " .oqt{text-align:right;white-space:nowrap}\n"
    " .oq{display:inline-block;min-width:74px;text-align:center;font-size:16px}\n"
    " .btn.pm{min-width:44px;min-height:44px;padding:8px 0;text-align:center;font-size:20px;margin:0 2px;box-sizing:border-box}\n"
    " .btn.sm{padding:11px 10px;font-size:14px;margin:12px 0 0 6px;min-height:44px;box-sizing:border-box}\n"
    " #osheet .row .btn.sm{margin-top:0}\n"
    " .ochips .btn.sm{margin:10px 10px 0 0}\n"
    " .ost{display:inline-block}\n"
    " .opk{width:100%;margin:10px 0 2px;min-height:48px;font-size:17px;box-sizing:border-box}\n"
    " details.oyest{margin:14px 2px}\n"
    " #obar{position:fixed;left:0;right:0;bottom:0;display:none;gap:8px;padding:8px 12px;background:#f6f4f1;border-top:1px solid #ddd;\n"
    "       box-sizing:border-box;max-width:584px;margin:0 auto;z-index:5}\n"
    " #obar .btn{flex:1;text-align:center;min-height:48px;box-sizing:border-box;margin:0;font-size:16px;padding:12px 6px}\n"
    " #msg{z-index:20}\n"
    " body.otab #msg{bottom:66px}\n"
    " #tabs .tab{min-height:44px;box-sizing:border-box;padding:11px 8px}\n"
    " #osheet{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.35);display:none;z-index:10}\n"
    " #osheet .box{position:absolute;left:0;right:0;bottom:0;max-height:86%;overflow:auto;background:#fff;border-radius:14px 14px 0 0;\n"
    "       padding:14px;max-width:560px;margin:0 auto;box-sizing:border-box}\n"
    " .ohit{padding:10px 4px;border-bottom:1px solid #eee;cursor:pointer}\n"
    " .ochips{margin-top:4px}\n"
)


def build_html(src):
    return edit("darpan_kal.html", src, [
        (" a{color:#3c6ac2}\n</style>\n", " a{color:#3c6ac2}\n" + CSS + "</style>\n"),
        (' <div class="tab on" id="tabKal">कल का हिसाब</div>\n'
         ' <div class="tab off" id="tabClaim" title="baad mein">Claim (jaldi)</div>\n'
         '</div>\n'
         '<div id="body">loading…</div>\n'
         '<div id="msg"></div>\n',
         ' <div class="tab on" id="tabKal">कल का हिसाब</div>\n'
         ' <div class="tab" id="tabOrder">आज का ऑर्डर</div>\n'
         ' <div class="tab off" id="tabClaim" title="baad mein">Claim (jaldi)</div>\n'
         '</div>\n'
         '<div id="body">loading…</div>\n'
         '<div id="order" style="display:none"></div>\n'
         '<div id="obar"><span class="btn" id="oaddbtn" onclick="oaddOpen()">+ दवा जोड़ो</span><span class="btn primary" id="oall" onclick="opakkaAll()">सब पक्का</span></div>\n'
         '<div id="osheet" onclick="if(event.target===this)oaddClose()"><div class="box"><div class="row"><b>दवा जोड़ो</b><span class="btn sm" onclick="oaddClose()">बंद करो</span></div>\n'
         ' <input class="big" id="oq" style="text-align:left;font-size:20px" placeholder="नाम के पहले 3 अक्षर" autocomplete="off" autocapitalize="characters" oninput="oaddType()">\n'
         ' <div class="muted">जैसे मार्ग में लिखते हैं</div><div id="ohits"></div></div></div>\n'
         '<div id="msg"></div>\n'),
        # the owner's view keeps the two tabs (he reads Darpan's list; no button is drawn for him there)
        (' document.documentElement.lang="en"; el("ttl").textContent="Darpan — the day"; el("tabs").style.display="none";\n',
         ' document.documentElement.lang="en"; el("ttl").textContent="Darpan — the day"; el("tabClaim").style.display="none"; OWNER_RO=true;   /* S485 */\n'),
        ('\nload();\n</script>\n',
         '\n' + block("order_tab_s485.js") + 'load();\nif(location.hash==="#order") showTab(true);   /* S485: the 09:30 notice lands on the tab */\n</script>\n'),
    ])


# ---------------------------------------------------------------------------------------------------------------------- order_sheet.py
def build_order_sheet(src):
    return edit("order_sheet.py", src, [
        ('    "order.source": ("marg_sheet", "S454 (D666): who decides the order -- marg_sheet (Darpan\'s sheet) or system (the system\'s own list)"),\n',
         '    "order.source": ("marg_sheet", "S454 (D666): who decides the order -- marg_sheet (Darpan\'s sheet), system (the system\'s own list) or, "\n'
         '                                   "S485 (D677), darpan (the system\'s list once Darpan has made it pakka on his own page)"),\n'),
        ('    return v if v in ("marg_sheet", "system") else "marg_sheet"\n',
         '    return v if v in ("marg_sheet", "system", "darpan") else "marg_sheet"\n'),
        ('def _proposals_today(con, t):\n'
         '    """order.source = system: the day\'s proposals that S410\'s rules let go out (the rules approved, not held, not paused)."""\n',
         'def _proposals_today(con, t, status="open"):\n'
         '    """order.source = system: the day\'s proposals that S410\'s rules let go out (the rules approved, not held, not paused).\n'
         '    S485 (D677): order.source = darpan asks for status darpan_ok -- the ones Darpan has made pakka."""\n'),
        ('    for p in con.execute("SELECT * FROM order_proposal WHERE day=? AND status=\'open\' ORDER BY kind DESC, vendor", (t.isoformat(),)):\n',
         '    for p in con.execute("SELECT * FROM order_proposal WHERE day=? AND status=? ORDER BY kind DESC, vendor", (t.isoformat(), status)):\n'),
        ('        for p in _proposals_today(con, t):\n'
         '            if p["supplier_norm"] in drafts:\n'
         '                continue\n'
         '            ed = _edits(con, "proposal", p["id"])\n'
         '            c = card(p["supplier_norm"], p["vendor"])\n'
         '            for l in p["lines"]:\n'
         '                e = ed.get(l["item"]) or {}\n'
         '                if e.get("removed"):\n'
         '                    continue\n',
         '        for p in _proposals_today(con, t, "darpan_ok" if source(con) == "darpan" else "open"):   # S485 (D677)\n'
         '            if p["supplier_norm"] in drafts:\n'
         '                continue\n'
         '            ed = _edits(con, "proposal", p["id"])\n'
         '            c = card(p["supplier_norm"], p["vendor"])\n'
         '            for l in p["lines"]:\n'
         '                e = ed.get(l["item"]) or {}\n'
         '                if e.get("removed") or l.get("held"):             # S485: a line Darpan held ("is baar nahi") is not on the card\n'
         '                    continue\n'),
        ("            con.execute(\"UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=? WHERE id=? AND status IN ('open','held')\",\n",
         "            con.execute(\"UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=? WHERE id=? AND status IN ('open','held','darpan_ok')\",\n"),
    ])


# ---------------------------------------------------------------------------------------------------------------------- order_rules.py
RULES_HELPERS = '''def darpan_list_time(con):
    """S485 (D677): order.darpan_list_time as HH:MM -- a ':x0' minute, because the tick runs every ten minutes and matches the minute
    exactly; anything else reads as 09:30."""
    v = str(_setting(con, "order.darpan_list_time") or "").strip()
    return v if re.match(r"^([01]\\d|2[0-3]):[0-5]0$", v) else "09:30"


def darpan_list_open(con, now=None):
    """S485: has the day's list opened on Darpan's tab? (ORDER_CLOCK = HH:MM is a walk's clock.)"""
    hm = os.environ.get("ORDER_CLOCK", "") or (now or dt.datetime.now()).strftime("%H:%M")
    return hm >= darpan_list_time(con)


def _s485_notice(con, today):
    """S485 (D677): the one notice of the list's hour, to Darpan only, once a day (order_notice UNIQUE(day, slot)); silent unless
    order.source = darpan and a proposal of today is open."""
    src = _s454_source(con)
    if src != "darpan":
        return dict(ok=True, silent=True, slot="0930", why="order.source = %s" % src)
    n = sum(1 for p in con.execute("SELECT supplier_norm FROM order_proposal WHERE day=? AND status='open'", (today.isoformat(),)).fetchall()
            if not int(rule_for(con, p[0]).get("paused") or 0))
    if not n or _frozen(con):
        return dict(ok=True, silent=True, slot="0930", why="no open proposal")
    to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip().lower() == "darpan"]
    return send_notice(con, today, "0930", to=to, text="\\u0906\\u091c \\u0915\\u093e \\u0911\\u0930\\u094d\\u0921\\u0930 \\u0924\\u0948\\u092f\\u093e\\u0930 \\u0939\\u0948 \\u2014 "
                       "\\u0915\\u0932 \\u0915\\u093e \\u0939\\u093f\\u0938\\u093e\\u092c \\u092a\\u0947\\u091c \\u092a\\u0930 \\u0926\\u0947\\u0916\\u093f\\u090f",
                       url="/finance/darpan/kal#order", title="\\u0906\\u091c \\u0915\\u093e \\u0911\\u0930\\u094d\\u0921\\u0930")


'''


def build_order_rules(src):
    return edit("order_rules.py", src, [
        # (a) the setting
        ('    "order.freeze": ("", "json {by, at, reason} while all medicine ordering is frozen"),\n}\n',
         '    "order.freeze": ("", "json {by, at, reason} while all medicine ordering is frozen"),\n'
         '    "order.darpan_list_time": ("09:30", "S485 (D677): the list opens on Darpan\'s tab at this time (HH:M0); the proposals are prepared at 09:00 as before"),\n}\n'),
        # (c) nightly: a list Darpan made pakka that reception did not order rides on like an open one
        ('    for p in con.execute("SELECT id, supplier_norm, day FROM order_proposal WHERE status=\'open\' AND day<?", (today.isoformat(),)).fetchall():\n',
         '    for p in con.execute("SELECT id, supplier_norm, day FROM order_proposal WHERE status IN (\'open\',\'darpan_ok\') AND day<?", (today.isoformat(),)).fetchall():   # S485\n'),
        # (d) Darpan's count line on darpan
        ('        d = day_state(con)\n'
         '        return dict(ok=True, n=d["n"], sent=d["sent"], unsent=d["unsent"], text=d["text"], frozen=bool(d["frozen"]), url=d["url"])\n',
         '        d = day_state(con)\n'
         '        if _s454_source(con) == "darpan":                     # S485 (D677): open (his to make pakka) and darpan_ok (reception\'s to order) both still to go\n'
         '            rows = [r for r in d["proposals"] if r["status"] in ("open", "darpan_ok", "sent")]\n'
         '            un = [r for r in rows if r["status"] != "sent"]\n'
         '            text = (("Aaj %d order: %d bheja, %d baaki — %s" % (len(rows), len(rows) - len(un), len(un), ", ".join(r["short"] for r in un))) if un\n'
         '                    else ("Aaj ke %d order sab bheje ja chuke." % len(rows) if rows else ""))\n'
         '            return dict(ok=True, n=len(rows), sent=len(rows) - len(un), unsent=len(un), text=text, frozen=bool(d["frozen"]), url=d["url"])\n'
         '        return dict(ok=True, n=d["n"], sent=d["sent"], unsent=d["unsent"], text=d["text"], frozen=bool(d["frozen"]), url=d["url"])\n'),
        # (b) send_notice: to / text / url / title may be given (the 09:30 notice goes to Darpan only, with its own words)
        ('def send_notice(con, today, slot, who="cron"):\n',
         'def send_notice(con, today, slot, who="cron", to=None, text=None, url=None, title=None):\n'),
        ('    text = notice_text(con, today, "prepare" if slot == "prepare" else "remind")\n',
         '    text = text or notice_text(con, today, "prepare" if slot == "prepare" else "remind")\n'),
        ('        return dict(ok=True, silent=True, slot=key)\n'
         '    to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip()]\n'
         '    payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True, ts=int(dt.datetime.now().timestamp() * 1000))\n',
         '        return dict(ok=True, silent=True, slot=key)\n'
         '    if to is None:\n'
         '        to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip()]\n'
         '    payload = dict(kind="order", title=title or "Purchase orders", body=text, url=url or "/finance/porders", tag="porders", ttl=3600, renotify=True, ts=int(dt.datetime.now().timestamp() * 1000))\n'),
        # (b) the helpers, above tick; the slot; the 0900 slot's own word for the source
        ('def tick(con, now=None):\n', RULES_HELPERS + 'def tick(con, now=None):\n'),
        ('        elif hm == SLOTS["prepare"]:\n'
         '            slot = "prepare"\n',
         '        elif hm == SLOTS["prepare"]:\n'
         '            slot = "prepare"\n'
         '        elif "%02d:%02d" % hm == darpan_list_time(con):       # S485 (D677): the list opens on Darpan\'s tab\n'
         '            slot = "0930"\n'),
        ('                                                              else dict(ok=True, silent=True, slot="0900", why="order.source = marg_sheet")))\n',
         '                                                              else dict(ok=True, silent=True, slot="0900", why="order.source = %s" % _s454_source(con))))\n'
         '    if slot == "0930":                                        # S485 (D677)\n'
         '        return dict(slot=slot, s454=s454, notice=_s485_notice(con, today))\n'),
        # (f) send_proposal: a darpan_ok proposal may be sent the old way too; a held line is never sent
        ('    if p["status"] not in ("open", "held"):\n',
         '    if p["status"] not in ("open", "held", "darpan_ok"):       # S485\n'),
        ('        base = {l["item"]: l for l in json.loads(p["lines"] or "[]")}\n',
         '        base = {l["item"]: l for l in json.loads(p["lines"] or "[]") if not l.get("held")}   # S485: both loops below skip a held line\n'),
        # (e) the owner's "Order not sent" line runs on darpan as on system
        ('                              (today.isoformat(),)) if _s454_source(con) == "system" else ()):    # S454: on marg_sheet the proposals reach no one\n',
         '                              (today.isoformat(),)) if _s454_source(con) in ("system", "darpan") else ()):    # S454: on marg_sheet the proposals reach no one (S485: darpan as system)\n'),
    ])


# --------------------------------------------------------------------------------------------------------------------- porders_s454.py
def build_porders(src):
    return edit("porders_s454.py", src, [
        ('    elif src == "system":\n'
         '        h.append(\'<div class="mut" id="whose">%s</div>\' % esc(L(en, "whose", L(en, "system"), OS.today().strftime("%d-%m"), len(es), sum(len(e["lines"]) for e in es))))\n',
         '    elif src == "system":\n'
         '        h.append(\'<div class="mut" id="whose">%s</div>\' % esc(L(en, "whose", L(en, "system"), OS.today().strftime("%d-%m"), len(es), sum(len(e["lines"]) for e in es))))\n'
         '    elif src == "darpan":                                     # S485 (D677): the system\'s list, as Darpan made it pakka on his page\n'
         '        h.append(\'<div class="mut" id="whose">%s</div>\' % esc(re.sub(r"(?<![\\d,])1 (medicine|supplier)s\\b", r"1 \\1",\n'
         '                 ("Darpan\'s confirmed list · %s · %d suppliers, %d medicines" if en else "Darpan ki pakki list · %s · %d supplier, %d dawa")\n'
         '                 % (OS.today().strftime("%d-%m"), len(es), sum(len(e["lines"]) for e in es)))))\n'),
        ('        return v in ("marg_sheet", "system"), v\n',
         '        return v in ("marg_sheet", "system", "darpan"), v       # S485 (D677)\n'),
        ('    h.append(\'<div %s id="s454src"><b>Who decides the order</b> · %s <button onclick="s454set(\\\'order.source\\\',\\\'%s\\\')" style="min-height:40px">%s</button>\'\n'
         '             \'<div style="color:#666;font-size:13px">%s</div></div>\'\n'
         '             % (st, "Darpan\'s Marg order sheet" if src == "marg_sheet" else "The system\'s own list", "system" if src == "marg_sheet" else "marg_sheet",\n'
         '                "Change to the system\'s own list" if src == "marg_sheet" else "Change to Darpan\'s sheet",\n'
         '                "The system\'s own list is worked out every order day but is shown to no staff." if src == "marg_sheet" else\n'
         '                "Darpan\'s sheet, when one arrives, is compared and shown to you only."))\n',
         '    s485 = {"marg_sheet": ("Darpan\'s Marg order sheet", "Change to Darpan\'s sheet",\n'
         '                           "The system\'s own list is worked out every order day but is shown to no staff."),\n'
         '            "system": ("The system\'s own list", "Change to the system\'s own list",\n'
         '                       "Darpan\'s sheet, when one arrives, is compared and shown to you only."),\n'
         '            "darpan": ("The system\'s list, confirmed by Darpan on his page", "Change to Darpan confirming the system\'s list",\n'
         '                       "Darpan sees the system\'s list on his own page from the list time and taps Pakka; reception orders what he confirmed. "\n'
         '                       "His Marg sheet, when one arrives, is compared and shown to you only.")}   # S485 (D677): three values, one tap to any other\n'
         '    h.append(\'<div %s id="s454src"><b>Who decides the order</b> · %s %s<div style="color:#666;font-size:13px">%s</div></div>\'\n'
         '             % (st, s485[src][0], "".join(\'<button onclick="s454set(\\\'order.source\\\',\\\'%s\\\')" style="min-height:40px">%s</button> \' % (k, s485[k][1])\n'
         '                                          for k in ("marg_sheet", "system", "darpan") if k != src), s485[src][2]))\n'),
    ])


BUILDERS = (("darpan_kal.py", build_darpan_kal_py), ("darpan_kal_schema.sql", build_schema), ("darpan_kal.html", build_html),
            ("order_sheet.py", build_order_sheet), ("order_rules.py", build_order_rules), ("porders_s454.py", build_porders))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = []
    for name, fn in BUILDERS:                                 # every pin and every anchor first ...
        raw = rd(os.path.join(a.finance, name))
        if md5(raw) != FROM[name]:
            raise SystemExit("!! %s is %s, not its FROM pin %s -- someone changed it since the brief; nothing built" % (name, md5(raw), FROM[name]))
        built.append((name, fn(raw.decode("utf-8")).encode("utf-8")))
    os.makedirs(a.out, exist_ok=True)
    for name, out in built:                                   # ... then the writes
        with io.open(os.path.join(a.out, name), "wb") as fh:
            fh.write(out)
        print("built %-22s %s -> %s  (%d bytes)" % (name, FROM[name][:8], md5(out)[:8], len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
