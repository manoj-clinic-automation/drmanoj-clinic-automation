# S455_IPV6_FACTS — session 291, 03-Oct-2026 — the parent — READ-ONLY

**Why.** F-692: `followup.dr-manoj.in` has one IPv4 address and no IPv6 address. On 02-Oct the reception PC was on the
owner's phone hotspot, which gave it IPv6 only: Google Drive worked, the clinic server could not be reached at all, and
both the direct upload (S449) and the server job door (S453) were dead until the PC was on another connection. The owner,
03-Oct: fix it. The rule of this project is that no change is built from an inferred anchor when the real file can be
read — and the web server's listener file is in no backup the assistant can reach. So this kit only **reads**.

**What the one line does** (it places nothing, edits nothing, restarts nothing):

1. takes the server-wide build lock (`/root/deploy/.claude_code_build.lock`, CLAUDE.md, F-694 — the first parent script
   to do so) and releases it on every exit;
2. confirms that the Reception PC kit the *Clinic PCs* page serves is whole after the pull — `kit.zip` `994871f3…` and
   the bundled Python `30a7b6ab…`, both exactly what `KIT_INFO.txt` names. This is the kit of 03-Oct: `secure_setup.cmd`
   is in it and the installer puts it beside the agent, so the firewall rules come back after a Windows reinstall
   (README_REINSTALL.txt step A.7);
3. reads what the box has for IPv6 — global addresses, the default route, the kernel switch, what listens on the web
   ports, the web server's own listener lines (name, address, secure — nothing else of that file), the firewall's IPv6
   side, the name's A and AAAA answers, one outbound test, and whether the site already answers on the box's own IPv6
   address — and writes it to `/root/finance/ipv6_facts_s455.json` (mode 600). The 01:35 code bundle carries
   `/root/finance/*.json` to the owner's PC, where the next session reads it. No secret and no patient data is in it.

**The line**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S455_IPV6_FACTS/read_S455_IPV6_FACTS.sh

**What comes after, and is NOT in this kit:** the change itself — the web server listening on IPv6 if it does not, the
firewall's IPv6 side if it is shut, and one AAAA record at the name's DNS — built from the file above, walked, and
installed by its own line. `ipv6_facts_s455.json` may be deleted once that kit is live.

**Proof before it left the PC:** run in the cloud workspace against a scratch tree holding the real `kit.zip`,
`KIT_INFO.txt` and the bundled Python — whole kit → green; a changed `kit.zip` → the red line and exit 1; a held lock →
exit 3 and nothing read; the lock gone after every exit; the facts file written and valid JSON on a box with no `ip`.
