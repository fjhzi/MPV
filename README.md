# MPV
Medizinproduktverwaltung - Web App für Studienzentren

## Planung
Die initiale fachliche und technische Planungsgrundlage liegt in:
- `docs/PLANUNG.md`

## Entwicklungsstand (Initialer Prototyp)
Es wurde ein erster Django-Prototyp mit folgenden Bereichen erstellt:
- Dashboard mit Suche, Filtern und tabellarischer Geräteübersicht
- CRUD für Medizinprodukte
- Stammdatenverwaltung für Kategorien und Räume
- Dokumenten-Upload pro Kategorie
- Termine pro Medizinprodukt und Reminder-Seite mit Farblogik

## Lokal starten
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py runserver
```

Dann öffnen:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Open-Source-Betrieb für Studienzentren
Für die Vorbereitung eines offenen, selbst gehosteten Betriebsmodells siehe:
- `docs/OPEN_SOURCE_CHECKLIST.md`
- `docs/LICENSING_GUIDE.md`
- `SECURITY.md`
- `CONTRIBUTING.md`


## Deployment ohne runserver (für Studienzentren)
Empfohlen ist Docker Compose statt `python manage.py runserver`:

```bash
cp .env.example .env
docker compose -f deploy/docker-compose.yml up -d --build
```

Details: `docs/DEPLOYMENT.md`
