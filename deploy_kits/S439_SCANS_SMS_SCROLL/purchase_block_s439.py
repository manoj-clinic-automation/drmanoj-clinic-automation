

# ======================================================================================================================
# S439_SCANS_SMS_SCROLL (30-Sep-2026, session 283, F-661) -- THE MATCHER READS WHAT OCR ACTUALLY WRITES
#
# The owner, 30-Sep: "Yesterday reception scanned all medical bills of September, but the system is showing very few."
# 77 pharmacy scans stood captured and 26 were linked. The S403 grades wanted the bill number letter for letter and the
# vendor as Marg spells it; OCR reads the PRINTED bill:
#   * the bill number with its prefix and zeros -- scan "A000166", Marg "166"; "GPPL-26-64906" / "64906"; "NOT015521" /
#     "15521"; "SF 003051" / "3051"; "18112 (NOT015878)" / "15878";
#   * the vendor misspelt ("KEDAR PHAMACEUTICAL", "SUNINA / CUNINA / QUNINA PHARMACEUTICALS", "SHIVAZ") or the BUYER read
#     as the vendor ("M/S SANJEEVNI MEDICOS");
#   * the year of the date off ("2024-09-14", "2036-09-14").
# So, from here:
#   BILL TAIL    both sides keep the digit runs of the bill number, zeros dropped, a financial-year suffix ("2026-27")
#                set aside; the LAST run is the number, an earlier run of 3+ digits stays as a second candidate.
#   VENDOR       resolved ONCE per scan to a supplier on the server: Marg's own names, both sides of the owner's S263
#                links, the spellings learned here, then a token-set similarity >= 0.70 that must beat the next supplier
#                by 0.10 (a trade word -- PHARMA, AGENCIES, MEDICOS -- weighs 0.3, and a NAME word must pair at 0.80).
#                A link made through similarity learns the spelling (purchase_scan_alias, audited "S439 learned from
#                scan <id>"). SANJEEV* / a bare MEDICOS* is the buyer: vendor unknown, bill tail + amount only.
#   DATE         a year outside this and last financial year is not believed (never blocks a link; its day and month
#                still break ties); vendor + date + amount takes +-3 days.
#   GRADES       1 EXACT    vendor+bill+amount                (S403, as it was)
#                2 EXACT    bill_tail+vendor+amount~2%
#                3 PROBABLE bill+amount~2%                    (S403, as it was)
#                4 PROBABLE bill_tail+amount~2%
#                5 PROBABLE bill_tail+vendor                  (the amount off, or not read)
#                6 PROBABLE vendor+date+amount                (S403's, the date now +-3 days)
#   THE PASS     _rematch() no longer wipes the links. A stored link STAYS while its scan and bill are still there and
#                still match; every captured, unlinked pharmacy scan is then tried, the strongest rule first. A scan
#                whose best bill already has a scan is a second scan of the same paper: dup_cand in purchase_scan_state,
#                NEVER a second link. Every link written is audited (scan_link: grade + rule); a second run links 0.
#                It runs at every Marg purchase push (_rematch_after_push, as since S225), when the scans change
#                (_rematch_if_changed), nightly at 23:59 by cron ("purchase_app.py rematch") and once at install.
#   WHY          every scan still open says why on the scan-links page: no bill on the server yet / vendor unknown /
#                amount differs / no digits read / bill number differs / already scanned. A bill that an open scan
#                probably belongs to says so in the list below it, so nobody is asked to scan it again.
# assets.db stays READ ONLY here (the asset app is the parent's): the duplicate candidate and the reasons live in
# finance.db (purchase_scan_state). The learned spellings live in purchase_scan_alias, NOT in purchase_vendor_alias:
# that table decides which bank account a bill is paid into (S263) and an OCR misreading has no business there.
# ======================================================================================================================
import difflib as _difflib_s439

S439_FY_RE = re.compile(r"(?<!\d)20\d\d\s*[-/]\s*(?:20)?\d\d(?!\d)")
S439_STOP = frozenset(("PVT", "PRIVATE", "LTD", "LIMITED", "MS", "PL", "EXTN", "EXT", "AND", "CO", "THE",
                       "BAREILLY", "BAREILL", "BAREIL", "BAREI"))
