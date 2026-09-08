#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""NO_PHONE_NUMBERS.py -- refuse to let a phone number into this repository.

Run from deploy_kits. Exit 0 clean, 1 if a number was found.

THE RULE, AS THE OWNER SETTLED IT ON 28-AUG-2026
    **No PATIENT number in the repository, enforced from that date forward.**

    F-185 previously read "no phone number", and the canon had never satisfied
    it -- 9 distinct numbers across 30 documents, going back to July. **A rule
    the codebase has always violated is a rule people learn to ignore.**

    The date line is not a setting. It is STRUCTURAL: this runs on the STAGED
    file list, so it only ever sees what is being added now. History stays
    exactly as it is, which is what D172 and A0 require anyway.

HOW IT ENFORCES "NO PATIENT NUMBER" WITHOUT BEING ABLE TO RECOGNISE ONE
    Ten digits are ten digits: nothing in the text says whose they are. An
    allowlist of the public ones was tried and thrown away -- it needs editing
    every time a supplier changes, and a list of numbers kept inside the repo
    is the very thing the rule forbids.

    **So the rule enforced is the stronger and simpler one: NO NUMBER AT ALL
    goes into the repository.** That satisfies "no patient number" absolutely
    and needs nothing maintained. Numbers live in the config store beside the
    archive, outside the repo, where the code already reads them from.

    And it is not a hardship, because there are only ever two honest fixes:

      * the number is DATA        -> move it to the config store (see --where)
      * the number is PROSE       -> mask it: 93xxxxxx80 reads the same to a
                                     human and is not a number any more.
                                     `--fix` does that for you, in place.

WHY IT EXISTS AT ALL
    .gitignore blocks
    .csv, .tsv, .xls and .xlsx under its PATIENT-DATA heading. It says nothing
    about .json. On 28-Aug a kit shipped 18 real supplier numbers in a .json
    inside deploy_kits, and nothing between writing it and PUBLISH_ALL would
    have stopped it -- not the F-100 gate, not the SUMS, not a review.

    A rule that depends on somebody remembering it is not a rule. This is the
    rule. Run it before publishing, and let it fail rather than argue with it.

WHAT COUNTS AS A NUMBER
    Ten digits beginning 6-9 (an Indian mobile), with optional +91, spaces or
    hyphens. Deliberately blunt.

WHAT DOES NOT, AND WHY EACH EXCEPTION EXISTS
    * a number whose digits are all the same -- 0000000000 is a placeholder;
    * .md5 files, which are hex by definition;
    * DIGITS INSIDE A HEX TOKEN. Run blind over the canon folder this reports
      444 hits, and almost all of them are md5 fragments: `...77abc12337...`
      inside a checksum is not a phone number. A gate that fires on every
      publish is one somebody waves through within a week, and then it is not a
      gate at all -- the same fault as an expectation that can never be met.

SCOPE -- THE PART THAT MATTERS MOST
    By default this checks ONLY THE FILES GIT IS ABOUT TO COMMIT (--files-from).
    That is the actual risk surface: you cannot publish what you are not
    committing, and everything already in the repository was published long ago.
    Scanning the whole history on every run produces hundreds of hits from canon
    that legitimately QUOTES the shop's own public number inside a Marg report
    header -- noise that buries the one line that matters.

    Pass a path to walk a folder instead, for a deliberate audit.
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Where numbers are allowed to live. Outside the repository, and `_config/` is
# gitignored, so a number put here cannot be committed by accident.
CONFIG_STORE = os.environ.get("SANJ_CONFIG_STORE",
                              "D:\\Downloads\\margsync\\_config")


# Canon that is carried forward, not newly written. A new Archive version is
# new BYTES and old CONTENT: its pre-marker bytes are proven byte-identical to
# the previous version at every close. The owner's 28-Aug ruling says history
# stays, so a number already living in canon is not something being "added"
# today -- but a number that has NEVER been in canon before is, and that is the
# one worth stopping.
HISTORY_DIRS = ("KB_canon_all",)
BASELINE = os.path.join(
    os.environ.get("SANJ_CONFIG_STORE", "D:\\Downloads\\margsync\\_config"),
    "canon_number_baseline.json")


def is_history(path):
    p = path.replace("\\", "/")
    return any(("/%s/" % d) in p or p.startswith("%s/" % d) for d in HISTORY_DIRS)


