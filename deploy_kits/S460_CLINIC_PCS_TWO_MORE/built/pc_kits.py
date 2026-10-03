#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pc_kits.py -- kit S450_CLINIC_PCS_TILE (session 290, 02-Oct-2026, D660). PARENT. S451: see the end of this note.

THE OWNER, 02-Oct-2026: "The agent kit you have parked in the Google Drive is a buried location and I think a better
place will be a server and a tile on my portal for all these kits which will be rarely required and the kit should be
self-sufficient to do an install after the Windows reinstall" ... "I log in into my portal in that PC in the browser.
And from there, I, by a very simple click, run and install the agent in that PC." And, on the mock: "looks good to me.
Go ahead with it."

  GET  /finance/pcs                      the page -- one card per clinic PC: is it working, and (when its kit is packed
                                         and rehearsed) one button. THE OWNER ONLY (the medical unit's checker).
  POST /finance/pcs/setup/<pc>           the button: hands the browser ONE small file, ClinicSetup_<PC>.cmd, carrying a
                                         one-time code. Keep, Run -- that is all a person does.
  GET  /finance/api/pc-kit/fetch         the setup file fetches the kit with that code      (part=kit | part=python)
  POST /finance/api/pc-kit/enroll        ...and gives the server that PC's new PUBLIC upload key with it

THE CODE is the only thing that opens the two api paths (they are in finance_app's PUBLIC_PATHS; this module checks the
code itself). It is made when the owner, signed in, presses the button; it names ONE PC; it lasts 60 minutes; only its
SHA-256 is kept on this box. It can fetch that PC's kit -- which holds no secret, no patient and no number -- and enrol
ONE upload key, which can do nothing but post that PC's heartbeat and the two Docterz reports (reception_door.py, S449).

THE KITS are files in the repository clone (deploy_kits/PC_KITS/<pc>/kit.zip, a zip so Windows line endings survive git;
the bundled Python is deploy_kits/PC_KITS/_shared/). A PC whose folder is not there shows no button -- never a button
that cannot work. WHETHER A PC IS WORKING is the same row /finance/health shows, in the same words.

Stdlib + Flask. One small state file beside this module (pc_kit_codes.json, mode 600) and one log (pc_kit_log.txt).

S451 (02-Oct-2026, the same day), two things the first live use found:
  * F-684 -- THE BUTTON REFUSED ITS OWN OWNER. S450 compared the request's Origin header with this server's address and
    refused anything else; on the live box the owner's own press came back 403 (signed in, the medical checker, the
    page itself open). The walk had tested "no Origin" and "another site's Origin" and never the real one behind the
    real front server. Now: a press is refused only when the BROWSER says it came from another site (Sec-Fetch-Site:
    cross-site), or -- from a browser that does not say -- when Origin names another host. Every refusal says WHY on
    the page and in the trail, with what was seen.
  * F-685 -- THE SETUP FILE DID NOT ASK WHICH COMPUTER IT WAS ON. Run on the wrong PC it would have installed the
    reception agent there and replaced the reception PC's key. It now names the computer, stops on the clinic's other
    known PCs, and asks before going on when the name is not the expected one; the enrol door refuses those names too.
