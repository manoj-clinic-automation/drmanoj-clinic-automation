"""walk_s761.py -- kit S761_HUB_NEEDS_GOTO (Sanjeevni session 414, 09-Nov-2026, D873 / F-1199). Writes nothing outside --scratch.
Loads sanjeevni_approvals and shelf_figure from the root under test and runs them on a COPY of finance.db (the walk's own made-up days are
dated 2099-01); every other source of a Needs-you line is replaced, for the walk only, by a stand-in that answers in that source's real words
with made-up names. Then the page: the Go to panel's links against the app's own url_map, the old strip's links all present, the drawing
by node.
  python walk_s761.py --root <root holding finance/ (as built, or live for the control)> --db <a COPY of finance.db> --scratch <dir>
       [--page <finance_approvals.html>] [--urlmap <rules.json, else made by importing finance_app on a scratch copy>]
The control (the live files): every S761 check red, every older check green."""
import argparse, json, os, re, shutil, sqlite3, subprocess, sys, types, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--root"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--page"); ap.add_argument("--urlmap")
a = ap.parse_args()
if a.page: a.page = os.path.abspath(a.page)
if a.urlmap: a.urlmap = os.path.abspath(a.urlmap)
ROOT = os.path.abspath(a.root)
FIN = os.path.join(ROOT, "finance")
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
DB = os.path.join(a.scratch, "walk761.db")
shutil.copyfile(os.path.abspath(a.db), DB)
sys.path[:0] = [FIN, os.path.join(FIN, "spine")]
os.chdir(a.scratch)
res = []


def check(name, ok, s761=True, note=""):
    res.append((name, bool(ok), s761, str(note)[:400]))


def con_():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


OLD_LINKS = ["/finance/sanjeevni/expiry", "/finance/purchase/page/staff", "/finance/purchase/page/hub", "/finance/stockmatch", "/finance/workbench",
             "/finance/darpan/kal/month", "/finance/review", "/finance/darpan/corrections", "/finance/accountant/upi-cash", "/finance/pipeline",
             "/finance/staff", "/finance/approvals/old"]

# ---- the made-up days (2099-01) -------------------------------------------------------------------------------------------------------
c = con_()
for d in ("2099-01-03", "2099-01-04"):
    c.execute("INSERT OR IGNORE INTO day_entry (unit, business_date, status, source) VALUES ('medical', ?, 'submitted', 'app')", (d,))
c.commit()

# ---- the stand-ins: each answers in its source's real words, made-up names -----------------------------------------------------------
ARR = [  # stock_watch.arrival_needs_you's two shapes (the scan, the tap), one carrying the other-size note
    "WALK ALPHA M: counted as arrived when the WALKVEND ONE bill was scanned 02-11 10:00 -- not in Marg's purchases up to 08-11",
    "WALK ALPHA L: counted as arrived when the WALKVEND ONE bill was scanned 02-11 10:00 -- not in Marg's purchases up to 08-11 (its bill B1 of 01-11 carried XL, not this size)",
    "WALK BETA: counted as arrived when the WALKVEND ONE bill was scanned 05-11 09:30 -- not in Marg's purchases up to 08-11",
    "WALK GAMMA: counted as arrived when the WALKVEND ONE bill was scanned 05-11 09:30 -- not in Marg's purchases up to 08-11",
    "WALK DELTA 500: counted as arrived when Darpan tapped it 05-11 11:00 (WALKVEND TWO) -- not in Marg's purchases up to 08-11"]
