

# ---- S973 (27-Nov-2026, Sanjeevni session 540, kit S973_VOUCHER_SCANS; the cold review's M1) ---------------------------------------------
#  A Marg STOCK VOUCHER scanned on the pharmacy lane (the Scan App files it as kind 'Stock voucher') is not a bill either: it has no bill
#  total, so it is never judged as one and never asked to be scanned again (reception's 'Aaj ka bill kaam', the scans to redo). The same rule
#  as S765's summary: the filed kind alone decides it.
KIT_S973 = "S973_VOUCHER_SCANS"
_is_summary_before_s973 = is_summary


def is_summary(bill, reading=None):                                  # noqa: F811 -- S973: + a stock voucher (no bill, no bill total)
    return _is_summary_before_s973(bill, reading) or str((bill or {}).get("kind") or "") == "Stock voucher"
# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------
