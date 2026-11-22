"""make_s931.py -- S931 (the parent, S498, 22-Nov-2026): staff_register.py 22a75b96 (S929) -> TO. The owner's word 15:11:
'pause shd start only with Shavez or my approval, reception can only initiate it.'
  1. a pause opened by a CHECKER (Shavez) or a doctor starts at once (status 'open'); one opened by a maker (reception:
     Alisha, Shivani) is an ASK (status 'requested') -- it does NOT stop the fine until Shavez or a doctor approves it;
  2. Approve / Reject on the person's page (checker / doctor only); a rejected ask never counts;
  3. the asks are shown: 'PAUSE ASKED' on the staff list, a card on Pending review, and counted in the portal tile's
     'to approve' for those who approve;
  4. S929's auto-close on a re-issue closes started pauses only, never an ask.
Anchored patches; nothing else changes."""
import hashlib, sys
FROM = "22a75b9637050f9e57b99faf59fb98a9"
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM:
    sys.exit("FROM pin mismatch: %s" % hashlib.md5(b).hexdigest())
t = b.decode("utf-8")
def rep(old, new, name, n=1):
    global t
    assert t.count(old) == n, "anchor %s: %d" % (name, t.count(old))
    t = t.replace(old, new)
# 1 the fine gate: an ask or a rejected ask never pauses
rep('''        "SELECT 1 FROM issuance_pause WHERE staff_id=? AND item_type=? "
        "AND from_date<=? AND (to_date IS NULL OR to_date>=?)",''',
    '''        "SELECT 1 FROM issuance_pause WHERE staff_id=? AND item_type=? "
        "AND from_date<=? AND (to_date IS NULL OR to_date>=?) "
        "AND COALESCE(status,'') NOT IN ('requested','rejected')",   # S931: an ask counts only once approved''', "A gate")
# 2 add_pause: status by who opens it
rep('''def add_pause(sid, item, from_date, reason, actor):
    """Open a fine-pause window (item lost / damaged / being purchased). Effective
    immediately (protects the staffer) — the daily gate reads it at once."""
    con = get_db()
    con.execute("INSERT INTO issuance_pause(staff_id,item_type,from_date,to_date,reason,"
                "maker_user,maker_ts,status) VALUES(?,?,?,NULL,?,?,?, 'open')",
                (sid, item, from_date, reason, actor, _now()))
    _audit(con, "pause", sid, "open", "", "%s from %s" % (item, from_date), actor)''',
'''def add_pause(sid, item, from_date, reason, actor, approved=True):
    """Open a fine-pause window (item lost / damaged / being purchased). S931 (the owner 22-Nov): opened by Shavez or a
    doctor (approved=True) it starts at once; opened by reception (approved=False) it is an ASK ('requested') that does not
    stop the fine until Shavez or a doctor approves it."""
    con = get_db()
    st = "open" if approved else "requested"
    con.execute("INSERT INTO issuance_pause(staff_id,item_type,from_date,to_date,reason,"
                "maker_user,maker_ts,status) VALUES(?,?,?,NULL,?,?,?,?)",
                (sid, item, from_date, reason, actor, _now(), st))
    _audit(con, "pause", sid, "open" if approved else "ask", "", "%s from %s" % (item, from_date), actor)''', "B add_pause")
