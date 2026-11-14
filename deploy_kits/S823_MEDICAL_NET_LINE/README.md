# S823_MEDICAL_NET_LINE — the medical PC says which connection carries it (session 454, the Sanjeevni chat, 14-Nov-2026)

**Why (F-1133, D966):** since 13-Nov the medical PC has a Wi-Fi USB dongle beside the network cable, both on the same Airtel line. Nothing said which one the PC actually uses. The owner's "build it" (06:00 IST 14-Nov).

**What changes:** ONE file on the medical PC, `D:\SendToClinic\medical_agent.py`, **S499.1 (d91fa79a) → S823.1**. Made by `make_s823.py` from the live bytes, by exact anchors. Added: `net_state()` — one PowerShell call (`Get-NetAdapter`, `Find-NetRoute -RemoteIPAddress 8.8.8.8`, `ConvertTo-Json`), at most every 30 minutes, 25-second limit, no window, any failure becomes one line; the heartbeat (`heartbeat.txt` / `.json`, here and in Drive `FromMedical`) gains, after the DISK line:

```
NETWORK : the internet goes through Wi-Fi 2 (the Wi-Fi dongle)
          Ethernet       cable  Up           100 Mbps
          Wi-Fi 2        Wi-Fi  Up           72.2 Mbps
```

The heartbeat's FIX line now names `INSTALL_AGENT_S823.bat`. Nothing else in the agent changes (the watcher, the kit pickup, the backup leg — byte-identical code).

**The install (the agent never replaces itself, by design):** `install_s823.py` + `INSTALL_AGENT_S823.bat` are S499's proven pair with only names and pins changed (`make_installer_s823.py`): pins, a backup `medical_agent.py.before_d91fa79a`, the guard's own switch `D:\SendToClinic\_off\AGENT_OFF.txt` on and off at once, the new agent's heartbeat waited for, the old file put back if anything is red, a result file in `D:\SendToClinic\` and Drive `FromMedical\S823_INSTALL_RESULT.txt`.

**Delivery:** into Drive `Clinic Data Archive\ToMedical\` (the root): `medical_agent.py` (replacing S499.1 there, kept as `medical_agent_S499_1_RETIRED.py.txt`), `install_s823.py`, `INSTALL_AGENT_S823.bat`. **The one action at the PC:** when nobody is exporting from Marg, double-click `G:\My Drive\Clinic Data Archive\ToMedical\INSTALL_AGENT_S823.bat`, do not touch the black window, wait about two minutes for DONE.

**Undo:** `medical_agent.py.before_d91fa79a` back by the same switch (the installer does it itself on any red).

**Proof:** `walk_s823.py` 23/23 GREEN on S823.1 (b94434dc); on S499.1 RED 1/8 (the control). **Cold review by a second reader: SAFE TO INSTALL, no must-fix** (the diff only as intended; pins and the CRLF/ASCII .bat checked; every failure of the PowerShell call caught; worst case one 25-second pause in 30 minutes). Three of its should-fixes built and walked: a UTF-8 BOM read; PowerShell's `{value:[...]}` wrapping unwrapped; the NETWORK lines can never raise. Left and said so: a phone's USB tethering would read as "cable"; a hung grandchild of PowerShell after a timeout (judged unlikely).
