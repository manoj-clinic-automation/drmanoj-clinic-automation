#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  stock_statement.py  ·  v1.0  ·  kit S431_COUNT_STATEMENT  ·  Session 283 (Sanjeevni)
#
#  THE COUNT AS ONE STATEMENT, SECTION BY SECTION -- the owner, 27-Sep-2026 13:0x: "Better it be section-wise. Now share the
#  complete list of 6th Sept with Marg stock, physical stock and shortages, and the excess items removed and matched; and the
#  orthotics, not seen by me -- are its losses also done? I need orthotic losses to show separately at selling price. Give me
#  a link for what's ready." "All prices have been worked out, probably in the spine; and Darpan's sheet was well made also."
#
#  Sections from the owner's map (stock_item_section): Medicines · Consumables · Orthotics, each with its own totals; within a
#  section the lines in the order of the count sheet. Per line: Marg stock on the count day · physical (counted) · the confirmed
#  swap partner and the quantity taken out · shortage after swaps · excess after swaps · value at SELLING PRICE (short and excess
#  apart) · what became of it (medicines: the S427 close's group -- allowance / small real gap / old stock / consumption / owner's
#  use / big loss -- or back in store / sold after the count / swap; orthotics: Darpan's reason, open, voucher status).
#  Lines with no difference after swaps sit under "Matched -- N lines" per section, never dropped.
#
#  SELLING PRICE, one rule for every section: the spine's S.RATE fact as on the count day, else its MRP fact as on the count day,
#  else the S235 rule for is_ortho_priced items (last purchase rate / 0.70), else stock_rate / (1 - the section's margin), else
#  "no price -- name it". Each price carries its source tag. Every quantity through qty_words.
#
#  FREEZE (the S227 discipline): one tap writes a stock_statement row -- frozen JSON + md5 + PDF + XLSX, dated, who; the hub
#  links point at the frozen copy "as at <time>"; a later freeze is a new row. The page renders live.
#
#  Mounted the S418 way: stock_app imports this file and its routes delegate here. No stock_app import at module level.
# =============================================================================
import datetime as dt
import hashlib
import io
import json
import os
import re
import sqlite3

VERSION = "1.0"
KIT = "S431_COUNT_STATEMENT"
HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "stock_statement.html")
SPINE_DB = os.environ.get("SPINE_DB") or os.path.join(HERE, "spine", "spine.db")
SECTIONS = ("Medicines", "Consumables", "Orthotics")
DOCTORS = ("bhawna",)                                          # the doctor beside the owner; staff never
ORTHO_MARGIN = 0.30                                            # S235: the pricing rule for is_ortho_priced items

SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_statement (
  id INTEGER PRIMARY KEY,                  -- S431: one frozen statement of one count
  count_id INTEGER NOT NULL,
  made_at TEXT NOT NULL, made_by TEXT,
  md5 TEXT NOT NULL,                       -- of the frozen JSON
  data TEXT NOT NULL,                      -- the statement as built at that moment
  totals TEXT NOT NULL,                    -- JSON: the three sections' totals + overall
  pdf TEXT, xlsx TEXT                      -- file names under pad_uploads/statements/
);
CREATE INDEX IF NOT EXISTS idx_statement_count ON stock_statement(count_id, id);
"""


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file, loaded first by finance_app
    return stock_app


def _qwm():
    import qty_words                                          # noqa: PLC0415
    return qty_words


def qw(units, pack=1, packing="", name=""):
    return _qwm().words(units, packing=packing, pack=pack, name=name)


def rs(p):
    return _sa()._loss_rs(p) if p is not None else "-"


def ensure(con):
    con.executescript(SCHEMA) if not con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_statement'").fetchone() else None


def may_read(u):
    sa = _sa()
    return sa._may_decide(u) or ((u or {}).get("user") or "") in DOCTORS


# ------------------------------------------------------------------ the spine's prices (read-only)
def _k20(name):
    return re.sub(r"\s+", " ", str(name or "").strip())[:20].strip()


class Prices(object):
    """The spine's S.RATE / MRP facts as on the count day, per (k20) item; per strip for a strip item, per piece otherwise."""

    def __init__(self, as_on_iso, path=None):
        self.ok, self.con, self._alias, self._names, self._cache = False, None, {}, {}, {}
        self.as_on = as_on_iso
        p = path or SPINE_DB
        try:
            if os.path.exists(p):
                self.con = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
                self._alias = {r[0]: r[1] for r in self.con.execute("SELECT alias, k20 FROM sp_alias")}
                for r in self.con.execute("SELECT k20, name FROM sp_item"):
                    self._names.setdefault(r[0], []).append(r[1])
                self.ok = True
        except sqlite3.Error:
            self.ok = False

    def key(self, name):
        k = _k20(name)
        return self._alias.get(k, k)

    def fact(self, item, fact):
        """The latest non-zero value of a fact as on the count day (rupees, per strip / piece), or None."""
        if not self.ok:
            return None
        names = self._names.get(self.key(item)) or []
        if not names:
            return None
        ck = (self.key(item), fact)
        if ck not in self._cache:
            q = ",".join("?" * len(names))
            val = None
            for r in self.con.execute("SELECT value, as_on FROM sp_item_fact WHERE name IN (%s) AND fact=? AND as_on<=? ORDER BY as_on DESC" % q, names + [fact, self.as_on]):
                try:
                    v = float(r[0])
                except (TypeError, ValueError):
                    continue
                if v > 0:
                    val = v
                    break
            self._cache[ck] = val
        return self._cache[ck]


