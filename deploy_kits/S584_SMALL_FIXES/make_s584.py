#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s584.py -- kit S584_SMALL_FIXES: the builder. Anchored edits on the LIVE bytes of nine files; no new file, no data step.

    python3 -B make_s584.py --finance /root/finance --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes the nine files into DIR and prints each md5 -- the installer compares them with PINS.sh.
The brief: claude_code_briefs/S584_SMALL_FIXES.md (v2). F-931 a/b, F-932, F-875, F-881, F-913, F-914, F-915, E of D737, the nine settings.
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "f279a3be440878bb30e418c20a5cf608",
    "stock_watch.py": "80896ce257b155f21429a559eec891b9",
    "stock_now.html": "91cdc56db4fd2d77cf8249c777f36f6f",
    "stock_drift.html": "daa40ee896548b97808cab564cadeee3",
    "stock_loss.html": "0f0dfed658d05d182811005ebce49df3",
    "stockmatch.py": "10e30d28053aca3090e193502b67b1e0",
    "amir_day.py": "73882a8391fde24f31e07b0191c5bd89",
    "purchase_app.py": "98f7d9f05bc06ef6be80181dd9be4c8c",
    "order_sheet_pdf.py": "bcd0cde59b916ea390b94d042627aaf9",
}

# =============================================================================================================== stock_drift.html (F-931 a)
DR = []
DR.append(("D1 the null-to-dash helper beside esc()", '''function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function ymd(d){''', '''function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function num(v){return v===null||v===undefined?"\\u2014":String(v);}   /* S584 (F-931a): no 'null' in a cell -- a dash for an item with no PC estimate */
function ymd(d){'''))
DR.append(("D2 the last-day gap cell through num()", '''+i.agreed+'</td><td class="n">'+i.disagreed+'</td><td class="n">'+i.last
''', '''+i.agreed+'</td><td class="n">'+i.disagreed+'</td><td class="n">'+num(i.last)
'''))

# =============================================================================================================== stock_now.html (F-931 b, F-932)
NW = []
NW.append(("N1 the PC note slot under the tiles", '''  <div class="tiles" id="tiles"></div>
</div>
''', '''  <div class="tiles" id="tiles"></div>
  <div id="pcnote" class="muted" style="margin-top:8px;display:none"></div>
</div>
'''))
NW.append(("N2 the head line: the capture the table stands on; ours_at is the read moment", '''  $("head").innerHTML="Stock as on <b>"+rdyEsc(rdyDmy(j.as_on))+"</b>. Our figure processed "
    +rdyEsc(j.ours_at?rdyStamp(j.ours_at):"— never received")
    +"; Marg&rsquo;s "+rdyEsc(j.marg_at?rdyStamp(j.marg_at):"— never received")+".";
''', '''  /* S584 (F-931b): one figure, one date -- the spine's capture (marg_at) the table stands on; ours_at is when this page was read, never "processed" */
  $("head").innerHTML="Stock as on <b>"+rdyEsc(rdyDmy(j.as_on))+"</b> &mdash; Marg&rsquo;s closing taken "
    +rdyEsc(j.marg_at?rdyDmHm(j.marg_at):"(no capture)")
    +"; read "+rdyEsc(rdyHm(j.ours_at))+".";
'''))
NW.append(("N3 the fifth column and its note, the doctor only", '''  $("tiles").innerHTML=
     tile(t.items,"items")+tile(t.agree,"agree with Marg")
    +tile(t.differ,"differ")+tile(t.below_zero,"below zero","bad");
  paint();
''', '''  $("tiles").innerHTML=
     tile(t.items,"items")+tile(t.agree,"agree with Marg")
    +tile(t.differ,"differ")+tile(t.below_zero,"below zero","bad");
  if(j.pc_old_head){                                            /* S584 (F-932): api_now sends pc_old_head to the doctor only; nobody else sees a fifth column */
    var th=document.createElement("th"); th.className="n"; th.textContent=j.pc_old_head;
    document.querySelector("table thead tr").appendChild(th);
    $("pcnote").textContent="PC's old estimate (retiring): shown to you only, retired after the side-by-side week (4b-2).";
    $("pcnote").style.display="block";
  }
  paint();
'''))
NW.append(("N4 the row: pc_old under pc_old_head", '''    return "<tr><td>"+rdyEsc(r.item)+'</td><td class="n">'+num(r.ours)
      +'</td><td class="n">'+num(r.marg)+'</td><td class="n">'+gapCell(r.gap)+"</td></tr>";
  }).join("")||'<tr><td colspan="4" class="muted">Nothing to show under this filter.</td></tr>';
''', '''    return "<tr><td>"+rdyEsc(r.item)+'</td><td class="n">'+num(r.ours)
      +'</td><td class="n">'+num(r.marg)+'</td><td class="n">'+gapCell(r.gap)
      +(DATA.pc_old_head?'</td><td class="n">'+num(r.pc_old):"")+"</td></tr>";   /* S584 (F-932): the fifth cell only under pc_old_head */
  }).join("")||'<tr><td colspan="'+(DATA.pc_old_head?5:4)+'" class="muted">Nothing to show under this filter.</td></tr>';
'''))
NW.append(("N5 the dd-mm hh:mm and hh:mm helpers", '''function rdyStamp(ts){
  ts=String(ts||"");
  return ts.length>=16?(rdyDmy(ts.slice(0,10))+" "+ts.slice(11,16)):rdyDmy(ts);
}
''', '''function rdyStamp(ts){
  ts=String(ts||"");
  return ts.length>=16?(rdyDmy(ts.slice(0,10))+" "+ts.slice(11,16)):rdyDmy(ts);
}
function rdyDmHm(ts){ ts=String(ts||""); return ts.length>=16?(ts.slice(8,10)+"-"+ts.slice(5,7)+" "+ts.slice(11,16)):rdyDmy(ts); }   /* S584 */
function rdyHm(ts){ ts=String(ts||""); return ts.length>=16?ts.slice(11,16):ts; }
'''))

