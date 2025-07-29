# Interactive Migration Plan - Comprehensive Update Strategy

**Related Code Files:**
- `interactive_utils_v2.py` - Enhanced shared utility module
- All Python tools with interactive prompts

---

## Executive Summary

We need to update 10+ tools to use the common `interactive_utils_v2.py` module for consistent non-interactive mode handling. This will eliminate EOF errors and provide clear, actionable error messages across all tools.

## Enhanced interactive_utils_v2.py Features

The new version now supports ALL interaction patterns found in our tools:

1. ✅ **Basic yes/no confirmations** - `get_confirmation()`
2. ✅ **Typed phrase confirmations** - `get_confirmation(typed_confirmation="DELETE")`
3. ✅ **Multi-choice prompts** - `get_multi_choice()` for y/n/force, y/n/q
4. ✅ **Numbered selection menus** - `get_numbered_selection()` for restore/undo
5. ✅ **Multi-step confirmations** - `get_multi_confirmation()` for dangerous ops
6. ✅ **Environment variable support** - Standardized checking
7. ✅ **Force flags** - Support for --force in addition to --yes

## Tool Update Priority and Plan

### Phase 1: High-Impact Tools (Most Used)

#### 1. **sync_tools_to_desktop.py** ⚠️
**Current State**: Limited non-interactive support (only --force)
**Interactive Patterns**:
- Three-way prompt: "y/N/force"
- Basic y/N confirmations

**Migration Tasks**:
```python
# Replace
response = input("Proceed with sync? (y/N/force): ").strip().lower()

# With
choice = get_multi_choice(
    "Proceed with sync?",
    [('y', PromptChoice.YES), ('n', PromptChoice.NO), ('force', PromptChoice.FORCE)],
    default=PromptChoice.NO,
    tool_name='sync_tools_to_desktop',
    env_var='SYNC_TOOLS_ASSUME_YES'
)
```

#### 2. **text_undo.py** ⚠️ 
**Current State**: Partial migration (confirmations done, selections missing)
**Interactive Patterns**:
- ✅ Y/n confirmations (already migrated)
- ❌ Numbered selection for interactive undo

**Migration Tasks**:
```python
# Add support for numbered selection
if args.interactive:
    selection = get_numbered_selection(
        "Select operation to undo",
        [str(op) for op in operations],
        tool_name='text_undo',
        env_var='TEXT_UNDO',
        flag_hint='--operation ID'
    )
```

### Phase 2: Tools with Complex Interactions

#### 3. **safe_move.py** ⚠️
**Current State**: Good support but not using common module
**Interactive Patterns**:
- Y/n confirmations
- Numbered selection for undo

**Migration Tasks**:
- Import interactive_utils_v2
- Replace custom input handling with common functions

#### 4. **safegit_undo_stack.py** ⚠️
**Current State**: Limited non-interactive support
**Interactive Patterns**:
- Y/n confirmations
- Numbered selection: "Select operation to undo (1-10)"

**Migration Tasks**:
- Add proper argument parsing for --yes flag
- Use get_numbered_selection() for interactive mode
- Add environment variable support

### Phase 3: Tools Already Well-Supported (Verify & Enhance)

#### 5. **replace_text_ast_v2.py / v3.py** ✅
**Current State**: Full non-interactive support
**Interactive Patterns**:
- File-by-file confirmations with quit option (y/N/q)
- Batch confirmations

**Migration Tasks**:
- Could benefit from using get_multi_choice() for consistency
- Already handles non-interactive well

#### 6. **refactor_rename.py / v2.py** ✅
**Current State**: Good support
**Migration Tasks**:
- Minor: Use common module for consistency

### Phase 4: Special Cases

#### 7. **api.py / api_prototype.py** 🔄
**Current State**: Interactive REPL by design
**Migration Tasks**:
- These are meant to be interactive
- Could add batch mode support using common module

## Implementation Steps

### Step 1: Test interactive_utils_v2.py
```bash
# Create test script
cat > test_interactive_utils.py << 'EOF'
#!/usr/bin/env python3
from interactive_utils_v2 import *

# Test all functions
print("Testing confirmations...")
result = get_confirmation("Test confirm?", tool_name="test", env_var="TEST_ASSUME_YES")
print(f"Result: {result}")

print("\nTesting multi-choice...")
choice = get_multi_choice(
    "Choose action",
    [('y', PromptChoice.YES), ('n', PromptChoice.NO), ('f', PromptChoice.FORCE)],
    tool_name="test"
)
print(f"Choice: {choice}")

print("\nTesting numbered selection...")
selection = get_numbered_selection(
    "Select item",
    ["Option 1", "Option 2", "Option 3"],
    tool_name="test"
)
print(f"Selected: {selection}")
EOF

# Test in different modes
python test_interactive_utils.py  # Interactive
echo "" | python test_interactive_utils.py  # Non-interactive
TEST_ASSUME_YES=1 python test_interactive_utils.py  # With env var
```

### Step 2: Create Migration Template
```python
# Standard migration template for each tool

# 1. Add imports
try:
    from interactive_utils_v2 import (
        safe_input, get_confirmation, get_multi_choice,
        get_numbered_selection, check_auto_yes_env,
        get_tool_env_var, Colors, PromptChoice
    )
    HAS_INTERACTIVE_UTILS = True
except ImportError:
    HAS_INTERACTIVE_UTILS = False
    # Provide fallbacks
    
# 2. Update argument parsing
parser.add_argument('--yes', '-y', action='store_true',
                   help='Auto-confirm prompts')
parser.add_argument('--non-interactive', action='store_true',
                   help='Fail instead of prompting')

# 3. Check environment
check_auto_yes_env('tool_name', args)

# 4. Replace input() calls
# See specific patterns above
```

### Step 3: Update Each Tool
1. Apply migration template
2. Test interactive mode
3. Test non-interactive mode
4. Test with environment variables
5. Update tool documentation

### Step 4: Create Comprehensive Tests
```bash
# Test suite for all migrated tools
for tool in text_undo.py sync_tools_to_desktop.py safe_move.py; do
    echo "Testing $tool"
    # Test non-interactive detection
    echo "" | python $tool --help
    # Test with flags
    python $tool --yes --dry-run
    # Test with env vars
    TOOL_ASSUME_YES=1 python $tool --dry-run
done
```

## Success Criteria

1. **No EOF Errors**: All tools handle non-interactive gracefully
2. **Clear Messages**: Users know exactly what flags/env vars to use
3. **Consistent Behavior**: All tools use same patterns
4. **Backward Compatible**: Existing scripts continue to work
5. **CI/CD Ready**: All tools work in automated environments

## Timeline

- **Phase 1**: 1 hour (high-impact tools)
- **Phase 2**: 1 hour (complex interactions)
- **Phase 3**: 30 minutes (verification)
- **Phase 4**: 30 minutes (special cases)
- **Testing**: 1 hour

Total: ~4 hours for complete migration

## Post-Migration

1. Update CLAUDE.md with new non-interactive guidelines
2. Create NON_INTERACTIVE_GUIDE.md with examples
3. Add to release notes
4. Consider making interactive_utils_v2.py the standard