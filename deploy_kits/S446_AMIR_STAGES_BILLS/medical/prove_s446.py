# -*- coding: utf-8 -*-
r"""prove_s446.py -- the proof for marg_txt S446 (F-674): Marg's *** in an item's second column.

    python -B prove_s446.py            (from this folder; writes PROVE_S446_RESULT.txt beside it)

Loads the OLD reader (S397, 38d85298, the medical PC's live bytes) and the NEW one (S446, built by
make_marg_txt_s446.py) side by side and runs both over every text export there is. Converted .XLS files
carry patients' names, so they are written only into _work\ here and removed at the end; this proof
prints counts, dates, bill numbers and rupees only -- never a name from a bill row.
"""
import ast, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, time
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OLD_PATH = os.path.join(REPO, "deploy_kits", "S397_STOCK_TEXT", "marg_txt.py")
WATCH_PATH = os.path.join(REPO, "deploy_kits", "S397_STOCK_TEXT", "marg_watch.py")
NEW_PATH = os.path.join(HERE, "marg_txt.py")
REF = os.path.join(HERE, "_probe", "ref")            # copies of the server's readers (taken out of deploy_kits)
DRIVE = r"H:\My Drive\Clinic Data Archive"
RT = os.path.join(DRIVE, "FromMedical", "refused_text")
KIT_TXT = os.path.join(DRIVE, "ToMedical", "_kit", "marg_txt.py")
F30 = os.path.join(RT, "20260930-221037__report__1a0ec847841e5d303d3c5768bd9d9d4e.txt")
F30B = os.path.join(RT, "20260930-221033__user_aa2031800700__956234ffda445746ca7b889763f235cd.txt")
F01 = os.path.join(RT, "20261001-125547__user_ab2706232559__f87d791be5f719416b11314e5ddfacdd.txt")
WORK = os.path.join(HERE, "_work")
OLD_MD5 = "38d85298f1627ab22b59c9f3459d8764"

LOG = []


def say(m=""):
    print(m)
    LOG.append(m)


RES = []


def check(label, cond, got=None):
    RES.append(bool(cond))
    say(("  ok   " if cond else "  FAIL ") + label + ("" if got is None else "   [%s]" % (got,)))


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def verdict(M, raw):
    """('CONVERTS', xls bytes) or ('REFUSED'/'NOT_THIS', message)."""
    try:
        x, info = M.convert(raw)
        return "CONVERTS", x
    except M.NotThisReport as e:
        return "NOT_THIS", str(e)
    except M.Refused as e:
        return "REFUSED", str(e)


def safe(msg):
    """A refusal message without the quoted line (it could carry text from a bill row)."""
    return msg.split(": '")[0].split(': "')[0]


def with_line(raw, n, fn):
    """The same bytes with line n (1-based, as the reader counts) changed by fn; CRLF kept."""
    ls = raw.split(b"\r\n")
    ls[n - 1] = fn(ls[n - 1])
    return b"\r\n".join(ls)


def line_no(raw, pred):
    for i, l in enumerate(raw.split(b"\r\n"), 1):
        if pred(l):
            return i
    return None


def worker():
    """--watcher <dir> <refused file>...: the LIVE marg_watch (S397) with the marg_txt in <dir> beside it,
    started as the medical PC starts it: does retry_refused take the refused texts now?"""
    d = sys.argv[2]
    sys.path.insert(0, d)
    W = load("marg_watch", os.path.join(d, "marg_watch.py"))
    W.TXT_LIVE_FORCE = True
    root = os.path.join(d, "SendToClinic")
    spool = os.path.join(root, "_captured")
    ref = os.path.join(root, "_captured_txt", "refused")
    os.makedirs(ref)
    for p in sys.argv[3:]:
        shutil.copyfile(p, os.path.join(ref, os.path.basename(p)))      # copied now: mtime = now, in the window
    msgs = []
    took = W.retry_refused(spool, W.prime_captured(spool), msgs.append)
    xs = sorted(f for f in os.listdir(spool)) if os.path.isdir(spool) else []
    out = {"took": took, "spool": [(f.split("__")[1], W.md5_of(os.path.join(spool, f))) for f in xs],
           "said": [m.split(":")[0].strip() for m in msgs], "days": W.CENSUS_DAYS,
           "version": W._marg_txt().VERSION}
    print("RESULT " + json.dumps(out))
    return 0


