#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s574.py -- kit S574_PHONEBOOK_ONE_RECORD: the builder. Anchored edits on the LIVE bytes of five files in /root/finance.

    python3 -B make_s574.py --fin /root/finance --out DIR

Each file must be at its FROM pin, and every anchor must occur exactly once in it (a region's start and end anchors each exactly once,
the end after the start), else STOP (exit 2, nothing written). Writes DIR/<file> for the five files and prints each md5; the installer
compares them with PINS.sh's TO pins.

  purchase_app.py
    PA1  _phone_for -> THE ONE READER: book_on, book_record, book_numbers, book_number, book_shown; _phone_for = book_number(.., 'order')
    PA2  /page/orders, the plan's tel: link   -> book_number(.., 'call')
    PA3  /page/orders, the order book's tel:  -> book_number(.., 'call')
    PA4  /page/staff call buttons             -> book_shown (was _phones_for)
    PA5  _ensure_book: the new columns, purchase_vendor_premerge, purchase_book_change, the switch (default '0')
    PA6  _phones_for retired (no caller left)
    PA7  _book_save: the doctor's door for numbers / picks / add / merge / undo / switch; the merge, the undo, Marg's push into the one
         record, the one-record page; the bank cell and the add form as helpers (the OFF page draws them byte for byte as before)
    PA8  /page/book: switch ON -> the one-record page
    PA9  /page/book (OFF): the row loop through the helpers; the number buttons for the doctor only (the door is his)
    PA10 /page/book (OFF): the add form for the doctor only
    PA11 /page/book (OFF): the "without a phone number" note for the doctor only (it tells him to tap add numbers)
    PA12 /page/book (OFF): the doctor's one line "One record per dealer: OFF -- Turn on"
    PA13 /api/vendors (Marg's push): switch ON -> into the one record, never a replace; OFF -> today's statement, byte for byte
  order_sheet.py
    OS1  _phones retired -> book_card (call, wa, shown, on) from the one reader
    OS2  entries(): the card's numbers from book_card
    OS3  _queue_message: the Order WhatsApp number
    OS4  entries() docstring
  order_sheet_pdf.py
    SP1, SP2, SP3  the band's numbers: book_card's shown (OFF numbers 1-2; ON the Calls number, the WhatsApp number when another)
  porders_s454.py
    PS1  the words: nonum, num_call, num_wa
    PS2  the card's no-number word (switch ON: nonum)
    PS3  the done list's Call: the Calls number
    PS4  the supplier page: switch ON "Call: <n>" and "WhatsApp: <n>"; OFF as before
    PS5  the supplier page's no-number sentence (switch ON: nonum)
  supplier_msg.py
    SM1  _digits (the NEFT / cheque notice): the Payment message number
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "purchase_app.py": "147201dd288d291323023a764df3411e",
    "order_sheet.py": "247eeb48db8cc007faedfe14f3676893",
    "order_sheet_pdf.py": "b0cc86945d560e8cce842b799913e021",
    "porders_s454.py": "1c3d3927163e08114e3e26c5f06052a4",
    "supplier_msg.py": "2f43af754a160376cec955f92f3aa43a",
}

# ============================================================================================================================ purchase_app
PA1_START = 'def _phone_for(con, vendor):\n'
PA1_END = '# ====================================================================== pages\n'
PA1_NEW = r'''# ==========================================================================================================================================
# S574_PHONEBOOK_ONE_RECORD (18-Oct-2026, the owner's "Proceed with the build" 06:19 IST) -- THE ONE READER of a dealer's number (charter 2).
# Every page, message and check that needs a number asks book_number(con, name, use) -- use 'call' (a Call button, a tel: link), 'order'
# (where a WhatsApp order goes), 'pay' (a NEFT or cheque notice) -- or book_record / book_numbers / book_shown for a list. _phone_for stays as
# the 'order' wrapper, so porders.py and order_rules.py are unchanged. The switch purchase.book_one_record.on ('0' until the owner's tap):
#   OFF -- the lookup as before S574, exactly: the row whose vendor_norm is supplier_key(name), its phone (numbers 1-2 for a list); no pick.
#   ON  -- that row; a row merged into another -> that one record (one hop); a bill name with no row of its own -> the bank sheet's record by
#          purchase_vendor_alias (live: RAVI MEDICAL AGENCY); numbers 1-4; the owner's pick for the use when its slot holds a number, else
#          the first number.
# ==========================================================================================================================================
BOOK_ON_KEY = "purchase.book_one_record.on"
BOOK_SLOTS = ("phone", "phone2", "phone3", "phone4")
BOOK_USES = ("call", "order", "pay")


def book_on(con):
    """The switch. Anything but '1' (no row, an unreadable table) is OFF."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (BOOK_ON_KEY,)).fetchone()
    except sqlite3.Error:
        return False
    return bool(r) and str(r[0] or "").strip() == "1"


def _book_row(con, key):
    """purchase_vendor_contact's row for a vendor_norm, as a dict (whatever the connection's row factory); None when there is none."""
    try:
        cur = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (key,))
        r = cur.fetchone()
    except sqlite3.Error:
        return None
    return dict(zip([d[0] for d in cur.description], tuple(r))) if r is not None else None


def book_record(con, vendor):
    """The one record (a dict) for a Marg name, a bill name, a bank sheet's name or a vendor_norm, or None. '_s574_on' in it says
    whether it was read with the switch ON."""
    k = supplier_key(vendor)
    rec = _book_row(con, k)
    on = book_on(con)
    if on:
        if rec is None:
            try:
                a = con.execute("SELECT register_norm FROM purchase_vendor_alias WHERE bill_norm=?", (k,)).fetchone()
            except sqlite3.Error:
                a = None
            rec = _book_row(con, a[0]) if a else None
        if rec is not None and rec.get("merged_into"):
            rec = _book_row(con, rec["merged_into"]) or rec
    if rec is not None:
        rec["_s574_on"] = on
    return rec


def book_numbers(rec):
    """[(slot, number)] for the slots that hold a number, in slot order: 1-4 when the record was read with the switch ON, 1-2 when OFF
    (a number 3 or 4 saved while ON never leaks into an OFF reader)."""
    if not rec:
        return []
    slots = BOOK_SLOTS if rec.get("_s574_on") else BOOK_SLOTS[:2]
    return [(i + 1, rec.get(s)) for i, s in enumerate(slots) if rec.get(s)]


def _book_pick(rec, use):
    try:
        p = int(rec.get("%s_pick" % use))
    except (TypeError, ValueError):
        return None
    return p if 1 <= p <= 4 else None


def book_number(con, vendor, use="order"):
    """The number for one use ('call' | 'order' | 'pay'): the picked slot's number when that pick is set and its slot holds a number,
    else the first number, else ''. Switch OFF: the row's phone, exactly as _phone_for answered before S574."""
    rec = book_record(con, vendor)
    if rec is None:
        return ""
    if not rec.get("_s574_on"):
        return rec.get("phone") or ""
    nums = book_numbers(rec)
    pick = _book_pick(rec, use) if use in BOOK_USES else None
    got = dict(nums).get(pick) if pick else None
    return got or (nums[0][1] if nums else "")


def book_shown(con, vendor):
    """The numbers a sender's page or paper prints under the dealer's name: switch OFF numbers 1-2 (as before); ON the Calls number,
    then the Order WhatsApp number when it is another."""
    rec = book_record(con, vendor)
    if rec is None:
        return []
    if not rec.get("_s574_on"):
        return [n for _s, n in book_numbers(rec)]
    call, wa = book_number(con, vendor, "call"), book_number(con, vendor, "order")
    return [x for x in (call, "" if wa == call else wa) if x]


def _phone_for(con, vendor):
    """S574: the Order WhatsApp number, by the one reader (porders.py, order_rules.py and order_sheet's checks call this)."""
    return book_number(con, vendor, "order")


'''

