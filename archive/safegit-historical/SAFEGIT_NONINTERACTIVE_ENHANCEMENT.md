<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT Non-Interactive Mode Enhancement

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT Non-Interactive Mode Enhancement

**Related Code Files:**
- `safegit.py` - Main wrapper requiring non-interactive support
- `safe_git_commands.py` - Core safety analysis engine
- `AI_AGENT_GIT_RULES.md` - AI automation guidance

---

## Current State Analysis

SafeGIT currently **lacks non-interactive support**, making it unsuitable for:
- CI/CD pipelines
- Automated scripts
- Batch operations
- AI agent usage in automated environments

### Current Interactive Prompts

SafeGIT requires manual input for:
1. **Typed confirmations**: `PROCEED`, `DELETE`, `MIRROR PUSH`, etc.
2. **Yes/No prompts**: `[Y/n]`, `[y/N]`
3. **Multiple choice**: `[1/2/3]`
4. **Branch name verification**: Type exact branch name
5. **Risk acknowledgments**: `I accept the risk`, `I understand the risks`

## Proposed Enhancement

### 1. Command-Line Flags

Add these flags to enable non-interactive usage:

```bash
# Skip all confirmations (dangerous operations still blocked)
safegit --yes <command>
safegit -y <command>

# Force dangerous operations without prompts (requires explicit flag)
safegit --force-yes <command>
safegit --assume-yes <command>

# Completely non-interactive (exit on any prompt)
safegit --non-interactive <command>
safegit --batch <command>
```

### 2. Environment Variables

Support environment-based configuration:

```bash
# Enable non-interactive mode
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1

# CI/CD detection
export CI=true  # Auto-detect CI environment
export SAFEGIT_CI_MODE=1

# Batch mode with specific responses
export SAFEGIT_BATCH_MODE=1
export SAFEGIT_DEFAULT_RESPONSE=yes
```

### 3. Configuration File

Support `.safegitrc` configuration:

```ini
[automation]
non_interactive = true
assume_yes = false
force_dangerous = false
default_response = no

[ci]
detect_ci_environment = true
ci_safe_defaults = true
```

## Implementation Examples

### Safe Non-Interactive Usage

```bash
# Safe operations proceed automatically
safegit --yes status
safegit --yes add file.txt
safegit --yes commit -m "message"

# Dangerous operations still require --force-yes
safegit --yes reset --hard  # Still blocked
safegit --force-yes reset --hard  # Proceeds with backup
```

### CI/CD Pipeline Usage

```yaml
# GitHub Actions
- name: Commit changes
  env:
    SAFEGIT_CI_MODE: 1
    SAFEGIT_ASSUME_YES: 1
  run: |
    safegit add .
    safegit commit -m "Automated commit"
    safegit push
```

### Batch Script Usage

```bash
#!/bin/bash
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_DEFAULT_RESPONSE=yes

# Process multiple repos
for repo in repo1 repo2 repo3; do
  cd $repo
  safegit pull
  safegit add -u
  safegit commit -m "Batch update"
  safegit push
done
```

## Safety Considerations

### 1. Graduated Risk Levels

```bash
# Level 1: Safe operations only
safegit --yes <safe-command>

# Level 2: Moderate risk with backups
safegit --yes --with-backups <moderate-command>

# Level 3: High risk requires explicit flag
safegit --force-yes --i-know-what-im-doing <dangerous-command>
```

### 2. Audit Trail

Non-interactive operations should:
- Log all operations to `.git/safegit-automation.log`
- Record who/what triggered automation
- Include timestamps and command details
- Show what safety checks were bypassed

### 3. Default Behaviors

```python
# Proposed defaults for non-interactive mode
NON_INTERACTIVE_DEFAULTS = {
    'reset_hard': 'deny',        # Always deny unless --force-yes
    'clean_fdx': 'backup_first', # Create backup then proceed
    'push_force': 'convert_to_lease',  # Auto-convert to safer option
    'stash_clear': 'backup_first',
    'gc_prune': 'use_grace_period',
    'commit_amend': 'check_pushed',
}
```

## Benefits

1. **CI/CD Integration**: SafeGIT can be used in automated pipelines
2. **Scripting Support**: Batch operations become possible
3. **AI Agent Safety**: AI can safely use git with protection
4. **Backwards Compatible**: Interactive mode remains default
5. **Configurable Safety**: Different levels for different needs

## Risks and Mitigations

### Risks:
- Users might blindly use `--force-yes` everywhere
- Automation might bypass important safety checks
- Loss of educational value from prompts

### Mitigations:
- Require explicit dangerous flags (`--force-yes --i-know-what-im-doing`)
- Log all automated operations
- Show summary of what was done
- Periodic reminders about safe practices

## Next Steps

1. **Implement basic --yes flag** for safe operations
2. **Add environment variable detection** for CI/CD
3. **Create configuration file support** for persistent settings
4. **Add comprehensive logging** for automated operations
5. **Update documentation** with automation examples

## Example Implementation Priority

```python
# Phase 1: Basic --yes support
if args.yes or os.environ.get('SAFEGIT_ASSUME_YES'):
    self.auto_confirm = True

# Phase 2: CI detection
if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
    self.ci_mode = True
    self.auto_confirm = True

# Phase 3: Graduated responses
if self.auto_confirm:
    if danger_level == 'low':
        return 'yes'
    elif danger_level == 'medium' and args.force_yes:
        return 'yes' 
    elif danger_level == 'high' and args.force_yes and args.i_know_what_im_doing:
        return 'yes'
    else:
        print(f"ERROR: Operation requires manual confirmation or additional flags")
        return 'no'
```

This enhancement would make SafeGIT suitable for both interactive safety education and automated workflows while maintaining appropriate safety levels.