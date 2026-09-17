#!/usr/bin/env python3
"""S299_STOCK_CHECK_HUB -- the Stock Check tile opens the whole flow; the swaps in the
09-Sep workbook's TRY TO MATCH layout; every confirmed swap becomes Marg vouchers at once.

S299 is the held S297_STOCK_CHECK_HUB (built 17-Sep, never published) with the owner's two
fixes of 17-Sep evening, under a fresh kit number (F-512: a kit that sat publishable is not
edited): (a) he types Darpan's answers too -- the hub says so and gives him the button;
(b) a confirmed swap is STOCK ISSUE on the short item and STOCK RECEIVE on the extra item for
the swapped quantity, reason "swap confirmed", at once -- on Amir's board, the Marg cleanup
Excel and the hub's step 6; a part swap gives its lines without waiting for the remainder, a
whole swap never reads CHANGE 0. stock_amir.html joins the patched files.

The owner, 17-Sep-2026: "Can this URL be accessed from a tile in my portal page? If not,
that is the proper place for it, not these fragmented and hidden URLs. Make a stock check
tile and populate the entire flow there ... and the previous outputs of orthotic matching
-- that was a good format, I would like you to follow that format only."

The format is D:\\Downloads\\margsync\\_analysis\\Sanjeevni_Orthotic_Loss_and_Correction_Voucher_09Sep2026.xlsx,
sheet TRY TO MATCH: Family | Item that is SHORT | Item that is EXTRA | Qty | Rate of the item
that left | Rate of the item billed | Difference per unit | How close | Confirmed? (yes / no).
The plan is S235 T5: the engine (family, then nearest size) proposes, the owner answers yes or
no per pair, it never applies itself; table stock_match.

stock_app.py (anchored edits)
  1. PAGE_HUB beside PAGE_LOSS;
  2. the TRY TO MATCH engine (stock_match, _match_proposals, _match_apply) before _pad_report_data;
  3. _pad_report_data applies the answers: a YES takes its units off the short line and the
     extra line (difference and value scale), a line wholly explained reads "swap confirmed --
     no loss"; the count's own figures are never touched; the proposals ride out as `matches`;
  4. Darpan's list waits for a Yes or No on every proposal (replaces the S294 word rule), and
     carries shortages only -- never a surplus, never a line a swap has settled;
  5. the list PDF learns which lines a swap has reduced;
  6. the hub: /page/hub, /api/pad/hub/<cid>, /api/pad/match/<cid> (POST), /api/pad/match/<cid>.xlsx.
pad_receipt.py (Darpan's list): columns Qty in Marg | Physical <day> | Difference, as the workbook;
  a swapped line prints its remainder and says so under the item.
stock_desk.html: the footer's "Darpan's list" link becomes "Stock check -- every step".
stock_hub.html: NEW -- the page.
portal.py: the Stock Check tile opens /finance/stock/page/hub (anyone who is not the checker is
  sent on to the counting screen, where the tile went before).

    python3 -B patch_stock_check_hub_s299.py --app stock_app.py --receipt pad_receipt.py \
        --desk stock_desk.html --portal portal.py --amir stock_amir.html
        [--app-from M --receipt-from M --desk-from M --portal-from M --amir-from M]
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

MATCH_BLOCK = "# ---------------------------------------------------------------------------\n# S299 TRY TO MATCH -- was the wrong item billed? (S235 T5, the 09-Sep workbook's\n# sheet of that name, now a screen.) The engine proposes, the owner answers yes or\n# no per pair, and it never applies itself. A YES takes the swapped units off both\n# lines -- the short line and the extra line -- so the loss, the desk and Darpan's\n# list all read the remainder; the count's own figures are never touched.\n# ---------------------------------------------------------------------------\nMATCH_SCHEMA = \"\"\"\nCREATE TABLE IF NOT EXISTS stock_match (\n  id         INTEGER PRIMARY KEY,         -- S299: the owner's answer on a proposed swap, append-only\n  count_id   INTEGER NOT NULL,            -- the ROOT count\n  short_item TEXT NOT NULL,\n  over_item  TEXT NOT NULL,\n  qty        INTEGER NOT NULL,            -- units, as proposed when he answered\n  answer     TEXT NOT NULL,               -- YES | NO | OPEN (OPEN clears the answer)\n  note       TEXT,\n  by_user    TEXT,\n  at         TEXT NOT NULL\n);\nCREATE INDEX IF NOT EXISTS idx_stock_match ON stock_match(count_id, short_item, over_item);\n\"\"\"\n\nMATCH_SIZES = (\"XS\", \"S\", \"M\", \"L\", \"XL\", \"XXL\", \"XXXL\")\n_MATCH_SIZE_ALIAS = {\"XXX\": \"XXXL\", \"SMALL\": \"S\", \"MEDIUM\": \"M\", \"LARGE\": \"L\", \"UNIVERSAL\": \"UNI\"}\n_MATCH_SIDE = (\"LF\", \"RT\", \"LEFT\", \"RIGHT\", \"LT\")\n_MATCH_CLIPPED = (\"UNISO\", \"ELAST\", \"ELA\", \"LYCRA\", \"CONT\", \"GRAY\", \"GREY\")\n\n\ndef _match_ensure(con):\n    con.executescript(MATCH_SCHEMA)\n\n\ndef _match_type_size(item):\n    \"\"\"(product type, size) of an orthotic: brand, side and filler words out, the size\n    kept apart. TYNOR WRIST SPLINT LF M ELAS and ... RT M ELAST are one type, size M.\"\"\"\n    u = \" \" + _re221.sub(r\"[^A-Z0-9]+\", \" \", (item or \"\").upper()) + \" \"\n    u = u.replace(\" L S \", \" LS \")                      # L S BELT is the LS belt, not sizes L and S\n    toks = [t for t in u.split() if t]\n    size, keep = \"\", []\n    for t in toks:\n        t2 = _MATCH_SIZE_ALIAS.get(t, t)\n        if t2 in MATCH_SIZES:\n            size = size or t2\n            continue\n        if t in _BRAND_WORDS or t in _MATCH_SIDE or t in _MATCH_CLIPPED or t.isdigit():\n            continue\n        keep.append(t)\n    return \" \".join(keep), size\n\n\ndef _match_close(s1, s2):\n    \"\"\"0 same size, 1 one size apart, 2 sizes differ (or unknown).\"\"\"\n    if s1 == s2:\n        return 0\n    if s1 in MATCH_SIZES and s2 in MATCH_SIZES and abs(MATCH_SIZES.index(s1) - MATCH_SIZES.index(s2)) == 1:\n        return 1\n    return 2\n\n\nMATCH_CLOSE_TEXT = {0: \"same size\", 1: \"one size apart\", 2: \"sizes differ\", 9: \"same salt\"}\n\n\ndef _match_rate(x):\n    \"\"\"Paise per unit of a line, from the line's own value -- the rate the loss uses.\"\"\"\n    try:\n        return int(round(abs(int(x[\"mrp_p\"])) / float(abs(int(x[\"diff\"]))))) if x.get(\"mrp_p\") is not None and x.get(\"diff\") else None\n    except (TypeError, ValueError, ZeroDivisionError):\n        return None\n\n\ndef _match_proposals(diffs, pairs, words):\n    \"\"\"The pairs to put to the owner, count-day figures only (so they never reshuffle):\n    orthotics by product type, then the nearest size; medicines by the identical Marg\n    salt (D385). Never a consumable, never a line below zero in Marg, never a line he has\n    parked (kept elsewhere is not a swap). Greedy: the closest pair takes its units first.\"\"\"\n    ok = lambda x: ((x.get(\"marg\") or 0) >= 0 and x[\"lane\"] not in (\"consume\", \"dead\")      # noqa: E731\n                    and not x.get(\"consumable\") and (words.get(x[\"item\"]) or {}).get(\"action\") != \"PARKED\")\n    out = []\n\n    def allocate(kind, group, shorts, overs, rank_of):\n        rem = {x[\"item\"]: -int(x[\"diff\"]) for x in shorts}\n        rem.update({x[\"item\"]: int(x[\"diff\"]) for x in overs})\n        cand = []\n        for s in shorts:\n            for o in overs:\n                rs, ro = _match_rate(s), _match_rate(o)\n                cand.append((rank_of(s, o), abs((rs or 0) - (ro or 0)), s[\"item\"], o[\"item\"], s, o, rs, ro))\n        cand.sort(key=lambda c: c[:4])\n        for rank, _gap, _si, _oi, s, o, rs, ro in cand:\n            q = min(rem[s[\"item\"]], rem[o[\"item\"]])\n            if q <= 0:\n                continue\n            rem[s[\"item\"]] -= q; rem[o[\"item\"]] -= q\n            out.append(dict(kind=kind, family=group, short=s[\"item\"], over=o[\"item\"], qty=q,\n                            short_pack=s[\"pack\"], over_pack=o[\"pack\"], rate_left_p=rs, rate_billed_p=ro,\n                            gap_p=(None if rs is None or ro is None else ro - rs), close=rank,\n                            close_text=MATCH_CLOSE_TEXT[rank]))\n\n    groups = {}\n    for x in diffs:\n        if x[\"diff\"] and ok(x) and (x[\"lane\"] == \"ortho\" or _is_orthotic(x[\"item\"])):\n            groups.setdefault(_match_type_size(x[\"item\"])[0], []).append(x)\n    for g in sorted(groups):\n        xs = groups[g]\n        sh = [x for x in xs if x[\"diff\"] < 0]; ov = [x for x in xs if x[\"diff\"] > 0]\n        if sh and ov:\n            label = \" \".join(w if len(w) <= 2 else w.lower() for w in g.split())\n            allocate(\"ortho\", label[:1].upper() + label[1:], sh, ov,\n                     lambda s, o: _match_close(_match_type_size(s[\"item\"])[1], _match_type_size(o[\"item\"])[1]))\n    by = {x[\"item\"]: x for x in diffs}\n    for p in sorted(pairs or [], key=lambda p: p[\"salt\"]):\n        sh = [by[m[\"item\"]] for m in p.get(\"short\") or [] if m[\"item\"] in by and ok(by[m[\"item\"]]) and not _is_orthotic(m[\"item\"])]\n        ov = [by[m[\"item\"]] for m in p.get(\"over\") or [] if m[\"item\"] in by and ok(by[m[\"item\"]]) and not _is_orthotic(m[\"item\"])]\n        if sh and ov:\n            allocate(\"med\", p[\"salt\"], sh, ov, lambda s, o: 9)\n    return out\n\n\ndef _match_answers(con, root_id):\n    \"\"\"(short, over) -> newest answer row; OPEN clears it.\"\"\"\n    _match_ensure(con)\n    out = {}\n    for r in con.execute(\"SELECT short_item, over_item, qty, answer, note, by_user, at FROM stock_match \"\n                         \"WHERE count_id=? ORDER BY id\", (root_id,)):\n        k = (r[0], r[1])\n        if r[3] == \"OPEN\":\n            out.pop(k, None)\n            continue\n        out[k] = dict(answer=r[3], qty=r[2], note=r[4] or \"\", by=r[5] or \"\", at=r[6])\n    return out\n\n\ndef _match_apply(con, root_id, diffs, pairs, words):\n    \"\"\"Proposals + answers onto the lines. A YES takes its units off both lines (diff and\n    value scale with it); a line wholly explained by confirmed swaps and carrying no word\n    of the owner's reads 'swap confirmed -- no loss'. Returns the proposals.\"\"\"\n    props = _match_proposals(diffs, pairs, words)\n    ans = _match_answers(con, root_id)\n    by = {x[\"item\"]: x for x in diffs}\n    for p in props:\n        a = ans.get((p[\"short\"], p[\"over\"]))\n        p[\"answer\"] = (a or {}).get(\"answer\")\n        p[\"answered_by\"] = (a or {}).get(\"by\", \"\"); p[\"answered_at\"] = (a or {}).get(\"at\", \"\")\n        p[\"note\"] = (a or {}).get(\"note\", \"\")\n        p[\"words\"] = bool(words.get(p[\"short\"])) and bool(words.get(p[\"over\"]))\n        p[\"settled\"] = bool(p[\"answer\"]) or p[\"words\"]\n        if p[\"answer\"] != \"YES\":\n            continue\n        for item, sign, other in ((p[\"short\"], 1, p[\"over\"]), (p[\"over\"], -1, p[\"short\"])):\n            x = by.get(item)\n            if not x:\n                continue\n            x.setdefault(\"diff_count_day\", x[\"diff\"]); x.setdefault(\"mrp_p_count_day\", x.get(\"mrp_p\")); x.setdefault(\"cost_p_count_day\", x.get(\"cost_p\"))\n            x[\"swapped\"] = int(x.get(\"swapped\") or 0) + p[\"qty\"]\n            x.setdefault(\"swap_with\", []).append(other)\n    for x in diffs:\n        if not x.get(\"swapped\"):\n            continue\n        d0 = int(x[\"diff_count_day\"]); n = min(abs(d0), int(x[\"swapped\"]))\n        rem = d0 + n if d0 < 0 else d0 - n\n        f = (abs(rem) / float(abs(d0))) if d0 else 0.0\n        x[\"diff\"] = rem\n        x[\"mrp_p\"] = None if x[\"mrp_p_count_day\"] is None else int(round(x[\"mrp_p_count_day\"] * f))\n        x[\"cost_p\"] = None if x[\"cost_p_count_day\"] is None else int(round(x[\"cost_p_count_day\"] * f))\n        if rem == 0 and not x.get(\"word\"):\n            x[\"word\"] = dict(action=\"EXPLAINED\", label=\"swap confirmed -- no loss\", note=\"swapped with \" + \", \".join(x[\"swap_with\"]),\n                             by=\"\", at=\"\", swap=True)\n    return props\n"
HUB_BLOCK = "# ---------------------------------------------------------------------------\n# S299 THE STOCK CHECK HUB -- the owner, 17-Sep-2026: \"can this URL be accessed from\n# a tile in my portal page? If not, that is the proper place for it, not these\n# fragmented and hidden URLs. Make a stock check tile and populate the entire flow\n# there.\" The portal's Stock Check tile opens this page: one count, every step in\n# the order it happens, each with where it stands and the one door that does it.\n# Nothing here computes anew -- it reads the report, the lists, the words.\n# ---------------------------------------------------------------------------\ndef _hub_rs(p_):\n    return \"\" if p_ is None else _loss_rs(p_).replace(\" \", \"\\u00a0\")      # Rs and the figure never part on a narrow column\n\n\ndef _hub_match_rows(props):\n    out = []\n    for p in props:\n        out.append(dict(kind=p[\"kind\"], family=p[\"family\"], short=p[\"short\"], over=p[\"over\"], qty=p[\"qty\"],\n                        qty_text=_qw(p[\"qty\"], p[\"short_pack\"]),\n                        rate_left=(None if p[\"rate_left_p\"] is None else _hub_rs(p[\"rate_left_p\"] * (p[\"short_pack\"] if p[\"kind\"] == \"med\" else 1))),\n                        rate_billed=(None if p[\"rate_billed_p\"] is None else _hub_rs(p[\"rate_billed_p\"] * (p[\"over_pack\"] if p[\"kind\"] == \"med\" else 1))),\n                        per=(\"strip\" if p[\"kind\"] == \"med\" and (p[\"short_pack\"] or 1) > 1 else \"each\"),\n                        gap=(None if p[\"gap_p\"] is None else _hub_rs(abs(p[\"gap_p\"]) * (p[\"short_pack\"] if p[\"kind\"] == \"med\" else 1))),\n                        close=p[\"close_text\"], answer=p.get(\"answer\") or \"\", settled=bool(p.get(\"settled\")),\n                        by_words=bool(p.get(\"words\")) and not p.get(\"answer\"),\n                        answered_by=p.get(\"answered_by\") or \"\", answered_text=(_r_stamp(p[\"answered_at\"]) + \" IST\") if p.get(\"answered_at\") else \"\"))\n    return out\n\n\ndef _hub_data(con, cid):\n    d = _pad_report_data(con, cid)\n    if d is None:\n        return None\n    root = d[\"count_id\"]\n    props = d.get(\"matches\") or []\n    diffs = d[\"differences\"]\n    tr = _tranches(con, root)\n    taken = {i for t in tr for i in t[\"items\"]}\n    # 2 -- the swaps, and the bridge the S235 lesson asks for (short at the count, taken out, still short)\n    short0 = sum(-int(x.get(\"mrp_p_count_day\", x[\"mrp_p\"])) for x in diffs\n                 if int(x.get(\"diff_count_day\", x[\"diff\"])) < 0 and x.get(\"mrp_p_count_day\", x[\"mrp_p\"]) is not None)\n    short1 = sum(-int(x[\"mrp_p\"]) for x in diffs if x[\"diff\"] < 0 and x[\"mrp_p\"] is not None)\n    unpriced = sum(1 for x in diffs if int(x.get(\"diff_count_day\", x[\"diff\"])) < 0 and x.get(\"mrp_p_count_day\", x[\"mrp_p\"]) is None)\n    yes = [p for p in props if p.get(\"answer\") == \"YES\"]\n    m_open = [p for p in props if not p.get(\"settled\")]\n    match = dict(total=len(props), answered=sum(1 for p in props if p.get(\"settled\")), open=len(m_open),\n                 yes=len(yes), no=sum(1 for p in props if p.get(\"answer\") == \"NO\"),\n                 yes_units=sum(p[\"qty\"] for p in yes), units=sum(p[\"qty\"] for p in props if p[\"kind\"] == \"ortho\"),\n                 rows=_hub_match_rows(props), short_count_day=_hub_rs(short0), taken_out=_hub_rs(short0 - short1),\n                 still_short=_hub_rs(short1), unpriced=unpriced,\n                 state=(\"done\" if props and not m_open else (\"now\" if props else \"done\")))\n    # 3 -- Darpan's lists\n    pool = dict(med=len([x for x in _tranche_pool(d, \"med\") if x[\"item\"] not in taken]),\n                ortho=len([x for x in _tranche_pool(d, \"ortho\") if x[\"item\"] not in taken]))\n    hold = _tranche_hold(d, \"med\")\n    out_with = [t for t in tr if not t[\"returned_at\"]]\n    lists = dict(tranches=tr, pool=pool, hold=hold, with_darpan=len(out_with),\n                 state=(\"wait\" if hold else (\"done\" if tr and not out_with and not pool[\"med\"] and not pool[\"ortho\"] else \"now\")))\n    # 4 -- Amir types the answers\n    back = [t for t in tr if t[\"returned_at\"]]\n    back_items = {i for t in back for i in t[\"items\"]}\n    typed = sum(1 for x in diffs if x[\"item\"] in back_items and x.get(\"answer\"))\n    answers = dict(returned=len(back), items=len(back_items), typed=typed,\n                   state=(\"wait\" if not back else (\"done\" if typed >= len(back_items) else \"now\")))\n    # 5 -- the owner's word on each line, and the loss\n    tot = d[\"totals\"]\n    words = dict(written_off=tot[\"written_off\"], written_off_rs=_hub_rs(tot[\"written_off_p\"]), pursue=tot[\"pursue\"],\n                 pursue_rs=_hub_rs(tot[\"pursue_p\"]), parked=tot[\"parked\"], parked_rs=_hub_rs(tot[\"parked_p\"]),\n                 explained=tot[\"explained\"], open=tot[\"open\"], open_rs=_hub_rs(tot[\"open_p\"]),\n                 state=(\"wait\" if match[\"state\"] != \"done\" else (\"done\" if not tot[\"open\"] else \"now\")))\n    # 6 -- what goes back into Marg\n    v_issue = [x for x in diffs if (x.get(\"word\") or {}).get(\"action\") == \"WRITE_OFF\"]\n    v_fix = [x for x in diffs if (x.get(\"word\") or {}).get(\"action\") in (\"MARG_FIX\", \"EXPLAINED\")]\n    vouchers = dict(issue=len(v_issue), fix=len(v_fix), state=(\"wait\" if tot[\"open\"] else \"now\"))\n    # 7 -- the proof, 8 -- the lines to pursue\n    return dict(ok=True, count_id=root, day=d[\"day\"], as_on=d[\"as_on\"], bill_no=d[\"bill_no\"], bill_date=d[\"bill_date_text\"],\n                counted_by=d[\"counted_by\"], entered_by=d[\"entered_by\"], counted=d[\"counted\"], agreed=d[\"agreed\"],\n                differed=d[\"differed\"], not_counted=d[\"not_counted\"], seal_ok=d[\"seal_ok\"], closed=d.get(\"closed\"),\n                sealed_text=\", \".join(s[\"sealed_text\"] for s in d[\"seals\"] if s.get(\"finding_no\")) or \"\",\n                match=match, lists=lists, answers=answers, words=words, vouchers=vouchers,\n                proof=dict(state=(\"done\" if d.get(\"closed\") else \"wait\")),\n                pursue=dict(lines=tot[\"pursue\"], state=(\"wait\" if not tot[\"pursue\"] else \"now\")),\n                links=dict(report=\"/finance/stock/page/report?count=%d\" % root, diffs_pdf=d[\"links\"][\"diffs_pdf\"],\n                           desk=\"/finance/stock/page/desk?count=%d\" % root, loss=d[\"links\"][\"loss_page\"],\n                           amir=d[\"links\"][\"amir_page\"], cleanup=d[\"links\"][\"cleanup\"], ortho=d[\"links\"][\"ortho\"],\n                           drift=\"/finance/stock/page/drift\", count=\"/finance/stock/page/count\",\n                           match_xlsx=\"/finance/stock/api/pad/match/%d.xlsx\" % root))\n\n\n@bp.route(\"/page/hub\")\ndef page_hub():\n    \"\"\"THE STOCK CHECK TILE OPENS HERE (S299). The owner's page; anyone else who holds\n    the tile is taken to the counting screen, exactly where the tile used to go.\"\"\"\n    u, err = _require(\"checker\", \"maker\", \"viewer\")\n    if err:\n        return err\n    from flask import Response, redirect                      # noqa: PLC0415\n    if not _may_decide(u):\n        return redirect(\"/finance/stock/page/count\", code=302)\n    con = _db()\n    ensure_schema(con)\n    _pad_ensure(con)\n    cid = request.args.get(\"count\", \"\").strip()\n    if not cid.isdigit():\n        r = con.execute(\"SELECT id FROM stock_count WHERE unit=? AND id NOT IN \"\n                        \"(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1\", (_unit,)).fetchone()\n        cid = str(r[0]) if r else \"0\"\n    try:\n        with io.open(PAGE_HUB, \"r\", encoding=\"utf-8\") as fh:\n            html = fh.read()\n    except IOError:\n        return jsonify(ok=False, error=\"missing\", message=\"stock_hub.html is not beside stock_app.py\"), 503\n    boot = json.dumps(dict(count_id=int(cid), user=(u or {}).get(\"user\") or \"\"))\n    return Response(html.replace(\"/*__BOOT__*/\", \"window.BOOT=\" + boot + \";\"), mimetype=\"text/html\",\n                    headers={\"Cache-Control\": \"no-store\"})\n\n\n@bp.route(\"/api/pad/hub/<int:cid>\")\ndef api_pad_hub(cid):\n    u, err = _require(\"checker\")\n    if err:\n        return err\n    if not _may_decide(u):\n        return jsonify(ok=False, error=\"forbidden\", message=\"This page is the owner's.\"), 403\n    con = _db()\n    ensure_schema(con)\n    _pad_ensure(con)\n    d = _hub_data(con, cid)\n    if d is None:\n        return jsonify(ok=False, error=\"not_found\", message=\"No count #%d.\" % cid), 404\n    return jsonify(**d)\n\n\n@bp.route(\"/api/pad/match/<int:cid>\", methods=[\"POST\"])\ndef api_pad_match(cid):\n    \"\"\"The owner's YES or NO on one proposed swap -- or OPEN to take the answer back.\n    Append-only; only a pair the engine proposes today can be answered.\"\"\"\n    u, err = _require(\"checker\")\n    if err:\n        return err\n    if not _may_decide(u):\n        return jsonify(ok=False, error=\"forbidden\", message=\"Only the doctor confirms a swap.\"), 403\n    b = request.get_json(silent=True) or {}\n    short, over = str(b.get(\"short\") or \"\").strip(), str(b.get(\"over\") or \"\").strip()\n    answer = str(b.get(\"answer\") or \"\").upper().strip()\n    note = (b.get(\"note\") or \"\").strip()[:200]\n    if answer not in (\"YES\", \"NO\", \"OPEN\") or not short or not over:\n        return jsonify(ok=False, error=\"bad_request\", message=\"short, over and YES / NO / OPEN are needed.\"), 400\n    con = _db()\n    ensure_schema(con)\n    _pad_ensure(con)\n    d = _pad_report_data(con, cid)\n    if d is None:\n        return jsonify(ok=False, error=\"not_found\", message=\"No count #%d.\" % cid), 404\n    p = [m for m in d.get(\"matches\") or [] if m[\"short\"] == short and m[\"over\"] == over]\n    if not p:\n        return jsonify(ok=False, error=\"no_such_pair\", message=\"That pair is not proposed on this count.\"), 400\n    con.execute(\"INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)\",\n                (d[\"count_id\"], short, over, int(p[0][\"qty\"]), answer, note or None, (u or {}).get(\"user\") or \"\", now_iso()))\n    con.commit()\n    msg = {\"YES\": \"Swap confirmed: %s billed for %s.\" % (over, short), \"NO\": \"Not a swap: %s stays short.\" % short,\n           \"OPEN\": \"Answer taken back.\"}[answer]\n    return jsonify(ok=True, answer=answer, message=msg)\n\n\n@bp.route(\"/api/pad/match/<int:cid>.xlsx\")\ndef api_pad_match_xlsx(cid):\n    \"\"\"TRY TO MATCH, as the 09-Sep workbook's sheet of that name -- with his answers.\"\"\"\n    u, err = _require(\"checker\")\n    if err:\n        return err\n    if not _may_decide(u):\n        return jsonify(ok=False, error=\"forbidden\", message=\"This sheet is the owner's.\"), 403\n    con = _db()\n    ensure_schema(con)\n    _pad_ensure(con)\n    h = _hub_data(con, cid)\n    if h is None:\n        return jsonify(ok=False, error=\"not_found\", message=\"No count #%d.\" % cid), 404\n    rows = []\n    for kind, title in ((\"ortho\", \"ORTHOTICS -- by product, then the nearest size\"), (\"med\", \"MEDICINES -- the same salt in Marg\")):\n        rs = [r for r in h[\"match\"][\"rows\"] if r[\"kind\"] == kind]\n        if not rs:\n            continue\n        rows.append([title, \"\", \"\", \"\", \"\", \"\", \"\", \"\", \"\"])\n        for r in rs:\n            rows.append([r[\"family\"], r[\"short\"], r[\"over\"], r[\"qty_text\"], r[\"rate_left\"] or \"not priced\",\n                         r[\"rate_billed\"] or \"not priced\", r[\"gap\"] or \"\", r[\"close\"],\n                         {\"YES\": \"yes\", \"NO\": \"no\"}.get(r[\"answer\"], \"decided on the desk\" if r[\"by_words\"] else \"\")])\n    rows.append([\"Short at the count\", h[\"match\"][\"short_count_day\"], \"\", \"\", \"\", \"\", \"\", \"\", \"\"])\n    rows.append([\"Taken out by confirmed swaps\", h[\"match\"][\"taken_out\"], \"\", \"\", \"\", \"\", \"\", \"\", \"\"])\n    rows.append([\"Still short\", h[\"match\"][\"still_short\"], \"\", \"\", \"\", \"\", \"\", \"\", \"\"])\n    return _xlsx_response(_xlsx_rows(\n        \"TRY TO MATCH -- WAS THE WRONG ITEM BILLED? -- stock count #%d (%s)\" % (h[\"count_id\"], h[\"day\"] or \"\"),\n        \"Where one product is short and its near neighbour is over, the likely story is not theft but a counter error: one item left the shelf and a different one was billed. Pairing them cancels two mistakes instead of writing off both. A pairing is a SUGGESTION until it is confirmed.\",\n        [\"Family\", \"Item that is SHORT\", \"Item that is EXTRA\", \"Qty\", \"Rate of the item that left\", \"Rate of the item billed\",\n         \"Difference per unit\", \"How close\", \"Confirmed? (yes / no)\"],\n        rows, {0: 24, 1: 32, 2: 32, 3: 10, 4: 14, 5: 14, 6: 12, 7: 16, 8: 18}),\n        \"STOCK_COUNT_%s_TRY_TO_MATCH.xlsx\" % (h[\"day\"] or \"\"))\n"

OLD_HELD = '''def _tranche_held(d):
    """S294: (open same-salt pairs, open orthotic swap families). A pair or a family is open
    until EVERY member that differs carries a word of the owner's -- the swap comes first.
    "Darpan counts again" is a word here: it is how he sends a paired line on to Darpan."""
    spoken = {x["item"]: bool(x.get("word")) for x in d["differences"]}
    open_pairs = [p for p in (d.get("pairs") or [])
                  if not all(spoken.get(o["item"]) for o in (p.get("over") or []) + (p.get("short") or []))]
    open_fams = [f for f in (d.get("ortho_families") or []) if f.get("short") and f.get("over")
                 and any(not spoken.get(m["item"]) for m in f.get("members") or [] if m.get("state") == "diff")]
    return open_pairs, open_fams
'''
NEW_HELD = '''def _tranche_held(d):
    """S299: (open medicine swaps, open orthotic swaps) -- a pair on TRY TO MATCH with no Yes
    or No yet, and not settled by the owner's word on both its lines. The swap comes first."""
    open_ = [p for p in (d.get("matches") or []) if not p.get("settled")]
    return [p for p in open_ if p["kind"] == "med"], [p for p in open_ if p["kind"] == "ortho"]
