#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s465.py -- S465_PAPERS_JOIN (D664 slice 2): one purchase, one PDF; and the suggestions as the real papers taught them.

  usage: walk_s465.py --apply <apply_s465.py> --module <clinic_papers.py S465> --assetapp <folder holding the S464 app>

The asset app's CODE as S464 left it (asset_register.py, clinic_papers.py, scanner_widget.js) is copied to a scratch
folder four times: 'old' as it is, 'new' with this kit's module and its one edit, 'bare' with the edit but NO module
(the guard), 'half' with the edit and S464's module (the two files are placed one after the other). Each runs in a process of its own on an EMPTY database the app makes for itself, with made-up papers and
tiny made-up PDFs in a scratch uploads folder. The PDF merge is the box's own (shared/scan_checks_s441.py). The child
refuses to go on if the database or the uploads folder is not the scratch one; S441 is given no finance database; no
OCR is called. Nothing live is opened. Last line: WALK_S465 GREEN|RED.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

AR_FROM = "6dd5f3abb3aa1e9be801028fdd6e40d2"
AR_TO = "b0e0915e0b73a6ffb1f4a6e17aec8274"
CP_FROM = "46cfdf8c46e90f0a70ff544a2a304529"
MARK = "@@S465JSON@@ "
DASH = chr(0x2014)
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:500]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def squash(html):
    return re.sub(r"\s+", " ", html).strip()


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def tiny_pdf(words):
    """A one-page PDF, written by hand (the box's own python need not have a PDF library)."""
    stream = ("BT /F1 12 Tf 20 100 Td (%s) Tj ET" % words).encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out


def pages_in(path):
    with open(path, "rb") as fh:
        return len(re.findall(rb"/Type\s*/Page(?![s])", fh.read()))


