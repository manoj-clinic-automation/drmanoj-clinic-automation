#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""patients_page.py -- kit S851_PATIENTS_PAGE (the parent, S474, 17-Nov-2026; D939). PARENT. NEW.

THE OWNER, 17-Nov-2026 12:01 IST: "build the analytics console which you had finalized few days ago" -- the Patients page of
his command console, mock-up v16 (https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA), the figures of the S433 study.

PART 1 (this kit): every block that the clinic's own record answers --
  the month at a glance · the reading-and-suggestions lines (fixed rules: the same figures always give the same words) ·
  month by month · new and seen-before, and who comes back within 30 days · the follow-ups he gave, in five states (kept / on
  medicines / came late / neither / still open) · by diagnosis group · back after a gap (the late returners) · how much the
  diagnoses cover, and the diagnosis words the taxonomy does not know.
PART 2 (kit S853, S477): patients_part2.read2() is called at the end of read(), inside a try -- the front desk (calls and
  WhatsApp), Google, the reviews, last year from his two Docterz exports, the "Called" columns. A fault there leaves Part 1 whole.

Pages (his login alone, the console's own gate -- unit 'packs'):
  /finance/console/patients             the page (patients_page.html beside this file)
  /finance/console/api/patients         the reading (aggregates only; built on request when older than MAX_AGE)
  /finance/console/api/patients/list    the patients behind one figure (name, clinic ID, the day) -- opened by a tap
Mounted by owner_console.init (S851). READ-ONLY on finance.db (mode=ro): it writes only its own reading file
patients_reading.dat beside this file (*.dat is in none of the nightly bundle's lists) and its lock.

Rules, from the S433 study (11/12-Nov-2026), unchanged:
  * NEW = a clinic ID above every ID seen on an earlier day (IDs are issued in order); patient_ref.first_seen is NOT used.
  * The diagnosis of a visit = dx_visit's category; a visit with none typed takes the same patient's nearest written one
    (earlier first, then later). Eight main groups; the small ones are "Other groups"; none at all = "No diagnosis typed".
  * Clinic rupees = clinic_day_line (consult + xray + proc) by clinic ID and day. Pharmacy = Sanjeevni bills tied to a clinic ID
    by the Patient Records page's own rule (verified by a person, or confidence >= 0.95; open identity disputes left out).
  * A follow-up = dx_visit.follow_up_date, counted in the month it falls due. Kept = a visit by the date or within 7 days after
    (an early visit counts). On medicines = no such visit, but a tied Sanjeevni bill on a day with no consultation, after the
    visit and up to 30 days past the date (before any later visit). Came late = a visit more than 7 days after the date.
    Still open = none of these and the date is less than 30 days old. Neither = the rest. Never closed as lost.
  * A percentage only where its base is >= 20; otherwise the count.
No patient name, number or ID is in this file (F-185).
"""
import datetime as dt
import json
import os
import re
import sqlite3
import time
from collections import Counter, defaultdict

VERSION = "S853 1.0"
FIN = os.path.dirname(os.path.abspath(__file__))
READING = os.environ.get("PATIENTS_READING", os.path.join(FIN, "patients_reading.dat"))
LOCK = READING + ".lock"
PAGE_FILE = os.path.join(FIN, "patients_page.html")
PAGE_URL = "/finance/console/patients"
MAX_AGE = 3600            # seconds: an older reading is rebuilt when the page asks (a build takes a few seconds)
LOCK_STALE = 120
FIRST_MONTH = "2026-07"   # June is left out (his ruling, S433)
MAIN = ("Rheumatology", "Degenerative Joint Disease", "Trauma", "Radicular Spine Disease", "Mechanical Spine",
        "Degenerative Spine", "General Orthopedics", "Foot & Ankle")
OTHER = "Other groups"
NONE = "No diagnosis typed"
GROUPS = MAIN + (OTHER, NONE)
KINDS = (("short", "Within a week"), ("review", "Planned review (8–30 d)"), ("long", "After a month"))
STATES = ("kept", "med", "late", "neither", "open")
MIN_BASE = 20

_db = _require = None
_unit = "packs"


def _md(p):
    return int(p or 0)


def D(s):
    return dt.date.fromisoformat(s)


def mlabel(ym):
    y, m = ym.split("-")
    return "%s %s" % (("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[int(m) - 1], y)


def mshort(ym):
    return mlabel(ym).split(" ")[0]


def dmy(iso):
    try:
        return D(iso).strftime("%d-%b")
    except (ValueError, TypeError):
        return str(iso or "–")


def months_between(a, b):
    out = []
    y, m = int(a[:4]), int(a[5:7])
    while "%04d-%02d" % (y, m) <= b:
        out.append("%04d-%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def pct(n, base):
    """'54%' where the base is >= 20, else 'n of base' -- a percentage of a handful misleads."""
    if not base:
        return "–"
    if base < MIN_BASE:
        return "%d of %d" % (n, base)
    return "%d%%" % round(100.0 * n / base)


def pct_num(n, base):
    return None if not base or base < MIN_BASE else round(100.0 * n / base)


def rupees(paise):
    p = int(round((paise or 0) / 100.0))
    neg, s = p < 0, str(abs(p))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("−₹" if neg else "₹") + s


# =================================================================================================== the reading (pure)
def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def read(con, today=None):
    """The whole reading from finance.db. Pure read. Returns (reading, lists): reading = aggregates only (what the page draws);
    lists = {key: [[clinic_id, day, note], ...]} -- the patients behind each figure, served only by a tap."""
    t0 = time.time()
    today = today or dt.date.today()
    q = lambda s, *a: con.execute(s, a).fetchall()                      # noqa: E731
    visits = [(r[0], r[1], str(r[2] or "").strip()) for r in q(
        "SELECT patient_uid, visit_date, clinic_id FROM patient_visit WHERE visit_date IS NOT NULL AND visit_date<>'' "
        "AND patient_uid IS NOT NULL AND patient_uid<>'' ORDER BY visit_date, patient_uid") if _okday(r[1])]
    if not visits:
        return dict(ok=False, why="no visits in the record"), {}
    END = D(max(v[1] for v in visits))
    START = D(min(v[1] for v in visits))
    byp = defaultdict(list)
    cid_of = {}
    for u, d, cid in visits:
        if not byp[u] or byp[u][-1] != d:
            byp[u].append(d)
        cid_of[u] = cid
    uid_of = {}
    for u, d, cid in visits:
        uid_of[cid] = u
    vset = {u: set(ds) for u, ds in byp.items()}
    # -- diagnoses and follow-up dates
    dx = {}
    if _has(con, "dx_visit"):
        for u, d, cat, f in q("SELECT patient_uid, substr(visit_date,1,10), category, follow_up_date FROM dx_visit"):
            dx[(u, d)] = ((cat or "").strip(), (f or "").strip()[:10])
    written = {u: [d for d in ds if dx.get((u, d), ("", ""))[0]] for u, ds in byp.items()}

    def eff(u, d):
        o = dx.get((u, d))
        if o and o[0]:
            return o[0], "own"
        w = written.get(u) or []
        prev = [x for x in w if x < d]
        if prev:
            return dx[(u, prev[-1])][0], "carried"
        nxt = [x for x in w if x > d]
        if nxt:
            return dx[(u, nxt[0])][0], "carried"
        return NONE, "none"

    def grp(u, d):
        g = eff(u, d)[0]
        return g if g in MAIN or g == NONE else OTHER

    # -- new = a clinic ID above every ID seen on an earlier day
    firstday = {}
    mx = 0
    cur = None
    daymax = 0
    for u, d, cid in visits:
        n = int(re.sub(r"\D", "", cid) or 0)
        if d != cur:
            mx = max(mx, daymax)
            cur = d
            daymax = 0
        daymax = max(daymax, n)
        if n > mx and u not in firstday:
            firstday[u] = d
    # -- the day sheet's money and free revisits by (clinic ID, day)
    rev = defaultdict(Counter)
    if _has(con, "clinic_day_line"):
        for d, cid, sec, amt in q("SELECT business_date, clinic_id, section, amount_p FROM clinic_day_line"):
            rev[(str(cid or "").strip(), d)][sec] += _md(amt)
            if sec in ("revisit", "concession"):
                rev[(str(cid or "").strip(), d)]["n_" + sec] += 1
    # -- Sanjeevni bills tied to a clinic ID (the Patient Records rule)
    bills = defaultdict(Counter)       # uid -> day -> paise
    bills_month = Counter()
    tied_month = Counter()
    if _has(con, "sale_item") and _has(con, "patient_ref") and _has(con, "day_entry"):
        disp = set()
        if _has(con, "identity_dispute"):
            disp = {(str(c or ""), str(b or "")) for c, b in q("SELECT clinic_id, bill_no FROM identity_dispute WHERE status='open'")}
        for cid, day, amt, bill, conf, ver in q(
                "SELECT p.clinic_id, d.business_date, s.amount_p, s.source_ref, s.confidence, COALESCE(s.verified_by,'') "
                "FROM sale_item s JOIN patient_ref p ON p.id=s.patient_ref_id JOIN day_entry d ON d.id=s.day_entry_id "
                "WHERE s.service='pharmacy'"):
            cid = str(cid or "").strip()
            bills_month[str(day)[:7]] += 1
            if not re.fullmatch(r"\d+", cid) or (cid, str(bill or "")) in disp or not (ver or (conf or 0) >= 0.95):
                continue
            tied_month[str(day)[:7]] += 1
            u = uid_of.get(cid)
            if u:
                bills[u][str(day)] += _md(amt)

    lists = {}

    def put(key, rows):
        lists[key] = rows

    months = months_between(FIRST_MONTH, END.isoformat()[:7])
    month_end = END.isoformat()[:7]

    def gap_next(u, d):
        ds = byp[u]
        i = ds.index(d)
        return (D(ds[i + 1]) - D(d)).days if i + 1 < len(ds) else None

    # ------------------------------------------------------------------ month by month
    mrows = []
    for m in months:
        vs = [(u, d, cid) for u, d, cid in visits if d[:7] == m]
        pats = {u for u, _, _ in vs}
        new = {u for u in pats if firstday.get(u, "")[:7] == m}
        days = len({d for _, d, _ in vs})
        r = Counter()
        free = 0
        once = set()
        for u, d, cid in vs:
            if (cid, d) in once:                      # the day's money once, however many visit rows carry it
                continue
            once.add((cid, d))
            for k in ("consult", "xray", "proc"):
                r[k] += rev[(cid, d)][k]
            if rev[(cid, d)]["n_revisit"]:
                free += 1
        medrows, medp, medr = [], set(), 0
        for u, dd in bills.items():
            for day, amt in dd.items():
                if day[:7] == m and day not in vset[u]:
                    medrows.append([cid_of[u], day, "medicines, no consultation that day"])
                    medp.add(u)
                    medr += amt
        put("m:%s:patients" % m, sorted([[cid_of[u], max(d for d in byp[u] if d[:7] == m), ""] for u in pats], key=lambda x: x[1], reverse=True))
        put("m:%s:new" % m, sorted([[cid_of[u], firstday[u], "first visit"] for u in new], key=lambda x: x[1], reverse=True))
        put("m:%s:med" % m, sorted(medrows, key=lambda x: x[1], reverse=True))
        tot = r["consult"] + r["xray"] + r["proc"]
        mrows.append(dict(ym=m, month=mshort(m), label=mlabel(m), partial=(m == month_end), days=days, patients=len(pats),
                          new=len(new), visits=len(vs), vpd=round(len(vs) / days, 1) if days else 0,
                          vpp=round(len(vs) / len(pats), 2) if pats else 0, revisits=free, med=len(medrows), med_patients=len(medp),
                          med_rs=medr, consult=r["consult"], xray=r["xray"], proc=r["proc"], total=tot,
                          tied_share=pct(tied_month[m], bills_month[m]) if bills_month[m] else "–"))

    # ------------------------------------------------------------------ do they come back within 30 days (matured visits only)
    back = []
    for m in months:
        newv = [(u, d) for u, d, _ in visits if d[:7] == m and firstday.get(u) == d and (END - D(d)).days >= 30]
        oldv = [(u, d) for u, d, _ in visits if d[:7] == m and firstday.get(u) != d and (END - D(d)).days >= 30]
        allm = [(u, d) for u, d, _ in visits if d[:7] == m]

        def share(vv, lo, hi):
            g = [gap_next(u, d) for u, d in vv]
            return sum(1 for x in g if x is not None and lo <= x <= hi)
        back.append(dict(ym=m, month=mshort(m), n_new=len(newv), n_old=len(oldv), all=len(allm),
                         n7=pct(share(newv, 0, 7), len(newv)), n30=pct(share(newv, 8, 30), len(newv)),
                         o7=pct(share(oldv, 0, 7), len(oldv)), o30=pct(share(oldv, 8, 30), len(oldv)),
                         o30_num=pct_num(share(oldv, 8, 30), len(oldv)),
                         matured_all=(len(newv) + len(oldv)) == len(allm)))

    # ------------------------------------------------------------------ follow-ups by the month they fall due
    fu = defaultdict(Counter)                         # (due month, kind) -> state counts
    fug = defaultdict(Counter)                        # (due month, group) -> state counts
    fulist = defaultdict(list)
    for (u, d), (cat, f) in dx.items():
        if not f or f <= d or u not in byp or not re.fullmatch(r"\d{4}-\d\d-\d\d", f):
            continue
        if not _okday(f):
            continue
        due = D(f)
        adv = (due - D(d)).days
        kind = "short" if adv <= 7 else "review" if adv <= 30 else "long"
        later = [D(x) for x in byp[u] if x > d]
        if any(x <= due + dt.timedelta(days=7) for x in later):
            st = "kept"
        else:
            came = [x for x in later if x > due + dt.timedelta(days=7)]
            med = [D(x) for x in bills.get(u, {}) if x > d and x not in vset[u] and D(x) <= due + dt.timedelta(days=30)
                   and (not came or D(x) < came[0])]
            if med:
                st = "med"
            elif came:
                st = "late"
            elif (END - due).days < 30:
                st = "open"
            else:
                st = "neither"
        m = f[:7]
        g = grp(u, d)
        fu[(m, kind)][st] += 1
        fug[(m, g)][st] += 1
        how = ""
        if st == "late":
            came = [x for x in later if x > due + dt.timedelta(days=7)]
            how = "came %d days after the date" % (came[0] - due).days
        elif st == "med":
            how = "medicines, no consultation"
        fulist[(m, kind, st)].append([cid_of[u], f, ("%s · %s" % (g, how)) if how else g])
    furows = []
    for m in months:
        for k, kl in KINDS:
            c = fu[(m, k)]
            n = sum(c.values())
            if not n:
                continue
            for st in STATES:
                put("fu:%s:%s:%s" % (m, k, st), sorted(fulist[(m, k, st)], key=lambda x: x[1]))
            closed = n - c["open"]
            furows.append(dict(ym=m, month=mshort(m), kind=k, kindl=kl, due=n, kept=c["kept"], med=c["med"], late=c["late"],
                               neither=c["neither"], open=c["open"], kept_pct=pct(c["kept"], closed),
                               kept_num=pct_num(c["kept"], closed), keptmed_num=pct_num(c["kept"] + c["med"], closed)))

    # ------------------------------------------------------------------ by diagnosis group, for each month (with the 3 months to it)
    groups = {}
    for i, m in enumerate(months):
        trio = months[max(0, i - 2):i + 1]
        T = {g: dict(p=set(), n=set(), r=0, ph=0, b7=0, b30=0, mt=0, b30m=Counter(), mtm=Counter()) for g in GROUPS}
        once = set()
        for u, d, cid in visits:
            if d[:7] not in trio:
                continue
            g = grp(u, d)
            t = T[g]
            if d[:7] == m:
                t["p"].add(u)
                if firstday.get(u, "")[:7] == m:
                    t["n"].add(u)
                if (cid, d) not in once:
                    once.add((cid, d))
                    t["r"] += sum(rev[(cid, d)][k] for k in ("consult", "xray", "proc"))
            if (END - D(d)).days >= 30:
                x = gap_next(u, d)
                t["mt"] += 1
                t["mtm"][d[:7]] += 1
                if x is not None and x <= 7:
                    t["b7"] += 1
                elif x is not None and x <= 30:
                    t["b30"] += 1
                    t["b30m"][d[:7]] += 1
        for u, dd in bills.items():
            for day, amt in dd.items():
                if day[:7] != m:
                    continue
                near = [x for x in byp[u] if x <= day] or byp[u]
                T[grp(u, near[-1])]["ph"] += amt
        rows = []
        for g in GROUPS:
            t = T[g]
            fk = []
            medn = medb = 0
            for mm in trio:
                c = fug[(mm, g)]
                closed = sum(c.values()) - c["open"]
                fk.append(pct(c["kept"], closed) if closed else "–")
                medn += c["med"]
                medb += closed
            put("g:%s:%s" % (m, g), sorted([[cid_of[u], max(d for d in byp[u] if d[:7] == m), g] for u in t["p"]], key=lambda x: x[1], reverse=True))
            rows.append(dict(name=g, inc=("folds the small groups" if g == OTHER else ""), p=len(t["p"]), n=len(t["n"]), r=t["r"], pp=t["ph"],
                             b7=pct(t["b7"], t["mt"]), b30=pct(t["b30"], t["mt"]),
                             t=" · ".join(pct(t["b30m"][mm], t["mtm"][mm]) if t["mtm"][mm] else "–" for mm in trio),
                             k=" → ".join(fk), md=pct(medn, medb), md_num=pct_num(medn, medb),
                             k_last=pct_num(fug[(trio[-1], g)]["kept"], sum(fug[(trio[-1], g)].values()) - fug[(trio[-1], g)]["open"])))
        groups[m] = dict(trio=[mshort(x) for x in trio], rows=rows)

    # ------------------------------------------------------------------ back after a gap (seen-before visits, gap > 30 days)
    LB = (("a", "31–60 days", 31, 60), ("b", "61–90 days", 61, 90), ("c", "91–180 days", 91, 180), ("d", "over 180 days", 181, 10 ** 6))
    late = {}
    for i, m in enumerate(months):
        trio = months[max(0, i - 2):i + 1]
        T = defaultdict(Counter)
        L = defaultdict(list)
        for u, d, cid in visits:
            if d[:7] not in trio or firstday.get(u) == d:
                continue
            prev = [x for x in byp[u] if x < d]
            if prev:
                gp = (D(d) - D(prev[-1])).days
                if gp <= 30:
                    continue
                b = next(k for k, _l, lo, hi in LB if lo <= gp <= hi)
            else:
                b = "e"                              # seen before (an older clinic ID), no visit in the record since it began
                gp = None
            g = grp(u, d)
            T[g][b] += 1
            T[g]["t"] += 1
            lo = prev[-1] if prev else "0000"
            if any(lo < x < d and x not in vset[u] for x in bills.get(u, {})):
                T[g]["med"] += 1
            L[g].append([cid, d, ("back after %d days" % gp) if gp else "back, not seen since the record began"])
        rows = []
        tot = Counter()
        for g in GROUPS:
            t = T[g]
            tot.update(t)
            put("late:%s:%s" % (m, g), sorted(L[g], key=lambda x: x[1], reverse=True))
            rows.append(dict(name=g, a=t["a"], b=t["b"], c=t["c"], d=t["d"], e=t["e"], t=t["t"], med=t["med"]))
        allseen = sum(1 for u, d, _ in visits if d[:7] in trio and firstday.get(u) != d)
        late[m] = dict(trio=[mshort(x) for x in trio], rows=rows, total=dict(tot), share=pct(tot["t"], allseen), seen=allseen)

    # ------------------------------------------------------------------ how much the diagnoses cover
    cov = {}
    for i, m in enumerate(months):
        c = Counter()
        nonep = set()
        for u, d, cid in visits:
            if d[:7] == m:
                how = eff(u, d)[1]
                c[how] += 1
                if how == "none":
                    nonep.add(u)
        n = sum(c.values())
        cov[m] = dict(n=n, own=c["own"], carried=c["carried"], none=c["none"], own_pct=pct(c["own"], n),
                      carried_pct=pct(c["carried"], n), none_pct=pct(c["none"], n), none_patients=len(nonep),
                      none_once=sum(1 for u in nonep if len(byp[u]) == 1), none_new=sum(1 for u in nonep if firstday.get(u, "")[:7] == m))
        put("cov:%s:none" % m, sorted([[cid, d, "no diagnosis typed"] for u, d, cid in visits if d[:7] == m and eff(u, d)[1] == "none"],
                                       key=lambda x: x[1], reverse=True))
    lastday = END.isoformat()
    yday_none = [[cid, d, "no diagnosis typed"] for u, d, cid in visits if d == lastday and not (dx.get((u, d), ("", ""))[0])]
    put("cov:lastday:none", yday_none)

    # ------------------------------------------------------------------ diagnosis words the taxonomy does not know
    words = []
    try:
        import dx_feed                                                 # noqa: PLC0415 -- the constant only; nothing is written
        un = getattr(dx_feed, "UNCLASSIFIED", "Unclassified")
        words = [dict(word=str(w or "").strip(), n=int(n)) for w, n in q(
            "SELECT diagnosis_raw, COUNT(*) FROM dx_visit WHERE std_dx=? AND TRIM(COALESCE(diagnosis_raw,''))<>'' "
            "GROUP BY UPPER(TRIM(diagnosis_raw)) ORDER BY COUNT(*) DESC, diagnosis_raw LIMIT 200", un)]
    except Exception:                                                  # noqa: BLE001 -- the block says it could not be read
        words = None

    reading = dict(ok=True, version=VERSION, built=dt.datetime.now().strftime("%Y-%m-%d %H:%M"), data_to=lastday,
                   data_from=START.isoformat(), months=[dict(ym=m, short=mshort(m), label=mlabel(m), partial=(m == month_end)) for m in months],
                   rows=mrows, back=back, fu=furows, groups=groups, late=late, cov=cov,
                   lastday_none=len(yday_none), lastday=lastday,
                   words=(dict(n=len(words), visits=sum(w["n"] for w in words), top=words[:8]) if words is not None else None),
                   took=round(time.time() - t0, 2))
    reading["readings"] = {m: readings_for(reading, m) for m in months}
    reading["glance"] = {m: glance_for(reading, m) for m in months}
    try:                                                               # S853: Part 2 -- never at Part 1's cost
        import patients_part2                                          # noqa: PLC0415
        reading["p2"] = patients_part2.read2(reading, lists, today)
    except Exception as e:                                             # noqa: BLE001 -- the page says Part 2 could not be read
        reading["p2"] = dict(ok=False, why="%s: %s" % (type(e).__name__, str(e)[:160]))
    return reading, lists


# =================================================================================================== the words (fixed rules)
def _row(reading, m):
    return next((r for r in reading["rows"] if r["ym"] == m), None)


def _prev(reading, m):
    ms = [x["ym"] for x in reading["months"]]
    i = ms.index(m)
    return ms[i - 1] if i > 0 else None


def glance_for(reading, m):
    r = _row(reading, m)
    if not r:
        return []
    fr = [f for f in reading["fu"] if f["ym"] == m]
    due = sum(f["due"] for f in fr)
    kept = sum(f["kept"] for f in fr)
    op = sum(f["open"] for f in fr)
    rv = next((f for f in fr if f["kind"] == "review"), None)
    out = [dict(label="Patients", value=str(r["patients"]), sub="%d visits · %s a day%s" % (r["visits"], r["vpd"], " · so far" if r["partial"] else ""), key="m:%s:patients" % m),
           dict(label="New patients", value=str(r["new"]), sub=pct(r["new"], r["patients"]) + " of the patients", key="m:%s:new" % m),
           dict(label="Clinic ₹", value=rupees(r["total"]), sub="consultation %s · X-ray %s · procedure %s" % (rupees(r["consult"]), rupees(r["xray"]), rupees(r["proc"]))),
           dict(label="Medicines, no visit", value=str(r["med"]), sub="%d patients · %s at Sanjeevni" % (r["med_patients"], rupees(r["med_rs"])), key="m:%s:med" % m),
           dict(label="Follow-ups due", value=str(due), sub="%d kept%s" % (kept, (" · %d still open" % op) if op else "")),
           dict(label="Planned reviews kept", value=(rv["kept_pct"] if rv else "–"), sub=("%d of %d due%s" % (rv["kept"], rv["due"], (" · %d open" % rv["open"]) if rv["open"] else "")) if rv else "none due",
                key=("fu:%s:review:kept" % m) if rv else None)]
    return out


def readings_for(reading, m):
    """The reading-and-suggestions lines for month m. FIXED RULES: the same figures always give the same words; no model call."""
    out = []
    r = _row(reading, m)
    pm = _prev(reading, m)
    p = _row(reading, pm) if pm else None
    if not r:
        return out
    so_far = " so far" if r["partial"] else ""
    # 1 -- how many came
    if p:
        ch = (r["vpd"] - p["vpd"]) / p["vpd"] * 100 if p["vpd"] else 0
        word = "more" if ch >= 5 else "fewer" if ch <= -5 else "about as many"
        newsh = pct_num(r["new"], r["patients"])
        out.append(dict(head="Who came", tone=("w" if ch <= -10 else "n"),
                        text="%s%s: %d patients, %d of them new; %s visits a day against %s in %s — %s." % (
                            r["label"], so_far, r["patients"], r["new"], r["vpd"], p["vpd"], p["month"], word),
                        sug=("Visits per open day fell by %d%%. Read it with the season first, then the missed calls at the "
                             "front desk." % round(-ch)) if ch <= -10 else
                            ("New patients are %s of the patients — the usual share is about half." % (pct(r["new"], r["patients"]))) if newsh else "",
                        key="m:%s:patients" % m))
    # 2 -- planned reviews kept (the paid review)
    fr = next((f for f in reading["fu"] if f["ym"] == m and f["kind"] == "review"), None)
    hist = [f["kept_num"] for f in reading["fu"] if f["kind"] == "review" and f["ym"] < m and f["kept_num"] is not None]
    if fr:
        closed = fr["due"] - fr["open"]
        usual = round(sum(hist) / len(hist)) if hist else None
        low = fr["kept_num"] is not None and usual is not None and fr["kept_num"] <= usual - 10
        out.append(dict(head="Planned reviews", tone=("w" if low else "n"),
                        text="Of %d planned reviews (8–30 days) due in %s, %d were kept, %d were on medicines from Sanjeevni without "
                             "coming, %d came late%s%s." % (
                                 fr["due"], r["month"], fr["kept"], fr["med"], fr["late"],
                                 (", %d are still open" % fr["open"]) if fr["open"] else "",
                                 (" — %s kept against a usual %d%%" % (fr["kept_pct"], usual)) if (usual is not None and closed >= MIN_BASE) else ""),
                        sug=("The %d who neither came nor bought medicines are the calling list — tap to open them." % fr["neither"]) if fr["neither"] else
                            "Nothing lost so far; the open ones close by themselves when they come.",
                        key="fu:%s:review:neither" % m))
    # 3 -- medicines without a consultation
    if p is not None:
        out.append(dict(head="On medicines, not reviewed", tone=("w" if r["med"] > p["med"] * 1.15 and r["med"] >= 20 else "n"),
                        text="%d Sanjeevni purchases%s by %d known patients on days they did not consult (%s), against %d in %s." % (
                            r["med"], so_far, r["med_patients"], rupees(r["med_rs"]), p["med"], p["month"]),
                        sug="They are on treatment without a review: the follow-up call says \"you bought medicines on <date> — come for "
                            "the review\", a different conversation from \"you never came\". Rheumatology and degenerative joints first.",
                        key="m:%s:med" % m))
    # 4 -- the group whose follow-ups slipped most
    g = reading["groups"].get(m)
    if g:
        cands = [x for x in g["rows"] if x["name"] in MAIN and x["k_last"] is not None]
        if cands:
            worst = min(cands, key=lambda x: x["k_last"])
            best = max(cands, key=lambda x: x["k_last"])
            medg = max((x for x in g["rows"] if x["md_num"] is not None), key=lambda x: x["md_num"], default=None)
            out.append(dict(head="By diagnosis group", tone="w" if worst["k_last"] < 40 else "n",
                            text="Follow-ups due in %s kept: lowest %s (%d%%), highest %s (%d%%).%s" % (
                                r["month"], worst["name"], worst["k_last"], best["name"], best["k_last"],
                                (" Most often on medicines instead of the review: %s (%s of its follow-ups due %s)." % (medg["name"], medg["md"], "–".join([g["trio"][0], g["trio"][-1]])))
                                if medg and medg["md_num"] else ""),
                            sug="%s first on the calling list." % worst["name"], key="g:%s:%s" % (m, worst["name"])))
    # 5 -- back after a gap
    lt = reading["late"].get(m)
    if lt and lt["total"].get("t"):
        top = max(lt["rows"], key=lambda x: x["t"])
        out.append(dict(head="Back after a gap", tone="n",
                        text="%s–%s: %d visits by patients seen before came after more than a month away (%s of seen-before visits); most in "
                             "%s (%d). %d of them had bought medicines at Sanjeevni in the gap." % (
                                 lt["trio"][0], lt["trio"][-1], lt["total"]["t"], lt["share"], top["name"], top["t"], lt["total"].get("med", 0)),
                        sug="Rheumatology patients come back even when late: their call at 2 months is a reminder, not a rescue. Degenerative "
                            "joints, radicular spine and trauma are more often truly lost — their second call goes a week after the missed date.",
                        key="late:%s:%s" % (m, top["name"])))
    # 6 -- diagnoses not typed
    c = reading["cov"].get(m)
    if c and c["n"]:
        out.append(dict(head="Diagnosis typed", tone=("w" if c["none"] >= 30 else "n"),
                        text="%s%s: %s of visits carry their own diagnosis, %s take the patient's other visit's; %d visits (%d patients) have none."
                             % (r["label"], so_far, c["own_pct"], c["carried_pct"], c["none"], c["none_patients"]),
                        sug=("Last open day (%s): %d visits with no diagnosis typed — filling them keeps every figure above whole." % (
                            dmy(reading["lastday"]), reading["lastday_none"])) if reading["lastday_none"] else "Every visit of the last open day has its diagnosis.",
                        key="cov:lastday:none" if reading["lastday_none"] else "cov:%s:none" % m))
    # 7 -- the money
    if p:
        perv = r["total"] / r["visits"] if r["visits"] else 0
        perv_p = p["total"] / p["visits"] if p["visits"] else 0
        out.append(dict(head="Clinic money", tone="n",
                        text="%s%s: %s from %d visits (%s a visit); %s: %s (%s a visit)." % (
                            r["label"], so_far, rupees(r["total"]), r["visits"], rupees(perv), p["label"], rupees(p["total"]), rupees(perv_p)),
                        sug=""))
    return out


# =================================================================================================== building and serving
def _db_path(con):
    try:
        for r in con.execute("PRAGMA database_list").fetchall():
            if r[1] == "main":
                return r[2] or ""
    except Exception:                                                  # noqa: BLE001
        pass
    return ""


def _okday(x):
    """A real calendar day 'YYYY-MM-DD' (one bad date in the record must not stop the whole reading)."""
    try:
        return bool(re.fullmatch(r"\d{4}-\d\d-\d\d", str(x or ""))) and bool(dt.date.fromisoformat(str(x)))
    except ValueError:
        return False


def build(db_path, out_path=READING):
    """Open finance.db READ-ONLY, read, write the reading file atomically. Returns the reading."""
    src = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=30)
    src.row_factory = None
    try:
        reading, lists = read(src)
    finally:
        src.close()
    tmp = "%s.tmp%d" % (out_path, os.getpid())
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)     # private from the first byte
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(dict(reading=reading, lists=lists, built_epoch=time.time()), fh, ensure_ascii=False)
        os.replace(tmp, out_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    try:
        os.chmod(out_path, 0o600)
    except OSError:
        pass
    return reading


def _load():
    try:
        with open(READING, encoding="utf-8") as fh:
            s = json.load(fh)
        return s, time.time() - float(s.get("built_epoch") or 0)
    except Exception:                                                  # noqa: BLE001 -- no reading yet, or half a file
        return None, None


def _take_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            if time.time() - os.stat(LOCK).st_mtime > LOCK_STALE:
                os.unlink(LOCK)
                return _take_lock()
        except OSError:
            pass
        return False


def fresh(con, force=False):
    """(stored dict or None, error text or ''). Rebuilds when the reading is missing or older than MAX_AGE (or forced and
    older than a minute). A build that fails leaves the older reading standing and says why."""
    s, age = _load()
    if s is not None and not force and age is not None and age < MAX_AGE:
        return s, ""
    if s is not None and force and age is not None and age < 60:
        return s, ""
    p = _db_path(con)
    if not p or not _take_lock():
        return s, ("" if p else "the database path could not be read")
    try:
        build(p)
        s2, _a = _load()
        return (s2 or s), ""
    except Exception as e:                                             # noqa: BLE001 -- the older reading stands
        return s, "%s: %s" % (type(e).__name__, str(e)[:160])
    finally:
        try:
            with open(LOCK) as fh:
                mine = fh.read().strip() == str(os.getpid())
            if mine:                                  # a slow build's lock broken by another worker stays theirs
                os.unlink(LOCK)
        except OSError:
            pass


def _names(con, cids):
    out = {}
    try:
        for i in range(0, len(cids), 400):
            part = cids[i:i + 400]
            for cid, name in con.execute("SELECT clinic_id, name FROM patient_ref WHERE clinic_id IN (%s) "
                                         "AND (merged_into IS NULL OR merged_into='') ORDER BY id" % ",".join("?" * len(part)), part):
                out.setdefault(str(cid), name or "")
    except Exception:                                                  # noqa: BLE001
        pass
    return out


DENIED = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
          "<title>Patients</title><body style='font-family:system-ui;margin:40px 20px;color:#1d211f'>"
          "<h2>This page is the owner's.</h2><p>Your login does not open it.</p><p><a href='/portal'>Back to the Clinic app</a></p>")


def init(app, db_getter, require_fn, unit="packs"):
    """Mount only; touches no database (F-303). Called by owner_console.init."""
    global _db, _require, _unit
    from flask import Blueprint, Response, jsonify, request            # noqa: PLC0415
    _db, _require, _unit = db_getter, require_fn, unit
    bp = Blueprint("patients_page", __name__)

    def _gate():
        return _require("checker", unit=_unit)

    @bp.route(PAGE_URL)
    def patients_page():
        _u, err = _gate()
        if err:
            return Response(DENIED, status=403, mimetype="text/html")
        try:
            with open(PAGE_FILE, encoding="utf-8") as fh:
                html = fh.read()
        except OSError as e:
            return Response("The Patients page's file could not be read (%s)." % e, status=500, mimetype="text/plain")
        r = Response(html, mimetype="text/html")
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/console/api/patients")
    def patients_api():
        _u, err = _gate()
        if err:
            return err
        s, why = fresh(_db(), request.args.get("refresh") == "1")
        r = jsonify(ok=bool(s), reading=(s or {}).get("reading"), build_error=why, version=VERSION)
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/console/api/patients/list")
    def patients_list():
        _u, err = _gate()
        if err:
            return err
        key = str(request.args.get("key") or "")[:120]
        s, _why = _load()
        rows = ((s or {}).get("lists") or {}).get(key)
        if rows is None:
            r = jsonify(ok=False, why="This list is not in the reading (it may have been rebuilt) — reload the page.")
            r.headers["Cache-Control"] = "no-store"
            return r
        con = _db()
        nm = _names(con, sorted({str(x[0]) for x in rows}))
        out = [dict(cid=str(c), name=nm.get(str(c), ""), day=d, note=n, href="/finance/records/p/%s" % c) for c, d, n in rows[:500]]
        r = jsonify(ok=True, key=key, n=len(rows), rows=out, cut=len(rows) > 500)
        r.headers["Cache-Control"] = "no-store"
        return r

    app.register_blueprint(bp)
    return bp


if __name__ == "__main__":                                             # python3 patients_page.py --build <finance.db>
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--build":
        rd = build(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else READING)
        print("built: %s months, data to %s, %ss" % (len(rd.get("months") or []), rd.get("data_to"), rd.get("took")))
    else:
        print(__doc__)
