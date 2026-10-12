#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s533.py -- the builder of kit S533_AMIR_DAY_PAGE (11/12-Oct-2026; D706 D708 D709 D712; F-839 F-861 F-863 F-864).

    python3 -B make_s533.py --finance DIR --briefs DIR --out DIR [--print-to]

Reads the LIVE files at their FROM pins (anything else: stop), makes anchored edits (each anchor must occur exactly once, else it
stops), compiles every python result on the python that runs it, and writes the results into --out (nothing else is written).
With --print-to the built md5s are printed and accepted (packing the kit); without it every result must equal its TO pin (PINS.sh).

  amir_day.py      replaced whole: the kit's amir_day.py (beside this file), checked against its TO pin; the live file must be at FROM.
  stock_app.py     section 3: the comment lines naming amir_duties and _S444_RENAMES_CACHE cut; _s444_renames and amir_duties cut
                   (amir_vouchers_open and the board-open record stay); two comment edits.
  purchase_app.py  section 5.1: EXPORT_DAY_SQL (the one expression of an export's day); purchase_bill.first_seen_day (added and
                   back-filled in _ensure, set by _store_bills on insert); scans_to_enter cut (no caller) and its header line edited.
  stockmatch.py    section 5.2: c4 reads the stage's B (renames_wait_stage_a when B is absent); the record rs stays for the hub.
  DUTY_MAP.json    section 6: v10 -> v11 -- the three due_sql strings from amir_day.DUTY_SQL, amir.arrival_bill_entry retired (never due),
                   amir.scan_files' marker, amir.marg_jobs' due_sql reads the reopen (the kit's decision, named in the README).
  DUTY_MAP.md      the rows of those duties, the stale table names, the log line.
  --briefs holding DUTY_MAP.json already at its TO pin (the box's clone pulled early) is accepted as it is.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import json
import os
import sys

PINS = {
    "amir_day.py": ("finance", "f90df5b211c89dc8bdcd2671e163cf94"),
    "stock_app.py": ("finance", "51620064e6849b02f0446b859a722638"),
    "purchase_app.py": ("finance", "c29050c18795a059e3cfbfae252efc21"),
    "stockmatch.py": ("finance", "4a2f9fcdfe969a0ca577c34536dbf9a2"),
    "DUTY_MAP.json": ("briefs", "7aa2f935677928e470454c355553210b"),
    "DUTY_MAP.md": ("briefs", "4888a228282d37133bb888e474d2d63c"),
}
TO_FILE = "PINS.sh"


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def once(t, a, what):
    n = t.count(a)
    if n != 1:
        raise Stop("%s: anchor occurs %d times (must be exactly 1): %r" % (what, n, a[:120]))


def rep(t, a, new, what):
    once(t, a, what)
    return t.replace(a, new, 1)


def cut(t, start, end, new, what):
    """Replace everything from `start` (inclusive) to `end` (exclusive) with `new`; both markers once, start before end."""
    once(t, start, what + " (start)")
    once(t, end, what + " (end)")
    i, j = t.index(start), t.index(end)
    if j <= i:
        raise Stop("%s: the end marker comes before the start marker" % what)
    return t[:i] + new + t[j:]


def kit_amir_day():
    here = os.path.dirname(os.path.abspath(__file__))
    return open(os.path.join(here, "amir_day.py"), "rb").read().decode("utf-8")


# ============================================================================================================== stock_app.py (section 3)
SA_HEAD_OLD = ('# The Marg vouchers of a count wait on his board (/finance/stock/page/amir); until S444 nothing on his own page said so. amir_day\n'
               '# reads amir_duties() for its step 6 "Marg sudhar" card; his visits to the board are remembered (the owner\'s Needs-you line d);\n'
               '# the board carries a BACK bar to /finance/amir and the signed-in name. Read-only but for the board-open row.\n'
               '_S444_RENAMES_CACHE = {}                                       # count_id -> (time, ready, open) -- the proof costs a full report read\n')
SA_HEAD_NEW = ('# The board-open record and amir_vouchers_open stay: the owner\'s Needs-you line (d) in amir_day reads them (S533). The board\n'
               '# carries a BACK bar to /finance/amir and the signed-in name.\n')


def build_stock_app(t):
    t = rep(t, SA_HEAD_OLD, SA_HEAD_NEW, "stock_app: the S444 section's comment lines and the renames cache")
    t = cut(t, "def _s444_renames(con, cid):\n", "def _s444_board_html(html, user):\n", "", "stock_app: _s444_renames and amir_duties")
    t = rep(t, "says the same as Amir's; and\n#   _s444_renames (his step-6 rename duty) asks the stage too.",
            "says the same as Amir's\n#   (S533: _s444_renames retired with amir_day's rebuild).", "stock_app: the S521 header comment")
    t = rep(t, "passed) and by _s444_renames. NEVER handed", "passed) (S533: its second reader _s444_renames is gone). NEVER handed",
            "stock_app: _report_cached's docstring")
    return t


# ============================================================================================================== purchase_app.py (5.1)
PA_NOW = "def now_iso():\n    return dt.datetime.now().replace(microsecond=0).isoformat()\n"
PA_EXPORT_DAY = (PA_NOW + "\n\n"
                 "# S533 (A4): the DAY of a purchase_export row, from Marg's own stamp (YYYYMMDD-HHMMSS) or else its received_at -- the ONE\n"
                 "# expression (amir_day reads it from here); {p} is the table alias prefix ('' or 'e.').\n"
                 "EXPORT_DAY_SQL = (\"CASE WHEN {p}export_stamp GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-*' THEN substr({p}export_stamp,1,4)||'-'||\"\n"
                 "                  \"substr({p}export_stamp,5,2)||'-'||substr({p}export_stamp,7,2) ELSE substr(COALESCE({p}export_stamp, {p}received_at), 1, 10) END\")\n")
PA_ENSURE_OLD = ('    for col, src in (("bw_amount_p", "bw_md5"), ("sw_amount_p", "sw_md5")):\n'
                 '        if col not in have:\n'
                 '            con.execute("ALTER TABLE purchase_bill ADD COLUMN %s INTEGER" % col)\n'
                 '        con.execute("UPDATE purchase_bill SET %s=amount_p WHERE %s IS NULL AND %s IS NOT NULL"\n'
                 '                    % (col, col, src))\n')
PA_ENSURE_NEW = (PA_ENSURE_OLD +
                 '    # S533 (A4): a bill\'s FIRST SIGHT -- the Marg-stamp day of the first purchase export (of any type) that carried it, set by\n'
                 '    # _store_bills on insert. The bills already here are back-filled once from the bill-wise export their row still names (the\n'
                 '    # only day the data holds), else their bill date.\n'
                 '    if "first_seen_day" not in have:\n'
                 '        con.execute("ALTER TABLE purchase_bill ADD COLUMN first_seen_day TEXT")\n'
                 '    con.execute("UPDATE purchase_bill SET first_seen_day = COALESCE((SELECT " + EXPORT_DAY_SQL.format(p="e.") + " FROM purchase_export e "\n'
                 '                "WHERE e.md5 = purchase_bill.bw_md5), substr(bill_date, 1, 10)) WHERE first_seen_day IS NULL")\n')
PA_INSERT_OLD = ('            con.execute("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,"\n'
                 '                        "month,cash_p,credit_p,amount_p,source_md5,%s,%s,date_src) "\n'
                 '                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)" % (col, amt),\n'
                 '                        (key, sup, bno, d, d[:7], cash, credit, cash + credit, md5, md5,\n'
                 '                         cash + credit, typ))\n')
PA_INSERT_NEW = ('            con.execute(("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,"\n'
                 '                         "month,cash_p,credit_p,amount_p,source_md5,%s,%s,date_src,first_seen_day) "\n'
                 '                         "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,(SELECT " + EXPORT_DAY_SQL.format(p="") + " FROM purchase_export WHERE md5 = ?))")\n'
                 '                        % (col, amt),\n'
                 '                        (key, sup, bno, d, d[:7], cash, credit, cash + credit, md5, md5,\n'
                 '                         cash + credit, typ, md5))           # S533: first sight = the day of the export that first carried it\n')
PA_HDR_OLD = "#   * scans_to_enter(con): every captured pharmacy scan not yet linked to a Marg bill, oldest first -- Amir's step 2 lists them.\n"
PA_HDR_NEW = "#   * (S533: scans_to_enter retired -- step 2 reads scans_for_amir)\n"


def build_purchase_app(t):
    t = rep(t, PA_NOW, PA_EXPORT_DAY, "purchase_app: EXPORT_DAY_SQL after now_iso()")
    t = rep(t, PA_ENSURE_OLD, PA_ENSURE_NEW, "purchase_app: _ensure's first_seen_day")
    t = rep(t, PA_INSERT_OLD, PA_INSERT_NEW, "purchase_app: _store_bills' INSERT")
    t = cut(t, "def scans_to_enter(con):\n", "def _s446_files_ok(con, u):\n", "", "purchase_app: scans_to_enter (no caller)")
    t = rep(t, PA_HDR_OLD, PA_HDR_NEW, "purchase_app: the S446 header line naming scans_to_enter")
    return t


# ============================================================================================================== stockmatch.py (5.2)
SM_C4_OLD = '    c4 = bool(rs.get("all_verified"))\n'
SM_C4_NEW = ('    B = (P or {}).get("B")                                     # S533 (F-863): the verdict is the stage\'s B (absent while stage A is not\n'
             '    c4 = bool(B and B.get("total") and B["verified"] == B["total"])   # verified); rs stays the record the hub and the statement read\n')
SM_WORDS_OLD = ('        dict(key="renames", ok=c4,\n'
                '             en=("all %d renames seen in Marg" % rs["total"] if c4 else "%d of %d renames not yet verified (%d ticked, %d not yet seen in Marg)"\n'
                '                 % (rs["total"] - rs["verified"], rs["total"], rs["done"] + rs["amber"], rs["amber"])),\n'
                '             hi=("Naam badal gaye, Marg mein dikh gaye" if c4 else "Naam badalna baaki (Amir): %d" % (rs["total"] - rs["verified"]))),\n')
SM_WORDS_NEW = ('        dict(key="renames", ok=c4,\n'
                '             en=(("all %d renames seen in Marg" % B["total"]) if c4 else\n'
                '                 ("%d of %d renames not yet verified (%d ticked, %d not yet seen in Marg)"\n'
                '                  % (B["total"] - B["verified"], B["total"], B["ticked"] - B["verified"], len(B["old"]))) if B else\n'
                '                 "renames wait for stage A — the orthotic vouchers\' proof"),\n'
                '             hi=("Naam badal gaye, Marg mein dikh gaye" if c4 else ("Naam badalna baaki (Amir): %d" % (B["total"] - B["verified"])) if B else\n'
                '                 "Naam badalna: orthotic voucher ke baad")),\n')
SM_RET_OLD = "               renames=rs)\n    if for_owner:\n"
SM_RET_NEW = "               renames=rs, renames_wait_stage_a=(B is None))\n    if for_owner:\n"


def build_stockmatch(t):
    t = rep(t, SM_C4_OLD, SM_C4_NEW, "stockmatch: c4")
    t = rep(t, SM_WORDS_OLD, SM_WORDS_NEW, "stockmatch: the renames condition's words")
    t = rep(t, SM_RET_OLD, SM_RET_NEW, "stockmatch: renames_wait_stage_a")
    return t


# ============================================================================================================== DUTY_MAP.json / .md (6)
V10_BILLS = ("SELECT COUNT(*) AS n, MIN(seen_day) AS since FROM (SELECT b.supplier_norm, b.bill_no, b.bill_date, MIN(CASE WHEN e.export_stamp GLOB "
             "'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-*' THEN substr(e.export_stamp,1,4)||'-'||substr(e.export_stamp,5,2)||'-'||substr(e.export_stamp,7,2) "
             "ELSE substr(COALESCE(e.export_stamp, e.received_at),1,10) END) AS seen_day FROM purchase_bill b JOIN purchase_export e ON e.md5 = b.bw_md5 "
             "LEFT JOIN amir_bill_disposition d ON d.supplier_norm = b.supplier_norm AND d.bill_no = b.bill_no AND d.bill_date = b.bill_date "
             "WHERE d.reason IS NULL AND e.type = 'BILLWISE' AND b.bill_date >= '2026-09-01' AND EXISTS (SELECT 1 FROM purchase_bill b2 JOIN "
             "purchase_export e2 ON e2.md5 = b2.bw_md5 WHERE e2.superseded_by IS NULL AND e2.type = 'BILLWISE' AND b2.supplier_norm = b.supplier_norm "
             "AND b2.bill_no = b.bill_no AND b2.bill_date = b.bill_date) GROUP BY b.supplier_norm, b.bill_no, b.bill_date)")
V10_OWN = "SELECT COUNT(*) AS n, MIN(at) AS since FROM amir_bill_disposition WHERE reason = 'self'"
V10_JOBS = "SELECT COUNT(*) AS n, MIN(substr(show_from,1,10)) AS since FROM amir_job WHERE done_at IS NULL AND said_at IS NULL AND show_from IS NOT NULL"
V11_JOBS = ("SELECT COUNT(*) AS n, MIN(substr(show_from,1,10)) AS since FROM amir_job WHERE show_from IS NOT NULL AND done_at IS NULL "
            "AND NOT (said_at IS NOT NULL AND said_at > COALESCE(reopened_at, ''))")
NOTE_ADD = (" S533 (11/12-Oct-2026, D706 / D712; F-839, F-863): Amir's page rebuilt -- amir.bills_answer, amir.own_correction and amir.salt_list carry"
            " amir_day.DUTY_SQL byte-equal (the code runs the same strings): a bill's since-when is its first sight (purchase_bill.first_seen_day),"
            " answers are append-only (amir_bill_answer), the own-correction duty is the open wait records, the salt list is judged by one rule"
            " (the newest VERIFIED list by received_at); amir.arrival_bill_entry is retired and never due (D712: the arrival tap is reception's"
            " record; Amir's card counts the scans, amir.scan_files' marker); amir.marg_jobs counts a reopened job as due again (reopened_at).")


def _duty(j, did):
    du = [x for x in j["duties"] if x.get("id") == did]
    if len(du) != 1:
        raise Stop("DUTY_MAP.json: %s occurs %d times" % (did, len(du)))
    return du[0]


def build_duty_json(raw, duty_sql):
    j = json.loads(raw)
    if j.get("version") != 10:
        raise Stop("DUTY_MAP.json is v%s, not v10" % j.get("version"))
    b = _duty(j, "amir.bills_answer")
    if b["due_sql"] != V10_BILLS:
        raise Stop("amir.bills_answer is not the v10 row this builder was written on")
    b["due_sql"] = duty_sql["amir.bills_answer"]
    b["duty"] += " -- S533: a bill's since-when is its first sight (first_seen_day); answers are append-only (amir_bill_answer)"
    o = _duty(j, "amir.own_correction")
    if o["due_sql"] != V10_OWN:
        raise Stop("amir.own_correction is not the v10 row")
    o["due_sql"] = duty_sql["amir.own_correction"]
    o["duty"] += " -- S533: the open wait records, not the reason column"
    s = _duty(j, "amir.salt_list")
    s["due_sql"] = duty_sql["amir.salt_list"]
    s["duty_hi"] = "Ek export aur: SALT WISE ITEM LIST -- Text ya Excel, dono chalte hain"
    s["duty"] = "Export Marg's SALT WISE ITEM LIST (text or Excel) after salt corrections, so the server can prove them"
    s["owner_line"] = "Salt list not received for {days} days -- {n} salt corrections unproven (Amir; Shavez if it did not come)"
    a = _duty(j, "amir.arrival_bill_entry")
    a["due_sql"] = "SELECT 0 AS n, NULL AS since"
    a["allowed_days"] = 0
    a["owner_line"] = None
    a["coded"] = ("D712 (S533): retired from Amir's card -- the arrival tap is reception's record; an arrival with nothing scanned after "
                  "arrival.bill_grace_days is the owner's line in amir_day.needs_you_lines")
    a["duty"] += " -- RETIRED S533 (D712)"
    f = _duty(j, "amir.scan_files")
    f["duty"] += " -- S533 (D712): the same scans are the card's line \"Scan hua bill Marg mein baaki: N\""
    f["door_marker"] = "Scan hua bill Marg mein baaki"
    mj = _duty(j, "amir.marg_jobs")
    if mj["due_sql"] != V10_JOBS:
        raise Stop("amir.marg_jobs is not the v10 row")
    mj["due_sql"] = V11_JOBS
    mj["duty"] += " -- S533: a job Marg's category list brings back is due again (reopened_at; what he said is kept)"
    j["version"] = 11
    j["kit"] = "S533_AMIR_DAY_PAGE"
    j["_note"] = j["_note"] + NOTE_ADD
    out = json.dumps(j, indent=1, ensure_ascii=False) + "\n"
    for k in ("amir.bills_answer", "amir.own_correction", "amir.salt_list"):
        if json.loads(out)["duties"][[x["id"] for x in json.loads(out)["duties"]].index(k)]["due_sql"] != duty_sql[k]:
            raise Stop("DUTY_MAP.json: %s was not written byte-equal to amir_day.DUTY_SQL" % k)
    return out


MD_EDITS = (
    ("| `amir_step` step 1 not ticked on a visit day; punch in /root/punches.csv |",
     "| no step-1 `amir_step_log` row on a visit day (S533: the row says which button -- punched / no_punch); punch in /root/punches.csv |"),
    ("| `amir_step` step 2 not ticked on a visit day |", "| no step-2 `amir_step_log` row on a visit day |"),
    ("| `purchase_bill` (bill-wise, from 01-Sep, in a live export) with no `amir_bill_disposition` row |",
     "| `purchase_bill` (bill-wise, from 01-Sep, in a live export) with no `amir_bill_answer` row (by `bill_id`, else the triple); since = the bill's first sight, `purchase_bill.first_seen_day` (S533) |"),
    ("| `amir_bill_disposition.reason='self'` |",
     "| an open `amir_self_wait` record (`cleared_at IS NULL`) -- S533: the wait records, not a reason column; a system 'ok' row beside his clears it when a later export shows the paper's amount (or a changed amount with no scan), or the bill leaves the live export |"),
    ("| `purchase_salt_task.done=0` (22 open today); `amir_step` step 6 |",
     "| `purchase_salt_task.done=0`; a step-6 `amir_step_log` row -- S533: step 6 holds the day only while his card holds a line of his Marg work; the salts sheet's door shows only while it has rows |"),
    ("| Export the SALT WISE ITEM LIST (Excel) after salt ticks `[amir.salt_list]` | ticks in `purchase_salt_task` newer than the newest VERIFIED `mi_file` SALT_WISE_ITEM_LIST |",
     "| Export the SALT WISE ITEM LIST (text or Excel) after salt ticks `[amir.salt_list]` | ticks in `purchase_salt_task` newer than the newest VERIFIED `mi_file` SALT_WISE_ITEM_LIST by `received_at` (S533, F-839: one rule, rule B) |"),
    ("\"Ek export aur: SALT WISE ITEM LIST\" | Needs-you, amir_day (a) |",
     "\"Ek export aur: SALT WISE ITEM LIST\" (\"Text ya Excel, dono chalte hain\") | Needs-you, amir_day (a) -- counted in Amir's visits (`amir.salt_owed_days`, S533; the map's {days} is coded and never prints) |"),
    ("| Key the bill for goods tapped as arrived `[amir.arrival_bill_entry]` | `purchase_order_line` arrived, supplied > 0, no billed bill, older than `arrival.bill_grace_days` (S454 part 2: the door's own grace -- the card reads stock_watch's own \"bill entry baaki\" list) | **door added S446**: his card — \"Maal aa gaya, Marg mein bill baaki: N — kholiye\" → board, section 4 | JSON: \"Arrived goods with no Marg bill\" |",
     "| ~~Key the bill for goods tapped as arrived `[amir.arrival_bill_entry]`~~ **RETIRED S533 (D712)** | never due (`SELECT 0`): the arrival tap is reception's record, not Amir's | his card now counts the SCANS instead: \"Scan hua bill Marg mein baaki: N — kholiye\" → step 2 `#scans` (`[amir.scan_files]`) | the owner only, coded in amir_day.needs_you_lines: \"Goods tapped as arrived on dd-mm from <vendor>: no bill scanned, nothing in Marg (N days)\" once `arrival.bill_grace_days` pass with no scan from that supplier |"),
    ("(\"N scan abhi reception ki jaanch mein hain — Marg mein mat daaliye\")",
     "(\"N scan reception ke paas hain — abhi Marg mein nahi daalne\"; S533: the card id is `scans`, and in the live mode `paper` the card is \"Scan ho chuke bill (N)\" -- the same list the card's \"Scan hua bill Marg mein baaki: N\" counts)"),
    ("| `amir_job` rows shown (`show_from`), not said and not done --",
     "| `amir_job` rows shown (`show_from`), not done, and not said since the newest reopen (S533: a reopen stamps `reopened_at`, what he said is kept) --"),
    ("| `amir_day.closed_at` empty for a visit day |", "| the day's newest step-7 `amir_step_log` row is not a 'close' (S533: a reopen is its own row; nothing is erased) |"),
    ("| The salt list when Amir's did not come (S444: \"Shavez kal subah nikalega\") |", "| The salt list when Amir's did not come (S533: \"Nahi nikli to Shavez subah nikaalega\") |"),
)
MD_LOG_AFTER = ("**11-Oct-2026 · kit S524_AMIR_ONE_JUDGMENT (D706, F-846):** `[amir.count_vouchers]`'s due count is the vouchers Amir can see — the orthotic "
                "batches and the batches of a released stage-C lot (a released lot's `since` is its release). No duty added, moved or removed; no other "
                "login's list changes. `DUTY_MAP.json` is v10.\n")
MD_LOG_NEW = ("\n**11-Oct-2026 · kit S533_AMIR_DAY_PAGE (D706, D712; F-839, F-863):** Amir's page rebuilt under the charter. `[amir.bills_answer]`, "
              "`[amir.own_correction]` and `[amir.salt_list]` carry `amir_day.DUTY_SQL` byte-equal (a bill's since-when is its first sight; answers "
              "append-only; the open wait records; one salt rule by `received_at`). `[amir.arrival_bill_entry]` is retired and never due (D712) -- his card "
              "counts the scans (`[amir.scan_files]`), the arrival with nothing scanned is the owner's line only. `[amir.marg_jobs]` counts a reopened "
              "job as due again. The step and close rows read `amir_step_log`. No other login's list changes. `DUTY_MAP.json` is v11.\n")


def build_duty_md(t):
    for a, n in MD_EDITS:
        t = rep(t, a, n, "DUTY_MAP.md row")
    return rep(t, MD_LOG_AFTER, MD_LOG_AFTER + MD_LOG_NEW, "DUTY_MAP.md log line")


def duty_sql_of(amir_day_text):
    """amir_day.DUTY_SQL, read by executing the kit's module text in a scratch namespace with a stub flask (no import from the kit)."""
    import types
    fl = types.ModuleType("flask")

    class _BP(object):
        def __init__(self, *a, **k):
            pass

        def route(self, *a, **k):
            return lambda f: f
    fl.Blueprint, fl.request, fl.redirect, fl.url_for = _BP, None, None, None
    saved = sys.modules.get("flask")
    sys.modules["flask"] = fl
    try:
        ns = {"__name__": "amir_day_s533_build"}
        exec(compile(amir_day_text, "amir_day.py", "exec"), ns)
    finally:
        if saved is not None:
            sys.modules["flask"] = saved
        else:
            sys.modules.pop("flask", None)
    return dict(ns["DUTY_SQL"])


def read_to(kit_dir):
    p = os.path.join(kit_dir, TO_FILE)
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith("TO[") and "]=" in line:
                k, v = line[3:].split("]=", 1)
                out[k] = v.strip()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true")
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    to = read_to(here)
    os.makedirs(a.out, exist_ok=True)
    dirs = dict(finance=a.finance, briefs=a.briefs)
    kit_ad = kit_amir_day()
    duty_sql = duty_sql_of(kit_ad)
    builders = {"amir_day.py": lambda t: kit_ad, "stock_app.py": build_stock_app, "purchase_app.py": build_purchase_app,
                "stockmatch.py": build_stockmatch, "DUTY_MAP.json": lambda t: build_duty_json(t, duty_sql), "DUTY_MAP.md": build_duty_md}
    rc = 0
    for name, fn in builders.items():
        where, frm = PINS[name]
        src = os.path.join(dirs[where], name)
        raw = open(src, "rb").read()
        m0 = md5(raw)
        if m0 != frm:
            if not a.print_to and name.startswith("DUTY_MAP") and to.get(name) == m0:
                with open(os.path.join(a.out, name), "wb") as fh:
                    fh.write(raw)
                print("   %-15s already at its TO pin %s (the clone was pulled) -- taken as it is" % (name, m0))
                continue
            print("!! %s is %s, not its FROM pin %s -- stopped" % (src, m0, frm))
            return 2
        try:
            new = fn(raw.decode("utf-8"))
        except Stop as e:
            print("!! %s: %s" % (name, e))
            return 2
        if name.endswith(".py"):
            try:
                compile(new, name, "exec")
            except SyntaxError as e:
                print("!! %s does not compile after the edits: %s" % (name, e))
                return 2
        nb = new.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(nb)
        m = md5(nb)
        want = to.get(name)
        print("   %-15s %s -> %s  (%+d lines)%s" % (name, frm[:8], m, new.count("\n") - raw.decode("utf-8").count("\n"),
                                                    "" if (a.print_to or want == m) else "   !! not the kit's TO pin %s" % want))
        if not a.print_to and want != m:
            rc = 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
