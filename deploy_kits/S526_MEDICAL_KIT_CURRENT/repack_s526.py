#!/usr/bin/env python3
"""repack_s526.py -- kit S526_MEDICAL_KIT_CURRENT: the Medical PC's setup kit (deploy_kits/PC_KITS/medical/kit.zip)
brought to the tools that PC runs today. Three payload files are replaced by their live pins; every other member is
copied byte for byte, in the same order, with the same dates; MD5SUMS.txt is rewritten for the three rows only.
Refuses unless the old zip and each new file are exactly their pins.
  python3 repack_s526.py <old kit.zip> <dir with the three new files> <out kit.zip>"""
import hashlib, io, os, sys, zipfile

OLD_ZIP = "83922881945b0cfd02da6fae808eee74"
SWAP = {  # member : (old md5, new md5, file in the source dir)
    "payload/medical_agent.py": ("70d5c4e3c439eaa049acb27f9851688c", "d91fa79ad972c39e531c70afb1a1c758", "S499_medical_agent.py"),
    "payload/marg_watch.py":    ("81145aa7d7c8e9f7e23072cfab1ee620", "0a78ae15be60d8a0293b96ecfa38f35b", "marg_watch.py"),
    "payload/marg_txt.py":      ("70f920c445ec82fc8c1e069f1f758efb", "7fa5136d3bc134a55ffd1392d9f06675", "marg_txt.py"),
}
md5 = lambda b: hashlib.md5(b).hexdigest()


def main(old, src, out):
    ob = open(old, "rb").read()
    if md5(ob) != OLD_ZIP:
        raise SystemExit("REFUSED: the old kit.zip is %s, not %s" % (md5(ob), OLD_ZIP))
    zin = zipfile.ZipFile(io.BytesIO(ob))
    new = {}
    for m, (o, n, f) in SWAP.items():
        if md5(zin.read(m)) != o:
            raise SystemExit("REFUSED: %s in the old zip is not %s" % (m, o))
        b = open(os.path.join(src, f), "rb").read()
        if md5(b) != n:
            raise SystemExit("REFUSED: %s is %s, not the live pin %s" % (f, md5(b), n))
        new[m] = b
    rows = zin.read("MD5SUMS.txt").decode("ascii").splitlines(True)
    out_rows, hit = [], 0
    for r in rows:
        h, name = r[:32], r[34:].rstrip("\r\n")
        if name in SWAP:
            if h != SWAP[name][0]:
                raise SystemExit("REFUSED: MD5SUMS row %s is %s" % (name, h))
            r = SWAP[name][1] + r[32:]
            hit += 1
        out_rows.append(r)
    if hit != 3:
        raise SystemExit("REFUSED: %d of 3 MD5SUMS rows found" % hit)
    new["MD5SUMS.txt"] = "".join(out_rows).encode("ascii")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zo:
        for i in zin.infolist():
            data = new.get(i.filename, zin.read(i.filename))
            zi = zipfile.ZipInfo(i.filename, date_time=(2026, 10, 11, 12, 0, 0) if i.filename in new else i.date_time)
            zi.compress_type = i.compress_type
            zi.external_attr = i.external_attr
            zi.create_system = i.create_system
            zo.writestr(zi, data)
    b = buf.getvalue()
    # read back: every member against the rewritten MD5SUMS, and nothing else changed
    zr = zipfile.ZipFile(io.BytesIO(b))
    assert [i.filename for i in zr.infolist()] == [i.filename for i in zin.infolist()]
    sums = {l[34:].rstrip("\r\n"): l[:32] for l in zr.read("MD5SUMS.txt").decode("ascii").splitlines() if l.strip()}
    for i in zr.infolist():
        if i.filename == "MD5SUMS.txt":
            continue
        d = zr.read(i.filename)
        if i.filename in sums:
            assert md5(d) == sums[i.filename], i.filename
        if i.filename not in new:
            assert d == zin.read(i.filename), i.filename
    assert zr.testzip() is None
    open(out, "wb").write(b)
    print("kit.zip %s -> %s  (%d members, 3 replaced, MD5SUMS 3 rows)" % (OLD_ZIP[:8], md5(b), len(zr.infolist())))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
