#!/usr/bin/env python3
"""make_s951.py -- S951_YESTERDAY_CARRY (the parent, S517, 25-Nov-2026; D1063, his "yes" 20:43 IST 24-Nov, widened 10:02 IST 25-Nov):
makes the TO bytes of /root/portal/calls_staff.py from its FROM bytes (S948, 05caf1c3, CONFIRMED by the 25-Nov bundle). Every missed call of
yesterday still unresolved (no call, no WhatsApp, no Docterz visit since) comes onto today's staff lists. Every anchor must occur exactly once, or
nothing is written.
  python make_s951.py <from calls_staff.py> <out dir>
"""
import hashlib
import os
import sys

FROM = "05caf1c3"

BLOCK = '''    # -- S951_YESTERDAY_CARRY (the parent, S517, 25-Nov-2026; D1063 his "yes" 20:43 24-Nov, widened by his word 10:02 IST
    # 25-Nov): EVERY missed call of yesterday still unresolved comes onto today's lists, on the missed-call path.
    # Unresolved = no connected call after it (that day or today), no WhatsApp from him after it (the WhatsApp tab has
    # him then), and no Docterz visit from yesterday on (finance.db patient_visit, read-only, by clinic ID or by the
    # mobile's fingerprint -- a patient on another mobile is caught once Docterz holds that mobile). Today is a fresh day
    # for tries: none -> Incoming missed, one -> Call again, two -> Evening calls, a third ends it; yesterday's tries are
    # said on the line. A miss from 21:00 on (PORTAL_STAFF_AFTER_HOURS_FROM) reads "Missed after hours", any other
    # "Missed yesterday, not reached". Today's own missed call for the number wins (that row already stands). Read-only;
    # a fault here costs the carry only ("carry_ok": False), never the page.
    out["carry_ok"], out["carry_visits_ok"] = True, None
    try:
        yday = today - _dt.timedelta(days=1)
        y = yday.isoformat()
        ah_from = _dt.datetime.combine(yday, _hm_cfg("PORTAL_STAFF_AFTER_HOURS_FROM", AFTER_HOURS_FROM_DEFAULT))
        Ly = CC.wa_load(conn, y, y, now, inbox_path)
        people_y, _iy, _ny = CC.build_people(conn, y, y, now, wa=Ly["span"], ctx=Ly["ctx"], dz=Ly["dz"])
        cand = []
        for py in people_y:
            ph = py.get("phone") or ""
            if py.get("spam") or py.get("not_patient") or not ph or ph in missed_phones:
                continue
            p_t = byp.get(ph)
            if p_t is not None and (p_t.get("spam") or p_t.get("not_patient")):
                continue
            ycalls = [x for x in py["calls"] if x.get("ch") != "wa"]
            ymiss = sorted((x for x in ycalls if x["kind"] == "in_miss" and x["t"] is not None), key=lambda x: x["t"])
            if not ymiss:
                continue
            yans = [x["t"] for x in ycalls if x["answered"] and x["t"] is not None]
            last_ans = max(yans) if yans else None
            open_ = [m for m in ymiss if last_ans is None or m["t"] > last_ans]
            if not open_:
                continue                                 # reached after it the same day
            first = open_[0]
            if any(x.get("kind") == "wa_in" and x.get("t") is not None and x["t"] > first["t"] for x in py["calls"]):
                continue                                 # he wrote after the missed call: the WhatsApp tab has him
            tcalls = [x for x in (p_t["calls"] if p_t else []) if x.get("ch") != "wa"]
            if any(x["answered"] for x in tcalls):
                continue                                 # reached today: off the lists by himself
            if p_t is not None and any(x.get("kind") == "wa_in" for x in p_t["calls"]):
                continue                                 # he wrote today: the WhatsApp tab has him
            cand.append((py, ph, ycalls, open_, first, tcalls))
        visits, R = {"ok": False, "by_id": {}, "by_fp": {}}, None
        if cand:
            try:
                R = CC._ro()
                visits = R.visits_since(y, today, fin_db)
            except Exception:
                R, visits = None, {"ok": False, "by_id": {}, "by_fp": {}}
            thr = visits.get("through")
            out["carry_visits_ok"] = bool(visits.get("ok") and thr is not None and thr >= yday)   # yesterday's export in
        ids_n = {}
        for k_, v_ in (visits.get("by_id") or {}).items():
            ids_n.setdefault(CC._cid_key(k_), []).extend(v_)
        for py, ph, ycalls, open_, first, tcalls in cand:
            pt = pats.get(ph) or {}
            cid = CC._cid_key(py.get("cid") or pt.get("cid") or "")
            came = bool(cid and any(d >= yday for d in ids_n.get(cid, ())))
            if not came and R is not None and visits.get("ok"):
                try:
                    fp = R._mobile_fp(ph)
                except Exception:
                    fp = ""
                came = bool(fp and any(d >= yday for d, _c in visits["by_fp"].get(fp, ())))
            if came:
                continue                                 # a Docterz visit since: resolved
            atts = sorted((x for x in tcalls if x["direction"] == "Out" and not x["answered"] and x["t"] is not None),
                          key=lambda x: x["t"])
            n = len(atts)
            if n >= MAX_TRIES:
                continue                                 # a third unanswered try today ends it (the follow-up path keeps him)
            missed_phones.add(ph)
            out["carry_n"] = out.get("carry_n", 0) + 1
            ytries = sum(1 for x in ycalls if x["direction"] == "Out" and not x["answered"] and x["t"] is not None
                         and x["t"] > first["t"])
            name = py.get("name") or pt.get("name", "")
            unknown = py.get("unknown")
            dx = py.get("dx") or pt.get("dx", "")
            times = ", ".join(m["t_h"] for m in open_ if m["t_h"])
            word = "Missed after hours" if all(m["t"] >= ah_from for m in open_) else "Missed yesterday, not reached"
            head = ("%s (%s)" % (word, times)) if len(open_) == 1 else ("%s %d (%s)" % (word, len(open_), times))
            bits = [head]
            if ytries:
                bits.append("tried %d time%s yesterday" % (ytries, "" if ytries == 1 else "s"))
            tail = "new number - may be a patient on another mobile" if unknown else dx
            if n == 0:
                if len(open_) == 1:
                    bits.append(CC.wait_words(CC.wait_h(first["t"], now)))
                bits.append(tail)
                missed.append(row(ph, name, unknown, " · ".join(b for b in bits if b), hi=True, kind="missed",
                                  sort=" " + first["t"].strftime("%H:%M:%S"), dx=dx))
            elif n == 1:
                a = atts[0]
                due_t = a["t"] + _dt.timedelta(hours=again_h)
                bits += ["call back %s %s" % (a["t_h"], _att_word(a)), tail]
                again.append(row(ph, name, unknown, " · ".join(b for b in bits if b), hi=(now >= due_t), kind="missed",
                                 sort=due_t.strftime("%H:%M:%S"), dx=dx))
            else:
                bits += ["2 attempts (%s) · last attempt today" % ", ".join(a["t_h"] for a in atts), tail]
                eve.append(row(ph, name, unknown, " · ".join(b for b in bits if b), hi=evening, kind="missed",
                               sort="0" + atts[-1]["t"].strftime("%H:%M:%S"), dx=dx))
    except Exception as _e_s951:                                 # noqa: BLE001
        out["carry_ok"] = False
        print("calls_staff: the yesterday carry failed: %r" % (_e_s951,), file=sys.stderr)

    # -- the follow-up path
'''

