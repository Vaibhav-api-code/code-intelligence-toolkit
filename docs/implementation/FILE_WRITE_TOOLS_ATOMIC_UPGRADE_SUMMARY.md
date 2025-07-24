<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

File Write Tools - Atomic Operations Upgrade Summary

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# File Write Tools - Atomic Operations Upgrade Summary

**Related Code Files:**
- `replace_text.py` - Enhanced text replacement tool
- `replace_text_ast.py` - Enhanced AST-aware text replacement
- `refactor_rename.py` - Enhanced file and symbol renaming
- `safe_move.py` - Enhanced safe file operations (most comprehensive)
- `organize_files.py` - Enhanced file organization with bulk operations
- `java_scope_refactor.py` - Enhanced Java-specific refactoring
- `ast_refactor.py` - Enhanced basic AST refactoring
- `ast_refactor_enhanced.py` - Enhanced advanced AST refactoring

---

## Overview

All file modification tools in the Java Intelligence Analysis Toolkit have been upgraded with enterprise-grade atomic operations, retry logic, and file locking detection. This ensures data integrity and handles concurrent file access scenarios gracefully.

## Enhanced Tools Summary

### 🎯 **Core Text Replacement Tools**

#### 1. **replace_text.py**
- **Primary Purpose**: General text replacement in files
- **Enhancements**: Full atomic write with retry, file lock detection, configurable retry behavior
- **New Options**: `--max-retries`, `--retry-delay`, `--no-retry`
- **Environment Variables**: `FILE_WRITE_MAX_RETRIES`, `FILE_WRITE_RETRY_DELAY`

#### 2. **replace_text_ast.py**
- **Primary Purpose**: AST-aware scope-sensitive text replacement
- **Enhancements**: Same as replace_text.py plus AST context preservation
- **New Options**: `--max-retries`, `--retry-delay`, `--no-retry`
- **Environment Variables**: `FILE_WRITE_MAX_RETRIES`, `FILE_WRITE_RETRY_DELAY`

### 🔄 **Refactoring and Renaming Tools**

#### 3. **refactor_rename.py**
- **Primary Purpose**: File and symbol renaming with code intelligence
- **Enhancements**: Atomic context manager, comprehensive retry logic, Windows/Unix compatibility
- **New Options**: `--max-retries`, `--retry-delay`
- **Environment Variables**: `REFACTOR_MAX_RETRIES`, `REFACTOR_RETRY_DELAY`
- **Special Features**: Custom exception classes, JSON output support

#### 4. **java_scope_refactor.py**
- **Primary Purpose**: Java-specific scope-aware refactoring
- **Enhancements**: Java-specific error handling, backup creation, AST integration
- **New Options**: `--max-retries`, `--retry-delay` (for rename and rename-project commands)
- **Environment Variables**: `JAVA_REFACTOR_MAX_RETRIES`, `JAVA_REFACTOR_RETRY_DELAY`

#### 5. **ast_refactor.py**
- **Primary Purpose**: Basic AST-based refactoring
- **Enhancements**: AST-aware atomic writes, backup creation
- **New Options**: `--max-retries`, `--retry-delay`
- **Environment Variables**: `AST_REFACTOR_MAX_RETRIES`, `AST_REFACTOR_RETRY_DELAY`

#### 6. **ast_refactor_enhanced.py**
- **Primary Purpose**: Advanced AST-based refactoring
- **Enhancements**: Enhanced AST processing with atomic safety
- **New Options**: `--max-retries`, `--retry-delay`
- **Environment Variables**: `AST_ENHANCED_MAX_RETRIES`, `AST_ENHANCED_RETRY_DELAY`

### 📁 **File Management Tools**

#### 7. **safe_move.py** (Most Comprehensive)
- **Primary Purpose**: Safe file moving, copying, and management
- **Enhancements**: Most comprehensive implementation with checksums, diagnostics, timeouts
- **New Options**: `--max-retries`, `--retry-delay`, `--timeout`, `--verify-checksum`, `--no-verify-checksum`
- **Environment Variables**: `SAFE_MOVE_MAX_RETRIES`, `SAFE_MOVE_RETRY_DELAY`, `SAFE_MOVE_TIMEOUT`, etc.
- **Special Features**: MD5 checksum verification, diagnostic mode, operation history

#### 8. **organize_files.py**
- **Primary Purpose**: Bulk file organization and management
- **Enhancements**: Bulk operation safety, manifest/rollback, checksum verification
- **New Options**: `--max-retries`, `--retry-delay`, `--operation-timeout`, `--verify-checksum`, `--wait-for-unlock`
- **Environment Variables**: `ORGANIZE_FILES_MAX_RETRIES`, `ORGANIZE_FILES_VERIFY_CHECKSUM`, etc.
- **Special Features**: Incremental manifest updates, bulk operation statistics

## Common Enhanced Features

### 🔒 **Atomic Write Operations**
All tools now use a consistent atomic write pattern:
1. **Temporary File Creation**: Create temp file in same directory
2. **Content Writing**: Write new content to temp file
3. **Data Sync**: Force data to disk with `fsync()`
4. **Backup Creation**: Create backup if requested
5. **Atomic Replace**: Use `os.replace()` for atomic operation

