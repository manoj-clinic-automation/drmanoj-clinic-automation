#!/usr/bin/env python3
"""make_s708.py -- S708_TRACK_REDESIGN: the counted edits to the two live files of this project.
    python3 -B make_s708.py <dir holding porders_s454.py and order_track.py> <out dir>
Each FROM file must carry its pinned md5; every edit must match exactly once; the TO md5s are printed."""
import hashlib
import os
import sys

FROM = {"porders_s454.py": "5de2a4b8d0a7eeab3872d044d81f99e4", "order_track.py": "9010a012117e707a2852cb2560855f5a"}

DEALER_BODY_OLD = '''    w = who(u)
    _answer(con, sid, "vendor", "chosen", pk, w)              # commits; audited s454_scan_answer
    try:                                                      # the S440 matcher's own door too (purchase_scan_state.chosen_vendor) -- no alias learnt:
        _po()._s440_put(con, sid, w, chosen_vendor=pk)        # the saved text names the WRONG dealer
        con.commit()
    except Exception:                                         # noqa: BLE001
        pass
    pa = _pa()
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
            OS.audit(con, w, "s628_tie_moved", sid, dict(from_order=t[0], to_order=moved, kit="S628"))
    OS.audit(con, w, "s628_dealer_fix", sid, dict(stamp=s.get("stamp_no"), saved=s.get("vendor"), paper=pk, kit="S628"))
    con.commit()
    try:
        _pa()._rematch(con, w)                                # the scan links follow at once (as S440's Supplier chuno does)
    except Exception:                                         # noqa: BLE001
        pass
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return jsonify(ok=True, dealer=pk, tie=moved, linked=bool(lk))'''

DEALER_CORE = '''def _s708_put_dealer(con, u, sid, pk, ctx, s, action="s628_dealer_fix"):
    """S628's dealer door, made callable (S708): the scan's dealer becomes pk (a supplier key the SERVER chose -- the paper's reading for
    Change dealer, the server's own list for S708's pick), s454_scan_answer + the S440 matcher's door, the tie moved to that dealer's newest
    untied order of the 7 days before the scan (else only removed), the links re-matched. -> dict(ok, dealer, tie, linked)."""
    w = who(u)
    kit = "S708" if action.startswith("s708") else "S628"
    _answer(con, sid, "vendor", "chosen", pk, w)              # commits; audited s454_scan_answer
    try:                                                      # the S440 matcher's own door too (purchase_scan_state.chosen_vendor) -- no alias learnt:
        _po()._s440_put(con, sid, w, chosen_vendor=pk)        # the saved text names the WRONG dealer
        con.commit()
    except Exception:                                         # noqa: BLE001
        pass
    pa = _pa()
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
    return dict(ok=True, dealer=pk, tie=moved, linked=bool(lk))


@bp.route(P + "/api/s454/dealer_fix", methods=["POST"])'''