'''
OLD_HOLD = '''    open_pairs, open_fams = _tranche_held(d)
    parts = []
    if open_pairs:
        parts.append("%d same-salt pair%s" % (len(open_pairs), "" if len(open_pairs) == 1 else "s"))
    if open_fams:
        parts.append("%d orthotic swap famil%s (%s)" % (len(open_fams), "y" if len(open_fams) == 1 else "ies",
                                                         ", ".join(f["key"] for f in open_fams[:4])))
    if not parts:
        return ""
    return "Darpan's list comes after the swaps. Still waiting for your word on the desk: " + " and ".join(parts) + "."
'''
NEW_HOLD = '''    open_med, open_ortho = _tranche_held(d)
    parts = []
    if open_ortho:
        parts.append("%d orthotic pair%s" % (len(open_ortho), "" if len(open_ortho) == 1 else "s"))
    if open_med:
        parts.append("%d medicine pair%s" % (len(open_med), "" if len(open_med) == 1 else "s"))
    if not parts:
        return ""
    return "Darpan's list comes after the swaps. Still waiting for your Yes or No on Try to match: " + " and ".join(parts) + "."   # S299
'''

APP_EDITS = [
    ('PAGE_LOSS = os.path.join(HERE, "stock_loss.html")      # S228 LOSS DESK: the owner\'s own page\n',
     'PAGE_LOSS = os.path.join(HERE, "stock_loss.html")      # S228 LOSS DESK: the owner\'s own page\n'
     'PAGE_HUB = os.path.join(HERE, "stock_hub.html")        # S299 HUB: the Stock Check tile -- every step of a count\n'),
    ('def _pad_report_data(con, root_id):\n', MATCH_BLOCK + '\n\ndef _pad_report_data(con, root_id):\n'),
    ('    # the cleanup lane also names the MATCHED items nobody sold (sitting dead)\n',
     '    matches = _match_apply(con, _root, diffs, pairs, words)   # S299 TRY TO MATCH: his Yes takes the units off both lines\n'
     '    # the cleanup lane also names the MATCHED items nobody sold (sitting dead)\n'),
    ('differences=diffs, lanes=lanes, pairs=pairs,', 'differences=diffs, lanes=lanes, pairs=pairs, matches=matches,'),
    ('        if (x.get("marg") or 0) < 0:\n            continue\n',
     '        if (x.get("marg") or 0) < 0:\n            continue\n'
     '        if int(x["diff"] or 0) >= 0:                           # S299: a surplus, or a line a swap has settled, is never on his list\n'
     '            continue\n'),
    (OLD_HELD, NEW_HELD),
    (OLD_HOLD, NEW_HOLD),
    ('    rows = {r["item"]: r for r in d["rows"]}\n    d = dict(d, rows=[rows[i] for i in t["items"] if i in rows], tranche=t)\n',
     '    rows = {r["item"]: r for r in d["rows"]}\n'
     '    rep = _pad_report_data(con, cid)                          # S299: a confirmed swap shows on the list\n'
     '    for x in (rep or {}).get("differences") or []:\n'
     '        if x.get("swapped") and x["item"] in rows:\n'
     '            rows[x["item"]] = dict(rows[x["item"]], swapped=int(x["swapped"]), swap_with=list(x.get("swap_with") or []))\n'
     '    d = dict(d, rows=[rows[i] for i in t["items"] if i in rows], tranche=t)\n'),
    ('@bp.route("/page/loss")\n', HUB_BLOCK + '\n\n@bp.route("/page/loss")\n'),
]

RECEIPT_EDITS = [
    ('       ("Shelf counted", _LL + 380, "r", 0), ("Marg stock", _LL + 460, "r", 0), ("Difference", _LL + 550, "r", 0),',
     '       ("Qty in Marg", _LL + 380, "r", 0), ("Physical", _LL + 460, "r", 0), ("Difference", _LL + 550, "r", 0),'),
    ('        for label, x, align, _w in _TC:\n            p.text(x, yy, label, 7.5, bold=True, align=align)',
     '        for label, x, align, _w in _TC:\n'
     '            p.text(x, yy, (getattr(self, "phys_label", "") or label) if label == "Physical" else label, 7.5, bold=True, align=align)   # S299'),
    ('''        if self.need(_DROW + 2):
            self.thead(cont=True)
        p = self.pdf
        yy = self.y - _DROW + 8
        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["counted"], r["pack"]), _units(r["marg"], r["pack"]),
                ("over " if (r["diff"] or 0) > 0 else "") + _units(r["diff"], r["pack"])]   # S294: shelf, then Marg, then the gap
        for (label, x, align, w), v in zip(_TC[:6], vals):
            p.text(x, yy, _fit(v, 8.5, w) if w else _latin(v), 9.5 if label == "Difference" else 8.5,
                   bold=(label in ("Item", "Difference")), align=align)
        top, bot = self.y + 1.0, self.y - _DROW + 4.5''',
     '''        sw = int(r.get("swapped") or 0)                       # S299: units a confirmed swap took off this line
        h = _DROW + (9 if sw else 0)
        if self.need(h + 2):
            self.thead(cont=True)
        p = self.pdf
        yy = self.y - _DROW + 8
        d0 = int(r["diff"] or 0)
        rem = (d0 + min(sw, -d0)) if d0 < 0 else (d0 - min(sw, d0))
        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["marg"], r["pack"]), _units(r["counted"], r["pack"]),
                ("over " if rem > 0 else "") + _units(rem, r["pack"])]   # S299: Qty in Marg, Physical, the difference -- as the 09-Sep workbook
        for (label, x, align, w), v in zip(_TC[:6], vals):
            p.text(x, yy, _fit(v, 8.5, w) if w else _latin(v), 9.5 if label == "Difference" else 8.5,
                   bold=(label in ("Item", "Difference")), align=align)
        if sw:
            p.text(_LL + 22, yy - 9, _fit("%s on the count; %s swapped with %s" % (_units(d0, r["pack"]), _units(sw, r["pack"]),
                                                                           ", ".join(r.get("swap_with") or [])), 7, 520), 7, gray=0.4)
        top, bot = self.y + 1.0, self.y - h + 4.5'''),
    ('''            p.line(x1, bot, x1, top, 0.7, 0.45); p.line(x2, bot, x2, top, 0.7, 0.45)
        self.y -= _DROW
        p.line(_LL, self.y + 3, _LR, self.y + 3, 0.3, 0.8)''',
     '''            p.line(x1, bot, x1, top, 0.7, 0.45); p.line(x2, bot, x2, top, 0.7, 0.45)
        self.y -= h
        p.line(_LL, self.y + 3, _LR, self.y + 3, 0.3, 0.8)'''),
    ('''    doc.line_text("Stock count of %s - shelf counted that day, Marg stock export of that day - list given %s - %d items"
                  % (d.get("day") or "-", t.get("issued_text") or "-", len(d.get("rows") or [])), 9, gray=0.2)   # S294''',
     '''    doc.line_text("Stock count of %s - Qty in Marg is the Marg stock export of that day, Physical is the shelf counted that day - list given %s - %d items"
                  % (d.get("day") or "-", t.get("issued_text") or "-", len(d.get("rows") or [])), 9, gray=0.2)   # S299
    try:
        doc.phys_label = "Physical " + dt.datetime.strptime(d.get("day") or "", "%d-%m-%Y").strftime("%d-%b")
    except ValueError:
        doc.phys_label = "Physical"'''),
]