PA2_OLD = '        phone = "" if viewer else _phone_for(con, v["vendor"])\n'
PA2_NEW = '        phone = "" if viewer else book_number(con, v["vendor"], "call")      # S574: a tel: link rings the Calls number\n'
PA3_OLD = '        phone = "" if viewer else _phone_for(con, o["vendor"])\n'
PA3_NEW = '        phone = "" if viewer else book_number(con, o["vendor"], "call")      # S574: a tel: link rings the Calls number\n'
PA4_OLD = '            phones = _phones_for(con, v["vendor"])\n'
PA4_NEW = '            phones = book_shown(con, v["vendor"])                 # S574: the one reader (OFF: numbers 1-2, as before)\n'

PA5_START = 'def _ensure_book(con):\n'
PA5_END = 'def _book_users(con):\n'
PA5_NEW = r'''S574_COLS = (("phone3", "TEXT"), ("phone4", "TEXT"), ("email1", "TEXT"), ("email2", "TEXT"), ("call_pick", "INTEGER"),
             ("order_pick", "INTEGER"), ("pay_pick", "INTEGER"), ("display_name", "TEXT"), ("merged_into", "TEXT"))
S574_TABLES = ("CREATE TABLE IF NOT EXISTS purchase_vendor_premerge (id INTEGER PRIMARY KEY AUTOINCREMENT, merged_at TEXT, merged_by TEXT, "
               "bill_norm TEXT, register_norm TEXT, bill_row_json TEXT, register_row_json TEXT, undone_at TEXT, undone_by TEXT)",
               "CREATE TABLE IF NOT EXISTS purchase_book_change (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, who TEXT, vendor_norm TEXT, "
               "what TEXT, old4 TEXT, new4 TEXT)")


def _ensure_book(con):
    have = {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    for col, typ in BOOK_COLS + S574_COLS:                     # S574: numbers 3-4, two emails, the three picks, the name kept, the merge
        if col not in have:
            con.execute("ALTER TABLE purchase_vendor_contact ADD COLUMN %s %s" % (col, typ))
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for sql in S574_TABLES:                                    # S574: the two rows as they stood before a merge (kept for undo); the changes
        con.execute(sql)
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?, '0', ?)",
                (BOOK_ON_KEY, "S574: one record per dealer -- '1' from the owner's tap on the phone book page; '0' reads the book as before S574"))
    con.commit()


'''

PA6_START = 'def _phones_for(con, vendor):\n'
PA6_END = 'def _book_rows(con):\n'
PA6_NEW = ''

