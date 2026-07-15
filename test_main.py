import pytest
import os
import sys
import json
from unittest.mock import patch, mock_open
from io import StringIO

from cryptography.fernet import Fernet, InvalidToken

# Importieren der zu testenden Komponenten aus main.py
from main import EnvVault, main, load_config, _resolve_key, EnvVaultConfigError

# Ein fester Testschlüssel für konsistente Tests
# Dies ist ein gültiger Fernet-Schlüssel, der für Tests verwendet wird.
TEST_KEY = Fernet.generate_key().decode('utf-8')

# Mock-Implementierung der Fernet-Klasse, um Kryptografie-Operationen zu simulieren
# und Tests isolierter und schneller zu machen.
class MockFernet:
    def __init__(self, key):
        # Speichert den Schlüssel, um zu überprüfen, ob er korrekt übergeben wurde.
        self._key = key

    def encrypt(self, value: bytes) -> bytes:
        # Simuliert die Verschlüsselung durch Hinzufügen eines Präfixes.
        return b"MOCKED_ENCRYPTED_" + value

    def decrypt(self, encrypted_value: bytes) -> bytes:
        # Simuliert die Entschlüsselung durch Entfernen des Präfixes.
        # Überprüft, ob der Wert mit dem erwarteten Präfix beginnt.
        if not encrypted_value.startswith(b"MOCKED_ENCRYPTED_"):
            raise InvalidToken("Mock: Token ist ungültig oder wurde manipuliert.")
        return encrypted_value[len(b"MOCKED_ENCRYPTED_"):]

@pytest.fixture
def env_vault_instance(mock_fernet_patch):
    """Fixture für eine EnvVault-Instanz mit einem Testschlüssel."""
    # Erstellt eine EnvVault-Instanz mit dem TEST_KEY.
    return EnvVault(TEST_KEY.encode('utf-8'))

@pytest.fixture
def mock_fernet_patch():
    """Patcht Fernet.generate_key und Fernet.__init__ für konsistente Tests."""
    # Ersetzt die echte Fernet-Klasse durch unsere MockFernet-Implementierung.
    with patch('main.Fernet') as mock_fernet_cls:
        # Konfiguriert die Mock-Fernet-Klasse, um eine MockFernet-Instanz zurückzugeben.
        mock_fernet_cls.return_value = MockFernet(TEST_KEY.encode('utf-8'))
        # Stellt sicher, dass generate_key auch einen konsistenten Wert zurückgibt.
        mock_fernet_cls.generate_key.return_value = TEST_KEY.encode('utf-8')
        yield mock_fernet_cls

def test_generate_key():
    """Testet die Schlüsselgenerierungsfunktion."""
    # Ruft die statische Methode generate_key auf.
    key = EnvVault.generate_key()
    # Überprüft, ob der zurückgegebene Schlüssel ein String ist und eine Länge hat.
    assert isinstance(key, str)
    assert len(key) > 0
    # Stellt sicher, dass der generierte Schlüssel ein gültiger Base64-String für Fernet ist.
    Fernet(key.encode('utf-8'))

def test_encrypt_value(env_vault_instance, mock_fernet_patch):
    """Testet die Verschlüsselung eines einzelnen Wertes."""
    plaintext = "mysecretvalue"
    # Verschlüsselt den Klartextwert.
    encrypted = env_vault_instance.encrypt_value(plaintext)
    # Vergleicht das Ergebnis mit dem erwarteten Mock-Output.
    assert encrypted == "MOCKED_ENCRYPTED_mysecretvalue"

def test_decrypt_value(env_vault_instance, mock_fernet_patch):
    """Testet die Entschlüsselung eines einzelnen Wertes."""
    encrypted = "MOCKED_ENCRYPTED_mysecretvalue"
    # Entschlüsselt den verschlüsselten Wert.
    plaintext = env_vault_instance.decrypt_value(encrypted)
    # Vergleicht das Ergebnis mit dem erwarteten Klartext.
    assert plaintext == "mysecretvalue"

def test_decrypt_value_invalid_token(env_vault_instance, mock_fernet_patch):
    """Testet die Entschlüsselung mit einem ungültigen Token."""
    invalid_encrypted = "INVALID_TOKEN_mysecretvalue"
    # Erwartet, dass ein ValueError ausgelöst wird, wenn der Token ungültig ist.
    with pytest.raises(ValueError, match="Ungültiger Token oder falscher Schlüssel"):
        env_vault_instance.decrypt_value(invalid_encrypted)

