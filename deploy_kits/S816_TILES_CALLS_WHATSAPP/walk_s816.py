#!/usr/bin/python3
# walk_s816.py -- kit S816_TILES_CALLS_WHATSAPP. Usage: walk_s816.py <portal.py BEFORE> <portal.py AFTER> [--control] [--list]
# Reads two files and writes nothing but a temp folder of its own (removed at the end). Stdlib only; no Flask, no network, no store.
# It runs the portal's OWN tile code -- the part of portal.py from "TILES = [" to the end of the S586 block: the tile list, the
# groups, the per-person fallbacks, _grants_for, _visible_sections, _home_blocks -- once from each file, and compares what every
# role and every login is drawn. Everything about people is MADE UP here: the logins are walk_* names and the grants file is
# written at run time. The only real names are the ones standing in portal.py's own fallback tables.
# --control: give the unpatched file as AFTER too; the walk must go RED.   --list: also print each role's tiles before -> after.
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red (k of n)" when it is red as it must be.
import difflib, json, os, re, shutil, sys, tempfile, types
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CONTROL, LIST = "--control" in sys.argv, "--list" in sys.argv
BEFORE, AFTER = os.path.abspath(ARGS[0]), os.path.abspath(ARGS[1])
T = tempfile.mkdtemp(prefix="s816w.")
MID = chr(0xb7)
WM, R1, R2 = "WhatsApp messages", "Follow-up WhatsApps", "WhatsApp Approvals"
RETIRED = (R1, R2)
CW, PAT, SYS_ = "Calls & WhatsApp", "Patients", "System"
WM_DESC = "Daily patient messages %s switches %s what went" % (MID, MID)
SYS_FACE_WAS = "Board %s users %s clinic PCs %s WhatsApp approvals" % (MID, MID, MID)
SYS_FACE = "Board %s users %s clinic PCs" % (MID, MID)
# the approved mock-up's order (artifact 8J3R3QtW9awbajmLN4rmic, "the tiles"); Follow-up Tracker is drawn on the clinic PC only
CW_MOCKUP = ["Clinic Gist", "Call Console", "Call Tracker", "Call ke baad", "GMB Review Assist", "WhatsApp Inbox", WM, "Send WhatsApp"]
CW_ON_PC = CW_MOCKUP + ["Follow-up Tracker"]
START, END, TAIL = "\nTILES = [\n", "# ---- S586 end", "# Every tile must map to a known group"
RES = []


def ck(name, ok, why=""):
    RES.append(bool(ok))
    print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)[:300]) if (why and not ok) else ""))


# the staff's "Call ke baad" switch: portal.py asks ring_outcome.list_on(); here it is a made-up module the walk turns on and off
RING = types.ModuleType("ring_outcome"); RING.on = False; RING.list_on = lambda: RING.on
sys.modules["ring_outcome"] = RING


def load(path, tag):
    """The tile code of one portal.py, run on its own. A file that fails its own 'ungrouped tile' asserts fails here."""
    src = open(path, encoding="utf-8").read()
    i, j = src.index(START), src.index(END)
    os.environ["TILE_GRANTS_FILE"] = os.path.join(T, "none.json")
    ns = {"os": os, "re": re, "json": json, "__file__": os.path.join(T, tag + "_portal.py"), "__name__": "s816_" + tag}
    exec(compile(src[i:j], tag, "exec"), ns)
    return src, ns


def use_grants(ns, path):
    ns["TILE_GRANTS_FILE"] = path
    ns["_GRANTS_CACHE"].update(mtime=None, data=None)


def secs(ns, role, pc, user):
    return [(g, [t["name"] for t in items]) for g, items in ns["_visible_sections"](role, pc, user)]


def expected(before, order):
    """What a login must be drawn after S816, worked out from what it is drawn before: the two retired tiles gone, WhatsApp
    messages (if it is drawn) under Calls & WhatsApp, a group with nothing left dropped, nothing else moved."""
    d = {g: [n for n in names if n not in RETIRED and n != WM] for g, names in before}
    had = any(WM in names for _g, names in before)
    return {g: d.get(g, []) for g in order if d.get(g) or (g == CW and had)}, had


