#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s866.py -- kit S866_PACKS_LATE_AND_CARD_BILL (the parent, S480, 18-Nov-2026). Builds packs.py and packs.html from the
18-Nov bundle's bytes (FROM checked by md5; every anchor exactly once).   python3 make_s866.py <from_dir> <to_dir>"""
import hashlib, os, sys
src, dst = sys.argv[1:3]
FROM = {"packs.py": "7dc8c39a", "packs.html": "f5991911"}
os.makedirs(dst, exist_ok=True)


def rep(t, a, b, w):
    n = t.count(a)
    if n != 1:
        sys.exit("!! anchor %s found %d times" % (w, n))
    return t.replace(a, b)


for n, m in FROM.items():
    if hashlib.md5(open(os.path.join(src, n), "rb").read()).hexdigest()[:8] != m:
        sys.exit("!! %s is not its FROM pin" % n)

# ------------------------------------------------------------------ packs.py
t = open(os.path.join(src, "packs.py"), encoding="utf-8").read()

# 1. the cell carries the card's true reason (the page showed 'newest original has no decrypted twin')
t = rep(t, '''                        every=every, period_words=(_period_words(month, every) if every > 1 else _month_name(month))))   # S621
    return out
''', '''                        every=every, period_words=(_period_words(month, every) if every > 1 else _month_name(month))))   # S621
        if s["kind"] == "card":        # S866: the cell says the true reason, in his words, not 'no decrypted twin'
            out[-1]["note"] = _s866_card_why(con, out[-1], month)[1] if (not f or twin_missing) else ""
    return out
''', "cells tail")

# 2. the helpers, before pack_rows
t = rep(t, '''def pack_rows(con, month, light=False):
''', '''S866_PW = ("no password is stored for this card yet -- type it once under Statement passwords on this page; "
           "every statement of the card then opens by itself")
S866_PW_WRONG = ("the password stored for this card does not open it -- replace it under Statement passwords on this page; "
                 "every statement of the card then opens by itself")


def _s866_pw(con, c):
    """S866 (review LOW 1): 'no password stored' only when none is; a stored one that did not open it is named as such."""
    try:
        keys = ("CARD:%s" % c.get("slot"), str(c.get("bank") or ""))
        r = con.execute("SELECT 1 FROM stmt_secret WHERE bank IN (?,?) AND COALESCE(secret,'')<>'' LIMIT 1", keys).fetchone()
        return S866_PW_WRONG if r else S866_PW
    except Exception:                                    # noqa: BLE001
        return S866_PW


def _s866_card_why(con, c, month):
    """S866 (18-Nov-2026, the owner on /finance/packs: 'it shows the credit card statements is not decrypted'): a card's row and
    cell say the TRUE reason in plain words -- the month's statement is here but locked (no password stored for the card), or
    the bank never mailed the month's statement (a later one came), or it has not come yet. A card's month is the month its
    statement is DATED in (S417, S505). Returns (status, why); a statement of the month on the shelf is 'ready' -- a NEWER one
    still locked is named, never makes the month late. Never raises."""
    try:
        lo, hi = month + "-01", _month_end(month)
        sid, f = c.get("slot_id"), c.get("file")
        locked = [dict(r) for r in con.execute(
            "SELECT id, period_to FROM stmt_file WHERE slot_id=? AND folder='cards' AND COALESCE(locked,0)=1 "
            "AND COALESCE(unlocked_path,'')='' AND read_status='locked -- no password' ORDER BY period_to, id", (sid,))]
        if f:
            why = "statement dated %s" % _dmy(f.get("period_to"))
            later = [x for x in locked if (x["period_to"] or "") > hi]
            if later:
                why += " (the newer one, dated %s, is here but locked: %s)" % (_dmy(later[-1]["period_to"]), _s866_pw(con, c))
            return "ready", why
        inm = [x for x in locked if lo <= (x["period_to"] or "") <= hi]
        if inm:
            return "missing", "the statement dated %s is here but locked: %s" % (_dmy(inm[-1]["period_to"]), _s866_pw(con, c))
        nxt = con.execute("SELECT MIN(period_to) FROM stmt_file WHERE slot_id=? AND folder IN ('cards','decrypted') AND period_to>?",
                          (sid, hi)).fetchone()
        if nxt and nxt[0]:
            sub = con.execute("SELECT subfolder FROM stmt_file WHERE slot_id=? AND folder='cards' AND COALESCE(subfolder,'')<>'' "
                              "ORDER BY id DESC LIMIT 1", (sid,)).fetchone()
            why = ("no statement dated %s came from the bank -- the next one, dated %s, did. Download %s's statement from the "
                   "bank's website and put it in Drive > Credit Card Statements > %s; the shelf takes it "
                   "from there" % (_month_name(month), _dmy(nxt[0]), _month_name(month), (sub[0] if sub else c.get("label") or "the card's folder")))
            if [x for x in locked if (x["period_to"] or "") > hi]:
                why += " (that next one is locked too: %s)" % _s866_pw(con, c)
            return "missing", why
        here = con.execute("SELECT COUNT(*) FROM stmt_file WHERE slot_id=? AND folder='cards' AND COALESCE(read_status,'')<>'duplicate of decrypted' "
                           "AND period_to BETWEEN ? AND ?", (sid, lo, hi)).fetchone()   # review SHOULD: never 'not come' for a file on the shelf
        if here and here[0]:
            return "missing", ("the statement of %s is on the shelf but not opened yet -- if a password for this card is stored the shelf "
                               "opens it at its next read (09:15, 13:15, 19:15); if none is stored: %s" % (_month_name(month), S866_PW))
        return "missing", "the statement dated %s has not come yet" % _month_name(month)
    except Exception:                                    # noqa: BLE001
        return ("ready" if c.get("file") else "missing"), ""


def _s866_elec_wait(con, cl, month):
    """S866: when the month's electricity bills are short, name the card statement the card-paid bill waits on
    (packs.electricity_cards, default the Amazon Pay card -- the owner: one bill from ICICI savings, one by that card)."""
    keys = {x.strip() for x in str(_setting(con, "packs.electricity_cards", "card_icici_amazon") or "").split(",") if x.strip()}
    out = []
    for c in cl:
        if c.get("kind") == "card" and c.get("slot") in keys:
            st, why = _s866_card_why(con, c, month)
            if st != "ready" and why:
                out.append("the bill the %s card pays is read from that card's statement: %s" % (re.sub(r"\\s*\\(card\\)\\s*$", "", c.get("label") or ""), why))
    return " · ".join(out)


def pack_rows(con, month, light=False):
''', "helpers")

