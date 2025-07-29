# Release Notes - Code Intelligence Toolkit v1.5.0

**Release Date**: July 28, 2025  
**Type**: Major Release - Interactive Utils Migration

## 🎯 Overview

Version 1.5.0 completes the migration of all critical Python tools to use the unified `interactive_utils.py` module, eliminating EOF errors in CI/CD environments and providing consistent non-interactive mode handling across the entire toolkit.

## 🚀 Major Features

### Complete Interactive Utils Migration

All critical tools now handle non-interactive environments gracefully:

- **No More EOF Crashes** - Clear, actionable error messages instead of cryptic failures
- **Automatic CI/CD Detection** - Recognizes GitHub Actions, GitLab CI, Jenkins, and more
- **Unified Configuration** - Same patterns work across all tools
- **Multiple Prompt Types** - Yes/no, typed phrases, numbered selections, multi-choice

### Tools Fully Migrated

1. **text_undo.py**
   - Numbered selection menus for restore operations
   - Full environment variable and config file support

2. **safe_file_manager.py**
   - Risk-based confirmations with typed phrases for high-risk operations
   - Automatic mode selection based on operation risk level

3. **safegit.py**
   - Multi-choice prompts (1/2/3 options)
   - Typed confirmations for dangerous git operations
   - Graduated safety levels with appropriate prompts

4. **replace_text_v9.py**
   - Large change confirmations with configurable thresholds
   - Automatic detection of batch operations

5. **replace_text_ast_v3.py**
   - Batch operation confirmations with y/n/q support
   - Per-file confirmation options for granular control

## 📋 Configuration Methods

Tools now support configuration in priority order:

1. **Command-line flags** (highest priority)
   ```bash
   ./run_any_python_tool.sh tool_name.py --yes
   ```

2. **Environment variables**
   ```bash
   export TOOL_NAME_ASSUME_YES=1
   ./run_any_python_tool.sh tool_name.py
   ```

3. **Tool-specific .pytoolsrc**
   ```ini
   [tool_name]
   assume_yes = true
   ```

4. **Global .pytoolsrc defaults**
   ```ini
   [defaults]
   non_interactive = true
   ```

5. **Hard-coded defaults** (interactive by default)

## 🔧 Technical Details

### interactive_utils.py Module

The new shared module provides:

```python
# Core functions
is_interactive()          # Auto-detect environment
safe_input()             # EOF-safe input handling
get_confirmation()       # Yes/no prompts
get_multi_choice()       # Multiple choice (y/n/q)
get_numbered_selection() # Numbered menu selections
check_auto_yes_env()     # Environment variable support
```

### Error Messages

Before (v1.4.0):
```
EOFError: EOF when reading a line
```

After (v1.5.0):
```
❌ ERROR: Interactive confirmation required but running in non-interactive mode.
       Use --yes flag to skip confirmation
       Or set TOOL_NAME_ASSUME_YES=1 environment variable
       Or set 'assume_yes = true' in .pytoolsrc [tool_name] section
```

## 🔄 Migration Guide

For tools not yet migrated:

1. Import interactive_utils with fallback:
   ```python
   try:
       from interactive_utils import get_confirmation
   except ImportError:
       # Fallback implementation
   ```

2. Replace `input()` calls:
   ```python
   # Before
   response = input("Continue? [y/N]: ")
   
   # After
   confirmed = get_confirmation("Continue?", tool_name="my_tool")
   ```

3. Add environment variable support:
   ```python
   check_auto_yes_env('my_tool', args)
   ```

## 📊 Impact

- **100% EOF Error Elimination** in migrated tools
- **Consistent UX** across all interactive prompts
- **CI/CD Ready** out of the box
- **Backward Compatible** with all existing workflows

## 🙏 Acknowledgments

Special thanks to all contributors who helped test and refine the interactive utils system, making the Code Intelligence Toolkit more robust and CI/CD friendly.

## 📚 Documentation

- [Interactive Utils Migration Status](INTERACTIVE_UTILS_MIGRATION_STATUS.md)
- [Non-Interactive Mode Guide](NON_INTERACTIVE_GUIDE.md)
- [Comprehensive Documentation](TOOLS_DOCUMENTATION_2025.md)

---

For questions or issues, please open an issue on GitHub.