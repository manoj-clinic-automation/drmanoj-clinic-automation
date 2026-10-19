# S595_WA_MEDIA_SEND_PROBE — can the clinic number send a photo, a PDF and a voice note? (D744, step 1)

**The owner, 19-Oct 01:56–06:10 IST:** an owner-only WhatsApp Inbox in the portal that replies with text, photos, PDFs and voice notes
(*"send photo and pdf back from beginning, so that the build is completed once only"*). The server has only ever sent text and templates
through MyOperator; this kit proves the three media types once, on the owner's own phone, before the inbox is built.

**First:** send any message (e.g. *hi*) from your phone to the clinic WhatsApp number — WhatsApp only lets a business send a photo, PDF
or voice note within 24 hours of the person's last message.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S595_WA_MEDIA_SEND_PROBE/install_S595_WA_MEDIA_SEND_PROBE.sh

**What it does:** reads your own number (`WA_TEST_NUMBER`, the approval page's test-mode number) and the live sender's settings the way
the running sender reads them; checks the 24-hour window with the live sender's own check; puts four made-up test files (a photo, a
one-page PDF, a 3-second tone as an OGG voice note and as an MP3) in a random-named folder of the website, checks each opens from the
internet, schedules the folder's removal after 30 minutes; sends photo, PDF, voice note — each in the text messages' shape first
(`data.context`), the flat shape (`data.*`) only if refused; the voice note falls back to MP3. Writes `/root/finance/s595_probe.json`
(no number, no token). Prints only the last 4 digits of any number. **Nothing live changes.**

**Proof (rule 35):** what arrives on your phone — a photo, a PDF, a voice note from the clinic number.

**Rehearsed offline (S329):** DRY · window closed → stop, nothing written · a test file not opening → stop, folder removed ·
a refused shape → the other shape · OGG refused → MP3 · no scheduler → folder removed at the end · refusal text with a number → masked.
