#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_register.py -- S837_STOCK_REGISTER_ONE_ITEM (14-Nov-2026, Sanjeevni session 463; the owner's "Mockup is good" of 20:28 IST).

Marg's Stock Register for one item (STOCK_ITEM_LEDGER, the TEXT export as the medical PC converts it) read NAME-FREE at the server's door.
The file carries a Patient Name and a Doctor Name column: those two columns are NEVER read (the one exception: the 'Opening' row's third
cell, read only when it is a date). The door deletes the file afterwards, as it deletes every sale-family file (S186); what is kept is one
row per item (mi_register) and one per entry (mi_register_line): day, entry number, entry type, batch, quantity, value, balance.

THE WITNESS: every balance = the one before it +/- the entry's quantity, and Marg's own Received / Issued footers = the sum of the rows.
A balance that moved by more or less than its entry is kept as the entry's JUMP (jump_u) -- Marg's stock changed outside any entry.
Quantities are strips:loose; a unit is a loose piece (strips x the pack's number after '*', '1*10' -> 10); a plain number is units.
Only the TEXT layout is read; another layout (Marg's Excel, BATCHWISE) is stored as 'not read' with its reason -- nothing is guessed.

Stdlib only.  Called by marg_take.take() and marg_ingest.run() for a VERIFIED STOCK_ITEM_LEDGER, before the file is deleted.
"""
import re

KIT = "S837_STOCK_REGISTER_ONE_ITEM"
DDL = (
    "CREATE TABLE IF NOT EXISTS mi_register (md5 TEXT NOT NULL, seq INTEGER NOT NULL, item TEXT NOT NULL, pack TEXT NOT NULL DEFAULT '', "
    "per INTEGER NOT NULL DEFAULT 1, date_from TEXT NOT NULL DEFAULT '', date_to TEXT NOT NULL DEFAULT '', opening_u INTEGER, closing_u INTEGER, "
    "received_u INTEGER, issued_u INTEGER, n_lines INTEGER NOT NULL DEFAULT 0, n_jumps INTEGER NOT NULL DEFAULT 0, ok INTEGER NOT NULL DEFAULT 0, "
    "note TEXT NOT NULL DEFAULT '', stored_at TEXT NOT NULL, PRIMARY KEY (md5, seq))",
    "CREATE TABLE IF NOT EXISTS mi_register_line (md5 TEXT NOT NULL, seq INTEGER NOT NULL, n INTEGER NOT NULL, day TEXT NOT NULL, "
    "bill_no TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT '', batch TEXT NOT NULL DEFAULT '', qty_u INTEGER NOT NULL, "
    "value_p INTEGER, bal_u INTEGER, jump_u INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (md5, seq, n))",
    "CREATE INDEX IF NOT EXISTS ix_mi_register_item ON mi_register(item)",
)
DATE_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
QTY_RE = re.compile(r"^(-?)(\d+)(?::(\d+))?$")
TITLE_RE = re.compile(r"STOCK\s+REGISTER\s+WHOLE\s+FROM\s+(\d{2}-\d{2}-\d{4})\s*-\s*(\d{2}-\d{2}-\d{4})", re.I)
BILL_RE = re.compile(r"^[A-Za-z0-9/._-]{1,24}$")
PLUS = ("PURCHASE", "SALE RETURN", "RECEIVE", "RECEIPT", "OPENING")
MINUS = ("PURCHASE RETURN", "SALE", "ISSUE", "BREAKAGE", "EXPIRY")
COL_PATIENT, COL_DOCTOR = 2, 3                       # never read


def iso(d):
    m = DATE_RE.match(str(d or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def _txt(v):
    if isinstance(v, float) and v == int(v):
        return "%d" % int(v)
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def split_heading(h):
    """'TYRO BR 1*10' -> ('TYRO BR', '1*10', 10). The pack is the last word when it carries a digit; a name ending in a number keeps it."""
    h = _txt(h).upper()
    parts = h.split(" ")
    pack = parts[-1] if len(parts) > 1 and re.search(r"\d", parts[-1]) and ("*" in parts[-1] or re.search(r"[A-Z]", parts[-1])) else ""
    name = " ".join(parts[:-1]) if pack else h
    m = re.search(r"\*\s*(\d+)\s*$", pack)
    per = int(m.group(1)) if m and int(m.group(1)) > 0 else 1
    return name, pack, per


def units(q, per):
    """'40:0' -> 400 at per 10; '-2:10' -> -30; '7' -> 7. None when not a quantity."""
    m = QTY_RE.match(_txt(q).replace(" ", ""))
    if not m:
        return None
    s, a, b = m.group(1), int(m.group(2)), m.group(3)
    u = a * per + int(b) if b is not None else a
    return -u if s else u


def sign_of(kind):
    k = _txt(kind).upper()
    if k.startswith("ISSUE RETURN"):                  # F-1423 S3: an issue taken back comes IN; a receipt sent back goes OUT
        return 1
    if k.startswith("RECEIVE RETURN") or k.startswith("RECEIPT RETURN"):
        return -1
    if any(k == x or k.startswith(x) for x in ("PURCHASE RETURN",)):
        return -1
    if any(k == x or k.startswith(x) for x in ("SALE RETURN",)):
        return 1
    if any(x in k for x in ("PURCHASE", "RECEIVE", "RECEIPT")):
        return 1
    if any(x in k for x in ("SALE", "ISSUE", "BREAKAGE", "EXPIRY")):
        return -1
    return 0                                          # unknown: the balance decides


def _paise(v):
    try:
        return int(round(float(str(v).replace(",", "")) * 100))
    except (TypeError, ValueError):
        return None


def read(sh):
    """sh: an xlrd-like sheet (nrows, ncols, cell_value). -> dict(ok, date_from, date_to, items=[...], reason). Never reads cols 2 and 3."""
    def c(r, k):
        return _txt(sh.cell_value(r, k)) if k < sh.ncols else ""
    title = ""
    for r in range(min(sh.nrows, 30)):
        j = " ".join(c(r, k) for k in (0, 1))
        m = TITLE_RE.search(j)
        if m:
            title = m
            break
    if not title:
        return dict(ok=False, reason="no 'STOCK REGISTER WHOLE FROM dd-mm-yyyy - dd-mm-yyyy' title (not the TEXT layout)", items=[])
    if sh.ncols < 8:
        return dict(ok=False, reason="fewer than 8 columns (not the TEXT layout)", items=[])
    items, cur, day, pend = [], None, "", None
    rows = [[c(r, k) if k not in (COL_PATIENT, COL_DOCTOR) else "" for k in range(8)] for r in range(sh.nrows)]
    for r, v in enumerate(rows):
        c0, c1, c4, c5, c6, c7 = v[0], v[1], v[4], v[5], v[6], v[7]
        only0 = bool(c0) and not any(v[1:])
        if c0 == "Opening" and c1.lower().startswith("balance"):
            head = next((rows[x][0] for x in range(r - 1, max(-1, r - 6), -1) if rows[x][0] and not any(rows[x][1:])), "")
            name, pack, per = split_heading(head)
            asof = iso(_txt(sh.cell_value(r, COL_PATIENT))) if sh.ncols > COL_PATIENT else ""     # the one cell of col 2 read: a date or nothing
            cur = dict(item=name, pack=pack, per=per, opening_u=units(c7, per), asof=asof, lines=[], received_u=None, issued_u=None)
            items.append(cur)
            day, pend = asof, None
            continue
        if cur is None:
            continue
        if c4 in ("Received :", "Issued :"):
            u = units(c5, cur["per"])
            cur["received_u" if c4.startswith("Received") else "issued_u"] = u
            pend = None
            continue
        if c0 in ("Carried", "Brought") or c0.startswith("Bill No") or (c0 == "Date" and not c1):
            pend = None
            continue
        if only0 and DATE_RE.match(c0):              # F-1423 S3: a row with only a date sets the day of the entries under it
            day, pend = iso(c0), None
            continue
        if only0:
            if pend is not None and BILL_RE.match(c0) and re.search(r"\d", c0):
                pend["bill_no"] = c0
            pend = None
            continue
        if not c1:
            pend = None
            continue
        q, b = units(c5, cur["per"]), units(c7, cur["per"])
        if q is None or b is None:
            pend = None
            continue
        if DATE_RE.match(c0):
            day = iso(c0)
            ln = dict(day=day, bill_no="", kind=c1, batch=c4, q=abs(q), value_p=_paise(c6), bal_u=b)
            pend = ln
        else:
            ln = dict(day=day, bill_no=c0 if BILL_RE.match(c0) else "", kind=c1, batch=c4, q=abs(q), value_p=_paise(c6), bal_u=b)
            pend = None
        cur["lines"].append(ln)
    if not items:
        return dict(ok=False, reason="no 'Opening Balance as on' row", items=[], date_from=iso(title.group(1)), date_to=iso(title.group(2)))
    for it in items:
        prev, rec, iss, jumps = it["opening_u"], 0, 0, 0
        for ln in it["lines"]:
            delta = (ln["bal_u"] - prev) if prev is not None else None
            s = sign_of(ln["kind"])
            if s == 0 and delta is not None:
                s = 1 if delta >= 0 else -1
            ln["qty_u"] = s * ln["q"] if s else ln["q"]
            ln["jump_u"] = (delta - ln["qty_u"]) if delta is not None else 0
            if ln["jump_u"]:
                jumps += 1
            if ln["qty_u"] > 0:
                rec += ln["qty_u"]
            else:
                iss -= ln["qty_u"]
            prev = ln["bal_u"]
        it["closing_u"] = prev
        it["n_jumps"] = jumps
        notes = []
        if it["received_u"] is not None and it["received_u"] != rec:
            notes.append("Received footer %s, rows %s" % (it["received_u"], rec))
        if it["issued_u"] is not None and it["issued_u"] != iss:
            notes.append("Issued footer %s, rows %s" % (it["issued_u"], iss))
        if it["received_u"] is None or it["issued_u"] is None:
            notes.append("no Received / Issued footer")
        if jumps:
            notes.append("%d balance step%s not equal to the entry" % (jumps, "" if jumps == 1 else "s"))
        it["ok"] = 1 if (not notes or (len(notes) == 1 and jumps)) else 0
        it["note"] = "; ".join(notes)
    return dict(ok=True, date_from=iso(title.group(1)), date_to=iso(title.group(2)), items=items, reason="")


def ensure(con):
    for s in DDL:
        con.execute(s)


def store(con, md5, sh, when):
    """Read the sheet and keep its name-free lines under md5 (replacing any earlier read of the same bytes). -> (n entries, note)."""
    ensure(con)
    rep = read(sh)
    con.execute("DELETE FROM mi_register_line WHERE md5=?", (md5,))
    con.execute("DELETE FROM mi_register WHERE md5=?", (md5,))
    if not rep.get("ok"):
        con.execute("INSERT INTO mi_register (md5, seq, item, date_from, date_to, ok, note, stored_at) VALUES (?,?,?,?,?,?,?,?)",
                    (md5, 0, "", rep.get("date_from", "") or "", rep.get("date_to", "") or "", 0, "not read: " + rep.get("reason", ""), when))
        return 0, rep.get("reason", "")
    n_all = 0
    for seq, it in enumerate(rep["items"], 1):
        con.execute("INSERT INTO mi_register (md5, seq, item, pack, per, date_from, date_to, opening_u, closing_u, received_u, issued_u, "
                    "n_lines, n_jumps, ok, note, stored_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (md5, seq, it["item"], it["pack"], it["per"], rep["date_from"], rep["date_to"], it["opening_u"], it["closing_u"],
                     it["received_u"], it["issued_u"], len(it["lines"]), it["n_jumps"], it["ok"], it["note"], when))
        con.executemany("INSERT INTO mi_register_line (md5, seq, n, day, bill_no, kind, batch, qty_u, value_p, bal_u, jump_u) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        [(md5, seq, n, ln["day"], ln["bill_no"], ln["kind"], ln["batch"], ln["qty_u"], ln["value_p"], ln["bal_u"], ln["jump_u"])
                         for n, ln in enumerate(it["lines"], 1)])
        n_all += len(it["lines"])
    return n_all, ""


def store_path(con, md5, path, when, open_sheet):
    """The door's call: never raises; a fault is stored as 'not read'. -> (n entries, note)."""
    try:
        return store(con, md5, open_sheet(path), when)
    except Exception as e:                            # noqa: BLE001
        try:
            ensure(con)
            con.execute("DELETE FROM mi_register_line WHERE md5=?", (md5,))     # F-1423 S4: no line left behind an earlier read
            con.execute("DELETE FROM mi_register WHERE md5=?", (md5,))
            con.execute("INSERT INTO mi_register (md5, seq, item, ok, note, stored_at) VALUES (?,?,?,?,?,?)",
                        (md5, 0, "", 0, "not read: %s" % str(e)[:200], when))
        except Exception:                             # noqa: BLE001
            pass
        return 0, str(e)[:200]
