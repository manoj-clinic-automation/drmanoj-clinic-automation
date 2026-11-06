#!/usr/bin/env python3
"""make_s711.py -- S711_TRACK_FIXES (S388, Sanjeevni, 06-Nov-2026): the counted edits to three live files of this project.
    python3 -B make_s711.py <dir holding order_track_page.py, porders_s454.py, order_sheet.py> <out dir>
Each FROM file must carry its pinned md5; every edit must match exactly once; the TO md5s are printed.

  1  the PC scan viewer: the card's words and buttons BESIDE the bill, not below it (S710's live read, 06-Nov 07:5x)
  2  the wrong-dealer card (the owner, 07:59 06-Nov, B-0239): a reading that names no known dealer says "not read clearly"; the dealer it was
     saved under first and never cut off, with "<it> is right (as saved)"; the week's dealers; "Other dealer" = every dealer, with a search box;
     "Send back for rescan" on the card; a scan already with reception is not asked twice
  3  F-1121: the dealer door no longer ties a scan by itself -- it removes the wrong dealer's tie (and the arrival that tie alone made) and the
     S454 tie (order_sheet.tie_pass, its own rules) ties it; every dealer change is kept with an Undo (7 days on the page)
  4  F-1120: order_sheet.tie_pass never ties a scan picked as the copy (S708's s708_scan_pick)
  5  F-1123: S618's old reception list (?old=1) no longer fails when the scan app's database cannot be opened
"""
import hashlib
import os
import sys

FROM = {"order_track_page.py": "b6181b62164cccc95158c192e9d6e3f9", "porders_s454.py": "1bc312dd1ee0b2338852731c7e29da7a",
        "order_sheet.py": "1bba95ab52126a2e354ba8eca7bfe8f6"}

# ============================================================================================ order_track_page.py
OTP = []

# 1 -- the viewer on a PC: two columns, the bill left, the card's words and buttons right (always in view)
OTP.append(("""@media (min-width:900px){#s7v{left:auto;width:62vw;max-width:1000px;box-shadow:-6px 0 24px rgba(0,0,0,.16)}
 body.s7vo .wrap{margin-right:min(62vw,1000px);max-width:none}body.s7vo .s7cols{grid-template-columns:minmax(0,1fr)}
 body.s7vo .s7up{right:calc(min(62vw,1000px) + 16px)}#s7v .vimg iframe{height:calc(100vh - 230px)}}""",
"""@media (min-width:900px){#s7v{left:auto;width:74vw;max-width:1400px;box-shadow:-6px 0 24px rgba(0,0,0,.16)}
 body.s7vo .wrap{margin-right:min(74vw,1400px);max-width:none}body.s7vo .s7cols{grid-template-columns:minmax(0,1fr)}
 body.s7vo .s7up{right:calc(min(74vw,1400px) + 16px)}
 #s7v .vb{display:grid;grid-template-columns:minmax(0,1fr) clamp(240px,26%,340px);grid-template-rows:auto minmax(0,1fr);gap:12px;overflow:hidden}
 #s7v .vb>.vimg{grid-column:1;grid-row:1 / span 2;min-height:0;overflow:auto;align-items:flex-start}
 #s7v .vb>#s7vfull{grid-column:2;grid-row:1;align-self:start}
 #s7v .vb>.vact{grid-column:2;grid-row:2;min-height:0;overflow:auto;align-self:stretch}
 #s7v .vimg iframe{height:calc(100vh - 170px)}}
.s7dl{display:flex;flex-direction:column;gap:6px}.s7dl input{min-height:44px;font-size:16px;padding:0 10px;border:1px solid #c9c4bc;border-radius:9px}
.s7dl .dl{display:flex;flex-wrap:wrap;gap:6px;max-height:260px;overflow:auto}"""))

