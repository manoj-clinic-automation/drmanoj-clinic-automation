// browser_walk_s713.js -- kit S713_GMB_SAVE (session 389). The GMB page in headless Chromium served from a made-up
// origin, its /portal/gmb/api/* answered by a made-up server (route interception). Proof only -- not run by the installer.
//   node browser_walk_s713.js <http url of the page>        (the page must be served over http, as the portal serves it)
const { chromium } = require("playwright");
const OK = [], RED = [];
const check = (l, c, w) => { (c ? OK : RED).push(l); console.log((c ? "GREEN " : "RED   ") + l + (c ? "" : "  -- " + JSON.stringify(w).slice(0, 300))); };
(async () => {
  const br = await chromium.launch();
  for (const vp of [{ width: 1366, height: 900, tag: "PC" }, { width: 390, height: 844, tag: "phone" }]) {
    const ctx = await br.newContext({ viewport: { width: vp.width, height: vp.height } });
    const pg = await ctx.newPage();
    const errs = []; pg.on("pageerror", e => errs.push(String(e)));
    let presses = [], shares = [], down = false, nextId = 41, slow = 0;
    await pg.route("**/portal/gmb/api/**", async route => {
      const rq = route.request(), u = new URL(rq.url());
      const hdr = rq.headers()["x-gmb"];
      if (down) return route.fulfill({ status: 503, body: "" });
      const b = JSON.parse(rq.postData() || "{}");
      if (u.pathname.endsWith("/press")) { presses.push({ b, hdr }); if (slow) await new Promise(r => setTimeout(r, slow)); return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, id: nextId++ }) }); }
      if (u.pathname.endsWith("/share")) {
        shares.push({ b, hdr });
        const p = presses.find((x, k) => 41 + k === b.id);
        const orig = p ? p.b.drafts[b.which] : null;
        return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, edited: (b.text || "").trim() !== (orig || "").trim() }) });
      }
      return route.fulfill({ status: 404, body: "" });
    });
    await pg.addInitScript(() => { window.open = () => null; });
    await pg.goto(process.argv[2]);
    await pg.click('.lb[data-l="Hindi"]'); await pg.click('.rb[data-r="mother"]');
    await pg.click('#pgrid .ptb[data-id="knee"]'); await pg.click('#ggrid .gptb[data-id="pain"]');
    await pg.click("#genbtn"); await pg.waitForTimeout(400);
    const t = vp.tag + ": ";
    const tas = await pg.$$eval(".rev-ta", x => x.map(e => e.value));
    check(t + "1 one press kept on Generate, with the page's own header", presses.length === 1 && presses[0].hdr === "1", presses.length);
    check(t + "2 it carries the three drafts exactly as shown", presses.length === 1 && JSON.stringify(presses[0].b.drafts) === JSON.stringify(tas), [presses[0] && presses[0].b.drafts, tas]);
    check(t + "3 it carries the ticks: Hindi, mother, knee, pain", presses.length === 1 && presses[0].b.state.language === "Hindi" && presses[0].b.state.relation === "mother"
      && JSON.stringify(presses[0].b.state.problems) === '["knee"]' && presses[0].b.state.good.includes("pain"), presses[0] && presses[0].b.state);
    check(t + "4 the page says 'Kept on the server.'", (await pg.textContent("#keepst")) === "Kept on the server.", await pg.textContent("#keepst"));
    check(t + "5 each draft has Copy, WhatsApp and Shared", (await pg.$$(".cpbtn")).length === 3 && (await pg.$$(".wabtn")).length === 3 && (await pg.$$(".shbtn")).length === 3, "");
    await pg.click("#cb0"); await pg.waitForTimeout(200);
    check(t + "6 Copy keeps the text as copied (draft 0, not edited)", shares.length === 1 && shares[0].b.how === "copied" && shares[0].b.which === 0 && shares[0].b.id === 41 && shares[0].b.text === tas[0], shares);
    await pg.fill("#rt2", tas[2] + " Sir ka dhanyavaad."); await pg.click("#sb2"); await pg.waitForTimeout(250);
    check(t + "7 Shared after an edit keeps the edited text, and says so", shares.length === 2 && shares[1].b.how === "shared" && shares[1].b.which === 2
      && shares[1].b.text.endsWith("Sir ka dhanyavaad.") && (await pg.textContent("#sb2")) === "✓ Noted, with your edit", [shares[1], await pg.textContent("#sb2")]);
    await pg.click("#sb1"); await pg.waitForTimeout(250);
    check(t + "8 Shared on an unedited draft says '✓ Noted'", (await pg.textContent("#sb1")) === "✓ Noted", await pg.textContent("#sb1"));
    await pg.click(".wabtn >> nth=1"); await pg.waitForTimeout(200);
    check(t + "9 WhatsApp keeps the text as sent by WhatsApp", shares.length === 4 && shares[3].b.how === "whatsapp" && shares[3].b.which === 1, shares.length);
    await pg.click(".regen-btn"); await pg.waitForTimeout(300);
    await pg.click("#cb1"); await pg.waitForTimeout(200);
    check(t + "10 Fresh variation is a new press, and a copy after it points at the new one", presses.length === 2 && shares[4] && shares[4].b.id === 42, [presses.length, shares[4]]);
    slow = 800; await pg.click(".regen-btn"); await pg.click("#cb2"); await pg.waitForTimeout(1300); slow = 0;
    check(t + "10b a Copy pressed before the server answers waits for the press and is kept with its id", shares.length === 6 && shares[5].b.id === 43 && shares[5].b.which === 2, [shares.length, shares[5]]);
    down = true;
    await pg.click(".regen-btn"); await pg.waitForTimeout(300);
    check(t + "11 with the server down the page says so plainly", (await pg.textContent("#keepst")) === "Not kept this time — Copy and WhatsApp still work.", await pg.textContent("#keepst"));
    await pg.click("#cb0"); await pg.waitForTimeout(100);
    check(t + "12 ...and Copy still works", (await pg.textContent("#cb0")) === "✓ Copied!", await pg.textContent("#cb0"));
    await pg.click("#sb0"); await pg.waitForTimeout(250);
    check(t + "13 ...and Shared says 'Not noted' instead of pretending", (await pg.textContent("#sb0")) === "Not noted", await pg.textContent("#sb0"));
    const sw = await pg.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
    check(t + "14 no sideways scroll", sw, "scrolls");
    check(t + "15 no script error", errs.length === 0, errs);
    await ctx.close();
  }
  await br.close();
  const n = OK.length + RED.length;
  console.log(RED.length ? RED.length + " S713 check(s) red . " + OK.length + " green" : n + " of " + n + " green");
})();
