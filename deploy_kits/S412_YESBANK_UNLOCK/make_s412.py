#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s412.py -- kit S412_YESBANK_UNLOCK. Builds the five patched files FROM THE LIVE BYTES with anchored edits (every anchor
exactly once, else it refuses) after checking each file's FROM pin:

  packs.py            the shelf opens Yes Bank's password-locked PDFs itself: stmt_secret (the owner's candidates, in finance.db only,
                      never echoed), the unlock step of process_inbox (a venv subprocess -- stmt_shelf.py unlock), 'locked -- no password'
                      when nothing opens a file, the branch copy is the one on the shelf ('duplicate of branch copy' for the locked twin),
                      the four non-Sanjeevni Yes Bank accounts go to their own tables (yesbank_account_statement_*), never the shared ones
                      the owner's Bank card reads; the anchor rule (3a); the Needs-you line; the 'Statement passwords' API and card state
  packs.html          the 'Statement passwords' card (masked, set on <date>, Replace); the cells and the unplaced table say 'opened' / 'no password'
  stmt_shelf.py       the 'unlock' command (pypdf in the venv; RC4 and AES-256 both) -- counts only, never a value
  finance_icici.py    (3b) a pipe .txt whose header period is degenerate (from == to) takes its rows' first and last dates; VERSION stays 1.1
  finance_yesbank.py  ingest_statement(..., tables=None): the shared tables by default, a named pair for the non-Sanjeevni accounts (declared)

Usage: make_s412.py --finance /root/finance --out DIR
"""
import hashlib
import io
import os
import sys

FROM = {"packs.py": "afd429bf8c0e7f685adda7d688045ab7", "packs.html": "b46d817c7a77944c4280ac72f95a6808",
        "stmt_shelf.py": "e74c29c0a5bb41f21cd2f7c1c8d3ad5d", "finance_icici.py": "6d55a28aac170b1ab5899faa60eaa257",
        "finance_yesbank.py": "825016c02364dc5d22027ff192d1d29d"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    with io.open(path, "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


# ============================================================================ packs.py
def build_packs(s):
    s = rep(s, '''statements are read; a password-locked PDF is named as such and waits for a decrypted copy; a statement covering only part of a month is
'partial' and never the month's statement. ICICI lines live in icici_statement_period/_line (finance_icici v1.1), never in the Yes Bank
tables the owner's Bank card reads.
"""''', '''statements are read; a password-locked PDF is named as such and waits for a decrypted copy; a statement covering only part of a month is
'partial' and never the month's statement. ICICI lines live in icici_statement_period/_line (finance_icici v1.1), never in the Yes Bank
tables the owner's Bank card reads.

