#!/usr/bin/env python3
"""make_s706.py -- S706_HAND_CHANGE_WATCH: the counted edits to the two live files of this project.
    python3 -B make_s706.py <dir holding owner_notice.py and expiry_watch.py> <out dir>
Each FROM file must carry its pinned md5; every edit must match exactly once; the TO md5s are printed."""
import hashlib
import os
import sys

FROM = {"owner_notice.py": "2bc969126990a723ef9d29e041fb83f8", "expiry_watch.py": "15417df553986694db5d8739f04bf0aa"}

E_OWNER = [
# 1 the docstring names the new message
('''  After 21:00 the pair of TODAY is looked for too, so an evening export is said that evening, not at midnight.''',
 '''  After 21:00 the pair of TODAY is looked for too, so an evening export is said that evening, not at midnight.
  hand:<found at>        S706 (D828): Marg's stock changed with no sale, bill or voucher (marg_hand_change.py) -- the item, the days and the
                         quantities shifted; one message per finding run, between owner_notice.hand_from and hand_to; the link opens his
                         Expiry watch, whose top section holds the list.'''),
# 2 two settings
('''    ("owner_notice.phone_to_sunday", "14:00", "S702 (F-1089): the working window closes on a Sunday (the half day)"),
)''',
 '''    ("owner_notice.phone_to_sunday", "14:00", "S702 (F-1089): the working window closes on a Sunday (the half day)"),
    ("owner_notice.hand_from", "08:00", "S706 (D828): a stock change with no bill, sale or voucher is told from this time ..."),
    ("owner_notice.hand_to", "21:00", "S706 (D828): ... until this time; one found later waits for the next morning"),
)'''),
# 3 the link of a hand message
('''CONSOLE_URL = "/finance/console"''',
 '''CONSOLE_URL = "/finance/console"
HAND_URL = "/finance/sanjeevni/expiry"                           # S706: a hand-change message opens the Expiry watch (its top section)'''),
('''    return dict(kind="owner", title="Sanjeevni · " + title, body=body, url=CONSOLE_URL, tag="owner-" + key, ttl=86400,''',
 '''    return dict(kind="owner", title="Sanjeevni · " + title, body=body, url=(HAND_URL if str(key).startswith("hand:") else CONSOLE_URL),
                tag="owner-" + key, ttl=86400,'''),
# 4 the part, in collect's list
('''              ("phone", lambda: _part_phone(con, now))]''',
 '''              ("phone", lambda: _part_phone(con, now)), ("hand", lambda: _part_hand(con, now, since))]'''),
# 5 the part itself, after _part_phone
('''def collect(con, now):''',
 '''def _part_hand(con, now, since):
    """S706 (D828): Marg's stock changed with no sale, bill or voucher -- one message per finding run (reads only)."""
    import marg_hand_change                                       # noqa: PLC0415
    n = now.replace(tzinfo=None)
    m = n.hour * 60 + n.minute
    if m < mins(setting(con, "owner_notice.hand_from"), 480) or m >= mins(setting(con, "owner_notice.hand_to"), 1260):
        return []
    out = []
    f_from, f_to = mins(setting(con, "owner_notice.hand_from"), 480), mins(setting(con, "owner_notice.hand_to"), 1260)
    hm = "%02d:%02d" % (f_from // 60, f_from % 60)
    groups = {}
    for found, rows in marg_hand_change.message_groups(con, since, now).items():
        # R2's N1: a row's key depends on the row alone -- found inside the hours: its own time; outside: the next morning's batch
        try:
            ft = dt.datetime.strptime(found[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        fm = ft.hour * 60 + ft.minute
        if f_from <= fm < f_to:
            key = found
        else:
            day = ft.date() if fm < f_from else ft.date() + dt.timedelta(days=1)
            key = "%s %s (overnight)" % (day.isoformat(), hm)
        groups.setdefault(key, []).extend(rows)
    for found, rows in groups.items():
        lines = [marg_hand_change.message_line(r) for r in rows]
        more = (" … and %d more" % (len(lines) - 8)) if len(lines) > 8 else ""
        body = "No sale, bill or voucher behind it: %s%s. Expiry watch, top section." % ("; ".join(lines[:8]), more)
        out.append(dict(key="hand:%s" % found, kind="hand", title="Stock changed in Marg by hand — %s" % plural(len(rows), "item"),
                        body=body))
    return out


def collect(con, now):'''),
# 6 the refresh, before collect, in the tick (it writes only its own table)
('''        msgs, errors = collect(con, now)
        made = 0''',
 '''        try:                                                      # S706: the hand-change rows, when the spine was rebuilt (fail-soft)
            import marg_hand_change                               # noqa: PLC0415
            marg_hand_change.refresh(con)
        except Exception:                                         # noqa: BLE001
            pass
        msgs, errors = collect(con, now)
        made = 0'''),
# 7 the phone line: the clinic Wi-Fi is fine (the owner 05-Nov)
('''        body = "Silent since %s — ask reception: phone unlocked, screen on, mobile data on.%s" % (when, wait)''',
 '''        body = "Silent since %s — ask reception: phone unlocked, screen on, on the clinic Wi-Fi or mobile data.%s" % (when, wait)'''),
]

