#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""owner_sheets.py -- S316 (18-Sep-2026), over S315. The owner's own two lists, on a page he can work:
the X-RAY INVENTORY and the PROCEDURE -> CONSUMABLES map (D546).

WHAT CHANGED AT S316, IN HIS WORDS. "The form you made me fill is not the proper one -- extract the
X-rays from the excel sheet, remove the X-ray word from the item name, do your own spelling
corrections, make a list of the various X-rays you find, and then I will only edit those or approve
those or reject those or maybe add some. Same for procedures -- I have shared a list with you
previously. No backfill; future work is what matters."

So nothing here asks him to fill a blank page. Both lists arrive ALREADY WRITTEN and every line waits
for one tap -- approve, or reject, or a corrected name:
  * THE X-RAYS come from `xray_seed.json`, which is the S223 extraction of the clinic's OWN
    "X-RAY DETAIL RAGISTER" -- 6,177 entries, 1,197 distinct typed forms, reduced to 19 studies in
    frequency order, spellings corrected (SHUOLDER/SHOLDER/SHOUKDER -> SHOULDER, CARVICAL ->
    CERVICAL, SPAINE -> SPINE, ELWOB -> ELBOW, CLAVICAL -> CLAVICLE, FORAM -> FOREARM), the word
    X-RAY itself dropped, and PROSISER taken out because he ruled it a PROCEDURE, not an X-ray.
  * THE PROCEDURES come from `proc_seed.json`, which is his own ruling of 04-Sep-2026: the eleven
    cast/slab sites (U slab may be a cast too; the clavicle bandage is neither), the five ILI sites,
    and dressing -- with the consumables exactly as he ruled them (size x quantity where he asked for
    dropdowns, stockinette used/not-used only, Loftypred OR Viracort, the D600 drape selectable).
NO BACKFILL. Past rows are never loaded as history; this is a list for the work that comes next.

WHY IT EXISTS. The chamber screen S267 designed fills a price by itself and, later, takes the
consumables off stock. Neither list exists anywhere in the system: Docterz's day lines carry a
section (consult / xray / proc) and an amount, never the name of the X-ray or the procedure. The
owner was asked for "one sheet, your words" -- this is that sheet, on the portal instead of on paper,
so nothing has to be typed twice and the chamber screen reads it directly.

WHAT IT SHOWS HIM, AND WHERE THE SEED COMES FROM
  * Every distinct amount actually billed under X-ray and under procedures in the last 180 days,
    with how many times and when it was last seen -- read from clinic_day_line, the store, not a page.
    He puts a name against an amount; the row is then a price-list line.
  * The consumables he can tap: the pharmacy's own item master. stock_item_section (S313) when it is
    there -- Consumables first, then the rest -- else the newest stock_snapshot. Read-only: this page
    never writes a pharmacy table.

WHAT IT WRITES. Two tables of its own in finance.db, created on first request (F-303):
    owner_service        one row per X-ray or procedure: name, price, active, who set it and when
    owner_service_item   the consumables of a procedure: item, quantity, unit, note
Nothing else is touched. No money, no ledger, no stock.

WHO. The doctor only: the clinic unit's checker AND a name in OWNER_SHEET_USERS (default manoj).
Reception and the staff never see it; the tile is doctor-only too.

THE READ-BACK DOOR. /finance/clinic/sheets/api/services returns both lists as JSON for the chamber
screen that comes next -- one authored source, no second copy.

