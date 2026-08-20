#!/usr/bin/env python3
"""dr_query — the STANDARD read-only box query tool for the clinic finance DB.

Opens finance.db READ-ONLY (mode=ro): it physically cannot write. Purpose:
one command, one clean paste — no more hand-crafted SQL back and forth.

Usage (run on the box):
  python3 /root/deploy/dr_query.py day    2026-08-17
  python3 /root/deploy/dr_query.py marg   2026-08-17
  python3 /root/deploy/dr_query.py cash   30
  python3 /root/deploy/dr_query.py custody
  python3 /root/deploy/dr_query.py flags  [2026-08-17]     (all open flags if no date)
  python3 /root/deploy/dr_query.py tables
  python3 /root/deploy/dr_query.py sql "SELECT ... "        (SELECT/WITH only; refuses writes)

Add new named reports over time; the SELECT-only 'sql' mode covers anything ad-hoc.
"""
import sqlite3, sys, os, json

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")

def con():
    return sqlite3.connect("file:%s?mode=ro" % DB, uri=True)

def rows(c, sql, args=()):
    c.row_factory = sqlite3.Row
    return [dict(r) for r in c.execute(sql, args).fetchall()]

def rs(p):  # paise -> rupees string
    try: return "%.2f" % (int(p)/100.0)
    except Exception: return str(p)

def head(t): print("\n== %s ==" % t)

def cmd_day(c, date):
    head("DAY %s" % date)
    for r in rows(c, "SELECT id,status,source,entered_by,approved_by FROM day_entry WHERE unit='medical' AND business_date=?", (date,)):
        print("  day_id %s | %s | source %s | by %s | approved_by %s" % (r['id'],r['status'],r['source'],r['entered_by'],r['approved_by']))
        did=r['id']
        rev=rows(c,"SELECT mode,SUM(amount_p) s FROM day_line WHERE day_entry_id=? GROUP BY mode",(did,))
        print("    revenue:", ", ".join("%s %s"%(x['mode'],rs(x['s'])) for x in rev) or "none")
        ex=rows(c,"SELECT COUNT(*) n,COALESCE(SUM(amount_p),0) s FROM day_expense WHERE day_entry_id=?",(did,))[0]
        print("    expenses: %d rows, %s" % (ex['n'], rs(ex['s'])))
        adv=rows(c,"SELECT id,amount_p,ledger_posted,ledger_ref FROM day_expense WHERE day_entry_id=? AND category_fixed='salary_advance'",(did,))
        for a in adv: print("      salary_advance #%s %s ledger_posted=%s ref=%s" % (a['id'],rs(a['amount_p']),a['ledger_posted'],a['ledger_ref']))
        mv=rows(c,"SELECT direction,party,amount_p,reference FROM cash_movement WHERE day_entry_id=?",(did,))
        for m in mv: print("      movement %s->%s %s (%s)" % (m['direction'],m['party'],rs(m['amount_p']),m['reference']))
        si=rows(c,"SELECT COUNT(*) n,COALESCE(SUM(amount_p),0) s FROM sale_item WHERE day_entry_id=?",(did,))[0]
        print("    Marg sale_item linked: %d bills, %s" % (si['n'], rs(si['s'])))
    sl=rows(c,"SELECT COUNT(*) lines,COUNT(DISTINCT bill_no) bills FROM sale_line_item WHERE unit='medical' AND business_date=?",(date,))[0]
    print("  Marg line-items dated %s: %d lines / %s bills" % (date, sl['lines'], sl['bills']))
    fl=rows(c,"SELECT kind,status FROM recon_exception WHERE unit='medical' AND business_date=?",(date,))
    print("  flags:", ", ".join("%s(%s)"%(f['kind'],f['status']) for f in fl) or "none")

def cmd_marg(c, date):
    head("MARG %s" % date)
    for r in rows(c,"SELECT id,received_at,filename_hint,status,applied_at,applied_by,apply_result_json,survey_json FROM marg_push_staging WHERE unit='medical' ORDER BY id DESC"):
        ar=r.get('apply_result_json') or ""
        touches = date in (r.get('survey_json') or "") or date in ar
        if not touches: continue
        print("  push#%s %s '%s' status=%s applied_at=%s by=%s" % (r['id'],r['received_at'],r['filename_hint'],r['status'],r['applied_at'],r['applied_by']))
        try: print("    result:", json.dumps(json.loads(ar)))
        except Exception: print("    result:", ar[:200])
    si=rows(c,"SELECT si.day_entry_id d,COUNT(*) n,COALESCE(SUM(si.amount_p),0) s FROM sale_item si JOIN day_entry e ON e.id=si.day_entry_id WHERE e.unit='medical' AND e.business_date=? GROUP BY 1",(date,))
    print("  bills linked to the %s day:" % date, si or "NONE")
    sl=rows(c,"SELECT COUNT(*) lines,COUNT(DISTINCT bill_no) bills FROM sale_line_item WHERE unit='medical' AND business_date=?",(date,))[0]
    print("  Marg line-items dated %s: %d lines / %s bills" % (date, sl['lines'], sl['bills']))

