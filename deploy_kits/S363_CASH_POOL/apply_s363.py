#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""apply_s363.py -- kit S363_CASH_POOL (Sanjeevni, session 280, 21-Sep-2026).

Supersedes S362_CASH_SCREENS (built and published, NEVER installed; its folder is frozen, F-512).
Part 2 of S280_CASH_ARCHITECTURE_AND_MONTH_TABLE, on the owner's ruling of 21-Sep-2026:
  "Darpan handed all cash daily from 1st to 19th Sept, and Dr Bhawna's receivings and yours go to
   the same pool, so maintain that flow; I will mark each day of Sept in approvals."
So: every Sanjeevni cash screen reads ONE calculation (sanjeevni_cash.py v1.1); the doctors hold ONE
pool; a day the owner approves is a day whose drawer cash went to the pool; the pool's deposits are
their own record. Nobody logs cash day by day any more -- approving the day is the record.

How: S362's own patcher (apply_s362.py, byte-identical, shipped beside this file) produces its
text in memory; the edits below are laid over it; nothing is written unless EVERY anchor is found
exactly once and every FROM pin matches.
  /root/finance/finance_app.py        (THE PARENT'S -- DECLARED)  FROM 4a399f30 (S359)
  /root/finance/darpan_app.py         FROM df3224c5 (S312)
  /root/finance/darpan_kal.py         FROM 2072e290 (S359)
  /root/finance/finance_yesbank.py    FROM cc55b5f4 (S360)   a pool deposit is a booked deposit
  /root/finance/finance_ui/finance_approvals.html (THE PARENT'S -- DECLARED) FROM c940c46f (S359)

    python3 apply_s363.py --dir /root/finance               # in place (backups .bak_S363_<from8>)
    python3 apply_s363.py --dir DIR --out OUTDIR            # patched copies (the walk)
"""
import argparse, hashlib, importlib.util, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("apply_s362", os.path.join(HERE, "apply_s362.py"))
s362 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(s362)

FROM = dict(s362.FROM)
FROM["finance_yesbank.py"] = "cc55b5f4bae367de3c194808da9dfdbc"
FROM["finance_ui/finance_approvals.html"] = "c940c46f5fce12a67836da951bb9b117"

EDITS = {
    'finance_app.py': [
        ('f1', None,
         '        p = dict(drawer=a["drawer_p"], dr_bhawna=a["bhawna_p"], dr_manoj=a["manoj_p"], bank=a["bank_p"])\n        p["as_of"] = a["anchor_date"]\n    p["in_unit"] = p["drawer"] + p["dr_bhawna"] + p["dr_manoj"]\n    p["anchor"], p["rows"] = a, b["rows"]\n    return p\n',
         '        p = dict(drawer=a["drawer_p"], dr_bhawna=a["bhawna_p"], dr_manoj=a["manoj_p"], pool=0, bank=a["bank_p"],\n                 with_doctors=a["bhawna_p"] + a["manoj_p"])\n        p["as_of"] = a["anchor_date"]\n    p["in_unit"] = p["drawer"] + p["with_doctors"]\n    p["waiting_days"] = [r["date"] for r in b["rows"] if r.get("waiting_approval")]\n    p["waiting_p"] = sum(r["into_drawer_p"] for r in b["rows"] if r.get("waiting_approval"))\n    p["anchor"], p["rows"] = a, b["rows"]\n    return p\n'),
        ('f2', 'RANGE',
         'def _sj_cash_position(con, p):',
         'def _sj_bank(con):\n    """S363: every cash deposit -- from the drawer (cash_movement) and from the doctors\'\n    pool (cash_pool_deposit, the owner\'s ruling of 21-Sep) -- newest first."""\n    deps = [dict(date=r["d"], amount_p=int(r["a"]), ref=(r["r"] or ""))\n            for r in con.execute(\n                "SELECT de.business_date d, cm.amount_p a, cm.reference r FROM cash_movement cm "\n                "JOIN day_entry de ON de.id=cm.day_entry_id WHERE de.unit=? AND cm.party=\'bank\' "\n                "AND cm.direction=\'out\'", (UNIT,))]\n    for x in _sjc.pool_deposits(con, UNIT):\n        deps.append(dict(date=x["date"], amount_p=x["amount_p"],\n                         ref="from the doctors\' pool -- %s %s" % (x["bank"], x["place"] or "")))\n    deps.sort(key=lambda x: x["date"], reverse=True)\n    return deps\n\n\ndef _sj_cash_position(con, p):\n    """/finance/api/cash-position from the one calculation -- every key the pages read.\n    reserve = the doctors\' pool: Dr Bhawna + Dr Manoj, one pool (the owner\'s ruling of 21-Sep)."""\n    a = p["anchor"]\n    deps = _sj_bank(con)\n    trail = [dict(date=a["anchor_date"], frm="count", to="pool", amount=rupees(a["bhawna_p"] + a["manoj_p"]),\n                  note="opening -- counted on %s (Dr Bhawna %s + Dr Manoj %s)"\n                       % (a["anchor_date"], rupees(a["bhawna_p"]), rupees(a["manoj_p"])), kind="count")]\n    for r in p["rows"]:\n        for h in r["handed"]:\n            if h["to"] in ("dr_bhawna", "dr_manoj", "pool"):\n                trail.append(dict(date=r["date"], frm="drawer", to=h["to"], amount=rupees(h["amount_p"]),\n                                  note=(h["note"] or "")[:120], kind=h.get("src") or "handover"))\n        for x in r.get("banked") or []:\n            trail.append(dict(date=x["date"], frm="pool", to="bank", amount=rupees(x["amount_p"]),\n                              note="deposited -- %s %s" % (x["bank"], x["place"] or ""), kind="deposit"))\n    trail.sort(key=lambda x: x["date"] or "", reverse=True)\n    days = [dict(date=r["date"], drawer=rupees(r["close"]["drawer"]),\n                 unbanked=rupees(r["close"]["drawer"] + r["close"]["with_doctors"]))\n            for r in p["rows"]][-60:]\n    return dict(ok=True, basis="sanjeevni_cash",\n                bank_deposits=[dict(date=x["date"], amount=rupees(x["amount_p"]), ref=x["ref"]) for x in deps[:40]],\n                reserve_detail=trail, manoj_detail=[],\n                drawer=rupees(p["drawer"]), reserve=rupees(p["with_doctors"]), with_manoj=rupees(0),\n                parked=rupees(p["with_doctors"]), bank_deposited=rupees(sum(x["amount_p"] for x in deps)),\n                bank_count=len(deps), last_bank_date=(deps[0]["date"] if deps else None),\n                unbanked=rupees(p["in_unit"]),\n                waiting_days=p["waiting_days"], waiting=rupees(p["waiting_p"]), waiting_p=p["waiting_p"],\n                drawer_p=p["drawer"], reserve_p=p["with_doctors"], with_manoj_p=0,\n                parked_p=p["with_doctors"], unbanked_p=p["in_unit"], baseline_p=a["bhawna_p"] + a["manoj_p"],\n                as_of=p["as_of"], since=a["anchor_date"], days=days)\n\n\n'),
        ('f3', None,
         '        held = [dict(party=k, held=rupees(int(_sjp[k]))) for k in ("drawer", "dr_bhawna", "dr_manoj")\n                if int(_sjp[k])]\n',
         '        held = [dict(party=n, held=rupees(int(_sjp[k]))) for n, k in (("drawer", "drawer"),\n                ("Dr Bhawna & Dr Manoj (pool)", "with_doctors")) if int(_sjp[k])]\n'),
        ('f4', None,
         '        parked = [dict(party=p, name=PARTY_NAMES.get(p, p), amount=rupees(int(_sjp[p])),\n                       amount_p=int(_sjp[p])) for p in ("dr_manoj", "dr_bhawna")]\n',
         '        parked = [dict(party="pool", name="Dr Manoj & Dr Bhawna", amount=rupees(int(_sjp["with_doctors"])),\n                       amount_p=int(_sjp["with_doctors"]))]\n'),
        ('f5', None,
         '                drawer, parked, closing = (_sjp["drawer"], _sjp["dr_bhawna"] + _sjp["dr_manoj"],\n',
         '                drawer, parked, closing = (_sjp["drawer"], _sjp["with_doctors"],\n'),
        ('f6', 'def api_tile(',
         '    since = None\n    if dep:\n        since = (today() - parse_iso_date(dep["d"])).days\n\n    nc = con.execute("SELECT COALESCE(SUM(noncash_p),0) n FROM v_cash_ledger "\n                     "WHERE unit=? AND business_date LIKE ?", (UNIT, ym + "%")).fetchone()["n"]\n\n    return jsonify(ok=True, unit_name="Sanjeevni Medicos",\n',
         '    if _sjp:                               # S363: a pool deposit is a bank deposit too\n        _dl = _sj_bank(con)\n        dep = {"d": _dl[0]["date"]} if _dl else dep\n    since = None\n    if dep:\n        since = (today() - parse_iso_date(dep["d"])).days\n\n    nc = con.execute("SELECT COALESCE(SUM(noncash_p),0) n FROM v_cash_ledger "\n                     "WHERE unit=? AND business_date LIKE ?", (UNIT, ym + "%")).fetchone()["n"]\n\n    return jsonify(ok=True, unit_name="Sanjeevni Medicos",\n'),
    ],
    'darpan_kal.py': [
        ('k1', None,
         '        if iso in covered and not (row and row.get("handed_p") is not None and not row.get("received_at")):\n            continue                                   # S362: already paid over\n',
         '        if (iso in covered or (r["status"] in ("approved", "locked") and iso >= _anchor_date(con))) and \\\n                not (row and row.get("handed_p") is not None and not row.get("received_at")):\n            continue                                   # S363: paid over, or approved (= to the pool)\n'),
        ('k2', None,
         '    hand = {}\n    for h in _sjc.handovers(con, a["anchor_date"], "9999-12-31", _unit, set(a["pre_anchor_custody_ids"])):\n        k = {"dr_manoj": "to_manoj_p", "dr_bhawna": "to_bhawna_p", "bank": "to_bank_p"}.get(h["to"], "to_other_p")\n        hand.setdefault(h["date"][:7], {}).setdefault(k, 0)\n        hand[h["date"][:7]][k] += h["amount_p"]\n    out = []\n    for m in _sjc.month_rows(con, _unit):\n        o = old.get(m["ym"], {})\n        r = dict(m, expense_p=o.get("expense_p", 0), adjust_p=o.get("adjust_p", 0), back_p=o.get("back_p", 0))\n        r["net_cash_p"] = m["cash_income_p"] + r["adjust_p"]\n        for k in ("to_manoj_p", "to_bhawna_p", "to_bank_p", "to_other_p"):\n            r[k] = (hand.get(m["ym"], {}).get(k, 0) + (o.get(k, 0) if m["ym"] < a["anchor_date"][:7] else 0)\n                    + (_pre_anchor_moves(con, m["ym"], a, k) if m["ym"] == a["anchor_date"][:7] else 0))\n        r["handed_p"] = r["to_manoj_p"] + r["to_bhawna_p"] + r["to_bank_p"] + r["to_other_p"]\n',
         '    hand = _sjc.month_moves(con, _unit)           # S363: every handover once, approved days to the pool, deposits\n    out = []\n    for m in _sjc.month_rows(con, _unit):\n        o = old.get(m["ym"], {})\n        r = dict(m, expense_p=o.get("expense_p", 0), adjust_p=o.get("adjust_p", 0), back_p=o.get("back_p", 0))\n        r["net_cash_p"] = m["cash_income_p"] + r["adjust_p"]\n        for k in ("to_manoj_p", "to_bhawna_p", "to_pool_p", "to_bank_p", "to_other_p"):\n            r[k] = (hand.get(m["ym"], {}).get(k, 0) + (o.get(k, 0) if m["ym"] < a["anchor_date"][:7] else 0)\n                    + (_pre_anchor_moves(con, m["ym"], a, k) if m["ym"] == a["anchor_date"][:7] else 0))\n        r["handed_p"] = r["to_manoj_p"] + r["to_bhawna_p"] + r["to_pool_p"] + r["to_bank_p"] + r["to_other_p"]\n'),
        ('k3', None,
         '        c = cov.get(x["date"])\n',
         '        if x.get("handed_p") is None and x["date"] not in cov and x.get("status") in ("approved", "locked") \\\n                and x["date"] >= _anchor_date(con):\n            x["handed_p"], x["handed_to"], x["received"] = x["net_cash_p"], "pool", True   # S363\n        c = cov.get(x["date"])\n'),
        ('k4', None,
         'def _month_days_s359(con, ym):\n',
         'def _anchor_date(con):\n    """S363: the counted anchor\'s date, or a date nothing reaches when there is none."""\n    if not _has(con, "cash_anchor"):\n        return "9999-12-31"\n    r = con.execute("SELECT MAX(anchor_date) FROM cash_anchor WHERE unit=?", (_unit,)).fetchone()\n    return r[0] or "9999-12-31"\n\n\ndef _month_days_s359(con, ym):\n'),
    ],
    'finance_yesbank.py': [
        ('y1', 'def reconcile_cash_deposits(',
         '        "  AND e.business_date BETWEEN ? AND ? ORDER BY e.business_date, m.id",\n        (unit, date_from, date_to)).fetchall()]\n',
         '        "  AND e.business_date BETWEEN ? AND ? ORDER BY e.business_date, m.id",\n        (unit, date_from, date_to)).fetchall()]\n    # S363: a cash deposit made from the doctors\' pool is a booked deposit too (the owner\'s\n    # ruling of 21-Sep) -- it lives in cash_pool_deposit, never as a drawer movement.\n    try:\n        booked += [dict(id=-r[0], date=r[1], amount_p=r[2]) for r in con.execute(\n            "SELECT id, deposit_date, amount_p FROM cash_pool_deposit WHERE unit=? "\n            "AND deposit_date BETWEEN ? AND ? ORDER BY deposit_date, id", (unit, date_from, date_to)).fetchall()]\n        booked.sort(key=lambda b: (b["date"], b["id"]))\n    except Exception:                                      # noqa: BLE001 -- no pool table: nothing to add\n        pass\n'),
    ],
    'finance_ui/finance_approvals.html': [
        ('a1', None,
         '      row("In Darpan’s drawer", j.drawer, drawerDetail)+\n      row("Parked · Dr Bhawna", j.reserve, trailTable(j.reserve_detail))+\n      row("Parked · Dr Manoj", j.with_manoj, trailTable(j.manoj_detail))+\n',
         '      row("In Darpan’s drawer"+((j.waiting_days&&j.waiting_days.length)?\' <span class="mut" style="font-weight:400">· \'+j.waiting_days.length+\' day(s) awaiting your approval</span>\':\'\'), j.drawer, drawerDetail)+\n      (j.basis==="sanjeevni_cash"\n        ? row("With you & Dr Bhawna (pool)", j.reserve, trailTable(j.reserve_detail))\n        : row("Parked · Dr Bhawna", j.reserve, trailTable(j.reserve_detail))+\n          row("Parked · Dr Manoj", j.with_manoj, trailTable(j.manoj_detail)))+\n'),
        ('a2', None,
         '    var NM={dr_bhawna:"Dr Bhawna",drawer:"Drawer (Darpan)",counter:"Counter (Vinay)",dr_manoj:"Dr Manoj",bank:"Bank"};\n',
         '    var NM={dr_bhawna:"Dr Bhawna",drawer:"Drawer (Darpan)",counter:"Counter (Vinay)",dr_manoj:"Dr Manoj",bank:"Bank",pool:"Pool (you & Dr Bhawna)",count:"Counted"};\n'),
    ],
}


