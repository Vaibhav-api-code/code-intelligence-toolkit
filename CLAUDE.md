▶ safegit.py show HEAD:CLAUDE.md
▶ safegit.py show HEAD:CLAUDE.md
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Last Updated**: July 28, 2025 - Major v1.5.0 release with unified interactive_utils module eliminating EOF errors in CI/CD environments

**CRITICAL DIRECTIVE (January 2025)**: Python tools are MANDATORY for ALL operations (read, write, analyze, file/filesystem operations) unless Python tools fail. Only use built-in Claude Code tools when Python tools encounter errors.

**CRITICAL DIRECTIVE (January 2025)**: SafeGIT is MANDATORY for ALL git operations. Never use `git` directly - always use `safegit` to prevent data loss. This applies to all git commands including status, diff, add, commit, push, pull, reset, etc.

**CRITICAL DIRECTIVE (January 2025)**: safe_file_manager.py is MANDATORY for basic file operations. Use appropriate Python tools through `./run_any_python_tool.sh`:
- **File operations**: `safe_file_manager.py` for move/copy/delete/mkdir/list/create
- **Reading code**: `find_text_v7.py`, `navigate_ast.py`, `show_structure_ast.py` 
- **Writing/editing**: `replace_text_v9.py`, `replace_text_ast_v3.py`, `unified_refactor_v2.py`
- **Analysis**: All Python analysis tools remain in use

**Built-in tool usage policy**: Built-in Claude Code tools (Read, Write, Edit, MultiEdit, LS) are ONLY allowed as fallback when:
1. Python tools encounter errors (file not found, permission denied, syntax errors)
2. Python tools are unavailable (wrapper script issues)
3. Extremely simple one-time operations where Python tool overhead is unnecessary
Always try Python tools first. Document when using built-in tools and why.

**🛡️ COMPLETE SAFETY ACHIEVED**: Direct access to ALL destructive commands is now BLOCKED via Claude Code permissions:
- **Git commands**: All git operations blocked - use SafeGIT via `./run_any_python_tool.sh safegit.py [command]`
- **File commands**: rm, mv, cp, mkdir, touch, chmod, chown, rmdir, dd, shred, unlink - ALL BLOCKED
- **Only safe access**: All file operations MUST go through `./run_any_python_tool.sh safe_file_manager.py [command]`

This protection prevents accidental data loss. Work with complete confidence knowing that:
- No accidental deletions possible - rm is completely blocked
- No accidental overwrites - mv/cp are blocked, use safe_file_manager.py
- Automatic backups before any operation
- Complete operation history and undo capabilities
- Non-interactive mode for automation (SFM_ASSUME_YES=1)

**File Size Monitoring**: This file should be kept under 40,000 characters for optimal performance. Target size: ~30,000 characters. Check size with `wc -c CLAUDE.md` and trim verbose sections if approaching 40k limit.

## Working with Confidence

With SafeGIT v2.0 fully integrated and direct git access blocked, you can now work with complete confidence:
- **No more lost work** - Dangerous git operations are intercepted and require confirmation
- **Automatic protection** - Backups created before any destructive operation
- **Recovery available** - Multi-level undo system with recovery scripts
- **Peace of mind** - Focus on coding, not worrying about accidental data loss

## Project Overview

This is a sophisticated Bookmap trading strategies repository implementing advanced market microstructure analysis, liquidity tracking, and algorithmic trading systems. Built on the Bookmap API framework for real-time market data processing and trading execution.

### Code Intelligence Toolkit Design Philosophy

**CRITICAL UNDERSTANDING**: The toolkit deliberately uses NO PERSISTENT INDEX - this is a cornerstone feature:

- **✅ Guaranteed Accuracy**: Analysis always reflects current file state - never stale results
- **⚡ Zero Setup Time**: Clone and run immediately - no indexing delays  
- **🏃 No Resource Drain**: Zero CPU/memory when idle - no background processes
- **🐳 Modern Workflow Ready**: Perfect for CI/CD, containers, and ephemeral environments
- **🤖 AI Agent Optimized**: Predictable, stateless operations ideal for AI workflows

This **"faster, safer, and more accurate"** approach ensures reliable analysis without indexing complexity or resource overhead. Every tool operates on current disk state, making results completely trustworthy for AI decision-making.

## Reference Component Versions

The following are the stable/validated versions that should be used as references throughout the codebase:

- **NubiaAutoMidasAnchoredVWAPV7_1_5** - Latest Nubia implementation with proximity virtual trend tracking and enhanced state management
- **NubiaAutoMidasAnchoredVWAPV6_0_7** - Previous stable implementation with thread safety improvements
- **NubiaAutoMidasAnchoredVWAPV6_0_0** - Legacy stable Nubia implementation
- **InputDataHealthTrackerV4** - Latest health tracking implementation with adaptive frequency detection and backward compatibility
- **MultiLevelOrderBookExpwithQDSelfCalcDisableV6_5** - Latest order book with ILiquidityDataProvider2 interface (used by NubiaV6_0_0)
- **LiquidityClusterAnalyzerV1_7** - Enhanced cluster detection with cleanup() and startNewSession() methods
- **VolumeProfileAnalyzerV3_1** - Latest volume profile analysis with HVN detection and automatic ES optimization (used by NubiaV6_0_0)
- **VolumeProfileChartFrameV3** - Latest chart frame using ManagedSingletonUI pattern (June 2025)
- **DiagnosticChartFrameV3_5** - Polling-based diagnostic chart with ILiquidityDataProvider2 (June 2025)
- **LiquidityTrackerMultiLevelV8** - Multi-level liquidity tracking implementation
- **OrdersTestUIV4_Bulletproof** - Latest orders UI with bulletproof implementation (used by NubiaV6_0_0)
- **OrderSenderControllerV2** - Order sending control (June 2025)
- **NubiaHealthStatusUIV5** - Enhanced health status UI with ManagedSingletonUI pattern (upgraded June 2025)
- **ManagedDataDistributor** - Thread-safe data distribution framework (June 2025)
- **ManagedFilteredDataDistributor** - Filtered data distribution with lifecycle management (June 2025)
- **RejectionMachineV3** - Advanced rejection detection with time-based analysis, confidence scoring, and velocity tracking (July 2025)
- **ProximityConditionCheckerV3** - Enhanced proximity analysis with 9-state model, state quality metrics, confidence scoring, and virtual trend tracking (July 2025)
- **DualColorManagedIndicator** - Advanced indicator framework supporting dual-color rendering and state management (July 2025)

Note: While newer versions may exist (e.g., V5, V8_5), these listed versions are the validated reference implementations. Always verify version stability before upgrading.

### Version Documentation Checklist

When changing ANY component version:

- [ ] Update class-level JavaDoc and .md files
- [ ] Update CLAUDE.md "Reference Component Versions" section
- [ ] Update all dependent class documentation
- [ ] Create VERSION_CHANGE_SUMMARY.md
- [ ] Run `./find_references.py OldVersionName --type class`
- [ ] Update DEPENDENCIES.md files
- [ ] Test all affected classes

**Remember**: Documentation debt compounds quickly. Keep docs in sync with code!

## Latest Tool Enhancements (July 2025)

### Non-Interactive Mode Support (July 28, 2025)

**interactive_utils.py** - Unified module eliminating EOF errors:
- **Auto-detection**: CI/CD, pipes, no TTY
- **Clear errors**: Actionable hints instead of crashes
- **Config hierarchy**: Flags > env vars > .pytoolsrc > defaults
- **Migrated tools**: text_undo, safe_file_manager, safegit, replace_text_v9, replace_text_ast_v3

**Usage**: `TOOL_NAME_ASSUME_YES=1` or `--yes` flag or `.pytoolsrc` config

### safe_file_manager.py - Enterprise File Management (MANDATORY)

**safe_file_manager.py** - Complete file management replacement for all built-in tools:
- **Atomic operations**: All file operations use temp files and atomic replace
- **Checksum verification**: Automatic integrity checking in paranoid mode
- **Cross-process locking**: Safe for concurrent operations
- **Complete undo system**: Operation history and trash for recovery
- **Non-interactive mode**: `SFM_ASSUME_YES=1` for automation
- **Overwrite safety**: Explicit `--overwrite` flag required

**Core commands:**
- `move/mv` - Move files with automatic backup
- `copy/cp` - Copy with checksum verification
- `create` - Create files with content (NEW - replaces echo > file)
- `trash/rm` - Safe deletion (never permanent delete)
- `list/ls` - Enhanced directory listing
- `cat/view` - Read file contents safely
- `info` - Detailed file metadata
- `mkdir`, `touch` - Create directories and files
- `chmod` - Change permissions (supports both octal: 755 and symbolic: +x, u+rwx)
- `chown`, `ln` - Change ownership and create links

