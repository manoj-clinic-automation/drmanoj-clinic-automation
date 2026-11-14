"""apply_s839.py -- kit S839_FREE_XRAY_WORDS: 'Free X-ray' on every screen (his word 20:41 IST 14-Nov, 'MUFT = FREE').
usage: python3 -I apply_s839.py <in_dir> <out_dir>  (check_screens.py f3c16787, S836's) -- every anchor exactly once."""
import hashlib, os, sys
IN, OUT = sys.argv[1], sys.argv[2]
FROM = "f3c16787"
R = [
 ('VERSION = "S836 1"', 'VERSION = "S839 1"'),
 ("his console's red line goes.\n", "his console's red line goes.\n  * S839 (his word 20:41 IST 14-Nov, 'MUFT = FREE'): the words are 'Free X-ray' on every screen, Hindi and English.\n"),
 ('"muft": "complimentary (Muft X-ray)",', '"muft": "free X-ray",'),
 ('(a complimentary X-ray?)"}', '(a free X-ray?)"}'),
 (" complimentary? One tap: 'Complimentary (Muft X-ray)', or 'Slip made' if it was billed after all\"", " free X-ray? One tap: 'Free X-ray', or 'Slip made' if it was billed after all\""),
 ('muft X-ray?"\n', 'free X-ray?"\n'),
 ('not in Docterz -- complimentary?" %', 'not in Docterz -- free X-ray?" %'),
 ('"Muft X-ray? %d"', '"Free X-ray? %d"'),
 ("&mdash; muft X-ray? Ek tap se band:", "&mdash; free X-ray? Ek tap se band:"),
 ('data-pg="muft">Muft X-ray</button>', 'data-pg="muft">Free X-ray</button>'),
 ("X-rayed, not registered · complimentary? one tap closes it", "X-rayed, not registered · free X-ray? one tap closes it"),
 ("usually a complimentary X-ray: one tap “Complimentary (Muft X-ray)” closes it", "usually a free X-ray: one tap “Free X-ray” closes it"),
 ("Not in Docterz — complimentary? One tap closes it:", "Not in Docterz — free X-ray? One tap closes it:"),
 ('data-pg="muft">Complimentary (Muft X-ray)</button>', 'data-pg="muft">Free X-ray</button>'),
 ("split(' · complimentary?')", "split(' · free X-ray?')"),
]
b = open(os.path.join(IN, "check_screens.py"), "rb").read()
if hashlib.md5(b).hexdigest()[:8] != FROM:
    sys.exit("STOP: check_screens.py is not S836's f3c16787")
t = b.decode("utf-8")
for k, (o, n) in enumerate(R, 1):
    if t.count(o) != 1:
        sys.exit("STOP: anchor %d found %d times: %r" % (k, t.count(o), o[:60]))
    t = t.replace(o, n)
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "check_screens.py"), "wb").write(t.encode("utf-8"))
print("check_screens.py %s -> %s (%d anchors)" % (FROM, hashlib.md5(t.encode("utf-8")).hexdigest()[:8], len(R)))
