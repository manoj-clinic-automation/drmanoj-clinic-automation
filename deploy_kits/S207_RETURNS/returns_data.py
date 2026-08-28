#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""returns_data.py -- what should go back to the supplier, built from Marg's own exports.

WHY THE SCREEN IS THE EXPIRY LIST AND NOT A BLANK FORM
    Darpan should not have to remember what needs returning. Marg's expiry
    export already knows, and it has been right and unread for a long time:
    VINBACTUM DS expired in 2/2025 and twenty-five vials are still on the
    shelf eighteen months later. A blank form would never have found that.
    A list with a button on it does.

    So this builds the list: every item Marg has flagged near or past expiry
    that we STILL HOLD, with its batch, its expiry, what is actually on the
    shelf today, and who sold it to us -- so a return is one tap and one
    number instead of five fields typed from memory.

THREE HONEST LIMITS, ALL VISIBLE ON THE PAGE
    1. The expiry export is a NARROW window that somebody chose in Marg when
       they ran it. The newest one we hold carries seven items. It is not the
       whole near-expiry picture and this page never claims to be.
    2. The items most likely to be returned are old stock, and old stock is
       exactly what has no purchase this year -- so the supplier is least
       likely to be known where it is most needed. Where it is unknown the
       page says so rather than guessing.
    3. An item flagged months ago and no longer on the shelf may have been
       sold, returned, or thrown away without a record. It is shown as gone,
       not as done.

Standard library only.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "S206_SANJEEVNI_MARG_PURCHASE"))
import xlsx_sheet  # noqa: E402

ARCHIVE = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")

# Marg prints a whole-unit item as "4.0" and a strip-packed one as "27:9" IN THE
# SAME COLUMN. This is the only shape a quantity may take; anything else is a
# heading, a page footer, or a total, and is not stock.
QTY_RE = re.compile(r"^-?[\d.]+(:-?[\d.]+)?$")

# The closing-stock Description column is NOT the item name. It is the name,
# padded, with the PACK glued on the end -- "VINBACTUM DS   1*1". 334 of 378
# rows carry one. Matching the expiry list against the raw column therefore
# matches NOTHING, which is exactly what it did: 57 flagged items, 0 found on
# the shelf, and the answer looked like good news. The pack is worth keeping --
# it is the pack size the strips convention needs -- so it is split off, not
# thrown away.
DESC_RE = re.compile(r"^(.*?)\s{2,}(\d+\*[\d.]+|\d+)\.?\s*$")


def split_desc(desc):
    """'VINBACTUM DS   1*1' -> ('VINBACTUM DS', '1*1', 1)."""
    d = (desc or "").rstrip()
    m = DESC_RE.match(d)
    if not m:
        return d.strip(), "", 1
    name, pack = m.group(1).strip(), m.group(2)
    size = 1
    if "*" in pack:
        try:
            size = max(1, int(float(pack.split("*")[1])))
        except ValueError:
            size = 1
    return name, pack, size


def as_on_key(s):
    """dd-mm-yyyy as a sortable tuple.

    Compared as TEXT, "31-03-2026" sorts AFTER "27-08-2026" because "31" > "27".
    That very comparison nearly posted 974 items of April opening stock as
    today's shelf. Never compare these as strings.
    """
    t = (s or "").strip().replace("/", "-").split("-")
    if len(t) != 3:
        return (0, 0, 0)
    try:
        return (int(t[2]), int(t[1]), int(t[0]))
    except ValueError:
        return (0, 0, 0)


def expiry_key(e):
    """mm/yyyy -> (yyyy, mm). Blank sorts LAST, never first: an unknown expiry
    must not lead a list whose whole purpose is 'soonest first'."""
    m = re.match(r"^\s*(\d{1,2})\s*/\s*(\d{4})\s*$", e or "")
    return (int(m.group(2)), int(m.group(1))) if m else (9999, 99)


def is_zero(raw):
    """True when Marg's quantity string means nothing on the shelf."""
    s = str(raw or "").replace(" ", "")
    if not s:
        return True
    parts = s.split(":")
    try:
        return all(float(p or 0) == 0 for p in parts)
    except ValueError:
        return True


def _txt(sh, r, c):
    return str(sh.cell_value(r, c)).strip()


