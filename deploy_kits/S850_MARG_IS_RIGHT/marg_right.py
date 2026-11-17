#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_right.py -- S850_MARG_IS_RIGHT (17-Nov-2026, Sanjeevni session 476; D993 b-d, D995; F-1440 in scan_ask.py).

THE OWNER, 16-Nov-2026 12:00-12:34 IST (D993): Marg accepted over a scanned line automatically when the totals agree, one tap 'Marg is right'
otherwise; every accepted line kept as a correction, a monthly list to the Scan App's reader. 17-Nov 11:38 IST: "ok" on mock-up v2
(https://claude.ai/artifact/FY6ubLCgQTww6g3Aqsjjzh, tabs 3 and 4).

WHAT (no new screen):
  * "Scan reading against Marg" (/finance/purchase/page/sarvam?month=) gets two cards under its table:
      - Lines that differ: each linked bill with a scan line differing from Marg's (name, qty, rate, batch, expiry -- as purchase_sarvam_check
        holds them). Totals agree (the bill's scan total within Rs 1 of Marg's, the stored total_ok) -> "Marg accepted - totals agree", by
        itself. Totals differ -> one tap "Marg is right" (the doctor; the page is his), or it is left for Amir's "Where Marg differs" as today.
      - Corrections kept: every accepted line, by kind, by totals / by a tap -- the month's list for the Scan App chat's reader.
  * The Item ledger: each purchase row carries its scan line's verdict (item_ledger.py calls annotate_ledger).
