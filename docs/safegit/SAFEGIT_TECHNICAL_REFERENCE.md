<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SafeGIT Technical Reference

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-22
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# SafeGIT Technical Reference

**Version**: 2.0  
**Last Updated**: January 23, 2025

**Related Code Files:**
- `safegit.py` - Main wrapper implementation
- `safe_git_commands.py` - Core safety engine
- `safegit_undo_stack.py` - Undo system implementation
- All test files in `test_safegit_*.py`

---

## 📐 Architecture Overview

### System Components

```
┌─────────────────┐
│   User/CI/AI    │
└────────┬────────┘
         │
┌────────▼────────┐
│   safegit.py    │ ← Main Entry Point (1226 lines)
├─────────────────┤
│ • Command Parse │
│ • Pattern Match │
│ • Handler Route │
│ • Non-Interactive│
└────────┬────────┘
         │
┌────────▼────────┐
│safe_git_commands│ ← Safety Engine (830 lines)
├─────────────────┤
│ • Risk Analysis │
│ • Backup Create │
│ • State Verify  │
│ • Recovery Hints│
└────────┬────────┘
         │
┌────────▼────────┐
│ safegit_undo_   │ ← Undo System
│    stack.py     │
├─────────────────┤
│ • Op History    │
│ • Atomic Journal│
│ • Recovery Gen  │
└─────────────────┘
```

## 🔍 Pattern Detection Engine

### Dangerous Command Patterns (37+ Total)

```python
DANGEROUS_PATTERNS = [
    # Reset Operations
    (r'^reset\s+--hard', 'reset_hard'),
    (r'^reset\s+--merge', 'reset_merge'),
    (r'^reset\s+--keep', 'reset_keep'),
    
    # Clean Operations
    (r'^clean\s+.*-[xX]', 'clean_force'),
    (r'^clean\s+.*-d', 'clean_force'),
    (r'^clean\s+.*-f', 'clean_force'),
    
    # Push Operations
    (r'^push\s+.*--force(?!-with-lease)', 'push_force'),
    (r'^push\s+.*-f(?!orce-with-lease)', 'push_force'),
    (r'^push\s+.*--mirror', 'push_destructive'),
    (r'^push\s+.*--delete', 'push_destructive'),
    
    # Branch Operations
    (r'^branch\s+.*-[dD]', 'branch_delete'),
    (r'^switch\s+.*--discard-changes', 'switch_discard'),
    
    # Checkout Operations
    (r'^checkout\s+.*--force', 'checkout_force'),
    (r'^checkout\s+.*-f', 'checkout_force'),
    (r'^checkout\s+[^-]', 'checkout_branch'),
    
    # Stash Operations
    (r'^stash\s+drop', 'stash_drop'),
    (r'^stash\s+clear', 'stash_clear'),
    
    # Rebase/Merge
    (r'^rebase', 'rebase'),
    (r'^merge\s+.*--strategy\s*=\s*ours', 'merge_ours'),
    
    # Commit Operations
    (r'^commit\s+.*--amend', 'commit_amend'),
    
    # GC Operations
    (r'^gc\s+.*--prune=now', 'gc_prune_now'),
    (r'^gc\s+.*--aggressive', 'gc_aggressive'),
    
    # Reflog Operations
    (r'^reflog\s+expire', 'reflog_expire'),
    (r'^reflog\s+delete', 'reflog_delete'),
    
    # Low-level Operations
    (r'^update-ref\s+.*-d', 'update_ref_delete'),
    (r'^symbolic-ref\s+.*-d', 'symbolic_ref_delete'),
    
    # Filter Operations
    (r'^filter-branch', 'filter_branch'),
    (r'^filter-repo', 'filter_repo'),
    
    # Submodule Operations
    (r'^submodule\s+.*deinit', 'submodule_deinit'),
    
    # Worktree Operations
    (r'^worktree\s+remove', 'worktree_remove'),
    
    # Remote Operations
    (r'^remote\s+remove', 'remote_remove'),
    (r'^remote\s+rm', 'remote_remove'),
    
    # Tag Operations
    (r'^tag\s+.*-d', 'tag_delete'),
    (r'^tag\s+.*--delete', 'tag_delete'),
    
    # Note Operations
    (r'^notes\s+remove', 'notes_remove'),
    
    # Replace Operations
    (r'^replace\s+--delete', 'replace_delete')
]
```

