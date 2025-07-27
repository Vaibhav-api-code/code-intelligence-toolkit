#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Universal Python Tool Runner for Java Analysis  
# This script allows running any Python analysis tool with a single approval
# Now supports unified configuration system via .pytoolsrc
# Automatic error logging enabled for all tools (disable with DISABLE_ERROR_LOGGING=1)
#
# Author: Vaibhav-api-code
# Co-Author: Claude Code (https://claude.ai/code)
# Created: 2025-01-01
# Updated: 2025-07-23
# License: Mozilla Public License 2.0 (MPL-2.0)

set -Eeuo pipefail
IFS=$'\n\t'

# Resolve the real script location (handles symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [[ -h "$SOURCE" ]]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Preflight validation function
preflight_check() {
    local tool_name="$1"
    local tool_path="$2"
    shift 2
    local args=("$@")
    
    # Store any warnings to display
    local warnings=""
    
    # Check 1: Verify script directory exists and is accessible
    if [ ! -d "$SCRIPT_DIR" ]; then
        echo ""
        echo "❌ Error: Script directory not found: $SCRIPT_DIR"
        return 1
    fi
    
    # Check 2: Verify tool path is valid
    if [ ! -f "$tool_path" ]; then
        echo ""
        echo "❌ Error: Tool not found: $tool_path"
        echo "   Expected location: $tool_path"
        return 1
    fi
    
    # Check 3: Verify tool is readable
    if [ ! -r "$tool_path" ]; then
        echo ""
        echo "❌ Error: Tool is not readable: $tool_path"
        echo "   Check file permissions"
        return 1
    fi
    
    # Check 4: Verify Python3 is available
    if ! command -v python3 &> /dev/null; then
        echo ""
        echo "❌ Error: python3 command not found"
        echo "   Please install Python 3"
        return 1
    fi
    
    # Check 5: Check for suspicious path traversal in arguments
    for arg in "${args[@]}"; do
        if [[ "$arg" == *"../"* ]] || [[ "$arg" == *"..\\"* ]]; then
            warnings="${warnings}⚠️  Warning: Potential path traversal in argument: $arg\n"
            warnings="${warnings}   Consider using absolute paths instead\n"
        fi
    done
    
    # Check 6: Verify working directory is accessible
    if ! pwd &> /dev/null; then
        echo ""
        echo "❌ Error: Current working directory is not accessible"
        echo "   The directory may have been deleted or you may lack permissions"
        return 1
    fi
    
    # Check 7: Check for required environment (optional warnings)
    if [ -z "${HOME:-}" ]; then
        warnings="${warnings}⚠️  Warning: HOME environment variable not set\n"
        warnings="${warnings}   Some tools may not function correctly\n"
    fi
    
    # Check 8: Verify the tool has a valid Python shebang or is a Python file
    local first_line=$(head -n 1 "$tool_path" 2>/dev/null)
    if [[ ! "$first_line" =~ ^#!.*python ]] && [[ ! "$tool_name" =~ \.py$ ]]; then
        warnings="${warnings}⚠️  Warning: Tool may not be a Python script: $tool_name\n"
        warnings="${warnings}   First line: $first_line\n"
    fi
    
    # Check 9: Check available disk space (warning only)
    if command -v df &> /dev/null; then
        local available_space=$(df -k . 2>/dev/null | awk 'NR==2 {print $4}')
        if [ -n "$available_space" ] && [ "$available_space" -lt 1048576 ]; then  # Less than 1GB
            warnings="${warnings}⚠️  Warning: Low disk space available ($(( available_space / 1024 ))MB)\n"
            warnings="${warnings}   Some operations may fail\n"
        fi
    fi
    
    # Check 10: Validate Python version
    local python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    if [ -n "$python_version" ]; then
        local major_version=$(echo "$python_version" | cut -d. -f1)
        local minor_version=$(echo "$python_version" | cut -d. -f2)
        if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 6 ]); then
            warnings="${warnings}⚠️  Warning: Python version $python_version detected\n"
            warnings="${warnings}   Python 3.6+ is recommended for optimal compatibility\n"
        fi
    fi
    
    # Display any warnings
    if [ -n "$warnings" ]; then
        printf "$warnings"
    fi
    
    return 0
}

