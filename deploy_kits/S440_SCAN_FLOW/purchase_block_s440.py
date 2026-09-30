# ---------------------------------------------------------------------------------------------------------------------
# S440_SCAN_FLOW (30-Sep-2026, D640, F-662): WHAT A PERSON DECIDED ABOUT A SCAN RIDES EVERY PASS
# The staff's "Scan ka kaam" (porders.py) lets a person answer what the matcher could not: "yes, this is that bill" /
# "no, it is not"; "this is the supplier"; "the paper says Rs X". Those answers live in purchase_scan_state (additive
# columns, below) and the pass must not wipe them -- until now it deleted the table and wrote it again. So:
#   * a link of grade CONFIRMED stays while its scan and bill exist (the rules are not asked again);
#   * a bill a person refused for a scan (hint_no) is never matched or hinted to it again;
#   * a chosen supplier stands in for the vendor OCR could not read; the paper amount stands in for the scan's;
#   * dup_ok marks a paper a person recognised as a second scan of a linked one;
#   * likely_bill names the bill the reason sentence speaks of, also when that bill already has a scan;
#   * a LINKED scan keeps its row (why 'linked') when a person decided something about it.
S440_STATE_COLS = (("likely_bill", "INTEGER"), ("confirmed_by", "TEXT"), ("confirmed_at", "TEXT"), ("paper_amount", "INTEGER"),
                   ("chosen_vendor", "TEXT"), ("hint_no", "TEXT"), ("amount_state", "TEXT"), ("dup_ok", "INTEGER"))
S440_DECIDED = ("confirmed_by", "confirmed_at", "paper_amount", "chosen_vendor", "hint_no", "amount_state", "dup_ok")


def _decisions_s440(con):
    """{scan id: what a person decided} -- only the rows that carry a decision."""
    out = {}
    try:
        for r in con.execute("SELECT asset_bill_id, %s FROM purchase_scan_state" % ", ".join(S440_DECIDED)).fetchall():
            d = {k: r[i + 1] for i, k in enumerate(S440_DECIDED)}
            if any(v not in (None, "") for v in d.values()):
                d["no"] = {int(x) for x in str(d.get("hint_no") or "").split(",") if x.strip().isdigit()}
                out[r[0]] = d
    except sqlite3.Error:
        pass
    return out


def _apply_decisions_s440(scans, dec, ctx):
    suppliers = set(ctx["canon"].values())
    for s in scans:
        d = dec.get(s["id"])
        if not d:
            continue
        if d.get("paper_amount") is not None:
            s["amount_p"] = int(d["paper_amount"])             # the amount a person read ON THE PAPER
        if d.get("chosen_vendor") and d["chosen_vendor"] in suppliers:
            s["_vendor"] = (d["chosen_vendor"], "chosen", 1.0)
        s["_no"] = d["no"]


def _state_put_s440(con, sid, why, detail, first, bid, hint, stamp, likely, d):
    d = d or {}
    con.execute("INSERT OR REPLACE INTO purchase_scan_state (asset_bill_id, why, detail, dup_cand, dup_bill, hint_bill, checked_at, likely_bill, "
                "confirmed_by, confirmed_at, paper_amount, chosen_vendor, hint_no, amount_state, dup_ok) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, why, detail, first, bid, hint, stamp, likely, d.get("confirmed_by"), d.get("confirmed_at"), d.get("paper_amount"),
                 d.get("chosen_vendor"), d.get("hint_no"), d.get("amount_state"), d.get("dup_ok")))


