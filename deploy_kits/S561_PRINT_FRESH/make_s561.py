#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s561.py -- kit S561_PRINT_FRESH (15-Oct-2026): the anchored patcher. Builds porders_s454.py and order_sheet_pdf.py from the box's
live bytes by counted edits: each anchor must occur exactly once in the text it is applied to, in order, else the build STOPS; each source
must be at its FROM pin and each result at its TO pin.
    python3 -B make_s561.py --fin /root/finance --out <dir>
Writes only into --out."""
import argparse
import hashlib
import os
import sys

PINS = {
    "porders_s454.py": ("72e7fd563dadf2ae657fadef66e4e72e", "1c3d3927163e08114e3e26c5f06052a4"),
    "order_sheet_pdf.py": ("d0735df84f17a67474bc0cecd58e5c6c", "b0cc86945d560e8cce842b799913e021"),
}

P_HEAD_A = ("#    GET  /finance/porders/s454/marg.pdf              S543: Marg's own PENDING ORDERS export, printed as Marg printed it "
            "(marg_order_pdf)\n")
P_HEAD_B = P_HEAD_A + (
    "#    S561 (15-Oct-2026): both PDF buttons open a new address at every tap (?s=<the export's stamp>&t=<the moment>, the moment set\n"
    "#    again by the click script); the two routes name the file by the export's time (the order sheet also by the print's) and send\n"
    "#    Cache-Control no-store, max-age=0 / Pragma no-cache / Expires 0 -- a phone has no old copy of either paper it could reopen.\n")

P_JS_A = '\n}\n"""\n\n\ndef shell(con, u, title, body, back="/portal", login=""):\n'
P_JS_B = ('\n}\n"""\n'
          "FRESH_JS = (\"<script>document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-fresh]');\"\n"
          "            \"if(a){var u=new URL(a.href);u.searchParams.set('t',Date.now());a.href=u.href;}},true);</script>\")"
          "   # S561: the tap's own moment\n"
          '\n\ndef shell(con, u, title, body, back="/portal", login=""):\n')

P_BTN_A = ("        h.append('<a class=\"big out\" id=\"print\" href=\"%s/s454/sheet.pdf\" target=\"_blank\">%s</a>' % (P, L(en, \"print\")))\n"
           "        h.append('<a class=\"big out\" id=\"margpdf\" href=\"%s/s454/marg.pdf\" target=\"_blank\">%s</a>' % (P, L(en, \"margpdf\")))\n")
P_BTN_B = ("        fq = _fresh_q(con)                                    # S561: a new address at every tap -- the export's stamp, the moment\n"
           "        h.append('<a class=\"big out\" id=\"print\" href=\"%s\" data-fresh=\"1\" target=\"_blank\">%s</a>' % (esc(P + \"/s454/sheet.pdf?\" + fq), L(en, \"print\")))\n"
           "        h.append('<a class=\"big out\" id=\"margpdf\" href=\"%s\" data-fresh=\"1\" target=\"_blank\">%s</a>' % (esc(P + \"/s454/marg.pdf?\" + fq), L(en, \"margpdf\")))\n"
           "        h.append(FRESH_JS)\n")

P_RT_A = '''@bp.route(P + "/s454/sheet.pdf")
def r_sheet_pdf():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import order_sheet_pdf                                    # noqa: PLC0415
    data = order_sheet_pdf.build(con)
    OS.audit(con, who(u), "s454_sheet_printed", "", dict(bytes=len(data)))
    con.commit()
    return data, 200, {"Content-Type": "application/pdf", "Cache-Control": "no-store",
                       "Content-Disposition": 'inline; filename="order_sheet_%s.pdf"' % OS.today().isoformat()}


@bp.route(P + "/s454/marg.pdf")
def r_marg_pdf():
    """S543 (D716): Marg's own PENDING ORDERS export, printed as Marg printed it -- beside the system's sheet, to compare."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import marg_order_pdf                                     # noqa: PLC0415
    ns = OS.newest_sheet(con)
    data = marg_order_pdf.build(con)
    OS.audit(con, who(u), "s454_marg_pdf_printed", (ns or {}).get("id", ""), dict(bytes=len(data), sheet=(ns or {}).get("id")))
    con.commit()
    stamp = re.sub(r"[^0-9-]", "", str((ns or {}).get("stamp") or "")) or OS.today().isoformat()
    return data, 200, {"Content-Type": "application/pdf", "Cache-Control": "no-store",
                       "Content-Disposition": 'inline; filename="marg_order_%s.pdf"' % stamp}
'''
P_RT_B = '''# ------------------------------------------------------------------ S561: the two papers, fresh at every tap
STAMP_RE = re.compile(r"^(\\d{4})(\\d\\d)(\\d\\d)-(\\d\\d)(\\d\\d)")         # the export's capture stamp, as order_sheet._stamp_text reads it


def _export(con):
    """(newest sheet, its stamp) -- the stamp ('20261015-141250', written by marg_watch / marg_router) only when it has that shape, else ''."""
    ns = OS.newest_sheet(con)
    st = str((ns or {}).get("stamp") or "")
    return ns, (st if STAMP_RE.match(st) else "")


def _fresh_q(con):
    """The query both PDF buttons carry: s = the newest export's stamp ('' when it has none), t = the server's moment (YYYYMMDDHHMMSS)."""
    return "s=%s&t=%s" % (quote(_export(con)[1]), OS.now().strftime("%Y%m%d%H%M%S"))


def _pdf_name(kind, st, n):
    """The file name: the export's dd-mm_HHMM from its stamp (no stamp: the print's), and for the order sheet the print's HHMMSS too."""
    m = STAMP_RE.match(st or "")
    base = ("%s-%s_%s%s" % (m.group(3), m.group(2), m.group(4), m.group(5))) if m else n.strftime("%d-%m_%H%M")
    return ("order_sheet_%s_%s.pdf" % (base, n.strftime("%H%M%S"))) if kind == "sheet" else ("marg_order_%s.pdf" % base)


def _pdf_headers(name):
    return {"Content-Type": "application/pdf", "Cache-Control": "no-store, max-age=0", "Pragma": "no-cache", "Expires": "0",
            "Content-Disposition": 'inline; filename="%s"' % name}


@bp.route(P + "/s454/sheet.pdf")
def r_sheet_pdf():
    """The printed order sheet -- always the newest sheet; s and t only make the address new (S561)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import order_sheet_pdf                                    # noqa: PLC0415
    n = OS.now()                                              # S561: one clock, the print's moment (never OS.today(), which follows ORDER_TODAY)
    name = _pdf_name("sheet", _export(con)[1], n)
    data = order_sheet_pdf.build(con, now=n)
    OS.audit(con, who(u), "s454_sheet_printed", "", dict(bytes=len(data), file=name))
    con.commit()
    return data, 200, _pdf_headers(name)


@bp.route(P + "/s454/marg.pdf")
def r_marg_pdf():
    """S543 (D716): Marg's own PENDING ORDERS export, printed as Marg printed it -- beside the system's sheet, to compare. S561: named by
    the export's time; s and t only make the address new."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import marg_order_pdf                                     # noqa: PLC0415
    n = OS.now()
    ns, st = _export(con)
    name = _pdf_name("marg", st, n)
    data = marg_order_pdf.build(con)
    OS.audit(con, who(u), "s454_marg_pdf_printed", (ns or {}).get("id", ""), dict(bytes=len(data), sheet=(ns or {}).get("id"), file=name))
    con.commit()
    return data, 200, _pdf_headers(name)
'''

