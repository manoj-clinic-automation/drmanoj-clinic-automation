import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == '484dce36777aa8e5e9afeb22fc7ba143', 'FROM pin differs'
s = b.decode('utf-8')
def rep(a, c):
    global s
    n = s.count(a)
    assert n == 1, (n, a[:80])
    s = s.replace(a, c)

# E1 -- the docstring
rep('''    the copy already read and never written twice; each cell shows every copy of its month side by side, and the pack uses one.
"""''', '''    the copy already read and never written twice; each cell shows every copy of its month side by side, and the pack uses one.

S504 (10-Oct-2026, the owner: the card sheet "is too crude ... properly categorised for me and accountant use ... like COCO is the
main petrol pump where fuel is filled"):
  * every card statement on the shelf is read LINE BY LINE here (card_lines.py) and PROVED against the statement's own printed
    debits and credits; a statement that does not prove is shown as such and never put in a pack as if whole.
  * each line carries two words: a plain one for the owner and the accountant's ledger; a merchant is named ONCE on this page
    ('Name these merchants') and every line of it, past and future, follows.
  * the pack's card sheet is built from these lines (By ledger . Every line . Statements) when every card statement dated in the
    month is proved; until then the running All_Transactions.xlsx still goes, as before.
  * the electricity bill a card pays is found in these lines first.
"""''')

# E2 -- process_inbox reads the card statements' lines after the passes
rep('''        if tails() == t0 or not r["unplaced"]:
            break
    if own:
        con.close()
    return out
''', '''        if tails() == t0 or not r["unplaced"]:
            break
    out["cards_read"] = _read_card_lines(con)                          # S504
    if own:
        con.close()
    return out
''')

# E3 -- the reader's call, the labels, the month view
rep('''def set_secret(con, bank, text, who):''', '''def _read_card_lines(con):
    """S504: every card statement on the shelf that is read (the decrypted twin, or the original the shelf opened) goes through
    card_lines.py -- every line, proved against its own printed totals. Idempotent (card_stmt_file remembers each shelf file); the
    same statement under two files is read once. Returns how many statements were read now. Never fatal."""
    try:
        import card_lines                                 # noqa: PLC0415
        card_lines.ensure(con)
    except Exception:                                    # noqa: BLE001
        return 0
    done = {r[0] for r in con.execute("SELECT file_id FROM card_stmt_file")}
    n = 0
    for fid, key in con.execute("SELECT f.id, s.key FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE s.kind='card' "
                                "AND f.read_status='read' ORDER BY f.id").fetchall():
        if fid in done:
            continue
        p, _name = _best_path(con, fid)
        text, locked = _file_text(p or "")
        if not text or locked:
            continue
        try:
            _sid, _parsed, new = card_lines.ingest(con, fid, key, text)
        except Exception as ex:                          # noqa: BLE001  (a layout it does not know: said on the row, never fatal)
            con.execute("UPDATE stmt_file SET note=? WHERE id=?", (("card lines not read: %s" % ex)[:200], fid))
            continue
        n += 1 if new else 0
    con.commit()
    return n


def _card_labels(con):
    return {r[0]: re.sub(r"\\s*\\(card\\)\\s*$", "", r[1] or r[0]) for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE kind='card'")}


def card_spends(con, month):
    """S504: the month's card spends as the page shows them (card_lines.month_view); {} when the reader is not on this server."""
    try:
        import card_lines                                 # noqa: PLC0415
    except Exception:                                    # noqa: BLE001
        return {}
    return card_lines.month_view(con, month, _card_labels(con))


def build_card_sheet(con, month):
    """S504: the accountants' card workbook for the month -- (bytes, why_not). Built only when every card statement dated in the
    month is read and proved; otherwise (None, why) and the pack keeps the running All_Transactions.xlsx."""
    try:
        import card_lines                                 # noqa: PLC0415
    except Exception:                                    # noqa: BLE001
        return None, "the card reader is not on this server"
    v, sheets = card_lines.month_sheet_rows(con, month, _card_labels(con))
    cards = [r[0] for r in con.execute("SELECT key FROM stmt_slot WHERE kind='card' ORDER BY sort")]
    have = {s["slot"] for s in v["statements"]}
    miss = [k for k in cards if k not in have]
    if not v["statements"]:
        return None, "no card statement dated in %s has been read yet" % _month_name(month)
    if miss:
        return None, "not every card's statement of %s is read yet (%s)" % (_month_name(month), ", ".join(_card_labels(con).get(k, k) for k in miss))
    bad = [s["label"] for s in v["statements"] if not s["proof_ok"]]
    if bad:
        return None, "a statement does not add up to its own totals (%s) -- look before it goes" % ", ".join(bad)
    return _xlsx(sheets), None


def set_secret(con, bank, text, who):''')

