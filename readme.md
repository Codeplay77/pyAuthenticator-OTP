<div align="center">

# Python Authenticator

### Modern 2FA/TOTP Authentication Manager

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](license)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Codeplay77/pyAuthenticator-OTP)
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

**A secure, feature-rich desktop application for managing Time-based One-Time Passwords (TOTP) with a beautiful Material Design interface.**
</div>

---

## Features

### Core Features
- ** TOTP Generation**: RFC 6238 compliant, compatible with Google Authenticator
- ** Modern UI**: Material Design inspired interface
- ** Secure Storage**: Fernet encryption (AES-128-CBC + HMAC-SHA256) for all secret keys
- ** Auto-Update**: Tokens refresh automatically every 30 seconds
- ** One-Click Copy**: Quick clipboard access to tokens
- ** Cross-Platform**: Works on Windows, Linux, and macOS

###  Advanced Features
- ** Global Hotkeys**: Toggle window with Ctrl+Shift+A, add accounts with Ctrl+Shift+N
- ** System Tray**: Minimize to system tray for background operation
- ** Progress Bar**: Visual countdown for token expiration
- ** Material Design**: Google-inspired clean interface
- ** Local Database**: SQLite storage with encrypted secrets
- ** Key Recovery**: Retrieve original secret keys when needed
- ** Input Validation**: Real-time validation of secret keys

###  Security Features
- **End-to-End Encryption**: All secrets encrypted at rest
- **No Cloud Sync**: Complete data privacy (local-only storage)
- **Secure Deletion**: Confirmation dialogs for account removal
- **Thread-Safe UI**: Hotkey and tray events are dispatched to the Tk main loop

---

## Installation

### Prerequisites

<table>
<tr>
<td>

**Required:**
- Python 3.8 or higher
- pip (Python package manager)

</td>
<td>

**Optional:**
- keyboard module (for global hotkeys)
- pystray module (for system tray)

</td>
</tr>
</table>

### Quick Start (3 steps)

#### 1️ Clone the Repository
```bash
git clone https://github.com/Codeplay77/pyAuthenticator-OTP.git
cd pyAuthenticator-OTP
```

#### 2️ Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install pyotp cryptography Pillow pystray keyboard
```

#### 3️ Run the Application
```bash
python main.py
```

### Building Standalone Executable

#### Windows
```bash
# Run the build script
build.bat

# Or manually with PyInstaller
pyinstaller --onefile --windowed --name=PythonAuthenticator ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    main.py
```

#### Linux/macOS
```bash
pyinstaller --onefile --windowed --name=PythonAuthenticator \
    --icon=icon.ico \
    --add-data "icon.ico:." \
    main.py
