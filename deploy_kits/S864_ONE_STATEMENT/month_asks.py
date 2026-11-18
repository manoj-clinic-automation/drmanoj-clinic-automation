#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
month_asks.py -- S855_MONTH_ASKS (17-Nov-2026, Sanjeevni session 476); S857_CHECK_OPEN_PATHS the same evening; S864_ONE_STATEMENT (18-Nov-2026,
session 479, D1000 reshaped): the supplier-wise statement is never asked -- Marg's bill-wise and supplier-wise are ONE family (the same five figures
per bill; purchase_app keeps the newest). A finished month needs the SAME pair Amir exports every visit, once more over the whole month, and again
only for a reason this file can name (a correction after the statement). open_items() -- every
open item of the month (rows 2-8 of the purchase check) named, with whose it is and its full path to resolution, for the check's strip; the card
counts what is open (the bills an export will clear are listed inside that export, not counted again).

THE OWNER, 17-Nov-2026 17:08-17:12 IST: the bill-wise / supplier-wise discrepancy (Kedar A000211, Yogendra 19612, Shivaaz 3854) was flagged, but
nobody was asked for the fresh Marg export that settles it; and Janta 21965's old Wrong mark was held on the payment page while the purchase
check said "clear". "It should also ask for whatever reports are needed as a fresh export from Marg ... Janta ... should also be flagged ...
I should need not come to you for these things." "What you have said should show prominently at multiple places ... the payments page, etc.,
for me as well as for Amir, as you had said for the statement part only."

