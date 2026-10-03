#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p4a.py -- kit S454_BILL_REGISTER, part 4 -- the server side (S454 10.2): the medical PC tells the owner when it refuses a file.
CLAUDE.md rule 2: built from the live bytes (every anchor exactly once, FROM -> TO pinned).

  marg_door.py  POST /finance/api/marg-file with the header X-Marg-Note: refused and a small JSON body -- {name, md5, kind, reason} and
                nothing else, never a file's content -- is the medical PC's note of a text it refused. Same address, same token (checked
                first, as for a file), before take(): one mi_file row, verdict and pc_verdict REFUSED, with the reason. The owner's Needs-you
                ("Report refused today"), the reports tile and Darpan's card (an order sheet: "Order sheet adhoori thi") already read such a
                row. The same file's note again adds nothing. finance_app.py is not touched.

    make_s454p4a.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os

FROM = {"marg_door.py": "598ba2df83f029d6f861e63190a62a33"}

MD = [('''    if not _rate_ok():
        return jsonify(ok=False, status="SLOW_DOWN",
                       message="more than %d files in a minute; nothing was taken" % RATE_PER_MIN), 429
''',
       '''    if not _rate_ok():
        return jsonify(ok=False, status="SLOW_DOWN",
                       message="more than %d files in a minute; nothing was taken" % RATE_PER_MIN), 429
    if str(request.headers.get("X-Marg-Note") or "").strip().lower() == "refused":   # S454 P4 (10.2): the PC's note, before take()
        return _s454_pc_note(MT)
''')]

MD_APPEND = '''

# ==========================================================================================================================================
# S454_BILL_REGISTER part 4 (03-Oct-2026, S454 10.2): THE MEDICAL PC'S NOTE OF A REFUSED FILE. Until now a text the medical PC refused stayed
# on that PC (a file in _captured_txt\\refused\\ and a log line) and reached nobody. Its watcher now sends a note -- the file's name, its md5,
# the kind it looked like and the reason; no content -- to this same door with the same token. One mi_file row is written, refused by the
# PC, and the readers that already exist name it: the owner's "Report refused today", the reports tile, Darpan's order-sheet card.
# ==========================================================================================================================================
_S454_KINDS = {"SALE": "SALE_BILLWISE", "STOCK": "STOCK_CLOSING", "ORDER": "ORDER_PENDING", "": ""}
_S454_KEYS = ("name", "md5", "kind", "reason", "at")


def _s454_pc_note(MT):
    if request.files or (request.content_length or 0) > 4096:
        return jsonify(ok=False, status="REFUSED", message="a note carries no file content -- nothing written"), 400
    b = request.get_json(silent=True)
    if not isinstance(b, dict) or [k for k in b if k not in _S454_KEYS]:
        return jsonify(ok=False, status="REFUSED", message="a note is {name, md5, kind, reason} and nothing else -- nothing written"), 400
    md5 = str(b.get("md5") or "").strip().lower()
    kind = str(b.get("kind") or "").strip().upper()
    if len(md5) != 32 or any(c not in "0123456789abcdef" for c in md5) or kind not in _S454_KINDS:
        return jsonify(ok=False, status="REFUSED", message="a note needs the file's md5 and a known kind (SALE, STOCK, ORDER or none)"), 400
    name = MT.safe_name(str(b.get("name") or ""))[:120]
    why = " ".join(str(b.get("reason") or "").split())[:240] or "no reason given"
    MI = MT.MI
    con = MT._connect(MI.DB_DEFAULT)
    try:
        if con.execute("SELECT 1 FROM mi_file WHERE md5=?", (md5,)).fetchone():
            return jsonify(ok=True, status="ALREADY", md5=md5, message="this file is already on the server's list -- nothing written twice"), 200
        now = MI.now_ist()
        con.execute(
            "INSERT INTO mi_file (md5, drive_id, drive_name, drive_folder, drive_mtime, size, stamp, type, variant, date_from, date_to, verdict, "
            "reason, server_name, kept, lines, pc_type, pc_verdict, agree, received_at, source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (md5, "", name, "pc_note", "", 0, now.strftime("%Y%m%d-%H%M%S"), _S454_KINDS[kind], "", "", "", "REFUSED",
             ("the medical PC refused it: %s" % why)[:300], "", 0, 0, kind, "REFUSED", "", now.isoformat(), "push"))
        con.commit()
    finally:
        con.close()
    return jsonify(ok=True, status="NOTED", md5=md5, type=_S454_KINDS[kind], message="the refusal is on the owner's list"), 200
# ---- S454 part 4 end -------------------------------------------------------------------------------------------------------------------
'''

EDITS = {"marg_door.py": MD}
APPEND = {"marg_door.py": MD_APPEND}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(FROM):
        raw = open(os.path.join(a.finance, f), "rb").read()
        m = md5b(raw)
        if m != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in EDITS.get(f, []):
            c = txt.count(old)
            if c != 1:
                raise SystemExit("STOP: an anchor occurs %d times in %s -- nothing built: %r" % (c, f, old[:90]))
            txt = txt.replace(old, new, 1)
        if "\nif __name__ == \"__main__\":" in txt:
            raise SystemExit("STOP: %s has a __main__ guard -- the block's place must be decided" % f)
        txt = txt.rstrip("\n") + "\n" + APPEND[f]
        out = txt.encode("utf-8")
        open(os.path.join(a.out, f), "wb").write(out)
        print("built %-18s %s -> %s  (%d edits + 1 block)" % (f, m[:8], md5b(out), len(EDITS[f])))


if __name__ == "__main__":
    main()
