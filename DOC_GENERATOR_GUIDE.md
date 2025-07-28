<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Documentation Generator Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-27
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Documentation Generator - Comprehensive Guide

**Related Code Files:**
- `code-intelligence-toolkit/doc_generator.py` - Original with sophisticated content generation and intelligence layer
- `code-intelligence-toolkit/doc_generator_enhanced.py` - Enhanced AST integration and interactive HTML (complementary tool)
- `code-intelligence-toolkit/data_flow_tracker_v2.py` - Underlying analysis engine
- `code-intelligence-toolkit/navigate_ast_v2.py` - AST navigation tool
- `code-intelligence-toolkit/method_analyzer_ast_v2.py` - Method analysis tool
- `code-intelligence-toolkit/trace_calls_with_timeout.py` - Call tracing tool
- `code-intelligence-toolkit/show_structure_ast.py` - Structure analysis tool
- `code-intelligence-toolkit/cross_file_analysis_ast.py` - Cross-file dependency analysis
- `code-intelligence-toolkit/run_any_python_tool.sh` - Wrapper script for execution
- `code-intelligence-toolkit/templates/` - HTML templates (optional Jinja2 support)

---

## Overview

The Documentation Generator comes in two complementary versions, each with unique strengths:

**doc_generator.py (Original)** - Sophisticated content generation with intelligence layer:
- Deep data flow integration with natural language explanations
- Rich, contextual documentation with impact analysis
- Sophisticated helper methods for inferring purpose and extracting parameters
- 2768 lines of comprehensive documentation logic

**doc_generator_enhanced.py (Enhanced)** - AST tool integration with interactive UI:
- Integrates all five major AST analysis tools for comprehensive code understanding
- Interactive HTML with 6-tab navigation interface
- Adds architecture and call-graph documentation styles
- Focuses on tool integration over content generation

Choose based on your needs:

- **Navigation Analysis**: Uses navigate_ast_v2.py for precise symbol location
- **Call Flow Analysis**: Uses method_analyzer_ast_v2.py and trace_calls_with_timeout.py for method relationships
- **Data Flow Analysis**: Uses data_flow_tracker_v2.py for variable dependencies and impact analysis
- **Structure Analysis**: Uses show_structure_ast.py for hierarchical code organization
- **Cross-File Dependencies**: Uses cross_file_analysis_ast.py for import and dependency tracking

Built on top of the data flow analysis engine, it automatically generates documentation that goes far beyond simple code comments to provide deep insights into code behavior, dependencies, and architectural patterns.

### Key Features

- **Multiple Documentation Styles**: API docs, user guides, technical references, tutorials, quick references, architecture docs, and call graphs
- **Comprehensive AST Integration**: Combines 5 specialized AST tools for complete code analysis
- **Interactive HTML Reports**: Multi-tab navigation with Overview, Navigation, Call Flow, Data Flow, Structure, and Dependencies
- **Full Java/Python Parity**: Both languages support all analysis features including data flow
- **Intelligent Analysis**: Leverages data flow tracking and impact analysis for accuracy
- **Natural Language Explanations**: Converts complex code behavior into readable explanations
- **Multiple Output Formats**: Markdown, HTML, interactive HTML, reStructuredText, and Python docstrings
- **Depth Control**: Surface, medium, or deep analysis levels
- **Smart Caching**: Caches expensive AST operations for better performance
- **ANSI Code Handling**: Automatically strips color codes for clean HTML output

### When to Use

- **API Documentation**: Generate comprehensive API references
- **Code Reviews**: Create detailed technical documentation for review processes
- **Knowledge Transfer**: Document complex algorithms and business logic
- **Onboarding**: Create user-friendly guides for new team members
- **Technical Writing**: Automate documentation creation for technical writers

## Installation & Requirements

### Core Requirements
```bash
# Original version
./run_any_python_tool.sh doc_generator.py --help

# Enhanced version with full AST integration (recommended)
./run_any_python_tool.sh doc_generator_enhanced.py --help
```

