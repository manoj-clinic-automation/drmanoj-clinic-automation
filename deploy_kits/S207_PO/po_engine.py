#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""po_engine.py — the purchase order generator.

Implements the cadence approved at S206 (`S206_CONSUMPTION_AND_ORDERING_CADENCE`)
and adds the quantity safety rails the owner asked for:

    "be careful of order quantities ... we can hold limited inventory in our
     small pharmacy"

    python3 po_engine.py [--archive DIR] [--cap 60000] [--json OUT]
    python3 po_engine.py --selftest

THE APPROVED MODEL, NOT A NEW ONE
    tier by monthly spend: weekly >= Rs 20,000 · fortnightly >= Rs 4,000 ·
    monthly below. CEILING NEVER FLOOR -- a vendor already ordered from less
    often than its tier keeps its own rhythm, so nobody's ordering gets MORE
    frequent. Cover = cadence + lead + safety. Quantities round UP to whole
    strips, because that is how they are ordered and how they arrive.

WHY THE RAILS EXIST — every one of them is a way to buy dead stock
    An order quantity is (rate x days) - on hand. Both terms can lie.

    1. A RATE FROM TOO FEW DAYS. An item sold on 3 days out of 133 has no
       meaningful daily rate. Twelve days of "cover" on that basis is how a
       shelf fills with things nobody asked for. Confidence comes from the
       number of distinct SELLING DAYS, and a thin rate never places an order
       by itself -- it asks.
    2. A SHORT SELLING WINDOW. An item first sold three weeks ago has its rate
       divided by 133 trading days and looks slow; one discontinued in May looks
       busy. Both are measured and flagged rather than averaged away.
    3. NO CEILING. A spike -- one bulk sale to one customer -- can ask for a
       year of stock. MAX_COVER_DAYS caps every line no matter what the tier
       says.
    4. NO BUDGET. The cadence is right and the total is still a decision. A
       run cap, and a per-vendor cap, so a plan is a proposal and not a
       surprise.
    5. SINGLE SOURCE. 129 items have exactly one vendor on record. Running one
       of those out is a different problem from running out of something three
       vendors carry, and it earns a longer buffer, not a shorter one.