S412 (Yes Bank unlock, 26-Sep-2026): the shelf opens Yes Bank's password-locked e-statements ITSELF. The owner types the bank's statement
password once (the 'Statement passwords' card; candidates one per line) -> stmt_secret, kept in finance.db only, never printed, never logged,
never sent back to any page (the page shows 'set on <date>' and Replace). process_inbox runs an unlock step: the venv python (the only one
with pypdf) opens every locked PDF the candidates fit into <inbox>/<id>.unlocked.pdf (stmt_shelf.py unlock), the locked original stays,
and the file is then identified and read as any other; a file nothing opens reads 'locked -- no password' and is retried on every run.
The branch's own statements (not locked) are the PRIMARY Yes Bank source: when a branch copy of the same account-month is on the shelf,
the locked twin is 'duplicate of branch copy' and never read into the tables. The four non-Sanjeevni Yes Bank accounts go to
yesbank_account_statement_period/_line (their own tables) -- never bank_statement_*, which the owner's Bank card, the statement-covers
test and the NEFT bank check read as 'the Yes Bank statement' with no account filter. The ICICI anchor moves only on a statement with a
real header period and a PRINTED closing (never the pipe .txt). No secret, no account number beyond a tail, anywhere in this file.
"""''', "header")
    s = rep(s, '''INBOX = os.environ.get("STMT_INBOX", os.path.join(HERE, "statements", "inbox"))
''', '''INBOX = os.environ.get("STMT_INBOX", os.path.join(HERE, "statements", "inbox"))
VPY = os.environ.get("STMT_VENV_PYTHON", "/root/wa/venv/bin/python3")      # S412: the unlock step runs under the venv (pypdf lives there only)
''', "VPY")
    s = rep(s, '''    " fetched_at TEXT, local_path TEXT, bank TEXT, holder TEXT, tail TEXT, kind TEXT, ident_how TEXT, note TEXT, identified_at TEXT)",
    "CREATE TABLE IF NOT EXISTS pack_send (''', '''    " fetched_at TEXT, local_path TEXT, bank TEXT, holder TEXT, tail TEXT, kind TEXT, ident_how TEXT, note TEXT, identified_at TEXT,"
    " locked INTEGER NOT NULL DEFAULT 0, unlocked_path TEXT, unlocked_at TEXT)",
    # S412: the owner's statement passwords -- candidates as a JSON list, per bank; never selected into any page or log
    "CREATE TABLE IF NOT EXISTS stmt_secret (bank TEXT PRIMARY KEY, secret TEXT NOT NULL, set_by TEXT, set_at TEXT)",
    "CREATE TABLE IF NOT EXISTS stmt_secret_log (id INTEGER PRIMARY KEY, bank TEXT NOT NULL, action TEXT NOT NULL, who TEXT, at TEXT)",
    # S412: the non-Sanjeevni Yes Bank accounts' own tables (the shape of the ICICI ones + slot_key); the shared bank_statement_* stay Sanjeevni's
    "CREATE TABLE IF NOT EXISTS yesbank_account_statement_period (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, slot_key TEXT, period_from TEXT NOT NULL,"
    " period_to TEXT NOT NULL, opening_p INTEGER, closing_p INTEGER, source_file TEXT, sha256 TEXT, ingested_at TEXT, UNIQUE (account_ref, period_from, period_to))",
    "CREATE TABLE IF NOT EXISTS yesbank_account_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, slot_key TEXT, txn_date TEXT NOT NULL,"
    " value_date TEXT, description TEXT NOT NULL, reference TEXT, withdrawal_p INTEGER NOT NULL DEFAULT 0, deposit_p INTEGER NOT NULL DEFAULT 0,"
    " balance_p INTEGER, is_cash_deposit INTEGER NOT NULL DEFAULT 0, source_file TEXT, sha256 TEXT, ingested_at TEXT,"
    " UNIQUE (account_ref, txn_date, reference, deposit_p, withdrawal_p))",
    "CREATE TABLE IF NOT EXISTS pack_send (''', "DDL")
    s = rep(s, '''LOCKED_NOTE = "password-protected PDF -- the bank's password is not on this server; put a decrypted copy in Bank Statements/Decrypted"
''', '''LOCKED_NOTE = "password-protected PDF -- type the bank's statement password once under 'Statement passwords' on this page; the shelf opens it itself"
LOCKED_NO_PW_NOTE = "password-protected PDF -- none of the stored passwords opens it (replace them under 'Statement passwords')"
LOCKED_NO_PW = "locked -- no password"
DUP_OF_BRANCH = "duplicate of branch copy"
SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"))       # the banks that send locked PDFs (Yes Bank now)
YES_ACCOUNT_TABLES = ("yesbank_account_statement_period", "yesbank_account_statement_line")
STMT_FILE_COLS = (("locked", "INTEGER NOT NULL DEFAULT 0"), ("unlocked_path", "TEXT"), ("unlocked_at", "TEXT"))
''', "notes")
    s = rep(s, '''def ensure(con):
    for d in DDL:
        con.execute(d)
    for i, (key, bank, label, kind, words, sanj) in enumerate(SLOTS):''', '''def ensure(con):
    for d in DDL:
        con.execute(d)
    have = {r[1] for r in con.execute("PRAGMA table_info(stmt_file)")}          # S412: the columns on a shelf made before this kit
    for c, d in STMT_FILE_COLS:
        if c not in have:
            con.execute("ALTER TABLE stmt_file ADD COLUMN %s %s" % (c, d))
    for i, (key, bank, label, kind, words, sanj) in enumerate(SLOTS):''', "ensure columns")
    # ---- read_file: the unlocked copy, the duplicate rule, the Yes Bank per-account tables, the period written back
    s = rep(s, '''def read_file(con, f, slot):
    """Read a placed bank statement into the bank tables; a card is filed as arrived. Returns (read_status, matched_status)."""
    if not slot or slot["kind"] == "card" or not f["local_path"] or not os.path.exists(f["local_path"]):
        return ("n/a" if slot and slot["kind"] == "card" else "no file"), ""
    with open(f["local_path"], "rb") as fh:
        blob = fh.read()
    try:
        if slot["bank"] == "YES":
            import finance_yesbank                        # noqa: PLC0415
            res = finance_yesbank.ingest_statement(con, f["name"], blob, None, now=_now())
        elif slot["bank"] == "ICICI":
            import finance_icici                          # noqa: PLC0415
            res = finance_icici.ingest_statement(con, f["name"], blob, now=_now())
            if slot["key"] == "icici_sanj":
                _anchor_refresh(con, res)
        else:
            return "n/a", ""
    except Exception as ex:                              # noqa: BLE001
        return "refused: %s" % str(ex)[:160], ""
    matched = "ingested %d lines" % res.get("lines", 0)
    return "read", matched
''', '''def read_file(con, f, slot):
    """Read a placed bank statement into the bank tables; a card is filed as arrived. Returns (read_status, matched_status).
    S412: a locked file is read from its unlocked copy; a Yes Bank statement of a NON-Sanjeevni account goes to the per-account tables;
    when a branch copy (not locked) of the same account-month is on the shelf, the locked twin is 'duplicate of branch copy' and never
    read into the tables; the period the reader proved is written back to the shelf row (the pipe .txt's widened one too)."""
    if not slot or slot["kind"] == "card":
        return ("n/a" if slot and slot["kind"] == "card" else "no file"), ""
    path = f.get("unlocked_path") or f.get("local_path")
    if not path or not os.path.exists(path):
        return "no file", ""
    with open(path, "rb") as fh:
        blob = fh.read()
    try:
        if slot["bank"] == "YES":
            import finance_yesbank                        # noqa: PLC0415
            parsed = finance_yesbank.parse_statement(blob)
            pf, pt = parsed["period_from"], parsed["period_to"]
            if f.get("locked"):
                dup = con.execute("SELECT id FROM stmt_file WHERE id<>? AND slot_id=? AND period_from=? AND period_to=? AND read_status='read' AND COALESCE(locked,0)=0",
                                  (f["id"], slot["id"], pf, pt)).fetchone()
                if dup:
                    con.execute("UPDATE stmt_file SET period_from=?, period_to=? WHERE id=?", (pf, pt, f["id"]))
                    return DUP_OF_BRANCH, "file %d is the branch copy" % dup[0]
            else:
                con.execute("UPDATE stmt_file SET read_status=?, matched_status=? WHERE id<>? AND slot_id=? AND period_from=? AND period_to=? AND locked=1 AND read_status='read'",
                            (DUP_OF_BRANCH, "file %d is the branch copy" % f["id"], f["id"], slot["id"], pf, pt))
            tables = None if slot.get("sanjeevni") else YES_ACCOUNT_TABLES
            res = finance_yesbank.ingest_statement(con, f["name"], blob, None, now=_now(), tables=tables)
            if tables:
                for t in tables:
                    con.execute("UPDATE %s SET slot_key=? WHERE account_ref=? AND (slot_key IS NULL OR slot_key='')" % t, (slot["key"], res["account_ref"]))
        elif slot["bank"] == "ICICI":
            import finance_icici                          # noqa: PLC0415
            res = finance_icici.ingest_statement(con, f["name"], blob, now=_now())
            if slot["key"] == "icici_sanj":
                _anchor_refresh(con, res)
        else:
            return "n/a", ""
    except Exception as ex:                              # noqa: BLE001
        return "refused: %s" % str(ex)[:160], ""
    if res.get("period") and res["period"][0] and res["period"][1]:
        con.execute("UPDATE stmt_file SET period_from=?, period_to=? WHERE id=?", (res["period"][0], res["period"][1], f["id"]))
    matched = "ingested %d lines" % res.get("lines", 0)
    return "read", matched
''', "read_file")
    s = rep(s, '''    if not _has(con, "bank_anchor"):
        return
    r = con.execute("SELECT as_on FROM bank_anchor WHERE unit='medical' AND account='icici'").fetchone()''', '''    if not _has(con, "bank_anchor"):
        return
    # S412 (3a): only a statement whose header period is REAL (from < to) and whose closing balance is PRINTED and proven may move the
    # anchor -- never the pipe .txt (no closing printed, a degenerate header): S411's first run had moved it to 10-Sep on exactly that.
    per = res.get("period") or (None, None)
    if not res.get("closing_printed") or res.get("layout") == "pipe" or not (per[0] and per[1] and per[0] < per[1]):
        return
    r = con.execute("SELECT as_on FROM bank_anchor WHERE unit='medical' AND account='icici'").fetchone()''', "anchor rule")
    # ---- the unlock step + process_inbox
    s = rep(s, '''def process_inbox(con=None, verbose=False):
    """S411: identify in passes -- a file that prints only its account number (ICICI's .txt) may arrive before the statement that
    teaches the account's tail; while a pass learns a new tail, the still-unplaced files get another look (at most three passes)."""
    own = con is None
    con = con or _con()
    ensure(con)
    tails = lambda: con.execute("SELECT COUNT(*) FROM stmt_slot WHERE ident_tail IS NOT NULL AND ident_tail<>''").fetchone()[0]   # noqa: E731
    out = None
    for _ in range(3):
        t0 = tails()
        r = _process_once(con, verbose)
        out = r if out is None else dict(placed=out["placed"] + r["placed"], read=out["read"] + r["read"], refused=out["refused"] + r["refused"],
                                         skipped=out["skipped"] + r["skipped"], unplaced=r["unplaced"])
        if tails() == t0 or not r["unplaced"]:
            break
    if own:
        con.close()
    return out
''', '''def _secret_count(con):
    try:
        return con.execute("SELECT COUNT(*) FROM stmt_secret").fetchone()[0]
    except sqlite3.Error:
        return 0


def _db_path(con):
    try:
        return next((r[2] for r in con.execute("PRAGMA database_list") if r[1] == "main"), "") or ""
    except sqlite3.Error:
        return ""


def _unlock_locked(con, retry_all=True):
    """S412: the venv python opens every locked PDF the stored candidates fit (stmt_shelf.py unlock -- pypdf lives in the venv only).
    Returns how many opened now. Nothing runs without a stored secret AND a locked file still closed; the secret never leaves the database
    (the subprocess reads it there) and nothing of it is printed. retry_all=False tries only the files not yet marked 'no password'
    (the later passes of one run); every run's first pass tries every closed file again."""
    if not _secret_count(con):
        return 0
    extra = "" if retry_all else " AND COALESCE(read_status,'')<>'%s'" % LOCKED_NO_PW
    if not con.execute("SELECT 1 FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='')%s LIMIT 1" % extra).fetchone():
        return 0
    con.commit()
    dbp = _db_path(con)
    if not dbp or not os.path.exists(VPY):
        return 0
    try:
        r = subprocess.run([VPY, "-B", os.path.join(HERE, "stmt_shelf.py"), "unlock"], cwd=HERE,
                           env=dict(os.environ, FINANCE_DB=dbp, STMT_INBOX=INBOX, STMT_UNLOCK_FRESH=("" if retry_all else "1")),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    except Exception:                                    # noqa: BLE001
        return 0
    m = re.search(r"opened (\\d+)", r.stdout.decode("utf-8", "replace"))
    return int(m.group(1)) if m else 0


def process_inbox(con=None, verbose=False):
    """S411: identify in passes -- a file that prints only its account number (ICICI's .txt) may arrive before the statement that
    teaches the account's tail; while a pass learns a new tail, the still-unplaced files get another look (at most three passes).
    S412: after a pass, the locked PDFs get the unlock step; every file it opened gets its look in the next pass."""
    own = con is None
    con = con or _con()
    ensure(con)
    tails = lambda: con.execute("SELECT COUNT(*) FROM stmt_slot WHERE ident_tail IS NOT NULL AND ident_tail<>''").fetchone()[0]   # noqa: E731
    out = None
    first = True
    for _ in range(4):
        t0 = tails()
        r = _process_once(con, verbose)
        out = r if out is None else dict(placed=out["placed"] + r["placed"], read=out["read"] + r["read"], refused=out["refused"] + r["refused"],
                                         skipped=out["skipped"] + r["skipped"], unplaced=r["unplaced"], unlocked=out.get("unlocked", 0))
        out.setdefault("unlocked", 0)
        opened = _unlock_locked(con, retry_all=first)
        first = False
        if opened:
            out["unlocked"] += opened
            continue
        if tails() == t0 or not r["unplaced"]:
            break
    if own:
        con.close()
    return out
''', "process_inbox")
    s = rep(s, '''        lp = f["local_path"] or ""
        text, locked = _file_text(lp)
        ident = identify_text(text) if text else dict(bank="", kind="", tail="", period_from=None, period_to=None, up="", holder="")
        slot, how = place(con, ident) if text else (None, (LOCKED_NOTE if locked else ("not a readable PDF" if lp else "no file")))''', '''        lp = f.get("unlocked_path") or f["local_path"] or ""          # S412: the unlocked copy when the venv opened it
        text, locked = _file_text(lp)
        if locked and not f.get("locked"):
            con.execute("UPDATE stmt_file SET locked=1 WHERE id=?", (f["id"],))
            f["locked"] = 1
        ident = identify_text(text) if text else dict(bank="", kind="", tail="", period_from=None, period_to=None, up="", holder="")
        slot, how = place(con, ident) if text else (None, ((LOCKED_NO_PW_NOTE if _secret_count(con) else LOCKED_NOTE) if locked else ("not a readable PDF" if lp else "no file")))''', "process_once locked")
    s = rep(s, '''            out["read" if rs == "read" else ("refused" if rs.startswith("refused") else "skipped")] += 1
        else:
            out["unplaced"] += 1
            con.execute("UPDATE stmt_file SET read_status=NULL WHERE id=?", (f["id"],))''', '''            out["read" if rs == "read" else ("refused" if rs.startswith("refused") else "skipped")] += 1
        else:
            out["unplaced"] += 1
            # S412: 'locked -- no password' is the unlock step's verdict (stmt_shelf.py unlock); it stays until a new password resets it
            con.execute("UPDATE stmt_file SET read_status=? WHERE id=?", ((LOCKED_NO_PW if (locked and f.get("read_status") == LOCKED_NO_PW) else None), f["id"]))''', "process_once unplaced")
    s = rep(s, '''    locked = str(f.get("note") or "").startswith("password-protected")
    con.execute("UPDATE stmt_file SET slot_id=?, holder=?, ident_how=?, note=NULL, identified_at=? WHERE id=?", (s["id"], s["holder_label"], "the owner's tap", _now(), f["id"]))''', '''    locked = str(f.get("note") or "").startswith("password-protected") and not f.get("unlocked_path")     # S412: an opened one reads as any other
    con.execute("UPDATE stmt_file SET slot_id=?, holder=?, ident_how=?, note=NULL, identified_at=? WHERE id=?", (s["id"], s["holder_label"], "the owner's tap", _now(), f["id"]))''', "assign locked")
    # ---- cells: the branch copy first; the file dict says 'locked'
    s = rep(s, '''            "SELECT * FROM stmt_file WHERE slot_id=? AND folder<>'cards' AND period_to IS NOT NULL AND period_from<=? AND period_to>=? "
            "ORDER BY period_to DESC, id DESC", (s["id"], hi, lo))]''', '''            "SELECT * FROM stmt_file WHERE slot_id=? AND folder<>'cards' AND period_to IS NOT NULL AND period_from<=? AND period_to>=? "
            "AND COALESCE(read_status,'')<>'duplicate of branch copy' ORDER BY period_to DESC, COALESCE(locked,0) ASC, id DESC", (s["id"], hi, lo))]   # S412: the branch copy first''', "cells order")
    s = rep(s, '''                        state=state, file=(dict(id=f["id"], name=f["name"], period_from=f["period_from"], period_to=f["period_to"],
                                                read_status=f["read_status"], matched_status=f["matched_status"]) if f else None),''', '''                        state=state, file=(dict(id=f["id"], name=f["name"], period_from=f["period_from"], period_to=f["period_to"],
                                                read_status=f["read_status"], matched_status=f["matched_status"], locked=bool(f.get("locked"))) if f else None),''', "cells file")
    s = rep(s, '''                 period_from=r["period_from"], period_to=r["period_to"], why=r["note"], fetched_at=r["fetched_at"], holder=r["holder"],
                 locked=str(r["note"] or "").startswith("password-protected"))
            for r in con.execute("SELECT * FROM stmt_file WHERE slot_id IS NULL AND folder<>'all_txn' ORDER BY id DESC LIMIT 60")]
''', '''                 period_from=r["period_from"], period_to=r["period_to"], why=r["note"], fetched_at=r["fetched_at"], holder=r["holder"],
                 locked=str(r["note"] or "").startswith("password-protected"), no_password=(r["read_status"] == LOCKED_NO_PW))
            for r in con.execute("SELECT * FROM stmt_file WHERE slot_id IS NULL AND folder<>'all_txn' ORDER BY id DESC LIMIT 60")]


def secret_state(con):
    """S412: what the page may know of the passwords -- per bank: set or not, by whom, when, how many candidates. NEVER the value."""
    ensure(con)
    have = {r[0]: r for r in con.execute("SELECT bank, set_by, set_at, secret FROM stmt_secret")}
    out = []
    for bank, label in SECRET_BANKS:
        r = have.get(bank)
        n = 0
        if r:
            try:
                n = len(json.loads(r[3]))
            except (TypeError, ValueError):
                n = 1
        out.append(dict(bank=bank, label=label, set=bool(r), set_by=(r[1] if r else None), set_at=(r[2] if r else None), candidates=n))
    lk = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder<>'cards' AND locked=1 AND (unlocked_path IS NULL OR unlocked_path='')", (LOCKED_NO_PW,)).fetchone()
    opened = con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL AND unlocked_path<>''").fetchone()[0]
    return dict(banks=out, locked_open=int(lk[0] or 0), no_password=int(lk[1] or 0), opened=int(opened or 0))


def set_secret(con, bank, text, who):
    """S412: the owner's candidates for one bank (one per line, at most 10, 64 chars each) replace what was stored; the log says set /
    replaced without the value; the locked files still closed are retried at once. Returns (body, code) -- the body never carries the value."""
    ensure(con)
    bank = str(bank or "").upper().strip()[:8]
    cands = []
    for ln in str(text or "").splitlines():
        ln = ln.strip()
        if ln and ln[:64] not in cands:
            cands.append(ln[:64])
    if bank not in {b for b, _ in SECRET_BANKS} or not cands or len(cands) > 10:
        return dict(ok=False, error="bad_request"), 400
    had = con.execute("SELECT 1 FROM stmt_secret WHERE bank=?", (bank,)).fetchone() is not None
    con.execute("INSERT INTO stmt_secret (bank, secret, set_by, set_at) VALUES (?,?,?,?) ON CONFLICT(bank) DO UPDATE SET secret=excluded.secret, "
                "set_by=excluded.set_by, set_at=excluded.set_at", (bank, json.dumps(cands), who, _now()))
    con.execute("INSERT INTO stmt_secret_log (bank, action, who, at) VALUES (?,?,?,?)", (bank, ("replaced" if had else "set"), who, _now()))
    con.execute("UPDATE stmt_file SET read_status=NULL WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='')")
    con.commit()
    res = process_inbox(con)
    return dict(ok=True, bank=bank, action=("replaced" if had else "set"), candidates=len(cands), result=res, secrets=secret_state(con)), 200
''', "unplaced + secrets")
    # ---- the Needs-you line
    s = rep(s, '''        op = open_items(con, m)
        if op:
            out.append(dict(cls="warn", target="bank", text="Shavez's month-end checklist for %s: %d item%s open" % (_month_name(m), len(op), "" if len(op) == 1 else "s")))
        return out''', '''        op = open_items(con, m)
        if op:
            out.append(dict(cls="warn", target="bank", text="Shavez's month-end checklist for %s: %d item%s open" % (_month_name(m), len(op), "" if len(op) == 1 else "s")))
        # S412: locked Yes Bank e-statements waiting -- only when the previous month's Yes Bank cell is empty on BOTH routes (no branch copy either)
        if any(c["bank"] == "YES" for c in empty):
            lk = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder='bank' AND locked=1 AND (unlocked_path IS NULL OR unlocked_path='')", (LOCKED_NO_PW,)).fetchone()
            n_lk, n_np = int(lk[0] or 0), int(lk[1] or 0)
            if n_lk and not _secret_count(con):
                out.append(dict(cls="warn", target="bank", text="Yes Bank statements need their password on the packs page (%d locked file%s waiting)" % (n_lk, "" if n_lk == 1 else "s")))
            elif n_lk and n_np:
                out.append(dict(cls="warn", target="bank", text="the stored Yes Bank password opens none of %d locked statement%s -- replace it on the packs page" % (n_np, "" if n_np == 1 else "s")))
        return out''', "needs you")
    # ---- api/state carries the passwords' state (never a value); the secret route
    s = rep(s, '''                   amir=amir_pack(con, m), checklist=checklist(con, m), items=[dict(r) for r in con.execute("SELECT * FROM packs_item ORDER BY sort, id")],
                   inbox_dir=INBOX, today=_today().isoformat())''', '''                   amir=amir_pack(con, m), checklist=checklist(con, m), items=[dict(r) for r in con.execute("SELECT * FROM packs_item ORDER BY sort, id")],
                   inbox_dir=INBOX, today=_today().isoformat(), secrets=secret_state(con))


@bp.route("/finance/packs/api/secret", methods=["POST"])
def api_secret():
    """S412: the owner types a bank's statement password(s) once -- stored in finance.db only, never echoed, never logged; the locked
    files are tried at once. The answer carries counts and 'set on', never the value."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    body, code = set_secret(_db(), b.get("bank"), b.get("text"), _who(u))
    return jsonify(**body), code''', "api state + secret")
    return s