**This tool is MANDATORY for all file operations unless it encounters errors.**

**Troubleshooting EOF errors:**
If you get "EOF when reading a line" errors, it means the tool is waiting for user confirmation but can't read input (common in scripts/CI). Solutions:
- Use `--yes` flag: `safe_file_manager.py --yes chmod 755 file.txt`
- Set environment: `SFM_ASSUME_YES=1`
- Use `--non-interactive` flag for strict automation

### SafeGIT - Enterprise Git Safety System (NEW)

**SafeGIT v2.0** - Complete git wrapper preventing accidental data loss with full CI/CD support:
- **Zero remaining gaps**: All 37+ dangerous operations intercepted with dedicated handlers
- **Intelligent confirmations**: Risk-based typed confirmations prevent accidental execution
- **Complete undo system**: Multi-level operation history with recovery scripts
- **Cross-platform atomic operations**: File locking prevents corruption under concurrent usage
- **AI agent protection**: Single rule prevents Replit-style disasters
- **Educational value**: Clear explanations of risks with safer alternatives

**Documentation:**
For comprehensive SafeGIT documentation, see:
- `code-intelligence-toolkit/SAFEGIT_COMPREHENSIVE.md` - Complete user guide with all v2.0 features
- `code-intelligence-toolkit/SAFEGIT_TECHNICAL_REFERENCE.md` - Implementation details
- `code-intelligence-toolkit/AI_AGENT_GIT_RULES.md` - AI integration guide

**Critical handlers added:**
- `push --mirror/--delete`: Repository-wide and branch-specific warnings
- `reflog expire`: Safety net removal warnings  
- `update-ref -d`: Low-level reference deletion warnings
- Enhanced `push --force`: Branch protection detection and divergence analysis

**Installation:** Simple alias replacement provides transparent git safety
**Usage:** `safegit --dry-run <command>` for training, normal usage requires confirmations

### Multi-Level Undo System (NEW in v9)

**text_undo.py** - Comprehensive undo management for all text operations:
- **View history**: `text_undo.py history` - Shows all tracked operations
- **Undo last**: `text_undo.py undo --last` - Reverts the most recent change
- **Undo specific**: `text_undo.py undo --operation ID` - Reverts a specific operation
- **Interactive mode**: `text_undo.py undo --interactive` - Choose from a list
- **Show details**: `text_undo.py show ID` - View operation details
- **Statistics**: `text_undo.py stats` - System usage statistics
- **Cleanup**: `text_undo.py clean` - Remove old operations (>30 days)

**Integration with replace_text_v9.py**:
- Automatic tracking enabled by default
- Use `--no-undo` to disable for specific operations
- Use `--undo-description "text"` for custom descriptions
- Every operation shows its undo ID for easy recovery

### Key Tool Features Summary

**find_text_v7.py** - Most comprehensive search tool with multiline search and ALL features:
- **Pattern search**: Text, regex, word, fixed string with full context support
- **Block extraction**: `--extract-block` for complete code blocks (if/for/while/try)
- **Method extraction**: `--extract-method` (500 lines) / `--extract-method-alllines` (unlimited)
- **Range extraction**: `--extract-ranges` outputs line numbers, `--merge-ranges` consolidates
- **Wholefile mode**: `--wholefile` displays entire files with/without pattern matching
- **Multiple files**: `--file file1.py file2.java file3.js` searches across files
- **Auto-find**: `--auto-find` locates files automatically by name
- **Context lines**: `-C 5`, `-A 3`, `-B 2`, or `"pattern" ±10` syntax
- **AST context**: Shows class → method hierarchy (enabled by default)
- **Line extraction**: `--lines "1-5,10-15"` extracts specific line ranges
- **Output control**: `--json`, `--no-color`, `--quiet`, `--verbose`
- **Direct line access**: `--ranges` for batch line range operations
- **Multiline search**: `--multiline` or `-U` enables patterns to span multiple lines

**NOTE**: v7 adds multiline search support + v6 (blocks/wholefile) + v5 (ranges/auto-find) + v4 (method extraction)

**replace_text_v9.py** - Text replacement with multi-level undo support (NEW):
- **Complete superset of v8**: Includes all v8 features plus undo system
- **Automatic undo tracking**: Every replacement is tracked by default
- **Multi-level undo**: Full operation history with recovery support
- **Undo control flags**:
  - `--no-undo`: Disable undo tracking for this operation
  - `--undo-description "text"`: Custom description for undo history
- **Escape sequence support**: All v8 escape sequences (`\n`, `\t`, `\r`, `\x`, `\u`, etc.)
- **Integration with text_undo.py**: Use `text_undo.py undo --last` to undo operations
- **Zero configuration**: Undo enabled by default, no setup required
- **Atomic operations**: Thread-safe with file locking
- **Previous versions**: v8 added escape sequences, v7 added ripgrep/blocks/JSON pipeline

**replace_text_ast_v3.py** - AST-based refactoring with multi-level undo support (NEW):
- **Complete superset of v2**: Includes all v2 features plus undo system
- **AST-aware undo tracking**: Every refactoring operation is tracked
- **Smart descriptions**: Automatically generates context-aware undo descriptions
- **Integration with text_undo.py**: Same undo workflow as replace_text_v9.py
- **Undo control flags**: `--no-undo` and `--undo-description` supported
- **Operation type**: Uses `OperationType.REPLACE_AST` for proper categorization
- **Previous versions**: v2 added enhanced AST features and escape sequence support

**replace_text_v9.py** + **replace_text_ast_v3.py** + **unified_refactor_v2.py** - Professional refactoring suite:
- **replace_text_v9.py**: Enhanced text replacement with multi-level undo, escape sequences (\\n, \\t, \\r, \\x, \\u), ripgrep integration, block-aware modes, JSON pipeline
- **replace_text_ast_v3.py**: AST-based refactoring with multi-level undo support, V7 compatibility features (block-mode, git integration, comments-only, strings-only) + V8 escape sequence support
- **unified_refactor_v2.py**: Universal refactoring interface with multi-level undo support and multiple backends (python_ast, rope, java_scope, text_based) featuring unified diff previews, AST-guided rope targeting, and JSON pipeline workflows
- **Version consolidation**: All features from previous versions unified into definitive tools
- **Professional features**: Unified diffs, smart rope offset calculation, JSON pipeline integration, multi-engine support
- **Full feature parity**: Complete feature sets with atomic operations, retry logic, and enterprise-grade safety

**unified_refactor_v2.py** - Universal refactoring interface with undo support (NEW):
- **Language-aware backends**: `auto` (default - detects Java vs Python), `rope`, `java_scope`, `text_based`
- **Auto-detection**: `.java` files → `java_scope`, `.py` files → `python_ast`, others → `text_based`
- **Commands**: `rename` (variable/function/class), `find` (references), `analyze` (code analysis)
- **Cross-language**: Seamless support for mixed Java/Python codebases
- **Known issues**: Replace command not working, Rope backend has path issues, dry-run inaccurate
- **Working features**: Rename with auto-detection, find references, analyze structure

**show_structure_ast_v4.py** - Hierarchical code viewer:
- Multi-language: Python (AST), Java (javalang), JavaScript (esprima)
- Java annotation filtering: `--filter-annotation "@Test"`
- Optional preprocessing: `--no-preprocess` for large files

**safegit.py** - Git safety wrapper preventing disasters:
- Intercepts 20+ dangerous git command patterns
- Automatic backups: stashes for reset, zips for clean
- Smart detection: checks if commits are pushed before amend
- Dry-run mode: `--dry-run` to preview any command
- Context modes: production, staging, code-freeze restrictions
- Reflog hints: shows recovery commands after operations
- AI protection: prevents Replit-style disasters

**File Operations V2** - Enterprise-grade atomic safety:
- All 8 file write tools with retry logic and lock detection
- Configurable: `--max-retries 5 --retry-delay 2.0`
- Checksums: `--verify-checksum`
- Interactive undo: `safe_move.py undo --interactive`

**Error Analysis Suite**:
- `analyze_errors.py` - Basic error viewing with `--clear` flag for log cleanup
- `error_analyzer.py` - Deep analysis with patterns
- `error_dashboard_v2.py` - Visual ASCII dashboard with `--clear` flag for reset

**Configuration**: `.pytoolsrc` via `common_config.py --create/--show`


### Version Naming Conventions