rep('''def close_pause(pid, to_date, actor):''',
'''def decide_pause(pid, approve, actor):
    """S931: Shavez or a doctor approves (the pause starts from its own date) or rejects a reception ask."""
    con = get_db()
    p = con.execute("SELECT * FROM issuance_pause WHERE id=?", (pid,)).fetchone()
    if not p or p["status"] != "requested":
        con.close()
        return None
    st = "open" if approve else "rejected"
    con.execute("UPDATE issuance_pause SET status=?, checker_user=?, checker_ts=? WHERE id=? AND status='requested'",
                (st, actor, _now(), pid))
    _audit(con, "pause", pid, "approve" if approve else "reject", "requested", st, actor)
    con.commit()
    sid = p["staff_id"]
    con.close()
    return sid


def pause_asks(con):
    """S931: the open reception asks, oldest first -- [{id, sid, name, item, from, reason, by}]."""
    try:
        return [{"id": r["id"], "sid": r["staff_id"], "name": r["name"], "item": r["item_type"], "from": r["from_date"],
                 "reason": r["reason"] or "", "by": r["maker_user"] or ""}
                for r in con.execute("SELECT p.*, s.name FROM issuance_pause p JOIN staff s ON s.staff_id=p.staff_id "
                                     "WHERE p.status='requested' ORDER BY p.from_date, p.id")]
    except Exception:                                    # noqa: BLE001 -- pre-init DB
        return []


def close_pause(pid, to_date, actor):''', "C decide")
# 3 S929's auto-close: started pauses only
rep('''    for p in con.execute("SELECT id, from_date FROM issuance_pause WHERE staff_id=? AND item_type=? AND to_date IS NULL "
                         "AND from_date<=?", (i["staff_id"], i["item_type"], i["issued_date"][:10])).fetchall():''',
'''    for p in con.execute("SELECT id, from_date FROM issuance_pause WHERE staff_id=? AND item_type=? AND to_date IS NULL "
                         "AND from_date<=? AND COALESCE(status,'') NOT IN ('requested','rejected')",   # S931
                         (i["staff_id"], i["item_type"], i["issued_date"][:10])).fetchall():''', "D autoclose")
# 4 routes
rep('''    add_pause(sid, request.form.get("item", "uniform"),
              request.form.get("from_date") or _today(),
              request.form.get("reason", ""), u["user"])
    return redirect(APP_PREFIX + "/staff/%d?m=Pause+started&c=ok" % sid)''',
'''    ok = bool(u["caps"].get("check"))                    # S931: Shavez / a doctor start it; reception asks
    add_pause(sid, request.form.get("item", "uniform"),
              request.form.get("from_date") or _today(),
              request.form.get("reason", ""), u["user"], approved=ok)
    return redirect(APP_PREFIX + "/staff/%d?m=%s&c=ok" % (sid, "Pause+started" if ok else
                    "Pause+asked+%E2%80%94+it+starts+when+Shavez+or+the+doctor+approves"))


@app.route(APP_PREFIX + "/pause/decide", methods=["POST"])
@require("check")
def pause_decide_route():
    """S931: approve / reject a reception pause ask."""
    u = current_user(request)
    try:
        pid = int(request.form.get("pid"))
    except (TypeError, ValueError):
        abort(400)
    ok = request.form.get("act") == "approve"
    sid = decide_pause(pid, ok, u["user"])
    back = request.form.get("back") == "review"
    if sid is None:
        return redirect(APP_PREFIX + ("/review?m=Already+decided&c=err" if back else "/staff"))
    msg = "Pause+approved+%E2%80%94+the+fine+is+off+from+its+date" if ok else "Pause+ask+rejected"
    return redirect(APP_PREFIX + ("/review?m=%s&c=ok" % msg if back else "/staff/%d?m=%s&c=ok" % (sid, msg)))''', "E routes")
# 5 the person's page: status + approve/reject; Close only for a started pause
rep('''      <thead><tr><th>Item</th><th>From</th><th>To</th><th>Reason</th><th></th></tr></thead>''',
    '''      <thead><tr><th>Item</th><th>From</th><th>To</th><th>Reason</th><th>Status</th><th></th></tr></thead>''', "F head")
rep('''            <td>{{ p.to_date or 'open' }}</td><td>{{ p.reason or '—' }}</td>
            <td>{% if not p.to_date and caps.check %}''',
'''            <td>{{ p.to_date or 'open' }}</td><td>{{ p.reason or '—' }}</td>
            <td>{% if p.status=='requested' %}<span class="pill draft">asked by {{ p.maker_user or '?' }} &mdash; not counted yet</span>
                {% elif p.status=='rejected' %}<span class="pill empty">rejected</span>
                {% elif p.to_date %}<span class="pill empty">closed</span>{% else %}<span class="pill approved">paused</span>{% endif %}</td>
            <td>{% if p.status=='requested' and caps.check %}
                <form method="POST" action="{{ prefix }}/pause/decide" style="display:flex;gap:6px">
                  <input type="hidden" name="pid" value="{{ p.id }}">
                  <button class="btn green" name="act" value="approve" type="submit">Approve</button>
                  <button class="btn ghost" name="act" value="reject" type="submit">Reject</button></form>
                {% elif not p.to_date and p.status not in ('requested','rejected') and caps.check %}''', "G row")
