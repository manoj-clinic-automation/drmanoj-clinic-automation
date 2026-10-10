"""S503 builder: packs.py (9f897eeb) -> S503, anchored edits on the live bytes, each anchor asserted exactly once."""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == '9f897eeb70bc65d1414985058e378310', 'FROM pin differs'
t = b.decode('utf-8')
def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:80])
    t = t.replace(old, new)

# E1 -- the kit's paragraph in the module's own record
rep('''the shelf opened (_best_path) -- the locked original is something only the owner can read.
"""
import datetime as dt''', '''the shelf opened (_best_path) -- the locked original is something only the owner can read.

S503 (10-Oct-2026, the owner: "passwords for ICICI and the cards on our own page, read both kinds, name what is locked"):
  * Yes Bank's CONSOLIDATED statement is read (yes_monthly.py 1.3); a file a reader REFUSED is offered again by itself whenever a
    reader is newer than the refusal (_retry_refused) -- the one-time correction is part of the design, not a step for anyone.
  * the passwords card has a box per ICICI account and per CARD as well as per Yes Bank account; a locked card original with no
    decrypted twin is opened by the shelf itself and stands as the month's card statement (nothing waits on an outside script).
  * the card names every locked file still closed, in words ('ICICI e-statement, Sep 2026'), and the owner may set one aside
    ('set aside': never tried, never counted, put back with one tap).
  * a second copy of an ICICI account-month (the bank's e-statement beside the branch's or the net-banking one) is CHECKED against
    the copy already read and never written twice; each cell shows every copy of its month side by side, and the pack uses one.
"""
import datetime as dt''')

# E2 -- constants
rep('''SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"))       # the banks that send locked PDFs (Yes Bank now)''',
    '''SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"))       # the banks that send locked PDFs (Yes Bank now)
SET_ASIDE = "set aside"                                              # S503: the owner's tap -- a locked file never tried, never counted
READERS = ("yes_monthly.py", "yes_branch.py", "finance_yesbank.py", "finance_icici.py", "packs.py")   # S503: a newer reader retries a refusal''')

# E3 -- secret keys: Yes accounts, ICICI accounts, cards, then the banks
rep('''    for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE bank='YES' AND kind<>'card' ORDER BY sort"):
        if r[0] not in retired:
            out.append(("YES:" + r[0], r[1], True))
    out += [(b, l + " (any other)", False) for b, l in SECRET_BANKS]''',
    '''    for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE bank='YES' AND kind<>'card' ORDER BY sort"):
        if r[0] not in retired:
            out.append(("YES:" + r[0], r[1], True))
    for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE bank='ICICI' AND kind<>'card' ORDER BY sort"):   # S503
        if r[0] not in retired:
            out.append(("ICICI:" + r[0], r[1], True))
    for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE kind='card' ORDER BY sort"):                     # S503
        if r[0] not in retired:
            out.append(("CARD:" + r[0], r[1], True))
    out += [(b, l + " (any other)", False) for b, l in SECRET_BANKS]''')

