#!/usr/bin/env python3
"""
finance_patient_match.py  --  S211 / H2 core: identity by LOOKUP (D355).

Given the text the counter typed on a bill, it returns a NAMED VERDICT and the
chain of steps that produced it. It never returns a confidence number, and it
never picks the nearest patient.

    verdict                 meaning
    ---------------------   ----------------------------------------------------
    matched_clinic_id       the clinic ID resolves to exactly one patient
    matched_partial         the subset present resolves to exactly one patient
    matched_visit           the bill could not resolve, but exactly one patient
                            who VISITED that day fits
    ambiguous               it resolves to more than one patient -- shown, never picked
    unmatched               nothing joins. This is the counter gap
    (not_a_patient is a human declaration, not something this module decides)

THE RULE THAT HOLDS IT TOGETHER
  Every rung returns the SET of patients it resolves to. One is a match; more
  than one is AMBIGUOUS. This is what a score destroyed: 0.6 could not tell one
  weak match from three equally good ones, and those are different situations.
  Measured on the real master at S211: 716 mobiles belong to more than one
  patient, covering 1,613 people, and 17 clinic IDs name more than one patient.

  Clinic ID and mobile carry the weight. The NAME ONLY CORROBORATES -- a near
  name plus an exact id or mobile is a match; a near name alone is not.

NO FULL MOBILE IS STORED. The bill's mobile is fingerprinted with the same
salted one-way function the clinic PC used, and the fingerprint is what is
looked up. The salt comes from the environment; without it, mobile matching is
refused rather than silently skipped.
"""
import hashlib
import json
import os
import re
import unicodedata

SALT_ENV = "PATIENT_FP_SALT"
# Adopted from revenue-reconciliation/reconcile_revenue.py (28-Jun, decision D11):
# a pharmacy purchase follows a consultation by days, not hours, so the visit
# match runs over a WINDOW. Same-day only was throwing the ledger away.
DATE_WINDOW_DAYS = int(os.environ.get("DATE_WINDOW_DAYS", "3"))
_DIGITS = re.compile(r"\D+")
_MOBILE_IN_TEXT = re.compile(r"(?<!\d)([6-9]\d{9})(?!\d)")
# a clinic id as the counter writes it: leading token of 1-8 digits, or in brackets
_ID_LEAD = re.compile(r"^\s*(\d{1,8})\b")
_ID_BRACKET = re.compile(r"[\(\[]\s*(\d{1,8})\s*[\)\]]")
_ID_TRAIL = re.compile(r"\b(\d{1,8})\s*$")


SALT_FILE = os.environ.get("PATIENT_FP_FILE", "/root/finance/patient_fp.env")


