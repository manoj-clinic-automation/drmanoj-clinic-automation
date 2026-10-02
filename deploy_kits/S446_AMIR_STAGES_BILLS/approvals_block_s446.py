

# ---- S446_AMIR_STAGES_BILLS (02-Oct-2026, F-680): lists chosen by STATE, not by the current month -------------------------------------
def _s446_returns_line(con, today):
    """Counter returns waiting for the owner's OK in EVERY open month (the last six), by returns_kinds' own rule (S406: counter
    returns, real items, from returns.act_from -- earlier ones are accepted, S219); the oldest named. None = keep the old path
    (NEEDS_YOU_WITHOUT_S406=1, an older kit's frozen walk) or nothing could be read."""
    if os.environ.get("NEEDS_YOU_WITHOUT_S406") == "1":
        return None
    try:
        import returns_kinds  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None
    y, m = int(today[:4]), int(today[5:7])
    months = []
    for _i in range(6):
        months.append("%04d-%02d" % (y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    n, p, dates = 0, 0, []
    try:
        for ym in reversed(months):
            notes = returns_kinds.month_notes(con, _unit, ym)
            s = returns_kinds.enrich(con, _unit, ym, notes, with_prev=False)
            n += int(s.get("pending_ok") or 0)
            p += int(s.get("pending_ok_p") or 0)
            dates += [str(x.get("date"))[:10] for x in notes if x.get("pending_ok") and x.get("date")]
    except Exception:  # noqa: BLE001
        return None
    if not n:
        return {}                                   # read, and nothing waits: no line (and not the old path)
    return dict(cls="warn", target="returns", text="Counter returns waiting for your OK: %d, %s (oldest %s)"
                % (n, rs(p), dmy(min(dates)) if dates else "?"))
# ---- S446_AMIR_STAGES_BILLS end ----
