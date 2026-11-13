#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s814b.py LIVE_BW SEG OUT -- kit S814 (13-Nov-2026, Sanjeevni session 445): marg_billwatch.py e6b4e534 (S812) -> Ask on every row of A and B.
Every patch is an exact anchor that occurs once; anything else stops the build.
S446: the JS line breaks inside its strings are written \\\\n -- the page's script is a plain Python string (F at the S446 close)."""
import hashlib, sys

FROM = "e6b4e53490416c6e62ae9299e6891bc6"


def one(s, a, b):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d): %r" % (s.count(a), a[:80]))
    return s.replace(a, b)


JS_ADD = r"""function mwAskInit(box){var r=box.querySelector('input[type=radio]:checked');mwAskText(r||box.querySelector('input'));}
function mwAskText(el){var box=el.closest('.mwask');var w=box.querySelector('input[type=radio]:checked');var who=w?w.value:'';
 var ls=[].map.call(box.querySelectorAll('.mwk:checked'),function(c){return c.getAttribute('data-line');});
 var tail=who==='amir'?'Apne card par jawab chuniye.':'Bataiye.';var t;
 if(box.getAttribute('data-kind')==='A'){t='Marg mein stock badla, par system mein iska koi bill, sale ya voucher nahi hai:\\n'+
  ls.map(function(l,i){return (i+1)+'. '+l;}).join('\\n')+'\\nYeh kisne aur kyon badla? '+tail;}
 else{t=box.getAttribute('data-detail')+'\\nYeh kisne aur kyon kiya? '+tail;}
 box.querySelector('.mwtext').textContent=ls.length?t:'Tick at least one row.';
 var c=box.querySelector('.mwcard');c.style.display=who==='amir'?'':'none';
 box.querySelector('.mwwa').href='https://wa.me/?text='+encodeURIComponent(t);}
function mwAskKeys(box){return [].map.call(box.querySelectorAll('.mwk:checked'),function(c){return c.value;});}
function mwAskWho(box){var w=box.querySelector('input[type=radio]:checked');return w?w.value:'';}
function mwAskSend(b){var box=b.closest('.mwask');var m=box.querySelector('.msg');if(!mwAskWho(box)){m.textContent='Pick whom first.';return;}
 if(!mwAskKeys(box).length){m.textContent='Tick at least one row.';return;}
 mwPost('/api/ask',{keys:mwAskKeys(box),to:mwAskWho(box),card:true},m);}
function mwAskCopy(b){var box=b.closest('.mwask');var m=box.querySelector('.msg');if(!mwAskWho(box)){m.textContent='Pick whom first.';return;}
 if(!mwAskKeys(box).length){m.textContent='Tick at least one row.';return;}
 try{navigator.clipboard.writeText(box.querySelector('.mwtext').textContent).then(function(){mwPost('/api/ask',{keys:mwAskKeys(box),to:mwAskWho(box),card:false},m);},
 function(){m.textContent='Copy was refused by the browser — select the text and copy it.';});}catch(e){m.textContent='Select the text and copy it.';}}
function mwAskTaken(a){var box=a.closest('.mwask');var m=box.querySelector('.msg');if(!mwAskWho(box)){m.textContent='Pick whom first.';return false;}
 if(!mwAskKeys(box).length){m.textContent='Tick at least one row.';return false;}
 mwPost('/api/ask',{keys:mwAskKeys(box),to:mwAskWho(box),card:false},m);return true;}
function mwAskNotice(b){mwPost('/api/ask/notice',{on:b.getAttribute('data-on')==='1'},b.parentNode.querySelector('.msg'));}
[].forEach.call(document.querySelectorAll('.mwask'),mwAskInit);
"""

ROUTES = '''
    @bp.route(PAGE + "/api/ask", methods=["POST"])                  # S814: Ask (plan v4 section 8)
    def api_ask():
        u, con, b, err = _post()
        if err:
            return err
        keys = b.get("keys") if isinstance(b.get("keys"), list) else []
        ok, msg, code = ask_send(con, str(u.get("user") or "owner"), keys, str(b.get("to") or ""), bool(b.get("card")))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/ask/notice", methods=["POST"])
    def api_ask_notice():
        u, con, b, err = _post()
        if err:
            return err
        if not isinstance(b.get("on"), bool):
            return jsonify(ok=False, message="On or off?"), 400
        ok, msg, code = ask_set_notice(con, str(u.get("user") or "owner"), b["on"])
        return jsonify(ok=ok, message=msg), code

    return bp


def init(app, db_getter, require_fn):'''


