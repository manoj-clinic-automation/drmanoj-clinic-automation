# makes install_s823.py and INSTALL_AGENT_S823.bat from S499's proven pair (names and pins only)
import sys,hashlib,os
K=sys.argv[1]
new_md5=hashlib.md5(open("medical_agent.py","rb").read()).hexdigest()
s=open(os.path.join(K,"install_s499.py"),"rb").read()
assert hashlib.md5(s).hexdigest().startswith("4c37c400")
R=[(b"70d5c4e3c439eaa049acb27f9851688c",b"@FROM@"),(b"d91fa79ad972c39e531c70afb1a1c758",b"@TO@"),
   (b'FROM_VER = "S205.1"',b'FROM_VER = "@OLDV@"'),(b'TO_VER = "S499.1"',b'TO_VER = "@NEWV@"'),
   (b"S205.1 (70d5c4e3) -> S499.1",b"@OLDV@ (d91fa79a) -> @NEWV@"),(b"before_70d5c4e3",b"before_d91fa79a"),
   (b"names S499.1",b"names @NEWV@"),(b"S499_MEDICAL_AGENT_BACKUP",b"S823_MEDICAL_NET_LINE"),
   (b"S499",b"S823"),(b"s499",b"s823"),
   (b"@FROM@",b"d91fa79ad972c39e531c70afb1a1c758"),(b"@TO@",new_md5.encode()),(b"@OLDV@",b"S499.1"),(b"@NEWV@",b"S823.1")]
for a,b in R: s=s.replace(a,b)
open("install_s823.py","wb").write(s); imd5=hashlib.md5(s).hexdigest()
b=open(os.path.join(K,"INSTALL_AGENT_S499.bat"),"rb").read()
for a,c in [(b"S205.1 to S499.1",b"@X@"),(b"4c37c400b1898d81ffaaaf0be3f88504",imd5.encode()),
            (b"S499_MEDICAL_AGENT_BACKUP",b"S823_MEDICAL_NET_LINE"),(b"S499",b"S823"),(b"s499",b"s823"),(b"@X@",b"S499.1 to S823.1")]:
    b=b.replace(a,c)
open("INSTALL_AGENT_S823.bat","wb").write(b)
print("agent",new_md5,"installer",imd5,"bat",hashlib.md5(b).hexdigest())