NOTHING HERE SENDS ANYTHING. It writes a plan. A person sends orders.
"""
import argparse, collections, glob, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for rel in ("../S206_SANJEEVNI_MARG_PURCHASE", "../S206_SANJEEVNI_RECONCILE"):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, rel)))

DEF_ARCHIVE = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")

# --- the approved cadence (S206 §3) ---------------------------------------
TIER_WEEKLY_P     = 2000000      # >= Rs 20,000 a month
TIER_FORTNIGHT_P  =  400000      # >= Rs  4,000 a month
CADENCE_DAYS      = {"weekly": 7, "fortnightly": 14, "monthly": 30}
LEAD_DAYS         = 2            # PLACEHOLDER until the vendor sheet returns
SAFETY_DAYS       = 3
SINGLE_SOURCE_EXTRA_DAYS = 3     # no second vendor to fall back on

# --- the rails ------------------------------------------------------------
MAX_COVER_DAYS    = 45           # backstop. NOTE: with the approved tiers the
                                 # longest cover is monthly 30 + 2 + 3 + 3 = 38,
                                 # so this NEVER BINDS today. It is kept as a
                                 # guard for a future tier change and the
                                 # selftest asserts that it does not bind --
                                 # a rail that silently cannot fire is worse
                                 # than no rail, because it is believed.
PEAK_SHARE_SPIKE  = 0.40         # one day carrying 40%+ of a year's units
THIN_SELL_DAYS    = 5            # under this many selling days: ask, never assume
LOW_CONF_DAYS     = 20           # under this: confidence 'medium'
DEAD_AFTER_DAYS   = 60           # nothing sold this long is not reordered
MIN_LINE_P        =   5000       # Rs 50 -- below this, only if at/near zero
DEFAULT_BOX       =     10       # strips, when the shop's own buying shows no box
BOX_STRETCH_ASK   =    2.0       # a box this many times the real need is a decision
CONFIRM_LINE_P    = 500000       # Rs 5,000 on one line: a person decides
TRADING_DAYS      = 133          # 1-Apr .. 26-Aug-2026, the measured window


def ceil_div(a, b):
    return -(-a // b) if b else 0


def as_on_key(s):
    """Marg writes dd-mm-yyyy; comparing it as text puts 31-03 after 27-08."""
    t = (s or "").strip().replace("/", "-").split("-")
    if len(t) == 3:
        try:
            d, m, y = (int(x) for x in t)
            if y > 1900 and 1 <= m <= 12:
                return (y, m, d)
        except ValueError:
            pass
    return (0, 0, 0)


def cadence_for(monthly_p, observed_per_month):
    """Tier by spend, then apply the CEILING: never more often than the vendor
    is already used. Without this rule five vendors who already order less often
    than their tier would be given MORE bills, not fewer -- the opposite of the
    point."""
    if monthly_p >= TIER_WEEKLY_P:
        want = "weekly"
    elif monthly_p >= TIER_FORTNIGHT_P:
        want = "fortnightly"
    else:
        want = "monthly"
    if observed_per_month and observed_per_month > 0:
        observed_days = 30.0 / observed_per_month
        for name in ("weekly", "fortnightly", "monthly"):
            if CADENCE_DAYS[name] >= observed_days - 0.01:
                break
        # keep whichever is LESS frequent
        if CADENCE_DAYS[name] > CADENCE_DAYS[want]:
            return name, want
    return want, want


def confidence(sell_days):
    if sell_days >= LOW_CONF_DAYS:
        return "high"
    if sell_days >= THIN_SELL_DAYS:
        return "medium"
    return "thin"


def plan_line(it, cad_days):
    """One item's order quantity, and every reason behind it.

    Returns a dict; `order_strips` of 0 means nothing is needed. `confirm` means
    a number was produced but a person must agree to it."""
    cover = cad_days + LEAD_DAYS + SAFETY_DAYS
    if it["single_source"]:
        cover += SINGLE_SOURCE_EXTRA_DAYS
    capped = min(cover, MAX_COVER_DAYS)
    rate = it["rate_per_day"]
    target = rate * capped
    need = target - it["on_hand"]
    size = max(1, int(it["pack_size"] or 1))
    strips = 0 if need <= 0 else ceil_div(int(math.ceil(need)), size)
    reasons, confirm = [], False

    # ROUND UP TO A BOX. Stockists do not send 47 strips; they send boxes, and
    # asking for 47 gets 50 anyway with nobody agreeing to the other three.
    # The box is MEASURED from the shop's own purchase history -- the GCD of
    # every quantity that item has been bought in -- and falls back to 10
    # strips, which is what 247 of the 900 purchase lines actually used.
    #
    # Single-piece items are exempt. An arm sling is bought in ones, and
    # rounding a device to the nearest ten would order forty slings.
    box = int(it.get("box") or 0)
    if size == 1:
        box = box if box > 1 else 1
    elif box <= 1:
        box = DEFAULT_BOX
    if strips and box > 1:
        rounded = ceil_div(strips, box) * box
        if rounded != strips:
            reasons.append("rounded up from %d to a box of %d" % (strips, box))
            # A BOX CAN BE FAR MORE THAN THE NEED. Rounding 1 strip up to 10 is
            # a tenfold order on a slow item, and that is how a small pharmacy
            # fills its shelf with things nobody asked for. Rounding 53 to 60
            # is not the same act at all. Past twice the need, a person decides.
            if rounded >= BOX_STRETCH_ASK * strips:
                confirm = True
                reasons.append("the box is %.0fx what is actually needed"
                               % (float(rounded) / strips))
        strips = rounded
    value_p = int(strips * size * (it["cost_p"] or 0))
    conf = confidence(it["sell_days"])

    # THE RAIL THAT ACTUALLY BITES. Cover is fixed by the tier, so a cap on DAYS
    # cannot stop a spike -- the quantity scales with the RATE, and one bulk
    # sale to one customer distorts a 133-day mean badly. If a single day
    # carried most of the year's units, the mean is not a rate at all.
    peak = it.get("peak_share") or 0.0
    if strips and peak >= PEAK_SHARE_SPIKE:
        confirm = True
        reasons.append("one day was %d%% of the year's sales — the average is "
                       "a spike, not a rate" % round(peak * 100))
    if strips and conf == "thin":
        confirm = True
        reasons.append("sold on only %d day%s in %d — the daily rate is a guess"
                       % (it["sell_days"], "" if it["sell_days"] == 1 else "s", TRADING_DAYS))
    if strips and value_p >= CONFIRM_LINE_P:
        confirm = True
        reasons.append("one line over Rs %d" % (CONFIRM_LINE_P // 100))
    if strips and it["days_since_sale"] > DEAD_AFTER_DAYS:
        strips, value_p = 0, 0
        reasons.append("nothing sold for %d days — not reordered"
                       % it["days_since_sale"])
    if strips and value_p < MIN_LINE_P and it["on_hand"] > 0:
        strips, value_p = 0, 0
        reasons.append("under Rs %d and not out of stock — waits for the next run"
                       % (MIN_LINE_P // 100))
    if cover > MAX_COVER_DAYS:
        reasons.append("cover capped at %d days" % MAX_COVER_DAYS)
    return {"item": it["item"], "vendor": it["vendor"], "on_hand": it["on_hand"],
            "rate_per_day": round(rate, 2), "sell_days": it["sell_days"],
            "confidence": conf, "cover_days": capped, "pack_size": size, "box": box,
            "order_strips": strips, "order_units": strips * size,
            "value_p": value_p, "confirm": confirm, "single_source": it["single_source"],
            "days_since_sale": it["days_since_sale"],
            "peak_share": round(peak, 3), "why": reasons}


def selftest():
    n = [0]

    def ck(c, m):
        n[0] += 1
        if not c:
            print("check %d FAILED: %s" % (n[0], m))
            raise AssertionError(m)

    base = dict(item="X", vendor="V", on_hand=0, rate_per_day=10.0, sell_days=40,
                pack_size=10, cost_p=100, single_source=False, days_since_sale=1)

    ck(ceil_div(1, 10) == 1, "a part strip rounds UP to a whole one")
    ck(ceil_div(0, 10) == 0, "nothing needed orders nothing")
    ck(ceil_div(20, 10) == 2, "an exact fit does not gain a spare strip")

    ck(as_on_key("27-08-2026") > as_on_key("31-03-2026"),
       "August beats March — dd-mm-yyyy as text gets this backwards")

    got, want = cadence_for(2500000, 9.4)
    ck(got == "weekly", "Rs 25,000 a month is a weekly vendor")
    got, want = cadence_for(2500000, 1.0)
    ck(got == "monthly" and want == "weekly",
       "CEILING NEVER FLOOR: a vendor already used monthly is not moved to weekly")
    got, _ = cadence_for(100000, 4.0)
    ck(got == "monthly", "a small vendor tiers to monthly")

    p = plan_line(dict(base), CADENCE_DAYS["weekly"])
    ck(p["cover_days"] == 12, "weekly cover is 7 + 2 lead + 3 safety")
    ck(p["order_strips"] == 20,
       "12 strips are needed, and the box is 10, so 20 go on the order")
    ck(any("box of 10" in w for w in p["why"]), "and the rounding says so")

    # boxes, measured from the shop's own buying
    ck(plan_line(dict(base, box=5), CADENCE_DAYS["weekly"])["order_strips"] == 15,
       "an item bought in fives rounds to 15, not to 20")
    ck(plan_line(dict(base, box=20), CADENCE_DAYS["weekly"])["order_strips"] == 20,
       "an item bought in twenties rounds to one box")
    p = plan_line(dict(base, rate_per_day=100.0, box=10), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 120 and not any("rounded" in w for w in p["why"]),
       "a quantity already on the box does not claim to have been rounded")
    p = plan_line(dict(base, pack_size=1, cost_p=20000, rate_per_day=0.3, sell_days=40),
                  CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 4,
       "a single-piece item is NOT rounded to ten -- that would order forty arm slings")
    ck(plan_line(dict(base), CADENCE_DAYS["weekly"])["value_p"] == 20 * 10 * 100,
       "the value is priced on what is ACTUALLY ordered, after rounding")

    # a box far bigger than the need is a decision, not a rounding
    # 1/day x 12 days = 12 units = 2 strips; a box of 10 is FIVE times that
    p = plan_line(dict(base, rate_per_day=1.0), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 10 and p["confirm"] is True,
       "2 strips needed, a box of 10 ordered -- that asks first")
    ck(any("5x what is actually needed" in w for w in p["why"]),
       "and says how big the stretch is, in the item's own arithmetic")
    p = plan_line(dict(base, rate_per_day=45.0), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 60 and p["confirm"] is False,
       "54 rounded to 60 is an ordinary box, and does not interrupt anybody")
    ck(p["confirm"] is False, "a well-measured line does not need asking about")

    p = plan_line(dict(base, single_source=True), CADENCE_DAYS["weekly"])
    ck(p["cover_days"] == 15, "a single-source item gets a LONGER buffer, not shorter")

    p = plan_line(dict(base, on_hand=200), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 0, "already covered: nothing is ordered")

    p = plan_line(dict(base, sell_days=3), CADENCE_DAYS["weekly"])
    ck(p["confirm"] is True and p["order_strips"] > 0,
       "a rate from 3 selling days still proposes, but never decides")
    ck(any("guess" in w for w in p["why"]), "and it says why")

    p = plan_line(dict(base, rate_per_day=500.0), CADENCE_DAYS["monthly"])
    ck(p["cover_days"] == 35, "monthly cover is 30 + 2 + 3 = 35")
    ck(p["cover_days"] < MAX_COVER_DAYS,
       "the day-ceiling does NOT bind under the approved tiers, and the test "
       "says so out loud rather than pretending it protects anything")
    ck(plan_line(dict(base, single_source=True), CADENCE_DAYS["monthly"]
                 )["cover_days"] == 38, "the longest cover reachable today is 38")

    # the rail that DOES bite: a mean distorted by one big day
    p = plan_line(dict(base, peak_share=0.55), CADENCE_DAYS["weekly"])
    ck(p["confirm"] is True and p["order_strips"] > 0,
       "a spike-driven average proposes a quantity but never places it alone")
    ck(any("spike" in w for w in p["why"]), "and it names the spike")
    p = plan_line(dict(base, peak_share=0.10), CADENCE_DAYS["weekly"])
    ck(p["confirm"] is False, "ordinary day-to-day variation is not a spike")

    p = plan_line(dict(base, days_since_sale=90), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 0, "nothing sold in 90 days is not reordered")

    p = plan_line(dict(base, cost_p=1, on_hand=5), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 0, "a trivial line waits for the next run")
    p = plan_line(dict(base, cost_p=1, on_hand=0), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] > 0, "unless it is actually out of stock")

    p = plan_line(dict(base, cost_p=20000), CADENCE_DAYS["weekly"])
    ck(p["confirm"] is True, "a line over Rs 5,000 is a person's decision")

    p = plan_line(dict(base, rate_per_day=0.0), CADENCE_DAYS["weekly"])
    ck(p["order_strips"] == 0, "an item with no measured sale asks for nothing")

    print("PO_ENGINE SELFTEST PASSED - %d checks OK" % n[0])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a, _ = ap.parse_known_args()
    if a.selftest:
        sys.exit(selftest())
    print("run with --selftest, or import build_plan from po_build.py")
