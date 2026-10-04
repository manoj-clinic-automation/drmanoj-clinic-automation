#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s471.py -- S471_PACKS_SEPTEMBER (session 293, 04-Oct-2026). Exact-anchor edits on three files, built from the
real bytes of the 04-Oct 01:35 bundle:  packs.py 23fda41a · packs.html 4c46cd0e · stmt_shelf.py 95ba0a4f.

The owner's four refinements of the month-end packs (04-Oct):
  1. STITCH -- an ICICI account whose statements come by cycle (11th -> 10th, 15th -> 14th) never covers a calendar month in one
     file; two consecutive statements that together cover it are the month's statement (both go in the pack, 'part 1 of 2').
     A single cycle statement is 'partial' on the row AND on the shelf (one word for one file), and the row says which
     statement is still to come and roughly when.
  2. STATEMENT PASSWORDS PER YES BANK ACCOUNT -- the card lists the six Yes Bank accounts (the shelf's own slots), one
     password each (stored under the key 'YES:<slot key>' in the same stmt_secret table; the per-bank boxes stay as 'any
     other'); the unlock step tries the account passwords first; the card shows how many files each key opened.
  3. WORDING -- row numbers that do not repeat (3.1 ... 3.12, 4.1 ... 4.4, 8.1, 8.2); the electricity row says the bills are
     paid around the 17th and show in the ICICI statements when those are not on the shelf yet; the Shavez summary says
     'done' and 'open' both; the shelf's intro names both fetch times.
  4. The second shelf fetch at 07:30 is a crontab line placed by the installer, not an edit here.
Every anchor must be found exactly once.
   usage: apply_s471.py <packs.py> <packs.html> <stmt_shelf.py>
"""
import hashlib
import sys

FROM = {"packs.py": "23fda41a19a6d4be398922e906d06702", "packs.html": "4c46cd0e19ec08a7678dd6088624a174",
        "stmt_shelf.py": "95ba0a4fadd25d9f30a67e7f99eba9f1"}

PY_EDITS = [
    # ---- the stitch helper, before cells()
    ('''# ---------------------------------------------------------------- the month cells
def cells(con, month):
''',
     '''# ---------------------------------------------------------------- the month cells
def _stitch(fs, lo, hi):
    """S471: the statements of one account that TOGETHER cover the month lo..hi, each starting on or before the day after the
    previous one ends (ICICI's cycle statements: 11th -> 10th, 15th -> 14th). Returns the pieces in date order, or []."""
    cand = sorted([x for x in fs if x.get("period_from") and x.get("period_to")], key=lambda x: (x["period_from"], x["period_to"]))
    for i, first in enumerate(cand):
        if first["period_from"] > lo:
            break
        chain, end = [first], first["period_to"]
        for nxt in cand[i + 1:]:
            if end >= hi:
                break
            if nxt["period_to"] <= end:
                continue
            if nxt["period_from"] <= _iso_plus(end, 1):
                chain.append(nxt)
                end = nxt["period_to"]
        if end >= hi and len(chain) > 1:
            return chain
    return []


def _iso_plus(iso, days):
    try:
        return (dt.date.fromisoformat(iso) + dt.timedelta(days=days)).isoformat()
    except (TypeError, ValueError):
        return iso


def _partial_words(f, lo, hi):
    """S471: what a single cycle statement leaves uncovered, in the owner's words, with the rough date the next one is due."""
    pf, pt = f.get("period_from") or "", f.get("period_to") or ""
    if pf <= lo and pt < hi:
        try:
            d0 = dt.date.fromisoformat(pt)
            nxt_from, nxt_to = d0 + dt.timedelta(days=1), (d0 + dt.timedelta(days=32)).replace(day=min(d0.day, 28))
            return "%s → %s on the shelf; the %s → %s statement completes the month (due from the bank about %s)" % (
                _dmy(pf), _dmy(pt), _dmy(nxt_from.isoformat()), _dmy(nxt_to.isoformat()), _dmy((nxt_to + dt.timedelta(days=1)).isoformat()))
        except ValueError:
            pass
    if pf > lo:
        return "%s → %s on the shelf; the earlier statement (up to %s) is not on the shelf" % (_dmy(pf), _dmy(pt), _dmy(_iso_plus(pf, -1)))
    return "only %s → %s on the shelf, not the whole month" % (_dmy(pf), _dmy(pt))


def cells(con, month):
'''),
    ('''        full = [x for x in fs if x["period_from"] <= lo and x["period_to"] >= hi]   # S411: the month's statement covers the whole month
''',
     '''        full = [x for x in fs if x["period_from"] <= lo and x["period_to"] >= hi]   # S411: the month's statement covers the whole month
        pieces = _stitch(fs, lo, hi) if (not full and s["kind"] != "card") else []   # S471: two cycle statements together cover it
'''),
    ('''        f = full[0] if full else (fs[0] if fs else None)
        partial = bool(f) and not full and s["kind"] != "card"
''',
     '''        f = full[0] if full else (pieces[-1] if pieces else (fs[0] if fs else None))
        partial = bool(f) and not full and not pieces and s["kind"] != "card"
'''),
    ('''        state = "empty"
        if partial:
            state = "partial"
        elif f:
            state = "arrived"
            if f["read_status"] == "read" or (s["kind"] == "card" and f["read_status"] in ("n/a", None, "")):
                state = "read"
''',
     '''        state = "empty"
        if partial:
            state = "partial"
        elif pieces:                                                                 # S471: every piece must be read
            state = "read" if all(x["read_status"] == "read" for x in pieces) else "arrived"
        elif f:
            state = "arrived"
            if f["read_status"] == "read" or (s["kind"] == "card" and f["read_status"] in ("n/a", None, "")):
                state = "read"
'''),
    ('''                        twin_missing=twin_missing, no_decrypted=no_dec))
    return out
''',
     '''                        twin_missing=twin_missing, no_decrypted=no_dec,
                        pieces=[dict(id=x["id"], name=x["name"], period_from=x["period_from"], period_to=x["period_to"], read_status=x["read_status"]) for x in pieces],   # S471
                        partial_words=(_partial_words(f, lo, hi) if partial else "")))
    return out
