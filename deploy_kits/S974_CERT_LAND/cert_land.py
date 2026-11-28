#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cert_land.py  --  the renewed certificate lands where the web server reads it
Dr. Manoj Agarwal Clinic . Bareilly . kit S974_CERT_LAND (session S541, 28-Nov-2026, F-1731)

WHY
  28-Nov-2026: followup.dr-manoj.in served the 08-Dec certificate while CyberPanel's
  nightly renew.py logged "SSL renewal SUCCESSFUL" every night from 23-Nov. The
  renewal lands in acme.sh's own folder (/root/.acme.sh/<site>_ecc/) and was never
  copied into the two files the site's vhost names (vhssl keyFile / certFile).
  It was copied in by hand at 07:58 28-Nov. S759 (09-Nov) mended the same for
  drmanojagarwal.com alone. This job does it for every watched site, every night.

WHAT IT DOES (nightly, 00:25 UTC = 05:55 IST: after renew.py 00:00 and acme.sh 00:07,
before the certificate watch at 06:40 IST)
  For each site cert_watch.py watches (one list, never two):
    LOOK  the vhost's keyFile / certFile; acme.sh's pair for the site.
    The acme.sh pair is INSTALLED only when every one of these holds:
      - it ends LATER than what certFile holds, and has more than MIN_DAYS left;
      - its certificate and key belong together (same public key);
      - it names the site; it is not from Let's Encrypt STAGING (S236);
      - the vhost's own two files are themselves a matching pair (the fallback).
    ACT   the two files backed up beside (.bak_S974_<date>), the new pair written
          into them by content (a symlinked path keeps its link), the web server
          restarted ONCE for all sites, and the certificate each site SERVES read
          back. A site that does not serve its new certificate gets its two files
          put back, and the web server is restarted once more.
  Silent otherwise: nothing to install = nothing printed but one log line.
  The state file feeds the health page (freshness leg "certificate lands").

  --dry   the LOOK only; nothing written, no state.
  --selftest  the pure parts, on certificates made in a temp folder.
No secret, key or certificate text is ever printed -- only names, days and verdicts.
"""
import datetime as dt
import glob
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

KIT = "S974_CERT_LAND"
VERSION = "1.1"
LSWS = os.environ.get("CERT_LAND_LSWS", "/usr/local/lsws")
ACME_HOME = os.environ.get("CERT_LAND_ACME", "/root/.acme.sh")
STATE = os.environ.get("CERT_LAND_STATE", "/root/wa/cert_land.state.json")
WATCH_DIR = os.environ.get("CERT_LAND_WATCH_DIR", "/root/wa")
SERVED_HOST = os.environ.get("CERT_LAND_HOST", "127.0.0.1")
RESTART_CMD = os.environ.get("CERT_LAND_RESTART", "")
SERVED_FROM_FILE = os.environ.get("CERT_LAND_SERVED_FROM_FILE", "")   # walks only: "served" = what certFile holds
WAIT_S = float(os.environ.get("CERT_LAND_WAIT", "8"))
TRIES = int(os.environ.get("CERT_LAND_TRIES", "4"))          # the read-back: up to 4 looks, WAIT_S apart
MIN_DAYS = 30
RETRY_DAYS = int(os.environ.get("CERT_LAND_RETRY_DAYS", "14"))                                          # a held pair is retried once the served one has 14 days or fewer
OPENSSL = os.environ.get("CERT_LAND_OPENSSL", "openssl")


def now_iso():
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def run(args, data=None, timeout=20):
    try:
        p = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return p.returncode, p.stdout
    except Exception:                                   # noqa: BLE001
        return 99, b""


# ---------------------------------------------------------------- certificates
def cert_info(pem):
    """bytes of a PEM certificate (first one) -> dict(end_epoch, fp, pub, names, issuer) or None."""
    if not pem:
        return None
    rc, out = run([OPENSSL, "x509", "-noout", "-enddate", "-fingerprint", "-sha256", "-issuer",
                   "-ext", "subjectAltName"], data=pem)
    if rc != 0 or not out:
        rc, out = run([OPENSSL, "x509", "-noout", "-enddate", "-fingerprint", "-sha256", "-issuer"], data=pem)
        if rc != 0 or not out:
            return None
    end, fp, issuer, names = None, "", "", []
    for line in out.decode("utf-8", "replace").splitlines():
        s = line.strip()
        if s.startswith("notAfter="):
            try:
                end = int(dt.datetime.strptime(s[9:].replace("  ", " "), "%b %d %H:%M:%S %Y %Z")
                          .replace(tzinfo=dt.timezone.utc).timestamp())
            except ValueError:
                end = None
        elif "Fingerprint=" in s:
            fp = s.split("=", 1)[1]
        elif s.startswith("issuer="):
            issuer = s[7:]
        elif "DNS:" in s:
            names += [x.strip()[4:] for x in s.split(",") if x.strip().startswith("DNS:")]
    rc, pub = run([OPENSSL, "x509", "-noout", "-pubkey"], data=pem)
    if end is None or not fp or rc != 0:
        return None
    return {"end": end, "fp": fp, "pub": pub.strip(), "names": names, "issuer": issuer}


def key_pub(key_bytes):
    if not key_bytes:
        return None
    rc, out = run([OPENSSL, "pkey", "-pubout"], data=key_bytes)
    return out.strip() if rc == 0 and out.strip() else None


def days_left(end, now=None):
    return int(((end or 0) - (now if now is not None else time.time())) // 86400)


def read(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


def name_matches(host, names):
    host = (host or "").lower().rstrip(".")
    for n in names:
        n = (n or "").lower().rstrip(".")
        if n == host:
            return True
        if n.startswith("*.") and n[2:] and host.endswith("." + n[2:]) and host[: -(len(n) - 1)].count(".") == 0:
            return True
    return False


def is_staging(issuer):
    t = (issuer or "").upper()
    return "STAGING" in t or "FAKE LE" in t or "(STAGING)" in t


# ---------------------------------------------------------------- the server's files
def sites():
    """cert_watch.py's own list -- adding a site there adds it here (one list)."""
    sys.path.insert(0, WATCH_DIR)
    try:
        import cert_watch                               # noqa: E402
        return [h for (h, watch, _l) in cert_watch.SITES if watch]
    finally:
        sys.path.pop(0)