# 2a -- the JS for "Other dealer": the full list is drawn once on the page (S7DL), the buttons made in the card when it opens
OTP.append(("""document.addEventListener('keydown',function(e){var v=document.getElementById('s7v');""",
"""function s7other(b,key,sid){var box=b.parentNode;if(box.querySelector('.s7dl'))return false;var w=document.createElement('div');w.className='s7dl';
 var inp=document.createElement('input');inp.type='search';inp.placeholder=b.getAttribute('data-ph')||'';inp.setAttribute('autocomplete','off');
 inp.setAttribute('oninput','s7dlf(this)');
 var dl=document.createElement('div');dl.className='dl';(window.S7DL||[]).forEach(function(d,i){var x=document.createElement('button');x.type='button';
  x.className='s7btn';x.textContent=d[1];x.setAttribute('data-for',key);x.setAttribute('data-n',d[1].toUpperCase());x.setAttribute('data-i',String(i));
  x.setAttribute('data-sid',String(sid));x.setAttribute('onclick','s7dlp(this)');dl.appendChild(x);});
 w.appendChild(inp);w.appendChild(dl);box.appendChild(w);b.style.display='none';try{inp.focus();}catch(e){}return false;}
function s7dlp(x){var d=(window.S7DL||[])[parseInt(x.getAttribute('data-i'),10)];if(!d)return;
 s7act(x,'"""
 + "/finance/porders" + """/api/s454/s708/dealer',{scan:parseInt(x.getAttribute('data-sid'),10),dealer:d[0]});}
function s7dlf(inp){var q=inp.value.toUpperCase().replace(/[^A-Z0-9]/g,'');var dl=inp.parentNode.querySelector('.dl');if(!dl)return;
 Array.prototype.forEach.call(dl.children,function(x){x.style.display=(!q||x.getAttribute('data-n').replace(/[^A-Z0-9]/g,'').indexOf(q)>=0)?'':'none';});}
document.addEventListener('keydown',function(e){var v=document.getElementById('s7v');"""))

# 2b -- the words
OTP.append(("""    "s708_r_view": ("Pichhla scan dekhiye ↗", "See the last scan ↗"),
}""",
"""    "s708_r_view": ("Pichhla scan dekhiye ↗", "See the last scan ↗"),
    # S711
    "s711_unread": ("Kaagaz par dealer ka naam saaf nahi padha gaya (padha: “%s”). Save hua: %s.",
                    "The paper's dealer could not be read clearly (read as “%s”). Saved as %s."),
    "s711_saved_ok": ("%s sahi hai (jaisa save hai)", "%s is right (as saved)"),
    "s711_or_pick": ("Ya scan dekhkar sahi dealer chuniye:", "Or open the scan and pick the dealer:"),
    "s711_other": ("Koi aur dealer ▸", "Other dealer ▸"),
    "s711_find": ("Dealer ka naam likhiye", "Type the dealer's name"),
    "s711_g_changed": ("Dealer badla gaya (7 din)", "Dealer changed (7 days)"),
    "s711_changed_l": ("Pehle: %s → ab: %s", "Was: %s → now: %s"),
    "s711_undone": ("Wapas kar diya — dealer pehle jaisa. Page dobara kholiye.", "Undone — the dealer is as before. Reload the page."),
    "s711_undone_part": ("Dealer pehle jaisa kar diya — par purane order par ab dusra scan hai, isliye yeh scan apne order ka intezaar karega.",
                         "The dealer is as before — but its old order now has another scan, so this scan waits for its order again."),
}"""))

# 2c -- the saved dealer first (never cut off) + the full list
OTP.append(('''def dealer_choices(con, ctx, sid):
    """[(supplier key, the name as ordered)] -- the dealers of the orders made in the 7 days before the scan, newest first, and the dealer it
    was saved under: the server's own list for the 'pick the dealer' door (never the browser's). At most 6."""
    OT = _ot()
    pa = OT._pa()
    s = ctx.scans.get(int(sid)) or {}
    at = s.get("at")
    out, seen = [], set()
    if at is not None:''',
'''def saved_choice(con, ctx, sid):
    """S711: (supplier key, name) of the dealer the scan was saved under -- the S454 tie's own reading of that name (order_sheet._resolver, so a
    spelling of a known dealer becomes that dealer), else its plain key; None when the scan has no dealer name."""
    s = ctx.scans.get(int(sid)) or {}
    name = str(s.get("vendor") or "").strip()
    if not name:
        return None
    k = None
    try:
        k = _os()._resolver(con)({"id": 0, "vendor": name})
    except Exception:                                         # noqa: BLE001
        k = None
    k = k or _ot()._pa().supplier_key(name)
    return (k, name) if k else None


def all_dealers(con):
    """S711: [(supplier key, name)] -- every dealer of a Marg purchase bill or an order (the newest spelling of each), A-Z: the 'Other dealer'
    list. The server's own list (the door checks a pick against it); never the browser's."""
    pa = _ot()._pa()
    out = {}
    for q in ("SELECT supplier, MAX(COALESCE(bill_date,'')) FROM purchase_bill WHERE COALESCE(supplier,'')<>'' GROUP BY supplier",
              "SELECT vendor, MAX(COALESCE(created_at,'')) FROM purchase_order WHERE COALESCE(vendor,'')<>'' GROUP BY vendor"):
        try:
            rows = con.execute(q).fetchall()
        except sqlite3.Error:
            continue
        for name, at in rows:
            k = pa.supplier_key(name or "")
            if k and (k not in out or str(at) > out[k][1]):
                out[k] = (str(name).strip(), str(at))
    return sorted(((k, v[0]) for k, v in out.items()), key=lambda x: (x[1].upper(), x[0]))


def dealer_choices(con, ctx, sid):
    """[(supplier key, name)] -- S711: the dealer the scan was saved under FIRST (never cut off), then the dealers of the orders made in the 7
    days before the scan, newest first: the server's own list for the 'pick the dealer' door (never the browser's). At most 9 (the saved one + 8).
    (S708 put the saved dealer last of 6, so a busy week cut it off -- B-0239, 06-Nov.)"""
    OT = _ot()
    pa = OT._pa()
    s = ctx.scans.get(int(sid)) or {}
    at = s.get("at")
    out, seen = [], set()
    sv = saved_choice(con, ctx, sid)
    if sv:
        seen.add(sv[0])
        out.append(sv)
    if at is not None:'''))