# ============================================================================ packs.html
def build_html(s):
    s = rep(s, '''     with the one-tap 'which account?'). Everything from /finance/packs/api/state. -->''', '''     with the one-tap 'which account?'). Everything from /finance/packs/api/state.
     S412: the 'Statement passwords' card -- the owner types Yes Bank's statement password once (masked, one candidate per line); the page
     shows only 'set on <date>' and Replace, never the value; the shelf opens the locked PDFs itself. -->''', "html header")
    s = rep(s, '''input,select{padding:6px;font-size:14px;border:1px solid #c9c5bb;border-radius:6px}
</style>''', '''input,select{padding:6px;font-size:14px;border:1px solid #c9c5bb;border-radius:6px}
textarea.sec{-webkit-text-security:disc;font-family:monospace;font-size:14px;border:1px solid #c9c5bb;border-radius:6px;padding:6px;width:260px;vertical-align:middle}
</style>''', "html style")
    s = rep(s, '''<div id="unplaced"></div></div>
<div class="card"><h2>Accountant pack</h2>''', '''<div id="unplaced"></div></div>
<div class="card"><h2>Statement passwords</h2>
<div class="mut">For the banks that send password-locked PDFs (Yes Bank's monthly e-statements). Typed once, kept on the server only, never shown again, never in any mail or log.
 Yes Bank usually uses the customer ID or a date pattern — type every candidate you know, one per line; the shelf tries each on every locked file, tonight and every night, until it opens.
 The branch's own statements (not locked) stay the first source; a locked copy of a month the branch already sent is marked a duplicate.</div>
<div id="secrets"></div></div>
<div class="card"><h2>Accountant pack</h2>''', "html card")
    s = rep(s, '''(f.read_status&&f.read_status!=="read"?' · '+esc(f.read_status):'')+'</span> <a href="/finance/packs/file/'+f.id+'" target="_blank">open</a>')''',
            '''(f.read_status&&f.read_status!=="read"?' · '+esc(f.read_status):'')+(f.locked?' · opened from the locked e-statement':'')+'</span> <a href="/finance/packs/file/'+f.id+'" target="_blank">open</a>')''', "html cell")
    s = rep(s, '''(x.holder?esc(x.holder):(x.locked?'<span class="warn">locked — password needed</span>':'<span class="mut">—</span>'))''',
            '''(x.holder?esc(x.holder):(x.locked?'<span class="warn">'+(x.no_password?'locked — the stored password does not open it':'locked — password needed (Statement passwords, below)')+'</span>':'<span class="mut">—</span>'))''', "html unplaced")
    s = rep(s, '''    $("rows").innerHTML='<table><tr><th>Item</th><th>Status</th><th>Why / detail</th><th>Preview</th></tr>'+j.rows.map(function(r){''', '''    var sc=j.secrets||{banks:[]};
    $("secrets").innerHTML='<table><tr><th>Bank</th><th>Password</th><th></th></tr>'+sc.banks.map(function(b){return '<tr><td><b>'+esc(b.label)+'</b></td><td>'+(b.set?'<span class="ok">set</span> <span class="mut">on '+esc((b.set_at||"").slice(0,16).replace("T"," "))+' by '+esc(b.set_by||"")+' · '+b.candidates+' candidate'+(b.candidates===1?'':'s')+'</span>':'<span class="warn">not set</span>')+
      '</td><td><textarea class="sec" id="sec_'+esc(b.bank)+'" rows="2" placeholder="one candidate per line" autocomplete="off"></textarea> <button class="ghost" onclick="setSecret(\\''+esc(b.bank)+'\\')">'+(b.set?'Replace':'Set')+'</button></td></tr>'}).join("")+'</table>'+
      '<div class="mut" style="margin-top:6px">Locked files still closed: '+sc.locked_open+(sc.no_password?' ('+sc.no_password+' that no stored password opens)':'')+' · opened by the shelf so far: '+sc.opened+'</div>';
    $("rows").innerHTML='<table><tr><th>Item</th><th>Status</th><th>Why / detail</th><th>Preview</th></tr>'+j.rows.map(function(r){''', "html secrets render")
    s = rep(s, '''function assign(fid){var s=$("sl"+fid).value;''', '''/* S412: the password goes to the server once and is cleared from the box; the answer carries counts, never the value */
function setSecret(bank){var t=$("sec_"+bank).value; if(!t.trim()){alert("type at least one candidate");return}
  post("/finance/packs/api/secret",{bank:bank,text:t}).then(function(j){$("sec_"+bank).value=""; if(!j.ok){alert(j.message||j.error||"not saved");return}
    var r=j.result||{}; flash("Password "+j.action+" for "+bank+" ("+j.candidates+" candidate"+(j.candidates===1?"":"s")+") · opened now: "+(r.unlocked||0)+", read: "+(r.read||0)+", still unplaced: "+(r.unplaced||0)+"."); load();});}
function assign(fid){var s=$("sl"+fid).value;''', "html setSecret")
    return s