STAND = {
    # porders.needs_you_lines: its own lines, then scan_register.owner_lines and order_sheet.owner_lines (the exact shapes at their sources)
    "porders": [dict(cls="warn", target="porders", text="Orthotic shortages: 8 items -- order not sent"),
                dict(cls="warn", target="porders", text="Bill scan waiting: 3 · the oldest 4 days (reception's Bill scan karna hai)"),
                dict(cls="info", target="scans", text="Paper not found by reception: 1 bill -- your tap accepts it on the register (WALKVEND ONE W9)"),
                dict(cls="info", target="scans", text="Scanned and not yet in Marg for more than 7 days: 2 bills (oldest 01-Nov) -- for your eyes only"),
                dict(cls="info", target="porders", text="Buying rules for medicines await your approval"),
                dict(cls="warn", target="porders", text="An order of 31-10 to WALKVEND THREE was never placed (1 item)"),
                dict(cls="info", target="porders", text="Order sheet: WALKVEND THREE prints a phone number the phone book lacks -- add it in the phone book"),
                dict(cls="info", target="porders", text="Order sheet of 02-11: 2 item names not found in Marg's stock list: WALK X, WALK Y")],
    "bank_sms": [dict(cls="warn", target="bank", text="NEFT of ₹500 seen on 03-Nov -- matched to October. OK?", neft_event=7)],
    "supplier_msg": [dict(cls="warn", target="bank", text="2 supplier messages unsent (30 minutes or more)"),
                     dict(cls="warn", target="bank", text="NEFT of October: bank shows ₹900, sheet ₹1,000 -- differs by ₹100")],
    "packs": [dict(cls="warn", target="bank", text="October: 1 statement not on the shelf (WALK BANK)")],
    "order_rules": [dict(cls="info", target="porders", text="Kedar review (02-11): twice-weekly since 26-09 held the big four at a peak of 22 boxes (08-10). Move Kedar to weekly?",
                         review_supplier="KEDAR PHARMACEUTICAL", review_target="weekly"),
                    dict(cls="info", target="porders", text="Medicine ordering is frozen since 05-11 10:00: walk reason"),
                    dict(cls="info", target="porders", text="This week: 3 medicine orders, ₹1,000, 1 still open")],
    "stock_watch": [dict(cls="warn", target="stock", text="Count #1: the full count is due -- Amir picks a Sunday"),
                    dict(cls="info", target="stock", text="Full count: Sunday 16-Nov (Amir picked, Darpan said yes)")] +
                   [dict(cls="warn", target="porders", text=t) for t in ARR],
    "amir_day": [dict(cls="warn", target="checks-marg", text="Salt list not received for 2 of Amir's visits -- 4 salt corrections unproven (Amir; owed since 01-11)"),
                 dict(cls="warn", target="checks-marg", text="Bank details to type for WALK RAMA -- Amir says its bill is scanned"),
                 dict(cls="warn", target="checks-marg", text="Claim for Darpan open 3 days: WALKVEND ONE bill W1 Rs 100 (raised by Amir 05-11)"),
                 dict(cls="info", target="porders", text="Goods tapped as arrived on 02-11 from WALKVEND TWO: no bill scanned, nothing in Marg (7 days) -- for your eyes only"),
                 dict(cls="info", target="checks-marg", text="WALK CAT is not on Marg's category list of 05-Nov -- its category could not be proved")],
    "expiry_watch": [dict(cls="warn", target="expiry", text="Expiry watch: 1 expired batch · 2 stop selling on 1-Dec", href="/finance/sanjeevni/expiry")],
    "sale_check": None, "darpan_kal": None}


class _Resp:
    def get_json(self):
        return {"ok": True, "count": 1, "owed_p": 0}


def stand_in():
    keep = {k: sys.modules.get(k) for k in STAND}
    for k, v in STAND.items():
        m = types.ModuleType(k)
        if k == "sale_check":
            m.days_with_mistakes = lambda con: 1
        elif k == "darpan_kal":
            m.api_owner = lambda: _Resp()
        else:
            m.needs_you_lines = (lambda L: (lambda con, *x, **kw: [dict(l) for l in L]))(v)
        sys.modules[k] = m
    return keep


def put_back(keep):
    for k, v in keep.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