"""
import datetime as dt
import fcntl
import hashlib
import html
import json
import os
import re
import secrets
import sys
import time

from flask import Blueprint, Response, jsonify, request, send_file

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.environ.get("PC_KITS_ROOT", "/root/deploy/repo/deploy_kits/PC_KITS")
CODES_FILE = os.environ.get("PC_KIT_CODES", os.path.join(HERE, "pc_kit_codes.json"))
LOG_FILE = os.environ.get("PC_KIT_LOG", os.path.join(HERE, "pc_kit_log.txt"))
SERVER_URL = os.environ.get("PC_KIT_SERVER_URL", "https://followup.dr-manoj.in")
CODE_MINUTES = 60
RATE_PER_MIN = 30

# One entry per clinic PC. `health` is the key of the row /finance/health already computes for that machine.
PCS = [
    {"id": "reception", "label": "Reception PC", "what": "Docterz reports · X-rays · Google Drive watch",
     "health": "reception", "file": "ClinicSetup_Reception.cmd", "key_label": "receptionpc", "names": ["RECEPTIONPC"],
     "person": [("drive", "Google Drive — sign in with the clinic account"),
                ("tailscale", "Tailscale — sign in"),
                ("share", "Your read-only view of this PC — the setup window offers it at the end; "
                          "type its password when it asks")]},
    # S460: these two are set up by the kit's own setup_pc.py (Python), which ONLY PUTS BACK WHAT IS NOT THERE.
    # `setup_label` is the plain-letters name the setup file prints; `pyhome` is where that PC keeps its own Python
    # ("" = it has none of its own: the setup file brings one just to run the installer).
    {"id": "medical", "label": "Medical PC (Sanjeevni)", "what": "Marg exports · Marg backups", "health": "watcher",
     "names": ["MEDICAL"], "file": "ClinicSetup_Medical.cmd", "setup_label": "the Medical PC", "pyhome": "D:\\SendToClinic",
     "person": [("marg", "Marg and its data on D:\\MARGERP — the Marg engineer restores it"),
                ("accounts", "The two Windows accounts; the PC signs itself in at power-on"),
                ("drive", "Google Drive — sign in with the clinic account"),
                ("tailscale", "Tailscale — sign in; D: shared as DDrive for your PC"),
                ("token", "token.txt — Claude gives the one line"),
                ("user", "The staff account: double-click ENABLE_AGENT_THIS_ACCOUNT.bat once")]},
    {"id": "manojz", "label": "Dr Manoj’s PC", "what": "Nightly records · follow-up tracker", "health": "pipeline",
     "names": ["MANOJZ"], "file": "ClinicSetup_DrManojPC.cmd", "setup_label": "Dr Manoj's PC", "pyhome": "",
     "person": [("ssd", "The ClinicBackup SSD plugged in, as drive F: — this PC is restored from it"),
                ("python", "Python from python.org, with “Add python.exe to PATH” ticked"),
                ("git", "Git for Windows; then the repository (one line, on the setup window)"),
                ("drive", "Google Drive — the clinic account, as drive H:"),
                ("tailscale", "Tailscale — sign in"),
                ("claude", "The Claude desktop app, with its folders connected again")]},
    {"id": "shavez", "label": "Shavez’s PC", "planned": True},
    {"id": "lab", "label": "Pathology lab PC", "planned": True},
]
PC_BY_ID = {p["id"]: p for p in PCS}

bp = Blueprint("pc_kits", __name__)
_db = None
_require = None
_health = None
_hits = []


def init(app, db_getter, require_fn, health_fn, url_prefix=""):
    """Mounted at import time from finance_app.py, like every other module here."""
    global _db, _require, _health
    _db, _require, _health = db_getter, require_fn, health_fn
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


def _ist_now():
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)


def _log(pc, event, who=""):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write("%s | %s | %s | %s\n" % (_ist_now().strftime("%Y-%m-%d %H:%M:%S"), pc, event, who))
        os.chmod(LOG_FILE, 0o600)
    except OSError:
        pass


def _log_tail(pc, n=3):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as fh:
            rows = [l.rstrip("\n").split(" | ") for l in fh if (" | %s | " % pc) in l]
        return rows[-n:]
    except OSError:
        return []


# ---------------------------------------------------------------------------------------------------------------------
# the kits on this box
# ---------------------------------------------------------------------------------------------------------------------
def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def kit_info(pc_id):
    """{'kit': path, 'kit_md5', 'python': path, 'python_md5', 'version', 'packed'} or None when the kit is not whole.
    KIT_INFO.txt says what the two files must be; a file that is not what it says makes the kit 'not whole'."""
    try:
        d = os.path.join(KIT_ROOT, pc_id)
        info = {}
        with open(os.path.join(d, "KIT_INFO.txt"), "r", encoding="utf-8") as fh:
            for line in fh:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip()
        kit = os.path.join(d, "kit.zip")
        py = os.path.join(KIT_ROOT, "_shared", info["python_file"])
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", info["python_file"]):
            return None
        if _md5(kit) != info["kit_md5"] or _md5(py) != info["python_md5"]:
            return None
        return {"kit": kit, "kit_md5": info["kit_md5"], "python": py, "python_md5": info["python_md5"],
                "version": info.get("version", ""), "packed": info.get("packed", "")}
    except (OSError, KeyError):
        return None


# ---------------------------------------------------------------------------------------------------------------------
# the one-time codes -- only their SHA-256 is kept
# ---------------------------------------------------------------------------------------------------------------------
class _Codes:
    def __enter__(self):
        self.lock = open(CODES_FILE + ".lock", "a")
        fcntl.flock(self.lock, fcntl.LOCK_EX)
        try:
            with open(CODES_FILE, "r", encoding="utf-8") as fh:
                self.data = json.load(fh)
            if not isinstance(self.data, dict):
                self.data = {}
        except (OSError, ValueError):
            self.data = {}
        now = time.time()
        self.data = {k: v for k, v in self.data.items() if now - float(v.get("at", 0)) < 7 * 86400}
        return self

    def save(self):
        tmp = "%s.%d.tmp" % (CODES_FILE, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh)
        os.chmod(tmp, 0o600)
        os.replace(tmp, CODES_FILE)

    def __exit__(self, *a):
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()
        return False


def _h(code):
    return hashlib.sha256(("pc-kit-code-v1:" + str(code)).encode("utf-8")).hexdigest()


def mint(pc_id, who):
    code = secrets.token_urlsafe(24)
    with _Codes() as c:
        c.data[_h(code)] = {"pc": pc_id, "at": time.time(), "by": who, "fetched": 0, "enrolled": ""}
        c.save()
    return code


def _code_row(codes, code):
    """The live row for a presented code, or None (unknown, or older than CODE_MINUTES)."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,64}", str(code or "")):
        return None
    row = codes.data.get(_h(code))
    if not row or time.time() - float(row.get("at", 0)) > CODE_MINUTES * 60:
        return None
    return row


