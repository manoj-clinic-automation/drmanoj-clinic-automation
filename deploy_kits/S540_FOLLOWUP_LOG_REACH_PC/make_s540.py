#!/usr/bin/env python3
"""make_s540.py -- kit S540 (session 311, 12-Oct-2026): manojz's docterz_pickup.py, S239 rev 2 (d117786f) -> S540.
Exact, counted, anchored edits on the live bytes; the new text is built in memory first; nothing is written unless every
anchor occurs exactly once.      python3 make_s540.py <docterz_pickup.py FROM> <out>"""
import hashlib
import sys

FROM_MD5 = "d117786f435906976aafd63446d7c88e"

E = []
E.append(("version", '''VERSION = "S239 rev 2"''', '''VERSION = "S540 (S239 rev 3)"'''))
E.append(("docstring", '''     calls -- with that day's report and the newest follow-up log. Then, as /run does, it sends the''',
'''     calls -- with that day's report and the follow-up log that REACHES its call day (S540: the newest
     log whose due dates reach the next working day; a newer one-day export never displaces it). Then, as /run does, it sends the'''))
E.append(("helpers", '''def uids(rows):
    return {(r.get("Patient UID") or "").strip() for r in rows}
''', '''def uids(rows):
    return {(r.get("Patient UID") or "").strip() for r in rows}


# ───────────────────────────────────────────────────────────────────────────── S540: which follow-up log a day pairs with
FU_WINDOW_DAYS = 4            # a log older than the newest by more than this is never preferred


def next_call_day(iso):
    """S540: the clinic's next call day after a business day -- Sunday is emergency-only (processor.py's own rule)."""
    d = _dt.date.fromisoformat(iso) + _dt.timedelta(days=1)
    if d.weekday() == 6:
        d += _dt.timedelta(days=1)
    return d.isoformat()


def log_reach(path):
    """S540: the last due date a follow-up log holds ('' when unreadable or empty)."""
    try:
        _h, body, _r = read_rows(path)
    except (OSError, UnicodeDecodeError, csv.Error):
        return ""
    ds = [iso_of(r.get("Followup Date")) for r in body if (r.get("Appointment ID") or "").strip()]
    ds = [x for x in ds if x]
    return max(ds) if ds else ""
'''))
E.append(("pick method", '''    def run_tracker(self, cons_path, fu_path, d, latest):''', '''    def pick_followup(self, st, day, extra=()):
        """S540: the follow-up log a run of `day` pairs with -- the NEWEST log whose due dates REACH the day's call day.
        A newer log that stops short (a one-day export) never displaces one that reaches; only logs within FU_WINDOW_DAYS
        of the newest are weighed; when none reaches, the newest. (path, reach, why) or (None, '', why)."""
        want = next_call_day(day)
        cands = {}
        for v in st["seen"].values():
            p = v.get("archived")
            if v.get("type") == "FOLLOWUP_LOG" and p and os.path.exists(p):
                cands[p] = float(v.get("mtime") or os.path.getmtime(p))
        for p in extra:
            if p and os.path.exists(p):
                cands[p] = os.path.getmtime(p)
        if not cands:
            for p in glob.glob(os.path.join(self.uploads, "followup_logs*.csv")):
                cands[p] = os.path.getmtime(p)
        if not cands:
            return None, "", "no follow-up log anywhere"
        ranked = sorted(cands.items(), key=lambda kv: kv[1], reverse=True)
        newest, top = ranked[0]
        for p, m in ranked:
            if top - m > FU_WINDOW_DAYS * 86400:
                break
            r = log_reach(p)
            if r and r >= want:
                return p, r, ("the newest log reaching %s" % want) if p == newest else (
                    "reaches %s; the newer %s stops at %s" % (want, os.path.basename(newest), log_reach(newest) or "?"))
        return newest, log_reach(newest), "no log reaches %s -- the newest" % want

    def reach_used(self, st, info):
        """S540: for a day processed before S540, the reach of the log it was paired with (the newest seen by then)."""
        at = str(info.get("processed_at") or "")
        best = None
        for v in st["seen"].values():
            if v.get("type") == "FOLLOWUP_LOG" and v.get("archived") and str(v.get("seen_at") or "") <= at:
                if best is None or float(v.get("mtime") or 0) > float(best.get("mtime") or 0):
                    best = v
        return log_reach(best["archived"]) if best and os.path.exists(best["archived"]) else ""

    def run_tracker(self, cons_path, fu_path, d, latest):'''))
