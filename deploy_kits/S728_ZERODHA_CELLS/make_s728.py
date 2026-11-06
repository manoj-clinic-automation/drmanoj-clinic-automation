#!/usr/bin/env python3
"""make_s728.py -- kit S728 (session 390, the parent, 06-Nov-2026). F-1007, D754: the Zerodha papers in the accountants' pack.
   python make_s728.py <live packs.py> <out> [--expect <md5>]
The owner (D754): "zerodha papers - quarterly flow to be built". Five Zerodha papers wait on the shelf since 21-Oct (UCC HF5397
Manoj Kumar Agarwal and DM7535 Bhawna Agarwal -- the statement of account and the retention statement, 04-Jul -> 16-Oct; DM7535's
statement of transactions, locked) because no cell takes them. This adds, by counted edits:
  * six slots -- Zerodha statement of account, retention statement and statement of transactions, for Dr Manoj and for Dr
    Bhawna -- every quarter;
  * a Zerodha paper read by its own head (Zerodha Broking Limited; the holder printed under the UCC; From Date / To Date, or
    'Retention Statement as on'); never a tail (its narrations carry other banks' numbers);
  * a broker's quarter is the paper settled AFTER it: the quarter that holds (its end date - 45 days) -- Zerodha settles each
    quarter in the weeks after it ends (the paper of 04-Jul -> 16-Oct is July - September's);
  * the paper is filed as the broker's statement (no bank lines are read from it); a password box 'Zerodha' for the locked one."""
import hashlib, sys

