

# ---- S973 (27-Nov-2026, Sanjeevni session 540, kit S973_VOUCHER_SCANS; kit C of S534_FINAL_BUILD_PLAN, D1091 plan 2.4) --------------------
#  RECEPTION'S LINE: on "Aaj ka bill kaam", a group "Stock voucher scan karna hai" -- every print Amir handed over ('Print diya -- reception
#  ko') that no scan answers yet (voucher_scan.reception_lines, assets.db READ ONLY): "<ITEM> (Amir ne print diya)" with Scan karo -- the
#  intake on the pharmacy lane with the voucher's number, back to this page. The line leaves by itself when the scan lands. Its count joins
#  the page's own (reception's home row). The one push went when Amir tapped (voucher_scan.after_print). No new tile, no typing.
KIT_S973 = "S973_VOUCHER_SCANS"
T.update({"bk_sv": ("Stock voucher scan karna hai · %d", "Stock vouchers to scan · %d"),
          "bk_sv_s": ("Amir ne print diya %s", "Amir handed the print over %s")})


def _s973_vs():
    import voucher_scan as VS                                 # noqa: PLC0415 -- beside this file
    return VS


_s736_model_before_s973 = s736_model


def s736_model(con, now=None, raised=None):                   # noqa: F811 -- S973: + the stock vouchers to scan
    m = _s736_model_before_s973(con, now, raised)
    sv = []
    try:
        sv = _s973_vs().reception_lines(con)
    except Exception as e:                                    # noqa: BLE001 -- the page stands without it
        print("S973 lines failed: %r" % (e,), file=sys.stderr)
    m["s973"] = sv
    m["n"] = int(m.get("n") or 0) + len(sv)
    return m


_billkaam_page_before_s973 = billkaam_page


def billkaam_page():                                          # noqa: F811 -- S973
    out = _billkaam_page_before_s973()
    if not (isinstance(out, tuple) and len(out) == 3 and isinstance(out[0], str)):
        return out
    page, code, hdr = out
    try:
        u, con, kind, login, err = _auth_page()
        if err:
            return out
        en = u["_en"]
        VS = _s973_vs()
        sv = VS.reception_lines(con)
        if sv:
            back = P + "/s454/billkaam"
            h = ['<div class="grp" id="g_s973" style="color:#1f3864">%s</div>' % L(en, "bk_sv", len(sv))]
            for x in sv:
                h.append('<div class="card" data-s973="%d"><div class="nm">%s%s</div><div class="sb">%s</div>'
                         '<div class="two"><a class="g" href="%s">%s</a></div></div>'
                         % (int(x["id"]), esc(x["item"]), (" · " + esc(x["no"])) if x["no"] else "", esc(L(en, "bk_sv_s", OS.ddmm(x["at"]))),
                            esc(VS.intake_link(x["no"], back)), L(en, "scankaro")))
            add = "".join(h)
            if '<div class="ok" id="alldone">' in page:
                page = re.sub(r'<div class="ok" id="alldone">.*?</div></div>', "", page, count=1, flags=re.S)
            page = page.replace('<div class="mut" id="bkaaj"', add + '<div class="mut" id="bkaaj"', 1)
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was drawn
        print("S973 billkaam failed: %r" % (e,), file=sys.stderr)
    return page, code, hdr

# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------
