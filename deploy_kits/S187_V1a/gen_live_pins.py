#!/usr/bin/env python3
# =============================================================================
#  gen_live_pins.py  ·  v1.1  ·  Session 186  ·  the F-110 structural fix
#
#  Builds `live_pins.txt` FROM the KB Register's live-file table.
#
#  WHY IT IS GENERATED, NOT HAND-WRITTEN
#  -------------------------------------
#  A hand-kept second copy of the pins would drift from the Register, and a
#  record that quietly disagrees with another record is precisely the fault
#  this whole exercise exists to close (F-97), and precisely what D202 warns
#  about. So there is exactly ONE authored source -- the Register table -- and
#  the pin list is derived from it. Re-run this whenever the Register changes;
#  the output carries the Register's filename and md5 so the checker can say
#  which record it is holding the box to.
#
#  CLASSIFICATION RULE
#     first cell is marked (superseded) -- a rollback reference        -> DROPPED
#     first cell is a backticked ABSOLUTE path  +  exactly one md5   -> VPS
#     anything else                                                  -> BLIND
#     no md5, but the cell SAYS SO in words ("no file md5")          -> BLIND
#     a row with no md5 and no explanation                           -> ERROR
#
#  A row this script cannot classify STOPS the run. It is never skipped: a
#  silently dropped row is a live file nobody is checking, which is the bug.
#
#  v1.1 -- THE F-110 FIX: THE SOURCE MUST BE THE CANONICAL REGISTER
#  ----------------------------------------------------------------
#  v1.0 recorded which Register it read and that file's md5 -- the right
#  instinct -- but it never checked that the file was the CANONICAL Register.
#  At S183 it was run against an intermediate draft of v5.5 (`ff509b01...`,
#  a hash that matches no file in the repo; canonical v5.5 is `3cad79e6...`),
#  so the pin list shipped to the box carried pre-S183 values for two Marg
#  files. At the S186 open that produced two FALSE drift reds. The list
#  announced its own staleness in its header and nothing was listening.
#
#  So from v1.1 the generator FAILS CLOSED: give it the manifest with
#  --manifest and it will refuse unless the Register you handed it hashes to
#  the md5 the manifest pins as CURRENT. A draft cannot become a pin list by
#  accident any more. If you must generate from a Register version the
#  manifest does not yet pin (the EOS ordering problem -- the new Register
#  exists before the manifest row does), say so out loud with
#  --allow-unpinned-register "reason"; the pin list is then stamped
#  `register_pin_verified: pending` and verify_live_pins.py reports AMBER and
#  refuses to say GREEN until it is regenerated against the rebuilt manifest.
#
#  This runs offline on the PC (or anywhere). It is not installed on the VPS.
#
#  v1.2 -- THE F-122 FIX: NEVER WRITE THE MANIFEST'S WHOLE-FILE HASH
#  -----------------------------------------------------------------
#  v1.1 wrote `# manifest_md5: <md5 of the manifest file at generation time>`.
#  The manifest's whole-file hash is TRANSIENT at every EOS: by its own rule
#  its self-row is "recomputed last", so the file keeps changing after the pin
#  list is generated. Every single generation minted a phantom -- V1b attested
#  to `04eff42c...`, V1c to `78881ddd...`, and neither hash matches any file in
#  any of the repo's 157 commits. A true hash of a state that no longer exists
#  is indistinguishable from an invented one (F-116's footer phantom is the
#  same disease), and verify_live_pins printed it as "VERIFIED" untested
#  (F-117).
#
#  From v1.2 the attestation is the value that is actually STABLE and actually
#  THE CLAIM: `# manifest_current_register_pin: <md5>` -- the md5 the
#  manifest's CURRENT KB_Register row pins, read out of the manifest, equal to
#  the Register's own hash when the verdict is yes. verify_live_pins v1.2 can
#  re-prove that claim on the box from /root/deploy/repo, by hash (D188).
#  The manifest's whole-file md5 is never written anywhere again.
#
#  USAGE
#     python gen_live_pins.py KB_Register_v5_7_S186.md --manifest CANONICAL_MANIFEST.md -o live_pins.txt
#     python gen_live_pins.py KB_Register_v5_7_S186.md --allow-unpinned-register "manifest row lands at EOS"
#     python gen_live_pins.py --selftest
# =============================================================================

