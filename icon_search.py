import os
from PIL import Image

def classify_images_by_size(images: list[str]) -> dict:
    """
    Classifica una lista di percorsi immagine in base
    alle dimensioni e rapporto d'aspetto.
    Ritorna dict con chiavi: icon, logo, header, poster, hero, others.
    """
    classified = {
        "icon": None,
        "logo": None,
        "header": None,
        "poster": None,
        "hero": None,
        "others": []
    }

    # Soglie (px) e ratio per distinguere i vari tipi
    ICON_MAX = 64        # icone tipicamente ≤64×64
    HEADER_MIN_RATIO = 2  # header
    POSTER_MIN_RATIO = 0.5 # poster verticali
    HERO_MIN_RATIO = 3  # hero

    for path in images:
        try:
            with Image.open(path) as img:
                w, h = img.size
        except Exception:
            classified["others"].append(path)
            continue

        ratio = w / h if h else 0

        # Icona: quadrata e piccola
        if w <= ICON_MAX and h <= ICON_MAX:
            classified["icon"] = path

        # Header: molto largo rispetto all'altezza
        elif ratio >= HEADER_MIN_RATIO and ratio < HERO_MIN_RATIO:
            classified["header"] = path

        # Poster: molto alto rispetto alla larghezza
        elif ratio <= POSTER_MIN_RATIO and ratio:
            classified["poster"] = path

        # Hero: orizzontale, dimensioni medio-grandi
        elif ratio >= HERO_MIN_RATIO and w >= 00:
            if classified["hero"] is not None:
                classified["hero"] = path

        # Logo: file png
        elif path.lower().endswith('.png'):
            classified["logo"] = path

        else:
            classified["others"].append(path)

    return classified

def find_and_classify_steam_images(steam_path: str, appid: int) -> dict:
    """
    Cerca in appcache/librarycache tutte le immagini contenenti l'appid 
    e le classifica automaticamente.
    """
    base = os.path.join(steam_path, "appcache", "librarycache", str(appid))
    if not os.path.isdir(base):
        raise FileNotFoundError(f"Directory non trovata: {base}")

    # Raccogli tutti i file che contengono l'appid
    candidates = [
        os.path.join(base, fn)
        for fn in os.listdir(base)
        if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.ico'))
    ]

    return classify_images_by_size(candidates)