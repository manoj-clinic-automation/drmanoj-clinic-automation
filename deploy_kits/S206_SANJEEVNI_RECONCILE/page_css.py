# Clinic Design Language v1 :root -- copied verbatim per the owner's S187 directive.
# Precedence: the project's existing system wins over any palette I would pick.
CSS = """
:root{
  --surface-page:#f3f2ee; --surface-1:#fbfaf8; --surface-2:#f5f4f0; --line:#e6e3dc;
  --text-1:#23272f; --text-2:#5d6470; --text-3:#8a8f99;
  --accent:#2a78d6; --accent-ink:#1c5cab;
  --good:#0ca30c; --good-bg:#e9f6e9; --warn:#8a6100; --warn-bg:#fdf3d7;
  --bad:#b02a2a; --bad-bg:#fbeaea; --shadow:0 1px 3px rgba(35,39,47,.06); --hdr:104px;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --surface-page:#191816; --surface-1:#211f1c; --surface-2:#262320; --line:#37332d;
  --text-1:#eceae5; --text-2:#b0aaa1; --text-3:#867f75;
  --accent:#6ea8e8; --accent-ink:#8dbcf0;
  --good:#5fc45f; --good-bg:#1b2c1b; --warn:#e0ae4e; --warn-bg:#2e2616;
  --bad:#e8837c; --bad-bg:#301d1c; --shadow:0 1px 3px rgba(0,0,0,.4);
}}
:root[data-theme="dark"]{
  --surface-page:#191816; --surface-1:#211f1c; --surface-2:#262320; --line:#37332d;
  --text-1:#eceae5; --text-2:#b0aaa1; --text-3:#867f75;
  --accent:#6ea8e8; --accent-ink:#8dbcf0;
  --good:#5fc45f; --good-bg:#1b2c1b; --warn:#e0ae4e; --warn-bg:#2e2616;
  --bad:#e8837c; --bad-bg:#301d1c; --shadow:0 1px 3px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
html{scroll-padding-top:var(--hdr);scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
body{margin:0;background:var(--surface-page);color:var(--text-1);
 font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.num{font-variant-numeric:tabular-nums;text-align:right}
b,strong{font-weight:600}
header.brand{position:sticky;top:0;z-index:40;background:var(--surface-page);border-bottom:1px solid var(--line)}
.brow{display:flex;align-items:center;gap:12px;padding:10px 16px 8px;max-width:1600px;margin:0 auto}
.mark{width:38px;height:38px;flex:none;border-radius:9px;background:var(--accent);display:grid;
 place-items:center;color:#fff;font-weight:700;font-size:15px;letter-spacing:-.5px}
.bt h1{margin:0;font-size:16px;font-weight:600;letter-spacing:-.2px}
.bt p{margin:0;font-size:12px;color:var(--text-3)}
.tabs{display:flex;gap:4px;overflow-x:auto;padding:0 16px 8px;max-width:1600px;margin:0 auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs button{flex:none;font:500 13px inherit;color:var(--text-2);background:none;border:0;cursor:pointer;
 padding:7px 12px;border-radius:8px;white-space:nowrap}
.tabs button:hover{background:var(--surface-2);color:var(--accent-ink)}
.tabs button[aria-selected="true"]{background:var(--accent);color:#fff}
.tabs button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
main{max-width:1600px;margin:0 auto;padding:16px 16px 90px}
.panel[hidden]{display:none}
.card{background:var(--surface-1);border:1px solid var(--line);border-radius:12px;padding:18px;
 box-shadow:var(--shadow);margin:0 0 14px}
.kicker{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin:0 0 3px}
.card h2{margin:0 0 4px;font-size:16px;font-weight:600}
.sub{margin:0 0 14px;font-size:13px;color:var(--text-2);max-width:68ch}
/* the identity, as an equation you can read left to right */
.eq{display:flex;flex-wrap:wrap;align-items:stretch;gap:8px}
.term{flex:1 1 130px;background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:11px 12px}
.term .l{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3)}
.term .v{display:block;font-size:19px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:3px}
.term .u{display:block;font-size:11.5px;color:var(--text-3)}
.op{align-self:center;font-size:19px;color:var(--text-3);font-weight:600;flex:none}
.term.res{background:var(--good-bg);border-color:var(--good)}
.term.res .v{color:var(--good)}
.chips{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:8px;margin:0 0 14px}
.chip{background:var(--surface-1);border:1px solid var(--line);border-radius:12px;padding:12px 13px;
 box-shadow:var(--shadow);text-align:left;font:inherit;color:inherit;cursor:pointer;width:100%}
.chip:hover{border-color:var(--accent)}
.chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.chip[aria-pressed="true"]{border-color:var(--accent);background:var(--surface-2)}
.chip .v{display:block;font-size:23px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.15}
.chip .l{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-top:3px}
.chip .w{display:block;font-size:11.5px;color:var(--text-2);margin-top:5px;line-height:1.35}
.tools{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap;align-items:center}
#q{flex:1 1 240px;min-width:150px;font:15px/1.4 inherit;padding:10px 12px;min-height:42px;
 border:1px solid var(--line);border-radius:10px;background:var(--surface-1);color:var(--text-1)}
#q:focus{outline:2px solid var(--accent);outline-offset:1px}
.hits{font-size:12.5px;color:var(--text-3)}
.tblwrap{overflow:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface-1);max-height:70vh}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:640px}
thead th{position:sticky;top:0;background:var(--surface-2);z-index:1;font-size:10.5px;text-transform:uppercase;
 letter-spacing:.05em;color:var(--text-3);font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
thead th.num{text-align:right}
tbody td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr.item{cursor:pointer}
tbody tr.item:hover{background:var(--surface-2)}
tbody tr.det td{background:var(--surface-2);font-size:12.5px;color:var(--text-2)}
.badge{display:inline-block;font-size:10.5px;font-weight:600;padding:1px 7px;border-radius:20px;white-space:nowrap}
.b-bad{background:var(--bad-bg);color:var(--bad)} .b-warn{background:var(--warn-bg);color:var(--warn)}
.b-good{background:var(--good-bg);color:var(--good)} .b-mut{background:var(--surface-2);color:var(--text-3)}
.mono{font-variant-numeric:tabular-nums}
.mgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:7px;margin-top:7px}
.mo{background:var(--surface-1);border:1px solid var(--line);border-radius:8px;padding:7px 9px}
.mo .m{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3)}
.mo .r{font-size:12.5px;font-variant-numeric:tabular-nums}
.vend{margin:0 0 10px}
.vend h3{margin:0 0 2px;font-size:14px;font-weight:600}
.vend .meta{font-size:12px;color:var(--text-3);margin-bottom:6px}
details.note{margin-top:10px;border-top:1px solid var(--line);padding-top:9px}
details.note summary{cursor:pointer;font-size:12.5px;color:var(--accent-ink);list-style:none}
details.note summary::-webkit-details-marker{display:none}
details.note summary::before{content:"\\2192  "}
details.note[open] summary::before{content:"\\2193  "}
details.note p{font-size:12.5px;color:var(--text-2);margin:8px 0 0;max-width:72ch}
.foot{font-size:12px;color:var(--text-3);margin-top:18px;max-width:72ch}
@media(max-width:640px){ .brow{padding:8px 12px 6px} main{padding:12px 12px 80px} .card{padding:14px} }
"""