def read_expiry(archive=ARCHIVE):
    """Every expiry export we hold, the newest reading of each item+batch winning.

    Older exports are kept DELIBERATELY. An item on June's list and absent from
    August's has not necessarily been dealt with -- August's export was run over
    a narrower window. Dropping it would quietly lose VINBACTUM DS, which is the
    single item this page exists for.
    """
    seen = {}
    for p in sorted(glob.glob(os.path.join(archive, "STOCK_EXPIRY", "*", "*"))):
        try:
            sh = xlsx_sheet.open_sheet_any(p)
        except Exception:
            continue
        stamp = os.path.basename(p)
        for r in range(sh.nrows):
            d, b, e, q = (_txt(sh, r, 0), _txt(sh, r, 1), _txt(sh, r, 2), _txt(sh, r, 3))
            if not b or "/" not in e:
                continue
            m = re.match(r"^\s*\d+\s+(.*)$", d)
            if not m:
                continue
            # The expiry export pads and glues the pack on exactly as the
            # closing-stock export does, so it is split the same way. Miss this
            # and every one of the 57 flagged items fails to match the shelf --
            # and the page reports "nothing needs returning", which reads like
            # good news and is the most dangerous wrong answer available here.
            name, _pack, _size = split_desc(m.group(1))
            if not name or name.upper().startswith("DESCRIPTION"):
                continue
            batch = b[:-2] if b.endswith(".0") else b
            key = (name.upper(), batch.upper())
            if key not in seen or stamp > seen[key]["seen_in"]:
                seen[key] = {"item": name, "batch": batch, "expiry": e.strip(),
                             "flagged": q, "seen_in": stamp}
    return seen


def read_stock(archive=ARCHIVE):
    """Item -> what is on the shelf, from the LARGEST export for the NEWEST date.

    F-235, and it is no longer theoretical: on 28-Aug a category-filtered
    orthotics export carrying 82 items landed under the full-stock name, NEWER
    than the 377-item real one, with a byte-identical header. Newest-wins would
    have read 295 items as gone. Largest-for-the-newest-date is the only
    defence the file itself permits.

    Marg's own quantity string is kept verbatim. It is the only lossless form,
    and it is what the person holding the box actually reads.
    """
    best, best_key = None, None
    for p in glob.glob(os.path.join(archive, "STOCK_CLOSING", "*", "*")):
        try:
            sh = xlsx_sheet.open_sheet_any(p)
        except Exception:
            continue
        as_on = ""
        for r in range(0, min(10, sh.nrows)):
            m = re.search(r"AS ON\s+([0-9\-/]+)", _txt(sh, r, 0).upper())
            if m:
                as_on = m.group(1)
                break
        rows = {}
        for r in range(sh.nrows):
            desc = _txt(sh, r, 1)
            if not desc or desc.upper().startswith(("DESCRIPTION", "TOTAL", "S.NO")):
                continue
            name, pack, size = split_desc(desc)
            if not name:
                continue
            raw = _txt(sh, r, 2)
            # Marg writes "-" for nil. That is a real reading of the shelf, not
            # an unparseable row: recorded as zero, never skipped, because
            # "absent from the file" and "none left" mean different things when
            # the question is whether an expired batch is still here.
            if raw.strip() == "-":
                rows[name.upper()] = {"raw": "-", "unit": _txt(sh, r, 3), "pack": pack,
                                      "pack_size": size, "zero": True}
                continue
            if not QTY_RE.match(raw.replace(" ", "")):
                continue
            rows[name.upper()] = {"raw": raw, "unit": _txt(sh, r, 3), "pack": pack,
                                  "pack_size": size, "zero": is_zero(raw)}
        k = (as_on_key(as_on), len(rows))
        if rows and (best_key is None or k > best_key):
            best, best_key = {"as_on": as_on, "rows": rows,
                              "file": os.path.basename(p)}, k
    return best or {"as_on": "", "rows": {}, "file": ""}