# =============================================================================================================== stock_loss.html (F-932, the settings heading)
LS = []
LS.append(("L1 the system's closures above the piles", '''  let h=groupCard();
  D.piles.forEach((P,i)=>{ h+=pileCard(P,i); });
''', '''  let h=sysClosedHtml()+groupCard();                            // S584 (F-932): the lines the system closed as 'sold after count' -- one muted English line
  D.piles.forEach((P,i)=>{ h+=pileCard(P,i); });
'''))
LS.append(("L2 sysClosedHtml()", '''function drawGroup(){ const e=document.getElementById("groupcard");''',
           '''function sysClosedHtml(){ const S=D.system_closed; return (S&&S.text)?'<div class="sub" style="margin:8px 2px 0">'+esc(S.text)+'</div>':''; }   // S584 (F-932): loss_piles._system_closed
function drawGroup(){ const e=document.getElementById("groupcard");'''))
LS.append(("L3 the approximate spot counts after the Traces group", '''    +'<div class="w">'+t.findings.filter(f=>!f.ok||f.explains).map(f=>esc(dash(f.text))).join(' · ')+(t.fix?' — <b>Amir: '+esc(t.fix)+'</b>':'')+'</div></div>'; });
  const V=W.tap_vs_bill||[];
''', '''    +'<div class="w">'+t.findings.filter(f=>!f.ok||f.explains).map(f=>esc(dash(f.text))).join(' · ')+(t.fix?' — <b>Amir: '+esc(t.fix)+'</b>':'')+'</div></div>'; });
  const AX=W.approx_lines||[];                                   // S584 (F-932): the approximate spot counts S577 computed (owner_view.approx_lines) -- drawn at last
  if(AX.length) h+='<div class="grp"><span>Approximate spot counts</span><span>'+AX.length+'</span></div>'+AX.map(x=>'<div class="rl">'+esc(dash(x))+'</div>').join("");
  const V=W.tap_vs_bill||[];
'''))
LS.append(("L4 watchSettings(): the rows grouped by heading", '''function watchSettings(){
  const W=D.watch; if(!W||!W.settings) return '';
  let h='<div class="grp" style="margin-top:18px"><span>Counts &amp; watch</span><span>S428</span></div><p class="lead">Sunday full counts, the mornings\\' spot counts, arrivals, the trace and the leakage budget. In strips words; every change recorded.</p>';
  W.settings.forEach(s=>{
    let c;
''', '''function watchSettings(){
  const W=D.watch; if(!W||!W.settings) return '';
  let h='', cur=null;                                           // S584: a heading line each time the row's heading changes -- 'Counts & watch' first, then 'Amir and the reports'
  W.settings.forEach(s=>{
    const hd=s.heading||"Counts & watch";
    if(hd!==cur){ cur=hd;
      if(hd==="Counts & watch") h+='<div class="grp" style="margin-top:18px"><span>Counts &amp; watch</span><span>S428</span></div><p class="lead">Sunday full counts, the mornings\\' spot counts, arrivals, the trace and the leakage budget. In strips words; every change recorded.</p>';
      else h+='<div class="grp" style="margin-top:18px"><span>'+esc(hd)+'</span><span>S584</span></div><p class="lead">How long Amir\\'s voucher proof, a refused report and his one-time Marg jobs may wait before your line, and when your salt and item lists fall overdue. Nothing changes until you save one.</p>';
    }
    let c;
'''))

