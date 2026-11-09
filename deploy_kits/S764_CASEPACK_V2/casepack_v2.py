#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
casepack_v2.py — the Case Pack enquiry v2 stores and routes (kit S764, session S418, the parent, 09-Nov-2026 · D880)
=====================================================================================================================
THE OWNER (10:36–13:32 IST 09-Nov-2026, his mock-ups PNrgan7RNL6Fko4oncFzAs v4 · BLxVkAJ2qt1yZGkUqeQFCE ·
GGyUJWvbHM5fpR91wJpczS): cash packages, the DTH per-day rates and every estimate given are SAVED ON THE SERVER —
the same list on his phone, the clinic PC and Shavez's PC; one editable DTH rates list; general ward and the basic
(SS) implant grade the defaults; charge groups (surgery ₹, stay and case size set once per group, implant ₹ per
fixation; a member may be unlinked); fracture templates by region, each fixation a template that opens the
estimate prefilled; his NET at 50% (a private setting); post-discharge revenue never in the case value.

Registered by casepack_portal.register() right after its own routes, behind the SAME owner-only guard the portal
hands it (casepack_required: the doctor's login, PORTAL_CASEPACK_USERS). Every file lives in CASEPACK_DIR
(/root/wa/casepack — the PHI store, in the encrypted nightly, D270; never in git). This module is the sole writer
of its files; nothing is ever deleted — every save keeps the previous file under cp_history/, dated.

Stores (small JSON files beside tr_dict.json):
  cp_packages.json   {version, saved_at, saved_by, defaults, groups[], packages[]}   seeded ONCE from the page's
                     own cash list (LIVE15 below, the bytes of casepack_page.html f95d186d) and the catalogue
  cp_rates.json      {version, saved_at, saved_by, rates[]}                          the one DTH per-day list
  cp_estimates.jsonl one line per estimate given (patient link, figures, who, when) — append-only; a 'mark'
                     line (taken up / not) references the estimate's id
  cp_settings.json   {share_pct, ...}                                                his eyes only
  cp_history/        every previous cp_packages / cp_rates / cp_settings, dated

Routes (GET unless said; all JSON; all owner-guarded):
  /portal/casepack/packages            the list + groups + defaults (+ POST: full replace, pinned by version)
  /portal/casepack/packages/import     POST — merge a device's localStorage dma_cash_v1 list (one-time, by name)
  /portal/casepack/rates               the DTH list (+ POST: replace, pinned by version)
  /portal/casepack/estimates           ?cid=&n=  newest first (+ POST: append one; POST /mark: taken up or not)
  /portal/casepack/templates           the fracture catalogue (regions → fractures → fixations, SB codes, notes)
  /portal/casepack/settings            (+ POST) share_pct
  /portal/casepack/seed                the seeding page (casepack_seed.html beside the main page)
  /portal/casepack/v2/calc             POST — the arithmetic, one place (the page uses the same formula in JS)
"""
import os, sys, json, re, time, shutil, fcntl, threading
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

CASEPACK_DIR = os.environ.get("PORTAL_CASEPACK_DIR", "/root/wa/casepack")
PKG_FILE  = os.path.join(CASEPACK_DIR, "cp_packages.json")
RATE_FILE = os.path.join(CASEPACK_DIR, "cp_rates.json")
EST_FILE  = os.path.join(CASEPACK_DIR, "cp_estimates.jsonl")
SET_FILE  = os.path.join(CASEPACK_DIR, "cp_settings.json")
HIST_DIR  = os.path.join(CASEPACK_DIR, "cp_history")
LOCK_FILE = os.path.join(CASEPACK_DIR, ".cp_write.lock")
SEED_HTML = os.path.join(CASEPACK_DIR, "casepack_seed.html")

# ----------------------------------------------------------------------------------------------------------------
# THE FIGURES THE OWNER APPROVED (the mock-ups of S416)
# ----------------------------------------------------------------------------------------------------------------
OT_PCT = 0.20                                   # OT charges = 20% of surgery (the page's rule since S172)
SIZE = {"small":  {"anaesthesia": 3000, "otMeds": 2000,  "wardMeds": 1000},
        "medium": {"anaesthesia": 5000, "otMeds": 3000,  "wardMeds": 2500},
        "major":  {"anaesthesia": 6000, "otMeds": 10000, "wardMeds": 5000}}
GRADES = [("eco", "Basic (SS)", 1.0), ("prem", "Premium (Ti)", 1.6), ("imp", "Imported", 2.4)]
GRADE_MULT = {k: m for k, _n, m in GRADES}
DEFAULTS = {"room": "gen", "grade": "eco", "admission": 1200, "carm": 4000, "investigations": 2000, "other": 0}
SETTINGS_DEFAULT = {"share_pct": 50}            # his eyes only (the page shows it under 'only you')
# The guard the portal hands this module is the Case Pack's owner-only gate (PORTAL_CASEPACK_USERS, default manoj). Should that list
# ever widen, his NET and his share stay his: they are sent only to a login named here ('doctor' is the gate's name for the owner's
# legacy trusted device with no SSO user).
OWNERS = set(x.strip().lower() for x in os.environ.get("PORTAL_CASEPACK_OWNERS", "manoj,doctor").split(",") if x.strip())
def is_owner(who): return str(who or "").strip().lower() in OWNERS

# the DTH per-day list — ONE list; ward = a room choice, day = added for every day, opt = per day when ticked
RATES_SEED = [
    {"k": "gen",     "n": "General Ward",   "r": 2000, "t": "ward"},
    {"k": "sp",      "n": "Semi Private",   "r": 3000, "t": "ward"},
    {"k": "pvt",     "n": "Private Room",   "r": 4000, "t": "ward"},
    {"k": "delux",   "n": "Deluxe Room",    "r": 5000, "t": "ward"},
    {"k": "icu",     "n": "ICU",            "r": 5000, "t": "ward"},
    {"k": "visit",   "n": "Doctor visit",   "r": 1000, "t": "day"},
    {"k": "nursing", "n": "Nursing",        "r": 500,  "t": "day"},
    {"k": "hr",      "n": "High-risk care", "r": 1300, "t": "opt"},
]

# His 15 live cash packages — the page's own BUNDLE.cash (casepack_page.html f95d186d), figures as they stand.
# These are the seed's 'have' packages; their heads are kept as they are (size = custom).
LIVE15 = [
 {"name": "DISTAL RADIUS CRIF", "stay": 1, "implant": 2000, "operation": 8000, "carm": 4000, "other": 150, "anaesthesia": 3000, "otMeds": 2000, "wardMeds": 1600, "investigations": 2000, "admission": 1200},
 {"name": "POTTS SPINE", "stay": 3, "implant": 80000, "operation": 50000, "carm": 4000, "other": 1750, "anaesthesia": 6000, "otMeds": 10000, "wardMeds": 8000, "investigations": 2000, "admission": 1200},
 {"name": "IMPLANT REMOVAL", "stay": 1, "implant": 0, "operation": 5000, "carm": 0, "other": 150, "anaesthesia": 3000, "otMeds": 2000, "wardMeds": 800, "investigations": 2000, "admission": 1200},
 {"name": "THR", "stay": 4, "implant": 130000, "operation": 50000, "carm": 4000, "other": 150, "anaesthesia": 6000, "otMeds": 10000, "wardMeds": 8000, "investigations": 2000, "admission": 1200},
 {"name": "THR REVISION", "stay": 4, "implant": 80000, "operation": 50000, "carm": 0, "other": 1150, "anaesthesia": 6000, "otMeds": 10000, "wardMeds": 8000, "investigations": 2000, "admission": 1200},
 {"name": "UNNAMED (was CHARU — rename later)", "stay": 1, "implant": 6000, "operation": 15000, "carm": 4000, "other": 150, "anaesthesia": 4000, "otMeds": 2000, "wardMeds": 800, "investigations": 2000, "admission": 1200, "unnamed": True},
 {"name": "TIBIA PLATE", "stay": 2, "implant": 8000, "operation": 15000, "carm": 4000, "other": 1150, "anaesthesia": 5000, "otMeds": 3000, "wardMeds": 2400, "investigations": 2000, "admission": 1200},
 {"name": "TIBIA ILN", "stay": 1, "implant": 15000, "operation": 15000, "carm": 4000, "other": 1150, "anaesthesia": 3000, "otMeds": 2000, "wardMeds": 1600, "investigations": 2000, "admission": 1200},
 {"name": "PFN", "stay": 1, "implant": 6000, "operation": 20000, "carm": 4000, "other": 1150, "anaesthesia": 4000, "otMeds": 2000, "wardMeds": 1600, "investigations": 2000, "admission": 1200},
 {"name": "CLAVICLE PLATE", "stay": 4, "implant": 8000, "operation": 20000, "carm": 4000, "other": 150, "anaesthesia": 3500, "otMeds": 2000, "wardMeds": 3200, "investigations": 2000, "admission": 1200},
 {"name": "CLAVICLE NAIL", "stay": 1, "implant": 6000, "operation": 10000, "carm": 4000, "other": 150, "anaesthesia": 3500, "otMeds": 2000, "wardMeds": 800, "investigations": 2000, "admission": 1200},
 {"name": "OLECRANON", "stay": 2, "implant": 0, "operation": 10000, "carm": 4000, "other": 150, "anaesthesia": 3000, "otMeds": 2000, "wardMeds": 1600, "investigations": 2000, "admission": 1200},
 {"name": "PROXIMAL TIBIA 1 PLATE", "stay": 5, "implant": 7000, "operation": 11000, "carm": 4000, "other": 0, "anaesthesia": 4000, "otMeds": 3000, "wardMeds": 4000, "investigations": 2000, "admission": 1200},
 {"name": "PROXIMAL TIBIA 2 PLATE", "stay": 5, "implant": 15000, "operation": 20000, "carm": 4000, "other": 0, "anaesthesia": 6000, "otMeds": 4000, "wardMeds": 4000, "investigations": 2000, "admission": 1200},
 {"name": "MODULAR BIPOLAR IMPORTED", "stay": 5, "implant": 85000, "operation": 50000, "carm": 0, "other": 0, "anaesthesia": 6000, "otMeds": 4000, "wardMeds": 4000, "investigations": 0, "admission": 1200},
]

# The charge groups he approved 13:27 IST ("OK"): surgery ₹, stay and size ONCE per group; implant per fixation.
# THR, THR revision and Potts spine stand on their own (no group).
GROUPS_SEED = [
 {"id": "g_small",   "name": "Small bone / percutaneous",       "surgery": 10000, "stay": 1, "size": "small"},
 {"id": "g_ul1",     "name": "Single plate / nail, upper limb",  "surgery": 20000, "stay": 2, "size": "medium"},
 {"id": "g_ulx",     "name": "Complex upper limb",               "surgery": 25000, "stay": 3, "size": "medium"},
 {"id": "g_hipfix",  "name": "Hip fixation",                     "surgery": 20000, "stay": 2, "size": "medium"},
 {"id": "g_hemi",    "name": "Hemiarthroplasty",                 "surgery": 30000, "stay": 3, "size": "medium"},
 {"id": "g_ll1",     "name": "Long bone, lower limb",            "surgery": 20000, "stay": 2, "size": "medium"},
 {"id": "g_llx",     "name": "Complex lower limb",               "surgery": 25000, "stay": 3, "size": "major"},
 {"id": "g_scope",   "name": "Arthroscopy",                      "surgery": 30000, "stay": 2, "size": "medium"},
]

# The fracture catalogue — the fracture-templates mock-up (20 fractures / 46 options + the knee set + the 'also
# common' set he is yet to say yes or no to). Each option: the SB code (HBP 2022, Tier 2 — the rate is read on the
# page from its own BUNDLE.ayush by sub-code), HBP's implant note, the suggested cash figures (surgery, basic
# implant, stay, size — his figures replace them on the seeding page), the charge group, the consent library key
# (casepack_page.html CONSENT_LIB) and the body part / bone the consent and OT list are prefilled with, the OT list
# procedure key, words that find the TPA row, and the live package's name where one exists ('have').
# region, fracture, fixation, sb, note, [surgery, implant, stay, size], group, consent_k, c_part, c_bone, ot_proc, tpa_q, have
C = [
 ("Shoulder girdle · arm", "Clavicle fracture", "Plating", "SB017A", "plate ₹3,000", [20000, 8000, 4, "medium"], "g_ul1", "clavicle", "कंधे", "हँसली की हड्डी", "clavicle", "clavicle", "CLAVICLE PLATE"),
 ("Shoulder girdle · arm", "Clavicle fracture", "Nailing (TENS / clavicle pin)", "SB017A", "plate ₹3,000", [10000, 6000, 1, "small"], "g_small", "clavicle", "कंधे", "हँसली की हड्डी", "clavicle", "clavicle", "CLAVICLE NAIL"),
 ("Shoulder girdle · arm", "Proximal humerus fracture", "PHILOS plating", "SB015C", "locking plate ₹12,000", [20000, 12000, 2, "medium"], "g_ul1", "shoulder", "कंधे", "बाजू की हड्डी का ऊपरी सिरा", "upperlimb", "humerus", None),
 ("Shoulder girdle · arm", "Proximal humerus fracture", "K-wire fixation (percutaneous)", "SB006A", "K-wire ₹250 each · screw ₹1,000 each", [8000, 1500, 1, "small"], "g_small", "shoulder", "कंधे", "बाजू की हड्डी का ऊपरी सिरा", "upperlimb", "humerus", None),
 ("Shoulder girdle · arm", "Proximal humerus fracture", "Greater tuberosity fixation (screws / anchor / TBW)", "SB015C", "locking plate ₹12,000", [12000, 3000, 1, "small"], "g_small", "shoulder", "कंधे", "बाजू की हड्डी का ऊपरी सिरा", "upperlimb", "humerus", None),
 ("Shoulder girdle · arm", "Shaft humerus fracture", "Interlocking nail", "SB010B", "IM nail ₹7,000", [20000, 12000, 2, "medium"], "g_ul1", "humshaft", "बाजू", "बाजू की हड्डी", "upperlimb", "humerus", None),
 ("Shoulder girdle · arm", "Shaft humerus fracture", "Plating", "SB010A", "plate (per HBP note)", [20000, 8000, 2, "medium"], "g_ul1", "humshaft", "बाजू", "बाजू की हड्डी", "upperlimb", "humerus", None),
 ("Shoulder girdle · arm", "Distal humerus fracture (intercondylar)", "Bicondylar plating ± olecranon osteotomy", "SB016A", "TBW + 2 plates ₹11,000", [25000, 15000, 3, "medium"], "g_ulx", "delbow", "कोहनी", "कोहनी के पास बाजू की हड्डी", "upperlimb", "humerus", None),
 ("Elbow · forearm · wrist", "Radial head fracture", "Excision", "SB012B", "—", [10000, 0, 1, "small"], "g_small", "headradius", "कोहनी", "कोहनी के पास हाथ की हड्डी", "upperlimb", "radius", None),
 ("Elbow · forearm · wrist", "Radial head fracture", "Radial head replacement", "SB012C", "prosthesis ₹10,000", [15000, 12000, 2, "small"], "g_ul1", "headradius", "कोहनी", "कोहनी के पास हाथ की हड्डी", "upperlimb", "radius", None),
 ("Elbow · forearm · wrist", "Radial head fracture", "Fixation (Herbert screw / mini plate)", "SB012A", "plate / screw ₹8,000 · Herbert screw", [12000, 5000, 1, "small"], "g_small", "headradius", "कोहनी", "कोहनी के पास हाथ की हड्डी", "upperlimb", "radius", None),
 ("Elbow · forearm · wrist", "Olecranon fracture", "Tension band wiring", "SB030A", "wire ₹2,000", [10000, 0, 2, "small"], "g_small", "generic", "कोहनी", "कोहनी की हड्डी", "upperlimb", "olecranon", "OLECRANON"),
 ("Elbow · forearm · wrist", "Olecranon fracture", "Plating", "SB011A", "plate ₹8,000", [12000, 6000, 2, "small"], "g_ul1", "generic", "कोहनी", "कोहनी की हड्डी", "upperlimb", "olecranon", None),
 ("Elbow · forearm · wrist", "Forearm shaft fracture", "Plating — both bones", "SB014A", "2 plates ₹5,000 · nails ₹2,000 each", [20000, 8000, 2, "medium"], "g_ulx", "forearm", "कोहनी", "हाथ की दोनों हड्डियाँ", "upperlimb", "forearm", None),
 ("Elbow · forearm · wrist", "Forearm shaft fracture", "Plating — single bone (radius or ulna)", "SB013A", "nail ₹2,000 · plate ₹5,000", [12000, 4000, 1, "small"], "g_ul1", "forearm", "कलाई", "हाथ की दोनों हड्डियाँ", "upperlimb", "forearm", None),
 ("Elbow · forearm · wrist", "Forearm shaft fracture", "Nailing (square / TENS)", "SB013A", "nail ₹2,000", [10000, 3000, 1, "small"], "g_small", "forearm", "कलाई", "हाथ की दोनों हड्डियाँ", "upperlimb", "forearm", None),
 ("Elbow · forearm · wrist", "Distal radius fracture", "CRIF — K-wires", "SB006A", "K-wire ₹250 each", [8000, 2000, 1, "small"], "g_small", "dradius", "कलाई", "कलाई के पास हाथ की हड्डी", "upperlimb", "radius", "DISTAL RADIUS CRIF"),
 ("Elbow · forearm · wrist", "Distal radius fracture", "ORIF — volar plate", "SB009A", "locking plate (per HBP note)", [15000, 7000, 1, "small"], "g_ul1", "dradius", "कलाई", "कलाई के पास हाथ की हड्डी", "upperlimb", "radius", None),
 ("Elbow · forearm · wrist", "Distal radius fracture", "External fixator (± K-wires)", "SB005A", "tubular fixator, 6 Schanz pins", [12000, 6000, 1, "small"], "g_ul1", "dradius", "कलाई", "कलाई के पास हाथ की हड्डी", "upperlimb", "radius", None),
 ("Hip · thigh", "Fracture neck of femur", "Cannulated screws (CRIF)", "SB019A", "screws ₹5,000", [15000, 4000, 1, "small"], "g_hipfix", "noffix", "कूल्हे", "जांघ की हड्डी का ऊपरी सिरा (गर्दन)", "lowerlimb", "neck femur", None),
 ("Hip · thigh", "Fracture neck of femur", "Hemiarthroplasty — unipolar (AMP)", "SB031A", "implant ₹4,000", [25000, 6000, 3, "medium"], "g_hemi", "hemi", "कूल्हे", "जांघ की हड्डी का ऊपरी सिरा (गर्दन)", "lowerlimb", "hemi", None),
 ("Hip · thigh", "Fracture neck of femur", "Hemiarthroplasty — bipolar non-modular", "SB031B", "₹8,500 uncemented · cemented per note", [30000, 15000, 3, "medium"], "g_hemi", "hemi", "कूल्हे", "जांघ की हड्डी का ऊपरी सिरा (गर्दन)", "lowerlimb", "hemi", None),
 ("Hip · thigh", "Fracture neck of femur", "Hemiarthroplasty — bipolar modular", "SB031C", "modular cemented ₹20,000 · uncemented per note", [50000, 85000, 5, "major"], "g_hemi", "hemi", "कूल्हे", "जांघ की हड्डी का ऊपरी सिरा (गर्दन)", "lowerlimb", "hemi", "MODULAR BIPOLAR IMPORTED"),
 ("Hip · thigh", "Fracture neck of femur", "Total hip replacement", "SB038A", "cemented ₹40,250 · cementless ₹65,000 · hybrid ₹51,750", [50000, 130000, 4, "major"], None, "thrneck", "कूल्हे", "जांघ की हड्डी का ऊपरी सिरा (गर्दन)", "thr", "hip replacement", "THR"),
 ("Hip · thigh", "Intertrochanteric fracture", "PFN / PFNA2", "SB019C", "PFN ₹8,000", [20000, 6000, 1, "medium"], "g_hipfix", "itfix", "कूल्हे", "जांघ की हड्डी का ऊपरी भाग", "lowerlimb", "femur", "PFN"),
 ("Hip · thigh", "Intertrochanteric fracture", "DHS", "SB019B", "DHS ₹5,000", [20000, 5000, 2, "medium"], "g_hipfix", "itfix", "कूल्हे", "जांघ की हड्डी का ऊपरी भाग", "lowerlimb", "femur", None),
 ("Hip · thigh", "Subtrochanteric fracture", "Long PFN", "SB019C", "PFN ₹8,000", [25000, 9000, 2, "medium"], "g_hipfix", "itfix", "जांघ", "जांघ की हड्डी का ऊपरी भाग", "lowerlimb", "femur", None),
 ("Hip · thigh", "Subtrochanteric fracture", "Proximal femoral locking plate", "SB009A", "locking plate (per HBP note)", [25000, 10000, 3, "medium"], "g_hipfix", "generic", "जांघ", "जांघ की हड्डी का ऊपरी भाग", "lowerlimb", "femur", None),
 ("Hip · thigh", "Shaft femur fracture", "Interlocking nail", "SB010B", "IM nail ₹7,000", [25000, 12000, 2, "medium"], "g_ll1", "femshaft", "जांघ", "जांघ की हड्डी", "lowerlimb", "femur", None),
 ("Hip · thigh", "Shaft femur fracture", "Plating", "SB010A", "plate (per HBP note)", [25000, 9000, 3, "medium"], "g_ll1", "generic", "जांघ", "जांघ की हड्डी", "lowerlimb", "femur", None),
 ("Hip · thigh", "Shaft femur fracture (child)", "Elastic nailing", "SB007A", "elastic nail ₹5,000", [12000, 4000, 1, "small"], "g_small", "femshaft", "जांघ", "जांघ की हड्डी", "lowerlimb", "femur", None),
 ("Hip · thigh", "Distal femur fracture", "Distal femur locking plate", "SB009A", "locking plate (per HBP note)", [25000, 12000, 3, "medium"], "g_llx", "dfemur", "घुटने", "जांघ की हड्डी का निचला सिरा", "lowerlimb", "femur", None),
 ("Hip · thigh", "Distal femur fracture", "Retrograde nail", "SB010B", "IM nail ₹7,000", [25000, 12000, 2, "medium"], "g_ll1", "dfemur", "घुटने", "जांघ की हड्डी का निचला सिरा", "lowerlimb", "femur", None),
 ("Knee · leg · ankle", "Patella fracture", "Tension band wiring", "SB030A", "wire ₹2,000", [12000, 1500, 2, "small"], "g_small", "patella", "घुटने", "घुटने की चपनी", "lowerlimb", "patella", None),
 ("Knee · leg · ankle", "Patella fracture", "Patellectomy (partial / total)", "SB035A", "—", [12000, 0, 2, "small"], "g_small", "patella", "घुटने", "घुटने की चपनी", "lowerlimb", "patella", None),
 ("Knee · leg · ankle", "Proximal tibia fracture (plateau)", "Unicondylar — one plate", "SB009A", "locking plate (per HBP note)", [20000, 7000, 5, "medium"], "g_llx", "ptibia", "घुटने", "पैर की मोटी हड्डी का ऊपरी सिरा", "lowerlimb", "tibia", "PROXIMAL TIBIA 1 PLATE"),
 ("Knee · leg · ankle", "Proximal tibia fracture (plateau)", "Bicondylar — two plates", "SB009A", "locking plate (per HBP note)", [25000, 15000, 5, "major"], "g_llx", "ptibia", "घुटने", "पैर की मोटी हड्डी का ऊपरी सिरा", "lowerlimb", "tibia", "PROXIMAL TIBIA 2 PLATE"),
 ("Knee · leg · ankle", "Shaft tibia fracture", "Interlocking nail", "SB010B", "IM nail ₹7,000", [20000, 15000, 1, "medium"], "g_ll1", "tibshaft", "टांग", "पैर की मोटी हड्डी", "lowerlimb", "tibia", "TIBIA ILN"),
 ("Knee · leg · ankle", "Shaft tibia fracture", "Plating", "SB010A", "plate (per HBP note)", [20000, 8000, 2, "medium"], "g_ll1", "tibshaft", "टांग", "पैर की मोटी हड्डी", "lowerlimb", "tibia", "TIBIA PLATE"),
 ("Knee · leg · ankle", "Shaft tibia fracture (open)", "External fixator", "SB005A", "tubular fixator, 6 Schanz pins", [15000, 7000, 2, "medium"], "g_ll1", "tibshaft", "टांग", "पैर की मोटी हड्डी", "lowerlimb", "tibia", None),
 ("Knee · leg · ankle", "Pilon fracture (distal tibia)", "Plating ± fibula", "SB009A", "locking plate (per HBP note)", [22000, 12000, 3, "medium"], "g_llx", "dtibia", "टांग", "पैर की दोनों हड्डियाँ", "lowerlimb", "tibia", None),
 ("Knee · leg · ankle", "Pilon fracture (distal tibia)", "External fixator / staged", "SB005A", "tubular fixator, 6 Schanz pins", [15000, 7000, 2, "medium"], "g_ll1", "dtibia", "टांग", "पैर की दोनों हड्डियाँ", "lowerlimb", "tibia", None),
 ("Knee · leg · ankle", "Ankle fracture (malleolar)", "ORIF — medial / lateral / bi- / tri-malleolar", "SB020A", "TBW / plate per note", [18000, 7000, 2, "medium"], "g_ll1", "ankle", "गट्टे (टखने)", "टखने की हड्डियाँ", "lowerlimb", "ankle", None),
 ("Knee — arthroscopy & ligaments", "Meniscus", "Arthroscopic repair / menisectomy", "SB036A", "fibre wire for repair", [15000, 5000, 1, "small"], "g_scope", "", "घुटने", "", "acl", "menisc", None),
 ("Knee — arthroscopy & ligaments", "ACL", "Arthroscopic reconstruction", "SB049A", "bio screw / endobutton / suture disc + brace", [30000, 25000, 2, "medium"], "g_scope", "acl", "घुटने", "", "acl", "acl", None),
 ("Knee — arthroscopy & ligaments", "PCL", "Arthroscopic reconstruction", "SB049B", "bio screw / endobutton / suture disc + brace", [30000, 25000, 2, "medium"], "g_scope", "", "घुटने", "", "acl", "pcl", None),
 ("Knee — arthroscopy & ligaments", "Multi-ligament (ACL + PCL / MCL)", "Reconstruction", "SB049A", "both provisions (SB049A + SB049B)", [45000, 45000, 3, "major"], "g_scope", "", "घुटने", "", "acl", "ligament", None),
 ("Knee — arthroscopy & ligaments", "Knee synovitis", "Arthroscopic / open synovectomy", "SB074A", "RF ablation wand ₹18,000", [15000, 3000, 1, "small"], "g_scope", "", "घुटने", "", "acl", "synov", None),
 ("Knee — arthroscopy & ligaments", "Knee", "High tibial osteotomy", "SB057A", "plate ₹7,000 · fixator", [25000, 12000, 3, "medium"], "g_scope", "", "घुटने", "पैर की मोटी हड्डी का ऊपरी सिरा", "lowerlimb", "osteotomy", None),
 ("Also common — say yes or no", "Supracondylar humerus (child)", "K-wires", "SB006A", "K-wire ₹250 each", [8000, 1000, 1, "small"], "g_small", "generic", "कोहनी", "कोहनी के पास बाजू की हड्डी", "upperlimb", "humerus", None),
 ("Also common — say yes or no", "Lateral condyle humerus (child)", "K-wires / screw", "SB015A", "implant ₹1,500", [10000, 1500, 1, "small"], "g_small", "generic", "कोहनी", "कोहनी के पास बाजू की हड्डी", "upperlimb", "humerus", None),
 ("Also common — say yes or no", "Elbow dislocation", "Closed reduction", "SB028C", "—", [5000, 0, 1, "small"], "g_small", "", "कोहनी", "", "upperlimb", "dislocation", None),
 ("Also common — say yes or no", "Implant removal", "Nail / plate under GA", "SB071B", "—", [5000, 0, 1, "small"], None, "implrem", "", "", "implantrem", "implant removal", "IMPLANT REMOVAL"),
 ("Also common — say yes or no", "Implant removal", "K-wire / screw under LA", "SB070A", "—", [3000, 0, 1, "small"], "g_small", "implrem", "", "", "implantrem", "implant removal", None),
]
REGIONS = []
for _row in C:
    if _row[0] not in REGIONS: REGIONS.append(_row[0])

def _slug(s):
    s = re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")
    return s[:48] or "x"

def catalogue():
    """The fracture catalogue as the page and the seeding page read it."""
    out = []
    for i, r in enumerate(C):
        region, fx, fix, sb, note, fig, grp, ck, part, bone, otp, tq, have = r
        out.append({"id": "t%02d_%s_%s" % (i + 1, _slug(fx), _slug(fix)), "region": region, "fx": fx, "fix": fix,
                    "sb": sb, "sb_note": note, "suggest": {"surgery": fig[0], "implant": fig[1], "stay": fig[2], "size": fig[3]},
                    "group": grp, "consent_k": ck, "c_part": part, "c_bone": bone, "ot_proc": otp, "tpa_q": tq,
                    "have": have})
    return {"regions": REGIONS, "options": out, "sizes": SIZE, "grades": [{"k": k, "n": n, "m": m} for k, n, m in GRADES]}

# ----------------------------------------------------------------------------------------------------------------
# THE ARITHMETIC — one place; the page carries the same formula in JS (s764Calc) and the walk proves both agree
# ----------------------------------------------------------------------------------------------------------------
def _n(v, lo=0, hi=5000000):
    try:
        x = int(round(float(v)))
    except Exception:
        return 0
    return max(lo, min(hi, x))

def calc(e, rates, share_pct=50):
    """e: {surgery, implant, grade, stay, room, opts{}, anaesthesia, otMeds, wardMeds, admission, carm,
    investigations, other, discount}. Returns every line and the owner's net.
    His NET (D880): estimate − admission (the hospital keeps it) − the outgoings paid from the lump sum
    (anaesthesia, OT meds, ward meds, implant, investigations) − the discount = the shareable amount; his share
    is share_pct of it. Worked example he approved: PFN, general ward, 2 days → 54,700 → 35,000 → 17,500."""
    by = {r["k"]: r for r in rates}
    stay = max(1, _n(e.get("stay", 1), 1, 60))
    surgery = _n(e.get("surgery")); ot = int(round(surgery * OT_PCT))
    impl_base = _n(e.get("implant"))
    mult = GRADE_MULT.get(e.get("grade") or "eco", 1.0)
    implant = int(round(impl_base * mult))
    an = _n(e.get("anaesthesia")); otm = _n(e.get("otMeds")); wm = _n(e.get("wardMeds"))
    adm = _n(e.get("admission")); carm = _n(e.get("carm")); inv = _n(e.get("investigations")); oth = _n(e.get("other"))
    room_k = e.get("room") or "gen"
    room = by.get(room_k) or next((r for r in rates if r.get("t") == "ward"), None) or {"n": "General Ward", "r": 0, "k": "gen"}
    room_amt = _n(room.get("r")) * stay
    day_lines = [(r["n"], _n(r["r"]) * stay) for r in rates if r.get("t") == "day"]
    opts = e.get("opts") or {}
    opt_lines = [(r["n"], _n(r["r"]) * stay) for r in rates if r.get("t") == "opt" and opts.get(r["k"])]
    day = sum(x[1] for x in day_lines); opt = sum(x[1] for x in opt_lines)
    heads = an + otm + wm + adm + carm + inv + oth
    total = surgery + ot + heads + room_amt + day + opt + implant
    disc = _n(e.get("discount"))
    net_to_patient = max(0, total - disc)
    outgoings = an + otm + wm + implant + inv
    shareable = net_to_patient - adm - outgoings
    my_net = int((shareable * _n(share_pct, 0, 100)) / 100.0 + 0.5) if shareable >= 0 else -int((-shareable * _n(share_pct, 0, 100)) / 100.0 + 0.5)   # half-up, as the page's Math.round
    lines = [("Surgery", surgery), ("OT charges (20%)", ot)]
    if carm: lines.append(("Image / C-arm", carm))
    if adm: lines.append(("Admission", adm))
    lines.append(("%s × %d day%s" % (room["n"], stay, "" if stay == 1 else "s"), room_amt))
    for nm, amt in day_lines: lines.append(("%s × %d" % (nm, stay), amt))
    for nm, amt in opt_lines: lines.append(("%s × %d" % (nm, stay), amt))
    lines.append(("Implant · %s" % dict((k, n) for k, n, _m in GRADES).get(e.get("grade") or "eco", "Basic (SS)"), implant))
    if an: lines.append(("Anaesthesia", an))
    if otm: lines.append(("OT medicines", otm))
    if wm: lines.append(("Ward medicines", wm))
    if inv: lines.append(("Investigations", inv))
    if oth: lines.append(("Other", oth))
    if disc: lines.append(("Discount", -disc))
    return {"surgery": surgery, "ot": ot, "implant": implant, "implant_base": impl_base, "heads": heads,
            "room": room_amt, "room_name": room["n"], "day": day, "opt": opt, "stay": stay, "total": total,
            "discount": disc, "net_to_patient": net_to_patient, "shareable": shareable, "my_net": my_net,
            "share_pct": _n(share_pct, 0, 100), "lines": lines}

# ----------------------------------------------------------------------------------------------------------------
# files
# ----------------------------------------------------------------------------------------------------------------
def _now():
    return datetime.now(IST).isoformat(timespec="seconds")

def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else default
    except Exception:
        return default

_LOCAL = threading.local()

class _Lock(object):
    """One writer at a time across processes (flock) — and RE-ENTRANT within a thread: a save that holds the lock may
    read a store that is still to be seeded without waiting on itself (the cold review's deadlock, S418)."""
    def __enter__(self):
        depth = getattr(_LOCAL, "depth", 0)
        if depth == 0:
            os.makedirs(CASEPACK_DIR, exist_ok=True)
            self.f = open(LOCK_FILE, "a+")
            fcntl.flock(self.f, fcntl.LOCK_EX)
            _LOCAL.f = self.f
        _LOCAL.depth = depth + 1
        return self
    def __exit__(self, *a):
        _LOCAL.depth = getattr(_LOCAL, "depth", 1) - 1
        if _LOCAL.depth <= 0:
            _LOCAL.depth = 0
            try:
                f = getattr(_LOCAL, "f", None)
                if f: fcntl.flock(f, fcntl.LOCK_UN); f.close()
            except Exception:
                pass
            _LOCAL.f = None

def _keep_history(path):
    """The previous file is kept, dated, never deleted (cp_history/<name>.<stamp>)."""
    if not os.path.exists(path): return
    os.makedirs(HIST_DIR, exist_ok=True)
    stamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(HIST_DIR, os.path.basename(path) + "." + stamp)
    n = 0
    while os.path.exists(dst):
        n += 1; dst = os.path.join(HIST_DIR, os.path.basename(path) + "." + stamp + "_%d" % n)
    shutil.copy2(path, dst)

def _write_json(path, obj):
    """Atomic: write beside, fsync, replace. The previous file goes to the history first."""
    os.makedirs(CASEPACK_DIR, exist_ok=True)
    _keep_history(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass

# ----------------------------------------------------------------------------------------------------------------
# packages — the seed, the shape, the save
# ----------------------------------------------------------------------------------------------------------------
PKG_NUM = ("surgery", "implant", "anaesthesia", "otMeds", "wardMeds", "admission", "carm", "investigations", "other")

def _pkg_from_live(p, pid, cat_row=None):
    """A live package of the page (BUNDLE.cash shape) → the v2 shape, heads kept as they are (size = custom)."""
    o = {"id": pid, "name": p["name"], "surgery": _n(p.get("operation")), "implant": _n(p.get("implant")),
         "stay": max(1, _n(p.get("stay", 1), 1, 60)), "size": None,
         "anaesthesia": _n(p.get("anaesthesia")), "otMeds": _n(p.get("otMeds")), "wardMeds": _n(p.get("wardMeds")),
         "admission": _n(p.get("admission", DEFAULTS["admission"])), "carm": _n(p.get("carm")),
         "investigations": _n(p.get("investigations")), "other": _n(p.get("other")),
         "group": None, "own": True, "suggested": False, "retired": False, "unnamed": bool(p.get("unnamed")),
         "region": None, "fx": None, "fix": None, "sb": None, "sb_note": None, "template": None,
         "consent_k": None, "c_part": None, "c_bone": None, "ot_proc": None, "tpa_q": None}
    if cat_row:
        o.update({"region": cat_row["region"], "fx": cat_row["fx"], "fix": cat_row["fix"], "sb": cat_row["sb"],
                  "sb_note": cat_row["sb_note"], "template": cat_row["id"], "group": cat_row["group"],
                  "consent_k": cat_row["consent_k"], "c_part": cat_row["c_part"], "c_bone": cat_row["c_bone"],
                  "ot_proc": cat_row["ot_proc"], "tpa_q": cat_row["tpa_q"]})
    return o

def _pkg_from_template(t, pid):
    s = t["suggest"]; sz = SIZE[s["size"]]
    return {"id": pid, "name": (t["fx"] + " — " + t["fix"]).upper()[:80], "surgery": s["surgery"], "implant": s["implant"],
            "stay": s["stay"], "size": s["size"], "anaesthesia": sz["anaesthesia"], "otMeds": sz["otMeds"],
            "wardMeds": sz["wardMeds"], "admission": DEFAULTS["admission"], "carm": DEFAULTS["carm"],
            "investigations": DEFAULTS["investigations"], "other": 0,
            "group": t["group"], "own": False, "suggested": True, "retired": False, "unnamed": False,
            "region": t["region"], "fx": t["fx"], "fix": t["fix"], "sb": t["sb"], "sb_note": t["sb_note"],
            "template": t["id"], "consent_k": t["consent_k"], "c_part": t["c_part"], "c_bone": t["c_bone"],
            "ot_proc": t["ot_proc"], "tpa_q": t["tpa_q"]}

def seed_packages(live=None):
    """The first fill: his live packages (figures kept, size custom, own figures — marked where they differ from
    their group) + one suggested package per catalogue option without one. Never called twice: the file exists."""
    live = live if live is not None else LIVE15
    cat = catalogue()["options"]
    by_have = {}
    for t in cat:
        if t["have"]: by_have.setdefault(t["have"].upper(), t)
    pkgs = []; n = 0
    seen_live = set()
    for p in live:
        n += 1
        t = by_have.get(str(p.get("name", "")).upper())
        pkgs.append(_pkg_from_live(p, "p%03d" % n, t))
        seen_live.add(str(p.get("name", "")).upper())
    for t in cat:
        if t["have"] and t["have"].upper() in seen_live: continue
        n += 1
        pkgs.append(_pkg_from_template(t, "p%03d" % n))
    for i, p in enumerate(pkgs): p["sort"] = i
    groups = [dict(g) for g in GROUPS_SEED]
    return {"version": 1, "saved_at": _now(), "saved_by": "seed S764", "seeded": True,
            "defaults": dict(DEFAULTS), "groups": groups, "packages": pkgs}

def _group_of(groups, gid):
    for g in groups:
        if g.get("id") == gid: return g
    return None

def _apply_groups(doc):
    """A member linked to its group (own=false) takes the group's surgery, stay and size (and the size's heads).
    A member with its own figures is marked 'differs' where they differ. Nothing else is touched."""
    groups = doc.get("groups") or []
    for p in doc.get("packages") or []:
        g = _group_of(groups, p.get("group"))
        if not g:
            p["differs"] = False; continue
        if not p.get("own"):
            p["surgery"] = _n(g.get("surgery")); p["stay"] = max(1, _n(g.get("stay", 1), 1, 60))
            if g.get("size") in SIZE:
                p["size"] = g["size"]; p.update(SIZE[g["size"]])
            p["differs"] = False
        else:
            p["differs"] = (_n(p.get("surgery")) != _n(g.get("surgery")) or _n(p.get("stay")) != _n(g.get("stay"))
                            or (p.get("size") or None) != (g.get("size") or None))
    return doc

def _clean_pkg(p, i):
    if not isinstance(p, dict): raise ValueError("package %d is not an object" % i)
    name = " ".join(str(p.get("name", "")).split())[:80]
    if not name: raise ValueError("package %d has no name" % i)
    o = {"id": re.sub(r"[^A-Za-z0-9_\-]", "", str(p.get("id") or ""))[:24] or ("p%03d" % (i + 1)), "name": name}
    for k in PKG_NUM: o[k] = _n(p.get(k))
    o["stay"] = max(1, _n(p.get("stay", 1), 1, 60))
    o["size"] = p.get("size") if p.get("size") in SIZE else None
    o["group"] = (str(p.get("group"))[:24] if p.get("group") else None)
    for k in ("own", "suggested", "retired", "unnamed"): o[k] = bool(p.get(k))
    for k in ("region", "fx", "fix", "sb", "sb_note", "template", "consent_k", "c_part", "c_bone", "ot_proc", "tpa_q"):
        v = p.get(k); o[k] = (str(v)[:120] if v not in (None, "") else None)
    o["sort"] = _n(p.get("sort", i), 0, 100000)
    return o

def _clean_group(g, i):
    if not isinstance(g, dict): raise ValueError("group %d is not an object" % i)
    name = " ".join(str(g.get("name", "")).split())[:60]
    if not name: raise ValueError("group %d has no name" % i)
    return {"id": re.sub(r"[^A-Za-z0-9_\-]", "", str(g.get("id") or ""))[:24] or ("g%02d" % (i + 1)), "name": name,
            "surgery": _n(g.get("surgery")), "stay": max(1, _n(g.get("stay", 1), 1, 60)),
            "size": g.get("size") if g.get("size") in SIZE else None}

def _clean_defaults(d):
    d = d if isinstance(d, dict) else {}
    o = dict(DEFAULTS)
    if d.get("room"): o["room"] = str(d["room"])[:24]
    if d.get("grade") in GRADE_MULT: o["grade"] = d["grade"]
    for k in ("admission", "carm", "investigations", "other"): o[k] = _n(d.get(k, o[k]))
    return o

def packages_read():
    doc = _read_json(PKG_FILE, None)
    if doc is None:
        with _Lock():
            doc = _read_json(PKG_FILE, None)
            if doc is None:
                doc = _apply_groups(seed_packages())
                _write_json(PKG_FILE, doc)
    return doc

def packages_save(body, who):
    """Full replace, pinned by version: the page sends base_version; a stale save is refused with the current list
    (another device saved first), nothing written."""
    with _Lock():
        cur = packages_read()
        base = _n(body.get("base_version"), 0, 10 ** 9)
        if not base:
            return {"ok": False, "error": "refused: no version pinned — reload the page and try again"}, 400
        if base != _n(cur.get("version"), 0, 10 ** 9):
            return {"ok": False, "stale": True, "error": "saved on another device since you opened this — reload", "current": cur}, 409
        pk = body.get("packages"); gr = body.get("groups")
        if not isinstance(pk, list) or not pk: return {"ok": False, "error": "refused: empty package list"}, 400
        if len(pk) > 400: return {"ok": False, "error": "refused: too many packages"}, 400
        if not isinstance(gr, list): gr = cur.get("groups") or []
        pkgs = [_clean_pkg(p, i) for i, p in enumerate(pk)]
        ids = [p["id"] for p in pkgs]
        if len(set(ids)) != len(ids): return {"ok": False, "error": "refused: two packages share an id"}, 400
        groups = [_clean_group(g, i) for i, g in enumerate(gr[:60])]
        doc = {"version": _n(cur.get("version"), 0, 10 ** 9) + 1, "saved_at": _now(), "saved_by": who or "doctor",
               "seeded": bool(cur.get("seeded")), "defaults": _clean_defaults(body.get("defaults") or cur.get("defaults")),
               "groups": groups, "packages": pkgs}
        _apply_groups(doc)
        _write_json(PKG_FILE, doc)
        return {"ok": True, "version": doc["version"], "count": len(pkgs), "saved_at": doc["saved_at"]}, 200

def packages_import(items, who, base_version=0):
    """One device's localStorage list (dma_cash_v1, the page's old shape) merged by name: a same-named package
    takes the device's figures (his edits on that device), a new name is added. Nothing is removed. Pinned by
    version like every save; the seeding page retires the device's key afterwards so it cannot run twice."""
    if not isinstance(items, list) or not items: return {"ok": False, "error": "nothing to import"}, 400
    with _Lock():
        cur = packages_read()
        base = _n(base_version, 0, 10 ** 9)
        if not base: return {"ok": False, "error": "refused: no version pinned — reload the page and try again"}, 400
        if base != _n(cur.get("version"), 0, 10 ** 9):
            return {"ok": False, "stale": True, "error": "saved on another device since you opened this — reload", "current": cur}, 409
        by_name = {p["name"].upper(): p for p in cur["packages"]}
        n_new = n_upd = 0; nmax = max([_n(p["id"][1:], 0, 10 ** 6) for p in cur["packages"] if re.match(r"^p\d+$", p["id"])] or [0])
        for it in items[:200]:
            if not isinstance(it, dict) or not str(it.get("name", "")).strip(): continue
            nm = " ".join(str(it["name"]).split())[:80]
            tgt = by_name.get(nm.upper())
            if tgt:
                for k_live, k_v2 in (("operation", "surgery"), ("implant", "implant"), ("anaesthesia", "anaesthesia"), ("otMeds", "otMeds"),
                                     ("wardMeds", "wardMeds"), ("admission", "admission"), ("carm", "carm"), ("investigations", "investigations"), ("other", "other")):
                    if k_live in it: tgt[k_v2] = _n(it[k_live])
                if "stay" in it: tgt["stay"] = max(1, _n(it["stay"], 1, 60))
                tgt["own"] = True; tgt["suggested"] = False; tgt["size"] = None
                n_upd += 1
            else:
                nmax += 1
                p = _pkg_from_live({"name": nm, "operation": it.get("operation"), "implant": it.get("implant"), "stay": it.get("stay", 1),
                                    "anaesthesia": it.get("anaesthesia"), "otMeds": it.get("otMeds"), "wardMeds": it.get("wardMeds"),
                                    "admission": it.get("admission", DEFAULTS["admission"]), "carm": it.get("carm"),
                                    "investigations": it.get("investigations"), "other": it.get("other"), "unnamed": it.get("unnamed")},
                                   "p%03d" % nmax)
                p["sort"] = len(cur["packages"]); cur["packages"].append(p); by_name[nm.upper()] = p; n_new += 1
        if not (n_new or n_upd): return {"ok": True, "imported": 0, "updated": 0, "version": cur["version"]}, 200
        cur["version"] = _n(cur.get("version"), 0, 10 ** 9) + 1; cur["saved_at"] = _now(); cur["saved_by"] = (who or "doctor") + " (import)"
        _apply_groups(cur); _write_json(PKG_FILE, cur)
        return {"ok": True, "imported": n_new, "updated": n_upd, "version": cur["version"]}, 200

# ----------------------------------------------------------------------------------------------------------------
# rates
# ----------------------------------------------------------------------------------------------------------------
def rates_read():
    doc = _read_json(RATE_FILE, None)
    if doc is None or not isinstance(doc.get("rates"), list) or not doc["rates"]:
        with _Lock():
            doc = _read_json(RATE_FILE, None)
            if doc is None or not isinstance(doc.get("rates"), list) or not doc["rates"]:
                doc = {"version": 1, "saved_at": _now(), "saved_by": "seed S764", "rates": [dict(r) for r in RATES_SEED]}
                _write_json(RATE_FILE, doc)
    return doc

def _clean_rate(r, i):
    if not isinstance(r, dict): raise ValueError("rate %d is not an object" % i)
    n = " ".join(str(r.get("n", "")).split())[:40]
    if not n: raise ValueError("rate %d has no name" % i)
    t = r.get("t") if r.get("t") in ("ward", "day", "opt") else "ward"
    k = re.sub(r"[^A-Za-z0-9_\-]", "", str(r.get("k") or ""))[:24] or ("r%d_%s" % (i, _slug(n)))
    return {"k": k, "n": n, "r": _n(r.get("r"), 0, 500000), "t": t}

def rates_save(body, who):
    with _Lock():
        cur = rates_read()
        base = _n(body.get("base_version"), 0, 10 ** 9)
        if not base:
            return {"ok": False, "error": "refused: no version pinned — reload the page and try again"}, 400
        if base != _n(cur.get("version"), 0, 10 ** 9):
            return {"ok": False, "stale": True, "error": "the rates were saved on another device since — reload", "current": cur}, 409
        rs = body.get("rates")
        if not isinstance(rs, list) or not rs: return {"ok": False, "error": "refused: empty rate list"}, 400
        if len(rs) > 60: return {"ok": False, "error": "refused: too many rates"}, 400
        rates = [_clean_rate(r, i) for i, r in enumerate(rs)]
        ks = [r["k"] for r in rates]
        if len(set(ks)) != len(ks): return {"ok": False, "error": "refused: two rates share a key"}, 400
        if not any(r["t"] == "ward" for r in rates): return {"ok": False, "error": "refused: keep at least one ward"}, 400
        doc = {"version": _n(cur.get("version"), 0, 10 ** 9) + 1, "saved_at": _now(), "saved_by": who or "doctor", "rates": rates}
        _write_json(RATE_FILE, doc)
        return {"ok": True, "version": doc["version"], "count": len(rates), "saved_at": doc["saved_at"]}, 200

# ----------------------------------------------------------------------------------------------------------------
# settings — his eyes only
# ----------------------------------------------------------------------------------------------------------------
def settings_read():
    d = _read_json(SET_FILE, None) or {}
    o = dict(SETTINGS_DEFAULT); o.update({k: v for k, v in d.items() if k in SETTINGS_DEFAULT})
    o["share_pct"] = _n(o.get("share_pct", 50), 0, 100)
    return o

def settings_save(body, who):
    with _Lock():
        o = settings_read()
        if "share_pct" in body: o["share_pct"] = _n(body.get("share_pct"), 0, 100)
        o["saved_at"] = _now(); o["saved_by"] = who or "doctor"
        _write_json(SET_FILE, o)
    return {"ok": True, "settings": settings_read()}

# ----------------------------------------------------------------------------------------------------------------
# estimates given — append-only; PHI (patient names) stays in CASEPACK_DIR
# ----------------------------------------------------------------------------------------------------------------
def _est_lines():
    out = []
    try:
        with open(EST_FILE, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln: continue
                try:
                    out.append(json.loads(ln))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out

def estimates_list(cid="", n=50):
    rows = _est_lines(); marks = {}
    ests = []
    for i, r in enumerate(rows):
        if r.get("mark_of"):
            marks[r["mark_of"]] = r
        else:
            r = dict(r); r["_i"] = i; ests.append(r)
    if cid:
        ests = [e for e in ests if (e.get("patient") or {}).get("cid", "") == cid]
    ests.sort(key=lambda e: (e.get("at", ""), e["_i"]), reverse=True)   # two in one second: the later line is the newer
    out = []
    for e in ests[:max(1, min(500, _n(n, 1, 500)))]:
        m = marks.get(e.get("id"))
        o = dict(e); o.pop("_i", None); o["taken_up"] = (m.get("taken_up") if m else None); o["marked_at"] = (m.get("at") if m else None)
        out.append(o)
    return out

def _next_est_id():
    d = datetime.now(IST)
    return "E-%s-%s" % (d.strftime("%Y%m%d"), d.strftime("%H%M%S%f"))   # to the microsecond

def estimate_append(body, who, rates, share_pct):
    p = body.get("patient") or {}
    fig = body.get("figures")
    rec = {"id": _next_est_id(), "at": _now(), "by": who or "doctor",
           "patient": {"uid": str(p.get("uid", ""))[:40], "cid": str(p.get("cid", ""))[:40], "name": str(p.get("name", ""))[:120]},
           "payer": str(body.get("payer", "Cash"))[:20], "title": " ".join(str(body.get("title", "Estimate")).split())[:120],
           "package_id": str(body.get("package_id") or "")[:24] or None, "template": str(body.get("template") or "")[:64] or None,
           "text": str(body.get("text", ""))[:4000], "note": str(body.get("note", ""))[:400]}
    if isinstance(fig, dict):
        # a cash estimate: the figures are kept and the arithmetic is the server's (the same formula as the page)
        c = calc(fig, rates, share_pct)
        rec["figures"] = {k: fig.get(k) for k in ("surgery", "implant", "grade", "stay", "room", "opts", "anaesthesia", "otMeds", "wardMeds", "admission", "carm", "investigations", "other", "discount")}
        rec["total"] = c["total"]; rec["net_to_patient"] = c["net_to_patient"]; rec["lines"] = c["lines"]
        rec["my_net"] = c["my_net"]   # his eyes only — the file is in the PHI store behind his gate
    else:
        # an Ayushman or TPA record: the figure is the scheme's, kept as given; no net of his is worked out
        rec["figures"] = None; rec["total"] = _n(body.get("total")); rec["net_to_patient"] = rec["total"]; rec["lines"] = []; rec["my_net"] = None
    with _Lock():
        os.makedirs(CASEPACK_DIR, exist_ok=True)
        with open(EST_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        try:
            os.chmod(EST_FILE, 0o600)
        except Exception:
            pass
    return {"ok": True, "estimate": rec}, 200

def estimate_mark(body, who):
    eid = str(body.get("id", ""))[:40]
    if not re.match(r"^E-\d{8}-\d{9,12}$", eid): return {"ok": False, "error": "no such estimate id"}, 400
    if not any(e.get("id") == eid for e in _est_lines() if not e.get("mark_of")): return {"ok": False, "error": "no such estimate"}, 404
    tu = body.get("taken_up")
    rec = {"mark_of": eid, "at": _now(), "by": who or "doctor", "taken_up": (None if tu is None else bool(tu)), "note": str(body.get("note", ""))[:200]}
    with _Lock():
        with open(EST_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "mark": rec}, 200

# ----------------------------------------------------------------------------------------------------------------
# registration — called by casepack_portal.register() with the same guard and get_user
# ----------------------------------------------------------------------------------------------------------------
def register(app, guard, get_user):
    from flask import request, jsonify, Response

    def _who():
        try:
            return (get_user() or "doctor")
        except Exception:
            return "doctor"

    def _body():
        return request.get_json(force=True, silent=True) or {}

    @app.route("/portal/casepack/seed")
    @guard
    def casepack_v2_seed_page():
        if not os.path.exists(SEED_HTML):
            return Response("casepack_seed.html not found at " + SEED_HTML, status=500, mimetype="text/plain")
        with open(SEED_HTML, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="text/html; charset=utf-8")

    @app.route("/portal/casepack/templates")
    @guard
    def casepack_v2_templates():
        return jsonify(dict(ok=True, **catalogue()))

    @app.route("/portal/casepack/packages")
    @guard
    def casepack_v2_packages():
        try:
            d = packages_read()
            return jsonify({"ok": True, "version": d.get("version"), "saved_at": d.get("saved_at"), "saved_by": d.get("saved_by"),
                            "defaults": d.get("defaults") or dict(DEFAULTS), "groups": d.get("groups") or [], "packages": d.get("packages") or [],
                            "settings": (settings_read() if is_owner(_who()) else None)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/packages", methods=["POST"])
    @guard
    def casepack_v2_packages_save():
        try:
            out, code = packages_save(_body(), _who())
            return jsonify(out), code
        except ValueError as e:
            return jsonify({"ok": False, "error": "refused: " + str(e)}), 400
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/packages/import", methods=["POST"])
    @guard
    def casepack_v2_packages_import():
        try:
            b = _body(); out, code = packages_import(b.get("items"), _who(), b.get("base_version"))
            return jsonify(out), code
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/rates")
    @guard
    def casepack_v2_rates():
        try:
            d = rates_read()
            return jsonify({"ok": True, "version": d.get("version"), "saved_at": d.get("saved_at"), "saved_by": d.get("saved_by"), "rates": d["rates"]})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/rates", methods=["POST"])
    @guard
    def casepack_v2_rates_save():
        try:
            out, code = rates_save(_body(), _who())
            return jsonify(out), code
        except ValueError as e:
            return jsonify({"ok": False, "error": "refused: " + str(e)}), 400
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/settings")
    @guard
    def casepack_v2_settings():
        if not is_owner(_who()): return jsonify({"ok": False, "error": "the owner's setting"}), 403
        return jsonify({"ok": True, "settings": settings_read()})

    @app.route("/portal/casepack/settings", methods=["POST"])
    @guard
    def casepack_v2_settings_save():
        try:
            if not is_owner(_who()): return jsonify({"ok": False, "error": "the owner's setting"}), 403
            return jsonify(settings_save(_body(), _who()))
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/estimates")
    @guard
    def casepack_v2_estimates():
        try:
            rows = estimates_list(request.args.get("cid", "").strip(), request.args.get("n", 50))
            if not is_owner(_who()):
                for r in rows: r.pop("my_net", None)
            return jsonify({"ok": True, "estimates": rows})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/estimates", methods=["POST"])
    @guard
    def casepack_v2_estimates_add():
        try:
            out, code = estimate_append(_body(), _who(), rates_read()["rates"], settings_read()["share_pct"])
            return jsonify(out), code
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/estimates/mark", methods=["POST"])
    @guard
    def casepack_v2_estimates_mark():
        try:
            out, code = estimate_mark(_body(), _who())
            return jsonify(out), code
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/v2/calc", methods=["POST"])
    @guard
    def casepack_v2_calc():
        try:
            c = calc(_body().get("figures") or {}, rates_read()["rates"], settings_read()["share_pct"])
            if not is_owner(_who()): c.pop("my_net", None); c.pop("shareable", None); c.pop("share_pct", None)
            return jsonify({"ok": True, "calc": c})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return True
