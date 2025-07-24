<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Installation Guide - Code Intelligence Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-19
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Installation Guide - Code Intelligence Toolkit

**Related Code Files:**
- `dependency_checker.py` - Automated dependency checking with multi-platform support
- `run_any_python_tool.sh` - Main wrapper script for running Python tools
- `requirements.txt` - Python package dependencies

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Platform-Specific Installation](#platform-specific-installation)
4. [Python Dependencies](#python-dependencies)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Dependencies

The toolkit requires the following external tools:

1. **Python 3.6+** - Core runtime
2. **ripgrep (rg)** - Fast file searching (REQUIRED)
3. **Git** - Version control (optional, for git-related tools)
4. **Java/JDK** - For Java compilation checking (optional)
5. **Node.js** - For JavaScript/TypeScript checking (optional)

### Checking Dependencies

Use the included dependency checker:

```bash
# Check all dependencies
python dependency_checker.py --all

# Check specific dependency
python dependency_checker.py rg
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/code-intelligence-toolkit.git
cd code-intelligence-toolkit
```

### 2. Install ripgrep (REQUIRED)

Ripgrep is the only mandatory external dependency. Choose your platform:

```bash
# macOS
brew install ripgrep

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ripgrep

# Fedora
sudo dnf install ripgrep

# Arch Linux
sudo pacman -S ripgrep

# Windows (with Chocolatey)
choco install ripgrep

# Universal (compile from source)
# See: https://github.com/BurntSushi/ripgrep#installation
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 4. Create Configuration

```bash
# Copy sample configuration
cp .pytoolsrc.sample .pytoolsrc

# Edit to match your project structure
# See CONFIG_GUIDE.md for details
```

## Platform-Specific Installation

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 ripgrep git

# Optional dependencies
brew install openjdk gradle maven node
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install python3 python3-pip ripgrep git

# Optional dependencies
sudo apt-get install default-jdk gradle maven nodejs npm
```

### Fedora

```bash
# Install dependencies
sudo dnf install python3 python3-pip ripgrep git

# Optional dependencies
sudo dnf install java-latest-openjdk-devel gradle maven nodejs npm
```

### Arch Linux

```bash
# Install dependencies
sudo pacman -S python python-pip ripgrep git

# Optional dependencies
sudo pacman -S jdk-openjdk gradle maven nodejs npm
```

### Windows

1. **Install Python**: Download from [python.org](https://www.python.org/downloads/)

2. **Install Chocolatey** (package manager):
   ```powershell
   # Run in Administrator PowerShell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

3. **Install dependencies**:
   ```powershell
   choco install python3 ripgrep git
   
   # Optional
   choco install openjdk gradle maven nodejs
   ```

## Python Dependencies

### Required Packages

Create a `requirements.txt` file:

```txt
# AST parsing for multiple languages
javalang>=0.13.0
esprima>=4.0.0

# System utilities
psutil>=5.9.0

# Optional: Advanced refactoring
rope>=1.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

### Optional Packages

For full functionality:
```bash
# Code formatting
pip install black autopep8

# Additional language support
pip install astroid pylint
```

## Configuration

### Basic Setup

1. **Create configuration file**:
   ```bash
   cp .pytoolsrc.sample .pytoolsrc
   ```

2. **Edit for your project**:
   ```ini
   [defaults]
   default_scope = src/
   
   [paths]
   java_source = src/main/java/
   python_source = src/main/python/
   test_directory = tests/
   ```

3. **Test configuration**:
   ```bash
   python common_config.py --show
   ```

See `CONFIG_GUIDE.md` for detailed configuration options.

## Verification

### 1. Check Installation

```bash
# Run dependency checker
python dependency_checker.py --all

# Test a basic tool
./run_any_python_tool.sh find_text.py "test" --help

# Run comprehensive test
python -m pytest test/
```

### 2. Verify Tool Functionality

```bash
# Test file search
./run_any_python_tool.sh find_files.py --ext py

# Test text search (requires ripgrep)
./run_any_python_tool.sh find_text.py "TODO" --scope .

# Test AST parsing (requires javalang for Java)
./run_any_python_tool.sh navigate_ast.py MyClass.java --help
```

## Troubleshooting

### Common Issues

#### 1. "ripgrep not found"
```bash
# Verify ripgrep installation
which rg || echo "ripgrep not installed"

# Re-run platform-specific install command
# See Platform-Specific Installation section
```

#### 2. "Module not found" errors
```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. Permission denied on wrapper script
```bash
# Make wrapper executable
chmod +x run_any_python_tool.sh
chmod +x java_analysis.sh
```

#### 4. Tools not finding files
```bash
# Check your .pytoolsrc configuration
python common_config.py --show

# Verify paths exist
ls -la src/  # Or your configured path
```

### Getting Help

1. **Check tool help**:
   ```bash
   ./run_any_python_tool.sh tool_name.py --help
   ```

2. **View error logs**:
   ```bash
   ./run_any_python_tool.sh analyze_errors.py --recent 10
   ```

3. **Enable debug logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   ./run_any_python_tool.sh tool_name.py
   ```

## Next Steps

1. Read `README.md` for toolkit overview
2. Review `CONFIG_GUIDE.md` for configuration details
3. Check `examples/` directory for usage examples
4. Run `./run_any_python_tool.sh --help` for available tools

## Support

- **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/code-intelligence-toolkit/issues)
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory for real-world usage