'''),
    # ---- the pack rows: numbering, the stitched pieces, 'partial' as its own status
    ('''    cl = cells(con, month)
    for c in cl:
        if c["kind"] == "card":
            continue
        f = c["file"]
        st = "ready" if (f and c["state"] in ("read", "matched", "arrived")) else "missing"
        files = None
        if f and st == "ready":
            fr = con.execute("SELECT local_path, name FROM stmt_file WHERE id=?", (f["id"],)).fetchone()
            if fr and fr[0] and os.path.exists(fr[0]):
                ext = os.path.splitext(fr[0])[1].lower() or ".pdf"
                with open(fr[0], "rb") as fh:
                    files = [("%s statement - %s%s" % (_nice(c["label"]), _month_name(month), ext), fh.read(), "application/pdf" if ext == ".pdf" else "text/plain")]   # S434
        why_ = ""
        if not f:
            why_ = "not on the shelf"
        elif c["state"] == "partial":                                  # S411
            why_ = "only %s → %s on the shelf, not the whole month" % (_dmy(f["period_from"]), _dmy(f["period_to"]))
        elif st != "ready":
            why_ = "read: " + (f["read_status"] or "arrived")
        elif f["read_status"] and f["read_status"] != "read":
            why_ = f["read_status"]
        row("stmt:" + c["slot"], "3 · %s statement" % c["label"], st, why_, files, "/finance/packs/file/%d" % f["id"] if f else None, bool(c["sanjeevni"]))