# ============================================================================ stmt_shelf.py
def build_shelf(s):
    s = rep(s, '''    stmt_shelf.py run          fetch + identify (the cron line)
    stmt_shelf.py status       what the shelf holds, one line per slot-month (read-only)
"""''', '''    stmt_shelf.py run          fetch + identify (the cron line)
    stmt_shelf.py status       what the shelf holds, one line per slot-month (read-only)
    stmt_shelf.py unlock       S412: open every password-locked PDF the owner's stored candidates fit (stmt_secret, read from the
                               database here -- never an argument, never printed) into <inbox>/<id>.unlocked.pdf with pypdf (this venv
                               only; RC4 and AES-256 alike); a file nothing opens is marked 'locked -- no password'. Prints counts only.
                               packs.process_inbox() calls this under the venv python after each identification pass.
"""''', "shelf doc")
    s = rep(s, '''       " fetched_at TEXT, local_path TEXT, bank TEXT, holder TEXT, tail TEXT, kind TEXT, ident_how TEXT, note TEXT, identified_at TEXT)")
''', '''       " fetched_at TEXT, local_path TEXT, bank TEXT, holder TEXT, tail TEXT, kind TEXT, ident_how TEXT, note TEXT, identified_at TEXT,"
       " locked INTEGER NOT NULL DEFAULT 0, unlocked_path TEXT, unlocked_at TEXT)")
S412_COLS = (("locked", "INTEGER NOT NULL DEFAULT 0"), ("unlocked_path", "TEXT"), ("unlocked_at", "TEXT"))
LOG_DDL_S412 = "CREATE TABLE IF NOT EXISTS stmt_secret_log (id INTEGER PRIMARY KEY, bank TEXT NOT NULL, action TEXT NOT NULL, who TEXT, at TEXT)"
LOCKED_NO_PW = "locked -- no password"


def _cols(con):
    """S412: the shelf columns on a table made before this kit."""
    have = {r[1] for r in con.execute("PRAGMA table_info(stmt_file)")}
    for c, d in S412_COLS:
        if c not in have:
            con.execute("ALTER TABLE stmt_file ADD COLUMN %s %s" % (c, d))


def unlock(con):
    """S412: open every locked PDF still closed with the stored candidates. Returns (opened, still_locked, candidates). The candidates
    are read from stmt_secret here and go nowhere else: not to a log line, not to a file name, not to the return value."""
    con.execute(DDL)
    _cols(con)
    con.execute(LOG_DDL_S412)
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='stmt_secret'").fetchone():
        return 0, 0, 0
    cands = []
    for bank, sec in con.execute("SELECT bank, secret FROM stmt_secret ORDER BY bank"):
        try:
            lst = json.loads(sec)
        except (TypeError, ValueError):
            lst = [sec]
        cands += [(bank, str(c)) for c in (lst if isinstance(lst, list) else [lst]) if str(c).strip()]
    fresh = " AND COALESCE(read_status,'')<>'%s'" % LOCKED_NO_PW if os.environ.get("STMT_UNLOCK_FRESH") == "1" else ""
    rows = con.execute("SELECT id, local_path FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='')%s ORDER BY id" % fresh).fetchall()
    if not cands or not rows:
        return 0, len(rows), len(cands)
    from pypdf import PdfReader, PdfWriter                # noqa: PLC0415  (the venv only)
    os.makedirs(INBOX, exist_ok=True)
    opened = 0
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    for fid, lp in rows:
        if not lp or not os.path.exists(lp):
            continue
        out = os.path.join(INBOX, "%d.unlocked.pdf" % fid)
        got = None
        for bank, pw in cands:
            try:
                rd = PdfReader(lp)
                if rd.is_encrypted and not rd.decrypt(pw):
                    continue
                wr = PdfWriter(clone_from=rd)
                with open(out, "wb") as fh:
                    wr.write(fh)
                got = bank
                break
            except Exception:                            # noqa: BLE001  (a wrong candidate, a damaged file: the next one)
                if os.path.exists(out):
                    os.remove(out)
                continue
        if got:
            con.execute("UPDATE stmt_file SET unlocked_path=?, unlocked_at=?, read_status=NULL, note=NULL WHERE id=?", (out, now, fid))
            con.execute("INSERT INTO stmt_secret_log (bank, action, who, at) VALUES (?,?,?,?)", (got, "opened file %d" % fid, "shelf", now))
            opened += 1
        else:
            con.execute("UPDATE stmt_file SET read_status=? WHERE id=?", (LOCKED_NO_PW, fid))
    con.commit()
    return opened, len(rows) - opened, len(cands)
''', "shelf unlock")
    s = rep(s, '''    if what != "run":
        print(__doc__)
        return 2''', '''    if what == "unlock":
        o, still, nc = unlock(con)
        log("unlock: opened %d, still locked %d, candidates %d" % (o, still, nc))
        return 0
    if what != "run":
        print(__doc__)
        return 2''', "shelf main")
    return s