PA7_START = 'def _book_save(con, u, b):\n'
PA7_END = '@bp.route("/api/book", methods=["POST"])\n'
PA7_NEW = r'''S574_OWNER_ACTIONS = ("add", "phones", "picks", "merge", "unmerge", "switch")
S574_USE_WORDS = (("call", "Calls"), ("order", "Order WhatsApp"), ("pay", "Payment msg"))
S574_UNDO_CLOSED = "Undo is closed: numbers were changed after the merge."
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _s574_d10(s):
    """A number's last 10 digits -- how two numbers are compared; '' when it has fewer."""
    d = re.sub(r"\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else ""


def _s574_4(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-4:] if d else ""


def _s574_change(con, who, vendor_norm, what, old="", new=""):
    """One line of the book's change list -- the last 4 digits only, never a full number."""
    con.execute("INSERT INTO purchase_book_change (at, who, vendor_norm, what, old4, new4) VALUES (?,?,?,?,?,?)",
                (now_iso(), who or "", vendor_norm or "", what, _s574_4(old), _s574_4(new)))


def _s574_mobile(s):
    """A number saved from the one-record page: 10 digits starting 6-9 (91 or 0 in front dropped); '' for a blank."""
    d = _clean_phone(s)
    if d and not re.match(r"^[6-9]\d{9}$", d):
        raise ValueError("a mobile number is 10 digits starting 6, 7, 8 or 9")
    return d


def _s574_email(s):
    v = str(s or "").strip()[:120]
    if v and (v.count("@") != 1 or not EMAIL_RE.match(v)):
        raise ValueError("an email has one @ and a dot after it")
    return v


def _book_save(con, u, b):
    """One door. Audit by field name and last-4 only. S574: numbers, picks, adding a supplier, the merge, its undo and the switch are
    Dr Manoj's alone, switch ON or OFF (the owner, 18-Oct 05:57 IST: staff hand him the number); bank and verify as before. A write names
    the record by its vendor_norm (the one-record page posts it); with the switch ON a write to a merged-away row lands on its one record."""
    action = str(b.get("action") or "")
    who = _who(u)
    if action in S574_OWNER_ACTIONS and not _is_doctor(u):
        return _refuse("Numbers are changed only by Dr Manoj.")
    if action in ("merge", "unmerge", "switch"):
        return _s574_owner_act(con, who, action, b)
    vendor = str(b.get("vendor") or "").strip()[:120]
    vn = str(b.get("vendor_norm") or "").strip()[:160]
    if action == "add" or not vn:
        if not vendor:
            return jsonify(ok=False, error="malformed", message="stockist name required"), 400
        key = supplier_key(vendor)
    else:
        key = vn
    on = book_on(con)
    row = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (key,)).fetchone()
    if on and row is not None and action != "add" and row["merged_into"]:
        one = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (row["merged_into"],)).fetchone()
        if one is not None:
            row, key = one, one["vendor_norm"]
    try:
        if action == "add":
            if row is not None or (on and book_record(con, vendor) is not None):
                return jsonify(ok=False, error="exists", message="%s is already in the book — edit it instead." % vendor), 409
            p1, p2 = _clean_phone(b.get("phone")), _clean_phone(b.get("phone2"))
            if not p1:
                return jsonify(ok=False, error="malformed", message="the first phone number is required"), 400
            bank = _bank_clean(b)
            has_bank = any(bank.values())
            status = ("VERIFIED" if _is_doctor(u) else "UNVERIFIED") if has_bank else ""
            con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, phone2, acct_name, acct_no, "
                        "ifsc, bank_branch, upi_id, bank_status, bank_verified_by, bank_verified_at, source, added_by, "
                        "updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (key, vendor, p1, p2, bank["acct_name"], bank["acct_no"], bank["ifsc"], bank["bank_branch"],
                         bank["upi_id"], status, who if status == "VERIFIED" else "", now_iso() if status == "VERIFIED" else "",
                         "server", who, now_iso()))
            _audit(con, who, "book_add", key, dict(vendor=vendor, phone=_last4(p1), phone2=_last4(p2),
                                                   bank_fields=[f for f in BANK_FIELDS if bank[f]], bank_status=status))
            _s574_change(con, who, key, "added", "", p1)
            con.commit()
            return jsonify(ok=True, vendor=vendor, bank_status=status)
        if row is None:
            return jsonify(ok=False, error="no_such_vendor", message="%s is not in the book." % (vendor or vn)), 404
        if action == "phones":
            if on:
                ps = [_s574_mobile(b.get(s)) for s in BOOK_SLOTS]
                ems = [_s574_email(b.get(e)) for e in ("email1", "email2")]
            else:
                ps, ems = [_clean_phone(b.get("phone")), _clean_phone(b.get("phone2"))], []
            if not ps[0]:
                return jsonify(ok=False, error="malformed", message="the first phone number is required"), 400
            if on:
                con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, phone3=?, phone4=?, email1=?, email2=?, source='server', "
                            "updated_at=? WHERE vendor_norm=?", tuple(ps) + tuple(ems) + (now_iso(), key))
            else:
                con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, source='server', updated_at=? WHERE vendor_norm=?",
                            (ps[0], ps[1], now_iso(), key))
            _audit(con, who, "book_phones", key, dict(vendor=row["vendor"], phone=_last4(ps[0]), phone2=_last4(ps[1]),
                                                      was=_last4(row["phone"]), was2=_last4(row["phone2"]),
                                                      **(dict(phone3=_last4(ps[2]), phone4=_last4(ps[3]), was3=_last4(row["phone3"]),
                                                              was4=_last4(row["phone4"]), emails=len([e for e in ems if e])) if on else {})))
            for i, n in enumerate(ps):
                if re.sub(r"\D", "", row[BOOK_SLOTS[i]] or "") != re.sub(r"\D", "", n or ""):
                    _s574_change(con, who, key, "phones: number %d" % (i + 1), row[BOOK_SLOTS[i]], n)
            for i, e in enumerate(ems):
                if (row["email%d" % (i + 1)] or "") != e:
                    _s574_change(con, who, key, "phones: email %d" % (i + 1))
            con.commit()
            return jsonify(ok=True)
        if action == "picks":
            if not on:
                return jsonify(ok=False, error="switch_off", message="Turn on one record per dealer first."), 409
            vals = {}
            for use in BOOK_USES:
                v = b.get("%s_pick" % use)
                if v in (None, "", 0, "0"):
                    vals[use] = None
                    continue
                try:
                    vals[use] = int(v)
                except (TypeError, ValueError):
                    vals[use] = 0
                if not 1 <= vals[use] <= 4:
                    raise ValueError("a pick is number 1, 2, 3 or 4")
            before = {use: book_number(con, key, use) for use in BOOK_USES}
            con.execute("UPDATE purchase_vendor_contact SET call_pick=?, order_pick=?, pay_pick=?, updated_at=? WHERE vendor_norm=?",
                        (vals["call"], vals["order"], vals["pay"], now_iso(), key))
            for use, word in S574_USE_WORDS:
                if row["%s_pick" % use] != vals[use]:
                    _s574_change(con, who, key, "%s: %s" % (word, ("number %d" % vals[use]) if vals[use] else "number 1"),
                                 before[use], book_number(con, key, use))
            _audit(con, who, "book_picks", key, dict(vendor=row["vendor"], **vals))
            con.commit()
            return jsonify(ok=True, saved=True)
        if action == "bank":
            bank = _bank_clean(b)
            changed = [f for f in BANK_FIELDS if (row[f] or "") != bank[f]]
            if not changed:
                return jsonify(ok=True, unchanged=True, bank_status=row["bank_status"] or "")
            # D370: a modified bank field drops back to UNVERIFIED -- unless the doctor himself saved it.
            status = "VERIFIED" if _is_doctor(u) else "UNVERIFIED"
            if not any(bank.values()):
                status = ""
            con.execute("UPDATE purchase_vendor_contact SET acct_name=?, acct_no=?, ifsc=?, bank_branch=?, upi_id=?, "
                        "bank_status=?, bank_verified_by=?, bank_verified_at=?, source='server', updated_at=? WHERE vendor_norm=?",
                        (bank["acct_name"], bank["acct_no"], bank["ifsc"], bank["bank_branch"], bank["upi_id"], status,
                         who if status == "VERIFIED" else "", now_iso() if status == "VERIFIED" else "", now_iso(), key))
            _audit(con, who, "book_bank", key, dict(vendor=row["vendor"], changed=changed, bank_status=status,
                                                    acct_last4=_last4(bank["acct_no"])))
            con.commit()
            return jsonify(ok=True, bank_status=status)
        if action == "verify":
            if not _is_doctor(u):
                return _refuse("Only the doctor verifies bank details.")
            if not any((row[f] or "") for f in BANK_FIELDS):
                return jsonify(ok=False, error="nothing_to_verify", message="No bank details on record for %s." % row["vendor"]), 400
            con.execute("UPDATE purchase_vendor_contact SET bank_status='VERIFIED', bank_verified_by=?, bank_verified_at=?, "
                        "updated_at=? WHERE vendor_norm=?", (who, now_iso(), now_iso(), key))
            _audit(con, who, "book_verify", key, dict(vendor=row["vendor"], acct_last4=_last4(row["acct_no"])))
            con.commit()
            return jsonify(ok=True, bank_status="VERIFIED")
    except ValueError as e:
        return jsonify(ok=False, error="malformed", message=str(e)), 400
    return jsonify(ok=False, error="malformed", message="action add|phones|picks|bank|verify|merge|unmerge|switch"), 400


# ---- S574: the merge (the owner's tap only; charter 10: keyed, idempotent, nothing deleted) ----------------------------------------------
def _s574_pending(con):
    """[(Marg's row, the bank sheet's row)] -- the alias pairs where both rows exist and neither is merged yet, by bill_norm."""
    out = []
    try:
        pairs = con.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias ORDER BY bill_norm").fetchall()
    except sqlite3.Error:
        return out
    for bill_norm, reg_norm in pairs:
        mb, rg = _book_row(con, bill_norm), _book_row(con, reg_norm)
        if mb and rg and bill_norm != reg_norm and not mb.get("merged_into") and not rg.get("merged_into"):
            out.append((mb, rg))
    return out


def _s574_name_options(mb, rg):
    """The names the owner may keep: Marg's name with its town dropped (the existing cutter, _acct_name_s265 -- the default), the bank
    sheet's name, Marg's name as printed."""
    out = []
    for x in (_acct_name_s265("", mb.get("vendor"), mb.get("vendor_norm")), rg.get("vendor"), mb.get("vendor")):
        x = " ".join(str(x or "").split())
        if x and x not in out:
            out.append(x)
    return out


def _s574_merge_pair(con, who, mb, rg, name):
    """One pair: the two rows as they stand into purchase_vendor_premerge first; the bank sheet's row keeps its own numbers in their
    slots and takes Marg's numbers that it lacks (by the digits) into its empty slots, up to 4; when the two first numbers differ, all
    three picks name the slot of Marg's first number (what every reader used before the merge); the name kept; Marg's row gets
    merged_into and nothing else. The register row's vendor, acct_name and bank fields are not touched. Returns the numbers left out."""
    t = now_iso()
    con.execute("INSERT INTO purchase_vendor_premerge (merged_at, merged_by, bill_norm, register_norm, bill_row_json, register_row_json) "
                "VALUES (?,?,?,?,?,?)", (t, who, mb["vendor_norm"], rg["vendor_norm"], json.dumps(mb, ensure_ascii=False),
                                         json.dumps(rg, ensure_ascii=False)))
    slots = [rg.get(s) for s in BOOK_SLOTS]
    have = {_s574_d10(x) for x in slots if _s574_d10(x)}
    extra = []
    for p in (mb.get("phone"), mb.get("phone2")):
        d = _s574_d10(p)
        if not d or d in have:
            continue
        free = [i for i, x in enumerate(slots) if not str(x or "").strip()]
        if free:
            slots[free[0]] = str(p).strip()
            have.add(d)
        else:
            extra.append(p)
    picks = (rg.get("call_pick"), rg.get("order_pick"), rg.get("pay_pick"))
    first = _s574_d10(mb.get("phone"))
    if first and first != _s574_d10(rg.get("phone")):
        k = next((i + 1 for i, x in enumerate(slots) if _s574_d10(x) == first), None)
        if k:
            picks = (k, k, k)
    con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, phone3=?, phone4=?, call_pick=?, order_pick=?, pay_pick=?, "
                "display_name=?, updated_at=? WHERE vendor_norm=?", tuple(slots) + tuple(picks) + (name, t, rg["vendor_norm"]))
    con.execute("UPDATE purchase_vendor_contact SET merged_into=? WHERE vendor_norm=?", (rg["vendor_norm"], mb["vendor_norm"]))
    for p in extra:
        _s574_change(con, who, rg["vendor_norm"], "merge: a fifth number left out (%s)" % mb["vendor"], "", p)
    _s574_change(con, who, rg["vendor_norm"], "merged")
    return extra


def _s574_merged(con):
    """The merges standing: premerge rows not undone whose Marg row is still merged into that record."""
    out = []
    try:
        rows = con.execute("SELECT id, merged_at, bill_norm, register_norm, register_row_json FROM purchase_vendor_premerge "
                           "WHERE undone_at IS NULL ORDER BY id").fetchall()
    except sqlite3.Error:
        return out
    for r in rows:
        mb = _book_row(con, r[2])
        if mb and mb.get("merged_into") == r[3]:
            out.append(dict(id=r[0], merged_at=r[1], bill_norm=r[2], register_norm=r[3], register_row_json=r[4]))
    return out


def _s574_undo_closed(con, merged):
    """True once any change line other than 'merged' stands for a merged record after its merge (rule 5: his later edits are kept)."""
    for p in merged:
        m = con.execute("SELECT MAX(id) FROM purchase_book_change WHERE vendor_norm=? AND what='merged'", (p["register_norm"],)).fetchone()
        if con.execute("SELECT 1 FROM purchase_book_change WHERE vendor_norm IN (?,?) AND id>? AND what<>'merged' LIMIT 1",
                       (p["register_norm"], p["bill_norm"], (m[0] if m and m[0] else 0))).fetchone():
            return True
    return False


def _s574_owner_act(con, who, action, b):
    """The doctor's three taps: switch (on / off), merge (all pending pairs), unmerge (every standing merge, refused once closed)."""
    if action == "switch":
        on = str(b.get("on") if b.get("on") is not None else "").strip().lower() in ("1", "true", "on")
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (BOOK_ON_KEY, "1" if on else "0", "S574: one record per dealer"))
        _s574_change(con, who, "", "one record per dealer: %s" % ("ON" if on else "OFF"))
        _audit(con, who, "book_switch", BOOK_ON_KEY, dict(on=on))
        con.commit()
        return jsonify(ok=True, on=on)
    if not book_on(con):
        return jsonify(ok=False, error="switch_off", message="Turn on one record per dealer first."), 409
    if action == "merge":
        names = b.get("names") if isinstance(b.get("names"), dict) else {}
        done, extra = [], []
        try:
            for mb, rg in _s574_pending(con):
                opts = _s574_name_options(mb, rg)
                want = " ".join(str(names.get(rg["vendor_norm"]) or "").split())
                extra += [(rg["vendor_norm"], x) for x in _s574_merge_pair(con, who, mb, rg, want if want in opts else opts[0])]
                done.append(rg["vendor_norm"])
            _audit(con, who, "book_merge", "", dict(n=len(done), records=done, left_out=len(extra)))
            con.commit()
        except sqlite3.Error:
            con.rollback()
            raise
        return jsonify(ok=True, merged=len(done), left_out=[dict(vendor_norm=k, number=_last4(x)) for k, x in extra])
    merged = _s574_merged(con)
    if not merged:
        return jsonify(ok=False, error="nothing_merged", message="Nothing is merged."), 409
    if _s574_undo_closed(con, merged):
        return jsonify(ok=False, error="undo_closed", message=S574_UNDO_CLOSED), 409
    try:
        for p in merged:
            rj = json.loads(p["register_row_json"] or "{}")
            con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, phone3=?, phone4=?, call_pick=?, order_pick=?, pay_pick=?, "
                        "display_name=?, updated_at=? WHERE vendor_norm=?",
                        tuple(rj.get(s) for s in BOOK_SLOTS) + (rj.get("call_pick"), rj.get("order_pick"), rj.get("pay_pick"),
                                                                rj.get("display_name"), now_iso(), p["register_norm"]))
            con.execute("UPDATE purchase_vendor_contact SET merged_into=NULL WHERE vendor_norm=? AND merged_into=?", (p["bill_norm"], p["register_norm"]))
            con.execute("UPDATE purchase_vendor_premerge SET undone_at=?, undone_by=? WHERE id=?", (now_iso(), who, p["id"]))
            _s574_change(con, who, p["register_norm"], "merge undone")
        _audit(con, who, "book_unmerge", "", dict(n=len(merged)))
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return jsonify(ok=True, undone=len(merged))


# ---- S574: Marg's push into the one record (switch ON) ------------------------------------------------------------------------------------
def _s574_push_one(con, name, phone):
    """True when the name has a record (it is then handled here): a number already in a slot -> only updated_at; else into the first
    empty slot ('from Marg'); all four full -> nothing written, one 'marg_extra' line per dealer and number. Never a replace, never the
    vendor's name, never a pick, never a row for a merged name. False -> no record: the caller inserts as before."""
    rec = book_record(con, name)
    if rec is None:
        return False
    key = rec["vendor_norm"]
    raw = str(phone or "").strip()
    d = _s574_d10(raw)
    if not d or d in {_s574_d10(rec.get(s)) for s in BOOK_SLOTS}:
        con.execute("UPDATE purchase_vendor_contact SET updated_at=? WHERE vendor_norm=?", (now_iso(), key))
        return True
    free = [s for s in BOOK_SLOTS if not str(rec.get(s) or "").strip()]
    if free:
        con.execute("UPDATE purchase_vendor_contact SET %s=?, updated_at=? WHERE vendor_norm=?" % free[0], (raw, now_iso(), key))
        _s574_change(con, "push_purchases", key, "from Marg", "", raw)
        return True
    if not con.execute("SELECT 1 FROM purchase_book_change WHERE vendor_norm=? AND what='marg_extra' AND new4=?", (key, _s574_4(raw))).fetchone():
        _s574_change(con, "push_purchases", key, "marg_extra", "", raw)
    return True


def _s574_marg_extra(con):
    """[(vendor_norm, last-4)] -- Marg's numbers the full records could not take, while no later number edit stands for that dealer."""
    try:
        return [(r[0], r[1]) for r in con.execute(
            "SELECT c.vendor_norm, c.new4 FROM purchase_book_change c WHERE c.what='marg_extra' AND NOT EXISTS (SELECT 1 FROM "
            "purchase_book_change p WHERE p.vendor_norm=c.vendor_norm AND p.what LIKE 'phones%' AND p.id>c.id) ORDER BY c.id")]
    except sqlite3.Error:
        return []


# ---- the phone book page's parts (one copy each: the OFF page and the one-record page both draw them) --------------------------------------
def _book_src_txt(r):
    return ("added by " + _esc(r["added_by"]) if (r["added_by"] and r["added_by"] != "neft_import_s225") else
            "from the NEFT records (04-Sep)" if (r["source"] or "") == "neft_import" else
            "from Marg / manojz" if (r["source"] or "manojz") != "server" else "edited here")


def _book_bank_cell(r, i, doctor):
    """The bank block of a row, as the page has drawn it since S225 (rev 12), with its Add/Edit and Verify."""
    st = r["bank_status"] or ""
    if st == "VERIFIED":
        chip = '<span class="chip ok">VERIFIED</span> <small class="muted">%s</small>' % _esc(_hhmm_ist_full(r["bank_verified_at"] or ""))
    elif st == "UNVERIFIED":
        chip = ('<span class="chip warn">UNVERIFIED</span> ' +
                ('<button class="sm p noprint" onclick="bookVerify(%d)">Verify</button>' % i if doctor else
                 '<small class="muted">waits for Dr Manoj</small>'))
    else:
        chip = '<small class="muted">no bank details</small>'
    has_bank = any((r[f] or "") for f in BANK_FIELDS)
    bank_lines = []
    if has_bank:
        if r["acct_name"]:
            bank_lines.append('<div><small class="muted">Account name</small> %s</div>' % _esc(r["acct_name"]))
        if r["acct_no"]:
            bank_lines.append('<div><small class="muted">A/c no</small> <b style="font-variant-numeric:tabular-nums;letter-spacing:.04em">%s</b></div>' % _esc(r["acct_no"]))
        if r["ifsc"]:
            bname = _bank_name(r["ifsc"])
            bank_lines.append('<div><small class="muted">IFSC</small> <b>%s</b>%s</div>'
                              % (_esc(r["ifsc"]), (" · " + _esc(bname)) if bname else ""))
        if r["bank_branch"]:
            bank_lines.append('<div><small class="muted">Bank / branch</small> %s</div>' % _esc(r["bank_branch"]))
        if r["upi_id"]:
            bank_lines.append('<div><small class="muted">UPI</small> %s</div>' % _esc(r["upi_id"]))
    return ('%s%s <button class="sm noprint" onclick="bookForm(%d,\'bank\')">%s bank details</button>'
            '<div class="inl noprint" id="inl-bank-%d" hidden></div><div class="inl noprint" id="inl-verify-%d" hidden></div>'
            % ("".join(bank_lines), chip, i, "edit" if has_bank else "add", i, i))


def _book_add_form(doctor):
    return ('<div class="card" id="addform"><h3>Add a new stockist</h3><div class="grid">'
            '<div><label>Name (as Marg prints it)</label><input name="vendor"></div>'
            '<div><label>Phone</label><input name="phone" inputmode="numeric"></div>'
            '<div><label>Second phone (optional)</label><input name="phone2" inputmode="numeric"></div>'
            '<div><label>Account name</label><input name="acct_name"></div>'
            '<div><label>Account number</label><input name="acct_no" inputmode="numeric"></div>'
            '<div><label>IFSC</label><input name="ifsc"></div>'
            '<div><label>Bank and branch</label><input name="bank_branch"></div>'
            '<div><label>UPI id (optional)</label><input name="upi_id"></div></div>'
            '<div class="row" style="margin-top:8px"><button class="p" onclick="bookAdd()">Save new stockist</button> '
            '<span class="muted">Bank details %s</span><span class="bad" id="msg-add" hidden></span></div></div>'
            % ("you save are VERIFIED by that act." if doctor else "wait UNVERIFIED until Dr Manoj verifies them."))


def _s574_switch_line(con):
    on = book_on(con)
    return ('<div class="note noprint" id="s574switch"><b>One record per dealer: %s</b> — <button class="sm%s" onclick="s574Switch(%d)">%s</button>'
            '<span class="bad" id="msg-switch" hidden></span></div>' % ("ON" if on else "OFF", "" if on else " p", 0 if on else 1,
                                                                       "Turn off" if on else "Turn on"))


S574_FIND_JS = r"""
function s574Find(){
  const q = (document.getElementById('s574q').value || '').trim().toUpperCase();
  for (const tr of document.querySelectorAll('#s574book tr[data-q]')) tr.hidden = !!q && tr.dataset.q.indexOf(q) < 0;
}
"""

S574_JS = S574_FIND_JS + r"""
async function s574Post(body, msgEl, reload){
  if (msgEl){ msgEl.className = 'muted'; msgEl.textContent = 'saving...'; msgEl.hidden = false; }
  const r = await fetch(P + '/api/book', {method:'POST', headers:{'Content-Type':'application/json'},
                                          credentials:'same-origin', body: JSON.stringify(body||{})});
  let j = {}; try { j = await r.json(); } catch(e) {}
  if (!r.ok || j.ok === false){
    if (msgEl){ msgEl.className = 'bad'; msgEl.textContent = j.message || j.error || ('HTTP ' + r.status); msgEl.hidden = false; }
    return null;
  }
  if (reload) location.reload();
  return j;
}
function s574Switch(on){ s574Post({action:'switch', on:on}, document.getElementById('msg-switch'), true); }
function s574Merge(){
  const names = {};
  for (const s of document.querySelectorAll('#s574merge select[data-reg]')) names[s.dataset.reg] = s.value;
  s574Post({action:'merge', names:names}, document.getElementById('msg-merge'), true);
}
function s574Undo(){ s574Post({action:'unmerge'}, document.getElementById('msg-undo'), true); }
async function s574Picks(i){
  const b = {action:'picks', vendor_norm:BOOKV[i]};
  for (const u of ['call','order','pay']){ const s = document.getElementById('pk-' + u + '-' + i); b[u + '_pick'] = s ? s.value : ''; }
  const m = document.getElementById('msg-pk-' + i);
  const j = await s574Post(b, m, false);
  if (j && m){ m.className = 'ok'; m.textContent = '✓ Saved'; m.hidden = false; }
}
function s574Edit(i){
  const d = document.getElementById('inl-s574-' + i); if (!d) return;
  if (!d.hidden){ d.hidden = true; d.innerHTML = ''; return; }
  const b = BOOK[BOOKV[i]] || {};
  d.innerHTML = '<div class="grid">' + bookField('Number 1 (10 digits)', 'phone', b.phone, 'numeric') +
      bookField('Number 2 (blank for none)', 'phone2', b.phone2, 'numeric') + bookField('Number 3 (blank for none)', 'phone3', b.phone3, 'numeric') +
      bookField('Number 4 (blank for none)', 'phone4', b.phone4, 'numeric') + bookField('Email 1 (blank for none)', 'email1', b.email1, 'email') +
      bookField('Email 2 (blank for none)', 'email2', b.email2, 'email') + '</div><div class="row" style="margin-top:8px">' +
      '<button class="p sm" onclick="s574Save(' + i + ')">Save</button><button class="sm" onclick="s574Edit(' + i + ')">Cancel</button>' +
      '<span class="bad" id="msg-s574-' + i + '" hidden></span></div>';
  d.hidden = false;
  const first = d.querySelector('input'); if (first) first.focus();
}
function s574Save(i){
  const d = document.getElementById('inl-s574-' + i); const m = document.getElementById('msg-s574-' + i);
  const b = {action:'phones', vendor_norm:BOOKV[i]};
  for (const el of d.querySelectorAll('input')) b[el.name] = el.value.trim();
  for (const k of ['phone','phone2','phone3','phone4']){
    const v = (b[k] || '').replace(/\D/g, '').replace(/^91(?=\d{10}$)/, '').replace(/^0(?=\d{10}$)/, '');
    if (v && !/^[6-9]\d{9}$/.test(v)){ m.textContent = 'A mobile number is 10 digits starting 6, 7, 8 or 9.'; m.hidden = false; return; }
  }
  for (const k of ['email1','email2']){
    const v = b[k] || '';
    if (v && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)){ m.textContent = 'An email has one @ and a dot after it.'; m.hidden = false; return; }
  }
  if (!b.phone){ m.textContent = 'Number 1 is required.'; m.hidden = false; return; }
  s574Post(b, m, true);
}
"""


def _s574_page(con, u, doctor):
    """S574 -- the phone book, one record per dealer (switch ON; mock-up v2 screen 2, in the live page's look). The doctor: everything;
    Shavez: the book to read and the bank details' Add/Edit as before; Darpan: the book to read. The screen follows the door (rule 13)."""
    rows = _book_rows(con)
    if not _s452_may_advice(con, u):                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
    also = {}
    for r in rows:
        if r.get("merged_into"):
            also.setdefault(r["merged_into"], []).append(r["vendor"])
    live = sorted((r for r in rows if not r.get("merged_into")), key=lambda r: (r.get("display_name") or r["vendor"] or "").upper())
    keys = [r["vendor_norm"] for r in live]
    names = {r["vendor_norm"]: (r.get("display_name") or r["vendor"]) for r in rows}
    book_json = {r["vendor_norm"]: dict(phone=r["phone"] or "", phone2=r["phone2"] or "", phone3=r.get("phone3") or "", phone4=r.get("phone4") or "",
                                        email1=r.get("email1") or "", email2=r.get("email2") or "", acct_name=r["acct_name"] or "",
                                        acct_no=r["acct_no"] or "", ifsc=r["ifsc"] or "", bank_branch=r["bank_branch"] or "",
                                        upi_id=r["upi_id"] or "") for r in live}
    trs = []
    for i, r in enumerate(live):
        name = r.get("display_name") or r["vendor"]
        others = []
        for x in ([r["vendor"]] if (r.get("display_name") and r["display_name"] != r["vendor"]) else []) + also.get(r["vendor_norm"], []):
            if x and x not in others:
                others.append(x)
        nums = book_numbers(dict(r, _s574_on=True))
        if nums:
            ph = " · ".join('<small class="muted">%d</small> <a href="tel:%s">%s</a>' % (s, _esc(n), _esc(n)) for s, n in nums)
        else:
            ph = '<span class="warn">no number yet</span>'
        em = " · ".join(_esc(r.get(e)) for e in ("email1", "email2") if r.get(e))
        picks = ""
        if doctor and len(nums) >= 2:
            sel = []
            for use, word in S574_USE_WORDS:
                cur = _book_pick(r, use)
                opts = ['<option value=""%s>Number 1</option>' % ("" if cur in dict(nums) else " selected")]
                opts += ['<option value="%d"%s>Number %d · …%s</option>' % (s, " selected" if cur == s else "", s, _esc(_s574_4(n))) for s, n in nums]
                sel.append('<label><small class="muted">%s</small> <select id="pk-%s-%d" onchange="s574Picks(%d)">%s</select></label>'
                           % (word, use, i, i, "".join(opts)))
            picks = ('<div class="row noprint" style="margin-top:6px">%s<span class="ok" id="msg-pk-%d" hidden></span></div>' % (" ".join(sel), i))
        elif doctor:
            picks = '<div><small class="muted">Calls · Order WhatsApp · Payment msg: Number 1</small></div>'
        edit = ('<br><button class="sm noprint" onclick="s574Edit(%d)">Edit</button><div class="inl noprint" id="inl-s574-%d" hidden></div>'
                % (i, i)) if doctor else ""
        q = " ".join([name, r["vendor"] or ""] + others).upper()
        trs.append('<tr data-q="%s"><td><b>%s</b>%s<br><small class="muted">%s</small></td><td>%s%s%s%s</td><td>%s</td></tr>'
                   % (_esc(q), _esc(name), ('<br><small class="muted">also: %s</small>' % _esc(", ".join(others))) if others else "",
                      _book_src_txt(r), ph, ('<br><small class="muted">%s</small>' % em) if em else "", picks, edit, _book_bank_cell(r, i, doctor)))
    head = []
    if doctor:
        head.append(_s574_switch_line(con))
        pend = _s574_pending(con)
        if pend:
            prow = []
            for mb, rg in pend:
                opts = _s574_name_options(mb, rg)
                first = _s574_d10(mb.get("phone"))
                note = ""
                if first and first != _s574_d10(rg.get("phone")):
                    k = next((j + 1 for j, s in enumerate(BOOK_SLOTS) if _s574_d10(rg.get(s)) == first), None)
                    note = ('<div class="warn"><small>Numbers differ: Marg\'s …%s is %s of the bank sheet\'s record. Calls, Order WhatsApp and '
                            'Payment msg will all use it, as they do today.</small></div>'
                            % (_esc(_s574_4(first)), ("number %d" % k) if k else "added as a number"))
                prow.append('<tr><td>%s<br><small class="muted">%s</small></td><td>%s<br><small class="muted">%s</small></td>'
                            '<td><select data-reg="%s">%s</select>%s</td></tr>'
                            % (_esc(mb["vendor"]), _esc(" · ".join("…" + _s574_4(x) for x in (mb.get("phone"), mb.get("phone2")) if x) or "no number"),
                               _esc(rg["vendor"]), _esc(" · ".join("…" + _s574_4(rg.get(s)) for s in BOOK_SLOTS if rg.get(s)) or "no number"),
                               _esc(rg["vendor_norm"]), "".join('<option%s>%s</option>' % (" selected" if j == 0 else "", _esc(x)) for j, x in enumerate(opts)),
                               note))
            head.append('<div class="card noprint" id="s574merge"><h2>%d dealers are in the book twice</h2><div class="muted">Marg\'s name on the '
                        'left, the bank sheet\'s name on the right (you linked them on 14-Sep). <b>Merge all</b> joins each pair into one record: '
                        'the bank details are not touched, both rows\' numbers are kept (up to 4), and calls, WhatsApp orders and payment messages '
                        'go to the numbers they go to today. It can be undone until a number is changed.</div><div class="scroll"><table><tr>'
                        '<th>Marg\'s name</th><th>Bank sheet\'s name</th><th>Name to keep</th></tr>%s</table></div><div class="row" '
                        'style="margin-top:8px"><button class="p" onclick="s574Merge()">Merge all %d</button><span class="bad" id="msg-merge" hidden>'
                        '</span></div></div>' % (len(pend), "".join(prow), len(pend)))
        merged = _s574_merged(con)
        if merged:
            when = _hhmm_ist_full(merged[-1]["merged_at"] or "")
            if _s574_undo_closed(con, merged):
                head.append('<div class="muted" id="s574undo">%d dealers joined into one record (%s). %s</div>' % (len(merged), _esc(when), S574_UNDO_CLOSED))
            else:
                head.append('<div class="muted noprint" id="s574undo">%d dealers joined into one record (%s). <a href="#" onclick="s574Undo();return false">'
                            'Undo the merge</a> <span class="bad" id="msg-undo" hidden></span></div>' % (len(merged), _esc(when)))
        for vn, n4 in _s574_marg_extra(con):
            head.append('<div class="note" data-s574="marg_extra">Marg has another number for %s (…%s)</div>' % (_esc(names.get(vn, vn)), _esc(n4)))
    try:
        ch = con.execute("SELECT at, who, vendor_norm, what, old4, new4 FROM purchase_book_change ORDER BY id DESC LIMIT 100").fetchall()
    except sqlite3.Error:
        ch = []
    chtr = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                   % (_esc(_hhmm_ist_full(c[0] or "")), _esc(c[1]), _esc(names.get(c[2], c[2]) if c[2] else "—"), _esc(c[3]),
                      _esc(("%s → %s" % (("…" + c[4]) if c[4] else "—", ("…" + c[5]) if c[5] else "—")) if (c[4] or c[5]) else ""))
                   for c in ch)
    body = ('<h1>Stockist phone book</h1><div class="muted">One record per dealer: up to 4 mobile numbers and 2 emails each. %s Bank '
            'details stay on this server only and are shown in full here because this page is the source for the bulk NEFT file — it opens '
            'for Dr Manoj, Darpan and Shavez only. A bank detail added or changed by anyone but Dr Manoj is <b>UNVERIFIED</b> until he taps '
            'Verify; payments will refuse an unverified account.</div>%s'
            '<style>.inl{margin-top:8px;padding:10px;border:1px solid var(--line);border-radius:8px;background:#f6f8fb}'
            '.inl label{display:block;font-size:12.5px;color:var(--muted)}.inl input{width:100%%}</style>'
            '<div class="card noprint"><input id="s574q" placeholder="Search a dealer" oninput="s574Find()" style="width:100%%"></div>'
            '<div class="card"><div class="scroll"><table id="s574book"><tr><th>Dealer</th><th>Numbers</th><th>Bank</th></tr>%s</table></div></div>%s'
            '<div class="card" id="s574changes"><h2>Changes</h2><div class="scroll"><table><tr><th>When</th><th>Who</th><th>Dealer</th><th>What</th>'
            '<th>Number</th></tr>%s</table></div></div>'
            % ("Calls, Order WhatsApp and Payment msg use number 1 unless you pick another; the emails are kept for reference (nothing sends email)."
               if doctor else "Numbers are changed only by Dr Manoj.", "".join(head),
               "".join(trs) or '<tr><td colspan="3" class="muted">nobody in the book yet</td></tr>', _book_add_form(doctor) if doctor else "",
               chtr or '<tr><td colspan="5" class="muted">no change yet</td></tr>'))
    return _page("Stockist phone book", body, BOOK_JS + (S574_JS if doctor else S574_FIND_JS)
                 + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(keys)))


'''

