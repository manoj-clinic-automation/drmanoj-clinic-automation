

# ---- S973 (27-Nov-2026, the Sanjeevni chat's session 540, kit S973_VOUCHER_SCANS; D1091 plan 2.4; PLANNED on board/_numbers v2415) -------
#  A printed Marg STOCK VOUCHER (the pharmacy's own Stock Issue L000045 / Stock Receive AD00045) scanned on the pharmacy lane is marked kind
#  'Stock voucher', doc_kind 'stock_voucher' -- never kind 'Pharmacy', so no Sanjeevni reader of the scan app (kind='Pharmacy' only) takes
#  it for a dealer's bill: Amir's enter list, the scanned-not-in-Marg ask and the bill pairing never see it. Sanjeevni's voucher_scan.py
#  reads it (READ ONLY) to settle Amir's voucher claims and to name the items Marg's report cuts.
#  Two roads, one kind:
#   * THE LINK: Amir's card and reception's line open the intake with lane=pharmacy and the voucher's number (bill_no L000045, no vendor);
#     such a paper is marked at once (compare-and-set, audited 'server (S973 link)') and read by read_pharmacy(); a reading that says it is
#     NOT a stock voucher puts it back to 'Pharmacy' and reads it on the lane's own road.
#   * THE READING: any pharmacy-lane paper read_pharmacy() recognises as a stock voucher is marked BEFORE _bg_extract fills the row (S841's
#     pattern); healed after every POST, every reading and at start. The row is lent only the voucher's number (Marg's form) and date:
#     never a seller, never an amount.
#  A PERSON's answer stands: a person's re-lane AFTER this kit marked it (off the lane and back) is never marked again. The papers page's
#  history rule never moves a stock voucher. The edit page keeps the kind. Switch: settings 'read.stock_voucher' = 'off' (absent = on) --
#  nothing is marked (a voucher scanned then stays 'Pharmacy' as before this kit; the reading still says so).
KIT_S973 = "S973_VOUCHER_SCANS"
S973_KIND = "Stock voucher"
_s550_claude_before_s973 = _s550_claude
_bg_extract_before_s973 = _bg_extract
_create_intake_bill_before_s973 = _create_intake_bill
_S973_DOC_SQL = ("SELECT id FROM bills WHERE doc_kind='stock_voucher' AND lane='pharmacy' AND kind='Pharmacy' "
                 "AND COALESCE(status,'')<>'rejected'")
_S973_READ_SQL = ("SELECT b.id FROM bills b JOIN claude_reading c ON c.bill_id=b.id WHERE c.ok=1 AND c.doc_kind='stock_voucher' "
                  "AND b.lane='pharmacy' AND b.kind='Pharmacy' AND COALESCE(b.doc_kind,'')='' AND COALESCE(b.status,'')<>'rejected'")


def _s973_vno(s):
    """A printed voucher number -> Marg's form (L000045 / AD00045); '' when it is not one."""
    import re as _s973_re
    t = _s973_re.sub(r"[\s\-/.]", "", str(s or "").upper())
    m = _s973_re.fullmatch(r"(L|AD)0*(\d{1,6})", t)
    if not m:
        return ""
    return ("L%06d" if m.group(1) == "L" else "AD%05d") % int(m.group(2))


def _s973_on():
    try:
        _d = sqlite3.connect(DB_PATH)
        try:
            _r = _d.execute("SELECT value FROM settings WHERE key='read.stock_voucher'").fetchone()
        finally:
            _d.close()
    except sqlite3.Error:
        return True
    return not (_r and (_r[0] or "").strip().lower() == "off")


def _s973_row(bid):
    try:
        _d = sqlite3.connect(DB_PATH, timeout=30)
        try:
            return _d.execute("SELECT kind, lane, doc_kind, status, vendor, bill_no FROM bills WHERE id=?", (bid,)).fetchone()
        finally:
            _d.close()
    except sqlite3.Error:
        return None


def _s973_person_said(_d, bid):
    """True when this kit marked the paper and a person re-laned it after that: the person's word stands."""
    r = _d.execute("SELECT MAX(rowid) FROM bill_audit WHERE bill_id=? AND action='kind' AND who LIKE 'server (S973%'", (bid,)).fetchone()
    if not r or r[0] is None:
        return False
    return _d.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='relane' AND rowid>?", (bid, r[0])).fetchone() is not None