import sanjeevni_approvals as sa                                       # noqa: E402
assert os.path.dirname(os.path.abspath(sa.__file__)) == FIN
sa._unit = "medical"
keep_rl = getattr(sa, "_s760_returns_line", None)
sa._s760_returns_line = lambda con, today: dict(cls="warn", target="returns", text="Returns waiting for your OK — 2 · ₹300 · oldest 01-Jan")
keep = stand_in()
try:
    J = sa.needs_you(c)
    OLD = sa._needs_you_before_s761(c) if hasattr(sa, "_needs_you_before_s761") else None
    os.environ["NEEDS_YOU_WITHOUT_S761"] = "1"
    J6 = sa.needs_you(c)
    del os.environ["NEEDS_YOU_WITHOUT_S761"]
    if hasattr(sa, "s761_groups"):
        kg = sa.s761_groups
        sa.s761_groups = lambda L: (_ for _ in ()).throw(RuntimeError("walk: grouping down"))
        J7 = sa.needs_you(c)
        sa.s761_groups = kg
    else:
        J7 = {}
finally:
    put_back(keep)
L = J.get("lines") or []
G = J.get("groups") or []
open(os.path.join(a.scratch, "needs761.json"), "w", encoding="utf-8").write(json.dumps(J, ensure_ascii=False))
by = {g["key"]: g for g in G}
idx = sorted(i for g in G for i in g.get("idx", []))
check("G0 the answer is ok and still carries every source's line (%d lines, count %s)" % (len(L), J.get("count")), J.get("ok") and len(L) >= 30, s761=False, note=len(L))
check("G1 the answer gains groups; the groups hold %d lines = the old %d lines; each line in exactly ONE group (nothing dropped, nothing doubled)" % (sum(g["n"] for g in G), len(L)),
      bool(G) and sum(g["n"] for g in G) == len(L) and idx == list(range(len(L))),
      note=[(g["key"], g["n"]) for g in G])
check("G2 red first (the days), information last; the amber in the fixed order",
      [g["key"] for g in G] == ["days", "returns", "orders", "arrived", "papers", "stock", "marg", "bank", "darpan", "expiry", "info"] and G[0]["cls"] == "bad" and G[-1]["cls"] == "info",
      note=[(g["key"], g["cls"]) for g in G])
ag = by.get("arrived") or {}
check("G3 arrived but not in Marg: one group of 5, by dealer -- 'WALKVEND ONE 4 · WALKVEND TWO 1', the other-size line marked",
      ag.get("n") == 5 and ag.get("summary") == "WALKVEND ONE 4 · WALKVEND TWO 1" and sum(1 for v in ag.get("vendors", []) for x in v["items"] if x["size"]) == 1
      and [x["item"] for x in (ag.get("vendors") or [{}])[0].get("items", [])] == ["WALK ALPHA M", "WALK ALPHA L", "WALK BETA", "WALK GAMMA"], note=ag.get("summary"))
tx = lambda k: [l["text"] for l in (by.get(k) or {}).get("lines", [])]          # noqa: E731
check("G4 each line in its own kind of work: unsent supplier messages and the never-placed order under Orders; the NEFT lines and the statement shelf under Bank; "
      "the Darpan claim with Darpan's own line; the bank details and the salt list under Marg; the days with Bhati's line",
      "2 supplier messages unsent (30 minutes or more)" in tx("orders") and any("never placed" in t for t in tx("orders"))
      and any(t.startswith("NEFT of ₹500") for t in tx("bank")) and any("not on the shelf" in t for t in tx("bank"))
      and any(t.startswith("Claim for Darpan") for t in tx("darpan")) and any(t.startswith("Darpan: 1 item") for t in tx("darpan"))
      and any(t.startswith("Bank details to type") for t in tx("marg")) and any(t.startswith("Salt list") for t in tx("marg"))
      and any("days to approve" in t for t in tx("days")) and any("Bhati found mistakes" in t for t in tx("days")),
      note={k: len(tx(k)) for k in by})
INFO_OK = ("Goods tapped as arrived on", "This week: 3 medicine", "Scanned and not yet in Marg", "Order sheet of 02-11:", "Full count: Sunday",
           "WALK CAT is not on Marg", "no Yes Bank statement", "the Yes Bank statement")
check("G5 the information fold holds ONLY grey lines that ask nothing (goods tapped, this week, scanned-not-in-Marg, the item names, the full-count "
      "Sunday, the category, the statement's age) -- and no line with an action of its own",
      by.get("info") and len(tx("info")) in (6, 7) and all(l.get("cls") == "info" and set(l) <= {"cls", "target", "text"} for l in by["info"]["lines"])
      and all(any(x.startswith(p) for p in INFO_OK) for x in tx("info")), note=tx("info"))