# Function to display usage
usage() {
    echo "Usage: $0 [--skip-preflight] <tool_name> [arguments...]"
    echo ""
    echo "Options:"
    echo "  --skip-preflight    Skip preflight validation checks (not recommended)"
    echo ""
    echo "Available tools:"
    echo "  Structure and Navigation:"
    echo "    check_java_structure.py - Validate Java source file structure and syntax"
    echo "    navigate.py - Navigate to specific methods/lines"
    echo "    extract_methods.py - Extract specific methods from large files"
    echo "    extract_class_structure.py - Get class overview"
    echo "    extract_block.py - Extract code blocks"
    echo "    show_structure_ast_v4.py - Main hierarchical code structure viewer with annotation filtering (RECOMMENDED)"
    echo "    show_structure_ast.py - Legacy version (redirects to v4)"
    echo ""
    echo "  Search and Find:"
    echo "    find_text.py - Enhanced text search with block extraction, robustness improvements, context display, ± syntax, auto-find (v6)"
    echo "                   NEW: AST context capability with interactive navigation for Python files"
    echo "                   AST context appears on a separate line above matches with format \"AST context of line X - [Class → method]\""
    echo "                   (search in files, find by name/size/date, find duplicates, AST context)"
    echo ""
    echo "  Analysis Tools:"
    echo "    find_references.py, find_references_rg.py - Find all references to a method/field/class"
    echo "    analyze_dependencies.py, analyze_dependencies_rg.py - Analyze file dependencies"
    echo "    analyze_unused_methods.py, analyze_unused_methods_rg.py - Find unused methods"
    echo "    trace_calls.py, trace_calls_rg.py - Trace method call hierarchies (30s timeout)"
    echo "    (Note: Non-rg versions may automatically redirect to faster rg versions)"
    echo "    (Note: trace_calls has 30s timeout protection, set TRACE_CALLS_TIMEOUT to change)"
    echo ""
    echo "  Smart Code-Aware Tools (NEW):"
    echo "    smart_find_references.py - Language-aware reference search with semantic analysis"
    echo "    analyze_usage.py - Multi-file correlation analysis for dependencies and call patterns"
    echo "    method_analyzer.py - Comprehensive method usage analysis with parameter tracking"
    echo "    method_analyzer_ast.py - AST-based call flow analysis with perfect accuracy (NEW)"
    echo "    pattern_analysis.py - Pattern frequency analysis with temporal trends"
    echo "    log_analyzer.py - Log pattern frequency and timeline analysis with anomaly detection"
    echo "    smart_refactor_v2.py - Scope-aware refactoring with conflict detection"
    echo "    cross_file_analysis.py - Cross-file dependency analysis for finding all callers"
    echo "    cross_file_analysis_ast.py - Enhanced with AST-based caller identification"
    echo "    semantic_diff_v3.py - Main semantic diff tool with enterprise-grade features and impact scoring"
    echo "    navigate_ast.py - AST-based definition finder with 100% accuracy (NEW)"
    echo "    replace_text_ast.py - Scope-aware variable renaming using AST (NEW)"
    echo "    data_flow_tracker.py - Track variable dependencies and data flow through code (NEW)"
    echo ""
    echo "  Refactoring and Quality:"
    echo "    suggest_refactoring.py - Get refactoring suggestions for Java code complexity"
    echo "    analyze_internal_usage.py - Analyze internal method usage (supports files and directories)"
    echo "    smart_diff.py - Smart diff between files"
    echo "    replace_text_v8.py - Enhanced text replacement tool (V8) with escape sequence support"
    echo "                     ALL FEATURES: V7 features + escape sequence interpretation (\\n, \\t, \\r, \\x, \\u)"
    echo "                     (ripgrep search, block-aware modes, JSON pipeline, multi-strategy replacement)"
    echo "    replace_text_ast.py - Definitive AST replacement (V2 consolidated) with enhanced features"
    echo "                         ALL FEATURES: V7 compatibility (block-mode, git integration, comments-only, strings-only)"
    echo "                         (scope-aware renaming, symbol discovery, batch rename, JSON pipeline integration)"
    echo "    ast_refactor.py - AST-based intelligent code refactoring (Python)"
    echo "                     (type-aware renaming, intelligent transformations, syntax preservation)"
    echo "    unified_refactor.py - Professional unified refactoring tool with multiple backends"
    echo "                        - Backends: python_ast, rope, java_scope, text_based"
    echo "                        - Commands: rename, rename-project, find, analyze, replace"
    echo "                        - NEW: Unified diff previews, AST-guided rope targeting, JSON pipeline"
    echo "                        - Multi-language support with automatic engine selection"
    echo ""
    echo "  Wrappers and Utilities:"
    echo "    safe_java_tools_fixed.py - Fixed wrapper for pipelines"
    echo "    safe_java_tools.py - Original wrapper"
    echo "    java_tools_batch.py - Batch processing"
    echo ""
    echo "  Code Quality Analysis:"
    echo "    dead_code_detector.py - Multi-language dead code finder (Python, Java, JavaScript)"
    echo "                          - Now with 60s timeout protection (configurable via DEAD_CODE_TIMEOUT)"
    echo "                          - Confidence levels: high/medium/low"
    echo "                          - Features: --confidence, --language, --format, --ignore-pattern"
    echo ""
    echo "  Git and Version Control:"
    echo "    git_commit_analyzer.py - Analyze staged changes and generate commit messages"
    echo "                           - Supports GIT SEQ 1/2 workflows from CLAUDE.md"
    echo "                           - Features: --full-diff, --sync-check, --stage-suggestions, --seq1"
    echo "    safegit.py - Enterprise git safety wrapper preventing data loss (v2.0)"
    echo "                - 37+ dangerous operations intercepted with automatic backups"
    echo "                - Non-interactive mode for CI/CD (--yes, --force-yes, --non-interactive)"
    echo "                - Multi-level undo system with recovery scripts"
    echo "                - AI agent protection and educational mode"
    echo ""
    echo "  Directory and File Management (NEW):"
    echo "    smart_ls.py - Smart directory listing with icons, filtering, and rich formatting"
    echo "    find_files.py - Fast file finding with comprehensive filters (size, time, type, pattern)"
    echo "    recent_files.py - Find recently modified/created files with smart filtering"
    echo "    tree_view.py - Directory tree visualization with depth control and filtering"
    echo "    dir_stats.py - Comprehensive directory analysis with insights and statistics"
    echo "    ⚠️  NOTE: These tools now show ALL file types by default. Use --ext java for Java-only analysis"
    echo ""
    echo "  File Management - MANDATORY PRIMARY TOOL:"
    echo "    safe_file_manager.py - Complete file system operations with safety and validation"
    echo "                          (ALL operations: cat, copy, move, trash, list, cd, pwd, mkdir, chmod, etc.)"
    echo "                          MANDATORY for all file operations - replaces ALL built-in tools"
    echo ""
    echo "    ⚠️  SHELL PARSING NOTE for 'create' command:"
    echo "    When creating files with complex content containing shell keywords (elif, done, fi, etc.),"
    echo "    use --from-stdin with here-docs instead of --content to avoid shell parsing errors:"
    echo ""
    echo "    cat << 'EOF' | ./run_any_python_tool.sh safe_file_manager.py create script.py --from-stdin"
    echo "    #!/usr/bin/env python3"
    echo "    if condition:"
    echo "        pass"
    echo "    elif other_condition:"
    echo "        pass"
    echo "    EOF"
    echo ""
    echo "    ⚠️  IMPORTANT: The 'EOF' marker must be on its own line with no spaces before or after."
    echo "    Never copy the 'EOF' line into your file content!"
    echo ""
    echo "  Bulletproof File Operations V2 (Legacy - use safe_file_manager.py instead):"
    echo "    safe_move.py - Safe file operations with undo capability and compile checking"
    echo "                  (move/copy files safely, automatic backups, full undo history)"
    echo "    organize_files.py - File organization with manifest/undo system and archiving"
    echo "                       (organize by extension, date, size with complete reversibility)"
    echo "    refactor_rename.py - AST-based code-aware file and symbol renaming"
    echo "                        (batch rename files and update imports/references)"
    echo ""
    echo "  Configuration Management (NEW):"
    echo "    common_config.py - Unified configuration system for all tools via .pytoolsrc"
    echo "                      (create defaults, show config, find project root)"
    echo "                      All tools now automatically load defaults from .pytoolsrc"
    echo "                      Command-line arguments always override config file settings"
    echo ""
    echo "  Error Monitoring and Analysis (NEW):"
    echo "    analyze_errors.py - Analyze error logs to find patterns and insights"
    echo "                       (view recent errors, failure patterns, time distributions)"
    echo "    error_dashboard.py - Visual error summary with actionable insights"
    echo "                        (categorizes errors, shows problematic tools, recommendations)"
    echo "    error_logger.py - Core error logging system (automatically used by all tools)"
    echo "    Note: Error logging is automatically enabled for all tool executions"
    echo "          Set DISABLE_ERROR_LOGGING=1 to disable error logging"
    echo ""
    echo "  Specialized Tools:"
    echo "    multiline_reader.py - Enhanced multiline reader with flexible line range specifications"
    echo ""
    echo "Examples:"
    echo ""
    echo "  MANDATORY File Operations (use safe_file_manager.py for EVERYTHING):"
    echo "  $0 safe_file_manager.py cat file.txt                    # Read file"
    echo "  $0 safe_file_manager.py copy source.txt dest.txt        # Copy file"
    echo "  $0 safe_file_manager.py move old.txt new.txt            # Move/rename"
    echo "  $0 safe_file_manager.py trash unwanted.txt              # Safe delete"
    echo "  $0 safe_file_manager.py list /directory                 # List files"
    echo "  $0 safe_file_manager.py cd /path/to/dir                 # Validate directory"
    echo "  $0 safe_file_manager.py pwd                             # Current directory"
    echo "  $0 safe_file_manager.py mkdir newdir                    # Create directory"
    echo ""
    echo "  Code Analysis Examples:"
    echo "  $0 check_java_structure.py MyClass.java"
    echo "  $0 find_references_rg.py configure --type method"
    echo "  $0 navigate.py LargeFile.java --to line:1500"
    echo "  $0 extract_methods.py ExampleController.java --list"
    echo "  $0 show_structure_ast.py MyClass.java --json"
    echo "  $0 safe_java_tools_fixed.py --pipeline analyze-all MyClass.java"
    echo ""
    echo "  # Skip preflight checks (use only if necessary):"
    echo "  $0 --skip-preflight find_text.py 'pattern' --file file.java"
    echo ""
    echo "Smart Code-Aware Tools examples (STANDARDIZED INTERFACES ⭐):"
    echo "  $0 smart_find_references.py MyClass --scope src/ --type method_call"
    echo "  $0 analyze_usage.py processItem --scope . --show-frequency"
    echo "  $0 method_analyzer_ast_v2.py calculateResult --scope . --show-args --trace-flow"
    echo "  $0 pattern_analysis.py PATTERN --scope . --type regex --show-frequency"
    echo "  $0 log_analyzer.py --pattern ERROR --files ./logs/ --timeline"
    echo "  $0 smart_refactor_v2.py rename --old-name oldMethod --new-name newMethod --file MyClass.java --dry-run"
    echo "  $0 cross_file_analysis.py processItem --scope src/ --analyze"
    echo "  $0 cross_file_analysis_ast.py processItem --scope . --max-depth 4"
    echo "  $0 semantic_diff_v3.py FileV1.java FileV2.java --logic-only"
    echo "  $0 semantic_diff_v3.py FileV1.java FileV2.java --risk-analysis --show-critical"
    echo "  $0 method_analyzer_ast_v2.py processData --file File.java --trace-flow"
    echo "  $0 method_analyzer_ast_v2.py processData --scope . --trace-flow"
    echo "  $0 navigate_ast_v2.py MyClass.java --to calculateValue"
    echo "  $0 navigate_ast_v2.py MyClass.java --line 42"
    echo "  $0 replace_text_ast.py --file utils.py --line 25 data payload  # AST-aware rename"
    echo "  $0 data_flow_tracker.py --var x --file calc.py                  # Track forward dependencies"
    echo "  $0 data_flow_tracker.py --var result --direction backward --file calc.py  # Track what affects result"
    echo "  $0 data_flow_tracker.py --var result --format graph --file module.py > flow.dot  # Generate dependency graph"
    echo ""
    echo "Enhanced Java refactoring with Spoon (NEW):"
    echo "  $0 replace_text_ast.py --file MyClass.java --line 42 oldVar newVar"
    echo "  $0 replace_text_ast.py --file MyClass.java --line 15 --dry-run methodName newMethodName"
    echo ""
    echo "Directory and File Management examples (NEW):"
    echo "  ⚠️  NOTE: Use --ext java when analyzing Java code (no longer default)"
    echo "  $0 smart_ls.py src/ --ext java --sort size --long          # List Java files by size"
    echo "  $0 smart_ls.py . --max 20                                   # List ALL files (--max is alias for --limit)"
    echo "  $0 find_files.py . --ext java --newer-than 2d              # Find recent Java files (specify --ext java)"
    echo "  $0 find_files.py . --ext py --min-size 1KB --newer-than 2d --max 50  # Find recent Python files"
    echo "  $0 recent_files_v2.py --since 4h --ext java                # Recent Java files (specify --ext java)"
    echo "  $0 recent_files_v2.py --since 4h --by-dir --show-size      # ALL recent files grouped by directory"
    echo "  $0 tree_view.py . --max-depth 3 --ext java --max 10        # Java tree view (specify --ext java)"
    echo "  $0 tree_view.py . --max-depth 3 --show-size                # ALL files tree view"
    echo "  $0 dir_stats.py src/ --ext java --detailed                 # Java-only analysis (specify --ext java)"
    echo "  $0 dir_stats.py src/ --show-files --show-dirs --detailed   # ALL files comprehensive analysis"
    echo ""
    echo "Configuration Management examples (NEW):"
    echo "  $0 common_config.py --create                               # Create default .pytoolsrc config"
    echo "  $0 common_config.py --show                                 # Show current configuration"  
    echo "  $0 common_config.py --find-root                            # Find project root directory"
    echo "  # Note: All tools now automatically load defaults from .pytoolsrc"
    echo ""
    echo "Error analysis examples (NEW):"
    echo "  $0 analyze_errors.py --recent 10          # Show last 10 errors"
    echo "  $0 analyze_errors.py --days 7             # Analyze errors from last week"
    echo "  $0 analyze_errors.py --tool smart_ls.py   # Errors for specific tool"
    echo "  $0 analyze_errors.py --patterns           # Show failure patterns"
    echo "  $0 analyze_errors.py --summary            # Show error summary statistics"
    echo "  # Note: Errors are automatically logged to ~/.pytoolserrors/"
    echo ""
    echo "replace_text_v8.py examples (V8 - Enhanced with escape sequence support):"
    echo "  ⚠️  IMPORTANT: Order is <old_text> <new_text> <paths>"
    echo "  $0 replace_text_v8.py oldMethod newMethod MyClass.java --whole-word    # Safe variable renaming"
    echo "  $0 replace_text_v8.py 'TODO' 'DONE' . -r -g '*.java' --dry-run        # Multi-file replacement preview"
    echo "  $0 replace_text_v8.py oldValue newValue . -r --git-only -g '*.py'     # Only Git-tracked files"
    echo "  $0 replace_text_v8.py old new . -r --staged-only -g '*.java'          # Only staged files"
    echo "  # CONSOLIDATED: JSON pipeline support for find→replace workflows"
    echo "  $0 replace_text_v8.py --from-find-json search_results.json old new    # Use find_text results"
    echo "  # CONSOLIDATED: Block-aware replacement modes"
    echo "  $0 replace_text_v8.py old new MyClass.java --block-mode within         # Replace only within code blocks"
    echo "  $0 replace_text_v8.py old new MyClass.java --block-mode extract        # Extract and replace in blocks"
    echo "  # CONSOLIDATED: AST context display during replacement"
    echo "  $0 replace_text_v8.py calculateValue computeResult MyClass.java --ast-context  # Show class/method context"
    echo "  # V8 NEW: Escape sequence interpretation"
    echo "  $0 replace_text_v8.py 'PLACEHOLDER' 'Line 1\\nLine 2\\nLine 3' file.txt --interpret-escapes  # Multi-line replacement"
    echo "  $0 replace_text_v8.py 'TAB' 'Col1\\tCol2\\tCol3' data.txt --interpret-escapes                # Tab-separated values"
    echo "  $0 replace_text_v8.py 'X' 'Unicode:\\u2713\\nHex:\\x41' file.txt --interpret-escapes         # Unicode & hex chars"
    echo "  # ALL traditional features included:"
    echo "  $0 replace_text_v8.py 'TODO:.*' 'TODO: Updated' Config.java --regex --comments-only --lang java"
    echo "  $0 replace_text_v8.py value formattedValue File.java --whole-word        # Avoids value→formattedValueInUnits"
    echo "  # IMPORTANT: --comments-only and --strings-only require --lang flag:"
    echo "  $0 replace_text_v8.py 'TODO' 'DONE' script.py --comments-only --lang python       # Comments in Python"
    echo "  $0 replace_text_v8.py 'old' 'new' app.rb --strings-only --lang ruby              # Strings in Ruby"
    echo "  # Process from stdin (use - as filename):"
    echo "  echo 'test' | $0 replace_text_v8.py 'test' 'exam' - --interpret-escapes          # stdin input"
    echo ""
    echo "find_text.py examples (V6 COMPLETE - ALL FEATURES COMBINED):"
    echo "  ⚠️  IMPORTANT: Pattern first, then use --file OR --scope (not both)"
    echo "  ⚠️  REGEX PATTERNS: Use 'pattern1|pattern2' with --type regex (NOT \\|)"
    echo "  💡 REGEX HINT: If your pattern has special chars (|*+?^$[](){}\\), add --type regex"
    echo "  # Basic search with all context options:"
    echo "  $0 find_text.py 'TODO' --scope src/ -g '*.java' --ast-context      # AST context enabled"
    echo "  $0 find_text.py 'error' --file app.log -C 3 --no-color           # Context without colors"
    echo "  $0 find_text.py 'boolean' --file SweepDetector.java ±5            # ± syntax for context"
    echo "  # V6 NEW: Block and method extraction"
    echo "  $0 find_text.py 'if.*error' --type regex --extract-block          # Extract complete if blocks"
    echo "  $0 find_text.py 'calculatePrice' --extract-method --ast-context   # Extract methods with AST"
    echo "  $0 find_text.py 'process' --extract-method-alllines               # Extract methods (no size limit)"
    echo "  # V6 NEW: Wholefile mode"
    echo "  $0 find_text.py --wholefile --file config.py                      # Show entire file"
    echo "  $0 find_text.py 'setting' --wholefile --file config.py --json    # Search + wholefile JSON"
    echo "  # V5 Range features in V6:"
    echo "  $0 find_text.py 'TODO' --extract-ranges --merge-ranges -C 2       # Merged line ranges"
    echo "  $0 find_text.py --lines '1-10,25-30' --file MyClass.java          # Direct line extraction"
    echo "  # V6 Multiple files and auto-find:"
    echo "  $0 find_text.py 'class' --file File1.java File2.java File3.java   # Multiple files"
    echo "  $0 find_text.py 'processOrder' --file OrderManager.java --auto-find  # Auto-find file"
    echo "  $0 find_text.py 'error' --file File.java -i                   # Case-insensitive search"
    echo "  $0 find_text.py 'def ' --scope . -g '*.py' --no-ast-context       # Disable AST context"
    echo "  # Method extraction features:"
    echo "  $0 find_text.py 'TODO' --extract-method                          # Extract methods containing TODOs"
    echo "  $0 find_text.py 'bug' --extract-method-alllines                   # Extract all methods regardless of size"
    echo "  $0 find_text.py 'calculateValue' --file DataManager.java --ast-context # Show class/method hierarchy"
    echo "  # 🆕 V6 Block extraction features:"
    echo "  $0 find_text.py 'error' --file Handler.java --extract-block       # Extract complete code block"
    echo "  $0 find_text.py 'validate' --file Process.py --extract-block      # Extract if/try/for/while block"
    echo "  # 🆕 V6 Whole file extraction:"
    echo "  $0 find_text.py 'TODO' --file MyClass.java --wholefile            # Return entire file when match found"
    echo "  $0 find_text.py 'bug' --scope src/ --wholefile --json             # Get full files with matches in JSON"
    echo "  # 🆕 V6 Standalone whole file display (no pattern needed):"
    echo "  $0 find_text.py --wholefile --file config.py                      # Display entire file without searching"
    echo "  $0 find_text.py --wholefile --file file1.txt file2.txt --json     # Multiple files in JSON format"
    echo ""
    echo "ast_refactor.py examples (NEW - AST-based intelligent refactoring):"
    echo "  $0 ast_refactor.py analyze my_file.py                              # Analyze code structure"
    echo "  $0 ast_refactor.py find --name calculate_result *.py                # Find all references safely"
    echo "  $0 ast_refactor.py rename --old-name old_func --new-name new_func --type function --dry-run *.py"
    echo "  $0 ast_refactor.py rename --old-name MyClass --new-name BetterClass --type class *.py"
    echo ""
    echo "Bulletproof File Operations examples (NEW - Enterprise-grade safety):"
    echo "  $0 safe_move.py move file.txt dest/                               # Move with automatic backup"
    echo "  $0 safe_move.py copy *.java backup/ --check-compile               # Copy with compile checking"
    echo "  $0 safe_move.py undo --interactive                                # Interactive undo mode"
    echo "  $0 safe_move.py history 20                                        # Show last 20 operations"
    echo "  $0 organize_files.py ~/Downloads --by-ext --create-manifest       # Organize with undo manifest"
    echo "  $0 organize_files.py ~/Downloads --by-date "%Y-%m" --create-manifest  # Organize by year-month"
    echo "  $0 refactor_rename.py --replace oldVar newVar --in \"src/**/*.py\" --yes  # Batch symbol rename"
    echo "  $0 refactor_rename.py --batch "test_" "spec_" . "*.py"       # Batch rename files"
    echo ""
    echo "multiline_reader.py examples (NEW - Enhanced multiline reading):"
    echo "  $0 multiline_reader.py file.java 100-120                          # Lines 100 to 120"
    echo "  $0 multiline_reader.py file.java 100,200,300                      # Specific lines"
    echo "  $0 multiline_reader.py file.java 150±10                           # 10 lines around line 150"
    echo "  $0 multiline_reader.py file.java 100:20                           # 20 lines starting from 100"
    echo "  $0 multiline_reader.py file.java --pattern TODO --context 5       # 5 lines around each TODO"
    echo "  $0 multiline_reader.py file.java --around-lines 100,200,300       # Context around multiple lines"
    echo ""
    echo "show_structure_ast.py examples (NEW - Hierarchical code structure):"
    echo "  $0 show_structure_ast.py MyClass.java                             # Show class/method structure"
    echo "  $0 show_structure_ast.py module.py --include-fields               # Include fields/attributes"
    echo "  $0 show_structure_ast.py file.js --json                           # JSON output for parsing"
    echo "  $0 show_structure_ast.py MyClass.java --max-depth 2               # Limit nesting depth"
    echo "  $0 show_structure_ast.py file.py --filter-visibility public       # Show only public methods"
    echo "  $0 show_structure_ast.py large.java --sort-by size               # Sort by method size"
    echo ""
    echo "show_structure_ast_v4.py examples (RECOMMENDED - Annotation filtering & robustness):"
    echo "  $0 show_structure_ast_v4.py MyClass.java                      # Basic structure view"
    echo "  $0 show_structure_ast_v4.py large.java --no-preprocess            # Skip preprocessing for speed"
    echo "  $0 show_structure_ast_v4.py MyClass.java --filter-name \"send.*\"   # Smart filtering keeps parents"
    echo "  $0 show_structure_ast_v4.py TestClass.java --filter-annotation \"@Test\" # Java annotation filtering"
    echo "  $0 show_structure_ast_v4.py Service.java --filter-annotation \"@Override\" # Find overridden methods"
    echo "  $0 show_structure_ast_v4.py file.java --filter-visibility private # Show only private members"
    echo "  $0 show_structure_ast_v4.py LargeFile.java --no-preprocess --max-depth 1  # Large files"
    echo ""
    echo "show_structure_ast_v4_package.py examples (Package version - proper imports):"
    echo "  $0 show_structure_ast_v4_package.py MyClass.java              # Uses package imports"
    echo "  $0 show_structure_ast_v4_enhanced.py MyClass.java --verbose       # Enhanced error reporting"
    echo ""
    echo "Enhanced navigate.py examples (ENHANCED with multiline ranges):"
    echo "  $0 navigate.py file.java --ranges \"100-120,200±5,300:10\"         # Multiple ranges"
    echo "  $0 navigate.py file.java --around-lines 100,200,300               # Context around specific lines"
    echo "  $0 navigate.py file.java --to-method processItem --show-signature --show-callers"
    echo ""
    echo "Enhanced find_text.py examples (V4 ENHANCED with method extraction):"
    echo "  $0 find_text.py 'TODO' --extract-method --ast-context               # Method extraction with AST context"
    echo "  $0 find_text.py 'error|warning' --type regex -i --extract-method   # Case-insensitive regex with method extraction"
    echo ""
    echo "Enhanced semantic_diff_v3.py examples (MAIN semantic diff tool):"
    echo "  $0 semantic_diff_v3.py FileV1.java FileV2.java --show-methods --show-details"
    echo "  $0 semantic_diff_v3.py FileV1.java FileV2.java --logic-only --risk-analysis"
    echo "  $0 semantic_diff_v3.py FileV1.java FileV2.java --format json --show-critical"
    echo ""
    echo "🚀 UNIFIED FIND→REPLACE WORKFLOW EXAMPLES (CONSOLIDATED V7 + V2 WITH V7 COMPATIBILITY):"
    echo "==========================================================================================="
    echo ""
    echo "1. Complete find→replace pipeline with JSON:"
    echo "   # Step 1: Find patterns and save results"
    echo "   $0 find_text.py 'calculateTotal' --scope src/ --json > search_results.json"
    echo "   # Step 2: Use results for targeted replacement"
    echo "   $0 replace_text_v8.py --from-find-json search_results.json calculateTotal computeTotal"
    echo ""
    echo "2. AST-enhanced find→replace for symbol renaming:"
    echo "   # Step 1: Find symbol locations with AST context"
    echo "   $0 find_text.py 'processOrder' --scope . --ast-context --json > symbols.json"
    echo "   # Step 2: Batch rename with scope awareness"
    echo "   $0 replace_text_ast.py --from-find-json symbols.json processOrder handleOrder"
    echo ""
    echo "3. Block-aware replacement workflow:"
    echo "   # Step 1: Find patterns in specific code blocks"
    echo "   $0 find_text.py 'validateInput' --scope src/ --extract-block --json > blocks.json"
    echo "   # Step 2: Replace only within extracted blocks"
    echo "   $0 replace_text_v8.py --from-find-json blocks.json --block-mode within validateInput checkInput"
    echo ""
    echo "4. Symbol discovery and batch rename:"
    echo "   # Step 1: Discover all symbol occurrences"
    echo "   $0 replace_text_ast.py --discover-symbols oldMethodName src/ --language java"
    echo "   # Step 2: Batch rename with confirmation"
    echo "   $0 replace_text_ast.py --batch-rename oldMethodName newMethodName src/ --confirm"
    echo ""
    echo "5. NEW V7 COMPATIBILITY: Comments-only AST operations:"
    echo "   # Step 1: Find symbols in comments"
    echo "   $0 find_text.py 'oldMethodName' --scope src/ --comments-only --json > comment_symbols.json"
    echo "   # Step 2: AST-based replacement in comments only"
    echo "   $0 replace_text_ast.py --from-find-json comment_symbols.json oldMethodName newMethodName --comments-only"
    echo ""
    echo "6. NEW V7 COMPATIBILITY: Git-integrated AST workflows:"
    echo "   # Step 1: Find staged changes with AST context"
    echo "   $0 find_text.py 'processData' --scope . --staged-only --ast-context --json > staged.json"
    echo "   # Step 2: AST replacement in Git-tracked files only"
    echo "   $0 replace_text_ast.py --from-find-json staged.json processData handleData --git-only"
    echo ""
    echo "7. Cross-tool integration for complex refactoring:"
    echo "   # Find with context → Replace with AST awareness → Validate with semantic diff"
    echo "   $0 find_text.py 'calculatePrice' --scope . --ast-context --json > price_calc.json"
    echo "   $0 replace_text_ast.py --from-find-json price_calc.json calculatePrice computePrice"
    echo "   $0 semantic_diff_v3.py original_file.java modified_file.java --risk-analysis"
    echo ""
    echo "8. V8 NEW: Multi-line replacement with escape sequences:"
    echo "   # Replace single-line placeholders with multi-line content"
    echo "   $0 replace_text_v8.py 'TODO_IMPLEMENT' 'def method():\\n    \"\"\"TODO: Implement this method\"\"\"\\n    pass' *.py --interpret-escapes"
    echo "   # Insert formatted data with tabs"
    echo "   $0 replace_text_v8.py 'DATA_PLACEHOLDER' 'Name\\tAge\\tCity\\nJohn\\t30\\tNYC\\nJane\\t25\\tLA' data.txt --interpret-escapes"
    echo ""
    echo "📋 LANGUAGE SUPPORT:"
    echo "  Most tools support multiple programming languages:"
    echo "  • Python (.py) - Full AST support, comprehensive analysis"
    echo "  • Java (.java) - AST support via javalang/Spoon, full analysis"
    echo "  • JavaScript (.js) - AST support via esprima, code analysis"
    echo "  • TypeScript (.ts) - Basic text-based support"
    echo "  • C/C++ (.c, .cpp, .h) - Text-based analysis"
    echo "  • Go (.go) - Text-based analysis"
    echo "  • Rust (.rs) - Text-based analysis"
    echo "  • Ruby (.rb) - Text-based analysis"
    echo "  • Shell (.sh, .bash) - Text-based analysis"
    echo ""
    echo "  Tool capabilities by language:"
    echo "  • AST-based tools (navigate_ast.py, replace_text_ast.py, etc.) - Python, Java, JavaScript"
    echo "  • Text-based tools (find_text.py, replace_text_v8.py, etc.) - All languages"
    echo "  • Dead code detection - Python, Java, JavaScript (with AST analysis)"
    echo "  • Semantic diff - All languages (AST-enhanced for Python/Java/JS)"
    echo ""
    echo "🚨 COMMON PITFALLS TO AVOID:"
    echo "  ❌ WRONG: replace_text_v8.py file.java 'old' 'new'     # File path should be LAST"
    echo "  ✅ RIGHT: replace_text_v8.py 'old' 'new' file.java     # Correct order"
    echo ""
    echo "  ❌ WRONG: find_text.py --file path 'pattern'        # Pattern should be FIRST"
    echo "  ✅ RIGHT: find_text.py 'pattern' --file path        # Correct order"
    echo ""
    echo "  ❌ WRONG: find_text.py 'regex.*pattern' file.java     # Don't mix pattern and path"
    echo "  ✅ RIGHT: find_text.py 'regex.*pattern' --file file.java  # Use --file flag"
    echo ""
    echo "  ❌ WRONG: find_text.py 'pattern1\\|pattern2' --file file.java  # Don't escape pipe in shell"
    echo "  ✅ RIGHT: find_text.py 'pattern1|pattern2' --file file.java --type regex  # Use raw pipe with --type regex"
    echo ""
    echo "  ❌ WRONG: find_text.py 'public.*class|@Override' --file file.java  # Complex regex needs --type"
    echo "  ✅ RIGHT: find_text.py 'public.*class|@Override' --file file.java --type regex  # Explicit --type regex"
    echo ""
    echo "  For multi-line text replacement:"
    echo "  ❌ WRONG: Passing huge text blocks as command arguments"
    echo "  ✅ RIGHT: Use escape sequences ('line1\\nline2') or put text in files"
    echo ""
    echo "  Note: All errors are logged to ~/.pytoolserrors/ for debugging"
    echo ""
    echo "📊 ERROR ANALYSIS TOOLS (NEW):"
    echo "  $0 analyze_errors.py --recent 10                  # Show 10 most recent errors"
    echo "  $0 analyze_errors.py --summary                     # Show error summary"
    echo "  $0 analyze_errors.py --tool find_text.py           # Errors for specific tool"
    echo "  $0 error_analyzer.py --analyze --hours 2           # Comprehensive analysis"
    echo "  $0 error_analyzer.py --analyze --json              # Export analysis as JSON"
    echo "  $0 error_dashboard.py --recent 20                  # Visual error dashboard"
    echo "  $0 error_dashboard.py --days 7                     # Dashboard for last week"
    echo "  $0 error_analyzer.py --clear-old 30                # Clean up old errors"
    echo ""
    echo "========================================================================="
    echo "⚠️  SAFETY WARNING: Direct shell commands are BLOCKED for your protection!"
    echo "========================================================================="
    echo "❌ BLOCKED: rm, mv, cp, mkdir, touch, chmod, chown, rmdir, dd, shred, unlink"
    echo "❌ BLOCKED: git (all commands - use safegit.py instead)"
    echo ""
    echo "✅ USE INSTEAD:"
    echo "  - File operations: $0 safe_file_manager.py [command]"
    echo "  - Git operations: $0 safegit.py [command]"
    echo ""
    echo "This protection prevents accidental data loss. All operations go through"
    echo "safe tools with automatic backups, undo capability, and confirmation prompts."
    echo "========================================================================="
    exit 0
}

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    usage
fi