def overlay(text, edits, name):
    for tag, where, old, new in edits:
        if where == "RANGE":
            i = text.find(old)
            j = text.find("def opening_p(con, unit, date_iso):", i)
            if i < 0 or text.find(old, i + 1) >= 0 or j < 0:
                raise SystemExit("!! %s %s: range anchor not found exactly once" % (name, tag))
            text = text[:i] + new + text[j:]
            continue
        if where is None:
            a, b = 0, len(text)
        else:
            a, b = s362.span(text, where)
        body = text[a:b]
        if body.count(old) != 1:
            raise SystemExit("!! %s %s: anchor occurs %d times" % (name, tag, body.count(old)))
        text = text[:a] + body.replace(old, new) + text[b:]
    return text


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    s362plan = {"finance_app.py": s362.FA, "darpan_app.py": s362.DA, "darpan_kal.py": s362.KA}
    new = {}
    for f in FROM:
        p = os.path.join(a.dir, f)
        if not os.path.isfile(p) or md5(p) != FROM[f]:
            raise SystemExit("!! %s is not its FROM pin %s -- nothing touched" % (p, FROM[f][:8]))
        text = open(p, encoding="utf-8").read()
        if f in s362plan:
            text = s362.apply(text, s362plan[f], f)
        new[f] = overlay(text, EDITS.get(f, []), f)
    out = a.out or a.dir
    for f, text in new.items():
        dst = os.path.join(out, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not a.out:
            shutil.copy2(os.path.join(a.dir, f), "%s.bak_S363_%s" % (os.path.join(a.dir, f), FROM[f][:8]))
        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("   %s %s -> %s" % (f, FROM[f][:8], md5(dst)))
    print("APPLIED")


if __name__ == "__main__":
    main()
