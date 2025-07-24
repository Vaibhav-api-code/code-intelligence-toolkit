<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Git Repository Setup Instructions

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-24
Updated: 2025-07-24
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Setting Up Code Intelligence Toolkit as a Standalone Git Repository

This guide will help you set up the Code Intelligence Toolkit as its own Git repository and push it to GitHub/GitLab.

## 📋 Prerequisites

- Git installed on your system
- GitHub/GitLab account
- SSH keys or HTTPS credentials configured

## 🚀 Step 1: Initialize the Repository

Navigate to the toolkit directory and initialize it as a Git repository:

```bash
cd code-intelligence-toolkit
git init
```

## 📝 Step 2: Initial Commit

Add all files and make the initial commit:

```bash
# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: Code Intelligence Toolkit v1.0.0

- 100+ enterprise-grade Python tools for code analysis and refactoring
- Support for Python, Java, JavaScript, and more
- SafeGIT integration for git safety
- Safe File Manager for atomic file operations
- Comprehensive documentation and examples
- All files include MPL 2.0 license headers

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## 🌐 Step 3: Create Remote Repository

### On GitHub:
1. Go to https://github.com/new
2. Repository name: `code-intelligence-toolkit`
3. Description: "Enterprise-grade tools for code analysis, refactoring, and development automation"
4. Make it Public (for open source) or Private
5. **DON'T** initialize with README, .gitignore, or license (we already have them)
6. Click "Create repository"

### On GitLab:
1. Go to https://gitlab.com/projects/new
2. Project name: `code-intelligence-toolkit`
3. Project slug: `code-intelligence-toolkit`
4. Visibility: Public or Private
5. **DON'T** initialize with README
6. Click "Create project"

## 🔗 Step 4: Connect to Remote

After creating the remote repository, connect your local repo:

### For GitHub:
```bash
# Using SSH (recommended)
git remote add origin git@github.com:YOUR_USERNAME/code-intelligence-toolkit.git

# OR using HTTPS
git remote add origin https://github.com/YOUR_USERNAME/code-intelligence-toolkit.git
```

### For GitLab:
```bash
# Using SSH (recommended)
git remote add origin git@gitlab.com:YOUR_USERNAME/code-intelligence-toolkit.git

# OR using HTTPS
git remote add origin https://gitlab.com/YOUR_USERNAME/code-intelligence-toolkit.git
```

## 📤 Step 5: Push to Remote

Push your code to the remote repository:

```bash
# Push main branch and set upstream
git push -u origin main

# If your default branch is 'master':
git push -u origin master
```

## 🏷️ Step 6: Create a Release (Optional)

Tag your first release:

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0: Initial public release"

# Push tags
git push origin --tags
```

## 📋 Step 7: Update Repository Settings

### On GitHub:
1. Go to Settings → General
2. Add topics: `python`, `code-analysis`, `refactoring`, `developer-tools`, `ast`, `git-safety`
3. Go to Settings → Pages (if you want GitHub Pages documentation)

### Add Repository Description:
```
Enterprise-grade toolkit with 100+ Python tools for code analysis, safe refactoring, and development automation. Features AST-based navigation, SafeGIT integration, atomic file operations, and multi-language support.
```

## 🛡️ Step 8: Set Up Branch Protection (Recommended)

Protect your main branch:

1. Go to Settings → Branches
2. Add rule for `main` (or `master`)
3. Enable:
   - Require pull request reviews
   - Dismiss stale pull request approvals
   - Require status checks to pass

## 📢 Step 9: Add Badges to README (Optional)

Add these badges to the top of your README.md:

```markdown
![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Tools](https://img.shields.io/badge/tools-100+-orange.svg)
```

## 🎉 Done!

Your Code Intelligence Toolkit is now available as a standalone repository! 

### Next Steps:
- Share the repository URL with your team
- Add collaborators if needed
- Set up CI/CD workflows
- Create issues for future enhancements
- Accept pull requests from contributors

### Repository URL Format:
- GitHub: `https://github.com/YOUR_USERNAME/code-intelligence-toolkit`
- GitLab: `https://gitlab.com/YOUR_USERNAME/code-intelligence-toolkit`

---

Remember to use SafeGIT for all git operations to prevent accidental data loss:
```bash
./run_any_python_tool.sh safegit.py [command]
```