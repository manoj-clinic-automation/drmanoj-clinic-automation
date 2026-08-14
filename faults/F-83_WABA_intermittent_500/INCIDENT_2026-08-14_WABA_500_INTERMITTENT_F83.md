# INCIDENT — 2026-08-14 — WABA `/chat/messages` INTERMITTENT HTTP 500 (F-83; resolves the F-82 mystery)

**System:** MyOperator WhatsApp Business API (Company 68384350414b9847 · Phone-Number-ID 1090067637530949 · number 9358008080)
**Detected:** 14 Aug 2026 · **Status at close:** OPEN vendor-side, escalated with evidence · **Severity:** blocks WABA go-live only (manual workflow unaffected; no patient impact)

## Summary
The long-running "persistent HTTP 500" that has blocked WABA go-live (F-82) is proven to be
**vendor-side intermittency**: the identical request (same server IP, same token, same payload)
succeeds and fails purely depending on the time window. During failures the gateway returns
HTTP 500 with body `{"message":null}` — stripping its own CHAT_xxxx error codes, which made the
fault look like a client-side mystery for weeks.

## Evidence timeline (all from VPS 93.127.195.49, token …wWHn, payload identical throughout)
| Time (IST) | Event | Result |
|---|---|---|
| 16:37 | Vendor's own Postman test (Khushi) | SUCCESS |
| 16:55–17:30 | Single-shot tests (curl / urllib / http.client) | MIXED — seeded three false theories |
| ~19:15 | Certainty harness: 3 transports × 3 trials incl. UNCHANGED original code | **9/9 SUCCESS** |
| 19:49:08, 19:49:13 | waba_diag run 1 | FAIL 500 `{"message":null}` |
| 20:05:32, 20:05:37 | waba_diag run 2 | FAIL 500 |
| ~20:12 | Send to a DIFFERENT recipient (owner's number) | FAIL 500 — rules out per-recipient throttle |
| 20:34:30, 20:34:35 | waba_diag run 3 | FAIL 500 — ≥45 min continuous |
| ~20:30 | Owner panel check | wallet OK · template active · number quality HIGH · service live |

## Root cause
Vendor-side (MyOperator API gateway or a backend behind it). Client side fully exonerated:
payload shape matches the vendor's own working example key-for-key; token byte-identical to the
one their team tested (heredoc file compare, md5 `55c131c5…` both sides); all account indicators
green while the API fails. Contributing vendor defect: null error body in the failure mode.

## What was ruled out (and how)
- Stale/corrupted token → byte-compare identical (an initial shell-paste compare was itself
  corrupted — F-84 — and discarded).
- Payload shape → live debug dump matched the vendor Postman body key-for-key.
- urllib header case-mangling / User-Agent → 9/9 harness success on the untouched original code.
- Per-recipient throttling (≈15 tests to one number) → different recipient also failed.
- Wallet / template / number quality / service state → owner-verified green in panel.

## Fixes shipped (client side)
1. `waba.py` retry-on-5xx with backoff (`031b4642…` live) — rides out short blips; fatal codes
   still stop batches instantly.
2. `waba_diag.py` (new, `b560d12d…`) — one-command health check producing a forwardable
   escalation pack; standing SOP D314.

## Escalation
Evidence email (timeline + cross-recipient proof + panel-vs-API contradiction + request for
gateway logs 19:49–20:35 IST + the null-error-body defect) sent from owner's personal email to
Khushi (account manager), CC Lokesh (engineer). Ball is vendor-side with timestamps.

## Prevention / follow-ups
- D313: repeated-trials rule before any code change blamed on a vendor API.
- Morning `waba_diag.py` run until stable; forward fresh packs while DOWN.
- Rotate the (now chat-exposed) token WITH Lokesh once sends are stable.
- Ask vendor to return proper CHAT_xxxx codes in this failure mode.

**END OF INCIDENT RECORD.**
