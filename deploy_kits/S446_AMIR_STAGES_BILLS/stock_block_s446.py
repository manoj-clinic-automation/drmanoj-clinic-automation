


# ---- S446_AMIR_STAGES_BILLS begin (02-Oct-2026, D649 / F-679): the count as GATED STAGES for Amir -----------------------------------
# The owner, 01-Oct: "Amir first does the orthotic stock issue and receive vouchers; you cross-check and verify the uploaded report;
# after that you give him the orthotic renaming list; then he renames ... When that is complete and verified, we move on to the
# remaining stock vouchers." Nothing of a later stage is shown to Amir before the earlier one is VERIFIED -- by the server's own
# proof (S304's drift test, here over one stage's lines only), never by a tap. The owner and the checkers see everything, as before.
#   A  the orthotic vouchers (every batch carrying an Orthotics line), ISSUE first, numbered 1..N on his board
#   B  the orthotic renames (S404/S437's list) -- verified when Marg's own export shows every new name (item_alias)
#   C  the medicine and consumable vouchers, `amir.vouchers_per_visit` (5) at a time, oldest round first; the next lot is released
#      when the lot is verified on a closing-stock export, or after 2 of his visits; an unverified lot stays listed, its wrong items named
_S446_PROOF_CACHE = {}                                          # (root, keys, entered stamp) -> (time, proof)


def _s446_ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS stock_stage_event (id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL, stage TEXT NOT NULL, "
                "event TEXT NOT NULL, ref TEXT, at TEXT NOT NULL, detail TEXT)")


