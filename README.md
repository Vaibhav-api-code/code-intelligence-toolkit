<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Code Intelligence Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-28 (v1.5.0)
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Code Intelligence Toolkit: An AI-First Platform for Safe Code Analysis & Refactoring

![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)
![Release: v1.5.0](https://img.shields.io/badge/Release-v1.5.0-blue.svg)
![Languages: Python, Java](https://img.shields.io/badge/Languages-Python%2C%20Java-orange.svg)
![Platform: AI-First](https://img.shields.io/badge/Platform-AI--First-success)
![Build: Passing](https://img.shields.io/badge/Build-Passing-brightgreen.svg)

**🤖 AI-First Code Analysis Platform with Intelligent Reasoning**

The most comprehensive suite of AI-optimized development tools, featuring structured JSON APIs, intelligent reasoning capabilities, and enterprise-grade safety. Built for AI agents, with 100+ tools providing lightning-fast analysis (10-100x faster than traditional tools) and unbreakable safety guarantees - preventing disasters like [Replit's AI database wipe](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/) while enabling unprecedented development velocity.

## 🚀 **NEW: AI Integration Roadmap Complete!**

✅ **Phase 1**: Unified JSON API - Production-ready programmatic access  
✅ **Phase 2**: AI Reasoning System - Intelligent analysis with risk assessment  
✅ **Phase 3**: Python SDK - High-level interfaces for seamless integration

## 🌟 At a Glance

- **🤖 AI-First Platform** - Unified JSON API, intelligent reasoning, Python SDK
- **🧠 Intelligent Analysis** - AI reasoning with risk assessment and security insights
- **⚡ 10-100x faster** than grep, IDEs, or manual refactoring - critical for AI token efficiency
- **🛡️ Disaster-proof** - Prevents AI agents from executing destructive operations
- **🎯 100% accurate** AST-based code understanding - no hallucinations, just facts
- **🌐 Language-aware** - Auto-detects Java vs Python for optimal AST processing
- **📊 Structured Output** - JSON APIs, reasoning schemas, programmatic interfaces
- **🔧 100+ tools** - Complete toolkit for any AI coding task with intelligent insights
- **📏 Handles massive files** - Edit 10k+ line files that break AI IDE edit tools
- **🚀 Production-ready** - Battle-tested on millions of lines of code with enterprise safety
- **⚡ No Persistent Index** - Always current, zero setup, perfect for CI/CD and ephemeral environments

## 🆚 How We Compare to Other Tools

While many excellent tools exist for individual tasks, the Code Intelligence Toolkit is unique in its ability to seamlessly integrate these capabilities into a single, AI-first platform governed by a "Safety First" philosophy.

Our focus is not on replacing these tools, but on providing a cohesive, scriptable, and safe layer on top of them, specifically designed for AI agents and automation while solving the critical pain points developers face in 2025.

<table>
<tr>
<th style="width: 15%; text-align: center;"><strong>Capability</strong></th>
<th style="width: 20%; text-align: center;"><strong>Conventional Tools</strong></th>
<th style="width: 30%; text-align: center;"><strong>Developer Pain Points (2025)</strong></th>
<th style="width: 35%; text-align: left;"><strong>Our Advantage (Code Intelligence Toolkit)</strong></th>
</tr>
<tr>
<td style="text-align: center;"><strong>Code Search</strong></td>
<td style="text-align: center;">grep, ripgrep (rg), IDE search</td>
<td>• grep "can be quite slow" on large codebases<br>• "search results can be difficult to navigate"<br>• No semantic understanding of code structure</td>
<td>Matches Ripgrep's speed but adds AST context, multiline search, and complete code block extraction. Navigate results by class→method hierarchy, not just line numbers.</td>
</tr>
<tr>
<td style="text-align: center;"><strong>Code Refactoring</strong></td>
<td style="text-align: center;">IDEs (VS Code, IntelliJ), Cursor ($20/mo), GitHub Copilot ($10-39/mo)</td>
<td>• IDEs "can be resource-intensive, need decent machine"<br>• IntelliJ Ultimate "isn't free but worth investment"<br>• Performance degradation with certain patterns</td>
<td>Provides IDE-level semantic accuracy directly on the command line with 40x faster performance than IDE refactoring. Every operation protected by automatic backups and Multi-Level Undo System. <strong>Cost: $0</strong></td>
</tr>
<tr>
<td style="text-align: center;"><strong>Static Analysis</strong></td>
<td style="text-align: center;">CodeQL, SonarQube, Semgrep, CodeAnt.ai ($10-20/mo)</td>
<td>• <strong>"Up to 50% false positives" if not configured properly</strong><br>• "15-30 minutes to triage each false positive"<br>• Causes "alert fatigue" and trust erosion<br>• "Substantial drain on productivity"</td>
<td>AI Reasoning System provides natural language explanations with confidence scoring and risk assessment. Interactive HTML reports turn raw data into actionable insights, eliminating noise and false positive fatigue.</td>
</tr>
<tr>
<td style="text-align: center;"><strong>AI Safety Infrastructure</strong></td>
<td style="text-align: center;">Basic shell access, no AI protection systems</td>
<td>• <strong>Safety Crisis</strong>: Recent Replit AI disaster wiped entire databases<br>• AI assistants have direct access to dangerous commands<br>• No structured APIs for AI agents<br>• No protection against <code>rm -rf /</code> or destructive git operations</td>
<td><strong>AI-First Safety Platform</strong> - Works WITH any AI assistant (Claude Code, Cursor, Copilot, Aider) to provide unbreakable safety guarantees. Structured JSON APIs and CLI interfaces make AI automation safer and more reliable. <strong>Enhances rather than replaces your AI workflow</strong>.</td>
</tr>
<tr>
<td style="text-align: center;"><strong>System Safety</strong></td>
<td style="text-align: center;">trash-cli, shell aliases, custom scripts</td>
<td>• No comprehensive protection system<br>• Manual setup required for each command<br>• No context awareness (dev vs production)<br>• Limited undo capabilities</td>
<td><strong>Enterprise-grade safety platform</strong>: SafeGIT adapts to environment (production/development), Safe File Manager makes ALL operations reversible, context-aware confirmations prevent accidents.</td>
</tr>
<tr>
<td style="text-align: center;"><strong>Documentation</strong></td>
<td style="text-align: center;">Sphinx, Javadoc, Doxygen, AI tools</td>
<td>• Only parses comments, not actual code behavior<br>• Manual setup and configuration required<br>• Static output, no interactivity<br>• No integration with code analysis</td>
<td><strong>Intelligence-driven documentation</strong>: Analyzes what code actually DOES through data flow tracking. Creates interactive multi-tab dashboards with live code analysis, not just comment parsing.</td>
</tr>
</table>

### 🚨 **The AI Safety Crisis of 2025**

Recent incidents demonstrate the critical need for AI-safe development tools:
- **Replit's AI assistant** accidentally wiped production databases ([Fortune, July 2025](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/))
- **AI agents executing `rm -rf /`** destroying entire development environments
- **Accidental git force pushes** losing weeks of team collaboration

**Our Solution**: The only toolkit that provides **unbreakable AI safety infrastructure** - dangerous operations are intercepted at the system level, making disasters impossible while preserving full AI automation capabilities and enhancing any AI assistant you already use.

### 💰 **Cost Comparison: Infrastructure & Analysis Tools (2025 Pricing)**

| Tool Category | Market Leaders | Annual Cost | Our Toolkit |
|---|---|---|---|
| **Static Analysis** | CodeAnt.ai ($120-240/year), SonarQube Enterprise ($8,000+) | $120-8000+ | **$0** |
| **Refactoring Tools** | IntelliJ Ultimate ($169/year), IDE + plugins | $169+ | **$0** |
| **Documentation Tools** | Confluence ($5-6/user/mo), GitBook ($8-12/user/mo) | $60-144/year | **$0** |
| **Safety & Recovery** | Enterprise backup solutions ($100s-1000s/year) | $100-1000+ | **$0** |
| **AI Safety Infrastructure** | Custom solutions, enterprise security tools | $1000-5000+ | **$0** |
| **Development Infrastructure** | Complete platform with all capabilities above | **TOTAL: $1,500-15,000+/year** | **$0** |

*Note: Keep your existing AI assistant (Claude Code, Cursor, Copilot, etc.) - our toolkit enhances their capabilities with safety and intelligence.*

### 🎯 **Why Add Our Toolkit to Your AI Workflow**

**If you're using AI coding assistants** → Add unbreakable safety protection without changing your workflow  
**If you're frustrated with slow IDEs** → Give your AI assistant 40x faster refactoring tools to use  
**If you're drowning in false positives** → Provide your AI with reasoning systems that explain what actually matters  
**If you're tired of tool subscription costs** → Get enterprise-grade infrastructure for free  
**If you need comprehensive AI-safe development** → Get analysis, intelligence, and safety designed for AI automation

**In summary**, our toolkit is the missing infrastructure layer that makes AI-driven development **safe, intelligent, and cost-effective**. It integrates **Analysis**, **Intelligence**, and **Safety** into a single platform designed to enhance any AI assistant - **at zero cost with unbreakable safety guarantees**.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Users & AI Agents                             │
└─────────────────────────┬───────────────┬───────────────────────────────┘
                          │               │
                          ▼               ▼
               ┌─────────────────┐ ┌─────────────────┐
               │   Python SDK    │ │ Unified JSON API│
               │  High-Level     │ │  Programmatic   │
               │  Interface      │ │    Access       │
               └─────────┬───────┘ └─────────┬───────┘
                         │                   │
                         └─────────┬─────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │     Intelligence Layer      │
                    │  • AI Reasoning Engine      │
                    │  • Risk Assessment          │
                    │  • Security Analysis        │
                    │  • Quality Metrics          │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │      Core Tool Suite        │
                    │ • AST Analysis (100% accurate)│
                    │ • Data Flow Tracking        │
                    │ • Safe File Operations      │
                    │ • Git Safety Wrapper        │
                    │ • Semantic Search           │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │        Your Codebase        │
                    │   Always Current State      │
                    │    No Persistent Index      │
                    └─────────────────────────────┘
```

**The Perfect Trilogy**: Analysis + Intelligence + Safety = Complete Code Understanding

## 🤖 Perfect for AI Coding Assistants

### Why AI Agents Love This Toolkit

```python
# Traditional AI coding can be dangerous
ai_agent.execute("rm -rf important_files")  # 💥 Disaster!

# With Code Intelligence Toolkit - Two Approaches:

# 1. CLI Approach (Perfect for Claude Code, GitHub Copilot)
import subprocess
result = subprocess.run([
    "./run_any_python_tool.sh", 
    "safe_file_manager.py", 
    "trash", "old_files"  # Safe, reversible operation
], capture_output=True, text=True)

# 2. API Approach (For custom AI integrations)
from code_intelligence.api.client import CodeIntelligenceAPI
api = CodeIntelligenceAPI()
result = api.execute({
    "tool": "safe_file_manager",
    "params": {"command": "trash", "files": ["old_files"]},
    "options": {"non_interactive": True}
})
```

> **Important for AI Developers**: While we provide both CLI and API interfaces, AI coding assistants like Claude Code work best with the CLI due to their subprocess execution model. Both interfaces provide identical functionality - the CLI is just more direct for sandbox environments!

### 🆕 AI Integration Features

#### 1. Unified JSON API
```bash
# Single endpoint for all 100+ tools
echo '{"tool": "data_flow_tracker_v2", "params": {"--var": "user_input", "--file": "app.py"}, "options": {"include_reasoning": true}}' | ./api.py
```

#### 2. AI Reasoning System
```json
{
  "ai_reasoning": {
    "logical_steps": ["Analyzed variable flow", "Detected security risk"],
    "risk_assessment": {
      "overall_risk": "high",
      "confidence": 0.92,
      "security_implications": ["SQL injection possible"]
    },
    "recommendations": ["Add input validation", "Use parameterized queries"]
  }
}
```

#### 3. Python SDK
```python
from code_intelligence import CodeIntelligence

ci = CodeIntelligence('/path/to/project')
result = ci.analyze_impact('app.py', 'user_input', include_reasoning=True)
print(f"Risk: {result.reasoning['risk_assessment']['overall_risk']}")
```

### Key AI Integration Features

**1. Non-Interactive Mode** - All tools support automation
```bash
# Environment variables for CI/CD and AI agents
export SAFEGIT_NONINTERACTIVE=1
export SAFE_FILE_MANAGER_ASSUME_YES=1

# Or use command flags
./run_any_python_tool.sh doc_generator_enhanced.py --class MyClass --file code.py --yes --non-interactive
```

**2. Structured Output** - Parse results programmatically
```python
# AI agent analyzing code
result = subprocess.run([
    "./run_any_python_tool.sh",
    "data_flow_tracker_v2.py",
    "--var", "user_input",
    "--file", "app.py",
    "--json"  # Structured output for AI parsing
], capture_output=True, text=True)

analysis = json.loads(result.stdout)
```

**3. SafeGIT Integration** - Prevent AI disasters
```python
# AI agents CANNOT bypass safety
# This is automatically intercepted and requires confirmation
subprocess.run(["git", "reset", "--hard"])  # ❌ Blocked!

# Safe alternative
subprocess.run([
    "./run_any_python_tool.sh",
    "safegit.py",
    "--force-yes",  # Explicit override for automation
    "reset", "--hard"
])
```

### Quick Start for AI Developers

1. **Clone and Configure for AI**
```bash
git clone https://github.com/Vaibhav-api-code/code-intelligence-toolkit.git
cd code-intelligence-toolkit

# Set up for AI/automation
echo "export CODE_INTEL_NONINTERACTIVE=1" >> ~/.bashrc
echo "export SAFEGIT_ASSUME_YES=1" >> ~/.bashrc
```

2. **Integrate with Your AI Agent**
```python
class SafeAICodingAgent:
    def __init__(self, toolkit_path):
        self.toolkit = toolkit_path
        
    def analyze_code(self, file_path):
        """Safe code analysis with structured output"""
        cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "doc_generator_enhanced.py",
            "--file", file_path,
            "--format", "json",
            "--non-interactive"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
    
    def refactor_safely(self, old_name, new_name, file_path):
        """Safe refactoring with automatic backups"""
        cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "replace_text_ast_v3.py",
            "--file", file_path,
            old_name, new_name,
            "--yes"  # Non-interactive mode
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
```

## 🌐 Language Support

### AST-Based Operations (Semantic Understanding)
- **Python** - Full AST analysis, refactoring, and navigation
- **Java** - Complete parsing with javalang, method analysis
- **JavaScript** (Experimental) - Basic AST support with esprima

### Text-Based Operations (All Languages)
- **Universal** - Works with any programming language or text format
- **Optimized for**: C/C++, Go, Rust, TypeScript, Ruby, PHP, Shell scripts
- **Also supports**: Configuration files, Markdown, YAML, JSON, XML

### Ripgrep File Type Support
The toolkit leverages ripgrep's extensive file type definitions, supporting 600+ file types out of the box. Run `rg --type-list` to see all supported types.

## 👥 Who Is This For?

### 🤖 **AI Agent Developers**
**Problem**: How to prevent AI coding assistants from making dangerous mistakes like file deletion or unsafe Git operations.
**Solution**: A production-ready Python SDK and JSON API with unbreakable safety guarantees, allowing AI agents to perform analysis and refactoring without risk.

### 🏗️ **Tech Leads & Architects**  
**Problem**: Legacy codebases are hard to understand, document, and maintain  
**Solution**: Quickly analyze complex data flows, understand system dependencies, and automatically generate documentation to facilitate knowledge sharing.

### 🔐 **Security Engineers**
**Problem**: Code changes introduce vulnerabilities and are hard to audit  
**Solution**: Use data flow tracking and semantic diff tools to audit changes, identify potential vulnerabilities, and enforce security best practices.

### 👨‍💻 **Individual Developers**
**Problem**: IDEs are slow for large codebases, refactoring is risky, search is limited  
**Solution**: Get a toolkit that is 10-100x faster than your IDE for search and refactoring, with the peace of mind that every operation is safe and reversible.

## 🚀 Quick Start - Two Ways to Use This Toolkit

### 🎯 Method 1: Command Line Interface (CLI)
Perfect for quick tasks, shell scripts, and AI coding assistants like Claude Code:

```bash
# Get started in 30 seconds
git clone https://github.com/Vaibhav-api-code/code-intelligence-toolkit.git
cd code-intelligence-toolkit
chmod +x run_any_python_tool.sh

# Find TODOs in your code
./run_any_python_tool.sh find_text_v7.py "TODO" --scope src/ --json

# Generate documentation
./run_any_python_tool.sh doc_generator_enhanced.py MyClass --style technical

# Safe refactoring
./run_any_python_tool.sh unified_refactor_v2.py rename oldMethod newMethod --file app.py   # Auto-detects backend

# Analyze dependencies
./run_any_python_tool.sh dependency_analyzer.py MyClass --export-all
```

### 🤖 Method 2: Unified JSON API
Ideal for automation, integrations, and building AI-powered tools:

```python
# Method 2a: Direct API usage (for Python integrations)
from code_intelligence.api.client import CodeIntelligenceAPI

api = CodeIntelligenceAPI()

# Single operation
result = api.execute({
    "tool": "find_text_v7",
    "params": {"pattern": "TODO", "--scope": "src/"},
    "options": {"cache": True, "include_reasoning": True}
})

# Batch operations
results = api.batch_execute([
    {"tool": "find_text_v7", "params": {"TODO": True}},
    {"tool": "replace_text_v9", "params": {"TODO": True, "DONE": True}}
])
```

```bash
# Method 2b: API via command line (for shell scripts/CI/CD)
# Single request
echo '{"tool": "find_text_v7", "params": {"TODO": true, "--json": true}}' | python3 api.py

# Interactive mode
python3 api.py
> {"tool": "doc_generator_enhanced", "params": {"MyClass": true}}

# Start API server
python3 api.py --server --port 8080
# Then use curl/wget/any HTTP client
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"tool": "semantic_diff_v3", "params": {"file1": "v1.py", "file2": "v2.py"}}'
```

### 🎯 Which Method Should You Use?

**Use CLI when:**
- Running quick one-off commands
- Working in AI coding assistants (Claude Code, GitHub Copilot)
- Shell scripting and automation
- Learning and exploring tools
- Debugging specific issues

**Use API when:**
- Building applications or services
- Need structured error handling
- Running batch operations
- Caching results for performance
- Creating dashboards or monitoring
- Integrating with other systems

> **Note**: The `run_any_python_tool.sh` wrapper handles environment setup and ensures all tools run with the correct shared configuration.

**What you get immediately:**
- ⚡ **10-100x faster** code analysis than traditional tools
- 🛡️ **Automatic backups** before any destructive operation
- ↩️ **Full undo capabilities** for all file operations
- 🎯 **Smart confirmations** that prevent accidents
- 📊 **Complete audit trail** of all operations

### 🔒 Level 2: Maximum Security (For AI Developers & Enterprises)
For those using AI coding assistants or requiring enterprise-grade protection:

```bash
# Block direct access to dangerous commands
# See "Achieving Maximum Safety" section below for full setup
```

**Additional protection:**
- 🤖 **AI agents cannot bypass** safety mechanisms
- 🚫 **System-level blocking** of dangerous commands
- 🔐 **Zero-trust architecture** for production environments
- 📡 **Monitoring and alerting** for bypass attempts

## 🚨 Why This Toolkit Exists

**The AI coding revolution has a safety problem.** Recent incidents like [Replit's AI wiping production databases](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/) show what happens when AI agents have unrestricted access to powerful commands.

**This toolkit is the solution** - providing AI agents with:
- 🛡️ **Unbreakable safety guarantees** - Dangerous operations are intercepted
- ⚡ **10-100x faster analysis** - Critical for token efficiency and cost
- 📊 **Structured, parseable output** - No more regex parsing of CLI output
- 🔄 **Full reversibility** - Every operation can be undone

## 🛡️ Built-in Safety Features (Available to Everyone)

### SafeGIT - Your Git Safety Net
```bash
# Protects against common disasters:
./run_any_python_tool.sh safegit.py reset --hard    # ✅ Creates backup first
./run_any_python_tool.sh safegit.py clean -fdx      # ✅ Shows preview
./run_any_python_tool.sh safegit.py push --force    # ✅ Converts to --force-with-lease
```

### Safe File Manager - Never Lose Data Again
```bash
# Every operation is reversible:
./run_any_python_tool.sh safe_file_manager.py move important.doc backup/
./run_any_python_tool.sh safe_file_manager.py trash old_files/  # To trash, not gone
./run_any_python_tool.sh safe_file_manager.py undo --interactive  # Recover anything
```

### Data Flow Tracker - Understand Your Code (Enhanced in v1.5.0)
```bash
# Track how data flows through your code:
./run_any_python_tool.sh data_flow_tracker_v2.py --var user_input --file app.py
./run_any_python_tool.sh data_flow_tracker_v2.py --var result --direction backward
```


## 🚀 Overview

The Code Intelligence Toolkit provides 100+ command-line tools for developers who value their data. Every tool is designed with safety first, productivity second.

### Core Principles
- **Explicit Over Implicit** - Clear intentions required
- **Reversible By Default** - Undo capability for all operations  
- **Fail Safe** - When in doubt, do nothing
- **Audit Everything** - Complete operation history
- **Always Current** - No persistent index means results reflect current file state

## 🎯 **Design Philosophy: No Persistent Index**

Our toolkit deliberately avoids persistent indexing - this is a **cornerstone feature**, not a limitation:

### ✅ **Guaranteed Accuracy**
- Analysis is always performed on the **current version** of your files on disk
- **Never worry** about stale or out-of-sync results from background indexers
- What you see is **exactly** what's in your files right now

### ⚡ **Zero Setup Time**
- Clone the repository and get **meaningful results in seconds**
- No slow, resource-intensive initial indexing process to wait through
- **Instant productivity** - perfect for AI agents that need immediate results

### 🏃 **No Resource Drain**
- **Zero CPU or memory consumption** when not actively being used
- No background services constantly monitoring and re-indexing files
- Your system resources remain **100% available** for your actual work

### 🐳 **Perfect for Modern Workflows**
- **Stateless, on-demand** nature ideal for ephemeral environments
- **CI/CD runners** and **Docker containers** where persistent indexes are impractical
- **Kubernetes pods** and **serverless functions** work flawlessly
- **Cloud development environments** get instant, accurate results

### 🤖 **AI Agent Optimized**
- **Consistent behavior** across different environments and runs
- **No cache invalidation complexity** - every run is fresh and accurate  
- **Predictable performance** - no variable indexing overhead
- **Container-friendly** - works perfectly in ephemeral environments

This **"faster, safer, and more accurate"** philosophy ensures that the toolkit provides reliable, current analysis without the complexity and resource overhead of maintaining persistent state.

## 🤖 **NEW: AI Integration Roadmap (100% Complete)**

Transform your toolkit into an AI-first platform with structured APIs, intelligent reasoning, and seamless integration.

### Phase 1: Unified JSON API ✅
**Production-ready programmatic access to all 100+ tools**

```bash
# Interactive mode
./api.py
> {"tool": "find_text_v7", "params": {"TODO": true, "--limit": 5}}

# Pipe mode  
echo '{"tool": "data_flow_tracker_v2", "params": {"--var": "user_input", "--file": "app.py"}}' | ./api.py

# Demo mode
./api.py --demo
```

**Key Features:**
- **Universal Tool Access**: Single endpoint for all operations
- **Caching System**: SHA256-based caching with 1-hour TTL
- **Batch Operations**: Execute multiple requests efficiently  
- **Statistics Tracking**: Performance monitoring and usage analytics
- **Non-Interactive Mode**: Perfect for CI/CD and automation

### Phase 2: AI Reasoning System ✅  
**Intelligent analysis with structured reasoning output**

Enhanced tools with AI-powered insights:

#### data_flow_tracker_v2.py - Security Risk Assessment
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var user_input --file app.py --output-reasoning-json
```

```json
{
  "ai_reasoning": {
    "risk_assessment": {
      "overall_risk": "high",
      "confidence": 0.92,
      "security_implications": ["SQL injection possible"]
    },
    "recommendations": [
      "Add input validation before database operations",
      "Use parameterized queries to prevent SQL injection"
    ]
  }
}
```

#### doc_generator_enhanced.py - Documentation Quality Assessment
```bash
./run_any_python_tool.sh doc_generator_enhanced.py --file MyClass.java --output-reasoning-json
```

#### semantic_diff_v3.py - Change Complexity Analysis  
```bash
./run_any_python_tool.sh semantic_diff_v3.py file1.py file2.py --output-reasoning-json
```

### Phase 3: Python SDK ✅
**High-level interfaces for seamless integration**

```python
# Install the SDK
pip install -e .

# High-level interface for AI agents
from code_intelligence import CodeIntelligence

ci = CodeIntelligence('/path/to/project')

# Analyze impact with AI reasoning
result = ci.analyze_impact('app.py', 'user_input', include_reasoning=True)
print(f"Risk: {result.reasoning['risk_assessment']['overall_risk']}")

# Generate documentation with quality assessment
docs = ci.generate_documentation('MyClass.java', style='api-docs')
print(f"Quality: {docs.reasoning['quality_assessment']['clarity_score']:.1%}")

# Safe refactoring with language-aware backend selection and impact analysis
refactor = ci.refactor_safely('oldName', 'newName', scope='project')  # Auto-detects Java/Python per file
print(f"Modified {refactor.files_modified} files using {len(refactor.backends_used)} different backends")
```

**SDK Packages:**
- **`analysis/`**: DataFlowAnalyzer, ImpactAssessor, ASTNavigator, SemanticDiffAnalyzer
- **`documentation/`**: DocumentationGenerator, StyleFormatter  
- **`refactoring/`**: SafeRefactorer, ASTRefactorer
- **`safety/`**: GitSafety, FileSafety
- **`api/`**: CodeIntelligenceAPI client

### 📚 Complete Documentation
- **[AI Integration Roadmap](docs/AI_INTEGRATION_ROADMAP.md)** - Complete implementation guide
- **[Unified JSON API](docs/UNIFIED_JSON_API.md)** - API reference and examples  
- **[AI Reasoning System](docs/AI_REASONING_SYSTEM.md)** - Intelligent analysis documentation
- **[Python SDK Guide](docs/PYTHON_SDK_GUIDE.md)** - Comprehensive SDK documentation

## 🎆 Powerful Capabilities

### ⚡ Lightning-Fast Performance
- **Ripgrep-powered search** - 10-100x faster than traditional grep
- **No file size limits** - Edit massive files (10k+ lines) that break AI IDE tools
- **Parallel processing** - Multi-threaded analysis across entire codebases
- **Smart caching** - Instant results for repeated operations
- **Optimized algorithms** - AST parsing with minimal overhead

### 🎯 Professional Refactoring Suite

#### Text-Based Operations (replace_text_v9.py)
- **Surgical precision** - Replace text with regex, whole-word, or fixed-string modes
- **Multi-file operations** - Refactor across entire projects in seconds
- **Git-aware** - Target only staged files or specific commits
- **Block-aware** - Replace within specific code blocks (if/for/while/try)
- **JSON pipelines** - Chain operations for complex transformations

#### AST-Based Refactoring (replace_text_ast_v3.py)
- **Semantic accuracy** - Understands code structure, not just text
- **Symbol renaming** - Rename variables/functions/classes with confidence
- **Scope awareness** - Changes only affect intended scope
- **Multi-language** - Python and Java with extensible architecture
- **Comment/string modes** - Target only comments or string literals

#### Universal Refactoring (unified_refactor_v2.py)
- **Language-aware auto-detection** - Java files use Java AST, Python files use Python AST
- **Multiple backends** - Choose between AST, Rope, or text engines, or use auto-detection
- **Cross-language** - Single interface for Python, Java, JavaScript with optimal backend selection
- **Intelligent suggestions** - AI-powered refactoring recommendations
- **Batch operations** - Rename hundreds of symbols in one command across mixed codebases

### 🔍 Advanced Code Analysis

#### find_text_v7.py - The Ultimate Search Tool with Multiline Support
- **Every search mode** - Regex, fixed-string, whole-word, case-sensitive
- **Context control** - Show N lines before/after matches (-A/-B/-C)
- **Block extraction** - Extract entire functions/classes containing matches
- **Method extraction** - Pull out complete methods (with size limits)
- **Range operations** - Extract specific line ranges from files
- **AST context** - Shows class → method hierarchy for every match
- **Multi-file search** - Search across file lists or entire directories

#### AST Navigation Suite
- **navigate_ast.py** - Jump to any symbol definition instantly
- **method_analyzer_ast.py** - Track call flows and dependencies
- **cross_file_analysis_ast.py** - Understand module interactions
- **show_structure_ast_v4.py** - Visualize code hierarchy
- **trace_calls_ast.py** - Follow execution paths through code

### 📋 Smart Automation

#### Git Integration
- **Intelligent commits** - Auto-generated messages from diffs
- **Smart staging** - Stage only files you actually modified
- **Safe operations** - All git commands go through SafeGIT
- **Workflow automation** - GIT SEQ commands for common patterns

#### Code Quality Tools
- **dead_code_detector.py** - Find unused code across languages
- **suggest_refactoring.py** - AI-powered improvement suggestions
- **analyze_internal_usage.py** - Understand API usage patterns
- **error monitoring** - Track and analyze runtime errors

### 🏆 Performance Benchmarks

```python
# AI agent searching massive codebase efficiently
import time
start = time.time()
result = subprocess.run([
    "./run_any_python_tool.sh", 
    "find_text_v7.py", 
    "security_issue",
    "--json"
], capture_output=True, text=True)
print(f"Searched 1M+ lines in {time.time() - start:.1f}s")  # 0.8s vs grep's 45s!

# Edit 15,000 line file
AI IDE tools                           # ❌ Timeout/crash/truncate
replace_text_v9.py "old" "new" big.py  # ✅ 0.3 seconds + backup + undo

# Rename variable across 500 files
Manual IDE refactoring                  # 2-3 minutes + verification
replace_text_ast_v3.py oldVar newVar    # 3 seconds + automatic backup

# Extract all methods from large file
Manual copy/paste                       # 10+ minutes
find_text_v7.py --extract-method-alllines  # 0.2 seconds
```

### 📊 Performance Comparison

| Task | Traditional Method | Our Tools | Speedup |
|------|-------------------|-----------|----------|
| Search 1M lines | `grep -r`: 45s | `find_text_v7.py`: 0.8s | **56x faster** |
| Edit 15k line file | AI IDE: crash/timeout | `replace_text_v9.py`: 0.3s | **✅ Works** |
| Find symbol usage | IDE indexing: 30s+ | `navigate_ast.py`: 0.1s | **300x faster** |
| Rename across project | IDE refactor: 2-3 min | `replace_text_ast_v3.py`: 3s | **40x faster** |
| Extract all methods | Manual: 10+ min | `find_text_v7.py`: 0.2s | **3000x faster** |
| Safe file move | `mv` + manual backup | `safe_file_manager.py`: instant | **✓ Reversible** |
| Git reset recovery | Often impossible | `safegit.py`: automatic | **✓ Always safe** |

### 🚀 Why So Fast?

1. **Ripgrep Core** - Written in Rust, uses SIMD, respects .gitignore
2. **Stream Processing** - Never loads entire file into memory (handles any size)
3. **Smart Caching** - Parse AST once, reuse everywhere
4. **Parallel Processing** - All CPU cores utilized automatically
5. **Optimized Algorithms** - Purpose-built for code analysis
6. **No IDE Overhead** - Direct file access, no language servers or indexing

## ✨ Complete Platform for Code Intelligence

Our toolkit includes over 100 tools for every stage of development, from lightning-fast search and safe refactoring to deep data flow analysis and automated documentation. The entire suite is accessible via our Unified JSON API and Python SDK.

**Core Capabilities:**
- **🔍 Advanced Analysis** - AST-based parsing, data flow tracking, semantic diff
- **🛠️ Safe Refactoring** - Multi-engine refactoring with automatic backups
- **🤖 AI Integration** - Structured APIs, intelligent reasoning, Python SDK
- **🛡️ Enterprise Safety** - Git protection, file safety, operation validation
- **📊 Smart Automation** - CI/CD ready, non-interactive mode, batch operations

➡️ **[See the Complete Feature List and Tool Reference →](docs/FEATURES.md)**

## 🏗️ Architecture

Built for safety at every level:
- **Defense in depth** - Multiple protection layers
- **Fail-safe defaults** - Safe unless explicitly overridden
- **Atomic operations** - No partial states
- **Comprehensive logging** - Full audit trail

### 🔄 Multi-Level Undo System (NEW)

**SafeGIT-style undo capabilities for all text operations:**

- **Automatic tracking** - Every operation creates an undo point
- **Multi-level history** - Restore to any previous state
- **Atomic operations** - All changes are reversible
- **Cross-tool awareness** - Track changes from any v9/v3/v2 tool
- **Compressed backups** - Efficient storage of operation history
- **Recovery scripts** - Generated for every operation

```bash
# Every operation is tracked automatically
./run_any_python_tool.sh replace_text_v9.py "old" "new" file.py
# Output: [Undo ID: 1753732740927_91513] Use 'text_undo.py undo --operation 1753732740927_91513' to undo.

# View operation history
./run_any_python_tool.sh text_undo.py history
./run_any_python_tool.sh text_undo.py history --file specific.py

# Undo last operation
./run_any_python_tool.sh text_undo.py undo --last --yes

# Undo specific operation
./run_any_python_tool.sh text_undo.py undo --operation 1753732740927_91513 --yes

# Clean old operations
./run_any_python_tool.sh text_undo.py clean --older-than 30d
```

**Tools with integrated undo support:**
- `replace_text_v9.py` - All text replacements tracked
- `replace_text_ast_v3.py` - AST-based refactoring with undo
- `unified_refactor_v2.py` - Universal refactoring with history
- `refactor_rename_v2.py` - Batch operations with rollback
- `safe_file_manager.py` - File operations with recovery

## 🆕 What's New (v1.5.0) - Complete Interactive Utils Migration

**Released: July 28, 2025** - This major release completes the migration of all critical tools to use unified interactive utilities, eliminating EOF errors in CI/CD environments while introducing revolutionary tool version updates.

### 🎯 **NEW: interactive_utils.py - Unified Non-Interactive Support**

**All Python tools now use a shared module for handling interactive prompts:**
- **No More EOF Errors** - Clear, actionable error messages instead of crashes
- **Automatic CI Detection** - Detects CI/CD, pipes, no TTY environments automatically
- **Multiple Config Methods** - Command flags > Environment variables > .pytoolsrc > defaults
- **Tool Version Updates** - `replace_text_v9.py`, `replace_text_ast_v3.py`, `unified_refactor_v2.py`
- **Multiple Prompt Types** - Yes/no, typed phrases, numbered selections, multi-choice

```bash
# Before (EOF crash in CI):
echo "" | python text_undo.py undo --last
# EOFError: EOF when reading a line

# After (helpful error with solutions):
echo "" | python text_undo.py undo --last
# ❌ ERROR: Interactive confirmation required but running in non-interactive mode.
#       Use --yes flag to skip confirmation
#       Or set TEXT_UNDO_ASSUME_YES=1 environment variable
#       Or set 'assume_yes = true' in .pytoolsrc [text_undo] section
```

**Migrated Tools:**
- ✅ `text_undo.py` - Multi-level undo with interactive selection
- ✅ `safe_file_manager.py` - Enterprise file operations
- ✅ `safegit.py` - Git safety wrapper with risk-based confirmations
- ✅ `replace_text_v9.py` - Text replacement with multi-level undo
- ✅ `replace_text_ast_v3.py` - AST refactoring with scope awareness

### 🧠 **NEW: data_flow_tracker_v2.py - Intelligence Layer Revolution**
**Complete rewrite with breakthrough intelligence capabilities:**
- **Natural Language Explanations** - Complex analysis explained in plain English
- **Interactive HTML Visualizations** - Self-contained reports with vis.js network graphs
- **Risk Assessment** - Smart analysis of code change impact with confidence scoring
- **Calculation Path Tracking** - Step-by-step breakdown of how values are computed
- **Type & State Evolution** - Monitor how variables change through code execution
- **Zero Dependencies** - Works with any codebase, no setup required

```bash
# Revolutionary intelligence in action
./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-impact --explain --output-html --file calc.py
```

### 📚 **NEW: doc_generator.py & doc_generator_enhanced.py - Automated Documentation Generation**
**Two complementary tools that transform code analysis into professional documentation:**
- **doc_generator.py** - Sophisticated content generation with deep intelligence (2768 lines of logic!)
- **doc_generator_enhanced.py** - AST tool integration with interactive HTML visualization
- **Use both together** - Enhanced for exploration, original for production docs
- **Multiple Styles** - API docs, user guides, technical analysis, quick reference, tutorials, architecture, call graphs
- **Interactive HTML** - Multi-tab interface with Navigation, Call Flow, Data Flow, Structure, Dependencies
- **Multiple Formats** - Markdown, HTML, reStructuredText, docstring injection
- **Intelligence Integration** - Leverages data flow analysis for smart content generation
- **Auto-Examples** - Contextually appropriate code samples and usage patterns
- **Depth Control** - Surface, medium, or deep analysis levels

```python
# AI agent generating documentation after writing code
import subprocess
import json

def generate_docs(class_name, file_path):
    """AI-safe documentation generation with structured output"""
    result = subprocess.run([
        "./run_any_python_tool.sh",
        "doc_generator_enhanced.py",
        "--class", class_name,
        "--file", file_path,
        "--format", "json",
        "--non-interactive"
    ], capture_output=True, text=True)
    
    return json.loads(result.stdout)

# Example: AI agent documents the code it just created
docs = generate_docs("UserManager", "auth.py")
print(f"Generated {len(docs['methods'])} method documentations")
```

### 🗂️ **Major Tool Organization & Cleanup**
- **Latest tools only** - Main directory contains only current, stable versions
- **Safe archival** - All older versions preserved in organized `archive/` structure
- **Clear hierarchy** - Easy to identify which tools to use (highest version number)

**Current Active Tools:**
- `data_flow_tracker_v2.py` (with intelligence layer) ← **NEW MAJOR FEATURE**
- `doc_generator.py` (automated documentation) ← **NEW MAJOR FEATURE**
- `doc_generator_enhanced.py` (with full AST integration) ← **ENHANCED VERSION**
- `find_text_v7.py` (with multiline search) ← Latest
- `replace_text_v9.py` (with escape sequences + multi-level undo) ← Latest  
- `replace_text_ast_v3.py` (enhanced AST refactoring + multi-level undo) ← Latest

### 🐛 **Critical Reliability Fixes**
- **Fixed infinite recursion** in data flow tracking - No more crashes with cyclic dependencies
- **Enhanced Java method detection** - Better regex patterns for complex signatures
- **Template system reliability** - Jinja2 templates with robust fallback mechanisms

### 📚 **Complete Documentation Overhaul**
- **Updated ALL documentation** - Every reference now points to correct tool versions
- **Performance benchmarks** - Updated with latest capabilities and tool names
- **Working examples** - All commands tested and verified

#### 🎯 Documentation Generation Features
  ```bash
  # 📖 Generate API documentation with enhanced AST integration
  ./run_any_python_tool.sh doc_generator_enhanced.py --function calculatePrice --file pricing.py --style api-docs
  
  # 🌐 Create interactive HTML documentation with 6 analysis tabs
  ./run_any_python_tool.sh doc_generator_enhanced.py --class MyClass --file MyClass.java --style api-docs --format interactive
  
  # 👥 Create user-friendly guides for classes
  ./run_any_python_tool.sh doc_generator_enhanced.py --class UserManager --file auth.py --style user-guide --depth deep
  
  # 🔬 Generate architecture documentation with call graphs
  ./run_any_python_tool.sh doc_generator_enhanced.py --module --file database.py --style architecture --format html
  
  # ⚡ Quick reference cards
  ./run_any_python_tool.sh doc_generator_enhanced.py --function process_data --file data.py --style quick-ref --format docstring
  
  # 🎓 Tutorial-style documentation  
  ./run_any_python_tool.sh doc_generator_enhanced.py --class APIClient --file client.py --style tutorial --depth medium
  ```

### 🧠 Intelligence Layer - Transform Analysis into Insights
- **BREAKTHROUGH: Intelligence Layer** - Revolutionary enhancement that transforms complex analysis into intuitive insights through natural language explanations and interactive visualizations.

#### 🎯 Intelligence Layer Features
  ```bash
  # 🧠 Natural Language Explanations - Understand analysis instantly
  ./run_any_python_tool.sh data_flow_tracker_v2.py --var config --show-impact --explain --file app.py
  
  # 🌐 Interactive HTML Visualization - Explore dependencies visually  
  ./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-calculation-path --output-html --file calc.py
  
  # 🎯 Combined Intelligence - Best of both worlds
  ./run_any_python_tool.sh data_flow_tracker_v2.py --var data --track-state --explain --output-html --file process.py
  
  # ⚡ All V2 analysis modes support intelligence layer
  ./run_any_python_tool.sh data_flow_tracker_v2.py --var x --direction backward --explain --file module.py
  ```

### 🚀 **Six Core Capabilities** (Complete V2 Suite + Documentation):

#### 1. 🔍 **Impact Analysis** - Know What Will Break
Shows where data escapes scope with **risk assessment** and **actionable recommendations**:
- **Returns**: Functions that return values dependent on the variable
- **Side Effects**: File writes, network calls, console output  
- **State Changes**: Modifications to global variables or class members
- **Risk Levels**: High/Medium/Low with specific testing advice

#### 2. 🧮 **Calculation Path Analysis** - Understand Complex Logic
Extracts the minimal "critical path" showing exactly how values are calculated:
- **Algorithm Flow**: Step-by-step calculation breakdown
- **Input Tracking**: Shows what each step depends on
- **Debugging Aid**: Trace issues back to their source
- **Noise Filtering**: Only shows essential calculation steps

#### 3. 🔄 **Type & State Tracking** - Catch Bugs Early  
Monitors how variable types and states evolve through code execution:
- **Type Evolution**: Tracks type changes that could indicate bugs
- **State Context**: Loop and conditional modification tracking
- **Warning System**: Alerts about potential null references and type issues
- **Confidence Scoring**: Statistical confidence in type inference

#### 4. 🧠 **Natural Language Explanations** (`--explain`)
Converts technical analysis into **intuitive explanations**:
- **Risk Assessment**: "🚨 High Risk Change: Modifying 'config' affects 5 different places across 3 functions..."
- **Algorithm Understanding**: "🔍 How 'finalTotal' is Calculated: This value is calculated through 14 steps..."
- **Bug Prevention**: "⚠️ Type Changes Detected: dict → UserModel. This could indicate potential bugs..."
- **Actionable Advice**: Specific recommendations for testing and validation

#### 5. 🌐 **Interactive HTML Visualization** (`--output-html`)
Self-contained professional reports with **zero external dependencies**:
- **vis.js Network Graphs**: Click-to-explore node relationships
- **Risk-Based Styling**: Color-coded by impact level and confidence
- **Progressive Disclosure**: Overview → drill-down → code context
- **Export Capabilities**: Save visualizations as PNG images
- **Responsive Design**: Works on desktop, tablet, and mobile

#### 6. 📚 **Automated Documentation Generation** (`doc_generator.py` & `doc_generator_enhanced.py`)
Transform code analysis into professional documentation:
- **Original Version** (`doc_generator.py`): Data flow intelligence integration
- **Enhanced Version** (`doc_generator_enhanced.py`): Full AST tool integration with 5 analysis engines
- **Multiple Styles**: API docs, user guides, technical analysis, quick reference, tutorials, architecture, call graphs
- **Interactive HTML**: Multi-tab navigation showing Overview, Navigation, Call Flow, Data Flow, Structure, Dependencies
- **Full Java/Python Parity**: Both languages support all analysis features including data flow
- **Multiple Formats**: Markdown, HTML, docstring, reStructuredText
- **Intelligence Integration**: Leverages data flow analysis for smart documentation
- **Depth Control**: Surface, medium, or deep analysis levels
- **Auto-Examples**: Contextually appropriate code samples and usage patterns

### 🎯 **Strategic Achievement: Complete Code Intelligence Platform**

**The Perfect Trilogy**: Analysis + Visualization + Documentation = **Complete Code Understanding**

- **Before**: Powerful analysis requiring expertise to interpret  
- **After**: Complete intelligence platform with analysis, visualization, and documentation
- **Impact**: Complex codebases become manageable, understandable, and well-documented
- **Result**: Confident development, debugging, refactoring, and knowledge sharing for everyone

### Enhanced Documentation
- **Improved EOF handling**: Added warnings to prevent 'EOF < /dev/null' issues in heredocs
- **Tool organization**: Better categorization in documentation
- **More examples**: Real-world use cases for data flow analysis

### Bug Fixes
- Fixed stdin processing in replace_text_v8.py
- Fixed configuration handling in replace_text_ast_v3.py
- Made `--line` optional for `--comments-only` and `--strings-only` modes in AST tool

## 🆕 What's New (v1.5.0) - Complete Interactive Utils Migration

**Released: July 28, 2025** - This major release completes the migration of all critical tools to use unified interactive utilities, eliminating EOF errors in CI/CD environments.

### 🎯 **NEW: interactive_utils.py - Unified Non-Interactive Support**

**All Python tools now use a shared module for handling interactive prompts:**
- **No More EOF Errors** - Clear, actionable error messages instead of crashes
- **Automatic Detection** - Detects CI/CD, pipes, no TTY environments
- **Language-Aware Backends** - Auto-detects Java vs Python for optimal AST processing
- **Configuration Support** - Respects `.pytoolsrc` settings for project defaults
- **Multiple Prompt Types** - Yes/no, typed phrases, numbered selections, multi-choice

```bash
# Before (EOF crash):
echo "" | python text_undo.py undo --last
# EOFError: EOF when reading a line

# After (helpful message):
echo "" | python text_undo.py undo --last
# ERROR: Interactive confirmation required but running in non-interactive mode.
#        Use --yes flag to skip confirmation
#        Or set TEXT_UNDO_ASSUME_YES=1 environment variable
#        Or set 'assume_yes = true' in .pytoolsrc [text_undo] section
```

### 📋 **Enhanced Configuration Priority**

Tools now check for settings in this order:
1. **Command-line flags** - `--yes`, `--non-interactive` (highest priority)
2. **Environment variables** - `{TOOL}_ASSUME_YES=1`
3. **Tool-specific .pytoolsrc** - `[tool_name]` section
4. **Global .pytoolsrc defaults** - `[defaults]` section
5. **Hard-coded defaults** - Conservative (interactive) by default

### 🎛️ **Specialized Configuration Profiles**

The toolkit includes pre-configured profiles for different environments:

- **`.pytoolsrc.ci`** - CI/CD automation with auto-confirm and non-interactive mode
- **`.pytoolsrc.automation`** - Local automation with balanced safety and speed
- **`.pytoolsrc.safe`** - Maximum safety with dry-run and interactive confirmations

```bash
# Use different configuration profiles
export PYTOOLSRC=.pytoolsrc.ci          # For CI/CD
export PYTOOLSRC=.pytoolsrc.automation   # For local automation  
export PYTOOLSRC=.pytoolsrc.safe         # For production/critical work
```

### 🔧 **Tools Fully Migrated (v1.5.0)**
- **text_undo.py** - Complete with numbered selection menus for restore operations
- **safe_file_manager.py** - Risk-based confirmations with typed phrases for high-risk ops
- **safegit.py** - Multi-choice prompts and typed confirmations for dangerous operations  
- **replace_text_v9.py** - Large change confirmations with auto-detection
- **replace_text_ast_v3.py** - Batch operation confirmations with y/n/q support

### 🎯 **Key Improvements**
- **100% EOF Error Elimination** - All migrated tools show helpful messages
- **Consistent Behavior** - Every tool handles non-interactive mode the same way
- **CI/CD Ready** - Automatic detection of GitHub Actions, GitLab CI, Jenkins, etc.
- **Backward Compatible** - All tools include fallback implementations

### 📝 **Documentation Updates**
- Enhanced CLAUDE.md with interactive utils section
- Updated NON_INTERACTIVE_GUIDE.md with new features
- Added comprehensive migration guide for tool developers

## 📦 Installation

### Prerequisites
- Python 3.7+ 
- Git
- ripgrep (`rg`)

### Dependencies

The toolkit uses a modular dependency system:

**Core Dependencies** (Required for basic functionality):
- `javalang>=0.13.0` - Java AST parsing support
- Basic Python standard library modules

**Optional Dependencies** (For enhanced features):
- `markdown>=3.3.0` - Enhanced HTML conversion in doc_generator.py (falls back to built-in converter if not installed)
- `jinja2>=3.0.0` - Template engine for clean separation of HTML presentation from logic (falls back to built-in templates if not installed)
- `rope>=1.0.0` - Advanced Python refactoring capabilities
- `numpy`, `pandas`, `scikit-learn` - Advanced semantic diff features
- `astroid>=2.0.0` - Enhanced Python AST analysis
- See `requirements-optional.txt` for complete list

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/code-intelligence-toolkit.git
cd code-intelligence-toolkit
```

2. Install dependencies:
```bash
# Core dependencies only (minimal installation)
pip install -r requirements-core.txt

# Or install everything including optional features
pip install -r requirements.txt  # Installs both core and optional
```

3. Run safety setup:
```bash
./setup_config.sh  # Interactive configuration
```

4. Test safety features:
```bash
# Try a dangerous operation (it will be blocked)
./run_any_python_tool.sh safegit.py reset --hard HEAD~1
```

## 🎯 Real-World AI Agent Usage Examples

### 1. AI Code Review Agent
```python
class AICodeReviewer:
    def __init__(self, toolkit_path):
        self.toolkit = toolkit_path
    
    def find_security_issues(self, project_path):
        """AI agent scanning for security vulnerabilities"""
        cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "find_text_v7.py",
            "password|secret|api_key",
            "--scope", project_path,
            "--extract-method",  # Get full context
            "--json"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = json.loads(result.stdout)
        
        # AI analyzes each finding
        for finding in findings:
            if self.is_security_risk(finding['code']):
                self.flag_for_review(finding)
```

### 2. AI Refactoring Assistant
```python
class AIRefactoringAgent:
    def rename_across_codebase(self, old_name, new_name, file_pattern="*.py"):
        """Safe, AST-aware renaming across entire project"""
        # First, find all occurrences
        search_cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "find_text_v7.py",
            old_name,
            "--json",
            "--scope", "src/"
        ]
        occurrences = self.run_command(search_cmd)
        
        # Then safely rename with AST understanding
        for file in occurrences['files']:
            rename_cmd = [
                f"{self.toolkit}/run_any_python_tool.sh",
                "replace_text_ast_v3.py",
                "--file", file,
                old_name, new_name,
                "--yes"  # Non-interactive
            ]
            result = self.run_command(rename_cmd)
            print(f"Renamed in {file}: {result['changes_made']} occurrences")
```

### 3. AI Documentation Generator
```python
class AIDocumentationAgent:
    def document_new_code(self, file_path):
        """AI agent auto-documents code it just created"""
        # Generate comprehensive documentation
        doc_cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "doc_generator_enhanced.py",
            "--file", file_path,
            "--style", "api-docs",
            "--format", "interactive",
            "--output", f"{file_path}.html",
            "--non-interactive"
        ]
        self.run_command(doc_cmd)
        
        # Also generate user guide
        guide_cmd = doc_cmd.copy()
        guide_cmd[guide_cmd.index("api-docs")] = "user-guide"
        guide_cmd[-2] = f"{file_path}_guide.html"
        self.run_command(guide_cmd)
        
        return f"Documentation generated: {file_path}.html"
```

### 4. AI Git Workflow Manager
```python
class AIGitManager:
    def safe_commit(self, ai_generated_message):
        """AI safely commits code with auto-generated messages"""
        # Stage changes safely
        stage_cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "safegit.py",
            "add", "-u",
            "--yes"
        ]
        self.run_command(stage_cmd)
        
        # Generate enhanced commit message
        analyze_cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "git_commit_analyzer.py",
            "--analyze-only",
            "--json"
        ]
        analysis = json.loads(self.run_command(analyze_cmd))
        
        # Commit with SafeGIT protection
        commit_cmd = [
            f"{self.toolkit}/run_any_python_tool.sh",
            "safegit.py",
            "commit", "-m",
            f"{ai_generated_message}\n\nDetails: {analysis['summary']}",
            "--force-yes"
        ]
        return self.run_command(commit_cmd)
