#!/usr/bin/env python3
"""make_s977.py -- builds kit S977_MORNING_REVENUE_MATCH (K2a) from the FROM bytes. Every anchor must occur exactly once."""
import hashlib, sys, os
FROM = {"day_check.py": "946f0408bd9763bfd1578648bd07ab1b", "register_push.py": "9b1fbc29aff1472a1a4dfb2ad4cfcf3a",
        "docterz_pickup.py": "8ffb93aa461c74ca4dbbeabdff1d2081"}
src, dst = sys.argv[1], sys.argv[2]

def sub(t, old, new, name):
    n = t.count(old)
    if n != 1:
        sys.exit("ANCHOR %s found %d times" % (name, n))
    return t.replace(old, new)

def load(n):
    b = open(os.path.join(src, n), "rb").read()
    if hashlib.md5(b).hexdigest() != FROM[n]:
        sys.exit("FROM %s is not %s" % (n, FROM[n]))
    return b.decode("utf-8")

# ============================================================== day_check.py
t = load("day_check.py")
t = sub(t, '''counts. A staff 'free' answer is named as theirs, never as his.
"""''', '''counts. A staff 'free' answer is named as theirs, never as his.

S977 (session S544, 28-Nov-2026; D1099, D1100 -- K2a of S537_MORNING_CHECK_FINAL_BUILD_PLAN; his word 14:03 "build K2 today";
F-1732 rides in docterz_pickup.py). THE MORNING AS A REVENUE MATCH: register total against Docterz total (net of refunds / radd)
only -- his 14:31 27-Nov: "skip cash to UPI corrections, only revenue mismatch flow to be kept ... only same-day Docterz edits".
With DAYCHK_REVENUE on (the default):
  * no payment-mode card of any kind (mode / modeany / swap / regupi / bank) -- the per-tender figures stay in 'totals' and the
    bank part stays on his page, as information;
  * no Docterz edit is asked the next morning: a slip Docterz lacks whose money the register holds and that his back-date list
    does not carry is counted 'kept outside Docterz' by itself (a note; nothing written -- his own list rows keep S970's answer);
    a slip line neither billed nor in the register is a note (the evening's matter);
  * the three slip shapes the widened evening check (S972) names the same evening -- a line twice, parchi short, parchi over --
    make no morning card on a day whose export went through it;
  * register MORE, unexplained -> ONE card 'nf:' naming the day's Docterz patients with no paid bill (the export's Rs 0 lines and
    Docterz's clinical visits) -- whose was it? -- with 'Make the parchi' (the slip then settles by itself, S970);
  * register LESS, after refunds and radd -> when the gap is exactly one bill of one head and the other heads agree: reception's
    card 'less:' -- the register was written wrong (the register page), or one patient did not pay: the pick writes slip_adjust's
    own 'money never taken' radd on that patient's slip (pending his approval, as every radd); otherwise his line 'less:'.
  * breakdown(chk): the day's sum in one line for the clean push.
DAYCHK_REVENUE=0 puts the S970 morning back exactly as it was.
"""''', "doc")