def main():
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    say("PROVE_S446  %s IST  (marg_txt S446, F-674)" % time.strftime("%Y-%m-%d %H:%M:%S"))
    old_b, new_b = open(OLD_PATH, "rb").read(), open(NEW_PATH, "rb").read()
    say("old reader %s  (%s)" % (md5(old_b), os.path.relpath(OLD_PATH, REPO)))
    say("new reader %s  (built by make_marg_txt_s446.py)" % md5(new_b))
    say("")
    say("0. the bytes")
    check("the old reader is the medical PC's live S397 (38d85298) -- the repository copy and Drive ToMedical\\_kit agree",
          md5(old_b) == OLD_MD5 and md5(open(KIT_TXT, "rb").read()) == OLD_MD5)
    check("the new reader parses as Python 3.8 (the medical PC runs 3.11) and compiles here",
          bool(ast.parse(new_b, feature_version=(3, 8))) and bool(compile(new_b, NEW_PATH, "exec")))
    st = subprocess.run([sys.executable, "-B", NEW_PATH, "--selftest"], capture_output=True, text=True, cwd=WORK)
    check("the new reader's own selftest passes (with the S446 checks)", st.stdout.strip().endswith("SELFTEST OK"),
          "%d OK, %d FAIL" % (st.stdout.count("  OK   "), st.stdout.count("  FAIL ")))
    OLD = load("marg_txt_old", OLD_PATH)
    NEW = load("marg_txt_new", NEW_PATH)

    raw30, raw30b, raw01 = open(F30, "rb").read(), open(F30B, "rb").read(), open(F01, "rb").read()
    say("")
    say("1. negative control: the OLD reader refuses the 30-Sep sale (and its two copies) at line 52")
    for lab, raw in (("30-Sep report.txt 1a0ec847", raw30), ("30-Sep user_aa..txt 956234ff", raw30b),
                     ("01-Oct re-export f87d791b", raw01)):
        v, m = verdict(OLD, raw)
        check("OLD refuses %s: line 52, the *** line" % lab,
              v == "REFUSED" and m.startswith("line 52: a line of a kind this reader does not know") and "***" in m,
              safe(m))

    say("")
    say("2. the NEW reader takes the 30-Sep sale whole")
    v, x30 = verdict(NEW, raw30)
    check("NEW converts the 30-Sep report.txt", v == "CONVERTS", "%d bytes, md5 %s" % (len(x30), md5(x30)) if v == "CONVERTS" else safe(x30))
    rows = NEW.to_rows(raw30)
    bills = [r for r in rows if NEW.RE_BILL.match(str(r[0]))]
    grand = [r for r in rows if r[2] == "GRAND TOTAL :"]
    days = [r for r in rows if r[2] == "DAY TOTAL :"]
    items = [r for r in rows if r[0] == "" and r[1][:1].isdigit()]
    check("its own rows: 24 bills, first %s last %s" % (bills[0][0], bills[-1][0]) if bills else "its own rows: 24 bills",
          len(bills) == 24, len(bills))
    check("its own rows: GRAND TOTAL printed Rs 23,598.00 net, footer 'Bills: 24'",
          len(grand) == 1 and grand[0][7] == 23598.0 and grand[0][1].replace(" ", "") == "Bills:24",
          "gross %.2f disc %.2f net %.2f cash %.2f" % (grand[0][3], grand[0][4], grand[0][7], grand[0][8]))
    check("its own rows: the 24 bills' NET add to the GRAND TOTAL NET (23,598.00)",
          abs(sum(b[7] for b in bills) - 23598.0) < 0.005, "%.2f" % sum(b[7] for b in bills))
    star = [r for r in items if "***" in r[1]]
    check("its own rows: the one *** line is bill A003920's item 4, Rs 180.00, qty 1, kept as Marg prints it",
          len(star) == 1 and star[0][1] == "4 *** FINGER EXTENSION SPL 1*1" and star[0][2] == 1.0
          and star[0][3].strip() == "180.00", star[0][1:4] if star else None)
    p30 = os.path.join(WORK, "conv_30sep.XLS")
    open(p30, "wb").write(x30)

    sys.path.insert(0, REF)
    FR = load("marg_report", os.path.join(REF, "marg_report.py"))
    A = FR.read_report(p30, keep_items=True)
    nb = sum(len(d["bills"]) for d in A["days"])
    ni = sum(len(d["items"]) for d in A["days"])
    check("server finance reader (marg_report, S444 copy f9370dde) reads it clean: every DAY TOTAL = its bills, "
          "GRAND = the days, footer = bills read", A["ok"] and not A["errors"], A["errors"][:2])
    check("finance reader: 24 bills, %d item lines, one day 2026-09-30, GRAND net Rs 23,598.00" % ni,
          nb == 24 and A["footer_bills"] == 24 and [d["date"] for d in A["days"]] == ["2026-09-30"]
          and A["grand"]["net"] == 2359800 and len(items) == ni,
          "grand paise %s" % json.dumps(A["grand"]))
    R = load("marg_router", os.path.join(REF, "marg_router.py"))
    sh = R.open_sheet(p30)
    pre = R.read_preamble(sh)
    sig, status, why = R.identify(pre[0], pre[1], R.load_signatures(os.path.join(REF, "signatures.json")))
    check("router (S302 copy) identifies it as Marg's Excel is: SALE_BILLWISE / DETAIL",
          status == "IDENTIFIED" and (sig or {}).get("type") == "SALE_BILLWISE" and (sig or {}).get("variant") == "DETAIL",
          ((sig or {}).get("type"), (sig or {}).get("variant"), status))
    MI = load("marg_ingest", os.path.join(REF, "marg_ingest.py"))
    lines = MI.sale_lines(p30)
    fl = [t for t in lines if "FINGER EXTENSION" in (t[4] or "")]
    check("the door's item lines (marg_ingest.sale_lines): %d, the *** line among them at Rs 180.00, bill A003920" % len(lines),
          len(lines) == ni and len(fl) == 1 and fl[0][9] == 18000 and fl[0][1] == "A003920",
          (fl[0][1], fl[0][3], fl[0][9]) if fl else None)
    SP = load("marg_read", os.path.join(REF, "marg_read.py"))
    fam, SR, _ = SP.read_file(p30)
    bad = [c for c in getattr(SR, "checks", []) if not c[1]]
    sl = [l for b in SR.data["bills"] for l in b["lines"]] if SR else []
    fsl = [l for l in sl if l["name"].startswith("FINGER EXTENSION")]
    check("the spine reader (marg_read S331) reads it SALE_BILLWISE, every check passing, no anomaly; "
          "it reads the *** line as Marg's Excel (seq 4, pack 1*1)",
          fam == "SALE_BILLWISE" and SR.ok and not bad and not SR.anomalies and len(fsl) == 1
          and fsl[0]["seq"] == 4 and fsl[0]["pack"] == "1*1" and fsl[0]["rate_p"] == 18000,
          "%d bills, %d lines, anomalies %d" % (len(SR.data["bills"]), len(sl), len(SR.anomalies)))

    say("")
    say("3. the 30-Sep copies and the 01-Oct re-export")
    for lab, raw in (("30-Sep user_aa..txt 956234ff", raw30b), ("01-Oct re-export f87d791b", raw01)):
        v, x = verdict(NEW, raw)
        r2 = NEW.to_rows(raw) if v == "CONVERTS" else []
        b2 = [r for r in r2 if NEW.RE_BILL.match(str(r[0]))]
        g2 = [r for r in r2 if r[2] == "GRAND TOTAL :"]
        check("NEW converts %s: 24 bills, GRAND net Rs 23,598.00" % lab,
              v == "CONVERTS" and len(b2) == 24 and g2 and g2[0][7] == 23598.0,
              ("xls md5 %s, %s the 30-Sep report.txt's" % (md5(x), "the SAME bytes as" if x == x30 else "NOT the same bytes as"))
              if v == "CONVERTS" else safe(x))
        if v == "CONVERTS" and x == x30:
            check("  ...and every cell equal to the 30-Sep report.txt's rows", r2 == rows, "%d rows" % len(r2))
        elif v == "CONVERTS":
            col2 = re.compile(r"^(\d+)\s+(\d+|\*\*\*)\s")
            def bare(rr):
                return [[col2.sub(r"\1 ", c) if (j == 1 and r[0] == "") else c for j, c in enumerate(r)] for r in rr]
            diffs = [(i, j) for i, (p, q) in enumerate(zip(rows, r2)) for j in range(9) if p[j] != q[j]]
            only2 = all(j == 1 and rows[i][0] == "" for i, j in diffs)
            check("  ...its bills, amounts, totals and item lines are the 30-Sep ones; only the items' SECOND column "
                  "differs (%d item lines) -- the figure Marg prints there is as of the moment of export"
                  % len(diffs), len(r2) == len(rows) and only2 and bare(r2) == bare(rows), "%d rows" % len(r2))

    say("")
    say("4. the only difference is the *** line: with a figure in that column both readers agree byte for byte")
    n52 = line_no(raw30, lambda l: b" *** FINGER EXTENSION" in l)
    check("the *** line is line %s of the file" % n52, n52 == 52)
    fig = with_line(raw30, 52, lambda l: l.replace(b"   4 *** FINGER", b"   4 999 FINGER"))
    vo, xo = verdict(OLD, fig)
    vn, xn = verdict(NEW, fig)
    check("30-Sep with '999' in that column: OLD converts, NEW converts, the same bytes",
          vo == vn == "CONVERTS" and xo == xn, md5(xn) if vn == "CONVERTS" else (vo, vn))
    rf = NEW.to_rows(fig)
    diff = [(i, c) for i, (a, b) in enumerate(zip(rf, rows)) for c in range(9) if a[c] != b[c]]
    check("NEW on the real file vs that: one cell differs, the item's own text ('4 *** ...' / '4 999 ...')",
          len(rf) == len(rows) and len(diff) == 1 and rows[diff[0][0]][1].startswith("4 *** FINGER"), diff)

    say("")
    say("5. parity: every other text export there is, OLD and NEW side by side")
    corpus = []
    for n in sorted(os.listdir(RT)):
        if n.lower().endswith(".txt") and not n.lower().endswith(".why.txt"):
            corpus.append(("refused_text\\" + n[:22] + ".." + n[-12:], open(os.path.join(RT, n), "rb").read()))
    corpus.append(("marg_txt SELFTEST_SAMPLE (sale)", OLD.SELFTEST_SAMPLE))
    corpus.append(("marg_txt STOCK_SAMPLE (stock)", OLD.STOCK_SAMPLE))
    for lab, raw in (("30-Sep with 999", fig), ("30-Sep copy with 999", raw30b.replace(b"   4 *** FINGER", b"   4 999 FINGER")),
                     ("01-Oct with 999", raw01.replace(b"   4 *** FINGER", b"   4 999 FINGER"))):
        corpus.append((lab, raw))
    for lab, p in PARITY_EXTRA:
        if os.path.isfile(p):
            corpus.append((lab, open(p, "rb").read()))
    same, changed = 0, []
    for lab, raw in corpus:
        vo, xo = verdict(OLD, raw)
        vn, xn = verdict(NEW, raw)
        star = raw in (raw30, raw30b, raw01)
        if star:
            ok = vo == "REFUSED" and vn == "CONVERTS"
            changed.append(lab)
            say("    %-46s OLD %-8s NEW %-8s  <- the *** file: the one intended change" % (lab, vo, vn))
        else:
            ok = vo == vn and xo == xn
            same += ok
            say("    %-46s OLD %-8s NEW %-8s  %s" % (lab, vo, vn, ("same bytes " + md5(xn)[:8]) if vn == "CONVERTS"
                                                     else ("same reason: " + safe(xn)[:60]) if ok else "DIFFERENT"))
        RES.append(ok)
    check("every file except the three *** copies: the same verdict, and the same .XLS bytes where it converts (%d files)"
          % same, same == len(corpus) - len(changed))
    check("the three *** copies (30-Sep x2, 01-Oct) are the only verdicts that change", len(changed) == 3, changed)
    stk = [raw for lab, raw in corpus if "47896301" in lab]
    xs = NEW.convert(stk[0])[0] if stk else b""
    check("the S397 proof's own file (24-Sep closing stock text 6da7cfb8) converts to the very .XLS PROVE_S397 recorded "
          "(451c3d573c97cf91dd820f5d14060d77)", md5(xs) == "451c3d573c97cf91dd820f5d14060d77", md5(xs))
    fires = []
    for lab, raw in corpus:
        for i, l in enumerate(raw.decode("latin-1").replace("\r\n", "\n").split("\n"), 1):
            s = l.rstrip()
            if NEW.RE_ITEM_STARS.match(s) and not NEW.RE_ITEM.match(s):
                fires.append((lab[:22], i))
    check("line by line over the whole corpus: the new rule takes a line the old item rule did not ONLY on the "
          "three *** lines (line 52 of each copy)", sorted(n for _, n in fires) == [52, 52, 52], fires)

    say("")
    say("6. *** anywhere else still refuses (crafted copies of the 30-Sep file, line 52 or its bill)")
    fix = lambda l: l.replace(b"   4 *** FINGER", b"   4  12 FINGER")            # the column back to a figure
    crafted = [
        ("*** moved into the quantity", 52, lambda l: fix(l).replace(b"1*1             1      180.00", b"1*1           ***      180.00")),
        ("*** moved into the amount (rate)", 52, lambda l: fix(l).replace(b"1*1             1      180.00", b"1*1             1         ***")),
        ("*** moved into the line number", 52, lambda l: l.replace(b"            4 *** FINGER", b"          ***  12 FINGER")),
        ("**** (four) in the column", 52, lambda l: l.replace(b"   4 *** FINGER", b"  4 **** FINGER")),
        ("** (two) in the column", 52, lambda l: l.replace(b"   4 *** FINGER", b"   4  ** FINGER")),
        ("*** with no space before the name", 52, lambda l: l.replace(b"   4 *** FINGER", b"   4 ***FINGER")),
    ]
    nb48 = line_no(raw30, lambda l: l.startswith(b"A003920"))
    crafted.append(("*** in bill A003920's CASH amount", nb48, lambda l: l[:-7] + b"    ***"))
    crafted.append(("*** in bill A003920's NET amount", nb48, lambda l: l[:-19] + b"    ***" + l[-12:]))
    nday = line_no(raw30, lambda l: b"DAY TOTAL :" in l)
    crafted.append(("*** in the DAY TOTAL", nday, lambda l: l[:-7] + b"    ***"))
    ngr = line_no(raw30, lambda l: b"GRAND TOTAL :" in l)
    crafted.append(("*** in the GRAND TOTAL", ngr, lambda l: l[:-7] + b"    ***"))
    for lab, n, fn in crafted:
        raw = with_line(raw30, n, fn)
        if lab.startswith("*** moved into the q") or lab.startswith("*** moved into the a"):
            vo, mo = verdict(OLD, raw)
        else:
            vo, mo = "REFUSED", ""
        vn, mn = verdict(NEW, raw)
        check("refused: %s (line %d)" % (lab, n), raw != raw30 and vn == "REFUSED" and vo == "REFUSED",
              safe(mn) if vn != "CONVERTS" else "CONVERTED")
    trunc = raw30[:raw30.find(b"GRAND TOTAL")]
    vn, mn = verdict(NEW, trunc)
    check("refused/left alone: the 30-Sep file cut short before its GRAND TOTAL", vn in ("REFUSED", "NOT_THIS"), safe(mn))

    say("")
    say("7. the medical PC's own path: the LIVE marg_watch (S397, unchanged) at its next start, with each reader")
    res = {}
    for tag, src in (("old", OLD_PATH), ("new", NEW_PATH)):
        d = os.path.join(WORK, "pc_" + tag)
        os.makedirs(d)
        shutil.copyfile(WATCH_PATH, os.path.join(d, "marg_watch.py"))
        shutil.copyfile(src, os.path.join(d, "marg_txt.py"))
        env = dict(os.environ, TMP=WORK, TEMP=WORK, PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--watcher", d, F30B, F30, F01],
                           capture_output=True, text=True, cwd=WORK, env=env)
        line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
        res[tag] = json.loads(line[0][7:]) if line else {"took": None, "err": p.stderr[-300:]}
    check("with the OLD reader: the refused 30-Sep texts are offered again and refused again (0 taken)",
          res["old"].get("took") == 0 and not res["old"].get("spool"), res["old"].get("took"))
    sp = res["new"].get("spool") or []
    x01 = NEW.convert(raw01)[0]
    check("with the NEW reader: retry_refused takes the 30-Sep sale, exactly marg_txt's bytes; its 22:10:33 twin is "
          "the same .XLS ('already taken'); the 01-Oct re-export is a SECOND .XLS of the same sale (other bytes)",
          res["new"].get("took") == 2 and sorted(m for _, m in sp) == sorted([md5(x30), md5(x01)]),
          (res["new"].get("took"), sp))
    sw = subprocess.run([sys.executable, "-B", os.path.join(WORK, "pc_new", "marg_watch.py"), "--selftest"],
                        capture_output=True, text=True, cwd=WORK, env=dict(os.environ, TMP=WORK, TEMP=WORK))
    check("the live marg_watch's own selftest passes with the new reader beside it",
          "SELFTEST OK" in sw.stdout, "%d OK, %d FAIL" % (sw.stdout.count("  OK   "), sw.stdout.count("  FAIL ")))
    say("    (marg_watch offers refused texts again ONLY at its start, and only those under %s days old)"
        % res["new"].get("days"))

    shutil.rmtree(WORK, ignore_errors=True)
    say("")
    say("PROVE_S446 %s -- %d/%d" % ("GREEN" if all(RES) else "RED", sum(RES), len(RES)))
    with open(os.path.join(HERE, "PROVE_S446_RESULT.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(LOG) + "\n")
    return 0 if all(RES) else 1


PARITY_EXTRA = []        # (label, path) of any further text export found on this PC -- see the result


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--watcher":
        sys.exit(worker())
    sys.exit(main())
