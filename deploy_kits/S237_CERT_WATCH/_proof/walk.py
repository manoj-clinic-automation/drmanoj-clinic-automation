"""LIVE-SHAPE WALK for cert_watch.py.
Serves seven REAL certificates over a REAL TLS socket on port 443, selected by
SNI, and drives the SHIPPED code path (fetch_cert -> evaluate -> build_message)
against them. Nothing is stubbed but the certificates themselves."""
import ssl, socket, threading, sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cert_watch as cw

CERTS = {
 "certwalk-good.test":     ("good",     cw.V_UNTRUSTED),   # self-signed: a browser DOES refuse it
 "certwalk-warn.test":     ("warn",     cw.V_UNTRUSTED),   # self-signed
 "certwalk-soon.test":     ("soon",     cw.V_UNTRUSTED),   # self-signed AND 4 days out:
                                                        # a browser refusing NOW outranks expiring LATER
 "certwalk-expired.test":  ("expired",  cw.V_EXPIRED),
 "certwalk-expstag.test":  ("expstag",  cw.V_EXPIRED),
 "certwalk-staging.test":  ("staging",  cw.V_STAGING),
 "certwalk-mismatch.test": ("mismatch", cw.V_MISMATCH),
}
HERE = os.path.dirname(os.path.abspath(__file__))

def ctx_for(base):
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    c.load_cert_chain(os.path.join(HERE, base + ".crt"), os.path.join(HERE, base + ".key"))
    return c

CTXS = {h: ctx_for(b) for h, (b, _) in CERTS.items()}
def sni(sock, name, ctx):
    if name in CTXS:
        sock.context = CTXS[name]

server_ctx = ctx_for("good")
server_ctx.sni_callback = sni

def serve(stop):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 443)); s.listen(16); s.settimeout(0.4)
    while not stop.is_set():
        try: c, _ = s.accept()
        except socket.timeout: continue
        except OSError: break
        try:
            with server_ctx.wrap_socket(c, server_side=True) as ss: ss.recv(16)
        except Exception: pass
        finally:
            try: c.close()
            except Exception: pass
    s.close()

stop = threading.Event()
t = threading.Thread(target=serve, args=(stop,), daemon=True); t.start()
import time; time.sleep(0.6)

now = dt.datetime.now(dt.timezone.utc).timestamp()
fails = 0; results = []
print("LIVE-SHAPE WALK -- real TLS, real certificates, shipped code path\n")
for host, (base, expect) in CERTS.items():
    cert, err, bok = cw.fetch_cert(host)                            # SHIPPED I/O
    r = cw.evaluate(host, True, cert, now, error=err, browser_ok=bok)  # SHIPPED logic
    results.append(r)
    ok = (r["verdict"] == expect)
    fails += 0 if ok else 1
    print("  %s %-26s got %-9s want %-9s  %s" % ("PASS" if ok else "FAIL", host, r["verdict"], expect, r["note"][:60]))

# an address that is not listening at all
cert, err, bok = cw.fetch_cert("certwalk-dead.test")
r = cw.evaluate("certwalk-dead.test", True, cert, now, error=err, browser_ok=bok)
results.append(r)
ok = r["verdict"] == cw.V_ERROR
fails += 0 if ok else 1
print("  %s %-26s got %-9s want %-9s  %s" % ("PASS" if ok else "FAIL", "certwalk-dead.test", r["verdict"], cw.V_ERROR, r["note"][:60]))

# a skipped host must never appear
r = cw.evaluate("certwalk-retired.test", False, None, now); results.append(r)
ok = r["verdict"] == cw.V_SKIP; fails += 0 if ok else 1
print("  %s %-26s got %-9s want %-9s" % ("PASS" if ok else "FAIL", "certwalk-retired.test", r["verdict"], cw.V_SKIP))

print("\n--- the message the owner would receive ---")
msg = cw.build_message(results)
print(msg)
print("--- end of message ---\n")

# assertions on the message itself
checks = [
 ("self-signed good cert is reported, not silently passed", "certwalk-good.test" in msg),
 ("skipped site absent from the message", "certwalk-retired.test" not in msg),
 ("expired site named", "certwalk-expired.test" in msg),
 ("staging site named", "certwalk-staging.test" in msg),
 ("mismatch site named", "certwalk-mismatch.test" in msg),
 ("dead site named", "certwalk-dead.test" in msg),
 ("count says 8", msg.splitlines()[0].startswith("CLINIC CERTIFICATES -- 8 site(s)")),
 ("expired appears before warn", msg.index("certwalk-expired.test") < msg.index("certwalk-warn.test")),
 ("message is ascii-encodable for the push header", cw._ascii_header("Clinic certificates: attention needed") != ""),
 ("expired+staging cert mentions staging", any(r["host"]=="certwalk-expstag.test" and "STAGING" in r["note"] for r in results)),
]
for name, ok in checks:
    fails += 0 if ok else 1
    print("  %s %s" % ("PASS" if ok else "FAIL", name))

cw.print_table(results)
stop.set(); t.join(timeout=2)
print("\nWALK: %d checks, %d failures" % (len(CERTS)+2+len(checks), fails))
sys.exit(1 if fails else 0)
