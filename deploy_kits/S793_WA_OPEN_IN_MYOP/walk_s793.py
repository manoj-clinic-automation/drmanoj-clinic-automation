#!/usr/bin/python3
# walk_s793.py -- kit S793_WA_OPEN_IN_MYOP (S431, 11-Nov-2026). Reads a portal_inbox.py as text (no import, no database, no patient row):
#   walk_s793.py <dir holding portal_inbox.py>            -> "WALK OK n/n" when every check is green
#   walk_s793.py <dir holding the LIVE file> --control    -> "CONTROL: red (k of n)" when the S793 checks fail on it (as they must)
import ast, os, py_compile, re, sys, tempfile
d = sys.argv[1]; control = "--control" in sys.argv
p = os.path.join(d, "portal_inbox.py")
src = open(p, encoding="utf-8").read()
R = []
def chk(name, ok): R.append((name, bool(ok)))
try:
    tmp = tempfile.mkdtemp(); py_compile.compile(p, cfile=os.path.join(tmp, "x.pyc"), doraise=True); comp = True
except Exception:
    comp = False
chk("W0 compiles", comp)
page = ""
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "PAGE" for t in node.targets):
        page = node.value.value
chk("W1 the inbox PAGE is found", len(page) > 10000)
ACC = "https://in.app.myoperator.com/chat/dfb2da39-0d45-4383-ad58-d63f29c09920/91/"
chk("W2 the clinic number's MyOperator chat address is in the page once", page.count(ACC) == 1)
chk("W3 myopUrl() takes the last 10 digits and gives nothing for a shorter number",
    'function myopUrl(p){var d=String(p==null?"":p).replace(/\\D/g,"");return d.length>=10?MYOP_CHAT+d.slice(-10):"";}' in page)
m = re.search(r"function drawHead\(\)\{(.*?)\n\}", page, re.S)
head = m.group(1) if m else ""
chk("W4 the header draws the MyOperator button before Call", head.find('cls:"myopbtn"') != -1 and head.find('cls:"myopbtn"') < head.find('cls:"callbtn"'))
chk("W5 it opens in a new tab with rel=noopener", 'target:"_blank",rel:"noopener"' in head)
chk("W6 no number -> an empty text node, never 'null'", ':document.createTextNode(""))' in head)
chk("W7 the Call button is still there, once", page.count("svg(IC.call)") == 1)
chk("W8 the button's style and its narrow-phone rule", ".myopbtn{height:44px;" in page and "@media (max-width:440px){.myopbtn .lbl{display:none}" in page)
chk("W9 the icon", "IC={ext:'" in page)
chk("W10 the health answer names S793", '"kit": "S793"' in src)
chk("W11 the routes unchanged (17)", src.count("@app.route") == 17)
chk("W12 nothing sends, reads or stores differently (myop_send, run_retries, ingest untouched by S793)",
    src.count("S793") == 2 and all(f in src for f in ("def myop_send(", "def run_retries(", "def ingest(")))
bad = [n for n, ok in R if not ok]
for n, ok in R:
    print(("ok   " if ok else "BAD  ") + n)
if control:
    print("CONTROL: red (%d of %d)" % (len(bad), len(R)) if len(bad) >= 8 else "CONTROL: NOT red (%d of %d)" % (len(bad), len(R)))
else:
    print("WALK OK %d/%d" % (len(R), len(R)) if not bad else "WALK RED %d of %d" % (len(bad), len(R)))
