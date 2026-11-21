# -*- coding: utf-8 -*-
"""docterz_clinical_send.py -- kit S780_CLINICAL_FROM_DOWNLOADS (session S424, 10-Nov-2026). PARENT. NEW. Runs on manojz.
S916 (S496, 21-Nov-2026, the owner 08:34: "from reception pc and manojz"): it now also sends his FOLLOW-UP LOGS and his ONE-DAY
CONSULTATION REPORTS from D:\Downloads to the same Drive folder, as followup_logs_<first due>_manojz_<6 hex>.csv and
consultation_report_<day>_manojz_<6 hex>.csv, so the server holds every export whichever PC made it (the missing-export alert
then counts his, and after the switch the server's list uses his). Recognised by columns as the server does (a follow-up log:
'Appointment ID' + 'Mobile No'; a consultation report: 'Consultation Date' + 'Mode Of Payment', not a clinical report).
  * never a file the server fetch brought (a name with '_reception_', or an md5 in _server_fetch_state.json) -- no loop;
  * a consultation report of MORE THAN ONE DAY, or with no patients, is NOT sent (the server's Drive pickup takes a report as
    one day): it is logged once -- such a file goes through the Docterz reports page on the portal;
  * only files downloaded on or after 20-Nov-2026 12:00 for these two kinds; the clinical rule unchanged;
  * its own switch: D:\Downloads\DocterzArchive\_fu_cons_send_OFF.txt stops only these two kinds;
  * every copy keeps the file's own modified time, so the server dates a follow-up log by its export, not by the copy.

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
FROM_FU = dt.datetime(2026, 11, 20, 12, 0).timestamp()  # S916: follow-up logs / consultation reports downloaded before this: not sent
FETCH_STATE = os.environ.get("CLINICAL_SEND_FETCH_STATE", "")


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


def _rows(raw):
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    try:
        return list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return []


def fu_cons_span(raw):
    """S916: ('followup', first due, last due, rows) / ('consultation', day, day, patients) / ('cons_skip', d0, d1, n) for a
    consultation report of several days or none; None for anything else (a clinical report is clinical_span's)."""
    rows = _rows(raw)
    if not rows:
        return None
    head = [h.strip() for h in rows[0]]
    if "Appointment ID" in head and "Mobile No" in head:
        key = next((k for k in ("Follow Up Date", "Follow-up Date", "Followup Date", "Due Date", "Date") if k in head), None)
        days = []
        if key:
            i = head.index(key)
            days = [d for d in (parse_day(r[i]) for r in rows[1:] if len(r) > i) if d]
        body = [r for r in rows[1:] if any(str(c).strip() for c in r)]
        if not days:
            return ("followup", None, None, len(body))
        return ("followup", min(days), max(days), len(body))
    if "Consultation Date" in head and "Mode Of Payment" in head and "Diagnosis" not in head:
        i = head.index("Consultation Date")
        days = [d for d in (parse_day(r[i]) for r in rows[1:] if len(r) > i) if d]
        uniq = sorted(set(days))
        if len(uniq) != 1:
            return ("cons_skip", uniq[0] if uniq else None, uniq[-1] if uniq else None, len(days))
        return ("consultation", uniq[0], uniq[0], len(days))
    return None


def _fetched_md5s():
    """S916: the md5s the server fetch brought into Downloads -- never sent back."""
    p = FETCH_STATE or os.path.join(ARCHIVE, "_server_fetch_state.json")
    try:
        with open(p, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        have = d.get("have") if isinstance(d, dict) else None
        return set(have) if isinstance(have, dict) else set()
    except (OSError, ValueError):
        return None


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
        kind = "clinical"
        if span is None:                                  # S916: a follow-up log or a one-day consultation report
            if os.path.exists(os.path.join(ARCHIVE, "_fu_cons_send_OFF.txt")) or mt < FROM_FU \
                    or "_reception_" in os.path.basename(p):
                continue
            fc = fu_cons_span(raw)
            if fc is None:
                continue                                  # not a Docterz report of these kinds -- not ours
            fetched = _fetched_md5s()
            if fetched is None:
                continue                                  # the fetch's record unreadable: wait, never risk sending one back
            if md5 in fetched:
                continue
            kind, d0, d1, n = fc
            if kind == "cons_skip":
                st["sent"][md5] = {"at": stamp(), "kind": "consultation", "days": "%s to %s" % (d0, d1), "rows": n, "as": "NOT SENT"}
                save_state(st)
                say("NOT sent: a consultation report of %s to %s (%d rows) -- more than one day or no patients; "
                    "upload it on the Docterz reports page if the server needs it" % (d0, d1, n))
                continue
            if kind == "followup":
                name = "followup_logs_%s_manojz_%s.csv" % ((d0.isoformat() if d0 else "nodate"), md5[:6])
            else:
                name = "consultation_report_%s_manojz_%s.csv" % (d0.isoformat(), md5[:6])
        else:
            d0, d1, n = span
            name = "clinical_data_report_%s_manojz_%s.csv" % (d1.isoformat(), md5[:6])
        dest = os.path.join(DEST, name)
        tmp = os.path.join(DEST, "~" + name + ".part")
        try:
            if not os.path.exists(dest):
                shutil.copyfile(p, tmp)
                os.utime(tmp, (mt, mt))                   # S916: the copy keeps the export's own time -- the server dates a
                os.replace(tmp, dest)                     # follow-up log by it (before 13:00 = the previous working day)
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
        st["sent"][md5] = {"at": stamp(), "kind": kind, "days": "%s to %s" % (d0, d1), "rows": n, "as": name}
        save_state(st)
        sent += 1
        say("SENT a %s: %s to %s, %d rows, md5 %s -> Drive 'Docterz exports' (the server takes it within 15 minutes)"
            % ({"clinical": "clinical data report", "followup": "follow-up log", "consultation": "consultation report"}[kind],
               d0, d1, n, md5[:8]))
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
