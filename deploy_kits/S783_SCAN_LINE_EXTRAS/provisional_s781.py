"""provisional_s781.py -- kit S781_PROVISIONAL_BILLS (+ S783: free / MRP / discount / GST from the reading; the newest-scan line) (11-Nov-2026, Sanjeevni session 426; D891, D892 -- the owner's mock V3 approved 04:29 IST).
The Purchase bills page (/finance/purchase/page/scans) gains, at its top:
  (a) the month in three parts -- in Marg · scanned, not yet in Marg (provisional) · both -- and how reliable the scans are, by month
      (the strict counter beside the October rules' count);
  (b) the provisional list -- each pharmacy scan of the month with no Marg bill yet: dealer, bill no., the date on the paper, total, its
      read item lines folded, and 'Reads right' / 'Check the paper -- <why>'. It leaves the list by itself when Marg's bill is linked;
  (c) where Marg's bill differs from its scan (the date, the total, a line on one side only) -- 'Check here': the scan inline, the paper's
      lines beside Marg's newest export, the difference named, and the doctor's taps: Amir fixes Marg (one amir_job, Hindi) / Marg is
      right -- clear / Raise a purchase return (one amir_job) / Flag something else (short supply, damaged, wrong batch or near expiry,
      rate above the agreed rate, free goods missing, a note).
NEVER into stock (D891): nothing here writes stock, Marg, purchase_bill, purchase_line or purchase_sarvam_check (the counter stays strict).
Writes only its own table purchase_s781_mark, amir_job rows it creates (created_by 'S781') and audit lines. assets.db is READ ONLY.
Run as a script: python3 provisional_s781.py <finance.db> --lift-all   (the undo: removes the open S781 jobs from Amir's card)."""
import datetime as dt
import difflib
import json
import re
import sqlite3
import sys

KIT = "S781_PROVISIONAL_BILLS"
BY = "S781"
DDL = ("CREATE TABLE IF NOT EXISTS purchase_s781_mark (bill_id INTEGER PRIMARY KEY, action TEXT NOT NULL, flag TEXT, note TEXT, "
       "what TEXT, by_user TEXT, at TEXT NOT NULL, job_key TEXT, export TEXT)")
FLAGS = (("short", "Short supply"), ("damaged", "Damaged / broken"), ("batch", "Wrong batch or expiry near"),
         ("rate", "Rate above the agreed rate"), ("free", "Free goods missing"), ("other", "Other"))
FLAG_EN = dict(FLAGS)
FLAG_HI = {"short": "maal kam aaya", "damaged": "maal toota / kharab", "batch": "galat batch ya expiry paas", "rate": "rate tay rate se zyada",
           "free": "free maal nahi aaya", "other": "aur baat"}
ACTIONS = ("amir", "clear", "return", "flag", "undo")
GST_TOP = 1.18                                               # lines read before tax: the total may sit up to 18% above them
# Free goods, MRP, discount and GST: the scanner does not read them today (11-Nov). The page shows each column by itself the day the
# scan's data carries it (a bill_items column of that name, or the reading's item key), with no change here.
EXTRA = ("free", "mrp", "discount", "gst")
EXTRA_COLS = ("free", "mrp", "discount", "gst")
EXTRA_KEYS = {"free": ("free", "free_qty"), "mrp": ("mrp",), "discount": ("discount", "disc", "discount_pct"), "gst": ("gst", "gst_pct", "tax")}
EXTRA_EN = {"free": "Free", "mrp": "MRP", "discount": "Disc %", "gst": "GST %"}
GONE_EN = {"free": "free goods", "mrp": "MRP", "discount": "discount", "gst": "GST"}


def SR():
    import scan_register                                      # noqa: PLC0415 -- beside this file
    return scan_register


def PA():
    return SR()._pa()


def ensure(con):
    con.execute(DDL)
    if "export" not in {r[1] for r in con.execute("PRAGMA table_info(purchase_s781_mark)")}:
        con.execute("ALTER TABLE purchase_s781_mark ADD COLUMN export TEXT")


def now_iso():
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _d(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def _p(v):
    """rupees (float / str) -> paise int, None when not read."""
    try:
        if v is None or str(v).strip() == "":
            return None
        return int(round(float(str(v).replace(",", "").replace("₹", "").strip()) * 100))
    except ValueError:
        return None


def _f(v):
    try:
        return None if v is None or str(v).strip() == "" else float(str(v).replace(",", ""))
    except ValueError:
        return None


def _table(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def _norm(s):
    return re.sub(r"[^A-Z0-9]+", " ", str(s or "").upper()).strip()


# ------------------------------------------------------------------ the month's bills and scans
def month_bills(con, month):
    pa = PA()
    rows = [dict(r) for r in con.execute("SELECT b.id, b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.month, b.amount_p, b.bw_md5, b.sw_md5 "
                                         "FROM purchase_bill b WHERE " + pa.EFF_BILL + " ORDER BY b.bill_date, b.id")]
    return [b for b in rows if str(b.get("month") or str(b["bill_date"])[:7]) == month]


def in_marg(bills):
    """(count, sum) as the register counts them: a double entry in Marg is one bill (S440's reading); a return reduces the sum."""
    dbl = SR()._doubles(bills)
    seen, n, tot = set(), 0, 0
    for b in bills:
        if b["id"] in seen:
            continue
        if b["id"] in dbl:
            seen.update(dbl[b["id"]])
        n += 1
        tot += int(b["amount_p"] or 0)
    return n, tot


class Assets(object):
    """One read-only look into assets.db per page: the read item lines and the document kind of the scans asked for."""

    def __init__(self, ids):
        self.lines, self.kind = {}, {}
        ids = sorted({int(i) for i in ids})
        if not ids:
            return
        acon = PA()._assets_con()
        if acon is None:
            return
        try:
            q = ",".join("?" * len(ids))
            try:
                bc = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
                if "doc_kind" in bc:
                    self.kind = {int(r[0]): str(r[1] or "") for r in acon.execute("SELECT id, doc_kind FROM bills WHERE id IN (%s)" % q, ids)}
            except sqlite3.Error:
                self.kind = {}
            try:
                cols = {r[1] for r in acon.execute("PRAGMA table_info(bill_items)")}
                if cols:
                    sel = [c if c in cols else "NULL" for c in ("bill_id", "item_name", "pack_size", "batch", "expiry", "quantity", "rate", "amount")
                           + EXTRA_COLS]
                    for r in acon.execute("SELECT %s FROM bill_items WHERE bill_id IN (%s) ORDER BY bill_id, id" % (", ".join(sel), q), ids):
                        if str(r[1] or "").strip():
                            d = dict(name=r[1], pack=r[2], batch=r[3], expiry=r[4], qty=_f(r[5]), rate=_f(r[6]), amount=_f(r[7]))
                            d.update({k: r[8 + i] for i, k in enumerate(EXTRA)})
                            self.lines.setdefault(int(r[0]), []).append(d)
            except sqlite3.Error:
                pass
            self._extras_from_reading(acon, [i for i in ids if i in self.lines])
            left = [i for i in ids if i not in self.lines]
            if left:
                try:
                    rows = acon.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1 AND bill_id IN (%s) ORDER BY rowid"
                                        % ",".join("?" * len(left)), left).fetchall()
                except sqlite3.Error:
                    rows = []
                for bid, data in rows:
                    try:
                        items = (json.loads(data) if data else {}).get("items") or []
                    except ValueError:
                        items = []
                    got = [dict(name=i.get("name"), pack=i.get("unit") or i.get("pack"), batch=i.get("batch"), expiry=i.get("expiry"),
                                qty=_f(i.get("qty")), rate=_f(i.get("rate")), amount=_f(i.get("amount")),
                                **{k: next((i.get(a) for a in EXTRA_KEYS[k] if i.get(a) not in (None, "")), None) for k in EXTRA})
                           for i in items if isinstance(i, dict) and str(i.get("name") or "").strip()]
                    if got:
                        self.lines[int(bid)] = got                 # the newest good reading wins
        finally:
            acon.close()


    def _extras_from_reading(self, acon, ids):
        """S783: free / MRP / discount / GST live only in the reading (bill_items has no columns for them): laid onto the bill_items lines --
        line for line when the counts agree, else by the item's name."""
        need = [i for i in ids if not any(l.get(k) not in (None, "") for l in self.lines.get(i, []) for k in EXTRA)]
        if not need:
            return
        try:
            rows = acon.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1 AND bill_id IN (%s) ORDER BY rowid"
                                % ",".join("?" * len(need)), need).fetchall()
        except sqlite3.Error:
            return
        for bid, data in rows:
            try:
                items = [i for i in ((json.loads(data) if data else {}).get("items") or []) if isinstance(i, dict) and str(i.get("name") or "").strip()]
            except (ValueError, AttributeError, TypeError):
                continue
            if not any(i.get(a) not in (None, "") for i in items for k in EXTRA for a in EXTRA_KEYS[k]):
                continue
            lines = self.lines.get(int(bid), [])
            byname = {}
            for i in items:
                byname.setdefault(_norm(i.get("name")), []).append(i)      # two batches of one item stay two, in their order
            for n, l in enumerate(lines):
                nm = _norm(l.get("name"))
                if n < len(items) and _norm(items[n].get("name")) == nm and byname.get(nm) and items[n] in byname[nm]:
                    src = items[n]
                    byname[nm].remove(src)
                else:
                    src = byname[nm].pop(0) if byname.get(nm) else None
                if src:
                    for k in EXTRA:
                        l[k] = next((src.get(a) for a in EXTRA_KEYS[k] if src.get(a) not in (None, "")), None)


