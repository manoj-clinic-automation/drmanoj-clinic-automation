#!/usr/bin/env bash
# walk_installer.sh -- the installer run offline against a fake VPS: green, re-run,
# red after install (health fails -> files + settings restored), wrong live file.
set -u
K="$(cd "$(dirname "$0")/.." && pwd)"
OLD_SP="$1"; OLD_SR="$2"          # the live v1.8 / v0.13 files
T=$(mktemp -d); mkdir -p "$T/bin"
cat > "$T/bin/systemctl" <<'S'
#!/bin/bash
case "$1" in show) echo "ExecStart={ path=/x/python3 ; argv[]=python3 staff_register.py }";; *) exit 0;; esac
S
cat > "$T/bin/curl" <<'S'
#!/bin/bash
cat "$HEALTH_FILE" 2>/dev/null || echo 200
S
chmod +x "$T/bin/"*
export PATH="$T/bin:$PATH" PY=python3 S238_WALK=1 HEALTH_FILE="$T/health"
fresh(){ rm -rf "$T/sr"; mkdir -p "$T/sr"; cp "$OLD_SP" "$T/sr/salary_policy.py"; cp "$OLD_SR" "$T/sr/staff_register.py"
         printf '{\n  "improve_pct": 30\n}\n' > "$T/sr/salary_policy_settings.json"; }
pass=0; fail=0
chk(){ if eval "$2"; then pass=$((pass+1)); echo "  ok   $1"; else fail=$((fail+1)); echo "  FAIL $1"; fi; }
echo "== 1 green"; fresh; echo 200 > "$T/health"
SR_DIR="$T/sr" bash "$K/install_sheet2_review.sh" > "$T/o1" 2>&1; rc=$?
chk "exit 0" "[ $rc = 0 ]"; chk "GREEN printed" "grep -q GREEN $T/o1"
chk "new salary_policy in place" "[ \$(md5sum < $T/sr/salary_policy.py | cut -c1-32) = \$(md5sum < $K/salary_policy.py | cut -c1-32) ]"
chk "new staff_register in place" "[ \$(md5sum < $T/sr/staff_register.py | cut -c1-32) = \$(md5sum < $K/staff_register.py | cut -c1-32) ]"
chk "improve_pct is 20" "grep -q '\"improve_pct\": 20' $T/sr/salary_policy_settings.json"
chk "audit line written" "grep -q 'owner ruling 10-Sep-2026' $T/sr/salary_policy_settings_audit.jsonl"
chk "backups exist" "ls $T/sr/*.bak_S238_SHEET2_REVIEW_* >/dev/null 2>&1"
echo "== 2 re-run"; SR_DIR="$T/sr" bash "$K/install_sheet2_review.sh" > "$T/o2" 2>&1; rc=$?
chk "re-run exit 0" "[ $rc = 0 ]"; chk "re-run says already" "grep -q 'already installed' $T/o2 && grep -q 'already 20' $T/o2"
echo "== 3 red after install"; fresh; echo 500 > "$T/health"
SR_DIR="$T/sr" bash "$K/install_sheet2_review.sh" > "$T/o3" 2>&1; rc=$?
chk "red exit 1" "[ $rc = 1 ]"; chk "RED printed" "grep -q 'RED' $T/o3"
chk "salary_policy restored" "cmp -s $OLD_SP $T/sr/salary_policy.py"
chk "staff_register restored" "cmp -s $OLD_SR $T/sr/staff_register.py"
chk "settings restored to 30" "grep -q '\"improve_pct\": 30' $T/sr/salary_policy_settings.json"
chk "no audit left behind" "[ ! -f $T/sr/salary_policy_settings_audit.jsonl ]"
echo "== 4 wrong live file"; fresh; echo 200 > "$T/health"; echo "# changed" >> "$T/sr/salary_policy.py"; cp "$T/sr/salary_policy.py" "$T/before"
SR_DIR="$T/sr" bash "$K/install_sheet2_review.sh" > "$T/o4" 2>&1; rc=$?
chk "refused exit 1" "[ $rc = 1 ]"; chk "CURRENCY GATE printed" "grep -q 'CURRENCY GATE' $T/o4"
chk "nothing touched" "cmp -s $T/before $T/sr/salary_policy.py && cmp -s $OLD_SR $T/sr/staff_register.py && grep -q 30 $T/sr/salary_policy_settings.json"
echo "== 5 tampered kit"; cp -r "$K" "$T/k2"; echo x >> "$T/k2/salary_policy.py"; fresh
SR_DIR="$T/sr" bash "$T/k2/install_sheet2_review.sh" > "$T/o5" 2>&1; rc=$?
chk "tampered refused" "[ $rc = 1 ] && grep -q 'SUMS.md5 gate failed' $T/o5 && cmp -s $OLD_SP $T/sr/salary_policy.py"
echo; sed -n 1,40p "$T/o1" | sed 's/^/  | /'
echo "installer walk: $pass passed, $fail failed"
rm -rf "$T"; [ $fail = 0 ]