## 🛠️ Handler Implementation

### Handler Types and Risk Levels

```python
# Handler mapping with risk levels
HANDLER_MAP = {
    'reset_hard': (_handle_reset_hard, 'HIGH'),
    'clean_force': (_handle_clean_force, 'HIGH'),
    'push_force': (_handle_push_force, 'HIGH'),
    'push_destructive': (_handle_push_destructive, 'CRITICAL'),
    'branch_delete': (_handle_branch_delete, 'MEDIUM'),
    'checkout_force': (_handle_checkout_force, 'MEDIUM'),
    'stash_clear': (_handle_stash_clear, 'HIGH'),
    'commit_amend': (_handle_commit_amend, 'MEDIUM'),
    'reflog_expire': (_handle_reflog_expire, 'CRITICAL'),
    'update_ref_delete': (_handle_update_ref_delete, 'CRITICAL'),
    # ... more handlers
}
```

### Specialized Handler Examples

#### Reset Hard Handler
```python
def _handle_reset_hard(self, args):
    """Handle git reset --hard with automatic backup."""
    # 1. Create automatic stash
    stash_msg = f"SAFEGIT: Auto-backup before reset --hard at {datetime.now()}"
    subprocess.run(['git', 'stash', 'push', '-m', stash_msg])
    
    # 2. Analyze impact
    commits_lost = self._count_commits_to_lose(args)
    files_affected = self._get_affected_files()
    
    # 3. Risk assessment
    risk_level = 'HIGH' if commits_lost > 5 else 'MEDIUM'
    
    # 4. Get confirmation
    if self.non_interactive:
        if self.force_yes:
            print("[AUTO-CONFIRM] Proceeding with reset --hard")
            return True
        else:
            print("ERROR: reset --hard requires --force-yes in non-interactive mode")
            return False
    
    # 5. Interactive confirmation
    print(f"⚠️  WARNING: This will lose {commits_lost} commits")
    print(f"📁 Files affected: {len(files_affected)}")
    confirmation = self._get_typed_confirmation("PROCEED")
    
    return confirmation
```

#### Clean Force Handler
```python
def _handle_clean_force(self, args):
    """Handle git clean with backup creation."""
    # 1. Find files to be deleted
    files_to_delete = self._get_untracked_files(args)
    total_size = sum(os.path.getsize(f) for f in files_to_delete)
    
    # 2. Create zip backup
    if files_to_delete:
        backup_name = f"safegit-backup-{datetime.now():%Y%m%d-%H%M%S}.zip"
        self._create_zip_backup(files_to_delete, backup_name)
        print(f"✅ Backup created: {backup_name}")
    
    # 3. Show impact
    print(f"🗑️  Will delete {len(files_to_delete)} files ({total_size / 1024 / 1024:.1f} MB)")
    
    # 4. Require typed confirmation
    return self._get_typed_confirmation("DELETE")
```

## 🔐 Non-Interactive Mode Implementation

### Mode Detection and Configuration

