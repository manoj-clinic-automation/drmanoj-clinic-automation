"""
amir_salts.py -- the salt list as a sheet Amir can carry: download, fill, upload.

WHY IT EXISTS (the owner, 12-Sep-2026)

    "make the salt correction file in such a way that he downloads it and
     uploads it again so that he can copy the exact names from the spreadsheet
     you make available for him."

The point is the EXACT SPELLING.  A salt correction is worthless if the name is
retyped with a space in the wrong place -- that is what put METHYLPREDNISOLONE 8
and METHYL PREDNISOLONE 16 in different groups in the first place.  So the sheet
carries the exact string to copy, in its own column, and he copies FROM the sheet
INTO Marg.  He never types a name into the sheet.

What comes back is one letter per row: did he do it.  The tick is matched by the
row's ID, never by a name -- the name is the thing that was wrong.

It is the same download-fill-upload shape as the stock count pad he already used
on 06-Sep, written and read by the same two standard-library files that already
sit beside the finance app (padwriter.py, padreader.py), so nothing new has to be
installed on the server.

The ticks are written into `purchase_salt_task` -- the SAME table his existing
salts page ticks -- so the two can never disagree.
"""

import hashlib
import html
import io
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, Response

bp = Blueprint("amir_salts", __name__)

_db = None
_require = None
_unit = "medical"
_roles = ("maker", "checker", "viewer")

IST = timezone(timedelta(hours=5, minutes=30))

MAX_BYTES = 8 * 1024 * 1024          # the pad's cap, the closer precedent
EXT_MAGIC = {".xlsx": (b"PK\x03\x04",)}

# section key -> (what to do, in Hinglish, which column holds the exact string)
SECTIONS = {
    "rename":  ("Salt ka naam badliye",      "b"),
    "create":  ("Naya salt naam banaiye",    "a"),
    "change":  ("Item ka salt badliye",      "c"),
    "cleanup": ("Safai ka kaam",             "b"),
}
# 'waiting' is the doctor's to answer, never Amir's -- it rides along read-only.

YES = ("y", "yes", "ha", "haan", "han", "1", "ok", "done", "✓", "✔", "hogaya", "ho gaya")


def _now():
    return datetime.now(IST)


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _esc(v):
    return html.escape("" if v is None else str(v))