Flask and the standard library only. No patient name, no number, no secret (F-185).
"""
import datetime as dt
import json
import os

from flask import Blueprint, jsonify, redirect, request

bp = Blueprint("owner_sheets", __name__)

_db = None
_require = None
_audit = None
UNIT = "clinic"
OWNERS = tuple(x.strip().lower() for x in
               os.environ.get("OWNER_SHEET_USERS", "manoj").split(",") if x.strip())
SEED_DAYS = int(os.environ.get("OWNER_SHEET_SEED_DAYS", "180"))
KINDS = (("xray", "X-ray"), ("proc", "Procedure"))
KIND_OF = dict(KINDS)

SCHEMA = """
CREATE TABLE IF NOT EXISTS owner_service (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  kind       TEXT    NOT NULL,                 -- xray | proc
  name       TEXT    NOT NULL,
  price_p    INTEGER NOT NULL DEFAULT 0,
  active     INTEGER NOT NULL DEFAULT 1,
  code       TEXT    NOT NULL DEFAULT '',      -- S316: the seed's own code (KNEE, LS, AK, ILI-HE ...)
  status     TEXT    NOT NULL DEFAULT 'pending',  -- pending | approved | rejected (his tap)
  seen       INTEGER NOT NULL DEFAULT 0,       -- how often the register carried it (evidence, not a figure to use)
  grp        TEXT    NOT NULL DEFAULT '',      -- Cast / slab · Injection (ILI) · Dressing
  forms      TEXT    NOT NULL DEFAULT '',      -- cast,slab -- what the chamber screen may offer
  source     TEXT    NOT NULL DEFAULT '',      -- register-S223 | ruling-S225 | owner
  note       TEXT    NOT NULL DEFAULT '',
  created_by TEXT    NOT NULL DEFAULT '',
  created_ts TEXT    NOT NULL DEFAULT '',
  updated_by TEXT    NOT NULL DEFAULT '',
  updated_ts TEXT    NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_owner_service ON owner_service(kind, name);

CREATE TABLE IF NOT EXISTS owner_service_item (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  service_id INTEGER NOT NULL REFERENCES owner_service(id),
  item       TEXT    NOT NULL,
  qty        REAL    NOT NULL DEFAULT 1,
  unit       TEXT    NOT NULL DEFAULT '',
  ask        TEXT    NOT NULL DEFAULT '',      -- S316: size_qty | used_yesno | one_of | selectable
  sizes      TEXT    NOT NULL DEFAULT '',
  note       TEXT    NOT NULL DEFAULT '',
  added_by   TEXT    NOT NULL DEFAULT '',
  added_ts   TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_owner_service_item ON owner_service_item(service_id);
"""

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def _now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return dt.datetime.now(IST).date()


def init(app, db_getter, require_fn, audit_fn=None, unit="clinic",
         url_prefix="/finance/clinic/sheets"):
    """Mounted by finance_app inside the CLINIC namespace, so the front gate's
    _unit_for_path already resolves this page to the clinic unit -- no change to
    the gate, and a login with no clinic role never reaches a route here."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)


NEW_COLS = (("owner_service", "code", "TEXT NOT NULL DEFAULT ''"),
            ("owner_service", "status", "TEXT NOT NULL DEFAULT 'pending'"),
            ("owner_service", "seen", "INTEGER NOT NULL DEFAULT 0"),
            ("owner_service", "grp", "TEXT NOT NULL DEFAULT ''"),
            ("owner_service", "forms", "TEXT NOT NULL DEFAULT ''"),
            ("owner_service", "source", "TEXT NOT NULL DEFAULT ''"),
            ("owner_service_item", "ask", "TEXT NOT NULL DEFAULT ''"),
            ("owner_service_item", "sizes", "TEXT NOT NULL DEFAULT ''"))


def ensure(con):
    """Idempotent, and safe over an S315 table that has none of the S316 columns:
    the table is created if absent, then each new column is added if missing, then the
    two seed files are loaded ONCE (a row already there is never overwritten)."""
    con.executescript(SCHEMA)
    for table, col, decl in NEW_COLS:
        have = [r[1] for r in con.execute("PRAGMA table_info(%s)" % table)]
        if col not in have:
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, decl))
    con.commit()
    seed(con)


SEED_DIR = os.environ.get("OWNER_SHEET_SEED_DIR", os.path.dirname(os.path.abspath(__file__)))


def _seed_file(name):
    path = os.path.join(SEED_DIR, name)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                   # noqa: BLE001 -- a missing seed is not a fault
        return None


