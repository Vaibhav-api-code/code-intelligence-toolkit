<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Safe File Manager - Comprehensive Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Safe File Manager - Comprehensive Guide

**Related Code Files:**
- `code-intelligence-toolkit/safe_file_manager.py` - Main implementation file
- `code-intelligence-toolkit/safe_move.py` - Original safe move tool
- `code-intelligence-toolkit/organize_files.py` - File organization features
- `code-intelligence-toolkit/refactor_rename.py` - AST-aware renaming features

---

## Overview

Safe File Manager is an enterprise-grade replacement for dangerous shell commands like `rm`, `mv`, `cp`, and `ls`. It combines the best features from multiple tools to provide bulletproof file operations with comprehensive safety checks, atomic operations, and full recovery capabilities.

## Key Features

### 🛡️ Enterprise-Grade Safety
- **Pre-operation analysis**: Checks permissions, disk space, conflicts, and git status
- **Atomic operations**: All operations use temporary files with atomic replace
- **Checksum verification**: SHA-256 checksums ensure data integrity
- **Automatic backups**: Files are backed up to trash before overwriting
- **Comprehensive undo**: Full operation history with recovery capabilities
- **Risk-based confirmations**: Graduated safety levels (safe → low → medium → high → critical)

### 🚀 Advanced Operations
- **Move & Copy**: Atomic operations with retry logic and checksum verification
- **Trash System**: Safe deletion with metadata tracking and restore capabilities
- **Organize**: Intelligent file organization by extension, date, size, MIME type, or custom rules
- **Sync**: Directory synchronization with exclusion patterns (like rsync but safer)
- **Batch Operations**: Concurrent execution with manifest tracking
- **Git Integration**: Awareness of version control status

### 🤖 Automation Support
- **Non-interactive mode**: Full support for AI agents and CI/CD pipelines
- **Environment variables**: Comprehensive configuration via environment
- **JSON output**: Structured output for scripting
- **Manifest system**: Track bulk operations with incremental updates

## Installation

```bash
# Make executable
chmod +x safe_file_manager.py

# Create alias (recommended)
alias sfm='python3 /path/to/safe_file_manager.py'

# Add to PATH
ln -s /path/to/safe_file_manager.py /usr/local/bin/sfm
```

## Command Reference

### Global Options

```bash
sfm [global-options] <command> [command-options]

Global Options:
  -v, --verbose         Verbose output
  -q, --quiet          Quiet mode (errors only)
  --dry-run            Preview operations without executing
  -y, --yes            Auto-confirm medium-risk operations
  --force              Auto-confirm high-risk operations
  --non-interactive    Non-interactive mode for automation
  --no-checksum        Disable checksum verification
  --no-preserve        Don't preserve file attributes
```

### Core Commands

#### Move (mv)
```bash
# Move single file
sfm move file.txt destination/

# Move multiple files
sfm move *.txt documents/

# Move with verification
sfm move --verbose important.dat backup/

# Dry run
sfm --dry-run move project/ archive/
```

#### Copy (cp)
```bash
# Copy file
sfm copy original.txt backup.txt

# Copy directory
sfm copy -r source/ destination/

# Copy with checksum verification
sfm copy --verify-checksum data.db backup/
```

#### Trash (rm)
```bash
# Move to trash (safe delete)
sfm trash unwanted.txt

# Trash multiple files
sfm trash *.tmp *.log

# Trash directory
sfm trash old_project/
```

#### Delete (permanent)
```bash
# Permanent delete (requires confirmation)
sfm delete --force temporary.txt

# Secure wipe (overwrite 3 times)
sfm delete --secure sensitive_data.txt
```

#### List (ls)
```bash
# List current directory
sfm list

# Long format with git status
sfm list -la

# Sort by size
sfm list -l --sort size downloads/

# Show hidden files
sfm list -a ~/.config/
```

#### Organize
```bash
# Organize by extension
sfm organize ~/Downloads --by extension

# Organize by date
sfm organize photos/ --by date

# Organize by size
sfm organize videos/ --by size

# Custom rules from YAML
sfm organize documents/ --by custom --rules organize_rules.yaml
```

Example rules file (organize_rules.yaml):
```yaml
"*.pdf": PDFs
"*.doc*": Documents/Word
"*.xls*": Documents/Excel
"*invoice*": Finance/Invoices
"*receipt*": Finance/Receipts
```

#### Sync
```bash
# Basic sync
sfm sync source/ backup/

# Sync with deletion of extra files
sfm sync --delete source/ mirror/

# Sync with exclusions
sfm sync source/ backup/ --exclude "*.tmp" "*.cache" "node_modules"
```