E.append(("refresh pick", '''        fus = [p for p in self.candidates() if classify(read_rows(p)[0]) == "FOLLOWUP_LOG"]
        fus += glob.glob(os.path.join(self.uploads, "followup_logs*.csv"))
        fu = max(fus, key=os.path.getmtime) if fus else None
''', '''        fus = [p for p in self.candidates() if classify(read_rows(p)[0]) == "FOLLOWUP_LOG"]
        fu, _reach, _why = self.pick_followup(st, latest, fus) if latest else (None, "", "")   # S540
'''))
E.append(("pass block", '''        # the follow-up log a run pairs with: the newest one ever seen
        fu = new_followup
        if fu is None:
            known = [v for v in st["seen"].values() if v.get("type") == "FOLLOWUP_LOG"
                     and v.get("archived") and os.path.exists(v["archived"])]
            if known:
                fu = max(known, key=lambda v: v.get("mtime", 0))["archived"]
        if fu is None:
            ups = glob.glob(os.path.join(self.uploads, "followup_logs*.csv"))
            fu = max(ups, key=os.path.getmtime) if ups else None

        latest_known = max([d for d in st["days"]] + list(todo), default="")
        ran = []
        for d in sorted(todo):
            cands_d = sorted(todo[d], key=lambda x: x[0])
            mt, p, header, raw, rows, md5, single = cands_d[-1]
            if fu is None:
                self.shout("no follow-up log anywhere -- %s NOT run; export the follow-up log too" % d)
                continue
            cons_in = self.place_input(p, md5) if single else self.write_day_file(p, raw, header, d, rows)
            fu_in = self.place_input(fu, md5_of(fu))
            ok = self.run_tracker(cons_in, fu_in, d, latest=(d >= latest_known))
            if ok:
                st["days"][d] = {"digest": day_digest(rows), "uids": len(uids(rows)),
                                 "input": cons_in, "source_md5": md5, "processed_at": stamp(),
                                 "src_mtime": mt, "how": "auto"}
                ran.append(d)
        # a new follow-up log alone: refresh the latest day's call list with it
        if new_followup and not ran and latest_known:
            age = (self.today - _dt.date.fromisoformat(latest_known)).days
            info = st["days"].get(latest_known, {})
            cons_in = info.get("input")
            if age <= 1 and cons_in and os.path.exists(cons_in):
                fmd5 = md5_of(new_followup)
                if self.already_run_by_hand(fmd5):
                    self.say("the new follow-up log was already processed on the /run page")
                else:
                    fu_in = self.place_input(new_followup, fmd5)
                    if self.run_tracker(cons_in, fu_in, latest_known, latest=True):
                        ran.append(latest_known + " (follow-up refresh)")
            else:
                self.say("new follow-up log archived; the latest day (%s) is not recent, so no re-run"
                         % latest_known)
''', '''        # S540: the follow-up log a run pairs with is the newest one that REACHES the run's call day (pick_followup)
        latest_known = max([d for d in st["days"]] + list(todo), default="")
        ran = []
        for d in sorted(todo):
            cands_d = sorted(todo[d], key=lambda x: x[0])
            mt, p, header, raw, rows, md5, single = cands_d[-1]
            fu, reach, why = self.pick_followup(st, d, (new_followup,))
            if fu is None:
                self.shout("no follow-up log anywhere -- %s NOT run; export the follow-up log too" % d)
                continue
            cons_in = self.place_input(p, md5) if single else self.write_day_file(p, raw, header, d, rows)
            fmd5 = md5_of(fu)
            fu_in = self.place_input(fu, fmd5)
            self.say("follow-up log for %s: %s -- %s" % (d, os.path.basename(fu), why))
            ok = self.run_tracker(cons_in, fu_in, d, latest=(d >= latest_known))
            if ok:
                st["days"][d] = {"digest": day_digest(rows), "uids": len(uids(rows)),
                                 "input": cons_in, "source_md5": md5, "processed_at": stamp(),
                                 "src_mtime": mt, "how": "auto", "fu_md5": fmd5, "fu_reach": reach}
                ran.append(d)
        # a new follow-up log alone -- or (S540) the latest day's list made with a log that stops short of its call day:
        # re-make the latest day's call list, once, while its call day has not passed (Sunday skipped)
        if not ran and latest_known:
            info = st["days"].get(latest_known, {})
            cons_in = info.get("input")
            want = next_call_day(latest_known)
            in_time = self.today.isoformat() <= want
            fu, reach, why = self.pick_followup(st, latest_known, (new_followup,))
            fmd5 = md5_of(fu) if fu else ""
            used = info.get("fu_reach")
            if used is None:
                used = self.reach_used(st, info)
            short = bool(fu) and (used or "") < want <= (reach or "")
            if not (cons_in and os.path.exists(cons_in)):
                if new_followup:
                    self.say("new follow-up log archived; the latest day (%s) has no input to re-run" % latest_known)
            elif not in_time:
                if new_followup:
                    self.say("new follow-up log archived; the latest day (%s) is not recent, so no re-run"
                             % latest_known)
            elif fu and fmd5 != info.get("fu_md5") and (new_followup or short) and info.get("heal_tried") != fmd5:
                if new_followup and self.already_run_by_hand(fmd5):
                    self.say("the new follow-up log was already processed on the /run page")
                else:
                    if not new_followup:
                        self.say("HEAL: the call list for %s was made with a follow-up log that stops at %s, short of its call "
                                 "day %s -- re-made with %s (%s)" % (latest_known, used or "?", want, os.path.basename(fu), why))
                    info["heal_tried"] = fmd5
                    st["days"][latest_known] = info
                    if self.run_tracker(cons_in, self.place_input(fu, fmd5), latest_known, latest=True):
                        info.update(fu_md5=fmd5, fu_reach=reach)
                        ran.append(latest_known + (" (follow-up refresh)" if new_followup else " (healed: short follow-up log)"))
'''))
E.append(("selftest", '''    print("SELFTEST: %d failure(s)" % len(fails))''', '''    check("S540: call day after Saturday is Monday", next_call_day("2026-10-10") == "2026-10-12")
    check("S540: call day after Monday is Tuesday", next_call_day("2026-10-12") == "2026-10-13")
    print("SELFTEST: %d failure(s)" % len(fails))'''))


def build(b):
    if hashlib.md5(b).hexdigest() != FROM_MD5:
        raise SystemExit("FROM is %s, expected %s -- nothing built" % (hashlib.md5(b).hexdigest(), FROM_MD5))
    t = b.decode("utf-8")
    for name, old, new in E:
        n = t.count(old)
        if n != 1:
            raise SystemExit("anchor '%s' occurs %d times -- nothing built" % (name, n))
        t = t.replace(old, new)
    return t.encode("utf-8")


if __name__ == "__main__":
    out = build(open(sys.argv[1], "rb").read())
    open(sys.argv[2], "wb").write(out)
    print("built %s md5 %s (%d edits)" % (sys.argv[2], hashlib.md5(out).hexdigest(), len(E)))