def _rate_ok():
    now = time.time()
    while _hits and now - _hits[0] > 60:
        _hits.pop(0)
    if len(_hits) >= RATE_PER_MIN:
        return False
    _hits.append(now)
    return True


def _no(message, code=401):
    return jsonify(ok=False, message=message), code


# ---------------------------------------------------------------------------------------------------------------------
# the two doors the setup file uses
# ---------------------------------------------------------------------------------------------------------------------
@bp.route("/finance/api/pc-kit/fetch", methods=["GET"])
def api_pc_kit_fetch():
    if not _rate_ok():
        return _no("too many requests in a minute", 429)
    part = request.args.get("part", "kit")
    if part not in ("kit", "python"):
        return _no("no such part", 404)
    with _Codes() as c:
        row = _code_row(c, request.headers.get("X-Kit-Code"))
        if not row:
            return _no("this code is not known or is more than %d minutes old -- press the button on the "
                       "Clinic PCs page again" % CODE_MINUTES)
        pc = row["pc"]
        info = kit_info(pc)
        if not info:
            return _no("the kit for this PC is not whole on the server", 503)
        row["fetched"] = int(row.get("fetched", 0)) + 1
        c.save()
    _log(pc, "the %s was fetched" % ("kit" if part == "kit" else "Python part"), request.headers.get("X-Real-IP", ""))
    r = send_file(info["kit"] if part == "kit" else info["python"], mimetype="application/zip")
    r.headers["Content-Disposition"] = 'attachment; filename="%s"' % ("kit.zip" if part == "kit" else "pyportable.zip")
    r.headers["Cache-Control"] = "no-store"
    return r


@bp.route("/finance/api/pc-kit/enroll", methods=["POST"])
def api_pc_kit_enroll():
    if not _rate_ok():
        return _no("too many requests in a minute", 429)
    if (request.content_length or 0) > 4096:
        return _no("too big", 413)
    j = request.get_json(silent=True) or {}
    key = str(j.get("pc_key") or "").strip().lower()
    rd = sys.modules.get("reception_door")
    if rd is None:
        return _no("the reception door is not installed on this server", 503)
    if not re.fullmatch(r"[0-9a-f]{64}", key) or rd._edecompress(bytes.fromhex(key)) is None:
        return _no("that is not a public key", 400)
    with _Codes() as c:
        row = _code_row(c, request.headers.get("X-Kit-Code"))
        if not row:
            return _no("this code is not known or is more than %d minutes old -- press the button on the "
                       "Clinic PCs page again" % CODE_MINUTES)
        pc = PC_BY_ID.get(row["pc"]) or {}
        if not pc.get("key_label"):
            return _no("this PC has no upload key to enrol", 400)
        comp = str(j.get("computer") or "").strip().upper()
        if comp and any(comp in (o.get("names") or []) for o in PCS if o["id"] != row["pc"]):
            _log(row["pc"], "enrolment REFUSED: the computer says it is %s, another clinic PC" % re.sub(r"[^A-Z0-9_-]", "", comp)[:20])
            return _no("this computer is %s, one of the clinic's other PCs -- its key is not enrolled as the %s"
                       % (re.sub(r"[^A-Z0-9_-]", "", comp)[:20], pc.get("label")), 400)
        if row.get("enrolled") and row["enrolled"] != key:
            return _no("this code has already enrolled a key")
        label = pc["key_label"]
        try:
            with open(rd.KEYS_FILE, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError:
            lines = ["# reception_keys.txt -- PUBLIC keys that may post to /finance/api/reception/*."]
        keep, had = [], False
        for line in lines:
            parts = line.split(None, 1)
            is_key = bool(parts) and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0])
            if is_key and len(parts) > 1 and parts[1].strip().startswith(label):
                if parts[0].lower() == key:
                    had = True
                    keep.append(line)
                continue                     # this PC's earlier key: its secret went with the old Windows
            keep.append(line)
        if not had:
            keep.append("%s  %s (enrolled from the Clinic PCs page %s IST, button pressed by %s)" % (
                key, label, _ist_now().strftime("%d-%b-%Y %H:%M"), re.sub(r"[^A-Za-z0-9_.-]", "", str(row.get("by")))[:40]))
            tmp = "%s.%d.tmp" % (rd.KEYS_FILE, os.getpid())
            try:
                if os.path.exists(rd.KEYS_FILE):
                    with open(rd.KEYS_FILE, "rb") as a, open(rd.KEYS_FILE + ".prev", "wb") as b:
                        b.write(a.read())
                with open(tmp, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(keep) + "\n")
                os.chmod(tmp, 0o644)
                os.replace(tmp, rd.KEYS_FILE)
            except OSError as ex:
                return _no("could not write the key file: %s" % str(ex)[:120], 500)
        row["enrolled"] = key
        c.save()
    _log(row["pc"], "this PC's upload key was %s" % ("already enrolled" if had else "ENROLLED"),
         str(j.get("computer") or "")[:40])
    return jsonify(ok=True, already=had), 200


