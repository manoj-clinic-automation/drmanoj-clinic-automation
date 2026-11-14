

# ---- S841 (14-Nov-2026, the Scan App chat's session 466, kit S841_PHARMACY_CREDIT_NOTE; F-1419, F-1422) ---------------------------------
#  A dealer's CREDIT NOTE scanned straight on the pharmacy lane, no tick: claude_reader.read_pharmacy (S841) recognises it, and the paper
#  is marked kind 'Pharmacy credit note', doc_kind 'credit_note' BEFORE _bg_extract fills the row -- the kind the sorting desk (S835)
#  gives a credit note handed to Sanjeevni. Every Sanjeevni reader of the scan app reads kind='Pharmacy' only (A-D52), so a credit note
#  is never paired as a bill; it waits for Amir's purchase return in Marg, and opens on the desk (S835's box) to be pointed at its bill.
#  A credit note on the pharmacy lane is never kind 'Pharmacy': healed after every POST, after every reading and at start -- a paper
#  with doc_kind 'credit_note', or one whose reading says credit note while its row was never marked (the database was busy; a clinic
#  credit note a person moved onto the pharmacy lane). A PERSON's answer stands: the desk saving it as a bill (another doc_kind), or a
#  person's re-lane AFTER this kit marked it (off the lane and back: the way back from a wrong recognition, as S754's) -- never healed
#  again. The papers page's history rule never moves a pharmacy credit note (it stays
#  where it was scanned until a person files it). The bill's edit page keeps the kind (F-1422: it fell through to the form's choice).
#  The way back without a code undo: settings 'read.pharmacy_cn' = 'off' (absent = on) -- no paper is marked; the reading still says so.
KIT_S841 = "S841_PHARMACY_CREDIT_NOTE"
S841_KIND = "Pharmacy credit note"
_s550_claude_before_s841 = _s550_claude
_bg_extract_before_s841 = _bg_extract
_S841_DOC_SQL = ("SELECT id FROM bills WHERE doc_kind='credit_note' AND lane='pharmacy' AND kind='Pharmacy' "
                 "AND COALESCE(status,'')<>'rejected'")
_S841_READ_SQL = ("SELECT b.id FROM bills b JOIN claude_reading c ON c.bill_id=b.id WHERE c.ok=1 AND c.doc_kind='credit_note' "
                  "AND b.lane='pharmacy' AND b.kind='Pharmacy' AND COALESCE(b.doc_kind,'')='' AND COALESCE(b.status,'')<>'rejected'")


def _s841_on():
    try:
        _d = sqlite3.connect(DB_PATH)
        try:
            _r = _d.execute("SELECT value FROM settings WHERE key='read.pharmacy_cn'").fetchone()
        finally:
            _d.close()
    except sqlite3.Error:
        return True
    return not (_r and (_r[0] or "").strip().lower() == "off")


def _s841_person_said(_d, bid):
    """True when this kit marked the paper and a person re-laned it after that: the person's word stands."""
    r = _d.execute("SELECT MAX(rowid) FROM bill_audit WHERE bill_id=? AND action='kind' AND who LIKE 'server (S841%'", (bid,)).fetchone()
    if not r or r[0] is None:
        return False
    return _d.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='relane' AND rowid>?", (bid, r[0])).fetchone() is not None


def _s841_heal(only=None, who="server (S841 heal)", tries=1):
    """Every credit note on the pharmacy lane still marked 'Pharmacy' -> kind 'Pharmacy credit note', doc_kind 'credit_note', audited
    'kind'. Returns how many (None when the database stayed busy). Its own short connection; never raises."""
    import time as _s841_time
    if not _s841_on():
        return 0
    for _try in range(max(1, tries)):
        try:
            _d = sqlite3.connect(DB_PATH, timeout=30)
            try:
                q, arg = (" AND id=?", (only,)) if only is not None else ("", ())
                ids = [r[0] for r in _d.execute(_S841_DOC_SQL + q, arg)]
                try:
                    rds = [r[0] for r in _d.execute(_S841_READ_SQL + (" AND b.id=?" if only is not None else ""), arg)]
                except sqlite3.OperationalError as _e:
                    if "no such table" not in str(_e):
                        raise
                    rds = []                                         # no reading yet
                n = 0
                for i in ids + [x for x in rds if x not in ids]:
                    if _s841_person_said(_d, i):
                        continue
                    cur = _d.execute("UPDATE bills SET kind=?, doc_kind='credit_note' WHERE id=? AND lane='pharmacy' AND kind='Pharmacy' "
                                     "AND COALESCE(status,'')<>'rejected' AND COALESCE(doc_kind,'') IN ('','credit_note')", (S841_KIND, i))
                    if cur.rowcount == 1:
                        _s754_audit(_d, i, "kind", {"from": "Pharmacy", "to": S841_KIND, "lane": "pharmacy",
                                                    "via": "S841: a credit note on the pharmacy lane"}, who=who)
                        n += 1
                if n:
                    _d.commit()
                return n
            finally:
                _d.close()
        except sqlite3.OperationalError:
            if _try + 1 < max(1, tries):
                _s841_time.sleep(2 * (_try + 1))
        except Exception:                                            # noqa: BLE001
            return 0
    return None


def _s550_claude(bid, path):                                         # noqa: F811 -- S841: a credit note recognised by its content
    res = _s550_claude_before_s841(bid, path)
    if res:
        try:
            _s841_heal(only=bid, who="server (S841 read)", tries=3)  # marked before _bg_extract fills the row and runs its checks
        except Exception:                                            # noqa: BLE001
            pass
    return res


def _bg_extract(bid, path, _reading=None):                           # noqa: F811 -- S841: the heal after every reading
    status = _bg_extract_before_s841(bid, path, _reading)
    _s841_heal(only=bid)
    return status


def _s841_after_post(resp):
    try:
        if request.method == "POST":
            _s841_heal()
    except Exception:                                                # noqa: BLE001
        pass
    return resp


def _s841_guard_auto_home():
    _cp = globals().get("_clinic_papers")
    if _cp is None or not hasattr(_cp, "auto_home") or getattr(_cp.auto_home, "_s841", False):
        return
    _orig = _cp.auto_home

    @functools.wraps(_orig)
    def _s841_auto_home(db, bid):
        try:
            _b = db.execute("SELECT kind, doc_kind, lane FROM bills WHERE id=?", (bid,)).fetchone()
            if _b is not None and (_b[2] or "") == "pharmacy" and ((_b[0] or "") == S841_KIND or (_b[1] or "") == "credit_note"):
                return []                                            # a pharmacy credit note stays where it was scanned
        except Exception:                                            # noqa: BLE001
            pass
        return _orig(db, bid)
    _s841_auto_home._s841 = True
    _cp.auto_home = _s841_auto_home


try:
    _s841_guard_auto_home()
except Exception as _ex_s841:                                        # noqa: BLE001
    print("S841 _s841_guard_auto_home NOT installed: %s" % _ex_s841, file=_sys.stderr)
try:
    app.after_request(_s841_after_post)
except Exception as _ex_s841:                                        # noqa: BLE001
    print("S841 heal after POST NOT installed: %s" % _ex_s841, file=_sys.stderr)
_s841_heal()                                                         # at start: any credit note already on the pharmacy lane as 'Pharmacy'
# ---- S841 end ---------------------------------------------------------------------------------------------------------------------------
