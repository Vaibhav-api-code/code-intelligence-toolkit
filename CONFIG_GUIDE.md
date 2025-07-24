<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Configuration Guide for Code Intelligence Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-24
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Configuration Guide for Code Intelligence Toolkit

**Related Code Files:**
- `common_config.py` - Core configuration system implementation
- `.pytoolsrc` - Default configuration file with project settings
- `.pytoolsrc.sample` - Sample configuration file with all available options
- `.pytoolsrc.ci` - CI/CD configuration example
- `setup_config.sh` - Interactive configuration setup script
- `NON_INTERACTIVE_GUIDE.md` - Guide for non-interactive environments

---

## Overview

The Code Intelligence Toolkit uses a flexible configuration system that allows you to customize tool behavior for your specific project without modifying the tools themselves. This is achieved through a `.pytoolsrc` configuration file.

**Key Features:**
- 🔧 Project-specific settings without code changes
- 🤖 Non-interactive mode support for automation
- 🔐 Safety-first defaults with configurable risk levels
- 🚀 Multiple configuration profiles (dev, CI/CD, production)

**For non-interactive environments** (CI/CD, automation), see the [NON_INTERACTIVE_GUIDE.md](NON_INTERACTIVE_GUIDE.md) for specific configuration to avoid EOF errors.

## ⚠️ Critical Safety Warning

**Configuration alone is NOT enough for safety!** You MUST also:

1. **Block direct access to dangerous commands** at the AI/system level
2. **Enforce use of safe tools** through system restrictions
3. **Monitor for bypass attempts** in your logs

### Why This Matters

- **Safe tools can be bypassed** if direct commands are available
- **Configuration is just one layer** of defense
- **AI agents need explicit blocking** of dangerous commands
- **One mistake** with direct access can destroy everything

### Required Actions

```bash
# These commands MUST be blocked at the AI/system level:
# - git (require safegit.py)
# - rm, mv, cp (require safe_file_manager.py)
# - chmod, chown, dd, shred (system-level dangers)
```

See [AI_SAFETY_SETUP.md](AI_SAFETY_SETUP.md) for complete safety configuration.

## Quick Start

### Option 1: Interactive Setup (Recommended)
```bash
# Run the setup script
./setup_config.sh

# This will:
# - Detect your environment
# - Offer configuration choices
# - Create appropriate .pytoolsrc
```

### Option 2: Manual Setup
```bash
# Copy from sample
cp .pytoolsrc.sample .pytoolsrc

# Or use the provided default
# .pytoolsrc is already configured with sensible defaults

# Edit to customize
nano .pytoolsrc
```

### Option 3: Quick CI/CD Setup
```bash
# Use the CI configuration
export PYTOOLSRC=.pytoolsrc.ci

# Or set environment variables
export SFM_ASSUME_YES=1
export SAFEGIT_NONINTERACTIVE=1
```

## Configuration File Structure

The `.pytoolsrc` file uses INI format with sections:

### [defaults] Section
Global defaults that apply to all tools:
```ini
[defaults]
# Path settings
default_scope = .              # Default search directory
source_directory = src/        # Source code location
test_directory = test/         # Test files location

# Behavior settings
ast_context = true             # Enable AST context
check_compile = true           # Enable compile checking
quiet = false                  # Verbosity setting

# Non-interactive settings (NEW)
non_interactive = false        # Set true for automation
assume_yes = false            # Auto-confirm medium-risk ops
force = false                 # Auto-confirm high-risk ops (DANGEROUS!)
auto_confirm = false          # Skip all confirmations

# Safety settings
backup = true                  # Always create backups
dry_run = false               # Preview mode
```

### [paths] Section
Project-specific path definitions:
```ini
[paths]
java_source = src/main/java/
python_source = .
test_directory = test/
output_directory = output/
log_directory = logs/
backup_directory = .backups/
documentation = docs/
examples = examples/
```

### Tool-Specific Sections
Each tool can have its own configuration:
```ini
[safe_file_manager]
non_interactive = false        # Tool-specific override
assume_yes = false
verify_checksum = true
preserve_attrs = true

[replace_text]
backup = true
whole_word = false
non_interactive = false

[git_commit_analyzer]
non_interactive = false
auto_stage = false
```

## Non-Interactive Configuration

### Environment Variables (Highest Priority)
```bash
# Safe File Manager
export SFM_ASSUME_YES=1              # Auto-confirm all operations

# SafeGIT
export SAFEGIT_NONINTERACTIVE=1      # Non-interactive mode
export SAFEGIT_ASSUME_YES=1          # Auto-confirm safe operations
export SAFEGIT_FORCE_YES=1           # Auto-confirm dangerous operations

# Global (if supported by tools)
export PYTOOLSRC_NON_INTERACTIVE=1   # Global non-interactive
export PYTOOLSRC_ASSUME_YES=1        # Global auto-confirm

# Use different config file
export PYTOOLSRC=.pytoolsrc.ci       # Use CI configuration
```

### Configuration Profiles

#### Development (.pytoolsrc)
```ini
[defaults]
non_interactive = false        # Interactive prompts
assume_yes = false            # Require confirmation
quiet = false                 # Show progress
check_compile = true          # Verify code changes
```

#### CI/CD (.pytoolsrc.ci)
```ini
[defaults]
non_interactive = true         # No prompts
assume_yes = true             # Auto-confirm medium-risk
quiet = true                  # Less output
check_compile = false         # Skip compile checks
```

#### Production (.pytoolsrc.prod)
```ini
[defaults]
non_interactive = true         # No prompts
assume_yes = false            # Still require confirmations
force = false                 # Never auto-force
backup = true                 # Always backup
paranoid_mode = true          # Extra safety checks
```

