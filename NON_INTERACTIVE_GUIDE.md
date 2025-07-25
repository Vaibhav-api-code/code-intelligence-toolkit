<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Non-Interactive Mode Configuration Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-24
Updated: 2025-07-24
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Non-Interactive Mode Configuration Guide

This guide explains how to configure the Code Intelligence Toolkit for non-interactive environments to avoid EOF errors and enable automation.

> **📚 Note**: For comprehensive documentation including all tools, CI/CD examples, and best practices, see the [Comprehensive Non-Interactive Mode Guide](docs/NON_INTERACTIVE_MODE_GUIDE.md).

## 🚨 The Problem

When running tools in non-interactive environments (CI/CD, automation, AI agents), you may encounter:
```
❌ Error: EOF when reading a line
```

This happens when tools expect user input but stdin is not available.

## ✅ Solutions

### 1. Environment Variables (Recommended for Temporary Use)

Set these before running tools:

```bash
# For safe_file_manager.py
export SFM_ASSUME_YES=1              # Auto-confirm all operations

# For SafeGIT
export SAFEGIT_NONINTERACTIVE=1      # Non-interactive mode
export SAFEGIT_ASSUME_YES=1          # Auto-confirm safe operations

# Global settings (if tools support them)
export PYTOOLSRC_NON_INTERACTIVE=1   # Global non-interactive mode
export PYTOOLSRC_ASSUME_YES=1        # Global auto-confirm
```

### 2. Configuration File (.pytoolsrc)

Create or modify `.pytoolsrc` in your project root:

```ini
[defaults]
# Enable non-interactive mode globally
non_interactive = true    # No prompts, fail if input needed
assume_yes = true        # Auto-confirm medium-risk operations
force = false           # Keep false unless you're sure!

[safe_file_manager]
non_interactive = true
assume_yes = true

[replace_text]
non_interactive = true
assume_yes = true
```

### 3. Command-Line Flags

Most tools support these flags:

```bash
# Safe file operations
./run_any_python_tool.sh safe_file_manager.py move file1 file2 --yes

# Text replacement
./run_any_python_tool.sh replace_text.py "old" "new" file.txt --yes

# SafeGIT operations
./run_any_python_tool.sh safegit.py add . --yes
```

## 📋 Tool-Specific Settings

### safe_file_manager.py

```bash
# Method 1: Environment variable
SFM_ASSUME_YES=1 ./run_any_python_tool.sh safe_file_manager.py move src dst

# Method 2: Command flag
./run_any_python_tool.sh safe_file_manager.py move src dst --yes

# Method 3: Config file
# Add to .pytoolsrc:
[safe_file_manager]
assume_yes = true
```

### SafeGIT

```bash
# Method 1: Configuration file (.pytoolsrc)
# Add to .pytoolsrc:
[safegit]
non_interactive = true
assume_yes = true
# Then just run:
./run_any_python_tool.sh safegit.py add .

# Method 2: Environment variables (override config)
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1
./run_any_python_tool.sh safegit.py add .

# Method 3: Command flags
./run_any_python_tool.sh safegit.py add . --yes
```

### Other Tools

Check tool help for specific flags:
```bash
./run_any_python_tool.sh [tool_name] --help | grep -E "(yes|interactive|confirm)"
```

## 🏗️ CI/CD Configuration

### GitHub Actions Example

```yaml
env:
  SFM_ASSUME_YES: 1
  SAFEGIT_NONINTERACTIVE: 1
  SAFEGIT_ASSUME_YES: 1

steps:
  - name: Run toolkit operations
    run: |
      ./run_any_python_tool.sh safe_file_manager.py organize src/
      ./run_any_python_tool.sh replace_text.py "old" "new" --scope src/
```

### Docker Example

```dockerfile
ENV SFM_ASSUME_YES=1
ENV SAFEGIT_NONINTERACTIVE=1
ENV PYTOOLSRC_NON_INTERACTIVE=1
```

### Create CI-Specific Config

Create `.pytoolsrc.ci`:
```ini
[defaults]
non_interactive = true
assume_yes = true
quiet = true
force = false  # Still require explicit --force for dangerous operations

[safe_file_manager]
non_interactive = true
assume_yes = true

[safegit]
non_interactive = true
assume_yes = true
```

Then use it:
```bash
export PYTOOLSRC=.pytoolsrc.ci
./run_any_python_tool.sh [commands]
```

## ⚠️ Safety Considerations

### Risk Levels

1. **Low Risk** (auto-confirm safe):
   - Reading files
   - Listing directories
   - Dry-run operations

2. **Medium Risk** (requires `assume_yes`):
   - Moving files (with backup)
   - Text replacements (with backup)
   - Git add/commit

3. **High Risk** (requires `force`):
   - Deleting files (even to trash)
   - Overwriting without backup
   - Git reset --hard

### Best Practices