# ---------------------------------------------------------------------------------------------------------------------
# the setup file
# ---------------------------------------------------------------------------------------------------------------------
SETUP_RECEPTION = r'''@echo off
setlocal
title Clinic PCs - setting up the Reception PC
set "CODE=__CODE__"
set "SRV=__SRV__"
set "KITMD5=__KITMD5__"
set "PYMD5=__PYMD5__"
set "ROOT=C:\ClinicAgent"
set "W=%TEMP%\ClinicSetup_%RANDOM%%RANDOM%"
echo.
echo   Setting up the Reception PC ...
echo.
REM  F-685: say which computer this is, stop on the clinic's other PCs, ask when the name is not the expected one
set "PCNAME=%COMPUTERNAME%"
for %%N in (__OTHERS__) do if /i "%PCNAME%"=="%%N" set "WHY=this computer is %PCNAME%, one of the clinic's other PCs. This file sets up the Reception PC only" & goto :stop
echo   This computer is %PCNAME%.
if /i "%PCNAME%"=="__EXPECT__" goto :go
echo   It is not named __EXPECT__ - after a Windows reinstall that is normal.
choice /c YN /n /m "   Set up THIS computer as the Reception PC?  Y = yes, N = stop : "
if errorlevel 2 set "WHY=this computer was not confirmed as the Reception PC" & goto :stop
:go
echo.
mkdir "%W%\kit" 2>nul
if not exist "%W%\kit\" set "WHY=could not make a working folder in %TEMP%" & goto :stop
where curl.exe >nul 2>&1
if errorlevel 1 set "WHY=this Windows has no curl.exe - it needs Windows 10 (2018 or later)" & goto :stop
where tar.exe >nul 2>&1
if errorlevel 1 set "WHY=this Windows has no tar.exe - it needs Windows 10 (2018 or later)" & goto :stop

<nul set /p "=   1 of 6  fetching the kit from the clinic server      "
curl.exe -fsS -m 600 -H "X-Kit-Code: %CODE%" -o "%W%\kit.zip" "%SRV%/finance/api/pc-kit/fetch?part=kit"
if errorlevel 1 set "WHY=the server did not hand over the kit. The button's code lasts 60 minutes - press the button on the Clinic PCs page again" & goto :failed
if exist "%ROOT%\pyportable\python.exe" goto :fetched
curl.exe -fsS -m 900 -H "X-Kit-Code: %CODE%" -o "%W%\pyportable.zip" "%SRV%/finance/api/pc-kit/fetch?part=python"
if errorlevel 1 set "WHY=the server did not hand over the Python part" & goto :failed
:fetched
echo ok

<nul set /p "=   2 of 6  checking every file                          "
call :md5of "%W%\kit.zip"
if /i not "%GOT%"=="%KITMD5%" set "WHY=the kit that arrived is not the kit the server holds" & goto :failed
if not exist "%W%\pyportable.zip" goto :unpack
call :md5of "%W%\pyportable.zip"
if /i not "%GOT%"=="%PYMD5%" set "WHY=the Python part that arrived is not the one the server holds" & goto :failed
:unpack
tar.exe -xf "%W%\kit.zip" -C "%W%\kit"
if errorlevel 1 set "WHY=the kit could not be unpacked" & goto :failed
if not exist "%W%\kit\INSTALL_RECEPTION_AGENT.bat" set "WHY=the kit has no installer in it" & goto :failed
if exist "%W%\pyportable.zip" move /y "%W%\pyportable.zip" "%W%\kit\pyportable.zip" >nul
echo ok

<nul set /p "=   3 of 6  its own Python, the agent, the guard         "
REM  the installer keeps its own log beside itself; its console output goes nowhere, so the agent it starts
REM  inherits no open file of ours
call "%W%\kit\INSTALL_RECEPTION_AGENT.bat" >nul 2>&1 <nul
set "ILOG=%W%\kit\install_log.txt"
findstr /c:"DONE. The agent is running" "%ILOG%" >nul 2>&1
if errorlevel 1 set "WHY=the installer did not finish - what it printed is above this line" & set "SHOWLOG=1" & goto :failed
echo ok
copy /y "%W%\kit\share_setup.cmd" "%ROOT%\share_setup.cmd" >nul 2>&1

<nul set /p "=   4 of 6  Chrome's download folder                     "
findstr /r /c:"^Chrome .*: SET to" /c:"^Chrome .*: already set" "%ILOG%" >nul 2>&1
if errorlevel 1 (echo later - Chrome is open or not opened yet; the agent sets it by itself) else (echo ok)

<nul set /p "=   5 of 6  start at every logon                         "
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ClinicAgent.cmd" (echo ok) else (echo MISSING)

<nul set /p "=   6 of 6  first report to the server                   "
"%ROOT%\pyportable\python.exe" "%ROOT%\reception_agent.py" --enroll "%CODE%" > "%W%\enroll_out.txt" 2>&1
if errorlevel 1 goto :noenroll
echo ok
goto :done
:noenroll
echo NOT YET
echo.
type "%W%\enroll_out.txt"
echo   The agent is installed and running; only its direct road to the server is not open.
echo   Press the button on the Clinic PCs page again and run the new file - it is safe to run twice.

:done
echo.
echo   DONE.  The agent is running on this PC and starts by itself at every logon.
echo.
echo   Only a person can do these, once (the Clinic PCs page ticks each as this PC reports it):
echo     - Google Drive: sign in with the clinic account
echo     - Tailscale: sign in
REM  asked of the registry: without administrator rights "net share ReceptionC" fails even when the share is there
reg query "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Shares" /v ReceptionC >nul 2>&1
if not errorlevel 1 goto :cleanup
echo     - your read-only view of this PC, for your phone and your own PC
echo.
choice /c YN /n /m "   Set up that read-only view now? It asks for Yes, then a password twice.  Y = now, N = later : "
if errorlevel 2 goto :cleanup
powershell -NoProfile -Command "Start-Process cmd -Verb RunAs -ArgumentList '/k %ROOT%\share_setup.cmd'"

:cleanup
rd /s /q "%W%" >nul 2>&1
echo.
echo   You can close this window.
echo.
pause >nul
endlocal
exit /b 0

:md5of
set "GOT="
for /f "skip=1 tokens=* delims=" %%H in ('certutil -hashfile "%~1" MD5 2^>nul') do if not defined GOT set "GOT=%%H"
set "GOT=%GOT: =%"
exit /b 0

:failed
echo FAILED
:stop
echo.
if defined SHOWLOG type "%ILOG%"
echo.
echo   STOP: %WHY%.
echo   Nothing else was changed. Tell Claude what this window says.
echo.
pause >nul
endlocal
exit /b 1
'''
SETUP_PYKIT = r'''@echo off
setlocal
title Clinic PCs - setting up __LABEL__
set "CODE=__CODE__"
set "SRV=__SRV__"
set "KITMD5=__KITMD5__"
set "PYMD5=__PYMD5__"
set "PYHOME=__PYHOME__"
set "W=%TEMP%\ClinicSetup_%RANDOM%%RANDOM%"
echo.
echo   Setting up __LABEL__ ...
echo.
REM  F-685: say which computer this is, stop on the clinic's other PCs, ask when the name is not the expected one
set "PCNAME=%COMPUTERNAME%"
for %%N in (__OTHERS__) do if /i "%PCNAME%"=="%%N" set "WHY=this computer is %PCNAME%, one of the clinic's other PCs. This file sets up __LABEL__ only" & goto :stop
echo   This computer is %PCNAME%.
if /i "%PCNAME%"=="__EXPECT__" goto :go
echo   It is not named __EXPECT__ - after a Windows reinstall that is normal.
choice /c YN /n /m "   Set up THIS computer as __LABEL__?  Y = yes, N = stop : "
if errorlevel 2 set "WHY=this computer was not confirmed as __LABEL__" & goto :stop
:go
echo.
mkdir "%W%\kit" 2>nul
if not exist "%W%\kit\" set "WHY=could not make a working folder in %TEMP%" & goto :stop
where curl.exe >nul 2>&1
if errorlevel 1 set "WHY=this Windows has no curl.exe - it needs Windows 10 (2018 or later)" & goto :stop
where tar.exe >nul 2>&1
if errorlevel 1 set "WHY=this Windows has no tar.exe - it needs Windows 10 (2018 or later)" & goto :stop

<nul set /p "=   fetching the kit from the clinic server      "
curl.exe -fsS -m 600 -H "X-Kit-Code: %CODE%" -o "%W%\kit.zip" "%SRV%/finance/api/pc-kit/fetch?part=kit"
if errorlevel 1 set "WHY=the server did not hand over the kit. The button's code lasts 60 minutes - press the button on the Clinic PCs page again" & goto :failed
set "PY="
if defined PYHOME if exist "%PYHOME%\pyportable\python.exe" set "PY=%PYHOME%\pyportable\python.exe"
if defined PY goto :fetched
curl.exe -fsS -m 900 -H "X-Kit-Code: %CODE%" -o "%W%\pyportable.zip" "%SRV%/finance/api/pc-kit/fetch?part=python"
if errorlevel 1 set "WHY=the server did not hand over the Python part" & goto :failed
:fetched
echo ok

<nul set /p "=   checking every file                          "
call :md5of "%W%\kit.zip"
if /i not "%GOT%"=="%KITMD5%" set "WHY=the kit that arrived is not the kit the server holds" & goto :failed
if not exist "%W%\pyportable.zip" goto :unpack
call :md5of "%W%\pyportable.zip"
if /i not "%GOT%"=="%PYMD5%" set "WHY=the Python part that arrived is not the one the server holds" & goto :failed
:unpack
tar.exe -xf "%W%\kit.zip" -C "%W%\kit"
if errorlevel 1 set "WHY=the kit could not be unpacked" & goto :failed
if not exist "%W%\kit\setup_pc.py" set "WHY=the kit has no installer in it" & goto :failed
if defined PY goto :checked
tar.exe -xf "%W%\pyportable.zip" -C "%W%"
if errorlevel 1 set "WHY=the Python part could not be unpacked" & goto :failed
set "PY=%W%\pyportable\python.exe"
if not exist "%PY%" set "WHY=the Python part has no python.exe in it" & goto :failed
:checked
echo ok
echo.

REM  the kit's own installer does the rest and says each step; it only puts back what is not there
"%PY%" -B "%W%\kit\setup_pc.py" --kit "%W%\kit" --pyzip "%W%\pyportable.zip" --log "%W%\install_log.txt"
if errorlevel 1 goto :ended

:ended
rd /s /q "%W%" >nul 2>&1
echo.
echo   You can close this window.
echo.
pause >nul
endlocal
exit /b 0

:md5of
set "GOT="
for /f "skip=1 tokens=* delims=" %%H in ('certutil -hashfile "%~1" MD5 2^>nul') do if not defined GOT set "GOT=%%H"
set "GOT=%GOT: =%"
exit /b 0

:failed
echo FAILED
:stop
echo.
echo   STOP: %WHY%.
echo   Nothing else was changed. Tell Claude what this window says.
echo.
rd /s /q "%W%" >nul 2>&1
pause >nul
endlocal
exit /b 1
'''
SETUPS = {"reception": SETUP_RECEPTION, "medical": SETUP_PYKIT, "manojz": SETUP_PYKIT}