## How Configuration Works

### 1. Configuration Loading Order:
- Environment variables (highest priority)
- Command-line arguments
- Tool-specific section in config
- [defaults] section in config
- Tool's built-in defaults (lowest priority)

### 2. Config File Discovery:
- Check current directory for `.pytoolsrc`
- Search up directory tree until found
- Stop at first `.pytoolsrc` or `.git` directory
- Use `PYTOOLSRC` env var to specify custom location

### 3. Path Resolution:
- Relative paths resolved from config file location
- Absolute paths used as-is
- Use forward slashes (/) on all platforms

## Safety Levels and Risk Management

### Risk Levels
```ini
# Low Risk (safe to auto-confirm)
- Reading files
- Listing directories
- Dry-run operations

# Medium Risk (requires assume_yes)
- Moving files (with backup)
- Text replacements (with backup)
- Git add, commit

# High Risk (requires force flag)
- Deleting files
- Overwriting without backup
- Git reset --hard, clean
```

### Safety Configuration
```ini
[defaults]
# NEVER set these together in production:
non_interactive = true
force = true              # This bypasses ALL safety checks!

# Instead, use targeted overrides:
# SAFE_FILE_FORCE=1 ./run_any_python_tool.sh safe_file_manager.py trash temp/
```

## Common Configuration Patterns

### Standard Development Setup
```ini
[defaults]
default_scope = .
non_interactive = false
assume_yes = false
backup = true
verbose = false

[paths]
source_directory = src/
test_directory = test/
documentation = docs/
```

### Automated Testing Environment
```ini
[defaults]
non_interactive = true
assume_yes = true
quiet = true
dry_run = false

[safe_file_manager]
non_interactive = true
assume_yes = true

[replace_text]
non_interactive = true
check_compile = false
```

### Multi-Language Project
```ini
[defaults]
default_scope = .

[paths]
java_source = backend/src/main/java/
python_source = scripts/
javascript_source = frontend/src/
docs = documentation/

[find_text]
scope = .
exclude_paths = node_modules/,__pycache__/,target/
```

## Testing Your Configuration

### View Current Configuration
```bash
# Show loaded configuration
./run_any_python_tool.sh common_config.py --show

# Find config file location
./run_any_python_tool.sh common_config.py --find-root

# Test specific tool config
./run_any_python_tool.sh find_text.py "test" --dry-run -v
```

### Test Non-Interactive Mode
```bash
# Test in subshell with no stdin
(exec < /dev/null && ./run_any_python_tool.sh safe_file_manager.py list .)

# Should work without prompts if configured correctly
```

## Best Practices

1. **Version Control**
   - Track `.pytoolsrc` for team settings
   - Use `.pytoolsrc.local` for personal overrides
   - Add `.pytoolsrc.local` to `.gitignore`

2. **Environment-Specific Configs**
   ```bash
   .pytoolsrc          # Default/development
   .pytoolsrc.ci       # CI/CD pipelines
   .pytoolsrc.test     # Test environments
   .pytoolsrc.prod     # Production (if applicable)
   ```

3. **Safety First**
   - Never set `force = true` in committed configs
   - Use environment variables for temporary overrides
   - Test with `--dry-run` before automation

4. **Documentation**
   ```ini
   # Document your settings
   [paths]
   # Main application source
   java_source = src/main/java/com/example/
   
   # Generated code - excluded from most operations
   generated = target/generated-sources/
   ```

## Troubleshooting

### Config Not Loading?
```bash
# Check discovery
./run_any_python_tool.sh common_config.py --find-root

# Verify parsing
./run_any_python_tool.sh common_config.py --show

# Check environment
echo $PYTOOLSRC
```

### EOF Errors in Automation?
```bash
# Quick fix
export SFM_ASSUME_YES=1
export SAFEGIT_NONINTERACTIVE=1

# Or use CI config
export PYTOOLSRC=.pytoolsrc.ci
```

### Path Resolution Issues?
```bash
# Test path resolution
./run_any_python_tool.sh find_text.py "test" -v
# Look for "Resolved scope:" in output

# Use absolute paths for debugging
default_scope = /absolute/path/to/source/
```

## Advanced Features

### Conditional Configuration
```bash
# Use different configs per environment
if [ "$CI" = "true" ]; then
    export PYTOOLSRC=.pytoolsrc.ci
elif [ "$USER" = "jenkins" ]; then
    export PYTOOLSRC=.pytoolsrc.jenkins
fi
```

### Tool Chaining with Configs
```bash
# Each tool respects the same config
./run_any_python_tool.sh find_text.py "TODO" | \
./run_any_python_tool.sh extract_methods.py | \
./run_any_python_tool.sh analyze_complexity.py
```

### Override Precedence
```bash
# CLI > ENV > tool-section > defaults > built-in
./run_any_python_tool.sh find_text.py "test" \
    --scope override/path/           # Wins over all configs
```

## Migration Guide

### From Hardcoded Paths
```bash
# Update tools automatically
python migrate_to_config_paths.py

# Review changes
git diff

# Test migrated tools
./run_any_python_tool.sh find_text.py "test"
```

### From Manual Confirmation
```bash
# Before: Always prompted
./tool.py  # "Continue? [y/N]"

# After: Configured
# .pytoolsrc:
[tool]
assume_yes = true

./tool.py  # No prompt!
```

## Summary

The configuration system provides:
- **Flexibility** - Adapt tools to any project structure
- **Safety** - Configurable risk management
- **Automation** - Full non-interactive support
- **Portability** - Share configs with your team
- **Simplicity** - Override anything from CLI when needed

Start with the defaults, customize as needed, and use environment variables for temporary overrides. The tools will just work!