def _s446_setting(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return int(r[0]) if r and str(r[0]).strip() else default
    except Exception:                                          # noqa: BLE001
        return default


def _s446_key(k):
    return "%d|%s|%d" % (int(k[0]), k[1], int(k[2]))


def _s446_unkey(s):
    a, b, c = str(s).split("|")
    return (int(a), b, int(c))


def _s446_batches(con, root):
    """{(round, kind, batch): {secs, lines: [(item, change, marg_to)], made}} for one count."""
    _voucher_ensure(con)
    out = {}
    for rno, kind, bno, sec, item, ch, mto, made in con.execute(
            "SELECT round_no, kind, batch_no, section, item, change, marg_to, made_at FROM stock_voucher_line WHERE count_id=? "
            "ORDER BY round_no, kind, batch_no, line_no", (root,)):
        b = out.setdefault((rno, kind, bno), dict(secs=set(), lines=[], made=made))
        b["secs"].add(sec or "")
        b["lines"].append((item, int(ch or 0), int(mto or 0)))
    return out


def _s446_entered(con, root):
    """{key: (marg_voucher_no, at)} -- the newest row of a batch wins; an empty number clears it (S301's rule)."""
    ent = {}
    for r in con.execute("SELECT round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered WHERE count_id=? ORDER BY id", (root,)):
        k = (r[0], r[1], r[2])
        if (r[3] or "").strip():
            ent[k] = (r[3], r[4])
        else:
            ent.pop(k, None)
    return ent


def _s446_order(keys):
    """ISSUE before RECEIVE, oldest round first, batch by batch -- the order he keys them."""
    return sorted(keys, key=lambda k: (k[1] != "ISSUE", k[0], k[2]))


def _s446_proof(con, root, keys, ent, batches):
    """S304's proof over THESE batches' lines only: wait (not all entered) | export (all entered, no Marg export after the last) |
    done (every item moved by exactly its vouchers) | wrong (rows named). Cached 5 minutes per (keys, entered stamps)."""
    keys = list(keys)
    if not keys or any(k not in ent for k in keys):
        return dict(state="wait", rows=[], text="")
    stamp = tuple(sorted((_s446_key(k), ent[k][1]) for k in keys))
    try:
        fstamp = con.execute("SELECT MAX(received_at), COUNT(*) FROM stock_feed").fetchone()      # a new export re-asks at once
    except Exception:                                          # noqa: BLE001
        fstamp = None
    ck = (root, stamp, tuple(fstamp) if fstamp else None)
    now = dt.datetime.now().timestamp()
    hit = _S446_PROOF_CACHE.get(ck)
    if hit and now - hit[0] < 300:
        return hit[1]
    need, vno = {}, {}
    for k in keys:
        for item, ch, _mto in batches[k]["lines"]:
            need[item] = need.get(item, 0) + ch
            vno.setdefault(item, []).append(k)
    first_at = min(ent[k][1] for k in keys)[:10]
    last_at = max(ent[k][1] for k in keys)[:19]
    feeds = _feed_latest(con)
    days = sorted({k[0] for k in feeds}, key=_proof_day_key)
    both = [x for x in days if (x, "marg") in feeds and (x, "expected") in feeds
            and _proof_pur_to(feeds[(x, "expected")]["source"]) >= _proof_day_key(x)]
    fk = first_at.replace("-", "")
    before = [x for x in both if _proof_day_key(x) < fk]
    after = [x for x in both if _proof_day_key(x) >= last_at[:10].replace("-", "") and feeds[(x, "marg")]["received_at"][:19] > last_at]
    if not before or not after:
        res = dict(state="export", rows=[], last_at=last_at,
                   text=("" if before else "no Marg export with our own figures before the vouchers"))
    else:
        R, L = before[-1], after[0]
        if _proof_basis(feeds[(R, "expected")]["source"]) != _proof_basis(feeds[(L, "expected")]["source"]):
            res = dict(state="export", rows=[], last_at=last_at, text="re-based between %s and %s" % (R, L))
        else:
            mR, eR, mL, eL = feeds[(R, "marg")]["items"], feeds[(R, "expected")]["items"], feeds[(L, "marg")]["items"], feeds[(L, "expected")]["items"]
            rows = []
            for item in sorted(need):
                if item not in mR or item not in eR or item not in mL or item not in eL:
                    rows.append(dict(item=item, need=need[item], moved=None, marg=mL.get(item), should=None, ok=False, keys=[_s446_key(k) for k in vno[item]]))
                    continue
                moved = (mL[item] - eL[item]) - (mR[item] - eR[item])
                ok = moved == need[item]
                rows.append(dict(item=item, need=need[item], moved=moved, marg=mL[item], should=mL[item] + (need[item] - moved), ok=ok,
                                 keys=[_s446_key(k) for k in vno[item]]))
            wrong = [r for r in rows if not r["ok"]]
            res = dict(state=("done" if not wrong else "wrong"), rows=wrong, as_before=R, as_after=L, last_at=last_at, items=len(rows))
    _S446_PROOF_CACHE[ck] = (now, res)
    return res


def _s446_event(con, root, stage, event, ref=None):
    r = con.execute("SELECT at FROM stock_stage_event WHERE count_id=? AND stage=? AND event=? AND COALESCE(ref,'')=?",
                    (root, stage, event, ref or "")).fetchone()
    return r[0] if r else None


def _s446_mark(con, root, stage, event, ref=None, detail=None):
    if _s446_event(con, root, stage, event, ref):
        return False
    con.execute("INSERT INTO stock_stage_event (count_id, stage, event, ref, at, detail) VALUES (?,?,?,?,?,?)",
                (root, stage, event, ref or "", now_iso(), detail))
    con.commit()
    return True


def _s446_visits_since(con, at):
    try:
        return [r[0] for r in con.execute("SELECT day FROM amir_day WHERE opened_at IS NOT NULL AND opened_at > ? ORDER BY day",
                                          (str(at or "").replace("T", " ")[:19],)).fetchall()]
    except Exception:                                          # noqa: BLE001
        return []


def _s446_root(con):
    """The count whose vouchers Amir works: the newest root count that has voucher lines."""
    _voucher_ensure(con)
    r = con.execute("SELECT MAX(count_id) FROM stock_voucher_line").fetchone()
    return int(r[0]) if r and r[0] else None


def amir_stage(con, cid=None):
    """Where the count stands for Amir: {count_id, stage A|B|C|done, A, B, C, visible (keys his board lists), renames_visible,
    numbers {key: n}}. Writes only stock_stage_event (a verification seen, a lot released) -- once each."""
    _s446_ensure(con)
    root = int(cid) if cid else _s446_root(con)
    if not root:
        return None
    batches = _s446_batches(con, root)
    if not batches:
        return None
    ent = _s446_entered(con, root)
    ortho = _s446_order([k for k, b in batches.items() if "Orthotics" in b["secs"]])
    med = sorted([k for k in batches if k not in set(ortho)], key=lambda k: (k[0], k[1] != "ISSUE", k[2]))   # oldest round first
    out = dict(count_id=root, stage="A", visible=[], renames_visible=False, numbers={})
    # ---- A
    a_open = [k for k in ortho if k not in ent]
    A = dict(total=len(ortho), entered=len(ortho) - len(a_open), open=len(a_open), proof=None, verified_at=_s446_event(con, root, "A", "verified"))
    if ortho and not a_open and not A["verified_at"]:
        A["proof"] = _s446_proof(con, root, ortho, ent, batches)
        if A["proof"]["state"] == "done" and _s446_mark(con, root, "A", "verified", detail=A["proof"].get("as_after")):
            A["verified_at"] = _s446_event(con, root, "A", "verified")
    out["A"] = A
    if not A["verified_at"] and ortho:
        out["visible"] = ortho
        out["numbers"] = {_s446_key(k): i + 1 for i, k in enumerate(ortho)}
        return out
    # ---- B
    out["stage"] = "B"
    B = dict(total=0, verified=0, ticked=0, open=[], old=[], verified_at=_s446_event(con, root, "B", "verified"))
    try:
        import item_alias                                      # noqa: PLC0415
        rows = item_alias.rows(con)
        B["total"] = len(rows)
        B["verified"] = sum(1 for r in rows if r.get("state") == "verified")
        B["ticked"] = sum(1 for r in rows if r.get("state") in ("done", "amber", "verified"))
        B["open"] = [r["old_name"] for r in rows if r.get("state") == "planned"]
        B["old"] = [r["old_name"] for r in rows if r.get("state") == "amber"]
        if rows and B["verified"] == len(rows) and not B["verified_at"] and _s446_mark(con, root, "B", "verified"):
            B["verified_at"] = _s446_event(con, root, "B", "verified")
    except Exception:                                          # noqa: BLE001
        pass
    out["B"] = B
    if not B["verified_at"]:
        out["renames_visible"] = True
        return out
    # ---- C
    out["stage"] = "C"
    per = max(1, _s446_setting(con, "amir.vouchers_per_visit", 5))
    lots = [dict(at=r[0], keys=[_s446_unkey(x) for x in (r[1] or "").split(",") if x]) for r in con.execute(
        "SELECT at, ref FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release' ORDER BY id", (root,))]
    released = {k for l in lots for k in l["keys"]}
    def release_next():
        nxt = [k for k in med if k not in released and k not in ent][:per]
        if nxt:
            _s446_mark(con, root, "C", "release", ",".join(_s446_key(k) for k in nxt))
            lots.append(dict(at=now_iso(), keys=nxt))
            released.update(nxt)
    if not lots:
        release_next()
    for l in lots:
        l["proof"] = _s446_proof(con, root, l["keys"], ent, batches) if all(k in ent for k in l["keys"]) else dict(state="wait", rows=[])
        l["verified"] = l["proof"]["state"] == "done"
        if l["verified"]:
            _s446_mark(con, root, "C", "verified", ",".join(_s446_key(k) for k in l["keys"]))
    cur = lots[-1] if lots else None
    if cur and (cur["verified"] or len(_s446_visits_since(con, cur["at"])) >= 2):
        before = len(lots)
        release_next()
        if len(lots) > before:
            lots[-1]["proof"], lots[-1]["verified"] = dict(state="wait", rows=[]), False
    vis = [k for l in lots if not l["verified"] for k in l["keys"]]
    C = dict(total=len(med), entered=sum(1 for k in med if k in ent), per=per,
             today=[k for k in (lots[-1]["keys"] if lots else []) if k not in ent],
             open=len([k for k in vis if k not in ent]), unreleased=len([k for k in med if k not in released and k not in ent]),
             waiting_export=[l for l in lots if not l["verified"] and l["proof"]["state"] == "export"],
             wrong=[r for l in lots if not l["verified"] for r in l["proof"].get("rows", [])],
             lot_at=(lots[-1]["at"] if lots else None), lots=len(lots))
    out["C"] = C
    out["visible"] = _s446_order(vis)
    out["numbers"] = {_s446_key(k): i + 1 for i, k in enumerate(out["visible"])}
    if not med or (C["entered"] == len(med) and not vis):
        out["stage"] = "done"
    return out


def _s446_board_filter(con, b, u):
    """For a login that is not the checker: the board lists only the stage's vouchers, numbered 1..N (ISSUE first), and the
    renames only in Stage B. The owner and the checkers see everything."""
    if _has_role(u, "checker"):
        return b
    try:
        st = amir_stage(con, b.get("count_id"))
    except Exception:                                          # noqa: BLE001
        st = None
    if not st:
        return b
    vis = {_s446_key(k) for k in st["visible"]}
    flat = (b.get("made") or {}).get("vouchers_flat") or []
    keep = []
    for v in flat:
        k = "%d|%s|%d" % (v["round_no"], v["kind"], v["batch_no"])
        if k in vis:
            v = dict(v, seq=st["numbers"].get(k, v["seq"]))
            v["title_hi"] = "%s — वाउचर %d" % (VOUCHER_HI.get(v["kind"], v["kind"]), v["seq"])
            v["title"] = "%s voucher %d" % (VOUCHER_HI.get(v["kind"], v["kind"]), v["seq"])
            keep.append(v)
    keep.sort(key=lambda v: v["seq"])
    if b.get("made") is not None:
        b["made"] = dict(b["made"], vouchers_flat=keep)
    b["renames_ready"] = bool(st.get("renames_visible"))
    if not b["renames_ready"]:
        b["renames_wait_hi"] = "नाम बदलना — orthotic voucher Marg में सही होने के बाद"
    b["stage"] = dict(stage=st["stage"], count_id=st["count_id"])
    return b
# ---- S446_AMIR_STAGES_BILLS end -------------------------------------------------------------------------------------------------------
