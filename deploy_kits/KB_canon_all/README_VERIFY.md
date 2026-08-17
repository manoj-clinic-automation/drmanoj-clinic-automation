# KB_canon_all — EVERY manifest-pinned canonical row, byte-authoritative in git
From this kit onward, Phase 0 hash verification is ONE mechanical command with
no transcription step and no judgment calls:

    cd /tmp && rm -rf kbv && git clone --depth 1 -q \
      https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
      && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt

Every row PASSES or FAILS definitively, **and the command must exit 0** — a WARNING that a listed
file could not be read is a FAIL, not a footnote (**F-119**: a row for a file that had been superseded
away locked the door to the next session, and nothing said so).

**`MD5SUMS_ALL.txt` is the ONE checksum authority for this folder (F-120).** It once shipped alongside
`SUMS.md5` and `MD5SUMS.txt`, both stale, both able to convict a correct file; they are now in
`deploy_kits/_attic_S186/`. Exactly two files are excluded from it, because neither can be inside it:
`MD5SUMS_ALL.txt` itself and `KIT_ID.txt`, which carries its hash. **Everything else in this folder is
listed.** The inverse check is part of the close: files on disk = rows listed + those two. Project knowledge remains the READING
copy; git is the VERIFICATION copy. RULE: a hash verdict is only ever
pronounced on bytes delivered as a FILE (git clone, or project_read returning
a file path) — re-keyed inline text may corroborate, never convict or acquit.
Push with deploy\push_kit.bat. Nothing to install; do not run vps_deploy.
