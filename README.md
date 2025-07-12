# PySec - Endpoint Security Management

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

PySec is a comprehensive, open-source endpoint security management platform that helps organizations monitor and secure their systems through automated auditing, vulnerability scanning, and centralized client-server management.

## 🚀 Quick Overview

**PySec** provides two main operational modes:

1. **Standalone Mode**: Run security audits directly on individual systems
2. **Client-Server Mode**: Centrally manage and monitor multiple endpoints through a web dashboard

## ✨ Key Features

### 🔍 Security Auditing
- **System Configuration Audit**: Check disk encryption, screen lock settings, automatic updates
- **Package Vulnerability Scanning**: CVE detection across multiple package managers
- **Multi-Platform Support**: Ubuntu, Arch Linux, macOS (with extensible architecture)

### 🌐 Client-Server Architecture
- **Centralized Dashboard**: Web-based management interface for all monitored systems
- **Token-Based Authentication**: Secure client registration and communication
- **Real-Time Monitoring**: Track client status, audit logs, and security posture
- **RESTful API**: Full API access for automation and integration

### 📦 Package Repository Support
- **APT** (Debian/Ubuntu)
- **Pacman** (Arch Linux)
- **Homebrew** (macOS)
- **pip** (Python packages)
- **Snap** packages
- **Docker** containers

### 🛡️ CVE Management
- **NVD Integration**: Automated CVE data download from NIST National Vulnerability Database
- **Severity Filtering**: Filter vulnerabilities by severity level (LOW, MEDIUM, HIGH, CRITICAL)
- **Version-Aware Matching**: Precise vulnerability matching based on installed package versions

![Server Dashboard](docs/pysec-server-dashboard.png)
*Centralized dashboard showing all monitored clients*

![Client Details](docs/pysec-server-client-detail.png)
*Detailed client view with packages and audit logs*

## 📋 Installation

### Prerequisites
- Python 3.11 or higher
- pip or pipx

### Quick Install

```bash
# Clone the repository
git clone https://github.com/MartinThoma/pysec.git
cd pysec

# Install with pipx (recommended)
pipx install -e .

# Or install with pip
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

## 🎯 Usage Examples

### Standalone Auditing

```bash
# Audit system security configuration
pysec audit config
# Output:
# Running system configuration audit...
# - Found checker: UbuntuSecurityChecker
# - Installed packages: 4035 across 4 repository types
#   - DEBIAN_APT: 3579 packages
#   - PYTHON_PIP: 438 packages
#   - SNAP: 18 packages
#   - DOCKER: 0 packages
# ✗ Disk is NOT encrypted
# ✓ Screen locks after 15 minutes
# ✓ Automatic daily updates are enabled

# Scan packages for vulnerabilities
pysec audit packages --verbose --min-severity HIGH
# Displays table of packages with HIGH+ severity CVEs

# Filter by severity and get detailed descriptions
pysec audit packages -vv --min-severity CRITICAL
```

### Server-Client Deployment

#### 1. Set Up the Server

```bash
# Initialize database (first time only)
pysec server manage.py migrate
pysec server manage.py createsuperuser

# Start the server
pysec server start
# Server available at: http://127.0.0.1:8000
```

#### 2. Register Clients

```bash
# Create a client token (on server)
pysec server manage.py create_client "laptop-001"

# Configure client (on remote system)
pysec client configure --server-url http://your-server:8000 --token YOUR_TOKEN

# Run client audit and report to server
pysec client run
```

#### 3. Web Dashboard

Visit `http://your-server:8000` to access the web dashboard where you can:
- View all registered clients
- Monitor client status and last-seen times
- Review detailed audit logs
- Analyze package inventories and vulnerabilities

## 🖥️ Supported Platforms


Operating system support is modular, allowing easy addition of new platforms.
Currently supported are:

| Platform      | Configuration Audit      | Package Scanning    | Status           |
|---------------|--------------------------|---------------------|------------------|
| Ubuntu/Debian | ✅                       | ✅ (APT, pip, snap) | Full Support     |
| Arch Linux    | ✅                       | ✅ (Pacman, pip)    | Full Support     |
| macOS         | ✅                       | ✅ (Homebrew, pip)  | Full Support     |


pysec also supports package scanning for:

* Python packages (pip)
* Docker images


## 🔧 Configuration

### Client Configuration
Client settings are stored in `~/.config/pysec/client.json`:
```json
{
  "server_url": "http://your-server:8000",
  "token": "your-client-token"
}
```

### Server Configuration
Server settings can be customized via Django settings in `pysec_django/settings.py`.

## 🛠️ Development

### Running Tests
```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_package_repositories.py -v

# Run with coverage
python -m pytest --cov=pysec
```

### Code Quality
```bash
# Run linter
make lint

# Format code
make format

# Run all quality checks
pre-commit run --all-files
```

### Adding Platform Support

To add support for a new operating system:

1. Create a new file in `pysec/oschecks/` (e.g., `linux_fedora.py`)
2. Inherit from `BaseSecurityChecker`
3. Implement required methods:
   - `is_current_os()`: Detect if running on this OS
   - `is_disk_encrypted()`: Check disk encryption
   - `screen_lock_timeout()`: Get screen lock timeout
   - `automatic_daily_updates_enabled()`: Check auto-updates

Example:
```python
class FedoraSecurityChecker(BaseSecurityChecker):
    @staticmethod
    def is_current_os() -> bool:
        return Path("/etc/fedora-release").exists()

    def is_disk_encrypted(self) -> bool:
        # Implement Fedora-specific disk encryption check
        pass
```

## 📁 Project Structure

```
pysec/
├── pysec/                          # Main package
│   ├── cli/                        # Command-line interface
│   ├── oschecks/                   # OS-specific security checkers
│   ├── package_repositories/       # Package manager integrations
│   ├── server/                     # Django server components
│   ├── client.py                   # Client functionality
│   ├── cve_manager.py             # CVE data management
│   └── config.py                  # Configuration management
├── pysec_django/                  # Django project settings
├── tests/                         # Test suite
├── docs/                          # Documentation
└── pyproject.toml                 # Package configuration
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`make test`)
5. Run code quality checks (`make lint`)
6. Submit a pull request

### Easy Contribution Areas
- **Add OS Support**: Implement security checkers for new operating systems
- **Package Managers**: Add support for additional package managers
- **CVE Sources**: Integrate additional vulnerability databases
- **UI Improvements**: Enhance the web dashboard interface

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Originally inspired by [pysec-notebook](https://github.com/MartinThoma/pysec-notebook)
- CVE data sourced from [NIST National Vulnerability Database](https://nvd.nist.gov/)
- Built with Django and Rich for excellent user experience

## 📞 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues and Discussions**: Report bugs or request features via GitHub Issues

---

**Made with ❤️ for the security community**
