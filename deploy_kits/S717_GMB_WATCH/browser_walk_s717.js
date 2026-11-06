// browser_walk_s717.js -- kit S717_GMB_WATCH (session 389). The GMB page's new section in headless Chromium, served over
// http, its /portal/gmb/api/* answered by a made-up server. Proof only -- not run by the installer.
//   node browser_walk_s717.js <http url of the page> <seed_s717.txt>
const { chromium } = require("playwright");
const fs = require("fs");
const SEED = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const OK = [], RED = [];
const check = (l, c, w) => { (c ? OK : RED).push(l); console.log((c ? "GREEN " : "RED   ") + l + (c ? "" : "  -- " + JSON.stringify(w).slice(0, 300))); };
const LIST = SEED.data.sources.filter(x => x !== "Our own listing");
(async () => {
  const br = await chromium.launch();
  for (const vp of [{ width: 1366, height: 900, tag: "PC" }, { width: 390, height: 844, tag: "phone" }]) {
    const t = vp.tag + ": ";
    // A -- only the 5-Nov reading
    let ctx = await br.newContext({ viewport: { width: vp.width, height: vp.height } });
    let pg = await ctx.newPage(); let errs = []; pg.on("pageerror", e => errs.push(String(e)));
    let list = LIST.slice(), added = [], mode = "one";
    await pg.route("**/portal/gmb/api/**", async route => {
      const rq = route.request(), u = new URL(rq.url());
      if (mode === "down") return route.fulfill({ status: 503, body: "" });
      if (u.pathname.endsWith("/watch") && rq.method() === "GET") {
        const prev = JSON.parse(JSON.stringify(SEED)); prev.taken_on = "2026-10-22"; prev.data.themes[0].ours = 7.4; prev.data.themes[1].ours = 3.9;
        return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, latest: SEED, previous: mode === "two" ? prev : null, listings: list }) });
      }
      if (u.pathname.endsWith("/watch") && rq.method() === "POST") {
        const b = JSON.parse(rq.postData() || "{}"); added.push({ b, hdr: rq.headers()["x-gmb"] }); list.push(b.name);
        return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, listings: list }) });
      }
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, id: 1, edited: false }) });
    });
    await pg.goto(process.argv[2]); await pg.waitForTimeout(500);
    check(t + "1 the section shows under the drafts", await pg.isVisible("#ws"), "hidden");
    const when = await pg.textContent("#ws-when");
    check(t + "2 it says the reading's date and when the next is due", when.startsWith("Reading of 5 Nov 2026 · the next one is due 19 Nov"), when);
    const rows = await pg.$$eval("#ws-ours .wrow", r => r.map(x => [x.querySelector(".wlab").textContent, x.querySelector(".wpct").textContent]));
    check(t + "3 our complaints, as a percent of our reviewers, largest first (a 0 is left out)",
      JSON.stringify(rows) === JSON.stringify([["Staff tone", "6.6%"], ["X-ray and test charges", "4.8%"], ["Bills and fees", "4.2%"], ["Waiting", "3.0%"], ["Treatment did not work", "1.2%"]]), rows);
    check(t + "4 'of our 167 reviewers'", (await pg.textContent("#ws-n")).includes("our 167 reviewers"), await pg.textContent("#ws-n"));
    const sum = await pg.textContent("#ws-sum");
    check(t + "5 the summary line", sum === "9.0% of our reviewers left a 1★ or 2★ review. Staff tone is mentioned most (6.6%), then x-ray and test charges (4.8%).", sum);
    check(t + "6 with one reading the trend says it starts next time", (await pg.$$eval("#ws-ours .wtr", x => x.every(e => e.textContent === "trend from the next reading"))), "");
    const ah = await pg.$$eval("#ws-ahead .wrow2", r => r.map(x => x.querySelector(".wlab").textContent));
    check(t + "7 to stay ahead of: only where elsewhere is higher (staff tone, then bills)", JSON.stringify(ah) === JSON.stringify(["Staff tone", "Bills and fees"]), ah);
    check(t + "8 the 16 words as chips", (await pg.$$("#ws-words .wchip")).length === 16, "");
    const src = await pg.textContent("#ws-src");
    check(t + "9 'Read from' starts with our own listing and names the five", src === "Our own listing · " + LIST.join(" · "), src);
    const body = await pg.textContent("#ws");
    check(t + "10 no star average, no review count of another listing, no word 'fake'", !/average|★ \d|fake|authentic/i.test(body.replace("1★ or 2★", "")), "");
    await pg.fill("#ws-in", "Dr Test Listing"); await pg.click(".wadd button"); await pg.waitForTimeout(250);
    check(t + "11 adding a listing sends it with the page's header and shows it at once",
      added.length === 1 && added[0].b.name === "Dr Test Listing" && added[0].hdr === "1" && (await pg.textContent("#ws-src")).endsWith("Dr Test Listing")
      && (await pg.textContent("#ws-msg")) === "Added — it is read from the next reading.", [added, await pg.textContent("#ws-msg")]);
    const sw = await pg.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
    check(t + "12 no sideways scroll", sw, "scrolls");
    check(t + "13 no script error", errs.length === 0, errs);
    await ctx.close();
    // B -- two readings: the trend
    ctx = await br.newContext({ viewport: { width: vp.width, height: vp.height } }); pg = await ctx.newPage(); errs = []; pg.on("pageerror", e => errs.push(String(e)));
    mode = "two";
    await pg.route("**/portal/gmb/api/**", async route => {
      const prev = JSON.parse(JSON.stringify(SEED)); prev.taken_on = "2026-10-22"; prev.data.themes[0].ours = 7.4; prev.data.themes[1].ours = 3.9; prev.data.themes[5].ours = 2.0;
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, latest: SEED, previous: prev, listings: LIST }) });
    });
    await pg.goto(process.argv[2]); await pg.waitForTimeout(500);
    const tr = await pg.$$eval("#ws-ours .wtr", x => x.map(e => [e.textContent, e.className]));
    check(t + "14 with two readings: staff tone down 0.8 (green), x-ray up 0.9 (red), the rest the same",
      tr[0][0] === "▼ down 0.8 since 22 Oct 2026" && tr[0][1].includes("dn") && tr[1][0] === "▲ up 0.9 since 22 Oct 2026" && tr[1][1].includes("up") && tr[2][0] === "same as 22 Oct 2026", tr);
    const gone = await pg.$$eval("#ws-ours .wrow", r => r.map(x => [x.querySelector(".wlab").textContent, x.querySelector(".wtr").textContent]).find(x => x[0] === "Doctor did not listen"));
    check(t + "14b a complaint that fell to 0 stays on the list, showing the fall", gone && gone[1] === "▼ down 2.0 since 22 Oct 2026", gone);
    check(t + "15 no script error", errs.length === 0, errs);
    await ctx.close();
    // C -- the server down / no reading: the section stays hidden, the page works
    ctx = await br.newContext({ viewport: { width: vp.width, height: vp.height } }); pg = await ctx.newPage(); errs = []; pg.on("pageerror", e => errs.push(String(e)));
    await pg.route("**/portal/gmb/api/**", r => r.fulfill({ status: 503, body: "" }));
    await pg.goto(process.argv[2]); await pg.waitForTimeout(500);
    check(t + "16 with the server down the section stays hidden", !(await pg.isVisible("#ws")), "visible");
    await pg.click('#pgrid .ptb[data-id="knee"]'); await pg.click('#ggrid .gptb[data-id="pain"]'); await pg.click("#genbtn"); await pg.waitForTimeout(300);
    check(t + "17 ...and Generate still makes three drafts", (await pg.$$(".rev-ta")).length === 3, "");
    check(t + "18 no script error", errs.length === 0, errs);
    await ctx.close();
  }
  await br.close();
  const n = OK.length + RED.length;
  console.log(RED.length ? RED.length + " S717 check(s) red . " + OK.length + " green" : n + " of " + n + " green");
})();