# Check for skip preflight flag
SKIP_PREFLIGHT=0
if [[ "$1" == "--skip-preflight" ]]; then
    SKIP_PREFLIGHT=1
    shift
    # Check again for at least one argument after flag
    if [ $# -lt 1 ]; then
        echo "Error: Tool name required after --skip-preflight"
        usage
    fi
fi

# Get the tool name and shift arguments
TOOL_NAME="$1"
shift

# Path traversal guard
if [[ "$TOOL_NAME" == *".."* ]]; then
    echo "🚫 Path traversal detected in tool name: $TOOL_NAME"
    exit 1
fi

# Handle help flags
if [[ "$TOOL_NAME" == "-h" || "$TOOL_NAME" == "--help" || "$TOOL_NAME" == "help" ]]; then
    usage
fi

# If tool name doesn't end with .py, add it
if [[ ! "$TOOL_NAME" == *.py ]]; then
    TOOL_NAME="${TOOL_NAME}.py"
fi

# Direct mapping to newer versions - silent operation
case "$TOOL_NAME" in
    "find_references.py")
        TOOL_NAME="find_references_rg.py"
        ;;
    "analyze_dependencies.py" | "analyze_dependencies_rg.py")
        TOOL_NAME="analyze_dependencies_with_timeout.py"
        ;;
    "analyze_unused_methods.py" | "analyze_unused_methods_rg.py")
        TOOL_NAME="analyze_unused_methods_with_timeout.py"
        ;;
    "trace_calls.py" | "trace_calls_rg.py")
        TOOL_NAME="trace_calls_with_timeout.py"
        ;;
    "extract_methods.py")
        TOOL_NAME="extract_methods_v2.py"
        ;;
    "find_text.py")
        TOOL_NAME="find_text_v7.py"
        
        ;;
    "method_analyzer_ast.py")
        TOOL_NAME="method_analyzer_ast_v2.py"
        ;;
    "navigate_ast.py")
        TOOL_NAME="navigate_ast_v2.py"
        ;;
    "smart_refactor.py")
        TOOL_NAME="smart_refactor_v2.py"
        ;;
    "recent_files.py")
        TOOL_NAME="recent_files_v2.py"
        ;;
    "dead_code_detector.py")
        TOOL_NAME="dead_code_detector_with_timeout.py"
        ;;
    "semantic_diff.py")
        TOOL_NAME="semantic_diff_v3.py"
        echo "ℹ️  Using semantic_diff_v3.py - the main semantic diff tool with enterprise features"
        ;;
    "analyze_errors.py")
        TOOL_NAME="analyze_errors.py"
        echo "ℹ️  Using analyze_errors.py for error log analysis"
        ;;
    "error_analyzer.py")
        TOOL_NAME="error_analyzer.py"
        echo "ℹ️  Using error_analyzer.py for comprehensive error analysis with insights"
        ;;
    "error_dashboard.py")
        TOOL_NAME="error_dashboard_v2.py"
        echo "ℹ️  Using error_dashboard_v2.py for visual error dashboard"
        ;;
    "show_structure_ast.py")
        TOOL_NAME="show_structure_ast_v4.py"
        echo "ℹ️  Using show_structure_ast_v4.py - production version with annotation filtering"
        ;;
    "replace_text.py")
        TOOL_NAME="replace_text_v8.py"
        echo "ℹ️  Using replace_text_v8.py - Enhanced with escape sequence interpretation (\\n, \\t, \\r, etc.)"
        ;;
    "replace_text_ast.py")
        TOOL_NAME="replace_text_ast_v2.py"
        echo "ℹ️  Using replace_text_ast_v2.py - DEFINITIVE AST tool with V7 compatibility features (block-mode, git integration, comments-only, strings-only)"
        ;;