OTP.append(('''        except sqlite3.Error:
            pass
    k = pa.supplier_key(s.get("vendor") or "")
    if k and k not in seen:
        out.append((k, str(s.get("vendor"))))
    return out[:6]''',
'''        except sqlite3.Error:
            pass
    return out[:9]


def dealer_changes(con, since_iso):
    """S711: the dealer changes (porders_s454's s711_dealer_change) made since since_iso and not undone, newest first. Fail-soft."""
    try:
        return [dict(r) for r in con.execute("SELECT id, scan, stamp, saved, dealer, tie_to, by, at FROM s711_dealer_change WHERE undone_at IS NULL "
                                             "AND at>=? ORDER BY id DESC", (since_iso,))]
    except sqlite3.Error:
        return []'''))

# 2d -- the model: a scan with an open rescan ask is with reception -- its dealer is asked again on the new scan, not twice; the changes
OTP.append(('''    wd = [w for w in OT.wrong_dealer(con, ctx) if int(w["scan"]) not in getattr(ctx, "dropped", ())]''',
'''    with_rec = {int(a["scan"]) for a in redo.get("asks") or []}                          # S711: already with reception for a rescan
    wd = [w for w in OT.wrong_dealer(con, ctx) if int(w["scan"]) not in getattr(ctx, "dropped", ()) and int(w["scan"]) not in with_rec]'''))
OTP.append(('''    kept = [p for p in picks(con) if str(p.get("picked_at") or "") >= lo]
    return dict(now=now, stale=stale,''',
'''    kept = [p for p in picks(con) if str(p.get("picked_at") or "") >= lo]
    changed = dealer_changes(con, lo)                                                    # S711
    return dict(changed=changed, now=now, stale=stale,'''))

