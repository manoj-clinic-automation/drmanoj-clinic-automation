# S628 anchored edits for /root/finance/order_track.py (FROM a8c46700)
EDITS = []

EDITS.append(('''VERSION = "1.0"
KIT = "S619_ORDER_TRACKER"''', '''VERSION = "1.1"
KIT = "S628_ONE_NAME_LIST"                                    # v1.1 S628 (D761): came from another dealer, tablets, carries follow, the one name list'''))

EDITS.append(('''    "set_aside": ("tied scan %s was set aside; its first scan is %s", "joda gaya scan %s hata diya gaya; asli scan %s hai"),
}''', '''    "set_aside": ("tied scan %s was set aside; its first scan is %s", "joda gaya scan %s hata diya gaya; asli scan %s hai"),
    "clearer": ("tied scan %s is a copy; the clearer scan of this paper is %s", "joda gaya scan %s ek copy hai; saaf scan %s hai"),   # S628
    "other_came": ("came from %s (bill %s)", "%s se aaya (bill %s)"),                                                           # S628
    "units": ("%d tablets came on the bill (another pack size)", "bill par %d goli aayi (doosra pack size)"),                   # S628
    "same_paper": ("%s and %s are the same paper (bill %s) scanned twice", "%s aur %s ek hi kaagaz (bill %s) ke do scan hain"),  # S628
}'''))

# the light half: a line that came on another dealer's bill, the tablets note; arrival / in-Marg follow
EDITS.append(('''    billed = [l for l in lines if l.get("billed_qty") is not None and str(l.get("billed_bill_no") or "").strip()]
    in_marg = bool(billed)
''', '''    billed = [l for l in lines if l.get("billed_qty") is not None and str(l.get("billed_bill_no") or "").strip()]
    other = [l for l in lines if l not in billed and str(l.get("other_bill_no") or "").strip()]      # S628 (F-991): came on another dealer's bill
    own_marg = bool(billed)                                   # S628: only the order's OWN dealer's bill makes an unbilled line short
    in_marg = bool(billed) or bool(other)
'''))

EDITS.append(('''        if l in billed:
            q = int(l["billed_qty"])
            x.update(came=q, how="marg")''', '''        if l in billed:
            q = int(l["billed_qty"])
            x.update(came=q, how="marg")
            if l.get("billed_units") is not None:              # S628: the bill's packing differs from the order's -- the tablets that came
                x["notes"].append(("units", (int(l["billed_units"]),)))'''))

EDITS.append(('''        elif in_marg:
            x.update(state="short", short=packs, how="marg", reason=("tapped_missing" if tapped(l) and int(l.get("missing") or 0) else "marg_short"))''',
              '''        elif l in other:                                      # S628 (F-991, D761): came, from another dealer -- never short, never carried
            q = int(l.get("other_qty") or 0)
            x.update(state="came", came=q, how="other", other=str(l.get("other_supplier") or ""))
            x["notes"].append(("other_came", (short_name(l.get("other_supplier")), str(l.get("other_bill_no") or ""))))
        elif own_marg:
            x.update(state="short", short=packs, how="marg", reason=("tapped_missing" if tapped(l) and int(l.get("missing") or 0) else "marg_short"))'''))

# the carry: an open carry follows its line's short (LINVIZ 600 10 -> 7); the Marg partners count as the item for 'already on Marg's order'
EDITS.append(('''def _marg_items(con):
    """{supplier_norm: {norm(item)}} of Marg's newest open order (the lines its newest export prints)."""
    pa = _pa()
    out = {}
    try:
        for l in _os().marg_lines(con):
            out.setdefault(l["supplier_norm"], set()).add(pa.norm(l["item"]))
    except Exception:                                         # noqa: BLE001
        pass
    return out''', '''def _marg_items(con):
    """{supplier_norm: {norm(item)}} of Marg's newest open order (the lines its newest export prints). S628: each line's Marg partners too."""
    pa = _pa()
    out = {}
    try:
        for l in _os().marg_lines(con):
            for f in _names(con, l["item"]):
                out.setdefault(l["supplier_norm"], set()).add(pa.norm(f))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def _names(con, item, sn=None):
    """S628: the item and its names in the one name list (med_names.forms) -- the item alone when the list is absent."""
    try:
        import med_names                                      # noqa: PLC0415
        return med_names.forms(con, item, sn)
    except Exception:                                         # noqa: BLE001
        return [item]'''))

