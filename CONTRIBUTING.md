# Contributing to EnvVault CLI

We welcome contributions to the EnvVault CLI project! Your help is valuable in making this tool better and more robust. Please take a moment to review this document to understand how you can contribute.

## Table of Contents

1.  [Code of Conduct](#code-of-conduct)
2.  [How to Contribute](#how-to-contribute)
    *   [Reporting Bugs](#reporting-bugs)
    *   [Suggesting Enhancements](#suggesting-enhancements)
    *   [Pull Requests](#pull-requests)
3.  [Development Setup](#development-setup)
    *   [Fork the Repository](#fork-the-repository)
    *   [Clone Your Fork](#clone-your-fork)
    *   [Create a Virtual Environment](#create-a-virtual-environment)
    *   [Install Dependencies](#install-dependencies)
4.  [Coding Guidelines](#coding-guidelines)
    *   [Python Style (PEP 8)](#python-style-pep-8)
    *   [Type Hinting](#type-hinting)
    *   [Docstrings and Comments](#docstrings-and-comments)
5.  [Testing](#testing)
    *   [Running Tests](#running-tests)
    *   [Writing Tests](#writing-tests)
6.  [Submitting a Pull Request](#submitting-a-pull-request)

## 1. Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [your-email@example.com].

## 2. How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on the [GitHub Issues page](https://github.com/your-username/env-vault-cli/issues). When reporting a bug, please include:

*   A clear and concise description of the bug.
*   Steps to reproduce the behavior.
*   Expected behavior.
*   Actual behavior.
*   Screenshots or error messages (if applicable).
*   Your operating system and Python version.

### Suggesting Enhancements

Have an idea for a new feature or an improvement? Open an issue on the [GitHub Issues page](https://github.com/your-username/env-vault-cli/issues) with the label `enhancement`. Describe your suggestion in detail, including why you think it would be beneficial.

### Pull Requests

We love pull requests! If you'd like to contribute code, please follow the [Development Setup](#development-setup) and [Coding Guidelines](#coding-guidelines) sections.

## 3. Development Setup

### Fork the Repository

Go to the [EnvVault CLI GitHub repository](https://github.com/your-username/env-vault-cli) and click the "Fork" button in the top right corner.

### Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/env-vault-cli.git
cd env-vault-cli
```

### Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate
```

### Install Dependencies

Install the required dependencies, including development and testing tools.

```bash
pip install -r requirements.txt
```

## 4. Coding Guidelines

### Python Style (PEP 8)

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style. We use `flake8` for linting, which is included in `requirements.txt`.

Before submitting a pull request, please run:

```bash
flake8 .
```

### Type Hinting

All new code should include [type hints](https://docs.python.org/3/library/typing.html) for function arguments and return values to improve readability and maintainability.

### Docstrings and Comments

*   **Docstrings**: Use [PEP 257](https://www.python.org/dev/peps/pep-0257/) style docstrings for modules, classes, and functions.
*   **Comments**: Inline comments (`#`) should be used to explain complex logic, design decisions, or non-obvious parts of the code. **Important:** As per project requirements, inline comments in code files (`.py`) must be in German to assist beginners.

## 5. Testing

### Running Tests

We use `pytest` for unit testing. To run the tests, activate your virtual environment and execute:

```bash
pytest
```

### Writing Tests

*   All new features and bug fixes should be accompanied by appropriate unit tests.
*   Tests should be placed in the `test_*.py` files in the root directory.
*   Aim for high test coverage.
*   Use `unittest.mock` or `pytest` fixtures to mock external dependencies (e.g., file system, `cryptography` library) to ensure tests are fast and isolated.

## 6. Submitting a Pull Request

1.  Ensure your code adheres to the [Coding Guidelines](#coding-guidelines).
2.  Make sure all [Tests](#testing) pass.
3.  Commit your changes with clear, descriptive commit messages.
4.  Push your branch to your fork on GitHub.
5.  Open a pull request from your fork's branch to the `main` branch of the original repository.
6.  Provide a clear title and description for your pull request, explaining the changes you've made and why.

Thank you for contributing to EnvVault CLI!
