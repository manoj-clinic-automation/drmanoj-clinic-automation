#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""freshness_page.py -- S350 (20-Sep-2026), over S349. The collector's own freshness table, served read-only.

WHY. freshness.py (S267/S310) writes /root/finance/freshness.html every morning at 08:05 -- the one
surface that dates every job's last success -- and nothing has ever served it: S310's installer printed
https://followup.dr-manoj.in/finance/freshness and the owner got 404 (F-540). This mounts that URL.

WHAT IT DOES. GET /finance/freshness returns the file freshness.py wrote, byte-for-byte, with one line
added at the top saying WHEN it was written (IST) -- because a table of ages that does not date itself
is the F-45 shape. Nothing here computes a freshness of its own, nothing runs the collector, nothing
writes. If the file is not there yet the page says so and answers 503.

WHO. The same gate as the health page: require("checker") on the medical unit (the doctors).

The HTML path is the collector's: HTML_OUT= in /root/finance/freshness.conf, else freshness.html
beside that conf -- read here the same way freshness.paths_of() resolves it, without importing the
collector (a job script is not a library). FRESHNESS_HTML in the environment overrides both (the walk).
"""
import datetime as dt
import os
import time

from flask import Blueprint, Response

KIT = "S350_FRESHNESS_CLOCK"
bp = Blueprint("freshness_page", __name__)
CONF_PATH = os.environ.get("FRESHNESS_CONF", "/root/finance/freshness.conf")
_require = None


def html_path():
    """Where the collector writes its HTML -- freshness.py's own rule (paths_of)."""
    env = os.environ.get("FRESHNESS_HTML")
    if env:
        return env
    val = ""
    try:
        with open(CONF_PATH, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("HTML_OUT=") and not line.startswith("#"):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return val or os.path.join(os.path.dirname(CONF_PATH) or "/tmp", "freshness.html")


def _ist(ts):
    return (dt.datetime.utcfromtimestamp(ts) + dt.timedelta(hours=5, minutes=30)).strftime("%d-%b-%Y %H:%M IST")


def _banner(path, mtime, now=None):
    # S350: the wall clock, as an epoch -- time.time(). S349 took datetime.utcnow().timestamp(),
    # which on a box whose local clock is IST is 5.5 h behind the epoch, so the age read
    # negative and the banner said "0 min ago" for a file four hours old (found live, 12:4x IST).
    now = now if now is not None else time.time()
    age_h = max(0.0, (now - mtime) / 3600.0)
    if age_h < 1:
        age = "%d min ago" % int(age_h * 60)
    elif age_h < 48:
        age = "%.1f h ago" % age_h
    else:
        age = "%.1f days ago" % (age_h / 24.0)
    stale = age_h > 30                      # the collector runs daily at 08:05; 30 h = one missed run
    return ('<div style="font-family:system-ui,sans-serif;font-size:14px;padding:10px 14px;margin:0 0 12px;'
            'border-radius:8px;background:%s;color:%s">This table was written by the collector on '
            '<b>%s</b> (%s).%s &nbsp;<a href="/finance/health" style="color:inherit">&#8592; Health</a></div>'
            % ("#fdecea" if stale else "#eef6ee", "#8a1f11" if stale else "#1f5e2a",
               _ist(mtime), age,
               " <b>That is more than a day old: the 08:05 collector has not run since.</b>" if stale else ""))


def render(path=None, now=None):
    """(status, html). Pure: reads one file, computes nothing about freshness itself."""
    path = path or html_path()
    if not os.path.isfile(path):
        return 503, ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,initial-scale=1">'
                     '<title>Clinic freshness</title></head><body style="font-family:system-ui,sans-serif;'
                     'padding:24px"><h1>Clinic freshness</h1><p>The collector has not written its table yet '
                     '(it runs every morning at 08:05). Nothing to show.</p>'
                     '<p><a href="/finance/health">&#8592; Health</a></p></body></html>')
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        body = fh.read()
    banner = _banner(path, os.path.getmtime(path), now)
    low = body.lower()
    i = low.find("<body")
    if i >= 0:
        j = body.find(">", i)
        if j >= 0:
            body = body[:j + 1] + banner + body[j + 1:]
        else:
            body = banner + body
    else:
        body = banner + body
    return 200, body


@bp.route("/finance/freshness")
def page():
    u, err = _require("checker")
    if err:
        return err
    status, html = render()
    return Response(html, status=status, mimetype="text/html")


def init(app, require_fn):
    global _require
    _require = require_fn
    app.register_blueprint(bp)
    return bp
