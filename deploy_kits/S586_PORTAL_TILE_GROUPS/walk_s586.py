#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s586.py -- the offline walk of S586_PORTAL_TILE_GROUPS: the home page rendered from the TO file for every login
that matters, against the FROM file, with the merged grants. Runs anywhere Flask imports; touches no live file.

    python3 walk_s586.py <from_portal.py> <to_portal.py> <grants_before.json> <grants_after.json> [--save-pages DIR]
    python3 walk_s586.py ... --expect-red     (the control: the TO checks run against the FROM file must FAIL)

Every check prints PASS / FAIL; the exit code is 1 on any FAIL (or, with --expect-red, on any PASS of a MUST_RED check).
"""
import sys, os, re, importlib.util, json, types, html

RETIRED = ["UPI Sheet", "Vehicle Tracking", "Monthly Accounting", "Revenue Reconciler", "Case Pack · PC fallback",
           "CC Statements → Tally", "CC Statement Saver", "Inbox Janitor"]
GROUPS10 = ["Patients", "Surgery", "Calls & WhatsApp", "Docterz & clinic day", "Accounts & month-end", "Staff",
            "Assets & papers", "Sanjeevni Medicos", "Personal", "System"]
SANJ14 = ["Sanjeevni Medicos", "Daily Sale", "Kal ka hisaab", "Medical sale check", "Stock milaan", "Stock Check",
          "Purchase orders", "Vaapsi Desk", "Corrections", "Marg Purchases", "Order Medicines", "Vendor payments",
          "Amir ka kaam", "Aaj ki reports"]
BHAWNA7 = ["Kal ka hisaab", "Physiotherapy", "Petty book", "Clinic", "Report baaki", "OPD & X-ray/Proc Slips", "Staff"]
LOGINS = [("manoj", "doctor"), ("bhawna", "doctor"), ("shavez", "manager"), ("shivani", "staff"), ("alisha", "staff"),
          ("reception", "staff"), ("amir", "staff"), ("darpan", "staff"), ("bhati", "staff"), ("awdhesh", "staff"),
          ("sukhveer", "staff"), ("surendra", "staff")]

results = []


def check(name, ok, detail="", must_red=False):
    results.append((name, bool(ok), detail, must_red))
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + detail) if detail else ""))


def load(path, grants_path, tag):
    """Import a portal.py copy with no VPS config: stub the sibling modules, point the grants file at a copy."""
    os.environ["TILE_GRANTS_FILE"] = grants_path
    os.environ.setdefault("PORTAL_TOKEN_SEED", "walk-seed")
    for mod in ("clinic_sso", "clinic_users", "tracker_pass", "portal_push", "portal_config"):
        sys.modules.pop(mod, None)
    spec = importlib.util.spec_from_file_location("portal_" + tag, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["portal_" + tag] = m
    spec.loader.exec_module(m)
    return m


def names(sections):
    return [t["name"] for _g, items in sections for t in items]


def render(m, user, role, pc=False):
    """What home() renders for this login: the same calls, without the request (no cookie, no SSO)."""
    sections = m._visible_sections(role, pc, user)
    who = {"user": user, "role": role}
    with m.app.test_request_context("/portal"):
        kw = dict(sections=sections, sso=False, who=who, role=role, pc=pc, s444_nowork=False)
        if hasattr(m, "_home_blocks"):
            kw["blocks"] = m._home_blocks(sections, m._folders_for(user))
        page = m.render_template_string(m.PORTAL_HTML, **kw)
    return sections, page


def tiles_on_home(page):
    """Tile names drawn on the home grid itself (outside any sheet)."""
    body = re.split(r'<section class="sheet"', page)[0]
    return re.findall(r'<div class="nm">([^<]+)</div>', body)


def sheet(page, slug):
    m = re.search(r'<section class="sheet" id="g-%s".*?</section>' % re.escape(slug), page, re.S)
    return re.findall(r'<div class="nm">([^<]+)</div>', m.group(0))[1:] if m else None   # [0] is the sheet header


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    expect_red = "--expect-red" in sys.argv
    save = None
    if "--save-pages" in sys.argv:
        save = sys.argv[sys.argv.index("--save-pages") + 1]; args = [a for a in args if a != save]
    frm, to, gb, ga = args[:4]
    before = load(frm, gb, "from")
    target = frm if expect_red else to
    after = load(target, ga, "to")
    un = html.unescape

    # W1 -- the same logins see the same tiles before and after, less the retired ones (display only: nothing granted, nothing lost)
    for user, role in LOGINS:
        for pc in (False, True):
            b = set(names(before._visible_sections(role, pc, user))) - set(RETIRED)
            a = set(names(after._visible_sections(role, pc, user)))
            if user == "bhawna":
                b -= {"Patient records", "Check karein"}
                b &= set(BHAWNA7 + ["Attendance", "Staff Register", "Salary — approve & lock", "Staff Ledger"])
            check("W1 %s/%s pc=%s same tiles" % (user, role, pc), a == b,
                  "missing %s extra %s" % (sorted(b - a), sorted(a - b)) if a != b else "%d tiles" % len(a))

    # W2 -- the retired eight are gone from TILES; Renewals points at the server
    tn = [t["name"] for t in after.TILES]
    check("W2 retired tiles absent", not (set(RETIRED) & set(tn)), str(sorted(set(RETIRED) & set(tn))), must_red=True)
    ren = [t for t in after.TILES if t["name"] == "Renewals"]
    check("W2 Renewals -> /scanapp/renewals", bool(ren) and ren[0]["url"] == "/scanapp/renewals", ren[0]["url"] if ren else "no tile", must_red=True)
    check("W2 groups are the ten", list(getattr(after, "GROUP_ORDER", [])) == GROUPS10, str(getattr(after, "GROUP_ORDER", None)), must_red=True)
    check("W2 every tile grouped", all(t.get("group") in GROUPS10 for t in after.TILES), must_red=True)
    check("W2 the Sanjeevni fourteen under one label", all(after._TILE_GROUP.get(n) == "Sanjeevni Medicos" for n in SANJ14)
          and sorted(k for k, v in after._TILE_GROUP.items() if v == "Sanjeevni Medicos") == sorted(SANJ14), must_red=True)
    # the Sanjeevni tile dicts themselves are byte-identical to FROM (only their group label moved)
    bt = {t["name"]: {k: v for k, v in t.items() if k != "group"} for t in before.TILES}
    at = {t["name"]: {k: v for k, v in t.items() if k != "group"} for t in after.TILES}
    check("W2 Sanjeevni tiles unchanged", all(bt.get(n) == at.get(n) for n in SANJ14))
    check("W2 every other kept tile unchanged", all(bt[n] == at[n] for n in at if n != "Renewals"))

    # W3 -- manoj: 10 group tiles on the home, nothing else; each sheet holds its tiles
    sec, page = render(after, "manoj", "doctor")
    home = [un(x) for x in tiles_on_home(page)]
    check("W3 manoj home = 10 group tiles", home == GROUPS10, str(home), must_red=True)
    for label, items in sec:
        slug = after._group_slug(label) if hasattr(after, "_group_slug") else ""
        got = [un(x) for x in (sheet(page, slug) or [])]
        want = [t["name"] for t in items]
        check("W3 manoj sheet %s" % label, got == want, "%s vs %s" % (got, want) if got != want else "%d tiles" % len(want), must_red=True)
    check("W3 manoj: Surgery cases in Surgery", "Surgery cases" in (sheet(page, "surgery") or []), must_red=True)
    check("W3 manoj: live-count hooks still in the page", all(k in page for k in ("data-sanjeevni-counts", "data-gist-summary", "data-review-counts")))
    check("W3 manoj: no 'Clinic PC tools' row", "Clinic PC tools" not in page, must_red=True)
    sec_pc, page_pc = render(after, "manoj", "doctor", pc=True)
    check("W3 manoj on the clinic PC: Follow-up Tracker inside Calls & WhatsApp", "Follow-up Tracker" in (sheet(page_pc, "calls-whatsapp") or []), must_red=True)
    check("W3 manoj off the clinic PC: no Follow-up Tracker", "Follow-up Tracker" not in page)
    if save:
        os.makedirs(save, exist_ok=True); open(os.path.join(save, "home_manoj.html"), "w", encoding="utf-8").write(page)

    # W4 -- bhawna: six flat tiles + the Staff folder; Patient records / Check karein gone; no Sanjeevni tile
    sec, page = render(after, "bhawna", "doctor")
    home = [un(x) for x in tiles_on_home(page)]
    check("W4 bhawna home = her 7, Staff last", sorted(home) == sorted(BHAWNA7) and home[-1] == "Staff", str(home), must_red=True)
    got = [un(x) for x in (sheet(page, "staff") or [])]
    check("W4 bhawna Staff sheet = 4", got == ["Attendance", "Staff Register", "Salary — approve & lock", "Staff Ledger"], str(got), must_red=True)
    check("W4 bhawna: no Patient records / Check karein", not ({"Patient records", "Check karein"} & set(names(sec))))   # the grants do this, not the patch
    check("W4 bhawna: no Sanjeevni tile but Kal ka hisaab", not ((set(SANJ14) - {"Kal ka hisaab"}) & set(names(sec))) and "Kal ka hisaab" in names(sec), must_red=True)
    if save:
        open(os.path.join(save, "home_bhawna.html"), "w", encoding="utf-8").write(page)

    # W5 -- staff and managers: flat, no sheets, no group tiles
    for user, role in LOGINS[2:]:
        sec, page = render(after, user, role)
        check("W5 %s flat" % user, '<section class="sheet"' not in page and 'class="tile grp"' not in page
              and sorted(un(x) for x in tiles_on_home(page)) == sorted(names(sec)), "%d tiles" % len(names(sec)))
        if save and user in ("shavez", "shivani", "amir"):
            open(os.path.join(save, "home_%s.html" % user), "w", encoding="utf-8").write(page)

    # W6 -- the grants file: additive only
    gbj, gaj = json.load(open(gb)), json.load(open(ga))
    for u, d in gbj["users"].items():
        for k in ("mask", "extra"):
            check("W6 %s.%s kept" % (u, k), set(d.get(k, [])) <= set(gaj["users"][u].get(k, [])))
    check("W6 version bumped", gaj.get("version", 0) == gbj.get("version", 0) + 1, "%s -> %s" % (gbj.get("version"), gaj.get("version")))

    # Z1 -- the FROM file renders the same old home for manoj (the walk itself is not broken)
    secb, pageb = render(before, "manoj", "doctor")
    check("Z1 FROM renders", "System Board" in pageb and '<section class="sheet"' not in pageb)

    bad = [r for r in results if not r[1]]
    if expect_red:
        reds = [r for r in results if r[3]]
        wrong = [r for r in reds if r[1]]
        print("\nCONTROL: %d MUST_RED checks, %d red, %d wrongly green" % (len(reds), len(reds) - len(wrong), len(wrong)))
        sys.exit(1 if wrong else 0)
    print("\n%d checks, %d FAIL" % (len(results), len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
