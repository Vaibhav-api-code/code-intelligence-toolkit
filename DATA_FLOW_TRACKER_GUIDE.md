# Data Flow Tracker Guide

**Related Code Files:**
- `code-intelligence-toolkit/data_flow_tracker.py` - Original implementation of the data flow analysis tool
- `code-intelligence-toolkit/data_flow_tracker_v2.py` - Enhanced version with impact analysis, calculation paths, and type tracking
- `code-intelligence-toolkit/run_any_python_tool.sh` - Wrapper script for execution
- `test_data_flow.py` - Simple test examples
- `test_complex_data_flow.py` - Complex test scenarios

---

## Overview

The Data Flow Tracker is a comprehensive static analysis tool that tracks how data flows through your Python and Java code. It builds a complete dependency graph showing how variables affect each other through assignments, function calls, and complex expressions.

## Key Concepts

### Data Flow Analysis
Data flow analysis tracks how values propagate through a program:
- **Forward Analysis**: Given variable X, find all variables that depend on X
- **Backward Analysis**: Given variable Y, find all variables that Y depends on

### Inter-procedural Analysis
The tool tracks data flow across function boundaries:
```python
def process(x):      # x is parameter
    y = x * 2        # y depends on x
    return y         # return value depends on y

result = process(input_val)  # result depends on input_val through process()
```

## Installation

The tool is already integrated into the code-intelligence-toolkit:
```bash
# Direct usage
python3 code-intelligence-toolkit/data_flow_tracker.py --help

# Through wrapper (recommended)
./run_any_python_tool.sh data_flow_tracker.py --help
```

## Basic Usage

### Forward Tracking (What does X affect?)
```bash
# Track what variable 'x' affects
./run_any_python_tool.sh data_flow_tracker.py --var x --file calc.py

# Example output:
# Variable 'x' affects:
# - y = 2 * x (line 10)
# - z = y + 5 (line 11) 
# - result = z * factor (line 15)
```

### Backward Tracking (What affects Y?)
```bash
# Track what affects variable 'result'
./run_any_python_tool.sh data_flow_tracker.py --var result --direction backward --file calc.py

# Example output:
# Variable 'result' depends on:
# - z (line 15: result = z * factor)
# - factor (line 15: result = z * factor)
# - y (line 11: z = y + 5)
# - x (line 10: y = 2 * x)
```

### Both Directions
```bash
# Track both forward and backward dependencies
./run_any_python_tool.sh data_flow_tracker.py --var total --direction both --file calc.py
```

## Advanced Features

### Inter-procedural Analysis
Track data flow across function calls:
```bash
# Enable inter-procedural tracking
./run_any_python_tool.sh data_flow_tracker.py --var user_input --file app.py --inter-procedural

# Tracks flows like:
# user_input → process_data(input_value) → scaled → transform(scaled) → result
```

### Multiple Files
Analyze entire directories or multiple files:
```bash
# Analyze all Python files in a directory
./run_any_python_tool.sh data_flow_tracker.py --var config --scope src/ --recursive

# Analyze specific files
./run_any_python_tool.sh data_flow_tracker.py --var price --file model.py utils.py calc.py
```

### Output Formats

#### JSON Format
Get structured output for programmatic processing:
```bash
./run_any_python_tool.sh data_flow_tracker.py --var x --file calc.py --format json

# Output:
{
  "forward": {
    "variable": "x",
    "affects": [
      {
        "name": "y",
        "location": "calc.py:10",
        "code": "y = 2 * x",
        "expression": "(2 * x)"
      }
    ],
    "flow_paths": ["x → y", "x → y → z"],
    "total_affected": 3
  }
}
```

#### GraphViz Format
Generate visual dependency graphs:
```bash
# Generate DOT file
./run_any_python_tool.sh data_flow_tracker.py --var x --file calc.py --format graph > flow.dot

# Convert to image
dot -Tpng flow.dot -o flow.png
dot -Tsvg flow.dot -o flow.svg
```

### Show All Variables
Analyze all variables in a file:
```bash
./run_any_python_tool.sh data_flow_tracker.py --show-all --file module.py

# Shows dependency information for every variable found
```

### Limit Analysis Depth
Control how deep to trace dependencies:
```bash
# Only trace 2 levels deep
./run_any_python_tool.sh data_flow_tracker.py --var x --max-depth 2 --file calc.py
```

### Filter by File Pattern
Analyze specific file types:
```bash
# Only analyze Python files
./run_any_python_tool.sh data_flow_tracker.py --var data --scope src/ -g "*.py"

# Exclude test files
./run_any_python_tool.sh data_flow_tracker.py --var config --scope . --exclude "*test*"
```

## Supported Python Constructs

### Basic Operations
- Variable assignments: `x = 5`, `y = x + 2`
- Multiple assignments: `a = b = c = 10`
- Augmented assignments: `x += 1`, `y *= 2`

### Complex Expressions
- Binary operations: `result = (a + b) * (c - d)`
- Ternary operators: `val = x if x > 0 else -x`
- Comparisons: `is_valid = x > 0 and y < 100`
- Boolean logic: `flag = condition1 or condition2`

