#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s618.py -- kit S618_SCAN_QUALITY (22-Oct-2026): the anchored builder. Reads the LIVE files, checks each FROM pin, applies each edit
at an anchor that must occur EXACTLY ONCE (else it stops and writes nothing), and writes the built files into --out:

    python3 -B make_s618.py --assetapp /root/assetapp --finance /root/finance --out <dir> [--kit <this folder>]

    <out>/asset_register.py  <out>/scanner_widget.js  <out>/claude_reader.py      (the Scan App, /root/assetapp)
    <out>/porders_s454.py    <out>/order_sheet.py                                 (the finance app, /root/finance)
    <out>/scan_quality.py                                                         (new: /root/shared/scan_quality.py, this kit's own file)

The blocks inserted are this kit's own files (s618_*_block.txt), byte for byte. No file outside --out is written."""
import argparse
import hashlib
import os
import sys

FROM = {"asset_register.py": "f29ee51561ef73b837a25e56651108ac", "scanner_widget.js": "10a8bb296944542278a06827c4d09c18",
        "claude_reader.py": "3894dc2358abd875ee61ced7619e1e1b",
        "porders_s454.py": "34bab4648940f30d7fc57188398c51b4", "order_sheet.py": "c7fe2561b22158f9dffa73b8c963e298"}   # the last two: S613's TO
HOME = {"asset_register.py": "assetapp", "scanner_widget.js": "assetapp", "claude_reader.py": "assetapp",
        "porders_s454.py": "finance", "order_sheet.py": "finance"}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def block(kit, name):
    with open(os.path.join(kit, name), "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def edits(kit):
    """[(file, anchor, new_text_for_the_anchor, what)] -- each anchor once in the live file."""
    E = []
    # ------------------------------------------------------------------------------------------------ claude_reader.py
    E.append(("claude_reader.py",
              'VERSION = "S550.2"\n',
              'VERSION = "S550.2"   # S618: + check_scan / lie_pass (how each page lies; upright on the server) -- read() is unchanged\n',
              "claude_reader: the version line names S618"))
    E.append(("claude_reader.py",
              "# ---------------------------------------------------------------------------------------------- the installer's live test\n",
              block(kit, "s618_reader_block.txt") + "# ---------------------------------------------------------------------------------------------- the installer's live test\n",
              "claude_reader: check_scan, turn_file, lie_pass, LIE_DDL (before the installer's live test)"))
    # ------------------------------------------------------------------------------------------------ asset_register.py
    E.append(("asset_register.py",
              '        ("pe_who",        "ALTER TABLE bills ADD COLUMN pe_who TEXT"),             # S544 (D719): a personal expense\'s person; NULL = Dr MK\n',
              '        ("pe_who",        "ALTER TABLE bills ADD COLUMN pe_who TEXT"),             # S544 (D719): a personal expense\'s person; NULL = Dr MK\n'
              '        ("rescan_of",     "ALTER TABLE bills ADD COLUMN rescan_of INTEGER"),       # S618: this scan is the rescan of that bill (its old scan set aside)\n',
              "asset_register: bills.rescan_of in init_db's guarded column list"))
    E.append(("asset_register.py",
              '    db.execute("CREATE TABLE IF NOT EXISTS bill_audit(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, at TEXT NOT NULL, "\n'
              '               "who TEXT, action TEXT NOT NULL, detail TEXT)")\n',
              '    db.execute("CREATE TABLE IF NOT EXISTS bill_audit(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, at TEXT NOT NULL, "\n'
              '               "who TEXT, action TEXT NOT NULL, detail TEXT)")\n'
              '    db.execute(S618_LIE_DDL)                                 # S618: how each page of a pharmacy scan lies (claude_reader.lie_pass)\n',
              "asset_register: table scan_lie by CREATE TABLE IF NOT EXISTS in init_db"))
    E.append(("asset_register.py",
              "def migrate(db):\n",
              "S618_LIE_DDL = (\"CREATE TABLE IF NOT EXISTS scan_lie(bill_id INTEGER NOT NULL, file TEXT NOT NULL, at TEXT, model TEXT, pages_json TEXT, \"   # S618: before\n"
              "                \"whole_bill INTEGER, totals_visible INTEGER, legible INTEGER, note TEXT, blur_kept INTEGER, rotated_to TEXT, PRIMARY KEY(bill_id, file))\")   # init_db runs at import\n"
              "\n\ndef migrate(db):\n",
              "asset_register: S618_LIE_DDL defined before migrate (init_db runs at import)"))
    E.append(("asset_register.py",
              'INTAKE_PREFILL = ("lane", "vendor", "bill_no", "bill_date", "amount", "bill_month")    # S435: + the confirmed month\n',
              'INTAKE_PREFILL = ("lane", "vendor", "bill_no", "bill_date", "amount", "bill_month", "rescan_of")    # S435: + the confirmed month; S618: + rescan_of (cleared after the first Save)\n',
              "asset_register: rescan_of rides the intake link (INTAKE_PREFILL)"))
    E.append(("asset_register.py",
              '    scan_cfg["uploadFields"].setdefault("lane", _lane_default)\n',
              '    scan_cfg["uploadFields"].setdefault("lane", _lane_default)\n'
              '    if scan_cfg["uploadFields"].get("lane") == "pharmacy":                   # S618: the half-A4 prior from the start on a pharmacy link\n'
              '        scan_cfg["expectAspect"] = 0.7048                                     # (the widget reads CFG at call time: the lane buttons still change it)\n'
              '        scan_cfg["expectLabel"] = "half-A4 bill"\n'
              '    if scan_cfg.get("cvScan"):                                                 # S618: the phone stops a badly blurred photo (OpenCV path only)\n'
              '        scan_cfg["blurMin"] = _s618_blur_min()\n',
              "asset_register: intake -- expectAspect on a pharmacy link, blurMin in SCANNER_CONFIG"))
    E.append(("asset_register.py",
              "['camsave','savebtn'].forEach(function(id){var e=document.getElementById(id);if(e){e.addEventListener('click',function(){setTimeout(function(){_challanSet(false);},0);});}});",
              "['camsave','savebtn'].forEach(function(id){var e=document.getElementById(id);if(e){e.addEventListener('click',function(){setTimeout(function(){_challanSet(false);if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){delete window.SCANNER_CONFIG.uploadFields.rescan_of;}},0);});}});"
              "\n(function(){var d=document.getElementById('directfile');if(d){d.addEventListener('change',function(){setTimeout(function(){if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){delete window.SCANNER_CONFIG.uploadFields.rescan_of;}},0);});}})();"
              "   /* S618: rescan_of rides the FIRST Save only (the widget keeps its own copy of the fields), as S531's challan -- the next bill is a plain scan */",
              "asset_register: intake page -- rescan_of cleared after the first Save (and after a PDF / file)"))
    E.append(("asset_register.py",
              "    try:                                                     # S441: who is scanning (the shared login's chosen name)\n"
              "        db.execute(\"UPDATE bills SET scanned_by=? WHERE id=?\", (_scanned_by_s441(), bid))\n",
              "    _s618_rescan(db, bid, stamp, _lane, pf.get(\"rescan_of\"))           # S618: the old scan set aside in THIS transaction, before the fingerprint guard\n"
              "    if (request.form.get(\"blur_kept\") or \"\") == \"1\":                         # S618: the phone kept a blurred photo after two refusals\n"
              "        _s618_blur_kept(db, bid, stored)\n"
              "    try:                                                     # S441: who is scanning (the shared login's chosen name)\n"
              "        db.execute(\"UPDATE bills SET scanned_by=? WHERE id=?\", (_scanned_by_s441(), bid))\n",
              "asset_register: _create_intake_bill -- the rescan and blur_kept before the first commit"))
    E.append(("asset_register.py",
              "# --- S601 end ---\n",
              "# --- S601 end ---\n" + block(kit, "s618_ar_block.txt"),
              "asset_register: the S618 block (blur min, the rescan, blur_kept, _s618_lie, the _bg_extract wrapper)"))
    # ------------------------------------------------------------------------------------------------ scanner_widget.js
    E.append(("scanner_widget.js",
              "  function arOK(w, h){\n    if (!wantAR || w <= 0 || h <= 0) return true;      // no prior -> judge nothing\n",
              "  function arOK(w, h){\n    var wantAR = parseFloat(CFG.expectAspect) || 0, wantTol = parseFloat(CFG.expectTol) || 0.15;   // S618: CFG read at call time\n"
              "    if (!wantAR || w <= 0 || h <= 0) return true;      // no prior -> judge nothing\n",
              "widget: arOK reads CFG at call time"))
    E.append(("scanner_widget.js",
              "  function guideRect(W, H){\n    if (!wantAR) return null;\n",
              "  function guideRect(W, H){\n    var wantAR = parseFloat(CFG.expectAspect) || 0;                    // S618: CFG read at call time\n"
              "    if (!wantAR) return null;\n",
              "widget: guideRect reads CFG at call time"))
    E.append(("scanner_widget.js",
              "      x.onclick = function(){ pages.splice(i,1); retakeIdx = -1; if (cvScanOn) dropSrc(i);                           // S523\n",
              "      x.onclick = function(){ pages.splice(i,1); retakeIdx = -1; if (cvScanOn) dropSrc(i);                           // S523\n"
              "        blurS618 = {slot: null, n: 0}; if (blurKeptS618 === i) blurKeptS618 = -1; else if (blurKeptS618 > i) blurKeptS618--;   // S618\n",
              "widget: a deleted page resets the blur count (and moves the kept-blurred mark)"))
    E.append(("scanner_widget.js",
              "    upq.unshift(it); renderStamps();\n    pagesToBlob(list,",
              "    if (blurKeptS618 >= 0 && blurKeptS618 < list.length) it.fields.blur_kept = \"1\";      // S618: a page kept after two blur refusals\n"
              "    blurKeptS618 = -1; blurS618 = {slot: null, n: 0}; blurBoxS618(false);\n"
              "    upq.unshift(it); renderStamps();\n    pagesToBlob(list,",
              "widget: enqueue -- blur_kept=1 with the upload; Save resets the count"))
    E.append(("scanner_widget.js",
              "  function autoAddCV(src){\n",
              block(kit, "s618_widget_block.txt") + "  function autoAddCV(src){\n",
              "widget: the S618 block (sharpness, the refusal box, the hook)"))
    E.append(("scanner_widget.js",
              "      try { du = cvUpright(cvWarp(full, q, $(\"bw\").checked)).toDataURL(\"image/jpeg\", 0.88); }     // S545: a sideways bill turned upright\n"
              "      catch (e) { autoAdd(full.toDataURL(\"image/jpeg\", 0.92)); return; }\n",
              "      var pgS618 = null;\n"
              "      try { pgS618 = cvUpright(cvWarp(full, q, $(\"bw\").checked)); du = pgS618.toDataURL(\"image/jpeg\", 0.88); }     // S545: a sideways bill turned upright\n"
              "      catch (e) { autoAdd(full.toDataURL(\"image/jpeg\", 0.92)); return; }\n"
              "      if (blurRefuseS618(pgS618)) return;                                               // S618: a badly blurred photo is not added\n",
              "widget: autoAddCV's go() -- the sharpness of the page as it will be saved"))
    E.append(("scanner_widget.js",
              "      say(\"Page \" + n + \" ✓\" + (whole ? \" (poori photo — Adjust se kaato)\" : \"\"));\n",
              "      if (blurForceS618) { blurKeptS618 = n - 1; blurForceS618 = false; } else if (blurKeptS618 === n - 1) { blurKeptS618 = -1; }   // S618\n"
              "      say(\"Page \" + n + \" ✓\" + (whole ? \" (poori photo — Adjust se kaato)\" : \"\"));\n",
              "widget: go() -- the third (kept) blurred photo is marked; a sharp retake clears the mark"))
    # ------------------------------------------------------------------------------------------------ order_sheet.py
    E.append(("order_sheet.py",
              "    \"CHECK (answer IN ('yes','no','remove')), item TEXT NOT NULL, qty INTEGER, short_at_answer INTEGER)\",      # S605 (D749): never updated, never deleted\n)\n",
              "    \"CHECK (answer IN ('yes','no','remove')), item TEXT NOT NULL, qty INTEGER, short_at_answer INTEGER)\",      # S605 (D749): never updated, never deleted\n"
              "    \"CREATE TABLE IF NOT EXISTS scan_rescan_ask (id INTEGER PRIMARY KEY, asset_bill_id INTEGER NOT NULL, stamp TEXT, reason TEXT NOT NULL,\"\n"
              "    \" asked_by TEXT NOT NULL, asked_at TEXT NOT NULL, done_bill_id INTEGER, done_at TEXT, withdrawn_at TEXT, withdrawn_by TEXT)\",   # S618: people's act; only done_* / withdrawn_* set; never deleted\n)\n",
              "order_sheet: table scan_rescan_ask in DDL (OS.ensure makes it)"))
    E.append(("order_sheet.py",
              "\"dup_of\", \"bill_month\", \"lane\", \"status\", \"kind\") if c in cols]\n        since = (dt.datetime.utcnow()",
              "\"dup_of\", \"bill_month\", \"lane\", \"status\", \"kind\", \"rescan_of\") if c in cols]      # S618: + rescan_of\n        since = (dt.datetime.utcnow()",
              "order_sheet: pharmacy_scans() reads rescan_of"))
    E.append(("order_sheet.py",
              "    t = today()\n    sup_of = _resolver(con)\n    tied_scans = {r[0] for r in con.execute(\"SELECT asset_bill_id FROM order_scan_tie\")}\n",
              "    t = today()\n    _s618_follow(con, scans, who)                             # S618: a rescan's re-point and its ask closed -- BEFORE the loop (R1-B4)\n"
              "    sup_of = _resolver(con)\n    tied_scans = {r[0] for r in con.execute(\"SELECT asset_bill_id FROM order_scan_tie\")}\n",
              "order_sheet: tie_pass -- _s618_follow before the loop"))
    E.append(("order_sheet.py",
              "    if m >= 120 and m % 60 == 0:\n        return \"%d hours\" % (m // 60)\n    return \"%d minute%s\" % (m, \"\" if m == 1 else \"s\")\n",
              "    if m >= 120 and m % 60 == 0:\n        return \"%d hours\" % (m // 60)\n    return \"%d minute%s\" % (m, \"\" if m == 1 else \"s\")\n"
              + block(kit, "s618_os_block.txt"),
              "order_sheet: _s618_follow, _s618_carry (at the end)"))
    # ------------------------------------------------------------------------------------------------ porders_s454.py
    E.append(("porders_s454.py",
              "                scan=len(scan_lines(con)), q=len(questions(con)))\n",
              "                scan=len(scan_lines(con)), q=len(questions(con)), rescan=_s618_open_count(con))      # S618: Phir se scan karo\n",
              "porders_s454: counts() carries rescan (and so api_s454/state)"))
    E.append(("porders_s454.py",
              "    rows = ((\"order\", P + \"/s454/order\", \"r_order\"), (\"maal\", P + \"/s454/maal\", \"r_maal\"), (\"scan\", P + \"/s454/scan\", \"r_scan\"), (\"q\", P + \"/s454/q\", \"r_q\"))\n",
              "    rows = ((\"order\", P + \"/s454/order\", \"r_order\"), (\"maal\", P + \"/s454/maal\", \"r_maal\"), (\"scan\", P + \"/s454/scan\", \"r_scan\"), (\"q\", P + \"/s454/q\", \"r_q\"))\n"
              "    if c.get(\"rescan\") and _s618_doer(con, str(login).lower()):   # S618: Phir se scan karo, directly above Bill scan karna hai -- the reception logins only\n"
              "        rows = rows[:2] + ((\"rescan\", P + \"/s454/rescan\", \"r_rescan\"),) + rows[2:]\n",
              "porders_s454: home -- the reception row above Bill scan karna hai"))
    E.append(("porders_s454.py",
              "    if kind == \"owner\" or str(login) in PURANA_USERS or str(u.get(\"user\") or \"\").lower() in PURANA_USERS:\n"
              "        h.append('<div class=\"lnk\"><a id=\"oldpage\" href=\"%s?old=1\">%s</a></div>' % (P, L(en, \"oldpage\")))\n",
              "    if _s618_asker(con, kind, _s618_login(u, login)):          # S618: Scans to redo -- the owner and the askers, while there is any\n"
              "        _n618 = _s618_count(con)\n"
              "        if _n618:\n"
              "            h.append('<div class=\"lnk\"><a id=\"redo\" href=\"%s/s454/scans\">%s</a></div>' % (P, L(en, \"redo_link\", _n618)))\n"
              "    if kind == \"owner\" or str(login) in PURANA_USERS or str(u.get(\"user\") or \"\").lower() in PURANA_USERS:\n"
              "        h.append('<div class=\"lnk\"><a id=\"oldpage\" href=\"%s?old=1\">%s</a></div>' % (P, L(en, \"oldpage\")))\n",
              "porders_s454: home -- the Scans to redo link for the owner and the askers"))
    E.append(("porders_s454.py",
              "# ---- S470 end ---------------------------------------------------------------------------------------------------------------------------\n",
              "# ---- S470 end ---------------------------------------------------------------------------------------------------------------------------\n"
              + block(kit, "s618_p4_block.txt"),
              "porders_s454: the S618 block (rescan_list, the two pages, the two POSTs)"))
    return E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assetapp", default="/root/assetapp")
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    src = {}
    for n, home in HOME.items():
        p = os.path.join(a.assetapp if home == "assetapp" else a.finance, n)
        with open(p, "rb") as fh:
            raw = fh.read()
        if md5b(raw) != FROM[n]:
            print("STOP: %s is %s, not its FROM pin %s -- it changed after the brief; nothing written" % (p, md5b(raw), FROM[n]))
            return 2
        src[n] = raw.decode("utf-8")
    for f, anchor, new, what in edits(a.kit):
        c = src[f].count(anchor)
        if c != 1:
            print("STOP: the anchor for '%s' occurs %d times in %s (must be once) -- nothing written" % (what, c, f))
            return 3
        src[f] = src[f].replace(anchor, new, 1)
        print("  %-18s anchored once, applied: %s" % (f, what))
    os.makedirs(a.out, exist_ok=True)
    for n, text in src.items():
        with open(os.path.join(a.out, n), "wb") as fh:
            fh.write(text.encode("utf-8"))
    with open(os.path.join(a.kit, "scan_quality.py"), "rb") as fh:
        sq = fh.read()
    with open(os.path.join(a.out, "scan_quality.py"), "wb") as fh:
        fh.write(sq)
    for n in sorted(list(src) + ["scan_quality.py"]):
        with open(os.path.join(a.out, n), "rb") as fh:
            print("BUILT %-18s %s" % (n, md5b(fh.read())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
