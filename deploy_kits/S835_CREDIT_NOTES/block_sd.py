

# ---------------------------------------------------------------------------------------------- S835_CREDIT_NOTES (D986, F-1174)
# The owner's FINAL mock-up ("Final", 18:39 IST 14-Nov-2026; https://claude.ai/artifact/D8jjGw4t8TjhvZSJWWwRnv; S461_CREDITNOTE_SPEC.md):
# a dealer's CREDIT NOTE (money given back: goods returned, a rate corrected) is a paper kind. The reader recognises it (its no. and the
# invoice no. it names; claude_reader S835) and the desk offers "Make it a Credit note" / "No -- leave it" (S560's pattern). The credit
# note box: its no., date and amount back; "Against which bill?" -- this dealer's bills of the last 90 days, newest first, the reader's
# pick pre-chosen, each opening its scan and, for a pharmacy bill, Marg's purchase entry lines (READ ONLY from finance.db, the bill
# Sanjeevni's register paired the scan with) and whether Marg's purchase return is entered (READ ONLY from the spine); or "Not against
# one bill -- on the dealer's account". One Save.
#   Against a pharmacy bill: handed to Sanjeevni (the pharmacy lane), marked kind 'Pharmacy credit note' -- every Sanjeevni reader of
#     the scan app reads kind='Pharmacy' only, so it is never paired as a bill; it waits there for Amir's purchase return in Marg.
#   Against any other bill: filed with that bill, in its place (its group); the group's month is lowered by the amount back, in the
#     month the CREDIT NOTE is dated in (_s835_cn_rows; _s566_total counts a credit note negative -- The month, the home card and
#     xray_costs read the one sum). The bill's paid state counts it (paid_state, paid_map): "Still owed".
#   On the dealer's account: kept where the person files it; lowers no bill until pointed at one; shown on that dealer's statement box.
#   The switch desk.cn (absent = OFF, on the desk's switch card): until he turns it on, a manager is offered none of it; the owner sees it.
#   NEVER counted as money spent (clinic_papers S835: never "live"), never approved as a bill (status captured), never into a stock or a
#   list (its line panels are refused), never a payment. ONE live link per credit note (credit_note): a re-save that changes it voids the
#   old row (kept) and writes the new one; both papers carry the fingerprint (created_at) -- a re-issued id never inherits a link.
import os as _os835

CN = "credit_note"
CN_KIND_PH = "Pharmacy credit note"      # the pharmacy lane's kind for a credit note: never 'Pharmacy' (Sanjeevni's registers pair those)
CN_DAYS = 90                             # the bills offered: this dealer's, of the 90 days before the credit note's date
CN_MAX = 30
CN_WORDS = ("credit note", "credit memo", "cr note", "cr. note")
FIX_TEXT[CN] = "This looks like a credit note"
FIN_DB_S835 = _os835.environ.get("FINANCE_DB_FOR_SCANS", "/root/finance/finance.db")
SPINE_DB_S835 = _os835.environ.get("SPINE_DB_FOR_SCANS", "/root/finance/spine/spine.db")
_S835_EFF_LINE = "EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND e.md5=l.source_md5)"     # purchase_app.EFF_LINE
S835_DDL = ("CREATE TABLE IF NOT EXISTS credit_note(id INTEGER PRIMARY KEY, cn_bill_id INTEGER NOT NULL, cn_created_at TEXT NOT NULL DEFAULT '', "
            "against_bill_id INTEGER, against_created_at TEXT NOT NULL DEFAULT '', on_account INTEGER NOT NULL DEFAULT 0, amount REAL, "
            "by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')")
DDL = DDL + (S835_DDL,)                  # ensure() reads DDL when it runs (at mount, and the installer's --ensure)


def _s835_on(db, owner):
    """The switch desk.cn (absent = OFF): the credit note flow for Shavez. The owner sees it always (to look at it before it is on)."""
    return bool(owner) or (_setting(db, "desk.cn", "off") or "").strip().lower() == "on"


