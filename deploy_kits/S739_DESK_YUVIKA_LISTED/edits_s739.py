# -*- coding: utf-8 -*-
"""edits_s739.py -- S739_DESK_YUVIKA_LISTED: the counted edits on /root/assetapp/sorting_desk.py (S732's TO, 52e959da).

The owner's FINAL (05:50 IST 07-Nov-2026) on the mock-up https://claude.ai/artifact/RAA6esA8dF8Bi5ojdazUzo:
  (F-1159) a listed supplier's challan (Variety) opened on the desk says it is sorted on the Stationery page, with the link; its
           destinations and Save do not move it, and the server refuses such a Save. A paper whose supplier is newly picked as a listed
           one is sent to the Stationery page by its Save (no lines from the desk).
  (D845 (3)) a Yuvika paper on the clinic side: her handwritten slip opens with Procedure room chosen and its lines ready, her
           printed bill with Pharmacy (Sanjeevni) chosen, one with nothing read offers two buttons -- a suggestion only, nothing moves
           until a person's Save; a place a person already gave it stays. This part is behind the owner's switch desk.yuvika
           (absent = OFF), on the home page's Switches card.
Each anchor must occur exactly once in the FROM file (make_s739.py refuses otherwise).
"""

EDITS = []


def E(name, old, new):
    EDITS.append((name, (old, new)))


E("1 the kit marker",
  'OTHERLINES = "S732"           # S732_DESK_OTHER_LINES (D838): Other lines on the desk\n',
  'OTHERLINES = "S732"           # S732_DESK_OTHER_LINES (D838): Other lines on the desk\n'
  'DESK_S739 = "S739"           # S739_DESK_YUVIKA_LISTED (F-1159, D845 (3)): a listed challan -> the Stationery page; Yuvika suggested\n')

E("2 the switch on the Switches card",
  '            ("batteries.on", "Batteries for Shavez"))                                   # S571 item 6 (absent = OFF)\n',
  '            ("batteries.on", "Batteries for Shavez"),                                   # S571 item 6 (absent = OFF)\n'
  '            ("desk.yuvika", "Yuvika slips on the desk"))                                # S739 (absent = OFF)\n')

E("3 the switch's state",
  '            "batteries.on": (_setting(db, "batteries.on", "off") or "").strip().lower() == "on"}      # S571\n',
  '            "batteries.on": (_setting(db, "batteries.on", "off") or "").strip().lower() == "on",      # S571\n'
  '            "desk.yuvika": _s739_on(db)}                                                              # S739\n')

E("4 the waiting list's line for a Yuvika paper",
  '    if _yuvika(b["vendor"]):\n        return "Yuvika — always chosen by a person"\n',
  '    if _yuvika(b["vendor"]) and _s739_on(db):                       # S739: her slip / her printed bill / nothing read\n'
  '        return S739_YUV_HINT.get(_s739_yuv(db, b, b["doc_kind"] or ""), "Yuvika — always chosen by a person")\n'
  '    if _yuvika(b["vendor"]):\n        return "Yuvika — always chosen by a person"\n')

E("5 the paper's suggestion for a Yuvika paper",
  '    if yuv:\n'
  '        hints.append("Yuvika supplies the pharmacy and the clinic — a person always chooses." +\n'
  '                     ((" Now: " + DEST_NAME.get(cur, cur) + ".") if cur else ""))\n'
  '    else:\n',
  '    y739 = _s739_yuv(db, b, kind) if (yuv and _s739_on(db)) else ""      # S739 (D845 (3)): switch desk.yuvika\n'
  '    if y739:\n'
  '        if cur:\n'
  '            dest, dest_line = cur, "Where it is now."             # a place a person gave it stays\n'
  '        elif y739 in S739_YUV_DEST:\n'
  '            dest, dest_line = S739_YUV_DEST[y739], S739_YUV_LINE[y739]     # unread: the page\'s two buttons\n'
  '    elif yuv:\n'
  '        hints.append("Yuvika supplies the pharmacy and the clinic — a person always chooses." +\n'
  '                     ((" Now: " + DEST_NAME.get(cur, cur) + ".") if cur else ""))\n'
  '    else:\n')

E("6 the paper's S739 part",
  '            **_s732_paper(db, b)}                                                            # S732: the Other lines panel\n',
  '            **_s732_paper(db, b),                                                            # S732: the Other lines panel\n'
  '            **_s739_paper(db, b, owner, y739)}                                               # S739: the Stationery-page card; Yuvika\n')

