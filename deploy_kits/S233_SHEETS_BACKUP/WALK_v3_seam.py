#!/usr/bin/env python3
# =============================================================================
#  WALK_v3_seam.py  ·  Session 233  ·  S233_SHEETS_BACKUP  ·  v1
#
#  THE ONE THING NEITHER OTHER WALK CAN SEE.
#
#  WALK_sheets_pull.py proves the exporter. WALK_clinic_state.py proves the
#  bundler — 104 checks — but it REPLACES SRC_DIRS with its own fixture list on
#  line 229, so it never once looks at the row S233 added. That is the F-369
#  shape exactly: a gate proves the rows it has and says nothing about the rows
#  it does not have. S232 paid for that lesson; this file is the receipt.
#
#  So this walk joins the two halves at the seam and proves the seam itself. It
#  runs the REAL sheets_pull against a fake Google, takes the REAL bytes it
#  writes, points the REAL v3 gather() at them, and then reads the collected
#  tree back to prove that a Google Sheet now arrives inside the bundle the
#  same way console.db does.
#
#  No network, no real path, no key, no Drive. Any python3.
# =============================================================================
import csv, importlib.util, json, os, shutil, sys, tempfile, types

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append(ok)
    print("  [%s] %-52s got=%r%s" % ("ok " if ok else "FAIL", name, got,
                                     "" if ok else "  want=%r" % (want,)))


# ------------------------------------------------- the fake Google, again ----
class FW:
    def __init__(self, t, r):
        self.title, self._r = t, r

    def get_all_values(self):
        return [list(x) for x in self._r]


class FS:
    def __init__(self, t, tabs):
        self.title, self._t = t, tabs

    def worksheets(self):
        return [FW(a, b) for a, b in self._t]


class FC:
    def __init__(self, w):
        self.w = w

    def open_by_key(self, k):
        if k not in self.w:
            raise PermissionError("not shared")
        return FS(*self.w[k])


WORLD = {}


def fake_gspread():
    m = types.ModuleType("gspread")
    m.service_account = lambda filename=None: FC(WORLD)
    sys.modules["gspread"] = m


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    tmp = tempfile.mkdtemp(prefix="walk_seam_")
    try:
        fake_gspread()
        conf_path = os.path.join(tmp, "clinic_state_backup.conf")
        sheets_root = os.path.join(tmp, "sheets")
        key = os.path.join(tmp, "fake_sa.json")
        open(key, "w").write("{}")
        rows = lambda n, t: [["a", "b"]] + [["%s%d" % (t, i), str(i)]
                                            for i in range(n - 1)]
        WORLD["ID_T"] = ("Clinic Callback Tracker",
                         [("Call_Durations", rows(30, "d")),
                          ("WA_Inbox", rows(12, "w"))])
        WORLD["ID_A"] = ("Call Audit (Doctor Only)",
                         [("Call_Verdicts", rows(20, "v"))])
        open(conf_path, "w").write(
            "SA_JSON=%s\nSHEETS_DIR=%s\nSHEETS=ID_T:tracker,ID_A:audit\n"
            % (key, sheets_root))

        # --- half one: the real exporter, on the real disk -------------------
        SP = load("sheets_pull.py", "sp_seam")
        SP.CONF_PATH = conf_path
        check("1  the exporter ran", SP.main(["x", "run"]), 0)
        check("2  it wrote real csv bytes",
              os.path.isfile(os.path.join(sheets_root, "tracker",
                                          "Call_Durations.csv")), True)

        # --- half two: the real bundler, pointed at those bytes --------------
        M = load("clinic_state_backup.py", "csb_seam")
        check("3  v3 carries the sheets row in SRC_DIRS",
              "/root/state_backup/sheets" in M.SRC_DIRS, True)
        check("4  and it is the ONLY row v3 added",
              len(M.SRC_DIRS), 3)

        M.SRC_FILES = []
        M.SRC_DIRS = [sheets_root]          # the fixture, in the live row's place
        M.SYSTEMD_DIR = os.path.join(tmp, "nosystemd")
        M.VHOST_DIR = os.path.join(tmp, "novhost")
        M.CRONTAB_CMD = ["printf", "seam\\n"]
        dest = os.path.join(tmp, "collected")
        g = M.gather({}, dest)

        data = os.path.join(dest, "data", "sheets")
        check("5  the sheets tree arrived in the bundle",
              os.path.isdir(data), True)
        check("6  every book came with it",
              sorted(d for d in os.listdir(data) if os.path.isdir(
                  os.path.join(data, d))), ["audit", "tracker"])
        check("7  a tab is a readable csv inside the bundle",
              len(list(csv.reader(open(os.path.join(
                  data, "tracker", "Call_Durations.csv"))))), 30)
        check("8  the book's own shape came too",
              os.path.isfile(os.path.join(data, "tracker", "_BOOK.json")), True)
        check("9  THE BUNDLE CAN STATE THE EXPORT'S AGE",
              "written_at_ist" in json.load(open(os.path.join(
                  data, "_TAKEN_AT.json"))), True)
        check("10 nothing was reported missing",
              [s for s in g.sources_missing], [])
        check("11 no secret pattern tripped", g.secrets_skipped, 0)
        check("12 the inventory counted the sheet files",
              sum(1 for e in g.entries if e[0].startswith("data/sheets/")), 6)

        # --- and the seam must survive a refusal upstream --------------------
        # sheets_pull refuses and exits 42; the export dir is still there, so
        # the bundle must still ship the LAST good copy rather than nothing.
        WORLD["ID_T"] = ("Clinic Callback Tracker",
                         [("Call_Durations", rows(1, "d")),
                          ("WA_Inbox", rows(12, "w"))])
        check("13 the exporter refuses the wipe", SP.main(["x", "run"]), 42)
    except SystemExit as ex:
        check("13 the exporter refuses the wipe", ex.code, 42)
    finally:
        pass
    try:
        dest2 = os.path.join(tmp, "collected2")
        g2 = M.gather({}, dest2)
        check("14 the bundle still carries the last good 30 rows",
              len(list(csv.reader(open(os.path.join(
                  dest2, "data", "sheets", "tracker",
                  "Call_Durations.csv"))))), 30)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = CHECKS.count(False)
    print("\n%d checks, %d failed" % (len(CHECKS), bad))
    print("FAILED" if bad else
          "ALL SEAM CHECKS PASS — a Google Sheet now rides in the bundle,\n"
          "and a wipe upstream cannot take the good copy out of it.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