def _s835_open(b, owner):
    """A pharmacy-lane credit note opens on the desk -- for the owner always, for a manager only while desk.cn is on."""
    if not _s835_is_cn(b):
        return False
    try:
        return _s835_on(AR.get_db(), owner)
    except Exception:                                                # noqa: BLE001
        return bool(owner)


CN_PLACES = CLINIC_DEST + ("construction", "pharmacy")      # where a credit note may be kept: a clinic group, or with Sanjeevni -- never
#                                                             an expense file, NK Pathology or Documents (their readers would count it as spend)


def _s835_is_cn(b):
    return b is not None and (_col(b, "doc_kind") or "") == CN


def _s835_fp(b):
    return (_col(b, "created_at") or "") if b is not None else ""


def _s835_day(b):
    return _iso(b["bill_date"]) or _iso(b["created_at"])


def _s835_link(db, b):
    """The live link of this credit-note paper (its fingerprint holding), or None."""
    try:
        return db.execute("SELECT * FROM credit_note WHERE cn_bill_id=? AND cn_created_at=? AND voided_at='' ORDER BY id DESC LIMIT 1",
                          (b["id"], _s835_fp(b))).fetchone()
    except sqlite3.Error:
        return None


def _s835_against(db, ln):
    """The bill a live link points at, when its fingerprint holds; else None."""
    if ln is None or not ln["against_bill_id"]:
        return None
    r = _row(db, ln["against_bill_id"])
    return r if (r is not None and _s835_fp(r) == (ln["against_created_at"] or "")) else None


def _s835_credits(db, b):
    """The live credit-note papers against this bill (both fingerprints hold; the credit note not set aside, not a double scan)."""
    try:
        return db.execute("SELECT b.* FROM credit_note c JOIN bills b ON b.id=c.cn_bill_id AND COALESCE(b.created_at,'')=c.cn_created_at "
                          "WHERE c.against_bill_id=? AND c.against_created_at=? AND c.voided_at='' AND b.status<>'rejected' AND b.dup_of IS NULL "
                          "AND COALESCE(b.doc_kind,'')=? ORDER BY COALESCE(NULLIF(b.bill_date,''), substr(b.created_at,1,10)), b.id",
                          (b["id"], _s835_fp(b), CN)).fetchall()
    except sqlite3.Error:
        return []


def _s835_credit_sum(db, b):
    if (_col(b, "doc_kind") or "") in NOT_SPEND + (CN,):
        return 0.0
    return float(sum((r["total_amount"] or 0) for r in _s835_credits(db, b)))


def _s835_credit_map(db):
    """{(bill id, bill created_at): the credit notes against it} -- one read for a list page (paid_map adds it)."""
    try:
        return {(r[0], r[1] or ""): float(r[2] or 0) for r in db.execute(
            "SELECT c.against_bill_id, c.against_created_at, SUM(COALESCE(b.total_amount,0)) FROM credit_note c JOIN bills b ON b.id=c.cn_bill_id "
            "AND COALESCE(b.created_at,'')=c.cn_created_at WHERE c.voided_at='' AND c.against_bill_id IS NOT NULL AND b.status<>'rejected' "
            "AND b.dup_of IS NULL AND COALESCE(b.doc_kind,'')=? GROUP BY c.against_bill_id, c.against_created_at", (CN,))}
    except sqlite3.Error:
        return {}


