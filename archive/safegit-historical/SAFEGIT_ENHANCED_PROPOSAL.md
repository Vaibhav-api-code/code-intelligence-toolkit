<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Enhanced SafeGIT Commands Tool - Based on Common Git Mistakes Research

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Enhanced SafeGIT Commands Tool - Based on Common Git Mistakes Research

## Critical Git Mistakes Discovered

Based on web research, the most dangerous and common git mistakes are:

1. **`git reset --hard`** - Permanently loses uncommitted changes
2. **`git clean -f`** - Permanently deletes untracked files (bypasses recycle bin!)
3. **`git checkout .`** - Overwrites uncommitted changes in tracked files
4. **`git clean -fdx`** - Nuclear option that deletes EVERYTHING untracked
5. **Force operations without understanding impact**
6. **Not realizing IDE/editor history might be the only recovery option**

## New Critical Features to Add

### 1. Safe Clean Command (HIGHEST PRIORITY)
```bash
# Check what would be deleted
./safegit.py check-clean
  - Shows all untracked files that would be deleted
  - Categorizes by type (source code, configs, logs, etc.)
  - Shows file sizes and creation dates
  - Warns about files that look important (by extension/content)
  - ALWAYS does dry-run first

# Safe clean with automatic backup
./safegit.py safe-clean --backup-first
  - Creates zip backup of all untracked files first
  - Names it: SAFEGIT-CLEAN-BACKUP-{timestamp}.zip
  - Shows recovery instructions
  - Then performs the clean

# Interactive clean
./safegit.py safe-clean --interactive
  - Shows each file with preview
  - Allows selective deletion
  - Groups by directory for bulk decisions
```

### 2. Pre-Operation Safety Snapshot
```bash
# Create safety snapshot before ANY dangerous operation
./safegit.py snapshot create "before major refactoring"
  - Creates lightweight backup branch
  - Stashes all changes (tracked and untracked)
  - Creates zip of untracked files
  - Tags with timestamp and message
  - Returns snapshot ID for easy recovery

# List snapshots
./safegit.py snapshot list
  - Shows all safety snapshots
  - Indicates what was preserved
  - Shows age and size

# Restore from snapshot
./safegit.py snapshot restore SNAP-20240122-143052
  - Restores complete working state
  - Including untracked files
```

### 3. Safe Checkout Protection
```bash
# Check before checkout
./safegit.py check-checkout feature-branch
  - Shows what files would be overwritten
  - Highlights uncommitted changes that would be lost
  - Warns about conflicts
  - Suggests stashing if needed

# Safe checkout with auto-stash
./safegit.py safe-checkout feature-branch
  - Auto-stashes changes if needed
  - Performs checkout
  - Attempts to reapply stash
  - Handles conflicts gracefully
```

### 4. Recovery Assistant
```bash
# Help recover lost work
./safegit.py recover --wizard
  - Checks git reflog for recent commits
  - Runs git fsck for dangling objects
  - Checks stashes for forgotten work
  - Looks for IDE backup files (.swp, ~, etc.)
  - Checks OS temp directories
  - Provides step-by-step recovery instructions

# Recover deleted untracked files (best effort)
./safegit.py recover-untracked
  - Checks IDE history (IntelliJ, VSCode, etc.)
  - Looks for editor swap files
  - Checks OS recycle bin/trash
  - Scans for backup files
```

### 5. Smart Stash Management
```bash
# Create descriptive stash with metadata
./safegit.py smart-stash "working on feature X"
  - Includes branch name in stash
  - Records file count and sizes
  - Tags with timestamp
  - Can include untracked files

# Find and preview stashes
./safegit.py stash-search "feature X"
  - Search stash messages
  - Show file lists
  - Preview changes
  - Show age and branch context
```

### 6. Danger Mode Protection
```bash
# Protect against accidental dangerous commands
./safegit.py protect enable
  - Creates git aliases that redirect dangerous commands
  - git reset --hard → safegit safe-reset
  - git clean -f → safegit safe-clean
  - Shows warning and requires confirmation

# Check current protection status
./safegit.py protect status
  - Shows which commands are protected
  - Lists recent near-misses
  - Suggests safer alternatives
```

### 7. Untracked Files Monitor
```bash
# Monitor important untracked files
./safegit.py monitor add "*.key" "config.local"
  - Tracks important untracked file patterns
  - Warns before operations that would delete them
  - Suggests adding to .gitignore

# Show monitoring status
./safegit.py monitor status
  - Lists monitored patterns
  - Shows current untracked files at risk
  - Suggests which files might need committing
```

### 8. Operation History & Undo
```bash
# Show recent safegit operations
./safegit.py history
  - Shows all safegit operations with timestamps
  - Indicates what was backed up
  - Shows available recovery points

# Undo last operation
./safegit.py undo
  - Intelligently undoes the last safegit operation
  - Restores from appropriate backup
  - Shows what was restored
```

## Implementation Priority (Based on Research)

1. **Safe Clean** - Most destructive command with NO recovery
2. **Snapshot System** - Universal safety net for all operations  
3. **Safe Reset Enhancement** - Already started, needs completion
4. **Recovery Assistant** - Helps when prevention fails
5. **Safe Checkout** - Common source of lost work
6. **Protection Mode** - Prevents accidents at the source
7. **Smart Stash** - Better stash management prevents need for dangerous operations
8. **Monitor & History** - Long-term safety improvements

## Key Insights from Research

1. **"git clean -f" is the most dangerous** - No recovery possible through git
2. **IDEs are often the only recovery option** - Tool should check IDE history
3. **Stashing is underused** - People use reset/clean when stash would be safer
4. **Dry-run is critical** - Always show what will happen before doing it
5. **Untracked files need special protection** - Git doesn't help with these at all
6. **Recovery is possible more often than people think** - Need better tooling

## Safety Principles Update

1. **Always create recoverable backups** - Especially for untracked files
2. **Make dry-run mandatory** - Don't allow skipping preview
3. **Use clear naming** - "SAFEGIT-BACKUP-CLEAN" vs generic "backup"
4. **Educate while protecting** - Show WHY operations are dangerous
5. **Progressive disclosure** - Simple commands with advanced options
6. **Recovery-first mindset** - Always provide undo/recovery path