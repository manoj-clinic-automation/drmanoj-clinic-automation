#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s411.py -- kit S411_SHELF_FIRST_RUN. Builds the two patched files FROM THE LIVE BYTES with anchored edits (every anchor
exactly once, else it refuses) after checking each file's FROM pin:

  packs.py     the identifier reads the HEADER (bank, holder line, account tail, period), never a narration; holders match as word
               sets, the longest wins, a tie is unplaced; the twelve accounts' words as the banks print them + three ICICI slots the
               first real run showed (NK Pathology current, Dr Bhawna savings, the HUF savings); a by-words placement learns the tail;
               .txt / .csv statements are read; a password-locked PDF is named as such; a statement covering only part of a month is
               'partial', never the month's statement; the electricity lines come from ICICI's own tables; the owner edits a slot's words
  packs.html   the unplaced table shows the holder the PDF prints; a slot's words are one tap to edit

Usage: make_s411.py --finance /root/finance --out DIR
"""
import hashlib
import io
import os
import sys

FROM = {"packs.py": "734c7fc0f4ff780a94448e2b834f72b1", "packs.html": "03fb47f68ffd28b375b50c91567cfcaa"}


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


def build_packs(s):
    s = rep(s, '''NO patient data, no account number beyond a tail, no password anywhere in this file. The mail credentials are read from
/root/wa/.env at send time and never printed. PACKS_TODAY / PACKS_MAIL_STUB / PACKS_ENV / STMT_INBOX serve the walk.
"""''', '''NO patient data, no account number beyond a tail, no password anywhere in this file. The mail credentials are read from
/root/wa/.env at send time and never printed. PACKS_TODAY / PACKS_MAIL_STUB / PACKS_ENV / STMT_INBOX serve the walk.