def _ensure(cx):
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_salt_upload(
        md5         TEXT PRIMARY KEY,
        filename    TEXT,
        bytes       INTEGER,
        uploaded_at TEXT,
        uploaded_by TEXT,
        ticked      INTEGER NOT NULL DEFAULT 0,
        already     INTEGER NOT NULL DEFAULT 0,
        unknown     INTEGER NOT NULL DEFAULT 0,
        blank       INTEGER NOT NULL DEFAULT 0
    )""")


def _has(cx, name):
    return cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                      (name,)).fetchone() is not None


# --------------------------------------------------------------------------
# what goes in the sheet
# --------------------------------------------------------------------------

def _open_tasks(cx):
    """Everything still to do, in the order the salts page shows it."""
    if not _has(cx, "purchase_salt_task"):
        return []
    rows = cx.execute(
        """SELECT id, section, seq, a, b, c, done
             FROM purchase_salt_task
            WHERE section IN ('rename','create','change','cleanup')
              AND COALESCE(done, 0) = 0
         ORDER BY CASE section WHEN 'rename' THEN 1 WHEN 'create' THEN 2
                               WHEN 'change' THEN 3 ELSE 4 END, seq, id"""
    ).fetchall()
    return [dict(r) for r in rows]


def _waiting(cx):
    if not _has(cx, "purchase_salt_task"):
        return []
    return [dict(r) for r in cx.execute(
        """SELECT id, a, b, c, answer FROM purchase_salt_task
            WHERE section='waiting' ORDER BY seq, id""").fetchall()]


def _new_items(cx):
    if not _has(cx, "purchase_new_item"):
        return []
    month = _now().strftime("%Y-%m") + "-01"
    return [dict(r) for r in cx.execute(
        """SELECT item, first_seen, supplier, packing FROM purchase_new_item
            WHERE first_seen >= ? ORDER BY first_seen, item""", (month,)).fetchall()]


def _exact(t):
    """The string he must copy, letter for letter."""
    which = SECTIONS.get(t.get("section"), (None, "b"))[1]
    return (t.get(which) or "").strip()


def _build_workbook(cx):
    import padwriter as PW                                   # noqa: PLC0415

    today = _now().strftime("%d-%m-%Y")
    tasks = _open_tasks(cx)
    waiting = _waiting(cx)
    newitems = _new_items(cx)

    # ---- tab 1: the work
    sh = PW.Sheet()
    sh.text(1, 0, "SALT KA KAAM -- AMIR", PW.TITLE)
    sh.text(2, 0, "Banaya: " + today + " · " + str(len(tasks)) + " kaam baaki", PW.NOTE)
    sh.text(3, 0, "Naam SHEET SE COPY kijiye aur Marg mein PASTE kijiye. "
                  "Sheet mein naam mat likhiye.", PW.NOTE)
    sh.text(4, 0, "Ho jaye to HO GAYA column mein Y likhiye. Phir yeh file "
                  "wapas upload kar dijiye.", PW.NOTE)

    hdr = ["ID", "KYA KARNA HAI", "KIS PAR", "ABHI KYA HAI",
           "YEH EXACT NAAM COPY KIJIYE", "HO GAYA (Y)", "REMARK"]
    HR = 6
    for c, h in enumerate(hdr):
        sh.text(HR, c, h, PW.HEADER)
    sh.widths = {0: 7, 1: 24, 2: 34, 3: 26, 4: 34, 5: 12, 6: 26}

    r = HR + 1
    for t in tasks:
        what = SECTIONS.get(t["section"], ("", "b"))[0]
        sh.num(r, 0, int(t["id"]), PW.BOLD)
        sh.text(r, 1, what)
        sh.text(r, 2, t.get("a") or "")
        sh.text(r, 3, t.get("b") if t["section"] == "change" else "")
        sh.text(r, 4, _exact(t), PW.BOLDBOX)
        sh.text(r, 5, "", PW.INPUT)
        sh.text(r, 6, "", PW.INPUT)
        r += 1
    sh.freeze = "A%d" % (HR + 1)
    if tasks:
        sh.filter = "A%d:G%d" % (HR, r - 1)
    sh.print_title_rows = (HR, HR)

    tabs = [("SALT KAAM", sh)]

    # ---- tab 2: the doctor's questions, read-only for him
    if waiting:
        w = PW.Sheet()
        w.text(1, 0, "DR SAHAB KE LIYE -- inka jawab doctor sahab denge", PW.TITLE)
        w.text(2, 0, "Yeh aapka kaam nahin hai. Sirf jaankari ke liye.", PW.NOTE)
        for c, h in enumerate(["ID", "ITEM", "MARG MEIN ABHI", "SAHI SALT"]):
            w.text(4, c, h, PW.HEADER)
        w.widths = {0: 7, 1: 34, 2: 26, 3: 26}
        rr = 5
        for t in waiting:
            w.num(rr, 0, int(t["id"]), PW.BOLD)
            w.text(rr, 1, t.get("a") or "")
            w.text(rr, 2, t.get("b") or "")
            w.text(rr, 3, t.get("answer") or "")
            rr += 1
        tabs.append(("DR SAHAB KE LIYE", w))

    # ---- tab 3: items bought for the first time this month
    if newitems:
        n = PW.Sheet()
        n.text(1, 0, "NAYE ITEM -- is mahine pehli baar aaye", PW.TITLE)
        for c, h in enumerate(["ITEM", "PEHLI BAAR", "SUPPLIER", "PACKING"]):
            n.text(3, c, h, PW.HEADER)
        n.widths = {0: 34, 1: 13, 2: 26, 3: 13}
        rr = 4
        for it in newitems:
            n.text(rr, 0, it.get("item") or "")
            n.text(rr, 1, (it.get("first_seen") or "")[:10])
            n.text(rr, 2, it.get("supplier") or "")
            n.text(rr, 3, it.get("packing") or "")
            rr += 1
        tabs.append(("NAYE ITEM", n))

    # ---- tab 4: how to use it
    h = PW.Sheet()
    h.text(1, 0, "KAISE ISTEMAAL KIJIYE", PW.TITLE)
    for i, line in enumerate([
        "1. SALT KAAM tab kholiye.",
        "2. 'YEH EXACT NAAM COPY KIJIYE' column se naam COPY kijiye.",
        "3. Marg mein PASTE kijiye -- khud mat likhiye, spelling galat ho jaati hai.",
        "4. Jo ho gaya uske saamne HO GAYA column mein Y likhiye.",
        "5. File SAVE kijiye aur usi page par wapas UPLOAD kijiye.",
        "6. ID column ko mat badliye aur na hi mitaiye -- usi se milan hota hai.",
        "7. Jo row aap khaali chhod denge wo agli baar phir aayegi. Kuch khota nahin.",
    ]):
        h.text(3 + i, 0, line)
    h.widths = {0: 92}
    tabs.append(("PADHIYE", h))

    return PW.workbook_bytes_multi(tabs), len(tasks)


# --------------------------------------------------------------------------
# what comes back
# --------------------------------------------------------------------------

def _cell(g, r, c):
    v = g.get((r, c))
    return "" if v is None else str(v).strip()


def _read_ticks(raw):
    """Find the SALT KAAM grid and pull (id, tick, remark) out of it.

    Returns (rows, error).  A formula is never trusted and a blank is blank --
    the two rules the pad reader earned.
    """
    import padreader as PR                                   # noqa: PLC0415

    try:
        allg = PR.grids(io.BytesIO(raw))
    except Exception as e:
        return [], "yeh file padhi nahin ja saki (%s)" % type(e).__name__
    if not allg:
        return [], "file mein koi sheet nahin mili"

    grid = None
    for name, g in allg:
        if name.strip().upper().startswith("SALT KAAM"):
            grid = g
            break
    if grid is None:
        grid = allg[0][1]

    # find the header row by looking for the ID + HO GAYA pair
    hr, cid, ctick, crem = None, None, None, None
    for (r, c), v in grid.items():
        t = str(v).strip().upper()
        if t == "ID":
            row = {cc: str(vv).strip().upper() for (rr, cc), vv in grid.items() if rr == r}
            for cc, vv in row.items():
                if vv.startswith("HO GAYA"):
                    ctick = cc
                if vv == "REMARK":
                    crem = cc
            if ctick is not None:
                hr, cid = r, c
                break
    if hr is None:
        return [], "SALT KAAM sheet mein ID / HO GAYA column nahin mila"

    out = []
    rows = sorted({r for (r, _c) in grid.keys() if r > hr})
    for r in rows:
        rawid = _cell(grid, r, cid)
        if not rawid:
            continue
        m = re.match(r"^(\d+)(\.0+)?$", rawid)
        if not m:
            continue
        tick = _cell(grid, r, ctick).lower()
        remark = _cell(grid, r, crem) if crem is not None else ""
        out.append({"id": int(m.group(1)), "tick": tick, "remark": remark, "row": r})
    return out, None


def _apply(cx, rows, user):
    ticked = already = unknown = blank = 0
    names = []
    for row in rows:
        if not row["tick"]:
            blank += 1
            continue
        if row["tick"] not in YES:
            blank += 1
            continue
        cur = cx.execute("SELECT id, a, b, c, section, COALESCE(done,0) AS done "
                         "FROM purchase_salt_task WHERE id=?", (row["id"],)).fetchone()
        if cur is None:
            unknown += 1
            continue
        if cur["done"]:
            already += 1
            continue
        cx.execute("UPDATE purchase_salt_task SET done=1, done_by=?, done_at=? WHERE id=?",
                   (user, _stamp(), row["id"]))
        ticked += 1
        if len(names) < 12:
            names.append(_exact(dict(cur)) or (cur["a"] or ""))
    return {"ticked": ticked, "already": already, "unknown": unknown,
            "blank": blank, "names": names}


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

_CSS = """
:root{--ink:#1b1b1b;--soft:#6b6b6b;--line:#e3e3e3;--ok:#137333;--warn:#8a6d00;
      --bad:#a50e0e;--bg:#fafafa;--accent:#12457a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:720px;margin:0 auto;padding:14px}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:17px;margin:0 0 10px}
p{margin:0 0 10px}
.sub{color:var(--soft);font-size:14px;margin:0 0 14px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 14px}
.btn{display:block;width:100%;padding:14px 18px;font-size:17px;font-weight:600;
     border-radius:10px;border:1px solid var(--accent);background:var(--accent);
     color:#fff;text-align:center;text-decoration:none;cursor:pointer;margin:0 0 10px}
.btn.plain{background:#fff;color:var(--accent)}
.good{color:var(--ok)} .bad{color:var(--bad)} .warn{color:var(--warn)}
.line{padding:9px 0;border-bottom:1px solid var(--line)} .line:last-child{border-bottom:0}
.big{font-size:17px;font-weight:600}
.note{background:#fff8e1;border:1px solid #f0e0a8;border-radius:10px;padding:12px;margin:0 0 14px}
input[type=file]{display:block;width:100%;padding:12px;border:1px dashed var(--line);
                 border-radius:10px;background:#fff;margin:0 0 10px;font-size:15px}
.foot{color:var(--soft);font-size:13px;margin:16px 0 0;text-align:center}
ol{margin:0 0 0 18px;padding:0} li{margin:0 0 6px}
"""


def _shell(title, body):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>%s"
            "</div></body></html>" % (_esc(title), _CSS, body))


def _denied():
    return _shell("Nahin khul saka",
                  "<div class=card><h2>Yeh page aapke liye nahin hai</h2>"
                  "<p>Apne login se kholiye, ya doctor sahab ko bataiye.</p></div>"), 403


def _page(cx, result=None):
    n = len(_open_tasks(cx))
    body = []
    if result:
        cls = "good" if result.get("ticked") else "warn"
        body.append("<div class=card><h2 class='%s'>File le li gayi</h2>" % cls)
        body.append("<div class=line><b>%d</b> kaam tick hue</div>" % result.get("ticked", 0))
        if result.get("already"):
            body.append("<div class=line>%d pehle se ho chuke the</div>" % result["already"])
        if result.get("blank"):
            body.append("<div class=line>%d khaali the -- wo agli baar phir aayenge</div>"
                        % result["blank"])
        if result.get("unknown"):
            body.append("<div class='line bad'>%d ID pehchani nahin gayi -- ID column badal "
                        "gaya tha</div>" % result["unknown"])
        if result.get("names"):
            body.append("<div class=line class=sub>%s</div>"
                        % _esc(", ".join(result["names"])))
        body.append("</div>")
    elif result is not None:
        pass

    if isinstance(result, dict) and result.get("error"):
        body.append("<div class=card><h2 class=bad>File nahin li ja saki</h2><p>%s</p></div>"
                    % _esc(result["error"]))

    body.append("<div class=card><h2>Salt ka kaam -- %d baaki</h2>"
                "<p>Sheet se naam <b>copy</b> kijiye, Marg mein <b>paste</b> kijiye. "
                "Khud mat likhiye.</p>"
                "<a class=btn href='/finance/amir/salts.xlsx'>Excel download kijiye</a>"
                "</div>" % n)

    body.append("<div class=card><h2>Bhar kar wapas dijiye</h2>"
                "<form method=post enctype='multipart/form-data'>"
                "<input type=file name=f accept='.xlsx' id='saltfile'>"
                "<button class=btn type=submit>Upload kijiye</button></form>"
                "<p class=sub>Wahi file, jismein aapne HO GAYA column mein Y likha hai.</p>"
                "</div>")

    body.append("<div class=note><b>Yaad rakhiye:</b><ol>"
                "<li>ID column mat badliye.</li>"
                "<li>Naam sheet mein mat likhiye -- sirf Y.</li>"
                "<li>Khaali chhoda hua kaam khota nahin, agli baar phir aayega.</li>"
                "</ol></div>")

    body.append("<p><a class='btn plain' href='/finance/amir'>Wapas apne kaam par</a></p>")
    return _shell("Salt ka kaam", "".join(body))


@bp.route("/finance/amir/salts", methods=["GET", "POST"])
def salts():
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    _ensure(cx)
    user = (u or {}).get("username") or (u or {}).get("user") or ""

    if request.method != "POST":
        return _page(cx)

    f = request.files.get("f")
    if f is None or not f.filename:
        return _page(cx, {"error": "koi file nahin chuni gayi"})
    raw = f.read()
    if not raw:
        return _page(cx, {"error": "file khaali hai"})
    if len(raw) > MAX_BYTES:
        return _page(cx, {"error": "file bahut badi hai (%.1f MB)" % (len(raw) / 1048576.0)})
    name = (f.filename or "").replace("\\", "/").split("/")[-1].lower()
    if not name.endswith(".xlsx"):
        return _page(cx, {"error": "sirf .xlsx file chalegi -- wahi file jo download ki thi"})
    if not raw.startswith(EXT_MAGIC[".xlsx"][0]):
        return _page(cx, {"error": "yeh sach mein Excel file nahin hai"})

    md5 = hashlib.md5(raw).hexdigest()
    seen = cx.execute("SELECT ticked, already, unknown, blank FROM amir_salt_upload WHERE md5=?",
                      (md5,)).fetchone()
    if seen is not None:
        d = dict(seen)
        d["names"] = []
        d["repeat"] = True
        return _page(cx, d)

    rows, err2 = _read_ticks(raw)
    if err2:
        return _page(cx, {"error": err2})

    res = _apply(cx, rows, user)
    cx.execute("""INSERT OR REPLACE INTO amir_salt_upload
                  (md5, filename, bytes, uploaded_at, uploaded_by, ticked, already, unknown, blank)
                  VALUES(?,?,?,?,?,?,?,?,?)""",
               (md5, name[:120], len(raw), _stamp(), user,
                res["ticked"], res["already"], res["unknown"], res["blank"]))
    cx.commit()
    return _page(cx, res)


@bp.route("/finance/amir/salts.xlsx")
def salts_xlsx():
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    _ensure(cx)
    try:
        data, n = _build_workbook(cx)
    except ImportError:
        return _shell("Abhi nahin",
                      "<div class=card><h2>Sheet abhi nahin ban saki</h2>"
                      "<p>padwriter.py finance app ke saath nahin hai. "
                      "Doctor sahab ko bataiye.</p></div>"), 503
    fn = "SALT_KAAM_%s.xlsx" % _now().strftime("%d-%m-%Y")
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="%s"' % fn,
                 "Cache-Control": "no-store"},
    )


def init(app, db_getter, require_fn, unit="medical",
         roles=("maker", "checker", "viewer"), url_prefix=""):
    global _db, _require, _unit, _roles
    _db, _require, _unit, _roles = db_getter, require_fn, unit, tuple(roles)
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp
