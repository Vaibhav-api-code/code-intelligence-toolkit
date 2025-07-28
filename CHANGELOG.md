<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Changelog

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-01-26
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Changelog

All notable changes to the Code Intelligence Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-07-28 - AI Integration Revolution & Universal Release

### 🤖 Complete AI Integration Platform
- **NEW: Unified JSON API (api.py)** - Single endpoint for 100+ code intelligence tools
  - Universal `/analyze` endpoint with intelligent request routing
  - Structured JSON responses with metadata, analysis results, and error handling
  - Python SDK integration for seamless AI agent development
  - RESTful architecture with comprehensive OpenAPI documentation
  - Built-in tool discovery and capability introspection

- **NEW: AI Reasoning System** - Intelligent analysis with natural language explanations
  - Risk assessment with confidence scoring for all analysis results
  - Step-by-step reasoning chains for complex code analysis
  - Contextual insights and actionable recommendations
  - Integration across all major analysis tools (AST, dependency, data flow)

- **NEW: Python SDK Integration (setup.py)** - Professional package management
  - Pip-installable package with proper dependencies
  - High-level Python interfaces for all core functionality
  - AI-first development patterns and best practices
  - Comprehensive examples and integration guides

### 📚 Documentation Revolution
- **TRANSFORMED: README.md** - From manual to powerful landing page
  - Visual ASCII architecture diagram showing system flow
  - "Who Is This For?" section with 4 targeted personas
  - Comprehensive FEATURES.md (400+ lines) with complete tool catalog
  - AI_SAFETY_SETUP.md (500+ lines) with enterprise safety implementation
  - Streamlined key features with strategic navigation to detailed docs

- **NEW: Complete Documentation Structure**
  - AI_INTEGRATION_ROADMAP.md - Strategic implementation phases
  - AI_API_QUICK_START.md - Rapid onboarding for developers
  - ENHANCED_DOC_GENERATOR_README.md - Advanced documentation generation
  - Professional documentation hierarchy for enterprise adoption

### 🌍 Universal Release Preparation
- **Project-Specific Reference Cleanup** - Ready for open-source distribution
  - All hardcoded package names changed to generic examples (com.example.*)
  - Trading/Bookmap-specific terms removed from all tools
  - Build configurations updated to use universal groupIds
  - Test files converted to generic package structure
  - All tools now use universally applicable examples

### 🌟 Enhanced Core Features
- **Enhanced: doc_generator_enhanced.py** - AST tool integration masterpiece
  - Integrates 5 specialized AST analysis tools for comprehensive code understanding
  - Interactive HTML format with 6-tab navigation interface
  - Full Java/Python feature parity including data flow analysis
  - ANSI code stripping for clean HTML output
  - Smart caching for improved performance
  - 7 documentation styles including architecture and call graphs
  - Graceful degradation when individual tools fail

### 🔧 Infrastructure Improvements
- **Enhanced: release_workflow.sh** - Added non-interactive automation support
  - `--yes` flag for auto-confirming all prompts (CI/CD friendly)
  - `--non-interactive` flag for strict non-interactive mode
  - Environment variable support: `RELEASE_WORKFLOW_ASSUME_YES=1`
  - Auto-detection of CI environments (GitHub Actions, GitLab CI, Jenkins, Travis)
  - Comprehensive help system with `--help` flag

### 🎯 Strategic Achievement
- **Complete AI Integration Platform**: The toolkit now provides a unified, AI-ready interface for all code intelligence operations
- **Universal Applicability**: Clean, generic codebase ready for widespread open-source adoption
- **Professional Documentation**: Enterprise-grade documentation structure with clear navigation paths
- **Developer Experience**: Streamlined onboarding with visual guides and comprehensive examples

## [1.3.0] - 2025-07-27

### 🌟 Major New Features
- **NEW: data_flow_tracker_v2.py** - Complete rewrite with intelligence layer
  - Natural language explanations of complex analysis
  - Interactive HTML visualizations with vis.js network graphs
  - Risk assessment with confidence scoring
  - Calculation path tracking and step-by-step breakdowns
  - Type and state evolution monitoring
- **NEW: doc_generator.py** - Automated documentation generation
  - Multiple styles: API docs, user guides, technical analysis, quick reference, tutorials
  - Multiple formats: Markdown, HTML, reStructuredText, docstring injection
  - Intelligence integration with data flow analysis
  - Auto-generated examples and usage patterns

