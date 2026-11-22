import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


UNAVAILABLE_MARKERS = (
    "non disponibile per l'acquisto",
    "non disponibile per l’acquisto",
    "scorte attualmente esaurite",
    "attualmente esaurite",
    "attualmente esaurito",
    "scorte esaurite",
    "attualmente non disponibile",
    "al momento non disponibile",
    "momentaneamente non disponibile",
    "esaurito",
    "non disponibile",
    "out of stock",
    "sold out",
    "temporarily unavailable",
    "currently unavailable",
)

AVAILABLE_MARKERS = (
    "aggiungi al carrello",
    "aggiungi alla cesta",
    "acquista ora",
    "compra ora",
    "buy now",
    "add to cart",
    "continua ad acquistare",
)


def classify_status(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.lower())
    if any(marker in normalized for marker in UNAVAILABLE_MARKERS):
        return "unavailable"
    if any(marker in normalized for marker in AVAILABLE_MARKERS):
        return "available"
    return "unknown"


def load_env() -> None:
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_status(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; PSStockBot/1.0)",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        },
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings).lower()
    status = classify_status(text)
    if status == "unknown" and "direct.playstation.com" in url:
        return "available"
    return status


def get_page_snapshot(url: str, mode: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; PSStockBot/1.0)",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        },
        timeout=20,
    )
    response.raise_for_status()

    if mode == "raw_html":
        return hashlib.sha256(response.content).hexdigest()

    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    for element in soup.find_all(["li", "article"]):
        text = " ".join(element.stripped_strings)
        text = re.sub(r"\s+", " ", text).lower()
        if mode == "deal" and re.search(
            r"risparmia|sconto|offerta|promozione|fino a",
            text,
        ):
            records.append(text)
        elif mode == "bundle" and re.search(
            r"bundle|console ps5|ps5 pro|edizione",
            text,
        ):
            records.append(text)
        elif mode == "store" and re.search(
            r"ps5|playstation 5|ps5 pro",
            text,
        ):
            records.append(text)

    normalized = "\n".join(sorted(set(records)))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def discover_catalog_products(catalog_url: str) -> list[dict]:
    response = requests.get(
        catalog_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; PSStockBot/1.0)",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        },
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    products = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        name = " ".join(anchor.stripped_strings)
        name = re.sub(r"\s+", " ", name).strip()
        href = anchor["href"].strip()
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.playstation.com" + href
        href = href.split("?")[0]

        is_product = (
            (
                "/ps5/" in href
                and ("/buy-now/" in href or "/product/" in href)
            )
            or "/product/" in href
        )
        is_navigation = any(
            href.endswith(path)
            for path in (
                "/it-it/ps5/",
                "/it-it/ps5/games/",
                "/it-it/consoles/ps5/shop-all/",
                "/it-it/store/hardware/",
            )
        )
        if is_product and not is_navigation and href not in seen:
            seen.add(href)
            products.append({
                "name": name or href.rsplit("/", 2)[-2].replace("-", " ").title(),
                "url": href,
            })

    for item in list(products):
        if len(products) >= 50:
            break
        try:
            nested_response = requests.get(
                item["url"],
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; PSStockBot/1.0)",
                    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
                },
                timeout=20,
            )
            nested_response.raise_for_status()
        except requests.RequestException:
            continue

        nested_soup = BeautifulSoup(nested_response.text, "html.parser")
        for anchor in nested_soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith("/"):
                href = "https://www.playstation.com" + href
            href = href.split("?")[0]
            if "/product/" not in href and "/buy-now/" not in href:
                continue
            if href in seen:
                continue
            seen.add(href)
            name = " ".join(anchor.stripped_strings)
            name = re.sub(r"\s+", " ", name).strip()
            products.append({
                "name": name or href.rsplit("/", 2)[-2].replace("-", " ").title(),
                "url": href,
            })
            if len(products) >= 50:
                break

    return products


def send_telegram(message: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "disable_web_page_preview": False},
        timeout=20,
    )
    response.raise_for_status()


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def monitor_once(products: list[dict], state_path: Path) -> dict:
    state = load_state(state_path)
    configured_names = {product["name"] for product in products}
    state = {name: value for name, value in state.items() if name in configured_names}
    for product in products:
        name = product["name"]
        url = product["url"]
        mode = product.get("mode")
        try:
            status = get_page_snapshot(url, mode) if mode else get_status(url)
        except requests.RequestException as exc:
            print(f"[WARN] {name}: controllo fallito ({exc})", file=sys.stderr)
            continue

        previous = state.get(name)
        if mode and previous is not None and previous != status:
            labels = {
                "deal": "Sconti PlayStation",
                "bundle": "Bundle/console PlayStation",
                "store": "Novità PlayStation Store",
                "raw_html": "Pagina PlayStation",
            }
            label = labels.get(mode, "Sezione PlayStation")
            send_telegram(
                f"🔔 CAMBIAMENTO: {label}\n"
                f"Potrebbe esserci una nuova offerta o disponibilità.\n"
                f"Controlla qui:\n{url}"
            )
        elif status == "available" and previous != "available":
            send_telegram(
                f"🎮 DISPONIBILE: {name}\n"
                f"Controlla subito sul sito ufficiale:\n{url}"
            )

        state[name] = status
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {name}: {status}")

    save_state(state_path, state)
    return state


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Notifica su Telegram le disponibilita PS5")
    parser.add_argument("--once", action="store_true", help="Effettua un solo controllo")
    parser.add_argument("--test-telegram", action="store_true", help="Invia un messaggio di prova")
    args = parser.parse_args()

    missing = [
        name
        for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
        if not os.environ.get(name)
    ]
    if missing:
        parser.error(
            "Configura TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nel file .env "
            "(vedi .env.example)"
        )

    if args.test_telegram:
        send_telegram("✅ Il bot PS Stock è configurato correttamente.")
        print("Messaggio Telegram inviato.")
        return

    products_path = Path(__file__).with_name("products.json")
    products = json.loads(products_path.read_text(encoding="utf-8"))
    state_path = Path(os.environ.get("STATE_FILE", "state.json"))
    if not state_path.is_absolute():
        state_path = Path(__file__).with_name(os.fspath(state_path))

    interval = max(10, int(os.environ.get("POLL_INTERVAL_SECONDS", "60")))
    while True:
        monitor_once(products, state_path)
        if args.once:
            break
        time.sleep(interval)


if __name__ == "__main__":
    main()
