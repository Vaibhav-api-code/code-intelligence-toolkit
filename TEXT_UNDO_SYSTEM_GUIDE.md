# Multi-Level Undo System for Text Operations

**Related Code Files:**
- `text_operation_history.py` - Core undo system with atomic operations and history tracking
- `text_undo.py` - CLI tool for managing undo operations
- `replace_text_v9.py` - Enhanced replacement tool with undo support
- `undo_system_demo.py` - Demonstration script showing system capabilities

---

## Overview

The Code Intelligence Toolkit now includes a **SafeGIT-style multi-level undo system** for all text editing operations. This system provides:

- 🔄 **Complete operation history** - Every text modification is tracked
- 💾 **Automatic backups** - Files are backed up before any change
- ↩️ **Multi-level undo** - Restore to any previous state
- 🔒 **Atomic operations** - Thread-safe with file locking
- 📊 **Rich analytics** - Statistics and operation tracking
- 🚀 **Zero configuration** - Works out of the box

## Architecture

### Core Components

1. **TextOperationHistory** (`text_operation_history.py`)
   - Manages operation tracking and backup storage
   - Provides atomic file locking for concurrent safety
   - Handles compression for large files
   - Generates recovery scripts automatically

2. **Operation Types**
   - `REPLACE_TEXT` - Standard text replacements
   - `REPLACE_AST` - AST-aware refactoring
   - `UNIFIED_REFACTOR` - Multi-engine refactoring
   - `MULTI_EDIT` - Batch edit operations
   - `WRITE_FILE` - File creation/overwrite
   - `DELETE_FILE` - File deletion

3. **Storage Structure**
   ```
   ~/.text_operation_history/
   ├── operations.jsonl      # Operation log (append-only)
   ├── backups/             # Compressed/uncompressed backups
   ├── metadata/            # Operation metadata
   └── recovery_scripts/    # Auto-generated recovery scripts
   ```

## Usage

### Basic Text Replacement with Undo

```bash
# Use replace_text_v9 for automatic undo tracking
python3 replace_text_v9.py "old text" "new text" file.txt

# Output includes undo ID:
# [Undo ID: 1753731617656_77627] Operation recorded. 
# Use 'text_undo.py --operation 1753731617656_77627' to undo.
```

### View Operation History

```bash
# Show recent operations
python3 text_undo.py history

# Show operations for specific file
python3 text_undo.py history --file script.py

# Show operations from last 2 hours
python3 text_undo.py history --since 2h

# Detailed view
python3 text_undo.py history --detailed
```

### Undo Operations

```bash
# Undo the last operation
python3 text_undo.py undo --last

# Undo specific operation
python3 text_undo.py undo --operation 1753731617656_77627

# Interactive undo (choose from list)
python3 text_undo.py undo --interactive

# Skip confirmation
python3 text_undo.py undo --last --yes
```

### System Management

```bash
# Show statistics
python3 text_undo.py stats

# Clean old operations (>30 days)
python3 text_undo.py clean

# Show operation details
python3 text_undo.py show 1753731617656_77627
```

## Integration with Existing Tools

### Direct Integration (Recommended)

For new tools or when updating existing ones:

```python
from text_operation_history import (
    TextOperationHistory, OperationType, get_history_instance
)

# Get the singleton instance
history = get_history_instance()

# Before making changes, record the operation
operation = history.record_operation(
    operation_type=OperationType.REPLACE_TEXT,
    file_path=Path("example.py"),
    tool_name="my_tool",
    command_args=sys.argv[1:],
    old_content=original_content,
    new_content=new_content,
    changes_count=5,
    description="Refactored variable names"
)

if operation:
    print(f"[Undo ID: {operation.operation_id}] Operation recorded.")
```

### Wrapper Approach

For existing tools without modification:

```python
# See replace_text_v9.py for example of wrapping v8
from existing_tool import main as original_main

def wrapped_main():
    # Track operations before/after
    # ... undo tracking code ...
    original_main()
    # ... record operations ...
```

## Features

### Automatic Compression

Files larger than 1KB are automatically compressed with gzip to save space:
- Transparent compression/decompression
- Typically 60-90% space savings for text files
- No user intervention required

### Recovery Scripts

Every operation generates a shell script for manual recovery:
```bash
~/.text_operation_history/recovery_scripts/recover_1753731617656_77627.sh
```

### Atomic Operations

All operations use file locking to ensure safety:
- Exclusive locks prevent concurrent modifications
- Timeout handling for stuck locks
- Cross-process safety

### Operation Dependencies

Track related operations:
- Chain multiple operations together
- Understand operation sequences
- Bulk undo capabilities (future)

## Configuration

The system uses sensible defaults but can be customized:

```python
history = TextOperationHistory()
history.max_history_size = 10000      # Operations to keep
history.max_backup_age_days = 30      # Backup retention
history.compression_threshold = 1024   # Bytes before compression
```

## Best Practices

1. **Regular Cleanup**: Run `text_undo.py clean` monthly to remove old backups
2. **Check History**: Use `text_undo.py history` before major operations
3. **Interactive Mode**: Use `--interactive` for user-friendly undo
4. **Integration**: Prefer direct integration over wrapper approach
5. **Description**: Always provide meaningful operation descriptions

## Troubleshooting

### "Operation not found"
- Check if operation exists: `text_undo.py history --limit 1000`
- Operations may have been cleaned up if >30 days old

### "Backup file not found"
- The backup may have been manually deleted
- Check `~/.text_operation_history/backups/` directory

### "Lock timeout"
- Another process may be using the history system
- Check for stuck processes: `ps aux | grep python`
- Remove stale lock: `rm ~/.text_operation_history/.lock`

## Performance Considerations

- **Minimal overhead**: ~5-10ms per operation
- **Efficient storage**: Compression reduces backup size
- **Scalable**: Handles thousands of operations efficiently
- **Memory safe**: Streaming operations prevent memory issues

## Future Enhancements

- [ ] Web UI for visual history browsing
- [ ] Integration with more tools (AST refactoring, etc.)
- [ ] Distributed undo across multiple machines
- [ ] Selective undo (undo specific changes within a file)
- [ ] Integration with git for hybrid version control

## Example Workflow

```bash
# 1. Make a series of changes
python3 replace_text_v9.py "TODO" "DONE" src/*.py
python3 replace_text_v9.py "oldAPI" "newAPI" lib/*.py

# 2. Check what was changed
python3 text_undo.py history --since 5m

# 3. Oops, the API change was wrong
python3 text_undo.py undo --interactive
# Select the API change operation

# 4. Verify restoration
python3 text_undo.py show <operation_id>

# 5. Clean up old operations monthly
python3 text_undo.py clean
```

## Security Notes

- Backups are stored in plain text (or gzip)
- No encryption is applied to backups
- File permissions are preserved
- Consider disk encryption for sensitive data

## Conclusion

The multi-level undo system brings enterprise-grade safety to text operations in the Code Intelligence Toolkit. With automatic tracking, atomic operations, and comprehensive recovery options, you can work with confidence knowing that any change can be undone.

Remember: **Every operation is reversible** - experiment freely!