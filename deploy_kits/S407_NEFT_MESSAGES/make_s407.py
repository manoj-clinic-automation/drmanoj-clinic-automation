#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s407.py -- builds the four patched live files of kit S407_NEFT_MESSAGES from the LIVE bytes by anchored edits.
Every anchor must occur exactly once, and every source must be at its FROM pin, or the build stops with nothing written.

  purchase_app.py          init mounts supplier_msg (fail-soft); the pay page gains the NEFT card (owner English / staff
                           Hindi) and the amber / green / red chip beside every NEFT vendor
  amir_day.py              every step page carries the NEFT card ('bheja <date> — bank se confirm baaki / ho gaya', bata diya)
  sanjeevni_approvals.py   Needs you gains 'N supplier message(s) unsent' and the bank-mismatch line (fail-soft)
  finance_app.py           the front gate's public list gains the two token doors of the reception phone (the module
                           checks the token itself, exactly as /finance/api/bank-sms does)

Usage: make_s407.py --finance /root/finance --out DIR
"""
import hashlib
import os
import sys

FROM = {
    "purchase_app.py": "7896eae4dff4427a2ebdb4f5023fd686",
    "amir_day.py": "00c443cbce0b07ba763bbe655a3e3c58",
    "sanjeevni_approvals.py": "74fe5437afd646851d0c28200592177d",
    "finance_app.py": "8055b0deddcb65234f1b9d818d56fda9",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


# ---------------------------------------------------------------- purchase_app.py
def build_purchase(s):
    s = rep(s, '''    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ====================================================================== keys
''', '''    app.register_blueprint(bp, url_prefix=url_prefix)
    # S407 (D623): the NEFT-messages module rides on this app; fail-soft -- the purchase book never waits for it
    try:
        import supplier_msg                                        # noqa: PLC0415
        supplier_msg.init(app, db_getter, require_fn, unit=unit, url_prefix=url_prefix)
    except Exception as _ex_sm:                                    # noqa: BLE001
        import sys as _sys                                         # noqa: PLC0415
        print("supplier_msg NOT mounted: %s" % _ex_sm, file=_sys.stderr)
    return bp


# ====================================================================== keys
''', "mount")
    s = rep(s, '''def _pay_sheet_table(groups, prefix, month, editable):
''', '''def _neft_state_s407(con, month):
    """S407 (D623): the month's NEFT state from supplier_msg (fail-soft: None when the module is absent)."""
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.state(con, month)
    except Exception:                                              # noqa: BLE001
        return None


def _neft_chip_s407(st, g):
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.chip(st, g)
    except Exception:                                              # noqa: BLE001
        return ""


def _neft_card_s407(con, u, month, prefix, final, groups):
    """S407: 'NEFT done (bank SMS received)' for the owner; the same state in Hindi for the staff; the suppliers' messages."""
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.pay_card(con, u, month, prefix, final, groups)
    except Exception as ex:                                        # noqa: BLE001
        return '<div class="card"><h2>NEFT</h2><div class="muted">the NEFT card is unavailable (%s)</div></div>' % _esc(str(ex)[:120])


def _pay_sheet_table(groups, prefix, month, editable):
''', "helpers")
    s = rep(s, '''    # ---------------------------------------------------------- 1 · the sheet
    cards = []
    for i, g in enumerate(groups):
        chips = ""
        if g["route"] != "NEFT":
            chips += ' <span class="chip warn">CHEQUE</span>'
''', '''    # ---------------------------------------------------------- 1 · the sheet
    _neft_st = _neft_state_s407(con, month)                        # S407: amber / green / red beside every NEFT vendor
    cards = []
    for i, g in enumerate(groups):
        chips = ""
        if g["route"] != "NEFT":
            chips += ' <span class="chip warn">CHEQUE</span>'
        else:
            chips += _neft_chip_s407(_neft_st, g)
''', "chips")
    s = rep(s, '''            '</div>%s%s%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               _pack_bar_s380(prefix, month),
               strip, sheet_card, verify_card,
''', '''            '</div>%s%s%s%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               _pack_bar_s380(prefix, month),
               strip, _neft_card_s407(con, u, month, prefix, final, groups), sheet_card, verify_card,
''', "the card on the page")
    return s


# ---------------------------------------------------------------- amir_day.py
def build_amir(s):
    s = rep(s, '''def _page(step, w, title, body, subtitle="", head_extra=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    return _shell("Amir -- kaam", _banner(step, w) + head + body +
                  "<p class=foot>Step %d of 7</p>" % step, head_extra)
''', '''def _neft_card_s407():
    """S407 (D623): 'NEFT <Month>: bheja <date> -- bank se confirm baaki / ho gaya' and the suppliers told (bata diya),
    on every step while an event is live. Read from supplier_msg; fail-soft: his day never waits for it."""
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.amir_card(_db())
    except Exception:                                              # noqa: BLE001
        return ""


def _page(step, w, title, body, subtitle="", head_extra=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    return _shell("Amir -- kaam", _banner(step, w) + head + body + _neft_card_s407() +
                  "<p class=foot>Step %d of 7</p>" % step, head_extra)
''', "the card")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.7  ·  kit S406_RETURNS_TWO_KINDS  ·  Session 283 (Sanjeevni)
#
''', '''#  sanjeevni_approvals.py  ·  v1.8  ·  kit S407_NEFT_MESSAGES  ·  Session 283 (Sanjeevni)
#
#  v1.8 (S407, D623, 26-Sep-2026): Needs you gains 'N supplier message(s) unsent' (a queued WhatsApp older than 30 minutes)
#  and 'NEFT of <Month>: bank shows X, sheet Y -- differs by Z' (read from supplier_msg, fail-soft).
#
''', "header")
    s = rep(s, '''VERSION = "1.7"
''', '''VERSION = "1.8"
''', "version")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 11 · S407 (D623): supplier messages unsent for 30 minutes; a NEFT the bank statement contradicts (fail-soft)
    try:
        import supplier_msg  # noqa: PLC0415
        lines.extend(supplier_msg.needs_you_lines(con))
    except Exception:  # noqa: BLE001
        pass
    # 7 · the statement's age (a word, not a fault)
''', "needs-you lines")
    return s


# ---------------------------------------------------------------- finance_app.py
def build_finance_app(s):
    s = rep(s, '''                "/finance/api/bank-sms",                   # S290: the phone's door; bank_sms.py checks its key
''', '''                "/finance/api/bank-sms",                   # S290: the phone's door; bank_sms.py checks its key
                "/finance/api/supplier-msg/next",          # S407: the reception phone's door; supplier_msg.py checks its token
                "/finance/api/supplier-msg/done",          # S407
''', "public paths")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance"), args.get("--out")
    if not (fin and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {
        "purchase_app.py": build_purchase(load(os.path.join(fin, "purchase_app.py"), "purchase_app.py")),
        "amir_day.py": build_amir(load(os.path.join(fin, "amir_day.py"), "amir_day.py")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "finance_app.py": build_finance_app(load(os.path.join(fin, "finance_app.py"), "finance_app.py")),
    }
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
