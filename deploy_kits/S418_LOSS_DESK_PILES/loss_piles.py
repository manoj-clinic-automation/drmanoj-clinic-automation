#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  loss_piles.py  ·  v1.0  ·  kit S418_LOSS_DESK_PILES  ·  Session 283 (Sanjeevni)  ·  D631 / F-641
#
#  THE OWNER'S LOSS DESK AS FOUR PILES -- the owner, 26-Sep-2026, on the live desk: "These products were kept
#  somewhere else and were not counted. Why make such a long path? I take it, it is there, it should be accepted
#  back into the system as it is. It is a very long list, very difficult to pursue ... it is not curated for easy
#  redressal for me."  Small shortages after six months without a proper count are normal shop loss and are
#  written off as a group, documented, never line by line.
#
#  Every open line of the round (medicines and consumables; the orthotics stay on S404's section) sits in exactly
#  ONE pile, the system's suggestion first, the owner's move over it:
#     with_me   With me / back in store   ONE tap Accept back -> EXPLAINED, cause FOUND, shelf corrected to Marg's
#     writeoff  Write off as normal loss  three documented groups (within allowance / small real gap / clinic
#                                         consumption) + his own moves; ONE tap (confirmed for 10 s) writes the
#                                         pile off and makes Amir's vouchers for exactly those lines
#     pursue    Pursue                    every real gap of Rs 1,000 or more at MRP; the sheet for Darpan (the
#                                         existing S228 sheet, unchanged); open with RECOVER until settled
#     recount   Recount                   the count cannot be right as written, or 50+ units off; Darpan's
#                                         'Phir se gino' box; his figure replaces the shelf and the line re-piles
#
#  THE FIVE TOTALS ARE DEFINED HERE ONCE (totals()) and read by the desk, the hub's status card and the record
#  PDF -- one figure everywhere (F-641: the desk said Rs 84,332 and the hub Rs 64,338 for the same lines).
#
#  EVERY RULING IS A SETTING (the owner: "so that we can alter them without going back to the code"), in the
#  `setting` table, every change audited and printed in the record. The piles re-compute from the settings on
#  every read; changing a setting never decides a line by itself.
#
#  THE SHELF LAYER: stock_shelf_fix holds a corrected shelf figure per item (Accept back = Marg's figure; a
#  recount = Darpan's figure). apply_fixes() lays it over the report's lines at read time, like the S299 swaps:
#  the count itself and its seal (stock_diff quantities) are never touched.
#
#  No stock_app import at module level: stock_app imports this file while it is itself being imported.
# =============================================================================
import datetime as dt
import hashlib
import json

VERSION = "1.0"
KIT = "S418_LOSS_DESK_PILES"

PILES = (("with_me", "With me / back in store"),
         ("writeoff", "Write off as normal loss"),
         ("pursue", "Pursue"),
         ("recount", "Recount"))
PILE_TITLE = dict(PILES)
GROUPS = (("allowance", "Within the allowance",
           "short within what an item of this turnover is expected to lose (sold volume, loose selling)"),
          ("small", "Small real gap",
           "short beyond the allowance, but under the small-gap ceiling at MRP -- a real loss, written off and recorded"),
          ("consume", "Clinic consumption",
           "procedure consumables (blades, gloves, syringes ...) used in the clinic, never billed"),
          ("owner", "Your choice",
           "a line you moved into this pile yourself"),
          ("earlier", "Written off before the piles",
           "decided line by line on the earlier desk"))
GROUP_TITLE = {k: t for k, t, _b in GROUPS}
GROUP_BLURB = {k: b for k, _t, b in GROUPS}

# ---- the settings (3b). kind: choice | rupees | units | int | text. `seed` is what the kit writes when the key is absent.
SETTINGS = (
    dict(key="stock.allowance_scale", label="Allowance width", kind="choice", default="1", seed="2",
         choices=(("1", "normal"), ("2", "wide"), ("3", "very wide")),
         hint="How much shortage counts as normal shop loss. The width is per item and grows with how much it sells and "
              "how often a strip is cut. Wide for count #1 (six months without a proper count)."),
    dict(key="stock.pursue_floor_p", label="Pursue floor (at MRP)", kind="rupees", default="100000", seed="100000",
         hint="A real gap at or above this starts in Pursue -- asked about, never written off by itself."),
    dict(key="stock.small_gap_ceiling_p", label="Small-gap ceiling (at MRP)", kind="rupees", default="", seed=None,
         hint="A real gap below this is written off with the pile, recorded as a real loss. Blank = the same as the "
              "pursue floor; it may be set lower (a gap between the two then starts in Pursue)."),
    dict(key="stock.recount_trigger", label="Recount trigger (units)", kind="units", default="50", seed="50",
         hint="A surplus, or a shortage, of this many units or more starts in Recount -- count again before deciding."),
    dict(key="stock.voucher_batch", label="Lines per Marg voucher", kind="int", default="6", seed="6", lo=1, hi=8,
         hint="How many lines Amir enters on one Marg voucher (Marg prints six to eight)."),
    dict(key="stock.accept_back_by", label="Who may tap Accept back", kind="choice", default="owner", seed="owner",
         choices=(("owner", "only you"), ("owner,darpan", "you and Darpan")),
         hint="Accept back closes a line as 'it is here, not lost'."),
    dict(key="stock.consume_auto", label="Consumables with the pile", kind="choice", default="1", seed="1",
         choices=(("1", "on"), ("0", "off")),
         hint="Blades, gloves, syringes ... written off as clinic consumption with the write-off pile."),
    dict(key="stock.rolling_section_items", label="Weekly rolling count: items per section", kind="int", default="90",
         seed="90", lo=10, hi=500, hint="Read by the weekly rolling count (next build)."),
    dict(key="stock.rolling_day", label="Weekly rolling count: start day", kind="choice", default="Monday", seed="Monday",
         choices=tuple((d, d) for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")),
         hint="Read by the weekly rolling count (next build)."),
)
SETTING_BY_KEY = {s["key"]: s for s in SETTINGS}

SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_pile_move (
  id        INTEGER PRIMARY KEY,          -- S418: the owner moved a line to a pile; append-only, the newest wins
  count_id  INTEGER NOT NULL,             -- the ROOT count
  item      TEXT NOT NULL,
  pile      TEXT NOT NULL,                -- with_me | writeoff | pursue | recount | auto (back to the suggestion)
  by_user   TEXT, at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pile_move ON stock_pile_move(count_id, item);
CREATE TABLE IF NOT EXISTS stock_shelf_fix (
  id        INTEGER PRIMARY KEY,          -- S418: a corrected shelf figure for one item of a count; append-only, the newest wins
  count_id  INTEGER NOT NULL,
  item      TEXT NOT NULL,
  qty       INTEGER NOT NULL,             -- units now on the shelf
  source    TEXT NOT NULL,                -- accept_back (= Marg's figure) | recount (Darpan's figure)
  note      TEXT, by_user TEXT, at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shelf_fix ON stock_shelf_fix(count_id, item);
CREATE TABLE IF NOT EXISTS stock_recount_ask (
  id        INTEGER PRIMARY KEY,          -- S418: the owner asked Darpan to count one item again
  count_id  INTEGER NOT NULL,
  item      TEXT NOT NULL,
  asked_by  TEXT, asked_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recount_ask ON stock_recount_ask(count_id, item);
CREATE TABLE IF NOT EXISTS stock_pile_arm (
  id        INTEGER PRIMARY KEY,          -- S418: 'Write off this pile' pressed once -- the 10-second confirm
  count_id  INTEGER NOT NULL,
  token     TEXT NOT NULL,
  items     TEXT NOT NULL,                -- JSON: the pile as it stood when armed
  by_user   TEXT, at TEXT NOT NULL, used_at TEXT
);
CREATE TABLE IF NOT EXISTS stock_writeoff_run (
  id        INTEGER PRIMARY KEY,          -- S418: one 'Write off this pile' -- FROZEN, the documented groups
  count_id  INTEGER NOT NULL,
  at        TEXT NOT NULL, by_user TEXT,
  lines_n   INTEGER NOT NULL, mrp_p INTEGER NOT NULL, cost_p INTEGER NOT NULL, unpriced INTEGER NOT NULL,
  groups    TEXT NOT NULL,                -- JSON {group: [ {item, short_units, short_text, mrp_p, cost_p, why}, ... ]}
  settings  TEXT NOT NULL,                -- JSON: the rules in force when it was written off
  round_no  INTEGER,                      -- the Marg voucher round made in the same call
  md5       TEXT NOT NULL
);
"""
ARM_SECONDS = 10
AUDIT_TABLE = "stock_pile"


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file, already loaded
    return stock_app


_TABLES = ("stock_pile_move", "stock_shelf_fix", "stock_recount_ask", "stock_pile_arm", "stock_writeoff_run")


def ensure(con):
    """Create the desk's tables -- only when one is missing. executescript COMMITs whatever the caller has open, and
    this is reached from the report's read path (apply_fixes), so it must be a no-op once the tables exist."""
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)"
                                      % ",".join("?" * len(_TABLES)), _TABLES)}
    if len(have) < len(_TABLES):
        con.executescript(SCHEMA)


def _audit(con, root, action, after, who, before=None):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    (AUDIT_TABLE, int(root), action, json.dumps(before) if before is not None else None,
                     json.dumps(after, sort_keys=True), who or "", now_iso()))
    except Exception:                                         # noqa: BLE001 -- the row it describes is the record that counts
        pass


