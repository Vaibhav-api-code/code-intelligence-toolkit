<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT Context Flags - Environment-Aware Git Safety

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT Context Flags - Environment-Aware Git Safety

## Overview

Add environment/context flags to SafeGIT that persist across sessions and affect command safety levels based on current development phase.

## Context Flag Types

### 1. Environment Flags (Mutually Exclusive)
```bash
# Set the current environment
safegit context set-env development    # Normal development work
safegit context set-env staging        # Testing environment
safegit context set-env production     # Production environment
safegit context set-env hotfix         # Emergency fixes only
```

### 2. Work Mode Flags (Can Combine)
```bash
# Set current work mode
safegit context set-mode feature       # Working on new features
safegit context set-mode bugfix        # Fixing bugs
safegit context set-mode refactor      # Code refactoring
safegit context set-mode docs          # Documentation only
safegit context set-mode experiment    # Experimental work
```

### 3. Restriction Flags (Temporary)
```bash
# Set temporary restrictions
safegit context set-freeze on          # CODE FREEZE - No commits allowed
safegit context set-freeze off         # Normal operations

safegit context set-lockdown on        # EMERGENCY - Only hotfixes allowed
safegit context set-lockdown off       # Normal operations

safegit context set-release-prep on    # Preparing release - extra careful
safegit context set-release-prep off   # Normal operations
```

## Context Storage

### Location: `.git/safegit-context.json`
```json
{
  "environment": "production",
  "mode": ["bugfix"],
  "restrictions": {
    "code_freeze": true,
    "freeze_started": "2024-01-22T10:00:00Z",
    "freeze_reason": "Q4 release preparation",
    "lockdown": false,
    "release_prep": false
  },
  "metadata": {
    "last_updated": "2024-01-22T14:30:00Z",
    "updated_by": "john.doe",
    "project_phase": "pre-release"
  }
}
```

## Context-Aware Command Behavior

### 1. During CODE FREEZE
```bash
# Attempting any commit
safegit commit -m "new feature"
❌ BLOCKED: Code freeze is active since 2024-01-22
   Reason: Q4 release preparation
   Only documentation and hotfix commits allowed.
   
   To override (requires justification):
   safegit commit -m "message" --override-freeze "Critical security fix CVE-2024-123"
```

### 2. In PRODUCTION Environment
```bash
# Attempting dangerous commands
safegit reset --hard HEAD~1
❌ BLOCKED: Cannot use 'reset --hard' in PRODUCTION environment
   
   Allowed in production:
   - safegit log, status, diff
   - safegit cherry-pick (for hotfixes)
   - safegit tag (for releases)
   
   Switch to development: safegit context set-env development

# Force push attempt
safegit push --force
❌ CRITICAL: Force push FORBIDDEN in production environment
   No override available for this command in production.
```

### 3. In HOTFIX Mode
```bash
# Only critical changes allowed
safegit commit -m "Added new feature"
⚠️  WARNING: In HOTFIX mode - commit message doesn't indicate a fix
   
   Hotfix commits should:
   - Fix specific bugs
   - Include issue numbers
   - Be minimal in scope
   
   Continue anyway? [y/N]
```

### 4. During RELEASE PREP
```bash
# Extra confirmations required
safegit merge feature/new-ui
⚠️  CAUTION: Release preparation is active
   
   This merge will add:
   - 47 files changed
   - 2,341 lines added
   - 156 lines removed
   
   Have you:
   ✓ Run all tests?
   ✓ Updated documentation?
   ✓ Reviewed with team?
   
   Proceed with merge? [y/N]
```

## Implementation Details

### Context Manager Class
```python
class SafeGitContext:
    def __init__(self, repo_path):
        self.context_file = Path(repo_path) / '.git' / 'safegit-context.json'
        self.global_context_file = Path.home() / '.safegit' / 'global-context.json'
        self.context = self.load_context()
    
    def load_context(self):
        """Load context from file, with defaults."""
        default_context = {
            'environment': 'development',
            'mode': ['feature'],
            'restrictions': {
                'code_freeze': False,
                'lockdown': False,
                'release_prep': False
            }
        }
        # Load and merge repo-specific and global contexts
        
    def check_command_allowed(self, command, args):
        """Check if command is allowed in current context."""
        # Return (allowed, reason, suggestions)
        
    def get_safety_level(self):
        """Get current safety level based on context."""
        if self.context['environment'] == 'production':
            return 'MAXIMUM'
        elif self.context['restrictions']['code_freeze']:
            return 'HIGH'
        elif self.context['environment'] == 'staging':
            return 'MEDIUM'
        else:
            return 'NORMAL'
```