def scan_lines(sid):
    return Assets([sid]).lines.get(int(sid), [])


def known_suppliers(con):
    pa = PA()
    return sorted({pa.supplier_key(r[0]) for r in con.execute("SELECT DISTINCT supplier FROM purchase_bill WHERE supplier IS NOT NULL")})


def dealer_of(con, cx, s, known=None):
    """(the dealer's name as Marg knows it, True) when the scan's vendor is a known supplier; else (the vendor as read, False).
    The exact name first, then the learnt spellings and aliases, then the closest containing name -- the longest, never the first."""
    S, pa = SR(), PA()
    sid = int(s["id"])
    if cx.chosen.get(sid):
        return pa.supplier_key(cx.chosen[sid]), True
    v = str(s.get("vendor") or "").strip()
    if not v or S.vendor_not_read(v):
        return v, False
    known = known if known is not None else known_suppliers(con)
    key = pa.supplier_key(v)
    if key in known:
        return key, True
    agree = []
    for k in known:
        try:
            if S.supplier(cx, v, k) == "agree":
                agree.append(k)
        except Exception:                                     # noqa: BLE001
            continue
    if not agree:
        return v, False
    sub = [k for k in agree if k in key or key in k]
    learnt = [k for k in agree if k not in sub]
    pick = learnt[0] if len(learnt) == 1 else (max(sub, key=lambda k: (len(k), k)) if sub else sorted(agree)[0])
    return pick, True


def provisional(con, month, scans=None, cx=None, assets=None):
    """The pharmacy scans of the month that wait for their Marg bill: [dict(id, stamp, dealer, known, bill_no, date, total_p, day, lines, why)]."""
    S = SR()
    scans = scans if scans is not None else (S.asset_scans(con) or {})
    cx = cx or S.Ctx(con)
    linked = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_link")}
    cand = []
    for sid, s in sorted(scans.items()):
        if sid in linked or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or s.get("month") != month:
            continue
        if cx.why.get(sid, "") not in ("no_bill_yet", "vendor_unknown") or S._unread(s):
            continue
        cand.append(sid)
    A = assets or Assets(cand)
    known = known_suppliers(con)
    open_bills = [b for b in month_bills(con, month) if int(b["id"]) not in {int(r[0]) for r in con.execute("SELECT bill_id FROM purchase_scan_link")}]
    out = []
    for sid in cand:
        s = scans[sid]
        if str(A.kind.get(sid) or s.get("doc_kind") or "").lower() in ("summary", "challan", "statement"):
            continue
        dealer, ok_dealer = dealer_of(con, cx, s, known)
        x = dict(id=sid, stamp=s.get("stamp_no") or "#%d" % sid, dealer=dealer, known=ok_dealer, bill_no=str(s.get("bill_no") or "").strip(),
                 date=str(s.get("bill_date") or "")[:10], total_p=s.get("amount_p"), day=str(s.get("day") or "")[:10], lines=A.lines.get(sid, []))
        x["why"] = judge(x)
        if ok_dealer and x["total_p"]:                         # a Marg bill of the month not yet paired, same dealer and total: never counted twice
            twin = next((b for b in open_bills if PA().supplier_key(b["supplier"]) == dealer and abs(abs(int(b["amount_p"] or 0)) - int(x["total_p"])) <= 200), None)
            if twin:
                x["why"].insert(0, "probably already in Marg as bill %s" % twin["bill_no"])
        out.append(x)
    out.sort(key=lambda x: (x["day"], x["id"]))
    return out


def lines_sum_p(lines):
    am = [_p(l.get("amount")) for l in lines]
    return (sum(a for a in am if a is not None), sum(1 for a in am if a is None))


def judge(x):
    """[] = Reads right; else the reasons, the first shown -- the October rules (measure_oct_v2) for a scan with no Marg bill yet."""
    why = []
    if not x["known"]:
        why.append("the supplier is not known" if x["dealer"] else "the supplier is not read")
    no = x["bill_no"]
    if not no:
        why.append("the bill number is not read")
    elif len(re.sub(r"[^A-Za-z0-9]", "", no)) <= 1:
        why.append('bill number "%s" — a one-digit number is usually a misread' % no)
    d, day = _d(x["date"]), _d(x["day"])
    if not d:
        why.append("the date is not read")
    elif day and (d > day + dt.timedelta(days=1) or d < day - dt.timedelta(days=60)):
        fixed = None
        for y in (day.year, day.year - 1):
            try:
                c = d.replace(year=y)
            except ValueError:
                continue
            if day - dt.timedelta(days=60) <= c <= day + dt.timedelta(days=1):
                fixed = c
                break
        why.append(("the year reads %d" % d.year) if fixed else ("the date reads %s, far from the day it was scanned" % d.strftime("%d-%b-%Y")))
    t = x["total_p"]
    if not t:
        why.append("the total is not read")
    if not x["lines"]:
        why.append("no item lines read")
    elif t:
        s, miss = lines_sum_p(x["lines"])
        if miss:
            why.append("%d line%s without an amount" % (miss, "" if miss == 1 else "s"))
        elif not (abs(s - t) <= 200 or (s < t <= s * GST_TOP + 200)):
            why.append("the lines read come to %s; the total is %s" % (SR().rs2(s), SR().rs2(t)))
    return why


# ------------------------------------------------------------------ how reliable the scans are (the October rules, as a function)
def rules_row(con, cx, r):
    """(strict, by the rules) for one purchase_sarvam_check row -- supplier, bill number, date, total."""
    S = SR()
    try:
        j = json.loads(r["detail"] or "{}")
    except ValueError:
        j = {}
    s, m = j.get("scan") or {}, j.get("marg") or {}
    strict = bool(r["supplier_ok"] and r["billno_ok"] and r["date_ok"] and r["total_ok"])
    if strict:
        return True, True
    b = con.execute("SELECT supplier_norm, bill_no FROM purchase_bill WHERE id=?", (r["bill_id"],)).fetchone()
    sup_ok = bool(r["supplier_ok"]) or S.supplier(cx, s.get("vendor"), m.get("supplier")) == "agree"
    sp, mp = s.get("total_p"), int(m.get("total_p") or 0)
    tot_ok = bool(r["total_ok"])
    if not tot_ok and sp and b:
        one = con.execute("SELECT source_md5 FROM purchase_line WHERE supplier_norm=? AND bill_no=? ORDER BY id DESC LIMIT 1", (b[0], b[1])).fetchone()
        ls = con.execute("SELECT COALESCE(SUM(net_amount_p),0), COUNT(*), COALESCE(SUM(amount_p),0) FROM purchase_line WHERE supplier_norm=? AND bill_no=? "
                         "AND source_md5=?", (b[0], b[1], one[0] if one else "")).fetchone()
        tot_ok = bool((ls[1] and abs(int(sp) - int(ls[0])) <= 100) or (ls[1] and abs(int(sp) - int(ls[2])) <= 100) or abs(int(sp) - mp) <= 200)
    sd, md = _d(s.get("date")), _d(m.get("date"))
    date_ok = bool(r["date_ok"]) or bool(sd and md and ((sd.month, sd.day) == (md.month, md.day)
                                                       or (sd.year == md.year and (sd.day, sd.month) == (md.month, md.day))
                                                       or 0 < (md - sd).days <= 20))
    bc = S.billno_compat(s.get("bill_no"), m.get("bill_no"))
    no_ok = bool(r["billno_ok"]) or bc == "agree" or (bc == "close" and sup_ok and tot_ok)
    return False, bool(sup_ok and tot_ok and date_ok and no_ok)


