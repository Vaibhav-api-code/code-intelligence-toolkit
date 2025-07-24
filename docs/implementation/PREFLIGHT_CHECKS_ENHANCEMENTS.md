<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Preflight Checks Enhancements

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-09
Updated: 2025-07-09
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Preflight Checks Enhancements

**Related Code Files:**
- `preflight_checks.py` - Main preflight checks module
- `test/test_preflight_checks.py` - Unit tests for preflight checks
- `example_preflight_usage.py` - Usage examples and best practices

---

## Overview

The `preflight_checks.py` module has been significantly enhanced to provide comprehensive validation capabilities for Python development tools. These enhancements help catch errors early, improve security, and ensure robust operation across different environments.

## New Validation Categories

### 1. Pattern Validation
- **`check_regex_pattern(pattern)`** - Validates regular expression patterns before use
- **`check_glob_pattern(pattern)`** - Validates glob patterns, detecting overly complex patterns

### 2. Git Integration
- **`check_git_repository(path)`** - Verifies if path is within a git repository
- Handles timeouts and missing git installations gracefully

### 3. Python Environment
- **`check_python_version(min_version)`** - Ensures minimum Python version requirements
- **`check_import_available(module_name)`** - Verifies required modules are installed
- **`check_command_available(command)`** - Checks if system commands are available

### 4. File Content Analysis
- **`check_binary_file(path)`** - Detects binary files to prevent text processing errors
- **`check_encoding(path, encoding)`** - Validates file encoding before reading
- **`check_file_not_too_new(path, max_age_seconds)`** - Avoids race conditions with recently modified files

### 5. System Resources
- **`check_disk_space(path, required_mb)`** - Ensures sufficient disk space
- **`check_memory_available(required_mb)`** - Checks available system memory
- **`check_file_permissions(path, need_write)`** - Comprehensive permission checks

## Enhanced Convenience Functions

### New Helper Functions
```python
check_regex_pattern(pattern)          # Validate regex patterns
check_glob_pattern(pattern)           # Validate glob patterns
check_git_repo(path)                  # Verify git repository
check_text_file(path, encoding)       # Comprehensive text file checks
check_writable_file(path)             # Check write permissions
check_system_resources(disk_mb, memory_mb)  # System resource checks
check_python_env(min_version, required_modules)  # Python environment
check_tool_dependencies(commands)     # System command availability
```

## Usage Examples

### Basic File Validation
```python
from preflight_checks import check_input_file, check_text_file

# Simple file check with size limit
check_input_file("data.txt", max_size_mb=50)

# Comprehensive text file validation
check_text_file("script.py", encoding='utf-8')
```

### Pattern Validation
```python
from preflight_checks import PreflightChecker

# Validate regex before compiling
success, msg = PreflightChecker.check_regex_pattern(r"test\d+")
if not success:
    print(f"Invalid pattern: {msg}")
    sys.exit(1)
```

### Environment Checks
```python
from preflight_checks import check_python_env, check_tool_dependencies

# Ensure Python 3.7+ with required modules
check_python_env((3, 7), ['numpy', 'pandas', 'matplotlib'])

# Ensure required tools are installed
check_tool_dependencies(['git', 'rg', 'jq'])
```

### Security Validation
```python
from preflight_checks import PreflightChecker

# Prevent path traversal attacks
base_dir = Path.cwd()
user_path = Path(user_input).resolve()

success, msg = PreflightChecker.is_path_within_base(user_path, base_dir)
if not success:
    print(f"Security violation: {msg}")
    sys.exit(1)
```

### Batch Processing
```python
from preflight_checks import run_preflight_checks, PreflightChecker

# Run multiple checks with custom error handling
checks = [
    (PreflightChecker.check_file_readable, (input_file,)),
    (PreflightChecker.check_binary_file, (input_file,)),
    (PreflightChecker.check_encoding, (input_file, 'utf-8')),
    (PreflightChecker.check_file_size, (input_file, 100)),
]

# Don't exit on failure, handle errors manually
if not run_preflight_checks(checks, exit_on_fail=False):
    print("Some checks failed, proceeding with caution...")
```

## Testing

The module includes comprehensive unit tests covering all new functionality:

```bash
# Run tests
python test/test_preflight_checks.py -v

# Run self-test
python preflight_checks.py

# Run with demo mode
python preflight_checks.py --demo
```

## Best Practices

1. **Early Validation**: Run preflight checks at the beginning of your tool
2. **Fail Fast**: Exit immediately on critical validation failures
3. **Informative Messages**: Provide clear error messages to help users fix issues
4. **Graceful Degradation**: Some checks (like memory/disk) should warn but not fail
5. **Security First**: Always validate user inputs, especially file paths

## Migration Guide

Existing tools using the original preflight_checks.py will continue to work without modification. The enhancements are purely additive and maintain full backward compatibility.

To leverage new features:
1. Import new convenience functions as needed
2. Add relevant checks for your tool's requirements
3. Consider security checks for any user-provided paths
4. Add resource checks for memory/disk-intensive operations