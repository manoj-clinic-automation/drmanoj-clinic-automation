#!/usr/bin/env python3
"""walk_s974.py -- S974_CERT_LAND on a made-up root (made-up certificates, no network, no restart).
   python3 walk_s974.py [path/to/cert_land.py]      exit 0 = all pass."""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "cert_land.py")
R = tempfile.mkdtemp(prefix="s974walk_")
LS, AC, WD = os.path.join(R, "lsws"), os.path.join(R, "acme"), os.path.join(R, "wa")
LE = os.path.join(R, "letsencrypt", "live")
P = [0, 0]


def ck(name, got, want=True):
    P[0 if got == want else 1] += 1
    print(("  ok   " if got == want else "  FAIL ") + name + ("" if got == want else "  (got %r)" % (got,)))


def mkpair(d, stem, days, cn, san=None, issuer_o=None):
    os.makedirs(d, exist_ok=True)
    k, c = os.path.join(d, stem + ".key"), os.path.join(d, stem + ".crt")
    subj = "/CN=%s" % cn + ("/O=%s" % issuer_o if issuer_o else "")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256", "-nodes",
                    "-keyout", k, "-out", c, "-days", str(days), "-subj", subj,
                    "-addext", "subjectAltName=DNS:%s" % (san or cn)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return k, c


def rd(p):
    with open(p, "rb") as fh:
        return fh.read()


def site(name, file_days, acme_days, acme_san=None, acme_key_other=False, staging=False, link=False,
         vh_mismatch=False, no_vhost=False, share_with=None):
    tmp = os.path.join(R, "gen", name)
    fk, fc = mkpair(tmp, "file", file_days, name)
    if vh_mismatch:
        fk, _ = mkpair(tmp, "other", file_days, name)
    if not no_vhost:
        if share_with:
            keyf, certf = os.path.join(R, "home", share_with, "ssl", "privkey.pem"), os.path.join(R, "home", share_with, "ssl", "fullchain.pem")
        elif link:
            live = os.path.join(LE, name)
            os.makedirs(live, exist_ok=True)
            shutil.copy(fk, os.path.join(live, "privkey.pem")); shutil.copy(fc, os.path.join(live, "fullchain.pem"))
            keyf, certf = os.path.join(R, "certs", name, "key.pem"), os.path.join(R, "certs", name, "cert.pem")
            os.makedirs(os.path.dirname(keyf), exist_ok=True)
            os.symlink(os.path.join(live, "privkey.pem"), keyf); os.symlink(os.path.join(live, "fullchain.pem"), certf)
        else:
            vd = os.path.join(R, "home", name, "ssl")
            os.makedirs(vd, exist_ok=True)
            shutil.copy(fk, os.path.join(vd, "privkey.pem")); shutil.copy(fc, os.path.join(vd, "fullchain.pem"))
            keyf, certf = "$VH_ROOT/ssl/privkey.pem", "$VH_ROOT/ssl/fullchain.pem"
        vdir = os.path.join(LS, "conf", "vhosts", name)
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "vhost.conf"), "w") as fh:
            fh.write("docRoot $VH_ROOT/public_html\nvhssl  {\n  keyFile                 %s\n  certFile                %s\n  certChain               1\n}\n" % (keyf, certf))
        with open(os.path.join(LS, "conf", "httpd_config.conf"), "a") as fh:
            fh.write("virtualhost %s {\n  vhRoot                  %s/home/%s/\n}\n" % (name, R, name))
    ad = os.path.join(AC, name + "_ecc")
    ak, ac = mkpair(os.path.join(R, "gen", name, "acme"), "a", acme_days, name, san=acme_san,
                    issuer_o="(STAGING) Lets Encrypt" if staging else None)
    if acme_key_other:
        ak, _ = mkpair(os.path.join(R, "gen", name, "acme2"), "b", acme_days, name)
    os.makedirs(ad, exist_ok=True)
    shutil.copy(ak, os.path.join(ad, name + ".key")); shutil.copy(ac, os.path.join(ad, "fullchain.cer"))


def files_of(name, link=False):
    if link:
        return os.path.join(R, "certs", name, "key.pem"), os.path.join(R, "certs", name, "cert.pem")
    d = os.path.join(R, "home", name, "ssl")
    return os.path.join(d, "privkey.pem"), os.path.join(d, "fullchain.pem")


