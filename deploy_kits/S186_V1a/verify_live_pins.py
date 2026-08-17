#!/usr/bin/env python3
# =============================================================================
#  verify_live_pins.py  ·  v1.1  ·  Session 186  ·  the F-97 + F-110 fixes
#
#  THE PROBLEM THIS EXISTS FOR
#  ---------------------------
#  The KB Register records an md5 for every live file. Nothing ever asked the
#  box whether that record was true. At S182 `/root/portal/portal.py` was
#  pinned `da417709...` (S176) while the box was actually running
#  `34f038a765...` -- stale by two sessions -- and the GitHub copy agreed with
#  the stale pin byte-for-byte. Two records agreed with each other and both
#  were wrong. A full-file replacement built on that pin would have deleted the
#  medical unit's two live finance tiles with every gate passing.
#
#  Phase 0 verifies DOCUMENTS. This verifies LIVE CODE.
#
#  WHAT IT DOES
#  ------------
#  Reads a pin list, hashes every pinned file ON THIS MACHINE, and gives each
#  one a verdict:
#
#     MATCH      record and reality agree
#     DRIFT      the box is running something else            <- F-97
#     MISSING    the record names a file that is not there
#     UNTRACKED  a live file the record never mentioned       <- the reverse gap
#
#  It also prints, every single run, the rows it CANNOT check from this machine
#  (Apps Script files, applied migrations, PC-side files). A checker that hides
#  what it cannot see is worse than no checker (D166: the correct entry is
#  sometimes UNKNOWN; F-99: a detector blind to a class must say so).
#
#  IT NEVER WRITES TO A LIVE FILE. Read-only, safe to run at any time.
#
#  F-88 APPLIED TO THIS TOOL: it reports which pin list it read AND that list's
#  own md5, so a stale pin list cannot pass itself off as a clean result.
#
#  v1.1 -- F-110: REPORTING IS NOT ENFORCING
#  ----------------------------------------
#  v1.0 printed the pin list's declared source and that source's md5. It did
#  not check them. At S183 the list on this box was generated from an
#  intermediate draft of Register v5.5 (`ff509b01...`) that never became
#  canonical -- and it said so, in its own header, in every run, for three
#  sessions. Nothing compared that md5 to the manifest, so at the S186 open the
#  tool reported three DRIFT reds of which TWO WERE FALSE: the canonical
#  Register already held the values the box was running. The record was right;
#  the checker was behind it, and announced its own staleness to nobody.
#
#  So from v1.1 the pin list must carry an ATTESTATION written by
#  gen_live_pins.py v1.1+, which refuses to build a list from a Register that
#  is not the one the manifest pins as CURRENT:
#
#     # register_pin_verified: yes            -> normal run
#     # register_pin_verified: pending: ...   -> runs, but AMBER, never GREEN
#     # (absent, or anything else)            -> REFUSES TO RUN, exit 2
#
#  A checker that can be stale must verify its own source before it verifies
#  anything else, and refuse to run rather than report.
#
#  EXIT CODES
#     0  every pinned file MATCHes  (untracked files may be reported as WARN)
#     1  at least one DRIFT or MISSING  -- the F-97 condition
#     2  setup problem: no pin list, unreadable pin list, bad arguments,
#        or a pin list carrying no source attestation at all (F-110)
#
#  USAGE
#     python3 verify_live_pins.py                    # check, using ./live_pins.txt
#     python3 verify_live_pins.py --pins /path/to/live_pins.txt
#     python3 verify_live_pins.py --emit             # + paste-back table for the Register
#     python3 verify_live_pins.py --selftest         # prove the checker can fail
#
#  Stdlib only. No network. No third-party imports.
# =============================================================================

import argparse
import hashlib
import os
import shutil
import sys
import tempfile

VERSION = "1.1"

# Files considered "code-ish" when hunting for UNTRACKED live files.
CODE_EXT = (".py", ".sh", ".sql", ".js", ".html")

# Never counted as untracked: backups, build leftovers, caches, hidden files.
NOISE_MARKERS = (".bak", ".new", ".candidate", ".orig", ".tmp", ".pyc",
                 "__pycache__", ".LIVE_")


# ----------------------------------------------------------------------------
# pin list
# ----------------------------------------------------------------------------

