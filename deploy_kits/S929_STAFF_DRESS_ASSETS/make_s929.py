"""make_s929.py -- S929 (the parent, S498, 22-Nov-2026): staff_register.py 18973ca9 -> TO. The owner's word 14:25-14:34:
dress / i-card showing 'paused'. Found: three uniform pause windows (lost / damaged) opened Aug-Oct and never closed, and their
re-issues entered but never approved -- two separate manual steps nobody did.
  1. approving a uniform / i-card issue now CLOSES that item's open pause windows by itself (to the day before the issue);
  2. an issue records what was given: SIZE and PIECES (blazer, shirts, hoodie, white / blue T), and a note;
  3. the record page shows them; an old seed row dated 2000-01-01 reads 'before the register'; a 'superseded' entry has no Approve.
Anchored patches; nothing else changes."""
import hashlib, sys
FROM = "18973ca92609519ed9aea819a66b9f68"
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM:
    sys.exit("FROM pin mismatch: %s" % hashlib.md5(b).hexdigest())
t = b.decode("utf-8")
def rep(old, new, name):
    global t
    assert t.count(old) == 1, "anchor %s: %d" % (name, t.count(old))
    t = t.replace(old, new)
rep('    ("daily_register", "late_minutes", "INTEGER"), # S196: machine late minutes, stored fact\n]',
    '    ("daily_register", "late_minutes", "INTEGER"), # S196: machine late minutes, stored fact\n'
    '    ("issuance", "size", "TEXT"),                   # S929: what was given -- size\n'
    '    ("issuance", "pieces", "TEXT"),                 # S929: blazer / shirts / hoodie / white T / blue T\n'
    '    ("issuance", "note", "TEXT"),                   # S929\n]', "A migrations")
rep('''def add_issuance(sid, item, season, issued_date, actor):
    con = get_db()
    con.execute("INSERT INTO issuance(staff_id,item_type,season,issued_date,maker_user,"
                "maker_ts,status) VALUES(?,?,?,?,?,?, 'draft')",
                (sid, item, season or None, issued_date, actor, _now()))''',
'''def add_issuance(sid, item, season, issued_date, actor, size=None, pieces=None, note=None):
    con = get_db()
    con.execute("INSERT INTO issuance(staff_id,item_type,season,issued_date,maker_user,"
                "maker_ts,status,size,pieces,note) VALUES(?,?,?,?,?,?, 'draft',?,?,?)",
                (sid, item, season or None, issued_date, actor, _now(),
                 (size or "").strip()[:40] or None, (pieces or "").strip()[:200] or None,
                 (note or "").strip()[:200] or None))''', "B add_issuance")
rep('''def approve_issuance(iid, actor):
    con = get_db()
    con.execute("UPDATE issuance SET status='approved',checker_user=?,checker_ts=? "
                "WHERE id=?", (actor, _now(), iid))
    _audit(con, "issuance", iid, "approve", "draft", "approved", actor)
    con.commit()
    con.close()''',
'''def approve_issuance(iid, actor):
    con = get_db()
    con.execute("UPDATE issuance SET status='approved',checker_user=?,checker_ts=? "
                "WHERE id=?", (actor, _now(), iid))
    _audit(con, "issuance", iid, "approve", "draft", "approved", actor)
    _s929_close_pauses(con, iid, actor)
    con.commit()
    con.close()


def _s929_close_pauses(con, iid, actor):
    """S929 (22-Nov-2026): an APPROVED issue closes that staff member's open pause windows for the same item that began on
    or before the issue -- to the day before the issue (never before the window's own start). The fine resumes from the
    issue day. Returns how many were closed. Same connection; the caller commits."""
    i = con.execute("SELECT staff_id, item_type, issued_date, status FROM issuance WHERE id=?", (iid,)).fetchone()
    if not i or i["status"] != "approved" or not i["issued_date"]:
        return 0
    try:
        day_before = (datetime.date.fromisoformat(i["issued_date"][:10]) - datetime.timedelta(days=1)).isoformat()
    except ValueError:
        return 0
    n = 0
    for p in con.execute("SELECT id, from_date FROM issuance_pause WHERE staff_id=? AND item_type=? AND to_date IS NULL "
                         "AND from_date<=?", (i["staff_id"], i["item_type"], i["issued_date"][:10])).fetchall():
        to = max(day_before, p["from_date"])
        con.execute("UPDATE issuance_pause SET to_date=?, checker_user=?, checker_ts=?, status='closed' WHERE id=? "
                    "AND to_date IS NULL", (to, actor, _now(), p["id"]))
        _audit(con, "pause", p["id"], "close", "open", "closed %s (re-issue approved, S929)" % to, actor)
        n += 1
    return n''', "C approve")
rep('''                 request.form.get("season"), request.form.get("issued_date") or _today(),
                 u["user"])''',
'''                 request.form.get("season"), request.form.get("issued_date") or _today(),
                 u["user"], request.form.get("size"), request.form.get("pieces"))   # S929''', "D route")
rep('<thead><tr><th>Item</th><th>Season</th><th>Issued</th><th>Status</th><th></th></tr></thead>',
    '<thead><tr><th>Item</th><th>Season</th><th>Issued</th><th>Size</th><th>What was given</th><th>Status</th><th></th></tr></thead>', "E head")
rep('''            <td>{{ i.issued_date }}</td>''',
'''            <td>{{ 'before the register' if i.issued_date == '2000-01-01' else i.issued_date }}</td>
            <td>{{ i.size or '—' }}</td>
            <td>{{ i.pieces or '—' }}{% if i.note %} <span class="gate">· {{ i.note }}</span>{% endif %}</td>''', "F row")
rep('''{% else %}<tr><td colspan="5" class="note">Nothing issued yet.</td></tr>{% endfor %}''',
    '''{% else %}<tr><td colspan="7" class="note">Nothing issued yet.</td></tr>{% endfor %}''', "G empty")
rep('''            <td>{% if i.status!='approved' and caps.check %}''',
    '''            <td>{% if i.status=='draft' and caps.check %}''', "H approve only drafts")
rep('''      <button class="btn" type="submit">Issue / re-issue</button>''',
    '''      <input name="size" placeholder="size (e.g. L 38)" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px;width:120px">
      <input name="pieces" placeholder="what was given (e.g. Blazer 1 · Shirts 2)" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px;min-width:240px">
      <button class="btn" type="submit">Issue / re-issue</button>''', "I form")
rep('''            <td>{% if i.status=='approved' %}<span class="pill approved">approved</span>
                {% else %}<span class="pill draft">pending</span>{% endif %}</td>''',
    '''            <td>{% if i.status=='approved' %}<span class="pill approved">approved</span>
                {% elif i.status=='superseded' %}<span class="pill empty">superseded</span>
                {% else %}<span class="pill draft">pending</span>{% endif %}</td>''', "J superseded")
open(dst, "w", encoding="utf-8", newline="").write(t)
print(hashlib.md5(t.encode("utf-8")).hexdigest())
