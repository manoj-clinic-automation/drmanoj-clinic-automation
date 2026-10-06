#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s489.py -- kit S489_SALARY_LAYOUT: THE LIVE-SHAPE WALK. Run ON THE BOX by the installer before
anything is placed (and offline by the builder on a box-shaped tree).

It loads TWO salary engines side by side -- the LIVE /root/staff_register/salary_policy.py and THE KIT'S
-- and has both compute the same months from the same data, read-only:

  PART 1  the ledger exactly as it stands.
          * every figure of every person is IDENTICAL between the two engines, except the four shown
            figures of a private-loan person (salary, advance, net, exact net). What those must be is
            worked out HERE, from the ledger's own lines, never taken from the kit engine:
                 kit salary  = live salary  - the long-term loan's standing instalment
                 kit advance = live advance - the long-term instalment the ledger took
                 kit net     = live net     - what the private page pays him       (to the rupee)
          * for every person, table 1 + table 2 of Sheet 2 add up to the Advance figure of the salary
            sheet AND to the ledger's own 'deducted' figure as the LIVE engine reads it
          * the figures PRINTED on Sheet 2's closing table and on every slip are those figures
          * the common pages (Sheet 2, Sheets 3/4, every slip) never show the private loan
          * the frozen Sheet 3 the lock would save reads back through the register's own
            locked_snapshot() and adds up to the lock's total; no SHEET 5 is written any more
  PART 2  a SCRATCH COPY of the ledger with the kit's one restatement row written by restate_s489.py:
          * the loan's balance falls by exactly Rs 1,000, no other figure of anybody moves
          * the private loan page, row by row, is what the ledger's RAW rows and the history record
            give when worked out here -- in the engine's table and in the figures printed on the page
          * a second run writes nothing; the LIVE ledger's md5 is the same before and after the walk

Nothing is written outside a private folder under /tmp. NO RUPEE FIGURE IS PRINTED (F-31): counts only.

usage:  walk_s489.py <kit dir>        env ROOT (default /root) · MONTHS (default 2026-08,2026-09,<this month>)
"""
import os, re, sys, json, html, shutil, hashlib, sqlite3, tempfile, datetime, importlib.util

N = [0]
FLAT = 1000.0                       # the ledger's flat monthly interest (staff_ledger.INTEREST_RS)


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def norm(v, keys=None):
    """A value as something comparable."""
    if isinstance(v, set):
        return sorted(v)
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items() if keys is None or k in keys}
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    return v


def same_lines(old, new, plan_may_move=False):
    """Ledger lines: every key the live engine wrote must be there, unchanged. The one exception is the
    forward plan ('terms') of a person who has a DEFER or a SKIP recorded: the kit's plan follows it,
    as the ledger's close will (and one advance's defer moves the others behind it in the same queue);
    the live engine's does not. Returns (same, n_plans_that_follow_a_defer)."""
    if len(old) != len(new):
        return False, 0
    moved = 0
    for a, b in zip(old, new):
        for k in a:
            if k not in b:
                return False, 0
            if norm(a[k]) != norm(b[k]):
                if k == "terms" and plan_may_move:
                    moved += 1
                    continue
                return False, 0
    return True, moved