def _scan_flow_s440(con, body):
    """The owner's Scan links page inside the scan flow: the BACK bar first (to ?from=, else the portal's tile hub), the
    five groups the staff work through on Purchase orders (read-only here), the floating up-arrow."""
    frm = str(request.args.get("from") or "")
    back = frm if (frm.startswith("/") and not frm.startswith("//") and len(frm) <= 300 and not re.search(r"[\\\r\n\"'<>]", frm)) else "/portal"
    bar = ('<div id="s440bar" style="position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;background:#1f3864;color:#fff;'
           'padding:6px 10px;margin:0 0 10px;border-radius:0 0 8px 8px"><a id="s440back" href="%s" style="display:flex;align-items:center;'
           'justify-content:center;min-height:44px;padding:0 20px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;'
           'text-decoration:none">← BACK</a><span style="margin-left:auto;font-weight:600">Scan links</span></div>' % _esc(back))
    up = ('<button id="s440up" aria-label="back to top" onclick="window.scrollTo({top:0,behavior:\'smooth\'})" style="position:fixed;right:14px;bottom:18px;'
          'width:48px;height:48px;border-radius:24px;border:0;background:#1f3864;color:#fff;font-size:24px;display:none;z-index:70;cursor:pointer">↑</button>'
          '<script>window.addEventListener("scroll",function(){var b=document.getElementById("s440up");if(b)b.style.display=(window.pageYOffset>window.innerHeight)?"block":"none"});</script>')
    groups = ""
    try:
        import porders                                         # noqa: PLC0415 -- beside this file; fail-soft: the tables below never wait for it
        k = porders.scan_work(con)

        def grp(title, rows, open_=False):
            if not rows:
                return ""
            return ('<details%s style="margin:6px 0"><summary style="cursor:pointer"><b>%s</b> (%d)</summary><ul style="margin:6px 0 2px 18px;padding:0">%s</ul></details>'
                    % (" open" if open_ else "", title, len(rows), "".join("<li>%s</li>" % r for r in rows)))
        g1 = ["%s bill %s · %s · %s · %d days%s" % (_esc(" ".join(str(x["vendor"]).split())), _esc(x["bill_no"]), _esc(x["date_text"]), _esc(x["amount"]), x["age"],
                                                       (" — <span class=\"bad\">entered twice in Marg (%s): on the WRONG list</span>" % _esc(" / ".join(x["double_nos"]))) if x.get("double") else "")
              for x in k["scan"]]
        g1 += ["%s — the order was received %s; its bill is not in Marg yet" % (_esc(x["vendor"]), _esc(x.get("received_text") or "")) for x in k.get("received") or []]
        g2 = ["scan %s reads '%s' · %s → %s bill %s (%s, %s)%s" % (_esc(x["stamp"]), _esc(x["scan_no"] or "nothing"), _esc(x["scan_amount"]), _esc(x["vendor"]), _esc(x["bill_no"]),
                                                                       _esc(x["date_text"]), _esc(x["amount"]),
                                                                       (" — that bill already has scan %s: a second scan?" % _esc(x.get("taken_stamp") or "")) if x.get("taken_by") else "")
              for x in k["confirm"]]
        g3 = ["scan %s reads '%s' · %s · %s" % (_esc(x["stamp"]), _esc(x["scan_vendor"] or "nothing"), _esc(x["scan_no"] or "no number"), _esc(x["scan_amount"])) for x in k["vendor"]]
        g4 = ["scan %s → %s bill %s: the scan reads %s, Marg %s" % (_esc(x["stamp"]), _esc(x["vendor"]), _esc(x["bill_no"]), _esc(x["scan_amount"]), _esc(x["amount"])) for x in k["amount"]]
        g5 = ["scan %s · %s · %s · %s — %s" % (_esc(x["stamp"]), _esc(x["scan_vendor"] or "no vendor"), _esc(x["scan_no"] or "no number"), _esc(x["scan_amount"]), _esc(x.get("note_en") or ""))
              for x in k["wait"]]
        c = k["counts"]
        groups = ('<div class="card" id="s440groups"><h2>Scan work — what the staff see on Purchase orders (%d to act on)</h2><div class="muted">Read-only here; each line carries its '
                  'buttons on <a href="/finance/porders?from=%s/page/scans">Purchase orders</a>. To scan %d · Is this the bill? %d · Choose the supplier %d · Match the amount %d · '
                  'Waiting for Marg %d · second scans %d.</div>%s%s%s%s%s</div>'
                  % (k["n"], request.script_root + _url_prefix, c["scan"], c["confirm"], c["vendor"], c["amount"], c["wait"], c["dup"],
                     grp("To scan (Scan karo)", g1), grp("Is this the bill? (Yahi bill hai?)", g2, True), grp("Choose the supplier (Supplier chuno)", g3, True),
                     grp("Match the amount (Amount milao)", g4, True), grp("Waiting for Marg (Marg ka intezaar)", g5)))
    except Exception:                                          # noqa: BLE001
        groups = ""
    i = body.find('<div class="card"><h2')
    if groups and i >= 0:
        body = body[:i] + groups + body[i:]
    else:
        body = body + groups
    return bar + body + up