# 2e -- the wrong-dealer card
OTP.append(('''def _wrong_card(con, en, m, w, asker):
    OT, ctx = _ot(), m["ctx"]
    key = "wrong-%d" % w["scan"]
    pk = OT.paper_dealer(con, ctx, w["scan"])
    title = "%s · %s" % (w["stamp"], _ddmm(w["date"]))
    say = ("saved as %s; the paper says %s" if en else "%s ke naam se save; kaagaz par %s") % (w["saved"], w["paper"])
    acts = ""
    if asker and pk:
        acts = _act(en, key, _p4().L(en, "fix_dealer", pk), "/api/s454/dealer_fix", {"scan": int(w["scan"])}, "g", ok=_L(en, "s708_dealer_ok2", pk))
    elif asker:
        ch = dealer_choices(con, ctx, w["scan"])
        if ch:
            acts = '<div class="s7s">%s</div><div style="display:flex;flex-wrap:wrap;gap:6px">%s</div>' % (_L(en, "s708_pick_d"), "".join(
                _act(en, key, name, "/api/s454/s708/dealer", {"scan": int(w["scan"]), "dealer": k}) for k, name in ch))
        else:
            acts = '<div class="s7amb">%s</div>' % _L(en, "s708_no_choice")
    return''',
'''def _wrong_card(con, en, m, w, asker):
    """S711: a paper whose reading names a KNOWN dealer (paper_dealer) -- Change dealer to it, one tap; a reading that names no known dealer
    (a slanted or blurred scan) -- 'not read clearly'. Either way: the saved dealer is right (as saved), the week's dealers, every dealer
    (Other dealer, with a search box), and Send back for rescan. Every pick goes to the one door (/s708/dealer), which offers Undo."""
    OT, P4, ctx = _ot(), _p4(), m["ctx"]
    sid = int(w["scan"])
    key = "wrong-%d" % sid
    pk = OT.paper_dealer(con, ctx, sid)
    title = "%s · %s" % (w["stamp"], _ddmm(w["date"]))
    if pk:
        say = ("saved as %s; the paper says %s" if en else "%s ke naam se save; kaagaz par %s") % (w["saved"], w["paper"])
    else:
        say = _L(en, "s711_unread", w["paper"], w["saved"])
    acts = ""
    if asker:
        ch = dealer_choices(con, ctx, sid)
        sv = saved_choice(con, ctx, sid)
        names = dict(all_dealers(con))
        parts = []
        if pk:
            parts.append(_act(en, key, P4.L(en, "fix_dealer", names.get(pk) or pk), "/api/s454/s708/dealer", {"scan": sid, "dealer": pk}, "g"))
        if sv:
            parts.append(_act(en, key, _L(en, "s711_saved_ok", sv[1]), "/api/s454/s708/dealer", {"scan": sid, "dealer": sv[0]}, "" if pk else "g"))
        rest = [(k, name) for k, name in ch if k != pk and not (sv and k == sv[0])]
        if rest:
            parts.append('<div class="s7s">%s</div><div style="display:flex;flex-wrap:wrap;gap:6px">%s</div>' % (_L(en, "s711_or_pick"), "".join(
                _act(en, key, name, "/api/s454/s708/dealer", {"scan": sid, "dealer": k}) for k, name in rest)))
        parts.append('<div><button type="button" class="s7btn q" data-ph="%s" onclick="return s7other(this,%s,%d)">%s</button></div>'
                     % (_e(_L(en, "s711_find")), _e(json.dumps(key)), sid, _L(en, "s711_other")))
        sq = P4._sq()
        if sq:
            parts.append('<div class="s7s">%s</div><div style="display:flex;flex-wrap:wrap;gap:6px">%s</div>' % (P4.L(en, "send_back"), "".join(
                _act(en, key, sq.CHIP_WORDS[c][0 if en else 1], "/api/s454/rescan", {"asset_bill_id": sid, "reason": c}, ok=P4.L(en, "sent_back"))
                for c in sq.CHIPS)))
        acts = "".join(parts)
    return'''))

# 2f -- the changed dealers' cards (with Undo), beside the kept picks
OTP.append(('''def _conflict_card(en, m, s):''',
'''def _changed_card(en, m, c, asker, names=None):
    """S711: a dealer change of the last 7 days -- was / now (the dealer's name as written), who and when, Undo."""
    key = "chg-%d" % c["id"]
    sid = int(c["scan"])
    st = c.get("stamp") or "#%d" % sid
    undo = _act(en, key, _L(en, "s708_undo"), "/api/s454/s711/dealer/undo", {"id": int(c["id"])}) if asker else ""
    return ('<div class="s7c" data-card="%s" data-chg="%d"><div class="s7th"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="">'
            '<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px"><b>%s</b><div class="vp s7grn">%s</div><div class="s7s">%s</div>%s</div></div>'
            '<div class="acts">%s</div></div>'
            % (key, int(c["id"]), sid, _e(st), _e(_L(en, "s711_changed_l", c.get("saved") or "-", (names or {}).get(c.get("dealer")) or c.get("dealer") or "-")),
               _e(_ddmm(c.get("at")) + " · " + str(c.get("by") or "")), _bigbtn(en, m["ctx"], sid, st, queue=False), undo))


def _conflict_card(en, m, s):'''))
OTP.append(('''    if m["kept"]:
        scan.append('<div class="s7g" id="g_kept">%s · %d</div>' % (_L(en, "s708_g_kept"), len(m["kept"])))
        scan += [_kept_card(en, m, p, asker) for p in m["kept"]]''',
'''    if m["kept"]:
        scan.append('<div class="s7g" id="g_kept">%s · %d</div>' % (_L(en, "s708_g_kept"), len(m["kept"])))
        scan += [_kept_card(en, m, p, asker) for p in m["kept"]]
    if m.get("changed"):                                                                 # S711
        scan.append('<div class="s7g" id="g_chg">%s · %d</div>' % (_L(en, "s711_g_changed"), len(m["changed"])))
        dn = dict(all_dealers(con))
        scan += [_changed_card(en, m, c, asker, dn) for c in m["changed"]]'''))
