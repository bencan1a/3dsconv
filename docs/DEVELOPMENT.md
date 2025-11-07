# Development Workflow Guide

This guide provides step-by-step workflows for common development tasks in the 3dsconv project.

## Table of Contents
- [Initial Setup](#initial-setup)
- [Daily Development Workflow](#daily-development-workflow)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Using AI Assistants](#using-ai-assistants)

## Initial Setup

### 1. Fork and Clone Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/3dsconv.git
cd 3dsconv

# Add upstream remote
git remote add upstream https://github.com/ihaveamac/3dsconv.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
3dsconv --help
pytest --version
```

### 3. Verify Everything Works

```bash
# Run tests
pytest

# Check code quality
black --check dsconv/
ruff check dsconv/
mypy dsconv/

# Try the tool
python -m dsconv --help
```

## Daily Development Workflow

### Start of Day

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Update from upstream
git fetch upstream
git checkout master
git merge upstream/master

# Create feature branch
git checkout -b feature/your-feature-name
```

### During Development

```bash
# Make changes to code
# ...

# Run tests frequently
pytest tests/unit/  # Fast unit tests

# Check formatting
black dsconv/

# Fix linting issues
ruff check --fix dsconv/

# Run full test suite
pytest
```

### End of Day

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature X

- Implement core logic
- Add tests
- Update documentation"

# Push to your fork
git push origin feature/your-feature-name
```

## Making Changes

### Adding a New Feature

```bash
# 1. Create branch
git checkout -b feature/your-feature-name

# 2. Plan your changes (create ADR if significant)
# Read relevant documentation:
# - agents.md (project context)
# - .github/copilot-instructions.md (coding guidance)
# - docs/adr/ (architecture decisions)

# 3. Write tests first (TDD approach)
# Create test file in tests/unit/ or tests/integration/
nano tests/unit/test_your_feature.py

# 4. Run tests (should fail initially)
pytest tests/unit/test_your_feature.py -v

# 5. Implement feature
nano dsconv/your_module.py

# 6. Run tests until they pass
pytest tests/unit/test_your_feature.py -v

# 7. Format and lint
black dsconv/
ruff check --fix dsconv/

# 8. Run full test suite
pytest

# 9. Update documentation
nano README.md
nano .github/copilot-instructions.md

# 10. Commit
git add .
git commit -m "Add feature: your feature description"
```

### Fixing a Bug

```bash
# 1. Create branch
git checkout -b fix/bug-description

# 2. Write test that reproduces bug
nano tests/unit/test_bug_fix.py

# 3. Verify test fails
pytest tests/unit/test_bug_fix.py -v

# 4. Fix the bug
nano dsconv/module.py

# 5. Verify test passes
pytest tests/unit/test_bug_fix.py -v

# 6. Run full test suite
pytest

# 7. Format and lint
black dsconv/
ruff check --fix dsconv/

# 8. Commit
git add .
git commit -m "Fix: bug description

- Add test that reproduces issue
- Implement fix
- Verify all tests pass"
```

### Refactoring Code

```bash
# 1. Ensure tests pass before refactoring
pytest

# 2. Make refactoring changes
nano dsconv/module.py

# 3. Run tests after each small change
pytest

# 4. Ensure coverage doesn't decrease
pytest --cov=dsconv

# 5. Format and lint
black dsconv/
ruff check --fix dsconv/

# 6. Commit
git add .
git commit -m "Refactor: description of changes

- Extract function X
- Simplify logic in Y
- Maintain test coverage"
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_crypto_utils.py

# Specific test function
pytest tests/unit/test_crypto_utils.py::test_rol_basic_rotation

# With coverage
pytest --cov=dsconv --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

### Writing Tests

```bash
# 1. Create test file
nano tests/unit/test_your_feature.py

# 2. Follow AAA pattern
"""
def test_feature_behavior():
    '''Test description.'''
    # Arrange - Set up test data
    input_data = "test"
    
    # Act - Call the function
    result = your_function(input_data)
    
    # Assert - Verify result
    assert result == expected_output
"""

# 3. Run test
pytest tests/unit/test_your_feature.py -v
```

### Test Coverage Tips

```bash
# Check what's missing coverage
pytest --cov=dsconv --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=dsconv --cov-report=html

# Focus on specific module
pytest --cov=dsconv.utils --cov-report=term-missing
```

## Submitting Changes

### Pre-submission Checklist

```bash
# 1. Ensure all tests pass
pytest

# 2. Check code formatting
black --check dsconv/
# If it fails, format:
black dsconv/

# 3. Check linting
ruff check dsconv/
# Fix issues:
ruff check --fix dsconv/

# 4. Run type checker
mypy dsconv/

# 5. Update documentation if needed
# - README.md (user-facing changes)
# - .github/copilot-instructions.md (code changes)
# - agents.md (architectural changes)
# - docs/adr/ (significant decisions)

# 6. Review your changes
git diff

# 7. Ensure commit message is descriptive
git log --oneline -1
```

### Creating Pull Request

```bash
# 1. Push to your fork
git push origin feature/your-feature-name

# 2. Go to GitHub and create PR

# 3. Fill out PR template:
# - Description of changes
# - Type of change
# - Testing performed
# - Checklist items

# 4. Link related issues
# - Fixes #123
# - Related to #456

# 5. Wait for CI checks to pass

# 6. Address review feedback
```

### Updating PR Based on Feedback

```bash
# 1. Make requested changes
nano dsconv/module.py

# 2. Run tests
pytest

# 3. Commit changes
git add .
git commit -m "Address review feedback: specific changes"

# 4. Push updates
git push origin feature/your-feature-name

# The PR will automatically update
```

## Using AI Assistants

### With GitHub Copilot

```bash
# 1. Ensure context files are open:
# - .github/copilot-instructions.md
# - agents.md
# - Relevant test files

# 2. Use descriptive comments to guide Copilot
# Example:
# # Extract title ID from NCSD header at offset 0x108

# 3. Review suggestions carefully
# - Check against existing patterns
# - Verify with tests
# - Ensure backward compatibility

# 4. Ask Copilot to generate tests
# Example comment:
# # Generate unit tests for parse_args() function
```

### With Claude/ChatGPT

```bash
# 1. Provide context:
# "I'm working on the 3dsconv project. Here's the relevant code..."

# 2. Reference documentation:
# "See agents.md for project context"
# "See .github/copilot-instructions.md for coding standards"

# 3. Be specific:
# "Generate a function to extract partition sizes from CCI file"
# NOT: "help me with file parsing"

# 4. Ask for tests:
# "Also generate pytest tests for this function"

# 5. Verify suggestions:
pytest  # Always test AI-generated code
```

## Troubleshooting

### Tests Failing

```bash
# Run with verbose output
pytest -v

# Run specific failing test
pytest tests/unit/test_file.py::test_function -v

# Check if test environment is clean
rm -rf .pytest_cache
pytest

# Ensure dependencies are up to date
pip install -e ".[dev]" --upgrade
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .

# Check package structure
python -c "import dsconv; print(dsconv.__file__)"

# Verify PYTHONPATH
python -c "import sys; print(sys.path)"
```

### Linting/Formatting Issues

```bash
# Auto-format everything
black dsconv/ tests/

# Auto-fix linting
ruff check --fix dsconv/

# See what would be fixed (dry run)
ruff check --fix --diff dsconv/
```

## Quick Reference

### Common Commands

```bash
# Environment
source venv/bin/activate        # Activate venv
deactivate                      # Deactivate venv

# Development
pytest                          # Run tests
black dsconv/                   # Format code
ruff check --fix dsconv/        # Lint and fix
mypy dsconv/                    # Type check

# Git
git status                      # Check status
git diff                        # See changes
git log --oneline -10          # Recent commits

# Run tool
3dsconv --help                  # Installed command
python -m dsconv --help         # Module execution
```

### Keyboard Shortcuts (pytest)

- `Ctrl+C` - Stop test run
- Add `-x` flag - Stop at first failure
- Add `-v` flag - Verbose output
- Add `-s` flag - Show print statements
- Add `-k pattern` - Run tests matching pattern

---

**Need help?** Check [CONTRIBUTING.md](../CONTRIBUTING.md) for more details.