# 3. the card row
t = rep(t, '''        why_ = ("statement dated %s" % _dmy(f["period_to"])) if f else (NO_TWIN if c.get("no_decrypted") else "no decrypted statement on the shelf")   # S417
        if c["twin_missing"]:
            why_ = (why_ + "; " if why_ else "") + "the newest original has no decrypted twin"
        n4 += 1
        row("card:" + c["slot"], "4.%d · %s statement (password removed)" % (n4, c["label"]), ("ready" if f else "missing") if not c["twin_missing"] else ("late" if f else "missing"), why_, files, "/finance/packs/file/%d" % f["id"] if f else None)
''', '''        st_, why_ = _s866_card_why(con, c, month)      # S866: the true reason (locked / never mailed / not yet), not 'no decrypted twin'
        n4 += 1
        row("card:" + c["slot"], "4.%d · %s statement (password removed)" % (n4, c["label"]), st_, why_, files, "/finance/packs/file/%d" % f["id"] if f else None)
''', "card row")

# 4. the electricity row names what the card-paid bill waits on
t = rep(t, '''    row("electricity", "5 · Electricity: the auto-paid bills (ICICI statements and the Amazon Pay card)", "ready" if len(el) >= want else "missing",   # S434
        (why or "") if not el else ("%d of %d found: " % (len(el), want) if len(el) < want else "") + " · ".join(el), None, None)
''', '''    ewhy = (why or "") if not el else ("%d of %d found: " % (len(el), want) if len(el) < want else "") + " · ".join(el)
    if len(el) < want:                                                  # S866: what the missing bill waits on
        wait = _s866_elec_wait(con, cl, month)
        if wait:
            ewhy = (ewhy + " -- " if ewhy else "") + wait
    row("electricity", "5 · Electricity: the auto-paid bills (ICICI statements and the Amazon Pay card)", "ready" if len(el) >= want else "missing",   # S434
        ewhy, None, None)
''', "electricity row")
open(os.path.join(dst, "packs.py"), "w", encoding="utf-8").write(t)

# ------------------------------------------------------------------ packs.html
h = open(os.path.join(src, "packs.html"), encoding="utf-8").read()
h = rep(h, '''      (c.twin_missing?'<br><span class="warn">newest original has no decrypted twin</span>':'')+''',
        '''      (c.note?'<br><span class="warn">'+esc(c.note)+'</span>':'')+''', "html cell note")
open(os.path.join(dst, "packs.html"), "w", encoding="utf-8").write(h)
print("make_s866: packs.py %s · packs.html %s" % tuple(hashlib.md5(open(os.path.join(dst, n), "rb").read()).hexdigest()[:8] for n in ("packs.py", "packs.html")))
