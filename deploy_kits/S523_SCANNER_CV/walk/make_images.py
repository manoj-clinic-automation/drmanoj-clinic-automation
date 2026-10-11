#!/usr/bin/env python3
"""Made-up bill photos for the S523 walk: a printed half-A4 'bill' laid on a cluttered desk, photographed at 8 MP,
with the paper's four corners KNOWN. No real paper, no person, no number of anyone's. Writes <out>/<name>.jpg and
<out>/truth.json ({name: {"w","h","quad":[[x,y]x4] TL,TR,BR,BL}}). Also a y4m clip for Chromium's fake camera."""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter

random.seed(523)
OUT = sys.argv[1] if len(sys.argv) > 1 else "images"
os.makedirs(OUT, exist_ok=True)
W, H = 3264, 2448


def desk(kind):
    base = {"wood": (120, 84, 50), "grey": (150, 152, 158), "light": (214, 210, 200), "black": (30, 30, 34)}[kind]
    im = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(im)
    # grain and clutter: a keyboard, a phone, a pen, a cable
    for _ in range(4000):
        x, y = random.randrange(W), random.randrange(H)
        c = tuple(max(0, min(255, v + random.randint(-18, 18))) for v in base)
        d.rectangle([x, y, x + random.randint(2, 40), y + random.randint(1, 3)], fill=c)
    d.rectangle([40, H - 520, 1500, H - 60], fill=(40, 40, 44))                      # keyboard
    for r in range(4):
        for k in range(24):
            d.rectangle([70 + k * 58, H - 500 + r * 110, 70 + k * 58 + 46, H - 500 + r * 110 + 90], fill=(70, 70, 76))
    d.rounded_rectangle([W - 520, 80, W - 120, 900], radius=60, fill=(18, 18, 20))   # a phone
    d.rounded_rectangle([W - 500, 110, W - 140, 870], radius=40, fill=(60, 90, 140))
    d.line([(200, 200), (1400, 420)], fill=(20, 20, 20), width=14)                   # a pen
    d.line([(W - 900, H - 200), (W - 300, H - 900)], fill=(230, 230, 230), width=8)  # a cable
    return im


def paper(pw, ph):
    p = Image.new("RGB", (pw, ph), (252, 251, 246))
    d = ImageDraw.Draw(p)
    d.rectangle([pw * 0.08, ph * 0.05, pw * 0.92, ph * 0.11], fill=(20, 20, 20))     # a header band
    y = ph * 0.16
    while y < ph * 0.9:
        x = pw * 0.08
        while x < pw * 0.9:
            wlen = random.randint(40, 160)
            d.rectangle([x, y, min(pw * 0.92, x + wlen), y + ph * 0.012], fill=(30, 30, 30))
            x += wlen + random.randint(20, 60)
        y += ph * 0.028
    d.rectangle([pw * 0.08, ph * 0.5, pw * 0.92, ph * 0.5 + 3], fill=(0, 0, 0))     # a rule across
    d.rectangle([pw * 0.6, ph * 0.86, pw * 0.92, ph * 0.9], fill=(10, 10, 10))      # a total box
    return p


def place(im, p, quad):
    """Paste the paper with its corners at quad (TL,TR,BR,BL) by an inverse perspective transform."""
    pw, ph = p.size
    # PIL's QUAD transform maps the OUTPUT box to a source quad; we want the reverse, so compute the 8 coefficients.
    def coeffs(src, dst):
        import numpy as np
        A = []
        for (x, y), (u, v) in zip(dst, src):
            A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        B = np.array([c for pt in src for c in pt], dtype=float)
        return tuple(np.linalg.solve(np.array(A, dtype=float), B))
    src = [(0, 0), (pw, 0), (pw, ph), (0, ph)]
    c = coeffs(src, quad)
    warped = p.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
    mask = Image.new("L", (pw, ph), 255).transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
    # a soft shadow under the paper, as a phone photo has
    sh = mask.filter(ImageFilter.GaussianBlur(30))
    shadow = Image.new("RGB", (W, H), (0, 0, 0))
    im = Image.composite(im, Image.blend(im, shadow, 0.35), ImageChops_invert(sh))
    im.paste(warped, (0, 0), mask)
    return im


def ImageChops_invert(m):
    from PIL import ImageChops
    return ImageChops.invert(m)


def rot(pts, deg, cx, cy):
    a = math.radians(deg)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


