#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s826.py ROOT OUT -- kit S826_TWIN_AMOUNT_RESTORE (14-Nov-2026, the Scan App chat's session 410; F-1378, the scan side).
Builds the two changed files FROM THE LIVE BYTES (exact anchors that occur once; anything else stops the build).

The case (the Sanjeevni chat's S455): Janta's revised bill JP21965 (B-0271, Rs 3,205 = the first paper Rs 4,450 less a Rs 1,245
return) was set aside on 08-Nov as "duplicate of B-0118" only because a person answered "same paper" to the twin question -- the two
amounts were 28% apart. The owner's word (14-Nov): two different amounts are two papers, never a double.

  ROOT/shared/scan_checks_s441.py 59d5cb1c -> (1) no twin question when both amounts are read and differ by more than 2% (a true
                                              double carries the same amount; an amount not read is not a difference); (2) a twin
                                              question already open on such a pair is settled 'different' by the server at the next
                                              pass; (3) a 'same' answer on such a pair keeps both (nothing is set aside).
  ROOT/assetapp/asset_register.py 74043cdb -> the owner's Restore for a PHARMACY scan set aside as a duplicate: status captured,
                                              dup_of cleared, the stamp kept, recorded (who, when, what it was a duplicate of).
"""
import hashlib, os, sys

FROM = {"shared/scan_checks_s441.py": "59d5cb1cb7b2caf1355726cdce6fe3bb",
        "assetapp/asset_register.py": "74043cdbe6a7d1c0a5ba0b61470eea5d"}

P = {"shared/scan_checks_s441.py": [
    ('def _ham(a, b):',
     'def _amounts_differ(a, b):\n'
     '    """S826 (F-1378, the owner 14-Nov-2026): both amounts read and more than 2% apart -- two papers (a revised bill, a second\n'
     '    bill), never a double. An amount not read is not a difference."""\n'
     '    a, b = _f(a), _f(b)\n'
     '    if a is None or b is None or not (0 < a < 1e12) or not (0 < b < 1e12):   # nan / inf / zero / negative: not a difference\n'
     '        return False\n'
     '    return not _amount_close(a, b)\n'
     '\n'
     '\n'
     'def settle_differing_s826(db, who="server (S826)"):\n'
     '    """S826: a twin question still open whose two scans carry amounts more than 2% apart is settled \'different\' (both kept) and\n'
     '    recorded -- such a pair is never asked about. Returns how many were settled. Does not commit."""\n'
     '    n = 0\n'
     '    for q in db.execute("SELECT q.id AS qid, q.bill_id, q.cand_id, b.total_amount AS ba, c.total_amount AS ca FROM scan_question q "\n'
     '                        "JOIN bills b ON b.id=q.bill_id JOIN bills c ON c.id=q.cand_id WHERE q.kind=\'twin\' AND q.answer IS NULL "\n'
     '                        "AND b.status<>\'rejected\' AND c.status<>\'rejected\'").fetchall():\n'
     '        if not _amounts_differ(q[3], q[4]):\n'
     '            continue\n'
     '        cur = db.execute("UPDATE scan_question SET answer=\'different\', answered_by=?, answered_at=? WHERE id=? AND answer IS NULL",\n'
     '                         (who, now_ist(), q[0]))\n'
     '        if cur.rowcount:\n'
     '            db.execute("UPDATE bills SET dup_flag=\'no\' WHERE id=? AND (dup_flag IS NULL OR dup_flag IN (\'\',\'maybe\'))", (q[1],))\n'
     '            _audit(db, q[1], "not_duplicate", {"cand": q[2], "how": "S826: the two amounts differ by more than 2%"}, who)\n'
     '            n += 1\n'
     '    return n\n'
     '\n'
     '\n'
     'def _ham(a, b):'),
    ('    ensure(db)\n    now = now or _dt.datetime.now()\n',
     '    ensure(db)\n'
     '    try:\n'
     '        settle_differing_s826(db)                                # S826 (F-1378): a pair of two amounts is never left asked\n'
     '    except _sqlite3.Error:\n'
     '        pass\n'
     '    now = now or _dt.datetime.now()\n'),
    ('            close = _amount_close(a["total_amount"], b["total_amount"])\n            if not (same_tail or close):\n',
     '            close = _amount_close(a["total_amount"], b["total_amount"])\n'
     '            if _amounts_differ(a["total_amount"], b["total_amount"]):\n'
     '                continue                                            # S826 (F-1378): two amounts are two papers -- never a twin question\n'
     '            if not (same_tail or close):\n'),
    ('        if ans == "same" and c is not None:\n',
     '        if ans == "same" and c is not None and _amounts_differ(b["total_amount"], c["total_amount"]):\n'
     '            db.execute("UPDATE scan_question SET answer=\'different\', answered_by=? WHERE id=?", ((who or "")[:60] + " -- S826: the amounts differ, both kept", qid))\n'
     '            db.execute("UPDATE bills SET dup_flag=\'no\' WHERE id=? AND (dup_flag IS NULL OR dup_flag IN (\'\',\'maybe\'))", (b["id"],))\n'
     '            _audit(db, b["id"], "not_duplicate", {"cand": q["cand_id"], "how": "S826: answered same, but the two amounts differ by more than 2% -- both kept"}, who)\n'
     '        elif ans == "same" and c is not None:\n'),
    ],
    "assetapp/asset_register.py": [
    ('''{{s557_line}}{% if b['dup_of'] %}<span class="badge red">duplicate of {{dupstamp or ('#'~b['dup_of'])}}</span><br>{% endif %}''',
     '''{{s557_line}}{% if b['dup_of'] %}<span class="badge red">duplicate of {{dupstamp or ('#'~b['dup_of'])}}</span>'''
     '''{% if is_owner and b['status']=='rejected' and (b['lane'] or '')=='pharmacy' and not b['page_of'] %} <form method=post id=s826restore '''
     '''action="{{url_for('bill_restore_s826',bid=b['id'])}}" style="display:inline" onsubmit="return confirm('Restore this scan? It goes back to Filed and is no longer a duplicate.')">'''
     '''<button class="btn small">Restore — not a duplicate</button></form>{% endif %}<br>{% endif %}'''),
    ('''    else:\n        flash("Duplicate or Not duplicate.")\n    return redirect(request.form.get("back") or url_for("bill_view", bid=bid))\n''',
     '''    else:\n        flash("Duplicate or Not duplicate.")\n    return redirect(request.form.get("back") or url_for("bill_view", bid=bid))\n'''
     '''\n\n'''
     '''KIT_S826 = "S826_TWIN_AMOUNT_RESTORE"\n\n\n'''
     '''@app.route("/bills/<int:bid>/restore_s826", methods=["POST"])\n'''
     '''@owner_required\n'''
     '''def bill_restore_s826(bid):\n'''
     '''    """S826 (F-1378, the owner 14-Nov-2026): a PHARMACY scan set aside as a duplicate is put back -- status captured, dup_of cleared,\n'''
     '''    the stamp kept, recorded (who, when, what it was a duplicate of and why). The pharmacy side then reads it as any captured scan.\n'''
     '''    The owner's only. A joined page, a scan not set aside as a duplicate, or one off the pharmacy lane: nothing changes."""\n'''
     '''    db = get_db()\n'''
     '''    b = _bill_or_404(bid)\n'''
     '''    name = b["stamp_no"] or ("#%d" % bid)\n'''
     '''    back = request.form.get("back") or url_for("bill_view", bid=bid)\n'''
     '''    page_of = b["page_of"] if "page_of" in b.keys() else None\n'''
     '''    if b["status"] != "rejected" or not b["dup_of"] or page_of or (b["lane"] or "") != "pharmacy":\n'''
     '''        flash("%s is not a pharmacy scan set aside as a duplicate; nothing changed." % name)\n'''
     '''        return redirect(back)\n'''
     '''    first = db.execute("SELECT stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()\n'''
     '''    cur = db.execute("UPDATE bills SET status='captured', dup_of=NULL, dup_flag='no', dup_why=NULL, reject_reason=NULL, approved_by=NULL, "\n'''
     '''                     "approved_at=NULL WHERE id=? AND status='rejected' AND dup_of=? AND page_of IS NULL AND lane='pharmacy'", (bid, b["dup_of"]))\n'''
     '''    if not cur.rowcount:\n'''
     '''        db.commit()\n'''
     '''        flash("%s changed meanwhile; nothing changed." % name)\n'''
     '''        return redirect(back)\n'''
     '''    db.execute("UPDATE bills SET dup_flag='no' WHERE id=? AND (dup_flag IS NULL OR dup_flag IN ('','maybe'))", (b["dup_of"],))\n'''
     '''    _audit_bill(db, b["dup_of"], "not_duplicate", {"cand": bid, "how": "S826: %s restored by the owner -- two papers" % name})\n'''
     '''    if S441 is not None:                                     # the pair is recorded as two papers: never asked or set aside again\n'''
     '''        S441.ensure(db)\n'''
     '''        for x, y in ((bid, b["dup_of"]), (b["dup_of"], bid)):\n'''
     '''            cur2 = db.execute("UPDATE scan_question SET answer='different', answered_by=?, answered_at=? WHERE bill_id=? AND kind='twin' AND cand_id=?",\n'''
     '''                              ("owner (S826 restore)", _now_ist(), x, y))\n'''
     '''            if x == bid and not cur2.rowcount:\n'''
     '''                db.execute("INSERT OR IGNORE INTO scan_question(bill_id, kind, cand_id, detail, asked_at, answer, answered_by, answered_at) "\n'''
     '''                           "VALUES(?,'twin',?,?,?,'different',?,?)", (bid, b["dup_of"], "S826 restore", _now_ist(), "owner (S826 restore)", _now_ist()))\n'''
     '''    _audit_bill(db, bid, "restore_s826", {"was_dup_of": b["dup_of"], "was_dup_of_stamp": (first[0] if first else None),\n'''
     '''                                          "was_reason": (b["reject_reason"] or "")[:120], "was_why": ((b["dup_why"] if "dup_why" in b.keys() else "") or "")[:120], "was_set_aside_by": b["approved_by"] or "",\n'''
     '''                                          "was_set_aside_at": b["approved_at"] or "", "stamp": b["stamp_no"]})\n'''
     '''    db.commit()\n'''
     '''    flash("%s restored — filed again on the pharmacy lane, no longer a duplicate of %s." % (name, (first[0] if first else ("#%d" % b["dup_of"]))))\n'''
     '''    return redirect(back)\n'''),
    ]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(root, out):
    for rel, pin in FROM.items():
        src = open(os.path.join(root, rel), "rb").read()
        if md5(src) != pin:
            sys.exit("STOP: %s is %s, expected %s" % (rel, md5(src)[:8], pin[:8]))
        t = src.decode("utf-8")
        for i, (a, b) in enumerate(P[rel], 1):
            n = t.count(a)
            if n != 1:
                sys.exit("STOP: %s patch %d: the anchor occurs %d times" % (rel, i, n))
            t = t.replace(a, b, 1)
        dst = os.path.join(out, os.path.basename(rel))
        open(dst, "wb").write(t.encode("utf-8"))
        print("built %s %s -> %s" % (rel, pin[:8], md5(t.encode("utf-8"))[:8]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: make_s826.py ROOT OUT")
    main(sys.argv[1], sys.argv[2])
