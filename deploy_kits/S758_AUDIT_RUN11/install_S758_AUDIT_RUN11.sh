#!/bin/bash
# =============================================================================
#  install_S758_AUDIT_RUN11.sh . kit S758 (09-Nov-2026, session S413, the parent) . the 09-Nov audit's asks; the owner's 'Proceed' 07:48
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s758kit && cp -rp /root/deploy/repo/deploy_kits/S758_AUDIT_RUN11 /tmp/s758kit && bash /tmp/s758kit/install_S758_AUDIT_RUN11.sh
#  (DRY=1 before bash: every gate, the walk, the summary and the certificate LOOK; nothing changed.)
#
#  PART 1 -- three files (backups *.bak_S758), clinic-finance restarted:
#    /root/finance/finance_ingest.py        029f5c20 -> e5853428  AF-37: a failed deduction at ingest opens a HIGH exception on the day
#    /root/state_backup/code_bundle.py      d6f94b12 -> aa8f985f  ask 3: code_nightly.MD5SUMS + finance_summary.json beside the bundle
#    /root/wa/clinic_health_report.py       27cbc9e4 -> 02b909e7  AF-36: the watchman's bracketed times read; no more July in 'last 24h'
#  PART 2 -- the public website's certificate (drmanojagarwal.com, ends 08-Dec-2026; renewal failing every night since 01/02-Nov,
#    the check file answering 404): LOOK -- which folder the website really serves the check file from (a temporary file, removed);
#    ACT -- only when exactly that is known: acme.sh's webroot set to it (its conf backed up), renewed, and the certificate the
#    site SERVES read back (more than 60 days left) -- else its conf is put back and nothing else is touched.
#  PART 3 -- root's crontab: the acme.sh line's output to /root/.acme.sh/s758_cron.log instead of a mail to an address that does
#    not exist (the nightly 00:07 bounce). Backup /root/deploy/crontab.bak_S758.
#  Undo:  bash /tmp/s758kit/install_S758_AUDIT_RUN11.sh --undo   (part 1, and the one cron line; the certificate setting stays --
#         putting the broken webroot back would only break the next renewal)
# =============================================================================
set -u
KIT="S758_AUDIT_RUN11"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
SITE="${SITE:-drmanojagarwal.com}"
ACME_HOME="${ACME_HOME:-/root/.acme.sh}"; ACME_CONF="${ACME_CONF:-$ACME_HOME/${SITE}_ecc/${SITE}.conf}"
LSWS="${LSWS:-/usr/local/lsws}"
CRONBAK="${CRONBAK:-/root/deploy/crontab.bak_S758}"
ROWS="$FIN/finance_ingest.py|finance_ingest.py|029f5c203508a2fe40946737d3550c6a|e5853428ed0ae8e32b19a3c8967517ac
$ROOT/state_backup/code_bundle.py|code_bundle.py|d6f94b121ec814469e61a01e58791db7|aa8f985f197289992e502b0cf997a25d
$ROOT/wa/clinic_health_report.py|clinic_health_report.py|27cbc9e4cb00b9c62ed85832bcc843ec|02b909e77fb6aa51286dc2973da5e8fd"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hcode /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  local bad=0
  while IFS='|' read -r LP KF FROM TO; do
    [ -f "$LP.bak_S758" ] && \cp -p "$LP.bak_S758" "$LP"; [ "$(m5 "$LP")" = "$FROM" ] || { echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S758 back by hand" >&2; bad=1; }
  done <<< "$ROWS"
  find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  echo "$bad"
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the three files back"
  local bad; bad=$(putback | tail -1); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$bad" = 0 ] && echo "   the three files are back byte-identically"
  echo "   finance healthz $(wait200). The certificate and the crontab were not touched. Send a photo of this screen to Claude."; exit 1
}
CERT_CHANGED=0; PROBE_FILE=""
on_signal() { trap '' INT TERM HUP; [ -n "$PROBE_FILE" ] && rm -f "$PROBE_FILE"; [ "$CERT_CHANGED" = 1 ] && [ -f "$ACME_CONF.bak_S758" ] && \cp -p "$ACME_CONF.bak_S758" "$ACME_CONF"; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
served_end() { if [ -n "${SERVED_CMD:-}" ]; then $SERVED_CMD; return; fi; echo | timeout 15 openssl s_client -servername "$SITE" -connect "${CERT_HOST:-127.0.0.1}:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | sed 's/^notAfter=//'; }
days_left() { local e; e=$(served_end); [ -n "$e" ] || { echo "?"; return; }; echo $(( ( $(date -d "$e" +%s) - $(date +%s) ) / 86400 )); }
conf_val() { sed -n "s/^$1='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" "$ACME_CONF" 2>/dev/null | head -1; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$KDIR/$KF")" = "$TO" ] || stop "the kit's $KF is not the built file"; done <<< "$ROWS"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$FIN/finance_ingest.py.bak_S758" ] || stop "no backups (*.bak_S758) -- nothing to undo"
  while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || stop "$LP is no longer this kit's (a later change) -- undo refused, so that change is not lost"; done <<< "$ROWS"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  bad=$(putback | tail -1); "$SYSTEMCTL" restart "$FSVC" || true
  echo "   the website's certificate setting is left as it is (putting the broken one back would only break the next renewal)"
  CL=$("$CRONTAB" -l 2>/dev/null); if [ -n "$CL" ] && printf '%s\n' "$CL" | grep -q 's758_cron.log'; then
    printf '%s\n' "$CL" | sed 's#>> /root/.acme.sh/s758_cron.log 2>&1#> /dev/null#' > "/tmp/s758undo.cron" && "$CRONTAB" "/tmp/s758undo.cron" && echo "   root's crontab: the acme.sh line only, put back"
    rm -f /tmp/s758undo.cron; fi
  [ "$bad" = 0 ] && echo "UNDONE: the three files are back; finance healthz $(wait200)" || echo "!! not every file is back -- send a photo"
  exit 0
fi
echo "[1/8] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
ALL_TO=1; while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || ALL_TO=0; done <<< "$ROWS"
if [ "$ALL_TO" = 1 ]; then echo "-- part 1 ALREADY INSTALLED (the three files are the kit's)"; else
  while IFS='|' read -r LP KF FROM TO; do L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"; done <<< "$ROWS"
fi
SCR=$(mktemp -d /tmp/s758.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/live" "$SCR/remake" "$SCR/old"
if [ "$ALL_TO" = 0 ]; then
  while IFS='|' read -r LP KF FROM TO; do \cp "$LP" "$SCR/live/$KF"; \cp "$LP" "$SCR/old/$KF"; done <<< "$ROWS"
  "$APY" -B "$KDIR/make_s758.py" "$SCR/live" "$SCR/remake" >/dev/null 2>&1 || stop "make_s758.py did not run on the live bytes"
  while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$SCR/remake/$KF")" = "$TO" ] || stop "make_s758.py on the live bytes does not give the kit's $KF"; done <<< "$ROWS"
  for f in finance_ingest.py code_bundle.py clinic_health_report.py; do
    "$APY" -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $APY"
    "$VPY" -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $VPY"
  done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  echo "[2/8] the three live files are the ones this kit was built from; remade on the box byte-identically; all compile under both pythons"
  "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/walk.db" || stop "could not make the scratch copy of finance.db"
  chmod 600 "$SCR/walk.db"
  R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s758.py" "$KDIR" "$FIN" "$SCR/walk.db" 2>/dev/null | tail -1)
  case "$R" in "WALK OK"*) ;; *) stop "the walk is not green ($R)";; esac
  \cp "$KDIR/walk_s758.py" "$SCR/old/"
  R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$SCR/old/walk_s758.py" "$SCR/old" "$FIN" "$SCR/walk.db" --control 2>/dev/null | tail -1)
  case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
  echo "[3/8] the walk on a scratch copy of finance.db (made-up bills on 2030-03-01): $R; the live files: $R2"
  S=$(cd "$SCR" && "$VPY" -B -c "import sys,json; sys.path.insert(0,sys.argv[1]); import code_bundle as C; s=C.s758_summary(sys.argv[2]); r=json.dumps(s,separators=(',',':')); print('%d bytes . %d tables counted . %d days . errors: %s' % (len(r.encode()), len(s.get('tables') or {}), len(s.get('days') or {}), [k for k,v in s.items() if isinstance(v,dict) and 'error' in v] or 'none'))" "$KDIR" "$SCR/walk.db" 2>&1 | tail -1)
  rm -f "$SCR/walk.db"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  echo "[4/8] finance_summary.json as it would ship tonight (from the copy): $S"
  case "$S" in *"errors: none"*) ;; *) stop "the summary is not clean ($S)";; esac
