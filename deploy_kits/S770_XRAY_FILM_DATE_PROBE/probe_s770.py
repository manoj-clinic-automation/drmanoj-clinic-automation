#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""probe_s770.py -- S770_XRAY_FILM_DATE_PROBE (session S422, 10-Nov-2026). READ-ONLY.

WHY. On 09-Nov evening 18 X-ray pictures, prepared afresh on the X-ray PC, were re-added for the October
'photo baaki' X-rays. A fresh copy carries no picture time, so the filing run dated every one by its file time
(09-Nov), found none of the IDs on 09-Nov's X-ray list and parked all 18 in the check folder. The owner: "X-rays
carry date of X-ray also". This probe measures, ON THE SERVER, how often the date can be read from the picture
itself -- (1) the picture's own metadata (EXIF / comment segments), (2) the text printed on the film (OCR) --
and scores it against already-filed X-rays whose day is known. Nothing leaves the server but counts and dates.

WHAT IT READS. finance.db read-only (mode=ro). Drive through records_drive.py (read-only scope). Each picture is
held in a private temp folder only while it is read, then deleted. It writes NOTHING to the database or Drive.
OUTPUT. <OUT>/report.txt and one mail to the clinic mailbox (the health report's own sender). No patient name,
no clinic ID, no Drive ID in either: pictures are numbered, the film's words are masked.
No patient data, no secret in this file (F-185).
"""
import datetime as dt
import json
import os
import re
import shutil
import smtplib
import sqlite3
import subprocess
import sys
import tempfile
import time
from email.mime.text import MIMEText

DB = os.environ.get("S770_DB", "/root/finance/finance.db")
HELPER = os.environ.get("S770_HELPER", "/root/finance/records_drive.py")
OUT = os.environ.get("S770_OUT", "/root/s770_probe")
ENV = os.environ.get("S770_ENV", "/root/wa/.env")
MAIL = os.environ.get("S770_MAIL", "1") == "1"
N_TRUTH = int(os.environ.get("S770_TRUTH", "25"))
REUP_FROM = "2026-11-09 19:00:00"          # the 09-Nov evening re-add was planned at 19:25 and 20:25
OCR_SECS = 90

MONTHS = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}
MON_RE = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC"
DATE_PATS = [
    ("dmy", re.compile(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?!\d)")),
    ("ymd", re.compile(r"(?<!\d)(\d{4})\s*[/.\-:]\s*(\d{1,2})\s*[/.\-:]\s*(\d{1,2})(?!\d)")),
    ("dMy", re.compile(r"(?<!\d)(\d{1,2})\s*[\-/ .,]?\s*(" + MON_RE + r")[A-Z]*\s*[\-/ .,]?\s*(\d{4}|\d{2})(?!\d)", re.I)),
    ("Mdy", re.compile(r"(?<![A-Z])(" + MON_RE + r")[A-Z]*\s*[\-/ .]?\s*(\d{1,2})\s*,?\s*(\d{4})(?!\d)", re.I)),
    ("ymd8", re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")),
]
LO, HI = dt.date(2025, 6, 1), dt.date(2026, 12, 31)


def say(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ dates in text
def _mk(y, m, d):
    try:
        y = int(y)
        if y < 100:
            y += 2000
        x = dt.date(y, int(m), int(d))
        return x if LO <= x <= HI else None
    except (ValueError, TypeError):
        return None


def dates_in(text):
    """[(date, how)] -- every plausible date in the text; dd/mm read first (India), mm/dd as a second reading."""
    out = []
    t = text or ""
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


# ------------------------------------------------------------------ the picture's own metadata
EXIF_DT = re.compile(rb"(20\d{2}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})")


def meta_dates(data):
    """[(date, where)] from the JPEG's own segments: EXIF date-times, the comment segment, other APPn text."""
    out = []
    if not data or data[:2] != b"\xff\xd8":
        return out
    i, n = 2, len(data)
    while i + 4 <= n:
        if data[i] != 0xFF:
            break
        mk = data[i + 1]
        if mk in (0xD9, 0xDA):                       # end of image / start of scan: no more headers
            break
        ln = int.from_bytes(data[i + 2:i + 4], "big")
        seg = data[i + 4:i + 2 + ln]
        where = "COM" if mk == 0xFE else ("APP%d" % (mk - 0xE0) if 0xE0 <= mk <= 0xEF else "")
        if where:
            if where == "APP1" and seg[:4] == b"Exif":
                for m in EXIF_DT.finditer(seg):
                    d = _mk(m.group(1), m.group(2), m.group(3))
                    if d:
                        out.append((d, "EXIF"))
            else:
                txt = seg.decode("latin-1", "replace")
                for d, how in dates_in(txt):
                    out.append((d, where + " text"))
        i += 2 + ln
    return out


# ------------------------------------------------------------------ the film's printed text
def have_pil():
    try:
        import PIL  # noqa: F401
        return True
    except Exception:                                 # noqa: BLE001
        return False


def ocr_text(path, work):
    """(text, seconds, how). The bands where the film's text is printed (top and bottom fifth, white on black,
    so inverted), then the whole picture if the bands give no date."""
    t0 = time.time()
    tess = shutil.which("tesseract")
    if not tess:
        return "", 0.0, "no tesseract"

    def run(p, psm="11"):
        try:
            r = subprocess.run([tess, p, "stdout", "--psm", psm], capture_output=True, timeout=OCR_SECS)
            return r.stdout.decode("utf-8", "replace")
        except Exception:                             # noqa: BLE001
            return ""
    texts = []
    if have_pil():
        from PIL import Image, ImageOps
        im = Image.open(path)
        im = ImageOps.exif_transpose(im).convert("L")
        w, h = im.size
        scale = 2600.0 / max(w, h) if max(w, h) > 2600 else 1.0
        if scale != 1.0:
            im = im.resize((int(w * scale), int(h * scale)))
            w, h = im.size
        for k, box in enumerate(((0, 0, w, int(h * 0.2)), (0, int(h * 0.8), w, h))):
            band = ImageOps.invert(im.crop(box))
            band = band.resize((band.size[0] * 2, band.size[1] * 2))
            bp = os.path.join(work, "band%d.png" % k)
            band.save(bp)
            texts.append(run(bp))
        how = "bands"
        if not any(dates_in(x) for x in texts):
            fp = os.path.join(work, "full.png")
            ImageOps.invert(im).save(fp)
            texts.append(run(fp))
            how = "bands+whole"
    else:
        texts.append(run(path))
        how = "whole (no Pillow)"
    return "\n".join(texts), time.time() - t0, how


# ------------------------------------------------------------------ the database (read-only)
def db():
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def setting(c, k):
    r = c.execute("SELECT value FROM record_setting WHERE key=?", (k,)).fetchone()
    return r["value"] if r else ""


def xray_days(c, cid):
    if not cid:
        return set()
    s = {r[0] for r in c.execute("SELECT DISTINCT s.day FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.clinic_id=? "
                                 "AND s.series='xp' AND s.state='ok' AND i.kind='xray'", (cid,))}
    s |= {r[0] for r in c.execute("SELECT DISTINCT business_date FROM clinic_day_line WHERE clinic_id=? AND section='xray'", (cid,))}
    return s


def filed_days(c, cid):
    return {r[0] for r in c.execute("SELECT DISTINCT day FROM record_file WHERE clinic_id=? AND kind='xray' AND state='ok'", (cid,))}


def names_of(c, cid):
    w = set()
    if not cid:
        return w
    for q in ("SELECT name FROM patient_ref WHERE clinic_id=?", "SELECT name_seen FROM slip WHERE clinic_id=?",
              "SELECT patient FROM clinic_day_line WHERE clinic_id=?"):
        try:
            for r in c.execute(q, (cid,)):
                w |= {x for x in re.findall(r"[A-Z]{3,}", (r[0] or "").upper())}
        except sqlite3.Error:
            pass
    return w


def day_patients(c, day):
    """{clinic ID: name words} of every X-ray patient of the day."""
    out = {}
    for r in c.execute("SELECT DISTINCT s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.day=? AND s.series='xp' "
                       "AND s.state='ok' AND i.kind='xray' AND s.clinic_id<>''", (day,)):
        out[r[0]] = names_of(c, r[0])
    for r in c.execute("SELECT DISTINCT clinic_id FROM clinic_day_line WHERE business_date=? AND section='xray' AND clinic_id<>''", (day,)):
        out.setdefault(r[0], names_of(c, r[0]))
    return out


IMG = re.compile(r"\.(jpe?g|png|bmp|tiff?|dcm)$", re.I)
NUM = re.compile(r"(?<!\d)(\d{1,8})(?!\d)")


def stem_words(name):
    s = IMG.sub("", name or "")
    return {x for x in re.findall(r"[A-Z]{3,}", NUM.sub(" ", s).upper())}


def file_id(name):
    nums = NUM.findall(IMG.sub("", name or ""))
    return nums[0] if len(nums) == 1 else ""


# ------------------------------------------------------------------ masking the film's words for the layout sample
ALLOW = {"AP", "PA", "ID", "LT", "RT", "KV", "MA", "MAS", "LAT", "AGE", "SEX", "DATE", "YRS", "YR", "DOB", "VIEW", "LATERAL", "OBLIQUE",
         "STANDING", "NAME", "STUDY", "TIME", "AM", "PM", "DR", "REF", "NO", "PID", "UHID", "EXAM", "ACC", "MRN", "MALE", "FEMALE"}


def keep_word(tok, secret_words):
    """A word shown as printed: a month name or a common film label, never a word of the patient's name."""
    u = tok.upper()
    if u in secret_words:
        return False
    return (u[:3] in MONTHS and len(u) <= 9) or u in ALLOW


def mask_line(line, secret_words, cid):
    """The film's line with every word of 3+ letters as 'a's (month names kept), every digit as 9 -- except
    the dates themselves, kept as printed so their format can be seen. The clinic ID becomes <ID>."""
    spans = []
    for _, rx in DATE_PATS:
        for m in rx.finditer(line):
            if dates_in(m.group(0)):
                spans.append((m.start(), m.end()))
    spans.sort()
    out, i = [], 0

    def scrub(p):
        if cid:
            p = p.replace(cid, "<ID>")
        p = re.sub(r"[A-Za-z]{2,}", lambda m: m.group(0) if keep_word(m.group(0), secret_words) else "a" * len(m.group(0)), p)
        return re.sub(r"\d", "9", p)
    for s0, e0 in spans:
        if s0 < i:
            continue
        out.append(scrub(line[i:s0]))
        out.append(line[s0:e0])
        i = e0
    out.append(scrub(line[i:]))
    return "".join(out).strip()


# ------------------------------------------------------------------ Drive
def helper(what, fid):
    r = subprocess.run([sys.executable, "-B", HELPER, what, fid], capture_output=True, timeout=180)
    if r.returncode != 0:
        return None
    return r.stdout


# ------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    os.chmod(OUT, 0o700)
    c = db()
    started = dt.datetime.now()
    lines, rows = [], []
    tools = "tesseract %s · Pillow %s" % ("yes" if shutil.which("tesseract") else "NO", "yes" if have_pil() else "NO")
    say("S770 probe:", tools)

    pics = []                                       # (group, drive id, file name, known day, clinic id, planned_at)
    cf = setting(c, "xray_check_id")
    lst = helper("list", cf) if cf else None
    listing = json.loads(lst.decode("utf-8")) if lst else []
    xf = {r["src_id"]: r for r in c.execute("SELECT * FROM xray_filing")}
    for f in listing:
        r = xf.get(f.get("id")) or {}
        g = "re-added 09-Nov" if (r and (r["planned_at"] or "") >= REUP_FROM) else "parked earlier"
        pics.append((g, f.get("id"), f.get("name") or "", "", (r["clinic_id"] if r else "") or file_id(f.get("name")),
                     (f.get("imageMediaMetadata") or {}).get("time", "")))
    for r in c.execute("SELECT drive_id, clinic_id, day, file_name FROM record_file WHERE kind='xray' AND state='ok' AND drive_id<>'' "
                       "AND source='xray_inbox' ORDER BY id DESC LIMIT ?", (N_TRUTH,)):
        pics.append(("filed (known day)", r["drive_id"], r["file_name"] or "", r["day"], r["clinic_id"], ""))
    say("pictures:", len(pics), "(check folder %d)" % len(listing))

    work = tempfile.mkdtemp(prefix="s770_")
    os.chmod(work, 0o700)
    sample = []
    try:
        for k, (g, did, name, known, cid, drive_time) in enumerate(pics, 1):
            rec = {"n": k, "g": g, "known": known, "has_id": bool(cid), "drive_time": bool(drive_time)}
            data = helper("media", did) if did else None
            if not data:
                rec["err"] = "could not fetch"
                rows.append(rec)
                continue
            p = os.path.join(work, "pic.jpg")
            with open(p, "wb") as fh:
                fh.write(data)
            rec["kb"] = len(data) // 1024
            md = meta_dates(data)
            rec["meta"] = sorted({(d.isoformat(), w) for d, w in md})
            text, secs, how = ocr_text(p, work)
            rec["secs"] = round(secs, 1)
            rec["how"] = how
            od = dates_in(text)
            rec["ocr"] = sorted({(d.isoformat(), f) for d, f in od})
            secret = names_of(c, cid) | stem_words(name)
            up = text.upper()
            rec["name_in"] = bool(secret and any(re.search(r"(?<![A-Z])%s(?![A-Z])" % re.escape(w), up) for w in secret))
            rec["id_in"] = bool(cid and re.search(r"(?<!\d)%s(?!\d)" % re.escape(cid), text))
            rec["chars"] = len(text.strip())
            # what the film's date would do for a check-folder picture
            if g != "filed (known day)":
                xd, fd = xray_days(c, cid), filed_days(c, cid)
                pend = xd - fd
                fdates = {d.isoformat() for d, _ in od} | {d for d, _ in rec["meta"]}
                rec["pend"] = len(pend)
                hit = sorted(fdates & pend)
                if cid and hit:
                    rec["would"] = "file: ID + film date = an X-ray day with no photo"
                elif cid and (fdates & fd):
                    rec["would"] = "already has a photo that day (copy?)"
                elif cid and len(pend) == 1 and not fdates:
                    rec["would"] = "file by the ID rule (no film date)"
                elif not cid and fdates:
                    m = []
                    sw = stem_words(name)
                    for d in sorted(fdates):
                        for pc, words in day_patients(c, d).items():
                            if sw and sw <= words:
                                m.append((d, pc))
                    rec["would"] = ("file by name on the film date" if len(m) == 1 else
                                    ("several name matches -- check" if m else "no name match on the film date -- check"))
                else:
                    rec["would"] = "stays for a person"
            else:
                got = {d for d, _ in rec["ocr"]} | {d for d, _ in rec["meta"]}
                rec["right"] = known in got
                rec["wrong_only"] = bool(got) and known not in got
                if len(sample) < 5 and text.strip():
                    sample.append((k, [mask_line(x, secret, cid) for x in text.splitlines() if x.strip()][:14]))
            rows.append(rec)
            say(k, g, "meta", len(rec["meta"]), "ocr", len(rec["ocr"]), rec.get("would") or rec.get("right"), "%.1fs" % secs)
            try:
                os.remove(p)
            except OSError:
                pass
    finally:
        shutil.rmtree(work, ignore_errors=True)

    # -------------------------------------------------------------- the report
    def cnt(g, f):
        return sum(1 for r in rows if r["g"] == g and f(r))
    L = lines.append
    L("S770 X-RAY FILM DATE PROBE -- read-only -- %s IST" % started.strftime("%d-%b-%Y %H:%M"))
    L("tools on the server: " + tools)
    L("")
    for g in ("filed (known day)", "re-added 09-Nov", "parked earlier"):
        n = cnt(g, lambda r: True)
        if not n:
            continue
        L("== %s: %d pictures" % (g, n))
        L("   fetched %d · date in the picture's metadata %d · date read from the film %d · ID on the film %d · name on the film %d"
          % (cnt(g, lambda r: "err" not in r), cnt(g, lambda r: r.get("meta")), cnt(g, lambda r: r.get("ocr")),
             cnt(g, lambda r: r.get("id_in")), cnt(g, lambda r: r.get("name_in"))))
        if g == "filed (known day)":
            L("   the known day found %d · only other dates found %d · nothing found %d"
              % (cnt(g, lambda r: r.get("right")), cnt(g, lambda r: r.get("wrong_only")),
                 cnt(g, lambda r: "err" not in r and not r.get("meta") and not r.get("ocr"))))
        else:
            ws = {}
            for r in rows:
                if r["g"] == g:
                    ws[r.get("would", r.get("err", "?"))] = ws.get(r.get("would", r.get("err", "?")), 0) + 1
            for k2, v in sorted(ws.items(), key=lambda x: -x[1]):
                L("   %3d  %s" % (v, k2))
        secs = [r["secs"] for r in rows if r["g"] == g and "secs" in r]
        if secs:
            L("   OCR seconds per picture: avg %.1f, max %.1f" % (sum(secs) / len(secs), max(secs)))
        L("")
    L("== per picture (no names, no IDs)")
    for r in rows:
        L("%3d %-18s kb=%-5s meta=%s ocr=%s known=%s right=%s would=%s id=%s name=%s chars=%s %s %ss"
          % (r["n"], r["g"], r.get("kb", "-"), [d for d in r.get("meta", [])][:3], [d for d in r.get("ocr", [])][:4],
             r["known"] or "-", r.get("right", "-"), r.get("would", "-"), "y" if r.get("id_in") else "n",
             "y" if r.get("name_in") else "n", r.get("chars", 0), r.get("how", r.get("err", "")), r.get("secs", "-")))
    L("")
    L("== the film's text, letters masked (a), digits as 9 except dates and month names -- filed samples")
    for k, ls in sample:
        L("-- picture %d" % k)
        for x in ls:
            L("   " + x)
    L("")
    L("took %.0f s · nothing written to the database or Drive" % (dt.datetime.now() - started).total_seconds())
    rep = "\n".join(lines)
    with open(os.path.join(OUT, "report.txt"), "w") as fh:
        fh.write(rep)
    os.chmod(os.path.join(OUT, "report.txt"), 0o600)
    say(rep)
    if MAIL:
        send("S770 X-ray film date probe -- report", rep)
    return 0


def send(subject, body):
    env = {}
    try:
        for raw in open(ENV):
            s = raw.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        say("mail: no .env -- the report is in", OUT)
        return
    user, pw = env.get("WATCHDOG_SMTP_USER", ""), env.get("WATCHDOG_SMTP_PASS", "")
    if not user or not pw:
        say("mail: no sender set up -- the report is in", OUT)
        return
    to = env.get("WATCHDOG_SMTP_TO", user)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    try:
        s = smtplib.SMTP(env.get("WATCHDOG_SMTP_HOST", "smtp.gmail.com"), int(env.get("WATCHDOG_SMTP_PORT", "587")), timeout=30)
        s.starttls()
        s.login(user, pw)
        s.sendmail(user, [x.strip() for x in to.split(",") if x.strip()], msg.as_string())
        s.quit()
        say("mail: sent")
    except Exception as ex:                          # noqa: BLE001
        say("mail: failed (%s) -- the report is in %s" % (type(ex).__name__, OUT))


if __name__ == "__main__":
    sys.exit(main())