#### Restore
```bash
# Interactive restore
sfm restore

# Restore by pattern
sfm restore "important"

# List trash contents
sfm list ~/.safe_file_manager/trash/
```

#### History
```bash
# Show recent operations
sfm history

# Show last 50 operations
sfm history --count 50

# Filter by operation type
sfm history --operation move

# Filter by path
sfm history --path /home/user/documents/

# Operations since date
sfm history --since 2024-01-01
```

#### Info
```bash
# Get file information
sfm info file.txt

# Multiple files
sfm info *.py

# Include checksums
sfm info --verbose important.dat
```

#### Create (NEW)
```bash
# Create file with content
sfm create file.txt --content "Hello, World!"
sfm create file.txt -c "Single line content"

# Create from stdin
echo "Content from command" | sfm create output.txt --from-stdin
cat template.txt | sfm create newfile.txt --from-stdin

# Multi-line content from stdin
cat << EOF | sfm create config.yml --from-stdin
server:
  host: localhost
  port: 8080
EOF

# Create with specific encoding
sfm create unicode.txt --content "Unicode: 你好" --encoding utf-8

# Force overwrite existing file
sfm --force create existing.txt --content "New content"

# Dry run to preview
sfm --dry-run create test.txt --content "Test content"
```

#### Touch
```bash
# Create empty file or update timestamp
sfm touch newfile.txt

# Update multiple files
sfm touch file1.txt file2.txt file3.txt

# Update timestamp only (don't create)
sfm touch -c existing.txt
```

#### Mkdir
```bash
# Create directory
sfm mkdir newdir

# Create with parents
sfm mkdir -p path/to/deep/directory

# Create with specific permissions
sfm mkdir -m 755 scripts/
```

## Configuration

### Environment Variables

```bash
# Operation settings
export SAFE_FILE_MAX_RETRIES=5              # Max retry attempts (default: 3)
export SAFE_FILE_RETRY_DELAY=1.0            # Initial retry delay in seconds (default: 0.5)
export SAFE_FILE_OPERATION_TIMEOUT=60       # Operation timeout in seconds (default: 30)
export SAFE_FILE_VERIFY_CHECKSUM=true       # Enable checksum verification (default: true)

# Performance settings
export SAFE_FILE_CONCURRENT_OPS=8           # Max concurrent operations (default: 4)
export SAFE_FILE_CHUNK_SIZE=8192            # File read chunk size (default: 4096)

# Safety settings
export SAFE_FILE_AUTO_BACKUP=true           # Auto-backup before overwrite (default: true)
export SAFE_FILE_GIT_AWARE=true             # Git status checking (default: true)

# Non-interactive mode
export SAFE_FILE_NONINTERACTIVE=1           # Enable non-interactive mode
export SAFE_FILE_ASSUME_YES=1               # Auto-confirm medium-risk operations
export SAFE_FILE_FORCE=1                    # Auto-confirm high-risk operations

# Paths
export SAFE_FILE_TRASH=~/.trash             # Custom trash directory
export SAFE_FILE_HISTORY=~/.sfm_history     # Custom history location

# Logging
export SAFE_FILE_LOG_LEVEL=DEBUG            # Log level (DEBUG, INFO, WARNING, ERROR)
```

### Configuration File (.sfmrc)

Create `~/.sfmrc` for persistent configuration:
```ini
[defaults]
verify_checksum = true
auto_backup = true
concurrent_operations = 4
git_aware = true

[organize]
default_method = extension
archive_after_days = 30

[sync]
verify_after_sync = true
preserve_permissions = true
```

## Safety Levels and Confirmations

### Risk Levels

1. **SAFE**: No confirmation needed
   - List operations
   - Info queries
   - Dry-run operations

2. **LOW**: Simple Y/n confirmation
   - Copy operations
   - Move within same filesystem

3. **MEDIUM**: Requires --yes or explicit confirmation
   - Move across filesystems
   - Overwriting existing files
   - Modifying git-tracked files

4. **HIGH**: Requires --force or typed confirmation
   - Permanent deletion
   - Recursive directory operations
   - Operations on special files (.git, .env, etc.)

5. **CRITICAL**: Multiple confirmations required
   - Secure wipe operations
   - Bulk permanent deletions
   - System directory modifications

### Non-Interactive Mode

For automation and AI agents:

```bash
# Safe operations work normally
sfm --non-interactive list

# Medium-risk operations require --yes
sfm --non-interactive --yes move file.txt backup/

# High-risk operations require --force
sfm --non-interactive --force delete temp/

# Or use environment variables
export SAFE_FILE_NONINTERACTIVE=1
export SAFE_FILE_ASSUME_YES=1
sfm move *.txt archive/
```

