#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p2.py -- kit S454_BILL_REGISTER, part 2 (S454 sections 5, 6, 7, 8, 12). CLAUDE.md rule 2: every live file is built from its live
bytes (every anchor exactly once, FROM -> TO pinned); scan_register.py is new; DUTY_MAP v4 -> v5 from the repository's v4.

  purchase_app.py  the matcher pairs by itself only what is VERIFIED, and the auto-link (5); a link that exists is never undone; a scan whose
                   bill number agrees names that bill as its likely bill; /page/scans is the month's register (7.1, ?legacy=1 the old tables);
                   the Sarvam counter by the rules (7.4); Vendor payments, its letter, annexure, advice and pack for supplier_msg.senders only,
                   the link drawn for them only, the phone book's account numbers and IFSC for them only (8); the earlier-month card counts
                   payment messages only
  porders.py       "the amount differs" beyond purchase.total_noise_rs, never 2% (5); the bill-scan Needs-you line only after
                   purchase.scan_wait_days, with the paper-not-found and not-yet-in-Marg lines (7.3)
  porders_s454.py  a scan started from a Marg bill's line carries that line's supplier only (5: it settles no bill by itself); the four
                   settings of this part on the owner's card; "digital" refused with its line (6)
  order_sheet.py   the four settings' defaults and meanings
  amir_day.py      purchase.entry_mode = paper: step 2's "Scan ho chuke bill (N)" with its words, the downloads, no grey line (6);
                   the owner's returns rule's own count kept for the duty map (12)
  reports_tile.py  Shavez's morning page: "Bill scan baaki: N · sabse purana X din" apart from the report rows (7.3)

    make_s454p2.py --finance /root/finance --kit DIR --dutymap-json FILE --dutymap-md FILE --out DIR
