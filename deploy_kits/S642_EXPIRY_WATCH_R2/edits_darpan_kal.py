# S638 anchored edits for /root/finance/darpan_kal.py (FROM 6159b75b)
# D780: the order tab's payload carries 'sell_first' -- the batches Marg stops selling within expiry.darpan_months, grouped by the
# day Marg stops them (expiry_watch.darpan_groups, read in-process, fail-soft: without it the tab is exactly as before).
EDITS = []
EDITS.append(('''bank_standin.py (the parent's); every read of it here is fail-soft: without it this file behaves as c45bb343 did.
"""''', '''bank_standin.py (the parent's); every read of it here is fail-soft: without it this file behaves as c45bb343 did.

S638 (D780, 24-Oct-2026, the owner's "yes" to the expiry mock-up): the order tab's payload carries 'sell_first' -- the batches Marg
stops selling within expiry.darpan_months months, each with its batch and its stock, grouped by the day Marg stops them
(expiry_watch.darpan_groups; the nightly list of spine/near_expiry.py). A do-this line, nothing to tap (D708). Fail-soft: an empty
list when the module, its tables or a run is missing -- the tab is then byte-for-byte what it was.
"""'''))
EDITS.append(('''    except Exception:                                          # noqa: BLE001 -- a spine that cannot be opened leaves the line out (never a stand-in)
        pu = None
    return dict(ok=True, date=day, list_time=lt,''', '''    except Exception:                                          # noqa: BLE001 -- a spine that cannot be opened leaves the line out (never a stand-in)
        pu = None
    try:                                                       # S638 (D780): the batches to sell first, from the nightly expiry watch
        import expiry_watch                                    # noqa: PLC0415
        sf = expiry_watch.darpan_groups(con)
    except Exception:                                          # noqa: BLE001 -- no module, no table, no run: the block stays out
        sf = []
    return dict(ok=True, sell_first=sf, date=day, list_time=lt,'''))