# =============================================================================================================== stock_watch.py (the nine settings)
SW = []
SW.append(("W1 version", '''VERSION = "1.6"
KIT = "S583_ARRIVALS_ONE_RULE"                                # v1.5 was S577_STOCK_ON_SPINE, v1.4 S502_STOCK_MILAAN_TODAY, v1.3 S436_STAFF_PAGES_CLEAN
''', '''VERSION = "1.7"
KIT = "S584_SMALL_FIXES"                                      # v1.6 was S583_ARRIVALS_ONE_RULE, v1.5 S577_STOCK_ON_SPINE, v1.4 S502_STOCK_MILAAN_TODAY
# v1.7 (S584, 18-Oct-2026): nine settings reach the owner's card under the heading "Amir and the reports" (amir.proof_wait_hours,
# amir.refused_keep_hours, amir.job_wait_days, amir.salt_owed_days, amir.self_exports, amir.claim_open_days, amir.voucher_visits,
# owner.salt_list_days, owner.item_lists_days) -- rows with no default of their own: _default(s) reads amir_day.S444_DEFAULTS /
# reports_tile.OWNER_LISTS (one default, one place); the hints are amir_day.S444_NOTES. PREFIXES gains "amir." and "owner." so the desk's
# save door (stock_app /api/loss/<cid>/pile/setting) hands them here. set_setting keeps a row's existing note (the S444 note survives a save).
'''))
SW.append(("W2 the heading constant before SETTINGS", '''SETTINGS = (
    dict(key="count.cadence_months",''', '''S584_HEADING = "Amir and the reports"                        # S584: the second heading of the owner's card; the first is "Counts & watch"
SETTINGS = (
    dict(key="count.cadence_months",'''))