def _s835_cn_rows(db, key, subs, ym):
    """The live credit notes against this section's bills (the bill's group now, on the section's lanes as month_data reads them),
    counted in the month the CREDIT NOTE is dated in (MONTH_OF of the credit note's own row). Rows of the credit-note papers."""
    ph = ",".join("?" * len(subs))
    lanes = ("COALESCE(h.lane,'clinic') IN ('clinic','other_doc','owner_expense')" if key == "construction" else "COALESCE(h.lane,'clinic')='clinic'")
    try:
        return db.execute("SELECT b.*, h.id AS s835_against, h.stamp_no AS s835_against_stamp FROM credit_note c "
                          "JOIN bills b ON b.id=c.cn_bill_id AND COALESCE(b.created_at,'')=c.cn_created_at "
                          "JOIN bills h ON h.id=c.against_bill_id AND COALESCE(h.created_at,'')=c.against_created_at "
                          "WHERE c.voided_at='' AND COALESCE(b.doc_kind,'')='" + CN + "' AND b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL "
                          "AND h.status<>'rejected' AND h.dup_of IS NULL AND " + lanes + " AND h.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? "
                          "ORDER BY b.id", tuple(subs) + (ym,)).fetchall()
    except sqlite3.Error:
        return []


def _s835_cn_view(db, rows):
    return [{"id": r["id"], "stamp": _stamp(r), "inr": _inr(r["total_amount"]), "against": r["s835_against_stamp"] or ""} for r in rows]


def _s835_reader(db, bid):
    """(the reader calls it a credit note, the invoice no. it names)."""
    try:
        r = db.execute("SELECT doc_kind, data FROM claude_reading WHERE bill_id=? AND ok=1", (bid,)).fetchone()
    except sqlite3.Error:
        return False, ""
    if not r:
        return False, ""
    try:
        d = json.loads(r[1] or "{}")
    except (TypeError, ValueError):
        d = {}
    if not isinstance(d, dict):
        d = {}
    return ((r[0] or d.get("doc_kind") or "") == CN), str(d.get("against_no") or "").strip()[:60]


def _s835_runs(s):
    return {x.lstrip("0") for x in re.findall(r"\d+", str(s or "")) if len(x.lstrip("0")) >= 3 and not re.fullmatch(r"20\d\d", x)}


def _s835_no_match(a, n):
    """The invoice no. a credit note names against a bill's number: equal (spaces and case ignored), or one run of three or more
    digits in common, leading zeros dropped ('YS/0803' meets '803'); a year is never the number."""
    if not str(a or "").strip() or not str(n or "").strip():
        return False
    return _numkey(a) == _numkey(n) or bool(_s835_runs(a) & _s835_runs(n))


def _s835_cands(db, b, owner, today=None, vendor=None, day=None):
    """'Against which bill?' -- this dealer's (supplier key) bills of the CN_DAYS days before the credit note's date (the scan day when
    none; a week after it allowed), newest first: a bill, an estimate or a paid-on-challan paper, on ANY lane -- a pharmacy bill scan
    too (kind 'Pharmacy'; read here only, never moved, never listed on the desk). Never this paper, a credit note, a receipt or a
    statement, a set-aside or double scan, a page, a patient's paper; never a bill of another lane (an expense file, NK Pathology, Documents)
    nor a Personal, Resume or Miscellaneous paper (a credit note kept there would be counted as spend). The bill its live link points at
    stays offered, whatever its age."""
    key = _key(b["vendor"] if vendor is None else vendor)
    cur = _s835_against(db, _s835_link(db, b))
    ref = day or _s835_day(b) or (today or _today())
    since, upto = ref - datetime.timedelta(days=CN_DAYS), ref + datetime.timedelta(days=7)
    out = []
    if key:
        for r in db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE b.id<>? AND b.status<>'rejected' AND b.dup_of IS NULL "
                            "AND b.page_of IS NULL AND COALESCE(b.subgroup,'') NOT IN ('" + PATIENT + "','personal','resume','misc') "
                            "AND (COALESCE(b.doc_kind,'bill') IN ('bill','estimate') OR (b.doc_kind='challan' AND b.challan_state='final')) "
                            "AND ((COALESCE(b.lane,'clinic')='clinic' AND COALESCE(b.kind,'')<>'Pharmacy') OR b.kind='Pharmacy') ORDER BY b.id DESC LIMIT 3000", (b["id"],)):
            if _key(r["vendor"]) != key:
                continue
            d = _s835_day(r)
            if (cur is None or r["id"] != cur["id"]) and (d is None or d < since or d > upto):
                continue
            out.append(r)
    out.sort(key=lambda r: ((_s835_day(r) or datetime.date.min), r["id"]), reverse=True)
    out = out[:CN_MAX]
    if cur is not None and cur["id"] not in {r["id"] for r in out} and (owner or (cur["subgroup"] or "") != "personal"):      # its place is checked at Save
        out.append(cur)
    return out