t = sub(t, '''def check_day(con, d):
    """The day's corrections.''', '''# ---------------------------------------------------------------- S977 (D1099, D1100): the morning as a revenue match (K2a)
S977 = "S977.1"
S972_FROM = "2026-11-27 19:50:00"                        # the evening check names the slip shapes from S972's install


def revenue_on():
    """S977: register total against Docterz total only (DAYCHK_REVENUE=0 -> the S970 morning as it was)."""
    try:
        import evening_check as _ev                      # noqa: PLC0415 -- the one settings reader (portal_config, then env)
        v = _ev.cfg("DAYCHK_REVENUE", "1")
    except Exception:                                    # noqa: BLE001
        v = os.environ.get("DAYCHK_REVENUE", "1")
    return str(v or "1").strip().lower() not in ("0", "off", "no", "false")


def _s977_shapes(s):
    out = set()
    for x in str(s or "").split(","):
        parts = x.split(":")
        if len(parts) == 3 and parts[1].isdigit():
            out.add((int(parts[1]), parts[2]))
    return out


def _s977_reached(sent):
    """True when an evening push reached somebody: 'sent N, failed F, ntfy K' with N or K above 0."""
    import re as _re                                     # noqa: PLC0415
    m = _re.match(r"sent (\d+), failed \d+, ntfy (\d+)", str(sent or ""))
    return bool(m) and (int(m.group(1)) > 0 or int(m.group(2)) > 0)


def _s977_evening_told(con, d):
    """{(slip_id, kind)} the widened evening check (S972) told reception about, AS THE DAY'S LAST EXPORT LEFT IT (second look):
    newest first -- a clean / cleared export: nothing still told; 'quiet' (clean again; its shapes empty) narrows to its lines and looks
    further back; 'missing' that reached somebody: its lines (within any later 'quiet' row's); one that reached nobody: nothing.
    set() when unreadable -- then the morning keeps its cards."""
    try:
        if not _has(con, "evening_check_push"):
            return set()
        cur = None
        for r in con.execute("SELECT outcome, sent, shapes FROM evening_check_push WHERE day=? AND at>=? AND outcome IN "
                             "('missing','clean','cleared','quiet') ORDER BY at DESC, export_id DESC", (d, S972_FROM)):
            if r[0] in ("clean", "cleared"):
                return set()
            sh = _s977_shapes(r[2])
            if r[0] == "quiet":
                cur = sh if cur is None else (cur & sh)
                continue
            if not _s977_reached(r[1]):
                return set()
            return sh if cur is None else (sh & cur)
        return set()
    except Exception:                                    # noqa: BLE001
        return set()


def _s977_cands(con, d, lines):
    """The day's Docterz patients with no paid bill -- the export's Rs 0 lines, then Docterz's clinical visits: [(cid, name)]."""
    paid = {ln["cid"] for ln in lines if ln["cid"] and ln["amount_p"] > 0}
    out, seen = [], set()
    for ln in lines:
        c = ln["cid"]
        if c and c not in paid and c not in seen:
            seen.add(c)
            out.append((c, ln["patient"]))
    if _has(con, "patient_visit"):
        try:
            vis = [str(r[0]).strip() for r in con.execute("SELECT DISTINCT clinic_id FROM patient_visit WHERE visit_date=? AND "
                                                          "clinic_id IS NOT NULL AND clinic_id<>'' ORDER BY clinic_id", (d,))]
        except Exception:                                # noqa: BLE001
            vis = []
        for c in vis:
            if c and c not in paid and c not in seen:
                seen.add(c)
                out.append((c, _name(con, c, lines)))
    return out


def _s977_names(cands, most=9):
    s = ", ".join(_who_en(nm, c) for c, nm in cands[:most])
    return s + ((" +%d" % (len(cands) - most)) if len(cands) > most else "")


def _s977_secs(sdelta):
    secs = {}
    for (s, _t), v in sdelta.items():
        secs[s] = secs.get(s, 0) + v
    return secs


def _s977_left(con, d, cards, delta, sdelta, paid_lines, lines):
    """S977 (K2.2, K2.3): what the money leaves after every slip, refund and radd -- one card, by the sign of the one figure."""
    left = sum(delta.values())
    secs = _s977_secs(sdelta)
    if left > 0:                                         # register MORE: whose money was it?
        t = max(TENDERS, key=lambda x: delta[x])
        pos = sorted(((v, s) for s, v in secs.items() if v > 0 and s in SEC_EN), reverse=True)
        sec = pos[0][1] if pos else "consult"
        cands = _s977_cands(con, d, lines)
        who_en = ("Patients of the day with no paid bill: %s" % _s977_names(cands)) if cands else "Every patient of the day has a paid bill"
        who_hi = ("Din ke bina-bill mareez: %s" % _s977_names(cands)) if cands else "Din ke sab mareez ka bill hai"
        cards.append(_card("notfound", "nf:%s:%d" % (sec, left), left, d, who="docterz", tender=t, section=sec, cands=cands,
                           en="%s %s — in the register, not in Docterz. %s — whose was it? Make the parchi; it is kept outside "
                              "Docterz by itself (no Docterz edit)" % (rs(left), SEC_EN[sec], who_en),
                           hi="%s %s — register mein hai, Docterz mein nahi. %s — kiska tha? Parchi banaiye; Docterz ke bahar "
                              "apne aap (Docterz nahi badalna)" % (rs(left), SEC_HI[sec], who_hi)))
    elif left < 0:                                       # register LESS, after refunds and radd
        g = -left
        one = [s for s, v in secs.items() if v == -g and s in SEC_EN]
        rest_ok = len(one) == 1 and all(v == 0 for s, v in secs.items() if s != one[0])
        same = [ln for ln in paid_lines if rest_ok and ln["section"] == one[0] and ln["amount_p"] == g
                and ln["tender"] in TENDERS + ("legs",)] if one else []
        if same:
            sec = one[0]
            heads = [ln for ln in paid_lines if ln["section"] == sec and ln["amount_p"] > 0]
            dsum = sum(ln["amount_p"] for ln in heads)
            cands, seen = [], set()
            for ln in same:
                if ln["cid"] and ln["cid"] not in seen:
                    seen.add(ln["cid"])
                    cands.append((ln["cid"], ln["patient"]))
            cards.append(_card("less", "less:%s:%d" % (sec, g), g, d, who="docterz", section=sec, cands=cands,
                               en="Docterz has %s %s more than the register (%d bills, %s; register %s) — was the register "
                                  "written wrong, or did one patient not pay: who?" % (SEC_EN[sec], rs(g), len(heads), rs(dsum), rs(dsum - g)),
                               hi="Docterz mein %s %s zyada (%d bill, %s; register %s) — register galat likha, ya ek mareez ne "
                                  "paise nahi diye — kaun?" % (SEC_HI[sec], rs(g), len(heads), rs(dsum), rs(dsum - g))))
        else:
            cards.append(_card("hand", "less:%d" % g, g, d,
                               en="Docterz has %s more than the register — not explained (refunds and radd already counted)" % rs(g),
                               hi="Docterz mein register se %s zyada — pata nahi (wapsi aur radd gine ja chuke)" % rs(g)))
    return left


def breakdown(chk, english=False):
    """S977 (K2.5): 'Register Rs 7,700 = Docterz Rs 7,600 + parchi bahar Rs 100 - wapas Rs 0 . 22 mareez mile'."""
    tp = chk.get("top") or {}
    if english:
        return "Register %s = Docterz %s + slips kept outside %s − refunded / never taken %s · %d patients matched" % (
            rs(tp.get("reg")), rs(tp.get("doc")), rs(tp.get("nid")), rs(tp.get("back")), int(chk.get("matched_n") or 0))
    return "Register %s = Docterz %s + parchi bahar %s − wapas %s · %d mareez mile" % (
        rs(tp.get("reg")), rs(tp.get("doc")), rs(tp.get("nid")), rs(tp.get("back")), int(chk.get("matched_n") or 0))


def check_day(con, d):
    """The day's corrections.''', "defs")