E_P4 = [
# 1 the header names the kit
('''#    GET  /finance/porders/s454/track    the order list: the owner (English) and the logins in porders.rescan_askers (Roman Hindi); every other sender''',
 '''#    S708 (05-Nov-2026, D830): /s454/track and /s454/rescan are drawn by order_track_page.py (beside this file); ?old=1 = the pages below.
#    GET  /finance/porders/s454/track    the order list: the owner (English) and the logins in porders.rescan_askers (Roman Hindi); every other sender'''),
# 2 the track page: the new page first, the old one at ?old=1 or if the new one fails
('''        return pg, 403, hd
    OT = _s619_ot()
    now = OS.now()
    rows = OT.light_all(con, now)''',
 '''        return pg, 403, hd
    if request.args.get("old") != "1":                        # S708 (D830): the order list rebuilt; ?old=1 keeps this page
        try:
            import order_track_page as OTP                    # noqa: PLC0415
            return OTP.page(con, u, kind, login, en)
        except Exception as ex:                               # noqa: BLE001
            print("S708 track page failed, the S619 page drawn: %r" % (ex,), file=sys.stderr)
    OT = _s619_ot()
    now = OS.now()
    rows = OT.light_all(con, now)'''),
# 3 reception's list: the new list first
('''    login = _s618_login(u, login)
    sq = _sq()
    x = rescan_list(con)
    h = ['<div class="mut">%s</div>' % L(en, "rescan_top")]''',
 '''    login = _s618_login(u, login)
    if request.args.get("old") != "1":                        # S708 (D830): reception's scan work rebuilt; ?old=1 keeps this list
        try:
            import order_track_page as OTP                    # noqa: PLC0415
            return OTP.reception(con, u, kind, login, en)
        except Exception as ex:                               # noqa: BLE001
            print("S708 reception page failed, the S618 list drawn: %r" % (ex,), file=sys.stderr)
    sq = _sq()
    x = rescan_list(con)
    h = ['<div class="mut">%s</div>' % L(en, "rescan_top")]'''),
# 4 reception's home row counts the paper asks too
('''scan=len(scan_lines(con)), q=len(questions(con)), rescan=_s618_open_count(con),      # S618: Phir se scan karo''',
 '''scan=len(scan_lines(con)), q=len(questions(con)), rescan=_s618_open_count(con) + _s708_papers(con),      # S618 + S708''',),
('''def parked_with_work(con):''',
 '''def _s708_papers(con):
    """S708: the papers never scanned that the owner or Shavez sent to reception (still needed) -- on reception's row with the rescans."""
    try:
        import order_track_page as OTP                        # noqa: PLC0415
        return OTP.open_paper_count(con)
    except Exception:                                         # noqa: BLE001
        return 0


def parked_with_work(con):'''),
# 4b the count's docstring says what it now is (R2)
('''    """THE count of reception's row (and DUTY_MAP reception.rescan's due_sql): the asks neither done nor withdrawn."""''',
 '''    """The rescan asks neither done nor withdrawn -- DUTY_MAP reception.rescan's due_sql. S708: reception's home row adds the paper asks
    (order_track_page.open_paper_count); the duty map does not count those yet (named to the parent, F-1024)."""'''),
# 5 the dealer door made callable (S628's code, unchanged in what it does)
('''@bp.route(P + "/api/s454/dealer_fix", methods=["POST"])''', DEALER_CORE),
(DEALER_BODY_OLD, '''    return jsonify(**_s708_put_dealer(con, u, sid, pk, ctx, s))'''),
# 6 the S708 doors (their logic is in order_track_page.py)
('''@bp.route(P + "/s454/track")
def r_track():
    return track_page()
''',
 '''@bp.route(P + "/s454/track")
def r_track():
    return track_page()


# ---- S708 (05-Nov-2026, D830): the doors of the rebuilt order list and reception's scan work (order_track_page.py) -------------------------
def _s708_door(fn):
    u, con, kind, err = _auth_api()
    if err:
        return err
    import order_track_page as OTP                            # noqa: PLC0415
    b = _body()
    if not isinstance(b, dict):
        return jsonify(ok=False, error="bad_request"), 400
    d, code = getattr(OTP, fn)(con, u, kind, _s618_login(u), b)
    return jsonify(**d), code


@bp.route(P + "/api/s454/s708/pick", methods=["POST"])
def api_s708_pick():
    return _s708_door("api_pick")


@bp.route(P + "/api/s454/s708/pick/undo", methods=["POST"])
def api_s708_pick_undo():
    return _s708_door("api_pick_undo")


@bp.route(P + "/api/s454/s708/dealer", methods=["POST"])
def api_s708_dealer():
    return _s708_door("api_dealer")


@bp.route(P + "/api/s454/s708/paper", methods=["POST"])
def api_s708_paper():
    return _s708_door("api_paper")


@bp.route(P + "/api/s454/s708/paper/withdraw", methods=["POST"])
def api_s708_paper_withdraw():
    return _s708_door("api_paper_withdraw")


@bp.route(P + "/api/s454/s708/paper/scanned", methods=["POST"])
def api_s708_paper_scanned():
    return _s708_door("api_paper_scanned")


@bp.route(P + "/api/s454/s708/paper/tie", methods=["POST"])
def api_s708_paper_tie():
    return _s708_door("api_paper_tie")


@bp.route(P + "/api/s454/s708/paper/reask", methods=["POST"])
def api_s708_paper_reask():
    return _s708_door("api_paper_reask")


@bp.route(P + "/api/s454/s708/lost", methods=["POST"])
def api_s708_lost():
    return _s708_door("api_lost")


@bp.route(P + "/api/s454/s708/lost/clear", methods=["POST"])
def api_s708_lost_clear():
    return _s708_door("api_lost_clear")
'''),
]