def _s973_mark(ids, who, via, tries=1, wait=30):
    """Each paper -> kind 'Stock voucher', doc_kind 'stock_voucher' (compare-and-set from 'Pharmacy' on the pharmacy lane), audited 'kind'.
    -> how many (None when the database stayed busy). Its own short connection; never raises."""
    import time as _s973_time
    for _try in range(max(1, tries)):
        try:
            _d = sqlite3.connect(DB_PATH, timeout=wait)
            try:
                n = 0
                for i in ids:
                    if _s973_person_said(_d, i):
                        continue
                    cur = _d.execute("UPDATE bills SET kind=?, doc_kind='stock_voucher' WHERE id=? AND lane='pharmacy' AND kind='Pharmacy' "
                                     "AND COALESCE(status,'')<>'rejected' AND COALESCE(doc_kind,'') IN ('','stock_voucher')", (S973_KIND, i))
                    if cur.rowcount == 1:
                        _s754_audit(_d, i, "kind", {"from": "Pharmacy", "to": S973_KIND, "lane": "pharmacy", "via": via}, who=who)
                        n += 1
                if n:
                    _d.commit()
                return n
            finally:
                _d.close()
        except sqlite3.OperationalError:
            if _try + 1 < max(1, tries):
                _s973_time.sleep(2 * (_try + 1))
        except Exception:                                            # noqa: BLE001
            return 0
    return None


def _s973_heal(only=None, who="server (S973 heal)", tries=1):
    """Every stock voucher on the pharmacy lane still marked 'Pharmacy' (doc_kind, or a reading that says so) -> 'Stock voucher'."""
    if not _s973_on():
        return 0
    try:
        _d = sqlite3.connect(DB_PATH, timeout=30)
        try:
            q, arg = (" AND id=?", (only,)) if only is not None else ("", ())
            ids = [r[0] for r in _d.execute(_S973_DOC_SQL + q, arg)]
            try:
                rds = []
                for _i, _dat in _d.execute(_S973_READ_SQL.replace("SELECT b.id FROM", "SELECT b.id, c.data FROM") + (" AND b.id=?" if only is not None else ""), arg):
                    try:
                        _no = json.loads(_dat or "{}").get("bill_no")
                    except ValueError:
                        _no = None
                    if _s973_vno(_no):                               # review: only a paper that carries a Marg voucher number
                        rds.append(_i)
            except sqlite3.OperationalError as _e:
                if "no such table" not in str(_e):
                    raise
                rds = []
        finally:
            _d.close()
    except sqlite3.Error:
        return None
    return _s973_mark(ids + [x for x in rds if x not in ids], who, "S973: a stock voucher on the pharmacy lane", tries)


def _s973_unmark(bid):
    """A paper the LINK marked whose reading says it is not a stock voucher -> back to 'Pharmacy' (compare-and-set, audited). -> True/False."""
    try:
        _d = sqlite3.connect(DB_PATH, timeout=30)
        try:
            if not _d.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='kind' AND who='server (S973 link)'", (bid,)).fetchone():
                return False
            cur = _d.execute("UPDATE bills SET kind='Pharmacy', doc_kind=NULL, bill_no=NULL WHERE id=? AND lane='pharmacy' AND kind=? "
                             "AND doc_kind='stock_voucher'", (bid, S973_KIND))   # the link's voucher number is not this paper's number
            if cur.rowcount == 1:
                _s754_audit(_d, bid, "kind", {"from": S973_KIND, "to": "Pharmacy", "lane": "pharmacy",
                                              "via": "S973: the reading says it is not a stock voucher"}, who="server (S973 not a voucher)")
                _d.commit()
                return True
            return False
        finally:
            _d.close()
    except sqlite3.Error:
        return False


def _s973_hdr(hdr):
    """The row is lent the voucher's number (Marg's form) and date only: never a seller, never an amount."""
    h = dict(hdr or {})
    h["bill_no"] = _s973_vno(h.get("bill_no")) or h.get("bill_no")
    for k in ("vendor", "vendor_phone", "vendor_email", "total_amount"):
        h[k] = None
    return h


def _create_intake_bill(fobj, note, lane=None, prefill=None, challan=False, kind_over=None, summary=False):   # noqa: F811 -- S973: the link
    bid = _create_intake_bill_before_s973(fobj, note, lane, prefill, challan, kind_over, summary)
    try:
        pf = prefill or {}
        if bid and not challan and not summary and not kind_over and not str(pf.get("vendor") or "").strip() and _s973_vno(pf.get("bill_no")) \
                and _s973_on() and _s973_link_first(bid, pf.get("bill_no")) is True:
            _s973_mark([bid], "server (S973 link)", "S973: the voucher's scan link (lane pharmacy, its number, no seller)", tries=1, wait=5)
    except Exception:                                                # noqa: BLE001
        pass
    return bid


def _s973_is_link(r):
    """A pharmacy paper still 'Pharmacy' with a Marg voucher number and no seller: the voucher's scan link made it."""
    return (r is not None and r[0] == "Pharmacy" and (r[1] or "") == "pharmacy" and not (r[2] or "") and str(r[3] or "") != "rejected"
            and not str(r[4] or "").strip() and bool(_s973_vno(r[5])))