def _s835_ro(path):
    if not path or not _os835.path.exists(path):
        return None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=3)
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.Error:
        return None


def _s835_rs(p):
    try:
        v = float(p or 0) / 100.0
    except (TypeError, ValueError):
        return ""
    return AR._inr(v) if v == int(v) else "%.2f" % v


def _s835_marg(fcon, scan_id):
    """Marg's purchase entry of a pharmacy scan (finance.db, READ ONLY): the bill Sanjeevni's register paired the scan with
    (purchase_scan_link) and its lines, one copy -- item_check.marg_lines' rule (the bill-item-wise lines when there are any, else the
    item-wise ones, from the newest export of that kind still in force). (dict, '') or (None, why)."""
    if fcon is None:
        return None, "Marg's entries could not be read here."
    try:
        lk = fcon.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (scan_id,)).fetchone()
        if not lk:
            return None, "Not paired with its Marg bill yet (Sanjeevni's register)."
        pb = fcon.execute("SELECT * FROM purchase_bill WHERE id=?", (lk[0],)).fetchone()
        if pb is None:
            return None, "Its Marg bill is not there any more."
        ls = [dict(r) for r in fcon.execute("SELECT l.* FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_no=? AND l.bill_date=? AND "
                                            + _S835_EFF_LINE + " ORDER BY l.id", (pb["supplier_norm"], pb["bill_no"], pb["bill_date"]))]
    except sqlite3.Error as ex:
        return None, "Marg's entries could not be read here (%s)." % type(ex).__name__
    if ls:
        typ = "BILLITEMWISE" if any(l.get("line_type") == "BILLITEMWISE" for l in ls) else ls[0].get("line_type")
        ls = [l for l in ls if l.get("line_type") == typ]
        newest = ls[-1]["source_md5"]
        ls = [l for l in ls if l["source_md5"] == newest]
    lines = [{"item": l.get("item") or "", "batch": l.get("batch") or "", "qty": _qty(l.get("qty")) + ((" + " + _qty(l.get("free")) + " free") if l.get("free") else ""),
              "rate": _s835_rs(l.get("rate_p")), "amount": _s835_rs(l.get("net_amount_p") if l.get("net_amount_p") is not None else l.get("amount_p"))}
             for l in ls[:80]]
    return {"bill_no": pb["bill_no"] or "", "date": _dmy(pb["bill_date"]), "seen": _dmy(pb["first_seen_day"]) if pb["first_seen_day"] else "",
            "total": _s835_rs(pb["amount_p"]), "lines": lines, "supplier": pb["supplier"] or ""}, ""


def _s835_ret(scon, supplier, day, amt):
    """Is Marg's purchase return for this credit note entered? The spine (READ ONLY): a RETURN bill of the same supplier (the spine's
    own supkey: the first eight letters), dated from a week before the credit note to 120 days after, within Rs 1 of the amount back."""
    if scon is None:
        return "could not be read here"
    sk = re.sub(r"[^A-Z]", "", (supplier or "").upper())[:8]
    if not sk or amt is None:
        return "not entered yet"
    d0 = day or _today()
    try:
        rows = scon.execute("SELECT bill, date, amount_p FROM sp_purchase_bill WHERE direction='RETURN' AND supkey=? AND date BETWEEN ? AND ? "
                            "ORDER BY date", (sk, (d0 - datetime.timedelta(days=7)).isoformat(), (d0 + datetime.timedelta(days=120)).isoformat())).fetchall()
    except sqlite3.Error:
        return "could not be read here"
    for r in rows:
        if abs(int(r["amount_p"] or 0) - int(round(float(amt) * 100))) <= 100:
            return "entered %s (Marg no. %s)" % (_dmy(r["date"]), r["bill"])
    return "not entered yet"


