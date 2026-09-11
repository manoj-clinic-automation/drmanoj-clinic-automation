#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docterz_pickup.py -- S239: the Docterz exports, picked up from Downloads and processed by themselves.

THE OWNER (11-Sep-2026): "automatic pickup of the reports -- consultation report and follow-up
logs -- from my Downloads folder, and process them; then the manual system either retires or
becomes a fallback. The tracker continues at my PC only."

WHAT ONE PASS DOES (Task Scheduler runs it every 5 minutes, hidden):
  1. Looks in D:\\Downloads for Docterz CSVs. Each is identified by its CONTENT (its header),
     never by its name: consultation report, follow-up log, clinical data report.
  2. Waits until the newest of them is at least 3 minutes old, so a consultation report and its
     follow-up log exported one after the other are taken together.
  3. COPIES every new one into D:\\Downloads\\DocterzArchive\\<TYPE>\\<YYYY-MM>\\, named by the
     BUSINESS date read from inside the file (Docterz names a file by the day it was downloaded).
     Nothing in Downloads is moved, renamed or deleted.
  4. Decides, for each business day in a new consultation report, whether the tracker needs it:
       * a day the tracker has never seen, or one with a patient the tracker lacks -> RUN
       * the same patients, the same money as already processed              -> skip (duplicate)
       * the same patients, different money, a recent day                    -> RUN (newest wins)
       * FEWER patients than the tracker already holds for that day          -> QUARANTINE, shout
     A report covering several days is cut into one file per day first, because the tracker's
     day-revenue reader stamps every row with the report's latest date.
  5. RUNS the tracker's own daily job -- processor.run_daily(), exactly what the browser /run page
     calls -- with that day's report and the newest follow-up log. Then, as /run does, it sends the
     staff workbook to the VPS, and runs push_patient_join.py --push (the second half of
     PUSH_TODAY.bat). The VPS send and the patient push happen only for the latest business day,
     so re-processing an old day never replaces today's call list.
  6. Rebuilds outputs\\Day_Tenders.csv (the split-payment legs the VPS day page reads), ONE row per
     leg: when two exports carry the same bill, the newer export wins, so no leg is ever doubled.

NEVER: deletes a file; overwrites a tracker output without first keeping a copy; prints a name or
a mobile number (counts, dates and file names only); runs while another pass is running.

The browser /run page is untouched and stays the fallback. If both run on the same export, the
second finds the day already processed and does nothing (the tracker de-duplicates by patient and
date, and this pass recognises a file the /run page already saved).

    python docterz_pickup.py              one pass (what the scheduled task runs)
    python docterz_pickup.py --dry-run    report what it would do; write nothing, run nothing
    python docterz_pickup.py --selftest   offline checks on built-in samples; touches nothing
"""
import argparse
import csv
import datetime as _dt
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

VERSION = "S239 rev 2"

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOWNLOADS = r"D:\Downloads"
DEFAULT_ARCHIVE = r"D:\Downloads\DocterzArchive"

QUIET_SECONDS = 180          # the newest Docterz file must be this old before a pass acts
RECENT_DAYS = 3              # a same-patients re-export is re-run only for a day this recent
STALE_LOCK_SECONDS = 1800
NAME_PREFIXES = ("consultation_report", "followup_logs", "clinical_data_report")

UID_RE = re.compile(r"[A-Z0-9]{8,14}")
DMY_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})")

CONSULT_NEED = {"Consultation Date", "Patient UID", "Amount collected", "Bill Amount"}
FOLLOW_NEED = {"Appointment ID", "Followup Date", "Mobile No"}
CLINICAL_NEED = {"Consultation Date", "Patient UID", "Drugs Prescribed", "Diagnosis"}

# the columns whose values make a day's money: the digest of a day is taken over these only
DIGEST_COLS = ["Patient UID", "Consultation Date", "Bill Amount", "Amount collected",
               "Bill Amount Pending", "Consultation Amount", "Consultation Discount",
               "Procedure Amount", "Procedure Discount", "Laboratory Amount",
               "Laboratory Discount", "Radiology Amount", "Radiology Discount",
               "Mode Of Payment", "Invoice No."]


# ───────────────────────────────────────────────────────────────────────────── small helpers
def now_ist():
    return _dt.datetime.now()          # the clinic PC's clock is IST


def stamp(t=None):
    return (t or now_ist()).strftime("%Y-%m-%d %H:%M:%S")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def iso_of(dmy):
    m = DMY_RE.match(str(dmy or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def read_rows(path):
    """(header, body_rows_as_dicts, raw_rows). Every non-blank row; callers keep only rows whose
    Patient UID is UID-shaped, so the banner and Docterz's payment footer (F-93) never count."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        raw = list(csv.reader(fh))
    if not raw:
        return [], [], raw
    header = [h.strip() for h in raw[0]]
    body = []
    for r in raw[1:]:
        if not any(x.strip() for x in r):
            continue
        body.append(dict(zip(header, r)))
    return header, body, raw


