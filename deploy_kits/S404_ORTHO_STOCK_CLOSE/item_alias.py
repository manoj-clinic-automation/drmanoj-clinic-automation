#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  item_alias.py  ·  v1.0  ·  kit S404_ORTHO_STOCK_CLOSE  ·  Session 283 (Sanjeevni)  ·  D620
#
#  THE RENAME MEMORY.  Amir renames 22 orthotic items in Marg (the owner's list
#  S268_ORTHOTIC_NAME_FIX_THE_22 v2: every new name <= 29 characters, no collision at 20 / 27 / 29
#  across the whole shop).  Every table that keys an item by its printed name would otherwise see a
#  NEW item appear and the OLD one go dead: the count, the differences, the vouchers, the sale lines
#  (20-character clip), the purchase lines (27), the closing snapshots (29), the spine.
#
#  So: ONE table, marg_item_rename -- old_name, new_name, both clipped forms, who planned it, who
#  ticked it done in Marg, and when the server first SAW it in a stock export (F-529: never assume a
#  rename happened; read it back).  Every lane that keys a name asks THIS module, at read time:
#      resolve_map(con)   {every form of a ticked NEW name: OLD name}
#  and a new name resolves to the row keyed by the old name FOR THE COUNT AND STOCK LANES.  The
#  snapshot and the spine keep the new name as Marg prints it, with the old recorded as its alias:
#  one item, two names, never two items.
#
#  A rename that is not ticked maps NOTHING.  A rename ticked but not seen in two closing exports
#  turns amber ("Marg mein abhi dikha nahi") on Amir's board and the hub.
#
#  Standard library only.  Python 3.9 (both of the box's pythons).
# =============================================================================
import datetime as dt
import hashlib
import json
import re
import sqlite3

VERSION = "1.0"
KIT = "S404_ORTHO_STOCK_CLOSE"
SALE_CLIP, PURCHASE_CLIP, MASTER_CLIP = 20, 27, 29     # measured at S268 (F-535): sale export, purchase export, item master
AMBER_AFTER_EXPORTS = 2                                 # ticked, not seen in this many closing exports -> amber

# The owner's list, S268_ORTHOTIC_NAME_FIX_THE_22 v2 (18-Sep-2026) -- typed exactly as written there.
THE_22 = (
    ("KNEE SUPPORT HINGED L",         "KNEE SUPPORT L HINGED",         "Knee support hinged"),
    ("KNEE SUPPORT HINGED M",         "KNEE SUPPORT M HINGED",         "Knee support hinged"),
    ("KNEE SUPPORT HINGED XL",        "KNEE SUPPORT XL HINGED",        "Knee support hinged"),
    ("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT XXL HINGED",       "Knee support hinged"),
    ("L S BELT CONT GRAY UNISON L",   "LS BELT L CONT GRAY UNISON",    "LS belt"),
    ("L S BELT CONT GRAY UNISON M",   "LS BELT M CONT GRAY UNISON",    "LS belt"),
    ("L S BELT CONT GRAY UNISON XL",  "LS BELT XL CONT GRAY UNISON",   "LS belt"),
    ("L S BELT CONT GRAY UNISON XXL", "LS BELT XXL CONT GRAY UNISON",  "LS belt"),
    ("L S BELT CONT GRAY UNISON XXX", "LS BELT XXXL CONT GRAY UNISON", "LS belt"),
    ("SHOULDER IMMOBILISE UNISON L",  "SHOULDER IMMOB L UNISON",       "Shoulder immobiliser"),
    ("SHOULDER IMMOBILISE UNISON M",  "SHOULDER IMMOB M UNISON",       "Shoulder immobiliser"),
    ("SHOULDER IMMOBILISE UNISON XL", "SHOULDER IMMOB XL UNISON",      "Shoulder immobiliser"),
    ("TYNOR WRIST SPLINT LF L ELAST", "TYNOR WRIST SPL LF L ELASTIC",  "Wrist splint"),
    ("TYNOR WRIST SPLINT LF M ELAS",  "TYNOR WRIST SPL LF M ELASTIC",  "Wrist splint"),
    ("TYNOR WRIST SPLINT RT L ELAST", "TYNOR WRIST SPL RT L ELASTIC",  "Wrist splint"),
    ("TYNOR WRIST SPLINT RT M ELAST", "TYNOR WRIST SPL RT M ELASTIC",  "Wrist splint"),
    ("KNEE IMMOBILIZER UNISON L",     "KNEE IMMOBILIZER L UNISON",     "Knee immobilizer"),
    ("KNEE IMMOBILIZER UNISON XL",    "KNEE IMMOBILIZER XL UNISON",    "Knee immobilizer"),
    ("ANKLE BINDER BAMBOO L",         "ANKLE BINDER L BAMBOO",         "Ankle binder"),
    ("ANKLE BINDER BAMBOO M",         "ANKLE BINDER M BAMBOO",         "Ankle binder"),
    ("BLING PELVIC TRACTION BELT L",  "BLING PELVIC TRACT L BELT",     "Pelvic traction belt"),
    ("BLING PELVIC TRACTION BELT XL", "BLING PELVIC TRACT XL BELT",    "Pelvic traction belt"),
)