def vh_root(site):
    conf = os.path.join(LSWS, "conf", "httpd_config.conf")
    data = (read(conf) or b"").decode("utf-8", "replace").splitlines()
    inside = False
    for line in data:
        f = line.split()
        if len(f) >= 2 and f[0] == "virtualhost":
            inside = (f[1] == site)
        elif inside and len(f) >= 2 and f[0] == "vhRoot":
            return f[1].rstrip("/")
    return "/home/" + site


def vhost_files(site):
    """-> (keyFile, certFile) from the vhost's vhssl block, or (None, None)."""
    vh = os.path.join(LSWS, "conf", "vhosts", site, "vhost.conf")
    text = read(vh)
    if text is None:
        return None, None
    key = cert = None
    inside = False
    for line in text.decode("utf-8", "replace").splitlines():
        s = line.strip()
        if s.startswith("vhssl") and s.endswith("{"):
            inside = True
            continue
        if inside and s.startswith("}"):
            inside = False
            continue
        if inside:
            f = s.split()
            if len(f) >= 2 and f[0] == "keyFile" and key is None:
                key = f[1]
            elif len(f) >= 2 and f[0] == "certFile" and cert is None:
                cert = f[1]
    root = vh_root(site)

    def sub(p):
        return p and p.replace("$VH_ROOT", root).replace("$SERVER_ROOT", LSWS).replace("$VH_NAME", site)
    return sub(key), sub(cert)


def acme_pair(site):
    for d in (os.path.join(ACME_HOME, site + "_ecc"), os.path.join(ACME_HOME, site)):
        c, k = os.path.join(d, "fullchain.cer"), os.path.join(d, site + ".key")
        if os.path.isfile(c) and os.path.isfile(k):
            return c, k
    return None, None


def served_pem(site, certfile=None):
    if SERVED_FROM_FILE:                                 # walks: the made-up server "serves" its certFile
        return read(certfile) if certfile else None
    rc, out = run([OPENSSL, "s_client", "-servername", site, "-connect", SERVED_HOST + ":443"],
                  data=b"", timeout=20)
    if not out:
        return None
    t = out.decode("utf-8", "replace")
    a, b = t.find("-----BEGIN CERTIFICATE-----"), t.find("-----END CERTIFICATE-----")
    if a < 0 or b < 0:
        return None
    return t[a:b + len("-----END CERTIFICATE-----")].encode() + b"\n"


