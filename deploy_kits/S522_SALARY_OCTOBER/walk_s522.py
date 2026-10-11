#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s522.py -- kit S522_SALARY_OCTOBER: THE LIVE-SHAPE WALK. Run ON THE BOX by the installer before anything
is placed (and offline by the builder on a made-up tree).

It loads the LIVE pair (/root/staff_ledger.py + /root/staff_register/salary_policy.py) and THE KIT'S pair side by
side. Neither ever reads the live ledger: each reads a private COPY of it under /tmp, and the live ledger's md5
is the same before and after the walk.

  PART 1  the ledger exactly as it stands (a byte-exact copy), for each month walked:
          * the two ledger modules agree on every open advance, every schedule and the loans view
          * the two engines agree on EVERY figure of every person (the kit changes no money)
          * Sheet 2 and every private loan page are byte for byte the live engine's (no skipped month yet)
          * Sheet 3 read back through the register's own reader (locked_snapshot) gives the same rows and
            figures from both engines -- the separators do not change what the lock freezes
          * Sheet 4 carries a TOTAL that is the sum of the amounts above it, each amount the person's net
          * every slip is the live engine's, save the negative-net line, which now says what is true
          * Sheet 3's dress / I-card footnote is the settings' own
  PART 2  a second private copy: every person with a long-term loan skips THIS month with the one button
          (record_skip_month), and a third copy does nothing; both are closed for the month by the kit's ledger:
          * one tap writes one skip-marked DEFER per long-term line, the month counts once in the year,
            a second tap is refused, the penalty only where the year's two free months are used
          * a skipped line collects nothing; every person who did not skip is collected exactly as without
          * the kit engine shows the month as skipped on Sheet 2's strip, the slip and the private page;
            the private page pays the instalment back to him, and full net == common net + paid to him
          * the LIVE engine reads the same copy to the same money -- the change is display only

Nothing is written outside a private folder under /tmp. NO RUPEE FIGURE IS PRINTED (F-31): counts only.

