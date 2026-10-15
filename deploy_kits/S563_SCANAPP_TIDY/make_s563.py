#!/usr/bin/env python3
"""make_s563.py -- S563_SCANAPP_TIDY: the five edited files rebuilt from the pinned live bytes.

    python3 make_s563.py <dir with the live sorting_desk.py, clinic_papers.py, asset_register.py, asset_machine.py,
                          scanner_widget.js> <out dir> [--cp-item3-only]

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. Every byte of each built file comes from the live file plus these edits. No new file on the box,
no new column, no data step.
--cp-item3-only: clinic_papers.py with item 3 (NEW1) only, not the tidy (item 12) -- the walk's byte-identical fetch swaps
this file with the TO file (the other four files at TO), so the tidy is proven to change no byte a page serves."""
import hashlib, os, sys

FROM = {"sorting_desk.py": "a4623438f068d8e691b797482bd942ab",
        "clinic_papers.py": "88963eacee217e051ae07091648a46d7",
        "asset_register.py": "9daed9ea4f2a87e40b43711e472e701f",
        "asset_machine.py": "0caec41e655cfd51c2eaf9176ee33365",
        "scanner_widget.js": "1128ac975ba2543e1fe9edf7c721d4f8"}

# ============================================================================================ sorting_desk.py
SD_EDITS = [
    # SD1 -- the mark
    ("RECEIPTS = \"S560\"             # S560_RECEIPTS_STATEMENTS: Receipt and Statement (never spend), one payment record, the desk on one screen\n",
     "RECEIPTS = \"S560\"             # S560_RECEIPTS_STATEMENTS: Receipt and Statement (never spend), one payment record, the desk on one screen\n"
     "TIDY = \"S563\"                 # S563_SCANAPP_TIDY: Restore a set-aside paper (F-902), never straight to accepted, the statement's order\n", 1),
    # SD2 (item 11, S560-N13) -- the three "append-only" comments say what the code does now
    ("    # S560 item 5: ONE payment record, append-only (a mistake is voided); every bill reference with its fingerprint (S557)\n",
     "    # S560 item 5: ONE payment record per paper -- a re-save updates it in place (FIX1 B1; the old values kept in payment_changed),\n"
     "    # a mistake is voided; every bill reference with its fingerprint (S557)\n", 1),
    ("# marked paid directly. ONE payment record (paper_payment + paper_payment_bill), append-only (a mistake is voided), every bill\n",
     "# marked paid directly. ONE payment record (paper_payment + paper_payment_bill) -- a re-save updates it in place, the old values\n"
     "# kept in payment_changed (FIX1 B1); a mistake is voided -- every bill\n", 1),
    ("    \"\"\"ONE payment (append-only): paper_payment + one paper_payment_bill per bill it pays, each with the bill's fingerprint;\n",
     "    \"\"\"ONE new payment (a re-save goes through _s560_update_payment instead: in place, never a second): paper_payment + one\n"
     "    paper_payment_bill per bill it pays, each with the bill's fingerprint;\n", 1),
    # SD3 (item 9, S560-N2) -- the receipt / statement words never matched on item names
    ("def _s560_claude_kind(db, b, rd):\n",
     "def _s563_words_text(b, rd):\n"
     "    \"\"\"S563 (S560-N2): what the receipt / statement words are matched on -- the vendor, the bill number and Claude's supplier\n"
     "    and number only, never an item name (a 'Receipt book' line on a stationery bill is goods, not a receipt). _s560_text, which\n"
     "    _s560_prefill also reads for cash / cheque / UTR, is unchanged.\"\"\"\n"
     "    bits = [b[\"vendor\"] or \"\", b[\"bill_no\"] or \"\"]\n"
     "    if rd:\n"
     "        bits += [str(rd.get(\"supplier\") or \"\"), str(rd.get(\"number\") or \"\")]\n"
     "    return re.sub(r\"\\s+\", \" \", \" ; \".join(bits).lower()).strip()\n"
     "\n\n"
     "def _s560_claude_kind(db, b, rd):\n", 1),
    ("    or statement kind) -- otherwise nothing is pre-chosen (blocked=True). Else the reader's kind as before.\"\"\"\n"
     "    t = _s560_text(db, b, rd)\n",
     "    or statement kind) -- otherwise nothing is pre-chosen (blocked=True). Else the reader's kind as before.\"\"\"\n"
     "    t = _s563_words_text(b, rd)                                     # S563 (S560-N2): never the item names\n", 1),
    ("    if CP._hits(_s560_text(db, b, rd), list(RECEIPT_WORDS)):\n",
     "    if CP._hits(_s563_words_text(b, rd), list(RECEIPT_WORDS)):     # S563 (S560-N2)\n", 1),
    ("    if CP._hits(_s560_text(db, b, rd), list(STATEMENT_WORDS)):\n",
     "    if CP._hits(_s563_words_text(b, rd), list(STATEMENT_WORDS)):   # S563 (S560-N2)\n", 1),
    # SD4 (item 5, S560-N4) -- a statement pays the invoices that have a total first; a no-total one only what is left
    ("            for row in sorted(s.get(\"covers\") or [], key=lambda r_: ((_s560_day(r_) or _today()), r_[\"id\"])):\n",
     "            byday = sorted(s.get(\"covers\") or [], key=lambda r_: ((_s560_day(r_) or _today()), r_[\"id\"]))\n"
     "            nototal = [r_ for r_ in byday if r_[\"total_amount\"] is None]      # S563 (S560-N4): the invoices with a total first\n"
     "            for row in [r_ for r_ in byday if r_[\"total_amount\"] is not None] + nototal:\n", 1),
    ("            msgs.append(\"%d invoice%s marked paid by this statement.\" % (len(allocs), \"\" if len(allocs) == 1 else \"s\"))\n",
     "            msgs.append(\"%d invoice%s marked paid by this statement.\" % (len(allocs), \"\" if len(allocs) == 1 else \"s\"))\n"
     "            if nototal:                                                 # S563 (S560-N4): said\n"
     "                msgs.append(_s563_nototal_line(nototal, [(r_, a_) for r_, a_ in allocs if r_[\"total_amount\"] is None]))\n", 1),
    # SD5 (items 1, 2: F-902, S560-N3) -- the paper's "Already set aside on ... — Restore?"
    ("    return {\"pay\": st, \"fix\": ({\"key\": f[0], \"text\": f[1]} if f else None), \"to_acc\": bool(_col(b, \"to_accountant\")),\n",
     "    return {\"pay\": st, \"fix\": ({\"key\": f[0], \"text\": f[1]} if f else None), \"aside\": _s563_aside(b, f),      # S563 F-902\n"
     "            \"to_acc\": bool(_col(b, \"to_accountant\")),\n", 1),
    ("    if b[\"status\"] == \"rejected\" and not aside:\n        raise DeskError(\"%s is rejected; it stays where it is.\" % st)\n",
     "    if b[\"status\"] == \"rejected\" and not aside:\n"
     "        raise DeskError(\"%s is set aside. Press Restore on it first, then Save.\" % st)      # S563 F-902\n", 1),
    # SD6 (items 1, 2) -- the blank fix's restore goes through the one shared restore; status_from is no longer read
    ("        if ans == \"restore\":\n"
     "            r = db.execute(\"SELECT detail FROM bill_audit WHERE bill_id=? AND action='desk_blank' ORDER BY id DESC LIMIT 1\", (bid,)).fetchone()\n"
     "            try:\n"
     "                back = json.loads(r[0] or \"{}\").get(\"status_from\") if r else None\n"
     "            except (TypeError, ValueError):\n"
     "                back = None\n"
     "            if back not in (\"draft\", \"approved\", \"captured\"):\n"
     "                back = AR._lane_kind_status(_lane(b))[1]\n"
     "            db.execute(\"UPDATE bills SET status=?, reject_reason=NULL%s WHERE id=?\" % (\"\" if back == \"approved\" else \", approved_by=NULL, approved_at=NULL\"),\n"
     "                       (back, bid))\n"
     "            AR._audit_bill(db, bid, \"desk_blank_restored\", {\"status_from\": \"rejected\", \"status\": back, \"reject_reason\": b[\"reject_reason\"],\n"
     "                                                            \"approved_by\": b[\"approved_by\"], \"approved_at\": b[\"approved_at\"], \"lane\": _lane(b), \"via\": \"desk\"})\n"
     "            msg = \"%s is back on its lane as it was (%s). Sort it now.\" % (_stamp(b), back)\n",
     "        if ans == \"restore\":\n"
     "            back = _s563_restore(db, b, \"blank\")                        # S563: the one shared restore -- never straight to accepted\n"
     "            msg = \"%s is back on its lane (%s). Sort it now — its Save accepts it as usual.\" % (_stamp(b), back)\n", 1),
    # SD7 (item 1) -- the helpers and the route, before the S560 block's end
    ("# --- S560_RECEIPTS_STATEMENTS end ---\n",
     "# --- S560_RECEIPTS_STATEMENTS end ---\n"
     "\n\n"
     "# ---------------------------------------------------------------------------------------------- S563_SCANAPP_TIDY\n"
     "def _s563_aside_day(b):\n"
     "    \"\"\"The day a paper was set aside: approved_at, which every set-aside path writes at that moment (IST); else the day it\n"
     "    was scanned (created_at, UTC, shown in IST).\"\"\"\n"
     "    if _iso(_col(b, \"approved_at\")):\n"
     "        return _dmy(b[\"approved_at\"])\n"
     "    try:\n"
     "        t = datetime.datetime.strptime(str(b[\"created_at\"])[:19], \"%Y-%m-%d %H:%M:%S\") + datetime.timedelta(minutes=330)\n"
     "        return t.strftime(\"%d-%m-%Y\")\n"
     "    except (TypeError, ValueError):\n"
     "        return _dmy(b[\"created_at\"])\n"
     "\n\n"
     "def _s563_aside(b, f=None):\n"
     "    \"\"\"S563 (F-902): a paper set aside (status 'rejected') that is not a joined page (page_of) and not an S441 double scan\n"
     "    (dup_of) shows ONE line, 'Already set aside on dd-mm-yyyy — Restore?', and a Restore button. Not while the blank fix's\n"
     "    line shows (f = ('blank', ..)): one Restore button serves both. Never depends on desk_fix_answered. Else None.\"\"\"\n"
     "    if b is None or b[\"status\"] != \"rejected\" or b[\"page_of\"] or b[\"dup_of\"] or (f and f[0] == \"blank\"):\n"
     "        return None\n"
     "    return {\"text\": \"Already set aside on %s — Restore?\" % _s563_aside_day(b)}\n"
     "\n\n"
     "def _s563_restore(db, b, via):\n"
     "    \"\"\"S563: THE restore of a paper set aside -- F-902's line ('aside') and the blank fix ('blank'). The status a fresh paper\n"
     "    on its lane has (AR._lane_kind_status: clinic draft, the other lanes captured), never straight back to approved (S560-N3:\n"
     "    the next Save runs the normal accept, with its duplicate check); reject_reason, approved_by and approved_at cleared; lane,\n"
     "    subgroup, kind, doc_kind, pe_who and challan_state kept as they are (D664). Audited: who, when, from what. Refuses a page\n"
     "    and a double scan. No commit (the route commits once). Returns the status.\"\"\"\n"
     "    st = _stamp(b)\n"
     "    if b[\"status\"] != \"rejected\":\n"
     "        raise DeskError(\"%s is not set aside.\" % st)\n"
     "    if b[\"page_of\"]:\n"
     "        raise DeskError(\"%s is a page of another paper — open that paper.\" % st)\n"
     "    if b[\"dup_of\"]:\n"
     "        raise DeskError(\"%s is set aside as a second scan — answer that question on it instead.\" % st)\n"
     "    back = AR._lane_kind_status(_lane(b))[1]\n"
     "    db.execute(\"UPDATE bills SET status=?, reject_reason=NULL, approved_by=NULL, approved_at=NULL WHERE id=? AND status='rejected'\",\n"
     "               (back, b[\"id\"]))\n"
     "    AR._audit_bill(db, b[\"id\"], \"desk_blank_restored\" if via == \"blank\" else \"desk_restored\",\n"
     "                   {\"status_from\": \"rejected\", \"status\": back, \"reject_reason\": b[\"reject_reason\"], \"approved_by\": b[\"approved_by\"],\n"
     "                    \"approved_at\": b[\"approved_at\"], \"lane\": _lane(b), \"by\": _who(), \"at\": AR._now_ist(), \"via\": \"desk \" + via})\n"
     "    return back\n"
     "\n\n"
     "def _s563_nototal_line(nototal, got):\n"
     "    \"\"\"S563 (S560-N4): the Save's words when a statement covers an invoice that has no total.\"\"\"\n"
     "    st = \", \".join(_stamp(r_) for r_ in nototal)\n"
     "    one = len(nototal) == 1\n"
     "    if got:\n"
     "        return \"%s %s no total: only what was left after the invoices with a total went to %s (%s).\" % (\n"
     "            st, \"has\" if one else \"have\", \"it\" if one else \"them\", _inr(sum(a_ for _r, a_ in got)))\n"
     "    return \"%s %s no total: nothing was left for %s after the invoices with a total.\" % (st, \"has\" if one else \"have\", \"it\" if one else \"them\")\n"
     "\n\n"
     "def restore_answer():\n"
     "    \"\"\"POST /desk/api/restore {id}: S563 (F-902) -- 'Already set aside on ... — Restore?'. The paper must be one this person\n"
     "    may open (_visible: a Personal paper is the owner's alone). Neither reads nor writes desk_fix_answered.\"\"\"\n"
     "    db = AR.get_db()\n"
     "    p = request.get_json(silent=True) or {}\n"
     "    try:\n"
     "        bid = int(p.get(\"id\"))\n"
     "    except (TypeError, ValueError):\n"
     "        return jsonify(ok=False, error=\"No paper was given.\"), 400\n"
     "    b = _row(db, bid)\n"
     "    err = _visible(b, _owner())\n"
     "    if err:\n"
     "        return jsonify(ok=False, error=err), (404 if not b else 403)\n"
     "    try:\n"
     "        back = _s563_restore(db, b, \"aside\")\n"
     "        db.commit()\n"
     "    except DeskError as e:\n"
     "        db.rollback()\n"
     "        return jsonify(ok=False, error=str(e)), e.code\n"
     "    except Exception as e:                                           # noqa: BLE001\n"
     "        db.rollback()\n"
     "        return jsonify(ok=False, error=\"Not saved (%s). Nothing was changed.\" % type(e).__name__), 500\n"
     "    return jsonify(ok=True, message=\"%s is back on its lane (%s). Sort it now — its Save files it as usual.\" % (_stamp(b), back), id=bid)\n"
     "\n\n"
     "# --- S563_SCANAPP_TIDY end ---\n", 1),
    ("    app.add_url_rule(\"/desk/api/payment/void\", \"s560_void\", cr(_gate(pay_void)), methods=[\"POST\"])         # S560 item 5\n",
     "    app.add_url_rule(\"/desk/api/payment/void\", \"s560_void\", cr(_gate(pay_void)), methods=[\"POST\"])         # S560 item 5\n"
     "    app.add_url_rule(\"/desk/api/restore\", \"s563_restore\", cr(_gate(restore_answer)), methods=[\"POST\"])     # S563 F-902\n", 1),
    ("           \"fix\": url_for(\"s560_fix\"), \"void\": url_for(\"s560_void\"), \"modes\": [list(m) for m in PAY_MODES],\n",
     "           \"fix\": url_for(\"s560_fix\"), \"void\": url_for(\"s560_void\"), \"restore\": url_for(\"s563_restore\"), \"modes\": [list(m) for m in PAY_MODES],\n", 1),
    # SD8 (item 1) -- the desk's script: the line, Save held until Restore, the button
    ("function fixb(j){if(!j.fix){return '';}var k=j.fix.key,h=",
     "function fixb(j){if(!j.fix){return j.aside?'<div class=flag id=s563aside><b>'+esc(j.aside.text)+'</b><br><button type=button class=b data-restore=1>Restore</button></div>':'';}var k=j.fix.key,h=", 1),
    ("function s560why(){var j=S.cur;if(j.fix&&j.fix.key=='blank'&&j.status=='set aside'){return 'Restore it first (above)';}\n",
     "function s560why(){var j=S.cur;if(j.fix&&j.fix.key=='blank'&&j.status=='set aside'){return 'Restore it first (above)';}if(j.aside&&j.status=='set aside'){return 'Restore it first (above)';}\n", 1),
    ("e.target.closest('[data-fix],[data-void],[data-s560k],[data-rc],[data-mode],[data-stt],#morecue'):null;if(!t||!S.cur){return;}var j=S.cur;\n"
     " if(t.id=='morecue'){$('fields').scrollTop=$('fields').scrollHeight;return;}\n",
     "e.target.closest('[data-fix],[data-restore],[data-void],[data-s560k],[data-rc],[data-mode],[data-stt],#morecue'):null;if(!t||!S.cur){return;}var j=S.cur;\n"
     " if(t.id=='morecue'){$('fields').scrollTop=$('fields').scrollHeight;return;}\n"
     " if(t.hasAttribute('data-restore')){jpost(C.restore,{id:j.id}).then(function(x){if(!x.ok){$('err').textContent=x.error||'Not saved.';return;}$('savednote').textContent=x.message;loadList(j.id);});return;}\n", 1),
]