t = sub(t, '''    out = dict(day=d, docterz=bool(lines), register=reg is not None, bank_known=bank_known, cards=[], notes=[])
    if not lines or reg is None:''', '''    out = dict(day=d, docterz=bool(lines), register=reg is not None, bank_known=bank_known, cards=[], notes=[])
    rev = out["rev"] = revenue_on()                      # S977 (D1099): the morning as a revenue match
    if not lines or reg is None:''', "rev")

t = sub(t, '''            cards.append(_card("missing", w["key"], w["amount"], d, who="docterz", tender=t, cid=w["cid"], name=w["name"],''',
'''            if rev:                                       # S977 (D1099): no Docterz edit the next morning -- kept outside by itself
                nid_placed += w["amount"]
                out["notes"].append(("%s %s · %s — kept outside Docterz by itself (the register holds it; no Docterz edit the next "
                                     "morning)" % (rs(w["amount"]), w["what_en"], _who_en(w["name"], w["cid"])),
                                     "%s %s · %s — Docterz ke bahar, apne aap (register mein hai; agle din Docterz nahi badalna)"
                                     % (rs(w["amount"]), w["what_hi"], _who_en(w["name"], w["cid"]))))
                continue
            cards.append(_card("missing", w["key"], w["amount"], d, who="docterz", tender=t, cid=w["cid"], name=w["name"],''', "missing")

t = sub(t, '''            cards.append(_card("notbilled", w["key"], w["amount"], d, who="docterz", cid=w["cid"], name=w["name"],''',
'''            if rev:                                       # S977: neither billed nor collected -- the evening's matter, no morning card
                out["notes"].append(("%s on the parchi — not billed, not in the register · %s · %s (nothing collected)" % (
                    rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"]),
                    "%s parchi par — na bill hua, na register mein · %s · %s (paise nahi aaye)" % (
                    rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"])))
                continue
            cards.append(_card("notbilled", w["key"], w["amount"], d, who="docterz", cid=w["cid"], name=w["name"],''', "notbilled")

