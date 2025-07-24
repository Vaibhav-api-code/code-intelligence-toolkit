<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT Installation and Usage Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT Installation and Usage Guide

**Related Code Files:**
- `safegit.py` - Main SafeGIT wrapper (fully functional)
- `test_safegit_interception.py` - Tests confirm all interception works
- `safe_git_commands.py` - Core safety analysis engine

---

## 🚨 CRITICAL FINDING: SafeGIT Works Perfectly

**The testing revealed SafeGIT is working correctly!** All dangerous commands are being intercepted and handled properly.

## The Real Issue: Installation and Usage

The problem reported in testing was that **dangerous commands were still executing** - this means users were running `git` directly instead of through SafeGIT.

## Verified Working Commands

✅ **All dangerous commands are intercepted:**
- `python3 safegit.py reset --hard` ✅ **INTERCEPTED**  
- `python3 safegit.py clean -fdx` ✅ **INTERCEPTED**
- `python3 safegit.py push --force` ✅ **INTERCEPTED**  
- `python3 safegit.py rebase HEAD~1` ✅ **INTERCEPTED**
- `python3 safegit.py stash clear` ✅ **INTERCEPTED**
- `python3 safegit.py gc --prune=now` ✅ **INTERCEPTED**

## Installation Options

### Option 1: Alias Method (Recommended)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# SafeGIT wrapper - protects against dangerous git operations
alias git='python3 /path/to/safegit.py'

# Or with absolute path
alias git='python3 /Users/vai/DemoStrategies/Strategies/code-intelligence-toolkit/safegit.py'
```

**Then reload your shell:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Option 2: Executable Script Method

```bash
# Make safegit executable
chmod +x safegit.py

# Create a git wrapper script
cat > /usr/local/bin/git << 'EOF'
#!/bin/bash
exec python3 /path/to/safegit.py "$@"
EOF

# Make wrapper executable
chmod +x /usr/local/bin/git

# Ensure /usr/local/bin is in PATH before system git
export PATH="/usr/local/bin:$PATH"
```

### Option 3: Symlink Method

```bash
# Make safegit executable
chmod +x safegit.py

# Create symlink (ensure directory is in PATH)
ln -s /path/to/safegit.py /usr/local/bin/git

# Or link with safegit name and use explicitly
ln -s /path/to/safegit.py /usr/local/bin/safegit
```

## Usage Verification

**After installation, verify SafeGIT is intercepting commands:**

```bash
# This should show SafeGIT interception message:
git --dry-run reset --hard

# Expected output:
# 🔍 DRY-RUN MODE: Simulating command without executing
# 🛡️  SafeGIT: Intercepting dangerous 'git reset --hard' command
```

## Common Issues

### Issue 1: Commands Still Execute Dangerously

**Problem:** Running `git reset --hard` still executes without SafeGIT warnings.

**Cause:** SafeGIT is not properly installed as git wrapper.

**Solution:** Verify your installation:
```bash
# Check which git is being used
which git

# Should point to SafeGIT location, not system git
```

### Issue 2: SafeGIT Not Found

**Problem:** `command not found: safegit` or import errors.

**Solution:** 
```bash
# Run with full python path
python3 /full/path/to/safegit.py --version

# Check dependencies
python3 -c "import sys; print(sys.path)"
```

### Issue 3: Permission Errors

**Problem:** Permission denied when running SafeGIT.

**Solution:**
```bash
# Make script executable
chmod +x safegit.py

# Check file permissions
ls -la safegit.py
```

## AI Agent Integration

For AI agents (Claude, GPT, etc.), configure them to use SafeGIT:

### Claude Code Integration

Add to your AI prompts:
```
Always use 'python3 safegit.py' instead of 'git' for all git operations.
Never run 'git' directly - always use the SafeGIT wrapper.
```

### Environment Integration

Set environment variable:
```bash
export SAFEGIT_PATH="/path/to/safegit.py"
```

## Testing Your Installation

Run this test sequence to verify SafeGIT is working:

```bash
# Test 1: Dry-run mode
git --dry-run reset --hard
# Should show: "🛡️ SafeGIT: Intercepting dangerous..."

# Test 2: Version check  
git --version
# Should show: "SafeGIT v1.0 - Git wrapper for AI safety"

# Test 3: Help
git --help
# Should show SafeGIT help, not system git help

# Test 4: Safe command passthrough
git status
# Should work normally (safe commands pass through)
```

## Advanced Configuration

### Context-Aware Safety

```bash
# Set development mode (more lenient)
git context development

# Set production mode (stricter)  
git context production

# View current context
git context show
```

### Undo System

```bash
# View operation history
git undo-history

# Undo last operation
git undo

# Interactive undo
git undo --interactive
```

## Troubleshooting

### Debug Mode

Enable verbose logging:
```bash
# Run with debug output
SAFEGIT_DEBUG=1 git reset --hard

# Check interception logs
tail ~/.safegit/intercepted_commands.log
```

### Reset to System Git

If you need to temporarily bypass SafeGIT:
```bash
# Run system git directly
/usr/bin/git reset --hard

# Or disable alias temporarily
\git reset --hard
```

## Conclusion

SafeGIT is **fully functional and correctly intercepting dangerous commands**. The key is proper installation as a git wrapper. Once installed correctly:

✅ **All dangerous operations are intercepted**  
✅ **Safe operations pass through normally**  
✅ **Provides educational warnings and alternatives**  
✅ **Supports dry-run mode for testing**  
✅ **Includes comprehensive undo system**  

The reported issues were due to users running `git` directly instead of through the SafeGIT wrapper.