# the full dealer list once on the page (only when a wrong-dealer card can use it)
OTP.append(('''    body = "<style>%s</style><script>%s</script>%s" % (CSS, JS, body)
    return P4.shell(con, u, P4.L(en, "track"), body, back=P, login=login)''',
'''    dl = ""
    if asker and m["wd"]:                                                                # S711: the 'Other dealer' list, drawn once
        dl = "<script>var S7DL=%s;</script>" % json.dumps([[k, n] for k, n in all_dealers(con)]).replace("<", "\\\\u003c").replace(">", "\\\\u003e").replace("&", "\\\\u0026")
    body = "<style>%s</style><script>%s</script>%s%s" % (CSS, JS, dl, body)
    return P4.shell(con, u, P4.L(en, "track"), body, back=P, login=login)'''))

# 2g -- the one dealer door: any dealer of the server's lists, read paper or not; the reply carries Undo; the undo door
OTP.append(('''    if OT.paper_dealer(con, ctx, sid):
        return _no("paper_read", en)
    ch = dict(dealer_choices(con, ctx, sid))
    if want not in ch:
        return _no("not_a_choice", en)
    res = P4._s708_put_dealer(con, u, sid, want, ctx, s, "s708_dealer_pick")
    if res.get("tie"):
        r = con.execute("SELECT created_at FROM purchase_order WHERE id=?", (res["tie"],)).fetchone()
        return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_dealer_to", ch[want], _ddmm(r[0]) if r else "#%s" % res["tie"])))
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_dealer_ok2", ch[want])))''',
'''    ch = dict(all_dealers(con))                               # S711: the read paper's dealer, the saved one, the week's and every dealer
    ch.update({k: v for k, v in dealer_choices(con, ctx, sid) if k not in ch})
    if want not in ch:
        return _no("not_a_choice", en)
    res = P4._s708_put_dealer(con, u, sid, want, ctx, s, "s708_dealer_pick")
    key = "wrong-%d" % sid
    undo = _act(en, key, _L(en, "s708_undo"), "/api/s454/s711/dealer/undo", {"id": int(res["change"])}) if res.get("change") else ""
    if res.get("tie"):
        r = con.execute("SELECT created_at FROM purchase_order WHERE id=?", (res["tie"],)).fetchone()
        return _ok('<div class="s7ok">%s %s</div>' % (_e(_L(en, "s708_dealer_to", ch[want], _ddmm(r[0]) if r else "#%s" % res["tie"])), undo))
    return _ok('<div class="s7ok">%s %s</div>' % (_e(_L(en, "s708_dealer_ok2", ch[want])), undo))


def api_dealer_undo(con, u, kind, login, b):
    """S711: undo one dealer change (porders_s454._s711_dealer_undo puts back the answer, the matcher's choice and the tie as they were)."""
    P4 = _w()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    cid = _int(b, "id")
    if not cid:
        return _no("bad_request", en, 400)
    ok, err = P4._s711_dealer_undo(con, u, cid)
    if not ok:
        return _no(err, en)
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s711_undone_part" if err else "s711_undone")))'''))
OTP.append(('''    "tied_already": ("Is order ya is scan ka jod pehle se hai — page dobara kholiye.", "The order or the scan is already tied — reload the page."),
}''',
'''    "tied_already": ("Is order ya is scan ka jod pehle se hai — page dobara kholiye.", "The order or the scan is already tied — reload the page."),
    "made_order": ("Is bill se ek naya order ban chuka hai — wapas nahi ho sakta. Doctor sahab ko bataiye.",
                   "An order was already made from this bill — it cannot be undone here. Tell Dr Manoj."),
    "moved_on": ("Iske baad is scan par aur kaam ho chuka hai — wapas nahi ho sakta. Doctor sahab ko bataiye.",
                 "This scan has moved on since (a newer change, another answer or another tie) — it cannot be undone here. Tell Dr Manoj."),
}'''))
OTP.append(('''KIT = "S708"                                                   # S710 (05-Nov): the PC viewer -- '#navpanes=0&view=FitH\'''',
'''KIT = "S708"                                                   # S710 (05-Nov): the PC viewer -- '#navpanes=0&view=FitH'
# S711 (06-Nov): the viewer's words and buttons beside the bill on a PC; the wrong-dealer card (saved dealer first, every dealer, rescan, Undo)'''))