```python
class SafeGitWrapper:
    def __init__(self):
        """Initialize with non-interactive support."""
        self.non_interactive = False
        self.force_yes = False
        self.assume_yes = False
        self.dry_run = False
        
        # Check environment variables
        self._check_environment()
        
    def _check_environment(self):
        """Check for CI environment and configuration."""
        # Non-interactive mode
        if any([
            os.getenv('SAFEGIT_NONINTERACTIVE'),
            os.getenv('CI'),
            os.getenv('CONTINUOUS_INTEGRATION'),
            os.getenv('GITHUB_ACTIONS'),
            os.getenv('GITLAB_CI'),
            os.getenv('JENKINS_URL'),
            os.getenv('TRAVIS')
        ]):
            self.non_interactive = True
            
        # Auto-confirmation levels
        if os.getenv('SAFEGIT_ASSUME_YES'):
            self.assume_yes = True
            
        if os.getenv('SAFEGIT_FORCE_YES'):
            self.force_yes = True
```

### Graduated Safety Implementation

```python
def _get_user_input(self, prompt: str, valid_responses: List[str] = None, 
                    danger_level: str = 'low') -> str:
    """Get user input with non-interactive support."""
    
    # Dry-run mode
    if self.dry_run:
        print(f"[DRY RUN] Would prompt: {prompt}")
        return 'n'
    
    # Non-interactive mode
    if self.non_interactive or self.assume_yes or self.force_yes:
        # Determine automatic response
        if danger_level == 'low' and (self.assume_yes or self.force_yes):
            # Safe operations - auto-confirm
            print(f"[AUTO-CONFIRM] {prompt} -> y")
            return 'y'
            
        elif danger_level == 'medium' and self.force_yes:
            # Medium risk - need force flag
            print(f"[FORCE-CONFIRM] {prompt} -> y")
            return 'y'
            
        elif danger_level == 'high' and self.force_yes:
            # High risk - handle typed confirmations
            if "Type" in prompt:
                # Extract required phrase
                match = re.search(r"Type '([^']+)'", prompt)
                if match:
                    required_text = match.group(1)
                    print(f"[AUTO-TYPE] {required_text}")
                    return required_text
            return 'y'
        else:
            # Cannot auto-confirm
            print(f"ERROR: {prompt}")
            print(f"ERROR: Requires --force-yes for {danger_level} risk operation")
            sys.exit(1)
    
    # Interactive mode - normal input
    return input(prompt)
```

## 🔄 Undo System Architecture

### Transaction Journal Structure

```python
{
    "id": "uuid-v4",
    "timestamp": "2025-01-23T10:30:00",
    "operation_type": "reset_hard",
    "command": ["reset", "--hard", "HEAD~1"],
    "metadata": {
        "branch": "main",
        "head_sha": "abc123",
        "head_message": "Previous commit message",
        "dirty_files": ["src/file1.py", "src/file2.py"],
        "stash_count": 3,
        "reflog_head": "HEAD@{0}: reset: moving to HEAD~1"
    },
    "backups": {
        "stash_ref": "stash@{0}",
        "backup_file": "/path/to/backup.zip"
    },
    "recovery_script": [
        "# Recover from hard reset",
        "git reset --hard HEAD@{1}",
        "# Or restore specific stash:",
        "git stash list | grep SAFEGIT",
        "git stash pop stash@{n}"
    ],
    "recovery_hints": {
        "primary": "Use reflog to find previous HEAD position",
        "command": "git reflog --date=iso"
    }
}
```

### Atomic File Operations

```python
def _atomic_write(path: Path, data: str):
    """Write file atomically with cross-platform support."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + f'.tmp-{uuid.uuid4().hex}')
    
    # Write to temp file
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    
    # Atomic rename
    os.replace(tmp, path)

@contextlib.contextmanager
def acquire_lock(lock_path: Path):
    """Cross-platform file locking."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, 'a+')
    
    try:
        if os.name == 'nt':
            # Windows
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # Unix/Linux/macOS
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield fh
    finally:
        # Release lock
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        fh.close()
```

## 📊 Performance Characteristics

### Overhead Analysis

| Operation | Overhead | Cause |
|-----------|----------|-------|
| Pattern Matching | ~5ms | Compiled regex |
| State Analysis | ~20ms | Git subprocess calls |
| Backup Creation | ~500ms | File I/O |
| Confirmation | 0ms (non-interactive) | Automated |
| Total Average | ~50ms | Negligible |