E("7 the Save: a listed challan is not moved here",
  '    dest, s560 = _s560_pre(db, b, p, dest, owner, today)           # S560: a receipt / statement is filed with the bill it pays\n',
  '    dest = _s739_save(db, b, p, dest, msgs)                         # S739 (F-1159): a listed challan -> the Stationery page\n'
  '    if dest is None:                                                # S739: a listed challan\'s second-scan answer only\n'
  '        AR._audit_bill(db, bid, "desk_saved", {"answer": str(p.get("flag") or ""), "via": "desk", "s739": 1})\n'
  '        return {"message": "%s: %s" % (st, " ".join(msgs)), "status": _row(db, bid)["status"]}\n'
  '    dest, s560 = _s560_pre(db, b, p, dest, owner, today)           # S560: a receipt / statement is filed with the bill it pays\n')

E("8 the card's place on the page",
  '<div id=groupsbox>',
  '<div id=s739 class=c739 style="display:none"></div><div id=groupsbox>')

E("9 the card's look",
  '.dt715 .b{font-size:12px;min-height:26px;padding:2px 8px}\n',
  '.dt715 .b{font-size:12px;min-height:26px;padding:2px 8px}\n'
  '.c739{flex-direction:column;gap:6px;border:1px solid #e3c27a;background:#fdf3df;border-radius:8px;padding:8px 10px;font-size:13px;margin-bottom:6px}'
  '.c739.here{border-color:#9dbad6;background:#e6eff8}.c739 b{font-size:14px}.c739 .go739{align-self:flex-start;display:inline-block;'
  'padding:7px 14px;border-radius:6px;background:#2b5d8a;color:#fff;text-decoration:none;font-weight:600}\n')

E("10 the Save button follows the card",
  "s715gate(ok);}",
  "s715gate(ok);s739gate();}")

E("11 the Save's body",
  "s732body(b,j);if($('pg_on')",
  "s732body(b,j);s739body(b,j);if($('pg_on')")

E("12 the page's S739 part",
  "function s715gate(ok){",
  "// S739_DESK_YUVIKA_LISTED: a listed supplier's challan is sorted on the Stationery page (F-1159); Yuvika's two buttons (D845 (3))\n"
  "function s739on(){var j=S.cur;if(!j||!j.s739){return '';}var x=j.s739,v=$('f_vendor').value.trim(),same=(v==(j.supplier||'').trim()),k=same?null:s715known(v);\n"
  " if(x.flow){return (same||(k&&k.listed))?'here':'';}if(S.kind&&S.kind!='challan'){return '';}return (k&&k.listed&&x.could)?'send':'';}\n"
  "function s739gate(){var j=S.cur,bx=$('s739');if(!j||!bx){return;}var m=s739on(),x=j.s739||{},h='',nm=x.name||'This supplier';\n"
  " if(m=='here'){h='<b>'+esc(nm)+'’s challans are sorted on the Stationery page</b><span>Each line goes to the clinic or NK there, and it joins their monthly statement. This desk does not move it.</span>'+(x.go?'<a class=go739 href=\"'+esc(x.go)+'\">Open '+esc(j.stamp)+' on the Stationery page</a>':'');\n"
  "  var q=!!(j.flags.hold||j.flags.s441);if(q&&(S.flag=='keep'||S.flag=='restore')){$('save').disabled=false;$('save').textContent='Save the answer — it is sorted on the Stationery page';}\n"
  "  else if(!q){$('save').disabled=true;$('save').textContent='Sorted on the Stationery page';}}\n"
  " else if(m=='send'){h='<b>A listed supplier’s challan</b><span>Save sends it to the Stationery page, where each line goes to the clinic or NK.</span>';\n"
  "  var hold=((j.flags.hold||j.flags.s441)&&!S.flag)||S715.state=='';$('save').disabled=!!hold;if(!hold){$('save').textContent='Save — send it to the Stationery page';}}\n"
  " else if(x.yuv=='unread'&&!S.dest){h='<span>Its lines could not be read. Yuvika sends both kinds — look at the scan and choose:</span><span style=\"display:flex;gap:8px;flex-wrap:wrap\"><button type=button class=b data-s739=slip>Handwritten slip → Procedure room</button><button type=button class=b data-s739=bill>Printed bill → Pharmacy (Sanjeevni)</button></span>';}\n"
  " bx.innerHTML=h;bx.style.display=h?'flex':'none';bx.className=(m=='here')?'c739 here':'c739';if(m){var sb=$('st568');if(sb){sb.style.display='none';}}\n"
  " Array.prototype.forEach.call(document.querySelectorAll('#groups .d'),function(b){b.disabled=(m=='here');b.style.opacity=(m=='here')?'.45':'';});}\n"
  "function s739body(b,j){var m=s739on();if(m=='send'||(m=='here'&&(S.flag=='keep'||S.flag=='restore'))){b.dest='stationery';delete b.st_lines;}}\n"
  "document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-s739]'):null;if(!t){return;}var w=t.getAttribute('data-s739');\n"
  " S.dest=(w=='slip')?'procedure':'pharmacy';if(w=='slip'){S.kind='estimate';}paint();});\n"
  "function s715gate(ok){")

