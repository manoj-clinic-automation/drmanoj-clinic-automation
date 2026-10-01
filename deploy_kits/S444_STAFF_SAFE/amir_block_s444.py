

# ==========================================================================
# S444_STAFF_SAFE (01-Oct-2026, D647 / D648 · F-669 F-670 F-671 F-672) -- the system remembers so the staff need not.
#
#   * The bill line shows what the server already knows: "Marg: Rs X · Kaagaz (scan): Rs Y" -- read through the
#     S439/S440 link (purchase_bill.scan_bill_id -> the paper amount S440 keeps, else the scan's read total). READ ONLY.
#   * A seventh answer, "Meri entry galat thi -- Marg mein theek kar di" (reason 'self'): NO claim; the bill waits in
#     the flagged list for Marg's next export and clears ITSELF when a later bill-wise export carries it at the paper's
#     amount (+-Rs 1) -- with no scan, at an amount other than the one he flagged.  Never holds a day open (S246).
#   * Step 6 is "Marg sudhar": (a) the count's stock vouchers not yet entered, orthotic first; (b) the renames, only
#     once the proof is green (S437 gate, read from stock_app); (c) the salt work.  (a)/(b) also stand at the top of
#     every step while open.  The SALT WISE ITEM LIST, while salt ticks are newer than the last verified list, is one
#     red card on step 6 and the close screen -- never a gate.
#   * needs_you_lines(con): the owner's lines, each with who and since when, each gone by itself when put right --
#     (a) the salt list owed, (b) his own correction unseen after N exports, (c) Darpan's claim open N days, (d) count
#     vouchers untouched for N of his visits, the duty map's orphan duties (DUTY_MAP.json) and a report refused today.
# ==========================================================================

S444_KIT = "S444_STAFF_SAFE"
S444_TOL_P = 100                                     # Rs 1 -- "equal within Rs 1"
S444_DUTY_MAP = os.environ.get("DUTY_MAP_JSON", "/root/deploy/repo/claude_code_briefs/DUTY_MAP.json")
S444_DEFAULTS = {"amir.salt_owed_days": 2, "amir.self_exports": 2, "amir.claim_open_days": 7, "amir.voucher_visits": 2}
S444_NOTES = {"amir.salt_owed_days": "S444: days a SALT WISE ITEM LIST may be owed before the owner's Needs-you line",
              "amir.self_exports": "S444: bill-wise exports after Amir's own correction before the owner's line",
              "amir.claim_open_days": "S444: days a claim for Darpan may stay open before the owner's line",
              "amir.voucher_visits": "S444: Amir's visits without opening the count vouchers before the owner's line"}


def _s444_setting(cx, key):
    try:
        r = cx.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        v = r[0] if r is not None else None
        return max(0, int(v)) if v not in (None, "") else S444_DEFAULTS[key]
    except Exception:                                                  # noqa: BLE001
        return S444_DEFAULTS[key]


def s444_seed_settings(cx):
    """The four day/visit counts as settings rows (INSERT OR IGNORE: a value already set is never moved)."""
    n = 0
    for k, v in S444_DEFAULTS.items():
        cur = cx.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, str(v), S444_NOTES[k]))
        n += cur.rowcount or 0
    return n