rep('''      {% else %}<tr><td colspan="5" class="note">No pause windows.</td></tr>{% endfor %}''',
    '''      {% else %}<tr><td colspan="6" class="note">No pause windows.</td></tr>{% endfor %}''', "H empty")
rep('''      <button class="btn" type="submit">Start pause</button>''',
    '''      <button class="btn" type="submit">{{ 'Start pause' if caps.check else 'Ask for a pause' }}</button>
      {% if not caps.check %}<span class="note">Shavez or the doctor approves it; until then the fine stays.</span>{% endif %}''', "I button")
rep('''    <p class="note">Open a window while an item is being replaced; the dress/i-card fine
       is paused for those dates until you close it on re-issue.</p>''',
'''    <p class="note">Open a window while an item is being replaced; the dress/i-card fine
       is paused for those dates until the re-issue is approved. Reception asks; Shavez or the doctor approves.</p>''', "J note")
# 6 staff list: the ask shown
rep('''        sd["uniform_ok"] = issuance_ok(con, s["staff_id"], "uniform", d)
        sd["icard_ok"] = issuance_ok(con, s["staff_id"], "icard", d)
        dec.append(sd)''',
'''        sd["uniform_ok"] = issuance_ok(con, s["staff_id"], "uniform", d)
        sd["icard_ok"] = issuance_ok(con, s["staff_id"], "icard", d)
        sd["asks"] = [r[0] for r in con.execute("SELECT item_type FROM issuance_pause WHERE staff_id=? AND status='requested'",
                                                (s["staff_id"],))]      # S931
        dec.append(sd)''', "K list data")
rep('''        <td><a class="btn ghost" href="{{ prefix }}/staff/{{ s.staff_id }}">Open</a></td>''',
'''        <td>{% if s.asks %}<span class="pill draft">PAUSE ASKED{{ ' · ' + s.asks|join(', ') }}</span> {% endif %}<a class="btn ghost" href="{{ prefix }}/staff/{{ s.staff_id }}">Open</a></td>''', "L list cell")
# 7 Pending review: a card + the count for approvers
rep('''            "xreq": _exit_board(con, ym, actor, can_check), }''',
'''            "xreq": _exit_board(con, ym, actor, can_check),
            "pasks": pause_asks(con) if can_check else [], }''', "M board")
rep('''  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">&#9989; Awaiting approval''',
'''  {% if bd.pasks %}
  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">&#128085; Dress / i-card pause asks
      <span class="pill draft">{{ bd.pasks|length }}</span></h2>
    <div class="note" style="margin:0 0 8px">Asked by reception. Not counted until approved &mdash; approve and the fine is off from the date asked.</div>
    <div class="tblwrap"><table>
      <tr><th>Staff</th><th>Item</th><th>From</th><th>Reason</th><th>Asked by</th><th></th></tr>
      {% for a in bd.pasks %}
      <tr><td class="nm"><a href="{{ prefix }}/staff/{{ a.sid }}">{{ a.name }}</a></td><td>{{ a.item }}</td><td>{{ a.from }}</td>
          <td>{{ a.reason or '—' }}</td><td>{{ a.by }}</td>
          <td><form method="POST" action="{{ prefix }}/pause/decide" style="display:flex;gap:6px">
            <input type="hidden" name="pid" value="{{ a.id }}"><input type="hidden" name="back" value="review">
            <button class="btn green" name="act" value="approve" type="submit">Approve</button>
            <button class="btn ghost" name="act" value="reject" type="submit">Reject</button></form></td></tr>
      {% endfor %}
    </table></div>
  </div>
  {% endif %}

  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">&#9989; Awaiting approval''', "N card")
rep('''               "to_approve": (bd["to_approve"] if show_approve else 0),''',
    '''               "to_approve": ((bd["to_approve"] + len(bd.get("pasks") or [])) if show_approve else 0),   # S931: + pause asks''', "O counts")
open(dst, "w", encoding="utf-8", newline="").write(t)
print(hashlib.md5(t.encode("utf-8")).hexdigest())
