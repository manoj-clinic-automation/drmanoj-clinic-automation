

# ==========================================================================================================================================
# S470_ORDER_ON_SPINE (04-Oct-2026, D672 / D673): the owner's card on the old page -- ONE LINE A WEEK from the nightly trial
# (spine/orders/order_score_latest.json, written by spine/order_rehearsal.py), the medicines with no supplier on record (order_rules.plan's
# no_supplier), a family member in the plan said as such, and the six engine settings on the settings card. English; the owner only (the
# old page's owner cards). Nothing here is on a staff screen.
# ==========================================================================================================================================
S470_LIMITS = {"order.pace_days": (7, 90), "order.dead_after_days": (1, 365), "order.on_order_days": (1, 30), "order.in_transit_days": (1, 60),
               "order.lot_history_days": (30, 730)}


def _s470_or():
    import order_rules                                        # noqa: PLC0415 -- beside this file
    return order_rules


def _s470_keys():
    return tuple(getattr(_s470_or(), "S470_KEYS", ()))


def _s470_valid(key, v):
    v = str(v or "").strip()
    if key == "order.engine_source":
        return v in ("spine", "tables"), v
    lim = S470_LIMITS.get(key)
    if not lim:
        return False, v
    try:
        n = int(v)
    except ValueError:
        return False, v
    return lim[0] <= n <= lim[1], str(n)


def _s470_set(con, u, key, value):
    """One of S470's six settings, from the same card and the same route as the others: validated, audited (s454_setting), the owner only."""
    ok, v = _s470_valid(key, value)
    if not ok:
        lim = S470_LIMITS.get(key)
        return jsonify(ok=False, error="bad_value", message="%s: not a valid value (%s)" % (key, ("%d to %d" % lim) if lim else "spine or tables")), 400
    old = _s470_or()._setting(con, key)
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, v, "S410 D626 -- " + _s470_or().SETTINGS[key][1]))
    OS.audit(con, who(u), "s454_setting", key, dict(before=old, after=v, kit="S470"))
    con.commit()
    return jsonify(ok=True, key=key, value=v, before=old)


def _s470_setting_rows(con):
    rows = []
    for k in _s470_keys():
        v = _s470_or()._setting(con, k)
        rows.append('<tr><td><code>%s</code><div style="color:#666;font-size:12.5px">%s</div></td><td><input id="s454k_%s" value="%s" style="width:120px;min-height:36px">'
                    ' <button onclick="s454set(\'%s\',document.getElementById(\'s454k_%s\').value)" style="min-height:36px">Save</button></td></tr>'
                    % (esc(k), esc(_s470_or().SETTINGS[k][1]), esc(k.replace(".", "_")), esc(v), esc(k), esc(k.replace(".", "_"))))
    return rows


def _s470_score_file():
    return os.environ.get("ORDER_SCORE_FILE") or os.path.join(os.path.dirname(os.path.abspath(_s470_or().__file__)), "spine", "orders", "order_score_latest.json")


def _s470_score_line():
    """The owner's one line a week, or 'not ready yet' when the file is missing, older than two days, or has no scored day."""
    not_ready = "The weekly score is not ready yet."
    try:
        with open(_s470_score_file(), encoding="utf-8") as fh:
            j = json.load(fh)
        day = dt.date.fromisoformat(str(j.get("date") or "")[:10])
    except (OSError, ValueError, TypeError):
        return not_ready
    if (dt.date.today() - day).days > 2 or not int(j.get("days_scored_7") or 0):
        if j.get("first_score_on") and (dt.date.today() - day).days <= 2:
            return not_ready + " The first week is scored on the night of %s." % OS.dmy(j["first_score_on"])
        return not_ready
    pct = lambda x, late: ("%d%%" % int(round(float(x)))) if x is not None else late       # noqa: E731
    m, k = int(j.get("stockouts") or 0), int(j.get("stockouts_listed_in_time") or 0)
    return ("Last week: of what was bought, %s was on the list beforehand · of what was listed, %s was bought within 14 days · "
            "%d medicine%s ran out, %d of them listed in time."
            % (pct(j.get("bought_on_list_pct"), "nothing yet"), pct(j.get("listed_bought_pct"), "not known yet (14 days are needed)"),
               m, "" if m == 1 else "s", k))


def _s470_card(con, st):
    h = ['<div %s id="s470"><div id="s470score">%s</div>' % (st, esc(_s470_score_line()))]
    try:
        p = _s470_or().plan(con)
        ns = p.get("no_supplier") or []
        if ns:
            h.append('<div id="s470nosup">%d medicine%s no supplier on record<details><summary>the list</summary>%s<div style="color:#666;font-size:13px">'
                     'Sold, and never bought on any purchase bill Marg has given: the system\'s list orders them from nobody.</div></details></div>'
                     % (len(ns), " has" if len(ns) == 1 else "s have", esc(", ".join(x["item"] for x in ns))))
        fam = [(l["item"], l["family"]) for v in (p.get("vendors") or {}).values() for l in v["lines"] if int(l.get("family") or 0) > 1]
        if fam:
            h.append('<div id="s470family">On the system\'s list: %s</div>' % esc("; ".join("%s (1 of %d under this name)" % (i, n) for i, n in sorted(fam))))
        nc = p.get("no_closing") or []
        if nc:
            h.append('<div id="s470noclose" style="color:#8c1d18">%d item%s of Marg\'s stock list %s not in the spine\'s latest closing and %s left out of the system\'s list: %s</div>'
                     % (len(nc), "" if len(nc) == 1 else "s", "is" if len(nc) == 1 else "are", "is" if len(nc) == 1 else "are", esc(", ".join(nc[:12]))))
        eng = str(p.get("engine") or "")
        if eng and eng != "spine":
            h.append('<div id="s470engine" style="color:#8c1d18">The system\'s list is made from %s.</div>'
                     % esc("the old tables (order.engine_source = tables)" if eng == "tables" else eng))
    except Exception:                                         # noqa: BLE001 -- the card never breaks the page
        pass
    h.append("</div>")
    return "".join(h)
# ---- S470 end ---------------------------------------------------------------------------------------------------------------------------