"""
import argparse
import hashlib
import json
import os

FROM = {"purchase_app.py": "591432422d6b06af3dff886a8a0fc378", "porders.py": "d4842f2c0f40a6ff69bd9a6d0425778f",
        "porders_s454.py": "c2608914e56b0f7ce049d93aeed23d39", "order_sheet.py": "cffbeef3f4405132ab1861ffc146bea9",
        "amir_day.py": "85f208d0d64def40fb5a02e02c531284", "reports_tile.py": "8a9870414cf299b0396bec4bc937ef04"}
NEWF = ("scan_register.py",)

# ============================================================================================================== purchase_app.py
PA = []
PA.append(('''        if b is not None and s is not None and r[1] not in linked and (r[2] == "CONFIRMED" or _match_s439(s, b) is not None):   # S440: a person's link stays''',
           '''        if b is not None and s is not None and r[1] not in linked:   # S454 (5): a link that exists is never undone by the rules; they only give it its state'''))
PA.append(('''    for s in scans:                                            # S440: a person recognised this paper as a second scan of a linked one''',
           '''    try:                                                       # S454 (5): the auto-link -- the ONE unscanned bill of the supplier with this amount
        new += _s454_autolink(con, who, scans, bills, taken, linked, dups)
    except Exception as _e_s454:                               # noqa: BLE001 -- the pass never fails for it
        _audit(con, who, "auto_link_error", "", dict(error=str(_e_s454)[:200], kit="S454"))
    for s in scans:                                            # S440: a person recognised this paper as a second scan of a linked one'''))
PA.append(('''    _rematch_if_changed(con, "scans")                          # S225 rev 9
    prefix = request.script_root + _url_prefix
    acon = _assets_con()''',
           '''    _rematch_if_changed(con, "scans")                          # S225 rev 9
    if request.args.get("legacy") != "1":
        return _s454_register_page(con, u)                     # S454 (7.1): the month's register; ?legacy=1 keeps the old tables
    prefix = request.script_root + _url_prefix
    acon = _assets_con()'''))
PA.append(('''        sc, mg = d.get("scan") or {}, d.get("marg") or {}
        yn = lambda v: "" if v else ' class="bad"'                  # noqa: E731
        bad_items = "; ".join("%s (%s)" % (x.get("scan_item") or "?", ", ".join(x.get("bad") or [])) for x in (d.get("items") or []) if x.get("bad"))''',
           '''        sc, mg = d.get("scan") or {}, d.get("marg") or {}
        r = _s454_sarvam_row(r, sc, mg, d)                          # S454 (7.4, F-690): the counter's own reading of each field
        yn = lambda v: "" if v else ' class="bad"'                  # noqa: E731
        bad_items = "; ".join("%s (%s)" % (x.get("scan_item") or "?", ", ".join(k for k in (x.get("bad") or []) if k not in ("batch", "expiry")))
                              for x in (d.get("items") or []) if [k for k in (x.get("bad") or []) if k not in ("batch", "expiry")])   # S454: not batch / expiry'''))
PA.append(('''    doctor = _is_doctor(u)
    rows = _book_rows(con)
    vendors = [r["vendor"] for r in rows]''',
           '''    doctor = _is_doctor(u)
    rows = _book_rows(con)
    if not _s452_may_advice(con, u):                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
    vendors = [r["vendor"] for r in rows]'''))
PA.append(('''    if not _book_allowed(u, con):
        return _refuse("The phone book is for Dr Manoj, Darpan and Shavez.")
    return _book_save(con, u, request.get_json(silent=True) or {})''',
           '''    if not _book_allowed(u, con):
        return _refuse("The phone book is for Dr Manoj, Darpan and Shavez.")
    body = request.get_json(silent=True) or {}
    if not _s452_may_advice(con, u):                           # S454 (8, D663): bank details are the owner's and Shavez's
        if str(body.get("action") or "") in ("bank", "verify"):
            return _refuse("Bank details are for Dr Manoj and Shavez.")
        body = {k: v for k, v in body.items() if k not in BANK_FIELDS}
    return _book_save(con, u, body)'''))
PA.append(('''                unsent = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE month=? AND status IN ('queued','failed')", (m,)).fetchone()[0])''',
           '''                unsent = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE month=? AND status IN ('queued','failed') AND kind IN ('neft','cheque')",
                                         (m,)).fetchone()[0])          # S454: payment messages only (an order or test message is not the sheet's)'''))
PA_APPEND = r'''


# ==========================================================================================================================================
# S454_BILL_REGISTER part 2 (03-Oct-2026, S454 5 / 7 / 8; D650 D662 D663 D665; F-690 F-691) -- the rules live in scan_register.py.
#   * _match_s439: a scan pairs with a Marg bill by itself only when the pair is VERIFIED (the total agrees within the noise, the bill number
#     agrees, and the supplier or the date agrees). _rematch keeps every stored link (the rules only give it its state) and, after the rules,
#     the auto-link pairs a scan with the ONE unscanned bill of its supplier carrying its amount (audit auto_link, grade AUTO).
#   * _why_s439: a scan whose bill number agrees with a bill (its supplier agreeing or not read) names that bill as its likely bill --
#     "Is this the bill?" -- so it is never sent to Amir as a bill Marg does not have.
#   * /page/scans is the month's register (scan_register.page_body); POST /api/s454/nopaper -- the owner's "Accept without paper" / Undo.
#   * The Sarvam counter reads every field by the counter's rule (scan_register.sarvam).
#   * Vendor payments (/page/pay..., the letter, the annexure, the advice, the pack; /api/pay-letter, /api/pay-verify, /api/pay-line) open only
#     for the owner and supplier_msg.senders; the "Vendor payments" link is drawn for them only; the phone book shows anyone else the
#     account number's last four digits and no IFSC, and refuses them a bank edit.
# ==========================================================================================================================================
_S454_CX = None


def _s454_sr():
    import scan_register                                       # noqa: PLC0415 -- beside this file
    return scan_register


def _s454_cx():
    return _S454_CX if _S454_CX is not None else _s454_sr().Ctx(_db())


_rematch_before_s454 = _rematch


def _rematch(con, who="system"):                                  # noqa: F811
    """S454: the S439 pass, with the rules' context loaded once for the pass."""
    global _S454_CX
    try:
        _S454_CX = _s454_sr().Ctx(con)
    except Exception:                                          # noqa: BLE001
        _S454_CX = None
    try:
        return _rematch_before_s454(con, who)
    finally:
        _S454_CX = None


_match_before_s454 = _match_s439


def _match_s439(s, b):                                            # noqa: F811
    """S454 (5): one scan against one Marg bill -> (1, 'EXACT', rule) when the pair is VERIFIED, else None."""
    if b["id"] in s.get("_no", ()):
        return None
    SR = _s454_sr()
    a = SR.agree(_s454_cx(), s, b)
    if SR.verified(a):
        return 1, "EXACT", "verified (S454 5): number + total%s" % ("".join(" + " + k for k in ("supplier", "date") if a[k] == "agree"))
    return None


_why_before_s454 = _why_s439


