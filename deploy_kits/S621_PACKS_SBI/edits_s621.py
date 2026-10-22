#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s621.py -- kit S621 (session S336, 22-Oct-2026, D754): exact, counted edits on two live files.
    python3 edits_s621.py py   LIVE OUT [KIT]     /root/finance/packs.py   e46264b8 -> the S621 file
    python3 edits_s621.py html LIVE OUT [KIT]     /root/finance/packs.html 49906969 -> the S621 file
(exit 0 only if every anchor occurs exactly once and OUT = KIT)

THE OWNER, 22-Oct-2026 08:09 IST (D754): "The SBI accounts are savings account for myself, Dr. Bhavna, and for HUF. There
are two loan accounts running, one in my account and another in Dr. Bhavna's account. Then there are two PPF accounts in
State Bank ... I need to manually download the statements from time to time, and the statements come with a password ...
They are not named properly, so I had to rename them ... I need the system to check these, incorporate these, and make a
provision for these in future packs."  His board note: SBI quarterly, PPF half-yearly.

  * SEVEN SBI SLOTS: three savings, two loans, two PPF -- each with its own cadence (savings and loans every quarter, the PPF
    every half-year of the financial year). A cadence slot is a pack row only in the month that ends its period (Jun, Sep,
    Dec, Mar; the PPF Sep and Mar) and needs ONE statement covering the whole period; it is not asked for in other months.
  * SBI's statements are read by their own head: the bank ('State Bank of India' / its IFS code), the holder from the
    'Account Name' line (Bhavna is Bhawna), the kind (PPF / loan / savings), the account tail and the period, in the date
    forms SBI prints. The file is filed as arrived (no line reading -- the accountants take the PDF).
  * A PASSWORD BOX per SBI account on the Statement passwords card (the shelf opens the PDF itself, as for Yes Bank).
  * 'ADD STATEMENTS' on the shelf: the owner picks one or several PDFs he downloaded (PC or phone, any name); each is
    kept, opened with the stored password and filed by its own content; the answer says where each went.
  * The statement road (the Gmail relay's watch) leaves the downloaded-by-hand accounts and the uploads out of its count.
No password, no account number beyond a tail, anywhere in either file.
"""
import hashlib
import sys

SBI_SLOTS = '''    ("card_icici_coral",  "ICICI", "ICICI Coral (card)",                       "card",    "CORAL",                        0),
    # S621 (D754): the SBI papers the owner downloads himself -- every quarter (savings, loans) or every half-year (PPF)
    ("sbi_sav_manoj",    "SBI",   "Dr Manoj Agarwal (SBI savings)",            "savings", "MANOJ AGARWAL",                0),
    ("sbi_sav_bhawna",   "SBI",   "Dr Bhawna Agarwal (SBI savings)",           "savings", "BHAWNA AGARWAL",               0),
    ("sbi_sav_huf",      "SBI",   "Manoj Kumar Agarwal HUF (SBI savings)",     "savings", "MANOJ KUMAR AGARWAL HUF",      0),
    ("sbi_loan_manoj",   "SBI",   "Dr Manoj Agarwal (SBI loan)",               "savings", "MANOJ AGARWAL",                0),
    ("sbi_loan_bhawna",  "SBI",   "Dr Bhawna Agarwal (SBI loan)",              "savings", "BHAWNA AGARWAL",               0),
    ("sbi_ppf_manoj",    "SBI",   "Dr Manoj Agarwal (SBI PPF)",                "savings", "MANOJ AGARWAL",                0),
    ("sbi_ppf_bhawna",   "SBI",   "Dr Bhawna Agarwal (SBI PPF)",               "savings", "BHAWNA AGARWAL",               0),
]
# S621 (D754): a slot's cadence in months (1 = every month, the default): it is a pack row only in the month that ends its period
SLOT_EVERY = {"sbi_sav_manoj": 3, "sbi_sav_bhawna": 3, "sbi_sav_huf": 3, "sbi_loan_manoj": 3, "sbi_loan_bhawna": 3,
              "sbi_ppf_manoj": 6, "sbi_ppf_bhawna": 6}
# S621: what each SBI slot holds (the table's kind stays 'savings' -- stmt_slot's CHECK allows current/savings/card only);
# an SBI statement's own head says savings / loan / ppf, and only a slot of that type may take it
SLOT_TYPE = {"sbi_sav_manoj": "savings", "sbi_sav_bhawna": "savings", "sbi_sav_huf": "savings", "sbi_loan_manoj": "loan",
             "sbi_loan_bhawna": "loan", "sbi_ppf_manoj": "ppf", "sbi_ppf_bhawna": "ppf"}
MANUAL_BANKS = ("SBI",)                     # S621: the banks whose statements the owner downloads and adds himself (no mail road)
UPLOAD_MAX_BYTES = 12 * 1024 * 1024         # S621: one added statement at most (the record doors' 12 MB)
UPLOAD_MAX_FILES = 20
'''

SBI_FUNCS = '''

# ---------------------------------------------------------------- S621 (D754): SBI, read by its own head
_SBI_D = r"(\\d{1,2}[\\s\\-/.](?:\\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)[\\s\\-/.,]*\\d{2,4})"
_SBI_PERIOD = re.compile(r"(?i)(?:from|period)\\s*(?:date)?\\s*[:\\-]?\\s*" + _SBI_D + r"\\s*(?:to|till|upto|-|\\u2013)\\s*(?:date)?\\s*[:\\-]?\\s*" + _SBI_D)
_SBI_NAME = re.compile(r"(?im)^\\s*(?:account\\s+holder(?:'s)?\\s+name|account\\s+name|customer\\s+name|name\\s+of\\s+(?:the\\s+)?(?:account\\s+)?holder|name)\\s*[:\\-]\\s*(.+?)\\s*$")


def _sbi_date(s):
    s = " ".join(str(s or "").replace(",", " ").split())
    for fmt in ("%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %m %Y", "%d-%b-%y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return dt.datetime.strptime(s.replace(" - ", "-"), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _sbi_fold(s):
    """Bhavna is Bhawna: the slot words and the bank's spelling meet."""
    return re.sub(r"\\bBHAVNA\\b", "BHAWNA", str(s or "").upper())


def sbi_ident(text, head):
    """S621 (D754): an SBI statement's head -> the holder (its 'Account Name' line), the kind, the period. Never raises."""
    out = dict(kind="", holder="", period_from=None, period_to=None)
    try:
        hup = " ".join(head.upper().split())
        if "PUBLIC PROVIDENT" in hup or re.search(r"\\bPPF\\b", hup):
            out["kind"] = "ppf"
        elif "LOAN" in hup:
            out["kind"] = "loan"
        else:
            out["kind"] = "savings"
        m = _SBI_NAME.search(head)
        if m:
            nm = re.split(r"\\s{3,}", m.group(1).strip())[0]
            out["holder"] = _sbi_fold(nm)
        m = _SBI_PERIOD.search(text)
        if m:
            out["period_from"], out["period_to"] = _sbi_date(m.group(1)), _sbi_date(m.group(2))
    except Exception:                                    # noqa: BLE001
        pass
    return out


def identify_text(text):'''

IDENT_RETURN = '''    sbi_type = ""
    if bank == "SBI":                                                 # S621 (D754): SBI's own head
        sb = sbi_ident(text, head)
        holder = sb["holder"] or holder
        hup = _sbi_fold(hup)
        kind, sbi_type = "savings", sb["kind"]
        if sb["period_to"]:
            pf, pt = sb["period_from"], sb["period_to"]
    return dict(sbi_type=sbi_type, bank=bank, kind=kind, tail=tail, period_from=pf, period_to=pt, up=hup, holder=holder,'''

CELLS_HEAD_OLD = '''    lo, hi = month + "-01", _month_end(month)
    out = []
    retired = _csv_setting(con, "packs.retired_slots")                                   # S433
    for s in [dict(r) for r in con.execute("SELECT * FROM stmt_slot ORDER BY sort")]:
        if s["key"] in retired:
            continue
'''
CELLS_HEAD_NEW = '''    lo0, hi = month + "-01", _month_end(month)
    out = []
    retired = _csv_setting(con, "packs.retired_slots")                                   # S433
    for s in [dict(r) for r in con.execute("SELECT * FROM stmt_slot ORDER BY sort")]:
        if s["key"] in retired:
            continue
        every = SLOT_EVERY.get(s["key"], 1)                                              # S621 (D754): a cadence slot
        if every > 1 and not _period_end_month(month, every):
            continue
        lo = _period_start(month, every) if every > 1 else lo0
'''

PERIOD_FUNCS = '''def _period_end_month(month, every):
    """S621: does `month` end a period of `every` months of the financial year (Apr-Mar)? Quarters end Jun, Sep, Dec, Mar;
    half-years Sep and Mar."""
    try:
        m = int(month[5:7])
    except (TypeError, ValueError):
        return False
    return ((m - 3) % 12) % every == 0


def _period_start(month, every):
    """S621: the first day of the period of `every` months that `month` ends ('2026-09', 3 -> '2026-07-01'; 6 -> '2026-04-01')."""
    y, m = int(month[:4]), int(month[5:7])
    t = y * 12 + (m - 1) - (every - 1)
    return "%04d-%02d-01" % (t // 12, t % 12 + 1)


def _period_words(month, every):
    """'July – September 2026' / 'October 2026 – March 2027'."""
    lo = _period_start(month, every)
    a = dt.date.fromisoformat(lo)
    b = dt.date(int(month[:4]), int(month[5:7]), 1)
    return ("%s – %s" % (a.strftime("%B"), b.strftime("%B %Y"))) if a.year == b.year else ("%s – %s" % (a.strftime("%B %Y"), b.strftime("%B %Y")))


def cells(con, month):'''

CELL_DICT_OLD = '''                        partial_words=(_partial_words(f, lo, hi) if partial else "")))
    return out
'''
CELL_DICT_NEW = '''                        partial_words=(_partial_words(f, lo, hi) if partial else ""),
                        every=every, period_words=(_period_words(month, every) if every > 1 else _month_name(month))))   # S621
    return out