def same_but(after, exp, had):
    """after (the portal's own answer) against the expectation; WhatsApp messages is looked at apart."""
    got = {g: [n for n in names if n != WM] for g, names in after}
    if [g for g, _n in after] != list(exp):
        return "groups %r, expected %r" % ([g for g, _n in after], list(exp))
    for g in exp:
        if got[g] != exp[g]:
            return "%s: %r, expected %r" % (g, got[g], exp[g])
    where = [g for g, names in after if WM in names]
    if had and where != [CW]:
        return "WhatsApp messages drawn under %r" % (where,)
    if not had and where:
        return "WhatsApp messages newly drawn under %r" % (where,)
    if had:
        names = dict(after)[CW]
        k = names.index(WM)
        if "WhatsApp Inbox" in names and names.index("WhatsApp Inbox") > k:
            return "WhatsApp messages stands before WhatsApp Inbox"
        if "Send WhatsApp" in names and names.index("Send WhatsApp") < k:
            return "WhatsApp messages stands after Send WhatsApp"
    return ""


try:
    SB, B = load(BEFORE, "before")
    ck("A0 the BEFORE file's tile code runs on its own (every tile grouped)", True)
except Exception as e:  # noqa: BLE001
    B = None; ck("A0 the BEFORE file's tile code runs on its own", False, repr(e))
try:
    SA, A = load(AFTER, "after")
    ck("A1 the AFTER file's tile code runs on its own (every tile grouped, every group known)", True)
except Exception as e:  # noqa: BLE001
    A = None; ck("A1 the AFTER file's tile code runs on its own", False, repr(e))

