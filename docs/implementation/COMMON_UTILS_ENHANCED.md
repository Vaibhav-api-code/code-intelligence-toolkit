<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Enhanced common_utils.py Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-09
Updated: 2025-07-09
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Enhanced common_utils.py Documentation

**Related Code Files:**
- `code-intelligence-toolkit/common_utils.py` - The enhanced utilities module
- `code-intelligence-toolkit/error_logger.py` - Error logging integration
- `code-intelligence-toolkit/*.py` - All Python tools that can use these utilities

---

## Overview

The enhanced `common_utils.py` provides comprehensive shared functionality for security, subprocess handling, file operations, and more. This module serves as the foundation for all Python tools in the code-intelligence-toolkit, ensuring consistent behavior and enterprise-grade safety across all operations.

## Key Features

### 1. Security Utilities

**Path Validation and Sanitization:**
- `validate_path()` - Prevents path traversal attacks with null byte detection
- `sanitize_command_arg()` - Removes dangerous characters from command arguments
- `safe_path_join()` - Safely joins paths without allowing directory traversal
- `is_safe_filename()` - Validates filenames against safe character set

```python
# Example usage
from common_utils import validate_path, safe_path_join

# Validate a path
safe_path = validate_path("./user_input.txt", base_dir="/allowed/dir")

# Safely join paths
output_path = safe_path_join("output", "results", "report.txt")
```

### 2. Subprocess Handling

**Safe Process Execution:**
- `run_subprocess()` - Execute commands with timeout, memory limits, and sanitization
- `SubprocessTimeout` - Custom exception for timeout handling
- `run_with_timeout()` - Execute Python functions with timeout using threading

```python
from common_utils import run_subprocess, SubprocessTimeout

try:
    result = run_subprocess(
        ['grep', '-r', 'pattern', '.'],
        timeout=30,
        max_memory_mb=256
    )
    print(result.stdout)
except SubprocessTimeout:
    print("Command timed out")
```

### 3. File Operations

**Atomic and Safe File Handling:**
- `atomic_write()` - Context manager for atomic file writes
- `safe_file_backup()` - Create timestamped backups
- `calculate_file_hash()` - Compute file checksums
- `safe_file_operation()` - Perform operations with rollback capability

```python
from common_utils import atomic_write, safe_file_backup

# Atomic write ensures file is either fully written or not at all
with atomic_write('config.json') as f:
    json.dump(config_data, f)

# Create backup before modifying
backup_path = safe_file_backup('important.txt')
```

### 4. Error Handling

**Context-Aware Error Management:**
- `ErrorContext` - Context manager for capturing errors with metadata
- Integration with `error_logger.py` for centralized error tracking

```python
from common_utils import ErrorContext

with ErrorContext("database_operation", {"table": "users", "action": "update"}):
    # If this fails, error is logged with context
    perform_database_update()
```

### 5. Manifest and Rollback Support

**Operation Tracking for Reversibility:**
- `OperationManifest` - Track file operations for potential rollback
- Supports undo functionality for move, copy, and delete operations

```python
from common_utils import OperationManifest, safe_file_operation

manifest = OperationManifest()

# Perform operation with tracking
result = safe_file_operation('move', 'old.txt', 'new.txt')
op_id = manifest.add_operation(result)

# Later, rollback if needed
manifest.rollback_operation(op_id)
```

### 6. Enhanced File Reading and Stats

**Existing Utilities (Preserved):**
- Language detection and file classification
- Safe file content reading with encoding fallback
- Binary file detection
- File statistics and formatting

### 7. Resource Management

**Platform-Aware Resource Limits:**
- `resource_limit()` - Context manager for CPU and memory limits
- Automatically handles platform differences (Linux vs macOS)

```python
from common_utils import resource_limit

# Limit CPU time and memory usage
with resource_limit(cpu_seconds=60, memory_mb=512):
    process_large_dataset()
```

### 8. Common CLI Arguments

**Standardized Argument Handling:**
- Pre-defined common arguments for consistency
- `add_common_args()` - Helper to add standard arguments to parsers

```python
import argparse
from common_utils import add_common_args

parser = argparse.ArgumentParser()
add_common_args(parser, 'scope', 'timeout', 'verbose', 'dry_run')
```

## Platform Compatibility

The module is designed to work across different platforms:
- **Linux**: Full support for all features including memory limits
- **macOS**: Most features supported, memory limits gracefully degrade
- **Windows**: Core functionality works, Unix-specific features disabled

## Integration Guidelines

1. **Import what you need:**
   ```python
   from common_utils import (
       validate_path, run_subprocess, atomic_write,
       ErrorContext, add_common_args
   )
   ```

2. **Use security functions for all user input:**
   ```python
   user_path = validate_path(user_input, base_dir=allowed_dir)
   ```

3. **Prefer atomic operations for file modifications:**
   ```python
   with atomic_write(output_file) as f:
       f.write(processed_data)
   ```

4. **Always use timeouts for external processes:**
   ```python
   result = run_subprocess(cmd, timeout=30)
   ```

## Migration Guide

For existing tools using the original `common_utils.py`:

1. **No breaking changes** - All original functions preserved
2. **New imports available** - Add security and subprocess utilities as needed
3. **Consider upgrading file operations** - Use atomic_write for critical files
4. **Add error context** - Wrap operations with ErrorContext for better debugging

## Best Practices

1. **Always validate paths** from user input or external sources
2. **Use atomic operations** for configuration files and critical data
3. **Set reasonable timeouts** for all subprocess and long-running operations
4. **Create backups** before destructive operations
5. **Track operations** with OperationManifest when reversibility is needed
6. **Handle platform differences** gracefully (test on target platforms)

## Error Handling

The module integrates with the error logging system:
- Errors are automatically logged to `~/.pytoolserrors/`
- Context information is preserved for debugging
- Use `analyze_errors.py` to review logged errors

## Performance Considerations

1. **Resource limits** may impact performance on Linux
2. **Atomic writes** use temporary files (ensure adequate disk space)
3. **File hashing** reads entire file (consider for large files)
4. **Subprocess sanitization** has minimal overhead

## Security Notes

- Path validation prevents directory traversal attacks
- Command sanitization removes shell metacharacters
- Atomic operations prevent partial file corruption
- Resource limits prevent runaway processes (Linux)

This enhanced module provides a solid foundation for building secure, reliable Python tools with consistent behavior and enterprise-grade safety features.