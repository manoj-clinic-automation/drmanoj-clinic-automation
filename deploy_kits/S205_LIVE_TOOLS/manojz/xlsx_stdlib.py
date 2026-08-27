#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx_stdlib.py  --  S201.  Read .xlsx with nothing but the standard library.

WHY THIS EXISTS
    The pipeline read .xlsx through xlrd 1.2.0, which lost .xlsx support at
    Python 3.9 (ElementTree.getiterator was removed). manojz reads .xlsx today
    only because its Python predates that. The day it is upgraded, every .xlsx
    Marg export becomes "not a readable .xls" -- and it will look like a
    refusal, not a breakage. Marg does emit .xlsx.

    The obvious fix is openpyxl. But that means pip on two machines, one of
    which has a bundled interpreter with no packages at all and no reliable way
    to add them. A dependency that must be installed on every clinic PC is a
    dependency that will be missing on one of them.

    An .xlsx is a zip of XML. The standard library can open a zip and parse
    XML. So this reads it directly and the dependency disappears -- no pip, no
    version to pin, works on any Python 3.

    Deliberately NOT a general xlsx library. It reads cell values as text and
    numbers, which is all the Marg parsers ever ask for. No styles, no dates as
    datetimes, no formulas beyond their cached result.

Interface matches the small part of xlrd's Sheet the router uses:
    sh.nrows, sh.ncols, sh.cell_value(row, col), sh.name
"""

import re
import zipfile
import xml.etree.ElementTree as ET

_CELL_RE = re.compile(r"([A-Z]+)(\d+)")


def _local(tag):
    """Strip the namespace: '{...main}row' -> 'row'."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _col_index(ref):
    """'A1' -> 0, 'B7' -> 1, 'AA3' -> 26."""
    m = _CELL_RE.match(ref or "")
    if not m:
        return None, None
    letters, digits = m.group(1), m.group(2)
    col = 0
    for ch in letters:
        col = col * 26 + (ord(ch) - 64)
    return col - 1, int(digits) - 1


def _text_of(node):
    """All text under a node, in document order. Shared strings can be split
    across several <r><t> runs when part of the string is formatted."""
    parts = []
    for el in node.iter():
        if _local(el.tag) == "t" and el.text:
            parts.append(el.text)
    return "".join(parts)


class Sheet(object):
    def __init__(self, name, grid, nrows, ncols):
        self.name = name
        self._grid = grid
        self.nrows = nrows
        self.ncols = ncols

    def cell_value(self, r, c):
        return self._grid.get((r, c), "")

    def row_values(self, r):
        return [self.cell_value(r, c) for c in range(self.ncols)]


class Book(object):
    def __init__(self, sheets):
        self._sheets = sheets

    def sheet_by_index(self, i):
        return self._sheets[i]

    def sheet_names(self):
        return [s.name for s in self._sheets]

    @property
    def nsheets(self):
        return len(self._sheets)


def _shared_strings(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [_text_of(si) for si in root if _local(si.tag) == "si"]


def _first_sheet_target(z):
    """The first sheet in the workbook's own order, resolved through rels.

    Falls back to sheet1.xml, and then to whatever worksheet exists, because a
    file that opens in Excel must not fail here over a rels quirk.
    """
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        wb = rels = None

    if wb is not None and rels is not None:
        rid_to_target = {}
        for rel in rels:
            rid_to_target[rel.get("Id")] = rel.get("Target")
        for el in wb.iter():
            if _local(el.tag) != "sheet":
                continue
            rid = None
            for k, v in el.attrib.items():
                if _local(k) == "id":
                    rid = v
                    break
            target = rid_to_target.get(rid)
            if target:
                target = target.lstrip("/")
                if not target.startswith("xl/"):
                    target = "xl/" + target
                if target in z.namelist():
                    return target, el.get("name") or "Sheet1"
    if "xl/worksheets/sheet1.xml" in z.namelist():
        return "xl/worksheets/sheet1.xml", "Sheet1"
    for n in z.namelist():
        if n.startswith("xl/worksheets/") and n.endswith(".xml"):
            return n, "Sheet1"
    raise ValueError("no worksheet found inside the .xlsx")


def open_workbook(path):
    """Open an .xlsx and return a Book. Raises on anything that is not one."""
    with zipfile.ZipFile(path) as z:
        strings = _shared_strings(z)
        target, name = _first_sheet_target(z)
        root = ET.fromstring(z.read(target))

        grid, maxr, maxc = {}, -1, -1
        for el in root.iter():
            if _local(el.tag) != "c":
                continue
            col, row = _col_index(el.get("r"))
            if col is None:
                continue
            ctype = el.get("t")
            value = ""
            if ctype == "inlineStr":
                value = _text_of(el)
            else:
                v = None
                for child in el:
                    if _local(child.tag) == "v":
                        v = child.text
                        break
                if v is not None:
                    if ctype == "s":
                        try:
                            value = strings[int(v)]
                        except (ValueError, IndexError):
                            value = ""
                    elif ctype == "b":
                        value = "TRUE" if v == "1" else "FALSE"
                    else:
                        # numbers come back as float, as xlrd did, so the
                        # parsers downstream see the same shape they always saw
                        try:
                            value = float(v)
                            if value == int(value) and abs(value) < 1e15:
                                value = float(int(value))
                        except ValueError:
                            value = v
            if value == "" and ctype is None:
                continue
            grid[(row, col)] = value
            if row > maxr:
                maxr = row
            if col > maxc:
                maxc = col
        return Book([Sheet(name, grid, maxr + 1, maxc + 1)])