# E4 -- the electricity bill a card paid: the card lines first, the running Excel after
rep('''def card_electricity(con, month, words):
    """S434: the electricity bills paid by a card, from the card sheet on the shelf (All_Transactions.xlsx): Date · Card · Narration ·
    Amount · Dr/Cr -- a debit whose narration carries an electricity word and whose date falls in the month."""
''', '''def card_electricity(con, month, words):
    """S434: the electricity bills paid by a card, from the card sheet on the shelf (All_Transactions.xlsx): Date · Card · Narration ·
    Amount · Dr/Cr -- a debit whose narration carries an electricity word and whose date falls in the month.
    S504: the card statements' own lines (card_line) first; the running Excel only when they hold nothing for the month."""
    if _has(con, "card_line"):
        lab = _card_labels(con)
        hits = [r for r in con.execute("SELECT txn_date, slot_key, description, amount_p FROM card_line WHERE credit=0 AND substr(txn_date,1,7)=? "
                                       "ORDER BY txn_date", (month,)).fetchall() if any(w in (r[2] or "").upper() for w in words)]
        if hits:
            return ["auto-paid %s on %s by the %s card (%s)" % (_inr(r[3]), _dmy(r[0]), lab.get(r[1], r[1]), re.sub(r"\\d{6,}", "", r[2] or "")[:40])
                    for r in hits]
''')

# E5 -- the pack's card sheet
rep('''    at = con.execute("SELECT id, local_path FROM stmt_file WHERE folder='all_txn' ORDER BY mtime DESC, id DESC LIMIT 1").fetchone()
    files = None
    if at and at[1] and os.path.exists(at[1]):
        with open(at[1], "rb") as fh:
            files = [("All card transactions.xlsx", fh.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")]   # S434
    row("cards", "4.%d · All_Transactions.xlsx (the cards' sheet)" % (n4 + 1), "ready" if files else "missing", "" if files else "not fetched from Drive yet", files, "/finance/packs/file/%d" % at[0] if at else None)''',
'''    cb, cwhy = build_card_sheet(con, month)                             # S504: the cards' own lines, by ledger, proved
    if cb:
        row("cards", "4.%d · Card spends by ledger (every line, proved against each statement)" % (n4 + 1), "ready", "",
            [("Card spends by ledger - %s.xlsx" % _month_name(month), cb, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")],
            "/finance/packs/preview/cards?month=" + month)
    else:
        at = con.execute("SELECT id, local_path FROM stmt_file WHERE folder='all_txn' ORDER BY mtime DESC, id DESC LIMIT 1").fetchone()
        files = None
        if at and at[1] and os.path.exists(at[1]):
            with open(at[1], "rb") as fh:
                files = [("All card transactions.xlsx", fh.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")]   # S434
        row("cards", "4.%d · All_Transactions.xlsx (the cards' sheet)" % (n4 + 1), "ready" if files else "missing",
            ("the running Excel goes, because " + cwhy) if files else "not fetched from Drive yet", files, "/finance/packs/file/%d" % at[0] if at else None)''')

# E6 -- the state carries the card spends
rep('''secrets=secret_state(con), road=statement_road(con))   # S476''', '''secrets=secret_state(con), road=statement_road(con), cards=card_spends(con, m))   # S476 S504''')

# E7 -- the owner names a merchant
rep('''@bp.route("/finance/packs/api/set-aside", methods=["POST"])''', '''@bp.route("/finance/packs/api/card-merchant", methods=["POST"])
def api_card_merchant():
    """S504: the owner names a card merchant once (a category from the list); every line of it, past and future, follows."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        import card_lines                                 # noqa: PLC0415
    except Exception:                                    # noqa: BLE001
        return jsonify(ok=False, error="no_reader"), 500
    con = _db()
    body, code = card_lines.name_merchant(con, str(b.get("merchant") or "").strip(), str(b.get("category") or "").strip(), _who(u))
    return jsonify(**body), code


@bp.route("/finance/packs/api/set-aside", methods=["POST"])''')

# E8 -- the owner's preview of the card workbook
rep('''    elif key.startswith("bundle_"):
        b, why = build_bundle(con, m, key[7:])''', '''    elif key == "cards":                                               # S504
        b, why = build_card_sheet(con, m)
        name, mime = "Card spends by ledger - %s.xlsx" % _month_name(m), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif key.startswith("bundle_"):
        b, why = build_bundle(con, m, key[7:])''')

open(dst, 'wb').write(s.encode('utf-8'))
print('built', hashlib.md5(s.encode('utf-8')).hexdigest())
