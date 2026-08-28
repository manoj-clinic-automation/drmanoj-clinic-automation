#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""item_company.py — read Marg's LIST OF ITEMS export, and infer a stockist.

WHAT THE EXPORT ACTUALLY CARRIES, AND WHAT IT DOES NOT
    Marg's column is spelled `Compnay` and it holds the MANUFACTURER --
    CADILA, VINTECH, ACCUSURE, TYNOR. It is NOT the stockist. CADILA makes
    ACILOC 300; KEDAR PHARMACEUTICAL is who the shop buys it from. Treating
    one as the other would put a manufacturer's name on a purchase order.

WHY IT ANSWERS THE QUESTION ANYWAY
    Distributors carry particular companies. So: for every item whose stockist
    IS on record, note which company it belongs to. That builds company ->
    stockist from the shop's own buying history. An item with no purchase in
    the window still has a company, and that company usually has one stockist.

    KEDAR supplies 135 HI CURE items, so a HI CURE item with no purchase
    history is very probably KEDAR. That is a SUGGESTION with its evidence
    attached, never a fact -- the count of items behind it is carried so a
    person can see whether it rests on 135 or on 1.
"""
import collections, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "S206_SANJEEVNI_MARG_PURCHASE")))

ROW = re.compile(r"^\s*(\d+)\s+(.*\S)\s*$")
STRONG, WEAK = 10, 3          # items behind a suggestion


def find_export(archive):
    """The newest LIST OF ITEMS export, wherever it landed.

    It arrives in _REFUSED because signatures.json has no entry for this report
    type yet -- the router quarantines what it cannot identify rather than
    guessing, which is right. So look there too."""
    best = None
    from xlsx_sheet import open_sheet_any
    for p in glob.glob(os.path.join(archive, "**", "*.xls*"), recursive=True):
        if os.path.getsize(p) > 4_000_000:
            continue
        try:
            sh = open_sheet_any(p)
        except Exception:
            continue
        head = " ".join(str(sh.cell_value(r, c)) for r in range(0, 6)
                        for c in range(0, min(sh.ncols, 4))).upper()
        if "LIST OF ITEMS" in head and "COMPNAY" in " ".join(
                str(sh.cell_value(3, c)).upper() for c in range(min(sh.ncols, 6))):
            m = os.path.getmtime(p)
            if best is None or m > best[0]:
                best = (m, p, sh)
    return (best[1], best[2]) if best else (None, None)


def read_companies(sh):
    """{item: company}. The company can spill into a second column."""
    out = {}
    for r in range(4, sh.nrows):
        m = ROW.match(str(sh.cell_value(r, 0)).strip())
        if not m:
            continue
        name = m.group(2).strip()
        co = " ".join(x for x in (str(sh.cell_value(r, 2)).strip(),
                                  str(sh.cell_value(r, 3)).strip()) if x).strip()
        if name and co:
            out[name] = co
    return out


def company_to_stockist(companies, item_vendor):
    """company -> Counter(stockist), built only from purchases actually made."""
    cv = collections.defaultdict(collections.Counter)
    for item, vendors in item_vendor.items():
        co = companies.get(item)
        if not co:
            continue
        for v, n in vendors.items():
            cv[co][v] += n
    return cv


def suggest(item, companies, cv):
    """(company, stockist, items_behind_it, strength) — or Nones."""
    co = companies.get(item)
    if not co:
        return (None, None, 0, None)
    c = cv.get(co)
    if not c:
        return (co, None, 0, None)
    v, n = c.most_common(1)[0]
    return (co, v, n, "likely" if n >= STRONG else ("possible" if n >= WEAK else "weak"))


def selftest():
    n = [0]

    def ck(c, m):
        n[0] += 1
        if not c:
            print("check %d FAILED: %s" % (n[0], m)); raise AssertionError(m)

    comp = {"A": "HI CURE", "B": "HI CURE", "C": "KIRTI", "D": "ODDCO"}
    iv = {"A": collections.Counter({"KEDAR": 100}),
          "B": collections.Counter({"KEDAR": 35}),
          "C": collections.Counter({"SHIVAAZ": 2})}
    cv = company_to_stockist(comp, iv)
    ck(cv["HI CURE"]["KEDAR"] == 135, "evidence adds up across the company's items")
    co, v, cnt, s = suggest("D", comp, cv)
    ck(co == "ODDCO" and v is None, "a company nobody has bought from suggests nothing")
    comp["E"] = "HI CURE"
    co, v, cnt, s = suggest("E", comp, cv)
    ck(v == "KEDAR" and cnt == 135 and s == "likely",
       "135 items behind it is a LIKELY suggestion")
    comp["F"] = "KIRTI"
    co, v, cnt, s = suggest("F", comp, cv)
    ck(v == "SHIVAAZ" and s == "weak",
       "two items behind it is WEAK, and says so rather than looking confident")
    co, v, cnt, s = suggest("ZZZ", comp, cv)
    ck(co is None and v is None, "an item not in the export suggests nothing at all")
    print("ITEM_COMPANY SELFTEST PASSED - %d checks OK" % n[0])
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    A = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
    p, sh = find_export(A)
    print("export:", os.path.basename(p) if p else "NOT FOUND")
    if sh:
        c = read_companies(sh)
        print("items with a company: %d   distinct companies: %d" % (len(c), len(set(c.values()))))
