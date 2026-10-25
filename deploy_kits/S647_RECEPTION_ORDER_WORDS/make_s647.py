"""make_s647.py -- kit S647_RECEPTION_ORDER_WORDS (session S349, the parent, 25-Oct-2026). The owner's 'do both' (07:55 IST) to the wording
'Order ka maal nahi aaya — supplier ko call kijiye' for reception's line reception.order_arrival: since S619 (22-Oct) that duty counts
orders whose goods have NOT come; the seed still said 'Maal aaya hai: supplier ka bill scan kijiye'. Her panel was never saved, so
the seed governs what she sees. ONE counted edit on /root/finance/aaj_seed.py 2df0d3a9 (S645's TO): that line's hi and en.
Usage: python make_s647.py <live aaj_seed.py> <out aaj_seed.py>"""
import hashlib, sys
FROM = "2df0d3a91bfc9c024763b9a837dab904"
OLD = ("            {'id': 'reception.order_arrival',\n"
       "             'hi': 'Maal aaya hai: supplier ka bill scan kijiye',\n"
       "             'en': \"Goods have come: scans the supplier's bill.\",\n")
NEW = ("            {'id': 'reception.order_arrival',\n"
       "             'hi': 'Order ka maal nahi aaya — supplier ko call kijiye',            # S647: the owner's wording, 25-Oct\n"
       "             'en': \"An order's goods have not come: calls the supplier.\",\n")
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "the live aaj_seed.py is not 2df0d3a9"
s = b.decode("utf-8"); assert s.count(OLD) == 1, "anchor not found exactly once"
s = s.replace(OLD, NEW, 1); open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("1 counted edit ->", hashlib.md5(s.encode("utf-8")).hexdigest())
