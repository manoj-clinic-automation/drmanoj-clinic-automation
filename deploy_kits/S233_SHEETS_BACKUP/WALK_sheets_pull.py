#!/usr/bin/env python3
# =============================================================================
#  WALK_sheets_pull.py  ·  Session 233  ·  S233_SHEETS_BACKUP  ·  v1
#
#  A KIT IS PROVEN ONLY BY A LIVE-SHAPE WALK. S208 found two defects behind 65
#  green checks; S209 found a page that killed a console behind four green
#  gates. So this walk does not test functions in isolation: it points the WHOLE
#  job at a fixture tree and a fake Google, runs it end to end the way cron
#  will, and then reads the bytes back off disk.
#
#  It touches NO real path, NO real sheet and NO network. It imports the real
#  sheets_pull.py from beside itself, repoints CONF_PATH at a temporary tree,
#  and installs a fake `gspread` module in sys.modules before the script can
#  import the real one.
#
#  AND IT MAKES THE GUARD FAIL ON PURPOSE. A selftest that cannot fail is not a
#  test (S232, rule 5). Checks 8-13 exist to watch a good backup REFUSE to be
#  overwritten by a bad day, and check 13 reads the surviving rows back to prove
#  the old copy is still the old copy.
#
#  Run it anywhere with any python3:  python WALK_sheets_pull.py
#  It prints one line per check and ends PASS or FAILED with a count.
# =============================================================================
import csv
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append((name, ok, got, want))
    print("%-6s %-58s got=%r" % ("ok" if ok else "FAIL", name, got)
          + ("" if ok else "  want=%r" % (want,)))
    return ok


# --------------------------------------------------------- the fake Google ----
class FakeWorksheet:
    def __init__(self, title, rows):
        self.title = title
        self._rows = rows

    def get_all_values(self):
        return [list(r) for r in self._rows]


class FakeSpreadsheet:
    def __init__(self, title, tabs):
        self.title = title
        self._tabs = tabs

    def worksheets(self):
        return [FakeWorksheet(t, r) for t, r in self._tabs]


class FakeClient:
    """WORLD is the whole of Google as far as the script can tell. A key absent
    from it raises, exactly as gspread does for a sheet that is not shared."""

    def __init__(self, world):
        self.world = world

    def open_by_key(self, key):
        if key not in self.world:
            raise PermissionError("the caller does not have permission")
        title, tabs = self.world[key]
        return FakeSpreadsheet(title, tabs)


WORLD = {}


def install_fake_gspread():
    mod = types.ModuleType("gspread")

    def service_account(filename=None):
        if not filename or not os.path.isfile(filename):
            raise OSError("no key")
        return FakeClient(WORLD)

    mod.service_account = service_account
    sys.modules["gspread"] = mod


# ------------------------------------------------------------- the fixture ----
def rows(n, tag):
    return [["header_a", "header_b"]] + [["%s_%d" % (tag, i), str(i)]
                                         for i in range(1, n)]