SW.append(("W3 the nine rows; PREFIXES; _default / _hint", '''    dict(key="leak.red_periods", label="Leakage: red months running -> Needs you", kind="int", default="2", seed="2", lo=1, hi=12,
         hint="This many red months in a row puts one line on your Needs you."),
)
SETTING_BY_KEY = {s["key"]: s for s in SETTINGS}
PREFIXES = ("count.", "spot.", "arrival.", "leak.")
''', '''    dict(key="leak.red_periods", label="Leakage: red months running -> Needs you", kind="int", default="2", seed="2", lo=1, hi=12,
         hint="This many red months in a row puts one line on your Needs you."),
    # S584: the nine rows below carry NO default and NO hint of their own -- _default(s) / _hint(s) read the module that owns the figure
    dict(key="amir.proof_wait_hours", label="Voucher proof: hours before your warn line", kind="int", seed=None, lo=1, hi=240,
         heading=S584_HEADING, default_from=("amir_day", "amir.proof_wait_hours")),
    dict(key="amir.refused_keep_hours", label="Refused report: hours on your Needs-you list", kind="int", seed=None, lo=1, hi=168,
         heading=S584_HEADING, default_from=("amir_day", "amir.refused_keep_hours")),
    dict(key="amir.job_wait_days", label="Amir's one-time Marg jobs: days before your line", kind="int", seed=None, lo=1, hi=60,
         heading=S584_HEADING, default_from=("amir_day", "amir.job_wait_days")),
    dict(key="amir.salt_owed_days", label="Salt list: visits owed before your line", kind="int", seed=None, lo=1, hi=30,
         heading=S584_HEADING, default_from=("amir_day", "amir.salt_owed_days")),
    dict(key="amir.self_exports", label="Amir's own correction: bill-wise exports before your line", kind="int", seed=None, lo=1, hi=10,
         heading=S584_HEADING, default_from=("amir_day", "amir.self_exports")),
    dict(key="amir.claim_open_days", label="A claim for Darpan: days open before your line", kind="int", seed=None, lo=1, hi=60,
         heading=S584_HEADING, default_from=("amir_day", "amir.claim_open_days")),
    dict(key="amir.voucher_visits", label="Count vouchers untouched: Amir's visits before your line", kind="int", seed=None, lo=1, hi=10,
         heading=S584_HEADING, default_from=("amir_day", "amir.voucher_visits")),
    dict(key="owner.salt_list_days", label="Your salt-wise list: overdue after (days)", kind="int", seed=None, lo=1, hi=60,
         heading=S584_HEADING, default_from=("reports_tile", "owner.salt_list_days"),
         hint="Marg's salt-wise item list counts as overdue on your Reports card after this many days without a fresh one."),
    dict(key="owner.item_lists_days", label="Your category and item lists: overdue after (days)", kind="int", seed=None, lo=1, hi=120,
         heading=S584_HEADING, default_from=("reports_tile", "owner.item_lists_days"),
         hint="Marg's category-wise list and item master count as overdue on your Reports card after this many days without a fresh one."),
)
SETTING_BY_KEY = {s["key"]: s for s in SETTINGS}
PREFIXES = ("count.", "spot.", "arrival.", "leak.", "amir.", "owner.")   # S584: the desk's save door routes these prefixes here


def _default(s):
    """S584: ONE default per setting. A row's own `default`, else the module that owns the figure: amir_day.S444_DEFAULTS[key], or the [2]
    of the reports_tile.OWNER_LISTS triple whose type maps to the key in reports_tile.S488_LIST_KEYS (two types share owner.item_lists_days
    and carry the same limit -- asserted). Lazy imports: amir_day imports this file lazily, reports_tile is stdlib + flask -- no cycle."""
    if "default" in s:
        return s["default"]
    mod, key = s["default_from"]
    if mod == "amir_day":
        import amir_day                                        # noqa: PLC0415
        return str(amir_day.S444_DEFAULTS[key])
    import reports_tile                                       # noqa: PLC0415
    vals = {int(t[2]) for t in reports_tile.OWNER_LISTS if reports_tile.S488_LIST_KEYS.get(t[0]) == key}
    assert len(vals) == 1, "reports_tile.OWNER_LISTS: %s has %d limits" % (key, len(vals))
    return str(vals.pop())


def _hint(s):
    """S584: the row's hint -- its own, else amir_day.S444_NOTES[key] (read, not copied)."""
    if "hint" in s:
        return s["hint"]
    import amir_day                                            # noqa: PLC0415
    return amir_day.S444_NOTES[s["default_from"][1]]
'''))
SW.append(("W4 settings(): every row through _default", '''        raw = setting_raw(con, s["key"])
        out[s["key"]] = raw if raw is not None else s["default"]
''', '''        raw = setting_raw(con, s["key"])
        out[s["key"]] = raw if raw is not None else _default(s)   # S584: a row without a default of its own reads its module's
'''))
SW.append(("W5 settings_view(): _default, _hint, the heading", '''        raw = setting_raw(con, s["key"])
        v = raw if raw is not None else s["default"]
        rows.append(dict(key=s["key"], label=s["label"], kind=s["kind"], value=v, shown=_shown(s, v), hint=s["hint"],
                         choices=[dict(v=a, t=b) for a, b in s.get("choices", ())], set=(raw is not None),
                         rupees=(None if s["kind"] != "rupees" else int(float(v)) // 100), heading="Counts & watch"))
''', '''        raw = setting_raw(con, s["key"])
        v = raw if raw is not None else _default(s)
        rows.append(dict(key=s["key"], label=s["label"], kind=s["kind"], value=v, shown=_shown(s, v), hint=_hint(s),
                         choices=[dict(v=a, t=b) for a, b in s.get("choices", ())], set=(raw is not None),
                         rupees=(None if s["kind"] != "rupees" else int(float(v)) // 100), heading=s.get("heading") or "Counts & watch"))   # S584
'''))
SW.append(("W6 set_setting(): keep the row's existing note", '''    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                (key, v, "S428 stock watch setting: %s" % s["label"]))
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("setting", 0, "stock_setting",''', '''    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
                "note=COALESCE(NULLIF(note,''), excluded.note)",   # S584: a row's own note (the S444 seed's) survives a save
                (key, v, "S428 stock watch setting: %s" % s["label"]))
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("setting", 0, "stock_setting",'''))

