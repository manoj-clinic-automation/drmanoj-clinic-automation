#!/usr/bin/env python3
"""
patch_pharma_lane_s219.py -- S219 M3 / PP0-lite: the PHARMACY LANE on the
existing bill intake.  ELEVEN anchored changes to /root/assetapp/asset_register.py,
every OLD block sliced verbatim from the live bytes
0cd8fc3bfe8d39322c6162a41124bddf (never re-typed -- A0).

WHAT IT DOES.  Reception picks "Pharmacy purchase" at the scan intake; that bill
is stored kind='Pharmacy', status='captured' -- a witness, not an approval item.
Because it never carries status='draft' or 'approved', the pending badge and all
eleven queries behind the owner's /purchases rate-history page are untouched, and
NOT ONE of them needed editing.

WHAT IT DOES NOT DO.  It does not send anything anywhere, does not touch Marg,
does not read or write any purchase figure, and adds no table.  August purchase
data remains provisional under the owner's 02-Sep hold; this only captures paper
arriving from now on.

SAFETY: exact-once assert on all eleven anchors, timestamped backup,
compile-with-restore, idempotent via MARK.
USAGE: python3 -B /root/assetapp/patch_pharma_lane_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("AR_PATH", "/root/assetapp/asset_register.py")
MARK = "S219 PP0-lite: the pharmacy lane"

A_OLD = 'def _create_intake_bill(fobj, note):'

A_NEW = 'def _create_intake_bill(fobj, note, lane=None):'

A2_OLD = '    cur = db.execute(\n        "INSERT INTO bills(kind,notes,source_stored,source_orig,stamp_no,status,"\n        "submitted_by,submitted_at) VALUES(\'Consumable\',?,?,?,?,\'draft\',?,?)",\n        (note, stored, secure_filename(fobj.filename), stamp,\n         g.user["display_name"], _now_ist()))'

A2_NEW = '    # S219 PP0-lite: the pharmacy lane.  A pharmacy purchase bill is a WITNESS --\n    # roughly eighty a month, scanned at arrival so the paper can be filed and\n    # later matched to what Marg says.  It is not a clinic asset or consumable\n    # awaiting anyone\'s approval, and D335 says so: kind=\'pharma_purchase\' exists\n    # to keep that volume OUT of the asset approval queue.\n    #\n    # So it lands as kind=\'Pharmacy\' with status=\'captured\', and that single\n    # choice is what keeps the rest of the app untouched:\n    #   * the pending badge counts status=\'draft\'      -> pharmacy never inflates it\n    #   * /purchases filters status=\'approved\' in all\n    #     eleven of its queries                        -> the owner\'s rate-history\n    #                                                     page is unchanged, with\n    #                                                     no edit to any of them\n    #   * bill_approve refuses anything but \'draft\'    -> it cannot enter that flow\n    # Anything that is not the pharmacy lane behaves EXACTLY as before.\n    _pharma = (lane or "").strip().lower() == "pharmacy"\n    cur = db.execute(\n        "INSERT INTO bills(kind,notes,source_stored,source_orig,stamp_no,status,"\n        "submitted_by,submitted_at) VALUES(?,?,?,?,?,?,?,?)",\n        ("Pharmacy" if _pharma else "Consumable", note, stored,\n         secure_filename(fobj.filename), stamp,\n         "captured" if _pharma else "draft",\n         g.user["display_name"], _now_ist()))'

B_OLD = '    bid = _create_intake_bill(fobj, request.form.get("note"))\n    if not bid:\n        flash("No usable file received — send a photo or a PDF and try again.")'

B_NEW = '    bid = _create_intake_bill(fobj, request.form.get("note"),\n                              request.form.get("lane"))\n    if not bid:\n        flash("No usable file received — send a photo or a PDF and try again.")'

C_OLD = '    bid = _create_intake_bill(fobj, request.form.get("note"))\n    if not bid:\n        return ("no usable file", 400)'

C_NEW = '    # the widget forwards CFG.uploadFields verbatim, which is how the Note has\n    # always reached the server -- the lane rides the same road, so the widget\n    # itself needs no change and stays at its S219 v2 bytes.\n    bid = _create_intake_bill(fobj, request.form.get("note"),\n                              request.form.get("lane"))\n    if not bid:\n        return ("no usable file", 400)'

D_OLD = '<label for=intake_note>Note <span class=muted>(optional, e.g. "2 boxes, one bill")</span></label>\n<input id=intake_note maxlength=120 style="max-width:300px"\n oninput="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.note=this.value;}"></div>'

D_NEW = '<label for=intake_lane>What kind of bill is this?</label>\n<select id=intake_lane style="max-width:300px"\n onchange="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.lane=this.value;}\n           var h=document.getElementById(\'lane_basic\'); if(h){h.value=this.value;}">\n<option value="clinic">Clinic bill — asset or consumable</option>\n<option value="pharmacy">Pharmacy purchase — Sanjeevni</option>\n</select>\n<p class=muted style="margin:4px 0 0">A pharmacy bill is filed as a scan and a stamp only.\nIt does not go into the clinic approval list.</p>\n<label for=intake_note>Note <span class=muted>(optional, e.g. "2 boxes, one bill")</span></label>\n<input id=intake_note maxlength=120 style="max-width:300px"\n oninput="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.note=this.value;}"></div>'

D2_OLD = '<form method=post action="{{url_for(\'intake_submit\')}}" enctype=multipart/form-data style="margin-top:12px">'

D2_NEW = '<form method=post action="{{url_for(\'intake_submit\')}}" enctype=multipart/form-data style="margin-top:12px">\n<input type=hidden name=lane id=lane_basic value="clinic">'

E_OLD = '    if fk in ("Asset", "Consumable"):'

E_NEW = '    if fk in ("Asset", "Consumable", "Pharmacy"):'

E2_OLD = '    if fs in ("draft", "approved", "rejected"):'

E2_NEW = '    if fs in ("draft", "approved", "rejected", "captured"):'

E3_OLD = '<select name=kind onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Kind: all</option><option {{\'selected\' if fk==\'Consumable\'}}>Consumable</option><option {{\'selected\' if fk==\'Asset\'}}>Asset</option></select>\n<select name=status onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Status: all</option><option {{\'selected\' if fs==\'draft\'}}>draft</option><option {{\'selected\' if fs==\'approved\'}}>approved</option><option {{\'selected\' if fs==\'rejected\'}}>rejected</option></select>'

E3_NEW = '<select name=kind onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Kind: all</option><option {{\'selected\' if fk==\'Consumable\'}}>Consumable</option><option {{\'selected\' if fk==\'Asset\'}}>Asset</option><option {{\'selected\' if fk==\'Pharmacy\'}}>Pharmacy</option></select>\n<select name=status onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Status: all</option><option {{\'selected\' if fs==\'draft\'}}>draft</option><option {{\'selected\' if fs==\'approved\'}}>approved</option><option {{\'selected\' if fs==\'rejected\'}}>rejected</option><option {{\'selected\' if fs==\'captured\'}}>captured</option></select>'

F_OLD = '    if b["status"] != "draft":\n        flash("Only draft bills can be edited.")\n        return redirect(url_for("bill_view", bid=bid))\n    if request.method == "POST":\n        f = request.form\n        kind = f.get("kind") if f.get("kind") in ("Asset", "Consumable") else "Consumable"\n        db.execute("UPDATE bills SET kind=?, vendor=?, bill_no=?, bill_date=?, total_amount=?,"'

F_NEW = '    # S219: \'captured\' joins \'draft\' here.  A pharmacy bill never becomes a draft,\n    # so without this a mis-read scan -- wrong vendor, wrong total -- could never\n    # be corrected by anyone, and a witness nobody can fix is worse than no\n    # witness at all.  Everything else about the guard is unchanged.\n    if b["status"] not in ("draft", "captured"):\n        flash("Only draft bills (and captured pharmacy scans) can be edited.")\n        return redirect(url_for("bill_view", bid=bid))\n    if request.method == "POST":\n        f = request.form\n        # \'Pharmacy\' MUST be in this whitelist: it is a fall-through to\n        # "Consumable", so without it any edit of a pharmacy bill would silently\n        # move it into the clinic lane -- and silently is how it would happen.\n        kind = f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy") else "Consumable"\n        db.execute("UPDATE bills SET kind=?, vendor=?, bill_no=?, bill_date=?, total_amount=?,"'

G_OLD = '<label>Kind</label><select name=kind style="width:auto"><option {{\'selected\' if hdr.get(\'kind\')!=\'Asset\'}}>Consumable</option><option {{\'selected\' if hdr.get(\'kind\')==\'Asset\'}}>Asset</option></select>'

G_NEW = '<label>Kind</label><select name=kind style="width:auto"><option {{\'selected\' if hdr.get(\'kind\') not in (\'Asset\',\'Pharmacy\')}}>Consumable</option><option {{\'selected\' if hdr.get(\'kind\')==\'Asset\'}}>Asset</option><option {{\'selected\' if hdr.get(\'kind\')==\'Pharmacy\'}}>Pharmacy</option></select>'

PAIRS = [("A", A_OLD, A_NEW), ("A2", A2_OLD, A2_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW), ("D", D_OLD, D_NEW), ("D2", D2_OLD, D2_NEW), ("E", E_OLD, E_NEW), ("E2", E2_OLD, E2_NEW), ("E3", E3_OLD, E3_NEW), ("F", F_OLD, F_NEW), ("G", G_OLD, G_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched (%s) -- nothing to do" % MARK)
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "The live file is not the one this kit was built "
                             "against; nothing has been changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S219_pharma_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); restored from %s" % (ex, bak))
    print("patched %s (%s)" % (TARGET, MARK))
    print("backup  %s" % bak)
    print("restart: systemctl restart assetapp.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
