#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image, ExifTags

IMAGE_EXTS = (".jpg", ".jpeg")

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

def process_file(path: Path):
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

            if img.format and img.format.upper() in ("JPEG", "JPG"):
                show_exif(img)

    except Exception as e:
        print(f"Erreur lors de l'ouverture de l'image : {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Scorpion - analyseur d'image (JPEG)")
    parser.add_argument("file", help="Chemin du fichier image à analyser")
    args = parser.parse_args()

    success = process_file(Path(args.file))
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