usage:  walk_s522.py <kit dir>      env ROOT (default /root) · LEDGER_DIR · MONTHS (default 2026-08,2026-09,<now>)
"""
import os, re, sys, html, shutil, hashlib, sqlite3, tempfile, datetime, importlib.util

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def norm(v):
    if isinstance(v, set):
        return sorted(norm(x) for x in v)
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    return v


def num(t):
    try:
        return float(str(t).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


NEG = re.compile(r'<div class="ownwarn">Is mahine advance, salary se.*?</div>', re.S)
SKIPROW = re.compile(r"<tr class='new'><td>Loan ki kist — is mahine (?:skip|roki gayi).*?</tr>", re.S)


def copy_ledger(src_dir, dst):
    os.makedirs(dst)
    for f in os.listdir(src_dir):
        p = os.path.join(src_dir, f)
        if os.path.isfile(p) and (f.endswith(".jsonl") or f.endswith(".json")):
            shutil.copy2(p, os.path.join(dst, f))
    return dst


def compute_with(P, Lmod, ldir, ym):
    """One engine, reading the ledger through one ledger module pointed at one private copy."""
    Lmod.LEDGER_DIR = ldir
    sys.modules["staff_ledger"] = Lmod
    return P.compute(ym)


def main():
    kit = os.path.abspath(sys.argv[1])
    ROOT = os.path.abspath(os.environ.get("ROOT", "/root"))
    live = os.path.join(ROOT, "staff_register")
    ledger_dir = os.environ.get("LEDGER_DIR") or os.path.join(ROOT, "staff_ledger")
    led_file = os.path.join(ledger_dir, "ledger.jsonl")
    for p in (os.path.join(live, "salary_policy.py"), os.path.join(kit, "salary_policy.py"),
              os.path.join(ROOT, "staff_ledger.py"), os.path.join(kit, "staff_ledger.py"), led_file):
        check("exists: %s" % p, os.path.isfile(p))
    scratch = tempfile.mkdtemp(prefix="s522_walk_", dir="/tmp")
    try:
        os.environ["ATT_DIR"] = ROOT
        os.environ.setdefault("STAFF_CSV", os.path.join(ROOT, "staff_master.csv"))
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        if live not in sys.path:
            sys.path.insert(1, live)
        dbp = os.path.join(scratch, "sr_walk.db")              # the register's database, a private copy
        live_db = os.path.join(live, "staff_register.db")
        if os.path.isfile(live_db):
            s = sqlite3.connect("file:%s?mode=ro" % live_db, uri=True)
            d = sqlite3.connect(dbp)
            s.backup(d); d.close(); s.close()
        os.environ["SR_DB_PATH"] = dbp
        os.environ["ATT_REGISTER_DB"] = dbp
        led_md5_before = md5_file(led_file)
        sc1 = copy_ledger(ledger_dir, os.path.join(scratch, "led_part1"))
        check("the walk's copy of the ledger is byte for byte the live one", md5_file(os.path.join(sc1, "ledger.jsonl")) == led_md5_before)
        os.environ["LEDGER_DIR"] = sc1                         # anything that reads the env reads the copy

        Lo = load(os.path.join(ROOT, "staff_ledger.py"), "sl_live_s522")
        Ln = load(os.path.join(kit, "staff_ledger.py"), "sl_kit_s522")
        Lo.LEDGER_DIR = Ln.LEDGER_DIR = sc1
        check("the kit ledger has the one-button skip", hasattr(Ln, "record_skip_month") and not hasattr(Lo, "record_skip_month"))
        sys.modules["staff_ledger"] = Lo
        Po = load(os.path.join(live, "salary_policy.py"), "sp_live_s522")
        Pn = load(os.path.join(kit, "salary_policy.py"), "sp_kit_s522")
        check("the kit engine says it is 1.18-S522", getattr(Pn, "VERSION", "") == "1.18-S522")
        check("the live engine is 1.17-S489", getattr(Po, "VERSION", "") == "1.17-S489")
        for k in ("BASE", "SETTINGS_PATH", "SETTINGS_AUDIT", "HOLD_LEDGER", "LOAN_PAGES_PATH"):
            setattr(Pn, k, getattr(Po, k))                     # the kit engine reads the box's own files, as it will once placed
        privn = Pn.private_loan_names(Pn.load_settings())
        settings = Pn.load_settings()

        sr = None
        try:                                                   # the register's own frozen-sheet reader, from a private copy
            srd = os.path.join(scratch, "sr")
            os.makedirs(srd)
            shutil.copy2(os.path.join(live, "staff_register.py"), srd)
            os.chdir(srd)
            sr = load(os.path.join(srd, "staff_register.py"), "sr_live_s522")
            check("the register's reader is there", hasattr(sr, "locked_snapshot"))
        except SystemExit:
            raise
        except Exception as e:
            print("   (the register app could not be loaded here: %s -- the frozen-sheet read-back is skipped)" % type(e).__name__)
            sr = None
        if os.environ.get("S522_NEED_REGISTER") == "1":
            check("on the box the register's reader must load", sr is not None)

        # ---------------- PART 1 ----------------
        rows1 = Lo.load_ledger()
        check("both ledger modules read the same rows", norm(rows1) == norm(Ln.load_ledger()))
        check("both ledger modules see the same open advances", norm(Lo.open_advances()) == norm(Ln.open_advances()))
        for a in Lo.open_advances():
            check("schedule state unchanged for an open advance",
                  norm(Lo.schedule_state(a["issue"], rows=rows1)) == norm(Ln.schedule_state(a["issue"], rows=rows1)))
        today = datetime.date.today().strftime("%Y-%m")
        months = sorted(set(m for m in os.environ.get("MONTHS", "2026-08,2026-09,%s" % today).split(",") if m))
        done = []
        n_slips = n_pages = 0
        for ym in months:
            check("%s: the loans view is the same" % ym, norm(Lo.loans_view(rows1, ym)) == norm(Ln.loans_view(rows1, ym)))
            try:
                ro = compute_with(Po, Lo, sc1, ym)
            except SystemExit:
                raise
            except Exception as e:
                print("   %s: the LIVE engine cannot compute this month here (%s) -- skipped" % (ym, type(e).__name__))
                continue
            rn = compute_with(Pn, Ln, sc1, ym)
            check("%s: the same people in the same order" % ym, [s["name"] for s in ro["staff"]] == [s["name"] for s in rn["staff"]])
            check("%s: closed / enforced / notes agree" % ym,
                  ro["ledger_closed"] == rn["ledger_closed"] and ro["enforced"] == rn["enforced"] and ro["notes"] == rn["notes"])
            for a, b in zip(ro["staff"], rn["staff"]):
                check("%s: every key of a person is there in the kit's result" % ym, set(a) == set(b))
                for k in a:
                    check("%s %s: '%s' is the same in both engines" % (ym, a["name"], k), norm(a[k]) == norm(b[k]))
            check("%s: Sheet 2 is byte for byte the live engine's" % ym, Po.sheet2_html(ro) == Pn.sheet2_html(rn))
            for p in privn:
                if any(str(s["name"]).strip().lower() == p for s in rn["staff"]):
                    check("%s: the private loan page is byte for byte the live engine's" % ym,
                          Po.sheet2_html(ro, staff=p) == Pn.sheet2_html(rn, staff=p))
                    n_pages += 1
            so, sn = Po.sheets34_html(ro), Pn.sheets34_html(rn)
            nets = [float(s["net"]) for s in rn["staff"]]
            total = int(round(sum(nets)))
            if sr is not None:
                a_rows, a_err = sr.locked_snapshot(so, total)
                b_rows, b_err = sr.locked_snapshot(sn, total)
                check("%s: the register reads the live Sheet 3 (%s)" % (ym, a_err), a_rows is not None)
                check("%s: the register reads the kit's Sheet 3 with separators (%s)" % (ym, b_err), b_rows is not None)
                check("%s: the lock would freeze the same rows and figures from both" % ym, norm(a_rows) == norm(b_rows))
            m = re.search(r"SHEET 4 · SALARY PAYMENT.*?<table>(.*?)</table>", sn, re.S)
            check("%s: Sheet 4 is there" % ym, m is not None)
            trs = re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S)
            body = [re.findall(r"<td[^>]*>(.*?)</td>", t, re.S) for t in trs]
            body = [c for c in body if c]
            tot_rows = [c for c in body if len(c) >= 3 and "TOTAL" in c[1]]
            ppl = [c for c in body if c not in tot_rows]
            check("%s: Sheet 4 has one row per person and ONE total row" % ym, len(ppl) == len(rn["staff"]) and len(tot_rows) == 1)
            check("%s: each Sheet 4 amount is that person's net" % ym,
                  all(abs(num(c[2]) - float(s["net"])) < 0.005 for c, s in zip(ppl, rn["staff"])))
            check("%s: the Sheet 4 total is the sum of the amounts above it" % ym, abs(num(tot_rows[0][2]) - sum(nets)) < 0.005)
            check("%s: Sheet 3's dress / I-card footnote is the settings' own" % ym, Pn._di_words(settings) in sn)
            for a, b in zip(ro["staff"], rn["staff"]):
                if Pn.has_slip(b, rn):
                    sa, sb = Po.slip_html(a, ro, "x"), Pn.slip_html(b, rn, "x")
                    check("%s: a slip is the live engine's save the negative-net line and the new skipped-kist line" % ym,
                          NEG.sub("", sa) == SKIPROW.sub("", NEG.sub("", sb)))
                    if float(b["net"]) < 0:
                        check("%s: a negative slip says nothing carries it" % ym, "apne-aap nahi katega" in sb)
                    n_slips += 1
            done.append("%s: %d people · %d slips · %s" % (ym, len(rn["staff"]), sum(1 for s in rn["staff"] if Pn.has_slip(s, rn)),
                                                          "ledger closed" if rn["ledger_closed"] else "ledger NOT closed"))
        check("at least one month was walked", bool(done))

        # ---------------- PART 2 ----------------
        rows_all = Ln.load_ledger()
        _cl = Ln.closed_months(rows_all)                       # newest first
        M = Ln._month_plus(_cl[0], 1) if _cl else today        # the month the Advances card offers by default
        sc2 = copy_ledger(ledger_dir, os.path.join(scratch, "led_skip"))
        sc3 = copy_ledger(ledger_dir, os.path.join(scratch, "led_base"))
        users = {"walk": {"role": "checker"}}
        Ln.LEDGER_DIR = sc2
        people = sorted({a["issue"]["staff"] for a in Ln.open_advances() if Ln.skip_month_lines(a["issue"]["staff"], M)})
        check("at least one person has a long-term loan to skip in %s" % M, bool(people))

        def _int_line(p_, m_):                                  # a loan with interest among his skippable lines
            return any(a_["interest"] for a_ in Ln.skip_month_lines(p_, m_))
        p_int = next((p for p in people if _int_line(p, M)), None)   # read before anything is skipped
        skipped_lines = {}
        for p in people:
            before = set(Ln.fy_defer_months(p, M))
            lines = Ln.skip_month_lines(p, M)
            rr = Ln.record_skip_month(users, "walk", p, M, "walk_s522")
            check("one tap = one skip-marked DEFER per long-term line",
                  len(rr) == len(lines) and all(r["category"] == "ADVANCE_DEFER" and r["skip_month"] and r["amount"] == 0
                                                and r["date_from"] == M for r in rr))
            months_now = set(Ln.fy_defer_months(p, M))
            check("the month counts ONCE in the year", months_now == before | {M})
            pen = len(before - {M}) >= Ln.DEFERS_FREE_FY
            check("the penalty only where the year's two free months are used, and only on a loan with interest",
                  all(bool(r["defer_penalty"]) == (pen and bool(next(a for a in lines if a["issue"]["id"] == r["contra_of"])["interest"]))
                      for r in rr))
            try:
                Ln.record_skip_month(users, "walk", p, M, "again")
                check("a second tap must be refused", False)
            except ValueError:
                check("a second tap is refused", True)
            check("the statement says MONTH SKIPPED on every row of the tap", all(r["narration"].startswith("MONTH SKIPPED") for r in rr))
            skipped_lines[p] = {r["contra_of"]: r for r in rr}
        # before the close: the kit engine already shows the month as skipped and plans nothing for it
        rk = compute_with(Pn, Ln, sc2, M)
        n_marked = 0
        for st in rk["staff"]:
            if st["name"] not in skipped_lines:
                continue
            for t in (st.get("ledger_money") or {}).get("lines", []):
                if t["id"] in skipped_lines[st["name"]]:
                    check("a skipped line plans nothing for the skipped month", not [1 for m_, p_, i_ in t["proj"] if m_ == M and p_ + i_ > 0.005])
                    check("a skipped line is marked skipped", t["marks"].get(M) == "skip")
                    n_marked += 1
        check("every skipped line was met in the engine's reading", n_marked == sum(len(v) for v in skipped_lines.values()))
        # the close, on both copies, by the kit's ledger
        Ln.LEDGER_DIR = sc2
        Ln.close_month(users, "walk", M)
        Ln.LEDGER_DIR = sc3
        Ln.close_month(users, "walk", M)
        Ln.LEDGER_DIR = sc2
        r2 = Ln.load_ledger()
        Ln.LEDGER_DIR = sc3
        r3 = Ln.load_ledger()

        def coll(rows, staff):
            return sorted((r["contra_of"], r["category"], r["amount"]) for r in rows
                          if r.get("closed_month") == M and r["staff"] == staff
                          and r["category"] in ("ADVANCE_INSTALMENT", "LOAN_INTEREST", "LOAN_CAPITALISE", "CAPACITY_HOLD"))
        everyone = sorted({r["staff"] for r in r3 if r.get("closed_month") == M})
        for s in everyone:
            if s in skipped_lines:
                got = [c for c in coll(r2, s) if c[0] in skipped_lines[s]]
                check("a skipped line collects nothing in the skipped month",
                      all(c[1] == "LOAN_CAPITALISE" and skipped_lines[s][c[0]]["defer_penalty"]
                          and not skipped_lines[s][c[0]]["penalty_waived"] for c in got))
            else:
                check("a person who did not skip is collected exactly as without the skip", coll(r2, s) == coll(r3, s))
        rk = compute_with(Pn, Ln, sc2, M)
        rl = compute_with(Po, Lo, sc2, M)
        check("the closed month reads as closed", rk["ledger_closed"] and rl["ledger_closed"])
        n_skip_pages = n_skip_slips = n_skip_strips = 0
        shown = set()
        for a, b in zip(rl["staff"], rk["staff"]):
            for k in ("base", "base_full", "adv_ded", "adv_ded_full", "net", "net_exact", "net_full", "open_bal"):
                check("%s: '%s' is the same money in the live and the kit engine after a skipped month" % (M, k), norm(a.get(k)) == norm(b.get(k)))
            pa, pb = a.get("priv") or {}, b.get("priv") or {}
            for k in ("kept", "cut", "cut_shown", "paid", "reserve"):
                check("%s: the private split '%s' is the same money in both engines" % (M, k), norm(pa.get(k)) == norm(pb.get(k)))
            if b["name"] not in skipped_lines:
                continue
            if pb:
                check("the private split reads skipped", pb["status"] == "skip")
                check("the instalment kept aside is paid back to him", abs(float(pb["paid"]) - float(pb["kept"])) < 0.005)
                check("full net == common net + paid to him", abs(float(b["net_full"]) - (float(b["net"]) + float(pb["reserve"]))) <= 10.0)
                page = Pn.sheet2_html(rk, staff=b["name"])
                check("the private loan page shows the month as Skipped", ">Skipped</span>" in page and "paid to him" in page)
                n_skip_pages += 1
                shown.add(b["name"])
            v = b["views"]
            for L in v["loans"]:
                if set(L["ids"]) & set(skipped_lines[b["name"]]):
                    check("Sheet 2's strip carries the skipped month", (M, 0.0, "skip") in [(m_, round(a_, 2), k_) for m_, a_, k_ in L["strip"]])
                    n_skip_strips += 1
                    shown.add(b["name"])
            if n_skip_strips:
                check("Sheet 2 prints 'skipped' for the month", "skipped</span>" in Pn.sheet2_html(rk))
            if Pn.has_slip(b, rk) and [L for L in v["loans"] if set(L["ids"]) & set(skipped_lines[b["name"]]) and L["cut"] <= 0.005]:
                check("the slip says the kist was skipped", "is mahine skip" in Pn.slip_html(b, rk, "x"))
                n_skip_slips += 1
        check("every person who skipped is shown as skipped on his private page or on Sheet 2", shown == set(skipped_lines))
        # the penalty path, on two more copies: the third skipped month of the year, charged and waived
        n_pen = 0
        why_no_pen = "" if p_int else "nobody has a loan with interest to skip in %s" % M
        if p_int:
            for waive in (False, True):
                scx = copy_ledger(ledger_dir, os.path.join(scratch, "led_pen_%d" % waive))
                Ln.LEDGER_DIR = scx
                used = [m_ for m_ in Ln.fy_defer_months(p_int, M)]
                mm, k = M, 0
                while len(set(used)) < Ln.DEFERS_FREE_FY and k < 12:          # use up the year's free months on later months
                    if Ln.skip_month_lines(p_int, mm) and Ln.fy_of(mm) == Ln.fy_of(M):
                        Ln.record_skip_month(users, "walk", p_int, mm, "walk free")
                        used = Ln.fy_defer_months(p_int, M)
                    mm = Ln._month_plus(mm, 1); k += 1
                while (not _int_line(p_int, mm) or Ln.fy_of(mm) != Ln.fy_of(M)) and k < 12:
                    mm = Ln._month_plus(mm, 1); k += 1
                if not (len(set(used)) >= Ln.DEFERS_FREE_FY and Ln.fy_of(mm) == Ln.fy_of(M) and _int_line(p_int, mm)):
                    why_no_pen = "fewer than three skippable months left in %s" % Ln.fy_of(M)
                else:
                    rr = Ln.record_skip_month(users, "walk", p_int, mm, "walk third", waive_penalty=waive)
                    ints = [r for r in rr if next(x for x in Ln.open_advances() if x["issue"]["id"] == r["contra_of"])["interest"]]
                    check("the third skipped month charges each loan with interest%s" % (" — waived" if waive else ""),
                          bool(ints) and all(r["defer_penalty"] and bool(r["penalty_waived"]) == waive for r in ints)
                          and not [r for r in rr if r not in ints and r["defer_penalty"]])
                    n_pen += 1
        check("the penalty path ran on both copies%s" % ((" — not possible: " + why_no_pen) if why_no_pen else ""),
              n_pen == 2 or (bool(why_no_pen) and n_pen == 0))
        check("the LIVE ledger is byte for byte what it was before the walk", md5_file(led_file) == led_md5_before)
        check("the kit ledger's own selftest passes", _selftest(kit, scratch, "staff_ledger.py", "SELFTEST PASSED"))
        check("the kit engine's own selftest passes", _selftest(kit, scratch, "salary_policy.py", "PASS"))
        for ln in done:
            print("   " + ln)
        print("   %s skipped on a copy: %d people · %d private pages · %d loan strips · %d slips · penalty path %d of 2"
              % (M, len(people), n_skip_pages, n_skip_strips, n_skip_slips, n_pen))
        print("WALK OK — %d checks; %d month(s); the live ledger untouched" % (N[0], len(done)))
    finally:
        os.chdir("/tmp")
        shutil.rmtree(scratch, ignore_errors=True)


def _selftest(kit, scratch, name, last):
    """A kit file's own selftest, in a private folder (each writes beside itself or in its own temp folder)."""
    import subprocess
    d = os.path.join(scratch, "st_" + name.split(".")[0])
    os.makedirs(d)
    shutil.copy2(os.path.join(kit, name), d)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TMPDIR"] = d                                          # its temp folders go with the scratch folder
    out = subprocess.run([sys.executable, "-B", os.path.join(d, name), "--selftest"],
                         cwd=d, env=env, capture_output=True, text=True, timeout=280)
    tail = (out.stdout.strip().splitlines() or [""])[-1]
    return out.returncode == 0 and tail.startswith(last)


if __name__ == "__main__":
    main()