DESK_EDITS = [
    ('<a href="\'+esc(D.links.loss_page)+\'"><b>Darpan\\\'s list</b> — cut and print it on the loss page</a>',
     '<a href="\'+esc(D.links.hub_page||"/finance/stock/page/hub")+\'"><b>Stock check</b> — every step, in order (the tile)</a>'),
]

PORTAL_EDITS = [
    ('     "desc": "\\u0938\\u094d\\u091f\\u0949\\u0915 \\u0917\\u093f\\u0928\\u0924\\u0940 \\u2014 count & differences",\n'
     '     "live": True,\n'
     '     "url": "/finance/stock/page/count",\n',
     '     # S299: the tile opens the whole flow of the count (the owner, 17-Sep-2026: "that is the\n'
     '     # proper place for it, not these fragmented and hidden URLs"); anyone who is not the\n'
     '     # checker is sent on to the counting screen, where the tile went before.\n'
     '     "desc": "\\u0938\\u094d\\u091f\\u0949\\u0915 \\u0917\\u093f\\u0928\\u0924\\u0940 \\u2014 every step, in order",\n'
     '     "live": True,\n'
     '     "url": "/finance/stock/page/hub",\n'),
]

LINKS_EDIT = ('                           loss_page="/finance/stock/page/loss?count=%d" % _root))',
              '                           loss_page="/finance/stock/page/loss?count=%d" % _root,\n'
              '                           hub_page="/finance/stock/page/hub?count=%d" % _root))')