# ============================================================================================ clinic_papers.py
CP_ITEM3 = [
    # CP1 -- the mark
    ("RECEIPTS = \"S560\"            # S560: a receipt / statement is never a purchase, never accepted\n",
     "RECEIPTS = \"S560\"            # S560: a receipt / statement is never a purchase, never accepted\n"
     "TIDY = \"S563\"                # S563: Bills awaited filters a patient's / Personal challan as the desk does; consolidated\n", 1),
    # CP2 (item 3, NEW1) -- the old Bills awaited page: the desk's two filters, in place (the desk is never called)
    ("def challans_awaiting(db):\n    if not _has_challans(db):\n        return []\n"
     "    return db.execute(\"SELECT b.* FROM bills b WHERE b.doc_kind='challan' AND COALESCE(b.challan_state,'awaiting')='awaiting' \"\n"
     "                      \"AND b.status<>'rejected' AND b.dup_of IS NULL ORDER BY b.id DESC\").fetchall()\n",
     "def _s563_who_sees(owner=None, alias=\"b\"):\n"
     "    \"\"\"S563 (NEW1): the two filters sorting_desk.awaiting_challans has had since S551 (C2 / C4), as an SQL tail -- never a\n"
     "    patient's paper, for anyone; never a Personal paper, for anyone but the owner. owner None -> the person signed in (outside a\n"
     "    request: not the owner).\"\"\"\n"
     "    if owner is None:\n"
     "        try:\n"
     "            owner = bool(AR.is_owner())\n"
     "        except Exception:                                            # noqa: BLE001\n"
     "            owner = False\n"
     "    w = \" AND COALESCE(%s.subgroup,'')<>'patient_paper'\" % alias\n"
     "    if not owner:\n"
     "        w += \" AND COALESCE(%s.subgroup,'')<>'personal'\" % alias\n"
     "    return w\n"
     "\n\n"
     "def challans_awaiting(db, owner=None):\n"
     "    \"\"\"The challans waiting for their bill, newest first; pharmacy challans stay listed (the page hands them on). S563 (NEW1):\n"
     "    filtered in place by _s563_who_sees -- this page is the door when the desk is off, so the desk's helper is not called.\"\"\"\n"
     "    if not _has_challans(db):\n        return []\n"
     "    return db.execute(\"SELECT b.* FROM bills b WHERE b.doc_kind='challan' AND COALESCE(b.challan_state,'awaiting')='awaiting' \"\n"
     "                      \"AND b.status<>'rejected' AND b.dup_of IS NULL\" + _s563_who_sees(owner) + \" ORDER BY b.id DESC\").fetchall()\n", 1),
    ("    amber = _amber_days(db)\n    rows = []\n",
     "    amber = _amber_days(db)\n    sees = _s563_who_sees()                                          # S563 (NEW1)\n    rows = []\n", 1),
    ("                                \"AND COALESCE(b.lane,'clinic')<>'pharmacy' ORDER BY b.id DESC LIMIT 400\", (c[\"id\"],)):\n",
     "                                \"AND COALESCE(b.lane,'clinic')<>'pharmacy'\" + sees + \" ORDER BY b.id DESC LIMIT 400\", (c[\"id\"],)):\n", 1),
    ("b.challan_state IN ('closed','deleted','joined') ORDER BY b.id DESC LIMIT 40\").fetchall() if _has_challans(db) else []\n",
     "b.challan_state IN ('closed','deleted','joined')\" + sees + \" ORDER BY b.id DESC LIMIT 40\").fetchall() if _has_challans(db) else []\n", 1),
]
CP_TIDY = [
    # CP3 (item 12) -- a current header docstring
    ("\"\"\"clinic_papers.py -- S464_CLINIC_PAPERS + S465_PAPERS_JOIN + S466_EXPENSE_WARRANTY (D664, the owner 03-Oct-2026).\n",
     "\"\"\"clinic_papers.py -- the clinic's papers: S464-S466 (D664, the owner 03-Oct-2026), S530 (D710), S531, S532, S544, S551,\n"
     "S559, S560 and S563 (consolidated: the header below is current; every rule of the earlier kits stands).\n", 1),
    ("\nWHAT IT DELIBERATELY DOES NOT DO\n",
     "    S531 -- CHALLANS (D689 item 2): a challan is never counted as a purchase -- the bill is. GET /papers/challans (Bills\n"
     "        awaited), POST /papers/challans/<id>/close and /delete; a bill's page offers the join of its supplier's challans.\n"
     "    S532 -- THE SYSTEM SENDS A SCAN HOME: from the supplier's earlier papers that a person placed (auto_home, heal_auto);\n"
     "        a section is never guessed (D664).\n"
     "    S544 -- PERSONAL EXPENSES (D719): Dr MK / Dr Bhawna on a personal expense (POST /papers/<id>/pe_who); a Personal paper\n"
     "        is the owner's alone (F-891).\n"
     "    S551 -- THE SORTING DESK (sorting_desk.py) shares this file's join (join_pages), its sections and its suggestion; the\n"
     "        desk's own sections (implant stock, clinic equipment, a patient's paper) are kept apart from the consumables.\n"
     "    S559 -- ONE ROAD: every paper row leads to the desk; this file's pages stay reachable by address with their banners.\n"
     "    S560 -- RECEIPTS AND STATEMENTS are never a purchase and never accepted (_live, _live_sections, _accept, heal).\n"
     "    S563 -- Bills awaited filters as the desk does (never a patient's paper; Personal for the owner only); the three\n"
     "        'live' filters share one tail (_tail).\n"
     "\nWHAT IT DELIBERATELY DOES NOT DO\n", 1),
    # CP4 (item 12) -- one shared tail for _live, _live_sort, _live_sections (_live_sort excludes only challans, kept)
    ("def _cols(db):\n    return {r[1] for r in db.execute(\"PRAGMA table_info(bills)\")}\n",
     "def _cols(db):\n    return {r[1] for r in db.execute(\"PRAGMA table_info(bills)\")}\n"
     "\n\n"
     "def _tail(db, alias, kinds):\n"
     "    \"\"\"S563: the shared tail of _live, _live_sort and _live_sections -- the paper kinds that are never a purchase (S531\n"
     "    challan; S560 receipt / statement; _live_sort passes the challan alone) and never a page joined into another. The bills\n"
     "    columns are read once.\"\"\"\n"
     "    cols = _cols(db)\n"
     "    w = \"\"\n"
     "    if \"doc_kind\" in cols:\n"
     "        if len(kinds) == 1:\n"
     "            w += \" AND COALESCE(%s.doc_kind,'bill')<>'%s'\" % (alias, kinds[0])\n"
     "        else:\n"
     "            w += \" AND COALESCE(%s.doc_kind,'bill') NOT IN (%s)\" % (alias, \",\".join(\"'%s'\" % k for k in kinds))\n"
     "    if \"page_of\" in cols:\n"
     "        w += \" AND %s.page_of IS NULL\" % alias\n"
     "    return w\n", 1),
    ("         % (alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill') NOT IN ('challan','receipt','statement')\" % alias      # S531; S560: nor a receipt / statement\n"
     "    if \"page_of\" in _cols(db):\n"
     "        w += \" AND %s.page_of IS NULL\" % alias\n"
     "    return w\n",
     "         % (alias, alias, alias))\n"
     "    return w + _tail(db, alias, (\"challan\", \"receipt\", \"statement\"))      # S531; S560: nor a receipt / statement\n", 1),
    ("         \" AND %s.dup_of IS NULL\" % (alias, alias, alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill')<>'challan'\" % alias                     # S531: a challan is not a purchase\n"
     "    if \"page_of\" in _cols(db):\n"
     "        w += \" AND %s.page_of IS NULL\" % alias\n"
     "    return w\n",
     "         \" AND %s.dup_of IS NULL\" % (alias, alias, alias, alias, alias))\n"
     "    return w + _tail(db, alias, (\"challan\",))                      # S531: a challan is not a purchase (only the challan here)\n", 1),
    ("         \" AND %s.dup_of IS NULL\" % (alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill') NOT IN ('challan','receipt','statement')\" % alias      # S531; S560: nor a receipt / statement\n"
     "    if \"page_of\" in _cols(db):\n"
     "        w += \" AND %s.page_of IS NULL\" % alias\n"
     "    return w\n",
     "         \" AND %s.dup_of IS NULL\" % (alias, alias, alias))\n"
     "    return w + _tail(db, alias, (\"challan\", \"receipt\", \"statement\"))      # S531; S560: nor a receipt / statement\n", 1),
]

