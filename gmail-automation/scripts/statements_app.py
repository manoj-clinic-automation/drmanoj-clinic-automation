"""
statements_app.py - CC Statements -> Tally runner for the Clinic Hub
Lives in D:/Scripts alongside process_statements.py. Port 127.0.0.1:5059.
Started by open_clinic_hub.bat like the other tools. Localhost only.
"""
import json, subprocess, sys, datetime
from pathlib import Path
from flask import Flask, request, redirect

HERE      = Path(__file__).parent
SCRIPT    = HERE / "process_statements.py"
STATE     = HERE / "statements_last_run.json"
LOG       = HERE / "process_statements.log"

app = Flask(__name__)

def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"when": "never", "ok": None, "tail": ""}

def save_state(ok, tail):
    STATE.write_text(json.dumps({
        "when": datetime.datetime.now().strftime("%d-%b-%Y %H:%M"),
        "ok": ok, "tail": tail[-4000:]
    }))

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>CC Statements &rarr; Tally</title>
<style>
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0f1b2d;color:#e8eef7;
     max-width:820px;margin:0 auto;padding:34px 18px}}
h1{{font-size:22px}} .dim{{color:#8fa3bd;font-size:13px}}
.badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;margin-left:8px}}
.ok{{background:#14532d;color:#86efac}} .bad{{background:#7f1d1d;color:#fca5a5}}
button{{background:#3b82f6;color:#fff;border:0;border-radius:10px;padding:12px 26px;
       font-size:15px;font-weight:700;cursor:pointer;margin:18px 0}}
button:hover{{background:#2563eb}}
pre{{background:#16263d;border:1px solid #2a3f5c;border-radius:10px;padding:14px;
    font-size:12px;white-space:pre-wrap;max-height:420px;overflow:auto}}
a{{color:#8fb8f6}}
</style></head><body>
<h1>&#128179; CC Statements &rarr; Tally {badge}</h1>
<p class="dim">Runs <code>process_statements.py</code>: decrypt new statement PDFs from
Drive &rarr; <code>Decrypted/</code> &middot; <code>All_Transactions.xlsx</code> &middot;
<code>tally_entries.csv</code>. Safe to run any time &mdash; already-processed files are skipped
or rebuilt deterministically.</p>
<p class="dim">Last run: <b>{when}</b></p>
<form method="post" action="/run"><button>&#9654; Run now</button></form>
<p class="dim">Output of last run:</p>
<pre>{tail}</pre>
<p class="dim"><a href="/">refresh</a> &middot; auto-runs once daily when the hub starts &middot; localhost only</p>
</body></html>"""

@app.route("/")
def home():
    s = load_state()
    badge = ('<span class="badge ok">OK</span>' if s["ok"]
             else '<span class="badge bad">FAILED</span>' if s["ok"] is False else "")
    return PAGE.format(badge=badge, when=s["when"], tail=(s["tail"] or "(no run yet)"))

@app.route("/run", methods=["POST"])
def run():
    try:
        r = subprocess.run([sys.executable, str(SCRIPT)], cwd=HERE,
                           capture_output=True, text=True, timeout=600)
        out = (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
        ok = (r.returncode == 0)
    except Exception as e:
        out, ok = f"Runner error: {e}", False
    stamp = f"===== {datetime.datetime.now()} (hub run) =====\n"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(stamp + out + "\n")
    except Exception:
        pass
    save_state(ok, out)
    return redirect("/")

def _auto_run_if_due():
    """Run once on startup if last run is older than 20h.
    Hub launch is the daily ritual -> this makes processing hands-off
    without Task Scheduler. Button remains for on-demand runs."""
    s = load_state()
    try:
        last = datetime.datetime.strptime(s["when"], "%d-%b-%Y %H:%M")
        due = (datetime.datetime.now() - last).total_seconds() > 20 * 3600
    except Exception:
        due = True   # never ran / unparsable -> run
    if due:
        import threading
        def _bg():
            with app.test_request_context("/run", method="POST"):
                run()
        threading.Timer(5.0, _bg).start()   # small delay; UI is usable immediately

if __name__ == "__main__":
    _auto_run_if_due()
    app.run(host="127.0.0.1", port=5059)
