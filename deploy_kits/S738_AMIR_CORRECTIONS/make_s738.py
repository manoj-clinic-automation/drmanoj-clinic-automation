#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s738.py -- S738_AMIR_CORRECTIONS: the appended sections and the one route of the three live files of this project.
    python3 -B make_s738.py <dir holding scan_register.py, amir_day.py, purchase_app.py> <out dir> [<dir holding the S738 sections>]
Each FROM file must carry its pinned md5; every anchor must stand EXACTLY ONCE; the TO md5s are printed. The sections are read from
sec_sr738.txt and sec_amir738.txt beside this script (or the third argument)."""
import hashlib
import os
import sys

FROM = {"scan_register.py": "4d8432ea94822692c15e5e840c8d08d7",     # S736's TO (live 06-Nov 20:42)
        "amir_day.py": "10a5f9c4793f170c040e5e71b516503c",          # S690's TO (= the bundle)
        "purchase_app.py": "5fde52aafbb5367f329fb3696082f784"}      # S736's TO

ROUTE_OLD = '''# ---- S736 end -----------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
'''
ROUTE_NEW = '''# ---- S736 end -----------------------------------------------------------------------------------------------------------------------------


# ---- S738 (06-Nov-2026, Sanjeevni session 396, kit S738_AMIR_CORRECTIONS; D839, D840): a scan shown in place -----------------------------
@bp.route("/api/s738/scan/<int:sid>")
def api_s738_scan(sid):
    """One captured pharmacy scan, INLINE (the owner's folded viewer on /page/check; Amir's 'Kaagaz dekhiye'). The doctor: any scan. Amir
    (purchase.scan_file_users): only a scan on his correction list (scan_register.s738_scan_ok). Read only."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    doc = _is_doctor(u)
    if not doc and not _s446_files_ok(con, u):
        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")
    if not _s454_sr().s738_scan_ok(con, sid, doc, str((u or {}).get("user") or "")):
        return _refuse("Yeh kaagaz aapki list par nahi hai.")
    got = _s446_file_bytes(sid)
    if got is None:
        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404
    data = got[1]
    mt = ("application/pdf" if data[:4] == b"%PDF" else "image/jpeg" if data[:3] == b"\\xff\\xd8\\xff" else "image/png" if data[:8] == b"\\x89PNG\\r\\n\\x1a\\n"
          else "application/octet-stream")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(got[0] or "scan"))[:80] or "scan"
    from flask import Response                                 # noqa: PLC0415
    return Response(data, mimetype=mt, headers={"Content-Disposition": 'inline; filename="%s"' % name, "Cache-Control": "no-store",
                                                "X-Content-Type-Options": "nosniff"})
# ---- S738 end -----------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sd, od = sys.argv[1], sys.argv[2]
    secd = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    src = {}
    for n, pin in FROM.items():
        b = open(os.path.join(sd, n), "rb").read()
        if md5(b) != pin:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (n, md5(b)[:8], pin[:8]))
        src[n] = b.decode("utf-8")
    out = {}
    for n, sec in (("scan_register.py", "sec_sr738.txt"), ("amir_day.py", "sec_amir738.txt")):
        if not src[n].endswith("\n"):
            sys.exit("REFUSED: %s does not end in a newline" % n)
        out[n] = src[n] + open(os.path.join(secd, sec), encoding="utf-8").read()
    pa = src["purchase_app.py"]
    if pa.count(ROUTE_OLD) != 1:
        sys.exit("REFUSED: purchase_app.py anchor found %d times (must be once)" % pa.count(ROUTE_OLD))
    out["purchase_app.py"] = pa.replace(ROUTE_OLD, ROUTE_NEW)
    os.makedirs(od, exist_ok=True)
    for n in ("scan_register.py", "amir_day.py", "purchase_app.py"):
        b = out[n].encode("utf-8")
        open(os.path.join(od, n), "wb").write(b)
        print("%s  %s -> %s" % (n, FROM[n][:8], md5(b)))


if __name__ == "__main__":
    main()
