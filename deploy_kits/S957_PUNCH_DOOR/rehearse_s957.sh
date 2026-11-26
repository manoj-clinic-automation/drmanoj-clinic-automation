#!/bin/bash
# rehearse_s957.sh -- S957_PUNCH_DOOR: the installer on a MADE-UP root (stub systemctl / ack / journal / the clock's --dry / the
#   presence read), every path. Everything in [3/6] runs for real: make, walk, control, S953's walk, THE EVIDENCE on a made-up source
#   log and punch file (a made-up mark), THE REPLAY through the TO listener.
#   bash rehearse_s957.sh <kit dir> <dir holding the FROM attlistener_v2.py, att_source_summary.py, callback_clock.py,
#        freshness_legs.json and the live calls_console.py, calls_staff.py, ring_outcome.py, ring_common.py, freshness.py> <python with flask>
set -u
KD="$(cd "$1" && pwd)"; FROMD="$(cd "$2" && pwd)"; PY="$3"
W="$(mktemp -d "${TMPDIR:-/tmp}/s957_reh.XXXXXX")"; PASS=0; FAIL=0
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
to() { awk -v f="to/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
R="$W/r"
fresh() { rm -rf "$R"; mkdir -p "$R/portal" "$R/finance" "$R/deploy/_off" "$W/bin"
  \cp "$FROMD/attlistener_v2.py" "$FROMD/att_source_summary.py" "$R/"
  \cp "$FROMD/callback_clock.py" "$FROMD/calls_console.py" "$FROMD/calls_staff.py" "$FROMD/ring_outcome.py" "$FROMD/ring_common.py" "$R/portal/"
  \cp "$FROMD/freshness_legs.json" "$FROMD/freshness.py" "$R/finance/"
  chmod 644 "$R/attlistener_v2.py" "$R/portal/callback_clock.py"
  "$PY" - "$R" "${1:-good}" <<'EOF'
import datetime as dt, json, os, sys
r, how = sys.argv[1], sys.argv[2]
now = dt.datetime.now().replace(microsecond=0)
src, pun = [], ["user_id,datetime,io_mode,verify_mode,received_at,machine_time"]
for back in range(9, 0, -1):
    for uid, hh in ((1, 9), (2, 10), (3, 9), (1, 18), (2, 19)):
        t = (now - dt.timedelta(days=back)).replace(hour=hh, minute=uid, second=0)
        mark = "WALKMARK7" if not (how == "nomark" and back == 2 and uid == 2) else "OTHERMARK"
        src.append({"t": t.strftime("%Y-%m-%d %H:%M:%S"), "ip": "100.64.%d.9" % back, "method": "POST", "path": "/",
                    "request_code": "realtime_glog", "ack": "OK", "punch": True, "user_id": str(uid),
                    "datetime": t.strftime("%Y-%m-%d %H:%M:%S"),
                    "headers": {"dev_id": mark, "request_code": "realtime_glog", "Accept-Language": "en-us", "User-Agent": "Mozilla/4.0",
                                "Connection": "close", "Content-Type": "application/octet-stream"}})
        pun.append("%d,%s,0,1,%s," % (uid, t.strftime("%Y-%m-%d %H:%M:%S"), t.strftime("%Y-%m-%d %H:%M:%S")))
if how == "gap":
    pun.append("5,%s,0,1,%s," % ((now - dt.timedelta(days=1)).strftime("%Y-%m-%d 11:11:11"), (now - dt.timedelta(days=1)).strftime("%Y-%m-%d 11:11:11")))
src.insert(3, {"t": src[3]["t"], "ip": "203.0.113.5", "punch": False, "ack": "ERROR_NO_CMD", "request_code": "", "headers": {}})
open(os.path.join(r, "attlistener_sources.jsonl"), "w").write("".join(json.dumps(x) + "\n" for x in src))
open(os.path.join(r, "punches.csv"), "w").write("\n".join(pun) + "\n")
open(os.path.join(r, "staff_master.csv"), "w").write("user_id,name,wd_start,wd_end,sun_start,sun_end,active\n1,Ana X,09:00,18:00,,,Y\n")
EOF
  rm -rf "$W/kit"; \cp -rp "$KD" "$W/kit"
  cat > "$W/bin/sysctl" <<EOF
#!/bin/bash
echo "\$@" >> "$W/sysctl.log"
if [ "\$1" = restart ]; then m=open; [ -f "$R/punch_door.json" ] && m=\$(grep -o '"mode": "[a-z]*"' "$R/punch_door.json" | cut -d'"' -f4); echo "{\"mode\": \"\$m\"}" > "$R/punch_door.state.json"; fi
[ "\$1" = is-active ] && echo active; true
EOF
  printf '#!/bin/bash\n[ -e %s/ACKBAD ] && echo none || echo ERROR_NO_CMD\n' "$R" > "$W/bin/ack"
  printf '#!/bin/bash\n[ -e %s/JOURNAL_BAD ] && echo "Traceback (most recent call last):"; true\n' "$R" > "$W/bin/jr"
  printf '#!/bin/bash\n[ -e %s/DRYBAD ] && echo "ImportError: boom" || echo "DRY 2026-11-26 10:00: callers not spoken to 0; lists ok; nothing sent, nothing written"\n' "$R" > "$W/bin/cdry"
  printf '#!/bin/bash\necho "PRESENCE S957 1.0 2026-11-26 10:00: ok True, basis punch (punches), people 1, punched in 1, punched out 0, on duty 1 (by roster 0)"\n' > "$W/bin/pres"
  chmod +x "$W/bin/"*; : > "$W/sysctl.log"; }
run() { ROOT="$R" PD="$R/portal" FD="$R/finance" APY="$PY" SPY="$PY" LOCK="$R/deploy/lock" OFFSW="$R/deploy/_off/DOCTOR_AUTO_OFF" SYSTEMCTL="$W/bin/sysctl" \
  ACK_CMD="$W/bin/ack" JOURNAL_CMD="$W/bin/jr" CLOCKDRY_CMD="$W/bin/cdry" PRES_CMD="$W/bin/pres" NAP=0 bash "$W/kit/install_S957_PUNCH_DOOR.sh" "$@" 2>&1; }
chk() { if eval "$2"; then PASS=$((PASS+1)); echo "  ok   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "$OUT" | tail -8 | sed 's/^/        /'; fi; }
isfrom() { [ "$(m5 "$R/attlistener_v2.py")" = 588ea08e744d11fc9fbbee7e41d7515c ] && [ "$(m5 "$R/att_source_summary.py")" = 2aa34b8862c178c236bc38b3dba73847 ] \
  && [ "$(m5 "$R/portal/callback_clock.py")" = 5fbcd29cb50a97ce46854d97addba9cd ] && [ "$(m5 "$R/finance/freshness_legs.json")" = f5c68b240f179a8aaee7d6e730dfcd07 ] \
  && [ ! -e "$R/portal/presence.py" ] && [ ! -e "$R/punch_door.json" ]; }
isto() { [ "$(m5 "$R/attlistener_v2.py")" = "$(to attlistener_v2.py)" ] && [ "$(m5 "$R/att_source_summary.py")" = "$(to att_source_summary.py)" ] \
  && [ "$(m5 "$R/portal/callback_clock.py")" = "$(to callback_clock.py)" ] && [ "$(m5 "$R/finance/freshness_legs.json")" = "$(to freshness_legs.json)" ] \
  && [ "$(m5 "$R/portal/presence.py")" = "$(to presence.py)" ]; }
door() { grep -o '"mode": "[a-z]*"' "$R/punch_door.json" 2>/dev/null | cut -d'"' -f4; }
clean() { [ ! -e "$R/deploy/lock" ] && [ ! -e "$R/deploy/_off/DOCTOR_AUTO_OFF" ] && [ -z "$(ls -A "$R" "$R/portal" "$R/finance" | grep '\.s957')" ] \
  && [ -z "$(ls /tmp | grep '^s957_inst\.')" ] && ! grep -q WALKMARK7 <<< "$OUT"; }
fresh; OUT="$(DRY=1 run)"; chk "DRY: [1]-[3] green, the door would be enforce, nothing changed, the mark never printed" 'echo "$OUT" | grep -q "DRY ok.*enforce" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
chk "DRY: the replay admitted every punch of the last 7 days and refused both spoofs" 'echo "$OUT" | grep -qE "REPLAY punches (3[0-9]) distinct \1 stored \1 refused 0 spoof_no_mark refused spoof_wrong refused"'
OUT="$(run)"; chk "install: INSTALLED, every TO, presence, the door file 0600 enforce, the listener restarted" 'echo "$OUT" | grep -q "INSTALLED" && echo "$OUT" | grep -q "DOOR IS SHUT" && isto && [ "$(door)" = enforce ] && [ "$(stat -c %a "$R/punch_door.json")" = 600 ] && grep -q "restart attlistener" "$W/sysctl.log" && clean'
chk "backups 0600 read as FROM; modes kept" '[ "$(m5 "$R/attlistener_v2.py.bak_S957_588ea08e")" = 588ea08e744d11fc9fbbee7e41d7515c ] && [ "$(m5 "$R/portal/callback_clock.py.bak_S957_5fbcd29c")" = 5fbcd29cb50a97ce46854d97addba9cd ] && [ "$(stat -c %a "$R/finance/freshness_legs.json.bak_S957_f5c68b24")" = 600 ] && [ "$(stat -c %a "$R/attlistener_v2.py")" = 644 ] && [ "$(stat -c %a "$R/portal/presence.py")" = 644 ]'
OUT="$(run)"; chk "again: ALREADY (door enforce)" 'echo "$OUT" | grep -q "ALREADY.*enforce" && isto'
OUT="$(run --undo)"; chk "--undo: every file back, presence and the door file removed, restarted" 'echo "$OUT" | grep -q "UNDONE" && isfrom && clean'
OUT="$(run --undo)"; chk "--undo twice: not installed" 'echo "$OUT" | grep -q "not installed" && isfrom'
OUT="$(run)"; chk "re-install after undo" 'echo "$OUT" | grep -q "INSTALLED" && isto && [ "$(door)" = enforce ] && clean'
echo x >> "$R/portal/callback_clock.py"; OUT="$(run --undo)"; chk "--undo refuses a later change" 'echo "$OUT" | grep -q "not S957" && clean'
fresh; OUT="$(FORCE_RED_AT=4 run)"; chk "forced red at [4/6]: all put back, the new files removed" 'echo "$OUT" | grep -q "RED" && isfrom && clean'
fresh; OUT="$(FORCE_RED_AT=5 run)"; chk "forced red at [5/6]: all put back" 'echo "$OUT" | grep -q "RED" && isfrom && clean'
fresh; OUT="$(FORCE_KILL_AT=4 run)"; chk "killed mid-[4/6]: all put back" 'echo "$OUT" | grep -q "ended before its proof" && isfrom && clean'
fresh; touch "$R/JOURNAL_BAD"; OUT="$(run)"; chk "the listener journal shows a Traceback: put back" 'echo "$OUT" | grep -q "Traceback" && isfrom && clean'
fresh; touch "$R/ACKBAD"; OUT="$(run)"; chk "the listener does not answer: put back" 'echo "$OUT" | grep -q "does not answer" && isfrom && clean'
fresh; touch "$R/DRYBAD"; OUT="$(run)"; chk "the installed clock --dry fails: put back" 'echo "$OUT" | grep -q "clock.s --dry did not run" && isfrom && clean'
fresh gap; OUT="$(run)"; chk "the evidence INCOMPLETE (a row with no source line): installed with the door WATCHING" 'echo "$OUT" | grep -q "DECIDE watch" && echo "$OUT" | grep -q "DOOR IS WATCHING" && isto && [ "$(door)" = watch ] && clean'
fresh nomark; OUT="$(run)"; chk "no single mark: installed with the door OPEN, no door file" 'echo "$OUT" | grep -q "DECIDE none" && echo "$OUT" | grep -q "DOOR IS OPEN" && isto && [ ! -e "$R/punch_door.json" ] && clean'
OUT="$(run --undo)"; chk "--undo of an open-door install" 'echo "$OUT" | grep -q "UNDONE" && isfrom'
fresh; mkdir "$R/deploy/lock"; OUT="$(run)"; chk "the build lock held: stops at [4/6], nothing changed" 'echo "$OUT" | grep -q "another build holds" && isfrom'
fresh; echo "# drift" >> "$R/attlistener_v2.py"; OUT="$(run)"; chk "a drifted listener: stops at [2/6]" 'echo "$OUT" | grep -q "\[2/6\].*changed after" && clean'
fresh; echo "x" > "$R/portal/presence.py"; OUT="$(run)"; chk "a presence.py already there: stops at [2/6]" 'echo "$OUT" | grep -q "\[2/6\].*presence.py already exists" && clean'
fresh; echo "{}" > "$R/punch_door.json"; OUT="$(run)"; chk "a door file already there: stops at [2/6]" 'echo "$OUT" | grep -q "\[2/6\].*punch_door.json already exists" && clean'
fresh; rm "$R/attlistener_sources.jsonl"; OUT="$(run)"; chk "no source log: stops at [2/6]" 'echo "$OUT" | grep -q "\[2/6\].*missing" && isfrom'
fresh; echo "# x" >> "$W/kit/to/presence.py"; OUT="$(run)"; chk "a corrupt kit: stops at [1/6]" 'echo "$OUT" | grep -q "\[1/6\]" && isfrom'
rm -rf "$W"
echo "REHEARSAL: $PASS/$((PASS+FAIL)) $([ $FAIL = 0 ] && echo PASS || echo FAIL)"
[ $FAIL = 0 ]