def read_suppliers(archive=ARCHIVE):
    """item -> the vendors who have actually billed it to us.

    WHY THIS DELEGATES INSTEAD OF PARSING
        The first version of this function read the purchase export itself and
        returned "/ITEM WISE PURCHASE STATEMENT" -- the report's own title -- as
        a supplier for seven items. It did not raise anything; it produced a
        plausible-looking answer that was a page heading. That is the same fault
        that made TYRO BR 32.6 a day instead of 112.6, three times in one
        session. So this uses marg_purchase.read_purchase, which is the parser
        the reconciliation was built on and which has been measured against
        known totals.

    Purchase history only. A supplier is never inferred from an item's name -- a
    guess wearing a fact's clothes, and a wrong vendor on a return is worse than
    a blank one because nobody re-checks it.
    """
    sys.path.insert(0, os.path.join(HERE, "..", "S206_SANJEEVNI_MARG_PURCHASE"))
    import marg_purchase as MP
    sup = {}
    for p in sorted(glob.glob(os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*"))):
        try:
            rep = MP.read_purchase(p)
        except Exception:
            continue
        for r in rep.get("rows", []):
            it = (r.get("item") or "").strip()
            v = (r.get("supplier") or "").strip()
            if not it or not v:
                continue
            sup.setdefault(split_desc(it)[0].upper(), set()).add(v)
    return {k: sorted(v) for k, v in sup.items()}


def expiry_date_of(stamp):
    """The as-on date out of an expiry export's filename: ..._DEFAULT__2026-08-23__..."""
    m = re.search(r"__(\d{4}-\d{2}-\d{2})__", stamp or "")
    return m.group(1) if m else ""


def newest_expiry_date(archive=ARCHIVE):
    """The newest as-on DATE, not the newest filename.

    Two exports can share a date -- on 23-Aug there are two, one carrying the
    single expired item and one carrying the seven near-expiry ones. Taking the
    last filename kept the seven and silently dropped VINBACTUM DS, the one item
    the whole list exists for, from 'current' into 'stale'. A tie on the thing
    you are ranking by is not a tie-break opportunity; it means both belong.
    """
    ds = [expiry_date_of(os.path.basename(x))
          for x in glob.glob(os.path.join(archive, "STOCK_EXPIRY", "*", "*"))]
    ds = [d for d in ds if d]
    return max(ds) if ds else ""


def other_batches_bought(archive=ARCHIVE):
    """item -> every batch we have ever been billed. Delegated, never hand-parsed."""
    sys.path.insert(0, os.path.join(HERE, "..", "S206_SANJEEVNI_MARG_PURCHASE"))
    import marg_purchase as MP
    out = {}
    for p in sorted(glob.glob(os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*"))):
        try:
            rep = MP.read_purchase(p)
        except Exception:
            continue
        for r in rep.get("rows", []):
            it = split_desc((r.get("item") or "").strip())[0].upper()
            b = (r.get("batch") or "").strip()
            if it and b:
                out.setdefault(it, set()).add(b.upper())
    return out


def build(archive=ARCHIVE):
    """The return list -- and, just as important, what it does NOT establish.

    THE CORRECTION THAT FORCED THIS REWRITE (owner's challenge, 28-Aug-2026:
    "first check yr source of these expiry items, i have serious doubts")
        He was right, and the fault was mine.

        The STOCK side was never in doubt -- it is the 27-Aug export, 377 items,
        and the 31-03-2026 export sitting in the same archive was correctly
        passed over. But the EXPIRY side is a union of every expiry export we
        hold, and the oldest is dated 3-JUNE-2025. Twenty of the twenty-eight
        rows I reported as "still on the shelf" were flagged by an export three
        to fifteen months old.

        Worse, the closing-stock export carries NO BATCH COLUMN. So matching a
        flagged batch against it can only ever prove that THE ITEM still has
        stock -- never that THAT BATCH is still there. For anything we buy
        repeatedly, today's stock is a newer batch and the flagged one went out
        long ago. Twelve of the twenty have a different batch on a later
        purchase bill, which is near-proof of exactly that.

        So the list is now split three ways by the strength of its evidence, and
        only the first is presented as fact. A count that cannot distinguish
        "this batch is here" from "this item is here" must say so, because the
        difference is the entire question.
    """
    ex, st, sup = read_expiry(archive), read_stock(archive), read_suppliers(archive)
    newest = newest_expiry_date(archive)
    bought = other_batches_bought(archive)
    current, stale, gone = [], [], []
    for (_, _), v in sorted(ex.items(), key=lambda kv: expiry_key(kv[1]["expiry"])):
        s = st["rows"].get(v["item"].upper())
        others = {b for b in bought.get(v["item"].upper(), set())
                  if b != v["batch"].upper()}
        row = {"item": v["item"], "batch": v["batch"], "expiry": v["expiry"],
               "shelf": (s or {}).get("raw", ""), "unit": (s or {}).get("unit", ""),
               "vendors": sup.get(v["item"].upper(), []), "flagged": v["flagged"],
               "seen_in": v["seen_in"],
               "evidence": ("current" if expiry_date_of(v["seen_in"]) == newest
                            else "stale"),
               "newer_batches": sorted(others)}
        if not s or s["zero"]:
            row["evidence"] = "gone"
            gone.append(row)
        elif expiry_date_of(v["seen_in"]) == newest:
            current.append(row)
        else:
            stale.append(row)
    return {"as_on": st["as_on"], "stock_file": st["file"],
            "stock_items": len(st["rows"]), "newest_expiry_date": newest,
            "current": current, "stale": stale, "gone": gone,
            "held": current + stale,
            "expiry_files": sorted({v["seen_in"] for v in ex.values()})}