# ============================================================================================ porders_s454.py
P4E = []
# 5 -- F-1123
P4E.append(('''    acon = OS._assets()
    if acon is None:
        out["asks"] = [dict(a, scan=int(a["asset_bill_id"])) for a in open_]
        return out''',
'''    acon = OS._assets()
    if acon is None:                                          # S711 (F-1123): the same shape as below, so every list can draw it
        for a in open_:
            login = str(a.get("asked_by") or "").lower()
            out["asks"].append(dict(id=a["id"], scan=int(a["asset_bill_id"]), stamp=a.get("stamp") or "", vendor="", date="", reason=a.get("reason") or "",
                                    asked_by=login, by_owner=login in owners, asked_at=a.get("asked_at") or "", month="", v=""))
        return out'''))
# 3 -- F-1121: the dealer core
P4E.append(('''def _s708_put_dealer(con, u, sid, pk, ctx, s, action="s628_dealer_fix"):
    """S628's dealer door, made callable (S708): the scan's dealer becomes pk (a supplier key the SERVER chose -- the paper's reading for
    Change dealer, the server's own list for S708's pick), s454_scan_answer + the S440 matcher's door, the tie moved to that dealer's newest
    untied order of the 7 days before the scan (else only removed), the links re-matched. -> dict(ok, dealer, tie, linked)."""
    w = who(u)
    kit = "S708" if action.startswith("s708") else "S628"
    _answer(con, sid, "vendor", "chosen", pk, w)              # commits; audited s454_scan_answer''',
'''S711_CHANGE = ("CREATE TABLE IF NOT EXISTS s711_dealer_change (id INTEGER PRIMARY KEY AUTOINCREMENT, scan INTEGER NOT NULL, stamp TEXT, saved TEXT, "
               "dealer TEXT NOT NULL, before TEXT, tie_to INTEGER, by TEXT, at TEXT, undone_at TEXT, undone_by TEXT)")


def _s711_state(con, sid):
    """What a dealer change touches, as it is now: the s454 vendor answer, the matcher's chosen_vendor, the scan's tie (+ its order's arrival)."""
    a = con.execute("SELECT answer, value, by, at FROM s454_scan_answer WHERE asset_bill_id=? AND kind='vendor'", (sid,)).fetchone()
    try:
        c = con.execute("SELECT chosen_vendor FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone()
    except sqlite3.Error:
        c = None
    t = con.execute("SELECT order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    o = con.execute("SELECT status, received_at, received_by FROM purchase_order WHERE id=?", (t[0],)).fetchone() if t else None
    return dict(answer=list(a) if a else None, chosen=(c[0] if c else None), state_row=c is not None,
                tie=list(t) if t else None, order=list(o) if o else None)


def _s711_untie(con, sid, stamp, w, why):
    """Remove the scan's tie; when that tie alone made its order 'arrived' (the S454 tie's own mark: received_by 'bill scan <stamp>'), the order
    waits again. -> the removed tie's order id or None."""
    t = con.execute("SELECT order_id, arrived FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if not t:
        return None
    con.execute("DELETE FROM order_scan_tie WHERE asset_bill_id=?", (sid,))
    if t[1]:
        con.execute("UPDATE purchase_order SET status='sent', received_at=NULL, received_by=NULL WHERE id=? AND status='received' AND received_by IN (?,?)",
                    (t[0], "bill scan %s" % (stamp or sid), "bill scan %s" % sid))
    OS.audit(con, w, "s711_untie", sid, dict(order=t[0], arrived=t[1], why=why, kit="S711"))
    return t[0]


def _s708_put_dealer(con, u, sid, pk, ctx, s, action="s628_dealer_fix"):
    """S628's dealer door, made callable (S708): the scan's dealer becomes pk (a supplier key the SERVER chose -- the paper's reading for
    Change dealer, the server's own list for S708's pick), s454_scan_answer + the S440 matcher's door, the links re-matched.
    S711 (F-1121): no tie is made here any more -- a tie to another dealer's order is removed (with the arrival that tie alone made) and the S454
    tie (order_sheet.tie_pass, its own rules, reading this answer first) ties the scan; the change is kept in s711_dealer_change with what it
    replaced, so _s711_dealer_undo can put it back. -> dict(ok, dealer, tie, linked, change)."""
    w = who(u)
    kit = "S708" if action.startswith("s708") else "S628"
    con.execute(S711_CHANGE)
    before = _s711_state(con, sid)
    _answer(con, sid, "vendor", "chosen", pk, w)              # commits; audited s454_scan_answer'''))