def seed(con):
    """Load the two lists the FIRST time only. Keyed on (kind, code): a row he has already
    touched -- renamed, priced, approved or rejected -- is never written over, and nothing
    is ever deleted here. Returns how many rows were added."""
    added = 0
    x = _seed_file("xray_seed.json")
    if x:
        for st in x.get("studies", []):
            if con.execute("SELECT 1 FROM owner_service WHERE kind='xray' AND code=?",
                           (st["code"],)).fetchone():
                continue
            con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,seen,grp,source,"
                        "created_by,created_ts,updated_by,updated_ts) "
                        "VALUES ('xray',?,0,?,'pending',?,'X-ray','register-S223','seed',?,'seed',?)",
                        (st["label"], st["code"], int(st.get("seen", 0)), _now(), _now()))
            added += 1
    p = _seed_file("proc_seed.json")
    if p:
        items = p.get("items", {})
        for pr in p.get("procedures", []):
            row = con.execute("SELECT id FROM owner_service WHERE kind='proc' AND code=?",
                              (pr["code"],)).fetchone()
            if row:
                continue
            cur = con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,grp,forms,source,"
                              "created_by,created_ts,updated_by,updated_ts) "
                              "VALUES ('proc',?,0,?,'pending',?,?,'ruling-S225','seed',?,'seed',?)",
                              (pr["label"], pr["code"], pr.get("group", ""),
                               ",".join(pr.get("forms", [])), _now(), _now()))
            sid = cur.lastrowid
            added += 1
            for key in pr.get("items", []):
                it = items.get(key)
                if not it:
                    continue
                con.execute("INSERT INTO owner_service_item (service_id,item,qty,unit,ask,sizes,"
                            "added_by,added_ts) VALUES (?,?,?,'',?,?,'seed',?)",
                            (sid, it["label"], 1, it.get("ask", ""), ",".join(it.get("sizes", [])), _now()))
    con.commit()
    return added


def _owner():
    """(user, None) for the doctor; (None, response) for anyone else. Two gates:
    the clinic unit's checker role, then the name allow-list."""
    u, err = _require("checker", unit=UNIT)
    if err:
        return None, err
    name = (u if isinstance(u, str) else (u or {}).get("user", "")).strip().lower()
    if name not in OWNERS:
        return None, (jsonify(ok=False, error="not_the_owner",
                              message="These two sheets are the doctor's own."), 403)
    return name, None


def rupees(p):
    return "%s" % ("{:,}".format(int(round(p / 100.0))))


def _paise(text):
    """'500' or '500.50' or '₹1,500' -> paise. Refuses anything else."""
    s = (text or "").strip().replace(",", "").replace("₹", "").replace("Rs", "").replace("rs", "")
    if not s:
        raise ValueError("a price is needed")
    v = float(s)
    if v < 0 or v > 1000000:
        raise ValueError("that price looks wrong")
    return int(round(v * 100))


# ---------------------------------------------------------------- the seed
def billed_amounts(con, kind, days=None):
    """Every distinct amount actually billed under this section, newest activity
    first. READ from clinic_day_line -- the store Docterz's own export lands in."""
    days = SEED_DAYS if days is None else days
    since = (_today() - dt.timedelta(days=days)).isoformat()
    rows = []
    try:
        for r in con.execute(
                "SELECT amount_p, COUNT(*) AS times, MAX(business_date) AS last_seen "
                "FROM clinic_day_line WHERE section=? AND business_date>=? AND amount_p>0 "
                "GROUP BY amount_p ORDER BY times DESC, amount_p", (kind, since)):
            rows.append({"amount_p": r["amount_p"], "amount": rupees(r["amount_p"]),
                         "times": r["times"], "last_seen": r["last_seen"]})
    except Exception:                                   # noqa: BLE001 -- no Docterz rows yet
        return []
    return rows