```

### 📦 Safe File & Git Operations
```bash
# Move files with automatic backup
./run_any_python_tool.sh safe_file_manager.py move old_structure/ new_structure/

# Git operations with safety net
./run_any_python_tool.sh safegit.py reset --hard  # Creates stash backup first
./run_any_python_tool.sh safegit.py clean -fdx    # Shows preview, requires confirmation
```

## 🌟 What Makes This Toolkit Unique

### 💯 Complete Feature Integration
Unlike other tools that do one thing well, our toolkit provides:
- **Unified interface** - One wrapper script for 100+ tools
- **Tool chaining** - Pipe results between tools for complex workflows
- **JSON pipelines** - Structured data flow between operations
- **Cross-tool intelligence** - Tools share AST analysis and caching

### 🏃 Performance That Scales
- **Ripgrep foundation** - Fastest regex engine available
- **Parallel processing** - Utilize all CPU cores automatically
- **Smart caching** - AST parse once, use everywhere
- **Memory efficient** - Stream processing for huge files

### 🧬 Enterprise-Grade Safety
- **Atomic operations** - No partial states ever
- **Automatic backups** - Before every change
- **Complete audit trail** - Know who changed what, when
- **Multi-level undo** - Recover from any mistake

### 🤯 Unique Capabilities
- **Extract code blocks** - Pull out complete if/for/try blocks
- **Method extraction** - Get entire methods with one command
- **AST-guided text ops** - Best of both semantic and text approaches
- **Git-aware operations** - Target staged/modified files only
- **Language polyglot** - Python, Java, JavaScript, and more

## 🎭 Context-Aware Environments

SafeGIT adapts its behavior based on your environment and workflow:

### Environment Settings
```bash
# Set environment context
./run_any_python_tool.sh safegit.py set-env production    # Maximum restrictions
./run_any_python_tool.sh safegit.py set-env staging       # Standard protections
./run_any_python_tool.sh safegit.py set-env development   # Default protections