S411 (the shelf's first real run, 26-Sep-2026): the identifier reads the HEADER of a statement -- the bank, the holder line ('Your
Details With Us'), the account tail, the period -- never a narration (a Yes Bank UPI narration inside an ICICI statement had flipped
the bank; 'NK PATHOLOGY' inside a transfer narration had placed Dr Bhawna's statement on NK's slot). Holders match as word sets and the
longest match wins (MANOJ KUMAR AGARWAL HUF beats MANOJ KUMAR AGARWAL); a tie is unplaced. Three ICICI slots the run showed were added
(NK Pathology current, Dr Bhawna savings, the HUF savings). A by-words placement learns the account tail. ICICI's pipe-delimited .txt
statements are read; a password-locked PDF is named as such and waits for a decrypted copy; a statement covering only part of a month is
'partial' and never the month's statement. ICICI lines live in icici_statement_period/_line (finance_icici v1.1), never in the Yes Bank
tables the owner's Bank card reads.
"""''', "header")
    s = rep(s, '''SLOTS = [
    ("yes_cur_nk",       "YES",   "NK Pathology (Yes Bank current)",           "current", "NK PATHOLOGY",                 0),
    ("yes_cur_clinic",   "YES",   "Dr Manoj Agarwal Clinic (Yes Bank current)", "current", "MANOJ AGARWAL CLINIC",         0),
    ("yes_cur_sanj",     "YES",   "Sanjeevni Medicos (Yes Bank current)",      "current", "SANJEEVNI",                    1),
    ("yes_sav_manoj",    "YES",   "Dr Manoj Agarwal (Yes Bank savings)",       "savings", "MANOJ AGARWAL",                0),
    ("yes_sav_bhawna",   "YES",   "Dr Bhawna Agarwal (Yes Bank savings)",      "savings", "BHAWNA",                       0),
    ("yes_sav_huf",      "YES",   "Manoj Kumar Agarwal HUF (Yes Bank savings)", "savings", "HUF",                          0),
    ("icici_sanj",       "ICICI", "Sanjeevni Medicos (ICICI)",                 "current", "SANJEEVNI",                    1),
    ("icici_clinic",     "ICICI", "Dr Manoj Agarwal Clinic (ICICI)",           "current", "MANOJ AGARWAL CLINIC",         0),
    ("icici_personal",   "ICICI", "Dr Manoj Agarwal (ICICI)",                  "savings", "MANOJ AGARWAL",                0),
    ("card_hdfc_regalia", "HDFC", "HDFC Business Regalia (card)",              "card",    "REGALIA",                      0),
    ("card_icici_amazon", "ICICI", "ICICI Amazon Pay (card)",                  "card",    "AMAZON",                       0),
    ("card_icici_coral",  "ICICI", "ICICI Coral (card)",                       "card",    "CORAL",                        0),
]''', '''SLOTS = [
    ("yes_cur_nk",       "YES",   "NK Pathology (Yes Bank current)",           "current", "NK PATHOLOGY",                 0),
    ("yes_cur_clinic",   "YES",   "Dr Manoj Agarwal Clinic (Yes Bank current)", "current", "MANOJ AGARWAL CLINIC",         0),
    ("yes_cur_sanj",     "YES",   "Sanjeevni Medicos (Yes Bank current)",      "current", "SANJEEVNI MEDICOS",            1),
    ("yes_sav_manoj",    "YES",   "Dr Manoj Agarwal (Yes Bank savings)",       "savings", "MANOJ KUMAR AGARWAL",          0),
    ("yes_sav_bhawna",   "YES",   "Dr Bhawna Agarwal (Yes Bank savings)",      "savings", "BHAWNA AGARWAL",               0),
    ("yes_sav_huf",      "YES",   "Manoj Kumar Agarwal HUF (Yes Bank savings)", "savings", "MANOJ KUMAR AGARWAL HUF",      0),
    ("icici_sanj",       "ICICI", "Sanjeevni Medicos (ICICI)",                 "current", "SANJEEVNI MEDICOS",            1),
    ("icici_clinic",     "ICICI", "Dr Manoj Agarwal Clinic (ICICI)",           "current", "MANOJ AGARWAL CLINIC",         0),
    ("icici_nk",         "ICICI", "NK Pathology (ICICI current)",              "current", "NK PATHOLOGY",                 0),   # S411
    ("icici_personal",   "ICICI", "Dr Manoj Agarwal (ICICI)",                  "savings", "MANOJ KUMAR AGARWAL",          0),
    ("icici_bhawna",     "ICICI", "Dr Bhawna Agarwal (ICICI savings)",         "savings", "BHAWNA AGARWAL",               0),   # S411
    ("icici_huf",        "ICICI", "Manoj Kumar Agarwal HUF (ICICI savings)",   "savings", "MANOJ KUMAR AGARWAL HUF",      0),   # S411
    ("card_hdfc_regalia", "HDFC", "HDFC Business Regalia (card)",              "card",    "REGALIA",                      0),
    ("card_icici_amazon", "ICICI", "ICICI Amazon Pay (card)",                  "card",    "AMAZON",                       0),
    ("card_icici_coral",  "ICICI", "ICICI Coral (card)",                       "card",    "CORAL",                        0),
]
# S411: the words the S408 seed wrote, by key -- the seed of S411 replaces exactly these (an owner-edited value is left alone)
S408_WORDS = {"yes_cur_sanj": "SANJEEVNI", "yes_sav_manoj": "MANOJ AGARWAL", "yes_sav_bhawna": "BHAWNA", "yes_sav_huf": "HUF",
              "icici_sanj": "SANJEEVNI", "icici_personal": "MANOJ AGARWAL"}
LOCKED_NOTE = "password-protected PDF -- the bank's password is not on this server; put a decrypted copy in Bank Statements/Decrypted"
NOISE_TOKENS = {"M", "S", "MS", "DR", "MR", "MRS", "SHRI", "SMT", "AND", "THE", "OF"}''', "slots")
    s = rep(s, '''def identify_text(text):
    """The bank, the kind, the tail, the period and the holder-word hits, from the text alone."""
    up = " ".join(text.upper().split())
    bank = "YES" if ("YES BANK" in up or "YESBANK" in up) else ("ICICI" if "ICICI" in up else ("HDFC" if "HDFC" in up else ""))
    kind = "card" if ("CREDIT CARD" in up or "MINIMUM AMOUNT DUE" in up or "CARD NUMBER" in up) else ("savings" if "SAVINGS" in up else ("current" if "CURRENT" in up else ""))
    tail = ""
    for rx in TAIL_RES:
        m = rx.search(text)
        if m:
            tail = m.group(1)[-4:]
            break
    pf = pt = None
    m = PERIOD_RES[0].search(text)
    if m:
        pf, pt = _iso_any(m.group(1)), _iso_any(m.group(2))
    else:
        m = PERIOD_RES[1].search(text)
        if m:
            d = _iso_any(m.group(1))
            if d:
                pt = d
                pf = d[:8] + "01"
    return dict(bank=bank, kind=kind, tail=tail, period_from=pf, period_to=pt, up=up)''', '''PIPE_ACCT_RE = re.compile(r"^\\s*[Xx*\\d]{2,16}?(\\d{4})\\|", re.M)     # S411: ICICI's pipe .txt prints the account at the start of every row


def _tokens(s):
    """Holder words as a set: upper-case, the salutations and 'M/S' dropped, SANJEEVANI folded to SANJEEVNI."""
    up = str(s or "").upper().replace("SANJEEVANI", "SANJEEVNI")
    return {t for t in re.split(r"[^A-Z0-9]+", up) if t and t not in NOISE_TOKENS}


def _header(text, n=40):
    """The statement's head: the non-empty lines BEFORE the first transaction row (a dated row, a B/F row or a pipe row) -- where the
    bank, the holder, the account and the period are printed; a narration never reaches it."""
    out = []
    for ln in (text or "").splitlines():
        if not ln.strip():
            continue
        if re.match(r"^\\s*\\d{2}[-–/]\\d{2}[-–/]\\d{4}\\s", ln) or re.search(r"\\bB/F\\b", ln) or re.match(r"^\\s*[Xx*\\d]{6,}\\|", ln):
            break
        out.append(ln)
        if len(out) >= n:
            break
    return "\\n".join(out)


def _bank_of(up):
    """The bank named FIRST in the text (the head names the issuing bank before anything else)."""
    hits = []
    for word, bank in (("YES BANK", "YES"), ("YESBANK", "YES"), ("YES FIRST", "YES"), ("ICICI", "ICICI"), ("HDFC", "HDFC")):
        i = up.find(word)
        if i >= 0:
            hits.append((i, bank))
    return min(hits)[1] if hits else ""


def identify_text(text):
    """S411: the bank, the kind, the tail, the period and the HOLDER from the statement's head -- never from a narration.
    'Your Details With Us:' (ICICI iCRM) names the holder on the next line; otherwise the head's own words are the holder text."""
    head = _header(text)
    hup = " ".join(head.upper().split())
    up = " ".join(text.upper().split())
    bank = _bank_of(hup) or _bank_of(up)
    kind = "card" if ("CREDIT CARD" in hup or "MINIMUM AMOUNT DUE" in hup or "CARD NUMBER" in hup) else ("savings" if "SAVINGS" in hup else ("current" if "CURRENT" in hup else ""))
    holder = ""
    hl = [ln.strip() for ln in head.splitlines()]
    for i, ln in enumerate(hl):
        if "YOUR DETAILS WITH US" in ln.upper() and i + 1 < len(hl):
            holder = hl[i + 1]
            break
    tail = ""
    for scope in (head, text):
        for rx in TAIL_RES + (PIPE_ACCT_RE,):
            m = rx.search(scope)
            if m:
                tail = m.group(1)[-4:]
                break
        if tail:
            break
    pf = pt = None
    m = PERIOD_RES[0].search(text)
    if m:
        pf, pt = _iso_any(m.group(1)), _iso_any(m.group(2))
    else:
        m = PERIOD_RES[1].search(text)
        if m:
            d = _iso_any(m.group(1))
            if d:
                pt = d
                pf = d[:8] + "01"
    return dict(bank=bank, kind=kind, tail=tail, period_from=pf, period_to=pt, up=hup, holder=holder,
                tokens=sorted(_tokens(holder) if holder else _tokens(hup)))''', "identify_text")
    s = rep(s, '''    slots = [dict(r) for r in con.execute("SELECT * FROM stmt_slot ORDER BY sort")]
    if ident["tail"]:
        for s in slots:
            if s["ident_tail"] and s["ident_tail"] == ident["tail"] and (not ident["bank"] or s["bank"] == ident["bank"]):
                return s, "by tail"
    cands = []
    for s in slots:
        if ident["bank"] and s["bank"] != ident["bank"]:
            continue
        if ident["kind"] and s["kind"] != ident["kind"] and not (ident["kind"] in ("current", "savings") and s["kind"] in ("current", "savings") and ident["kind"] == s["kind"]):
            if ident["kind"] == "card" or s["kind"] == "card":
                continue
        words = [w.strip() for w in (s["ident_words"] or "").split(",") if w.strip()]
        if words and all(w in ident["up"] for w in words):
            cands.append((len(" ".join(words)), s))
    if not cands:
        return None, "no slot's words are in the text"
    cands.sort(key=lambda x: -x[0])
    if len(cands) > 1 and cands[0][0] == cands[1][0]:
        return None, "two slots fit the words (%s / %s)" % (cands[0][1]["holder_label"], cands[1][1]["holder_label"])
    best = cands[0][1]
    if best["ident_tail"] and ident["tail"] and best["ident_tail"] != ident["tail"]:
        return None, "the words say %s but the tail %s is not that account's (%s)" % (best["holder_label"], ident["tail"], best["ident_tail"])
    return best, "by words"''', '''    slots = [dict(r) for r in con.execute("SELECT * FROM stmt_slot ORDER BY sort")]
    if ident["tail"]:
        for s in slots:
            if s["ident_tail"] and s["ident_tail"] == ident["tail"] and (not ident["bank"] or s["bank"] == ident["bank"]):
                return s, "by tail"
    have = set(ident.get("tokens") or _tokens(ident.get("holder") or ident.get("up") or ""))
    text_up = " ".join(str(ident.get("holder") or ident.get("up") or "").upper().replace("SANJEEVANI", "SANJEEVNI").split())
    cands = []
    for s in slots:
        if ident["bank"] and s["bank"] != ident["bank"]:
            continue
        if (ident["kind"] == "card") != (s["kind"] == "card"):
            continue
        raw = (s["ident_words"] or "").upper()
        words = _tokens(raw.replace(",", " "))
        if not words or not words <= have:
            continue
        # the phrase as printed ranks above a word set: 'HUF' printed beats 'MANOJ AGARWAL' assembled from 'MANOJ KUMAR AGARWAL HUF'
        phrase = 1 if all(" ".join(g.split()) in text_up for g in raw.split(",") if g.strip()) else 0
        cands.append((phrase, len(words), 1 if (ident["kind"] and s["kind"] == ident["kind"]) else 0, s))
    if not cands:
        return None, "no slot's words are in the holder text%s" % ((" '%s'" % ident["holder"]) if ident.get("holder") else "")
    cands.sort(key=lambda x: (-x[0], -x[1], -x[2]))
    if len(cands) > 1 and cands[0][:3] == cands[1][:3]:
        return None, "two slots fit the words (%s / %s)" % (cands[0][3]["holder_label"], cands[1][3]["holder_label"])
    best = cands[0][3]
    if best["ident_tail"] and ident["tail"] and best["ident_tail"] != ident["tail"]:
        return None, "the words say %s but the tail %s is not that account's (%s)" % (best["holder_label"], ident["tail"], best["ident_tail"])
    return best, "by words"''', "place")
    s = rep(s, '''def process_inbox(con=None, verbose=False):''', '''def _file_text(lp):
    """(text, locked): pdftotext -layout for a PDF (locked=True when it is password-protected), the file itself for .txt / .csv."""
    if not lp or not os.path.exists(lp):
        return "", False
    low = lp.lower()
    if low.endswith(".pdf"):
        try:
            r = subprocess.run(["pdftotext", "-layout", lp, "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        except Exception:                                # noqa: BLE001
            return "", False
        err = r.stderr.decode("utf-8", "replace")
        if "Incorrect password" in err or "Encrypted" in err:
            return "", True
        return r.stdout.decode("utf-8", "replace"), False
    if low.endswith((".txt", ".csv")):
        try:
            with open(lp, "rb") as fh:
                return fh.read(400000).decode("utf-8", "replace"), False
        except OSError:
            return "", False
    return "", False


def process_inbox(con=None, verbose=False):
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


def _process_once(con=None, verbose=False):''', "file_text helper + the passes")
    s = rep(s, '''        lp = f["local_path"] or ""
        text = pdf_text(lp) if lp.lower().endswith(".pdf") and os.path.exists(lp) else ""
        ident = identify_text(text) if text else dict(bank="", kind="", tail="", period_from=None, period_to=None, up="")
        slot, how = place(con, ident) if text else (None, "not a readable PDF" if lp else "no file")''',
            '''        lp = f["local_path"] or ""
        text, locked = _file_text(lp)
        ident = identify_text(text) if text else dict(bank="", kind="", tail="", period_from=None, period_to=None, up="", holder="")
        slot, how = place(con, ident) if text else (None, (LOCKED_NOTE if locked else ("not a readable PDF" if lp else "no file")))''', "process text")
    s = rep(s, '''                    (ident["bank"], ident["kind"] or (slot["kind"] if slot else ""), ident["tail"], ident["period_from"], ident["period_to"],
                     (slot["holder_label"] if slot else ""), (slot["id"] if slot else None), (how if slot else None), (None if slot else how), _now(), f["id"]))
        if slot:
            out["placed"] += 1''', '''                    (ident["bank"], ident["kind"] or (slot["kind"] if slot else ""), ident["tail"], ident["period_from"], ident["period_to"],
                     (slot["holder_label"] if slot else (ident.get("holder") or "")), (slot["id"] if slot else None), (how if slot else None), (None if slot else how), _now(), f["id"]))
        if slot:
            out["placed"] += 1
            if how == "by words" and ident["tail"] and not (slot.get("ident_tail") or "") and f["folder"] == "bank":   # S411: the tail is learned
                con.execute("UPDATE stmt_slot SET ident_tail=?, owner_set=? WHERE id=? AND (ident_tail IS NULL OR ident_tail='')",
                            (ident["tail"], "learned from the statement (file %d) %s" % (f["id"], _now()), slot["id"]))''', "learn tail")
    s = rep(s, '''    con.execute("UPDATE stmt_file SET slot_id=?, holder=?, ident_how=?, note=NULL, identified_at=? WHERE id=?", (s["id"], s["holder_label"], "the owner's tap", _now(), f["id"]))
    rs, ms = ("locked original", "") if f["folder"] == "cards" else read_file(con, f, s)''',
            '''    locked = str(f.get("note") or "").startswith("password-protected")
    con.execute("UPDATE stmt_file SET slot_id=?, holder=?, ident_how=?, note=NULL, identified_at=? WHERE id=?", (s["id"], s["holder_label"], "the owner's tap", _now(), f["id"]))
    rs, ms = ("locked original", "") if (f["folder"] == "cards" or locked) else read_file(con, f, s)''', "assign locked")
    s = rep(s, '''        fs = [dict(r) for r in con.execute(
            "SELECT * FROM stmt_file WHERE slot_id=? AND folder<>'cards' AND period_to IS NOT NULL AND period_from<=? AND period_to>=? "
            "ORDER BY period_to DESC, id DESC", (s["id"], hi, lo))]
        f = fs[0] if fs else None
        state = "empty"
        if f:
            state = "arrived"''', '''        fs = [dict(r) for r in con.execute(
            "SELECT * FROM stmt_file WHERE slot_id=? AND folder<>'cards' AND period_to IS NOT NULL AND period_from<=? AND period_to>=? "
            "ORDER BY period_to DESC, id DESC", (s["id"], hi, lo))]
        full = [x for x in fs if x["period_from"] <= lo and x["period_to"] >= hi]   # S411: the month's statement covers the whole month
        f = full[0] if full else (fs[0] if fs else None)
        partial = bool(f) and not full and s["kind"] != "card"
        state = "empty"
        if partial:
            state = "partial"
        elif f:
            state = "arrived"''', "cells partial")
    s = rep(s, '''        out.append(dict(slot=s["key"], label=s["holder_label"], bank=s["bank"], kind=s["kind"], tail=s["ident_tail"], sanjeevni=s["sanjeevni"],
                        state=state, file=(dict(id=f["id"], name=f["name"], period_from=f["period_from"], period_to=f["period_to"],
                                                read_status=f["read_status"], matched_status=f["matched_status"]) if f else None),
                        twin_missing=twin_missing))''', '''        out.append(dict(slot=s["key"], slot_id=s["id"], words=s["ident_words"], label=s["holder_label"], bank=s["bank"], kind=s["kind"], tail=s["ident_tail"], sanjeevni=s["sanjeevni"],
                        state=state, file=(dict(id=f["id"], name=f["name"], period_from=f["period_from"], period_to=f["period_to"],
                                                read_status=f["read_status"], matched_status=f["matched_status"]) if f else None),
                        twin_missing=twin_missing))''', "cells fields")
    s = rep(s, '''    return [dict(id=r["id"], name=r["name"], folder=r["folder"], subfolder=r["subfolder"], bank=r["bank"], kind=r["kind"], tail=r["tail"],
                 period_from=r["period_from"], period_to=r["period_to"], why=r["note"], fetched_at=r["fetched_at"])''',
            '''    return [dict(id=r["id"], name=r["name"], folder=r["folder"], subfolder=r["subfolder"], bank=r["bank"], kind=r["kind"], tail=r["tail"],
                 period_from=r["period_from"], period_to=r["period_to"], why=r["note"], fetched_at=r["fetched_at"], holder=r["holder"],
                 locked=str(r["note"] or "").startswith("password-protected"))''', "unplaced holder")
    s = rep(s, '''    icici |= {r[0] for r in con.execute("SELECT f.tail FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE s.bank='ICICI' AND f.tail IS NOT NULL AND f.tail<>''")}
    if not _has(con, "bank_statement_line"):
        return [], "no statement lines on this server"
    if not icici:
        return [], "no ICICI statement on the shelf yet"
    rows = [dict(r) for r in con.execute("SELECT account_ref, txn_date, description, withdrawal_p FROM bank_statement_line WHERE withdrawal_p>0 AND substr(txn_date,1,7)=? ORDER BY txn_date", (month,))]''',
            '''    icici |= {r[0] for r in con.execute("SELECT f.tail FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE s.bank='ICICI' AND f.tail IS NOT NULL AND f.tail<>''")}
    if not _has(con, "icici_statement_line"):                       # S411: ICICI's own table (finance_icici v1.1), never the Yes Bank one
        return [], "no ICICI statement lines on this server yet"
    if not icici:
        return [], "no ICICI statement on the shelf yet"
    rows = [dict(r) for r in con.execute("SELECT account_ref, txn_date, description, withdrawal_p FROM icici_statement_line WHERE withdrawal_p>0 AND substr(txn_date,1,7)=? ORDER BY txn_date", (month,))]''', "electricity table")
    s = rep(s, '''        st = "ready" if (f and c["state"] in ("read", "matched", "arrived")) else "missing"
        files = None
        if f:
            fr = con.execute("SELECT local_path, name FROM stmt_file WHERE id=?", (f["id"],)).fetchone()
            if fr and fr[0] and os.path.exists(fr[0]):
                with open(fr[0], "rb") as fh:
                    files = [("Statement_%s_%s.pdf" % (c["slot"], month), fh.read(), "application/pdf")]
        row("stmt:" + c["slot"], "3 · %s statement" % c["label"], st, ("not on the shelf" if not f else ("read: " + (f["read_status"] or "arrived"))) if st != "ready" or f else "", files, "/finance/packs/file/%d" % f["id"] if f else None, bool(c["sanjeevni"]))''',
            '''        st = "ready" if (f and c["state"] in ("read", "matched", "arrived")) else "missing"
        files = None
        if f and st == "ready":
            fr = con.execute("SELECT local_path, name FROM stmt_file WHERE id=?", (f["id"],)).fetchone()
            if fr and fr[0] and os.path.exists(fr[0]):
                ext = os.path.splitext(fr[0])[1].lower() or ".pdf"
                with open(fr[0], "rb") as fh:
                    files = [("Statement_%s_%s%s" % (c["slot"], month, ext), fh.read(), "application/pdf" if ext == ".pdf" else "text/plain")]
        why_ = ""
        if not f:
            why_ = "not on the shelf"
        elif c["state"] == "partial":                                  # S411
            why_ = "only %s → %s on the shelf, not the whole month" % (_dmy(f["period_from"]), _dmy(f["period_to"]))
        elif st != "ready":
            why_ = "read: " + (f["read_status"] or "arrived")
        elif f["read_status"] and f["read_status"] != "read":
            why_ = f["read_status"]
        row("stmt:" + c["slot"], "3 · %s statement" % c["label"], st, why_, files, "/finance/packs/file/%d" % f["id"] if f else None, bool(c["sanjeevni"]))''', "stmt rows")
    s = rep(s, '''    ready = bool(ys and ys["file"] and ic and ic["file"])''', '''    ready = bool(ys and ys["file"] and ys["state"] != "partial" and ic and ic["file"] and ic["state"] != "partial")   # S411''', "amir partial")
    s = rep(s, '''@bp.route("/finance/packs/api/tick", methods=["POST"])
def api_tick():''', '''@bp.route("/finance/packs/api/slot-words", methods=["POST"])
def api_slot_words():
    """S411: the owner edits the words a slot's holder must print (data, never code); the unplaced files are re-identified."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        sid = int(b.get("slot") or 0)
    except (TypeError, ValueError):
        sid = 0
    words = " ".join(str(b.get("words") or "").upper().replace(",", " ").split())[:80]
    con = _db()
    ensure(con)
    r = con.execute("SELECT key, ident_words FROM stmt_slot WHERE id=?", (sid,)).fetchone()
    if not r or not words:
        return jsonify(ok=False, error="bad_request"), 400
    con.execute("UPDATE stmt_slot SET ident_words=?, owner_set=? WHERE id=?", (words, "words by %s %s" % (_who(u), _now()), sid))
    con.commit()
    return jsonify(ok=True, slot=r[0], before=r[1], words=words, reidentified=process_inbox(con))


@bp.route("/finance/packs/api/tick", methods=["POST"])
def api_tick():''', "slot-words route")
    return s


def build_packs_html(s):
    s = rep(s, '''<th>File</th><th>Bank / kind / tail</th><th>Period</th><th>Why unplaced</th><th>Which account?</th></tr>'+
      u.map(function(x){return '<tr><td>'+esc(x.name)+' <span class="mut">('+esc(x.folder)+(x.subfolder?'/'+esc(x.subfolder):'')+')</span></td><td>'+esc(x.bank||"?")''',
            '''<th>File</th><th>Holder (as the PDF prints it)</th><th>Bank / kind / tail</th><th>Period</th><th>Why unplaced</th><th>Which account?</th></tr>'+
      u.map(function(x){return '<tr><td>'+esc(x.name)+' <span class="mut">('+esc(x.folder)+(x.subfolder?'/'+esc(x.subfolder):'')+')</span></td><td>'+(x.holder?esc(x.holder):(x.locked?'<span class="warn">locked — password needed</span>':'<span class="mut">—</span>'))+'</td><td>'+esc(x.bank||"?")''', "unplaced holder column")
    s = rep(s, '''(c.tail?' · …'+esc(c.tail):' · tail not learned yet')+'</span><br>'+''',
            '''(c.tail?' · …'+esc(c.tail):' · tail not learned yet')+' · <a href="#" onclick="words('+c.slot_id+',\\''+esc(c.words||"").replace(/'/g,"\\\\'")+'\\');return false">words</a></span><br>'+''', "cell words link")
    s = rep(s, '''function post(p,b){return fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})}).then(function(r){return r.json()})}''',
            '''function post(p,b){return fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})}).then(function(r){return r.json()})}
/* S411: the words a slot's holder must print, one tap to edit (data, never code); the unplaced files are re-identified */
function words(sid,cur){var w=prompt("The words this account's statement prints in its holder line (all must appear; the longest match wins):",cur||""); if(w==null||!w.trim()) return;
  post("/finance/packs/api/slot-words",{slot:sid,words:w}).then(function(j){if(!j.ok){alert(j.message||j.error||"not saved");return} flash("words saved: "+j.words+" · re-identified "+JSON.stringify(j.reidentified)); load();});}''', "words js")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance"), args.get("--out")
    if not (fin and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {"packs.py": build_packs(load(os.path.join(fin, "packs.py"), "packs.py")),
             "packs.html": build_packs_html(load(os.path.join(fin, "packs.html"), "packs.html"))}
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
