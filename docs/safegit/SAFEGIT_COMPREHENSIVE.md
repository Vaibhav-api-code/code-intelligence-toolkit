<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT - Comprehensive Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT - Comprehensive Documentation

**Version**: 2.0 (with Non-Interactive Support)  
**Last Updated**: January 23, 2025

**Related Code Files:**
- `safegit.py` - Main wrapper with interception logic (1226 lines)
- `safe_git_commands.py` - Core safety analysis engine (830 lines)
- `safegit_undo_stack.py` - Multi-level undo system with atomic metadata capture
- `test_safegit_*.py` - Comprehensive test suites

---

## 🛡️ Overview

SafeGIT is an enterprise-grade protective wrapper around git that prevents accidental data loss from dangerous operations. Originally designed to prevent AI agent disasters (like the Replit incident), it now supports both interactive safety education and fully automated workflows for CI/CD pipelines.

## 🎯 Core Philosophy

SafeGIT operates on three principles:
1. **Prevention is better than recovery** - Intercept dangerous commands before execution
2. **Education over restriction** - Teach users safer alternatives
3. **Zero friction for safe operations** - Only intervene for dangerous commands

## 🚀 Key Features

### Safety Features
- **37+ Dangerous Pattern Detection**: Comprehensive coverage of all common git disasters
- **Automatic Backups**: Creates stashes/backups before destructive operations
- **Smart Conversions**: Converts dangerous commands to safer alternatives
- **Multi-Level Undo System**: Complete operation history with recovery paths
- **Branch Protection Detection**: Platform-specific protection rules (GitHub, GitLab, Bitbucket)
- **Atomic File Operations**: Thread-safe with cross-platform file locking
- **Risk Assessment**: Graduated confirmations based on operation danger level

### Educational Features
- **Recovery Hints**: Shows reflog commands after potentially dangerous operations
- **Impact Analysis**: Explains what each command will do before execution
- **Alternative Suggestions**: Recommends safer approaches
- **Dry-Run Mode**: Preview command effects without execution

### Automation Features (NEW in v2.0)
- **Non-Interactive Mode**: Full CI/CD and script support
- **Graduated Safety Levels**: Different flags for different risk levels
- **Environment Variables**: Comprehensive configuration options
- **CI Platform Auto-Detection**: Works seamlessly in automated environments
- **Automation Logging**: Complete audit trail of automated operations

## 📦 Installation

### Method 1: Symlink (Recommended)
```bash
chmod +x safegit.py
sudo ln -s $(pwd)/safegit.py /usr/local/bin/safegit

# Verify installation
safegit --version
```

### Method 2: Alias
```bash
alias git='python3 /path/to/safegit.py'
echo "alias git='python3 /path/to/safegit.py'" >> ~/.bashrc
```

### Method 3: Executable Script
```bash
chmod +x safegit.py
sudo cp safegit.py /usr/local/bin/safegit
```

## ⚙️ Configuration

SafeGIT supports multiple configuration methods with a clear priority hierarchy.

### Configuration File (.pytoolsrc)

SafeGIT integrates with the Code Intelligence Toolkit's unified configuration system. Create a `.pytoolsrc` file in your project root:

```ini
[safegit]
# Non-interactive mode settings
non_interactive = false    # Set to true for CI/CD environments
assume_yes = false        # Auto-confirm safe operations
force_yes = false         # DANGEROUS: Auto-confirm ALL operations
dry_run = false           # Preview mode - show what would happen

# You can also use the [defaults] section for common settings
[defaults]
# These apply to SafeGIT if [safegit] section is not present
dry_run = false
assume_yes = false
```

### Configuration Priority

1. **Command-line flags** (highest priority)
   - `--yes`, `--force-yes`, `--dry-run`, `--non-interactive`

2. **Environment variables**
   - `SAFEGIT_NONINTERACTIVE`, `SAFEGIT_ASSUME_YES`, `SAFEGIT_FORCE_YES`

