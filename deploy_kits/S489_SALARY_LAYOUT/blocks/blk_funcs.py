# =============================================================================
#  S489 (D681 / D682 -- the owner, 06-Oct-2026): HOW ADVANCES AND LOANS ARE SHOWN.
#
#  D681. On the month's money sheet advances are TWO tables that never mix:
#        "this month's advances" (taken and cut in full inside one salary) and
#        "instalment loans" -- ONE LINE PER PERSON PER LOAN, however many parts it was
#        handed over in: instalment, paid n of N, cut this month, balance, end month and
#        a month strip. One closing line per person: advances + instalment = cut this month.
#        A salary slip is printed only for a person with a running instalment loan.
#  D682. A person with a PRIVATE long-term loan (private_loan_staff -- Darpan) sits on the
#        common sheets at base LESS the loan's standing instalment; everything attendance
#        is still worked on the full base. The long-term loan and its instalment live only
#        on his own page, which is one loan-ledger table. A month the instalment is not
#        taken (skipped, deferred, held) changes ONLY that page: the common sheets still
#        read base-less-instalment and the amount kept aside is paid to him there.
#
#  NOTHING HERE MOVES MONEY. Every rupee is still the staff ledger's own (D349/D442):
#  these functions only sort the ledger's lines into what each sheet shows. The one
#  identity that must always hold, and that the walk proves on the box:
#        full net  ==  common-sheet net  +  paid to him on the private page
# =============================================================================
PRIVATE_LOAN_DEFAULT = "darpan"
LOAN_PAGES_PATH = os.path.join(BASE, "loan_pages.json")
INTEREST_FLAT = 1000.0          # D250's flat monthly interest; the ledger's own figure is used wherever it exists

_MON3 = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def private_loan_names(s=None):
    """Staff whose long-term loan is kept on a private page (D682). Lower-case names."""
    raw = str((s or {}).get("private_loan_staff", "") or "").strip()
    return {x.strip().lower() for x in (raw or PRIVATE_LOAN_DEFAULT).split(",") if x.strip()}


def _is_ym(x):
    return isinstance(x, str) and len(x) == 7 and x[4] == "-" and x[:4].isdigit() and x[5:].isdigit() \
        and 1 <= int(x[5:]) <= 12