```

**Output:** Executable will be created in `dist/` folder (~12-25 MB, depending on Python and library versions)

> Account data (`authenticator.db`, `key.key`) is stored next to the executable. `build.bat` only replaces `PythonAuthenticator.exe` and keeps the other files in `dist/`.

---

## Usage

### Adding Your First Account

<details>
<summary><b> From Mobile App (Google Authenticator, etc.)</b></summary>

1. Open your 2FA-enabled service (Google, GitHub, etc.)
2. Navigate to **Security Settings** → **Two-Factor Authentication**
3. Select **"Cannot scan QR code?"** or **"Enter manually"**
4. Copy the secret key (usually 16-32 characters)
5. In Python Authenticator:
   - Click **"Add Account"**
   - Enter account name (e.g., `user@gmail.com`)
   - Enter issuer (e.g., `Google`)
   - Paste the secret key
   - Click **"Add Account"**

</details>

<details>
<summary><b>🔑 Manual Entry</b></summary>

**Example Configuration:**

| Field | Example | Required |
|-------|---------|----------|
| Account Name | `user@gmail.com` | ✅ Yes |
| Issuer | `Google` | ⚪ Optional |
| Secret Key | `JBSWY3DPEHPK3PXP` | ✅ Yes |

**Secret Key Format:**
- Base32 encoded (A-Z, 2-7)
- Typically 16-32 characters
- Case insensitive
- Spaces and dashes are automatically removed

</details>

### Using Generated Tokens

| Action | Method |
|--------|--------|
| **Copy Token** | Click on the 6-digit code or 📋 icon |
| **View Time Remaining** | Check the progress bar or countdown timer |
| **Delete Account** | Click ✖ button → Confirm deletion |
| **Recover Secret Key** | Click 🔑 icon → Confirm security warning |

### Keyboard Shortcuts

| Shortcut | Action | Configurable |
|----------|--------|--------------|
| `Ctrl+Shift+A` | Show the window, or hide it if it already has focus | ✅ Yes |
| `Ctrl+Shift+N` | Add new account | ✅ Yes |
| `ESC` | Close dialog | ❌ No |
| `Enter` | Confirm dialog | ❌ No |

**Configure in:** `config.json` (set a hotkey to `"disabled"` to turn it off)

> Global hotkeys are captured in every application. Avoid combinations used for navigation, such as `ctrl+tab` or `shift+tab`.

### Token Lifecycle

```
┌─────────────────────────────────────────┐
│  Token Generated (T=0s)                 │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  30s    │ ← Fresh token (Blue)
└─────────────────────────────────────────┘
           ↓ Time passes...
┌─────────────────────────────────────────┐
│  Token Valid (T=15s)                    │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░  15s     │ ← Still valid (Blue)
└─────────────────────────────────────────┘
           ↓ Almost expired...
┌─────────────────────────────────────────┐
│  Token Expiring (T=25s)                 │
│  ▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░   5s    │ ← About to expire (Red)
└─────────────────────────────────────────┘
           ↓ New token generated
┌─────────────────────────────────────────┐
│  New Token (T=30s → T=0s)               │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  30s    │ ← Fresh token (Blue)
└─────────────────────────────────────────┘
```

## Como Usar

### Adicionar uma nova conta

1. **Clique em "Adicionar conta"**
2. **Preencha os dados:**
   - **Nome da conta:** `usuario@gmail.com`
   - **Emissor:** `Google` (opcional)
   - **Chave secreta:** `JBSWY3DPEHPK3PXP...`
3. **Clique em "Adicionar conta"**

### Obter códigos 2FA

- Os códigos são **atualizados automaticamente** a cada 30 segundos
- **Clique no código** ou no ícone 📋 para copiar
- A **barra de progresso** mostra o tempo restante
- Códigos ficam **vermelhos** quando estão prestes a expirar

### Gerenciar contas

- **Remover conta:** Clique no ✖ e confirme
- **Copiar código:** Clique no número ou no ícone 📋
- **Visualizar tempo:** Barra de progresso e contador

---

## Configuration

### File Structure

```
pyAuthenticator-OTP/
├── Core Application Files
│   ├── main.py                    # Entry point & dependency checks
│   ├── authenticator_app.py       # Main application controller
│   ├── database.py                # Database & encryption layer
│   ├── totp_generator.py          # TOTP token generation (RFC 6238)
│   ├── token_widget.py            # Individual token UI component
│   ├── add_account_dialog.py      # Add account dialog
│   └── config_manager.py          # Configuration management
│
├── Data Files (Auto-generated)
│   ├── authenticator.db           # SQLite database (encrypted)
│   ├── key.key                    # Fernet encryption key
│   └── config.json                # User preferences
│
├── Tools
│   └── recover_otp_keys.py        # Prints decrypted secrets from the database
│
├── Build & Deploy
│   ├── requirements.txt           # Python dependencies
│   ├── install_dependencies.bat   # Windows dependency installer
│   ├── build.bat                  # Windows build script
│   └── icon.ico                   # Executable icon
│
└── Documentation
    ├── readme.md                  # This file
    └── license                    # MIT License