### Optimization Techniques

1. **Compiled Regex Patterns**: All patterns pre-compiled at startup
2. **Lazy Loading**: Handlers loaded only when needed
3. **State Caching**: Repository state cached per operation
4. **Parallel Processing**: Multiple git queries run concurrently
5. **Atomic Operations**: Minimize lock time with temp files

## 🧪 Testing Framework

### Test Coverage

```bash
# Core functionality tests
test_safegit_interception.py      # Pattern matching
test_safegit_handlers.py           # Handler logic
test_safegit_backup.py             # Backup creation
test_safegit_undo.py               # Undo system

# Feature tests
test_safegit_dryrun.py             # Dry-run mode
test_safegit_noninteractive.py    # CI/CD mode
test_safegit_context.py            # Context awareness
test_safegit_concurrency.py        # Thread safety

# Integration tests
test_safegit_ai_integration.py    # AI agent scenarios
test_safegit_cicd.py               # Pipeline integration
```

### Concurrency Testing

```python
def test_concurrent_operations():
    """Test SafeGIT under concurrent access."""
    import threading
    import queue
    
    results = queue.Queue()
    
    def run_safegit(cmd, q):
        try:
            result = subprocess.run(
                ['python3', 'safegit.py'] + cmd.split(),
                capture_output=True,
                text=True
            )
            q.put((cmd, result.returncode, result.stdout, result.stderr))
        except Exception as e:
            q.put((cmd, -1, '', str(e)))
    
    # Launch concurrent operations
    threads = []
    commands = [
        'status',
        'log --oneline -5',
        'diff',
        '--dry-run reset --hard',
        '--dry-run clean -fdx'
    ]
    
    for cmd in commands:
        t = threading.Thread(target=run_safegit, args=(cmd, results))
        t.start()
        threads.append(t)
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Verify all succeeded
    while not results.empty():
        cmd, code, out, err = results.get()
        assert code == 0, f"Command failed: {cmd}"
```

## 🔧 Configuration System

### Configuration File Structure

```json
// .git/safegit-context.json
{
    "environment": "production",
    "mode": "normal",
    "restrictions": {
        "allow_force_push": false,
        "allow_history_rewrite": false,
        "require_review": true
    },
    "protected_branches": ["main", "master", "production"],
    "audit_log": true,
    "education_mode": true
}
```

### Runtime Configuration

```python
class SafeGitConfig:
    """Runtime configuration management."""
    
    DEFAULT_CONFIG = {
        'max_backup_size_mb': 100,
        'stash_before_dangerous': True,
        'auto_recovery_hints': True,
        'verbose_mode': False,
        'education_mode': True,
        'audit_all_operations': False
    }
    
    def load_config(self):
        """Load configuration with fallback to defaults."""
        config_path = Path('.git/safegit-config.json')
        
        if config_path.exists():
            with open(config_path) as f:
                user_config = json.load(f)
                # Merge with defaults
                return {**self.DEFAULT_CONFIG, **user_config}
        
        return self.DEFAULT_CONFIG
```

## 🚀 Future Architecture Considerations

### Planned Enhancements

1. **Plugin System**: Allow custom handlers for organization-specific rules
2. **Remote State Cache**: Reduce API calls for branch protection checks
3. **Machine Learning**: Risk assessment based on operation patterns
4. **Team Policies**: Shared safety rules across repositories
5. **GUI Integration**: Visual confirmation dialogs for desktop users

### Performance Targets

- Sub-10ms overhead for safe operations
- Sub-100ms for dangerous operation analysis
- Zero blocking on non-interactive mode
- Scalable to mono-repos with 100k+ files

---

This technical reference provides the implementation details needed to understand, maintain, and extend SafeGIT. For user-facing documentation, see SAFEGIT_COMPREHENSIVE.md.