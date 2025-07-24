<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT Wrapper - Comprehensive Git Command Protection

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT Wrapper - Comprehensive Git Command Protection

## Overview
A wrapper around git that intercepts dangerous commands and redirects them to safe alternatives, while allowing normal safe commands to pass through.

## Dangerous Git Commands to Intercept

### Critical Data Loss Commands (Must Block)

1. **git reset --hard**
   - Loses uncommitted changes permanently
   - Redirect to: `safegit check-reset` then `safegit safe-reset`

2. **git clean** (all variations)
   - `-f`, `-fd`, `-fdx`, `-ffdx` - Permanently deletes untracked files
   - `-X` - Removes ignored files
   - Redirect to: `safegit check-clean` then `safegit safe-clean`

3. **git checkout -f / --force**
   - Overwrites uncommitted changes
   - Redirect to: `safegit check-checkout` then `safegit safe-checkout`

### History Rewriting Commands (Must Warn)

4. **git push --force** (all variations)
   - `--force`, `-f` - Can overwrite remote history
   - `--force-with-lease` - Safer but still dangerous
   - `--force-if-includes` - Still needs caution
   - Redirect to: `safegit check-push --force` then `safegit safe-push`

5. **git rebase** (interactive and regular)
   - `-i`, `--interactive` - Rewrites history
   - `--onto` - Complex history changes
   - Without `-i` on public branches
   - Redirect to: `safegit check-rebase` then `safegit safe-rebase`

6. **git filter-branch**
   - Extremely dangerous history rewriting
   - Redirect to: `safegit check-filter` with strong warnings

### Branch/Commit Destruction Commands

7. **git branch -D / --delete --force**
   - Force deletes branches with unique commits
   - Redirect to: `safegit check-branch-delete` then `safegit safe-branch-delete`

8. **git reset** (without --hard but still dangerous)
   - `--mixed` (default) - Unstages changes
   - `--soft` - Moves HEAD but keeps changes
   - Redirect to: `safegit check-reset --mode=mixed/soft`

### Other Risky Commands

9. **git gc --prune=now**
   - Permanently removes unreachable objects
   - Redirect to: `safegit check-gc` with safety analysis

10. **git checkout .** or **git checkout -- <path>**
    - Discards changes in working directory
    - Redirect to: `safegit check-checkout-path`

11. **git stash drop/clear**
    - Permanently removes stashed changes
    - Redirect to: `safegit check-stash-drop`

12. **git commit --amend** (on public commits)
    - Rewrites history
    - Redirect to: `safegit check-amend`

## Safe Commands to Pass Through

These commands are generally safe and should pass through:
- `git status`, `git log`, `git diff`
- `git add`, `git commit` (without --amend)
- `git pull`, `git fetch`
- `git push` (without force)
- `git branch` (listing)
- `git stash` (save/list)
- `git merge` (can be undone)
- `git tag`
- `git remote`
- `git config` (read operations)

## Wrapper Implementation Strategy

```bash
#!/bin/bash
# safegit wrapper

# Dangerous command patterns
DANGEROUS_PATTERNS=(
    "reset.*--hard"
    "clean.*-[fdxX]"
    "checkout.*(-f|--force)"
    "push.*--force"
    "rebase"
    "filter-branch"
    "branch.*-D"
    "gc.*--prune"
    "stash.*(drop|clear)"
    "commit.*--amend"
)

# Check if command matches dangerous patterns
check_dangerous_command() {
    local full_command="$*"
    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        if [[ "$full_command" =~ $pattern ]]; then
            return 0  # Dangerous
        fi
    done
    return 1  # Safe
}

# Main wrapper logic
if check_dangerous_command "$@"; then
    # Redirect to appropriate safe command
    redirect_to_safe_command "$@"
else
    # Pass through to regular git
    /usr/bin/git "$@"
fi
```

## Detailed Command Interception Rules

### 1. git reset
```bash
# Intercept these:
git reset --hard [<commit>]
git reset --hard HEAD~1
git reset --hard origin/main

# Redirect to:
safegit check-reset [files] && safegit safe-reset --mode=hard [files]

# Allow these:
git reset --soft HEAD~1  # (with warning)
git reset HEAD <file>    # (unstaging is safer)
```

### 2. git clean
```bash
# Intercept ALL variations:
git clean -f
git clean -fd
git clean -fdx
git clean -ffdx
git clean -X
git clean -i  # (still needs safety check)

# Redirect to:
safegit check-clean && safegit safe-clean --backup
```

### 3. git checkout
```bash
# Intercept these:
git checkout -f <branch>
git checkout --force
git checkout .
git checkout -- <file>
git checkout HEAD -- <file>

# Redirect to:
safegit check-checkout <target> && safegit safe-checkout <target>

# Allow these:
git checkout <branch>     # (without -f)
git checkout -b <branch>  # (creating new branch)
```

### 4. git push --force
```bash
# Intercept these:
git push --force
git push -f
git push --force-with-lease
git push --force-if-includes
git push origin +main  # (force push syntax)

# Redirect to:
safegit check-push --force && safegit safe-push --force

# Allow these:
git push
git push origin main
```

### 5. git rebase
```bash
# Intercept these:
git rebase -i HEAD~3
git rebase main
git rebase --onto <branch>
git rebase --continue  # (check for conflicts)

# Redirect to:
safegit check-rebase <args> && safegit safe-rebase <args>
```

### 6. git branch -D
```bash
# Intercept these:
git branch -D <branch>
git branch --delete --force <branch>

# Redirect to:
safegit check-branch-delete <branch> && safegit safe-branch-delete <branch>

# Allow these:
git branch -d <branch>  # (only if merged)
```

## Protection Levels

### Level 1: Warning Mode (Default)
- Shows warning for dangerous commands
- Requires confirmation
- Logs all dangerous operations

### Level 2: Redirect Mode
- Automatically redirects to safe alternatives
- No direct dangerous commands allowed
- Provides educational messages

### Level 3: Strict Mode
- Blocks all dangerous commands
- Must use safegit commands explicitly
- No bypass allowed

## Bypass Mechanism (Emergency Only)

```bash
# For experienced users who know the risks
SAFEGIT_BYPASS=1 git reset --hard HEAD~1

# Or with explicit unsafe mode
safegit unsafe git reset --hard HEAD~1
# This still logs the operation for audit
```

## Installation Strategy

```bash
# 1. Rename real git
sudo mv /usr/bin/git /usr/bin/git.real

# 2. Install safegit wrapper as git
sudo cp safegit /usr/bin/git
sudo chmod +x /usr/bin/git

# 3. Configure protection level
safegit config set protection.level redirect
safegit config set protection.educational true
```

## Educational Messages

When intercepting commands, show:
1. What the command would do
2. What data is at risk
3. Safer alternative command
4. Link to learn more

Example:
```
⚠️  DANGEROUS: git reset --hard HEAD~1

This would:
- Delete all uncommitted changes permanently
- Move HEAD back one commit
- Cannot be undone

Safer alternative:
  safegit safe-reset HEAD~1 --backup

Learn more: safegit help reset
```

## Audit and Logging

All intercepted commands should be logged:
- Timestamp
- Command attempted
- User
- Working directory
- Whether it was blocked/redirected/allowed
- Backup created (if any)

## Configuration

```bash
# Configure safegit behavior
safegit config set protection.level strict
safegit config set backup.automatic true
safegit config set education.verbose true
safegit config set audit.enabled true
safegit config set cleanup.protect "*.key,*.env,config.local"
```

This wrapper would provide comprehensive protection against the most common git mistakes while maintaining usability for safe operations.