t = sub(t, '''    # --- 3 · payment modes: money in one tender of Docterz that the register holds in another
''', '''    if rev:                                              # S977 (D1099): money against money only -- no tender split, no mode card
        out["s977_left"] = _s977_left(con, d, cards, delta, sdelta, paid_lines, lines)
        delta = dict.fromkeys(TENDERS, 0)                # sections 3 and 4 below then find nothing to move or name
        bank_known = False                               # the bank stays on his page as information (_bank_html)
    # --- 3 · payment modes: money in one tender of Docterz that the register holds in another
''', "sec3")

t = sub(t, '''    for p in parchi_side:
        cards.append(_parchi_card(p, d))
''', '''    _ev_told = _s977_evening_told(con, d) if rev else set()   # S977: what the evening told reception the same day
    _ev_n = 0
    for p in parchi_side:
        _ps = p.get("slip") or {}
        if (p["kind"] in ("dup_item", "parchi_short", "parchi_over") and _ps.get("id")
                and (int(_ps["id"]), p.get("section")) in _ev_told):
            _ev_n += 1
            continue
        cards.append(_parchi_card(p, d))
    if _ev_n:
        out["notes"].append(("%d slip line%s told to reception by the evening check the same day — no morning card" % (_ev_n, "" if _ev_n == 1 else "s"),
                             "%d parchi line shaam ki jaanch ne usi din bataayi — subah koi card nahi" % _ev_n))
''', "sec5")

t = sub(t, '''    c = dict(missing_p=0, missing_n=0, notfound_p=0, modes=0, parchi=0, notbilled=0, notbilled_p=0, hand=0)''',
'''    c = dict(missing_p=0, missing_n=0, notfound_p=0, modes=0, parchi=0, notbilled=0, notbilled_p=0, hand=0, less=0)''', "counts0")
t = sub(t, '''        elif x["kind"] == "hand":
            c["hand"] += 1
    return c''', '''        elif x["kind"] == "hand":
            c["hand"] += 1
        elif x["kind"] == "less":                        # S977
            c["less"] += 1
    return c''', "counts1")

# the 'less' card's buttons, and the not-found card's picker leads with the patients who have no paid bill
t = sub(t, '''        elif c["kind"] == "notfound":
            opts = _day_people(con, d)''', '''        elif c["kind"] == "less":                        # S977 (K2.3): register wrong, or who did not pay
            btns.append("<a class='tb' href='/finance/clinic/register/%s'>%s</a>" % (
                d, "The register was wrong" if english else "Register galat tha"))
            if c.get("cands") and _SA() is not None:
                sel = "".join("<option value='%s'>%s</option>" % (_esc(cid), _esc(_who_en(nm, cid))) for cid, nm in c["cands"])
                btns.append(_btn(d, c["key"], "lessnp", "Did not pay" if english else "Paise nahi diye", "x",
                                 "<select name='pick' class='rs'>%s</select>" % sel))
        elif c["kind"] == "notfound":
            opts = _day_people(con, d)
            if c.get("cands"):                           # S977: the day's patients with no paid bill first
                _cs = [x[0] for x in c["cands"]]
                opts = list(c["cands"]) + [o for o in opts if o[0] not in _cs]''', "onecard")

t = sub(t, '''        if a in ("notpaid", "free") and card["who"] == "docterz" and can_docterz(u):''',
'''        if a == "lessnp" and card.get("kind") == "less" and can_docterz(u):   # S977 (K2.3)
            return done(*_s977_lessnp(con, date, card, (f.get("pick") or "")[:12], who, english))
        if a in ("notpaid", "free") and card["who"] == "docterz" and can_docterz(u):''', "act")

