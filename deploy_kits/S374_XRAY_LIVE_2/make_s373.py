#!/usr/bin/env python3
# make_s373.py -- records.py S353 (07ec9b41) -> S373 (the X-ray live filing): anchored edits on the LIVE bytes + one appended block.
import hashlib, os, sys
FROM = "07ec9b41cb5bbded215dcd1b1916e3d0"
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read(); assert hashlib.md5(b).hexdigest() == FROM, "live records.py is not 07ec9b41 (S353)"
t = b.decode("utf-8")
here = os.path.dirname(os.path.abspath(__file__))
block = open(os.path.join(here, "xray_live_block.py"), encoding="utf-8").read()
def once(old, new, label):
    global t
    assert t.count(old) == 1, "anchor not unique: %s (%d)" % (label, t.count(old))
    t = t.replace(old, new)
# 1 -- the plan row carries the Drive id (the test page never needed it; the live filing does)
once('        row = {"orig": name, "time": None, "src": "", "cid": "", "proposed": "", "verdict": "", "kind": ""}\n',
     '        row = {"orig": name, "time": None, "src": "", "cid": "", "proposed": "", "verdict": "", "kind": "", "id": f.get("id", "")}\n', "row id")
# 2 -- Check karein: two new kinds and their answers
once('    "wa": [],                                                # S344: its own form (patient + kind), see _wa_form\n}\n',
     '    "wa": [],                                                # S344: its own form (patient + kind), see _wa_form\n'
     '    "xray_file": [("not_xray", "Yeh X-ray nahi / bekaar")],   # S373 (+ the ID box, like lab_id)\n'
     '    "xray_missing": [("asked", "File baad mein daalenge"), ("not_done", "X-ray nahi hua")],   # S373\n}\n', "ANS")
once('"id_fixed": "ID corrected"}', '"id_fixed": "ID corrected", "not_xray": "not an X-ray", "not_done": "X-ray not done"}', "ANS_EN")
once('    out.extend(wa_items(con))\n    out.sort(key=lambda i: (i["day"], i["key"]))\n',
     '    out.extend(wa_items(con))\n    try:\n        out.extend(xray_items(con))                         # S373\n    except Exception:                                   # noqa: BLE001\n        pass\n'
     '    out.sort(key=lambda i: (i["day"], i["key"]))\n', "items")
once('        if i["kind"] == "lab_id":\n', '        if i["kind"] in ("lab_id", "xray_file"):\n', "page id box")
once('    allowed = {c for c, _ in ANS[item["kind"]]} | ({"id_fixed"} if item["kind"] == "lab_id" else set())\n',
     '    allowed = {c for c, _ in ANS[item["kind"]]} | ({"id_fixed"} if item["kind"] in ("lab_id", "xray_file") else set())\n', "allowed")
once('''        con.execute("UPDATE record_file SET clinic_id=?, note=? WHERE id=?",
                    (nid, "ID corrected from %s by %s at %s" % (item["clinic_id"], _who(u), _stamp()), item["file_id"]))
        note = "%s -> %s" % (item["clinic_id"], nid)
''', '''        if item["kind"] == "xray_file":                     # S373: the next mailbox run files it under this ID
            note = nid
        else:
            con.execute("UPDATE record_file SET clinic_id=?, note=? WHERE id=?",
                        (nid, "ID corrected from %s by %s at %s" % (item["clinic_id"], _who(u), _stamp()), item["file_id"]))
            note = "%s -> %s" % (item["clinic_id"], nid)
''', "id_fixed")
# 3 -- the patient page: the pictures, side by side, instead of "(next step)"
once('''        xr.append('<h3>X-rays taken</h3><p class="sm">The images join this page with the X-ray inbox (next step).</p>')\n''',
     '''        xr.append('<h3>X-rays taken</h3>' + xray_gallery(con, cid))\n''', "gallery")
# 4 -- the block, before the shell
once("\n\n# ---------------------------------------------------------------- the frame\n", block + "\n\n# ---------------------------------------------------------------- the frame\n", "block")
open(out, "wb").write(t.encode("utf-8"))
print("records.py S373 ->", hashlib.md5(t.encode("utf-8")).hexdigest())
