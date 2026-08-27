#!/usr/bin/env python3
"""
build_S205_B.py  --  S205 · kit S205_B · the VPS half of D350 §2/§3, and F-195

RUN ON THE VPS:
    /root/wa/venv/bin/python3 /root/deploy/build_S205_B.py

WHAT IT CHANGES, IN ONE PASS (so there is one paste, not three)
---------------------------------------------------------------
  1 + 2.  F-195 -- make the B2 selftest bite.
          The B2 test added at the S203 close CLAIMS to post "the REAL
          caller's shape -- token header, NO session". It does not. By the
          time the suite reaches that block it has set ALLOW_HEADER_AUTH True
          and FINANCE_DEV_USER / FINANCE_DEV_ROLE, so current_user() hands an
          identity to ANY client and roles_for() grants that role outright.
          _gate() returns at the ROLE clause and never reaches the token
          clause the test exists to prove. Delete the token clause and the
          test stays green -- which is F-195 in one sentence, and it was
          PROVEN offline before this kit was written (see f195_proof.py: with
          the identity stripped, removing the clause turns the test 401).

  3.      D350 §2/§3 -- THE LINK ITSELF, on the health page.
          Every check on this page watches an ENDPOINT. On 26-Aug-2026 both
          endpoints were healthy and the wire between them was dead for eight
          hours and forty minutes. These five checks watch the wire:

            link        which point is down, IN WORDS -- not "the pipeline
                        failed" but "the PC answers, the share refuses --
                        most likely credentials"
            tailscale   both ends: address, up/down, when each was confirmed
            transport   which route carried the cycle, and WARN, persistently,
                        for as long as it is the reserve one
            credential  whether a stored credential exists at all, and which
                        Windows account the pull runs as -- they are stored
                        PER USER, and a manual test can pass for ever while
                        the scheduled task fails
            backup      the pharmacy's own backup age. manojz has been sending
                        this since S203 and NOTHING ON THIS SERVER HAS EVER
                        READ IT. Found by tracing the payload: it is stored in
                        pipeline_status.payload_json and never looked at.

          A manojz running an OLDER reporter sends none of those sections.
          That reads as "not reported yet", never as ok -- B2C's lesson one
          layer out: silence must never become a green.

WHAT IT DOES NOT CHANGE
-----------------------
No route. No gate. No money path. No data. `_gate()` is untouched -- the F-195
work is entirely inside the smoke suite. The five new checks are readers.

DISCIPLINE
----------
  * refuses unless the input file is byte-for-byte what this was built
    against (md5 asserted -- a filename is not provenance, D188)
  * every anchor asserts its OCCURRENCE COUNT
  * THE PROJECTION IS COMPUTED AND PRINTED BEFORE ANYTHING IS WRITTEN, and
    the file on disk is verified against it afterwards
  * timestamped backup first; on ANY failure nothing is written at all
"""
import hashlib
import io
import os
import shutil
import sys

# The env override exists ONLY so this builder could be proven against a
# scratch copy before ever being pointed at the money application. It defaults
# to the live path.
TARGET = os.environ.get("S205_B_TARGET", "/root/finance/finance_app.py")

# The S204 live bytes. CANONICAL_MANIFEST records /root/finance/finance_app.py
# moving to this md5 at the S204 close.
WANT_IN = "70f799973a0f131c3f515407b2a8cd03"

# ============================================================ F-195, edit 1/3
OLD_A = '''        _mod.MARG_TOKEN = _B2TOK
        try:
            _anon = app.test_client()
'''

NEW_A = '''        _mod.MARG_TOKEN = _B2TOK
        # ---- S205 (F-195): THE TEST BELOW CLAIMS "NO SESSION". MAKE IT TRUE.
        # The suite reaches here having already set ALLOW_HEADER_AUTH True and
        # FINANCE_DEV_USER / FINANCE_DEV_ROLE. current_user() therefore hands
        # an identity to ANY client -- cookie or not -- and roles_for() grants
        # that role outright. _gate() returns at the ROLE clause and NEVER
        # reaches the token clause this test was written to prove. Removing
        # the token clause left this test green: it passed for a reason other
        # than the one it names, which is the whole of F-195.
        # A client that says it has no session must have no WAY to get one.
        _oldaha = _mod.ALLOW_HEADER_AUTH
        _olddu = os.environ.pop("FINANCE_DEV_USER", None)
        _olddr = os.environ.pop("FINANCE_DEV_ROLE", None)
        _mod.ALLOW_HEADER_AUTH = False
        try:
            # Assert the condition rather than trust it. If a future change
            # re-enables header auth above this line, THIS goes red -- rather
            # than the two checks below going quietly meaningless again.
            check("B2/F-195: the anonymous client really is anonymous -- "
                  "header auth off, no dev identity in the environment",
                  _mod.ALLOW_HEADER_AUTH is False
                  and not os.environ.get("FINANCE_DEV_USER")
                  and not os.environ.get("FINANCE_DEV_ROLE"))
            _anon = app.test_client()
'''