''',
     '''    cl = cells(con, month)
    n3 = 0
    for c in cl:
        if c["kind"] == "card":
            continue
        n3 += 1
        f = c["file"]
        st = "ready" if (f and c["state"] in ("read", "matched", "arrived")) else ("partial" if c["state"] == "partial" else "missing")   # S471
        files = None
        if f and st == "ready":
            pieces = c.get("pieces") or []                                     # S471: the stitched month goes in as part 1 of 2
            srcs = [(p["id"], i + 1, len(pieces)) for i, p in enumerate(pieces)] if pieces else [(f["id"], 0, 0)]
            files = []
            for fid, i, n in srcs:
                fr = con.execute("SELECT local_path, name FROM stmt_file WHERE id=?", (fid,)).fetchone()
                if fr and fr[0] and os.path.exists(fr[0]):
                    ext = os.path.splitext(fr[0])[1].lower() or ".pdf"
                    with open(fr[0], "rb") as fh:
                        files.append(("%s statement - %s%s%s" % (_nice(c["label"]), _month_name(month), (" (part %d of %d)" % (i, n)) if n else "", ext), fh.read(), "application/pdf" if ext == ".pdf" else "text/plain"))   # S434
            files = files or None
        why_ = ""
        if not f:
            why_ = "not on the shelf"
        elif c["state"] == "partial":                                  # S411 · S471: which statement is still to come
            why_ = c.get("partial_words") or ("only %s → %s on the shelf, not the whole month" % (_dmy(f["period_from"]), _dmy(f["period_to"])))
        elif c.get("pieces"):                                          # S471
            why_ = "%d statements together cover the month: %s" % (len(c["pieces"]), " + ".join("%s → %s" % (_dmy(p["period_from"]), _dmy(p["period_to"])) for p in c["pieces"]))
            if st != "ready":
                why_ += "; read: " + ", ".join(p["read_status"] or "arrived" for p in c["pieces"])
        elif st != "ready":
            why_ = "read: " + (f["read_status"] or "arrived")
        elif f["read_status"] and f["read_status"] != "read":
            why_ = f["read_status"]
        row("stmt:" + c["slot"], "3.%d · %s statement" % (n3, c["label"]), st, why_, files, "/finance/packs/file/%d" % f["id"] if f else None, bool(c["sanjeevni"]))
    n4 = 0
'''),
    ('''        row("card:" + c["slot"], "4 · %s statement (password removed)" % c["label"], ("ready" if f else "missing") if not c["twin_missing"] else ("late" if f else "missing"), why_, files, "/finance/packs/file/%d" % f["id"] if f else None)
''',
     '''        n4 += 1
        row("card:" + c["slot"], "4.%d · %s statement (password removed)" % (n4, c["label"]), ("ready" if f else "missing") if not c["twin_missing"] else ("late" if f else "missing"), why_, files, "/finance/packs/file/%d" % f["id"] if f else None)
'''),
    ('''    row("cards", "4 · All_Transactions.xlsx (the cards' sheet)", "ready" if files else "missing", "" if files else "not fetched from Drive yet", files, "/finance/packs/file/%d" % at[0] if at else None)
''',
     '''    row("cards", "4.%d · All_Transactions.xlsx (the cards' sheet)" % (n4 + 1), "ready" if files else "missing", "" if files else "not fetched from Drive yet", files, "/finance/packs/file/%d" % at[0] if at else None)
'''),
    ('''    row("electricity", "5 · Electricity: the auto-paid bills (ICICI statements and the Amazon Pay card)", "ready" if len(el) >= want else "missing",   # S434
        (why or "") if not el else ("%d of %d found: " % (len(el), want) if len(el) < want else "") + " · ".join(el), None, None)
''',
     '''    if len(el) < want and not any(c["file"] for c in cl if c["bank"] == "ICICI" and c["kind"] != "card"):   # S471: the bills come with the statements
        why = "the ICICI statements for %s are not on the shelf yet -- the two bills are paid around the 17th and show there" % _month_name(month)
    row("electricity", "5 · Electricity: the auto-paid bills (ICICI statements and the Amazon Pay card)", "ready" if len(el) >= want else "missing",   # S434
        (why or "") if not el else ("%d of %d found: " % (len(el), want) if len(el) < want else "") + " · ".join(el), None, None)
