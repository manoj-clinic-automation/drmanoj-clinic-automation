# ---- S482_BILL_CHAIN begin (05-Oct-2026, D675 b): the chain of Marg's bill numbers says what is missing ---------------------------------
# The owner, 05-Oct: the continuity of Marg's bill numbers decides what export is missing -- never the calendar. ANY gap, even one or
# two numbers, is shown with its dates and the exact numbers and must be re-exported by someone; it is NEVER presumed a cancelled bill.
# Sale bills carry A + digits, credit notes CN + digits (mi_sale_line.bill_no, as Marg prints them); each series runs in one unbroken
# sequence across every day, open or closed. An EMPTY day (mi_file: SALE_BILLWISE, VERIFIED, lines 0, reason 'EMPTY ...') carries no
# number and is transparent: the chain runs from the numbered day before it to the numbered day after it, and a gap across it names all
# three dates (the empty day may have been a false empty). This block SHOWS: nothing is computed over a gap and nothing is blocked here.
CHAIN_FROM_DAY = "2026-08-17"       # the chain starts the day the daily feed began: mi_sale_line holds one test day in June and then
                                    # nothing until 17-Aug -- a whole-table chain would show a June -> August gap for ever
CHAIN_WIDTH = {"A": 6, "CN": 5}     # the digits Marg prints in each series, used only where no bill of the series is at hand
CHAIN_RUN = 3                       # this many missing numbers in a row, or more, are written as one run: FIRST..LAST
_CHAIN_NO = re.compile(r"^([A-Z]{1,3})(\d+)$")
_CHAIN_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CHAIN_DDL = ("CREATE TABLE IF NOT EXISTS mi_bill_chain ("
             " series TEXT NOT NULL,"                   # A (sale bills) | CN (credit notes) -- the letters of the bill number
             " day TEXT NOT NULL,"                      # ISO
             " first_no INTEGER, last_no INTEGER,"      # NULL on an EMPTY day
             " n_bills INTEGER NOT NULL DEFAULT 0,"
             " gap_before TEXT NOT NULL DEFAULT '',"    # the numbers missing between the numbered day before and this day's first, as
                                                        # Marg prints them, comma-separated (a run of CHAIN_RUN or more: FIRST..LAST)
             " gap_inside TEXT NOT NULL DEFAULT '',"    # the same format: numbers skipped within this day
             " empty INTEGER NOT NULL DEFAULT 0,"       # 1 = an EMPTY day's row: no numbers
             " source_md5 TEXT NOT NULL DEFAULT '',"
             " computed_at TEXT NOT NULL,"
             " PRIMARY KEY (series, day))")


def _chain_print(series, n, width):
    return "%s%0*d" % (series, int(width or 0), int(n))


def _chain_words(series, nos, width):
    """Missing numbers as the column holds them: 'A003478,A003480' ; a run of CHAIN_RUN or more as 'A003481..A003499'."""
    out, i, nos = [], 0, sorted(nos)
    while i < len(nos):
        j = i
        while j + 1 < len(nos) and nos[j + 1] == nos[j] + 1:
            j += 1
        if j - i + 1 >= CHAIN_RUN:
            out.append("%s..%s" % (_chain_print(series, nos[i], width), _chain_print(series, nos[j], width)))
        else:
            out.extend(_chain_print(series, n, width) for n in nos[i:j + 1])
        i = j + 1
    return ",".join(out)


def _chain_count(words):
    """How many numbers a gap column names (a run FIRST..LAST counts every number in it)."""
    n = 0
    for w in [x for x in (words or "").split(",") if x]:
        if ".." in w:
            a, b = w.split("..", 1)
            ma, mb = _CHAIN_NO.match(a), _CHAIN_NO.match(b)
            n += (int(mb.group(2)) - int(ma.group(2)) + 1) if (ma and mb) else 1
        else:
            n += 1
    return n