'''

SECRET_SBI_OLD = '''    out += [(b, l + " (any other)", False) for b, l in SECRET_BANKS]
'''
SECRET_SBI_NEW = '''    for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE bank='SBI' AND kind<>'card' ORDER BY sort"):     # S621 (D754)
        if r[0] not in retired:
            out.append(("SBI:" + r[0], r[1], True))
    out += [(b, l + " (any other)", False) for b, l in SECRET_BANKS]
'''

UPLOAD_FUNC = '''# ---------------------------------------------------------------- S621 (D754): the statements the owner adds himself
def add_uploads(con, items, who):
    """[(file name, bytes)] -> each PDF kept in the inbox as a shelf file (folder 'bank', subfolder 'upload'), then the shelf's own
    pass: opened with the stored password, identified by its content, filed. The same bytes twice are one file. Returns the answer
    for the page: per file, where it went (the account and the period) or why not. Never a password, never a full account number."""
    ensure(con)
    os.makedirs(INBOX, exist_ok=True)
    added, same, refused = [], [], []
    for name, blob in list(items)[:UPLOAD_MAX_FILES]:
        nm = re.sub(r"[^A-Za-z0-9 ._()\\-]+", "_", os.path.basename(str(name or "statement.pdf")))[:120] or "statement.pdf"
        if not blob:
            refused.append(dict(name=nm, why="empty"))
            continue
        if len(blob) > UPLOAD_MAX_BYTES:
            refused.append(dict(name=nm, why="larger than %d MB" % (UPLOAD_MAX_BYTES // (1024 * 1024))))
            continue
        if not blob[:1024].lstrip().startswith(b"%PDF"):
            refused.append(dict(name=nm, why="not a PDF"))
            continue
        sha = hashlib.sha256(blob).hexdigest()
        did = "upload:" + sha[:40]
        r = con.execute("SELECT id FROM stmt_file WHERE drive_id=? OR sha256=? LIMIT 1", (did, sha)).fetchone()
        if r:
            same.append(r[0])
            continue
        lp = os.path.join(INBOX, "up_%s.pdf" % sha[:20])
        with open(lp, "wb") as fh:
            fh.write(blob)
        try:
            os.chmod(lp, 0o600)
        except OSError:
            pass
        cur = con.execute("INSERT INTO stmt_file (drive_id, name, mtime, size, folder, subfolder, sha256, fetched_at, local_path, note) "
                          "VALUES (?,?,?,?,?,?,?,?,?,?)", (did, nm, _now(), len(blob), "bank", "upload", sha, _now(), lp, "added by %s" % who))
        added.append(cur.lastrowid)
    con.commit()
    res = process_inbox(con) if added else None
    files = []
    for fid in added + same:
        f = con.execute("SELECT f.id, f.name, f.period_from, f.period_to, f.read_status, f.note, f.locked, f.unlocked_path, s.holder_label "
                        "FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.id=?", (fid,)).fetchone()
        if not f:
            continue
        locked_closed = bool(f[6]) and not f[7]
        files.append(dict(id=f[0], name=f[1], account=f[8], period_from=f[2], period_to=f[3], again=(fid in same),
                          why=("" if f[8] else ("locked — type its password in Statement passwords, further down this page; it will then open by itself" if locked_closed
                                                 else (f[5] or "not placed yet")))))
    return dict(ok=bool(added or same) or not refused, added=len(added), same=len(same), refused=refused, files=files,
                result=(dict((k, v) for k, v in res.items() if isinstance(v, int)) if res else None))


@bp.route("/finance/packs/api/upload", methods=["POST"])
def api_upload():
    """S621 (D754): the owner adds the statements he downloads himself (SBI) -- one or several PDFs, any name."""
    u, err = _owner()
    if err:
        return err
    items = [(f.filename, f.read(UPLOAD_MAX_BYTES + 1)) for f in request.files.getlist("files")]
    if not items:
        return jsonify(ok=False, error="no_file", message="choose one or more PDF files first"), 400
    body = add_uploads(_db(), items, _who(u))
    return jsonify(**body), (200 if body["ok"] else 400)


@bp.route("/finance/packs/api/secret", methods=["POST"])'''

EDITS = {
    "py": [
        ('    ("card_icici_coral",  "ICICI", "ICICI Coral (card)",                       "card",    "CORAL",                        0),\n]\n', SBI_SLOTS),
        ('SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"))',
         'SECRET_BANKS = (("YES", "Yes Bank"), ("ICICI", "ICICI Bank"), ("HDFC", "HDFC Bank"), ("SBI", "State Bank of India"))   # S621'),
        ('    bank = _bank_of(hup) or _bank_of(up)\n',
         '    bank = _bank_of(hup) or ("SBI" if ("STATE BANK OF INDIA" in hup or "SBIN0" in hup) else "") or _bank_of(up)   # S621: SBI by its head only\n'),
        ('\n\ndef identify_text(text):', SBI_FUNCS),
        ('    return dict(bank=bank, kind=kind, tail=tail, period_from=pf, period_to=pt, up=hup, holder=holder,', IDENT_RETURN),
        ('def cells(con, month):', PERIOD_FUNCS),
        (CELLS_HEAD_OLD, CELLS_HEAD_NEW),
        ('        if (ident["kind"] == "card") != (s["kind"] == "card"):\n            continue\n',
         '        if (ident["kind"] == "card") != (s["kind"] == "card"):\n            continue\n'
         '        if s["key"] in SLOT_TYPE and ident.get("sbi_type") and SLOT_TYPE[s["key"]] != ident["sbi_type"]:   # S621: savings / loan / PPF\n'
         '            continue\n'),
        (CELL_DICT_OLD, CELL_DICT_NEW),
        (SECRET_SBI_OLD, SECRET_SBI_NEW),
        ('                        files.append(("%s statement - %s%s%s" % (_nice(c["label"]), _month_name(month), (" (part %d of %d)" % (i, n)) if n else "", ext),',
         '                        files.append(("%s statement - %s%s%s" % (_nice(c["label"]), c.get("period_words") or _month_name(month), (" (part %d of %d)" % (i, n)) if n else "", ext),'),
        ('            why_ = "not on the shelf"\n',
         '            why_ = "not on the shelf" + ((" — download it from %s, then use the Add statements box on this page" % c["bank"]) if c["bank"] in MANUAL_BANKS else "")   # S621\n'),
        ('        row("stmt:" + c["slot"], "3.%d · %s statement" % (n3, c["label"]), st,',
         '        row("stmt:" + c["slot"], "3.%d · %s statement%s" % (n3, c["label"], (" (" + c["period_words"] + ")") if c.get("every", 1) > 1 else ""), st,'),
        ("        r = con.execute(\"SELECT MAX(fetched_at), SUM(CASE WHEN fetched_at>=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder='bank'\",\n",
         "        r = con.execute(\"SELECT MAX(fetched_at), SUM(CASE WHEN fetched_at>=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder='bank' \"\n"
         "                        \"AND COALESCE(subfolder,'')<>'upload'\",                     # S621: the relay's road, not the owner's uploads\n"),
        ('        bank_cells = [c for c in cells(con, m) if c["kind"] != "card"]\n',
         '        bank_cells = [c for c in cells(con, m) if c["kind"] != "card" and c["bank"] not in MANUAL_BANKS]   # S621: not the downloads\n'),
        ('\n@bp.route("/finance/packs/api/secret", methods=["POST"])', '\n' + UPLOAD_FUNC),
        ('bank=s["bank"], kind=s["kind"], sanjeevni=s["sanjeevni"],',
         'bank=s["bank"], kind={"loan": "loan", "ppf": "PPF"}.get(SLOT_TYPE.get(s["key"], ""), s["kind"]), sanjeevni=s["sanjeevni"],'),   # S621: loan / PPF said as such
    ],
    "html": [
        ('<details class="sec" id="d_pack">',
         '<div class="top" id="upcard" style="border-left-color:#2f6b45"><b>Add statements</b> <span class="mut">— the ones you download '
         'yourself from SBI (savings, loans, PPF). Pick one or several PDFs; the name does not matter. Each is opened with its password '
         '(Statement passwords, further down) and filed by what it says inside.</span><br><input type="file" id="upf" '
         'accept="application/pdf,.pdf" multiple style="margin-top:6px;max-width:100%"> <button onclick="upload()" id="upb">Add</button>'
         '<div id="upres" style="margin-top:6px"></div></div>\n<details class="sec" id="d_pack">'),
        ('One box per Yes Bank account, per ICICI account and per card; the three bank rows at the end take any other.',
         'One box per Yes Bank, ICICI and SBI account and per card; the bank-wide rows at the end take any other.'),
        ('function refreshShelf(){',
         'var MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];\n'
         'function dmy(s){var m=/^(\\d{4})-(\\d{2})-(\\d{2})/.exec(s||""); return m?(m[3]+"\\u00a0"+MON[+m[2]-1]+"\\u00a0"+m[1]):""}\n'
         '/* S621 (D754): Add statements -- one file per request, so a big one cannot sink the rest */\n'
         'function upload(){var fs=$("upf").files; if(!fs||!fs.length){alert("Choose one or more PDF files first.");return}\n'
         '  var list=Array.prototype.slice.call(fs), b=$("upb"), out=[], i=0; b.disabled=true; b.textContent="Adding…";\n'
         '  function show(more){$("upres").innerHTML=out.join("")+(more?\'<div class="mut">Adding \'+(i+1)+\' of \'+list.length+\' — keep this page open.</div>\':\'\')}\n'
         '  function one(x){var p=x.account?\'<span class="ok">\'+esc(x.account)+\'</span>\'+(x.period_from?\' <span class="mut">\'+dmy(x.period_from)+\' to \'+dmy(x.period_to)+\'</span>\':\'\')+(x.again?\' <span class="mut">· already on the shelf</span>\':\'\'):\'<span class="warn">\'+esc(x.why||"not placed")+\'</span>\';\n'
         '    return \'<div>\'+esc(x.name)+\' — \'+p+\'</div>\'}\n'
         '  function next(){if(i>=list.length){b.disabled=false;b.textContent="Add";$("upf").value="";show(false);load();return} show(true);\n'
         '    var f=list[i], fd=new FormData(); fd.append("files",f);\n'
         '    fetch("/finance/packs/api/upload",{method:"POST",body:fd}).then(function(r){if(r.status===413)return {refused:[{name:f.name,why:"too large for the server"}]}; return r.json()})\n'
         '      .then(function(j){(j.files||[]).forEach(function(x){out.push(one(x))}); (j.refused||[]).forEach(function(x){out.push(\'<div>\'+esc(x.name)+\' — <span class="bad">\'+esc(x.why)+\'</span></div>\')});\n'
         '        if(!(j.files||[]).length&&!(j.refused||[]).length)out.push(\'<div>\'+esc(f.name)+\' — <span class="bad">\'+esc(j.message||j.error||"not added")+\'</span></div>\'); i++; next()})\n'
         '      .catch(function(){out.push(\'<div>\'+esc(f.name)+\' — <span class="warn">the page lost the answer; look at the shelf below before adding it again</span></div>\'); i++; next()})}\n'
         '  next()}\n'
         'function refreshShelf(){'),
    ],
}


def main():
    which, live, out = sys.argv[1], sys.argv[2], sys.argv[3]
    kit = sys.argv[4] if len(sys.argv) > 4 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS[which], 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: %s edit %d's anchor occurs %d times (expected 1)" % (which, i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %s: %d edits applied · rebuilt %s" % (which, len(EDITS[which]), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
