# S638 anchored edits for /root/finance/amir_day.py (FROM 2c99c29e)
# D780: his Marg sudhar card gains the expiry watch's rows -- the month's Batch Stock card (until the file arrives), the expired batches
# to write off or return, the batches to correct (folded) -- read once in state(), never his_line (they never hold his day open).
EDITS = []
EDITS.append(('''  * The owner's ending for a proof whose items Marg's closing does not print under their name: 'absent' (stock_app._s488_why, F-786).
"""''', '''  * The owner's ending for a proof whose items Marg's closing does not print under their name: 'absent' (stock_app._s488_why, F-786).

S638_EXPIRY_WATCH (24-Oct-2026; D771 / D777 / D780, the owner's "yes" to the mock-up): the card gains the expiry watch's rows, read ONCE
in state() as S.expiry (expiry_watch.amir_rows, fail-soft): "Mahine ki report: Batch Stock (poora store) text mein save karein" with the
steps from the owner's screenshots, until the month's Batch Stock is received; "Marg mein expiry write-off ya stockist ko return karein"
with the expired batches; "Marg mein in N dawaon ka batch theek karein" (folded list). his_line is False on every one: they are monthly
work proved only by the next Batch Stock, so they never hold his day open (no gate he cannot clear).
"""'''))
EDITS.append(('''KIT = "S603_AMIR_CALENDAR_SAFE"                           # the kit that last placed this file (S533 built the page; S584 named it; S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner's 48-hour line)''',
              '''KIT = "S638_EXPIRY_WATCH"                                 # the kit that last placed this file (S533 built the page; S584 named it; S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner's 48-hour line; S638: the expiry watch's rows)'''))
EDITS.append(('''    S.jobs = _s494_read(cx) if _table_exists(cx, "amir_job") else dict(rows=[], jobs=[], label=None, newest=None, read=None, cat_read={}, cat_newest={})
    S.notes = []''', '''    S.jobs = _s494_read(cx) if _table_exists(cx, "amir_job") else dict(rows=[], jobs=[], label=None, newest=None, read=None, cat_read={}, cat_newest={})
    S.expiry = []                                              # S638 (D780): the expiry watch's rows, read once (fail-soft)
    try:
        import expiry_watch                                    # noqa: PLC0415
        S.expiry = expiry_watch.amir_rows(cx)
    except Exception:                                          # noqa: BLE001
        S.expiry = []
    S.notes = []'''))
EDITS.append(('''    for h in _s494_lines(S.jobs.get("jobs") or []):
        rows.append(("jobs", h, "one-time Marg jobs: %d" % len(S.jobs.get("jobs") or []), True))''', '''    for h in _s494_lines(S.jobs.get("jobs") or []):
        rows.append(("jobs", h, "one-time Marg jobs: %d" % len(S.jobs.get("jobs") or []), True))
    rows.extend(getattr(S, "expiry", None) or [])              # S638 (D780): the Batch Stock card, the expired batches, the batch fixes'''))