# ============================================================================================ asset_register.py
AR_EDITS = [
    # AR1 -- the mark
    ("RECEIPTS_S560 = \"S560\"\n",
     "RECEIPTS_S560 = \"S560\"\n"
     "TIDY_S563 = \"S563\"             # S563_SCANAPP_TIDY: the owner's Delete voids the payment a paper proves; an old AMC's renewal date\n", 1),
    # AR2 (item 4, NEW2 + S557-K2-N2) -- the owner's Delete of a paper
    ("def bill_delete(bid):\n"
     "    db = get_db()\n"
     "    db.execute(\"DELETE FROM bill_items WHERE bill_id=?\", (bid,))\n"
     "    db.execute(\"DELETE FROM bills WHERE id=?\", (bid,))\n"
     "    db.commit()\n"
     "    flash(\"Bill deleted.\")\n"
     "    return redirect(url_for(\"bills_list\"))\n",
     "def bill_delete(bid):\n"
     "    db = get_db()\n"
     "    # S563 (NEW2 + S557-K2-N2): in ONE transaction -- every live payment this paper proves is voided with its allocations (the\n"
     "    # desk's own helpers, through sys.modules), so the bill a deleted receipt paid reads unpaid again; assets.bill_id is cleared\n"
     "    # where it pointed here; one 'paper_deleted' audit row. Refused, nothing changed, when the desk module is not loaded.\n"
     "    b = db.execute(\"SELECT * FROM bills WHERE id=?\", (bid,)).fetchone()\n"
     "    if b is not None:\n"
     "        _sd = _sys.modules.get(\"sorting_desk\")\n"
     "        if _sd is None or not hasattr(_sd, \"_s560_void_own\") or not hasattr(_sd, \"_s560_void_allocs\"):\n"
     "            flash(\"%s was not deleted: the sorting desk is not loaded, and it is what voids a payment the paper proves. \"\n"
     "                  \"Nothing was changed.\" % (b[\"stamp_no\"] or \"#%d\" % bid))\n"
     "            return redirect(url_for(\"bill_view\", bid=bid))\n"
     "        try:\n"
     "            try:\n"
     "                pays = db.execute(\"SELECT * FROM paper_payment WHERE proof_bill_id=? AND proof_created_at=? AND voided_at='' ORDER BY id\",\n"
     "                                  (bid, b[\"created_at\"] or \"\")).fetchall()\n"
     "            except sqlite3.OperationalError:\n"
     "                pays = []\n"
     "            for _p in pays:\n"
     "                _sd._s560_void_own(db, _p, b, \"paper deleted\")\n"
     "                _sd._s560_void_allocs(db, _p[\"id\"])\n"
     "            _na = db.execute(\"UPDATE assets SET bill_id=NULL WHERE bill_id=?\", (bid,)).rowcount\n"
     "            _audit_bill(db, bid, \"paper_deleted\", {\"stamp\": b[\"stamp_no\"], \"created_at\": b[\"created_at\"],\n"
     "                                                  \"payments_voided\": [_p[\"id\"] for _p in pays], \"assets_cleared\": _na})\n"
     "            db.execute(\"DELETE FROM bill_items WHERE bill_id=?\", (bid,))\n"
     "            db.execute(\"DELETE FROM bills WHERE id=?\", (bid,))\n"
     "            db.commit()\n"
     "        except Exception as _ex:                                      # noqa: BLE001\n"
     "            db.rollback()\n"
     "            flash(\"Not deleted (%s). Nothing was changed.\" % type(_ex).__name__)\n"
     "            return redirect(url_for(\"bill_view\", bid=bid))\n"
     "        flash(\"Bill deleted.\" + (\" Its payment record is voided (kept on record) — the bill it paid reads unpaid again.\" if pays else \"\"))\n"
     "        return redirect(url_for(\"bills_list\"))\n"
     "    db.execute(\"DELETE FROM bill_items WHERE bill_id=?\", (bid,))\n"
     "    db.execute(\"DELETE FROM bills WHERE id=?\", (bid,))\n"
     "    db.commit()\n"
     "    flash(\"Bill deleted.\")\n"
     "    return redirect(url_for(\"bills_list\"))\n", 1),
    # AR3 (item 8, S559-K1-N6(i)) -- the PM sentence: an old AMC / CMC whose own Contract renewal date is past is not covered
    ("        print(\"S559 pm: %s\" % _ex, file=_sys.stderr)\n"
     "    try:\n"
     "        return (a[\"contract_type\"] or \"\").strip() in (\"AMC\", \"CMC\")\n"
     "    except (IndexError, KeyError):\n"
     "        return False\n",
     "        print(\"S559 pm: %s\" % _ex, file=_sys.stderr)\n"
     "    try:\n"
     "        if (a[\"contract_type\"] or \"\").strip() not in (\"AMC\", \"CMC\"):\n"
     "            return False\n"
     "    except (IndexError, KeyError):\n"
     "        return False\n"
     "    try:                                                          # S563 (S559-K1-N6(i)): its own renewal date past -> lapsed\n"
     "        _m = _s557_mod()\n"
     "        if _m is not None and hasattr(_m, \"old_renewal\"):\n"
     "            _rn = _m.old_renewal(get_db(), a)\n"
     "            if _rn is not None and _rn < _m._today():\n"
     "                return False\n"
     "    except Exception as _ex:                                      # noqa: BLE001\n"
     "        print(\"S563 pm: %s\" % _ex, file=_sys.stderr)\n"
     "    return True\n", 1),
]

