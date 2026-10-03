# =====================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, D666): WHO DECIDES THE ORDER, AND ONE REMINDER A DAY.
#   * order.source = marg_sheet (the default): Darpan's sheet is the order; the proposals are still prepared at 09:00 but shown to no
#     staff -- no 09:00 notice, no "Order not sent" line. order.source = system: S410 as it was, the 09:00 notice included.
#   * The reminders at 12:00 and 15:00 go; ONE push at order.remind_times (default 17:00), only while a supplier is still to be ordered,
#     naming them (order_sheet.reminder_text). Decided once a day, at the first tick at or after that time.
#   * Every tick runs order_sheet.cron_pass: the sheets the door took, the WhatsApp line, Marg's clearing, the bill-scan tie -- so none of
#     them waits for someone to open the page. The cron line runs every ten minutes, 05:00-21:50 (S454's crontab edit).
# =====================================================================================================================
def _s454_source(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.source(con)
    except Exception:                                         # noqa: BLE001
        return "marg_sheet"


def _s454_or_arrived(con):
    """S454 (4.4): an order that arrived by its bill's scan keeps its open lines on the way until Marg's bill answers them (the next
    interim check does not order them twice). No tie table yet: nothing added."""
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " OR o.id IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)"
    except sqlite3.Error:
        return ""


def _s454_pass(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.cron_pass(con, "cron")
    except Exception as e:                                    # noqa: BLE001
        return dict(error=str(e)[:120])


def _s454_remind(con, today, now, force=""):
    """The one reminder of the day: once, at the first tick at or after order.remind_times; silent (but decided) when nothing is pending.
    force = a walk's forced slot ("remind17"): it speaks only when its hour is the remind time's hour -- the 12:00 and 15:00 reminders go."""
    try:
        import order_sheet                                    # noqa: PLC0415
        key, text = order_sheet.reminder_due(con, now)
        if not key:
            return dict(ok=True, silent=True, why="no remind time")
        if force:
            if str(force)[6:8] != key[1:3]:
                return dict(ok=True, silent=True, slot=key, why="S454: no reminder at %s:00" % str(force)[6:8])
            text = order_sheet.reminder_text(con)
        elif text is None and (now.hour, now.minute) < (int(key[1:3]), int(key[3:5])):
            return dict(ok=True, silent=True, why="not yet")
        ensure(con)
        if con.execute("SELECT 1 FROM order_notice WHERE day=? AND slot=?", (today.isoformat(), key)).fetchone():
            return dict(ok=True, already=True, slot=key)
        if not text:
            con.execute("INSERT OR IGNORE INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (today.isoformat(), key, "(silent: nothing pending)", "{}", now_iso()))
            con.commit()
            return dict(ok=True, silent=True, slot=key)
        to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip()]
        payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True,
                       ts=int(dt.datetime.now().timestamp() * 1000))
        sent = {}
        for u in to:
            try:
                s, f = _push(u, payload)
                sent[u] = dict(sent=s, failed=f)
            except Exception as e:                            # noqa: BLE001
                sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
        con.execute("INSERT OR IGNORE INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (today.isoformat(), key, text, json.dumps(sent), now_iso()))
        con.commit()
        return dict(ok=True, slot=key, text=text, sent=sent)
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, error=str(e)[:120])