# ------------------------------------------------------------------ settings
def setting_raw(con, key):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and str(r[0]).strip() != "":
            return str(r[0]).strip()
    except Exception:                                         # noqa: BLE001
        pass
    return None


def settings(con):
    """The rules in force, typed, with where each came from."""
    out = {}
    for s in SETTINGS:
        raw = setting_raw(con, s["key"])
        out[s["key"]] = raw if raw is not None else s["default"]
    def num(k, dflt):
        try:
            return int(float(out[k]))
        except (TypeError, ValueError):
            return dflt
    floor = num("stock.pursue_floor_p", 100000)
    ceil_raw = out["stock.small_gap_ceiling_p"]
    try:
        ceiling = int(float(ceil_raw)) if str(ceil_raw).strip() != "" else floor
    except (TypeError, ValueError):
        ceiling = floor
    try:
        scale = float(out["stock.allowance_scale"])
    except (TypeError, ValueError):
        scale = 1.0
    who = [w.strip() for w in str(out["stock.accept_back_by"] or "owner").split(",") if w.strip()]
    return dict(raw=out, allowance_scale=scale, pursue_floor_p=floor, small_gap_ceiling_p=min(ceiling, floor),
                ceiling_follows_floor=(str(ceil_raw).strip() == ""), recount_trigger=max(1, num("stock.recount_trigger", 50)),
                voucher_batch=max(1, min(8, num("stock.voucher_batch", 6))), accept_back_by=who,
                consume_auto=str(out["stock.consume_auto"]).strip() not in ("0", "off", "no", "false"),
                rolling_section_items=num("stock.rolling_section_items", 90), rolling_day=out["stock.rolling_day"])


def _rs(p_):
    return _sa()._loss_rs(p_) if p_ is not None else "-"


def settings_view(con):
    st = settings(con)
    rows = []
    for s in SETTINGS:
        raw = setting_raw(con, s["key"])
        v = raw if raw is not None else s["default"]
        shown = v
        if s["kind"] == "rupees":
            shown = ("= pursue floor (%s)" % _rs(st["pursue_floor_p"])) if str(v).strip() == "" else _rs(int(float(v)))
        elif s["kind"] == "choice":
            shown = dict(s["choices"]).get(str(v), str(v))
        rows.append(dict(key=s["key"], label=s["label"], kind=s["kind"], value=v, shown=shown, hint=s["hint"],
                         choices=[dict(v=a, t=b) for a, b in s.get("choices", ())], set=(raw is not None),
                         rupees=(None if s["kind"] != "rupees" or str(v).strip() == "" else int(float(v)) // 100)))
    return rows


def set_setting(con, key, value, who, root=0):
    """Validate, store, audit. Returns (ok, message)."""
    s = SETTING_BY_KEY.get(key)
    if not s:
        return False, "Not a setting of this desk."
    v = "" if value is None else str(value).strip()
    if s["kind"] == "choice":
        if v not in [a for a, _b in s["choices"]]:
            return False, "Choose one of: %s." % ", ".join(b for _a, b in s["choices"])
    elif s["kind"] == "rupees":
        if v == "" and key == "stock.small_gap_ceiling_p":
            pass
        else:
            try:
                r = float(v.replace(",", "").replace("Rs", "").strip())
            except ValueError:
                return False, "Type an amount in rupees."
            if r < 0 or r > 1000000:
                return False, "Type an amount in rupees."
            v = str(int(round(r * 100)))
    elif s["kind"] in ("units", "int"):
        try:
            n = int(float(v))
        except ValueError:
            return False, "Type a whole number."
        lo, hi = s.get("lo", 1), s.get("hi", 100000)
        if n < lo or n > hi:
            return False, "Between %d and %d." % (lo, hi)
        v = str(n)
    old = setting_raw(con, key)
    if (old or "") == v:
        return True, "No change."
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                (key, v, "S418 loss desk setting: %s" % s["label"]))
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("setting", int(root or 0), "stock_setting", json.dumps(dict(key=key, value=old)),
                     json.dumps(dict(key=key, value=v, label=s["label"])), who or "", now_iso()))
    except Exception:                                         # noqa: BLE001
        pass
    con.commit()
    return True, "%s set." % s["label"]


def seed(con, who="S418"):
    """INSERT the kit's defaults for every key that is not there yet; never overwrite. Returns the keys written."""
    wrote = []
    for s in SETTINGS:
        if s["seed"] is None or setting_raw(con, s["key"]) is not None:
            continue
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)",
                    (s["key"], s["seed"], "S418 loss desk setting: %s (seeded)" % s["label"]))
        try:
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("setting", 0, "stock_setting", json.dumps(dict(key=s["key"], value=None)),
                         json.dumps(dict(key=s["key"], value=s["seed"], label=s["label"], seeded=True)), who, now_iso()))
        except Exception:                                     # noqa: BLE001
            pass
        wrote.append(s["key"])
    con.commit()
    return wrote