APP_EDITS.append(LINKS_EDIT)


# ===========================================================================================
# S299 -- the owner's review of the held S297 (17-Sep-2026 evening), both fixes:
#  (a) he types Darpan's answers too, not only Amir: the hub's step 4 says so and gives him the
#      button; Amir's board opens at the typing card (#answers) and says "Amir or the doctor".
#  (b) every confirmed swap becomes Marg vouchers straight away -- STOCK ISSUE on the short item,
#      STOCK RECEIVE on the extra item, the swapped quantity, reason "swap confirmed" -- on Amir's
#      board, the Marg cleanup Excel and the hub's step 6. A part swap gives its lines at once (the
#      remainder waits for his word, from Marg-after-swap to the shelf); a whole swap gives its
#      full quantity, never CHANGE 0. "A swap only reduces the loss burden and sanitises the
#      physical stock; Marg must still be corrected to the shelf."
# ===========================================================================================
SWAP_BLOCK = '''

def _swap_moved(x):
    """S299: units confirmed swaps moved on this line -- never more than the count-day gap."""
    d0 = int(x.get("diff_count_day", x["diff"]) or 0)
    return min(abs(d0), int(x.get("swapped") or 0))


def _marg_after_swap(x):
    """S299: Marg's figure once this line's swap vouchers are keyed -- down on a short line,
    up on an extra one. What is left of the line is corrected from here to the shelf."""
    d0 = int(x.get("diff_count_day", x["diff"]) or 0)
    n = _swap_moved(x)
    return int(x["marg"]) - n if d0 < 0 else int(x["marg"]) + n


def _swap_vouchers(d):
    """S299 -- the owner, 17-Sep-2026: every confirmed swap becomes Marg vouchers straight away.
    STOCK ISSUE on the item that is short (it left the shelf, Marg still holds it), STOCK RECEIVE
    on the item that is extra (it was billed, the shelf still holds it), for the swapped quantity,
    reason 'swap confirmed'. Nothing waits for the rest of the line."""
    by = {x["item"]: x for x in d.get("differences") or []}
    used, out = {}, []
    for p in d.get("matches") or []:
        if p.get("answer") != "YES":
            continue
        for item, kind, other in ((p["short"], "ISSUE", p["over"]), (p["over"], "RECEIVE", p["short"])):
            x = by.get(item)
            if not x:
                continue
            d0 = int(x.get("diff_count_day", x["diff"]) or 0)
            if (d0 < 0) != (kind == "ISSUE"):
                continue
            done = used.get(item, 0)
            q = min(int(p["qty"] or 0), abs(d0) - done)
            if q <= 0:
                continue
            before = int(x["marg"]) - done if kind == "ISSUE" else int(x["marg"]) + done
            used[item] = done + q
            out.append(dict(voucher=kind, voucher_text=("STOCK ISSUE" if kind == "ISSUE" else "STOCK RECEIVE"),
                            item=item, packing=x.get("packing") or "", pack=int(x.get("pack") or 1), kind=p["kind"],
                            qty=q, marg=before, after=(before - q if kind == "ISSUE" else before + q),
                            change=(-q if kind == "ISSUE" else q), with_item=other, reason="swap confirmed",
                            note=(("left the shelf, billed as " if kind == "ISSUE" else "billed in place of ") + other),
                            by=p.get("answered_by") or "", at=p.get("answered_at") or ""))
    return out


def _word_vouchers(d):
    """S299: the lines the owner has decided that still move Marg once the swap lines are keyed
    (written off, pursued, explained, a Marg fix) -- from Marg-after-swap to the shelf. A line a
    swap has wholly settled is not here (its swap lines are), nor a line with nothing left to move."""
    out = []
    for x in d.get("differences") or []:
        w = x.get("word")
        if not w or w.get("swap") or w.get("action") not in ("WRITE_OFF", "EXPLAINED", "MARG_FIX", "RECOVER"):
            continue
        rem = int(x["diff"] or 0)
        if not rem:
            continue
        out.append(dict(x, marg_from=_marg_after_swap(x), change=rem, voucher=("ISSUE" if rem < 0 else "RECEIVE"),
                        voucher_text=("STOCK ISSUE" if rem < 0 else "STOCK RECEIVE")))
    return out


def _cleanup_rows(d):
    """S299: the rows of AMIR'S MARG CLEANUP LIST -- the confirmed swaps first, then every decided
    line. A line with a swap and a remainder has two rows; keyed in order they end at the shelf."""
    rows = []
    for v in _swap_vouchers(d):
        rows.append([v["item"], v["packing"], v["voucher_text"], v["marg"], v["after"], v["change"],
                     "swap confirmed -- " + v["note"],
                     "Stock count #%d of %s: swap confirmed -- %s" % (d["count_id"], d["day"], v["note"]),
                     (_r_stamp(v["at"]) + " IST") if v["at"] else ""])
    for x in _word_vouchers(d):
        w = x["word"]
        rows.append([x["item"], x["packing"], x["voucher_text"], x["marg_from"], x["counted"], x["change"],
                     "%s%s" % (w["label"], (" -- " + w["note"]) if w.get("note") else ""),
                     "Stock count #%d of %s: %s" % (d["count_id"], d["day"], x.get("why") or ""),
                     w.get("at_text") or ""])
    return rows
'''
assert MATCH_BLOCK.endswith("    return props\n")
MATCH_BLOCK = MATCH_BLOCK + SWAP_BLOCK
APP_EDITS[1] = ('def _pad_report_data(con, root_id):\n', MATCH_BLOCK + '\n\ndef _pad_report_data(con, root_id):\n')