PA8_OLD = '    doctor = _is_doctor(u)\n    rows = _book_rows(con)\n'
PA8_NEW = ('    doctor = _is_doctor(u)\n'
           '    if book_on(con):                                            # S574: one record per dealer (the owner\'s switch)\n'
           '        return _s574_page(con, u, doctor)\n'
           '    rows = _book_rows(con)\n')

PA9_START = '    for i, r in enumerate(rows):\n        st = r["bank_status"] or ""\n'
PA9_END = '''    add = ('<div class="card" id="addform"><h3>Add a new stockist</h3><div class="grid">'\n'''
PA9_NEW = r'''    for i, r in enumerate(rows):
        src_txt = _book_src_txt(r)
        if r["phone"]:
            phones = '<a href="tel:%s">%s</a>%s' % (_esc(r["phone"]), _esc(r["phone"]),
                                                   (' · <a href="tel:%s">%s</a>' % (_esc(r["phone2"]), _esc(r["phone2"]))) if r["phone2"] else "")
        else:
            n_nophone += 1
            phones = '<span class="warn">no number yet</span>'
        numbtn = ('<br><button class="sm noprint" onclick="bookForm(%d,\'phones\')">%s numbers</button>'      # S574: the door is the doctor's
                  '<div class="inl noprint" id="inl-phones-%d" hidden></div>' % (i, "edit" if r["phone"] else "add", i)) if doctor else ""
        trs.append('<tr><td><b>%s</b><br><small class="muted">%s</small></td><td>%s%s</td><td>%s</td></tr>'
                   % (_esc(r["vendor"]), src_txt, phones, numbtn, _book_bank_cell(r, i, doctor)))
'''

