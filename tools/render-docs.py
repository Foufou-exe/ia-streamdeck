"""Génère les images de la documentation (docs/images/) à partir des touches et des fonds du plugin.

Usage : python tools/render-docs.py
  - page-claude.gif / page-chatgpt.gif : Stream Deck+ animé avec chaque page
  - molettes-etats.png                  : les états des 4 molettes (×2)
  - panneau-prompt.png                  : le panneau de réglages d'une touche Prompt IA
"""
import base64, io, json, pathlib
from PIL import Image, ImageDraw, ImageSequence
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYOUTS = ROOT / "plugin" / "com.foufou-exe.profil-ia.sdPlugin" / "imgs" / "layouts"
OUT = ROOT / "docs" / "images"
CFG = json.loads((ROOT / "profils" / "profil-ia.json").read_text(encoding="utf-8"))

def data_url(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()

def segment(bg, title, value, value_color, pct, fill):
    return f'''<div style="position:relative;width:200px;height:100px;background:url({data_url(LAYOUTS / (bg + '.png'))})">
<div style="position:absolute;left:66px;top:9px;width:128px;height:24px;font:700 19px/24px Inter,sans-serif;color:#F3F4F6">{title}</div>
<div style="position:absolute;left:66px;top:34px;width:128px;height:20px;font:600 15px/20px Inter,sans-serif;color:{value_color}">{value}</div>
<div style="position:absolute;left:14px;top:64px;width:172px;height:18px;background:#2A2C35"><div style="width:{pct}%;height:18px;background:{fill}"></div></div></div>'''

STRIP = [("bg-defiler", "Défiler", "↓ Bas", "#C9C1FF", 72, "#8B7CF6"), ("bg-zoom", "Zoom", "130 %", "#A9D4FB", 53, "#4EA8F5"),
         ("bg-volume", "Volume", "68 %", "#A6EBC3", 68, "#43D17F"), ("bg-dictee-actif", "Dictée", "Écoute 0:12", "#FFC2AD", 84, "#FF7A52")]

STATES = [
    ("Défiler", [("bg-defiler", "Défiler", "Normal ×1", "#C9C1FF", 0, "#8B7CF6"), ("bg-defiler", "Défiler", "↓ Bas", "#C9C1FF", 72, "#8B7CF6"), ("bg-defiler", "Défiler", "↑ Haut ×3", "#C9C1FF", 100, "#8B7CF6")]),
    ("Zoom", [("bg-zoom", "Zoom", "100 %", "#A9D4FB", 33, "#4EA8F5"), ("bg-zoom", "Zoom", "130 %", "#A9D4FB", 53, "#4EA8F5"), ("bg-zoom", "Zoom", "80 %", "#A9D4FB", 20, "#4EA8F5")]),
    ("Volume", [("bg-volume", "Volume", "68 %", "#A6EBC3", 68, "#43D17F"), ("bg-volume-muet", "Volume", "Muet", "#9A9EAA", 68, "#4A4D57"), ("bg-volume", "Volume", "100 %", "#A6EBC3", 100, "#43D17F")]),
    ("Dictée", [("bg-dictee", "Dictée", "Appuyer", "#F6B89C", 0, "#F0804E"), ("bg-dictee-actif", "Dictée", "Écoute 0:12", "#FFC2AD", 84, "#FF7A52"), ("bg-dictee-actif", "Dictée", "Écoute 0:13", "#FFC2AD", 38, "#D9603D")]),
]

# chaque colonne (touche, segment, molette) est centrée sur un segment de 200 px du bandeau
KEY, GAP, PAD = 144, 24, 44
W = 800 + 2 * PAD
COL = lambda c: PAD + 100 + 200 * c  # centre horizontal de la colonne c
KEYS_Y = PAD
STRIP_Y = KEYS_Y + 2 * KEY + GAP + 28
DIAL_Y = STRIP_Y + 100 + 32
H = DIAL_Y + 120 + PAD

def device_base(page, shot):
    dials = "".join(f'<div style="position:absolute;left:{COL(i) - 60}px;top:{DIAL_Y}px;width:120px;height:120px;border-radius:50%;'
                    f'background:#2b2c33;box-shadow:inset 0 0 0 9px #18191d,0 8px 18px rgba(0,0,0,.45)"></div>' for i in range(4))
    strip = "".join(segment(*s) for s in STRIP)
    html = f'''<html><body style="margin:0;background:transparent">
<div style="position:relative;width:{W}px;height:{H}px;background:#1d1e23;border-radius:36px">
<div style="position:absolute;left:{PAD}px;top:{STRIP_Y}px;width:800px;height:100px;display:flex;border-radius:8px;overflow:hidden;outline:1px solid #34363f">{strip}</div>
{dials}</div></body></html>'''
    return shot(html, W, H)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        def shot(html, w, h, scale=1):
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
            pg.set_content(html)
            img = Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert("RGBA")
            pg.close()
            return img

        # 1. pages animées
        for page in CFG["pages"]:
            base = device_base(page, shot)
            # le bandeau fait 800 px : on centre l'appareil autour
            keys = []
            for pos, k in page["keys"].items():
                c, r = map(int, pos.split(","))
                gif = Image.open(ROOT / "profils" / page["touches"] / f"{k['image']}.gif")
                frames = [f.convert("RGBA") for f in ImageSequence.Iterator(gif)]
                keys.append(((c, r), frames))
            n = max(len(f) for _, f in keys)
            mask = Image.new("L", (KEY, KEY), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, KEY - 1, KEY - 1], radius=18, fill=255)
            out = []
            for i in range(n):
                fr = base.copy()
                for (c, r), frames in keys:
                    k = frames[i % len(frames)]
                    fr.paste(k, (COL(c) - KEY // 2, KEYS_Y + r * (KEY + GAP)), mask)
                bg = Image.new("RGBA", fr.size, (246, 246, 244, 255))
                bg.alpha_composite(fr)
                out.append(bg.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
            out[0].save(OUT / f"page-{page['id']}.gif", save_all=True, append_images=out[1:], duration=60, loop=0, optimize=True)

        # 2. états des molettes
        rows = "".join(
            f'<div style="display:flex;align-items:center;gap:18px"><div style="width:110px;font:700 20px Inter,sans-serif;color:#f3f4f6">{name}</div>'
            + "".join(f'<div style="transform:scale(2);transform-origin:0 0;width:400px;height:200px"><div style="width:200px">{segment(*s)}</div></div>' for s in states)
            + "</div>" for name, states in STATES)
        html = f'<html><body style="margin:0;background:#1d1e23"><div style="padding:32px;display:flex;flex-direction:column;gap:22px">{rows}</div></body></html>'
        shot(html, 32 * 2 + 110 + 18 + 3 * 400 + 2 * 18, 32 * 2 + 4 * 200 + 3 * 22).convert("RGB").save(OUT / "molettes-etats.png", optimize=True)

        # 3. panneau de réglages
        pi = (ROOT / "plugin" / "com.foufou-exe.profil-ia.sdPlugin" / "ui" / "prompt.html").as_uri()
        pg = b.new_page(viewport={"width": 420, "height": 560}, device_scale_factor=2)
        pg.goto(pi)
        pg.evaluate("connectElgatoStreamDeckSocket(1,'X','r','{}',JSON.stringify({payload:{settings:{preset:'resume'}}}))")
        pg.wait_for_timeout(200)
        pg.screenshot(path=str(OUT / "panneau-prompt.png"))
        b.close()
    for f in sorted(OUT.iterdir()):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size // 1024} Ko")

if __name__ == "__main__":
    main()
