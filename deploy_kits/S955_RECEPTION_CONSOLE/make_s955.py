#!/usr/bin/env python3
"""make_s955.py -- S955_RECEPTION_CONSOLE (the parent, S521, 25-Nov-2026; D1068, his word 17:05 IST 25-Nov "Reception mobile
required"): makes the TO bytes of /root/portal/calls_staff.py and /root/portal/tile_grants.json from their LIVE bytes.

  python make_s955.py <live calls_staff.py> <live tile_grants.json> <out dir>

calls_staff.py f7e77203 (S953) -> exact edits, each anchor found exactly once (VERSION stays 'S951 1.1', which S951's walk pins):
  * the page admits the reception mobile's login (its card key = PORTAL_RECEPTION_AGENT, default 'reception'), unless the
    setting PORTAL_STAFF_CONSOLE_RECEPTION is 0 / false / no / off;
  * for that login, "Handled today" lists every call made or answered on the reception mobile today (whoever the owner's
    page credited it to), with the Call verdict; no "Wrong?" and no recording there (both belong to a person's card);
  * the tab's empty line and foot say "the reception mobile".
tile_grants.json v48 (4a23e3c4) -> v49: 'My Call Console' granted by name to reception, beside 'Call Tracker'.
Refuses any other FROM. Writes nothing but the two files in <out dir>."""
import hashlib
import json
import os
import sys

CS_FROM = "f7e77203bec9e58274af16c1475b9911"
TG_FROM = "4a23e3c410754e1a5ba2a74b35cf14fb"
TILE = "My Call Console"
USER = "reception"

