# AI Agents - Multi-Agent Code Generation System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Anthropic Claude](https://img.shields.io/badge/AI-Anthropic%20Claude-orange.svg)](https://www.anthropic.com/)

A Python-based multi-agent system for automated code generation with **Architect → Coder → Tester → DocWriter** workflow.

## 🎯 What does this tool do?

This AI-powered system automates your entire development workflow:

1. **🏗️ Architect** analyzes your requirements and creates a technical specification
2. **💻 Coder** implements the solution with production-ready code
3. **🧪 Tester** performs comprehensive quality assurance and testing
4. **📝 DocWriter** creates professional PR documentation

**Result**: Complete features with code, tests, and documentation - ready for production!

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Anthropic API Key** (get it from [Anthropic Console](https://console.anthropic.com/))
- **Git** (for repository operations)
- **GitHub CLI** (optional, for PR creation)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ai-agents.git
cd ai-agents

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Create .env from template
cp .env.example .env

# Edit .env and fill in:
# ANTHROPIC_API_KEY=your_actual_key_here
# REPO_PATH=/absolute/path/to/your/target/repo
```

**Required Environment Variables:**

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `REPO_PATH`: Absolute path to the repository you want to work on

### 3. Usage

```bash
# Dry-run (shows generated patch only)
python run_task.py --goal "Add dark mode toggle to navbar" --dry-run

# Real run with PR creation
python run_task.py --goal "Add dark mode toggle to navbar" --apply --pr --scope "feat/dark-mode"

# With additional context files
python run_task.py --goal "Fix login validation" --context-files "src/routes/login/+page.svelte src/lib/auth.ts" --apply
```

### Context Files: Files, Folders, Globs

The `--context-files` argument accepts various specifications:

```bash
# Individual files
--context-files "src/app.ts src/lib/utils.js"

# Entire folders (all allowed file types)
--context-files "src/components src/lib"

# Glob patterns
--context-files "src/routes/**/*.svelte src/lib/components/ui/*.ts"
```

## Features

- **Package Manager Auto-Detection**: Supports npm, yarn, pnpm, bun automatically via lockfiles
- **Security**: Branch name validation and commit message sanitizing
- **Fallbacks**: Graceful handling when JS project tools are missing
- **Configurable**: Overridable test commands in `config.yaml`
- **Budget Control**: Token limits and cost monitoring

## Model Optimization & Provider

### Adaptive Model Selection

The system automatically selects the optimal model based on task complexity:

- **LOW Complexity**: `claude-3-5-haiku-latest` (~€0.10/Task)
- **MEDIUM Complexity**: `claude-3-5-sonnet-latest` (~€0.30/Task)  
- **HIGH Complexity**: `claude-3-5-sonnet-latest` (~€1.00/Task)

### Budget Optimization

```bash
# Check budget status
python run_task.py --budget-report

# Force cheaper model
python run_task.py --goal "Task" --force-model claude-3-5-haiku-latest

# Complexity analysis without execution
python run_task.py --goal "Task" --complexity-only
```

The system automatically warns at 80% daily budget usage and recommends cost optimizations.

## Intelligent Context Caching

### Automatic File Caching

The system implements intelligent caching for optimal token efficiency:

- **Smart Sessions**: Logically related prompts share the same cache
- **Change Detection**: Only changed files are reloaded
- **Context Chaining**: Follow-up prompts are cheaper and seamless

```bash
# Normal workflow (caching automatically active)
python run_task.py --goal "Build layout" --context-files "src/components"
python run_task.py --goal "Add functionality to layout" --context-files "src/components"  # Cache hit!

# Check cache status
python run_task.py --cache-stats

# Reset cache (for new task)
python run_task.py --cache-reset all

# Disable caching (if desired)
python run_task.py --goal "Task" --no-cache
```

### Token Optimization

- **Up to 40 files** per cache session
- **24h session timeout** for automatic cleanup
- **Warning on exceeding** file limits
- **Intelligent deduplication** prevents duplicate content

## 📋 Requirements

### System Requirements

- Python 3.8 or higher
- Git installed and configured
- Internet connection for AI API calls

### Dependencies

All dependencies are listed in `requirements.txt`:

- `anthropic>=0.20.0` - Anthropic Claude API
- `pyyaml>=6.0` - Configuration file parsing
- `rich>=13.0.0` - Beautiful terminal output
- `gitpython>=3.1.0` - Git operations
- `python-dotenv>=1.0.0` - Environment variable management

### Optional Dependencies

- `click>=8.0.0` - Enhanced CLI functionality
- `typer>=0.9.0` - Advanced CLI features
- `loguru>=0.7.0` - Enhanced logging

## 💰 Cost Information

This tool uses Anthropic's Claude API, which is a paid service:

- **Haiku Model**: ~€0.10 per task (simple tasks)
- **Sonnet Model**: €0.30-1.00 per task (complex tasks)
- **Budget Control**: Built-in cost monitoring and warnings
- **Optimization**: Automatic model selection based on complexity

## 🛠️ How It Works

1. **Task Analysis**: The system analyzes your goal and determines complexity
2. **Context Collection**: Gathers relevant files from your repository
3. **Multi-Agent Pipeline**:
   - Architect creates technical specification
   - Coder implements the solution
   - Tester validates quality and security
   - DocWriter creates PR documentation
4. **Git Integration**: Creates branch, applies changes, and optionally creates PR

## 🔒 Security & Privacy

- **Local Processing**: Your code stays on your machine
- **API Calls**: Only sends relevant context to Anthropic (no full codebase)
- **No Storage**: AI provider doesn't store your code
- **Input Validation**: All inputs are sanitized for security
- **Branch Protection**: Safe git operations with validation

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/ai-agents/issues)
- **Documentation**: [Contributing Guide](CONTRIBUTING.md)
- **Questions**: Use the [Question Template](.github/ISSUE_TEMPLATE/question.md)