P4E.append(('''    pa = _pa()
    moved = None
    t = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t:
        o = con.execute("SELECT vendor FROM purchase_order WHERE id=?", (t[0],)).fetchone()
        if o and pa.supplier_key(o[0]) != pk:
            con.execute("DELETE FROM order_scan_tie WHERE asset_bill_id=?", (sid,))
            at = s.get("at")
            if at is not None:
                lo = (at - dt.timedelta(days=7)).replace(microsecond=0).isoformat()
                for r in con.execute("SELECT id, vendor FROM purchase_order WHERE status IN ('sent','received') AND created_at<=? AND created_at>=? "
                                     "AND id NOT IN (SELECT order_id FROM order_scan_tie) ORDER BY created_at DESC, id DESC",
                                     (at.replace(microsecond=0).isoformat(), lo)).fetchall():
                    if pa.supplier_key(r[1]) == pk:
                        con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,0)",
                                    (r[0], sid, s.get("stamp_no") or "", at.replace(microsecond=0).isoformat(), OS.now_iso(), "dealer_fix"))
                        moved = r[0]
                        break
            OS.audit(con, w, "s628_tie_moved", sid, dict(from_order=t[0], to_order=moved, kit=kit))
    OS.audit(con, w, action, sid, dict(stamp=s.get("stamp_no"), saved=s.get("vendor"), paper=pk, kit=kit))
    con.commit()
    try:
        _pa()._rematch(con, w)                                # the scan links follow at once (as S440's Supplier chuno does)
    except Exception:                                         # noqa: BLE001
        pass
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return dict(ok=True, dealer=pk, tie=moved, linked=bool(lk))''',
'''    pa = _pa()
    moved = None
    t = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t:
        o = con.execute("SELECT vendor FROM purchase_order WHERE id=?", (t[0],)).fetchone()
        if o and pa.supplier_key(o[0]) != pk:
            _s711_untie(con, sid, s.get("stamp_no") or "", w, "dealer changed to %s" % pk)
    OS.audit(con, w, action, sid, dict(stamp=s.get("stamp_no"), saved=s.get("vendor"), paper=pk, kit=kit))
    con.commit()
    try:                                                      # S711 (F-1121): the S454 tie, by its own rules, now -- not a tie of this door's
        OS.tie_pass(con, "%s dealer" % w)
    except Exception as ex:                                   # noqa: BLE001
        con.rollback()                                        # a half-done pass is not kept (the cron runs it again)
        print("S711 tie_pass after a dealer change failed: %r" % (ex,), file=sys.stderr)
    t2 = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t2 and (not t or t2[0] != t[0]):
        moved = t2[0]
    cur = con.execute("INSERT INTO s711_dealer_change (scan, stamp, saved, dealer, before, tie_to, by, at) VALUES (?,?,?,?,?,?,?,?)",
                      (sid, s.get("stamp_no") or "", s.get("vendor") or "", pk, json.dumps(before), t2[0] if t2 else None, w, OS.now_iso()))
    change = cur.lastrowid
    OS.audit(con, w, "s711_dealer_change", sid, dict(id=change, dealer=pk, tie_to=t2[0] if t2 else None, kit="S711"))
    con.commit()
    try:
        _pa()._rematch(con, w)                                # the scan links follow at once (as S440's Supplier chuno does)
    except Exception:                                         # noqa: BLE001
        pass
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return dict(ok=True, dealer=pk, tie=moved, linked=bool(lk), change=change)


def _s711_dealer_undo(con, u, cid):
    """S711: undo one dealer change, while nothing newer has happened to the scan (no later change; its tie is the one the change left):
    the s454 vendor answer and the matcher's choice back as they were, the tie made after it removed (and the arrival it alone made), the
    tie it removed put back (with its order's arrival) when that order is still free. -> (ok, error)."""
    w = who(u)
    try:
        r = con.execute("SELECT id, scan, stamp, dealer, before, tie_to, undone_at, at FROM s711_dealer_change WHERE id=?", (cid,)).fetchone()
    except sqlite3.Error:
        r = None
    if not r or r[6]:
        return False, "not_open"
    sid = int(r[1])
    if con.execute("SELECT 1 FROM s711_dealer_change WHERE scan=? AND id>? AND undone_at IS NULL", (sid, cid)).fetchone():
        return False, "moved_on"
    t = con.execute("SELECT order_id, tied_at, how FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t and t[0] != r[5] and (str(t[2] or "") != "scan" or str(t[1] or "") < str(r[7] or "")):
        return False, "moved_on"                              # a person's tie, or a tie older than the change: not ours to undo
    if t and str(t[2] or "") == "scan_made_order":
        return False, "made_order"                            # the S454 tie made an order from this bill: undo would leave it paperless
    a_now = con.execute("SELECT answer, value, at FROM s454_scan_answer WHERE asset_bill_id=? AND kind='vendor'", (sid,)).fetchone()
    if not a_now or a_now[0] != "chosen" or a_now[1] != r[3] or str(a_now[2] or "") > str(r[7] or ""):
        return False, "moved_on"                              # the dealer was answered another way since (S440's door): not ours to undo
    if not con.execute("UPDATE s711_dealer_change SET undone_at=?, undone_by=? WHERE id=? AND undone_at IS NULL", (OS.now_iso(), w, cid)).rowcount:
        return False, "not_open"                              # a second tap at the same moment
    t2 = con.execute("SELECT order_id, tied_at, how FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if (tuple(t2) if t2 else None) != (tuple(t) if t else None):
        con.rollback()
        return False, "moved_on"                              # the S454 tie ran between the read and the claim: read again
    try:
        b = json.loads(r[4] or "{}")
    except ValueError:
        b = {}
    if t:                                                     # the tie the change left, or the S454 tie made after it under the new dealer
        _s711_untie(con, sid, r[2] or "", w, "undo of dealer change %d" % cid)
    a = b.get("answer")
    if a:
        con.execute("UPDATE s454_scan_answer SET answer=?, value=?, by=?, at=? WHERE asset_bill_id=? AND kind='vendor'", (a[0], a[1], a[2], a[3], sid))
    else:
        con.execute("DELETE FROM s454_scan_answer WHERE asset_bill_id=? AND kind='vendor'", (sid,))
    try:
        con.execute("UPDATE purchase_scan_state SET chosen_vendor=? WHERE asset_bill_id=?", (b.get("chosen"), sid))
    except sqlite3.Error:
        pass
    old = b.get("tie")
    part = ""
    if old and not con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=? OR asset_bill_id=?", (old[0], sid)).fetchone():
        con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,?)", tuple(old))
        o = b.get("order")
        if o and o[0] == "received":
            con.execute("UPDATE purchase_order SET status='received', received_at=?, received_by=? WHERE id=? AND status='sent'", (o[1], o[2], old[0]))
    elif old:
        part = "old_tie_taken"                                # its old order has another scan now: this scan waits for its order again
    OS.audit(con, w, "s711_dealer_undo", sid, dict(id=cid, part=part, kit="S711"))
    con.commit()
    try:
        _pa()._rematch(con, w)
    except Exception:                                         # noqa: BLE001
        pass
    return True, part'''))
