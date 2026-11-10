#!/usr/bin/env python3
"""make_s768.py LIVE_FINANCE_DIR OUT_DIR -- builds the kit's files from THIS box's live bytes (F-472).
stockmatch.py and stockmatch.html must be at their FROM pins; each anchored edit must match exactly once.
The two new files (section_count.py, section_count.html) and the seed are copied from the kit folder."""
import hashlib
import os
import shutil
import sys

KDIR = os.path.dirname(os.path.abspath(__file__))
FROM = {"stockmatch.py": "623cb6f1db2640edd6fe2b8ef7f98837", "stockmatch.html": "02826136d9cbb015dfb44c63ef5263d1"}
EDITS = {
    "stockmatch.py": [(
        "    _db, _require, _unit = db_getter, require_fn, unit\n    app.register_blueprint(bp)\n    return bp\n",
        "    _db, _require, _unit = db_getter, require_fn, unit\n    app.register_blueprint(bp)\n"
        "    try:                                                      # S768 (10-Nov-2026): the section count -- Stock milaan > Orthotics count\n"
        "        import section_count                                  # noqa: PLC0415 -- beside this file\n"
        "        section_count.init(app, db_getter, require_fn)\n"
        "    except Exception as _e768:                                # noqa: BLE001 -- Stock milaan keeps working without it\n"
        "        print(\"section_count NOT mounted: %s\" % _e768, file=sys.stderr)\n"
        "    return bp\n"),
    ],
    "stockmatch.html": [(
        '<div class="sub" id="sub"></div>\n<div id="body">',
        '<div class="sub" id="sub"></div>\n'
        '<a id="s768count" href="/finance/stockmatch/count" style="display:inline-block;margin:6px 0 10px;padding:10px 14px;border-radius:8px;'
        'background:#0E5C58;color:#fff;font-weight:600;text-decoration:none">Orthotics ginti (shelf count) &rarr;</a>\n<div id="body">'),
    ],
}
NEW = ("section_count.py", "section_count.html", "section_count_seed_S768.txt")


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(live, out):
    os.makedirs(out, exist_ok=True)
    for name, edits in EDITS.items():
        raw = open(os.path.join(live, name), "rb").read()
        if md5(raw) != FROM[name]:
            print("REFUSED: %s is %s, not its FROM pin %s" % (name, md5(raw)[:8], FROM[name][:8]))
            return 2
        t = raw.decode("utf-8")
        for old, new in edits:
            if t.count(old) != 1:
                print("REFUSED: %s: an anchor matches %d times" % (name, t.count(old)))
                return 2
            t = t.replace(old, new)
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(t.encode("utf-8"))
        print("built %s %s -> %s" % (name, FROM[name][:8], md5(t.encode("utf-8"))[:8]))
    for name in NEW:
        shutil.copy2(os.path.join(KDIR, name), os.path.join(out, name))
        print("copied %s %s" % (name, md5(open(os.path.join(out, name), "rb").read())[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
