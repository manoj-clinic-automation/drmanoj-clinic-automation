#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s436.py -- builds the patched live files of kit S436_STAFF_PAGES_CLEAN from the LIVE bytes by anchored edits. Every anchor must
occur exactly once and every source must be at its FROM pin, or the build stops with nothing written. (stockmatch.py v1.1,
stockmatch.html, stock_amir.html, loss_piles.py v2.3 and stock_watch.py v1.3 are whole files shipped in the kit.)

  stock_app.py           the same-salt matcher leaves out an item whose salt is on the OPEN salt-fix list (3.3); Amir's board JSON gains
                         salt_fix (the four tasks with what Marg's list says today), rate_tasks (the orthotic items without a selling
                         rate), renames_ready (the orthotic round exists and every earlier round is entered), proof_hi (the closing-stock
                         proof in Hindi), ortho (the section's close-by-rule run). Nothing is removed from the JSON: the S221 lookups, the
                         tranches and the families stay readable for the owner (the page no longer shows them).
  stock_hub.html         the orthotic card shows the loss when the section closed by rule; its table lists the defaulted lines too.
  stock_statement.py     an orthotic line in the close-by-rule run reads "orthotic loss -- sold without bill" / "book correction --
                         billed, not handed over" (with its voucher round); such a line is not 'open'.

Usage: make_s436.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "02ad3d6ac3390dcf940d7a443557ac7c",
    "stock_hub.html": "38e0537cd7d1eb3fb40d1a5a0b7df0e5",
    "stock_statement.py": "05c63235a9f78c9f0f6969c683548880",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what, count=1):
    n = s.count(old)
    if n != count:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly %d): %r" % (what, n, count, old[:90]))
    return s.replace(old, new)