S_HEAD_A = ("#  pending\". Every quantity is order_sheet.qty_of (qty_words). _build takes the page size (marg_order_pdf prints A4 landscape).\n")
S_HEAD_B = S_HEAD_A + (
    "#\n"
    "#  S561_PRINT_FRESH (15-Oct-2026): every page's foot also says when it was printed -- \"chhapa: dd-mm-yyyy hh:mm  ·  Sanjeevni\", as\n"
    "#  Marg's own PDF says it -- drawn inside the room the foot already keeps (the page count and the rows on a page do not change).\n"
    "#  build(con, lay=None, now=None): now is the print's moment (the route's one clock; order_sheet.now() when not given).\n")

S_CONST_A = 'BAND_LABELS = ("Bill scan", "Call", "WhatsApp")\n'
S_CONST_B = ('PRINTED = "chhapa: %s  ·  Sanjeevni"                     # S561: the words of marg_order_pdf\'s foot, size 8, on every page\n'
             + S_CONST_A)

S_BUILD_A = "def build(con, lay=None):\n    lay = lay or layout(con)\n"
S_BUILD_B = ("def build(con, lay=None, now=None):\n    lay = lay or layout(con)\n"
             "    now = now or OS.now()                                     # S561: the print's moment\n")

S_FOOT_A = ("        for k, s in enumerate(f2):\n            p.text(LM, ty - k * 4.2 * MM, s, FOOT2_SZ)\n        out.append(p)\n")
S_FOOT_B = ("        for k, s in enumerate(f2):\n            p.text(LM, ty - k * 4.2 * MM, s, FOOT2_SZ)\n"
            "        p.text(LM, ty - (len(f2) - 1) * 4.2 * MM - 3.6 * MM, PRINTED % now.strftime(\"%d-%m-%Y %H:%M\"), 8)   # S561: inside _foot_h's room\n"
            "        out.append(p)\n")

EDITS = {
    "porders_s454.py": [(P_HEAD_A, P_HEAD_B), (P_JS_A, P_JS_B), (P_BTN_A, P_BTN_B), (P_RT_A, P_RT_B)],
    "order_sheet_pdf.py": [(S_HEAD_A, S_HEAD_B), (S_CONST_A, S_CONST_B), (S_BUILD_A, S_BUILD_B), (S_FOOT_A, S_FOOT_B)],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, src_bytes):
    frm, to = PINS[name]
    if md5(src_bytes) != frm:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- it changed after this kit was built" % (name, md5(src_bytes), frm))
    t = src_bytes.decode("utf-8")
    for i, (a, b) in enumerate(EDITS[name], 1):
        n = t.count(a)
        if n != 1:
            raise SystemExit("STOP: %s edit %d: its anchor occurs %d times (must be exactly once)" % (name, i, n))
        t = t.replace(a, b, 1)
    out = t.encode("utf-8")
    if md5(out) != to:
        raise SystemExit("STOP: %s built to %s, not its TO pin %s" % (name, md5(out), to))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", default="/root/finance")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name in PINS:
        with open(os.path.join(a.fin, name), "rb") as fh:
            out = build(name, fh.read())
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(out)
        print("built %s %s -> %s (%d counted edits)" % (name, PINS[name][0][:8], PINS[name][1][:8], len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