3. **Configuration file** (.pytoolsrc)
   - `[safegit]` section settings
   - `[defaults]` section (fallback)

4. **Built-in defaults** (lowest priority)
   - All features disabled by default

### Example Configurations

#### Development Environment
```ini
[safegit]
non_interactive = false
assume_yes = false
dry_run = false
```

#### CI/CD Environment
```ini
[safegit]
non_interactive = true
assume_yes = true
force_yes = false    # Still require explicit --force for dangerous ops
dry_run = false
```

#### Testing Environment
```ini
[safegit]
non_interactive = true
assume_yes = true
force_yes = false
dry_run = true       # Preview all operations
```

## 🎮 Usage Modes

### Interactive Mode (Default)

SafeGIT provides graduated protection based on operation risk:

#### Safe Operations (Pass Through)
```bash
safegit status
safegit log
safegit diff
safegit add file.txt
safegit commit -m "message"
safegit pull
safegit fetch
```

#### Medium Risk (Warnings & Confirmations)
```bash
safegit checkout main       # Warns about uncommitted changes
safegit merge feature       # Checks for conflicts
safegit rebase main        # History rewrite warning
```

#### High Risk (Typed Confirmations & Backups)
```bash
safegit reset --hard       # Creates stash, requires "PROCEED"
safegit clean -fdx         # Creates zip backup, requires "DELETE"
safegit push --force       # Converts to --force-with-lease, requires risk acceptance
```

### Non-Interactive Mode (v2.0)

Perfect for CI/CD pipelines and automated scripts:

#### Command-Line Flags
```bash
# Auto-confirm safe operations
safegit --yes add .
safegit --yes commit -m "Automated commit"
safegit --yes pull

# Force dangerous operations (use with extreme caution!)
safegit --force-yes reset --hard HEAD~1
safegit --force-yes clean -fdx

# Strict non-interactive mode (fails on any prompt)
safegit --non-interactive --yes status
safegit --batch --force-yes push
```

#### Configuration Methods

##### Method 1: Configuration File (.pytoolsrc) - RECOMMENDED
```ini
# Create or edit .pytoolsrc in your project root
[safegit]
non_interactive = false    # Set to true for automation
assume_yes = false        # Set to true to auto-confirm safe operations
force_yes = false         # DANGEROUS: Set to true only in fully automated environments
dry_run = false           # Set to true to preview commands without executing
```

##### Method 2: Environment Variables (Override Config)
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

**Priority Order**: Environment variables > .pytoolsrc config > Built-in defaults

#### Graduated Safety Levels

1. **Low Risk** (works with `--yes` or `SAFEGIT_ASSUME_YES`):
   - add, commit, pull, fetch, status, log, diff
   - checkout -b (new branch)
   - stash, tag, merge (fast-forward)

2. **Medium Risk** (requires `--yes` with warnings):
   - checkout (existing branch)
   - merge (non-fast-forward)
   - rebase (interactive)
   - cherry-pick

3. **High Risk** (requires `--force-yes` or `SAFEGIT_FORCE_YES`):
   - reset --hard
   - clean -fdx
   - push --force / push --mirror
   - branch -D
   - stash clear
   - gc --prune=now
   - reflog expire
   - update-ref -d

### Dry-Run Mode

Preview any command's effects without execution:

```bash
safegit --dry-run reset --hard HEAD~3
# Output: Would reset to 3 commits ago, losing changes in: file1.js, file2.py

safegit --dry-run clean -fdx
# Output: Would delete 15 untracked files (total size: 2.3MB)

safegit --dry-run push --force origin main
# Output: Would force push, overwriting 5 remote commits
```

## 🔄 Undo System

SafeGIT maintains a complete operation history with recovery paths:

```bash
# Undo last operation
safegit undo

# Interactive undo (select from history)
safegit undo --interactive

# View operation history
safegit undo-history

# Export complete history
safegit export-history
```

