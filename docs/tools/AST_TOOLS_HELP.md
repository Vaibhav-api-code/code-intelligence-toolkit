<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

AST Tools Help Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# AST Tools Help Documentation

**Related Code Files:**
- `navigate_ast_v2.py` - Navigate to code locations using AST parsing
- `method_analyzer_ast_v2.py` - Analyze method call flows with AST
- `show_structure_ast_v4.py` - Display hierarchical code structure
- `semantic_diff_v3.py` - Advanced semantic code comparison
- `replace_text_ast.py` - AST-based scope-aware refactoring
- `unified_refactor.py` - Universal refactoring interface with multiple backends (NEW)
- `ast_context_finder.py` - Find AST context for specific lines

---

This document provides comprehensive help documentation for all AST-based analysis tools in the code-intelligence-toolkit.

## Table of Contents
1. [navigate_ast_v2.py](#navigate_ast_v2py)
2. [method_analyzer_ast_v2.py](#method_analyzer_ast_v2py)
3. [show_structure_ast_v4.py](#show_structure_ast_v4py)
4. [semantic_diff_v3.py](#semantic_diff_v3py)
5. [replace_text_ast.py](#replace_text_astpy)
6. [ast_context_finder.py](#ast_context_finderpy)
7. [unified_refactor.py](#unified_refactorpy)

---

## navigate_ast_v2.py

**Purpose**: Navigate to code locations with 100% accuracy using AST parsing

### Usage
```
navigate_ast_v2.py [-h] [--file FILE] [--scope SCOPE]
                   [--type {method,class,function,variable,auto}]
                   [--max-depth MAX_DEPTH] [--show-callers]
                   [--show-callees] [-v] [-q] [--json] 
                   (--to TO | --line LINE | --method METHOD | 
                    --class CLASS_NAME | --variable VAR_NAME) 
                   [--highlight] [--no-highlight]
                   target file
```

### Key Features
- **100% accurate definition finding** using AST parsing
- Multi-language support (Python, Java, JavaScript)
- Shows callers and callees relationships
- Hierarchical navigation with context
- JSON output for tool integration

### Positional Arguments
- `target` - Name of method/class/symbol to analyze
- `file` - File to navigate in

### Options
- `--file FILE` - Analyze in specific file
- `--scope SCOPE` - Directory scope for analysis (default: current dir)
- `--type {method,class,function,variable,auto}` - Type of symbol to analyze
- `--max-depth MAX_DEPTH` - Maximum depth for dependency analysis
- `--show-callers` - Show where this symbol is called from
- `--show-callees` - Show what this symbol calls
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Minimal output
- `--json` - Output in JSON format
- `--to TO` - Navigate to symbol (auto-detect type)
- `--line, -l LINE` - Go to line number
- `--method, -m METHOD` - Go to method/function
- `--class, -c CLASS_NAME` - Go to class
- `--variable VAR_NAME` - Go to variable
- `--highlight` - Highlight target line (default: true)
- `--no-highlight` - Disable highlighting

### Examples
```bash
# Navigate to a method
python navigate_ast_v2.py processData DataManager.java --to processData

# Go to specific line
python navigate_ast_v2.py MyClass.java 150 --line 150

# Find all callers of a method
python navigate_ast_v2.py calculateTotal Invoice.java --method calculateTotal --show-callers

# Navigate to class definition
python navigate_ast_v2.py OrderProcessor.java OrderProcessor --class OrderProcessor

# JSON output for tooling
python navigate_ast_v2.py sendNotification NotificationService.java --to sendNotification --json
```

---

## method_analyzer_ast_v2.py

**Purpose**: Perfect call flow analysis using AST parsing for accurate dependency tracking

### Key Features
- **100% accurate call flow analysis** using AST
- Cross-file dependency tracking
- Call hierarchy visualization
- Multi-language support
- Perfect accuracy replacing regex-based analysis

### Common Use Cases
- Trace method calls through codebase
- Understand dependency chains
- Find all usages of a method
- Analyze call hierarchies
- Generate dependency reports

---

## show_structure_ast_v4.py

**Purpose**: Enhanced hierarchical code structure viewer with robustness and performance improvements

### Usage
```
show_structure_ast_v4.py [-h] [--include-fields] [--include-imports]
                         [--include-variables]
                         [--filter-visibility {public,private,protected,package-private}]
                         [--filter-name FILTER_NAME]
                         [--filter-decorator FILTER_DECORATOR]
                         [--filter-annotation FILTER_ANNOTATION]
                         [--sort-by {line,name,size}] [--no-preprocess]
                         file
```

### Key Features
- **Multi-language support**: Python (AST), Java (javalang/regex), JavaScript (esprima/regex)
- **Smart filtering** that preserves parent-child relationships
- **Java annotation filtering** with `--filter-annotation` flag (@Test, @Override, etc.)
- **Defensive error handling** for all parsers
- **Performance optimized** with lazy filtering and early termination
- **Visual hierarchy display** with icons and line numbers
- **JSON output** for programmatic use
- **Configuration file support** via .showstructurerc

### Options
- `--include-fields` - Include field/attribute definitions
- `--include-imports` - Include import statements
- `--include-variables` - Include variable declarations
- `--filter-visibility` - Filter by visibility (public, private, protected, package-private)
- `--filter-name REGEX` - Filter elements by name using regex
- `--filter-decorator` - Filter Python elements by decorator
- `--filter-annotation` - Filter Java elements by annotation (e.g., @Test, @Override)
- `--sort-by {line,name,size}` - Sort elements by criteria
- `--no-preprocess` - Skip preprocessing (faster but less accurate)
- `--json` - Output in JSON format
- `--max-depth N` - Maximum nesting depth to display

### Examples
```bash
# Basic structure view
python show_structure_ast_v4.py MyClass.java

# Filter by name pattern
python show_structure_ast_v4.py module.py --filter-name "test_.*"

# Filter Java test methods
python show_structure_ast_v4.py TestClass.java --filter-annotation "@Test"

# Filter overridden methods
python show_structure_ast_v4.py Service.java --filter-annotation "@Override"

# Include all details
python show_structure_ast_v4.py MyClass.java --include-fields --include-imports

# For large files, skip preprocessing
python show_structure_ast_v4.py HugeFile.java --no-preprocess

# JSON output for tooling
python show_structure_ast_v4.py module.py --json > structure.json

# Sort by size
python show_structure_ast_v4.py LargeClass.java --sort-by size
```

### Visual Output Example
```
📦 OrderManager (1-500)
├── 📄 imports (1-15)
├── 🔧 __init__ (20-35)
├── 📊 processData (40-120)
│   ├── validateOrder (45-60)
│   └── executeOrder (65-115)
├── 📊 calculateTotal (125-180)
└── 🔒 _privateHelper (185-200)
```

---

## semantic_diff_v3.py

**Purpose**: Most advanced semantic diff with enterprise-grade features and multi-format reporting

### Usage
```
semantic_diff_v3.py [-h] [--git COMMIT1 COMMIT2]
                    [--extensions EXT [EXT ...]] [--test-impact]
                    [--performance] [--security] [--dependencies]
                    [--output FILE]
                    [--format {text,json,html,markdown}] [--parallel N]
                    [--cache] [--streaming]
                    file1 file2
```

### Key Features
- **Deep AST-based comparison** with structural change detection
- **Change impact scoring** with risk assessment metrics
- **Comprehensive refactoring safety analysis**
- **Multi-language support** with specialized analyzers
- **Enterprise-grade security** with input validation
- **Rich output formats**: text, JSON, HTML, markdown
- **Performance optimization** with parallel processing and caching
- **Git integration** for commit comparison

### Options
- `--git COMMIT1 COMMIT2` - Compare git commits
- `--extensions EXT [EXT ...]` - File extensions to analyze (e.g., .py .java)
- `--test-impact` - Analyze test coverage impact
- `--performance` - Analyze performance impact
- `--security` - Analyze security implications
- `--dependencies` - Build full dependency graph
- `--output, -o FILE` - Output file for report
- `--format {text,json,html,markdown}` - Output format
- `--parallel N` - Number of parallel workers
- `--cache` - Use caching for large projects
- `--streaming` - Use streaming for huge files

### Examples
```bash
# Basic file comparison
python semantic_diff_v3.py FileV1.java FileV2.java

# Compare with all analysis features
python semantic_diff_v3.py old.py new.py --test-impact --performance --security

# Generate HTML report
python semantic_diff_v3.py src1/ src2/ --format html --output report.html

# Compare git commits
python semantic_diff_v3.py . . --git HEAD~1 HEAD

# JSON output for CI/CD
python semantic_diff_v3.py file1.js file2.js --format json -o changes.json

# Parallel processing for large projects
python semantic_diff_v3.py proj1/ proj2/ --parallel 8 --cache

# Markdown report for documentation
python semantic_diff_v3.py v1.0/ v2.0/ --format markdown -o CHANGELOG.md
```

### Output Includes
- Structural changes (methods, classes, functions)
- Semantic impact analysis
- Risk assessment scores
- Dependency impact graphs
- Test coverage implications
- Performance considerations
- Security vulnerability detection

---

## replace_text_ast.py

**Purpose**: AST-enhanced replacement tool with scope-aware variable renaming

### Usage
```
replace_text_ast.py [-h] [--ast-rename] --line LINE
                    [--language {python,java,auto}] [--use-rope]
                    [--backup] [--no-backup] [--ast-context]
                    [--check-compile] [--no-check-compile]
                    [--source-dir SOURCE_DIRS] [--jar JAR_PATHS]
                    old_name new_name
```

### Key Features
- **Scope-aware variable renaming** - only renames within proper scope
- **Multi-language support** - Python, Java with auto-detection
- **Semantic understanding** - understands shadowing and nested scopes
- **Rope integration** for advanced Python refactoring
- **Compile checking** to ensure changes don't break code
- **Backup creation** for safety
- **Java dependency resolution** via source dirs and JARs

### Positional Arguments
- `old_name` - The original variable or method name to be replaced
- `new_name` - The new variable or method name

### Options
- `--ast-rename` - Enable AST-based scope-aware renaming
- `--line, -l LINE` - Line number where the variable is declared
- `--language {python,java,auto}` - Programming language (default: auto-detect)
- `--use-rope` - Use rope library for Python (if available)
- `--backup, -b` - Create backup before modifying
- `--no-backup` - Explicitly disable backup creation
- `--ast-context` - Show AST context (class/method) in diff output
- `--check-compile` - Check syntax/compilation after edits (default: enabled)
- `--no-check-compile` - Disable compile checking
- `--source-dir` - Add source directory for Java symbol resolution
- `--jar` - Add JAR file for Java dependency resolution

### Examples
```bash
# Rename variable at specific line
python replace_text_ast.py old_var new_var --file myfile.py --line 42

# Rename with language specification  
python replace_text_ast.py myVar newVar --file MyClass.java --line 15 --language java

# Preview changes without applying  
python replace_text_ast.py foo bar --file script.py --line 10 --dry-run

# Use rope for advanced Python refactoring
python replace_text_ast.py var1 var2 --file module.py --line 25 --use-rope

# Java with dependencies
python replace_text_ast.py oldName newName --file Service.java --line 30 \
    --source-dir src/main/java --jar lib/commons.jar

# Disable compile checking for speed
python replace_text_ast.py x y --file calc.py --line 5 --no-check-compile
```

### Benefits
- **True semantic refactoring**, not text replacement
- Renames only the specific variable in its scope
- Leaves other variables with the same name untouched
- Understands nested scopes and variable shadowing
- Prevents accidental renames in strings or comments

---

## ast_context_finder.py

**Purpose**: Find AST context (class/method hierarchy) for specific lines in files

### Usage
```
ast_context_finder.py [-h] [--file FILE] [--scope SCOPE]
                      [--type {method,class,function,variable,auto}]
                      [--max-depth MAX_DEPTH] [--show-callers]
                      [--show-callees] [-v] [-q] [--json]
                      target line_number
```

### Key Features
- **Precise context identification** for any line in a file
- Shows containing class, method, and function hierarchy
- Multi-language support with AST parsing
- Useful for understanding code location in complex files
- Integration with other tools for enhanced context

### Positional Arguments
- `target` - Name of method/class/symbol to analyze
- `line_number` - Line number to find context for

### Options
- `--file FILE` - Analyze in specific file
- `--scope SCOPE` - Directory scope for analysis
- `--type` - Type of symbol to analyze
- `--max-depth` - Maximum depth for dependency analysis
- `--show-callers` - Show where this symbol is called from
- `--show-callees` - Show what this symbol calls
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Minimal output
- `--json` - Output in JSON format

### Examples
```bash
# Find context for line 150 in a file
python ast_context_finder.py OrderProcessor.java 150

# Get context with callers
python ast_context_finder.py MyClass.java 200 --show-callers

# JSON output for integration
python ast_context_finder.py module.py 75 --json

# Verbose output with full details
python ast_context_finder.py Service.java 300 -v
```

### Typical Output
```
Line 150 context:
  File: OrderProcessor.java
  Class: OrderProcessor (lines 10-500)
  Method: processData (lines 140-180)
  Context: OrderProcessor → processData → validateInput
```

---

## Common Patterns and Best Practices

### 1. **Use AST tools for accuracy**
```bash
# Instead of grep/find, use AST tools
python navigate_ast_v2.py MyClass.java --to calculateValue
python method_analyzer_ast_v2.py processData --scope src/
```

### 2. **Combine tools for comprehensive analysis**
```bash
# First understand structure
python show_structure_ast_v4.py ComplexClass.java

# Then navigate to specific method
python navigate_ast_v2.py ComplexClass.java --method importantMethod

# Analyze its impact
python method_analyzer_ast_v2.py importantMethod --show-callers
```

### 3. **Use semantic diff for code reviews**
```bash
# Generate comprehensive change report
python semantic_diff_v3.py feature-branch/ main/ \
    --format markdown --output review.md \
    --test-impact --performance
```

### 4. **Safe refactoring workflow**
```bash
# 1. Find exact location
python navigate_ast_v2.py MyClass.java --to oldVariable

# 2. Check usage
python method_analyzer_ast_v2.py oldVariable --show-callers

# 3. Perform rename
python replace_text_ast.py oldVariable newVariable \
    --file MyClass.java --line 42 --backup

# 4. Verify changes
python semantic_diff_v3.py MyClass.java.backup MyClass.java
```

### 5. **JSON output for automation**
```bash
# All tools support JSON for scripting
python show_structure_ast_v4.py module.py --json | jq '.methods[]'
python navigate_ast_v2.py file.py --to func --json | jq '.location'
```

## Performance Tips

1. **For large files**: Use `--no-preprocess` with show_structure_ast_v4
2. **For large projects**: Use `--parallel` and `--cache` with semantic_diff_v3
3. **For quick navigation**: Use specific `--type` to avoid auto-detection
4. **For Java projects**: Provide `--source-dir` and `--jar` for better resolution

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Install required dependencies: `pip install javalang esprima rope`
   - For semantic_diff_v3 advanced features: `pip install numpy pandas networkx`

2. **Performance issues**
   - Use `--no-preprocess` for show_structure_ast_v4
   - Enable `--parallel` for semantic_diff_v3
   - Limit `--max-depth` for deep hierarchies

3. **Inaccurate results**
   - Ensure correct `--language` specification
   - For Java, provide classpath via `--source-dir` and `--jar`
   - Update to latest parser libraries

4. **Memory issues with large files**
   - Use `--streaming` option in semantic_diff_v3
   - Process files individually rather than directories
   - Increase Python memory limit if needed

## unified_refactor.py

**Universal refactoring interface supporting multiple backends and languages**

### Professional Enhancements
- **Unified Diff Previews**: Professional diff formatting showing exact changes before application
- **AST-Guided Rope Targeting**: Smart offset calculation for precise symbol targeting in Python code
- **JSON Pipeline Integration**: Read operations from JSON files or stdin for workflow automation
- **Multi-Engine Support**: Choose optimal backend per task (python_ast, rope, java_scope, text_based)

### Usage
```
unified_refactor.py COMMAND ARGS [OPTIONS]
```

### Commands
- `rename OLD NEW` - Rename a variable, function, or class with unified diff preview
- `find SYMBOL` - Find all references to a symbol with JSON output support
- `analyze` - Analyze code structure and dependencies with detailed reporting
- `rename-project OLD NEW` - Project-wide symbol renaming

### Options
- `--backend {python_ast,rope,java_scope,text_based}` - Choose refactoring backend (default: python_ast)
- `--file FILE` - Target file for operation
- `--scope PATH` - Directory scope for multi-file operations
- `--line LINE` - Line number for precise targeting (enhances AST-guided rope targeting)
- `--dry-run` - Preview changes with unified diff without applying
- `--from-json FILE` - Read operations from JSON file (use '-' for stdin)
- `--json` - Output in JSON format
- `--verbose` - Enable verbose output

### Professional Examples
```bash
# Rename with unified diff preview
python unified_refactor.py rename old_function new_function --file script.py --dry-run

# AST-guided rope targeting with line precision
python unified_refactor.py rename old_var new_var --backend rope --file code.py --line 42

# JSON pipeline workflow - read operations from file
echo '[{"file":"script.py","old":"oldMethod","new":"newMethod","line":42}]' | \
python unified_refactor.py rename --from-json -

# Find all references with JSON output
python unified_refactor.py find MyClass --backend java_scope --scope src/ --json

# Project-wide renaming with unified diff preview
python unified_refactor.py rename-project OldClassName NewClassName --scope src/ --dry-run

# Text-based backend for any language with preview
python unified_refactor.py rename OLD_CONST NEW_CONST --backend text_based --file config.yml --dry-run
```

### Key Features
- **Atomic Operations**: All file modifications are atomic with retry logic
- **Smart Backend Selection**: Auto-selects optimal engine based on file type and operation complexity
- **Professional Diff Output**: Shows exactly what will change with unified diff format
- **Error Recovery**: Comprehensive error handling with rollback capabilities
- **Multi-Language Support**: Handles Python, Java, JavaScript, and generic text files

## Integration with Other Tools

These AST tools integrate seamlessly with other tools in the toolkit:

- **find_text.py** with `--ast-context` shows hierarchical location
- **trace_calls.py** uses method_analyzer_ast internally
- **cross_file_analysis_ast.py** builds on these AST foundations
- **git_commit_analyzer.py** can use semantic_diff_v3 for analysis
- **unified_refactor.py** provides a unified interface to multiple refactoring backends

## Summary

The AST tool suite provides:
- **100% accuracy** through semantic parsing
- **Multi-language support** (Python, Java, JavaScript)
- **Enterprise-grade features** for production use
- **Rich output formats** for different use cases
- **Performance optimization** for large codebases
- **Safety features** like backup and compile checking

Always prefer AST tools over text-based searching for:
- Code navigation
- Refactoring operations
- Dependency analysis
- Impact assessment
- Code structure understanding