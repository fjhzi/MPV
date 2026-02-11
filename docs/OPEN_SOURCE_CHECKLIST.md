# Open-Source-Checkliste für MPV (Self-Hosting in Studienzentren)

Diese Checkliste hilft dabei, MPV als offene, lokal betreibbare Lösung bereitzustellen, bei der die Datenhoheit vollständig bei den Studienzentren liegt.

## 1. Recht & Lizenz

- [ ] Lizenzmodell festlegen (`MIT`, `Apache-2.0`, `GPL-3.0`, `AGPL-3.0`).
- [ ] `LICENSE`-Datei im Repo ergänzen.
- [ ] Haftungsausschluss im README deutlich machen (Software „as is“).
- [ ] Betreiberverantwortung dokumentieren (Datenschutz, Betrieb, Zugriffskontrolle).

## 2. Repository-Basis (Mindeststandard)

- [ ] `README.md` mit:
  - [ ] Zweck der Software
  - [ ] Zielgruppe (Studienzentren)
  - [ ] Installations- und Update-Anleitung
  - [ ] Sicherheits-Hinweise für Betreiber
  - [ ] Backup/Restore-Hinweise
- [ ] `SECURITY.md` mit Meldeweg und unterstützten Versionen.
- [ ] `CONTRIBUTING.md` mit Entwicklungs- und Review-Regeln.
- [ ] Optional: `CODE_OF_CONDUCT.md` für Community-Zusammenarbeit.
- [ ] Changelog-Strategie festlegen (`CHANGELOG.md`, Releases mit Notes).

## 3. Betriebssicherheit für Self-Hosting

- [ ] Sichere Standardkonfiguration:
  - [ ] `DEBUG=False` in Produktion
  - [ ] starke `SECRET_KEY`-Vorgabe
  - [ ] sichere Cookie-/Session-Settings
- [ ] Rollen/Rechte klar dokumentieren.
- [ ] TLS-Empfehlung und Reverse-Proxy-Setup dokumentieren.
- [ ] Healthchecks und Logging aktivieren.
- [ ] Backup/Restore-Prozess schriftlich dokumentieren und testen.

## 4. Datenhoheit & Datenschutz

- [ ] Daten liegen ausschließlich in der Infrastruktur des Betreibers.
- [ ] Exportpfade für relevante Daten dokumentieren.
- [ ] Aufbewahrungs-/Löschkonzept als Empfehlung für Betreiber beschreiben.
- [ ] Datenschutz-Hinweis: Betreiber ist Verantwortlicher im Sinne der DSGVO.

## 5. Release- und Wartungsmodell

- [ ] Klare Versionierung (SemVer empfohlen).
- [ ] Regelmäßige Security-/Bugfix-Releases.
- [ ] Definierter Weg für Sicherheitsfixes außerhalb des normalen Release-Zyklus.
- [ ] Support-Modell schriftlich festlegen (Best Effort / keine SLA etc.).

## 6. Onboarding für Studienzentren

- [ ] „Erste Schritte“-Guide für IT/Admins des Studienzentrums.
- [ ] Checkliste für produktiven Go-Live (TLS, Backup, Rollen, Updates).
- [ ] Beispielkonfiguration (`.env.example`) und Pflichtvariablen.
- [ ] Bekannte Grenzen/Annahmen der Software dokumentieren.

## 7. Empfohlene Reihenfolge für MPV

1. Lizenz auswählen und `LICENSE` hinzufügen.
2. `README.md`, `SECURITY.md`, `CONTRIBUTING.md` vervollständigen.
3. Self-Hosting-Runbook (Deployment, Backup, Update) dokumentieren.
4. Pilotbetrieb in 1–2 Studienzentren durchführen.
5. Feedback in ein erstes stabiles Open-Source-Release überführen.

---

## Schneller Selbstcheck vor Veröffentlichung

- [ ] Kann ein neues Studienzentrum MPV mit der Doku ohne Rückfragen starten?
- [ ] Ist klar, wie Sicherheitslücken gemeldet werden?
- [ ] Ist klar, wer welche Betriebsverantwortung trägt?
- [ ] Sind Update- und Backup-Prozesse nachvollziehbar beschrieben?
- [ ] Ist die Lizenzentscheidung mit den Projektzielen konsistent?
