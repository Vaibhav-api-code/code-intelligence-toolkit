# Non-Interactive Mode Error Handling Fix

**Related Code Files:**
- `text_undo.py` - Needs TTY detection and better error messages
- `safe_file_manager.py` - Already has good non-interactive support
- `safe_file_manager_undo_wrapper.py` - Needs to inherit parent's non-interactive handling

---

## Problem Analysis

When running in non-interactive environments (CI/CD, pipes, background processes), tools that call `input()` receive EOF errors because there's no TTY attached. This results in ugly stack traces instead of helpful error messages.

## Current State

### Good Examples (How It Should Work)
- **safe_file_manager.py**: Has proper non-interactive detection with `--non-interactive` flag and `SFM_ASSUME_YES` environment variable
- **safegit.py**: Auto-detects CI environments and supports `SAFEGIT_ASSUME_YES`

### Problem Cases
- **text_undo.py**: Crashes with EOFError when trying to confirm undo operations
- **safe_file_manager_undo_wrapper.py**: Doesn't properly pass through non-interactive flags

## Proposed Solution

### 1. Add TTY Detection Helper

```python
def is_interactive():
    """Check if we're running in an interactive terminal."""
    # Check if stdin is a TTY
    if not sys.stdin.isatty():
        return False
    
    # Check common CI environment variables
    ci_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 
               'GITLAB_CI', 'JENKINS_URL', 'TRAVIS']
    if any(os.getenv(var) for var in ci_vars):
        return False
    
    # Check for non-interactive flags
    if os.getenv('NONINTERACTIVE') == '1':
        return False
        
    return True
```

### 2. Wrap Input Calls

```python
def safe_input(prompt, default=None):
    """Safe input that handles non-interactive mode."""
    if not is_interactive():
        if default is not None:
            print(f"{prompt} [auto-answering: {default}]")
            return default
        else:
            print(f"ERROR: Interactive confirmation required but running in non-interactive mode.")
            print(f"       Use --yes flag or set appropriate environment variable.")
            print(f"       Original prompt: {prompt}")
            sys.exit(1)
    
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled.")
        sys.exit(1)
```

### 3. Update text_undo.py

Replace line 227:
```python
# OLD
confirm = input(f"\n{Colors.BOLD}Proceed with undo? (y/N):{Colors.END} ")

# NEW
if not is_interactive() and not args.yes:
    print(f"\n{Colors.RED}ERROR: Interactive confirmation required but running in non-interactive mode.{Colors.END}")
    print(f"       Use --yes flag to skip confirmation or set TEXT_UNDO_ASSUME_YES=1")
    return 1

confirm = safe_input(f"\n{Colors.BOLD}Proceed with undo? (y/N):{Colors.END} ", 
                    default='y' if args.yes else None)
```

### 4. Environment Variable Support

Add to text_undo.py:
```python
# Check environment variable
if os.getenv('TEXT_UNDO_ASSUME_YES') == '1':
    args.yes = True
```

## Benefits

1. **Clear Error Messages**: Users understand why the tool failed and how to fix it
2. **Consistent Behavior**: All tools handle non-interactive mode the same way
3. **CI/CD Friendly**: Tools work seamlessly in automated environments
4. **Backward Compatible**: Existing interactive usage unchanged

## Implementation Priority

1. **text_undo.py** - Most commonly hits this error
2. **safe_file_manager_undo_wrapper.py** - Should inherit parent's behavior
3. **Any other tools with input()** - Apply same pattern

## Testing

```bash
# Test non-interactive detection
echo "test" | ./run_any_python_tool.sh text_undo.py undo --last
# Should show: "ERROR: Interactive confirmation required..."

# Test with flag
echo "test" | ./run_any_python_tool.sh text_undo.py undo --last --yes
# Should work without prompting

# Test with environment
TEXT_UNDO_ASSUME_YES=1 ./run_any_python_tool.sh text_undo.py undo --last
# Should work without prompting
```