# ============================================================================ the child
def child(mode):
    root = os.path.realpath(os.environ["S465_ROOT"]) + os.sep
    sys.path.insert(0, os.getcwd())
    import asset_register as A
    if not os.path.realpath(A.DB_PATH).startswith(root) or not os.path.realpath(A.UPLOAD_DIR).startswith(root):
        print(MARK + json.dumps({"abort": "the database or the uploads folder is not the scratch one"}))
        return
    out = {"mode": mode, "endpoints": sorted(k for k in A.app.view_functions if k.startswith("d664_")),
           "s441": A.S441 is not None}
    con = sqlite3.connect(A.DB_PATH)
    con.row_factory = sqlite3.Row
    cols = [r[1] for r in con.execute("PRAGMA table_info(bills)")]
    out["tables"] = sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE name LIKE 'd664%'"))
    up = A.UPLOAD_DIR
    os.makedirs(up, exist_ok=True)

    def bill(stamp, vendor, lane="clinic", status=None, no=None, total=None, date=None, items=(), pdf=None, ext="pdf",
             created="2026-10-02 06:00:00", ocr="read"):
        kind, st = A.LANES[lane][1], A.LANES[lane][2]
        stored = None
        if pdf is not None:
            stored = "bill_walk%s.%s" % (stamp.replace("-", "").lower(), ext)
            with open(os.path.join(up, stored), "wb") as fh:
                fh.write(tiny_pdf(pdf) if ext == "pdf" else b"\xff\xd8\xff\xe0 not a pdf: a made-up photo")
        con.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,created_at,stamp_no,status,lane,"
                    "ocr_status,source_stored,source_orig) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (kind, vendor, no, date, total, created, stamp, status or st, lane, ocr, stored, stored))
        bid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        for it in items:
            con.execute("INSERT INTO bill_items (bill_id,item_name) VALUES (?,?)", (bid, it))
        con.commit()
        return bid

    B = {}
    # the real papers of 03-Oct, by their words (made-up amounts)
    B["mannat"] = bill("B-9112", "MANNAT PHARMA", no="A000408", total=7535.0, date="2026-10-02", items=["TAB ORICOX-P", "TRAMATEE P TAB", "Q2-7 CAP"])
    B["yogendra"] = bill("B-9111", "YOGENDRA AGENCIES.", no="T018074", total=2651.0, date="2026-10-02", items=["NUCOXIA-P"])
    B["lk"] = bill("B-9110", "L.K. DRUG HOUSE", no="RT-490058", total=958.0, date="2026-10-02", items=["KETOTRAM TAB 1*10TAB"])
    B["stat"] = bill("B-9109", "VARIETY STATIONERS", no="2622", date="2026-10-01", items=["Regem 104 pen Ached"])
    B["aa_approved"] = bill("B-9108", "A.A. PHARMACEUTICALS", status="approved", no="0000440", total=1097.0, date="2026-10-01", items=["XYCAL-K2 TAB"])
    B["jugnu"] = bill("B-9114", "JUGNU MEDICOS (A Unit of SEEVEE HINDUSTHAN PVT.LTD.)", no="JM/26-27/1150", total=5929.0, date="2026-09-25", items=["DHL 8*10 150 SH"])
    B["yuv_garble"] = bill("B-9118", "YUVIKA SURGICALS", date="2026-09-29", items=['Gloster S"', "13cm x 4 mt Bandye"])
    B["light"] = bill("B-9115", "Krishna Sales Corporation", no="ELEC/26-27/1945", total=10907.0, date="2026-09-25", items=["GATE LIGHT FITTING NO PGL 024 MEDIUM"])
    B["implant"] = bill("B-9101", "Shri Ram Enterprisae", no="SRE/737", total=130003.0, date="2025-08-21", items=["J&J PINNACLE SECTOR II CUP 54MM", "J&J CORAIL AMT COLLARLES"])
    B["agar_inj"] = bill("B-9120", "Agarwal Surgicals", no="A-9", total=640.0, date="2026-10-02", items=["Lignocaine inj 2%", "Cotton roll"])
    # a purchase scanned as three papers: the bill, then two blank warranty cards
    B["head"] = bill("B-9205", "Jasoria Brothers", lane="owner_expense", no="26-27/A2753", total=28400.0, date="2026-10-01",
                     items=["BATTERY 200AH"], pdf="the bill")
    B["w1"] = bill("B-9206", "", pdf="warranty card one")
    B["w2"] = bill("B-9207", "", pdf="warranty card two")
    B["after"] = bill("B-9208", "City Stationers", no="5", total=480.0, date="2026-10-03", items=["A4 paper"], pdf="another bill")
    B["photo"] = bill("B-9209", "", pdf="x", ext="jpg")
    # the refusals
    B["pharm"] = bill("B-9300", "Yuvika Surgicals", lane="pharmacy", no="Y/11", total=7000.0, date="2026-10-02", items=["Knee cap"], pdf="pharmacy scan")
    B["pharm_blank"] = bill("B-9301", "", lane="pharmacy", pdf="pharmacy blank")
    B["nototal"] = bill("B-9400", "Some Shop", lane="owner_expense", no="77", date="2026-10-02", items=["Fan"], pdf="bill without its total")
    B["lastpage"] = bill("B-9401", "", lane="owner_expense", total=3300.0, pdf="the page with the total")
    out["B"] = B
    snap = lambda bid: dict(con.execute("SELECT lane, kind, status, source_stored, total_amount, reject_reason, approved_by"
                                        + (", page_of" if "page_of" in cols else "") + (", subgroup" if "subgroup" in cols else "")
                                        + " FROM bills WHERE id=?", (bid,)).fetchone())
    out["pharm_before"] = [snap(B["pharm"]), snap(B["pharm_blank"])]

    owner, manager, nobody, staff = (A.app.test_client() for _ in range(4))
    with owner.session_transaction() as s:
        s["uid"], s["epoch"] = 1, "1"
    with manager.session_transaction() as s:
        s["uid"], s["epoch"] = 3, "1"
    try:
        staff.set_cookie("clinic_sso", "wstaff|staff|1")
    except TypeError:
        staff.set_cookie("localhost", "clinic_sso", "wstaff|staff|1")

    def get(c, p):
        r = c.get(p)
        return [r.status_code, r.get_data(as_text=True), r.headers.get("Location") or ""]

    def post(c, p, data=None):
        r = c.post(p, data=data or {})
        return [r.status_code, r.headers.get("Location") or ""]

    def flashes(c):
        return re.findall(r"<div class=flash>(.*?)</div>", c.get("/papers").get_data(as_text=True), re.S)

    def cards(html):
        got = {}
        for m in re.finditer(r'<div class=d6card>(.*?)(?=<div class=d6card>|<p class=muted>Skip leaves)', html, re.S):
            st = re.search(r'>(B-\d+)</a>', m.group(1))
            if st:
                got[st.group(1)] = dict(text=text(m.group(1)),
                                        yes=re.findall(r'class="d6b yes" name=(\w+) value="?([a-z_0-9]+)"?>', m.group(1)),
                                        links=re.findall(r'<a class="d6b (?:yes|alt)" href="([^"]+)">([^<]+)</a>', m.group(1)))
        return got

    p0 = get(owner, "/papers")
    out["papers"] = [p0[0], cards(p0[1])]
    out["bill_exp"] = get(owner, "/bills/%d" % B["head"])
    out["bill_pharm"] = get(owner, "/bills/%d" % B["pharm"])
    out["bill_clinic"] = get(owner, "/bills/%d" % B["stat"])
    out["bills_page"] = get(owner, "/bills")
    out["healthz"] = get(nobody, "/healthz")[0]
    if "d664_join" not in out["endpoints"]:
        out["join_404"] = get(owner, "/papers/%d/join" % B["head"])[0] if out["endpoints"] else None
        if out["endpoints"]:
            import clinic_papers as CP
            with A.app.test_request_context("/"):
                db = A.get_db()
                S = lambda v, it, no=False, tot=False: CP.suggest(db, v, it, no, tot)
                out["unit"] = {"mannat": S("MANNAT PHARMA", "TAB ORICOX-P ; TRAMATEE P TAB ; Q2-7 CAP", True, True),
                               "jugnu": S("JUGNU MEDICOS", "DHL 8*10 150 SH", True, True),
                               "agar_slip": S("AGARWAL SURGICALS", "", False, False),
                               "yuv_garble": S("YUVIKA SURGICALS", 'Gloster S" ; 13cm x 4 mt Bandye', False, False)}
        print(MARK + json.dumps(out))
        return
    import clinic_papers as CP
    # ---- the suggestions, by the real papers' words
    with A.app.test_request_context("/"):
        db = A.get_db()
        S = lambda v, it, no=False, tot=False: CP.suggest(db, v, it, no, tot)
        out["unit"] = {
            "mannat": S("MANNAT PHARMA", "TAB ORICOX-P ; TRAMATEE P TAB ; Q2-7 CAP", True, True),
            "lk": S("L.K. DRUG HOUSE", "KETOTRAM TAB 1*10TAB", True, True),
            "aa": S("A.A. PHARMACEUTICALS", "XYCAL-K2 TAB", True, True),
            "yogendra": S("YOGENDRA AGENCIES.", "NUCOXIA-P", True, True),
            "jugnu": S("JUGNU MEDICOS (A Unit of SEEVEE HINDUSTHAN PVT.LTD.)", "DHL 8*10 150 SH", True, True),
            "yuv_garble": S("YUVIKA SURGICALS", 'Gloster S" ; 13cm x 4 mt Bandye', False, False),
            "yuv_garble2": S("YUVIKA SURGICALS", '" ) Obsteter 5"', False, False),
            "yuv_ortho": S("Yuvika Surgicals", "Knee cap pair ; Lumbar belt", True, True),
            "agar_inj": S("Agarwal Surgicals", "Lignocaine inj 2% ; Cotton roll", True, True),
            "agar_unknown": S("Agarwal Surgicals", "Item XZ-200", True, True),
            "agar_slip": S("AGARWAL SURGICALS", "", False, False),
            "agar_tabs": S("Agarwal Surgicals and Medicals", "TAB ABC ; CAP XYZ", True, True),
            "stat": S("VARIETY STATIONERS", "A4 Ream 75gsm", True, False),
            "battery": S("Jasoria Brothers", "BATTERY 225005SR (200AH) ADDO SP", True, True),
            "ups": S("B.L.Computers", "Ups Battery 12v9ah", True, True),
            "light": S("Krishna Sales Corporation", "GATE LIGHT FITTING NO PGL 024 MEDIUM ; ME CS SF 873 7W NW", True, True),
            "implant": S("Shri Ram Enterprisae", "J&J PINNACLE SECTOR II CUP 54MM ; J&J ALTREX +4 10 DEG 36*54 MM ; J&J CORAIL AMT COLLARLES", True, True),
            "plumbing": S("", "CPVC Solvent 50g ; CP Brass Nozzle Set ; Bib Cock", False, True),
            "pharma_no_items": S("MANNAT PHARMA", "", True, True),
            "film_11": S("X", "X-ray film 11x14 box", True, True),
        }
        CP.ensure(db)
    # ---- who may ask
    out["roles"] = {who: [get(c, "/papers/%d/join" % B["head"])[0], post(c, "/papers/%d/join" % B["head"], {"page": str(B["w1"])})[0],
                          post(c, "/papers/%d/unjoin" % B["head"])[0]] for who, c in (("nobody", nobody), ("staff", staff))}
    out["after_roles"] = [snap(B["head"]), snap(B["w1"])]
    # ---- the join page
    jp = get(owner, "/papers/%d/join" % B["head"])
    fold = jp[1].split("Other papers scanned near it", 1)
    out["join_page"] = [jp[0], text(jp[1]),
                        re.findall(r'<input type=checkbox name=page value="(\d+)"\s*(checked)?', jp[1]),
                        re.findall(r'<input type=checkbox name=page value="(\d+)"', fold[0]),
                        re.findall(r'<input type=checkbox name=page value="(\d+)"', fold[1]) if len(fold) == 2 else None]
    out["paper_blank0"] = get(owner, "/papers/%d" % B["w1"])[1]
    out["paper_mannat0"] = get(owner, "/papers/%d" % B["mannat"])[1]
    out["paper_light0"] = text(get(owner, "/papers/%d" % B["light"])[1])
    seen = p0[1] + jp[1] + out["paper_blank0"] + out["paper_mannat0"] + get(owner, "/papers/month")[1]
    out["ctrl"] = sorted({hex(ord(ch)) for ch in seen if ord(ch) < 32 and ch not in "\n\r\t"})
    head_file0 = snap(B["head"])["source_stored"]
    out["pages0"] = pages_in(os.path.join(up, head_file0))
    # ---- refusals first (nothing may change)
    ref = {}
    ref["no_tick"] = post(owner, "/papers/%d/join" % B["head"])
    ref["no_tick_flash"] = flashes(owner)
    ref["pharm_page"] = post(owner, "/papers/%d/join" % B["head"], {"page": str(B["pharm_blank"])})
    ref["pharm_page_flash"] = flashes(owner)
    ref["pharm_head"] = post(owner, "/papers/%d/join" % B["pharm"], {"page": str(B["w1"])})
    ref["pharm_head_flash"] = flashes(owner)
    ref["approved_page"] = post(owner, "/papers/%d/join" % B["head"], {"page": str(B["aa_approved"])})
    ref["approved_flash"] = flashes(owner)
    ref["unknown_also"] = post(owner, "/papers/%d/join" % B["head"], {"also": "B-0000"})
    ref["unknown_flash"] = flashes(owner)
    ref["self"] = post(owner, "/papers/%d/join" % B["head"], {"page": str(B["head"])})
    flashes(owner)
    ref["undo_nothing"] = post(owner, "/papers/%d/unjoin" % B["head"])
    ref["undo_nothing_flash"] = flashes(owner)
    ref["missing"] = [get(owner, "/papers/999999/join")[0], post(owner, "/papers/999999/unjoin")[0]]
    ref["state"] = [snap(B["head"]), snap(B["w1"]), snap(B["pharm"]), snap(B["pharm_blank"]), snap(B["aa_approved"]),
                    con.execute("SELECT COUNT(*) FROM d664_join").fetchone()[0]]
    out["ref"] = ref
    # ---- join the two warranty cards
    out["join"] = post(owner, "/papers/%d/join" % B["head"], {"page": [str(B["w1"]), str(B["w2"])], "back": "/papers"})
    out["join_flash"] = flashes(owner)
    h1 = snap(B["head"])
    out["head1"] = h1
    out["pages1"] = pages_in(os.path.join(up, h1["source_stored"]))
    out["w_after"] = [snap(B["w1"]), snap(B["w2"])]
    out["originals_on_disk"] = all(os.path.isfile(os.path.join(up, f)) for f in (head_file0, "bill_walkb9206.pdf", "bill_walkb9207.pdf"))
    out["rows1"] = [dict(r) for r in con.execute("SELECT batch, head_id, page_id, who, head_before, head_after, merged, page_status, undone_at FROM d664_join ORDER BY id")]
    out["audit1"] = {"head": [r[0] for r in con.execute("SELECT action FROM bill_audit WHERE bill_id=? AND action LIKE 'd664%'", (B["head"],))],
                     "page": [r[0] for r in con.execute("SELECT action FROM bill_audit WHERE bill_id=? AND action LIKE 'd664%'", (B["w1"],))]}
    out["papers1"] = cards(get(owner, "/papers")[1])
    out["bill_head1"] = text(get(owner, "/bills/%d" % B["head"])[1])
    out["bill_page1"] = text(get(owner, "/bills/%d" % B["w1"])[1])
    out["paper_head1"] = text(get(owner, "/papers/%d" % B["head"])[1])
    out["paper_page1"] = text(get(owner, "/papers/%d" % B["w1"])[1])
    out["rejoin_joined"] = post(owner, "/papers/%d/join" % B["after"], {"page": str(B["w1"])})
    out["rejoin_flash"] = flashes(owner)
    out["page_as_head"] = post(owner, "/papers/%d/join" % B["w1"], {"page": str(B["after"])})
    flashes(owner)
    # ---- undo
    out["undo"] = post(owner, "/papers/%d/unjoin" % B["head"], {"back": "/papers"})
    out["undo_flash"] = flashes(owner)
    out["head2"] = snap(B["head"])
    out["w_undone"] = [snap(B["w1"]), snap(B["w2"])]
    out["rows2_undone"] = con.execute("SELECT COUNT(*) FROM d664_join WHERE undone_at IS NOT NULL").fetchone()[0]
    out["undo_again"] = post(owner, "/papers/%d/unjoin" % B["head"])
    flashes(owner)
    # ---- two joins, one after the other; each undo takes back the last one only
    post(manager, "/papers/%d/join" % B["head"], {"page": str(B["w1"])})
    out["step_a"] = [pages_in(os.path.join(up, snap(B["head"])["source_stored"])), snap(B["w1"])["status"], snap(B["w2"])["status"]]
    post(manager, "/papers/%d/join" % B["head"], {"also": "9207"})
    out["step_b"] = [pages_in(os.path.join(up, snap(B["head"])["source_stored"])), snap(B["w2"])["status"], snap(B["w2"]).get("page_of")]
    post(owner, "/papers/%d/unjoin" % B["head"])
    out["step_c"] = [pages_in(os.path.join(up, snap(B["head"])["source_stored"])), snap(B["w1"])["status"], snap(B["w2"])["status"]]
    post(owner, "/papers/%d/unjoin" % B["head"])
    out["step_d"] = [snap(B["head"])["source_stored"] == head_file0, snap(B["w1"])["status"], snap(B["w2"])["status"]]
    flashes(owner)
    # ---- a photo is linked, not merged; and it comes back
    out["photo_join"] = post(owner, "/papers/%d/join" % B["head"], {"also": "b-9209"})
    out["photo_flash"] = flashes(owner)
    out["photo_state"] = [snap(B["head"])["source_stored"] == head_file0, snap(B["photo"])]
    post(owner, "/papers/%d/unjoin" % B["head"])
    out["photo_undone"] = snap(B["photo"])
    flashes(owner)
    # ---- the total on the last page
    post(owner, "/papers/%d/join" % B["nototal"], {"page": str(B["lastpage"])})
    out["total_joined"] = snap(B["nototal"])
    post(owner, "/papers/%d/unjoin" % B["nototal"])
    out["total_undone"] = snap(B["nototal"])
    flashes(owner)
    # ---- the file changed after the join: the undo refuses
    post(owner, "/papers/%d/join" % B["head"], {"page": str(B["w1"])})
    con.execute("UPDATE bills SET source_stored='bill_someone_else.pdf' WHERE id=?", (B["head"],))
    con.commit()
    out["undo_changed"] = post(owner, "/papers/%d/unjoin" % B["head"])
    out["undo_changed_flash"] = flashes(owner)
    out["undo_changed_state"] = [snap(B["w1"])["status"], con.execute("SELECT COUNT(*) FROM d664_join WHERE head_id=? AND undone_at IS NULL", (B["head"],)).fetchone()[0]]
    # ---- the medicine paper moves through the app's own door
    out["move_mannat"] = post(owner, "/bills/%d/lane" % B["mannat"], {"lane": "pharmacy", "back": "/papers"})
    out["mannat_after"] = snap(B["mannat"])
    # ---- S464 still stands
    out["set_group"] = post(owner, "/bills/%d/subgroup" % B["jugnu"], {"subgroup": "xray_small", "back": "/papers"})
    out["jugnu_after"] = snap(B["jugnu"])
    out["month"] = [get(owner, "/papers/month?ym=2026-09")[0], text(get(owner, "/papers/month?ym=2026-09")[1])]
    out["prefix"] = get(owner, "/scanapp/papers/%d/join" % B["nototal"])
    out["pharm_after"] = [snap(B["pharm"]), snap(B["pharm_blank"])]
    print(MARK + json.dumps(out))