def _s835_lines_of(db, b, rd=None):
    if rd and rd.get("items"):
        return [{"name": str(i.get("name") or "").strip(), "qty": _qty(i.get("qty")), "amount": _plain(i.get("amount"))} for i in rd["items"][:40]]
    return [{"name": r[0], "qty": _qty(r[1]), "amount": _plain(r[2])} for r in db.execute(
        "SELECT item_name, quantity, amount FROM bill_items WHERE bill_id=? ORDER BY id LIMIT 40", (b["id"],)) if r[0]]


def _s835_acct(db, b, owner):
    """The dealer's credit notes kept on its account (no bill): for the statement box."""
    key = _key(b["vendor"])
    if not key:
        return []
    out = []
    try:
        rows = db.execute("SELECT b.* FROM credit_note c JOIN bills b ON b.id=c.cn_bill_id AND COALESCE(b.created_at,'')=c.cn_created_at "
                          "WHERE c.voided_at='' AND c.on_account=1 AND b.status<>'rejected' AND b.dup_of IS NULL AND COALESCE(b.doc_kind,'')=? "
                          "ORDER BY b.id DESC LIMIT 200", (CN,)).fetchall()
    except sqlite3.Error:
        return []
    for r in rows:
        if r["id"] != b["id"] and _key(r["vendor"]) == key and (owner or (r["subgroup"] or "") != "personal"):
            out.append({"id": r["id"], "stamp": _stamp(r), "no": r["bill_no"] or "", "date": _dmy(r["bill_date"] or r["created_at"]),
                        "inr": _inr(r["total_amount"])})
    return out


