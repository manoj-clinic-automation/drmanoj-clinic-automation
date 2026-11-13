#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s815a.py LIVE_PY LIVE_HTML OUT_PY OUT_HTML -- kit S815 (13-Nov-2026, Sanjeevni session 446): Darpan's Kal ka hisaab gets the owner's
Marg watch question ('Doctor sahab ka sawaal'), first on his page, one tap per answer and an optional short line; no take-back (11-Oct rule).
darpan_kal.py a64353c0 -> the payload's mw_ask (staff and owner see it) + one door that only Darpan's (staff) login may use.
darpan_kal.html b89ca3ad -> the block, drawn first. Every patch is an exact anchor that occurs once; anything else stops the build."""
import hashlib, sys

FROM_PY = "a64353c066bfbaa5b226415786486850"
FROM_HTML = "b89ca3ad270af00eb174973d8975ad3d"


def one(s, a, b):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d): %r" % (s.count(a), a[:80]))
    return s.replace(a, b)


PY_BLOCK = '''

# ---- S815_MARG_WATCH_DARPAN_REPORTS (13-Nov-2026, Sanjeevni session 446): the owner's Marg watch question on Darpan's own page ----------------
# The question is the owner's (marg_billwatch.ask_send, to Darpan, on his page); its state lives in marg_watch_ask and is read and answered
# only through marg_billwatch's two functions -- one place for the rules (once only, an offered answer only, no take-back). Fail-soft:
# a fault here leaves the rest of his page whole.
def _s815_mw_ask(con, who):
    if who[0] not in ("staff", "owner"):
        return []
    try:
        import marg_billwatch as BW                            # noqa: PLC0415
        return BW.ask_for_darpan(con)
    except Exception:                                          # noqa: BLE001
        return []


@bp.route("/finance/darpan/kal/api/mw-ask-answer", methods=["POST"])
def api_s815_mw_ask_answer():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] != "staff":
        return jsonify(ok=False, error="not_permitted", message="Yeh jawab Darpan ke login se hi jaata hai."), 403
    b = request.get_json(silent=True) or {}
    try:
        import marg_billwatch as BW                            # noqa: PLC0415
    except Exception:                                          # noqa: BLE001
        return jsonify(ok=False, error="unavailable", message="Abhi jawab nahin ja raha -- thodi der baad."), 503
    ok, msg, code = BW.ask_answer_darpan(con, u["user"], b.get("id"), str(b.get("answer") or "").strip(), str(b.get("note") or ""))
    return jsonify(ok=ok, message=msg), code
# ---- S815 end ----
'''

HTML_FUNCS = '''/* S815: Doctor sahab ka sawaal -- the owner's question from the Marg watch; first on the page; one tap, an optional line; no take-back */
let MWBUSY=0;
function mwAskSec(a){
 if(!a||!a.length) return "";
 return a.map(x=>sec('<div style="border-left:4px solid #d92d20;padding-left:9px"><div class="row"><span class="k"><b>Doctor sahab ka sawaal</b></span></div>'+
  '<div>'+esc(x.text).split("\\n").join("<br>")+'</div></div>'+
  '<input class="big" id="mwn'+x.id+'" maxlength="300" placeholder="Kuch likhna ho to pehle yahan likhiye (zaroori nahi)" style="font-size:16px;margin:8px 0 2px;width:100%">'+
  (x.answers||[]).map(c=>'<span class="btn" style="display:block;margin:6px 0 0" onclick="mwAnswer('+x.id+',\\''+esc(c.code)+'\\')">'+esc(c.label)+'</span>').join(""))).join("");
}
async function mwAnswer(id,code){if(MWBUSY)return;MWBUSY=1;const e=el("mwn"+id);
 try{await post("/finance/darpan/kal/api/mw-ask-answer",{id:id,answer:code,note:(e&&e.value)||""});toast("Jawab chala gaya");}catch(e2){toast(""+e2);}
 MWBUSY=0;load();}
'''


def main():
    sp, sh, op, oh = sys.argv[1:5]
    rp, rh = open(sp, "rb").read(), open(sh, "rb").read()
    if hashlib.md5(rp).hexdigest() != FROM_PY:
        raise SystemExit("darpan_kal.py is not %s -- stopped" % FROM_PY[:8])
    if hashlib.md5(rh).hexdigest() != FROM_HTML:
        raise SystemExit("darpan_kal.html is not %s -- stopped" % FROM_HTML[:8])
    p, h = rp.decode("utf-8"), rh.decode("utf-8")
    p = one(p, "                amir_claims=_s446_claims(con),                 # S446 (D648): Amir's supplier claims -- Darpan's queue\n",
            "                amir_claims=_s446_claims(con),                 # S446 (D648): Amir's supplier claims -- Darpan's queue\n"
            "                mw_ask=_s815_mw_ask(con, who),                 # S815: the owner's Marg watch question, first on his page\n")
    p = one(p, "# ---- S446_AMIR_STAGES_BILLS end ----\n", "# ---- S446_AMIR_STAGES_BILLS end ----\n" + PY_BLOCK)
    h = one(h, " h+=amirClaimsSec(j.amir_claims);   /* S446 (D648): Amir ke claim -- two taps, nothing to type */\n el(\"body\").innerHTML=h;",
            " h+=amirClaimsSec(j.amir_claims);   /* S446 (D648): Amir ke claim -- two taps, nothing to type */\n"
            " el(\"body\").innerHTML=mwAskSec(j.mw_ask)+h;   /* S815: Doctor sahab ka sawaal -- first on the page */")
    h = one(h, "/* S446 (D648): Amir ke claim -- his supplier claims, Darpan's queue: supplier, bill, amount, raised when; two taps */\n",
            HTML_FUNCS + "/* S446 (D648): Amir ke claim -- his supplier claims, Darpan's queue: supplier, bill, amount, raised when; two taps */\n")
    bp_, bh = p.encode("utf-8"), h.encode("utf-8")
    open(op, "wb").write(bp_)
    open(oh, "wb").write(bh)
    print(hashlib.md5(bp_).hexdigest(), hashlib.md5(bh).hexdigest())


if __name__ == "__main__":
    main()
