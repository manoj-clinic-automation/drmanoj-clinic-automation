#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_sign.py  --  S655.  For a Claude session on manojz, NOT for the lab PC. (reception_sign.py S448, for the lab road.)

Signs a job so the LAB agent will accept it through the clinic Drive or the server.
Needs lab_agent.py beside it (the Ed25519 code lives there) and nothing
else -- no third-party package.

    python lab_sign.py keygen  <secret-file>
        makes a new 32-byte secret, prints the PUBLIC key (64 hex). The public
        key is what goes into C:\\ClinicAgent\\authorized_keys.txt. The secret
        file stays on the owner's PC (D:\\Downloads\\margsync\\_config\\) and is
        never put on Drive, in the repository or in chat.

    python lab_sign.py sign  <secret-file>  <job-file>
        writes a copy of the job named  <signing time, IST>_<job-file>  and
        its .sig beside it. Put BOTH into
        My Drive\\Clinic Data Archive\\ToLab\\jobs\\  within 48 hours.
        The name is part of what is signed and is used once: a refused or
        finished name is never read again, and a job signed more than 48
        hours ago is refused.
        THE SECOND DOOR (S453): the same two files can instead be posted to
        the clinic server, /finance/api/lab/jobs/submit, as JSON
        {"name", "job" (base64 of the stamped file), "sig"} -- for the day
        Google Drive is what is broken on that PC.

    python lab_sign.py list-token  <secret-file>
        prints {"ts","sig"} for /finance/api/lab/snap/list -- what snapshots the
        server holds (names, sizes, dates; never the bytes). Good for 15 minutes.

    python lab_sign.py read-token  <secret-file>  <stamped job name>
        prints one line of JSON {"name", "ts", "sig"}: what the server's
        /finance/api/lab/jobs/read asks for before it shows that job's
        state and output. Good for 15 minutes.
"""
import datetime as dt
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "labpc"))   # the kit's layout
sys.path.insert(0, _HERE)                                            # or a copy beside this file
import lab_agent as ra                                   # noqa: E402

READ_CONTEXT = b"clinic-lab-job-read-v1\n"   # the server's lab_door.py builds the same bytes
LIST_CONTEXT = b"clinic-lab-snap-list-v1\n"


def main(argv):
    if len(argv) == 3 and argv[1] == "keygen":
        if os.path.exists(argv[2]):
            print("refusing to overwrite %s" % argv[2])
            return 2
        secret = os.urandom(32)
        with open(argv[2], "w", encoding="ascii") as fh:
            fh.write(secret.hex() + "\n")
        print(ra.ed_public(secret).hex())
        return 0
    if len(argv) == 4 and argv[1] == "sign":
        with open(argv[2], "r", encoding="ascii") as fh:
            secret = bytes.fromhex(fh.read().strip())
        with open(argv[3], "rb") as fh:
            content = fh.read()
        # the agent reads the stamp on the lab PC's own clock: IST,
        # wherever this tool happens to run
        ist = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)
        name = ist.strftime("%Y%m%dT%H%M%S_") + os.path.basename(argv[3])
        if not ra._job_name_ok(name) or not ra.DRIVE_JOB_STAMP_RE.match(name):
            print("the agent will refuse this name: %s" % name)
            return 2
        msg = ra.job_message(name, content)
        sig = ra.ed_sign(secret, msg)
        if not ra.ed_verify(ra.ed_public(secret), msg, sig):
            print("self-check failed")
            return 1
        out = os.path.join(os.path.dirname(os.path.abspath(argv[3])), name)
        with open(out, "wb") as fh:
            fh.write(content)
        with open(out + ".sig", "w", encoding="ascii") as fh:
            fh.write(sig.hex() + "\n")
        print("signed: %s  and  %s.sig  (public key %s)"
              % (name, name, ra.ed_public(secret).hex()))
        print("put BOTH into  My Drive\\Clinic Data Archive\\ToLab\\jobs\\  "
              "within 48 hours")
        return 0
    if len(argv) == 4 and argv[1] == "read-token":
        with open(argv[2], "r", encoding="ascii") as fh:
            secret = bytes.fromhex(fh.read().strip())
        name, ts = argv[3], str(int(time.time()))
        if not ra._job_name_ok(name) or not ra.DRIVE_JOB_STAMP_RE.match(name):
            print("not a stamped job name: %s" % name)
            return 2
        sig = ra.ed_sign(secret, READ_CONTEXT + name.encode("utf-8") + b"\n" + ts.encode("ascii"))
        print(json.dumps({"name": name, "ts": ts, "sig": sig.hex()}))
        return 0
    if len(argv) == 3 and argv[1] == "list-token":
        with open(argv[2], "r", encoding="ascii") as fh:
            secret = bytes.fromhex(fh.read().strip())
        ts = str(int(time.time()))
        sig = ra.ed_sign(secret, LIST_CONTEXT + ts.encode("ascii"))
        print(json.dumps({"ts": ts, "sig": sig.hex()}))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
