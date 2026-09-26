#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s417.py -- kit S417_DAY_ONE_FIXES (F-636). Builds the seven patched files FROM THE LIVE BYTES with anchored edits (every
anchor exactly once, else it refuses) after checking each file's FROM pin:

  purchase_app.py                      stock_text(): the stock beside an order in the order's own unit -- '12 strips + 4' from the item's
                                       pack size, 'N pcs' for an orthotic, bottles / tubes / units where the packing is not a strip, the
                                       raw count WITH its unit word when the pack size is unknown; used on /page/orders (On hand) and
                                       /page/staff (Stock now); _staff_plan's lines carry it. The WhatsApp text is untouched.
  porders.py                           the Purchase orders screen's plan lines and the day's proposals carry stock_text; the orthotic
                                       lines (and the owner's full list) carry shelf_text in pieces.
  porders.html                         section 1 (shelf), section 4 (the day's proposals, the engine's plan) print those words.
  finance_ui/finance_approvals.html    the owner's Purchase orders table prints the shelf in pieces; the Yes Bank tile prints
                                       '− ₹X provisional NEFT (awaiting statement)' under the balance and 'incl. provisional' beside it.
  sanjeevni_approvals.py               provisional_nefts(): an owner-tapped / SMS-confirmed NEFT no statement has confirmed yet is taken
                                       off the tile's headline as its own line; gone the moment the statement carries it. Read-only.
  packs.py                             the card statements READ (statement date, period, card number) from the decrypted PDF; a card's
                                       month is the month its statement is dated in; the slot learns every card number (one card, two
                                       numbers after a re-issue); the locked original is 'duplicate of decrypted' or its month reads
                                       'decrypted copy not yet made'; an .xlsx in the Credit Card Statements root is the running Excel
                                       (all_txn), never 'which account?'.
  stmt_shelf.py                        the fetch files that .xlsx as all_txn.

Usage: make_s417.py --finance /root/finance --out DIR   (writes the seven files into DIR, flat)
"""
import hashlib
import io
import os
import sys

FROM = {"purchase_app.py": "cdd4e9c069bc8ab78160349a11a4a4c7", "porders.py": "c75fc91060d127fd05c56b6b81ad9b97",
        "porders.html": "5913e99302930d9fae24c42ac630f010", "finance_approvals.html": "eba564a425c1fc844f1d8d975a1d5eca",
        "sanjeevni_approvals.py": "c5b93455a69083a6b8d634014898bd30", "packs.py": "359403f792eaafad37d4eeac3f762641",
        "stmt_shelf.py": "94f456ce0a6f469ecd7d3f16ca1e874e"}
SRC = {"finance_approvals.html": os.path.join("finance_ui", "finance_approvals.html")}
ORDER = ("purchase_app.py", "porders.py", "porders.html", "finance_approvals.html", "sanjeevni_approvals.py", "packs.py", "stmt_shelf.py")


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    with io.open(path, "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:90]))
    return s.replace(old, new)


# ============================================================================ purchase_app.py
STOCK_FN = '''# S417 (F-636, 26-Sep-2026): the stock beside an order, in the order's own unit. The owner, first day on the order pages: "the orders page
# shows the stock in tablets and the order in strips -- confusing." Strips + loose from the item's pack size (the spine's reading,
# stock_snapshot.pack_size / packing -- the packing text decides when the pack size says 1); pieces for an orthotic; bottles / tubes / units
# where the packing is not a strip; a pack size nobody knows prints the raw count WITH its unit word, never a bare number. The WhatsApp
# text (the D-decided format) is untouched.
def _pack_from_packing(packing):
    m = re.match(r"^\\s*\\d+\\s*\\*\\s*(\\d+)", str(packing or ""))
    return int(m.group(1)) if (m and int(m.group(1)) > 1) else 0


def stock_text(units, pack_size, packing, ortho=False):
    """124 units of a 10-strip -> '12 strips + 4'; an orthotic -> '3 pcs'; a syrup -> '3 bottles'; unknown pack -> '5 units'."""
    try:
        n = int(round(float(units or 0)))
    except (TypeError, ValueError):
        n = 0
    neg, a = n < 0, abs(n)
    if ortho:
        return "%s%d pc%s" % ("\\u2212" if neg else "", a, "" if a == 1 else "s")
    try:
        size = int(pack_size or 0)
    except (TypeError, ValueError):
        size = 0
    if size <= 1:
        size = _pack_from_packing(packing)
    if size > 1:
        s, loose = divmod(a, size)
        txt = "%d strip%s" % (s, "" if s == 1 else "s") + ((" + %d" % loose) if loose else "")
        return ("\\u2212(%s)" % txt) if neg else txt
    return "%s%d %s" % ("\\u2212" if neg else "", a, _unit_word(packing, 1, a))


def _ortho_set(con):
    """S417: the orthotics of the section map (norm keys) -- their stock reads in pieces."""
    try:
        return {norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")}
    except Exception:                                               # noqa: BLE001
        return set()


def _stock_of(l, snap, orth):
    """S417: a plan line's stock in words (the snapshot gives the packing the line does not carry)."""
    s = snap.get(norm(l["item"])) or {}
    return stock_text(l.get("on_hand"), l.get("pack_size") or s.get("pack_size"), l.get("packing") or s.get("packing"), norm(l["item"]) in orth)


def _staff_qty(order_strips, unit):'''


def build_purchase(s):
    s = rep(s, "    vend_html, plan_json = [], []\n",
            "    vend_html, plan_json = [], []\n"
            "    _as_s417, snap_s417 = _latest_snapshot(con)               # S417: the stock in the order's own unit\n"
            "    orth_s417 = _ortho_set(con)\n", "page_orders snapshot")
    s = rep(s, '''            '<tr><td>%s%s</td><td class="n">%d</td><td class="n"><b>%d</b> %s</td><td class="n">%s</td><td class="n">%s</td>\'''',
            '''            '<tr><td>%s%s</td><td class="n">%s</td><td class="n"><b>%d</b> %s</td><td class="n">%s</td><td class="n">%s</td>\'''', "page_orders row format")
    s = rep(s, '''               l["on_hand"], l["order_strips"], _esc(_uw(l)), _esc(l["pack_size"]), _r(l["rate_p"]),''',
            '''               _esc(_stock_of(l, snap_s417, orth_s417)), l["order_strips"], _esc(_uw(l)), _esc(l["pack_size"]), _r(l["rate_p"]),''', "page_orders row values")
    s = rep(s, "def _staff_qty(order_strips, unit):", STOCK_FN, "stock_text")
    s = rep(s, "    plan = reorder_plan(con)\n    _, snap = _latest_snapshot(con)\n",
            "    plan = reorder_plan(con)\n    _, snap = _latest_snapshot(con)\n    orth = _ortho_set(con)                                      # S417\n", "_staff_plan ortho")
    s = rep(s, '''            lines.append(dict(item=l["item"], on_hand=l["on_hand"], qty=qty, unit=unit,''',
            '''            lines.append(dict(item=l["item"], on_hand=l["on_hand"], qty=qty, unit=unit,
                              stock_text=stock_text(l["on_hand"], l["pack_size"], s.get("packing"), norm(l["item"]) in orth),   # S417''', "_staff_plan stock_text")
    s = rep(s, '''        rows = "".join('<tr><td>%s</td><td class="n">%d</td><td class="n"><b>%d</b> %s</td></tr>'
                       % (_esc(l["item"]), l["on_hand"], l["qty"], _unit_word(l["packing"], l["pack_size"], l["qty"]))''',
            '''        rows = "".join('<tr><td>%s</td><td class="n">%s</td><td class="n"><b>%d</b> %s</td></tr>'
                       % (_esc(l["item"]), _esc(l.get("stock_text") or l["on_hand"]), l["qty"], _unit_word(l["packing"], l["pack_size"], l["qty"]))''', "page_staff row")
    return s