def price_for(con, item, pack, section, st, P, rates):
    """(paise per tab / piece, source tag) by the one rule; (None, None) when nothing prices it."""
    pack = max(1, int(pack or 1))
    for fact, tag in (("s_rate", "spine S.RATE"), ("mrp", "spine MRP")):
        v = P.fact(item, fact)
        if v:
            return int(round(v * 100 / pack)), tag
    rate = rates.get(item)
    if rate:
        try:
            import section_map                                # noqa: PLC0415
            ortho_priced = bool(section_map.is_ortho_priced(item))
        except Exception:                                     # noqa: BLE001
            ortho_priced = section == "Orthotics"
        if ortho_priced:
            return int(round(rate / (1.0 - ORTHO_MARGIN))), "rule 0.30"
        m = st.get("margin_ortho" if section == "Orthotics" else "margin_med", 0.20)
        return int(round(rate / max(0.05, 1.0 - float(m)))), "rate / margin"
    return None, None


# ------------------------------------------------------------------ the statement
def build(con, d):
    """The statement of one count, live. d = stock_app._pad_report_data(con, root)."""
    sa = _sa()
    root = d["count_id"]
    as_on = sa._dmy_to_iso(d.get("as_on") or "") or ""
    st = sa._stock_settings(con)
    P = Prices(as_on)
    rates = {r[0]: int(r[1]) for r in con.execute("SELECT item, rate_p FROM stock_rate") if r[1]}
    _r, fam, _R = sa._pad_family(con, root)
    q = ",".join("?" * len(fam))
    # the owner's map
    sec = {r[0]: r[1] for r in con.execute("SELECT item, section FROM stock_item_section")}
    try:
        import section_map                                    # noqa: PLC0415
        classify_word = section_map.classify
    except Exception:                                         # noqa: BLE001
        classify_word = lambda it: "Medicines"                # noqa: E731
    # the S427 desk's verdict per line (medicines and consumables), and the over lines
    became, over_items = {}, {}
    try:
        import loss_piles                                     # noqa: PLC0415
        lines, over, _s = loss_piles.classify(con, d)
        for l in lines:
            became[l["item"]] = l
        for l in over:
            over_items[l["item"]] = l
        GT = loss_piles.GROUP_TITLE
        PT = loss_piles.PILE_TITLE
    except Exception:                                         # noqa: BLE001
        GT, PT = {}, {}
    # the orthotic section: Darpan's reasons, the pending round, the renames
    ortho_lines, ortho_state, pending, rounds_by_item, ortho_open = {}, None, set(), {}, set()
    try:
        import stockmatch                                     # noqa: PLC0415
        ortho_state = stockmatch.section_state(con, d)
        for l in ortho_state["lines"]:
            ortho_lines[l["item"]] = l
        pending = set(ortho_state["vouchers"]["pending_items"])
        # still open: Darpan's (no answer yet) and the owner's (answered, still moving Marg without his word -- section_state's 'unsettled')
        ortho_darpan = {l["item"] for l in ortho_state["lines"] if l["open"] and not l["answered"]}
        ortho_owner = set(ortho_state.get("unsettled") or []) - ortho_darpan
        ortho_open = ortho_darpan | ortho_owner
    except Exception:                                         # noqa: BLE001
        ortho_state = None
    for r in con.execute("SELECT item, round_no FROM stock_voucher_line WHERE count_id=? ORDER BY round_no", (root,)):
        rounds_by_item.setdefault(r[0], []).append(int(r[1]))
    diffs = {x["item"]: x for x in d["differences"]}
    matched = {m["item"]: m for m in d.get("matched") or []}
    out_sections = {s: dict(key=s, title=s, lines=[], matched=[]) for s in SECTIONS}
    src_counts = {}
    for row in con.execute("SELECT item, packing, pack_size, marg_qty, counted_qty FROM stock_count_item WHERE count_id IN (%s) ORDER BY count_id, id" % q, tuple(fam)):
        item, packing, pack, marg_c, counted_c = row[0], row[1] or "", int(row[2] or 1), int(row[3] or 0), int(row[4] or 0)
        s = sec.get(item) or classify_word(item)
        if s not in out_sections:
            s = "Medicines"
        x = diffs.get(item)
        if x is not None:
            packing = x.get("packing") or packing
            pack = int(x.get("pack") or pack)
            marg = int(x["marg"])
            counted = int(x.get("counted_count_day", x["counted"]))
            d0 = int(x.get("diff_count_day", counted - marg))
            swapped = min(abs(d0), int(x.get("swapped") or 0)) if d0 else 0
            after = (d0 + swapped) if d0 < 0 else (d0 - swapped)
            swap_with = list(x.get("swap_with") or [])
        else:
            m = matched.get(item)
            marg = int(m["qty"]) if m else marg_c
            counted = marg if m else counted_c
            d0, swapped, after, swap_with = counted - marg, 0, counted - marg, []
        short = -after if after < 0 else 0
        over_ = after if after > 0 else 0
        price, src = price_for(con, item, pack, s, st, P, rates) if (short or over_) else (None, None)
        if short or over_:
            src_counts[src or "none"] = src_counts.get(src or "none", 0) + 1
        L = dict(item=item, packing=packing, pack=pack, section=s, marg=marg, counted=counted, marg_text=qw(marg, pack, packing, item), counted_text=qw(counted, pack, packing, item),
                 diff_day=d0, swapped=swapped, swap_with=swap_with, swap_text=(("%s with %s" % (qw(swapped, pack, packing, item), ", ".join(swap_with))) if swapped else ""),
                 short=short, over=over_, short_text=(qw(short, pack, packing, item) if short else ""), over_text=(qw(over_, pack, packing, item) if over_ else ""),
                 price_p=price, price_src=src, price_text=(("%s a %s" % (rs(price * pack if pack > 1 else price), "strip" if pack > 1 else "pc")) if price else "no price"),
                 short_p=(short * price if (price and short) else (0 if price else None)), over_p=(over_ * price if (price and over_) else (0 if price else None)),
                 became="", became_key="", open=False, voucher="")
        if s == "Orthotics":
            ol = ortho_lines.get(item)
            if ol:
                if ol.get("word"):
                    L["became"] = "the owner: %s" % ol["word"]
                elif ol.get("cause_en"):
                    L["became"] = "Darpan: %s" % ol["cause_en"]
                elif ol.get("open"):
                    L["became"] = "open -- Darpan's word awaited"
                elif ol.get("settled"):
                    L["became"] = "settled" + (" -- swap confirmed" if swapped and not after else "")
                L["became_key"] = "ortho"
            elif short or over_:
                L["became"] = "swap confirmed -- no loss" if (swapped and not after) else "open"
            L["open"] = item in ortho_open
            if item in rounds_by_item:
                L["voucher"] = "on voucher round %s" % ", ".join(str(r) for r in sorted(set(rounds_by_item[item])))
            elif item in pending:
                L["voucher"] = "not yet on a voucher"
        else:
            b = became.get(item)
            if b:
                if b["bucket"] == "written_off":
                    L["became"] = "written off -- %s" % GT.get(b["group"], b["group"] or "")
                    L["became_key"] = "wo:%s" % (b["group"] or "")
                elif b["bucket"] == "back":
                    L["became"] = b["why"].replace(" -- ", " — ")
                    L["became_key"] = "back"
                else:
                    L["became"] = "open -- %s" % PT.get(b["bucket"], b["bucket"])
                    L["became_key"] = "open"; L["open"] = True
            elif over_ or item in over_items:
                L["became"] = "excess -- Marg corrected by the vouchers, never a loss"
                L["became_key"] = "over"
            elif short:
                L["became"] = "swap confirmed -- no loss" if (swapped and not after) else "-"
            if item in rounds_by_item:
                L["voucher"] = "on voucher round %s" % ", ".join(str(r) for r in sorted(set(rounds_by_item[item])))
        if short or over_:
            out_sections[s]["lines"].append(L)
        else:
            L["became"] = L["became"] or ("swap confirmed -- no loss" if swapped else "matched")
            out_sections[s]["matched"].append(L)
    sections = []
    for s in SECTIONS:
        S = out_sections[s]
        ls = S["lines"]
        T = dict(lines=len(ls) + len(S["matched"]), differing=len(ls), matched=len(S["matched"]),
                 short_lines=sum(1 for l in ls if l["short"]), over_lines=sum(1 for l in ls if l["over"]),
                 short_p=sum(l["short_p"] or 0 for l in ls), over_p=sum(l["over_p"] or 0 for l in ls),
                 unpriced=sum(1 for l in ls if l["price_p"] is None), unpriced_items=[l["item"] for l in ls if l["price_p"] is None],
                 swaps=sum(1 for l in ls + S["matched"] if l["swapped"]), swapped_units=sum(l["swapped"] for l in ls + S["matched"]),
                 sources={})
        for l in ls:
            T["sources"][l["price_src"] or "none"] = T["sources"].get(l["price_src"] or "none", 0) + 1
        T["net_p"] = T["short_p"] - T["over_p"]
        S["totals"] = T
        if s == "Orthotics" and ortho_state:
            V = ortho_state["vouchers"]
            R_ = ortho_state["renames"] or {}
            S["block"] = dict(open_lines=len(ortho_darpan), open_items=sorted(ortho_darpan), await_owner=len(ortho_owner), await_owner_items=sorted(ortho_owner),
                              not_vouchered=V.get("pending", 0), not_vouchered_items=V.get("pending_items") or [],
                              renames_total=R_.get("total", 0), renames_unverified=(R_.get("total", 0) - R_.get("verified", 0)),
                              verdict=ortho_state.get("verdict_en", ""), closed=bool(ortho_state.get("closed")))
        else:
            S["block"] = None
        # the close's groups for this section (medicines / consumables)
        if s != "Orthotics":
            g = {}
            for l in ls:
                if l["became_key"].startswith("wo:"):
                    k = l["became_key"][3:]
                    g.setdefault(k, dict(key=k, title=GT.get(k, k), n=0, short_p=0))
                    g[k]["n"] += 1; g[k]["short_p"] += (l["short_p"] or 0)
            S["groups"] = [g[k] for k in sorted(g)]
            S["back"] = sum(1 for l in ls + S["matched"] if l["became_key"] == "back")   # a back line wholly swapped sits under Matched
            S["open"] = sum(1 for l in ls if l["open"])
        sections.append(S)
    # the close, as the desk counts it (S427 groups, at the desk's MRP)
    close = None
    try:
        wo = [l for l in became.values() if l["bucket"] == "written_off"]
        back = [l for l in became.values() if l["bucket"] == "back"]
        close = dict(written_off=len(wo), written_off_p=sum(l["mrp_p"] or 0 for l in wo), back=len(back), back_p=sum(l["mrp_day_p"] or 0 for l in back),
                     open=sum(1 for l in became.values() if l["bucket"] not in ("written_off", "back")),
                     groups={g: dict(n=sum(1 for l in wo if l["group"] == g), mrp_p=sum((l["mrp_p"] or 0) for l in wo if l["group"] == g)) for g in sorted({l["group"] for l in wo})})
        r = con.execute("SELECT at, by_user FROM stock_writeoff_run WHERE count_id=? ORDER BY id DESC LIMIT 1", (root,)).fetchone()
        close["at"], close["by"], close["at_text"] = (r[0], r[1], sa._r_stamp(r[0]) + " IST") if r else (None, None, "")
    except Exception:                                         # noqa: BLE001
        close = None
    overall = dict(lines=sum(S["totals"]["lines"] for S in sections), differing=sum(S["totals"]["differing"] for S in sections),
                   matched=sum(S["totals"]["matched"] for S in sections), short_p=sum(S["totals"]["short_p"] for S in sections),
                   over_p=sum(S["totals"]["over_p"] for S in sections), unpriced=sum(S["totals"]["unpriced"] for S in sections))
    overall["net_p"] = overall["short_p"] - overall["over_p"]
    return dict(kit=KIT, version=VERSION, count_id=root, day=d.get("day") or "", as_on=d.get("as_on") or "", as_on_iso=as_on, built_at=now_iso(),
                built_text=sa._r_stamp(now_iso()) + " IST", counted_by=d.get("counted_by") or "", entered_by=d.get("entered_by") or "",
                price_rule="the spine's S.RATE as on the count day, else its MRP, else the 0.30 rule for orthotic-priced items (last purchase rate / 0.70), else the last purchase rate / (1 - the section's margin)",
                spine_ok=P.ok, sections=sections, overall=overall, close=close, price_sources=src_counts,
                links=dict(page="/finance/stock/page/statement?count=%d" % root, json="/finance/stock/api/statement/%d" % root,
                           pdf="/finance/stock/api/statement/%d.pdf" % root, xlsx="/finance/stock/api/statement/%d.xlsx" % root,
                           freeze="/finance/stock/api/statement/%d/freeze" % root, hub="/finance/stock/page/hub?count=%d" % root,
                           report="/finance/stock/page/report?count=%d" % root))