# ============================================================ F-195, edit 2/3
OLD_B = '''        finally:
            _mod.MARG_TOKEN = _oldmt
'''

NEW_B = '''        finally:
            _mod.MARG_TOKEN = _oldmt
            # S205 (F-195): put back exactly what was taken, and only that.
            _mod.ALLOW_HEADER_AUTH = _oldaha
            if _olddu is not None:
                os.environ["FINANCE_DEV_USER"] = _olddu
            if _olddr is not None:
                os.environ["FINANCE_DEV_ROLE"] = _olddr
'''

# ====================================================== D350 §2/§3, edit 3/3
OLD_C = '''            _off = _ps.get("offsite") or {}
            if _off.get("lag_hours") is not None and float(_off["lag_hours"]) > 26:
                add("offsite", "Offsite copy", "warn",
                    "the Drive mirror is %s hours behind" % _off["lag_hours"],
                    "The archive is the only copy of a report once Marg "
                    "overwrites its slot.")
'''

NEW_C = '''            _off = _ps.get("offsite") or {}
            if _off.get("lag_hours") is not None and float(_off["lag_hours"]) > 26:
                add("offsite", "Offsite copy", "warn",
                    "the Drive mirror is %s hours behind" % _off["lag_hours"],
                    "The archive is the only copy of a report once Marg "
                    "overwrites its slot.")

            # ================================================================
            #  S205 (D350 §2 / §3): THE LINK ITSELF.
            #
            #  Every check above this line watches an ENDPOINT. On 26-Aug-2026
            #  BOTH endpoints were healthy -- the medical PC was on, the owner
            #  was in an RDP session with it, Tailscale showed it active and
            #  direct, the agent was running, Marg was capturing -- and the
            #  feed was dead for eight hours and forty minutes because Windows
            #  on manojz had stopped allowing an unauthenticated connection to
            #  the share. Two green lights either side of a broken wire.
            #
            #  These watch the wire. And they are DELIBERATELY guarded on the
            #  reporter version: a manojz running the older pipeline_status
            #  sends none of these sections, and that must read as "not
            #  reported yet", never as ok. That is B2C's lesson -- a value that
            #  stopped being written is a MEMORY, not a reading -- applied one
            #  layer out, to a field that was never written at all.
            # ================================================================
            _hrnow = None
            try:
                _hrnow = int(str(_ps.get("at") or "")[11:13])
            except Exception:                                     # noqa: BLE001
                pass
            _cfrom = int(setting(con, "pipeline.clinic_hour_from", "9") or 9)
            _cto = int(setting(con, "pipeline.clinic_hour_to", "21") or 21)
            _inhrs = (_hrnow is not None and _cfrom <= _hrnow < _cto)

            if not _ps.get("reporter"):
                add("link", "The link to the medical PC", "info",
                    "manojz is running a reporter older than these checks",
                    "Tailscale at both ends, the share test, which transport "
                    "carried the cycle and whether a credential exists are not "
                    "being reported yet. Install the S205 pipeline_status.py "
                    "on manojz and they appear here.")
            else:
                # ---- which point is down, IN WORDS (D350 §3) ---------------
                _lk = _ps.get("link") or {}
                _v = _lk.get("verdict")
                _words = _lk.get("verdict_words") or "no verdict was recorded"
                if _v == "ok":
                    add("link", "The link to the medical PC", "ok",
                        "the share was read, in %s ms"
                        % ((_lk.get("share") or {}).get("ms")))
                elif _v == "share_refusing":
                    # The 26-Aug fault. Named, not described in general terms.
                    add("link", "The link to the medical PC", "bad", _words,
                        "THE 26-AUG-2026 FAULT. The machine is there and "
                        "answering; the share is refusing us, which is almost "
                        "always a missing stored credential. On manojz: "
                        "cmdkey /add:<the medical address> /user:MEDICAL\\\\SET "
                        "/pass -- run as the SAME Windows account the "
                        "scheduled task runs as. Do NOT re-enable insecure "
                        "guest access to fix it.")
                elif _v == "host_unreachable":
                    add("link", "The link to the medical PC",
                        "bad" if _inhrs else "info",
                        _words,
                        "In clinic hours: check the medical PC is on and "
                        "Tailscale is connected at BOTH ends. Out of hours "
                        "the machine is meant to be off and this is expected."
                        if _inhrs else
                        "Expected outside clinic hours -- the PC is off.")
                else:
                    add("link", "The link to the medical PC", "info", _words)

                # ---- Tailscale, both ends, with WHEN each was confirmed ----
                _ts = _ps.get("tailscale") or {}
                _here, _med = _ts.get("here") or {}, _ts.get("medical") or {}
                if not _here.get("installed"):
                    add("tailscale", "Tailscale", "warn",
                        "manojz cannot find tailscale.exe",
                        _here.get("note") or "The pull runs over the Tailscale "
                        "share. D347 called it 'not load-bearing'; that is "
                        "wrong and 26-Aug proved it.")
                elif not _here.get("read"):
                    add("tailscale", "Tailscale", "warn",
                        "Tailscale is installed on manojz but could not be read",
                        _here.get("note") or "")
                elif _med.get("seen"):
                    _st = ("ok" if (_med.get("online") is not False)
                           else ("bad" if _inhrs else "info"))
                    add("tailscale", "Tailscale", _st,
                        "manojz %s (%s) — medical %s at %s, %s"
                        % (_here.get("address") or "?",
                           _here.get("backend") or "?",
                           "online" if _med.get("online") else "OFFLINE",
                           _med.get("address") or "?",
                           _med.get("route") or "?"),
                        "Confirmed at %s. A green Tailscale is NOT a working "
                        "pipeline: on 26-Aug this read active and direct for "
                        "the whole outage." % (_ts.get("checked_at") or "?"))
                else:
                    add("tailscale", "Tailscale", "warn",
                        "manojz cannot see the medical PC as a Tailscale peer",
                        _med.get("note") or "The address may have changed.")

                # ---- the MagicDNS name vs the hardcoded number (B6) --------
                _dns = _ps.get("magicdns") or {}
                if _dns.get("agrees") is False:
                    add("tsname", "The medical PC's name and address", "warn",
                        _dns.get("note") or "the name and the number disagree",
                        "The pull addresses the medical PC by a number. When "
                        "the number moves, the feed stops and nothing says "
                        "why. Ask me to switch the pull to the name.")

                # ---- WHICH ROUTE, and warn for as long as it is the reserve
                _tr = _ps.get("transport") or {}
                if _tr.get("fallback"):
                    # D350 §3, taken as written: a fallback nobody notices
                    # becomes the new normal, and then its failure looks like
                    # the first failure. It stays warn for as long as it is
                    # true. This is not an error state; it is a degraded one,
                    # and it must READ as one.
                    add("transport", "Which route reports are travelling", "warn",
                        "running on the FALLBACK route (%s)" % _tr.get("used"),
                        "The primary route is down and the reserve is carrying "
                        "the feed. Nothing is being lost. This stays amber for "
                        "as long as it is true, on purpose -- a reserve route "
                        "that reads as normal is how the SECOND failure "
                        "arrives with no warning.")
                elif _tr.get("used") and not _tr.get("measured"):
                    add("transport", "Which route reports are travelling", "info",
                        "%s — inferred, not reported" % _tr.get("used"),
                        _tr.get("source") or "")

                # ---- does a credential exist AT ALL, and for which account -
                _cr = _ps.get("credential") or {}
                if _cr.get("checked") and _cr.get("exists") is False:
                    add("credential", "The stored credential on manojz",
                        "bad" if _v == "share_refusing" else "warn",
                        "no stored credential for the medical PC under %s"
                        % (_cr.get("running_as") or "the account that ran"),
                        "Credentials are stored PER WINDOWS USER. A manual "
                        "test by you can succeed while the scheduled task "
                        "fails for ever, because the task runs as a different "
                        "account. If the link is refusing, this is the cause.")

                # ---- THE PHARMACY'S BACKUP ---------------------------------
                # manojz has posted this since S203 and nothing here has ever
                # read it. A field that travels and is never looked at is not
                # a monitor; it is a habit. Found by tracing the payload.
                _bku = _ps.get("backup") or {}
                if _bku.get("reported"):
                    _age = _bku.get("stick_age_days")
                    if _age is None:
                        add("margbackup", "Marg backup", "bad",
                            "there is NO backup file on the stick",
                            "Everything the pharmacy has done exists in one "
                            "place. Take a backup in Marg.")
                    elif float(_age) > 3:
                        add("margbackup", "Marg backup", "warn",
                            "the newest Marg backup is %.1f days old"
                            % float(_age),
                            "Marg's own serverbackup sits on D:, the same disk "
                            "as the data -- it is not a disaster copy.")
                    else:
                        add("margbackup", "Marg backup", "ok",
                            "newest backup %.1f day(s) old, offsite copy %s"
                            % (float(_age),
                               "complete" if _bku.get("offsite_complete")
                               else "still catching up"))
                    if _bku.get("offsite_complete") is False:
                        add("margoffsite", "Marg backup, offsite copy", "info",
                            "%s file(s) still to copy"
                            % (_bku.get("pending") or "?"),
                            "It works through them by itself.")
'''