def restart_web():
    if RESTART_CMD:
        cmd = RESTART_CMD.split()
    elif os.path.exists(os.path.join(LSWS, "bin", "lswsctrl")):
        cmd = [os.path.join(LSWS, "bin", "lswsctrl"), "restart"]
    else:
        cmd = ["systemctl", "restart", "lsws"]
    rc, _ = run(cmd, timeout=60)
    time.sleep(WAIT_S)
    return rc


# ---------------------------------------------------------------- judgement
IN_PLACE, INSTALL, NO_VHOST, NO_ACME, OLDER, NOT_FRESH, ACME_BAD, VH_BAD, STAGING, NAME, SHARED, HELD = (
    "in place", "install", "no vhost", "no acme pair", "acme not newer", "acme not fresh",
    "acme pair mismatched", "vhost pair mismatched", "acme staging", "acme misnamed",
    "vhost files shared", "held: failed before")
FAULTS = (ACME_BAD, VH_BAD, STAGING, NAME, SHARED, HELD)


def judge(site, now=None):
    r = {"site": site, "verdict": None, "file_days": None, "acme_days": None}
    keyf, certf = vhost_files(site)
    if not keyf or not certf or not os.path.isfile(keyf) or not os.path.isfile(certf):
        r["verdict"] = NO_VHOST
        return r
    r["keyf"], r["certf"] = keyf, certf
    ac, ak = acme_pair(site)
    if not ac:
        r["verdict"] = NO_ACME
        return r
    r["ac"], r["ak"] = ac, ak
    cur = cert_info(read(certf))
    new = cert_info(read(ac))
    if cur:
        r["file_days"] = days_left(cur["end"], now)
    if new:
        r["acme_days"] = days_left(new["end"], now)
    if not new:
        r["verdict"] = ACME_BAD                          # unreadable
        return r
    if cur and cur["fp"] == new["fp"]:
        r["verdict"] = IN_PLACE
        return r
    if cur and new["end"] <= cur["end"]:
        r["verdict"] = OLDER
        return r
    if days_left(new["end"], now) <= MIN_DAYS:
        r["verdict"] = NOT_FRESH
        return r
    if key_pub(read(ak)) != new["pub"]:                 # a fault only where it would otherwise be installed
        r["verdict"] = ACME_BAD
        return r
    if is_staging(new["issuer"]):
        r["verdict"] = STAGING
        return r
    if not name_matches(site, new["names"]):
        r["verdict"] = NAME
        return r
    if not cur or key_pub(read(keyf)) != cur["pub"]:
        r["verdict"] = VH_BAD                            # no proven fallback -> hands off
        return r
    r["verdict"] = INSTALL
    r["new_fp"] = new["fp"]
    return r


# ---------------------------------------------------------------- acting
def write_content(path, data, mode=None):
    """By content: a symlinked path keeps its link; the file's owner, group and mode are kept.
    Empty or missing bytes are refused BEFORE the file is opened (never truncate a key to nothing)."""
    if not data:
        raise ValueError("refusing to write empty bytes")
    with open(path, "wb") as fh:
        fh.write(data)
    if mode is not None:
        os.chmod(path, mode)


def backup(path, stamp):
    b = path + ".bak_S974_" + stamp
    if os.path.exists(b):
        if read(b) == read(path):
            return b                                     # the same bytes: the day's backup stands
        b = b + "_" + dt.datetime.now().strftime("%H%M%S")   # the files changed since: a backup of THESE bytes
    shutil.copyfile(path, b)                             # follows a link: the bytes
    os.chmod(b, 0o600)
    return b


ACTED = []                                               # [(site, keyf, certf, kbak, cbak, kmode, cmode)] for put-back


def putback(entries):
    bad = []
    for (site, keyf, certf, kb, cb, km, cm) in entries:
        try:
            write_content(keyf, read(kb), km)
            write_content(certf, read(cb), cm)
        except Exception:                                # noqa: BLE001
            bad.append(site)
    return bad


def on_signal(signum, _frame):
    if ACTED:
        putback(ACTED)
        restart_web()
    sys.exit(130)


def load_state():
    try:
        with open(STATE) as fh:
            d = json.load(fh)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)
    os.replace(tmp, STATE)


