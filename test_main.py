import pytest
import os
import sys
from unittest.mock import patch, mock_open
from io import StringIO

from cryptography.fernet import Fernet, InvalidToken

# Importieren der zu testenden Komponenten aus main.py
from main import EnvVault, main

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
def env_vault_instance():
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