# review 1: each source's actionable grey line is OUTSIDE the information fold, in its own kind of work
for nm, frag, want in (("order_rules (the Kedar review, its Move-to-weekly button)", "Kedar review (", "orders"),
                       ("order_rules (ordering frozen)", "Medicine ordering is frozen", "orders"),
                       ("porders (buying rules await your approval)", "Buying rules for medicines await", "orders"),
                       ("scan_register (paper not found -- your tap accepts it)", "Paper not found by reception", "papers"),
                       ("order_sheet (add it in the phone book)", "prints a phone number the phone book lacks", "orders")):
    where = [g["key"] for g in G for l in g["lines"] if frag in str(l.get("text"))]
    check("G5-%s: a grey line that asks him something is work -- in '%s', never in 'For your information'" % (nm, want),
          where == [want], note=where)
check("G5-unknown: an unknown grey line with any action of its own (a field the fold does not know) is work, never information",
      hasattr(sa, "s761_is_info") and not sa.s761_is_info(dict(cls="info", target="zz", text="walk plain words", some_button=1))
      and sa.s761_is_info(dict(cls="info", target="zz", text="walk plain words")) and sa._s761_key(dict(cls="info", target="zz", text="walk", some_button=1)) == "other")
# review 2: the header counts only what needs him
ninfo = len(tx("info"))
check("G5-header: the header counts what needs him: n_items %s = the lines outside the information fold (%d of %d); the fold counts its own %s; "
      "the old 'count' (%s) counted %d grey no-action module lines as work, so it is NOT the header's figure" % (J.get("n_items"), len(L) - ninfo, len(L), J.get("n_info"),
      J.get("count"), (J.get("count") or 0) - (len(L) - ninfo)),
      J.get("n_items") == len(L) - ninfo and J.get("n_info") == ninfo and J.get("n_groups") == len(G) - 1)
check("G6 the old answer is untouched: 'lines' and 'count' exactly as before S761 (owner_console and older walks read them)",
      OLD is not None and OLD.get("lines") == L and OLD.get("count") == J.get("count"), note=(OLD or {}).get("count"))
check("G7 NEEDS_YOU_WITHOUT_S761=1 (an older kit's frozen walk) gives the old answer, no groups", J6.get("ok") and "groups" not in J6 and J6.get("lines") == L)
check("G8 the grouping failing leaves the old answer (lines, count) and says why, no groups -- the page then draws the flat list",
      J7.get("ok") and "groups" not in J7 and J7.get("lines") == L and "groups_error" in J7, note=J7.get("groups_error"))
check("G9 the actions ride along unchanged inside the groups: the NEFT one-tap id, the Kedar button, the expiry page's own href",
      any(l.get("neft_event") == 7 for l in (by.get("bank") or {}).get("lines", [])) and any(l.get("review_supplier") == "KEDAR PHARMACEUTICAL" for l in (by.get("orders") or {}).get("lines", []))
      and any(l.get("href") == "/finance/sanjeevni/expiry" for l in (by.get("expiry") or {}).get("lines", [])))
# the door, through Flask
try:
    from flask import Flask                                            # noqa: E402
    app = Flask("walk761")
    sa.init(app, lambda: con_(), lambda *r, **k: (dict(user="manoj"), None), unit="medical")
    keep = stand_in()
    try:
        r = app.test_client().get("/finance/sanjeevni/api/needs-you")
    finally:
        put_back(keep)
    jj = r.get_json(silent=True) or {}
    check("E1 GET /finance/sanjeevni/api/needs-you answers 200 with the groups; n_items + n_info = its lines", r.status_code == 200 and jj.get("groups")
          and (jj.get("n_items") or 0) + (jj.get("n_info") or 0) == len(jj.get("lines") or []),
          note=(r.status_code, jj.get("n_items"), len(jj.get("lines") or [])))
except Exception as e:                                                # noqa: BLE001
    check("E1 the door answers", False, note=repr(e))