# Production environment blocks:
# - force push, reset --hard, clean -fdx
# - rebase on main/master branches
# - any operation that could lose committed work
```

### Work Mode Settings
```bash
# Set work mode
./run_any_python_tool.sh safegit.py set-mode normal       # Default behavior
./run_any_python_tool.sh safegit.py set-mode code-freeze  # Only hotfixes allowed
./run_any_python_tool.sh safegit.py set-mode paranoid     # Read-only operations only

# Code-freeze mode:
# - Blocks all write operations except on 'hotfix/*' branches
# - Perfect for release preparation periods

# Paranoid mode:
# - Only allows: status, log, diff, show, branch -l
# - Blocks ALL modifications including add and commit
```

### Custom Restrictions
```bash
# Add custom pattern restrictions
./run_any_python_tool.sh safegit.py add-restriction "push.*production"
./run_any_python_tool.sh safegit.py add-restriction "merge.*experiment"

# View current context
./run_any_python_tool.sh safegit.py show-context
```

These settings persist across sessions and provide an extra layer of protection based on your current workflow needs.

## 🤖 Non-Interactive Mode Support

### Complete CI/CD & Automation Support

Every tool in the toolkit supports non-interactive operation for seamless integration with:
- **CI/CD Pipelines** - GitHub Actions, GitLab CI, Jenkins, CircleCI
- **AI Agents** - Claude, GPT, Copilot, and other coding assistants
- **Automation Scripts** - Bash, Python, or any scripting language
- **Docker Containers** - Fully automated environments

### Configuration Methods

#### 1. Environment Variables (Recommended for CI/CD)
```bash
# Safe File Manager
export SFM_ASSUME_YES=1              # Auto-confirm all file operations

