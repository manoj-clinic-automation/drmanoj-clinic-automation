# S617_PCS_PAGE_LIVE — the Clinic PCs page keeps itself current (S336, 22-Oct-2026)

**The owner, his board note (his pick 07:12 IST):** *"clinic pc tile - keep the content and data updated there, so that
it stays current always"*.

**What was there.** On `https://followup.dr-manoj.in/finance/pcs` the PC and phone cards are already read live (the health
rows, each PC's heartbeat, the kits on the server). The *Other set-ups* cards (S492, S527) were typed once and could only age.

**What it does** (`/root/finance/setup_notes.py` d32423d1 → new, 12 exact edits in `edits_s617.py`):
- the **Hostinger**, **CyberPanel** and **Websites** cards carry a **Now** box read from the server each time the page
  opens: the disk, how long the server has been running, the nightly jobs and backups as the freshness check last found
  them (late ones named), and this morning's certificate check — a check too old, or a file that cannot be read, says so;
- every set-up card ends *Notes checked 22-Oct-2026*; the page says a change to a set-up updates its card the same day;
- the Websites card brought up to date: the website's mail through the clinic Gmail (S590), its forms to the clinic Gmail
  only (S592), the vendor's FTP login removed and FTP off (S589).

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S617_PCS_PAGE_LIVE/install_S617_PCS_PAGE_LIVE.sh

**Proven by:** `walk_s617.py` (14 checks on made-up files — on time / late, healthy / a problem, old checks, missing
files; with the additions taken out the page is the old page byte for byte; no password-shaped text) and, on the box, the
real files read only; the S527 file goes RED. Screen review at 375 px by a sub-agent.

**Undo:** `--undo` puts the S527 file back (`/root/s617_backup/`) and restarts clinic-finance.

**The standing rule this records:** a kit that changes a PC, a phone or a set-up updates its card on this page in the same kit.
