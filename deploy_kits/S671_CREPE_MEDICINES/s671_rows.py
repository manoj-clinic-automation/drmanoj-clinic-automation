"""s671_rows.py -- kit S671_CREPE_MEDICINES (Sanjeevni session S359, 28-Oct-2026). The owner, 05:31 IST: "crepe bandages, all sizes, and
leukoband are stocked in pharmacy for selling to patients, and they shdnt be consumables." Leukoband is Medicines by his own ruling of
18-Sep; the nine crepe rows of stock_item_section are still the S268 seed's Consumables (the word CREPE). This moves them to Medicines, as
his word (source owner). Data only; no code changes; every reader of the table (the count rounds, the stock statement, the piles, the
expiry watch) follows at its next read.
  python s671_rows.py check  DB      -> prints BEFORE / AFTER / OTHER (exit 0 when the nine rows are wholly one or the other)
  python s671_rows.py apply  DB OUT  -> backs the nine rows up to OUT (json), moves them, reads back; exit 0 only when all nine moved
  python s671_rows.py undo   DB OUT  -> puts the nine rows back exactly from OUT"""
import hashlib, json, sqlite3, sys, datetime as dt

KEYS = ("CREPE 8CM 3IN SUNLINE", "CREPE BANDAGE 6CM 2IN", "GLOCREPE", "LEUKOCREPE 6 CM", "LEUKOCREPE 8 CM", "LEUKOCREPE 10CM 4IN",
        "LEUKOCREPE 15CM 6INC", "TOPCREPE 10 CM", "TOPCREPE 15 CM")
BY = "manoj (28-Oct-2026, S359: crepe bandages are sold, not consumables)"
Q = ",".join("?" * len(KEYS))


def rows(c):
    return {r[0]: r for r in c.execute("SELECT item_key, item, section, source, seeded_as, by_user, at FROM stock_item_section WHERE item_key IN (%s)" % Q, KEYS)}


def others_md5(c):
    h = hashlib.md5()
    for r in c.execute("SELECT * FROM stock_item_section WHERE item_key NOT IN (%s) ORDER BY item_key" % Q, KEYS):
        h.update(repr(tuple(r)).encode())
    return h.hexdigest(), c.execute("SELECT COUNT(*) FROM stock_item_section").fetchone()[0]


def state(c):
    rr = rows(c)
    before = sum(1 for r in rr.values() if r[2] == "Consumables" and r[3] == "seed")
    after = sum(1 for r in rr.values() if r[2] == "Medicines" and r[3] == "owner" and r[5] == BY)
    return len(rr), before, after


def main(a):
    cmd, db = a[1], a[2]
    c = sqlite3.connect(db, timeout=60)
    n, before, after = state(c)
    if cmd == "check":
        print("ROWS %d BEFORE %d AFTER %d" % (n, before, after))
        return 0 if n == len(KEYS) and (before == n or after == n) else 1
    if cmd == "apply":
        if not (n == len(KEYS) and before == n):
            print("REFUSED: the nine rows are not as this kit read them (rows %d, seed Consumables %d, moved %d)" % (n, before, after))
            return 1
        rr = rows(c)
        json.dump({k: list(v) for k, v in rr.items()}, open(a[3], "w"), indent=1)
        m0 = others_md5(c)
        at = dt.datetime.now().replace(microsecond=0).isoformat()
        with c:
            for k in KEYS:
                c.execute("UPDATE stock_item_section SET section='Medicines', source='owner', by_user=?, at=? WHERE item_key=? AND section='Consumables' AND source='seed'", (BY, at, k))
        n2, b2, a2 = state(c)
        m1 = others_md5(c)
        ok = a2 == len(KEYS) and b2 == 0 and m0 == m1
        print("%s: moved %d of %d; every other row of the table unchanged: %s (%d rows)" % ("OK" if ok else "RED", a2, len(KEYS), m0 == m1, m1[1]))
        return 0 if ok else 1
    if cmd == "undo":
        saved = json.load(open(a[3]))
        with c:
            for k, v in saved.items():
                c.execute("UPDATE stock_item_section SET item=?, section=?, source=?, seeded_as=?, by_user=?, at=? WHERE item_key=?", (v[1], v[2], v[3], v[4], v[5], v[6], k))
        n2, b2, a2 = state(c)
        print("UNDONE: seed Consumables %d of %d" % (b2, len(KEYS)))
        return 0 if b2 == len(KEYS) else 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