def _s973_link_first(bid, no):
    """The link's number rides the scanner's fields to EVERY later Save on that page (second look M1): only the FIRST paper carrying it is
    the voucher's. Any later one -> its borrowed number cleared (compare-and-set, audited) and False: its reading decides what it is."""
    try:
        _d = sqlite3.connect(DB_PATH, timeout=10)
        try:
            if not _d.execute("SELECT 1 FROM bills WHERE id<>? AND id<? AND lane='pharmacy' AND bill_no=? AND COALESCE(status,'')<>'rejected'",
                              (bid, bid, no)).fetchone():
                return True
            if _d.execute("UPDATE bills SET bill_no=NULL WHERE id=? AND bill_no=? AND COALESCE(vendor,'')='' AND kind='Pharmacy'", (bid, no)).rowcount == 1:
                _s754_audit(_d, bid, "bill_no", {"cleared": no, "via": "S973: the voucher link's number rode a later Save -- not this paper's"},
                            who="server (S973 link once)")
                _d.commit()
            return False
        finally:
            _d.close()
    except sqlite3.Error:
        return None                                                  # re-look S2: not known -- the caller marks nothing


def _s550_claude(bid, path):                                         # noqa: F811 -- S973: a stock voucher recognised by its content
    r = _s973_row(bid)
    lf = _s973_link_first(bid, r[5]) if (_s973_is_link(r) and _s973_on()) else True
    if lf is False:
        r = _s973_row(bid)                                           # a later paper of that page: read on the lane's own road
    if lf is True and _s973_is_link(r) and _s973_on():                              # review M3: the reading thread can start before the link's mark --
        _s973_mark([bid], "server (S973 link)", "S973: the voucher's scan link (lane pharmacy, its number, no seller)", tries=3)
        r = _s973_row(bid)                                           # it marks the paper itself, so it is read as a voucher either way
    if r is not None and r[0] == S973_KIND and (r[1] or "") == "pharmacy" and CLAUDE is not None and hasattr(CLAUDE, "read_pharmacy"):
        try:                                                         # a paper the link (or an earlier reading) marked: the pharmacy reader
            if not CLAUDE.available(DB_PATH) or not _s601_asked(bid):
                return None
            data = CLAUDE.read_pharmacy(path, bid=bid, db_path=DB_PATH)
            if not data:
                return None
            if data.get("doc_kind") != "stock_voucher":
                if _s973_unmark(bid):
                    return _s550_claude_before_s973(bid, path)       # not a voucher after all: the lane's own road reads it
                return None
            hdr, items = CLAUDE.to_bill(data)
            return _s973_hdr(hdr), items
        except Exception:                                            # noqa: BLE001
            return None
    res = _s550_claude_before_s973(bid, path)
    if res:
        try:
            _s973_heal(only=bid, who="server (S973 read)", tries=3)  # marked before _bg_extract fills the row and runs its checks
            r2 = _s973_row(bid)
            if r2 is not None and r2[0] == S973_KIND:
                res = (_s973_hdr(res[0]), res[1])
        except Exception:                                            # noqa: BLE001
            pass
    return res


def _bg_extract(bid, path, _reading=None):                           # noqa: F811 -- S973: the heal after every reading
    status = _bg_extract_before_s973(bid, path, _reading)
    _s973_heal(only=bid)
    return status


def _s973_after_post(resp):
    try:
        if request.method == "POST":
            _s973_heal()
    except Exception:                                                # noqa: BLE001
        pass
    return resp


def _s973_guard_auto_home():
    _cp = globals().get("_clinic_papers")
    if _cp is None or not hasattr(_cp, "auto_home") or getattr(_cp.auto_home, "_s973", False):
        return
    _orig = _cp.auto_home

    @functools.wraps(_orig)
    def _s973_auto_home(db, bid):
        try:
            _b = db.execute("SELECT kind, doc_kind, lane FROM bills WHERE id=?", (bid,)).fetchone()
            if _b is not None and (_b[2] or "") == "pharmacy" and ((_b[0] or "") == S973_KIND or (_b[1] or "") == "stock_voucher"):
                return []                                            # a stock voucher stays where it was scanned
        except Exception:                                            # noqa: BLE001
            pass
        return _orig(db, bid)
    _s973_auto_home._s973 = True
    _cp.auto_home = _s973_auto_home


try:
    _s973_guard_auto_home()
except Exception as _ex_s973:                                        # noqa: BLE001
    print("S973 _s973_guard_auto_home NOT installed: %s" % _ex_s973, file=_sys.stderr)
try:
    app.after_request(_s973_after_post)
except Exception as _ex_s973:                                        # noqa: BLE001
    print("S973 heal after POST NOT installed: %s" % _ex_s973, file=_sys.stderr)
_s973_heal()                                                         # at start: any stock voucher already on the pharmacy lane as 'Pharmacy'
# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------
