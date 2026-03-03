# EnvVault CLI: Sichere Verwaltung von Umgebungsvariablen

[![Python CI/CD](https://github.com/your-username/env-vault-cli/actions/workflows/python-app.yml/badge.svg)](https://github.com/your-username/env-vault-cli/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

EnvVault CLI ist ein unternehmenstaugliches Open-Source-Kommandozeilen-Dienstprogramm, das entwickelt wurde, um in `.env`-Dateien gespeicherte Umgebungsvariablen sicher zu ver- und entschlüsseln. Es wurde für Entwickler, DevOps-Ingenieure und CI/CD-Pipelines entwickelt, die eine robuste Lösung für die Verwaltung sensibler Konfigurationsdaten benötigen.

## Funktionen

*   **Symmetrische Verschlüsselung**: Nutzt die Fernet-Implementierung der `cryptography`-Bibliothek für eine starke, authentifizierte symmetrische Verschlüsselung.
*   **Schlüsselgenerierung**: Generieren Sie einfach sichere Fernet-Schlüssel direkt über die CLI.
*   **Dateibasierte Ver-/Entschlüsselung**: Verschlüsseln Sie ganze `.env`-Dateien und entschlüsseln Sie diese zurück in Klartext.
*   **CLI-freundlich**: Intuitive Kommandozeilenschnittstelle mit klaren Optionen für verschiedene Operationen.
*   **Unterstützung von Umgebungsvariablen**: Übergeben Sie den Verschlüsselungsschlüssel sicher über eine Umgebungsvariable (`ENVVAULT_KEY`).
*   **Ausgabe auf Stdout**: Entschlüsseln Sie Geheimnisse und geben Sie diese direkt auf der Konsole aus, um sie in Skripten zu verwenden, ohne temporäre Dateien zu erstellen.
*   **Plattformübergreifend**: Mit Python erstellt, wodurch die Kompatibilität mit verschiedenen Betriebssystemen gewährleistet ist.

## Installation

1.  **Voraussetzungen**:
    *   Python 3.8+ auf Ihrem System installiert.

2.  **Installation von PyPI (Demnächst verfügbar)**:
    ```bash
    pip install env-vault-cli
    ```

3.  **Manuelle Installation (vom Quellcode)**:
    ```bash
    git clone https://github.com/your-username/env-vault-cli.git
    cd env-vault-cli
    python3 -m venv venv
    source venv/bin/activate # Unter Windows: .\venv\Scripts\activate
    pip install -r requirements.txt
    # CLI verfügbar machen (optional, für die Entwicklung)
    # python3 -m pip install -e .
    ```

## Verwendung

### 1. Neuen Verschlüsselungsschlüssel generieren

Generieren Sie zunächst einen starken Fernet-Schlüssel. **Bewahren Sie diesen Schlüssel sicher auf!** Er ist sowohl für die Ver- als auch für die Entschlüsselung unerlässlich.

```bash
python main.py generate-key
# Die Ausgabe wird etwa so aussehen:
# Neuer Fernet-Schlüssel generiert: <IHR_SICHERER_FERNET_SCHLUESSEL_HIER>
# Bewahren Sie diesen Schlüssel sicher auf! Er wird für die Ver- und Entschlüsselung benötigt.
```

Exportieren Sie diesen Schlüssel als Umgebungsvariable (`ENVVAULT_KEY`) oder übergeben Sie ihn direkt mit dem Flag `-k` für nachfolgende Operationen. Die Verwendung einer Umgebungsvariablen wird aus Sicherheitsgründen empfohlen.

```bash
export ENVVAULT_KEY="<IHR_SICHERER_FERNET_SCHLUESSEL_HIER>"
```

### 2. Eine Umgebungsvariablen-Datei verschlüsseln

Angenommen, Sie haben eine `.env`-Datei:

`my_app/.env`:
```env
DATABASE_URL=postgres://user:pass@host:5432/db
API_KEY=your_super_secret_api_key
DEBUG=False
```

Zum Verschlüsseln:

```bash
python main.py encrypt my_app/.env -o my_app/.env.enc
# Oder, wenn ENVVAULT_KEY nicht gesetzt ist:
# python main.py encrypt my_app/.env -o my_app/.env.enc -k "<IHR_SICHERER_FERNET_SCHLUESSEL_HIER>"
```

Dadurch wird `my_app/.env.enc` mit verschlüsselten Werten erstellt:

`my_app/.env.enc`:
```env
DATABASE_URL=gAAAAABl... (langer verschlüsselter String)
API_KEY=gAAAAABl... (langer verschlüsselter String)
DEBUG=gAAAAABl... (langer verschlüsselter String)
```

### 3. Eine verschlüsselte Datei entschlüsseln

Um `my_app/.env.enc` wieder in eine neue Datei `my_app/.env.dec` zu entschlüsseln:

```bash
python main.py decrypt my_app/.env.enc -o my_app/.env.dec
```

`my_app/.env.dec` enthält dann die ursprünglichen Klartextvariablen.

### 4. Entschlüsseln und auf die Standardausgabe ausgeben

Dies ist nützlich, um Geheimnisse direkt in andere Befehle zu leiten oder für eine schnelle Überprüfung, ohne eine physische Datei zu erstellen.

```bash
python main.py decrypt my_app/.env.enc --print
# Die Ausgabe wird sein:
# DATABASE_URL=postgres://user:pass@host:5432/db
# API_KEY=your_super_secret_api_key
# DEBUG=False
```

## Sicherheitsüberlegungen

*   **Schlüsselverwaltung**: Die Sicherheit Ihrer verschlüsselten Umgebungsvariablen hängt direkt von der Sicherheit Ihres Fernet-Schlüssels ab. **Geben Sie Ihren Verschlüsselungsschlüssel niemals in die Versionskontrolle.** Speichern Sie ihn an einem sicheren Ort (z.B. einem dedizierten Geheimnismanager, KMS oder einem sicheren System zur Injektion von Umgebungsvariablen für CI/CD).
*   **Umgebungsvariablen**: Wenn Sie den `ENVVAULT_KEY` über eine Umgebungsvariable übergeben, beachten Sie, dass er für andere Prozesse auf demselben Computer sichtbar sein könnte. Für hochsensible Umgebungen sollten Sie eine sicherere Methode zur Schlüsselinjektion in Betracht ziehen, die von Ihrem Orchestrator- oder CI/CD-System bereitgestellt wird.
*   **Dateiberechtigungen**: Stellen Sie sicher, dass Ihre `.env`- und `.env.enc`-Dateien über geeignete Dateiberechtigungen verfügen, um unbefugten Zugriff zu verhindern.

## Mitwirken

Wir freuen uns über Beiträge! Details zur Vorgehensweise finden Sie in unserer [CONTRIBUTING.md](CONTRIBUTING.md).

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert – weitere Details finden Sie in der Datei [LICENSE](LICENSE).