E_EXPIRY = [
('''    head = ('<div class="wrap"><h1>Expiry, dump and stock-out watch</h1>')''',
 '''    head = ('<div class="wrap"><h1>Expiry, dump and stock-out watch</h1>') + _hand_section(con, today)   # S706 (D828): on top, collapsed'''),
('''def _export_line(con, today, run_):''',
 '''def _hand_section(con, today):
    """S706 (D828, the owner 05-Nov): Marg's stock changed with no sale, bill or voucher -- on top of this page, collapsed, the red count
    when something new was found.  Reads marg_hand_change only (its rows are made by owner_notice's tick); never raises."""
    try:
        return _hand_section_body(con, today)
    except Exception as e:                                        # noqa: BLE001
        return '<p class="sub bad">Stock changed in Marg by hand: not readable (%s).</p>' % esc(e.__class__.__name__)


def _hand_section_body(con, today):
    import marg_hand_change as H                                  # noqa: PLC0415
    rows = H.rows_for_page(con)
    openr = [r for r in rows if r["status"] == "open" and r["kind"] == "hand"]
    ren = [r for r in rows if r["status"] == "open" and r["kind"] == "rename"]
    floor = (today - dt.timedelta(days=30)).isoformat()
    done = [r for r in rows if r["status"] != "open" and (r["status_at"] or "")[:10] >= floor]
    new = [r for r in openr if H.is_new(con, r, today)]
    badge = ('<span class="count red">%d new</span>' % len(new) if new else "") + \\
            ' <span class="count %s">%d open</span>' % ("amber" if openr else "", len(openr))

    def card(r, hi):
        return ('<div style="padding:8px 0;border-bottom:1px solid var(--line)%s"><div><b>%s</b> '
                '<span class="m">%s &rarr; %s (%s)</span> <span class="note" style="margin:0">%s &ndash; %s</span>%s</div>'
                '<div style="font-size:.86rem">%s</div><div style="font-size:.86rem;color:var(--accent)">%s</div></div>'
                % (";background:var(--red-soft)" if hi else "", esc(r["item"]), esc(H.num(r["marg_from"])), esc(H.num(r["marg_to"])),
                   esc(H.snum(r["shift"])), esc(dmon(r["day_from"])), esc(dmon(r["day_to"])), ' <span class="tag">new</span>' if hi else "",
                   esc(H.why_of(r)), esc(H.remedy_of(r))))
    body = "".join(card(r, r in new) for r in sorted(openr, key=lambda r: (r in new, r["day_to"], r["item"]), reverse=True))
    parts = ['<p class="what">Marg\\'s stock moved and nothing in the system explains it &mdash; no sale, bill or voucher. Marg went '
             '<b>from &rarr; to</b> (the shift) between the two days. You are told the morning after it is found.</p>',
             '<div style="margin-left:20px">%s</div>' % (body or '<p class="note">None.</p>')]
    if ren:
        parts.append('<details class="inner"><summary><h3>Renamed in Marg &mdash; no stock moved</h3><span class="count">%d</span></summary>'
                     '<div style="margin-left:20px">%s</div></details>' % (len(ren), "".join(card(r, False) for r in ren)))
    if done:
        parts.append('<details class="inner"><summary><h3>Put right or explained &mdash; last 30 days</h3><span class="count">%d</span>'
                     '</summary>%s</details>' % (len(done), _tbl(("Item", "Days", "Shift", "Now"), "".join(
                         '<tr><td>%s</td><td class="m">%s &ndash; %s</td><td class="m n">%s</td><td>%s</td></tr>'
                         % (esc(r["item"]), esc(dmon(r["day_from"])), esc(dmon(r["day_to"])), esc(H.snum(r["shift"])),
                            esc("put right in Marg" if r["status"] == "put right" else "explained by a later bill or voucher"))
                         for r in done), (2,))))
    return ('<details class="screen" id="hand" style="margin:10px 0 12px"><summary><h3>Stock changed in Marg without a bill or voucher</h3>'
            '%s</summary>%s</details>' % (badge, "".join(parts)))


def _export_line(con, today, run_):'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(src, edits, name):
    for i, (a, b) in enumerate(edits, 1):
        n = src.count(a)
        if n != 1:
            raise SystemExit("make_s706: %s edit %d matches %d times -- nothing written" % (name, i, n))
        src = src.replace(a, b)
    return src


def main():
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for name, edits in (("owner_notice.py", E_OWNER), ("expiry_watch.py", E_EXPIRY)):
        raw = open(os.path.join(src_dir, name), "rb").read()
        if md5(raw) != FROM[name]:
            raise SystemExit("make_s706: %s is %s, not the pinned %s -- nothing written" % (name, md5(raw), FROM[name]))
        new = apply(raw.decode("utf-8"), edits, name).encode("utf-8")
        open(os.path.join(out_dir, name), "wb").write(new)
        print("make_s706: %s %s -> %s (%d edits)" % (name, FROM[name][:8], md5(new)[:8], len(edits)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
