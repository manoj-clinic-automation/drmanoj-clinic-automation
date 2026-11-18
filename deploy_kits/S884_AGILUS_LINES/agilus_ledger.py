#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""agilus_ledger.py -- S884 (the parent, S486, 18-Nov-2026). NK Pathology's own Agilus ledger, every line.

THE OWNER, 18-Nov-2026 18:39-18:48: Agilus is paid a lump sum in advance; it raises its invoices against it as a
running ledger and, asked, sends its own ledger only reluctantly -- "construct our own ... ledger for NK pathology ...
every receipt comes in the email"; "the Agilus ledger should contain the patient names, date, amount, etc. everything".
Deposits go from the bank; the accountants match them for now.

WHAT IT DOES
  build   (cron 02:35, after S882's 02:20 copy): reads every Agilus 'Bill of Supply' copied to the server
          (payment_record_file, vendor 'Agilus (NK Pathology)'), and writes:
            agilus_invoice  one row per paper: its number, date, the paper's own amount, the sum of its lines,
                            and whether they agree ('ok' / 'lines differ' / 'no lines read' / 'unreadable');
            agilus_line     one row per patient line: the test's date, the accession, the client code, the
                            patient's name and reference, the HSN, the test, the amount.
          A paper is re-read only when it is new or this reader's version changed. Nothing is ever printed but counts.
  status  counts only.
The layout was learned from the masked layout (S882, /finance/ledgers/agilus/layout): no patient's name ever left the
server to build this (D656). No patient data, no secret and no number in this file (F-185).
"""
import datetime as dt
import os
import re
import sqlite3
import subprocess
import sys

FIN = os.environ.get("FIN_DIR", "/root/finance")
DB = os.environ.get("FINANCE_DB", os.path.join(FIN, "finance.db"))
VENDOR = "Agilus (NK Pathology)"
PARSER = "S884-2"
VERSION = "S884-AGILUS-LEDGER-1.1"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

SCHEMA = """
CREATE TABLE IF NOT EXISTS agilus_invoice (
  file_id      INTEGER PRIMARY KEY,
  sha256       TEXT NOT NULL,
  invoice_no   TEXT,
  inv_date     TEXT,
  amount_paise INTEGER,
  lines_paise  INTEGER NOT NULL DEFAULT 0,
  n_lines      INTEGER NOT NULL DEFAULT 0,
  unread_rows  INTEGER NOT NULL DEFAULT 0,
  status       TEXT NOT NULL,
  parser       TEXT NOT NULL,
  parsed_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agilus_line (
  id           INTEGER PRIMARY KEY,
  file_id      INTEGER NOT NULL,
  line_no      INTEGER NOT NULL,
  test_date    TEXT,
  accession    TEXT,
  client_code  TEXT,
  patient_name TEXT,
  patient_ref  TEXT,
  hsn          TEXT,
  test         TEXT,
  amount_paise INTEGER
);
CREATE INDEX IF NOT EXISTS ix_agilus_line_file ON agilus_line(file_id);
CREATE INDEX IF NOT EXISTS ix_agilus_line_name ON agilus_line(patient_name);
"""

MONEY = r"(\d[\d,]*\.\d{2})"
ROW = re.compile(r"^(\s*)(\d{2}/\d{2})\s+(\S+)\s+([A-Z]{1,3}\d{5,12})\s+(\S.*?\S|\S)\s{2,}(\d{4,8})\s+(\S.*?),\s*" + MONEY + r"\s*$")
CHUNK = re.compile(r"\S(?:\S| (?=\S))*")


def now_ist():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def text_of(path):
    try:
        r = subprocess.run(["pdftotext", "-layout", path, "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
        return r.stdout.decode("utf-8", "replace")
    except Exception:                                                  # noqa: BLE001
        return ""


def _paise(s):
    try:
        return int(round(float(s.replace(",", "")) * 100))
    except (TypeError, ValueError):
        return None


def _after(lines, i, label, rx, ahead=4):
    """The first match of rx after the label on line i, else on the next `ahead` lines -- read only from the label's
    own column rightwards (the left half of those lines is the address block)."""
    col = lines[i].lower().find(label)
    for s in [lines[i][col + len(label):]] + [x[max(0, col - 2):] for x in lines[i + 1:i + 1 + ahead]]:
        m = rx.search(s)
        if m:
            return m.group(1)
    return None


def _year_for(mm, inv_date):
    try:
        y, m = int(inv_date[:4]), int(inv_date[5:7])
    except (TypeError, ValueError):
        return None
    return y if int(mm) <= m else y - 1


def parse(text, inv_date=None):
    """One Agilus Bill of Supply's text -> (header dict, list of line dicts, rows not read). Pure: no I/O."""
    lines = (text or "").replace("\f", "\n").splitlines()      # the header fields; the rows are read page by page below
    head = {"invoice_no": None, "amount": None}
    for i, l in enumerate(lines):
        low = l.lower()
        if head["invoice_no"] is None and "bill of supply no" in low:
            head["invoice_no"] = _after(lines, i, "bill of supply no", re.compile(r"\b([A-Z]{0,3}\d{8,16})\b"))
        if head["amount"] is None and "bill of supply amount" in low:
            v = _after(lines, i, "bill of supply amount", re.compile(MONEY))
            head["amount"] = _paise(v) if v else None
    out, unread = [], 0
    for page in (text or "").split("\f"):                             # every page starts clean (review S884: page-2 header)
        cur, in_table = None, False
        for l in page.splitlines():
            if not l.strip():
                continue
            if re.search(r"patient name|hsn/sac", l, re.I):            # the table's header (repeated on every page)
                in_table, cur = True, None
                continue
            m = ROW.match(l)
            if m:
                dd, mm = m.group(2).split("/")
                yr = _year_for(mm, inv_date) if inv_date else None
                try:
                    tdate = dt.date(yr, int(mm), int(dd)).isoformat() if yr else None
                except ValueError:
                    tdate = None
                cur = {"line_no": len(out) + 1, "test_date": tdate, "accession": m.group(3), "client_code": m.group(4),
                       "patient_name": re.sub(r"\s+", " ", m.group(5)).strip(), "patient_ref": "", "hsn": m.group(6),
                       "test": re.sub(r"\s+", " ", m.group(7)).strip(), "amount_paise": _paise(m.group(8)),
                       "_p": m.start(5), "_t": m.start(7)}
                out.append(cur)
                continue
            if re.search(r"\btotal\b\s*:|grand total|rupees|payment|bank|regd|details of|bill of supply|page\s*\d", l, re.I):
                if re.search(r"\btotal\b\s*:|grand total", l, re.I):
                    in_table = False                                   # the table ends at its total
                cur = None
                continue
            if in_table and (re.match(r"^\s*\d{1,2}/\d{1,2}", l) or re.search(MONEY + r"\s*$", l)):
                unread += 1                                            # a line row this reader could not take: counted, never merged
                cur = None
                continue
            if cur is None:
                continue
            chunks = [(c.start(), c.group(0)) for c in CHUNK.finditer(l)]
            if not all(abs(st - cur["_p"]) <= 6 or st >= cur["_t"] - 6 for st, _x in chunks):
                cur = None                                             # not a continuation of this row: never glued onto it
                continue
            for st, txt in chunks:
                if abs(st - cur["_p"]) <= 6:
                    if re.search(r"\d", txt):
                        cur["patient_ref"] = (cur["patient_ref"] + " " + txt).strip()
                    else:
                        cur["patient_name"] = (cur["patient_name"] + " " + txt).strip()
                else:
                    cur["test"] = (cur["test"] + " " + txt).strip()
    for x in out:
        x.pop("_p", None)
        x.pop("_t", None)
    return head, out, unread


def ensure_schema(con):
    con.executescript(SCHEMA)
    con.commit()


def _papers(con):
    try:
        rows = list(con.execute("SELECT id, sha256, mail_date, local_path, kind FROM payment_record_file "
                                "WHERE vendor=? AND kind IN ('invoice','unreadable') ORDER BY mail_date, id", (VENDOR,)))
    except sqlite3.Error:
        return []
    seen, out = set(), []
    for r in rows:
        if r["sha256"] in seen:
            continue
        seen.add(r["sha256"])
        out.append(r)
    return out


def build(con, force=False):
    ensure_schema(con)
    done = {r["file_id"]: r["parser"] for r in con.execute("SELECT file_id, parser FROM agilus_invoice")}
    n = 0
    for p in _papers(con):
        if not force and done.get(p["id"]) == PARSER:
            continue
        t = text_of(p["local_path"]) if p["kind"] != "unreadable" else ""
        head, rows, unread = parse(t, p["mail_date"])
        total = sum(r["amount_paise"] or 0 for r in rows)
        retry = (not t.strip()) and p["kind"] == "invoice"            # pdftotext failed tonight: try again tomorrow
        if not t.strip():
            status = "unreadable"
        elif not rows:
            status = "no lines read"
        elif head["amount"] is not None and total == head["amount"] and not unread:
            status = "ok"
        else:
            status = "lines differ"
        with con:
            con.execute("DELETE FROM agilus_line WHERE file_id=?", (p["id"],))
            con.executemany("INSERT INTO agilus_line(file_id, line_no, test_date, accession, client_code, patient_name, "
                            "patient_ref, hsn, test, amount_paise) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            [(p["id"], r["line_no"], r["test_date"], r["accession"], r["client_code"], r["patient_name"],
                              r["patient_ref"], r["hsn"], r["test"], r["amount_paise"]) for r in rows])
            con.execute("INSERT OR REPLACE INTO agilus_invoice(file_id, sha256, invoice_no, inv_date, amount_paise, "
                        "lines_paise, n_lines, unread_rows, status, parser, parsed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (p["id"], p["sha256"], head["invoice_no"], p["mail_date"], head["amount"], total, len(rows),
                         unread, status, "" if retry else PARSER, now_ist()))
        n += 1
    keep = [p["id"] for p in _papers(con)]                             # a paper gone from the copy leaves the ledger too
    with con:
        q = ",".join("?" * len(keep)) or "NULL"
        con.execute("DELETE FROM agilus_line WHERE file_id NOT IN (%s)" % q, keep)
        con.execute("DELETE FROM agilus_invoice WHERE file_id NOT IN (%s)" % q, keep)
    return n


