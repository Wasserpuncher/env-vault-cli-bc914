# EnvVault CLI: Secure Environment Variable Management

[![Python CI/CD](https://github.com/your-username/env-vault-cli/actions/workflows/python-app.yml/badge.svg)](https://github.com/your-username/env-vault-cli/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

EnvVault CLI is an enterprise-ready, open-source command-line utility designed to securely encrypt and decrypt environment variables stored in `.env` files. It's built for developers, DevOps engineers, and CI/CD pipelines that require a robust solution for managing sensitive configuration data.

## Features

*   **Symmetric Encryption**: Leverages the `cryptography` library's Fernet implementation for strong, authenticated symmetric encryption.
*   **Key Generation**: Easily generate secure Fernet keys directly from the CLI.
*   **File-Based Encryption/Decryption**: Encrypt entire `.env` files and decrypt them back to plaintext.
*   **CLI-Friendly**: Intuitive command-line interface with clear options for various operations.
*   **Environment Variable Support**: Pass the encryption key securely via an environment variable (`ENVVAULT_KEY`).
*   **Print to Stdout**: Decrypt secrets and print them directly to the console for use in scripts without creating temporary files.
*   **Cross-Platform**: Built with Python, ensuring compatibility across different operating systems.

## Installation

1.  **Prerequisites**:
    *   Python 3.8+ installed on your system.

2.  **Install from PyPI (Coming Soon)**:
    ```bash
    pip install env-vault-cli
    ```

3.  **Manual Installation (from source)**:
    ```bash
    git clone https://github.com/your-username/env-vault-cli.git
    cd env-vault-cli
    python3 -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    pip install -r requirements.txt
    # Make the CLI available (optional, for development)
    # python3 -m pip install -e .
    ```

## Usage

### 1. Generate a New Encryption Key

First, generate a strong Fernet key. **Store this key securely!** It's essential for both encryption and decryption.

```bash
python main.py generate-key
# Output will be something like:
# Neuer Fernet-Schlüssel generiert: <YOUR_SECURE_FERNET_KEY_HERE>
# Bewahren Sie diesen Schlüssel sicher auf! Er wird für die Ver- und Entschlüsselung benötigt.
```

Export this key as an environment variable (`ENVVAULT_KEY`) or pass it directly using the `-k` flag for subsequent operations. Using an environment variable is recommended for security.

```bash
export ENVVAULT_KEY="<YOUR_SECURE_FERNET_KEY_HERE>"
```

### 2. Encrypt an Environment File

Let's say you have a `.env` file:

`my_app/.env`:
```env
DATABASE_URL=postgres://user:pass@host:5432/db
API_KEY=your_super_secret_api_key
DEBUG=False
```

To encrypt it:

```bash
python main.py encrypt my_app/.env -o my_app/.env.enc
# Or, if ENVVAULT_KEY is not set:
# python main.py encrypt my_app/.env -o my_app/.env.enc -k "<YOUR_SECURE_FERNET_KEY_HERE>"
```

This will create `my_app/.env.enc` with encrypted values:

`my_app/.env.enc`:
```env
DATABASE_URL=gAAAAABl... (long encrypted string)
API_KEY=gAAAAABl... (long encrypted string)
DEBUG=gAAAAABl... (long encrypted string)
```

### 3. Decrypt an Encrypted File

To decrypt `my_app/.env.enc` back to a new file `my_app/.env.dec`:

```bash
python main.py decrypt my_app/.env.enc -o my_app/.env.dec
```

`my_app/.env.dec` will contain the original plaintext variables.

### 4. Decrypt and Print to Standard Output

Useful for piping secrets directly into other commands or for quick inspection without creating a physical file.

```bash
python main.py decrypt my_app/.env.enc --print
# Output will be:
# DATABASE_URL=postgres://user:pass@host:5432/db
# API_KEY=your_super_secret_api_key
# DEBUG=False
```

## Security Considerations

*   **Key Management**: The security of your encrypted environment variables directly depends on the security of your Fernet key. **Never commit your encryption key to version control.** Store it in a secure location (e.g., a dedicated secrets manager, KMS, or a secure environment variable injection system for CI/CD).
*   **Environment Variables**: When passing the `ENVVAULT_KEY` via an environment variable, be aware that it might be visible to other processes on the same machine. For highly sensitive environments, consider using a more secure method of key injection provided by your orchestrator or CI/CD system.
*   **File Permissions**: Ensure that your `.env` and `.env.enc` files have appropriate file permissions to prevent unauthorized access.

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
