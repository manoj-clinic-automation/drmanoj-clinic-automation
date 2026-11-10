# -*- coding: utf-8 -*-
"""docterz_clinical_send.py -- kit S780_CLINICAL_FROM_DOWNLOADS (session S424, 10-Nov-2026). PARENT. NEW. Runs on manojz.

THE OWNER, 10-Nov-2026 19:23 IST: "It should also pick up when I export to my downloads folder in my PC."

Every pass of DOCTERZ_PICKUP.bat (Task Scheduler, every 5 minutes) runs this first. It looks at the CSV files in
D:\\Downloads, recognises a Docterz *Clinical data report* BY ITS COLUMNS (any file name -- Chrome's "clinical data report (1).csv"
too), and copies each one it has not sent before, once, into the Drive folder the clinic server reads:
    H:\\My Drive\\Clinic Records\\Docterz exports\\clinical_data_report_<latest day>_manojz_<6 hex>.csv
The server's pickup (kit S779) takes it within 15 minutes as a clinical report and reads every visit's diagnosis.
  * only a file downloaded on or after 10-Nov-2026 (older partial exports are not resent);
  * a file still being written is left for the next pass (it must be 2 minutes old);
  * nothing else in Downloads is touched; nothing is moved or deleted; the original stays where it is;
  * it prints counts, dates and md5s only -- never a name or a number.
SWITCH: D:\\Downloads\\DocterzArchive\\_clinical_send_OFF.txt (or D:\\Downloads\\margsync\\_off\\ALL_OFF.txt).
LOG: D:\\Downloads\\DocterzArchive\\_clinical_send_log.txt   STATE: D:\\Downloads\\DocterzArchive\\_clinical_send_state.json
Always ends 0, so the pickup after it always runs.
"""
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import os
import shutil
import sys
import time

DOWNLOADS = os.environ.get("CLINICAL_SEND_DOWNLOADS", r"D:\Downloads")
ARCHIVE = os.environ.get("CLINICAL_SEND_ARCHIVE", r"D:\Downloads\DocterzArchive")
DEST = os.environ.get("CLINICAL_SEND_DEST", r"H:\My Drive\Clinic Records\Docterz exports")
ALL_OFF = os.environ.get("CLINICAL_SEND_ALL_OFF", r"D:\Downloads\margsync\_off\ALL_OFF.txt")
FROM_DAY = dt.datetime(2026, 11, 10).timestamp()        # files downloaded before this are not sent
MIN_AGE = 120                                             # seconds: a file still being written waits a pass
MAX_BYTES = 5 * 1024 * 1024                               # the server's own limit for one report
NEED = ("Consultation Date", "Patient UID", "Diagnosis", "Drugs Prescribed")


def stamp():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def say(msg):
    line = "[%s] clinical send: %s" % (stamp(), msg)
    print(line)
    try:
        with open(os.path.join(ARCHIVE, "_clinical_send_log.txt"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def load_state():
    try:
        with open(os.path.join(ARCHIVE, "_clinical_send_state.json"), "r", encoding="utf-8") as fh:
            st = json.load(fh)
            return st if isinstance(st, dict) and isinstance(st.get("sent"), dict) else {"sent": {}}
    except (OSError, ValueError):
        return {"sent": {}}


def save_state(st):
    p = os.path.join(ARCHIVE, "_clinical_send_state.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)
    os.replace(tmp, p)


def parse_day(s):
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def clinical_span(raw):
    """(first day, last day, visit rows) when the bytes are a clinical data report; None otherwise."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return None
    if not rows:
        return None
    head = [h.strip() for h in rows[0]]
    if any(k not in head for k in NEED):
        return None
    i = head.index("Consultation Date")
    days = [parse_day(r[i]) for r in rows[1:] if len(r) > i]
    days = [d for d in days if d]
    if not days:
        return None
    return min(days), max(days), len(days)


def one_pass(now=None):
    now = now or time.time()
    if os.path.exists(os.path.join(ARCHIVE, "_clinical_send_OFF.txt")) or os.path.exists(ALL_OFF):
        return "off"
    if not os.path.isdir(DEST):
        say("the Drive folder is not reachable (%s) -- nothing sent; tried again next pass" % DEST)
        return "no-dest"
    st = load_state()
    sent = 0
    for p in sorted(glob.glob(os.path.join(DOWNLOADS, "*.csv")), key=os.path.getmtime):
        try:
            mt, size = os.path.getmtime(p), os.path.getsize(p)
        except OSError:
            continue
        if mt < FROM_DAY or size > MAX_BYTES or size == 0 or now - mt < MIN_AGE:
            continue
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        md5 = hashlib.md5(raw).hexdigest()
        if md5 in st["sent"]:
            continue
        span = clinical_span(raw)
        if span is None:
            continue                                      # not a clinical data report -- not ours
        d0, d1, n = span
        name = "clinical_data_report_%s_manojz_%s.csv" % (d1.isoformat(), md5[:6])
        dest = os.path.join(DEST, name)
        tmp = os.path.join(DEST, "~" + name + ".part")
        try:
            if not os.path.exists(dest):
                shutil.copyfile(p, tmp)
                os.replace(tmp, dest)
            with open(dest, "rb") as fh:
                ok = hashlib.md5(fh.read()).hexdigest() == md5
        except OSError as ex:
            say("could not copy a clinical report (%s): %s -- tried again next pass" % (md5[:8], ex.__class__.__name__))
            try:
                os.remove(tmp)
            except OSError:
                pass
            continue
        if not ok:
            say("the copy of %s did not read back -- tried again next pass" % md5[:8])
            continue
        st["sent"][md5] = {"at": stamp(), "days": "%s to %s" % (d0, d1), "rows": n, "as": name}
        save_state(st)
        sent += 1
        say("SENT a clinical data report: %s to %s, %d visit rows, md5 %s -> Drive 'Docterz exports' (the server takes it within 15 minutes)"
            % (d0, d1, n, md5[:8]))
    return "sent %d" % sent


def main():
    try:
        os.makedirs(ARCHIVE, exist_ok=True)
        one_pass()
    except Exception as ex:                               # noqa: BLE001 -- the pickup after this must always run
        say("ERROR %s: %s" % (ex.__class__.__name__, str(ex)[:160]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