### Data Structures
- Lists: `data = [x, y, z]`, `first = data[0]`
- Tuples: `point = (x, y)`, `a, b = point`
- Dictionaries: `config = {'a': x, 'b': y}`, `val = config['a']`
- Sets: `unique = {x, y, z}`

### Advanced Features
- Tuple unpacking: `first, second, *rest = values`
- List comprehensions: `squares = [x*x for x in data]`
- Dict comprehensions: `mapped = {k: v*2 for k, v in items.items()}`
- Generator expressions: `gen = (x*2 for x in range(10))`

### Object-Oriented
- Instance variables: `self.value = x`
- Method calls: `result = self.process(data)`
- Property access: `val = obj.property`
- Method chaining: `result = obj.method1().method2().value`

### Control Flow
- Function calls: `result = process(x, y)`
- Return values: `return x * 2`
- Global variables: `global config; config = x`
- Lambda functions: `fn = lambda x: x * 2`

## Supported Java Constructs

### Basic Operations
- Variable declarations: `int x = 5;`
- Assignments: `y = x + 2;`
- Field access: `this.value = x;`

### Expressions
- Binary operations: `result = (a + b) * (c - d);`
- Ternary operators: `val = x > 0 ? x : -x;`
- Method calls: `result = process(x, y);`
- Object creation: `obj = new MyClass(x);`

### Data Structures
- Arrays: `int[] data = {x, y, z};`
- Array access: `first = data[0];`
- Method chaining: `result = obj.method1().method2();`

## Real-World Examples

### Example 1: Configuration Parameter Flow
```python
# config_manager.py
def calculate_timeout(base_timeout, retry_count, backoff_factor):
    adjusted_timeout = base_timeout * (1 + backoff_factor)
    max_wait = adjusted_timeout * retry_count
    final_timeout = min(max_wait, 300)  # Cap at 5 minutes
    return final_timeout

# Track what affects final_timeout
$ ./run_any_python_tool.sh data_flow_tracker.py --var final_timeout --direction backward --file config_manager.py

# Output shows:
# final_timeout depends on:
# - max_wait (from adjusted_timeout and retry_count)
# - adjusted_timeout (from base_timeout and backoff_factor)
```

### Example 2: Data Processing Pipeline
```python
# data_processor.py
input_size = 1000
compression_ratio = 0.75
buffer_multiplier = 2

compressed_size = input_size * compression_ratio
buffer_size = compressed_size * buffer_multiplier
final_allocation = buffer_size + (input_size * 0.1)  # 10% overhead

# Track forward flow from compression_ratio
$ ./run_any_python_tool.sh data_flow_tracker.py --var compression_ratio --file data_processor.py

# Shows how changing compression_ratio affects:
# - compressed_size
# - buffer_size  
# - final_allocation
```

### Example 3: Complex Class Analysis
```python
# analyzer.py
class DataAnalyzer:
    def __init__(self):
        self.scale_factor = 1.5
        self.threshold = 0.02
    
    def analyze_data(self, raw_value, weight, confidence):
        weighted_value = raw_value * weight
        score = (weighted_value * confidence) / self.scale_factor
        
        if score > self.threshold:
            result = score * 100
            return self.normalize_result(result)
        return 0
    
    def normalize_result(self, value):
        return value * 0.95  # 5% adjustment

# Analyze the entire module
$ ./run_any_python_tool.sh data_flow_tracker.py --show-all --file analyzer.py --inter-procedural
```

## Output Interpretation

### Flow Paths
The tool shows complete paths of data flow:
```
x → y → z → result
```
This means: x affects y, which affects z, which affects result

### Location Information
Each dependency includes:
- File and line number: `calc.py:15`
- Actual code: `result = x * factor`
- Parsed expression: `(x * factor)`

### Dependency Counts
- `Total affected variables: N` - How many variables are affected (forward)
- `Total dependencies: N` - How many variables contribute (backward)

## Best Practices

1. **Start with key variables**: Focus on critical values like configuration parameters, user inputs, or calculation results

2. **Use inter-procedural for complex code**: Enable `--inter-procedural` when analyzing code with many function calls

3. **Combine with refactoring**: Use before refactoring to understand impact:
   ```bash
   # See what depends on old_method before renaming
   ./run_any_python_tool.sh data_flow_tracker.py --var old_method --file module.py
   ```

4. **Generate graphs for documentation**: Visual graphs help explain complex calculations

5. **Use JSON for automation**: Parse JSON output for automated dependency checking

## Limitations

1. **Static Analysis**: Only tracks explicit data flow, not runtime behavior
2. **No Alias Analysis**: Doesn't track pointer/reference aliases
3. **Limited Dynamic Features**: Can't track `eval()`, `exec()`, or reflection
4. **No Cross-Language**: Can't track Python calling Java or vice versa

## Troubleshooting

### "Variable not found"
- Check variable name spelling
- Ensure the variable is actually assigned in the code
- Try `--show-all` to see all available variables

### "No files found"
- Check file paths are correct
- Use `--scope` for directories
- Ensure file extensions match (`*.py` for Python)

