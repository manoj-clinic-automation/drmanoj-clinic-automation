#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  med_names.py  ·  v1.0  ·  kit S628_ONE_NAME_LIST  ·  22-Oct-2026 (Sanjeevni session 339; D761, D760)
#
#  THE ONE NAME LIST OF THE PHARMACY. Every spelling of a medicine that the estate meets -- Marg's item list, its order sheet, its purchase
#  report, a dealer's printed bill as Claude reads it -- is joined to ONE Marg item here. Two kinds of row in one table, med_name:
#    kind 'marg'  two Marg items that are ONE medicine (Marg holds THIO Q AP and, since 15-10, THIO Q AP TAB; LINVIZ 600 and LINVIZ 600 6T).
#                 Learnt from an order: its own dealer's bill after the order carries the other item and no line of the ordered one; the two
#                 names differ ONLY by pack / form words (TAB, CAP, STRIP, 6T, 10*10, 1X10), never by a strength or a letter; the price per
#                 tablet agrees within PRICE_TOL. Anything weaker is ASKED of the owner once (one line on his order list), never assumed.
#    kind 'scan'  a dealer's printed spelling of a Marg item ("TAB ORICOX-P 10*10" on Kedar's paper = ORICOX P). Learnt from every pharmacy
#                 scan linked to its Marg bill (purchase_scan_link) that Claude has read: quantity agrees, rate agrees, the names pass the
#                 loose test, and the pairing is one to one. Only sure pairs are kept; a scan spelling is never asked (it moves no count).
#  NEVER: two strengths or two sizes outside the pack-word rule (S598's sibling rule stands); a substitute (D760: FLEMCORT for FLACORT is a
#  different medicine -- its letters differ, so it is never sure; and the owner's question says "the same medicine?").
#
#  READERS (pure SQL on finance.db, no import of stock_figure -- stock_figure.printed_forms calls same_items(), so no cycle):
#    same_items(con, name)        the 'marg' partners of a name (sure or yes), both directions
#    forms(con, item, sn=None)    the item, its partners, and -- for a dealer -- the scan spellings of each (sure)
#    questions(con) / answer(con, id, yes, who)    the owner's Yes / No
#  THE ONE WRITER: learn(con, now) -- keyed, idempotent; writes med_name and med_name_seen only. Called at the head of porders.detect_supplies
#  (fail-soft) and once by the installer (the September seed). assets.db and the spine are opened READ ONLY.
#  No phone number is read or printed by this file.
# =============================================================================
import datetime as dt
import difflib
import json
import re
import sqlite3

VERSION = "1.0"
KIT = "S628_ONE_NAME_LIST"
PRICE_TOL = 0.05                     # the price per tablet of two Marg items of one medicine
RATE_TOL = 0.03                      # a scan line's rate against Marg's line of the same bill
WINDOW_DAYS_DEFAULT = 7              # names.window_days: an order's own dealer's bill this many days after the order day
ASK_RATIO = 0.85                     # letters this alike (numbers equal, no form clash) -> asked, never sure
DDL = ("CREATE TABLE IF NOT EXISTS med_name (id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('marg','scan')), supplier_norm TEXT NOT NULL DEFAULT '',"
       " form TEXT NOT NULL, form_norm TEXT NOT NULL, item TEXT NOT NULL, item_norm TEXT NOT NULL, state TEXT NOT NULL CHECK (state IN ('sure','ask','yes','no')),"
       " why TEXT, learnt_at TEXT NOT NULL, answered_by TEXT, answered_at TEXT, UNIQUE (kind, supplier_norm, form_norm, item_norm))")
