<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

AI Safety Setup Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-24
Updated: 2025-07-24
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# AI Safety Setup Guide

**Related Code Files:**
- `safegit.py` - Safe git wrapper that intercepts dangerous commands
- `safe_file_manager.py` - Safe file operations with undo capability
- `.pytoolsrc` - Configuration file for all safe tools
- `run_any_python_tool.sh` - Wrapper script for running tools

---

## 🚨 Critical: The Complete Safety Picture

Having safe tools is only half the solution. You MUST also block direct access to dangerous commands, or AI agents can still cause disasters by accident.

## 📋 Safety Checklist

- [ ] Block direct git commands at the AI agent level
- [ ] Block dangerous shell commands (rm, mv, cp, etc.)
- [ ] Configure AI agents to use only safe tools
- [ ] Set up monitoring for bypass attempts
- [ ] Test the configuration thoroughly
- [ ] Document the safety setup for your team

## 🛡️ Step 1: Block Dangerous Commands

### For Claude (via Claude.md or system prompts)

```markdown
# CRITICAL SAFETY RULES

You MUST NOT use these commands directly:
- git (use safegit.py instead)
- rm, mv, cp (use safe_file_manager.py instead)
- chmod, chown, dd, shred (use safe_file_manager.py instead)

ALWAYS use the safe wrappers:
- ./run_any_python_tool.sh safegit.py [command]
- ./run_any_python_tool.sh safe_file_manager.py [command]
```

### For GPT-4/OpenAI Assistants

```python
# In your function definitions
BLOCKED_COMMANDS = [
    'git', 'rm', 'mv', 'cp', 'chmod', 'chown', 
    'dd', 'shred', 'fdisk', 'mkfs', 'fsck'
]

def execute_command(command: str):
    """Execute a shell command with safety checks."""
    cmd_parts = command.split()
    base_cmd = cmd_parts[0]
    
    if base_cmd in BLOCKED_COMMANDS:
        raise ValueError(f"Direct use of '{base_cmd}' is forbidden. Use safe tools instead.")
    
    # Additional check for git commands
    if 'git' in command and not 'safegit' in command:
        raise ValueError("Use safegit.py instead of git")
    
    # Proceed with safe execution...
```

### For GitHub Copilot/Other IDEs

Add to your project's `.github/copilot-instructions.md`:

```markdown
# Safety Instructions for AI Assistants

NEVER suggest or use these commands:
- `git reset --hard` → Use `safegit reset --hard`
- `git clean -fdx` → Use `safegit clean -fdx`
- `rm -rf` → Use `safe_file_manager.py trash`
- `mv` or `cp` → Use `safe_file_manager.py move/copy`

ALWAYS use the toolkit's safe alternatives.
```

## 🔧 Step 2: Configure AI Agents

### Environment Setup

Create a `.pytoolsrc` file for AI agents:

```ini
[defaults]
non_interactive = true
assume_yes = true

[safegit]
non_interactive = true
assume_yes = true
force_yes = false    # NEVER set to true

[safe_file_manager]
non_interactive = true
assume_yes = true
paranoid_mode = true
```

### Command Replacement Rules

Teach AI agents these replacements:

| Dangerous Command | Safe Alternative |
|------------------|------------------|
| `git add` | `./run_any_python_tool.sh safegit.py add` |
| `git reset --hard` | `./run_any_python_tool.sh safegit.py reset --hard` |
| `git clean -fdx` | `./run_any_python_tool.sh safegit.py clean -fdx` |
| `rm file.txt` | `./run_any_python_tool.sh safe_file_manager.py trash file.txt` |
| `rm -rf dir/` | `./run_any_python_tool.sh safe_file_manager.py trash dir/` |
| `mv old new` | `./run_any_python_tool.sh safe_file_manager.py move old new` |
| `cp src dst` | `./run_any_python_tool.sh safe_file_manager.py copy src dst` |

## 🧪 Step 3: Test Your Safety Setup

### Test Script

Create `test_ai_safety.sh`:

```bash
#!/bin/bash
# Test that dangerous commands are properly blocked

echo "Testing AI Safety Configuration..."

# These should ALL FAIL
test_commands=(
    "git reset --hard HEAD~1"
    "rm -rf test_dir"
    "mv important.txt /dev/null"
    "dd if=/dev/zero of=test.img"
)

for cmd in "${test_commands[@]}"; do
    echo "Testing: $cmd"
    # Your AI should refuse to execute this
    # Log the attempt for monitoring
done

echo "If any of the above succeeded, your safety config is BROKEN!"
```

### Verification Commands

Run these to verify safe tools are working:

```bash
# Verify safegit is intercepting
./run_any_python_tool.sh safegit.py --version

# Verify safe_file_manager is working
./run_any_python_tool.sh safe_file_manager.py --help

# Check configuration
./run_any_python_tool.sh common_config.py --show
```

## 📊 Step 4: Monitoring and Alerts

### Log Dangerous Attempts

Add logging to track when AI tries dangerous commands:

```python
# In your AI command executor
def log_safety_violation(command, ai_model, timestamp):
    """Log attempts to use dangerous commands."""
    with open('.ai_safety_log.json', 'a') as f:
        json.dump({
            'timestamp': timestamp,
            'ai_model': ai_model,
            'blocked_command': command,
            'action': 'blocked'
        }, f)
        f.write('\n')
```

### Set Up Alerts

```bash
# Monitor for safety violations
watch -n 60 'grep "blocked" .ai_safety_log.json | tail -20'
```

## 🎯 Step 5: Best Practices

### 1. Principle of Least Privilege

- AI agents should have minimal permissions
- Use read-only access where possible
- Require explicit approval for writes

### 2. Defense in Depth

```
Layer 1: AI Instructions (block at prompt level)
Layer 2: Function Guards (block in code)
Layer 3: Safe Tools (intercept dangerous operations)
Layer 4: System Permissions (OS-level restrictions)
Layer 5: Backups (when all else fails)
```

### 3. Regular Testing

- Test safety weekly
- Update blocking rules as new risks emerge
- Review AI command logs

### 4. Clear Documentation

Document for your team:
- Which commands are blocked
- How to use safe alternatives
- What to do if safety is bypassed

## 🚫 Common Mistakes to Avoid

### ❌ DON'T: Rely Only on Safe Tools

```python
# WRONG: Safe tools alone aren't enough
def execute(cmd):
    subprocess.run(cmd, shell=True)  # AI can still run 'git reset --hard'!
```

### ❌ DON'T: Allow Command Injection

```python
# WRONG: Allows injection
user_input = "file.txt; rm -rf /"
os.system(f"cat {user_input}")  # Disaster!
```

### ✅ DO: Block at Multiple Levels

```python
# CORRECT: Multiple safety layers
SAFE_COMMANDS = ['safegit', 'safe_file_manager', 'ls', 'cat', 'grep']

def execute(cmd):
    base_cmd = cmd.split()[0]
    
    # Layer 1: Whitelist check
    if base_cmd not in SAFE_COMMANDS:
        raise ValueError(f"Command '{base_cmd}' not in safe list")
    
    # Layer 2: Blacklist check
    if any(danger in cmd for danger in ['rm ', 'dd ', 'mkfs']):
        raise ValueError("Dangerous pattern detected")
    
    # Layer 3: Use safe tool
    if 'git' in cmd and 'safegit' not in cmd:
        cmd = cmd.replace('git', 'safegit')
    
    # Execute with limits
    subprocess.run(cmd, shell=False, timeout=60)
```

## 📚 Additional Resources

- [SAFEGIT_COMPREHENSIVE.md](docs/safegit/SAFEGIT_COMPREHENSIVE.md) - Complete SafeGIT documentation
- [SAFE_FILE_MANAGER_GUIDE.md](SAFE_FILE_MANAGER_GUIDE.md) - File operation safety
- [NON_INTERACTIVE_GUIDE.md](NON_INTERACTIVE_GUIDE.md) - Automation configuration

## 🆘 Getting Help

If you discover a safety gap:
1. Stop using the affected AI immediately
2. Document the issue
3. Report to: [your-safety-email@example.com]
4. Share with the community to help others

---

**Remember**: The time you spend on safety setup is nothing compared to the time you'll lose from a single disaster. Make safety your #1 priority!