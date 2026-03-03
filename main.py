import argparse
import os
import sys
from typing import Literal, Dict

from cryptography.fernet import Fernet, InvalidToken

class EnvVault:
    """
    Eine Klasse zur Verwaltung der Verschlüsselung und Entschlüsselung von Umgebungsvariablen-Dateien.
    Verwendet Fernet für symmetrische Verschlüsselung.
    """
    def __init__(self, key: bytes):
        """
        Initialisiert EnvVault mit einem Fernet-Schlüssel.

        :param key: Der Fernet-Schlüssel als Bytes.
        """
        # Der Fernet-Schlüssel muss ein URL-sicherer Base64-kodierter 32-Byte-Schlüssel sein.
        self.fernet = Fernet(key)

    @staticmethod
    def generate_key() -> str:
        """
        Generiert einen neuen, sicheren Fernet-Verschlüsselungsschlüssel.
        Dieser Schlüssel sollte sicher gespeichert und geheim gehalten werden.

        :return: Der generierte Schlüssel als URL-sicherer Base64-String.
        """
        # Fernet.generate_key() erzeugt einen neuen, zufälligen Schlüssel.
        return Fernet.generate_key().decode('utf-8')

    def encrypt_value(self, value: str) -> str:
        """
        Verschlüsselt einen einzelnen String-Wert.

        :param value: Der zu verschlüsselnde Klartext-String.
        :return: Der verschlüsselte Wert als URL-sicherer Base64-String.
        """
        # Der Wert muss vor der Verschlüsselung in Bytes umgewandelt werden.
        encrypted_bytes = self.fernet.encrypt(value.encode('utf-8'))
        # Der verschlüsselte Wert wird wieder in einen String umgewandelt (Base64-kodiert).
        return encrypted_bytes.decode('utf-8')

    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Entschlüsselt einen einzelnen verschlüsselten String-Wert.

        :param encrypted_value: Der verschlüsselte Wert als URL-sicherer Base64-String.
        :return: Der entschlüsselte Klartext-String.
        :raises InvalidToken: Wenn der Schlüssel ungültig ist oder der Token manipuliert wurde.
        """
        try:
            # Der verschlüsselte Wert muss vor der Entschlüsselung in Bytes umgewandelt werden.
            decrypted_bytes = self.fernet.decrypt(encrypted_value.encode('utf-8'))
            # Der entschlüsselte Wert wird wieder in einen String umgewandelt.
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            # Fängt Fehler bei ungültigen oder manipulierten Tokens ab.
            raise ValueError("Ungültiger Token oder falscher Schlüssel. Die Daten konnten nicht entschlüsselt werden.")

    def _parse_env_file(self, file_path: str) -> Dict[str, str]:
        """
        Parst eine .env-ähnliche Datei in ein Dictionary von Schlüssel-Wert-Paaren.
        Ignoriert leere Zeilen und Kommentare (Zeilen, die mit '#').

        :param file_path: Pfad zur Umgebungsvariablen-Datei.
        :return: Dictionary der Umgebungsvariablen.
        """
        env_vars = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Leere Zeilen und Kommentarzeilen ignorieren.
                if not line or line.startswith('#'):
                    continue
                # Zeilen im Format KEY=VALUE parsen.
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars

    def _format_env_vars(self, env_vars: Dict[str, str]) -> str:
        """
        Formatiert ein Dictionary von Umgebungsvariablen zurück in einen .env-Dateistring.

        :param env_vars: Dictionary der Umgebungsvariablen.
        :return: String im .env-Format.
        """
        # Jedes Schlüssel-Wert-Paar wird in eine Zeile KEY=VALUE umgewandelt.
        return "\n".join(f"{key}={value}" for key, value in env_vars.items())

    def process_env_file(self, input_file_path: str, mode: Literal['encrypt', 'decrypt']) -> Dict[str, str]:
        """
        Verarbeitet eine .env-Datei (verschlüsseln oder entschlüsseln) und gibt die verarbeiteten Variablen zurück.

        :param input_file_path: Pfad zur Eingabedatei.
        :param mode: 'encrypt' zum Verschlüsseln, 'decrypt' zum Entschlüsseln.
        :return: Dictionary der verarbeiteten Umgebungsvariablen.
        :raises FileNotFoundError: Wenn die Eingabedatei nicht gefunden wird.
        :raises ValueError: Bei Fehlern während der Ver- oder Entschlüsselung (z.B. ungültiger Token).
        :raises Exception: Bei anderen unerwarteten Fehlern.
        """
        try:
            # Umgebungsvariablen aus der Eingabedatei parsen.
            env_vars = self._parse_env_file(input_file_path)
            processed_env_vars = {}

            for key, value in env_vars.items():
                if mode == 'encrypt':
                    # Wert verschlüsseln und zum Dictionary hinzufügen.
                    processed_env_vars[key] = self.encrypt_value(value)
                else:  # mode == 'decrypt'
                    # Wert entschlüsseln und zum Dictionary hinzufügen.
                    processed_env_vars[key] = self.decrypt_value(value)
            return processed_env_vars
        except FileNotFoundError:
            # Fehler weiterleiten, wenn die Datei nicht existiert.
            raise FileNotFoundError(f"Fehler: Die Datei '{input_file_path}' wurde nicht gefunden.")
        except ValueError as e:
            # Fehler bei der Ver-/Entschlüsselung weiterleiten.
            raise ValueError(f"Fehler bei der {mode}ung: {e}")
        except Exception as e:
            # Allgemeine Fehler abfangen und weiterleiten.
            raise Exception(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

def main():
    """
    Hauptfunktion des CLI-Dienstprogramms EnvVault.
    Parst Kommandozeilenargumente und führt die entsprechende Operation aus.
    """
    parser = argparse.ArgumentParser(
        description="EnvVault: Ein CLI-Dienstprogramm zum Verschlüsseln und Entschlüsseln von Umgebungsvariablen-Dateien."
    )

    # Argument für den Schlüssel, optional über Umgebungsvariable ENVVAULT_KEY.
    parser.add_argument(
        "-k", "--key",
        type=str,
        default=os.environ.get("ENVVAULT_KEY"),
        help="Der Fernet-Verschlüsselungsschlüssel (Base64-kodiert). Kann auch über die Umgebungsvariable ENVVAULT_KEY gesetzt werden."
    )

    # Subparser für verschiedene Befehle (generate-key, encrypt, decrypt).
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Befehle")

    # Subparser für den 'generate-key'-Befehl.
    generate_key_parser = subparsers.add_parser(
        "generate-key",
        help="Generiert einen neuen, sicheren Fernet-Verschlüsselungsschlüssel."
    )

    # Subparser für den 'encrypt'-Befehl.
    encrypt_parser = subparsers.add_parser(
        "encrypt",
        help="Verschlüsselt eine Umgebungsvariablen-Datei."
    )
    encrypt_parser.add_argument(
        "input",
        type=str,
        help="Pfad zur Klartext-Umgebungsvariablen-Datei (z.B. .env)."
    )
    encrypt_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Pfad zur Ausgabedatei für die verschlüsselten Variablen (Standard: <input>.enc)."
    )

    # Subparser für den 'decrypt'-Befehl.
    decrypt_parser = subparsers.add_parser(
        "decrypt",
        help="Entschlüsselt eine Umgebungsvariablen-Datei."
    )
    decrypt_parser.add_argument(
        "input",
        type=str,
        help="Pfad zur verschlüsselten Umgebungsvariablen-Datei (z.B. .env.enc)."
    )
    decrypt_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Pfad zur Ausgabedatei für die entschlüsselten Variablen (Standard: <input>.dec)."
    )
    decrypt_parser.add_argument(
        "-p", "--print",
        action="store_true",
        help="Gibt die entschlüsselten Variablen auf stdout aus, anstatt sie in eine Datei zu schreiben."
    )

    args = parser.parse_args()

    # Befehl 'generate-key' behandeln.
    if args.command == "generate-key":
        key = EnvVault.generate_key()
        print(f"Neuer Fernet-Schlüssel generiert: {key}")
        print("Bewahren Sie diesen Schlüssel sicher auf! Er wird für die Ver- und Entschlüsselung benötigt.")
        sys.exit(0)

    # Überprüfen, ob ein Schlüssel für Ver- und Entschlüsselungsbefehle vorhanden ist.
    if args.command in ["encrypt", "decrypt"]:
        if not args.key:
            # Schlüssel ist zwingend erforderlich für diese Operationen.
            print("Fehler: Ein Fernet-Schlüssel ist erforderlich. Verwenden Sie -k oder setzen Sie ENVVAULT_KEY.", file=sys.stderr)
            sys.exit(1)
        try:
            # Den Schlüssel dekodieren, da Fernet Bytes erwartet.
            fernet_key = args.key.encode('utf-8')
            vault = EnvVault(fernet_key)
        except Exception as e:
            # Fehler beim Initialisieren des Schlüssels abfangen, z.B. bei ungültigem Base64-Format.
            print(f"Fehler: Ungültiger Fernet-Schlüssel. {e}", file=sys.stderr)
            sys.exit(1)

        # Befehl 'encrypt' behandeln.
        if args.command == "encrypt":
            try:
                # Datei verschlüsseln und die verarbeiteten Variablen erhalten.
                processed_vars = vault.process_env_file(args.input, 'encrypt')
                # Ausgabepfad bestimmen.
                output_path = args.output if args.output else f"{args.input}.enc"
                # Verarbeitete Variablen formatieren und in die Ausgabedatei schreiben.
                output_content = vault._format_env_vars(processed_vars)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                print(f"Datei '{args.input}' erfolgreich verschlüsselt nach '{output_path}'.")
                sys.exit(0)
            except (FileNotFoundError, ValueError, Exception) as e:
                # Fehler aus process_env_file abfangen und ausgeben.
                print(e, file=sys.stderr)
                sys.exit(1)

        # Befehl 'decrypt' behandeln.
        elif args.command == "decrypt":
            try:
                # Datei entschlüsseln und die verarbeiteten Variablen erhalten.
                processed_vars = vault.process_env_file(args.input, 'decrypt')
                # Verarbeitete Variablen formatieren.
                output_content = vault._format_env_vars(processed_vars)
                if args.print:
                    # Wenn --print gesetzt ist, auf stdout ausgeben.
                    print(output_content)
                else:
                    # Sonst in eine Ausgabedatei schreiben.
                    output_path = args.output if args.output else f"{args.input}.dec"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(output_content)
                    print(f"Datei '{args.input}' erfolgreich entschlüsselt nach '{output_path}'.")
                sys.exit(0)
            except (FileNotFoundError, ValueError, Exception) as e:
                # Fehler aus process_env_file abfangen und ausgeben.
                print(e, file=sys.stderr)
                sys.exit(1)
    else:
        # Wenn kein Befehl angegeben wurde, Hilfe anzeigen.
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