def settings_log(con):
    out = []
    try:
        for r in con.execute("SELECT before_json, after_json, by_whom, at FROM audit_log WHERE table_name='setting' AND action='stock_setting' ORDER BY id"):
            b, a = json.loads(r[0] or "{}"), json.loads(r[1] or "{}")
            s = SETTING_BY_KEY.get(a.get("key"))
            if not s:
                continue
            out.append(dict(key=a.get("key"), label=s["label"], old=b.get("value"), new=a.get("value"),
                            old_text=_shown(s, b.get("value")), new_text=_shown(s, a.get("value")),
                            by=r[2] or "", at=r[3], at_text=_sa()._r_stamp(r[3]) + " IST", seeded=bool(a.get("seeded"))))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def _shown(s, v):
    if v is None:
        return "not set"
    if s["kind"] == "rupees":
        return "= pursue floor" if str(v).strip() == "" else _rs(int(float(v)))
    if s["kind"] == "choice":
        return dict(s["choices"]).get(str(v), str(v))
    return str(v)


# ------------------------------------------------------------------ the shelf layer (read time)
def fixes(con, root):
    """item -> the newest shelf fix of this count."""
    out = {}
    try:
        ensure(con)
        for r in con.execute("SELECT item, qty, source, note, by_user, at FROM stock_shelf_fix WHERE count_id=? ORDER BY id", (int(root),)):
            out[r[0]] = dict(qty=int(r[1]), source=r[2], note=r[3] or "", by=r[4] or "", at=r[5])
    except Exception:                                         # noqa: BLE001
        return {}
    return out


def apply_fixes(con, root, diffs):
    """Lay the corrected shelf figures over the report's lines (in place). The count-day figures stay on the
    line (counted_count_day, diff_count_day, mrp_p_count_day, cost_p_count_day). Never raises."""
    try:
        fx = fixes(con, root)
        if not fx:
            return 0
        sa = _sa()
        st = sa._stock_settings(con)
        n = 0
        for x in diffs:
            f = fx.get(x["item"])
            if not f:
                continue
            x.setdefault("diff_count_day", x["diff"])
            x.setdefault("mrp_p_count_day", x.get("mrp_p"))
            x.setdefault("cost_p_count_day", x.get("cost_p"))
            x["counted_count_day"] = x["counted"]
            base = int(f["qty"]) - int(x["marg"])
            d0 = int(x["diff_count_day"] or 0)
            sw = int(x.get("swapped") or 0)
            rem = base
            if sw and base and ((base < 0) == (d0 < 0)):
                k = min(abs(base), sw)
                rem = base + k if base < 0 else base - k
            x["counted"] = int(f["qty"])
            x["diff"] = rem
            if rem:
                mv, src = sa._price_value_p(con, x["item"], rem, st)
                x["mrp_p"], x["mrp_source"] = mv, src
                x["cost_p"] = sa._value_p(con, x["item"], rem)
            else:
                x["mrp_p"] = 0 if x.get("mrp_p_count_day") is not None else None
                x["cost_p"] = 0 if x.get("cost_p_count_day") is not None else None
            x["shelf_fix"] = dict(f, at_text=sa._r_stamp(f["at"]) + " IST")
            if rem == 0 and not x.get("word"):
                x["word"] = dict(action="EXPLAINED", swap=True, by=f["by"], at=f["at"], at_text=sa._r_stamp(f["at"]) + " IST",
                                 label=("back in store -- shelf = Marg" if f["source"] == "accept_back" else "recounted -- the shelf agrees with Marg"),
                                 note=f["note"])
            n += 1
        return n
    except Exception:                                         # noqa: BLE001 -- a layer is never worth a broken report
        return 0


# ------------------------------------------------------------------ the piles
def _moves(con, root):
    out = {}
    for r in con.execute("SELECT item, pile, by_user, at FROM stock_pile_move WHERE count_id=? ORDER BY id", (int(root),)):
        if r[1] == "auto":
            out.pop(r[0], None)
        else:
            out[r[0]] = dict(pile=r[1], by=r[2] or "", at=r[3])
    return out


def _asks(con, root):
    out = {}
    for r in con.execute("SELECT item, asked_by, asked_at FROM stock_recount_ask WHERE count_id=? ORDER BY id", (int(root),)):
        out[r[0]] = dict(by=r[1] or "", at=r[2])
    return out


def _runs_by_item(con, root):
    out = {}
    for r in con.execute("SELECT id, at, groups FROM stock_writeoff_run WHERE count_id=? ORDER BY id", (int(root),)):
        try:
            g = json.loads(r[2])
        except ValueError:
            continue
        for grp, rows in g.items():
            for l in rows:
                out[l["item"]] = dict(group=grp, run=int(r[0]), at=r[1])
    return out


def _shares_by_item(con, root):
    out = {}
    try:
        for r in con.execute("SELECT id, no, lines, made_at FROM stock_loss_share WHERE count_id=? ORDER BY no", (int(root),)):
            for l in json.loads(r[2]):
                out.setdefault(l["item"], dict(no=int(r[1]), id=int(r[0]), at=r[3]))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def _claims_by_item(con, root):
    sa = _sa()
    out = {}
    if not getattr(sa, "CLAIM_QUEUE_OK", False):
        return out
    try:
        for c in sa._cq.lines(con, int(root), limit=500):
            out[c["item"]] = c
    except Exception:                                         # noqa: BLE001
        pass
    return out


def is_ortho(con, x):
    sa = _sa()
    return x.get("lane") == "ortho" or sa._item_section(con, x) == "Orthotics"


def _is_consumable_line(con, x):
    sa = _sa()
    return bool(x.get("consumable")) or x.get("lane") == "consume" or sa._item_section(con, x) == "Consumables"


def _loss(x, key="mrp_p"):
    v = x.get(key)
    return (-int(v)) if (v is not None and int(v) < 0) else (0 if v is not None else None)


def _allow_at(con, x, scale, st, cache):
    sa = _sa()
    it = x["item"]
    if it not in cache:
        cache[it] = sa._price_p(con, it, st)[0]
    return sa._allowance_units(x.get("sold_fy") or 0, x.get("loose_fy") or 0, x.get("pack") or 1, cache[it],
                               dict(st, allowance_scale=scale))


def _suggest(con, x, S, st, scale, cache, recounted):
    """(pile, group, why) for one OPEN shortage with no move of the owner's on it."""
    sa = _sa()
    w = (x.get("word") or {}).get("action")
    short = -int(x["diff"])
    pack = int(x.get("pack") or 1)
    if w == "PARKED":
        return "with_me", None, "you had it set aside -- kept elsewhere, not counted"
    if w == "RECOUNT":
        return "recount", None, "you sent it to be counted again"
    if S["consume_auto"] and _is_consumable_line(con, x):
        return "writeoff", "consume", "a procedure consumable -- used in the clinic, never billed"
    if not recounted:
        if x.get("lane") == "recount":
            return "recount", None, "the count cannot be right as written -- count it again"
        if short >= S["recount_trigger"]:
            return "recount", None, "%s short (%d units or more) -- count it again before deciding" % (sa._qw(short, pack), S["recount_trigger"])
    allow = _allow_at(con, x, scale, st, cache)
    if short <= allow:
        return "writeoff", "allowance", "short %s, within the allowance of %s for how much it sells" % (sa._qw(short, pack), sa._qw(allow, pack))
    v = _loss(x)
    if v is None:
        v = _loss(x, "cost_p")
    if v is None:
        return "pursue", None, "no price on record -- ask before writing it off"
    if v < S["small_gap_ceiling_p"]:
        return "writeoff", "small", "a real gap of %s, under %s" % (_rs(v), _rs(S["small_gap_ceiling_p"]))
    if v >= S["pursue_floor_p"]:
        return "pursue", None, "%s at MRP -- %s or more is worth asking about" % (_rs(v), _rs(S["pursue_floor_p"]))
    return "pursue", None, "%s at MRP -- above the small-gap ceiling of %s" % (_rs(v), _rs(S["small_gap_ceiling_p"]))


