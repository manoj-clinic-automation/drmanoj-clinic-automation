#!/usr/bin/python3
"""
padreader.py -- read the STOCK COUNT PAD without needing anything installed.

WHY IT IS WRITTEN THIS WAY

  * STDLIB ONLY. This runs on the VPS beside stock_app.py. openpyxl may or may
    not be in that venv, and a stock count is not the moment to find out. An
    .xlsx is a zip of XML; zipfile and ElementTree are enough.

  * IT DOES NOT TRUST THE TOTAL COLUMN. That column is a formula. A formula
    written by a program carries NO cached value until something recalculates
    it, so a pad that was filled and saved by one tool and not another can hand
    back an empty total over two perfectly good numbers. The total is computed
    here from STRIPS and LOOSE and the pack size -- the same arithmetic the
    counting page does. A literal number typed straight into the total column is
    honoured too, but only when strips and loose are both empty.

  * IT NEVER GUESSES A NAME. A row whose item does not match the shop's list is
    returned as unmatched, with its row number, for a person to look at. Half a
    count silently dropped is worse than a count refused.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col(ref):
    """'BD12' -> 55 (zero-based column index)."""
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return n - 1


def _row(ref):
    m = re.search(r"(\d+)$", ref or "")
    return int(m.group(1)) if m else 0


def _shared(z):
    try:
        x = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in x.findall(NS + "si"):
        out.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return out


def _sheet_paths(z):
    """Every sheet, in the workbook's own tab order."""
    out = []
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        tgt = {}
        for rel in rels:
            t = (rel.get("Target") or "").lstrip("/")
            tgt[rel.get("Id")] = t if t.startswith("xl/") else ("xl/" + t)
        for sh in wb.iter(NS + "sheet"):
            rid = None
            for k, v in sh.attrib.items():
                if k.endswith("}id"):
                    rid = v
            if rid in tgt:
                out.append((sh.get("name") or "", tgt[rid]))
    except Exception:
        pass
    if not out:
        for n in sorted(z.namelist()):
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"):
                out.append((n, n))
    if not out:
        raise ValueError("no worksheet found in this file")
    return out


def _grid_of(x, ss):
    g = {}
    for c in x.iter(NS + "c"):
        ref = c.get("r") or ""
        t = c.get("t")
        v = c.find(NS + "v")
        if t == "inlineStr":
            isn = c.find(NS + "is")
            txt = "".join(e.text or "" for e in isn.iter(NS + "t")) if isn is not None else ""
            g[(_row(ref), _col(ref))] = txt
            continue
        if v is None or v.text is None:
            continue
        raw = v.text
        if t == "s":
            try:
                g[(_row(ref), _col(ref))] = ss[int(raw)]
            except Exception:
                pass
        elif t == "str" or t == "e":
            g[(_row(ref), _col(ref))] = raw          # a formula's cached text
        else:
            try:
                g[(_row(ref), _col(ref))] = float(raw)
            except ValueError:
                g[(_row(ref), _col(ref))] = raw
    return g


def grids(data):
    """[(sheet name, {(row, col): value})] for every sheet, in tab order."""
    z = zipfile.ZipFile(data)
    try:
        ss = _shared(z)
        out = []
        for name, path in _sheet_paths(z):
            try:
                out.append((name, _grid_of(ET.fromstring(z.read(path)), ss)))
            except Exception:
                continue
    finally:
        z.close()
    return out


def grid(data):
    """The first sheet only -- kept for callers that want just that."""
    return grids(data)[0][1]


def _num(v):
    """A number, or None. Blank is None -- never zero: 'nothing written' and
    'counted zero' are different answers and must never be confused."""
    if v is None:
        return None
    if isinstance(v, float):
        return v
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


WANT = {"item": ("ITEM",), "packing": ("PACKING",), "pack": ("PACK SIZE", "PACKSIZE"),
        "strips": ("STRIPS", "STRIP"), "loose": ("LOOSE", "TABLETS", "PIECES"),
        "total": ("TOTAL UNITS", "TOTAL"), "remarks": ("REMARKS", "REMARK", "NOTE")}