EDITS.append(('''        if exclude and r[0] == exclude:
            continue
        if pa.norm(r[2]) == pa.norm(item):
            return r[0], r[1]
    return None''', '''        if exclude and r[0] == exclude:
            continue
        if pa.norm(r[2]) in {pa.norm(f) for f in _names(con, item)}:   # S628: a Marg partner of the item is the item
            return r[0], r[1]
    return None'''))

EDITS.append(('''    for c in [dict(r) for r in con.execute("SELECT * FROM order_carry WHERE done_at IS NULL AND dropped_at IS NULL")]:
        hit = _ordered_since(con, c["supplier_norm"], c["item"], c["at"], exclude=c["from_order_id"])''', '''    for c in [dict(r) for r in con.execute("SELECT * FROM order_carry WHERE done_at IS NULL AND dropped_at IS NULL")]:
        sx = short_now.get(c["from_line_id"])                 # S628 (D761): an open carry follows its line's short (LINVIZ 600: 10 -> 7)
        if sx is not None and int(sx[1]["short"]) > 0 and int(sx[1]["short"]) != int(c["qty"]):
            con.execute("UPDATE order_carry SET qty=? WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (int(sx[1]["short"]), c["id"]))
            _os().audit(con, who, "s628_carry_qty", c["from_order_id"], dict(item=c["item"], line=c["from_line_id"], was=int(c["qty"]), qty=int(sx[1]["short"]), kit="S628"))
            resized += 1
        hit = _ordered_since(con, c["supplier_norm"], c["item"], c["at"], exclude=c["from_order_id"])'''))

EDITS.append(('''            if pa.norm(x["item"]) in marg.get(s["sn"], set()):
                continue                                      # still on Marg's open order: not carried twice''', '''            if pa.norm(x["item"]) in marg.get(s["sn"], set()):
                continue                                      # still on Marg's open order: not carried twice (S628: a partner name counts)'''))

# the scan half: the loosened name test, the one name list, the clearer scan of a family, a corrected dealer, the same paper twice
EDITS.append(('''def name_score(form, read):
    """1.0 an exact name (punctuation and spacing apart); else the strict fuzzy rule: the numbers in the names agree (never a sibling size) and
    the letters are at least 0.8 alike (difflib); else 0. Quantities are never compared."""
    a, b = _nm(form), _nm(read)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0''', '''def name_score(form, read):
    """1.0 an exact name (punctuation and spacing apart); else the strict fuzzy rule: the numbers in the names agree (never a sibling size) and
    the letters are at least 0.8 alike (difflib); else 0. Quantities are never compared.
    S628 (F-996): pack and form words (TAB, CAP, 10*10, 1X10, 6T) are dropped first and a name whose words all sit inside the other's (two
    words at least) is the same -- med_names.loose; the higher of the two rules wins."""
    a, b = _nm(form), _nm(read)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    try:
        import med_names                                      # noqa: PLC0415
        lo = med_names.loose(read, form)
    except Exception:                                         # noqa: BLE001
        lo = 0.0
    return max(lo, _name_score_s619(form, read))


def _name_score_s619(form, read):
    """S619's rule, unchanged (S628 keeps it beside med_names.loose)."""
    a, b = _nm(form), _nm(read)'''))

EDITS.append(('''    try:
        out += [r[0] for r in con.execute("SELECT scan_name FROM s454_item_name WHERE supplier_norm=? AND marg_item=?", (sn, item)) if r[0]]
    except sqlite3.Error:
        pass
    seen, res = set(), []''', '''    out += [f for f in _names(con, item, sn) if f not in out]   # S628 (D761): the one name list (its sure scan spellings), not s454_item_name
    seen, res = set(), []'''))