def _wo_group(con, x, S, st, scale, cache):
    """The documented group of a line the owner moved into the write-off pile."""
    sa = _sa()
    if _is_consumable_line(con, x):
        return "consume"
    if -int(x["diff"]) <= _allow_at(con, x, scale, st, cache):
        return "allowance"
    v = _loss(x)
    if v is None:
        v = _loss(x, "cost_p")
    if v is not None and v < S["small_gap_ceiling_p"]:
        return "small"
    return "owner"


def classify(con, d, S=None, scale=None):
    """Every line of the round that belongs on the desk, with its bucket. One pass; the desk, the hub, the record
    and the preview all call this. Returns (lines, over, skipped_ortho)."""
    sa = _sa()
    ensure(con)
    S = S or settings(con)
    st = sa._stock_settings(con)
    scale = S["allowance_scale"] if scale is None else scale
    root = d["count_id"]
    moves, asks, fx = _moves(con, root), _asks(con, root), fixes(con, root)
    runs, shares = _runs_by_item(con, root), _shares_by_item(con, root)
    cache, lines, over, skipped = {}, [], [], 0
    for x in d["differences"]:
        if is_ortho(con, x):
            skipped += 1
            continue
        item = x["item"]
        w = x.get("word") or {}
        act = w.get("action")
        rem = int(x["diff"] or 0)
        d0 = int(x.get("diff_count_day", rem) or 0)
        f = fx.get(item)
        ask = asks.get(item)
        recounted = bool(f and f["source"] == "recount" and (not ask or str(f["at"]) >= str(ask["at"])))
        pack = int(x.get("pack") or 1)
        mv = moves.get(item)
        if mv and mv["pile"] == "recount" and recounted and str(f["at"]) >= str(mv["at"]):
            mv = None                                           # his figure came after the move: the line re-piles itself
        base = dict(item=item, packing=x.get("packing") or "", pack=pack, marg=int(x["marg"]), counted=int(x["counted"]),
                    diff=rem, diff_count_day=d0, short_units=(-rem if rem < 0 else 0),
                    short_text=(sa._qw(-rem, pack) if rem < 0 else ""),
                    mrp_p=_loss(x), cost_p=_loss(x, "cost_p"),
                    mrp_day_p=_loss(dict(mrp_p=x.get("mrp_p_count_day", x.get("mrp_p")))),
                    cost_day_p=_loss(dict(cost_p=x.get("cost_p_count_day", x.get("cost_p"))), "cost_p"),
                    short_day_text=(sa._qw(-d0, pack) if d0 < 0 else ""),
                    consumable=_is_consumable_line(con, x), moved=None, sent=None, asked=None, recount=None,
                    word=act or "", word_by=w.get("by") or "", word_at=w.get("at") or "", life=x.get("life"),
                    swapped=int(x.get("swapped") or 0))
        if f:
            base["recount"] = dict(qty=f["qty"], source=f["source"], by=f["by"], at=f["at"],
                                   at_text=sa._r_stamp(f["at"]) + " IST", qty_text=sa._qw(f["qty"], pack),
                                   counted_day=int(x.get("counted_count_day", x["counted"])))
        if act == "WRITE_OFF":
            if d0 >= 0 and rem >= 0:
                continue                                        # a surplus written down: not a loss line
            r = runs.get(item)
            base.update(bucket="written_off", pile=None, group=(r or {}).get("group") or "earlier",
                        why="written off " + (sa._r_stamp(w.get("at")) + " IST" if w.get("at") else ""))
            lines.append(base)
            continue
        if act in ("EXPLAINED", "MARG_FIX") or rem == 0:
            if d0 >= 0:
                continue                                        # a surplus explained: never a loss line
            base.update(bucket="back", pile=None, group=None,
                        why=(w.get("label") or "explained -- no loss"))
            lines.append(base)
            continue
        if rem > 0:
            if mv and mv["pile"] == "recount":
                pile, why = "recount", "moved here by you"
                base["moved"] = mv
            elif not f and (x.get("lane") == "recount" or rem >= S["recount_trigger"] or act == "RECOUNT"):
                pile, why = "recount", ("the count cannot be right as written -- count it again" if x.get("lane") == "recount"
                                        else "%s more on the shelf than Marg -- count it again" % sa._qw(rem, pack))
            else:
                over.append(dict(base, bucket="over", pile=None, group=None,
                                 over_text=sa._qw(rem, pack),
                                 why=("recounted: %s more than Marg -- never a loss" % sa._qw(rem, pack)) if f
                                 else "more on the shelf than Marg -- never a loss"))
                continue
            base.update(bucket="recount", pile="recount", group=None, why=why, over_text=sa._qw(rem, pack),
                        asked=(dict(ask, at_text=sa._r_stamp(ask["at"]) + " IST") if ask and not recounted else None))
            lines.append(base)
            continue
        # an OPEN shortage -- the owner's move first, then his earlier word, then the system's suggestion
        if mv:
            pile, group, why = mv["pile"], None, "moved here by you"
            base["moved"] = mv
            if pile == "writeoff":
                group = _wo_group(con, x, S, st, scale, cache)
        elif act == "RECOVER":
            pile, group, why = "pursue", None, "you marked it to pursue"
        else:
            pile, group, why = _suggest(con, x, S, st, scale, cache, recounted)
        if recounted and pile != "recount":
            why = "recounted by %s: %s on the shelf -- %s" % (f["by"] or "Darpan", sa._qw(f["qty"], pack), why)
        base.update(bucket=pile, pile=pile, group=group, why=why)
        if pile == "pursue":
            base["sent"] = shares.get(item)
        if pile == "recount":
            base["asked"] = dict(ask, at_text=sa._r_stamp(ask["at"]) + " IST") if (ask and not recounted) else None
        lines.append(base)
    return lines, over, skipped


def _sum(ls, day=False):
    k1, k2 = ("mrp_day_p", "cost_day_p") if day else ("mrp_p", "cost_p")
    return dict(n=len(ls), mrp_p=sum(l[k1] or 0 for l in ls), cost_p=sum(l[k2] or 0 for l in ls),
                unpriced=sum(1 for l in ls if l[k1] is None))