WHAT -- one source of a month's open asks, drawn in every place they apply (never computed twice):
  EXPORT asks (a month that has ended, not FINAL), S864: the finished month's PAIR -- Marg's BILL WISE PURCHASE STATEMENT and the
    SUPPLIER/ITEM WISE PURCHASE STATEMENT, FROM the 1st TO the last day -- asked when
      * no statement covering the whole month has reached the server, or no item lines covering it (the month has ended);
      * a correction the system knows of came AFTER the newest whole-month statement: Amir's own 'meri entry galat thi' on a bill of the
        month; a bill of the month on Amir's correction list (S738: Marg to be corrected to the paper, then the pair); a scanned bill of the
        month answered 'not in Marg -- enter it' (S849) and not yet in Marg;
      * bills still without item lines (the item-wise alone).
    Every ask NAMES its reason (English on his pages, Hindi on Amir's steps and card). Nothing is ever asked 'again' without one.
    -> his payment sheet (a card at the top), his purchase check (a card at the top + row 8 counts them), his Needs-you, and AMIR'S CARD and
    steps 3 / 4 (amir_pairs). Each leaves by itself when the report reaches the server (and the reason is gone).
  WRONG marks (his only, never Amir's): every bill of the month still marked Wrong --
    * the newest statement shows the paper's figure -> resolved by itself (purchase_app._resolve_wrong, S371's rule on the newest statement);
    * settled as a purchase return (S740's track resolved by the dealer's revised bill / credit note) -> resolved here by itself, recorded;
    * on Amir's correction list (S738) -> "with Amir to correct Marg";
    * anything else -> "nothing will clear it by itself": his one tap "Correct -- Marg's figure stands" (POST /finance/purchase/api/s855/correct,
      the doctor only).
  No 'disagree' bucket: the two statements are one family and cannot disagree (the newer is the figure).
Writes: purchase_bill.verdict (the two resolutions above, never on a FINAL month), purchase_audit. Nothing else.
OFF: /root/finance/_off/ALL_OFF or /root/finance/_off/S855_OFF -- no asks drawn, nothing resolved.
"""
import calendar
import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys

KIT = "S855_MONTH_ASKS"
VERSION = "S864-MONTH-ASKS-2.0"
HERE = os.path.dirname(os.path.abspath(__file__))
OFF_FLAGS = (os.path.join(HERE, "_off", "ALL_OFF"), os.path.join(HERE, "_off", "S855_OFF"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
EN_KIND = {"STATEMENT": "bill-wise statement", "ITEMS": "item lines"}
TYPE_KEY = {"SUPPLIERWISE": "STATEMENT", "BILLWISE": "STATEMENT", "ITEMWISE": "ITEMS", "BILLITEMWISE": "ITEMS"}
# the pair as Amir's step 3 names it (amir_day.PAIR order): (export kind, purchase_export types, his label, the month-asks key)
PAIR_KINDS = (("ITEMWISE", ("ITEMWISE", "BILLITEMWISE"), "Item-detail purchase report", "ITEMS"),
              ("BILLWISE", ("BILLWISE", "SUPPLIERWISE"), "Bill-wise purchase report", "STATEMENT"))
CARD_CSS = ("<style>.s855{border:2px solid #dc6803;background:#fffaeb;border-radius:12px;padding:12px 14px;margin:0 0 14px}"
            ".s855 h2{margin:0 0 6px;font-size:17px;color:#93370d}.s855 .it{margin:8px 0;padding:8px 10px;background:#fff;border-radius:8px;"
            "border:1px solid #fedf89}.s855 .t{font-family:monospace;font-size:13px;background:#f2f4f7;padding:2px 6px;border-radius:4px}"
            ".s855 .sub{color:#667085;font-size:13px}.s855 button{margin-top:6px}</style>")


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def now_iso():
    return dt.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S")


def today():
    return dt.datetime.now(IST).date()


def is_off():
    """OFF by the switch files; also under MONTH_ASKS_FROZEN_WALK=1, set ONLY by an installer around an older kit's frozen walk re-run (its exact
    counts predate these asks) -- the service never sets it."""
    if os.environ.get("MONTH_ASKS_FROZEN_WALK") == "1":
        return "MONTH_ASKS_FROZEN_WALK"
    return next((f for f in OFF_FLAGS if os.path.exists(f)), None)


def PA():
    import purchase_app                                     # noqa: PLC0415 -- beside this file
    return purchase_app


def SR():
    import scan_register                                    # noqa: PLC0415
    return scan_register


def _q(con, sql, params=()):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.execute(sql, params)]


def _table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def _ddmon(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b")
    except (TypeError, ValueError):
        return str(iso or "")


def _month_last(month):
    y, m = int(month[:4]), int(month[5:7])
    return dt.date(y, m, calendar.monthrange(y, m)[1])


def _rs(p):
    try:
        return PA()._r(p)
    except Exception:                                         # noqa: BLE001
        return "Rs %d" % round((p or 0) / 100.0)


def _bill_name(b):
    s = re.sub(r"\s+", " ", str(b.get("supplier") or "")).strip()
    s = re.sub(r"\s+BAREILLY$", "", s, flags=re.I)
    return "%s %s" % (s.title(), b.get("bill_no") or "")


def _audit(con, who, action, ref, detail):
    try:
        d = dict(detail or {})
        d.setdefault("kit", KIT)
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (now_iso(), who or "", action, str(ref or ""), json.dumps(d, sort_keys=True, default=str)))
    except sqlite3.Error as e:
        print("month_asks audit failed: %s" % e, file=sys.stderr)


# ====================================================================== the months
def months(con):
    """The months the asks look at: from purchase.register_from (the first counted month) to this month, not FINAL."""
    pa = PA()
    try:
        r = con.execute("SELECT value FROM setting WHERE key='purchase.register_from'").fetchone()
        first = str(r[0])[:7] if r and r[0] else "2026-10"
    except sqlite3.Error:
        first = "2026-10"
    if not re.match(r"^\d{4}-\d\d$", first):
        first = "2026-10"
    out, cur, end = [], dt.date(int(first[:4]), int(first[5:7]), 1), today().replace(day=1)
    while cur <= end and len(out) < 24:
        m = cur.strftime("%Y-%m")
        try:
            if pa._month_status(con, m)["status"] != "final":
                out.append(m)
        except Exception:                                     # noqa: BLE001
            out.append(m)
        cur = (cur.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    return out


def _stamp(con, md5):
    """(digits of the export's own stamp -- or of its received time when the stamp is empty --, type); ('', '') when unknown. Review L3."""
    if not md5:
        return ("", "")
    r = con.execute("SELECT export_stamp, type, received_at FROM purchase_export WHERE md5=?", (md5,)).fetchone()
    if not r:
        return ("", "")
    d = re.sub(r"\D", "", str(r[0] or ""))[:14] or re.sub(r"\D", "", str(r[2] or ""))[:14]
    return (d, str(r[1] or ""))


# ====================================================================== the asks of one month
_CACHE = {}


def month_asks(con, month, s=None):
    """The month's asks, cached for as long as the connection has not written (review S5)."""
    if s is not None or is_off():
        return _month_asks(con, month, s)
    try:                                                      # another process's commit moves data_version; a new connection with a reused id
        dv = con.execute("PRAGMA data_version").fetchone()[0]  # is caught by the 10-second bucket
    except sqlite3.Error:
        dv = None
    k = (id(con), month, getattr(con, "total_changes", 0), dv, int(dt.datetime.now().timestamp()) // 10)
    got = _CACHE.get(k)
    if got is None:
        if len(_CACHE) > 64:
            _CACHE.clear()
        got = _month_asks(con, month)
        _CACHE[k] = got
    return got


def _norm14(s):
    """Any stored time -> 14 digits (YYYYMMDDHHMMSS) so Marg's stamp and the server's ISO times compare as text; '' when unreadable."""
    d = re.sub(r"\D", "", str(s or ""))
    return d[:14] if len(d) >= 12 else ""


def _reasons(con, month, s, stmt):
    """[(en, hi, bill dict or None)] -- the corrections the system knows of that came AFTER the newest whole-month statement `stmt`
    (a purchase_export row), or that stand open on a bill of the month. Each is a reason to export the finished month's pair again."""
    out = []
    since = _norm14(stmt.get("export_stamp") or stmt.get("received_at")) if stmt else ""
    by_id = {int(b["id"]): b for b in s["bills"]}
    # (a) Amir's correction list (S738): a bill of the month Marg is to be corrected on, not yet shown by any export
    try:
        tracked = SR().s738_tracked(con)
    except Exception:                                         # noqa: BLE001
        tracked = {}
    for bid, t in sorted(tracked.items()):
        if (t or {}).get("settled_at") or (t or {}).get("gone_at") or str((t or {}).get("month") or "") != month:
            continue
        b = by_id.get(int(bid))
        if b is None:
            continue
        out.append(("%s is on Amir's correction list (paper %s, Marg %s): Marg corrected to the paper, then the pair exported again"
                    % (_bill_name(b), _rs(b.get("wrong_amount_p")), _rs(b.get("marg_p"))),
                    "%s Marg mein paper ke hisaab se theek karein (paper %s), phir dono report dobara" % (_bill_name(b), _rs(b.get("wrong_amount_p"))), b))
    # (b) his own 'meri entry galat thi' after the statement
    if _table(con, "amir_bill_answer"):
        for r in _q(con, "SELECT a.bill_id, a.at FROM amir_bill_answer a WHERE a.reason='self' AND a.bill_id IS NOT NULL ORDER BY a.at"):
            b = by_id.get(int(r["bill_id"]))
            if b is None or (since and _norm14(r["at"]) <= since):
                continue
            if not since and stmt is not None:
                continue
            out.append(("Amir corrected his own entry of %s on %s, after the statement" % (_bill_name(b), _ddmon(r["at"])),
                        "%s ki apni entry %s ko theek ki thi -- report usse purani hai" % (_bill_name(b), _ddmon(r["at"])), b))
    # (d) the newest whole-month statement does not carry every bill on the sheet (a bill left by an older statement, a part list): the pair again
    if stmt is not None:
        try:
            v = PA()._verify_statement(con, month, s)
            miss = [b for b in s["bills"] if b.get("bw_md5") != stmt.get("md5") and b.get("sw_md5") != stmt.get("md5")]
            if miss and not v.get("ok"):
                out.append(("the newest whole-month statement (%s) does not carry %d bill%s on the sheet: %s"
                            % (_ddmon(stmt.get("received_at") or ""), len(miss), "" if len(miss) == 1 else "s", ", ".join(_bill_name(b) for b in miss[:4])),
                            "poore mahine ki bill-wise mein %d bill nahi hai -- dono report dobara" % len(miss), None))
        except Exception as e:                                # noqa: BLE001
            print("month_asks: verify: %s" % str(e)[:120], file=sys.stderr)
    # (c) a scanned bill of the month answered 'not in Marg -- enter it' (S849) and not yet in Marg
    try:
        import scan_ask                                       # noqa: PLC0415
        v = scan_ask.view(con, for_amir=True)
        for c in v.get("enter") or []:
            if str(c.get("base") or "")[:7] != month:
                continue
            out.append(("a scanned bill of %s %s (%s) was answered 'not in Marg -- enter it': entered in Marg, then the pair exported again"
                        % (c.get("supplier") or "the dealer", c.get("bill_no") or "", _ddmon(c.get("base"))),
                        "scan ka bill %s %s Marg mein daalein, phir dono report dobara" % (c.get("supplier") or "", c.get("bill_no") or ""), None))
    except Exception as e:                                    # noqa: BLE001 -- the asks never wait on the scan list
        print("month_asks: scan_ask.view: %s" % str(e)[:120], file=sys.stderr)
    return out


def _month_asks(con, month, s=None):
    """dict(month, exports=[dict(key, title, first, last, why, why_hi, bills)], wrong=[dict(bill, how, words)], disagree=[], n,
    pair=dict(first, last, kinds=[(kind, label)], why=[en], why_hi=[hi]) or None). Read only."""
    out = dict(month=month, exports=[], wrong=[], disagree=[], n=0, pair=None)
    if is_off():
        return out
    pa = PA()
    s = s if s is not None else pa._month_summary(con, month)
    if s["status"]["status"] == "final" or not s["bills"]:
        return out
    ended = today() > _month_last(month)
    reps = pa._month_reports(con, month, s)
    by = {e["key"]: e for e in reps}
    stmt_e, items_e = by.get("STATEMENT"), by.get("ITEMS")
    first, last = month + "-01", _month_last(month).isoformat()
    need = {}                                                 # key -> [(en, hi)]
    if ended and stmt_e is not None and items_e is not None:
        stmt = stmt_e.get("export") if stmt_e["state"] == "received" else None
        if stmt is None:
            need.setdefault("STATEMENT", []).append(("the month has ended and no statement covering the whole of it has reached the server",
                                                     "mahina khatam -- poore mahine ki bill-wise report abhi nahi aayi"))
        if items_e["state"] != "received":
            need.setdefault("ITEMS", []).append(("the month has ended and no item lines covering the whole of it have reached the server",
                                                 "mahina khatam -- poore mahine ki item-wise report abhi nahi aayi"))
        elif items_e.get("no_lines"):
            k = int(items_e["no_lines"])
            need.setdefault("ITEMS", []).append(("%d bill%s still without item lines" % (k, "" if k == 1 else "s"),
                                                 "%d bill ki item lines abhi nahi aayi" % k))
        rs_ = _reasons(con, month, s, stmt)
        for en, hi, _b in rs_:
            need.setdefault("STATEMENT", []).append((en, hi))
        if need.get("STATEMENT"):                             # the statement asked -> the PAIR: the lines come with it
            need.setdefault("ITEMS", []).append(("exported with the statement -- the same visit, the same dates",
                                                 "bill-wise ke saath, same tareekh"))
    for key in ("STATEMENT", "ITEMS"):
        if key not in need:
            continue
        e = by[key]
        bills = []
        out["exports"].append(dict(key=key, title=e["title"], first=first, last=last, bills=bills,
                                   why="; ".join(x[0] for x in need[key]), why_hi=[x[1] for x in need[key]]))
    if out["exports"]:
        kinds = [(kind, label) for kind, _types, label, mk in PAIR_KINDS if mk in need]
        why_en, why_hi = [], []
        for key in ("STATEMENT", "ITEMS"):
            for en, hi in need.get(key, []):
                if en not in why_en and not en.startswith("exported with the statement"):
                    why_en.append(en)
                    why_hi.append(hi)
        out["pair"] = dict(first=first, last=last, kinds=kinds, why=why_en, why_hi=why_hi)
    # the bills still marked Wrong (the newest statement's self-resolution has run in settle())
    try:
        tracked = SR().s738_tracked(con)
    except Exception:                                         # noqa: BLE001
        tracked = {}
    for b in s["bills"]:
        if b.get("verdict") != "WRONG":
            continue
        wp = b.get("wrong_amount_p")
        t = tracked.get(int(b["id"])) or {}
        if int(b["id"]) in tracked and not t.get("settled_at") and not t.get("gone_at"):
            how, words = "amir", "with Amir to correct Marg to the paper (%s), since %s" % (_rs(wp), _ddmon(t.get("first_seen")))
        else:
            how, words = "yours", ("marked Wrong on %s (%s): paper %s, Marg %s. Nothing in the system will clear it by itself — "
                                   "if Marg's figure stands, tap Correct." % (_ddmon(b.get("verdict_at")), b.get("verdict_by") or "staff",
                                                                             _rs(wp), _rs(b.get("marg_p"))))
        out["wrong"].append(dict(bill=b, how=how, words=words))
    out["n"] = len(out["exports"]) + sum(1 for w in out["wrong"] if w["how"] == "yours")
    return out



# ====================================================================== the resolutions written by the system
def _s740_settled(con, b):
    """The S740 track of this bill's purchase return when it is RESOLVED (and not gone), AND the Wrong mark is that return's (the paper figure
    marked right is the return's own paper figure, review L1): dict(road, ref, at) or None."""
    if not _table(con, "s740_track") or not _table(con, "s740_answer"):
        return None
    ans = _q(con, "SELECT sup, paper_p FROM s740_answer WHERE lower(trim(bill_no))=? AND bill_date=? AND answer='yes' AND undone_at IS NULL",
             (str(b["bill_no"]).strip().lower(), str(b["bill_date"])[:10]))
    try:                                                      # review (second look): S740 keeps the number lowercased; the dealer by its key
        ans = [a for a in ans if PA().supplier_key(a["sup"]) == PA().supplier_key(b["supplier"])]
    except Exception:                                         # noqa: BLE001
        ans = []
    if not any(a["paper_p"] is not None and b.get("wrong_amount_p") is not None and abs(int(a["paper_p"]) - int(b["wrong_amount_p"])) <= PA().AGREE_P
               for a in ans):
        return None
    for r in _q(con, "SELECT rkey, road, ref, resolved_at, gone_at FROM s740_track WHERE kind='on_bill' AND rkey LIKE ?",
                ("bill:%%|%s|%s" % (b["bill_no"], str(b["bill_date"])[:10]),)):
        sup = r["rkey"][5:].split("|")[0]
        try:
            same = PA().supplier_key(sup) == PA().supplier_key(b["supplier"])
        except Exception:                                     # noqa: BLE001
            same = False
        if same and r["resolved_at"] and not r["gone_at"]:
            return dict(road=r["road"], ref=r["ref"], at=r["resolved_at"])
    return None


ROAD_EN = {"revised": "revised bill", "credit": "credit note", "adjusted": "adjustment on a later bill"}


def settle(con, month=None):
    """What the system resolves by itself, never on a FINAL month: (1) S864 -- a Wrong mark whose paper figure the NEWEST statement shows
    (purchase_app._resolve_wrong, S371's rule on the newest statement); (2) a Wrong mark settled as a purchase return (the dealer's revised
    bill / credit note, S740) becomes Correct. Never while the connection holds someone else's open transaction; any error rolls back its own
    writes (review S4). Returns [(bill id, words)]."""
    if is_off() or not _table(con, "purchase_bill") or getattr(con, "in_transaction", False):
        return []
    try:
        return _settle(con, month)
    except Exception as e:                                    # noqa: BLE001 -- nothing half-written stays
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("month_asks settle failed: %s" % str(e)[:160], file=sys.stderr)
        return []


def _settle(con, month=None):
    pa = PA()
    out = []
    rows = _q(con, "SELECT id, supplier, bill_no, bill_date, month, verdict, wrong_amount_p FROM purchase_bill WHERE verdict='WRONG'" +
              (" AND month=?" if month else ""), (month,) if month else ())
    if not rows:
        return out
    if hasattr(pa, "_resolve_wrong"):                         # S864: the newest statement shows the paper's figure
        for r in pa._resolve_wrong(con, who="S864 (newest statement)"):
            out.append((r[0], "resolved: the newest Marg statement shows %s, the figure marked right" % _rs(r[3])))
        if out:
            con.commit()
            done = {x[0] for x in out}
            rows = [b for b in rows if b["id"] not in done]
    for b in rows:
        try:
            if pa._month_status(con, b["month"] or "")["status"] == "final":
                continue
        except Exception:                                     # noqa: BLE001
            continue
        t = _s740_settled(con, b)
        if not t:
            continue
        reason = ("resolved: the purchase return was settled by the dealer's %s%s (%s) -- Marg's figure stands"
                  % (ROAD_EN.get(t["road"], t["road"] or "paper"), (" " + t["ref"]) if t["ref"] else "", _ddmon(t["at"])))
        n = con.execute("UPDATE purchase_bill SET verdict='CORRECT', verdict_by=?, verdict_at=?, reason=? WHERE id=? AND verdict='WRONG'",
                        ("S855 (purchase return settled)", now_iso(), reason, b["id"])).rowcount
        if n:
            _audit(con, "S855 (purchase return settled)", "verdict_resolved", b["id"],
                   dict(before="WRONG", wrong_amount_p=b["wrong_amount_p"], road=t["road"], ref=t["ref"]))
            out.append((b["id"], reason))
    if out:
        con.commit()
    return out


def correct(con, who, bill_id):
    """The doctor's tap on a Wrong mark nothing will clear: Correct, Marg's figure stands. (ok, message, http)."""
    if is_off():
        return False, "This is switched off.", 409
    pa = PA()
    b = con.execute("SELECT id, supplier, bill_no, month, verdict, wrong_amount_p, amount_p FROM purchase_bill WHERE id=?", (int(bill_id),)).fetchone()
    if not b:
        return False, "No such bill.", 404
    if b[4] != "WRONG":
        return False, "This bill is no longer marked Wrong — reload the page.", 409
    try:
        if pa._month_status(con, b[3] or "")["status"] == "final":
            return False, "This month is FINAL.", 409
    except Exception:                                         # noqa: BLE001
        return False, "The month could not be read.", 503
    reason = "you: Marg's figure stands (the Wrong mark of %s cleared on the payment sheet)" % _rs(b[5])
    n = con.execute("UPDATE purchase_bill SET verdict='CORRECT', verdict_by=?, verdict_at=?, reason=? WHERE id=? AND verdict='WRONG'",
                    (who, now_iso(), reason, int(bill_id))).rowcount
    if not n:
        con.rollback()
        return False, "This bill was answered on another screen a moment ago.", 409
    _audit(con, who, "verdict", int(bill_id), dict(verdict="CORRECT", before="WRONG", wrong_amount_p=b[5], via="S855 card"))
    con.commit()
    return True, "Correct — Marg's figure stands.", 200


# ====================================================================== the words, the cards
def export_en(a):
    title = "%s, FROM %s TO %s" % (a["title"], _dmy(a["first"]), _dmy(a["last"]))
    return title, a["why"]


def export_hi(a):
    return "%s, FROM %s TO %s" % (a["title"], _dmy(a["first"]), _dmy(a["last"]))


JS = ("<script>async function s855c(b){b.disabled=true;try{const r=await fetch(b.dataset.u,{method:'POST',credentials:'same-origin',"
      "headers:{'Content-Type':'application/json'},body:JSON.stringify({bill:+b.dataset.b})});const j=await r.json().catch(()=>({}));"
      "if(r.ok&&j.ok){location.reload();}else{b.disabled=false;b.nextElementSibling.textContent=j.message||('HTTP '+r.status);}}"
      "catch(e){b.disabled=false;}}</script>")


def card_html(con, month, prefix, doctor=True, A=None, where="pay"):
    """The card at the top of the payment sheet / the purchase check: '' when nothing is open."""
    if is_off():
        return ""
    settle(con, month)
    A = A if A is not None else month_asks(con, month)
    if not A["exports"] and not A["wrong"]:
        return ""
    try:
        mname = PA()._month_name(month)
    except Exception:                                         # noqa: BLE001
        mname = month
    items = []
    if A.get("pair"):
        p = A["pair"]
        items.append('<div class="it"><b>Amir exports last month\'s %s once more, from Marg as TEXT file%s:</b> %s'
                     '<div class="sub"><b>Why:</b> %s.</div><div class="sub">Asked on Amir\'s card and his steps 3 and 4; this line leaves by itself '
                     'when the reports reach the server.</div></div>'
                     % ("pair" if len(A["exports"]) > 1 else "item-wise report", "s" if len(A["exports"]) > 1 else "",
                        "".join('<div><span class="t">%s</span></div>' % esc(export_hi(a)) for a in A["exports"]),
                        esc("; ".join(p["why"]) or "the month has ended")))
    else:
        for a in A["exports"]:
            t, why = export_en(a)
            items.append('<div class="it"><b>Export from Marg as a TEXT file:</b> <span class="t">%s</span><div class="sub">%s. Asked of Amir on his card; '
                         'this line leaves by itself when the report reaches the server.</div></div>' % (esc(t), esc(why[:1].upper() + why[1:])))
    for w in A["wrong"]:
        b = w["bill"]
        btn = ""
        if w["how"] == "yours" and doctor:
            btn = ('<div><button type="button" data-b="%d" data-u="%s/api/s855/correct" onclick="s855c(this)">Correct — Marg\'s figure stands</button>'
                   ' <span class="sub"></span></div>' % (int(b["id"]), esc(prefix)))
        items.append('<div class="it"><b>%s</b> · %s · <span class="%s">%s</span>%s</div>'
                     % (esc(_bill_name(b)), esc(_ddmon(b.get("bill_date"))), "bad" if w["how"] == "yours" else "sub", esc(w["words"]), btn))
    with_amir = sum(1 for w in A["wrong"] if w["how"] == "amir")
    head = "Before %s can lock — %d open" % (mname, A["n"]) if A["n"] else "Before %s can lock" % mname
    if with_amir:
        head += " · %d with Amir" % with_amir
    return ('%s<div class="card s855" id="s855_%s"><h2>%s</h2>%s<div class="sub">The same list stands on the payment sheet, the purchase check and '
            'your Needs-you; Amir sees only the Marg reports to export, with the reason.</div></div>%s' % (CARD_CSS, esc(where), esc(head), "".join(items), JS))


def open_items(con, month):
    """S857: every open item of the month, in the purchase check's row order: [dict(row, what, whose, steps=[...])]. Read only (settle aside)."""
    if is_off():
        return []
    out = []
    try:
        mname = PA()._month_name(month).split(" ")[0]
    except Exception:                                         # noqa: BLE001
        mname = month
    try:
        n = SR().s749_month_open(con, month)
    except Exception as e:                                    # noqa: BLE001
        return [dict(row=8, what="The purchase check could not be read (%s)" % str(e)[:80], whose="—", steps=["Tell Claude."])]
    def pl(k, one, many):
        return one if k == 1 else many
    if n.get("amir"):
        k = n["amir"]
        out.append(dict(row=2, what="%d difference%s between the paper and Marg" % (k, pl(k, "", "s")), whose="Amir — on his card",
                        steps=["Amir corrects the bill in Marg to the paper's figure (₹1 included).", "His next Marg purchase export shows the fix.",
                               "The row clears by itself — nothing for you."]))
    if n.get("confirm"):
        k = n["confirm"]
        out.append(dict(row=3, what="%d bill%s waiting for your confirmation" % (k, pl(k, "", "s")), whose="You",
                        steps=["Open row 3.", "Tap Confirm on each bill once it is as you paid it."]))
    if n.get("reception"):
        k = n["reception"]
        out.append(dict(row=4, what="%d with reception (a scan, a rescan or a one-tap question)" % k, whose="Reception — on their list Aaj ka bill kaam",
                        steps=["Reception scans, rescans or answers on their own list.", "The row clears by itself when they do."]))
    if n.get("you"):
        k = n["you"]
        out.append(dict(row=5, what="%d for you and Shavez (a disputed reading or a paper not found)" % k, whose="You or Shavez",
                        steps=["Open row 5.", "Use its buttons on each line."]))
    if n.get("returns"):
        k = n["returns"]
        out.append(dict(row=6, what="%d purchase return%s waiting for the dealer's paper" % (k, pl(k, "", "s")), whose="The dealer, then reception",
                        steps=["The dealer gives a credit note or a revised bill.", "Reception scans it; the server reads it.", "The return clears by itself."]))
    try:
        dn = SR().s750_open(con, month)
    except Exception:                                         # noqa: BLE001
        dn = {}
    if dn.get("awaited"):
        k = dn["awaited"]
        out.append(dict(row=7, what="%d dealer summar%s awaited" % (k, pl(k, "y", "ies")), whose="Reception — it is on their list by itself",
                        steps=["Reception scans each dealer's %s summary on the pharmacy lane." % mname, "The server reads it and holds it against Marg.",
                               "You and Shavez are reminded each morning until all are in."]))
    if dn.get("differ") or dn.get("asked"):
        k = int(dn.get("differ") or 0) + int(dn.get("asked") or 0)
        out.append(dict(row=7, what="%d dealer summar%s differ%s from Marg" % (k, pl(k, "y", "ies"), pl(k, "s", "")), whose="You",
                        steps=["Open row 7.", "On each dealer: Ask the dealer, Carry to next month, or Accept the dealer's figure."]))
    if dn.get("unread"):
        k = dn["unread"]
        out.append(dict(row=7, what="%d dealer summar%s could not be read" % (k, pl(k, "y", "ies")), whose="Reception",
                        steps=["Open row 7: tap 'Ask reception to rescan'.", "The rescan is read by itself."]))
    try:
        settle(con, month)
        A = month_asks(con, month)
    except Exception:                                         # noqa: BLE001
        A = dict(exports=[], wrong=[], disagree=[], pair=None)
    if A.get("pair"):
        p = A["pair"]
        steps = ["Why: %s." % ("; ".join(p["why"]) or "the month has ended")]
        steps += ["Amir exports from Marg as a TEXT file: %s." % export_hi(a) for a in A["exports"]]
        steps += ["The medical PC sends them; the server reads them within about a quarter of an hour.",
                  "This item leaves by itself — nothing for you."]
        out.append(dict(row=8, what="Last month's %s (%s) to export from Marg once more, %s to %s" % ("pair" if len(A["exports"]) > 1 else "report",
                                                                                                        " + ".join(EN_KIND.get(a["key"], a["title"]) for a in A["exports"]),
                                                                                                        _dmy(p["first"]), _dmy(p["last"])),
                        whose="Amir — on his card and steps", steps=steps))
    else:
        for a in A["exports"]:
            t, why = export_en(a)
            out.append(dict(row=8, what="The %s for %s to %s to export from Marg" % (EN_KIND.get(a["key"], a["title"]), _dmy(a["first"]), _dmy(a["last"])),
                            whose="Amir — on his card",
                            steps=["Why: %s." % why, "Amir exports from Marg as a TEXT file: %s." % t,
                                   "The medical PC sends it; the server reads it within about a quarter of an hour.", "This item leaves by itself — nothing for you."]))
    for w in A["wrong"]:
        if w["how"] == "yours":
            out.append(dict(row=8, what="%s marked Wrong — nothing will clear it by itself" % _bill_name(w["bill"]), whose="You",
                            steps=["If Marg's figure is right: tap Correct on the card at the top of this page.",
                                   "If the paper is right: Amir corrects the bill in Marg; his next export clears it."]))
    return out


def row8_lines(con, month):
    """(open count, [html lines]) for the purchase check's row 8."""
    if is_off():
        return 0, []
    try:
        settle(con, month)
        A = month_asks(con, month)
    except Exception as e:                                    # noqa: BLE001 -- fails closed: one open line
        return 1, ['<div class="bad">The month\'s asks could not be read (%s) — the lock holds.</div>' % esc(str(e)[:80])]
    lines = []
    for a in A["exports"]:
        t, why = export_en(a)
        lines.append('<div class="bad"><b>Marg report to export:</b> %s — %s.</div>' % (esc(t), esc(why)))
    for w in A["wrong"]:
        if w["how"] == "yours":
            lines.append('<div class="bad"><b>Marked Wrong:</b> %s — %s</div>' % (esc(_bill_name(w["bill"])), esc(w["words"])))
    return A["n"], lines


def needs_lines(con):
    """One Needs-you line per month with something open (warn), opening that month's payment sheet."""
    out = []
    if is_off():
        return out
    for m in months(con):
        try:
            settle(con, m)
            A = month_asks(con, m)
        except Exception as e:                                # noqa: BLE001
            print("month_asks needs %s: %s" % (m, str(e)[:160]), file=sys.stderr)
            continue
        ye = [w for w in A["wrong"] if w["how"] == "yours"]
        if not A["exports"] and not ye:
            continue
        bits = []
        if A.get("pair"):
            bits.append("last month's Marg %s to export once more (asked of Amir: %s)" % ("pair" if len(A["exports"]) > 1 else "item-wise report",
                                                                                      "; ".join(A["pair"]["why"]) or "the month has ended"))
        elif A["exports"]:
            bits.append("Marg report%s to export: %s (asked of Amir)" % ("" if len(A["exports"]) == 1 else "s",
                                                                       ", ".join(EN_KIND.get(a["key"], a["title"]) for a in A["exports"])))
        if ye:
            bits.append("%d bill%s marked Wrong that nothing will clear by itself (%s)" % (len(ye), "" if len(ye) == 1 else "s",
                                                                                        ", ".join(_bill_name(w["bill"]) for w in ye[:3])))
        try:
            mname = PA()._month_name(m)
        except Exception:                                     # noqa: BLE001
            mname = m
        out.append(dict(cls="warn", target="scans", href="/finance/purchase/page/pay/%s" % m,
                        text="%s purchases cannot lock yet — %s" % (mname, "; ".join(bits))))
    return out


def _hi_month(month):
    try:
        y, m = int(month[:4]), int(month[5:7])
        return "January February March April May June July August September October November December".split()[m - 1] + " " + str(y)
    except (TypeError, ValueError, IndexError):
        return str(month or "")


def _got(con, kind, types, first, last, day):
    """Step 4's reading of one report of the finished month's pair for TODAY: ok (a live export covering first..last stamped today),
    door (the server's door VERIFIED one stamped today, not yet pulled), none."""
    d8 = str(day or today().isoformat()).replace("-", "")[:8]
    try:
        r = con.execute("SELECT export_stamp, received_at FROM purchase_export WHERE type IN (%s) AND superseded_by IS NULL AND period_from<=? "
                        "AND period_to>=? AND substr(replace(export_stamp,'-',''),1,8)=? ORDER BY export_stamp DESC LIMIT 1" % ",".join("?" * len(types)),
                        tuple(types) + (first, last, d8)).fetchone()
    except sqlite3.Error:
        r = None
    if r:
        st = _norm14(r[0] or r[1])
        return dict(state="ok", at=("%s:%s" % (st[8:10], st[10:12])) if len(st) >= 12 else "")
    if _table(con, "mi_file"):
        try:
            r = con.execute("SELECT stamp, received_at FROM mi_file WHERE verdict='VERIFIED' AND type IN (%s) AND substr(stamp,1,8)=? "
                            "AND substr(date_from,1,10)<=? AND substr(date_to,1,10)>=? ORDER BY stamp DESC LIMIT 1" % ",".join("?" * len(types)),
                            tuple("PURCHASE_" + t for t in types) + (d8, first, last)).fetchone()
        except sqlite3.Error:
            r = None
        if r:
            st = _norm14(r[0] or r[1])
            return dict(state="door", at=("%s:%s" % (st[8:10], st[10:12])) if len(st) >= 12 else "")
    return dict(state="none")


def amir_pairs(con, day=None):
    """S864 -- the finished months whose pair is asked, for Amir's steps 3 and 4: [dict(month, first, last, kinds=[(kind, label)], why_hi=[...],
    why=[...], got={kind: dict(state, at)})]. Read only."""
    out = []
    if is_off():
        return out
    for m in months(con):
        try:
            A = month_asks(con, m)
        except Exception as e:                                # noqa: BLE001
            print("month_asks amir_pairs %s: %s" % (m, str(e)[:160]), file=sys.stderr)
            continue
        p = A.get("pair")
        if not p:
            continue
        got = {}
        for kind, types, _label, _mk in PAIR_KINDS:
            if any(kind == k for k, _l in p["kinds"]):
                got[kind] = _got(con, kind, types, p["first"], p["last"], day)
        out.append(dict(month=m, first=p["first"], last=p["last"], kinds=list(p["kinds"]), why_hi=list(p["why_hi"]), why=list(p["why"]), got=got))
    return out


def amir_lines(con):
    """His card: one Hindi 'do this' line per finished month whose pair is asked, with the reason. [html]."""
    out = []
    if is_off():
        return out
    for p in amir_pairs(con):
        reps = " &middot; ".join(esc(label) for _k, label in p["kinds"])
        why = "".join("<li>%s</li>" % esc(w) for w in p["why_hi"])
        out.append("<div class=line style='border-left:4px solid #b42318;padding-left:8px'><span class=big><b>Pichhle mahine (%s) ki report dobara "
                   "nikaaliye</b></span><br><span>%s &mdash; FROM %s TO %s</span><ul class=sub style='margin:4px 0 0;padding-left:18px'>%s</ul>"
                   "<p class=sub>Tarika step 3 par hai. Report server par aate hi yeh line apne aap hat jaayegi.</p></div>"
                   % (esc(_hi_month(p["month"])), reps, esc(_dmy(p["first"])), esc(_dmy(p["last"])), why))
    return out


if __name__ == "__main__":
    # python3 month_asks.py <finance.db> -- the asks of every open month as text (read only: settle() is not called)
    c = sqlite3.connect(sys.argv[1])
    c.row_factory = sqlite3.Row
    for m in months(c):
        A = month_asks(c, m)
        for a in A["exports"]:
            print(m, "EXPORT", *export_en(a))
        for w in A["wrong"]:
            print(m, "WRONG", w["how"], _bill_name(w["bill"]), w["words"])