if A and B:
    # ---- A. the two files as text: only the tile list and the group table differ
    try:
        compile(SA, "after_portal.py", "exec")
        ck("A2 the AFTER portal.py compiles whole", True)
    except Exception as e:  # noqa: BLE001
        ck("A2 the AFTER portal.py compiles whole", False, repr(e))
    ck("A3 everything above the tile list is byte-for-byte the same", SB[:SB.index(START)] == SA[:SA.index(START)])
    ck("A4 everything from the grouping asserts to the end of the file (the grants, every page, every route) is byte-for-byte the same",
       SB[SB.index(TAIL):] == SA[SA.index(TAIL):] and len(SB[SB.index(TAIL):]) > 300000)
    lb, la = SB.split("\n"), SA.split("\n")
    ops = [o for o in difflib.SequenceMatcher(None, lb, la, autojunk=False).get_opcodes() if o[0] != "equal"]
    gone = [x for o in ops for x in lb[o[1]:o[2]]]
    came = [x for o in ops for x in la[o[3]:o[4]]]
    ck("A5 six places changed, no more: the tile's old place, its new place, the two retired tiles, the System face, two lines of the group table",
       len(ops) == 6 and len(gone) == 20 and len(came) == 20, "%d places, %d lines out, %d lines in" % (len(ops), len(gone), len(came)))
    code_in = [x.strip() for x in came if x.strip() and not x.strip().startswith("#")]
    ck("A6 the lines that came in: the moved tile's five lines, the System face's line and one line of the group table; the rest are notes",
       len(code_in) == 7 and code_in[0].startswith('{"icon": "\\U0001F4E8", "name": "%s",' % WM) and '"/portal/messages"' in "".join(code_in[:5])
       and code_in[5].startswith('"System":') and "approvals" not in code_in[5] and code_in[6].startswith('"%s": "%s",' % (WM, CW)), code_in)
    rts = lambda s: re.findall(r"^@app\.route\(.*$", s, re.M)                     # noqa: E731
    ck("A7 no route added, removed or changed (%d routes)" % len(rts(SB)), rts(SB) == rts(SA) and len(rts(SB)) > 20)
    ck("A8 no page text carries a retired tile's name as a tile any more; the fallback mask for one login is left as it was",
       SA.count('"name": "%s"' % R1) == 0 and SA.count('"name": "%s"' % R2) == 0 and SA.count('"name": "%s"' % WM) == 1
       and SA.count('"/portal/messages"') == SB.count('"/portal/messages"'))

    # ---- B. the tile list and the groups, as the portal loads them
    tb, ta = B["TILES"], A["TILES"]
    nb, na = [t["name"] for t in tb], [t["name"] for t in ta]
    db, da = {t["name"]: t for t in tb}, {t["name"]: t for t in ta}
    ck("B1 BEFORE holds the three tiles, each the doctors' by role alone (no staff role is drawn any of them)",
       all(n in db and db[n]["roles"] == ["doctor"] for n in (WM, R1, R2)), [db.get(n, {}).get("roles") for n in (WM, R1, R2)])
    ck("B2 no tile name twice, before or after", len(set(nb)) == len(nb) and len(set(na)) == len(na))
    ck("B3 the two retired tiles are gone from the list and from the group table",
       not (set(RETIRED) & set(na)) and not (set(RETIRED) & set(A["_TILE_GROUP"])), sorted(set(RETIRED) & (set(na) | set(A["_TILE_GROUP"]))))
    ck("B4 the tile names are the same ones less the two (%d -> %d): no tile renamed, none added" % (len(nb), len(na)),
       set(na) == set(nb) - set(RETIRED) and len(na) == len(nb) - 2, sorted(set(na) ^ (set(nb) - set(RETIRED))))
    w0, w1 = db.get(WM, {}), da.get(WM, {})
    ck("B5 WhatsApp messages is under Calls & WhatsApp (it was under Patients)", w0.get("group") == PAT and w1.get("group") == CW, (w0.get("group"), w1.get("group")))
    ck("B6 its small line is the approved one, to the letter", w1.get("desc") == WM_DESC, w1.get("desc"))
    ck("B7 its name, icon, address, roles and 'live' are untouched; it gained and lost no key",
       set(w0) == set(w1) and all(w0.get(k) == w1.get(k) for k in w0 if k not in ("desc", "group"))
       and w1.get("url") == "/portal/messages" and w1.get("roles") == ["doctor"] and w1.get("live") is True)
    oth = [n for n in nb if n not in (WM, R1, R2)]
    bad = [n for n in oth if db[n] != da.get(n)]
    ck("B8 every other tile (%d) is the same in every field: name, small line, icon, address, roles, group, switches" % len(oth), not bad and len(oth) > 50, bad)
    ck("B9 every other tile stands in the same order", [n for n in na if n != WM] == oth)
    ck("B10 the group list is untouched; nine group faces are untouched; the System face keeps its icon",
       B["GROUP_ORDER"] == A["GROUP_ORDER"] and len(A["GROUP_ORDER"]) == 10 and set(A["GROUP_META"]) == set(B["GROUP_META"])
       and all(B["GROUP_META"][g] == A["GROUP_META"][g] for g in B["GROUP_META"] if g != SYS_) and B["GROUP_META"][SYS_][0] == A["GROUP_META"][SYS_][0])
    ck("B13 the System group's face drops ' %s WhatsApp approvals' and nothing else; no group face names a retired tile" % MID,
       B["GROUP_META"][SYS_][1] == SYS_FACE_WAS and A["GROUP_META"][SYS_][1] == SYS_FACE
       and not any("approvals" in d.lower() or "follow-up whatsapp" in d.lower() for _i, d in A["GROUP_META"].values()), A["GROUP_META"][SYS_][1])
    gb = dict(B["_TILE_GROUP"]); ga = dict(A["_TILE_GROUP"])
    gb.pop(R1, None); gb.pop(R2, None); gb[WM] = CW
    ck("B11 the group table: WhatsApp messages re-pointed, the two retired names out, every other line as it was", ga == gb, sorted(set(ga.items()) ^ set(gb.items())))
    ck("B12 the per-person fallback tables and the folded-screen labels are untouched",
       all(B[k] == A[k] for k in ("USER_TILE_MASK", "USER_TILE_EXTRA", "S657_STAFF_SCREENS", "S660_WHO", "S497_TILE", "S657_STAFF_GROUP")))
    ROLES = sorted({r for t in tb for r in t["roles"]} | {"doctor", "manager", "staff"})

    # ---- C. what each role is drawn, by the portal's own _visible_sections: no grants file (the fallback tables)
    order0 = list(A["GROUP_ORDER"])
    for pc in (False, True):
        RING.on = True
        got = dict(secs(A, "doctor", pc, "walk_owner")).get(CW)
        ck("C1 a doctor's Calls & WhatsApp, %s: the mock-up's tiles in the mock-up's order" % ("on the clinic PC" if pc else "on a phone"),
           got == (CW_ON_PC if pc else CW_MOCKUP), got)
    sb, sa = secs(B, "doctor", True, "walk_owner"), secs(A, "doctor", True, "walk_owner")
    fb = set(n for _g, x in sb for n in x); fa = set(n for _g, x in sa for n in x)
    ck("C2 a doctor is drawn two tiles fewer -- the two retired ones -- and no other tile comes or goes", fb - fa == set(RETIRED) and not (fa - fb), (sorted(fb - fa), sorted(fa - fb)))
    ck("C3 a doctor's Patients loses WhatsApp messages and nothing else; System loses WhatsApp Approvals and nothing else",
       [n for n in dict(sb)[PAT] if n != WM] == dict(sa)[PAT] and [n for n in dict(sb)[SYS_] if n != R2] == dict(sa)[SYS_]
       and WM in dict(sb)[PAT] and R2 in dict(sb)[SYS_], (dict(sa)[PAT], dict(sa)[SYS_]))
    n_same = n_all = 0
    for role in ROLES:
        if role == "doctor":
            continue
        for user in ["walk_nobody"] + sorted(set(B["USER_TILE_MASK"]) | set(B["USER_TILE_EXTRA"])):
            for pc in (False, True):
                for on in (False, True):
                    RING.on = on; n_all += 1
                    n_same += secs(B, role, pc, user) == secs(A, role, pc, user)
    ck("C4 every role that is not a doctor (%s) is drawn EXACTLY the same screen, tile for tile, order for order (%d screens)"
       % (", ".join(r for r in ROLES if r != "doctor"), n_all), n_same == n_all and n_all >= 8, "%d of %d differ" % (n_all - n_same, n_all))
    n_ok = n_all = 0; first = ""
    for role in ROLES:
        for user in ["walk_nobody"] + sorted(set(B["USER_TILE_MASK"]) | set(B["USER_TILE_EXTRA"])):
            for pc in (False, True):
                for on in (False, True):
                    RING.on = on; n_all += 1
                    exp, had = expected(secs(B, role, pc, user), order0)
                    why = same_but(secs(A, role, pc, user), exp, had)
                    n_ok += not why; first = first or (why and "%s/%s: %s" % (role, user, why))
    ck("C5 every role x every name in the fallback tables x phone / clinic PC: the only differences are the three (%d screens)" % n_all, n_ok == n_all, first)

    # ---- D. the same with a grants file -- MADE UP: walk_* logins, with the kinds of line the real file holds
    G = {"version": 1, "users": {
        "walk_owner": {"folders": ["*"], "extra": ["Manage Users", "Clinic PCs"], "mask": ["Daily Sale"],
                       "groups": ["Calls & WhatsApp", "Patients", "System"]},
        "walk_doc2": {"only": ["Physiotherapy", "Petty book", "Report baaki", "Attendance", "Staff Register"],
                      "mask": [R1, "Send WhatsApp", "WhatsApp Inbox", "Patient records"], "folders": ["Staff"]},
        "walk_desk": {"extra": ["Call Tracker", "Call ke baad", "Online booking", "Check karein", "Physiotherapy"], "mask": ["Attendance"]},
        "walk_mgr": {"extra": ["Asset Register", "Mahine ka kaam", "Vendor payments"]},
        "walk_plain": {},
        "walk_given": {"extra": [WM, R1, R2, "Call Tracker"]},      # a staff login GIVEN the three by name (nobody is, today)
        "walk_only": {"only": [WM, R2]},                            # a login narrowed to two of them
    }, "defaults": {"groups_by_role": {"staff": ["Calls & WhatsApp", "Patients", "Docterz & clinic day", "Staff"]}}}
    gp = os.path.join(T, "walk_grants.json")
    with open(gp, "w", encoding="utf-8") as fh:
        json.dump(G, fh)
    use_grants(A, gp); use_grants(B, gp)
    ck("D0 the made-up grants file is the one being read", A["_tile_grants"]() is not None and A["_folders_for"]("walk_owner") == set(A["GROUP_ORDER"]))
    n_ok = n_all = n_same = n_staff = 0; first = ""
    for user in sorted(G["users"]) + ["walk_absent"]:
        for role in ROLES:
            for pc in (False, True):
                for on in (False, True):
                    RING.on = on; n_all += 1
                    b_, a_ = secs(B, role, pc, user), secs(A, role, pc, user)
                    exp, had = expected(b_, A["_grants_for"](user, role)[2])
                    why = same_but(a_, exp, had)
                    n_ok += not why; first = first or (why and "%s/%s: %s" % (role, user, why))
                    if role != "doctor" and user not in ("walk_given", "walk_only"):
                        n_staff += 1; n_same += b_ == a_
    ck("D1 every made-up login x every role x phone / clinic PC x the staff list on / off: the only differences are the three (%d screens)" % n_all, n_ok == n_all, first)
    ck("D2 a login that is not a doctor and is not given one of the three by name: EXACTLY the same screen (%d screens)" % n_staff, n_same == n_staff and n_staff >= 40,
       "%d of %d differ" % (n_staff - n_same, n_staff))
    RING.on = True
    gv = secs(A, "staff", False, "walk_given"); gvn = [n for _g, x in gv for n in x]
    ck("D3 a grant by name follows the tile: 'WhatsApp messages' is drawn under Calls & WhatsApp; a grant of a retired name draws nothing",
       WM in dict(gv).get(CW, []) and R1 not in gvn and R2 not in gvn, gv)
    hb = [(l, [t["name"] for t in it], f, s, ic, d) for l, it, f, s, ic, d in B["_home_blocks"](B["_visible_sections"]("doctor", True, "walk_owner"), B["_folders_for"]("walk_owner"))]
    ha = [(l, [t["name"] for t in it], f, s, ic, d) for l, it, f, s, ic, d in A["_home_blocks"](A["_visible_sections"]("doctor", True, "walk_owner"), A["_folders_for"]("walk_owner"))]
    ck("D4 the folded home (every group one tile): the same folders in the same order, the same faces but System's small line; only the three inside them differ",
       [(l, f, s, ic, SYS_FACE if l == SYS_ else d) for l, _n, f, s, ic, d in hb] == [(l, f, s, ic, d) for l, _n, f, s, ic, d in ha]
       and set(n for _l, x, *_r in hb for n in x) - set(n for _l, x, *_r in ha for n in x) == set(RETIRED)
       and dict((l, x) for l, x, *_r in ha)[CW][:3] == CW_ON_PC[:3] and WM in dict((l, x) for l, x, *_r in ha)[CW])
    ck("D5 the group's page address (its slug) is what it was", A["_group_slug"](CW) == B["_group_slug"](CW) == "calls-whatsapp")

    if LIST:
        use_grants(A, os.path.join(T, "none.json")); use_grants(B, os.path.join(T, "none.json")); RING.on = True
        print("---- each role, by role alone (no grants file), on the clinic PC, the staff list on: tiles BEFORE -> AFTER")
        for role in ROLES:
            b_, a_ = secs(B, role, True, "walk_nobody"), secs(A, role, True, "walk_nobody")
            fb = [n for _g, x in b_ for n in x]; fa = [n for _g, x in a_ for n in x]
            print("role %-8s %d tiles -> %d tiles%s" % (role, len(fb), len(fa), "" if b_ != a_ else "   (the same screen)"))
            for g in A["GROUP_ORDER"]:
                x, y = dict(b_).get(g), dict(a_).get(g)
                if x != y:
                    print("   %-18s before: %s" % (g, ", ".join(x or [])))
                    print("   %-18s after:  %s" % ("", ", ".join(y or [])))

shutil.rmtree(T, ignore_errors=True)
bad = len([r for r in RES if not r])
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
    sys.exit(0 if bad else 1)
print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
sys.exit(1 if bad else 0)