def served_is(site, certf, fp):
    """The read-back: up to TRIES looks, WAIT_S apart (a slow graceful restart is not put back by mistake)."""
    for i in range(max(1, TRIES)):
        got = cert_info(served_pem(site, certf))
        if got and got["fp"] == fp:
            return got
        if i + 1 < TRIES:
            time.sleep(WAIT_S)
    return None


def mark_shared(rows):
    """Two watched sites whose vhosts name the same real file: hands off both (one write would change the other)."""
    seen = {}
    for r in rows:
        for k in ("keyf", "certf"):
            if r.get(k):
                seen.setdefault(os.path.realpath(r[k]), []).append(r["site"])
    for r in rows:
        if r["verdict"] == INSTALL and any(len(seen.get(os.path.realpath(r[k]), [])) > 1 for k in ("keyf", "certf")):
            r["verdict"] = SHARED


def mark_held(rows, st):
    """A pair whose install failed before is not tried again until acme.sh has a different one (no nightly restart loop)."""
    held = st.get("held") or {}
    for r in rows:
        h = held.get(r["site"])
        if r["verdict"] == INSTALL and isinstance(h, dict) and h.get("fp") == r.get("new_fp") \
                and (r.get("file_days") is None or r["file_days"] > RETRY_DAYS):
            r["verdict"] = HELD                          # in the last fortnight it is tried again, once a night


def main(argv):
    try:
        return run_main(argv)
    except SystemExit:
        raise
    except Exception as ex:                              # noqa: BLE001 -- a crash must turn the health leg red
        if ACTED:                                        # a crash after a write: the sites acted on go back
            try:
                putback(ACTED)
                restart_web()
            except Exception:                            # noqa: BLE001
                pass
            del ACTED[:]
        if "--dry" not in argv:
            try:
                st = load_state()
                st["last_fail_iso"] = now_iso()
                st["last_fail"] = ["the job itself failed: %s" % type(ex).__name__]
                st.setdefault("last_success_iso", "")
                save_state(st)
            except Exception:                            # noqa: BLE001
                pass
        print("%s %s %s: !! the job itself failed: %s: %s" % (now_iso(), KIT, VERSION, type(ex).__name__, str(ex)[:160]))
        return 2


