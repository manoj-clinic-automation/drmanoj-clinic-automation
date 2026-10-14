#!/bin/bash
# rehearse_s556.sh -- kit S556_REFUSED_TEXT_ROAD: the installer on a MADE-UP root (/tmp/s556rh), never the live one.
#   A copy of /root/finance (code + a backup-API copy of finance.db), a made-up clone (its DUTY_MAP v13 and .md, S543's kit folder for its walk),
#   a stand-in service (the real finance_app from the made-up root on 127.0.0.1:18556, run by a stand-in systemctl), a stand-in git whose
#   'pull' brings the kit's v14 map (log / show are read from the real clone's history; status says clean). Four runs: (1) red after placing
#   (a stand-in journal with a Traceback) -> the three files back byte-identically; (2) green -> PLACED; (3) again -> ALREADY INSTALLED;
#   (4) PHASE=pull -> the made-up clone at v14. The live box is only read (the databases by the backup API).
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
R=/tmp/s556rh; rm -rf "$R"; mkdir -p "$R/finance/spine" "$R/finance/finance_ui" "$R/repo/claude_code_briefs" "$R/repo/deploy_kits" "$R/bin"
cp -p /root/finance/*.py "$R/finance/"; cp -p /root/finance/*.html /root/finance/*.json /root/finance/*.sql "$R/finance/" 2>/dev/null
cp -rp /root/finance/finance_ui/. "$R/finance/finance_ui/"; cp -p /root/finance/spine/*.py /root/finance/spine/*.json "$R/finance/spine/" 2>/dev/null
/usr/bin/python3 -c "import sqlite3; s=sqlite3.connect('file:/root/finance/finance.db?mode=ro',uri=True,timeout=60); d=sqlite3.connect('$R/finance/finance.db'); s.backup(d); d.close(); s.close()"
cp -p /root/deploy/repo/claude_code_briefs/DUTY_MAP.json /root/deploy/repo/claude_code_briefs/DUTY_MAP.md "$R/repo/claude_code_briefs/"
cp -rp /root/deploy/repo/deploy_kits/S543_ORDER_SHEET_MARG "$R/repo/deploy_kits/"
cat > "$R/bin/systemctl" <<EOF
#!/bin/bash
PIDF=$R/standin.pid
case "\$1" in
  restart) if [ -f \$PIDF ]; then P=\$(cat \$PIDF); kill -9 \$P 2>/dev/null; for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do kill -0 \$P 2>/dev/null || break; sleep 0.5; done; fi; pkill -9 -f "18556, fa.app" 2>/dev/null; sleep 2
           ( cd $R/finance && FINANCE_DB=$R/finance/finance.db PYTHONDONTWRITEBYTECODE=1 nohup /usr/bin/python3 -B -c "import sys; sys.path.insert(0, '$R/finance'); import finance_app as fa; from werkzeug.serving import run_simple; run_simple('127.0.0.1', 18556, fa.app, use_reloader=False)" >$R/standin.log 2>&1 & echo \$! > \$PIDF ); exit 0;;
  is-active) [ -f \$PIDF ] && kill -0 \$(cat \$PIDF) 2>/dev/null && { [ "\${2:-}" = "--quiet" ] || echo active; exit 0; }; [ "\${2:-}" = "--quiet" ] || echo inactive; exit 3;;
esac
exit 0
EOF
cat > "$R/bin/git" <<EOF
#!/bin/bash
# stand-in: 'pull --ff-only' brings the kit's v14 map and the kit folder, as the real pull would; log / show read the real clone's history
case "\$3" in
  pull) /usr/bin/python3 -B "$KDIR/make_s556.py" --only server --fin $R/standin_from --briefs /root/deploy/repo/claude_code_briefs --out $R/pulled >/dev/null || exit 1
        cp -p $R/pulled/DUTY_MAP.json $R/pulled/DUTY_MAP.md $R/repo/claude_code_briefs/; rm -rf $R/repo/deploy_kits/S556_REFUSED_TEXT_ROAD; cp -rp "$KDIR" $R/repo/deploy_kits/S556_REFUSED_TEXT_ROAD
        echo "Fast-forward (stand-in)";;
  status) exit 0;;
  log|show) shift 2; exec /usr/bin/git -C /root/deploy/repo "\$@";;
  *) exit 1;;
esac
EOF
printf '#!/bin/bash\necho "Traceback (most recent call last): (stand-in red)"\n' > "$R/bin/journal_red"
printf '#!/bin/bash\nexit 0\n' > "$R/bin/journal_ok"
chmod +x "$R/bin/"*
mkdir -p "$R/standin_from"; for f in reports_tile.py reports_watch.py order_sheet.py; do cp -p "/root/finance/$f" "$R/standin_from/"; done
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ENVS=(FIN="$R/finance" REPO="$R/repo" LOCK="$R/lock" FIN_PORT=18556 SYSTEMCTL="$R/bin/systemctl" GIT="$R/bin/git" TMPW="$R" MAPBAK="$R/DUTY_MAP_v13.bak_S556")
"$R/bin/systemctl" restart x; sleep 4
B0="$(for f in reports_tile.py reports_watch.py order_sheet.py; do m5 "$R/finance/$f"; done)"
echo "== run 1: red after placing (a stand-in journal with a Traceback)"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_red" bash "$KDIR/install_S556_REFUSED_TEXT_ROAD.sh" > "$R/run1.out" 2>&1; R1=$?
grep -E "^\[|^!!|^   /tmp|^   after|^   the clone|^   the database" "$R/run1.out" | grep -v "^\[3/11\]" | tail -14
B1="$(for f in reports_tile.py reports_watch.py order_sheet.py; do m5 "$R/finance/$f"; done)"
[ "$R1" = 1 ] && [ "$B0" = "$B1" ] && echo "REHEARSAL 1 OK: red -> the three files byte-identical to before (exit $R1)" || echo "REHEARSAL 1 FAILED (exit $R1)"
echo "== run 2: green"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S556_REFUSED_TEXT_ROAD.sh" > "$R/run2.out" 2>&1; R2=$?
grep -E "^\[|^!!|^ *  /finance|^PAGE|PLACED" "$R/run2.out" | grep -v "^\[3/11\]" | tail -16
[ "$R2" = 0 ] && grep -q "the server part is PLACED" "$R/run2.out" && echo "REHEARSAL 2 OK: green install on the made-up root" || echo "REHEARSAL 2 FAILED (exit $R2)"
echo "== run 3: again"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S556_REFUSED_TEXT_ROAD.sh" > "$R/run3.out" 2>&1; R3=$?
tail -1 "$R/run3.out"
[ "$R3" = 0 ] && grep -q "ALREADY INSTALLED" "$R/run3.out" && echo "REHEARSAL 3 OK: ALREADY INSTALLED" || echo "REHEARSAL 3 FAILED (exit $R3)"
echo "== run 4: PHASE=pull"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_ok" PHASE=pull bash "$KDIR/install_S556_REFUSED_TEXT_ROAD.sh" > "$R/run4.out" 2>&1; R4=$?
tail -2 "$R/run4.out"
[ "$R4" = 0 ] && grep -q "map gate is v14" "$R/run4.out" && echo "REHEARSAL 4 OK: the made-up clone pulled to v14" || echo "REHEARSAL 4 FAILED (exit $R4)"
pkill -9 -f "18556, fa.app" 2>/dev/null
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