def _s835_paper(db, b, owner, rd, today=None):
    """paper_json's S835 part: the credit note box (cn) and, on a bill, its credit notes and what is still owed (cn_on)."""
    out = {"cn": None, "cn_on": None}
    if not _s835_on(db, owner):
        return out
    try:
        if not _s835_is_cn(b):
            cr = _s835_credits(db, b)
            if cr:
                st = paid_state(db, b)
                tot = b["total_amount"]
                credit = sum((r["total_amount"] or 0) for r in cr)
                out["cn_on"] = {"no": b["bill_no"] or "", "date": _dmy(b["bill_date"]) if b["bill_date"] else "", "total": _inr(tot),
                                "paid": _inr(st["paid"]) if st["paid"] else "",
                                "credits": [{"id": r["id"], "stamp": _stamp(r), "no": r["bill_no"] or "", "date": _dmy(r["bill_date"] or r["created_at"]),
                                             "inr": _inr(r["total_amount"])} for r in cr],
                                "owed": _inr(max(0.0, float(tot) - st["paid"] - credit)) if tot is not None else "—"}
        is_cn, ag_no = _s835_reader(db, b["id"])
        ln = _s835_link(db, b)
        cur = _s835_against(db, ln)
        vov, dov = None, None                                       # the supplier and date typed on the desk, not saved yet (the panel's refresh)
        try:
            if "cn_vendor" in request.args:
                vov = str(request.args.get("cn_vendor") or "").strip()[:120]
            dov = parse_date(request.args.get("cn_day")) if request.args.get("cn_day") else None
        except RuntimeError:                                         # outside a request (a walk's direct call)
            pass
        cands = _s835_cands(db, b, owner, today, vendor=vov, day=dov)
        fcon = scon = None
        if any(_lane(r) == "pharmacy" for r in cands):
            fcon, scon = _s835_ro(FIN_DB_S835), _s835_ro(SPINE_DB_S835)
        day = dov or _s835_day(b)
        amt = b["total_amount"] if b["total_amount"] is not None else (rd or {}).get("amount")
        rows, hits = [], []
        try:
            for r in cands:
                ph = _lane(r) == "pharmacy"
                d = _s835_day(r)
                c = {"id": r["id"], "stamp": _stamp(r), "no": r["bill_no"] or "", "date": _dmy(d.isoformat()) if d else "",
                     "inr": _inr(r["total_amount"]) if r["total_amount"] is not None else "no amount", "lane": AR._lane_word_s555(r),
                     "dest": "pharmacy" if ph else (current_dest(r) if current_dest(r) in CN_PLACES else ""), "pharmacy": ph, "file": _s560_file(r["id"]) if r["source_stored"] else "",
                     "cur": bool(cur is not None and cur["id"] == r["id"]), "pre": False, "marg": None, "marg_why": "", "ret": "", "lines": []}
                c["unsorted"] = not c["dest"]
                if ph:
                    c["marg"], c["marg_why"] = _s835_marg(fcon, r["id"])
                    c["ret"] = _s835_ret(scon, (c["marg"] or {}).get("supplier") or r["vendor"], day, amt)
                else:
                    c["lines"] = [{"item": x[0], "qty": _qty(x[1]), "rate": _plain(x[2]), "amount": _plain(x[3])} for x in db.execute(
                        "SELECT item_name, quantity, rate, amount FROM bill_items WHERE bill_id=? ORDER BY id LIMIT 40", (r["id"],)) if x[0]]
                if ag_no and (_s835_no_match(ag_no, r["bill_no"]) or (c["marg"] and _s835_no_match(ag_no, c["marg"]["bill_no"]))):
                    hits.append(c)
                rows.append(c)
        finally:
            for x in (fcon, scon):
                if x is not None:
                    x.close()
        if cur is not None:
            for c in rows:
                c["pre"] = c["cur"]
        elif len(hits) == 1:
            hits[0]["pre"] = True
        out["cn"] = {"read_cn": is_cn, "against_no": ag_no, "cands": rows, "lines": _s835_lines_of(db, b, rd),
                     "cur": ("acct" if (ln is not None and int(ln["on_account"] or 0)) else (str(cur["id"]) if cur is not None else "")),
                     "none": ("No bill of this dealer in the last %d days." % CN_DAYS) if _key(b["vendor"] if vov is None else vov) else "Type the supplier first — the bills offered are that dealer's.",
                     "acct": _s835_acct(db, b, owner)}
    except Exception as ex:                                          # noqa: BLE001 -- the desk never fails because of this panel
        print("S835 panel: %s" % ex, file=sys.stderr)
    return out


def _s835_fix(db, b, rd, owner=True):
    """The 'put right' prompt for a paper the reader calls a credit note (or whose name / number says so) and that is not one yet."""
    if (_col(b, "doc_kind") or "") == CN or not _s835_on(db, owner):
        return None
    is_cn, ag = _s835_reader(db, b["id"])
    if not (is_cn or CP._hits(_s563_words_text(b, rd), list(CN_WORDS))):
        return None
    no = (rd or {}).get("number") or b["bill_no"] or ""
    bits = [x for x in (("Its no. " + no) if no else "", ("against invoice " + ag) if ag else "") if x]
    return (CN, "The reader says this is a CREDIT NOTE — money the dealer gives back (goods returned, a rate corrected)." +
            ((" " + ", ".join(bits) + ".") if bits else ""))


def _s835_named(b):
    """For the refusal on a pharmacy bill: its credit note(s), which do open on the desk."""
    try:
        cr = _s835_credits(AR.get_db(), b)
    except Exception:                                                # noqa: BLE001
        return ""
    return (" Its credit note %s opens here." % ", ".join(_stamp(r) for r in cr)) if cr else ""