def fingerprint(d):
    """A number's identity WITHOUT storing the number.

    The baseline has to answer "have we seen this one before" and must not
    itself become a list of phone numbers in a file -- which is the thing the
    whole rule forbids. A salted digest answers the question and stores nothing
    anybody can dial.
    """
    return hashlib.sha256(("canon-baseline-v1:" + d).encode()).hexdigest()[:16]


def load_baseline():
    try:
        return set(json.load(io.open(BASELINE, encoding="utf-8")).get("known", []))
    except (OSError, ValueError):
        return None


def save_baseline(fps, note):
    try:
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        json.dump({"_what": "Fingerprints of numbers ALREADY present in carried-forward "
                            "canon as at the 28-Aug-2026 ruling. Not numbers -- salted "
                            "digests, so this file is not a phone list.",
                   "_note": note, "known": sorted(fps)},
                  io.open(BASELINE, "w", encoding="utf-8"), indent=1)
        return True
    except OSError:
        return False


def digit_span(m):
    """The span of the number itself, without the separators the regex swallowed.

    `[6-9][0-9 -]{9,13}` is greedy, so a match on "<number> for stock" ends
    AFTER the space. Replacing that span ate the space and produced
    "93xxxxxx80for stock". The number ends at its last digit; nothing else in
    the line is ours to touch.
    """
    g = m.group(1)
    trimmed = g.rstrip(" -\t\r\n")
    return m.start(1), m.start(1) + len(trimmed)


def mask(d):
    """a ten-digit mobile -> 93xxxxxx80. Still recognisable to whoever wrote it,
    no longer a number anyone can dial."""
    return d[:2] + "xxxxxx" + d[-2:]
# Separators are SPACE and HYPHEN only -- never \s. With \s in the class a
# "number" could span a line break: "9876543" then "210" on the next line is
# not a phone number, and a match that swallowed the newline also destroyed
# it when masking, joining two lines into one.
NUM = re.compile(r"(?<![0-9])(?:\+?91[ -]?)?([6-9][0-9 -]{9,13})(?![0-9])")
SKIP_EXT = (".md5", ".png", ".jpg", ".gif", ".pdf", ".zip", ".xls", ".xlsx",
            ".pyc", ".mp3", ".wav", ".exe", ".dll")
SKIP_DIR = ("__pycache__", ".git", "node_modules")
MAX_BYTES = 4 * 1024 * 1024   # a file larger than this is not hand-written text


HEX_RUN = re.compile(r"[0-9a-fA-F]{16,}")


def digits(s):
    return re.sub(r"[^0-9]", "", s)


def in_hex_token(text, start, end):
    """True when the match sits inside a long hex run -- an md5, a sha, an id.

    Checked against the SURROUNDING token rather than the match itself: the ten
    digits inside `...c0ffee1234abcd...` are indistinguishable from a mobile until you
    look at what they are embedded in.
    """
    a = start
    while a > 0 and (text[a - 1].isalnum()):
        a -= 1
    b = end
    while b < len(text) and text[b].isalnum():
        b += 1
    token = text[a:b]
    if len(token) < 16:
        return False
    return bool(HEX_RUN.fullmatch(token)) and any(c in "abcdefABCDEF" for c in token)