def _why_s439(s, bills, taken, last_date):                        # noqa: F811
    why, detail, hint = _why_before_s454(s, bills, taken, last_date)
    if why not in ("no_bill_yet", "vendor_unknown") or not s.get("bill_no"):
        return why, detail, hint
    SR = _s454_sr()
    cx = _s454_cx()
    canon = (s.get("_vendor") or (None,))[0]
    no = s.get("_no", ())
    scanned = _date_or_none_s439(s.get("created_at"))

    def gap(b):
        g = [abs((d - b["_date"]).days) for d in (s.get("_date"), scanned) if d is not None and b.get("_date") is not None]
        return min(g) if g else 9999
    cands = [b for b in bills if b["id"] not in no and SR.billno(s["bill_no"], b["bill_no"]) == "agree" and gap(b) <= S439_HINT_DAYS
             and (canon is None or canon == b.get("_skey") or SR.supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(s["id"])) == "agree")]
    if not cands:
        return why, detail, hint
    b = min(cands, key=lambda b: (1 if b["id"] in taken else 0, gap(b), abs((s.get("amount_p") or 0) - b["amount_p"]), b["id"]))
    s["_likely"] = b["id"]
    lab = "%s bill %s (%s, %s)" % (b.get("_skey") or supplier_key(b["supplier"]), b["bill_no"], _human(b["bill_date"]), _r(b["amount_p"]))
    also = (" — that bill already has scan #%d" % taken[b["id"]]) if b["id"] in taken else ""
    amt = s.get("amount_p")
    return ("amount_differs", "amount differs — the scan reads %s; %s carries the same number%s" % (_r(amt) if amt is not None else "no amount", lab, also),
            None if b["id"] in taken else b["id"])


def _s454_autolink(con, who, scans, bills, taken, linked, dups):
    """S454 (5): every unlinked scan (not a second scan) whose supplier agrees and whose amount is within Rs 1 of EXACTLY ONE unscanned bill
    of that supplier is paired with it (grade AUTO, audit auto_link). Returns the links made."""
    SR = _s454_sr()
    cx = _s454_cx()
    scan_from = _scan_from_s409(con)
    dup_ok = set()
    try:
        dup_ok = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_state WHERE dup_ok IS NOT NULL")}
    except sqlite3.Error:
        pass
    made = []
    for s in sorted(scans, key=lambda x: x["id"]):
        if s["id"] in linked or s["id"] in dups or s["id"] in dup_ok:
            continue
        b = SR.autolink_choice(cx, s, bills, taken, scan_from, refused=s.get("_no", ()))
        if not b:
            continue
        rule = "auto_link (S454 5): the only unscanned bill of this supplier with this amount"
        cur = con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id,asset_bill_id,grade,matched_on,linked_at) VALUES (?,?,?,?,?)",
                          (b["id"], s["id"], "AUTO", rule, now_iso()))
        if not cur.rowcount:
            continue
        con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (s["id"], b["id"]))
        _audit(con, who, "auto_link", b["id"], dict(scan=s["id"], supplier=supplier_key(b["supplier"]), bill_no=b["bill_no"], amount_p=b["amount_p"],
                                                     scan_no=s.get("bill_no"), scan_date=s.get("bill_date"), kit="S454"))
        taken[b["id"]] = s["id"]
        linked.add(s["id"])
        made.append((s["id"], b["id"], "AUTO", "auto_link"))
    return made


def _s454_bar(month):
    return ('<div id="s440bar" style="position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;background:#1f3864;color:#fff;'
            'padding:6px 10px;margin:0 0 10px;border-radius:0 0 8px 8px"><a id="s440back" href="%s" style="display:flex;align-items:center;'
            'justify-content:center;min-height:44px;padding:0 20px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;'
            'text-decoration:none">← BACK</a><span style="margin-left:auto;font-weight:600">Purchase bills</span></div>' % _esc(_s454_back()))


def _s454_back():
    frm = str(request.args.get("from") or "")
    return frm if (frm.startswith("/") and not frm.startswith("//") and len(frm) <= 300 and not re.search(r"[\\\r\n\"'<>]", frm)) else "/portal"


def _s454_register_page(con, u):
    SR = _s454_sr()
    prefix = request.script_root + _url_prefix
    months = SR.months_with_bills(con)
    month = str(request.args.get("month") or (months[0] if months else dt.date.today().strftime("%Y-%m")))[:7]
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    if month not in months:
        months = sorted(set(months + [month]), reverse=True)
    try:
        sarvam_compare(con)
    except Exception:                                          # noqa: BLE001
        pass
    body = SR.page_body(con, month, prefix, _is_doctor(u), months)
    up = ('<button id="s440up" aria-label="back to top" onclick="window.scrollTo({top:0,behavior:\'smooth\'})" style="position:fixed;right:14px;bottom:18px;'
          'width:48px;height:48px;border-radius:24px;border:0;background:#1f3864;color:#fff;font-size:24px;display:none;z-index:70;cursor:pointer">↑</button>'
          '<script>window.addEventListener("scroll",function(){var b=document.getElementById("s440up");if(b)b.style.display=(window.pageYOffset>window.innerHeight)?"block":"none"});</script>')
    return _page("Purchase bills — %s" % SR.month_name(month), _s454_bar(month) + body + up)     # S440's bar and up-arrow, once each