```

### Configuration File (`config.json`)

<details>
<summary><b>View Default Configuration</b></summary>

```json
{
  "hotkeys": {
    "toggle_window": "ctrl+shift+a",
    "add_account": "ctrl+shift+n"
  },
  "ui": {
    "window_position": "right",
    "margin": 20,
    "always_on_top": false,
    "custom_x": 100,
    "custom_y": 100
  },
  "tray": {
    "enabled": true,
    "hide_on_close": true,
    "tooltip": "Python Authenticator"
  },
  "update": {
    "auto_refresh": true,
    "refresh_interval": 1,
    "show_progress_bar": true
  }
}
```

</details>

### Important Files

#### Critical Files (Backup Required!)

| File | Purpose | Size | Backup Priority |
|------|---------|------|-----------------|
| `authenticator.db` | Encrypted account database | ~50-500 KB | 🔴 Critical |
| `key.key` | Encryption key | 44 bytes | 🔴 Critical |
| `config.json` | User preferences | ~500 bytes | 🟡 Medium |

> **Warning:** Without `authenticator.db` and `key.key`, you will lose all stored accounts!

#### Backup Recommendations

```bash
# Manual backup
cp authenticator.db authenticator.db.backup
cp key.key key.key.backup

# Automated backup (Windows - Task Scheduler)
# Create a .bat file:
@echo off
set BACKUP_DIR=C:\Backups\PythonAuth
xcopy authenticator.db %BACKUP_DIR%\authenticator_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db /Y
xcopy key.key %BACKUP_DIR%\key_%date:~-4,4%%date:~-10,2%%date:~-7,2%.key /Y
```

---

## Security

### Encryption Architecture

```
┌─────────────────────────────────────────────┐
│  User Input (Secret Key)                    │
│  "JBSWY3DPEHPK3PXP..."                      │
└─────────────────────────────────────────────┘
              ↓ Validation
┌─────────────────────────────────────────────┐
│  Base32 Validation & Sanitization           │
│  • Remove spaces/dashes                     │
│  • Verify format [A-Z2-7]                   │
│  • Check minimum length (8 chars)           │
└─────────────────────────────────────────────┘
              ↓ Encryption
┌─────────────────────────────────────────────┐
│  Fernet Symmetric Encryption                │
│  • Algorithm: AES-128-CBC                   │
│  • HMAC: SHA256                             │
│  • Key: 32-byte random key                  │
└─────────────────────────────────────────────┘
              ↓ Storage