S439_TRADE = ("PHARMACEUTICALS", "PHARMACEUTICAL", "PHARMA", "MEDICAL", "MEDICALS", "MEDICOS", "MEDICOSE", "AGENCIES",
              "AGENCY", "SURGICALS", "SURGICAL", "FORMULATIONS", "DISTRIBUTORS", "ENTERPRISES", "TRADERS", "SCIENTIFIC",
              "CHEMIST", "DRUGGIST", "DRUG", "HOUSE", "CENTRE", "AID", "WHOLE", "SALE", "WHOLESALE", "BROS", "STORES",
              "HEALTHCARE")
S439_BUYER = ("SANJEEVNI", "SANJEEVANI", "SANJIVANI")
S439_SIM_MIN = 0.70            # the token-set similarity a vendor must reach ...
S439_SIM_MARGIN = 0.10         # ... and the lead it must have over the next supplier
S439_NAME_MIN = 0.80           # a NAME word must pair this well; trade words alone never make a vendor
S439_DATE_DAYS = 3
S439_HINT_DAYS = 60            # a bill is named as an open scan's likely bill only this near the scan
S439_WHY = {"dup": "already scanned", "no_bill_yet": "no bill on the server yet", "vendor_unknown": "vendor unknown",
            "amount_differs": "amount differs", "no_digits": "no digits read", "number_differs": "bill number differs"}
_trade_memo_s439 = {}


def _bill_tails_s439(s):
    """The digit runs of a bill number, zeros dropped, the LAST run first: 'GPPL-26-64906' -> ['64906'];
    'A000166' -> ['166']; '18112 (NOT015878)' -> ['15878', '18112']; 'YS/0585/2026-27' -> ['585']."""
    t = str(s if s is not None else "")
    runs = [r.lstrip("0") for r in re.findall(r"\d+", S439_FY_RE.sub(" ", t))]
    runs = [r for r in runs if r]
    if not runs:
        runs = [r for r in (x.lstrip("0") for x in re.findall(r"\d+", t)) if r]
    if not runs:
        return []
    out = [runs[-1]]
    for r in reversed(runs[:-1]):
        if len(r) >= 3 and r not in out:
            out.append(r)
    return out


def _tok_sim_s439(a, b):
    if a == b:
        return 1.0
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a)):
        return 0.9
    return _difflib_s439.SequenceMatcher(None, a, b).ratio()


def _trade_word_s439(w):
    """PHARMA, AGENCIES, MEDICOS ... and their misspellings ('PHAMACEUTICAL'): words many suppliers share."""
    if w not in _trade_memo_s439:
        _trade_memo_s439[w] = (w in S439_TRADE) or any(_tok_sim_s439(w, g) >= 0.85 for g in S439_TRADE)
    return _trade_memo_s439[w]


def _vendor_tokens_s439(s):
    """Upper case, letters only, initials joined ('L.K.' -> 'LK'), M/S, PVT, LTD, EXTN and the city dropped."""
    t = re.sub(r"\bM\s*/\s*S\b\.?", " ", str(s or "").upper())
    out, run = [], ""
    for w in re.findall(r"[A-Z]+", t):
        if len(w) == 1:
            run += w
            continue
        if len(run) > 1:
            out.append(run)
        run = ""
        out.append(w)
    if len(run) > 1:
        out.append(run)
    while len(out) > 1 and out[-1] in _CITY_TAILS:
        out.pop()
    return [w for w in out if w not in S439_STOP]


def _vendor_sim_s439(a, b):
    """Token-set similarity of two vendor names, 0..1: every word finds its best partner on the other side
    (spelling-tolerant), a trade word weighs 0.3, the two directions are averaged. 0 unless a NAME word of one pairs
    with a name word of the other at S439_NAME_MIN -- two names that share only 'PHARMACEUTICALS' are not alike."""
    if not a or not b:
        return 0.0
    an = [t for t in a if not _trade_word_s439(t)]
    bn = [t for t in b if not _trade_word_s439(t)]
    if not an or not bn or max(_tok_sim_s439(x, y) for x in an for y in bn) < S439_NAME_MIN:
        return 0.0

    def side(p, q):
        num = den = 0.0
        for t in p:
            w = 0.3 if _trade_word_s439(t) else 1.0
            num += w * max(_tok_sim_s439(t, u) for u in q)
            den += w
        return num / den
    return (side(a, b) + side(b, a)) / 2.0


