"""S454_ORDER_SHEET_PROTOTYPE -- a REFERENCE, not code to install (the Sanjeevni chat, 03-Oct-2026).

Reads Marg's report PENDING ORDERS (PURCHASE) saved as text, checks its own unit totals, and draws the A4
order sheet the owner gave the staff on 03-Oct for their opinion. It shows (1) the parsing rules that held on the
real sheet of 02-Oct -- note the item line is split on the packing's shape, because a name that fills its column
leaves only one space before it -- and (2) the look of the printed page. It uses reportlab, which the server does
not have: the server draws its PDFs by hand.

    python S454_ORDER_SHEET_PROTOTYPE.py <sheet.txt> <out.pdf> [all]

'all' also prints the old pending lines, each tagged "purana, dd-mm".
"""
import re, sys, datetime
SRC=sys.argv[1]   # the order sheet as Marg saves it (text)
raw=open(SRC,encoding='utf-8',errors='replace').read()
assert 'PENDING ORDERS (PURCHASE)' in raw and '*** End of Report ***' in raw
lines=raw.splitlines()
item_re=re.compile(r'^  (\S.*?)\s+(\d+\*\d+)\.?\s+(OP-\d+)\s+(\d\d-\d\d-\d{4})\s+(\d+(?::\d+)?)\s+(-|\d+(?::\d+)?)\s+(\d+(?::\d+)?)\s+([\d.]+)\s+(\d+)\s*$')
sub_re=re.compile(r'^\s{20,}(\d+)\s+(\d+)\s+(\d+)\s*$')
tot_re=re.compile(r'^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
sup_re=re.compile(r'^(\S.*?)\s+Ph\.\s*(.*)$')
def units(q,pack):
    n=int(pack.split('*')[1])
    if ':' in q:
        a,b=q.split(':'); return int(a)*n+int(b)
    return int(q)
suppliers=[]; cur=None; grand=None; unknown=[]; in_body=False
for l in lines:
    if not l.strip(): continue
    s=l.rstrip()
    if s.strip().startswith('ITEM NAME'): in_body=True; continue      # the column heads end the letterhead / page furniture
    if s.strip().startswith('Continued..'): in_body=False; continue  # the next page's furniture follows
    if not in_body: continue
    if set(s.strip())<=set('-'): continue
    if s.strip().startswith('*** End of Report'): continue
    m=tot_re.match(s)
    if m: grand=(int(m.group(1)),int(m.group(3))); continue
    m=item_re.match(s)
    if m:
        name,pack,entry,date,q,rec,pend,rate,val=m.groups()
        cur['items'].append(dict(item=name.strip(),pack=pack,entry=entry,date=date,qty=q,units=units(q,pack),value=int(val)))
        continue
    m=sub_re.match(s)
    if m: cur['sub']=(int(m.group(1)),int(m.group(3))); continue
    m=sup_re.match(s)
    if m and not s.startswith(' '):
        nm=re.sub(r'\s{2,}.*$','',m.group(1)).strip()
        ph=[]
        for p in m.group(2).split():
            if p not in ph: ph.append(p)
        cur=dict(name=nm,phones=ph,items=[],sub=None); suppliers.append(cur); continue
    unknown.append(s)
assert not unknown, unknown
# the file's own arithmetic
tu=0
for s in suppliers:
    u=sum(i['units'] for i in s['items']); tu+=u
    if s['sub']: assert s['sub'][0]==u,(s['name'],s['sub'],u)
assert grand and grand[0]==tu,(grand,tu)
tv=sum(i['value'] for s in suppliers for i in s['items'])
assert abs(tv-grand[1])<=sum(len(s['items']) for s in suppliers)
allitems=[i for s in suppliers for i in s['items']]
d=lambda x: datetime.datetime.strptime(x,'%d-%m-%Y').date()
newest=max(d(i['date']) for i in allitems)
ALL_ITEMS=len(sys.argv)>3 and sys.argv[3]=='all'
keep=[]
for s in suppliers:
    its=[i for i in s['items'] if ALL_ITEMS or (newest-d(i['date'])).days<7]
    its=sorted(its,key=lambda i:-d(i['date']).toordinal())
    if its: keep.append(dict(name=s['name'],phones=s['phones'],items=its))
n_items=sum(len(s['items']) for s in keep)
n_new=sum(1 for s in keep for i in s['items'] if d(i['date'])==newest)
print('suppliers',len(suppliers),'lines',len(allitems),'units',tu,'value',tv,'printed',grand,'| kept',len(keep),'suppliers',n_items,'lines; newest',newest)
def qtxt(q):
    if ':' in q:
        a,b=q.split(':'); return a+' strip'+((' + '+b) if int(b) else '')
    return q

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
OUT=sys.argv[2]
W,H=A4; L=12*mm; R=W-12*mm; TOP=H-11*mm; BOT=11*mm
cols=[('Item',66),('Pack',17),('Qty',25),('Order',17),('Aaya',17),('Kam aaya / nahi aaya',44)]
xs=[L]
for _,w in cols: xs.append(xs[-1]+w*mm)
assert abs(xs[-1]-R)<0.5
ROW=6.7*mm; BAND=7.4*mm; GAP=1.7*mm; BOX=3.6*mm
order_date=newest.strftime('%d-%m-%Y')
entries=sorted({i['entry'] for s in keep for i in s['items']})
c=canvas.Canvas(OUT,pagesize=A4)
c.setTitle('Sanjeevni order sheet '+order_date); c.setAuthor('Sanjeevni Medicos')
def box(x,y,sz=BOX,lw=0.9):
    c.setLineWidth(lw); c.setStrokeGray(0); c.rect(x,y,sz,sz,stroke=1,fill=0)
def head(page,pages):
    y=TOP
    c.setFillGray(0); c.setFont('Helvetica-Bold',15); c.drawString(L,y-5*mm,'SANJEEVNI MEDICOS')
    c.setFont('Helvetica-Bold',12.5); c.drawString(L+62*mm,y-5*mm,'ORDER SHEET')
    c.setFont('Helvetica',9.5); c.drawRightString(R,y-5*mm,'Page %d / %d'%(page,pages))
    c.setFont('Helvetica',9.5)
    if ALL_ITEMS: c.drawString(L,y-10.2*mm,'Order: %s  \u00b7  Darpan (Marg)  \u00b7  %d supplier  \u00b7  %d item: %d naye, %d purane pending'%(order_date,len(keep),n_items,n_new,n_items-n_new))
    else:
        c.drawString(L,y-10.2*mm,'Order: %s  ·  Darpan (Marg, %s to %s)  ·  %d supplier  ·  %d item'%(order_date,entries[0],entries[-1],len(keep),n_items))
    c.setLineWidth(1.2); c.line(L,y-12.2*mm,R,y-12.2*mm)
    y=y-14*mm
    # column heads
    c.setFillGray(0.86); c.rect(L,y-6*mm,R-L,6*mm,stroke=0,fill=1); c.setFillGray(0)
    c.setLineWidth(0.6); c.rect(L,y-6*mm,R-L,6*mm,stroke=1,fill=0)
    c.setFont('Helvetica-Bold',8.6)
    for i,(t,w) in enumerate(cols):
        if i in (3,4): c.drawCentredString((xs[i]+xs[i+1])/2,y-4.2*mm,t)
        else: c.drawString(xs[i]+1.6*mm,y-4.2*mm,t)
        if i: c.line(xs[i],y-6*mm,xs[i],y)
    return y-6*mm-GAP
def foot():
    y=BOT+9*mm
    c.setLineWidth(0.6); c.line(L,y+3.4*mm,R,y+3.4*mm)
    c.setFont('Helvetica',8.8)
    c.drawString(L,y-0.6*mm,"Order ho gaya to 'Order' mein tick.  Maal aaya to 'Aaya' mein tick.  Kam aaya to kitna aaya, likhiye.  Nahi aaya to X.")
    c.setFont('Helvetica',9.5)
    c.drawString(L,y-7.2*mm,'Order kisne kiya: ____________________     Maal kisne liya: ____________________     Tareekh: ____________')
def block_h(s): return BAND+ROW*len(s['items'])+GAP
# paginate
pages=[[]]; avail=(TOP-14*mm-6*mm-GAP)-(BOT+14*mm); used=0
for s in keep:
    h=block_h(s)
    if used+h>avail and pages[-1]: pages.append([]); used=0
    pages[-1].append(s); used+=h
for pi,pg in enumerate(pages,1):
    y=head(pi,len(pages))
    for s in pg:
        # supplier band
        c.setFillGray(0.93); c.rect(L,y-BAND,R-L,BAND,stroke=0,fill=1); c.setFillGray(0)
        c.setLineWidth(0.9); c.rect(L,y-BAND,R-L,BAND,stroke=1,fill=0)
        c.setFont('Helvetica-Bold',10.6); c.drawString(L+1.6*mm,y-5.1*mm,s['name'])
        nx=L+1.6*mm+c.stringWidth(s['name'],'Helvetica-Bold',10.6)+4*mm
        c.setFont('Helvetica',9.6); ph='Ph. '+(', '.join(s['phones']) if s['phones'] else '(number nahi hai)')
        c.drawString(nx,y-5.1*mm,ph)
        # three boxes at the right
        labels=['WhatsApp','Call','Bill scan']; c.setFont('Helvetica',8.8)
        x=R-1.6*mm
        for lab in reversed(labels):
            w=c.stringWidth(lab,'Helvetica',8.8); x-=w; c.drawString(x,y-5.0*mm,lab); x-=1.3*mm+BOX; box(x,y-BAND+(BAND-BOX)/2); x-=4.2*mm
        assert nx+c.stringWidth(ph,'Helvetica',9.6) < x, ('band too tight',s['name'])
        y-=BAND
        for it in s['items']:
            c.setLineWidth(0.5); c.setStrokeGray(0.25); c.rect(L,y-ROW,R-L,ROW,stroke=1,fill=0)
            for i in range(1,len(cols)): c.line(xs[i],y-ROW,xs[i],y)
            c.setStrokeGray(0); c.setFillGray(0)
            c.setFont('Helvetica',10.2); c.drawString(xs[0]+1.6*mm,y-4.7*mm,it['item'])
            if d(it['date'])!=newest:
                tx=xs[0]+1.6*mm+c.stringWidth(it['item'],'Helvetica',10.2)+2*mm; c.setFont('Helvetica-Oblique',7.6); c.drawString(tx,y-4.6*mm,'purana, '+it['date'][:5]); assert tx+c.stringWidth('purana, 00-00','Helvetica-Oblique',7.6)<xs[1]
            c.setFont('Helvetica',9.2); c.drawString(xs[1]+1.6*mm,y-4.7*mm,it['pack'])
            c.setFont('Helvetica-Bold',10.4); c.drawString(xs[2]+1.6*mm,y-4.7*mm,qtxt(it['qty']))
            for i in ((4,) if d(it['date'])!=newest else (3,4)): box((xs[i]+xs[i+1])/2-BOX/2,y-ROW+(ROW-BOX)/2,lw=0.8)   # an old pending line has no box under Order
            y-=ROW
        y-=GAP
    foot(); c.showPage()
c.save()
print('pages',len(pages),[len(p) for p in pages])
