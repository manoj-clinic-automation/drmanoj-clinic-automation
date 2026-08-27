#!/usr/bin/env python3
"""
af1_proof.py  --  S205 · AF-1 / F-206 · THE DECISION TABLE, PROVEN

WHAT AF-1 IS
------------
`SEND_TO_CLINIC.bat` on the medical PC decides whether a report reached the
clinic server by reading a RESPONSE FILE, and it never looks at the HTTP code.

    line 133   set "RESP=%HERE%last_response.txt"
    line 134   curl -s -m 90 -o "%RESP%" -w "%%{http_code}" ... > last_http.txt
    line 136   set /p HTTP=<"%HERE%last_http.txt"
    line 138   findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%"
    line 139   if not errorlevel 1  ->  ACCEPTED
    line 142                        ->  echo %HASH%>> "%HASHES%"     <-- FOR EVER

NEITHER FILE IS CLEARED BEFORE curl RUNS. So when a request fails without
producing a body, `last_response.txt` still holds the PREVIOUS run's body. If
that previous run was accepted, the failed send reads as ACCEPTED, and line 142
writes the report's md5 into `sent_hashes.txt` -- which line 123 then uses to
SKIP that report for ever. A send that did not happen becomes a report that can
never be sent again.

TWO STALE FILES, NOT ONE
------------------------
The record describes `%RESP%`. `last_http.txt` has exactly the same problem, and
it is worse in one way: `:one` is called in a LOOP over the Marg user folders,
so within a SINGLE run report #2 can inherit report #1's HTTP code. Found by
reading the file rather than the record (A0).

WHY THIS FILE EXISTS
--------------------
A Windows batch cannot be executed here. So this proves the PREDICATE -- the
decision table both versions implement -- exactly as f195_proof.py did for the
gate. The verdict functions below are transcriptions of the two batch decision
paths, and the point of the exercise is that ONE ROW of the table differs, and
that row is the one that loses a report permanently.

    python3 af1_proof.py
"""
import sys

ACC = "ACCEPTED-FOR-REVIEW"
ALR = "ALREADY-RECEIVED"


def verdict_v3(http, body_file):
    """SEND_TO_CLINIC.bat v3, lines 138-158, as it stands on the medical PC.

    `http` is read but NEVER consulted by the two accepting branches. The
    decision is made entirely from the text sitting in the response file --
    whoever put it there, and whenever.
    """
    if ACC in body_file:
        return "ACCEPTED", True          # True = md5 written to sent_hashes
    if ALR in body_file:
        return "ALREADY", True
    return "REFUSED", False


def verdict_v4(http, body_file, cleared):
    """The fix. Three changes, and the third is the one that matters.

      1. both response files are DELETED before curl runs, so a stale body
         cannot be read as this run's answer;
      2. an accepting branch must see HTTP 200 *and* the affirmative body --
         either alone is not evidence;
      3. the md5 is written to sent_hashes.txt ONLY on a proven accept. That
         file is the blacklist, and it is the only irreversible thing this
         script does.
    """
    if not cleared:
        raise AssertionError("v4 always clears before curl")
    if http == "200" and ACC in body_file:
        return "ACCEPTED", True
    if http == "200" and ALR in body_file:
        return "ALREADY", True
    return "REFUSED", False


CASES = [
    # name, http, what is IN the response file when findstr reads it
    ("a real accept",
     "200", ACC, "ACCEPTED"),
    ("the server already had it",
     "200", ALR, "ALREADY"),
    ("a stale token -- 401",
     "401", '{"error":"not_signed_in"}', "REFUSED"),
    ("the server is unwell -- 503",
     "503", '{"error":"not_configured"}', "REFUSED"),
    ("a bad payload -- 400",
     "400", '{"error":"bad_payload"}', "REFUSED"),
    # ---- THE ONE THAT MATTERS -------------------------------------------
    ("NO NETWORK: curl writes no body, so the file still holds YESTERDAY'S "
     "accept",
     "000", ACC, "REFUSED"),
    ("NO NETWORK after an ALREADY-RECEIVED run",
     "000", ALR, "REFUSED"),
    ("timeout mid-transfer, previous body still on disk",
     "000", ACC, "REFUSED"),
]


def main():
    print("=" * 78)
    print("  AF-1 / F-206 -- the decision table both versions implement")
    print("=" * 78)
    print()
    print("%-56s %-6s %-10s %-10s" % ("case", "http", "v3 says", "v4 says"))
    print("-" * 88)
    wrong_v3, wrong_v4 = [], []
    for name, http, body, want in CASES:
        v3, v3_blacklists = verdict_v3(http, body)
        v4, v4_blacklists = verdict_v4(http, body, cleared=True)
        mark3 = "" if v3 == want else "  <-- WRONG"
        mark4 = "" if v4 == want else "  <-- WRONG"
        if v3 != want:
            wrong_v3.append((name, v3, want, v3_blacklists))
        if v4 != want:
            wrong_v4.append((name, v4, want, v4_blacklists))
        short = name if len(name) <= 54 else name[:51] + "..."
        print("%-56s %-6s %-10s %-10s%s%s"
              % (short, http, v3, v4, mark3, mark4))
    print()
    print("  correct rows:   v3 %d/%d      v4 %d/%d"
          % (len(CASES) - len(wrong_v3), len(CASES),
             len(CASES) - len(wrong_v4), len(CASES)))
    print()

    print("=" * 78)
    print("  WHAT v3 GETS WRONG, AND WHAT IT COSTS")
    print("=" * 78)
    for name, got, want, blacklists in wrong_v3:
        print("  * %s" % name)
        print("      v3 says %s, the truth is %s" % (got, want))
        if blacklists:
            print("      AND it appends the report's md5 to sent_hashes.txt.")
            print("      That file is the blacklist. The report is now SKIPPED")
            print("      for ever -- a send that never happened has made the")
            print("      report unsendable.")
        print()

    ok = (not wrong_v4) and bool(wrong_v3)
    print("=" * 78)
    if ok:
        print("  PROVEN: v3 false-accepts on every no-body failure and")
        print("  blacklists the report; v4 is correct on all %d rows." % len(CASES))
        print()
        print("  SCOPE, SAID OUT LOUD: this proves the DECISION TABLE. A Windows")
        print("  batch cannot be executed here, so the clearing of the two")
        print("  response files and the curl invocation itself are proven by")
        print("  construction and by reading, NOT by running. The first real run")
        print("  on the medical PC is the measurement -- and it is safe, because")
        print("  the failure mode being fixed only bites when a send FAILS.")
    else:
        print("  PROOF INCOMPLETE.")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
