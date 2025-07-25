<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT - Enterprise Git Safety Wrapper

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT - Enterprise Git Safety Wrapper

**Version**: 2.0 (with Non-Interactive Support)  
**Last Updated**: January 23, 2025

**Related Code Files:**
- `safegit.py` - Main wrapper with interception logic
- `safe_git_commands.py` - Core safety analysis engine
- `safegit_undo_stack.py` - Multi-level undo system
- `test_safegit_*.py` - Test suites

---

## 🛡️ Overview

SafeGIT is a protective wrapper around git that prevents accidental data loss from dangerous operations. Originally designed to prevent AI agent disasters (like the Replit incident), it now supports both interactive safety education and automated workflows.

## 🚀 Key Features

### Safety Features
- **37+ Dangerous Pattern Detection**: Intercepts risky commands before execution
- **Automatic Backups**: Creates stashes/backups before destructive operations
- **Smart Conversions**: Converts `push --force` to safer `--force-with-lease`
- **Multi-Level Undo**: Revert operations with full metadata tracking
- **Branch Protection**: Detects protected branches across platforms
- **Atomic File Operations**: Thread-safe logging and configuration

### Automation Features (NEW in v2.0)
- **Non-Interactive Mode**: Full support for CI/CD and scripts
- **Graduated Safety Levels**: Different flags for different risk levels
- **Environment Variables**: Auto-detection of CI environments
- **Comprehensive Logging**: Tracks all automated operations
- **Dry-Run Mode**: Test commands without execution

## 📦 Installation

```bash
# Basic installation
chmod +x safegit.py
sudo ln -s $(pwd)/safegit.py /usr/local/bin/safegit

# Verify installation
safegit --version
safegit --help
```

## 🎯 Usage

### Interactive Mode (Default)

```bash
# Safe commands pass through
safegit status
safegit add file.txt
safegit commit -m "message"

# Dangerous commands are intercepted
safegit reset --hard      # Prompts for confirmation
safegit clean -fdx        # Offers to create backup
safegit push --force      # Converts to --force-with-lease
```

### Non-Interactive Mode (NEW)

> **📖 For comprehensive documentation**: See [SafeGIT Non-Interactive Complete Guide](docs/safegit/SAFEGIT_NONINTERACTIVE_COMPLETE.md) for detailed examples, best practices, and advanced configurations.

#### Command-Line Flags

```bash
# Auto-confirm safe operations
safegit --yes add .
safegit --yes commit -m "Automated commit"
safegit --yes pull

# Force dangerous operations (use with caution!)
safegit --force-yes reset --hard HEAD~1
safegit --force-yes clean -fdx

# Strict non-interactive mode
safegit --non-interactive --yes status
safegit --batch --force-yes push
```

#### Environment Variables

```bash
# Enable non-interactive mode
export SAFEGIT_NONINTERACTIVE=1

# Auto-confirm safe operations
export SAFEGIT_ASSUME_YES=1

# Force all confirmations (dangerous!)
export SAFEGIT_FORCE_YES=1

# CI environments are auto-detected
# Supported: CI, GITHUB_ACTIONS, GITLAB_CI, JENKINS_URL, TRAVIS
```

### CI/CD Integration

#### GitHub Actions
```yaml
name: Deploy
on: push

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install SafeGIT
        run: |
          chmod +x safegit.py
          sudo ln -s $(pwd)/safegit.py /usr/local/bin/safegit
      
      - name: Safe Deploy
        env:
          SAFEGIT_ASSUME_YES: 1
        run: |
          safegit add .
          safegit commit -m "Deploy: ${{ github.sha }}"
          safegit push
```

#### GitLab CI
```yaml
deploy:
  script:
    - export SAFEGIT_ASSUME_YES=1
    - safegit add .
    - safegit commit -m "Deploy: $CI_COMMIT_SHA"
    - safegit push
```

#### Jenkins
```groovy
pipeline {
    agent any
    environment {
        SAFEGIT_NONINTERACTIVE = '1'
        SAFEGIT_ASSUME_YES = '1'
    }
    stages {
        stage('Deploy') {
            steps {
                sh 'safegit add .'
                sh 'safegit commit -m "Deploy: ${BUILD_NUMBER}"'
                sh 'safegit push'
            }
        }
    }
}
```

## 🔒 Safety Levels