def totals_of(lines):
    """THE FIVE TOTALS -- defined here, once. Every desk line is in exactly one bucket:
         back        back in store / explained -- valued at the count day (what did not go missing)
         written_off written off -- by group (allowance / small / consume / owner / earlier)
         with_me, writeoff, pursue, recount -- the four piles still open
       open  = with_me + writeoff + pursue + recount
       short = open + back + written_off   (every desk shortage of the round)"""
    by = {}
    for l in lines:
        by.setdefault(l["bucket"], []).append(l)
    back = _sum(by.get("back", []), day=True)
    wo = _sum(by.get("written_off", []))
    wo["groups"] = {g: _sum([l for l in by.get("written_off", []) if l["group"] == g]) for g, _t, _b in GROUPS}
    piles = {}
    for k, _t in PILES:
        piles[k] = _sum(by.get(k, []))
    piles["writeoff"]["groups"] = {g: _sum([l for l in by.get("writeoff", []) if l["group"] == g]) for g, _t, _b in GROUPS}
    piles["pursue"]["sent"] = sum(1 for l in by.get("pursue", []) if l.get("sent"))
    piles["recount"]["asked"] = sum(1 for l in by.get("recount", []) if l.get("asked"))
    open_ = dict(n=sum(piles[k]["n"] for k, _t in PILES), mrp_p=sum(piles[k]["mrp_p"] for k, _t in PILES),
                 cost_p=sum(piles[k]["cost_p"] for k, _t in PILES), unpriced=sum(piles[k]["unpriced"] for k, _t in PILES))
    short = dict(n=open_["n"] + back["n"] + wo["n"], mrp_p=open_["mrp_p"] + back["mrp_p"] + wo["mrp_p"],
                 cost_p=open_["cost_p"] + back["cost_p"] + wo["cost_p"], unpriced=open_["unpriced"] + back["unpriced"] + wo["unpriced"])
    return dict(open=open_, back=back, written_off=wo, pursue=piles["pursue"], recount=piles["recount"],
                with_me=piles["with_me"], writeoff=piles["writeoff"], short=short)


def totals(con, d):
    """The one figure the desk, the hub's status card and the record PDF all print."""
    lines, _o, _s = classify(con, d)
    return totals_of(lines)


def preview(con, d, S):
    """The allowance dial: what each width would do (nothing is decided by it). The width moves lines between
    'small real gap' (or Pursue / Recount) and 'within the allowance' -- into_n/out_n count the lines that would
    enter / leave the allowance group; pile_in_n/pile_out_n the lines that would enter / leave the write-off pile."""
    now_lines, _o, _s = classify(con, d, S)
    allow_now = {l["item"] for l in now_lines if l["bucket"] == "writeoff" and l["group"] == "allowance"}
    pile_now = {l["item"] for l in now_lines if l["bucket"] == "writeoff"}
    val = {l["item"]: (l["mrp_p"] or 0) for l in now_lines}
    out = []
    for sc, name in (("1", "normal"), ("2", "wide"), ("3", "very wide")):
        ls, _o, _s = classify(con, d, S, float(sc))
        allow = {l["item"] for l in ls if l["bucket"] == "writeoff" and l["group"] == "allowance"}
        pile = {l["item"] for l in ls if l["bucket"] == "writeoff"}
        into, outof = allow - allow_now, allow_now - allow
        out.append(dict(scale=sc, name=name, current=(float(sc) == S["allowance_scale"]),
                        into_n=len(into), into_p=sum(val.get(i, 0) for i in into),
                        out_n=len(outof), out_p=sum(val.get(i, 0) for i in outof),
                        allowance_n=len(allow), allowance_p=sum(val.get(i, 0) for i in allow),
                        pile_in_n=len(pile - pile_now), pile_out_n=len(pile_now - pile), writeoff_n=len(pile)))
    return out


def _sortkey(l):
    return (-(l["mrp_p"] if l["mrp_p"] is not None else -1), l["item"])


def desk(con, d, who=""):
    """Everything the Loss desk page shows."""
    sa = _sa()
    S = settings(con)
    lines, over, skipped = classify(con, d, S)
    claims = _claims_by_item(con, d["count_id"])
    for l in lines:
        c = claims.get(l["item"])
        if c and l["bucket"] == "pursue":
            l["claim"] = dict(state=c["state"], answer=c.get("answer_label") or "", note=c.get("answer_note") or "",
                              outcome=c.get("outcome_label") or "")
    T = totals_of(lines)
    piles = []
    for k, title in PILES:
        ls = sorted([l for l in lines if l["bucket"] == k], key=_sortkey)
        if k == "with_me":
            ls.sort(key=lambda l: (l["word"] != "PARKED", -(l["mrp_p"] or 0), l["item"]))
        if k == "writeoff":
            order = {g: i for i, (g, _t, _b) in enumerate(GROUPS)}
            ls.sort(key=lambda l: (order.get(l["group"], 9), -(l["mrp_p"] or 0), l["item"]))
        piles.append(dict(key=k, title=title, lines=ls, **T[k]))
    done = dict(back=sorted([l for l in lines if l["bucket"] == "back"], key=_sortkey),
                written_off=sorted([l for l in lines if l["bucket"] == "written_off"], key=lambda l: (l["group"], -(l["mrp_p"] or 0), l["item"])))
    over.sort(key=lambda l: (-l["diff"], l["item"]))
    return dict(kit=KIT, count_id=d["count_id"], day=d.get("day") or "", as_on=d.get("as_on") or "", when=d.get("when") or "",
                totals=T, piles=piles, done=done, over=over, orthotics_elsewhere=skipped,
                groups=[dict(key=g, title=t, blurb=b) for g, t, b in GROUPS],
                settings=settings_view(con), rules=dict(pursue_floor=_rs(S["pursue_floor_p"]), ceiling=_rs(S["small_gap_ceiling_p"]),
                                                        trigger=S["recount_trigger"], scale=S["allowance_scale"],
                                                        batch=S["voucher_batch"], consume_auto=S["consume_auto"]),
                preview=preview(con, d, S), record=record(con, d, lines=lines),
                may_accept=True, arm_seconds=ARM_SECONDS,
                links=dict(hub="/finance/stock/page/hub?count=%d" % d["count_id"], amir=d["links"]["amir_page"],
                           record_pdf="/finance/stock/api/loss/%d/record.pdf" % d["count_id"],
                           report="/finance/stock/page/report?count=%d" % d["count_id"]))


# ------------------------------------------------------------------ the record (the audit trail at the desk's foot)
def runs(con, root):
    out = []
    for r in con.execute("SELECT id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, round_no, md5 "
                         "FROM stock_writeoff_run WHERE count_id=? ORDER BY id", (int(root),)):
        g = json.loads(r[7])
        out.append(dict(id=r[0], at=r[1], at_text=_sa()._r_stamp(r[1]) + " IST", by=r[2] or "", lines=r[3], mrp_p=r[4],
                        cost_p=r[5], unpriced=r[6], round_no=r[9], md5=(r[10] or "")[:8],
                        groups=[dict(key=k, title=GROUP_TITLE.get(k, k), lines=v, n=len(v), mrp_p=sum(l["mrp_p"] or 0 for l in v),
                                     cost_p=sum(l["cost_p"] or 0 for l in v)) for k, v in g.items() if v],
                        settings=json.loads(r[8])))
    return out


