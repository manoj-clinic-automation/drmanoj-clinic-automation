

# ---- S973 (27-Nov-2026, Sanjeevni session 540, kit S973_VOUCHER_SCANS; kit C of S534_FINAL_BUILD_PLAN, D1091 plan 2.4) --------------------
#  The voucher's print card on his page (voucher_scan.py makes it): 'Voucher ka print' -- the words of mock-up v7 -- with ONE tap
#  'Print diya — reception ko' (reception gets its line and one push at once) and 'Khud scan karein' (the Scan App's intake on the pharmacy
#  lane with the voucher's number; no camera code here). 'Pehle bana chuka hoon' on a claim card syncs at once, so the print card follows
#  without waiting for the 5-minute sync. Nothing else on the page changes.
KIT_S973 = "S973_VOUCHER_SCANS"
S814_ANS["printed"] = "Print diya — reception ko"
S973_PRT = re.compile(r"^S973:prt:(\d+):([A-Z0-9]{0,8})$")     # the ask's id and its voucher number ('' when Amir named none)
_s494_lines_before_s973 = _s494_lines
_s494_tap_before_s973 = _s494_tap


def _s973_card(j):
    m = S973_PRT.match(str(j.get("key") or ""))
    no = m.group(2) if m else ""
    try:
        import voucher_scan as VS                              # noqa: PLC0415 -- beside this file
        link = VS.intake_link(no, "/finance/amir")
    except Exception:                                          # noqa: BLE001
        link = "/scanapp/intake?lane=pharmacy&from=%2Ffinance%2Famir"
    return ("<div class=line style='border-left:4px solid var(--bad);padding-left:8px'><span class=big><b>Voucher ka print</b></span><br>"
            "<span>%s</span><form method=post style='margin-top:8px'><button type=submit disabled hidden aria-hidden=true></button>"
            "<input type=hidden name=job value='ask:%d'><button class='btn plain' name=ans value='printed' "
            "style='display:block;width:100%%;text-align:left;margin:0 0 6px'>%s</button></form>"
            "<a class='btn plain' href='%s' style='display:block;text-align:left;margin:0 0 6px'>Khud scan karein%s</a></div>"
            % (_esc(j.get("text_hi") or j["subject"]), j["id"], _esc(S814_ANS["printed"]), _esc(link), (" (%s)" % _esc(no)) if no else ""))


def _s494_lines(jobs):                                         # noqa: F811 -- S973: the print card first among the asks
    jobs = list(jobs or [])
    prt = [j for j in jobs if j.get("kind") == "ask" and S973_PRT.match(str(j.get("key") or ""))]
    if not prt:
        return _s494_lines_before_s973(jobs)
    out = _s494_lines_before_s973([j for j in jobs if j not in prt])
    head = "<div class=line id=s494jobs><span class=sub><b>Ek baar ke kaam</b></span></div>"
    cards = [_s973_card(j) for j in prt]
    if out and out[0] == head:
        return [head] + cards + out[1:]
    return [head] + cards + out


def _s494_tap(cx, who, val, note=""):                          # noqa: F811 -- S973: 'Print diya' tells reception at once; 'already' syncs at once
    n = _s494_tap_before_s973(cx, who, val, note)
    try:
        ma = re.match(r"^ask:(\d{1,9}):([a-z]{3,10})$", str(val or "").strip())
        if n and ma:
            key = (cx.execute("SELECT key FROM amir_job WHERE id=?", (int(ma.group(1)),)).fetchone() or [""])[0] or ""
            if ma.group(2) == "printed" and S973_PRT.match(key):
                import voucher_scan as VS                      # noqa: PLC0415
                VS.after_print(cx, int(ma.group(1)), who)
            elif ma.group(2) == "already" and key.startswith("S971:clm:"):
                import voucher_inquiry as VI                   # noqa: PLC0415
                VI.sync_maybe(cx, force=True)
    except Exception as e:                                     # noqa: BLE001
        print("amir_day S973 tap: %s" % str(e)[:200], file=sys.stderr)
    return n
# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------
