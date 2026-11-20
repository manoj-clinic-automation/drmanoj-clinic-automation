# make_s898.py -- kit S898_PHONE_STUCK_AND_SILENT: three live files from their exact bytes, by anchors.
#   python3 make_s898.py <supplier_msg.py> <porders_s454.py> <finance_approvals.html> <outdir>
import hashlib, os, sys
PINS = {"supplier_msg.py": "bdfe4ce75ca0930b92ecd4fd960723cd", "porders_s454.py": "c992ba910315200293fdd7273ebbfacb",
        "finance_approvals.html": "f045686d8f53535184bbb64758165118"}
src = dict(zip(PINS, sys.argv[1:4])); out = sys.argv[4]


def load(name):
    b = open(src[name], "rb").read()
    assert hashlib.md5(b).hexdigest() == PINS[name], "%s is not at its FROM pin" % name
    return b.decode("utf-8")


def rep(s, a, b, name):
    assert s.count(a) == 1, ("%s: anchor found %d times: %r" % (name, s.count(a), a[:90]))
    return s.replace(a, b)


# ---------------------------------------------------------------- supplier_msg.py
s = load("supplier_msg.py")
s = rep(s, '''    con.commit()
    _s454_done(con, mid, ok, errt)                       # S454: an order message sent makes its supplier ORDERED; one failed is withdrawn''',
'''    con.commit()
    _s898_done_seen(con)                                 # S898: the phone's 'sent' report arrived -- when, for the silent-phone line
    _s454_done(con, mid, ok, errt)                       # S454: an order message sent makes its supplier ORDERED; one failed is withdrawn''', "supplier_msg.py")
s = rep(s, '''    p = pending(con)
    if p:
        lines.append(dict(cls="warn", target="bank", text="%d supplier message%s unsent (%d min or more)" % (len(p), "" if len(p) == 1 else "s", PENDING_MIN)))''',
'''    p = pending(con)
    if p:
        lines.append(dict(cls="warn", target="bank", text="%d supplier message%s unsent (%d min or more)" % (len(p), "" if len(p) == 1 else "s", PENDING_MIN)))
    sil = s898_silent_line(con)                          # S898: the phone takes messages but its 'sent' reports stopped
    if sil:
        lines.append(sil)''', "supplier_msg.py")
