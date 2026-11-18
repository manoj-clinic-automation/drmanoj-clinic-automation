#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""agilus_ledger.py -- S884-S888 (the parent, S486, 18-Nov-2026). NK Pathology's own Agilus ledger, every line.

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
import json
import os
import re
import sqlite3
import subprocess
import sys

FIN = os.environ.get("FIN_DIR", "/root/finance")
DB = os.environ.get("FINANCE_DB", os.path.join(FIN, "finance.db"))
VENDOR = "Agilus (NK Pathology)"
PARSER = "S888-1"
VERSION = "S888-AGILUS-LEDGER-1.5"
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
  shapes_json  TEXT NOT NULL DEFAULT '{}',
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


ROWSTART = re.compile(r"^(\s*)(\d{1,2})/(\d{1,2})(?:/\d{2,4})?\s+(\S+)")
NUM = re.compile(r"^\d[\d,]*(?:\.\d{1,2})?$")
CODE = re.compile(r"^[A-Za-z]{0,6}\d{4,}$")
HSN = re.compile(r"^\d{4,8}$")


def _row(l, m0, inv_date):
    """One table row by its columns (2+ spaces apart): client code, the patient (the first words after it), then the test
    (the other words; its rate after a comma), an HSN where one stands, and any figures. The HSN is optional and may stand
    before or after the test (S886: 35 papers read no line in S885). None when no patient or no figure."""
    chunks = [(c.start(), c.group(0)) for c in CHUNK.finditer(l, m0.end(4))]
    if len(chunks) < 3:
        return None
    first = chunks[0][1].split(" ", 1)
    if not CODE.match(first[0]):
        return None
    client = first[0]
    if len(first) > 1:                                                 # the code and the name only one space apart
        chunks[0] = (chunks[0][0] + len(first[0]) + 1, first[1])
    else:
        chunks = chunks[1:]
    if not chunks or NUM.match(chunks[0][1]):
        return None
    pst, name = chunks[0]
    hsn, svc, nums = "", [], []
    for st, t in chunks[1:]:
        if HSN.match(t) and not hsn:
            hsn = t
        elif NUM.match(t):
            nums.append((st, t))
        else:
            svc.append((st, t))
    test = " ".join(t for _s, t in svc)
    rate = None
    mr = re.search(r",\s*" + MONEY + r"$", test)
    if mr:
        rate, test = _paise(mr.group(1)), test[:mr.start()].strip()
    moneys = [t for _s, t in nums if re.search(r"\.\d{2}$", t)]
    last = _paise(moneys[-1]) if moneys else None
    if rate is None and last is None:
        return None
    gross = rate                                                       # S888: the gross is the rate, else the row's biggest other figure
    if gross is None:
        others = [_paise(t) for _s, t in nums if t != moneys[-1]] if moneys else []
        others = [v for v in others if v]
        gross = max(others) if others else None
    net = (gross - last) if (gross is not None and last is not None and gross > last) else None
    dd, mm = int(m0.group(2)), int(m0.group(3))
    yr = _year_for(mm, inv_date) if inv_date else None
    try:
        tdate = dt.date(yr, mm, dd).isoformat() if yr else None
    except ValueError:
        tdate = None
    return {"test_date": tdate, "accession": m0.group(4), "client_code": client, "patient_name": re.sub(r"\s+", " ", name),
            "patient_ref": "", "hsn": hsn, "test": re.sub(r"\s+", " ", test), "amount_paise": None,
            "_rate": rate, "_last": last, "_gross": gross, "_net": net, "_p": pst, "_t": svc[0][0] if svc else pst + len(name) + 2,
            "_n": nums[0][0] if nums else None}


def mask_all(l):
    """Every letter run to X's (at most 4), every digit to 9: the line's shape and spacing only, never a word (D656)."""
    return re.sub(r"[^\W\d_]+", lambda m: "X" * min(len(m.group(0)), 4), re.sub(r"\d", "9", l))