t = sub(t, '''def _q(s):''', '''def _s977_lessnp(con, d, card, pick, who, english):
    """S977 (K2.3): the picked patient did not pay -- slip_adjust's own 'money never taken' radd on that patient's one slip of
    the head (pending his approval, as every radd). Refused when the pick is not on the card, or the patient has no single slip
    of that head and amount. -> (ok, er)."""
    if not pick or pick not in [c for c, _n in (card.get("cands") or [])]:
        return "", ("Pick a patient from the list." if english else "List mein se mareez chuniye.")
    sa = _SA()
    if sa is None:
        return "", ("The radd entry is not reachable — tell Dr Manoj." if english else "Radd entry nahi ho saki — Dr sahab ko batayein.")
    sec, g = card.get("section"), int(card.get("amount") or 0)
    hit = []
    for s in _parchi(con, d):
        if str(s.get("clinic_id") or "") != pick or s.get("cancel"):
            continue
        if sec == "consult" and s["series"] == "opd":
            hit.append(s)
        elif sec in ("xray", "proc") and s["series"] == "xp":
            its = s.get("items") or []
            if its and all(it.get("kind") == sec for it in its) and sum(int(it.get("expect_p") or 0) for it in its) == g:
                hit.append(s)
    if len(hit) != 1:
        return "", (("No single parchi of this patient for this bill (%d found) — tell Dr Manoj." % len(hit)) if english else
                    ("Is bill ki ek parchi nahi mili (%d) — Dr sahab ko batayein." % len(hit)))
    # review M4: the radd must take out exactly this one bill -- tried first as the day check will read it
    lines, _legs = _docterz(con, d)
    slips = _parchi(con, d)
    for s in slips:
        if s["id"] == hit[0]["id"]:
            s["cancel"] = {"state": "pending"}
    if hit[0]["series"] == "opd":
        try:
            fee = int(_SL().usual_fee(con, d) or 0) if _SL() is not None else 0
        except Exception:                                # noqa: BLE001
            fee = 0
        items = [("consult", fee, "")]
    else:
        items = _s962_items(con, hit[0]["id"])
    trial = dict(slip_id=hit[0]["id"], series=hit[0]["series"], slip_no=hit[0]["slip_no"], cid=pick, how="never_taken", tender="",
                 state="pending", made_by=who, made_at="", paid="", items=items, amount=sum(x[1] for x in items), name="")
    before, _r = _s962_hold(lines, _parchi(con, d), _cancels(con, d))
    after, _r = _s962_hold(lines, slips, _cancels(con, d) + [trial])
    took = [ln for ln in lines if (ln["section"], ln["sn"]) in after and (ln["section"], ln["sn"]) not in before]
    if len(took) != 1 or took[0]["amount_p"] != g or took[0]["section"] != sec or took[0]["cid"] != pick:
        return "", ("This patient's parchi would not take out exactly this one bill — tell Dr Manoj." if english else
                    "Is mareez ki parchi se theek yahi ek bill nahi hatega — Dr sahab ko batayein.")
    try:
        sa.add_cancel(con, who, int(hit[0]["id"]), pick, "never_taken", note="day check S977")
    except Exception as ex:                              # noqa: BLE001 -- slip_adjust's own refusal (7 days, already radd) as it is
        try:
            con.rollback()
        except Exception:                                # noqa: BLE001
            pass
        return "", str(ex)[:200]
    return ("Sent for approval — the day matches once it is in." if english else "Manzoori ke liye gaya — din mil jayega."), ""


def _q(s):''', "lessnp")
t = sub(t, '''        t = ticks.get(c["key"])
        c["tick"], c["not_fixed"] = t, None''', '''        t = ticks.get(c["key"])
        if t is None and rev and str(c["key"]).startswith("nf:"):   # S977 (second look): a tick under the old key, with its tender
            _p = str(c["key"]).split(":")
            t = next((ticks[k] for k in ["nf:%s:%s" % (x, ":".join(_p[1:])) for x in TENDERS] if k in ticks), None)
        c["tick"], c["not_fixed"] = t, None''', "oldtick")
t = sub(t, '''    if a == "undo":
        undo_tick(con, date, key, who)''', '''    if a == "undo":
        undo_tick(con, date, key, who)
        if key.startswith("nf:") and key.count(":") == 2:   # S977 (re-look): a tick under the old key, with its tender
            for _t in TENDERS:
                undo_tick(con, date, "nf:%s:%s" % (_t, key[3:]), who)''', "undo_old")
t = sub(t, '''    out["reexport"] = bool(dcs) and all(c["tick"] for c in dcs) and any(c["tick"]["act"] in ("added", "changed", "found") for c in dcs)''',
'''    _rx = ("added", "changed") if rev else ("added", "changed", "found")   # S977 (review): a money-only day asks for no re-export
    out["reexport"] = bool(dcs) and all(c["tick"] for c in dcs) and any(c["tick"]["act"] in _rx for c in dcs)''', "reexport")