PA10_START = PA9_END
PA10_END = '''    nophone = ('<div class="note noprint"><b>%d stockist%s without a phone number yet</b>'''
PA10_NEW = '    add = _book_add_form(doctor) if doctor else ""             # S574: adding a supplier is the doctor\'s (the door refuses anyone else)\n'

PA11_OLD = '               if n_nophone else "")\n'
PA11_NEW = '               if (n_nophone and doctor) else "")                    # S574: it asks for a tap only the doctor has\n'

PA12_OLD = '    return _page("Stockist phone book", body, BOOK_JS + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(vendors)))\n'
PA12_NEW = ('    if doctor:                                                  # S574: the doctor\'s one line -- One record per dealer: OFF -- Turn on\n'
            '        body = _s574_switch_line(con) + body\n'
            '    return _page("Stockist phone book", body, BOOK_JS + (S574_JS if doctor else "") + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(vendors)))\n')

PA13_OLD = '''    n = 0
    for name, phone in pairs.items():
        name = str(name or "").strip()
        if not name:
            continue
        # rev 7: a number edited in the phone book (source='server') is never overwritten by the push.
'''
PA13_NEW = '''    n = 0
    s574_on = book_on(con)                                     # S574: switch ON -> into the one record, never a replace; OFF -> as before
    for name, phone in pairs.items():
        name = str(name or "").strip()
        if not name:
            continue
        if s574_on and _s574_push_one(con, name, phone):
            n += 1
            continue
        # rev 7: a number edited in the phone book (source='server') is never overwritten by the push.
'''

