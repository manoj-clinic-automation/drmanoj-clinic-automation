#!/usr/bin/env python3
"""
make_force_keys.py v1.1 — ONE-OFF, READ-ONLY (S143, D240 companion; v1.1 = numeric time compare, the unpadded-hour fix)

Resolves the 41 D237 referee calls (seed D237-S142) to their exact Join Keys
by reading the live Call_Verdicts tab, and writes them, in referee-workbook
order, to force_keys.txt for verdict_review.py v3 to draw as full cards.

READS  : Call_Verdicts (doctor-only audit sheet) — nothing else.
WRITES : /root/wa/recordings-archive/force_keys.txt — a local VPS file only.
         NO Google Sheet is written. No tab is touched.

Match rule: Patient Number exact + Date exact + Time starts with HH:MM.
0 matches for a row  -> named in the report, run continues.
2+ matches for a row -> AMBIGUOUS: named, NOT guessed, run continues.
The file is written only if at least one key resolved; the report always
states resolved / missing / ambiguous so nothing fails silently (D172).

USAGE
  /root/wa/venv/bin/python3 make_force_keys.py --selftest   (offline)
  /root/wa/venv/bin/python3 make_force_keys.py --dry-run    (reads, writes nothing)
  /root/wa/venv/bin/python3 make_force_keys.py              (writes force_keys.txt)
"""

import argparse
import os
import sys

ENV_PATH = "/root/wa/.env"
AUDIT_SHEET_ID_DEFAULT = "1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ"
VERDICT_TAB = "Call_Verdicts"
OUT_PATH = "/root/wa/recordings-archive/force_keys.txt"

# The 41 referee calls, in D237_Referee_Set_S142.xlsx order (#1..#41).
TRIPLES = [
    ("8881440092", "2026-06-29", "09:06"),
    ("9690543321", "2026-06-29", "09:26"),
    ("9458746024", "2026-06-29", "13:06"),
    ("7830874960", "2026-06-30", "09:10"),
    ("9760354820", "2026-06-30", "13:42"),
    ("8445361509", "2026-06-30", "15:05"),
    ("9198094807", "2026-06-30", "15:08"),
    ("9758166664", "2026-06-30", "17:39"),
    ("9719292532", "2026-07-01", "08:53"),
    ("8679432210", "2026-07-01", "14:18"),
    ("8796328006", "2026-07-03", "09:32"),
    ("9027976079", "2026-07-03", "17:42"),
    ("8317010363", "2026-07-03", "19:28"),
    ("9917583193", "2026-07-04", "07:59"),
    ("8868060296", "2026-07-04", "09:10"),
    ("7830874960", "2026-07-04", "12:22"),
    ("8791797575", "2026-07-06", "09:10"),
    ("9808130895", "2026-07-06", "09:17"),
    ("8171661506", "2026-07-06", "10:41"),
    ("9412292255", "2026-07-06", "10:50"),
    ("6395365227", "2026-07-06", "12:01"),
    ("7818829169", "2026-07-06", "13:56"),
    ("7388701581", "2026-07-06", "14:32"),
    ("8368159367", "2026-07-06", "14:46"),
    ("7830874960", "2026-07-07", "08:43"),
    ("6393579456", "2026-07-07", "08:55"),
    ("9045018813", "2026-07-07", "14:36"),
    ("7830874960", "2026-07-08", "08:35"),
    ("9557874503", "2026-07-08", "08:39"),
    ("8445359357", "2026-07-08", "08:47"),
    ("8287590248", "2026-07-08", "08:51"),
    ("8859928651", "2026-07-08", "11:18"),
    ("7455861757", "2026-07-08", "13:40"),
    ("9415178016", "2026-07-09", "08:33"),
    ("9897802196", "2026-07-09", "08:44"),
    ("6387662448", "2026-07-09", "09:22"),
    ("1205076473", "2026-07-09", "14:44"),
    ("8077143486", "2026-07-10", "08:59"),
    ("7947063805", "2026-07-12", "12:29"),
    ("7835056790", "2026-07-13", "09:36"),
    ("8016679400", "2026-07-13", "10:04")
]


def load_env():
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(),
                                  val.strip().strip('"').strip("'"))


def time_minutes(t):
    """'9:06', '09:06', '09:06:12' -> minutes since midnight; None if unparseable.
    Call_Verdicts stores UNPADDED hours (the S142 lesson) — compare times as
    parsed numbers, never as text."""
    import re
    m = re.match(r"^\s*(\d{1,2}):(\d{2})", str(t or ""))
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def match_rows(rows, triples):
    """rows: list of dicts with Patient Number / Date / Time / Join Key.
    Returns (resolved_keys_in_order, missing_triples, ambiguous_triples)."""
    resolved, missing, ambiguous = [], [], []
    for num, date, hhmm in triples:
        want = time_minutes(hhmm)
        hits = [r for r in rows
                if str(r.get("Patient Number", "")).strip() == num
                and str(r.get("Date", "")).strip() == date
                and time_minutes(r.get("Time")) == want]
        keys = sorted({str(r.get("Join Key", "")).strip() for r in hits} - {""})
        if len(keys) == 1:
            resolved.append(keys[0])
        elif not keys:
            missing.append((num, date, hhmm))
        else:
            ambiguous.append((num, date, hhmm))
    return resolved, missing, ambiguous