1. **Version in Class Name**: Always include version (e.g., `V6_5`)
2. **Version Format**: Use V{major}_{minor} for clarity (e.g., `V3_1` not `V31`)
3. **Variant Naming**: Use descriptive suffixes (e.g., `V4_Bulletproof`)
4. **No Version = Legacy**: Classes without versions are legacy code
5. **Import Consistency**: Imports must match exact class name versions

## Recent Major Updates (January 2025)

**Configuration & Error Systems**:
- Unified config via `.pytoolsrc` - All tools load project defaults with CLI override
- Automatic error logging to `~/.pytoolserrors/` - Analyze with error tools suite
- Compile checking overhauled - Honest feedback with `✓ Compiles` or `✗ Cannot check`

**Tool Enhancements**:
- **AST Suite**: Perfect accuracy for navigation, refactoring, analysis
- **Directory Tools**: Enhanced listing, search, stats with rich features
- **File Operations V2**: Atomic writes, retry logic, checksums, undo support
- **Dead Code Detector**: Multi-language with 60s timeout protection
- **Git Analyzer**: GIT SEQ workflows, smart staging, commit generation
- **Security Framework**: Enterprise-grade protection across all 40+ tools
- **Release Workflow**: Automated versioning and GitHub releases for code-intelligence-toolkit

**Key Fixes**:
- Argparse `--max` alias added for `--limit`
- Threading support with `--threads N`
- Trace calls rewritten with AST
- DrawdownGuard, ManagedIndicator, NubiaV6_0_0 fixes

## Tool Usage Priority Guidelines

**CRITICAL: Python tools are MANDATORY for ALL operations unless they fail**

### Tool Selection Priority

1. **🥇 Python tools via wrappers** - MANDATORY first attempt for all operations
2. **🥇 AST tools** - Perfect accuracy, semantic understanding
3. **🥇 Bulletproof file tools** - Enterprise-grade safety with atomic operations and retry logic
4. **🥇 Directory tools** - Rich features, comprehensive output
5. **⚠️ Built-in tools** - ONLY when Python tools fail or encounter errors

**Built-in tool usage rules:**
- ALWAYS try Python tools first
- Document Python tool failure before using built-in tools
- Example: "Using built-in Read because find_text_v7.py returned 'file not found' error"
- Never use built-in tools for convenience - only for failures

### For DIRECTORY Operations:
**ALWAYS use directory tools first:**
- `./run_any_python_tool.sh smart_ls.py` - Enhanced directory listing
- `./run_any_python_tool.sh find_files.py` - Comprehensive file search
- `./run_any_python_tool.sh recent_files.py` - Track recent changes
- `./run_any_python_tool.sh tree_view.py` - Visual directory structure
- `./run_any_python_tool.sh dir_stats.py` - Directory analysis

### For READ Operations:
**ALWAYS use AST-based tools first:**
- `./run_any_python_tool.sh navigate_ast.py` - 100% accurate definition finding
- `./run_any_python_tool.sh method_analyzer_ast.py` - Perfect call flow analysis  
- `./run_any_python_tool.sh cross_file_analysis_ast.py` - Enhanced dependency analysis
- `./run_any_python_tool.sh semantic_diff_v3.py` - Most advanced semantic diff with enterprise features
- `./run_any_python_tool.sh data_flow_tracker_v2.py` - Track variable dependencies and data flow (NEW)

**Text-based tools for simple searches:**
- `./run_any_python_tool.sh find_text_v7.py` - Enhanced with context lines and AST context
- `./run_any_python_tool.sh cross_file_analysis.py` - Basic dependency analysis

### For Code Operations:
**Use the right Python tool for the job:**

**Reading/searching code:**
- `./run_any_python_tool.sh find_text_v7.py` - Text search with context
- `./run_any_python_tool.sh navigate_ast.py` - AST navigation
- `./run_any_python_tool.sh show_structure_ast.py` - Code structure
- Built-in Read tool - ONLY if Python tools fail with errors

**Writing/editing code:**
- `./run_any_python_tool.sh replace_text_v9.py` - Text replacements with escape sequences
- `./run_any_python_tool.sh replace_text_ast_v3.py` - AST-aware refactoring with escape sequences
- `./run_any_python_tool.sh unified_refactor_v2.py` - Universal refactoring with undo
- Built-in Write/Edit/MultiEdit - ONLY if Python tools fail with errors

**File operations (move/copy/delete/create):**
- `./run_any_python_tool.sh safe_file_manager.py` - For ALL file management
- Shell commands (rm, mv, cp) are BLOCKED - no exceptions
- Built-in tools cannot perform these operations

**Directory navigation (cd/pwd):**
- `./run_any_python_tool.sh safe_file_manager.py cd <dir>` - Validate directory (returns path)
- `./run_any_python_tool.sh safe_file_manager.py pwd` - Show current directory
- For actual directory changes, use the `scd` shell function (run `./setup_safe_cd.sh`)
- Regular `cd` is allowed but `scd` provides validation

### Security Framework

All Python tools include enterprise-grade security:
- Path traversal protection, input sanitization
- Resource limits (memory, CPU, file handles)
- Atomic operations with rollback support
- Comprehensive error logging to `~/.pytoolserrors/`
- Inherits from `SecureFileHandler`, `SecureCommandExecutor`
- 100% coverage with zero breaking changes

### safe_file_manager.py - The ONLY File Operation Tool:
**Enterprise-grade file management with MANDATORY usage for ALL operations:**
- `./run_any_python_tool.sh safe_file_manager.py move <src> <dst>` - Move files/directories
- `./run_any_python_tool.sh safe_file_manager.py copy <src> <dst> [--overwrite]` - Copy with checksums
- `./run_any_python_tool.sh safe_file_manager.py trash <files>` - Safe deletion to trash
- `./run_any_python_tool.sh safe_file_manager.py list <dir>` - Directory listing
- `./run_any_python_tool.sh safe_file_manager.py mkdir <dir>` - Create directories
- `./run_any_python_tool.sh safe_file_manager.py organize <dir>` - Auto-organize files
- `./run_any_python_tool.sh safe_file_manager.py cd <dir>` - Validate and change directory (returns absolute path)
- `./run_any_python_tool.sh safe_file_manager.py pwd` - Print current working directory
- **Atomic operations**: All operations use temp files and atomic replace
- **Checksum verification**: Automatic in paranoid mode, configurable otherwise
- **Complete reversibility**: Undo system and trash for recovery
- **Cross-process locking**: Safe for concurrent operations
- **Non-interactive mode**: `SFM_ASSUME_YES=1` for automation
- **Shell integration**: Use `scd` function for actual directory changes (see SAFE_CD_INTEGRATION.md)

### Wrapper Usage:
- **Always use wrapper**: `./run_any_python_tool.sh`
- **One approval covers all operations** in that session
- **Never use Python tools directly** - always through wrapper
- **Note**: `java_analysis.sh` has been retired (all its tools are in run_any_python_tool.sh)

### Tool Troubleshooting:
**CRITICAL: Before giving up on any tool, always check the help first**
- `./run_any_python_tool.sh tool_name.py --help` - Get authoritative usage syntax
- **Common issues**: Wrong argument order, missing flags, incorrect regex syntax
- **Example**: If `find_text_v7.py` returns "No matches found", check `--help` for proper regex syntax
- The built-in help is always the most accurate and up-to-date reference

### When Built-in Tools Can Be Used (EXCEPTIONS ONLY)

**Built-in tools are ONLY acceptable when Python tools fail. Examples:**

```bash
# ❌ WRONG - Using built-in for convenience
Read /path/to/file.txt              # Don't do this - use Python tools

# ✅ CORRECT - Using built-in after Python tool failure
./run_any_python_tool.sh find_text_v7.py --file nonexistent.txt
# Error: File not found
# Now using built-in Read due to Python tool error
Read /path/to/check/if/exists.txt

# ❌ WRONG - Using built-in Edit for simple change  
Edit file.py                        # Don't do this - use replace_text_v9.py

# ✅ CORRECT - Documenting fallback usage
./run_any_python_tool.sh replace_text_v9.py "old" "new" file.py
# Error: Permission denied
# Falling back to built-in Edit due to permission error
Edit file.py
```

**Remember**: Document WHY you're using built-in tools (what error occurred)


### The Complete safe_file_manager.py Philosophy (January 2025)

**safe_file_manager.py is now the COMPLETE solution for ALL file system operations.**

With the addition of `cd` and `pwd` commands, there is virtually NO legitimate reason to use anything else for file operations. This represents the completion of our toolset development goal: making the safe way the only way.

#### Why This Matters:

1. **Total Coverage** - Every file operation you need:
   - Reading: `cat`, `view`
   - Writing: `copy`, `create`, `touch`
   - Moving: `move`, `mv`
   - Deleting: `trash`, `rm` (to trash, never permanent)
   - Listing: `list`, `ls`
   - Navigation: `cd`, `pwd` (NEW!)
   - Directories: `mkdir`, `rmdir`
   - Permissions: `chmod`, `chown`
   - Links: `ln`
   - Info: `info`, `history`

2. **Zero Accidents** - It's practically impossible to:
   - Accidentally delete important files (trash system)
   - Overwrite without explicit permission
   - Navigate to non-existent directories
   - Lose work (automatic backups, undo system)

3. **Consistency** - One tool means:
   - One set of behaviors to learn
   - One configuration system
   - One audit trail
   - One safety philosophy

4. **The 99% Rule**:
   - 99% of the time: Use safe_file_manager.py
   - 1% exceptions: Emergency recovery, Python failures, specific shell operations
   - Always document the 1% cases with clear justification

**Achievement Unlocked**: We've successfully created a comprehensive, safe file management system that makes dangerous operations impossible while keeping common operations simple. This completes our vision of "making the safe way the easy way."


### Python Tool Examples

```bash
# ✅ CORRECT - Always use Python tools first:
./run_any_python_tool.sh find_text_v7.py "pattern" --file file.txt
./run_any_python_tool.sh safe_file_manager.py cat file.txt
./run_any_python_tool.sh replace_text_v9.py "old" "new" file.txt
./run_any_python_tool.sh safe_file_manager.py ls /directory
./run_any_python_tool.sh safe_file_manager.py create file.txt --content "text"

# Complete examples:
./run_any_python_tool.sh find_text_v7.py "pattern" --file file.txt      # For reading/searching
./run_any_python_tool.sh replace_text_v9.py "old" "new" file.txt        # For editing
./run_any_python_tool.sh safe_file_manager.py list /directory        # For listing
./run_any_python_tool.sh safe_file_manager.py copy src.txt dst.txt   # For copying
./run_any_python_tool.sh safe_file_manager.py move old.txt new.txt   # For moving
./run_any_python_tool.sh safe_file_manager.py create file.txt --content "text"  # For creating files
echo "content" | ./run_any_python_tool.sh safe_file_manager.py create file.txt --from-stdin
./run_any_python_tool.sh safe_file_manager.py cd /path/to/dir        # For validating directories
./run_any_python_tool.sh safe_file_manager.py pwd                    # For current directory
```

**Python tools are mandatory first choice. Built-in tools are only for fallback when Python tools fail.**

### Shell Parsing Pitfalls and Solutions

**CRITICAL: When creating files with complex content, beware of shell parsing issues**

Shell command line parsing can fail when passing multi-line content containing shell keywords (elif, done, fi, esac, etc.) via command-line arguments. This is NOT a deficiency in our tools - it's a shell parsing limitation.

**Problem Example (WILL FAIL):**
```bash
# ❌ This fails with "parse error near 'elif'"
./run_any_python_tool.sh safe_file_manager.py create script.py --content '#!/usr/bin/env python3
if condition:
    pass
elif other_condition:
    pass'
```

**Solution: Use --from-stdin with here-docs for complex content:**
```bash
# ✅ CORRECT - Use here-doc to avoid shell parsing issues
cat << 'EOF' | ./run_any_python_tool.sh safe_file_manager.py create script.py --from-stdin
#!/usr/bin/env python3
"""Complex multi-line Python script"""
if condition:
    pass
elif other_condition:
    pass
EOF

# ⚠️ IMPORTANT: The 'EOF' marker must be on its own line with NO indentation
# The EOF line is NOT part of the file content - it's a shell delimiter
# If you see 'EOF < /dev/null' in your files, you've included the delimiter by mistake
```

**Alternative Solutions:**
```bash
# Using echo with pipe
echo '#!/usr/bin/env python3
if True:
    pass
elif False:
    pass' | ./run_any_python_tool.sh safe_file_manager.py create script.py --from-stdin

# Using ANSI-C quoting (for simpler cases)
./run_any_python_tool.sh safe_file_manager.py create script.py --content $'#!/usr/bin/env python3\nprint("Hello")'
```

**Guidelines:**
- Simple single-line content: Use `--content "text"`
- Multi-line content with shell keywords: Use `--from-stdin` with here-docs
- Complex Python/JavaScript/Shell scripts: Always use `--from-stdin`
- When in doubt: Use `--from-stdin` - it's always safer

### Avoiding the 'EOF < /dev/null' Issue

**CRITICAL: If you see `EOF < /dev/null` at the end of files you create, you've made a heredoc mistake**

**Common Causes:**
1. **Copying terminal output** that includes the EOF delimiter
2. **Indenting the EOF marker** (it must be at the start of the line)
3. **Including extra text after EOF** on the same line
4. **Copying examples incorrectly** from documentation

**Correct Heredoc Usage:**
```bash
# ✅ CORRECT - EOF is alone on its line, no indentation
cat << 'EOF' | ./run_any_python_tool.sh safe_file_manager.py create file.py --from-stdin
#!/usr/bin/env python3
print("Hello World")
EOF

# ❌ WRONG - EOF is indented (will not terminate heredoc)
cat << 'EOF' | ./run_any_python_tool.sh safe_file_manager.py create file.py --from-stdin
#!/usr/bin/env python3
print("Hello World")
    EOF

# ❌ WRONG - Extra text after EOF
cat << 'EOF' | ./run_any_python_tool.sh safe_file_manager.py create file.py --from-stdin
#!/usr/bin/env python3
print("Hello World")
EOF < /dev/null
```

**Remember:** The `EOF` line is a shell delimiter, NOT part of your file content!

### Parallel Task Execution

**CRITICAL: Use parallel Tasks for multi-file analysis**

The Task tool can launch multiple agents in parallel. This is MUCH faster than sequential analysis.

**Best practices:**
- Give each Task a specific file or package to analyze
- Make Task prompts self-contained with clear output requirements
- Launch all Tasks in a single tool invocation

**Example:**
```
Task 1: "Use ./run_any_python_tool.sh smart_ls.py src/ --ext java to find Java files"
Task 2: "Use ./run_any_python_tool.sh navigate_ast.py OrderSender.java sendOrder to find method"
Task 3: "Use ./run_any_python_tool.sh recent_files.py --since 2d --ext java to find recent changes"
```

## Task Completion Guidelines

**CRITICAL: Always complete tasks properly, never take shortcuts**

Complete all aspects thoroughly: address full scope, prioritize quality over speed, test and verify. Avoid shortcuts like moving files instead of converting, partial implementations, ignoring edge cases, or skipping verification.

## Code Commenting and Debugging Guidelines

**CRITICAL: Never leave code commented out permanently**

When working with code:
- **Temporary commenting**: You MUST restore before completing the task
- **Document why**: Add clear TODO comment if temporarily disabled
- **Complete restoration**: Ensure all commented code is restored or removed with justification
- **Never leave broken state**: Commenting out functionality and leaving it is unacceptable

**Examples:**
```java
// WRONG: Leaving code commented without restoration
// public void importantMethod() { ... }  // Commented for debugging - NEVER leave this way

// CORRECT: Proper temporary commenting with restoration plan
// TODO: Restore when MissingClass is implemented
// public void importantMethod() { ... }

// CORRECT: Complete removal with documentation if truly obsolete
// Removed importantMethod() - replaced by newMethod() in V2.0
```

## Undo and File Restoration Guidelines

**CRITICAL: When asked to undo changes, NEVER use git restore unless explicitly requested**

When user asks to "undo" changes:
- **Use Python tools first**: `./run_any_python_tool.sh replace_text_v9.py` to revert specific changes
- **Fallback to Edit/MultiEdit**: Only if Python tools fail or for extremely simple reversions
- **Preserve unsaved changes**: File may contain user's unsaved work
- **Never use git restore**: This destroys ALL changes including user's work

**Preferred undo workflow:**
```bash
# 1. Use Python tools for complex undos
./run_any_python_tool.sh replace_text_v9.py "new_code" "old_code" file.java --backup

# 2. Use built-in Edit only for simple single-line reverts
Edit file.java  # Only if Python tools fail
```

## SafeGIT - Git Safety Tool

**NEW TOOL: SafeGIT prevents git disasters before they happen**

SafeGIT is a protective wrapper that intercepts dangerous git commands and provides safety features:

### Key Features:
- **Automatic Backups**: Creates stashes before reset, zip files before clean
- **Smart Detection**: Knows if commits are pushed before allowing amend
- **Force Push Protection**: Converts `--force` to safer `--force-with-lease` 
- **Dry-Run Mode**: Test any command with `--dry-run` to see effects
- **Recovery Hints**: Shows reflog commands after destructive operations
- **Context Awareness**: Different rules for production/staging/development

### Usage in this codebase:
```bash
# SafeGIT is available in code-intelligence-toolkit/
cd code-intelligence-toolkit
./safegit.py reset --hard HEAD~1    # Will create backup first
./safegit.py --dry-run clean -fdx   # Preview what would be deleted

# For AI safety: Configure to use safegit instead of git
# This prevents accidental data loss from AI commands
```

### When to use SafeGIT:
- **Always** when executing user's git reset/clean/force commands
- When working with important branches (main, production)
- To preview effects of dangerous operations
- To educate users about git recovery options

## SafeGIT - Complete Git Safety System

**SafeGIT v2.0** provides comprehensive protection against git disasters through intelligent command interception and safety analysis, now with full non-interactive mode for automation.

### Key Features
- **100% Dangerous Command Coverage**: Intercepts 37+ risky operations (reset --hard, clean -fdx, push --force, etc.)
- **Enterprise-Grade Safety**: Multi-level confirmations, atomic operations, complete undo system
- **Educational Warnings**: Clear explanations of risks with safer alternatives
- **Cross-Platform**: Windows/macOS/Linux support with atomic file locking
- **AI Agent Protection**: Single rule prevents Replit-style disasters
- **Zero Configuration**: Works immediately with intelligent defaults

### Installation and Usage

**Quick Setup (Recommended):**
```bash
# Add to ~/.bashrc or ~/.zshrc
alias git='python3 /path/to/safegit.py'
source ~/.bashrc

# Verify installation
git --version  # Should show "SafeGIT v2.0 - Git wrapper for AI safety"
```

**Usage Examples:**
```bash
# Dangerous operations require explicit confirmation:
git reset --hard              # Shows safety analysis → requires "PROCEED"
git clean -fdx                # Shows impact → requires "DELETE"  
git push --force              # Converts to --force-with-lease + confirmation
git stash clear               # Offers backup → requires confirmation

# Safe operations pass through normally:
safegit status                    # Safe command
safegit add .                     # Requires confirmation for bulk add
safegit commit -m "msg"           # Checks for issues before commit
```

### SafeGIT Command Reference

**Core Operations:**
- `safegit --dry-run <command>`: Preview what would happen without executing
- `safegit --version`: Show SafeGIT version and real git path
- `safegit undo-history`: View complete operation history with recovery hints
- `safegit undo`: Undo last dangerous operation
- `safegit undo --interactive`: Choose specific operation to undo
- `safegit stats`: Show interception statistics

**Context Management:**
- `safegit set-env <development|staging|production>`: Set environment restrictions
- `safegit set-mode <normal|code-freeze|maintenance|paranoid>`: Set work mode
- `safegit show-context`: Display current environment and mode settings
- `safegit show-context --json`: Machine-readable context output
- `safegit add-restriction <pattern>`: Add custom command restriction
- `safegit remove-restriction <pattern>`: Remove custom restriction

**Dangerous Operations Intercepted:**
```bash
# Reset operations
git reset --hard              → Dedicated handler, backup creation
git reset --keep              → Allowed (safer alternative)

# Clean operations  
git clean -f/-d/-x            → Dedicated handler, backup offered

# Push operations
git push --force              → Converted to --force-with-lease
git push --mirror             → Extreme danger warnings
git push --delete             → Branch-specific warnings

# History operations
git rebase                    → History rewrite warnings
git reflog expire             → Safety net removal warnings  
git update-ref -d             → Low-level operation warnings

# Stash operations
git stash clear               → Backup creation offered
git stash drop                → Per-stash confirmation

# Advanced operations
git gc --prune=now            → Repository impact warnings
git filter-branch/filter-repo → Blocked by default
```

### AI Agent Integration

**For AI Agents (Claude, GPT, etc.):**
```
CRITICAL RULE: Always use 'python3 safegit.py' instead of 'git' for all git operations.
Never run 'git' directly - always use the SafeGIT wrapper to prevent disasters.
```

**Environment Setup:**
```bash
export SAFEGIT_PATH="/path/to/safegit.py"
# AI agents should use: python3 $SAFEGIT_PATH <command>
```

**Non-Interactive Mode (NEW in v2.0):**
```bash
# For CI/CD and automated scripts
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1

# Command-line flags
safegit --yes add .                    # Auto-confirm safe operations
safegit --force-yes reset --hard       # Force dangerous operations (use carefully!)
safegit --non-interactive status       # Strict mode - fail on any prompt

# CI environments auto-detected: GitHub Actions, GitLab CI, Jenkins, Travis
```

### Advanced Features

**Environment Restrictions:**
- **development** (default): Standard SafeGIT protections
- **staging**: Standard protections, similar to development
- **production**: Maximum restrictions
  - No force pushes allowed
  - No `reset --hard` allowed
  - No `clean -fdx` allowed
  - No rebasing allowed

**Work Mode Restrictions:**
- **normal** (default): Standard SafeGIT behavior
- **code-freeze**: Only read operations and hotfix branches allowed
  - Blocks: push, commit, merge, rebase, reset, clean
  - Exception: Commands containing "hotfix" or "HOTFIX" are permitted
- **maintenance**: Standard behavior (reserved for future features)
- **paranoid**: Allowlist approach, only safe commands permitted
  - Allowed: status, log, diff, fetch, show, ls-files, branch*, tag*, remote*
  - branch: No deletion (-d, -D, --delete)
  - tag: Only listing (-l, --list, -n)
  - remote: Only show/get-url/-v

**Risk-Based Confirmations:**
- Low risk: Standard Y/n confirmation
- High risk: Typed phrases ("PROCEED", "DELETE", etc.)
- Protected branches: Enhanced confirmation ("I understand the protection risks")
- Critical operations: Multiple typed confirmations + branch name verification

**Graduated Safety Levels (v2.0):**
- **Safe Operations** (work with `--yes`): add, commit, pull, fetch, status, log
- **Medium Risk** (require `--yes` with warnings): checkout, merge, rebase, cherry-pick
- **High Risk** (require `--force-yes`): reset --hard, clean -fdx, push --force, branch -D

**CI/CD Integration Examples:**
```yaml
# GitHub Actions
- name: Safe Deploy
  env:
    SAFEGIT_ASSUME_YES: 1
  run: |
    safegit add .
    safegit commit -m "Deploy: ${{ github.sha }}"
    safegit push

# For dangerous operations in CI
- name: Force Reset
  env:
    SAFEGIT_FORCE_YES: 1
  run: safegit reset --hard origin/main
```

**Recovery System:**
- Complete undo history with metadata (branch, HEAD, files affected)
- Recovery scripts generated for each operation
- Multi-level undo capability
- Reflog integration for advanced recovery

**Safety Analysis:**
- Branch protection detection (GitHub/GitLab/Bitbucket/Azure)
- Upstream divergence analysis with conflict risk assessment  
- File impact analysis (lines changed, files affected, categories)
- Cross-platform atomic file operations prevent corruption

### Troubleshooting

**If dangerous commands still execute:**
- Verify SafeGIT is installed: `which git` should point to SafeGIT
- Check alias: `alias git` should show SafeGIT path
- Test: `git --dry-run reset --hard` should show SafeGIT interception

**Common Issues:**
- Commands bypass SafeGIT: Install alias or PATH override
- Permission errors: `chmod +x safegit.py`
- Import errors: Ensure Python 3+ and required modules
- Non-interactive failures: Check `env | grep SAFEGIT` for proper environment
- CI detection: SafeGIT auto-detects CI environments via standard env vars

## Git Workflow Commands

**CRITICAL: ALL git operations MUST use SafeGIT - NO EXCEPTIONS**

**✅ GIT SAFETY ACTIVE**: Direct git commands are BLOCKED. You can work with complete confidence knowing that accidental data loss is prevented. All git operations automatically go through SafeGIT's protection system.

**Mandatory SafeGIT Usage**: All git commands must use SafeGIT via the wrapper:
- ❌ BLOCKED: `git add`, `git commit`, `git push`, `git reset`, etc.
- ✅ USE: `./run_any_python_tool.sh safegit.py add`, `./run_any_python_tool.sh safegit.py commit`, etc.

This applies to ALL git commands including: add, commit, push, pull, reset, revert, checkout, stash, merge, rebase, cherry-pick, clean, restore, rm.

