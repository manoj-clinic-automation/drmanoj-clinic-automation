

# ---- S864_ONE_STATEMENT (18-Nov-2026, Sanjeevni session 479; the owner's 'go' 08:21): the finished month's pair on his steps -----------------------
#  After a month ends, the month needs the SAME pair he exports every visit (bill-wise + item-wise), once more, over the finished month -- FROM its
#  1st TO its last day -- and again only for a reason the system can name (month_asks.amir_pairs). Step 3 lists it ABOVE this month's pair with the
#  reason in Hindi; step 4 shows whether each report of it has reached the server today. Never a gate (his_line False): his day never waits on it.
#  Fail-soft: without month_asks, or on any error, the two steps draw as before.
_state_before_s864 = state


def state(cx, day, who="", step=None, owner=False):           # noqa: F811 -- S864
    S = _state_before_s864(cx, day, who, step, owner)
    S.s864 = []
    try:
        import month_asks                                      # noqa: PLC0415
        S.s864 = month_asks.amir_pairs(cx, day=day)
    except Exception as e:                                     # noqa: BLE001
        print("amir_day S864: the finished month's pair could not be read: %s" % str(e)[:200], file=sys.stderr)
    return S


def _s864_month_hi(month):
    try:
        y, m = int(month[:4]), int(month[5:7])
        return ("January February March April May June July August September October November December".split()[m - 1]) + " " + str(y)
    except (TypeError, ValueError, IndexError):
        return str(month or "")


def _s864_step3_card(S):
    q = getattr(S, "s864", None) or []
    if not q:
        return ""
    cards = []
    for p in q:
        rows = "".join("<div class=line><span class=big>%d. %s</span><br><span class=sub>%s se %s tak</span></div>"
                       % (i + 1, _esc(label), _esc(_ddmmyyyy(p["first"])), _esc(_ddmmyyyy(p["last"])))
                       for i, (_k, label) in enumerate(p["kinds"]))
        why = "".join("<li>%s</li>" % _esc(w) for w in (p.get("why_hi") or []))
        cards.append("<div class=card style='border-left:6px solid #b42318'><h2>Pehle pichhle mahine (%s) ki report</h2>%s"
                     "<div class=dates><div class=sub>Marg mein yeh do tareekh daaliye:</div>"
                     "<div class=line>FROM &nbsp; <span class=d>%s</span></div>"
                     "<div class=line>TO &nbsp;&nbsp;&nbsp;&nbsp; <span class=d>%s</span> <span class=sub>(mahine ka aakhri din)</span></div></div>"
                     "<div class=note><b>Kyon:</b><ul style='margin:4px 0 0;padding-left:20px'>%s</ul>"
                     "Yeh line report server par aate hi apne aap hat jaayegi.</div></div>"
                     % (_esc(_s864_month_hi(p["month"])), rows, _esc(_ddmmyyyy(p["first"])), _esc(_ddmmyyyy(p["last"])), why))
    return "".join(cards)


def _s864_step4_card(S):
    q = getattr(S, "s864", None) or []
    if not q:
        return ""
    out = []
    for p in q:
        lines = []
        for k, label in p["kinds"]:
            g = (p.get("got") or {}).get(k) or {}
            st = g.get("state") or "none"
            if st == "ok":
                lines.append("<div class=line><span class='big good'>%s &#10003;</span><br><span class=sub>%s se %s &middot; %s baje &middot; padh li gayi</span></div>"
                             % (_esc(label), _esc(_ddmmyyyy(p["first"])), _esc(_ddmmyyyy(p["last"])), _esc(g.get("at") or "")))
            elif st == "door":
                lines.append("<div class=line><span class='big warn'>%s &hellip;</span><br><span class=sub>Server par %s baje aa gayi &mdash; padhi ja rahi hai. Dobara nahi nikaalni.</span></div>"
                             % (_esc(label), _esc(g.get("at") or "")))
            else:
                lines.append("<div class=line><span class=big>%s</span><br><span class=sub>Abhi nikaali nahi gayi &mdash; %s se %s tak.</span></div>"
                             % (_esc(label), _esc(_ddmmyyyy(p["first"])), _esc(_ddmmyyyy(p["last"]))))
        out.append("<div class=card style='border-left:6px solid #b42318'><h2>Pichhle mahine (%s) ki %s</h2>%s"
                   "<p class=sub>Yeh aapka din nahi rokti; report aate hi yeh card hat jaata hai.</p></div>"
                   % (_esc(_s864_month_hi(p["month"])), "do report" if len(p["kinds"]) > 1 else "report", "".join(lines)))
    return "".join(out)


_step3_before_s864 = _step3
_step4_before_s864 = _step4
_S864_A3 = "<div class=card><h2>Do report nikaaliye</h2>"
_S864_A4 = "<div class=card><h2>Do report</h2>"


def _step3(S):                                                # noqa: F811 -- S864
    html_ = _step3_before_s864(S)
    try:
        card = _s864_step3_card(S)
        if card and html_.count(_S864_A3) == 1:
            html_ = html_.replace(_S864_A3, card + "<div class=card><h2>Is mahine ki do report nikaaliye</h2>", 1)
    except Exception as e:                                     # noqa: BLE001
        print("amir_day S864 step 3: %s" % str(e)[:200], file=sys.stderr)
    return html_


def _step4(S):                                                # noqa: F811 -- S864
    html_ = _step4_before_s864(S)
    try:
        card = _s864_step4_card(S)
        if card and html_.count(_S864_A4) == 1:
            html_ = html_.replace(_S864_A4, card + "<div class=card><h2>Is mahine ki do report</h2>", 1)
    except Exception as e:                                     # noqa: BLE001
        print("amir_day S864 step 4: %s" % str(e)[:200], file=sys.stderr)
    return html_
# ---- S864 end ---------------------------------------------------------------------------------------------------------------------------