def setup_file(pc_id, code, info):
    pc = PC_BY_ID[pc_id]
    others = " ".join(n for o in PCS if o["id"] != pc_id for n in (o.get("names") or []))
    text = SETUPS[pc_id].replace("__CODE__", code).replace("__SRV__", SERVER_URL) \
        .replace("__KITMD5__", info["kit_md5"]).replace("__PYMD5__", info["python_md5"]) \
        .replace("__OTHERS__", others).replace("__EXPECT__", (pc.get("names") or [""])[0]) \
        .replace("__LABEL__", pc.get("setup_label") or "this PC").replace("__PYHOME__", pc.get("pyhome") or "")
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def _seen(v):
    """A header as it may be written into the trail: short, and nothing but address characters."""
    return re.sub(r"[^A-Za-z0-9.:/_-]", "?", str(v or "-"))[:80]


def _cross_site():
    """None when the press came from this site's own page; else a short reason (F-684).
    The browser's own word (Sec-Fetch-Site) decides when it is there. Origin is only asked of a browser that does not
    send it, and then only its HOST is compared -- with this server's name and with the name the request came to."""
    sfs = (request.headers.get("Sec-Fetch-Site") or "").strip().lower()
    if sfs:
        return None if sfs in ("same-origin", "same-site", "none") else "the browser says %s" % sfs[:20]
    origin = (request.headers.get("Origin") or "").strip()
    if not origin or origin == "null":
        return None
    host = re.sub(r"^[a-z]+://", "", origin.lower()).split("/")[0].split(":")[0]
    mine = {re.sub(r"^[a-z]+://", "", SERVER_URL.lower()).split("/")[0].split(":")[0],
            (request.host or "").split(":")[0].lower(), "127.0.0.1", "localhost"}
    return None if host in mine else "it came from %s" % re.sub(r"[^a-z0-9.-]", "", host)[:60]


