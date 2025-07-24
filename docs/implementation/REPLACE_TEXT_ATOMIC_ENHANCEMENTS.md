<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Replace Text Tool - Atomic Write and File Locking Enhancements

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Replace Text Tool - Atomic Write and File Locking Enhancements

**Related Code Files:**
- `replace_text.py` - The enhanced text replacement tool with atomic operations and retry logic

---

## Summary of Enhancements

The `replace_text.py` tool has been enhanced with robust file handling capabilities to ensure safe atomic operations and handle concurrent file access scenarios.

## Key Features Added

### 1. Enhanced Atomic Write Operation (`_atomic_write`)

The atomic write function now includes:
- **Proper temp file handling** with file descriptors
- **fsync() calls** to ensure data is written to disk
- **Retry logic** for handling locked files
- **Cross-platform support** for both Unix and Windows
- **Configurable retry behavior** via command-line arguments

```python
def _atomic_write(path: Path, data: str, bak: bool = False, 
                  max_retries: int = 3, retry_delay: float = 1.0) -> None
```

### 2. File Lock Detection (`is_file_locked`)

A new function that detects if a file is currently locked:
- **Platform-specific implementations** (Unix vs Windows)
- **Multiple detection methods** as fallbacks
- **Process information** when available (using `lsof` on Unix)
- Returns both lock status and descriptive information

### 3. Command-Line Options for Retry Control

New options added:
- `--max-retries N` - Set maximum retry attempts (default: 3)
- `--retry-delay SECONDS` - Set delay between retries (default: 1.0)
- `--no-retry` - Disable retry logic entirely

Environment variable fallbacks:
- `FILE_WRITE_MAX_RETRIES` - Override default max retries
- `FILE_WRITE_RETRY_DELAY` - Override default retry delay

### 4. Enhanced Error Reporting

When file operations fail:
- **Detailed error messages** explaining the failure
- **Lock detection** with process information if available
- **Helpful suggestions** for resolving lock issues

## Usage Examples

### Basic usage with default retry behavior:
```bash
./run_any_python_tool.sh replace_text.py "old_text" "new_text" file.txt
```

### Custom retry configuration:
```bash
# More retries with shorter delay
./run_any_python_tool.sh replace_text.py "old" "new" file.txt --max-retries 10 --retry-delay 0.5

# Disable retry for scripts that need to fail fast
./run_any_python_tool.sh replace_text.py "old" "new" file.txt --no-retry
```

### Environment variable configuration:
```bash
# Set globally for a session
export FILE_WRITE_MAX_RETRIES=5
export FILE_WRITE_RETRY_DELAY=2.0
./run_any_python_tool.sh replace_text.py "old" "new" file.txt
```

## How It Works

1. **Atomic Write Process**:
   - Creates a temporary file in the same directory
   - Writes new content to temp file
   - Calls fsync() to ensure data is on disk
   - Creates backup if requested
   - Attempts atomic rename (os.replace)
   - Retries if file is locked

2. **Lock Detection**:
   - First tries platform-specific methods (fcntl on Unix)
   - Falls back to exclusive open attempts
   - Final fallback: try to rename file to itself
   - Provides descriptive error messages

3. **Retry Logic**:
   - Detects specific error codes (EACCES, EPERM, EBUSY, ETXTBSY)
   - Waits specified delay between attempts
   - Provides progress feedback (unless QUIET_MODE is set)
   - Cleans up temp files on failure

## Benefits

1. **Data Safety**: Atomic operations prevent partial writes or data corruption
2. **Concurrent Access**: Handles files being used by other processes gracefully
3. **User Control**: Configurable retry behavior for different use cases
4. **Cross-Platform**: Works on Unix/Linux, macOS, and Windows
5. **Transparency**: Clear error messages help diagnose issues

## Error Handling

The tool handles various error scenarios:
- **Permission denied**: Detected and reported with suggestions
- **File locked by another process**: Retries with configurable behavior
- **Disk full**: Proper cleanup of temp files
- **Network file systems**: Atomic operations work correctly
- **Read-only filesystems**: Clear error reporting

## Best Practices

1. **For interactive use**: Keep default retry settings (3 retries, 1 second delay)
2. **For scripts**: Consider using `--no-retry` for predictable behavior
3. **For busy files**: Increase retries and/or delay
4. **For CI/CD**: Set environment variables for consistent behavior

## Technical Notes

- Uses `os.replace()` for true atomic rename (not `os.rename()`)
- Temp files created with secure random names
- File descriptors properly managed to prevent leaks
- Compatible with network file systems that support atomic operations
- Thread-safe implementation

This enhancement ensures that the `replace_text.py` tool can safely handle real-world scenarios where files might be temporarily locked or in use by other processes, while maintaining data integrity through atomic operations.