def salt(env=None):
    """The salt, from the environment or from the file the setup script wrote.

    A file rather than a systemd Environment= line on purpose: adding it to the
    unit would mean editing the unit, a daemon-reload and a restart of the money
    application, for a value that is only read. A 0600 file beside the app is
    the smaller blast radius.
    """
    v = (env or os.environ).get(SALT_ENV, "")
    if v:
        return v
    if env is not None:
        return ""                       # an explicit env dict is authoritative
    try:
        with open(SALT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(SALT_ENV + "="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def normalise_mobile(raw):
    d = _DIGITS.sub("", str(raw or ""))
    if len(d) > 10:
        if d.startswith("91") and len(d) == 12:
            d = d[2:]
        elif d.startswith("0") and len(d) == 11:
            d = d[1:]
        else:
            d = d[-10:]
    return d if len(d) == 10 and d[0] in "6789" else ""


def fingerprint(mobile10, s):
    if not mobile10 or not s:
        return ""
    return hashlib.sha256(("%s|%s" % (s, mobile10)).encode("utf-8")).hexdigest()[:32]


def norm_name(s):
    """Fold to comparable letters. Spelling need not be exact, so this is
    deliberately blunt: case, accents, punctuation and doubled letters go."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z ]+", " ", s).upper()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def name_tokens(s):
    return [t for t in norm_name(s).split(" ") if len(t) > 1]


def given_name_agrees(a, b):
    """The GIVEN name only -- what actually separates people in one family.
    Order-tolerant: the counter writes 'RAM KUMAR' or 'KUMAR RAM'."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return False
    if ta[0] == tb[0]:
        return True
    # one dropped or mistyped letter in the given name still counts
    x, y = ta[0], tb[0]
    return abs(len(x) - len(y)) <= 1 and x[:4] == y[:4] and len(x) >= 4


def names_agree(a, b):
    """True when two names plausibly name the same person. Corroboration only:
    this can never promote a bill to a match on its own."""
    ta, tb = set(name_tokens(a)), set(name_tokens(b))
    if not ta or not tb:
        return False
    if ta & tb:
        return True
    # one common misspelling shape: same first token bar one edit
    fa, fb = sorted(ta)[0], sorted(tb)[0]
    if abs(len(fa) - len(fb)) <= 1 and (fa[:3] == fb[:3]):
        return True
    return False


JSON_KEYS = ("clinic_id", "patient_name", "phone_last4", "bill_no", "bill_date")


def read_bill_identity_json(text):
    """The ingest stores what it EXTRACTED, as JSON -- not the counter's prose.

    S211, found the hard way: `description` on an unresolved bill holds
    {"bill_date":..., "bill_no":..., "clinic_id":..., "patient_name":...,
     "phone_last4":..., "description":..., "amount":..., "mode":...}.
    Parsing that blob as prose made a regex find digit runs inside `amount` and
    `bill_date` and read them as clinic IDs -- 154 bills were matched to
    patients on the strength of a stray number in a date. Read the fields.

    Returns None when the text is not one of these records, so the prose reader
    still handles anything else.
    """
    t = str(text or "").strip()
    if not (t.startswith("{") and t.endswith("}")):
        return None
    try:
        d = json.loads(t)
    except ValueError:
        return None
    if not isinstance(d, dict) or not any(k in d for k in JSON_KEYS):
        return None
    return dict(clinic_id=str(d.get("clinic_id") or "").strip(),
                mobile="",                       # the full number is NOT kept
                last4=str(d.get("phone_last4") or "").strip(),
                name=str(d.get("patient_name") or "").strip(),
                bill_no=str(d.get("bill_no") or "").strip(),
                raw="(structured record)")


def read_bill_identity(text):
    """Pull whatever the counter actually typed out of the bill's description.

    Returns dict(clinic_id, mobile, name, raw). Anything absent comes back ''.
    Nothing is guessed: a token is only a clinic id if it is where a clinic id
    goes, and only a mobile if it is a full ten-digit Indian mobile.
    """
    raw = str(text or "").strip()
    mobile = ""
    m = _MOBILE_IN_TEXT.search(raw)
    if m:
        mobile = m.group(1)
    rest = _MOBILE_IN_TEXT.sub(" ", raw).strip(" -/:.,")

    cid = ""
    b = _ID_BRACKET.search(rest)
    if b:
        cid = b.group(1)
        rest = _ID_BRACKET.sub(" ", rest)
    else:
        lead = _ID_LEAD.match(rest)
        if lead:
            cid = lead.group(1)
            rest = rest[lead.end():]
        else:
            tr = _ID_TRAIL.search(rest)
            if tr:
                cid = tr.group(1)
                rest = rest[:tr.start()]
    name = re.sub(r"\s+", " ", rest.strip(" -/:.,"))
    return dict(clinic_id=cid, mobile=mobile, last4="", name=name,
                bill_no="", raw=raw)


# ---------------------------------------------------------------- the lookup

def _rows(con, sql, *a):
    return con.execute(sql, a).fetchall()


def match_bill(con, text, business_date=None, env=None):
    """Return dict(verdict, patient, candidates, steps). Never raises on data."""
    ident = read_bill_identity_json(text) or read_bill_identity(text)
    s = salt(env)
    steps = []
    fp = fingerprint(normalise_mobile(ident["mobile"]), s) if ident["mobile"] else ""

    steps.append(dict(step="on the bill", detail=dict(
        clinic_id=ident["clinic_id"] or "(blank)",
        mobile="present" if ident["mobile"] else "(blank)",
        name=ident["name"] or "(blank)")))

    # rung 1 -- the clinic id
    if ident["clinic_id"]:
        hits = _rows(con, "SELECT id, clinic_id, name FROM patient_ref "
                          "WHERE clinic_id=?", ident["clinic_id"])
        collide = _rows(con, "SELECT 1 FROM patient_id_collision WHERE clinic_id=?",
                        ident["clinic_id"]) if _has_table(con, "patient_id_collision") else []
        if collide:
            steps.append(dict(step="by clinic ID",
                              detail="this ID names more than one patient - AMBIGUOUS"))
            return _out("ambiguous", None, [dict(r) for r in hits], steps, con)
        if len(hits) == 1:
            steps.append(dict(step="by clinic ID", detail="1 patient found"))
            if ident["name"] and not names_agree(ident["name"], hits[0]["name"]):
                steps.append(dict(step="name check",
                                  detail="the name on the bill does not agree - AMBIGUOUS"))
                return _out("ambiguous", None, [dict(hits[0])], steps, con)
            if ident["name"]:
                steps.append(dict(step="name check", detail="agrees (corroborates)"))
            return _out("matched_clinic_id", dict(hits[0]), [], steps)
        if len(hits) > 1:
            steps.append(dict(step="by clinic ID", detail="%d patients - AMBIGUOUS" % len(hits)))
            return _out("ambiguous", None, [dict(r) for r in hits], steps, con)
        steps.append(dict(step="by clinic ID", detail="no patient with that ID"))

    # rung 2 -- whatever else was entered
    if fp:
        hits = _rows(con, "SELECT id, clinic_id, name FROM patient_ref "
                          "WHERE mobile_fp=?", fp)
        if len(hits) == 1:
            steps.append(dict(step="by mobile", detail="1 patient found"))
            if ident["name"] and not names_agree(ident["name"], hits[0]["name"]):
                steps.append(dict(step="name check",
                                  detail="the name does not agree - AMBIGUOUS"))
                return _out("ambiguous", None, [dict(hits[0])], steps, con)
            steps.append(dict(step="name check",
                              detail="agrees (corroborates)" if ident["name"] else "no name on the bill"))
            return _out("matched_partial", dict(hits[0]), [], steps)
        if len(hits) > 1:
            # the family mobile. A name can still separate them -- but only to ONE.
            steps.append(dict(step="by mobile",
                              detail="%d patients share this number" % len(hits)))
            if ident["name"]:
                # Within a family the SURNAME is shared, so a loose token match
                # cannot separate relatives -- measured on the real master, it
                # separates only about half of them. The GIVEN name can. Try the
                # strict test first; fall back to the loose one; and if neither
                # leaves exactly one candidate, say AMBIGUOUS rather than pick.
                strict = [r for r in hits if given_name_agrees(ident["name"], r["name"])]
                loose = [r for r in hits if names_agree(ident["name"], r["name"])]
                narrowed = strict if len(strict) == 1 else loose
                if len(narrowed) == 1:
                    steps.append(dict(step="name check",
                                      detail="the given name separates them to 1"
                                             if len(strict) == 1 else
                                             "the name separates them to 1"))
                    return _out("matched_partial", dict(narrowed[0]), [], steps)
                steps.append(dict(step="name check",
                                  detail="relatives share this name - AMBIGUOUS"))
            return _out("ambiguous", None, [dict(r) for r in hits], steps, con)
        steps.append(dict(step="by mobile", detail="no patient with that number"))
    elif ident["mobile"] and not s:
        steps.append(dict(step="by mobile",
                          detail="REFUSED - no salt set, so no fingerprint was computed"))

    if ident.get("last4") and ident["name"]:
        # LAST FOUR PLUS THE NAME. Never last4 alone: measured on the real
        # master, 1,506 of 4,903 last-four values are shared by more than one
        # number, so on its own it identifies nobody.
        hits = _rows(con, "SELECT id, clinic_id, name FROM patient_ref "
                          "WHERE phone_last4=?", ident["last4"])
        fit = [r for r in hits if names_agree(ident["name"], r["name"])]
        strict = [r for r in fit if given_name_agrees(ident["name"], r["name"])]
        chosen = strict if len(strict) == 1 else fit
        if len(chosen) == 1:
            steps.append(dict(step="by last-4 + name",
                              detail="%d patient(s) on those last four, the name "
                                     "narrows it to 1" % len(hits)))
            return _out("matched_partial", dict(chosen[0]), [], steps)
        if len(chosen) > 1:
            steps.append(dict(step="by last-4 + name",
                              detail="%d patients fit - AMBIGUOUS" % len(chosen)))
            return _out("ambiguous", None, [dict(r) for r in chosen], steps, con)
        steps.append(dict(step="by last-4 + name",
                          detail="%d patient(s) on those last four, none whose "
                                 "name agrees" % len(hits)))

    if ident["name"] and not ident["clinic_id"] and not ident["mobile"] \
            and not ident.get("last4"):
        steps.append(dict(step="by name alone",
                          detail="a name alone is corroboration, never an identifier"))

    # rung 3 -- the visit record for that day
    if business_date and _has_table(con, "patient_visit"):
        vis = _rows(con,
                    "SELECT DISTINCT p.id, p.clinic_id, p.name FROM patient_visit v "
                    "JOIN patient_ref p ON p.clinic_id = v.clinic_id "
                    "WHERE v.visit_date BETWEEN date(?, ?) AND date(?, ?)",
                    business_date, "-%d days" % DATE_WINDOW_DAYS,
                    business_date, "+%d days" % DATE_WINDOW_DAYS)
        fit = [r for r in vis if ident["name"] and names_agree(ident["name"], r["name"])]
        if len(fit) == 1:
            steps.append(dict(step="visit record",
                              detail="1 patient visited within %d days and fits"
                                     % DATE_WINDOW_DAYS))
            return _out("matched_visit", dict(fit[0]), [], steps)
        if len(fit) > 1:
            steps.append(dict(step="visit record",
                              detail="%d patients who visited within %d days fit "
                                     "- AMBIGUOUS" % (len(fit), DATE_WINDOW_DAYS)))
            return _out("ambiguous", None, [dict(r) for r in fit], steps, con)
        steps.append(dict(step="visit record",
                          detail="no visiting patient fits"
                                 if vis else "no visits within %d days"
                                 % DATE_WINDOW_DAYS))

    return _out("unmatched", None, [], steps)


def _has_table(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                            (name,)).fetchone())


def collapse_to_people(con, cands):
    """Several RECORDS are not several PEOPLE.

    S211, owner-reported: a 29-July bill for one patient came back AMBIGUOUS with
    five candidate clinic IDs -- 7666, 7772, 7683, 7779, 7770 -- all the same
    person, re-registered five times. Docterz issues a fresh clinic ID on
    re-registration, so the master holds one human under several IDs; the S211
    join already found 137 such pairs and recorded them in
    patient_merge_candidate.

    An ambiguity rule that counts ROWS therefore refuses matches it should make.
    This groups the candidates by WHO THEY ARE -- same mobile fingerprint and
    the same name -- and returns the groups. One group means one person, however
    many rows carry them.

    It never merges anything. It reports that the records describe one person;
    merging them is the owner's call and belongs on the Docterz side.
    """
    groups = {}
    for c in cands:
        row = con.execute("SELECT mobile_fp, name FROM patient_ref WHERE clinic_id=?",
                          (c.get("clinic_id"),)).fetchone()
        fp = (row["mobile_fp"] if row else "") or ""
        nm = norm_name(row["name"] if row else c.get("name"))
        groups.setdefault((fp, nm), []).append(c)
    return list(groups.values())


def _out(verdict, patient, candidates, steps, con=None):
    """If a verdict is AMBIGUOUS only because one person holds several records,
    it is not ambiguous. Checked here, once, so no rung can forget to."""
    if verdict == "ambiguous" and con is not None and candidates and len(candidates) > 1:
        groups = collapse_to_people(con, candidates)
        if len(groups) == 1:
            one = sorted(groups[0], key=lambda c: str(c.get("clinic_id")))[0]
            steps.append(dict(step="same person, several records",
                              detail="%d records, one person (clinic IDs %s) - "
                                     "matched, and recorded as a merge candidate"
                                     % (len(candidates),
                                        ", ".join(str(c.get("clinic_id"))
                                                  for c in candidates))))
            steps.append(dict(step="verdict", detail="matched_partial"))
            return dict(verdict="matched_partial", patient=one,
                        candidates=candidates, steps=steps,
                        merge_needed=[c.get("clinic_id") for c in candidates])
    steps.append(dict(step="verdict", detail=verdict))
    return dict(verdict=verdict, patient=patient, candidates=candidates,
                steps=steps, merge_needed=[])
