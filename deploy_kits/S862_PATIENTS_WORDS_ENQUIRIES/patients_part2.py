#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""patients_part2.py -- kit S853_PATIENTS_PART2 (the parent, S477, 17-Nov-2026; D939 Part 2). PARENT. NEW.

THE OWNER, 17-Nov-2026 13:19 IST: "first complete the analytics dashboard part" -- Part 2 of his Patients page, as mock-up v16
(https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA). Called by patients_page.read() at the end of each reading, inside a try:
anything that fails here leaves Part 1 exactly as it was and the block says it could not be read.

WHAT IT ADDS (reading["p2"], aggregates only; lists of clinic IDs only where a figure is about known patients):
  history  -- the same month a year before, the usual ranges and how each review date was finally kept, from
              patients_history.json beside this file: counts worked out ON THE OWNER'S PC from his two Docterz exports
              (Jan-2025..Jun-2026) by S851's own read() rules. No patient is in that file.
  google   -- "Before they reach you": patients_google.json beside this file (Google's monthly mail; Google's own year-on-year).
  desk     -- "At the front desk": the month's calls and WhatsApp, READ-ONLY from the Call Console's own record
              (/root/wa/console.db) and the WhatsApp inbox (/root/wa/wa_inbox/inbox.db) with the owner's Done / Not-a-patient
              marks (/root/portal/wa_awaiting.db), judged by the Call Console's OWN functions (calls_console.py loaded read-only
              under another name: phone_of, call_start, wa_items, wa_chat, wa_is_reply, en_out) -- one rule everywhere.
              Each caller is counted once a day however many times he rang; "unknown" = the number is not in the patient
              list today (console.db patients).
  reviews  -- "Google reviews": READ-ONLY from Review Assist's own store (/root/portal/gmb_store.db): the fortnightly readings
              and the drafts made / shared each month.
  called   -- the "Called" columns: a follow-up is CALLED when the clinic rang (any outgoing call, answered or not) a number of
              that clinic ID (console.db patients) from 3 days before the date to 30 days after it (or to today). A follow-up
              whose window starts before the call record begins is left out of the split (said on the page).
  became   -- S862 (S480, 18-Nov-2026): enquiry callers who became patients. A caller of the month = a number that rang in
              (incoming, answered or not) while it was not yet a patient's: in no clinic ID of a patient seen before, and not
              yet at a first visit. He "became a patient" when a NEW patient's first visit (Part 1's rule) under that number
              came within BECAME_DAYS (60) days of his first call of the month. Beside it: of the month's new patients, how many
              rang the clinic in the 60 days up to their first visit (only where the call record covers those 60 days). A
              number shared by a family counts for whichever patient it carries; a call from another number is not seen.
  google   -- S862: also patients_google_mail.json beside this file when present -- the months the server read from Google's
              own monthly mail (S863's reader); a month's counts from the mail win, Google's year-on-year stays from the
              session file; an unreadable mail file is ignored.
It also puts its own lines at the head of each month's reading-and-suggestions (fixed rules, as Part 1's).

