


# ==========================================================================================================================================
# S939_ORDER_FINAL (23-Nov-2026, Sanjeevni session 509; D1053, the owner's "Mockup okay" 18:52 IST) -- order_d1053.py beside this file
#  holds the logic. With setting order.d1053 = 1 and the order made from Marg's sheet:
#   * the old lines are Darpan's (his tab): reception's red box gives way to one line and the waiting / final banner; the lines that
#     came leave by themselves (F-1623, order_s778.red_lines wrapped);
#   * reception only raises: a card line's Out of stock and the remove chips become "Dealer ke paas nahi → Darpan ko"
#     (POST /finance/porders/api/d1053/raise); her strip's Dobara / Out of stock become the same raise; the doctor keeps his buttons;
#   * WhatsApp all, its confirm screen and its door are LOCKED until Darpan's सूची पक्की करो; Call and Order done stay open;
#   * the day's "Ho chuke" becomes the SENT record -- each dealer with its WhatsApp / call time and the day its goods are due, until
#     they come.
#  Any other value of order.d1053, or any fault here: every screen and door exactly as before this kit.
# ==========================================================================================================================================
def _d53():
    import order_d1053                                        # noqa: PLC0415 -- beside this file
    return order_d1053


def _d53_log(where, e):
    print("S939 %s failed: %r" % (where, e), file=sys.stderr)


def _d53_con():
    try:
        return getattr(_s778_g(), "d1053_con", None)
    except Exception:                                         # noqa: BLE001
        return None


try:
    import order_s778 as _d53_S7                              # noqa: E402
    _d53_red_lines_before = _d53_S7.red_lines

    def _d53_red_lines(con, en=False, cards=None):
        g, key = None, "d1053_red_%d" % (1 if en else 0)
        try:
            g = _s778_g()
            hit = getattr(g, key, None)
            if hit is not None:
                return hit                                    # one reading per request, as order_s778's own (cleared after a write)
        except Exception:                                     # noqa: BLE001 -- outside a request
            g = None
        out = _d53_red_lines_before(con, en, cards)
        try:
            out = _d53().red_lines_filter(con, out)
        except Exception as e:                                # noqa: BLE001 -- the lines as order_s778 made them
            _d53_log("red_lines", e)
            return out
        if g is not None:
            try:
                setattr(g, key, out)
            except Exception:                                 # noqa: BLE001
                pass
        return out
    _d53_S7.red_lines = _d53_red_lines

    _d53_red_box_before = _d53_S7.red_box

    def _d53_red_box(con, en, cards=None):
        try:
            D = _d53()
            if D.live(con):
                q = D.questions(con, cards)
                n = len(q["old"])
                line = ""
                if n:
                    line = ('<div class="mut" id="d1053old">%s</div>' % esc(("%d old medicine%s wait for Darpan's decision on his tab" % (n, "" if n == 1 else "s"))
                                                                         if en else ("%d purani dawa — Darpan apne page par faisla karenge" % n)))
                return '<div id="s778box" data-d1053="1">%s%s</div>' % (D.banner_html(con, en), line)
        except Exception as e:                                # noqa: BLE001 -- the box as before
            _d53_log("red_box", e)
        return _d53_red_box_before(con, en, cards)
    _d53_S7.red_box = _d53_red_box

    _d53_na_button_before = _d53_S7.na_button

    def _d53_na_button(en, e, l):
        try:
            con = _d53_con()
            if con is not None and _d53().live(con):
                note = _d53().raised_on_card(con, e["sn"]).get((l.get("src"), str(l.get("ref")), l.get("item")))
                if note:
                    return _d53().raised_note(note, "", en)
                if not en:
                    return _d53().raise_button(e, l)
        except Exception as ex:                               # noqa: BLE001
            _d53_log("na_button", ex)
        return _d53_na_button_before(en, e, l)
    _d53_S7.na_button = _d53_na_button

    _d53_card_extra_before = _d53_S7.card_extra

    def _d53_card_extra(con, en, e):
        h = _d53_card_extra_before(con, en, e)
        try:
            D = _d53()
            if D.live(con):
                for (src, ref, item), ba in D.raised_on_card(con, e["sn"]).items():
                    h += D.raised_note(ba, item, en)
        except Exception as ex:                               # noqa: BLE001
            _d53_log("card_extra", ex)
        return h
    _d53_S7.card_extra = _d53_card_extra