# =====================================================================
#  THE SECRET LAYER -- S232, and it is the durable half of F-365.
#
#  On 16-Jun-2026 a live MyOperator WhatsApp credential was committed to
#  this PUBLIC repository inside a file called `python test_send.py` -- a
#  filename with a literal space in it, born of a mistyped shell command.
#  It carried the Bearer token, the company ID, the phone-number ID and a
#  real mobile number: a complete, runnable set. It sat there for 84 days
#  and nothing was looking. This is what looks.
#
#  IT IS THE SAME GATE, WIDENED -- NOT A SECOND GATE.
#  One gate in one place, or neither gets maintained.
#
#  WHAT IT REFUSES
#     * Authorization: Bearer <a literal 16+ character token>
#     * -----BEGIN ... PRIVATE KEY-----
#     * a secret-shaped NAME (TOKEN / SECRET / API_KEY / PASSWORD / AUTH /
#       PASSWD / PWD) assigned a STRING LITERAL of meaningful length
#     * and, unchanged, a bare ten-digit number
#
#  WHAT IT MUST NOT REFUSE, OR IT IS SWITCHED OFF WITHIN A WEEK
#  This list is not guesswork. It is the exact false-alarm set measured by
#  the S231 census -- every entry opened and ruled out in context -- and
#  the gate was built against it, so it started life calibrated:
#     os.environ.get("MYOP_AUTH_TOKEN", "")   69 of these; the CORRECT pattern
#     MYOP_TOKEN_KEY = "MYOP_LOGS_TOKEN"      a name held as a constant
#     DEFAULT_DRIVE_TOKEN = "/root/wa/.../drive_token.json"   a path
#     CLIENT_SECRET_FILE = "client_secret.json"               a filename
#     PUT-THE-TOKEN-HERE, PASTE...HERE, <paste the ... token here>,
#     "change-this-password", «MASKED-S230»                   placeholders
#     CRON_TOKEN in 51 files, SECRET/SECRET_PREV in call_hook_capture.py,
#     marg_token=... in the walk harnesses                    selftest fixtures
#     credentials:'same-origin'  (99 hits)                    not a secret name
#     password_hash=?                                         a SQL placeholder
#     md5 pins and hash constants, 16/32/40/64 hex            not credentials
#
#  MEASURED, NOT ASSERTED: over the whole repository this layer reports
#  ZERO. Pointed at the file that actually leaked, it reports ONE.
#
#  NO HISTORY EXEMPTION. The number rule exempts canon carried forward,
#  because the owner ruled on 28-Aug that history stays. A credential is
#  different: it is not history, it is a live key, and if one is ever found
#  in canon the publish SHOULD stop. There is nothing to exempt today --
#  the repository measures zero.
#
#  NOTHING IS EVER PRINTED. A gate that echoes the secret it caught has
#  copied it into a terminal, a scrollback and probably a chat window.
#  Only the kind, the file, the line and the LENGTH are reported.
# =====================================================================

BEARER = re.compile(r"(?i)\bbearer\s+([A-Za-z0-9_\-\.=+/]{16,})")
PRIVKEY = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")
SECRET_ASSIGN = re.compile(
    r"(?i)\b([A-Za-z0-9_]*"
    r"(?:TOKEN|SECRET|API_?KEY|PASSWORD|PASSWD|PWD|AUTH)"
    r"[A-Za-z0-9_]*)['\"]?\s*[:=]\s*(['\"])([^'\"\n]*)\2")

PLACEHOLDER = re.compile(
    r"(?i)(put|paste|here|mask|xxxx|todo|change[-_ ]?(this|me|it)|your[_ -]"
    r"|example|dummy|sample|redact|<|>|«|»|…|\.\.\.)")
