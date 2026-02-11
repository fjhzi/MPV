# Deployment (einfach, ohne `runserver`)

Für Studienzentren wird ein Docker-Setup bereitgestellt. Dadurch ist kein manuelles Python-Setup nötig und `python manage.py runserver` entfällt.

## Voraussetzungen

- Docker + Docker Compose Plugin installiert
- Freier Port `8000` auf dem Zielsystem

## Schnellstart

```bash
cp .env.example .env
# SECRET_KEY und ALLOWED_HOSTS in .env anpassen

docker compose -f deploy/docker-compose.yml up -d --build
```

Danach ist MPV erreichbar unter:
- `http://<server>:8000`

## Betrieb

Status prüfen:
```bash
docker compose -f deploy/docker-compose.yml ps
```

Logs ansehen:
```bash
docker compose -f deploy/docker-compose.yml logs -f web
```

Stoppen:
```bash
docker compose -f deploy/docker-compose.yml down
```

## Updates

```bash
git pull

docker compose -f deploy/docker-compose.yml up -d --build
```

## Datenpersistenz

Die Compose-Volumes behalten Daten bei Container-Neustarts:
- `mpv_data` (SQLite-Datenbank)
- `mpv_media` (Uploads)
- `mpv_static` (gesammelte Static Files)

## Produktionshinweise

- `DJANGO_DEBUG=False` setzen
- `DJANGO_SECRET_KEY` stark/zufällig setzen
- `DJANGO_ALLOWED_HOSTS` auf echte Hostnamen/IPs begrenzen
- Für HTTPS einen Reverse Proxy (z. B. Nginx, Traefik) davor setzen