# ============================================================================================================================ order_sheet
OS1_START = 'def _phones(con, vendor):\n'
OS1_END = 'def make_order(con, who, vendor, lines, status, via, created_at=None, sheet_id=None, ext_ref="", section="Medicines", note=""):\n'
OS1_NEW = r'''def book_card(con, vendor):
    """S574 (charter 2): the numbers a sender's page and paper show, from the phone book's one reader (purchase_app.book_number /
    book_shown) -- (call, wa, shown, on): call rings (Call karo, tel:), wa is where a WhatsApp order goes, shown is printed under the name,
    on = the switch purchase.book_one_record.on. Switch OFF: call = wa = number 1, shown = numbers 1-2 -- as _phones gave them."""
    pa = _pa()
    try:
        return pa.book_number(con, vendor, "call"), pa.book_number(con, vendor, "order"), pa.book_shown(con, vendor), pa.book_on(con)
    except sqlite3.Error:
        return "", "", [], False


'''
OS2_OLD = '''        p1, p2 = _phones(con, c["vendor"])
        c["has_phone"] = bool(pa._wa_digits(p1))
        c["phone"], c["phone2"] = p1, p2
'''
OS2_NEW = '''        call, wa, shown, on = book_card(con, c["vendor"])        # S574: the one reader
        c["has_phone"] = bool(pa._wa_digits(wa))
        c["phone"], c["wa"], c["shown"], c["book_on"] = call, wa, shown, on
'''
OS3_OLD = '    to = pa._wa_digits(_phones(con, e["vendor"])[0])\n'
OS3_NEW = '    to = pa._wa_digits(pa.book_number(con, e["vendor"], "order"))     # S574: the Order WhatsApp number\n'
OS4_OLD = '    """[{sn, vendor, lines, state, draft, msg_state, called, has_phone, phone, phone2, sources}] -- one card per supplier still to be ordered.\n'
OS4_NEW = ('    """[{sn, vendor, lines, state, draft, msg_state, called, has_phone, phone, wa, shown, book_on, sources}] -- one card per supplier still to be\n'
           '    ordered (S574: phone = the Calls number, wa = the Order WhatsApp number, shown = the numbers printed, from book_card).\n')

