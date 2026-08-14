#!/root/wa/venv/bin/python3
"""
waba_diag.py — WABA pipeline health check + escalation report (S177, F-82 aftermath).

One command answers: is WhatsApp sending healthy RIGHT NOW, from THIS server,
through the REAL live code path (waba.py + installed .env token)?

Usage:
    /root/wa/venv/bin/python3 /root/wa/waba_diag.py            # 2 trials (default)
    /root/wa/venv/bin/python3 /root/wa/waba_diag.py --trials 5 # deeper check
    /root/wa/venv/bin/python3 /root/wa/waba_diag.py --dry      # config check only, no sends

Each successful trial delivers a REAL WhatsApp to the test number.
Secrets are never printed (token shown as length + last-4 only).

Exit codes: 0 healthy · 1 degraded/down (escalation pack printed) · 2 config error.
"""
import sys, time, json, argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/root/wa")
import waba

TEST_NUM = "7042780781"           # Lokesh (MyOperator engineer) — agreed test number
TEST_TPL = "drmanoj_post_visit"
TEST_VAR = ["Lokesh"]
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--dry", action="store_true", help="config check only, no sends")
    args = ap.parse_args()

    print("=" * 66)
    print("WABA DIAGNOSTIC  ·", now_ist())
    print("=" * 66)

    # ── 1. Config check ──────────────────────────────────────────────
    tok = waba.AUTH_TOKEN or ""
    print("endpoint        :", waba.BASE_URL + waba.SEND_PATH)
    print("company_id      :", waba.COMPANY_ID or "(MISSING)")
    print("phone_number_id :", waba.PHONE_NUMBER_ID or "(MISSING)")
    print("token           : len=%d last4=%s" % (len(tok), tok[-4:] if tok else "----"))
    print("body format     :", waba.BODY_FORMAT)
    try:
        waba.check_config()
        print("config          : OK")
    except Exception as e:
        print("config          : FAIL ->", e)
        print("\nVERDICT: CONFIG ERROR — fix .env before anything else.")
        return 2

    if args.dry:
        print("\n(dry run — no sends performed)")
        return 0

    # ── 2. Live trials through the REAL code path ────────────────────
    print("-" * 66)
    print("trials          : %d  (template=%s -> %s, real messages)"
          % (args.trials, TEST_TPL, TEST_NUM))
    rows = []
    for i in range(args.trials):
        t0 = time.time()
        try:
            r = waba.send_template(TEST_NUM, TEST_TPL, TEST_VAR)
            ms = int((time.time() - t0) * 1000)
            rows.append({"t": now_ist(), "ok": r["ok"], "status": r["status_code"],
                         "code": r["code"], "ms": ms,
                         "msg_id": (r.get("message_id") or "")[:8],
                         "raw": (r.get("raw") or "")[:120]})
        except waba.WabaFatalError as e:
            rows.append({"t": now_ist(), "ok": False, "status": "FATAL",
                         "code": e.code, "ms": int((time.time() - t0) * 1000),
                         "msg_id": "", "raw": str(e)})
            break                                   # fatal = stop immediately
        except Exception as e:
            rows.append({"t": now_ist(), "ok": False, "status": "EXC",
                         "code": type(e).__name__, "ms": int((time.time() - t0) * 1000),
                         "msg_id": "", "raw": str(e)[:120]})
        if i < args.trials - 1:
            time.sleep(2)

    for r in rows:
        print("  %(t)s  ok=%(ok)-5s status=%(status)-5s code=%(code)-10s "
              "%(ms)5dms  msg_id=%(msg_id)s" % r)

    ok_n = sum(1 for r in rows if r["ok"])
    n = len(rows)
    print("-" * 66)

    # ── 3. Verdict ───────────────────────────────────────────────────
    if ok_n == n:
        print("VERDICT: HEALTHY — %d/%d sends accepted. No action needed." % (ok_n, n))
        return 0

    fatal = next((r for r in rows if r["status"] == "FATAL"), None)
    if fatal:
        print("VERDICT: FATAL CONDITION — %s (%s)."
              % (fatal["code"], waba.FATAL_CODES.get(fatal["code"], "?")))
        print("ACTION : this is account-level (wallet/WABA/number). "
              "Fix in MyOperator panel or contact account manager (Khushi).")
    elif ok_n == 0:
        print("VERDICT: DOWN — 0/%d accepted." % n)
    else:
        print("VERDICT: DEGRADED — %d/%d accepted (intermittent)." % (ok_n, n))

    # ── 4. Escalation pack ───────────────────────────────────────────
    print()
    print("──── ESCALATION PACK (copy everything below to MyOperator) ────")
    print("From      : Advanced Orthopaedic Surgery Centre (Dr. Manoj Agarwal)")
    print("Server IP : 93.127.195.49  (all requests originate here)")
    print("When      :", now_ist())
    print("Endpoint  : POST", waba.BASE_URL + waba.SEND_PATH)
    print("Company ID:", waba.COMPANY_ID)
    print("PhoneNumID:", waba.PHONE_NUMBER_ID)
    print("Template  :", TEST_TPL, "(approved), language=en, numbered body vars")
    print("Auth      : Bearer token ending ...%s (the WhatsApp-APIs Authentication token)"
          % (tok[-4:] if tok else "----"))
    print("Results   : %d/%d requests accepted; failures below:" % (ok_n, n))
    for r in rows:
        if not r["ok"]:
            print("   - %(t)s  HTTP %(status)s  code=%(code)s  body=%(raw)s" % r)
    print("Payload shape (working reference, tested in Postman by MyOperator team):")
    print(json.dumps(waba.build_payload("XXXXXXXXXX", TEST_TPL, ["<name>"]), indent=2))
    print("Request   : please check gateway/service logs for the above timestamps")
    print("            and confirm root cause; identical requests succeed at other")
    print("            times, so this appears to be intermittent on the API side.")
    print("───────────────────────── END PACK ───────────────────────────")
    return 1

if __name__ == "__main__":
    sys.exit(main())
