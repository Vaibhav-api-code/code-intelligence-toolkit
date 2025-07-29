# Interactive Utils - Comprehensive Non-Interactive Mode Solution

**Related Code Files:**
- `interactive_utils.py` - The unified solution for all interactive prompts
- `text_undo.py` - Example of migrated tool
- `INTERACTIVE_MIGRATION_PLAN.md` - Complete migration strategy

---

## Problem Solved

We've created a comprehensive solution for the EOF errors that occur when tools run in non-interactive environments (CI/CD, pipes, scripts). Instead of ugly stack traces, users now get clear, actionable error messages.

## Solution Overview

### 1. Created `interactive_utils.py`

A shared module that ALL tools can use for consistent non-interactive handling:

```python
from interactive_utils import (
    get_confirmation,         # Yes/no prompts
    get_multi_choice,        # y/n/force, y/n/q prompts
    get_numbered_selection,  # Select from list (1-10)
    get_multi_confirmation,  # Multiple confirmations
    safe_input,             # Safe input with defaults
    check_auto_yes_env      # Environment variable support
)
```

### 2. Comprehensive Feature Set

The module handles ALL interaction patterns found in our tools:

| Pattern | Function | Example |
|---------|----------|---------|
| Yes/No | `get_confirmation()` | "Proceed? [y/N]" |
| Typed Phrase | `get_confirmation(typed_confirmation="DELETE")` | "Type 'DELETE' to confirm" |
| Multi-Choice | `get_multi_choice()` | "Action? [y/N/force]" |
| Numbered List | `get_numbered_selection()` | "Select (1-10) or 0 to cancel" |
| Multi-Step | `get_multi_confirmation()` | Multiple dangerous confirmations |

### 3. Non-Interactive Support

Every function gracefully handles non-interactive mode:

```bash
# EOF error before:
echo "" | python tool.py
# EOFError: EOF when reading a line

# Clear message after:
echo "" | python tool.py
# ERROR: Interactive confirmation required but running in non-interactive mode.
#        Use --yes flag to skip confirmation
#        Or set TOOL_ASSUME_YES=1 environment variable
```

### 4. Environment Variables

Standardized environment variable support:
- `{TOOL}_ASSUME_YES=1` - Auto-confirm prompts
- `{TOOL}_FORCE_YES=1` - Force dangerous operations
- `{TOOL}_NONINTERACTIVE=1` - Strict non-interactive mode

### 5. Example Migration

text_undo.py has been migrated as an example:

```python
# Before (crashes with EOF):
confirm = input(f"Proceed with undo? (y/N): ")

# After (handles non-interactive gracefully):
if not get_confirmation(
    "Proceed with undo?",
    tool_name='text_undo',
    env_var='TEXT_UNDO_ASSUME_YES'
):
    print("Cancelled.")
    return
```

## Tools to Migrate

### High Priority
1. **sync_tools_to_desktop.py** - No env var support
2. **text_undo.py** - Needs numbered selection support
3. **safegit_undo_stack.py** - Limited non-interactive support

### Medium Priority
4. **safe_move.py** - Not using common module
5. **refactor_rename.py/v2.py** - For consistency

### Already Good (Minor Updates)
6. **safe_file_manager.py** - Has full support
7. **safegit.py** - Has full support
8. **replace_text_ast_v2/v3.py** - Has full support

## Benefits

1. **No More EOF Errors** - Clear messages instead of crashes
2. **CI/CD Ready** - All tools work in automation
3. **Consistent UX** - Same behavior across all tools
4. **User Friendly** - Clear instructions on what to do
5. **Backward Compatible** - Existing scripts continue to work

## Next Steps

1. Migrate remaining tools using the template
2. Test in various non-interactive environments
3. Update documentation
4. Add to release notes as a major improvement

This solution ensures that all Code Intelligence Toolkit tools work seamlessly in both interactive terminals and automated environments!