t = sub(t, '''            add_tick(con, date, key, a, who, reason=reason, pick=(f.get("pick") or "")[:12])
            return done(''', '''            add_tick(con, date, key, a, who, reason=reason, pick=(f.get("pick") or "")[:12])
            if a == "found" and chk.get("rev"):          # S977 (review): no Docterz edit -- the parchi settles it
                return done("Noted. Make the parchi; the day matches by itself." if english
                            else "Likh liya. Parchi banaiye; din apne aap mil jayega.")
            return done(''', "foundmsg")
open(os.path.join(dst, "day_check.py"), "wb").write(t.encode("utf-8"))

# ============================================================== register_push.py
t = load("register_push.py")
t = sub(t, '''No patient name, no number, no secret in this file (F-185). A push carries the day check's own line words.''',
'''S977 (session S544, 28-Nov-2026; D1099 K2.5 / K2.6 -- the morning as a revenue match): the clean push carries the day's sum
(day_check.breakdown); a staff line's lasting name drops the amount of 'nf:' and 'less:' keys alike; and HIS push -- what nobody
else can explain (the day check's 'check by hand' lines 'less:' and 's962ans:') goes to his own devices only (day_check's S962
road, never the staff topic), once per day per line (register_push.owner_sent, one additive column). REGPUSH_OWNER=0 turns his
push alone off. A seeded old day is never pushed to him (recorded as told). A full return to the S970 morning is DAYCHK_REVENUE=0
AND REGPUSH_OWNER=0 (the clean push's one-line sum stays; it only describes).
No patient name, no number, no secret in this file (F-185). A push carries the day check's own line words.''', "rp_doc")
t = sub(t, '''VERSION = "S970 1"''', '''VERSION = "S977 1"
OWNER = "manoj"                                           # S977: his login -- his own devices only
OWNER_KEYS = ("less:", "s962ans:")                        # S977: the lines nobody else can explain
QUIET = False                                             # S977: --quiet (the installer): record every line as told, push nothing''', "rp_ver")
t = sub(t, '''def ensure(con):
    con.executescript(DDL)
    con.commit()''', '''def ensure(con):
    con.executescript(DDL)
    try:                                                  # S977: one additive column -- the lines already told to him
        cols = [r[1] for r in con.execute("PRAGMA table_info(register_push)")]
        if "owner_sent" not in cols:
            con.execute("ALTER TABLE register_push ADD COLUMN owner_sent TEXT NOT NULL DEFAULT ''")
    except sqlite3.Error:
        pass
    con.commit()''', "rp_ensure")
t = sub(t, '''    return re.sub(r":\\d+$", "", k) if k.startswith("nf:") else k''',
'''    return re.sub(r":\\d+$", "", k) if k.startswith(("nf:", "less:")) else k     # S977: 'less:' as 'nf:\'''', "rp_norm")
t = sub(t, '''def auto_on():''', '''def owner_on():
    return cfg("REGPUSH_OWNER", "1").lower() not in ("0", "off", "no", "false")


def owner_lines(chk):
    """S977: {key: words} of the lines nobody but him can explain -- 'check by hand' 'less:' / 's962ans:', not ticked."""
    out = {}
    for c in chk.get("cards") or []:
        k = str(c.get("key") or "")
        if c.get("who") == "hand" and k.startswith(OWNER_KEYS) and not c.get("tick"):
            out[k] = (c.get("en") or c.get("hi") or "", int(c.get("amount") or 0))
    return out


def owner_told(con, day):
    """S977: the lasting names already told to him for the day -- read BEFORE the row is rewritten (review M1). None when the
    column cannot be read: then he is not pushed at all (second look: never a push that cannot be remembered)."""
    try:
        r = con.execute("SELECT owner_sent FROM register_push WHERE day=?", (day,)).fetchone()
        return set(k for k in ((r[0] if r else "") or "").split(",") if k)
    except sqlite3.Error:
        return None


def tell_owner(con, dc, day, chk, push, outcome, told, at=None):
    """S977 (K2.6): his push, once per day per line (by its lasting name -- a changed gap is not a new line). Returns the
    owner_sent text to keep."""
    if told is None:
        return None
    told = set(told)
    lines = {}
    for k, v in owner_lines(chk).items():
        lines.setdefault(_norm(k), v)
    new = [k for k in sorted(lines) if k not in told]
    old_day = day < ((at or now_ist()).date() - dt.timedelta(days=1)).isoformat()   # re-look: the judge's own clock
    if (QUIET and old_day) or outcome == "seeded":       # the installer's quiet sweep (days before yesterday), an old day met first
        return ",".join(sorted(told | set(new)))
    if QUIET:                                             # second look: yesterday and today still reach him at the next sweep
        return ",".join(sorted(told))
    if not new or not push or not is_on() or not owner_on():
        return ",".join(sorted(told))
    amt = sum(lines[k][1] for k in new)
    title = "%s: Rs %s not explained" % (dm(day), "{:,}".format(int(round(amt / 100.0))))
    body = " ; ".join(lines[k][0] for k in new if lines[k][0])[:300]
    try:
        s, why = dc._s962_push(con, (OWNER,), title, body, "/finance/clinic/check/%s" % day, "daycheck-owner-" + day)
    except Exception as ex:                               # noqa: BLE001
        s, why = 0, "send: %s" % str(ex)[:60]
    if s:                                                 # review S6: told only when a device of his took it
        told.update(new)
    return ",".join(sorted(told))


def auto_on():''', "rp_owner")
t = sub(t, '''        title, body = "✓ %s: register, Docterz aur parchi sab mile" % dm(day), "Kuch nahi karna"''',
'''        try:                                              # S977 (K2.5): the day's sum in one line
            bd = dc.breakdown(chk)
        except Exception:                                 # noqa: BLE001
            bd = ""
        title, body = "✓ %s: register, Docterz aur parchi sab mile" % dm(day), (bd or "Kuch nahi karna")''', "rp_clean")