def run(*args, extra=None):
    env = dict(os.environ, CERT_LAND_LSWS=LS, CERT_LAND_ACME=AC, CERT_LAND_STATE=os.path.join(WD, "cert_land.state.json"),
               CERT_LAND_WATCH_DIR=WD, CERT_LAND_RESTART="true", CERT_LAND_WAIT="0", CERT_LAND_SERVED_FROM_FILE="1")
    env.update(extra or {})
    p = subprocess.run([sys.executable, "-B", MOD] + list(args), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode()


def state():
    with open(os.path.join(WD, "cert_land.state.json")) as fh:
        return json.load(fh)


try:
    os.makedirs(os.path.join(LS, "conf"), exist_ok=True); os.makedirs(WD)
    SITES = [("inplace.test", 80, 80), ("renewed.test", 9, 89), ("older.test", 80, 50), ("keybad.test", 9, 89),
             ("staging.test", 9, 89), ("young.test", 9, 25), ("linked.test", 9, 89), ("noserve.test", 20, 89),
             ("novhost.test", 9, 89), ("misnamed.test", 9, 89), ("vhbad.test", 9, 89),
             ("share1.test", 9, 89), ("share2.test", 9, 89)]
    with open(os.path.join(WD, "cert_watch.py"), "w") as fh:
        fh.write("SITES = [\n" + "".join('    ("%s", True, "walk"),\n' % s[0] for s in SITES) +
                 '    ("retired.test", False, "retired"),\n]\n')
    for n, f, a in SITES:
        site(n, f, a, acme_key_other=(n == "keybad.test"), staging=(n == "staging.test"), link=(n == "linked.test"),
             acme_san=("other.test" if n == "misnamed.test" else None), vh_mismatch=(n == "vhbad.test"),
             no_vhost=(n == "novhost.test"), share_with=("share1.test" if n == "share2.test" else None))
    # inplace.test: the acme pair IS the vhost pair
    k, c = files_of("inplace.test")
    shutil.copy(os.path.join(AC, "inplace.test_ecc", "inplace.test.key"), k); shutil.copy(os.path.join(AC, "inplace.test_ecc", "fullchain.cer"), c)
    before = {n: (rd(files_of(n, n == "linked.test")[0]), rd(files_of(n, n == "linked.test")[1]))
              for n, _f, _a in SITES if n not in ("novhost.test", "share2.test")}

    print("W1 --dry: the LOOK only")
    rc, out = run("--dry")
    ck("dry exits 0", rc, 0)
    ck("dry writes no state", os.path.exists(os.path.join(WD, "cert_land.state.json")), False)
    ck("dry changes no file", all((rd(files_of(n, n == "linked.test")[0]), rd(files_of(n, n == "linked.test")[1])) == v
                                  for n, v in before.items()))
    ck("dry would install 3 (renewed, linked, noserve)", "would install: 3" in out, True)
    ck("retired site not looked at", "retired.test" in out, False)
    ck("no key text printed", "PRIVATE KEY" in out or "BEGIN CERT" in out, False)

    print("W2 the real run; noserve.test 'serves' a frozen old certificate")
    frozen = os.path.join(R, "frozen.pem")
    shutil.copy(files_of("noserve.test")[1], frozen)
    # served-from-file mode reads certFile; for noserve we point its vhost certFile reading at... use a wrapper:
    wrapper = os.path.join(R, "cl_wrap.py")
    with open(wrapper, "w") as fh:
        fh.write("import runpy, sys, os\nsys.argv=[%r]+sys.argv[1:]\nimport importlib.util\n"
                 "spec=importlib.util.spec_from_file_location('cl', %r); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                 "_o=m.served_pem\n"
                 "def sp(site, certfile=None):\n    return open(%r,'rb').read() if site=='noserve.test' else _o(site, certfile)\n"
                 "m.served_pem=sp\nsys.exit(m.main(sys.argv[1:]))\n" % (MOD, MOD, frozen))
    env_mod = MOD
    MOD = wrapper
    rc, out = run()
    MOD = env_mod
    print("     | " + out.strip().splitlines()[0])
    st = state()
    v = {s["site"]: s["verdict"] for s in st["sites"]}
    ck("exit 1 (faults present)", rc, 1)
    ck("inplace: in place", v.get("inplace.test"), "in place")
    ck("renewed: installed", v.get("renewed.test"), "installed")
    k, c = files_of("renewed.test")
    ck("renewed: files now = acme pair", (rd(k), rd(c)) == (rd(os.path.join(AC, "renewed.test_ecc", "renewed.test.key")),
                                                          rd(os.path.join(AC, "renewed.test_ecc", "fullchain.cer"))))
    import glob as _g, time as _t
    bk = _g.glob(k + ".bak_S974_*") + _g.glob(c + ".bak_S974_*")
    ck("renewed: two backups beside", len(bk), 2)
    ck("renewed: backups = the old pair", sorted(rd(b) for b in bk) == sorted(before["renewed.test"]))
    ck("renewed: key backup mode 600", oct(os.stat([b for b in bk if "privkey" in b][0]).st_mode & 0o777), "0o600")
    ck("older: not touched", v.get("older.test"), "acme not newer")
    ck("older: files unchanged", (rd(files_of("older.test")[0]), rd(files_of("older.test")[1])) == before["older.test"])
    ck("keybad: fault, untouched", (v.get("keybad.test"), (rd(files_of("keybad.test")[0]), rd(files_of("keybad.test")[1])) == before["keybad.test"]),
       ("acme pair mismatched", True))
    ck("staging: fault, untouched", (v.get("staging.test"), (rd(files_of("staging.test")[0]), rd(files_of("staging.test")[1])) == before["staging.test"]),
       ("acme staging", True))
    ck("young: not fresh, untouched", (v.get("young.test"), (rd(files_of("young.test")[0]), rd(files_of("young.test")[1])) == before["young.test"]),
       ("acme not fresh", True))
    lk, lc = files_of("linked.test", True)
    ck("linked: installed", v.get("linked.test"), "installed")
    ck("linked: still links", os.path.islink(lk) and os.path.islink(lc), True)
    ck("linked: target holds the new pair", rd(os.path.join(LE, "linked.test", "fullchain.pem")) == rd(os.path.join(AC, "linked.test_ecc", "fullchain.cer")))
    ck("noserve: not served, put back", v.get("noserve.test"), "not served, put back")
    ck("noserve: files = the old pair again", (rd(files_of("noserve.test")[0]), rd(files_of("noserve.test")[1])) == before["noserve.test"])
    ck("novhost: counted, no act", v.get("novhost.test"), "no vhost")
    ck("misnamed: fault, untouched", (v.get("misnamed.test"), (rd(files_of("misnamed.test")[0]), rd(files_of("misnamed.test")[1])) == before["misnamed.test"]),
       ("acme misnamed", True))
    ck("vhbad: hands off", (v.get("vhbad.test"), (rd(files_of("vhbad.test")[0]), rd(files_of("vhbad.test")[1])) == before["vhbad.test"]),
       ("vhost pair mismatched", True))
    ck("shared: both hands off", (v.get("share1.test"), v.get("share2.test")), ("vhost files shared", "vhost files shared"))
    ck("shared: the one real pair unchanged", (rd(files_of("share1.test")[0]), rd(files_of("share1.test")[1])) == before["share1.test"])
    ck("state: last_fail written", bool(st.get("last_fail_iso")), True)
    ck("state: the failed pair held", sorted((st.get("held") or {}).keys()), ["noserve.test"])
    ck("state: held carries fp + since", sorted((st.get("held") or {}).get("noserve.test", {}).keys()), ["fp", "since"])
    ck("state: no success on a run with faults", bool(st.get("last_success_iso")), False)
    ck("state: installed listed", sorted(st.get("last_installed", [])), ["linked.test", "renewed.test"])
    ck("state holds no key or cert text", "BEGIN" in json.dumps(st), False)
    ck("printed: no key text", "PRIVATE KEY" in out or "BEGIN CERT" in out, False)

    print("W2b the next night: the failed pair is held (no restart loop; 20 days left > 14)")
    MOD = wrapper
    rc, out = run()
    MOD = env_mod
    v = {s["site"]: s["verdict"] for s in state()["sites"]}
    ck("noserve: held, not tried again", v.get("noserve.test"), "held: failed before")
    ck("noserve: files still the old pair", (rd(files_of("noserve.test")[0]), rd(files_of("noserve.test")[1])) == before["noserve.test"])
    ck("noserve: no second backup", len(_g.glob(files_of("noserve.test")[1] + ".bak_S974_*")), 1)

    print("W2c in the last fortnight a held pair is tried again")
    import time as _tm
    # noserve's served cert has 20 days; with the retry line at 30 days it is tried again, fails again, is put back again
    MOD = wrapper
    rc, out = run(extra={"CERT_LAND_RETRY_DAYS": "30"})
    MOD = env_mod
    v = {s["site"]: s["verdict"] for s in state()["sites"]}
    ck("noserve (inside the retry line): tried again, put back", v.get("noserve.test"), "not served, put back")
    ck("noserve: files still the old pair", (rd(files_of("noserve.test")[0]), rd(files_of("noserve.test")[1])) == before["noserve.test"])

    print("W3 a clean estate: faulty sites mended -> success, second run of the day keeps the first backup")
    for n in ("keybad.test", "staging.test", "misnamed.test", "vhbad.test", "noserve.test", "share1.test", "share2.test"):
        shutil.rmtree(os.path.join(LS, "conf", "vhosts", n))
    bk_before = {b: rd(b) for b in bk}
    rc, out = run()
    st = state()
    v = {s["site"]: s["verdict"] for s in st["sites"]}
    ck("exit 0", rc, 0)
    ck("renewed: now in place", v.get("renewed.test"), "in place")
    ck("success written", bool(st.get("last_success_iso")), True)
    ck("success newer than the fail", st.get("last_success_iso", "") >= st.get("last_fail_iso", "~"), True)
    ck("the day's first backup kept", all(rd(b) == x for b, x in bk_before.items()), True)

    print("W3b a crash turns the leg red")
    rc, out = run(extra={"CERT_LAND_WATCH_DIR": os.path.join(R, "nowhere")})
    st = state()
    ck("crash: exit 2", rc, 2)
    ck("crash: last_fail newer than last_success", st.get("last_fail_iso", "") >= st.get("last_success_iso", "~"), True)
    ck("crash: said so", "the job itself failed" in out, True)

    print("W3c an empty write is refused before the file is opened")
    import importlib.util as _iu
    spec = _iu.spec_from_file_location("cl_unit", MOD); cl = _iu.module_from_spec(spec); spec.loader.exec_module(cl)
    tf = os.path.join(R, "unit.key"); open(tf, "wb").write(b"KEEP")
    try:
        cl.write_content(tf, None); refused = False
    except ValueError:
        refused = True
    ck("None refused, file kept", (refused, rd(tf)), (True, b"KEEP"))
    tb = os.path.join(R, "unit.crt"); open(tb, "wb").write(b"one")
    b1 = cl.backup(tb, "20990101"); open(tb, "wb").write(b"two"); b2 = cl.backup(tb, "20990101")
    ck("a changed file gets a fresh backup", (b1 != b2, rd(b1), rd(b2)), (True, b"one", b"two"))

    print("W4 the health leg reads the state")
    sys.path.insert(0, os.path.join(HERE, "_fresh"))
    legs_ok = True
    try:
        import freshness                                   # the box's own collector, copied beside for the walk
        leg = {"name": "certificate lands", "group": "Watchdog", "kind": "state_json",
               "target": os.path.join(WD, "cert_land.state.json"), "field": "last_success_iso",
               "fail_field": "last_fail_iso", "max_age_h": 26, "note": "walk"}
        ts, never, detail = freshness.read_state_json(leg)
        ck("the collector reads last_success_iso", ts is not None and never is None, True)
        ck("the collector reads last_fail_iso", freshness.read_fail_ts(leg, "last_fail_iso") is not None, True)
    except ImportError:
        legs_ok = False
        ck("freshness.py copied beside for the walk", False)
finally:
    shutil.rmtree(R, ignore_errors=True)
print("walk_s974: %d pass, %d fail" % (P[0], P[1]))
sys.exit(0 if P[1] == 0 else 1)
