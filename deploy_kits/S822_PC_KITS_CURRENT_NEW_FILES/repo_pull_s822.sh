#!/bin/bash
# repo_pull_s822.sh -- kit S822_PC_KITS_CURRENT_NEW_FILES (S456, the parent, 14-Nov-2026). D972, F-1386.
# Pulls the repository clone the Clinic PCs page serves its kits from, fast-forward only, so a kit repacked on Dr Manoj's PC
# and published by him reaches https://followup.dr-manoj.in/finance/pcs within half an hour -- no server line.
# Cron: 7,37 * * * *   # S822_REPO_PULL.   Nothing but `git pull --ff-only` in /root/deploy/repo; nothing is installed.
# Quiet unless the clone moved or the pull failed; one line per event in /root/deploy/repo_pull_s822.log.
set -u
# its own variable names (S822_*), so nothing an installer exports can reach them
REPO="${S822_REPO:-/root/deploy/repo}"
LOG="${S822_LOG:-/root/deploy/repo_pull_s822.log}"
LOCK="${S822_LOCK:-/root/deploy/.repo_pull_s822.lock}"
INSTALL_LOCK="${S822_INSTALL_LOCK:-/root/deploy/.claude_code_build.lock}"   # held by a running kit installer: skip this round
export GIT_TERMINAL_PROMPT=0 LC_ALL=C
exec 9>"$LOCK" || exit 0
flock -n 9 || exit 0
[ -d "$INSTALL_LOCK" ] && exit 0
[ -d "$REPO/.git" ] || { echo "$(date '+%F %T') FAILED: $REPO is not a git clone" >> "$LOG"; exit 0; }
cd "$REPO" || exit 0
before=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "?")
out=$(timeout 150 git pull --ff-only -q 2>&1); rc=$?
after=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "?")
if [ "$rc" -ne 0 ]; then
  echo "$(date '+%F %T') FAILED rc=$rc: $(printf '%s' "$out" | tail -1 | cut -c1-160)" >> "$LOG"
elif [ "$before" != "$after" ]; then
  echo "$(date '+%F %T') pulled $before -> $after" >> "$LOG"
fi
# keep the log small: the last 400 lines
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 600 ]; then tail -n 400 "$LOG" > "$LOG.tmp" && mv -f "$LOG.tmp" "$LOG"; fi
exit 0
