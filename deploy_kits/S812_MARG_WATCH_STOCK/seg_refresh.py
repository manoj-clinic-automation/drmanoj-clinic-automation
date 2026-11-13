def refresh(con, spine_path=SPINE_DB, finance_db=None, now=None, force=False):
    """Recompute and store; only when the spine was rebuilt since the last read (or force).  Never raises -> dict.
    S812: the record behind a move is stored with it (rec_kind, rec_ref, rec_note), and so are the bill Marg took in late (owed_paid) and
    the rupees (rate_p, value_p).  A stored row that is no longer found takes the record that absorbed it, when one did."""
    try:
        ensure(con)
        o = off(con)
        if o:
            return {"ok": True, "off": o}
        if not os.path.exists(spine_path):
            return {"ok": True, "skip": "no spine"}
        sp = sqlite3.connect("file:%s?mode=ro" % spine_path, uri=True, timeout=30)
        try:
            built = (sp.execute("SELECT value FROM sp_meta WHERE key='built'").fetchone() or [""])[0]
        finally:
            sp.close()
        ver = KIT2 + ":" + built
        if not force and built and setting(con, "hand.built_seen") in (built, ver) and setting(con, "hand.built_seen") == ver:
            return {"ok": True, "same": built}
        if finance_db is None:
            finance_db = _main_path(con)
        first = not con.execute("SELECT 1 FROM marg_hand_change LIMIT 1").fetchone() and not setting(con, "hand.since")
        first812 = not setting(con, "hand.s812_since")            # S812's first run: what it finds that was never stored is history too
        rows, info = compute(spine_path, finance_db, setting(con, "hand.from_day") or "2026-10-16")
        now = now or now_ist()
        t = stamp(now)
        if info.get("bills_why"):                                 # the review's MUST 5: matcher 1 could not read the bills -- store NOTHING
            con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",   # (a row it explains would read as counted and be told)
                        ("hand.last_run", json.dumps(dict(at=t, built=built, held=True, bills_why=info["bills_why"]), ensure_ascii=False),
                         "S812: the last refresh -- what it read"))
            con.commit()
            return {"ok": False, "held": True, "error": "the bills changed after their day could not be read: %s -- nothing stored" % info["bills_why"]}
        found = set()
        new = 0
        for r in rows:
            found.add((r["k20"], r["day_to"], r["kind"]))
            st = "put right" if r["settled"] else "open"
            extra = (r.get("rec_kind") or None, r.get("rec_ref") or None, r.get("rec_note") or None, r.get("owed_paid"), r.get("rate_p"),
                     r.get("value_p"))
            cur = con.execute("INSERT OR IGNORE INTO marg_hand_change (k20, item, kind, day_from, day_to, marg_from, marg_to, system_moved, "
                              "shift, pair_item, found_at, status, status_at, hist, rec_kind, rec_ref, rec_note, owed_paid, rate_p, value_p) "
                              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (r["k20"], r["item"], r["kind"], r["day_from"], r["day_to"], r["marg_from"], r["marg_to"], r["system_moved"],
                               r["shift"], r["pair_item"], t, st, t, 1 if (first or first812) else 0) + extra)
            new += cur.rowcount or 0
            if not cur.rowcount:
                con.execute("UPDATE marg_hand_change SET item=?, day_from=?, marg_from=?, marg_to=?, system_moved=?, shift=?, pair_item=?, "
                            "status=CASE WHEN status=? THEN status ELSE ? END, status_at=CASE WHEN status=? THEN status_at ELSE ? END, "
                            "rec_kind=?, rec_ref=?, rec_note=?, owed_paid=?, rate_p=?, value_p=? "
                            "WHERE k20=? AND day_to=? AND kind=?",
                            (r["item"], r["day_from"], r["marg_from"], r["marg_to"], r["system_moved"], r["shift"], r["pair_item"],
                             st, st, st, t) + extra + (r["k20"], r["day_to"], r["kind"]))
        gone = 0
        edge = min(info["judged_to"] or "", info["last_pur"] or "", info.get("pur_after_to") or "")   # F-1278 in the sweep too
        ex = info.get("explain") or {}
        for rid, k, d, kind, st in con.execute("SELECT id, k20, day_to, kind, status FROM marg_hand_change").fetchall():
            if (k, d, kind) not in found and st != "explained" and d <= edge:     # the cold review's S6: only inside what is judged now
                rk = ex.get((k, d))
                con.execute("UPDATE marg_hand_change SET status='explained', status_at=?, rec_kind=?, rec_ref=?, rec_note=? WHERE id=?",
                            (t, rk[0] if rk else None, (rk[1] or None) if rk else None, rk[2] if rk else None, rid))
                gone += 1
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    ("hand.built_seen", ver, next(n for k, _d, n in SETTINGS if k == "hand.built_seen")))
        if first:                                                 # the first fill is the history: shown on the page, never announced, never 'new'
            con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                        ("hand.since", t, next(n for k, _d, n in SETTINGS if k == "hand.since")))
        if first812:
            con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                        ("hand.s812_since", t, next(n for k, _d, n in SETTINGS if k == "hand.s812_since")))
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    ("hand.last_run", json.dumps(dict(at=t, built=built, rows=len(rows), counted=sum(1 for r in rows if r["kind"] == "hand" and not r.get("rec_kind")),
                                                      bills=info.get("bills"), bills_why=info.get("bills_why"), judged_to=info["judged_to"],
                                                      last_pur=info["last_pur"], last_pur_taken=info.get("last_pur_taken")), ensure_ascii=False),
                     "S812: the last refresh -- what it read (the Marg watch's section A shows it)"))
        con.commit()
        return {"ok": True, "built": built, "rows": len(rows), "new": new, "explained": gone, "judged_to": info["judged_to"],
                "last_pur": info["last_pur"], "bills": info.get("bills"), "bills_why": info.get("bills_why")}
    except Exception as e:                                        # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return {"ok": False, "error": ("%s: %s" % (e.__class__.__name__, e))[:200]}