# ============================================================================================================================ order_sheet_pdf
SP1_OLD = '''        p1, p2 = OS._phones(con, b["name"])
        blocks.append(dict(name=b["name"], phones=[x for x in (p1, p2) if x], only_old=False, ticks=ticks, rows=b["rows"]))
'''
SP1_NEW = '''        blocks.append(dict(name=b["name"], phones=OS.book_card(con, b["name"])[2], only_old=False, ticks=ticks, rows=b["rows"]))   # S574
'''
SP2_OLD = '        p1, p2 = OS._phones(con, ls[0]["supplier"])\n'
SP2_NEW = '        shown = OS.book_card(con, ls[0]["supplier"])[2]          # S574: the one reader (OFF: numbers 1-2, as before)\n'
SP3_OLD = '        blocks.append(dict(name=ls[0]["supplier"], phones=[x for x in (p1, p2) if x], only_old=True,'
SP3_NEW = '        blocks.append(dict(name=ls[0]["supplier"], phones=shown, only_old=True,'

# ============================================================================================================================ porders_s454
PS1_OLD = '    "nophone_l": ("Is supplier ka phone number yahan nahi hai", "This supplier has no phone number here"),\n'
PS1_NEW = ('    "nophone_l": ("Is supplier ka phone number yahan nahi hai", "This supplier has no phone number here"),\n'
           '    "nonum": ("Number nahi hai — Dr sahab ko dijiye", "No number — give it to Dr Manoj"),     # S574 (switch ON): for nophone / nophone_l\n'
           '    "num_call": ("Call: %s", "Call: %s"), "num_wa": ("WhatsApp: %s", "WhatsApp: %s"),            # S574 (switch ON): under the name\n')