# ============================================================================ porders.py
PORDERS_HEAD = '''#  S417 (F-636, 26-Sep-2026): the stock beside an order reads in the order's own unit -- the plan lines and the day's proposals carry
#  stock_text ('12 strips + 4', '3 bottles', '5 units', from purchase_app.stock_text), the orthotic lines carry shelf_text in pieces.
#  Every figure stays as it was; the words are added beside it.
#
#  ONE SCREEN -- "Purchase orders" (the owner, 26-Sep-2026)'''

PORDERS_FN = '''def _pcs(n):
    """S417 (F-636): an orthotic's stock in pieces -- the unit it is ordered in."""
    try:
        return _pa().stock_text(n, 1, "", ortho=True)
    except Exception:                                         # noqa: BLE001
        return "%s pcs" % n


def _stock_texts_s417(con, d):
    """S417: each proposed line carries its stock in the order's own unit (strips + loose / bottles / units) for the screen."""
    try:
        pa = _pa()
        orth = pa._ortho_set(con)
        for p in (d or {}).get("proposals") or []:
            for l in p.get("lines") or []:
                if isinstance(l, dict) and "on_hand" in l:
                    l["stock_text"] = pa.stock_text(l.get("on_hand"), l.get("pack_size"), l.get("packing"), pa.norm(l.get("item") or "") in orth)
    except Exception:                                         # noqa: BLE001 -- the screen never waits for a word
        pass
    return d


def _day_s410(con):'''