### Enhanced Command Interception
```python
def run(self, args: List[str]) -> int:
    # Load context
    context = SafeGitContext(os.getcwd())
    
    # Check if command is allowed in current context
    allowed, reason, suggestions = context.check_command_allowed(command, args)
    
    if not allowed:
        print(f"❌ BLOCKED: {reason}")
        if suggestions:
            print(f"\n💡 Suggestions:\n{suggestions}")
        return 1
    
    # Show context warnings
    self._show_context_warnings(context)
    
    # Continue with normal interception logic...
```

## Command Rules by Context

### PRODUCTION Environment
```python
PRODUCTION_RULES = {
    'forbidden': [
        'reset --hard',
        'clean',
        'rebase',
        'filter-branch',
        'push --force*',
        'branch -D'
    ],
    'restricted': [
        'merge',      # Requires extra confirmation
        'commit',     # Only hotfixes with proper message
        'cherry-pick' # Only from approved branches
    ],
    'allowed': [
        'status', 'log', 'diff', 'fetch', 'tag', 'show'
    ]
}
```

### CODE FREEZE Restrictions
```python
CODE_FREEZE_RULES = {
    'forbidden': [
        'merge feature/*',
        'rebase',
        'commit' # Unless --override-freeze with reason
    ],
    'restricted': [
        'cherry-pick',  # Only critical fixes
        'push'          # Requires freeze override
    ],
    'allowed': [
        'commit' # Only if message contains: fix, hotfix, revert, docs
    ]
}
```

## Context Commands

### Setting Context
```bash
# Set environment
safegit context set-env production
✅ Environment set to: PRODUCTION
⚠️  Warning: Dangerous commands are now restricted

# Set work mode
safegit context set-mode bugfix
✅ Work mode set to: bugfix
📌 Reminder: Keep commits focused on bug fixes

# Enable code freeze
safegit context set-freeze on --reason "Q4 release prep"
✅ CODE FREEZE enabled
🔒 Only critical fixes and documentation updates allowed
```

### Viewing Context
```bash
# Show current context
safegit context show

Current Context:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Environment:     🚨 PRODUCTION
Work Mode:       🐛 bugfix
Code Freeze:     🔒 ACTIVE (4 hours ago)
  Reason:        Q4 release preparation
Safety Level:    MAXIMUM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Restrictions in effect:
- No force operations allowed
- No history rewriting allowed  
- Commits must be fixes only
- All merges require approval
```

### Context History
```bash
# Show context changes
safegit context history

Context History:
2024-01-22 14:30:00 - Code freeze enabled by john.doe
2024-01-22 10:00:00 - Environment changed to production by jane.smith
2024-01-21 16:45:00 - Work mode set to bugfix by john.doe
```

## Smart Warnings Based on Context

### Example: Commit in Different Contexts

**In Development + Feature Mode:**
```bash
safegit commit -m "Added new dashboard"
✅ Committing in development environment...
```

**In Production + Bugfix Mode:**
```bash
safegit commit -m "Added new dashboard"
⚠️  WARNING: In PRODUCTION + bugfix mode
   This commit message suggests new features, not bug fixes.
   
   Production commits should:
   - Fix specific issues
   - Include ticket numbers
   - Be minimal in scope
   
   Continue? [y/N]
```

**During Code Freeze:**
```bash
safegit commit -m "Added new dashboard"
❌ BLOCKED: Code freeze is active
   
   To commit during freeze, one of these is required:
   1. Message must start with: [HOTFIX], [CRITICAL], or [DOCS]
   2. Use --override-freeze flag with justification
   
   Example:
   safegit commit -m "[HOTFIX] Fix login crash" 
```

## Integration with CI/CD

### Automatic Context from CI Environment
```bash
# CI/CD can set context automatically
if [ "$CI_ENVIRONMENT" = "production" ]; then
    safegit context set-env production --ci-automated
fi

if [ "$CI_RELEASE_PHASE" = "freeze" ]; then
    safegit context set-freeze on --reason "Automated by CI"
fi
```

### Context Enforcement in CI
```yaml
# .github/workflows/safety.yml
- name: Enforce SafeGIT Context
  run: |
    safegit context verify
    if [ $? -ne 0 ]; then
      echo "Context verification failed"
      exit 1
    fi
```

## Benefits

1. **Prevents Accidents**: Can't force-push to production by mistake
2. **Enforces Process**: Code freeze actually prevents commits
3. **Clear Communication**: Everyone knows current project phase
4. **Audit Trail**: Track who changed context and when
5. **Flexible Override**: Emergency overrides with justification
6. **Team Awareness**: Context visible to entire team

## Migration and Adoption

### Phase 1: Optional Warnings
- Context provides warnings but doesn't block
- Team gets used to checking context

### Phase 2: Soft Enforcement  
- Dangerous commands blocked in production
- Code freeze provides strong warnings

### Phase 3: Full Enforcement
- All context rules enforced
- Override requires justification
- Full audit trail

This context system would make git operations much safer by being aware of the current development phase and preventing inappropriate operations automatically.