@bp.route("/api/s454/nopaper", methods=["POST"])
def api_s454_nopaper():
    """The owner's tap on a "paper not found" row of a counted month: accept it without paper, or undo (audited)."""
    u, err = _person("checker")
    if err:
        return err
    con = _db()
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        bid = 0
    ok, msg = _s454_sr().accept_nopaper(con, _who(u), bid, bool(int(b.get("accept") or 0)))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


def sarvam_summary(con, month):                                  # noqa: F811
    """S454 (7.4, F-690): the month's linked bills by the counter's rule (the old keys kept for the pages that read them)."""
    s = _s454_sr().sarvam(con, month)
    m = s["misses"]
    return dict(n=s["n"], agreed=s["agreed"], supplier_wrong=m["supplier"], billno_wrong=m["billno"], date_wrong=m["date"], total_wrong=m["total"],
                items_wrong=s["items_read"] - s["items_right"], items_read=s["items_read"], items_right=s["items_right"])


def _s446_sarvam_text(month, s):                                 # noqa: F811
    return ("%s: %d bill%s · read right in full %d · supplier misread %d · bill no. misread %d · date misread %d · total misread %d · "
            "item lines %d of %d read right (batch and expiry are not judged from a scan)"
            % (_month_name(month), s["n"], "" if s["n"] == 1 else "s", s["agreed"], s["supplier_wrong"], s["billno_wrong"], s["date_wrong"],
               s["total_wrong"], s.get("items_right", s["items_read"] - s["items_wrong"]), s["items_read"]))


def _s454_sarvam_row(r, sc, mg, d):
    """One row of the Sarvam page, its four flags by the counter's rule, its item count without batch / expiry."""
    try:
        SR = _s454_sr()
        f = SR.sarvam_flags(_s454_sr().Ctx(_db()), dict(vendor=sc.get("vendor"), bill_no=sc.get("bill_no"), bill_date=sc.get("date"),
                                                         amount_p=sc.get("total_p")),
                            dict(supplier=mg.get("supplier") or "", bill_no=mg.get("bill_no"), bill_date=mg.get("date"), amount_p=mg.get("total_p") or 0))
        wrong = sum(1 for x in (d.get("items") or []) if [k for k in (x.get("bad") or []) if k not in ("batch", "expiry")])
        return (r[0], f["supplier_ok"], f["billno_ok"], f["date_ok"], f["total_ok"], r[5], wrong, int(all(f.values()) and not wrong), r[8])
    except Exception:                                          # noqa: BLE001
        return r


# ---- Vendor payments: the owner and supplier_msg.senders only (S454 8, D663)
S454_PAY_PATHS = ("/page/pay", "/api/pay-letter", "/api/pay-verify", "/api/pay-line")


@bp.before_request
def _s454_pay_gate():
    path = request.path or ""
    rel = path[len(_url_prefix):] if path.startswith(_url_prefix) else None
    if rel is None or not any(rel == p or rel.startswith(p + "/") for p in S454_PAY_PATHS):
        return None
    try:
        u, err = _require("checker", "maker", "viewer")
        if err or not u:
            return None                                        # the page's own gate answers a stranger
        if _s452_may_advice(_db(), u):
            return None
    except Exception:                                          # noqa: BLE001 -- fail closed: these pages carry account numbers
        pass
    return _refuse("Vendor payments sirf doctor sahab aur Shavez ke liye hai.")


_book_nav_before_s454 = _book_nav


def _book_nav(prefix):                                          # noqa: F811
    out = _book_nav_before_s454(prefix)
    try:
        u, err = _require("checker", "maker", "viewer")
        if err or not u or not _s452_may_advice(_db(), u):
            out = out.replace('<a href="%s/page/pay">Vendor payments</a>' % prefix, "")
    except Exception:                                          # noqa: BLE001
        out = out.replace('<a href="%s/page/pay">Vendor payments</a>' % prefix, "")
    return out


def _s454_mask_bank(r):
    d = {k: r[k] for k in r.keys()}
    d["acct_no"] = _last4(d.get("acct_no")) if d.get("acct_no") else ""
    d["ifsc"] = ""
    d["upi_id"] = ""
    return d
# ---- S454 part 2 end --------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== porders.py
PO = []
PO.append(('''def _s440_differs(scan_p, marg_p):
    return scan_p is not None and abs(int(scan_p) - int(marg_p)) > max(S440_TOL_P, int(round(0.02 * int(marg_p))))''',
           '''def _s440_differs(scan_p, marg_p):
    return bool(scan_p) and abs(int(scan_p) - int(marg_p)) > _s454_noise_p()   # S454 (5): beyond purchase.total_noise_rs (Rs 10), never 2%'''))
