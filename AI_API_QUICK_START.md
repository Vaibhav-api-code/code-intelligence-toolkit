<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

AI API Quick Start Implementation

Author: Code Intelligence Team
Created: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# AI API Quick Start - Implementation Plan

## Immediate Actions (This Week)

### 1. Make `api.py` Production Ready

```bash
# Add to code-intelligence-toolkit/
cp api_prototype.py api.py
chmod +x api.py

# Add shebang and make it runnable
echo '#!/usr/bin/env python3' > api.py.tmp
cat api_prototype.py >> api.py.tmp
mv api.py.tmp api.py
```

### 2. Update `run_any_python_tool.sh` to Include API

Add to the tool list:
```bash
echo "    api.py - Unified JSON API for AI agents (NEW)"
```

Add examples:
```bash
echo "  AI Agent Integration:"
echo "    echo '{\"tool\": \"find_text_v7\", \"params\": {\"TODO\": true, \"--json\": true}}' | $0 api.py"
echo "    $0 api.py --demo  # Run interactive demo"
```

### 3. Create Minimal Documentation

Create `AI_AGENT_GUIDE.md`:
```markdown
# AI Agent Integration Guide

## Quick Start

```python
import subprocess
import json

# Call any tool via JSON API
def call_tool(tool_name, params):
    request = {
        "tool": tool_name,
        "params": params,
        "options": {"non_interactive": True}
    }
    
    proc = subprocess.Popen(
        ["./run_any_python_tool.sh", "api.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    
    stdout, _ = proc.communicate(json.dumps(request))
    return json.loads(stdout)

# Example: Find security issues
result = call_tool("find_text_v7", {
    "password|api_key|secret",
    "--scope": "src/",
    "--extract-method": True
})

if result["success"]:
    findings = result["result"]["matches"]
    print(f"Found {len(findings)} potential security issues")
```
```

## Testing the API

### 1. Basic Functionality Test

```python
# test_api.py
import json
import subprocess

def test_api():
    # Test 1: Simple search
    request = {
        "tool": "find_text_v7",
        "params": {"TODO": True, "--json": True}
    }
    
    proc = subprocess.Popen(
        ["./api.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    
    stdout, _ = proc.communicate(json.dumps(request))
    response = json.loads(stdout)
    
    assert response["success"], "API call failed"
    assert "result" in response, "No result in response"
    print("✅ Test 1 passed: Basic search")
    
    # Test 2: Non-existent tool
    request = {"tool": "fake_tool"}
    # ... similar test
    
    # Test 3: Batch operations
    # ... test batch_execute

if __name__ == "__main__":
    test_api()
```

### 2. AI Integration Test

```python
# test_ai_integration.py
from api_prototype import AICodeAssistant

assistant = AICodeAssistant()

# Test comprehensive analysis
analysis = assistant.analyze_before_change("example.py", "config")
print(f"Risk level: {analysis.get('impact_analysis', {}).get('risk_level')}")
print(f"Safe to proceed: {analysis['safe_to_proceed']}")
```

## Marketing the New API

### 1. Update README.md

Add new section after "Perfect for AI Coding Assistants":

```markdown
### 🆕 Unified JSON API (Just Launched!)

The easiest way for AI agents to use the toolkit:

```python
# One API for all 100+ tools
from code_intelligence_toolkit import api

response = api.execute({
    "tool": "data_flow_tracker_v2",
    "params": {"--var": "user_input", "--file": "app.py"},
    "options": {"include_reasoning": True}
})

# AI-optimized reasoning output
if response["reasoning"]["risk_level"] == "high":
    print("AI Decision: Requires human review")
```

- 10x faster than shell subprocess calls
- Structured JSON input/output
- AI reasoning data included
- Batch operations support
```

### 2. Create Blog Post

Title: "Introducing the Code Intelligence JSON API for AI Agents"

Key points:
- Why subprocess.run() is inefficient for AI
- How structured data improves AI decision making
- Performance comparisons
- Code examples
- Future roadmap (Python SDK)

### 3. Example AI Agents

Create `examples/ai_agents/`:
- `security_scanner.py` - AI agent that finds and fixes security issues
- `refactoring_assistant.py` - AI that safely refactors code
- `documentation_bot.py` - AI that maintains documentation
- `code_reviewer.py` - AI that reviews PRs

## Measuring Success

### Week 1 Metrics
- [ ] API working with all major tools
- [ ] 5+ example AI agents created
- [ ] Documentation complete
- [ ] Performance: <100ms overhead vs direct tool calls

### Month 1 Goals
- [ ] 10+ projects using the API
- [ ] Feedback incorporated
- [ ] Start Python SDK development
- [ ] Partnership discussions with AI platforms

## Next Steps

1. **Today**: Implement `api.py` and basic tests
2. **Tomorrow**: Update documentation and create examples
3. **This Week**: Announce on social media and dev forums
4. **Next Week**: Gather feedback and iterate
5. **Next Month**: Begin Python SDK development

The JSON API is the bridge between the current CLI tools and the future Python SDK. It provides immediate value while setting the foundation for the full SDK implementation.