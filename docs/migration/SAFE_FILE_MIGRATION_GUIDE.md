<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Safe File Manager - Migration Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Safe File Manager - Migration Guide

**Related Code Files:**
- `code-intelligence-toolkit/safe_file_manager.py` - Main implementation
- `code-intelligence-toolkit/safe_move.py` - Original tool being replaced
- `code-intelligence-toolkit/SAFE_FILE_MANAGER_GUIDE.md` - Comprehensive documentation

---

## Quick Start: Replacing Dangerous Commands

### For AI Agents and Automation

```bash
# Set up for non-interactive use
export SAFE_FILE_NONINTERACTIVE=1
export SAFE_FILE_ASSUME_YES=1

# Now use sfm instead of traditional commands
alias rm='sfm trash'
alias mv='sfm move'
alias cp='sfm copy'
alias ls='sfm list'
```

### Command Translation Table

| Instead of... | Use... | Benefits |
|--------------|--------|----------|
| `rm file.txt` | `sfm trash file.txt` | Recoverable from trash |
| `rm -rf dir/` | `sfm trash dir/` | Safe with confirmations |
| `rm -f *.tmp` | `sfm trash *.tmp` | Batch operation with manifest |
| `mv old new` | `sfm move old new` | Atomic operation with checksum |
| `mv *.txt dir/` | `sfm move *.txt dir/` | Concurrent processing |
| `cp file backup` | `sfm copy file backup` | Verified copy with retry |
| `cp -r src/ dst/` | `sfm copy src/ dst/` | Recursive by default |
| `ls -la` | `sfm list -la` | Git status included |
| `ls -ltr` | `sfm list -l --sort time` | Enhanced sorting |
| `cat file.txt` | `sfm info file.txt` | Safe file inspection |

## Migration Scenarios

### Scenario 1: Replacing rm in Scripts

**Before:**
```bash
#!/bin/bash
# Dangerous cleanup script
rm -f /tmp/*.log
rm -rf /tmp/build-*
find . -name "*.tmp" -delete
```

**After:**
```bash
#!/bin/bash
# Safe cleanup script
sfm trash /tmp/*.log
sfm trash /tmp/build-*
find . -name "*.tmp" -exec sfm trash {} \;
```

### Scenario 2: Safe Deployment Scripts

**Before:**
```bash
# Risky deployment
rm -rf /var/www/old_version
mv /var/www/current /var/www/old_version
cp -r build/ /var/www/current
```

**After:**
```bash
# Safe deployment with rollback capability
sfm trash /var/www/old_version
sfm move /var/www/current /var/www/old_version
sfm copy --verify-checksum build/ /var/www/current

# Can restore if needed:
# sfm restore "old_version"
```

### Scenario 3: File Organization

**Before:**
```bash
# Manual organization
mkdir -p sorted/pdf sorted/doc sorted/img
mv *.pdf sorted/pdf/
mv *.doc sorted/doc/
mv *.{jpg,png,gif} sorted/img/
```

**After:**
```bash
# Automated organization
sfm organize . --by extension
# or with custom rules
sfm organize . --by custom --rules my_rules.yaml
```

### Scenario 4: Backup Synchronization

**Before:**
```bash
# Basic rsync
rsync -av --delete source/ backup/
```

**After:**
```bash
# Safe sync with verification
sfm sync source/ backup/ --delete --verify-checksum
```

## Setting Up Aliases

### Bash/Zsh (.bashrc or .zshrc)

```bash
# Safe replacements for dangerous commands
alias rm='sfm trash'
alias mv='sfm move'
alias cp='sfm copy'
alias ls='sfm list'

# Convenience aliases
alias ll='sfm list -l'
alias la='sfm list -la'
alias ltr='sfm list -l --sort time'
alias org='sfm organize'
alias restore='sfm restore'

# Quick info
alias info='sfm info'
alias finfo='sfm info'  # file info

# For habits
alias del='echo "Use sfm trash instead"'
alias delete='echo "Use sfm trash instead"'
```

### Fish Shell (config.fish)

```fish
# Safe command replacements
function rm
    sfm trash $argv
end

function mv
    sfm move $argv
end

function cp
    sfm copy $argv
end

function ls
    sfm list $argv
end
```

### PowerShell

```powershell
# Safe command replacements
function rm { sfm trash @args }
function mv { sfm move @args }
function cp { sfm copy @args }
function ls { sfm list @args }
```

## Integration Examples

### Makefile Integration