**Why SafeGIT is Mandatory**:
- Prevents accidental data loss from dangerous operations
- Provides automatic backups before destructive commands
- Requires typed confirmations for high-risk operations
- Offers recovery instructions and undo capabilities

### Streamlined Git Sequences

**GIT SEQ 1** - Auto-commit with generated message:
1. Stage all files you modified/created
2. Analyze diff of staged files
3. Generate commit message from changes
4. **ASK USER FOR CONFIRMATION BEFORE COMMITTING**

**GIT SEQ 1 PUSH** - Same as SEQ 1 + push (requires confirmation)
**GIT SEQ 2** - Commit with confirmation message shown first
**GIT SEQ 2 PUSH** - Same as SEQ 2 + push (requires confirmation)
**GIT SEQ STAGE** - Smart staging with approval
**GIT PRs** - PR analysis
**SYNC CHECK** - Check for CLAUDE.md updates

### Commit Message Generation Pattern

```bash
# Analyze changes for commit message
safegit diff --cached --name-status | head -20
safegit diff --cached --stat

# Generate message based on:
# - feat: New features
# - fix: Bug fixes  
# - refactor: Code restructuring
# - docs: Documentation only
# - test: Test additions/changes
# - perf: Performance improvements
```

### Implementation Examples

**When user says "GIT SEQ 1":**
```bash
# 1. Stage your changes
safegit add -u  # Stages modified/deleted files you touched
safegit add <new-files>  # Add any new files you created

# 2. Analyze and generate message
safegit diff --cached --stat
# Analyze changes and generate: "feat: add time-based stop loss with 3 interpolation modes"

# 3. Commit immediately AFTER GETTING CONFIRMATION
safegit commit -m "feat: add time-based stop loss with 3 interpolation modes"
```

**When user says "GIT SEQ STAGE":**
```bash
# Track all files modified in this session
safegit status --porcelain | grep -E '^( M|\?\?)' | awk '{print $2}'
# Review each file to ensure you actually modified it
# Stage only files you touched
safegit add src/main/java/com/.../FileYouModified.java
safegit status  # Show what's staged
```

## Release Workflow System

**IMPORTANT**: The code-intelligence-toolkit has an automated release workflow for creating new versions.

### Release Workflow Overview

The project uses a two-repository system:
- **Main development repo**: `~/DemoStrategies/Strategies/code-intelligence-toolkit` (this repo)
- **Desktop release repo**: `~/Desktop/code-intelligence-toolkit` (for public releases)

### Automated Release Process

**Command**: `./release_workflow.sh [patch|minor|major] "Release description"`

**What it does**:
1. Checks for uncommitted changes in both repositories
2. Syncs changed files from main to desktop repo (using `sync_tools_to_desktop.py`)
3. Creates a commit in desktop repo with proper message
4. Creates and pushes a version tag (e.g., v1.0.3)
5. Creates a GitHub release with release notes

**Examples**:
```bash
# Patch release (bug fixes)
./release_workflow.sh patch "Fixed non-interactive mode in safe_file_manager.py"

# Minor release (new features)
./release_workflow.sh minor "Added new AST analysis tools and enhanced error handling"

# Major release (breaking changes)
./release_workflow.sh major "Complete redesign of tool architecture with breaking API changes"
```

### Files Excluded from Desktop Repository

These files exist only in the main repo and are automatically excluded:
- `release_workflow.sh` - The release script itself
- `RELEASE_WORKFLOW_GUIDE.md` - Release workflow documentation
- `sync_tools_to_desktop.py` - The sync script (though it may exist in desktop for other purposes)

### Manual Release Steps (if needed)

If the automated workflow fails, you can manually:
```bash
# 1. Sync files
python3 sync_tools_to_desktop.py --force

# 2. Go to desktop repo
cd ~/Desktop/code-intelligence-toolkit

# 3. Commit changes
git add -A
git commit -m "chore: sync tools from main repository for v1.0.X"

# 4. Create and push tag
git tag -a v1.0.X -m "Release v1.0.X: Description"
git push origin master
git push origin v1.0.X

# 5. Create GitHub release (if gh CLI installed)
gh release create v1.0.X --title "v1.0.X: Description" --notes "Release notes..."
```

### Version Guidelines

- **Patch** (x.x.1): Bug fixes, typos, documentation updates
- **Minor** (x.1.0): New features, significant improvements, backward compatible
- **Major** (1.0.0): Breaking changes, major refactoring, API changes

## Warning Suppressions

**CRITICAL**: The build.gradle suppresses many compiler warnings. Since compile-time checks are disabled:
- Use properly typed generics: `List<String>` not `List`
- Check types before casting: `if (obj instanceof MyType)`
- Use @SuppressWarnings sparingly

## Class Versioning and File Creation Guidelines

**CRITICAL: When creating new versions, ALWAYS copy the original and then edit**

```bash
# CORRECT: Copy then edit
cp MultiLevelOrderBookV4.java MultiLevelOrderBookV5.java
# Then edit V5.java to add new features
```

**Why**: Preserves working functionality, edge case handling, performance optimizations, and subtle bug fixes.

## Logging Guidelines

**CRITICAL: Only log state transitions, not every occurrence**

```java
// CORRECT: Log state transitions only
if (isStaleDataNow && !wasStaleDataLastTime) {
    MaindebugUI.log("Entering stale data period");
}

// WRONG: Creates log bottleneck
if (isStaleDataNow) {
    MaindebugUI.log("Stale data detected"); // Logs thousands of times!
}
```

## Bulk Text Processing Guidelines

**CRITICAL: Always test bulk operations on dummy files first**

```bash
# 1. Test on dummy data
echo "sample text" > test.txt
sed -E 'pattern' test.txt

# 2. Apply to small subset
find src/test -name "*.java" | head -3 | xargs sed -i.bak 'command'

# 3. Verify before full run
./gradlew compileTestJava 2>&1 | rg -c "error:"
```

**Key**: Use simple patterns, verify incrementally.

## Build System and Development Commands

### Core Build Commands

**AUTOMATIC CLEAN BUILDS: The `build` task now automatically runs `clean` first**

```bash
# Standard build command (automatically does clean build)
./gradlew build -x test

# Full build with tests
./gradlew build

# Run tests separately
./gradlew test
```

**Build Configuration:**
- Gradle daemon disabled - no background processes
- Build always runs clean first
- Every build is guaranteed fresh with no stale classes
- Prevents NoClassDefFoundError from stale inner classes

### JAR Output Location
**IMPORTANT**: JAR files created on Desktop (`~/Desktop/`):
- `bm-strategies.jar` - Regular JAR
- `bm-strategies-fat.jar` - **Fat JAR with all dependencies (required for deployment)**

### Trade Log Output Location
**Trade logs saved to**: `~/Desktop/TradeLog/`

### Post-Task Completion Protocol
Always build after finishing any significant task:
```bash
./gradlew build -x test
```

### Enterprise Java Refactoring Engine Setup

**Build the Spoon-based refactoring engine:**
```bash
# Build the engine
./build_java_engine_gradle.sh

# Verify build
ls -la spoon-refactor-engine.jar

# Test the engine
java -jar spoon-refactor-engine.jar --help
```

**Usage patterns:**
```bash
# Direct engine usage
java -jar spoon-refactor-engine.jar --file MyClass.java --line 42 --old oldVar --new newVar

# Python wrapper (recommended for enhanced features)
./run_any_python_tool.sh replace_text_ast_v3.py --file MyClass.java oldVar newVar --line 42

# Dry-run mode
java -jar spoon-refactor-engine.jar --file MyClass.java --line 42 --old oldVar --new newVar --dry-run
```

## Architecture Overview

### Core Framework
- **Bookmap Layer1 API**: Foundation for market data and trading
- **CustomModule Interface**: Base for indicators and strategies
- **Annotation-driven Configuration**: `@Layer1SimpleAttachable`, `@Parameter`
- **Event-driven Architecture**: Real-time processing via listeners

### Major Component Categories

#### Market Microstructure Analysis
- **LiquidityTracker Family** (V1-V8): Multi-level liquidity imbalance detection
- **QuotesDelta Family** (V1-V8): Order flow and delta analysis
- **MultiLevelOrderBook Components**: Advanced order book data structures

#### Algorithmic Trading Strategies
- **VWAP Strategies**: `NubiaAutoMidasAnchoredVWAP*` family
- **Technical Analysis**: EMA strategies, ATR-based systems
- **STRAT Pattern Framework**: `StratBar`, `StratPatternDetector`

