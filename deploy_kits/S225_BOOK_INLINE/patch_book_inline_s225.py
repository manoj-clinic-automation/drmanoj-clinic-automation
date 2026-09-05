#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_book_inline_s225.py -- rev 11b (ed5aa926) -> rev 12: the phone book shows FULL bank details to its
three editors, names the bank from the IFSC, and every add/edit/verify is an INLINE form on the page --
no prompt(), confirm() or alert() anywhere in the book. Anchor-patch: refuses on any base other than
ed5aa92631b9e87466d9942cb5ead14c; every anchor must match exactly once."""
import hashlib, io, sys, os

BASE = "ed5aa92631b9e87466d9942cb5ead14c"
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "purchase_app.py")
src = io.open(p, encoding="utf-8").read()
if hashlib.md5(src.encode("utf-8")).hexdigest() != BASE:
    print("REFUSING: purchase_app.py is not the rev-11b base %s" % BASE); sys.exit(2)


def swap(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        print("REFUSING: anchor '%s' found %d times, need exactly 1" % (label, n)); sys.exit(2)
    src = src.replace(old, new)


# 1 -- header line
swap('purchase_app.py -- S224: Marg\'s purchases, on the box.  (rev 11b, S225, 04-Sep-2026)',
     'purchase_app.py -- S224: Marg\'s purchases, on the box.  (rev 12, S225, 05-Sep-2026)\n\n'
     'REV 12 (S225, 05-Sep, the owner: "full bank details that display correctly in page, and a bank detail\n'
     '    addition/modification opens an inline form and not a popup") -- the phone book shows the FULL account\n'
     '    number and IFSC to its three editors (it is the NEFT file\'s source; last-4 stays for audit rows and every\n'
     '    other screen), names the bank from the IFSC, labels rows that came from the NEFT records, and every\n'
     '    add / edit numbers / edit bank / verify is an INLINE form in the row -- no prompt(), confirm() or\n'
     '    alert() anywhere on the book page. The API and its rules (D370) are untouched.', "header")

# 2 -- the JS: whole block replaced
old_js_start = src.index('BOOK_JS = """')
old_js_end = src.index('"""', old_js_start + 14) + 3
NEW_JS = r'''IFSC_BANKS = {"SBIN": "State Bank of India", "HDFC": "HDFC Bank", "ICIC": "ICICI Bank", "UTIB": "Axis Bank",
              "KKBK": "Kotak Mahindra Bank", "PUNB": "Punjab National Bank", "BARB": "Bank of Baroda", "CNRB": "Canara Bank",
              "UBIN": "Union Bank of India", "UCBA": "UCO Bank", "CBIN": "Central Bank of India", "KARB": "Karnataka Bank",
              "YESB": "Yes Bank", "IDIB": "Indian Bank", "IOBA": "Indian Overseas Bank", "BKID": "Bank of India",
              "MAHB": "Bank of Maharashtra", "PSIB": "Punjab & Sind Bank", "IDFB": "IDFC First Bank", "INDB": "IndusInd Bank",
              "FDRL": "Federal Bank", "AUBL": "AU Small Finance Bank", "BDBL": "Bandhan Bank", "RATN": "RBL Bank",
              "SIBL": "South Indian Bank", "PYTM": "Paytm Payments Bank", "AIRP": "Airtel Payments Bank"}


def _bank_name(ifsc):
    """The bank, read off the first four letters of the IFSC (public codes). '' when unknown."""
    return IFSC_BANKS.get((ifsc or "")[:4].upper(), "")


BOOK_JS = """
function bookMsg(el, text){ if (!el) return; el.textContent = text || ''; el.hidden = !text; }
async function bookPost(body, msgEl){
  bookMsg(msgEl, 'saving...');
  const r = await fetch(P + '/api/book', {method:'POST', headers:{'Content-Type':'application/json'},
                                          credentials:'same-origin', body: JSON.stringify(body||{})});
  let j = {}; try { j = await r.json(); } catch(e) {}
  if (!r.ok || j.ok === false){ bookMsg(msgEl, j.message || j.error || ('HTTP ' + r.status)); return null; }
  location.reload(); return j;
}
function bookClose(i){ for (const k of ['phones','bank','verify']){ const d = document.getElementById('inl-' + k + '-' + i); if (d){ d.hidden = true; d.innerHTML = ''; } } }
function bookField(label, name, value, hint){
  return '<div><label>' + label + '</label><input name="' + name + '" value="' + (value||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;') + '"' + (hint ? ' inputmode="' + hint + '"' : '') + '></div>';
}
function bookForm(i, kind){
  const v = BOOKV[i]; const b = BOOK[v] || {}; const d = document.getElementById('inl-' + kind + '-' + i);
  if (!d) return;
  if (!d.hidden){ bookClose(i); return; }
  bookClose(i);
  let f = '';
  if (kind === 'phones'){
    f = bookField('First phone (10 digits)', 'phone', b.phone, 'numeric') + bookField('Second phone (blank for none)', 'phone2', b.phone2, 'numeric');
  } else {
    f = bookField('Account name', 'acct_name', b.acct_name) + bookField('Account number', 'acct_no', b.acct_no, 'numeric') +
        bookField('IFSC', 'ifsc', b.ifsc) + bookField('Bank and branch', 'bank_branch', b.bank_branch) + bookField('UPI id (blank for none)', 'upi_id', b.upi_id);
  }
  d.innerHTML = '<div class="grid">' + f + '</div><div class="row" style="margin-top:8px"><button class="p sm" onclick="bookSave(' + i + ',\\'' + kind + '\\')">Save</button>' +
                '<button class="sm" onclick="bookClose(' + i + ')">Cancel</button><span class="bad" id="msg-' + kind + '-' + i + '" hidden></span></div>';
  d.hidden = false;
  const first = d.querySelector('input'); if (first) first.focus();
}
async function bookSave(i, kind){
  const d = document.getElementById('inl-' + kind + '-' + i); const body = {action: kind, vendor: BOOKV[i]};
  for (const el of d.querySelectorAll('input')) body[el.name] = el.value;
  return bookPost(body, document.getElementById('msg-' + kind + '-' + i));
}
function bookVerify(i){
  const d = document.getElementById('inl-verify-' + i); if (!d) return;
  if (!d.hidden){ bookClose(i); return; }
  bookClose(i);
  d.innerHTML = '<span>Mark the bank details of <b></b> as VERIFIED? Only you can do this.</span> ' +
                '<button class="p sm" onclick="bookPost({action:\\'verify\\', vendor:BOOKV[' + i + ']}, document.getElementById(\\'msg-verify-' + i + '\\'))">Yes, verified</button> ' +
                '<button class="sm" onclick="bookClose(' + i + ')">No</button><span class="bad" id="msg-verify-' + i + '" hidden></span>';
  d.querySelector('b').textContent = BOOKV[i];
  d.hidden = false;
}
function bookAdd(){
  const f = document.getElementById('addform'); const d = {action:'add'}; const m = document.getElementById('msg-add');
  for (const el of f.querySelectorAll('input')) d[el.name] = el.value;
  if (!d.vendor || !d.phone){ bookMsg(m, 'Name and first phone are required.'); return; }
  bookPost(d, m);
}
"""'''
src = src[:old_js_start] + NEW_JS + src[old_js_end:]