def _main_path(con):
    try:
        for r in con.execute("PRAGMA database_list").fetchall():
            if str(r[1]) == "main":
                return str(r[2] or "")
    except sqlite3.Error:
        pass
    return ""


# ------------------------------------------------------------------ what the owner sees
COLS = ("id", "k20", "item", "kind", "day_from", "day_to", "marg_from", "marg_to", "system_moved", "shift", "pair_item", "found_at", "status",
        "status_at", "hist", "rec_kind", "rec_ref", "rec_note", "owed_paid", "rate_p", "value_p")
REC_WORDS = {"bill": "A bill changed after its day", "timing": "A bill Marg took in at another closing", "undone": "Undone a closing or two later",
             "sibling": "A voucher on another size or form of the item", "voucher_qty": "A voucher of a different quantity",
             "sale_not_off": "A sale Marg did not take off", "free": "Free goods counted in Marg"}


def rows_for_page(con, all_rows=False):
    """The rows. By default (the Expiry watch's section, S706) only what is COUNTED -- a row with a record behind it (S812) is left out;
    all_rows=True gives every row, with the record (the Marg watch's section A)."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='marg_hand_change'").fetchone():
        return []
    have = {r[1] for r in con.execute("PRAGMA table_info(marg_hand_change)")}
    sel = ", ".join(c if c in have else "NULL" for c in COLS)
    shut = set() if all_rows else _closed_ids(con)             # a move he closed on the Marg watch leaves the Expiry watch's list too
    out = []
    for r in con.execute("SELECT %s FROM marg_hand_change ORDER BY day_to DESC, item" % sel).fetchall():
        d = dict(zip(COLS, tuple(r)))
        if all_rows or not (d.get("rec_kind") or d["id"] in shut):
            out.append(d)
    return out


def _closed_ids(con):
    """The moves he closed on the Marg watch (billwatch_act 'hand:<id>', the newest act a close)."""
    shut = set()
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='billwatch_act'").fetchone():
        for fk, act in con.execute("SELECT fkey, action FROM billwatch_act WHERE fkey LIKE 'hand:%' ORDER BY id"):
            try:
                rid = int(fk[5:])
            except ValueError:
                continue
            (shut.add if act == "close" else shut.discard)(rid)
    return shut


def counted(r):
    """D914: a move is counted only when nothing stands behind it -- kind 'hand', no record."""
    return r.get("kind") == "hand" and not r.get("rec_kind")


def is_new(con, r, today, days=None):
    """Found after the first fill and within hand.new_days days -> the page's red badge."""
    hs = setting(con, "hand.since")
    try:
        days = int(days if days is not None else (setting(con, "hand.new_days") or 3))
    except ValueError:
        days = 3
    return bool(hs) and not r.get("hist") and r["found_at"][:10] >= (today - dt.timedelta(days=days)).isoformat()


