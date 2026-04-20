# MPV
Medizinproduktverwaltung - Web App für Studienzentren

## Entwicklungsstand
Dies ist ein Django-Prototyp zur lokalen Verwaltung von Medizinprodukten in Studienzentren.
- Dashboard mit Suche, Filtern und tabellarischer Geräteübersicht
- Stammdatenverwaltung (Kategorien, Räume)
- Dokumenten-Upload & Termin-Reminder mit Farblogik
- **Datenbank:** PostgreSQL (im Docker-Container)
- **Webserver:** Gunicorn mit WhiteNoise (für CSS/statische Dateien)

## Planung & Dokumentation
Weitere Details finden sich in:
- `docs/PLANUNG.md` (Fachliche Grundlage)
- `docs/DEPLOYMENT.md` (Erweiterte Details zum Betrieb)
- `SECURITY.md` & `CONTRIBUTING.md`

---

## Installation & Betrieb mit Docker (Empfohlen)
Dies ist der Standardweg für Studienzentren. Voraussetzung ist **Docker Desktop** (Windows).

### 1. Konfiguration
Erstelle eine Datei namens `.env` im Hauptverzeichnis (Basis: `.env.example`).
Inhalt der `.env`:
```env
POSTGRES_DB=mpv_db
POSTGRES_USER=mpv_admin
POSTGRES_PASSWORD=dein_passwort
POSTGRES_HOST=db
POSTGRES_PORT=5432
```
### 2. Windows-Fix (Line Endings)
Damit das Start-Skript im Container fehlerfrei läuft, muss das Format einmalig für Linux korrigiert werden. Führe diesen Befehl in der **PowerShell** aus:
```powershell
(Get-Content scripts/entrypoint.sh) -join "`n" | Set-Content -NoNewline scripts/entrypoint.sh
```
### 3. Starten der Anwendung
Baue die Container und starte sie im Hintergrund:

```powershell
docker compose -f deploy/docker-compose.yml --env-file .env up -d --build
```
### 4. Datenbank einrichten
Initialisiere die Tabellen und erstelle einen Admin-Zugang:

```powershell
# Tabellen anlegen
docker compose -f deploy/docker-compose.yml --env-file .env exec web python manage.py migrate

# Admin-Nutzer erstellen
docker compose -f deploy/docker-compose.yml --env-file .env exec web python manage.py createsuperuser
```
**Erreichbarkeit:**
- Lokal: http://localhost:8000/admin/
- Im Netzwerk: http://[Server-IP]:8000/admin/ 

*(Hinweis: Port 8000 muss ggf. in der Windows-Firewall des Server-PCs für eingehende Verbindungen freigegeben werden.)*