@bp.route("/finance/pcs/setup/<pc_id>", methods=["POST"])
def pcs_setup(pc_id):
    u, err = _require("checker")
    if err:
        return _page("Clinic PCs", _denied()), 403
    why = _cross_site()
    if why:
        _log(pc_id if pc_id in PC_BY_ID else "?", "a press was REFUSED: %s [origin=%s host=%s]" % (
            why, _seen(request.headers.get("Origin")), _seen(request.host)), u.get("user") or "")
        return _page("Clinic PCs", "<h1>Clinic PCs</h1><div class=pc><div class=pcn>Not taken</div><p class=what>The "
                     "press did not come from this page (%s). Open the Clinic PCs tile from your portal and press "
                     "the button there.</p></div>" % html.escape(why)), 403
    pc = PC_BY_ID.get(pc_id)
    info = kit_info(pc_id) if pc and pc_id in SETUPS else None
    if not info:
        return _page("Clinic PCs", "<div class=pc><div class=pcn>No kit</div><p class=what>This PC's kit is not on the "
                     "server yet, so there is nothing to set it up with.</p></div>"), 404
    code = mint(pc_id, u.get("user") or "")
    _log(pc_id, "the setup file was made", u.get("user") or "")
    r = Response(setup_file(pc_id, code, info), mimetype="application/octet-stream")
    r.headers["Content-Disposition"] = 'attachment; filename="%s"' % pc["file"]
    r.headers["Cache-Control"] = "no-store"
    return r