import argparse
import hashlib
import os
import re
import shutil
import sys
import tempfile

VERSION = "1.2"

START_MARK = "## CURRENT LIVE FILE VERSIONS"
END_MARK = "## §12 STATE"

MD5_RE = re.compile(r"\b[0-9a-f]{32}\b")

# A row may legitimately have no file hash -- an APPLIED database migration is
# state, not a file on disk. v1.1 accepts that ONLY when the cell says so in
# words. A cell that merely forgot its md5 still stops the run: an explicit
# declaration is classifiable, a silent omission is the bug (D166: the correct
# entry is sometimes UNKNOWN, but it has to be written down as UNKNOWN).
NO_MD5_DECLARED = re.compile(r"no\s+(?:file\s+)?md5|not\s+a\s+file", re.I)

# The Register keeps the PREVIOUS md5 of a live file as a rollback reference,
# marked *(superseded)* in the file column. v1.0 read that as a second live pin
# for the same path -- so the same file was held to two different hashes at
# once and one of them could only ever be DRIFT. A red that can never go green
# is worse than no red: it is the halt that gets waved through (D316).
SUPERSEDED_RE = re.compile(r"\(\s*superseded\s*\)|\bsuperseded\b", re.I)
TICK_RE = re.compile(r"`([^`]+)`")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


MANIFEST_REGISTER_NAME = "KB_Register"


def current_register_pin(manifest_text):
    """
    Find the md5 the manifest pins as the CURRENT KB_Register.

    Deliberately strict: the row's first cell must name exactly `KB_Register`
    (the superseded rows are `KB_Register` (pre-S185) and friends), and its
    notes cell must say CURRENT. Anything ambiguous raises rather than guesses
    -- guessing here is how F-110 happened in the first place.
    """
    found = []
    for line in manifest_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4:
            continue
        name = cells[0].replace("`", "").replace("*", "").strip()
        if name != MANIFEST_REGISTER_NAME:
            continue
        if "CURRENT" not in cells[3].upper():
            continue
        digests = MD5_RE.findall(cells[2])
        if len(digests) != 1:
            raise ValueError("the manifest's CURRENT %s row does not carry "
                             "exactly one md5: %r" % (MANIFEST_REGISTER_NAME, s[:110]))
        found.append((cells[1].replace("`", "").replace("*", "").strip(), digests[0]))
    if not found:
        raise ValueError("no CURRENT `%s` row found in the manifest -- is this "
                         "CANONICAL_MANIFEST.md?" % MANIFEST_REGISTER_NAME)
    if len(found) > 1:
        raise ValueError("the manifest names %d CURRENT %s rows; exactly one is "
                         "required" % (len(found), MANIFEST_REGISTER_NAME))
    return found[0]


