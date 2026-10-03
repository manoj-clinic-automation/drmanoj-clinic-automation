# S291 BUILD BRIEF — 03-Oct-2026 (the parent)

Session 291, one morning (04:33 → 08:2x IST). One kit, a reader (S455). Numbers from `board/_numbers` (v186 → v203).

## What you asked for today, and where each stands
| what you asked | where it stands |
|---|---|
| The jobs still owed on the reception PC — "go and do 1 to 6, also 7 and 8" | **Done, with nobody at that desk.** The last test of its setup passed; the Claude app is removed from it; the firewall step is now part of the one-click reinstall on your *Clinic PCs* tile; the leftovers are cleared. |
| The server from your phone's hotspot — "why not complete it" | **Done.** The server needed no change. You added one record at GoDaddy; the reception PC now reaches the server on that kind of connection. To undo it, delete that one record. |
| "The doctor's report for yesterday has not landed" | **02-Oct is on your portal** (33 bills). The cause stands — see *What needs you*, item 2. |
| The reception PC and the clinic Wi-Fi | **Solved.** Its 2016 Wi-Fi driver could not see your Wi-Fi 6 network at all. After the Intel driver you installed, it is on `Airtel_Airtrl_mano_8080`. My first two readings of this fault were wrong; your screenshot of the Wi-Fi name settled it. |
| The LAN cable to the reception PC | **Still no link.** Pushing the plug changed nothing: try a different cable or wall socket. If a known-good cable shows nothing, it is the PC's own socket — the vendor's. Not urgent now that Wi-Fi works. |
| Windows on the reception PC | It has had no Windows security fixes since November 2025 and cannot run Windows 11. "Enroll now" is worth one try after clinic hours; the lasting answer is a new PC for reception, which your *Clinic PCs* tile makes a short setup. |

## What needs you
1. **One double-click — the publish.** It carries only this record; no server line follows.
2. **One word — yes or no:** shall your PC pick up reception's Docterz reports from the clinic Drive by itself? Until then, on any morning the previous day is missing from your portal, this one line on your PC brings it in within 15 minutes:

```
cmd /c copy /y "H:\My Drive\Clinic Records\Docterz exports\*.csv" "D:\Downloads\"
```

## Read and parked at your word
Your ruling on papers scanned at reception that are not pharmacy purchases (clinic consumables and its sub-groups, one PDF per purchase, the *Dr MK expense* lane, the battery's warranty). Next: a short plan and a mock — no build until you say.

## Waiting on your word (you said "later")
The follow-up tracker on the server · the contacts workbook · the mail flood · the portal tiles.