PS2_OLD = '        sub, am = sub + " · " + L(en, "nophone"), True\n'
PS2_NEW = '        sub, am = sub + " · " + L(en, "nonum" if e.get("book_on") else "nophone"), True      # S574\n'
PS3_OLD = 'sent_at=sent_at, by=o.get("created_by") or "", phone=OS._phones(con, o["vendor"])[0]))\n'
PS3_NEW = 'sent_at=sent_at, by=o.get("created_by") or "", phone=_pa().book_number(con, o["vendor"], "call")))   # S574: the Calls number\n'
PS4_OLD = '''            nums = "".join('<div class="num">%s</div>' % esc(x) for x in (e["phone"], e["phone2"]) if x)\n'''
PS4_NEW = '''            if e.get("book_on"):                              # S574: the Calls number and the Order WhatsApp number, to read only
                nums = ('<div class="num" id="numcall">%s</div><div class="num" id="numwa">%s</div>'
                        % (esc(L(en, "num_call", e["phone"])), esc(L(en, "num_wa", e["wa"]))))
            else:
                nums = "".join('<div class="num">%s</div>' % esc(x) for x in e["shown"])
'''
PS5_OLD = '''            h.append('<div class="mut" id="nophone">%s</div>' % L(en, "nophone_l"))\n'''
PS5_NEW = '''            h.append('<div class="mut" id="nophone">%s</div>' % L(en, "nonum" if e.get("book_on") else "nophone_l"))   # S574\n'''

# ============================================================================================================================ supplier_msg
SM1_OLD = '        return pa._wa_digits(pa._phone_for(con, vendor))\n'
SM1_NEW = '        return pa._wa_digits(pa.book_number(con, vendor, "pay"))     # S574: the Payment message number\n'

EDITS = {
    "purchase_app.py": [("PA1 the one reader", "region", PA1_START, PA1_END, PA1_NEW),
                        ("PA2 orders plan tel:", "exact", PA2_OLD, None, PA2_NEW),
                        ("PA3 order book tel:", "exact", PA3_OLD, None, PA3_NEW),
                        ("PA4 /page/staff call buttons", "exact", PA4_OLD, None, PA4_NEW),
                        ("PA5 _ensure_book", "region", PA5_START, PA5_END, PA5_NEW),
                        ("PA6 _phones_for retired", "region", PA6_START, PA6_END, PA6_NEW),
                        ("PA7 _book_save + the merge + the page", "region", PA7_START, PA7_END, PA7_NEW),
                        ("PA8 /page/book ON", "exact", PA8_OLD, None, PA8_NEW),
                        ("PA9 /page/book OFF rows", "region", PA9_START, PA9_END, PA9_NEW),
                        ("PA10 /page/book OFF add form", "region", PA10_START, PA10_END, PA10_NEW),
                        ("PA11 /page/book OFF no-number note", "exact", PA11_OLD, None, PA11_NEW),
                        ("PA12 /page/book OFF switch line", "exact", PA12_OLD, None, PA12_NEW),
                        ("PA13 Marg's push", "exact", PA13_OLD, None, PA13_NEW)],
    "order_sheet.py": [("OS1 book_card (was _phones)", "region", OS1_START, OS1_END, OS1_NEW),
                       ("OS2 the cards' numbers", "exact", OS2_OLD, None, OS2_NEW),
                       ("OS3 the WhatsApp queue", "exact", OS3_OLD, None, OS3_NEW),
                       ("OS4 entries docstring", "exact", OS4_OLD, None, OS4_NEW)],
    "order_sheet_pdf.py": [("SP1 band numbers", "exact", SP1_OLD, None, SP1_NEW),
                           ("SP2 old-only band numbers", "exact", SP2_OLD, None, SP2_NEW),
                           ("SP3 old-only band numbers", "exact", SP3_OLD, None, SP3_NEW)],
    "porders_s454.py": [("PS1 words", "exact", PS1_OLD, None, PS1_NEW),
                        ("PS2 card no-number word", "exact", PS2_OLD, None, PS2_NEW),
                        ("PS3 done list Call", "exact", PS3_OLD, None, PS3_NEW),
                        ("PS4 supplier page numbers", "exact", PS4_OLD, None, PS4_NEW),
                        ("PS5 supplier page no-number", "exact", PS5_OLD, None, PS5_NEW)],
    "supplier_msg.py": [("SM1 _digits pay", "exact", SM1_OLD, None, SM1_NEW)],
}


def apply(name, t, edits):
    for label, kind, a, z, new in edits:
        na = t.count(a)
        if na != 1:
            return None, "anchor %s (%s) occurs %d times in %s (must be exactly 1)" % (label, "start" if kind == "region" else "text", na, name)
        if kind == "exact":
            t = t.replace(a, new, 1)
        else:
            nz = t.count(z)
            i = t.index(a)
            if nz != 1 or t.index(z) <= i:
                return None, "anchor %s (end) occurs %d times in %s or before its start" % (label, nz, name)
            t = t[:i] + new + t[t.index(z):]
        print("  edit %-40s anchored once, applied" % label)
    return t, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for name, edits in EDITS.items():
        raw = open(os.path.join(a.fin, name), "rb").read()
        m = hashlib.md5(raw).hexdigest()
        if m != FROM[name]:
            print("STOP: %s is %s, not its FROM pin %s -- nothing built" % (name, m, FROM[name]))
            return 2
        print("%s at its FROM pin %s" % (name, m))
        t, err = apply(name, raw.decode("utf-8"), edits)
        if err:
            print("STOP: " + err + " -- nothing built")
            return 2
        built[name] = t.encode("utf-8")
    os.makedirs(a.out, exist_ok=True)
    for name, data in built.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(data)
        print("built %s md5 %s (FROM %s)" % (name, hashlib.md5(data).hexdigest(), FROM[name]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
