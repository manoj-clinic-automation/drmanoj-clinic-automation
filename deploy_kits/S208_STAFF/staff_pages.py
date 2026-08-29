#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""staff_pages.py — the guided faces for the S207 joiner register.

THE OWNER'S INSTRUCTION (30-Aug-2026): "do Pravesh-type exit flow as a guided
page in the user-manage tile of my portal, and similar for Amir onboarding —
all is final and prepared already."

He is right that it is prepared: joiner_app.py (S207, 65 checks) already
carries the whole register — the six-step joining, the seven-step exit,
refusals in words, the never-reuse Emp Code rule, the WhatsApp message, the
owner password reset. THIS FILE ADDS ONLY PAGES. joiner_app.py is reused
byte-for-byte, unedited: what is prepared is not rebuilt (the owner's own
standing rule).

One page, two flows:  /finance/staff
    "Naya aadmi" (the Amir shape) and "Vidaai" (the Pravesh shape), each a
    guided ladder of steps driven by the register's own API -- so a step out
    of order is refused BY THE REGISTER, in words, and the page merely shows
    what it said. The page invents no rule of its own.

Point the portal's user-manage tile at /finance/staff -- one link.
"""
import os

from flask import Blueprint, send_file


def joiner_require(require_fn):
    """Adapter that lets the S207 register stay byte-for-byte untouched.

    finance_app's require() returns a USER DICT; the register was written
    against a require() returning a plain name and binds that value straight
    into SQL -- so with the live signature its very first /open would crash
    (sqlite: 'type dict is not supported'). Caught by this kit's selftest,
    which mimics the live signature on purpose. One adapter beats editing a
    proven 65-check file.
    """
    def _shim(*roles):
        u, err = require_fn(*roles)
        if isinstance(u, dict):
            u = u.get("user") or u.get("username") or "?"
        return u, err
    return _shim

HERE = os.path.dirname(os.path.abspath(__file__))

bp = Blueprint("staffpages", __name__)

_require = None


def init(app, require_fn):
    global _require
    _require = require_fn
    app.register_blueprint(bp)
    return bp


@bp.route("/finance/staff")
def page_staff():
    u, err = _require("checker")
    if err:
        return err
    return send_file(os.path.join(HERE, "staff_manage.html"))