# ------------------------------------------------------------------ the PDF (the sheet's style: portrait, a section a heading, totals first, then the lines)
def render_pdf(S):
    import pad_receipt as PR                                  # noqa: PLC0415 -- the estate's own stdlib writer, read-only use
    cid = S["count_id"]
    doc = PR._Doc("Stock count #%d - the count statement" % cid, "%s - %s" % (PR.CLINIC, PR.STORE), "COUNT #%d - STATEMENT" % cid)
    p = doc.pdf
    p.text(PR._L, doc.y - 15, "%s - %s" % (PR.CLINIC, PR.STORE), 14, bold=True)
    doc.y -= 21
    p.text(PR._L, doc.y - 13, "STOCK COUNT #%d OF %s - THE COUNT STATEMENT, SECTION BY SECTION" % (cid, S.get("day") or ""), 12, bold=True)
    doc.y -= 19
    p.line(PR._L, doc.y, PR._R, doc.y, 0.8)
    doc.y -= 6
    frozen = S.get("frozen")
    doc.line_text(("Frozen %s IST by %s - fingerprint %s." % (frozen["made_text"], frozen["made_by"], frozen["md5"][:8])) if frozen else ("Built %s (live)." % S["built_text"]), 8.5, gray=0.3)
    doc.line_text("Marg stock as on %s; counted by %s, entered by %s. Values at SELLING PRICE: %s." % (S.get("as_on") or "-", S["counted_by"] or "-", S["entered_by"] or "-", S["price_rule"]), 8, gray=0.35)
    O = S["overall"]
    doc.line_text("ALL SECTIONS: %d lines - %d differ, %d matched - short %s - excess %s - net %s%s" % (
        O["lines"], O["differing"], O["matched"], PR._rs(O["short_p"]), PR._rs(O["over_p"]), PR._rs(O["net_p"]), (" - %d line(s) without a price" % O["unpriced"]) if O["unpriced"] else ""), 10, bold=True)
    C = S.get("close")
    if C and C.get("at_text"):
        doc.line_text("The close of %s by %s: %d lines written off (%s at the desk's MRP), %d back in store, %d still open." % (C["at_text"], C["by"] or "-", C["written_off"], PR._rs(C["written_off_p"]), C["back"], C["open"]), 8.5, gray=0.25)
    cols = [("#", PR._L + 14, "r", 0), ("Item", PR._L + 18, "l", 150), ("Marg", PR._L + 214, "r", 0), ("Physical", PR._L + 268, "r", 0), ("Short", PR._L + 330, "r", 0),
            ("Excess", PR._L + 392, "r", 0), ("Short Rs", PR._L + 452, "r", 0), ("Excess Rs", PR._R, "r", 0)]
    sub = [("", PR._L + 18, "l", 495)]
    for sec in S["sections"]:
        T = sec["totals"]
        doc.heading("%s - %d lines (%d differ, %d matched)" % (sec["title"].upper(), T["lines"], T["differing"], T["matched"]))
        doc.kv("Short at selling price", "%s (%d line%s)" % (PR._rs(T["short_p"]), T["short_lines"], "" if T["short_lines"] == 1 else "s"), kw=170)
        doc.kv("Excess at selling price", "%s (%d line%s)" % (PR._rs(T["over_p"]), T["over_lines"], "" if T["over_lines"] == 1 else "s"), kw=170)
        doc.kv("Net", PR._rs(T["net_p"]), kw=170)
        if T["swaps"]:
            doc.kv("Confirmed swaps", "%d line%s" % (T["swaps"], "" if T["swaps"] == 1 else "s"), kw=170)
        if T["unpriced"]:
            doc.kv("Without a price", "%d: %s" % (T["unpriced"], ", ".join(T["unpriced_items"][:8]) + (" ..." if T["unpriced"] > 8 else "")), kw=170)
        B = sec.get("block")
        if B:
            doc.kv("Lines still open (Darpan)", "%d%s" % (B["open_lines"], (": " + ", ".join(B["open_items"][:6])) if B["open_items"] else ""), kw=170)
            doc.kv("Awaiting the owner's word", "%d%s" % (B["await_owner"], (": " + ", ".join(B["await_owner_items"][:6]) + (" ..." if B["await_owner"] > 6 else "")) if B["await_owner_items"] else ""), kw=170)
            doc.kv("Not yet on a voucher", "%d" % B["not_vouchered"], kw=170)
            doc.kv("Renames unverified", "%d of %d" % (B["renames_unverified"], B["renames_total"]), kw=170)
        if sec.get("groups"):
            doc.kv("The close's groups", "; ".join("%s %d (%s)" % (g["title"], g["n"], PR._rs(g["short_p"])) for g in sec["groups"]), kw=170)
        if sec["lines"]:
            doc.thead("%s - the lines that differ" % sec["title"], cols)
            for i, l in enumerate(sec["lines"], 1):
                doc.trow("%s - the lines that differ" % sec["title"], cols, [str(i), "%s%s" % (l["item"], (" (%s)" % l["packing"]) if l["packing"] else ""), l["marg_text"], l["counted_text"],
                                                                            l["short_text"] or "", l["over_text"] or "", PR._rs(l["short_p"]) if l["short"] else "", PR._rs(l["over_p"]) if l["over"] else ""], size=7.5)
                bits = []
                if l["swap_text"]:
                    bits.append("swap: " + l["swap_text"])
                if l["became"]:
                    bits.append(l["became"])
                if l["voucher"]:
                    bits.append(l["voucher"])
                bits.append(("price %s (%s)" % (l["price_text"], l["price_src"])) if l["price_p"] else "no price -- name it")
                doc.trow("%s - the lines that differ" % sec["title"], sub, ["    " + " - ".join(bits)], size=7)
        if sec["matched"]:
            doc.heading("%s - matched: %d lines (Marg = physical)" % (sec["title"], T["matched"]))
            mcols = [("#", PR._L + 14, "r", 0), ("Item", PR._L + 18, "l", 300), ("Marg = physical", PR._L + 420, "r", 0), ("Swap", PR._R, "r", 0)]
            doc.thead("%s - matched" % sec["title"], mcols)
            for i, l in enumerate(sec["matched"], 1):
                doc.trow("%s - matched" % sec["title"], mcols, [str(i), "%s%s" % (l["item"], (" (%s)" % l["packing"]) if l["packing"] else ""), l["marg_text"], l["swap_text"] or ""], size=7.5)
    return doc.finish("Stock count #%d - the count statement - %s%s" % (cid, KIT, (" - frozen %s IST" % frozen["made_text"]) if frozen else ""))