E("13 the S739 helpers",
  "def _s732_paper(db, b):\n",
  '# ---------------------------------------------------------------------------------------------- S739_DESK_YUVIKA_LISTED\n'
  '# The owner\'s FINAL, 05:50 IST 07-Nov-2026 (mock-up RAA6esA8dF8Bi5ojdazUzo). F-1159: a listed supplier\'s challan on the Stationery\n'
  '# page\'s flow (scanned on or after its start day, not placed elsewhere by a person, never the pharmacy lane) is sorted THERE: the\n'
  '# desk shows the link and its Save refuses to move it; a paper whose supplier is newly picked as a listed one is sent there by its\n'
  '# Save, with no lines. D845 (3), behind desk.yuvika (absent = OFF): Yuvika\'s paper on the clinic side -- her handwritten slip is\n'
  '# suggested to the Procedure room, her printed bill (a bill number, not a slip or challan) to the pharmacy, nothing read: two\n'
  '# buttons. A suggestion only; a place a person gave it stays; nothing moves until a person\'s Save.\n'
  'S739_YUV_DEST = {"slip": "procedure", "bill": "pharmacy"}\n'
  'S739_YUV_LINE = {"slip": "Yuvika\'s handwritten slip — procedure-room goods. Suggested: check the lines, then Save.",\n'
  '                 "bill": "Yuvika\'s printed bill — the pharmacy\'s. Save hands it to Sanjeevni, as today; it pairs with its Marg bill there.",\n'
  '                 "unread": "Its lines could not be read. Yuvika sends both kinds — choose Handwritten slip or Printed bill."}\n'
  'S739_YUV_HINT = {"slip": "Yuvika — handwritten slip: Procedure room suggested", "bill": "Yuvika — printed bill: Pharmacy suggested",\n'
  '                 "unread": "Yuvika — lines not read: choose slip or bill"}\n'
  '\n'
  '\n'
  'def _s739_on(db):\n'
  '    return (_setting(db, "desk.yuvika", "off") or "").strip().lower() == "on"\n'
  '\n'
  '\n'
  'def _s739_yuv(db, b, kind):\n'
  '    """Yuvika\'s paper on the clinic side: \'slip\', \'bill\' or \'unread\' (\'\' on the pharmacy lane). A printed bill carries a bill number\n'
  '    and is not read as a slip or a challan; her handwritten slips carry none; no number and no line read = unread."""\n'
  '    if _lane(b) == "pharmacy":\n'
  '        return ""\n'
  '    if (b["bill_no"] or "").strip() and (kind or "") not in ("estimate", "challan"):\n'
  '        return "bill"\n'
  '    if not CP._items_text(db, b["id"]):\n'
  '        return "unread"                                               # no number and no line read: the scan decides, a person chooses\n'
  '    return "slip"\n'
  '\n'
  '\n'
  'def _s739_flow(db, b, vendor=None, kind=None, listed=None):\n'
  '    """Is this paper -- with the supplier and kind given (default: its own) -- a listed supplier\'s challan on the Stationery page\'s\n'
  '    flow? listed=True skips the supplier test (could it be, were its supplier listed). False when stationery.py is not mounted."""\n'
  '    st = _s568_st()\n'
  '    if st is None or not hasattr(st, "is_listed") or not hasattr(st, "floor_day"):\n'
  '        return False\n'
  '    v = (b["vendor"] or "") if vendor is None else vendor\n'
  '    k = (b["doc_kind"] or "") if kind is None else kind\n'
  '    if k not in ("", "challan"):\n'
  '        return False\n'
  '    if listed is None and not st.is_listed(db, v):\n'
  '        return False\n'
  '    if _lane(b) == "pharmacy" or b["dup_of"] or b["page_of"] or b["status"] == "rejected":\n'
  '        return False\n'
  '    fl = st.floor_day(db)\n'
  '    if not fl or (b["created_at"] or "")[:10] < fl:\n'
  '        return False                                                 # before the start day: the desk as before (F-1158)\n'
  '    if hasattr(st, "left_ids") and b["id"] in st.left_ids(db):\n'
  '        return False                                                 # he left it as it is on the Stationery page: the desk as before\n'
  '    sg = b["subgroup"] or ""\n'
  '    if sg and (b["lane"] or "clinic") == "clinic" and sg != "stationery":\n'
  '        return False                                                 # a person placed it elsewhere: the Stationery page leaves it too\n'
  '    return True\n'
  '\n'
  '\n'
  'def _s739_go(db, b, owner):\n'
  '    """The Stationery page for this paper: his page (its To sort, or Change once sorted); a manager\'s sort page."""\n'
  '    st = _s568_st()\n'
  '    vf = AR.app.view_functions\n'
  '    if owner and "s568_stock" in vf:\n'
  '        try:\n'
  '            sorted_ = bool(st.saved_lines(db, b)) if hasattr(st, "saved_lines") else False\n'
  '        except Exception:                                            # noqa: BLE001\n'
  '            sorted_ = False\n'
  '        return url_for("s568_stock") + (("?change=%d#s674change" % b["id"]) if sorted_ else "#s674sort")\n'
  '    if "s674_sort" in vf:\n'
  '        return url_for("s674_sort")\n'
  '    return ""\n'
  '\n'
  '\n'
  'def _s739_paper(db, b, owner, yuv=""):\n'
  '    """paper_json\'s S739 part: flow (sorted on the Stationery page, with its link and the supplier), could (it would be, were its\n'
  '    supplier a listed one), yuv (Yuvika\'s paper: slip / bill / unread, only while desk.yuvika is ON)."""\n'
  '    out = {"flow": False, "could": False, "go": "", "name": "", "yuv": yuv or ""}\n'
  '    try:\n'
  '        out["could"] = bool(_s739_flow(db, b, kind="challan", listed=True))\n'
  '        if _s739_flow(db, b):\n'
  '            out.update(flow=True, name=b["vendor"] or "", go=_s739_go(db, b, owner))\n'
  '    except Exception as ex:                                          # noqa: BLE001\n'
  '        print("S739 paper: %s" % ex, file=sys.stderr)\n'
  '    return {"s739": out}\n'
  '\n'
  '\n'
  'def _s739_save(db, b, p, dest, msgs):\n'
  '    """In the Save, before anything is written. A paper on the Stationery page\'s flow whose supplier stays a listed one is not moved\n'
  '    here: refused -- unless a second-scan question was just answered (keep / restore), when the answer stands and nothing else is\n'
  '    written (None: save() returns at once, the paper keeps its place). A paper whose supplier is newly picked as a listed one goes to\n'
  '    Stationery & packaging with no lines -- the Stationery page\'s To sort then offers it. Any other paper: the destination as given."""\n'
  '    if not dest:\n'
  '        return dest\n'
  '    st = _s568_st()\n'
  '    vend = str(p.get("vendor") if p.get("vendor") is not None else (b["vendor"] or "")).strip()\n'
  '    kind = str(p.get("kind") or "").strip() or (b["doc_kind"] or "")\n'
  '    if _s739_flow(db, b):                                            # the paper as stored is on the flow\n'
  '        if not st.is_listed(db, vend):\n'
  '            return dest                                              # its supplier corrected to another: the desk as before\n'
  '        if str(p.get("flag") or "").strip() in ("keep", "restore"):\n'
  '            msgs.append("The answer is saved; it stays where it is and is sorted on the Stationery page (any other change is made there).")\n'
  '            return None\n'
  '        raise DeskError("%s is %s\'s challan — it is sorted on the Stationery page, not on the desk. Nothing was saved."\n'
  '                        % (_stamp(b), b["vendor"] or "a listed supplier"))\n'
  '    if not _s739_flow(db, b, vendor=vend, kind=kind):\n'
  '        return dest\n'
  '    p.pop("st_lines", None)\n'
  '    msgs.append("A listed supplier\'s challan: sort its lines on the Stationery page (To sort).")\n'
  '    return "stationery"\n'
  '\n'
  '\n'
  "def _s732_paper(db, b):\n")
