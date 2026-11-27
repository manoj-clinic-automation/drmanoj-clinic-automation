

# ---------------------------------------------------------------------------------------------- S973_VOUCHER_SCANS (D1091 plan 2.4)
# A printed Marg STOCK VOUCHER scanned on the pharmacy lane -- the pharmacy's own Stock Issue (L000045) or Stock Receive / Goods Receipt
# Note (AD00045), printed from its Marg software -- is recognised by read_pharmacy(): doc_kind 'stock_voucher', its number (bill_no), its
# date, its lines (item as printed, qty, batch, expiry) and 'voucher_type' ISSUE / RECEIVE; no seller, no amount. PHARMACY_PROMPT and the
# max-tokens fallback (_S783_PROMPT_BEFORE) are re-bound once more with the kind list widened and a pharmacy-worded rule (S841's pattern);
# clean() is re-bound to keep the kind and voucher_type. asset_register (S973) then marks the paper kind 'Stock voucher'. PROMPT (the
# desk's reader), read(), the statement shape, S783's four item figures and S841's credit note are unchanged. If the kind list is not found
# once in both prompts, both are left as they were (the reader keeps working; the walk goes red). Planned on the board (D646) by the
# Sanjeevni chat; the Scan App chat owns this file.
KIT_S973 = "S973_VOUCHER_SCANS"
_S973_KINDS_OLD = _S835_KINDS_NEW
_S973_KINDS_NEW = '{"doc_kind": "tax_invoice" | "bill" | "estimate" | "challan" | "quotation" | "credit_note" | "stock_voucher" | "other",'
S973_SV_RULE = """

A STOCK VOUCHER is the pharmacy's OWN internal paper printed from its Marg software -- it moves goods in or out of its own stock and is
not bought from or sold to anyone: a "Stock Issue" (goods taken OUT of stock; its number looks like L000045) or a "Stock Receive" / "Goods
Receipt Note" (goods put back INTO stock; its number looks like AD00045). It has no supplier's bill number, no GST invoice and usually no
amount payable. For a stock voucher answer in the bill shape with "doc_kind": "stock_voucher" and "is_summary": false; "bill_no" is the
voucher's number exactly as printed; "bill_date" its date; "vendor": null; "total_amount": null; "items" every line printed, each with the
item's FULL name as printed, "qty" as printed, "batch" and "expiry"; and one more key: "voucher_type": "ISSUE" for a stock issue, "RECEIVE"
for a stock receive / goods receipt note (null if you cannot tell). A supplier's bill, challan, delivery note or credit note is NEVER a stock
voucher, even when it names the pharmacy. For every other paper "voucher_type" is null."""
_S973_PH_BEFORE = PHARMACY_PROMPT
_S973_783_BEFORE = _S783_PROMPT_BEFORE


def _s973_rebind(p):
    return p.replace(_S973_KINDS_OLD, _S973_KINDS_NEW, 1) + S973_SV_RULE


if PHARMACY_PROMPT.count(_S973_KINDS_OLD) == 1 and _S783_PROMPT_BEFORE.count(_S973_KINDS_OLD) == 1:
    PHARMACY_PROMPT, _S783_PROMPT_BEFORE = _s973_rebind(PHARMACY_PROMPT), _s973_rebind(_S783_PROMPT_BEFORE)
    S973_READY = True
else:
    S973_READY = False
    try:
        import sys as _s973_sys
        print("S973: the pharmacy reader's kind list is not where it was -- its prompt is left unchanged", file=_s973_sys.stderr)
    except Exception:                                                # noqa: BLE001
        pass
_clean_before_s973 = clean


def clean(data):                                                     # noqa: F811 -- S973: + stock_voucher, voucher_type
    out = _clean_before_s973(data)
    if out is None or not isinstance(data, dict):
        return out
    if _txt(data.get("doc_kind"), 20) == "stock_voucher":
        import re as _s973_re
        if not _s973_re.fullmatch(r"(L|AD)0*\d{1,6}", _s973_re.sub(r"[\s\-/.]", "", str(data.get("bill_no") or "").upper())):
            out["doc_kind"] = None                                   # review: no Marg voucher number on it -- never wipe a possible bill's seller
            return out
        vt = (_txt(data.get("voucher_type"), 10) or "").upper()
        out["doc_kind"] = "stock_voucher"
        out["voucher_type"] = vt if vt in ("ISSUE", "RECEIVE") else None
        out["vendor"] = None                                         # the pharmacy's own paper: never a seller
        out["total_amount"] = None
        raw = [it for it in (data.get("items") if isinstance(data.get("items"), list) else []) if isinstance(it, dict) and _txt(it.get("name"))]
        for it, src in zip(out.get("items") or [], raw):             # the same order and filter as clean() itself
            q = src.get("qty_printed", src.get("qty"))
            it["qty_printed"] = _txt(q, 20) if q is not None else None   # '6:11' as printed (the number field cannot hold it)
    return out
# ---- S973 end -------------------------------------------------------------------------------------------------------------------------
