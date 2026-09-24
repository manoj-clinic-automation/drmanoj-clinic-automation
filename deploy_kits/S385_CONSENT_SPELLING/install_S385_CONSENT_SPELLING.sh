#!/bin/bash
# =============================================================================
#  install_S385_CONSENT_SPELLING.sh · kit S385_CONSENT_SPELLING (session 279, 24-Sep-2026)
#
#  THE OWNER, 24-Sep-2026: "the translation of the name and ... the address were not correct, and I edited them. Saved
#  them at one place, but when the print came, all the other places it was showing the wrong translation."
#  The fault: the consent body is editable, but the name appears in several paragraphs and the header printed on
#  every page is built from the generated values -- an edit changed one place only (his archived consent carries the
#  first name in two spellings). Now a "Hindi spelling" box after Generate: correct once -> every occurrence and the
#  header change; the spelling is remembered (tr_dict.json beside the case ledger) and used first next time; a
#  hand-edit made in some places but not all is caught before printing.
#
#  FILES:  /root/wa/casepack/casepack_page.html  S216 d5d4a3e7 -> 08807cdf
#          /root/portal/casepack_portal.py        760e8c36 -> cbbd392d  (+ /portal/casepack/trdict GET/POST, owner-only)
#  Restarts clinic-portal.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S385_CONSENT_SPELLING/install_S385_CONSENT_SPELLING.sh
# =============================================================================
set -u
KIT="S385_CONSENT_SPELLING"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; PD="${PD:-/root/portal}"; CPD="${PORTAL_CASEPACK_DIR:-/root/wa/casepack}"; PPORT="${PORTAL_PORT:-8099}"
G_FROM=d5d4a3e7bd10fb1553f86bcf9d21e16c; G_TO=08807cdfbfd595f6425f5cc277a38dbb
M_FROM=760e8c36a5e3182e0d3d418564ec6d84; M_TO=cbbd392d849f7bc5824197d25830cf05
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 casepack_page.html)" = "$G_TO" ] && [ "$(m5 casepack_portal.py)" = "$M_TO" ] || { say "!! [1/6] kit files not at their pins - nothing installed"; exit 1; }
say "[1/6] kit gates green"
if [ "$(m5 "$CPD/casepack_page.html")" = "$G_TO" ] && [ "$(m5 "$PD/casepack_portal.py")" = "$M_TO" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
[ "$(m5 "$CPD/casepack_page.html")" = "$G_FROM" ] || { say "!! [2/6] casepack_page.html is $(m5 "$CPD/casepack_page.html"), not S216 - nothing installed"; exit 1; }
[ "$(m5 "$PD/casepack_portal.py")" = "$M_FROM" ] || { say "!! [2/6] casepack_portal.py is $(m5 "$PD/casepack_portal.py"), not its pin - nothing installed"; exit 1; }
say "[2/6] live pins exact (page S216 · casepack_portal)"
"$VPY" -B -m py_compile casepack_portal.py check_s385.py || { say "!! [3/6] compile failed - nothing installed"; exit 1; }
COUT="$( cd /tmp && timeout 60 "$VPY" -B "$KDIR/check_s385.py" "$KDIR" "$CPD/casepack_page.html" 2>&1 | tail -1 )"
echo "$COUT" | grep -q "^CHECK_S385 OK" || { say "!! [3/6] check red: $COUT - nothing installed"; exit 1; }
say "[3/6] $COUT"
BG="$CPD/casepack_page.html.bak_S385_d5d4a3e7"; BM="$PD/casepack_portal.py.bak_S385_760e8c36"
\cp -p "$CPD/casepack_page.html" "$BG" && \cp -p "$PD/casepack_portal.py" "$BM" || { say "!! [4/6] backups failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing (${1:-a check failed}) - restoring byte-identically"
  \cp -p "$BG" "$CPD/casepack_page.html"; \cp -p "$BM" "$PD/casepack_portal.py"; systemctl restart clinic-portal || true; sleep 4
  say "   page $(m5 "$CPD/casepack_page.html") · casepack_portal $(m5 "$PD/casepack_portal.py")"; exit 1
}
\cp -p casepack_page.html "$CPD/casepack_page.html" && [ "$(m5 "$CPD/casepack_page.html")" = "$G_TO" ] || restore "the page did not read back"
\cp -p casepack_portal.py "$PD/casepack_portal.py" && [ "$(m5 "$PD/casepack_portal.py")" = "$M_TO" ] || restore "casepack_portal.py did not read back"
say "[4/6] placed; backups $BG · $BM"
systemctl restart clinic-portal || restore "clinic-portal would not restart"
sleep 4; systemctl is-active --quiet clinic-portal || restore "clinic-portal not active after restart"
PH=$(curl -s -m 8 "http://127.0.0.1:$PPORT/portal/health"); echo "$PH" | grep -q '"status": *"ok"' || restore "portal health: $(echo "$PH" | cut -c1-100)"
TD=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT/portal/casepack/trdict")
{ [ "$TD" = 302 ] || [ "$TD" = 401 ] || [ "$TD" = 403 ]; } || restore "the spelling door without login answered $TD (expected locked)"
say "[5/6] clinic-portal healthy; the spelling door is locked without a login ($TD)"
md5sum "$CPD/casepack_page.html" "$PD/casepack_portal.py"
say "[6/6] $KIT: DONE -- open the Case Pack, Generate the consent, correct the spelling in the new box"