def run_main(argv):
    dry = "--dry" in argv
    stamp = dt.datetime.now().strftime("%Y%m%d")
    st0 = load_state()
    rows = [judge(s) for s in sites()]
    mark_shared(rows)
    mark_held(rows, st0)
    todo = [r for r in rows if r["verdict"] == INSTALL]
    faults = [r for r in rows if r["verdict"] in FAULTS]
    if dry:
        print("%s %s DRY -- the LOOK only; nothing written" % (KIT, VERSION))
        for r in rows:
            print("  %-26s %-22s file %s d . acme %s d" % (r["site"], r["verdict"],
                  r["file_days"] if r["file_days"] is not None else "-",
                  r["acme_days"] if r["acme_days"] is not None else "-"))
        print("  would install: %d . faults: %d" % (len(todo), len(faults)))
        return 0
    for sg in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sg, on_signal)
    installed, failed, put_back_bad = [], [], []
    for r in todo:
        keyf, certf = r["keyf"], r["certf"]
        km, cm = os.stat(keyf).st_mode & 0o777, os.stat(certf).st_mode & 0o777
        try:
            kb, cb = backup(keyf, stamp), backup(certf, stamp)
        except Exception:                                # noqa: BLE001
            r["verdict"] = "backup failed"
            failed.append(r)
            continue
        entry = (r["site"], keyf, certf, kb, cb, km, cm)
        ACTED.append(entry)
        try:
            write_content(keyf, read(r["ak"]), km)
            write_content(certf, read(r["ac"]), cm)
            if key_pub(read(keyf)) != (cert_info(read(certf)) or {}).get("pub"):
                raise ValueError("written pair does not match")
        except Exception:                                # noqa: BLE001
            put_back_bad += putback([entry])
            ACTED.remove(entry)
            r["verdict"] = "write failed, put back"
            failed.append(r)
    if ACTED:
        restart_web()
        retry = []
        for entry in list(ACTED):
            site, keyf, certf = entry[0], entry[1], entry[2]
            r = [x for x in todo if x["site"] == site][0]
            got = served_is(site, certf, r["new_fp"])
            if got:
                r["verdict"] = "installed"
                r["file_days"] = days_left(got["end"])
                installed.append(r)
            else:
                retry.append(entry)
        if retry:
            put_back_bad += putback(retry)
            restart_web()
            for entry in retry:
                r = [x for x in todo if x["site"] == entry[0]][0]
                old = cert_info(read(entry[4]))
                back = served_is(entry[0], entry[2], old["fp"]) if old else None
                r["verdict"] = "not served, put back" if back else "not served, put back NOT SERVED"
                r["failed_fp"] = r["new_fp"]
                failed.append(r)
        del ACTED[:]
    st = st0
    st["kit"], st["version"] = KIT, VERSION
    held = st.get("held") or {}
    for r in failed:
        if r.get("failed_fp"):
            held[r["site"]] = {"fp": r["failed_fp"], "since": now_iso()}
    for r in rows:
        if r["verdict"] in (IN_PLACE, "installed") and r["site"] in held:
            del held[r["site"]]
    st["held"] = held
    st.setdefault("last_success_iso", "")
    st["last_run_iso"] = now_iso()
    st["sites"] = [{"site": r["site"], "verdict": r["verdict"], "file_days": r["file_days"],
                    "acme_days": r["acme_days"]} for r in rows]
    if installed:
        st["last_install_iso"] = now_iso()
        st["last_installed"] = [r["site"] for r in installed]
    bad = failed + faults
    if bad or put_back_bad:
        st["last_fail_iso"] = now_iso()
        st["last_fail"] = ["%s: %s" % (r["site"], r["verdict"]) for r in bad] + \
                          ["%s: PUT BACK FAILED -- restore its .bak_S974_%s by hand" % (s, stamp) for s in put_back_bad]
    else:
        st["last_success_iso"] = now_iso()
    save_state(st)
    line = "%s %s %s: %d sites . in place %d . installed %d . failed %d . faults %d" % (
        now_iso(), KIT, VERSION, len(rows), sum(1 for r in rows if r["verdict"] == IN_PLACE),
        len(installed), len(failed), len(faults))
    print(line)
    for r in installed:
        print("  INSTALLED %s: serves %d days" % (r["site"], r["file_days"]))
    for r in bad:
        print("  !! %s: %s" % (r["site"], r["verdict"]))
    for s in put_back_bad:
        print("  !!!! %s: PUT BACK FAILED -- restore its .bak_S974_%s by hand" % (s, stamp))
    return 1 if (bad or put_back_bad) else 0


# ---------------------------------------------------------------- selftest (pure parts)
def selftest():
    ok = [0, 0]

    def ck(name, got, want):
        ok[0 if got == want else 1] += 1
        if got != want:
            print("  FAIL %s: %r != %r" % (name, got, want))
    ck("exact name", name_matches("followup.dr-manoj.in", ["followup.dr-manoj.in"]), True)
    ck("wildcard one label", name_matches("followup.dr-manoj.in", ["*.dr-manoj.in"]), True)
    ck("wildcard not two labels", name_matches("a.b.dr-manoj.in", ["*.dr-manoj.in"]), False)
    ck("wildcard not bare", name_matches("dr-manoj.in", ["*.dr-manoj.in"]), False)
    ck("other name", name_matches("rx.dr-manoj.in", ["fit.dr-manoj.in"]), False)
    ck("staging", is_staging("C = US, O = (STAGING) Let's Encrypt, CN = (STAGING) Ersatz Edamame E1"), True)
    ck("real issuer", is_staging("C = US, O = Let's Encrypt, CN = E6"), False)
    ck("days", days_left(86400 * 10 + 5, 0), 10)
    d = tempfile.mkdtemp()
    try:
        k = os.path.join(d, "k.pem")
        c = os.path.join(d, "c.pem")
        rc, _ = run([OPENSSL, "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256", "-nodes",
                     "-keyout", k, "-out", c, "-days", "40", "-subj", "/CN=t.example",
                     "-addext", "subjectAltName=DNS:t.example"])
        ck("openssl made a test pair", rc, 0)
        i = cert_info(read(c))
        ck("cert read", bool(i), True)
        ck("names read", (i or {}).get("names"), ["t.example"])
        ck("days ~40", days_left((i or {}).get("end", 0)) in (39, 40), True)
        ck("key matches", key_pub(read(k)) == (i or {}).get("pub"), True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("selftest: %d pass, %d fail" % (ok[0], ok[1]))
    return 0 if ok[1] == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