# ------------------------------------------------------------------ the XLSX (one sheet a section + Totals)
def render_xlsx(S):
    import padwriter                                          # noqa: PLC0415
    W = padwriter
    tot = W.Sheet()
    tot.text(1, 0, "STOCK COUNT #%d OF %s - THE COUNT STATEMENT" % (S["count_id"], S.get("day") or ""), W.TITLE)
    fz = S.get("frozen")
    tot.text(2, 0, ("Frozen %s IST by %s - fingerprint %s. " % (fz["made_text"], fz["made_by"], fz["md5"][:8]) if fz else "Live, built %s. " % S["built_text"]) + "Selling price: " + S["price_rule"], W.NOTE)
    heads = ["Section", "Lines", "Differ", "Matched", "Short lines", "Short Rs", "Excess lines", "Excess Rs", "Net Rs", "Without a price", "Confirmed swaps"]
    for i, h in enumerate(heads):
        tot.text(4, i, h, W.HEADER)
    r = 5
    for sec in S["sections"] + [dict(title="ALL", totals=dict(S["overall"], short_lines=sum(x["totals"]["short_lines"] for x in S["sections"]), over_lines=sum(x["totals"]["over_lines"] for x in S["sections"]), swaps=sum(x["totals"]["swaps"] for x in S["sections"])))]:
        T = sec["totals"]
        vals = [sec["title"], T["lines"], T["differing"], T["matched"], T["short_lines"], T["short_p"] / 100.0, T["over_lines"], T["over_p"] / 100.0, T["net_p"] / 100.0, T["unpriced"], T.get("swaps", 0)]
        for i, v in enumerate(vals):
            (tot.num if isinstance(v, (int, float)) else tot.text)(r, i, v, W.BOX)
        r += 1
    r += 1
    B = next((s.get("block") for s in S["sections"] if s.get("block")), None)
    if B:
        for k, v in (("Orthotics -- lines still open (Darpan)", B["open_lines"]), ("Orthotics -- awaiting the owner's word", B["await_owner"]), ("Orthotics -- not yet on a voucher", B["not_vouchered"]), ("Orthotics -- renames unverified", "%d of %d" % (B["renames_unverified"], B["renames_total"]))):
            tot.text(r, 0, k, W.BOLD); (tot.num if isinstance(v, int) else tot.text)(r, 1, v, W.BOX); r += 1
    tot.widths = {0: 34, 1: 8, 2: 8, 3: 9, 4: 11, 5: 13, 6: 12, 7: 13, 8: 12, 9: 14, 10: 14}
    sheets = [("Totals", tot)]
    heads = ["#", "Item", "Packing", "Marg", "Physical", "Marg (words)", "Physical (words)", "Swap partner", "Swapped", "Short", "Excess", "Price Rs (strip / pc)", "Price source", "Short Rs", "Excess Rs", "What became of it", "Voucher", "Matched?"]
    for sec in S["sections"]:
        sh = W.Sheet()
        sh.text(1, 0, "%s - stock count #%d of %s" % (sec["title"].upper(), S["count_id"], S.get("day") or ""), W.TITLE)
        T = sec["totals"]
        sh.text(2, 0, "%d lines - %d differ, %d matched - short Rs %.2f - excess Rs %.2f - net Rs %.2f%s" % (T["lines"], T["differing"], T["matched"], T["short_p"] / 100.0, T["over_p"] / 100.0, T["net_p"] / 100.0, (" - %d without a price" % T["unpriced"]) if T["unpriced"] else ""), W.NOTE)
        for i, h in enumerate(heads):
            sh.text(4, i, h, W.HEADER)
        r = 5
        for l in sec["lines"] + sec["matched"]:
            vals = [len(sec["lines"]) and (sec["lines"].index(l) + 1 if l in sec["lines"] else len(sec["lines"]) + sec["matched"].index(l) + 1) or (sec["matched"].index(l) + 1), l["item"], l["packing"], l["marg"], l["counted"], l["marg_text"], l["counted_text"],
                    ", ".join(l["swap_with"]), l["swapped"] or "", l["short"] or "", l["over"] or "", ((l["price_p"] * (l["pack"] if l["pack"] > 1 else 1)) / 100.0) if l["price_p"] else "",
                    l["price_src"] or ("" if not (l["short"] or l["over"]) else "no price"), (l["short_p"] / 100.0) if l["short"] and l["price_p"] else "", (l["over_p"] / 100.0) if l["over"] and l["price_p"] else "",
                    l["became"], l["voucher"], "matched" if not (l["short"] or l["over"]) else ""]
            for i, v in enumerate(vals):
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    sh.num(r, i, v, W.BOX)
                else:
                    sh.text(r, i, "" if v is None else str(v), W.BOX)
            r += 1
        sh.widths = {0: 5, 1: 30, 2: 8, 3: 7, 4: 8, 5: 18, 6: 18, 7: 26, 8: 8, 9: 7, 10: 7, 11: 12, 12: 13, 13: 11, 14: 11, 15: 46, 16: 20, 17: 9}
        sh.freeze = "A5"
        sheets.append((sec["title"], sh))
    return W.workbook_bytes_multi(sheets)


