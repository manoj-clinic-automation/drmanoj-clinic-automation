#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""apply_s362.py -- kit S362_CASH_SCREENS (Sanjeevni, session 280, 21-Sep-2026).

Part 2 of S280_CASH_ARCHITECTURE_AND_MONTH_TABLE: EVERY SANJEEVNI CASH FIGURE FROM ONE
CALCULATION (sanjeevni_cash.py, S361). Anchored edits, each inside the function it names;
an anchor that does not occur exactly once in that function stops everything, touching nothing.

  /root/finance/finance_app.py   (THE PARENT'S FILE -- DECLARED)  FROM 4a399f30 (S359)
      one helper block; day_state; api_month; api_tile; api_workbench; _custody_state;
      api_cash_position; api_where_is_the_cash; api_days; the health card's drawer leg.
  /root/finance/darpan_app.py    FROM df3224c5 (S312)   Darpan's card: the drawer he should hold.
  /root/finance/darpan_kal.py    FROM 2072e290 (S359)   the cash log's pending days, the day it
      covers, the month table.

Every edit falls back to the old arithmetic, byte for byte in behaviour, when sanjeevni_cash
is absent, when the unit is not Sanjeevni, or for a date before the counted anchor.

    python3 apply_s362.py --dir /root/finance               # in place (backups .bak_S362_<from8>)
    python3 apply_s362.py --dir DIR --out OUTDIR            # patched copies (the walk)
"""
import argparse, hashlib, os, re, shutil, sys

FROM = {"finance_app.py": "4a399f3068799917b8e58f89a1645131",
        "darpan_app.py": "df3224c5fb45964d8b53df660ff60def",
        "darpan_kal.py": "2072e2904f2b363eab9cb494533bd198"}

HELPERS = '''# ============================================================================
#  S362 (Sanjeevni, 21-Sep-2026) -- EVERY SANJEEVNI CASH FIGURE FROM ONE CALCULATION.
#  sanjeevni_cash.py (S361) starts from the counted position of 17-Aug-2026 and
#  reads BOTH handover registers (cash_movement and cash_custody_event), counting
#  each once. Before it, each screen in this file chose one register, and the same
#  drawer read 4,36,597 / 2,29,459 / 2,29,452 / 2,29,652 while the workbench went
#  negative. Where it can speak, every Sanjeevni drawer and custody figure below
#  comes from it. Where it cannot -- module absent, the clinic unit, no counted
#  anchor, a date before the count -- the old arithmetic runs, unchanged.
# ============================================================================
try:
    import sanjeevni_cash as _sjc
except Exception:                                          # noqa: BLE001
    _sjc = None


def _sj_book(con, unit=None):
    """The one calculation's day rows for Sanjeevni, or None when it cannot speak."""
    if _sjc is None or (unit or UNIT) != UNIT:
        return None
    try:
        r = _sjc.days(con, "0000-00-00", "9999-12-31", UNIT)
    except Exception:                                      # noqa: BLE001
        return None
    return r if r.get("ok") else None


def _sj_closes(con, unit=None):
    """({date: close positions}, anchor) -- ({}, None) when it cannot speak."""
    b = _sj_book(con, unit)
    if not b:
        return {}, None
    return {r["date"]: r["close"] for r in b["rows"]}, b["anchor"]


def _sj_drawer_or(closes, anchor, iso, old_p):
    """The drawer at the close of iso from the one calculation; old_p before the count."""
    if anchor and iso >= anchor["anchor_date"] and iso in closes:
        return closes[iso]["drawer"]
    return old_p


def _sj_latest(con, unit=None):
    """Where every rupee is at the close of the newest filed day, or None."""
    b = _sj_book(con, unit)
    if not b:
        return None
    a = b["anchor"]
    if b["rows"]:
        p = dict(b["rows"][-1]["close"]); p["as_of"] = b["rows"][-1]["date"]
    else:
        p = dict(drawer=a["drawer_p"], dr_bhawna=a["bhawna_p"], dr_manoj=a["manoj_p"], bank=a["bank_p"])
        p["as_of"] = a["anchor_date"]
    p["in_unit"] = p["drawer"] + p["dr_bhawna"] + p["dr_manoj"]
    p["anchor"], p["rows"] = a, b["rows"]
    return p


def _sj_cash_position(con, p):
    """/finance/api/cash-position from the one calculation -- every key the pages read."""
    a = p["anchor"]
    bank = con.execute(
        "SELECT COALESCE(SUM(cm.amount_p),0) p, COUNT(*) n, MAX(de.business_date) last "
        "FROM cash_movement cm JOIN day_entry de ON de.id=cm.day_entry_id "
        "WHERE de.unit=? AND cm.party='bank' AND cm.direction='out'", (UNIT,)).fetchone()
    dep = con.execute(
        "SELECT de.business_date d, cm.amount_p a, cm.reference r FROM cash_movement cm "
        "JOIN day_entry de ON de.id=cm.day_entry_id WHERE de.unit=? AND cm.party='bank' "
        "AND cm.direction='out' ORDER BY de.business_date DESC, cm.id DESC LIMIT 40", (UNIT,)).fetchall()
    names = {"dr_bhawna": "Dr Bhawna", "dr_manoj": "Dr Manoj", "bank": "the bank"}

    def trail(party, opening_p):
        rows = [dict(date=a["anchor_date"], frm="count", to=party, amount=rupees(opening_p),
                     note="opening -- counted on %s" % a["anchor_date"], kind="count")]
        for h in _sjc.handovers(con, a["anchor_date"], "9999-12-31", UNIT,
                                set(a.get("pre_anchor_custody_ids") or [])):
            if h["to"] == party:
                rows.append(dict(date=h["date"], frm="drawer", to=party, amount=rupees(h["amount_p"]),
                                 note=(h["note"] or "")[:120], kind="handover"))
        rows.sort(key=lambda x: x["date"] or "", reverse=True)
        return rows
    days = [dict(date=r["date"], drawer=rupees(r["close"]["drawer"]),
                 unbanked=rupees(r["close"]["drawer"] + r["close"]["dr_bhawna"] + r["close"]["dr_manoj"]))
            for r in p["rows"]][-60:]
    parked_p = p["dr_bhawna"] + p["dr_manoj"]
    return dict(ok=True, basis="sanjeevni_cash",
                bank_deposits=[dict(date=r["d"], amount=rupees(int(r["a"])), ref=(r["r"] or "")) for r in dep],
                reserve_detail=trail("dr_bhawna", a["bhawna_p"]),
                manoj_detail=trail("dr_manoj", a["manoj_p"]),
                drawer=rupees(p["drawer"]), reserve=rupees(p["dr_bhawna"]), with_manoj=rupees(p["dr_manoj"]),
                parked=rupees(parked_p), bank_deposited=rupees(int(bank["p"])), bank_count=int(bank["n"]),
                last_bank_date=bank["last"], unbanked=rupees(p["in_unit"]),
                drawer_p=p["drawer"], reserve_p=p["dr_bhawna"], with_manoj_p=p["dr_manoj"],
                parked_p=parked_p, unbanked_p=p["in_unit"], baseline_p=a["bhawna_p"] + a["manoj_p"],
                as_of=p["as_of"], since=a["anchor_date"], days=days)


'''

FA = [
    # (function header or None for file-level, old, new)
    (None, "def opening_p(con, unit, date_iso):\n", HELPERS + "def opening_p(con, unit, date_iso):\n"),
    (None, "def day_state(con, unit, date_iso):\n",
     "def day_state(con, unit, date_iso):\n"
     "    \"\"\"S362: the day as the books hold it; its opening and closing drawer from the\n"
     "    one calculation (sanjeevni_cash) from the counted anchor on.\"\"\"\n"
     "    st = _day_state_v_ledger(con, unit, date_iso)\n"
     "    closes, a = _sj_closes(con, unit)\n"
     "    if a and date_iso >= a[\"anchor_date\"]:\n"
     "        prev = [d for d in closes if d < date_iso]\n"
     "        op = closes[max(prev)][\"drawer\"] if prev else a[\"drawer_p\"]\n"
     "        cl = closes[date_iso][\"drawer\"] if date_iso in closes else op\n"
     "        st.update(opening_p=op, opening=rupees(op), closing_p=cl, closing=rupees(cl),\n"
     "                  drawer_basis=\"sanjeevni_cash\")\n"
     "    return st\n\n\n"
     "def _day_state_v_ledger(con, unit, date_iso):\n"),
    ("def api_month(", "    _expense_uid_col(con)                  # D330: the drawings subselect below\n",
     "    _expense_uid_col(con)                  # D330: the drawings subselect below\n"
     "    _sjc_c, _sjc_a = _sj_closes(con)       # S362\n"),
    ("def api_month(", "closing=rupees(e[\"closing_p\"]) if e else \"\"))",
     "closing=rupees(_sj_drawer_or(_sjc_c, _sjc_a, iso, e[\"closing_p\"])) if e else \"\"))"),
    ("def api_tile(", "    cash_p = int(cust[\"cash_p\"]) if cust else 0\n",
     "    cash_p = int(cust[\"cash_p\"]) if cust else 0\n"
     "    _sjp = _sj_latest(con)                 # S362: the drawer, not the running total\n"
     "    if _sjp:\n"
     "        cash_p = _sjp[\"drawer\"]\n"),
    ("def api_workbench(", "    con = db()\n    rows = con.execute(\n",
     "    con = db()\n    _sjc_c, _sjc_a = _sj_closes(con)       # S362\n    rows = con.execute(\n"),
    ("def api_workbench(", "closing=rupees(int(r[\"closing_p\"] or 0)),",
     "closing=rupees(_sj_drawer_or(_sjc_c, _sjc_a, r[\"business_date\"], int(r[\"closing_p\"] or 0))),"),
    ("def _custody_state(", "    held = [dict(party=r[\"party\"], held=rupees(int(r[\"held_p\"] or 0)))\n",
     "    _sjp = _sj_latest(con)                 # S362: one calculation; no negative 'counter'/'drawer'\n"
     "    if _sjp:\n"
     "        held = [dict(party=k, held=rupees(int(_sjp[k]))) for k in (\"drawer\", \"dr_bhawna\", \"dr_manoj\")\n"
     "                if int(_sjp[k])]\n"
     "        return dict(people=people, held=held, as_of=_sjp[\"as_of\"], basis=\"sanjeevni_cash\")\n"
     "    held = [dict(party=r[\"party\"], held=rupees(int(r[\"held_p\"] or 0)))\n"),
    ("def api_cash_position(", "    con = db()\n    held = {",
     "    con = db()\n"
     "    _sjp = _sj_latest(con)                 # S362: the one calculation\n"
     "    if _sjp:\n"
     "        return jsonify(**_sj_cash_position(con, _sjp))\n"
     "    held = {"),
    ("def api_where_is_the_cash(", "    total_p = sum(x[\"amount_p\"] for x in parked)\n",
     "    total_p = sum(x[\"amount_p\"] for x in parked)\n"
     "    _sjp = _sj_latest(con)                 # S362: both registers, each handover once\n"
     "    if _sjp:\n"
     "        parked = [dict(party=p, name=PARTY_NAMES.get(p, p), amount=rupees(int(_sjp[p])),\n"
     "                       amount_p=int(_sjp[p])) for p in (\"dr_manoj\", \"dr_bhawna\")]\n"
     "        total_p = sum(x[\"amount_p\"] for x in parked)\n"),
    ("def api_days(", "    rows = con.execute(\n        \"SELECT e.id, e.business_date, e.status, e.source",
     "    _sjc_c, _sjc_a = _sj_closes(con)       # S362\n"
     "    rows = con.execute(\n        \"SELECT e.id, e.business_date, e.status, e.source"),
    ("def api_days(", "             closing=rupees(r[\"closing_p\"]),",
     "             closing=rupees(_sj_drawer_or(_sjc_c, _sjc_a, r[\"business_date\"], r[\"closing_p\"])),"),
    (None, "            drawer = closing - parked\n",
     "            drawer = closing - parked\n"
     "            _sjp = _sj_latest(con)         # S362: the one calculation\n"
     "            if _sjp:\n"
     "                drawer, parked, closing = (_sjp[\"drawer\"], _sjp[\"dr_bhawna\"] + _sjp[\"dr_manoj\"],\n"
     "                                           _sjp[\"in_unit\"])\n"),
]

DA = [
    ("def api_card(", "    if drawer[\"counted_p\"] is not None and drawer[\"expected_p\"] is not None:\n",
     "    # S362: the drawer Darpan should hold, from the one calculation (sanjeevni_cash), which\n"
     "    # reads every handover once -- the old running total counted what was already handed.\n"
     "    try:\n"
     "        import sanjeevni_cash as _sjc\n"
     "        _b = _sjc.days(con, \"0000-00-00\", iso, _unit)\n"
     "        _me = [r for r in (_b.get(\"rows\") or []) if r[\"date\"] == iso] if _b.get(\"ok\") else []\n"
     "        if _me:\n"
     "            _prev = [r for r in _b[\"rows\"] if r[\"date\"] < iso]\n"
     "            _m = _me[0]\n"
     "            _op = _prev[-1][\"close\"][\"drawer\"] if _prev else _b[\"anchor\"][\"drawer_p\"]\n"
     "            drawer[\"expected_p\"] = _m[\"close\"][\"drawer\"]\n"
     "            led = dict(opening_p=_op, cash_in_p=_m[\"cash_p\"],\n"
     "                       noncash_p=_m[\"without_cash_p\"] + _m[\"received_elsewhere_p\"],\n"
     "                       expense_p=_m[\"expense_p\"], cash_out_p=sum(h[\"amount_p\"] for h in _m[\"handed\"]),\n"
     "                       cash_back_p=_m[\"adjust_p\"])\n"
     "    except Exception:                                      # noqa: BLE001\n"
     "        pass\n"
     "    if drawer[\"counted_p\"] is not None and drawer[\"expected_p\"] is not None:\n"),
]

KA = [
    (None, "def _pending_days(con, who):\n",
     "def _covered_days(con):\n"
     "    \"\"\"S362: counter days already paid over, as the one calculation's cover records\n"
     "    them (every August handover mapped at S361, every log from now on) -- never asked again.\"\"\"\n"
     "    if not _has(con, \"cash_handover_cover\"):\n"
     "        return set()\n"
     "    return {r[0] for r in con.execute(\"SELECT DISTINCT covers_date FROM cash_handover_cover WHERE unit=?\",\n"
     "                                      (_unit,))}\n\n\n"
     "def _cover(con, src, hid, iso, amount_p, who):\n"
     "    \"\"\"S362: record which day a handover paid for, in the one calculation's register.\"\"\"\n"
     "    if hid is None or not _has(con, \"cash_handover_cover\"):\n"
     "        return\n"
     "    con.execute(\"DELETE FROM cash_handover_cover WHERE handover_src=? AND handover_id=?\", (src, hid))\n"
     "    con.execute(\"INSERT INTO cash_handover_cover (unit, handover_src, handover_id, covers_date, amount_p, \"\n"
     "                \"note, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?)\",\n"
     "                (_unit, src, hid, iso, int(amount_p), \"darpan_kal: the day this handover paid for\", who, now_iso()))\n\n\n"
     "def _pending_days(con, who):\n"),
    ("def _pending_days(", "    since, until = _log_from(con), _yesterday()\n    out = []\n",
     "    since, until = _log_from(con), _yesterday()\n    out = []\n    covered = _covered_days(con)\n"),
    ("def _pending_days(", "        row = _row(con, iso)\n        if row and row.get(\"handed_p\") is not None:\n",
     "        row = _row(con, iso)\n"
     "        if iso in covered and not (row and row.get(\"handed_p\") is not None and not row.get(\"received_at\")):\n"
     "            continue                                   # S362: already paid over\n"
     "        if row and row.get(\"handed_p\") is not None:\n"),
    ("def _land_movement(", "        con.execute(\"UPDATE cash_movement SET direction='out', party=?, amount_p=?, reference=? WHERE id=?\",\n"
     "                    (party, handed_p, ref, ex[\"id\"]))\n        return ex[\"id\"]\n",
     "        con.execute(\"UPDATE cash_movement SET direction='out', party=?, amount_p=?, reference=? WHERE id=?\",\n"
     "                    (party, handed_p, ref, ex[\"id\"]))\n"
     "        _cover(con, \"movement\", ex[\"id\"], iso, handed_p, who)\n        return ex[\"id\"]\n"),
    ("def _land_movement(", "            if dup:\n                _audit(con, who, \"landing_skipped_custody_dup\", {\"date\": iso, \"custody_id\": dup[\"id\"]})\n                return None\n",
     "            if dup:\n                _audit(con, who, \"landing_skipped_custody_dup\", {\"date\": iso, \"custody_id\": dup[\"id\"]})\n"
     "                _cover(con, \"custody\", dup[\"id\"], iso, handed_p, who)\n                return None\n"),
    ("def _land_movement(", "                      \"VALUES (?,'out',?,?,?)\", (eid, party, handed_p, ref))\n    return cur.lastrowid\n",
     "                      \"VALUES (?,'out',?,?,?)\", (eid, party, handed_p, ref))\n"
     "    _cover(con, \"movement\", cur.lastrowid, iso, handed_p, who)\n    return cur.lastrowid\n"),
    (None, "def _month_rows(con):\n",
     "def _month_rows(con):\n"
     "    \"\"\"S362: the month table from the one calculation (sanjeevni_cash.month_rows) -- sale, UPI,\n"
     "    cash, home, procedure, other, paid elsewhere, cash income -- with the handovers from BOTH\n"
     "    registers after the counted anchor. The S359 arithmetic below stays as the fallback.\"\"\"\n"
     "    try:\n"
     "        import sanjeevni_cash as _sjc\n"
     "        a = _sjc.anchor(con, _unit)\n"
     "    except Exception:                                      # noqa: BLE001\n"
     "        _sjc, a = None, None\n"
     "    if not a:\n"
     "        return _month_rows_s359(con)\n"
     "    old = {m[\"ym\"]: m for m in _month_rows_s359(con)}\n"
     "    hand = {}\n"
     "    for h in _sjc.handovers(con, a[\"anchor_date\"], \"9999-12-31\", _unit, set(a[\"pre_anchor_custody_ids\"])):\n"
     "        k = {\"dr_manoj\": \"to_manoj_p\", \"dr_bhawna\": \"to_bhawna_p\", \"bank\": \"to_bank_p\"}.get(h[\"to\"], \"to_other_p\")\n"
     "        hand.setdefault(h[\"date\"][:7], {}).setdefault(k, 0)\n"
     "        hand[h[\"date\"][:7]][k] += h[\"amount_p\"]\n"
     "    out = []\n"
     "    for m in _sjc.month_rows(con, _unit):\n"
     "        o = old.get(m[\"ym\"], {})\n"
     "        r = dict(m, expense_p=o.get(\"expense_p\", 0), adjust_p=o.get(\"adjust_p\", 0), back_p=o.get(\"back_p\", 0))\n"
     "        r[\"net_cash_p\"] = m[\"cash_income_p\"] + r[\"adjust_p\"]\n"
     "        for k in (\"to_manoj_p\", \"to_bhawna_p\", \"to_bank_p\", \"to_other_p\"):\n"
     "            r[k] = (hand.get(m[\"ym\"], {}).get(k, 0) + (o.get(k, 0) if m[\"ym\"] < a[\"anchor_date\"][:7] else 0)\n"
     "                    + (_pre_anchor_moves(con, m[\"ym\"], a, k) if m[\"ym\"] == a[\"anchor_date\"][:7] else 0))\n"
     "        r[\"handed_p\"] = r[\"to_manoj_p\"] + r[\"to_bhawna_p\"] + r[\"to_bank_p\"] + r[\"to_other_p\"]\n"
     "        out.append(r)\n"
     "    return out\n\n\n"
     "def _pre_anchor_moves(con, ym, a, key):\n"
     "    \"\"\"In the anchor's own month: cash_movement handovers dated before the anchor day.\"\"\"\n"
     "    party = {\"to_manoj_p\": \"dr_manoj\", \"to_bhawna_p\": \"dr_bhawna\", \"to_bank_p\": \"bank\"}.get(key)\n"
     "    q = (\"SELECT COALESCE(SUM(m.amount_p),0) FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id \"\n"
     "         \"WHERE e.unit=? AND m.direction='out' AND e.business_date LIKE ? AND e.business_date < ? \")\n"
     "    if party:\n"
     "        return int(con.execute(q + \"AND m.party=?\", (_unit, ym + \"%\", a[\"anchor_date\"], party)).fetchone()[0])\n"
     "    return int(con.execute(q + \"AND m.party NOT IN ('dr_manoj','dr_bhawna','bank')\",\n"
     "                           (_unit, ym + \"%\", a[\"anchor_date\"])).fetchone()[0])\n\n\n"
     "def _month_rows_s359(con):\n"),
    (None, "def _month_days(con, ym):\n    out = []\n",
     "def _month_days(con, ym):\n"
     "    \"\"\"S362: a day's handover from the one calculation's cover records when it has one\n"
     "    (so August reads handed, not '--'); else Darpan's / the doctors' kal row as before.\"\"\"\n"
     "    out = _month_days_s359(con, ym)\n"
     "    if not _has(con, \"cash_handover_cover\"):\n"
     "        return out\n"
     "    rul = {}\n"
     "    if _has(con, \"cash_bill_ruling\"):\n"
     "        for d, amt in con.execute(\"SELECT business_date, SUM(amount_p) FROM cash_bill_ruling WHERE unit=? \"\n"
     "                                  \"AND business_date LIKE ? GROUP BY business_date\", (_unit, ym + \"%\")):\n"
     "            rul[d] = int(amt or 0)\n"
     "    cov = {}\n"
     "    for d, src, hid, amt in con.execute(\"SELECT covers_date, handover_src, handover_id, amount_p FROM cash_handover_cover \"\n"
     "                                        \"WHERE unit=? AND covers_date LIKE ?\", (_unit, ym + \"%\")):\n"
     "        if src == \"movement\":\n"
     "            t = con.execute(\"SELECT party FROM cash_movement WHERE id=?\", (hid,)).fetchone()\n"
     "        else:\n"
     "            t = con.execute(\"SELECT to_party FROM cash_custody_event WHERE id=?\", (hid,)).fetchone()\n"
     "        c = cov.setdefault(d, dict(p=0, to=set()))\n"
     "        c[\"p\"] += int(amt or 0)\n"
     "        if t:\n"
     "            c[\"to\"].add(t[0])\n"
     "    for x in out:\n"
     "        x[\"received_elsewhere_p\"] = rul.get(x[\"date\"], 0)\n"
     "        x[\"other_p\"] -= x[\"received_elsewhere_p\"]\n"
     "        x[\"net_cash_p\"] += x[\"received_elsewhere_p\"]\n"
     "        c = cov.get(x[\"date\"])\n"
     "        if c and x.get(\"handed_p\") is None:\n"
     "            x[\"handed_p\"] = c[\"p\"]\n"
     "            x[\"handed_to\"] = sorted(c[\"to\"])[0] if len(c[\"to\"]) == 1 else \"split\"\n"
     "            x[\"handed_split\"] = sorted(c[\"to\"])\n"
     "            x[\"received\"] = True\n"
     "    return out\n\n\n"
     "def _month_days_s359(con, ym):\n    out = []\n"),
]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def span(src, header):
    i = src.find(header)
    if i < 0 or src.find(header, i + 1) >= 0:
        raise SystemExit("!! function %r not found exactly once" % header)
    nxt = [j for j in (src.find("\n@app.route", i + 1), src.find("\n@bp.route", i + 1),
                       src.find("\ndef ", i + 1)) if j > 0]
    return i, (min(nxt) if nxt else len(src))


def apply(src, edits, name):
    for header, old, new in edits:
        if header is None:
            if src.count(old) != 1:
                raise SystemExit("!! %s: file-level anchor occurs %d times: %r" % (name, src.count(old), old[:70]))
            src = src.replace(old, new)
        else:
            a, b = span(src, header)
            body = src[a:b]
            if body.count(old) != 1:
                raise SystemExit("!! %s: anchor occurs %d times in %s: %r" % (name, body.count(old), header, old[:70]))
            src = src[:a] + body.replace(old, new) + src[b:]
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    plan = {"finance_app.py": FA, "darpan_app.py": DA, "darpan_kal.py": KA}
    new = {}
    for f, edits in plan.items():
        p = os.path.join(a.dir, f)
        if not os.path.isfile(p) or md5(p) != FROM[f]:
            raise SystemExit("!! %s is not its FROM pin %s -- nothing touched" % (p, FROM[f][:8]))
        new[f] = apply(open(p, encoding="utf-8").read(), edits, f)
    out = a.out or a.dir
    os.makedirs(out, exist_ok=True)
    for f, text in new.items():
        if not a.out:
            shutil.copy2(os.path.join(a.dir, f), os.path.join(a.dir, "%s.bak_S362_%s" % (f, FROM[f][:8])))
        with open(os.path.join(out, f), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("   %s %s -> %s" % (f, FROM[f][:8], md5(os.path.join(out, f))))
    print("APPLIED")


if __name__ == "__main__":
    main()