### 🗂️ Tool Organization & Archival
- **Archived older tool versions** to organized `archive/` directory structure
- **Main directory cleanup** - Only latest, stable tool versions remain
- **Version hierarchy** - Clear identification of which tools to use
- **Safe archival process** - All versions preserved with complete git history

### 🐛 Critical Bug Fixes
- **Fixed infinite recursion** in data_flow_tracker_v2.py when tracking cyclic dependencies
- **Enhanced Java method detection** with improved regex patterns for complex signatures
- **Template system reliability** with robust Jinja2 fallback mechanisms

### 📚 Documentation Updates
- **Complete documentation overhaul** - All references updated to latest tool versions
- **Updated performance benchmarks** with current tool names and capabilities
- **Verified examples** - All command examples tested and working
- **Enhanced guides** - README.md, CLAUDE.md, and comprehensive tool documentation

### 🔧 Enhanced Reliability
- **Improved error handling** with better error messages and graceful degradation
- **Template system** with Jinja2 templates and built-in fallbacks
- **Cross-platform compatibility** improvements

## [1.2.3] - 2025-07-27

### Added - Complete Intelligence Platform
- **doc_generator.py**: Revolutionary automated documentation generator leveraging intelligence layer
  - **Five Documentation Styles**: API docs, user guides, technical analysis, quick reference, tutorials
  - **Four Output Formats**: Markdown, HTML, docstring, reStructuredText
  - **Intelligence Integration**: Leverages data_flow_tracker_v2.py for smart dependency analysis
  - **Depth Control**: Surface, medium, deep analysis levels with complexity assessment
  - **Auto-Generated Examples**: Contextually appropriate code samples and usage patterns
  - **Multi-Target Support**: Functions, classes, and entire modules
- **Complete Code Intelligence Platform**: Analysis + Visualization + Documentation = Complete Understanding
  - **Strategic Achievement**: Transform complex codebases into manageable, understandable, well-documented systems
  - **Knowledge Sharing**: Enable confident development, debugging, refactoring for all skill levels

### Enhanced
- **README.md**: Updated with documentation generation features and six core capabilities
- **DATA_FLOW_TRACKER_GUIDE.md**: Added comprehensive documentation generation section
- **Tool Reference**: Added doc_generator.py to quick reference with updated command examples

### Documentation
- **Complete Platform Documentation**: Updated all guides to reflect the complete intelligence platform
- **Combined Workflow Examples**: Shows integration between analysis, visualization, and documentation

## [1.2.2] - 2025-07-27

### Added - Intelligence Layer
- **Natural Language Explanations** (`--explain` flag): Transform complex technical analysis into intuitive explanations
  - **Impact Analysis Explanations**: Risk assessment with actionable recommendations
  - **Calculation Path Explanations**: Step-by-step algorithm understanding in plain English
  - **State Tracking Explanations**: Type evolution analysis with warnings and advice
  - **Template-Based Consistency**: Professional formatting with risk-based messaging
- **Interactive HTML Visualization** (`--output-html` flag): Self-contained professional reports
  - **vis.js Network Graphs**: Click-to-explore node relationships and dependencies
  - **Risk-Based Styling**: Color-coded by impact level and confidence scoring
  - **Progressive Disclosure**: Overview → drill-down → code context workflow
  - **Export Capabilities**: Save visualizations as PNG images for documentation
  - **Responsive Design**: Works on desktop, tablet, and mobile devices
  - **Zero Dependencies**: Self-contained HTML files using vis.js CDN

### Enhanced
- **data_flow_tracker_v2.py**: Intelligence layer integration across all analysis modes
  - All V2 features (impact, calculation path, state tracking) support explanations
  - Standard forward/backward analysis now supports natural language explanations
  - Combined intelligence: explanation + visualization in single command
- **Five Core Capabilities**: Complete V2 suite now includes intelligence transformation
- **Strategic Achievement**: Visualization + Explanation = Intuitive Code Understanding

### Documentation
- **README.md**: Updated with intelligence layer features and wrapper clarification
- **DATA_FLOW_TRACKER_GUIDE.md**: Comprehensive intelligence layer documentation with examples
- **Quick Start**: Added note about run_any_python_tool.sh wrapper purpose

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