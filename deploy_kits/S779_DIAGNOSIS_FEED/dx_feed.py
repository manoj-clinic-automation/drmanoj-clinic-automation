#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dx_feed.py -- kit S779_DIAGNOSIS_FEED (session S424, 10-Nov-2026, D884, F-1225). PARENT. NEW.

THE OWNER (D884, 10-Nov-2026): the Patients section starts from the diagnosis of every visit. Docterz's *Clinical data
report* carries it; reception adds it as a third evening export, and one catch-up export (01-Jul onward) brings the past.

WHAT THIS DOES: every clinical data report that docterz_pickup.py keeps as 'current' (kind 'clinical') is read here, row by
row, into ONE row per patient per visit day in `dx_visit`:
  * the Docterz Patient UID, the clinic's own ID, the visit day, the diagnosis as written, and the follow-up date advised;
  * the diagnosis is normalised by the owner's own taxonomy (diagnosis_normalizer.py -- his Orthopedic_Diagnosis_Taxonomy_
    Master, 27 diagnoses + 12 gap terms, as on the follow-up tracker on his PC since June) into a standard diagnosis,
    its category and its follow-up priority;
  * a term the taxonomy does not know stays 'Other / Unclassified' unless the owner has mapped it once (`dx_term_map`,
    filled by the one-tap list that comes with the Patients section);
  * a later export of the same visit wins (the export's id); two rows of one patient on one day (consultation + procedure)
    give the first diagnosis written and the latest follow-up date.
Patient names and mobile numbers are NOT copied here (they stay in the kept export on the box). Prints counts only.

    /root/wa/venv/bin/python3 -B /root/finance/dx_feed.py [--db PATH] [--status]
docterz_pickup.take() calls run() by itself whenever a clinical report is taken (fail-soft: a fault here never refuses an export).
"""
import argparse
import csv
import datetime as dt
import io
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
UNCLASSIFIED = "Other / Unclassified"

DDL = """
CREATE TABLE IF NOT EXISTS dx_visit (
  patient_uid     TEXT NOT NULL,
  visit_date      TEXT NOT NULL,
  clinic_id       TEXT NOT NULL DEFAULT '',
  diagnosis_raw   TEXT NOT NULL DEFAULT '',
  std_dx          TEXT NOT NULL DEFAULT '',
  category        TEXT NOT NULL DEFAULT '',
  priority        TEXT NOT NULL DEFAULT '',
  dx_status       TEXT NOT NULL DEFAULT '',
  follow_up_date  TEXT NOT NULL DEFAULT '',
  export_id       INTEGER NOT NULL DEFAULT 0,
  updated_at      TEXT NOT NULL,
  PRIMARY KEY (patient_uid, visit_date)
);
CREATE INDEX IF NOT EXISTS ix_dx_visit_day ON dx_visit(visit_date);
CREATE INDEX IF NOT EXISTS ix_dx_visit_dx ON dx_visit(std_dx);
CREATE TABLE IF NOT EXISTS dx_term_map (
  term     TEXT PRIMARY KEY,
  std_dx   TEXT NOT NULL,
  set_by   TEXT NOT NULL DEFAULT '',
  set_at   TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS dx_feed_run (
  export_id  INTEGER PRIMARY KEY,
  rows_read  INTEGER NOT NULL DEFAULT 0,
  visits     INTEGER NOT NULL DEFAULT 0,
  run_at     TEXT NOT NULL
);
"""


def now():
    return dt.datetime.now().replace(microsecond=0).isoformat(sep=" ")


def ensure(con):
    con.executescript(DDL)


def _normaliser():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import diagnosis_normalizer as dn                       # noqa: PLC0415 -- the owner's taxonomy, beside this file
    return dn


def parse_day(s):
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def term_key(raw):
    return " ".join(str(raw or "").upper().split())


def classify(dn, raw, term_map):
    """(diagnosis_raw, std_dx, category, priority, status) for one written diagnosis."""
    raw = str(raw or "").strip()
    if not raw:
        return "", "", "", "", ""
    r = dn.normalise_diagnosis(raw)
    std = r.get("Standardized_Diagnosis") or UNCLASSIFIED
    cat, pri, sta = r.get("Diagnosis_Category", ""), r.get("Diagnosis_Priority", ""), r.get("Diagnosis_Status", "")
    clean = r.get("Diagnosis_Raw", raw)
    if std == UNCLASSIFIED:
        mapped = term_map.get(term_key(clean)) or term_map.get(term_key(raw))
        if mapped:
            std, cat = mapped, dn.CATEGORY.get(mapped, cat)
    return clean, std, cat, pri, sta


def read_rows(raw_bytes):
    """[(uid, day, clinic_id, diagnosis, follow_up)] from a clinical data report's bytes; [] when it is not one."""
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("cp1252", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    head = [h.strip() for h in rows[0]]
    idx = {h: i for i, h in enumerate(head)}
    need = ("Patient UID", "Consultation Date", "Diagnosis")
    if any(k not in idx for k in need):
        return []

    def cell(r, k):
        i = idx.get(k)
        return r[i].strip() if i is not None and len(r) > i else ""
    out = []
    for r in rows[1:]:
        uid, day = cell(r, "Patient UID"), parse_day(cell(r, "Consultation Date"))
        if not uid or not day:
            continue                                        # the clinic-name row and footers carry neither
        out.append((uid, day, cell(r, "Clinic Specific Id"), cell(r, "Diagnosis"), parse_day(cell(r, "Follow Up"))))
    return out


def ingest(con, export_id, raw_bytes, dn=None, term_map=None):
    """One export into dx_visit. Returns (rows read, visits written)."""
    ensure(con)
    dn = dn or _normaliser()
    if term_map is None:
        term_map = {t: s for t, s in con.execute("SELECT term, std_dx FROM dx_term_map")}
    per = {}
    rows = read_rows(raw_bytes)
    for uid, day, cid, dx, fu in rows:
        k = (uid, day)
        cur = per.get(k)
        if cur is None:
            per[k] = [cid, dx, fu]
        else:
            if not cur[1] and dx:
                cur[1] = dx                                 # the first diagnosis written that day
            if fu and fu > cur[2]:
                cur[2] = fu                                 # the latest follow-up advised that day
            if not cur[0] and cid:
                cur[0] = cid
    ts, n = now(), 0
    for (uid, day), (cid, dx, fu) in per.items():
        clean, std, cat, pri, sta = classify(dn, dx, term_map)
        old = con.execute("SELECT export_id FROM dx_visit WHERE patient_uid=? AND visit_date=?", (uid, day)).fetchone()
        if old is not None and int(old[0] or 0) > int(export_id):
            continue                                        # a newer export already gave this visit
        con.execute("INSERT OR REPLACE INTO dx_visit (patient_uid, visit_date, clinic_id, diagnosis_raw, std_dx, category, priority, "
                    "dx_status, follow_up_date, export_id, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (uid, day, cid, clean, std, cat, pri, sta, fu, int(export_id), ts))
        n += 1
    con.execute("INSERT OR REPLACE INTO dx_feed_run (export_id, rows_read, visits, run_at) VALUES (?,?,?,?)", (int(export_id), len(rows), n, ts))
    con.commit()
    return len(rows), n


def run(con, only_new=True):
    """Every current clinical export not yet read (all of them with only_new=False), oldest first. Returns [(id, rows, visits)]."""
    ensure(con)
    done = {r[0] for r in con.execute("SELECT export_id FROM dx_feed_run")} if only_new else set()
    dn = _normaliser()
    term_map = {t: s for t, s in con.execute("SELECT term, std_dx FROM dx_term_map")}
    out = []
    try:
        todo = con.execute("SELECT id, stored FROM docterz_export WHERE kind='clinical' AND status='current' AND stored<>'' ORDER BY id").fetchall()
    except sqlite3.Error:
        return out                                          # docterz_pickup has not made its table yet
    for eid, stored in todo:
        if eid in done:
            continue
        try:
            with open(stored, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        rr, vv = ingest(con, eid, raw, dn, term_map)
        out.append((eid, rr, vv))
    return out


def reclassify(con):
    """After the owner maps a term: every visit is re-read through the taxonomy and the map. Returns the rows changed."""
    ensure(con)
    dn = _normaliser()
    term_map = {t: s for t, s in con.execute("SELECT term, std_dx FROM dx_term_map")}
    n = 0
    for uid, day, raw, std in con.execute("SELECT patient_uid, visit_date, diagnosis_raw, std_dx FROM dx_visit WHERE diagnosis_raw<>''").fetchall():
        _, s2, c2, p2, t2 = classify(dn, raw, term_map)
        if s2 != std:
            con.execute("UPDATE dx_visit SET std_dx=?, category=?, priority=?, dx_status=?, updated_at=? WHERE patient_uid=? AND visit_date=?",
                        (s2, c2, p2, t2, now(), uid, day))
            n += 1
    con.commit()
    return n


def unknown_terms(con, limit=200):
    """[(term as written, visits)] the taxonomy does not know and the owner has not mapped -- the one-tap list's rows."""
    ensure(con)
    return con.execute("SELECT diagnosis_raw, COUNT(*) FROM dx_visit WHERE std_dx=? GROUP BY UPPER(TRIM(diagnosis_raw)) "
                       "ORDER BY COUNT(*) DESC, diagnosis_raw LIMIT ?", (UNCLASSIFIED, limit)).fetchall()


def status(con):
    ensure(con)
    t = con.execute("SELECT COUNT(*), COUNT(DISTINCT patient_uid), MIN(visit_date), MAX(visit_date), "
                    "SUM(diagnosis_raw<>''), SUM(std_dx=?) FROM dx_visit", (UNCLASSIFIED,)).fetchone()
    return {"visits": t[0], "patients": t[1], "from": t[2], "to": t[3], "with_diagnosis": t[4] or 0, "unclassified": t[5] or 0,
            "exports_read": con.execute("SELECT COUNT(*) FROM dx_feed_run").fetchone()[0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--all", action="store_true", help="re-read every current clinical export")
    a = ap.parse_args()
    con = sqlite3.connect(a.db, timeout=30)
    if not a.status:
        for eid, rr, vv in run(con, only_new=not a.all):
            print("  clinical export #%d: %d rows -> %d visits" % (eid, rr, vv))
    print("dx_feed: %s" % status(con))


if __name__ == "__main__":
    main()