### Language Support
- **Python**: Full AST analysis with complete feature support
- **Java**: Requires `javalang>=0.13.0` (included in requirements-core.txt)

### Optional Dependencies
- **Enhanced HTML**: `markdown>=3.3.0` for better HTML conversion (requirements-optional.txt)
- **Template Support**: `jinja2>=3.0.0` for clean HTML templates (requirements-optional.txt)

## Quick Start

### Basic Documentation Generation

```bash
# Generate API documentation for a function
./run_any_python_tool.sh doc_generator_enhanced.py --function calculate --file module.py --style api-docs

# Generate user guide for a class
./run_any_python_tool.sh doc_generator_enhanced.py --class UserManager --file auth.py --style user-guide --depth deep

# Generate interactive HTML documentation with all AST analysis
./run_any_python_tool.sh doc_generator_enhanced.py --class MyClass --file MyClass.java --style api-docs --format interactive

# Generate architecture documentation
./run_any_python_tool.sh doc_generator_enhanced.py --module --file database.py --style architecture --format html

# Generate call graph visualization
./run_any_python_tool.sh doc_generator_enhanced.py --function process --file module.py --style call-graph --format markdown
```

## Command-Line Reference

### Required Arguments
- `--file FILE` - Source file to analyze (Python or Java)
- One target type: `--function NAME`, `--class NAME`, or `--module`

### Documentation Targets
- `--function FUNCTION` - Document a specific function
- `--class CLASS_NAME` - Document a specific class
- `--module` - Document the entire module

### Style Options
- `--style {api-docs,user-guide,technical,quick-ref,tutorial,architecture,call-graph}` - Documentation style (default: api-docs)
  - `api-docs`: Comprehensive API reference with all AST analysis
  - `user-guide`: End-user focused documentation
  - `technical`: Deep technical implementation details
  - `quick-ref`: Concise reference guide
  - `tutorial`: Step-by-step learning guide
  - `architecture`: System design and structure overview
  - `call-graph`: Visual representation of function/method relationships

### Analysis Depth
- `--depth {surface,medium,deep}` - Analysis depth level (default: medium)

### Output Format
- `--format {markdown,html,interactive,docstring,rst}` - Output format (default: markdown)
  - `markdown`: Standard Markdown format
  - `html`: Static HTML with styling
  - `interactive`: Interactive HTML with tabbed navigation (recommended for api-docs style)
  - `docstring`: Python docstring format
  - `rst`: reStructuredText format

### Output Control
- `--output OUTPUT` - Output file (default: stdout)
- `--quiet` - Suppress progress messages
- `--verbose` - Show detailed error information

## Documentation Styles

### 1. API Documentation (`api-docs`)

**Purpose**: Technical reference documentation for developers

**Content includes**:
- Function signatures with parameter details
- Purpose and functionality description
- Parameter descriptions and types
- Return value information
- Usage examples with code snippets
- Variable dependencies and data flow
- Interactive visualizations (HTML format)

**Example Output** (Markdown):
```markdown
# Function: `calculate`

**Location**: `calculator.py` (Line 45)

## Purpose
Performs complex calculations based on input parameters with advanced algorithm application.

## Signature
```python
calculate(value: float, params: Dict[str, float], options: float = 0.0)
```

## Parameters
- `value`: Primary input value for calculation
- `params`: Dictionary mapping parameter names to values
- `options`: Optional configuration parameters

## Key Variables
- `processed_value`: Intermediate calculation result
- `final_result`: Final calculated output
- `performance_metric`: Calculation efficiency metric

## Usage Example
```python
result = calculate(75000, {"param1": 0.22, "param2": 0.32}, 12000)
print(f"Result: {result}")
```
```

**When to use**:
- Technical documentation for APIs
- Developer reference materials
- Code review documentation

### 2. User Guide (`user-guide`)

**Purpose**: User-friendly documentation for end users

**Content includes**:
- Plain-language explanations
- Step-by-step usage instructions
- Real-world examples and scenarios
- Common use cases and patterns
- Troubleshooting tips
- Integration guidance