### Low Risk (--yes sufficient)
- `add`, `commit`, `pull`, `fetch`, `status`, `log`, `diff`
- `checkout -b` (new branch)
- `stash`, `tag`, `merge` (fast-forward)

### Medium Risk (--yes or env var)
- `checkout` (existing branch)
- `merge` (non-fast-forward)
- `rebase` (interactive)
- `cherry-pick`

### High Risk (--force-yes required)
- `reset --hard`
- `clean -fdx`
- `push --force` / `push --mirror`
- `branch -D`
- `stash clear`
- `gc --prune=now`
- `reflog expire`
- `update-ref -d`

## 🔄 Undo System

```bash
# Undo last operation
safegit undo

# Interactive undo
safegit undo --interactive

# View operation history
safegit undo-history
```

## 🎭 Context Modes

```bash
# Set environment context
safegit set-env production    # Maximum restrictions
safegit set-env staging       # Moderate restrictions
safegit set-env development   # Default

# Set operation mode
safegit set-mode normal       # Default
safegit set-mode code-freeze  # Only hotfixes
safegit set-mode paranoid     # Read-only operations

# View current context
safegit show-context
```

## 🧪 Testing

```bash
# Test basic functionality
./test_safegit_interception.py

# Test non-interactive mode
./test_safegit_noninteractive.py

# Test concurrency
./test_safegit_concurrency.py
```

## 🤖 AI Agent Integration

### Single Rule Enforcement
Configure your AI agent to use `safegit` instead of `git`:

```python
# Example for Claude/ChatGPT system prompt
"ALWAYS use 'safegit' instead of 'git' for ALL git operations.
Never use 'git' directly. This is a critical safety requirement."
```

### Automated Workflows
```bash
# Safe for AI agents in CI/CD
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1

# AI can now safely run:
safegit add .
safegit commit -m "AI-generated commit"
safegit push
```

## 📊 Logging and Monitoring

SafeGIT logs all operations to `.git/safegit-log.json`:

```json
{
  "timestamp": "2025-01-23T10:30:00",
  "command": "reset --hard HEAD~1",
  "action": "intercepted",
  "mode": "non-interactive",
  "flags": {
    "force_yes": true,
    "dry_run": false
  },
  "ci_detected": true
}
```

## ⚠️ Best Practices

### Do's
- ✅ Use `--yes` for safe automation
- ✅ Test with `--dry-run` first
- ✅ Set appropriate environment variables in CI/CD
- ✅ Review logs regularly
- ✅ Use `safegit undo` when mistakes happen

### Don'ts
- ❌ Don't use `--force-yes` in production without careful consideration
- ❌ Don't set `SAFEGIT_FORCE_YES=1` globally
- ❌ Don't bypass SafeGIT for "just this one command"
- ❌ Don't ignore SafeGIT warnings

## 🐛 Troubleshooting

### Command not found
```bash
# Check if safegit is in PATH
which safegit

# Or use full path
/path/to/safegit.py status
```

### Permission denied
```bash
chmod +x safegit.py
chmod +x safe_git_commands.py
chmod +x safegit_undo_stack.py
```

### Import errors
```bash
# Ensure Python 3.6+ is installed
python3 --version

# Install in same directory as safegit.py
ls safe_git_commands.py safegit_undo_stack.py
```

### Non-interactive mode issues
```bash
# Check environment
env | grep SAFEGIT

# Enable debug output
export SAFEGIT_DEBUG=1
```

## 🔧 Configuration

SafeGIT stores configuration in:
- `.git/safegit-context.json` - Environment and mode settings
- `.git/safegit-log.json` - Operation logs
- `.git/safegit-undo-stack.json` - Undo history

## 📈 Performance

- Minimal overhead: ~50ms per command
- Atomic file operations prevent corruption
- Efficient pattern matching with compiled regex
- Smart caching of git state information

## 🤝 Contributing

SafeGIT is part of the code-intelligence-toolkit. Contributions welcome!

1. Test your changes with all test suites
2. Update documentation
3. Follow existing code style
4. Add tests for new features

## 📜 License

Part of the code-intelligence-toolkit project.

## 🙏 Acknowledgments

Created to prevent AI agent disasters and make git safer for everyone.

---

**Remember**: SafeGIT is your safety net, not a replacement for understanding git. Use it to learn safer git practices!