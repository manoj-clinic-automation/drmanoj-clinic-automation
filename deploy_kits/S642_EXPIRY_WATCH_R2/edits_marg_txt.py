# S638 anchored edits for the medical PC's D:\SendToClinic\marg_txt.py (via Drive ToMedical\_kit; FROM e8a60d9d, S604)
# F-1008 / D771: Marg's Batch Stock (WHOLE STORES, one row per batch) is read and converted like the expiry report it is shaped as.
EDITS = []

EDITS.append(('''  server counts them from Marg's own minus sign on the bill. BILL/ITEM WISE is not changed.

    python marg_txt.py report.txt out.XLS      convert one file''', '''  server counts them from Marg's own minus sign on the bill. BILL/ITEM WISE is not changed.

S638 (F-1008, D771 / D780, 24-Oct-2026, the owner's "yes" to the expiry mock-up): MARG'S BATCH STOCK. Stocks -> Batch Stock,
  WHOLE store, saved as text, prints the closing stock's own title ("WHOLE STORES CLOSING STOCK AS ON dd-mm-yyyy") over the expiry
  report's own column heads (S.No. Description | Batch | Expiry | Stock Unit) and its own TOTAL (strips x pack + loose, Batch TOTAL
  rows as furniture). It was refused as "a closing stock the reader cannot take" (23-Oct, 05:10). The STOCK_EXPIRY spec now takes
  that title too -- the same heads, the same check, the same cutter -- so the text becomes the sheet Marg's Excel export of it is.
  Only the whole-store title is taken (a store's own title is not); the item-wise closing (Total Stock heads) is read by the STOCK
  reader exactly as before, and answers first. The server files the sheet by its own signature as BATCH_STOCK, never as a closing.
  Every text the reader took before converts to the same bytes.

    python marg_txt.py report.txt out.XLS      convert one file'''))

EDITS.append(('''VERSION = "S604"''', '''VERSION = "S638"'''))

EDITS.append(('''    dict(key="STOCK_EXPIRY", kind="EXPIRY", title=r"^EXP\\. BEFORE\\b",''',
              '''    dict(key="STOCK_EXPIRY", kind="EXPIRY", title=r"^(?:EXP\\. BEFORE\\b|WHOLE STORES CLOSING STOCK AS ON \\d{2}-\\d{2}-\\d{4}$)",   # S638: + Batch Stock'''))

EDITS.append(('''def selftest(sample=None):
    ok = True''', '''def _selftest_s638(ck):
    """S638 (F-1008): Marg's Batch Stock (WHOLE STORES title over the expiry report's heads) is taken; nothing else moves."""
    S = _s480_samples()
    E = S["STOCK_EXPIRY"]
    B = E.replace(b"EXP. BEFORE *BA.,   0", b"WHOLE STORES CLOSING STOCK AS ON 22-10-2030")
    ck("S638: the Batch Stock text is recognised (kind EXPIRY, the STOCK_EXPIRY spec)",
       kind(B) == "EXPIRY" and (spec_of(B) or {}).get("key") == "STOCK_EXPIRY", kind(B))
    xb, ib = convert(B)
    rb = spec_rows(B)
    ck("S638: it converts, keeping its own title in the sheet", ib["kind"] == "EXPIRY" and len(xb) > 4096
       and any(isinstance(c, str) and "WHOLE STORES CLOSING STOCK AS ON 22-10-2030" in c for r in rb for c in r), ib["rows"])
    ck("S638: the same text gives the same bytes every time", xb == convert(B)[0])
    ck("S638: the expiry report itself converts as before (same rows)", len(spec_rows(E)) == len(rb))
    bad = B.replace(b"\\r\\nTOTAL" + b" " * 69 + b"25", b"\\r\\nTOTAL" + b" " * 69 + b"26")
    try:
        spec_rows(bad)
        r_ = "taken"
    except Refused as ex:
        r_ = str(ex)[:60]
    ck("S638: a Batch Stock whose TOTAL is not the sum of its batches is refused", r_ != "taken" and "TOTAL" in r_, r_)
    one = B.replace(b"WHOLE STORES CLOSING STOCK AS ON", b"MAIN STORE CLOSING STOCK AS ON")
    ck("S638: a store's own batch print is not taken", spec_of(one) is None)
    tail = b"WHOLE STORES CLOSING STOCK AS ON 22-10-2030 X"
    ck("S638: the title must end at the date", spec_of(B.replace(b"WHOLE STORES CLOSING STOCK AS ON 22-10-2030", tail)) is None)


def selftest(sample=None):
    ok = True'''))

EDITS.append(('''    _selftest_s604(ck)                                                   # S604: returns inside a supplier's block (made-up blocks)
''', '''    _selftest_s604(ck)                                                   # S604: returns inside a supplier's block (made-up blocks)
    _selftest_s638(ck)                                                   # S638: Marg's Batch Stock, read as the expiry report
'''))