def test_parse_env_file(env_vault_instance):
    """Testet das Parsen einer .env-Datei."""
    mock_file_content = "KEY1=value1\n# Kommentar\nKEY2=value2 with spaces\n\nKEY3 = some_value\n"
    # Patcht 'builtins.open', um den Dateiinhalt zu simulieren.
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Parst die simulierte Datei.
        parsed_vars = env_vault_instance._parse_env_file("dummy.env")
        # Überprüft, ob die Variablen korrekt geparst wurden.
        assert parsed_vars == {
            "KEY1": "value1",
            "KEY2": "value2 with spaces",
            "KEY3": "some_value"
        }

def test_format_env_vars(env_vault_instance):
    """Testet das Formatieren von Umgebungsvariablen in einen String."""
    env_vars = {
        "KEY1": "value1",
        "KEY2": "value2"
    }
    # Formatiert das Dictionary in einen .env-String.
    formatted_string = env_vault_instance._format_env_vars(env_vars)
    # Überprüft, ob der String korrekt formatiert ist.
    assert formatted_string == "KEY1=value1\nKEY2=value2"

def test_process_env_file_encrypt(env_vault_instance, mock_fernet_patch, tmp_path):
    """Testet die Verschlüsselung einer gesamten Datei."""
    # Erstellt eine temporäre Eingabedatei.
    input_file = tmp_path / "test.env"
    input_file.write_text("VAR1=plain1\nVAR2=plain2")
    
    # Verarbeitet die Datei im Verschlüsselungsmodus.
    processed_vars = env_vault_instance.process_env_file(str(input_file), 'encrypt')
    # Überprüft, ob die Variablen korrekt verschlüsselt wurden (mit Mock-Output).
    assert processed_vars == {
        "VAR1": "MOCKED_ENCRYPTED_plain1",
        "VAR2": "MOCKED_ENCRYPTED_plain2"
    }

def test_process_env_file_decrypt(env_vault_instance, mock_fernet_patch, tmp_path):
    """Testet die Entschlüsselung einer gesamten Datei."""
    # Erstellt eine temporäre Eingabedatei mit Mock-verschlüsselten Inhalten.
    input_file = tmp_path / "test.env.enc"
    input_file.write_text("VAR1=MOCKED_ENCRYPTED_plain1\nVAR2=MOCKED_ENCRYPTED_plain2")

    # Verarbeitet die Datei im Entschlüsselungsmodus.
    processed_vars = env_vault_instance.process_env_file(str(input_file), 'decrypt')
    # Überprüft, ob die Variablen korrekt entschlüsselt wurden (mit Mock-Output).
    assert processed_vars == {
        "VAR1": "plain1",
        "VAR2": "plain2"
    }

def test_process_env_file_not_found(env_vault_instance):
    """Testet das Verhalten, wenn die Eingabedatei nicht existiert."""
    # Erwartet, dass ein FileNotFoundError ausgelöst wird.
    with pytest.raises(FileNotFoundError, match="wurde nicht gefunden"):
        env_vault_instance.process_env_file("non_existent.env", 'encrypt')

# CLI-Tests für die main-Funktion
@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {'ENVVAULT_KEY': TEST_KEY})
def test_cli_generate_key(mock_stderr, mock_stdout):
    """Testet den CLI-Befehl 'generate-key'."""
    # Simuliert Kommandozeilenargumente.
    with patch('sys.argv', ['main.py', 'generate-key']):
        # Patcht Fernet.generate_key, um einen vorhersagbaren Schlüssel zurückzugeben.
        with patch('main.Fernet.generate_key', return_value=b'some_generated_key_for_test'):
            # Erwartet, dass das Programm mit SystemExit (Code 0) beendet wird.
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0
            # Überprüft die Standardausgabe.
            output = mock_stdout.getvalue()
            assert "Neuer Fernet-Schlüssel generiert" in output
            assert "some_generated_key_for_test" in output