fi
# ---------------------------------------------------------------- PART 2 LOOK (read-only but for one temporary file)
CERT_ACT=""; CERT_NOTE=""
echo "[5/8] the website's certificate -- LOOK"
DL=$(days_left); echo "      served now: ends $(served_end) -- $DL days left"
if ! [ "$DL" -eq "$DL" ] 2>/dev/null; then CERT_NOTE="the served certificate could not be read -- nothing changed"
elif [ "$DL" -gt 60 ]; then CERT_NOTE="the served certificate has $DL days left -- nothing to renew"
elif [ ! -f "$ACME_CONF" ]; then CERT_NOTE="no acme.sh conf at $ACME_CONF"; else
  WR=$(conf_val Le_Webroot); echo "      acme.sh's webroot for $SITE: ${WR:-?}"
  NAMES=$(printf '%s,%s' "$(conf_val Le_Domain)" "$(conf_val Le_Alt)" | tr ',' '\n' | awk 'NF && $0!="no" && !s[$0]++'); [ -n "$NAMES" ] || NAMES="$SITE"
  echo "      the certificate's names: $(echo $NAMES)"
  VH="$LSWS/conf/vhosts/$SITE/vhost.conf"; [ -f "$VH" ] || VH=$(grep -l -s "vhDomain.*$SITE" "$LSWS"/conf/vhosts/*/vhost.conf 2>/dev/null | head -1)
  CANDS="$WR"
  if [ -n "$VH" ]; then
    VHN=$(basename "$(dirname "$VH")")
    VHR=$(awk -v n="$VHN" '$1=="virtualhost" && $2==n {f=1} f && $1=="vhRoot" {print $2; exit}' "$LSWS/conf/httpd_config.conf" 2>/dev/null); VHR="${VHR:-/home/$VHN}"; VHR="${VHR%/}"
    DR=$(awk '$1=="docRoot"{print $2; exit}' "$VH" | sed "s#\$VH_ROOT#$VHR#; s#\$SERVER_ROOT#$LSWS#; s#\$VH_NAME#$VHN#"); DR="${DR%/}"
    CX=$(awk '/context[[:space:]]+\/\.well-known\/acme-challenge/{f=1} f && $1=="location"{print $2; exit}' "$VH" | sed "s#\$VH_ROOT#$VHR#; s#\$SERVER_ROOT#$LSWS#; s#\$VH_NAME#$VHN#")
    CXR="${CX%/}"; CXR="${CXR%/.well-known/acme-challenge}"
    echo "      the website ($VH): docRoot ${DR:-?}; a /.well-known/acme-challenge context: ${CX:-none}"
    CANDS="$CANDS
$CXR
$DR"
  fi
  GOOD=""; NGOOD=0
  for C in $(printf '%s\n' "$CANDS" $LSWS/Example/html "/home/$SITE/public_html" | sed 's#/*$##' | awk 'NF' | while read -r x; do [ -d "$x" ] && realpath "$x"; done | awk '!s[$0]++'); do
    [ -d "$C" ] || continue
    D="$C/.well-known/acme-challenge"; MADE=""
    [ -d "$C/.well-known" ] || MADE="$C/.well-known"; [ -n "$MADE" ] || { [ -d "$D" ] || MADE="$D"; }
    mkdir -p "$D" 2>/dev/null || continue
    T="s758probe$(date +%s%N | tail -c 9)"; PROBE_FILE="$D/$T"; echo "$T" > "$D/$T"; chmod 644 "$D/$T"
    ALLOK=1
    for NM in $NAMES; do
      B=$(curl -s -L -m 12 "${PROBE_BASE:-http://$NM}/.well-known/acme-challenge/$T" 2>/dev/null | head -c 64)
      [ "$B" = "$T" ] || ALLOK=0
    done
    rm -f "$D/$T"; PROBE_FILE=""; [ -n "$MADE" ] && { rmdir "$D" 2>/dev/null; [ "$MADE" = "$C/.well-known" ] && rmdir "$C/.well-known" 2>/dev/null; }
    if [ "$ALLOK" = 1 ]; then echo "      $C -- the website SERVES the check file from here (for every name)"; GOOD="$C"; NGOOD=$((NGOOD+1)); else echo "      $C -- not served from here"; fi
  done
  if [ "$NGOOD" = 1 ]; then CERT_ACT="$GOOD"; [ "$GOOD" = "$WR" ] && CERT_NOTE="acme.sh's webroot already serves -- renew only" || CERT_NOTE="acme.sh's webroot is wrong -- it becomes $GOOD"
  elif [ "$NGOOD" = 0 ]; then CERT_NOTE="no folder serves the check file -- nothing changed (Claude needs these lines)"
  else CERT_NOTE="$NGOOD folders serve it -- ambiguous, nothing changed (Claude needs these lines)"; fi
fi
echo "      => $CERT_NOTE"
ACMEL=$("$CRONTAB" -l 2>/dev/null | grep -c 'acme.sh --cron.*> */dev/null *$')
echo "[6/8] root's crontab: $ACMEL acme.sh line(s) mailing their output (expected 1)"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate run; nothing changed."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
# ---------------------------------------------------------------- PART 1 ACT
if [ "$ALL_TO" = 0 ]; then
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
  while IFS='|' read -r LP KF FROM TO; do { \cp -p "$LP" "$LP.bak_S758" && [ "$(m5 "$LP.bak_S758")" = "$FROM" ]; } || stop "could not keep a backup of $LP"; done <<< "$ROWS"
  PLACED=1
  while IFS='|' read -r LP KF FROM TO; do
    \cp "$KDIR/$KF" "$LP.s758new" && chmod --reference="$LP.bak_S758" "$LP.s758new" && { chown --reference="$LP.bak_S758" "$LP.s758new" 2>/dev/null; true; } \
      && mv -f "$LP.s758new" "$LP" || restore "$LP could not be placed"
    [ "$(m5 "$LP")" = "$TO" ] || restore "$LP read-back did not match"
  done <<< "$ROWS"
  find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  T0=$(date '+%Y-%m-%d %H:%M:%S')
  "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
  c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
  ( cd "$FIN" && "$APY" -B -c "import finance_ingest as f, sys; sys.exit(0 if hasattr(f, '_s758_noncash_mark') else 3)" ) >/dev/null 2>&1 || restore "finance_ingest.py does not carry the S758 mark"
  sleep 2
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
  JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'finance_ingest|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
  PLACED=0
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0
  echo "[7/8] part 1 placed and read back (backups *.bak_S758); $FSVC restarted: healthz $c1; the journal clean"
fi
# ---------------------------------------------------------------- PART 2 ACT and PART 3
if [ -n "$CERT_ACT" ]; then
  [ -f "$ACME_CONF.bak_S758" ] || \cp -p "$ACME_CONF" "$ACME_CONF.bak_S758" || CERT_ACT=""
fi
if [ -n "$CERT_ACT" ]; then
  if [ "$(conf_val Le_Webroot)" != "$CERT_ACT" ]; then
    CERT_CHANGED=1; sed -i "s#^Le_Webroot=.*#Le_Webroot='$CERT_ACT'#" "$ACME_CONF"
  fi
  timeout 240 "$ACME_HOME/acme.sh" --renew -d "$SITE" --ecc --force --home "$ACME_HOME" > "$SCR/acme.out" 2>&1; RC=$?
  if [ "$RC" = 0 ]; then
    CERT_CHANGED=0
    DL2=$(days_left)
    if ! [ "$DL2" -gt 60 ] 2>/dev/null; then              # renewed on disk; the web server may still hold the old one
      if [ -x "$LSWS/bin/lswsctrl" ]; then "$LSWS/bin/lswsctrl" restart >/dev/null 2>&1; else "$SYSTEMCTL" restart lsws >/dev/null 2>&1; fi
      sleep 8; DL2=$(days_left)
      W1=$(curl -s -o /dev/null -m 12 -w '%{http_code}' --resolve "$SITE:443:${CERT_HOST:-127.0.0.1}" "${SITE_CHECK:-https://$SITE/}" 2>/dev/null)
      echo "      the web server was reloaded; the website answers $W1"
    fi
    if [ "$DL2" -gt 60 ] 2>/dev/null; then echo "      the website's certificate RENEWED: it now serves one ending $(served_end) -- $DL2 days"
    else echo "      !! acme.sh renewed (its webroot now $CERT_ACT, kept), but the certificate SERVED still shows $DL2 days -- send a photo to Claude"; fi
  else
    \cp -p "$ACME_CONF.bak_S758" "$ACME_CONF"; CERT_CHANGED=0
    echo "      !! the renewal failed (acme.sh exit $RC); acme.sh's conf put back; the web server NOT restarted. Its last words: $(tail -3 "$SCR/acme.out" | tr '\n' ' ' | cut -c1-300)"
    echo "      Nothing else was touched. Send a photo of this screen to Claude."
  fi
else
  echo "      the certificate: nothing changed ($CERT_NOTE)"
fi
if [ "$ACMEL" = 1 ] && "$CRONTAB" -l > "$CRONBAK" 2>/dev/null && [ -s "$CRONBAK" ]; then
  chmod 600 "$CRONBAK"
  sed 's#\(acme.sh --cron.*\)> */dev/null *$#\1>> /root/.acme.sh/s758_cron.log 2>\&1#' "$CRONBAK" > "$SCR/cron.new"
  if [ "$(diff "$CRONBAK" "$SCR/cron.new" | grep -c '^[<>]')" != 2 ]; then
    echo "[8/8] root's crontab NOT changed (the edit did not come out as exactly one line)"
  elif "$CRONTAB" "$SCR/cron.new" && "$CRONTAB" -l | grep -q 's758_cron.log'; then
    echo "[8/8] root's crontab: the acme.sh line now writes to /root/.acme.sh/s758_cron.log (backup $CRONBAK)"
  else
    "$CRONTAB" "$CRONBAK" 2>/dev/null; echo "[8/8] !! root's crontab: the edit did not read back -- put back as it was"
  fi
else
  echo "[8/8] root's crontab: not changed ($ACMEL matching lines, expected 1 -- or it could not be read)"
fi
echo ""
echo "$KIT: DONE."
