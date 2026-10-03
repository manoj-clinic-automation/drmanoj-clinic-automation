# ==========================================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, F-695 / D668): a paper with no bill number and no amount read (or read as an Estimate, Challan or
# Quotation) is never on Amir's list or in its count -- reception is asked "Kya yeh dawa (pharmacy) ka bill hai?" first (porders_s454).
# The matcher's fingerprint (_scan_fingerprint) now also changes when a scan's supplier, number or amount is filled in after the scan was
# made (the OCR is a background job), so the matcher sees it at the next page or cron run.
# ==========================================================================================================================================
_S454_HEAD = re.compile(r"\b(ESTIMATE|CHALLAN|QUOTATION)\b", re.I)


def _s454_unread_row(r):
    no_no = not str(r.get("bill_no") or "").strip()
    no_amt = r.get("total_amount") in (None, "") or _float_or_none(r.get("total_amount")) in (None, 0.0)
    return bool((no_no and no_amt) or _S454_HEAD.search("%s %s" % (r.get("vendor") or "", r.get("bill_no") or "")))