purchase_sarvam_check stays strict (D891): never written here. Writes: its own tables s850_tap and s850_correction, purchase_audit.
assets.db READ ONLY (the scan's own read values). OFF: /root/finance/_off/ALL_OFF or /root/finance/_off/S850_OFF -- the cards and the ledger
tags are not drawn, nothing written.
"""
import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys

KIT = "S850_MARG_IS_RIGHT"
VERSION = "S850-MARG-RIGHT-1.1"
HERE = os.path.dirname(os.path.abspath(__file__))
OFF_FLAGS = (os.path.join(HERE, "_off", "ALL_OFF"), os.path.join(HERE, "_off", "S850_OFF"))
KINDS = ("name", "qty", "rate", "batch", "expiry")
DDL_TAP = ("CREATE TABLE IF NOT EXISTS s850_tap (asset_bill_id INTEGER NOT NULL, line_key TEXT NOT NULL, bill_id INTEGER NOT NULL, "
           "by_user TEXT, at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, line_key))")
DDL_COR = ("CREATE TABLE IF NOT EXISTS s850_correction (asset_bill_id INTEGER NOT NULL, line_key TEXT NOT NULL, kind TEXT NOT NULL, "
           "bill_id INTEGER NOT NULL, month TEXT, scan_item TEXT, marg_item TEXT, read_value TEXT, marg_value TEXT, how TEXT NOT NULL, "
           "by_user TEXT, at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, line_key, kind))")
TAG = ('<span style="display:inline-block;font-size:12px;border-radius:6px;padding:1px 7px;margin-left:6px;background:%s;color:%s">%s</span>')
GREEN, GREY, AMBER = ("#dcfae6", "#085d3a"), ("#f2f4f7", "#475467"), ("#fef0c7", "#93370d")


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def now_iso():
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def is_off():
    return next((f for f in OFF_FLAGS if os.path.exists(f)), None)


def PA():
    import purchase_app                                     # noqa: PLC0415 -- beside this file
    return purchase_app


def ensure(con):
    con.execute(DDL_TAP)
    con.execute(DDL_COR)


def _q(con, sql, params=()):
    """[dict] -- through a cursor of its own with Row rows: the caller's connection's row factory is never assumed or changed (review 6)."""
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.execute(sql, params)]


def _table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _g(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v or "").strip()
    return ("%.2f" % f).rstrip("0").rstrip(".") if f != int(f) else "%d" % int(f)


def _rs(p):
    try:
        return PA()._r(p)
    except Exception:                                         # noqa: BLE001
        return "₹%s" % _g((p or 0) / 100.0)


def _dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def _dmhm(iso):
    try:
        return dt.datetime.fromisoformat(str(iso)[:19]).strftime("%d-%b %H:%M")
    except (TypeError, ValueError):
        return str(iso or "")


def _audit(con, who, action, ref, detail):
    try:
        d = dict(detail or {})
        d.setdefault("kit", KIT)
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (now_iso(), who or "", action, str(ref or ""), json.dumps(d, sort_keys=True, default=str)))
    except sqlite3.Error as e:
        print("marg_right audit failed: %s" % e, file=sys.stderr)


# ====================================================================== the lines and their verdicts
def _keys(items):
    """A line's key: its scan name, normalised, and which time that name comes on the paper (#1, #2 ...) -- stable while the scan stands."""
    seen, out = {}, []
    for it in items:
        n = _norm(it.get("scan_item"))[:60] or "?"
        seen[n] = seen.get(n, 0) + 1
        out.append("%s#%d" % (n, seen[n]))
    return out


def _taps(con):
    if not _table(con, "s850_tap"):
        return {}
    return {(int(r[0]), str(r[1])): dict(by=r[2], at=r[3], bill_id=int(r[4])) for r in con.execute("SELECT asset_bill_id, line_key, by_user, at, bill_id FROM s850_tap")}


def _check_rows(con, where, params):
    if not _table(con, "purchase_sarvam_check"):
        return []
    return _q(con, "SELECT asset_bill_id, bill_id, month, total_ok, items_read, detail FROM purchase_sarvam_check WHERE %s ORDER BY asset_bill_id" % where,
              params)


def _bill(r, d, taps):
    """One check row -> dict(asset_bill_id, bill_id, month, scan, marg, total_ok, lines=[dict(key, scan_item, marg_item, bad, state, tap)]).
    state: agrees | auto (totals agree: Marg accepted by itself) | tapped (the doctor's 'Marg is right') | ask (totals differ, no tap)."""
    items = list(d.get("items") or [])
    sid, tot = int(r["asset_bill_id"]), bool(r["total_ok"])
    lines = []
    for it, k in zip(items, _keys(items)):
        bad = [x for x in (it.get("bad") or []) if x in KINDS]
        tap = taps.get((sid, k))
        if tap and tap.get("bill_id") != int(r["bill_id"]):     # review 1: a tap judged one Marg bill; the scan relinked -> not this bill's
            tap = None
        st = "agrees" if not bad else "auto" if tot else "tapped" if tap else "ask"
        lines.append(dict(key=k, scan_item=it.get("scan_item") or "", marg_item=it.get("marg_item") or "", bad=bad, state=st, tap=tap))
    return dict(asset_bill_id=sid, bill_id=int(r["bill_id"]), month=r.get("month") or "", scan=d.get("scan") or {}, marg=d.get("marg") or {},
                total_ok=tot, lines=lines)


def bills(con, month):
    """The month's linked bills with their line verdicts (every check row, read only)."""
    taps = _taps(con)
    out = []
    for r in _check_rows(con, "month=?", (month,)):
        try:
            d = json.loads(r["detail"] or "{}")
        except ValueError:
            d = {}
        out.append(_bill(r, d, taps))
    return out


def _one(con, sid):
    taps = _taps(con)
    for r in _check_rows(con, "asset_bill_id=?", (int(sid),)):
        try:
            return _bill(r, json.loads(r["detail"] or "{}"), taps)
        except ValueError:
            return None
    return None


# ====================================================================== the read values (assets.db read only; Marg's newest export)
def _scan_items(acon, sid):
    try:
        return _q(acon, "SELECT item_name, quantity, rate, batch, expiry FROM bill_items WHERE bill_id=? ORDER BY id", (int(sid),))
    except sqlite3.Error:
        return []


def _marg_rows(con, bill_id):
    """Marg's own lines of the bill, from the newest export -- the same read as purchase_app._s446_compare_one."""
    b = con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE id=?", (int(bill_id),)).fetchone()
    if not b:
        return []
    ml = _q(con, "SELECT item, qty, free, rate_p, batch, expiry, source_md5 FROM purchase_line WHERE supplier_norm=? AND bill_no=? "
                 "AND bill_date=? ORDER BY id", (b[0], b[1], b[2]))
    if ml:
        newest = ml[-1]["source_md5"]
        ml = [x for x in ml if x["source_md5"] == newest]
    return ml


def values(con, acon, B):
    """{line key: (scan item row | None, Marg line | None)} -- paired in the order the check read them (the scan's lines by id, Marg's by
    name). acon None -> the scan side None."""
    sitems = _scan_items(acon, B["asset_bill_id"]) if acon is not None else []
    mrows = _marg_rows(con, B["bill_id"])
    s_used, out = set(), {}
    for ln in B["lines"]:
        si = next((i for i, x in enumerate(sitems) if i not in s_used and str(x.get("item_name") or "") == ln["scan_item"]), None)
        if si is None:
            si = next((i for i, x in enumerate(sitems) if i not in s_used and _norm(x.get("item_name")) == _norm(ln["scan_item"])), None)
        mi = next((i for i, x in enumerate(mrows) if ln["marg_item"] and str(x.get("item") or "") == ln["marg_item"]), None)   # review 2: as the
        if si is not None:                                                                         # check paired it (one Marg line may serve two)
            s_used.add(si)
        out[ln["key"]] = (sitems[si] if si is not None else None, mrows[mi] if mi is not None else None)
    return out


def kind_values(kind, s, m):
    """(what the scan read, what Marg holds) for one kind, as text."""
    s, m = s or {}, m or {}
    if kind == "name":
        return str(s.get("item_name") or ""), str(m.get("item") or "")
    if kind == "qty":
        q, f = m.get("qty"), m.get("free")
        mv = "" if q is None else (_g(q) + (" + %s free" % _g(f) if f not in (None, "", 0, 0.0) else ""))
        return _g(s.get("quantity")) if s.get("quantity") not in (None, "") else "", mv
    if kind == "rate":
        return (_g(s.get("rate")) if s.get("rate") not in (None, "") else ""), ("%.2f" % (m["rate_p"] / 100.0) if m.get("rate_p") is not None else "")
    return str(s.get(kind) or "").strip(), str(m.get(kind) or "").strip()


# ====================================================================== the corrections kept
def sync(con, month, B_list=None, acon=None):
    """The month's accepted lines into s850_correction: 'totals' rows for the auto ones, 'tap' rows for the doctor's. A row whose line is no
    longer accepted (its link moved, the check judged again) leaves. Needs the scan's read values: nothing written when acon is None.
    Returns (added, removed)."""
    if is_off() or acon is None:
        return 0, 0
    ensure(con)
    B_list = bills(con, month) if B_list is None else B_list
    have = {(int(r[0]), str(r[1]), str(r[2])): (str(r[3]), r[4] or "", r[5] or "") for r in con.execute(
        "SELECT asset_bill_id, line_key, kind, how, read_value, marg_value FROM s850_correction WHERE month=?", (month,))}
    want = {}
    for B in B_list:
        acc = [ln for ln in B["lines"] if ln["state"] in ("auto", "tapped")]
        if not acc:
            continue
        V = values(con, acon, B)
        for ln in acc:
            s, m = V.get(ln["key"], (None, None))
            how = "totals" if ln["state"] == "auto" else "tap"
            for k in ln["bad"]:
                rv, mv = kind_values(k, s, m)
                if rv and rv == mv:                           # review 2: the reading and Marg's agree on this kind -- no misread to keep,
                    old = have.get((B["asset_bill_id"], ln["key"], k))      # unless one was kept already (the scan read again since)
                    if not (old and old[1] and old[0] == ("totals" if ln["state"] == "auto" else "tap")):
                        continue
                    rv, mv = old[1], old[2]
                want[(B["asset_bill_id"], ln["key"], k)] = (B["bill_id"], B["month"] or month, ln["scan_item"], ln["marg_item"], rv, mv, how,
                                                            (ln["tap"] or {}).get("by") if how == "tap" else "", (ln["tap"] or {}).get("at") if how == "tap" else now_iso())
    bill_of = {B["asset_bill_id"]: B["bill_id"] for B in B_list}
    tapped = {k for k, v in _taps(con).items() if v.get("bill_id") == bill_of.get(k[0])}   # review 5: a tap committed meanwhile keeps its rows
    added = removed = 0
    for key, h in have.items():
        if h[0] == "tap" and (key[0], key[1]) in tapped and key not in want:
            continue
        if key not in want or want[key][6] != h[0]:
            con.execute("DELETE FROM s850_correction WHERE asset_bill_id=? AND line_key=? AND kind=?", key)
            removed += 1
    for key, v in want.items():
        if key in have and have[key][0] == v[6]:                 # review 3: a kept value is never overwritten -- only an empty one filled
            h = have[key]
            if (h[1] or not v[4]) and (h[2] or not v[5]):
                continue
            con.execute("UPDATE s850_correction SET read_value=?, marg_value=? WHERE asset_bill_id=? AND line_key=? AND kind=?",
                        (h[1] or v[4], h[2] or v[5]) + key)
            added += 1
            continue
        con.execute("INSERT OR REPLACE INTO s850_correction (asset_bill_id, line_key, kind, bill_id, month, scan_item, marg_item, read_value, marg_value, "
                    "how, by_user, at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", key + v)
        added += 1
    if added or removed:
        con.commit()
    return added, removed


def month_table(con, month, B_list=None):
    """dict(kinds=[(kind, n, by totals, by tap)], bills, differing, agreeing, for_tap, tapped)."""
    B_list = bills(con, month) if B_list is None else B_list
    dif = [B for B in B_list if any(ln["bad"] for ln in B["lines"])]
    out = dict(kinds=[], bills=len(B_list), differing=len(dif), agreeing=sum(1 for B in dif if B["total_ok"]),
               for_tap=sum(1 for B in dif if any(ln["state"] == "ask" for ln in B["lines"])),
               tapped=sum(1 for B in dif if any(ln["state"] == "tapped" for ln in B["lines"])))
    if _table(con, "s850_correction"):
        got = {}
        for k, how, n in con.execute("SELECT kind, how, COUNT(*) FROM s850_correction WHERE month=? GROUP BY kind, how", (month,)):
            got.setdefault(k, {})[how] = n
        out["kinds"] = [(k, sum(got[k].values()), got[k].get("totals", 0), got[k].get("tap", 0)) for k in KINDS if k in got]
    return out


def corrections(con, month):
    """Every kept correction of the month, for the Scan App chat's monthly list (read only)."""
    if not _table(con, "s850_correction"):
        return []
    return _q(con, "SELECT * FROM s850_correction WHERE month=? ORDER BY kind, asset_bill_id, line_key", (month,))


# ====================================================================== the doctor's tap
def tap(con, who, sid, key, do="right"):
    """(ok, message, http). do = right | undo, on one line of a linked bill whose totals differ."""
    if is_off():
        return False, "This is switched off.", 409
    ensure(con)
    B = _one(con, sid)
    ln = B and next((x for x in B["lines"] if x["key"] == str(key or "")), None)
    if not B or not ln:
        return False, "That line is no longer on the page — reload it.", 409
    if do == "undo":
        if ln["state"] != "tapped":
            return False, "Nothing to undo on that line.", 409
        con.execute("DELETE FROM s850_tap WHERE asset_bill_id=? AND line_key=?", (B["asset_bill_id"], ln["key"]))
        con.execute("DELETE FROM s850_correction WHERE asset_bill_id=? AND line_key=? AND how='tap'", (B["asset_bill_id"], ln["key"]))
        _audit(con, who, "s850_undo", B["asset_bill_id"], dict(line=ln["key"], bill_id=B["bill_id"]))
        con.commit()
        return True, "Undone.", 200
    if do != "right":
        return False, "Unknown action.", 400
    if ln["state"] == "tapped":
        return False, "This line already has your answer — Undo first.", 409
    if ln["state"] != "ask":
        return False, "This line needs no tap (%s)." % ("its bill's totals agree" if ln["state"] == "auto" else "it agrees"), 409
    ts = now_iso()
    gone = con.execute("DELETE FROM s850_tap WHERE asset_bill_id=? AND line_key=? AND bill_id<>?", (B["asset_bill_id"], ln["key"], B["bill_id"])).rowcount
    if gone:                                                  # review 1: a tap judged another Marg bill (the scan relinked since)
        con.execute("DELETE FROM s850_correction WHERE asset_bill_id=? AND line_key=? AND how='tap'", (B["asset_bill_id"], ln["key"]))
    try:
        con.execute("INSERT INTO s850_tap (asset_bill_id, line_key, bill_id, by_user, at) VALUES (?,?,?,?,?)", (B["asset_bill_id"], ln["key"], B["bill_id"], who, ts))
    except sqlite3.IntegrityError:
        con.rollback()
        return False, "This line was answered on another screen a moment ago.", 409
    acon = None
    try:
        acon = PA()._assets_con()
    except Exception:                                         # noqa: BLE001
        acon = None
    try:
        s, m = values(con, acon, B).get(ln["key"], (None, None)) if acon is not None else (None, None)
    finally:
        if acon is not None:
            acon.close()
    for k in ln["bad"]:
        rv, mv = kind_values(k, s, m) if acon is not None else ("", "")
        if rv and rv == mv:
            continue
        con.execute("INSERT OR REPLACE INTO s850_correction (asset_bill_id, line_key, kind, bill_id, month, scan_item, marg_item, read_value, marg_value, "
                    "how, by_user, at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (B["asset_bill_id"], ln["key"], k, B["bill_id"], B["month"], ln["scan_item"], ln["marg_item"], rv, mv, "tap", who, ts))
    _audit(con, who, "s850_marg_is_right", B["asset_bill_id"], dict(line=ln["key"], bill_id=B["bill_id"], kinds=ln["bad"]))
    con.commit()
    return True, "Marg is right — kept as a correction for the scan reader.", 200


# ====================================================================== the cards on "Scan reading against Marg"
JS = """
async function s850(b){ b.disabled = true; const j = await post(P + '/api/s850/line', {a: +b.dataset.a, k: b.dataset.k, do: b.dataset.do}); if (j) location.reload(); else b.disabled = false; }
"""
CSS = ("<style>.s850 table{margin:4px 0 12px}.s850 .h{font-weight:600;margin-top:10px}.s850 .sub{color:#667085;font-size:13px}"
       ".s850 button{font-size:13px;padding:3px 10px}</style>")


def _verdict_cell(B, ln):
    if ln["state"] == "agrees":
        return TAG % (GREY[0], GREY[1], "agrees")
    if ln["state"] == "auto":
        return TAG % (GREEN[0], GREEN[1], "Marg accepted — totals agree")
    if ln["state"] == "tapped":
        t = ln["tap"] or {}
        return (TAG % (GREEN[0], GREEN[1], esc("Marg is right · %s, %s" % (t.get("by") or "you", _dmhm(t.get("at"))))) +
                ' <button type="button" data-a="%d" data-k="%s" data-do="undo" onclick="s850(this)">Undo</button>' % (B["asset_bill_id"], esc(ln["key"])))
    return ('<button type="button" data-a="%d" data-k="%s" data-do="right" onclick="s850(this)">Marg is right</button> '
            '<span class="sub">or leave it for Amir\'s “Where Marg differs”</span>' % (B["asset_bill_id"], esc(ln["key"])))


def _side(name, kinds, vals, idx):
    bits = ["%s %s" % (k, esc(vals[k][idx])) for k in kinds if k != "name" and vals.get(k) and vals[k][idx]]
    return esc(name or "—") + ((" · " + " · ".join(bits)) if bits else "")


def _bill_html(con, acon, B, scan_url):
    sc, mg = B["scan"], B["marg"]
    head = "%s · bill %s · %s · %s" % (re.sub(r"\s+", " ", str(mg.get("supplier") or sc.get("vendor") or "")).strip().upper(), mg.get("bill_no") or sc.get("bill_no") or "?",
                                       _dmy(mg.get("date")), _rs(mg.get("total_p")))
    if B["total_ok"]:
        tg = TAG % (GREEN[0], GREEN[1], "totals agree")
    else:
        dif = None
        try:
            dif = abs(int(sc.get("total_p")) - int(mg.get("total_p") or 0)) if sc.get("total_p") is not None else None
        except (TypeError, ValueError):
            dif = None
        tg = TAG % ("#fee4e2", "#912018", esc("totals differ by %s" % _rs(dif)) if dif is not None else "the scan's total not read")
    V = values(con, acon, B) if acon is not None else {}
    rows = []
    for ln in B["lines"]:
        s, m = V.get(ln["key"], (None, None))
        vals = {k: kind_values(k, s, m) for k in ln["bad"]} if (s or m) else {}
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            _side(ln["scan_item"], ln["bad"], vals, 0), _side(ln["marg_item"], ln["bad"], vals, 1), esc(", ".join(ln["bad"]) or "—"), _verdict_cell(B, ln)))
    return ('<div class="h">%s %s <a class="sub" href="%s" target="_blank" rel="noopener">the scan</a></div><div class="scroll"><table>'
            '<tr><th>Line on the scan</th><th>Marg\'s line</th><th>Differs in</th><th>Verdict</th></tr>%s</table></div>'
            % (esc(head), tg, esc(scan_url % B["asset_bill_id"]), "".join(rows)))