PO.append(('''        b = [x for x in unscanned_bills(con) if _s454_counted(con, x["bill_date"])]     # S454 (4.8): a parked month raises no Needs-you
        if b:
            out.append(dict(cls="warn", target="porders", text="Bill scan pending on %d purchase bill%s%s" % (
                len(b), "" if len(b) == 1 else "s", (" (%d older than %d days)" % (sum(1 for x in b if x["red"]), SCAN_RED_DAYS)) if any(x["red"] for x in b) else "")))''',
           '''        out.extend(_s454_scan_lines(con))                        # S454 P2 (7.3): the bill-scan line only after purchase.scan_wait_days; paper not found;
                                                                  # a read scan not in Marg after purchase.entry_wait_days (counted months)'''))
PO_APPEND = '''


# ---- S454 part 2 (S454 5 / 7.3) ----------------------------------------------------------------------------------------------------------
def _s454_noise_p():
    """purchase.total_noise_rs in paise (Rs 10 when it cannot be read)."""
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.noise_p(_db())
    except Exception:                                          # noqa: BLE001
        return 1000


def _s454_scan_lines(con):
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.owner_lines(con)
    except Exception:                                          # noqa: BLE001
        return []
# ---- S454 part 2 end ---------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== porders_s454.py
PS = []
PS.append(('''                        intake=intake(b["vendor"], b["bill_no"], b["bill_date"], b["amount_p"], back=P + "/s454/scan" + ("?month=" + month if month else ""))))''',
           '''                        intake=intake(b["vendor"], back=P + "/s454/scan" + ("?month=" + month if month else ""))))   # S454 (5): the line's supplier only'''))
PS.append(('''    if key == "order.source":
        return v in ("marg_sheet", "system"), v''',
           '''    if key == "order.source":
        return v in ("marg_sheet", "system"), v
    if key == "purchase.entry_mode":                          # S454 P2 (6): paper, or both; digital is not built
        return v in ("paper", "both"), v'''))
PS.append(('''           "purchase.unread_pair_days": (1, 60)}.get(key)''',
           '''           "purchase.unread_pair_days": (1, 60), "purchase.total_noise_rs": (0, 100), "purchase.scan_wait_days": (1, 30),
           "purchase.entry_wait_days": (1, 60)}.get(key)'''))
PS.append(('''        return jsonify(ok=False, error="bad_value", message="%s: not a valid value" % key), 400''',
           '''        if key == "purchase.entry_mode" and str(b.get("value") or "").strip() == "digital":
            return jsonify(ok=False, error="not_built", message="purchase.entry_mode: 'digital' is not built yet -- scans go into Marg's digital "
                                                                "entry without Amir only in a later kit. Choose paper or both."), 400
        return jsonify(ok=False, error="bad_value", message="%s: not a valid value" % key), 400'''))

# ============================================================================================================== order_sheet.py
OSE = [('''    "purchase.unread_pair_days": ("7", "S454: how near in date a Marg bill must be for reception to be asked whether an unread paper is that bill"),''',
        '''    "purchase.unread_pair_days": ("7", "S454: how near in date a Marg bill must be for reception to be asked whether an unread paper is that bill"),
    "purchase.entry_mode": ("paper", "S454 P2 (6): paper = Amir enters from the paper bill and his register, the scans only offered; both = S452's words "
                                     "and its grey line; digital is not built"),
    "purchase.total_noise_rs": ("10", "S454 P2 (5): a scan's total within this many rupees of Marg's agrees (the difference shown); more is a question"),
    "purchase.scan_wait_days": ("3", "S454 P2 (7.3): you hear of a bill waiting to be scanned only after this many days"),
    "purchase.entry_wait_days": ("7", "S454 P2 (7.3): you see a read scan not yet entered in Marg after this many days (Amir is not told)"),''')]

# ============================================================================================================== amir_day.py
AD = []
AD.append(('''    s = w.get("s446") or {}
    bills, held = s.get("bills") or [], s.get("held") or []
    if not bills and not held:
        return ""
    today = [b for b in bills if b.get("today")]''',
           '''    s = w.get("s446") or {}
    bills, held = s.get("bills") or [], s.get("held") or []
    if _s454_entry_mode() == "paper":                          # S454 P2 (6): nothing new is asked of Amir
        return _s454_paper_card(bills)
    if not bills and not held:
        return ""
    today = [b for b in bills if b.get("today")]'''))
AD.append(('''        # the duty map's orphan duties, and a report refused today
        out.extend(_s444_duty_lines(con))''',
           '''        # the duty map's orphan duties, and a report refused today
        _s454_returns_cache(con)                               # S454 P2 (12): the owner's returns rule's own count, for manoj.returns_ok
        out.extend(_s444_duty_lines(con))'''))
