<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Configuration Guide for Code Intelligence Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-19
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Configuration Guide for Code Intelligence Toolkit

**Related Code Files:**
- `common_config.py` - Core configuration system implementation
- `.pytoolsrc.sample` - Sample configuration file with all available options
- `migrate_to_config_paths.py` - Script to migrate tools to use configuration

---

## Overview

The Code Intelligence Toolkit uses a flexible configuration system that allows you to customize tool behavior for your specific project without modifying the tools themselves. This is achieved through a `.pytoolsrc` configuration file.

**For non-interactive environments** (CI/CD, automation), see the [NON_INTERACTIVE_GUIDE.md](NON_INTERACTIVE_GUIDE.md) for specific configuration to avoid EOF errors.

## Quick Start

1. **Create a configuration file from the sample:**
   ```bash
   cp .pytoolsrc.sample .pytoolsrc
   ```

2. **Edit `.pytoolsrc` to match your project structure:**
   ```ini
   [defaults]
   # Set your default source directory
   default_scope = src/main/java/
   
   [paths]
   # Define project-specific paths
   java_source = src/main/java/
   test_directory = src/test/java/
   log_directory = logs/
   ```

3. **Run tools - they'll automatically use your configuration:**
   ```bash
   # Will search in your configured default_scope
   ./run_any_python_tool.sh find_text.py "TODO"
   
   # CLI arguments still override config
   ./run_any_python_tool.sh find_text.py "TODO" --scope lib/
   ```

## Configuration File Structure

The `.pytoolsrc` file uses INI format with sections:

### [defaults] Section
Global defaults that apply to all tools:
```ini
[defaults]
default_scope = .              # Default search directory
ast_context = true             # Enable AST context
check_compile = true           # Enable compile checking
quiet = false                  # Verbosity setting
```

### [paths] Section
Project-specific path definitions:
```ini
[paths]
java_source = src/main/java/
python_source = src/main/python/
test_directory = test/
output_directory = output/
log_directory = logs/
```

### Tool-Specific Sections
Each tool can have its own configuration section:
```ini
[find_text]
# Override defaults for find_text tool
scope = src/main/

[analyze_dependencies]
scope = src/
depth = 5

[log_analyzer]
log_paths = logs/,/var/log/myapp/
```

## How Configuration Works

1. **Configuration Loading Order:**
   - Tools first check for `.pytoolsrc` in the current directory
   - Then search up the directory tree for a `.pytoolsrc` file
   - Stop at the first `.pytoolsrc` found or a `.git` directory

2. **Value Priority (highest to lowest):**
   - Command-line arguments (always win)
   - Tool-specific section in config
   - [defaults] section in config
   - Tool's built-in defaults

3. **Path Resolution:**
   - Relative paths in config are resolved from the project root
   - Absolute paths are used as-is
   - Use forward slashes (/) even on Windows

## Common Configuration Patterns

### Java Project
```ini
[defaults]
default_scope = src/main/java/

[paths]
java_source = src/main/java/
java_test = src/test/java/
resources = src/main/resources/

[dead_code_detector]
analyze_paths = src/main/java/
language = java
```

### Python Project
```ini
[defaults]
default_scope = src/

[paths]
python_source = src/
test_directory = tests/
docs_directory = docs/

[find_text]
exclude_paths = __pycache__/,*.pyc,.pytest_cache/
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

[analyze_dependencies]
# Different scopes for different languages
scope = backend/src/main/java/

[find_text]
# Search everywhere by default
scope = .
```

## Migrating from Hardcoded Paths

If you have tools with hardcoded paths, use the migration script:

```bash
# Automatically update tools to use configuration
python migrate_to_config_paths.py

# Review changes
git diff

# Test the updated tools
./run_any_python_tool.sh find_text.py "test"
```

## Environment Variables

Some paths can also be set via environment variables:
```bash
# Override log directory
export PYTOOLS_LOG_DIR=/var/log/myapp

# Override config file location
export PYTOOLS_CONFIG=~/myproject.pytoolsrc
```

## Best Practices

1. **Keep `.pytoolsrc` in version control** - Share common settings with your team
2. **Use `.pytoolsrc.local` for personal overrides** - Not tracked by git
3. **Document project-specific paths** - Add comments explaining custom paths
4. **Use relative paths** - Makes project portable across machines
5. **Test configuration** - Run `common_config.py --show` to verify settings

## Troubleshooting

### Config not loading?
```bash
# Check if config is found
./run_any_python_tool.sh common_config.py --find-root

# Show current configuration
./run_any_python_tool.sh common_config.py --show
```

### Path not working as expected?
```bash
# Check how paths are resolved
./run_any_python_tool.sh find_text.py "test" -v
# Look for "Scope:" in output
```

### Want to ignore config temporarily?
```bash
# Most tools support --no-config flag
./run_any_python_tool.sh find_text.py "test" --no-config
```

## Example: Complete Project Configuration

Here's a complete example for a typical Java project:

```ini
# Code Intelligence Toolkit Configuration
# Project: MyApp

[defaults]
# Global defaults
default_scope = src/
check_compile = true
ast_context = true
quiet = false

[paths]
# Project structure
java_source = src/main/java/com/mycompany/myapp/
java_test = src/test/java/com/mycompany/myapp/
resources = src/main/resources/
webapp = src/main/webapp/
build_output = target/
logs = logs/

# Tool-specific configurations

[find_text]
# Include test files in searches
scope = src/
exclude_paths = target/,*.class

[analyze_dependencies]
# Focus on main source only
scope = src/main/java/

[dead_code_detector]
# Check both main and test
analyze_paths = src/main/java/,src/test/java/
confidence = high
language = java

[log_analyzer]
# Production logs location
log_paths = logs/,/var/log/myapp/

[recent_files]
# Monitor all source files
monitor_paths = src/
since = 1d

[safe_move]
# Backups location
backup_dir = .backups/

[git_commit_analyzer]
# Important files to track
important_files = pom.xml,README.md,CHANGELOG.md
```

## Summary

The configuration system provides a clean separation between:
- **Generic tools** - No hardcoded paths or project assumptions
- **Project configuration** - All project-specific settings in `.pytoolsrc`
- **User preferences** - Command-line arguments always take precedence

This approach makes the toolkit immediately useful for any project while maintaining flexibility for customization.