def trail(con, root, limit=200):
    out = []
    try:
        for r in con.execute("SELECT action, after_json, by_whom, at FROM audit_log WHERE table_name=? AND row_id=? ORDER BY id DESC LIMIT ?",
                             (AUDIT_TABLE, int(root), int(limit))):
            a = json.loads(r[1] or "{}")
            out.append(dict(action=r[0], what=a.get("text") or "", by=r[2] or "", at=r[3], at_text=_sa()._r_stamp(r[3]) + " IST"))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def record(con, d, lines=None):
    if lines is None:
        lines, _o, _s = classify(con, d)
    T = totals_of(lines)
    wo = [l for l in lines if l["bucket"] == "written_off"]
    groups = []
    for g, t, b in GROUPS:
        ls = sorted([l for l in wo if l["group"] == g], key=_sortkey)
        if ls:
            groups.append(dict(key=g, title=t, blurb=b, lines=ls, **T["written_off"]["groups"][g]))
    return dict(groups=groups, runs=runs(con, d["count_id"]), settings_log=settings_log(con),
                trail=trail(con, d["count_id"]), back=sorted([l for l in lines if l["bucket"] == "back"], key=_sortkey))


# ------------------------------------------------------------------ the owner's taps
def _lines_now(con, root):
    sa = _sa()
    d = sa._pad_report_data(con, root)
    if d is None:
        return None, None
    ls, over, _s = classify(con, d)
    return d, {l["item"]: l for l in ls + over}


def _newest_diff_id(con, root, item):
    sa = _sa()
    _r, fam, _R = sa._pad_family(con, root)
    q = ",".join("?" * len(fam))
    r = con.execute("SELECT id FROM stock_diff WHERE item=? AND count_id IN (%s) ORDER BY count_id DESC, id DESC LIMIT 1" % q,
                    (item,) + tuple(fam)).fetchone()
    return int(r[0]) if r else None


def _word(con, root, item, action, note, who, ts, close=False, recovery_state=None):
    """The same two rows /api/pad/decide writes (lane word + the S221 decision), and -- for a closing word --
    the line's status, the way /api/diff/<id>/decision closes it."""
    sa = _sa()
    con.execute("INSERT INTO stock_diff_lane (count_id, item, action, note, by_user, at) VALUES (?,?,?,?,?,?)",
                (root, item, action, note, who, ts))
    did = _newest_diff_id(con, root, item)
    if did and action in sa.DECISIONS:
        con.execute("INSERT INTO stock_diff_decision (diff_id, decision, recover_from, recover_p, recovery_state, note, decided_by, decided_at) "
                    "VALUES (?,?,?,?,?,?,?,?)", (did, action, None, None, recovery_state or ("open" if action == "RECOVER" else "none"), note, who, ts))
        if close:
            con.execute("UPDATE stock_diff SET status='closed', closed_at=? WHERE id=?", (ts, did))
    return did


def move(con, root, item, pile, who):
    d, L = _lines_now(con, root)
    if d is None:
        return False, "No such count.", 404
    l = L.get(item)
    if not l:
        return False, "That line is not on the desk (orthotics stay on their own section).", 400
    if pile not in PILE_TITLE and pile != "auto":
        return False, "Choose one of the four piles.", 400
    if l["bucket"] in ("back", "written_off"):
        return False, "That line is already closed.", 409
    if l["bucket"] == "over" and pile not in ("recount", "auto"):
        return False, "A line with more on the shelf is never a loss -- it can only be counted again.", 400
    if l.get("pile") == pile and l.get("moved"):
        return True, "Already in %s." % PILE_TITLE[pile], 200
    ts = now_iso()
    con.execute("INSERT INTO stock_pile_move (count_id, item, pile, by_user, at) VALUES (?,?,?,?,?)", (root, item, pile, who, ts))
    _audit(con, root, "move", dict(item=item, pile=pile, was=l.get("pile") or l["bucket"],
                                   text="%s moved %s -> %s" % (item, PILE_TITLE.get(l.get("pile") or "", l["bucket"]),
                                                               PILE_TITLE.get(pile, "the system's suggestion"))), who)
    con.commit()
    return True, "%s moved to %s." % (item, PILE_TITLE.get(pile, "the system's suggestion")), 200


def accept(con, root, items, who):
    """Accept back: EXPLAINED, cause FOUND, status closed, shelf corrected to Marg's, audited. Only a line that is in
    the With-me pile now; a repeat finds it closed and writes nothing."""
    d, L = _lines_now(con, root)
    if d is None:
        return False, "No such count.", 404, 0
    ts, done, skipped = now_iso(), [], []
    for item in items:
        l = L.get(item)
        if not l or l["bucket"] != "with_me":
            skipped.append(item)
            continue
        did = _word(con, root, item, "EXPLAINED", "owner: back in store", who, ts, close=True)
        if did:
            con.execute("UPDATE stock_diff SET cause='FOUND', cause_note=?, cause_by=?, cause_at=? WHERE id=?",
                        ("owner: back in store -- kept elsewhere, turned up (S418)", who, ts, did))
        con.execute("INSERT INTO stock_shelf_fix (count_id, item, qty, source, note, by_user, at) VALUES (?,?,?,?,?,?,?)",
                    (root, item, int(l["marg"]), "accept_back", "owner: back in store", who, ts))
        _audit(con, root, "accept_back", dict(item=item, diff_id=did, marg=l["marg"], counted=l["counted"], mrp_p=l["mrp_p"],
                                              text="%s accepted back -- %s short at the count, shelf corrected to Marg's %s" % (item, l["short_day_text"] or l["short_text"], l["marg"])), who)
        done.append(item)
    con.commit()
    if not done:
        return True, ("Already closed -- nothing written." if skipped else "Nothing to accept."), 200, 0
    return True, "Accepted back: %s." % ", ".join(done), 200, len(done)


def _pile_items(con, root, key):
    d, L = _lines_now(con, root)
    if d is None:
        return None, None, []
    return d, L, sorted(i for i, l in L.items() if l.get("bucket") == key)


def arm(con, root, who):
    d, L, items = _pile_items(con, root, "writeoff")
    if d is None:
        return False, "No such count.", 404, None
    if not items:
        return False, "The write-off pile is empty.", 400, None
    token = hashlib.md5(("%s|%s|%s" % (root, now_iso(), json.dumps(items))).encode("utf-8")).hexdigest()[:16]
    con.execute("INSERT INTO stock_pile_arm (count_id, token, items, by_user, at) VALUES (?,?,?,?,?)",
                (root, token, json.dumps(items), who, now_iso()))
    con.commit()
    T = totals_of(list(L.values()))["writeoff"]
    return True, "Tap again within %d seconds: write off %d lines, %s at MRP." % (ARM_SECONDS, len(items), _rs(T["mrp_p"])), 200, \
        dict(token=token, n=len(items), mrp_p=T["mrp_p"], seconds=ARM_SECONDS)