AD_APPEND = '''


# ==========================================================================================================================================
# S454_BILL_REGISTER part 2 (03-Oct-2026, S454 6 / 12) -- Amir: nothing new is asked of him.
#   * purchase.entry_mode = paper (the default): step 2's card is "Scan ho chuke bill (N)" -- his paper bill and his register stay, the
#     scanned file is only offered; the downloads stay; no grey line "... reception ki jaanch mein hain"; nothing in step 7. both: S452's
#     words and its grey line return. digital is not built (the owner's settings card refuses it).
#   * The owner's returns rule (returns_kinds, the rule the owner's Needs-you line reads) is counted when his Needs-you is built and kept as
#     setting returns.pending_ok = "<n>|<oldest date>" -- manoj.returns_ok's one SELECT reads it (S454 12).
# ==========================================================================================================================================
def _s454_entry_mode():
    try:
        r = _db().execute("SELECT value FROM setting WHERE key='purchase.entry_mode'").fetchone()
        v = str(r[0]).strip() if r and r[0] else "paper"
        return v if v in ("paper", "both") else "paper"
    except Exception:                                          # noqa: BLE001
        return "paper"


def _s454_paper_card(bills):
    today = [b for b in bills if b.get("today")]
    rows = []
    for b in bills:
        bd = ("bill %s" % _ddmmyyyy(b["bill_date"])) if b.get("bill_date") else "bill ki tareekh scan par saaf nahi"
        rows.append("<div class=line><span class=big>%s</span> <span class=sub>%s &middot; scan: %s, %s &middot; %s</span><br>"
                    "<a class='btn plain' href='/finance/purchase/api/scan-file/%d'>Download</a></div>"
                    % (_esc(b.get("stamp")), _esc(b.get("supplier")), _esc(b.get("scan_ddmm")), _esc(b.get("who") or "?"), _esc(bd), int(b["id"])))
    zipl = ("<p><a class=btn href='/finance/purchase/api/scan-files/today.zip'>Aaj ke sab (%d) &mdash; ek zip</a></p>" % len(today)) if today else ""
    return ("<div class=card id=s446bills><h2>Scan ho chuke bill (%d)</h2>"
            "<p class=sub>Reception ne jo bill scan kiye hain aur Marg mein abhi nahi hain, woh yahan dikhenge. Aap apne register se jaise daalte hain, "
            "waise hi daaliye. Chahein to bill ki file yahan se le sakte hain.</p>%s%s</div>" % (len(bills), zipl, "".join(rows)))


def _s454_returns_cache(con):
    """The owner's returns rule (returns_kinds: counter returns from returns.act_from that wait for his OK, the last six months) -> setting
    returns.pending_ok '<n>|<oldest yyyy-mm-dd>'. Fail-soft: the old value stays when it cannot be read."""
    try:
        import returns_kinds                                   # noqa: PLC0415
        t = datetime.now().date()
        y, m = t.year, t.month
        months = []
        for _i in range(6):
            months.append("%04d-%02d" % (y, m))
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        n, dates = 0, []
        for ym in reversed(months):
            notes = returns_kinds.month_notes(con, "medical", ym)
            s = returns_kinds.enrich(con, "medical", ym, notes, with_prev=False)
            n += int(s.get("pending_ok") or 0)
            dates += [str(x.get("date"))[:10] for x in notes if x.get("pending_ok") and x.get("date")]
        con.execute("INSERT INTO setting (key, value, note) VALUES ('returns.pending_ok', ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    ("%d|%s" % (n, min(dates) if dates else ""), "S454 (12): the owner's returns rule's own count, kept for the duty map (manoj.returns_ok)"))
        con.commit()
    except Exception:                                          # noqa: BLE001
        pass
# ---- S454 part 2 end -----------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== reports_tile.py
RT = []
RT.append(('''            "line": line, "at": now.strftime("%Y-%m-%d %H:%M:%S")}''',
           '''            "line": line, "at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "s454_scan": _s454_scan_line(cx)}                  # S454 P2 (7.3): apart from the report rows -- their counts stay right'''))
RT.append(('''    body += lead + "<div class=card>" + rows + "</div>"''',
           '''    body += lead + "<div class=card>" + rows + "</div>"
    sl = s.get("s454_scan")
    if sl:                                                      # S454 P2 (7.3): one line while a bill of a counted month waits to be scanned
        body += ("<div class=card id=s454scan><div class=line><span class='big due'>%s</span> "
                 "<a class=btn style='display:inline-block;width:auto;padding:8px 14px;margin-left:8px' href='%s'>Kholiye</a></div></div>"
                 % (_esc(sl["text"]), _esc(sl["url"])))'''))
