"""Construit le profil Stream Deck+ « Profil IA » (pages Claude + ChatGPT) à partir de profils/profil-ia.json.

Usage : python tools/build-profile.py [--pack]
Sortie : dist/<UUID>.sdProfile/  (dossier au format ProfilesV3 de Stream Deck)
         dist/Profil-IA.streamDeckProfile  (archive importable, avec --pack)

Pour l'installer à la main : quitter Stream Deck, copier le dossier dans
%APPDATA%\\Elgato\\StreamDeck\\ProfilesV3\\ puis relancer Stream Deck.
Le plus simple reste d'importer le fichier Profil-IA.streamDeckProfile publié dans les Releases.
"""
import hashlib, json, pathlib, shutil, sys, uuid, zipfile
from PIL import Image, ImageSequence

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "profils"
NS = uuid.UUID("6f1c5e2a-0d3b-4c1e-9a77-3a5b2c1d0e9f")
OUT = ROOT / "dist" / (str(uuid.uuid5(NS, "profil-ia")).upper() + ".sdProfile")
ARCHIVE = ROOT / "dist" / "Profil-IA.streamDeckProfile"
# version unique : celle du plugin (plugin/package.json), au format Stream Deck x.y.z.0
VERSION = json.loads((ROOT / "plugin" / "package.json").read_text(encoding="utf-8"))["version"] + ".0"
PLUGIN = {"Name": "Profil IA", "UUID": "com.foufou-exe.profil-ia", "Version": VERSION}

def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))

def img_id(*parts):
    h = hashlib.sha1("/".join(parts).encode()).hexdigest().upper()
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n = int(h, 16)
    s = ""
    while len(s) < 26:
        n, r = divmod(n, 36)
        s += alphabet[r]
    return s + "Z"

def gif_to_webp(src, dst):
    im = Image.open(src)
    frames, durations = [], []
    for f in ImageSequence.Iterator(im):
        frames.append(f.convert("RGBA"))
        durations.append(f.info.get("duration", 60))
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=durations, loop=0, lossless=True)

def key_action(page, pos, k, images):
    name = k["image"]
    image = f"Images/{img_id(page['id'], name)}.webp"
    gif_to_webp(SRC / page["touches"] / f"{name}.gif", images / pathlib.Path(image).name)
    base = {"ActionID": uid(page["id"], pos), "LinkedTitle": True, "Resources": None, "State": 0,
            "States": [{"Image": image, "ShowTitle": False}]}
    a = k["action"]
    if a == "website":
        return {**base, "Name": "Website", "UUID": "com.elgato.streamdeck.system.website",
                "Plugin": {"Name": "Website", "UUID": "com.elgato.streamdeck.system.website", "Version": "1.0"},
                "Settings": {"browser": "", "openInBrowser": True, "path": k["url"]}}
    if a in ("next-page", "previous-page"):
        kind = "next" if a == "next-page" else "previous"
        return {**base, "Name": "Next Page" if kind == "next" else "Previous Page", "UUID": f"com.elgato.streamdeck.page.{kind}",
                "Plugin": {"Name": "Pages", "UUID": "com.elgato.streamdeck.page", "Version": "1.0"}, "Settings": {}}
    if a == "prompt":
        settings = {"preset": k["preset"], "source": "selection", "fallback": "none", "target": k["target"],
                    "longTarget": k["longTarget"], "send": k["send"], "restore": True}
        if "prompt" in k:
            settings["prompt"] = k["prompt"]
        return {**base, "Name": "Prompt IA", "UUID": "com.foufou-exe.profil-ia.prompt", "Plugin": PLUGIN, "Settings": settings}
    raise ValueError(f"action inconnue : {a}")

def dial_action(page, pos, dial):
    labels = {"defiler": "Défiler (barre XL)", "zoom": "Zoom (barre XL)", "volume": "Volume (barre XL)", "dictee": "Dictée (barre XL)"}
    return {"ActionID": uid(page["id"], "dial", pos), "LinkedTitle": True, "Name": labels[dial], "Plugin": PLUGIN,
            "Resources": None, "Settings": {}, "State": 0, "States": [{}], "UUID": f"com.foufou-exe.profil-ia.{dial}"}

def main():
    cfg = json.loads((SRC / "profil-ia.json").read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    page_ids = []
    for page in cfg["pages"]:
        pid = uid("page", page["id"])
        page_ids.append(pid)
        folder = OUT / "Profiles" / pid.upper()
        images = folder / "Images"
        images.mkdir(parents=True)
        keys = {pos: key_action(page, pos, k, images) for pos, k in page["keys"].items()}
        dials = {f"{i},0": dial_action(page, f"{i},0", d) for i, d in enumerate(cfg["dials"])}
        manifest = {"Controllers": [{"Actions": keys, "Type": "Keypad"}, {"Actions": dials, "Type": "Encoder"}],
                    "Icon": "", "Name": page["name"]}
        (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # page « par défaut » vide attendue par Stream Deck (hors liste des pages)
    default_id = uid("page", "default")
    (OUT / "Profiles" / default_id.upper() / "Images").mkdir(parents=True)
    (OUT / "Profiles" / default_id.upper() / "manifest.json").write_text(
        json.dumps({"Controllers": [{"Actions": None, "Type": "Keypad"}, {"Actions": None, "Type": "Encoder"}], "Icon": "", "Name": ""}),
        encoding="utf-8")
    root = {"Device": {"Model": cfg["device"], "UUID": ""}, "Name": cfg["name"],
            "Pages": {"Current": page_ids[0], "Default": default_id, "Pages": page_ids}, "Version": "3.0"}
    (OUT / "manifest.json").write_text(json.dumps(root, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"profil généré : {OUT.relative_to(ROOT)} ({len(page_ids)} pages)")
    if "--pack" in sys.argv:
        pack()

def pack():
    """Archive zip contenant le dossier <UUID>.sdProfile, importable par double-clic."""
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            info = zipfile.ZipInfo(f.relative_to(OUT.parent).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))  # date fixe = archive reproductible
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())
    print(f"archive {ARCHIVE.relative_to(ROOT)} ({len(files)} fichiers)")

if __name__ == "__main__":
    main()