SEEN_DDL = "CREATE TABLE IF NOT EXISTS med_name_seen (asset_bill_id INTEGER PRIMARY KEY, reading_at TEXT, pairs INTEGER, at TEXT NOT NULL)"
TAB_WORDS = {"TAB", "TABS", "TABLET", "TABLETS", "TB"}
CAP_WORDS = {"CAP", "CAPS", "CAPSULE", "CAPSULES"}
NEUTRAL_WORDS = {"STRIP", "STRIPS"}
VARIANT_WORDS = {"FORTE", "FORT", "PLUS", "XT", "SR", "CR", "MR", "ER", "XR", "DS", "DSR", "OD", "XL", "SP", "AP", "LS", "MAX", "NEO", "NANO", "DT", "MD",
                 "KID", "KIDS", "JUNIOR", "JR", "AQ", "GEL", "INJ", "SYP", "CREAM", "OINT", "DROP", "DROPS", "SPRAY", "SUSP", "TH", "CV", "LA", "EXTRA",
                 "XTRA", "P", "M", "D", "H", "Z", "SACH", "SACHET", "POWDER", "LOTION"}   # a word that makes another medicine of the same name
GOOD = ("sure", "yes")


# ------------------------------------------------------------------ names
def nm(s):
    """The name as the list keys it: case and spacing folded, a trailing dot dropped (stock_watch.pad_norm's shape)."""
    t = re.sub(r"\s+", " ", str(s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", t)


def toks(s, packs=False):
    """Words of a name; every mark is a space. packs=True (the scan test only): a pack count '10*10' / '1X10' becomes the word PACK. For two Marg
    items (packs=False) a 'N*M' stays numbers -- LEUKOCREPE 6*4 and 8*4 are two sizes, never one medicine."""
    t = str(s or "").upper()
    if packs:
        t = re.sub(r"(\d+)\s*[\*X]\s*(\d+)", " PACK ", t)
    return [w for w in re.sub(r"[^A-Z0-9]+", " ", t).split() if w]


def is_pack(w, packs=False):
    """A tablet / capsule / strip word, or a tablet count '6T' (or 'PACK' in the scan test). '15S' is never dropped (a size)."""
    return w in TAB_WORDS or w in CAP_WORDS or w in NEUTRAL_WORDS or bool(re.match(r"^\d+T$", w)) or (packs and w == "PACK")


def core(s, packs=False):
    return [w for w in toks(s, packs) if not is_pack(w, packs)]


def _form(s):
    """'tab' / 'cap' / '' -- the dose-form family a name prints."""
    ws = set(toks(s))
    if ws & TAB_WORDS or any(re.match(r"^\d+T$", w) for w in ws):
        return "tab"
    if ws & CAP_WORDS:
        return "cap"
    return ""


def form_clash(a, b):
    fa, fb = _form(a), _form(b)
    return bool(fa and fb and fa != fb)


def pack_pair(a, b):
    """True when the two names are ONE medicine by the pack-word rule: every word that is not a pack / form word is the same, in the same
    order (so every strength number agrees), the names are not the same, and no tablet / capsule clash."""
    ca, cb = core(a), core(b)
    return bool(ca) and ca == cb and nm(a) != nm(b) and not form_clash(a, b)


def _nums(ws):
    return [w for w in ws if re.search(r"\d", w)]


VARIANT_SAME = {"FORT": "FORTE", "XTRA": "EXTRA", "SACH": "SACHET", "DROP": "DROPS", "KID": "KIDS", "JR": "JUNIOR"}


def _variants(ws):
    return sorted(VARIANT_SAME.get(w, w) for w in ws if w in VARIANT_WORDS)


def _letters(ws):
    return "".join(re.sub(r"[^A-Z]", "", w) for w in ws)


def near_pair(a, b):
    """Weaker than pack_pair -- the numbers agree, no form clash, and the letters are at least ASK_RATIO alike: ASKED, never sure."""
    ca, cb = core(a), core(b)
    if not ca or not cb or form_clash(a, b) or _nums(ca) != _nums(cb) or _variants(ca) != _variants(cb):
        return False
    la, lb = _letters(ca), _letters(cb)
    if not la or not lb or la == lb:
        return False
    return difflib.SequenceMatcher(None, la, lb).ratio() >= ASK_RATIO


def loose(read, marg):
    """The scan test: a dealer's printed name against Marg's (pack / form words dropped first). The numbers left must agree; then the same
    letters, or one side's words all inside the other's (two words at least: 'NASO B12 NASAL SPRY' / 'NASO B12'), or one a prefix of the
    other (0.6 of the length), or the letters 0.8 alike. Returns a score in (0, 1]; 0 = no."""
    ca, cb = core(read, True), core(marg, True)
    if not ca or not cb or _nums(ca) != _nums(cb) or form_clash(read, marg) or _variants(ca) != _variants(cb):
        return 0.0                                            # PATOPAN D is never PATOPAN DSR; TYCOB-FORT is TYCOB FORTE
    la, lb = _letters(ca), _letters(cb)
    if not la or not lb:
        return 0.0
    if la == lb:
        return 1.0
    sa, sb = set(ca), set(cb)
    small, big = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    if len(small) >= 2 and small == (sa & sb) and not ((big - small) & VARIANT_WORDS):
        return 0.95                                           # NASO B12 NASAL SPRY = NASO B12; never DOLO 650 PLUS = DOLO 650
    if la.startswith(lb) or lb.startswith(la):
        r = min(len(la), len(lb)) / float(max(len(la), len(lb)))
        if r >= 0.6:
            return 0.9
    r = difflib.SequenceMatcher(None, la, lb).ratio()
    return r if r >= 0.8 else 0.0


def packn(p):
    m = re.match(r"^\s*(\d+)\s*[\*X]\s*(\d+)\s*\.?\s*$", str(p or "").upper())
    return int(m.group(1)) * int(m.group(2)) if m else None


# ------------------------------------------------------------------ the table
def ensure(con):
    try:
        con.execute(DDL)
        con.execute(SEEN_DDL)
        con.execute("CREATE INDEX IF NOT EXISTS med_name_item ON med_name (item_norm)")
        con.execute("CREATE INDEX IF NOT EXISTS med_name_form ON med_name (form_norm)")
    except sqlite3.Error:
        pass


def _has(con):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE name='med_name'").fetchone() is not None
    except sqlite3.Error:
        return False


def same_items(con, name):
    """The other Marg item names that are the same medicine as `name` (kind 'marg', sure or yes), both directions. [] when none or no table."""
    if con is None or not _has(con):
        return []
    n = nm(name)
    out = []
    try:
        for f, i in con.execute("SELECT form, item FROM med_name WHERE kind='marg' AND state IN ('sure','yes') AND (item_norm=? OR form_norm=?)", (n, n)):
            o = f if nm(i) == n else i
            if nm(o) != n and o not in out:
                out.append(o)
    except sqlite3.Error:
        return []
    return out


def forms(con, item, sn=None):
    """The item, its Marg partners and -- for the dealer `sn` (purchase_app.supplier_key) -- the dealer's printed spellings of each."""
    out = [str(item)]
    out += [x for x in same_items(con, item) if x not in out]
    if sn and con is not None and _has(con):
        norms = [nm(x) for x in out]
        try:
            q = "SELECT form FROM med_name WHERE kind='scan' AND state IN ('sure','yes') AND supplier_norm=? AND item_norm IN (%s) ORDER BY id" % ",".join("?" * len(norms))
            for (f,) in con.execute(q, [sn] + norms):
                if f and nm(f) not in [nm(x) for x in out]:
                    out.append(f)
        except sqlite3.Error:
            pass
    return out


def _put(con, kind, sn, form, item, state, why, now):
    """One row by its key; an existing row keeps its state (an answered 'yes' / 'no' is never re-asked, a 'sure' never downgraded) -- except an
    'ask' that the learner now finds sure."""
    t = now.replace(microsecond=0).isoformat() if hasattr(now, "isoformat") else str(now)
    r = con.execute("SELECT id, state FROM med_name WHERE kind=? AND supplier_norm=? AND form_norm=? AND item_norm=?", (kind, sn or "", nm(form), nm(item))).fetchone()
    if r is None and kind == "marg":                          # a marg pair is one row whichever side was ordered
        r = con.execute("SELECT id, state FROM med_name WHERE kind='marg' AND form_norm=? AND item_norm=?", (nm(item), nm(form))).fetchone()
    if r is not None:
        if r[1] == "ask" and state == "sure":
            con.execute("UPDATE med_name SET state='sure', why=?, learnt_at=? WHERE id=?", (json.dumps(why, sort_keys=True), t, r[0]))
            return "upgraded"
        return ""
    con.execute("INSERT INTO med_name (kind, supplier_norm, form, form_norm, item, item_norm, state, why, learnt_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (kind, sn or "", str(form), nm(form), str(item), nm(item), state, json.dumps(why, sort_keys=True), t))
    return state


# ------------------------------------------------------------------ the owner's questions
def questions(con):
    if not _has(con):
        return []
    return [dict(r) for r in _rows(con, "SELECT * FROM med_name WHERE state='ask' ORDER BY id")]


def _rows(con, q, a=()):
    old = con.row_factory
    con.row_factory = sqlite3.Row
    try:
        return con.execute(q, a).fetchall()
    finally:
        con.row_factory = old


def question_text(r, en=True):
    w = json.loads(r.get("why") or "{}")
    if r["kind"] == "marg":
        return "%s on %s's bill %s = %s? The same medicine?" % (r["form"], w.get("dealer") or "the dealer", w.get("bill") or "", r["item"])
    return "%s on %s's bill = %s?" % (r["form"], w.get("dealer") or r.get("supplier_norm") or "the dealer", r["item"])


def answer(con, qid, yes, who):
    """The owner's Yes / No on one asked row -> (ok, state). Only an 'ask' row is answered; the answer is kept (a 'no' is never asked again)."""
    ensure(con)
    st = "yes" if yes else "no"
    cur = con.execute("UPDATE med_name SET state=?, answered_by=?, answered_at=? WHERE id=? AND state='ask'",
                      (st, str(who or ""), dt.datetime.now().replace(microsecond=0).isoformat(), int(qid)))
    if not cur.rowcount:
        return False, ""
    con.commit()
    return True, st


# ------------------------------------------------------------------ the learner
def _setting_int(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return int(float(r[0])) if r and str(r[0]).strip() != "" else default
    except (sqlite3.Error, ValueError, TypeError):
        return default


def _since(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='order.track_since'").fetchone()
        v = str(r[0]) if r else ""
    except sqlite3.Error:
        v = ""
    return v[:10] if re.match(r"^\d{4}-\d\d-\d\d", v) else "2026-10-12"


def _bill(b):
    return re.sub(r"^0+(?=\d)", "", re.sub(r"\s+", "", str(b or "")).upper())


def _per_tab(amount_p, qty, packing):
    try:
        q = float(qty or 0)
        a = float(amount_p or 0)
    except (TypeError, ValueError):
        return None
    n = packn(packing) or 1
    if q <= 0 or a <= 0:
        return None
    return a / (q * n)


def _close(a, b, tol):
    return a is not None and b is not None and b > 0 and abs(a - b) / b <= tol


def _sp_names(sp, k20, cache):
    if k20 not in cache:
        try:
            cache[k20] = [str(r["name"]) for r in sp.q("SELECT DISTINCT name FROM sp_item WHERE k20=?", k20) if r["name"]]
        except Exception:                                     # noqa: BLE001
            cache[k20] = []
    return cache[k20]


def _full(sp, k20, name27, cache):
    """Marg's full item name for a bill line: the sp_item name of its key that the printed (27-letter) name starts; else the printed name."""
    n27 = nm(name27)
    names = _sp_names(sp, k20, cache)
    for n in names:
        if nm(n) == n27:
            return n
    for n in names:
        if nm(n).startswith(n27) or n27.startswith(nm(n)):
            return n
    return str(name27 or "").strip()


def learn_marg(con, sp, now, log=None):
    """kind 'marg' from the orders since order.track_since (see the head). Returns dict(sure, ask, upgraded)."""
    import stock_figure as SF                                 # noqa: PLC0415 -- lazy: stock_figure reads this module, not the reverse at import
    import stock_watch as SW                                  # noqa: PLC0415
    out = dict(sure=0, ask=0, upgraded=0)
    back = 2
    try:
        S = SW.settings(con)
        back = int(S["back_days"]) if S.get("back_days") is not None else 2
    except Exception:                                         # noqa: BLE001
        pass
    win = _setting_int(con, "names.window_days", WINDOW_DAYS_DEFAULT)
    cache = {}
    lines = con.execute("SELECT l.id, l.order_id, l.item, l.packs, l.pack_size, l.rate_p, o.vendor, o.created_at FROM purchase_order_line l "
                        "JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN ('sent','received') AND substr(o.created_at,1,10)>=? "
                        "AND COALESCE(l.billed_bill_no,'')='' ORDER BY o.created_at, l.id", (_since(con),)).fetchall()
    billed = con.execute("SELECT l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                         "WHERE COALESCE(l.billed_bill_no,'')<>''").fetchall()
    for lid, oid, item, packs, ps, rate_p, vendor, created in lines:
        ctx = SF._ctx(con, sp, None)
        if SF.carried(con, sp, dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=None), ctx):
            continue
        own = SW.supkey(vendor)
        try:
            od = dt.date.fromisoformat(str(created)[:10])
        except ValueError:
            continue
        lo, hi = (od - dt.timedelta(days=back)).isoformat(), (od + dt.timedelta(days=win)).isoformat()
        k = SF.key_of(sp, item, ctx)
        same_order = {SF.key_of(sp, r[0], ctx) for r in con.execute("SELECT item FROM purchase_order_line WHERE order_id=? AND id<>?", (oid, lid))}
        cands = {}
        for p in sp.q("SELECT supkey, bill, date, seq, name27, k20, packing, qty, free, amount_p FROM sp_purchase_line WHERE supkey=? AND direction='PURCHASE' "
                      "AND date>=? AND date<=? ORDER BY date, bill, seq", own, lo, hi):
            k2 = str(p["k20"] or "")
            if not k2 or k2 == k or k2 in same_order:
                continue
            full = _full(sp, k2, p["name27"], cache)
            if any(_bill(b[1]) == _bill(p["bill"]) and SW.supkey(b[2]) == own and SF.key_of(sp, b[0], ctx) == k2 for b in billed):
                continue                                      # that bill line answers another order line of its own item
            if pack_pair(item, full):
                cands.setdefault(k2, (p, full, "pack"))
            elif near_pair(item, full):
                cands.setdefault(k2, (p, full, "near"))
        if not cands:
            continue
        sure_ones = [c for c in cands.values() if c[2] == "pack"]
        for k2, (p, full, how) in sorted(cands.items()):
            new_pt = _per_tab(p["amount_p"], p["qty"], p["packing"])
            hists = []
            try:                                              # the ordered item's last three purchases (a price moves month to month)
                for h in sp.q("SELECT amount_p, qty, packing FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' AND date<=? AND qty>0 "
                              "ORDER BY date DESC, bill DESC LIMIT 3", k, str(p["date"])):
                    hists.append(_per_tab(h["amount_p"], h["qty"], h["packing"]))
            except Exception:                                 # noqa: BLE001
                hists = []
            hist = next((x for x in hists if _close(new_pt, x, PRICE_TOL)), hists[0] if hists else None)
            order_pt = (float(rate_p) / float(ps or 1)) if rate_p else None
            price_ok = any(_close(new_pt, x, PRICE_TOL) for x in hists) or _close(new_pt, order_pt, PRICE_TOL)
            own_pk = ""
            try:
                r0 = sp.q("SELECT packing FROM sp_item WHERE k20=? ORDER BY last_seen DESC LIMIT 1", k)
                own_pk = str(r0[0]["packing"] or "") if r0 else ""
            except Exception:                                 # noqa: BLE001
                own_pk = ""
            na, nb = packn(own_pk), packn(p["packing"])
            pack_ok = (nm(own_pk) == nm(p["packing"]) and bool(own_pk)) or (bool(na) and bool(nb) and na > 1 and nb > 1)
            state = "sure" if (how == "pack" and len(sure_ones) == 1 and len(cands) == 1 and price_ok and pack_ok) else "ask"
            why = dict(order=oid, line=lid, dealer=str(vendor), bill=str(p["bill"]), date=str(p["date"]), how=how, packing_old=own_pk, packing_new=str(p["packing"] or ""),
                       per_tab_new=round(new_pt / 100.0, 2) if new_pt else None, per_tab_old=round(hist / 100.0, 2) if hist else None,
                       per_tab_order=round(order_pt / 100.0, 2) if order_pt else None, kit=KIT)
            r = _put(con, "marg", "", full, item, state, why, now)
            if r:
                out["upgraded" if r == "upgraded" else state] += 1
                if log:
                    log("  marg %-5s %s = %s (%s, bill %s)" % (state, full, item, vendor, p["bill"]))
    return out


def _reading(acon, sid):
    r = acon.execute("SELECT data, at FROM claude_reading WHERE bill_id=? AND ok=1 ORDER BY at DESC LIMIT 1", (int(sid),)).fetchone()
    if not r or not r[0]:
        return None, None
    try:
        return json.loads(r[0]), r[1]
    except ValueError:
        return None, None


def pair_bill(reads, margs):
    """One bill: Claude's item lines [dict(name, qty, rate)] against Marg's lines [dict(name, qty, free, amount_p)] -> [(read, marg, score)] of
    the sure pairs (quantity, rate and name agree; one to one)."""
    cand = {}
    for i, r in enumerate(reads):
        try:
            rq = float(r.get("qty") or 0)
        except (TypeError, ValueError):
            continue
        if rq <= 0 or not str(r.get("name") or "").strip():
            continue
        for j, m in enumerate(margs):
            q, f = float(m.get("qty") or 0), float(m.get("free") or 0)
            if rq not in (q, q + f):
                continue
            try:
                rr = float(r.get("rate") or 0)
            except (TypeError, ValueError):
                rr = 0.0
            if rr > 0 and q > 0 and m.get("amount_p"):
                a = float(m["amount_p"]) / 100.0
                if not (_close(rr, a / q, RATE_TOL) or (q + f > 0 and _close(rr, a / (q + f), RATE_TOL))):
                    continue
            sc = loose(r["name"], m["name"])
            if sc > 0:
                cand.setdefault(i, []).append((j, sc))
    by_m = {}
    for i, js in cand.items():
        for j, sc in js:
            by_m.setdefault(j, []).append(i)
    out = []
    for i, js in cand.items():
        if len(js) != 1:
            continue
        j, sc = js[0]
        if len(by_m.get(j) or []) != 1:
            continue
        out.append((reads[i], margs[j], sc))
    return out


def learn_scan(con, sp, acon, now, log=None, only_new=True):
    """kind 'scan' from every linked pharmacy scan with a Claude reading (see the head). Returns dict(scans, sure)."""
    import stock_watch as SW                                  # noqa: PLC0415
    out = dict(scans=0, sure=0)
    if acon is None:
        return out
    seen = {int(r[0]): r[1] for r in con.execute("SELECT asset_bill_id, reading_at FROM med_name_seen")}
    cache = {}
    rows = con.execute("SELECT k.asset_bill_id, b.supplier_norm, b.supplier, b.bill_no FROM purchase_scan_link k JOIN purchase_bill b ON b.id=k.bill_id "
                       "ORDER BY k.asset_bill_id").fetchall()
    t = now.replace(microsecond=0).isoformat()
    for sid, sn, supplier, bno in rows:
        data, at = _reading(acon, sid)
        if not data:
            continue
        if only_new and seen.get(int(sid)) == at:
            continue
        sk = SW.supkey(supplier)
        ml = [p for p in sp.q("SELECT bill, date, seq, name27, k20, qty, free, amount_p FROM sp_purchase_line WHERE supkey=? AND direction='PURCHASE'", sk)
              if _bill(p["bill"]) == _bill(bno)]
        if ml:
            top = max(str(p["date"]) for p in ml)             # one bill number reused in another year: the newest
            ml = [p for p in ml if str(p["date"]) == top]
        margs = [dict(name=_full(sp, p["k20"], p["name27"], cache), qty=p["qty"], free=p["free"], amount_p=p["amount_p"]) for p in ml]
        reads = [x for x in (data.get("items") or []) if isinstance(x, dict)]
        n = 0
        for r, m, sc in pair_bill(reads, margs):
            if nm(r["name"]) == nm(m["name"]):
                continue
            st = _put(con, "scan", sn, str(r["name"]).strip(), m["name"], "sure",
                      dict(scan=int(sid), bill=str(bno), dealer=str(supplier), qty=r.get("qty"), score=round(sc, 2), kit=KIT), now)
            if st:
                n += 1
                if log:
                    log("  scan sure  %s: %s = %s" % (sn, r["name"], m["name"]))
        con.execute("INSERT OR REPLACE INTO med_name_seen (asset_bill_id, reading_at, pairs, at) VALUES (?,?,?,?)", (int(sid), at, n, t))
        out["scans"] += 1
        out["sure"] += n
    return out


def learn(con, now=None, sp=None, acon=None, log=None, force=False):
    """THE ONE WRITER: the 'marg' pass then the 'scan' pass; one commit. Fail-soft for its callers (they wrap it). Returns a dict.
    Runs at most once in names.learn_gap_min minutes (default 10; setting names.last_learn) unless force -- porders.detect_supplies runs on
    page views as well as the cron pass."""
    now = now or dt.datetime.now()
    ensure(con)
    if not force:
        try:
            r = con.execute("SELECT value FROM setting WHERE key='names.last_learn'").fetchone()
            last = dt.datetime.fromisoformat(str(r[0])) if r and r[0] else None
        except (sqlite3.Error, ValueError):
            last = None
        if last is not None and (now - last).total_seconds() < 60 * _setting_int(con, "names.learn_gap_min", 10) and now >= last:
            return dict(ok=True, skipped="recent")
    try:
        con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        con.execute("INSERT INTO setting (key, value, note) VALUES ('names.last_learn', ?, 'S628 med_names.learn -- the last run') "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (now.replace(microsecond=0).isoformat(),))
    except sqlite3.Error:
        pass
    own_sp = sp is None
    if own_sp:
        import stock_watch as SW                              # noqa: PLC0415
        sp = SW.Spine()
    if not getattr(sp, "ok", False):
        return dict(ok=False, why="spine unread")
    own_acon = acon is None
    if own_acon:
        try:
            import order_sheet as OS                          # noqa: PLC0415
            acon = OS._assets()
        except Exception:                                     # noqa: BLE001
            acon = None
    try:
        m = learn_marg(con, sp, now, log)
        s = learn_scan(con, sp, acon, now, log)
        con.commit()
        return dict(ok=True, marg=m, scan=s)
    finally:
        if own_acon and acon is not None:
            acon.close()
        if own_sp:
            try:
                sp.con.close()
            except Exception:                                 # noqa: BLE001
                pass
