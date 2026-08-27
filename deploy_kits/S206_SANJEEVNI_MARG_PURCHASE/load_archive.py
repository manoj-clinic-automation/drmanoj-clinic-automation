import sys,glob,os,json,collections
K='/sessions/rcw-01y9d9zd4e5vdfg7p1wmkijm/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits'
sys.path.insert(0,K+'/S206_SANJEEVNI_MARG_PURCHASE'); sys.path.insert(0,K+'/S205_LIVE_TOOLS/manojz')
import marg_purchase as MP, marg_stock as MS, marg_report as MR
A=os.path.expanduser('~/mnt/Downloads/margsync/MargArchive')
out={}
# purchase
pur=[]
for p in sorted(glob.glob(A+'/PURCHASE_ITEMWISE/*/*.XLS')):
    r=MP.read_purchase(p); m=os.path.basename(os.path.dirname(p))
    for x in r['rows']: x['month']=m
    pur+=r['rows']
out['purchase']=pur
# sale item lines, DEDUPED by (date,bill,seq) because files overlap
seen=set(); sale=[]; files=[]
for p in sorted(glob.glob(A+'/SALE_BILLWISE/*/*.XLS')):
    try: rep=MR.read_report(p,keep_items=True)
    except Exception as e: files.append((os.path.basename(p),'REFUSED: %s'%e)); continue
    n=0
    for d in rep['days']:
        for it in d.get('items') or []:
            ps=it.get('parsed') or {}
            key=(it['bill_date'],it['bill_no'],ps.get('seq'))
            if key in seen: continue
            seen.add(key); n+=1
            sale.append({'date':it['bill_date'],'bill':it['bill_no'],'item':ps.get('item_name'),
                         'pack':ps.get('pack'),'strips':ps.get('qty_strips'),'loose':ps.get('qty_loose'),
                         'amount_p':ps.get('amount_p'),'expiry':ps.get('expiry_ym'),'batch':ps.get('batch')})
    files.append((os.path.basename(p),'ok, %d new lines'%n))
out['sale']=sale; out['sale_files']=files
# stock + expiry
st={}
for p in sorted(glob.glob(A+'/STOCK_CLOSING/2026-08/*.XLS')):
    r=MS.read_closing(p); st[r['store']]={'as_on':r['as_on'],'rows':r['rows']}
out['stock']=st
exp=[]
for p in sorted(glob.glob(A+'/STOCK_EXPIRY/2026-08/*.XLS')):
    r=MS.read_expiry(p)
    for x in r['rows']: x['source']=r['source']
    exp+=r['rows']
out['expiry']=exp
json.dump(out,open(os.path.expanduser('~/q1.json'),'w'))
print("purchase rows :",len(pur))
print("sale lines    :",len(sale),"  distinct dates:",len({s['date'] for s in sale}))
print("stock stores  :",list(st))
print("expiry rows   :",len(exp))
print("\nsale files:")
for f,s in files: print("  %-58s %s"%(f[:58],s))