sa._s760_returns_line = keep_rl

# ---- F-1199: the owner console's Sanjeevni section counts what the hub's header counts ---------------------------------------------------
try:
    import owner_console as oc                                         # noqa: E402
    assert os.path.dirname(os.path.abspath(oc.__file__)) == FIN
    oc._sanj_pages = lambda con, cx: ([], 0)                          # his page links: not this check's business (they read their own tables)
    cxa = dict(needs_you=J, tile={})
    sa_ = oc.sec_sanj(c, cxa)
    flat = {k: v for k, v in J.items() if k not in ("groups", "n_items", "n_groups", "n_info")}
    cxb = dict(needs_you=flat, tile={})
    sb_ = oc.sec_sanj(c, cxb)
    rb = sum(1 for x in J["lines"] if x.get("cls") in ("bad", "warn"))
    check("C1 the console's Sanjeevni chip and tile count = the hub's header N (%s): chip '%s', sanj_open %s" % (J.get("n_items"), sa_.get("chip"), cxa["tile"].get("sanj_open")),
          J.get("n_items") is not None and cxa["tile"].get("sanj_open") == J.get("n_items") and sa_.get("chip") == "%d open" % J["n_items"] and J["n_items"] != rb,
          note=(sa_.get("chip"), cxa["tile"].get("sanj_open"), J.get("n_items"), rb))
    check("C2 an answer without n_items (an older sanjeevni_approvals, a grouping that failed) keeps the red + amber count (%d)" % rb,
          cxb["tile"].get("sanj_open") == rb and sb_.get("chip") == "%d open" % rb, s761=False, note=(sb_.get("chip"), cxb["tile"].get("sanj_open")))
except Exception as e:                                                # noqa: BLE001
    check("C1 the console's Sanjeevni section", False, note=repr(e))

# ---- F-1199: the shelf line says how many it does not name ----------------------------------------------------------------------------
try:
    import shelf_figure as sf                                           # noqa: E402
    kgf = sf.gap_flags
    sf.gap_flags = lambda con: ("2099-01-06", [dict(item="WALK ITEM %02d" % i) for i in range(13)])
    t13 = (sf.gap_line(c) or {}).get("text", "")
    sf.gap_flags = lambda con: ("2099-01-06", [dict(item="WALK ITEM %02d" % i) for i in range(5)])
    t5 = (sf.gap_line(c) or {}).get("text", "")
    sf.gap_flags = kgf
    check("F1 F-1199: 'moved apart on 13 items' names 8 and says 'and 5 more'; with 5 it names all 5 and says no more",
          "on 13 items" in t13 and "WALK ITEM 07 and 5 more --" in t13 and "WALK ITEM 08" not in t13 and "more" not in t5 and "WALK ITEM 04 --" in t5, note=t13[-90:])
except Exception as e:                                                # noqa: BLE001
    check("F1 the shelf line", False, note=repr(e))