# E4 -- secret_state: counts without the set-aside files; the locked files named
rep('''    lk = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder<>'cards' AND locked=1 AND (unlocked_path IS NULL OR unlocked_path='')", (LOCKED_NO_PW,)).fetchone()
    opened = con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL AND unlocked_path<>''").fetchone()[0]
    return dict(banks=out, locked_open=int(lk[0] or 0), no_password=int(lk[1] or 0), opened=int(opened or 0))''',
    '''    lk = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='') "
                     "AND COALESCE(read_status,'')<>?", (LOCKED_NO_PW, SET_ASIDE)).fetchone()
    opened = con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL AND unlocked_path<>''").fetchone()[0]
    files, aside = _locked_list(con)                                  # S503: every closed file named, in words
    return dict(banks=out, locked_open=int(lk[0] or 0), no_password=int(lk[1] or 0), opened=int(opened or 0), locked_files=files, set_aside=aside)


def _copy_kind(name, folder=""):
    """S503: what a file IS, in words, from the shape of its name only (used to name a copy -- never to place or read a file)."""
    n = str(name or "")
    m = re.search(r"Statement_(\\d{4})MTH(\\d{2})_", n)
    if m:
        return "ICICI e-statement, %s" % _month_name("%s-%s" % (m.group(1), m.group(2)))
    if re.search(r"_YFB?_quarterly", n, re.I):
        return "Yes Bank quarterly statement"
    if re.search(r"\\bCS_\\d+_", n):
        return "Yes Bank consolidated e-statement"
    if "CASA_" in n:
        return "Yes Bank monthly e-statement"
    if folder == "cards":
        return "card statement (locked original)"
    if re.search(r"_0192\\d{8}_\\d{4}-\\d{2}-\\d{2}_\\d{4}-\\d{2}-\\d{2}_", n):
        return "ICICI net-banking statement"
    if n.lower().endswith(".txt"):
        return "ICICI text statement"
    return "branch statement"


def _locked_list(con):
    """S503: the locked files still closed (and the ones the owner set aside), each named in words, its account number masked."""
    files, aside = [], []
    for r in con.execute("SELECT id, name, folder, subfolder, fetched_at, read_status, note FROM stmt_file WHERE locked=1 AND "
                         "(unlocked_path IS NULL OR unlocked_path='') ORDER BY id"):
        d = dict(id=r[0], name=re.sub(r"\\d{6,}", lambda m: "x" + m.group(0)[-4:], r[1] or ""), what=_copy_kind(r[1], r[2]),
                 card=r[3] if r[2] == "cards" else "", arrived=(r[4] or "")[:10], why=(r[6] or "") if r[5] == SET_ASIDE else
                 ("no stored password opens it yet" if r[5] == LOCKED_NO_PW else "waiting for its first try"))
        (aside if r[5] == SET_ASIDE else files).append(d)
    return files, aside


def set_aside(con, fid, back, who, why=""):
    """S503: the owner's tap on a locked file -- 'set aside' (never tried, never counted) or put back (tried again on the next run)."""
    ensure(con)
    r = con.execute("SELECT id, locked, unlocked_path, read_status FROM stmt_file WHERE id=?", (fid,)).fetchone()
    if not r:
        return dict(ok=False, error="no_such"), 404
    if not r[1] or r[2]:
        return dict(ok=False, error="not_a_closed_locked_file"), 400
    if back:
        con.execute("UPDATE stmt_file SET read_status=NULL, note=NULL WHERE id=? AND read_status=?", (fid, SET_ASIDE))
    else:
        con.execute("UPDATE stmt_file SET read_status=?, note=? WHERE id=?", (SET_ASIDE, ("set aside by %s %s%s" % (who, _now()[:16], (" -- " + why[:120]) if why else "")), fid))
    con.commit()
    return dict(ok=True, file=fid, set_aside=not back), 200


def _retry_refused(con):
    """S503: a file a reader refused is offered again when any reader is newer than that refusal -- so a reader that learns a layout
    reads every file it refused before, by itself (the one-time correction carried by the design). Returns how many were re-offered."""
    try:
        newest = max(os.path.getmtime(os.path.join(HERE, x)) for x in READERS if os.path.exists(os.path.join(HERE, x)))
    except ValueError:
        return 0
    stamp = dt.datetime.fromtimestamp(newest).replace(microsecond=0).isoformat()
    cur = con.execute("UPDATE stmt_file SET read_status=NULL WHERE read_status LIKE 'refused%' AND COALESCE(identified_at,'')<?", (stamp,))
    con.commit()
    return cur.rowcount or 0''')

# E5 -- a new password retries every closed file except the set-aside ones
rep('''    con.execute("UPDATE stmt_file SET read_status=NULL WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='')")''',
    '''    con.execute("UPDATE stmt_file SET read_status=NULL WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='') AND COALESCE(read_status,'')<>?", (SET_ASIDE,))''')

# E6 -- _unlock_locked: the set-aside files are not a reason to run
rep('''    if not con.execute("SELECT 1 FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='')%s LIMIT 1" % extra).fetchone():''',
    '''    if not con.execute("SELECT 1 FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='') AND COALESCE(read_status,'')<>'%s'%s LIMIT 1"
                       % (SET_ASIDE, extra)).fetchone():''')

# E7 -- process_inbox: a newer reader re-offers its refusals first
rep('''    own = con is None
    con = con or _con()
    ensure(con)
    tails = lambda:''', '''    own = con is None
    con = con or _con()
    ensure(con)
    _retry_refused(con)                                               # S503
    tails = lambda:''')

# E8 -- _process_once: a set-aside file is not looked at again
rep('''SELECT * FROM stmt_file WHERE (slot_id IS NULL AND COALESCE(read_status,'')<>?) OR read_status IS NULL ORDER BY id", (OFF_STATUS,))''',
    '''SELECT * FROM stmt_file WHERE (slot_id IS NULL AND COALESCE(read_status,'') NOT IN (?, ?)) OR read_status IS NULL ORDER BY id", (OFF_STATUS, SET_ASIDE))''')