'''),
    ('''    for lane, label in (("lab_purchase", "Dr Bhawna's lab-purchase bills"), ("owner_expense", "Dr Manoj's expense-file bills")):
        b, why = build_bundle(con, month, lane, count_only=light)
        row("bundle:" + lane, "8 · Scanned bills: %s (numbered bundle + index)" % label, "ready" if b else "missing", why or "",
''',
     '''    for n8, (lane, label) in enumerate((("lab_purchase", "Dr Bhawna's lab-purchase bills"), ("owner_expense", "Dr Manoj's expense-file bills")), 1):
        b, why = build_bundle(con, month, lane, count_only=light)
        row("bundle:" + lane, "8.%d · Scanned bills: %s (numbered bundle + index)" % (n8, label), "ready" if b else "missing", why or "",
'''),
    # ---- the passwords: per Yes Bank account
    ('''def secret_state(con):
    """S412: what the page may know of the passwords -- per bank: set or not, by whom, when, how many candidates. NEVER the value."""
    ensure(con)
    have = {r[0]: r for r in con.execute("SELECT bank, set_by, set_at, secret FROM stmt_secret")}
    out = []
    for bank, label in SECRET_BANKS:
        r = have.get(bank)
        n = 0
        if r:
            try:
                n = len(json.loads(r[3]))
            except (TypeError, ValueError):
                n = 1
        out.append(dict(bank=bank, label=label, set=bool(r), set_by=(r[1] if r else None), set_at=(r[2] if r else None), candidates=n))
    lk = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder<>'cards' AND locked=1 AND (unlocked_path IS NULL OR unlocked_path='')", (LOCKED_NO_PW,)).fetchone()
    opened = con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL AND unlocked_path<>''").fetchone()[0]
    return dict(banks=out, locked_open=int(lk[0] or 0), no_password=int(lk[1] or 0), opened=int(opened or 0))
''',
     '''def secret_keys(con):
    """S471: the keys a password may be stored under -- one per Yes Bank account on the shelf ('YES:<slot key>', the account's
    label) first, then the three banks. Data from stmt_slot; never a value."""
    out = []
    retired = _csv_setting(con, "packs.retired_slots")
    for r in con.execute("SELECT key, holder_label FROM stmt_slot WHERE bank='YES' AND kind<>'card' ORDER BY sort"):
        if r[0] not in retired:
            out.append(("YES:" + r[0], r[1], True))
    out += [(b, l + " (any other)", False) for b, l in SECRET_BANKS]
    return out


def secret_state(con):
    """S412: what the page may know of the passwords -- per key: set or not, by whom, when, how many candidates, how many files
    it opened. NEVER the value. S471: one key per Yes Bank account, then the three banks."""
    ensure(con)
    have = {r[0]: r for r in con.execute("SELECT bank, set_by, set_at, secret FROM stmt_secret")}
    opened_by = {r[0]: r[1] for r in con.execute("SELECT bank, COUNT(*) FROM stmt_secret_log WHERE action LIKE 'opened file %' GROUP BY bank")}
    out = []
    for bank, label, is_account in secret_keys(con):
        r = have.get(bank)
        n = 0
        if r:
            try:
                n = len(json.loads(r[3]))
            except (TypeError, ValueError):
                n = 1
        out.append(dict(bank=bank, label=label, account=is_account, set=bool(r), set_by=(r[1] if r else None), set_at=(r[2] if r else None), candidates=n,
                        opened=int(opened_by.get(bank, 0))))
    lk = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder<>'cards' AND locked=1 AND (unlocked_path IS NULL OR unlocked_path='')", (LOCKED_NO_PW,)).fetchone()
    opened = con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL AND unlocked_path<>''").fetchone()[0]
    return dict(banks=out, locked_open=int(lk[0] or 0), no_password=int(lk[1] or 0), opened=int(opened or 0))
'''),
    ('''    ensure(con)
    bank = str(bank or "").upper().strip()[:8]
    cands = []
    for ln in str(text or "").splitlines():
        ln = ln.strip()
        if ln and ln[:64] not in cands:
            cands.append(ln[:64])
    if bank not in {b for b, _ in SECRET_BANKS} or not cands or len(cands) > 10:
        return dict(ok=False, error="bad_request"), 400
''',
     '''    ensure(con)
    bank = str(bank or "").strip()[:40]                                 # S471: 'YES:<slot key>' keeps its case; a bank name is upper
    bank = bank if ":" in bank else bank.upper()[:8]
    cands = []
    for ln in str(text or "").splitlines():
        ln = ln.strip()
        if ln and ln[:64] not in cands:
            cands.append(ln[:64])
    if bank not in {k for k, _l, _a in secret_keys(con)} or not cands or len(cands) > 10:
        return dict(ok=False, error="bad_request"), 400
'''),
]

HTML_EDITS = [
    ('''<div class="mut">One cell per account or card. Nightly at 05:40 the box lists the Drive folders and files what it finds by the statement's own content — the bank, the holder's name, the account or card tail, the period. Never by file name.</div>''',
     '''<div class="mut">One cell per account or card. At 05:40 and again at 07:30 the box lists the Drive folders and files what it finds by the statement's own content — the bank, the holder's name, the account or card tail, the period. Never by file name. Two cycle statements that together cover the month count as the month's statement.</div>'''),
    ('''<div class="mut">Only for password-locked PDFs (Yes Bank's e-statements). Not needed while the branch sends each month's statements unlocked. Typed once, kept on the server only, never shown again, never in any mail or log.</div>''',
     '''<div class="mut">Only for password-locked PDFs (the banks' e-statements). Not needed while the branch sends each month's statements unlocked. One password per Yes Bank account — each account's e-statement has its own; the three bank rows below take any other. Typed once, kept on the server only, never shown again, never in any mail or log.</div>'''),
    ('''      (f?('<span class="ok">'+esc(c.state)+'</span> <span class="mut">'+esc(f.period_from||"")+' → '+esc(f.period_to||"")+(f.read_status&&f.read_status!=="read"?' · '+esc(f.read_status):'')+(f.locked?' · opened from the locked e-statement':'')+'</span> <a href="/finance/packs/file/'+f.id+'" target="_blank">open</a>'):'<span class="bad">empty</span>')+''',
     '''      (f?('<span class="'+(c.state==="partial"?"warn":"ok")+'">'+esc(c.state)+'</span> <span class="mut">'+(c.pieces&&c.pieces.length?c.pieces.map(function(p){return esc(p.period_from||"")+' → '+esc(p.period_to||"")}).join(' + '):esc(f.period_from||"")+' → '+esc(f.period_to||""))+(f.read_status&&f.read_status!=="read"?' · '+esc(f.read_status):'')+(f.locked?' · opened from the locked e-statement':'')+(c.state==="partial"&&c.partial_words?' · '+esc(c.partial_words):'')+'</span> '+(c.pieces&&c.pieces.length?c.pieces.map(function(p,i){return '<a href="/finance/packs/file/'+p.id+'" target="_blank">open part '+(i+1)+'</a>'}).join(' '):'<a href="/finance/packs/file/'+f.id+'" target="_blank">open</a>')):'<span class="bad">empty</span>')+'''),
    ('''    $("secrets").innerHTML='<table><tr><th>Bank</th><th>Password</th><th></th></tr>'+sc.banks.map(function(b){return '<tr><td><b>'+esc(b.label)+'</b></td><td>'+(b.set?'<span class="ok">set</span> <span class="mut">on '+esc((b.set_at||"").slice(0,16).replace("T"," "))+' by '+esc(b.set_by||"")+' · '+b.candidates+' candidate'+(b.candidates===1?'':'s')+'</span>':'<span class="warn">not set</span>')+
      '</td><td><textarea class="sec" id="sec_'+esc(b.bank)+'" rows="2" placeholder="one candidate per line" autocomplete="off"></textarea> <button class="ghost" onclick="setSecret(\\''+esc(b.bank)+'\\')">'+(b.set?'Replace':'Set')+'</button></td></tr>'}).join("")+'</table>'+''',
     '''    $("secrets").innerHTML='<table><tr><th>Account / bank</th><th>Password</th><th></th></tr>'+sc.banks.map(function(b){return '<tr><td><b>'+esc(b.label)+'</b>'+(b.account?'':' <span class="mut">(bank-wide)</span>')+'</td><td>'+(b.set?'<span class="ok">set</span> <span class="mut">on '+esc((b.set_at||"").slice(0,16).replace("T"," "))+' by '+esc(b.set_by||"")+' · '+b.candidates+' candidate'+(b.candidates===1?'':'s')+(b.opened?' · opened '+b.opened+' file'+(b.opened===1?'':'s')+' ✓':' · opened nothing yet')+'</span>':'<span class="warn">not set</span>')+
      '</td><td><textarea class="sec" id="sec_'+esc(b.bank).replace(/:/g,"_")+'" rows="2" placeholder="one candidate per line" autocomplete="off"></textarea> <button class="ghost" onclick="setSecret(\\''+esc(b.bank)+'\\')">'+(b.set?'Replace':'Set')+'</button></td></tr>'}).join("")+'</table>'+'''),
    ('''      var st=r.status==="ready"?'<span class="ok">ready ✓</span>':(r.status==="late"?'<span class="warn">late</span>':(r.status==="tick"?'<button class="ghost" onclick="tick(\\''+esc(r.key)+'\\')">tick — handed over</button>':'<span class="bad">missing</span>'));''',
     '''      var st=r.status==="ready"?'<span class="ok">ready ✓</span>':(r.status==="late"?'<span class="warn">late</span>':(r.status==="partial"?'<span class="warn">partial</span>':(r.status==="tick"?'<button class="ghost" onclick="tick(\\''+esc(r.key)+'\\')">tick — handed over</button>':'<span class="bad">missing</span>')));'''),
    ('''  $("toplist").innerHTML=miss.map(function(r){return '<li>'+esc(r.title.replace(/^\\d+ · /,""))+' — <span class="'+(r.status==="tick"?"warn":"bad")+'">'+(r.status==="tick"?"tick when handed over":esc(r.why||"missing"))+'</span></li>'}).join("");''',
     '''  $("toplist").innerHTML=miss.map(function(r){return '<li>'+esc(r.title.replace(/^[\\d.]+ · /,""))+' — <span class="'+((r.status==="tick"||r.status==="partial")?"warn":"bad")+'">'+(r.status==="tick"?"tick when handed over":esc(r.why||"missing"))+'</span></li>'}).join("");'''),
    ('''  $("s_chk").textContent="· "+dn.length+" of "+ch.length+" done";''',
     '''  $("s_chk").textContent="· "+dn.length+" of "+ch.length+" done · "+(ch.length-dn.length)+" open";'''),
    ('''function setSecret(bank){var t=$("sec_"+bank).value; if(!t.trim()){alert("type at least one candidate");return}
  post("/finance/packs/api/secret",{bank:bank,text:t}).then(function(j){$("sec_"+bank).value=""; if(!j.ok){alert(j.message||j.error||"not saved");return}''',
     '''function setSecret(bank){var box=$("sec_"+bank.replace(/:/g,"_")); var t=box.value; if(!t.trim()){alert("type at least one candidate");return}
  post("/finance/packs/api/secret",{bank:bank,text:t}).then(function(j){box.value=""; if(!j.ok){alert(j.message||j.error||"not saved");return}'''),
]