# ------------------------------------------------------------------ freeze (the S227 discipline)
def _dir(con):
    d = os.path.join(_sa()._pad_archive_dir(con), "statements")
    os.makedirs(d, exist_ok=True)
    return d


def frozen_row(con, sid, with_data=False):
    ensure(con)
    r = con.execute("SELECT id, count_id, made_at, made_by, md5, totals, pdf, xlsx%s FROM stock_statement WHERE id=?" % (", data" if with_data else ""), (int(sid),)).fetchone()
    if not r:
        return None
    out = dict(id=r[0], count_id=r[1], made_at=r[2], made_text=_sa()._r_stamp(r[2]), made_by=r[3] or "", md5=r[4], totals=json.loads(r[5] or "{}"), pdf=r[6], xlsx=r[7],
               links=dict(pdf="/finance/stock/api/statement/frozen/%d.pdf" % r[0], xlsx="/finance/stock/api/statement/frozen/%d.xlsx" % r[0], json="/finance/stock/api/statement/frozen/%d.json" % r[0]))
    if with_data:
        out["data"] = json.loads(r[8])
    return out


def frozen_list(con, cid):
    ensure(con)
    return [frozen_row(con, r[0]) for r in con.execute("SELECT id FROM stock_statement WHERE count_id=? ORDER BY id DESC", (int(cid),))]


