"""Génère toutes les images PNG du plugin (fonds des segments, icônes) avec Playwright.

Usage : python plugin/tools/render-plugin-assets.py [dossier_sdPlugin]
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent / "com.foufou-exe.profil-ia.sdPlugin"

G = {
    "defiler": '<rect x="8" y="5" width="8" height="14" rx="4"/><path d="M12 8.5v2.5"/><path d="M9.5 2.5 12 1l2.5 1.5"/><path d="M9.5 21.5 12 23l2.5-1.5"/>',
    "zoom": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/><path d="M10.5 7.5v6"/><path d="M7.5 10.5h6"/>',
    "volume": '<path d="M3 9.5h3.5L11 5.5v13l-4.5-4H3z" fill="currentColor"/><path d="M15 9a4.2 4.2 0 0 1 0 6"/><path d="M17.8 6.2a8.2 8.2 0 0 1 0 11.6"/>',
    "muet": '<path d="M3 9.5h3.5L11 5.5v13l-4.5-4H3z" fill="currentColor"/><path d="m15.5 9.5 5 5"/><path d="m20.5 9.5-5 5"/>',
    "prompt": '<path d="M4 5.5h16v10H9.5L5 19.5v-4H4z"/><path d="M12 7.6l.9 1.9 1.9.9-1.9.9-.9 1.9-.9-1.9-1.9-.9 1.9-.9z" fill="currentColor"/>',
    "dictee": '<rect x="9" y="2.5" width="6" height="11.5" rx="3"/><path d="M5.5 10.5a6.5 6.5 0 0 0 13 0"/><path d="M12 17v4"/>',
}

def svg(glyph, size, color, sw=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" style="color:{color}">{glyph}</svg>')

# Segment backgrounds 200x100 (icon baked in, text + bar are drawn natively by the layout)
SEGS = {
    "bg-defiler":      ("defiler", "#8b7cf6", "139,124,246", 0.30),
    "bg-zoom":         ("zoom",    "#4ea8f5", "78,168,245",  0.30),
    "bg-volume":       ("volume",  "#43d17f", "67,209,127",  0.30),
    "bg-volume-muet":  ("muet",    "#6b6f7b", "120,124,136", 0.18),
    "bg-dictee":       ("dictee",  "#f0804e", "240,128,78",  0.30),
    "bg-dictee-actif": ("dictee",  "#ff7a52", "255,122,82",  0.45),
}

def seg_html(glyph, color, rgb, a):
    return f"""<html><body style="margin:0;width:200px;height:100px;background:#15161b;overflow:hidden;position:relative">
<div style="position:absolute;left:-35px;top:-40px;width:140px;height:145px;
 background:radial-gradient(circle at 50% 50%, rgba({rgb},{a}) 0%, rgba({rgb},0) 62%)"></div>
<div style="position:absolute;left:0;top:18px;width:1px;height:64px;background:rgba(255,255,255,0.08)"></div>
<div style="position:absolute;left:12px;top:10px;width:44px;height:44px;box-sizing:border-box;border-radius:50%;
 border:1.5px solid {color};display:flex;align-items:center;justify-content:center">{svg(G[glyph], 23, color, 2)}</div>
</body></html>"""

# Key-style images (state image shown in the action list / key area), 144 and 72
def key_html(glyph, color, rgb, label, px):
    s = px / 144
    return f"""<html><body style="margin:0;width:{px}px;height:{px}px;background:#15161b;overflow:hidden;position:relative;font-family:Segoe UI,Inter,Arial,sans-serif">
<div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 42%, rgba({rgb},0.30) 0%, rgba({rgb},0) 60%)"></div>
<div style="position:absolute;left:{36*s}px;top:{18*s}px">{svg(G[glyph], 72*s, color, 2)}</div>
<div style="position:absolute;left:0;right:0;top:{100*s}px;text-align:center;color:#f3f4f6;font-weight:700;font-size:{20*s}px">{label}</div>
</body></html>"""

def mono_html(glyph, px, color="#ffffff", bg="transparent"):
    return f"""<html><body style="margin:0;width:{px}px;height:{px}px;background:{bg};display:flex;align-items:center;justify-content:center">{svg(G[glyph], px*0.9, color, 2)}</body></html>"""

def plugin_icon_html(px):
    s = px / 256
    return f"""<html><body style="margin:0;width:{px}px;height:{px}px;background:transparent">
<div style="width:{px}px;height:{px}px;border-radius:{48*s}px;background:#15161b;position:relative;overflow:hidden">
<div style="position:absolute;inset:0;background:radial-gradient(circle at 30% 30%, rgba(139,124,246,0.45), rgba(139,124,246,0) 55%),radial-gradient(circle at 72% 72%, rgba(67,209,127,0.40), rgba(67,209,127,0) 55%)"></div>
<div style="position:absolute;left:{40*s}px;right:{40*s}px;top:{150*s}px;height:{30*s}px;background:#2a2c35"><div style="width:68%;height:100%;background:#43d17f"></div></div>
<div style="position:absolute;left:{40*s}px;top:{48*s}px;width:{80*s}px;height:{80*s}px;border-radius:50%;box-sizing:border-box;border:{5*s}px solid #8b7cf6;display:flex;align-items:center;justify-content:center">{svg(G['volume'], 44*s, '#8b7cf6', 2)}</div>
<div style="position:absolute;left:{136*s}px;top:{60*s}px;width:{80*s}px;height:{20*s}px;border-radius:{4*s}px;background:#f3f4f6"></div>
<div style="position:absolute;left:{136*s}px;top:{94*s}px;width:{56*s}px;height:{16*s}px;border-radius:{4*s}px;background:#a6ebc3"></div>
</div></body></html>"""

KEYS = {
    "defiler": ("defiler", "#8b7cf6", "139,124,246", "Défiler"),
    "zoom": ("zoom", "#4ea8f5", "78,168,245", "Zoom"),
    "volume": ("volume", "#43d17f", "67,209,127", "Volume"),
    "dictee": ("dictee", "#f0804e", "240,128,78", "Dictée"),
    "prompt": ("prompt", "#e8794a", "232,121,74", "Prompt IA"),
}

with sync_playwright() as p:
    b = p.chromium.launch()
    def shot(html, path, w, h):
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        pg.set_content(html)
        path.parent.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(path), omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h})
        pg.close()
    for name, (g, c, rgb, a) in SEGS.items():
        shot(seg_html(g, c, rgb, a), OUT / "imgs/layouts" / f"{name}.png", 200, 100)
    for name, (g, c, rgb, label) in KEYS.items():
        shot(key_html(g, c, rgb, label, 72), OUT / "imgs/actions" / f"{name}-key.png", 72, 72)
        shot(key_html(g, c, rgb, label, 144), OUT / "imgs/actions" / f"{name}-key@2x.png", 144, 144)
        shot(mono_html(g, 20), OUT / "imgs/actions" / f"{name}.png", 20, 20)
        shot(mono_html(g, 40), OUT / "imgs/actions" / f"{name}@2x.png", 40, 40)
    shot(plugin_icon_html(256), OUT / "imgs/plugin/icon.png", 256, 256)
    shot(plugin_icon_html(512), OUT / "imgs/plugin/icon@2x.png", 512, 512)
    shot(mono_html("volume", 28), OUT / "imgs/plugin/category.png", 28, 28)
    shot(mono_html("volume", 56), OUT / "imgs/plugin/category@2x.png", 56, 56)
    b.close()
print("ok")
