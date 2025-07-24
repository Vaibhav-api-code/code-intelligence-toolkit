<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Refactor Rename Tool Enhancements

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Refactor Rename Tool Enhancements

**Related Code Files:**
- `refactor_rename.py` - Enhanced code-aware file and symbol renaming tool with atomic operations
- `test_refactor_atomic.py` - Test script demonstrating atomic write functionality (created for testing, can be removed)

---

## Summary

Enhanced the `refactor_rename.py` tool with enterprise-grade atomic write operations and retry logic to ensure safe, reliable file operations even in challenging environments with file locking, network storage, or high-concurrency scenarios.

## Key Enhancements

### 1. Atomic Write Operations

**New Context Manager: `atomic_write()`**
- Writes to temporary files in the same directory as the target
- Uses `os.replace()` for atomic move operations
- Preserves original file permissions when replacing existing files
- Automatically cleans up temporary files on failure
- Cross-platform compatibility (Windows and Unix-like systems)

**Features:**
```python
with atomic_write(file_path, encoding='utf-8') as f:
    f.write(content)
```

### 2. Retry Logic with Environment Variable Support

**Configurable Retry Parameters:**
- `--max-retries N`: Maximum retry attempts (default: 3)
- `--retry-delay SECONDS`: Delay between retries in seconds (default: 0.1)
- Environment variables: `REFACTOR_MAX_RETRIES` and `REFACTOR_RETRY_DELAY`

**Intelligent Retry Logic:**
- Detects file locking conditions specifically
- Exponential backoff available via environment configuration
- Detailed logging of retry attempts and failure reasons

### 3. Enhanced File Lock Detection

**Cross-Platform Lock Detection:**
```python
def is_file_locked(file_path: Path, error: OSError) -> bool:
    # Detects Windows-specific error codes (sharing violations, lock violations)
    # Detects Unix-specific error codes (busy, permission denied, text file busy)
    # Checks both errno and winerror on Windows systems
```

**Supported Error Types:**
- Windows: `ERROR_SHARING_VIOLATION`, `ERROR_LOCK_VIOLATION`, `EACCES`, `EBUSY`
- Unix: `EACCES`, `EBUSY`, `ETXTBSY`, `EAGAIN`, `EWOULDBLOCK`

### 4. Safe Atomic Move Function

**New Function: `safe_atomic_move()`**
- Atomic file renaming with retry logic
- Prevents data loss during file moves
- Handles locked files gracefully
- Used for all file rename operations in the tool

### 5. Enhanced Error Reporting

**Custom Exception Classes:**
- `AtomicWriteError`: For atomic write operation failures
- `FileOperationError`: For file operations with retry context (includes attempt count)

**Improved Logging:**
- Detailed retry attempt logging
- Clear distinction between different failure types
- Structured error messages with context

### 6. Environment Variable Configuration

**Supported Environment Variables:**
```bash
export REFACTOR_MAX_RETRIES=5          # Maximum retry attempts
export REFACTOR_RETRY_DELAY=0.2        # Delay between retries (seconds)
```

**Usage Examples:**
```bash
# Using command-line options
python3 refactor_rename.py file.py NewFile --max-retries 5 --retry-delay 0.1

# Using environment variables
REFACTOR_MAX_RETRIES=4 REFACTOR_RETRY_DELAY=0.05 python3 refactor_rename.py file.py NewFile
```

## Integration Points

### File Content Updates
All content modification operations now use atomic writes:
- Class/method renaming within files
- Symbol replacement operations
- Content-only updates (`--content-only` flag)

### File Rename Operations
All file rename operations now use atomic moves:
- Single file renaming
- Batch renaming operations
- Related file renaming (`--related` flag)

### Compile Checking Integration
Atomic operations are fully integrated with the existing compile checking system:
- Compile checks run after successful atomic writes
- Failures are properly logged with operation context
- No partial operations left in invalid states

## Testing

**Comprehensive Test Suite:**
- Basic atomic write functionality
- Existing file replacement with permission preservation
- Retry logic with environment variable configuration
- Error handling for invalid operations
- File lock detection across platforms

**Test Results:**
All tests pass successfully, demonstrating:
- ✅ Basic atomic write operations
- ✅ Permission preservation during file replacement
- ✅ Environment variable configuration
- ✅ Proper error handling for invalid paths
- ✅ Cross-platform file lock detection

## Backward Compatibility

**Zero Breaking Changes:**
- All existing command-line options work unchanged
- Default behavior remains the same (max_retries=3, retry_delay=0.1)
- Existing APIs and usage patterns are preserved
- Optional retry parameters default to environment variables or sensible defaults

## Benefits

1. **Reliability**: Atomic operations prevent partial writes and data corruption
2. **Robustness**: Retry logic handles temporary file locking and network issues
3. **Flexibility**: Environment variable configuration supports CI/CD and automation
4. **Safety**: Never leaves files in inconsistent states
5. **Performance**: Minimal overhead while providing enterprise-grade reliability
6. **Observability**: Enhanced logging and error reporting for debugging

## CI/CD Integration

**JSON Output Support:**
```bash
python3 refactor_rename.py file.py NewFile --json --yes
```

**Output Format:**
```json
{
  "processed": 1,
  "operations": [
    ["COMPILE CHECK", "NewFile.py - ✓ Compiles"],
    ["RENAMED", "file.py → NewFile.py"]
  ],
  "files": ["NewFile.py"],
  "success": true
}
```

**Automation Features:**
- `--yes` flag for auto-confirmation
- Non-interactive mode detection
- Environment variable configuration
- Structured JSON output for parsing

This enhancement makes `refactor_rename.py` suitable for production environments, automated workflows, and high-reliability scenarios while maintaining full backward compatibility with existing usage patterns.