# ============================================================================ the parent
def make(root, tag, src, apply_py, module):
    d = os.path.join(root, tag, "assetapp")
    os.makedirs(d)
    for f in ("asset_register.py", "scanner_widget.js", "clinic_papers.py"):
        shutil.copy2(os.path.join(src, f), d)
    if apply_py:
        p = subprocess.run([sys.executable, "-B", apply_py, os.path.join(d, "asset_register.py")], capture_output=True, text=True)
        if p.returncode:
            return d, p
    if module == "none":
        os.remove(os.path.join(d, "clinic_papers.py"))
    elif module:
        shutil.copy2(module, os.path.join(d, "clinic_papers.py"))
    return d, None


def run(root, tag, d):
    base = os.path.join(root, tag)
    portal = os.path.join(base, "portal")
    os.makedirs(portal)
    with open(os.path.join(portal, "clinic_sso.py"), "w") as fh:
        fh.write('COOKIE_NAME = "clinic_sso"\n'
                 'def verify_token(tok, secret, current_epoch=None):\n'
                 '    try:\n        u, r, e = tok.split("|")\n    except Exception:\n        return None\n'
                 '    return {"user": u, "role": r}\n')
    with open(os.path.join(portal, "portal_config.py"), "w") as fh:
        fh.write('CLINIC_SSO_SECRET = "the-walk-stub"\n')
    with open(os.path.join(portal, "clinic_users.json"), "w") as fh:
        fh.write('{"epoch": 1}\n')
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    e = dict(os.environ)
    e.update({"S465_ROOT": root, "ASSETS_DB": os.path.join(base, "assets.db"), "ASSETS_UPLOADS": os.path.join(base, "uploads"),
              "CLINIC_PORTAL_DIR": portal, "SARVAM_API_KEY": "", "SCANAPP_PREFIX": "/scanapp",
              "FINANCE_LOCAL_URL": "http://127.0.0.1:9", "FINANCE_DB_FOR_SCANS": os.path.join(base, "no_finance.db"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", tag], cwd=d, env=e,
                       capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--assetapp", required=True)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s465_walk_")
    try:
        walk(a, root)
    except Exception as ex:                                        # a walk that breaks is a RED walk, never a traceback
        check("the walk itself ran to its end", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print("  kept: %s" % root)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S465 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    src = os.path.abspath(a.assetapp)
    have = (md5(os.path.join(src, "asset_register.py")), md5(os.path.join(src, "clinic_papers.py")) if os.path.isfile(os.path.join(src, "clinic_papers.py")) else "absent")
    check("0.1 the asset app is as S464 left it (asset_register.py 6dd5f3ab, clinic_papers.py 46cfdf8c)", have == (AR_FROM, CP_FROM), have)
    if have != (AR_FROM, CP_FROM):
        return
    d_old, _ = make(root, "old", src, None, None)
    d_new, err = make(root, "new", src, a.apply, a.module)
    got = md5(os.path.join(d_new, "asset_register.py"))
    check("0.2 the one edit applies and gives the predicted bytes", err is None and got == AR_TO, got + (" " + err.stderr[-200:] if err else ""))
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(d_new, "asset_register.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(d_new, "asset_register.py")) == got)
    so = open(os.path.join(d_old, "asset_register.py"), encoding="utf-8").read().splitlines()
    sn = open(os.path.join(d_new, "asset_register.py"), encoding="utf-8").read().splitlines()
    ch = [(x, y) for x, y in zip(so, sn) if x != y]
    check("0.4 exactly one line of asset_register.py differs: S464's own line on the bill page",
          len(so) == len(sn) and len(ch) == 1 and "d664_group_label is defined" in ch[0][0] and "d664_group_label is defined" in ch[0][1], len(ch))
    d_bare, _ = make(root, "bare", src, a.apply, "none")
    d_half, _ = make(root, "half", src, a.apply, None)
    R = {}
    for tag, d in (("old", d_old), ("new", d_new), ("bare", d_bare), ("half", d_half)):
        p, R[tag] = run(root, tag, d)
        R[tag + "_err"] = p.stderr
        check("0.5 the %s app starts on a scratch database and answers" % tag,
              bool(R[tag]) and "abort" not in R[tag] and R[tag].get("healthz") == 200, (R[tag] or {}).get("abort") or p.stderr[-700:])
    if not all(R.get(k) and "B" in R[k] for k in ("old", "new", "bare", "half")):
        return
    o, n, b, hf = R["old"], R["new"], R["bare"], R["half"]
    B = n["B"]
    check("0.6 new: the two new addresses are mounted beside S464's four, and d664_join exists; the box's own S441 is loaded for the merge",
          n["endpoints"] == ["d664_join", "d664_month", "d664_paper", "d664_papers", "d664_set", "d664_unjoin"]
          and n["tables"] == ["d664_join"] and n["s441"], (n["endpoints"], n["tables"], n["s441"]))
    check("0.7 THE GUARD: with clinic_papers.py absent the edited app starts, says so, and its pages are the bare app's pages",
          b["endpoints"] == [] and "clinic_papers NOT mounted" in R["bare_err"] and b["bill_exp"][0] == 200
          and "join pages" not in b["bill_exp"][1] and "Clinic papers to sort" not in b["bills_page"][1])

    check("0.8 THE HALF-WAY STATE: the edited app with S464's module still opens every bill page -- the group shows, the join button does not",
          hf["endpoints"] == ["d664_month", "d664_paper", "d664_papers", "d664_set"] and hf["bill_clinic"][0] == 200
          and "<b>Group:</b>" in hf["bill_clinic"][1] and "join pages" not in hf["bill_clinic"][1]
          and hf["bill_exp"][0] == 200 and "join pages" not in hf["bill_exp"][1] and hf["bill_pharm"][0] == 200,
          (hf["endpoints"], hf["bill_clinic"][0], hf["bill_exp"][0]))
    if "d664_join" not in n["endpoints"]:
        return
    check("0.9 no stray control character on any new page (an escape in a template that python read as its own)", n["ctrl"] == [], n["ctrl"])
    # ---- 1 · the suggestions, as the real papers taught them
    u, uo = n["unit"], o["unit"]
    check("1.1 SHOWN on the old module: a medicine bill, the X-ray film bill ('DHL 8*10') and Yuvika's garbled slip got NO suggestion",
          uo["mannat"] is None and uo["jugnu"] is None and uo["yuv_garble"] is None, uo)
    check("1.2 new: medicine bills on the clinic lane are named a Pharmacy purchase (Mannat Pharma, L.K. Drug House, A.A. Pharmaceuticals)",
          all(u[k] and u[k]["kind"] == "lane" and u[k]["value"] == "pharmacy" for k in ("mannat", "lk", "aa")), [u["mannat"], u["lk"], u["aa"]])
    check("1.3 new: 'DHL 8*10 150 SH' is X-ray films, small film -- though the supplier is called Medicos",
          u["jugnu"] and u["jugnu"]["value"] == "xray_small", u["jugnu"])
    check("1.4 new: Yuvika's handwritten slips are Procedure room whatever garble was read off them",
          all(u[k] and u[k]["value"] == "procedure" and "handwritten" in u[k]["why"] for k in ("yuv_garble", "yuv_garble2")), u["yuv_garble"])
    check("1.4b SHOWN on the old module: Agarwal Surgicals' own slip got nothing (its name was matched as a whole word and never matched); new: Procedure room",
          uo["agar_slip"] is None and u["agar_slip"] and u["agar_slip"]["value"] == "procedure", (uo["agar_slip"], u["agar_slip"]))
    check("1.5 unchanged: Yuvika's printed knee caps and belts get no tap; Agarwal's lignocaine and cotton are Procedure room, not medicines",
          u["yuv_ortho"]["kind"] == "note" and u["agar_inj"]["value"] == "procedure", (u["yuv_ortho"], u["agar_inj"]))
    check("1.6 a procedure-room supplier's printed bill with unknown items: suggested, with 'look at the paper'; with tablets and capsules: a Pharmacy purchase",
          u["agar_unknown"]["value"] == "procedure" and "look at the paper" in u["agar_unknown"]["why"]
          and u["agar_tabs"]["value"] == "pharmacy", (u["agar_unknown"], u["agar_tabs"]))
    check("1.7 unchanged: stationery is Others; the two batteries are Dr MK expense; an 11x14 film keeps its size",
          u["stat"]["value"] == "others" and u["battery"]["value"] == "owner_expense" and u["ups"]["value"] == "owner_expense"
          and u["film_11"]["value"] == "xray_11x14")
    check("1.8 nothing is guessed where nothing is known: the gate light, the implants ('COLLARLES' is not a collar), the plumbing, "
          "Yogendra Agencies' one item, a pharma supplier with no item read",
          all(u[k] is None for k in ("light", "implant", "plumbing", "yogendra", "pharma_no_items")),
          {k: u[k] for k in ("light", "implant", "plumbing", "yogendra", "pharma_no_items")})
    c = n["papers"][1]
    check("1.9 on the list: Mannat Pharma's card offers the move to the pharmacy lane through the app's own door",
          c["B-9112"]["yes"] == [["lane", "pharmacy"]] and "Pharmacy purchase" in c["B-9112"]["text"], c["B-9112"])
    check("1.10 an APPROVED clinic bill of medicines gets no tap, and it says why", c["B-9108"]["yes"] == [] and "already approved" in c["B-9108"]["text"])
    check("1.11 the move itself is the app's: lane pharmacy, kind Pharmacy, status captured", n["move_mannat"] == [302, "/papers"]
          and [n["mannat_after"][k] for k in ("lane", "kind", "status")] == ["pharmacy", "Pharmacy", "captured"], n["mannat_after"])

    # ---- 2 · the list points a bill at its pages, and a blank scan at its bill
    check("2.1 SHOWN on the old module: the two blank scans after a bill say only 'No suggestion'",
          "No suggestion" in o["papers"][1]["B-9206"]["text"] and o["papers"][1]["B-9206"]["links"][0][1] == "Open it")
    check("2.2 new: a blank scan says which paper it was scanned after, and offers to join into it",
          all("It comes after B-9205" in c[k]["text"] and c[k]["links"][0][1] == "Join into B-9205"
              and ("/papers/%d/join" % B["head"]) in c[k]["links"][0][0] for k in ("B-9206", "B-9207")), c.get("B-9206"))
    check("2.3 a blank scan after ANOTHER bill is not offered to the first one (B-9209 follows B-9208)",
          "It comes after B-9208" in c["B-9209"]["text"] and "B-9205" not in c["B-9209"]["text"], c["B-9209"]["text"][:200])
    check("2.3b and from the bill's side: the stationery bill's card says the next scan had nothing read on it, and offers to join it",
          "The next scan" in c["B-9208"]["text"] and "B-9209" in c["B-9208"]["text"]
          and any(("/papers/%d/join" % B["after"]) in l[0] and l[1] == "Join B-9209 into this one" for l in c["B-9208"]["links"]), c["B-9208"])
    pb = n["paper_blank0"]
    check("2.3c the blank scan's OWN page points the right way: 'Join into B-9205', and it does not offer to take pages itself",
          "A page of another purchase?" in pb and ">Join into B-9205</a>" in pb and ("/papers/%d/join?tick=%d" % (B["head"], B["w1"])) in pb.replace("&amp;", "&")
          and "Join pages into this paper" not in pb and "open the scan" in pb)
    check("2.3d a medicine bill's own page offers the move right under the suggestion; a paper with no suggestion has no such button",
          n["paper_mannat0"].count('name=lane value="pharmacy">Move to Pharmacy purchase') == 1 and "Move to " not in n["paper_light0"],
          n["paper_mannat0"].count("Move to Pharmacy purchase"))
    check("2.4 a pharmacy scan is never offered as a page or as a bill to join into",
          "B-9301" not in c and "B-9300" not in c)

    # ---- 3 · who may ask
    check("3.1 with no login: sent to the login page; a scanning login: refused -- the page, the join and the undo",
          n["roles"]["nobody"] == [302, 302, 302] and n["roles"]["staff"] == [403, 403, 403], n["roles"])
    check("3.2 and their attempts changed nothing", n["after_roles"][0]["source_stored"] == "bill_walkb9205.pdf" and n["after_roles"][1]["status"] == "draft")

    # ---- 4 · the join page
    jp = n["join_page"]
    ticked = {int(i) for i, ck in jp[2] if ck}
    offered = {int(i) for i, _ck in jp[2]}
    check("4.1 the join page shows the bill ('This number stays for the whole purchase') and says how to undo",
          jp[0] == 200 and ("B-9205 %s the bill" % DASH) in jp[1] and "This number stays for the whole purchase" in jp[1]
          and "What joining does" in jp[1] and "open B-9205 and press" in jp[1])
    front, behind = {int(x) for x in jp[3]}, {int(x) for x in (jp[4] or [])}
    check("4.1b only the bill's own blank scans stand in the open; the next real bill and the scan that follows IT wait behind 'Other papers scanned near it'",
          front == {B["w1"], B["w2"]} and {B["after"], B["photo"]} <= behind and "comes after B-9208" in jp[1], (sorted(front), sorted(behind)))
    check("4.2 the two blank scans right after the bill come ticked; the next real bill and the photo after it are offered, not ticked",
          ticked == {B["w1"], B["w2"]} and B["after"] in offered and B["photo"] in offered, (sorted(ticked), sorted(offered)))
    check("4.3 a pharmacy scan, an approved bill and the bill itself are not offered",
          not ({B["pharm"], B["pharm_blank"], B["aa_approved"], B["head"]} & offered))

    # ---- 5 · what is refused, and that a refusal changes nothing
    r = n["ref"]
    check("5.1 no tick: asked to tick one", any("Tick at least one" in f for f in r["no_tick_flash"]), r["no_tick_flash"])
    check("5.2 a pharmacy scan as a page: refused", any("cannot be joined" in f for f in r["pharm_page_flash"]), r["pharm_page_flash"])
    check("5.3 a pharmacy scan as the bill: refused", any("cannot take pages" in f for f in r["pharm_head_flash"]), r["pharm_head_flash"])
    check("5.4 an approved bill as a page: refused", any("cannot be joined" in f for f in r["approved_flash"]))
    check("5.5 a number that is no paper: said so; a paper that is not there: 404", any("no paper numbered B-0000" in f for f in r["unknown_flash"])
          and r["missing"] == [404, 404], (r["unknown_flash"], r["missing"]))
    check("5.6 undo with nothing joined: said so", any("no join" in f for f in r["undo_nothing_flash"]))
    st = r["state"]
    check("5.7 after all seven refusals nothing has moved: the bill's file, the blank scan, both pharmacy scans, the approved bill; no join row",
          st[0]["source_stored"] == "bill_walkb9205.pdf" and st[1]["status"] == "draft" and st[1].get("page_of") is None
          and [st[2], st[3]] == n["pharm_before"] and st[4]["status"] == "approved" and st[5] == 0, st)

    # ---- 6 · the join
    check("6.1 the bill starts as one page", n["pages0"] == 1)
    check("6.2 joining the two cards: back to where the owner came from, and it says 'One PDF now'",
          n["join"] == [302, n["join"][1]] and "/papers/%d" % B["head"] in n["join"][1]
          and any("B-9206 and B-9207 are joined into B-9205. One PDF now." in f for f in n["join_flash"]), (n["join"], n["join_flash"]))
    h1 = n["head1"]
    check("6.3 the bill now points at a NEW file of three pages; its number, lane and status are as they were",
          h1["source_stored"] != "bill_walkb9205.pdf" and h1["source_stored"].startswith("bill_") and n["pages1"] == 3
          and [h1["lane"], h1["status"]] == ["owner_expense", "captured"], (h1, n["pages1"]))
    check("6.4 each card keeps its number and reads as a page of the bill (S441's own shape: rejected + page_of), with who joined it",
          all(w["status"] == "rejected" and w["page_of"] == B["head"] and w["reject_reason"] == "joined into B-9205"
              and w["approved_by"] for w in n["w_after"]), n["w_after"])
    check("6.5 all three original files are still on disk", n["originals_on_disk"] is True)
    rows = n["rows1"]
    check("6.6 what was joined is written down for the undo: two rows, one batch, each with the file before and after",
          len(rows) == 2 and rows[0]["batch"] == rows[1]["batch"] and rows[0]["head_before"] == "bill_walkb9205.pdf"
          and rows[1]["head_after"] == h1["source_stored"] and rows[0]["head_after"] == rows[1]["head_before"]
          and all(x["merged"] == 1 and x["page_status"] == "draft" and x["undone_at"] is None for x in rows), rows)
    check("6.7 and in the audit trail of the bill and of each page", n["audit1"] == {"head": ["d664_join"], "page": ["d664_joined_into"]}, n["audit1"])
    check("6.8 the joined pages have left the list to sort", "B-9206" not in n["papers1"] and "B-9207" not in n["papers1"])
    check("6.9 the app's own bill page shows it: the bill says 'pages joined', the card says 'a page of B-9205'",
          "pages joined: B-9206 B-9207" in n["bill_head1"] and "a page of B-9205" in n["bill_page1"], n["bill_head1"][:300])
    check("6.10 the paper's own page lists the joined pages and offers the undo; the page's page says it is a page of another",
          "Joined into this paper" in n["paper_head1"] and "B-9206" in n["paper_head1"] and "B-9207" in n["paper_head1"]
          and "Undo the last join (B-9206 and B-9207)" in n["paper_head1"] and "a page of another" in n["paper_page1"]
          and "open B-9205 and press" in n["paper_page1"],
          n["paper_head1"][-500:])
    check("6.11 a page already joined cannot be joined again elsewhere, and a page cannot take pages itself",
          any("cannot be joined" in f for f in n["rejoin_flash"]) and n["w_after"][0]["page_of"] == B["head"], n["rejoin_flash"])

    # ---- 7 · the undo
    check("7.1 undo: the bill has its own one-page file back; both cards are papers of their own again, as they were",
          n["head2"]["source_stored"] == "bill_walkb9205.pdf"
          and all(w["status"] == "draft" and w.get("page_of") is None and w["reject_reason"] is None and w["approved_by"] is None for w in n["w_undone"])
          and n["rows2_undone"] == 2 and any("Undone" in f for f in n["undo_flash"]), (n["head2"], n["w_undone"]))
    check("7.2 two joins one after the other make 2 then 3 pages (the second by typing just '9207'); each undo takes back only the last",
          n["step_a"] == [2, "rejected", "draft"] and n["step_b"] == [3, "rejected", B["head"]]
          and n["step_c"] == [2, "rejected", "draft"] and n["step_d"] == [True, "draft", "draft"],
          (n["step_a"], n["step_b"], n["step_c"], n["step_d"]))
    check("7.3 a photo (not a PDF) is linked to the bill but the file is left alone, and it says so; the undo frees it",
          n["photo_state"][0] is True and n["photo_state"][1]["status"] == "rejected" and n["photo_state"][1]["page_of"] == B["head"]
          and any("It is linked to it, but could not be put into one PDF" in f for f in n["photo_flash"]) and n["photo_undone"]["status"] == "draft", (n["photo_flash"], n["photo_state"]))
    check("7.4 a bill with no total takes the total from its last page; the undo takes it back",
          n["total_joined"]["total_amount"] == 3300.0 and n["total_undone"]["total_amount"] is None, (n["total_joined"], n["total_undone"]))
    check("7.5 if the bill's file was changed by something else after the join, the undo refuses and nothing moves",
          any("cannot be undone" in f for f in n["undo_changed_flash"]) and n["undo_changed_state"] == ["rejected", 1], n["undo_changed_flash"])

    # ---- 8 · what must not move
    check("8.1 THE PHARMACY SCANS ARE NOT TOUCHED: both exactly as they were", n["pharm_after"] == n["pharm_before"], n["pharm_after"])
    check("8.2 S464 still stands: a group is set in one tap; the month page counts the X-ray film paper",
          n["set_group"] == [302, "/papers"] and n["jugnu_after"]["subgroup"] == "xray_small" and n["month"][0] == 200
          and "X-ray films 1 paper" in n["month"][1], n["month"][1][:300])
    check("8.3 under /scanapp the join page opens and posts back under the prefix",
          n["prefix"][0] == 200 and 'action="/scanapp/papers/%d/join"' % B["nototal"] in n["prefix"][1])
    check("8.4 the bill page: 'join pages' on a Dr MK expense paper, group and join on a clinic paper, nothing on a pharmacy scan",
          ">join pages</a>" in n["bill_exp"][1] and "<b>Group:</b>" not in n["bill_exp"][1] and "<b>Group:</b>" in n["bill_clinic"][1]
          and ">choose</a>" in n["bill_clinic"][1] and ">join pages</a>" in n["bill_clinic"][1]
          and "join pages" not in n["bill_pharm"][1] and "join pages" not in o["bill_exp"][1])
    check("8.5 a pharmacy bill's page is byte for byte the old page", squash(n["bill_pharm"][1]) == squash(o["bill_pharm"][1]))
    check("8.6 nothing in the asset app's own folder was written by this walk",
          (md5(os.path.join(src, "asset_register.py")), md5(os.path.join(src, "clinic_papers.py"))) == (AR_FROM, CP_FROM))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        sys.exit(main())