Each undo entry includes:
- Original command and parameters
- Repository state at time of operation
- Automatic backups (if created)
- Recovery script with exact commands
- Recovery hints and best practices

## 🎭 Context Awareness

SafeGIT adapts its behavior based on environment and workflow:

### Environment Context
```bash
safegit set-env production    # Maximum restrictions
safegit set-env staging       # Moderate restrictions
safegit set-env development   # Default restrictions
```

**Environment-Specific Restrictions:**

- **development** (default): Standard SafeGIT protections apply
- **staging**: Standard protections, similar to development
- **production**: Maximum safety restrictions
  - No force pushes (`push --force`, `push -f`)
  - No hard resets (`reset --hard`)
  - No force cleans (`clean -fdx`, `clean -fxd`)
  - No rebasing operations

### Work Mode
```bash
safegit set-mode normal       # Default behavior
safegit set-mode code-freeze  # Only critical fixes allowed
safegit set-mode maintenance  # Reserved for future use
safegit set-mode paranoid     # Allowlist approach (only safe commands)
```

**Mode-Specific Restrictions:**

- **normal** (default): Standard SafeGIT behavior with all safety features
- **code-freeze**: Restricts write operations except for hotfix branches
  - Blocks: push, commit, merge, rebase, reset, clean
  - Exception: Commands containing "hotfix" or "HOTFIX" are allowed
  - Perfect for release periods when only critical fixes should be merged
- **maintenance**: Currently same as normal mode (reserved for future features)
- **paranoid**: Allowlist approach - only explicitly safe commands are permitted
  - Allowed base commands: status, log, diff, fetch, show, ls-files, branch, tag, remote
  - Additional restrictions on allowed commands:
    - `branch`: No deletion flags (-d, -D, --delete)
    - `tag`: Only listing allowed (-l, --list, -n)
    - `remote`: Only show/get-url/-v allowed

### View Current Context
```bash
safegit show-context
# Output: Environment: production, Mode: code-freeze

# JSON output for scripting
safegit show-context --json
# Output: {"environment": "production", "mode": "code-freeze", "restrictions": [], ...}
```

### Custom Restrictions
```bash
# Add custom pattern-based restrictions
safegit add-restriction "experimental"     # Blocks any command containing "experimental"
safegit add-restriction "force"           # Blocks any command containing "force"

# Remove restrictions
safegit remove-restriction "experimental"

# View all restrictions in current context
safegit show-context
```

### Context Persistence

All context settings are stored in `.git/safegit-context.json` and persist across sessions. The file includes:
- Current environment and mode
- Custom restrictions list
- Creation and last update timestamps

### Practical Examples

```bash
# Production deployment scenario
safegit set-env production
safegit set-mode code-freeze
# Now only hotfix branches can be pushed, no force operations allowed

# Development with experimental features
safegit set-env development
safegit add-restriction "experimental"
# Prevents accidental commits to experimental branches

# Maximum safety for junior developers
safegit set-mode paranoid
# Only read operations allowed, perfect for code review sessions
```

## 🤖 AI Agent Integration

### The Problem
AI agents executing git commands can cause catastrophic data loss, as seen in the Replit incident where an AI deleted an entire production database.

### The Solution
SafeGIT provides comprehensive protection through a single rule:

```python
# For any AI system - just replace 'git' with 'safegit'
command = command.replace('git ', 'safegit ')
```

### Implementation Examples

#### Recommended: Configuration File Setup

For AI agents, the safest approach is to configure SafeGIT via `.pytoolsrc`:

```ini
# .pytoolsrc for AI agents
[safegit]
non_interactive = true    # No prompts in AI context
assume_yes = true        # Auto-confirm safe operations
force_yes = false        # Never auto-confirm dangerous operations
dry_run = false          # Set to true for testing
```

This ensures consistent behavior without relying on environment variables that might be forgotten.