def _is_buyer_s439(toks):
    """The buyer's own name read as the vendor: SANJEEV* (any spelling), or a bare MEDICOS* with no name beside it."""
    for t in toks:
        if t.startswith(("SANJEEV", "SANJIV", "SANJEV")) or max(_tok_sim_s439(t, x) for x in S439_BUYER) >= 0.8:
            return True
    return (not [t for t in toks if not _trade_word_s439(t)]) and any(t.startswith("MEDICOS") for t in toks)


def _ensure_s439(con):
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_scan_state (
        asset_bill_id INTEGER PRIMARY KEY,        -- assets.db bills.id: a pharmacy scan with no link
        why           TEXT NOT NULL,              -- dup | no_bill_yet | vendor_unknown | amount_differs | no_digits | number_differs
        detail        TEXT,                       -- the sentence the scan-links page shows
        dup_cand      INTEGER,                    -- the scan ALREADY linked to the bill this one matched (never a second link)
        dup_bill      INTEGER,                    -- that purchase_bill.id
        hint_bill     INTEGER,                    -- an unscanned bill this scan probably belongs to (number or amount read differently)
        checked_at    TEXT NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_scan_alias (
        ocr_norm      TEXT PRIMARY KEY,           -- the vendor as OCR spelt it (supplier_key)
        supplier_norm TEXT NOT NULL,              -- the supplier on Marg's bills it was matched to
        scan_id       INTEGER,
        who           TEXT,                       -- 'S439 learned from scan <id>'
        at            TEXT)""")


def _vendor_ctx_s439(con, bills):
    """Every known spelling of every supplier -> the supplier's key on Marg's bills: Marg's own names, both sides of
    the owner's S263 links (READ only), and what this matcher has learned from scans."""
    canon = {}
    for b in bills:
        k = supplier_key(b["supplier"])
        if k:
            canon.setdefault(k, k)
    try:
        for r in con.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias").fetchall():
            c = canon.get(supplier_key(r[0]))
            if c and supplier_key(r[1]):
                canon.setdefault(supplier_key(r[1]), c)
    except sqlite3.Error:
        pass
    suppliers = set(canon.values())
    learned = {}
    try:
        for r in con.execute("SELECT ocr_norm, supplier_norm FROM purchase_scan_alias").fetchall():
            if r[1] in suppliers:
                learned[r[0]] = r[1]
    except sqlite3.Error:
        pass
    return dict(canon=canon, learned=learned, toks={k: _vendor_tokens_s439(k) for k in canon}, memo={})


def _vendor_resolve_s439(text, ctx):
    """The vendor on a scan -> (supplier key or None, how, score); how = exact | learned | similar | buyer | unknown | empty."""
    text = str(text or "")
    if text in ctx["memo"]:
        return ctx["memo"][text]
    toks = _vendor_tokens_s439(text)
    k = supplier_key(text)
    if not toks:
        out = (None, "empty", 0.0)
    elif _is_buyer_s439(toks):
        out = (None, "buyer", 0.0)
    elif k in ctx["canon"]:
        out = (ctx["canon"][k], "exact", 1.0)
    elif k in ctx["learned"]:
        out = (ctx["learned"][k], "learned", 1.0)
    else:
        best, same = {}, None
        for sp, st in ctx["toks"].items():
            if sorted(set(st)) == sorted(set(toks)):
                same = ctx["canon"][sp]                    # only the punctuation differs ('PVT. LTD.', '(EXTN)')
                break
            sc = _vendor_sim_s439(toks, st)
            if sc > best.get(ctx["canon"][sp], 0.0):
                best[ctx["canon"][sp]] = sc
        if same:
            out = (same, "exact", 1.0)
        else:
            ranked = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
            top, sc = ranked[0] if ranked else (None, 0.0)
            second = ranked[1][1] if len(ranked) > 1 else 0.0
            out = ((top, "similar", round(sc, 3)) if top and sc >= S439_SIM_MIN and sc - second >= S439_SIM_MARGIN
                   else (None, "unknown", round(sc, 3)))
    ctx["memo"][text] = out
    return out


def _fy_window_s439(today=None):
    """The first day of LAST financial year to the last day of THIS one: the years an OCR date may carry."""
    today = today or dt.date.today()
    y = today.year if today.month >= 4 else today.year - 1
    return dt.date(y - 1, 4, 1), dt.date(y + 1, 3, 31)


def _date_or_none_s439(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def _prep_s439(scans, bills, ctx):
    win = _fy_window_s439()
    for b in bills:
        b["_skey"] = supplier_key(b["supplier"])
        b["_tails"] = _bill_tails_s439(b["bill_no"])
        b["_date"] = _date_or_none_s439(b["bill_date"])
    for s in scans:
        s["_tails"] = _bill_tails_s439(s["bill_no"])
        s["_vendor"] = _vendor_resolve_s439(s["vendor"], ctx)
        d = _date_or_none_s439(s["bill_date"])
        s["_md"] = (d.month, d.day) if d else None             # the day and month still break ties when the year is off
        s["_date"] = d if (d and win[0] <= d <= win[1]) else None


def _date_gap_s439(s, b):
    """Days between the scan's date and the bill's; an unbelievable year lends its day and month to the bill's year.
    9999 when nothing can be compared."""
    bd = b["_date"]
    if bd is None:
        return 9999
    if s["_date"] is not None:
        return abs((s["_date"] - bd).days)
    if s["_md"]:
        try:
            return abs((dt.date(bd.year, s["_md"][0], s["_md"][1]) - bd).days)
        except ValueError:
            return 9999
    return 9999


def _match_s439(s, b):
    """One scan against one Marg bill -> (rank, grade, rule) or None. The six rules are in the header above."""
    sa, ba = s["amount_p"], b["amount_p"]
    canon, how, _sc = s["_vendor"]
    vend = how != "buyer" and (_vendor_match(s["vendor"], b["supplier"]) or (canon is not None and canon == b["_skey"]))
    bno = bool(s["bill_no"]) and s["bill_no"] == b["bill_no"]
    tail = bool(s["_tails"]) and bool(b["_tails"]) and b["_tails"][0] in s["_tails"]
    near1 = sa is not None and abs(sa - ba) <= 100
    near2 = sa is not None and abs(sa - ba) <= max(100, int(round(0.02 * ba)))
    if vend and bno and near1:
        return 1, "EXACT", "vendor+bill+amount"
    if vend and tail and near2:
        return 2, "EXACT", "bill_tail+vendor+amount~2%"
    if bno and near2:
        return 3, "PROBABLE", "bill+amount~2%"
    if tail and near2:
        return 4, "PROBABLE", "bill_tail+amount~2%"
    if vend and tail:
        return 5, "PROBABLE", "bill_tail+vendor"
    if (vend and near1 and s["_date"] is not None and b["_date"] is not None
            and abs((s["_date"] - b["_date"]).days) <= S439_DATE_DAYS):
        return 6, "PROBABLE", "vendor+date+amount"
    return None


def _tie_s439(s, b):
    """Among bills one rule allows: the bill's number is the scan's LAST digit run first, then the same vendor, then
    the nearer date, then the nearer amount."""
    canon = s["_vendor"][0]
    primary = 0 if (s["_tails"] and b["_tails"] and b["_tails"][0] == s["_tails"][0]) else 1
    vend = 0 if (canon is not None and canon == b["_skey"]) else 1
    return (primary, vend, _date_gap_s439(s, b), abs((s["amount_p"] or 0) - b["amount_p"]))


def _why_s439(s, bills, taken, last_date):
    """Why a scan has no link -> (why, the sentence for the page, hint bill id or None)."""
    tails, amt = s["_tails"], s["amount_p"]
    canon, how, _sc = s["_vendor"]

    def lab(b):
        return "%s bill %s (%s, %s)" % (b["_skey"], b["bill_no"], _human(b["bill_date"]), _r(b["amount_p"]))

    def also(b):
        return " — that bill already has scan #%d" % taken[b["id"]] if b["id"] in taken else ""

    scanned = _date_or_none_s439(s.get("created_at"))
    last = _date_or_none_s439(last_date)
    fresh = s["_date"] is not None and last is not None and s["_date"] > last     # dated after Marg's last bill on the server

    def gap(b):
        """Days from the bill to the scan -- by the date on the paper or the day it was scanned, whichever is nearer."""
        g = [abs((d - b["_date"]).days) for d in (s["_date"], scanned) if d is not None and b["_date"] is not None]
        return min(g) if g else 9999

    def near(b):
        return (1 if b["id"] in taken else 0, gap(b), abs((amt or 0) - b["amount_p"]), b["id"])

    def likely(b):
        """The same supplier's bill of this amount to the rupee -- or within 2% when the numbers are nearly the same digits."""
        d = abs(amt - b["amount_p"])
        if d <= 100:
            return True
        return bool(d <= max(100, int(round(0.02 * b["amount_p"]))) and tails and b["_tails"]
                    and _difflib_s439.SequenceMatcher(None, tails[0], b["_tails"][0]).ratio() >= 0.8)

    if not tails and amt is None:
        return "no_digits", "no digits read — OCR found neither a bill number nor an amount on this scan", None
    # a bill is named as the scan's likely bill only when it is within S439_HINT_DAYS of the scan: an April bill that
    # happens to carry the same number or amount is a coincidence, not a hint
    if canon is None:
        same = [b for b in bills if tails and b["_tails"] and b["_tails"][0] in tails and gap(b) <= S439_HINT_DAYS]
        if same:
            b = min(same, key=near)
            hint = None if b["id"] in taken else b["id"]
            if amt is None:
                return "no_digits", "no digits read — no amount on the scan; %s carries the same number%s" % (lab(b), also(b)), hint
            return ("amount_differs", "amount differs — the scan reads %s; %s on the server%s" % (_r(amt), lab(b), also(b)), hint)
    elif amt is not None and not fresh:
        close = [b for b in bills if b["_skey"] == canon and likely(b) and gap(b) <= S439_HINT_DAYS]
        if close:
            b = min(close, key=near)
            more = (" (%d bills of this supplier carry this amount; this is the nearest)" % len(close)) if len(close) > 1 else ""
            return ("number_differs", "bill number differs — the scan reads '%s' (%s); the likely bill is %s%s%s"
                    % (s["bill_no"] or "nothing", _r(amt), lab(b), more, also(b)), None if b["id"] in taken else b["id"])
    if not tails:
        return "no_digits", "no digits read — OCR found no bill number on this scan", None
    if canon is None:
        if how == "buyer":
            return ("vendor_unknown", "vendor unknown — OCR read the buyer's own name as the vendor, and no bill on the "
                    "server has number %s with this amount" % tails[0], None)
        return ("vendor_unknown", "vendor unknown — '%s' is not a supplier on the server, and no bill has number %s with "
                "this amount" % (str(s["vendor"] or "")[:40] or "nothing read", tails[0]), None)
    return ("no_bill_yet", "no bill on the server yet — %s has no bill %s here; Marg's bills on the server end at %s"
            % (canon, tails[0], _human(last_date) if last_date else "—"), None)


_rematch_before_s439 = _rematch


def _rematch(con, who="system"):                                  # noqa: F811
    """S439: the scan-vs-bill pass (the header above). Stored links stay; every unlinked pharmacy scan is tried, the
    strongest rule first; a second scan of a linked bill is marked, never linked; every open scan gets its reason.
    Returns None when the asset app's database is not reachable, else the counts (new = links written this run)."""
    acon = _assets_con()
    if acon is None:
        return None
    scans = _scans(acon)
    acon.close()
    _ensure_s439(con)
    bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    ctx = _vendor_ctx_s439(con, bills)
    _prep_s439(scans, bills, ctx)
    sby = {s["id"]: s for s in scans}
    bby = {b["id"]: b for b in bills}
    # 1 · a stored link stays while its scan and its bill are still there and still match
    taken, linked, dropped = {}, set(), 0
    for r in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link ORDER BY linked_at, bill_id").fetchall():
        b, s = bby.get(r[0]), sby.get(r[1])
        if b is not None and s is not None and r[1] not in linked and _match_s439(s, b) is not None:
            taken[r[0]] = r[1]
            linked.add(r[1])
            continue
        con.execute("DELETE FROM purchase_scan_link WHERE bill_id=?", (r[0],))
        con.execute("UPDATE purchase_bill SET scan_bill_id=NULL WHERE id=? AND scan_bill_id=?", (r[0], r[1]))
        _audit(con, who, "scan_unlink", r[0], dict(scan=r[1], kit="S439", why=(
            "the bill left the live exports" if b is None else "the scan is gone or rejected" if s is None
            else "the scan and the bill no longer match")))
        dropped += 1
    # 2 · every unlinked scan: the bills its BEST rule allows, the nearest first
    cand = {}
    for s in scans:
        if s["id"] in linked:
            continue
        hits = []
        for b in bills:
            m = _match_s439(s, b)
            if m:
                hits.append((m[0], _tie_s439(s, b), b["id"], m[1], m[2]))
        if hits:
            hits.sort()
            cand[s["id"]] = [h for h in hits if h[0] == hits[0][0]]
    # 3 · the strongest rule first; a bill takes ONE scan -- a scan whose best bill is taken is a second scan of it
    new, dups = [], {}
    for rank in sorted({v[0][0] for v in cand.values()}):
        for tie, sid, bid, grade, rule in sorted((h[1], sid, h[2], h[3], h[4]) for sid, v in cand.items() if v[0][0] == rank for h in v):
            if sid in linked or bid in taken:
                continue
            s, b = sby[sid], bby[bid]
            cur = con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id,asset_bill_id,grade,matched_on,linked_at) VALUES (?,?,?,?,?)",
                              (bid, sid, grade, rule, now_iso()))
            if not cur.rowcount:                                   # another pass linked this bill a moment ago (the cron and a page at once)
                taken[bid] = con.execute("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", (bid,)).fetchone()[0]
                linked.add(taken[bid])
                continue
            con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, bid))
            _audit(con, who, "scan_link", bid, dict(scan=sid, grade=grade, rule=rule, supplier=b["_skey"], bill_no=b["bill_no"], kit="S439"))
            taken[bid] = sid
            linked.add(sid)
            new.append((sid, bid, grade, rule))
            canon, how, sc = s["_vendor"]
            if how == "similar" and canon == b["_skey"]:          # the link proved the spelling: learn it, once
                cur = con.execute("INSERT OR IGNORE INTO purchase_scan_alias (ocr_norm, supplier_norm, scan_id, who, at) VALUES (?,?,?,?,?)",
                                  (supplier_key(s["vendor"]), canon, sid, "S439 learned from scan %d" % sid, now_iso()))
                if cur.rowcount:
                    _audit(con, who, "alias_learn", supplier_key(s["vendor"]), dict(supplier=canon, score=sc, note="S439 learned from scan %d" % sid))
        for sid, v in cand.items():
            if v[0][0] == rank and sid not in linked:
                dups[sid] = (taken[v[0][2]], v[0][2], v[0][4])
    # 4 · the reason of every scan still open
    before = {}
    for r in con.execute("SELECT asset_bill_id, dup_cand FROM purchase_scan_state").fetchall():
        before[r[0]] = r[1]
    con.execute("DELETE FROM purchase_scan_state")
    last_date = max([b["bill_date"] for b in bills if b["bill_date"]] or [None])
    stamp, reasons = now_iso(), {}
    for s in scans:
        sid = s["id"]
        if sid in linked:
            continue
        if sid in dups:
            first, bid, rule = dups[sid]
            b = bby[bid]
            why, hint = "dup", None
            detail = ("already scanned — a second scan of %s bill %s (%s): that bill is linked to scan #%d"
                      % (b["_skey"], b["bill_no"], _human(b["bill_date"]), first))
            if before.get(sid) != first:
                _audit(con, who, "scan_dup", bid, dict(scan=sid, dup_cand=first, rule=rule, kit="S439"))
        else:
            first, bid = None, None
            why, detail, hint = _why_s439(s, bills, taken, last_date)
        reasons[why] = reasons.get(why, 0) + 1
        con.execute("INSERT OR REPLACE INTO purchase_scan_state (asset_bill_id, why, detail, dup_cand, dup_bill, hint_bill, checked_at) VALUES (?,?,?,?,?,?,?)",
                    (sid, why, detail, first, bid, hint, stamp))
    _audit(con, who, "rematch", "", dict(links=len(taken), new=len(new), dups=len(dups), dropped=dropped, scans=len(scans), bills=len(bills)))
    con.commit()
    return dict(links=len(taken), new=len(new), new_links=new, dups=len(dups), dropped=dropped, reasons=reasons,
                scans=len(scans), bills=len(bills),
                unmatched_scans=[s for s in scans if s["id"] not in linked],
                unscanned_bills=[b for b in bills if b["id"] not in taken])