def _find_header(g, maxr):
    for r in range(1, min(maxr, 40) + 1):
        seen = {}
        for (rr, cc), v in g.items():
            if rr != r or not isinstance(v, str):
                continue
            up = " ".join(v.upper().split())
            for key, names in WANT.items():
                if up in names and key not in seen:
                    seen[key] = cc
        if "item" in seen and ("strips" in seen or "loose" in seen or "total" in seen):
            return r, seen
    return None, {}


def read_pad(data):
    """-> {'sheets':[names read], 'rows':[...], 'problems':[...], 'part_of':n}

    EVERY sheet that carries a fill-in table is read -- the pad has one, the
    result workbook has two (NOT COUNTED and SENT BACK TO FIX) -- and their rows
    are joined. A sheet without the header (SUMMARY, DIFFERENCES, MATCHED) is
    skipped, but its text is still searched for the PART OF COUNT line.

    Every row that carries an item name comes back, whether or not anything was
    written against it: a blank is an item NOT COUNTED, which the report has to
    be able to name. A sheet's table ends at its first blank row."""
    all_g = grids(data)
    if not all_g or not any(g for _, g in all_g):
        raise ValueError("this file has no readable cells")

    part_of = None
    for _, g in all_g:
        for (rr, cc), v in g.items():
            if isinstance(v, str):
                m = re.search(r"PART OF COUNT\s*#\s*(\d+)", v.upper())
                if m:
                    part_of = int(m.group(1))
                    break
        if part_of:
            break

    rows, problems, sheets_read = [], [], []
    for name, g in all_g:
        if not g:
            continue
        maxr = max(r for r, _ in g)
        hdr, cols = _find_header(g, maxr)
        if hdr is None:
            continue
        sheets_read.append(name)
        started = False
        for r in range(hdr + 1, maxr + 1):
            nm_v = g.get((r, cols["item"]))
            blank = not (isinstance(nm_v, str) and nm_v.strip())
            if blank:
                if started:
                    break
                continue
            started = True
            nm = " ".join(nm_v.split())
            if nm.upper() in ("ITEMS WITH A FIGURE ENTERED", "TOTAL UNITS COUNTED"):
                continue
            ps = _num(g.get((r, cols.get("pack", -1))))
            st = _num(g.get((r, cols.get("strips", -1))))
            lo = _num(g.get((r, cols.get("loose", -1))))
            tl = _num(g.get((r, cols.get("total", -1))))
            rem = g.get((r, cols.get("remarks", -1)))
            rem = str(rem).strip() if isinstance(rem, str) else None
            counted, how = None, None
            if st is not None or lo is not None:
                # With no PACK SIZE column the total cannot be settled here; the
                # server settles it from the shop's own pack size. Strips and
                # loose are handed on as written.
                counted = ((st or 0) * int(ps) + (lo or 0)) if ps else None
                how = "strips+loose"
            elif tl is not None:
                counted = tl
                how = "total typed in"
            if counted is not None:
                if counted != int(counted):
                    problems.append((r, nm, "the figure is not a whole number: %s" % counted, name))
                    counted, st, lo = None, None, None
                elif counted < 0:
                    problems.append((r, nm, "a negative count: %s" % int(counted), name))
                    counted, st, lo = None, None, None
            if (st is not None and (st < 0 or st != int(st))) or \
                    (lo is not None and (lo < 0 or lo != int(lo))):
                problems.append((r, nm, "strips or loose is negative or not a whole number", name))
                counted, st, lo = None, None, None
            rows.append({"row": r, "sheet": name, "item": nm,
                         "pack_size": int(ps) if ps else None,
                         "strips": None if st is None else int(st),
                         "loose": None if lo is None else int(lo),
                         "counted": None if counted is None else int(counted),
                         "how": how, "remarks": rem})
    if not sheets_read:
        raise ValueError("could not find the header row -- is this the stock count pad?")
    return {"sheets": sheets_read, "rows": rows, "problems": problems, "part_of": part_of}