def build_porders(s):
    s = rep(s, '#  ONE SCREEN -- "Purchase orders" (the owner, 26-Sep-2026)', PORDERS_HEAD, "porders header")
    s = rep(s, '''        lines = [dict(item=l["item"], on_hand=l["on_hand"], qty=l["qty"], unit=l["unit"], pack_size=l["pack_size"], packing=l["packing"], rate_p=l["rate_p"],''',
            '''        lines = [dict(item=l["item"], on_hand=l["on_hand"], stock_text=l.get("stock_text"), qty=l["qty"], unit=l["unit"], pack_size=l["pack_size"], packing=l["packing"], rate_p=l["rate_p"],''', "plan meds stock_text")
    s = rep(s, "def _day_s410(con):", PORDERS_FN, "stock texts fn")
    s = rep(s, "        return order_rules.day_state(con)\n", "        return _stock_texts_s417(con, order_rules.day_state(con))     # S417\n", "day_state words")
    s = rep(s, '''    lines_out = [dict(item=it["item"], short=it["short"], shelf=it["shelf"], marg=it["marg"],''',
            '''    lines_out = [dict(item=it["item"], short=it["short"], shelf=it["shelf"], shelf_text=_pcs(it["shelf"]), marg=it["marg"],''', "ortho shelf_text")
    s = rep(s, '''ret=int(round(it["ret"] + it["pool_ret"])), shelf=it["shelf"], marg=it["marg"],''',
            '''ret=int(round(it["ret"] + it["pool_ret"])), shelf=it["shelf"], shelf_text=_pcs(it["shelf"]), marg=it["marg"],''', "all rows shelf_text")
    return s


# ============================================================================ porders.html
def build_porders_html(s):
    s = rep(s, "<title>Purchase orders</title>\n",
            "<title>Purchase orders</title>\n<!-- S417_DAY_ONE_FIXES (26-Sep-2026, F-636): the stock beside an order in the order's own unit -- '12 strips + 4', "
            "'3 pcs', '3 bottles', '5 units' (stock_text / shelf_text from the API); the WhatsApp text is untouched. -->\n", "html comment")
    s = rep(s, """'<div class="muted">'+L("shelf")+' '+l.shelf+(l.approx""", """'<div class="muted">'+L("shelf")+' '+esc(l.shelf_text||l.shelf)+(l.approx""", "ortho shelf")
    s = rep(s, """m+='<table>'+p.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+l.on_hand+'</td>""",
            """m+='<table>'+p.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+esc(l.stock_text!=null?l.stock_text:l.on_hand)+'</td>""", "proposal stock")
    s = rep(s, """v.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+l.on_hand+'</td><td class="n"><b>'+l.qty""",
            """v.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+esc(l.stock_text!=null?l.stock_text:l.on_hand)+'</td><td class="n"><b>'+l.qty""", "plan stock")
    return s


# ============================================================================ finance_approvals.html
def build_approvals_html(s):
    s = rep(s, """'</td><td class="num">'+l.shelf+'</td><td class="num">'+(l.marg==null""",
            """'</td><td class="num">'+esc(l.shelf_text||l.shelf)+'</td><td class="num">'+(l.marg==null""", "owner ortho shelf in pieces")
    s = rep(s, """'<div class="balbox"><div class="ttl">Yes Bank Sanjeevni</div><div class="fig">₹'+esc(yb.holds||"0")+'</div>'+""",
            """'<div class="balbox"><div class="ttl">Yes Bank Sanjeevni</div><div class="fig">₹'+esc(yb.holds||"0")+(yb.incl_provisional?' <span class="mut" style="font-size:12px;font-weight:400">incl. provisional</span>':'')+'</div>'+""", "tile headline")
    s = rep(s, """          : 'no statement loaded yet')+'</div></div>'+""",
            """          : 'no statement loaded yet')+'</div>'+(yb.provisional||[]).map(function(p){return '<div class="how"><b>− ₹'+esc(p.amount)+' provisional NEFT (awaiting statement)</b> · '+esc(p.text||"")+'</div>'}).join("")+'</div>'+  /* S417 (F-636) */""", "tile provisional line")
    return s