EDITS.append(('''        try:
            import stock_figure as SF                         # noqa: PLC0415
            self.sf = SF._ctx(con, None, None)
        except Exception:                                     # noqa: BLE001
            self.sf = None

    def head(self, sid):
        """A set-aside scan's head (dup_of), else the scan itself."""
        s = self.scans.get(int(sid)) or {}
        return int(s["dup_of"]) if s.get("dup_of") else int(sid)''', '''        try:
            import stock_figure as SF                         # noqa: PLC0415
            self.sf = SF._ctx(con, None, None)
        except Exception:                                     # noqa: BLE001
            self.sf = None
        self.chosen = {}                                      # S628: a scan whose dealer the owner or Shavez corrected (s454_scan_answer vendor)
        try:
            for r in con.execute("SELECT asset_bill_id, value FROM s454_scan_answer WHERE kind='vendor' AND answer='chosen'"):
                if r[1] and r[1] != "-":
                    self.chosen[int(r[0])] = r[1]
        except sqlite3.Error:
            pass
        self.best = self._families()

    def _root(self, sid):
        seen = set()
        s = int(sid)
        while s not in seen:
            seen.add(s)
            d = (self.scans.get(s) or {}).get("dup_of")
            if not d:
                return s
            s = int(d)
        return s

    def _families(self):
        """S628 (F-992): {root: the clearer scan} for every duplicate family -- the most item lines read, then the earliest."""
        fam = {}
        for sid in self.scans:
            fam.setdefault(self._root(sid), []).append(int(sid))
        out = {}
        self.fam_n = {root: len(ids) for root, ids in fam.items()}
        for root, ids in fam.items():
            ids = [i for i in ids if str((self.scans.get(i) or {}).get("lane") or "pharmacy") == "pharmacy" and not (self.scans.get(i) or {}).get("page_of")]
            if not ids:
                continue
            out[root] = max(ids, key=lambda i: (len(self.names(i)), -i))
        return out

    def head(self, sid):
        """A set-aside scan's head (dup_of), else the scan itself. S628 (F-992): the CLEARER scan of the family (most item lines read)."""
        r = self._root(sid)
        return int(self.best.get(r, r))'''))

EDITS.append(('''    def usable(self, sid):
        s = self.scans.get(int(sid)) or {}
        return bool(s) and str(s.get("lane") or "pharmacy") == "pharmacy" and str(s.get("status") or "") != "rejected" and not s.get("dup_of") \\
            and not s.get("page_of") and int(sid) not in self.bad''', '''    def usable(self, sid):
        s = self.scans.get(int(sid)) or {}
        if self.fam_n.get(self._root(sid), 1) > 1:               # S628 (F-992): in a duplicate family only the clearer scan reads, set aside or not
            return bool(s) and int(sid) == self.head(sid) and int(sid) not in self.bad and not s.get("page_of") \\
                and str(s.get("lane") or "pharmacy") == "pharmacy"
        return bool(s) and str(s.get("lane") or "pharmacy") == "pharmacy" and str(s.get("status") or "") != "rejected" and not s.get("dup_of") \\
            and not s.get("page_of") and int(sid) not in self.bad'''))

