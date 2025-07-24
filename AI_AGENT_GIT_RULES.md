<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

AI Agent Git Safety Rules

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# AI Agent Git Safety Rules

**Version**: 2.0 (with Non-Interactive Support)  
**Last Updated**: January 23, 2025

## Critical Rule: NEVER Use Direct Git Commands

To prevent catastrophic data loss incidents like the Replit AI disaster, these rules MUST be enforced:

### 1. Mandatory SafeGIT Usage

**RULE**: AI agents MUST use `safegit` wrapper instead of direct `git` commands.

```bash
# ❌ FORBIDDEN - Direct git usage
git reset --hard HEAD~1
git clean -fdx
git push --force

# ✅ REQUIRED - SafeGIT wrapper usage  
safegit reset --hard HEAD~1
safegit clean -fdx
safegit push --force
```

### 1.1 Non-Interactive Mode for AI Agents (NEW)

AI agents can now operate safely in automated environments using SafeGIT's non-interactive mode:

```bash
# For CI/CD and automated workflows
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1

# Safe operations proceed automatically
safegit add .
safegit commit -m "AI-generated commit"
safegit push

# Dangerous operations still blocked without explicit flag
safegit reset --hard  # ❌ Will fail - requires --force-yes
```

### 2. Blocked Commands

The following commands are COMPLETELY FORBIDDEN, even with safegit:

```bash
# ❌ NEVER ALLOW THESE:
rm -rf .git              # Destroys repository
git filter-branch        # Can corrupt entire history
git reflog expire --all  # Removes all recovery options
```

### 3. Required Confirmations

For these operations, AI MUST:
1. Explain what will happen
2. List what data might be lost
3. Wait for explicit user confirmation

```bash
# Operations requiring explicit confirmation:
- safegit reset --hard
- safegit clean (any variation)
- safegit push --force
- safegit rebase
- safegit branch -D
```

### 4. Automatic Safety Measures

AI agents MUST automatically:

```bash
# Before any potentially destructive operation:
1. Run: safegit status
2. Show uncommitted changes to user
3. Suggest creating backup: safegit stash save "AI backup before <operation>"
4. Only proceed after confirmation
```

### 5. Safe Command Whitelist

These commands can be used without special confirmation:

```bash
safegit status
safegit log
safegit diff
safegit add <specific files>
safegit commit -m "message"
safegit pull
safegit fetch
safegit branch (listing only)
safegit stash save
safegit merge (without --strategy=ours)
```

#### 5.1 Automated Safe Commands (with --yes or environment variables)

```bash
# With flag
safegit --yes add .
safegit --yes commit -m "Automated commit"
safegit --yes pull

# With environment variable
export SAFEGIT_ASSUME_YES=1
safegit add .
safegit commit -m "CI/CD commit"
safegit push
```

### 6. Pre-Operation Checks

Before ANY git operation, AI MUST:

```python
# Pseudo-code for AI logic
def before_git_operation(command):
    # 1. Check if using safegit
    if not command.startswith('safegit'):
        raise Error("Direct git usage forbidden - use safegit")
    
    # 2. Check if command is dangerous
    if is_dangerous_command(command):
        # 3. Show current state
        run("safegit status")
        
        # 4. Explain risks
        explain_risks(command)
        
        # 5. Get confirmation
        if not get_user_confirmation():
            abort_operation()
    
    # 6. Log operation
    log_ai_git_operation(command)
```

### 7. Recovery Protocol

If AI accidentally runs a dangerous command:

```bash
1. IMMEDIATELY STOP all operations
2. Run: safegit status
3. Check: safegit log --oneline -10
4. Report: "I may have made an error with git. Here's the current state..."
5. Suggest: "Run 'safegit stats' to see what I did"
```

### 8. Education Mode

AI should educate users about git safety:

```bash
# When user requests dangerous operation:
User: "Delete all untracked files"
AI: "I'll use 'safegit clean' which will:
     1. Show what files would be deleted
     2. Create a backup before deleting
     3. Give you recovery instructions
     
     This is safer than 'git clean -fdx' which permanently deletes files.
     Shall I proceed?"
```

## Implementation for AI Systems

### For OpenAI Function Calling / Tools:

```python
@tool
def run_git_command(command: str, auto_confirm: bool = False) -> str:
    """Run a git command safely using safegit wrapper."""
    if command.startswith('git '):
        raise ValueError("Direct git commands are forbidden. Use 'safegit' instead.")
    
    if not command.startswith('safegit '):
        command = f'safegit {command}'
    
    # Add non-interactive flags for automation
    if auto_confirm:
        # Check if dangerous
        dangerous_patterns = ['reset.*--hard', 'clean.*-f', 'push.*--force', 'branch.*-D']
        is_dangerous = any(re.search(p, command) for p in dangerous_patterns)
        
        if is_dangerous:
            # Dangerous operations need explicit approval even in auto mode
            return "DANGEROUS_COMMAND_NEEDS_MANUAL_APPROVAL: " + command
        else:
            # Safe operations can use --yes
            command = command.replace('safegit ', 'safegit --yes ', 1)
    
    # Set environment for non-interactive mode
    env = os.environ.copy()
    if auto_confirm:
        env['SAFEGIT_NONINTERACTIVE'] = '1'
        env['SAFEGIT_ASSUME_YES'] = '1'
    
    # Run command
    result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
    
    if result.returncode != 0 and 'requires --force-yes' in result.stderr:
        return f"BLOCKED_DANGEROUS_OPERATION: {command}\nSafeGIT prevented potential data loss. Manual confirmation required."
    
    return result.stdout + result.stderr
```

### For LangChain/Other Frameworks:

```python
class SafeGitTool(BaseTool):
    name = "safegit"
    description = "Run git commands safely with automatic protection"
    
    def _run(self, command: str, auto_mode: bool = False) -> str:
        # Enforce safegit usage
        if command.startswith('git '):
            return "ERROR: Direct git forbidden. Use format: 'safegit <command>'"
        
        # Auto-prepend safegit if needed
        if not command.startswith('safegit '):
            command = f'safegit {command}'
        
        # Configure for automation if requested
        env = os.environ.copy()
        if auto_mode:
            env['SAFEGIT_NONINTERACTIVE'] = '1'
            env['SAFEGIT_ASSUME_YES'] = '1'
            
            # Check for dangerous operations
            if any(pattern in command for pattern in ['reset', 'clean', 'force', '-D']):
                return f"SAFETY_BLOCK: Command '{command}' is too dangerous for auto-mode. Requires manual review."
        
        # Execute with safety wrapper
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            env=env
        )
        
        if result.returncode != 0:
            return f"SafeGIT prevented operation: {result.stderr}"
            
        return result.stdout
```

## CI/CD and Automated Workflow Guidelines

### Safe Automation Patterns

```yaml
# GitHub Actions Example
- name: AI-Safe Git Operations
  env:
    SAFEGIT_NONINTERACTIVE: '1'
    SAFEGIT_ASSUME_YES: '1'
  run: |
    # Safe operations proceed automatically
    safegit add .
    safegit commit -m "AI: Updated documentation"
    safegit push
    
    # Dangerous operations still blocked
    # safegit reset --hard  # This will fail without --force-yes
```

### Dangerous Operations Require Explicit Approval

Even in CI/CD, dangerous operations should require manual workflow approval:

```yaml
# Require manual approval for dangerous operations
- name: Dangerous Operation
  if: github.event.inputs.allow_dangerous == 'true'
  env:
    SAFEGIT_FORCE_YES: '1'  # Only set when explicitly approved
  run: |
    safegit reset --hard ${{ github.event.inputs.target }}
```

## Monitoring and Compliance

1. **Log all git operations** to `.git/safegit-log.json` (automatic)
2. **Track automation mode** - logs show `"mode": "non-interactive"`
3. **Alert on direct git usage** attempts
4. **Track dangerous command frequency**
5. **Regular safety audits** of AI git usage
6. **CI environment detection** - logs show `"ci_detected": true`

## Remember: The Replit Incident

The Replit AI deleted an entire production database during a code freeze. This happened because:
- No safety checks on dangerous commands
- Direct access to destructive operations
- No confirmation before irreversible actions

SafeGIT prevents this by:
- Intercepting dangerous commands
- Creating automatic backups
- Requiring explicit confirmation
- Providing recovery options

**ENFORCE THESE RULES TO PREVENT AI DISASTERS**