# ---------------------------------------------------------------- stock_app.py
SALTS_OLD = '''    salts = _salts(con)
    words = _lane_actions(con, _root)
'''
SALTS_NEW = '''    salts = _salts_less_fixes(con)                            # S436 (3.3): an item whose salt is on the open salt-fix list pairs with nothing
    words = _lane_actions(con, _root)
'''
BOARD_OLD = '''    return dict(watch=(_sw.amir_view(con) if STOCK_WATCH_OK else None),   # S428: the Sunday buttons, bill entry baaki, the traces' fix lines
'''
BOARD_NEW = '''    return dict(**_s436_board_extra(con, d), watch=(_sw.amir_view(con) if STOCK_WATCH_OK else None),   # S436 + S428: the salt fixes, the rates, the renames gate, the proof in Hindi; the Sunday buttons, bill entry baaki, the traces' fix lines
'''
BLOCK = r'''
# ---- S436_STAFF_PAGES_CLEAN begin (D638) -----------------------------------------
# The owner, 28-Sep-2026: "PARI CR 12.5, LINVIZ and LACTOVAX have wrong salts in Marg, so the pairs can't be matched"; "Amir does the
# vouchers, uploads the suitable report, gets confirmation, any remaining work and any corrections"; "renames should appear only when
# our flow is ready". The salt-fix list lives in purchase_salt_task (section 'change', source_md5 'S436-owner...', the owner's word);
# a task clears itself when Marg's own salt list (purchase_salt_marg, pushed with every salt export) shows the new salt.
SALT_FIX_SOURCE = "S436-owner"


def _salt_fix_rows(con):
    """The owner's salt fixes with what Marg's list says today: [{id, item, salt_now, salt_new, marg_now, marg_done, done, done_by}]."""
    out = []
    try:
        marg = {str(r[0] or "").strip().upper(): str(r[1] or "").strip() for r in con.execute("SELECT item_norm, salt FROM purchase_salt_marg")}
    except Exception:                                          # noqa: BLE001
        marg = {}
    try:
        rows = con.execute("SELECT id, a, b, c, COALESCE(done,0), done_by, done_at FROM purchase_salt_task WHERE section='change' AND source_md5 LIKE ? ORDER BY seq, id",
                           (SALT_FIX_SOURCE + "%",)).fetchall()
    except Exception:                                          # noqa: BLE001
        return out
    for r in rows:
        item, now_, new = str(r[1] or "").strip(), str(r[2] or "").strip(), str(r[3] or "").strip()
        m = marg.get(item.upper())
        if m is None:
            m = marg.get(_pad_norm(item))
        marg_done = bool(m) and m.strip().upper() == new.upper()
        out.append(dict(id=r[0], item=item, salt_now=now_, salt_new=new, marg_now=(m or ""), marg_done=marg_done,
                        done=bool(r[4]), done_by=r[5] or "", done_at=r[6] or "",
                        state=("done" if marg_done else ("ticked" if r[4] else "open")),
                        hi=("Marg में हो गया" if marg_done else ("टिक किया, Marg की लिस्ट में अभी नहीं" if r[4] else "करना है"))))
    return out


def _salts_less_fixes(con):
    """S436 (3.3): the count's salt map without the items whose salt is on the open salt-fix list -- a wrong salt pairs nothing."""
    S = _salts(con)
    try:
        fix = {_pad_norm(x["item"]) for x in _salt_fix_rows(con) if not x["marg_done"]}
    except Exception:                                          # noqa: BLE001
        fix = set()
    if not fix:
        return S
    return {k: v for k, v in S.items() if k not in fix}


def _s436_board_extra(con, d):
    """Amir's board (S436): the four sections' data beside the S301 rounds."""
    root = d["count_id"]
    out = dict(salt_fix=_salt_fix_rows(con), rate_tasks=[], renames_ready=False, renames_wait_hi="", proof_hi="", proof_state="", ortho=None, rounds_order=[])
    # (b) Rate daalo -- the orthotic SHORT lines without a selling rate (the statement's price rule, S431): the loss cannot be priced
    #     without it. Once the section closed by rule, exactly the run's unpriced loss lines.
    try:
        import stockmatch as _smx                              # noqa: PLC0415
        _orun, _oby = _smx.ortho_run(con, root)
    except Exception:                                          # noqa: BLE001
        _orun, _oby = None, {}
    try:
        if _orun:
            for x in _orun["groups"].get("ortho_loss", []):
                if x.get("mrp_p") is None:
                    out["rate_tasks"].append(dict(item=x["item"], packing=x.get("packing") or "", hi="Marg में selling rate डालें"))
        elif STOCK_STATEMENT_OK:
            st = _stock_settings(con)
            P = _ss.Prices(_dmy_to_iso(d.get("as_on") or "") or "")
            rates = {r[0]: int(r[1]) for r in con.execute("SELECT item, rate_p FROM stock_rate") if r[1]}
            for x in d["differences"]:
                if int(x["diff"] or 0) >= 0 or _item_section(con, x) != "Orthotics":
                    continue
                price, _src = _ss.price_for(con, x["item"], int(x.get("pack") or 1), "Orthotics", st, P, rates)
                if not price:
                    out["rate_tasks"].append(dict(item=x["item"], packing=x.get("packing") or "", hi="Marg में selling rate डालें"))
        out["rate_tasks"].sort(key=lambda r: r["item"])
    except Exception:                                          # noqa: BLE001
        pass
    # (c) Naam badlo -- only when the orthotic round exists and every earlier round is entered
    try:
        vm = _voucher_state(con, d)
        ortho_rounds = [r for r in vm["rounds"] if r["batches"] and all((b.get("sections") or []) == ["Orthotics"] for b in r["batches"])]
        earlier = [r for r in vm["rounds"] if r not in ortho_rounds]
        out["renames_ready"] = bool(ortho_rounds) and all(r["closed"] for r in earlier)
        out["renames_wait_hi"] = "" if out["renames_ready"] else ("नाम बदलना — बाद में, जब वाउचर हो जाएँ" + ("" if ortho_rounds else " (orthotic round अभी बना नहीं)"))
        order = sorted(earlier, key=lambda r: -r["round_no"]) + sorted(ortho_rounds, key=lambda r: r["round_no"])
        out["rounds_order"] = [r["round_no"] for r in order]
    except Exception:                                          # noqa: BLE001
        pass
    # (2) the closing-stock proof, in Hindi
    try:
        P2 = _proof_state(con, d)
        out["proof_state"] = P2.get("state") or ""
        if P2.get("as_after"):
            bad = [r["item"] for r in (P2.get("rows") or []) if not r.get("ok")]
            out["proof_hi"] = "Marg = shelf: %d of %d · %d to correct%s" % (P2.get("agree", 0), P2.get("items", 0), len(bad), (": " + ", ".join(bad[:6])) if bad else "")
        elif P2.get("state") == "wait":
            out["proof_hi"] = "अभी बाकी — पहले वाउचर Marg में डालें"
        else:
            out["proof_hi"] = "अभी बाकी — वाउचर डल गए, Marg का अगला closing stock export आने दें"
    except Exception:                                          # noqa: BLE001
        out["proof_hi"] = "अभी बाकी"
    # the orthotic section's close-by-rule run (stockmatch)
    try:
        import stockmatch                                      # noqa: PLC0415
        run, _by = stockmatch.ortho_run(con, root)
        if run:
            out["ortho"] = dict(run_id=run["id"], round_no=run["round_no"], n_short=run["n_short"], n_fix=run["n_fix"], mrp_p=run["mrp_p"],
                                rs=_loss_rs(run["mrp_p"]), unpriced=run["unpriced"], at_text=run["at_text"])
    except Exception:                                          # noqa: BLE001
        pass
    return out
# ---- S436_STAFF_PAGES_CLEAN end -------------------------------------------------
'''


def build_stock_app(s):
    s = rep(s, SALTS_OLD, SALTS_NEW, "the salt map without the fixes")
    s = rep(s, BOARD_OLD, BOARD_NEW, "Amir's board extra")
    s = rep(s, "# ---- S432_DESK_GROUP_FLOW end --------------------------------------------------\n",
            "# ---- S432_DESK_GROUP_FLOW end --------------------------------------------------\n" + BLOCK.lstrip("\n"), "the S436 block")
    return s


