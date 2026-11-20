#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s892.py -- kit S892 (the parent, S489, 19-Nov-2026). His word 09:53: "Even if I'm not sitting, the daily follow-up logs
should be refreshed ... not tied to the consultation reports." The PC's docterz_pickup.py (FROM cd829f5f, S540) made a call list
only after a consultation day, so after his away days (16-18 Nov) the 19-Nov log was filed and the 18 due today never reached the
Call Console. This adds ONE method and ONE call; nothing else changes:
  Pass.followup_alone(st, latest_known) -- when a pass ran nothing, the NEWEST follow-up log makes the list for its first call day
  (the earliest due date from today on, Sunday skipped) unless a consultation day already owns that call day. The tracker's own
  run_daily is given a header-only consultation file named for the day before the call day (processor.parse_consultation_report
  reads an empty report's day from its name), so no visit is invented. Once per (call day, log): a newer log for the same day
  re-makes it; a failure is shouted once, never retried every five minutes.
    python3 make_s892.py <FROM docterz_pickup.py> <TO docterz_pickup.py>
"""
import hashlib
import sys

src, out = sys.argv[1:3]
t = open(src, encoding="utf-8").read()
assert hashlib.md5(t.encode("utf-8")).hexdigest() == "cd829f5fd074e8451f027e08da2ef68d", "FROM is not cd829f5f"


def once(old, new):
    global t
    n = t.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:80])
    t = t.replace(old, new)


once('VERSION = "S540 (S239 rev 3)"', 'VERSION = "S892 (S239 rev 4)"')

REFRESH_OLD = """        if not cons or not os.path.exists(cons) or not fu:
            self.shout("refresh impossible: latest day %r input %r follow-up log %r" % (latest, cons, fu))
            self.finish(st, "refresh FAILED")
            return 1
        self.say("REFRESH: latest business day %s -- re-running with %s + %s"
                 % (latest, os.path.basename(cons), os.path.basename(fu)))
        self.last_staff = None
        ok = self.run_tracker(cons, self.place_input(fu, md5_of(fu)), latest, latest=True)
        if not ok or not self.last_staff:
            self.finish(st, "refresh FAILED")
            return 1
"""
REFRESH_NEW = """        alone = sorted(d for d in st.get("fu_alone", {}) if d >= self.today.isoformat())
        if latest and alone and alone[-1] > next_call_day(latest) and next_call_day(latest) < self.today.isoformat():
            # S892: the newest call list was made from the follow-up log alone -- re-make THAT one, never an older day's
            st["fu_alone"].pop(alone[-1], None)
            self.last_staff = None
            made = self.followup_alone(st, latest)
            if not made or not self.last_staff:
                self.shout("refresh impossible: the call list for %s could not be re-made from the follow-up log" % alone[-1])
                self.finish(st, "refresh FAILED")
                return 1
            self.say("REFRESH: the newest call list re-made from the follow-up log alone: %s" % made)
        else:
            if not cons or not os.path.exists(cons) or not fu:
                self.shout("refresh impossible: latest day %r input %r follow-up log %r" % (latest, cons, fu))
                self.finish(st, "refresh FAILED")
                return 1
            self.say("REFRESH: latest business day %s -- re-running with %s + %s"
                     % (latest, os.path.basename(cons), os.path.basename(fu)))
            self.last_staff = None
            ok = self.run_tracker(cons, self.place_input(fu, md5_of(fu)), latest, latest=True)
            if not ok or not self.last_staff:
                self.finish(st, "refresh FAILED")
                return 1
"""
once(REFRESH_OLD, REFRESH_NEW)

once('''        # the split-payment legs, every pass that saw something new
''', '''        # S892 (the owner, 19-Nov-2026): the newest follow-up log makes the next call list on its own -- sitting or not
        if not ran:
            alone = self.followup_alone(st, latest_known)
            if alone:
                ran.append(alone)
        # the split-payment legs, every pass that saw something new
''')

once('''    def finish(self, st, summary):
''', '''    def followup_alone(self, st, latest_known):
        """S892: when no consultation report made the coming call list (he was away, or reception exported only the follow-up
        log), the NEWEST follow-up log makes it alone. Its call day = the earliest due date from today on (Sunday skipped), at
        most 7 days ahead. Not run when a consultation day already owns that call day (S540's heal keeps that one's log current).
        The tracker is given a header-only consultation file named for the day before the call day: processor reads an empty
        report's day from its name, so no visit is invented. Once per (call day, log md5) -- success or failure. Stands aside while a
        consultation day's list is still today's or a later one (cold review: a later list never replaces a proper one early)."""
        logs = [(float(v.get("mtime") or 0), v.get("archived")) for v in st["seen"].values()
                if v.get("type") == "FOLLOWUP_LOG" and v.get("archived") and os.path.exists(v["archived"])]
        if not logs:
            return None
        fu = max(logs)[1]
        try:
            _h, body, _r = read_rows(fu)
        except (OSError, UnicodeDecodeError, csv.Error):
            return None
        today = self.today.isoformat()
        dues = sorted({iso_of(r.get("Followup Date")) for r in body if (r.get("Appointment ID") or "").strip()} - {""})
        dues = [d for d in dues if d >= today and _dt.date.fromisoformat(d).weekday() != 6]
        if not dues:
            return None
        target = dues[0]
        if (_dt.date.fromisoformat(target) - self.today).days > 7:
            return None
        if latest_known and next_call_day(latest_known) >= min(target, today):
            return None
        fmd5 = md5_of(fu)
        done = st.setdefault("fu_alone", {})
        if done.get(target) == fmd5:
            return None
        done[target] = fmd5
        a = _dt.date.fromisoformat(target) - _dt.timedelta(days=1)
        if a.weekday() == 6:                     # a Monday call day reads from Saturday, so Sunday's dues are not lost
            a -= _dt.timedelta(days=1)
        anchor = a.isoformat()
        cons = os.path.join(self.uploads, "consultation_report_%s__fu_alone_%s.csv"
                            % (anchor, now_ist().strftime("%Y%m%d-%H%M%S")))
        if not self.dry:
            with open(cons, "w", encoding="utf-8-sig", newline="") as fh:
                fh.write("Sr No,Consultation Date,Patient UID,Patient Name,Mobile\\n")
        self.say("S892: no consultation report made the call list for %s (the last consultation day is %s) -- "
                 "the follow-up log %s makes it alone" % (target, latest_known or "none", os.path.basename(fu)))
        if self.run_tracker(cons, self.place_input(fu, fmd5), anchor, latest=True):
            return "%s (follow-up log alone)" % target
        return None

    def finish(self, st, summary):
''')
open(out, "w", encoding="utf-8", newline="").write(t)
print("make_s892: TO written", hashlib.md5(t.encode("utf-8")).hexdigest())