_HUB_OLD = '''    v_issue = [x for x in diffs if (x.get("word") or {}).get("action") == "WRITE_OFF"]
    v_fix = [x for x in diffs if (x.get("word") or {}).get("action") in ("MARG_FIX", "EXPLAINED")]
    vouchers = dict(issue=len(v_issue), fix=len(v_fix), state=("wait" if tot["open"] else "now"))
'''
_HUB_NEW = '''    sv, wv = _swap_vouchers(d), _word_vouchers(d)             # S299: a confirmed swap is on the vouchers at once
    vouchers = dict(swap_issue=sum(1 for v in sv if v["voucher"] == "ISSUE"), swap_receive=sum(1 for v in sv if v["voucher"] == "RECEIVE"),
                    swap_units=sum(v["qty"] for v in sv if v["voucher"] == "ISSUE"),
                    issue=sum(1 for x in wv if x["word"]["action"] == "WRITE_OFF"),
                    fix=sum(1 for x in wv if x["word"]["action"] in ("MARG_FIX", "EXPLAINED")),
                    state=("now" if (sv or not tot["open"]) else "wait"))
'''
assert HUB_BLOCK.count(_HUB_OLD) == 1
HUB_BLOCK = HUB_BLOCK.replace(_HUB_OLD, _HUB_NEW)
APP_EDITS[8] = ('@bp.route("/page/loss")\n', HUB_BLOCK + '\n\n@bp.route("/page/loss")\n')