def _s444_ensure(cx):
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_self_wait(
        supplier_norm TEXT NOT NULL,
        bill_no       TEXT NOT NULL,
        bill_date     TEXT NOT NULL,
        marked_at     TEXT NOT NULL,
        marked_by     TEXT,
        marg_p        INTEGER,                 -- Marg's amount on the newest export when he said 'self'
        paper_p       INTEGER,                 -- the paper's amount then (S440 paper amount, else the scan's read total)
        paper_src     TEXT,
        export_md5    TEXT,                    -- that newest bill-wise export
        export_at     TEXT,                    -- its received_at: only LATER exports can clear the bill
        cleared_at    TEXT,
        cleared_how   TEXT,
        PRIMARY KEY(supplier_norm, bill_no, bill_date))""")


def _s444_audit(cx, who, action, ref, detail):
    try:
        cx.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                   (_stamp(), who, action, ref, json.dumps(detail, sort_keys=True)))
    except Exception:                                                  # noqa: BLE001
        pass


def _s444_rs(p):
    try:
        return "{:,}".format(int(round(int(p) / 100.0)))
    except (TypeError, ValueError):
        return "-"


def _s444_exports_for(cx, supplier_norm, bill_no, bill_date):
    """Every bill-wise export carrying the bill, newest first: [(amount_p, received_at, md5)]."""
    if not (_table_exists(cx, "purchase_bill") and _table_exists(cx, "purchase_export")):
        return []
    return [(r[0], r[1] or "", r[2]) for r in cx.execute(
        "SELECT b.amount_p, e.received_at, e.md5 FROM purchase_bill b JOIN purchase_export e ON e.md5 = b.bw_md5 "
        "WHERE e.type = 'BILLWISE' AND b.supplier_norm = ? AND b.bill_no = ? AND b.bill_date = ? "
        "ORDER BY e.received_at DESC, e.export_stamp DESC", (supplier_norm, bill_no, bill_date)).fetchall()]


def _s444_paper(cx, supplier_norm, bill_no, bill_date):
    """(paper_p, src) through the S439/S440 link: the paper amount S440 keeps, else the scan's read total; (None, None)
    when the bill has no scan; (None, 'scan') when it has one whose amount was not read.  Fail-soft, read only."""
    sid = None
    try:
        r = cx.execute("SELECT MAX(scan_bill_id) FROM purchase_bill WHERE supplier_norm=? AND bill_no=? AND bill_date=? "
                       "AND scan_bill_id IS NOT NULL", (supplier_norm, bill_no, bill_date)).fetchone()
        sid = r[0] if r else None
        if sid is None and _table_exists(cx, "purchase_scan_link"):
            r = cx.execute("SELECT l.asset_bill_id FROM purchase_scan_link l JOIN purchase_bill b ON b.id = l.bill_id "
                           "WHERE b.supplier_norm=? AND b.bill_no=? AND b.bill_date=? ORDER BY b.id DESC LIMIT 1",
                           (supplier_norm, bill_no, bill_date)).fetchone()
            sid = r[0] if r else None
    except Exception:                                                  # noqa: BLE001
        sid = None
    if sid is None:
        return None, None
    try:
        cols = {c[1] for c in cx.execute("PRAGMA table_info(purchase_scan_state)").fetchall()}
        if "paper_amount" in cols:
            r = cx.execute("SELECT paper_amount FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone()
            if r is not None and r[0] is not None:
                return int(r[0]), "paper"
    except Exception:                                                  # noqa: BLE001
        pass
    try:
        import purchase_app                                            # noqa: PLC0415 -- READ ONLY: its read-only door to assets.db
        acon = purchase_app._assets_con()
        if acon is not None:
            try:
                r = acon.execute("SELECT total_amount FROM bills WHERE id=?", (sid,)).fetchone()
            finally:
                acon.close()
            if r is not None and r[0] not in (None, ""):
                return int(round(float(r[0]) * 100)), "scan"
    except Exception:                                                  # noqa: BLE001
        pass
    return None, "scan"


def _s444_enrich(cx, bills):
    """Each bill on step 5 gets what the server knows: Marg's newest amount and the paper's."""
    for b in bills:
        try:
            ex = _s444_exports_for(cx, b["supplier_norm"], b["bill_no"], b["bill_date"])
            marg = ex[0][0] if ex else b.get("amount_p")
            paper, src = _s444_paper(cx, b["supplier_norm"], b["bill_no"], b["bill_date"])
            if paper is not None and marg is not None:
                state = "ok" if abs(int(marg) - int(paper)) <= S444_TOL_P else "diff"
            else:
                state = "noscan" if src is None else "noamount"
            b["s444"] = {"marg_p": marg, "paper_p": paper, "src": src, "state": state}
        except Exception:                                              # noqa: BLE001
            b["s444"] = None


def _s444_paper_line(b):
    """Under the supplier and the number: Marg: Rs X · Kaagaz (scan): Rs Y -- and, on his own correction, what it waits for."""
    s = b.get("s444") or None
    out = ""
    if s:
        if s["state"] == "ok":
            tail = "<b class=good>mil gaya &#10003;</b>"
        elif s["state"] == "diff":
            tail = "<b class=bad>farq &#8377;%s</b>" % _esc(_s444_rs(abs(int(s["marg_p"]) - int(s["paper_p"]))))
        elif s["state"] == "noamount":
            tail = "<span class=sub>scan mein rakam nahi padhi</span>"
        else:
            tail = "<span class=sub>scan nahi hua</span>"
        paper = ("&#8377;%s" % _esc(_s444_rs(s["paper_p"]))) if s.get("paper_p") is not None else "&mdash;"
        out = ("<div class=meta id='s444amt'>Marg: &#8377;%s &middot; Kaagaz (%s): %s &middot; %s</div>"
               % (_esc(_s444_rs(s["marg_p"])), "paper" if s.get("src") == "paper" else "scan", paper, tail))
    if b.get("reason") == "self":
        out += ("<div class=was>Marg ki agli export ka intezaar &mdash; Marg mein sahi rakam aate hi yeh khud hat jayega. "
                "Na hate to <b>Theek hai</b> dabaiye.</div>")
    return out


def s444_mark_self(cx, supplier_norm, bill_no, bill_date, who, settled_by=None):
    """His own slip, corrected in Marg: the bill waits for Marg's next export (amir_self_wait), and any claim open on it for
    Darpan is settled as 'amir_own_entry' -- a claim against a supplier for his own typing is the wrong record."""
    _ensure(cx)
    _s444_ensure(cx)
    ex = _s444_exports_for(cx, supplier_norm, bill_no, bill_date)
    paper, src = _s444_paper(cx, supplier_norm, bill_no, bill_date)
    cx.execute("INSERT OR REPLACE INTO amir_self_wait (supplier_norm, bill_no, bill_date, marked_at, marked_by, marg_p, paper_p, "
               "paper_src, export_md5, export_at, cleared_at, cleared_how) VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
               (supplier_norm, bill_no, bill_date, _stamp(), who, ex[0][0] if ex else None, paper, src,
                ex[0][2] if ex else None, ex[0][1] if ex else ""))
    n = 0
    for (cid, amt) in cx.execute("SELECT id, amount_p FROM amir_claim WHERE supplier_norm=? AND bill_no=? AND bill_date=? "
                                 "AND state <> 'settled'", (supplier_norm, bill_no, bill_date)).fetchall():
        cx.execute("UPDATE amir_claim SET state='settled', settled_outcome='amir_own_entry', settled_at=?, settled_by=? WHERE id=?",
                   (_stamp(), settled_by or who, cid))
        _s444_audit(cx, settled_by or who, "amir_claim_settled", "%s|%s|%s" % (supplier_norm, bill_no, bill_date),
                    {"claim": cid, "amount_p": amt, "outcome": "amir_own_entry", "kit": S444_KIT})
        n += 1
    _s444_audit(cx, who, "amir_self", "%s|%s|%s" % (supplier_norm, bill_no, bill_date),
                {"marg_p": ex[0][0] if ex else None, "paper_p": paper, "paper_src": src, "claims_settled": n, "kit": S444_KIT})
    return n


def _s444_self_clear(cx):
    """Every 'self' bill clears ITSELF when a LATER bill-wise export carries it at the paper's amount (+-Rs 1) -- with no
    scan, at an amount other than the one he flagged.  Audited once (the disposition becomes 'ok')."""
    try:
        _ensure(cx)
        _s444_ensure(cx)
        rows = cx.execute("SELECT w.supplier_norm, w.bill_no, w.bill_date, w.marg_p, w.paper_p, w.paper_src, w.export_at, d.reason "
                          "FROM amir_self_wait w LEFT JOIN amir_bill_disposition d ON d.supplier_norm = w.supplier_norm "
                          "AND d.bill_no = w.bill_no AND d.bill_date = w.bill_date WHERE w.cleared_at IS NULL").fetchall()
        changed = 0
        for sn, bno, bdt, marg0, paper0, src0, ex_at, reason in rows:
            if reason != "self":
                cx.execute("UPDATE amir_self_wait SET cleared_at=?, cleared_how=? WHERE supplier_norm=? AND bill_no=? AND bill_date=?",
                           (_stamp(), "answered %s" % (reason or "-"), sn, bno, bdt))
                changed += 1
                continue
            later = [e for e in _s444_exports_for(cx, sn, bno, bdt) if (e[1] or "") > (ex_at or "")]
            if not later:
                continue
            m = later[0][0]
            paper, _src = _s444_paper(cx, sn, bno, bdt)
            if paper is None:
                paper = paper0
            if paper is not None:
                ok, who = (m is not None and abs(int(m) - int(paper)) <= S444_TOL_P), "S444 auto: Marg = kaagaz"
            else:
                ok, who = (m is not None and marg0 is not None and int(m) != int(marg0)), "S444 auto: Marg ki rakam badli"
            if not ok:
                continue
            cx.execute("UPDATE amir_bill_disposition SET reason='ok', by_user=?, at=? WHERE supplier_norm=? AND bill_no=? AND bill_date=? "
                       "AND reason='self'", (who, _stamp(), sn, bno, bdt))
            cx.execute("UPDATE amir_self_wait SET cleared_at=?, cleared_how=? WHERE supplier_norm=? AND bill_no=? AND bill_date=?",
                       (_stamp(), "auto", sn, bno, bdt))
            _s444_audit(cx, who, "amir_self_cleared", "%s|%s|%s" % (sn, bno, bdt),
                        {"marg_p": m, "paper_p": paper, "flagged_marg_p": marg0, "export": later[0][2], "kit": S444_KIT})
            changed += 1
        if changed:
            cx.commit()
        return changed
    except Exception:                                                  # noqa: BLE001
        return 0


# ---- the salt list (F-671): owed while salt ticks are newer than the last VERIFIED list ----
def _s444_salt(cx):
    out = {"pending": False, "ticks": 0, "last_list": None, "oldest_tick": None, "days": None, "owed_days": None}
    try:
        lists = []
        if _table_exists(cx, "mi_file"):
            for r in cx.execute("SELECT stamp, received_at FROM mi_file WHERE type=? AND verdict='VERIFIED'", (SALT_LIST_TYPE,)).fetchall():
                t = _norm_ts(r[1]) or _norm_ts(r[0])
                if t:
                    lists.append(t)
        last = max(lists) if lists else None
        ticks = []
        if _table_exists(cx, "purchase_salt_task"):
            for r in cx.execute("SELECT done_at FROM purchase_salt_task WHERE COALESCE(done,0)=1 AND done_at IS NOT NULL").fetchall():
                t = _norm_ts(r[0])
                if t and (last is None or t > last):
                    ticks.append(t)
        out["last_list"] = last
        if ticks:
            today = _today()
            first = min(ticks)
            out.update(pending=True, ticks=len(ticks), oldest_tick=first,
                       days=(datetime.strptime(today, "%Y-%m-%d") - datetime.strptime((last or first)[:10], "%Y-%m-%d")).days,
                       owed_days=(datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(first[:10], "%Y-%m-%d")).days)
    except Exception:                                                  # noqa: BLE001
        pass
    return out


def _s444_salt_card(w, close=False):
    s = (w.get("s444") or {}).get("salt") or {}
    if not s.get("pending"):
        return ""
    last = ("aakhri list %s ki" % _dm_hm(s["last_list"])) if s.get("last_list") else "abhi tak koi list nahi aayi"
    return ("<div class=card id=s444salt style='border:2px solid var(--bad);background:#fff4f4'>"
            "<p class='big bad'>Ek export aur: SALT WISE ITEM LIST &mdash; Excel mein (text nahi)</p>"
            "<p>Marg se SALT WISE ITEM LIST nikaalo &mdash; yahan khud tick ho jayegi. <b>Excel</b> mein nikaaliye: "
            "text file server nahi padhta.</p>"
            "<p class=sub>%d salt kaam tick hue, list %d din se nahi aayi &middot; %s.</p>%s</div>"
            % (int(s.get("ticks") or 0), int(s.get("days") or 0), _esc(last),
               ("<p class=sub><b>Aaj nahi aayi to Shavez kal subah nikalega.</b> Din band karne se nahi rukta.</p>" if close else "")))


# ---- the count's vouchers and the renames (F-672): read from stock_app, which owns them ----
def _s444_duties(cx):
    try:
        import stock_app                                               # noqa: PLC0415 -- beside this file; loaded by finance_app
        return stock_app.amir_duties(cx)
    except Exception:                                                  # noqa: BLE001
        return {"counts": [], "renames": None}


def _s444_state(cx, day):
    d = _s444_duties(cx)
    return {"counts": [c for c in d.get("counts") or [] if c.get("open")], "renames": d.get("renames"), "salt": _s444_salt(cx)}


def _s444_open(w):
    s = w.get("s444") or {}
    rn = s.get("renames") or {}
    return bool(s.get("counts")) or bool(rn.get("ready") and rn.get("open"))


def _s444_card(w, top=False):
    """(a) Stock voucher, (b) Naam badlo -- each line gone when its work is done; on step 6 the salt work follows as (c)."""
    s = w.get("s444") or {}
    lines = []
    for c in s.get("counts") or []:
        lines.append("<div class=line><a class=btn href='%s'>Stock voucher baaki: %d orthotic, %d dawa &mdash; kholiye</a>"
                     "<span class=sub>Ginti #%d &middot; har voucher Marg mein daal kar uska number likhiye. "
                     "Din band karne se nahi rukta.</span></div>"
                     % (_esc(c["url"]), int(c["ortho"]), int(c["dawa"]), int(c["count_id"])))
    rn = s.get("renames") or {}
    if rn.get("ready") and rn.get("open"):
        lines.append("<div class=line><a class='btn plain' href='%s'>Naam badlo: %d naam Marg mein badalne hain &mdash; kholiye</a></div>"
                     % (_esc(rn["url"]), int(rn["open"])))
    if not lines:
        return ""
    return ("<div class=card id=s444duty style='border:2px solid var(--bad)'><h2 class=bad>%s</h2>%s</div>"
            % ("Marg sudhar &mdash; abhi baaki" if top else "Marg sudhar", "".join(lines)))


def _s444_left(w):
    s = w.get("s444") or {}
    out = []
    for c in s.get("counts") or []:
        out.append("%d stock vouchers of count #%d not entered in Marg (%d orthotic)" % (int(c["open"]), int(c["count_id"]), int(c["ortho"])))
    rn = s.get("renames") or {}
    if rn.get("ready") and rn.get("open"):
        out.append("%d renames to make in Marg" % int(rn["open"]))
    if (s.get("salt") or {}).get("pending"):
        out.append("SALT WISE ITEM LIST not received (Excel)")
    return out


def _s444_summary_rows(w):
    s = w.get("s444") or {}
    rows = []
    for c in s.get("counts") or []:
        rows.append("<div class=line>Stock voucher baaki: <b>%d orthotic, %d dawa</b> <span class=sub>(din band karne se nahi rukte)</span></div>"
                    % (int(c["ortho"]), int(c["dawa"])))
    rn = s.get("renames") or {}
    if rn.get("ready") and rn.get("open"):
        rows.append("<div class=line>Naam badlo: <b>%d</b></div>" % int(rn["open"]))
    return rows


def _s444_login():
    try:
        u, err = _require(*_roles, unit=_unit)
        return "" if err else str((u or {}).get("user") or (u or {}).get("username") or "")
    except Exception:                                                  # noqa: BLE001
        return ""


def _s444_who_line():
    who = _s444_login()
    return ("<p class=sub style='text-align:right;margin:0 0 6px'>Signed in: %s</p>" % _esc(who)) if who else ""


# ---- the owner's lines (sanjeevni_approvals' Needs-you hook) ----
def _s444_days_since(ts):
    t = _norm_ts(ts)
    if not t:
        return None
    try:
        return (datetime.strptime(_today(), "%Y-%m-%d") - datetime.strptime(t[:10], "%Y-%m-%d")).days
    except ValueError:
        return None


def _s444_ddmm(ts):
    t = _norm_ts(ts)
    return ("%s-%s" % (t[8:10], t[5:7])) if t else "-"


def _s444_voucher_line(cx):
    """(d) Count vouchers waiting -- untouched (board not opened by him, no voucher entered) for N of his visits."""
    out = []
    d = _s444_duties(cx)
    need = _s444_setting(cx, "amir.voucher_visits")
    for c in d.get("counts") or []:
        if not c.get("open"):
            continue
        since = max([x for x in (c.get("made_first"), c.get("last_touch")) if x] or [""])
        since = _norm_ts(since) or ""
        visits = [r[0] for r in cx.execute("SELECT day FROM amir_day WHERE opened_at IS NOT NULL AND opened_at > ? ORDER BY day",
                                           (since,)).fetchall()] if _table_exists(cx, "amir_day") else []
        if len(visits) >= need:
            out.append(dict(cls="warn", target="checks-marg",
                            text="Count vouchers waiting: %d (orthotic %d) -- Amir has not opened them in %d visits (%s), count #%d"
                                 % (int(c["open"]), int(c["ortho"]), len(visits), ", ".join(_s444_ddmm(v) for v in visits[-3:]), int(c["count_id"]))))
    return out


def _s444_duty_lines(cx):
    """The duty map's machine part: every ORPHAN duty (no door on the person's own home) whose owner line no code raises yet
    ('coded' empty) -- its due_sql run read-only; due longer than allowed_days -> one line.  A duty WITH a door is shown to its
    person on their home (the staff-eye walk proves it) and is not repeated to the owner here.  A missing map is silence; an
    unreadable one is one grey line."""
    import sqlite3                                                     # noqa: PLC0415 -- the read-only door for the map's queries
    path = os.environ.get("DUTY_MAP_JSON") or S444_DUTY_MAP
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
        duties = list(m.get("duties") or [])
    except Exception as e:                                             # noqa: BLE001
        return [dict(cls="info", target="checks-marg", text="The duty map (DUTY_MAP.json) could not be read: %s" % str(e)[:80])]
    try:
        dbfile = [r[2] for r in cx.execute("PRAGMA database_list").fetchall() if r[1] == "main"][0]
    except Exception:                                                  # noqa: BLE001
        dbfile = ""
    if not dbfile:
        return []
    out = []
    ro = sqlite3.connect("file:%s?mode=ro" % dbfile, uri=True, timeout=5)
    try:
        people = m.get("people") or {}
        for du in duties:
            sql = str(du.get("due_sql") or "").strip().rstrip(";").strip()
            if du.get("coded") or (du.get("door") and du.get("raise") is not True) or not du.get("owner_line") or not sql:
                continue
            if not re.match(r"(?is)^(select|with)\b", sql) or ";" in sql:
                continue
            try:
                r = ro.execute(sql).fetchone()
                n = int((r[0] if r else 0) or 0)
                since = r[1] if (r is not None and len(r) > 1) else None
            except Exception:                                          # noqa: BLE001
                continue
            if n <= 0:
                continue
            days = _s444_days_since(since) if since else None
            try:
                allowed = int(du.get("allowed_days") or 0)
            except (TypeError, ValueError):
                allowed = 0
            if days is not None and days < allowed:
                continue
            try:
                text = str(du["owner_line"]).format(n=n, days=(days if days is not None else "?"), since=_s444_ddmm(since) if since else "-",
                                                    person=people.get(du.get("person"), du.get("person") or ""))
            except Exception:                                          # noqa: BLE001
                text = "%s: %d due (%s)" % (du.get("duty") or du.get("id"), n, people.get(du.get("person"), du.get("person") or ""))
            out.append(dict(cls="warn", target="checks-marg", text=text, duty=du.get("id")))
    finally:
        ro.close()
    return out


def _s444_refused_lines(cx):
    """A report refused TODAY, named the same day (the door's own refusals; the medical PC's refused texts stay on the PC
    and in Drive, which this server does not read)."""
    out = []
    if not _table_exists(cx, "mi_file"):
        return out
    seen = set()
    for typ, verdict, reason, pcv, at in cx.execute(
            "SELECT type, verdict, reason, pc_verdict, received_at FROM mi_file WHERE substr(received_at,1,10)=? "
            "AND (verdict <> 'VERIFIED' OR COALESCE(pc_verdict,'') = 'REFUSED') ORDER BY received_at", (_today(),)).fetchall():
        k = (typ or "?", _hhmm(at))
        if k in seen:
            continue
        seen.add(k)
        why = (reason or "").strip() or (("the medical PC refused it (%s)" % pcv) if pcv else (verdict or ""))
        out.append(dict(cls="warn", target="checks-marg",
                        text="Report refused today: %s at %s -- %s (Shavez / Amir to export it again)" % (typ or "unknown file", _hhmm(at), why[:120])))
    return out


def needs_you_lines(con):
    """S444 (D647): the owner's Needs-you lines -- English, each with who and since when, each gone by itself when put right."""
    out = []
    try:
        _ensure(con)
        _s444_ensure(con)
        _s444_self_clear(con)
        # (a) the salt list owed
        s = _s444_salt(con)
        if s.get("pending") and (s.get("owed_days") or 0) >= _s444_setting(con, "amir.salt_owed_days"):
            out.append(dict(cls="warn", target="checks-marg",
                            text="Salt list not received for %d days -- %d salt corrections unproven (Amir / Shavez; owed since %s)"
                                 % (int(s.get("days") or 0), int(s.get("ticks") or 0), _s444_ddmm(s.get("oldest_tick")))))
        # (b) his own correction not yet seen in Marg
        need = _s444_setting(con, "amir.self_exports")
        for sn, bno, bdt, sup, marked, ex_at in con.execute(
                "SELECT w.supplier_norm, w.bill_no, w.bill_date, (SELECT MAX(supplier) FROM purchase_bill b WHERE b.supplier_norm=w.supplier_norm), "
                "w.marked_at, w.export_at FROM amir_self_wait w JOIN amir_bill_disposition d ON d.supplier_norm=w.supplier_norm "
                "AND d.bill_no=w.bill_no AND d.bill_date=w.bill_date AND d.reason='self' WHERE w.cleared_at IS NULL ORDER BY w.marked_at").fetchall():
            n = con.execute("SELECT COUNT(DISTINCT md5) FROM purchase_export WHERE type='BILLWISE' AND received_at > ?", (ex_at or "",)).fetchone()[0]
            if n >= need:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Amir's own correction on %s bill %s (%s) not yet seen in Marg after %d exports (marked %s)"
                                     % (sup or sn, bno, _s444_ddmm(bdt), n, _s444_ddmm(marked))))
        # (c) Darpan's claims open too long
        days_c = _s444_setting(con, "amir.claim_open_days")
        for cid, sup, bno, amt, raised, by in con.execute("SELECT id, supplier, bill_no, amount_p, raised_at, raised_by FROM amir_claim "
                                                          "WHERE state <> 'settled' ORDER BY raised_at").fetchall():
            dd = _s444_days_since(raised)
            if dd is not None and dd >= days_c:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Claim for Darpan open %d days: %s bill %s Rs %s (raised by %s %s)" % (dd, sup or "-", bno, _s444_rs(amt), by or "-", _s444_ddmm(raised))))
        # (d) the count vouchers
        out.extend(_s444_voucher_line(con))
        # the duty map's orphan duties, and a report refused today
        out.extend(_s444_duty_lines(con))
        out.extend(_s444_refused_lines(con))
    except Exception:                                                  # noqa: BLE001
        return out
    return out
# ---- S444_STAFF_SAFE end --------------------------------------------------------------------------------------------------------
