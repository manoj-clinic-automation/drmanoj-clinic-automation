import re, sqlite3, sys
def split_sql(sql):
    # remove /* */ block comments
    sql=re.sub(r'/\*.*?\*/','',sql,flags=re.S)
    out=[]; buf=[]; i=0; inq=None
    while i<len(sql):
        ch=sql[i]
        if inq:
            buf.append(ch)
            if ch==inq: inq=None
            i+=1; continue
        if ch in ("'",'"'):
            inq=ch; buf.append(ch); i+=1; continue
        if ch=='-' and i+1<len(sql) and sql[i+1]=='-':
            j=sql.find('\n',i);  i=len(sql) if j<0 else j; continue
        if ch==';':
            out.append("".join(buf)); buf=[]; i+=1; continue
        buf.append(ch); i+=1
    if "".join(buf).strip(): out.append("".join(buf))
    return out
db=sys.argv[1]; f=sys.argv[2]
con=sqlite3.connect(db)
applied=0; skipped=0; failed=[]
for s in split_sql(open(f).read()):
    t=s.strip()
    if not t: continue
    kw=t.split()[0].upper() if t.split() else ""
    if kw in ("CREATE","ALTER","DROP"):
        try:
            con.execute(t); applied+=1
        except Exception as e:
            failed.append((kw, str(e)[:60], t.split('\n')[0][:70]))
    else:
        skipped+=1
con.commit(); con.close()
print(f"DDL applied={applied} skipped(non-DDL)={skipped} failed={len(failed)}")
for k,e,h in failed: print(f"  [{k}] {e}  |  {h}")