EDITS = [
    ('VERSION = "S948 1.0"\n',
     'VERSION = "S951 1.1"           # S948 1.0 + S951_YESTERDAY_CARRY (D1063, his word 10:02 25-Nov)\n'),
    ('EVENING_TO_DEFAULT = "18:00"\n',
     'EVENING_TO_DEFAULT = "18:00"\n'
     'AFTER_HOURS_FROM_DEFAULT = "21:00"   # S951: a miss from this time reads "Missed after hours" (his word 10:02 25-Nov)\n'),
    ('                     missed-call path.\n',
     '                     missed-call path.\n'
     '                     S951 (D1063, his word 10:02 25-Nov): EVERY missed call of yesterday still unresolved -- no\n'
     '                     connected call, no WhatsApp from him, no Docterz visit since -- is on today\'s lists on this path\n'
     '                     ("Missed after hours" from 21:00, else "Missed yesterday, not reached"); today is a fresh day for\n'
     '                     tries, yesterday\'s are said on the line.\n'),
    ('    # -- the follow-up path\n', BLOCK),
    ('    clear = "All clear — no callbacks pending."\n',
     '    clear = "All clear — no callbacks pending."\n'
     '    if d.get("carry_ok") is False:                    # S951: said, never silent\n'
     '        missed_warn = "Yesterday\'s missed calls could not be read just now - try again in a few minutes."\n'
     '    elif d.get("carry_visits_ok") is False and d.get("carry_n"):    # only when a carried row is on the lists\n'
     '        missed_warn = "Docterz visits are not up to date - a caller from yesterday may already have come. Check before calling."\n'
     '    else:\n'
     '        missed_warn = ""\n'),
    ('         "title": "Needs a callback now", "warn": "", "empty": clear,\n',
     '         "title": "Needs a callback now", "warn": missed_warn, "empty": clear,\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(a):
    src, out = a[1], a[2]
    raw = open(src, "rb").read()
    if md5(raw)[:8] != FROM:
        sys.exit("calls_staff.py is not the FROM bytes (%s) -- stop" % md5(raw)[:8])
    txt = raw.decode("utf-8")
    for old, new in EDITS:
        n = txt.count(old)
        if n != 1:
            sys.exit("anchor found %d times -- stop: %r" % (n, old[:60]))
        txt = txt.replace(old, new)
    os.makedirs(out, exist_ok=True)
    b = txt.encode("utf-8")
    open(os.path.join(out, "calls_staff.py"), "wb").write(b)
    print("calls_staff.py %s -> %s  (%d -> %d bytes)" % (FROM, md5(b)[:8], len(raw), len(b)))


if __name__ == "__main__":
    main(sys.argv)