# ============================================================================ finance_icici.py
def build_icici(s):
    s = rep(s, '''The account is kept as its last four digits only (F-607).
"""''', '''The account is kept as its last four digits only (F-607).

S412: a pipe .txt whose header period is DEGENERATE (from == to -- ICICI prints the day it was generated) takes its rows' first and last
dates as the period, and the proof says so; the ICICI anchor never moves on it (packs._anchor_refresh, closing_printed False).
"""''', "icici doc")
    s = rep(s, '''    if not pf:
        pf, pt = lines[0]["txn_date"], lines[-1]["txn_date"]
    return dict(account_ref=acct, period_from=pf, period_to=pt, opening_p=opening, closing_p=prev, lines=lines, layout="pipe",
                closing_printed=False, proof="B/F + %d rows = every running balance; no closing is printed in this format, the last running balance stands" % len(lines))''',
            '''    widened = ""
    if not pf or not pt or pf == pt:                       # S412: no header period, or a degenerate one -> the rows' first and last dates
        dates = sorted(l["txn_date"] for l in lines)
        widened = "; the header period was %s, widened to the rows %s..%s" % (("%s..%s" % (pf, pt)) if pf else "missing", dates[0], dates[-1])
        pf, pt = dates[0], dates[-1]
    return dict(account_ref=acct, period_from=pf, period_to=pt, opening_p=opening, closing_p=prev, lines=lines, layout="pipe",
                closing_printed=False, proof="B/F + %d rows = every running balance; no closing is printed in this format, the last running balance stands%s" % (len(lines), widened))''', "icici pipe period")
    return s