ALLCAPS_NAME = re.compile(r"[A-Z][A-Z0-9_]*$")
HASH_PIN = re.compile(r"(?:[0-9a-fA-F]{16}|[0-9a-fA-F]{32}"
                      r"|[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
FILENAME_VAL = re.compile(r"[\w.-]+\.[A-Za-z0-9]{1,6}$")
FILEISH_NAME = re.compile(r"(?i).*(_FILE|_PATH|FILENAME|_DIR)$")

SECRET_MIN = 16   # shorter than this is not a live credential worth a halt

# The keyword must be a WHOLE COMPONENT of the name, not a fragment of a word.
# `author` contains "auth"; it is not a credential, and the first sweep of this
# repository found exactly that one false alarm and nothing else.
SECRET_WORD = re.compile(
    r"(?i)(?:^|[_\-])(token|secret|api_?key|password|passwd|pwd|auth)(?:$|[_\-])")
SECRET_CAMEL = re.compile(
    r"(?:^|[a-z0-9])(Token|Secret|ApiKey|Password|Passwd|Auth)(?:$|[A-Z_\-])")


def name_is_secret_shaped(name):
    return bool(SECRET_WORD.search(name) or SECRET_CAMEL.search(name))



def secret_length_only(v):
    """The ONLY thing this gate is allowed to say about a value."""
    return "(%d chars, not shown)" % len(v)


def benign_secret(name, value):
    """Why this assignment is NOT a credential -- or None if it looks like one.

    Every branch here was earned by a real line in this repository.
    """
    v = value.strip()
    if len(v) < SECRET_MIN:
        return "too short"
    if ALLCAPS_NAME.match(v):
        return "a name held as a constant"
    if "/" in v or "\\" in v:
        return "a path"
    if FILEISH_NAME.match(name) or FILENAME_VAL.match(v):
        return "a filename"
    if PLACEHOLDER.search(v):
        return "a placeholder"
    if HASH_PIN.match(v):
        return "a hash pin"
    if "{" in v or "%s" in v or "$" in v:
        return "interpolated, not a literal"
    return None


def scan_secrets_text(text):
    """[(line, kind, redacted)] -- never the value."""
    out = []
    for m in PRIVKEY.finditer(text):
        out.append((text[:m.start()].count("\n") + 1,
                    "PRIVATE KEY BLOCK", "(a private key, not shown)"))
    for m in BEARER.finditer(text):
        v = m.group(1)
        if PLACEHOLDER.search(v):
            continue
        out.append((text[:m.start()].count("\n") + 1,
                    "Authorization: Bearer", secret_length_only(v)))
    for m in SECRET_ASSIGN.finditer(text):
        name, v = m.group(1), m.group(3)
        if not name_is_secret_shaped(name):
            continue
        if benign_secret(name, v):
            continue
        out.append((text[:m.start()].count("\n") + 1,
                    "%s = <literal>" % name, secret_length_only(v)))
    return out


def _readable(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        return io.open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None


def scan_secrets_files(paths, base):
    hits = []
    for rel in paths:
        path = rel if os.path.isabs(rel) else os.path.join(base, rel)
        if not os.path.isfile(path) or path.lower().endswith(SKIP_EXT):
            continue
        text = _readable(path)
        if text is None:
            continue
        for ln, kind, red in scan_secrets_text(text):
            hits.append((rel, ln, kind, red))
    return hits


def scan_secrets_tree(root):
    hits = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for name in fn:
            if name.lower().endswith(SKIP_EXT):
                continue
            path = os.path.join(dp, name)
            text = _readable(path)
            if text is None:
                continue
            for ln, kind, red in scan_secrets_text(text):
                hits.append((os.path.relpath(path, root), ln, kind, red))
    return hits


def report_secrets(hits):
    """Print and return 1 if anything was found. Never prints a value."""
    if not hits:
        return 0
    print("NO_PHONE_NUMBERS: %d POSSIBLE CREDENTIAL(S) IN WHAT YOU ARE ABOUT "
          "TO PUBLISH." % len(hits))
    print("This repository is PUBLIC. On 16-Jun-2026 a live WhatsApp token went")
    print("in this way and stayed readable for 84 days (F-365).")
    print("")
    print("The fix is always one of two things:")
    print("  a LIVE credential -> take it out of the file, read it from the")
    print("                       environment or from a conf file on the box:")
    print("                       os.environ.get(\"MYOP_AUTH_TOKEN\", \"\")")
    print("  a FIXTURE/EXAMPLE -> make it obviously not real: PUT-THE-TOKEN-HERE")
    print("")
    print("If this gate is wrong, say so and it gets fixed -- do not switch it off.")
    for f, ln, kind, red in hits:
        print("   %-46s line %-5d %-34s %s" % (f[:46], ln, kind[:34], red))
    return 1


def selftest_secrets():
    """Fixtures are BUILT, never written as literals -- a gate whose own source
    trips it is a gate that gets switched off on its first run."""
    tok = "A1b2C3d4E5f6G7h8I9j0K1"
    must_catch = [
        ("Authorization: Bearer " + tok, "a real bearer header"),
        ("-----BEGIN RSA PRIVATE" + " KEY-----", "a private key block"),
        ('MYOP_AUTH_TOKEN = "' + tok + '"', "a token assigned a literal"),
        ("api_key: '" + tok + "'", "a yaml/json api key"),
        ('"password": "' + "s3cretPassw0rdValue" + '"', "a password literal"),
        ('authToken = "' + tok + '"', "a camelCase token"),
        ('apiKey: "' + tok + '"', "a camelCase api key"),
    ]
    must_pass = [
        ('os.environ.get("MYOP_AUTH_TOKEN", "")', "the correct pattern"),
        ('MYOP_TOKEN_KEY = "MYOP_LOGS_TOKEN"', "a name as a constant"),
        ('DEFAULT_DRIVE_TOKEN = "/root/wa/recordings-archive/drive_token.json"', "a path"),
        ('CLIENT_SECRET_FILE = "client_secret.json"', "a filename"),
        ('TOKEN = "PUT-THE-TOKEN-HERE"', "a placeholder"),
        ('DASHBOARD_PASSWORD = "change-this-password"', "an example config"),
        ("MD5_TOKEN = \"0123456789abcdef\"", "a hash fixture"),
        ("credentials:'same-origin'", "a fetch option"),
        ('author = "Dr Manoj Agarwal, Bareilly"', "author -- contains auth, is not auth"),
        ('AUTHORISED_BY = "the owner, in writing, 28-Aug"', "a word beginning AUTH"),
        ('cur.execute("... password_hash=?", (h,))', "a sql placeholder"),
        ('AUTH = "Bearer %s" % tok', "an interpolation"),
        ('CRON_TOKEN = "' + "abc" + '"', "a short fixture"),
    ]
    bad = 0
    for line, why in must_catch:
        if not scan_secrets_text(line):
            print("  FAIL  should have been caught: %s" % why); bad += 1
    for line, why in must_pass:
        got = scan_secrets_text(line)
        if got:
            print("  FAIL  false alarm on %s -> %s" % (why, got[0][1])); bad += 1
    n = len(must_catch) + len(must_pass)
    print("secret layer selftest: %d/%d passed" % (n - bad, n))
    return 0 if bad == 0 else 1


def scan(root):
    hits = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for name in fn:
            if name.lower().endswith(SKIP_EXT):
                continue
            path = os.path.join(dp, name)
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
            except OSError:
                continue
            try:
                text = io.open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for m in NUM.finditer(text):
                d = digits(m.group(1))
                if len(d) != 10:
                    continue
                if len(set(d)) == 1:          # 0000000000 -- a placeholder
                    continue
                if in_hex_token(text, *digit_span(m)):
                    continue                  # an md5 fragment, not a number
                line = text[:m.start()].count("\n") + 1
                hits.append((os.path.relpath(path, root), line, mask(d)))
    return hits


def scan_files(paths, base):
    """Check an explicit list -- what git is about to commit."""
    hits = []
    for rel in paths:
        path = rel if os.path.isabs(rel) else os.path.join(base, rel)
        if not os.path.isfile(path):
            continue
        if path.lower().endswith(SKIP_EXT):
            continue
        try:
            if os.path.getsize(path) > MAX_BYTES:
                continue
            text = io.open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for m in NUM.finditer(text):
            d = digits(m.group(1))
            if len(d) != 10 or len(set(d)) == 1:
                continue
            if in_hex_token(text, *digit_span(m)):
                continue
            line = text[:m.start()].count("\n") + 1
            hits.append((rel, line, mask(d)))
    return hits


def fix_files(paths, base):
    """Mask every number in place. Deliberate, opt-in, and it reports each edit.

    Only ever touches text files it can read and re-write whole, and only when
    something actually changed -- a no-op write would move an mtime for nothing.
    """
    changed = []
    for rel in paths:
        path = rel if os.path.isabs(rel) else os.path.join(base, rel)
        if not os.path.isfile(path) or path.lower().endswith(SKIP_EXT):
            continue
        try:
            if os.path.getsize(path) > MAX_BYTES:
                continue
            text = io.open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        out, last, n = [], 0, 0
        for m in NUM.finditer(text):
            d = digits(m.group(1))
            if len(d) != 10 or len(set(d)) == 1:
                continue
            if in_hex_token(text, *digit_span(m)):
                continue
            a, b = digit_span(m)
            out.append(text[last:a])
            out.append(mask(d))
            last = b
            n += 1
        if not n:
            continue
        out.append(text[last:])
        try:
            io.open(path, "w", encoding="utf-8", newline="").write("".join(out))
            changed.append((rel, n))
        except OSError as e:
            print("   could not rewrite %s: %s" % (rel, e))
    return changed


def main():
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        return selftest_secrets()
    if args and args[0] == "--fix":
        # MASK IN PLACE. Only for prose. If the number is DATA, move the file to
        # the config store instead -- masking data destroys it.
        rest = args[1:]
        if not rest or rest[0] != "--files-from" or len(rest) < 2:
            print("usage: NO_PHONE_NUMBERS.py --fix --files-from <list> [base]")
            return 2
        base = os.path.abspath(rest[2]) if len(rest) > 2 else os.getcwd()
        try:
            paths = [l.strip() for l in io.open(rest[1], encoding="utf-8",
                                                errors="ignore") if l.strip()]
        except OSError as e:
            print("could not read the file list: %s" % e)
            return 2
        changed = fix_files(paths, base)
        if not changed:
            print("NO_PHONE_NUMBERS --fix: nothing to mask.")
            return 0
        print("NO_PHONE_NUMBERS --fix: masked %d number(s) in %d file(s)."
              % (sum(n for _, n in changed), len(changed)))
        for f, n in changed:
            print("   %-52s %d" % (f, n))
        print("")
        print("Read the diff before committing. If any of those was DATA rather than")
        print("prose, masking has destroyed it -- restore the file and move it to")
        print("%s instead." % CONFIG_STORE)
        return 0

    if args and args[0] == "--files-from":
        # THE DEFAULT MODE FOR THE PUBLISH GATE: only what is being committed.
        if len(args) < 2:
            print("--files-from needs a file holding one path per line")
            return 2
        base = os.path.abspath(args[2]) if len(args) > 2 else os.getcwd()
        try:
            paths = [l.strip() for l in io.open(args[1], encoding="utf-8",
                                                errors="ignore") if l.strip()]
        except OSError as e:
            print("could not read the file list: %s" % e)
            return 2
        if not paths:
            print("NO_PHONE_NUMBERS: nothing staged to check.")
            return 0

        # THE SECRET LAYER RUNS FIRST, and both layers are always reported:
        # finding a token and then hiding a phone number behind an early exit
        # would just cost a second publish.
        sec_rc = report_secrets(scan_secrets_files(paths, base))
        if sec_rc:
            print("")

        hits = scan_files(paths, base)

        # Split what was found: new work, versus canon carried forward.
        fresh = [h for h in hits if not is_history(h[0])]
        hist = [h for h in hits if is_history(h[0])]

        if hist:
            known = load_baseline()
            hist_fps = {}
            for rel, ln, masked in hist:
                path = rel if os.path.isabs(rel) else os.path.join(base, rel)
                try:
                    text = io.open(path, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                for m in NUM.finditer(text):
                    d = digits(m.group(1))
                    if len(d) == 10 and len(set(d)) != 1 and not in_hex_token(text, *digit_span(m)):
                        hist_fps[fingerprint(d)] = True
            if known is None:
                save_baseline(list(hist_fps), "established at the S207 close, 28-Aug-2026")
                print("NO_PHONE_NUMBERS: canon baseline established -- %d distinct number(s) "
                      "already in carried-forward history." % len(hist_fps))
                print("   Those are history and are left alone (owner ruling, 28-Aug-2026).")
                print("   A number that has NEVER been in canon will refuse from here on.")
            else:
                new_ones = [f for f in hist_fps if f not in known]
                if new_ones:
                    print("NO_PHONE_NUMBERS: %d NUMBER(S) NEW TO CANON." % len(new_ones))
                    print("History is exempt; something never seen in canon before is not.")
                    for rel, ln, masked in hist:
                        print("   %-52s line %-5d %s" % (rel, ln, masked))
                    return 1
                print("NO_PHONE_NUMBERS: canon carried forward -- %d known number(s), none new."
                      % len(hist_fps))

        hits = fresh
        if not hits:
            if not sec_rc:
                print("NO_PHONE_NUMBERS: clean -- %d staged file(s) checked "
                      "(numbers and credentials)." % len(paths))
            return sec_rc
        print("NO_PHONE_NUMBERS: %d number(s) in what you are about to publish."
              % len(hits))
        print("Rule: NO PATIENT NUMBER, from 28-Aug-2026 (owner, S207) -- enforced as")
        print("no number at all, because nothing in the text says whose a number is.")
        print("")
        print("Two fixes, and both are quick:")
        print("  DATA  -> move the file to the config store:")
        print("           %s" % CONFIG_STORE)
        print("  PROSE -> mask it. Re-run with --fix to do that in place:")
        print("           python NO_PHONE_NUMBERS.py --fix --files-from <list> <base>")
        for f, ln, masked in hits:
            print("   %-52s line %-5d %s" % (f, ln, masked))
        return 1

    # A deliberate audit of a folder. Expect historical noise in canon.
    root = os.path.abspath(args[0]) if args else HERE
    sec_rc = report_secrets(scan_secrets_tree(root))
    if sec_rc:
        print("")
    hits = scan(root)
    if not hits:
        if not sec_rc:
            print("NO_PHONE_NUMBERS: clean -- no contact number and no credential.")
        return sec_rc
    print("NO_PHONE_NUMBERS: %d FOUND. Do not publish." % len(hits))
    print("Move them to the config store beside the archive, outside this repository.")
    for f, ln, masked in hits:
        print("   %-52s line %-5d %s" % (f, ln, masked))
    return 1


if __name__ == "__main__":
    sys.exit(main())