RT_APPEND = '''


# ---- S454_BILL_REGISTER part 2 (S454 7.3): Shavez's one line about bills to scan, counted months only ----------------------------------
def _s454_scan_line(cx):
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.shavez_line(cx)
    except Exception:                                          # noqa: BLE001
        return None
# ---- S454 part 2 end -----------------------------------------------------------------------------------------------------------------
'''

EDITS = {"purchase_app.py": PA, "porders.py": PO, "porders_s454.py": PS, "order_sheet.py": OSE, "amir_day.py": AD, "reports_tile.py": RT}
APPEND = {"purchase_app.py": PA_APPEND, "porders.py": PO_APPEND, "amir_day.py": AD_APPEND, "reports_tile.py": RT_APPEND}

# ============================================================================================================== DUTY_MAP v4 -> v5
RETURNS_SQL = ("SELECT COALESCE((SELECT CAST(substr(value, 1, instr(value, '|') - 1) AS INTEGER) FROM setting WHERE key = 'returns.pending_ok'), 0) AS n, "
               "(SELECT NULLIF(substr(value, instr(value, '|') + 1), '') FROM setting WHERE key = 'returns.pending_ok') AS since")
ARRIVAL_SQL = ("SELECT COUNT(*) AS n, MIN(substr(arrived_at,1,10)) AS since FROM purchase_order_line WHERE arrived_at IS NOT NULL AND COALESCE(supplied,0) > 0 "
               "AND COALESCE(billed_bill_no,'') = '' AND arrived_at < strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime', '-' || MAX(1, COALESCE((SELECT "
               "CAST(value AS INTEGER) FROM setting WHERE key = 'arrival.bill_grace_days'), 3)) || ' days')")   # the door's own grace (stock_watch.bill_pending_lines)
DM_CHANGE = {
    "manoj.returns_ok": dict(due_sql=RETURNS_SQL,
                             coded="sanjeevni_approvals.needs_you (3) -- every open month since S446 (returns_kinds' rule); S454 (12): the due_sql reads that rule's "
                                   "own count (setting returns.pending_ok, kept by amir_day when Needs-you is built) -- returns.act_from applied"),
    "reception.bill_scan": dict(owner_line="Bill scan waiting: {n} -- oldest {since} (after purchase.scan_wait_days)",
                                coded="porders.needs_you_lines -> scan_register.owner_lines (S454 7.3: only once the oldest is older than purchase.scan_wait_days)"),
    "amir.arrival_bill_entry": dict(due_sql=ARRIVAL_SQL),
}
DM_NEW = [dict(id="amir.scan_files", person="amir", tile="Amir ka kaam", door="/finance/amir", door_marker="Scan ho chuke bill",
               duty="(none asked) The scanned medicine bills Marg does not have yet are offered on step 2, 'Scan ho chuke bill (N)': he enters from his paper "
                    "bill and register as today; the file is there if he wants it (S454 6, purchase.entry_mode = paper)",
               duty_hi="Scan ho chuke bill (chahein to file lijiye)", due_sql="SELECT 0 AS n, NULL AS since", allowed_days=0, owner_line=None,
               coded="never due: nothing new is asked of Amir (S454 6); a read scan not in Marg after purchase.entry_wait_days reaches the owner only "
                     "(scan_register.owner_lines)")]
DM_MD_EDITS = (
    ("03-Oct-2026 by S454_BILL_REGISTER part 1 (D666, D668, D669: the one-task reception screen, Darpan's order sheet).**",
     "03-Oct-2026 by S454_BILL_REGISTER part 1 (D666, D668, D669: the one-task reception screen, Darpan's order sheet); 03-Oct-2026 by part 2 (D662, D663, "
     "D665: pairing on what a scan reads well, Amir asked nothing new, the bill-scan line after purchase.scan_wait_days, manoj.returns_ok on the "
     "owner's own rule).**"),
    ("| `purchase_order_line` arrived, supplied > 0, no billed bill (the card reads stock_watch's own \"bill entry baaki\" list) |",
     "| `purchase_order_line` arrived, supplied > 0, no billed bill, older than `arrival.bill_grace_days` (S454 part 2: the door's own grace -- the card reads "
     "stock_watch's own \"bill entry baaki\" list) |"),
)


def md5b(b):
    return hashlib.md5(b).hexdigest()


GUARD = "\nif __name__ == \"__main__\":"


def place_block(txt, block):
    """The block goes ABOVE the file's `if __name__ == "__main__":` guard when it has one (a cron runs some of these files as scripts:
    a block below the guard is not defined yet when main() runs -- part 1's fault in order_rules.py, mended by part 1D), else at the end."""
    c = txt.count(GUARD)
    if c > 1:
        raise SystemExit("STOP: the __main__ guard occurs %d times -- nothing built" % c)
    if c == 1:
        i = txt.index(GUARD)
        return txt[:i].rstrip("\n") + "\n" + block.rstrip("\n") + "\n\n" + txt[i:]
    return txt.rstrip("\n") + "\n" + block