cases = {}
pw, ph = 1250, 1770                                                              # half A4, ~0.706
def rect(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]

cases["straight_wood"] = ("wood", rect(W / 2, H / 2, pw, ph))
cases["tilted12_wood"] = ("wood", rot(rect(W / 2, H / 2, pw, ph), 12, W / 2, H / 2))
q = rect(W / 2, H / 2, pw, ph); cases["perspective_grey"] = ("grey", [(q[0][0] + 140, q[0][1] + 60), (q[1][0] - 90, q[1][1] + 30), (q[2][0] + 60, q[2][1]), (q[3][0] - 110, q[3][1] + 10)])
cases["near_edge_black"] = ("black", rect(W - pw / 2 - 60, H / 2 + 100, pw, ph))
cases["small_light"] = ("light", rot(rect(W / 2 - 300, H / 2, pw * 0.75, ph * 0.75), -7, W / 2 - 300, H / 2))
cases["landscape_wood"] = ("wood", rot(rect(W / 2, H / 2, ph * 1.05, pw * 1.05), 4, W / 2, H / 2))

cases["phone_on_bill_wood"] = ("wood", rot(rect(W / 2, H / 2, pw, ph), 6, W / 2, H / 2), "phone")
cases["hand_holding_grey"] = ("grey", rot(rect(W / 2, H / 2 - 100, pw, ph), -9, W / 2, H / 2), "hand")
cases["shadow_across_light"] = ("light", rot(rect(W / 2 + 200, H / 2, pw, ph), 14, W / 2, H / 2), "shadow")

truth = {}
for name, item in cases.items():
    kind, quad = item[0], item[1]; extra = item[2] if len(item) > 2 else ""
    im = desk(kind)
    im = place(im, paper(pw, ph), quad)
    d = ImageDraw.Draw(im)
    cx = sum(p[0] for p in quad) / 4; cy = sum(p[1] for p in quad) / 4
    if extra == "phone":      # a dark phone lying across the lower part of the bill, over its right edge
        d.rounded_rectangle([cx + 150, cy + 250, cx + 850, cy + 600], radius=50, fill=(22, 22, 26))
    if extra == "hand":       # a hand holding the bottom edge: fingers over the paper, the hand outside it
        for k in range(4):
            d.rounded_rectangle([cx - 420 + k * 130, cy + ph * 0.42 - 90, cx - 420 + k * 130 + 95, cy + ph * 0.42 + 420], radius=45, fill=(196, 150, 120))
        d.rounded_rectangle([cx - 470, cy + ph * 0.42 + 300, cx + 120, cy + ph * 0.42 + 800], radius=120, fill=(190, 142, 112))
    if extra == "shadow":     # the phone's own shadow: the left half of the frame darker, with a soft edge
        sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(0, 0), (int(W * 0.55), 0), (int(W * 0.35), H), (0, H)], fill=120)
        sh = sh.filter(ImageFilter.GaussianBlur(60))
        im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, sh.point(lambda v: v)).convert("RGB") if False else Image.blend(im, Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, sh), 1.0)
    # uneven light and a little blur, as a phone photo has
    vign = Image.radial_gradient("L").resize((W, H)).point(lambda v: 255 - int(v * 0.25))
    im = Image.composite(im, Image.new("RGB", (W, H), (0, 0, 0)), vign)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    im.save(os.path.join(OUT, name + ".jpg"), quality=90)
    truth[name] = {"w": W, "h": H, "quad": [[round(x, 1), round(y, 1)] for x, y in quad]}
json.dump(truth, open(os.path.join(OUT, "truth.json"), "w"), indent=1)

# a short y4m clip of the tilted case for Chromium's fake camera (640x480, I420)
src = Image.open(os.path.join(OUT, "tilted12_wood.jpg")).resize((640, 480))
ycc = src.convert("YCbCr")
y, cb, cr = ycc.split()
cb = cb.resize((320, 240)); cr = cr.resize((320, 240))
frame = y.tobytes() + cb.tobytes() + cr.tobytes()
with open(os.path.join(OUT, "cam.y4m"), "wb") as f:
    f.write(b"YUV4MPEG2 W640 H480 F10:1 Ip A1:1 C420jpeg\n")
    for _ in range(30):
        f.write(b"FRAME\n" + frame)
print("wrote", len(truth), "images and cam.y4m")
