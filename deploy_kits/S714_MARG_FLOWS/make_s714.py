#!/usr/bin/env python3
"""make_s714.py -- S714_MARG_FLOWS (S388, Sanjeevni, 06-Nov-2026; D827, D830): the Marg report flows, one public page each.
    python3 -B make_s714.py <dir holding finance_app.py and reports_tile.py> <out dir>
Each FROM file must carry its pinned md5; every edit must match exactly once; the TO md5s are printed.  marg_flows.py and
marg_flows_pics.py are NEW files carried whole in this kit (their pins in TO_PINS.md5).

  finance_app.py (THE PARENT'S -- a PLANNED line on board/_numbers, v940): ONE line in _gate -- GET/HEAD of the three flow pages (by their endpoints)
      pass without a login (marg_flows.py serves only fixed text and pictures there: no database read, no name, no figure)
  reports_tile.py (this project's): the four routes (the public index, a flow, a picture; the in-app list with the server's word on
      each report's last file) and one card on "Aaj ki reports" -- "Marg reports: har report ke steps" -- for every login that has it
"""
import hashlib
import os
import sys

FROM = {"finance_app.py": "00cc4935217ac0c59860be947565dbad", "reports_tile.py": "0598072c2b2b32adee80d28c4864f556"}

FA = [('''    p = request.path.rstrip("/") or request.path
    if p in PUBLIC_PATHS or request.path in PUBLIC_PATHS:
        return None
''', '''    p = request.path.rstrip("/") or request.path
    if p in PUBLIC_PATHS or request.path in PUBLIC_PATHS:
        return None
    if request.method in ("GET", "HEAD") and request.endpoint in ("reports_tile.s714_flows_index", "reports_tile.s714_flow", "reports_tile.s714_flow_pic"):
        return None                                           # S714 (D827, the Sanjeevni chat): the three Marg-flow pages -- fixed text and pictures only
''')]

RT = [
    ('''    if picked_date:
        body += "<p><a class=btn href='/finance/reports/aaj'>Aaj par wapas</a></p>"
    return _shell("Aaj ki reports", body, refresh=30 if not picked_date else 0)''',
     '''    body += ("<div class=card id=s714flows><div class=line><span class=big>Marg reports: har report ke steps</span> "
             "<a class=btn style='display:inline-block;width:auto;padding:8px 14px;margin-left:8px' href='/finance/reports/flows'>Kholiye</a>"
             "<br><span class=small>Har report ka apna page -- kisi ko bhi WhatsApp par bhej sakte hain.</span></div></div>")   # S714 (D827)
    if picked_date:
        body += "<p><a class=btn href='/finance/reports/aaj'>Aaj par wapas</a></p>"
    return _shell("Aaj ki reports", body, refresh=30 if not picked_date else 0)'''),
    ('''@bp.route("/finance/reports/aaj/api/healthz")''',
     '''# ---- S714 (06-Nov-2026, D827 / D830): the Marg report flows -- one public page each (marg_flows.py), and the in-app list ----------
def _s714_mf():
    try:
        import marg_flows as MF                                 # noqa: PLC0415
        return MF
    except Exception:                                           # noqa: BLE001
        return None


def _s714_public(body, mimetype="text/html; charset=utf-8", max_age=300):
    return Response(body, mimetype=mimetype, headers={"X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer",
                                                      "Cache-Control": "public, max-age=%d" % max_age, "X-Content-Type-Options": "nosniff"})


def _s714_last(cx, types):
    """The newest file the door filed under one of these mi_file types: dict(at, verdict, reason_hi) or None.  Reads only."""
    if not types or not _table_exists(cx, "mi_file"):
        return None
    r = cx.execute("SELECT received_at, verdict, reason FROM mi_file WHERE type IN (%s) ORDER BY replace(received_at,'T',' ') DESC LIMIT 1"
                   % ",".join("?" * len(types)), tuple(types)).fetchone()
    if not r:
        return None
    v = str(r[1] or "")
    return dict(at=str(r[0] or ""), verdict=v, reason_hi=("" if v == "VERIFIED" else hindi_reason(r[2], v)))


def _s714_ddmm(iso):
    s = str(iso or "")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])).strip() if len(s) >= 10 else s


@bp.route("/finance/flows")
def s714_flows_index():
    """PUBLIC (finance_app's gate, S714): every flow, one link each.  Fixed text only."""
    mf = _s714_mf()
    if mf is None:
        return "not available", 503
    return _s714_public(mf.index_page())


@bp.route("/finance/flows/<fid>")
def s714_flow(fid):
    """PUBLIC: one flow's steps with Marg's own screens and its WhatsApp share.  Fixed text only."""
    mf = _s714_mf()
    page = mf.flow_page(fid) if mf is not None else None
    if page is None:
        return redirect("/finance/flows", code=302)
    return _s714_public(page)


@bp.route("/finance/flows/pic/<name>")
def s714_flow_pic(name):
    """PUBLIC: one picture of a flow (marg_flows_pics.py, else reports_guide_pics.py)."""
    mf = _s714_mf()
    data = mf.pic(name[:-4]) if (mf is not None and name.endswith(".jpg")) else None
    if not data:
        return "no such picture", 404
    return _s714_public(data, mimetype="image/jpeg", max_age=86400)


@bp.route("/finance/reports/flows")
def s714_flows_app():
    """Inside the app (any medical role, as Aaj ki reports): every flow with the server's word on its last report."""
    u, err = _gate()
    if err:
        return _denied()
    mf = _s714_mf()
    if mf is None:
        return redirect("/finance/flows", code=302)
    en = "checker" in ((u or {}).get("roles") or [])
    return mf.app_page(_db(), en, _s714_last, _s714_ddmm)


@bp.route("/finance/reports/aaj/api/healthz")'''),
]

EDITS = {"finance_app.py": FA, "reports_tile.py": RT}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    sd, od = sys.argv[1], sys.argv[2]
    os.makedirs(od, exist_ok=True)
    for name in ("finance_app.py", "reports_tile.py"):
        raw = open(os.path.join(sd, name), "rb").read()
        if md5(raw) != FROM[name]:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
        src = raw.decode("utf-8")
        for i, (a, b) in enumerate(EDITS[name], 1):
            n = src.count(a)
            if n != 1:
                sys.exit("REFUSED: %s edit %d matches %d times" % (name, i, n))
            src = src.replace(a, b)
        out = src.encode("utf-8")
        open(os.path.join(od, name), "wb").write(out)
        print("%s  %s -> %s" % (name, FROM[name][:8], md5(out)))


if __name__ == "__main__":
    main()