# =============================================================================================================== stock_app.py (F-931 b, E of D737)
SA = []
SA.append(("A1 _r_stock(): the figures of record, one line; stock_feed no longer read here", '''def _r_stock(con):
    """Marg's closing-stock export and our computed figure: the as-on date of
    each, when this server processed it, and how many items it carried."""
    out = dict(ok=False, marg=None, expected=None,
               line="Stock export: nothing has reached the server yet.")
    try:
        # S226b: COUNT(*) here was a ROW count, and every push appends a
        # whole set -- so three pushes of a 373-item day read as 1,119
        # items. The owner saw 746 and 1,492 on the first live screen.
        newest = {}
        for (as_on, kind), v in _feed_latest(con).items():
            cur = newest.get(kind)
            if cur is None or (_proof_day_key(as_on), v["received_at"]) > (_proof_day_key(cur["as_on"]),   # S488 (F-753)
                                                                           cur["processed_at"]):
                newest[kind] = dict(as_on=as_on, source=v["source"],
                                    items=len(v["items"]),
                                    processed_at=v["received_at"])
        out["marg"] = newest.get("marg")
        out["expected"] = newest.get("expected")
        out["ok"] = bool(out["marg"] or out["expected"])
        parts = []
        if out["marg"]:
            parts.append("Marg's closing stock: as on %s, processed here %s (%d items)."
                         % (_r_dmy(out["marg"]["as_on"]),
                            _r_stamp(out["marg"]["processed_at"]),
                            out["marg"]["items"]))
        else:
            parts.append("Marg's closing stock: never received.")
        if out["expected"]:
            parts.append("Our computed figure: as on %s, processed %s (%d items)."
                         % (_r_dmy(out["expected"]["as_on"]),
                            _r_stamp(out["expected"]["processed_at"]),
                            out["expected"]["items"]))
        else:
            parts.append("Our computed figure: never received.")
        out["line"] = " ".join(parts)
    except Exception:
        out["line"] = ("Stock export: the feed table could not be read, so the "
                       "export's date and time are unknown.")
    return out
''', '''def _r_stock(con):
    """S584 (F-931 b): the figures of record the stock-now table stands on -- Marg's closing CAPTURE (stock_figure.capture_at, the one
    _s577_record reads) and the shelf figure's basis (the newest full count, stock_figure.count_family) -- in ONE line. The old pushes (the
    PC's push_expected and Marg's push_snapshot, the feed table) are no longer read here; api_drift's PC series stays as the 4b-2 witness.
    out['marg'] keeps its shape (as_on dd-mm-yyyy, processed_at = the capture's stamp, items) for readiness()'s warning; 'expected' is gone."""
    out = dict(ok=False, marg=None,
               line="Stock export: nothing has reached the server yet.")
    try:
        sp = _s524_spine()
        if not _sf.ready(sp):
            return out
        ctx = _sf.Ctx(con, sp)
        cap = _sf.capture_at(sp, None, ctx)
        if cap is None:
            return out
        n_items = int((sp.q("SELECT COUNT(*) AS n FROM sp_close_name WHERE md5=?", cap["md5"]) or [{"n": 0}])[0]["n"] or 0)
        out["marg"] = dict(as_on=_r_dmy(cap["as_on"]), source="spine", items=n_items, processed_at=cap["stamp_iso"])
        out["ok"] = True
        si = str(cap["stamp_iso"] or "")
        parts = ["Marg's closing stock: as on %s, taken %s-%s %s (%d items)." % (_r_dmy(cap["as_on"]), si[8:10], si[5:7], si[11:16], n_items)]
        cf = _sf.count_family(con, ctx) or {}
        days = sorted(str(v.get("day") or "")[:10] for v in cf.values() if v.get("day"))
        if days:
            parts.append("The shelf figure: the count of %s carried forward to that closing through Marg's sales, purchases and the filed vouchers."
                         % _r_dmy(days[-1]))
        else:
            parts.append("The shelf figure: no full count yet.")
        out["line"] = " ".join(parts)
    except Exception:
        out["line"] = ("Stock export: the spine's closing table could not be read, so the "
                       "capture's date and time are unknown.")
    return out
'''))
SA.append(("A2 _s584_pur_landed() before _s521_stage_words()", '''def _s521_stage_words(con, st):
    """{state, lines: [{hi, anchor}], card_hi, board_hi, owner_en, owner_lines: [dict(cls, target, text)], wrong_rows, questions} for the''',
           '''def _s584_pur_landed(con, sp):
    """S584 (E of D737): the moment Amir's purchase report LANDED after the spine's purchase reach -- the newest VERIFIED mi_file row of a
    purchase type (PURCHASE_BILLWISE / PURCHASE_ITEMWISE / PURCHASE_BILLITEMWISE) whose received_at, folded as amir_day._norm_ts folds it
    ('YYYY-MM-DD HH:MM:SS'; the '+05:30' and the odd space dropped), is later than stamp_iso(reach(sp)['pur_stamp']). None when none has,
    when the spine or its purchase reach is missing (never 'every row is later'), or when there is no mi_file table. The judgment itself
    (tryable / covers / the verdict) still reads the spine: only the do-this line follows this fact."""
    try:
        if sp is None or not getattr(sp, "ok", False):
            return None
        ps = _sf.stamp_iso((_sf.reach(sp) or {}).get("pur_stamp"))
        if not ps:
            return None
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='mi_file'").fetchone():
            return None
        r = con.execute("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE verdict='VERIFIED' "
                        "AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')").fetchone()
        at = str((r[0] if r else "") or "").strip()[:19]
        return at if (len(at) == 19 and at > ps.replace("T", " ")[:19]) else None
    except Exception:                                          # noqa: BLE001
        return None


def _s521_stage_words(con, st):
    """{state, lines: [{hi, anchor}], card_hi, board_hi, owner_en, owner_lines: [dict(cls, target, text)], wrong_rows, questions} for the'''))
