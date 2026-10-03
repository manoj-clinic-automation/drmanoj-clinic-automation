#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figure_s465.py -- READ-ONLY on the live system: the join, shown the box's REAL papers on a COPY of assets.db.

The installer copies /root/assetapp/assets.db into its scratch folder (sqlite's own backup, read-only on the live
file) and points the edited app at the COPY and at an EMPTY scratch uploads folder. This then
  * opens the list, the join page of a few papers and the month page as the owner, and counts what the list now says;
  * REHEARSES ONE REAL JOIN: it finds a scan with nothing read on it that sits right after a bill, COPIES those two
    scanned PDFs out of the live uploads folder into the scratch one, joins them there, counts the pages of the PDF
    that comes out, and undoes it. A hand-made test PDF is not a scanner's PDF; this is the scanner's own.
It prints counts and paper numbers only (no supplier, no amount), writes nothing outside the scratch folder, and the
installer removes the scratch folder afterwards. The live uploads folder is only ever read.
   usage: figure_s465.py <scratch assetapp folder>
   env:   S465_ROOT (the scratch root)  ASSETS_DB / ASSETS_UPLOADS (inside it)  S465_LIVE_UPLOADS (read only)
"""
import os
import shutil
import sqlite3
import subprocess
import sys

COUNT_SRC = "import sys\nfrom pypdf import PdfReader\nprint(len(PdfReader(sys.argv[1]).pages))\n"


def pages(path, merge_py):
    try:
        from pypdf import PdfReader
        return len(PdfReader(path).pages)
    except ImportError:
        pass
    except Exception:
        return None
    try:
        r = subprocess.run([merge_py, "-c", COUNT_SRC, path], capture_output=True, text=True, timeout=60)
        return int(r.stdout.strip()) if r.returncode == 0 else None
    except Exception:
        return None


def main():
    d = os.path.abspath(sys.argv[1])
    scratch = os.path.realpath(os.environ.get("S465_ROOT", "")) + os.sep
    live_up = os.environ.get("S465_LIVE_UPLOADS", "")
    os.chdir(d)
    sys.path.insert(0, d)
    import asset_register as A
    if not os.path.realpath(A.DB_PATH).startswith(scratch) or not os.path.realpath(A.UPLOAD_DIR).startswith(scratch):
        print("FIGURE_S465 REFUSED: the database or the uploads folder is not the scratch one")
        return 1
    if "d664_join" not in A.app.view_functions:
        print("FIGURE_S465 RED: the join did not mount on the box's own database")
        return 1
    import clinic_papers as CP
    merge_py = getattr(A.S441, "MERGE_PY", "/root/wa/venv/bin/python3") if A.S441 else ""
    con = sqlite3.connect(A.DB_PATH)
    con.row_factory = sqlite3.Row
    own = con.execute("SELECT id FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone()
    ep = con.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()
    if not own or not ep:
        print("FIGURE_S465 RED: no active owner login in the copy")
        return 1
    c = A.app.test_client()
    with c.session_transaction() as s:
        s["uid"], s["epoch"] = own["id"], ep["value"]
    bad = []
    r = c.get("/papers")
    if r.status_code != 200 or "Clinic papers to sort" not in r.get_data(as_text=True):
        bad.append("/papers %s" % r.status_code)
    r = c.get("/papers/month")
    if r.status_code != 200:
        bad.append("/papers/month %s" % r.status_code)
    with A.app.test_request_context("/"):
        db = A.get_db()
        if not CP._can_join(db):
            print("FIGURE_S465 RED: this database has no page_of column -- S441 is not as expected")
            return 1
        rows = db.execute("SELECT b.* FROM bills b WHERE " + CP._live(db) + " AND COALESCE(b.subgroup,'')='' ORDER BY b.id DESC").fetchall()
        tally, offers, pairs = {}, [], []
        for b in rows:
            p = CP._paper(db, b)
            k = ("no suggestion" if not p["s"] else p["s"].get("label") or
                 ("a note, no tap" if p["s"]["kind"] == "note" else "?")) if not p["reading"] else "still being read"
            if p["head"] is not None:
                k = "a page of another paper"
                offers.append("%s into %s" % (p["stamp"], p["head_stamp"]))
                pairs.append((p["head"]["id"], b["id"]))
            tally[k] = tally.get(k, 0) + 1
        heads = sorted({h for h, _ in pairs})
    for h in heads[:6]:
        r = c.get("/papers/%d/join" % h)
        if r.status_code != 200 or "This number stays" not in r.get_data(as_text=True):
            bad.append("/papers/%d/join %s" % (h, r.status_code))
    for b in rows[:6]:
        for pth in ("/papers/%d" % b["id"], "/bills/%d" % b["id"]):
            if c.get(pth).status_code != 200:
                bad.append(pth)
    if bad:
        print("FIGURE_S465 RED: " + "; ".join(bad[:6]))
        return 1

    # ---- one real join, on the copy, with the scanner's own PDFs
    said = "no scan with nothing read on it sits beside a bill today, so there was no real pair to rehearse on"
    for h, pg in pairs:
        hb = con.execute("SELECT stamp_no, source_stored, status FROM bills WHERE id=?", (h,)).fetchone()
        pb = con.execute("SELECT stamp_no, source_stored, status FROM bills WHERE id=?", (pg,)).fetchone()
        fs = [hb["source_stored"] or "", pb["source_stored"] or ""]
        if not live_up or not all(f.lower().endswith(".pdf") and os.path.isfile(os.path.join(live_up, f)) for f in fs):
            said = "the pairs found are not two PDFs on disk (a photo, or the file is not in %s), so no real merge was rehearsed" % (live_up or "the uploads folder")
            continue
        os.makedirs(A.UPLOAD_DIR, exist_ok=True)
        for f in fs:
            shutil.copy2(os.path.join(live_up, f), os.path.join(A.UPLOAD_DIR, f))
        n0 = [pages(os.path.join(A.UPLOAD_DIR, f), merge_py) for f in fs]
        r = c.post("/papers/%d/join" % h, data={"page": str(pg)})
        now = con.execute("SELECT source_stored FROM bills WHERE id=?", (h,)).fetchone()[0]
        pnow = con.execute("SELECT status, page_of FROM bills WHERE id=?", (pg,)).fetchone()
        out = os.path.join(A.UPLOAD_DIR, now or "")
        n1 = pages(out, merge_py) if now and now != fs[0] and os.path.isfile(out) else None
        if r.status_code != 302 or now == fs[0] or n1 is None or None in n0 or n1 != n0[0] + n0[1] or pnow["status"] != "rejected" or pnow["page_of"] != h:
            print("FIGURE_S465 RED: the real join of %s into %s did not make one PDF (pages %s + %s -> %s; http %s)"
                  % (pb["stamp_no"], hb["stamp_no"], n0[0], n0[1], n1, r.status_code))
            return 1
        r = c.post("/papers/%d/unjoin" % h)
        back = con.execute("SELECT source_stored FROM bills WHERE id=?", (h,)).fetchone()[0]
        pback = con.execute("SELECT status, page_of FROM bills WHERE id=?", (pg,)).fetchone()
        if back != fs[0] or pback["status"] != pb["status"] or pback["page_of"] is not None:
            print("FIGURE_S465 RED: the undo of the real join did not put %s and %s back" % (hb["stamp_no"], pb["stamp_no"]))
            return 1
        said = ("ONE REAL JOIN REHEARSED on the copy: %s (%d page%s) + %s (%d) made one PDF of %d, and the undo put both back"
                % (hb["stamp_no"], n0[0], "" if n0[0] == 1 else "s", pb["stamp_no"], n0[1], n1))
        break
    print("FIGURE_S465 OK: on a copy of the box's own database every page opens. Clinic papers waiting: %d -- %s. "
          "Offered as a page of another: %s. %s."
          % (len(rows), ", ".join("%s %d" % (k, v) for k, v in sorted(tally.items(), key=lambda x: -x[1])) or "none",
             "; ".join(offers[:12]) or "none", said))
    return 0


if __name__ == "__main__":
    sys.exit(main())
