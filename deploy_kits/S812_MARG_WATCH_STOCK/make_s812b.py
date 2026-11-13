#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s812b.py LIVE_BW SEG OUT -- kit S812 (13-Nov-2026, Sanjeevni session 445): marg_billwatch.py 9be1b460 -> the Marg watch with section A
(stock moved in Marg with no record) on top: the moves, his close on each row (D923), the floor field (D943), Explained after all (D914), the stock
record's own health line (F-1329). Every patch is an exact anchor that occurs once; anything else stops the build."""
import hashlib, sys

FROM = "9be1b460f2ebf763af98afc7e56b068f"


def one(s, a, b):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d): %r" % (s.count(a), a[:80]))
    return s.replace(a, b)


JS_ADD = r"""function mwHClose(b){var box=b.closest('.closep');var m=box.querySelector('.msg');var c=box.querySelector('input[type=radio]:checked');
 if(!c){m.textContent='Pick one of the choices first.';return;}
 mwPost('/api/hand/close',{id:parseInt(b.getAttribute('data-h'),10),decision:c.value,reason:box.querySelector('input[type=text]').value},m);}
function mwHReopen(b){mwPost('/api/hand/reopen',{id:parseInt(b.getAttribute('data-h'),10)},b.parentNode.querySelector('.msg'));}
function mwHLot(b){var m=b.parentNode.querySelector('.msg');if(b.getAttribute('data-sure')!=='1'){b.setAttribute('data-sure','1');
 b.textContent='Tap again to close all '+b.getAttribute('data-n')+' moves';return;}mwPost('/api/hand/oklot',{n:parseInt(b.getAttribute('data-n'),10)},m);}
function mwHFloor(b){var row=b.parentNode;mwPost('/api/hand/floor',{rupees:row.querySelector('input').value},row.querySelector('.msg'));}
"""

ROUTES = '''
    @bp.route(PAGE + "/api/hand/close", methods=["POST"])            # S812: section A -- his close on a move (D923)
    def api_hand_close():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = hand_close(con, str(u.get("user") or "owner"), b.get("id"), str(b.get("decision") or ""), str(b.get("reason") or ""))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/hand/reopen", methods=["POST"])
    def api_hand_reopen():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = hand_reopen(con, str(u.get("user") or "owner"), b.get("id"))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/hand/oklot", methods=["POST"])
    def api_hand_oklot():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = hand_ok_lot(con, str(u.get("user") or "owner"), b.get("n"))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/hand/floor", methods=["POST"])            # D943: the floor, a figure he changes on the page
    def api_hand_floor():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = hand_set_floor(con, str(u.get("user") or "owner"), b.get("rupees"))
        return jsonify(ok=ok, message=msg), code

    return bp


def init(app, db_getter, require_fn):'''


def main():
    src, seg, out = sys.argv[1:4]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    s = one(s, "import datetime as dt\n", "import collections\nimport datetime as dt\n")
    s = one(s, "# ====================================================================== his acts", open(seg, encoding="utf-8").read() +
            "# ====================================================================== his acts")
    s = one(s, " table.bill td:first-child{display:block;font-weight:600}table.bill tr.tot td{border:0}}\n\"\"\"",
            " table.bill td:first-child{display:block;font-weight:600}table.bill tr.tot td{border:0}}\n.bad{color:#b42318}\n\"\"\"")
    s = one(s, "[].forEach.call(document.querySelectorAll('.jump a'),", JS_ADD + "[].forEach.call(document.querySelectorAll('.jump a'),")
    s = one(s, "'Stock that moved in Marg with no record is the next part to be built.</p>')",
            "'Stock that moved in Marg with no record is section A, at the top.</p>')")
    s = one(s, "    h.append(inputs_html(con, B))\n", "    h.append(inputs_html(con, B))\n    h.append(hand_html(con))                                  # S812: section A\n")
    s = one(s, "h.append('<div class=\"jump\"><a href=\"#inputs\">Today\\'s inputs</a>",
            "h.append('<div class=\"jump\"><a href=\"#inputs\">Today\\'s inputs</a><a href=\"#stock\">Stock moved with no record</a>")
    s = one(s, "\n    return bp\n\n\ndef init(app, db_getter, require_fn):", ROUTES)
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
