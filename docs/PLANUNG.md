# Produkt- und Umsetzungsplanung: MPV (Medizinproduktverwaltung)

## 1) Zielbild
Eine moderne Webanwendung für Studienzentren in Deutschland zur zentralen Verwaltung von Medizinprodukten inklusive:
- Dashboard mit durchsuchbarer und filterbarer Haupttabelle.
- Vollständigem Lebenszyklus pro Medizinprodukt (anlegen, bearbeiten, Detailansicht).
- Frei verwaltbaren Stammdaten (Kategorien, Räume).
- Dokumentenmanagement auf Kategorie-Ebene mit Verknüpfung zu Produkten.
- Terminverwaltung (z. B. Kalibrierung/Wartung) mit Reminder-Übersicht.

## 2) Kernnutzer und Nutzungskontext
- **Studienkoordinator:innen**: Überblick über alle Geräte, schnelle Suche, Statuskontrolle.
- **Technik/Biomedizin**: Wartung, Kalibrierung, Defekte dokumentieren und nachverfolgen.
- **Qualitätsmanagement**: CE-Informationen, Dokumentation, Auditfähigkeit.

## 3) Funktionsumfang (MVP)

### 3.1 Dashboard + Haupttabelle
- Liste aller Medizinprodukte eines Studienzentrums.
- **Suche** (global, z. B. über Bezeichnung, Seriennummer, Gerätenummer, Hersteller).
- **Filter** mindestens nach:
  - Kategorie
  - Raum / Raumnummer
  - Status (aktiv / nicht aktiv)
  - Zustand (defekt / funktionsfähig)
- Sortierung, Paginierung, Spaltenauswahl.
- Zeilenklick öffnet Detailansicht.

### 3.2 Medizinprodukt-Verwaltung (CRUD)
Pro Medizinprodukt erfassbar:
- Bezeichnung
- Kategorie (aus Stammdaten)
- Raum (aus Stammdaten)
- Status (aktiv / nicht aktiv)
- Zustand (defekt / funktionsfähig)
- Seriennummer
- Gerätenummer der Kohorte
- Hersteller
- CE-Kennzeichnung
- Lieferdatum
- Kontaktdaten
- Notizen

Aktionen:
- Anlegen
- Bearbeiten
- Löschen
- Detailansicht

### 3.3 Stammdatenverwaltung
- **Kategorien** können von Nutzer:innen selbst erstellt/editiert werden.
- **Räume** können von Nutzer:innen selbst erstellt/editiert werden.
- Dublettenprüfung (z. B. gleicher Name im selben Zentrum).

### 3.4 Dokumentenbereich pro Kategorie
- Upload per Dateidialog und Drag-and-Drop.
- Dokumente sind einer Kategorie zugeordnet und erscheinen automatisch in allen Produkt-Detailansichten dieser Kategorie.
- Klick auf Dokument öffnet Vorschau/Download in neuem Fenster/Tab.
- Validierung (Dateityp, maximale Größe).
- Zugelassene Dateitypen: `pdf`, `doc`, `docx`, `txt`, `png`, `jpg`.
- Serverseitige Speicheroptimierung/Kompression, sofern fachlich zulässig.

### 3.5 Termine + Reminder
- In jeder Produkt-Detailansicht: Termine anlegen (z. B. Kalibrierung, Wartung).
- Felder je Termin: Terminart, Datum, optional Notiz/Verantwortliche.
- Reminder-Seite außerhalb des Dashboards:
  - „Nächste fällige Termine“ (z. B. heute, nächste 7/30 Tage, überfällig).
  - Pro Termin/Produkt wird angezeigt, in wie vielen Tagen der Termin ansteht (negativer Wert bzw. „überfällig“, wenn Datum überschritten ist).
  - Visuelle Hervorhebung in der Reminder-Tabelle:
    - **Rot**, wenn Termin überfällig ist.
    - **Gelb**, wenn Termin innerhalb der nächsten 30 Tage fällig wird.
  - Filterbar nach Zeitraum, Kategorie, Raum, Status.

## 4) Datenmodell (fachlich)

### 4.1 Entitäten
- **StudyCenter**
- **MedicalDevice**
- **Category**
- **Room**
- **CategoryDocument**
- **DeviceAppointment**
- **User**

