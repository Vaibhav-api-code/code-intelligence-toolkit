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