# ============================================================================================ asset_machine.py
AM_EDITS = [
    # AM1 -- the mark
    ("TODAY = None                  # the walk sets a made-up day here\n",
     "TODAY = None                  # the walk sets a made-up day here\n"
     "TIDY = \"S563\"                 # S563_SCANAPP_TIDY: one machine per paper under a lock; the stamp box refuses a copy / a page; old AMC lapses\n", 1),
    # AM2 (item 7, S557-K1-N6) -- the stamp box refuses a copy or a page (refusal() unchanged: it also drives three displays)
    ("    why = refusal(b, owner)\n    if why:\n        raise Refused(why + \" Nothing was saved.\")\n    return b[\"id\"]\n",
     "    why = refusal(b, owner)\n    if why:\n        raise Refused(why + \" Nothing was saved.\")\n"
     "    if _col(b, \"dup_of\") or _col(b, \"page_of\"):                     # S563 (S557-K1-N6): a copy or a page -> the real paper\n"
     "        of = db.execute(\"SELECT id, stamp_no FROM bills WHERE id=?\", (b[\"dup_of\"] or b[\"page_of\"],)).fetchone()\n"
     "        os_ = _stamp(of) if of is not None else \"another paper\"\n"
     "        raise Refused(\"This paper is %s %s — open %s instead. Nothing was saved.\" % (\"a copy of\" if b[\"dup_of\"] else \"a page of\", os_, os_))\n"
     "    return b[\"id\"]\n", 1),
    # AM3 (item 8, S559-K1-N6(i)) -- the old record's own Contract renewal date
    ("            prov = (_col(a, \"provider\") or \"\").strip()\n"
     "            return \"Covered (old record): %s%s\" % (ct, (\" — \" + prov) if prov else \"\"), \"\"\n",
     "            prov = (_col(a, \"provider\") or \"\").strip()\n"
     "            txt = \"Covered (old record): %s%s\" % (ct, (\" — \" + prov) if prov else \"\")\n"
     "            rn = old_renewal(db, a)                                  # S563 (S559-K1-N6(i)): its own renewal date past -> lapsed\n"
     "            if rn is not None and rn < today:\n"
     "                return \"%s — lapsed on %s\" % (txt, rn.strftime(\"%d-%m-%Y\")), \"red\"\n"
     "            return txt, \"\"\n", 1),
    ("def live_amc(db, a, today=None):\n",
     "def old_renewal(db, a):\n"
     "    \"\"\"S563 (S559-K1-N6(i)): the old record's own Contract renewal date -- the latest expiries row labelled 'Contract renewal'\n"
     "    for this machine -- as a date, or None.\"\"\"\n"
     "    try:\n"
     "        r = db.execute(\"SELECT MAX(due_date) FROM expiries WHERE entity='asset' AND entity_id=? AND label='Contract renewal'\", (a[\"id\"],)).fetchone()\n"
     "    except sqlite3.Error:\n"
     "        return None\n"
     "    return _iso(r[0]) if (r and r[0]) else None\n"
     "\n\n"
     "def live_amc(db, a, today=None):\n", 1),
    # AM4 (item 6, S557-K1-N9) -- a second tap gets the machine the first made, never a new one
    ("            cur = db.execute(\"INSERT INTO assets(name, location_id, category, purchase_date, price, vendor, serial_no, status, contract_type, \"\n",
     "            own = not db.in_transaction                             # S563 (S557-K1-N9): checked again under the write lock\n"
     "            if own:\n"
     "                db.execute(\"BEGIN IMMEDIATE\")\n"
     "            again = db.execute(\"SELECT id FROM assets WHERE bill_id=? ORDER BY id LIMIT 1\", (bid,)).fetchone()\n"
     "            if again:\n"
     "                db.rollback()\n"
     "                flash(\"%s is already the purchase bill of this machine.\" % _stamp(b))\n"
     "                return redirect(url_for(\"asset_view\", aid=again[0]))\n"
     "            cur = db.execute(\"INSERT INTO assets(name, location_id, category, purchase_date, price, vendor, serial_no, status, contract_type, \"\n", 1),
]

