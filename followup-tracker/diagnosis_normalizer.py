"""
diagnosis_normalizer.py
Dr. Manoj Agarwal Clinic — Orthopedic Diagnosis Normalization Engine

Grounded in the doctor's own Orthopedic_Diagnosis_Taxonomy_Master.xlsx
(27 standardized diagnoses + normalization rules), extended with 12 gap-filling
terms and an administrative-code extractor (CC / PD / BID / VIP).

PUBLIC ENTRY POINT
------------------
normalise_diagnosis(raw_text) -> dict with keys:
    Diagnosis_Raw            cleaned clinical text after admin codes stripped
    Standardized_Diagnosis   one of the 27 taxonomy diagnoses, or 'Other / Unclassified'
    Diagnosis_Category       taxonomy category, or 'Unclassified'
    Diagnosis_Priority       A / B / C / D  (A = most urgent for follow-up)
    Diagnosis_Status         Confirmed / Suspected
    Admin_CC                 consultation charge in rupees (int) or '' — LITERAL number
    Admin_PD                 pharmacy discount %  (int) or ''           — LITERAL number
    Admin_BID                blood-investigation discount % (int) or ''  — LITERAL number
    Is_VIP                   bool — reception/caller alert flag

DESIGN NOTES
------------
* Admin codes are STRIPPED before any clinical matching, so they never pollute
  the diagnosis. CC/PD/BID numbers are taken LITERALLY (CC 5 -> 5, CC 500 -> 500).
* Clinical matching is POSITION-AWARE: when a string contains two conditions
  ("OSTEOARTHRITIS KNEE and INJURY LEFT KNEE"), the FIRST-written (primary)
  diagnosis wins, not whichever tuple happens to be listed first.
* Abbreviations (THR, TKR, ACL, etc.) are matched on WORD BOUNDARIES so that,
  e.g., "THR" never matches inside "ARTHRITIS".
* To add a future diagnosis: append one (keyword, standardized) tuple to
  TAXONOMY. No retraining, no database change.
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
# 1.  STANDARDIZED DIAGNOSIS  ->  CATEGORY      (from the doctor's master sheet)
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY = {
    "Inflammatory Arthritis":                    "Rheumatology",
    "Inflammatory Spondyloarthropathy":          "Rheumatology / Spine",
    "Cervical Mechanical Pain Syndrome":         "Mechanical Spine",
    "Cervical Degenerative Disease":             "Degenerative Spine",
    "Cervical Radiculopathy":                    "Radicular Spine Disease",
    "Lumbar Mechanical Pain Syndrome":           "Mechanical Spine",
    "Lumbar Degenerative Disease":               "Degenerative Spine",
    "Lumbar Radiculopathy / Sciatica":           "Radicular Spine Disease",
    "Knee Osteoarthritis":                       "Degenerative Joint Disease",
    "Bilateral Knee Osteoarthritis":             "Degenerative Joint Disease",
    "Knee Internal Derangement":                 "Sports / Knee Injury",
    "Shoulder Degenerative Disorder":            "Degenerative Joint Disease",
    "Hip Degenerative Disease":                  "Degenerative Joint Disease",
    "Trauma / Fracture":                         "Trauma",
    "Fragility Fracture / Osteoporotic Fracture":"Trauma / Osteoporosis",
    "Hand / Wrist Disorder":                     "Soft Tissue / Nerve Compression",
    "Elbow Soft Tissue Disorder":                "Soft Tissue Disorder",
    "Foot / Heel Pain Syndrome":                 "Foot & Ankle",
    "Pediatric Orthopedic Disorder":             "Pediatric Orthopedics",
    "Osteoporosis / Metabolic Bone Disease":     "Metabolic Bone Disease",
    "Post-Operative Follow-Up":                  "Postoperative Care",
    "Post-Traumatic Stiffness / Rehabilitation": "Rehabilitation",
    "Gouty Arthritis":                           "Rheumatology",
    "Infection / Osteomyelitis":                 "Infection",
    "Tumor / Suspected Tumor":                   "Tumor",
    "Deformity / Alignment Disorder":            "Deformity",
    "General Musculoskeletal Pain":              "General Orthopedics",
}

# ─────────────────────────────────────────────────────────────────────────────
# 2.  CATEGORY / DIAGNOSIS  ->  PRIORITY  (A most urgent ... D unknown)
# ─────────────────────────────────────────────────────────────────────────────
_PRIORITY_BY_CATEGORY = {
    "Trauma": "A", "Trauma / Osteoporosis": "A", "Postoperative Care": "A",
    "Infection": "A", "Tumor": "A",
    "Rheumatology": "B", "Rheumatology / Spine": "B",
    "Radicular Spine Disease": "B", "Sports / Knee Injury": "B",
    "Degenerative Joint Disease": "C", "Degenerative Spine": "C",
    "Mechanical Spine": "C", "Soft Tissue / Nerve Compression": "C",
    "Soft Tissue Disorder": "C", "Foot & Ankle": "C",
    "Metabolic Bone Disease": "C", "Rehabilitation": "C",
    "Deformity": "C", "Pediatric Orthopedics": "C",
    "General Orthopedics": "C",
    "Unclassified": "D",
}
# Standardized-diagnosis overrides (surgical-candidate cohorts → Priority B)
_PRIORITY_OVERRIDE = {
    "Bilateral Knee Osteoarthritis": "B",
    "Hip Degenerative Disease":      "B",
}

def _priority(standardized, category):
    if standardized in _PRIORITY_OVERRIDE:
        return _PRIORITY_OVERRIDE[standardized]
    return _PRIORITY_BY_CATEGORY.get(category, "D")

# ─────────────────────────────────────────────────────────────────────────────
# 3.  TAXONOMY  — ordered (keyword, standardized_diagnosis)
#     Specific phrases first; generic catch-alls last.
#     Matching is position-aware (earliest in the raw string wins).
#     *** To add a future diagnosis, append one line here. ***
# ─────────────────────────────────────────────────────────────────────────────
TAXONOMY = [
    # --- Post-operative (done surgery being followed up) ---
    ("POST OPERATIVE",                  "Post-Operative Follow-Up"),
    ("POST-OPERATIVE",                  "Post-Operative Follow-Up"),
    ("POST OP",                         "Post-Operative Follow-Up"),

    # --- Knee: arthritis-with-knee must beat generic ARTHRITIS ---
    ("OSTEOARTHRITIS KNEE",             "Knee Osteoarthritis"),
    ("OA KNEE",                         "Knee Osteoarthritis"),
    ("KNEE OSTEOARTHRITIS",             "Knee Osteoarthritis"),
    ("KNEE OA",                         "Knee Osteoarthritis"),
    ("ARTHRITIS KNEE",                  "Knee Osteoarthritis"),
    ("ARTHRITIS BOTH KNEE",             "Bilateral Knee Osteoarthritis"),
    ("OSTEOARTHRITIS BOTH KNEE",        "Bilateral Knee Osteoarthritis"),
    ("GONARTHROSIS",                    "Knee Osteoarthritis"),

    # --- Knee internal derangement / sports ---
    ("MENISCUS",                        "Knee Internal Derangement"),
    ("MENISCAL",                        "Knee Internal Derangement"),
    ("INTERNAL DERANGEMENT",            "Knee Internal Derangement"),
    ("DISLOCATION PATELLA",             "Knee Internal Derangement"),         # +ADD (recurrent patellar instability)
    ("PATELLA DISLOCATION",             "Knee Internal Derangement"),         # +ADD
    ("EFFUSION",                        "Knee Internal Derangement"),         # +ADD (knee effusion)

    # --- Shoulder ---
    ("FROZEN SHOULDER",                 "Shoulder Degenerative Disorder"),
    ("ADHESIVE CAPSULITIS",             "Shoulder Degenerative Disorder"),
    ("CAPSULITIS",                       "Shoulder Degenerative Disorder"),    # +ADD (catches misspellings, post-traumatic)
    ("PERIARTHRITIS SHOULDER",          "Shoulder Degenerative Disorder"),
    ("ROTATOR CUFF",                    "Shoulder Degenerative Disorder"),

    # --- Hip ---
    ("AVN HIP",                         "Hip Degenerative Disease"),
    ("AVASCULAR NECROSIS",              "Hip Degenerative Disease"),
    ("OA HIP",                          "Hip Degenerative Disease"),
    ("OSTEOARTHRITIS HIP",              "Hip Degenerative Disease"),
    ("HIP OSTEOARTHRITIS",              "Hip Degenerative Disease"),

    # --- Cervical spine ---
    ("CERVICAL SPONDYLOSIS",            "Cervical Degenerative Disease"),
    ("CERVICOBRACHALGIA",               "Cervical Radiculopathy"),
    ("CERVICAL RADICULOPATHY",          "Cervical Radiculopathy"),
    ("CERVICAL ROOT",                   "Cervical Radiculopathy"),
    ("CERVICAL DISC PROLAPSE",          "Cervical Radiculopathy"),      # +ADD
    ("CERVICAL DISC",                   "Cervical Radiculopathy"),      # +ADD
    ("CERVICAL SPRAIN",                 "Cervical Mechanical Pain Syndrome"),  # +ADD
    ("CERVICAL STRAIN",                 "Cervical Mechanical Pain Syndrome"),  # +ADD (doctor's term)
    ("CERVICAL PAIN",                   "Cervical Mechanical Pain Syndrome"),  # +ADD
    ("MECHANICAL CERVICAL",             "Cervical Mechanical Pain Syndrome"),
    ("NECK PAIN",                       "Cervical Mechanical Pain Syndrome"),

    # --- Lumbar spine ---
    ("LUMBAR SPONDYLOSIS",              "Lumbar Degenerative Disease"),
    ("SPONDYLOLISTHESIS",               "Lumbar Radiculopathy / Sciatica"),  # +ADD
    ("PIVD",                            "Lumbar Radiculopathy / Sciatica"),
    ("SCIATICA",                        "Lumbar Radiculopathy / Sciatica"),
    ("SLIP DISC",                       "Lumbar Radiculopathy / Sciatica"),
    ("PROLAPSED INTERVERTEBRAL",        "Lumbar Radiculopathy / Sciatica"),
    ("RADICULOPATHY",                   "Lumbar Radiculopathy / Sciatica"),
    ("CANAL STENOSIS",                  "Lumbar Radiculopathy / Sciatica"),
    ("LUMBAR STRAIN",                   "Lumbar Mechanical Pain Syndrome"),    # +ADD
    ("COCCYGEAL PAIN",                  "Lumbar Mechanical Pain Syndrome"),    # +ADD
    ("COCCYDYNIA",                      "Lumbar Mechanical Pain Syndrome"),    # +ADD
    ("ACUTE LUMBAGO",                   "Lumbar Mechanical Pain Syndrome"),
    ("LUMBAGO",                         "Lumbar Mechanical Pain Syndrome"),
    ("CLBA",                            "Lumbar Mechanical Pain Syndrome"),
    ("LOW BACK PAIN",                   "Lumbar Mechanical Pain Syndrome"),
    ("LOW BACK ACHE",                   "Lumbar Mechanical Pain Syndrome"),
    ("MECHANICAL BACK",                 "Lumbar Mechanical Pain Syndrome"),
    ("BACKACHE",                        "Lumbar Mechanical Pain Syndrome"),
    ("BACK ACHE",                       "Lumbar Mechanical Pain Syndrome"),    # +ADD (with space)
    ("PAIN IN BACK",                    "Lumbar Mechanical Pain Syndrome"),    # +ADD
    ("LBA",                             "Lumbar Mechanical Pain Syndrome"),    # +ADD (low back ache)
    ("BACK PAIN",                       "Lumbar Mechanical Pain Syndrome"),    # +ADD

    # --- Inflammatory rheumatology ---
    ("ANKYLOSING SPONDYLITIS",          "Inflammatory Spondyloarthropathy"),
    ("HLA-B27",                         "Inflammatory Spondyloarthropathy"),
    ("HLA B27",                         "Inflammatory Spondyloarthropathy"),
    ("SACROILIITIS",                    "Inflammatory Spondyloarthropathy"),  # +ADD
    ("SACROILEITIS",                    "Inflammatory Spondyloarthropathy"),  # +ADD (doctor's spelling)
    ("SPONDYLOARTHROPATHY",             "Inflammatory Spondyloarthropathy"),  # +ADD
    ("SPONDYLARTHROPATHY",              "Inflammatory Spondyloarthropathy"),  # +ADD (doctor's spelling)
    ("SPONDYLOARTHOPATHY",              "Inflammatory Spondyloarthropathy"),  # +ADD (missing-R spelling)
    ("SERONEGATIVE SPONDYL",            "Inflammatory Spondyloarthropathy"),  # +ADD
    ("RHEUMATOID",                      "Inflammatory Arthritis"),
    ("CCP POSITIVE",                    "Inflammatory Arthritis"),
    ("ANA POSITIVE",                    "Inflammatory Arthritis"),
    ("POLYARTHRITIS",                   "Inflammatory Arthritis"),
    ("POLYARTHRALGIA",                  "Inflammatory Arthritis"),
    ("MCTD",                            "Inflammatory Arthritis"),             # +ADD (mixed connective tissue disease)
    ("MIXED CONNECTIVE TISSUE",         "Inflammatory Arthritis"),             # +ADD
    ("CONNECTIVE TISSUE DISORDER",      "Inflammatory Arthritis"),             # +ADD

    # --- Gout ---
    ("GOUTY",                           "Gouty Arthritis"),
    ("GOUT",                            "Gouty Arthritis"),
    ("HYPERURICEMIA",                   "Gouty Arthritis"),                    # +ADD (precursor to gout)
    ("HYPERURICAEMIA",                  "Gouty Arthritis"),                    # +ADD

    # --- Hand / wrist / elbow soft tissue ---
    ("DE QUERVAIN",                     "Hand / Wrist Disorder"),              # +ADD
    ("DEQUERVAIN",                      "Hand / Wrist Disorder"),              # +ADD
    ("GANGLION",                        "Hand / Wrist Disorder"),              # +ADD
    ("TRIGGER FINGER",                  "Hand / Wrist Disorder"),
    ("TRIGGER THUMB",                   "Hand / Wrist Disorder"),              # +ADD
    ("TENOSYNOVITIS",                   "Hand / Wrist Disorder"),              # +ADD (stenosing / de quervain's)
    ("KIENBOCK",                        "Hand / Wrist Disorder"),              # +ADD (lunate AVN)
    ("KEINBOCK",                        "Hand / Wrist Disorder"),              # +ADD (doctor's spelling)
    ("CARPAL TUNNEL",                   "Hand / Wrist Disorder"),
    ("TENNIS ELBOW",                    "Elbow Soft Tissue Disorder"),
    ("LATERAL EPICONDYLITIS",           "Elbow Soft Tissue Disorder"),
    ("GOLFER",                          "Elbow Soft Tissue Disorder"),
    ("MEDIAL EPICONDYLITIS",            "Elbow Soft Tissue Disorder"),

    # --- Foot & ankle ---
    ("PLANTAR FASCIITIS",               "Foot / Heel Pain Syndrome"),
    ("PLANTAR FASCITIS",                "Foot / Heel Pain Syndrome"),         # +ADD (doctor's spelling)
    ("CALCANEAL SPUR",                  "Foot / Heel Pain Syndrome"),
    ("RETROCALCANEAL BURSITIS",         "Foot / Heel Pain Syndrome"),         # +ADD
    ("RETROCALCAENEAL BURSITIS",        "Foot / Heel Pain Syndrome"),         # +ADD (doctor's spelling)
    ("RCB",                             "Foot / Heel Pain Syndrome"),         # +ADD (retrocalcaneal bursitis abbrev)
    ("PES PLANUS",                      "Foot / Heel Pain Syndrome"),         # +ADD
    ("FLAT FOOT",                       "Foot / Heel Pain Syndrome"),         # +ADD
    ("HEEL PAIN",                       "Foot / Heel Pain Syndrome"),

    # --- Infection ---
    ("POTTS SPINE",                     "Infection / Osteomyelitis"),         # +ADD (TB spine)
    ("POTT'S SPINE",                    "Infection / Osteomyelitis"),         # +ADD
    ("OSTEOMYELITIS",                   "Infection / Osteomyelitis"),
    ("SEPTIC ARTHRITIS",                "Infection / Osteomyelitis"),

    # --- Tumor ---
    ("TUMOR",                           "Tumor / Suspected Tumor"),
    ("TUMOUR",                          "Tumor / Suspected Tumor"),
    ("EWING",                           "Tumor / Suspected Tumor"),
    ("OSTEOSARCOMA",                    "Tumor / Suspected Tumor"),

    # --- Deformity ---
    ("VARUS",                           "Deformity / Alignment Disorder"),
    ("VALGUS",                          "Deformity / Alignment Disorder"),
    ("GENU ",                           "Deformity / Alignment Disorder"),

    # --- Metabolic bone ---
    ("OSTEOPOROSIS",                    "Osteoporosis / Metabolic Bone Disease"),
    ("OSTEOPENIA",                      "Osteoporosis / Metabolic Bone Disease"),
    ("OSTEOMALACIA",                    "Osteoporosis / Metabolic Bone Disease"),  # +ADD
    ("VITAMIN D",                       "Osteoporosis / Metabolic Bone Disease"),
    ("RICKETS",                         "Osteoporosis / Metabolic Bone Disease"),  # +ADD

    # --- Fragility fracture (elderly) ---
    ("NECK FEMUR",                      "Fragility Fracture / Osteoporotic Fracture"),
    ("NECK OF FEMUR",                   "Fragility Fracture / Osteoporotic Fracture"),
    ("INTERTROCHANTERIC",               "Fragility Fracture / Osteoporotic Fracture"),

    # --- Trauma / fracture (generic — kept BELOW knee-OA so OA wins when primary) ---
    ("FRACTURE",                        "Trauma / Fracture"),
    ("SPRAINED ANKLE",                  "Trauma / Fracture"),                 # +ADD
    ("ANKLE SPRAIN",                    "Trauma / Fracture"),                 # +ADD
    ("SPRAIN",                          "Trauma / Fracture"),                 # +ADD
    ("STRAIN",                          "Trauma / Fracture"),                 # +ADD (generic strain; lumbar/cervical handled above)
    ("FRESH TRAUMA",                    "Trauma / Fracture"),                 # +ADD
    ("CONTUSION",                       "Trauma / Fracture"),                 # +ADD
    ("DISLOCATION",                     "Trauma / Fracture"),                 # +ADD (shoulder/IP/PIP; patella handled above)
    ("DISCLOCATION",                    "Trauma / Fracture"),                 # +ADD (doctor's spelling)
    ("SUBLUXATION",                     "Trauma / Fracture"),                 # +ADD
    ("SUBLAXATION",                     "Trauma / Fracture"),                 # +ADD (doctor's spelling)
    ("LIGAMENT INJURY",                 "Trauma / Fracture"),
    ("STI ",                            "Trauma / Fracture"),                 # +ADD soft-tissue injury
    ("SOFT TISSUE INJURY",              "Trauma / Fracture"),                 # +ADD
    ("LER",                             "Trauma / Fracture"),
    ("INJURY",                          "Trauma / Fracture"),
    ("TRAUMA",                          "Trauma / Fracture"),

    # --- Post-operative / implant ---
    ("IMPLANT REMOVAL",                 "Post-Operative Follow-Up"),          # +ADD
    ("IMPLANT EXIT",                    "Post-Operative Follow-Up"),          # +ADD

    # --- Pediatric / congenital ---
    ("CTEV",                            "Pediatric Orthopedic Disorder"),     # +ADD (congenital club foot)
    ("CLUB FOOT",                       "Pediatric Orthopedic Disorder"),     # +ADD
    ("CONGENITAL",                      "Pediatric Orthopedic Disorder"),     # +ADD

    # --- Rehabilitation ---
    ("REHABILITATION",                  "Post-Traumatic Stiffness / Rehabilitation"),
    ("POST FRACTURE STIFFNESS",         "Post-Traumatic Stiffness / Rehabilitation"),

    # --- Generic OA / arthritis (LAST among clinical so specifics win first) ---
    ("OSTEOARTHRITIS",                  "Knee Osteoarthritis"),
    ("ARTHRITIS",                       "Inflammatory Arthritis"),

    # --- Fallback vague MSK pain (doctor's own 'General Musculoskeletal Pain' bucket) ---
    ("MULTIPLE JOINT PAIN",             "General Musculoskeletal Pain"),
    ("PAIN BOTH KNEE",                  "General Musculoskeletal Pain"),       # +ADD
    ("PAIN KNEE",                       "General Musculoskeletal Pain"),       # +ADD (reversed word order)
    ("BOTH KNEE",                       "General Musculoskeletal Pain"),       # +ADD (late fallback)
    ("KNEE PAIN",                       "General Musculoskeletal Pain"),       # +ADD
    ("ARTHRALGIA",                      "General Musculoskeletal Pain"),       # +ADD (joint pain, non-specific)
    ("HIP PAIN",                        "General Musculoskeletal Pain"),       # +ADD
    ("PAIN HIP",                        "General Musculoskeletal Pain"),       # +ADD (reversed)
    ("ANKLE PAIN",                      "General Musculoskeletal Pain"),       # +ADD
    ("PAIN ANKLE",                      "General Musculoskeletal Pain"),       # +ADD
    ("SHOULDER PAIN",                   "General Musculoskeletal Pain"),       # +ADD
    ("PAIN SHOULDER",                   "General Musculoskeletal Pain"),       # +ADD (reversed)
    ("WRIST PAIN",                      "General Musculoskeletal Pain"),       # +ADD
    ("ELBOW PAIN",                      "General Musculoskeletal Pain"),       # +ADD
    ("PAIN ELBOW",                      "General Musculoskeletal Pain"),       # +ADD
    ("FOOT PAIN",                       "General Musculoskeletal Pain"),       # +ADD
    ("PAIN FOOT",                       "General Musculoskeletal Pain"),       # +ADD
    ("TIETZE",                          "General Musculoskeletal Pain"),       # +ADD (costochondritis)
    ("BODY PAIN",                       "General Musculoskeletal Pain"),
    ("JOINT PAIN",                      "General Musculoskeletal Pain"),
]

# Abbreviations / short tokens matched ONLY on word boundaries (avoid substring hits)
_WORD_BOUNDARY_KEYS = {
    "OA KNEE", "KNEE OA", "OA HIP", "PIVD", "CLBA", "LER", "HLA B27",
    "GOUT", "TUMOR", "TUMOUR", "VARUS", "VALGUS", "SPRAIN", "INJURY",
    "TRAUMA", "ARTHRITIS", "RICKETS", "PES PLANUS",
    "STRAIN", "EFFUSION", "RCB", "LBA", "MCTD", "CTEV", "CONGENITAL",
    "DISLOCATION", "SUBLUXATION", "SUBLAXATION", "CAPSULITIS", "TENOSYNOVITIS",
}
# Abbreviations handled separately (expanded then matched)
_ABBREV = [
    ("THR", "Post-Operative Follow-Up"),   # total hip replacement → followed up post-op
    ("TKR", "Post-Operative Follow-Up"),   # total knee replacement → followed up post-op
    ("ACL", "Knee Internal Derangement"),
    ("IDK", "Knee Internal Derangement"),
    ("CTS", "Hand / Wrist Disorder"),
    ("SPRA", "Inflammatory Arthritis"),
    ("AS",  "Inflammatory Spondyloarthropathy"),
    ("AVN", "Hip Degenerative Disease"),
]

SUSPECTED_TOKENS = ["?", "U/O", "SUSPECTED", "SUSPECT", "QUERY", "R/O", "RULE OUT", "PROBABLE"]

# ─────────────────────────────────────────────────────────────────────────────
# 4.  ADMINISTRATIVE-CODE EXTRACTION  (CC / PD / BID / VIP)
# ─────────────────────────────────────────────────────────────────────────────
_CC_RE  = re.compile(r"\bCC[\s:.-]*0*([0-9]+)\b", re.IGNORECASE)
_PD_RE  = re.compile(r"\bPD[\s:.-]*0*([0-9]+)\b", re.IGNORECASE)
_BID_RE = re.compile(r"\bBID[\s:.-]*0*([0-9]+)\b", re.IGNORECASE)
_VIP_RE = re.compile(r"\bVIP\b", re.IGNORECASE)

def extract_admin_codes(text):
    """Pull CC/PD/BID/VIP out of the free-text field. Numbers are LITERAL.
    Returns (clean_text_without_codes, admin_dict)."""
    admin = {"Admin_CC": "", "Admin_PD": "", "Admin_BID": "", "Is_VIP": False}
    if not text:
        return "", admin
    s = str(text)

    # CC = consultation charge (rupees); PD / BID = discount percentages.
    # Record only sane values so a misaligned digit-run ('PD97516') is ignored;
    # the matched token is still stripped so it never reaches clinical matching.
    m = _CC_RE.search(s)
    if m:
        v = int(m.group(1))
        if 0 <= v <= 5000:
            admin["Admin_CC"] = v
        s = _CC_RE.sub(" ", s)
    m = _PD_RE.search(s)
    if m:
        v = int(m.group(1))
        if 0 <= v <= 100:
            admin["Admin_PD"] = v
        s = _PD_RE.sub(" ", s)
    m = _BID_RE.search(s)
    if m:
        v = int(m.group(1))
        if 0 <= v <= 100:
            admin["Admin_BID"] = v
        s = _BID_RE.sub(" ", s)
    if _VIP_RE.search(s):
        admin["Is_VIP"] = True
        s = _VIP_RE.sub(" ", s)
    # VIP implies a complimentary (zero) consultation charge unless an explicit CC was given
    if admin["Is_VIP"] and admin["Admin_CC"] == "":
        admin["Admin_CC"] = 0
    # "Complimentary" (any spelling) means a free consultation -> CC 0
    if re.search(r"\bcomplim", s, re.IGNORECASE):
        if admin["Admin_CC"] == "":
            admin["Admin_CC"] = 0
        s = re.sub(r"\bcomplim\w*", " ", s, flags=re.IGNORECASE)

    # tidy leftover connectors ("SPRA and  ; ," -> "SPRA")
    s = re.sub(r"\s+(and|AND|;|,)\s*$", "", s.strip())
    s = re.sub(r"^\s*(and|AND|;|,)\s+", "", s.strip())
    s = re.sub(r"\s{2,}", " ", s).strip(" ;,.-")
    return s, admin

# ─────────────────────────────────────────────────────────────────────────────
# 4b.  COMORBIDITY EXTRACTION  (second axis — for NK Pathology package targeting)
#      Comorbidities co-exist with the orthopedic diagnosis. They are pulled out
#      first so they never block the clinical match, and recorded separately.
#      e.g. "TRIGGER THUMB AND DIABETES MELLITUS"
#            -> Diagnosis = Hand/Wrist Disorder ; Comorbidities = Diabetes
# ─────────────────────────────────────────────────────────────────────────────
# (regex pattern, canonical label).  Order matters: longer/CAD phrases first.
COMORBIDITY_PATTERNS = [
    (r"\bCAD\b|CORONARY ARTERY|POST[\s-]*CAD|CAD[\s-]*POST|ISCHEMIC HEART|\bIHD\b", "CAD"),
    (r"DIABETES MELLITUS|DIABETES|DIABETIC|\bDM\b|\bT2DM\b|\bNIDDM\b|\bIDDM\b",     "Diabetes"),
    (r"HYPERTENSION|HYPERTENSIVE|\bHTN\b",                                          "Hypertension"),
    (r"HYPOTHYROIDISM|HYPOTHYROID",                                                 "Hypothyroidism"),
    (r"HYPERTHYROIDISM|HYPERTHYROID|THYROTOXICOSIS",                                "Hyperthyroidism"),
    (r"DYSLIPID|HYPERLIPID|HIGH CHOLESTEROL",                                       "Dyslipidemia"),
    (r"\bCKD\b|CHRONIC KIDNEY|RENAL FAILURE",                                       "Chronic Kidney Disease"),
    (r"\bCOPD\b|\bASTHMA\b",                                                        "Respiratory (COPD/Asthma)"),
    (r"\bOBESITY\b|MORBIDLY OBESE",                                                 "Obesity"),
]
_COMORBID_RES = [(re.compile(p, re.IGNORECASE), lbl) for p, lbl in COMORBIDITY_PATTERNS]

def extract_comorbidities(text):
    """Return (clean_text_without_comorbidities, [comorbidity_labels])."""
    if not text:
        return "", []
    s = str(text)
    found = []
    for rx, lbl in _COMORBID_RES:
        if rx.search(s):
            if lbl not in found:
                found.append(lbl)
            s = rx.sub(" ", s)
    # tidy leftover connectors after removal
    s = re.sub(r"\b(and|AND|with|WITH|c/o|C/O)\b", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ;,.-")
    return s, found

# ─────────────────────────────────────────────────────────────────────────────
# CONCESSION SCHEME EXTRACTION — the "why" behind CC/PD/BID concessions.
#   These markers travel alongside the CC/PD/BID discount codes / VIP flag,
#   e.g. "OA KNEE and VIP CC 0 PD 10 BID 30" or "CLBA and ARMY PD 10".
#   Pulled out before the clinical match so they never pollute the diagnosis.
# ─────────────────────────────────────────────────────────────────────────────
CONCESSION_PATTERNS = [
    (r"AYUSHMAN|PM[\s-]*JAY|PMJAY|\bPM\s*JAY\b",              "Ayushman (PM-JAY)"),
    (r"\bARMY\b|\bECHS\b|EX[\s-]*SERVICE\w*|\bEXSERVICE\w*\b", "Army / Ex-servicemen (ECHS)"),
    (r"\bCGHS\b",                                              "CGHS"),
    (r"\bESI\b|\bESIC\b",                                      "ESI"),
    (r"\bSTAFF\b|\bEMPLOYEE\b",                                "Staff / Employee"),
    (r"\bCAMP\b",                                              "Camp"),
    (r"\bBPL\b",                                               "BPL"),
]
_CONCESSION_RES = [(re.compile(p, re.IGNORECASE), lbl) for p, lbl in CONCESSION_PATTERNS]

def extract_concession_scheme(text):
    """Return (clean_text_without_scheme_markers, [scheme_labels])."""
    if not text:
        return "", []
    s = str(text)
    found = []
    for rx, lbl in _CONCESSION_RES:
        if rx.search(s):
            if lbl not in found:
                found.append(lbl)
            s = rx.sub(" ", s)
    s = re.sub(r"\b(and|AND|with|WITH|c/o|C/O)\b", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ;,.-")
    return s, found

# ─────────────────────────────────────────────────────────────────────────────
# 4c.  DISCARD TERMS  (junk or non-orthopedic, non-comorbid — drop entirely)
# ─────────────────────────────────────────────────────────────────────────────
DISCARD_EXACT = {"HE", "URTI", "SHE", "PATIENT", "NA", "NIL", "NONE"}
def _is_discard(cleaned):
    up = cleaned.strip().upper()
    if up in DISCARD_EXACT:
        return True
    # pure punctuation / symbol junk e.g. "*(((^^"
    if up and not re.search(r"[A-Z0-9]", up):
        return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
# 5.  CLEANING & STATUS
# ─────────────────────────────────────────────────────────────────────────────
def _clean_raw(text):
    """Strip clinical junk so only the diagnosis phrase(s) remain."""
    s = str(text or "")
    # cut trailing narrative ("... . He was treated with ...", "On examination ...")
    s = re.split(r"\.\s*(?:He|She|Patient|he|she|On examination|On Examination|HE|SHE)\b", s)[0]
    s = re.sub(r"\bComplimentary\b.*$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\bfollowed up\b.*$", "", s, flags=re.IGNORECASE)
    return s.strip(" .;,-")

def _detect_status(text):
    up = str(text).upper()
    for tok in SUSPECTED_TOKENS:
        if tok in up:
            return "Suspected"
    return "Confirmed"

def _preprocess(text):
    """Remove side markers etc.  B/L -> BILATERAL.  Return upper-cased string."""
    s = " " + str(text).upper() + " "
    s = s.replace("B/L", " BILATERAL ").replace("BILAT", " BILATERAL ")
    for side in [" LEFT ", " RIGHT ", " LT ", " RT ", " (LEFT) ", " (RIGHT) ",
                 " L>R ", " R>L ", " C/O "]:
        s = s.replace(side, " ")
    for tok in ["?", "U/O", "SUSPECTED", "SUSPECT"]:
        s = s.replace(tok, " ")
    # drop standalone connector words so "PAIN IN KNEE" -> "PAIN KNEE", "EFFUSION OF KNEE" -> "EFFUSION KNEE"
    s = re.sub(r"\b(IN|OF|THE|A|AN)\b", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s

# ─────────────────────────────────────────────────────────────────────────────
# 6.  POSITION-AWARE MATCH
# ─────────────────────────────────────────────────────────────────────────────
def _match(processed):
    """Return (standardized | None). The earliest-written condition wins; ties
    broken by listing order in TAXONOMY (specific entries appear earlier)."""
    best_pos, best_order, best_std = None, None, None

    for order, (kw, std) in enumerate(TAXONOMY):
        if kw in _WORD_BOUNDARY_KEYS:
            m = re.search(r"\b" + re.escape(kw) + r"\b", processed)
            pos = m.start() if m else -1
        else:
            pos = processed.find(kw)
        if pos != -1:
            if best_pos is None or pos < best_pos or (pos == best_pos and order < best_order):
                best_pos, best_order, best_std = pos, order, std

    # abbreviations (always word-boundary)
    for kw, std in _ABBREV:
        m = re.search(r"\b" + re.escape(kw) + r"\b", processed)
        if m:
            pos = m.start()
            if best_pos is None or pos < best_pos:
                best_pos, best_order, best_std = pos, -1, std

    return best_std

# ─────────────────────────────────────────────────────────────────────────────
# 7.  PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def normalise_diagnosis(raw_text):
    # 1) pull admin codes out first so they never reach clinical matching
    clinical_text, admin = extract_admin_codes(raw_text)

    # 2) pull comorbidities out (second axis) so they never block the clinical match
    clinical_text, comorbidities = extract_comorbidities(clinical_text)

    # 2b) pull concession-scheme markers out (Ayushman / Army / Staff ...)
    clinical_text, schemes = extract_concession_scheme(clinical_text)

    # 3) clean clinical narrative
    cleaned = _clean_raw(clinical_text)

    out = {
        "Diagnosis_Raw":          cleaned,
        "Standardized_Diagnosis": "Other / Unclassified",
        "Diagnosis_Category":     "Unclassified",
        "Diagnosis_Priority":     "D",
        "Diagnosis_Status":       "Confirmed",
        "Comorbidities":          "; ".join(comorbidities),
        "Concession_Scheme":      "; ".join(schemes),
        "Is_Discard":             False,
        **admin,
    }

    if not cleaned:
        # pure admin / pure comorbidity entry — no clinical diagnosis text left
        return out

    if _is_discard(cleaned):
        # junk or non-orthopedic ("HE", "URTI", "*(((^^") — flag for exclusion
        out["Is_Discard"] = True
        out["Diagnosis_Raw"] = cleaned
        return out

    status = _detect_status(clinical_text)
    processed = _preprocess(cleaned)
    std = _match(processed)

    if std:
        cat = CATEGORY.get(std, "Unclassified")
        # "Suspected" only meaningful for non-trauma/non-postop confirmed cohorts
        if status == "Suspected" and std not in (
            "Trauma / Fracture", "Fragility Fracture / Osteoporotic Fracture",
            "Post-Operative Follow-Up"):
            disp = f"{std} (Suspected)"
        else:
            disp = std
            status = "Confirmed"
        out.update({
            "Standardized_Diagnosis": disp,
            "Diagnosis_Category":     cat,
            "Diagnosis_Priority":     _priority(std, cat),
            "Diagnosis_Status":       status,
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 8.  Long-form extractor for Docterz "Patient Medical History" column
# ─────────────────────────────────────────────────────────────────────────────
_DIAG_RE = re.compile(
    r"(?:was diagnosed with|diagnosed with)\s+(.+?)"
    r"(?:\.\s*(?:He|She|Patient|he|she)|\.\s*$|$)",
    re.IGNORECASE)

def extract_diagnosis_from_history(history_text):
    """Pull the diagnosis phrase out of the long-form Docterz narrative:
       'Name, age, sex. He was diagnosed with <DIAGNOSIS>. He was treated with ...'
       Returns '' if the row records treatment only (no formal diagnosis)."""
    if not history_text:
        return ""
    m = _DIAG_RE.search(str(history_text))
    return m.group(1).strip() if m else ""


if __name__ == "__main__":
    tests = [
        "ACUTE LUMBAGO and PD10",
        "OSTEOARTHRITIS KNEE (Bilateral) and INJURY LEFT KNEE",
        "ARTHRITIS BOTH KNEE L>R",
        "Suspected c/o LUMBAR PIVD CC 500 VIP",
        "Followup c/o THR RIGHT HIP",
        "SPRAINED ANKLE RIGHT",
        "SACROILEITIS LEFT WITH EFFUSION",
        "RICKETS",
        "DE QUERVAIN'S TENOSYNOVITIS (Right) BID 50",
        "CC 00 VIP",
        # comorbidity axis
        "TRIGGER THUMB (LEFT) AND DIABETES MELLITUS",
        "HYPERTENSION AND DIABETES MELLITUS",
        "HYPERTENSION, DIABETES MELLITUS AND CAD-POST",
        "DIABETES MELLITUS, HYPERTENSION AND HYPOTHYROIDISM",
        # new clinical additions
        "BILATERAL CTEV",
        "MCTD",
        "OSTEOMALACIA",
        "IMPLANT REMOVAL DONE",
        "RECURRENT DISLOCATION SHOULDER (LEFT)",
        "RECURRENT DISLOCATION PATELLA RIGHT",
        "RCB RIGHT",
        "CHRONIC LBA",
        "COMPLIMENATARY",
        "URTI",
        "*(((^^",
    ]
    for t in tests:
        r = normalise_diagnosis(t)
        cm = f" CO={r['Comorbidities']}" if r['Comorbidities'] else ""
        dc = " [DISCARD]" if r['Is_Discard'] else ""
        print(f"{t:48} -> {r['Standardized_Diagnosis']:40} [{r['Diagnosis_Priority']}]"
              f" CC={r['Admin_CC']}{cm}{dc}")