DDL = (
    "CREATE TABLE IF NOT EXISTS marg_item_rename ("
    " id INTEGER PRIMARY KEY,"
    " old_name TEXT NOT NULL UNIQUE,"          # as Marg printed it before (the count's key)
    " new_name TEXT NOT NULL UNIQUE,"          # as the owner's list says it must read (<= 29)
    " old20 TEXT NOT NULL, old27 TEXT NOT NULL, new20 TEXT NOT NULL, new27 TEXT NOT NULL,"
    " family TEXT,"
    " planned_by TEXT, planned_at TEXT NOT NULL,"
    " done_by TEXT, done_at TEXT,"             # Amir's tick: 'Marg mein badal diya'
    " verified_at TEXT, verified_md5 TEXT, verified_as_on TEXT,"   # the first closing export with the new name and not the old
    " seen_n INTEGER NOT NULL DEFAULT 0,"      # closing exports seen since the tick that did NOT carry it
    " last_seen_as_on TEXT,"
    " note TEXT)",
    "CREATE INDEX IF NOT EXISTS ix_marg_item_rename_new ON marg_item_rename(new_name)",
)


# ------------------------------------------------------------------ the name forms
def clip(name, width):
    """What Marg prints of a name in a report of that width."""
    return str(name or "")[:width].rstrip()