# E9 -- a card original with no decrypted twin is the unlock step's too (S503)
rep('''        if locked and not f.get("locked") and f["folder"] != "cards":      # S417: a card's locked original is never the unlock step's''',
    '''        if locked and not f.get("locked") and (f["folder"] != "cards" or not _has_twin(con, f)):   # S503: a card original with no twin is opened by the shelf''')
rep('''def _mark_twin(con, f, slot, card):''', '''def _has_twin(con, f):
    """S503: a card original's decrypted twin (the same name in the same card's Decrypted folder) is on the shelf."""
    return con.execute("SELECT 1 FROM stmt_file WHERE folder='decrypted' AND id<>? AND LOWER(name)=LOWER(?) AND COALESCE(subfolder,'')=COALESCE(?,'') LIMIT 1",
                       (f["id"], f["name"], f.get("subfolder"))).fetchone() is not None


def _mark_twin(con, f, slot, card):''')

# E10 -- an original the shelf opened stands as the month's card statement
rep('''    sd = (card or {}).get("statement_date") or _name_date(f.get("name"))
    if sd:''', '''    if f.get("unlocked_path") and card and card.get("statement_date"):          # S503: opened by the shelf with the stored password
        con.execute("UPDATE stmt_file SET period_from=?, period_to=? WHERE id=?", (card.get("period_from"), card.get("period_to"), f["id"]))
        return "read", "statement dated %s · opened by the shelf" % _dmy(card["statement_date"])
    sd = (card or {}).get("statement_date") or _name_date(f.get("name"))
    if sd:''')

# E11 -- cells: a card's month may be an opened original; every copy of a bank month is shown beside the one used
rep('''            fs = [dict(r) for r in con.execute("SELECT * FROM stmt_file WHERE slot_id=? AND folder='decrypted' AND period_to BETWEEN ? AND ? "
                                               "ORDER BY period_to DESC, id DESC", (s["id"], lo, hi))]''',
    '''            fs = [dict(r) for r in con.execute("SELECT * FROM stmt_file WHERE slot_id=? AND (folder='decrypted' OR (folder='cards' AND "
                                               "COALESCE(unlocked_path,'')<>'' AND read_status='read')) AND period_to BETWEEN ? AND ? "   # S503
                                               "ORDER BY period_to DESC, id DESC", (s["id"], lo, hi))]''')
rep('''            if orig and (not dec or (dec[0]["mtime"] or "") < (orig[0]["mtime"] or "")):''',
    '''            if orig and not (orig[0].get("unlocked_path") and orig[0].get("read_status") == "read") and (not dec or (dec[0]["mtime"] or "") < (orig[0]["mtime"] or "")):   # S503''')
rep('''                        twin_missing=twin_missing, no_decrypted=no_dec,''',
    '''                        twin_missing=twin_missing, no_decrypted=no_dec,
                        copies=([dict(id=x["id"], what=_copy_kind(x["name"], x["folder"]), read_status=x["read_status"], matched_status=x["matched_status"],
                                      period_from=x["period_from"], period_to=x["period_to"])
                                 for x in con.execute("SELECT * FROM stmt_file WHERE slot_id=? AND folder='bank' AND period_to IS NOT NULL AND period_from<=? "
                                                      "AND period_to>=? AND id<>? ORDER BY id", (s["id"], hi, lo, f["id"]))] if (f and s["kind"] != "card") else []),   # S503''')