def cards_html(con, month, prefix):
    """The two cards under the table of "Scan reading against Marg". '' when OFF."""
    if is_off():
        return ""
    ensure(con)
    B_list = bills(con, month)
    acon = None
    try:
        acon = PA()._assets_con()
    except Exception:                                         # noqa: BLE001
        acon = None
    try:
        try:
            sync(con, month, B_list, acon)
        except Exception as e:                                # noqa: BLE001 -- review 4: the cards still draw; caught up on the next open
            try:
                con.rollback()
            except sqlite3.Error:
                pass
            print("marg_right sync failed: %s" % e, file=sys.stderr)
        scan_url = prefix + "/api/s738/scan/%d"
        dif = [B for B in B_list if any(ln["bad"] for ln in B["lines"])]
        tap_b = [B for B in dif if not B["total_ok"]]
        auto_b = [B for B in dif if B["total_ok"]]
        mname = PA()._month_name(month) if hasattr(PA(), "_month_name") else month
        parts = [CSS, '<div class="card s850" id="s850lines"><b>Lines that differ — %s</b><div class="sub">Where a bill\'s totals agree, Marg\'s line '
                 'is taken over the scan\'s by itself. Where they differ, tap <b>Marg is right</b> on a line the scan misread; a real Marg mistake stays '
                 'on Amir\'s “Where Marg differs” list as today.</div>' % esc(mname)]
        parts += [_bill_html(con, acon, B, scan_url) for B in tap_b]
        if not tap_b:
            parts.append('<div class="sub" style="margin-top:8px">No bill with differing totals has a differing line this month.</div>')
        if auto_b:
            parts.append('<details><summary class="sub" style="cursor:pointer;padding:8px 0">Accepted by themselves — totals agree: %d bill%s</summary>%s</details>'
                         % (len(auto_b), "" if len(auto_b) == 1 else "s", "".join(_bill_html(con, acon, B, scan_url) for B in auto_b)))
        if acon is None:
            parts.append('<div class="sub">The scans\' own readings are not reachable just now: the corrections are kept on the next open.</div>')
        parts.append("</div>")
        T = month_table(con, month, B_list)
        kr = "".join("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>" % (esc(k), n, a, t) for k, n, a, t in T["kinds"])
        parts.append('<div class="card s850" id="s850kept"><b>Corrections kept · %s</b><div class="sub">What the scan reader read wrong where Marg was '
                     'accepted — it goes to the Scan App chat each month, for its reader.</div><table><tr><th>Kind</th><th>Lines</th>'
                     '<th>By totals agreeing</th><th>By a tap</th></tr>%s</table><div class="sub">%s: %d bill%s checked · %d with a line differing · '
                     '%d of them with totals agreeing (accepted by themselves) · %d for a tap%s.</div></div>'
                     % (esc(mname), kr or '<tr><td colspan="4">none yet</td></tr>', esc(mname), T["bills"], "" if T["bills"] == 1 else "s",
                        T["differing"], T["agreeing"], T["for_tap"], (" · %d answered" % T["tapped"]) if T["tapped"] else ""))
        return "".join(parts)
    finally:
        if acon is not None:
            acon.close()