┌─────────────────────────────────────────────┐
│  SQLite Database (authenticator.db)         │
│  • Encrypted secrets                        │
│  • Prepared statements (SQL injection safe) │
└─────────────────────────────────────────────┘
```

### Security Features

#### What IS Protected

| Feature | Implementation | Security Level |
|---------|----------------|----------------|
| **Secret Keys** | Fernet encryption (AES-128-CBC + HMAC-SHA256) | 🟢 High |
| **SQL Injection** | Prepared statements with parameter binding | 🟢 High |
| **Input Validation** | Real-time Base32 validation | 🟢 High |
| **Memory Safety** | Tokens never persisted, only generated | 🟢 High |
| **Thread Safety** | Hotkey and tray events queued to the Tk main loop | 🟢 High |

#### Security Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Encryption key on disk** | If attacker has file access, can decrypt | 🟡 Medium - Use OS keyring (future) |
| **No master password** | Anyone with file access can read keys | 🟡 Medium - Add password protection (future) |
| **Local storage only** | No cloud sync/backup | 🟢 Low - Feature, not bug (privacy) |
| **OS-level permissions** | Files protected only by OS permissions | 🟡 Medium - Set restrictive file permissions |

### Best Security Practices

#### For Users

1. **File Permissions** (Linux/macOS):
   ```bash
   chmod 600 authenticator.db key.key
   ```

2. **Backup Securely**:
   - Store backups in encrypted containers (VeraCrypt, BitLocker)
   - Never share `key.key` without `authenticator.db`

3. **Physical Security**:
   - Lock your computer when away
   - Enable full-disk encryption (BitLocker, FileVault)

4. **Network Security**:
   - No network access required (app is 100% offline)
   - Firewall can block all connections

#### For Developers

1. **Code Auditing**:
   - All cryptographic operations use standard libraries
   - No custom crypto implementations
   - Regular dependency updates

2. **Dependency Security**:
   ```bash
   # Check for vulnerabilities
   pip install safety
   safety check -r requirements.txt
   ```

3. **Static Analysis**:
   ```bash
   # Code quality checks
   pylint *.py
   mypy --strict *.py
   bandit -r .
   ```

### Compliance & Standards

| Standard | Status | Notes |
|----------|--------|-------|
| **RFC 6238** (TOTP) | Compliant | Standard 30-second time step |
| **RFC 4648** (Base32) | Compliant | Secret key encoding |
| **PEP 8** (Python) | Compliant | Code style guidelines |
| **OWASP Top 10** | Partial | Local app, limited attack surface |

### Threat Model

#### Protected Against

- Network interception (no network activity)
- SQL injection attacks
- Invalid input exploitation
- Race conditions in UI updates
- Unauthorized token generation (requires key.key)

#### NOT Protected Against

- Physical access to unlocked computer
- Malware with file system access
- Screen recording/keylogging
- Authorized user misuse

## Development

### Technology Stack

<table>
<tr>
<td width="50%">

#### Core Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Core language |
| **Tkinter** | Built-in | GUI framework |
| **SQLite3** | Built-in | Database |

</td>
<td width="50%">

#### Dependencies
| Library | Version | Purpose |
|---------|---------|---------|
| **pyotp** | ≥2.8.0 | TOTP generation |
| **cryptography** | ≥3.4.8 | Encryption |
| **Pillow** | ≥9.0.0 | Image handling |
| **pystray** | ≥0.19.4 | System tray |
| **keyboard** | ≥0.13.5 | Global hotkeys |

</td>
</tr>
</table>

### Project Architecture

```
┌─────────────────────────────────────────┐
│      Presentation Layer (UI)            │
│  • Main Window (authenticator_app.py)   │
│  • Token Widgets (token_widget.py)      │
│  • Dialogs (add_account_dialog.py)      │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Business Logic Layer               │
│  • TOTP Generation (totp_generator.py)  │
│  • Config Management (config_manager.py)│
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Data Access Layer                  │
│  • Database (database.py)               │
│  • Encryption (Fernet)                  │
└─────────────────────────────────────────┘
```

### Development Setup

#### 1. Clone & Setup Environment
```bash
# Clone repository
git clone https://github.com/Codeplay77/pyAuthenticator-OTP.git
cd pyAuthenticator-OTP

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black isort flake8
```

#### 2. Code Formatting
```bash
# Format code
black *.py --line-length 88

# Sort imports
isort *.py

# Check style
flake8 *.py --max-line-length=88
```

### Contributing

We welcome contributions! Please follow these guidelines:

#### Contribution Process

1. **Fork** the repository
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes** following code standards
4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

#### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat(auth): add QR code scanning support

- Implement camera access
- Add QR code decoder
- Update UI for scanner

Closes #123
```

#### Code Style Guidelines

- Follow **PEP 8** (enforced by Black formatter)
- Use **type hints** for all functions
- Write **docstrings** for all public methods
- Maximum line length: **88 characters**
- Use **meaningful variable names**

**Example:**
```python
def generate_token(self, secret: str) -> str:
    """Generate TOTP token from secret key.
    
    Args:
        secret: Base32 encoded secret key
        
    Returns:
        6-digit TOTP token
        
    Raises:
        ValueError: If secret is invalid
    """
    pass
```

### Running in Development Mode

