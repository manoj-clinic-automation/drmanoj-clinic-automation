#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s808.py -- kit S808_WA_LADDER_SEND. Remakes the kit's /root/portal/wa_ladder.py from the LIVE bytes.

    make_s808.py <the live wa_ladder.py> <out folder>      -> <out folder>/portal/wa_ladder.py

wa_ladder.py gains the page's controls and the doors only: it still opens no connection and calls no sender (the sending is
wa_ladder_send.py). Every anchor must be found exactly once in a file whose md5 is the one this kit was built on; otherwise
nothing is written.
"""
import hashlib
import os
import sys

FROM = "cb19729379836550183bad91736559d5"
HERE = os.path.dirname(os.path.abspath(__file__))

EDITS = [
    # 1 -- the file's own account of itself
    ('''SHOW ONLY. This file holds NO send code: it opens no network connection and calls no sender. It answers one question for the
owner -- "which approved WhatsApp message would go to whom today?" -- and keeps the STOP list.
''',
     '''THE LISTS. This file holds NO send code: it opens no network connection and calls no sender. It answers one question for the
owner -- "which approved WhatsApp message would go to whom today?" -- and keeps the STOP list.
S808 (13-Nov-2026): the page gains a switch for each message, the tests and today's record. The SENDING is in
wa_ladder_send.py; the doors below only hand a request over to it (a list's key and row tokens -- never a number or a name).
'''),
    ('''  POST /portal/messages/api/restop S805: the doctor puts a number he took off back on the stop list
''',
     '''  POST /portal/messages/api/restop S805: the doctor puts a number he took off back on the stop list
  POST /portal/messages/api/send/<what>  S808: switch | stopall | test | testok | ticked -> wa_ladder_send.door (the doctor only)
'''),
    # 2 -- the version
    ('VERSION = "S805 1.3"\n', 'VERSION = "S808 1.4"\n'),
    # 3 -- the sending part, found when asked for (absent or broken = the page stands, show only)
    ('''    def _doctor():
        return ((sso_user(request) or {}).get("role")) == "doctor"
''',
     '''    def _doctor():
        return ((sso_user(request) or {}).get("role")) == "doctor"

    def _send_mod():                                                   # S808: the sending lives in its own file
        try:
            import wa_ladder_send
            return wa_ladder_send
        except Exception:                                              # noqa: BLE001 -- the page stands without it, show only
            return None
'''),
    # 4 -- the plan door: the switches, the tests and today's record ride on the plan
    ('''        p = plan(day)
        if p is None:
            return jsonify({"ok": False, "msg": "database not readable"}), 503
        resp = jsonify(p)
''',
     '''        p = plan(day)
        if p is None:
            return jsonify({"ok": False, "msg": "database not readable"}), 503
        S = _send_mod()                                                # S808
        if S is None:
            p["send"] = {"ok": False, "msg": "The sending part is not on the server."}
        else:
            try:
                S.decorate(p, sso_user(request))
            except Exception as e:                                     # noqa: BLE001 -- the lists still show
                p["send"] = {"ok": False, "broken": True,
                             "msg": "The switches could not be read (%s). Sending may still be ON. Tell Claude." % type(e).__name__}
                p["sends"] = False
        resp = jsonify(p)
'''),
    # 5 -- the one door for every change the page can ask for
    ('''    @app.route("/portal/messages/api/restop", methods=["POST"])       # S805
    @login_required
    def wl_restop():
        return _stop_door(restop)
''',
     '''    @app.route("/portal/messages/api/restop", methods=["POST"])       # S805
    @login_required
    def wl_restop():
        return _stop_door(restop)

    @app.route("/portal/messages/api/send/<what>", methods=["POST"])  # S808
    @login_required
    def wl_send(what):
        if not _doctor():
            return jsonify({"ok": False, "msg": "Not for this login."}), 403
        if request.headers.get("X-Messages") != "1":                   # only this page's own script sends it
            return jsonify({"ok": False, "msg": "bad request"}), 400
        S = _send_mod()
        if S is None:
            return jsonify({"ok": False, "msg": "The sending part is not on the server. Nothing was sent."}), 503
        d = request.get_json(silent=True)
        if not isinstance(d, dict):
            d = {}
        try:
            ok, text = S.door(str(what), d, sso_user(request))
        except Exception as e:                                         # noqa: BLE001
            ok, text = False, "It did not work (%s). Do not press again: look at 'What went today', and tell Claude." % type(e).__name__
        resp = jsonify({"ok": bool(ok), "msg": str(text)})
        resp.headers["Cache-Control"] = "no-store"
        return resp, (200 if ok else 409)
'''),
]


def make(src):
    s = src.decode("utf-8")
    for old, new in EDITS:
        if s.count(old) != 1:
            raise SystemExit("anchor not found exactly once: %r" % old[:60])
        s = s.replace(old, new)
    a = s.index('PAGE = r"""')
    b = s.index('"""\n\n\nif __name__ == "__main__":', a)
    if s.count('PAGE = r"""') != 1:
        raise SystemExit("the page is not where it was")
    with open(os.path.join(HERE, "parts", "page.html"), encoding="utf-8") as fh:
        page = fh.read()
    if '"""' in page or not page.endswith("</body></html>\n"):
        raise SystemExit("the kit's page is not whole")
    s = s[:a] + 'PAGE = r"""' + page[:-1] + s[b:]
    return s.encode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    with open(sys.argv[1], "rb") as fh:
        live = fh.read()
    if hashlib.md5(live).hexdigest() != FROM:
        raise SystemExit("the live wa_ladder.py is not the one this kit was built on (%s)" % hashlib.md5(live).hexdigest()[:8])
    out = make(live)
    os.makedirs(os.path.join(sys.argv[2], "portal"), exist_ok=True)
    with open(os.path.join(sys.argv[2], "portal", "wa_ladder.py"), "wb") as fh:
        fh.write(out)
    print("made", hashlib.md5(out).hexdigest())