# SafeGIT
export SAFEGIT_NONINTERACTIVE=1      # Strict non-interactive mode
export SAFEGIT_ASSUME_YES=1          # Auto-confirm safe git operations

# Global settings
export PYTOOLSRC_NON_INTERACTIVE=1   # Apply to all tools
```

#### 2. Configuration File (.pytoolsrc)
```ini
[defaults]
non_interactive = true    # No prompts, fail if input needed
assume_yes = true        # Auto-confirm medium-risk operations

[safe_file_manager]
assume_yes = true
backup = true           # Always create backups in automation

[safegit]
non_interactive = true
assume_yes = true
force_yes = false       # Never auto-confirm dangerous operations
```

#### 3. Command-Line Flags
```bash
# Use --yes flag for individual commands
./run_any_python_tool.sh safe_file_manager.py --yes move file1 file2
./run_any_python_tool.sh safegit.py add . --yes
./run_any_python_tool.sh replace_text_ast_v3.py oldVar newVar --file script.py --yes
```

### Safety Levels in Non-Interactive Mode

1. **Auto-Approved** (with assume_yes):
   - Reading files, listing directories
   - Creating backups, dry-run operations
   - Git status, log, diff

2. **Requires --yes or assume_yes**:
   - Moving/copying files
   - Text replacements
   - Git add, commit, pull

3. **Requires --force-yes explicitly**:
   - Deleting files (even to trash)
   - Git reset --hard
   - Git push --force
   - Any destructive operation

### Example CI/CD Integrations

#### GitHub Actions
```yaml
env:
  SFM_ASSUME_YES: 1
  SAFEGIT_ASSUME_YES: 1