```bash
# Run with profiling
python -m cProfile -o profile.stats main.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### Platform-Specific Notes

#### Windows
- Requires Visual C++ Redistributable for some dependencies
- PyInstaller builds work out of the box
- System tray requires `pystray` with `PIL`

#### Linux
- May require `python3-tk` package: `sudo apt install python3-tk`
- Global hotkeys require root privileges or uinput permissions
- System tray depends on desktop environment (GNOME, KDE, etc.)

#### macOS
- Tkinter included with Python.org installer
- May require Rosetta 2 on Apple Silicon
- Notarization required for distribution

### Bug Reports

Found a bug? Please [open an issue](../../issues/new) with:

- **Description**: Clear explanation of the bug
- **Steps to Reproduce**: Numbered steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**:
  - OS and version
  - Python version
  - Dependency versions
- **Screenshots**: If applicable
- **Logs**: Relevant error messages

### Feature Requests

Have an idea? [Open a feature request](../../issues/new) with:

- **Problem**: What problem does this solve?
- **Solution**: How would it work?
- **Alternatives**: Other approaches considered
- **Additional Context**: Any other relevant info

---

### API Documentation

<details>
<summary><b>Core Modules</b></summary>

#### TOTPGenerator
```python
from totp_generator import TOTPGenerator

generator = TOTPGenerator()

# Generate token
token = generator.generate_token("JBSWY3DPEHPK3PXP")
# Returns: "123456"

# Validate secret
is_valid, message = generator.validate_secret("JBSWY3DPEHPK3PXP")
# Returns: (True, "Valid key")

# Get time remaining
remaining = generator.get_time_remaining()
# Returns: 15 (seconds)
```

#### Database
```python
from database import Database

db = Database()

# Add account
account_id = db.add_account(
    name="user@example.com",
    secret="JBSWY3DPEHPK3PXP",
    issuer="Google"
)

# Get all accounts
accounts = db.get_all_accounts()
# Returns: [(id, name, secret, issuer), ...]

# Delete account
db.delete_account(account_id)
```

</details>

---

## FAQ

<details>
<summary><b>Q: Is this compatible with Google Authenticator?</b></summary>

**A:** Yes! This app implements the standard TOTP algorithm (RFC 6238), making it 100% compatible with Google Authenticator, Microsoft Authenticator, Authy, and any other RFC 6238-compliant authenticator app.

</details>

<details>
<summary><b>Q: Can I use this on multiple devices?</b></summary>

**A:** You can copy the `authenticator.db` and `key.key` files to another device, but they must be kept together. However, there's no automatic sync - you need to manually transfer files.

</details>

<details>
<summary><b>Q: What happens if I lose my key.key file?</b></summary>

**A:** Unfortunately, without the `key.key` file, you cannot decrypt your stored secrets. This is why **backups are critical**. Always keep both `authenticator.db` and `key.key` together in your backups.

</details>

<details>
<summary><b>Q: Why aren't tokens generated offline?</b></summary>

**A:** Tokens **ARE** generated offline! The app requires no internet connection. TOTP uses your computer's time, not network time. Just make sure your system clock is accurate.

</details>

<details>
<summary><b>Q: Can I import from Google Authenticator?</b></summary>

**A:** Currently, you need to manually re-add accounts. Future versions may support importing from other authenticators. The easiest way is to disable 2FA on each service and re-enable it, adding it to Python Authenticator during setup.

</details>

<details>
<summary><b>Q: Is my data sent to the cloud?</b></summary>

**A:** No! This app is 100% offline and local. Your data never leaves your device. No telemetry, no analytics, no cloud sync.

</details>

---

## Troubleshooting

### Common Issues

#### Issue: "Module not found" errors

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or install missing module directly
pip install pyotp cryptography Pillow
```

#### Issue: Global hotkeys don't work

**Possible Causes:**
- `keyboard` module not installed
- Insufficient permissions (Linux/macOS may require root)
- Hotkey conflict with another application

