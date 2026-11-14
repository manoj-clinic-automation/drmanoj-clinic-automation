

# ---------------------------------------------------------------------------------------------- S841_PHARMACY_CREDIT_NOTE (F-1419)
# A dealer's CREDIT NOTE scanned straight on the pharmacy lane (no desk): read_pharmacy() recognises it as read() does since S835 --
# doc_kind 'credit_note', its own no. (bill_no), the amount back (total_amount), the invoice it names (against_no). PHARMACY_PROMPT and
# the max-tokens fallback (_S783_PROMPT_BEFORE) are re-bound with S835's kind list and a pharmacy-worded rule; clean() (S835) already
# keeps the two values and clean_pharmacy() calls it. asset_register (S841) then marks the paper kind 'Pharmacy credit note'.
# PROMPT (the desk's reader), read(), the statement shape and S783's four item figures are unchanged. If the kind list is not found
# once in both prompts, both are left as they were (the reader keeps working; the walk goes red).
KIT_S841 = "S841_PHARMACY_CREDIT_NOTE"
S841_PH_CN_RULE = """

A CREDIT NOTE is money a supplier gives BACK to the pharmacy -- goods returned (expiry, breakage, short supply), a rate corrected, a
discount allowed -- printed under the heading "Credit Note" (or a "Credit Memo" that returns money). For a credit note answer in the
bill shape with "doc_kind": "credit_note" and "is_summary": false; "bill_no" is the credit note's OWN number; "bill_date" its own date;
"total_amount" the amount credited back (a positive number); "items" the lines credited back; and one more key: "against_no": the number
of the invoice / bill it refers to, exactly as printed (string or null). Medicine bills very often print the word CREDIT for a sale on
credit -- "Credit Invoice", "Credit Bill", "Cash / Credit", "Credit Sale", "Mode: Credit", or a "Credit Memo" that lists goods SOLD --
every such paper is a BILL ("tax_invoice" or "bill"), never a credit note; so is a bill with a line such as "Less CN" or "CN adj.". A statement that lists credit notes among its lines is still
a STATEMENT. For every other paper "against_no" is null."""
_S841_PH_BEFORE = PHARMACY_PROMPT
_S841_783_BEFORE = _S783_PROMPT_BEFORE


def _s841_rebind(p):
    return p.replace(_S835_KINDS_OLD, _S835_KINDS_NEW, 1) + S841_PH_CN_RULE


if PHARMACY_PROMPT.count(_S835_KINDS_OLD) == 1 and _S783_PROMPT_BEFORE.count(_S835_KINDS_OLD) == 1:
    PHARMACY_PROMPT, _S783_PROMPT_BEFORE = _s841_rebind(PHARMACY_PROMPT), _s841_rebind(_S783_PROMPT_BEFORE)
    S841_READY = True
else:
    S841_READY = False
    try:
        import sys as _s841_sys
        print("S841: the pharmacy reader's kind list is not where it was -- its prompt is left unchanged", file=_s841_sys.stderr)
    except Exception:                                                # noqa: BLE001
        pass
# ---- S841 end -------------------------------------------------------------------------------------------------------------------------