**Example Output**:
```markdown
# Using the Calculator Class

## What it does
The Calculator helps you perform complex calculations automatically. It handles all the mathematical details internally, so you don't have to worry about the implementation complexity.

## When to use it
Use Calculator when you need to:
- Perform automated calculations in your application
- Process numerical data with business logic
- Handle complex computational workflows

## How to use it
1. Create a calculator instance with your tax brackets
2. Call the calculate method with an income amount
3. Get back the exact tax owed

## Example walkthrough
```python
# Step 1: Set up the calculator
calculator = Calculator()

# Step 2: Calculate tax for someone earning $75,000
tax_amount = calculator.calculate(75000)

# Step 3: Use the result
print(f"Tax owed: ${tax_amount:,.2f}")
```
```

**When to use**:
- End-user documentation
- Onboarding materials
- Non-technical stakeholder documentation

### 3. Technical Analysis (`technical`)

**Purpose**: Deep technical analysis for architects and senior developers

**Content includes**:
- Architectural pattern analysis
- Complexity metrics and recommendations
- Data flow analysis with full dependency graphs
- Performance considerations
- Algorithm analysis
- Impact assessment
- Risk factors and recommendations

**Example Output**:
```markdown
# Technical Analysis: processData

## Architecture Overview
The `processData` function follows these architectural patterns:
- **Transformer Pattern**: Balanced input/output data flow
- **Complex Processing**: High variable count indicates sophisticated logic

## Data Flow Analysis
### Dependencies (What This Depends On)
- `input_data`: Core data structure for processing
- `initial_state`: Starting configuration
- `target_state`: Desired end state
- `algorithm_params`: Configuration parameters

### Effects (What This Affects)
- Return value affects 5 downstream functions
- Modifies cache state in RouteCache class
- Triggers logging in performance monitoring system

## Complexity Analysis
- **Variable Count**: 23
- **Dependency Count**: 8
- **Complexity Level**: High - Consider refactoring into smaller functions

## Performance Characteristics
- Time Complexity: O(V log V + E) for Dijkstra's algorithm
- Space Complexity: O(V) for distance and visited arrays
- Memory Usage: ~50KB per 1000 nodes in typical graphs

## Risk Assessment
**MEDIUM RISK**: Changes affect path calculation algorithms used by 3 different services.
Recommendation: Comprehensive testing required for navigation systems.
```

**When to use**:
- Architecture reviews
- Performance optimization
- Complex algorithm documentation
- System design documentation

### 4. Quick Reference (`quick-ref`)

**Purpose**: Concise reference for quick lookup

**Content includes**:
- Essential information only
- Compact format
- Key signatures and parameters
- Minimal examples
- Basic usage patterns

**Example Output**:
```markdown
# process - Quick Reference

**Purpose**: Processes data using advanced algorithms

**Signature**: `process(data: bytes, config: bytes) -> bytes`

**Key Points**:
- Works with 3 variables
- Has 2 dependencies
- Returns processed bytes

**Example**:
```python
result = process(data, config)
```
```

**When to use**:
- Cheat sheets and reference cards
- IDE tooltips and inline help
- Quick lookup during development

### 5. Tutorial (`tutorial`)

**Purpose**: Step-by-step learning material

**Content includes**:
- Learning objectives
- Progressive examples
- Hands-on exercises
- Best practices
- Common pitfalls to avoid
- Building from simple to complex

**Example Output**:
```markdown
# Tutorial: Working with the Connection Class

## What You'll Learn
By the end of this tutorial, you'll understand:
- How to establish secure database connections
- Best practices for connection pooling
- Error handling and retry strategies
- Performance optimization techniques

## Step 1: Basic Connection
Let's start with the simplest possible database connection:

```python
from database import Connection

# Create a connection
db = Connection("localhost", "myapp")
```

## Step 2: Adding Configuration
Now let's add some configuration options:

```python
config = {
    "host": "localhost",
    "database": "myapp",
    "pool_size": 10,
    "timeout": 30
}
db = Connection(config)
```

## Practice Exercises
1. Create a connection to a test database
2. Try different configuration options
3. Handle connection errors gracefully
```