EDITS.append(('''        ov = ctx.other_dealer(sid, s.get("vendor") or "")
        if ov:
            out.append(dict(scan=sid, stamp=s.get("stamp_no") or "#%d" % sid, saved=s.get("vendor") or "", paper=ov,
                            date=str(s.get("bill_date") or "")[:10] or (s["at"].date().isoformat() if s.get("at") else "")))
    return out''', '''        if int(sid) in getattr(ctx, "chosen", {}):
            continue                                          # S628: its dealer was corrected (s454_scan_answer) -- no longer listed
        ov = ctx.other_dealer(sid, s.get("vendor") or "")
        if ov:
            out.append(dict(scan=sid, stamp=s.get("stamp_no") or "#%d" % sid, saved=s.get("vendor") or "", paper=ov,
                            date=str(s.get("bill_date") or "")[:10] or (s["at"].date().isoformat() if s.get("at") else "")))
    return out


def paper_dealer(con, ctx, sid):
    """S628: the supplier key of the dealer a scan's paper names (its Claude reading through scan_register's supplier test against the known
    suppliers), or '' -- the server's own answer for the 'Change dealer' door (never the browser's)."""
    rv = ctx.reading_vendor(sid)
    if not rv or ctx.sr is None or ctx.sr_cx is None:
        return ""
    pa = _pa()
    best = ""
    try:
        sups = sorted({pa.supplier_key(r[0]) for r in con.execute("SELECT DISTINCT supplier FROM purchase_bill") if r[0]})
    except sqlite3.Error:
        sups = []
    for k in sups:
        try:
            if ctx.sr.supplier(ctx.sr_cx, rv, k) == "agree":
                if best:
                    return ""                                 # two dealers answer: no one-tap door
                best = k
        except Exception:                                     # noqa: BLE001
            continue
    return best


def same_paper(con, ctx):
    """S628 (F-992): two usable pharmacy scans since order.track_since whose Claude readings agree on the bill number (leading zeros apart) and
    the total, under one dealer, neither set aside -> [dict(a, b, stamps, bill)]. A note for the owner; nothing is set aside here."""
    seen = {}
    out = []
    for sid, s in sorted(ctx.scans.items()):
        if str(s.get("created_at") or "")[:10] < since(con) or not ctx.usable(sid):
            continue
        rd = ctx.read.get(int(sid)) or {}
        bno = re.sub(r"[^A-Z0-9]", "", str(rd.get("bill_no") or "").upper())
        bno = re.sub(r"^([A-Z]*)0+(?=\\d)", r"\\1", bno)
        tot = rd.get("total_amount")
        if not bno or tot in (None, ""):
            continue
        try:
            key = (pa_key(s), bno, round(float(tot), 2))
        except (TypeError, ValueError):
            continue
        if key in seen:
            a = seen[key]
            out.append(dict(a=a, b=sid, sa=ctx.scans[a].get("stamp_no") or "#%d" % a, sb=s.get("stamp_no") or "#%d" % sid, bill=str(rd.get("bill_no") or "")))
        else:
            seen[key] = sid
    return out


def pa_key(s):
    return _pa().supplier_key(s.get("vendor") or "")'''))

EDITS.append(("""    have = {r[0]: r for r in con.execute("SELECT from_line_id, id FROM order_carry")}
    short_now = {}
    written = done = dropped = 0""", """    have = {r[0]: r for r in con.execute("SELECT from_line_id, id FROM order_carry")}
    short_now = {}
    written = done = dropped = resized = 0"""))

EDITS.append(("""    if written or done or dropped:
        con.commit()
    return dict(written=written, done=done, dropped=dropped)""", """    if written or done or dropped or resized:
        con.commit()
    return dict(written=written, done=done, dropped=dropped, resized=resized)"""))

EDITS.append(("""            h = ctx.head(x["scan"])
            x["head"] = h
            if h != int(x["scan"]):
                hs = ctx.scans.get(h) or {}
                s["notes"].append(W("set_aside", en, x["stamp"], hs.get("stamp_no") or "#%d" % h))""", """            h = ctx.head(x["scan"])
            x["head"] = h
            x["head_stamp"] = (ctx.scans.get(h) or {}).get("stamp_no") or "#%d" % h      # S628: the clearer scan's own number
            if h != int(x["scan"]):
                hs = ctx.scans.get(h) or {}
                me = ctx.scans.get(int(x["scan"])) or {}       # S628: set aside by the scan app, or a copy of a clearer scan
                s["notes"].append(W("set_aside" if (me.get("dup_of") and h == ctx._root(x["scan"])) else "clearer", en, x["stamp"],
                                    hs.get("stamp_no") or "#%d" % h))"""))

EDITS.append(("""        self.ok = False
        self.scans, self.read, self.bad, self.sr_cx = {}, {}, set(), None
        self.sf = None""", """        self.ok = False
        self.scans, self.read, self.bad, self.sr_cx = {}, {}, set(), None
        self.sf = None
        self.best, self.fam_n, self.chosen, self.sr = {}, {}, {}, None      # S628: set before any early return"""))
