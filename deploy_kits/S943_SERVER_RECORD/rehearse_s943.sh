#!/bin/bash
# rehearse_s943.sh -- kit S943 on a MADE-UP root: stub systemctl, stub health (HEALTH_CMD), stub crontab (a file), the VM's python3
# as the venv; the FROM owner_console.py / freshness_legs.json as the live files. No live file, no network.
# Scenes: A dry . B install . C again . D undo . E forced red at [4/5] -> everything back . F healthz not 200 -> nothing .
#         G tampered kit . H wrong live pin -> nothing . I lock held -> nothing
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; R="$(mktemp -d /tmp/s943_reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OCFROM="${OCFROM:?owner_console.py cf7f8b09}"; LGFROM="${LGFROM:?freshness_legs.json f2ade687}"
n=0; f=0; ok() { n=$((n+1)); if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; f=$((f+1)); fi; }
m8() { md5sum "$1" | cut -c1-8; }
to8() { awk -v f="finance/$1" '$2==f{print substr($1,1,8)}' "$KDIR/TO_PINS.md5"; }
mk() { rm -rf "$R/root"; mkdir -p "$R/root/finance/logs" "$R/root/deploy"; cp "$OCFROM" "$R/root/finance/owner_console.py"; cp "$LGFROM" "$R/root/finance/freshness_legs.json"
  echo "5 1 * * * /bin/true # an existing line" > "$R/crontab.txt"; printf '#!/bin/bash\nif [ "$1" = -l ]; then cat "%s"; else cat > "%s"; fi\n' "$R/crontab.txt" "$R/crontab.txt" > "$R/crontab"
  printf '#!/bin/bash\necho "$*" >> "%s"; exit 0\n' "$R/systemctl.log" > "$R/systemctl"
  printf '#!/bin/bash\n[ -f "%s" ] && cat "%s" || echo 200\n' "$R/health_code" "$R/health_code" > "$R/health"
  chmod +x "$R/crontab" "$R/systemctl" "$R/health"; : > "$R/systemctl.log"; rm -f "$R/health_code"; }
run() { ROOT="$R/root" LOCK="$R/root/deploy/.lock" SYSTEMCTL="$R/systemctl" HEALTH_CMD="$R/health" CRONTAB="$R/crontab" NAP=0 APY="$(command -v python3)" SR_DIR="$R/root/finance/server_record" bash "$KDIR/install_S943_SERVER_RECORD.sh" "$@" 2>&1; }
OC="$R/root/finance/owner_console.py"; LG="$R/root/finance/freshness_legs.json"; SR="$R/root/finance/server_record.py"
echo "A  dry"; mk; out="$(DRY=1 run)"; echo "$out" | tail -2 | sed 's/^/     /'
ok "A dry: nothing changed" 'echo "$out" | grep -q "nothing live changed" && [ "$(m8 "$OC")" = cf7f8b09 ] && [ ! -f "$SR" ] && ! grep -q S943 "$R/crontab.txt"'
echo "B  install"; out="$(run)"; echo "$out" | tail -4 | sed 's/^/     /'
ok "B DONE" 'echo "$out" | grep -q "S943_SERVER_RECORD: DONE"'
ok "B three files at TO, baks beside" '[ "$(m8 "$OC")" = "$(to8 owner_console.py)" ] && [ "$(m8 "$LG")" = "$(to8 freshness_legs.json)" ] && [ "$(m8 "$SR")" = "$(to8 server_record.py)" ] && [ "$(m8 "$OC.bak_S943_cf7f8b09")" = cf7f8b09 ] && [ "$(m8 "$LG.bak_S943_f2ade687")" = f2ade687 ]'
ok "B first record written, cron line in (the old line kept), restarted once" '[ -f "$R/root/finance/server_record/LATEST.json" ] && grep -q S943_SERVER_RECORD "$R/crontab.txt" && grep -q "an existing line" "$R/crontab.txt" && [ "$(grep -c restart "$R/systemctl.log")" = 1 ] && [ ! -d "$R/root/deploy/.lock" ]'
echo "C  again"; out="$(run)"; ok "C already installed" 'echo "$out" | grep -q "already installed"'
echo "D  undo"; out="$(run --undo)"; ok "D UNDONE: files back, cron out, new file aside" 'echo "$out" | grep -q UNDONE && [ "$(m8 "$OC")" = cf7f8b09 ] && [ "$(m8 "$LG")" = f2ade687 ] && [ ! -f "$SR" ] && [ -f "$SR.undone_S943" ] && ! grep -q S943 "$R/crontab.txt"'
echo "E  forced red at 4"; mk; out="$(REHEARSE_RED_AT=4 run)"; ok "E everything back" 'echo "$out" | grep -q RED && [ "$(m8 "$OC")" = cf7f8b09 ] && [ "$(m8 "$LG")" = f2ade687 ] && [ ! -f "$SR" ] && ! grep -q S943 "$R/crontab.txt" && [ ! -d "$R/root/deploy/.lock" ]'
echo "F  healthz 500 before"; mk; echo 500 > "$R/health_code"; out="$(run)"; ok "F nothing installed" 'echo "$out" | grep -q "healthz 500 before" && [ "$(m8 "$OC")" = cf7f8b09 ]'
echo "G  tampered kit"; mk; rm -rf "$R/kitT"; cp -rp "$KDIR" "$R/kitT"; echo "# x" >> "$R/kitT/server_record.py"
out="$(ROOT="$R/root" LOCK="$R/root/deploy/.lock" SYSTEMCTL="$R/systemctl" HEALTH_CMD="$R/health" CRONTAB="$R/crontab" APY="$(command -v python3)" bash "$R/kitT/install_S943_SERVER_RECORD.sh" 2>&1)"; ok "G SUMS gate" 'echo "$out" | grep -q "SUMS.md5 gate failed"'
echo "H  wrong live pin"; mk; echo "# drift" >> "$OC"; out="$(run)"; ok "H stop" 'echo "$out" | grep -q "it changed after this kit was built" && [ ! -f "$SR" ]'
echo "I  lock held"; mk; mkdir -p "$R/root/deploy/.lock"; out="$(run)"; ok "I refused" 'echo "$out" | grep -q "another build holds" && [ "$(m8 "$OC")" = cf7f8b09 ]'
echo "J  crontab -l empty"; mk; : > "$R/crontab.txt"; out="$(run)"; ok "J restored, crontab untouched, files back" 'echo "$out" | grep -q "crontab -l came back empty" && [ "$(m8 "$OC")" = cf7f8b09 ] && [ ! -f "$SR" ] && [ ! -s "$R/crontab.txt" ]'
echo "REHEARSAL $((n-f))/$n"; [ "$f" = 0 ]