def _clean(text):
    """Flatten a Register cell into one short, tab-free note."""
    text = text.replace("`", "").replace("\t", " ").replace("**", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_register(md_text):
    """
    Pull the live-file table out of the Register.
    Returns (vps_rows, blind_rows). Raises ValueError on an unclassifiable row.
    """
    if START_MARK not in md_text:
        raise ValueError("could not find the live-file section (%r) -- is this "
                         "the KB Register?" % START_MARK)
    section = md_text.split(START_MARK, 1)[1]
    if END_MARK in section:
        section = section.split(END_MARK, 1)[0]

    vps, blind, dropped = [], [], []
    for lineno, line in enumerate(section.splitlines(), 1):
        s = line.strip()
        if not s.startswith("|"):
            continue
        if set(s) <= set("|-: "):          # markdown rule row
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() == "file":      # header row
            continue
        if SUPERSEDED_RE.search(cells[0]):
            # a rollback reference, not a live pin -- dropped LOUDLY, never
            # silently: the caller prints every one of these.
            dropped.append({"name": _clean(cells[0])[:70],
                            "note": _clean(cells[2])[:90]})
            continue

        paths = TICK_RE.findall(cells[0])
        digests = MD5_RE.findall(cells[1])

        if not digests:
            if NO_MD5_DECLARED.search(cells[1]):
                blind.append({"md5": "none",
                              "name": _clean(cells[0])[:60],
                              "note": _clean(cells[2])[:110]})
                continue
            raise ValueError(
                "live-file row %d has no md5 and cannot be classified: %r\n"
                "   Fix the Register, or this file goes unchecked.\n"
                "   (If it legitimately has no file hash -- an applied migration,\n"
                "    say -- write that in the md5 cell in words, e.g.\n"
                "    '*(applied marker; no file md5)*', and it becomes BLIND.)"
                % (lineno, s[:110]))

        if paths and paths[0].startswith("/") and len(digests) == 1:
            vps.append({"md5": digests[0], "path": paths[0],
                        "note": _clean(cells[2])[:110]})
        else:
            blind.append({"md5": digests[0] if len(digests) == 1 else "multi",
                          "name": _clean(cells[0])[:60],
                          "note": _clean(cells[2])[:110]})

    if not vps:
        raise ValueError("no VPS-hashable rows found -- refusing to write an "
                         "empty pin list")

    # No path may be pinned twice. Two pins for one file means one of them is
    # guaranteed to fail forever; taking the first would be a guess, and this
    # tool does not guess.
    seen = {}
    for r in vps:
        if r["path"] in seen:
            raise ValueError(
                "the same live path is pinned twice, with %s and %s:\n"
                "   %s\n"
                "   A file can only have one live md5. Mark the older row\n"
                "   *(superseded)* in the Register's file column, or remove it."
                % (seen[r["path"]], r["md5"], r["path"]))
        seen[r["path"]] = r["md5"]
    return vps, blind, dropped


BLIND_REASON = [
    ("VPS_Push_", "Google Apps Script -- lives in Apps Script, not on this box"),
    (".gs", "Google Apps Script -- lives in Apps Script, not on this box"),
    ("migration", "an APPLIED database migration -- state, not a file on disk"),
    ("docterz_report", "PC-side file -- not on this box"),
    ("PC-side", "PC-side file -- not on this box"),
    (".service", "systemd unit -- path not recorded in the Register table"),
]


def reason_for(name, existing_note):
    for needle, why in BLIND_REASON:
        if needle.lower() in name.lower():
            return why
    return existing_note or "not checkable from this machine"


def build(register_path, out_path, session_label, attest):
    with open(register_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    vps, blind, dropped = parse_register(text)

    lines = []
    lines.append("# live_pins.txt -- generated by gen_live_pins.py v%s" % VERSION)
    lines.append("# DO NOT HAND-EDIT the VPS rows. Change the Register, re-run the")
    lines.append("# generator. One authored source (D202).")
    lines.append("# source: %s" % os.path.basename(register_path))
    lines.append("# source_md5: %s" % md5_of(register_path))
    lines.append("# session: %s" % session_label)
    lines.append("# manifest: %s" % attest["manifest"])
    # F-122: the manifest's WHOLE-FILE hash is transient at EOS and is never
    # written. What is written is the claim itself: the md5 the manifest's
    # CURRENT KB_Register row pins -- stable, and re-provable on the box.
    lines.append("# manifest_current_register_pin: %s" % attest["manifest_pin"])
    lines.append("# register_pin_verified: %s" % attest["verdict"])
    lines.append("# columns: kind <TAB> md5 <TAB> path-or-name <TAB> note")
    lines.append("#")
    lines.append("# VPS    = hashed on the box and held to this md5")
    lines.append("# BLIND  = listed every run as NOT verified; never counted as a pass")
    lines.append("# IGNORE = a live file deliberately not pinned; add by hand, with a reason")
    lines.append("")
    for r in vps:
        lines.append("VPS\t%s\t%s\t%s" % (r["md5"], r["path"], r["note"]))
    lines.append("")
    for b in blind:
        lines.append("BLIND\t%s\t%s\t%s"
                     % (b["md5"], b["name"], reason_for(b["name"], b["note"])))
    lines.append("")

    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    return vps, blind, dropped


def selftest():
    """Prove the generator classifies correctly and refuses a row it cannot read."""
    print("gen_live_pins v%s -- selftest" % VERSION)
    checks, failures = 0, []

    def ok(label, cond):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(label)

    a = "a" * 32
    b = "b" * 32
    c = "c" * 32
    good = "\n".join([
        START_MARK + " -- table",
        "| File | md5 | live as of |",
        "|---|---|---|",
        "| `/root/app/one.py` | `%s` | S183 -- a real file |" % a,
        "| `gas/Push.gs` | `%s` | delivered, not wired |" % b,
        "| migrations `X` + `Y` | `%s` · `%s` | applied |" % (a, b),
        "| `docterz_report.py` (PC-side, tracker) | `%s` | PC |" % c,
        "",
        END_MARK,
        "| `/root/app/ignored_after_the_section.py` | `%s` | must not be read |" % a,
    ])
    vps, blind, dropped = parse_register(good)
    ok("one VPS row found", len(vps) == 1)
    ok("VPS row keeps its path", vps[0]["path"] == "/root/app/one.py")
    ok("VPS row keeps its md5", vps[0]["md5"] == a)
    ok("three BLIND rows found", len(blind) == 3)
    ok("a .gs file is BLIND", any("Push.gs" in x["name"] for x in blind))
    ok("a two-md5 migration row is BLIND",
       any(x["md5"] == "multi" for x in blind))
    ok("a PC-side row is BLIND", any("docterz" in x["name"] for x in blind))
    ok("the section END is respected",
       all("ignored_after" not in r["path"] for r in vps))
    ok("blind reasons are filled in", all(x["note"] for x in blind))

    declared = "\n".join([
        START_MARK,
        "| File | md5 | live as of |",
        "|---|---|---|",
        "| `/root/app/one.py` | `%s` | real |" % a,
        "| migration `X_applied` | *(applied marker; no file md5)* | applied |",
        END_MARK,
    ])
    dv, db, dd = parse_register(declared)
    ok("a DECLARED no-md5 row becomes BLIND", len(db) == 1 and db[0]["md5"] == "none")
    ok("a DECLARED no-md5 row keeps its name",
       db and "X_applied" in db[0]["name"])
    ok("a DECLARED no-md5 row does not become VPS", len(dv) == 1)

    sup = "\n".join([
        START_MARK,
        "| File | md5 | live as of |",
        "|---|---|---|",
        "| `/root/app/one.py` | `%s` | S184 current |" % a,
        "| *(superseded)* `/root/app/one.py` | `%s` | S181 rollback ref |" % b,
        END_MARK,
    ])
    sv, sb, sd = parse_register(sup)
    ok("a superseded row is NOT a live pin", len(sv) == 1)
    ok("the live pin survives, with the current md5", sv[0]["md5"] == a)
    ok("the superseded row is reported, not silent", len(sd) == 1)

    dup = "\n".join([
        START_MARK,
        "| File | md5 | live as of |",
        "|---|---|---|",
        "| `/root/app/one.py` | `%s` | current |" % a,
        "| `/root/app/one.py` | `%s` | ALSO current -- an authoring error |" % b,
        END_MARK,
    ])
    try:
        parse_register(dup)
        ok("the same path pinned twice stops the run", False)
    except ValueError:
        ok("the same path pinned twice stops the run", True)

    no_md5 = "\n".join([
        START_MARK,
        "| File | md5 | live as of |",
        "|---|---|---|",
        "| `/root/app/one.py` | (to be measured) | S183 |",
        END_MARK,
    ])
    try:
        parse_register(no_md5)
        ok("a SILENT no-md5 row still stops the run", False)
    except ValueError:
        ok("a SILENT no-md5 row still stops the run", True)

    try:
        parse_register("nothing that looks like a register")
        ok("a non-Register file is refused", False)
    except ValueError:
        ok("a non-Register file is refused", True)

    only_blind = "\n".join([
        START_MARK,
        "| File | md5 | live as of |",
        "|---|---|---|",
        "| `gas/Push.gs` | `%s` | x |" % a,
        END_MARK,
    ])
    try:
        parse_register(only_blind)
        ok("a table with no VPS rows is refused", False)
    except ValueError:
        ok("a table with no VPS rows is refused", True)

    # ---- v1.2 / F-122: the written attestation is the pin, never the file ---
    tmpd = tempfile.mkdtemp(prefix="glp_selftest_")
    try:
        regp = os.path.join(tmpd, "REG.md")
        outp = os.path.join(tmpd, "pins.txt")
        with open(regp, "w", encoding="utf-8") as fh:
            fh.write(good)
        build(regp, outp, "selftest",
              {"manifest": "FAKE_MANIFEST.md", "manifest_pin": "e" * 32,
               "verdict": "yes"})
        with open(outp, "r", encoding="utf-8") as fh:
            written = fh.read()
        ok("the pin list carries manifest_current_register_pin",
           "# manifest_current_register_pin: %s" % ("e" * 32) in written)
        ok("the pin list NEVER carries a whole-file manifest_md5 (F-122)",
           "manifest_md5" not in written)
        ok("the pin list carries its source_md5",
           "# source_md5: " in written)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

    print("  %d/%d checks passed" % (checks - len(failures), checks))
    if failures:
        for f in failures:
            print("  FAILED: %s" % f)
        print("SELFTEST RED")
        return 1
    print("SELFTEST GREEN")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate live_pins.txt from the KB Register's live-file table.")
    ap.add_argument("register", nargs="?", help="path to the KB Register .md")
    ap.add_argument("-o", "--out", default="live_pins.txt")
    ap.add_argument("--session", default="", help="label, e.g. 'S182 close'")
    ap.add_argument("--manifest", default="",
                    help="CANONICAL_MANIFEST.md -- the Register you pass must hash "
                         "to the md5 it pins as CURRENT, or this refuses to run (F-110)")
    ap.add_argument("--allow-unpinned-register", default="", metavar="REASON",
                    help="generate from a Register the manifest does not yet pin. "
                         "Requires a written reason; stamps the list 'pending' so the "
                         "checker reports AMBER until it is regenerated.")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.register:
        ap.error("give me the KB Register .md (or --selftest)")

    # ---- F-110: the source must be the canonical Register, or say why not ---
    if not args.manifest and not args.allow_unpinned_register:
        ap.error("refusing to generate a pin list from an unverified source.\n"
                 "   Pass --manifest CANONICAL_MANIFEST.md so the Register can be\n"
                 "   checked against the md5 the manifest pins as CURRENT, or pass\n"
                 "   --allow-unpinned-register \"reason\" and own it in writing.\n"
                 "   (F-110: at S183 this tool was run against a draft that never\n"
                 "   became canonical, and the box was held to it for three sessions.)")

    attest = {"manifest": "(none)", "manifest_pin": "(none)", "verdict": "no"}
    try:
        reg_md5 = md5_of(args.register)
        if args.manifest:
            with open(args.manifest, "r", encoding="utf-8") as fh:
                man = fh.read()
            ver, pinned = current_register_pin(man)
            attest["manifest"] = os.path.basename(args.manifest)
            attest["manifest_pin"] = pinned
            if pinned != reg_md5:
                sys.stderr.write(
                    "\n!! THE REGISTER YOU GAVE ME IS NOT THE ONE THE MANIFEST PINS\n"
                    "     register file : %s\n"
                    "     its md5       : %s\n"
                    "     manifest pins : %s  (%s, CURRENT)\n\n"
                    "   Refusing to write a pin list from it. This is F-110: a pin\n"
                    "   list generated from a draft holds the box to a record that\n"
                    "   does not exist. Either hand me the canonical Register, or\n"
                    "   pass --allow-unpinned-register \"reason\".\n\n"
                    % (os.path.basename(args.register), reg_md5, pinned, ver))
                return 3
            attest["verdict"] = "yes"
        else:
            attest["verdict"] = "pending: %s" % args.allow_unpinned_register.strip()
    except (ValueError, OSError) as e:
        sys.stderr.write("\n!! %s\n\n" % e)
        return 2

    try:
        vps, blind, dropped = build(args.register, args.out,
                                    args.session or "unlabelled", attest)
    except (ValueError, OSError) as e:
        sys.stderr.write("\n!! %s\n\n" % e)
        return 2

    print("wrote %s" % args.out)
    if attest["verdict"] == "yes":
        print("  register_pin_verified: YES -- matches the manifest's CURRENT pin")
    else:
        print("  register_pin_verified: %s" % attest["verdict"].upper())
        print("  ^ the checker will report AMBER and will NOT say GREEN until this")
        print("    list is regenerated against a manifest that pins this Register.")
    print("  %d VPS rows  (hashed on the box)" % len(vps))
    print("  %d BLIND rows (listed every run as NOT verified)" % len(blind))
    print("  %d rows DROPPED as superseded rollback references (not live pins):"
          % len(dropped))
    for d in dropped:
        print("      %-52s %s" % (d["name"], d["note"][:60]))
    for b in blind:
        print("      %-44s %s" % (b["name"], b["note"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
