#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""xray_filmdate.py -- kit S772_XRAY_FILM_DATE (the parent; session S422, 10-Nov-2026). The owner, 11:10 IST: "X-rays carry
date of X-ray also, so a better match is possible?" -- 11:13: "do all thats possible".

WHAT. Every parked X-ray picture nobody has answered (xray_filing state 'check', the picture in Drive's "X-ray check" folder)
is read ONCE: the date printed on the film (OCR of the top and bottom bands, the whole picture if they give none). Every
plausible date found -- both readings of 05/11 -- within the 120 days before the picture was first seen goes into
xray_filmdate(src_id, dates, ids, how, secs, read_at) with the clinic IDs it prints (4-6 digits beside the name). records.py's S772 re-try uses it on the next filing run: a date that is one
of the ID's X-ray days (or, with no ID, the one date found) is the day the picture is filed on.
Reads finance.db and Drive (records_drive.py, read-only scope); writes ONLY the xray_filmdate table. The picture is held in
a private temp folder while read and deleted at once; nothing of it is kept. At most S772_MAX pictures and S772_SECS seconds
per run (cron every 30 minutes). A picture whose film gives no date gets a row with dates '[]' and is not read again.
Switch: /root/finance/_off/XRAY_FILMDATE_OFF (or ALL_OFF) -> the run does nothing.
OCR: tesseract when on PATH, else RapidOCR in the running python (the installer picks the python).
No patient data, no secret in this file (F-185).
"""
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
HELPER = os.environ.get("S772_HELPER", "/root/finance/records_drive.py")
HELPER_PY = os.environ.get("S772_HELPER_PY", "/root/wa/venv/bin/python3")
OFF = [os.environ.get("S772_OFF", "/root/finance/_off/XRAY_FILMDATE_OFF"), "/root/finance/_off/ALL_OFF"]
MAX = int(os.environ.get("S772_MAX", "40"))
SECS = int(os.environ.get("S772_SECS", "900"))
WINDOW = 120
OCR_SECS = 90
SCHEMA = """CREATE TABLE IF NOT EXISTS xray_filmdate (src_id TEXT PRIMARY KEY, dates TEXT NOT NULL DEFAULT '[]', ids TEXT NOT NULL DEFAULT '[]',
  how TEXT NOT NULL DEFAULT '', secs REAL NOT NULL DEFAULT 0, read_at TEXT NOT NULL DEFAULT '')"""


def ids_in(text):
    """The clinic IDs the film prints -- in the clinic's films the ID follows the name ('NAME 8241' or 'NAME8241'): every run
    of 4-6 digits that is not part of a date, a time or a longer number (the clinic's phone)."""
    out = []
    for line in (text or "").splitlines():
        t = norm(line)
        for _, rx in DATE_PATS:
            t = rx.sub(" ", t)
        t = re.sub(r"\d{1,2}:\d{2}", " ", t)
        for m in re.finditer(r"(?<!\d)(\d{4,6})(?!\d)", t):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


MONTHS = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}
MON_RE = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC"
DATE_PATS = [
    ("dmy", re.compile(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?=\D|$|\d{1,2}:\d{2})")),
    ("ymd", re.compile(r"(?<!\d)(\d{4})\s*[/.\-:]\s*(\d{1,2})\s*[/.\-:]\s*(\d{2}|\d)(?=\D|$|\d{2}:\d{2})")),
    ("dMy", re.compile(r"(?<!\d)(\d{1,2})\s*[\-/ .,]?\s*(" + MON_RE + r")[A-Z]*\s*[\-/ .,]?\s*(\d{4}|\d{2})(?=\D|$|\d{1,2}:\d{2})", re.I)),
    ("Mdy", re.compile(r"(?<![A-Z])(" + MON_RE + r")[A-Z]*\s*[\-/ .]?\s*(\d{1,2})\s*,?\s*(\d{4})(?!\d)", re.I)),
    ("ymd8", re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")),
]
LO, HI = dt.date(2024, 1, 1), dt.date(2040, 12, 31)          # the window per picture is applied in main()



def _mk(y, m, d):
    try:
        y = int(y)
        if y < 100:
            y += 2000
        x = dt.date(y, int(m), int(d))
        return x if LO <= x <= HI else None
    except (ValueError, TypeError):
        return None


def norm(t):
    """OCR's usual confusions in a date: a zero for the O of a month (12-0ct, N0v), O / o for a zero between digits."""
    t = re.sub(r"(?i)(?<=[\dA-Z \-/.,])0(?=CT|CTOBER)", "O", t)
    t = re.sub(r"(?i)(?<=N)0(?=V)", "O", t)
    t = re.sub(r"(?<=\d)[Oo](?=\d)", "0", t)
    t = re.sub(r"(?<=[\-/.])[Oo](?=\d)", "0", t)
    return t


def dates_in(text):
    """[(date, how)] -- every plausible date in the text; dd/mm read first (India), mm/dd as a second reading."""
    out = []
    t = norm(text or "")
    for how, rx in DATE_PATS:
        for m in rx.finditer(t):
            g = m.groups()
            if how == "dmy":
                a = _mk(g[2], g[1], g[0])
                if a:
                    out.append((a, "dd/mm"))
                b = _mk(g[2], g[0], g[1])
                if b and b != a:
                    out.append((b, "mm/dd"))
            elif how in ("ymd", "ymd8"):
                a = _mk(g[0], g[1], g[2])
                if a:
                    out.append((a, how))
            elif how == "dMy":
                a = _mk(g[2], MONTHS.get(g[1].upper()[:3]), g[0])
                if a:
                    out.append((a, "d-Mon-y"))
            elif how == "Mdy":
                a = _mk(g[2], MONTHS.get(g[0].upper()[:3]), g[1])
                if a:
                    out.append((a, "Mon-d-y"))
    return out


_RAPID = []



def engine():
    """'tesseract' | 'rapidocr' | '' -- the system tool when there, else RapidOCR in this python."""
    if shutil.which("tesseract"):
        return "tesseract"
    try:
        if not _RAPID:
            from rapidocr_onnxruntime import RapidOCR
            _RAPID.append(RapidOCR())
        return "rapidocr"
    except Exception:                                 # noqa: BLE001
        return ""


def ocr_text(path, work):
    """(text, seconds, how). The bands where the film's text is printed (top and bottom fifth), then the whole
    picture if the bands give no date."""
    t0 = time.time()
    eng = engine()
    if not eng:
        return "", 0.0, "no OCR tool"
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(path)).convert("L")
    w, h = im.size
    if max(w, h) > 3000:
        sc = 3000.0 / max(w, h)
        im = im.resize((int(w * sc), int(h * sc)))
        w, h = im.size

    def read(img, tag):
        if eng == "tesseract":
            p = os.path.join(work, tag + ".png")
            ImageOps.invert(img).save(p)
            try:
                r = subprocess.run(["tesseract", p, "stdout", "--psm", "11"], capture_output=True, timeout=OCR_SECS)
                return r.stdout.decode("utf-8", "replace")
            except Exception:                         # noqa: BLE001
                return ""
        import numpy as np
        try:
            res, _ = _RAPID[0](np.array(img.convert("RGB")))
        except Exception:                             # noqa: BLE001
            return ""
        return "\n".join(x[1] for x in (res or []))
    texts = [read(im.crop((0, 0, w, int(h * 0.2))), "top"), read(im.crop((0, int(h * 0.8), w, h)), "bottom")]
    how = eng + " bands"
    if not any(dates_in(x) for x in texts):
        texts.append(read(im, "whole"))
        how = eng + " bands+whole"
    return "\n".join(texts), time.time() - t0, how


def helper(what, fid):
    py = HELPER_PY if os.path.exists(HELPER_PY) else sys.executable
    r = subprocess.run([py, "-B", HELPER, what, fid], capture_output=True, timeout=180)
    if r.returncode != 0:
        return None
    return r.stdout



def say(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def main():
    if any(os.path.exists(p) for p in OFF if p):
        say("switched off -- nothing done")
        return 0
    eng = engine()
    if not eng:
        say("no OCR tool -- nothing done")
        return 1
    c = sqlite3.connect(DB, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute(SCHEMA)
    c.commit()
    todo = [r for r in c.execute("SELECT x.src_id, x.file_time, x.day FROM xray_filing x LEFT JOIN xray_filmdate d ON d.src_id=x.src_id "
                                 "WHERE x.state='check' AND d.src_id IS NULL ORDER BY x.planned_at DESC")]
    if not todo:
        return 0
    t0, n, got = time.time(), 0, 0
    work = tempfile.mkdtemp(prefix="s772_")
    os.chmod(work, 0o700)
    try:
        for r in todo[:MAX]:
            if time.time() - t0 > SECS:
                break
            data = helper("media", r["src_id"])
            if not data:
                continue                                 # not fetched (gone, or Drive busy): tried again next run
            p = os.path.join(work, "pic")
            with open(p, "wb") as fh:
                fh.write(data)
            try:
                text, secs, how = ocr_text(p, work)
            finally:
                try:
                    os.remove(p)
                except OSError:
                    pass
            first = str(r["file_time"] or r["day"] or "")[:10]
            try:
                hi = dt.date.fromisoformat(first)
            except ValueError:
                hi = dt.date.today()
            lo = hi - dt.timedelta(days=WINDOW)
            ds = sorted({d.isoformat() for d, _ in dates_in(text) if lo <= d <= hi})
            c.execute("INSERT OR REPLACE INTO xray_filmdate(src_id, dates, ids, how, secs, read_at) VALUES (?,?,?,?,?,?)",
                      (r["src_id"], json.dumps(ds), json.dumps(ids_in(text)[:6]), how, round(secs, 1), time.strftime("%Y-%m-%d %H:%M:%S")))
            c.commit()
            n += 1
            got += 1 if ds else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)
    say("read %d parked picture(s), a date on %d, %d left, %s, %.0fs" % (n, got, max(0, len(todo) - n), eng, time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