SA.append(("A3 pur(): no suffix once his export has landed", '''        lines, en, state, wrong = [], "", "", []

        def pur(p):
            return (" \\u00b7 " + S528_PUR_HI) if (p or {}).get("why") == "pur_behind" else ""
''', '''        lines, en, state, wrong = [], "", "", []
        landed = _s584_pur_landed(con, _s524_spine()) if (pr or {}).get("why") == "pur_behind" else None   # S584 (E of D737): his fact has landed

        def pur(p):
            return (" \\u00b7 " + S528_PUR_HI) if ((p or {}).get("why") == "pur_behind" and not landed) else ""

        def landed_en():
            return "purchase report landed %s \\u2014 judged at the spine's next build (within 10 minutes)" % landed[11:16]
'''))
SA.append(("A4 stage A export: the English follows the fact", '''                lines.append(dict(hi="Orthotic voucher daal diye \\u2713" + pur(pr), anchor=None))
                en = "Stage A: all %d entered \\u2014 waiting: %s" % (tot, _s524_english_ending(pr) or "for the closing-stock export that proves them")
''', '''                lines.append(dict(hi="Orthotic voucher daal diye \\u2713" + pur(pr), anchor=None))
                en = (("Stage A: all %d entered \\u2014 %s" % (tot, landed_en())) if landed else                        # S584
                      "Stage A: all %d entered \\u2014 waiting: %s" % (tot, _s524_english_ending(pr) or "for the closing-stock export that proves them"))
'''))
SA.append(("A5 stage C export: the English follows the fact", '''                lines.append(dict(hi="Dawa ke voucher daal diye \\u2713" + pur(pr), anchor=None))
                en = "Stage C: lot %d entered on %s \\u2014 waiting: %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?",
                                                                         _s524_english_ending(pr) or "for the closing-stock export")
''', '''                lines.append(dict(hi="Dawa ke voucher daal diye \\u2713" + pur(pr), anchor=None))
                en = (("Stage C: lot %d entered on %s \\u2014 %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?", landed_en())) if landed else   # S584
                      "Stage C: lot %d entered on %s \\u2014 waiting: %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?",
                                                                          _s524_english_ending(pr) or "for the closing-stock export"))
'''))