# ---------------------------------------------------------------------------------------------------------------------
# the page
# ---------------------------------------------------------------------------------------------------------------------
_CSS = """
:root{--bg:#0f2233;--card:#16324a;--ink:#eaf2fa;--muted:#9fb6cc;--blue:#3b82f6;--line:#274b66}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);
 color:var(--ink);line-height:1.45}
.wrap{max-width:720px;margin:0 auto;padding:18px 16px 44px}
h1{font-size:19px;margin:6px 0 2px;color:#fff}
.sub{font-size:13px;color:var(--muted);margin:0 0 16px}
.pc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:0 0 12px}
.row{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap}
.pcn{font-size:16px;font-weight:650;color:#fff}
.st{font-size:12px;border-radius:999px;padding:3px 10px;font-weight:650;white-space:nowrap}
.st.ok{background:rgba(34,197,94,.16);color:#86efac}.st.bad{background:rgba(239,68,68,.2);color:#fca5a5}
.st.warn{background:rgba(245,158,11,.2);color:#fcd34d}.st.info{background:rgba(91,113,132,.3);color:#c5d3e0}
.what{font-size:12.5px;color:var(--muted);margin:4px 0 0}
.said{font-size:13px;color:#d5e2ee;margin:8px 0 0}
button{appearance:none;margin-top:12px;background:var(--blue);color:#fff;font:650 15px/1 inherit;border-radius:10px;
 padding:12px 16px;border:0;cursor:pointer}
button:focus-visible{outline:2px solid #fff;outline-offset:2px}
.todo{margin:12px 0 0;padding:10px 12px;border-radius:10px;background:#10293d;border:1px dashed var(--line);
 font-size:12.5px;color:#c9d8e6}
.todo b{color:#fff}.todo ul{list-style:none;margin:6px 0 0;padding:0}.todo li{margin:4px 0;padding-left:22px;position:relative}
.todo li:before{content:"\\25CB";position:absolute;left:2px;color:var(--muted)}
.todo li.y:before{content:"\\2713";color:#86efac}
.kit{font-size:11.5px;color:var(--muted);margin:10px 0 0}
.how{font-size:12.5px;color:var(--muted);margin:18px 2px 0}
a{color:#93c5fd}
"""


