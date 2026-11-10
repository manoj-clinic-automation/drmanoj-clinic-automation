


# ---- S778 (10-Nov-2026, Sanjeevni session 425, kit S778_ORDER_SCREEN; D890, the owner's mock approved 15:08 IST) ------------------------
#  The order screen (order_s778.py beside this file holds the logic):
#   (a) Order karna hai opens with the OLD ORDERS in a red box -- ordered, not come 3 days after (Sundays not counted), the age big,
#       'Dobara order karo' / 'Ab nahi milta'; the dealer's card names its old lines 'PURANA · N din'.
#   (b) 'Ab nahi milta' on a card line or a red-box line: off today's list at once; the doctor's Needs-you line opens
#       /finance/porders/s454/abnahi (Stop it everywhere / Keep ordering / Undo).
#   (c) the wrong-dealer check on the cards and in the red box ('<X> ke card par bhejo' / '<dealer> hi sahi', remembered).
#  order_sheet.entries / order_supplier / cron_pass and order_rules.needs_you_lines are wrapped here, fail-soft: an error in S778 leaves
#  every screen as it was before it. POST /finance/porders/api/s778/{again, na, na_answer (owner), dealer_ok, move}.
def _s778():
    import order_s778                                         # noqa: PLC0415 -- beside this file
    return order_s778


def _s778_log(where, e):
    print("S778 %s failed: %r" % (where, e), file=sys.stderr)


def _s778_g():
    from flask import g                                       # noqa: PLC0415
    return g


_s778_entries_before = OS.entries
_s778_order_supplier_before = OS.order_supplier
_s778_cron_before = OS.cron_pass


def _s778_entries(con, *a, **k):
    out = _s778_entries_before(con, *a, **k)
    try:
        return _s778().adjust_entries(con, [dict(e, lines=list(e["lines"])) for e in out])
    except Exception as e:                                    # noqa: BLE001 -- the cards as order_sheet made them
        _s778_log("entries", e)
        return out


def _s778_order_supplier(con, who_, sn, via):
    body, code = _s778_order_supplier_before(con, who_, sn, via)
    try:
        if code == 200 and body.get("ok") and body.get("order_id") and not body.get("already"):
            _s778().mark_done(con, sn, body["order_id"])
    except Exception as ex:                                   # noqa: BLE001
        _s778_log("order_supplier mark", ex)
    return body, code


def _s778_cron(con, who_="cron"):
    out = _s778_cron_before(con, who_)
    try:
        out["s778"] = _s778().clear_by_bills(con)
    except Exception as e:                                    # noqa: BLE001
        out["s778"] = "error: %s" % str(e)[:80]
    return out


OS.entries = _s778_entries
OS.order_supplier = _s778_order_supplier
OS.cron_pass = _s778_cron
try:
    import order_rules as _s778_OR                            # noqa: E402
    _s778_nyl_before = _s778_OR.needs_you_lines

    def _s778_nyl(con):
        out = _s778_nyl_before(con)
        try:
            return list(out) + _s778().owner_lines(con)
        except Exception as e:                                # noqa: BLE001
            _s778_log("needs_you", e)
            return out
    _s778_OR.needs_you_lines = _s778_nyl
except Exception as _e778:                                    # noqa: BLE001
    _s778_log("needs_you wrap", _e778)

_s778_order_list_before = order_list
_s778_card_before = _card
_s778_supplier_page_before = supplier_page
S778_MARK = '<div id="msg" class="err" style="display:none"></div>'


def order_list():                                             # noqa: F811 -- S778: the red box at the top, the cards' tags and warnings
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    g = None
    try:
        g = _s778_g()
        g.s778_con = con
    except Exception as e:                                    # noqa: BLE001
        _s778_log("order_list g", e)
    r = _s778_order_list_before()
    try:
        import order_rules                                    # noqa: PLC0415
        if isinstance(r, tuple) and r[1] == 200 and not order_rules._frozen(con) and S778_MARK in r[0]:
            S, en = _s778(), u["_en"]
            add = '<style>%s</style>%s%s' % (S.CSS, S.ok_html(en, request.args), S.red_box(con, en))
            n = S.wrong_count(con, OS.entries(con))
            if n:
                add += '<div class="s778wd" id="s778wdtop">%s</div>' % esc(S.T(en, "wd_top", n, "" if n == 1 else "s") if en else S.T(en, "wd_top", n))
            page = r[0].replace(S778_MARK, S778_MARK + add, 1)
            if 'id="s778box"' in add:                         # the old lines are in the box at the top: S543's link to them is not repeated
                page = re.sub(r'<div class="lnk"><a id="oldlink" [^>]*>[^<]*</a></div>', "", page, count=1)
            r = (page,) + tuple(r[1:])
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was
        _s778_log("order_list", e)
    finally:
        if g is not None:
            g.s778_con = None
    return r


def _card(en, e, sent=False):                                 # noqa: F811 -- S778: the old lines named, the wrong-dealer warnings
    h = _s778_card_before(en, e, sent)
    try:
        con = getattr(_s778_g(), "s778_con", None)
        if con is not None:
            x = _s778().card_extra(con, en, e)
            if x and '</div><div class="two">' in h:
                h = h.replace('</div><div class="two">', x + '</div><div class="two">', 1)
    except Exception as ex:                                   # noqa: BLE001
        _s778_log("card", ex)
    return h


def supplier_page(sn):                                        # noqa: F811 -- S778: S543's screen, each line with its age, Ab nahi milta, the warning
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    try:
        return _s778_supplier_page(u, con, kind, login, sn)
    except Exception as e:                                    # noqa: BLE001 -- the screen as it was before S778
        _s778_log("supplier_page", e)
        return _s778_supplier_page_before(sn)