# =============================================================================================================== stockmatch.py (F-875)
SM = []
SM.append(("M1 c2 also waits on the guard's held lines; amir_stage read once, above it", '''    not_entered = [b for b in ob if not b["entered"]]
    c2 = (not pend) and (not not_entered)
    # 3 -- the proof, for the orthotic lines: S524 (F-840) -- the STAGE proof (stock_app.amir_stage / _s446_proof, read from the spine), the
    #      one judgment Amir's card, his board, the hub and the statement all read; the pending orthotic line is c2's, never c3's
    P = sa.amir_stage(con, root, d=d)
    AP = ((P or {}).get("A") or {}).get("proof") or {}
''', '''    not_entered = [b for b in ob if not b["entered"]]
    P = sa.amir_stage(con, root, d=d)                           # S584 (F-875): the stage read ONCE, above c2 -- c3 below reuses it
    held = ((P or {}).get("A") or {}).get("held") or []       # the orthotic lines A's guard holds back for the owner (S537 / S577): not yet on a voucher
    c2 = (not pend) and (not not_entered) and (not held)      # a held line keeps the section waiting -- the tick never says done over an open line
    # 3 -- the proof, for the orthotic lines: S524 (F-840) -- the STAGE proof (stock_app.amir_stage / _s446_proof, read from the spine), the
    #      one judgment Amir's card, his board, the hub and the statement all read; the pending orthotic line is c2's, never c3's
    AP = ((P or {}).get("A") or {}).get("proof") or {}
'''))
SM.append(("M2 the c2 words count the held lines with the pending ones (the existing words)", '''        dict(key="vouchers", ok=c2,
             en=("orthotic round made and entered" if c2 else ("%d orthotic line%s not yet on a voucher" % (len(pend), "" if len(pend) == 1 else "s") if pend
                                                              else "%d orthotic voucher%s not yet entered in Marg" % (len(not_entered), "" if len(not_entered) == 1 else "s"))),
             hi=("Amir ke vouchers ho gaye" if c2 else ("Vouchers banane baaki: %d line" % len(pend) if pend else "Amir ke vouchers Marg mein daalne baaki: %d" % len(not_entered)))),
''', '''        dict(key="vouchers", ok=c2,                           # S584 (F-875): a held line is 'not yet on a voucher' -- counted with the pending ones
             en=("orthotic round made and entered" if c2 else ("%d orthotic line%s not yet on a voucher" % (len(pend) + len(held), "" if len(pend) + len(held) == 1 else "s") if (pend or held)
                                                              else "%d orthotic voucher%s not yet entered in Marg" % (len(not_entered), "" if len(not_entered) == 1 else "s"))),
             hi=("Amir ke vouchers ho gaye" if c2 else ("Vouchers banane baaki: %d line" % (len(pend) + len(held)) if (pend or held) else "Amir ke vouchers Marg mein daalne baaki: %d" % len(not_entered)))),
'''))

# =============================================================================================================== amir_day.py (F-881)
AD = []
AD.append(("Y1 KIT names the kit that placed the file", '''KIT = "S533_AMIR_DAY_PAGE"
''', '''KIT = "S584_SMALL_FIXES"                                   # F-881: the kit that last placed this file (S533 built the page; S537, S577, S583 read it)
'''))