# E12 -- ICICI: a second copy of an account-month is checked, never written twice
rep('''        elif slot["bank"] == "ICICI":
            import finance_icici                          # noqa: PLC0415
            res = finance_icici.ingest_statement(con, f["name"], blob, now=_now())''',
    '''        elif slot["bank"] == "ICICI":
            import finance_icici                          # noqa: PLC0415
            # S503: the bank's own e-statement and the branch / net-banking copy of an account are BOTH kept and shown. When another
            # read copy of the same account overlaps this one's dates, a line is written only if no line of that account already has its
            # date, amounts and running balance (the two layouts print references differently) -- so nothing is ever counted twice, and
            # the days only this copy covers are still written. Its closing is checked against a held statement ending the same day.
            parsed = finance_icici.parse_statement(blob)
            pf, pt = parsed["period_from"], parsed["period_to"]
            other = con.execute("SELECT id FROM stmt_file WHERE id<>? AND slot_id=? AND read_status='read' AND period_from<=? AND period_to>=? ORDER BY id LIMIT 1",
                                (f["id"], slot["id"], pt, pf)).fetchone()
            if other:
                finance_icici.ensure_tables(con)
                fname = re.sub(r"\\d{6,}", lambda m: "x" + m.group(0)[-4:], str(f["name"] or "icici.pdf"))[-120:]
                sha = hashlib.sha256(blob if isinstance(blob, bytes) else blob.encode()).hexdigest()
                held = con.execute("SELECT closing_p FROM %s WHERE account_ref=? AND period_to=? AND COALESCE(sha256,'')<>? ORDER BY id DESC LIMIT 1"
                                   % finance_icici.PERIOD_TABLE, (parsed["account_ref"], pt, sha)).fetchone()
                con.execute("INSERT OR IGNORE INTO %s (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at, layout, "
                            "closing_printed) VALUES (?,?,?,?,?,?,?,?,?,?)" % finance_icici.PERIOD_TABLE,
                            (parsed["account_ref"], pf, pt, parsed["opening_p"], parsed["closing_p"], fname, sha, _now(), parsed["layout"],
                             1 if parsed["closing_printed"] else 0))
                new = 0
                for ln in parsed["lines"]:
                    if con.execute("SELECT 1 FROM %s WHERE account_ref=? AND txn_date=? AND withdrawal_p=? AND deposit_p=? AND COALESCE(balance_p,-1)=COALESCE(?,-1) LIMIT 1"
                                   % finance_icici.LINE_TABLE, (parsed["account_ref"], ln["txn_date"], ln["withdrawal_p"], ln["deposit_p"], ln["balance_p"])).fetchone():
                        continue
                    cur = con.execute("INSERT OR IGNORE INTO %s (account_ref, txn_date, value_date, description, reference, withdrawal_p, deposit_p, balance_p, "
                                      "is_cash_deposit, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)" % finance_icici.LINE_TABLE,
                                      (parsed["account_ref"], ln["txn_date"], ln["value_date"], ln["description"], ln["reference"], ln["withdrawal_p"],
                                       ln["deposit_p"], ln["balance_p"], ln["is_cash_deposit"], fname, sha, _now()))
                    new += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
                con.execute("UPDATE stmt_file SET period_from=?, period_to=? WHERE id=?", (pf, pt, f["id"]))
                close = ("closing agrees (%s)" % _inr(parsed["closing_p"]) if held and parsed.get("closing_p") is not None and int(held[0] or 0) == int(parsed["closing_p"] or 0)
                         else "CLOSING DIFFERS from the statement held to the same day -- look at both" if held and held[0] is not None
                         else "no other statement ends the same day")
                return "read", "second copy beside file %d -- %d lines, %d new, %d already held; %s" % (other[0], len(parsed["lines"]), new, len(parsed["lines"]) - new, close)
            res = finance_icici.ingest_statement(con, f["name"], blob, now=_now())''')

# E13 -- the card row attaches the copy the accountants can open
rep('''            fr = con.execute("SELECT local_path FROM stmt_file WHERE id=?", (f["id"],)).fetchone()
            if fr and fr[0] and os.path.exists(fr[0]):
                with open(fr[0], "rb") as fh:''', '''            fr = _best_path(con, f["id"])                                   # S503: an original the shelf opened attaches its unlocked copy
            if fr and fr[0] and os.path.exists(fr[0]):
                with open(fr[0], "rb") as fh:''')

# E14 -- unplaced: a set-aside file is not a question
rep('''"AND LOWER(name) LIKE '%.xls%') AND COALESCE(read_status,'')<>? "''', '''"AND LOWER(name) LIKE '%.xls%') AND COALESCE(read_status,'') NOT IN (?, 'set aside') "''')

# E15 -- the route
rep('''@bp.route("/finance/packs/api/assign", methods=["POST"])''', '''@bp.route("/finance/packs/api/set-aside", methods=["POST"])
def api_set_aside():
    """S503: the owner sets a locked file aside (never tried, never counted) or puts it back."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        fid = int(b.get("file") or 0)
    except (TypeError, ValueError):
        fid = 0
    if not fid:
        return jsonify(ok=False, error="bad_request"), 400
    body, code = set_aside(_db(), fid, bool(b.get("back")), _who(u), str(b.get("why") or ""))
    return jsonify(**body), code


@bp.route("/finance/packs/api/assign", methods=["POST"])''')
open(dst, 'w', encoding='utf-8').write(t)
print('built', hashlib.md5(t.encode()).hexdigest())
