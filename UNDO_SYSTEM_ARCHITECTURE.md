# Multi-Level Undo System Architecture

**Related Code Files:**
- `text_operation_history.py` - Core undo tracking system
- `text_undo.py` - CLI interface for undo operations
- `replace_text_v9.py` - Text replacement with undo
- `replace_text_ast_v3.py` - AST refactoring with undo
- `unified_refactor_v2.py` - Universal refactoring with undo
- `refactor_rename_v2.py` - Batch renaming with undo
- `safe_file_manager_undo_wrapper.py` - File operations wrapper with undo

---

## Overview

The Code Intelligence Toolkit multi-level undo system provides SafeGIT-style protection for all text editing operations. Every modification is tracked, backed up, and reversible through a unified interface.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User/AI Agent                           │
│                    (Executes editing tools)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Editing Tools Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│  │replace_text │ │replace_text │ │unified      │ │refactor  │ │
│  │_v9.py       │ │_ast_v3.py   │ │_refactor_v2 │ │_rename_v2│ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬────┘ │
│         │                │                │              │      │
│         └────────────────┴────────────────┴──────────────┘      │
│                                  │                              │
│                          Undo Integration                       │
│                    (Tracks all operations)                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TextOperationHistory (Core)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Singleton instance per process                         │   │
│  │ • Thread-safe with file locking                         │   │
│  │ • Atomic operation recording                            │   │
│  │ • Automatic backup creation                             │   │
│  │ • Compression for files >1KB                            │   │
│  │ • Recovery script generation                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ operations   │ │   backups/   │ │  recovery    │           │
│  │ .jsonl       │ │  (gzipped)   │ │  _scripts/   │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│              ~/.text_operation_history/                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    text_undo.py (CLI)                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Commands:                                                │   │
│  │ • history - View operation history                      │   │
│  │ • undo - Restore previous state                         │   │
│  │ • show - Display operation details                      │   │
│  │ • stats - System statistics                             │   │
│  │ • clean - Remove old operations                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. TextOperationHistory Class

The heart of the undo system, providing:

```python
class TextOperationHistory:
    """Manages undo history for text operations with atomic guarantees"""
    
    def record_operation(
        self,
        operation_type: OperationType,
        file_path: Path,
        tool_name: str,
        command_args: List[str],
        old_content: Optional[str] = None,
        new_content: Optional[str] = None,
        changes_count: int = 0,
        description: str = ""
    ) -> Optional[TextOperation]
```

**Key Features:**
- Singleton pattern ensures single history instance
- Thread-safe with exclusive file locking
- Atomic writes to prevent corruption
- Automatic compression for storage efficiency

### 2. Operation Types

```python
class OperationType(Enum):
    REPLACE_TEXT = "replace_text"
    REPLACE_AST = "replace_ast"
    UNIFIED_REFACTOR = "unified_refactor"
    MULTI_EDIT = "multi_edit"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
```

Each operation type has specific handling and recovery strategies.

### 3. Storage Format

Operations are stored in JSONL format for streaming processing:

```json
{
  "operation_id": "1753732740927_91513",
  "timestamp": 1753732740.927,
  "operation_type": "replace_text",
  "file_path": "/path/to/file.py",
  "tool_name": "replace_text_v9",
  "command_args": ["old", "new", "file.py"],
  "changes_count": 3,
  "description": "Replace 'old' with 'new'",
  "backup_path": "backups/1753732740927_91513_file.py.gz",
  "metadata": {
    "original_size": 1024,
    "new_size": 1027,
    "compressed": true
  }
}
```

## Integration Pattern

### For New Tools

```python
# Import undo system
from text_operation_history import (
    TextOperationHistory, OperationType, get_history_instance
)

# In your write operation
def write_file(path, content):
    # Get original content if exists
    old_content = path.read_text() if path.exists() else None
    
    # Record operation BEFORE making changes
    history = get_history_instance()
    operation = history.record_operation(
        operation_type=OperationType.WRITE_FILE,
        file_path=path,
        tool_name="my_tool",
        command_args=sys.argv[1:],
        old_content=old_content,
        new_content=content,
        description="My operation description"
    )
    
    # Perform the actual write
    path.write_text(content)
    
    # Notify user
    if operation:
        print(f"[Undo ID: {operation.operation_id}]")
```

### For Existing Tools

Minimal modification approach used in v9/v3/v2 tools:

1. Add imports at top
2. Add global tracking variables
3. Modify atomic write function
4. Add argument parsing for --no-undo
5. Add summary display at end

## Safety Guarantees

### Atomicity
- All operations use file locking
- Backup created before any modification
- Operations logged only after backup succeeds

### Concurrency
- Exclusive locks prevent race conditions
- Timeout handling for stuck locks
- Process-safe operation IDs

### Recovery
- Multiple recovery paths:
  1. CLI undo command
  2. Recovery scripts
  3. Manual backup restoration
  4. Operation replay from log

## Performance Considerations

### Storage Efficiency
- Automatic gzip compression for files >1KB
- Typically 60-90% space savings
- Streaming decompression for large files

### Operation Performance
- ~5-10ms overhead per operation
- Parallel backup creation
- Lazy loading of operation history

### Scalability
- Append-only log scales to millions of operations
- Automatic cleanup of old operations
- No memory issues with streaming

## Configuration

### Environment Variables
```bash
TEXT_UNDO_MAX_HISTORY=10000      # Max operations (default: 5000)
TEXT_UNDO_MAX_AGE_DAYS=60        # Retention days (default: 30)
TEXT_UNDO_COMPRESSION=0          # Disable compression
TEXT_UNDO_STORAGE_PATH=/custom  # Custom storage location
```

### Per-Tool Control
```bash
# Disable for specific operation
--no-undo

# Custom description
--undo-description "Fix critical security bug"
```

## Security Considerations

### File Permissions
- Backups inherit source file permissions
- Storage directory is user-only (700)
- No sensitive data logging

### Data Privacy
- No encryption (use disk encryption)
- Local storage only
- No network operations

## Future Enhancements

### Planned Features
1. **Selective Undo** - Undo specific changes within a file
2. **Undo Groups** - Group related operations
3. **Remote Sync** - Sync undo history across machines
4. **Git Integration** - Hybrid version control
5. **Web UI** - Visual history browser

### Extension Points
- Custom operation types
- Plugin architecture for tools
- Alternative storage backends
- Encryption support

## Best Practices

### For Tool Developers
1. Always track operations before modifying files
2. Provide meaningful descriptions
3. Use appropriate operation types
4. Handle undo system failures gracefully

### For Users
1. Review history before major operations
2. Use custom descriptions for clarity
3. Clean old operations periodically
4. Backup the undo directory itself

## Conclusion

The multi-level undo system brings enterprise-grade safety to all text operations in the Code Intelligence Toolkit. By following SafeGIT's proven patterns and extending them to all file modifications, we provide developers and AI agents with the confidence to experiment freely, knowing that any change can be reversed.

The architecture prioritizes safety, performance, and ease of integration, making it a foundational component for reliable automated code modification.