def selftest():
    ok = [0]

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok[0] += 0 if cond else 1

    rows = [
        {"Patient Number": "8881440092", "Date": "2026-06-29",
          "Time": "09:06:12", "Join Key": "8881440092_1782704172"},
        {"Patient Number": "9690543321", "Date": "2026-06-29",
          "Time": "09:26", "Join Key": "9690543321_1782705360"},
        {"Patient Number": "7000000001", "Date": "2026-07-01",
          "Time": "10:00:01", "Join Key": "7000000001_1"},
        {"Patient Number": "7000000001", "Date": "2026-07-01",
          "Time": "10:00:59", "Join Key": "7000000001_2"},
    ]
    r, m, a = match_rows(rows, [("8881440092", "2026-06-29", "09:06")])
    check("seconds-bearing time still matches on HH:MM",
          r == ["8881440092_1782704172"] and not m and not a)
    r, m, a = match_rows(rows, [("9690543321", "2026-06-29", "09:26")])
    check("bare HH:MM time matches", r == ["9690543321_1782705360"])
    r, m, a = match_rows(
        [{"Patient Number": "8881440092", "Date": "2026-06-29",
          "Time": "9:06", "Join Key": "8881440092_1782704172"}],
        [("8881440092", "2026-06-29", "09:06")])
    check("UNPADDED tab hour '9:06' matches padded '09:06' (the S142/live lesson)",
          r == ["8881440092_1782704172"] and not m and not a)
    check("time_minutes parses unpadded, padded, and seconds forms alike",
          time_minutes("9:06") == time_minutes("09:06") == time_minutes("09:06:12") == 546)
    check("time_minutes junk -> None", time_minutes("") is None and time_minutes("x") is None)
    r, m, a = match_rows(rows, [("1111111111", "2026-06-29", "09:06")])
    check("unknown number -> missing, never guessed", not r and len(m) == 1)
    r, m, a = match_rows(rows, [("7000000001", "2026-07-01", "10:00")])
    check("two calls in one minute -> AMBIGUOUS, never guessed",
          not r and len(a) == 1)
    check("41 triples embedded", len(TRIPLES) == 41)
    check("all numbers are 10 digits",
          all(len(t[0]) == 10 and t[0].isdigit() for t in TRIPLES))
    check("no duplicate triples", len(set(TRIPLES)) == 41)
    check("output path is inside recordings-archive",
          OUT_PATH.startswith("/root/wa/recordings-archive/"))
    print(f"SELFTEST: {'PASS' if ok[0] == 0 else str(ok[0]) + ' FAILED'}")
    return ok[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())

    import gspread
    from google.oauth2.service_account import Credentials
    load_env()
    sa_path = os.environ.get("GOOGLE_SA_KEY") or os.environ.get("WA_SA_KEY")
    if not sa_path:
        sys.exit("ERROR: no service-account key path in the environment.")
    creds = Credentials.from_service_account_file(
        sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(os.environ.get("AUDIT_SHEET_ID", AUDIT_SHEET_ID_DEFAULT))
    ws = ss.worksheet(VERDICT_TAB)
    values = ws.get_all_values()
    hdr = values[0]
    rows = [dict(zip(hdr, r)) for r in values[1:]]
    print(f"Read {len(rows)} rows from '{VERDICT_TAB}' (READ-ONLY scope).")

    resolved, missing, ambiguous = match_rows(rows, TRIPLES)
    print(f"Resolved {len(resolved)}/41 referee keys.")
    for num, d, t in missing:
        print(f"  MISSING   ******{num[-4:]}  {d} {t} — no Call_Verdicts row matched")
    for num, d, t in ambiguous:
        print(f"  AMBIGUOUS ******{num[-4:]}  {d} {t} — 2+ rows in that minute; not guessed")

    if args.dry_run:
        print("DRY RUN — force_keys.txt NOT written.")
        return
    if not resolved:
        sys.exit("ERROR: zero keys resolved; refusing to write an empty file.")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("# D237 referee set (seed D237-S142) — written by make_force_keys.py S143\n")
        for k in resolved:
            f.write(k + "\n")
    print(f"Wrote {len(resolved)} key(s) to {OUT_PATH}.")


if __name__ == "__main__":
    main()
