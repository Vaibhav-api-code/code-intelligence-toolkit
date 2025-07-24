<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Java Intelligence Analysis Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Java Intelligence Analysis Toolkit

A collection of powerful command-line tools for analyzing and refactoring Java and Python code.

## Overview

This toolkit provides a suite of sophisticated tools for developers and software engineers to perform deep analysis and automated refactoring of their codebases. It is designed to be used from the command line and can be integrated into CI/CD pipelines for automated code quality checks.

## Features

*   **Advanced Code Analysis:** Perform deep analysis of your code, including dependency analysis, usage patterns, and call frequency.
*   **AST-Based Refactoring:** Safely refactor your code using Abstract Syntax Trees (ASTs) for a deep understanding of the code's structure.
*   **Ripgrep Integration:** Leverage the power of `ripgrep` for lightning-fast text searching.
*   **Error Analysis:** A suite of tools for analyzing and reporting errors in your toolkit.
*   **Multi-Language Support:** While the toolkit is primarily focused on Java, many of the tools also support Python.

## Getting Started

### Prerequisites

*   Python 3.7+
*   `ripgrep` (for search-related tools)
*   `javalang` (for Java AST parsing)
*   `neo4j` (for some of the example analysis scripts)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/code-intelligence-toolkit.git
    ```
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

The toolkit is a collection of individual Python scripts that can be run from the command line. Here are a few examples:

*   **Find all usages of a method:**
    ```bash
    python find_references_rg.py MyClass.myMethod --scope src/
    ```
*   **Analyze the dependencies of a class:**
    ```bash
    python dependency_analyzer.py com.mycompany.MyClass
    ```
*   **Get a structural overview of a file:**
    ```bash
    python show_structure_ast_v4.py src/main/java/com/mycompany/MyClass.java
    ```

## Tools

The toolkit includes a wide range of tools for different purposes. Here's a brief overview of some of the key tools:

*   **`find_text_v6.py`:** An enhanced text search tool with support for multi-line searching and code block extraction.
*   **`replace_text_v7.py`:** A powerful text replacement tool with block-aware replacement modes and JSON pipeline support.
*   **`dependency_analyzer.py`:** A comprehensive tool for analyzing class dependencies in Java projects.
*   **`unified_refactor.py`:** A multi-language refactoring tool with support for both Python and Java.
*   **`error_dashboard_v2.py`:** A visual summary of tool errors with actionable insights.

For more information on a specific tool, run it with the `--help` flag.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE.txt](LICENSE.txt) file for details.