s = s.rstrip("\n") + '''


# ==========================================================================================================================================
# S898_PHONE_STUCK_AND_SILENT (20-Nov-2026, Sanjeevni session 490; the owner 17:35-17:49 IST). From 12-Nov the reception phone's MacroDroid
# sent every message but its last step ('sent' report, POST /done) was refused on the phone by an action constraint (App foreground,
# WhatsApp Business) -- no report reached the server for eight days, and the only sign was a line per order 'never confirmed'.
#   * the phone's last 'sent' report is kept (setting supplier_msg.phone_done_last);
#   * ONE Needs-you line when the phone took messages (15 min to 24 h ago, none reported) and its last report is older than them;
#   * the messages the phone took and never reported (payment notices, month-summary reminders) are listed on the owner's Reception
#     phone card with 'Send again' (handed to the phone once more) and 'Remove' (marked skipped, kept) -- per message and for all.
# Never the key, never a number or a body on any page or line.
# ==========================================================================================================================================
S898_DONE_KEY = "supplier_msg.phone_done_last"
S898_KINDS_HI = {"neft": "payment notice", "cheque": "payment notice", "summary": "month-summary reminder"}


def _s898_done_seen(con):
    try:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (S898_DONE_KEY, _iso(), "S898 -- when the reception phone's 'sent' report last reached the server"))
        con.commit()
    except Exception:                                          # noqa: BLE001 -- the door never fails for its own record
        pass


def _s898_ddmm(iso):
    s = str(iso or "")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if len(s) >= 16 else (s or "never")


def s898_last_done(con):
    a = str(_setting(con, S898_DONE_KEY, "") or "")
    try:
        r = con.execute("SELECT MAX(sent_at) FROM supplier_msg WHERE sent_by='reception-phone'").fetchone()
        b = str(r[0] or "") if r else ""
    except Exception:                                          # noqa: BLE001
        b = ""
    return max(a, b)


def s898_silent_line(con):
    """One Needs-you line, or None: messages handed to the phone 15 min - 24 h ago, none reported since, and no report newer than them."""
    try:
        now = _now()
        lo, hi = (now - dt.timedelta(hours=24)).isoformat(), (now - dt.timedelta(minutes=15)).isoformat()
        r = con.execute("SELECT COUNT(*), MIN(handed_at), MAX(handed_at) FROM supplier_msg WHERE handed_at>=? AND handed_at<=? AND status<>'sent'",
                        (lo, hi)).fetchone()
        n, first, last = int(r[0] or 0), r[1], r[2]
        if not n:
            return None
        done = s898_last_done(con)
        if done and done >= str(last):
            return None
        return dict(cls="bad", target="bank",
                    text="The reception phone took %d message%s since %s but its 'sent' report has not reached the server since %s -- the messages may "
                         "well have gone. On the reception phone: MacroDroid > System Log, the last step (HTTP Request POST) of 'Sanjeevni Whatsapp'."
                         % (n, "" if n == 1 else "s", _s898_ddmm(first), _s898_ddmm(done)))
    except Exception:                                          # noqa: BLE001
        return None


def s898_stuck(con, older_min=30):
    """The messages the phone took and never reported (not orders -- they settle themselves -- and not tests): id, kind, vendor, times."""
    cut = (_now() - dt.timedelta(minutes=older_min)).isoformat()
    rows = con.execute("SELECT id, kind, month, vendor, queued_at, handed_at FROM supplier_msg WHERE handed_at IS NOT NULL AND handed_at<=? "
                       "AND status IN ('queued','failed') AND kind NOT IN ('order','test') AND to_number IS NOT NULL AND attempts<? "
                       "ORDER BY handed_at, id", (cut, MAX_ATTEMPTS)).fetchall()
    return [dict(id=r[0], kind=r[1], what=S898_KINDS_HI.get(r[1], r[1]), month=r[2], vendor=str(r[3] or "").strip(),
                 queued=_s898_ddmm(r[4]), handed=_s898_ddmm(r[5])) for r in rows]


def _s898_ids(con, ids):
    ok = {x["id"] for x in s898_stuck(con, 0)}
    out = []
    for v in ids or []:
        try:
            i = int(v)
        except (TypeError, ValueError):
            continue
        if i in ok:
            out.append(i)
    return out


def s898_resend(con, who, ids):
    """Handed to the phone once more (its 'handed' mark cleared). Only messages still on the stuck list."""
    good = _s898_ids(con, ids)
    for i in good:
        con.execute("UPDATE supplier_msg SET handed_at=NULL, status='queued' WHERE id=? AND status IN ('queued','failed')", (i,))
    try:
        _pa()._audit(con, who, "s898_resend", "supplier_msg", dict(ids=good))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return len(good)


def s898_remove(con, who, ids):
    """Taken off every list (status skipped, the row kept with who and when). Only messages still on the stuck list."""
    good = _s898_ids(con, ids)
    for i in good:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=? AND status IN ('queued','failed')",
                    ("removed by %s %s (S898): taken by the phone, never reported" % (str(who)[:40], _iso()[:16].replace("T", " ")), i))
    try:
        _pa()._audit(con, who, "s898_remove", "supplier_msg", dict(ids=good))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return len(good)
'''
open(os.path.join(out, "supplier_msg.py"), "wb").write(s.encode("utf-8"))

