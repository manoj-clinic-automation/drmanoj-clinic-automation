"""make_s918.py -- S918 (the parent, S498, 21-Nov-2026): check_screens.py 5d00b2e8 -> TO. A parked X-ray photo of a person who is
not registered anywhere (a free X-ray -- three of September) is CLOSED in one tap, 'Free X-ray', on Shavez's
card and on the owner's waiting card: the photo's group is marked not in Docterz and explained 'free X-ray' at once (the two
answers the owner's 'Not in Docterz' tile already reads), so it leaves every list. Four anchors."""
import hashlib, sys
FROM = "5d00b2e80f25875a431b97b0a0331515"
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM:
    sys.exit("FROM pin mismatch: %s" % hashlib.md5(b).hexdigest())
t = b.decode("utf-8")
def rep(old, new, name):
    global t
    assert t.count(old) == 1, "anchor %s: %d" % (name, t.count(old))
    t = t.replace(old, new)
rep('        g = group_of(con, sid, nodz=(a in ("id_fixed", "not_xray")))',
    '        g = group_of(con, sid, nodz=(a in ("id_fixed", "not_xray", "free_xray")))   # S918: + free X-ray (from his Not-in-Docterz tile too)',
    "A group")
rep('        if a == "id_fixed":\n            if not _id_ok(con, nid):',
    '        if a == "free_xray":                             # S918: a free X-ray, closed in one tap -- not in Docterz AND explained\n'
    '            for x in g:\n'
    '                _write(con, "xf:" + x["src_id"], "xray_file", x["clinic_id"] or "", "no_docterz", "free X-ray (S918)", u)\n'
    '                _write(con, "pg:" + x["src_id"], "xray_payment", "", "explained", PG_WHY["muft"], u)\n'
    '            con.commit()\n'
    '            return 200, {"ok": True, "msg": W("Free X-ray \\u2014 band ho gaya", "Closed: free X-ray") + many}\n'
    '        if a == "id_fixed":\n            if not _id_ok(con, nid):',
    "B answer")
rep('''<button class="b3" id="nodz">Docterz mein nahi</button>''',
    '''<button class="b3" id="nodz">Free X-ray</button>''', "C staff button")
rep('''var nd=$('nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:it.key,a:'no_docterz'})''',
    '''var nd=$('nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:it.key,a:'free_xray'})''', "D staff tap")
rep('''(TAB==='wait'?'<button class="b2" id="nodz">Not in Docterz (not registered)</button>':'')''',
    '''(TAB==='wait'?'<button class="b2" id="nodz">Free X-ray (not registered)</button>':'')''', "E owner button")
rep('''var nd=el.querySelector('#nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:key,a:'no_docterz'}).then(function(r){if(r.ok){B.nodz.unshift(i);drop(key,r.msg);}''',
    '''var nd=el.querySelector('#nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:key,a:'free_xray'}).then(function(r){if(r.ok){drop(key,r.msg);}''', "F owner tap")
open(dst, "w", encoding="utf-8", newline="").write(t)
print(hashlib.md5(t.encode("utf-8")).hexdigest())
