<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT Commands Tool Proposal

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT Commands Tool Proposal

**Tool Name:** `safe_git_commands.py` (or `safegit.py` for short)

## Purpose
A comprehensive git safety tool that provides confidence in git operations by analyzing impact, suggesting safe alternatives, and preventing data loss.

## Core Features

### 1. File History & Analysis
```bash
# What happened to this file?
./safegit.py history file.java
  - Shows complete commit history
  - Highlights major changes (rewrites, renames, deletions)
  - Shows authors and change frequency
  
# What changed across versions?
./safegit.py changes file.java --last 5
  - Shows diffs across last N versions
  - Summarizes types of changes (refactoring vs feature additions)
  - Highlights breaking changes
```

### 2. Backup & Recovery
```bash
# Do we have backups in git?
./safegit.py find-backups file.java
  - Searches all branches for versions
  - Checks stashes
  - Looks in reflog for recently deleted versions
  
# Recover deleted file
./safegit.py recover deleted_file.java
  - Finds when file was deleted
  - Shows last version before deletion
  - Offers to restore with confirmation
```

### 3. Safe Reset Analysis
```bash
# Is it safe to reset this file?
./safegit.py check-reset file.java
  - Shows uncommitted changes that would be lost
  - Shows staged changes that would be unstaged  
  - Calculates "significance score" based on:
    - Lines changed
    - Time invested (first change timestamp)
    - Whether changes include TODOs/FIXMEs
  - Suggests: "High risk - 500 lines over 3 hours would be lost!"

# Safe reset with backup
./safegit.py safe-reset file.java --backup
  - Creates timestamped backup branch
  - Stashes current changes
  - Performs reset
  - Shows recovery instructions
```

### 4. Commit Impact Analysis
```bash
# Is it safe to undo/revert this commit?
./safegit.py analyze-commit abc123 --for-file file.java
  - Shows ALL files changed in that commit
  - Highlights if commit touches other critical files
  - Shows if other commits depend on this one
  - Risk assessment: "This commit also modifies 15 other files!"

# Check before revert
./safegit.py check-revert abc123
  - Simulates revert to show conflicts
  - Shows which files would be affected
  - Suggests safer alternatives (partial revert)
```

### 5. Interactive Safety Features
```bash
# Safe interactive operations
./safegit.py safe-rebase -i HEAD~3
  - Shows impact analysis before rebase
  - Creates safety branch
  - Provides undo instructions

# Safe force push
./safegit.py safe-push --force
  - Checks if others have pulled
  - Shows what commits would be lost on remote
  - Requires confirmation with summary
```

### 6. Blame & Ownership Analysis
```bash
# Who owns this code?
./safegit.py owners file.java --lines 100-150
  - Shows who wrote specific sections
  - Shows who last modified
  - Suggests reviewers based on history

# Find related changes
./safegit.py related file.java
  - Finds files often changed together
  - Shows coupling patterns
  - Helps identify impact of changes
```

### 7. Branch Safety
```bash
# Safe branch deletion
./safegit.py safe-delete-branch feature-x
  - Checks if fully merged
  - Shows unique commits that would be lost
  - Creates backup tag before deletion

# Branch analysis
./safegit.py branch-status feature-x
  - Shows divergence from main
  - Lists unmerged commits
  - Shows age and activity
```

### 8. Stash Management
```bash
# Smart stash with context
./safegit.py smart-stash "working on feature X"
  - Creates descriptive stash
  - Records branch context
  - Shows related stashes

# Find stashes
./safegit.py find-stash "feature X"
  - Searches stash messages
  - Shows stash contents preview
  - Indicates age and branch context
```

### 9. Conflict Prevention
```bash
# Check before merge
./safegit.py pre-merge feature-branch
  - Simulates merge without changing anything
  - Shows potential conflicts
  - Suggests resolution strategies

# Find conflicting changes
./safegit.py conflicts file.java --with main
  - Shows conflicting changes before they happen
  - Identifies problematic sections
  - Suggests who to coordinate with
```

### 10. Undo/Recovery Helper
```bash
# What can I undo?
./safegit.py undo --help
  - Shows recent operations from reflog
  - Provides specific undo commands
  - Explains impact of each undo

# Emergency recovery
./safegit.py emergency-recover
  - Guides through recovery options
  - Checks reflog, stashes, branches
  - Creates recovery branch with findings
```

## Safety Principles

1. **Non-destructive by default** - Never modifies without explicit confirmation
2. **Dry-run everything** - Show what would happen before doing it
3. **Automatic backups** - Create safety branches/tags before risky operations
4. **Clear risk communication** - Use color coding and risk scores
5. **Recovery instructions** - Always show how to undo operations
6. **Education mode** - Explain what git commands would be run

## Implementation Structure

```python
safe_git_commands.py
├── Core Modules:
│   ├── FileHistoryAnalyzer
│   ├── CommitImpactAnalyzer  
│   ├── SafetyChecker
│   ├── BackupManager
│   ├── ConflictPredictor
│   └── RecoveryHelper
├── Safety Features:
│   ├── Dry-run mode
│   ├── Confirmation prompts
│   ├── Automatic stashing
│   ├── Branch protection
│   └── Rollback tracking
└── Output Formats:
    ├── Interactive CLI
    ├── JSON for scripting
    ├── Markdown reports
    └── Visual diff displays
```

## Example Workflow

```bash
# Before making changes
./safegit.py status file.java --detailed
  ✓ File has uncommitted changes (50 lines)
  ⚠ Last commit was 30 days ago
  ℹ 3 developers have modified this file

# Check safety
./safegit.py check-reset file.java
  ⚠️ HIGH RISK: Reset would lose:
  - 500 lines of changes
  - 3 hours of work (since 9:00 AM)
  - Changes include 5 TODO markers
  
  Suggestion: Stash changes first:
  git stash save "file.java work in progress"

# Safe operation
./safegit.py safe-reset file.java --stash --backup
  ✓ Created stash: stash@{0} "file.java work in progress"
  ✓ Created backup branch: backup/file-java-2024-01-22-1430
  ✓ Reset file.java to HEAD
  
  To recover: 
  - From stash: git stash pop
  - From backup: git checkout backup/file-java-2024-01-22-1430 file.java
```

## Integration Ideas

- Alias common git commands to use safe versions
- Git hooks that call safety checks
- Integration with CI/CD for protected branches
- Team policies enforced through the tool
- Learning mode for git beginners

Would you like me to start implementing this tool with some of these core features?