import importlib.util, pandas as pd, sys
from datetime import date, timedelta
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
M=load(sys.argv[1],'m')
D0=date(2026,10,1); ID0=21000000; PER=30000
def aid(d,k=0): return str(ID0+(d-D0).days*PER+100+k)
FU=[];V=[];n=[0]
def fu(uid,presc,due,k=0,conf='High'):
    n[0]+=1; FU.append(dict(Followup_ID=f'F{n[0]:06d}',Followup_Log_Date=str(due-timedelta(1)),Due_Date=str(due),
      Appointment_ID=aid(presc,k),Patient_UID_Resolved=uid,Identity_Confidence=conf,Followup_Status='')); return f'F{n[0]:06d}'
def vis(uid,d): V.append(dict(Visit_ID=f'V{len(V)+1:06d}',Visit_Date=str(d),Patient_UID=uid))
# anchors: one single-visit patient per day, 7-day follow-ups
for i in range(0,60):
    d=D0+timedelta(i); u=f'ANC{i}'; vis(u,d); fu(u,d,d+timedelta(7),k=50)
today=date(2026,11,10); due=date(2026,11,7)
c={}
# 1 prescribed 3 days ahead, only visit is the prescribing one -> OPEN
vis('P1',due-timedelta(3)); c['1 prescribing visit at due-3 stays open']=(fu('P1',due-timedelta(3),due),'open')
# 2 prescribed 7 ahead, early return at due-2 -> CLOSED
vis('P2',due-timedelta(7)); vis('P2',due-timedelta(2)); c['2 early return at due-2 closes']=(fu('P2',due-timedelta(7),due),'closed')
# 3 two open rows, one visit on the later due -> BOTH closed
vis('P3',date(2026,10,10)); r31=fu('P3',date(2026,10,10),date(2026,10,17)); vis('P3',date(2026,10,25)); r32=fu('P3',date(2026,10,25),due); vis('P3',due)
c['3a rule b older row closes']=(r31,'closed'); c['3b rule b newer row closes']=(r32,'closed')
# 3c overlapping rows: R1 (presc 20-Oct, due 1-Nov), R2 (presc 28-Oct, due 7-Nov), one visit 7-Nov -> BOTH closed
vis('P8',date(2026,10,20)); r81=fu('P8',date(2026,10,20),date(2026,11,1)); vis('P8',date(2026,10,28)); r82=fu('P8',date(2026,10,28),due); vis('P8',due)
c['3c overlapping older row closes']=(r81,'closed'); c['3d overlapping newer row closes (rule b)']=(r82,'closed')
# 4 wrong patient: P4 open; another UID visits on the due date -> P4 OPEN
vis('P4',due-timedelta(10)); vis('P4x',due); c['4 wrong-patient visit does not close']=(fu('P4',due-timedelta(10),due),'open')
# 5 visit at due-4 -> OPEN
vis('P5',due-timedelta(10)); vis('P5',due-timedelta(6)); c['5 10-day advice: visit at due-6 does not close']=(fu('P5',due-timedelta(10),due),'open')
vis('P9',due-timedelta(10)); vis('P9',due-timedelta(5)); c['5b 10-day advice: visit at due-5 closes']=(fu('P9',due-timedelta(10),due),'closed')
vis('PA',due-timedelta(30)); vis('PA',due-timedelta(12)); c['5c 30-day advice: visit at due-12 closes']=(fu('PA',due-timedelta(30),due),'closed')
vis('PB',due-timedelta(7)); vis('PB',due-timedelta(4)); c['5d 7-day advice: visit at due-4 does not close']=(fu('PB',due-timedelta(7),due),'open')
# 6 R1 closed by visit X which prescribed R2 (due X+2); no later visit -> R2 OPEN
vis('P6',date(2026,10,20)); fu('P6',date(2026,10,20),date(2026,11,4)); vis('P6',date(2026,11,5)); c['6 prescribing visit of R2 never closes R2']=(fu('P6',date(2026,11,5),date(2026,11,7)),'open')
# 7 on-time return on due -> CLOSED (both)
vis('P7',due-timedelta(7)); vis('P7',due); c['7 visit on due closes']=(fu('P7',due-timedelta(7),due),'closed')
fu_df=pd.DataFrame(FU)
for col in M.FU_COLS:
    if col not in fu_df: fu_df[col]=''
fu_df=fu_df.fillna('')
v_df=pd.DataFrame(V)
R=M.recalculate_statuses(fu_df,v_df,today,str(today)).set_index('Followup_ID')
bad=0
for k,(fid,exp) in c.items():
    st=R.at[fid,'Followup_Status']; got='closed' if st.startswith('Returned') else 'open'
    ok=got==exp; bad+=not ok; print(('PASS' if ok else 'FAIL'),k,'->',st)
print('RESULT', 'GREEN' if not bad else f'RED ({bad} fail)')