def _page(title, body, refresh=False):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>%s"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>%s</div></body></html>"
            % ("<meta http-equiv=refresh content=60>" if refresh else "", html.escape(title), _CSS, body))


def _denied():
    return ("<h1>Clinic PCs</h1><div class=pc><div class=pcn>Not permitted</div><p class=what>This page sets up the "
            "clinic's computers. It is open to Dr Manoj's login only.</p></div>")


_WORD = {"ok": "Working", "warn": "Needs a look", "bad": "Not working", "info": "No report"}


def _when(stamp):
    """'2026-10-02 13:05:10' -> '02-Oct 13:05' (the owner's way of writing a date)."""
    try:
        return dt.datetime.strptime(stamp[:16], "%Y-%m-%d %H:%M").strftime("%d-%b %H:%M")
    except ValueError:
        return stamp[:16]


def _ticks(pc_id):
    """{'drive': bool|None, ...} from the PC's own last heartbeat (reception only, today)."""
    rd = sys.modules.get("reception_door")
    rec = rd.read_beat() if (rd is not None and pc_id == "reception") else None
    if not rec:
        return {}
    b, ov = rec["beat"], rec["beat"].get("owner_view") or {}
    return {"drive": bool(b.get("google_drive_running") and b.get("my_drive")),
            "tailscale": ov.get("tailscale_running"), "share": ov.get("share_ready")}


@bp.route("/finance/pcs", methods=["GET"])
def pcs_page():
    u, err = _require("checker")
    if err:
        return _page("Clinic PCs", _denied()), 403
    try:
        rows = {c["key"]: c for c in _health(_db())["checks"]}
    except Exception:                                          # noqa: BLE001 -- the page never dies of a health check
        rows = {}
    out = ["<h1>Clinic PCs</h1><p class=sub>After a Windows reinstall: sign in to the portal on that PC, open this "
           "page, press that PC’s button.</p>"]
    planned = []
    for pc in PCS:
        if pc.get("planned"):
            planned.append(pc)
            continue
        row = rows.get(pc["health"])
        state = row["state"] if row else "info"
        said = row["detail"] if row else "its row on the health page could not be read"
        card = ["<div class=pc><div class=row><div class=pcn>%s</div><span class='st %s'>%s</span></div>"
                "<p class=what>%s</p><p class=said>%s</p>"
                % (html.escape(pc["label"]), state, _WORD.get(state, state), html.escape(pc["what"]), html.escape(said))]
        info = kit_info(pc["id"]) if pc["id"] in SETUPS else None
        if info:
            card.append("<form method=post action='/finance/pcs/setup/%s'><button type=submit>Set up this PC as the %s"
                        "</button></form>" % (pc["id"], html.escape(pc["label"])))
            if pc.get("person"):
                t = _ticks(pc["id"])
                card.append("<div class=todo><b>Only a person can do these, once, after a reinstall:</b><ul>%s</ul>"
                            "A tick is what this PC itself last reported.</div>" % "".join(
                                "<li%s>%s</li>" % (" class=y" if t.get(k) else "", html.escape(words))
                                for k, words in pc["person"]))
            last = _log_tail(pc["id"])
            card.append("<p class=kit>Kit on the server: %s, packed %s.%s</p>" % (
                html.escape(info["version"]), html.escape(info["packed"]),
                (" Last: " + html.escape(" · ".join("%s %s" % (_when(r[0]), r[2]) for r in last if len(r) > 2))) if last else ""))
        else:
            card.append("<p class=kit>Its setup kit is not on the server yet — it is being packed and rehearsed. "
                        "Until then this card only shows whether the PC is working.</p>")
        card.append("</div>")
        out.append("".join(card))
    if planned:
        out.append("<div class=pc>%s</div>" % "".join(
            "<div class=row%s><div class=pcn>%s</div><span class='st info'>Not set up yet</span></div>"
            % (" style='margin-top:8px'" if i else "", html.escape(p["label"])) for i, p in enumerate(planned)))
    out.append("<p class=how>The button downloads one small file. Chrome asks <b>Keep</b>; you click the file and "
               "Windows asks <b>Run</b>. It then fetches the kit from this server, installs it and reports back — "
               "nothing is typed. The file works for %d minutes and for that one PC. "
               "<a href='/finance/health'>The full health page</a></p>" % CODE_MINUTES)
    return _page("Clinic PCs", "".join(out), refresh=True)