except Exception as _e939:                                    # noqa: BLE001
    _d53_log("order_s778 wraps", _e939)

_d53_whatsapp_all_before = OS.whatsapp_all


def _d53_whatsapp_all(con, who_, expect=None):
    try:
        if _d53().locked(con):
            return dict(ok=False, error="not_final", message="Darpan ne list abhi pakki nahi ki — tab tak WhatsApp band hai. Call se order kar sakte hain."), 409
    except Exception as e:                                    # noqa: BLE001 -- the door as before
        _d53_log("whatsapp lock", e)
    return _d53_whatsapp_all_before(con, who_, expect=expect)


OS.whatsapp_all = _d53_whatsapp_all

_d53_wa_confirm_before = wa_confirm_page


def wa_confirm_page():                                         # noqa: F811 -- S939: locked until Darpan's final
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    try:
        D = _d53()
        if D.locked(con):
            en = u["_en"]
            back = P + "/s454/order"
            return shell(con, u, L(en, "wa_q"), '%s<a class="more" id="waback" href="%s">%s</a>' % (D.banner_html(con, en), back, L(en, "wa_back")),
                         back=back, login=login)
    except Exception as e:                                    # noqa: BLE001
        _d53_log("wa_confirm", e)
    return _d53_wa_confirm_before()


_d53_order_list_before = order_list
_D53_DONE_END = ('<div class="lnk"><a id="oldlink"', '<div class="ok"><div class="t">')


def _d53_body_end(page):
    """Where shell()'s body ends: the last </div> before </body> (a shared login's who-script may sit between them)."""
    e = page.find("</body>")
    return page.rfind("</div>", 0, e) if e >= 0 else -1


def order_list():                                             # noqa: F811 -- S939: the lock on WhatsApp all, the sent record
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    g = None
    try:
        g = _s778_g()
        g.d1053_con = con
    except Exception as e:                                    # noqa: BLE001
        _d53_log("order_list g", e)
    r = _d53_order_list_before()
    try:
        D = _d53()
        if isinstance(r, tuple) and r[1] == 200 and D.live(con):
            en = u["_en"]
            page = r[0]
            if D.locked(con):
                page = re.sub(r'<a class="big" id="waall" href="[^"]*">([^<]*)</a>',
                              lambda m: '<button class="big" id="waall" disabled>%s</button>' % (m.group(1) + (" (locked)" if en else " (band)")), page, count=1)
            a = page.find('<div class="mut" id="donehead">')
            sent = D.sent_html(con, en)
            be = _d53_body_end(page)
            if a >= 0:
                ends = [page.find(x, a) for x in _D53_DONE_END] + [be]
                b = min([x for x in ends if x > a] or [-1])
                if b > a:
                    page = page[:a] + sent + page[b:]
            elif sent:
                ends = [page.find(x) for x in _D53_DONE_END] + [be]
                b = min([x for x in ends if x >= 0] or [-1])
                if b >= 0:
                    page = page[:b] + sent + page[b:]
            r = (page,) + tuple(r[1:])
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was
        _d53_log("order_list", e)
    finally:
        if g is not None:
            g.d1053_con = None
    return r


_d53_supplier_page_before = supplier_page


def supplier_page(sn):                                        # noqa: F811 -- S939: the line's button is the raise
    g = None
    try:
        po = _po()
        u, con, kind, err = po._auth()
        if not err:
            g = _s778_g()
            g.d1053_con = con
    except Exception as e:                                    # noqa: BLE001
        _d53_log("supplier g", e)
    try:
        return _d53_supplier_page_before(sn)
    finally:
        if g is not None:
            g.d1053_con = None


_d53_remove_chips_before = _s619_remove_chips


def _s619_remove_chips(en, b):                                # noqa: F811 -- S939: reception raises to Darpan instead of removing
    try:
        con = _d53_con()
        if con is not None and not en and _d53().live(con):
            return ""
    except Exception as e:                                    # noqa: BLE001
        _d53_log("remove chips", e)
    return _d53_remove_chips_before(en, b)


_D53_DECIDE = (P + "/api/s778/na", P + "/api/s778/again", P + "/api/s454/reorder")