# ---------------------------------------------------------------- porders_s454.py
p = load("porders_s454.py")
p = rep(p, '''def phone_card(con, st):
    import supplier_msg as SM                                 # noqa: PLC0415''', '''def phone_card(con, st):
    """S898: the S454 card, with the phone's last 'sent' report and the messages it took and never reported. Fail-soft."""
    h = _s454_phone_card(con, st)
    try:
        h = h[:h.rindex("</div>")] + _s898_block(con) + "</div>"
    except Exception:                                         # noqa: BLE001 -- the card never waits on its new part
        pass
    return h


def _s898_block(con):
    import supplier_msg as SM                                 # noqa: PLC0415
    done = SM.s898_last_done(con)
    rows = SM.s898_stuck(con)
    h = ['<div id="s898" style="margin-top:10px;border-top:1px solid #ccc;padding-top:8px">',
         '<div>Last "sent" report from the phone: <b>%s</b></div>' % esc(SM._s898_ddmm(done) if done else "never")]
    if rows:
        ids = [r["id"] for r in rows]
        h.append('<div style="margin-top:6px"><b>Taken by the phone, never reported: %d</b> '
                 '<span style="color:#666;font-size:13px">-- they may have gone. Send again, or remove from every list (kept on record).</span></div>' % len(rows))
        h.append('<div style="margin:6px 0"><button style="min-height:36px" onclick="s898t(this,\\'resend\\',%s)">Send all %d again</button> '
                 '<button style="min-height:36px" onclick="s898t(this,\\'remove\\',%s)">Remove all %d</button></div>'
                 % (json.dumps(ids), len(rows), json.dumps(ids), len(rows)))
        h.append('<table style="border-collapse:collapse;font-size:14px"><tr><th align="left">Dealer</th><th align="left">What</th>'
                 '<th align="left">Taken by the phone</th><th></th></tr>')
        for r in rows:
            h.append('<tr><td style="padding:3px 8px 3px 0">%s</td><td style="padding:3px 8px">%s%s</td><td style="padding:3px 8px">%s</td>'
                     '<td><button onclick="s898t(this,\\'resend\\',[%d])">Send again</button> <button onclick="s898t(this,\\'remove\\',[%d])">Remove</button></td></tr>'
                     % (esc(r["vendor"]), esc(r["what"]), (" (%s)" % esc(r["month"])) if r["month"] else "", esc(r["handed"]), r["id"], r["id"]))
        h.append('</table>')
    else:
        h.append('<div style="color:#2f6b45">Nothing taken by the phone is left unreported.</div>')
    h.append('<script>function s898t(b,a,ids){if(!b.dataset.armed){b.dataset.armed="1";b.dataset.t=b.textContent;b.textContent="Tap again to confirm";'
             'setTimeout(function(){if(b.dataset.armed){delete b.dataset.armed;b.textContent=b.dataset.t;}},5000);return;}b.disabled=true;'
             'fetch("/finance/porders/api/s898/"+a,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids:ids})})'
             '.then(function(r){return r.json();}).then(function(j){if(!j.ok){b.textContent=j.message||j.error||"Not done";return;}location.reload();})'
             '.catch(function(){b.textContent="Not done (network)";});}</script></div>')
    return "".join(h)


def _s454_phone_card(con, st):
    import supplier_msg as SM                                 # noqa: PLC0415''', "porders_s454.py")
p = rep(p, '''@bp.route(P + "/api/s454/test_send", methods=["POST"])''', '''@bp.route(P + "/api/s898/resend", methods=["POST"])
def api_s898_resend():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    n = SM.s898_resend(con, who(u), (_body().get("ids") or [])[:200])
    return (jsonify(ok=True, done=n), 200) if n else (jsonify(ok=False, message="Nothing to send again -- the list moved; reload."), 409)


@bp.route(P + "/api/s898/remove", methods=["POST"])
def api_s898_remove():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    n = SM.s898_remove(con, who(u), (_body().get("ids") or [])[:200])
    return (jsonify(ok=True, done=n), 200) if n else (jsonify(ok=False, message="Nothing to remove -- the list moved; reload."), 409)


@bp.route(P + "/api/s454/test_send", methods=["POST"])''', "porders_s454.py")
open(os.path.join(out, "porders_s454.py"), "wb").write(p.encode("utf-8"))

# ---------------------------------------------------------------- finance_approvals.html (the Hub's Go to)
f = load("finance_approvals.html")
f = rep(f, '''        <a href="/finance/purchase/page/phone-setup">Reception phone (supplier WhatsApp)</a></div>''',
'''        <a href="/finance/purchase/page/phone-setup">Reception phone (supplier WhatsApp)</a>
        <a href="/finance/porders?old=1#s454phone">Reception phone — test message, messages not reported</a></div>''', "finance_approvals.html")
open(os.path.join(out, "finance_approvals.html"), "wb").write(f.encode("utf-8"))
for n in ("supplier_msg.py", "porders_s454.py", "finance_approvals.html"):
    print("make_s898:", n, hashlib.md5(open(os.path.join(out, n), "rb").read()).hexdigest())