# ============================================================================ finance_yesbank.py
def build_yesbank(s):
    s = rep(s, '''def ingest_statement(con, filename, blob, store_dir=None, now=None):
    """Parse + store one statement. Idempotent on (account, date, ref, amounts).
    Never half-ingests: the parse either succeeds whole or raises."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()''', '''def ingest_statement(con, filename, blob, store_dir=None, now=None, tables=None):
    """Parse + store one statement. Idempotent on (account, date, ref, amounts).
    Never half-ingests: the parse either succeeds whole or raises.
    S412 (declared): tables=(period_table, line_table) names the pair to write; the default is the shared
    bank_statement_period / bank_statement_line (Sanjeevni's). The statement shelf passes the per-account pair
    for the non-Sanjeevni Yes Bank accounts, whose lines must never reach the shared tables."""
    ptab, ltab = tables or ("bank_statement_period", "bank_statement_line")
    if not (re.match(r"^[a-z_]+$", ptab) and re.match(r"^[a-z_]+$", ltab)):
        raise StatementRejected("the table pair must be plain identifiers")
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()''', "yesbank signature")
    s = rep(s, '''        "INSERT INTO bank_statement_period (account_ref, period_from, period_to, opening_p,"
        " closing_p, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?) "''', '''        "INSERT INTO " + ptab + " (account_ref, period_from, period_to, opening_p,"
        " closing_p, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?) "''', "yesbank period insert")
    s = rep(s, '''            "INSERT OR IGNORE INTO bank_statement_line (account_ref, txn_date, value_date,"''', '''            "INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date,"''', "yesbank line insert")
    return s


BUILDERS = {"packs.py": build_packs, "packs.html": build_html, "stmt_shelf.py": build_shelf, "finance_icici.py": build_icici, "finance_yesbank.py": build_yesbank}


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance", "/root/finance"), args.get("--out")
    if not out:
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    for name, fn in BUILDERS.items():
        src = os.path.join(fin, name)
        built = fn(load(src, name))
        if not built.endswith("\n"):
            built += "\n"
        b = built.encode("utf-8")
        with io.open(os.path.join(out, name), "wb") as fh:
            fh.write(b)
        print("built %s  %s -> %s  (%d bytes)" % (name, FROM[name][:8], md5(b), len(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