**Solution:**
```bash
# Install keyboard module
pip install keyboard

# Linux: Run with sudo or configure uinput permissions
sudo python main.py
# OR
sudo usermod -a -G input $USER  # Then re-login
```

#### Issue: System tray icon not appearing

**Solution:**
```bash
# Install pystray
pip install pystray

# Ensure PIL/Pillow is installed
pip install Pillow
```

#### Issue: Tokens don't match Google Authenticator

**Possible Causes:**
- System clock out of sync
- Wrong secret key entered
- Time zone misconfiguration

**Solution:**
```bash
# Windows: Sync time
w32tm /resync

# Linux/macOS: Sync time
sudo ntpdate -s time.nist.gov

# Or enable automatic time sync in system settings
```

#### Issue: Database locked error

**Solution:**
```bash
# Close all instances of the app
# Check for background processes
# Windows:
taskkill /F /IM PythonAuthenticator.exe

# Linux/macOS:
killall PythonAuthenticator
```

#### Issue: Can't build executable with PyInstaller

**Solution:**
```bash
# Update PyInstaller
pip install --upgrade pyinstaller

# Rebuild (build.bat already runs PyInstaller with --clean)
build.bat
```

### Getting Help

1. **Check existing issues:** [GitHub Issues](../../issues)
2. **Search documentation:** This README
3. **Ask the community:** [Discussions](../../discussions)
4. **Report a bug:** [New Issue](../../issues/new)

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](license) file for details.

```
MIT License

Copyright (c) 2025 Codeplay77

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[See full license in LICENSE file]
```

---

## Acknowledgments

### Open Source Libraries

| Library | License | Purpose |
|---------|---------|---------|
| [PyOTP](https://github.com/pyauth/pyotp) | MIT | TOTP token generation |
| [Cryptography](https://github.com/pyca/cryptography) | Apache 2.0/BSD | Encryption |
| [Pillow](https://github.com/python-pillow/Pillow) | PIL License | Image processing |
| [pystray](https://github.com/moses-palmer/pystray) | LGPL 3.0 | System tray |
| [keyboard](https://github.com/boppreh/keyboard) | MIT | Global hotkeys |

### Inspirations

- **Google Authenticator** - Reference implementation
- **Material Design** - UI/UX principles
- **RFC 6238** - TOTP standard specification
- **Python Community** - Excellent libraries and support

### Contributors

<a href="https://github.com/Codeplay77/pyAuthenticator-OTP/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Codeplay77/pyAuthenticator-OTP" />
</a>

---

## Project Stats

![GitHub stars](https://img.shields.io/github/stars/Codeplay77/pyAuthenticator-OTP?style=social)
![GitHub forks](https://img.shields.io/github/forks/Codeplay77/pyAuthenticator-OTP?style=social)
![GitHub issues](https://img.shields.io/github/issues/Codeplay77/pyAuthenticator-OTP)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Codeplay77/pyAuthenticator-OTP)
![GitHub last commit](https://img.shields.io/github/last-commit/Codeplay77/pyAuthenticator-OTP)
![GitHub code size](https://img.shields.io/github/languages/code-size/Codeplay77/pyAuthenticator-OTP)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Codeplay77/pyAuthenticator-OTP&type=Date)](https://star-history.com/#Codeplay77/pyAuthenticator-OTP&Date)

---

<div align="center">

### Support This Project

If you find this project helpful, please consider:
 **Starring** the repository  
 **Reporting** bugs  
 **Suggesting** new features  
 **Contributing** code  
 **Sharing** with others

---

**Made with ❤️ by [Codeplay77](https://github.com/Codeplay77)**

[🏠 Homepage](https://github.com/Codeplay77/pyAuthenticator-OTP) • [📖 Documentation](https://github.com/Codeplay77/pyAuthenticator-OTP/wiki) • [🐛 Issues](https://github.com/Codeplay77/pyAuthenticator-OTP/issues) • [💬 Discussions](https://github.com/Codeplay77/pyAuthenticator-OTP/discussions)

</div>