APP_EDITS += [
    ('''    # 2 -- the Marg vouchers to post, by kind
    vouchers = dict(issue=[], fix=[], consume=[])
    for x in d["differences"]:
        w = x.get("word")
        if not w:
            continue
        if w["action"] == "WRITE_OFF":''',
     '''    # 2 -- the Marg vouchers to post, by kind (S299: the confirmed swaps first, straight away;
    #      a decided line runs from Marg-after-swap to the shelf, a swap-settled line is not repeated)
    vouchers = dict(issue=[], fix=[], consume=[], swap=_swap_vouchers(d))
    for x in _word_vouchers(d):
        w = x["word"]
        if w["action"] == "WRITE_OFF":'''),
    ('''    rows = []
    for x in d["differences"]:
        w = x.get("word")
        if not w or w["action"] not in ("WRITE_OFF", "EXPLAINED", "MARG_FIX", "RECOVER"):
            continue
        rows.append([x["item"], x["packing"], x["marg"], x["counted"], x["diff"],
                     "%s%s" % (w["label"], (" -- " + w["note"]) if w.get("note") else ""),
                     "Stock count #%d of %s: %s" % (d["count_id"], d["day"], x["why"]),
                     w["at_text"]])
    return _xlsx_response(_xlsx_rows(
        "MARG CLEANUP LIST -- stock count #%d (%s) -- for Amir" % (d["count_id"], d["day"]),
        "Key ONE stock adjustment per line in Marg: from MARG FIGURE to NEW FIGURE, with the reason. Tick the last column when done. The next Marg export proves it.",
        ["ITEM", "PACKING", "MARG FIGURE (units)", "NEW FIGURE (units)", "CHANGE", "OWNER'S DECISION", "REASON FOR THE VOUCHER", "DECIDED AT", "DONE IN MARG (tick)"],
        rows, {0: 32, 1: 10, 2: 14, 3: 14, 4: 9, 5: 30, 6: 60, 7: 18, 8: 14}),''',
     '''    rows = _cleanup_rows(d)                                     # S299: confirmed swaps first, then the decided lines
    return _xlsx_response(_xlsx_rows(
        "MARG CLEANUP LIST -- stock count #%d (%s) -- for Amir" % (d["count_id"], d["day"]),
        "Key ONE voucher per line in Marg, in the order of the rows: STOCK ISSUE brings Marg DOWN, STOCK RECEIVE brings it UP, by CHANGE, from MARG FIGURE to NEW FIGURE, with the reason. A confirmed swap is two lines -- issue on the short item, receive on the extra item. Tick the last column when done. The next Marg export proves it.",
        ["ITEM", "PACKING", "VOUCHER", "MARG FIGURE (units)", "NEW FIGURE (units)", "CHANGE", "OWNER'S DECISION", "REASON FOR THE VOUCHER", "DECIDED AT", "DONE IN MARG (tick)"],
        rows, {0: 32, 1: 10, 2: 15, 3: 14, 4: 14, 5: 9, 6: 34, 7: 60, 8: 18, 9: 14}),'''),
    ('a family that nets to zero was sold as one brand and billed as another -- swap the figures in Marg. Tick the last column when done.',
     'a family that nets to zero was sold as one brand and billed as another. Key NOTHING in Marg from this sheet: a swap you confirm on Try to match is on the Marg cleanup list as its STOCK ISSUE and STOCK RECEIVE lines (S299).'),
]