def counts(con):
    c = {"invoices": 0, "ok": 0, "lines differ": 0, "no lines read": 0, "unreadable": 0, "lines": 0, "rows_not_read": 0,
         "charged_paise": 0, "version": VERSION}
    try:
        amt = {x["file_id"]: x["amount"] for x in ledger(con)}
        for r in con.execute("SELECT i.status, COUNT(*) n, SUM(i.n_lines) l, SUM(i.unread_rows) u, GROUP_CONCAT(i.file_id) ids "
                             "FROM agilus_invoice i JOIN payment_record_file f ON f.id=i.file_id GROUP BY i.status"):
            c["invoices"] += r["n"]
            c[r["status"]] = r["n"]
            c["lines"] += r["l"] or 0
            c["rows_not_read"] += r["u"] or 0
            c["charged_paise"] += sum(amt.get(int(x)) or 0 for x in (r["ids"] or "").split(",") if x)
    except sqlite3.Error:
        pass
    return c


def ledger(con):
    """Invoices oldest first, each with its lines and the running total (the paper's own amount; its lines' sum when
    the paper's amount was not read)."""
    out, run = [], 0
    try:
        inv = list(con.execute("SELECT i.*, f.name, f.total_paise FROM agilus_invoice i JOIN payment_record_file f ON f.id=i.file_id "
                               "ORDER BY i.inv_date, i.file_id"))
    except sqlite3.Error:
        return []
    s882 = {}
    try:                                                               # S882's figures: the paper's own total, else the mail's
        if FIN not in sys.path:
            sys.path.insert(0, FIN)
        import payment_records as _pr                                  # noqa: PLC0415
        s882 = {r["file"]: r["amount"] for r in _pr.agilus_rows(con)}
    except Exception:                                                  # noqa: BLE001
        s882 = {}
    for i in inv:
        amt = i["amount_paise"]
        if amt is None:
            amt = i["total_paise"] if i["total_paise"] else s882.get(i["file_id"])
        if amt is None and i["lines_paise"]:
            amt = i["lines_paise"]
        run += amt or 0
        lines = [dict(r) for r in con.execute("SELECT * FROM agilus_line WHERE file_id=? ORDER BY line_no", (i["file_id"],))]
        out.append(dict(i, amount=amt, running=run, lines=lines))
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "status"
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    if cmd in ("build", "rebuild"):
        try:
            n = build(con, force=(cmd == "rebuild"))
        except Exception as e:                                         # noqa: BLE001 -- a name never reaches the log
            print("agilus_ledger NOT OK: %s" % type(e).__name__)
            return 2
        c = counts(con)
        print("agilus_ledger %s: %d read now; %d invoices -- %d lines add up to the paper, %d differ, %d no lines read, "
              "%d unreadable; %d patient lines; %d rows not read" % (VERSION, n, c["invoices"], c["ok"], c["lines differ"],
                                                                     c["no lines read"], c["unreadable"], c["lines"], c["rows_not_read"]))
        return 0
    c = counts(con)
    print("agilus_ledger %s: %d invoices -- %d add up, %d differ, %d no lines, %d unreadable; %d lines; %d rows not read" % (
        VERSION, c["invoices"], c["ok"], c["lines differ"], c["no lines read"], c["unreadable"], c["lines"], c["rows_not_read"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