#### OpenAI Function Calling
```python
@tool
def run_git_command(command: str, auto_confirm: bool = False) -> str:
    """Run a git command safely using safegit wrapper."""
    if command.startswith('git '):
        raise ValueError("Direct git commands are forbidden. Use 'safegit' instead.")
    
    if not command.startswith('safegit '):
        command = f'safegit {command}'
    
    # Optional: Override config with environment variables
    env = os.environ.copy()
    if auto_confirm:
        env['SAFEGIT_NONINTERACTIVE'] = '1'
        env['SAFEGIT_ASSUME_YES'] = '1'
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
    return result.stdout + result.stderr
```

### ⚠️ CRITICAL: Blocking Direct Git Access

**SafeGIT only works if direct git access is blocked!** You MUST configure your AI agents to prevent direct git command execution.

#### Required Blocking Configuration

1. **System Prompt / Instructions**
   ```markdown
   You are FORBIDDEN from using 'git' commands directly.
   ALWAYS use 'safegit' or './run_any_python_tool.sh safegit.py' instead.
   Direct git commands like 'git reset --hard' are strictly prohibited.
   ```

2. **Function-Level Blocking**
   ```python
   BLOCKED_COMMANDS = ['git', 'rm', 'mv', 'cp', 'dd', 'shred']
   
   def execute_command(cmd: str):
       base_cmd = cmd.split()[0]
       if base_cmd in BLOCKED_COMMANDS:
           raise ValueError(f"Direct '{base_cmd}' is forbidden. Use safe wrappers.")
   ```

3. **Command Replacement**
   ```python
   # Automatically replace git with safegit
   if cmd.startswith('git '):
       cmd = cmd.replace('git ', 'safegit ', 1)
   ```

#### Why This Is Critical

- **AI doesn't understand danger** - It will happily run `git reset --hard` if allowed
- **One command can destroy everything** - No undo for direct git operations
- **SafeGIT can be bypassed** - If direct git access exists, protection is useless
- **Defense requires blocking** - You must block at the source

#### Testing Your Blocking

```bash
# These should ALL be rejected by your AI:
test_commands=(
    "git reset --hard HEAD~10"
    "git clean -fdx"
    "git push --force origin main"
    "rm -rf important_directory"
)

# If ANY of these execute, your AI setup is unsafe!
```

See [AI_SAFETY_SETUP.md](../../AI_SAFETY_SETUP.md) for complete configuration instructions.

#### CI/CD Integration

##### GitHub Actions
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

##### GitLab CI
```yaml
deploy:
  script:
    - export SAFEGIT_ASSUME_YES=1
    - safegit add .
    - safegit commit -m "Deploy: $CI_COMMIT_SHA"
    - safegit push
```

## 🛡️ Protected Operations

### Complete Coverage List

SafeGIT protects against 37+ dangerous operations, including:

#### Destructive Operations
- `reset --hard` - Creates automatic stash before reset
- `clean -fdx` - Creates zip backup of all files to be deleted
- `checkout --force` - Stashes changes before force checkout
- `switch --discard-changes` - Protects uncommitted work

#### History Rewriting
- `rebase` - Warns about history changes, shows recovery
- `commit --amend` - Checks if commit was already pushed
- `filter-branch` - Extreme warnings about repository corruption

#### Remote Operations
- `push --force` - Converts to `--force-with-lease`, checks branch protection
- `push --mirror` - Requires "MIRROR PUSH" confirmation
- `push --delete` - Remote branch deletion protection

#### Reference Operations
- `branch -D` - Local branch deletion warnings
- `update-ref -d` - Low-level reference deletion protection
- `reflog expire` - Safety net removal warnings

#### Repository Maintenance
- `gc --prune=now` - Immediate garbage collection warnings
- `gc --aggressive` - Performance impact warnings
- `stash clear` - Creates text backup before clearing

## 📊 Logging and Monitoring

