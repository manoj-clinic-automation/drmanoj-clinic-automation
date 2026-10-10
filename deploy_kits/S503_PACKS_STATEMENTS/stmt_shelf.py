#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""stmt_shelf.py -- S408 (26-Sep-2026, D624). The statement shelf's fetcher: nightly at 05:40 IST (root cron, declared) and
on demand. Lists Drive / Clinic Data Archive / Bank Statements / <year> and Credit Card Statements (the three card folders =
the password-locked originals; Decrypted/<card> = the readable ones; All_Transactions.xlsx), fetches every file not yet on the
shelf into /root/finance/statements/inbox/<drive id>.<ext>, records it in stmt_file (drive_id, name, mtime, size, folder,
sha256, fetched_at, local_path), then hands the inbox to packs.process_inbox() under the app's python, which identifies each
file BY ITS CONTENT (pdftotext) against stmt_slot -- never by file name, subject or sender.

Runs under the venv python (the only one with the Google libraries), through the same service account records_drive.py uses.
Read-only on Drive. STMT_DRIVE_STUB=<dir> serves the walk: <dir>/bank/<year>/*, <dir>/cards/<card>/*, <dir>/decrypted/<card>/*,
<dir>/all_transactions.xlsx stand in for the four Drive places; nothing is downloaded.

    stmt_shelf.py run          fetch + identify (the cron line)
    stmt_shelf.py status       what the shelf holds, one line per slot-month (read-only)
    stmt_shelf.py unlock       S412: open every password-locked PDF the owner's stored candidates fit (stmt_secret, read from the
                               database here -- never an argument, never printed) into <inbox>/<id>.unlocked.pdf with pypdf (this venv
                               only; RC4 and AES-256 alike); a file nothing opens is marked 'locked -- no password'. Prints counts only.
                               packs.process_inbox() calls this under the venv python after each identification pass.

S417 (F-636): an .xlsx in the Credit Card Statements root is recorded as the running Excel (folder all_txn), never as a card file.
S503 (10-Oct-2026): the running Excel is fetched AGAIN whenever Drive's copy changes (it is rebuilt in place, so its id never
changes and the old 'once per id' rule left the shelf on its first copy for ever); a locked file the owner set aside is never tried.
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

FIN = os.environ.get("FINANCE_DIR", "/root/finance")
DB = os.environ.get("FINANCE_DB", os.path.join(FIN, "finance.db"))
INBOX = os.environ.get("STMT_INBOX", os.path.join(FIN, "statements", "inbox"))
SPY = os.environ.get("STMT_APP_PYTHON", "/usr/bin/python3")
BANK_ROOT = os.environ.get("STMT_BANK_FOLDER", "1wGzaXnCoKcILw1VSv3UGYfQlVTl78UgT")
CARDS_ROOT = os.environ.get("STMT_CARDS_FOLDER", "1XpDt8YMovgMBivMC4_aBvK_gwTESCAA6")
DECRYPTED = os.environ.get("STMT_DECRYPTED_FOLDER", "1LOSA173EQPF5IvWK3ISksS1Qjh9DUXiV")
ALL_TXN = os.environ.get("STMT_ALL_TXN_FILE", "1-DGksJHegCC0Md6uDDRCP8Z9w3uxeqv0")
STUB = os.environ.get("STMT_DRIVE_STUB", "")
FOLDER_MIME = "application/vnd.google-apps.folder"

DDL = ("CREATE TABLE IF NOT EXISTS stmt_file ("
       " id INTEGER PRIMARY KEY, drive_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, mtime TEXT, size INTEGER, folder TEXT NOT NULL,"
       " subfolder TEXT, slot_id INTEGER, period_from TEXT, period_to TEXT, read_status TEXT, matched_status TEXT, sha256 TEXT,"
       " fetched_at TEXT, local_path TEXT, bank TEXT, holder TEXT, tail TEXT, kind TEXT, ident_how TEXT, note TEXT, identified_at TEXT,"
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
    # S471: an account's own password ('YES:<slot key>') is tried before a bank-wide one
    for bank, sec in con.execute("SELECT bank, secret FROM stmt_secret ORDER BY CASE WHEN instr(bank, ':') > 0 THEN 0 ELSE 1 END, bank"):
        try:
            lst = json.loads(sec)
        except (TypeError, ValueError):
            lst = [sec]
        cands += [(bank, str(c)) for c in (lst if isinstance(lst, list) else [lst]) if str(c).strip()]
    fresh = " AND COALESCE(read_status,'')<>'%s'" % LOCKED_NO_PW if os.environ.get("STMT_UNLOCK_FRESH") == "1" else ""
    rows = con.execute("SELECT id, local_path FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='') "
                       "AND COALESCE(read_status,'')<>'set aside'%s ORDER BY id" % fresh).fetchall()       # S503: the owner's set-aside files are left alone
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


def log(msg):
    sys.stdout.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    sys.stdout.flush()


# ---------------------------------------------------------------- Drive (or the stub)
def _drive():
    sys.path.insert(0, FIN)
    import records_drive as rd                          # noqa: PLC0415
    import requests                                     # noqa: PLC0415
    h = rd.headers()

    def kids(fid):
        out, tok = [], None
        while True:
            params = {"q": "'%s' in parents and trashed=false" % fid, "pageSize": 200, "supportsAllDrives": "true",
                      "includeItemsFromAllDrives": "true", "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime)"}
            if tok:
                params["pageToken"] = tok
            r = requests.get(rd.API, params=params, headers=h, timeout=60)
            if r.status_code != 200:
                raise RuntimeError("Drive said %s for folder %s" % (r.status_code, fid[:8]))
            j = r.json()
            out += j.get("files", [])
            tok = j.get("nextPageToken")
            if not tok:
                return out

    def media(fid):
        r = requests.get(rd.API + "/" + fid, params={"alt": "media", "supportsAllDrives": "true"}, headers=h, timeout=180)
        if r.status_code != 200:
            raise RuntimeError("Drive said %s for file %s" % (r.status_code, fid[:8]))
        return r.content

    def meta(fid):
        r = requests.get(rd.API + "/" + fid, params={"fields": "id,name,mimeType,size,modifiedTime", "supportsAllDrives": "true"}, headers=h, timeout=60)
        return r.json() if r.status_code == 200 else None
    return kids, media, meta


def _stub():
    def kids(fid):
        d = fid
        if not os.path.isdir(d):
            return []
        out = []
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            st = os.stat(p)
            out.append(dict(id=p, name=n, mimeType=(FOLDER_MIME if os.path.isdir(p) else "application/octet-stream"),
                            size=str(st.st_size), modifiedTime=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(st.st_mtime))))
        return out

    def media(fid):
        with open(fid, "rb") as fh:
            return fh.read()

    def meta(fid):
        if not os.path.isfile(fid):
            return None
        st = os.stat(fid)
        return dict(id=fid, name=os.path.basename(fid), mimeType="application/octet-stream", size=str(st.st_size),
                    modifiedTime=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(st.st_mtime)))
    return kids, media, meta


def places():
    """(label, folder id, subfolder-walk?) -- the four Drive places; the stub's four directories."""
    if STUB:
        return [("bank", os.path.join(STUB, "bank"), True), ("cards", os.path.join(STUB, "cards"), True),
                ("decrypted", os.path.join(STUB, "decrypted"), True)], os.path.join(STUB, "all_transactions.xlsx")
    return [("bank", BANK_ROOT, True), ("cards", CARDS_ROOT, True), ("decrypted", DECRYPTED, True)], ALL_TXN


def sha(b):
    return hashlib.sha256(b).hexdigest()


def _folder_s417(label, sub, name):
    """S417 (F-636): an .xlsx / .xls in the Credit Card Statements ROOT is the running Excel (All_Transactions) -- folder all_txn, never
    a card statement waiting to be placed."""
    return "all_txn" if (label == "cards" and not sub and str(name or "").lower().endswith((".xlsx", ".xls"))) else label


def fetch(con):
    """List the places, fetch what the shelf does not hold, record it. Returns (new, seen, errors)."""
    kids, media, meta = _stub() if STUB else _drive()
    con.execute(DDL)
    os.makedirs(INBOX, exist_ok=True)
    have = {r[0] for r in con.execute("SELECT drive_id FROM stmt_file")}
    new, seen, errors = 0, 0, []
    plist, all_txn = places()
    for label, root, walk in plist:
        try:
            top = kids(root)
        except Exception as ex:                          # noqa: BLE001
            errors.append("%s: %s" % (label, str(ex)[:120]))
            continue
        entries = []
        for k in top:
            if k["mimeType"] == FOLDER_MIME and walk:
                try:
                    for s in kids(k["id"]):
                        if s["mimeType"] != FOLDER_MIME:
                            entries.append((k["name"], s))
                except Exception as ex:                  # noqa: BLE001
                    errors.append("%s/%s: %s" % (label, k["name"][:30], str(ex)[:100]))
            elif k["mimeType"] != FOLDER_MIME:
                if label == "cards" and k["name"].lower().endswith(".xlsx"):
                    entries.append(("", k))              # All_Transactions.xlsx sits beside the card folders
                elif label != "cards":
                    entries.append(("", k))
        for sub, f in entries:
            seen += 1
            if f["id"] in have:
                continue
            try:
                blob = media(f["id"])
            except Exception as ex:                      # noqa: BLE001
                errors.append("%s: %s" % (f["name"][:40], str(ex)[:100]))
                continue
            ext = (f["name"].rsplit(".", 1)[-1].lower() if "." in f["name"] else "bin")[:5]
            local = os.path.join(INBOX, "%s.%s" % (re.sub(r"[^A-Za-z0-9_-]", "_", os.path.basename(f["id"]))[:80], ext))
            with open(local, "wb") as fh:
                fh.write(blob)
            con.execute("INSERT OR IGNORE INTO stmt_file (drive_id, name, mtime, size, folder, subfolder, sha256, fetched_at, local_path) "
                        "VALUES (?,?,?,?,?,?,?,?,?)", (f["id"], f["name"][:200], (f.get("modifiedTime") or "")[:19], int(f.get("size") or 0),
                                                       _folder_s417(label, sub, f["name"]), sub[:80], sha(blob), time.strftime("%Y-%m-%dT%H:%M:%S"), local))
            new += 1
    if all_txn:
        m = None
        try:
            m = meta(all_txn)
        except Exception as ex:                          # noqa: BLE001
            errors.append("All_Transactions.xlsx: %s" % str(ex)[:100])
        if m and m["id"] not in have:
            try:
                blob = media(m["id"])
                local = os.path.join(INBOX, "all_transactions.xlsx")
                with open(local, "wb") as fh:
                    fh.write(blob)
                con.execute("INSERT OR IGNORE INTO stmt_file (drive_id, name, mtime, size, folder, subfolder, sha256, fetched_at, local_path) "
                            "VALUES (?,?,?,?,?,?,?,?,?)", (m["id"], m["name"][:200], (m.get("modifiedTime") or "")[:19], int(m.get("size") or 0),
                                                           "all_txn", "", sha(blob), time.strftime("%Y-%m-%dT%H:%M:%S"), local))
                new += 1
            except Exception as ex:                      # noqa: BLE001
                errors.append("All_Transactions.xlsx: %s" % str(ex)[:100])
        elif m and m["id"] in have:
            seen += 1
            old = con.execute("SELECT mtime, size FROM stmt_file WHERE drive_id=?", (m["id"],)).fetchone()     # S503: rebuilt in place -> fetched again
            if old and ((m.get("modifiedTime") or "")[:19] != (old[0] or "") or int(m.get("size") or 0) != int(old[1] or 0)):
                try:
                    blob = media(m["id"])
                    local = os.path.join(INBOX, "all_transactions.xlsx")
                    with open(local, "wb") as fh:
                        fh.write(blob)
                    con.execute("UPDATE stmt_file SET name=?, mtime=?, size=?, sha256=?, fetched_at=?, local_path=? WHERE drive_id=?",
                                (m["name"][:200], (m.get("modifiedTime") or "")[:19], int(m.get("size") or 0), sha(blob), time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 local, m["id"]))
                    new += 1
                except Exception as ex:                  # noqa: BLE001
                    errors.append("All_Transactions.xlsx (refresh): %s" % str(ex)[:100])
    con.commit()
    return new, seen, errors


def identify():
    """packs.process_inbox() under the app's python (it needs no Google library; it needs pdftotext and the app's readers)."""
    env = dict(os.environ, FINANCE_DB=DB)
    p = subprocess.run([SPY, "-B", "-c", "import sys; sys.path.insert(0, %r); import packs; print(packs.process_inbox(None, verbose=True))" % FIN],
                       cwd=FIN, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)
    return p.returncode, (p.stdout or "").strip()[-2000:], (p.stderr or "").strip()[-800:]


def main(argv):
    what = argv[1] if len(argv) > 1 else "run"
    con = sqlite3.connect(DB, timeout=60)
    if what == "status":
        con.execute(DDL)
        for r in con.execute("SELECT folder, subfolder, name, period_from, period_to, read_status, matched_status, slot_id FROM stmt_file ORDER BY folder, name"):
            print(" | ".join(str(x) for x in r))
        return 0
    if what == "unlock":
        o, still, nc = unlock(con)
        log("unlock: opened %d, still locked %d, candidates %d" % (o, still, nc))
        return 0
    if what != "run":
        print(__doc__)
        return 2
    new, seen, errors = fetch(con)
    log("fetch: %d new, %d seen%s" % (new, seen, ("; errors: " + " · ".join(errors)) if errors else ""))
    rc, out, err = identify()
    log("identify (rc %d): %s%s" % (rc, out, (" | " + err) if err else ""))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