def reliability(con, months):
    """[(month, n, strict, rules)] -- the counter's rows of each month whose scan is still paired with that bill (an undone pair is not counted)."""
    S = SR()
    cx = S.Ctx(con)
    out = []
    for m in months:
        rows = [dict(r) for r in con.execute("SELECT c.* FROM purchase_sarvam_check c JOIN purchase_scan_link l ON l.asset_bill_id=c.asset_bill_id "
                                             "AND l.bill_id=c.bill_id WHERE c.month=?", (m,))]
        if not rows:
            continue
        st = ru = 0
        for r in rows:
            a, b = rules_row(con, cx, r)
            st += int(a)
            ru += int(b)
        out.append((m, len(rows), st, ru))
    return out


# ------------------------------------------------------------------ where Marg's bill differs from its scan
def marg_lines(con, bill):
    try:
        import section_count                                  # noqa: PLC0415 -- S771's reader of Marg's newest export (spilled numbers too)
        lines, _sp = section_count.bill_lines(con, bill)
        return [dict(name=l["name"], qty=l["qty"], amount=l["amount_net"]) for l in lines]
    except Exception:                                         # noqa: BLE001 -- the plain read
        rows = [dict(r) for r in con.execute("SELECT item, qty, free, net_amount_p, source_md5, id FROM purchase_line WHERE supplier_norm=? AND bill_no=? "
                                             "AND bill_date=? AND direction='PURCHASE' ORDER BY id", (bill["supplier_norm"], bill["bill_no"], bill["bill_date"]))]
        if not rows:
            return []
        newest = rows[-1]["source_md5"]
        return [dict(name=r["item"], qty=(_f(r["qty"]) or 0) + (_f(r["free"]) or 0), amount=(_f(r["net_amount_p"]) or 0) / 100.0)
                for r in rows if r["source_md5"] == newest]


def pair_lines(scan, marg, hints=None):
    """[(scan line | None, marg line | None)] -- the counter's learnt pairs first (hints: scan name -> marg name), then the closest names."""
    hints = hints or {}
    used, out = set(), []
    for sl in scan:
        best, score = None, 0.0
        h = hints.get(_norm(sl["name"]))
        for i, ml in enumerate(marg):
            if i in used:
                continue
            sc = 1.0 if (h and _norm(ml["name"]) == h) else difflib.SequenceMatcher(None, _norm(sl["name"]), _norm(ml["name"])).ratio()
            if sc > score:
                best, score = i, sc
        if best is not None and score >= 0.6:
            used.add(best)
            out.append((sl, marg[best]))
        else:
            out.append((sl, None))
    out += [(None, ml) for i, ml in enumerate(marg) if i not in used]
    return out


def _export(b):
    return "%s/%s" % (b.get("bw_md5") or "", b.get("sw_md5") or "")


def _job(con, key):
    if not key or not _table(con, "amir_job"):
        return None
    r = con.execute("SELECT done_at, said_at, reopened_at FROM amir_job WHERE key=?", (key,)).fetchone()
    return dict(r) if r else None


def _job_finished(j):
    return bool(j and (j.get("done_at") or (j.get("said_at") and str(j["said_at"]) > str(j.get("reopened_at") or ""))))