def consumable_items(con, limit=400):
    """The pharmacy's own item master, read-only. stock_item_section (S313) when
    it exists -- Consumables first -- else the newest stock_snapshot."""
    out, seen = [], set()
    try:
        for r in con.execute("SELECT item, section FROM stock_item_section "
                             "ORDER BY CASE WHEN LOWER(section)='consumables' THEN 0 ELSE 1 END, item"):
            if r["item"] not in seen:
                seen.add(r["item"])
                out.append({"item": r["item"], "section": r["section"]})
    except Exception:                                   # noqa: BLE001
        pass
    if not out:
        try:
            as_on = con.execute("SELECT MAX(as_on) AS a FROM stock_snapshot").fetchone()["a"]
            if as_on:
                for r in con.execute("SELECT item FROM stock_snapshot WHERE as_on=? ORDER BY item",
                                     (as_on,)):
                    if r["item"] not in seen:
                        seen.add(r["item"])
                        out.append({"item": r["item"], "section": ""})
        except Exception:                               # noqa: BLE001
            pass
    return out[:limit]


# ---------------------------------------------------------------- the sheets
def services(con, kind=None):
    ensure(con)
    where, args = ("WHERE kind=?", (kind,)) if kind else ("", ())
    rows = []
    for r in con.execute("SELECT * FROM owner_service %s ORDER BY kind, "
                         "CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, "
                         "seen DESC, name" % where, args):
        items = [dict(id=i["id"], item=i["item"], qty=i["qty"], unit=i["unit"], note=i["note"],
                      ask=i["ask"], sizes=i["sizes"])
                 for i in con.execute("SELECT * FROM owner_service_item WHERE service_id=? ORDER BY item",
                                      (r["id"],))]
        rows.append({"id": r["id"], "kind": r["kind"], "name": r["name"],
                     "price_p": r["price_p"], "price": rupees(r["price_p"]),
                     "active": bool(r["active"]), "note": r["note"],
                     "code": r["code"], "status": r["status"], "seen": r["seen"],
                     "grp": r["grp"], "forms": r["forms"], "source": r["source"],
                     "updated_by": r["updated_by"], "updated_ts": r["updated_ts"],
                     "items": items})
    return rows


def add_service(con, who, kind, name, price_text, note=""):
    ensure(con)
    kind = (kind or "").strip().lower()
    if kind not in KIND_OF:
        raise ValueError("X-ray or procedure -- nothing else")
    name = " ".join((name or "").split())[:80]
    if not name:
        raise ValueError("a name is needed")
    price_p = _paise(price_text) if (price_text or "").strip() else 0
    dup = con.execute("SELECT id FROM owner_service WHERE kind=? AND LOWER(name)=LOWER(?)",
                      (kind, name)).fetchone()
    if dup:
        raise ValueError("%s is already on the list" % name)
    cur = con.execute("INSERT INTO owner_service (kind,name,price_p,note,status,source,grp,"
                      "created_by,created_ts,updated_by,updated_ts) "
                      "VALUES (?,?,?,?,'approved','owner',?,?,?,?,?)",
                      (kind, name, price_p, (note or "").strip()[:200],
                       "X-ray" if kind == "xray" else "", who, _now(), who, _now()))
    con.commit()
    if _audit:
        try:
            _audit("owner_service", str(cur.lastrowid), "add", "", "%s %s %d" % (kind, name, price_p), who)
        except Exception:                               # noqa: BLE001
            pass
    return cur.lastrowid


def set_price(con, who, sid, price_text):
    ensure(con)
    price_p = _paise(price_text)
    r = con.execute("SELECT price_p FROM owner_service WHERE id=?", (sid,)).fetchone()
    if not r:
        raise ValueError("no such line")
    con.execute("UPDATE owner_service SET price_p=?, updated_by=?, updated_ts=? WHERE id=?",
                (price_p, who, _now(), sid))
    con.commit()
    if _audit:
        try:
            _audit("owner_service", str(sid), "price", str(r["price_p"]), str(price_p), who)
        except Exception:                               # noqa: BLE001
            pass
    return price_p


def set_active(con, who, sid, on):
    ensure(con)
    con.execute("UPDATE owner_service SET active=?, updated_by=?, updated_ts=? WHERE id=?",
                (1 if on else 0, who, _now(), sid))
    con.commit()