def rebuild_chain(con, from_day=None):
    """Rewrite mi_bill_chain from `from_day` (default CHAIN_FROM_DAY) on: one row per series per day, from every distinct
    (bill_date, bill_no) of mi_sale_line -- a re-exported day counts once; a credit note is the CN series by its letters, not by the
    is_return flag -- and one row per series, empty = 1, for every EMPTY day of mi_file. A number is MISSING only when no day of the
    series carries it; it is written on the first day that carries a higher number: before that day's first number -> gap_before
    (between the numbered day before and this one), after it -> gap_inside. The first numbered day has no gap_before: the chain
    starts there. Returns the number of rows written. Commits."""
    from_day = from_day or CHAIN_FROM_DAY
    con.execute(CHAIN_DDL)
    days, width = {}, {}
    for day, bill in con.execute("SELECT DISTINCT bill_date, bill_no FROM mi_sale_line WHERE bill_date >= ?", (from_day,)):
        m = _CHAIN_NO.match(str(bill or "").strip().upper())
        if not m or not _CHAIN_DAY.match(str(day or "")):
            continue
        s = m.group(1)
        days.setdefault(s, {}).setdefault(day, set()).add(int(m.group(2)))
        width[s] = max(width.get(s, 0), len(m.group(2)))
    src = {}
    for day, md5 in con.execute("SELECT l.bill_date, l.md5 FROM (SELECT DISTINCT bill_date, md5 FROM mi_sale_line WHERE bill_date >= ?) l "
                                "LEFT JOIN mi_file f ON f.md5 = l.md5 ORDER BY l.bill_date, COALESCE(f.received_at, ''), l.md5", (from_day,)):
        src[day] = md5 or ""                                    # the newest export that carries the day
    empties = {}
    for day, md5 in con.execute("SELECT substr(date_from, 1, 10), md5 FROM mi_file WHERE type = 'SALE_BILLWISE' AND verdict = 'VERIFIED' "
                                "AND lines = 0 AND reason LIKE 'EMPTY%' AND substr(date_from, 1, 10) >= ? ORDER BY received_at", (from_day,)):
        if _CHAIN_DAY.match(str(day or "")):
            empties[day] = md5 or ""
    now = MI.now_ist().isoformat()
    rows = []
    for s in sorted(set(days) | (set(CHAIN_WIDTH) if empties else set())):
        per = days.get(s, {})
        allnos = set().union(*per.values()) if per else set()
        w = width.get(s) or CHAIN_WIDTH.get(s, 0)
        hi = None                                               # the highest number any earlier day of the series carried
        for day in sorted(set(per) | set(empties)):
            nos = per.get(day)
            if not nos:
                rows.append((s, day, None, None, 0, "", "", 1, empties[day], now))
                continue
            first, last = min(nos), max(nos)
            fresh = [n for n in nos if hi is None or n > hi]    # this day's numbers beyond everything seen before it
            before, inside = [], []
            if fresh:
                f0 = min(fresh)
                if hi is not None:
                    before = [n for n in range(hi + 1, f0) if n not in allnos]
                inside = [n for n in range(f0 + 1, last) if n not in allnos]
            rows.append((s, day, first, last, len(nos), _chain_words(s, before, w), _chain_words(s, inside, w), 0, src.get(day, ""), now))
            hi = last if hi is None else max(hi, last)
    con.execute("DELETE FROM mi_bill_chain WHERE day >= ?", (from_day,))
    con.executemany("INSERT OR REPLACE INTO mi_bill_chain (series, day, first_no, last_no, n_bills, gap_before, gap_inside, empty, "
                    "source_md5, computed_at) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    return len(rows)


def chain_state(con):
    """A PURE READ of mi_bill_chain -> {built, complete, gaps: [{series, between: [day_before, day_after], via_empty: [days],
    missing: ['A003478', ...], n}], last: {series: [day, number as Marg prints it]}}. A gap inside one day has between = [day, day].
    `missing` holds the column's own words (a long run is one word, FIRST..LAST); `n` counts every number. A chain never built
    (no table) is not known complete: built False, complete False, no gaps."""
    out = dict(built=False, complete=False, gaps=[], last={})
    try:
        rows = con.execute("SELECT series, day, first_no, last_no, gap_before, gap_inside, empty FROM mi_bill_chain "
                           "ORDER BY series, day").fetchall()
    except sqlite3.OperationalError:
        return out
    out["built"] = True
    prev, via, top = {}, {}, {}
    for r in rows:
        s, day, first, last, gb, gi, empty = r[0], r[1], r[2], r[3], r[4] or "", r[5] or "", r[6]
        if empty or first is None:
            via.setdefault(s, []).append(day)
            continue
        if gb:
            out["gaps"].append(dict(series=s, between=[prev.get(s) or day, day], via_empty=list(via.get(s) or []),
                                    missing=[x for x in gb.split(",") if x], n=_chain_count(gb)))
        if gi:
            out["gaps"].append(dict(series=s, between=[day, day], via_empty=[], missing=[x for x in gi.split(",") if x], n=_chain_count(gi)))
        prev[s], via[s] = day, []
        if s not in top or int(last) >= top[s][1]:
            top[s] = (day, int(last))
    for s, (day, last) in top.items():
        w = 0
        try:
            w = con.execute("SELECT MAX(length(bill_no)) FROM mi_sale_line WHERE bill_date = ? AND bill_no GLOB ?",
                            (day, s + "[0-9]*")).fetchone()[0] or 0
        except sqlite3.OperationalError:
            w = 0
        out["last"][s] = [day, _chain_print(s, last, (w - len(s)) if w else CHAIN_WIDTH.get(s, 0))]
    out["gaps"].sort(key=lambda g: (g["between"][1], g["between"][0], g["series"]))
    out["complete"] = not out["gaps"]
    return out


def _s482_chain(con):
    """After a sale report or an EMPTY day lands. Fail-soft: the door never refuses a file because the chain could not be rewritten;
    the next sale report rewrites it whole."""
    try:
        return rebuild_chain(con)
    except Exception as e:                                       # noqa: BLE001
        print("marg_take: the bill chain was not rebuilt now (%s) -- the next sale report rebuilds it" % str(e)[:120], file=sys.stderr)
        try:
            con.rollback()
        except Exception:                                        # noqa: BLE001
            pass
        return None
# ---- S482_BILL_CHAIN end ---------------------------------------------------------------------------------------------------------------