SHELF_EDITS = [
    ('''    for bank, sec in con.execute("SELECT bank, secret FROM stmt_secret ORDER BY bank"):''',
     '''    # S471: an account's own password ('YES:<slot key>') is tried before a bank-wide one
    for bank, sec in con.execute("SELECT bank, secret FROM stmt_secret ORDER BY CASE WHEN instr(bank, ':') > 0 THEN 0 ELSE 1 END, bank"):'''),
]


def apply(src, edits, what):
    for n, (old, new) in enumerate(edits, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! %s anchor %d was found %d time(s), expected 1 - nothing written" % (what, n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: apply_s471.py <packs.py> <packs.html> <stmt_shelf.py>")
    plan = [("packs.py", sys.argv[1], PY_EDITS), ("packs.html", sys.argv[2], HTML_EDITS), ("stmt_shelf.py", sys.argv[3], SHELF_EDITS)]
    outs = []
    for name, path, edits in plan:
        raw = open(path, "rb").read()
        have = hashlib.md5(raw).hexdigest()
        if have != FROM[name]:
            raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM[name]))
        out = apply(raw.decode("utf-8"), edits, name).encode("utf-8")
        if name.endswith(".py"):
            compile(out, path, "exec")
        outs.append((name, path, raw, out))
    for name, path, raw, out in outs:                     # all three verified before any is written
        with open(path, "wb") as fh:
            fh.write(out)
        print("%s %s -> %s (%d edits; %+d bytes)" % (name, hashlib.md5(raw).hexdigest()[:8], hashlib.md5(out).hexdigest()[:8],
                                                     len({"packs.py": PY_EDITS, "packs.html": HTML_EDITS, "stmt_shelf.py": SHELF_EDITS}[name]), len(out) - len(raw)))


if __name__ == "__main__":
    main()
