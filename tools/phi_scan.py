#!/usr/bin/env python3
"""
phi_scan.py -- refuse to publish patient data or secrets into a repository.

WHY THIS EXISTS (S202)
----------------------
F-96 (S181) recorded "7 unmasked patient mobiles, >=2 patient names and 1 clinic
patient ID across 48 files" and D320 ruled, on that evidence, that the repo may
stay public. At the S202 open the repo was MEASURED for the first time:
133 distinct mobile-shaped numbers across ~190 files, including two orphan
sample files carrying 13 named patients WITH THEIR DIAGNOSES.

The ruling was sound; the count it was given was wrong by about nineteen times
and had never looked at code or at test data. D172/D188 applied to a decision:
a ruling inherits the reliability of the facts it was given.

So this is the check that was missing. Run it before every publish.
It NEVER prints a matched value -- printing them is the thing it exists to stop.

USAGE
    python tools\\phi_scan.py                 (from the repo root)
    exit 0 = clean   exit 1 = something to look at

An ALLOWLIST entry needs a stated reason. "It's fine" is not a reason.
"""
import os, re, subprocess, sys, json

MOBILE  = re.compile(r'(?<!\d)[6-9]\d{9}(?!\d)')
SECRET  = re.compile(r'(?i)(token|secret|api[_-]?key|password|passwd)\s*[:=]\s*[\'"][^\'"]{8,}')
BEARER  = re.compile(r'(?i)bearer\s+\S{16,}')
SCAN_EXT = {'.py','.md','.json','.txt','.html','.sql','.gs','.bat','.cmd','.csv','.tsv','.vbs','.js','.yml','.yaml'}
SKIP_DIR = {'.git','__pycache__','node_modules','_PHI_QUARANTINE_S202'}

# path substring -> why it is allowed to contain mobile-shaped digits
ALLOWLIST = {
    "followup-tracker/test_ivr_reconcile.py": "synthetic fixtures: Asha/Beena/Chaya on sequential 90000000NN",
    "followup-tracker/test_suite.py":         "synthetic fixtures, same sequential pattern",
    "followup-tracker/test_fixes.py":         "synthetic fixtures",
    "/api/":                                  "MyOperator API docs: the clinic's OWN business lines and vendor DIDs",
    "/obd/":                                  "click-to-call docs: the clinic's own lines",
    "/sops/":                                 "SOP docs: the clinic's own lines",
}

def allowed(rel):
    r = rel.replace("\\", "/")
    for k, why in ALLOWLIST.items():
        if k in r:
            return why
    return None

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    findings, allowed_hits, distinct = [], 0, set()
    # S202 CORRECTION -- THE BUG THIS TOOL SHIPPED WITH.
    # v1 walked the FILESYSTEM. That is the wrong set: it sees files git is
    # deliberately excluding, and reports them as public when they are not.
    # It did exactly that on its first run -- flagged two .csv files holding 13
    # named patients WITH DIAGNOSES as a public exposure, when `.gitignore`
    # line 31 (`*.csv`) had always excluded them and NOT ONE .csv is tracked in
    # this repository. The protection was working; the scanner was not looking
    # at what "public" means.
    # A scanner that reports what is public must ask GIT what is public.
    # RULE (the same one this project keeps re-learning): a claim about a
    # mechanism must be made by opening the mechanism.
    try:
        out = subprocess.run(["git", "--no-optional-locks", "ls-files"],
                             cwd=root, capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip() or "git ls-files failed")
        rels = [r for r in out.stdout.split("\n") if r.strip()]
    except Exception as exc:                      # noqa: BLE001 -- fail loud
        print("!! cannot ask git what is tracked (%s)." % exc)
        print("   REFUSING to fall back to a filesystem walk: it would report")
        print("   ignored files as public and overstate the exposure.")
        return 2
    for rel in rels:
            p = os.path.join(root, rel)
            if not os.path.isfile(p):
                continue
            if os.path.splitext(rel)[1].lower() not in SCAN_EXT:
                continue
            try:
                t = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            mob = set(MOBILE.findall(t))
            sec = len(SECRET.findall(t)) + len(BEARER.findall(t))
            if not mob and not sec:
                continue
            why = allowed(rel)
            if why and not sec:
                allowed_hits += 1
                continue
            distinct |= mob
            findings.append((rel, len(mob), sec, why))

    print("=" * 72)
    print("PHI / SECRET SCAN -- no matched value is ever printed")
    print("=" * 72)
    if not findings:
        print("\nCLEAN. Nothing outside the allowlist.")
        print(f"({allowed_hits} file(s) matched but are allowlisted with a stated reason.)")
        return 0
    print(f"\n{len(findings)} file(s) to look at. {len(distinct)} distinct mobile-shaped number(s).\n")
    for rel, nm, ns, why in sorted(findings, key=lambda x: -x[1]):
        bits = []
        if nm: bits.append(f"{nm} mobile-shaped")
        if ns: bits.append(f"{ns} SECRET-SHAPED")
        print(f"  {', '.join(bits):32}  {rel}")
    print(f"\n({allowed_hits} other file(s) allowlisted with a stated reason.)")
    print("\nA file here is not automatically a breach -- it is a file nobody has")
    print("ruled on. Either clear it and add an ALLOWLIST entry WITH A REASON, or")
    print("move it out of the tree. Do not widen the allowlist to make this quiet.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