### 🔄 **Retry Logic**
Configurable retry behavior for handling file conflicts:
- **Default**: 3 retries with 1-second delays
- **Exponential Backoff**: Some tools use progressive delays
- **Lock Detection**: Specific handling for file locking errors
- **User Feedback**: Progress reporting during retries

### 🛡️ **File Lock Detection**
Cross-platform file lock detection:
- **Unix/macOS**: Uses `fcntl.flock()` for exclusive locks
- **Windows**: Handles sharing violations and lock errors
- **Process Info**: Shows which process has file locked (when available)
- **Graceful Handling**: Waits and retries instead of failing immediately

### ⚙️ **Configuration Options**
Consistent configuration across all tools:

#### Command-Line Options:
- `--max-retries N`: Maximum retry attempts
- `--retry-delay SECONDS`: Delay between retries
- `--no-retry`: Disable retry logic (some tools)
- Tool-specific options (timeout, checksum, etc.)

#### Environment Variables:
Each tool has unique environment variable names:
- `{TOOL}_MAX_RETRIES`: Override max retries
- `{TOOL}_RETRY_DELAY`: Override retry delay
- Tool-specific variables for additional features

### 📊 **Enhanced Error Reporting**
Detailed error information for troubleshooting:
- **Specific Error Types**: Permission, locking, disk space, etc.
- **Process Information**: Which process has file locked
- **Recovery Suggestions**: Helpful guidance for users
- **Attempt Tracking**: Shows retry attempt counts
- **Context Information**: File paths, operation details

## Usage Examples

### Basic Usage (Backward Compatible)
```bash
# All existing commands work unchanged
./run_any_python_tool.sh replace_text.py "old" "new" file.txt
./run_any_python_tool.sh safe_move.py move source.txt dest.txt
./run_any_python_tool.sh organize_files.py ~/Downloads --by-ext
```

### Enhanced Safety Features
```bash
# Custom retry configuration
./run_any_python_tool.sh replace_text.py "old" "new" file.txt --max-retries 5 --retry-delay 2.0

# Disable retry for scripts that need to fail fast
./run_any_python_tool.sh refactor_rename.py --replace oldVar newVar --in "*.py" --no-retry

# Enhanced file operations with checksum verification
./run_any_python_tool.sh safe_move.py copy important.dat backup/ --verify-checksum --timeout 120

# Bulk operations with safety features
./run_any_python_tool.sh organize_files.py large_directory --by-type --verify-checksum --max-retries 10
```

### Environment Variable Configuration
```bash
# Set globally for a session
export FILE_WRITE_MAX_RETRIES=5
export FILE_WRITE_RETRY_DELAY=2.0
export SAFE_MOVE_VERIFY_CHECKSUM=true
export ORGANIZE_FILES_OPERATION_TIMEOUT=60

# Tools will use these settings automatically
./run_any_python_tool.sh replace_text.py "old" "new" *.txt
./run_any_python_tool.sh organize_files.py ~/Downloads --by-date
```

## Benefits

### 🛡️ **Data Integrity**
- **Atomic Operations**: Prevent partial writes and file corruption
- **Backup Creation**: Preserve original files before modifications
- **Checksum Verification**: Ensure data integrity for critical operations
- **Rollback Capability**: Undo operations when things go wrong

### 🚀 **Reliability**
- **Concurrent Access**: Handle files being used by other processes
- **Network Filesystems**: Work correctly with NFS, SMB, etc.
- **Large Files**: Handle large files without hanging or failing
- **Resource Management**: Proper cleanup of temporary files

### 🔧 **Operational Excellence**
- **Monitoring**: Detailed logging and error reporting
- **Configuration**: Flexible configuration via CLI and environment
- **Automation**: Suitable for CI/CD pipelines and automated workflows
- **Debugging**: Comprehensive diagnostic information

### 🌐 **Cross-Platform Compatibility**
- **Windows**: Handles file locking and sharing violations
- **Unix/Linux**: Uses proper file locking mechanisms
- **macOS**: Compatible with macOS file system features
- **Network Storage**: Works with mounted network drives

## Best Practices

### For Interactive Use
- Keep default settings (3 retries, 1-second delay)
- Use verbose mode to see retry progress
- Enable checksum verification for important files

### For Automation/Scripts
- Set appropriate timeouts for your environment
- Use environment variables for consistent configuration
- Consider `--no-retry` for predictable behavior in CI/CD
- Enable logging for troubleshooting

### For Production Environments
- Increase retry counts for busy systems
- Enable checksum verification for critical data
- Set appropriate timeouts for network storage
- Use manifest/rollback features for bulk operations

## Migration Notes

### Backward Compatibility
- **100% Compatible**: All existing commands work unchanged
- **Default Behavior**: Conservative defaults maintain existing behavior
- **Opt-in Features**: New safety features are optional
- **Performance**: Minimal performance impact with default settings

### Recommended Upgrades
1. **Enable checksum verification** for critical file operations
2. **Increase retries** for systems with high file contention
3. **Use environment variables** for consistent configuration
4. **Enable verbose mode** to see retry progress

This comprehensive upgrade ensures that all file modification tools in the toolkit provide enterprise-grade reliability while maintaining full backward compatibility. Users can now handle concurrent file access scenarios gracefully and prevent data corruption through atomic operations.