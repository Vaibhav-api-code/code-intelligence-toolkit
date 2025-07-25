# Tool Synchronization Guide

**Related Code Files:**
- `sync_tools_to_desktop.py` - Main synchronization script
- `.sync_log.json` - Sync history tracking (created in destination)

---

## Overview

The `sync_tools_to_desktop.py` script provides intelligent synchronization between your main code-intelligence-toolkit repository and a separate copy on your Desktop. This is useful when you have two separate git repositories and want to keep the tools synchronized without manual copying.

## Features

- **Smart Detection**: Only syncs files that have actually changed (using MD5 hashing)
- **Git Awareness**: Warns about uncommitted changes in the destination repository
- **Selective Sync**: Syncs Python tools, shell scripts, config files, and documentation
- **Safe Operation**: Creates backups of modified files before overwriting
- **History Tracking**: Maintains a log of all sync operations
- **Dry Run Mode**: Preview changes before applying them
- **Force Mode**: Override safety checks when needed

## Installation

1. The script is already created in your main repository
2. Make it executable:
   ```bash
   chmod +x sync_tools_to_desktop.py
   ```

## Usage

### Basic Sync
From your main repository directory:
```bash
./sync_tools_to_desktop.py
```

### Dry Run (Preview Changes)
```bash
./sync_tools_to_desktop.py --dry-run
```

### Force Sync (Override Warnings)
```bash
./sync_tools_to_desktop.py --force
```

### Custom Paths
```bash
./sync_tools_to_desktop.py --source /path/to/source --dest /path/to/destination
```

## What Gets Synced

### Included:
- All Python files (`*.py`)
- Shell scripts (`*.sh`, including `run_any_python_tool.sh`)
- Configuration files (`.pytoolsrc*`)
- Documentation (`*.md`)

### Excluded:
- Git directories (`.git`)
- Python cache (`__pycache__`, `*.pyc`)
- macOS files (`.DS_Store`)
- The sync script itself
- Sync history (`.sync_log.json`)

## Workflow Example

1. **Make changes in main repository**:
   ```bash
   cd ~/DemoStrategies/Strategies/code-intelligence-toolkit
   # Edit tools, fix bugs, add features
   git add .
   git commit -m "Enhanced tool features"
   ```

2. **Sync to desktop**:
   ```bash
   ./sync_tools_to_desktop.py
   ```

3. **Review and commit in desktop repo**:
   ```bash
   cd ~/Desktop/code-intelligence-toolkit
   git status
   git add -u  # Modified files
   git add .   # New files
   git commit -m "Sync tools from main repository"
   ```

## Safety Features

### Modification Detection
The script checks for uncommitted changes in the destination repository and warns you:
```
⚠️  WARNING: Desktop repository has local modifications:
  Modified files:
    - tool1.py
    - tool2.py
    
Proceed with sync? (y/N/force):
```

### Backup Creation
Modified files are backed up before overwriting:
- Original: `tool.py`
- Backup: `tool.py.backup`

### Sync History
A `.sync_log.json` file tracks all sync operations:
```json
{
  "syncs": [
    {
      "timestamp": "2025-07-25T10:30:45",
      "files_synced": 15,
      "total_files": 15
    }
  ],
  "file_hashes": {
    "tool1.py": "abc123...",
    "tool2.py": "def456..."
  }
}
```

## Advanced Usage

### Automated Sync Script
Create a shell script for regular syncing:
```bash
#\!/bin/bash
# sync_and_commit.sh

# Sync tools
./sync_tools_to_desktop.py --force

# Auto-commit in desktop repo
cd ~/Desktop/code-intelligence-toolkit
if [[ $(git status --porcelain) ]]; then
    git add .
    git commit -m "Auto-sync from main repository $(date +%Y-%m-%d)"
    echo "✅ Synced and committed"
else
    echo "✅ No changes to sync"
fi
```

### Git Hooks Integration
Add to `.git/hooks/post-commit` in main repo:
```bash
#\!/bin/bash
echo "🔄 Syncing to desktop repository..."
./sync_tools_to_desktop.py --dry-run
```

## Troubleshooting

### "Destination directory does not exist"
Create the desktop repository first:
```bash
mkdir -p ~/Desktop/code-intelligence-toolkit
cd ~/Desktop/code-intelligence-toolkit
git init
```

### Permission Errors
Ensure the sync script is executable:
```bash
chmod +x sync_tools_to_desktop.py
```

### Hash Mismatch Issues
Clear the sync history to force re-sync:
```bash
rm ~/Desktop/code-intelligence-toolkit/.sync_log.json
./sync_tools_to_desktop.py
```

## Best Practices

1. **Commit Before Syncing**: Always commit changes in both repositories before syncing
2. **Review Changes**: Use `--dry-run` to preview what will be synced
3. **Regular Syncs**: Sync frequently to avoid large divergences
4. **Document Changes**: Keep commit messages descriptive in both repositories
5. **Test After Sync**: Run key tools after syncing to ensure everything works

## Integration with Development Workflow

### Recommended Workflow:
1. Primary development in main repository
2. Test thoroughly
3. Commit changes
4. Sync to desktop
5. Test in desktop environment
6. Commit in desktop repository

### For Hotfixes in Desktop:
1. Make urgent fix in desktop repository
2. Commit the fix
3. Manually port important changes back to main repository
4. Resume normal sync flow

## Future Enhancements

Potential improvements for the sync tool:
- Bidirectional sync support
- Exclude list configuration file
- Sync specific file patterns only
- Integration with git operations
- Conflict resolution strategies
