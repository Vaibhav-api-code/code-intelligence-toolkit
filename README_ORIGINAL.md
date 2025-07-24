<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Code Intelligence Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-24
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Code Intelligence Toolkit

A comprehensive suite of enterprise-grade tools for code analysis, refactoring, and development automation across multiple programming languages.

## 🚀 Overview

The Code Intelligence Toolkit is a collection of 100+ powerful command-line tools designed to enhance developer productivity through intelligent code analysis, automated refactoring, and advanced search capabilities. Originally developed for Java and Python, it now supports multiple languages and provides enterprise-grade safety features.

## ✨ Key Features

### 🔍 Advanced Search & Analysis
- **AST-based code navigation** - Navigate code using Abstract Syntax Trees for 100% accuracy
- **Semantic code analysis** - Understand code structure, dependencies, and patterns
- **Cross-file dependency tracking** - Trace usage across entire codebases
- **Dead code detection** - Find unused code with configurable confidence levels

### 🛠️ Safe Refactoring
- **AST-aware refactoring** - Rename variables, methods, and classes with semantic understanding
- **Unified refactoring interface** - Multiple backends (Python AST, Rope, Java Scope)
- **Atomic file operations** - All changes are reversible with automatic backups
- **Preview changes** - Dry-run mode for all refactoring operations

### 🛡️ Enterprise Safety
- **SafeGIT integration** - Prevents accidental data loss from dangerous git operations
- **Safe File Manager** - Atomic file operations with complete undo system
- **Comprehensive error handling** - All tools include retry logic and graceful degradation
- **Built-in security** - Path traversal protection, input sanitization, resource limits

### 📊 Development Tools
- **Error analysis dashboard** - Visual error tracking and pattern analysis
- **Git workflow automation** - Smart commit generation, staging suggestions
- **Directory statistics** - Comprehensive codebase metrics and insights
- **Configuration management** - Project-wide settings with `.pytoolsrc`

## 🏗️ Architecture

The toolkit is built with:
- **Modular design** - Each tool is independent and can be used standalone
- **Consistent interfaces** - All tools follow similar argument patterns
- **Enterprise patterns** - Proper error handling, logging, and security
- **Performance optimized** - Multi-threading support, efficient algorithms

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Git
- ripgrep (`rg`) - For enhanced search capabilities

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/code-intelligence-toolkit.git
cd code-intelligence-toolkit
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up the convenient wrapper:
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
alias cit="/path/to/code-intelligence-toolkit/run_any_python_tool.sh"
```

## 🎯 Usage Examples

### Search for code patterns
```bash
./run_any_python_tool.sh find_text.py "pattern" --file MyClass.java --extract-method
```

### Navigate to function definition
```bash
./run_any_python_tool.sh navigate_ast.py MyClass.py --to calculate_price
```

### Safe file operations
```bash
./run_any_python_tool.sh safe_file_manager.py move old_file.py new_file.py
```

### Refactor code
```bash
./run_any_python_tool.sh unified_refactor.py rename oldFunction newFunction --file script.py
```

### Analyze errors
```bash
./run_any_python_tool.sh error_dashboard.py --days 7
```

## 📚 Documentation

Comprehensive documentation is available in the toolkit:

- **[TOOLS_DOCUMENTATION_2025.md](TOOLS_DOCUMENTATION_2025.md)** - Complete tool reference
- **[PYTHON_TOOLS_MASTER_HELP.md](PYTHON_TOOLS_MASTER_HELP.md)** - Master help guide
- **[SAFEGIT_COMPREHENSIVE.md](docs/safegit/SAFEGIT_COMPREHENSIVE.md)** - SafeGIT documentation
- **[SAFE_FILE_MANAGER_GUIDE.md](SAFE_FILE_MANAGER_GUIDE.md)** - Safe file operations

### Tool Categories

- **Search Tools** - find_text, grep, find_files
- **AST Tools** - navigate_ast, method_analyzer_ast, semantic_diff
- **File Tools** - safe_file_manager, organize_files, safe_move
- **Analysis Tools** - dead_code_detector, dependency_analyzer, trace_calls
- **Utility Tools** - error_dashboard, git_commit_analyzer, dir_stats

## 🤝 Contributing

We welcome contributions! Please ensure:

1. All code includes MPL 2.0 license headers
2. Follow existing code patterns and conventions
3. Add tests for new functionality
4. Update documentation as needed

## 📄 License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See [LICENSE.txt](LICENSE.txt) for details.

## 🙏 Acknowledgments

- Original author: [Vaibhav-api-code](https://github.com/Vaibhav-api-code)
- Co-developed with: [Claude Code](https://claude.ai/code)
- Built on top of excellent tools like ripgrep, AST libraries, and more

## 🔗 Links

- [Report Issues](https://github.com/[your-username]/code-intelligence-toolkit/issues)
- [Documentation Wiki](https://github.com/[your-username]/code-intelligence-toolkit/wiki)
- [Release Notes](https://github.com/[your-username]/code-intelligence-toolkit/releases)

---

Made with ❤️ for developers who value code quality and productivity