# =============================================================================================================== purchase_app.py (F-913, F-914)
PA = []
PA.append(("P1 _book_bank_cell(): the button only for whom the door admits", '''def _book_bank_cell(r, i, doctor):
    """The bank block of a row, as the page has drawn it since S225 (rev 12), with its Add/Edit and Verify."""
''', '''def _book_bank_cell(r, i, doctor, may_bank):
    """The bank block of a row, as the page has drawn it since S225 (rev 12), with its Add/Edit and Verify. S584 (F-914, rule 13): the
    'add / edit bank details' button and its form slots are drawn only when may_bank (= _s452_may_advice: the owner and Shavez) -- the
    save door refuses 'bank' / 'verify' for anyone else, so Darpan sees the chip and the masked lines, and no button."""
'''))
PA.append(("P2 _book_bank_cell(): the return", '''    return ('%s%s <button class="sm noprint" onclick="bookForm(%d,\\'bank\\')">%s bank details</button>'
            '<div class="inl noprint" id="inl-bank-%d" hidden></div><div class="inl noprint" id="inl-verify-%d" hidden></div>'
            % ("".join(bank_lines), chip, i, "edit" if has_bank else "add", i, i))
''', '''    if not may_bank:
        return "%s%s" % ("".join(bank_lines), chip)
    return ('%s%s <button class="sm noprint" onclick="bookForm(%d,\\'bank\\')">%s bank details</button>'
            '<div class="inl noprint" id="inl-bank-%d" hidden></div><div class="inl noprint" id="inl-verify-%d" hidden></div>'
            % ("".join(bank_lines), chip, i, "edit" if has_bank else "add", i, i))
'''))
PA.append(("P3 _s574_page(): may_bank read once", '''    rows = _book_rows(con)
    if not _s452_may_advice(con, u):                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
    also = {}
''', '''    rows = _book_rows(con)
    may_bank = _s452_may_advice(con, u)                        # S584 (F-914): the door's own test, read once; the screen follows it
    if not may_bank:                                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
    also = {}
'''))
PA.append(("P4 _s574_page(): 'also' never lists the record's own spelling (norm)", '''        others = []
        for x in ([r["vendor"]] if (r.get("display_name") and r["display_name"] != r["vendor"]) else []) + also.get(r["vendor_norm"], []):
            if x and x not in others:
                others.append(x)
''', '''        others = []
        for x in [r["vendor"]] + also.get(r["vendor_norm"], []):   # S584 (F-913): a name joins 'also' only when norm(x) != norm(name) -- never the record's own spelling
            if x and norm(x) != norm(name) and all(norm(x) != norm(o) for o in others):
                others.append(x)
'''))
PA.append(("P5 _s574_page(): the caller passes may_bank", '''                      _book_src_txt(r), ph, ('<br><small class="muted">%s</small>' % em) if em else "", picks, edit, _book_bank_cell(r, i, doctor)))
''', '''                      _book_src_txt(r), ph, ('<br><small class="muted">%s</small>' % em) if em else "", picks, edit, _book_bank_cell(r, i, doctor, may_bank)))
'''))
PA.append(("P6 page_book() (the OFF page): may_bank read once", '''        return _s574_page(con, u, doctor)
    rows = _book_rows(con)
    if not _s452_may_advice(con, u):                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
''', '''        return _s574_page(con, u, doctor)
    rows = _book_rows(con)
    may_bank = _s452_may_advice(con, u)                        # S584 (F-914)
    if not may_bank:                                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
'''))
PA.append(("P7 page_book() (the OFF page): the caller passes may_bank", '''                   % (_esc(r["vendor"]), src_txt, phones, numbtn, _book_bank_cell(r, i, doctor)))
''', '''                   % (_esc(r["vendor"]), src_txt, phones, numbtn, _book_bank_cell(r, i, doctor, may_bank)))
'''))

# =============================================================================================================== order_sheet_pdf.py (F-915)
OP = []
OP.append(("O1 the header follows", '''#  number(s) -- "(number nahi hai)" when none -- and three boxes (WhatsApp · Call · Bill scan); a row per medicine with its quantity in
''', '''#  number(s) -- the screens' own words when none (porders_s454.T["nonum"], S584: one copy) -- and three boxes (WhatsApp · Call · Bill scan); a row per medicine with its quantity in
'''))
OP.append(("O2 _band_geom(): the screens' words for a supplier with no number", '''    ph = "Ph. " + (", ".join(b["phones"]) if b["phones"] else "(number nahi hai)")
''', '''    if b["phones"]:
        ph = "Ph. " + ", ".join(b["phones"])
    else:
        import porders_s454                                   # noqa: PLC0415 -- S584 (F-915): the screens' sentence, one copy; porders_s454 imports this file lazily (a top-level import would be a cycle)
        ph = porders_s454.T["nonum"][0]                       # "Number nahi hai -- Dr sahab ko dijiye" (_latin folds the dash for the PDF as it does for every string)
'''))

EDITS = {"stock_drift.html": DR, "stock_now.html": NW, "stock_loss.html": LS, "stock_watch.py": SW, "stock_app.py": SA,
         "stockmatch.py": SM, "amir_day.py": AD, "purchase_app.py": PA, "order_sheet_pdf.py": OP}


def apply(src, edits, label):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM[label]:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, FROM[label]))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label)
        if out is None:
            return 2
        built[label] = out
    os.makedirs(a.out, exist_ok=True)
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM[label]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
