<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Changelog

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-01-26
Updated: 2025-01-26
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Changelog

All notable changes to the Code Intelligence Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-07-27

### Added
- **data_flow_tracker_v2.py**: Enhanced data flow analysis with three major V2 capabilities
  - **Impact Analysis**: Shows where data escapes scope and causes observable effects (returns, side effects, state changes)
  - **Calculation Path Analysis**: Extracts minimal critical path showing exactly how values are calculated
  - **Type and State Tracking**: Monitors how variable types and states evolve through code execution
  - **Full Java Parity**: Complete Java implementation matching all Python V2 features
  - **Enhanced Visualization**: Risk assessment, type evolution tracking, and comprehensive reporting

### Fixed
- **Java AST Compatibility**: Fixed javalang tree node naming (ArrayAccess→ArraySelector, ExpressionStatement→StatementExpression)
- **ForStatement Parsing**: Corrected Java for-loop structure parsing using control.init instead of direct init access
- **Import Handling**: Added proper javalang import with fallback error handling

### Documentation
- **DATA_FLOW_TRACKER_GUIDE.md**: Updated with comprehensive V2 examples and use cases
- **Test Examples**: Added test_java_v2_features.java for demonstrating all V2 capabilities

## [1.2.0] - 2025-07-26

### Added
- **data_flow_tracker.py**: New tool for tracking variable dependencies and data flow through code
  - Bidirectional tracking (forward: what X affects, backward: what affects Y)
  - Inter-procedural analysis across function boundaries
  - Support for Python and Java with full AST parsing
  - Complex expression handling (ternary, comprehensions, method chains)
  - Multiple output formats (text, JSON, GraphViz)
- **DATA_FLOW_TRACKER_GUIDE.md**: Comprehensive user guide with examples
- **DATA_FLOW_TRACKER_ADVANCED_EXAMPLES.md**: Real-world use cases
- **Test examples**: Organized test suite in test-examples/data-flow-tracker/
- **EOF heredoc warnings**: Added to documentation to prevent 'EOF < /dev/null' issues

### Changed
- **safe_file_manager.py**: Added warnings about EOF heredoc issues
- **SAFE_FILE_MANAGER_GUIDE.md**: Enhanced with EOF troubleshooting
- **run_any_python_tool.sh**: Added data_flow_tracker.py and EOF warnings
- **TOOLS_DOCUMENTATION_2025.md**: Added data flow analysis category

### Fixed
- Cleaned up nested code-intelligence-toolkit/code-intelligence-toolkit/ directory
- Organized test files into proper directory structure

## [1.1.2] - 2025-01-26

### Added
- **find_text_v7.py**: Multiline search capability with `--multiline` flag
- **CHANGELOG.md**: Comprehensive version history documentation
- **VERSION file**: Simple version reference
- **Quick Tool Reference**: Added to main README for easy tool lookup

### Changed
- Updated all documentation to reflect latest tool versions
- Updated wrapper script to use find_text_v7.py
- Enhanced README files with "What's New" sections

### Documentation
- Created comprehensive CHANGELOG.md
- Updated main README.md with v1.1.1 features
- Updated docs/README.md with recent updates section
- Updated SEARCH_TOOLS_HELP.md with multiline examples

## [1.1.1] - 2025-01-26

### Added
- **replace_text_ast_v2.py**: Added `--interpret-escapes` flag for escape sequence interpretation in `--comments-only` and `--strings-only` modes
- **find_text_v7.py**: Added `--multiline` (`-U`) flag for searching patterns that span multiple lines
- **release_workflow.sh**: Added `--yes` flag for non-interactive mode in CI/CD pipelines

### Fixed
- Fixed stdin processing bug in replace_text_v8.py (UnboundLocalError for 'sys')
- Fixed configuration handling in replace_text_ast_v2.py (HAS_CONFIG and related functions)
- Made `--line` optional for `--comments-only` and `--strings-only` modes in replace_text_ast_v2.py

### Changed
- Updated documentation to reflect v8 and v7 tool versions

## [1.1.0] - 2025-01-26

### Added
- **replace_text_v8.py**: Major enhancement with `--interpret-escapes` flag for multi-line replacements
  - Supports escape sequences: `\n`, `\t`, `\r`, `\\`, `\b`, `\f`, `\v`, `\0`, `\"`, `\'`
  - Hex sequences: `\xHH` (e.g., `\x20` for space)
  - Unicode: `\uHHHH` and `\UHHHHHHHH`
- Comprehensive documentation for escape sequence features

### Fixed
- Documentation consistency across all files

## [1.0.2] - 2025-01-25

### Added
- SafeGIT v2.0 with comprehensive git safety features
- Safe File Manager with enterprise-grade file operations
- Non-interactive mode support across major tools

### Fixed
- Various bug fixes and performance improvements

## [1.0.1] - 2025-01-24

### Added
- Initial stable release of Code Intelligence Toolkit
- 100+ professional development tools
- AST-based refactoring for Python and Java
- Ripgrep integration for lightning-fast searches
- Comprehensive safety features

### Security
- SafeGIT wrapper to prevent destructive git operations
- Atomic file operations with automatic backups
- Risk-based confirmation system

## [1.0.0] - 2025-01-23

### Added
- Initial release with core functionality
- Basic tool suite for code analysis and refactoring
- Documentation and examples

---

## Release Types

- **Major (x.0.0)**: Breaking changes, major refactoring, API changes
- **Minor (0.x.0)**: New features, significant improvements, backward compatible
- **Patch (0.0.x)**: Bug fixes, typos, documentation updates

## How to Upgrade

```bash
# Pull latest changes
git pull origin master

# Check current version
git describe --tags

# View specific release notes
git show v1.1.1
```

## Automated Releases

Releases are created using the release workflow:

```bash
# Create a patch release
./release_workflow.sh patch "Bug fix description"

# Create a minor release
./release_workflow.sh minor "New feature description"

# Create a major release
./release_workflow.sh major "Breaking changes description"

# Non-interactive mode for CI/CD
./release_workflow.sh --yes minor "Automated release"
```