def _s835_pre(db, b, p, dest, owner, today=None):
    """Before the Save's destination (before S560's): a credit note's bill checked -- one of this dealer's offered bills, or the dealer's
    account; the destination FORCED to that bill's place ('pharmacy' for a pharmacy bill: handed to Sanjeevni; else the bill's own
    group). A credit note takes no lines into a stock or a list, no challans and no payment (those parts of the Save are dropped). A
    credit note saved as another kind goes back to draft on the clinic lane, so that Save's accept (with its double check) runs.
    Returns (dest, s)."""
    k = str(p.get("kind") or "").strip()
    s = {"cn": k == CN}
    if _s835_is_cn(b) and k != CN and b["status"] == "captured" and _lane(b) == "clinic":
        db.execute("UPDATE bills SET status='draft' WHERE id=?", (b["id"],))
        AR._audit_bill(db, b["id"], "desk_cn_undone", {"kind": k, "status_from": "captured", "status": "draft", "via": "desk"})
    if k != CN:
        return dest, s
    if not _s835_on(db, owner):
        raise DeskError("Credit notes on the desk open when Dr Manoj switches them on. Nothing was saved.", 403)
    for x in ("st_lines", "pr_lines", "fo_lines", "pay", "joins", "mixed"):
        p.pop(x, None)
    amt = _amount(p.get("total_amount")) if "total_amount" in p else b["total_amount"]
    if amt is None or amt <= 0:
        raise DeskError("A credit note: type the amount back. Nothing was saved.")
    ag = str((p.get("cn") or {}).get("against") or "").strip()
    if not ag:
        raise DeskError("A credit note: choose the bill it is against, or “Not against one bill — on the dealer’s account”. Nothing was saved.")
    if ag == "acct":
        if dest and dest not in CN_PLACES:
            raise DeskError("A credit note on the dealer’s account is kept in a clinic group or with Sanjeevni — never in an expense file, NK Pathology or Documents. Nothing was saved.")
        s["acct"] = True
        return dest, s
    day = typed_date(p.get("bill_date"), b["bill_date"]) if str(p.get("bill_date") or "").strip() else None
    offered = {r["id"]: r for r in _s835_cands(db, b, owner, today, vendor=p.get("vendor") if "vendor" in p else None,
                                                 day=_iso(day) if day else None)}
    bid_ = int(ag) if ag.isdigit() else 0
    if bid_ not in offered:
        raise DeskError("That bill is not one of this dealer’s bills of the last %d days. Nothing was saved." % CN_DAYS)
    bl = offered[bid_]
    to = "pharmacy" if _lane(bl) == "pharmacy" else current_dest(bl)
    if not to:
        raise DeskError("%s is not sorted yet — sort it first, then file its credit note. Nothing was saved." % _stamp(bl))
    if to not in CN_PLACES or (to != "pharmacy" and _lane(bl) != "clinic"):
        raise DeskError("%s is not a clinic or pharmacy bill now — choose another, or the dealer’s account. Nothing was saved." % _stamp(bl))
    s["bill"] = bl
    return to, s