# ---- P: the page -------------------------------------------------------------------------------------------------------------------
if a.page:
    page = open(a.page, encoding="utf-8").read()
    m = re.search(r'<div id="gotoPanel"(.*?)\n  </div>\n</div></div>', page, re.S)
    panel = m.group(1) if m else ""
    hrefs = re.findall(r'href="([^"]+)"', panel)
    check("P0 the Go to button and its panel sit on the top bar; the six headings as the mock",
          'id="gotoBtn"' in page and bool(panel) and all(h in panel for h in ("Purchases &amp; dealers", ">Payments<", ">Orders<", "Stock &amp; expiry", "Returns &amp; sale", "What staff see")),
          note=len(hrefs))
    check("P1 every link the old 'Other pages' strip had is in the panel (%d), and the strip itself is gone" % len(OLD_LINKS),
          all(x in hrefs for x in OLD_LINKS) and 'id="linksCard"' not in page, note=[x for x in OLD_LINKS if x not in hrefs])
    check("P2 Amir's step page (/finance/amir -- its GET settles his day) is NOT in the panel; his English summary (/finance/amir/day) is",
          "/finance/amir" not in hrefs and "/finance/amir/day" in hrefs)
    rules = None
    try:
        if a.urlmap:
            rules = json.load(open(a.urlmap, encoding="utf-8"))
        else:
            um = os.path.join(a.scratch, "um761"); os.makedirs(um, exist_ok=True)
            shutil.copyfile(DB, os.path.join(um, "f.db"))
            prog = ("import os,sys,json,io,contextlib\nfin=%r\nos.environ['FINANCE_DB']=%r\nos.environ['FINANCE_SCAN_DIR']=%r\nos.environ['FINANCE_ATTENDANCE_DB']=%r\n"
                    "sys.path[:0]=[fin,os.path.join(fin,'spine')]\nos.chdir(%r)\nb=io.StringIO()\n"
                    "with contextlib.redirect_stdout(b), contextlib.redirect_stderr(b):\n    import finance_app\n"
                    "json.dump(sorted(set((r.rule, ','.join(sorted(r.methods-{'HEAD','OPTIONS'}))) for r in finance_app.app.url_map.iter_rules())),open(%r,'w'))\n"
                    % (FIN, os.path.join(um, "f.db"), os.path.join(um, "scans"), os.path.join(um, "att.db"), um, os.path.join(um, "rules.json")))
            open(os.path.join(um, "um.py"), "w").write(prog)
            subprocess.run([sys.executable, "-I", os.path.join(um, "um.py")], timeout=180, capture_output=True, env=dict(os.environ))
            rules = json.load(open(os.path.join(um, "rules.json")))
    except Exception as e:                                            # noqa: BLE001
        check("P3 the app's url_map could be read", False, note=repr(e))
    if rules is not None:
        gets = set(r for r, mth in rules if "GET" in mth)
        miss = []
        for h in hrefs:
            p = h.split("?")[0].split("#")[0]
            if p.startswith("/scanapp/"):
                asrc = os.path.join(ROOT, "assetapp", "asset_register.py")
                if os.path.exists(asrc) and ('@app.route("%s")' % p[len("/scanapp"):]) not in open(asrc, encoding="utf-8").read():
                    miss.append(h)
                continue
            if p not in gets:
                miss.append(h)
        check("P3 every link in the panel (%d) is a page the app serves (its own url_map, %d rules; /scanapp/ against the scan app's routes)" % (len(hrefs), len(rules)),
              hrefs and not miss, note=miss)
    check("P4 F-1199 on the page: the Cash card names no day count of its own; 'banked' names one figure (the Cash card's) -- Days says nothing of the bank, Bank says 'pool deposits'",
          "day(s) awaiting your approval" not in page and "DAYS.position.bank" not in page and "banked from the pool" not in page and "pool deposits recorded here" in page
          and 'Banked to date ("+esc(j.bank_count)+")' in page)
    check("P5 the Orders tab, the header count's place, Cash and Bank in one row (Cash then Bank, the Returns card after)",
          '<a href="#porders">Orders</a>' in page and 'id="needsHead"' in page
          and page.index('<div class="cb-row">') < page.index('id="cashPosCard"') < page.index('id="bankCard"') < page.index('id="returnsCard"'))
    check("P6 Days: only the open month opens (a month with a day to approve, or this month); the approved months say 'all approved ✓'",
          "(pend||(ix===0&&ym===s761Ym())?' open':'')" in page and "all approved ✓" in page)
    # ---- J: the drawing, by node (the page's own script) ------------------------------------------------------------------------
    js = page[page.rindex("<script>") + 8:page.rindex("</script>")]
    if "/* ==== KIT_S761" in js and shutil.which("node"):
        s = js[js.index("/* ==== KIT_S761"):js.index("/* ==== end KIT_S761 ==== */")]
        prelude = ("var window={};var document={addEventListener:function(){},querySelectorAll:function(){return []}};var ELS={};function $(i){return ELS[i]||null}\n"
                   "function esc(s){return (s==null?'':String(s)).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}\n"
                   "function fmt(s){return (s==null?'\\u2014':String(s)).replace(/\\.00$/,'')}function goSec(){}\n")
        cash = dict(unbanked="3,75,341", drawer="24,700", reserve="3,50,641", bank_deposited="23,70,600", bank_count=4, basis="sanjeevni_cash", as_of="07-Nov")
        bankj = dict(month="2099-01", upi_total="67,104", deposits=[dict(status="ok"), dict(status="ok")], transfers=[dict(status="ok"), dict(status="wait")])
        prog = (prelude + s + "\nvar J=" + json.dumps(J, ensure_ascii=False) + ";\nELS.needs={innerHTML:''};ELS.needsHead={textContent:''};\n"
                "s761Needs(J);\nvar BX=[['Cash in the unit','3,75,341',''],['In Darpan\\u2019s drawer','24,700','<i>d</i>'],['With you &amp; Dr Bhawna (pool)','3,50,641','<i>t</i>'],['Banked to date (4)','23,70,600','<i>x</i>']];\n"
                "process.stdout.write(ELS.needs.innerHTML+'\\n@@HEAD@@'+ELS.needsHead.textContent+'\\n@@CASH@@'+s761CashHTML(" + json.dumps(cash) + ",BX,'09-Oct \\u00b7 30 days ago','b-bad')+'\\n@@BANK@@'+s761BankLine(" + json.dumps(bankj) + "));\n")
        open(os.path.join(a.scratch, "draw761.js"), "w", encoding="utf-8").write(prog)
        o = subprocess.run(["node", os.path.join(a.scratch, "draw761.js")], capture_output=True, text=True, timeout=60)
        out = o.stdout
        check("J1 drawn: the header ' — %s items in %s groups' (what needs him); the red days group first with 'Open the days'" % (J.get("n_items"), J.get("n_groups")),
              ("@@HEAD@@ — %s items in %s groups" % (J.get("n_items"), J.get("n_groups"))) in out and out.index("Open the days") < out.index("Returns waiting for your OK"), note=o.stderr[-300:])
        check("J2 drawn: 'Arrived but not in Marg's purchases' — 'WALKVEND ONE 4 · WALKVEND TWO 1', each item on its own line, the other-size note as TEXT (not a hover)",
              "Arrived but not in Marg&#39;s purchases</b>" in out and "— WALKVEND ONE 4 · WALKVEND TWO 1" in out and "<b>WALKVEND ONE (4)</b>" in out
              and '<li class="vitem">WALK ALPHA L <span class="vnote">— its bill B1 of 01-11 carried XL, not this size</span></li>' in out
              and "1 of these: the bill carried another size" in out and "title=" not in out.split("Arrived but not in Marg")[1].split("</details>")[0])
        check("J3 drawn: 'For your information' folded and blue, '— nothing to do'; the red group open, no amber group open",
              'class="grp info"><details><summary>' in out and "For your information</b> <span class=\"gsum\">— nothing to do" in out and 'class="grp warn"><details open' not in out)
        check("J4 drawn: the old line's own buttons still inside the groups (NEFT OK / Not this, Move Kedar to weekly) and the expiry line's own page",
              "neftEvent(7,'ok')" in out and "Move Kedar to weekly" in out and 'data-href="/finance/sanjeevni/expiry"' in out)
        check("J5 drawn: Cash as four figures (₹3,75,341 · ₹24,700 · ₹3,50,641 · Banked to date (4) ₹23,70,600), no day count, the deposit gap amber",
              out.count('class="cb-box"') == 4 and "₹23,70,600" in out and "awaiting" not in out.split("@@CASH@@")[1] and 'cb-line warn">Last bank deposit 09-Oct' in out)
        check("J6 drawn: Bank's one line '2 deposits ✓ · 1 transfer ✓ · 1 waiting for a statement · Pharmacy UPI Jan ₹67,104' (not 'all confirmed' while one waits)",
              "2 deposits ✓ · 1 transfer ✓ · 1 waiting for a statement · Pharmacy UPI Jan ₹67,104" in out and "all confirmed" not in out.split("@@BANK@@")[1])
        check("J7 the escaper of this section escapes ' and no line's words sit inside a quoted onclick string",
              "&#39;" in out and "location.href='" not in out.split("@@HEAD@@")[0])
        try:
            ln = js[js.index("function loadNeeds(){"):]; ln = ln[:ln.index("\n}\n") + 3]
            sj = js[js.index("function srvJSON(r){"):]; sj = sj[:sj.index("return {s:r.status,j:j}})}") + len("return {s:r.status,j:j}})}")] + "\n"
            pre2 = (prelude.replace("var ELS={};", "var ELS={needs:{innerHTML:''},needsHead:{textContent:''},needsNote:{textContent:''}};") + s + "\n" + sj + ln +
                    "\nfunction loadPOSummary(){} function loadPOOos(){}\nvar ANS=null, FAIL=false;\n"
                    "function fetch(){ if(FAIL) return Promise.reject(new Error('walk')); var t=JSON.stringify(ANS); return Promise.resolve({status:200,text:function(){return Promise.resolve(t)}}); }\n"
                    "var GJ=" + json.dumps(J, ensure_ascii=False) + ";\nvar FLAT=JSON.parse(JSON.stringify(GJ)); delete FLAT.groups; delete FLAT.n_items; delete FLAT.n_groups;\n"
                    "var CASES=[['groups',GJ,false],['empty',{ok:true,lines:[],count:0},false],['error',{ok:false,error:'walk'},false],['flat',FLAT,false],['unreachable',null,true],"
                    "['info only',{ok:true,count:0,lines:[{cls:'info',target:'bank',text:'walk info'}],groups:[{key:'info',title:'For your information',cls:'info',n:1,idx:[0],lines:[{cls:'info',target:'bank',text:'walk info'}],summary:''}],n_items:0,n_groups:0,n_info:1},false]];\n"
                    "var OUT=[]; (function next(i){ if(i>=CASES.length){ process.stdout.write(JSON.stringify(OUT)); return; } ELS.needsHead.textContent='STALE'; ANS=CASES[i][1]; FAIL=CASES[i][2]; loadNeeds();"
                    " setTimeout(function(){ OUT.push([CASES[i][0], ELS.needsHead.textContent, ELS.needs.innerHTML.slice(0,80)]); next(i+1); }, 30); })(0);\n")
            open(os.path.join(a.scratch, "draw761b.js"), "w", encoding="utf-8").write(pre2)
            o2 = subprocess.run(["node", os.path.join(a.scratch, "draw761b.js")], capture_output=True, text=True, timeout=60)
            P = {k: (h, b) for k, h, b in json.loads(o2.stdout or "[]")}
            check("J10 the header on every path of loadNeeds: groups ' — %s items in %s groups'; nothing to show, a read error, the flat list, the server unreachable "
                  "-> no header (never a stale one); only information -> ' — nothing needs you'" % (J.get("n_items"), J.get("n_groups")),
                  P.get("groups", ("",))[0] == " — %s items in %s groups" % (J.get("n_items"), J.get("n_groups")) and all(P.get(k, ("x",))[0] == "" for k in ("empty", "error", "flat", "unreachable"))
                  and P.get("info only", ("",))[0] == " — nothing needs you" and "Nothing needs you" in P.get("empty", ("", ""))[1] and "could not reach" in P.get("unreachable", ("", ""))[1],
                  note=(P, o2.stderr[-300:]))
        except Exception as e:                                        # noqa: BLE001
            check("J10 the header on every path of loadNeeds", False, note=repr(e))
    elif "/* ==== KIT_S761" in js:
        print("  --  J1-J7 not run: node is not on this machine (the drawing was proved where it is)")
    else:
        check("J0 the page carries the S761 drawing", False)
    check("J8 the whole page script parses (node --check)", (not shutil.which("node")) or subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True).returncode == 0
          or subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(0,'utf8'))"], input=js, capture_output=True, text=True).returncode == 0, s761=False)

c.close()
bad = [r for r in res if not r[1]]
for n_, ok, s7, note in res:
    print("  %s  %s%s" % ("ok " if ok else "RED", n_, ("" if ok else "  -- " + note)))
print("walk_s761: %d check(s) failed (%d of them S761 checks)" % (len(bad), sum(1 for r in bad if r[2])))
sys.exit(1 if bad else 0)