# ====================================================================== the Item ledger's purchase rows
def ledger_verdict(con, names, supkey, bill_no, day, acon=None):
    """The verdict of this item's line on a Marg purchase bill: (state, words, note) or None (no linked scan / the line not on it)."""
    if is_off() or not _table(con, "purchase_sarvam_check"):
        return None
    rows = _q(con, "SELECT id, supplier FROM purchase_bill WHERE bill_no=? AND bill_date=?", (str(bill_no), str(day)[:10]))
    rows = [r for r in rows if re.sub(r"[^A-Z]", "", str(r["supplier"] or "").upper())[:8] == supkey] or (rows if len(rows) == 1 else [])   # review 7
    want = {_norm(n) for n in (names or []) if n}
    taps = _taps(con)
    for b in rows:
        for r in _check_rows(con, "bill_id=?", (int(b["id"]),)):
            try:
                B = _bill(r, json.loads(r["detail"] or "{}"), taps)
            except ValueError:
                continue
            ln = next((x for x in B["lines"] if _norm(x["marg_item"]) in want), None)
            if ln is None:
                continue
            note = ""
            if ln["state"] in ("auto", "tapped") and acon is not None:
                s, m = values(con, acon, B).get(ln["key"], (None, None))
                note = "; ".join("scan read %s %s" % (k, kind_values(k, s, m)[0]) for k in ln["bad"] if kind_values(k, s, m)[0])
            words = {"agrees": "agrees", "auto": "Marg accepted — totals agree",
                     "tapped": "Marg is right · %s" % ((ln["tap"] or {}).get("by") or "you"),
                     "ask": "the scan differs (%s) — a tap on Scan reading against Marg" % ", ".join(ln["bad"])}[ln["state"]]
            return ln["state"], words, note
    return None


