"""
att_mailer.py  —  builds and sends the attendance email (shift-aware).

Run by cron:
    morning check (11:30) :  python3 /root/att_mailer.py morning
    day summary  (21:00)  :  python3 /root/att_mailer.py evening

If SMTP_PASS is blank in att_config.py, the email is written to a file instead
of sent, so you can preview it safely.  Manual test (ignores Sunday skip):
    python3 /root/att_mailer.py evening test
"""
import sys
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
import att_config as cfg
import att_core as core

WRAP = "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#1d2733;"


def hm(dt):
    return dt.strftime("%H:%M")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(mode, d, data):
    day = d.strftime("%A, %d %b %Y")
    sun = " &middot; Sunday (reduced hours)" if data["is_sunday"] else ""
    absent_lbl = "OFF / NOT IN" if data["is_sunday"] else ("NOT IN YET" if mode == "morning" else "ABSENT")
    head = (f'<div style="background:#1f4e79;color:#fff;padding:14px 18px;border-radius:10px">'
            f'<div style="font-size:18px;font-weight:700">Clinic Attendance</div>'
            f'<div style="opacity:.85">'
            f'{"Morning check" if mode == "morning" else "Day summary"} &middot; {day}{sun}</div></div>')
    cards = (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;margin:14px 0"><tr>'
        f'<td style="text-align:center"><div style="font-size:24px;font-weight:800;color:#1a8a4a">'
        f'{data["present_count"]}</div><div style="font-size:12px;color:#6b7785">PRESENT</div></td>'
        f'<td style="text-align:center"><div style="font-size:24px;font-weight:800;color:#c0392b">'
        f'{data["absent_count"]}</div><div style="font-size:12px;color:#6b7785">{absent_lbl}</div></td>'
        f'<td style="text-align:center"><div style="font-size:24px;font-weight:800;color:#c77f00">'
        f'{data["late_count"]}</div><div style="font-size:12px;color:#6b7785">LATE</div></td></tr></table>')

    def late_tag(r):
        return f' <b style="color:#9a4b00">(late {r["late_min"]}m)</b>' if r["late"] else ""

    if mode == "morning":
        subject = (f"Attendance — morning check ({d.strftime('%d %b')}): "
                   f"{data['present_count']} in, {data['absent_count']} not yet")
        rows = ""
        for r in data["present"]:
            rows += (f'<tr><td style="padding:6px 0">{esc(r["name"])}{late_tag(r)}</td>'
                     f'<td style="padding:6px 0;text-align:right"><b>{hm(r["first"])}</b></td></tr>')
        names = ", ".join(esc(r["name"]) for r in data["absent"]) or "None"
        inner = (f'<h3 style="color:#6b7785;font-size:13px">IN SO FAR ({data["present_count"]})</h3>'
                 f'<table style="width:100%">{rows or "<tr><td>None yet</td></tr>"}</table><br>'
                 f'<h3 style="color:#6b7785;font-size:13px">{absent_lbl} ({data["absent_count"]})</h3>'
                 f'<div>{names}</div>')
    else:
        subject = (f"Attendance — day summary ({d.strftime('%d %b')}): "
                   f"{data['present_count']} present, {data['absent_count']} absent")
        rows = ('<tr style="color:#6b7785;font-size:12px;text-align:left">'
                '<th style="padding:4px 0">Name</th><th>In</th><th>Out/Last</th>'
                '<th style="text-align:right">Hours</th></tr>')
        for r in data["present"]:
            out = hm(r["last"]) if r["n"] >= 2 else "&mdash;"
            hrs = r["hours"] if r["hours"] is not None else "&mdash;"
            early = ' <b style="color:#8a6400">(early)</b>' if r["early"] else ""
            rows += (f'<tr><td style="padding:5px 0;border-top:1px solid #eee">'
                     f'{esc(r["name"])}{late_tag(r)}{early}</td>'
                     f'<td style="border-top:1px solid #eee">{hm(r["first"])}</td>'
                     f'<td style="border-top:1px solid #eee">{out}</td>'
                     f'<td style="border-top:1px solid #eee;text-align:right">{hrs}</td></tr>')
        names = ", ".join(esc(r["name"]) for r in data["absent"]) or "None"
        inner = (f'<h3 style="color:#6b7785;font-size:13px">PRESENT ({data["present_count"]})</h3>'
                 f'<table style="width:100%">{rows}</table><br>'
                 f'<h3 style="color:#6b7785;font-size:13px">{absent_lbl} ({data["absent_count"]})</h3>'
                 f'<div style="color:#c0392b">{names}</div>')

    note = ('<div style="color:#9aa4af;font-size:11px;margin-top:18px">'
            'Late/early are judged against each person\u2019s own shift (Sunday timings on Sundays). '
            'Hours show only when both an arrival and a departure were punched. '
            'Generated automatically on the clinic server.</div>')
    return subject, f'<div style="{WRAP}max-width:640px">{head}{cards}{inner}{note}</div>'


def send(subject, html):
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = cfg.EMAIL_FROM
    msg["To"] = ", ".join(cfg.EMAIL_TO)
    ctx = ssl.create_default_context()
    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=30) as s:
        s.starttls(context=ctx)
        s.login(cfg.SMTP_USER, cfg.SMTP_PASS)
        s.sendmail(cfg.EMAIL_FROM, cfg.EMAIL_TO, msg.as_string())


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "evening"
    test = len(sys.argv) > 2 and sys.argv[2] == "test"
    if mode not in ("morning", "evening"):
        print("Usage: att_mailer.py morning|evening [test]")
        return
    d = datetime.date.today()
    if d.weekday() == 6 and not cfg.SEND_ON_SUNDAY and not test:
        print(f"[{datetime.datetime.now()}] Sunday — skipping {mode} email.")
        return
    data = core.compute_day(d)
    subject, html = build(mode, d, data)
    if not cfg.SMTP_PASS:
        path = f"/root/att_email_{mode}_{d}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[{datetime.datetime.now()}] SMTP not configured — wrote preview to {path}")
        return
    send(subject, html)
    print(f"[{datetime.datetime.now()}] Sent {mode} email to {', '.join(cfg.EMAIL_TO)}")


if __name__ == "__main__":
    main()