# the undo door's route
P4E.append(('''@bp.route(P + "/api/s454/s708/paper", methods=["POST"])
def api_s708_paper():''',
'''@bp.route(P + "/api/s454/s711/dealer/undo", methods=["POST"])
def api_s711_dealer_undo():
    return _s708_door("api_dealer_undo")                      # S711


@bp.route(P + "/api/s454/s708/paper", methods=["POST"])
def api_s708_paper():'''))

# ============================================================================================ order_sheet.py
OSE = []
OSE.append(('''    tied_scans = {r[0] for r in con.execute("SELECT asset_bill_id FROM order_scan_tie")}
    ans = answers(con)
    made = []''',
'''    tied_scans = {r[0] for r in con.execute("SELECT asset_bill_id FROM order_scan_tie")}
    try:                                                      # S711 (F-1120): a scan picked as the copy (S708's "This one is right") ties nothing
        copies = {int(r[0]) for r in con.execute("SELECT drop_id FROM s708_scan_pick WHERE undone_at IS NULL")}
    except sqlite3.Error:
        copies = set()
    ans = answers(con)
    made = []'''))
OSE.append(('''        if sid in tied_scans or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or not s.get("at"):
            continue
        if unread(s)''',
'''        if sid in tied_scans or sid in copies or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or not s.get("at"):
            continue
        if unread(s)'''))

EDITS = {"order_track_page.py": OTP, "porders_s454.py": P4E, "order_sheet.py": OSE}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    sd, od = sys.argv[1], sys.argv[2]
    os.makedirs(od, exist_ok=True)
    for name in ("order_track_page.py", "porders_s454.py", "order_sheet.py"):
        raw = open(os.path.join(sd, name), "rb").read()
        if md5(raw) != FROM[name]:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
        src = raw.decode("utf-8")
        for i, (a, b) in enumerate(EDITS[name], 1):
            n = src.count(a)
            if n != 1:
                sys.exit("REFUSED: %s edit %d matches %d times" % (name, i, n))
            src = src.replace(a, b)
        out = src.encode("utf-8")
        open(os.path.join(od, name), "wb").write(out)
        print("%s  %s -> %s" % (name, FROM[name][:8], md5(out)))


if __name__ == "__main__":
    main()
