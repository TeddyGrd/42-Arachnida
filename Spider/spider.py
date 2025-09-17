import argparse
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from collections import deque

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp",".svg")

def list_images(page_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if not src:
            continue
        abs_url = urljoin(page_url, src)
        images.append(abs_url)
    return images


def find_internal_links(base_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    base_netloc = urlparse(base_url).netloc
    links = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        if not href:
            continue
        abs_url = urljoin(base_url, href)
        p = urlparse(abs_url)
        if p.scheme in ("http", "https") and p.netloc == base_netloc:
            links.append(abs_url)
    return links

def safe_filename_from_url(url: str, idx: int) -> str:
    path = urlparse(url).path
    name = os.path.basename(path)
    if name and name.lower().endswith(IMAGE_EXTS):
        return name
    for ext in IMAGE_EXTS:
        if url.lower().endswith(ext):
            return f"image_{idx}{ext}"
    return f"image_{idx}.bin"

def download_image(url: str, out_dir: Path, idx: int, headers: dict):
    with requests.get(url, headers=headers,stream=True,timeout=15) as resp:
        resp.raise_for_status()
        fname = safe_filename_from_url(url,idx)
        target = out_dir / fname
        base, ext = os.path.splitext(target.name)
        n = 1
        while target.exists():
            target = out_dir / f"{base} ({n}){ext}"
            n += 1
        with open(target,"wb") as f:
            for chunk in resp.iter_content(8192):
                if chunk:
                    f.write(chunk)

def crawl(start_url: str, out_dir: Path, headers: dict, recursive: bool, max_depth: int ):
    visited = set()
    queue = deque([(start_url, 1)])
    img_counter = 0
    downloaded = set()

    while queue:
        url,depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        print(f"[page] depth={depth} {url}")
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            print(f"   [net] Erreur reseau {url}: {e}")
            continue

        status = r.status_code
        if status < 200 or status >= 300:
            print(f"   [http {status}] {url}")
            continue
        
        images = list_images(url, html)
        for u in images:
            if u in downloaded:
                continue
            downloaded.add(u)
            
            img_counter +=1
            try:
                download_image(u, out_dir, img_counter, headers)
                print(f"   [img] {os.path.basename(u)}")
            except Exception as e:
                print(f"[!] Echec telechargement {u}: {e}")
        if recursive and depth < max_depth:
            for nxt in find_internal_links(url,html):
                if nxt not in visited:
                    queue.append((nxt,depth + 1))
    print(f"[done] pages visitees={len(visited)} | images telechargees={img_counter}")

def main():
    parser = argparse.ArgumentParser(
        description="Lister et telecharger les images d'une page (options -r/-l/-p)"
    )
    parser.add_argument("url", help="L'URL du site a analyser")
    parser.add_argument("-p", dest="path", default="./data/", help="Dossier de sortie (defaut: ./data/)")
    parser.add_argument("-r", action="store_true", help="Mode récursif (crawl)")
    parser.add_argument("-l", type=int, dest="level", help="Profondeur max (defaut 5 si -r)")
    args = parser.parse_args()

    print("URL reçue :", args.url)

    headers = {"User-Agent": "ArachnidaSpider/1.0"}

    out_dir = Path(args.path)
    out_dir.mkdir(parents=True, exist_ok=True)

    DEFAULT_DEPTH = 5

    if not args.r:
        max_depth = 1
    elif args.level and args.level > 0:
        max_depth = args.level
    else:
        max_depth = DEFAULT_DEPTH
    
    print(f"Recursif: {args.r} | Profondeur: {max_depth} | Dossier: {out_dir.resolve()}")

    crawl(args.url, out_dir, headers, recursive=args.r, max_depth=max_depth)

if __name__ == "__main__":
    main()
