# Contributing

Vielen Dank für Ihren Beitrag zu MPV.

## Grundprinzipien

- Kleine, klar abgegrenzte Pull Requests.
- Nachvollziehbare Commit-Messages.
- Änderungen möglichst mit Tests/Checks absichern.
- Dokumentation aktualisieren, wenn Verhalten oder Betrieb betroffen ist.

## Entwicklungssetup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Pull-Request-Checkliste

- [ ] Änderung ist fachlich begründet und im PR beschrieben.
- [ ] Lokale Checks/Tests wurden ausgeführt.
- [ ] Keine sensiblen Daten/Secrets committed.
- [ ] Doku (`README.md`/`docs/`) bei Bedarf ergänzt.

## Issues

- Für Bugs bitte Schritte zur Reproduktion angeben.
- Für Feature-Wünsche bitte Ziel, Nutzen und Akzeptanzkriterien nennen.