**When to use**:
- Training materials
- Educational content
- Onboarding documentation
- Workshop materials

## Analysis Depth Levels

### Surface Level
- **Focus**: Basic signature and purpose
- **Content**: Function name, basic description, simple example
- **Use case**: Quick overviews and initial documentation

### Medium Level (Default)
- **Focus**: Include dependencies and basic flow
- **Content**: Full signatures, parameter details, usage examples, key dependencies
- **Use case**: Standard documentation needs

### Deep Level
- **Focus**: Complete analysis with all details
- **Content**: Full data flow analysis, impact assessment, complexity metrics, architectural patterns
- **Use case**: Comprehensive technical documentation

## Output Formats

### Markdown (Default)
- **Best for**: README files, GitHub documentation, general purpose
- **Features**: Standard markdown with code blocks and tables
- **Compatibility**: Universal - works with all documentation platforms

### HTML
- **Best for**: Web documentation, interactive reports
- **Features**: Styled output, interactive visualizations, responsive design
- **Advanced**: Uses vis.js for dependency graphs and network visualization

### reStructuredText (RST)
- **Best for**: Sphinx documentation, Python projects
- **Features**: Rich formatting, cross-references, code highlighting
- **Integration**: Works with Read the Docs and Sphinx

### Docstring
- **Best for**: Inline code documentation, IDE integration
- **Features**: Python docstring format, PEP 257 compliant
- **Usage**: Copy directly into Python code as docstrings

## Advanced Features

### Interactive HTML Visualizations

When using `--format html`, the generator creates rich, interactive reports:

**Network Graphs**:
- Variable dependency visualization
- Interactive node exploration
- Zoom and pan capabilities
- Color-coded by variable type

**Collapsible Sections**:
- Expandable analysis details
- Copy-to-clipboard code blocks
- Responsive design for mobile

**Self-Contained Reports**:
- No external dependencies
- Embedded CSS and JavaScript
- Works offline

### Data Flow Integration

The generator leverages data_flow_tracker_v2.py for intelligent analysis:

**Impact Analysis**:
- Shows what functions are affected by changes
- Risk assessment for modifications
- External effect detection

**Calculation Paths**:
- Traces how values are computed
- Essential step identification
- Algorithm flow visualization

**Type Tracking**:
- Variable type evolution
- State change detection
- Safety warnings

### Template System

With Jinja2 installed, the generator supports custom templates:

```bash
# Custom template directory structure
templates/
  doc_generator/
    api_docs.html
    user_guide.html
    technical.html
```

## Enhanced Version Features (doc_generator_enhanced.py)

### Comprehensive AST Tool Integration

The enhanced version integrates all five major AST analysis tools for unprecedented code understanding:

**1. Navigation Analysis (navigate_ast_v2.py)**:
- Precise symbol location and context
- Cross-file symbol tracking
- Import resolution
- Definition finding

**2. Call Flow Analysis (method_analyzer_ast_v2.py + trace_calls_with_timeout.py)**:
- Method call hierarchies
- Argument tracking
- Call frequency analysis
- Execution path visualization

**3. Data Flow Analysis (data_flow_tracker_v2.py)**:
- Variable dependency tracking
- Impact analysis
- Type evolution
- State change detection
- Full Java/Python parity

**4. Structure Analysis (show_structure_ast.py)**:
- Hierarchical code organization
- Class/method relationships
- Annotation support (Java)
- Multi-language parsing

**5. Cross-File Dependencies (cross_file_analysis_ast.py)**:
- Import tracking
- External dependencies
- Module relationships
- Package structure

### Interactive HTML Reports

The enhanced version's `--format interactive` creates multi-tab documentation:

**Tab Structure**:
- **Overview**: Quick summary and key metrics
- **Navigation**: Symbol locations and definitions
- **Call Flow**: Method relationships and execution paths
- **Data Flow**: Variable dependencies and impact analysis
- **Structure**: Code organization and hierarchy
- **Dependencies**: Import and module relationships

