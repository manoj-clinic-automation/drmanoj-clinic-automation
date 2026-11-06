// browser_walk_s712.js -- kit S712 (session 389). The Add staff page in headless Chromium, its API answered
// by a made-up server (route interception). Proof only -- not run by the installer.
//   node browser_walk_s712.js <staff_easy.html>
const { chromium } = require("playwright");
const fs = require("fs");
const HTML = fs.readFileSync(process.argv[2], "utf8");
const OK = [], RED = [];
const check = (l, c, w) => { (c ? OK : RED).push(l); console.log((c ? "GREEN " : "RED   ") + l + (c ? "" : "  -- " + JSON.stringify(w))); };
const META = { ok: true, people: [], settled: [], jobs: ["Reception", "Clinic", "Cleaner"],
  employment: ["FULLTIME", "PARTTIME"], sunday: null, handover: { whatsapp: "WhatsApp", sms: "SMS", slip: "slip", none: "no phone" }, authorities: {} };
const person = (ref, det) => ({ ok: true, ref, person: "Madeup " + ref, stage: "details", complete: false, job: "Cleaner",
  opened_on: "2026-11-06", code: null, details: det, login: null, steps: {} });
const DET = { department: "Cleaner", employment: "PARTTIME", join_date: "2026-11-01", wd_start: "09:00", wd_end: "10:30",
  base_salary: 3500, allowed_offs: 4, minutes_exempt: 1, handover: "none" };

(async () => {
  const sundayJson = process.argv[3] === "--old"
    ? { A: "1st and 3rd Sunday, full day", B: "2nd and 4th Sunday, full day", C: "Every Sunday, Sunday hours" }
    : { C: "Works every Sunday", OFF: "Sunday off" };
  META.sunday = sundayJson;
  const br = await chromium.launch();
  const ctx = await br.newContext({ viewport: { width: 390, height: 844 } });
  const pg = await ctx.newPage();
  const errs = []; pg.on("pageerror", e => errs.push(String(e)));
  let posted = null;
  await pg.route("**/*", async route => {
    const u = new URL(route.request().url());
    if (u.pathname === "/finance/staff/new") return route.fulfill({ contentType: "text/html", body: HTML });
    if (u.pathname.endsWith("/api/list")) return route.fulfill({ contentType: "application/json", body: JSON.stringify(META) });
    if (u.pathname.endsWith("/api/save")) { posted = JSON.parse(route.request().postData() || "{}");
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, ref: "R1", message: "Saved." }) }); }
    if (u.pathname.endsWith("/api/person")) {
      const ref = u.searchParams.get("ref");
      const det = ref === "OFF" ? Object.assign({}, DET, { sunday_group: "", sun_start: null, sun_end: null })
               : ref === "SUN" ? Object.assign({}, DET, { sunday_group: "C", sun_start: "09:00", sun_end: "10:30" })
               : null;
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(person(ref, det)) }); }
    return route.fulfill({ status: 404, body: "" });
  });
  const base = "https://followup.dr-manoj.in/finance/staff/new";
  // A new joining: the form
  await pg.goto(base); await pg.waitForTimeout(300);
  await pg.evaluate(() => showForm(null)); await pg.waitForTimeout(100);
  const chips = await pg.$$eval('.chips[data-name="sunday"] .chip', cs => cs.map(c => [c.dataset.v, c.textContent, c.classList.contains("on")]));
  check("1 two Sunday choices, 'Works every Sunday' chosen", JSON.stringify(chips) === JSON.stringify([["C", "Works every Sunday", true], ["OFF", "Sunday off", false]]), chips);
  const body = await pg.textContent("#app");
  check("2 no '5th Sunday' line; the offs line is there", !/5th Sunday/.test(body) && /A Sunday he does not come counts as one of his offs\./.test(body), body.slice(0, 300));
  check("3 Sunday hours shown, defaulting to the weekday hours", await pg.isVisible("#f_ss") && await pg.inputValue("#f_ss") === "09:00" && await pg.inputValue("#f_se") === "21:00",
        [await pg.isVisible("#f_ss"), await pg.inputValue("#f_ss"), await pg.inputValue("#f_se")]);
  await pg.fill("#f_ws", "07:30"); await pg.fill("#f_we", "10:30");
  check("4 Sunday hours follow the weekday hours until touched", await pg.inputValue("#f_ss") === "07:30" && await pg.inputValue("#f_se") === "10:30",
        [await pg.inputValue("#f_ss"), await pg.inputValue("#f_se")]);
  await pg.fill("#f_ss", "08:00"); await pg.fill("#f_ws", "06:00");
  check("5 once touched, Sunday's own hour stays", await pg.inputValue("#f_ss") === "08:00", await pg.inputValue("#f_ss"));
  await pg.click('.chips[data-name="sunday"] .chip[data-v="OFF"]').catch(() => {});
  check("6 'Sunday off' hides the Sunday hours and the offs line", !(await pg.isVisible("#f_ss")) && !(await pg.isVisible("text=A Sunday he does not come")), "visible");
  await pg.fill("#f_name", "Madeup Joiner");
  await pg.click('.chips[data-name="phone"] .chip[data-v="none"]');
  await pg.click('.chips[data-name="job"] .chip[data-v="Cleaner"]');
  await pg.click("#saveBtn"); await pg.waitForTimeout(300);
  check("7 the save sends sunday_group OFF", posted && posted.sunday_group === "OFF", posted);
  // Saved people
  await pg.goto(base + "?ref=OFF"); await pg.waitForTimeout(400);
  let t = await pg.textContent("#app");
  check("8 a saved 'Sunday off' reads 'Sunday: off'", /Sunday: off ·/.test(t), t.slice(0, 400));
  await pg.evaluate(() => showForm(CUR)); await pg.waitForTimeout(100);
  const on1 = await pg.$eval('.chips[data-name="sunday"] .chip.on', c => c.dataset.v).catch(() => null);
  check("9 'Change' on him opens with 'Sunday off' chosen", on1 === "OFF", on1);
  await pg.goto(base + "?ref=SUN"); await pg.waitForTimeout(400);
  t = await pg.textContent("#app");
  check("10 a saved 'works Sundays' reads 'every Sunday (09:00–10:30)'", /Sunday: every Sunday \(09:00–10:30\)/.test(t), t.slice(0, 400));
  await pg.evaluate(() => showForm(CUR)); await pg.waitForTimeout(100);
  const on2 = await pg.$eval('.chips[data-name="sunday"] .chip.on', c => c.dataset.v).catch(() => null);
  check("11 'Change' on him opens with 'Works every Sunday' and his hours", on2 === "C" && await pg.inputValue("#f_ss") === "09:00" && await pg.inputValue("#f_se") === "10:30", on2);
  const sw = await pg.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
  check("12 no sideways scroll at phone width (390 px)", sw, "scrolls");
  check("13 no script error", errs.length === 0, errs);
  await br.close();
  const n = OK.length + RED.length;
  console.log(RED.length ? RED.length + " S712 check(s) red . " + OK.length + " green" : n + " of " + n + " green");
})();