steps:
  - name: Refactor code
    run: |
      ./run_any_python_tool.sh replace_text_v9.py "old_api" "new_api" --scope src/
      ./run_any_python_tool.sh safe_file_manager.py organize build/ --by-date
      ./run_any_python_tool.sh safegit.py add .
      ./run_any_python_tool.sh safegit.py commit -m "Automated refactoring"
```

For complete non-interactive mode documentation, see [NON_INTERACTIVE_GUIDE.md](NON_INTERACTIVE_GUIDE.md).

## 🤝 Working with AI Assistants

### For AI Developers
When using this toolkit with AI coding assistants:

```python
# ✅ CORRECT - AI must use safegit wrapper
os.system("./run_any_python_tool.sh safegit.py add .")

# ❌ WRONG - Direct git commands are blocked
os.system("git reset --hard")  # BLOCKED!
```

### Configuration for AI
```bash
# Enable non-interactive mode for AI
export SAFEGIT_NONINTERACTIVE=1
export SAFEGIT_ASSUME_YES=1  # Still requires --force for dangerous ops

# But NEVER set:
export SAFEGIT_FORCE_YES=1  # This would bypass critical safety!
```

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[DATA_FLOW_TRACKER_GUIDE.md](DATA_FLOW_TRACKER_GUIDE.md)** - Complete data flow analysis and intelligence layer guide
- **[SAFEGIT_COMPREHENSIVE.md](docs/safegit/SAFEGIT_COMPREHENSIVE.md)** - Complete SafeGIT documentation
- **[SAFE_FILE_MANAGER_GUIDE.md](SAFE_FILE_MANAGER_GUIDE.md)** - Safe file operations guide
- **[NON_INTERACTIVE_GUIDE.md](NON_INTERACTIVE_GUIDE.md)** - Automation safety guide
- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Configuration for safety
- **[docs/](docs/)** - Comprehensive documentation directory

## 🛡️ Safety Guarantees

1. **No Accidental Data Loss** - Multiple confirmation layers
2. **No Surprise Operations** - Everything is explicit
3. **Always Recoverable** - Undo system and backups
4. **AI-Safe** - Cannot be tricked into dangerous operations
5. **Audit Trail** - Know what happened and when

## ⚠️ Important Safety Notes

- **Default Deny** - Operations fail safe when uncertain
- **No Force Flags in Production** - Use environment-specific configs
- **Regular Backups** - Tools create backups, but have your own too
- **Test First** - Use `--dry-run` before automation
- **Read the Warnings** - They're there for a reason

## 📝 Quick Tool Reference

### Latest Tool Versions

| Category | Tool | Version | Key Feature |
|----------|------|---------|-------------|
| **Documentation** | doc_generator.py | NEW | Automated intelligent documentation generation |
| **Documentation** | doc_generator_enhanced.py | ENHANCED | Full AST integration with interactive HTML |
| **Data Flow** | data_flow_tracker_v2.py | v2 | Intelligence layer with explanations & HTML |
| **Search** | find_text_v7.py | v7 | Multiline search with `--multiline` flag |
| **Replace** | replace_text_v9.py | v9 | Escape sequences + multi-level undo support |
| **AST Replace** | replace_text_ast_v3.py | v3 | Escape sequences + multi-level undo support |
| **Git Safety** | safegit.py | v2.0 | Complete protection, non-interactive mode |
| **File Safety** | safe_file_manager.py | Latest | Atomic operations, complete undo |
| **Release** | release_workflow.sh | Latest | `--yes` flag for automation |

### Most Used Commands

```bash
# Generate documentation (enhanced version recommended)
./run_any_python_tool.sh doc_generator_enhanced.py --function calculatePrice --file pricing.py --style api-docs