### Large Output
- Use `--max-depth` to limit traversal depth
- Filter specific variables instead of `--show-all`
- Use `--format json` and process programmatically

## Integration with Other Tools

Combine with other code-intelligence-toolkit tools:

```bash
# Find where a method is defined
./run_any_python_tool.sh navigate_ast.py MyClass.py --to process_data

# Track data flow from that method
./run_any_python_tool.sh data_flow_tracker.py --var result --file MyClass.py

# Then refactor safely
./run_any_python_tool.sh replace_text_ast.py --file MyClass.py result new_result
```

## Version 2 Enhanced Features

Data Flow Tracker V2 adds three powerful capabilities for deeper code intelligence:

### 1. Impact Analysis - Know What Will Break

Shows where data "escapes" its local scope and causes observable effects:

```bash
# See all the places where changing db_config would have effects
./run_any_python_tool.sh data_flow_tracker_v2.py --var db_config --show-impact --file app.py
```

Output shows:
- **Returns**: Functions that return values dependent on the variable
- **Side Effects**: File writes, network calls, console output
- **State Changes**: Modifications to global variables or class members
- **Risk Assessment**: Overall risk level of making changes

Example output:
```
============================================================
Impact Analysis
============================================================

🔄 RETURNS:
  - get_connection at db.py:45
    Returns value dependent on db_config

⚠️  SIDE EFFECTS:
  🟡 file_write at logger.py:89
     External call to write

📝 STATE CHANGES:
  - global_write at config.py:23
    External call to cache_config

────────────────────────────────────────────────────────────
SUMMARY:
  Total exit points: 4
  Functions affected: 3
  High risk count: 1

  ⚡ MEDIUM RISK: External side effects detected - ensure testing covers these
```

### 2. Calculation Path Analysis - Understand Complex Logic

Extracts the minimal "critical path" showing exactly how a value is calculated:

```bash
# Understand how final_price is calculated
./run_any_python_tool.sh data_flow_tracker_v2.py --var final_price --show-calculation-path --file pricing.py
```

Shows only the essential steps, filtering out noise:
```
============================================================
Calculation Path
============================================================

1. base_price = get_product_price()
   Location: pricing.py:10
   ↓

2. tax_rate = lookup_tax_rate(location)
   Inputs: location
   Location: pricing.py:15
   ↓

3. discount = apply_coupon(coupon_code)
   Inputs: coupon_code
   Location: pricing.py:20
   ↓

4. final_price = (base_price * (1 + tax_rate)) - discount
   Inputs: base_price, tax_rate, discount
   Location: pricing.py:25
```

### 3. Type and State Tracking - Catch Bugs Early

Monitors how variable types and states evolve through the code:

```bash
# Track type changes and potential issues
./run_any_python_tool.sh data_flow_tracker_v2.py --var user_data --track-state --file process.py
```

Reveals type changes and warnings:
```
============================================================
Type & State Evolution for 'user_data'
============================================================

📈 TYPE EVOLUTION:
  process.py:10: dict ✓
  process.py:15: dict (nullable) ✓
    Possible values: [None]
  process.py:20: UserModel ✓

🔄 STATE CHANGES:
  process.py:10: assignment
  process.py:15: assignment (in conditional)
  process.py:20: assignment

⚠️  WARNINGS:
  - Variable may be None - add null checks
  - Type changes detected: dict → UserModel
```

### V2 Use Cases

**Before Refactoring**:
```bash
# Check impact before renaming a configuration variable
./run_any_python_tool.sh data_flow_tracker_v2.py --var old_config_name --show-impact --file settings.py
```

**Debugging Complex Calculations**:
```bash
# Understand why a value is wrong
./run_any_python_tool.sh data_flow_tracker_v2.py --var wrong_result --show-calculation-path --file calc.py
```

**Type Safety Validation**:
```bash
# Verify type consistency before deployment
./run_any_python_tool.sh data_flow_tracker_v2.py --var api_response --track-state --file handler.py
```

### Combining V2 Features

You can use V2 alongside V1 features:
```bash
# First, see what affects the variable (V1)
./run_any_python_tool.sh data_flow_tracker.py --var total --direction backward --file calc.py

# Then, understand the calculation path (V2)
./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-calculation-path --file calc.py

# Finally, check impact of changes (V2)
./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-impact --file calc.py
```

## Advanced Use Cases

### Debugging Incorrect Calculations
```bash
# If final_result is wrong, trace back to find the issue
./run_any_python_tool.sh data_flow_tracker.py --var final_result --direction backward --file calc.py
```

### Security Analysis
```bash
# Track where user input flows
./run_any_python_tool.sh data_flow_tracker.py --var user_input --file app.py --inter-procedural
```

### Performance Optimization
```bash
# Find all variables affected by expensive calculation
./run_any_python_tool.sh data_flow_tracker.py --var expensive_calc --file module.py
```

### Code Review
```bash
# Verify no unintended dependencies
./run_any_python_tool.sh data_flow_tracker.py --var sensitive_data --file security.py
```