# ============================================================================ sanjeevni_approvals.py
SA_HEAD = '''#  S417 (F-636, 26-Sep-2026): the Yes Bank tile takes a provisional supplier NEFT off its headline -- '− ₹X provisional NEFT (awaiting
#  statement)' as its own line, the headline marked 'incl. provisional' -- until the statement confirms it (S407), then the line goes and
#  nothing is counted twice. Read-only; no table. With no such NEFT the tile's answer is byte-identical.
#
#  v1.10 (S410, D626, 26-Sep-2026)'''

SA_FN = '''# ------------------------------------------------------------------ S417: a provisional NEFT on the Yes Bank tile (F-636)
def _neft_tol(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='neft.stmt_tolerance_p'").fetchone()
        return max(0, int(float(r[0]))) if (r and r[0] not in (None, "")) else 0
    except Exception:  # noqa: BLE001
        return 0


def provisional_nefts(con, yp=None):
    """S417 (F-636). The owner tapped 'NEFT done' for August and the Yes Bank tile did not move. A supplier NEFT that is PROVISIONAL --
    tapped by the owner, or seen by the bank SMS and confirmed by him (S405 / S407's purchase_neft_event) -- and that no statement has
    confirmed yet is taken off the tile as its own line. Confirmed means: S407's bank_line_id; or a NEFT debit of the same amount (within
    neft.stmt_tolerance_p) from 3 days before to 15 days after its date in the loaded statement; or a statement whose period already
    reaches its date (the debit is then inside the bank's own closing balance -- subtracting it again would count it twice).
    Read-only: nothing is written here."""
    if not _has(con, "purchase_neft_event"):
        return []
    yp = yp or yesbank_position(con)
    as_on = str(yp.get("as_on") or "")
    tol = _neft_tol(con)
    has_lines = _has(con, "bank_statement_line")
    out = []
    for r in con.execute("SELECT id, month, source, amount_p, sms_date, created_at FROM purchase_neft_event WHERE kind='provisional' "
                         "AND (source='owner' OR confirmed_by IS NOT NULL) AND bank_line_id IS NULL ORDER BY id").fetchall():
        d = str(r[4] or r[5] or "")[:10]
        try:
            d0 = dt.date.fromisoformat(d)
        except ValueError:
            continue
        amt = int(r[3] or 0)
        if amt <= 0 or (as_on and as_on >= d):
            continue
        lo, hi = (d0 - dt.timedelta(days=3)).isoformat(), (d0 + dt.timedelta(days=15)).isoformat()
        if has_lines and con.execute("SELECT 1 FROM bank_statement_line WHERE withdrawal_p BETWEEN ? AND ? AND UPPER(description) LIKE '%NEFT%' "
                                     "AND txn_date BETWEEN ? AND ? LIMIT 1", (amt - tol, amt + tol, lo, hi)).fetchone():
            continue
        try:
            mname = dt.date(int(str(r[1])[:4]), int(str(r[1])[5:7]), 1).strftime("%B %Y")
        except (TypeError, ValueError):
            mname = str(r[1] or "")
        out.append(dict(id=int(r[0]), month=r[1], amount_p=amt, amount=rs(amt), date=d, day=dmy(d),
                        text="%s purchases · NEFT %s · %s" % (mname, dmy(d), "you tapped NEFT done" if r[2] == "owner" else "the bank SMS, confirmed by you")))
    return out


def _yes_tile_s417(con, yp):
    """The Yes Bank tile's figures (S378) -- and, S417, the provisional NEFT line(s) with the headline net of them. With none, the very
    same dict as before (same keys, same order, same values)."""
    tile = dict(holds=rs(max(yp["holds_p"], 0)), base=rs(yp["base_p"]), as_on=(dmy(yp["as_on"]) if yp["as_on"] else None),
                added=rs(yp["added_p"]), taken=rs(yp["taken_p"]), anchored=yp["anchored"])
    try:
        prov = provisional_nefts(con, yp)
    except Exception:  # noqa: BLE001 -- the tile never waits for this
        prov = []
    if prov:
        p = sum(x["amount_p"] for x in prov)
        tile.update(holds=rs(max(yp["holds_p"] - p, 0)), incl_provisional=True, provisional=prov, provisional_total=rs(p),
                    before_provisional=rs(max(yp["holds_p"], 0)))
    return tile


def bank_view(con, ym):'''


def build_sa(s):
    s = rep(s, "#  v1.10 (S410, D626, 26-Sep-2026)", SA_HEAD, "sa header")
    s = rep(s, "def bank_view(con, ym):", SA_FN, "sa provisional fn")
    s = rep(s, '''                yesbank=dict(holds=rs(max(yp["holds_p"], 0)), base=rs(yp["base_p"]),
                             as_on=(dmy(yp["as_on"]) if yp["as_on"] else None),
                             added=rs(yp["added_p"]), taken=rs(yp["taken_p"]), anchored=yp["anchored"]),''',
            '''                yesbank=_yes_tile_s417(con, yp),                                                   # S417''', "sa tile dict")
    return s


