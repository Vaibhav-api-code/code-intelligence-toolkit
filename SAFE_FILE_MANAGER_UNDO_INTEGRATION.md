# Safe File Manager Undo Integration

**Related Code Files:**
- `safe_file_manager_undo_wrapper.py` - Lightweight wrapper that adds undo tracking
- `sfm_undo_integration.py` - Deep integration module with hook system
- `safe_file_manager.py` - The core file management tool
- `text_operation_history.py` - Multi-level undo system
- `text_undo_system.py` - Command-line interface for undo operations

---

## Overview

The Safe File Manager Undo Integration provides automatic tracking of file operations performed through `safe_file_manager.py`, enabling multi-level undo capabilities for recovery from mistakes.

## Components

### 1. Lightweight Wrapper (`safe_file_manager_undo_wrapper.py`)

A drop-in replacement for `safe_file_manager.py` that intercepts operations and tracks them in the undo system.

**Features:**
- Transparent operation - no changes to safe_file_manager's behavior
- Automatic content tracking for create/write operations
- Operation type mapping to undo system categories
- Minimal overhead - only tracks on successful operations

**Usage:**
```bash
# Instead of:
./run_any_python_tool.sh safe_file_manager.py create file.txt --content "text"

# Use:
./safe_file_manager_undo_wrapper.py create file.txt --content "text"
```

**Environment Variables:**
- `SFM_NO_UNDO=1` - Disable undo tracking for specific operations

### 2. Hook-Based Integration (`sfm_undo_integration.py`)

A more sophisticated approach that integrates with safe_file_manager's internal transaction system (if available).

**Features:**
- Pre/post operation hooks
- Transaction-aware tracking
- Binary file handling
- Atomic operation support

**Setup:**
```bash
# Install hooks
python3 sfm_undo_integration.py

# Disable hooks
python3 sfm_undo_integration.py disable
```

## Operation Type Mapping

| safe_file_manager Command | Undo Operation Type | Content Tracked |
|---------------------------|---------------------|-----------------|
| create                    | CREATE              | New content     |
| write                     | WRITE               | Old + New       |
| copy/cp                   | CREATE              | New content     |
| move/mv                   | RENAME              | Path change     |
| trash/rm                  | DELETE              | Old content*    |
| chmod                     | MODIFY              | Permission      |
| chown                     | MODIFY              | Ownership       |

*Note: Delete operations require pre-capture of content

## Undo Workflow

### View Recent Operations
```bash
# List recent file operations
./run_any_python_tool.sh text_undo_system.py list --recent 10

# Show operations for specific file
./run_any_python_tool.sh text_undo_system.py list --file myfile.txt
```

### Undo Operations
```bash
# Undo last operation
./run_any_python_tool.sh text_undo_system.py undo

# Undo specific operation
./run_any_python_tool.sh text_undo_system.py undo <operation-id>

# Interactive undo
./run_any_python_tool.sh text_undo_system.py undo --interactive
```

## Integration Examples

### Example 1: Safe File Creation with Undo
```bash
# Create file with undo tracking
./safe_file_manager_undo_wrapper.py create config.json --content '{"key": "value"}'
# Output: ✓ Operation tracked for undo: create_1234567890

# Oops, wrong content\! Undo it
./run_any_python_tool.sh text_undo_system.py undo
# File removed, ready to recreate
```

### Example 2: Batch Operations with Tracking
```bash
# Enable undo for batch operations
export SFM_ASSUME_YES=1

# Perform multiple operations
for file in *.tmp; do
    ./safe_file_manager_undo_wrapper.py trash "$file"
done

# Review what was done
./run_any_python_tool.sh text_undo_system.py list --recent 20

# Undo if needed
./run_any_python_tool.sh text_undo_system.py undo --interactive
```

### Example 3: CI/CD Integration
```bash
# In CI scripts, disable undo to avoid overhead
export SFM_NO_UNDO=1
./safe_file_manager_undo_wrapper.py create build/output.txt
```

## Technical Details

### Content Tracking Strategy
1. **Before Operation**: Capture existing file content (if applicable)
2. **Execute Operation**: Let safe_file_manager perform the operation
3. **After Success**: Capture new state and record in undo system
4. **On Failure**: Discard tracking data

### Performance Considerations
- Text files: Full content tracked (for reliable undo)
- Binary files: Only metadata tracked (size, permissions)
- Large files: Consider disabling undo with `SFM_NO_UNDO=1`

### Limitations
1. **Delete Recovery**: Wrapper cannot capture content before deletion without modifying safe_file_manager
2. **Atomic Operations**: Some complex operations may not be fully reversible
3. **Binary Files**: Content recovery limited to text files

## Future Enhancements

1. **Deep Integration**: Modify safe_file_manager.py to call undo hooks directly
2. **Binary Support**: Add binary file recovery via temporary copies
3. **Batch Undo**: Group related operations for single undo
4. **Remote Sync**: Track operations across machines

## Troubleshooting

### Undo Not Working
```bash
# Check if undo system is available
python3 -c "import text_operation_history; print('Undo system available')"

# Check operation history
ls -la ~/.undo_history/
```

### Performance Issues
```bash
# Disable for large operations
SFM_NO_UNDO=1 ./safe_file_manager_undo_wrapper.py copy large_dir/ backup/

# Or use original tool
./run_any_python_tool.sh safe_file_manager.py copy large_dir/ backup/
```

### Wrapper Errors
```bash
# Test wrapper directly
python3 safe_file_manager_undo_wrapper.py --help

# Check Python path
which python3
python3 --version
```

## Best Practices

1. **Use Wrapper for Interactive Work**: Human errors benefit most from undo
2. **Disable for Automation**: CI/CD rarely needs undo overhead
3. **Review Before Undo**: Always check what will be undone
4. **Test First**: Try undo on test files before production use

## Summary

The Safe File Manager Undo Integration provides a safety net for file operations without changing the core tool's behavior. Choose the wrapper for simple drop-in undo support, or the hook system for deeper integration.