WRITES NOTHING ANYWHERE. Every store is opened read-only (mode=ro). No patient name, number or ID is in this file (F-185).
"""
import datetime as dt
import importlib.util
import json
import os
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict

VERSION = "S853 1.0"
FIN = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.environ.get("PATIENTS_HISTORY", os.path.join(FIN, "patients_history.json"))
GOOGLE = os.environ.get("PATIENTS_GOOGLE", os.path.join(FIN, "patients_google.json"))
GOOGLE_MAIL = os.environ.get("PATIENTS_GOOGLE_MAIL", os.path.join(FIN, "patients_google_mail.json"))   # S862 / S863
CONSOLE_DB = os.environ.get("PATIENTS_CONSOLE_DB", "/root/wa/console.db")
INBOX_DB = os.environ.get("PATIENTS_INBOX_DB", "/root/wa/wa_inbox/inbox.db")
AWAIT_DB = os.environ.get("PATIENTS_AWAIT_DB", "/root/portal/wa_awaiting.db")
GMB_DB = os.environ.get("PATIENTS_GMB_DB", "/root/portal/gmb_store.db")
CC_PATH = os.environ.get("PATIENTS_CALLS_CONSOLE", "/root/portal/calls_console.py")
MIN_BASE = 20
WA_FROM = "2026-09"           # the WhatsApp record is complete from September (S433); earlier months are partial and left out
LATER_DAYS = 7                # a caller "reached on a later day" = an answered call within 7 days after
CALLED_BEFORE, CALLED_AFTER = 3, 30
BECAME_DAYS = 60              # S862: an enquiry caller "became a patient" when his first visit came within 60 days
HOURS = (("Before 9 a.m.", 0, 9), ("9 to 11", 9, 11), ("11 to 2", 11, 14), ("2 to 5", 14, 17), ("5 to 7", 17, 19),
         ("7 to 9", 19, 21), ("After 9 p.m.", 21, 24))
GREET = {"hi", "hii", "hiii", "hello", "helo", "hey", "namaste", "namaskar", "hlo", "hy"}
ASK_TIME = re.compile(r"\b(time|timing|timings|appointment|appoint|kab|samay|available|open|opd|book|booking|milna|mil sakte)\b"
                      r"|समय|कब|अपॉइंटमेंट|मिल", re.I)
MEDIA = ("image", "document", "video")
# a complaint theme of the reviews -> where this page can look (the mock-up's words); matched by a word in the theme's name
THEME_LOOK = (("staff", "calls missed and never returned; the staff cards"),
              ("x-ray", "X-ray revenue per patient, by group"), ("test", "X-ray revenue per patient, by group"),
              ("bill", "paid and free visits; rupees per patient"), ("fee", "paid and free visits; rupees per patient"),
              ("charge", "paid and free visits; rupees per patient"), ("wait", "visits per open day — the crowded days"),
              ("treatment", "patients who say “treatment elsewhere” on a call"))

_CC = [None, None]


def _calls_console():
    """The Call Console's own module, loaded read-only under another name (its import touches nothing); loaded again when
    its file changes (a later Call Console kit changes this page's rule at once, not at the next restart)."""
    mt = os.stat(CC_PATH).st_mtime
    if _CC[0] is None or _CC[1] != mt:
        spec = importlib.util.spec_from_file_location("_s853_calls_console", CC_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CC[0], _CC[1] = mod, mt
    return _CC[0]


def D(s):
    return dt.date.fromisoformat(str(s)[:10])


def pct(n, base):
    if not base:
        return "–"
    return ("%d%%" % round(100.0 * n / base)) if base >= MIN_BASE else ("%d of %d" % (n, base))


def pnum(n, base):
    return round(100.0 * n / base) if base and base >= MIN_BASE else None


def mspan(ym, today):
    a = D(ym + "-01")
    b = (a.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    return a, min(b, today)


def add_months(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) + k
    while m < 1:
        y, m = y - 1, m + 12
    while m > 12:
        y, m = y + 1, m - 12
    return "%04d-%02d" % (y, m)


def _ro(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def _json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:                                             # noqa: BLE001 -- the block says it could not be read
        return dict(ok=False, why="%s: %s" % (type(e).__name__, str(e)[:160]))


# =================================================================================================== last year
def history_block(reading):
    H = _json(HISTORY)
    out = dict(ok=True, source=H.get("source", ""), fees_from=H.get("fees_from", {}), range=H.get("range", {}),
               final=H.get("final", {}), ly={}, late_full=H.get("late_full", {}))
    for mo in reading["months"]:
        ly = add_months(mo["ym"], -12)
        if ly in H.get("months", {}):
            out["ly"][mo["ym"]] = dict(H["months"][ly], ym=ly)
    out["months"] = H.get("months", {})
    return out


# =================================================================================================== Google
FIG_MAIL = ("searches", "views", "calls", "directions", "chats", "website", "interactions")


def google_mail():
    """S862: the months the server read from Google's own monthly mail (S863's reader writes patients_google_mail.json:
    {"months": {ym: {searches, views, calls, directions, chats, website, interactions}}, "mail_day": "YYYY-MM-DD", ...}).
    Missing or unreadable = {} (the page stands on patients_google.json alone, as before)."""
    try:
        g = _json(GOOGLE_MAIL)
        return g if isinstance(g, dict) and isinstance(g.get("months"), dict) else {}
    except Exception:                                                  # noqa: BLE001
        return {}


MERGED = {"n": 0}


def merge_months(base, mail):
    """A month's counts from the mail win; Google's year-on-year (read from the Performance page) stays from the session file."""
    out = {k: dict(v) for k, v in base.items() if isinstance(v, dict)}
    for ym, g in mail.items():
        if not (isinstance(g, dict) and re.fullmatch(r"\d{4}-\d\d", str(ym))):
            continue
        figs = {}
        for k in FIG_MAIL:
            v = g.get(k)
            if isinstance(v, float) and v.is_integer():
                v = int(v)                                             # second look 6: a whole number written as 12.0
            if isinstance(v, int) and not isinstance(v, bool) and v >= 0:
                figs[k] = v
        if len(figs) == len(FIG_MAIL):
            out[ym] = dict(out.get(ym) or {}, **figs)
            out[ym].setdefault("yoy", {})
            MERGED["n"] += 1
    return out


def google_block(reading, hist):
    try:
        G = _json(GOOGLE)
        G = G if isinstance(G, dict) else {}
    except Exception:                                                  # noqa: BLE001 -- second look 4: the mail alone can stand
        G = {}
    GM = google_mail()                                                 # S862: the months S863's reader took from the mail
    MERGED["n"] = 0
    G = dict(G, months=merge_months(G.get("months") or {}, GM.get("months") or {}))
    merged = MERGED["n"]
    rows = []
    newp = {r["ym"]: r["new"] for r in reading["rows"]}
    hm = (hist or {}).get("months", {}) if isinstance(hist, dict) else {}
    FIG = ("searches", "views", "calls", "directions", "chats", "website", "interactions")
    for ym in sorted(G.get("months", {})):
        g = G["months"][ym]
        if not all(isinstance(g.get(k), (int, float)) and not isinstance(g.get(k), bool) for k in FIG):
            continue                                  # second look 2: a month with a missing figure is left out, never drawn
        n = newp.get(ym, (hm.get(ym) or {}).get("new"))
        n_ly = (hm.get(add_months(ym, -12)) or {}).get("new")
        part = any(r["ym"] == ym and r["partial"] for r in reading["rows"])
        yoy = g.get("yoy") or {}
        rows.append(dict(ym=ym, searches=g["searches"], views=g["views"], calls=g["calls"], directions=g["directions"],
                         chats=g["chats"], website=g["website"], actions=g["interactions"],
                         acts3=g["calls"] + g["directions"] + g["website"], new=n,
                         new_ly=n_ly, new_yoy=(round(100.0 * (n - n_ly) / n_ly) if (n and n_ly and not part) else None),
                         per10=(round(10.0 * n / g["directions"], 1) if (n and g["directions"]) else None),
                         yoy=yoy))
    return dict(ok=True, rows=rows, top_terms=G.get("top_terms", ""), closed_days=G.get("closed_days", ""),
                last=(rows[-1]["ym"] if rows else None),
                read_by=("server" if merged else ""), mail_day=(str(GM.get("mail_day") or "") if merged else ""))   # S862


# =================================================================================================== the front desk
_CALL_SQL = ("SELECT c.id, c.direction, c.answered, c.total_duration, c.customer_ring_duration, c.customer_talk_duration, "
             "c.phone10, c.join_key, c.ended_at_ist, c.client_ref_id, "
             "COALESCE((SELECT v.ai_outcome FROM verdicts v WHERE v.join_key=c.join_key AND c.join_key<>'' "
             "ORDER BY v.id DESC LIMIT 1),'') AS ai "
             "FROM calls c WHERE substr(c.ended_at_ist,1,10)>=? AND substr(c.ended_at_ist,1,10)<=? ORDER BY c.ended_at_ist, c.id")


def _int(v):
    try:
        return int(float(str(v or 0).strip() or 0))
    except ValueError:
        return 0


def load_calls(con, cc, lo, hi):
    out = []
    for r in con.execute(_CALL_SQL, (lo, hi)):
        ph = cc.phone_of(r)
        t = cc.call_start(r["ended_at_ist"], r["join_key"], r["total_duration"])
        if len(ph) != 10 or t is None:
            continue
        d = (r["direction"] or "").strip()
        out.append(dict(phone=ph, direction=("In" if d == "In" else "Out"), answered=(r["answered"] == 1), t=t,
                        day=t.strftime("%Y-%m-%d"), talk=_int(r["customer_talk_duration"]), dur=_int(r["total_duration"]),
                        ring=_int(r["customer_ring_duration"]), ai=(r["ai"] or "").strip(), kind="call"))
    return out


def cid_key(v):
    """One form for a clinic ID from either store: '8118', ' 08118 ', '8118.0' -> '8118' (S853 review 3)."""
    t = str(v or "").strip()
    if re.fullmatch(r"\d+\.0+", t):
        t = t.split(".")[0]
    t = re.sub(r"\D", "", t).lstrip("0")
    return t


def known_phones(con):
    ph = set()
    cid = defaultdict(set)
    for r in con.execute("SELECT phone10, clinic_id FROM patients WHERE COALESCE(phone10,'')<>''"):
        p = re.sub(r"\D", "", str(r["phone10"] or ""))[-10:]
        if len(p) == 10:
            ph.add(p)
            c = cid_key(r["clinic_id"])
            if c:
                cid[c].add(p)
    return ph, cid


def _norm(s):
    return " ".join(unicodedata.normalize("NFKC", str(s or "")).lower().replace(".", " ").replace("!", " ").split())


def desk_month(ym, today, calls, wa, known, cc, byph, waph, chats):
    """One month. byph / waph / chats: every call, every WhatsApp and the chat rule's verdicts by number -- worked out ONCE
    for all the months by desk_block (S853 review 4)."""
    a, b = mspan(ym, today)
    lo, hi = a.isoformat(), b.isoformat()
    inm = [c for c in calls if lo <= c["day"] <= hi]
    # -- caller-days (incoming)
    cd = defaultdict(list)
    for c in inm:
        if c["direction"] == "In":
            cd[(c["phone"], c["day"])].append(c)
    T = {k: Counter() for k in ("all", "unk", "pat")}
    tries = Counter()
    missed = Counter()
    for (ph, day), legs in cd.items():
        legs.sort(key=lambda x: x["t"])
        first = legs[0]
        same = [x for x in byph[ph] if x["day"] == day and x["t"] >= first["t"]]
        later_end = (D(day) + dt.timedelta(days=LATER_DAYS)).isoformat()
        if first["answered"]:
            st = "first"
        elif any(x["answered"] and x["direction"] == "In" for x in legs[1:]):
            st = "again"
        elif any(x["answered"] and x["direction"] == "Out" for x in same):
            st = "back"
        elif any(x["answered"] and day < x["day"] <= later_end for x in byph[ph]):
            st = "later"
        elif later_end >= today.isoformat():
            st = "open"                       # S853 review 1: its 7 days have not run -- neither reached nor lost yet
        else:
            st = "never"
        nocb = st == "never" and not any(x["direction"] == "Out" and x["t"] > first["t"] and x["day"] <= later_end for x in byph[ph])
        n = len(legs)
        tries["1" if n == 1 else "2" if n == 2 else "3" if n == 3 else "4+"] += 1
        for k in ("all", "unk" if ph not in known else "pat"):
            T[k]["n"] += 1
            T[k][st] += 1
            if nocb:
                T[k]["nocb"] += 1
        missed["calls"] += sum(1 for x in legs if not x["answered"])
    rows = []
    for k, lab in (("all", "All callers"), ("unk", "Unknown numbers"), ("pat", "Your patients")):
        t = T[k]
        nb = t["n"] - t["open"]                       # second look 1: one base everywhere -- the caller-days whose 7 days have run
        rows.append(dict(key=k, label=lab, n=t["n"], first=t["first"], again=t["again"], back=t["back"], later=t["later"],
                         never=t["never"], nocb=t["nocb"], open=t["open"], first_p=pct(t["first"], nb), again_p=pct(t["again"], nb),
                         back_p=pct(t["back"], nb), later_p=pct(t["later"], nb), never_p=pct(t["never"], nb)))
    incoming = [c for c in inm if c["direction"] == "In"]
    outgoing = [c for c in inm if c["direction"] == "Out"]
    # -- hours (incoming calls)
    hrs = []
    for lab, h0, h1 in HOURS:
        cs = [c for c in incoming if c["t"].weekday() != 6 and h0 <= c["t"].hour < h1]
        an = sum(1 for c in cs if c["answered"])
        hrs.append(dict(label=lab, ans=an, miss=len(cs) - an, share=pct(len(cs) - an, len(cs))))
    cs = [c for c in incoming if c["t"].weekday() == 6]
    an = sum(1 for c in cs if c["answered"])
    hrs.append(dict(label="Sundays (all day)", ans=an, miss=len(cs) - an, share=pct(len(cs) - an, len(cs))))
    # -- what the answered calls were about (the AI's verdict)
    about = []
    for lab, sel in (("Incoming — unknown numbers", lambda c: c["direction"] == "In" and c["phone"] not in known),
                     ("Incoming — your patients", lambda c: c["direction"] == "In" and c["phone"] in known),
                     ("Outgoing calls that were answered", lambda c: c["direction"] == "Out")):
        cs = [c for c in inm if c["answered"] and c["ai"] and sel(c)]
        w = Counter(cc.en_out(c["ai"]) for c in cs)
        bk = w.pop("booked", 0) + w.pop("coming", 0)
        eq = w.pop("enquiry", 0)
        ag = w.pop("call again", 0)
        about.append(dict(label=lab, n=len(cs), booked=bk, booked_p=pct(bk, len(cs)), enq=eq, enq_p=pct(eq, len(cs)), again=ag,
                          other=" · ".join("%s %d" % (k, v) for k, v in w.most_common(6))))
    # -- WhatsApp senders this month (each sender once)
    wam = [w for w in wa if lo <= w["day"] <= hi]
    senders = sorted({w["phone"] for w in wam if w["kind"] == "wa_in" and not w.get("wa_np")})
    W = {k: Counter() for k in ("all", "pat", "unk")}
    never_rang = never_rang_nothing = 0
    wam_by = defaultdict(list)
    for w in wam:
        if w["kind"] == "wa_in":
            wam_by[w["phone"]].append(w)
    for ph in senders:
        its, st, _res = chats[ph]
        mine = wam_by[ph]
        open_ = [w for w in mine if st.get(id(w), ("open", None))[0] == "open"]
        if not open_:
            res = "ans"
        else:
            f0 = min(w["t"] for w in open_ if w["t"]) if any(w["t"] for w in open_) else None
            tried = f0 is not None and any(
                (x.get("ch") == "call" and x["direction"] == "Out" and x["t"] > f0) or
                (x.get("ch") == "wa" and x["kind"] == "wa_out" and x["t"] and x["t"] > f0) for x in its)
            res = "tried" if tried else "nothing"
        for k in ("all", "unk" if ph not in known else "pat"):
            W[k]["n"] += 1
            W[k][res] += 1
        if not any(c["direction"] == "In" and lo <= c["day"] <= hi for c in byph.get(ph, ())):
            never_rang += 1
            if res == "nothing":
                never_rang_nothing += 1
    warows = [dict(key=k, label=lab, n=W[k]["n"], ans=W[k]["ans"], tried=W[k]["tried"], nothing=W[k]["nothing"],
                   lost=pct(W[k]["nothing"], W[k]["n"]))
              for k, lab in (("all", "Everyone who wrote"), ("pat", "Your patients"), ("unk", "Unknown numbers"))]
    people = {c["phone"] for c in inm} | set(senders)
    unk_people = {p for p in people if p not in known}
    t = T["all"]
    spoke = t["first"] + t["again"] + t["back"]
    tiles = [dict(label="People who contacted the clinic", value=str(len(people)),
                  sub="%d rang or were rung · %d wrote on WhatsApp · %d did both" % (
                      len({c["phone"] for c in inm}), len(senders), len({c["phone"] for c in inm} & set(senders)))),
             dict(label="From numbers not in your list", value=str(len(unk_people)),
                  sub="%s of everyone — mostly new patients" % pct(len(unk_people), len(people))),
             dict(label="Callers who spoke to the clinic the same day", value=pct(spoke, t["n"]),
                  sub="%d of %d caller-days · %s at the first ring · %d calls in all" % (spoke, t["n"], pct(t["first"], t["n"]), len(incoming))),
             dict(label="Callers never reached", value=str(t["never"]), warn=bool(t["never"]),
                  sub="%s of caller-days · %d from unknown numbers · %d with no call-back on record%s" % (
                      pct(t["never"], t["n"] - t["open"]), T["unk"]["never"], t["nocb"],
                      (" · %d of the last 7 days not reached yet" % t["open"]) if t["open"] else "")),
             dict(label="WhatsApp with no reply or call", value="%d of %d" % (W["all"]["nothing"], W["all"]["n"]), warn=bool(W["all"]["nothing"]),
                  sub="people · %d from unknown numbers" % W["unk"]["nothing"]),
             dict(label="Wrote on WhatsApp, never rang", value=str(never_rang), warn=bool(never_rang_nothing),
                  sub="%d of them with nothing on record" % never_rang_nothing)]
    note = ("%d incoming calls came from %d caller-days: %d rang once, %d twice, %d three times, %d four times or more. %d of the "
            "incoming calls were missed. %d calls went out from the clinic, %d of them picked up (%s)." % (
                len(incoming), t["n"], tries["1"], tries["2"], tries["3"], tries["4+"], missed["calls"],
                len(outgoing), sum(1 for c in outgoing if c["answered"]), pct(sum(1 for c in outgoing if c["answered"]), len(outgoing))))
    return dict(ok=True, ym=ym, span="%s to %s" % (a.strftime("%d-%b"), b.strftime("%d-%b")), days=(b - a).days + 1,
                tiles=tiles, calls=rows, hours=hrs, about=about, wa=warows, note=note,
                fig=dict(n=t["n"], first=t["first"], again=t["again"], back=t["back"], later=t["later"], never=t["never"],
                         nocb=t["nocb"], open=t["open"], unk_never=T["unk"]["never"], wa_n=W["all"]["n"], wa_nothing=W["all"]["nothing"],
                         wa_unk=W["unk"]["n"], never_rang=never_rang))


def wa_month_rows(wa, cc, today, google, chats):
    """WhatsApp to the clinic number, month by month (from WA_FROM)."""
    gm = {r["ym"]: r for r in (google or {}).get("rows", [])} if isinstance(google, dict) else {}
    eps = []
    for ph, (its, _st, res) in chats.items():
        for ep in res["eps"]:
            if ep["msgs"]:
                eps.append((ph, ep["msgs"][0]))
    rows = []
    ym = WA_FROM
    last = today.isoformat()[:7]
    while ym <= last:
        a, b = mspan(ym, today)
        lo, hi = a.isoformat(), b.isoformat()
        ins = [w for w in wa if w["kind"] == "wa_in" and lo <= w["day"] <= hi and not w.get("wa_np")]
        ppl = {w["phone"] for w in ins}
        firsts = [m for ph, m in eps if lo <= m["day"] <= hi]
        greet = sum(1 for m in firsts if _norm(m.get("txt")) in GREET)
        media = sum(1 for m in firsts if (m.get("mtype") or "") in MEDIA)
        askt = sum(1 for m in firsts if ASK_TIME.search(str(m.get("txt") or "")))
        outs = [w for w in wa if w["kind"] == "wa_out" and lo <= w["day"] <= hi]
        rows.append(dict(ym=ym, people=len(ppl), unk=sum(1 for p in ppl if p not in KNOWN_CACHE.get("ph", set())),
                         convs=len(firsts), greet=greet, media=media, askt=askt,
                         replies=sum(1 for w in outs if cc.wa_is_reply(w)), failed=sum(1 for w in outs if w.get("status") == "failed"),
                         chats=(gm.get(ym) or {}).get("chats"), partial=(ym == last)))
        ym = add_months(ym, 1)
    return rows


KNOWN_CACHE = {}


def desk_block(reading, today, google):
    cc = _calls_console()
    con = _ro(CONSOLE_DB)
    try:
        known, cid_ph = known_phones(con)
        KNOWN_CACHE["ph"] = known
        first = reading["months"][0]["ym"]
        lo = (D(first + "-01") - dt.timedelta(days=8)).isoformat()
        hi = today.isoformat()
        calls = load_calls(con, cc, lo, hi)
        cmin = con.execute("SELECT MIN(substr(ended_at_ist,1,10)) FROM calls WHERE COALESCE(ended_at_ist,'')<>''").fetchone()[0]
    finally:
        con.close()
    wa_ok = True
    try:
        dz = cc.wz_read(AWAIT_DB)
        wa, wa_ok = cc.wa_items(INBOX_DB, min(lo, add_months(WA_FROM, 0) + "-01"), hi, dz=dz)
    except Exception:                                                  # noqa: BLE001 -- the WhatsApp half says so; calls still show
        wa, wa_ok = [], False
    if not wa_ok:
        wa = []
    for w in wa:
        w["day"] = w.get("day") or ""
    byph = defaultdict(list)                  # S853 review 4: every number's calls, WhatsApps and chat verdicts ONCE
    for c in calls:
        byph[c["phone"]].append(c)
    waph = defaultdict(list)
    for w in wa:
        waph[w["phone"]].append(w)
    chats = {}
    for ph, ws in waph.items():
        its = ws + [dict(c, ch="call") for c in byph.get(ph, ())]
        res = cc.wa_chat(its)
        chats[ph] = (its, res["st"], res)
    months = {}
    for mo in reading["months"]:
        months[mo["ym"]] = desk_month(mo["ym"], today, calls, wa, known, cc, byph, waph, chats)
    return dict(ok=True, wa_ok=wa_ok, calls_from=cmin, months=months,
                wa_months=(wa_month_rows(wa, cc, today, google, chats) if wa_ok else [])), calls, cid_ph


# =================================================================================================== S862: callers who became patients
def became_block(reading, lists, today, calls, cid_ph, calls_from):
    """Enquiry callers who became patients, month by month (see the head of this file). Adds lists bec:<ym> and rf:<ym>
    (clinic IDs only, with the first-visit day)."""
    newday, orig, seen_max = {}, {}, 0
    for mo in reading["months"]:
        for row in lists.get("m:%s:new" % mo["ym"], []):
            c = cid_key(row[0])
            d = str(row[1] or "")[:10]
            if c and re.fullmatch(r"\d{4}-\d\d-\d\d", d) and (c not in newday or d < newday[c]):
                newday[c] = d
                orig[c] = str(row[0]).strip()                   # review 3: the clinic ID as Part 1 wrote it (lists, links)
        for row in lists.get("m:%s:patients" % mo["ym"], []) + lists.get("m:%s:new" % mo["ym"], []):
            c = cid_key(row[0])
            if c.isdigit():
                seen_max = max(seen_max, int(c))
    ph_cids = defaultdict(set)
    for c, phs in cid_ph.items():
        for p in phs:
            ph_cids[p].add(c)
    known = set(KNOWN_CACHE.get("ph") or ()) | set(ph_cids)
    ph_first, old = {}, set()
    for p in known:
        cs = ph_cids.get(p) or set()
        cs = {c for c in cs if not (c.isdigit() and seen_max and int(c) > seen_max)}   # review 4: an ID the visit record
        if not cs and ph_cids.get(p):                                                      # has not reached yet -- not old
            continue
        if not cs or any(c not in newday for c in cs):
            old.add(p)                    # a patient seen before the new ones of these months, or a number with no clinic ID
        else:
            ph_first[p] = min(newday[c] for c in cs)
    inc = defaultdict(list)
    for c in calls:
        if c["direction"] == "In":
            inc[c["phone"]].append(c["day"])
    for p in inc:
        inc[p].sort()
    loaded = (D(reading["months"][0]["ym"] + "-01") - dt.timedelta(days=8)).isoformat()
    cover = max(str(calls_from or "9999-12-31"), loaded)
    months = {}
    for mo in reading["months"]:
        ym = mo["ym"]
        a, b = mspan(ym, today)
        lo, hi = a.isoformat(), b.isoformat()
        mend = (a.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
        callers = {}
        for p, days in inc.items():
            if p in old:
                continue
            d1 = next((d for d in days if lo <= d <= hi), None)
            if d1 is None:
                continue
            f = ph_first.get(p)
            if f is not None and f < d1:
                continue                  # already a patient on that day
            callers[p] = d1
        bec = []
        for p, d1 in sorted(callers.items()):
            f = ph_first.get(p)
            if f is not None and (D(f) - D(d1)).days <= BECAME_DAYS:
                cid = orig.get(sorted(c for c in ph_cids[p] if newday.get(c) == f)[0], "")
                gap = (D(f) - D(d1)).days
                bec.append([cid, f, ("rang %s and came the same day" % _dmy(d1)) if gap == 0 else
                            ("rang %s, first visit %d day%s later" % (_dmy(d1), gap, "" if gap == 1 else "s"))])
        lists["bec:%s" % ym] = sorted(bec, key=lambda x: x[1], reverse=True)
        newp = [(cid_key(r[0]), str(r[1] or "")[:10], str(r[0]).strip()) for r in lists.get("m:%s:new" % ym, [])]
        base, rang, rf = 0, 0, []
        for c, f, raw in newp:
            phs = cid_ph.get(c) or set()
            if not phs or not f or (D(f) - dt.timedelta(days=BECAME_DAYS)).isoformat() < cover:
                continue
            base += 1
            lo2 = (D(f) - dt.timedelta(days=BECAME_DAYS)).isoformat()
            hit = sorted(d for p in phs for d in inc.get(p, ()) if lo2 <= d <= f)
            if hit:
                rang += 1
                rf.append([raw, f, "rang first on %s" % _dmy(hit[0])])
        lists["rf:%s" % ym] = sorted(rf, key=lambda x: x[1], reverse=True)
        months[ym] = dict(callers=len(callers), became=len(bec), became_p=pct(len(bec), len(callers)),
                          complete=(mend + dt.timedelta(days=BECAME_DAYS)) <= today, newp=len(newp),
                          rang=(rang if base else None), rang_base=base, rang_p=pct(rang, base))
    return dict(ok=True, months=months, window=BECAME_DAYS, calls_from=calls_from,
                note=("A caller here is a number that rang in while it was not yet a patient's; he became a patient when a new "
                      "patient's first visit under that number came within %d days of his first call of the month. A month is "
                      "\u201cso far\u201d until %d days after its end. The right-hand count needs the call record to cover the %d days "
                      "before the first visit (it begins on %s). A call from another number, or a number shared by a family, "
                      "is not told apart. A caller who rang in two months before he came counts in both.") % (BECAME_DAYS, BECAME_DAYS, BECAME_DAYS, _dmy(calls_from) if calls_from else "–"))


# =================================================================================================== the "Called" columns
def called_block(reading, lists, today, calls, cid_ph, calls_from):
    outs = defaultdict(list)
    for c in calls:
        if c["direction"] == "Out":
            outs[c["phone"]].append(c["day"])
    start = calls_from or "9999-12-31"
    fu = {}
    grp = defaultdict(Counter)
    for key, rows in list(lists.items()):
        p = key.split(":")
        if p[0] != "fu" or len(p) != 4:
            continue
        m, kind, st = p[1], p[2], p[3]
        c = fu.setdefault((m, kind), Counter())
        cl, nl = [], []
        for cid, due, note in rows:
            a = (D(due) - dt.timedelta(days=CALLED_BEFORE)).isoformat()
            if a < start:
                c["unknown"] += 1
                continue
            if st == "open" or a > today.isoformat():
                c["notyet"] += 1              # S853 review 2: still open, or its window has not begun -- not in the split
                continue
            if not cid_ph.get(cid_key(cid)):
                c["nophone"] += 1             # S853 review 3: no number on record for this ID -- not "not called"
                continue
            b = min(D(due) + dt.timedelta(days=CALLED_AFTER), today).isoformat()
            hit = any(a <= d <= b for ph in cid_ph.get(cid_key(cid), ()) for d in outs.get(ph, ()))
            c["n"] += 1
            c["c_" + st if hit else "n_" + st] += 1
            c["called" if hit else "not"] += 1
            g = str(note).split(" · ")[0]
            if st in ("neither", "late", "med"):
                grp[(m, g)]["missed"] += 1
                if hit:
                    grp[(m, g)]["called"] += 1
            (cl if hit else nl).append([cid, due, "%s · %s" % (st.replace("med", "on medicines").replace("neither", "neither came nor bought"), note)])
        lists.setdefault("fuc:%s:%s:called" % (m, kind), []).extend(cl)
        lists.setdefault("fuc:%s:%s:not" % (m, kind), []).extend(nl)
    rows = {}
    for (m, kind), c in fu.items():
        ck = c["c_kept"]
        cc_closed = c["called"] - c["c_open"]
        nk = c["n_kept"]
        nc_closed = c["not"] - c["n_open"]
        rows["%s:%s" % (m, kind)] = dict(n=c["n"], called=c["called"], not_=c["not"], unknown=c["unknown"], notyet=c["notyet"],
                                         nophone=c["nophone"],
                                         kept_called=pct(ck, cc_closed), kept_not=pct(nk, nc_closed),
                                         kc=pnum(ck, cc_closed), kn=pnum(nk, nc_closed))
    groups = {"%s:%s" % k: dict(missed=v["missed"], called=v["called"]) for k, v in grp.items()}
    tot = Counter()
    for c in fu.values():
        tot.update(c)
    return dict(ok=True, rows=rows, groups=groups, calls_from=calls_from,
                matched=dict(split=tot["n"], nophone=tot["nophone"], notyet=tot["notyet"], before=tot["unknown"]))


# =================================================================================================== reviews
def reviews_block(reading):
    con = _ro(GMB_DB)
    try:
        snaps = []
        for r in con.execute("SELECT taken_on, data FROM snapshot ORDER BY taken_on, id"):
            try:                                                       # S853 review 7: one bad row costs only itself
                d = json.loads(r["data"])
                if isinstance(d, dict) and not isinstance(d.get("ours_n"), bool) and int(float(d.get("ours_n") or 0)) > 0:
                    d["ours_n"] = int(float(d["ours_n"]))     # a reading with no count is not a reading; any number form is taken
                    snaps.append(dict(taken_on=r["taken_on"], data=d))
            except (ValueError, TypeError):
                pass
        pres = Counter(str(r[0])[:7] for r in con.execute("SELECT at FROM press"))
        shr = Counter({str(m): n for m, n in con.execute(
            "SELECT substr(p.at,1,7), COUNT(DISTINCT p.id) FROM share s JOIN press p ON p.id=s.press_id GROUP BY 1")})
        first = con.execute("SELECT MIN(at) FROM press").fetchone()[0]
    finally:
        con.close()
    last = snaps[-1] if snaps else None
    prev = snaps[-2] if len(snaps) > 1 else None
    themes = []
    if last:
        for t in last["data"].get("themes", []):
            nm = str(t.get("name", ""))
            look = next((v for k, v in THEME_LOOK if k in nm.lower()), "")
            themes.append(dict(name=nm, ours=t.get("ours"), other=t.get("else"), look=look))
    months = {}
    pts = {r["ym"]: r["patients"] for r in reading["rows"]}
    for mo in reading["months"]:
        m = mo["ym"]
        months[m] = dict(drafts=pres.get(m, 0), shared=shr.get(m, 0),
                         per100=(round(100.0 * pres.get(m, 0) / pts[m], 1) if pts.get(m) else None))
    return dict(ok=True, n_snap=len(snaps), last=(dict(taken_on=last["taken_on"], ours_n=last["data"].get("ours_n"),
                                                        low=last["data"].get("ours_low_pct"),
                                                        sources=len(last["data"].get("sources", []))) if last else None),
                new_since=(((last["data"].get("ours_n") or 0) - (prev["data"].get("ours_n") or 0))
                           if (last and prev and last["data"].get("ours_n") and prev["data"].get("ours_n")) else None),
                prev_on=(prev["taken_on"] if prev else None), themes=themes, months=months, since=(str(first)[:10] if first else None))


# =================================================================================================== the lines
def _line_desk(reading, p2, m, lab):
    dk = (p2.get("desk") or {}).get("months", {}).get(m) if (p2.get("desk") or {}).get("ok") else None
    if not dk:
        return None
    f = dk["fig"]
    n = f["n"] - f.get("open", 0)                          # caller-days whose 7 days have run
    if n < MIN_BASE:
        return None
    nv = f["never"]
    return dict(head=("%d callers in a hundred never speak to anyone" % round(100.0 * nv / n)) if nv else "Every caller spoke to the clinic",
                tone=("w" if 100.0 * nv / n >= 8 else "n"),
                text="%s, counting each caller once a day (caller-days whose 7 days have run: %d): %s were answered at the first ring, %s "
                     "got through by ringing again, %s by a call-back from the clinic, %s on a later day and %s never (%d of them numbers not "
                     "in your list; %d with no call-back on record). On WhatsApp, %d of %d senders have nothing on record." % (
                         lab, n, pct(f["first"], n), pct(f["again"], n), pct(f["back"], n), pct(f["later"], n), pct(nv, n),
                         f["unk_never"], f["nocb"], f["wa_nothing"], f["wa_n"]),
                sug=("It is the caller who repairs a missed call: %d got through by trying again against %d reached by a call-back. "
                     "The never-reached with no call-back are the list to ring first — unknown numbers first." % (f["again"], f["back"])) if nv else "")


def _line_google(reading, p2, m, lab):
    gg = p2.get("google") or {}
    if not gg.get("ok"):
        return None
    rows = {r["ym"]: r for r in gg["rows"]}
    g, gp = rows.get(m), rows.get(add_months(m, -1))
    if not (g and gp and g.get("new") and gp.get("new") and g.get("directions") is not None and gp.get("directions") is not None):
        return None
    gd = g["directions"] - gp["directions"]
    nd = g["new"] - gp["new"]
    inside = (gd >= 0 and nd < 0)
    both = (gd < 0 and nd < 0)
    y = g.get("yoy") or {}
    yy = ""
    if y.get("directions") is not None and y.get("calls") is not None:
        yy = " Against the same month of 2025 Google shows direction requests %+d%%, calls %+d%%%s." % (
            round(y["directions"]), round(y["calls"]), (", and your new patients %+d%%" % g["new_yoy"]) if g.get("new_yoy") is not None else "")
    return dict(head="Google and the clinic door", tone=("w" if inside else "n"),
                text="Direction requests on Google %d → %d, calls %s → %s, searches %s → %s; new patients at the clinic %d → %d.%s" % (
                    gp["directions"], g["directions"], gp.get("calls"), g.get("calls"), gp.get("searches"), g.get("searches"), gp["new"], g["new"], yy),
                sug=("Google held and new patients fell: look inside the clinic — the missed calls above first." if inside else
                     "Both fell together: that is people setting out, the season — not how the clinic received them." if both else
                     "When Google holds steady and new patients fall, look inside the clinic; when both fall together, it is the season."))


def _line_lastyear(reading, p2, m, lab):
    hb = p2.get("history") or {}
    ly = (hb.get("ly") or {}).get(m) if hb.get("ok") else None
    r = next((x for x in reading["rows"] if x["ym"] == m), None)
    if not (ly and r and ly.get("vpd") is not None):
        return None
    if r["partial"]:                                       # S853 review 6: a part month is read per open day only
        return dict(head="Against the same month last year", tone="n",
                    text="%s so far: %s visits a day against %s in %s (the whole month); %s new patients a day against %s." % (
                        lab, r["vpd"], ly["vpd"], _mlab(ly["ym"]), (round(r["new"] / r["days"], 1) if r["days"] else 0),
                        (round((ly.get("new") or 0) / ly["days"], 1) if ly.get("days") else "–")),
                    sug="A month in progress is compared per open day; the whole-month figures come when it ends.")
    fee = ""
    if ly.get("consult") and r.get("consult"):
        fee = " Consultation fees %s against %s." % (_rs(r["consult"]), _rs(ly["consult"]))
    return dict(head="Against the same month last year", tone="n",
                text="%s: %s visits a day against %s in %s; %s new patients against %s; %s patients against %s.%s" % (
                    lab, r["vpd"], ly["vpd"], _mlab(ly["ym"]), r["new"], ly.get("new", "–"), r["patients"], ly.get("patients", "–"), fee),
                sug="Read each month against the same month of last year, not only the month before: the autumn dip came both years.")


def _line_reviews_kept(reading, p2, m, lab):
    hb = p2.get("history") or {}
    rv = next((f for f in reading["fu"] if f["ym"] == m and f["kind"] == "review"), None)
    rg = (hb.get("range") or {}).get("review_kept") if hb.get("ok") else None
    if not (rv and rg and rv.get("kept_num") is not None):
        return None
    return dict(head="Planned reviews against 18 months", tone=("w" if rv["kept_num"] < rg["p25"] else "n"),
                text="%s of the planned reviews due in %s were kept. From January 2025 to June 2026 this figure moved between %d%% and "
                     "%d%% and was usually %d–%d%%." % (rv["kept_pct"], lab, rg["lo"], rg["hi"], rg["p25"], rg["p75"]),
                sug=("Below the usual: planned reviews go to the top of the calling list." if rv["kept_num"] < rg["p25"] else ""),
                key="fu:%s:review:neither" % m)


def _line_called(reading, p2, m, lab):
    cl = p2.get("called") or {}
    if not cl.get("ok"):
        return None
    for kind in ("review", "short"):
        x = cl["rows"].get("%s:%s" % (m, kind))
        if x and x.get("kc") is not None and x.get("kn") is not None:
            return dict(head="Calling brings them back", tone="n",
                        text="Follow-ups due in %s (%s): those the clinic called were kept %d%% of the time, those not called %d%% "
                             "(%d called, %d not)." % (lab, "planned reviews" if kind == "review" else "within a week", x["kc"], x["kn"],
                                                       x["called"], x["not_"]),
                        sug="The not-called who neither came nor bought medicines are the list — tap to open them.",
                        key="fuc:%s:%s:not" % (m, kind))
    return None


def _line_reviews(reading, p2, m, lab):
    rb = p2.get("reviews") or {}
    last = rb.get("last") if rb.get("ok") else None
    if not last or not last.get("ours_n"):
        return None
    mo = rb["months"].get(m) or {}
    low = ("%s%% of them unhappy — mostly about the desk and the charges. " % last["low"]) if last.get("low") is not None else ""
    return dict(head="Good reviews follow your asks, not the month", tone="n",
                text="%d reviewers on your listing (read %s), %sReview Assist drafts in %s: %d made, %d shared." % (
                    last["ours_n"], _dmy(last.get("taken_on")), low, lab, mo.get("drafts", 0), mo.get("shared", 0)),
                sug="Ask two or three of the day's returning patients who have done well; the page counts the asks against patients seen.")


def lines_for(reading, p2, m):
    """Part 2's reading-and-suggestions lines for month m (fixed rules: the same figures always give the same words).
    Each line is guarded by itself (S853 review 5): one bad value costs that line only."""
    lab = next((x["label"] for x in reading["months"] if x["ym"] == m), m)
    out = []
    for fn in (_line_desk, _line_google, _line_lastyear, _line_reviews_kept, _line_called, _line_reviews):
        try:
            x = fn(reading, p2, m, lab)
        except Exception:                                              # noqa: BLE001
            x = None
        if x:
            out.append(x)
    return out


def _rs(p):
    p = int(round((p or 0) / 100.0))
    s = str(abs(p))
    if len(s) > 3:
        h, t = s[:-3], s[-3:]
        parts = []
        while len(h) > 2:
            parts.insert(0, h[-2:])
            h = h[:-2]
        if h:
            parts.insert(0, h)
        s = ",".join(parts) + "," + t
    return "₹" + s


def _mlab(ym):
    return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")


def _dmy(iso):
    try:
        return D(iso).strftime("%d-%b")
    except Exception:                                                  # noqa: BLE001
        return str(iso or "")


# =================================================================================================== entry
def read2(reading, lists, today=None):
    """Part 2 for this reading. Adds its own list keys (fuc:*) and puts its lines at the head of each month's readings."""
    today = today or dt.date.today()
    t0 = dt.datetime.now()
    p2 = dict(ok=True, version=VERSION)
    p2["history"] = _safe(history_block, reading)
    p2["google"] = _safe(google_block, reading, p2["history"])
    try:
        desk, calls, cid_ph = desk_block(reading, today, p2["google"])
        p2["desk"] = desk
        p2["called"] = _safe(called_block, reading, lists, today, calls, cid_ph, desk.get("calls_from"))
        p2["became"] = _safe(became_block, reading, lists, today, calls, cid_ph, desk.get("calls_from"))   # S862
    except Exception as e:                                             # noqa: BLE001
        why = "%s: %s" % (type(e).__name__, str(e)[:160])
        p2["desk"] = dict(ok=False, why=why)
        p2["called"] = dict(ok=False, why=why)
        p2["became"] = dict(ok=False, why=why)
    p2["reviews"] = _safe(reviews_block, reading)
    for mo in reading["months"]:
        m = mo["ym"]
        try:
            ln = lines_for(reading, p2, m)
        except Exception:                                              # noqa: BLE001 -- Part 1's lines stand alone
            ln = []
        reading.setdefault("readings", {}).setdefault(m, [])
        reading["readings"][m] = ln + reading["readings"][m]
    p2["took"] = round((dt.datetime.now() - t0).total_seconds(), 2)
    return p2
