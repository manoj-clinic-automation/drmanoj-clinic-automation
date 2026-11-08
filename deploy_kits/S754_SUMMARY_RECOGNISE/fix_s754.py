#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_s754.py -- kit S754_SUMMARY_RECOGNISE, the data step: today's papers that are dealers' month statements, put right (08-Nov-2026).
The owner, 17:27 IST 08-Nov (superseding D870's 'staff rescan it'): the system recognises a summary; these are recognised by this line.

    python3 -B fix_s754.py --assets /root/assetapp/assets.db --uploads /root/assetapp/uploads --finance /root/finance/finance.db          # DRY
    python3 -B fix_s754.py --assets ... --uploads ... --finance ... --real                                                             # REAL

  B-0297 Mannat · B-0298 Gunina · B-0299 Deepam  (pharmacy lane, read as bills)   -> kind 'Summary', doc_kind 'summary', re-read
  B-0291 Shraddha · B-0292 Drug Deals · B-0293 A.A. Pharmaceuticals  (clinic-lane drafts on the desk)
                                                 -> the pharmacy lane, status captured (off the desk), kind 'Summary', re-read
  B-0296 L.K. Drug House  (joined to Janta's B-0295 as its 'page 2')
                                                 -> unjoined (page_of empty, captured), kind 'Summary', re-read; B-0295's own single
                                                    file put back (S441 kept both originals)
  B-0303 Daanshi  (read with the buyer's name, dated 02-11)                         -> re-read with S754's summary reader

A re-read: claude_reader.read_summary (the S754 cleaner: the dealer never the buyer, the period from the bills); the bills row's
vendor / bill no / date / figure lent by the old bill reading are cleared and filled from the summary, through the app's own
_bg_extract (then the month, the double guard, the S441 checks), as a new scan. Every guard is read first: the paper is the one read on
the screen (id, stamp, scanned 08-Nov by Alisha, the vendor and the amount as read), in the state it was found in (or already put right
by an earlier run of this line); nothing a person decided on it (an audit row by a person after the scan, a question answered by a
person, a payment, a machine, a procedure-room line, stationery, a warranty, an outside paper pointing at it; on finance.db -- read
only -- a link to a Marg bill, a person's decision on its pairing row, s736 / s749 / s750 decisions); no item lines. Any refusal: NOTHING
is changed. REAL backs up assets.db first (beside it, .bak_S754_<stamp>), changes the rows in ONE transaction, then re-reads one by one;
a re-read the reader could not finish is said so, and running the same line again carries on (the rows already put right are skipped).
finance.db is never written. Prints no person's name except the scanner's, no number of a patient (there is none on these papers)."""
import json
import os
import sqlite3
import sys
import time

KIT = "S754_SUMMARY_RECOGNISE"
DAY = "2026-11-08"
WHO = "Alisha"
# id, stamp, what is done, vendor as the page read it ('' = none), amount as read
TARGETS = [
    (291, "B-0291", "move", "SANJEEVNI MEDICOS", 2453),
    (292, "B-0292", "move", "DRUG DEALS", 1557),
    (293, "B-0293", "move", "A.A.PHARMACEUTICALS", 12818),
    (296, "B-0296", "unjoin", "", 3656),
    (297, "B-0297", "kind", "MANNAT PHARMA", 24212),
    (298, "B-0298", "kind", "GUNINA PHARMACEUTICALS PVT. LTD.", 60682),
    (299, "B-0299", "kind", "DEEPAM PHARMA", 32114),
    (303, "B-0303", "reread", "SANJEEVNI MEDICOS", 8603),
]
HEAD = (295, "B-0295", "JANTA PHARMACEUTICALS", 13146)      # B-0296's 'head': only its own file put back
IDS = [t[0] for t in TARGETS]
ALL = IDS + [HEAD[0]]
Q = ",".join("?" * len(IDS))
PERSON_OK = ("summary", "challan", "blur_kept", "rescan_of")     # what the scanner's own Save writes under her name
REFUSE_A = [("paper_payment_bill", "bill_id"), ("proc_paper", "bill_id"), ("proc_line", "bill_id"), ("proc_photo", "bill_id"), ("stationery_line", "bill_id"),
            ("d664_warranty", "bill_id"), ("d664_join", "head_id"), ("d664_join", "page_id"), ("paper_payment", "proof_bill_id"), ("assets", "bill_id")]
FIN_REFUSE = [("purchase_scan_link", "asset_bill_id"), ("s736_decision", "asset_bill_id"), ("s749_act", "scan"), ("s750_dealer_of", "scan")]


def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def has_table(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def has_col(con, t, c):
    return has_table(con, t) and c in {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}


def now_ist():
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 19800))


def vendor_ok(read, have):
    a = "".join(ch for ch in (read or "").upper() if ch.isalnum())
    b = "".join(ch for ch in (have or "").upper() if ch.isalnum())
    return (not b) if not a else a[:6] == b[:6]


def reading(con, bid):
    r = con.execute("SELECT ok, doc_kind, data FROM claude_reading WHERE bill_id=?", (bid,)).fetchone() if has_table(con, "claude_reading") else None
    if not r:
        return None, None, {}
    try:
        d = json.loads(r[2]) if r[2] else {}
    except ValueError:
        d = {}
    return r[0], r[1], d if isinstance(d, dict) else {}


def reread_done(con, bid):
    """Re-read by S754's reader AND the row filled from it (the app's reading finished: ocr 'read' or 'empty')."""
    ok, dk, d = reading(con, bid)
    st = con.execute("SELECT ocr_status FROM bills WHERE id=?", (bid,)).fetchone()
    return (bool(ok) and dk == "summary" and "period_by" in d and d.get("is_summary") is not False
            and bool(st) and (st[0] or "") in ("read", "empty"))


def s754_reread_started(con, bid):
    """This line already cleared the row for a re-read (its 'reread_summary' audit row) -- the re-read was cut short: carry on."""
    return con.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='reread_summary' AND who='S754 (the owner''s line)'", (bid,)).fetchone() is not None


def placed(r):
    """The row is in the state this line puts it in (kind Summary on the pharmacy lane, captured, not a page)."""
    return (r["lane"] == "pharmacy" and r["kind"] == "Summary" and (r["doc_kind"] or "") == "summary" and r["status"] == "captured"
            and not r["page_of"])


def found_as(r, what):
    if what == "move":
        return r["lane"] == "clinic" and r["kind"] == "Consumable" and r["status"] == "draft" and not r["page_of"] and not r["dup_of"] \
            and not (r["doc_kind"] or "")
    if what == "unjoin":
        return (r["lane"] == "pharmacy" and r["kind"] == "Pharmacy" and r["status"] == "rejected" and r["page_of"] == HEAD[0]
                and (r["reject_reason"] or "").startswith("page 2 of " + HEAD[1]) and (r["approved_by"] or "") == "server (S441 forgotten page)"
                and not r["dup_of"])
    if what == "kind":
        return r["lane"] == "pharmacy" and r["kind"] == "Pharmacy" and r["status"] == "captured" and not r["page_of"] and not r["dup_of"] \
            and (r["doc_kind"] or "") not in ("challan", "summary")
    if what == "reread":
        return placed(r) and not r["dup_of"]
    return False


def merge_of(con):
    """B-0295's s441_page_merged audit naming B-0296: (before, after) or (None, None)."""
    for a in con.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action='s441_page_merged' ORDER BY rowid DESC", (HEAD[0],)):
        try:
            d = json.loads(a[0] or "{}")
        except ValueError:
            continue
        if int(d.get("page") or 0) == 296:
            return d.get("before"), d.get("after")
    return None, None


def rotations(con, f):
    """f and every upright copy made of it since (scan_lie.rotated_to, S618; B-0295's rows)."""
    out, seen = [f], {f}
    if not has_table(con, "scan_lie"):
        return out
    while True:
        r = con.execute("SELECT rotated_to FROM scan_lie WHERE bill_id=? AND file=? AND rotated_to IS NOT NULL", (HEAD[0], out[-1])).fetchone()
        if not r or not r[0] or r[0] in seen:
            return out
        out.append(r[0])
        seen.add(r[0])


def main():
    adb, up, fdb, real = arg("--assets"), arg("--uploads"), arg("--finance"), "--real" in sys.argv
    if not adb or not up or not fdb:
        print(__doc__)
        return 2
    for p in (adb, fdb):
        if not os.path.isfile(p):
            print("!! not a file: %s -- nothing done" % p)
            return 2
    if not os.path.isdir(up):
        print("!! not a folder: %s -- nothing done" % up)
        return 2
    print("%s -- %s IST  %s" % (KIT, now_ist(), "REAL" if real else "DRY (nothing written)"))
    a = sqlite3.connect(adb, timeout=30)
    a.row_factory = sqlite3.Row
    f = sqlite3.connect("file:%s?mode=ro" % fdb, uri=True, timeout=30)
    f.row_factory = sqlite3.Row
    bad, todo = [], {}
    print("1  the eight papers (and B-0295, whose file is put back)")
    for bid, stamp, what, vendor, rs in TARGETS + [(HEAD[0], HEAD[1], "head", HEAD[2], HEAD[3])]:
        r = a.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        if r is None:
            bad.append("%s (#%d) is not in bills" % (stamp, bid))
            print("   !! %s #%d NOT FOUND" % (stamp, bid))
            continue
        probs = []
        if (r["stamp_no"] or "") != stamp:
            probs.append("stamp is %r" % r["stamp_no"])
        if not str(r["submitted_at"] or "").startswith(DAY):
            probs.append("scanned %r, not %s" % (r["submitted_at"], DAY))
        if WHO.lower() not in str(r["submitted_by"] or "").lower() and WHO.lower() not in str(r["scanned_by"] if "scanned_by" in r.keys() else "").lower():
            probs.append("scanned by %r, not %s" % (r["submitted_by"], WHO))
        state = "?"
        if what == "head":
            bf, af = merge_of(a)
            cur = r["source_stored"]
            if r["lane"] != "pharmacy" or r["kind"] != "Summary" or r["status"] != "captured":
                probs.append("not the captured Summary it was (%s, %s, %s)" % (r["lane"], r["kind"], r["status"]))
            if bf and cur in rotations(a, bf):
                state = "its own file already"
            elif not bf or not af:
                probs.append("no audit of the merge with B-0296 (s441_page_merged)")
            elif cur not in rotations(a, af):
                probs.append("its file %r is not the merged file %r (or an upright copy of it)" % (cur, af))
            elif not os.path.isfile(os.path.join(up, bf)):
                probs.append("its own first file %r is not on disk" % bf)
            else:
                state = "file to put back: %s -> %s" % (cur, bf)
                todo[bid] = ("head", bf, cur)
            if not vendor_ok(vendor, r["vendor"]) or r["total_amount"] is None or abs(float(r["total_amount"]) - rs) > 1.0:
                probs.append("vendor/amount %r / %r, read %r / %d" % (r["vendor"], r["total_amount"], vendor, rs))
        else:
            done_state = placed(r)
            if found_as(r, what) and not (what == "reread" and (reread_done(a, bid) or s754_reread_started(a, bid))):
                state = "as found -> " + {"move": "pharmacy lane, captured, Summary", "unjoin": "unjoined, captured, Summary",
                                          "kind": "Summary", "reread": "re-read"}[what]
                if not vendor_ok(vendor, r["vendor"]) or r["total_amount"] is None or abs(float(r["total_amount"]) - rs) > 1.0:
                    probs.append("vendor/amount %r / %r, read %r / %d" % (r["vendor"], r["total_amount"], vendor, rs))
                todo[bid] = (what, "state" if what != "reread" else "", "")
            elif done_state and reread_done(a, bid):
                state = "ALREADY DONE (Summary, re-read by S754)"
            elif done_state:
                state = "put right earlier, the re-read still to do"
                todo[bid] = (what, "", "")
            else:
                probs.append("not in the state it was found in (%s, %s, %s, page_of %s, doc_kind %s)" % (r["lane"], r["kind"], r["status"], r["page_of"], r["doc_kind"]))
            n_it = a.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (bid,)).fetchone()[0]
            if n_it:
                probs.append("%d item line(s) on it" % n_it)
            if (r["subgroup"] if "subgroup" in r.keys() else None) in ("personal", "resume", "patient_paper"):
                probs.append("in a person's section (%s)" % r["subgroup"])
        ok_, dk, d = reading(a, bid)
        print("   %s #%d  %-22s %9s  %s  %-8s %-10s %-9s dup_flag %-5s read %s/%s  -> %s%s" % (
            stamp, bid, (r["vendor"] or "(no vendor)")[:22], ("%.0f" % float(r["total_amount"])) if r["total_amount"] is not None else "-",
            str(r["submitted_at"] or "")[11:16], r["lane"] or "", r["kind"] or "", r["status"] or "", (r["dup_flag"] if "dup_flag" in r.keys() else "") or "-",
            ok_, dk, state, ("   !! " + "; ".join(probs)) if probs else ""))
        if probs:
            bad.append("%s: %s" % (stamp, "; ".join(probs)))
        # what a person did on it, after the scan
        for au in a.execute("SELECT at, who, action, detail FROM bill_audit WHERE bill_id=? ORDER BY rowid", (bid,)):
            w = (au["who"] or "").strip()
            person = bool(w) and not w.lower().startswith("server") and not w.startswith("S7")
            mark = ""
            if person and au["action"] not in PERSON_OK:
                mark = "   !! a person's decision"
                bad.append("%s: %s by %s (%s)" % (stamp, au["action"], w, au["at"]))
            print("        audit %s  %-24s %-22s %s%s" % (au["at"], (w or "(the reader)")[:24], au["action"], (au["detail"] or "")[:80], mark))
        if has_table(a, "scan_question"):
            for qq in a.execute("SELECT id, kind, cand_id, answer, answered_by FROM scan_question WHERE bill_id=? OR cand_id=?", (bid, bid)):
                wb = (qq["answered_by"] or "")
                by_person = qq["answer"] is not None and not wb.lower().startswith("server")
                print("        question #%d %s (cand %s) answer %s by %s%s" % (qq["id"], qq["kind"], qq["cand_id"], qq["answer"], wb or "-",
                                                                         "   !! answered by a person" if by_person else ""))
                if by_person:
                    bad.append("%s: question #%d answered by %s" % (stamp, qq["id"], wb))
    print("2  what else points at them (assets.db)")
    for t, c in REFUSE_A:
        if has_col(a, t, c):
            n = a.execute("SELECT COUNT(*) FROM %s WHERE %s IN (%s)" % (t, c, Q), IDS).fetchone()[0]
            print("   %-20s.%-14s %d" % (t, c, n))
            if n:
                bad.append("%s.%s names %d of them" % (t, c, n))
    for c in ("dup_of", "dup_cand", "challan_of", "rescan_of", "page_of"):
        if has_col(a, "bills", c):
            rows = a.execute("SELECT id, stamp_no, %s v FROM bills WHERE %s IN (%s) AND id NOT IN (%s)" % (c, c, Q, Q), IDS + IDS).fetchall()
            print("   bills.%-12s from outside: %d%s" % (c, len(rows), "".join("  [%s -> #%s]" % (x["stamp_no"], x["v"]) for x in rows)))
            if rows and c != "dup_cand":
                bad.append("an outside paper's bills.%s names one of them" % c)
    print("3  finance.db (read only; never written)")
    for t, c in FIN_REFUSE:
        if has_col(f, t, c):
            rows = [int(x[0]) for x in f.execute("SELECT %s FROM %s WHERE %s IN (%s)" % (c, t, c, Q), IDS)]
            hit = [x for x in rows if not (t == "s750_dealer_of" and x == 303)]
            print("   %-20s.%-14s %d%s" % (t, c, len(rows), (" (B-0303's dealer chosen on the Sanjeevni side: kept, it wins over the reading)" if rows and not hit else "")))
            if hit:
                bad.append("finance %s names %s" % (t, ", ".join("#%d" % x for x in sorted(set(hit)))))
    if has_col(f, "purchase_scan_state", "asset_bill_id"):
        cols = {r[1] for r in f.execute("PRAGMA table_info(purchase_scan_state)")}
        conds = [x for x, col in (("COALESCE(confirmed_by,'')<>''", "confirmed_by"), ("COALESCE(chosen_vendor,'')<>''", "chosen_vendor"), ("dup_ok IS NOT NULL", "dup_ok")) if col in cols]
        n_all = f.execute("SELECT COUNT(*) FROM purchase_scan_state WHERE asset_bill_id IN (%s)" % Q, IDS).fetchone()[0]
        n_p = f.execute("SELECT COUNT(*) FROM purchase_scan_state WHERE asset_bill_id IN (%s) AND (%s)" % (Q, " OR ".join(conds)), IDS).fetchone()[0] if conds else 0
        print("   purchase_scan_state  rows %d, a person's decision on %d  (the others: the Sanjeevni side's pairing scratch, left; kind 'Summary' leaves its register)" % (n_all, n_p))
        if n_p:
            bad.append("finance purchase_scan_state carries a person's decision on %d of them" % n_p)
    if bad:
        print("REFUSED -- nothing changed:")
        for b in bad:
            print("   - " + b)
        return 1
    if not todo:
        print("ALREADY DONE -- every paper is a Summary re-read by S754; B-0295 has its own file. Nothing to do.")
        return 0
    if not real:
        print("DRY OK -- every guard green; %d paper(s) to put right. The real line is the same without DRY=1." % len(todo))
        return 0
    # ---- 4 · the backup, then the one transaction
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = "%s.bak_S754_%s" % (adb, stamp)
    bk = sqlite3.connect(dst)
    a.backup(bk)
    bk.close()
    print("4  backup %s (%d B)" % (dst, os.path.getsize(dst)))
    at, who = now_ist(), "S754 (the owner's line)"

    def aud(bid, action, detail):
        a.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (bid, at, who, action, json.dumps(detail, ensure_ascii=False)[:500]))
    try:
        a.execute("BEGIN IMMEDIATE")
        for bid, (what, s, cur) in sorted(todo.items()):
            if what == "move" and s == "state":
                n = a.execute("UPDATE bills SET lane='pharmacy', kind='Summary', doc_kind='summary', status='captured' WHERE id=? AND lane='clinic' "
                              "AND kind='Consumable' AND status='draft'", (bid,)).rowcount
                if n != 1:
                    raise RuntimeError("#%d changed between the read and the write" % bid)
                aud(bid, "relane", {"from": "clinic", "to": "pharmacy", "status": "captured", "via": KIT})
                aud(bid, "summary", {"lane": "pharmacy", "via": "%s: a dealer's month statement (the owner, 17:27 IST 08-Nov)" % KIT})
                if has_table(a, "scan_question"):
                    a.execute("UPDATE scan_question SET answer='pharmacy', answered_by=?, answered_at=? WHERE bill_id=? AND kind='lane' AND answer IS NULL",
                              ("server (%s)" % KIT, at, bid))
            elif what == "unjoin" and s == "state":
                n = a.execute("UPDATE bills SET page_of=NULL, status='captured', reject_reason=NULL, approved_by=NULL, approved_at=NULL, kind='Summary', "
                              "doc_kind='summary' WHERE id=? AND page_of=? AND status='rejected'", (bid, HEAD[0])).rowcount
                if n != 1:
                    raise RuntimeError("#%d changed between the read and the write" % bid)
                aud(bid, "s441_page_unjoined", {"from": HEAD[0], "from_stamp": HEAD[1], "why": "a separate statement (L.K. Drug House), not B-0295's page 2", "via": KIT})
                aud(bid, "summary", {"lane": "pharmacy", "via": "%s: a dealer's month statement" % KIT})
                if has_table(a, "scan_check_s441"):
                    a.execute("UPDATE scan_check_s441 SET verdict='clear', other_id=NULL, detail=? WHERE bill_id=?", ("S754: a statement on its own, unjoined", bid))
            elif what == "kind" and s == "state":
                n = a.execute("UPDATE bills SET kind='Summary', doc_kind='summary' WHERE id=? AND lane='pharmacy' AND kind='Pharmacy' AND status='captured'", (bid,)).rowcount
                if n != 1:
                    raise RuntimeError("#%d changed between the read and the write" % bid)
                aud(bid, "summary", {"lane": "pharmacy", "via": "%s: a dealer's month statement (the owner, 17:27 IST 08-Nov)" % KIT})
            elif what == "head":
                n = a.execute("UPDATE bills SET source_stored=? WHERE id=? AND source_stored=?", (s, bid, cur)).rowcount
                if n != 1:
                    raise RuntimeError("B-0295's file changed between the read and the write")
                aud(bid, "s441_page_unmerged", {"back_to": s, "was": cur, "page": 296, "via": KIT})
        a.commit()
    except Exception as e:                                           # noqa: BLE001
        a.rollback()
        print("!! %s -- rolled back, nothing changed (the backup above is a spare)" % repr(e)[:200])
        return 1
    print("5  the rows put right in one transaction: %s" % ", ".join("#%d %s" % (b, todo[b][0]) for b in sorted(todo)))
    a.close()
    # ---- 6 · the re-reads, one by one, through the app's own reading
    here = os.path.dirname(os.path.abspath(adb))
    os.environ["ASSETS_DB"] = adb
    os.environ["ASSETS_UPLOADS"] = up
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import claude_reader as CR                                   # noqa: E402
        import asset_register as AR                                  # noqa: E402
    except Exception as e:                                           # noqa: BLE001
        print("!! the app could not be loaded (%s) -- the rows are put right; the re-reads are not done. Run the same line again." % type(e).__name__)
        return 1
    if getattr(CR, "KIT_S754", "") != KIT or getattr(AR, "KIT_S754", "") != KIT:
        print("!! the reader / the app on the box are not S754's -- the re-reads are not done. Run the same line again after the install.")
        return 1
    a = sqlite3.connect(adb, timeout=30)
    a.row_factory = sqlite3.Row
    left = 0
    for bid in [t[0] for t in TARGETS if t[0] in todo]:
        r = a.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        if r is None or not placed(r):
            print("   #%d is not a captured Summary on the pharmacy lane now -- not re-read" % bid)
            left += 1
            continue
        path = os.path.join(up, r["source_stored"] or "")
        data = CR.read_summary(path, bid=bid, db_path=adb)
        if not data or data.get("is_summary") is False:
            print("   %s #%d  !! the reader %s -- left as it is; run the same line again later" % (r["stamp_no"], bid,
                  "says this is not a summary" if data else "could not finish (busy, the day's limit, or off)"))
            left += 1
            continue
        a.execute("UPDATE bills SET vendor=NULL, bill_no=NULL, bill_date=NULL, total_amount=NULL, ocr_status='reading' WHERE id=?", (bid,))
        a.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
                  (bid, now_ist(), "S754 (the owner's line)", "reread_summary",
                   json.dumps({"was": {"vendor": r["vendor"], "bill_no": r["bill_no"], "bill_date": r["bill_date"], "total": r["total_amount"]}}, ensure_ascii=False)[:500]))
        a.commit()
        st = AR._bg_extract(bid, path, _reading=CR.summary_to_bill(data))
        r2 = a.execute("SELECT vendor, bill_date, total_amount, kind, lane, status, late_for FROM bills WHERE id=?", (bid,)).fetchone()
        nb = len([x for x in data.get("lines") or [] if x.get("kind") == "bill"])
        print("   %s #%d  re-read: dealer %s · %s .. %s (%s) · %d bill line(s) · figure %s  -> row: %s, %s, %s/%s/%s, ocr %s" % (
            r["stamp_no"], bid, data.get("dealer") or "(none printed -- found from the bills on the Sanjeevni side)", data.get("period_from"), data.get("period_to"),
            data.get("period_by"), nb, data.get("closing") if data.get("closing") is not None else data.get("total_bills"),
            r2["vendor"] or "(no vendor)", r2["bill_date"], r2["kind"], r2["lane"], r2["status"], st))
    print("%s: %s" % (KIT, "DONE." if not left else "%d re-read(s) still to do -- run the same line again." % left))
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
