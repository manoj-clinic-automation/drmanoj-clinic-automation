#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""walk_s454p4c.py -- kit S454_BILL_REGISTER, part 4C (the brief's section 20.3): the corrected watcher, walked.

It loads a watcher -- P4C's, P4B's, or a MUTANT of P4C's -- in a scratch folder with a MADE-UP marg_push.py beside it and a MADE-UP
sender (urllib's urlopen replaced in this process), Drive's FromMedical stubbed to a scratch folder and the census kept inside the
scratch folder. NOTHING leaves the PC from this walk. Every check runs through watch()'s own start and census (watch() in a thread; a
"restart" is a new process on the same scratch folder), never by calling a new function alone.

  1  a note whose sending fails (a dead line) still waits after the attempt, is sent at the next census, is marked, is not sent again
  2  a note the server answers 400 is marked and not tried again; one answered 401 still waits (and goes when the key is known again)
  3  with the off switch set nothing is sent and nothing is marked; lifted, it goes
  4  the first start: texts already in refused are marked as old and no note leaves; a second start, the sentinel there: a waiting note
     is still waiting and is then sent
  5  a text the reader takes at the start's retry is marked "taken later" and no note leaves
  6  a waiting ORDER note with a later ORDER text taken is marked "overtaken" and no note leaves
  7  a report*.txt with none of the three headings: the note's reason holds nothing of its first line, its .why.txt still does; a sale
     statement the reader refuses at a line: the note says "(line N)" and nothing of that line
  8  share_refused and the listing on Drive still agree with refused, markers present; a marker is never offered to the reader
  9  every check P4B's selftest made still passes
 10  (more than the brief asks) a waiting note older than CENSUS_DAYS is marked "expired", logged, never sent
 11  (more than the brief asks) a note still being tried is not started twice