EDITS = [
('''    ("sbi_ppf_bhawna",   "SBI",   "Dr Bhawna Agarwal (SBI PPF)",               "savings", "BHAWNA AGARWAL",               0),
]''',
'''    ("sbi_ppf_bhawna",   "SBI",   "Dr Bhawna Agarwal (SBI PPF)",               "savings", "BHAWNA AGARWAL",               0),
    # S728 (F-1007, D754): the Zerodha papers -- the statement of account and the retention statement, every quarter, both holders
    ("zerodha_acct_manoj",  "ZERODHA", "Dr Manoj Agarwal (Zerodha statement of account)",   "savings", "MANOJ KUMAR AGARWAL", 0),
    ("zerodha_ret_manoj",   "ZERODHA", "Dr Manoj Agarwal (Zerodha retention statement)",    "savings", "MANOJ KUMAR AGARWAL", 0),
    ("zerodha_acct_bhawna", "ZERODHA", "Dr Bhawna Agarwal (Zerodha statement of account)",  "savings", "BHAWNA AGARWAL",      0),
    ("zerodha_ret_bhawna",  "ZERODHA", "Dr Bhawna Agarwal (Zerodha retention statement)",   "savings", "BHAWNA AGARWAL",      0),
    ("zerodha_txn_manoj",   "ZERODHA", "Dr Manoj Agarwal (Zerodha statement of transactions)",  "savings", "MANOJ KUMAR AGARWAL", 0),
    ("zerodha_txn_bhawna",  "ZERODHA", "Dr Bhawna Agarwal (Zerodha statement of transactions)", "savings", "BHAWNA AGARWAL",      0),
]'''),
('''              "sbi_ppf_manoj": 6, "sbi_ppf_bhawna": 6}''',
'''              "sbi_ppf_manoj": 6, "sbi_ppf_bhawna": 6,
              "zerodha_acct_manoj": 3, "zerodha_ret_manoj": 3, "zerodha_acct_bhawna": 3, "zerodha_ret_bhawna": 3,
              "zerodha_txn_manoj": 3, "zerodha_txn_bhawna": 3}   # S728'''),
('''             "sbi_loan_bhawna": "loan", "sbi_ppf_manoj": "ppf", "sbi_ppf_bhawna": "ppf"}''',
'''             "sbi_loan_bhawna": "loan", "sbi_ppf_manoj": "ppf", "sbi_ppf_bhawna": "ppf",
             "zerodha_acct_manoj": "z_account", "zerodha_ret_manoj": "z_retention",            # S728: the paper's own words
             "zerodha_acct_bhawna": "z_account", "zerodha_ret_bhawna": "z_retention",
             "zerodha_txn_manoj": "z_transactions", "zerodha_txn_bhawna": "z_transactions"}'''),
('''SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"), ("SBI", "State Bank of India"))   # S621''',
'''SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"), ("SBI", "State Bank of India"),
                ("ZERODHA", "Zerodha"))   # S621; S728 (the statement of transactions comes locked)'''),
('''def identify_text(text):''',
'''_Z_ISO = r"(\\d{4}-\\d{2}-\\d{2}|\\d{2}[-/]\\d{2}[-/]\\d{4}|\\d{1,2}[- ][A-Za-z]{3,9}[- ,]+\\d{4})"
_Z_NARR = re.compile(r"(?i)\\b(?:NEFT|IMPS|UPI|RTGS|ACH|NACH|BIL|INF|MMT)\\b|\\d{2}[-/]\\d{2}[-/]\\d{2,4}|\\d{4}-\\d{2}-\\d{2}|\\b\\d{1,2}\\s+[A-Za-z]{3}\\s+\\d{4}")


def _z_date(s):
    s = " ".join((s or "").replace(",", " ").split())
    if re.match(r"^\\d{4}-\\d{2}-\\d{2}$", s):
        return s
    for fmt in ("%d-%b-%Y", "%d %b %Y", "%d-%B-%Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return _iso_any(s.replace("/", "-")) if s else None


def is_zerodha(text):
    """S728: a Zerodha paper prints 'Zerodha Broking Limited' in its first lines, on a line that is no transaction row (no date, no
    NEFT / IMPS / UPI ...). A bank statement whose narration names Zerodha is the bank's."""
    for ln in [x for x in (text or "").splitlines() if x.strip()][:8]:
        if "ZERODHA BROKING" in ln.upper() and not _Z_NARR.search(ln):
            return True
    return False


def zerodha_ident(text):
    """S728 (F-1007): a Zerodha paper's own head -> the holder (the line under the UCC, left of 'Zerodha Broking Limited'), the kind
    (retention statement / statement of account / statement of transactions / other) and the period. Never raises."""
    out = dict(holder="", kind="z_other", period_from=None, period_to=None)
    try:
        lines = [ln for ln in (text or "").splitlines() if ln.strip()][:12]
        for ln in lines:
            m = re.match(r"^\\s*([A-Z][A-Z .]{3,}?)\\s{2,}(?i:zerodha broking limited)", ln)
            if m:
                out["holder"] = " ".join(m.group(1).split())
                break
        up = " ".join((text or "").upper().split())
        if "RETENTION STATEMENT" in up:
            out["kind"] = "z_retention"
            m = re.search(r"(?i)retention\\s+(?:statement\\s+as\\s+on|date)\\s*[:\\-]?\\s*" + _Z_ISO, text or "")
            if m:
                out["period_from"] = out["period_to"] = _z_date(m.group(1))
            return out
        # the statement of account names its own columns (Cost Center, Voc. No); 'Statement of Transactions' names itself; anything
        # else (a contract note, a P&L) is not one of the three -- no slot takes it (the owner's one tap does)
        out["kind"] = "z_account" if ("VOC. NO" in up or "COST CENTER" in up) else ("z_transactions" if re.search(r"STATEMENT OF TRANSACTION|TRANSACTION STATEMENT", up) else "z_other")
        a = re.search(r"(?i)from\\s+date\\s*[:\\-]?\\s*" + _Z_ISO, text or "")
        b = re.search(r"(?i)to\\s+date\\s*[:\\-]?\\s*" + _Z_ISO, text or "")
        if a and b:
            out["period_from"], out["period_to"] = _z_date(a.group(1)), _z_date(b.group(1))
        else:                                                         # 'for the period from 01-07-2026 to 30-09-2026'
            m = re.search(r"(?i)period\\s+from\\s*[:\\-]?\\s*" + _Z_ISO + r"\\s*(?:to|-|–)\\s*" + _Z_ISO, text or "")
            if m:
                out["period_from"], out["period_to"] = _z_date(m.group(1)), _z_date(m.group(2))
    except Exception:                                                 # noqa: BLE001
        pass
    return out


def identify_text(text):'''),
('''        if sb["period_to"]:
            pf, pt = sb["period_from"], sb["period_to"]
    return dict(sbi_type=sbi_type, bank=bank, kind=kind, tail=tail, period_from=pf, period_to=pt, up=hup, holder=holder,''',
'''        if sb["period_to"]:
            pf, pt = sb["period_from"], sb["period_to"]
    if is_zerodha(text):                                              # S728: the broker's own head -- its narrations name other banks
        zb = zerodha_ident(text)
        bank, kind, sbi_type, tail = "ZERODHA", "savings", zb["kind"], ""
        holder = _sbi_fold(zb["holder"]) if zb["holder"] else holder
        hup = " ".join(_sbi_fold(zb["holder"] or hup).split())
        if zb["period_to"]:
            pf, pt = zb["period_from"], zb["period_to"]
    return dict(sbi_type=sbi_type, bank=bank, kind=kind, tail=tail, period_from=pf, period_to=pt, up=hup, holder=holder,'''),
('''        else:
            return "n/a", ""
    except Exception as ex:''',
'''        elif slot["bank"] == "ZERODHA":                                # S728: filed as the broker's statement
            return "read", "filed -- the broker's statement (no bank lines are read from it)"
        else:
            return "n/a", ""
    except Exception as ex:'''),
('''        if s["kind"] == "card":        # S417: a card's month is the month its statement is DATED in (the statement date = period_to)''',
'''        if s["bank"] == "ZERODHA":     # S728: a broker's quarter is the paper settled after it -- the quarter holding (its end - 45 days)
            fs = [dict(r) for r in con.execute(
                "SELECT * FROM stmt_file WHERE slot_id=? AND period_to IS NOT NULL AND date(period_to, '-45 days') BETWEEN ? AND ? "
                "ORDER BY period_to DESC, COALESCE(locked,0) ASC, id DESC", (s["id"], lo, hi))]
            full, pieces = fs[:1], []
        if s["kind"] == "card":        # S417: a card's month is the month its statement is DATED in (the statement date = period_to)'''),
('''{"loan": "loan", "ppf": "PPF"}.get(SLOT_TYPE.get(s["key"], ""), s["kind"])''',
'''{"loan": "loan", "ppf": "PPF", "z_account": "statement of account", "z_retention": "retention statement", "z_transactions": "statement of transactions"}.get(SLOT_TYPE.get(s["key"], ""), s["kind"])'''),
('''AND period_to>=? AND id<>? ORDER BY id", (s["id"], hi, lo, f["id"]))] if (f and s["kind"] != "card") else []),''',
'''AND period_to>=? AND id<>? ORDER BY id", (s["id"], hi, lo, f["id"]))] if (f and s["kind"] != "card" and s["bank"] != "ZERODHA") else []),   # S728'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    s = open(src, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS, 1):
        n = s.count(a)
        if n != 1:
            print("make_s728: edit %d matches %d times (must be 1) -- nothing written" % (i, n))
            return 2
        s = s.replace(a, b)
    data = s.encode("utf-8")
    if "--expect" in sys.argv and hashlib.md5(data).hexdigest() != sys.argv[sys.argv.index("--expect") + 1]:
        print("make_s728: the result is %s, not the expected one -- nothing written" % hashlib.md5(data).hexdigest())
        return 3
    open(out, "wb").write(data)
    print("make_s728: %d edits applied -> %s (%s)" % (len(EDITS), out, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
