#!/usr/bin/env python3
"""obd_test.py - ONE-SHOT OBD test call. Prints NO secrets.

Two modes:
  python obd_test.py 9389559274
        -> User Dialer (type 1): rings the agent in MYOP_OBD_TEST_USER_ID,
           then dials the patient number.
  python obd_test.py 9389559274 9358XXXXXX
        -> Anonymous Dialer (type 1): rings AGENT MOBILE (2nd number) then
           the patient number. No user_id used. Use this to prove the
           campaign places real calls without depending on a user id.

Numbers are sent in E.164 (+91XXXXXXXXXX). Reads /root/wa/.env:
MYOP_OBD_SECRET, MYOP_OBD_XAPIKEY, MYOP_PUBLIC_IVR_ID, MYOP_OBD_TEST_USER_ID."""
import os, re, sys, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env(os.path.join(HERE, ".env"))

COMPANY_ID = "68384350414b9847"
SECRET     = os.environ.get("MYOP_OBD_SECRET", "").strip()
XAPIKEY    = os.environ.get("MYOP_OBD_XAPIKEY", "").strip()
IVR_ID     = os.environ.get("MYOP_PUBLIC_IVR_ID", "").strip()
USER_ID    = os.environ.get("MYOP_OBD_TEST_USER_ID", "6838435041f29988").strip()
URL        = "https://obd-api.myoperator.co/obd-api-v1"


def e164(s):
    ten = re.sub(r"\D", "", str(s or ""))[-10:]
    return "+91" + ten, ten


def main():
    miss = [k for k, v in {"MYOP_OBD_SECRET": SECRET, "MYOP_OBD_XAPIKEY": XAPIKEY,
                           "MYOP_PUBLIC_IVR_ID": IVR_ID}.items() if not v]
    if miss:
        print("MISSING in .env:", ", ".join(miss)); sys.exit(2)
    if len(sys.argv) < 2:
        print("Usage: python obd_test.py <patient10> [agentmobile10]"); sys.exit(2)

    patient, pten = e164(sys.argv[1])
    if len(pten) != 10:
        print("Patient number must be 10 digits."); sys.exit(2)

    body = {
        "company_id": COMPANY_ID,
        "secret_token": SECRET,
        "type": "1",
        "number": patient,
        "public_ivr_id": IVR_ID,
        "reference_id": "obdtest-" + str(int(time.time())),
        "max_call_duration": 300,
        "call_hold": True,
    }

    if len(sys.argv) >= 3:
        agent, aten = e164(sys.argv[2])
        if len(aten) != 10:
            print("Agent mobile must be 10 digits."); sys.exit(2)
        body["number_2"] = agent
        print("MODE: Anonymous Dialer  | agent +91XXXXXX%s rings, then %s"
              % (aten[-4:], patient))
    else:
        body["user_id"] = USER_ID
        print("MODE: User Dialer       | user_id ...%s rings, then %s"
              % (USER_ID[-4:], patient))

    req = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("x-api-key", XAPIKEY)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("HTTP", r.status); print(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code); print(e.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print("ERROR:", e)


if __name__ == "__main__":
    main()