NEGATIVE CONTROLS, on what the code DOES:
  P4B  (marg_watch.py 20ec1602, as published)  -- checks 1, 4 and 7 go red: a note lost; the note waiting across a restart never sent;
       a line of the file in the reason. Checks 4 (old texts) and 5 are also run on it and what it does is printed as it is.
  MUT  (P4C with section 20's three guards taken out by anchored edits: the first-start marking, "taken later", "overtaken") --
       checks 4, 5 and 6 go red: a note sent for an old text, for a taken text, for an overtaken refusal.

  walk_s454p4c.py --p4c <marg_watch.py> --p4b <marg_watch.py> --reader <marg_txt.py> --work DIR
No phone number and no key in its output: the key is made up, and a long digit run is masked.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

TAG = "W454P4CJSON "
KEY = "walk-made-up-key"
FAKE_PUSH = '''# walk_s454p4c: a MADE-UP marg_push.py -- no address that exists, no key that exists, no sending
import os
HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://walk.invalid/finance/api/marg-file"


def off_marker(offdir=None):
    p = os.path.join(HERE, "_off", "ALL_OFF.txt")
    return p if os.path.isfile(p) else None


def token():
    return "%s"


def _ctx():
    return None


def loop(spool=None, out=None, every=60, stop=None, wake=None):
    return None
''' % KEY

# MUT: P4C with section 20's guards taken out -- each anchor must occur exactly once in P4C's file
MUTATIONS = [
    ('''    notes_first_start(spool, out)       # S454 P4C: before the first sweep -- what is already in refused is never announced
''', '''    pass                                # MUT: the past is not marked
'''),
    ('''        if only is None and NOTE_SINK is None and not os.path.exists(os.path.join(os.path.dirname(ref), NOTE_SENTINEL)):
            return 0                                            # the past is not marked yet: nothing old is announced
''', ''),
    ('''        if got or str(TXT_VERDICT.get(p, (0, ""))[1]).startswith(("TAKEN", "already taken", "HELD")):
''', '''        if False:                                               # MUT: no "taken later"
'''),
    ('''    if kind and _taken_after(spool, kind, kept):
''', '''    if False:                                                   # MUT: no "overtaken"
'''),
]


def mask(s):
    return re.sub(r"\d{9,}", "#", str(s))


# ------------------------------------------------------------------------------------------------------------ one scene, one process
class Stage(object):
    def __init__(self, pc):
        self.pc = pc
        self.spool = os.path.join(pc, "_captured")
        self.keep = os.path.join(pc, "_captured_txt")
        self.ref = os.path.join(self.keep, "refused")
        self.room = os.path.join(pc, "margfolder")
        self.fm = os.path.join(pc, "FromMedical")
        for d in (self.room, self.fm):
            os.makedirs(d, exist_ok=True)
        sys.path.insert(0, pc)
        import urllib.error
        import urllib.request
        import marg_watch as MW                                         # noqa: E402 -- the scratch copy, never the kit's
        import marg_push as MP                                          # noqa: E402 -- the made-up one
        import marg_txt as MT                                           # noqa: E402
        assert os.path.dirname(os.path.abspath(MW.__file__)) == pc and os.path.dirname(os.path.abspath(MP.__file__)) == pc
        assert MP.URL.startswith("http://walk.invalid/") and MP.token() == KEY
        self.MW, self.MT = MW, MT
        self.mode = "ok"
        self.sent, self.msgs, self.census = [], [], [0]
        self.busy, self.maxbusy = {}, {}
        self.lock = threading.Lock()
        st = self

        class Resp(object):
            def read(self):
                return b'{"status": "NOTED"}'

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def urlopen(req, timeout=None, context=None):                   # THE MADE-UP SENDER: nothing leaves this process
            body = json.loads(req.data.decode("utf-8"))
            heads = dict((k.lower(), v) for k, v in req.header_items())
            mode, m = st.mode, body.get("md5")
            with st.lock:
                st.busy[m] = st.busy.get(m, 0) + 1
                st.maxbusy[m] = max(st.maxbusy.get(m, 0), st.busy[m])
                st.sent.append(dict(mode=mode, md5=m, keys=sorted(body), name=body.get("name"), kind=body.get("kind"),
                                    reason=body.get("reason"), url=req.full_url, note_head=heads.get("x-marg-note"),
                                    key_ok=heads.get("x-finance-marg") == KEY, ctype=heads.get("content-type")))
            try:
                if mode == "slow":
                    time.sleep(2.5)
                if mode == "dead":
                    raise urllib.error.URLError("walk: the line is dead")
                if mode in ("400", "401"):
                    raise urllib.error.HTTPError(req.full_url, int(mode), "walk", None, None)
                return Resp()
            finally:
                with st.lock:
                    st.busy[m] -= 1
        urllib.request.urlopen = urlopen
        MW.SETTLE_MS = 5
        MW.NOTE_GAP_S = 0.05
        MW.CENSUS_EVERY_S = 1.0
        MW.TXT_LIVE_FORCE = True                                        # the text route is live, as on the medical PC
        MW._from_medical = lambda: st.fm                                # Drive, stubbed
        MW._census_dirs = lambda roots: [(r, 6, True) for r in roots]   # the census stays inside the scratch folder
        orig = MW.publish_diagnostics

        def counted(*a, **k):
            r = orig(*a, **k)
            st.census[0] += 1
            return r
        MW.publish_diagnostics = counted

    # ---- the watcher's own start and loop
    def start(self):
        t = threading.Thread(target=self.MW.watch, args=([self.room], self.spool, False, False, self.msgs.append, None, 0.2), daemon=True)
        t.start()
        self.wait(lambda: self.census[0] >= 1, 30, "the start's own census")
        self.idle()

    def wait(self, cond, secs, what):
        end = time.time() + secs
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.05)
        self.msgs.append("WALK: timed out waiting for " + what)
        return False

    def idle(self, secs=20):
        return self.wait(lambda: not any(t.name == "refusal_note" and t.is_alive() for t in threading.enumerate()), secs, "the note thread")

    def censuses(self, n):
        want = self.census[0] + n
        self.wait(lambda: self.census[0] >= want, 30, "%d census(es)" % n)
        self.idle()

    def drop(self, name, raw):
        p = os.path.join(self.room, name)
        with open(p, "wb") as fh:
            fh.write(raw)
        m = hashlib.md5(raw).hexdigest()
        return m

    def kept(self, m):
        self.wait(lambda: os.path.isdir(self.ref) and any(m in n and n.endswith(".why.txt") for n in os.listdir(self.ref)), 20, "the text to be kept")
        time.sleep(0.2)
        self.idle()

    def plant(self, slot, raw, why, age_s, src=r"C:\Users\Public\MARG\17476\report.txt"):
        """A text already in refused (kept by an earlier run of the watcher), AGE_S seconds old."""
        os.makedirs(self.ref, exist_ok=True)
        m = hashlib.md5(raw).hexdigest()
        when = time.time() - age_s
        stem = "%s__%s__%s" % (time.strftime("%Y%m%d-%H%M%S", time.localtime(when)), slot, m)
        with open(os.path.join(self.ref, stem + ".txt"), "wb") as fh:
            fh.write(raw)
        with open(os.path.join(self.ref, stem + ".why.txt"), "w", encoding="utf-8") as fh:
            fh.write("%s\nfrom: %s\nwhy:  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(when)), src, why))
        for e in (".txt", ".why.txt"):
            os.utime(os.path.join(self.ref, stem + e), (when, when))
        return m

    def flag(self):
        os.makedirs(self.keep, exist_ok=True)
        with open(os.path.join(self.keep, "S454_NOTES_STARTED.flag"), "w") as fh:
            fh.write("walk: this PC's watcher has started with notes before\n")

    # ---- what is seen
    def marker(self, m):
        if not os.path.isdir(self.ref):
            return None
        for n in os.listdir(self.ref):
            if m in n and n.endswith(".note"):
                with open(os.path.join(self.ref, n), encoding="utf-8") as fh:
                    return fh.read().strip()[21:]
        return None

    def n_sent(self, m, mode=None):
        return len([s for s in self.sent if s["md5"] == m and (mode is None or s["mode"] == mode)])

    def state(self, **more):
        d = dict(sent=self.sent, msgs=[mask(x)[:260] for x in self.msgs if "note" in x or "WALK" in x or "refused" in x.lower()][-40:],
                 flag=os.path.exists(os.path.join(self.keep, "S454_NOTES_STARTED.flag")), maxbusy=self.maxbusy)
        d.update(more)
        return d


def cut_order(MT, tail=b""):
    return MT.ORDER_SAMPLE[:MT.ORDER_SAMPLE.rindex(b"***")] + tail


def scene(name, stage, pc):
    S = Stage(pc)
    MT = S.MT
    out = {}
    if name == "1":                                     # a dead line: waits, goes at the next census, marked, not again
        S.mode = "dead"
        S.start()
        m = S.drop("report.txt", cut_order(MT))
        S.kept(m)
        out["tried_dead"], out["marker_after_dead"] = S.n_sent(m, "dead"), S.marker(m)
        S.mode = "ok"
        S.censuses(2)
        out["ok_after_census"], out["marker_after_census"] = S.n_sent(m, "ok"), S.marker(m)
        S.censuses(3)
        out["ok_later"] = S.n_sent(m, "ok")
    elif name == "2":                                   # 400 ends it; 401 waits; then section 8 on the same folder
        S.mode = "400"
        S.start()
        a = S.drop("report.txt", cut_order(MT))
        S.kept(a)
        S.censuses(3)
        out["a_tries"], out["a_marker"] = S.n_sent(a), S.marker(a)
        S.mode = "401"
        b = S.drop("report.txt", cut_order(MT, b"\r\n"))
        S.kept(b)
        n1 = S.n_sent(b, "401")
        S.censuses(3)
        out["b_tries_first"], out["b_tries_after_censuses"], out["b_marker_401"] = n1, S.n_sent(b, "401"), S.marker(b)
        S.mode = "ok"
        S.censuses(2)
        out["b_ok"], out["b_marker_ok"] = S.n_sent(b, "ok"), S.marker(b)
        S.wait(lambda: os.path.isdir(os.path.join(S.fm, "refused_text"))
               and sorted(os.listdir(os.path.join(S.fm, "refused_text"))) == sorted(os.listdir(S.ref)), 15, "Drive's list to agree")
        here, there = sorted(os.listdir(S.ref)), sorted(os.listdir(os.path.join(S.fm, "refused_text"))) if os.path.isdir(os.path.join(S.fm, "refused_text")) else []
        out["s8"] = dict(agree=here == there, n=len(here), notes=len([n for n in there if n.endswith(".note")]))
    elif name == "3":                                   # the off switch
        os.makedirs(os.path.join(pc, "_off"))
        open(os.path.join(pc, "_off", "ALL_OFF.txt"), "w").close()
        S.start()
        m = S.drop("report.txt", cut_order(MT))
        S.kept(m)
        S.censuses(3)
        out["sent_while_off"], out["marker_while_off"] = S.n_sent(m), S.marker(m)
        out["off_lines"] = len([x for x in S.msgs if "sending is OFF" in x and "wait" in x])
        os.remove(os.path.join(pc, "_off", "ALL_OFF.txt"))
        S.censuses(2)
        out["ok_after_lift"], out["marker_after_lift"] = S.n_sent(m, "ok"), S.marker(m)
    elif name == "4" and stage == "a":                  # the first start: the past is marked, not announced; then a note is left waiting
        o1 = S.plant("report", MT.SELFTEST_SAMPLE.replace(b"End of Report", b"End of Page"),
                     "a bill-wise report, but without the '*** End of Report ***' line at the end (cut short?)", 26 * 3600)
        o2 = S.plant("user_ab1", cut_order(MT, b"\r\n\r\n\r\n"),
                     "an order sheet without the '*** End of Report ***' line at the end (cut short?)", 20 * 3600)
        S.start()
        S.censuses(2)
        out["old_sent"], out["old_markers"] = [S.n_sent(o1), S.n_sent(o2)], [S.marker(o1), S.marker(o2)]
        out["flag_after_first_start"] = os.path.exists(os.path.join(S.keep, "S454_NOTES_STARTED.flag"))
        S.mode = "dead"
        m = S.drop("report.txt", cut_order(MT))
        S.kept(m)
        out["new_tried_dead"], out["new_marker"] = S.n_sent(m, "dead"), S.marker(m)
        with open(os.path.join(pc, "walk_scene4.json"), "w") as fh:
            json.dump(dict(new=m, old=[o1, o2]), fh)
    elif name == "4" and stage == "b":                  # a second start: the waiting note is still waiting, and is then sent
        ids = json.load(open(os.path.join(pc, "walk_scene4.json")))
        m = ids["new"]
        out["waiting_before_start"] = S.marker(m) is None and any(m in n and n.endswith(".txt") for n in os.listdir(S.ref))
        out["flag_before_start"] = os.path.exists(os.path.join(S.keep, "S454_NOTES_STARTED.flag"))
        S.start()
        S.censuses(2)
        out["new_ok"], out["new_marker"] = S.n_sent(m, "ok"), S.marker(m)
        out["old_sent"] = [S.n_sent(x) for x in ids["old"]]
        drv = os.path.join(S.fm, "refused_text")
        S.wait(lambda: os.path.isdir(drv) and sorted(os.listdir(drv)) == sorted(os.listdir(S.ref)), 15, "Drive's list to agree")
        here, there = sorted(os.listdir(S.ref)), sorted(os.listdir(drv)) if os.path.isdir(drv) else []
        out["s8"] = dict(agree=here == there, n=len(here), notes=len([n for n in there if n.endswith(".note")]),
                         note_offered=[p for p in list(S.MW.TXT_VERDICT) + list(S.MW.TXT_STAT) if p.endswith(".note")],
                         texts_offered=len([p for p in set(S.MW.TXT_VERDICT) | set(S.MW.TXT_STAT) if os.path.dirname(p) == S.ref]))
    elif name == "5":                                   # a refused text the reader takes at the start's retry
        S.flag()
        m = S.plant("report", MT.SELFTEST_SAMPLE, "the reader refused it: line 7: a line of a kind this reader does not know: 'X'", 2 * 3600)
        S.start()
        S.censuses(3)
        out["taken"] = len([n for n in (os.listdir(S.spool) if os.path.isdir(S.spool) else []) if n.endswith(".XLS")])
        out["sent"], out["marker"] = S.n_sent(m), S.marker(m)
    elif name == "6":                                   # a waiting ORDER note, then a good ORDER text taken: overtaken
        S.mode = "dead"
        S.start()
        m = S.drop("report.txt", cut_order(MT))
        S.kept(m)
        out["waiting_first"] = S.marker(m) is None
        time.sleep(0.4)
        S.drop("report.txt", MT.ORDER_SAMPLE)
        S.wait(lambda: os.path.isdir(S.spool) and any(n.endswith(".XLS") for n in os.listdir(S.spool)), 20, "the good order sheet to be taken")
        out["good_taken"] = os.path.isdir(S.spool) and len([n for n in os.listdir(S.spool) if n.endswith(".XLS")])
        S.idle()
        S.mode = "ok"
        S.censuses(3)
        out["ok_sent"], out["marker"] = S.n_sent(m, "ok"), S.marker(m)
    elif name == "7":                                   # the note never carries a line of the file
        S.start()
        first = "WALK454 LETTERHEAD OF A SHOP, 12 SOME STREET"
        raw_a = (first + "\r\nREGISTER OF SOMETHING ELSE FROM 01-10-2026\r\n" + "-" * 60 + "\r\nROW ONE OF IT     12.00\r\n").encode()
        a = S.drop("report_x.txt", raw_a)
        S.kept(a)
        bad = "   ZZ WALK454 A LINE OF NO KIND THE READER KNOWS"
        T = MT.SELFTEST_SAMPLE.decode()
        k = T.index("A000002")
        raw_b = (T[:k] + bad + "\r\n" + T[k:]).encode()
        b = S.drop("report.txt", raw_b)
        S.kept(b)
        S.censuses(1)

        def why_of(m):
            for n in os.listdir(S.ref):
                if m in n and n.endswith(".why.txt"):
                    return open(os.path.join(S.ref, n), encoding="utf-8").read()
            return ""

        def leaks(m, raw):
            lines = [l.strip() for l in raw.decode("latin-1").splitlines() if len(l.strip()) >= 8 and set(l.strip()) - set("-= *")]
            vals = " | ".join(str(v) for s in S.sent if s["md5"] == m for v in (s["name"], s["kind"], s["reason"]))
            return [l[:40] for l in lines if l in vals or l[:20] in vals]
        ra = [s for s in S.sent if s["md5"] == a]
        rb = [s for s in S.sent if s["md5"] == b]
        out["a"] = dict(n=len(ra), reason=ra[0]["reason"] if ra else None, leaks=leaks(a, raw_a), why_has_first=first in why_of(a),
                        first_in_reason=bool(ra) and "WALK454" in ra[0]["reason"])
        out["b"] = dict(n=len(rb), reason=rb[0]["reason"] if rb else None, leaks=leaks(b, raw_b), why_has_line="WALK454" in why_of(b),
                        line_in_reason=bool(rb) and "WALK454" in rb[0]["reason"], kind=rb[0]["kind"] if rb else None)
        out["shape"] = [dict(keys=s["keys"], url=s["url"], note_head=s["note_head"], key_ok=s["key_ok"], ctype=s["ctype"]) for s in S.sent]
    elif name == "10":                                  # expired
        S.flag()
        m = S.plant("report", cut_order(MT), "an order sheet without the '*** End of Report ***' line at the end (cut short?)", 4 * 86400)
        S.start()
        S.censuses(2)
        out["sent"], out["marker"] = S.n_sent(m), S.marker(m)
        out["logged"] = any("EXPIRED" in x for x in S.msgs)
    elif name == "11":                                  # one attempt at a time
        S.MW.CENSUS_EVERY_S = 0.4
        S.mode = "slow"
        S.start()
        m = S.drop("report.txt", cut_order(MT))
        S.kept(m)
        S.censuses(4)
        S.idle(30)
        out["sends"], out["maxbusy"], out["marker"] = S.n_sent(m), S.maxbusy.get(m), S.marker(m)
    print(TAG + json.dumps(S.state(**out), default=str))


# --------------------------------------------------------------------------------------------------------------------------- the walk
def main():
    ap = argparse.ArgumentParser()
    for k in ("--p4c", "--p4b", "--reader", "--work"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    work = os.path.abspath(a.work)
    assert "_scratch" in work.replace("\\", "/").split("/") or work.startswith("/tmp/"), "refusing a non-scratch folder: " + work
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    c_txt = open(a.p4c, "rb").read().decode("utf-8")
    mut = c_txt
    for old, new in MUTATIONS:
        assert mut.count(old) == 1, "a mutation's anchor occurs %d times: %r" % (mut.count(old), old[:70])
        mut = mut.replace(old, new, 1)
    with open(os.path.join(work, "marg_watch_MUT.py"), "wb") as fh:
        fh.write(mut.encode("utf-8"))
    SIDES = {"P4C": a.p4c, "P4B": a.p4b, "MUT": os.path.join(work, "marg_watch_MUT.py")}
    md5 = dict((k, hashlib.md5(open(v, "rb").read()).hexdigest()) for k, v in SIDES.items())
    print("walk_s454p4c: P4C %s . P4B %s . MUT %s (P4C less section 20's three guards) . reader %s . python %s"
          % (md5["P4C"], md5["P4B"], md5["MUT"][:8], hashlib.md5(open(a.reader, "rb").read()).hexdigest()[:8], sys.version.split()[0]))
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(json.dumps(got, default=str))[:600] + "]") if got is not None else ""))
        if not cond:
            fails.append(label)

    def pc_of(side, sc):
        pc = os.path.join(work, "%s_scene%s" % (side, sc), "SendToClinic")
        if not os.path.isdir(pc):
            os.makedirs(pc)
            shutil.copyfile(SIDES[side], os.path.join(pc, "marg_watch.py"))
            shutil.copyfile(a.reader, os.path.join(pc, "marg_txt.py"))
            with open(os.path.join(pc, "marg_push.py"), "w") as fh:
                fh.write(FAKE_PUSH)
        return pc

    def run(side, sc, stage=""):
        pc = pc_of(side, sc)
        env = dict(os.environ)
        for k in ("MARG_PUSH_URL", "HTTP_PROXY", "HTTPS_PROXY"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.abspath(__file__), "--scene", sc, stage, pc], env=env, cwd=pc,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- %s scene %s%s did not finish (exit %s); its last lines:" % (side, sc, stage, p.returncode))
            for l in p.stdout.splitlines()[-25:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])

    jobs = [("P4C", s, st) for s, st in (("1", ""), ("2", ""), ("3", ""), ("4", "a"), ("4", "b"), ("5", ""), ("6", ""), ("7", ""), ("10", ""), ("11", ""))]
    jobs += [("P4B", s, st) for s, st in (("1", ""), ("4", "a"), ("4", "b"), ("5", ""), ("7", ""))]
    jobs += [("MUT", s, st) for s, st in (("4", "a"), ("5", ""), ("6", ""))]
    R = {}
    for side, sc, st in jobs:
        R[(side, sc + st)] = run(side, sc, st)
    check("every scene ran to its end (%d scenes: P4C 10, P4B 5, MUT 3)" % len(jobs), all(v is not None for v in R.values()),
          [k for k, v in R.items() if v is None] or None)
    if any(v is None for v in R.values()):
        print("WALK_S454P4C RED -- a scene did not finish")
        return 1
    C = lambda s: R[("P4C", s)]
    B = lambda s: R[("P4B", s)]
    M = lambda s: R[("MUT", s)]

    print("-- 1  a dead line")
    r = C("1")
    check("the attempt on a dead line is made (%d tries, three to an attempt) and the note still WAITS: no marker" % r["tried_dead"],
          r["tried_dead"] >= 3 and r["tried_dead"] % 3 == 0 and r["marker_after_dead"] is None, [r["tried_dead"], r["marker_after_dead"]])
    check("at the next census it is sent, once, and marked ('%s')" % r["marker_after_census"],
          r["ok_after_census"] == 1 and str(r["marker_after_census"]).startswith("sent"), [r["ok_after_census"], r["marker_after_census"]])
    check("three censuses later it has not been sent again", r["ok_later"] == 1, r["ok_later"])
    b = B("1")
    check("NEGATIVE (P4B): the same note is LOST -- tried %d times on the dead line, never sent once the line is back (sent %d)"
          % (b["tried_dead"], b["ok_later"]), b["tried_dead"] >= 1 and b["ok_later"] == 0, [b["tried_dead"], b["ok_after_census"], b["ok_later"]])

    print("-- 2  what the server answers")
    r = C("2")
    check("answered 400: tried once, marked ('%s'), not tried again over three censuses" % r["a_marker"],
          r["a_tries"] == 1 and str(r["a_marker"]).startswith("refused by the server (HTTP 400)"), [r["a_tries"], r["a_marker"]])
    check("answered 401: no marker, still waiting, tried again at each census (%d -> %d tries)" % (r["b_tries_first"], r["b_tries_after_censuses"]),
          r["b_marker_401"] is None and r["b_tries_first"] >= 1 and r["b_tries_after_censuses"] > r["b_tries_first"],
          [r["b_tries_first"], r["b_tries_after_censuses"], r["b_marker_401"]])
    check("...and once the server knows the key again it goes, once, and is marked", r["b_ok"] == 1 and str(r["b_marker_ok"]).startswith("sent"),
          [r["b_ok"], r["b_marker_ok"]])

    print("-- 3  the off switch")
    r = C("3")
    check("with the off switch set nothing is sent and nothing is marked", r["sent_while_off"] == 0 and r["marker_while_off"] is None,
          [r["sent_while_off"], r["marker_while_off"]])
    check("...and the log says so once, not at every census (%d line over three censuses)" % r["off_lines"], r["off_lines"] == 1, r["off_lines"])
    check("lifted, the note goes at the next census, once, and is marked", r["ok_after_lift"] == 1 and str(r["marker_after_lift"]).startswith("sent"),
          [r["ok_after_lift"], r["marker_after_lift"]])

    print("-- 4  the first start and the second")
    ra, rb = C("4a"), C("4b")
    check("the first start: both texts already in refused are marked 'kept before S454', no note leaves for them, the sentinel is written",
          ra["old_sent"] == [0, 0] and all(str(x).startswith("kept before S454") for x in ra["old_markers"]) and ra["flag_after_first_start"],
          [ra["old_sent"], ra["old_markers"], ra["flag_after_first_start"]])
    check("a note kept on a dead line is left waiting across the restart (tried %d times, no marker; the sentinel is there)" % ra["new_tried_dead"],
          ra["new_tried_dead"] >= 3 and ra["new_marker"] is None and rb["waiting_before_start"] and rb["flag_before_start"],
          [ra["new_tried_dead"], ra["new_marker"], rb["waiting_before_start"], rb["flag_before_start"]])
    check("the second start sends it, once, and marks it; the old texts stay silent",
          rb["new_ok"] == 1 and str(rb["new_marker"]).startswith("sent") and rb["old_sent"] == [0, 0], [rb["new_ok"], rb["new_marker"], rb["old_sent"]])
    ba, bb = B("4a"), B("4b")
    check("NEGATIVE (P4B): the note waiting across the restart is never sent -- LOST (sent %d at the second start)" % bb["new_ok"],
          ba["new_tried_dead"] >= 1 and bb["new_ok"] == 0, [ba["new_tried_dead"], bb["new_ok"]])
    check("AS IT IS (P4B): it sends no note for a text already in refused either -- it has no retry of notes at all (the brief expected one sent)",
          ba["old_sent"] == [0, 0] and bb["old_sent"] == [0, 0] and ba["old_markers"] == [None, None], [ba["old_sent"], bb["old_sent"], ba["old_markers"]])
    m = M("4a")
    check("NEGATIVE (MUT, the retry without the first-start rule): a note IS sent for each old text (%s)" % m["old_sent"],
          all(x >= 1 for x in m["old_sent"]), [m["old_sent"], m["old_markers"]])

    print("-- 5  a text the reader takes at the start's retry")
    r = C("5")
    check("it is taken (1 .XLS in the spool), marked 'taken later', and no note leaves -- at the start or at three censuses",
          r["taken"] == 1 and r["sent"] == 0 and str(r["marker"]).startswith("taken later"), [r["taken"], r["sent"], r["marker"]])
    b = B("5")
    check("AS IT IS (P4B): it takes the text and sends no note for it either (no retry of notes); it has no marker (the brief expected a note)",
          b["taken"] == 1 and b["sent"] == 0 and b["marker"] is None, [b["taken"], b["sent"], b["marker"]])
    m = M("5")
    check("NEGATIVE (MUT, the retry without 'taken later' and 'overtaken'): a note IS sent for the text the server already holds (%d)" % m["sent"],
          m["taken"] == 1 and m["sent"] >= 1, [m["taken"], m["sent"], m["marker"]])

    print("-- 6  overtaken")
    r = C("6")
    check("a waiting ORDER note, then a good order sheet taken: marked 'overtaken', no note leaves once the line is back",
          r["waiting_first"] and r["good_taken"] == 1 and r["ok_sent"] == 0 and str(r["marker"]).startswith("overtaken -- a ORDER text"),
          [r["waiting_first"], r["good_taken"], r["ok_sent"], r["marker"]])
    m = M("6")
    check("NEGATIVE (MUT): the late note IS sent after the good sheet (%d) -- Darpan's card would say 'adhoori' wrongly" % m["ok_sent"],
          m["good_taken"] == 1 and m["ok_sent"] >= 1, [m["good_taken"], m["ok_sent"], m["marker"]])

    print("-- 7  no line of the file")
    r = C("7")
    check("a report*.txt with none of the three headings: reason '%s' -- nothing of its first line; its .why.txt still has it" % r["a"]["reason"],
          r["a"]["n"] == 1 and r["a"]["reason"] == "not a bill-wise sales statement" and not r["a"]["leaks"] and r["a"]["why_has_first"], r["a"])
    check("a sale statement refused at a line: reason '%s' -- nothing of that line; its .why.txt still has it" % r["b"]["reason"],
          r["b"]["n"] == 1 and re.match(r"^the reader refused it \(line \d+\)$", r["b"]["reason"] or "") is not None and not r["b"]["leaks"]
          and r["b"]["why_has_line"] and r["b"]["kind"] == "SALE", r["b"])
    check("the note is what the door takes: keys {kind, md5, name, reason}, X-Marg-Note: refused, the key in X-Finance-Marg, JSON, marg_push's address",
          len(r["shape"]) == 2 and all(s["keys"] == ["kind", "md5", "name", "reason"] and s["note_head"] == "refused" and s["key_ok"]
                                       and s["ctype"] == "application/json" and s["url"] == "http://walk.invalid/finance/api/marg-file" for s in r["shape"]),
          [dict(s, key_ok=bool(s["key_ok"])) for s in r["shape"]][:1])
    b = B("7")
    check("NEGATIVE (P4B): the first line of the file is in the reason", b["a"]["first_in_reason"] and bool(b["a"]["leaks"]), [b["a"]["reason"], b["a"]["leaks"]])
    check("NEGATIVE (P4B): the refused line of the sale statement is in the reason", b["b"]["line_in_reason"] and bool(b["b"]["leaks"]),
          [b["b"]["reason"], b["b"]["leaks"]])
    check("...and P4B's note has the same shape (the door is not asked anything new)", [dict(s) for s in b["shape"]] == [dict(s) for s in r["shape"]],
          None if b["shape"] == r["shape"] else [b["shape"], r["shape"]])

    print("-- 8  Drive's copy of refused")
    s8 = C("2")["s8"]
    check("with markers present, the listing on Drive (through the census's own share_refused) agrees with refused: %d files, %d of them markers"
          % (s8["n"], s8["notes"]), s8["agree"] and s8["n"] == 6 and s8["notes"] == 2, s8)
    s8 = C("4b")["s8"]
    check("...and after a restart with markers there: %d files, %d markers, Drive agrees" % (s8["n"], s8["notes"]),
          s8["agree"] and s8["n"] == 9 and s8["notes"] == 3, s8)
    check("at that start the retry offered the reader the %d kept texts and never a marker" % s8["texts_offered"],
          s8["note_offered"] == [] and s8["texts_offered"] == 3, s8)

    print("-- 9  the selftests")
    st = {}
    for side in ("P4B", "P4C"):
        pc = pc_of(side, "selftest")
        p = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.join(pc, "marg_watch.py"), "--selftest"], cwd=pc, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, timeout=600)
        st[side] = dict(rc=p.returncode, ok=[l.strip()[2:].strip() for l in p.stdout.splitlines() if l.strip().startswith("OK ")],
                        bad=[l.strip() for l in p.stdout.splitlines() if l.strip().startswith("FAIL")], last=p.stdout.strip().splitlines()[-1:])
    missing = [l for l in st["P4B"]["ok"] if l not in st["P4C"]["ok"]]
    check("P4B's selftest passes with %d checks; every one of them passes in P4C's, which has %d (%d new)"
          % (len(st["P4B"]["ok"]), len(st["P4C"]["ok"]), len(st["P4C"]["ok"]) - len(st["P4B"]["ok"])),
          st["P4B"]["rc"] == 0 and st["P4C"]["rc"] == 0 and len(st["P4B"]["ok"]) == 37 and not missing and not st["P4C"]["bad"]
          and len(st["P4C"]["ok"]) == 40, [st["P4B"]["last"], st["P4C"]["last"], missing, st["P4C"]["bad"]])
    pc = pc_of("P4C", "selftest")
    p = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.join(pc, "marg_txt.py"), "--selftest"], cwd=pc, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, timeout=600)
    check("the reader's own selftest passes beside it (%s)" % (p.stdout.strip().splitlines()[-1:] or [""])[0][:60], p.returncode == 0)

    print("-- 10, 11  more than the brief asks")
    r = C("10")
    check("a waiting note four days old is marked 'expired', logged, and never sent", r["sent"] == 0 and str(r["marker"]).startswith("expired") and r["logged"],
          [r["sent"], r["marker"], r["logged"]])
    r = C("11")
    check("a note still being tried (a slow line, a census every 0.4 s) is not started twice: sent %s time, never two at once" % r["sends"],
          r["sends"] == 1 and r["maxbusy"] == 1 and str(r["marker"]).startswith("sent"), [r["sends"], r["maxbusy"], r["marker"]])
    leak = [k for k, v in R.items() if KEY in json.dumps(v)]
    check("no key in any scene's output (the made-up one included)", not leak, leak or None)
    print("WALK_S454P4C %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--scene" in sys.argv:
        i = sys.argv.index("--scene")
        scene(sys.argv[i + 1], sys.argv[i + 2], os.path.abspath(sys.argv[i + 3]))
    else:
        sys.exit(main())
