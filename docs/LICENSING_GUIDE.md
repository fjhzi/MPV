# Lizenz-Entscheidungshilfe für MPV

Ziel: Eine passende Open-Source-Lizenz wählen, abhängig davon, wie offen Weiterentwicklungen bleiben sollen.

## Kurzvergleich

| Ziel | Geeignete Lizenz | Bedeutung |
|---|---|---|
| Maximale Verbreitung, geringe Hürden | MIT | Sehr permissiv, auch proprietäre Weiterverwendung möglich |
| Verbreitung + explizite Patentklauseln | Apache-2.0 | Wie MIT, aber mit klarerem Patentschutz |
| Änderungen an verteilter Software sollen offen bleiben | GPL-3.0 | Copyleft bei Weitergabe der Software |
| Auch bei gehosteten/Netzwerkdiensten sollen Änderungen offen bleiben | AGPL-3.0 | Stärkeres Copyleft, relevant für SaaS-ähnliche Nutzung |

## Entscheidungsmatrix

### Nimm **MIT** oder **Apache-2.0**, wenn …
- breite Adoption wichtiger ist als „Pflicht zur Offenlegung“ von Änderungen.
- auch kommerzielle/proprietäre Nutzung explizit erlaubt sein soll.

### Nimm **GPL-3.0**, wenn …
- Weiterentwicklungen bei Weitergabe nicht proprietär geschlossen werden sollen.
- Copyleft gewünscht ist, aber primär bei Softwareverteilung.

### Nimm **AGPL-3.0**, wenn …
- du verhindern möchtest, dass gehostete Weiterentwicklungen (z. B. Webbetrieb) geschlossen bleiben.
- Transparenz auch im Netzwerkbetrieb eingefordert werden soll.

## Praktische Empfehlung für MPV

Für ein Community-orientiertes, datenschutzsensibles Studienzentrum-Projekt sind typischerweise zwei Wege sinnvoll:

1. **AGPL-3.0**: Wenn Offenheit aller Weiterentwicklungen (auch bei Hosting) Priorität hat.
2. **Apache-2.0**: Wenn maximale praktische Verbreitung und geringe Hürden Priorität haben.

## Wichtiger Hinweis

Dies ist eine technische Entscheidungshilfe und keine Rechtsberatung. Für verbindliche rechtliche Bewertung sollte eine juristische Prüfung erfolgen.