```makefile
# Use sfm for safe operations
.PHONY: clean
clean:
	sfm trash build/ dist/ *.log

.PHONY: install
install:
	sfm copy --verify-checksum dist/* /usr/local/bin/

.PHONY: backup
backup:
	sfm sync . ../backup/$(shell date +%Y%m%d)/
```

### Python Script Integration

```python
import subprocess
import json

def safe_move(source, destination):
    """Safely move files using sfm"""
    result = subprocess.run(
        ['sfm', '--non-interactive', '--yes', 'move', source, destination],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def get_file_info(path):
    """Get file information using sfm"""
    result = subprocess.run(
        ['sfm', 'info', '--json', path],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None
```

### Node.js Integration

```javascript
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function safeMove(source, destination) {
    try {
        await execPromise(`sfm --non-interactive --yes move ${source} ${destination}`);
        return true;
    } catch (error) {
        console.error('Move failed:', error);
        return false;
    }
}

async function organizeDownloads() {
    try {
        const { stdout } = await execPromise('sfm organize ~/Downloads --by extension --json');
        return JSON.parse(stdout);
    } catch (error) {
        console.error('Organization failed:', error);
        return null;
    }
}
```

## Gradual Migration Strategy

### Phase 1: Awareness (Week 1)
```bash
# Add warnings but don't block
alias rm='echo "Consider using sfm trash instead" && command rm'
alias mv='echo "Consider using sfm move instead" && command mv'
```

### Phase 2: Soft Enforcement (Week 2-3)
```bash
# Interactive prompt
function rm() {
    echo "Warning: rm is dangerous. Use sfm trash instead? [Y/n]"
    read response
    if [[ "$response" != "n" ]]; then
        sfm trash "$@"
    else
        command rm "$@"
    fi
}
```

### Phase 3: Full Migration (Week 4+)
```bash
# Complete replacement
alias rm='sfm trash'
alias mv='sfm move'
alias cp='sfm copy'

# Block direct access
alias /bin/rm='echo "Direct rm blocked. Use sfm trash"'
alias /bin/mv='echo "Direct mv blocked. Use sfm move"'
```

## Common Concerns and Solutions

### "It's slower than native commands"

Safe File Manager is optimized for safety, not raw speed. However:
- Concurrent operations often match native speed
- Disable checksums for non-critical files: `--no-checksum`
- Use native commands within sfm's safety framework when needed

### "I need to delete immediately"

For true immediate deletion:
```bash
# Skip trash, directly delete (still requires confirmation)
sfm delete file.txt

# Force in non-interactive mode
sfm --non-interactive --force delete file.txt
```

### "My scripts depend on specific rm behavior"

Create compatibility wrappers:
```bash
# rm-compat: Compatibility wrapper
#!/bin/bash
if [[ "$1" == "-rf" ]]; then
    shift
    sfm --non-interactive --force trash "$@"
else
    sfm --non-interactive --yes trash "$@"
fi
```

### "I work with huge files"

Optimize for large files:
```bash
# Disable checksum for large files
export SAFE_FILE_VERIFY_CHECKSUM=false
sfm move large.iso /backup/

# Or per-operation
sfm --no-checksum move large.iso /backup/
```

## Rollback Plan

If you need to temporarily disable safe replacements:

```bash
# Temporary disable
unalias rm mv cp ls

# Or use full paths
/bin/rm file.txt
/bin/mv old new

# Re-enable when ready
source ~/.bashrc
```

## Getting Help

```bash
# General help
sfm --help

# Command-specific help
sfm move --help
sfm organize --help

# Check current configuration
sfm config show

# View recent operations
sfm history

# Debug issues
export SAFE_FILE_LOG_LEVEL=DEBUG
sfm --verbose [command]
```

## Next Steps

1. **Install Safe File Manager**
   ```bash
   chmod +x safe_file_manager.py
   sudo ln -s $(pwd)/safe_file_manager.py /usr/local/bin/sfm
   ```

2. **Set up basic aliases**
   ```bash
   echo "alias rm='sfm trash'" >> ~/.bashrc
   echo "alias mv='sfm move'" >> ~/.bashrc
   echo "alias cp='sfm copy'" >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Configure for your workflow**
   ```bash
   # For development
   export SAFE_FILE_GIT_AWARE=true
   export SAFE_FILE_VERIFY_CHECKSUM=true
   
   # For automation
   export SAFE_FILE_NONINTERACTIVE=1
   export SAFE_FILE_ASSUME_YES=1
   ```

4. **Start using gradually**
   - Begin with less critical operations
   - Build confidence with dry-run mode
   - Extend to more critical operations

Remember: The goal is to prevent data loss while maintaining productivity. Safe File Manager makes dangerous operations safe by default while still allowing you to work efficiently.