def _shape(l, m0):
    """A row's shape in classes only -- never its words (D656): D date, A accession, C code, W words, H hsn,
    S test, S, test ending in a figure, M money, Q a whole number."""
    out = ["D", "A"]
    for c in CHUNK.finditer(l, m0.end(4)):
        t = c.group(0)
        out.append("M" if re.match(r"^\d[\d,]*\.\d{2}$", t) else "H" if HSN.match(t) else "Q" if NUM.match(t) else
                   "C" if CODE.match(t.split(" ")[0]) and len(out) == 2 else "S," if re.search(r",\s*" + MONEY + r"$", t) else "W")
    return " ".join(out)


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
    out, unread, shapes = [], 0, {}
    for page in (text or "").split("\f"):                             # every page starts clean (review S884: page-2 header)
        cur, in_table = None, False
        for l in page.splitlines():
            if not l.strip():
                continue
            if re.search(r"patient name|hsn/sac", l, re.I):            # the table's header (repeated on every page)
                in_table, cur = True, None
                continue
            if re.search(r"\btotal\b\s*:|grand total|rupees|payment|bank|regd|details of|bill of supply|page\s*\d", l, re.I):
                if re.search(r"\btotal\b\s*:|grand total", l, re.I):
                    in_table = False                                   # the table ends at its total
                cur = None
                continue
            m0 = ROWSTART.match(l) if in_table else None
            if m0:
                row = _row(l, m0, inv_date)
                sk = _shape(l, m0)
                shapes[sk] = shapes.get(sk, 0) + 1
                if row is None:
                    unread += 1                                        # a line row this reader could not take: counted, never merged
                    if len(head.setdefault("unread_masked", [])) < 3:
                        head["unread_masked"].append(mask_all(l.rstrip())[:400])
                    cur = None
                    continue
                row["line_no"] = len(out) + 1
                out.append(row)
                cur = row
                continue
            if in_table and re.search(MONEY + r"\s*$", l):
                unread += 1
                if len(head.setdefault("unread_masked", [])) < 3:
                    head["unread_masked"].append(mask_all(l.rstrip())[:400])
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
                elif cur["_n"] is None or st < cur["_n"] - 2:
                    cur["test"] = (cur["test"] + " " + txt).strip()
    head["shapes"] = shapes
    tl = None                                                          # the paper's own 'TOTAL:' line (not GRAND TOTAL)
    for l in lines:
        mt = re.search(r"(?<!grand )\btotal\s*:\s*" + MONEY, l, re.I)
        if mt and not re.search(r"grand", l[:mt.start() + 1], re.I):
            tl = _paise(mt.group(1))
    if head["amount"] is None and tl is not None:
        head["amount"] = tl                                            # the paper's net from its TOTAL line when the header's is not read
    # a line's amount is its NET (his word 20:25): the column -- or gross less discount -- that adds up to the paper's net
    sums = {k: sum(r[k] or 0 for r in out) for k in ("_last", "_rate", "_net", "_gross")}
    full = {k: bool(out) and all(r[k] is not None for r in out) for k in sums}
    use = next((k for k in ("_last", "_rate", "_net", "_gross") if head["amount"] is not None and full[k] and sums[k] == head["amount"]), None)
    if use is None:
        use = "_net" if full["_net"] else ("_rate" if full["_rate"] else "_last")
    for r in out:
        r["amount_paise"] = next((r[k] for k in (use, "_net", "_rate", "_last") if r[k] is not None), None)
    head["figures"] = {"sum_rate": sums["_rate"], "sum_last": sums["_last"], "sum_net": sums["_net"], "total_line": tl, "use": use}
    for x in out:
        for k in ("_p", "_t", "_n", "_rate", "_last", "_gross", "_net"):
            x.pop(k, None)
    return head, out, unread


def ensure_schema(con):
    con.executescript(SCHEMA)
    if "shapes_json" not in {r[1] for r in con.execute("PRAGMA table_info(agilus_invoice)")}:
        con.execute("ALTER TABLE agilus_invoice ADD COLUMN shapes_json TEXT NOT NULL DEFAULT '{}'")
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
                        "lines_paise, n_lines, unread_rows, status, shapes_json, parser, parsed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (p["id"], p["sha256"], head["invoice_no"], p["mail_date"], head["amount"], total, len(rows),
                         unread, status, json.dumps({"shapes": head.get("shapes") or {}, "unread_masked": head.get("unread_masked") or [],
                                    "figures": head.get("figures") or {}}, sort_keys=True),
                         "" if retry else PARSER, now_ist()))
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
        sh = {}
        um = []
        for r in con.execute("SELECT shapes_json FROM agilus_invoice ORDER BY inv_date DESC"):
            d = json.loads(r["shapes_json"] or "{}")
            for k, v in (d.get("shapes", d) if isinstance(d.get("shapes", None), dict) else d).items():
                if isinstance(v, int):
                    sh[k] = sh.get(k, 0) + v
            for x in d.get("unread_masked") or []:
                if len(um) < 8:
                    um.append(x)
        c["row_shapes"] = sorted(sh.items(), key=lambda x: -x[1])[:6]       # classes only, never a word (D656)
        c["rows_not_read_masked"] = um                                     # every letter X, every digit 9 (D656)
        ds = []                                                            # S887: why a paper differs -- figures only, never a word
        for r in con.execute("SELECT amount_paise, lines_paise, n_lines, unread_rows, shapes_json FROM agilus_invoice "
                             "WHERE status='lines differ' ORDER BY inv_date DESC LIMIT 12"):
            f = (json.loads(r["shapes_json"] or "{}").get("figures") or {})
            ds.append({"paper": r["amount_paise"], "rates": f.get("sum_rate"), "last": f.get("sum_last"), "net": f.get("sum_net"),
                       "total_line": f.get("total_line"), "lines": r["n_lines"], "unread": r["unread_rows"]})
        c["differ_figures"] = ds
        reg = {}
        try:
            for r in con.execute("SELECT date_iso, amount_paise FROM payment_register WHERE vendor=? AND amount_paise IS NOT NULL", (VENDOR,)):
                reg.setdefault(r["date_iso"], []).append(r["amount_paise"])
        except sqlite3.Error:
            reg = {}
        ag = dis = 0
        for r in con.execute("SELECT inv_date, amount_paise FROM agilus_invoice WHERE amount_paise IS NOT NULL"):
            cand = reg.get(r["inv_date"]) or []
            if len(cand) == 1:
                if cand[0] == r["amount_paise"]:
                    ag += 1
                else:
                    dis += 1
        c["paper_vs_mail"] = {"agree": ag, "differ": dis}
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


def accountants(con, month=None):
    """The accountants' Agilus ledger -- NET amounts against the invoices only, nothing else (his word 20:25-20:29):
    rows of (date, Bill of Supply number, net amount in paise, running total in paise); the brought-forward total of
    every invoice before the month. month 'YYYY-MM' or None for all. No patient's anything."""
    led = ledger(con)
    rows, bf = [], 0
    for x in led:
        d = x["inv_date"] or ""
        if month and d[:7] < month:
            bf = x["running"]
            continue
        if month and d[:7] > month:
            continue
        rows.append({"date": d, "invoice_no": x["invoice_no"] or "", "net": x["amount"], "running": x["running"],
                     "read": x["amount_paise"] is not None})
    return {"month": month, "brought_forward": bf if month else 0, "rows": rows,
            "months": sorted({(x["inv_date"] or "")[:7] for x in led if x["inv_date"]})}


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
