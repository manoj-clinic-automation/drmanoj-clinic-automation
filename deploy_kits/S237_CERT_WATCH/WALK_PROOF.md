# S237_CERT_WATCH — the live-shape walk, and what it caught

**Run 10-Sep-2026 in the assistant's container.** Seven real certificates, generated for the walk,
served over a real TLS socket on port 443 and selected by SNI, then read by the **shipped** code
path — `fetch_cert()` → `evaluate()` → `build_message()`. Nothing is stubbed but the certificates.

## ⚠ WHAT THE WALK CAUGHT, BEHIND 50 GREEN CHECKS

The first version connected once, with verification deliberately off, so that it could see a bad
certificate rather than have the handshake refuse it. It passed **50 of 50** unit checks.

**It was wrong about all seven live sites.** `ssl.getpeercert()` returns an **empty dict** on an
unverified connection — Python only fills it in when it has actually validated the chain. Every
site would have come back `ERROR: no certificate returned`, for ever: a watchman crying wolf on
the whole estate, which is worse than no watchman at all.

**The repair became a better design than the original.** Two passes:

1. connect exactly as a browser does, fully verified — if that succeeds, a browser accepts the site,
   which is the strongest statement available and the one the owner actually cares about;
2. only on refusal, reconnect with verification off and read the raw certificate, to say *why*.

A new verdict, **UNTRUSTED**, catches any browser refusal the three named causes do not explain, so
a broken site can never fall through to OK.

## THE WALK OUTPUT

*Re-run 10-Sep-2026 after the thresholds were retuned to CyberPanel's measured 15-day
renewal window. `_proof/walk.py` now mints its own fixture certificates and adds its own
hosts entries, so the proof is reproducible from the kit alone.*

```
minted 7 fixture certificates

LIVE-SHAPE WALK -- real TLS, real certificates, shipped code path

  PASS certwalk-good.test         got UNTRUSTED want UNTRUSTED  a browser refuses this site -- self-signed certificate
  PASS certwalk-warn.test         got UNTRUSTED want UNTRUSTED  a browser refuses this site -- self-signed certificate
  PASS certwalk-soon.test         got UNTRUSTED want UNTRUSTED  a browser refuses this site -- self-signed certificate
  PASS certwalk-expired.test      got EXPIRED   want EXPIRED    EXPIRED 4 days ago -- browsers are refusing this site now
  PASS certwalk-expstag.test      got EXPIRED   want EXPIRED    EXPIRED 4 days ago -- browsers are refusing this site now (a
  PASS certwalk-staging.test      got STAGING   want STAGING    issued by the Let's Encrypt STAGING CA -- every browser reje
  PASS certwalk-mismatch.test     got MISMATCH  want MISMATCH   certificate does not cover this name (it covers somebody-els
  PASS certwalk-dead.test         got ERROR     want ERROR      gaierror: [Errno -2] Name or service not known
  PASS certwalk-retired.test      got SKIP      want SKIP     

--- the message the owner would receive ---
CLINIC CERTIFICATES -- 8 site(s) need attention.

* certwalk-dead.test -- ERROR
   gaierror: [Errno -2] Name or service not known

* certwalk-expired.test -- EXPIRED
   EXPIRED 4 days ago -- browsers are refusing this site now
   expires 07-Sep-2026 07:59 IST, issued by certwalk-expired.test

* certwalk-expstag.test -- EXPIRED
   EXPIRED 4 days ago -- browsers are refusing this site now (and it is a STAGING certificate)
   expires 07-Sep-2026 07:59 IST, issued by certwalk-expstag.test

* certwalk-staging.test -- STAGING
   issued by the Let's Encrypt STAGING CA -- every browser rejects it
   expires 08-Dec-2026 07:59 IST, issued by certwalk-staging.test

* certwalk-mismatch.test -- MISMATCH
   certificate does not cover this name (it covers somebody-else.test)
   expires 08-Dec-2026 07:59 IST, issued by somebody-else.test

* certwalk-good.test -- UNTRUSTED
   a browser refuses this site -- self-signed certificate
   expires 08-Dec-2026 07:59 IST, issued by certwalk-good.test

* certwalk-soon.test -- UNTRUSTED
   a browser refuses this site -- self-signed certificate
   expires 14-Sep-2026 07:59 IST, issued by certwalk-soon.test

* certwalk-warn.test -- UNTRUSTED
   a browser refuses this site -- self-signed certificate
   expires 30-Sep-2026 07:59 IST, issued by certwalk-warn.test

Checked by opening each site the way a browser does.
Nothing was changed. Time: 2026-09-10 07:59:21 IST
--- end of message ---

  PASS self-signed good cert is reported, not silently passed
  PASS skipped site absent from the message
  PASS expired site named
  PASS staging site named
  PASS mismatch site named
  PASS dead site named
  PASS count says 8
  PASS expired appears before warn
  PASS message is ascii-encodable for the push header
  PASS expired+staging cert mentions staging
=== Clinic certificates -- 2026-09-10 07:59:21 IST ===
  !!  certwalk-good.test         UNTRUSTED   88 d  a browser refuses this site -- self-signed certificate
  !!  certwalk-warn.test         UNTRUSTED   19 d  a browser refuses this site -- self-signed certificate
  !!  certwalk-soon.test         UNTRUSTED    3 d  a browser refuses this site -- self-signed certificate
  !!  certwalk-expired.test      EXPIRED     -4 d  EXPIRED 4 days ago -- browsers are refusing this site now
  !!  certwalk-expstag.test      EXPIRED     -4 d  EXPIRED 4 days ago -- browsers are refusing this site now (and it is a STAGING certificate)
  !!  certwalk-staging.test      STAGING     88 d  issued by the Let's Encrypt STAGING CA -- every browser rejects it
  !!  certwalk-mismatch.test     MISMATCH    88 d  certificate does not cover this name (it covers somebody-else.test)
  !!  certwalk-dead.test         ERROR             gaierror: [Errno -2] Name or service not known
  --  certwalk-retired.test      SKIP              not watched on purpose
---

WALK: 19 checks, 0 failures
```

---
*Reproduce with `_proof/walk.py` (needs `cryptography`, port 443 free, and permission to write
`/etc/hosts`). The shipped `cert_watch.py` needs none of that.*
