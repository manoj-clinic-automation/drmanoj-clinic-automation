# make_s882.py -- S882: owner_console.py e47235b2 -> TO, one anchored insertion (the ledgers' mount beside the Patients page).
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == "e47235b216928793220c0932c0317b09", "FROM pin"
s = b.decode("utf-8")
A = ('    except Exception as _ex_s851:                                      # noqa: BLE001 -- the console stands without it\n'
     '        print("patients_page NOT mounted: %s" % _ex_s851, file=sys.stderr)\n')
assert s.count(A) == 1, "anchor"
ADD = ('    try:                                                               # S882: the two ledgers (his login alone, the same gate)\n'
       '        import payment_ledgers as _s882_pl                             # noqa: PLC0415 -- beside this file\n'
       '        _s882_pl.init(app, db_getter, require_fn, unit)\n'
       '    except Exception as _ex_s882:                                      # noqa: BLE001 -- the console stands without it\n'
       '        print("payment_ledgers NOT mounted: %s" % _ex_s882, file=sys.stderr)\n')
assert "payment_ledgers" not in s
open(dst, "wb").write(s.replace(A, A + ADD).encode("utf-8"))