1. **Development**: Keep interactive mode (default)
2. **Testing**: Use `--dry-run` first
3. **Automation**: Use environment variables
4. **Production**: Create specific config files

### Safety Rules

```ini
# NEVER set these in production .pytoolsrc:
force = true         # This allows destructive operations!

# Instead, use environment variables for specific operations:
SAFE_FILE_FORCE=1 ./run_any_python_tool.sh safe_file_manager.py trash old_files/
```

## 🔧 Troubleshooting

### Still Getting EOF Errors?

1. Check if tool supports non-interactive mode:
   ```bash
   ./run_any_python_tool.sh [tool] --help | grep -i interactive
   ```

2. Try multiple methods:
   ```bash
   # Combine environment variable and flag
   SFM_ASSUME_YES=1 ./run_any_python_tool.sh safe_file_manager.py move a b --yes
   ```

3. Use wrapper script for stubborn tools:
   ```bash
   echo "y" | ./run_any_python_tool.sh [tool] [args]
   ```

### Testing Non-Interactive Mode

```bash
# Test in a subshell with no stdin
(exec < /dev/null && ./run_any_python_tool.sh safe_file_manager.py list .)
```

## 📚 Examples

### Automated File Organization
```bash
# Set up environment
export SFM_ASSUME_YES=1

# Run operations
./run_any_python_tool.sh safe_file_manager.py organize ~/Downloads --by-type
./run_any_python_tool.sh safe_file_manager.py trash *.tmp
```

### Batch Text Replacement
```bash
# Create batch config
cat > .pytoolsrc.batch << EOF
[defaults]
non_interactive = true
assume_yes = true

[replace_text]
backup = true
check_compile = false
EOF

# Use it
PYTOOLSRC=.pytoolsrc.batch ./run_any_python_tool.sh replace_text.py "old" "new" src/
```

### Safe Git Automation
```bash
# Option 1: Using .pytoolsrc configuration
# Add to .pytoolsrc:
[safegit]
non_interactive = true
assume_yes = true

# Option 2: Using environment variables
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1

# Run git operations (works with either option)
./run_any_python_tool.sh safegit.py add .
./run_any_python_tool.sh safegit.py commit -m "Automated update"
```

## 🎯 Quick Reference

| Tool | Environment Variable | Config Section | Command Flag |
|------|---------------------|----------------|--------------|
| safe_file_manager | `SFM_ASSUME_YES=1` | `[safe_file_manager]` | `--yes`, `-y` |
| SafeGIT | `SAFEGIT_ASSUME_YES=1`<br>`SAFEGIT_NONINTERACTIVE=1` | `[safegit]` | `--yes`, `--force-yes`, `--non-interactive` |
| safe_move | `SAFEMOVE_ASSUME_YES=1`<br>`SAFEMOVE_NONINTERACTIVE=1` | `[safe_move]` | `--yes`, `-y`, `--no-confirm` |
| replace_text | - | `[replace_text]` | `--yes`, `-y` |
| replace_text_ast | `REPLACE_TEXT_AST_ASSUME_YES=1` | `[replace_text_ast]` | `--yes`, `-y`, `--no-confirm` |
| refactor_rename | `REFACTOR_ASSUME_YES=1` | `[refactor_rename]` | `--yes`, `-y`, `--no-confirm` |
| All tools | `PYTOOLSRC_NON_INTERACTIVE=1` | `[defaults]` | varies |

## 🔧 Advanced Configuration

### Configuration Hierarchy

Tools check for non-interactive settings in this order (first found wins):

1. **Command-line flags** - Highest priority
2. **Environment variables** - Override config files
3. **Configuration file** (.pytoolsrc) - Project defaults
4. **Tool defaults** - Interactive mode

### Safety Levels

1. **Low Risk** (auto-confirmed with assume_yes):
   - Reading files, listing directories
   - Dry-run operations, creating backups
   - Git status, log, diff

2. **Medium Risk** (requires assume_yes or --yes):
   - Moving/copying files (with backup)
   - Text replacements (with backup)
   - Git add, commit, pull
   - Creating directories

3. **High Risk** (requires explicit force or --force-yes):
   - Deleting files (even to trash)
   - Overwriting without backup
   - Git reset --hard, clean -fdx
   - Git push --force, rebase operations

### Testing Non-Interactive Mode

```bash
# Test with no stdin
(exec < /dev/null && ./run_any_python_tool.sh safe_file_manager.py list .)

# Test with explicit flags
./run_any_python_tool.sh safe_file_manager.py move test1.txt test2.txt --dry-run --yes

# Create test configuration
cat > .pytoolsrc.test << EOF
[defaults]
non_interactive = true
assume_yes = true
dry_run = true
EOF

PYTOOLSRC=.pytoolsrc.test ./run_any_python_tool.sh safe_file_manager.py organize test_dir/
```

Remember: **Safety first!** Test thoroughly before enabling non-interactive mode in production.