def cmd_cash(c, n):
    head("CASH LEDGER last %s days" % n)
    for r in rows(c,"SELECT business_date d,cash_in_p,upi_in_p,expense_p,cash_out_p,closing_p FROM v_cash_ledger WHERE unit='medical' ORDER BY business_date DESC LIMIT ?", (int(n),)):
        print("  %s | cash %s | upi %s | exp %s | out %s | closing %s" % (r['d'],rs(r['cash_in_p']),rs(r['upi_in_p']),rs(r['expense_p']),rs(r['cash_out_p']),rs(r['closing_p'])))

def cmd_custody(c):
    head("CASH CUSTODY (net per party, this FY)")
    net={}
    for r in rows(c,"SELECT to_party p,SUM(amount_p) s FROM cash_custody_event WHERE unit='medical' GROUP BY 1"): net[r['p']]=net.get(r['p'],0)+r['s']
    for r in rows(c,"SELECT from_party p,SUM(amount_p) s FROM cash_custody_event WHERE unit='medical' GROUP BY 1"): net[r['p']]=net.get(r['p'],0)-r['s']
    for p,v in sorted(net.items(), key=lambda x:-x[1]): print("  %-18s %s" % (p, rs(v)))
    head("recent custody events")
    for r in rows(c,"SELECT event_date,from_party,to_party,amount_p FROM cash_custody_event WHERE unit='medical' ORDER BY event_date DESC LIMIT 8"):
        print("  %s  %s -> %s  %s" % (r['event_date'],r['from_party'],r['to_party'],rs(r['amount_p'])))

def cmd_flags(c, date=None):
    head("FLAGS" + (" "+date if date else " (all open)"))
    if date: q,a="SELECT business_date,kind,status,detail FROM recon_exception WHERE unit='medical' AND business_date=? ORDER BY kind",(date,)
    else:    q,a="SELECT business_date,kind,status,detail FROM recon_exception WHERE unit='medical' AND status='open' ORDER BY business_date DESC LIMIT 60",()
    for r in rows(c,q,a): print("  %s | %s | %s | %s" % (r['business_date'],r['kind'],r['status'],(r['detail'] or "")[:70]))

def cmd_tables(c):
    head("TABLES")
    for r in rows(c,"SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY type,name"): print("  ", r['name'])

def cmd_sql(c, q):
    ql=q.strip().lower()
    if not (ql.startswith("select") or ql.startswith("with")):
        sys.exit("REFUSED: read-only tool — only SELECT / WITH queries are allowed.")
    if ";" in q.rstrip(";"):
        sys.exit("REFUSED: one statement only.")
    head("SQL")
    for r in rows(c,q):
        print("  ", {k:(rs(v) if isinstance(v,int) and abs(v)>=1000 else v) for k,v in r.items()})

def main():
    a=sys.argv[1:]
    if not a or a[0] in ("-h","--help"): print(__doc__); return
    c=con()
    try:
        cmd=a[0]
        if   cmd=="day":     cmd_day(c, a[1])
        elif cmd=="marg":    cmd_marg(c, a[1])
        elif cmd=="cash":    cmd_cash(c, a[1] if len(a)>1 else 30)
        elif cmd=="custody": cmd_custody(c)
        elif cmd=="flags":   cmd_flags(c, a[1] if len(a)>1 else None)
        elif cmd=="tables":  cmd_tables(c)
        elif cmd=="sql":     cmd_sql(c, a[1])
        elif cmd=="selftest":
            cmd_tables(c); print("\nSELFTEST OK — read-only, %d tables/views" % len(rows(c,"SELECT name FROM sqlite_master WHERE type IN ('table','view')")))
        else: sys.exit("unknown command; run --help")
    finally: c.close()

if __name__=="__main__": main()
