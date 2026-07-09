#!/bin/bash
# rotate_callhook.sh - CALLHOOK_SECRET rotation (D162, four steps).
# Guards: D164 (never sed, never line numbers), D168 (candidate path, never overwrite),
# D169 (names+lengths, never values). Keys appear only as key_<md5[:6]> labels.
ENVF=/root/wa/.env
CAND=/root/wa/.env.candidate_s127
STATE=/root/wa/.rotate_s127_state
SVC=call-hook.service
FAILED=0

mask(){ printf 'key_%s' "$(printf '%s' "$1" | md5sum | cut -c1-6)"; }
ok(){   printf '  PASS   %s\n' "$1"; }
bad(){  printf '  FAIL   %s\n' "$1"; FAILED=1; }
line(){ printf -- '-------------------------------------------------------------\n'; }
since2(){ date -d '2 minutes ago' '+%Y-%m-%d %H:%M:%S'; }

startup_line(){
  journalctl -u "$SVC" --no-pager --since "$(since2)" | grep "secret gate" | tail -1
}

check_candidate(){
  FAILED=0
  [ -f "$CAND" ] || { bad "candidate missing"; return; }
  local le lc ce cc dl
  le=$(wc -l < "$ENVF"); lc=$(wc -l < "$CAND")
  [ "$le" = "$lc" ] && ok "line count unchanged ($lc)" || bad "line count $le -> $lc"
  cc=$(grep -c $'\r' "$CAND"); [ "$cc" = "0" ] && ok "no carriage returns" || bad "$cc carriage returns"
  ce=$(grep -c '^CALLHOOK_SECRET=' "$CAND"); [ "$ce" = "1" ] && ok "exactly one CALLHOOK_SECRET line" || bad "$ce CALLHOOK_SECRET lines"
  ce=$(grep -c '^CALLHOOK_SECRET_PREV=' "$CAND"); [ "$ce" = "1" ] && ok "exactly one CALLHOOK_SECRET_PREV line" || bad "$ce PREV lines"
  dl=$(diff "$ENVF" "$CAND" | grep -c '^[<>]')
  [ "$dl" = "2" ] && ok "exactly one line changed" || bad "$dl diff lines (expected 2)"
  if diff <(cut -d= -f1 "$ENVF") <(cut -d= -f1 "$CAND") > /dev/null; then
    ok "variable names identical"; else bad "variable names changed"; fi
}

show_labels(){
  local c p
  c=$(grep '^CALLHOOK_SECRET=' "$1" | cut -d= -f2-)
  p=$(grep '^CALLHOOK_SECRET_PREV=' "$1" | cut -d= -f2-)
  printf '  CALLHOOK_SECRET       len=%-3s  %s\n' "${#c}" "$(mask "$c")"
  if [ -z "$p" ]; then printf '  CALLHOOK_SECRET_PREV  (empty)\n'
  else printf '  CALLHOOK_SECRET_PREV  len=%-3s  %s\n' "${#p}" "$(mask "$p")"; fi
}

cmd_status(){
  line; echo "STATUS"; line
  printf '  service               %s\n' "$(systemctl is-active $SVC)"
  printf '  listening             %s\n' "$(ss -ltn | grep -c ':8098')"
  show_labels "$ENVF"
  local today rawl rej jl warn
  today=$(date +%F)
  rawl=/root/wa/call-hook/call_hook_logs/$today.jsonl
  rej=/root/wa/call-hook/call_hook_rejects/$today.jsonl
  [ -f "$rawl" ] && printf '  accepted today        %s calls\n' "$(wc -l < $rawl)" || printf '  accepted today        (no raw log yet)\n'
  [ -f "$rej" ]  && printf '  REFUSED today         %s  <-- investigate\n' "$(wc -l < $rej)" || printf '  refused today         none\n'
  jl=$(journalctl -u $SVC --no-pager --since "$(date -d '30 minutes ago' '+%Y-%m-%d %H:%M:%S')" | wc -l)
  if [ "$jl" = "0" ]; then
    printf '  last 30 min           journal EMPTY - cannot judge\n'
  else
    warn=$(journalctl -u $SVC --no-pager --since "$(date -d '30 minutes ago' '+%Y-%m-%d %H:%M:%S')" | grep -c "PREVIOUS key")
    printf '  on PREVIOUS key/30min %s\n' "$warn"
  fi
  printf '  startup line          %s\n' "$(startup_line | sed 's/.*\[call_hook_capture\] //')"
  line
}