def md5_of(path):
    """md5 of a file, or None if it cannot be read."""
    try:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return None


def load_pins(pins_path):
    """
    Read the pin list.

    Format is TSV, one row per artefact, '#' starts a comment:
        VPS<TAB><md5><TAB><absolute path><TAB><note>
        BLIND<TAB><md5 or ->><TAB><name><TAB><why it cannot be checked here>
        IGNORE<TAB>-<TAB><absolute path><TAB><why it is deliberately unpinned>

    Returns (meta, vps_rows, blind_rows, ignore_paths).
    Raises ValueError on anything it cannot classify -- a row shape this tool
    does not understand must stop the run, never be silently skipped.
    """
    if not os.path.isfile(pins_path):
        raise ValueError("pin list not found: %s" % pins_path)

    meta = {"path": os.path.abspath(pins_path), "md5": md5_of(pins_path)}
    vps, blind, ignore = [], [], []

    with open(pins_path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            if line.startswith("#"):
                # '# key: value' header lines carry provenance we want to print.
                body = line.lstrip("#").strip()
                if ":" in body:
                    k, v = body.split(":", 1)
                    k = k.strip().lower()
                    if k in ("source", "source_md5", "generated", "session",
                             "manifest", "manifest_md5",
                             "register_pin_verified"):
                        meta[k] = v.strip()
                continue

            parts = line.split("\t")
            if len(parts) < 3:
                raise ValueError(
                    "pin list line %d has %d columns, needs at least 3: %r"
                    % (lineno, len(parts), line[:90]))

            kind = parts[0].strip().upper()
            digest = parts[1].strip().lower()
            name = parts[2].strip()
            note = parts[3].strip() if len(parts) > 3 else ""

            if kind == "VPS":
                if len(digest) != 32 or any(c not in "0123456789abcdef" for c in digest):
                    raise ValueError(
                        "pin list line %d: %r is not an md5" % (lineno, digest))
                if not name.startswith("/"):
                    raise ValueError(
                        "pin list line %d: VPS path must be absolute, got %r"
                        % (lineno, name))
                vps.append({"md5": digest, "path": name, "note": note})
            elif kind == "BLIND":
                blind.append({"md5": digest, "name": name, "note": note})
            elif kind == "IGNORE":
                if not name.startswith("/"):
                    raise ValueError(
                        "pin list line %d: IGNORE path must be absolute, got %r"
                        % (lineno, name))
                ignore.append(name)
            else:
                raise ValueError(
                    "pin list line %d: unknown row type %r (expected VPS, BLIND or IGNORE)"
                    % (lineno, kind))

    if not vps:
        raise ValueError("pin list contains no VPS rows -- nothing to verify")

    seen = {}
    for row in vps:
        if row["path"] in seen:
            raise ValueError("pin list names %s twice" % row["path"])
        seen[row["path"]] = True

    return meta, vps, blind, ignore


# ----------------------------------------------------------------------------
# the check
# ----------------------------------------------------------------------------

def _under(root, abspath):
    """Re-root an absolute path. root='/' is the real machine; the selftest
    passes a temporary directory so the checker can be exercised for real."""
    if root in ("", "/"):
        return abspath
    return os.path.join(root, abspath.lstrip("/"))


def check_pinned(vps_rows, root="/"):
    """Hash each pinned file and return a verdict row per pin."""
    out = []
    for row in vps_rows:
        real = _under(root, row["path"])
        actual = md5_of(real)
        if actual is None:
            verdict = "MISSING"
        elif actual == row["md5"]:
            verdict = "MATCH"
        else:
            verdict = "DRIFT"
        out.append({"verdict": verdict, "path": row["path"],
                    "expected": row["md5"], "actual": actual,
                    "note": row["note"]})
    return out


def find_untracked(vps_rows, ignore_paths, root="/"):
    """
    Look for live code files sitting in the same directories as pinned files
    that the record never mentions. This is the reverse of DRIFT and it is how
    a file becomes stale in the first place: it changes, or appears, and the
    Register is never told.

    Non-recursive by design -- one level per pinned directory, so the result
    stays small enough that a person actually reads it.
    """
    pinned = set(r["path"] for r in vps_rows)
    ignored = set(ignore_paths)
    dirs = sorted(set(os.path.dirname(r["path"]) for r in vps_rows))

    found = []
    for d in dirs:
        real_dir = _under(root, d)
        try:
            names = sorted(os.listdir(real_dir))
        except (OSError, IOError):
            continue
        for n in names:
            if n.startswith("."):
                continue
            if not n.endswith(CODE_EXT):
                continue
            if any(m in n for m in NOISE_MARKERS):
                continue
            full = d.rstrip("/") + "/" + n
            if full in pinned or full in ignored:
                continue
            if not os.path.isfile(_under(root, full)):
                continue
            found.append(full)
    return found


# ----------------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------------

def attestation(meta):
    """
    F-110 gate. Returns ('ok'|'pending'|'absent', detail).

    'absent' is a REFUSAL, not a warning: a pin list with no attestation was
    built by a generator that never checked its own source, which is exactly
    the condition that held this box to a draft for three sessions.
    """
    raw = (meta.get("register_pin_verified") or "").strip()
    if not raw:
        return "absent", ""
    low = raw.lower()
    if low == "yes":
        return "ok", ""
    if low.startswith("pending"):
        detail = raw.split(":", 1)[1].strip() if ":" in raw else ""
        return "pending", detail
    return "absent", raw


def report(meta, results, blind, untracked, emit=False, out=sys.stdout):
    w = out.write
    counts = {"MATCH": 0, "DRIFT": 0, "MISSING": 0}
    for r in results:
        counts[r["verdict"]] += 1

    w("\n")
    w("=" * 74 + "\n")
    w("  LIVE-CODE PIN CHECK  (verify_live_pins v%s)  --  the F-97 check\n" % VERSION)
    w("=" * 74 + "\n")
    w("  pin list : %s\n" % meta.get("path", "?"))
    w("  its md5  : %s   <- a stale pin list cannot look clean (F-88)\n"
      % meta.get("md5", "?"))
    if meta.get("source"):
        w("  built from: %s" % meta["source"])
        if meta.get("source_md5"):
            w("  (md5 %s)" % meta["source_md5"])
        w("\n")
    if meta.get("session"):
        w("  pinned at: %s\n" % meta["session"])

    state, detail = attestation(meta)
    if state == "ok":
        w("  source   : VERIFIED against the manifest %s (md5 %s)\n"
          % (meta.get("manifest", "?"), meta.get("manifest_md5", "?")))
    else:
        w("\n")
        w("  " + "!" * 70 + "\n")
        w("  !! THIS PIN LIST'S SOURCE IS NOT VERIFIED AGAINST THE MANIFEST\n")
        w("  !! %s\n" % (detail or "no attestation in the pin list header"))
        w("  !! Every verdict below is measured against a record that has not\n")
        w("  !! been proved canonical. This is the F-110 condition.\n")
        w("  " + "!" * 70 + "\n")
    w("\n")

    # --- the failures first: nobody should have to scroll to find bad news ---
    bad = [r for r in results if r["verdict"] in ("DRIFT", "MISSING")]
    if bad:
        w("  !! THE BOX DOES NOT MATCH THE RECORD\n\n")
        for r in bad:
            w("   %-9s %s\n" % (r["verdict"], r["path"]))
            w("             record says : %s\n" % r["expected"])
            if r["verdict"] == "DRIFT":
                w("             box is  now : %s\n" % r["actual"])
            else:
                w("             box has     : nothing at that path\n")
            if r["note"]:
                note = r["note"]
                w("             note        : %s\n"
                  % (note if len(note) <= 84 else note[:81] + "..."))
            w("\n")
        w("   Do NOT build a full-file replacement on the recorded md5 for the\n")
        w("   files above. Read the live file off the box and build on that.\n")
        w("   That is exactly what F-97 was.\n\n")
    else:
        w("  All %d pinned files match the record.\n\n" % counts["MATCH"])

    # --- files the record never mentioned ---
    if untracked:
        w("  -- UNTRACKED (live code the record never mentioned) : %d\n"
          % len(untracked))
        w("     Not a failure by itself. Either add it to the Register, or add\n")
        w("     an IGNORE line to the pin list saying why it does not belong.\n")
        for p in untracked:
            w("       %s\n" % p)
        w("\n")

    # --- what this machine cannot see, stated every run ---
    w("  -- CANNOT BE CHECKED FROM THIS MACHINE : %d\n" % len(blind))
    if blind:
        for b in blind:
            w("       %-42s %s\n" % (b["name"], b["note"] or ""))
    w("     These are blind spots, not passes. Nothing here was verified.\n\n")

    w("-" * 74 + "\n")
    w("  match %d   drift %d   missing %d   untracked %d   unverifiable %d\n"
      % (counts["MATCH"], counts["DRIFT"], counts["MISSING"],
         len(untracked), len(blind)))
    if bad:
        w("  VERDICT: RED -- the record is wrong about %d file(s). Fix the record\n"
          % len(bad))
        w("           (or the box) before building anything on those pins.\n")
    elif state == "pending":
        w("  VERDICT: AMBER -- every pinned file matches, but the pin list was\n")
        w("           built from a Register the manifest does not pin as CURRENT.\n")
        w("           Regenerate it against the rebuilt manifest before trusting\n")
        w("           this as a pass (F-110).\n")
    else:
        w("  VERDICT: GREEN -- every pinned file on this box is what the record says.\n")
    w("-" * 74 + "\n\n")

    if emit:
        w("  PASTE-BACK -- measured on this box, for the Register live-file table.\n")
        w("  Transcribe the Register from THIS, not from what we believe we installed.\n\n")
        for r in results:
            if r["verdict"] == "MISSING":
                continue
            w("| `%s` | `%s` |\n" % (r["path"], r["actual"]))
        w("\n")

    return 1 if bad else 0


# ----------------------------------------------------------------------------
# selftest -- a check that cannot fail is not a check
# ----------------------------------------------------------------------------

def selftest():
    """
    Build a fake machine containing, deliberately:
      * a file that matches its pin          -> must report MATCH
      * a file that does NOT match its pin   -> must report DRIFT
      * a pin whose file is absent           -> must report MISSING
      * a live file no pin mentions          -> must report UNTRACKED
      * a live file covered by IGNORE        -> must NOT be reported
      * a backup file next to a pinned file  -> must NOT be reported
      * a BLIND row                          -> must be listed, never counted as a pass
    Then assert the checker reports exactly those and exits 1.
    A run where every assertion could pass by accident proves nothing, so the
    drifted file is also checked to be sure the tool noticed the RIGHT hash.
    """
    print("verify_live_pins v%s -- selftest" % VERSION)
    checks = 0
    failures = []

    def ok(label, cond):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(label)

    tmp = tempfile.mkdtemp(prefix="vlp_selftest_")
    try:
        fake_dir = os.path.join(tmp, "root", "app")
        os.makedirs(fake_dir)

        def put(name, text):
            p = os.path.join(fake_dir, name)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            return md5_of(p)

        good_md5 = put("good.py", "print('unchanged since it was pinned')\n")
        put("drifted.py", "print('somebody changed me on the box')\n")
        drifted_actual = md5_of(os.path.join(fake_dir, "drifted.py"))
        put("surprise.py", "print('live, and the record has never heard of me')\n")
        put("known_extra.py", "print('deliberately unpinned')\n")
        put("good.py.bak_S182", "print('a backup, not live code')\n")

        wrong_md5 = "0" * 32
        pins = os.path.join(tmp, "pins.tsv")
        with open(pins, "w", encoding="utf-8") as fh:
            fh.write("# source: FAKE_Register_for_selftest.md\n")
            fh.write("# manifest: FAKE_MANIFEST.md\n")
            fh.write("# manifest_md5: %s\n" % ("f" * 32))
            fh.write("# register_pin_verified: yes\n")
            fh.write("VPS\t%s\t/root/app/good.py\tshould match\n" % good_md5)
            fh.write("VPS\t%s\t/root/app/drifted.py\tshould drift\n" % wrong_md5)
            fh.write("VPS\t%s\t/root/app/vanished.py\tshould be missing\n" % wrong_md5)
            fh.write("IGNORE\t-\t/root/app/known_extra.py\tdeliberately unpinned\n")
            fh.write("BLIND\tdeadbeef\tsome_script.gs\tlives in Apps Script\n")

        meta, vps, blind, ignore = load_pins(pins)
        ok("pin list parsed: 3 VPS rows", len(vps) == 3)
        ok("pin list parsed: 1 BLIND row", len(blind) == 1)
        ok("pin list parsed: 1 IGNORE row", len(ignore) == 1)
        ok("pin list reports its own md5", meta.get("md5") and len(meta["md5"]) == 32)
        ok("an attested pin list is accepted", attestation(meta)[0] == "ok")

        # F-110: the three attestation states
        att_absent = os.path.join(tmp, "att_absent.tsv")
        with open(att_absent, "w", encoding="utf-8") as fh:
            fh.write("# source: no_attestation.md\n")
            fh.write("VPS\t%s\t/root/app/good.py\tx\n" % good_md5)
        m2, _, _, _ = load_pins(att_absent)
        ok("a pin list with NO attestation is refused",
           attestation(m2)[0] == "absent")
        # main() shouts about this on stderr by design; the selftest is not the
        # place to shout, so it is muffled here and only the verdict is checked.
        _real_err = sys.stderr
        try:
            sys.stderr = open(os.devnull, "w")
            _rc_unattested = main(["--pins", att_absent])
        finally:
            try:
                sys.stderr.close()
            except Exception:
                pass
            sys.stderr = _real_err
        ok("an unattested list is refused by main(), exit 2", _rc_unattested == 2)

        att_pending = os.path.join(tmp, "att_pending.tsv")
        with open(att_pending, "w", encoding="utf-8") as fh:
            fh.write("# source: draft.md\n")
            fh.write("# register_pin_verified: pending: manifest row lands at EOS\n")
            fh.write("VPS\t%s\t/root/app/good.py\tx\n" % good_md5)
        m3, _, _, _ = load_pins(att_pending)
        ok("a PENDING attestation is neither ok nor absent",
           attestation(m3)[0] == "pending")
        ok("a PENDING attestation carries its reason forward",
           "EOS" in attestation(m3)[1])

        att_junk = os.path.join(tmp, "att_junk.tsv")
        with open(att_junk, "w", encoding="utf-8") as fh:
            fh.write("# register_pin_verified: probably fine\n")
            fh.write("VPS\t%s\t/root/app/good.py\tx\n" % good_md5)
        m4, _, _, _ = load_pins(att_junk)
        ok("an attestation that is not 'yes' is treated as absent",
           attestation(m4)[0] == "absent")

        sink2 = open(os.devnull, "w")
        rc_amber = report(m3, check_pinned([{"md5": good_md5,
                                             "path": "/root/app/good.py",
                                             "note": ""}], root=tmp),
                          [], [], out=sink2)
        sink2.close()
        ok("a clean PENDING run still exits 0 (it is AMBER, not a failure)",
           rc_amber == 0)

        results = check_pinned(vps, root=tmp)
        by_path = dict((r["path"], r) for r in results)
        ok("good.py -> MATCH", by_path["/root/app/good.py"]["verdict"] == "MATCH")
        ok("drifted.py -> DRIFT", by_path["/root/app/drifted.py"]["verdict"] == "DRIFT")
        ok("vanished.py -> MISSING", by_path["/root/app/vanished.py"]["verdict"] == "MISSING")
        # the tool must have read the REAL file, not merely disagreed with the pin
        ok("DRIFT reports the hash actually on the box",
           by_path["/root/app/drifted.py"]["actual"] == drifted_actual)
        ok("MISSING reports no hash",
           by_path["/root/app/vanished.py"]["actual"] is None)

        untracked = find_untracked(vps, ignore, root=tmp)
        ok("surprise.py -> UNTRACKED", "/root/app/surprise.py" in untracked)
        ok("IGNORE row is not reported untracked",
           "/root/app/known_extra.py" not in untracked)
        ok("a .bak file is not reported untracked",
           not any("bak" in u for u in untracked))
        ok("untracked finds exactly one file", len(untracked) == 1)

        sink = open(os.devnull, "w")
        rc = report(meta, results, blind, untracked, emit=True, out=sink)
        sink.close()
        ok("a run with drift exits 1", rc == 1)

        # and the mirror case: a clean machine must exit 0
        clean_pins = os.path.join(tmp, "clean.tsv")
        with open(clean_pins, "w", encoding="utf-8") as fh:
            fh.write("VPS\t%s\t/root/app/good.py\tclean\n" % good_md5)
            fh.write("IGNORE\t-\t/root/app/drifted.py\t-\n")
            fh.write("IGNORE\t-\t/root/app/surprise.py\t-\n")
            fh.write("IGNORE\t-\t/root/app/known_extra.py\t-\n")
        m2, v2, b2, i2 = load_pins(clean_pins)
        r2 = check_pinned(v2, root=tmp)
        u2 = find_untracked(v2, i2, root=tmp)
        sink = open(os.devnull, "w")
        rc2 = report(m2, r2, b2, u2, out=sink)
        sink.close()
        ok("a clean run exits 0", rc2 == 0)

        # malformed pin lists must stop the run, never be skipped
        for bad_text, label in (
                ("VPS\tnot-a-hash\t/root/app/good.py\tx\n", "rejects a non-md5"),
                ("VPS\t%s\trelative/path.py\tx\n" % good_md5, "rejects a relative path"),
                ("WAT\t%s\t/root/app/good.py\tx\n" % good_md5, "rejects an unknown row type"),
                ("VPS\t%s\n" % good_md5, "rejects a short line"),
                ("BLIND\t-\tonly.gs\tx\n", "rejects a list with no VPS rows"),
                ("VPS\t%s\t/root/app/good.py\ta\nVPS\t%s\t/root/app/good.py\tb\n"
                 % (good_md5, good_md5), "rejects a duplicated path"),
        ):
            p = os.path.join(tmp, "bad.tsv")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(bad_text)
            try:
                load_pins(p)
                ok(label, False)
            except ValueError:
                ok(label, True)

        try:
            load_pins(os.path.join(tmp, "does_not_exist.tsv"))
            ok("rejects a missing pin list", False)
        except ValueError:
            ok("rejects a missing pin list", True)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("  %d/%d checks passed" % (checks - len(failures), checks))
    if failures:
        for f in failures:
            print("  FAILED: %s" % f)
        print("SELFTEST RED -- the checker is not trustworthy. Do not rely on it.")
        return 1
    print("SELFTEST GREEN -- the checker detects drift, absence and surprises,")
    print("                  ignores backups, and refuses a malformed pin list.")
    return 0


# ----------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check that the live files on this machine are what the "
                    "KB Register says they are (the F-97 check). Read-only.")
    ap.add_argument("--pins", default=None,
                    help="path to live_pins.txt (default: next to this script, "
                         "then the current directory)")
    ap.add_argument("--emit", action="store_true",
                    help="also print a paste-back table of the md5s measured "
                         "on this box, for the EOS Register update")
    ap.add_argument("--accept-unattested-pins", action="store_true",
                    help="run even though the pin list carries no verified "
                         "source attestation (F-110). Prints the banner anyway.")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the checker can fail, then exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.pins:
        pins_path = args.pins
    else:
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "live_pins.txt")
        pins_path = here if os.path.isfile(here) else "live_pins.txt"

    try:
        meta, vps, blind, ignore = load_pins(pins_path)
    except ValueError as e:
        sys.stderr.write("\n!! cannot run: %s\n" % e)
        sys.stderr.write("   Refusing to report anything rather than report "
                         "something misleading.\n\n")
        return 2

    state, detail = attestation(meta)
    if state == "absent" and not args.accept_unattested_pins:
        sys.stderr.write(
            "\n!! REFUSING TO RUN: this pin list carries no verified source.\n"
            "     pin list : %s\n"
            "     header   : register_pin_verified = %s\n\n"
            "   Regenerate it with gen_live_pins.py v1.1+ and --manifest, so the\n"
            "   Register it was built from is proved to be the one the manifest\n"
            "   pins as CURRENT.\n\n"
            "   Why this is a refusal and not a warning: at S183 this box was\n"
            "   held to a Register draft that never became canonical. The list\n"
            "   printed its own source md5 every run for three sessions and\n"
            "   nothing compared it to anything (F-110). A checker that can be\n"
            "   stale must verify its own source before it verifies anything\n"
            "   else, and refuse to run rather than report.\n\n"
            "   To override anyway (and see the reds, unverified):\n"
            "     python3 verify_live_pins.py --accept-unattested-pins\n\n"
            % (meta.get("path", "?"), detail or "(absent)"))
        return 2

    results = check_pinned(vps)
    untracked = find_untracked(vps, ignore)
    return report(meta, results, blind, untracked, emit=args.emit)


if __name__ == "__main__":
    sys.exit(main())