@bp.before_request
def _d53_gate():
    """Every request of this screen: the request knows its connection and who asks (the line buttons read it). With the flow on, the
    decisions on a line are the doctor's and Darpan's: a staff POST to Out of stock, Dobara / again, or the remove is refused -- she
    raises to Darpan."""
    try:
        po = _po()
        u, con, kind, err = po._auth()
        if err:
            return None
        g = _s778_g()
        g.d1053_con, g.d1053_kind = con, kind
        if request.method != "POST" or kind == "owner":
            return None
        path = request.path
        if path == P + "/api/s454/qty":
            if not (request.get_json(silent=True) or {}).get("remove"):
                return None
        elif path not in _D53_DECIDE:
            return None
        if _d53().live(con):
            return jsonify(ok=False, error="raise_only", message="Iska faisla Darpan karenge — 'Dealer ke paas nahi → Darpan ko' dabaiye."), 409
    except Exception as e:                                    # noqa: BLE001 -- the door as before
        _d53_log("gate", e)
    return None


_d53_old_block_before = _old_block


def _old_block(en, olds, title=True):                         # noqa: F811 -- S939: no Dobara button for staff (Darpan decides)
    h = _d53_old_block_before(en, olds, title)
    try:
        con = _d53_con()
        if con is not None and not en and _d53().live(con):
            h = re.sub(r'<button class="sm" onclick="s454\(\'[^\']*/api/s454/reorder\',\{line:\d+\}\)">[^<]*</button>', "", h)
    except Exception as e:                                    # noqa: BLE001
        _d53_log("old block", e)
    return h


@bp.route(P + "/api/d1053/raise", methods=["POST"])
def api_d1053_raise():
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    try:
        D = _d53()
        if not D.live(con):
            return jsonify(ok=False, error="off", message="Yeh button abhi band hai."), 409
        body, code = D.raise_line(con, who(u), _body())
    except Exception as e:                                    # noqa: BLE001
        _d53_log("raise door", e)
        return jsonify(ok=False, error="unavailable"), 503
    return jsonify(**body), code


try:                                                          # reception's strip (order_flow): Dobara / Out of stock become the raise
    import order_flow as _d53_OF                              # noqa: E402
    _d53_rline_before = _d53_OF._rline_btns
    _d53_rrow_before = _d53_OF._rrow_acts
    _d53_rec_act_before = _d53_OF.rec_act

    def _d53_flow_live():
        """Once per request (cached on g): is the flow live? Outside a request: no (the strip as before)."""
        try:
            from flask import g, has_app_context              # noqa: PLC0415
            if not has_app_context():
                return False
            v = getattr(g, "d1053_flowlive", None)
            if v is None:
                v = bool(_d53().live(_po()._db()))
                g.d1053_flowlive = v
            return v
        except Exception:                                     # noqa: BLE001
            return False

    def _d53_rline(r, l):
        if l.get("state") in ("short", "part") and r.get("id") and l.get("id") and not r.get("orderless") and _d53_flow_live():
            return (_d53_OF._rbtn("Substitute aaya", dict(oid=r["id"], lid=l["id"], do="sub")) +
                    '<span class="small">Baaki dawa ka faisla Darpan karenge</span>')
        return _d53_rline_before(r, l)

    def _d53_rrow(r):
        if r.get("group") == "late" and r.get("id") and not r.get("orderless") and _d53_flow_live():
            return (_d53_OF._rbtn("Call kiya — aa raha hai", dict(do="called", oid=r["id"]), "p") +
                    _d53_OF._rbtn("Dealer ke paas nahi → Darpan ko", dict(do="raise", oid=r["id"])) +
                    _d53_OF._rbtn("Nahi bhejenge", dict(do="refused", oid=r["id"]), "w"))
        return _d53_rrow_before(r)

    def _d53_rec_act(con, who_, b):
        try:
            D = _d53()
            if isinstance(b, dict) and D.live(con):
                do = str(b.get("do") or "")
                if do == "raise":
                    return D.raise_line(con, who_, dict(oid=b.get("oid")))
                if do in ("again", "oos", "oosrow"):
                    return dict(ok=False, error="raise_only", message="Iska faisla Darpan karenge — 'Dealer ke paas nahi → Darpan ko' dabaiye."), 409
        except Exception as e:                                # noqa: BLE001
            _d53_log("rec_act", e)
        return _d53_rec_act_before(con, who_, b)

    _d53_OF._rline_btns = _d53_rline
    _d53_OF._rrow_acts = _d53_rrow
    _d53_OF.rec_act = _d53_rec_act
except Exception as _e939b:                                   # noqa: BLE001
    _d53_log("order_flow wraps", _e939b)
# ---- S939 end ---------------------------------------------------------------------------------------------------------------------------