# ============================================================================ packs.py
PACKS_DOC = '''real header period and a PRINTED closing (never the pipe .txt). No secret, no account number beyond a tail, anywhere in this file.

S417 (F-636, day one of the packs page, 26-Sep-2026): the CARD statements are READ -- the statement date, the billing period and the card
number from the decrypted PDF's own text (HDFC's two layouts, ICICI's one), never the 'linked savings account XX…' line that had given the
old identifier a bank account's tail. A card's month is the month its statement is DATED in. The slot learns every card number its
statements print (the ICICI Amazon card changed number in Feb 2026: both forms, one card). The password-locked original cannot be read; its
twin is the file of the SAME NAME in the card's Decrypted folder (the owner's script keeps the name): with a twin it is 'duplicate of
decrypted'; without one its month reads 'decrypted copy not yet made' on the pack row. An .xlsx in the Credit Card Statements root is the
running Excel (folder all_txn, pack row 4's attachment) and is never asked about.
"""'''

PACKS_FN = '''# ---------------------------------------------------------------- S417: the card statements, read (F-636)
_MON = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\.?"
_CD1 = r"(\\d{1,2}\\s+%s,?\\s+\\d{4})" % _MON          # 15 Aug, 2026        (HDFC)
_CD2 = r"(%s\\s+\\d{1,2},\\s*\\d{4})" % _MON            # August 12, 2026     (ICICI)
_CD3 = r"(\\d{2}[/-]\\d{2}[/-]\\d{4})"                  # 15/03/2025          (HDFC's older layout)
_CARD_SD = (r"(?i)statement\\s+date\\s*:?\\s*" + _CD1, r"(?i)statement\\s+date\\s*:?\\s*" + _CD3, r"(?i)statement\\s+date[^\\n]*\\n\\s*" + _CD2,
            r"(?i)statement\\s+date\\s*:?\\s*" + _CD2)
_CARD_PER = (r"(?i)billing\\s+period\\s*:?\\s*" + _CD1 + r"\\s*(?:-|–|to)\\s*" + _CD1, r"(?i)statement\\s+period\\s*:?\\s*" + _CD2 + r"\\s*(?:-|–|to)\\s*" + _CD2,
             r"(?i)(?:billing|statement)\\s+period\\s*:?\\s*" + _CD3 + r"\\s*(?:-|–|to)\\s*" + _CD3)
_CARD_NO = (re.compile(r"(?i)card\\s*(?:no\\.?|number)\\s*:?\\s*([0-9Xx*][0-9Xx* \\-]{6,24}?\\d{4})\\b"), re.compile(r"\\b[1-9]\\d{3}[Xx*]{6,10}(\\d{4})\\b"))


def _card_date(s):
    s = " ".join(str(s or "").replace(",", " ").replace(".", " ").split())
    for fmt in ("%d %b %Y", "%d %B %Y", "%B %d %Y", "%b %d %Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def card_read(text):
    """S417: a card statement's statement date, billing period and card number(s), from its own text. The period, when the statement
    does not print one (HDFC's older layout), is the month up to the statement date. Returns dict(statement_date, period_from,
    period_to, tails) -- dates ISO or None; tails the last four of every card number printed, in order, once each."""
    t = text or ""
    sd = pf = pt = None
    for rx in _CARD_SD:
        m = re.search(rx, t)
        if m and _card_date(m.group(1)):
            sd = _card_date(m.group(1))
            break
    for rx in _CARD_PER:
        m = re.search(rx, t)
        if m and _card_date(m.group(1)) and _card_date(m.group(2)):
            pf, pt = _card_date(m.group(1)), _card_date(m.group(2))
            break
    sd = sd or pt
    pt = pt or sd
    if sd and not pf:
        y, mo = (sd.year - 1, 12) if sd.month == 1 else (sd.year, sd.month - 1)
        last = (dt.date(sd.year, sd.month, 1) - dt.timedelta(days=1)).day
        pf = dt.date(y, mo, min(sd.day, last)) + dt.timedelta(days=1)
    tails = []
    for m in _CARD_NO[0].finditer(t):
        if m.group(1)[-4:] not in tails:
            tails.append(m.group(1)[-4:])
    for m in _CARD_NO[1].finditer(t):
        if m.group(1) not in tails:
            tails.append(m.group(1))
    iso = lambda d: d.isoformat() if d else None      # noqa: E731
    return dict(statement_date=iso(sd), period_from=iso(pf), period_to=iso(pt), tails=tails)


def _tailset(t):
    """S417: a slot may know several tails ('9012,9004' -- one card re-issued); a file's tail may carry several."""
    return {x for x in re.split(r"[^0-9]+", str(t or "")) if x}


def _running_excel(f):
    """S417: an .xlsx / .xls in the Credit Card Statements ROOT is the running Excel (All_Transactions), never a statement."""
    return f.get("folder") == "cards" and not (f.get("subfolder") or "") and str(f.get("name") or "").lower().endswith((".xlsx", ".xls"))


def _name_date(name):
    """S417: the date a card file's NAME starts with, less a day (the bank's mail comes the day after the statement) -- used only for a
    locked original that has no decrypted twin, to say which month waits for its decrypted copy. Never used to place a file."""
    m = re.match(r"^(\\d{4}-\\d{2}-\\d{2})", str(name or ""))
    try:
        return (dt.date.fromisoformat(m.group(1)) - dt.timedelta(days=1)).isoformat() if m else None
    except ValueError:
        return None


def _original_status(con, f, slot, card=None):
    """S417: a card folder's (password-locked) original. Its twin is the file of the same name in the same card's Decrypted folder; with a
    twin it is a duplicate and takes the twin's month, without one its month waits for the decrypted copy. Returns (read_status, matched)."""
    tw = con.execute("SELECT id, period_from, period_to FROM stmt_file WHERE folder='decrypted' AND id<>? AND LOWER(name)=LOWER(?) "
                     "AND (COALESCE(subfolder,'')=COALESCE(?,'') OR slot_id=?) ORDER BY id DESC LIMIT 1",
                     (f["id"], f["name"], f.get("subfolder"), slot["id"] if slot else -1)).fetchone()
    if tw:
        if tw[2]:
            con.execute("UPDATE stmt_file SET period_from=?, period_to=? WHERE id=?", (tw[1], tw[2], f["id"]))
        return DUP_OF_DECRYPTED, "file %d is the decrypted copy" % tw[0]
    sd = (card or {}).get("statement_date") or _name_date(f.get("name"))
    if sd:
        con.execute("UPDATE stmt_file SET period_to=?, period_from=COALESCE(period_from, ?) WHERE id=?", (sd, sd, f["id"]))
    return "locked original", NO_TWIN


def _mark_twin(con, f, slot, card):
    """S417: a decrypted card statement makes its locked original (same name, same card folder) a duplicate and gives it its month."""
    con.execute("UPDATE stmt_file SET read_status=?, matched_status=?, period_from=?, period_to=? WHERE folder='cards' AND id<>? AND LOWER(name)=LOWER(?) "
                "AND (COALESCE(subfolder,'')=COALESCE(?,'') OR slot_id=?)",
                (DUP_OF_DECRYPTED, "file %d is the decrypted copy" % f["id"], (card or {}).get("period_from"), (card or {}).get("period_to"),
                 f["id"], f["name"], f.get("subfolder"), slot["id"]))


def _learn_card_tails(con):
    """S417: every card slot learns the card numbers its decrypted statements print, the newest first ('9012,9004': one card, two numbers);
    a tail the owner set himself (his tap) is never overwritten."""
    for s in [dict(r) for r in con.execute("SELECT id, ident_tail, owner_set FROM stmt_slot WHERE kind='card'")]:
        if s["ident_tail"] and s["owner_set"] and not str(s["owner_set"]).startswith("learned"):
            continue
        seen, n = {}, 0
        for tail, pt in con.execute("SELECT tail, period_to FROM stmt_file WHERE slot_id=? AND folder='decrypted' AND read_status='read' "
                                    "AND tail IS NOT NULL AND tail<>''", (s["id"],)).fetchall():
            n += 1
            for t in [x.strip() for x in str(tail).split(",") if x.strip()]:
                if str(pt or "") >= seen.get(t, ""):
                    seen[t] = str(pt or "")
        if not seen:
            continue
        want = ",".join(sorted(seen, key=lambda t: (seen[t], t), reverse=True))
        if want != (s["ident_tail"] or ""):
            con.execute("UPDATE stmt_slot SET ident_tail=?, owner_set=? WHERE id=?", (want, "learned from the card statements (%d files) %s" % (n, _now()), s["id"]))


def place(con, ident):'''


