#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s408.py -- builds the five patched live files of kit S408_MONTH_END_PACKS from the LIVE bytes by anchored edits.
Every anchor must occur exactly once, and every source must be at its FROM pin, or the build stops with nothing written.

  finance_app.py           the front gate learns the unit 'packs' (/finance/packs/...); packs is mounted, guarded
  portal.py                two tiles: 'Month-end packs' (the doctor) and 'Mahine ka kaam' (roles ['doctor'], granted by name)
  tile_grants.json         v28 -> v29: 'Mahine ka kaam' to shavez
  sanjeevni_approvals.py   Needs you gains the shelf's and the checklist's lines after the 10th (fail-soft)
  amir_day.py              every step page carries 'Pichle mahine ka pack' when it is ready (fail-soft)

Usage: make_s408.py --finance /root/finance --portal /root/portal --out DIR
"""
import hashlib
import json
import os
import sys

FROM = {
    "finance_app.py": "d19c2046b190a4ec00745dc4121152e8",
    "portal.py": "968ca6027ae30d67e7d18b83f35b395d",
    "tile_grants.json": "0aadfc523f9ab9c59633dedcd618cee9",
    "sanjeevni_approvals.py": "f6fc90d5d31badd3c5eec3691a78c4fb",
    "amir_day.py": "59a51d471cb30702dfd0cb8b6b6f3a44",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


def build_finance_app(s):
    s = rep(s, '''    if path == "/finance/porders" or path.startswith("/finance/porders/"):
        return "porders"     # S403: the Purchase orders screen (owner, 26-Sep-2026, D618). bhati holds no row here.
''', '''    if path == "/finance/porders" or path.startswith("/finance/porders/"):
        return "porders"     # S403: the Purchase orders screen (owner, 26-Sep-2026, D618). bhati holds no row here.
    if path == "/finance/packs" or path.startswith("/finance/packs/"):
        return "packs"       # S408: Month-end packs (the doctor checker) and Shavez's checklist (maker) -- PARENT (clinic), D624.
''', "unit map")
    s = rep(s, '''# --- S403_PURCHASE_ORDERS_LIVE end ---
''', '''# --- S403_PURCHASE_ORDERS_LIVE end ---

# --- S408_MONTH_END_PACKS begin -- the statement shelf, the accountant pack, Amir's pack, Shavez's checklist (owner, 26-Sep-2026, D624) ---
# PARENT (clinic). Its own unit 'packs' (shavez maker, the doctor checker). Reads the clinic day revenue, the UPI feed, the
# payment register, purchase_app's pay sheet, the asset app's lanes -- in process, read-only. GUARDED (S209): a fault inside
# the module is printed and every other page keeps serving.
try:
    import packs                                               # noqa: E402
    packs.init(app, db, require, unit="packs")
except Exception as _ex_pk:                                    # noqa: BLE001
    print("packs NOT mounted: %s" % _ex_pk, file=sys.stderr)
# --- S408_MONTH_END_PACKS end ---
''', "mount")
    return s


def build_portal(s):
    s = rep(s, '''     "url": "/finance/porders",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', '''     "url": "/finance/porders",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4E6", "name": "Month-end packs",
     # S408 NEW (owner, 26-Sep-2026, D624). PARENT (clinic). The statement shelf (every account's month: arrived / read / matched),
     # the accountant pack (his formal list, ready / missing / late, ONE Send), Amir's pack, Shavez's checklist as the system sees it.
     # Its own server unit ('packs': the doctor checker). The doctor holds the tile by role; nobody else sees it.
     "desc": "Statements on the shelf \\u00b7 the accountants' pack \\u00b7 one Send",
     "live": True,
     "url": "/finance/packs",
     "roles": ["doctor"]},
    {"icon": "\\U0001F5D3", "name": "Mahine ka kaam",
     # S408 NEW (owner, 26-Sep-2026, D624). PARENT (clinic). Shavez's monthly checklist as a page (Hindi): 'system se ho gaya' where
     # automatic, a tick for the rest. Its own server unit ('packs': shavez maker). Granted by name in tile_grants.json v29 to shavez;
     # the doctor holds it by role.
     "desc": "Mahine ke ant ka kaam \\u2014 tick karo",
     "live": True,
     "url": "/finance/packs/checklist",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', "portal tiles")
    s = rep(s, '''    "Purchase orders": "Money & Accounts",
''', '''    "Purchase orders": "Money & Accounts",
    "Month-end packs": "Money & Accounts",
    "Mahine ka kaam": "Money & Accounts",
''', "portal sections")
    return s


def build_grants(raw):
    d = json.loads(raw)
    if json.dumps(d, indent=2, ensure_ascii=False) != raw:
        sys.exit("REFUSED: tile_grants.json does not round-trip through json.dumps(indent=2) -- build by hand")
    if d.get("version") != 28:
        sys.exit("REFUSED: tile_grants.json is v%r, expected v28" % d.get("version"))
    ex = d["users"].setdefault("shavez", {}).setdefault("extra", [])
    if "Mahine ka kaam" not in ex:
        ex.append("Mahine ka kaam")
    d["version"] = 29
    d["_note"] += (" | v29 (S408, 26-Sep-2026, PARENT): the NEW tile 'Mahine ka kaam' (/finance/packs/checklist -- Shavez's monthly checklist as a "
                   "page: 'system se ho gaya' where automatic, a tick for the rest) to shavez; the doctor holds it and the NEW 'Month-end packs' "
                   "tile (/finance/packs) by role. Their gate is a NEW server unit 'packs' (shavez maker, the doctor checker); nothing else in "
                   "this file moves.")
    return json.dumps(d, indent=2, ensure_ascii=False)


def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.8  ·  kit S407_NEFT_MESSAGES  ·  Session 283 (Sanjeevni)
#
''', '''#  sanjeevni_approvals.py  ·  v1.9  ·  kit S408_MONTH_END_PACKS  ·  Session 283
#
#  v1.9 (S408, D624, 26-Sep-2026): after the 10th, Needs you gains the previous month's empty statement cells and Shavez's open
#  checklist items (read from packs, fail-soft). NEEDS_YOU_WITHOUT_S408=1 leaves them out -- set only by S400's frozen walk re-run.
#
''', "header")
    s = rep(s, '''VERSION = "1.8"
''', '''VERSION = "1.9"
''', "version")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 12 · S408 (D624): the statement shelf's empty cells and the month-end checklist's open items, after the 10th (fail-soft).
    #      NEEDS_YOU_WITHOUT_S408=1 is set ONLY by S400's frozen walk re-run (it asserts Needs you unchanged); the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S408") != "1":
        try:
            import packs  # noqa: PLC0415
            lines.extend(packs.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)
''', "needs-you lines")
    return s


def build_amir(s):
    s = rep(s, '''def _neft_card_s407():
''', '''def _packs_card_s408():
    """S408 (D624): 'Pichle mahine ka pack' -- the paid NEFT sheet and the two Sanjeevni statements, when both are on the shelf;
    tap-to-open each, 'dekh liya' once. Read from packs; fail-soft."""
    try:
        import packs                                               # noqa: PLC0415
        return packs.amir_card(_db())
    except Exception:                                              # noqa: BLE001
        return ""


def _neft_card_s407():
''', "packs card helper")
    s = rep(s, '''    return _shell("Amir -- kaam", _banner(step, w) + head + body + _neft_card_s407() +
''', '''    return _shell("Amir -- kaam", _banner(step, w) + head + body + _neft_card_s407() + _packs_card_s408() +
''', "packs card on the page")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, por, out = args.get("--finance"), args.get("--portal"), args.get("--out")
    if not (fin and por and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {
        "finance_app.py": build_finance_app(load(os.path.join(fin, "finance_app.py"), "finance_app.py")),
        "portal.py": build_portal(load(os.path.join(por, "portal.py"), "portal.py")),
        "tile_grants.json": build_grants(load(os.path.join(por, "tile_grants.json"), "tile_grants.json")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "amir_day.py": build_amir(load(os.path.join(fin, "amir_day.py"), "amir_day.py")),
    }
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