def _num(x):
    """A plain number out of a record, or None (a bool, a text or a list is not a number)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return float(x)


def loan_pages(path=None):
    """The two small records Sheet 2 cannot read out of the ledger, kept in loan_pages.json
    beside this engine (written by the S489 kit, owner-ruled):
      groups  -- advances that are ONE loan handed over in parts:
                 [{"staff": name, "ids": [advance ids], "given": "14-17 Aug 2026"}]
      history -- a private loan's months BEFORE the ledger began:
                 {name: {"loan_id", "opening_date",
                         "pre": [{"ym", "kind": "skip" | "paid"}, ...],
                         "ledger_adjust": net of the ledger's own adjustment rows dated in those months}}
                 A 'paid' month is at the loan's standing terms unless it carries its own
                 "instalment" / "interest"; a 'skip' month adds "added" (default nothing). The
                 opening balance is worked back from the ledger unless the record states "opening".
    The record is CLEANED on the way in, and this never raises: history is keyed by the lower-case
    name; a group keeps only text ids, and an id belongs to the FIRST group that names it (so no
    advance can be counted twice); a month is listed once; anything malformed is dropped.
    Missing or unreadable -> both empty: every advance is then its own loan and the private page
    starts where the ledger starts, and says so."""
    out = {"groups": [], "history": {}}
    try:
        with open(path or LOAN_PAGES_PATH, encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        return out
    if not isinstance(j, dict):
        return out
    seen = set()
    for g in (j.get("groups") if isinstance(j.get("groups"), list) else []):
        if not isinstance(g, dict) or not isinstance(g.get("ids"), list) or not isinstance(g.get("staff"), str):
            continue
        ids = []
        for i in g["ids"]:
            if isinstance(i, str) and i and i not in seen:
                seen.add(i)
                ids.append(i)
        if ids:
            out["groups"].append({"staff": g["staff"], "ids": ids,
                                  "given": g["given"] if isinstance(g.get("given"), str) else ""})
    h = j.get("history")
    for k, v in (h.items() if isinstance(h, dict) else []):
        if not isinstance(k, str) or not k.strip() or not isinstance(v, dict):
            continue
        pre, months = [], set()
        for p in (v.get("pre") if isinstance(v.get("pre"), list) else []):
            if not isinstance(p, dict) or not _is_ym(p.get("ym")) or p.get("kind") not in ("skip", "paid") \
                    or p["ym"] in months:
                continue
            months.add(p["ym"])
            q = {"ym": p["ym"], "kind": p["kind"]}
            for f in ("added", "instalment", "interest"):
                if _num(p.get(f)) is not None:
                    q[f] = _num(p[f])
            pre.append(q)
        pre.sort(key=lambda p: p["ym"])
        rec = {"loan_id": v["loan_id"] if isinstance(v.get("loan_id"), str) else "",
               "opening_date": v["opening_date"] if isinstance(v.get("opening_date"), str) else "",
               "pre": pre}
        for f in ("opening", "ledger_adjust"):
            if _num(v.get(f)) is not None:
                rec[f] = _num(v[f])
        out["history"][k.strip().lower()] = rec
    return out


def loan_history(name, lp=None):
    """The history record of one person's private loan ({} when there is none), whatever the case of the name."""
    return dict(((lp or loan_pages()).get("history") or {}).get(str(name).strip().lower()) or {})


def inr(x):
    """1234567 -> '12,34,567' (Indian grouping). Paise, always two digits, only when there are any."""
    v = round(float(x or 0) + 1e-9, 2)
    neg = v < 0
    v = abs(v)
    whole = int(v)
    frac = round(v - whole, 2)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    if frac:
        s += ("%.2f" % frac)[1:]
    return ("-" if neg and (whole or frac) else "") + s


def _d_short(iso):
    """'2026-09-03' -> '3 Sep'."""
    try:
        return "%d %s" % (int(iso[8:10]), _MON3[int(iso[5:7])])
    except (ValueError, TypeError, IndexError):
        return str(iso or "")


def _m_short(ym):
    """'2026-09' -> 'Sep'."""
    try:
        return _MON3[int(ym[5:7])]
    except (ValueError, TypeError, IndexError):
        return str(ym or "")


def _given_words(parts):
    """When a loan was handed over: '17 Aug 2026', or '14-17 Aug 2026' for several parts."""
    ds = sorted(str(t.get("date", "")) for t in parts if t.get("date"))
    if not ds:
        return ""
    a, b = ds[0], ds[-1]
    if a == b:
        return "%s %s" % (_d_short(a), a[:4])
    if a[:7] == b[:7]:
        return "%d–%s %s" % (int(a[8:10]), _d_short(b), b[:4])
    return "%s – %s %s" % (_d_short(a), _d_short(b), b[:4])


def _inst_words(amounts):
    """How a loan is paid back, from its monthly amounts in order."""
    am = [round(a, 2) for a in amounts if a > 0.005]
    if not am:
        return "no instalment set"
    if len(set(am)) == 1:
        return "%s a month" % inr(am[0]) if len(am) > 1 else "%s in one go" % inr(am[0])
    if len(am) == 2:
        return "%s, then %s" % (inr(am[0]), inr(am[1]))
    if len(set(am[1:])) == 1:
        return "%s, then %s a month" % (inr(am[0]), inr(am[1]))
    if len(set(am[:-1])) == 1:
        return "%s a month, last %s" % (inr(am[0]), inr(am[-1]))
    return " · ".join(inr(a) for a in am)


def _loan_entry(members, ym, closed, label=None):
    """ONE loan, from the ledger lines that make it up (one line, or the parts of a group)."""
    members = sorted(members, key=lambda t: (str(t.get("date", "")), str(t.get("id", ""))))
    past, fut, marks = {}, {}, {}
    this = 0.0
    for t in members:
        for m, p, i in t.get("hist", []):
            if m < ym and p + i > 0.005:
                past[m] = round(past.get(m, 0.0) + p + i, 2)
        if closed:
            this += t["recovered"] + t["interest"]
        for m, p, i in t.get("proj", []):
            if p + i <= 0.005:
                continue
            if m == ym and not closed:
                this += p + i
            elif m > ym:
                fut[m] = round(fut.get(m, 0.0) + p + i, 2)
        for m, kind in (t.get("marks") or {}).items():
            if m <= ym:
                marks[m] = kind
    this = round(this, 2)
    strip = [(m, past[m], "paid") for m in sorted(past)]
    if this > 0.005:
        strip.append((ym, this, "paid" if closed else "now"))
    for m in sorted(marks):
        if m not in past and not (m == ym and this > 0.005):
            strip.append((m, 0.0, marks[m]))
    strip += [(m, fut[m], "due") for m in sorted(fut)]
    strip.sort(key=lambda x: x[0])
    n_paid = sum(1 for _m, _a, k in strip if k == "paid")
    n_all = sum(1 for _m, _a, k in strip if k in ("paid", "now", "due"))
    balance = round(sum(t["end"] for t in members), 2)
    if not closed:
        balance_after = round(balance - this, 2)
    else:
        balance_after = balance
    return {
        "ids": [t["id"] for t in members], "parts": members,
        "amount": round(sum(t["amount"] for t in members), 2),
        "given": label or _given_words(members),
        "first_date": str(members[0].get("date", "")) if members else "",
        "inst": _inst_words([a for _m, a, k in strip if k in ("paid", "now", "due")]),
        "paid": round(sum(past.values()) + (this if closed else 0.0), 2),
        "n_paid": n_paid, "n_all": n_all, "cut": this,
        "balance": balance, "balance_after": balance_after,
        "ends": (sorted(fut)[-1] if fut else (ym if balance_after <= 0.005 else "")),
        "next": fut.get(_ym_add(ym, 1), 0.0), "strip": strip,
        "unplanned": bool(balance_after > 0.005 and not fut),
        "late_month": any((t.get("against") or "") > str(t.get("date", ""))[:7]
                          and t.get("lane") == "quota" for t in members),
    }


def advance_views(lm, name, ym, closed, groups=None, private=False):
    """Sort ONE person's ledger lines (ledger_money) into what Sheet 2 shows.
      month_adv  -- taken and cut in full inside this one salary: [{id, date, amount, cut, bf}]
      loans      -- everything paid back over more than one salary, ONE entry per loan
      priv_lines -- the long-term loan's own lines (private staff only; never in the two above)
    Pure: reads only what ledger_money put on each line. Before the ledger close the 'cut'
    figures are what the close WILL take (the ledger's own projection), and say so."""
    out = {"month_adv": [], "loans": [], "priv_lines": []}
    if not lm:
        return out
    lines = list(lm.get("lines") or [])
    cleared = list(lm.get("cleared") or [])
    by_id = {t["id"]: t for t in cleared}
    by_id.update({t["id"]: t for t in lines})
    gmap = {}
    for gi, g in enumerate(groups or []):
        if str(g.get("staff", "")).strip().lower() != str(name).strip().lower():
            continue
        for i in (g.get("ids") or []):
            if i in by_id:
                gmap[i] = gi
    seen_groups = set()
    for t in lines:
        if private and t.get("private"):
            out["priv_lines"].append(t)
            continue
        gi = gmap.get(t["id"])
        if gi is not None:
            if gi in seen_groups:
                continue
            seen_groups.add(gi)
            g = groups[gi]
            members = [by_id[i] for i in (g.get("ids") or [])
                       if i in by_id and not (private and by_id[i].get("private"))]
            out["loans"].append(_loan_entry(members, ym, closed, label=g.get("given") or None))
            continue
        hist_before = [1 for m, p, i in t.get("hist", []) if m < ym and p + i > 0.005]
        proj_after = [1 for m, p, i in t.get("proj", []) if m > ym and p + i > 0.005]
        if closed:
            th = round(t["recovered"] + t["interest"], 2)
            left = t["end"]
        else:
            th = round(sum(p + i for m, p, i in t.get("proj", []) if m == ym), 2)
            left = round(t["end"] - th, 2)
        if not hist_before and not proj_after and th > 0.005 and left <= 0.005:
            out["month_adv"].append({"id": t["id"], "date": t.get("date", ""), "amount": t["amount"],
                                     "cut": th, "bf": bool(t.get("bf"))})
        elif t["start"] > 0 or t["taken"] > 0 or th > 0.005 or t["end"] > 0:
            out["loans"].append(_loan_entry([t], ym, closed))
    out["loans"].sort(key=lambda L: (L["first_date"], L["ids"]))
    out["month_adv"].sort(key=lambda a: (str(a["date"]), a["id"]))
    return out


def private_split(priv_lines, ym, closed):
    """D682: what the private page keeps aside from the month's salary, and what became of it.
    kept      -- the long-term loan's standing instalment (never more than is still owed)
    cut       -- what the ledger actually took for the long-term loan this month (principal + interest)
    paid      -- kept less cut: paid to him on the private page (0 in an ordinary month; the whole
                 instalment in a month it was skipped). None until the ledger month is closed.
    None when the person has no long-term loan open or moving this month."""
    live = [t for t in (priv_lines or [])
            if t["start"] > 0 or t["taken"] > 0 or t["end"] > 0 or t["recovered"] > 0 or t["interest"] > 0]
    if not live:
        return None
    head = live[0]                                   # interest loan first, then oldest (ledger_money's order)
    principal = round(sum(t["recovered"] for t in live), 2)
    interest = round(sum(t["interest"] for t in live), 2)
    cut = round(principal + interest, 2)
    owed = round(sum(t["start"] + t["taken"] for t in live), 2)
    int_due = interest if closed else (INTEREST_FLAT if any(t.get("interest_loan") and t["start"] > 0 for t in live) else 0.0)
    kept = round(min(float(head.get("inst") or 0.0), owed + int_due), 2)
    cut_shown = round(min(cut, kept), 2)
    mark = ""
    for t in live:
        mark = (t.get("marks") or {}).get(ym) or mark
    if not closed:
        status = "pending"
    elif cut_shown >= kept - 0.005:
        status = "paid"
    elif mark:
        status = mark
    elif cut_shown > 0.005:
        status = "part"
    else:
        status = "none"
    return {"kept": kept, "cut": cut, "cut_shown": cut_shown, "extra": round(cut - cut_shown, 2),
            "paid": (round(kept - cut_shown, 2) if closed else None),
            "reserve": round(kept - cut_shown, 2) if closed else kept,
            "principal": principal, "interest": interest, "status": status,
            "owed_after": round(sum(t["end"] for t in live), 2), "lines": live}


def fy_of_ym(ym):
    """'2026-09' -> 2026 (the Indian financial year April-March it falls in, by its first year)."""
    y, m = int(ym[:4]), int(ym[5:7])
    return y if m >= 4 else y - 1


def loan_ledger(t, hist, ym, closed):
    """The private page's one table for ONE loan line: a row per salary month.
    Months before the ledger began come from loan_pages.json (history); every later month is
    the ledger's own rows. Returns (rows, opening, note). A row:
      {ym, start, inst, interest, principal, added, end, status, src}
      status: paid | part | skip | defer | hold | pending | none | next
    The opening balance is the record's own when it states one; otherwise it is worked BACK from
    the ledger: the ledger's balance where the history ends, plus what the history's months paid
    off. note is non-empty when the history and the ledger do not meet at the join, when the
    ledger's own adjustment for the history's months is not the one the record was written for,
    or when the table's last balance is not the ledger's -- the page then SAYS so; it never
    papers over."""
    rows, note = [], ""
    hist = hist or {}
    caps = list(t.get("caps") or [])
    hh = list(t.get("hist") or [])
    marks = dict(t.get("marks") or {})
    inst_std = float(t.get("inst") or 0.0)
    int_std = INTEREST_FLAT if t.get("interest_loan") else 0.0
    pre, months = [], set()
    for p in sorted((p for p in (hist.get("pre") or []) if isinstance(p, dict) and _is_ym(p.get("ym"))),
                    key=lambda p: p["ym"]):
        if p["ym"] in months:
            continue
        months.add(p["ym"])
        if p.get("kind") == "skip":
            pre.append((p["ym"], "skip", 0.0, 0.0, float(_num(p.get("added")) or 0.0)))
        else:
            inst = _num(p.get("instalment"))
            intr = _num(p.get("interest"))
            inst = inst_std if inst is None else inst
            intr = min(int_std, inst) if intr is None else intr
            pre.append((p["ym"], "paid", inst, intr, 0.0))
    last_pre = pre[-1][0] if pre else ""
    coll = sorted(m for m, p, i in hh if p + i > 0.005)
    opening = None
    if pre:
        adj = round(sum(a for m, a in caps if m <= last_pre), 2)
        led_start = round(float(t["amount"]) + adj - sum(p for m, p, _i in hh if m <= last_pre), 2)
        back = round(sum(inst - intr for _m, k, inst, intr, _a in pre if k == "paid")
                     - sum(a for _m, k, _i, _n, a in pre if k == "skip"), 2)
        stated = _num(hist.get("opening"))
        opening = stated if stated is not None else round(led_start + back, 2)
        if abs((opening - back) - led_start) > 0.5:
            note = ("The months before the ledger end at Rs %s, but the ledger starts this loan at Rs %s "
                    "— a difference of Rs %s. The balances from %s on are the ledger's."
                    % (inr(opening - back), inr(led_start), inr(abs(opening - back - led_start)),
                       month_words(_ym_add(last_pre, 1))))
        want_adj = _num(hist.get("ledger_adjust"))
        if not note and want_adj is not None and abs(adj - want_adj) > 0.5:
            note = ("For the months before the ledger began, the ledger's own adjustment on this loan is Rs %s; "
                    "this page was written for Rs %s. The opening balance may be out by the difference — read "
                    "the ledger statement." % (inr(adj), inr(want_adj)))
        bal = opening
        for m, k, inst, intr, added in pre:
            if m > ym:
                break
            start = bal
            if k == "skip":
                bal = round(start + added, 2)
                rows.append({"ym": m, "start": start, "inst": 0.0, "interest": 0.0, "principal": 0.0,
                             "added": added, "end": bal, "status": "skip", "src": "history"})
            else:
                bal = round(start - (inst - intr), 2)
                rows.append({"ym": m, "start": start, "inst": inst, "interest": intr,
                             "principal": round(inst - intr, 2), "added": 0.0, "end": bal,
                             "status": "paid", "src": "history"})
        first = _ym_add(last_pre, 1)
        bal = led_start
    else:
        # no history record: the table starts where the LEDGER starts this loan. Anything the ledger
        # dates before that (a migrated loan's earlier skip mark or adjustment) is inside the opening.
        d0 = str(t.get("date", ""))[:7]
        first = min([m for m in ([d0] if _is_ym(d0) else []) + coll] or [ym])
        opening = round(float(t["amount"]) + sum(a for m, a in caps if m < first), 2)
        bal = opening
    m = first
    guard = 0
    while m <= ym and guard < 600:
        guard += 1
        p = round(sum(pp for mm, pp, _i in hh if mm == m), 2)
        i = round(sum(ii for mm, _p, ii in hh if mm == m), 2)
        c = round(sum(a for mm, a in caps if mm == m), 2)
        start = bal
        bal = round(start - p + c, 2)
        if p + i > 0.005:
            status = "paid" if (p + i) >= inst_std - 0.005 or bal <= 0.005 else "part"
        elif marks.get(m):
            status = marks[m]
        elif m == ym and not closed:
            status = "pending"
        else:
            status = "none"
        rows.append({"ym": m, "start": start, "inst": round(p + i, 2), "interest": i, "principal": p,
                     "added": c, "end": bal, "status": status, "src": "ledger"})
        m = _ym_add(m, 1)
    if ym >= first and abs(bal - float(t["end"])) > 0.5 and not note:
        note = ("This table ends at Rs %s but the ledger's balance for the month is Rs %s — read the "
                "ledger statement; one of its rows is not on this table." % (inr(bal), inr(t["end"])))
    nxt = [(mm, p, i) for mm, p, i in (t.get("proj") or []) if mm > ym and p + i > 0.005]
    if closed and nxt and float(t["end"]) > 0.005:     # before the close the month itself is still to come
        mm, p, i = nxt[0]
        rows.append({"ym": mm, "start": float(t["end"]), "inst": round(p + i, 2), "interest": i, "principal": p,
                     "added": 0.0, "end": round(float(t["end"]) - p, 2), "status": "next", "src": "plan"})
    return rows, opening, note


def skips_in_fy(rows, ym):
    """Months of the financial year of `ym`, up to `ym`, in which the instalment was skipped or deferred."""
    fy = fy_of_ym(ym)
    return [r["ym"] for r in rows if r["status"] in ("skip", "defer") and r["ym"] <= ym and fy_of_ym(r["ym"]) == fy]


