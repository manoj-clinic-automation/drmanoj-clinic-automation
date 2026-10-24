# S638 anchored edits for /root/finance/bank_sms.py (FROM aa527840)
# F-1014: the owner's OK on an SMS-seen NEFT (Needs you) also queues the suppliers' messages -- supplier_msg.queue_neft, the one queue;
# only for a final month with a NEFT portion (neft_done's own guards); idempotent (supplier_msg's UNIQUE (month, vendor_norm, kind, ref) and INSERT OR IGNORE); audited.
EDITS = []
EDITS.append(('''def neft_event_decide(con, event_id, how, who):
    """The owner's tap: 'ok' sets confirmed_by/at; anything else marks the event rejected (Not this)."""''',
              '''def neft_event_decide(con, event_id, how, who):
    """The owner's tap: 'ok' sets confirmed_by/at; anything else marks the event rejected (Not this).
    S638 (F-1014, 24-Oct-2026): 'ok' then queues the month's supplier messages through supplier_msg.queue_neft -- the same call the pay
    page's 'NEFT done' makes -- so an SMS-seen NEFT is never left with no path to the messages (23-Oct: the OK was given, nothing was
    queued). Idempotent: a second OK answers 'already' and a re-queue adds no row. Fail-soft: a queue that cannot be made leaves the
    OK recorded and says so in the answer (queued None)."""'''))
EDITS.append(('''    con.commit()
    return dict(ok=True, id=int(r[0]), kind=kind, confirmed_by=(who if how == "ok" else None), at=stamp), 200''',
              '''    con.commit()
    queued = None
    if how == "ok":                                            # S638 (F-1014): the OK tells the suppliers
        try:
            import supplier_msg                                # noqa: PLC0415
            e = con.execute("SELECT id, month, sms_date, created_at FROM purchase_neft_event WHERE id=?", (int(r[0]),)).fetchone()
            ev = dict(id=int(e[0]), month=e[1], sms_date=e[2], created_at=e[3])
            _np, _g, final = supplier_msg.sheet(con, ev["month"])   # neft_done's own guards: a final month with a NEFT portion
            if not final or _np <= 0:
                raise ValueError("the month is not final or has no NEFT portion")
            queued = supplier_msg.queue_neft(con, ev["month"], ev)
            supplier_msg._pa()._audit(con, who, "neft_sms_ok_queued", ev["month"], dict(event=ev["id"], queued=queued))
            con.commit()
        except Exception:                                      # noqa: BLE001
            con.rollback()                                     # nothing half-queued; the OK itself was committed above
            queued = None
    return dict(ok=True, id=int(r[0]), kind=kind, confirmed_by=(who if how == "ok" else None), at=stamp, queued=queued), 200'''))