def cells(html_text):
    """Every table row of a piece of HTML as a list of its cells' plain text."""
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html_text, flags=re.S):
        row = []
        for td in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S):
            row.append(html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", td)).strip()))
        out.append(row)
    return out


def shows(doc, figure):
    """True when `figure` (a printed number) stands in `doc` as a number of its own -- not inside a longer one."""
    return re.search(r"(?<![\d,.])%s(?![\d,])" % re.escape(figure), doc) is not None


def want_private(lines, closed):
    """D682, worked out HERE from the ledger's own lines (the live engine's reading of them): the
    long-term loan is the migrated opening balances and any loan with interest. None when there is none."""
    pl = sorted((t for t in lines if t.get("interest_loan") or t.get("bf")),
                key=lambda t: (not t.get("interest_loan"), str(t.get("date", ""))))
    pl = [t for t in pl if t["start"] > 0 or t["taken"] > 0 or t["end"] > 0 or t["recovered"] > 0 or t["interest"] > 0]
    if not pl:
        return None
    owed = sum(t["start"] + t["taken"] for t in pl)
    if closed:
        intr = sum(t["interest"] for t in pl)
    else:
        intr = FLAT if any(t.get("interest_loan") and t["start"] > 0 for t in pl) else 0.0
    kept = round(min(float(pl[0]["inst_raw"]), owed + intr), 2)
    cut = round(sum(t["recovered"] + t["interest"] for t in pl), 2)
    cut_shown = round(min(cut, kept), 2)
    return {"ids": sorted(t["id"] for t in pl), "kept": kept, "cut": cut, "cut_shown": cut_shown,
            "reserve": round(kept - cut_shown, 2) if closed else kept,
            "paid": round(kept - cut_shown, 2) if closed else None}


def raw_instalment(raw, issue_id):
    r = next((x for x in raw if x.get("id") == issue_id), None) or {}
    return float(r.get("instalment") or r.get("amount") or 0)


def expected_loan_rows(raw, loan_id, hist, ym):
    """The private page's table, worked out HERE from the ledger's RAW rows and the history record.
    Returns (opening, [(ym, start, instalment, interest, off_the_loan, added, end)], ledger_adjust)."""
    issue = next(x for x in raw if x.get("id") == loan_id)
    inst = float(issue.get("instalment") or issue["amount"])
    kids = [x for x in raw if x.get("contra_of") == loan_id and x.get("status") == "APPROVED"]
    pre = sorted((p["ym"], p["kind"]) for p in hist.get("pre", []))
    last_pre = pre[-1][0] if pre else ""
    adj = sum(float(x["amount"]) for x in kids if x["category"] == "LOAN_CAPITALISE" and str(x.get("date_from", ""))[:7] <= last_pre)
    led_start = float(issue["amount"]) + adj
    opening = led_start + sum(inst - FLAT for _m, k in pre if k == "paid")
    out, bal = [], opening
    for m, k in pre:
        if m > ym:
            break
        if k == "paid":
            out.append((m, bal, inst, FLAT, inst - FLAT, 0.0, bal - (inst - FLAT)))
            bal -= inst - FLAT
        else:
            out.append((m, bal, 0.0, 0.0, 0.0, 0.0, bal))
    m = "%04d-%02d" % ((int(last_pre[:4]) * 12 + int(last_pre[5:7])) // 12, (int(last_pre[:4]) * 12 + int(last_pre[5:7])) % 12 + 1)
    while m <= ym:
        p = -sum(float(x["amount"]) for x in kids if x["category"] == "ADVANCE_INSTALMENT" and x.get("closed_month") == m)
        i = -sum(float(x["amount"]) for x in kids if x["category"] == "LOAN_INTEREST" and x.get("closed_month") == m)
        c = sum(float(x["amount"]) for x in kids if x["category"] == "LOAN_CAPITALISE" and str(x.get("date_from", ""))[:7] == m)
        out.append((m, bal, p + i, i, p, c, bal - p + c))
        bal = bal - p + c
        t = int(m[:4]) * 12 + int(m[5:7])
        m = "%04d-%02d" % (t // 12, t % 12 + 1)
    return opening, out, adj


PRIV_KEYS = ("base", "adv_ded", "net", "net_exact")
NEW_KEYS = ("base_full", "adv_ded_full", "views", "priv", "net_full")
MON3 = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def compare_month(ym, ro, rn, Pn, raw, privn):
    """PART 1 for one month. Returns (n_staff, n_private, n_loans, n_month_adv, n_plans_moved)."""
    so, sn = ro["staff"], rn["staff"]
    check("%s: both engines compute the same people, in the same order" % ym,
          [s["name"] for s in so] == [s["name"] for s in sn])
    check("%s: both engines agree on closed / enforced / notes" % ym,
          ro["ledger_closed"] == rn["ledger_closed"] and ro["enforced"] == rn["enforced"] and ro["notes"] == rn["notes"])
    closed = bool(rn["ledger_closed"])
    plan_staff = {x.get("staff") for x in raw if x.get("status") == "APPROVED"
                  and x.get("category") in ("ADVANCE_DEFER", "LOAN_SKIP")}
    n_priv = n_loans = n_adv = n_moved = 0
    for a, b in zip(so, sn):
        nm = a["name"]
        is_priv = str(nm).strip().lower() in privn
        lo = a.get("ledger_money") or {}
        for t in lo.get("lines", []):
            t["inst_raw"] = raw_instalment(raw, t["id"])          # the walk's own note, from the raw ledger row
        want = want_private(lo.get("lines", []), closed) if is_priv else None
        for t in lo.get("lines", []):
            t.pop("inst_raw", None)
        priv = b.get("priv")
        for k in a:
            if k == "ledger_money":
                ln = b[k] or {}
                ok, mv = same_lines(lo.get("lines", []), ln.get("lines", []), nm in plan_staff)
                n_moved += mv
                check("%s %s: the ledger's own lines are unchanged" % (ym, nm),
                      ok and all(norm(lo.get(t)) == norm(ln.get(t)) for t in ("start", "taken", "recovered", "interest", "end", "deducted")))
            elif k == "loans":
                check("%s %s: the loan lines are unchanged" % (ym, nm), same_lines(a[k], b[k], nm in plan_staff)[0])
            elif k in PRIV_KEYS and want:
                continue
            else:
                check("%s %s: '%s' is the same in both engines" % (ym, nm, k), norm(a[k]) == norm(b[k]))
        for k in NEW_KEYS:
            check("%s %s: the kit's result carries '%s'" % (ym, nm, k), k in b)
        check("%s %s: base_full / net_full / adv_ded_full are the live engine's figures" % (ym, nm),
              norm(b["base_full"]) == norm(a["base"]) and norm(b["net_full"]) == norm(a["net"])
              and norm(b["adv_ded_full"]) == norm(a["adv_ded"]))
        check("%s %s: a private split exactly when he has a long-term loan this month" % (ym, nm),
              (priv is not None) == (want is not None))
        if want:
            n_priv += 1
            check("%s %s: the private page holds exactly the long-term loan's lines" % (ym, nm),
                  sorted(t["id"] for t in priv["lines"]) == want["ids"])
            check("%s %s: kept aside / taken / paid are what the ledger's lines give when worked out here" % (ym, nm),
                  want["kept"] > 0 and all(abs(priv[k] - want[k]) < 0.005 for k in ("kept", "cut", "cut_shown", "reserve"))
                  and (priv["paid"] is None) == (want["paid"] is None)
                  and (want["paid"] is None or abs(priv["paid"] - want["paid"]) < 0.005))
            check("%s %s: common salary = full salary - the instalment kept aside" % (ym, nm),
                  abs(b["base"] - (a["base"] - want["kept"])) < 0.005 and b["base"] < a["base"])
            check("%s %s: common advance = the ledger's figure - the long-term instalment it took" % (ym, nm),
                  abs(b["adv_ded"] - (a["adv_ded"] - want["cut_shown"])) < 0.005)
            check("%s %s: common net = full net - what the private page pays, to the rupee" % (ym, nm),
                  abs(b["net"] - (a["net"] - want["reserve"])) < 0.005)
            check("%s %s: the exact net moves by the same amount" % (ym, nm),
                  abs(b["net_exact"] - (a["net_exact"] - want["reserve"])) < 0.005)
        v = b["views"]
        n_loans += len(v["loans"])
        n_adv += len(v["month_adv"])
        shown = sum(x["cut"] for x in v["month_adv"]) + sum(L["cut"] for L in v["loans"])
        if closed:
            check("%s %s: table 1 + table 2 make the Advance figure of the salary sheet" % (ym, nm),
                  abs(shown + float((priv or {}).get("extra") or 0) + float(b.get("manual_adv") or 0) - b["adv_ded"]) < 0.5)
            if lo:
                check("%s %s: table 1 + table 2 + the private instalment = the ledger's own 'deducted' (live engine)" % (ym, nm),
                      abs(shown + (want["cut"] if want else 0.0) - float(lo.get("deducted") or 0)) < 0.5)
        ids_adv = [x["id"] for x in v["month_adv"]]
        ids_loan = [i for L in v["loans"] for i in L["ids"]]
        ids_priv = [t["id"] for t in v["priv_lines"]]
        check("%s %s: no advance sits in two tables" % (ym, nm),
              len(set(ids_adv + ids_loan + ids_priv)) == len(ids_adv) + len(ids_loan) + len(ids_priv))
        check("%s %s: every open ledger line is in exactly one table" % (ym, nm),
              all(t["id"] in set(ids_adv + ids_loan + ids_priv) for t in lo.get("lines", [])))
        check("%s %s: only a private-loan person has anything kept off the common tables" % (ym, nm), is_priv or not ids_priv)
        old = {t["id"]: t for t in lo.get("lines", [])}
        for L in v["loans"]:
            mine = [old[i] for i in L["ids"] if i in old]
            took = sum(t["recovered"] + t["interest"] for t in mine)
            check("%s %s: a loan's balance and this month's cut are the ledger's own (live engine's lines)" % (ym, nm),
                  abs(sum(t["end"] for t in mine) - L["balance"]) < 0.5 and (not closed or abs(took - L["cut"]) < 0.5)
                  and abs(sum(x for _m, x, k in L["strip"] if k == "paid") - L["paid"]) < 0.5)
            before = -sum(float(x["amount"]) for x in raw if x.get("contra_of") in L["ids"] and x.get("status") == "APPROVED"
                          and x.get("category") in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")
                          and (x.get("closed_month") or str(x.get("date_from", ""))[:7]) < ym)
            check("%s %s: 'paid so far' is what the RAW ledger rows took before this month, plus this month's cut" % (ym, nm),
                  abs(L["paid"] - (before + (took if closed else 0.0))) < 0.5)
            paid_months = {(x.get("closed_month") or str(x.get("date_from", ""))[:7]) for x in raw
                           if x.get("contra_of") in L["ids"] and x.get("status") == "APPROVED"
                           and x.get("category") in ("ADVANCE_INSTALMENT", "LOAN_INTEREST") and float(x.get("amount") or 0) < 0}
            check("%s %s: 'paid n of N' counts the months the RAW ledger rows collected in" % (ym, nm),
                  L["n_paid"] == len([m for m in paid_months if m < ym or (closed and m == ym)]) and L["n_all"] >= L["n_paid"])
    return len(sn), n_priv, n_loans, n_adv, n_moved


def groups_met(ym, rn, groups):
    """How many loan groups of the kit's record were met this month -- each must be ONE loan line."""
    met = 0
    for g in groups:
        st = next((x for x in rn["staff"] if str(x["name"]).strip().lower() == str(g.get("staff", "")).strip().lower()), None)
        if not st or not st.get("ledger_money"):
            continue
        open_ids = {t["id"] for t in st["ledger_money"]["lines"]}
        known = open_ids | {t["id"] for t in st["ledger_money"].get("cleared", [])}
        want = [i for i in g["ids"] if i in known]
        if not (set(want) & open_ids) or len(want) < 2:
            continue
        holders = [L for L in st["views"]["loans"] if set(L["ids"]) & set(want)]
        check("%s %s: a loan handed over in parts is ONE loan line, with every part in it" % (ym, st["name"]),
              len(holders) == 1 and sorted(holders[0]["ids"]) == sorted(want) and len(holders[0]["parts"]) == len(want))
        check("%s %s: none of its parts is also listed as a month advance" % (ym, st["name"]),
              not (set(want) & {a["id"] for a in st["views"]["month_adv"]}))
        met += 1
    return met


def pages(ym, rn, Pn, sr, privn, restated):
    """Render every page the kit changes and hold what must be true of them. Returns n_slips."""
    closed = bool(rn["ledger_closed"])
    s2 = Pn.sheet2_html(rn, doors=True, back="/x", prefix="/register", approve_html="<b>a</b>")
    s34 = Pn.sheets34_html(rn, approved=True, prefix="/register")
    check("%s: Sheet 2 carries the three advance tables" % ym,
          "1 · This month's advances" in s2 and "2 · Instalment loans" in s2 and "3 · What each salary bears" in s2)
    check("%s: the old two tables are gone" % ym,
          "Advances taken this month" not in s2 and "still being recovered" not in s2)
    check("%s: Sheet 2 has no 'does not add up' note and no 'could not be laid out' note" % ym,
          "Does not add up" not in s2 and "could not be laid out" not in s2)
    check("%s: nobody is sent to a separate money page any more" % ym, "has a separate money page" not in s2)
    check("%s: no SHEET 5 own sheet is written" % ym, "SHEET 5" not in s34 and "FULL WORKING" not in s34)
    total = int(round(sum(st["net"] for st in rn["staff"])))
    if sr is not None:
        snap, why = sr.locked_snapshot(s34, total)
        check("%s: the frozen Sheet 3 reads back through the register's own reader and adds up to the lock total"
              % ym, snap is not None and len(snap) == len(rn["staff"]) and not any(r["own"] for r in snap))
        check("%s: against the same result the lock desk would list no difference" % ym,
              sr.locked_differences(snap, rn["staff"], Pn.money) == [])
    # Sheet 2's closing table prints, for each person in it, the Advance figure of the salary sheet
    t3 = s2.split("3 · What each salary bears", 1)[1].split("</table>", 1)[0]
    bears = {r[0]: r for r in cells(t3) if len(r) == 6}
    if closed:
        for st in rn["staff"]:
            if st["name"] in bears:
                check("%s %s: Sheet 2's closing line prints the Advance figure of the salary sheet" % (ym, st["name"]),
                      bears[st["name"]][3] == Pn.inr(st["adv_ded"]))
            else:
                check("%s %s: a person missing from Sheet 2's closing table has nothing cut" % (ym, st["name"]),
                      abs(float(st["adv_ded"])) < 0.005)
    # tables 1 and 2, and the closing table's last two columns: what is PRINTED is what the views hold
    def by_person(part, width):
        got, cur = {}, None
        for r in cells(part):
            if len(r) != width or r[0] == "Staff":
                continue
            cur = r[0] or cur
            got.setdefault(cur, []).append(r)
        return got
    p1 = by_person(s2.split("1 · This month's advances", 1)[1].split("</table>", 1)[0], 5)
    p2 = by_person(s2.split("2 · Instalment loans", 1)[1].split("</table>", 1)[0], 8)
    dash = "—"
    for st in rn["staff"]:
        v, nm = st["views"], st["name"]
        check("%s %s: table 1 prints each of this month's advances at its amount" % (ym, nm),
              [r[2] for r in p1.get(nm, [])] == [Pn.inr(a["amount"]) for a in v["month_adv"]])
        r2 = p2.get(nm, [])
        check("%s %s: table 2 prints one line per loan: amount, paid n of N, cut this month, balance" % (ym, nm),
              len(r2) == len(v["loans"]) and all(
                  r[1].startswith("Rs %s given" % Pn.inr(L["amount"]))
                  and r[3] == (("%s %d of %d" % (Pn.inr(L["paid"]), L["n_paid"], L["n_all"])) if L["n_all"] else Pn.inr(L["paid"]))
                  and r[4] == (Pn.inr(L["cut"]) if L["cut"] > 0.005 else dash)
                  and r[5] == Pn.inr(L["balance"] if closed else L["balance_after"])
                  for r, L in zip(r2, v["loans"])))
        if nm in bears:
            bal = sum(L["balance_after"] for L in v["loans"])
            nxt = sum(L["next"] for L in v["loans"])
            check("%s %s: the closing line prints the loan balance after and next month's instalment" % (ym, nm),
                  bears[nm][4] == (Pn.inr(bal) if bal > 0.005 else dash) and bears[nm][5] == (Pn.inr(nxt) if nxt > 0.005 else dash))
    n_slips = 0
    slips = s34.split('<div class="s4pg slip"')
    for st in rn["staff"]:
        # worked out HERE: a slip for a loan paid back over more than one salary that was cut or is still owed
        want = any((L["cut"] > 0.005 or L["balance_after"] > 0.005)
                   and len([1 for _m, _a, k in L["strip"] if k in ("paid", "now", "due")]) != 1
                   for L in st["views"]["loans"])
        marker = "SALARY SLIP — %s — " % str(st["name"]).upper()
        mine = [x for x in slips[1:] if marker in x]
        check("%s %s: a slip exactly when an instalment loan runs" % (ym, st["name"]),
              (len(mine) == 1) == want and (marker in s34) == want)
        if not want:
            continue
        n_slips += 1
        rows = cells(mine[0])
        sal = [r for r in rows if len(r) == 2 and r[0] == "Salary"]
        net = [r for r in rows if len(r) == 2 and r[0].startswith("Is mahine mila")]
        adv = [r for r in rows if len(r) == 2 and r[0].startswith("Advance kata — kul")]
        check("%s %s: the slip prints the salary and the net of the common sheet" % (ym, st["name"]),
              len(sal) == 1 and sal[0][1] == Pn.inr(st["base"]) and len(net) == 1 and net[0][1] == Pn.inr(st["net"]))
        check("%s %s: the slip's advance total is the Advance figure of the salary sheet" % (ym, st["name"]),
              len(adv) == 1 and (not closed or adv[0][1] == Pn.inr(st["adv_ded"])))
        check("%s %s: a slip before the ledger close says it is not final" % (ym, st["name"]),
              closed or "FINAL NAHI" in mine[0])
        v = st["views"]
        kist = [r for r in rows if len(r) == 2 and r[0].startswith("Loan ki kist")]
        cutl = [L for L in v["loans"] if L["cut"] > 0.005]
        check("%s %s: the slip prints one instalment row per loan cut: which instalment, of how many, and how much" % (ym, st["name"]),
              len(kist) == len(cutl) and all(
                  ("kist %d / %d · loan Rs %s (" % (L["n_paid"] + (0 if closed else 1), L["n_all"], Pn.inr(L["amount"]))) in r[0]
                  and r[1] == Pn.inr(L["cut"]) for r, L in zip(kist, cutl)))
        madv = [r for r in rows if len(r) == 2 and r[0].startswith("Is mahine ka advance")]
        check("%s %s: the slip prints this month's advances as one row adding up to them" % (ym, st["name"]),
              (len(madv) == 1 and madv[0][1] == Pn.inr(sum(a["cut"] for a in v["month_adv"]))) if v["month_adv"] else not madv)
        text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", mine[0])))
        for L in v["loans"]:
            due = [1 for _m, _a, k in L["strip"] if k == "due"]
            check("%s %s: the slip says what is still owed on each loan" % (ym, st["name"]),
                  (("Loan Rs %s (%s): poora ho gaya." % (Pn.inr(L["amount"]), L["given"])) in text)
                  if (L["balance_after"] <= 0.005 and not due) else (("Loan baaki: Rs %s (" % Pn.inr(L["balance_after"])) in text))
    check("%s: as many slips are printed as there are people with a running loan" % ym, s34.count("SALARY SLIP — ") == n_slips)
    for st in rn["staff"]:
        priv = st.get("priv")
        if str(st["name"]).strip().lower() not in privn:
            continue
        lp = Pn.sheet2_html(rn, doors=True, back="/x", staff=st["name"])
        check("%s %s: the private page is the loan ledger" % (ym, st["name"]),
              "LOAN LEDGER" in lp and ">PRIVATE<" in lp)
        if not priv:
            continue
        check("%s %s: the loan ledger has its table and its three facts" % (ym, st["name"]),
              "table class='lled'" in lp and lp.count("class='f'") == 3 and "Opening balance" in lp)
        check("%s %s: until the ledger carries the restatement the page SAYS so; once it does, no 'Check' note" % (ym, st["name"]),
              ("<b>Check:</b>" in lp) == (not restated))
        secret = set()
        for t in priv["lines"]:
            for x in (t["end"], t["start"], t["amount"]):
                if x >= 50000:
                    secret.add(Pn.inr(x)); secret.add(Pn.money(x))
        for name, doc in (("Sheet 2", s2), ("Sheets 3/4 and the slips", s34)):
            check("%s: %s never shows the private loan's balances" % (ym, name), not any(shows(doc, x) for x in secret))
            check("%s: %s never says 'interest'" % (ym, name), "interest" not in doc.lower())
        check("%s %s: the common sheet shows the reduced salary, never the full one, in his row" % (ym, st["name"]),
              ("<td><b>%s</b></td><td class='n'>%s</td>" % (st["name"], Pn.money(st["base"]))) in s34
              and ("<td><b>%s</b></td><td class='n'>%s</td>" % (st["name"], Pn.money(st["base_full"]))) not in s34
              and st["base"] < st["base_full"])
    return n_slips


def loan_page_checks(ym, b, r2, Pn, raw2, loan_id):
    """PART 2: the private page against the RAW ledger rows and the history record, worked out here."""
    nm = b["name"]
    closed = bool(r2["ledger_closed"])
    main_t = next((t for t in b["priv"]["lines"] if t["id"] == loan_id), None)
    if main_t is None:
        return 0
    hist = Pn.loan_history(nm)
    check("%s %s: the history record of his loan is read, whatever the case of the name" % (ym, nm),
          hist.get("loan_id") == loan_id and len(hist.get("pre", [])) >= 1 and Pn.loan_history(nm.upper()) == hist)
    last_pre = max(p["ym"] for p in hist["pre"])
    skips_raw = sorted(str(x.get("date_from", ""))[:7] for x in raw2 if x.get("category") == "LOAN_SKIP"
                       and x.get("contra_of") == loan_id and x.get("status") == "APPROVED"
                       and str(x.get("date_from", ""))[:7] <= last_pre)
    check("%s %s: the months the record calls skipped are the months the ledger has a skip recorded for" % (ym, nm),
          sorted(p["ym"] for p in hist["pre"] if p["kind"] == "skip") == skips_raw)
    months = sorted(p["ym"] for p in hist["pre"])
    check("%s %s: the record's months run without a gap up to where the ledger begins" % (ym, nm),
          all(int(b[:4]) * 12 + int(b[5:7]) - int(a[:4]) * 12 - int(a[5:7]) == 1 for a, b in zip(months, months[1:]))
          and not any(x.get("contra_of") == loan_id and x.get("status") == "APPROVED"
                      and x.get("category") in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")
                      and (x.get("closed_month") or "") <= last_pre for x in raw2)
          and any(x.get("contra_of") == loan_id and x.get("status") == "APPROVED" and x.get("category") == "ADVANCE_INSTALMENT"
                  and x.get("closed_month") == "%04d-%02d" % ((int(last_pre[:4]) * 12 + int(last_pre[5:7])) // 12,
                                                              (int(last_pre[:4]) * 12 + int(last_pre[5:7])) % 12 + 1) for x in raw2))
    opening_w, rows_w, adj_w = expected_loan_rows(raw2, loan_id, hist, ym)
    rows, opening, note = Pn.loan_ledger(main_t, hist, ym, closed)
    past = [x for x in rows if x["status"] != "next"]
    check("%s %s: the ledger's adjustment for the months before it began is the one the record names" % (ym, nm),
          abs(adj_w - float(hist.get("ledger_adjust"))) < 0.005)
    check("%s %s: the history meets the ledger -- no 'Check' note" % (ym, nm), note == "")
    check("%s %s: the opening balance is the one the RAW ledger rows and the history give" % (ym, nm),
          abs(opening - opening_w) < 0.005 and past and past[0]["ym"] == hist["pre"][0]["ym"])
    check("%s %s: the table has one row per month, each as the RAW ledger rows give it" % (ym, nm),
          len(past) == len(rows_w) and all(
              x["ym"] == w[0] and abs(x["start"] - w[1]) < 0.005 and abs(x["inst"] - w[2]) < 0.005
              and abs(x["interest"] - w[3]) < 0.005 and abs(x["principal"] - w[4]) < 0.005
              and abs(x["added"] - w[5]) < 0.005 and abs(x["end"] - w[6]) < 0.005 for x, w in zip(past, rows_w)))
    check("%s %s: the table ends on the ledger's own balance" % (ym, nm), abs(past[-1]["end"] - main_t["end"]) < 0.005)
    lp = Pn.sheet2_html(r2, doors=False, staff=nm)
    check("%s %s: the page prints no 'Check' note" % (ym, nm), "<b>Check:</b>" not in lp)
    tbl = cells(lp.split("<table class='lled'>", 1)[1].split("</table>", 1)[0])
    body = [r for r in tbl if len(r) == 7 and r[0] not in ("Salary month",) and not r[6].startswith("Next") and " to " not in r[0]]
    dash = "—"
    check("%s %s: the page prints one row per month" % (ym, nm), len(body) == len(rows_w))
    for r, w in zip(body, rows_w):
        check("%s %s %s: the printed row is the row worked out here" % (ym, nm, w[0]),
              r[0] == "%s %s" % (MON3[int(w[0][5:7])], w[0][:4]) and r[1] == Pn.inr(w[1])
              and r[2] == (Pn.inr(w[2]) if w[2] else dash) and r[4] == (Pn.inr(w[4]) if w[4] else dash)
              and r[5] == Pn.inr(w[6]) and (r[3].split(" ")[0] == (Pn.inr(w[3]) if w[3] else (Pn.inr(abs(w[5])) if w[5] else dash))))
    opened = [r for r in tbl if len(r) == 3 and r[0].startswith("Opening balance")]
    total = [r for r in tbl if len(r) == 7 and " to " in r[0]]
    check("%s %s: the opening line and the totals line print the same figures" % (ym, nm),
          len(opened) == 1 and opened[0][1] == Pn.inr(opening_w) and len(total) == 1
          and total[0][2] == Pn.inr(sum(w[2] for w in rows_w)) and total[0][4] == Pn.inr(sum(w[4] for w in rows_w))
          and total[0][5] == Pn.inr(rows_w[-1][6]) and total[0][3].split(" ")[0] == Pn.inr(sum(w[3] for w in rows_w)))
    nxt_e = [x for x in rows if x["status"] == "next"]
    nxt_p = [r for r in tbl if len(r) == 7 and r[6].startswith("Next")]
    check("%s %s: the 'Next' row is printed exactly when the engine plans one, and prints its figures" % (ym, nm),
          len(nxt_p) == len(nxt_e) and all(
              abs(x["start"] - rows_w[-1][6]) < 0.005 and abs(x["end"] - (x["start"] - x["principal"])) < 0.005
              and r[1] == Pn.inr(x["start"]) and r[2] == Pn.inr(x["inst"]) and r[4] == Pn.inr(x["principal"])
              and r[5] == Pn.inr(x["end"]) for r, x in zip(nxt_p, nxt_e)))
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", lp)))
    pv = b["priv"]
    if closed:
        check("%s %s: the foot line prints what was kept aside, what was taken and what was paid to him" % (ym, nm),
              ("Rs %s kept aside from salary · Rs %s instalment taken · %s." % (
                  Pn.inr(pv["kept"]), Pn.inr(pv["cut_shown"]),
                  ("Rs %s paid to him" % Pn.inr(pv["paid"])) if pv["paid"] > 0.005 else "nothing left to pay him")) in text)
    else:
        check("%s %s: before the close the foot line prints what is kept aside" % (ym, nm),
              ("Rs %s is kept aside from the salary for this instalment" % Pn.inr(pv["kept"])) in text)
    for t in pv["lines"]:
        if t["id"] != loan_id:
            check("%s %s: the other long-term line is printed with its own balance" % (ym, nm),
                  ("of Rs %s: balance Rs %s — " % (Pn.inr(t["amount"]), Pn.inr(t["end"]))) in text)
    facts = re.findall(r"<div class='l'>(.*?)</div><div class='v'>(.*?)</div>", lp)
    check("%s %s: the three fact boxes print the opening balance, the instalment and the balance now" % (ym, nm),
          len(facts) == 3 and facts[0][1] == Pn.inr(opening_w) and facts[1][1] == "%s a month" % Pn.inr(raw_instalment(raw2, loan_id))
          and facts[2][1] == Pn.inr(rows_w[-1][6]))
    return 1


def main():
    kit = os.path.abspath(sys.argv[1])
    ROOT = os.path.abspath(os.environ.get("ROOT", "/root"))
    live = os.path.join(ROOT, "staff_register")
    ledger_dir = os.environ.get("LEDGER_DIR") or os.path.join(ROOT, "staff_ledger")
    led_file = os.path.join(ledger_dir, "ledger.jsonl")
    for p in (os.path.join(live, "salary_policy.py"), os.path.join(kit, "salary_policy.py"),
              os.path.join(ROOT, "staff_ledger.py"), led_file):
        check("exists: %s" % p, os.path.isfile(p))
    scratch = tempfile.mkdtemp(prefix="s489_walk_", dir="/tmp")
    try:
        os.environ["ATT_DIR"] = ROOT
        os.environ["LEDGER_DIR"] = ledger_dir
        os.environ.setdefault("STAFF_CSV", os.path.join(ROOT, "staff_master.csv"))
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        # the register's database: a private copy (read through a read-only door), as S303's walk did
        dbp = os.path.join(scratch, "sr_walk.db")
        live_db = os.path.join(live, "staff_register.db")
        if os.path.isfile(live_db):
            s = sqlite3.connect("file:%s?mode=ro" % live_db, uri=True)
            d = sqlite3.connect(dbp)
            s.backup(d); d.close(); s.close()
        os.environ["SR_DB_PATH"] = dbp
        os.environ["ATT_REGISTER_DB"] = dbp
        led_md5_before = md5_file(led_file)

        Po = load(os.path.join(live, "salary_policy.py"), "sp_live_s489")
        Pn = load(os.path.join(kit, "salary_policy.py"), "sp_kit_s489")
        check("the kit engine says it is 1.17-S489", getattr(Pn, "VERSION", "") == "1.17-S489")
        check("the live engine is the one this kit was built on (no VERSION, has own_sheet_html)",
              not hasattr(Po, "VERSION") and hasattr(Po, "own_sheet_html"))
        # the kit engine reads the box's own settings and hold ledger, exactly as it will once placed
        Pn.BASE = live
        Pn.SETTINGS_PATH = Po.SETTINGS_PATH
        Pn.SETTINGS_AUDIT = Po.SETTINGS_AUDIT
        Pn.HOLD_LEDGER = Po.HOLD_LEDGER
        lp_path = os.path.join(scratch, "loan_pages.json")
        D = load(os.path.join(kit, "data_s489.py"), "data_s489")
        check("the kit's loan record writes", D.main(["data", "--write", lp_path]) == 0 and D.main(["data", "--check", lp_path]) == 0)
        Pn.LOAN_PAGES_PATH = lp_path
        lpr = Pn.loan_pages()
        check("the engine reads the kit's loan record whole: every group, every history, nothing dropped",
              len(lpr["groups"]) == len(D.RECORD["groups"]) and len(lpr["history"]) == len(D.RECORD["history"])
              and all(g["ids"] == w["ids"] for g, w in zip(lpr["groups"], D.RECORD["groups"]))
              and all(len(lpr["history"][k.lower()]["pre"]) == len(v["pre"]) for k, v in D.RECORD["history"].items()))
        privn = Pn.private_loan_names(Pn.load_settings())
        check("one private-loan name is set", len(privn) == 1)

        sr = None
        try:                                            # the register's own frozen-sheet reader -- a COPY of the live
            srd = os.path.join(scratch, "sr")           # file, loaded from the private folder (as S303's walk did), so
            os.makedirs(srd)                            # whatever the app makes when it loads lands there, not in /root
            shutil.copy2(os.path.join(live, "staff_register.py"), srd)
            os.chdir(srd)
            sr = load(os.path.join(srd, "staff_register.py"), "sr_live_s489")
            check("the register's reader is there", hasattr(sr, "locked_snapshot") and hasattr(sr, "locked_differences"))
        except SystemExit:
            raise
        except Exception as e:
            print("   (the register app could not be loaded here: %s -- the frozen-sheet read-back is skipped)" % type(e).__name__)
            sr = None
        if os.environ.get("S489_NEED_REGISTER") == "1":
            check("on the box the register's reader must load", sr is not None)

        import staff_ledger as LIVE_L                     # the module both engines read the ledger through
        raw = LIVE_L.load_ledger()
        RS = load(os.path.join(kit, "restate_s489.py"), "restate_s489")
        restated = any(r.get("restate") == RS.TAG for r in raw)

        today = datetime.date.today().strftime("%Y-%m")
        months = [m for m in os.environ.get("MONTHS", "2026-08,2026-09,%s" % today).split(",") if m]
        months = sorted(set(months))
        done, results = [], {}
        n_groups = [0]
        n_moved = 0
        for ym in months:
            try:
                ro = Po.compute(ym)
            except Exception as e:
                print("   %s: the LIVE engine cannot compute this month here (%s) -- skipped" % (ym, type(e).__name__))
                continue
            rn = Pn.compute(ym)
            ns, npv, nl, na, mv = compare_month(ym, ro, rn, Pn, raw, privn)
            n_moved += mv
            nslip = pages(ym, rn, Pn, sr, privn, restated)
            n_groups[0] += groups_met(ym, rn, lpr["groups"])
            results[ym] = rn
            done.append("%s: %d people · %d on a private loan · %d month advances · %d loans · %d slips · %s"
                        % (ym, ns, npv, na, nl, nslip, "ledger closed" if rn["ledger_closed"] else "ledger NOT closed"))
        check("at least one month was walked", bool(done))
        check("a private loan was met in the walk", any(st.get("priv") for r in results.values() for st in r["staff"]))
        if any(m in results for m in ("2026-08", "2026-09", "2026-10", "2026-11")):
            check("the loan handed over in parts (the kit's group record) was met in the walk", n_groups[0] >= 1)

        # ---------------- PART 2: the restatement, on a scratch copy of the ledger ----------------
        sl = os.path.join(scratch, "staff_ledger")
        os.makedirs(sl)
        shutil.copy2(led_file, os.path.join(sl, "ledger.jsonl"))
        sm = RS.load_module(os.path.join(ROOT, "staff_ledger.py"), sl)
        rows0 = sm.load_ledger()
        state, row, why = RS.plan(sm, rows0, "walk")
        check("the restatement either plans one row or is already in the ledger (%s)" % why, state in ("plan", "done"))
        already = state == "done"
        check("the ledger carries the restatement exactly when the tool says it is done", already == restated)
        if not already:
            check("the planned row is the one ruled", row["category"] == "LOAN_CAPITALISE" and row["amount"] == -1000
                  and row["contra_of"] == RS.LOAN_ID and row["date_from"] == "2026-04" and row["status"] == "APPROVED"
                  and row["restate"] == "S489" and row["closed_month"] == "2026-07")
            closed_before = sm.closed_months(rows0)
            bal0 = RS.balance(sm, rows0)
            RS.apply_row(sm, sl, row, md5_file(os.path.join(sl, "ledger.jsonl")), "walk")
            rows1 = sm.load_ledger()
            check("one row more, every earlier row untouched, the loan lower by exactly the ruled amount",
                  len(rows1) == len(rows0) + 1 and rows1[:len(rows0)] == rows0 and RS.balance(sm, rows1) == bal0 - 1000)
            check("no new 'closed month' appears in the ledger", sm.closed_months(rows1) == closed_before)
            st2, row2, why2 = RS.plan(sm, rows1, "walk")
            check("a second run writes nothing", st2 == "done" and row2 is None)
            check("a backup and a correction note were left beside the scratch ledger",
                  any(f.startswith("ledger.jsonl.bak_restate_S489_") for f in os.listdir(sl))
                  and os.path.isdir(os.path.join(sl, "corrections")))
            # the tool takes back ONLY its own row, and only while it is the last line
            probe = os.path.join(scratch, "probe.jsonl")
            shutil.copy2(os.path.join(sl, "ledger.jsonl"), probe)
            with open(probe, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": "someone-else", "category": "X"}) + "\n")
            size = os.path.getsize(probe)
            check("the tool never takes its row back from under a row written after it",
                  RS.take_back(probe, row["id"]) is False and os.path.getsize(probe) == size)
            shutil.copy2(os.path.join(sl, "ledger.jsonl"), probe)
            check("while its row is the last line, taking it back leaves the ledger byte for byte as it was",
                  RS.take_back(probe, row["id"]) is True and md5_file(probe) == led_md5_before)
        raw2 = sm.load_ledger()
        real_dir = LIVE_L.LEDGER_DIR
        n_pages = 0
        try:
            LIVE_L.LEDGER_DIR = sl
            for ym, r1 in results.items():
                r2 = Pn.compute(ym)
                for a, b in zip(r1["staff"], r2["staff"]):
                    pa, pb = a.get("priv"), b.get("priv")
                    for k in a:
                        if k in ("ledger_money", "loans", "views", "priv", "open_bal"):
                            continue
                        check("%s %s: with the restatement '%s' does not move" % (ym, a["name"], k), norm(a[k]) == norm(b[k]))
                    if not pb:
                        check("%s %s: the ledger's lines do not move" % (ym, a["name"]),
                              norm((a["ledger_money"] or {}).get("end")) == norm((b["ledger_money"] or {}).get("end")))
                        continue
                    ta = {t["id"]: t for t in pa["lines"]}
                    tb = {t["id"]: t for t in pb["lines"]}
                    for i in tb:
                        want = -1000.0 if (i == RS.LOAN_ID and not already) else 0.0
                        check("%s %s: only the ruled loan's balance moves, by exactly the ruled amount" % (ym, a["name"]),
                              abs((tb[i]["end"] - ta[i]["end"]) - want) < 0.005)
                    check("%s %s: kept / taken / paid on the private page do not move" % (ym, a["name"]),
                          all(norm(pa[k]) == norm(pb[k]) for k in ("kept", "cut", "cut_shown", "paid", "reserve", "status")))
                    if ym >= "2026-07":
                        n_pages += loan_page_checks(ym, b, r2, Pn, raw2, RS.LOAN_ID)
        finally:
            LIVE_L.LEDGER_DIR = real_dir
        check("the private loan page was walked with the restatement", n_pages >= 1)
        check("the LIVE ledger is byte for byte what it was before the walk", md5_file(led_file) == led_md5_before)
        check("the kit engine's own selftest passes", _selftest(kit, scratch))
        for ln in done:
            print("   " + ln)
        if n_moved:
            print("   %d forward plan(s) differ from the live engine's because a defer or a skip is recorded — the kit's follows it" % n_moved)
        print("   restatement on the scratch copy: %s" % ("already in the ledger" if already else "1 row written, balance -1,000, nothing else moved"))
        print("WALK OK — %d checks; %d month(s); the live ledger untouched" % (N[0], len(done)))
    finally:
        os.chdir("/tmp")
        shutil.rmtree(scratch, ignore_errors=True)


def _selftest(kit, scratch):
    """The kit engine's own selftest, in a private folder (it writes a settings file beside itself)."""
    import subprocess
    d = os.path.join(scratch, "st")
    os.makedirs(d)
    shutil.copy2(os.path.join(kit, "salary_policy.py"), d)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out = subprocess.run([sys.executable, "-B", os.path.join(d, "salary_policy.py"), "--selftest"],
                         cwd=d, env=env, capture_output=True, text=True, timeout=120)
    return out.returncode == 0 and out.stdout.strip().splitlines()[-1:] == ["PASS"]


if __name__ == "__main__":
    main()
