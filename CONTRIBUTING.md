# Contributing to 3dsconv

Thank you for your interest in contributing to 3dsconv! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Using GitHub Copilot](#using-github-copilot)

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- Basic understanding of Nintendo 3DS file formats (helpful but not required)
- Familiarity with binary file handling in Python

### Understanding the Project

Before contributing, please review:
1. **[README.md](README.md)** - Project overview and usage
2. **[agents.md](agents.md)** - Complete technical context and architecture
3. **[Test-Automation-Plan.md](Test-Automation-Plan.md)** - Testing strategy
4. **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Copilot-specific guidance

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/3dsconv.git
cd 3dsconv
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install package in editable mode with dev tools
pip install -e ".[dev]"

# Verify installation
3dsconv --help
pytest --version
black --version
ruff --version
```

### 4. Verify Setup

```bash
# Run existing tests
pytest

# Check code formatting
black --check dsconv/

# Run linter
ruff check dsconv/

# Run type checker
mypy dsconv/
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-encryption-support`
- `fix/hash-validation-bug`
- `docs/update-readme`
- `test/add-integration-tests`

```bash
git checkout -b feature/your-feature-name
```

### Code Organization

- **Main logic:** `dsconv/3dsconv.py` (conversion implementation)
- **Utilities:** `dsconv/utils.py` (testable helper functions)
- **Entry point:** `dsconv/__main__.py` (CLI interface)
- **Tests:** `tests/` (unit, integration, e2e)

### Making Minimal Changes

Follow the principle of **minimal change**:
- Only modify what's necessary to fix the issue or add the feature
- Don't refactor unrelated code in the same PR
- Preserve backward compatibility unless explicitly breaking
- Keep changes focused and easy to review

### Documentation

Update documentation when making user-facing changes:
- Update `README.md` for new CLI options or usage changes
- Update `agents.md` for architectural changes
- Add docstrings to new functions
- Update `.github/copilot-instructions.md` for significant changes

## Testing

### Test Structure

```
tests/
├── unit/                # Fast, isolated tests
│   ├── test_crypto_utils.py
│   ├── test_parse_args.py
│   └── test_output.py
├── integration/         # Multi-component tests
├── e2e/                # Full workflow tests
├── fixtures/           # Test data
└── conftest.py         # Shared fixtures
```

### Writing Tests

**Always add tests for new code:**

```python
# tests/unit/test_your_feature.py
import pytest
from dsconv.utils import your_function

class TestYourFeature:
    """Test suite for your new feature."""
    
    def test_basic_behavior(self):
        """Test the basic behavior of the function."""
        # Arrange
        input_value = "test"
        expected = "expected_output"
        
        # Act
        result = your_function(input_value)
        
        # Assert
        assert result == expected
    
    @pytest.mark.parametrize("input,expected", [
        ("case1", "output1"),
        ("case2", "output2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple input cases."""
        assert your_function(input) == expected
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_crypto_utils.py

# Run with coverage
pytest --cov=dsconv --cov-report=html

# Run specific test
pytest tests/unit/test_parse_args.py::TestParseArgs::test_minimal_required
```

### Test Coverage Requirements

- **New code:** Aim for 80%+ coverage
- **Bug fixes:** Add test that reproduces the bug
- **Refactoring:** Maintain or improve existing coverage

## Code Style

### Python Conventions

We follow PEP 8 with some modifications:

- **Line length:** 100 characters (configured in black and ruff)
- **Indentation:** 4 spaces (no tabs)
- **Naming:**
  - Functions/variables: `snake_case`
  - Constants: `snake_case` (not UPPER_CASE in this project)
  - Classes: `PascalCase` (if adding new classes)
- **Type hints:** Encouraged for new code, optional for existing

### Formatting and Linting

**Before committing, always run:**

```bash
# Auto-format code
black dsconv/

# Fix auto-fixable linting issues
ruff check --fix dsconv/

# Check remaining issues
ruff check dsconv/

# Type check
mypy dsconv/
```

### Pre-commit Checklist

- [ ] Code is formatted with black
- [ ] No ruff linting errors
- [ ] Type hints added for new functions
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages are descriptive

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

**Good:**
```
Add support for retail dev-unit encryption detection

- Detect dev-unit encryption bitmask
- Add --dev-keys validation
- Update tests for dev encryption path
```

**Bad:**
```
fixed stuff
update
changes
```

### Pull Request Process

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub:**
   - Use descriptive title
   - Fill out PR template completely
   - Reference related issues
   - Include testing performed

3. **PR Template Sections:**
   - **Description:** What changes were made and why
   - **Type of Change:** Bug fix, feature, docs, etc.
   - **Testing:** How was this tested?
   - **Checklist:** Pre-submission checks

4. **Review Process:**
   - Maintainers will review your PR
   - Address feedback promptly
   - Keep PR focused and small
   - Be patient and respectful

### PR Best Practices

- **Keep PRs small:** Easier to review and merge
- **One feature per PR:** Don't combine unrelated changes
- **Update branch:** Rebase on main if needed
- **Fix CI failures:** Ensure all checks pass
- **Respond to reviews:** Address comments and questions

## Using GitHub Copilot

### For Contributors

If you're using GitHub Copilot or similar AI assistants:

1. **Read context files first:**
   - [.github/copilot-instructions.md](.github/copilot-instructions.md)
   - [agents.md](agents.md)
   
2. **Key Copilot prompts:**
   ```
   # Generate a function
   "Create a function to extract partition sizes from NCSD header"
   
   # Write tests
   "Generate unit tests for parse_args() function"
   
   # Explain code
   "Explain how encryption detection works in 3dsconv.py lines 363-368"
   ```

3. **Verify suggestions:**
   - Always review Copilot-generated code
   - Test thoroughly
   - Check against existing patterns
   - Ensure backward compatibility

### For Maintainers

When reviewing Copilot-assisted PRs:
- Look for understanding of project context
- Verify tests are comprehensive
- Check adherence to coding standards
- Ensure minimal changes principle

## Common Contribution Areas

### 1. Bug Fixes
- Check existing issues first
- Add test that reproduces bug
- Fix with minimal change
- Verify fix doesn't break other features

### 2. New Features
- Discuss in issue first for major features
- Follow existing patterns
- Add comprehensive tests
- Update documentation

### 3. Documentation
- Fix typos and clarifications
- Add examples and tutorials
- Improve code comments
- Update agent context files

### 4. Tests
- Improve test coverage
- Add integration tests
- Create test fixtures
- Fix flaky tests

### 5. Performance
- Profile before optimizing
- Maintain correctness
- Add benchmarks
- Document improvements

## Questions and Help

- **General questions:** Open a discussion
- **Bug reports:** Open an issue with reproduction steps
- **Feature requests:** Open an issue with use case
- **Security issues:** Email maintainers privately

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to 3dsconv! Your efforts help make this tool better for everyone.
