# ---- S482_BILL_CHAIN (05-Oct-2026, D675 b): the gap lines of Marg's bill-number chain -- read and worded here, never computed here -----
# The chain lives in mi_bill_chain (marg_take.rebuild_chain, rewritten whenever a sale report or an EMPTY day lands). This page only
# READS it (marg_take.chain_state) and words ONE line per open gap -- Hindi for the counter, English for the owner. The line leaves by
# itself when a re-export closes the gap. No calendar word anywhere: the numbers decide.
_S482_INGEST = os.environ.get("MARG_INGEST_DIR", "/root/marg_ingest")
_S482_MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_S482_N_HI = {3: "teen", 4: "chaar", 5: "paanch", 6: "chhah", 7: "saat"}
_S482_N_EN = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def _s482_day(d):
    """'2026-09-08' -> '08-Sep'."""
    try:
        return "%s-%s" % (d[8:10], _S482_MON[int(d[5:7]) - 1])
    except (ValueError, IndexError, TypeError):
        return str(d)


def _s482_join(parts, word):
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " %s " % word + parts[-1]


def _s482_lines(state):
    """[{between, via_empty, n, text_hi, text_en}] -- one per open gap; the series that miss numbers between the same days share a line."""
    groups = {}
    for g in (state or {}).get("gaps") or []:
        k = (tuple(g["between"]), tuple(g.get("via_empty") or ()))
        groups.setdefault(k, []).append(g)
    out = []
    for (between, via), gs in sorted(groups.items(), key=lambda kv: (kv[0][0][1], kv[0][0][0])):
        gs = sorted(gs, key=lambda g: g["series"])
        words = [w for g in gs for w in g["missing"]]
        n = sum(int(g["n"]) for g in gs)
        hi = _s482_join([w.replace("..", " se ") + (" tak" if ".." in w else "") for w in words], "aur")
        en = _s482_join([w.replace("..", " to ") for w in words], "and")
        a, b = _s482_day(between[0]), _s482_day(between[1])
        verb = "nahi mila" if n == 1 else "nahi mile"
        if between[0] == between[1]:
            t_hi = "Bill %s %s (%s ke andar) — %s ki bikri report dobara banaiye." % (hi, verb, a, a)
            t_en = "Bill chain: %s missing inside %s — re-export that day." % (en, a)
        elif via:
            k = 2 + len(via)
            ev = _s482_join([_s482_day(x) for x in via], "aur")
            t_hi = ("Bill %s %s (%s se %s ke beech, %s %s) — %s dinon ki bikri report dobara banaiye."
                    % (hi, verb, a, b, ev, "khali tha" if len(via) == 1 else "khali the", _S482_N_HI.get(k, str(k))))
            t_en = ("Bill chain: %s missing between %s and %s (%s %s empty) — re-export all %s days."
                    % (en, a, b, _s482_join([_s482_day(x) for x in via], "and"), "was" if len(via) == 1 else "were", _S482_N_EN.get(k, str(k))))
        else:
            t_hi = "Bill %s %s (%s se %s ke beech) — %s aur %s ki bikri report dobara banaiye." % (hi, verb, a, b, a, b)
            t_en = "Bill chain: %s missing between %s and %s — re-export both days." % (en, a, b)
        out.append({"between": list(between), "via_empty": list(via), "n": n, "text_hi": t_hi, "text_en": t_en})
    return out


def _s482_chain(cx):
    """The chain's state with its lines, or None when the door's module cannot be read (the page never fails for this)."""
    try:
        if _S482_INGEST not in sys.path:
            sys.path.append(_S482_INGEST)
        import marg_take                                       # noqa: PLC0415
        st = marg_take.chain_state(cx)
        st["lines"] = _s482_lines(st)
        return st
    except Exception:                                          # noqa: BLE001
        return None
# ---- S482 end --------------------------------------------------------------------------------------------------------------------------