def writeoff(con, root, token, who):
    """The second tap. The pile must be what it was when armed, within ARM_SECONDS. Every line -> WRITE_OFF (closed),
    the documented run frozen, and the Marg voucher round made for exactly those lines in the same call."""
    sa = _sa()
    r = con.execute("SELECT id, items, at, used_at FROM stock_pile_arm WHERE count_id=? AND token=?", (root, str(token or ""))).fetchone()
    if not r:
        return False, "Tap 'Write off this pile' first.", 400, None
    if r[3]:
        return True, "Already written off -- nothing done twice.", 200, dict(lines=0, round_no=None)
    try:
        age = (dt.datetime.now() - dt.datetime.fromisoformat(str(r[2])[:19])).total_seconds()
    except ValueError:
        age = 999
    if age > ARM_SECONDS:
        return False, "More than %d seconds passed -- tap 'Write off this pile' again." % ARM_SECONDS, 409, None
    armed = json.loads(r[1])
    d, L, items = _pile_items(con, root, "writeoff")
    if items != armed:
        return False, "The pile changed since you tapped -- look again and tap once more.", 409, None
    S = settings(con)
    ts = now_iso()
    con.execute("UPDATE stock_pile_arm SET used_at=? WHERE id=?", (ts, r[0]))
    groups = {}
    for item in items:
        l = L[item]
        g = l["group"] or "owner"
        note = "owner: written off with the pile -- %s" % GROUP_TITLE.get(g, g) + (" (clinic consumption)" if g == "consume" else "")
        _word(con, root, item, "WRITE_OFF", note, who, ts, close=True)
        groups.setdefault(g, []).append(dict(item=item, short_units=l["short_units"], short_text=l["short_text"],
                                             mrp_p=l["mrp_p"], cost_p=l["cost_p"], why=l["why"], pack=l["pack"]))
    lines_n = len(items)
    mrp = sum(x["mrp_p"] or 0 for v in groups.values() for x in v)
    cost = sum(x["cost_p"] or 0 for v in groups.values() for x in v)
    unpriced = sum(1 for v in groups.values() for x in v if x["mrp_p"] is None)
    frozen = json.dumps(groups, sort_keys=True, separators=(",", ":"))
    rules = dict(allowance_scale=S["allowance_scale"], pursue_floor_p=S["pursue_floor_p"], small_gap_ceiling_p=S["small_gap_ceiling_p"],
                 recount_trigger=S["recount_trigger"], voucher_batch=S["voucher_batch"], consume_auto=S["consume_auto"])
    cur = con.execute("INSERT INTO stock_writeoff_run (count_id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?)", (root, ts, who, lines_n, mrp, cost, unpriced, frozen, json.dumps(rules, sort_keys=True),
                                                         hashlib.md5(frozen.encode("utf-8")).hexdigest()))
    run_id = int(cur.lastrowid)
    _audit(con, root, "writeoff_pile", dict(run=run_id, lines=lines_n, mrp_p=mrp, groups={k: len(v) for k, v in groups.items()},
                                            text="wrote off the pile: %d lines, %s at MRP (%s)" % (
                                                lines_n, _rs(mrp), ", ".join("%s %d" % (GROUP_TITLE.get(k, k), len(v)) for k, v in sorted(groups.items())))), who)
    con.commit()
    d2 = sa._pad_report_data(con, root)
    if con.in_transaction:
        con.commit()
    rno, nv = sa._voucher_make(con, d2, dict(user=who), items=set(items))
    if rno:
        con.execute("UPDATE stock_writeoff_run SET round_no=? WHERE id=?", (rno, run_id))
        _audit(con, root, "vouchers", dict(round_no=rno, lines=nv, text="Marg voucher round %d made for the pile: %d lines, at most %d a voucher" % (rno, nv, S["voucher_batch"])), who)
        con.commit()
    return True, "Written off: %d lines, %s at MRP. %s" % (
        lines_n, _rs(mrp), ("Amir's vouchers: round %d, %d lines." % (rno, nv)) if rno else "No Marg voucher was needed."), 200, \
        dict(lines=lines_n, mrp_p=mrp, round_no=rno, voucher_lines=nv, run=run_id)


def pursue_prepare(con, root, who):
    """Before the existing S228 sheet is made: every Pursue line not yet on a sheet carries RECOVER (open) and the
    tick; a tick on any other unshared line is taken off (recorded). Returns the number readied."""
    d, L, items = _pile_items(con, root, "pursue")
    if d is None:
        return None
    sa = _sa()
    sa._loss_ensure(con)
    ts = now_iso()
    ready = [i for i in items if not L[i].get("sent")]
    for i in ready:
        if L[i]["word"] != "RECOVER":
            _word(con, root, i, "RECOVER", "owner: pursue -- the sheet for Darpan", who, ts)
        con.execute("INSERT INTO stock_loss_tick (count_id, item, on_, by_user, at) VALUES (?,?,?,?,?) "
                    "ON CONFLICT(count_id, item) DO UPDATE SET on_=excluded.on_, by_user=excluded.by_user, at=excluded.at",
                    (root, i, 1, who, ts))
    shared = set(_shares_by_item(con, root))
    for r in con.execute("SELECT item FROM stock_loss_tick WHERE count_id=? AND on_=1", (root,)).fetchall():
        if r[0] not in ready and r[0] not in shared:
            con.execute("UPDATE stock_loss_tick SET on_=0, by_user=?, at=? WHERE count_id=? AND item=?", (who, ts, root, r[0]))
    if ready:
        _audit(con, root, "pursue", dict(items=ready, text="%d line%s readied for the sheet for Darpan" % (len(ready), "" if len(ready) == 1 else "s")), who)
    con.commit()
    return len(ready)


def recount_ask(con, root, who):
    d, L, items = _pile_items(con, root, "recount")
    if d is None:
        return False, "No such count.", 404, 0
    ts = now_iso()
    new = [i for i in items if not L[i].get("asked")]
    for i in new:
        con.execute("INSERT INTO stock_recount_ask (count_id, item, asked_by, asked_at) VALUES (?,?,?,?)", (root, i, who, ts))
    if new:
        _audit(con, root, "recount_ask", dict(items=new, text="Darpan asked to recount %d item%s" % (len(new), "" if len(new) == 1 else "s")), who)
    con.commit()
    if not new:
        return True, ("Every recount line is already with Darpan." if items else "The recount pile is empty."), 200, 0
    return True, "Sent to Darpan's Stock milaan: %d item%s to count again (Phir se gino)." % (len(new), "" if len(new) == 1 else "s"), 200, len(new)


# ------------------------------------------------------------------ Darpan's side (Stock milaan)
def recount_list(con, root):
    """What Darpan is asked to count again: every asked item, with his answer if he gave one after the ask.
    Blind: Marg's figure and the first count are NOT given to him."""
    ensure(con)
    sa = _sa()
    asks, fx = _asks(con, root), fixes(con, root)
    packs, packing = {}, {}
    try:
        as_on = con.execute("SELECT marg_as_on FROM stock_count WHERE id=?", (int(root),)).fetchone()[0]
        for r in con.execute("SELECT item, pack_size, packing FROM stock_snapshot WHERE as_on=?", (as_on,)):
            packs[r[0]] = int(r[1] or 1); packing[r[0]] = r[2] or ""
    except Exception:                                         # noqa: BLE001
        pass
    out = []
    for item, a in asks.items():
        f = fx.get(item)
        done = bool(f and f["source"] == "recount" and str(f["at"]) >= str(a["at"]))
        ps = packs.get(item, 1)
        out.append(dict(item=item, packing=packing.get(item, ""), pack=ps, asked_at=a["at"], asked_text=sa._r_stamp(a["at"]) + " IST",
                        done=done, qty=(f["qty"] if done else None), qty_text=(sa._qw(f["qty"], ps) if done else ""),
                        by=(f["by"] if done else ""), at=(f["at"] if done else ""), at_text=((sa._r_stamp(f["at"]) + " IST") if done else "")))
    out.sort(key=lambda r: (r["done"], r["item"]))
    return out