#### Order Management and Risk
- **Order Execution**: `OrderSender*`, `OrderSenderController*`
- **Risk Management**: `DrawdownGuard`, `TrailingStopController*`
- **Performance Tracking**: Comprehensive metrics and dashboards

### Bookmap Timestamp Format

**CRITICAL**: Understanding Bookmap timestamps is essential for time-based calculations:

- **Format**: Bookmap timestamps are in **nanoseconds since Unix epoch** (January 1, 1970 UTC)
- **Type**: `long` values representing nanoseconds
- **Conversion to milliseconds**: Divide by 1,000,000 (e.g., `timestamp / 1_000_000`)
- **Conversion from System.currentTimeMillis()**: Multiply by 1,000,000

**Examples**:
```java
// Convert Bookmap timestamp to milliseconds
long bookmapTimestampNanos = someTimestamp; // From Bookmap API
long millisSinceEpoch = bookmapTimestampNanos / 1_000_000;

// Convert System.currentTimeMillis() to Bookmap format
long systemMillis = System.currentTimeMillis();
long bookmapFormatNanos = systemMillis * 1_000_000;

// Calculate latency (system arrival time - exchange timestamp)
long exchangeTimeMillis = timestampNanos / 1_000_000;
long feedLatencyMillis = System.currentTimeMillis() - exchangeTimeMillis;

// In onTrade context (timestamps vary by API method)
public void onTrade(double price, int size, TradeInfo info) {
    long tradeTimestampNanos = info.timestamp; // Available in some contexts
    // ... latency calculation
}
```

**Important Notes**:
- In **live/realtime mode**: Timestamps represent actual exchange time
- In **replay mode**: Timestamps are historical but maintain nanosecond precision
- Always use nanosecond precision for calculations to avoid precision loss
- Timestamp availability varies by API context (not all methods provide `TradeInfo.timestamp`)
- When comparing Bookmap timestamps with system time, always convert to the same unit
- Common timestamp sources: `onTrade()` parameters, event timestamps, sweep start/end times

### Order Book Price Ordering Convention

**CRITICAL**: Specific ordering convention based on `OrderBookUtils`:

- **Bid Books**: Reverse order (highest price first)
  - `TreeMap<Integer, Integer> bidBook = new TreeMap<>(Comparator.reverseOrder())`
  - FirstKey() returns highest price (best bid)

- **Ask Books**: Natural order (lowest price first)  
  - `TreeMap<Integer, Integer> askBook = new TreeMap<>()`
  - FirstKey() returns lowest price (best ask)

### MultiLevelOrderBook Configuration

**Level Depths**: `levelDepthsCSV="5,10,15,21,30"` defines cumulative levels

**Getting Liquidity Sums**:
```java
int[] bidSums = multiLevelOrderBook.getAllExponentialSums(true);  // bid side
int[] askSums = multiLevelOrderBook.getAllExponentialSums(false); // ask side
// bidSums[0] = sum of first 5 levels, bidSums[1] = sum of first 10 levels, etc.
```

## Parameter Setup and Usage

### @Parameter Annotation Guidelines

**CRITICAL**: The `@Parameter` annotation is used to create user-configurable settings in Bookmap indicators/strategies.

**Import Required**:
```java
import velox.api.layer1.simplified.Parameter;
```

**Supported Types** (MUST use wrapper classes, not primitives):
- ✅ `Integer` (not `int`)
- ✅ `Double` (not `double`) 
- ✅ `Boolean` (not `boolean`)
- ✅ `String`
- ✅ `Color`

**Basic Usage**:
```java
@Parameter(name = "MA Period", minimum = 5, maximum = 200)
private Integer maPeriod = 20;

@Parameter(name = "Threshold", minimum = 0.1, maximum = 10.0, step = 0.1)
private Double threshold = 1.5;

@Parameter(name = "Enable Feature")
private Boolean enableFeature = true;

@Parameter(name = "Symbol Prefix")
private String symbolPrefix = "ES";
```

**Advanced Features**:
```java
// HTML formatting in parameter names
@Parameter(name = "<html><b>Section Title</b><br>Parameter Name</html>")
private Integer value = 10;

// Reload on change (triggers reinitialization)
@Parameter(name = "Critical Setting", reloadOnChange = true)
private Integer criticalValue = 50;

// Step size for numeric parameters
@Parameter(name = "Price Level", minimum = 0.0, maximum = 100.0, step = 0.25)
private Double priceLevel = 50.0;
```

**Common Patterns**:
```java
// Using integer as scaled decimal (divide by 10 for 0.1-1.0 range)
@Parameter(name = "Smoothing Factor (0.1-1.0)", minimum = 1, maximum = 10)
private Integer smoothingFactorInt = 8; // Represents 0.8

// In code:
double smoothingFactor = smoothingFactorInt / 10.0;

// Enum-like behavior with integer
@Parameter(name = "Mode (0=Off, 1=Normal, 2=Aggressive)", minimum = 0, maximum = 2)
private Integer mode = 1;
```

**Examples from Production Code**:
- See `NubiaAutoMidasAnchoredVWAPV6_0_7.java` for extensive parameter usage
- See `QuotesDeltaV3.java` for calculator-based parameter pattern
- See `QuotesDeltaMultiLevelV5.java` for CSV string parameters

## Testing Framework

### Unit Testing Configuration
- **JUnit 4**: `junit:junit:4.13.2`
- **Mocking**: `mockito-core:3.12.4`

**IMPORTANT**: JUnit 4 parameter order differs from JUnit 5:
- `assertEquals(String message, Object expected, Object actual)` - message FIRST

### Parallel Test Execution
- Tests run in parallel across different classes
- Each test class gets its own JVM fork
- Custom in-memory Preferences avoids macOS locking
- Tests that took 100+ seconds now run in ~300ms

### Test Timing Framework
**CRITICAL: All test classes MUST extend `TimedTestBase`**

```java
import com.bookmap.api.simple.demo.utils.TimedTestBase;

public class MyNewTest extends TimedTestBase {
    @Test
    public void testSomeFeature() {
        // Timing is automatically handled by TimedTestBase
    }
}
```

**Features**: Automatic timing, >5 second warnings, build bottleneck identification.

### UI Tests in Headless Environments

**IMPORTANT**: UI tests that create Swing components may timeout in headless environments (CI/CD, servers without displays).

The project uses **conditional test exclusion** in `build.gradle`:

```gradle
test {
    // Only exclude UI tests if running in headless environment
    if (System.getenv("DISPLAY") == null && !System.getProperty("os.name").toLowerCase().contains("windows")) {
        // Likely headless environment on Unix/Linux
        exclude '**/NubiaHealthStatusUIV4Test.class'
        exclude '**/NubiaHealthStatusUIV4SimpleTest.class'
        exclude '**/OrdersTestUIV4Test.class'
        println "Running in headless environment - excluding UI tests"
    }
}
```

## Development Tools Overview

**Complete documentation: See TOOLS_DOCUMENTATION_2025.md**

### Essential Commands Reference