def _s778_supplier_page(u, con, kind, login, sn):
    S = _s778()
    en = u["_en"]
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return shell(con, u, L(en, "order"), '<div class="err">%s</div>' % L(en, "frozen"), back=P + "/s454/order", login=login)
    e = OS.entry_of(con, sn)
    olds = OS.old_lines(con, sn)
    vendor = e["vendor"] if e else (olds[0]["supplier"] if olds else sn)
    h = ['<style>%s</style>' % S.CSS, S.ok_html(en, request.args), '<h1>%s</h1>' % esc(vendor)]
    edit = request.args.get("edit") == "1"
    if e:
        ages = S.old_of(con, e["sn"])
        h.append('<div class="mut">%s</div>' % L(en, "likhwaiye"))
        items = []
        for l in e["lines"]:
            age = next((ages[f] for f in S.forms(con, l["item"], e["sn"]) if f in ages), 0)
            tag = _s619_carry_tag(en, l) + S.tag_html(en, age)
            q = OS.qty_of(l, en, con=con)                     # S543: qty_words, the shop's one nomenclature
            if edit and l["src"] != "draft":
                b = esc(json.dumps(dict(src=l["src"], ref=l["ref"], item=l["item"])))
                ctl = ('<span class="qbox"><button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:-1}))">−</button><b>%d</b>'
                       '<button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:1}))">+</button></span>'
                       % (P, b, int(l["qty"]), P, b)) + _s619_remove_chips(en, b)           # S619: the one remove door asks a reason
                items.append('<div class="li" style="flex-wrap:wrap"><span class="i">%s%s</span>%s</div>' % (esc(l["item"]), tag, ctl))
            else:
                items.append('<div class="li" style="flex-wrap:wrap"><span class="i">%s%s</span><span class="q">%s</span>%s</div>'
                             % (esc(l["item"]), tag, esc(q), S.na_button(en, e, l)))
            items.append(S.line_wrong_html(con, en, e, l))
        h.append('<div class="list" id="lines">%s</div>' % "".join(items))
        if e["has_phone"]:
            if e.get("book_on"):                              # S574: the Calls number and the Order WhatsApp number, to read only
                nums = ('<div class="num" id="numcall">%s</div><div class="num" id="numwa">%s</div>'
                        % (esc(L(en, "num_call", e["phone"])), esc(L(en, "num_wa", e["wa"]))))
            else:
                nums = "".join('<div class="num">%s</div>' % esc(x) for x in e["shown"])
            h.append('<div><a class="big blue" id="callkaro" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">📞 %s</a>%s</div>'
                     % (esc(_tel(e["phone"])), P, esc(json.dumps(e["sn"])), L(en, "callkaro"), nums))
            h.append('<div class="mut" style="text-align:center">%s</div>' % L(en, "baat"))
        else:
            h.append('<div class="mut" id="nophone">%s</div>' % L(en, "nonum" if e.get("book_on") else "nophone_l"))   # S574
        if e["state"] == "in_line":
            h.append('<div class="mut">%s</div>' % L(en, "inline"))
        elif e["state"] == "withdrawn":
            h.append('<div class="mut am">%s</div>' % L(en, "wa_no"))
        h.append('<button class="big" id="ordered" onclick="s454(\'%s/api/s454/ordered\',{sn:%s},\'%s/s454/order\')">%s</button>'
                 % (P, esc(json.dumps(e["sn"])), P, L(en, "ordered")))
        if not e.get("draft"):
            h.append('<div class="lnk"><a id="qtylink" href="?edit=%d">%s</a></div>' % (0 if edit else 1, L(en, "qtychange")))
    if olds:
        h.append(_old_block(en, olds))
    return shell(con, u, L(en, "order"), "".join(h), back=P + "/s454/order", login=login)


def s778_abnahi_page():
    """The doctor's answers to 'Ab nahi milta' and the week's wrong-dealer catches (owner only, English)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    if kind != "owner":
        return redirect(P + "/s454/order")
    S = _s778()
    return shell(con, u, "No longer available", '<style>%s</style>%s%s' % (S.CSS, S.owner_ok_html(request.args), S.owner_page_body(con)),
                 back="/finance/approvals", login=login)


def _s778_door(name):
    def view():
        owner = name == "na_answer"
        u, con, kind, err = _auth_api(order=not owner)
        if err:
            return err
        if owner and kind != "owner":
            return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
        b = _body()
        S = _s778()
        try:
            if name == "again":
                body, code = S.again(con, who(u), str(b.get("kind") or ""), str(b.get("ref") or ""), str(b.get("to") or ""))
            elif name == "na":
                body, code = S.na(con, who(u), b)
            elif name == "na_answer":
                body, code = S.na_answer(con, who(u), int(b.get("id") or 0), str(b.get("answer") or ""))
            elif name == "dealer_ok":
                body, code = S.dealer_ok(con, who(u), str(b.get("sn") or ""), str(b.get("item") or ""))
            else:
                body, code = S.move(con, who(u), b)
        except (TypeError, ValueError) as e:
            return jsonify(ok=False, error="bad_request", message=str(e)[:120]), 400
        return jsonify(body), code
    view.__name__ = "api_s778_" + name
    return view


bp.add_url_rule(P + "/s454/abnahi", "s778_abnahi", s778_abnahi_page)
for _n778 in ("again", "na", "na_answer", "dealer_ok", "move"):
    bp.add_url_rule(P + "/api/s778/" + _n778, "api_s778_" + _n778, _s778_door(_n778), methods=["POST"])
# ---- S778 end ---------------------------------------------------------------------------------------------------------------------------