# 3 -- the page: whole function body replaced, from 'def page_book' to the rev-8 banner
pb_start = src.index('@bp.route("/page/book")\ndef page_book():')
pb_end = src.index('# ====================================================================== S225 rev 8: when the goods arrive')
NEW_PAGE = r'''@bp.route("/page/book")
def page_book():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    _ensure_book(con)
    if not _book_allowed(u, con):
        return _refuse("The phone book is for Dr Manoj, Darpan and Shavez.")
    doctor = _is_doctor(u)
    rows = _book_rows(con)
    vendors = [r["vendor"] for r in rows]
    book_json = {r["vendor"]: dict(phone=r["phone"] or "", phone2=r["phone2"] or "", acct_name=r["acct_name"] or "",
                                   acct_no=r["acct_no"] or "", ifsc=r["ifsc"] or "", bank_branch=r["bank_branch"] or "",
                                   upi_id=r["upi_id"] or "") for r in rows}
    trs = []
    n_nophone = 0
    for i, r in enumerate(rows):
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
        src_txt = ("added by " + _esc(r["added_by"]) if (r["added_by"] and r["added_by"] != "neft_import_s225") else
                   "from the NEFT records (04-Sep)" if (r["source"] or "") == "neft_import" else
                   "from Marg / manojz" if (r["source"] or "manojz") != "server" else "edited here")
        if r["phone"]:
            phones = '<a href="tel:%s">%s</a>%s' % (_esc(r["phone"]), _esc(r["phone"]),
                                                   (' · <a href="tel:%s">%s</a>' % (_esc(r["phone2"]), _esc(r["phone2"]))) if r["phone2"] else "")
        else:
            n_nophone += 1
            phones = '<span class="warn">no number yet</span>'
        trs.append('<tr><td><b>%s</b><br><small class="muted">%s</small></td>'
                   '<td>%s<br><button class="sm noprint" onclick="bookForm(%d,\'phones\')">%s numbers</button>'
                   '<div class="inl noprint" id="inl-phones-%d" hidden></div></td>'
                   '<td>%s%s <button class="sm noprint" onclick="bookForm(%d,\'bank\')">%s bank details</button>'
                   '<div class="inl noprint" id="inl-bank-%d" hidden></div><div class="inl noprint" id="inl-verify-%d" hidden></div></td></tr>'
                   % (_esc(r["vendor"]), src_txt,
                      phones, i, "edit" if r["phone"] else "add", i,
                      "".join(bank_lines), chip, i, "edit" if has_bank else "add", i, i))
    add = ('<div class="card" id="addform"><h3>Add a new stockist</h3><div class="grid">'
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
    nophone = ('<div class="note noprint"><b>%d stockist%s without a phone number yet</b> — their bank details came from the NEFT '
               'records; tap <i>add numbers</i> on the row when you have the number.</div>' % (n_nophone, "s" if n_nophone != 1 else "")
               if n_nophone else "")
    body = ('<h1>Stockist phone book</h1><div class="muted">Two numbers per stockist; bank details stay on this server only and are '
            'shown in full here because this page is the source for the bulk NEFT file — it opens for Dr Manoj, Darpan and Shavez only. '
            'A bank detail added or changed by anyone but Dr Manoj is <b>UNVERIFIED</b> until he taps Verify; payments will refuse an '
            'unverified account. Details on record from the NEFT files stand as accepted (the owner, 04-Sep).</div>%s'
            '<style>.inl{margin-top:8px;padding:10px;border:1px solid var(--line);border-radius:8px;background:#f6f8fb}'
            '.inl label{display:block;font-size:12.5px;color:var(--muted)}.inl input{width:100%%}</style>'
            '<div class="card"><div class="scroll"><table><tr><th>Stockist</th><th>Phones</th><th>Bank</th></tr>%s</table></div></div>%s'
            % (nophone, "".join(trs) or '<tr><td colspan="3" class="muted">nobody in the book yet</td></tr>', add))
    return _page("Stockist phone book", body, BOOK_JS + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(vendors)))


'''
src = src[:pb_start] + NEW_PAGE + src[pb_end:]

io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched -> %s" % hashlib.md5(src.encode("utf-8")).hexdigest())