def build_packs(s):
    s = rep(s, '''real header period and a PRINTED closing (never the pipe .txt). No secret, no account number beyond a tail, anywhere in this file.
"""''', PACKS_DOC, "packs doc")
    s = rep(s, 'DUP_OF_BRANCH = "duplicate of branch copy"\n',
            'DUP_OF_BRANCH = "duplicate of branch copy"\nDUP_OF_DECRYPTED = "duplicate of decrypted"                    # S417\nNO_TWIN = "decrypted copy not yet made"                        # S417\n', "packs consts")
    s = rep(s, "def place(con, ident):", PACKS_FN, "card reader")
    s = rep(s, '''        if s["ident_tail"] and s["ident_tail"] == ident["tail"] and (not ident["bank"] or s["bank"] == ident["bank"]):''',
            '''        if s["ident_tail"] and (_tailset(s["ident_tail"]) & _tailset(ident["tail"])) and (not ident["bank"] or s["bank"] == ident["bank"]):   # S417: sets''', "place by tail")
    s = rep(s, '''    if best["ident_tail"] and ident["tail"] and best["ident_tail"] != ident["tail"]:''',
            '''    if best["ident_tail"] and ident["tail"] and not (_tailset(best["ident_tail"]) & _tailset(ident["tail"])):''', "place tail mismatch")
    s = rep(s, '''        if f["folder"] == "all_txn":
            con.execute("UPDATE stmt_file SET read_status='n/a', matched_status='', identified_at=? WHERE id=?", (_now(), f["id"]))''',
            '''        if f["folder"] == "all_txn" or _running_excel(f):         # S417: an .xlsx in the Credit Card Statements root IS the running Excel
            con.execute("UPDATE stmt_file SET folder='all_txn', read_status='n/a', matched_status='', note=NULL, identified_at=? WHERE id=?", (_now(), f["id"]))''', "all_txn")
    s = rep(s, '''        if locked and not f.get("locked"):''',
            '''        if locked and not f.get("locked") and f["folder"] != "cards":      # S417: a card's locked original is never the unlock step's''', "cards not unlocked")
    s = rep(s, '''        ident = identify_text(text) if text else dict(bank="", kind="", tail="", period_from=None, period_to=None, up="", holder="")
''', '''        ident = identify_text(text) if text else dict(bank="", kind="", tail="", period_from=None, period_to=None, up="", holder="")
        card = card_read(text) if (text and (f["folder"] in ("cards", "decrypted") or ident.get("kind") == "card")) else None     # S417
        if card and card["statement_date"]:
            ident.update(kind="card", tail=",".join(card["tails"]), period_from=card["period_from"], period_to=card["period_to"])
''', "card ident")
    s = rep(s, '''            if f["folder"] == "cards":
                rs, ms = "locked original", ""
            else:
                rs, ms = read_file(con, f, slot)''',
            '''            if f["folder"] == "cards":
                rs, ms = _original_status(con, f, slot, card)                       # S417
            elif slot.get("kind") == "card":
                rs, ms = (("read", "statement dated %s" % _dmy(card["statement_date"])) if (card and card["statement_date"])
                          else ("n/a", "the statement date could not be read from the PDF"))
                _mark_twin(con, f, slot, card)
            else:
                rs, ms = read_file(con, f, slot)''', "card status")
    s = rep(s, '''    con.commit()
    if own:
        con.close()
    return out


def assign(con, file_id, slot_id, who):''', '''    _learn_card_tails(con)                                                 # S417
    con.commit()
    if own:
        con.close()
    return out


def assign(con, file_id, slot_id, who):''', "learn tails")
    s = rep(s, '''        full = [x for x in fs if x["period_from"] <= lo and x["period_to"] >= hi]   # S411: the month's statement covers the whole month
''', '''        full = [x for x in fs if x["period_from"] <= lo and x["period_to"] >= hi]   # S411: the month's statement covers the whole month
        if s["kind"] == "card":        # S417: a card's month is the month its statement is DATED in (the statement date = period_to)
            fs = [dict(r) for r in con.execute("SELECT * FROM stmt_file WHERE slot_id=? AND folder='decrypted' AND period_to BETWEEN ? AND ? "
                                               "ORDER BY period_to DESC, id DESC", (s["id"], lo, hi))]
            full = fs[:1]
''', "card month")
    s = rep(s, "        twin_missing = False\n",
            "        no_dec = bool(s[\"kind\"] == \"card\" and not f and con.execute(\"SELECT 1 FROM stmt_file WHERE slot_id=? AND folder='cards' AND matched_status=? \"\n"
            "                                                            \"AND period_to BETWEEN ? AND ? LIMIT 1\", (s[\"id\"], NO_TWIN, lo, hi)).fetchone())   # S417\n"
            "        twin_missing = False\n", "no decrypted")
    s = rep(s, '''        out.append(dict(slot=s["key"], slot_id=s["id"], words=s["ident_words"], label=s["holder_label"], bank=s["bank"], kind=s["kind"], tail=s["ident_tail"], sanjeevni=s["sanjeevni"],''',
            '''        out.append(dict(slot=s["key"], slot_id=s["id"], words=s["ident_words"], label=s["holder_label"], bank=s["bank"], kind=s["kind"], sanjeevni=s["sanjeevni"],
                        tail=(((s["ident_tail"] or "").replace(",", " / ") or None) if s["kind"] == "card" else s["ident_tail"]),   # S417: one card, every number''', "cell tail")
    s = rep(s, "                        twin_missing=twin_missing))\n", "                        twin_missing=twin_missing, no_decrypted=no_dec))\n", "cell no_decrypted")
    s = rep(s, '''        why_ = "" if f else "no decrypted statement on the shelf"''',
            '''        why_ = ("statement dated %s" % _dmy(f["period_to"])) if f else (NO_TWIN if c.get("no_decrypted") else "no decrypted statement on the shelf")   # S417''', "row 4 why")
    s = rep(s, '''            for r in con.execute("SELECT * FROM stmt_file WHERE slot_id IS NULL AND folder<>'all_txn' ORDER BY id DESC LIMIT 60")]''',
            '''            for r in con.execute("SELECT * FROM stmt_file WHERE slot_id IS NULL AND folder<>'all_txn' AND NOT (folder='cards' AND COALESCE(subfolder,'')='' "
                                 "AND LOWER(name) LIKE '%.xls%') ORDER BY id DESC LIMIT 60")]''', "unplaced no excel")
    s = rep(s, '''    icici = {r[0] for r in con.execute("SELECT ident_tail FROM stmt_slot WHERE bank='ICICI' AND ident_tail IS NOT NULL AND ident_tail<>''")}''',
            '''    icici = {r[0] for r in con.execute("SELECT ident_tail FROM stmt_slot WHERE bank='ICICI' AND kind<>'card' AND ident_tail IS NOT NULL AND ident_tail<>''")}   # S417''', "electricity slots")
    s = rep(s, '''    icici |= {r[0] for r in con.execute("SELECT f.tail FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE s.bank='ICICI' AND f.tail IS NOT NULL AND f.tail<>''")}''',
            '''    icici |= {r[0] for r in con.execute("SELECT f.tail FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE s.bank='ICICI' AND s.kind<>'card' AND f.tail IS NOT NULL AND f.tail<>''")}''', "electricity files")
    return s