**Features**:
- Clean, modern UI with Bootstrap styling
- Tab navigation with JavaScript
- ANSI code stripping for clean output
- Responsive design
- Self-contained (no external dependencies)

### Performance Optimizations

**Smart Caching**:
- AST operations cached per file
- Expensive analyses cached in memory
- Graceful degradation on tool failures

**Error Handling**:
- Individual tool failures don't break generation
- Fallback content for failed analyses
- Clear error reporting

### Java/Python Feature Parity

**Full Java Support**:
- JavaDataFlowAnalyzerV2 for complete data flow
- Method analysis for Java classes
- Structure analysis with annotation filtering
- Import and dependency tracking

**Consistent Features Across Languages**:
- All documentation styles work for both languages
- All output formats supported
- Same analysis depth levels
- Identical interactive HTML structure

## Language-Specific Features

### Python Analysis

**Comprehensive Support**:
- Full AST parsing with all Python constructs
- Type hint extraction and analysis
- Decorator and context manager support
- Async/await pattern recognition
- Exception handling analysis

**Advanced Features**:
- Lambda expression documentation
- Comprehension analysis
- Import dependency tracking
- Class inheritance documentation

### Java Analysis

**Robust Structure Analysis**:
- Class and method documentation
- Package structure analysis
- Method overloading detection
- Basic inheritance patterns

**Limitations**:
- Limited type inference compared to Python
- No generic type parameter analysis
- Basic state tracking capabilities

## Integration Patterns

### CI/CD Integration

```bash
# Generate documentation as part of build process
./run_any_python_tool.sh doc_generator.py \
  --class APIClient \
  --file client.py \
  --style api-docs \
  --format html \
  --output docs/api_client.html

# Batch generate documentation for all modules
for file in src/*.py; do
    ./run_any_python_tool.sh doc_generator.py \
      --module \
      --file "$file" \
      --style api-docs \
      --output "docs/$(basename "$file" .py).md"
done
```

### IDE Integration

```bash
# Generate docstring for copying into code
./run_any_python_tool.sh doc_generator.py \
  --function calculate_metrics \
  --file analytics.py \
  --style api-docs \
  --format docstring \
  --quiet
```

### Documentation Pipeline

```bash
# 1. Generate technical analysis
./run_any_python_tool.sh doc_generator.py \
  --class MyProcessor \
  --file processor.py \
  --style technical \
  --depth deep \
  --output technical/data_processor.md

# 2. Generate user guide
./run_any_python_tool.sh doc_generator.py \
  --class MyProcessor \
  --file processor.py \
  --style user-guide \
  --output guides/data_processor.md

# 3. Generate API reference
./run_any_python_tool.sh doc_generator.py \
  --class MyProcessor \
  --file processor.py \
  --style api-docs \
  --format html \
  --output api/data_processor.html
```

## Best Practices

### Documentation Strategy

1. **Start with API docs** for technical reference
2. **Add user guides** for complex features
3. **Use technical analysis** for architecture reviews
4. **Generate tutorials** for onboarding
5. **Create quick references** for daily use

### Quality Guidelines

- **Medium depth** for most use cases
- **Deep analysis** for critical components
- **HTML format** for stakeholder presentations
- **Markdown format** for version control

### Content Organization

```
docs/
├── api/          # API documentation (api-docs style)
├── guides/       # User guides (user-guide style)
├── technical/    # Technical analysis (technical style)
├── tutorials/    # Learning materials (tutorial style)
└── reference/    # Quick references (quick-ref style)
```

## Troubleshooting

### Common Issues

**1. "Function not found" errors**
```bash
# Check available functions
./run_any_python_tool.sh show_structure_ast.py file.py

# Verify exact function name
./run_any_python_tool.sh find_text_v7.py "def function_name" --file file.py
```

**2. Poor analysis quality**
- Increase depth level: `--depth deep`
- Ensure dependencies are available
- Check for syntax errors in source file

**3. HTML reports not generating**
- Install optional dependencies: `pip install markdown jinja2`
- Check write permissions to output directory
- Use `--verbose` for detailed error messages