esac

# Full path to the tool
# Since the script is now in code-intelligence-toolkit/, 
# the tools are in the same directory
TOOL_PATH="${SCRIPT_DIR}/${TOOL_NAME}"

# Run preflight checks unless skipped
if [ "$SKIP_PREFLIGHT" -eq 0 ]; then
    if ! preflight_check "$TOOL_NAME" "$TOOL_PATH" "$@"; then
        echo "❌ Preflight checks failed. Use --skip-preflight to bypass (not recommended)"
        exit 1
    fi
fi

# Check if the tool exists
if [ ! -f "$TOOL_PATH" ]; then
    echo "Error: Tool '$TOOL_NAME' not found at $TOOL_PATH"
    echo ""
    usage
fi

# Check if the tool is executable, if not make it executable
if [ ! -x "$TOOL_PATH" ]; then
    chmod +x "$TOOL_PATH"
fi

# Special handling for common_config.py with no arguments
if [[ "$TOOL_NAME" == "common_config.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for common_config.py (NEW Configuration System):"
    echo "================================================================="
    echo ""
    echo "Unified configuration management for all Python tools via .pytoolsrc"
    echo ""
    echo "KEY FEATURES:"
    echo "• Project-aware configuration - automatically finds .pytoolsrc in parent directories"
    echo "• Tool-specific defaults - each tool has its own configuration section"
    echo "• CLI override support - command-line arguments always override config file settings"
    echo "• Graceful fallbacks - all tools work perfectly without configuration files"
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Create a default configuration file:"
    echo "   $0 common_config.py --create"
    echo ""
    echo "2. Show current configuration status and all loaded values:"
    echo "   $0 common_config.py --show"
    echo ""
    echo "3. Find the project root directory (where .pytoolsrc should be placed):"
    echo "   $0 common_config.py --find-root"
    echo ""
    echo "CONFIGURATION EXAMPLE (.pytoolsrc):"
    echo "[Global]"
    echo "verbose = true"
    echo "dry_run = false"
    echo ""
    echo "[smart_ls]"
    echo "summary = true"
    echo "long = true"
    echo "ext = java"
    echo ""
    echo "[dir_stats]"
    echo "show_files = true"
    echo "show_dirs = true"
    echo "detailed = true"
    echo ""
    echo "[replace_text_ast]"
    echo "dry_run = true    # Safety first for AST operations"
    echo "backup = true"
    echo ""
    echo "LATEST UPDATES (January 2025):"
    echo "• Fixed smart_ls.py extension filter to correctly show directories"
    echo "• Fixed replace_text_ast.py to properly respect dry_run configuration"
    echo "• Added comprehensive test suite - 34/34 tests passing"
    echo "• All directory and refactoring tools now integrated with config system"
    echo ""
    echo "For full help: $0 common_config.py --help"
    echo ""
    exit 0
fi

# Special handling for replace_text.py with no arguments
if [[ "$TOOL_NAME" == "replace_text_v8.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for replace_text_v8.py (V8 - Enhanced with escape sequences):"
    echo "=========================================================================="
    echo ""
    echo "Definitive text replacement tool with ALL features consolidated from previous versions:"
    echo "blazing fast file discovery, block-aware replacement, JSON pipeline support, and enhanced robustness."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Rename a variable/method (safe from recursive replacement):"
    echo "   $0 replace_text_v8.py oldMethod newMethod MyClass.java --whole-word"
    echo ""
    echo "2. Multi-file replacement with preview:"
    echo "   $0 replace_text_v8.py \"old text\" \"new text\" . -r -g '*.java' --dry-run"
    echo ""
    echo "3. JSON pipeline workflow (find→replace):"
    echo "   $0 find_text.py \"TODO\" --scope src/ --json > results.json"
    echo "   $0 replace_text_v8.py --from-find-json results.json \"TODO\" \"DONE\""
    echo ""
    echo "4. Block-aware replacement (replace only within code blocks):"
    echo "   $0 replace_text_v8.py calculateTotal computeTotal MyClass.java --block-mode within"
    echo ""
    echo "5. Extract and replace in code blocks:"
    echo "   $0 replace_text_v8.py old new MyClass.java --block-mode extract"
    echo ""
    echo "6. AST context display during replacement:"
    echo "   $0 replace_text_v8.py processData handleData Service.java --ast-context"
    echo ""
    echo "7. Git-integrated replacement (only tracked files):"
    echo "   $0 replace_text_v8.py oldValue newValue . -r --git-only -g '*.py'"
    echo ""
    echo "8. Traditional features (still supported):"
    echo "   $0 replace_text_v8.py \"TODO\" \"DONE\" . -r --comments-only --lang java -g '*.java'"
    echo "   $0 replace_text_v8.py value formattedValue MyClass.java --whole-word"
    echo ""
    echo "9. Language-specific replacements (--lang required for comments/strings):"
    echo "   $0 replace_text_v8.py \"TODO\" \"DONE\" script.py --comments-only --lang python"
    echo "   $0 replace_text_v8.py \"error\" \"ERROR\" app.rb --strings-only --lang ruby"
    echo ""
    echo "10. Process from stdin (use - as filename):"
    echo "   echo \"test\" | $0 replace_text_v8.py \"test\" \"exam\" - --interpret-escapes"
    echo ""
    echo "V8 FEATURES (ALL V7 FEATURES + ESCAPE SEQUENCES):"
    echo "• NEW: Escape sequence interpretation with --interpret-escapes flag:"
    echo "  - Basic escapes: \\n (newline), \\t (tab), \\r (carriage return), \\\\ (backslash)"
    echo "  - Unicode: \\uHHHH (4-digit), \\UHHHHHHHH (8-digit)"
    echo "  - Hex codes: \\xHH (2-digit hex values)"
    echo "  - Additional: \\b (backspace), \\f (form feed), \\v (vertical tab), \\0 (null)"
    echo "• NEW: stdin support fixed - use '-' as filename to process from stdin"
    echo "• IMPORTANT: --comments-only and --strings-only now require --lang flag"
    echo "• All V7 features retained:"
    echo "  - Ripgrep integration for blazing fast file discovery"
    echo "  - JSON pipeline support for find→replace workflows"
    echo "  - Block-aware replacement modes (within, extract, surround)"
    echo "  - AST context display during replacement"
    echo "  - Cross-platform support with enhanced pattern handling"
    echo ""
    echo "For full help: $0 replace_text_v8.py --help"
    echo ""
    exit 0
fi

# Special handling for ast_refactor.py with no arguments
if [[ "$TOOL_NAME" == "ast_refactor.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for ast_refactor.py (NEW AST-based refactoring):"
    echo "=================================================================="
    echo ""
    echo "AST refactoring understands code structure, not just text patterns."
    echo "It's safer and more intelligent than text-based replacement."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Analyze code structure:"
    echo "   $0 ast_refactor.py analyze my_file.py"
    echo ""
    echo "2. Find all references to a function safely:"
    echo "   $0 ast_refactor.py find --name my_function *.py"
    echo ""
    echo "3. Preview function renaming (type-aware):"
    echo "   $0 ast_refactor.py rename --old-name old_func --new-name new_func --type function --dry-run *.py"
    echo ""
    echo "4. Apply safe function renaming:"
    echo "   $0 ast_refactor.py rename --old-name old_func --new-name new_func --type function *.py"
    echo ""
    echo "5. Rename class across multiple files:"
    echo "   $0 ast_refactor.py rename --old-name OldClass --new-name NewClass --type class src/"
    echo ""
    echo "ADVANTAGES OVER TEXT REPLACEMENT:"
    echo "• Type-aware: Distinguishes between functions, classes, variables"
    echo "• Type-aware: Knows difference between functions, classes, variables"
    echo "• Context-sensitive: Won't change comments when you want code changes"
    echo "• Safe: Preserves code structure and syntax validity"
    echo ""
    echo "For full help: $0 ast_refactor.py --help"
    echo ""
    exit 0
fi

# Special handling for smart_refactor.py with no arguments  
if [[ "$TOOL_NAME" == "smart_refactor_v2.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for smart_refactor_v2.py (NEW Java scope-aware refactoring):"
    echo "==========================================================================="
    echo ""
    echo "Smart refactoring for Java with scope awareness and conflict detection."
    echo "Understands Java syntax, imports, and naming conflicts."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Safe method rename with conflict detection:"
    echo "   $0 smart_refactor_v2.py rename --old-name oldMethod --new-name newMethod --file MyClass.java --dry-run"
    echo ""
    echo "2. Multi-file variable rename:"
    echo "   $0 smart_refactor_v2.py rename --old-name counter --new-name index --scope src/ --type variable"
    echo ""
    echo "3. Extract method from code block:"
    echo "   $0 smart_refactor_v2.py extract-method --file MyClass.java --start-line 50 --end-line 65 --method-name validateInput"
    echo ""
    echo "4. Class rename across project:"
    echo "   $0 smart_refactor_v2.py rename --old-name OldClass --new-name NewClass --scope . --type class --max-files 20"
    echo ""
    echo "5. Preview changes safely:"
    echo "   $0 smart_refactor_v2.py rename --old-name data --new-name payload --scope . --dry-run --show-conflicts"
    echo ""
    echo "SAFETY FEATURES:"
    echo "• Scope conflict detection (method/field/class name conflicts)"
    echo "• Import analysis and collision detection" 
    echo "• Automatic backup creation"
    echo "• Dry-run preview mode"
    echo "• Java syntax awareness"
    echo ""
    echo "For full help: $0 smart_refactor_v2.py --help"
    echo ""
    exit 0
fi

# Special handling for method_analyzer.py with no arguments
if [[ "$TOOL_NAME" == "method_analyzer.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for method_analyzer.py (NEW comprehensive method analysis):"
    echo "============================================================================"
    echo ""
    echo "Analyze method usage patterns, parameters, and call flow across your codebase."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Basic method usage analysis:"
    echo "   $0 method_analyzer.py processItem --show-parameters"
    echo ""
    echo "2. Method flow tracing with dependencies:"
    echo "   $0 method_analyzer.py initialize --trace-flow --max-depth 2"
    echo ""
    echo "3. Parameter pattern analysis:"
    echo "   $0 method_analyzer.py calculateResult --parameter-patterns --frequency-analysis"
    echo ""
    echo "4. Cross-file usage analysis:"
    echo "   $0 method_analyzer.py performComplexOperation --scope src/ --show-callers"
    echo ""
    echo "5. JSON output for further processing:"
    echo "   $0 method_analyzer.py updateParameters --json --max-results 100"
    echo ""
    echo "ANALYSIS FEATURES:"
    echo "• Parameter usage patterns and frequencies"
    echo "• Calling context analysis (conditional, loop, etc.)"
    echo "• Method flow tracing and dependencies"
    echo "• Cross-file usage statistics"
    echo "• Sample code extraction"
    echo ""
    echo "For full help: $0 method_analyzer.py --help"
    echo ""
    exit 0
fi

# Special handling for analyze_errors.py with no arguments
if [[ "$TOOL_NAME" == "analyze_errors.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for analyze_errors.py (NEW Error Analysis):"
    echo "============================================================="
    echo ""
    echo "Analyze error logs to find patterns, trends, and insights."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. View recent errors:"
    echo "   $0 analyze_errors.py --recent 10"
    echo ""
    echo "2. Analyze errors from the last week:"
    echo "   $0 analyze_errors.py --days 7"
    echo ""
    echo "3. Show error summary statistics:"
    echo "   $0 analyze_errors.py --summary"
    echo ""
    echo "4. Find failure patterns:"
    echo "   $0 analyze_errors.py --patterns"
    echo ""
    echo "5. Analyze errors for a specific tool:"
    echo "   $0 analyze_errors.py --tool smart_ls.py --days 30"
    echo ""
    echo "6. Export analysis as JSON:"
    echo "   $0 analyze_errors.py --json > error_report.json"
    echo ""
    echo "ERROR LOG FEATURES:"
    echo "• Automatic error capture for all Python tools"
    echo "• System context and environment capture"
    echo "• Error pattern detection (file not found, permissions, etc.)"
    echo "• Time-based analysis (errors by hour, day)"
    echo "• Tool reliability tracking"
    echo ""
    echo "ERROR LOG LOCATION: ~/.pytoolserrors/"
    echo "DISABLE LOGGING: Set DISABLE_ERROR_LOGGING=1"
    echo ""
    echo "For full help: $0 analyze_errors.py --help"
    echo ""
    exit 0
fi

# Special handling for log_analyzer.py with no arguments
if [[ "$TOOL_NAME" == "log_analyzer.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for log_analyzer.py (NEW log pattern analysis):"
    echo "================================================================="
    echo ""
    echo "Analyze log files for pattern frequency, timeline trends, and anomaly detection."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Pattern frequency analysis:"
    echo "   $0 log_analyzer.py --pattern PATTERN --files ./logs/*.txt --frequency"
    echo ""
    echo "2. Timeline analysis with trends:"
    echo "   $0 log_analyzer.py --pattern ERROR --files ./logs/ --timeline --time-window hour"
    echo ""
    echo "3. Anomaly detection for error bursts:"
    echo "   $0 log_analyzer.py --pattern Exception --files . --anomaly-detection --threshold 2.5"
    echo ""
    echo "4. Complete analysis with all features:"
    echo "   $0 log_analyzer.py --pattern 'process.*completed' --files . --all-analysis --regex"
    echo ""
    echo "5. Hourly distribution analysis:"
    echo "   $0 log_analyzer.py --pattern WARNING --files /var/log/ --timeline --samples 20"
    echo ""
    echo "ANALYSIS FEATURES:"
    echo "• Frequency patterns by log level, file, thread, class"
    echo "• Timeline trends and peak activity detection"
    echo "• Anomaly detection for spikes and error bursts"
    echo "• Temporal pattern analysis with time windows"
    echo "• Exception tracking and context extraction"
    echo ""
    echo "For full help: $0 log_analyzer.py --help"
    echo ""
    exit 0
fi

# Special handling for replace_text_ast.py with no arguments
if [[ "$TOOL_NAME" == "replace_text_ast_v2.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for replace_text_ast_v2.py (CONSOLIDATED with V7 compatibility features):"
    echo "======================================================================================="
    echo ""
    echo "Definitive AST-based refactoring tool with symbol discovery, batch operations, JSON pipeline integration,"
    echo "and ALL V7 compatibility features: block-mode, git integration, comments-only, strings-only."
    echo "Scope-aware variable and method renaming with multi-file support."
    echo ""
    echo "CORE AST FEATURES:"
    echo ""
    echo "1. Java variable renaming with scope awareness:"
    echo "   $0 replace_text_ast.py --file MyClass.java --line 42 oldVar newVar"
    echo ""
    echo "2. Symbol discovery across multiple files:"
    echo "   $0 replace_text_ast.py --discover-symbols oldMethod src/ --language java"
    echo ""
    echo "3. Batch symbol rename across project:"
    echo "   $0 replace_text_ast.py --batch-rename oldMethod newMethod src/ --confirm"
    echo ""
    echo "4. JSON pipeline integration (find→replace workflow):"
    echo "   $0 replace_text_ast.py --from-find-json search_results.json oldVar newVar"
    echo ""
    echo "5. Preview changes before applying (dry-run):"
    echo "   $0 replace_text_ast.py --file MyClass.java --line 15 --dry-run data payload"
    echo ""
    echo "NEW V7 COMPATIBILITY FEATURES:"
    echo ""
    echo "6. Comments-only replacement (language-aware):"
    echo "   $0 replace_text_ast.py --file Code.java --line 5 oldVar newVar --comments-only"
    echo ""
    echo "7. String literals-only replacement:"
    echo "   $0 replace_text_ast.py --file Config.py --line 10 oldPath newPath --strings-only"
    echo ""
    echo "8. Git-integrated AST operations (only Git-tracked files):"
    echo "   $0 replace_text_ast.py --file MyClass.java --line 42 oldMethod newMethod --git-only"
    echo ""
    echo "9. Block-aware AST replacement modes:"
    echo "   $0 replace_text_ast.py --file Service.java --line 25 data payload --block-mode within"
    echo ""
    echo "10. Multi-file AST operations with staging filter:"
    echo "    $0 replace_text_ast.py --discover-symbols oldVar src/ --staged-only --language java"
    echo ""
    echo "CONSOLIDATED FEATURES (V2 + V7 COMPATIBILITY):"
    echo "• Core AST: Symbol discovery, batch operations, JSON pipeline integration"
    echo "• V7 Compatibility: Block-mode (preserve/within/extract), git integration, comments-only, strings-only"
    echo "• Enhanced scope analysis - block and AST context awareness with language-specific processing"
    echo "• Multi-language support - Python, Java, JavaScript with appropriate analyzers"
    echo "• Interactive confirmation - review each change during batch operations"
    echo "• Complete feature parity with text-based replace_text_v7.py where applicable"
    echo ""
    echo "SAFETY FEATURES:"
    echo "• Validates identifiers before processing"
    echo "• Creates backups atomically before modifications"
    echo "• Falls back to basic analysis if AST engines fail"
    echo "• Multiple validation checks prevent file corruption"
    echo "• Interactive confirmation for batch operations"
    echo ""
    echo "For full help: $0 replace_text_ast.py --help"
    echo ""
    exit 0
fi

# Special handling for safe_file_manager.py with no arguments
if [[ "$TOOL_NAME" == "safe_file_manager.py" && $# -eq 0 ]]; then
    echo "Safe File Manager - Complete File System Operations"
    echo "=================================================="
    echo ""
    echo "MANDATORY tool for ALL file operations with safety and validation."
    echo ""
    echo "USAGE:"
    echo "   $0 safe_file_manager.py <command> [options]"
    echo ""
    echo "COMMON COMMANDS:"
    echo "   cat/view <file>           Read file contents"
    echo "   copy/cp <src> <dst>       Copy files (use --overwrite to replace)"
    echo "   move/mv <src> <dst>       Move or rename files"
    echo "   trash/rm <files>          Safe deletion (to trash, recoverable)"
    echo "   list/ls <dir>             List directory contents"
    echo "   cd <dir>                  Validate directory (returns absolute path)"
    echo "   pwd                       Print current working directory"
    echo "   mkdir <dirs>              Create directories"
    echo "   create <file>             Create new file (--content or --from-stdin)"
    echo "   info <paths>              Detailed file information"
    echo "   history                   View operation history"
    echo ""
    echo "SHELL INTEGRATION:"
    echo "   Run ./setup_safe_cd.sh to install 'scd' function for actual directory changes"
    echo ""
    echo "Run with --help for complete documentation"
    exit 0
fi

# Special handling for safegit.py with no arguments
if [[ "$TOOL_NAME" == "safegit.py" && $# -eq 0 ]]; then
    echo "SafeGIT v2.0 - Enterprise Git Safety Wrapper"
    echo "============================================"
    echo ""
    echo "Prevents accidental data loss from dangerous git operations."
    echo ""
    echo "USAGE:"
    echo "   $0 safegit.py [safegit-flags] <git-command> [git-args]"
    echo ""
    echo "SAFEGIT FLAGS:"
    echo "   --yes, -y             Auto-confirm safe operations"
    echo "   --force-yes           Force confirmation of ALL operations (use carefully!)"
    echo "   --non-interactive     Fail on any interactive prompt (for scripts)"
    echo "   --dry-run             Show what would happen without executing"
    echo ""
    echo "COMMON EXAMPLES:"
    echo ""
    echo "1. Safe interactive usage:"
    echo "   $0 safegit.py status"
    echo "   $0 safegit.py add file.txt"
    echo "   $0 safegit.py commit -m \"message\""
    echo ""
    echo "2. Dangerous operations (will prompt):"
    echo "   $0 safegit.py reset --hard HEAD~1"
    echo "   $0 safegit.py clean -fdx"
    echo "   $0 safegit.py push --force"
    echo ""
    echo "3. CI/CD automation:"
    echo "   $0 safegit.py --yes add ."
    echo "   $0 safegit.py --yes commit -m \"Deploy\""
    echo "   $0 safegit.py --force-yes reset --hard origin/main"
    echo ""
    echo "4. Undo operations:"
    echo "   $0 safegit.py undo"
    echo "   $0 safegit.py undo --interactive"
    echo "   $0 safegit.py undo-history"
    echo ""
    echo "FEATURES:"
    echo "• 37+ dangerous patterns intercepted"
    echo "• Automatic backups before destructive operations"
    echo "• Multi-level undo with recovery scripts"
    echo "• Non-interactive mode for CI/CD"
    echo "• Educational mode with safer alternatives"
    echo ""
    echo "For full help: $0 safegit.py --help"
    echo ""
    exit 0
fi

# Special handling for dead_code_detector.py with no arguments
if [[ "$TOOL_NAME" == "dead_code_detector.py" && $# -eq 0 ]]; then
    echo "Quick Start Guide for dead_code_detector.py (ENHANCED with threading):"
    echo "======================================================================"
    echo ""
    echo "Multi-language dead code finder with confidence levels and threading support."
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Basic dead code detection:"
    echo "   $0 dead_code_detector.py /path/to/project"
    echo ""
    echo "2. High confidence dead code only:"
    echo "   $0 dead_code_detector.py /path/to/project --confidence high"
    echo ""
    echo "3. Fast analysis with threading:"
    echo "   $0 dead_code_detector.py /path/to/project --threads 8"
    echo ""
    echo "4. Java-specific analysis:"
    echo "   $0 dead_code_detector.py /path/to/project --language java --format markdown"
    echo ""
    echo "5. Exclude patterns:"
    echo "   $0 dead_code_detector.py /path/to/project --ignore-pattern 'test_.*' --ignore-pattern '.*_test'"
    echo ""
    echo "ENHANCED FEATURES (July 2025):"
    echo "• Threading support - configurable thread count for faster analysis"
    echo "• Multi-language support - Python, Java, JavaScript/TypeScript"
    echo "• Confidence levels - high/medium/low with detailed reasoning"
    echo "• Framework awareness - recognizes framework-specific patterns"
    echo "• Output formats - text, JSON, markdown"
    echo ""
    echo "For full help: $0 dead_code_detector.py --help"
    echo ""
    exit 0
fi

# Special handling for unified_refactor.py with no arguments
if [[ "$TOOL_NAME" == "unified_refactor.py" && $# -eq 0 ]]; then
    echo "Unified Refactoring Tool - Multiple backends, multiple languages"
    echo "================================================================"
    echo ""
    echo "A single tool that combines all refactoring capabilities with automatic"
    echo "backend selection based on file type and operation."
    echo ""
    echo "AVAILABLE BACKENDS:"
    echo "  python_ast - Built-in Python AST transformer"
    echo "  rope - Advanced Python refactoring (if installed)"
    echo "  java_scope - Java refactoring (requires external parser)"
    echo "  text_based - Simple text replacement (always available)"
    echo "  auto - Automatic selection based on file type (default)"
    echo ""
    echo "COMMON USE CASES:"
    echo ""
    echo "1. Rename a function/method:"
    echo "   $0 unified_refactor.py rename --old oldFunction --new newFunction file.py"
    echo "   $0 unified_refactor.py rename --old oldMethod --new newMethod *.java"
    echo ""
    echo "2. Rename across entire project:"
    echo "   $0 unified_refactor.py rename-project --old OldClass --new NewClass"
    echo ""
    echo "3. Find symbol occurrences:"
    echo "   $0 unified_refactor.py find --name myFunction src/"
    echo ""
    echo "4. Analyze file structure:"
    echo "   $0 unified_refactor.py analyze MyClass.java"
    echo ""
    echo "5. Preview changes without applying (dry-run):"
    echo "   $0 unified_refactor.py --dry-run rename --old old --new new file.py"
    echo ""
    echo "6. JSON pipeline workflow:"
    echo "   echo '[{\"file\":\"code.py\",\"old\":\"oldFunc\",\"new\":\"newFunc\",\"line\":42}]' | \\"
    echo "   $0 unified_refactor.py rename --from-json -"
    echo ""
    echo "7. Force specific backend:"
    echo "   $0 unified_refactor.py --engine python_ast rename --old var --new newVar file.py"
    echo ""
    echo "PROFESSIONAL FEATURES:"
    echo "• Unified diff previews - See exact changes before applying"
    echo "• AST-guided rope targeting - Smart offset calculation for precise targeting"  
    echo "• JSON pipeline integration - Read operations from JSON files or stdin"
    echo "• Automatic language detection and backend selection"
    echo "• Multiple backend support (python_ast, rope, java_scope, text_based)"
    echo "• Dry-run mode with professional diff formatting"
    echo "• Symbol type awareness (function, class, variable, etc.)"
    echo "• Project-wide refactoring with atomic operations"
    echo ""
    echo "For full help: $0 unified_refactor.py --help"
    echo ""
    exit 0
fi

# Set PYTHONPATH to include the toolkit directory for package imports
# Since the script is now in the toolkit directory, use SCRIPT_DIR directly
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

# Check if error logging is available and enabled
ERROR_LOG_WRAPPER="$SCRIPT_DIR/run_with_error_logging.py"

# Special handling for SafeGIT help/version only - still use error logging for actual git operations
if [[ "$TOOL_NAME" == "safegit.py" ]] && [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" || "$1" == "help" || "$1" == "--version" || "$1" == "-v" || "$1" == "version" || "$1" == "show-context" ]]; then
    # Run SafeGIT directly ONLY for help/version/show-context commands
    echo "▶ ${TOOL_NAME} $@"
    exec python3 "$TOOL_PATH" "$@"
elif [ -f "$ERROR_LOG_WRAPPER" ] && [ "${DISABLE_ERROR_LOGGING:-}" != "1" ]; then
    # Run with error logging for ALL other operations (including SafeGIT git commands)
    echo "▶ ${TOOL_NAME} $@"
    exec python3 "$ERROR_LOG_WRAPPER" "$TOOL_PATH" "$@"
else
    # Run without error logging (fallback)
    echo "▶ ${TOOL_NAME} $@"
    exec "$TOOL_PATH" "$@"
fi