## Advanced Features

### Manifest System

For bulk operations, a manifest is automatically created:

```bash
# Organize creates a manifest
sfm organize ~/Downloads --by extension

# Manifest location shown in output
# Contains all operation details for recovery
```

### Atomic Operations

All write operations use atomic patterns:
1. Write to temporary file
2. Verify checksum (if enabled)
3. Atomic rename to final destination
4. Clean up on failure

### Concurrent Operations

Multiple files are processed concurrently:
```bash
# Uses thread pool for parallel execution
sfm copy *.jpg photos/  # Processes multiple files simultaneously
```

### Git Integration

Automatically checks git status:
- Warns about modifying tracked files
- Shows git status in directory listings
- Preserves git metadata

### Recovery Features

1. **Trash System**: All deletions go to trash first
2. **Operation History**: Complete log of all operations
3. **Undo Capabilities**: Restore from trash or reverse operations
4. **Manifest Recovery**: Bulk operation recovery

## Use Cases

### Safe File Management for AI Agents

```python
# AI agents can use non-interactive mode
import subprocess

# Safe move with automatic confirmation
result = subprocess.run([
    'sfm', '--non-interactive', '--yes',
    'move', 'output.txt', 'results/'
], capture_output=True)
```

### CI/CD Pipeline Integration

```yaml
# GitHub Actions example
- name: Organize build artifacts
  env:
    SAFE_FILE_NONINTERACTIVE: 1
    SAFE_FILE_ASSUME_YES: 1
  run: |
    sfm organize dist/ --by extension
    sfm sync dist/ s3://bucket/releases/
```

### Bulk File Processing

```bash
# Organize downloads folder
sfm organize ~/Downloads --by date

# Sync with verification
sfm sync --verify-checksum source/ backup/

# Clean up old files
sfm trash $(sfm list --format json | jq -r '.files[] | select(.mtime < "2023-01-01") | .path')
```

## Best Practices

1. **Always use dry-run first** for complex operations
2. **Enable checksums** for important data transfers
3. **Regular history cleanup** to maintain performance
4. **Use manifests** for bulk operations
5. **Configure environment** for your workflow
6. **Leverage git integration** for code repositories

## Troubleshooting

### Common Issues

**Permission Denied**
- Check file permissions with `sfm info`
- Run with proper user permissions
- Use `--no-preserve` if attribute preservation fails

**Checksum Mismatch**
- Indicates data corruption during transfer
- Enable verbose mode to see details
- Check disk health and network stability

**Operation Timeout**
- Increase timeout: `export SAFE_FILE_OPERATION_TIMEOUT=120`
- Check for file locks
- Verify disk I/O performance

**Lock Detection Failed**
- Platform-specific issue
- Disable with retry: `--max-retries 0`
- Check antivirus/backup software

### Debug Mode

```bash
# Enable debug logging
export SAFE_FILE_LOG_LEVEL=DEBUG
sfm --verbose move large_file.iso backup/

# Check operation details
sfm history --verbose --count 1
```

## Comparison with Traditional Commands

| Traditional | Safe File Manager | Key Differences |
|------------|------------------|-----------------|
| `rm file` | `sfm trash file` | Recoverable deletion |
| `rm -rf dir` | `sfm trash dir` | Safe with confirmations |
| `mv src dst` | `sfm move src dst` | Atomic with verification |
| `cp -r src dst` | `sfm copy src dst` | Checksum verification |
| `ls -la` | `sfm list -la` | Git status integration |
| `rsync -av src dst` | `sfm sync src dst` | Safer with manifests |

## Integration with Existing Tools

Safe File Manager is designed to work alongside existing tools:

```bash
# Use with find
find . -name "*.tmp" -exec sfm trash {} \;

# Use with xargs
ls *.backup | xargs sfm move -t archive/

# Use in scripts
for file in *.log; do
    sfm move "$file" "logs/$(date +%Y%m)/"
done
```

## Future Enhancements

Planned features:
- Cloud storage support (S3, GCS, Azure)
- Network file system optimization
- Encrypted trash with compression
- Distributed operation support
- Plugin system for custom operations
- GUI interface for desktop users

## Contributing

This tool is part of the code-intelligence-toolkit. Contributions should:
- Maintain backward compatibility
- Include comprehensive tests
- Follow existing safety patterns
- Document new features
- Consider AI/automation use cases

## License

Same as parent project - see repository LICENSE file.