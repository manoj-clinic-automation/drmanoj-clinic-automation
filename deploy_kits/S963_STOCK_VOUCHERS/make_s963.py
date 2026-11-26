#!/usr/bin/env python3
"""make_s963.py -- S963_STOCK_VOUCHERS: builds the three changed server files from their live bytes (the 26-Nov bundle = the S837 pins)
and checks the new reader. Every insertion is anchored on text that occurs exactly once; a FROM of any other md5 is refused.
    python3 make_s963.py FROM_DIR OUT_DIR        (FROM_DIR holds marg_ingest/{signatures.json,marg_take.py,marg_ingest.py})"""
import hashlib, json, os, sys

FROM = {"marg_ingest/signatures.json": "50ca61f470da66dcc7b22f32f9740190",
        "marg_ingest/marg_take.py": "bc621caf202de958517cd5e8d9c25290",
        "marg_ingest/marg_ingest.py": "b11099ffdf66f6fd78409cecd36a1ec5"}

HEAD = ["DATE", "VOUCHER", "PARTY", "ITEM NAME", "PACKING", "BATCH", "QTY", "UNIT", "EXPIRY", "RATE", "VALUE", "UNITS", "BILL VALUE"]
NOTE = ("S963 (D1083, D1084, 26-Nov-2026): Marg's STOCK %s report (Transactions > Stock %s > Modify > Alt+P > Report, Detail+Items, a "
        "period) -- the text converted on the medical PC by marg_txt S963 into one row per voucher (day, number, 'cash' or 'party' -- the "
        "party's name is never written -- gross and bill value) and one per item line, the TOTAL row last. Dated by its own title's FROM .. "
        "TO; every row's day must lie inside it (verify). Name-free, so the file is kept. A VERIFIED sheet is read at once by "
        "marg_vouchers.py (marg_take / marg_ingest hooks) into mi_voucher_file / mi_voucher / mi_voucher_line.")


def sig(kind):
    return {"type": "STOCK_VOUCHERS", "variant": kind, "title_regex": "^\\s*STOCK\\s+%s\\s+FROM\\s+\\d{2}-\\d{2}-\\d{4}\\s+TO\\b" % kind,
            "header": HEAD, "end_row": ["TOTAL"], "deep_verify": "structural", "uploadable": False,
            "_note": NOTE % (kind, kind.title())}


def block():
    out = ""
    for k in ("ISSUE", "RECEIVE"):
        t = json.dumps(sig(k), indent=2, ensure_ascii=False)
        out += ",\n" + "\n".join("    " + l for l in t.split("\n"))
    return out


TAKE_FN_OLD = ('def take(raw, name="", source="manual", db=None, archive=None):\n')
TAKE_FN_NEW = ('def _s963_vouchers(con, md5, path, stamp=""):\n'
               '    """S963 (D1084): Marg\'s stock vouchers -> mi_voucher_file / mi_voucher / mi_voucher_line, name-free (marg_vouchers.py).\n'
               '    Never raises -> (lines read, note); a note starting "not read: " means no file of it is kept either."""\n'
               '    try:\n'
               '        import marg_vouchers                                  # noqa: PLC0415\n'
               '        return marg_vouchers.store_path(con, md5, path, MI.now_ist().isoformat(), MI._readers().open_sheet, stamp)\n'
               '    except Exception as e:                                    # noqa: BLE001\n'
               '        return 0, "failed: %s" % str(e)[:100]\n'
               '\n\n' + TAKE_FN_OLD)
TAKE_HOOK_OLD = ('                nlines = _s837_register(con, md5, local)                            #   before the file is deleted below (S186)\n')
TAKE_HOOK_NEW = (TAKE_HOOK_OLD +
                 '            if typ == "STOCK_VOUCHERS" and verdict == "VERIFIED":                   # S963 (D1084): Marg\'s stock vouchers, '
                 'name-free\n'
                 '                nlines, _n963 = _s963_vouchers(con, md5, local, MI.stamp_of(sname, ""))   # its own export time, or none\n'
                 '                if _n963.startswith("not read: "):\n'
                 '                    phi = True                                                      #   a sheet not read: no file of it kept\n')
ING_OLD = ('                    nlines, _n837 = marg_register.store_path(con, f["md5"], local, now_ist().isoformat(), R.open_sheet)\n'
           '                except Exception:                                              # noqa: BLE001\n'
           '                    nlines = 0\n')
ING_NEW = (ING_OLD +
           '            if typ == "STOCK_VOUCHERS" and verdict == "VERIFIED" and not dry:      # S963 (D1084): Marg\'s stock vouchers, name-free\n'
           '                try:\n'
           '                    import marg_vouchers                                       # noqa: PLC0415\n'
           '                    nlines, _n963 = marg_vouchers.store_path(con, f["md5"], local, now_ist().isoformat(), R.open_sheet, stamp)\n'
           '                    if _n963.startswith("not read: "):\n'
           '                        phi = True                                             #   a sheet not read: no file of it kept\n'
           '                except Exception:                                              # noqa: BLE001\n'
           '                    nlines = 0\n')
HEAL_OLD = ('    t1 = now_ist()\n    note = "more than %d new -- the rest next run" % limit if len(new) > limit else ""\n')
HEAL_NEW = ('    if not dry:                                                # S963 (cold review S7): a voucher sheet whose read failed is read again\n'
            '        try:\n'
            '            import marg_vouchers                                       # noqa: PLC0415\n'
            '            marg_vouchers.heal(con, cfg["archive"], R.open_sheet, now_ist().isoformat())\n'
            '        except Exception:                                              # noqa: BLE001\n'
            '            pass\n' + HEAL_OLD)
SIG_OLD = ('through marg_take\'s hook."\n    }\n  ],\n  "_EXAMPLE_adding_a_new_type"')


def one(t, old, new, what):
    if t.count(old) != 1:
        sys.exit("REFUSED: anchor %s found %d times" % (what, t.count(old)))
    return t.replace(old, new)


def main(src, out):
    files = {}
    for rel, want in FROM.items():
        b = open(os.path.join(src, rel), "rb").read()
        got = hashlib.md5(b).hexdigest()
        if got != want:
            sys.exit("REFUSED: %s is %s, not the live %s" % (rel, got, want))
        files[rel] = b.decode("utf-8")
    s = files["marg_ingest/signatures.json"]
    s = one(s, SIG_OLD, SIG_OLD.replace('\n    }\n  ],', '\n    }' + block() + '\n  ],'), "signatures")
    json.loads(s)
    files["marg_ingest/signatures.json"] = s
    t = files["marg_ingest/marg_take.py"]
    t = one(t, TAKE_FN_OLD, TAKE_FN_NEW, "take()")
    t = one(t, TAKE_HOOK_OLD, TAKE_HOOK_NEW, "take hook")
    files["marg_ingest/marg_take.py"] = t
    g = one(files["marg_ingest/marg_ingest.py"], ING_OLD, ING_NEW, "ingest hook")
    files["marg_ingest/marg_ingest.py"] = one(g, HEAL_OLD, HEAL_NEW, "ingest heal")
    for rel, txt in files.items():
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        b = txt.encode("utf-8")
        open(p, "wb").write(b)
        print("%s  %s" % (hashlib.md5(b).hexdigest(), rel))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