E_OT = [
# 1 the picks are read once per page, with the rest of the scan half
('''        self.chosen = {}                                      # S628: a scan whose dealer the owner or Shavez corrected (s454_scan_answer vendor)''',
 '''        self.dropped, self.keep_of = set(), {}                # S708 (D830): "this one is right" -- the other scan of the paper is the copy
        try:
            for r in con.execute("SELECT keep_id, drop_id FROM s708_scan_pick WHERE undone_at IS NULL ORDER BY id"):
                self.keep_of[int(r[1])] = int(r[0])
                self.dropped.add(int(r[1]))
        except sqlite3.Error:
            pass
        self.chosen = {}                                      # S628: a scan whose dealer the owner or Shavez corrected (s454_scan_answer vendor)'''),
# 2 a family's clearer scan is never a dropped one
('''            ids = [i for i in ids if str((self.scans.get(i) or {}).get("lane") or "pharmacy") == "pharmacy" and not (self.scans.get(i) or {}).get("page_of")]''',
 '''            ids = [i for i in ids if str((self.scans.get(i) or {}).get("lane") or "pharmacy") == "pharmacy" and not (self.scans.get(i) or {}).get("page_of")]
            gone = [i for i in ids if i in getattr(self, "dropped", ())]
            if gone:                                          # S708 (R3): a family whose scan was picked as a copy heads to the kept scan
                out[root] = self.keep_of[gone[0]]
                continue'''),
# 3 the head of a dropped scan is the kept one's
('''    def head(self, sid):
        """A set-aside scan's head (dup_of), else the scan itself. S628 (F-992): the CLEARER scan of the family (most item lines read)."""
        r = self._root(sid)''',
 '''    def head(self, sid):
        """A set-aside scan's head (dup_of), else the scan itself. S628 (F-992): the CLEARER scan of the family (most item lines read).
        S708: a scan picked as the copy of another (s708_scan_pick) heads to the kept one."""
        s, seen = int(sid), set()
        while s in getattr(self, "keep_of", {}) and s not in seen:
            seen.add(s)
            s = self.keep_of[s]
        sid = s
        r = self._root(sid)'''),
# 4 a dropped scan is never usable; ignore_bad (S708): a scan sent back for a rescan still counts as one copy of its paper
('''    def usable(self, sid):
        s = self.scans.get(int(sid)) or {}
        if self.fam_n.get(self._root(sid), 1) > 1:               # S628 (F-992): in a duplicate family only the clearer scan reads, set aside or not
            return bool(s) and int(sid) == self.head(sid) and int(sid) not in self.bad and not s.get("page_of") \\
                and str(s.get("lane") or "pharmacy") == "pharmacy"
        return bool(s) and str(s.get("lane") or "pharmacy") == "pharmacy" and str(s.get("status") or "") != "rejected" and not s.get("dup_of") \\
            and not s.get("page_of") and int(sid) not in self.bad''',
 '''    def usable(self, sid, ignore_bad=False):
        s = self.scans.get(int(sid)) or {}
        bad = set() if ignore_bad else self.bad                 # S708: ignore_bad -- a scan with an open rescan ask is still one copy of its paper
        if int(sid) in getattr(self, "dropped", ()):             # S708: picked as the copy of another scan
            return False
        if self.fam_n.get(self._root(sid), 1) > 1:               # S628 (F-992): in a duplicate family only the clearer scan reads, set aside or not
            return bool(s) and int(sid) == self.head(sid) and int(sid) not in bad and not s.get("page_of") \\
                and str(s.get("lane") or "pharmacy") == "pharmacy"
        return bool(s) and str(s.get("lane") or "pharmacy") == "pharmacy" and str(s.get("status") or "") != "rejected" and not s.get("dup_of") \\
            and not s.get("page_of") and int(sid) not in bad'''),
# 5 same_paper(asked_too=True): a pair one of whose scans was sent back for a rescan is still a pair (S708's page and its pick door)
('''def same_paper(con, ctx):
    """S628 (F-992): two usable pharmacy scans since order.track_since whose Claude readings agree on the bill number (leading zeros apart) and
    the total, under one dealer, neither set aside -> [dict(a, b, stamps, bill)]. A note for the owner; nothing is set aside here."""
    seen = {}
    out = []
    for sid, s in sorted(ctx.scans.items()):
        if str(s.get("created_at") or "")[:10] < since(con) or not ctx.usable(sid) or _aside(s):''',
 '''def same_paper(con, ctx, asked_too=False):
    """S628 (F-992): two usable pharmacy scans since order.track_since whose Claude readings agree on the bill number (leading zeros apart) and
    the total, under one dealer, neither set aside -> [dict(a, b, stamps, bill)]. A note for the owner; nothing is set aside here.
    S708: asked_too -- a scan with an OPEN rescan ask still counts (the pair stays until "this one is right" is picked)."""
    seen = {}
    out = []
    asked = {int(a["scan"]) for a in ((getattr(ctx, "redo", None) or {}).get("asks") or [])} if asked_too else set()
    for sid, s in sorted(ctx.scans.items()):
        if str(s.get("created_at") or "")[:10] < since(con) or _aside(s) or not (ctx.usable(sid) or (int(sid) in asked and ctx.usable(sid, ignore_bad=True))):'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(src, edits, name):
    for i, (a, b) in enumerate(edits, 1):
        n = src.count(a)
        if n != 1:
            sys.exit("REFUSED: %s edit %d matches %d times" % (name, i, n))
        src = src.replace(a, b)
    return src


def main():
    sd, od = sys.argv[1], sys.argv[2]
    os.makedirs(od, exist_ok=True)
    for name, edits in (("porders_s454.py", E_P4), ("order_track.py", E_OT)):
        raw = open(os.path.join(sd, name), "rb").read()
        if md5(raw) != FROM[name]:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
        out = apply(raw.decode("utf-8"), edits, name).encode("utf-8")
        open(os.path.join(od, name), "wb").write(out)
        print("%s  %s -> %s" % (name, FROM[name][:8], md5(out)))


if __name__ == "__main__":
    main()