**4. Java analysis limitations**
- Install javalang: `pip install javalang>=0.13.0`
- Some advanced features work better with Python

### Debug Mode

```bash
# Enable verbose output for troubleshooting
./run_any_python_tool.sh doc_generator.py \
  --function problematic_function \
  --file problem.py \
  --verbose \
  --style technical \
  --depth deep
```

## Real-World Examples

### Example 1: API Reference Generation

```bash
# Generate complete API documentation for a web service
./run_any_python_tool.sh doc_generator.py \
  --class APIHandler \
  --file api_handler.py \
  --style api-docs \
  --depth deep \
  --format html \
  --output docs/api_reference.html
```

**Result**: Comprehensive API documentation with request/response examples, parameter validation, and error handling details.

### Example 2: Algorithm Documentation

```bash
# Document a complex sorting algorithm
./run_any_python_tool.sh doc_generator.py \
  --function optimize_algorithm \
  --file algorithms.py \
  --style technical \
  --depth deep \
  --format markdown \
  --output docs/algorithm_analysis.md
```

**Result**: Technical analysis showing time complexity, memory usage, and optimization techniques.

### Example 3: User Onboarding Guide

```bash
# Create user-friendly documentation for a configuration class
./run_any_python_tool.sh doc_generator.py \
  --class ConfigManager \
  --file config.py \
  --style user-guide \
  --format html \
  --output guides/configuration_guide.html
```

**Result**: Step-by-step guide for non-technical users to configure the system.

### Example 4: Batch Documentation Generation

```bash
# Generate documentation for all classes in a project
find src/ -name "*.py" -exec basename {} .py \; | while read module; do
    ./run_any_python_tool.sh doc_generator.py \
      --module \
      --file "src/${module}.py" \
      --style api-docs \
      --output "docs/${module}.md"
done
```

**Result**: Complete project documentation with consistent formatting.

## Performance Considerations

### Analysis Speed
- **Small files (< 500 lines)**: All styles and depths, ~1-2 seconds
- **Medium files (500-2000 lines)**: Medium depth recommended, ~3-5 seconds
- **Large files (> 2000 lines)**: Surface depth for speed, ~5-10 seconds

### Memory Usage
- **Basic documentation**: ~5MB per 1000 lines of code
- **Deep analysis**: ~20MB per 1000 lines with full data flow
- **HTML with visualizations**: Additional ~10MB per report

### Optimization Tips
- Use `--depth surface` for quick documentation
- Generate HTML reports for important components only
- Use batch processing for large projects
- Cache results when generating multiple formats

## Customization and Extension

### Custom Templates

Create custom Jinja2 templates for organization-specific formatting:

```html
<\!-- templates/doc_generator/custom_api.html -->
<\!DOCTYPE html>
<html>
<head>
    <title>{{ target.name }} - {{ company_name }} API</title>
    <link rel="stylesheet" href="{{ company_css }}">
</head>
<body>
    <header>
        <img src="{{ company_logo }}" alt="Company Logo">
        <h1>{{ target.name }}</h1>
    </header>
    <\!-- Custom content structure -->
</body>
</html>
```

### Style Customization

Modify CSS for HTML output to match corporate branding:

```css
/* Custom styling for generated HTML */
.api-docs {
    font-family: "Corporate Font", sans-serif;
    color: #corporate-blue;
}

.code-block {
    background: #f8f9fa;
    border-left: 4px solid #corporate-accent;
}
```

## Integration with Documentation Systems

### Sphinx Integration

```python
# conf.py for Sphinx integration
extensions = ['sphinx.ext.autodoc']

# Custom directive for doc_generator content
def setup(app):
    app.add_directive('docgen', DocGenDirective)
```

### MkDocs Integration

```yaml
# mkdocs.yml
nav:
  - API Reference: 
    - MyProcessor: api/my_processor.md
    - ConfigManager: api/config_manager.md
  - User Guides:
    - Getting Started: guides/getting_started.md
```

### GitHub Pages

