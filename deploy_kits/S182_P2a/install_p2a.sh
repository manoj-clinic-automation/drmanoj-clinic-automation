#!/bin/bash
# =============================================================================
#  install_p2a.sh · kit S182_P2a — F-98: the portal must not assume "doctor".
#
#  A browser holding the legacy PIN-era device cookie, with NO SSO session, was
#  treated as the doctor by home() and by _is_doctor() — reaching every
#  @doctor_required surface (Gist, Call Console, staff coaching report). That is
#  F-84's pattern (identity granted for convenience) sitting in the SSO broker
#  itself. This kit makes identity PROVEN, never assumed.
#
#  D264 is preserved deliberately: the new behaviour keys off _sso_ready(), so
#  if the portal secret ever becomes unreadable the legacy device-trust path is
#  UNCHANGED and nobody is locked out by a config failure.
#
#  NO tile changes. The gate asserts the tile set is byte-identical to live.
#  Shape per D317: preflight -> SUMS -> KIT_ID -> LIVE-FILE CURRENCY -> smoke
#  gate BEFORE any swap -> backup -> swap -> restart -> health -> HONEST red.
# =============================================================================
set -u

KIT_NAME="S182_P2a"
LIVE=/root/portal
SVC=clinic-portal
PORT=8090
# The portal is served by gunicorn from the wa venv, so the gate must run under
# the SAME interpreter that will import the file in production (F-53 discipline).
PY=/root/wa/venv/bin/python3
EXPECT_LIVE_MD5="410388daa9cf39daba6bb2d4c187a1e6"

for c in systemctl md5sum awk curl cp mv; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing before touching anything"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing before touching anything"; exit 1; }
[ -f "$LIVE/portal.py" ] || { echo "!! preflight: $LIVE/portal.py not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

LIVE_NOW="$(md5sum "$LIVE/portal.py" | awk '{print $1}')"

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum portal.py.new | awk '{print $1}')" ] \
&& { [ "$LIVE_NOW" = "$EXPECT_LIVE_MD5" ] || {
       echo ""
       echo "!! REFUSING — the live portal.py is NOT the file this kit was built against."
       echo "     live now : $LIVE_NOW"
       echo "     expected : $EXPECT_LIVE_MD5"
       echo "   Nothing has been touched. Installing would overwrite whatever changed"
       echo "   since this kit was built. Send the current /root/portal/portal.py back"
       echo "   and the kit will be rebuilt on top of it."
       exit 1; }; } \
&& echo "-- live-file currency OK ($LIVE_NOW)" \
&& echo "-- running the smoke gate BEFORE touching anything live..." \
&& "$PY" smoke_portal_F98.py portal.py.new "$LIVE/portal.py" \
&& "$PY" -m py_compile portal.py.new \
&& echo "-- gate green; installing" \
&& cp portal.py.new "$LIVE/portal.py.new" \
&& cd "$LIVE" \
&& cp portal.py portal.py.bak_S182P2 \
&& touch .S182P2_touched \
&& mv portal.py.new portal.py \
&& systemctl restart "$SVC" \
&& sleep 3 \
&& curl -sf "http://127.0.0.1:$PORT/portal/health" >/dev/null \
&& rm -f .S182P2_touched \
&& echo "" \
&& echo "$KIT_NAME INSTALLED — smoke green, service restarted, health OK" \
&& echo "   backup: $LIVE/portal.py.bak_S182P2" \
&& echo "   change: identity proven, never assumed (F-98). Tiles unchanged." \
&& echo "   note  : anyone on a legacy device cookie must now sign in once." \
|| { echo ""; \
     echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S182P2_touched" ]; then \
        echo "   live files WERE touched — restoring portal.py from the S182P1 backup:"; \
        cp -f "$LIVE/portal.py.bak_S182P2" "$LIVE/portal.py" && echo "   portal.py restored"; \
        systemctl restart "$SVC" && echo "   $SVC restarted on the restored file"; \
        sleep 2; \
        if curl -sf "http://127.0.0.1:$PORT/portal/health" >/dev/null; then \
          echo "   health OK after restore — the portal is back as it was."; \
        else \
          echo "   !! health STILL failing after restore — check: journalctl -u $SVC -n 40"; \
        fi; \
        rm -f "$LIVE/.S182P2_touched"; \
     else \
        echo "   the gate fired BEFORE anything live was touched — nothing to restore."; \
        echo "   the portal is running exactly as it was."; \
     fi; \
     exit 1; }