EDITS = (("A  F-195: neutralise the identity for the anonymous-client block",
          OLD_A, NEW_A, 1),
         ("B  F-195: restore it in the finally", OLD_B, NEW_B, 1),
         ("C  D350 §2/§3: the five link checks on the health page",
          OLD_C, NEW_C, 1))


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def fail(msg):
    print("")
    print("  REFUSED: %s" % msg)
    print("  NOTHING WAS WRITTEN.")
    return 1


def main():
    print("=" * 74)
    print("  S205_B  ·  D350 §2/§3 (the link) + F-195 (make the test bite)")
    print("=" * 74)

    if not os.path.exists(TARGET):
        return fail("%s does not exist on this machine." % TARGET)

    raw = io.open(TARGET, "rb").read()
    got_in = md5_bytes(raw)
    print("  target      : %s" % TARGET)
    print("  md5 on disk : %s" % got_in)
    print("  md5 expected: %s" % WANT_IN)
    if got_in != WANT_IN:
        return fail("the file on disk is not the file this kit was built\n"
                    "           against. A filename is not provenance (D188).\n"
                    "           Send me the md5 above and I will rebuild the kit.")
    print("  input verified.")
    print("")

    src = raw.decode("utf-8")

    print("  anchors:")
    for name, old, _new, want_n in EDITS:
        n = src.count(old)
        print("    %-58s found %d, want %d" % (name, n, want_n))
        if n != want_n:
            return fail("anchor '%s' matched %d time(s), not %d.\n"
                        "           An anchor that is not unique is not an "
                        "anchor." % (name, n, want_n))
    print("")

    out = src
    for _name, old, new, _n in EDITS:
        out = out.replace(old, new, 1)
    blob = out.encode("utf-8")
    want_out = md5_bytes(blob)
    print("  PROJECTION (computed before writing):")
    print("    lines  %d  ->  %d   (+%d)"
          % (src.count("\n") + 1, out.count("\n") + 1,
             out.count("\n") - src.count("\n")))
    print("    bytes  %d  ->  %d" % (len(raw), len(blob)))
    print("    md5    %s  ->  %s" % (got_in, want_out))
    print("    checks +1 (the F-195 anonymity assertion) — expect 721 -> 722")
    print("")

    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        return fail("the projected file does not compile: %s" % ex)
    print("  projected file compiles.")

    bak = "%s.bak_S205_B" % TARGET
    if os.path.exists(bak):
        return fail("%s already exists — this kit has been run before.\n"
                    "           Move it aside if you mean to re-run." % bak)
    shutil.copy2(TARGET, bak)
    print("  backup      : %s  (md5 %s)"
          % (bak, md5_bytes(io.open(bak, "rb").read())))

    with io.open(TARGET, "wb") as fh:
        fh.write(blob)

    got_out = md5_bytes(io.open(TARGET, "rb").read())
    print("  written     : md5 %s" % got_out)
    if got_out != want_out:
        shutil.copy2(bak, TARGET)
        return fail("the file on disk does NOT match the projection.\n"
                    "           The backup has been restored.")
    print("  VERIFIED against the projection.")
    print("")
    print("=" * 74)
    print("  DONE. Now, in this order:")
    print("")
    print("    /root/wa/venv/bin/python3 /root/finance/finance_app.py --selftest")
    print("        expect 722/722. Anything else — send me the failing line.")
    print("")
    print("    systemctl restart clinic-finance")
    print("    systemctl is-active clinic-finance")
    print("")
    print("  The five new checks stay quiet until manojz runs the S205")
    print("  pipeline_status.py — until then they say 'not reported yet',")
    print("  which is the truth and not a green.")
    print("")
    print("  TO UNDO:  cp %s %s" % (bak, TARGET))
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