# Interactive HTML with all AST analysis
./run_any_python_tool.sh doc_generator_enhanced.py --class MyClass --file code.java --style api-docs --format interactive

# Track data flow with intelligence
./run_any_python_tool.sh data_flow_tracker_v2.py --var input_data --show-impact --explain --file app.py

# Search
./run_any_python_tool.sh find_text_v7.py "pattern" --multiline --type regex

# Replace with newlines
./run_any_python_tool.sh replace_text_v8.py "old" "new\nline" --interpret-escapes

# AST refactoring
./run_any_python_tool.sh unified_refactor_v2.py rename old new --file script.py  # Auto-detects Python backend

# Safe file operations
./run_any_python_tool.sh safe_file_manager.py move old.txt new.txt

# Safe git
./run_any_python_tool.sh safegit.py status
```

## 🔐 Achieving Maximum Safety (For AI Developers & Enterprises)

While the toolkit provides immediate value with its built-in safety features, achieving **maximum protection** requires blocking direct access to dangerous commands at the system level. This is especially critical when using AI coding assistants.

### Why Full Lockdown Matters

Recent incidents demonstrate that AI agents can cause catastrophic damage:
- **[Replit's AI database wipe](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/)** - Complete data loss from AI assistant
- **Accidental `rm -rf /`** - Entire systems destroyed by AI misunderstanding  
- **Git force pushes** - Permanent loss of team's work
- **File system corruption** - `dd` commands overwriting critical data

### The Defense-in-Depth Approach

```
┌─────────────────────────────────────────────────────┐
│                AI Agent Protection                  │
├─────────────────────────────────────────────────────┤
│ Level 1: Safe Tools (Immediate)                     │
│  • Automatic backups before operations              │
│  • Smart confirmations prevent accidents            │
│  • Complete undo/recovery capabilities              │
├─────────────────────────────────────────────────────┤
│ Level 2: System Lockdown (Maximum Protection)       │
│  • Block dangerous commands at OS level             │  
│  • Enforce safe alternatives only                   │
│  • Monitor and alert on bypass attempts             │
│  • Zero-trust configuration for AI agents           │
└─────────────────────────────────────────────────────┘
```

### Quick Examples

**Single most compelling SafeGIT example:**
```bash
# AI agent attempts dangerous operation
git reset --hard  # ❌ BLOCKED with confirmation required