cmd_stage(){
  command -v openssl >/dev/null || { echo "STOPPED: no openssl"; exit 1; }
  line; echo "STEP 2a - STAGE (nothing installed, nothing restarted)"; line
  local B; B=/root/wa/.env.bak_s127_step2_$(date +%Y%m%d_%H%M%S)
  cp -a "$ENVF" "$B"; chmod 600 "$B"
  if cmp -s "$B" "$ENVF"; then ok "backup verified byte-identical: $B"
  else echo "STOPPED: backup mismatch"; exit 1; fi
  export NEWKEY=$(openssl rand -hex 12)
  [ ${#NEWKEY} = 24 ] && ok "new key generated, 24 chars" || bad "bad key length"
  printf '%s' "$NEWKEY" | grep -qE '^[0-9a-f]{24}$' && ok "hex only - no @, nothing percent-encodes" || bad "bad charset"
  local OLD; OLD=$(grep '^CALLHOOK_SECRET=' "$ENVF" | cut -d= -f2-)
  [ "$NEWKEY" != "$OLD" ] && ok "new key differs from old" || bad "collision"
  awk '/^CALLHOOK_SECRET=/{print "CALLHOOK_SECRET=" ENVIRON["NEWKEY"]; next} {print}' "$ENVF" > "$CAND"
  chmod 600 "$CAND"
  ok "candidate built with awk+ENVIRON (never sed, never line numbers)"
  check_candidate
  echo; echo "  candidate contents (labels only):"; show_labels "$CAND"
  unset NEWKEY
  echo "$B" > "$STATE"; chmod 600 "$STATE"
  line
  if [ "$FAILED" = "0" ]; then
    echo "ALL GUARDS PASSED. .env is UNCHANGED. Nothing restarted."
    echo "Next, when you are ready:   bash /root/wa/rotate_callhook.sh install"
  else
    rm -f "$CAND"; echo "GUARD FAILED. Candidate deleted. .env untouched. Stop and report."
  fi
  line
}

cmd_install(){
  [ -f "$CAND" ] || { echo "STOPPED: no candidate. Run 'stage' first."; exit 1; }
  [ -f "$STATE" ] || { echo "STOPPED: no state file."; exit 1; }
  local B; B=$(cat "$STATE")
  line; echo "STEP 2b - INSTALL + RESTART"; line
  check_candidate
  [ "$FAILED" = "0" ] || { echo "STOPPED: guards failed. .env untouched."; exit 1; }
  if cmp -s "$B" "$ENVF"; then ok "rollback point valid RIGHT NOW: $B"
  else echo "STOPPED: .env changed since stage. Re-run stage."; exit 1; fi
  mv "$CAND" "$ENVF"; chmod 600 "$ENVF"; ok "atomic mv - .env replaced"
  rm -f /root/wa/call-hook/__pycache__/*.pyc 2>/dev/null
  systemctl restart $SVC; sleep 3
  [ "$(systemctl is-active $SVC)" = "active" ] && ok "service active" || bad "service NOT active"
  line; echo "STARTUP LINE (must say ROTATION IN PROGRESS):"
  startup_line; line
  echo "Panel still sends the OLD key. It is accepted via PREV, and each"
  echo "delivery now logs a WARN. That WARN is the instrument, not a fault."
  echo
  echo "Next: update the MyOperator panel to the new key, then run:"
  echo "  bash /root/wa/rotate_callhook.sh status"
  echo "The WARN count must fall to 0 and stay 0 for an hour."
  echo
  echo "Rollback at any time:  bash /root/wa/rotate_callhook.sh rollback"
  line
}

cmd_rollback(){
  [ -f "$STATE" ] || { echo "STOPPED: no state file."; exit 1; }
  local B; B=$(cat "$STATE")
  [ -f "$B" ] || { echo "STOPPED: backup $B missing."; exit 1; }
  cp -a "$B" "$ENVF"; chmod 600 "$ENVF"
  systemctl restart $SVC; sleep 3
  echo "Rolled back from $B. Service: $(systemctl is-active $SVC)"
  startup_line
}

case "$1" in
  status)   cmd_status ;;
  stage)    cmd_stage ;;
  install)  cmd_install ;;
  rollback) cmd_rollback ;;
  *) echo "usage: bash /root/wa/rotate_callhook.sh {status|stage|install|rollback}" ;;
esac