def dutymap(jpath, mpath, out):
    d = json.load(open(jpath, encoding="utf-8"))
    if d.get("version") != 4 or d.get("kit") != "S454_BILL_REGISTER":
        raise SystemExit("STOP: %s is not the v4 map of S454 part 1 -- nothing written" % jpath)
    ids = [x["id"] for x in d["duties"]]
    for k in DM_CHANGE:
        if ids.count(k) != 1:
            raise SystemExit("STOP: duty %s occurs %d times" % (k, ids.count(k)))
    for x in d["duties"]:
        if x["id"] in DM_CHANGE:
            x.update(DM_CHANGE[x["id"]])
    for n in DM_NEW:
        if n["id"] in ids:
            raise SystemExit("STOP: %s is there already" % n["id"])
        at = max(i for i, x in enumerate(d["duties"]) if x["person"] == n["person"])
        d["duties"].insert(at + 1, n)
    d["version"] = 5
    d["_note"] = d["_note"] + (" S454 (03-Oct-2026, part 2): manoj.returns_ok reads the owner's own returns rule (returns.act_from; setting returns.pending_ok kept "
                               "by amir_day when Needs-you is built); reception.bill_scan's owner line only after purchase.scan_wait_days (scan_register); "
                               "amir.scan_files added -- never due: Amir is asked nothing new; amir.arrival_bill_entry due only after arrival.bill_grace_days, as its door.")
    bj = (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    md = open(mpath, "rb").read().decode("utf-8")
    for old, new in DM_MD_EDITS:
        if md.count(old) != 1:
            raise SystemExit("STOP: DUTY_MAP.md -- an anchor occurs %d times: %r" % (md.count(old), old[:80]))
        md = md.replace(old, new, 1)
    anchor = "| A parked month's work (optional) |"
    if md.count(anchor) != 1:
        raise SystemExit("STOP: DUTY_MAP.md -- the parked-month row occurs %d times" % md.count(anchor))
    i = md.index(anchor)
    j = md.index("\n", i) + 1
    md = md[:j] + (
        "| **S454 part 2:** the month's register (owner, English) | `/finance/purchase/page/scans?month=`: every Marg bill in one state -- Verified, Has its scan, "
        "Amount differs, No scan, Entered twice in Marg, Accepted without paper -- and the month's scans with no Marg bill | Scan links | Needs-you, scan_register: "
        "\"Bill scan waiting: N · the oldest X days\" (after `purchase.scan_wait_days`), \"Paper not found by reception\", \"Scanned and not yet in Marg for more "
        "than 7 days\" (owner only) |\n"
        "| Amir: the scanned bills Marg does not have `[amir.scan_files]` | never due (S454 6: nothing new is asked of him) | Amir ka kaam → step 2 \"Scan ho chuke "
        "bill (N)\" (purchase.entry_mode = paper) | none |\n"
        "| Shavez: bills to scan, one line | a counted line of \"Bill scan karna hai\" | Aaj ki reports → \"Bill scan baaki: N · sabse purana X din\" → Kholiye | "
        "(the owner's own line above) |\n") + md[j:]
    bm = md.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "DUTY_MAP.json"), "wb").write(bj)
    open(os.path.join(out, "DUTY_MAP.md"), "wb").write(bm)
    print("built DUTY_MAP.json v5 %s · DUTY_MAP.md %s" % (md5b(bj), md5b(bm)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--dutymap-json", required=True)
    ap.add_argument("--dutymap-md", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(FROM):
        raw = open(os.path.join(a.finance, f), "rb").read()
        m = md5b(raw)
        if m != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in EDITS.get(f, []):
            c = txt.count(old)
            if c != 1:
                raise SystemExit("STOP: an anchor occurs %d times in %s -- nothing built: %r" % (c, f, old[:90]))
            txt = txt.replace(old, new, 1)
        if f in APPEND:
            txt = place_block(txt, APPEND[f])
        out = txt.encode("utf-8")
        open(os.path.join(a.out, f), "wb").write(out)
        print("built %-18s %s -> %s  (%d edits%s)" % (f, m[:8], md5b(out), len(EDITS.get(f, [])), " + 1 block" if f in APPEND else ""))
    for f in NEWF:
        raw = open(os.path.join(a.kit, f), "rb").read()
        if os.path.exists(os.path.join(a.finance, f)):
            raise SystemExit("STOP: %s exists already on the box -- nothing built" % f)
        open(os.path.join(a.out, f), "wb").write(raw)
        print("new   %-18s %s" % (f, md5b(raw)))
    dutymap(a.dutymap_json, a.dutymap_md, a.out)


if __name__ == "__main__":
    main()