def _scan_state_s439(con):
    """{scan id: why / detail / dup_cand / hint_bill} as the last pass left it; {} before the first pass."""
    try:
        return {r[0]: dict(why=r[1], detail=r[2], dup_cand=r[3], dup_bill=r[4], hint_bill=r[5]) for r in con.execute(
            "SELECT asset_bill_id, why, detail, dup_cand, dup_bill, hint_bill FROM purchase_scan_state").fetchall()}
    except sqlite3.Error:
        return {}


def _cli_s439(argv):
    """python3 -B purchase_app.py rematch [--list] -- the nightly pass (root cron, 23:59) and the install's first run.
    One line of counts; --list adds every scan still open with its reason. Exit 0 also when the asset app's database
    is not reachable (the line says so): the pass simply waits for the next night."""
    global _assets_db

    def say(line):
        try:
            print(line)
        except UnicodeEncodeError:                     # a cron shell with no UTF-8 locale
            print(line.encode("ascii", "replace").decode("ascii"))
    if len(argv) < 2 or argv[1] != "rematch":
        say("usage: purchase_app.py rematch [--list]")
        return 2
    _assets_db = os.environ.get("ASSETS_DB", _assets_db)
    con = sqlite3.connect(os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db")), timeout=60)
    con.row_factory = sqlite3.Row
    _ensure(con)
    r = _rematch(con, os.environ.get("REMATCH_WHO", "nightly"))
    if r is None:
        say("S439 rematch %s: the asset app's database is not reachable -- nothing matched" % now_iso())
        return 0
    fp = _scan_fingerprint()
    if fp:
        con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (REMATCH_SEEN_KEY, fp))
        con.commit()
    say("S439 rematch %s: %d new link(s) · %d links stored · %d pharmacy scans · %d still open (%s)%s"
        % (now_iso(), r["new"], r["links"], r["scans"], len(r["unmatched_scans"]),
           " · ".join("%s %d" % (S439_WHY.get(k, k), v) for k, v in sorted(r["reasons"].items())) or "none",
           (" · %d stale link(s) dropped" % r["dropped"]) if r["dropped"] else ""))
    if "--list" in argv:
        for sid, bid, grade, rule in r["new_links"]:
            b = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (bid,)).fetchone()
            say("  linked  scan #%d -> %s bill %s (%s, %s)  %s  %s" % (sid, supplier_key(b[0]), b[1], _human(b[2]), _r(b[3]), grade, rule))
        st = _scan_state_s439(con)
        for s in sorted(r["unmatched_scans"], key=lambda x: x["id"]):
            say("  open    scan #%d  %s" % (s["id"], (st.get(s["id"]) or {}).get("detail") or ""))
    return 0


if __name__ == "__main__":
    import sys as _sys_s439
    _sys_s439.exit(_cli_s439(_sys_s439.argv))