def _s835_void(db, ln, b, why):
    db.execute("UPDATE credit_note SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (AR._now_ist(), _who(), ln["id"]))
    det = {"link": ln["id"], "against": ln["against_bill_id"], "on_account": int(ln["on_account"] or 0), "why": why, "via": "desk"}
    AR._audit_bill(db, b["id"], "credit_note_voided", det)
    if ln["against_bill_id"]:
        AR._audit_bill(db, ln["against_bill_id"], "credit_note_voided", det)


def _s835_post(db, bid, p, s, status0):
    """After the Save's destination: a credit note FILED (status captured -- never accepted, never spend), on the pharmacy lane marked
    kind 'Pharmacy credit note', its ONE live link written (a change voids the old row, kept). A paper that is no longer a credit note
    has its link voided and, on the pharmacy lane, its kind back to 'Pharmacy'. Returns the lines for the message."""
    msgs = []
    b = _row(db, bid)
    ln = _s835_link(db, b)
    if not s.get("cn"):
        if ln is not None:
            _s835_void(db, ln, b, "now a %s" % (b["doc_kind"] or "bill"))
            msgs.append("It is no longer a credit note — its link is taken off (kept on record).")
        if _lane(b) == "pharmacy" and (b["kind"] or "") == CN_KIND_PH:
            to_k = "Challan" if (b["doc_kind"] or "") == "challan" else "Pharmacy"      # as _relane: a challan never enters Sanjeevni's register
            db.execute("UPDATE bills SET kind=? WHERE id=?", (to_k, bid))
            AR._audit_bill(db, bid, "kind", {"from": CN_KIND_PH, "to": to_k, "via": "desk"})
        return msgs
    st, pr = _s568_st(), _s634_pr()                                 # a credit note keeps no lines in a stock or a list
    try:
        if st is not None and st.has_lines(db, b):
            st.void_lines(db, b, _who(), "now a credit note")
            msgs.append("Its stationery lines are taken off the stock (a credit note counts nothing there).")
        if pr is not None and pr.has_lines(db, b):
            pr.void_lines(db, b, _who(), "now a credit note")
            msgs.append("Its Procedure room lines are taken off (a credit note counts nothing there).")
    except ValueError as e:
        raise DeskError(str(e) + " Nothing was saved.")
    if _lane(b) == "other_doc":                                     # a credit note is never on the Documents lane (Construction from Sanjeevni's)
        _relane(db, b, "clinic", status0)
        b = _row(db, bid)
    if _lane(b) == "pharmacy":
        if (b["kind"] or "") != CN_KIND_PH:
            db.execute("UPDATE bills SET kind=? WHERE id=?", (CN_KIND_PH, bid))
            AR._audit_bill(db, bid, "kind", {"from": b["kind"], "to": CN_KIND_PH, "via": "desk"})
        if b["status"] != "captured":
            db.execute("UPDATE bills SET status='captured' WHERE id=?", (bid,))
            AR._audit_bill(db, bid, "desk_cn_filed", {"status_from": b["status"], "status": "captured", "lane": "pharmacy", "via": "desk"})
    elif b["status"] in ("draft", "approved"):
        db.execute("UPDATE bills SET status='captured' WHERE id=?", (bid,))
        AR._audit_bill(db, bid, "desk_cn_filed", {"status_from": b["status"], "status": "captured", "lane": _lane(b), "via": "desk"})
    b = _row(db, bid)
    bl = s.get("bill")
    want = (bl["id"], _s835_fp(bl), 0) if bl is not None else (None, "", 1)
    have = (ln["against_bill_id"], ln["against_created_at"] or "", int(ln["on_account"] or 0)) if ln is not None else None
    amt = b["total_amount"]
    if have != want or round(float(ln["amount"] or 0), 2) != round(float(amt or 0), 2):
        if ln is not None:
            _s835_void(db, ln, b, "changed on the desk")
        cur = db.execute("INSERT INTO credit_note(cn_bill_id, cn_created_at, against_bill_id, against_created_at, on_account, amount, by_whom, at) "
                         "VALUES(?,?,?,?,?,?,?,?)", (bid, _s835_fp(b), want[0], want[1], want[2], amt, _who(), AR._now_ist()))
        det = {"link": cur.lastrowid, "credit_note": bid, "against": want[0], "on_account": want[2], "amount": amt, "via": "desk"}
        AR._audit_bill(db, bid, "credit_note", det)
        if bl is not None:
            AR._audit_bill(db, bl["id"], "credit_note_against", det)
        _audit_desk(db, "credit_note", det)
    if bl is None:
        msgs.append("A credit note of %s on the dealer’s account — it lowers no bill until it is pointed at one." % _inr(amt))
    elif _lane(bl) == "pharmacy":
        msgs.append("A credit note of %s against %s — handed to Sanjeevni; it waits there for Amir’s purchase return in Marg." % (_inr(amt), _stamp(bl)))
    else:
        msgs.append("A credit note of %s against %s — its group’s month is lowered by the amount back. Never counted as spend." % (_inr(amt), _stamp(bl)))
    return msgs


# --- S835_CREDIT_NOTES end ---