def _note(r):
    if str(r.get("day_to") or "") > NOTES_TO:
        return None
    k = r["k20"] if r.get("k20") in NOTES else K(r["item"])
    note = NOTES.get(k)
    day = NOTES_DAY.get(k)
    if note is None or not day or str(r.get("day_to") or "") != day:  # S812 (F-1270): a note is the owner's word on ONE move, not on every move of the item
        return None
    return note


def rs(p):
    """Paise -> his rupees, signed."""
    if p is None:
        return "no rate"
    v = int(p) / 100.0
    return ("+" if v > 0 else "−" if v < 0 else "") + "₹" + format(abs(int(round(v))), ",")


def why_of(r):
    if r.get("rec_kind") and r.get("rec_note"):
        return r["rec_note"]
    note = _note(r)
    if note and note[0]:
        return note[0]
    if r["kind"] == "rename":
        return "Renamed in Marg (%s): the same quantity left one name and arrived on the other." % (r.get("pair_item") or "")
    moved = float(r.get("system_moved") or 0)
    paid = float(r.get("owed_paid") or 0)                      # S812 (F-1270): the whole sum -- Marg's move = the system's + a late bill + the shift
    mm = float(r.get("marg_to") or 0) - float(r.get("marg_from") or 0)
    s = ("Marg went %s to %s (%s) between %s and %s. The system moved %s (sales, bills and vouchers)"
         % (num(r["marg_from"]), num(r["marg_to"]), snum(mm), dmon(r["day_from"]), dmon(r["day_to"]), snum(moved) if moved else "nothing"))
    if abs(paid) >= TOL:
        s += "; %s is a bill Marg took in late" % snum(paid)
    s += " — %s with no record." % snum(r["shift"])
    if r.get("rec_note"):
        s += " " + r["rec_note"]
    return s


def remedy_of(r):
    note = _note(r)
    if note and note[1]:
        return note[1]
    return REMEDY_RENAME if r["kind"] == "rename" else REMEDY


def floor_p(con):
    """D943: the floor, in paise -- a counted move worth less is listed, never told. 0 = none."""
    try:
        return max(0, int(round(float(setting(con, "hand.floor_rs") or 0) * 100)))
    except ValueError:
        return 0


def message_groups(con, since, now, hours=36):
    """{found_at: [rows]} of kind 'hand', found after `since`, not the first fill (the history), within `hours` -- for owner_notice.
    S812: only what is COUNTED (no record behind it), and not below his floor (a move with no rate is told)."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='marg_hand_change'").fetchone():
        return {}
    hs = setting(con, "hand.since")
    if not hs:
        return {}
    have = {r[1] for r in con.execute("PRAGMA table_info(marg_hand_change)")}
    if not {"rec_kind", "value_p"} <= have:
        return {}                                                # S812 not yet filled: say nothing rather than tell explained rows
    since = str(since or "~")
    floor = stamp(now - dt.timedelta(hours=hours))
    fp = floor_p(con)
    shut = _closed_ids(con)                                      # a move he closed on the Marg watch is never pushed
    g = collections.OrderedDict()
    recent = (now.date() - dt.timedelta(days=10)).isoformat()     # S2 / R2's N2: a shift older than ten days found late is on the page, not told
    for r in con.execute("SELECT item, day_from, day_to, marg_from, marg_to, shift, found_at, value_p, id FROM marg_hand_change WHERE kind='hand' "
                         "AND status='open' AND hist=0 AND COALESCE(rec_kind,'')='' AND found_at > ? AND found_at >= ? AND day_to >= ? "
                         "ORDER BY found_at, day_to, item", (since or "~", floor, recent)).fetchall():
        if (fp and r[7] is not None and abs(int(r[7])) < fp) or r[8] in shut:
            continue
        g.setdefault(r[6], []).append(dict(item=r[0], day_from=r[1], day_to=r[2], marg_from=r[3], marg_to=r[4], shift=r[5]))
    return g


def message_line(r):
    return "%s: %s → %s (%s), between %s and %s" % (r["item"], num(r["marg_from"]), num(r["marg_to"]), snum(r["shift"]),
                                                     dmon(r["day_from"]), dmon(r["day_to"]))