def set_status(con, who, sid, status):
    """His tap: approved or rejected. Nothing is deleted -- a rejected line stays,
    greyed, and can be brought back, because 'rejected' is itself an answer."""
    ensure(con)
    if status not in ("approved", "rejected", "pending"):
        raise ValueError("approve or reject -- nothing else")
    r = con.execute("SELECT status FROM owner_service WHERE id=?", (sid,)).fetchone()
    if not r:
        raise ValueError("no such line")
    con.execute("UPDATE owner_service SET status=?, updated_by=?, updated_ts=? WHERE id=?",
                (status, who, _now(), sid))
    con.commit()
    if _audit:
        try:
            _audit("owner_service", str(sid), "status", r["status"], status, who)
        except Exception:                               # noqa: BLE001
            pass
    return status


def rename(con, who, sid, name):
    ensure(con)
    name = " ".join((name or "").split())[:80]
    if not name:
        raise ValueError("a name is needed")
    r = con.execute("SELECT kind, name FROM owner_service WHERE id=?", (sid,)).fetchone()
    if not r:
        raise ValueError("no such line")
    if con.execute("SELECT id FROM owner_service WHERE kind=? AND LOWER(name)=LOWER(?) AND id<>?",
                   (r["kind"], name, sid)).fetchone():
        raise ValueError("%s is already on the list" % name)
    con.execute("UPDATE owner_service SET name=?, updated_by=?, updated_ts=? WHERE id=?",
                (name, who, _now(), sid))
    con.commit()
    if _audit:
        try:
            _audit("owner_service", str(sid), "rename", r["name"], name, who)
        except Exception:                               # noqa: BLE001
            pass
    return name


def counts(con, kind):
    ensure(con)
    out = {"pending": 0, "approved": 0, "rejected": 0}
    for r in con.execute("SELECT status, COUNT(*) AS n FROM owner_service WHERE kind=? GROUP BY status",
                         (kind,)):
        out[r["status"]] = r["n"]
    return out


def add_item(con, who, sid, item, qty_text="1", unit="", note=""):
    ensure(con)
    s = con.execute("SELECT kind FROM owner_service WHERE id=?", (sid,)).fetchone()
    if not s:
        raise ValueError("no such line")
    if s["kind"] != "proc":
        raise ValueError("consumables belong to a procedure, not to an X-ray")
    item = " ".join((item or "").split())[:100]
    if not item:
        raise ValueError("pick an item")
    try:
        qty = float((qty_text or "1").strip())
    except ValueError:
        raise ValueError("the quantity is a number")
    if qty <= 0 or qty > 1000:
        raise ValueError("that quantity looks wrong")
    if con.execute("SELECT id FROM owner_service_item WHERE service_id=? AND LOWER(item)=LOWER(?)",
                   (sid, item)).fetchone():
        raise ValueError("%s is already on this procedure" % item)
    cur = con.execute("INSERT INTO owner_service_item (service_id,item,qty,unit,note,added_by,added_ts) "
                      "VALUES (?,?,?,?,?,?,?)",
                      (sid, item, qty, (unit or "").strip()[:20], (note or "").strip()[:200], who, _now()))
    con.commit()
    return cur.lastrowid


def drop_item(con, who, iid):
    ensure(con)
    con.execute("DELETE FROM owner_service_item WHERE id=?", (iid,))
    con.commit()


def unnamed(con, kind):
    """The seed amounts that still carry no name -- what is left for him to do."""
    have = {r["price_p"] for r in con.execute("SELECT price_p FROM owner_service WHERE kind=?", (kind,))}
    return [a for a in billed_amounts(con, kind) if a["amount_p"] not in have]


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _shell(body, msg="", cls="ok"):
    note = ("<div class='%s'>%s</div>" % (cls, _esc(msg))) if msg else ""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>X-rays &amp; procedures</title><style>
