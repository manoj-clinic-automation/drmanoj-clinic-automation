

# ---------------------------------------------------------------------------------------------- S835_CREDIT_NOTES (D986, F-1174)
# The bill reader (read() -- the desk's papers) recognises a dealer's CREDIT NOTE: doc_kind 'credit_note', its own number (bill_no),
# the amount given back (total_amount), the lines credited (items) and the invoice no. it names ('against_no'). PROMPT is re-bound
# here, so read() asks it from now on; PHARMACY_PROMPT (built from the old PROMPT above) and the pharmacy reader are unchanged -- the
# Sanjeevni side's readings keep their kinds. clean() is re-bound to keep the two new values; every other field is cleaned as before.
_S835_KINDS_OLD = '{"doc_kind": "tax_invoice" | "bill" | "estimate" | "challan" | "quotation" | "other",'
_S835_KINDS_NEW = '{"doc_kind": "tax_invoice" | "bill" | "estimate" | "challan" | "quotation" | "credit_note" | "other",'
S835_CN_RULE = """

A CREDIT NOTE is money the supplier gives BACK to the clinic -- goods returned, a rate corrected, a discount allowed -- printed under a
heading such as "Credit Note" or "Credit Memo". For a credit note answer "doc_kind": "credit_note"; "bill_no" is the credit note's OWN
number; "bill_date" its own date; "total_amount" the amount credited back (a positive number); "items" the lines credited back. Add one
more key to the object: "against_no": the number of the invoice / bill it refers to, exactly as printed (string or null). A "credit
invoice", "credit bill" or "credit memo" that SELLS goods on credit is NOT a credit note -- it is a bill. For every other paper
"against_no" is null."""
_S835_PROMPT_BEFORE = PROMPT
if PROMPT.count(_S835_KINDS_OLD) != 1:
    raise RuntimeError("S835: the reader's kind list is not where it was -- the prompt is left unchanged")
PROMPT = PROMPT.replace(_S835_KINDS_OLD, _S835_KINDS_NEW, 1) + S835_CN_RULE
_clean_before_s835 = clean


def clean(data):                                                     # noqa: F811 -- S835: + credit_note, against_no
    out = _clean_before_s835(data)
    if out is None or not isinstance(data, dict):
        return out
    if _txt(data.get("doc_kind"), 20) == "credit_note":
        out["doc_kind"] = "credit_note"
        out["against_no"] = _txt(data.get("against_no"), 60)
    return out
