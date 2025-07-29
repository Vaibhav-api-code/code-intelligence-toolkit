# Interactive Utils Migration Guide

**Related Code Files:**
- `interactive_utils.py` - The new shared utility module
- `text_undo.py` - Example of migrated tool
- All Python tools that use `input()` or interactive prompts

---

## Overview

We've created a common solution for handling non-interactive environments across all tools. This prevents ugly EOF errors and provides clear, actionable error messages.

## Migration Steps

### 1. Import the Module

Add to your imports:
```python
try:
    from interactive_utils import (
        safe_input, get_confirmation, check_auto_yes_env,
        get_tool_env_var, require_interactive, Colors
    )
except ImportError:
    # Fallback for older installations
    print("Warning: interactive_utils module not found. Using basic input handling.", file=sys.stderr)
    safe_input = input
    # ... provide basic fallbacks
```

### 2. Replace Direct input() Calls

**Before:**
```python
response = input("Enter value: ")
confirm = input("Proceed? [y/N]: ")
```

**After:**
```python
response = safe_input(
    "Enter value: ",
    tool_name="my_tool",
    env_var="MY_TOOL_ASSUME_YES"
)

confirmed = get_confirmation(
    "Proceed?",
    default=False,
    tool_name="my_tool",
    env_var="MY_TOOL_ASSUME_YES"
)
```

### 3. Add Environment Variable Support

In your argument parsing:
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--yes', '-y', action='store_true', 
                       help='Skip confirmations')
    args = parser.parse_args()
    
    # Check environment variable
    check_auto_yes_env('my_tool', args)
```

### 4. Handle Interactive-Only Operations

For operations that cannot work in non-interactive mode:
```python
# For selecting from a list
require_interactive("interactive file selection", tool_name="my_tool")
choice = input("Select file (1-10): ")  # Safe to use input() after require_interactive
```

## Common Patterns

### Simple Yes/No Confirmation
```python
if not get_confirmation("Delete file?", tool_name="my_tool"):
    print("Operation cancelled")
    return
```

### Typed Confirmation (High Risk)
```python
if not get_confirmation(
    "This will delete all data!",
    typed_confirmation="DELETE ALL",
    tool_name="my_tool"
):
    return
```

### Input with Default
```python
name = safe_input(
    "Enter name [default]: ",
    default="default",
    tool_name="my_tool"
)
```

## Environment Variables

Each tool should support:
- `{TOOL_NAME}_ASSUME_YES=1` - Auto-confirm all prompts
- Standard CI variables are auto-detected

## Tools Needing Migration

High Priority (frequently hit EOF errors):
1. ✅ `text_undo.py` - DONE
2. ❌ `safe_file_manager.py` - Already has good support, needs integration
3. ❌ `replace_text_v9.py` - Confirmation prompts
4. ❌ `replace_text_ast_v3.py` - Confirmation prompts
5. ❌ `unified_refactor_v2.py` - Confirmation prompts
6. ❌ `refactor_rename_v2.py` - Confirmation prompts

Medium Priority:
- All tools with `--confirm-each` options
- Tools that show diffs and ask for confirmation
- Any tool using `getpass` for sensitive input

## Testing

Test your migrated tool:
```bash
# Should show clear error
echo "test" | python my_tool.py

# Should work
echo "test" | python my_tool.py --yes

# Should work
MY_TOOL_ASSUME_YES=1 python my_tool.py
```

## Benefits

1. **Consistent UX** - All tools behave the same way
2. **CI/CD Ready** - Works in all automation environments
3. **Clear Errors** - Users know exactly what to do
4. **Backward Compatible** - Fallbacks for older installations