```bash
# Directory Operations
./run_any_python_tool.sh smart_ls.py src/ --ext java --sort size
./run_any_python_tool.sh find_files.py --ext py --newer-than 2d
./run_any_python_tool.sh recent_files.py --since 4h --by-dir
./run_any_python_tool.sh tree_view.py --max-depth 3 --ext java
./run_any_python_tool.sh dir_stats.py src/ --detailed

# Text Search (find_text_v7.py - ALL FEATURES + MULTILINE)
./run_any_python_tool.sh find_text_v7.py "pattern" --file file.java --ast-context
./run_any_python_tool.sh find_text_v7.py "TODO" --scope src/ -g "*.java" --extract-ranges --merge-ranges
./run_any_python_tool.sh find_text_v7.py "error" --file Handler.java --extract-block
./run_any_python_tool.sh find_text_v7.py --wholefile --file config.py
./run_any_python_tool.sh find_text_v7.py "calculatePrice" --extract-method --ast-context
./run_any_python_tool.sh find_text_v7.py --lines "1-10,25-30" --file MyClass.java
./run_any_python_tool.sh find_text_v7.py "pattern1|pattern2" --type regex --no-color -C 5
./run_any_python_tool.sh find_text_v7.py "class MyClass.*?^}" --type regex --multiline script.py  # Find entire class
./run_any_python_tool.sh find_text_v7.py '""".*?"""' --type regex --multiline -g "*.py"      # Find all docstrings
./run_any_python_tool.sh find_text_v7.py "TODO:.*\n.*Priority:.*High" --type regex --multiline  # Multi-line TODO

# AST Operations (Enhanced V2)
./run_any_python_tool.sh navigate_ast.py MyClass.java --to calculatePrice
./run_any_python_tool.sh method_analyzer_ast.py processOrder --file File.java
./run_any_python_tool.sh semantic_diff_v3.py FileV1.java FileV2.java
./run_any_python_tool.sh data_flow_tracker_v2.py --var x --file calc.py                # Track dependencies
./run_any_python_tool.sh data_flow_tracker_v2.py --var result --direction backward    # What affects result
./run_any_python_tool.sh replace_text_ast_v3.py --file file.py --line 42 old new
./run_any_python_tool.sh replace_text_ast_v3.py --file code.java --line 15 oldVar newVar --comments-only
./run_any_python_tool.sh replace_text_ast_v3.py --file script.py --line 20 oldStr newStr --strings-only
./run_any_python_tool.sh replace_text_ast_v3.py _ "TODO" "TODO:\n- Implement\n- Test" --comments-only --interpret-escapes --lang python --file app.py

# Unified Refactoring (NEW) - Language-aware auto-detection
./run_any_python_tool.sh unified_refactor_v2.py rename oldFunc newFunc --file script.py    # Python: auto-uses python_ast
./run_any_python_tool.sh unified_refactor_v2.py rename OldClass NewClass --file MyClass.java  # Java: auto-uses java_scope
./run_any_python_tool.sh unified_refactor_v2.py find calculatePrice --scope src/           # Mixed codebase: auto-detects per file
./run_any_python_tool.sh unified_refactor_v2.py analyze --file MyClass.java               # Backend auto-selected by file extension

# Text Operations (V8 Enhanced with Escape Sequences)
./run_any_python_tool.sh replace_text_v9.py "old" "new" file.java                          # Basic replacement
./run_any_python_tool.sh replace_text_v9.py "pattern" "replacement" . -g "*.java"         # Multi-file with glob
./run_any_python_tool.sh replace_text_v9.py "old" "new" --git-only --staged-only         # Git-aware replacement
./run_any_python_tool.sh replace_text_v9.py "fix" "repair" src/ --block-mode within      # Block-aware mode
./run_any_python_tool.sh replace_text_v9.py "PLACEHOLDER" "Line 1\nLine 2\nLine 3" file.txt --interpret-escapes  # Multi-line replacement
./run_any_python_tool.sh replace_text_v9.py "TAB" "Column1\tColumn2\tColumn3" data.csv --interpret-escapes       # Tab-separated values
./run_any_python_tool.sh replace_text_v9.py "OLD" "New\nMulti\nLine\nText" src/*.py --interpret-escapes         # Multi-line in multiple files
./run_any_python_tool.sh replace_text_v9.py "TODO" "DONE" script.py --comments-only --lang python  # Comments only (requires --lang)
./run_any_python_tool.sh replace_text_v9.py "old" "new" code.rb --strings-only --lang ruby        # Strings only (requires --lang)
echo "test" | ./run_any_python_tool.sh replace_text_v9.py "test" "exam" - --interpret-escapes    # Process from stdin

# File Operations
./run_any_python_tool.sh safe_move.py move file.txt dest/
./run_any_python_tool.sh organize_files.py ~/Downloads --by-ext
./run_any_python_tool.sh refactor_rename_v2.py --replace oldVar newVar --in "src/**/*.py"

# Git Operations
./run_any_python_tool.sh git_commit_analyzer.py --seq1
./run_any_python_tool.sh git_commit_analyzer.py --stage-suggestions
./run_any_python_tool.sh git_commit_analyzer.py --sync-check

# Code Analysis
./run_any_python_tool.sh dead_code_detector.py src/ --confidence high
./run_any_python_tool.sh suggest_refactoring.py file.java
./run_any_python_tool.sh analyze_internal_usage.py src/

# Error Monitoring
./run_any_python_tool.sh analyze_errors.py --recent 10
./run_any_python_tool.sh error_analyzer.py --analyze --hours 2
./run_any_python_tool.sh error_dashboard.py --days 7
./run_any_python_tool.sh analyze_errors.py --clear
./run_any_python_tool.sh error_dashboard_v2.py --clear
```

### Common Flags Reference

**Compile checking**: `--check-compile` / `--no-check-compile`
**Automation**: `--yes` (skip confirmations), `--json` (structured output)
**Retry config**: `--max-retries N`, `--retry-delay S`, `--no-retry`
**AST context**: `--ast-context` / `--no-ast-context`
**Verbosity**: `-v` / `-q`

### Non-Interactive Mode Support

Many Python tools now support non-interactive mode for CI/CD and automation:

**Supported Tools:**
- `safe_file_manager.py` - Full non-interactive support (SFM_ASSUME_YES=1)
- `safe_move.py` - Non-interactive undo operations (--yes --non-interactive)
- `replace_text_ast_v3.py` - Batch operations without prompts (--no-confirm or --yes)
- `safegit.py` - CI/CD mode with auto-detection and --force-yes

**Configuration Methods (in priority order):**
1. Command-line flags: `--yes`, `--non-interactive`, `--no-confirm`
2. Environment variables: `TOOL_ASSUME_YES=true`, `TOOL_NONINTERACTIVE=true`
3. Config file (.pytoolsrc): `assume_yes = true`, `non_interactive = true`

**Examples:**
```bash
# Automation with environment variables
export SAFE_MOVE_ASSUME_YES=1
./run_any_python_tool.sh safe_move.py undo --interactive

# Command-line flags
./run_any_python_tool.sh replace_text_ast_v3.py old new --yes --non-interactive *.py

# Config file approach (.pytoolsrc)
[safe_file_manager]
non_interactive = true
assume_yes = true
```


## Java Refactoring Tools (JavaRefactorCLI)

```bash
# Using gradle
./gradlew -q runMain -PmainClass=com.bookmap.tools.JavaRefactorCLI --args="<command> <args>"

# Common commands
list-methods <file>
list-invocations <file> <method>
remove-sout <file>
rename-method <file> <oldName> <newName>
```

## Trade Reason System

**CRITICAL**: Every order must have meaningful trade reason with parameters.

See **TRADE_REASON_SYSTEM_GUIDE.md** for implementation guidelines.

## ManagedUIBase and ManagedSingletonUI Usage

**CRITICAL: Avoid duplicate initialization calls**

```java
// CORRECT - Let parent handle initialization
private MyUIClass() {
    super();  // Parent calls initialize() and setRunning()
    initializeMyComponents();
}

// WRONG - Causes IllegalStateException
private MyUIClass() {
    super();
    initialize();     // ❌ DUPLICATE!
    setRunning();     // ❌ DUPLICATE!
}
```

### BookmapTimeDistributorV2 Setup

**Time distributor must be created FIRST in initialize()**

```java
this.timeDistributor = new BookmapTimeDistributorV2(
    "StrategyName",
    () -> this.currentTimestampNanos,  // Lambda to volatile field
    50,  // Update interval ms
    ZoneId.systemDefault()
);
```

## Common Pitfalls and Solutions

### Event Listener Memory Leaks
Always remove listeners in `stop()`:
```java
@Override
public void stop() {
    if (depthListener != null) {
        api.removeDepthDataListener(depthListener);
    }
}
```

### Threading Context
- Bookmap events arrive on market data threads (NOT EDT)
- UI updates need `SwingUtilities.invokeLater()`
- Use concurrent collections for thread safety

### Bash Session Troubleshooting
If encountering bizarre bash errors:
1. Use fresh subshell: `bash -c 'your command here'`
2. Test with absolute paths: `/usr/bin/ls` instead of `ls`
3. Check environment: `echo $PATH`

---

**IMPORTANT**: When starting work on this codebase, begin with: "I have read the Claude.md file and am ready to start!" followed by current date and time.

**CRITICAL**: Immediately after acknowledging:
1. Check if CLAUDE.md modified: `safegit status CLAUDE.md`
2. If modified, review changes: `safegit diff CLAUDE.md | head -200`
3. Run wrapper script to pre-approve:
   - `./run_any_python_tool.sh --help`

To get date: `date '+%B %d, %Y at %I:%M %p %Z'`

# Important Instruction Reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## Documentation File Guidelines

**CRITICAL: When creating any .md documentation file, ALWAYS include at the top:**

```markdown
# [Document Title]

**Related Code Files:**
- `path/to/SpecificFile1.java` - Brief description of what this file does
- `path/to/SpecificFile2.java` - Brief description of what this file does
- `path/to/package/*` - If documenting an entire package

---

[Rest of documentation content]
```

This header block must appear immediately after the title and before any other content. It helps readers quickly identify which code files they should reference alongside the documentation.