AMIR_EDITS = [
    ('''  const V=d.vouchers||{issue:[],fix:[],consume:[]};
  const vrow=x=>'<div class="row"><div><div class="it">'+esc(x.item)+' <span class="sub">'+esc(x.packing)+'</span></div><div class="q">Marg '+esc(units(x.marg,x.pack))+' → shelf \'''',
     '''  const V=d.vouchers||{issue:[],fix:[],consume:[],swap:[]}; V.swap=V.swap||[];   // S299
  const srow=v=>'<div class="row"><div><div class="it">'+esc(v.item)+' <span class="sub">'+esc(v.packing)+'</span></div><div class="q"><b>'+esc(v.voucher_text)+'</b> · Marg '+esc(units(v.marg,v.pack))+' → '+esc(units(v.after,v.pack))+' · swap confirmed — '+esc(v.note)+'</div></div><div class="r">'+(v.voucher==="ISSUE"?"− ":"+ ")+esc(units(v.qty,v.pack))+'</div></div>';
  const vrow=x=>'<div class="row"><div><div class="it">'+esc(x.item)+' <span class="sub">'+esc(x.packing)+'</span></div><div class="q">Marg '+esc(units(x.marg_from!=null?x.marg_from:x.marg,x.pack))+' → shelf \''''),
    ('''    +'<div class="lead">Only lines the doctor has decided. Post ONE voucher per block, then tick the Excel.</div>'
''',
     '''    +'<div class="lead">Confirmed swaps first — key them as soon as the doctor says Yes: STOCK ISSUE on the short item, STOCK RECEIVE on the extra item. The other blocks only after the doctor has decided the line. Post ONE voucher per block, then tick the Excel.</div>'
    +'<h3 style="font-size:15px;margin:8px 0 2px">Swaps confirmed — stock issue and stock receive ('+V.swap.length+')</h3>'+(V.swap.length?V.swap.map(srow).join(""):'<div class="empty">none yet</div>')
'''),
    ('''  h+='<div class="card"><h2><span class="n">3</span>Type Darpan\\'s answers</h2>''',
     '''  h+='<div class="card" id="answers"><h2><span class="n">3</span>Type Darpan\\'s answers</h2>'''),
    ('its items appear here — type the reason number and the note against each, and record them.',
     'its items appear here — Amir or the doctor types the reason number and the note against each, and records them.'),
    ('''  document.getElementById("body").innerHTML=h;
}
function board(d){''',
     '''  document.getElementById("body").innerHTML=h;
  if(location.hash==="#answers"){ const e=document.getElementById("answers"); if(e) e.scrollIntoView(); }   // S299: the hub's "type the answers" button
}
function board(d){'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_one(path, edits, from_md5, marker, dry):
    raw = io.open(path, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if marker in text:
        print("ALREADY PATCHED: %s is %s" % (path, cur))
        return cur
    if from_md5 and cur != from_md5.lower():
        sys.exit("REFUSING: %s is %s, expected %s" % (path, cur, from_md5))
    for old, new in edits:
        if text.count(old) != 1:
            sys.exit("REFUSING: anchor not found exactly once in %s: %r" % (path, old[:80]))
        text = text.replace(old, new)
    new = text.encode("utf-8")
    if dry:
        print("would write %s : %s -> %s" % (path, cur, md5(new)))
        return md5(new)
    shutil.copy2(path, "%s.bak_S299_%s" % (path, cur[:8]))
    with io.open(path, "wb") as fh:
        fh.write(new)
    back = md5(io.open(path, "rb").read())
    print("patched %s : %s -> %s" % (path, cur, back))
    if back != md5(new):
        sys.exit(4)
    return back


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--desk", required=True)
    ap.add_argument("--portal", required=True)
    ap.add_argument("--amir", required=True)
    ap.add_argument("--app-from", default=None)
    ap.add_argument("--receipt-from", default=None)
    ap.add_argument("--desk-from", default=None)
    ap.add_argument("--portal-from", default=None)
    ap.add_argument("--amir-from", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    patch_one(a.app, APP_EDITS, a.app_from, "def _swap_vouchers(d):", a.dry_run)
    patch_one(a.receipt, RECEIPT_EDITS, a.receipt_from, "# S299: units a confirmed swap took off", a.dry_run)
    patch_one(a.desk, DESK_EDITS, a.desk_from, "every step, in order (the tile)", a.dry_run)
    patch_one(a.portal, PORTAL_EDITS, a.portal_from, '"url": "/finance/stock/page/hub",', a.dry_run)
    patch_one(a.amir, AMIR_EDITS, a.amir_from, "S299: the hub's", a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
