#!/usr/bin/env python3
"""
Setup configuration for Code Intelligence Toolkit Python SDK

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from package
def get_version():
    version_file = Path(__file__).parent / "src" / "code_intelligence" / "__init__.py"
    if version_file.exists():
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "0.1.0"

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="code-intelligence-toolkit",
    version=get_version(),
    author="Code Intelligence Team",
    author_email="noreply@example.com",
    description="AI-first code analysis and manipulation library for safe, intelligent development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/code-intelligence-toolkit",
    
    # Package configuration
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    
    # Dependencies
    install_requires=requirements or [
        "ast-tools>=0.1.0",
        "typing-extensions>=4.0.0",
        "pathlib2>=2.3.0; python_version<'3.6'",
    ],
    
    # Optional dependencies
    extras_require={
        "java": ["javalang>=0.13.0"],
        "markdown": ["markdown>=3.0.0"],
        "templates": ["jinja2>=3.0.0"],
        "visualization": ["graphviz>=0.20.0"],
        "advanced": ["numpy>=1.20.0", "pandas>=1.3.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "all": [
            "javalang>=0.13.0",
            "markdown>=3.0.0", 
            "jinja2>=3.0.0",
            "graphviz>=0.20.0",
            "numpy>=1.20.0",
            "pandas>=1.3.0",
        ]
    },
    
    # Entry points for CLI tools
    entry_points={
        "console_scripts": [
            "ci-analyze=code_intelligence.cli:analyze_main",
            "ci-document=code_intelligence.cli:document_main",
            "ci-refactor=code_intelligence.cli:refactor_main",
            "ci-diff=code_intelligence.cli:diff_main",
        ],
    },
    
    # Metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    python_requires=">=3.8",
    
    # Include package data
    include_package_data=True,
    package_data={
        "code_intelligence": ["templates/*.html", "templates/*.md"],
    },
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/your-org/code-intelligence-toolkit/issues",
        "Source": "https://github.com/your-org/code-intelligence-toolkit",
        "Documentation": "https://code-intelligence-toolkit.readthedocs.io/",
    },
    
    # Keywords for PyPI
    keywords="code-analysis, ast, refactoring, documentation, ai, safety, static-analysis",
    
    # Zip safety
    zip_safe=False,
)