```yaml
# .github/workflows/docs.yml
name: Generate Documentation
on: [push]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate API docs
        run: |
          ./run_any_python_tool.sh doc_generator.py \
            --module --file src/main.py \
            --style api-docs --format html \
            --output docs/index.html
```

## Conclusion

The Documentation Generator transforms the tedious process of creating comprehensive documentation into an automated, intelligent workflow. By leveraging deep code analysis and multiple presentation styles, it produces documentation that serves different audiences and use cases:

- **Developers** get accurate API references with data flow insights
- **Users** get friendly guides with practical examples
- **Architects** get technical analysis with complexity metrics
- **Educators** get tutorials with progressive learning paths

The tool's integration with the data flow analysis engine ensures that generated documentation reflects the actual behavior of the code, not just surface-level descriptions. This makes it invaluable for maintaining accurate, up-to-date documentation in fast-moving development environments.

Whether you're documenting a single function or an entire codebase, the Documentation Generator provides the flexibility and intelligence needed to create professional, comprehensive documentation that truly serves its intended audience.

## Choosing Between Versions

### Use doc_generator.py when you need:
- **Rich content generation** with natural language explanations
- **Deep intelligence** about code purpose and impact
- **Sophisticated analysis** with contextual understanding
- **Production-ready documentation** with professional formatting

### Use doc_generator_enhanced.py when you need:
- **Interactive HTML** with multi-tab navigation
- **Comprehensive AST analysis** from 5 different tools
- **Architecture and call-graph** documentation styles
- **Visual exploration** of code relationships

### Best Practice:
Consider using both tools together:
1. Use `doc_generator_enhanced.py` for interactive exploration and AST analysis
2. Use `doc_generator.py` for final production documentation with rich content

Both tools are maintained and serve different but complementary purposes in the documentation workflow.

## Enhanced Version Examples (doc_generator_enhanced.py)

### Example 1: Interactive API Documentation

```bash
# Generate interactive HTML with all AST analysis tabs
./run_any_python_tool.sh doc_generator_enhanced.py \
  --class MyClass \
  --file /path/to/MyClass.java \
  --style api-docs \
  --format interactive \
  --output MyClass_Interactive.html
```

**Result**: Interactive HTML with 6 tabs showing Overview, Navigation, Call Flow, Data Flow, Structure, and Dependencies.

### Example 2: Architecture Documentation with Call Graph

```bash
# Generate architecture overview with visual call graph
./run_any_python_tool.sh doc_generator_enhanced.py \
  --module \
  --file core_system.py \
  --style architecture \
  --format html \
  --depth deep \
  --output architecture_overview.html
```

**Result**: Complete architectural analysis with method relationships, data flow patterns, and system structure.

### Example 3: Java Data Flow Analysis

```bash
# Full Java support including data flow analysis
./run_any_python_tool.sh doc_generator_enhanced.py \
  --class MyProcessor \
  --file DataProcessor.java \
  --style technical \
  --format markdown \
  --output java_data_flow.md
```

**Result**: Complete Java analysis with variable dependencies, impact analysis, and type tracking - full parity with Python.

### Example 4: Multi-Style Documentation Generation

```bash
# Generate multiple documentation styles for the same code
for style in api-docs user-guide technical quick-ref tutorial architecture call-graph; do
    ./run_any_python_tool.sh doc_generator_enhanced.py \
      --class UserManager \
      --file auth.py \
      --style $style \
      --format markdown \
      --output "docs/UserManager_${style}.md"
done
```

**Result**: 7 different documentation perspectives for comprehensive coverage.

### Example 5: Call Graph Visualization

```bash
# Generate detailed call graph analysis
./run_any_python_tool.sh doc_generator_enhanced.py \
  --function main \
  --file application.py \
  --style call-graph \
  --format html \
  --depth deep \
  --output call_graph.html
```

**Result**: Visual representation of all function calls, execution paths, and method relationships.

The enhanced version represents the next evolution of intelligent documentation generation, combining the power of multiple AST tools to provide unprecedented code understanding and documentation quality.

