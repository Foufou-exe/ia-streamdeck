"""Touches de la page ChatGPT : mascotte « Pixel » bleu-violet, 144x144, GIF animés 30 images.

Usage : python tools/render-chatgpt-keys.py [dossier_sortie]
Par défaut : profils/chatgpt/touches/
"""
import math, sys, pathlib, io
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "profils" / "chatgpt" / "touches"
N, DUR = 30, 60
FAM = {"write": "110,128,255", "create": "176,140,255", "nav": "120,132,190"}
KEYS = [
    ("01-nouvelle-conv", "Nouvelle conv.", "create"),
    ("02-explique", "Explique", "write"),
    ("03-corrige", "Corrige", "write"),
    ("04-traduis", "Traduis", "write"),
    ("05-image", "Image", "create"),
    ("06-resume", "Résumé", "write"),
    ("07-idees", "Idées", "create"),
    ("08-retour", "Retour", "nav"),
]
INK = "#1a1b4b"

def mascot(t, sleepy=False, look=0):
    dy = 1.8 * math.sin(2 * math.pi * t)
    blink = 0.70 <= t < 0.76
    if sleepy:
        eyes = (f'<path d="M58.5 70 q3.5 3 7 0" stroke="{INK}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
                f'<path d="M78.5 70 q3.5 3 7 0" stroke="{INK}" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
        mouth = f'<ellipse cx="72" cy="83" rx="2.6" ry="2" fill="{INK}"/>'
    elif blink:
        eyes = (f'<path d="M58.5 70.5 h7" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
                f'<path d="M78.5 70.5 h7" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
        mouth = f'<path d="M67 81 q5 4.5 10 0" stroke="{INK}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
    else:
        eyes = (f'<ellipse cx="{62+look}" cy="70" rx="3.6" ry="4.6" fill="{INK}"/><circle cx="{63.2+look}" cy="68.4" r="1.25" fill="#fff"/>'
                f'<ellipse cx="{82+look}" cy="70" rx="3.6" ry="4.6" fill="{INK}"/><circle cx="{83.2+look}" cy="68.4" r="1.25" fill="#fff"/>')
        mouth = f'<path d="M67 81 q5 4.5 10 0" stroke="{INK}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
    return f'''<g transform="translate(0 {dy:.2f})">
  <defs><linearGradient id="body" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="#c3b2ff"/><stop offset="0.5" stop-color="#7f96ff"/><stop offset="1" stop-color="#5354f2"/></linearGradient></defs>
  <line x1="72" y1="52" x2="72" y2="41" stroke="#4b47d6" stroke-width="3" stroke-linecap="round"/>
  <circle cx="72" cy="38.5" r="4.6" fill="#eef4ff"/>
  <circle cx="45" cy="73" r="5.2" fill="#4b47d6"/><circle cx="99" cy="73" r="5.2" fill="#4b47d6"/>
  <rect x="46" y="52" width="52" height="42" rx="17" fill="url(#body)"/>
  <rect x="46.75" y="52.75" width="50.5" height="40.5" rx="16.3" fill="none" stroke="#dfe3ff" stroke-opacity="0.55" stroke-width="1.5"/>
  <ellipse cx="63" cy="58" rx="11" ry="3.2" fill="#fff" opacity="0.35"/>
  <ellipse cx="54.5" cy="79.5" rx="4.6" ry="2.6" fill="#ff9ad5" opacity="0.55"/>
  <ellipse cx="89.5" cy="79.5" rx="4.6" ry="2.6" fill="#ff9ad5" opacity="0.55"/>
  {eyes}{mouth}
</g>'''

def acc(name, t):
    s = math.sin(2 * math.pi * t)
    if name == "01-nouvelle-conv":
        k = 1 + 0.09 * s
        return f'''<g transform="translate(34 34) scale({k:.3f})"><circle r="11.5" fill="#b9a6ff"/>
<path d="M0 -5.5v11M-5.5 0h11" stroke="#1a1b4b" stroke-width="2.8" stroke-linecap="round"/></g>'''
    if name == "02-explique":
        dots = ""
        for i in range(3):
            ph = (t * 3 - i * 0.5) % 3
            up = -2.2 if ph < 0.5 else 0
            op = 1 if ph < 0.5 else 0.45
            dots += f'<circle cx="{107+i*9}" cy="{25+up}" r="3.1" fill="#7f96ff" opacity="{op}"/>'
        return f'''<circle cx="97" cy="46" r="2.6" fill="#eef4ff"/><circle cx="102.5" cy="39" r="3.8" fill="#eef4ff"/>
<rect x="97" y="13" width="38" height="24" rx="12" fill="#eef4ff"/>{dots}'''
    if name == "03-corrige":
        p = min(1, (t % 1) * 1.8)
        dash = 22 * (1 - p)
        return f'''<g transform="rotate(6 112 60)"><rect x="98" y="34" width="30" height="44" rx="4" fill="#eef4ff"/>
<path d="M104 44h18M104 51h14M104 65h18M104 72h11" stroke="#aab3e6" stroke-width="2.2" stroke-linecap="round"/>
<path d="M104 58 q2 -2.5 4 0 t4 0 t4 0 t4 0" stroke="#ef5b5b" stroke-width="1.8" fill="none"/>
<path d="M106 58 l5 5 9 -11" stroke="#5354f2" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"
 stroke-dasharray="22" stroke-dashoffset="{dash:.2f}"/></g>'''
    if name == "04-traduis":
        word = "EN" if t < 0.5 else "FR"
        return f'''<rect x="96" y="14" width="36" height="26" rx="8" fill="#eef4ff"/><path d="M104 39l-3 8 9-7z" fill="#eef4ff"/>
<text x="114" y="32.5" text-anchor="middle" font-family="Inter" font-weight="800" font-size="13.5" fill="#3b3ad0">{word}</text>'''
    if name == "05-image":
        sy = 34 - 4 * (0.5 + 0.5 * s)
        sp = 0.5 + 0.5 * math.sin(2 * math.pi * (t + 0.25))
        return f'''<g><rect x="95" y="16" width="38" height="31" rx="6" fill="#eef4ff"/>
<clipPath id="c"><rect x="98" y="19" width="32" height="25" rx="3.5"/></clipPath>
<g clip-path="url(#c)"><rect x="98" y="19" width="32" height="25" fill="#d9dcff"/>
<circle cx="122" cy="{sy:.2f}" r="4.2" fill="#ffffff"/>
<path d="M98 44 l9 -11 7 8 5 -5 11 8z" fill="#7f96ff"/></g></g>
<path d="M88 22 l1.4 3.3 3.3 1.4 -3.3 1.4 -1.4 3.3 -1.4 -3.3 -3.3 -1.4 3.3 -1.4z" fill="#c3b2ff" opacity="{sp:.2f}"/>'''
    if name == "06-resume":
        out = '<rect x="98" y="22" width="32" height="40" rx="5" fill="#eef4ff"/>'
        for i in range(3):
            vis = 1 if (t * 4) % 4 >= i + 0.6 or (t * 4) % 4 >= 3.4 else 0.15
            y = 31 + i * 10
            out += (f'<circle cx="104.5" cy="{y}" r="2.2" fill="#b9a6ff" opacity="{vis}"/>'
                    f'<path d="M110 {y}h{14 - i*3}" stroke="#7f96ff" stroke-width="2.4" stroke-linecap="round" opacity="{vis}"/>')
        return out
    if name == "07-idees":
        g = 0.55 + 0.45 * (0.5 + 0.5 * s)
        return f'''<circle cx="72" cy="22" r="{16*g:.2f}" fill="#b9c4ff" opacity="{0.30*g:.2f}"/>
<path d="M66 20a6 6 0 1 1 12 0c0 3 -2.4 4.2 -2.4 7h-7.2c0 -2.8 -2.4 -4 -2.4 -7z" fill="#eef4ff"/>
<rect x="68.6" y="28.2" width="6.8" height="3.2" rx="1.4" fill="#9aa3d9"/>
<path d="M56 18h-4M92 18h-4M60 8l-2.5 -2.5M84 8l2.5 -2.5" stroke="#c3b2ff" stroke-width="2" stroke-linecap="round" opacity="{g:.2f}"/>'''
    if name == "08-retour":
        z = ""
        for i in range(2):
            ph = (t + i * 0.5) % 1
            z += (f'<text x="{102+ph*10:.1f}" y="{46-ph*20:.1f}" font-family="Inter" font-weight="800" font-size="{9+ph*5:.1f}"'
                  f' fill="#c9d1ff" opacity="{1-ph:.2f}">z</text>')
        return f'''<circle cx="34" cy="34" r="11.5" fill="#8c97cf"/>
<path d="M29.5 31.5h7.5a4.5 4.5 0 0 1 0 9h-5" stroke="#121633" stroke-width="2.4" fill="none" stroke-linecap="round"/>
<path d="M32 27.5l-4 4 4 4" stroke="#121633" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>{z}'''
    return ""

def frame_html(name, label, fam, t, with_text):
    rgb = FAM[fam]
    sleepy = name == "08-retour"
    look = 1.2 if name in ("02-explique", "03-corrige", "04-traduis", "06-resume", "05-image") else 0
    lbl = (f'<text x="72" y="133" text-anchor="middle" font-family="Inter" font-weight="700" font-size="16.5" fill="#eef4ff">{label}</text>'
           if with_text else "")
    return f'''<html><body style="margin:0;background:#121633">
<svg width="144" height="144" viewBox="0 0 144 144" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="g" cx="50%" cy="44%" r="55%"><stop offset="0" stop-color="rgb({rgb})" stop-opacity="0.34"/>
<stop offset="1" stop-color="rgb({rgb})" stop-opacity="0"/></radialGradient></defs>
<rect width="144" height="144" fill="#121633"/><rect width="144" height="144" fill="url(#g)"/>
{mascot(t, sleepy, look)}{acc(name, t)}{lbl}</svg></body></html>'''

def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 144, "height": 144}, device_scale_factor=1)
        for name, label, fam in KEYS:
            for variant, wt in (("avec-texte", True), ("sans-texte", False)):
                frames = []
                for i in range(N):
                    pg.set_content(frame_html(name, label, fam, i / N, wt))
                    frames.append(Image.open(io.BytesIO(pg.screenshot())).convert("RGB"))
                d = OUT / variant; d.mkdir(parents=True, exist_ok=True)
                pal = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
                pal[0].save(d / f"{name}.gif", save_all=True, append_images=pal[1:], duration=DUR, loop=0, disposal=1, optimize=False)
                if wt:
                    s = OUT / "png-statique"; s.mkdir(parents=True, exist_ok=True)
                    frames[0].save(s / f"{name}.png")
        b.close()
    print("ok")

main()
