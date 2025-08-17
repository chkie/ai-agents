# Contributing to AI Agents

We welcome contributions to this project! Here you'll find all the important information.

## 🚀 Quick Start

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd ai-agents

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY + REPO_PATH
```

### Run First Test

```bash
# Dry-run test
python run_task.py --goal "Add simple test feature" --dry-run

# Complexity analysis
python run_task.py --goal "Test task" --complexity-only
```

## 📝 Development Guidelines

### Code Standards

- **Python 3.8+** required
- **Type Hints** use where possible
- **Docstrings** for all public functions
- **Error Handling** with specific Exception types
- **Logging** instead of print() for debug output

### Code Style

```bash
# Format code (optional)
black src/ run_task.py

# Linting (optional)
flake8 src/ run_task.py
```

### Commit Convention

```bash
# Format: <type>(<scope>): <description>
feat(core): Add new complexity analyzer
fix(budget): Fix cost calculation bug
docs: Update README with new examples
refactor(context): Improve caching logic
```

## 🧪 Testing

### Manual Testing

```bash
# Check budget status
python run_task.py --budget-report

# Cache statistics
python run_task.py --cache-stats

# Test with different complexity levels
python run_task.py --goal "Simple fix" --complexity-only
python run_task.py --goal "Complex architecture refactoring" --complexity-only
```

### Test Scenarios

1. **Low Complexity**: Simple bug fixes, typo corrections
2. **Medium Complexity**: Feature implementations, API changes
3. **High Complexity**: Architecture refactoring, security updates

## 🔧 Component Overview

### Core Modules

- **`run_task.py`**: Main entry point and workflow orchestration
- **`src/llm.py`**: LLM API integration with error handling
- **`src/context.py`**: File context collection and caching
- **`src/git_ops.py`**: Git operations (branch, commit, PR)
- **`src/budget_monitor.py`**: Cost tracking and budget management

### Advanced Features

- **`src/complexity_analyzer.py`**: Task complexity assessment
- **`src/context_cache.py`**: Intelligent file caching system
- **`src/premium_features.py`**: Extended quality features
- **`src/test_runner.py`**: Package manager detection and test execution

## 🐛 Bug Reports

### Use Issue Templates

Use the provided issue templates:

- **Bug Report**: For errors and unexpected behavior
- **Feature Request**: For new features and improvements
- **Question**: For usage questions

### Important Information

```bash
# Gather debug information
python run_task.py --budget-report
python run_task.py --cache-stats

# Check log files
ls -la .ai_agents_*
```

## 🚀 Feature Requests

### Before You Start

1. **Create issue** with detailed description
2. **Wait for discussion** - a solution might already exist
3. **Create fork** and feature branch
4. **Implementation** with tests
5. **Pull request** with detailed description

### Priorities

- **Security**: Security improvements have highest priority
- **Performance**: Optimizations for large codebases
- **Usability**: User experience improvements
- **New Features**: New functionality based on community needs

## 📋 Pull Request Process

### Checklist

- [ ] Branch created from `main`
- [ ] Descriptive commit messages
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Manually tested
- [ ] PR template completely filled out

### Review Process

1. **Automated Checks**: Linting and basic tests
2. **Code Review**: At least 1 maintainer approval
3. **Manual Testing**: Functionality test for larger changes
4. **Merge**: Squash-merge into main branch

## 🎯 Roadmap & Vision

### Short/Medium Term

- **Unit Tests**: Comprehensive test suite
- **CI/CD Pipeline**: Automated testing and releases
- **Documentation**: API documentation and tutorials
- **Performance**: Parallelization of API calls

### Long Term

- **Multi-Provider Support**: OpenAI, Anthropic, Local Models
- **Plugin System**: Extensible architecture
- **Web Interface**: Optional GUI for non-CLI users
- **Team Features**: Multi-user and collaboration features

## 💬 Community

### Communication

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and idea exchange
- **Pull Requests**: For code contributions

### Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📚 Additional Resources

### Useful Links

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Rich Console Documentation](https://rich.readthedocs.io/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)

### Example Configurations

```yaml
# config.yaml - Example for development
models:
  architect: "claude-3-5-haiku-latest"    # Cost-effective for testing
  coder: "claude-3-5-sonnet-latest"       # Premium for code quality
  tester: "claude-3-5-sonnet-latest"      # Premium for QA
  docwriter: "claude-3-5-haiku-latest"    # Cost-effective for docs

budget:
  target_monthly_eur: 50.00               # Lower for development
  warn_at_percentage: 70                  # Earlier warning
```

---

**Thank you for your contributions! 🙏**
