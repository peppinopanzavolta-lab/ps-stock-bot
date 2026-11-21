# PlayStation Stock Telegram Bot

Monitora ogni minuto le pagine PlayStation ufficiali configurate in `products.json`
e invia una notifica Telegram quando una PS5 torna disponibile o quando cambiano
le offerte hardware e i bundle pubblicati sul sito ufficiale.

## Configurazione

1. Crea il bot con `@BotFather` su Telegram e copia il token.
2. Ottieni il tuo chat ID; puoi usare `@userinfobot`.
3. Copia la configurazione:

```bash
cp .env.example .env
```

Inserisci token e chat ID nel file `.env`.

## Avvio

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python telegram_bot.py --test-telegram
.venv/bin/python telegram_bot.py
```

Oppure con Docker:

```bash
docker compose up -d --build
docker compose logs -f
```

## Senza tenere acceso il PC

Puoi usare GitHub Actions:

1. Carica questa cartella in un repository GitHub.
2. In `Settings > Secrets and variables > Actions`, aggiungi:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Dalla scheda `Actions` abilita il workflow e avvialo con `Run workflow`.

Il workflow controlla PlayStation ogni 10 minuti e salva lo stato nel repository.
Condivisioni future o fork del repository potrebbero esporre dati sensibili:
mantieni token e chat ID esclusivamente nei secrets GitHub.

Per aggiungere un prodotto, inserisci un oggetto `{ "name": "...", "url": "..." }`
in `products.json`. Di default sono monitorate la PS5 Pro e la PS5 Slim con unità disco sulle rispettive pagine ufficiali.