def recount_answer(con, root, item, qty, who, may_change_minutes=10):
    """Darpan's figure. Once per ask; his own figure may be corrected within ten minutes."""
    rl = {r["item"]: r for r in recount_list(con, root)}
    r = rl.get(item)
    if not r:
        return False, "Yeh item phir se ginne ki list mein nahi hai.", 404
    try:
        q = int(qty)
    except (TypeError, ValueError):
        return False, "Ginti likhiye.", 400
    if q < 0 or q > 100000:
        return False, "Ginti sahi likhiye.", 400
    if r["done"]:
        try:
            recent = (dt.datetime.now() - dt.datetime.fromisoformat(str(r["at"])[:19])) <= dt.timedelta(minutes=may_change_minutes)
        except ValueError:
            recent = False
        if r["qty"] == q:
            return True, "Pehle hi likha hai — dobara nahi likha.", 200
        if not (recent and r["by"] == who):
            return False, "Ginti darj ho chuki hai — badalna ho to doctor sahab se kahiye.", 409
    ts = now_iso()
    con.execute("INSERT INTO stock_shelf_fix (count_id, item, qty, source, note, by_user, at) VALUES (?,?,?,?,?,?,?)",
                (root, item, q, "recount", "Phir se gino (Stock milaan)", who, ts))
    _audit(con, root, "recount", dict(item=item, qty=q, text="%s recounted by %s: %s" % (item, who, _sa()._qw(q, r["pack"]))), who)
    con.commit()
    return True, "Likh liya: %s — %s." % (item, _sa()._qw(q, r["pack"])), 200


# ------------------------------------------------------------------ the record as a PDF
def record_pdf(con, d):
    import pad_receipt as PR                                  # noqa: PLC0415 -- the estate's own stdlib PDF writer, read-only use
    sa = _sa()
    lines, over, _s = classify(con, d)
    T = totals_of(lines)
    R = record(con, d, lines=lines)
    S = settings(con)
    cid = d["count_id"]
    doc = PR._Doc("Stock count #%d - loss desk record" % cid, "%s - %s" % (PR.CLINIC, PR.STORE), "COUNT #%d - LOSS DESK RECORD" % cid)
    p = doc.pdf
    p.text(PR._L, doc.y - 15, "%s - %s" % (PR.CLINIC, PR.STORE), 14, bold=True)
    doc.y -= 21
    p.text(PR._L, doc.y - 13, "STOCK COUNT #%d OF %s - THE LOSS DESK RECORD" % (cid, d.get("day") or ""), 12, bold=True)
    doc.y -= 19
    p.line(PR._L, doc.y, PR._R, doc.y, 0.8)
    doc.y -= 6
    doc.line_text("Printed %s IST. Marg stock as on %s. Medicines and consumables; the orthotics are closed on their own section."
                  % (sa._r_stamp(now_iso()), d.get("as_on") or "-"), 8.5, gray=0.3)
    cols = [("", PR._L, "l", 200), ("Lines", PR._L + 260, "r", 0), ("At MRP", PR._L + 350, "r", 0), ("At cost", PR._L + 440, "r", 0),
            ("Unpriced", PR._R, "r", 0)]
    doc.thead("THE FIVE TOTALS (the same figures as the desk and the hub)", cols)
    for label, t in (("Short at the count (all lines below)", T["short"]), ("Open -- still to settle", T["open"]),
                     ("   with you / back in store (to accept)", T["with_me"]), ("   write-off pile (to write off)", T["writeoff"]),
                     ("   to pursue", T["pursue"]), ("   recount", T["recount"]),
                     ("Back in store / explained", T["back"]), ("Written off", T["written_off"])):
        doc.trow("THE FIVE TOTALS", cols, [label, str(t["n"]), PR._rs(t["mrp_p"]), PR._rs(t["cost_p"]), str(t["unpriced"] or "")],
                 bold=not label.startswith("   "))
    doc.heading("THE RULES IN FORCE NOW")
    for s in settings_view(con):
        doc.kv(s["label"], str(s["shown"]), kw=200)
    icols = [("#", PR._L + 16, "r", 0), ("Item", PR._L + 22, "l", 230), ("Short", PR._L + 330, "r", 0),
             ("At MRP", PR._L + 410, "r", 0), ("At cost", PR._R, "r", 0)]
    for g in R["groups"]:
        doc.heading("WRITTEN OFF -- %s: %d line%s, %s at MRP, %s at cost" % (g["title"].upper(), g["n"], "" if g["n"] == 1 else "s", PR._rs(g["mrp_p"]), PR._rs(g["cost_p"])))
        doc.para(g["blurb"])
        doc.thead(g["title"], icols)
        for i, l in enumerate(g["lines"], 1):
            doc.trow(g["title"], icols, [str(i), l["item"], l["short_text"] or l["short_day_text"], PR._rs(l["mrp_p"]), PR._rs(l["cost_p"])])
    if R["runs"]:
        doc.heading("EACH WRITE-OFF TAP")
        for r in R["runs"]:
            doc.para("%s by %s: %d lines, %s at MRP, %s at cost; %s; Marg voucher round %s; fingerprint %s. Rules: allowance x%s, "
                     "pursue floor %s, small-gap ceiling %s, recount at %s units, %s lines a voucher."
                     % (r["at_text"], r["by"] or "-", r["lines"], PR._rs(r["mrp_p"]), PR._rs(r["cost_p"]),
                        "; ".join("%s %d" % (g["title"], g["n"]) for g in r["groups"]), r["round_no"] or "-", r["md5"],
                        r["settings"].get("allowance_scale"), PR._rs(r["settings"].get("pursue_floor_p")),
                        PR._rs(r["settings"].get("small_gap_ceiling_p")), r["settings"].get("recount_trigger"),
                        r["settings"].get("voucher_batch")), 8.5, 0.2)
    for key, title in (("back", "BACK IN STORE / EXPLAINED -- valued at the count day"), ("pursue", "TO PURSUE"), ("recount", "TO RECOUNT"),
                       ("with_me", "WITH YOU -- TO ACCEPT BACK"), ("writeoff", "IN THE WRITE-OFF PILE -- NOT YET WRITTEN OFF")):
        ls = sorted([l for l in lines if l["bucket"] == key], key=_sortkey)
        if not ls:
            continue
        doc.heading("%s: %d line%s" % (title, len(ls), "" if len(ls) == 1 else "s"))
        doc.thead(title, icols)
        for i, l in enumerate(ls, 1):
            day = key == "back"
            doc.trow(title, icols, [str(i), l["item"], (l["short_day_text"] if day else (l["short_text"] or l.get("over_text") or "")),
                                    PR._rs(l["mrp_day_p"] if day else l["mrp_p"]), PR._rs(l["cost_day_p"] if day else l["cost_p"])])
    if R["settings_log"]:
        doc.heading("EVERY CHANGE OF A RULE")
        for c in R["settings_log"]:
            doc.para("%s  %s: %s -> %s  (%s)" % (c["at_text"], c["label"], c["old_text"], c["new_text"], "seeded by the kit" if c["seeded"] else c["by"]), 8.5, 0.2)
    return doc.finish("Stock count #%d - the loss desk record - %s" % (cid, KIT))