### 4.2 Beziehungen
- Ein StudyCenter hat viele MedicalDevices, Categories, Rooms, Users.
- Ein MedicalDevice gehört genau einer Category und optional einem Room.
- Eine Category hat viele CategoryDocuments.
- Ein MedicalDevice hat viele DeviceAppointments.
- CategoryDocuments sind indirekt mit Devices verknüpft (über Category).

### 4.3 Beispiel-Felder (technisch)
- MedicalDevice:
  - id, study_center_id, category_id, room_id
  - name, serial_number, cohort_device_number
  - manufacturer, ce_marking, delivery_date
  - is_active, is_defective
  - contact_data, notes
  - created_at, updated_at
- DeviceAppointment:
  - id, medical_device_id, type, due_date, note, status

## 5) UX/UI-Leitlinien („neuester Standard“)
- Responsive Design (Desktop-first, Tablet-tauglich).
- Klare Informationshierarchie, große klickbare Flächen, gute Lesbarkeit.
- Barrierearm nach WCAG-orientierten Prinzipien (Kontrast, Fokuszustände, Tastaturbedienung).
- Konsistente Formulare mit Inline-Validierung.
- Tabellen-UX mit Sticky Header, schnelle Filterchips, gespeicherte Filteransichten.
- Leere Zustände, Ladezustände, Fehlermeldungen klar und hilfreich.

## 6) Nicht-funktionale Anforderungen
- Mandantenfähigkeit pro Studienzentrum (Daten strikt getrennt).
- Rollen-/Rechtekonzept (mindestens Admin, Editor, Viewer).
- DSGVO-konforme Datenspeicherung und Zugriffskontrolle.
- Nachvollziehbarkeit (Audit-Log für kritische Änderungen).
- Performance-Ziel: Tabelleninteraktion und Suche < 300 ms bei üblicher Datenmenge.

## 7) Technische Entscheidungsleitplanken (Vorschlag)
- Frontend: modernes Component-Framework (z. B. React + TypeScript).
- Backend: REST oder GraphQL mit sauberem Domain-Modell.
- Datenbank: relational (z. B. PostgreSQL) wegen klarer Beziehungen/Filter.
- Dateiablage: Object Storage (lokal/S3-kompatibel) + Metadaten in DB.
- Suche/Filter: serverseitig, indexgestützt.
- Dokumentenkompression:
  - Bilder/PDFs optimieren beim Upload (verlustarm, konfigurierbar).
  - Original optional aufbewahren (Compliance-abhängig).

## 8) MVP-Backlog in Phasen

### Phase 1: Fundament
- Authentifizierung + Rollen
- Mandantenstruktur (Studienzentrum)
- Stammdaten: Kategorien, Räume

### Phase 2: Geräteverwaltung
- CRUD für Medizinprodukte
- Dashboard-Tabelle mit Suche/Filtern
- Sortierung über klickbaren Spalten-Header (aufsteigend/absteigend)
- Detailansicht (ohne Termine/Dokumente)

### Phase 3: Dokumente + Termine
- Kategorie-Dokumentenbereich inkl. Upload (Dialog + Drag-and-Drop)
- Verlinkung der Kategorie-Dokumente in Produktdetail
- Termine in Produktdetail
- Reminder-Seite

### Phase 4: Qualität und Feinschliff
- Audit-Log, Exporte, bessere Sortier-/Filteroptionen
- UX-Polishing, Accessibility-Tests, Performance-Optimierung

## 9) Offene fachliche Entscheidungen
- Maximale Dokumentgröße und Upload-Limits (pro Datei / pro Kategorie).
- Erinnerungslogik (nur Anzeige vs. E-Mail/Push-Benachrichtigung).
- Definition „Status“ vs. „Zustand“ final abstimmen.
- Lebenszyklus von Räumen/Kategorien bei Löschung (Soft-Delete, Sperre, Migration).

## 10) Festgelegte Basisregeln
- Pflichtfelder beim Anlegen eines Medizinprodukts: **Bezeichnung**, **Seriennummer**, **Kategorie**.
- Zugelassene Dokument-Dateitypen: **pdf, doc, docx, txt, png, jpg**.

## 11) Vorschlag für nächste Planungsschritte (ohne Coding)
1. Fachliches Review dieses Dokuments mit Stakeholdern.
2. Priorisierung MVP vs. Nice-to-have.
3. Klickbarer UX-Prototyp (Dashboard, Detailansicht, Reminder).
4. Ableitung in User Stories inkl. Akzeptanzkriterien.
5. Technische Architekturentscheidung und Sprint-Planung.
