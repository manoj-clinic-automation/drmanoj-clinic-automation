# KB_canon_all — EVERY manifest-pinned canonical row, byte-authoritative in git
From this kit onward, Phase 0 hash verification is ONE mechanical command with
no transcription step and no judgment calls:

    cd /tmp && rm -rf kbv && git clone --depth 1 -q \
      https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
      && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt

Every row PASSES or FAILS definitively. Project knowledge remains the READING
copy; git is the VERIFICATION copy. RULE: a hash verdict is only ever
pronounced on bytes delivered as a FILE (git clone, or project_read returning
a file path) — re-keyed inline text may corroborate, never convict or acquit.
Push with deploy\push_kit.bat. Nothing to install; do not run vps_deploy.