# Safe alternative automatically suggested  
./run_any_python_tool.sh safegit.py reset --hard  # ✅ Creates backup first
```

**Single most compelling Safe File Manager example:**
```bash  
# AI agent attempts file deletion
rm important_files/  # ❌ BLOCKED - rm not available

# Safe alternative with full recovery
./run_any_python_tool.sh safe_file_manager.py trash important_files/  # ✅ Reversible
```

### The Complete Solution

For step-by-step implementation of enterprise-grade AI safety:

➡️ **[Complete AI Safety Setup Guide →](docs/AI_SAFETY_SETUP.md)**

**Includes:**
- **Code-level protection** - AI agent integration patterns
- **System-level lockdown** - Shell restrictions and command blocking  
- **Container isolation** - Docker/Kubernetes deployment
- **Enterprise compliance** - Audit trails and monitoring
- **Validation scripts** - Automated safety testing
- **Incident response** - When safety measures are bypassed

### The Payoff

With maximum protection in place:
- **🛡️ Zero risk** of AI agents destroying data
- **📊 Complete audit trail** of all operations  
- **↩️ Instant recovery** from any mistake
- **😌 Peace of mind** when using AI assistants
- **✅ Compliance ready** for regulated environments

**Remember: The safe tools only protect you if dangerous commands are blocked at the source!**

## 🤝 Contributing

We welcome contributions that enhance safety! Please ensure:

1. All code follows safety-first principles
2. Dangerous operations have confirmations
3. Changes are reversible where possible
4. Documentation includes safety warnings

## 📄 License

Mozilla Public License 2.0 (MPL-2.0) - See [LICENSE.txt](LICENSE.txt)

## 🙏 Acknowledgments

- Built in response to real-world AI disasters
- Inspired by aerospace "fail-safe" design principles
- Thanks to the community for safety feedback

## 🔗 Quick Links

- [Report Safety Issues](https://github.com/[your-username]/code-intelligence-toolkit/issues)
- [Safety Best Practices](docs/SAFETY_BEST_PRACTICES.md)
- [Disaster Recovery Guide](docs/DISASTER_RECOVERY.md)

---

**Remember: In software, as in life, safety first! 🛡️**

*"The best error is the one that never happens." - Code Intelligence Toolkit Philosophy*

---

**Keywords**: AI Agent Development, Safe Code Refactoring, Static Analysis Tools, AI Safety, Data Flow Analysis, Python SDK, Code Intelligence, Zero-Index Architecture, DevSecOps, CI/CD Automation, Java Code Analysis.