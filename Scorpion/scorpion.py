#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image, ExifTags

try:
    from PIL.PngImagePlugin import PngInfo
except Exception:
    PngInfo = None

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

def print_header(title: str):
    print("\n" + title)
    print("-" * len(title))

def kv(label: str, value):
    print(f"{label:>15}: {value}")

def show_exif(img):
    try:
        raw = img.getexif()
        if not raw:
            print("(Aucune donnee EXIF trouvee)")
            return
        exif = dict(raw)
    except Exception:
        print("(Erreur lors de la lecture EXIF)")
        return

    print_header("Donnees EXIF")
    for tag_id, value in exif.items():
        tag = ExifTags.TAGS.get(tag_id, f"Tag-{tag_id}")
        kv(tag, value)

def save_stripped_copy(img: Image.Image, path: Path) -> Path:
    fmt = (img.format or "").upper()
    out_path = path.with_stem(path.stem + "_stripped")

    if fmt in ("JPEG", "JPG"):
        img.save(out_path, format="JPEG", exif=b"", icc_profile=None, quality=95)
    elif fmt == "PNG":
        img2 = Image.new(img.mode, img.size)
        img2.putdata(list(img.getdata()))
        if PngInfo is not None:
            empty = PngInfo()
            img2.save(out_path, format="PNG", pnginfo=empty, optimize=True)
        else:
            img2.save(out_path, format="PNG", optimize=True)
    elif fmt == "GIF":
        try:
            img.save(out_path, format="GIF", save_all=True, comment=b"")
        except TypeError:
            img.save(out_path, format="GIF", save_all=True)
    elif fmt == "BMP":
        img.save(out_path, format="BMP")
    else:
        img.save(out_path, format=img.format)

    return out_path

def process_file(path: Path, strip: bool):
    if not path.is_file():
        print(f"Erreur : fichier introuvable : {path}")
        return False

    print_header(f"Fichier : {path.name}")
    kv("Taille (octets)", path.stat().st_size)

    try:
        with Image.open(path) as img:
            kv("Format", img.format)
            kv("Dimensions", f"{img.width}×{img.height}")
            kv("Mode couleur", img.mode)

            fmt = (img.format or "").upper()
            if fmt in ("JPEG", "JPG"):
                show_exif(img)

            if strip:
                out_path = save_stripped_copy(img, path)
                print(f" Copie sans metadonnees enregistree : {out_path}")
            
            if img.format == "PNG":
                info_keys = list(img.info.keys())
                if info_keys:
                    print_header("Metadonnees PNG")
                    for k, v in img.info.items():
                        kv(k, v)
                else:
                    print("(Aucune metadonnee PNG trouvée)")

            if img.format == "GIF" and "comment" in img.info:
                print_header("Commentaire GIF")
                kv("Comment", img.info["comment"])


    except Exception as e:
        print(f"Erreur lors de l'ouverture de l'image : {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Scorpion - analyseur d'image (JPEG)")
    parser.add_argument("files", nargs="+", help="Un ou plusieurs fichiers image a analyser")
    parser.add_argument("--strip", action="store_true",
    help="Supprimer les metadonnees EXIF des fichiers JPEG")
    args = parser.parse_args()

    success = True
    for f in args.files:
        if not process_file(Path(f), args.strip):
            success = False
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()