body{margin:0;padding:14px;background:#dfe5e9;color:#14181c;font:17px/1.55 "Segoe UI",system-ui,sans-serif}
h1{font-size:22px;color:#14456e;margin:0 0 4px}h2{font-size:19px;color:#14456e;margin:0 0 8px}
h3{font-size:17px;margin:14px 0 6px}
.card{background:#fffdf7;border:2px solid #8a9aa6;border-radius:10px;padding:14px;margin:0 0 14px;overflow-x:auto}
.mut{color:#3c464e;font-size:15px}
.ok{background:#e6f4ea;border-left:6px solid #2f7d5c;padding:10px 14px;margin-bottom:12px}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:10px 14px;margin-bottom:12px}
table.grid{width:100%%;border-collapse:collapse;margin-top:6px}
.grid th,.grid td{border:1px solid #8a9aa6;padding:8px;vertical-align:middle;text-align:left}
.grid th{background:#eef2f5;font-size:15px}
input,select{font:16px "Segoe UI",system-ui,sans-serif;padding:8px;border:1px solid #8a9aa6;border-radius:7px;background:#fff}
input.name{min-width:190px}input.q{width:70px}input.p{width:100px}
button{font:16px "Segoe UI",system-ui,sans-serif;padding:8px 14px;border:0;border-radius:8px;background:#14456e;color:#fff;cursor:pointer}
button.lite{background:#eef2f5;color:#14456e;border:1px solid #8a9aa6}
form.inline{display:inline-flex;gap:6px;align-items:center;margin:0}
.items{margin:4px 0 0;padding-left:18px;font-size:15px}
.tag{font-size:13px;color:#3c464e}
tr.off td{opacity:.45}
td.grp{background:#eef2f5;font-weight:600;color:#14456e}
.yes{color:#2f7d5c;font-weight:600}.no{color:#9c2a20;font-weight:600}
</style></head><body><h1>X-rays &amp; procedures</h1>
<p class="mut">Both lists are already written. Approve, correct a name, reject, or add one —
the chamber screen reads what you approve.</p>
%s%s<p class="mut"><a href="/portal">&larr; Portal</a></p></body></html>""" % (note, body)


def _rows_html(kind, rows):
    """One line per study or procedure, his three taps on the right. A rejected line is greyed
    and keeps a way back -- nothing he has said 'no' to is deleted."""
    if not rows:
        return "<p class='mut'>Nothing on this list yet.</p>"
    out = ["<table class='grid'><tr><th>%s</th><th>Price</th><th>%s</th><th>Your call</th></tr>"
           % ("X-ray" if kind == "xray" else "Procedure",
              "Seen in the register" if kind == "xray" else "Consumables, as you ruled them")]
    last_grp = None
    for s_ in rows:
        if kind == "proc" and s_["grp"] and s_["grp"] != last_grp:
            last_grp = s_["grp"]
            out.append("<tr><td colspan='4' class='grp'>%s</td></tr>" % _esc(last_grp))
        cls = " class='off'" if s_["status"] == "rejected" else ""
        name = ("<form class='inline' method='post' action='rename'>"
                "<input type='hidden' name='id' value='%d'>"
                "<input class='name' name='name' value='%s'>"
                "<button class='lite' type='submit'>rename</button></form>" % (s_["id"], _esc(s_["name"])))
        price = ("<form class='inline' method='post' action='price'>"
                 "<input type='hidden' name='id' value='%d'>"
                 "<input class='p' name='price' value='%s' inputmode='decimal' placeholder='\u2014'>"
                 "<button class='lite' type='submit'>save</button></form>"
                 % (s_["id"], s_["price"] if s_["price_p"] else ""))
        if kind == "xray":
            third = ("<span class='tag'>%s%s</span>"
                     % (("%d times" % s_["seen"]) if s_["seen"] else "not in the register",
                        (" &middot; " + _esc(s_["code"])) if s_["code"] else ""))
        else:
            lis = "".join(
                "<li>%s%s <form class='inline' method='post' action='item/drop'>"
                "<input type='hidden' name='id' value='%d'><button class='lite' type='submit'>remove</button>"
                "</form></li>" % (_esc(i["item"]), _ask_text(i), i["id"]) for i in s_["items"]) \
                or "<li class='mut'>nothing tracked</li>"
            pick = ("<form class='inline' method='post' action='item/add' style='margin-top:6px'>"
                    "<input type='hidden' name='id' value='%d'>"
                    "<input class='name' name='item' list='items' placeholder='add an item' required>"
                    "<input class='q' name='qty' value='1' inputmode='decimal'>"
                    "<button type='submit'>Add</button></form>" % s_["id"])
            forms = (" <span class='tag'>%s</span>" % _esc(s_["forms"].replace(",", " or "))) \
                if s_["forms"] else ""
            third = "%s<ul class='items'>%s</ul>%s" % (forms, lis, pick)
        if s_["status"] == "approved":
            call = ("<span class='yes'>approved</span> "
                    "<form class='inline' method='post' action='status'>"
                    "<input type='hidden' name='id' value='%d'><input type='hidden' name='s' value='rejected'>"
                    "<button class='lite' type='submit'>reject</button></form>" % s_["id"])
        elif s_["status"] == "rejected":
            call = ("<span class='no'>rejected</span> "
                    "<form class='inline' method='post' action='status'>"
                    "<input type='hidden' name='id' value='%d'><input type='hidden' name='s' value='approved'>"
                    "<button class='lite' type='submit'>bring back</button></form>" % s_["id"])
        else:
            call = ("<form class='inline' method='post' action='status'>"
                    "<input type='hidden' name='id' value='%d'><input type='hidden' name='s' value='approved'>"
                    "<button type='submit'>Approve</button></form> "
                    "<form class='inline' method='post' action='status'>"
                    "<input type='hidden' name='id' value='%d'><input type='hidden' name='s' value='rejected'>"
                    "<button class='lite' type='submit'>Reject</button></form>" % (s_["id"], s_["id"]))
        out.append("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (cls, name, price, third, call))
    out.append("</table>")
    return "".join(out)


_ASK = {"size_qty": "size &times; quantity, each time",
        "used_yesno": "used / not used only",
        "one_of": "one or the other",
        "selectable": "selectable, 1 piece"}


def _ask_text(i):
    bits = []
    if i.get("sizes"):
        bits.append(i["sizes"].replace(",", " &middot; "))
    if i.get("ask") in _ASK:
        bits.append(_ASK[i["ask"]])
    elif i.get("qty"):
        bits.append("&times; %g" % i["qty"])
    return (" <span class='tag'>(%s)</span>" % " &mdash; ".join(bits)) if bits else ""


def _amounts_hint(con, kind):
    """What the days actually carry, as a hint for pricing only. NOT a backfill and not a list
    to name: his ruling of 04-Sep stands -- history is evidence, never data for this module."""
    seeds = billed_amounts(con, kind)[:6]
    if not seeds:
        return ""
    return ("<p class='mut'>For the price, what your own days carry: %s. "
            "(Only a hint \u2014 nothing from the past is loaded.)</p>"
            % " &middot; ".join("&#8377;%s <span class='tag'>%d&times;</span>" % (a["amount"], a["times"])
                                for a in seeds))


@bp.route("", methods=["GET"])
@bp.route("/", methods=["GET"])
def page():
    who, err = _owner()
    if err:
        return err
    con = _db()
    ensure(con)
    msg, cls = request.args.get("m", ""), ("bad" if request.args.get("c") == "bad" else "ok")
    all_rows = services(con)
    items = consumable_items(con)
    body = []
    for kind, label in KINDS:
        rows = [r for r in all_rows if r["kind"] == kind]
        c = counts(con, kind)
        head = ("<h2>%s</h2><p class='mut'>%d waiting for you &middot; %d approved &middot; %d rejected. %s</p>"
                % ("X-rays" if kind == "xray" else "Procedures and their consumables",
                   c["pending"], c["approved"], c["rejected"],
                   ("Read out of your own X-ray register \u2014 6,177 entries reduced to these, "
                    "spellings corrected, the word X-ray dropped.") if kind == "xray" else
                   ("Your rulings of 4 September: the cast and slab sites, the ILI sites, dressing "
                    "\u2014 with the consumables exactly as you set them.")))
        body.append("<div class='card'>%s%s%s</div>"
                    % (head, _rows_html(kind, rows), _amounts_hint(con, kind)))
    body.append("<div class='card'><h2>Add one that is not on either list</h2>"
                "<form class='inline' method='post' action='add'>"
                "<select name='kind'><option value='xray'>X-ray</option>"
                "<option value='proc'>Procedure</option></select>"
                "<input class='name' name='name' placeholder='name' required>"
                "<input class='p' name='price' placeholder='price (optional)' inputmode='decimal'>"
                "<button type='submit'>Add</button></form>"
                "<p class='mut'>Anything you add is approved already \u2014 it is your own line.</p></div>")
    body.append("<datalist id='items'>%s</datalist>"
                % "".join("<option value='%s'>" % _esc(i["item"]) for i in items))
    body.append("<p class='mut'>%d pharmacy items to pick from. Nothing here is loaded from past days: "
                "this list is for the work that comes next.</p>" % len(items))
    return _shell("".join(body), msg, cls)


def _back(msg="", bad=False):
    q = "?m=%s&c=%s" % (msg.replace(" ", "+").replace("&", ""), "bad" if bad else "ok")
    return redirect("/finance/clinic/sheets" + (q if msg else ""))


@bp.route("/add", methods=["POST"])
def route_add():
    who, err = _owner()
    if err:
        return err
    con = _db()
    try:
        add_service(con, who, request.form.get("kind"), request.form.get("name"),
                    request.form.get("price"), request.form.get("note", ""))
    except ValueError as e:
        return _back(str(e), True)
    return _back("Added.")


@bp.route("/status", methods=["POST"])
def route_status():
    who, err = _owner()
    if err:
        return err
    try:
        st = set_status(_db(), who, int(request.form.get("id", "0")), request.form.get("s", ""))
    except ValueError as e:
        return _back(str(e), True)
    return _back("Marked %s." % st)


@bp.route("/rename", methods=["POST"])
def route_rename():
    who, err = _owner()
    if err:
        return err
    try:
        rename(_db(), who, int(request.form.get("id", "0")), request.form.get("name"))
    except ValueError as e:
        return _back(str(e), True)
    return _back("Name saved.")


@bp.route("/price", methods=["POST"])
def route_price():
    who, err = _owner()
    if err:
        return err
    try:
        set_price(_db(), who, int(request.form.get("id", "0")), request.form.get("price"))
    except ValueError as e:
        return _back(str(e), True)
    return _back("Price saved.")


@bp.route("/active", methods=["POST"])
def route_active():
    who, err = _owner()
    if err:
        return err
    set_active(_db(), who, int(request.form.get("id", "0")), request.form.get("on") == "1")
    return _back("Done.")


@bp.route("/item/add", methods=["POST"])
def route_item_add():
    who, err = _owner()
    if err:
        return err
    try:
        add_item(_db(), who, int(request.form.get("id", "0")), request.form.get("item"),
                 request.form.get("qty", "1"), request.form.get("unit", ""))
    except ValueError as e:
        return _back(str(e), True)
    return _back("Added to the procedure.")


@bp.route("/item/drop", methods=["POST"])
def route_item_drop():
    who, err = _owner()
    if err:
        return err
    drop_item(_db(), who, int(request.form.get("id", "0")))
    return _back("Removed.")


@bp.route("/api/services")
def api_services():
    """The read-back door for the chamber screen (D546). Active lines only."""
    who, err = _owner()
    if err:
        return err
    con = _db()
    rows = [s for s in services(con) if s["active"] and s["status"] == "approved"]
    return jsonify(ok=True, count=len(rows), note="approved lines only (S316)",
                   xray=[s for s in rows if s["kind"] == "xray"],
                   proc=[s for s in rows if s["kind"] == "proc"])


@bp.route("/api/healthz")
def healthz():
    con = _db()
    ensure(con)
    n = con.execute("SELECT COUNT(*) AS n FROM owner_service").fetchone()["n"]
    return jsonify(ok=True, services=n)