# ============================================================================================ scanner_widget.js
JS_EDITS = [
    # JS1 (item 10, S559-K2-N7 + the stage label) -- inside the intake-only cvScanOn branch (dropSrc is called only there)
    ("  function dropSrc(i){ pageSrc.splice(i, 1); pageCorners.splice(i, 1); if (adjustIdx === i) adjustIdx = -1; else if (adjustIdx > i) adjustIdx--; }   // S523; S559_FIX1 C2\n",
     "  function dropSrc(i){ pageSrc.splice(i, 1); pageCorners.splice(i, 1); adjGenS559++;                    // S563: a late Adjust picture of a deleted page is ignored\n"
     "    if (adjustIdx === i) adjustIdx = -1;\n"
     "    else if (adjustIdx > i) { adjustIdx--; $(\"addpage\").textContent = \"\\u2714 Theek hai \\u2014 page \" + (adjustIdx + 1); }   // S523; S559_FIX1 C2; S563: the stage names the page now adjusted\n"
     "  }\n", 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    n = 0
    for i, (old, new, cnt) in enumerate(edits, 1):
        got = text.count(old)
        if got != cnt:
            raise SystemExit("REFUSED: %s edit %d: the anchor is found %d times, not %d:\n  %s" % (name, i, got, cnt, old[:160]))
        text = text.replace(old, new)
        n += 1
    return text, n


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    item3_only = "--cp-item3-only" in sys.argv
    os.makedirs(out, exist_ok=True)
    plan = {"sorting_desk.py": SD_EDITS, "clinic_papers.py": CP_ITEM3 + ([] if item3_only else CP_TIDY),
            "asset_register.py": AR_EDITS, "asset_machine.py": AM_EDITS, "scanner_widget.js": JS_EDITS}
    built = {}
    for f, edits in plan.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5(raw) != FROM[f]:
            raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
        text, n = apply(f, raw.decode("utf-8"), edits)
        built[f] = (text.encode("utf-8"), n)
    for f, (b, n) in built.items():
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("%-18s %s -> %s  (%d counted edit%s, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n, "" if n == 1 else "s"))
    if item3_only:
        print("clinic_papers.py: item 3 only (no tidy) -- the walk's byte-identical fetch")


if __name__ == "__main__":
    main()
