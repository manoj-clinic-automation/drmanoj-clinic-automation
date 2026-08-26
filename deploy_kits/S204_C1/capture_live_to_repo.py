#!/usr/bin/env python3
"""
capture_live_to_repo.py  --  kit S204_C1  (D350 section 4, the reinstall kit)

WHY THIS EXISTS (S204)
----------------------
At the S204 open every one of the 67 rows in live_pins_S203close.txt was checked
against every one of the 1,952 files in the repository, BY HASH. 61 are
recoverable -- the exact live bytes sit somewhere in the repo. FOUR DO NOT EXIST
IN THE REPO AT ALL:

    /root/finance/finance_app.py            (the clinic's money application)
    /root/finance/finance_ui/finance_entry.html
    /root/deploy/email_agent.py
    /root/wa/recordings-archive/make_force_keys.py

verify_live_pins.py is GREEN on all four, and GREEN is correct: they match the
record. THE RECORD IS A HASH, NOT THE BYTES. A pin proves identity; it cannot
restore a file. D350 section 4 says the reinstall kit is "what rebuilds it if it
dies" -- so this is the missing half: the bytes themselves, carried back off the
box into the repo where git keeps them.

WHAT IT DOES
------------
Reads the live pin list, and for every VPS row:

  * hashes the live file and compares it with the pin
      MATCH   -> eligible to be captured
      DRIFT   -> reported loudly, NEVER captured (capturing an unrecorded file
                 would put bytes nobody has ruled on into the repo, and would
                 also hide the drift by making it look normal)
      MISSING -> reported
  * applies the F-185 publish gate BEFORE copying anything: the same patterns
    tools/phi_scan.py uses (mobile-shaped, secret-shaped, bearer-shaped). A file
    with a hit is NOT captured unless it carries an ALLOWLIST entry with a
    stated reason. Counts are printed; VALUES NEVER ARE.
  * copies the eligible files into the destination folder under flattened
    names, and writes SUMS.md5 + MANIFEST.md beside them
  * re-hashes every written file and refuses to report success unless every
    one matches what was read

It writes ONLY inside the destination folder. It never touches a live file, it
never commits, it never pushes, and it never prints a secret.

USAGE (on the VPS)
    /root/wa/venv/bin/python3 /root/deploy/capture_live_to_repo.py            (dry run: plan only)
    /root/wa/venv/bin/python3 /root/deploy/capture_live_to_repo.py --write    (actually copy)

    --pins PATH   default /root/deploy/live_pins.txt
    --dest PATH   default /root/deploy/repo/deploy_kits/S204_VPS_LIVE

EXIT CODES
    0  everything eligible was captured and verified (or, on a dry run, the plan
       is clean)
    1  something needs a human: drift, a missing file, a gate hit, or a
       verification failure after writing
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
import time

KIT = "S204_C1"

# --- the F-185 publish gate: the same three patterns tools/phi_scan.py uses ---
MOBILE = re.compile(r'(?<!\d)[6-9]\d{9}(?!\d)')
SECRET = re.compile(r'(?i)(token|secret|api[_-]?key|password|passwd)\s*[:=]\s*[\'"][^\'"]{8,}')
BEARER = re.compile(r'(?i)bearer\s+\S{16,}')

# live path -> the stated reason it may carry a pattern hit and still be captured.
# "It's fine" is not a reason (tools/phi_scan.py's rule, kept verbatim here).
ALLOWLIST = {
    "/root/finance/finance_app.py":
        "S204: the only secret-shaped literal is the smoke test's own placeholder "
        "CRON_TOKEN at the D204-era Docterz feed check -- a dummy assigned inside "
        "selftest(), not a credential. Verified by reading the line at S204.",
}

TEXT_EXT = {'.py', '.md', '.txt', '.html', '.json', '.sql', '.gs', '.sh',
            '.bat', '.cmd', '.csv', '.tsv', '.vbs', '.js', '.yml', '.yaml'}


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def gate_counts(path):
    """(mobiles, secrets, bearers) -- counts only. Never returns a value."""
    if os.path.splitext(path)[1].lower() not in TEXT_EXT:
        return (0, 0, 0)
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            t = f.read()
    except OSError:
        return (0, 0, 0)
    return (len(set(MOBILE.findall(t))), len(SECRET.findall(t)), len(BEARER.findall(t)))


def read_pins(pins_path):
    """[(host, md5, path, note)] for rows that carry a real hash.

    The pin list is tab-separated and its note column contains free text, so
    only the first three fields are parsed strictly."""
    rows = []
    with open(pins_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 3:
                continue
            host, digest, path = parts[0].strip(), parts[1].strip(), parts[2].strip()
            if not re.fullmatch(r'[0-9a-f]{32}', digest):
                continue
            rows.append((host, digest, path, parts[3].strip() if len(parts) > 3 else ""))
    return rows


def flat_name(live_path):
    """/root/finance/finance_ui/finance_entry.html -> root__finance__finance_ui__finance_entry.html"""
    return live_path.lstrip('/').replace('/', '__')


def classify(rows):
    """-> (eligible, drift, missing, gated)"""
    eligible, drift, missing, gated = [], [], [], []
    for host, digest, path, note in rows:
        if host.upper() != 'VPS':
            continue
        if not os.path.isfile(path):
            missing.append((path, digest, note))
            continue
        actual = md5_of(path)
        if actual != digest:
            drift.append((path, digest, actual, note))
            continue
        m, s, b = gate_counts(path)
        if (m or s or b) and path not in ALLOWLIST:
            gated.append((path, digest, m, s, b, note))
            continue
        eligible.append((path, digest, note, (m, s, b)))
    return eligible, drift, missing, gated


def write_capture(eligible, dest, pins_path):
    os.makedirs(dest, exist_ok=True)
    written, failed = [], []
    for path, digest, note, counts in eligible:
        target = os.path.join(dest, flat_name(path))
        shutil.copy2(path, target)
        back = md5_of(target)
        if back == digest:
            written.append((path, digest, os.path.getsize(target), note, counts))
        else:
            failed.append((path, digest, back))

    sums = os.path.join(dest, "SUMS.md5")
    with open(sums, 'w', encoding='utf-8', newline='\n') as f:
        for path, digest, _size, _note, _c in written:
            f.write("%s  %s\n" % (digest, flat_name(path)))

    stamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    man = os.path.join(dest, "MANIFEST.md")
    with open(man, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# %s -- LIVE VPS BYTES, CAPTURED\n\n" % KIT)
        f.write("**Written by `capture_live_to_repo.py` at %s. D350 section 4.**\n\n" % stamp)
        f.write("Every file below was read from the running VPS and its md5 matched the pin in\n")
        f.write("`%s` at the moment of capture. A pin proves identity; these are the bytes.\n\n" % pins_path)
        f.write("| live path | md5 | bytes | gate (mob/sec/bearer) |\n|---|---|---|---|\n")
        for path, digest, size, _note, c in written:
            f.write("| `%s` | `%s` | %d | %d / %d / %d |\n" % (path, digest, size, c[0], c[1], c[2]))
        f.write("\n**Restore:** copy the flattened file back to its live path, then run\n")
        f.write("`python3 /root/deploy/verify_live_pins.py` and expect GREEN.\n")
        if ALLOWLIST:
            f.write("\n## Gate allowlist entries used\n\n")
            for k, v in ALLOWLIST.items():
                f.write("- `%s` — %s\n" % (k, v))
    return written, failed, sums, man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pins", default="/root/deploy/live_pins.txt")
    ap.add_argument("--dest", default="/root/deploy/repo/deploy_kits/S204_VPS_LIVE")
    ap.add_argument("--write", action="store_true",
                    help="actually copy; without it this is a dry run")
    a = ap.parse_args()

    print("=" * 74)
    print("  %s  --  capture the live VPS bytes into the repo   (D350 section 4)" % KIT)
    print("=" * 74)
    print("  pins : %s" % a.pins)
    print("  dest : %s" % a.dest)
    print("  mode : %s" % ("WRITE" if a.write else "DRY RUN -- nothing will be copied"))
    print()

    if not os.path.isfile(a.pins):
        print("!! pin list not found: %s" % a.pins)
        print("   copy live_pins_S203close.txt to it first, then run this again.")
        return 1

    rows = read_pins(a.pins)
    eligible, drift, missing, gated = classify(rows)
    vps_rows = [r for r in rows if r[0].upper() == 'VPS']
    print("  VPS rows in the pin list : %d" % len(vps_rows))
    print("  eligible to capture      : %d" % len(eligible))
    print("  DRIFT (never captured)   : %d" % len(drift))
    print("  missing on the box       : %d" % len(missing))
    print("  held by the F-185 gate   : %d" % len(gated))
    print()

    for path, pin, actual, _n in drift:
        print("  !! DRIFT   %s" % path)
        print("             pinned %s   on the box %s" % (pin, actual))
    for path, pin, _n in missing:
        print("  !! MISSING %s   (pinned %s)" % (path, pin))
    for path, _d, m, s, b, _n in gated:
        print("  !! GATED   %s   mobile-shaped=%d secret-shaped=%d bearer-shaped=%d"
              % (path, m, s, b))
        print("             values are never printed. Either clear it and add an")
        print("             ALLOWLIST entry WITH A REASON, or leave it out of the repo.")
    if drift or missing or gated:
        print()

    if not a.write:
        print("  DRY RUN. Would capture %d file(s):" % len(eligible))
        for path, digest, _n, _c in eligible:
            print("     %s  ->  %s" % (path, flat_name(path)))
        print()
        print("  Nothing was written. Re-run with --write to capture.")
        return 1 if (drift or missing or gated) else 0

    written, failed, sums, man = write_capture(eligible, a.dest, a.pins)
    print("  CAPTURED %d of %d eligible file(s)" % (len(written), len(eligible)))
    for path, digest, size, _n, _c in written:
        print("     %s  %8d bytes  %s" % (digest, size, path))
    for path, want, got in failed:
        print("  !! VERIFY FAILED after copy: %s" % path)
        print("     expected %s   read back %s" % (want, got))
    print()
    print("  wrote %s" % sums)
    print("  wrote %s" % man)
    print()
    print("  Verify independently:   cd %s && md5sum -c SUMS.md5" % a.dest)
    print("  These files are inside the repo clone. They reach GitHub only when the")
    print("  repo is committed and pushed -- this script deliberately does neither.")
    ok = bool(written) and not failed and not drift and not missing and not gated
    print()
    print("  RESULT: %s" % ("GREEN -- every eligible file captured and verified"
                            if ok else "NEEDS A LOOK -- see the lines marked !! above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