t = sub(t, '''    if outcome == "quiet" and prev is not None:
        con.execute("UPDATE register_push SET keys=?''', '''    _told = owner_told(con, day)                          # S977 (review M1): before INSERT OR REPLACE empties it
    if outcome == "quiet" and prev is not None:
        con.execute("UPDATE register_push SET keys=?''', "rp_told")
t = sub(t, '''                    (day, ",".join(keys), len(keys), _stamp(at), outcome, sent))
    con.commit()''', '''                    (day, ",".join(keys), len(keys), _stamp(at), outcome, sent))
    try:                                                  # S977 (K2.6): his own push -- after the row is written, so it is kept
        _os = tell_owner(con, dc, day, chk, push, outcome, _told, at)
        if _os is not None:
            con.execute("UPDATE register_push SET owner_sent=? WHERE day=?", (_os, day))
    except Exception:                                     # noqa: BLE001 -- the staff push stands without it
        pass
    con.commit()''', "rp_write")
t = sub(t, '''    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args(argv)''', '''    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--quiet", action="store_true")       # S977: with --sweep at install -- the week recorded, nothing sent
    a = ap.parse_args(argv)
    if a.quiet:
        globals()["QUIET"] = True
        a.no_push = True''', "rp_quiet")
open(os.path.join(dst, "register_push.py"), "wb").write(t.encode("utf-8"))

# ============================================================== docterz_pickup.py
t = load("docterz_pickup.py")
t = sub(t, '''        elif s868_empty == "worked":
            st = "quarantined"                                 # S868: an empty report never stands for a day he worked''',
'''        elif s868_empty == "worked" and con.execute("SELECT 1 FROM docterz_export WHERE kind=? AND business_date=? AND status='current' "
                                                    "AND rows>0", (kind, day)).fetchone() is not None:
            st, note = "superseded", "an empty report after the day's real export -- nothing to take (F-1732)"   # S977
        elif s868_empty == "worked":
            st = "quarantined"                                 # S868: an empty report never stands for a day he worked''', "dp_take")
t = sub(t, '''                             "AND NOT (kind='consultation' AND rows=0 AND note='no date in the file') "            # S868: the old empty ones''',
'''                             "AND NOT (kind='consultation' AND rows=0 AND note='no date in the file') "            # S868: the old empty ones
                             "AND NOT (kind='consultation' AND rows=0 AND EXISTS (SELECT 1 FROM docterz_export g WHERE g.kind='consultation' "
                             "AND g.business_date=docterz_export.business_date AND g.status='current' AND g.rows>0)) "   # S977 (F-1732)''', "dp_warn")
open(os.path.join(dst, "docterz_pickup.py"), "wb").write(t.encode("utf-8"))
print("BUILT")