def annotate_ledger(con, it, L):
    """item_ledger: each PURCHASE entry gets e['s850_html'] -- its scan line's verdict tag. Never raises past here."""
    if is_off():
        return 0
    acon = None
    try:
        acon = PA()._assets_con()
    except Exception:                                         # noqa: BLE001
        acon = None
    n, memo = 0, {}
    try:
        for day in L.get("days") or []:
            for e in day.get("entries") or []:
                if e.get("kind") != "PURCHASE" or not e.get("ref"):
                    continue
                k = (e.get("supkey") or "", e["ref"], day["day"])
                if k not in memo:
                    try:
                        memo[k] = ledger_verdict(con, it.get("names") or [it.get("name")], k[0], k[1], k[2], acon)
                    except Exception as ex:                   # noqa: BLE001 -- the row as before
                        print("marg_right ledger verdict failed: %r" % (ex,), file=sys.stderr)
                        memo[k] = None
                v = memo[k]
                if not v:
                    continue
                col = {"agrees": GREY, "auto": GREEN, "tapped": GREEN, "ask": AMBER}[v[0]]
                e["s850_html"] = (TAG % (col[0], col[1], esc(v[1]))) + ((' <span class="grey">%s</span>' % esc(v[2])) if v[2] else "")
                n += 1
    finally:
        if acon is not None:
            acon.close()
    return n


if __name__ == "__main__":
    # python3 marg_right.py <finance.db> <YYYY-MM> -- the month's verdicts as text (read only; no assets.db)
    c = sqlite3.connect(sys.argv[1])
    c.row_factory = sqlite3.Row
    BL = bills(c, sys.argv[2])
    for B in BL:
        for ln in B["lines"]:
            if ln["bad"]:
                print(B["asset_bill_id"], B["marg"].get("bill_no"), ln["key"], ",".join(ln["bad"]), ln["state"])
    print(json.dumps(month_table(c, sys.argv[2], BL)))