def classify(header):
    hs = set(header)
    if CLINICAL_NEED <= hs:
        return "CLINICAL"
    if CONSULT_NEED <= hs:
        return "CONSULTATION"
    if FOLLOW_NEED <= hs:
        return "FOLLOWUP_LOG"
    return None


def day_groups(body):
    """{iso_date: [row, ...]} over UID-shaped patient rows only."""
    out = {}
    for r in body:
        uid = (r.get("Patient UID") or "").strip()
        d = iso_of(r.get("Consultation Date"))
        if d and UID_RE.fullmatch(uid):
            out.setdefault(d, []).append(r)
    return out


def day_digest(rows):
    keyed = sorted("\x1f".join((r.get(c) or "").strip() for c in DIGEST_COLS) for r in rows)
    return hashlib.md5("\x1e".join(keyed).encode("utf-8")).hexdigest()


def uids(rows):
    return {(r.get("Patient UID") or "").strip() for r in rows}


# ───────────────────────────────────────────────────────────────────────────── the pass
class Pass:
    def __init__(self, tracker, downloads, archive, dry_run=False, today=None, runner=None,
                 vps_upload=None, patient_push=None):
        self.tracker = tracker
        self.downloads = downloads
        self.archive = archive
        self.dry = dry_run
        self.today = today or now_ist().date()
        self.uploads = os.path.join(tracker, "uploads")
        self.outputs = os.path.join(tracker, "outputs")
        self.state_path = os.path.join(archive, "_pickup_state.json")
        self.log_path = os.path.join(archive, "_pickup_log.txt")
        self.index_path = os.path.join(archive, "index.csv")
        self.lines = []
        self.shouts = []
        self.runner = runner              # injectable for tests; default = processor.run_daily
        self.vps_upload = vps_upload      # default = push_to_vps.upload_workbook
        self.patient_push = patient_push  # default = push_patient_join.py --push

    # ── logging ────────────────────────────────────────────────────────────
    def say(self, msg):
        line = "[%s] %s" % (stamp(), msg)
        self.lines.append(line)
        print(line, flush=True)

    def shout(self, msg):
        self.shouts.append(msg)
        self.say("SHOUT: " + msg)

    def flush_log(self):
        if self.dry or not self.lines:
            return
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines) + "\n")

    # ── state ──────────────────────────────────────────────────────────────
    def load_state(self):
        try:
            with open(self.state_path, encoding="utf-8") as fh:
                st = json.load(fh)
        except (OSError, ValueError):
            st = {}
        st.setdefault("seen", {})       # md5 -> {type, name, archived, seen_at}
        st.setdefault("days", {})       # iso -> {digest, uids, input, source_md5, processed_at, how}
        st.setdefault("last_followup", None)
        return st

    def save_state(self, st):
        if self.dry:
            return
        fd, tmp = tempfile.mkstemp(dir=self.archive, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1, sort_keys=True)
        os.replace(tmp, self.state_path)

    # ── the tracker's own memory: which patients it already holds for each day ──
    def ledger_uids(self):
        out = {}
        p = os.path.join(self.tracker, "data", "visit_ledger.csv")
        try:
            with open(p, encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    out.setdefault((r.get("Visit_Date") or "").strip(), set()).add(
                        (r.get("Patient_UID") or "").strip())
        except OSError:
            pass
        return out

    def seed_days_from_uploads(self, st):
        """First run: remember what the /run page has already processed, day by day, from the
        consultation reports it saved in uploads\\ (the newest file for a day wins)."""
        files = sorted(glob.glob(os.path.join(self.uploads, "consultation_report_*.csv")),
                       key=os.path.getmtime)
        seeded = 0
        for p in files:
            try:
                header, body, _ = read_rows(p)
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
            if classify(header) != "CONSULTATION":
                continue
            for d, rows in day_groups(body).items():
                prev = st["days"].get(d)
                if prev and prev.get("how") != "seeded":
                    continue
                st["days"][d] = {"digest": day_digest(rows), "uids": len(uids(rows)),
                                 "input": p, "source_md5": md5_of(p),
                                 "src_mtime": os.path.getmtime(p),
                                 "processed_at": stamp(_dt.datetime.fromtimestamp(
                                     os.path.getmtime(p))),
                                 "how": "seeded"}
                seeded += 1
        return seeded

    # ── discovery ──────────────────────────────────────────────────────────
    def candidates(self):
        out = []
        for p in glob.glob(os.path.join(self.downloads, "*.csv")):
            name = os.path.basename(p).lower()
            if name.startswith(NAME_PREFIXES):
                out.append(p)
        return sorted(out, key=os.path.getmtime)

    # ── archive ────────────────────────────────────────────────────────────
    def archive_copy(self, src, kind, date_from, date_to, md5):
        mt = _dt.datetime.fromtimestamp(os.path.getmtime(src))
        span = date_from if date_from == date_to else "%s_to_%s" % (date_from, date_to)
        month = ((date_from if kind == "FOLLOWUP_LOG" else date_to) or mt.strftime("%Y-%m-%d"))[:7]
        folder = os.path.join(self.archive, kind, month)
        name = "%s__%s__%s__%s.csv" % (kind, span or "nodate", mt.strftime("%Y%m%d-%H%M%S"),
                                        md5[:8])
        dest = os.path.join(folder, name)
        if not self.dry:
            os.makedirs(folder, exist_ok=True)
            if not os.path.exists(dest):
                shutil.copy2(src, dest)
        return dest

    def index_row(self, **kw):
        cols = ["seen_at", "type", "date_from", "date_to", "days", "rows", "md5", "verdict",
                "reason", "archived_path", "source_name"]
        if self.dry:
            return
        new = not os.path.exists(self.index_path)
        with open(self.index_path, "a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(cols)
            w.writerow([kw.get(c, "") for c in cols])

    # ── the decision for one business day of one consultation report ─────
    def decide(self, st, ledger, d, rows, mtime=None):
        dig, u = day_digest(rows), uids(rows)
        have = ledger.get(d, set())
        prev = st["days"].get(d)
        if prev and prev.get("digest") == dig:
            return "SKIP", "identical to what was already processed for this day"
        new = u - have
        if new:
            return "RUN", "%d patient(s) the tracker does not yet hold for this day" % len(new)
        if len(u) < len(have):
            return "QUARANTINE", ("this export has %d patients for %s; the tracker already holds %d "
                                  "-- a newer export with FEWER patients is never applied"
                                  % (len(u), d, len(have)))
        if prev is None and not have:
            return "RUN", "a day the tracker has never seen"
        if prev and mtime is not None and mtime <= prev.get("src_mtime", 0):
            return "SKIP", "same patients; this export is OLDER than the one already processed"
        age = (self.today - _dt.date.fromisoformat(d)).days
        if age <= RECENT_DAYS:
            return "RUN", "same patients, different money -- the newest export wins"
        return "SKIP", ("same patients, different money, but %d days old -- archived, not re-run "
                        "(run it on the /run page if it matters)" % age)

    # ── the tracker job ────────────────────────────────────────────────────
    def write_day_file(self, src, raw, header, d, rows):
        """A multi-day report cut to one day: header, banner, that day's rows. No footer."""
        name = "consultation_report_%s__auto_%s.csv" % (d, now_ist().strftime("%Y%m%d-%H%M%S"))
        dest = os.path.join(self.uploads, name)
        if self.dry:
            return dest
        with open(dest, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(raw[0])
            if len(raw) > 1 and not (raw[1][2].strip() if len(raw[1]) > 2 else ""):
                w.writerow(raw[1])                               # the clinic-name banner
            for r in rows:
                w.writerow([r.get(h, "") for h in header])
        return dest

    def place_input(self, src, md5):
        """Put the file in uploads\\ the way /run does, never over a different file."""
        base = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(src).replace(" (", "_").replace(")", ""))
        dest = os.path.join(self.uploads, base)
        if os.path.exists(dest):
            if md5_of(dest) == md5:
                return dest
            stem, ext = os.path.splitext(base)
            dest = os.path.join(self.uploads, "%s__auto_%s%s" % (
                stem, now_ist().strftime("%Y%m%d-%H%M%S"), ext))
        if not self.dry:
            shutil.copy2(src, dest)
        return dest

    def already_run_by_hand(self, md5):
        """True if the /run page has saved this exact file and produced a workbook after it."""
        for p in glob.glob(os.path.join(self.uploads, "*.csv")):
            try:
                if os.path.getsize(p) and md5_of(p) == md5:
                    t = os.path.getmtime(p)
                    for o in glob.glob(os.path.join(self.outputs, "Staff_Action_Today_*.xlsx")):
                        if os.path.getmtime(o) >= t:
                            return True
            except OSError:
                continue
        return False

    def keep_outputs(self, d):
        """Before a run, copy the nearby Staff_Action_Today workbooks aside -- a run can overwrite
        one of them, and nothing is ever lost."""
        folder = os.path.join(self.archive, "_outputs_before_run", now_ist().strftime("%Y%m%d-%H%M%S"))
        base = _dt.date.fromisoformat(d)
        kept = 0
        for k in range(-2, 4):
            n = "Staff_Action_Today_%s.xlsx" % (base + _dt.timedelta(days=k)).isoformat()
            p = os.path.join(self.outputs, n)
            if os.path.exists(p):
                if not self.dry:
                    os.makedirs(folder, exist_ok=True)
                    shutil.copy2(p, os.path.join(folder, n))
                kept += 1
        return kept

    def run_tracker(self, cons_path, fu_path, d, latest):
        if self.dry:
            self.say("DRY RUN -- would run the tracker for %s" % d)
            return True
        kept = self.keep_outputs(d)
        self.say("tracker run for %s  (inputs: %s + %s; %d nearby workbook(s) kept aside)"
                 % (d, os.path.basename(cons_path), os.path.basename(fu_path), kept))
        sys.path.insert(0, self.tracker)
        cwd = os.getcwd()
        try:
            os.chdir(self.tracker)
            if self.runner is None:
                import processor                                   # the tracker's own engine
                audit, staff = processor.run_daily(cons_path, fu_path, today=None)
                notices = list(getattr(processor, "INGEST_NOTICES", []))
            else:
                audit, staff, notices = self.runner(cons_path, fu_path)
        except Exception as e:                                     # noqa: BLE001
            self.shout("the tracker run for %s FAILED: %s" % (d, e))
            self.say(traceback.format_exc().rstrip())
            return False
        finally:
            os.chdir(cwd)
        self.say("tracker wrote %s" % os.path.basename(staff))
        self.last_staff = staff
        for n in notices:
            self.say("  tracker notice: %s" % n)
        if not latest:
            self.say("not the latest business day -- the staff list on the VPS is left as it is")
            return True
        try:
            if self.vps_upload is None:
                from push_to_vps import upload_workbook
                ok, msg = upload_workbook(staff)
            else:
                ok, msg = self.vps_upload(staff)
            (self.say if ok else self.shout)("VPS: %s" % msg)
        except Exception as e:                                     # noqa: BLE001
            self.shout("VPS upload skipped: %s" % e)
        try:
            if self.patient_push is None:
                r = subprocess.run([sys.executable, "-B", os.path.join(self.tracker,
                                    "push_patient_join.py"), "--push"], cwd=self.tracker,
                                   capture_output=True, text=True, timeout=600)
                tail = [x for x in (r.stdout or "").splitlines() if x.strip()][-3:]
                ok = r.returncode == 0
            else:
                ok, tail = self.patient_push()
            (self.say if ok else self.shout)("patient push: %s" % (" | ".join(tail) or "no output"))
        except Exception as e:                                     # noqa: BLE001
            self.shout("patient push skipped: %s" % e)
        return True

    # ── the split-payment legs ─────────────────────────────────────────────
    def write_tenders(self, st):
        sources = glob.glob(os.path.join(self.uploads, "consultation_report_*.csv"))
        sources += glob.glob(os.path.join(self.archive, "CONSULTATION", "*", "*.csv"))
        sources += glob.glob(os.path.join(self.archive, "CLINICAL", "*", "*.csv"))
        best = {}        # (date, bill key) -> (mtime, legs, source)
        loud = []
        for p in sources:
            try:
                header, body, _ = read_rows(p)
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
            if classify(header) not in ("CONSULTATION", "CLINICAL"):
                continue
            mt = os.path.getmtime(p)
            for r in body:
                d = iso_of(r.get("Consultation Date"))
                uid = (r.get("Patient UID") or "").strip()
                if not d or not UID_RE.fullmatch(uid):
                    continue
                try:
                    t = parse_tenders(r.get("Amount collected"), r.get("Mode Of Payment") or "")
                except UnknownTender as e:
                    loud.append("%s: %s" % (os.path.basename(p), e))
                    continue
                cid = str(r.get("Clinic Specific Id") or "").strip()
                if cid.endswith(".0"):
                    cid = cid[:-2]
                inv = str(r.get("Invoice No.") or "").strip()
                key = (d, inv or ("uid:" + uid))
                nz = {k: v for k, v in t.items() if v}
                cur = best.get(key)
                if cur is None or mt > cur[0]:
                    best[key] = (mt, nz, cid, inv, os.path.basename(p))
        rows = []
        for (d, _k), (mt, nz, cid, inv, src) in best.items():
            if len(nz) < 2:
                continue                                          # one tender: nothing to break up
            for tender, amt in sorted(nz.items()):
                rows.append([d, cid, inv, tender, int(round(amt * 100)), src])
        rows.sort()
        for m in loud[:10]:
            self.shout("unrecognised tender token, NOT guessed at -- " + m)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\r\n")
        w.writerow(["business_date", "clinic_id", "invoice_no", "tender", "amount_p", "source_file"])
        w.writerows(rows)
        data = buf.getvalue().encode("utf-8")
        out = os.path.join(self.outputs, "Day_Tenders.csv")
        try:
            with open(out, "rb") as fh:
                old = fh.read()
        except OSError:
            old = None
        days = len({r[0] for r in rows})
        if old is not None and old.replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n"):
            return "unchanged (%d legs across %d days)" % (len(rows), days)
        if self.dry:
            return "DRY RUN -- would write %d legs across %d days" % (len(rows), days)
        if old is not None:
            keep = os.path.join(self.archive, "_outputs_before_run", "Day_Tenders")
            os.makedirs(keep, exist_ok=True)
            shutil.copy2(out, os.path.join(keep, "Day_Tenders_%s.csv"
                                           % now_ist().strftime("%Y%m%d-%H%M%S")))
        fd, tmp = tempfile.mkstemp(dir=self.outputs, suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, out)
        return "written: %d legs across %d days" % (len(rows), days)

    # ── the emergency path: make today's call list current, now ─────────────
    def refresh_latest(self, sheet_push=None):
        """Re-run the tracker for the LATEST business day with the newest follow-up log, send that
        workbook to the VPS (so it is the newest there), and write it straight into the call-list
        tabs with push_followups_today.py -- the list staff see is current within a minute."""
        if not self.dry:
            os.makedirs(self.archive, exist_ok=True)
        st = self.load_state()
        if not st["days"]:
            self.say("first run: remembered %d day(s) the /run page has already processed"
                     % self.seed_days_from_uploads(st))
        latest = max(st["days"], default="")
        info = st["days"].get(latest, {})
        cons = info.get("input")
        fus = [p for p in self.candidates() if classify(read_rows(p)[0]) == "FOLLOWUP_LOG"]
        fus += glob.glob(os.path.join(self.uploads, "followup_logs*.csv"))
        fu = max(fus, key=os.path.getmtime) if fus else None
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
        try:
            if sheet_push is None:
                r = subprocess.run([sys.executable, "-B", os.path.join(self.tracker,
                                    "push_followups_today.py"), "--file", self.last_staff, "--push"],
                                   cwd=self.tracker, capture_output=True, text=True, timeout=600)
                tail = [x for x in (r.stdout or "").splitlines() if x.strip()][-3:]
                ok = r.returncode == 0 and any(x.startswith("DONE") for x in (r.stdout or "").splitlines())
            else:
                ok, tail = sheet_push(self.last_staff)
            (self.say if ok else self.shout)("call list tabs: %s" % (" | ".join(tail) or "no output"))
        except Exception as e:                                     # noqa: BLE001
            self.shout("call list push skipped: %s" % e)
            ok = False
        self.finish(st, "refresh of %s %s" % (latest, "ok" if ok else "with a SHOUT"))
        return 0 if ok else 1

    # ── one whole pass ─────────────────────────────────────────────────────
    def run(self):
        if not os.path.isdir(self.tracker) or not os.path.exists(os.path.join(self.tracker, "processor.py")):
            print("REFUSING: %s is not the tracker folder (no processor.py)." % self.tracker)
            return 2
        if not os.path.isdir(self.downloads):
            print("REFUSING: the Downloads folder %s is not there." % self.downloads)
            return 2
        if not self.dry:
            os.makedirs(self.archive, exist_ok=True)
        cands = self.candidates()
        st = self.load_state()
        if not st["days"]:
            n = self.seed_days_from_uploads(st)
            self.say("first run: remembered %d day(s) the /run page has already processed" % n)
        if cands:
            newest = max(os.path.getmtime(p) for p in cands)
            if time.time() - newest < QUIET_SECONDS:
                self.say("a Docterz file arrived %d s ago -- waiting for it to settle"
                         % int(time.time() - newest))
                self.finish(st, "waiting")
                return 0
        ledger = self.ledger_uids()
        todo = {}                 # iso -> list of (mtime, path_for_run, how, digest, uid_count, md5)
        new_followup = None
        saw_new = False
        for p in cands:
            try:
                md5 = md5_of(p)
            except OSError:
                continue
            if md5 in st["seen"]:
                continue
            saw_new = True
            try:
                header, body, raw = read_rows(p)
            except (OSError, UnicodeDecodeError, csv.Error) as e:
                self.say("unreadable, left alone: %s (%s)" % (os.path.basename(p), e))
                continue
            kind = classify(header)
            base = os.path.basename(p)
            if kind is None:
                st["seen"][md5] = {"type": "UNKNOWN", "name": base, "seen_at": stamp()}
                self.index_row(seen_at=stamp(), type="UNKNOWN", md5=md5, verdict="IGNORED",
                               reason="header is not a Docterz report this pass knows",
                               source_name=base)
                self.say("not a Docterz report I know, left alone: %s" % base)
                continue
            if kind == "FOLLOWUP_LOG":
                ds = sorted(iso_of(r.get("Followup Date")) or str(r.get("Followup Date", ""))[:10]
                            for r in body if (r.get("Appointment ID") or "").strip())
                ds = [x for x in ds if re.match(r"\d{4}-\d{2}-\d{2}$", x)]
                arch = self.archive_copy(p, kind, ds[0] if ds else "", ds[-1] if ds else "", md5)
                st["seen"][md5] = {"type": kind, "name": base, "archived": arch, "seen_at": stamp(),
                                   "mtime": os.path.getmtime(p)}
                self.index_row(seen_at=stamp(), type=kind, date_from=ds[0] if ds else "",
                               date_to=ds[-1] if ds else "", rows=len(body), md5=md5,
                               verdict="ARCHIVED", archived_path=arch, source_name=base)
                self.say("follow-up log archived: %s (%d rows, due %s to %s)"
                         % (base, len(body), ds[0] if ds else "?", ds[-1] if ds else "?"))
                if not new_followup or os.path.getmtime(p) > os.path.getmtime(new_followup):
                    new_followup = p
                continue
            groups = day_groups(body)
            days = sorted(groups)
            arch = self.archive_copy(p, kind, days[0] if days else "", days[-1] if days else "", md5)
            st["seen"][md5] = {"type": kind, "name": base, "archived": arch, "seen_at": stamp(),
                               "mtime": os.path.getmtime(p)}
            if kind == "CLINICAL":
                self.index_row(seen_at=stamp(), type=kind, date_from=days[0] if days else "",
                               date_to=days[-1] if days else "", days=len(days), rows=len(body),
                               md5=md5, verdict="ARCHIVED",
                               reason="kept for the clinical-report work (Ask 2); not fed to the tracker",
                               archived_path=arch, source_name=base)
                self.say("clinical data report archived: %s (%d days, %d rows)" % (base, len(days), len(body)))
                continue
            if not days:
                self.index_row(seen_at=stamp(), type=kind, rows=len(body), md5=md5,
                               verdict="ARCHIVED", reason="no patient rows (a closed day)",
                               archived_path=arch, source_name=base)
                self.say("consultation report with no patient rows archived, not run: %s" % base)
                continue
            by_hand = self.already_run_by_hand(md5)
            verdicts = []
            for d in days:
                rows = groups[d]
                v, why = self.decide(st, ledger, d, rows, os.path.getmtime(p))
                if v == "RUN" and by_hand and len(days) == 1:
                    v, why = "SKIP", "the /run page already processed this exact file"
                    st["days"][d] = {"digest": day_digest(rows), "uids": len(uids(rows)),
                                     "input": p, "source_md5": md5, "processed_at": stamp(),
                                     "src_mtime": os.path.getmtime(p), "how": "by hand"}
                verdicts.append("%s %s" % (d, v))
                self.say("%s  %s: %s -- %s" % (base, d, v, why))
                if v == "QUARANTINE":
                    self.shout("%s: %s" % (base, why))
                    if not self.dry:
                        q = os.path.join(self.archive, "_QUARANTINE")
                        os.makedirs(q, exist_ok=True)
                        shutil.copy2(arch, os.path.join(q, os.path.basename(arch)))
                elif v == "RUN":
                    todo.setdefault(d, []).append(
                        (os.path.getmtime(p), p, header, raw, rows, md5, len(days) == 1))
            self.index_row(seen_at=stamp(), type=kind, date_from=days[0], date_to=days[-1],
                           days=len(days), rows=sum(len(groups[x]) for x in days), md5=md5,
                           verdict="; ".join(verdicts), archived_path=arch, source_name=base)

        # the follow-up log a run pairs with: the newest one ever seen
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
        # the split-payment legs, every pass that saw something new
        if ran or saw_new or st.get("tenders_dirty") \
                or not os.path.exists(os.path.join(self.outputs, "Day_Tenders.csv")):
            try:
                self.say("split-payment legs: " + self.write_tenders(st))
                st["tenders_dirty"] = False
            except Exception as e:                                 # noqa: BLE001
                st["tenders_dirty"] = True                          # try again next pass
                self.shout("split-payment legs NOT written (will retry next pass): %s" % e)
        self.finish(st, "ran " + ", ".join(ran) if ran else "nothing new to run")
        return 0

    def finish(self, st, summary):
        st["last_pass"] = {"at": stamp(), "summary": summary, "version": VERSION,
                           "shouts": self.shouts[-5:]}
        self.save_state(st)
        self.flush_log()
        if self.dry:
            return
        with open(os.path.join(self.archive, "_last_pass.txt"), "w", encoding="utf-8") as fh:
            fh.write("END %s -- %s -- %s\n" % (stamp(), "SHOUT" if self.shouts else "ok", summary))
        if self.shouts:
            with open(os.path.join(self.archive, "DOCTERZ_SHOUTS.txt"), "a", encoding="utf-8") as fh:
                for s in self.shouts:
                    fh.write("[%s] %s\n" % (stamp(), s))


# ───────────────────────────────────────────────────────────────────────────── tenders (S223, proven)
CANON = {"cash": "Cash", "credit card": "Credit Card", "debit card": "Debit Card",
         "net banking": "Net Banking", "online payment": "Online Payment",
         "patient app": "Patient APP", "wallet": "Wallet"}
_PAIR = re.compile(r"([A-Za-z][A-Za-z .]*?)\s*:\s*([\d,]+(?:\.\d+)?)")
_LEAD = re.compile(r"\s*([\d,]+(?:\.\d+)?)")
_GATEWAY = re.compile(r"\s+(?:pay|order|txn|ref)[_-][A-Za-z0-9]{6,}\s*$", re.I)


class UnknownTender(ValueError):
    pass


def _num(x):
    if x is None:
        return 0.0
    s = str(x).replace(",", "").replace("\u20b9", "").strip()
    if s in ("", "nan", "None", "#VALUE!", "-"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _norm(k):
    return " ".join(str(k or "").strip().casefold().split())


def parse_tenders(amount_collected, mode_of_payment=""):
    raw = "" if amount_collected is None else str(amount_collected)
    out = {}
    pairs = _PAIR.findall(raw)
    if pairs:
        unknown = []
        for k, v in pairs:
            key = _norm(k)
            if key in CANON:
                out[CANON[key]] = out.get(CANON[key], 0.0) + _num(v)
            else:
                unknown.append(k.strip())
        if unknown:
            raise UnknownTender("unrecognised tender token(s) %r in %r" % (unknown, raw))
        return out
    m = _LEAD.match(raw)
    total = _num(m.group(1)) if m else 0.0
    if total == 0.0:
        return {}
    mode = _norm(_GATEWAY.sub("", str(mode_of_payment or "")))
    return {CANON.get(mode, mode_of_payment.strip() or "Unknown"): total}


# ───────────────────────────────────────────────────────────────────────────── lock + main
def take_lock(path):
    try:
        if os.path.exists(path) and time.time() - os.path.getmtime(path) > STALE_LOCK_SECONDS:
            os.remove(path)            # a lock left by a crashed pass -- our own file, not user data
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, stamp().encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", default=HERE)
    ap.add_argument("--downloads", default=DEFAULT_DOWNLOADS)
    ap.add_argument("--archive", default=DEFAULT_ARCHIVE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--refresh-latest", action="store_true",
                    help="re-make the latest day's call list now and push it to the call-list tabs")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if a.selftest:
        return selftest()
    lock = os.path.join(a.tracker, "_docterz_pickup.lock")
    if not a.dry_run and not take_lock(lock):
        print("another pass is running -- this one stands down")
        return 0
    try:
        p = Pass(a.tracker, a.downloads, a.archive, dry_run=a.dry_run)
        return p.refresh_latest() if a.refresh_latest else p.run()
    finally:
        if not a.dry_run:
            try:
                os.remove(lock)
            except OSError:
                pass


def selftest():
    fails = []

    def check(name, cond):
        print(("  ok   " if cond else "  FAIL ") + name)
        if not cond:
            fails.append(name)

    check("tender: split with wallet", parse_tenders("1100 (Wallet: 600, Online Payment: 500)")
          == {"Wallet": 600.0, "Online Payment": 500.0})
    check("tender: plain cash", parse_tenders("600", "Cash") == {"Cash": 600.0})
    try:
        parse_tenders("700 (Voucher: 700)")
        check("tender: unknown token raises", False)
    except UnknownTender:
        check("tender: unknown token raises", True)
    check("date: dd-mm-yyyy", iso_of("10-09-2026 11:05 AM") == "2026-09-10")
    check("classify consult", classify(["Consultation Date", "Patient UID", "Amount collected",
                                        "Bill Amount", "Advance Collected"]) == "CONSULTATION")
    check("classify clinical", classify(["Consultation Date", "Patient UID", "Amount collected",
                                         "Bill Amount", "Drugs Prescribed", "Diagnosis"]) == "CLINICAL")
    check("classify follow-up", classify(["Appointment ID", "Mobile No", "Patient Name",
                                          "Followup Date"]) == "FOLLOWUP_LOG")
    check("classify other", classify(["a", "b"]) is None)
    p = Pass("/nonexistent", "/nonexistent", "/nonexistent", dry_run=True,
             today=_dt.date(2026, 9, 11))
    r1 = [{"Patient UID": "ABCDEFGH1", "Consultation Date": "10-09-2026", "Bill Amount": "600"}]
    r2 = r1 + [{"Patient UID": "ABCDEFGH2", "Consultation Date": "10-09-2026", "Bill Amount": "600"}]
    st = {"days": {}, "seen": {}}
    check("decide: new day runs", p.decide(st, {}, "2026-09-10", r1)[0] == "RUN")
    led = {"2026-09-10": {"ABCDEFGH1", "ABCDEFGH2"}}
    check("decide: fewer patients quarantines", p.decide(st, led, "2026-09-10", r1)[0] == "QUARANTINE")
    check("decide: late-comer runs", p.decide(st, {"2026-09-10": {"ABCDEFGH1"}}, "2026-09-10", r2)[0] == "RUN")
    st2 = {"days": {"2026-09-10": {"digest": day_digest(r2)}}, "seen": {}}
    check("decide: identical skips", p.decide(st2, led, "2026-09-10", r2)[0] == "SKIP")
    r3 = [dict(r, **{"Bill Amount": "900"}) for r in r2]
    check("decide: recent money change runs", p.decide(st2, led, "2026-09-10", r3)[0] == "RUN")
    st3 = {"days": {"2026-08-01": {"digest": "x"}}, "seen": {}}
    led3 = {"2026-08-01": {"ABCDEFGH1", "ABCDEFGH2"}}
    r4 = [dict(r, **{"Consultation Date": "01-08-2026"}) for r in r3]
    check("decide: old money change is archived only", p.decide(st3, led3, "2026-08-01", r4)[0] == "SKIP")
    st4 = {"days": {"2026-09-10": {"digest": "x", "src_mtime": 200.0}}, "seen": {}}
    check("decide: an OLDER export never wins", p.decide(st4, led, "2026-09-10", r3, 100.0)[0] == "SKIP")
    check("decide: a NEWER export wins", p.decide(st4, led, "2026-09-10", r3, 300.0)[0] == "RUN")
    print("SELFTEST: %d failure(s)" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