@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {'ENVVAULT_KEY': TEST_KEY})
@patch('main.Fernet', new=MockFernet) # Verwendet unsere MockFernet für CLI-Tests
def test_cli_encrypt_command(mock_stderr, mock_stdout, tmp_path):
    """Testet den CLI-Befehl 'encrypt'."""
    input_file = tmp_path / "test.env"
    output_file = tmp_path / "test.env.enc"
    input_file.write_text("USER=testuser\nPASS=testpass")

    # Simuliert Kommandozeilenargumente für den Verschlüsselungsbefehl.
    with patch('sys.argv', ['main.py', 'encrypt', str(input_file), '-o', str(output_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
        output = mock_stdout.getvalue()
        # Überprüft die Erfolgsmeldung und den Inhalt der Ausgabedatei.
        assert f"Datei '{input_file}' erfolgreich verschlüsselt nach '{output_file}'." in output
        assert output_file.read_text() == "USER=MOCKED_ENCRYPTED_testuser\nPASS=MOCKED_ENCRYPTED_testpass"

@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {'ENVVAULT_KEY': TEST_KEY})
@patch('main.Fernet', new=MockFernet)
def test_cli_decrypt_command_to_file(mock_stderr, mock_stdout, tmp_path):
    """Testet den CLI-Befehl 'decrypt' und schreibt in eine Datei."""
    input_file = tmp_path / "test.env.enc"
    output_file = tmp_path / "test.env.dec"
    input_file.write_text("USER=MOCKED_ENCRYPTED_testuser\nPASS=MOCKED_ENCRYPTED_testpass")

    # Simuliert Kommandozeilenargumente für den Entschlüsselungsbefehl (Ausgabe in Datei).
    with patch('sys.argv', ['main.py', 'decrypt', str(input_file), '-o', str(output_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
        output = mock_stdout.getvalue()
        # Überprüft die Erfolgsmeldung und den Inhalt der Ausgabedatei.
        assert f"Datei '{input_file}' erfolgreich entschlüsselt nach '{output_file}'." in output
        assert output_file.read_text() == "USER=testuser\nPASS=testpass"

@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {'ENVVAULT_KEY': TEST_KEY})
@patch('main.Fernet', new=MockFernet)
def test_cli_decrypt_command_print(mock_stderr, mock_stdout, tmp_path):
    """Testet den CLI-Befehl 'decrypt' mit der Option '--print'."""
    input_file = tmp_path / "test.env.enc"
    input_file.write_text("USER=MOCKED_ENCRYPTED_testuser\nPASS=MOCKED_ENCRYPTED_testpass")

    # Simuliert Kommandozeilenargumente für den Entschlüsselungsbefehl (Ausgabe auf stdout).
    with patch('sys.argv', ['main.py', 'decrypt', str(input_file), '--print']):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
        output = mock_stdout.getvalue()
        # Überprüft, ob der entschlüsselte Inhalt auf stdout ausgegeben wird.
        assert "USER=testuser\nPASS=testpass" in output
        # Bei --print sollte keine Erfolgsmeldung ausgegeben werden.
        assert "erfolgreich entschlüsselt" not in output

@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {}) # Keine ENVVAULT_KEY Umgebungsvariable gesetzt
def test_cli_missing_key(mock_stderr, mock_stdout, tmp_path):
    """Testet das Verhalten, wenn der Schlüssel für Ver-/Entschlüsselung fehlt."""
    input_file = tmp_path / "test.env"
    input_file.write_text("VAR=value")
    
    # Simuliert den Verschlüsselungsbefehl ohne Angabe eines Schlüssels.
    with patch('sys.argv', ['main.py', 'encrypt', str(input_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        error_output = mock_stderr.getvalue()
        # Überprüft, ob die Fehlermeldung für fehlenden Schlüssel ausgegeben wird.
        assert "Fehler: Ein Fernet-Schlüssel ist erforderlich." in error_output

@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {'ENVVAULT_KEY': 'invalid-key'}) # Ungültiges Base64-Format
def test_cli_invalid_key_format(mock_stderr, mock_stdout, tmp_path):
    """Testet das Verhalten bei einem ungültig formatierten Schlüssel."""
    input_file = tmp_path / "test.env"
    input_file.write_text("VAR=value")
    
    # Simuliert den Verschlüsselungsbefehl mit einem ungültig formatierten Schlüssel.
    with patch('sys.argv', ['main.py', 'encrypt', str(input_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        error_output = mock_stderr.getvalue()
        # Überprüft die Fehlermeldung für einen ungültigen Fernet-Schlüssel.
        assert "Fehler: Ungültiger Fernet-Schlüssel." in error_output

@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('os.environ', {'ENVVAULT_KEY': TEST_KEY})
@patch('main.Fernet', new=MockFernet)
def test_cli_decrypt_invalid_content(mock_stderr, mock_stdout, tmp_path):
    """Testet den CLI-Befehl 'decrypt' mit manipulierten/ungültigen Inhalten."""
    input_file = tmp_path / "test.env.enc"
    # Eine Zeile ist gültig, die andere ist manipuliert (kein Mock-Präfix).
    input_file.write_text("VAR1=MOCKED_ENCRYPTED_plain1\nVAR2=INVALID_ENCRYPTED_plain2")

    # Simuliert den Entschlüsselungsbefehl mit manipulierten Inhalten.
    with patch('sys.argv', ['main.py', 'decrypt', str(input_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        error_output = mock_stderr.getvalue()
        # Überprüft die Fehlermeldung, die von der MockFernet-Klasse ausgelöst wird.
        assert "Fehler bei der decryptung: Ungültiger Token oder falscher Schlüssel." in error_output


# --- Test JSON configuration file support ---
def test_load_config_reads_json_object(tmp_path):
    """Eine gültige JSON-Config wird als Dictionary geladen."""
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"key_file": "k.key", "output": "out.enc"}))
    assert load_config(str(cfg)) == {"key_file": "k.key", "output": "out.enc"}


def test_load_config_missing_explicit_raises(tmp_path):
    """Eine explizit angeforderte, fehlende Config ist ein Fehler."""
    with pytest.raises(EnvVaultConfigError, match="not found"):
        load_config(str(tmp_path / "nope.json"))


def test_load_config_invalid_json_raises(tmp_path):
    """Ungültiges JSON löst einen Fehler aus."""
    cfg = tmp_path / "bad.json"
    cfg.write_text("{not valid json}")
    with pytest.raises(EnvVaultConfigError, match="Could not read configuration file"):
        load_config(str(cfg))


def test_load_config_non_object_raises(tmp_path):
    """Eine JSON-Datei, die kein Objekt ist, wird abgelehnt."""
    cfg = tmp_path / "list.json"
    cfg.write_text(json.dumps([1, 2, 3]))
    with pytest.raises(EnvVaultConfigError, match="must contain a JSON object"):
        load_config(str(cfg))


def test_load_config_rejects_raw_key(tmp_path):
    """Ein roher Schlüssel in der Config wird aus Sicherheitsgründen abgelehnt."""
    cfg = tmp_path / "secret.json"
    cfg.write_text(json.dumps({"key": "leaked"}))
    with pytest.raises(EnvVaultConfigError, match="must not contain a raw key"):
        load_config(str(cfg))


def test_load_config_default_absent_returns_empty(tmp_path, monkeypatch):
    """Fehlt die implizite Standarddatei, wird eine leere Config geliefert."""
    monkeypatch.chdir(tmp_path)  # Verzeichnis ohne .envvault.json
    monkeypatch.delenv("ENVVAULT_CONFIG", raising=False)
    assert load_config(None) == {}


def test_resolve_key_precedence(tmp_path):
    """Vorrang des Schlüsselmaterials: --key > Config key_file > ENVVAULT_KEY."""
    key_file = tmp_path / "k.key"
    key_file.write_text("KEY_FROM_FILE")

    # 1. CLI-Flag gewinnt gegen Config und Env.
    with patch.dict(os.environ, {"ENVVAULT_KEY": "KEY_FROM_ENV"}, clear=True):
        assert _resolve_key("KEY_FROM_CLI", {"key_file": str(key_file)}) == "KEY_FROM_CLI"
    # 2. Config-Schlüsseldatei gewinnt gegen Env.
    with patch.dict(os.environ, {"ENVVAULT_KEY": "KEY_FROM_ENV"}, clear=True):
        assert _resolve_key(None, {"key_file": str(key_file)}) == "KEY_FROM_FILE"
    # 3. Ohne Flag/Config kommt der Schlüssel aus der Umgebung.
    with patch.dict(os.environ, {"ENVVAULT_KEY": "KEY_FROM_ENV"}, clear=True):
        assert _resolve_key(None, {}) == "KEY_FROM_ENV"
    # 4. Nichts gesetzt -> None.
    with patch.dict(os.environ, {}, clear=True):
        assert _resolve_key(None, {}) is None


def test_resolve_key_missing_config_key_file_raises(tmp_path):
    """Eine in der Config referenzierte, fehlende Schlüsseldatei ist ein Fehler."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvVaultConfigError, match="referenced in config not found"):
            _resolve_key(None, {"key_file": str(tmp_path / "missing.key")})


@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('main.Fernet', new=MockFernet)
def test_cli_encrypt_with_config_key_file(mock_stderr, mock_stdout, tmp_path):
    """encrypt liest den Schlüssel über die in der Config referenzierte Datei (ohne -k/Env)."""
    key_file = tmp_path / "vault.key"
    key_file.write_text(TEST_KEY)
    config_file = tmp_path / ".envvault.json"
    config_file.write_text(json.dumps({"key_file": str(key_file)}))

    input_file = tmp_path / "test.env"
    output_file = tmp_path / "test.env.enc"
    input_file.write_text("USER=testuser\nPASS=testpass")

    argv = ['main.py', '--config', str(config_file), 'encrypt', str(input_file), '-o', str(output_file)]
    with patch.dict(os.environ, {}, clear=True):  # kein ENVVAULT_KEY
        with patch('sys.argv', argv):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0, mock_stderr.getvalue()
            assert output_file.read_text() == "USER=MOCKED_ENCRYPTED_testuser\nPASS=MOCKED_ENCRYPTED_testpass"


@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('main.Fernet', new=MockFernet)
def test_cli_encrypt_output_from_config(mock_stderr, mock_stdout, tmp_path):
    """Der Ausgabepfad wird aus der Config gelesen, wenn -o fehlt."""
    config_out = tmp_path / "configured_output.enc"
    config_file = tmp_path / ".envvault.json"
    config_file.write_text(json.dumps({"output": str(config_out)}))

    input_file = tmp_path / "test.env"
    input_file.write_text("USER=testuser")

    argv = ['main.py', '--config', str(config_file), 'encrypt', str(input_file)]
    with patch.dict(os.environ, {"ENVVAULT_KEY": TEST_KEY}, clear=True):
        with patch('sys.argv', argv):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0, mock_stderr.getvalue()
            assert config_out.exists()
            assert config_out.read_text() == "USER=MOCKED_ENCRYPTED_testuser"


@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
@patch('main.Fernet', new=MockFernet)
def test_cli_flag_output_overrides_config(mock_stderr, mock_stdout, tmp_path):
    """-o hat Vorrang vor dem 'output' aus der Config."""
    config_out = tmp_path / "config_out.enc"
    flag_out = tmp_path / "flag_out.enc"
    config_file = tmp_path / ".envvault.json"
    config_file.write_text(json.dumps({"output": str(config_out)}))

    input_file = tmp_path / "test.env"
    input_file.write_text("USER=testuser")

    argv = ['main.py', '--config', str(config_file), 'encrypt', str(input_file), '-o', str(flag_out)]
    with patch.dict(os.environ, {"ENVVAULT_KEY": TEST_KEY}, clear=True):
        with patch('sys.argv', argv):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0, mock_stderr.getvalue()
            assert flag_out.exists()
            assert not config_out.exists()


@patch('sys.stdout', new_callable=StringIO)
@patch('sys.stderr', new_callable=StringIO)
def test_cli_config_missing_key_file_errors(mock_stderr, mock_stdout, tmp_path):
    """Eine fehlende, per Config referenzierte Schlüsseldatei führt zu Exit-Code 1."""
    config_file = tmp_path / ".envvault.json"
    config_file.write_text(json.dumps({"key_file": str(tmp_path / "missing.key")}))

    input_file = tmp_path / "test.env"
    input_file.write_text("USER=testuser")

    argv = ['main.py', '--config', str(config_file), 'encrypt', str(input_file)]
    with patch.dict(os.environ, {}, clear=True):
        with patch('sys.argv', argv):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1
            assert "referenced in config not found" in mock_stderr.getvalue()