def sale_key(name):
    """finance_returns.norm_item(), verbatim -- the key sale_line_item.item_key is stored under."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\s+", " ", s).strip()


def pad_norm(s):
    """stock_app._pad_norm(), verbatim -- case, inner spacing, trailing dots; the purchase-line key."""
    t = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", t)


def spine_norm(s):
    """marg_spine.norm(), verbatim -- the key marg_item_name.name is stored under."""
    return re.sub(r"[^A-Z0-9]+", " ", (s or "").upper()).strip()


def forms_of(name):
    """Every spelling a lane might key this name under: exact, the two clips, and their keys."""
    n = str(name or "")
    out = []
    for f in (n, clip(n, SALE_CLIP), clip(n, PURCHASE_CLIP), sale_key(n), sale_key(clip(n, SALE_CLIP)),
              pad_norm(n), pad_norm(clip(n, PURCHASE_CLIP)), spine_norm(n)):
        if f and f not in out:
            out.append(f)
    return out


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _iso(d):
    """'26-09-2026' or '2026-09-26' -> '2026-09-26'; anything else unchanged."""
    s = str(d or "").strip()[:10]
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", s):
        return "%s-%s-%s" % (s[6:10], s[3:5], s[0:2])
    return s


# ------------------------------------------------------------------ the table
def ensure(con):
    for ddl in DDL:
        con.execute(ddl)


def check_list(pairs, all_names=()):
    """The S268 proof, re-run: every new name <= 29, no two names of the shop share a 20 / 27 / 29 clip
    once the renames are applied. Returns a list of problems (empty = fine)."""
    problems = []
    ren = {o: n for o, n, _f in pairs}
    for o, n, _f in pairs:
        if len(n) > MASTER_CLIP:
            problems.append("%s -> %s is %d characters (Marg's item master holds %d)" % (o, n, len(n), MASTER_CLIP))
    names = [ren.get(x, x) for x in all_names] if all_names else [n for _o, n, _f in pairs]
    for w in (SALE_CLIP, PURCHASE_CLIP, MASTER_CLIP):
        seen = {}
        for x in names:
            k = clip(x, w)
            if k in seen and seen[k] != x:
                problems.append("collision at %d: %r and %r" % (w, seen[k], x))
            seen.setdefault(k, x)
    return problems


def seed(con, by_user="S404", ts=None, all_names=None):
    """Insert the 22 where absent. Never overwrites a row. Refuses (returns the problems) if the list
    would collide at 20 / 27 / 29 across `all_names` (the count's 373 names when given).
    Returns (added, kept, problems)."""
    ensure(con)
    if all_names is None:
        try:
            all_names = [r[0] for r in con.execute("SELECT item FROM stock_count_item WHERE count_id=1")]
        except sqlite3.Error:
            all_names = []
    problems = check_list(THE_22, all_names)
    if problems:
        return 0, 0, problems
    ts = ts or now_iso()
    added = kept = 0
    for old, new, fam in THE_22:
        if con.execute("SELECT 1 FROM marg_item_rename WHERE old_name=?", (old,)).fetchone():
            kept += 1
            continue
        con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, family, planned_by, planned_at, note) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (old, new, clip(old, SALE_CLIP), clip(old, PURCHASE_CLIP), clip(new, SALE_CLIP), clip(new, PURCHASE_CLIP),
                     fam, by_user, ts, "S268_ORTHOTIC_NAME_FIX_THE_22 v2 (18-Sep-2026)"))
        added += 1
    return added, kept, []


def _state(r):
    if r["verified_at"]:
        return "verified"
    if r["done_at"]:
        return "amber" if int(r["seen_n"] or 0) >= AMBER_AFTER_EXPORTS else "done"
    return "planned"


STATE_HI = {"planned": "Marg mein badalna hai", "done": "Badal diya — Marg export ka intezaar",
            "amber": "Marg mein abhi dikha nahi", "verified": "Marg mein dikh gaya ✓"}
STATE_EN = {"planned": "to rename in Marg", "done": "ticked -- waiting for Marg's next stock export",
            "amber": "ticked, not yet seen in Marg", "verified": "seen in Marg's export"}


def rows(con):
    """Every rename with its state: planned | done | amber | verified."""
    ensure(con)
    out = []
    cur = con.execute("SELECT id, old_name, new_name, old20, old27, new20, new27, family, planned_by, planned_at, done_by, done_at, "
                      "verified_at, verified_md5, verified_as_on, seen_n, last_seen_as_on, note FROM marg_item_rename ORDER BY id")
    cols = [c[0] for c in cur.description]
    for t in cur.fetchall():
        r = dict(zip(cols, tuple(t)))
        r["state"] = _state(r)
        r["state_hi"] = STATE_HI[r["state"]]
        r["state_en"] = STATE_EN[r["state"]]
        out.append(r)
    return out


def summary(con):
    rs = rows(con)
    s = dict(total=len(rs), planned=0, done=0, amber=0, verified=0, kit=KIT)
    for r in rs:
        s[r["state"]] += 1
    s["all_verified"] = bool(rs) and s["verified"] == len(rs)
    return s


def done_rows(con):
    return [r for r in rows(con) if r["done_at"]]


def resolve_map(con):
    """{form of a ticked NEW name: OLD name}. Only a rename Amir has ticked maps anything."""
    out = {}
    for r in done_rows(con):
        for f in forms_of(r["new_name"]):
            out.setdefault(f, r["old_name"])
    return out


def resolve(con, name):
    """The OLD name a NEW name (or its clipped form) resolves to; the name itself otherwise."""
    m = resolve_map(con)
    for f in forms_of(name):
        if f in m:
            return m[f]
    return name


def aliases_of(con, old_name):
    """The NEW names (every form) that resolve to this OLD name -- [] when it has no ticked rename."""
    for r in done_rows(con):
        if r["old_name"] == old_name:
            return forms_of(r["new_name"])
    return []


# ------------------------------------------------------------------ Amir's tick
def _audit(con, who, action, detail):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("marg_item_rename", None, action, None, json.dumps(detail, ensure_ascii=False), who, now_iso()))
    except sqlite3.Error:
        pass


def _follow(con, r, who, ts):
    """What the rest of the estate must know once Amir has renamed: the section map (the new name
    inherits the old name's section), the item spine's name table (kind 'alias' on the OLD item),
    and the S229 rename task on Amir's salt page (closed -- the same rename, older spelling)."""
    notes = []
    try:
        import section_map                                    # noqa: PLC0415 -- beside this file
        ok, msg = section_map.inherit(con, r["old_name"], r["new_name"], by_user=who, ts=ts)
        notes.append("section: %s" % msg)
    except Exception as e:                                    # noqa: BLE001
        notes.append("section map not updated: %s" % str(e)[:80])
    try:
        item_id = None
        x = con.execute("SELECT item_id FROM marg_item_name WHERE name=? AND kind='canonical' AND active=1",
                        (spine_norm(r["old_name"]),)).fetchone()
        if x:
            item_id = int(x[0])
        else:
            x = con.execute("SELECT item_id FROM marg_item WHERE canonical_raw=? OR canonical=?", (r["old_name"], spine_norm(r["old_name"]))).fetchone()
            item_id = int(x[0]) if x else None
        if item_id is not None:
            nn = spine_norm(r["new_name"])
            con.execute("INSERT OR IGNORE INTO marg_item_name (name, item_id, name_raw, kind, active, note, source, created_at) VALUES (?,?,?,?,1,?,?,?)",
                        (nn, item_id, r["new_name"], "alias", "renamed in Marg by %s (S404, D620); the old name stays the item" % who, "S404", ts))
            con.execute("UPDATE marg_item_name SET kind='alias', active=1 WHERE name=? AND item_id=?", (nn, item_id))
            con.execute("UPDATE marg_item_name SET active=0, note=COALESCE(note,'')||' | superseded by the S268 v2 list (S404)' "
                        "WHERE item_id=? AND kind='pending_rename' AND name<>?", (item_id, nn))
            notes.append("spine alias on item %d" % item_id)
        else:
            notes.append("no spine item for the old name")
    except sqlite3.Error as e:
        notes.append("spine name table not updated: %s" % str(e)[:80])
    try:
        n = con.execute("UPDATE marg_task SET status='done', done_by=?, done_at=?, answer=?, "
                        "source=COALESCE(source,'')||' | closed by the S404 tick' WHERE kind='rename' AND a=? AND status='open'",
                        (who, ts, r["new_name"], r["old_name"])).rowcount
        if n:
            notes.append("S229 rename task closed")
    except sqlite3.Error:
        pass
    return notes


def tick(con, old_name, who, ts=None):
    """'Marg mein badal diya' -- Amir's one tick. Idempotent: a second tick answers already=True and
    writes nothing. Returns (ok, message, row)."""
    ensure(con)
    ts = ts or now_iso()
    rs = [r for r in rows(con) if r["old_name"] == old_name or r["new_name"] == old_name]
    if not rs:
        return False, "that name is not on the rename list", None
    r = rs[0]
    if r["done_at"]:
        return True, "already", r
    con.execute("UPDATE marg_item_rename SET done_by=?, done_at=? WHERE id=?", (who, ts, r["id"]))
    notes = _follow(con, r, who, ts)
    _audit(con, who, "rename_ticked", dict(old=r["old_name"], new=r["new_name"], notes=notes))
    return True, "ticked", [x for x in rows(con) if x["id"] == r["id"]][0]


def untick(con, old_name, who, ts=None):
    """Taken back -- only while the rename has not been seen in Marg (a verified rename is a fact)."""
    ensure(con)
    ts = ts or now_iso()
    rs = [r for r in rows(con) if r["old_name"] == old_name or r["new_name"] == old_name]
    if not rs:
        return False, "that name is not on the rename list", None
    r = rs[0]
    if r["verified_at"]:
        return False, "Marg's export already carries the new name -- it cannot be taken back", r
    if not r["done_at"]:
        return True, "already", r
    con.execute("UPDATE marg_item_rename SET done_by=NULL, done_at=NULL, seen_n=0, last_seen_as_on=NULL WHERE id=?", (r["id"],))
    try:
        con.execute("UPDATE marg_item_name SET active=0, note=COALESCE(note,'')||' | tick taken back' WHERE name_raw=? AND kind='alias'", (r["new_name"],))
    except sqlite3.Error:
        pass
    _audit(con, who, "rename_untick", dict(old=r["old_name"], new=r["new_name"]))
    return True, "taken back", [x for x in rows(con) if x["id"] == r["id"]][0]


# ------------------------------------------------------------------ the verification (F-529: read it back)
def names_md5(names, as_on):
    h = hashlib.md5()
    h.update(json.dumps([str(as_on or "")] + sorted(str(n) for n in names)).encode("utf-8"))
    return h.hexdigest()


def verify_closing(con, names, as_on, md5=None, source="", ts=None, captured=None):
    """ONE closing-stock export has arrived (names = every item it lists, as_on = its date; captured =
    the moment it was taken, ISO, when the door knows it). For every rename ticked before it: the export
    carrying the NEW name and not the OLD one marks it verified (with the export's md5); an export still
    carrying the old name counts as a sighting that did not show it (seen_n, one per as_on day).
    An export dated -- or captured -- before the tick cannot carry it and is not counted.
    Returns dict(verified=[..], seen=[..])."""
    ensure(con)
    ts = ts or now_iso()
    day = _iso(as_on)
    md5 = md5 or names_md5(names, day)
    have = set(str(n or "").strip() for n in names)
    have29 = {clip(n, MASTER_CLIP) for n in have}
    out = dict(verified=[], seen=[], as_on=day, md5=md5)
    for r in rows(con):
        if not r["done_at"] or r["verified_at"]:
            continue
        if day and day < str(r["done_at"])[:10]:
            continue                                          # an export from before the tick cannot carry it
        if captured and str(captured)[:19] < str(r["done_at"])[:19]:
            continue                                          # taken before the tick: the same
        new_in = r["new_name"] in have or clip(r["new_name"], MASTER_CLIP) in have29
        old_in = r["old_name"] in have
        if new_in and not old_in:
            con.execute("UPDATE marg_item_rename SET verified_at=?, verified_md5=?, verified_as_on=? WHERE id=?", (ts, md5, day, r["id"]))
            out["verified"].append(r["old_name"])
            _audit(con, source or "export", "rename_verified", dict(old=r["old_name"], new=r["new_name"], as_on=day, md5=md5))
        elif day and day != (r["last_seen_as_on"] or ""):
            con.execute("UPDATE marg_item_rename SET seen_n=seen_n+1, last_seen_as_on=? WHERE id=?", (day, r["id"]))
            out["seen"].append(r["old_name"])
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--status":
        c = sqlite3.connect("file:%s?mode=ro" % sys.argv[2], uri=True)
        for r in rows(c):
            print("%-9s %-31s -> %-30s %s" % (r["state"], r["old_name"], r["new_name"], r["done_by"] or ""))
        print(summary(c))
    else:
        print("usage: item_alias.py --status /root/finance/finance.db")
