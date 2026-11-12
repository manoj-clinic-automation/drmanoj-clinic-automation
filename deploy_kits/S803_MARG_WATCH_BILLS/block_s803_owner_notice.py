# ---- S803 (12-Nov-2026, Sanjeevni session 438, kit S803_MARG_WATCH_BILLS; plan v3 6.5 with D923-D928, D935, D936) --------------------------
#  A BILL CHANGED AFTER ITS DAY, TOLD ONCE: a sale or purchase bill removed, added late or altered in Marg after the day's report was taken
#  (marg_billwatch.py). One message per new finding that counts and is still open -- "Sale bill A004591 (3-Nov, Rs 1,760) is gone from Marg;
#  6 items back in Marg's stock." -- between owner_notice.hand_from and hand_to; more than three at once come as one message. A change that
#  its scanned paper settles is not told. Nothing found before the Marg watch began (billchange.since) is ever told. Tapping opens the Marg
#  watch. Before the pass the tick notes what is new and judges it once (marg_billwatch.refresh, .judge -- its own table billwatch_seen
#  only); collect only reads. A report of an older day that arrives late brings history: never told.
#  OFF until the owner turns it on, on the Marg watch page (billchange.on); then only what is found after that moment, one bill at most
#  once a week, never more than six messages a day. Every switch this file already obeys stops it too.
KIT_S803 = "S803_MARG_WATCH_BILLS"
BILLS_URL = "/finance/sanjeevni/marg-watch"
BILLS_A_DAY = 6


def _part_bills(con, now):
    n = now.replace(tzinfo=None)
    m = n.hour * 60 + n.minute
    if m < mins(setting(con, "owner_notice.hand_from"), 480) or m >= mins(setting(con, "owner_notice.hand_to"), 1260):
        return []
    import marg_billwatch as BW                                   # noqa: PLC0415 -- this project's Marg watch; one cheap read here
    rows = BW.tellable(con, n)                                    # judged by the tick (BW.judge): nothing is built or compared here
    if not rows:
        return []
    told = {r[0] for r in con.execute("SELECT key FROM owner_notice WHERE kind='bill'")}
    if sum(1 for r in con.execute("SELECT made_at FROM owner_notice WHERE kind='bill'") if str(r[0] or "")[:10] == n.strftime("%Y-%m-%d")) >= BILLS_A_DAY:
        return []                                                 # the last line of defence: never more than six bill messages in a day
    cover = max([k[len("bill:batch:"):] for k in told if k.startswith("bill:batch:")] or [""])   # a batch covers what was JUDGED up to its moment
    un = [f for f in rows if ("bill:" + f["fkey"]) not in told and f["judged_at"] > cover]
    if not un:
        return []
    if len(un) <= 3:
        return [dict(key="bill:%s" % f["fkey"], kind="bill",
                     title=("A bill was removed from Marg" if f["kind"] == "gone" else "A bill was added late in Marg" if f["kind"] == "late"
                            else "A bill was changed in Marg after its day"),
                     body="%s Marg watch." % f["line"]) for f in un]
    lines = [f["line"] for f in un]
    more = (" … and %d more." % (len(lines) - 5)) if len(lines) > 5 else ""
    return [dict(key="bill:batch:%s" % max(f["judged_at"] for f in un), kind="bill", title="%d bills changed in Marg after their day" % len(un),
                 body="%s%s Marg watch." % (" ".join(lines[:5]), more))]


_collect_before_s803 = collect


def collect(con, now):                                            # noqa: F811 -- S803: + a bill changed after its day, fail-soft like every part
    msgs, errors = _collect_before_s803(con, now)
    try:
        more = _part_bills(con, now)
    except Exception as e:                                        # noqa: BLE001
        more, errors = [], errors + ["bills: %s" % e.__class__.__name__]
    try:
        con.commit()
    except sqlite3.Error:
        pass
    seen = {m["key"] for m in msgs}
    return msgs + [m for m in more if m["key"] not in seen], errors


_payload_before_s803 = _payload


def _payload(key, title, body):                                   # noqa: F811 -- S803: a bill message opens the Marg watch
    p = _payload_before_s803(key, title, body)
    if str(key).startswith("bill:"):
        p["url"] = BILLS_URL
    return p


_tick_before_s803 = _tick


def _tick(con, now=None):                                         # noqa: F811 -- S803: note what is new before the pass (its own table only)
    try:
        if not _off() and setting(con, "owner_notice.on").strip().lower() == "on":
            import marg_billwatch as BW                           # noqa: PLC0415
            BW.refresh(con)
            BW.judge(con, (now if (now is not None and now.tzinfo is not None) else now_ist()).replace(tzinfo=None))
    except Exception:                                             # noqa: BLE001 -- the tick never waits for the Marg watch
        try:
            con.rollback()
        except sqlite3.Error:
            pass
    return _tick_before_s803(con, now)
# ---- S803 end -------------------------------------------------------------------------------------------------------------------------------