def differences(con, month, scans=None, only=None):
    """The month's linked bills whose Marg entry differs from the scan: [dict(bill, scan, sid, diffs, pairs, mark, s738, note, cleared)].
    A bill the doctor cleared ('Marg is right') comes back with cleared=True, so its Undo stays reachable. The DATE rule is the owner's
    (D889): Marg carries the date printed on the bill -- a paper date up to 20 days from Marg's is a difference for Amir."""
    S = SR()
    ensure(con)
    scans = scans if scans is not None else (S.asset_scans(con) or {})
    lk = {int(r[0]): int(r[1]) for r in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link")}
    marks = {int(r["bill_id"]): dict(r) for r in con.execute("SELECT * FROM purchase_s781_mark")}
    try:
        tracked = S.s738_tracked(con)
    except Exception:                                         # noqa: BLE001
        tracked = {}
    hints_all = {}
    for r in con.execute("SELECT asset_bill_id, detail FROM purchase_sarvam_check WHERE month=?", (month,)):
        try:
            hints_all[int(r[0])] = {_norm(i.get("scan_item")): _norm(i.get("marg_item")) for i in (json.loads(r[1] or "{}").get("items") or [])
                                    if i.get("marg_item") and (i.get("score") or 0) >= 0.6}
        except ValueError:
            pass
    bills = [b for b in month_bills(con, month) if only is None or int(b["id"]) == int(only)]
    pairs_of = {int(b["id"]): lk[int(b["id"])] for b in bills if int(b["id"]) in lk and lk[int(b["id"])] in scans}
    A = Assets(pairs_of.values())
    SC, sec_dealers, sc_acon = _sc(), set(), None
    if SC is not None and pairs_of:                            # the orthotics bills: S771's own line check (size, side, brand, quantity)
        try:
            SC.ensure_s771(con)
            for sec in SC.COUNT_SECTIONS:
                sec_dealers |= set(SC.section_dealers(con, sec))
            sc_acon = SC._acon() if sec_dealers else None
        except Exception:                                     # noqa: BLE001 -- the plain comparison then
            sec_dealers = set()
    out = []
    try:
        for b in bills:
            x = _one(con, b, scans, pairs_of, A, hints_all, marks, tracked, SC, sec_dealers, sc_acon)
            if x is not None:
                out.append(x)
    finally:
        if sc_acon is not None:
            sc_acon.close()
    return out


def _sc():
    try:
        import section_count                                  # noqa: PLC0415 -- S771's orthotics bill check, beside this file
        return section_count
    except Exception:                                         # noqa: BLE001
        return None


def _one(con, b, scans, pairs_of, A, hints_all, marks, tracked, SC, sec_dealers, sc_acon):
    """One linked bill against its scan: its differences, or None when it agrees."""
    bid = int(b["id"])
    sid = pairs_of.get(bid)
    if sid is None:
        return None
    s = scans[sid]
    diffs = []
    sd, md = _d(s.get("bill_date")), _d(b["bill_date"])
    if sd and md and sd != md and abs((md - sd).days) <= 20 and (sd.month, sd.day) != (md.month, md.day):
        diffs.append(dict(kind="date", paper=sd.isoformat(), marg=md.isoformat()))
    sp, mp = s.get("amount_p"), int(b["amount_p"] or 0)
    mlines = marg_lines(con, b)
    if sp and abs(int(sp) - abs(mp)) > 200:
        msum = int(round(sum((l["amount"] or 0) for l in mlines) * 100)) if mlines else None
        if not (msum is not None and abs(int(sp) - msum) <= 100):
            diffs.append(dict(kind="total", paper=int(sp), marg=abs(mp), diff=int(sp) - abs(mp)))
    slines = A.lines.get(sid, [])
    s771 = None
    if b.get("supplier_norm") in sec_dealers:              # an orthotics dealer: S771's line check, its own taps per line
        try:
            s771 = SC.one_bill(con, sc_acon, b)
        except Exception:                                 # noqa: BLE001 -- the plain comparison then
            s771 = None
    if s771 is not None and s771.get("state") not in ("differs", "agrees"):
        s771 = None                                       # S771 could not compare it (no lines in bill_items, no scan): the plain way
    if s771 is not None:
        pairs = []
        for l in s771.get("lines") or []:
            if l.get("kind") and not (l.get("mark") or {}).get("action"):
                diffs.append(dict(kind="s771", item=l.get("scan") or l.get("marg"), why=l.get("why") or "", line=l))
    else:
        pairs = pair_lines(slines, mlines, hints_all.get(sid)) if slines else []
        one_side = [p for p in pairs if p[0] is None or p[1] is None]
        if slines and mlines and one_side and (len(slines) != len(mlines) or any(d["kind"] == "total" for d in diffs)):
            for a, m in one_side:
                diffs.append(dict(kind="missing_marg" if m is None else "missing_paper", item=(a or m)["name"], amount=(a or m).get("amount")))
    s771_marked = [((l.get("mark") or {}).get("action")) for l in (s771 or {}).get("lines") or [] if l.get("kind") and (l.get("mark") or {}).get("action")]
    if not diffs and not s771_marked:
        return None
    mk, note = marks.get(bid), ""
    if mk and mk["action"] in ("amir", "return") and _job_finished(_job(con, mk.get("job_key"))) and mk.get("export") != _export(b):
        note = "Amir marked it done; Marg's newer export still differs."     # the old answer is spent: the bill asks again
        mk = None
    tr = tracked.get(bid)
    only_cleared_lines = not diffs and s771_marked and all(a == "clear" for a in s771_marked)
    return dict(bill=b, sid=sid, stamp=s.get("stamp_no") or "#%d" % sid, scan=s, diffs=diffs, pairs=pairs, mark=mk, note=note,
                cleared=bool(mk and mk["action"] == "clear") or bool(only_cleared_lines), s771=s771,
                s738=tr if tr and not tr.get("settled_at") and not tr.get("gone_at") else None)


def diff_words(x):
    S = SR()
    w = []
    for d in x["diffs"]:
        if d["kind"] == "date":
            w.append("the paper is dated %s; Marg says %s" % (S.ddmon(d["paper"]), S.ddmon(d["marg"])))
        elif d["kind"] == "total":
            w.append("the paper's total is %s, Marg's %s (%s %s on the paper)" % (S.rs2(d["paper"]), S.rs2(d["marg"]), S.rs2(abs(d["diff"])),
                                                                                 "more" if d["diff"] > 0 else "less"))
        elif d["kind"] == "missing_marg":
            w.append("%s is on the paper, not in Marg" % d["item"])
        elif d["kind"] == "s771":
            w.append("%s — %s" % (d["item"], d["why"][:1].lower() + d["why"][1:]))
        else:
            w.append("%s is in Marg, not on the paper" % d["item"])
    return w or ["every differing line is with Amir"]


def chip(x):
    k = {d["kind"] for d in x["diffs"]}
    if "total" in k:
        d = next(d for d in x["diffs"] if d["kind"] == "total")
        return "Marg differs by %s" % SR().rs(abs(d["diff"]))
    if "date" in k and len(k) == 1:
        return "Marg's date is not the paper's"
    if k & {"missing_marg", "missing_paper", "s771"}:
        n = sum(1 for d in x["diffs"] if d["kind"] in ("missing_marg", "missing_paper", "s771"))
        return "%d line%s differ%s" % (n, "" if n == 1 else "s", "s" if n == 1 else "")
    if x.get("s771"):
        return "Lines with Amir"
    return "Marg differs"


def _hi_parts(x):
    S = SR()
    parts = []
    for d in x["diffs"]:
        if d["kind"] == "date":
            parts.append("bill par tareekh %s hai, Marg mein %s chadhi hai" % (S.ddmon(d["paper"]), S.ddmon(d["marg"])))
        elif d["kind"] == "total":
            parts.append("bill par %s hai, Marg mein %s" % (S.rs2(d["paper"]), S.rs2(d["marg"])))
        elif d["kind"] == "missing_marg":
            parts.append("%s bill par hai, Marg mein nahi chadha" % d["item"])
        elif d["kind"] == "missing_paper":
            parts.append("%s Marg mein hai, bill par nahi hai" % d["item"])
    return parts[:4]


def _amir_busy(con, x):
    """Why 'Amir fixes Marg' would give Amir a second job for the same thing, or ''."""
    S = SR()
    kinds = {d["kind"] for d in x["diffs"]}
    if "s771" in kinds and kinds - {"s771"} <= {"total", "missing_marg", "missing_paper"}:
        return "the line buttons above send each line to Amir"
    if x["s738"] and kinds <= {"total", "missing_marg", "missing_paper", "s771"}:
        return "already on Amir's list to correct Marg (since %s)" % S.ddmon(x["s738"].get("first_seen"))
    if "date" not in kinds and _table(con, "section_bill_mark"):
        r = con.execute("SELECT m.job_key FROM section_bill_mark m WHERE m.bill_id=? AND m.action='amir'", (int(x["bill"]["id"]),)).fetchall()
        for (k,) in r:
            if k and not _job_finished(_job(con, k)) and _job(con, k):
                return "already with Amir from the item check"
    return ""


# ------------------------------------------------------------------ the doctor's taps
def mark(con, who, bill_id, action, flag="", note=""):
    """(ok, message, http). amir | clear | return | flag | undo -- on a bill now listed as differing (undo on any marked bill)."""
    try:
        return _mark(con, who, bill_id, action, flag, note)
    except sqlite3.Error as e:
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return False, "Not saved — the database was busy (%s). Try again." % str(e)[:60], 503


def _mark(con, who, bill_id, action, flag, note):
    ensure(con)
    if action not in ACTIONS:
        return False, "Unknown action.", 400
    have = con.execute("SELECT * FROM purchase_s781_mark WHERE bill_id=?", (bill_id,)).fetchone()
    if action == "undo":
        if not have:
            return False, "Nothing to undo on that bill.", 409
        con.execute("DELETE FROM purchase_s781_mark WHERE bill_id=?", (bill_id,))
        gone = 0
        if have["job_key"] and _table(con, "amir_job"):           # a job Amir has neither done nor said done leaves his card with the mark
            gone = con.execute("DELETE FROM amir_job WHERE key=? AND done_at IS NULL AND said_at IS NULL", (have["job_key"],)).rowcount
        _audit(con, who, "s781_undo", bill_id, dict(was=have["action"], job=have["job_key"], job_removed=gone))
        con.commit()
        return True, ("Undone." if gone or not have["job_key"] else "Undone here. Amir has already done it, so it stays in his record."), 200
    b = con.execute("SELECT * FROM purchase_bill WHERE id=?", (bill_id,)).fetchone()
    if not b:
        return False, "No such bill.", 404
    b = dict(b)
    month = str(b["month"] or str(b["bill_date"])[:7])
    x = next(iter(differences(con, month, only=bill_id)), None)
    if x is None:
        return False, "This bill no longer differs from its scan — the page was out of date. Reload it.", 409
    if x["mark"]:
        return False, "This bill already has your answer (%s) — Undo first." % _done_words(x["mark"]), 409
    if have:                                                  # a spent answer (Amir did it; Marg still differs): the new one replaces it
        con.execute("DELETE FROM purchase_s781_mark WHERE bill_id=?", (bill_id,))
    flag = str(flag or "") if action == "flag" else ""
    note = re.sub(r"\s+", " ", str(note or "")).strip()[:300] if action in ("flag", "return") else ""
    if action == "clear" and x["diffs"] and {d["kind"] for d in x["diffs"]} <= {"s771"}:
        return False, "Each line has its own 'Marg is right' — use those.", 409
    if action == "flag" and flag not in FLAG_EN:
        return False, "Pick what to flag.", 400
    if action == "flag" and flag == "other" and not note:
        return False, "Write a short note for 'Other'.", 400
    ts = now_iso()
    job = None
    dealer = str(b["supplier"] or b["supplier_norm"] or "").title()
    sub = "%s bill %s · %s · Dr sahab ne scan se milaya" % (dealer, b["bill_no"], SR().ddmon(b["bill_date"]))
    if action in ("amir", "return"):
        if not _table(con, "amir_job"):
            return False, "Amir's card is not on this server.", 503
        if action == "amir":
            busy = _amir_busy(con, x)
            if busy:
                return False, "This bill is %s." % busy, 409
            text = "%s bill %s — %s. Marg ki entry theek kijiye." % (dealer, b["bill_no"], "; ".join(_hi_parts(x)))
        else:
            text = "%s bill %s — is bill ka PURCHASE RETURN banaiye (Dr sahab ne kaha)%s." % (dealer, b["bill_no"], (": " + note) if note else "")
        job = "S781:%s:b%d:%s" % (action, int(bill_id), re.sub(r"\D", "", ts))
        con.execute("INSERT OR IGNORE INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                    (job, "tap", dealer, text, sub, ts.replace("T", " "), BY, ts.replace("T", " ")))
    try:
        con.execute("INSERT INTO purchase_s781_mark (bill_id, action, flag, note, what, by_user, at, job_key, export) VALUES (?,?,?,?,?,?,?,?,?)",
                    (int(bill_id), action, flag or None, note or None, "; ".join(diff_words(x))[:500], who, ts, job, _export(b)))
    except sqlite3.IntegrityError:                             # another screen answered the same bill a moment ago
        con.rollback()
        return False, "This bill was answered on another screen a moment ago.", 409
    _audit(con, who, "s781_" + action, bill_id, dict(flag=flag or None, note=note or None, job=job))
    con.commit()
    return True, {"amir": "On Amir's card. The row clears by itself when Marg's next export shows the fix.",
                  "clear": "Cleared: Marg is right for this bill.",
                  "return": "On Amir's card: raise a purchase return.",
                  "flag": "Flagged: %s." % FLAG_EN.get(flag, flag)}[action], 200


def _done_words(mk):
    a = mk.get("action")
    if a == "amir":
        return "with Amir"
    if a == "return":
        return "purchase return asked" + ((" — " + mk["note"]) if mk.get("note") else "")
    if a == "flag":
        return "flagged: %s%s" % (FLAG_EN.get(mk.get("flag"), mk.get("flag") or ""), (" — " + mk["note"]) if mk.get("note") else "")
    return "cleared: Marg is right"


def _audit(con, who, action, ref, detail):
    try:
        PA()._audit(con, who, action, str(ref), detail)
    except Exception:                                         # noqa: BLE001 -- the mark row itself is the record
        pass


def lift_all(con):
    """The undo's last step (after the old code is back): the open S781 jobs leave Amir's card. The marks stay (nothing reads them)."""
    n = 0
    if _table(con, "amir_job"):
        n = con.execute("DELETE FROM amir_job WHERE created_by=? AND done_at IS NULL AND said_at IS NULL", (BY,)).rowcount
    con.commit()
    return n


# ------------------------------------------------------------------ the HTML
CSS = """
#s781{display:flex;flex-direction:column;gap:12px;margin:10px 0 14px}
#s781 .sum{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
#s781 .tile{background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:10px 14px;display:flex;flex-direction:column;gap:2px}
#s781 .tile .k{font-size:13px;color:#5b5b5b}
#s781 .tile .v{font-size:22px;font-weight:800;font-variant-numeric:tabular-nums}
#s781 .tile.prov{background:#e8eef8;border-color:#3b5a8a}#s781 .tile.prov .v{color:#3b5a8a}
#s781 .sub{font-size:13px;color:#5b5b5b}
#s781 .card2{background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:8px}
#s781 h2{font-size:14px;margin:0;letter-spacing:.04em;text-transform:uppercase;color:#5b5b5b}
#s781 .tw{overflow-x:auto}
#s781 table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
#s781 table.main{min-width:760px}
#s781 th{font-size:12px;text-align:left;color:#5b5b5b;font-weight:700;text-transform:uppercase;padding:6px 8px;border-bottom:1px solid #e4e0da}
#s781 td{padding:8px;border-bottom:1px solid #e4e0da;vertical-align:top;font-size:14px}
#s781 td.n,#s781 th.n{text-align:right;white-space:nowrap}
#s781 td.nw{white-space:nowrap}
#s781 .chip{display:inline-block;font-size:12.5px;font-weight:800;border-radius:999px;padding:2px 10px}
#s781 .chip.ok{background:#e4f2e6;color:#2e6b34}#s781 .chip.bad{background:#fbe7e5;color:#b3261e}#s781 .chip.done{background:#e8eef8;color:#3b5a8a}
#s781 .chip.chk{display:block;border-radius:8px;white-space:normal;background:#fdf1dc;color:#8a5300;padding:4px 10px;max-width:34ch}
#s781 .chip.chk span{display:block;font-weight:600}
#s781 .exp{font:700 13.5px system-ui,sans-serif;color:#1f3864;background:#fff;border:1px solid #1f3864;border-radius:8px;padding:5px 10px;cursor:pointer;min-height:44px;white-space:nowrap}
#s781 .lrow td{background:#f6f4f1}
#s781 table.items{min-width:560px;font-size:13.5px}#s781 table.items td{padding:5px 8px;font-size:13.5px}
#s781 .pnl table.items{min-width:0}
#s781 tr.miss td{background:#fbe7e5;color:#b3261e}
#s781 .nr{color:#8a5300;font-size:12.5px;font-weight:700}
#s781 .pnl{display:flex;flex-wrap:wrap;gap:14px}
#s781 .pw{flex:2 1 560px;min-width:0;display:flex;flex-direction:column;gap:8px}
#s781 .pv{flex:1 1 300px;min-width:0;display:flex;flex-direction:column;gap:4px}
#s781 .pv summary{cursor:pointer;font-size:14px;padding:10px 0;color:#1f3864;font-weight:700}
#s781 .pv .s738vb{display:block}
#s781 .pv .s738f{min-height:0;flex:1 1 auto;min-width:0;white-space:normal}
#s781 .pv .s738f iframe{width:100%;height:480px;border:0}
#s781 .pv .s738f:has(.s738err){padding:12px;background:#fdf1dc;border-radius:8px}
#s781 .dw{font-size:14.5px}
#s781 .acts{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
#s781 .act{font:700 14px system-ui,sans-serif;min-height:44px;padding:8px 12px;border-radius:9px;border:1px solid #5b5b5b;background:#fff;color:#1c1c1c;cursor:pointer}
#s781 .act.go{background:#2e6b34;border-color:#2e6b34;color:#fff}
#s781 .flag{display:none;flex-wrap:wrap;gap:6px;align-items:center}
#s781 .flag.on{display:flex}
#s781 .fc{font:600 13px system-ui,sans-serif;border:1px dashed #8a5300;color:#8a5300;background:#fdf1dc;border-radius:999px;padding:6px 12px;cursor:pointer;min-height:44px}
#s781 .note{font:14px system-ui,sans-serif;padding:8px 10px;border:1px solid #5b5b5b;border-radius:8px;min-height:44px;width:100%;max-width:520px;box-sizing:border-box}
#s781 a.lnk{color:#1f3864;font-weight:700;white-space:nowrap;display:inline-flex;align-items:center;min-height:44px}
#s781 tr[hidden]{display:none!important}
#s781 .msg{font-weight:700;color:#b3261e}
#s781diff{padding-bottom:64px}
#s781 .lacts{display:flex;flex-wrap:wrap;gap:6px}#s781 .lacts .act{flex:1 1 130px;white-space:nowrap}
#s781 table.s771 td:first-child,#s781 table.s771 td:nth-child(3){min-width:12ch}
@media (min-width:641px){#s781 .pv{order:-1}}
@media (max-width:640px){
 #s781 .sum{grid-template-columns:1fr}
 #s781 table.main{min-width:0}
 #s781 table.main>tbody>tr.th{display:none}
 #s781 table.main,#s781 table.main>tbody,#s781 table.main>tbody>tr,#s781 table.main>tbody>tr>td{display:block;width:auto}
 #s781 table.main>tbody>tr{border-bottom:1px solid #e4e0da;padding:6px 0}
 #s781 table.main>tbody>tr>td{border:0;padding:3px 4px;text-align:left}
 #s781 table.main>tbody>tr>td[data-k]::before{content:attr(data-k) " · ";color:#5b5b5b;font-size:12px;font-weight:600}
 #s781 .chip.chk{max-width:none}
 #s781 table.s771 tr.th{display:none}
 #s781 table.s771,#s781 table.s771 tbody,#s781 table.s771 tr,#s781 table.s771 td{display:block;width:auto;min-width:0}
 #s781 table.s771 tr{padding:6px 0;border-bottom:1px solid #e4e0da}
 #s781 table.s771 td{border:0;padding:2px 4px;text-align:left}
 #s781 table.s771 td[data-k]::before{content:attr(data-k) " · ";color:#5b5b5b;font-size:12px;font-weight:600}
 #s781 .lrow table.items:not(.s771){min-width:0}
 #s781 .lrow table.items:not(.s771) th:nth-child(2),#s781 .lrow table.items:not(.s771) td:nth-child(2),#s781 .lrow table.items:not(.s771) th:nth-child(3),#s781 .lrow table.items:not(.s771) td:nth-child(3){display:none}
 #s781 .lrow table.items td,#s781 .lrow table.items th{padding:4px 3px}
 #s781 .lrow table.items.wide .rt{display:none}
 #s781 .lrow table.items.wide th{white-space:normal;padding:4px 2px}
 #s781 .lrow table.items.wide td{padding:4px 2px;font-size:13px}
 #s781 .lrow td.n .nr{white-space:normal;display:inline-block;line-height:1.15}
 #s781 .lrow table.items th{font-size:11px}
 #s781 .lrow table.items:not(.s771) th:nth-child(4),#s781 .lrow table.items:not(.s771) td:nth-child(4){display:none}
 #s781 .pnl table.items:not(.s771) th:nth-child(2),#s781 .pnl table.items:not(.s771) td:nth-child(2),#s781 .pnl table.items:not(.s771) th:nth-child(4),#s781 .pnl table.items:not(.s771) td:nth-child(4){display:none}
}
"""

JS = """<script>
function s781tg(b){var r=document.getElementById(b.getAttribute('aria-controls'));if(!r)return;var o=r.hidden;r.hidden=!o;b.setAttribute('aria-expanded',o?'true':'false');
b.textContent=b.textContent.replace(o?'\\u25b8':'\\u25be',o?'\\u25be':'\\u25b8');if(o){var d=r.querySelector('details.s738v');if(d&&!d.open){d.open=true;}}}
function s781l(b){var id=b.getAttribute('data-b');var m=document.getElementById('s781lm'+id);if(m)m.textContent='Saving…';
fetch('/finance/stockmatch/count/api/bills/mark',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({bill:parseInt(id,10),key:b.getAttribute('data-k'),action:b.getAttribute('data-a')})})
.then(function(r){return r.json();}).then(function(j){if(!j.ok){if(m)m.textContent=j.message||j.error||'Not saved.';return;}location.reload();})
.catch(function(){if(m)m.textContent='Not saved — the network did not answer. Try again.';});}
function s781fl(id){var f=document.getElementById('s781f'+id);if(f)f.classList.toggle('on');}
function s781(id,action,flag){var i=document.getElementById('s781n'+id);var note=i?i.value:'';
var m=document.getElementById('s781m'+id);if(m)m.textContent='Saving…';
fetch('%(P)s/api/s781/mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bill:id,action:action,flag:flag||'',note:note})})
.then(function(r){return r.json();}).then(function(j){if(!j.ok){if(m)m.textContent=j.message||j.error||'Not saved.';return;}location.reload();})
.catch(function(){if(m)m.textContent='Not saved — the network did not answer. Try again.';});}
</script>"""


def _dm(iso, day=""):
    """dd-Mon, with the year when it is not the year of the day it was scanned (a misread or an old paper shows itself)."""
    d, t = _d(iso), _d(day) or dt.date.today()
    if not d:
        return ""
    return d.strftime("%d-%b") if d.year == t.year else d.strftime("%d-%b-%Y")


def _cell(v, num=False, money=False):
    S = SR()
    if v is None or str(v).strip() == "":
        return '<td class="%s"><span class="nr">not read</span></td>' % ("n" if (num or money) else "")
    if money:
        return '<td class="n">%s</td>' % S.esc(S.rs2(_p(v)))
    if num:
        f = _f(v)
        return '<td class="n">%s</td>' % S.esc(("%g" % f) if f is not None else v)
    return "<td>%s</td>" % S.esc(v)


def _lines_table(lines):
    S = SR()
    extra = [k for k in EXTRA if any(l.get(k) not in (None, "") for l in lines)]
    head = ('<tr><th>Item as read</th><th>Packing</th><th>Batch</th><th>Expiry</th><th class="n">Qty</th>%s<th class="n rt">Rate</th>%s'
            '<th class="n">Amount</th></tr>' % ('<th class="n">Free</th>' if "free" in extra else "",
                                                "".join('<th class="n">%s</th>' % EXTRA_EN[k] for k in extra if k != "free")))
    body = "".join("<tr>%s%s%s%s%s%s%s%s%s</tr>" % (_cell(l["name"]), _cell(l.get("pack")), _cell(l.get("batch")), _cell(l.get("expiry")),
                                                     _cell(l.get("qty"), num=True), _cell(l.get("free"), num=True) if "free" in extra else "",
                                                     _cell(l.get("rate"), money=True).replace('<td class="n">', '<td class="n rt">', 1),
                                                     "".join(_cell(l.get(k), money=(k == "mrp"), num=(k != "mrp")) for k in extra if k != "free"),
                                                     _cell(l.get("amount"), money=True))
                   for l in lines)
    s, miss = lines_sum_p(lines)
    gone = [GONE_EN[k] for k in EXTRA if k not in extra]
    return ('<div class="tw"><table class="items%s">%s%s</table></div><div class="sub">The lines read add up to <b>%s</b>%s.%s</div>'
            % (" wide" if extra else "", head, body, S.esc(S.rs2(s)), (" (%d without an amount)" % miss) if miss else "",
               (" Not read on this scan: %s." % ", ".join(gone)) if gone else ""))


def summary_html(con, month, prefix, owner, r=None):
    """The whole S781 section for the top of the Purchase bills page."""
    S = SR()
    ensure(con)
    raw_scans = S.asset_scans(con)
    scans = raw_scans or {}
    cx = S.Ctx(con)
    in_n, in_p = in_marg(month_bills(con, month))
    prov = provisional(con, month, scans, cx)
    ok = [x for x in prov if not x["why"]]                    # only a scan that reads right counts: a flagged one is listed, not counted
    pv_p = sum(int(x["total_p"] or 0) for x in ok)
    nchk = len(prov) - len(ok)
    h = ['<div id="s781"><style>%s</style>' % CSS]
    h.append('<div class="sum"><div class="tile"><span class="k">In Marg (Amir has entered)</span><span class="v">%s</span><span class="sub">%d bill%s</span></div>'
             '<div class="tile prov"><span class="k">Scanned, not yet in Marg — provisional</span><span class="v">%s</span><span class="sub">%d bill%s · from the scans%s</span></div>'
             '<div class="tile"><span class="k">The month so far, both together</span><span class="v">%s</span><span class="sub">%d bills</span></div></div>'
             % (S.esc(S.rs(in_p)), in_n, "" if in_n == 1 else "s", S.esc(S.rs(pv_p)), len(ok), "" if len(ok) == 1 else "s",
                (" · %d more to check, not counted" % nchk) if nchk else "", S.esc(S.rs(in_p + pv_p)), in_n + len(ok)))
    h.append(fresh_html(con, raw_scans))
    prev = (dt.date(int(month[:4]), int(month[5:7]), 1) - dt.timedelta(days=1)).strftime("%Y-%m")
    rel = reliability(con, [prev, month])
    if rel:
        parts = "".join('<span><b>%s</b>: %d of %d right on supplier, bill number, date and total <span class="sub">· strictly right on all four: %d</span></span>'
                        % (S.esc(S.month_name(m).split()[0]), ru, n, st) for m, n, st, ru in rel)
        h.append('<div class="card2"><h2>How reliable the scans are</h2><div style="display:flex;flex-wrap:wrap;gap:6px 22px">%s</div>'
                 '<div class="sub">Provisional means the purchase register only. Nothing is added to stock from a scan. When the scans have '
                 'stayed reliable long enough, you decide when they start adding to stock ahead of Marg.</div></div>' % parts)
    rows = []
    for x in prov:
        lid = "s781L%d" % x["id"]
        n = len(x["lines"])
        btn = ('<button type="button" class="exp" aria-expanded="false" aria-controls="%s" onclick="s781tg(this)">%d line%s ▸</button>'
               % (lid, n, "" if n == 1 else "s")) if n else '<span class="nr">none read</span>'
        verdict = ('<span class="chip ok">Reads right</span>' if not x["why"] else
                   '<span class="chip chk">Check the paper<span>%s</span></span>' % S.esc(x["why"][0]) +
                   ("".join('<div class="sub">also: %s</div>' % S.esc(w) for w in x["why"][1:3])))
        dealer = S.esc(x["dealer"]) if x["dealer"] else '<span class="nr">not read</span>'
        if x["dealer"] and not x["known"]:
            dealer += ' <span class="sub">(as read)</span>'
        link = ('<a class="lnk" href="%s/api/s738/scan/%d" target="_blank" rel="noopener">Open the paper</a>' % (S.esc(prefix), x["id"])) if owner else ""
        rows.append('<tr data-scan="%d"><td data-k="Dealer">%s</td><td data-k="Bill no." class="nw">%s</td><td data-k="Date on the paper" class="nw">%s</td>'
                    '<td data-k="Total" class="n">%s</td><td>%s</td><td data-k="Scanned" class="nw">%s</td><td>%s</td><td>%s</td></tr>'
                    % (x["id"], dealer, S.esc(x["bill_no"]) or '<span class="nr">not read</span>',
                       S.esc(_dm(x["date"], x["day"])) if _d(x["date"]) else '<span class="nr">not read</span>',
                       S.esc(S.rs(x["total_p"])) if x["total_p"] else '<span class="nr">not read</span>', btn,
                       S.esc(_dm(x["day"], x["day"])) if x["day"] else "", verdict, link))
        if n:
            rows.append('<tr class="lrow" id="%s" hidden><td colspan="8">%s</td></tr>' % (lid, _lines_table(x["lines"])))
    h.append('<div class="card2" id="s781prov"><h2>Scanned, not yet in Marg — provisional</h2><div class="sub"><b>%d scanned · %d counted · %d to check</b></div>%s'
             '<div class="sub">A row that reads right counts in the month from the day it is scanned; a row to check is not counted until it is '
             'fixed or Marg brings it. A row leaves this list by itself the day Amir\'s Marg export brings the same bill. Amir still enters every '
             'bill in Marg from the paper.</div></div>'
             % (len(prov), len(ok), nchk,
                ('<div class="tw"><table class="main"><tr class="th"><th>Dealer</th><th>Bill no.</th><th>Date on the paper</th><th class="n">Total</th>'
                 '<th>Item lines read</th><th>Scanned</th><th>The scan</th><th></th></tr>%s</table></div>' % "".join(rows))
                if rows else '<div class="sub">None — every scan of the month has its Marg bill.</div>'))
    if owner:
        h.append(differs_html(con, month, prefix, scans))
    h.append(JS % dict(P=prefix))
    h.append("</div>")
    return "".join(h)


def fresh(con, scans):
    """(the newest pharmacy scan's moment | None, the newest Marg bill's date | None) -- for the line that shows a gap."""
    S, pa = SR(), PA()
    newest = None
    cand = [int(i) for i, s in (scans or {}).items() if str(s.get("lane") or "pharmacy") == "pharmacy" and not s.get("dup_of")]
    kinds = Assets(cand).kind if cand else {}
    for i in cand:
        s = scans[i]
        if str(kinds.get(i) or s.get("doc_kind") or "").lower() in ("summary", "challan", "statement"):
            continue                                          # a dealer's statement or a challan is not a bill
        try:
            mo = S._scan_moment(s)
        except Exception:                                     # noqa: BLE001
            mo = None
        if mo and (newest is None or mo > newest):
            newest = mo
    r = con.execute("SELECT MAX(b.bill_date) FROM purchase_bill b WHERE " + pa.EFF_BILL).fetchone()
    return newest, _d(r[0]) if r else None


def fresh_html(con, scans, now=None):
    S = SR()
    newest, marg = fresh(con, scans or {})
    now = now or (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30))       # the scan moments are IST; the server's clock may be UTC
    seen = ("the scans could not be read" if scans is None else
            S.esc(newest.strftime("%d-%b %I:%M %p").replace(" 0", " ")) if newest else "none")
    bits = ["Newest bill scanned: <b>%s</b>" % seen,
            "Marg's bills on the server reach: <b>%s</b>" % (S.esc(marg.strftime("%d-%b")) if marg else "none")]
    gap = ""
    if newest is not None:
        days = sum(1 for k in range(1, (now.date() - newest.date()).days + 1)
                   if (newest.date() + dt.timedelta(days=k)).weekday() != 6)      # working days: a Sunday brings no delivery to scan
        if days >= 2:
            gap = ('<div class="chip chk" style="max-width:none">No bill scanned for %d working days — bills that came since are not on this page '
                   'until reception scans them.</div>' % days)
    return '<div class="card2" id="s781fresh"><div style="display:flex;flex-wrap:wrap;gap:4px 22px">%s</div>%s</div>' % (
        "".join("<span>%s</span>" % b for b in bits), gap)


def _panel(con, x, prefix):
    S = SR()
    bid = int(x["bill"]["id"])
    cmp_rows = []
    for a, m in x["pairs"]:
        miss = a is None or m is None
        cmp_rows.append('<tr class="%s"><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
                        % ("miss" if miss else "", S.esc((a or m)["name"]) + ((' <span class="sub">(Marg: %s)</span>' % S.esc(m["name"]))
                                                                             if a and m and _norm(a["name"]) != _norm(m["name"]) else ""),
                           S.esc("%g" % a["qty"]) if a and a.get("qty") is not None else "—", S.esc(S.rs2(_p(a["amount"]))) if a and a.get("amount") is not None else "—",
                           S.esc("%g" % m["qty"]) if m and m.get("qty") is not None else "—", S.esc(S.rs2(_p(m["amount"]))) if m and m.get("amount") is not None else "—",
                           "<b>not in Marg</b>" if m is None else ("<b>not on the paper</b>" if a is None else "both")))
    table = ('<div class="tw"><table class="items"><tr><th>Item</th><th class="n">Scan qty</th><th class="n">Scan ₹</th><th class="n">Marg qty</th>'
             '<th class="n">Marg ₹</th><th></th></tr>%s</table></div>' % "".join(cmp_rows)) if x["pairs"] else \
        '<div class="sub">No item lines were read on this scan.</div>'
    if x.get("s771"):
        table = _s771_table(x)
    src = "%s/api/s738/scan/%d" % (prefix, x["sid"])
    viewer = ('<details class="s738v" ontoggle="s738open(this)"><summary>The scanned paper ▾</summary><div class="s738vb"><div class="s738f" data-src="%s">'
              '</div></div></details><a class="lnk" href="%s" target="_blank" rel="noopener">Open the scan in a new tab</a>' % (S.esc(src), S.esc(src)))
    mk = x["mark"]
    if mk:
        acts = ('<div class="acts"><span class="sub">Your answer: %s.</span><button type="button" class="act" onclick="s781(%d,\'undo\')">Undo</button>'
                '<span class="msg" id="s781m%d"></span></div>' % (S.esc(_done_words(mk)), bid, bid))
    else:
        busy = _amir_busy(con, x)
        amir_btn = ('<span class="sub">%s.</span>' % S.esc(busy[0].upper() + busy[1:])) if busy else \
            ('<button type="button" class="act go" onclick="s781(%d,\'amir\')">Amir fixes Marg</button>' % bid)
        lines_only = {d["kind"] for d in x["diffs"]} <= {"s771"} and bool(x["diffs"])
        chips = "".join('<button type="button" class="fc" onclick="s781(%d,\'flag\',\'%s\')">%s</button>' % (bid, k, S.esc(v)) for k, v in FLAGS)
        clear_btn = "" if lines_only else ('<button type="button" class="act" onclick="s781(%d,\'clear\')">Whole bill: Marg is right</button>' % bid)
        acts = ('<div class="acts">%s%s'
                '<button type="button" class="act" onclick="s781(%d,\'return\')">Raise a purchase return</button>'
                '<button type="button" class="act" onclick="s781fl(%d)">Flag something else / a note ▸</button><span class="msg" id="s781m%d"></span></div>'
                '<div class="flag" id="s781f%d"><input class="note" id="s781n%d" maxlength="300" placeholder="Note (needed for Other)">%s</div>'
                % (amir_btn, clear_btn, bid, bid, bid, bid, bid, chips))
    note = ('<div class="sub">%s</div>' % S.esc(x["note"])) if x.get("note") else ""
    return ('<div class="pnl"><div class="pw"><div class="dw"><b>The difference:</b> %s.</div>%s%s%s</div><div class="pv">%s</div></div>'
            % (S.esc("; ".join(diff_words(x))), note, table, acts, viewer))


def _s771_table(x):
    """The orthotics bill check (S771) line by line: the bill's item and quantity beside Marg's, the difference, and S771's own taps."""
    S = SR()
    bid = int(x["bill"]["id"])
    bill_ans = (x.get("mark") or {}).get("action") in ("amir", "return")
    rows = []
    for l in x["s771"].get("lines") or []:
        mk = l.get("mark") or {}
        if l.get("kind"):
            if mk.get("action"):
                tap = ('<div class="lacts"><span class="chip done">%s</span><button type="button" class="act" data-b="%d" data-k="%s" data-a="undo" '
                       'onclick="s781l(this)">Undo</button></div>' % ("with Amir" if mk["action"] == "amir" else "this line cleared: Marg is right",
                                                                     bid, S.esc(l["key"])))
            elif bill_ans:
                tap = '<span class="sub">the whole bill is with Amir</span>'
            else:
                tap = ('<div class="lacts"><button type="button" class="act go" data-b="%d" data-k="%s" data-a="amir" onclick="s781l(this)">Amir fixes Marg</button>'
                       '<button type="button" class="act" data-b="%d" data-k="%s" data-a="clear" onclick="s781l(this)">This line: Marg is right</button></div>'
                       % (bid, S.esc(l["key"]), bid, S.esc(l["key"])))
            what = S.esc(l.get("why") or "")
        else:
            tap, what = "", S.esc(l.get("note") or "agrees")
        rows.append('<tr class="%s"><td data-k="On the bill">%s</td><td data-k="Qty" class="n">%s</td><td data-k="In Marg">%s</td>'
                    '<td data-k="Qty" class="n">%s</td><td data-k="Check">%s</td><td>%s</td></tr>'
                    % ("miss" if l.get("kind") and not mk.get("action") else "", S.esc(l.get("scan") or "—"),
                       S.esc("%s" % l["sq"]) if l.get("sq") is not None else "—", S.esc(l.get("marg") or "—"),
                       S.esc("%s" % l["mq"]) if l.get("mq") is not None else "—", what, tap))
    return ('<div class="sub">The orthotics line check — size, side, brand and quantity, line by line:</div><div class="tw"><table class="items s771">'
            '<tr class="th"><th>On the bill</th><th class="n">Qty</th><th>In Marg</th><th class="n">Qty</th><th>Check</th><th></th></tr>%s</table></div>'
            '<span class="msg" id="s781lm%d"></span>' % ("".join(rows), bid))


def _cleared_row(x):
    S = SR()
    bid = int(x["bill"]["id"])
    head = "%s %s" % (S.esc(PA().supplier_key(x["bill"]["supplier"])), S.esc(x["bill"]["bill_no"]))
    if x.get("mark"):
        return ('<div class="acts"><span>%s · %s · %s</span><button type="button" class="act" onclick="s781(%d,\'undo\')">Undo</button>'
                '<span class="msg" id="s781m%d"></span></div>' % (head, S.esc(chip(x)), S.esc(S.ddmon(x["mark"]["at"])), bid, bid))
    return '<div><span>%s · its lines, each cleared by you</span>%s</div>' % (head, _s771_table(x))     # S771's line Undo, reachable here too


def differs_html(con, month, prefix, scans=None):
    S = SR()
    allx = differences(con, month, scans)
    xs = [x for x in allx if not x["cleared"]]
    cleared = [x for x in allx if x["cleared"]]
    rows = []
    for x in xs:
        b, bid = x["bill"], int(x["bill"]["id"])
        cid = "s781C%d" % bid
        mk = x["mark"]
        status = ""
        if mk:
            status = '<span class="chip done">%s · %s</span>' % (S.esc(_done_words(mk)), S.esc(S.ddmon(mk["at"])))
        elif x["s738"]:
            status = '<span class="sub">on Amir\'s list to correct Marg since %s</span>' % S.esc(S.ddmon(x["s738"].get("first_seen")))
        sd = _d(x["scan"].get("bill_date"))
        paper = "%s · %s" % (_dm(sd.isoformat(), b["bill_date"]) if sd else "date not read",
                             S.rs(x["scan"].get("amount_p")) if x["scan"].get("amount_p") else "total not read")
        rows.append('<tr data-bill="%d"><td data-k="Dealer">%s</td><td data-k="Bill no." class="nw">%s</td><td data-k="Paper" class="nw">%s</td>'
                    '<td data-k="Marg" class="nw">%s · %s</td><td><span class="chip bad">%s</span> %s '
                    '<button type="button" class="exp" aria-expanded="false" aria-controls="%s" onclick="s781tg(this)">Check here ▸</button></td></tr>'
                    % (bid, S.esc(PA().supplier_key(b["supplier"])), S.esc(b["bill_no"]), S.esc(paper), S.esc(S.ddmon(b["bill_date"])),
                       S.esc(S.rs(b["amount_p"])), S.esc(chip(x)), status, cid))
        rows.append('<tr class="lrow" id="%s" hidden><td colspan="5">%s</td></tr>' % (cid, _panel(con, x, prefix)))
    cl = ""
    if cleared:
        cl = ('<details><summary class="sub" style="cursor:pointer;padding:8px 0">Cleared by you (Marg is right): %d</summary>%s</details>'
              % (len(cleared), "".join(_cleared_row(x) for x in cleared)))
    if not rows:
        return ('<div class="card2" id="s781diff"><h2>Where Marg differs from the scan: 0</h2><div class="sub">None this month — '
                'every Marg bill with a scan agrees with its paper on the date, the total and the lines.</div>%s</div>' % cl)
    return ('<div class="card2" id="s781diff"><h2>Where Marg differs from the scan: %d</h2><div class="sub">Check here opens the scanned bill, '
            'its lines beside Marg\'s, and what can be done from the same place. Your rule: Marg carries the date printed on the bill. '
            'Nothing here changes stock.</div><div class="tw"><table class="main"><tr class="th"><th>Dealer</th><th>Bill no.</th><th>Paper</th>'
            '<th>Marg</th><th>Result</th></tr>%s</table></div>%s</div>' % (len(xs), "".join(rows), cl))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[2] == "--lift-all":
        c = sqlite3.connect(sys.argv[1], timeout=30)
        print("S781 lift-all: %d open job(s) removed from Amir's card" % lift_all(c))
        c.close()
    else:
        print(__doc__)
