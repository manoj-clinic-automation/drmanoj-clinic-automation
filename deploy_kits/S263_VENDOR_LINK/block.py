

# =====================================================================
# S263 -- ONE FIRM, TWO NAMES.
#
# The bank details for 22 vendors were imported from the April-July 2026 NEFT
# advice sheets at S225, under the NAME THE BANK KNOWS. Marg's bills carry the
# name the VENDOR PRINTS. For 14 of them the two are not the same string, so a
# bill has never once landed on its own account row: they have all been falling
# to the cheque lane while their details sat on the server, correct and
# unreachable. August alone routed Rs 2,22,608 to cheques for this reason.
#
# THE FIX IS A LINK, NOT A COPY. One account still lives in exactly one row; the
# bill's name simply points at it. No account number is duplicated, so there is
# no second copy to go stale, and when Marg renames a supplier again the answer
# is one more row in this table -- not a re-import.
#
# Every pair below was confirmed by the owner on 14-Sep-2026 after the finding
# was put to him, including ESS KAY AGENCIES EXTN, which he checked against the
# bank himself ("verified, correct bank, name on bill is ESS KAY AGENCIES EXTN").
#
# NOT LINKED, deliberately: RAMA MEDICOSE and AGARWAL SURGICALS AND MEDICALS have
# no details anywhere and stay on the cheque lane by his ruling until they come.
#
# NO ACCOUNT NUMBER APPEARS IN THIS FILE, and none ever will: bank numbers do not
# enter the repository. A new vendor's account is carried on the install line and
# written straight into the database by seed_account_s263.py.
# =====================================================================

_ALIAS_S263 = (
    # the name on Marg's bill            the name on the account row
    ("KEDAR PHARMACEUTICAL",             "KEDAR PHARMA"),
    ("GUNINA PHARMACEUTICALS PVT LTD",   "GUNINA PHARMACEUTICALS"),
    ("L.K. DRUG HOUSE",                  "LK DRUG HOUSE"),
    ("SHRADDHA MEDICOSE",                "SHRADDHA MEDICOS"),
    ("YOGENDRA AGENCIES",                "YOGENDRA"),
    ("JUBILEE AGENCIES",                 "JUBLI AGENCY"),
    ("YUVIKA SURGICALS",                 "YUVIKA SURGICAL"),
    ("ESS KAY AGENCIES EXTN",            "ESS KAY AGENCIES"),
    ("RADHA MEDICAL & SCIENTIFIC",       "RADHA MEDICAL AND SCIENTIFIC"),
    ("DRUG DEAL",                        "DRUG DEALS"),
    ("RAVI MEDICAL AGENCY",              "RAVI MEDICAL AGENCIES"),
    ("SAISUN PHARMA PVT. LTD",           "SAISUN PHARMA PRIVATE LIMITED"),
    ("VERMA BROS. AND CO",               "VERMA BROS.AND CO"),
    ("SCIENTIFIC&MEDICAL AID CENTRE",    "SCIENTIFIC & MEDICAL AID CENTRE"),
)

def _alias_ensure_s263(con):
    """The link table. Idempotent: running it on every request must change
    nothing after the first time."""
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_vendor_alias (
        bill_norm     TEXT PRIMARY KEY,
        register_norm TEXT NOT NULL,
        who           TEXT,
        at            TEXT)""")
    for bill_norm, reg_norm in _ALIAS_S263:
        con.execute("INSERT OR IGNORE INTO purchase_vendor_alias "
                    "(bill_norm, register_norm, who, at) VALUES (?,?,?,?)",
                    (bill_norm, reg_norm, "owner (S263, 14-Sep-2026)", now_iso()))
    con.commit()


_vendor_bank_before_s263 = _vendor_bank


def _vendor_bank(con):                                            # noqa: F811
    """As before, and then: a bill name that is linked to a confirmed account
    row inherits that row's NEFT lane, and SAYS WHOSE ROW IT IS. A link to a row
    with no confirmed account changes nothing -- it cannot invent a lane."""
    try:
        _alias_ensure_s263(con)
    except sqlite3.Error:
        pass
    out = _vendor_bank_before_s263(con)
    try:
        rows = con.execute("SELECT bill_norm, register_norm "
                           "FROM purchase_vendor_alias").fetchall()
    except sqlite3.Error:
        return out
    for bill_norm, reg_norm in rows:
        src = out.get(reg_norm)
        if not src or src.get("route") != "NEFT":
            continue
        cur = out.get(bill_norm)
        if cur and cur.get("route") == "NEFT":
            continue
        out[bill_norm] = {"route": "NEFT",
                          "why": "account confirmed — on the register as %s" % reg_norm}
    return out
