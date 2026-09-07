# ---- S228 THREE-WAY: the shelf, Marg, and our own system ----------------------
# The owner, 06-Sep-2026: "today's stock check having three columns, one for the
# physical, second for the Marg, and third for our own system. Then we compare our
# system with the Marg export -- we should match -- and then only we should
# populate the screens."
#
# The count has always carried two figures: what was counted, and what
# stock_snapshot says. This adds the third and, more importantly, says WHICH the
# second one actually is.
#
# THE FAULT THIS EXPOSES, and it is the reason the owner asked. stock_snapshot is
# keyed (as_on, item) and LAST WRITE WINS. Two different pushes land on it: the
# Marg closing-stock export (push_snapshot) and our own computed figure
# (push_expected). Whichever arrived later for a given day IS the count's "Marg"
# column -- and until now nothing on any screen said which one that was. A count
# could be measured against our own arithmetic while every page called it Marg.
# stock_feed keeps both, append-only, which is what makes the comparison possible
# at all; this reads it and prints the answer in one line.
#
# Nothing here computes a stock figure. It reads the two feeds already on the
# server and subtracts them. Where our system has not computed a day, the column
# says so rather than showing a number nobody can stand behind.
THREE_WAY_TOP = 6          # how many differing lines the headline names


def _snapshot_source(con, as_on):
    """Which push last wrote the figures this count was measured against.
    ('marg' | 'expected' | 'other' | None, the raw source strings)."""
    raws = [str(r[0] or "") for r in con.execute(
        "SELECT DISTINCT source FROM stock_snapshot WHERE as_on=?", (as_on,)) if (r[0] or "").strip()]
    kinds = {_feed_kind(s) for s in raws}
    if kinds == {"marg"}:
        return "marg", raws
    if kinds == {"expected"}:
        return "expected", raws
    if not kinds:
        return None, raws
    if "marg" in kinds:
        return "mixed", raws           # more than one sender for one day
    return "other", raws


def _three_way(con, as_on, pack_of=None):
    """{item: ours} for this as_on, plus the provenance and the verdict.

    ours  -- the newest push_expected figure for that day, or None when our
             system did not compute it. None is never rendered as a number.
    """
    _feed_ensure(con)
    feeds = _feed_latest(con)
    ours = (feeds.get((str(as_on), "expected")) or {}).get("items") or {}
    marg = (feeds.get((str(as_on), "marg")) or {}).get("items") or {}
    ours_at = (feeds.get((str(as_on), "expected")) or {}).get("received_at")
    marg_at = (feeds.get((str(as_on), "marg")) or {}).get("received_at")
    src, raws = _snapshot_source(con, as_on)
    gaps = []
    both = 0
    for item, q in ours.items():
        if item not in marg:
            continue
        both += 1
        d = int(q) - int(marg[item])
        if d:
            pk = (pack_of or {}).get(item) or 1
            gaps.append(dict(item=item, ours=int(q), marg=int(marg[item]), gap=d,
                             pack=int(pk), gap_text=_qw(abs(d), int(pk))))
    gaps.sort(key=lambda g: (-abs(g["gap"] * 1.0 / max(1, g["pack"])), g["item"]))
    only_ours = sorted(set(ours) - set(marg))
    only_marg = sorted(set(marg) - set(ours))
    have = bool(ours)
    if not have:
        line = ("Our own system has not computed a figure for %s, so there is nothing "
                "to compare against Marg for this count." % _r_dmy(_dmy_to_iso(as_on) or as_on))
    elif not marg:
        line = ("Marg's own export for %s is not on the server -- only our computed "
                "figure is -- so the two cannot be compared." % _r_dmy(_dmy_to_iso(as_on) or as_on))
    elif not gaps:
        line = ("Our system and Marg's export AGREE on all %d items both of them carry."
                % both)
    else:
        top = ", ".join("%s %s" % (g["item"], g["gap_text"]) for g in gaps[:3])
        line = ("Our system and Marg's export differ on %d of the %d items both of them "
                "carry \u2014 largest: %s." % (len(gaps), both, top))
    # the provenance line: what the count's own figures actually are
    if src == "marg":
        prov = "Marg's own closing-stock export."
    elif src == "expected":
        prov = ("OUR OWN COMPUTED FIGURE, not Marg's export \u2014 our push landed last "
                "on this day, so it is what the count was measured against.")
    elif src == "mixed":
        prov = ("more than one sender wrote this day (%s) -- the newest per item wins, "
                "so this count's figures are not from one source." % ", ".join(sorted(raws)))
    elif src == "other":
        prov = "a sender the server does not recognise (%s)." % ", ".join(sorted(raws))
    else:
        prov = "not recorded."
    # THE BANNER. The comparison above is between the two FEEDS and stays true
    # whatever wrote stock_snapshot -- but the count's own column is a different
    # question, and a card that reports "ours vs Marg" above a count measured
    # against ourselves reads as the opposite of the truth. So the state says so
    # in its own line, at the top of the card, and the card is never green.
    bang = ""
    if src == "expected":
        bang = ("This count's own figures came from OUR SYSTEM, not from Marg's export. "
                "What follows compares the two feeds, not the count against Marg.")
    elif src == "mixed":
        bang = ("This count's own figures were written by more than one sender, so they "
                "are not all Marg's. What follows compares the two feeds.")
    elif src in ("other", None):
        bang = ("It is not recorded which sender wrote this count's figures, so they "
                "cannot be called Marg's.")
    return dict(as_on=as_on, ours=ours, marg=marg, have_ours=have, have_marg=bool(marg),
                bang=bang,
                compared=both, differ=len(gaps), agree=both - len(gaps),
                gaps=gaps[:THREE_WAY_TOP], all_gaps=len(gaps),
                only_ours=only_ours[:THREE_WAY_TOP], only_ours_n=len(only_ours),
                only_marg=only_marg[:THREE_WAY_TOP], only_marg_n=len(only_marg),
                ours_at=ours_at, ours_at_text=(_r_stamp(ours_at) if ours_at else ""),
                marg_at=marg_at, marg_at_text=(_r_stamp(marg_at) if marg_at else ""),
                snapshot_source=src, snapshot_sources=sorted(raws),
                measured_against=prov, line=line,
                trustworthy=bool(have and marg and not gaps and src == "marg"))
# ---- end S228 THREE-WAY -------------------------------------------------------
