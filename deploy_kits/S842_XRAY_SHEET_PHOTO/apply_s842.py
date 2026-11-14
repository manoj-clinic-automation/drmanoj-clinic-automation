#!/usr/bin/python3
"""apply_s842.py -- kit S842_XRAY_SHEET_PHOTO (the parent, S467, 14-Nov-2026). Usage: apply_s842.py <in> <out>
Patches /root/finance/clinic_lists.py 92aca69e (read whole from the 14-Nov bundle) on exact anchors; each anchor once."""
import hashlib, sys
FROM = "92aca69e267c7c656cdd1621eea978f2"
src = open(sys.argv[1], "rb").read()
assert hashlib.md5(src).hexdigest() == FROM, "not the 92aca69e clinic_lists.py"
s = src.decode("utf-8")
def r(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

r("CLINICLISTS_NOW=<iso> pins the clock for the walk. No patient name, no number, no secret in this file (F-185).\n\"\"\"",
  "S842 (S467, 14-Nov-2026; D979 item 5): the X-rays tab carries a PHOTO column per patient and day -- Filed (opens the photo) /\n"
  "Being filed / Issue / Pending (with its due day) / Not due yet / X-ray not done -- read from Check karein's own states\n"
  "(check_screens.day_strip, S836; S834's due rule; a photo that day or the two after counts), never a copy of the rule; a 'Not\n"
  "filed only' switch (?nf=1) and the Excel follow the screen. If those states cannot be read the column shows '-' and nothing\n"
  "else changes. READ ONLY still (record_file and xray_filing are read through check_screens / one SELECT of record_file ids).\n"
  "CLINICLISTS_NOW=<iso> pins the clock for the walk. No patient name, no number, no secret in this file (F-185).\n\"\"\"")
r('VERSION = "S691-CLINIC-LISTS-1.1"', 'VERSION = "S842-CLINIC-LISTS-1.2"')
r('''# ============================================================================================ the request
def _args(today):''', '''# ============================================================================================ S842: the photo of each X-ray
PHOTO_WORD = {"filed": "Filed", "filing": "Being filed", "issue": "Issue", "pending": "Pending", "notdue": "Not due yet",
              "notdone": "X-ray not done", "answered": "Answered"}
PHOTO_COUNT = {"filed": "filed", "filing": "being filed", "issue": "issue", "pending": "pending", "notdue": "not due yet",
               "notdone": "X-ray not done", "answered": "answered"}
RECORDS_FILE = "/finance/records/file/%d"                           # records.open_file: the photo itself
XRAY_CHECK = "/finance/records/xray-check"                          # his X-ray check page (S836)


def photo_map(con, d0, d1, today):
    """S842: {(day, clinic ID): [state, record_file id, due]} for the X-ray days d0..d1 -- the states Check karein's date strip
    gives (check_screens.day_strip, S836), never a copy of S834's due rule. None when they cannot be read."""
    try:
        import check_screens as CS                                     # noqa: PLC0415 -- beside this app
        CS._rec()
        days = (today - _d(d0)).days + 1
        if days < 1:
            return {}
        strip = CS.day_strip(con, min(days, 3000))
        due = CS._xray_days(con, d0, d1)
    except Exception:                                                  # noqa: BLE001 -- the sheet as it was
        return None
    out = {}
    for sd in strip:
        if d0 <= sd["day"] <= d1:
            for r_ in sd["x"]["rows"]:
                out[(sd["day"], r_["cid"])] = [r_["st"], 0, str(due.get((sd["day"], r_["cid"])) or "")]
    want = {}
    for (day, cid), v in out.items():
        if v[0] == "filed":
            want.setdefault(cid, []).append(day)
    if want:
        hi = (_d(d1) + dt.timedelta(days=2)).isoformat()
        for f in con.execute("SELECT id, clinic_id, day FROM record_file WHERE kind='xray' AND state='ok' AND day>=? AND day<=? "
                             "ORDER BY day, id", (d0, hi)):
            for day in want.get(f["clinic_id"], ()):
                v = out[(day, f["clinic_id"])]
                if not v[1] and day <= f["day"] <= (_d(day) + dt.timedelta(days=2)).isoformat():
                    v[1] = int(f["id"])
    return out


def photo_tag(rows, pm):
    """Each X-ray row gets e['ph'] = [state, file id, due] of its patient and day, or None (no clinic ID, or pm unreadable)."""
    for e in rows:
        e["ph"] = (pm or {}).get((e["day"], e["cid"])) if e["cid"] else None
    return rows


def photo_counts(rows):
    """Per patient and day (not per line): {state: n}."""
    seen = {}
    for e in rows:
        if e.get("ph"):
            seen[(e["day"], e["cid"])] = e["ph"][0]
    c = {}
    for st in seen.values():
        c[st] = c.get(st, 0) + 1
    return c


def not_filed(e):
    """'Not filed only': a row whose patient-day has a state other than filed / X-ray not done (a row with no clinic ID has none)."""
    return bool(e.get("ph")) and e["ph"][0] not in ("filed", "notdone")


def photo_cell(e):
    ph = e.get("ph")
    if not ph:
        return "—"
    st, fid, due = ph
    if st == "filed":
        return ("<a href='%s' target='_blank' rel='noopener'>Filed&nbsp;&#8599;</a>" % (RECORDS_FILE % fid)) if fid else "Filed"
    if st == "pending":
        return "<span class='red'>Pending</span>%s" % ((" <span class='sm'>due %s</span>" % dm(due)) if due else "")
    if st == "issue":
        return "<a class='amb' href='%s'>Issue</a>" % XRAY_CHECK
    if st in ("notdue", "filing", "answered", "notdone"):
        return "<span class='sm'>%s</span>" % PHOTO_WORD[st]
    return _esc(PHOTO_WORD.get(st, st))


def photo_text(e):
    ph = e.get("ph")
    if not ph:
        return ""
    return PHOTO_WORD.get(ph[0], ph[0]) + ((" (due %s)" % dm(ph[2])) if ph[0] == "pending" and ph[2] else "")


# ============================================================================================ the request
def _args(today):''')
r('''    rows = rows_for(con, tab, d0.isoformat(), d1.isoformat(), q)
    s = summary(rows, tab)
    xr = tab == "xray"
    word = "X-ray" if xr else "procedure"
    keep = dict(q=q, f=request.args.get("f", "") if how == "range" else "", t=request.args.get("t", "") if how == "range" else "",
                m=ym if how == "month" else "")''', '''    rows = rows_for(con, tab, d0.isoformat(), d1.isoformat(), q)
    xr = tab == "xray"
    nf = xr and request.args.get("nf") == "1"                          # S842: 'Not filed only'
    pc, pm = {}, None
    if xr:
        pm = photo_map(con, d0.isoformat(), d1.isoformat(), today)
        photo_tag(rows, pm)
        pc = photo_counts(rows)
        if pm is None:
            nf = False                                                 # states unreadable: the switch does nothing
        if nf:
            rows = [e for e in rows if not_filed(e)]
    s = summary(rows, tab)
    word = "X-ray" if xr else "procedure"
    keep = dict(q=q, f=request.args.get("f", "") if how == "range" else "", t=request.args.get("t", "") if how == "range" else "",
                m=ym if how == "month" else "", nf="1" if nf else "")''')
r('''    out.append("<div class='card'><p class='mut'>%s · %d day%s%s</p><div class='sum'>%s</div></div>" % (
        head, s["days"], "" if s["days"] == 1 else "s", (" · " + " · ".join(extra)) if extra else "", "".join(tiles)))''',
  '''    photo = ""
    if xr:                                                             # S842: the photos, per patient and day
        nnf = sum(v for k, v in pc.items() if k not in ("filed", "notdone"))
        bits = ["<b>%d</b> %s" % (pc[k], PHOTO_COUNT[k]) for k in ("filed", "pending", "issue", "filing", "notdue", "notdone", "answered")
                if pc.get(k)]
        sw = dict(keep, nf="" if nf else "1")
        photo = "<p class='mut' style='margin-top:8px'>Photos: their states could not be read just now (the column shows —).</p>" if pm is None else (
            "<p class='mut' style='margin-top:8px'>Photos (per patient and day): %s %s</p>" % (
            " · ".join(bits) or "none yet",
            ("<a class='btn on' href='%s/xray?%s'>Show all</a>" % (BASE, _qs(**sw))) if nf else
            ("<a class='btn' href='%s/xray?%s'>Not filed only (%d)</a>" % (BASE, _qs(**sw), nnf))))
    out.append("<div class='card'><p class='mut'>%s · %d day%s%s</p><div class='sum'>%s</div>%s</div>" % (
        head, s["days"], "" if s["days"] == 1 else "s", (" · " + " · ".join(extra)) if extra else "", "".join(tiles), photo))''')
r('''    th = (["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Side", "Film", "Films", "Paid", "Amount"] if xr else''',
  '''    th = (["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Side", "Film", "Films", "Photo", "Paid", "Amount"] if xr else''')
r('''                          ("%d" % e["films"]) if not e["dz"] else "—"]''',
  '''                          ("%d" % e["films"]) if not e["dz"] else "—", photo_cell(e)]''')
r('''    empty = ("Nothing matches “%s”." % _esc(q)) if q else ("No %s in these days." % word)''',
  '''    empty = ("Nothing matches “%s”." % _esc(q)) if q else (("Every X-ray in these days has its photo filed." if nf else "No %s in these days." % word))''')
r('''    rows = rows_for(con, tab, d0.isoformat(), d1.isoformat(), q)
    xr = tab == "xray"
    data = []''', '''    rows = rows_for(con, tab, d0.isoformat(), d1.isoformat(), q)
    xr = tab == "xray"
    if xr:                                                             # S842: the photo column, and 'Not filed only' as on the screen
        pm = photo_map(con, d0.isoformat(), d1.isoformat(), today)
        photo_tag(rows, pm)
        if pm is not None and request.args.get("nf") == "1":
            rows = [e for e in rows if not_filed(e)]
    data = []''')
r('''            r += ["" if e["dz"] else SIZE_LABEL.get(e["size"], "size not set"), "" if e["dz"] else e["films"]]''',
  '''            r += ["" if e["dz"] else SIZE_LABEL.get(e["size"], "size not set"), "" if e["dz"] else e["films"], photo_text(e)]''')
r('''    head = (["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Side", "Film", "Films", "Paid", "Amount (Rs)", "Discount (Rs)"] if xr''',
  '''    head = (["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Side", "Film", "Films", "Photo", "Paid", "Amount (Rs)", "Discount (Rs)"] if xr''')
r('''    widths = [12, 9, 12, 28, 40, 6] + ([12, 7] if xr else [14]) + [16, 12, 12]''',
  '''    widths = [12, 9, 12, 28, 40, 6] + ([12, 7, 18] if xr else [14]) + [16, 12, 12]''')
r(".warn{margin:0 0 10px;", ".red{color:#9c2a20;font-weight:600}\n.warn{margin:0 0 10px;")
open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("applied:", hashlib.md5(s.encode("utf-8")).hexdigest())