def main():
    src, seg, out = sys.argv[1:4]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    s = one(s, "# ====================================================================== his acts", open(seg, encoding="utf-8").read() +
            "# ====================================================================== his acts")
    s = one(s, "[].forEach.call(document.querySelectorAll('.jump a'),", JS_ADD + "[].forEach.call(document.querySelectorAll('.jump a'),")
    s = one(s, "\n    return bp\n\n\ndef init(app, db_getter, require_fn):", ROUTES)
    s = one(s, '    fs = B["findings"]\n    new = [f for f in fs if not f["before"] and f["status"] == "open"]\n',
            '    fs = B["findings"]\n    _ask_attach(con, fs)                                      # S814: the asks on the bill rows\n'
            '    new = [f for f in fs if not f["before"] and f["status"] == "open"]\n')
    s = one(s, "def status_html(f):\n    act = f.get(\"act\") or {}\n",
            "def status_html(f):\n    act = f.get(\"act\") or {}\n    if f.get(\"ask\") and f[\"status\"] not in (\"closed\", \"settled\") and act.get(\"action\") != \"notok\":\n"
            "        return ask_chip(f[\"ask\"])                           # S814\n")
    s = one(s, "    det = '<tr class=\"dt\" id=\"d%s\" hidden><td colspan=\"6\">%s%s%s</td></tr>' % (fk, strip_html(f), panel, decision_html(f))",
            "    det = '<tr class=\"dt\" id=\"d%s\" hidden><td colspan=\"6\">%s%s%s%s%s</td></tr>' % (fk, strip_html(f), panel, decision_html(f),\n"
            "                                                                         ask_answer_html(f.get(\"ask\")), ask_box_b(f))   # S814")
    s = one(s, "        else:\n            out[\"counted\"].append(r)\n    return out\n",
            "        else:\n            out[\"counted\"].append(r)\n"
            "    try:                                                       # S814: the asks, and the moves of the same closing that may ride along\n"
            "        S = ask_state(con)\n    except Exception:                                          # noqa: BLE001\n        S = {}\n"
            "    for r in rows:\n        r[\"ask\"] = S.get(\"hand:%d\" % int(r[\"id\"]))\n"
            "    try:                                                       # S446 review S6: a question on a move no longer open leaves Amir's card\n"
            "        ask_withdraw(con, {\"hand:%d\" % int(r[\"id\"]) for r in rows}, {\"hand:%d\" % int(r[\"id\"]) for r in out[\"counted\"]})\n"
            "    except Exception:                                          # noqa: BLE001\n        try:\n            con.rollback()\n"
            "        except sqlite3.Error:\n            pass\n"
            "    for r in out[\"counted\"]:\n        r[\"peers\"] = [p for p in out[\"counted\"] if p[\"day_to\"] == r[\"day_to\"] and p[\"id\"] != r[\"id\"]]\n"
            "    return out\n")
    s = one(s, "def _hand_status(r):\n    act = r.get(\"act\") or {}\n",
            "def _hand_status(r):\n    act = r.get(\"act\") or {}\n    if r.get(\"ask\") and act.get(\"action\") not in (\"close\", \"notok\"):\n"
            "        return ask_chip(r[\"ask\"])                           # S814\n")
    s = one(s, "body += '<p class=\"note\" style=\"margin:0 0 8px\">%s</p>%s' % (esc(H.remedy_of(r)), _hand_decide(r))",
            "body += '<p class=\"note\" style=\"margin:0 0 8px\">%s</p>%s%s%s' % (esc(H.remedy_of(r)), _hand_decide(r), ask_answer_html(r.get(\"ask\"), False),\n"
            "                                                                          ask_box_a(r, r.get(\"peers\") or []))   # S814")
    s = one(s, "    h.append(_spine_line(con))\n", "    h.append(_spine_line(con))\n    h.append(ask_notice_html(con))                            # S814: the answer notice, OFF to begin with\n")
    s = one(s, "def ensure(con):\n", "def ensure(con):\n    ask_ensure(con)                                           # S814\n")
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