# ---------------------------------------------------------------- stock_hub.html
HUB_FIGS_OLD = '''    +'<span>Renames seen in Marg <b>'+(R.verified||0)+' of '+(R.total||0)+'</b>'+(R.amber?' \\u00b7 <span class="err">'+R.amber+' ticked, not yet seen</span>':'')+'</span></div>'
'''
HUB_FIGS_NEW = '''    +'<span>Renames seen in Marg <b>'+(R.verified||0)+' of '+(R.total||0)+'</b>'+(R.amber?' \\u00b7 <span class="err">'+R.amber+' ticked, not yet seen</span>':'')+'</span>'
    +(O.loss?'<span>Orthotic loss <b>'+esc(O.loss.rs)+'</b> \\u00b7 '+O.loss.n_short+' line'+(O.loss.n_short===1?'':'s')+' short, sold without bill'+(O.loss.unpriced?' \\u00b7 '+O.loss.unpriced+' without a price':'')+(O.loss.round_no?' \\u00b7 round '+O.loss.round_no+' on Amir\\'s board':'')+'</span>':'')+'</div>'   /* S436 (D638) */
'''
HUB_LINES_OLD = '''  const L=(O.lines||[]).filter(l=>l.open);
'''
HUB_LINES_NEW = '''  const L=(O.lines||[]).filter(l=>l.open||l.defaulted);   /* S436: a line the rule answered by default is shown for the one-tap word */
'''


def build_hub(s):
    s = rep(s, HUB_FIGS_OLD, HUB_FIGS_NEW, "the orthotic card's loss figure")
    s = rep(s, HUB_LINES_OLD, HUB_LINES_NEW, "the orthotic card's lines")
    return s


# ---------------------------------------------------------------- stock_statement.py
ST_RUN_OLD = '''    for r in con.execute("SELECT item, round_no FROM stock_voucher_line WHERE count_id=? ORDER BY round_no", (root,)):
        rounds_by_item.setdefault(r[0], []).append(int(r[1]))
'''
ST_RUN_NEW = '''    for r in con.execute("SELECT item, round_no FROM stock_voucher_line WHERE count_id=? ORDER BY round_no", (root,)):
        rounds_by_item.setdefault(r[0], []).append(int(r[1]))
    orun_by = {}                                              # S436 (D638): the orthotic section's close-by-rule run -- the loss and the corrections
    try:
        import stockmatch                                     # noqa: PLC0415
        _orun, orun_by = stockmatch.ortho_run(con, root)
    except Exception:                                         # noqa: BLE001
        orun_by = {}
'''
ST_BECAME_OLD = '''        if s == "Orthotics":
            ol = ortho_lines.get(item)
            if ol:
'''
ST_BECAME_NEW = '''        if s == "Orthotics":
            ol = ortho_lines.get(item)
            orl = orun_by.get(item)                           # S436
            if orl:
                L["became"] = ("orthotic loss -- sold without bill" if orl["group"] == "ortho_loss" else "book correction -- billed, not handed over") \\
                    + ((" (Darpan by default)") if "by default" in (orl.get("why") or "") else "")
                L["became_key"] = orl["group"]
            elif ol:
'''
ST_OPEN_OLD = '''            L["open"] = item in ortho_open
'''
ST_OPEN_NEW = '''            L["open"] = (item in ortho_open) and not orl        # S436: a line the rule closed is not open
'''
ST_VER_OLD = '''VERSION = "1.1"
KIT = "S432_DESK_GROUP_FLOW"                                   # v1.0 was S431_COUNT_STATEMENT
'''
ST_VER_NEW = '''VERSION = "1.2"
KIT = "S436_STAFF_PAGES_CLEAN"                                 # v1.0 was S431_COUNT_STATEMENT, v1.1 S432_DESK_GROUP_FLOW
# v1.2 (S436, D638, 28-Sep-2026): an orthotic line in the section's close-by-rule run reads "orthotic loss -- sold without bill" or
# "book correction -- billed, not handed over" (its voucher round beside it) and is no longer 'open'.
'''


def build_statement(s):
    s = rep(s, ST_VER_OLD, ST_VER_NEW, "the statement's version")
    s = rep(s, ST_RUN_OLD, ST_RUN_NEW, "the ortho run read")
    s = rep(s, ST_BECAME_OLD, ST_BECAME_NEW, "the ortho became")
    s = rep(s, ST_OPEN_OLD, ST_OPEN_NEW, "the ortho open flag")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {name: load(os.path.join(a.finance, name), name) for name in FROM}
    out = {"stock_app.py": build_stock_app(src["stock_app.py"]), "stock_hub.html": build_hub(src["stock_hub.html"]),
           "stock_statement.py": build_statement(src["stock_statement.py"])}
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