EDITS = [
    # 1 -- the docstring says who the page is for
    ('ONE PAGE, SIX TABS, for the phone staff (setting PORTAL_PHONE_STAFF) and the logins of PORTAL_STAFF_CONSOLE_EXTRA\n'
     '(default "shavez"):\n',
     'ONE PAGE, SIX TABS, for the phone staff (setting PORTAL_PHONE_STAFF) and the logins of PORTAL_STAFF_CONSOLE_EXTRA\n'
     '(default "shavez") -- and, from S955 (D1068, his word 17:05 IST 25-Nov "Reception mobile required"), the reception\n'
     'mobile\'s login (PORTAL_RECEPTION_AGENT, default "reception"; PORTAL_STAFF_CONSOLE_RECEPTION=0 keeps it out). Its\n'
     '"Handled today" is the reception mobile\'s own calls of today, whoever the owner\'s page credits them to, with the Call\n'
     'verdict, without "Wrong?" or the recording (both belong to a person\'s card; the recording route serves her own calls):\n'),
    # 2 -- the constants
    ('EXTRA_DEFAULT = "shavez"\n',
     'EXTRA_DEFAULT = "shavez"\n'
     'RECEPTION_ON_DEFAULT = "1"     # S955 (D1068): the reception mobile\'s login is admitted unless the setting says 0\n'
     'KIT_S955 = "S955_RECEPTION_CONSOLE"\n'),
    # 3 -- allowed_keys() admits the reception mobile; three small helpers
    ('            out.append(k)\n    return out\n\n\ndef section_rank(',
     '            out.append(k)\n'
     '    rec = reception_key()                              # S955 (D1068): the reception mobile\'s login\n'
     '    if rec and rec not in out and rec not in CC.OWNER_FIRST and reception_on():\n'
     '        out.append(rec)\n'
     '    elif rec and rec in out and not reception_on() and is_reception(rec):\n'
     '        out.remove(rec)                                # the switch off wins over EXTRA (a phone staff key is a person)\n'
     '    return out\n'
     '\n'
     '\n'
     'def reception_key():\n'
     '    """S955: the reception mobile\'s card key -- its MyOperator agent\'s first name as calls_console reads it\n'
     '    (PORTAL_RECEPTION_AGENT, default \'reception\'), which is also its portal login. \'\' when it cannot be read."""\n'
     '    try:\n'
     '        v = str(_cfg("PORTAL_RECEPTION_AGENT", CC.RECEPTION_DEFAULT) or "").strip().lower() or CC.RECEPTION_DEFAULT\n'
     '        return re.sub(r"[^a-z]", "", v.split()[0])\n'
     '    except Exception:\n'
     '        return ""\n'
     '\n'
     '\n'
     'def reception_on():\n'
     '    """S955: PORTAL_STAFF_CONSOLE_RECEPTION (default 1); "0" / "false" / "no" / "off" keeps the reception mobile off this page.\n'
     '    Write it as a STRING in portal_config.py: the portal\'s own reader (portal._cfg_get) treats an int 0 / False as unset."""\n'
     '    try:\n'
     '        v = CC._CFG("PORTAL_STAFF_CONSOLE_RECEPTION", None) if CC._CFG else None\n'
     '    except Exception:\n'
     '        v = None\n'
     '    if v is None or str(v).strip() == "":\n'
     '        v = RECEPTION_ON_DEFAULT\n'
     '    return str(v).strip().lower() not in ("0", "false", "no", "off")\n'
     '\n'
     '\n'
     'def is_reception(key):\n'
     '    """S955: this card key is the reception mobile -- and not one of the phone staff (calls_console\'s own rule)."""\n'
     '    phone = [re.sub(r"[^a-z]", "", p.strip().lower().split()[0]) for p in str(_cfg("PORTAL_PHONE_STAFF", "shivani,alisha") or "").split(",") if p.strip()]\n'
     '    return bool(key) and key == reception_key() and key not in phone\n'
     '\n'
     '\n'
     'def reception_calls(conn, now):\n'
     '    """S955: today\'s calls on the reception mobile exactly as the owner\'s page reads them -- every card\'s calls marked\n'
     '    \'reception mobile\' (credited to the one phone staff member on duty, or kept on the Reception mobile card), each once,\n'
     '    newest first. None when the cards cannot be made. Read-only."""\n'
     '    d_from, d_to, _m = CC.span_bounds("today", "", now)\n'
     '    L = CC.wa_load(conn, d_from, d_to, now, CC._cfg_path("PORTAL_INBOX_DB", CC.INBOX_DB_DEFAULT))\n'
     '    people, _i, _n = CC.build_people(conn, d_from, d_to, now, wa=L["span"], ctx=L["ctx"], dz=L["dz"])\n'
     '    cards = CC._safe_cards(conn, people, d_from, d_to, now, CC._cfg_path("SR_STAFF_MASTER", CC.STAFF_MASTER_DEFAULT),\n'
     '                           CC._cfg_path("SR_PUNCH_CSV", CC.PUNCH_CSV_DEFAULT))\n'
     '    if cards is None:\n'
     '        return None\n'
     '    seen, rows = set(), []\n'
     '    for c in cards:\n'
     '        if c.get("both"):\n'
     '            continue\n'
     '        for r in CC.card_json(c).get("calls") or []:\n'
     '            if r.get("rec") and r.get("ref") not in seen:\n'
     '                seen.add(r.get("ref"))\n'
     '                rows.append(r)\n'
     '    return sorted(rows, key=lambda r: r["sort"], reverse=True)\n'
     '\n'
     '\n'
     'def section_rank('),
    # 4 -- Handled today: the reception mobile's own calls for its login
    ('    try:\n'
     '        c, _handler, _mode, made = CC.card_for(conn, key, "today", now=now)\n'
     '        out["card_ok"] = bool(made)\n'
     '        cj = CC.card_json(c) if c else {"calls": [], "disputes": []}\n'
     '    except Exception:\n'
     '        out["card_ok"], cj = False, {"calls": [], "disputes": []}\n',
     '    rec_view = is_reception(key)                       # S955: the reception mobile\'s own calls, whoever was credited\n'
     '    try:\n'
     '        if rec_view:\n'
     '            rc = reception_calls(conn, now)\n'
     '            out["card_ok"] = rc is not None\n'
     '            cj = {"calls": rc or [], "disputes": []}\n'
     '        else:\n'
     '            c, _handler, _mode, made = CC.card_for(conn, key, "today", now=now)\n'
     '            out["card_ok"] = bool(made)\n'
     '            cj = CC.card_json(c) if c else {"calls": [], "disputes": []}\n'
     '    except Exception:\n'
     '        out["card_ok"], cj = False, {"calls": [], "disputes": []}\n'
     '    if rec_view:\n'
     '        out["reception"] = True\n'),
    # 5 -- no "Wrong?" and no recording on the reception mobile's list: both belong to a person's card (the recording route
    #      serves a person's own calls only -- the cold review's MUST)
    ('                     "can_dispute": bool(r["ai"]) and d_ is None and r["ref"] not in open_ref,\n'
     '                     "disputed": st, "jk": r["jk"] if r["has_rec"] else "", "sort": r["sort"]})\n',
     '                     "can_dispute": bool(r["ai"]) and d_ is None and r["ref"] not in open_ref and not rec_view,\n'
     '                     "disputed": st, "jk": r["jk"] if (r["has_rec"] and not rec_view) else "", "sort": r["sort"]})\n'),
    # 6 -- the tab's words for the reception mobile
    ('"warn": card_warn, "empty": "No calls handled by you yet today.", "foot": "Only your own calls · no transcripts"},\n',
     '"warn": card_warn,\n'
     '         "empty": "No calls on the reception mobile yet today." if d.get("reception") else "No calls handled by you yet today.",\n'
     '         "foot": "Calls on the reception mobile · no transcripts" if d.get("reception") else "Only your own calls · no transcripts"},\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(cs_p, tg_p, out):
    cs, tgb = open(cs_p, "rb").read(), open(tg_p, "rb").read()
    if md5(cs) != CS_FROM:
        sys.exit("REFUSED: calls_staff.py is %s, not S953's %s" % (md5(cs)[:8], CS_FROM[:8]))
    if md5(tgb) != TG_FROM:
        sys.exit("REFUSED: tile_grants.json is %s, not v48's %s" % (md5(tgb)[:8], TG_FROM[:8]))
    s = cs.decode("utf-8")
    for old, new in EDITS:
        if s.count(old) != 1:
            sys.exit("REFUSED: an edit's anchor is found %d times (must be 1): %r" % (s.count(old), old[:70]))
        s = s.replace(old, new)
    tg = json.loads(tgb.decode("utf-8"))
    if tg.get("version") != 48:
        sys.exit("REFUSED: tile_grants.json is not v48")
    ent = tg.get("users", {}).get(USER)
    if not isinstance(ent, dict) or isinstance(ent.get("only"), list):
        sys.exit("REFUSED: no plain grants entry for %s" % USER)
    ex = ent.setdefault("extra", [])
    if TILE in ex:
        sys.exit("REFUSED: already granted to %s" % USER)
    ex.insert(ex.index("Call Tracker") + 1 if "Call Tracker" in ex else 0, TILE)
    tg["version"] = 49
    tg["_note"] = tg.get("_note", "") + ("  S955 v49 (S521, 25-Nov-2026, D1068): 'My Call Console' granted by name to reception "
                                          "(the reception mobile), beside 'Call Tracker'; the page admits its login unless "
                                          "PORTAL_STAFF_CONSOLE_RECEPTION is 0.")
    os.makedirs(out, exist_ok=True)
    sb = s.encode("utf-8")
    tb = (json.dumps(tg, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    with open(os.path.join(out, "calls_staff.py"), "wb") as fh:
        fh.write(sb)
    with open(os.path.join(out, "tile_grants.json"), "wb") as fh:
        fh.write(tb)
    print("calls_staff.py %s -> %s" % (CS_FROM[:8], md5(sb)[:8]))
    print("tile_grants.json v48 %s -> v49 %s" % (TG_FROM[:8], md5(tb)[:8]))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