def frozen_latest_links(con, cid):
    rows = frozen_list(con, cid)
    if not rows:
        return None
    f = rows[0]
    return dict(id=f["id"], as_at=f["made_text"] + " IST", by=f["made_by"], pdf=f["links"]["pdf"], xlsx=f["links"]["xlsx"], n=len(rows))


def freeze(con, d, who):
    """One tap: the statement as it stands -> a row (JSON + md5), its PDF and XLSX kept beside the database."""
    ensure(con)
    S = build(con, d)
    frozen_json = json.dumps(S, sort_keys=True, separators=(",", ":"), default=str)
    md5 = hashlib.md5(frozen_json.encode("utf-8")).hexdigest()
    ts = now_iso()
    cur = con.execute("INSERT INTO stock_statement (count_id, made_at, made_by, md5, data, totals) VALUES (?,?,?,?,?,?)",
                      (S["count_id"], ts, who or "", md5, frozen_json, json.dumps(dict(overall=S["overall"], sections={s["key"]: s["totals"] for s in S["sections"]}, block=next((s.get("block") for s in S["sections"] if s.get("block")), None)), default=str)))
    sid = int(cur.lastrowid)
    S["frozen"] = dict(id=sid, made_at=ts, made_text=_sa()._r_stamp(ts), made_by=who or "", md5=md5)
    pdf_name, xlsx_name = "%s.pdf" % md5, "%s.xlsx" % md5
    try:
        d_ = _dir(con)
        with io.open(os.path.join(d_, pdf_name), "wb") as fh:
            fh.write(render_pdf(S))
        with io.open(os.path.join(d_, xlsx_name), "wb") as fh:
            fh.write(render_xlsx(S))
        con.execute("UPDATE stock_statement SET pdf=?, xlsx=? WHERE id=?", (pdf_name, xlsx_name, sid))
    except (IOError, OSError):
        pass
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("stock_statement", sid, "freeze", None, json.dumps(dict(count_id=S["count_id"], md5=md5, lines=S["overall"]["lines"], short_p=S["overall"]["short_p"], over_p=S["overall"]["over_p"],
                                                                              text="statement of count #%d frozen: %d lines, short %s, excess %s" % (S["count_id"], S["overall"]["lines"], rs(S["overall"]["short_p"]), rs(S["overall"]["over_p"])))), who or "", ts))
    except sqlite3.Error:
        pass
    con.commit()
    return frozen_row(con, sid)


def frozen_file(con, sid, kind):
    """The kept PDF / XLSX of a frozen statement -- from disk, else rebuilt from the frozen JSON and kept now."""
    f = frozen_row(con, sid, with_data=True)
    if not f:
        return None, None
    name = f.get(kind) or ("%s.%s" % (f["md5"], kind))
    path = os.path.join(_dir(con), name)
    if os.path.exists(path):
        with io.open(path, "rb") as fh:
            return fh.read(), f
    S = f["data"]
    S["frozen"] = dict(id=f["id"], made_at=f["made_at"], made_text=f["made_text"], made_by=f["made_by"], md5=f["md5"])
    data = render_pdf(S) if kind == "pdf" else render_xlsx(S)
    try:
        with io.open(path, "wb") as fh:
            fh.write(data)
        con.execute("UPDATE stock_statement SET %s=? WHERE id=?" % kind, (name, f["id"]))
        con.commit()
    except (IOError, OSError, sqlite3.Error):
        pass
    return data, f