# ============================================================================ stmt_shelf.py
SHELF_FN = '''def _folder_s417(label, sub, name):
    """S417 (F-636): an .xlsx / .xls in the Credit Card Statements ROOT is the running Excel (All_Transactions) -- folder all_txn, never
    a card statement waiting to be placed."""
    return "all_txn" if (label == "cards" and not sub and str(name or "").lower().endswith((".xlsx", ".xls"))) else label


def fetch(con):'''


def build_shelf(s):
    s = rep(s, '''                               packs.process_inbox() calls this under the venv python after each identification pass.
"""''', '''                               packs.process_inbox() calls this under the venv python after each identification pass.

S417 (F-636): an .xlsx in the Credit Card Statements root is recorded as the running Excel (folder all_txn), never as a card file.
"""''', "shelf doc")
    s = rep(s, "def fetch(con):", SHELF_FN, "shelf folder fn")
    s = rep(s, "                                                       label, sub[:80], sha(blob), time.strftime(\"%Y-%m-%dT%H:%M:%S\"), local))",
            "                                                       _folder_s417(label, sub, f[\"name\"]), sub[:80], sha(blob), time.strftime(\"%Y-%m-%dT%H:%M:%S\"), local))", "shelf insert")
    return s


BUILD = {"purchase_app.py": build_purchase, "porders.py": build_porders, "porders.html": build_porders_html,
         "finance_approvals.html": build_approvals_html, "sanjeevni_approvals.py": build_sa, "packs.py": build_packs, "stmt_shelf.py": build_shelf}


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance", "/root/finance"), args.get("--out")
    if not out:
        sys.exit("usage: make_s417.py --finance /root/finance --out DIR")
    os.makedirs(out, exist_ok=True)
    for name in ORDER:
        src = os.path.join(fin, SRC.get(name, name))
        new = BUILD[name](load(src, name)).encode("utf-8")
        with io.open(os.path.join(out, name), "wb") as fh:
            fh.write(new)
        print("built %-24s %s -> %s  (%d bytes)" % (name, FROM[name][:8], md5(new)[:8], len(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
