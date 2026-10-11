# S527_SETUP_CARDS — the five set-up cards on the Clinic PCs page

Kit of session 305 (the parent), 11-Oct-2026. Number claimed on the System Board (`_numbers` v355).

**The owner, 06-Oct:** *"all hostinger, cyberpanel, ssh login etc, websites setup and logins, links to open these from
here, bitwarden setup for storing logins in a phased easy and comprehensive way"*. **11-Oct 08:10 IST:** *"DO NOW"*.

On `https://followup.dr-manoj.in/finance/pcs`, section *Other set-ups*, the five "to be built" lines become five cards
like the biometric machine's, each with folding sections, links and a *Not written down yet* box:

- **Hostinger — the server:** the plan (KVM 2) and its renewal (10-Jun-2028; Webuzo to stay off), its name and address,
  hPanel, the doors open on its two firewalls, the nightly and weekly backups, and what to do if it is down.
- **CyberPanel:** what OpenLiteSpeed does for the website and the clinic pages, the certificates and the morning watch on
  them, its link (door 8090), and what not to touch.
- **SSH login:** key only (ed25519), password login off, `ssh vps`, WinSCP in Binary for .py/.env, where the key belongs
  (the PC and Bitwarden only), and the steps for a new PC or a lost key (hPanel's browser terminal).
- **Websites:** drmanojagarwal.com (WordPress here, renews 10-Jun-2029), dr-manoj.in (GoDaddy, auto-renew, its addresses
  on this server and its forwarding links), drmanojagarwal.in (retired, D422), nkpathology.com (another host).
- **Bitwarden:** what is decided (D421), what is in it already, how to file a login, and the four stages to bring the
  rest in.

**Where the lines come from:** the server's own files (cert_watch.py's site list, att_doctor.py's ports, the crontab,
the unit list), the records (the Register, the S230/S232 renewals and vendor register, the estate inventory, the GoDaddy
mails in the clinic account) and a read of the live sites. Nothing is guessed: what no record holds is said on the card.
**Never a password, a key, a code, nor where one lies on a PC** (S232: that is a map to the vault).

| file | from | to |
|---|---|---|
| `/root/finance/setup_notes.py` | `61348f425820d28f3e2a53435ca64acd` | `63477bc0781f6554b57a7868ea6161dc` |

Read only: `pc_kits.py` (imports the notes under its guard). Restarts `clinic-finance`.

**Proven:** `walk_s527.py` — the biometric card byte for byte the same with this box's live reads; five well-formed cards
after it; every link on this site or https; no secret-shaped text, login-file name or PC path to one; the two live reads
unchanged. The installer rehearsed on a made-up root.

## Install
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S527_SETUP_CARDS/install_S527_SETUP_CARDS.sh
```
## Undo
```
\cp -p /root/finance/setup_notes.py.bak_S527_61348f42 /root/finance/setup_notes.py && systemctl restart clinic-finance
```