SafeGIT maintains comprehensive logs for all operations:

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
  "ci_detected": true,
  "backup_created": {
    "type": "stash",
    "ref": "stash@{0}",
    "message": "SAFEGIT: Auto-backup before reset --hard"
  }
}
```

Log locations:
- `.git/safegit-log.json` - All operations
- `.git/safegit-undo-stack.json` - Undo history
- `.git/safegit-context.json` - Environment settings

## ⚡ Performance

- **Overhead**: ~50ms per command (negligible)
- **Backup Creation**: <1 second for most operations
- **Pattern Matching**: Compiled regex for efficiency
- **Atomic Operations**: Thread-safe with minimal locking

## 🐛 Troubleshooting

### SafeGIT not intercepting commands
```bash
# Verify you're using safegit, not git
which git
which safegit

# Check if alias is set
alias | grep git
```

### Permission denied errors
```bash
chmod +x safegit.py
chmod +x safe_git_commands.py
chmod +x safegit_undo_stack.py
```

### Non-interactive mode not working
```bash
# Check configuration file
cat .pytoolsrc | grep -A 5 "\[safegit\]"

# Check environment variables (these override config)
env | grep SAFEGIT

# Enable debug output
export SAFEGIT_DEBUG=1

# Test configuration loading
python3 -c "from common_config import load_config, get_config_value; \
  config = load_config(); \
  print('non_interactive:', get_config_value('safegit', 'non_interactive', False, config)); \
  print('assume_yes:', get_config_value('safegit', 'assume_yes', False, config))"
```

### Import errors
```bash
# Ensure Python 3.6+ is installed
python3 --version

# Check all files are in same directory
ls safe_git_commands.py safegit_undo_stack.py
```

## 🏗️ Architecture

### Component Overview

1. **safegit.py** (1226 lines)
   - Main entry point and command interceptor
   - Pattern matching engine
   - Handler dispatch system
   - Non-interactive mode logic

2. **safe_git_commands.py** (830 lines)
   - Core safety analysis
   - Backup creation logic
   - State verification
   - Recovery hint generation

3. **safegit_undo_stack.py**
   - Atomic undo journal
   - Operation metadata capture
   - Recovery script generation
   - Cross-platform file locking

### Design Principles

1. **Fail-Safe**: Always err on the side of caution
2. **Atomic Operations**: All-or-nothing file operations
3. **Educational**: Teach users safer git practices
4. **Zero Data Loss**: Multiple backup mechanisms
5. **Cross-Platform**: Works on Windows, macOS, Linux

## 🎯 Best Practices

### For Interactive Users
- ✅ Use SafeGIT as your default git interface
- ✅ Pay attention to warnings and suggestions
- ✅ Use dry-run mode when unsure
- ✅ Learn from recovery hints
- ✅ Review operation history regularly

### For CI/CD Pipelines
- ✅ Use `--yes` for safe automation
- ✅ Test with `--dry-run` in staging
- ✅ Set appropriate environment variables
- ✅ Monitor logs for blocked operations
- ✅ Use graduated safety levels appropriately

### For AI Agents
- ✅ Always use 'safegit' instead of 'git'
- ✅ Configure non-interactive mode
- ✅ Handle blocked operations gracefully
- ✅ Log all git operations
- ✅ Never use `--force-yes` without human approval

## 📈 Future Enhancements

Planned features for future versions:
- Remote repository state caching
- Team-wide safety policies
- Integration with git hooks
- Machine learning for risk assessment
- Visual operation history browser

## 🤝 Contributing

SafeGIT is part of the code-intelligence-toolkit project. Contributions welcome!

1. Test thoroughly with all test suites
2. Update documentation
3. Follow existing patterns
4. Add tests for new features
5. Consider backward compatibility

## 📜 License

Part of the code-intelligence-toolkit project.

---

**Remember**: SafeGIT is your safety net, not a replacement for understanding git. Use it to learn safer git practices and prevent disasters before they happen!