def load_script(conf_path):
    spec = importlib.util.spec_from_file_location(
        "sheets_pull_under_test", os.path.join(HERE, "sheets_pull.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.CONF_PATH = conf_path
    return mod


def write_conf(path, sheets, extra=""):
    key = os.path.join(os.path.dirname(path), "fake_sa.json")
    with open(key, "w") as fh:
        fh.write("{}")
    with open(path, "w") as fh:
        fh.write("SA_JSON=%s\n" % key)
        fh.write("SHEETS_DIR=%s\n" % os.path.join(os.path.dirname(path), "sheets"))
        fh.write("SHEETS=%s\n" % sheets)
        if extra:
            fh.write(extra + "\n")


def run_mode(mod, mode):
    """Run one mode and return its exit code, catching the SystemExit the
    script raises on a refusal — cron sees exactly this number."""
    try:
        return mod.main(["sheets_pull.py", mode])
    except SystemExit as ex:
        return ex.code


def read_rows(root, label, tab):
    with open(os.path.join(root, label, tab + ".csv"), newline="",
              encoding="utf-8") as fh:
        return list(csv.reader(fh))


def main():
    tmp = tempfile.mkdtemp(prefix="walk_sheets_")
    try:
        conf = os.path.join(tmp, "clinic_state_backup.conf")
        root = os.path.join(tmp, "sheets")
        install_fake_gspread()

        # --- the world, at its first light -----------------------------------
        WORLD.clear()
        WORLD["ID_TRACKER"] = ("Clinic Callback Tracker", [
            ("Call_Durations", rows(40, "dur")),
            ("WA_Inbox", rows(25, "wa")),
        ])
        WORLD["ID_AUDIT"] = ("Call Audit (Doctor Only)", [
            ("Call_Verdicts", rows(60, "v")),
        ])
        write_conf(conf, "ID_TRACKER:tracker,ID_AUDIT:audit")
        mod = load_script(conf)

        # 1-2 · preflight reads the world and writes nothing
        check("1  preflight exits 0", run_mode(mod, "preflight"), 0)
        check("2  preflight wrote no export directory",
              os.path.isdir(os.path.join(root, "tracker")), False)

        # 3-7 · the first real pull
        check("3  first run exits 0", run_mode(mod, "run"), 0)
        check("4  both books on disk",
              sorted(d for d in os.listdir(root) if not d.startswith(("_", "."))),
              ["audit", "tracker"])
        check("5  every tab is a csv",
              sorted(f for f in os.listdir(os.path.join(root, "tracker"))),
              ["Call_Durations.csv", "WA_Inbox.csv", "_BOOK.json"])
        check("6  rows survived the round trip",
              len(read_rows(root, "tracker", "Call_Durations")), 40)
        check("7  the backup can state its own age",
              "last_success_ist" in json.load(
                  open(os.path.join(root, "_TAKEN_AT.json")))["books"]["tracker"],
              True)

        # 8-10 · A BAD DAY. The tracker is wiped to its header row in Google.
        #        The good copy on disk must survive it.
        WORLD["ID_TRACKER"] = ("Clinic Callback Tracker", [
            ("Call_Durations", rows(1, "dur")),
            ("WA_Inbox", rows(25, "wa")),
        ])
        check("8  a wiped tab makes the run refuse", run_mode(mod, "run"), 42)
        check("9  the previous export is STILL 40 rows",
              len(read_rows(root, "tracker", "Call_Durations")), 40)
        check("10 the innocent book still updated",
              len(read_rows(root, "audit", "Call_Verdicts")), 60)

        # 11-12 · a shrink INSIDE the guard is ordinary and is taken
        WORLD["ID_TRACKER"] = ("Clinic Callback Tracker", [
            ("Call_Durations", rows(36, "dur")),
            ("WA_Inbox", rows(25, "wa")),
        ])
        check("11 a 10% fall is accepted", run_mode(mod, "run"), 0)
        check("12 and it is the new copy on disk",
              len(read_rows(root, "tracker", "Call_Durations")), 36)

        # 13-14 · a book that vanishes from Google keeps its last good export
        del WORLD["ID_AUDIT"]
        check("13 an unreachable book exits 41", run_mode(mod, "run"), 41)
        check("14 its last good export is untouched",
              len(read_rows(root, "audit", "Call_Verdicts")), 60)

        # 15 · a tab that disappears is refused too, not silently dropped
        WORLD["ID_AUDIT"] = ("Call Audit (Doctor Only)", [])
        check("15 a vanished tab is refused", run_mode(mod, "run"), 42)

        # 16-17 · a NEW book, never seen, is taken on its first sight
        WORLD["ID_AUDIT"] = ("Call Audit (Doctor Only)", [
            ("Call_Verdicts", rows(60, "v")),
        ])
        WORLD["ID_PAY"] = ("Payment Register", [("Sheet1", rows(12, "p"))])
        write_conf(conf, "ID_TRACKER:tracker,ID_AUDIT:audit,ID_PAY:payments")
        check("16 a newly added book exits 0", run_mode(mod, "run"), 0)
        check("17 and lands on disk",
              len(read_rows(root, "payments", "Sheet1")), 12)

        # 18 · a book never yet exported that is not shared is named, not fatal
        #      to the others: the others still updated, the run still refuses
        write_conf(conf, "ID_TRACKER:tracker,ID_AUDIT:audit,ID_PAY:payments,"
                         "ID_NOPE:renewals")
        check("18 an unshared new book exits 41", run_mode(mod, "run"), 41)
        check("19 the others were still exported",
              len(read_rows(root, "payments", "Sheet1")), 12)

        # 20 · two books sharing a label would overwrite each other — refused
        write_conf(conf, "ID_TRACKER:tracker,ID_AUDIT:tracker")
        check("20 a duplicate label is refused", run_mode(mod, "run"), 10)

        # 21 · a title that is not a plain name cannot escape the directory
        check("21 a hostile label is made safe",
              mod.safe_label("../../etc/passwd"), "etc_passwd")

        # 22 · list is read-only and works with no network at all
        write_conf(conf, "ID_TRACKER:tracker,ID_AUDIT:audit")
        sys.modules.pop("gspread", None)
        check("22 list needs no Google at all", run_mode(mod, "list"), 0)
        install_fake_gspread()

        # 23 · no staging directory is ever left behind
        check("23 no staging left behind",
              os.path.isdir(os.path.join(root, ".staging")), False)

        # 24 · the export directory is not world-readable
        check("24 export directory is 0700",
              oct(os.stat(root).st_mode & 0o777), "0o700")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [c for c in CHECKS if not c[1]]
    print("\n%d checks, %d failed" % (len(CHECKS), len(bad)))
    if bad:
        print("FAILED")
        return 1
    print("PASS — the walk proved the guard by making it fire, twice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
