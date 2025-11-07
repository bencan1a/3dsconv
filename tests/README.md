# 3dsconv Test Suite

This directory contains automated tests for the 3dsconv project, following the test automation plan documented in `Test-Automation-Plan.md`.

## Test Structure

```
tests/
├── conftest.py          # Shared pytest fixtures
├── unit/                # Unit tests for isolated functions
│   ├── test_crypto_utils.py    # Tests for cryptographic functions (rol)
│   ├── test_parse_args.py      # Tests for CLI argument parsing
│   └── test_output.py          # Tests for output utilities
├── integration/         # Integration tests (Phase 2 - TODO)
├── e2e/                # End-to-end tests (Phase 3 - TODO)
└── fixtures/           # Test data files (Phase 2 - TODO)
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/unit/test_crypto_utils.py
```

### Run with coverage
```bash
pytest tests/ --cov=dsconv.utils --cov-report=term-missing
```

### Run with verbose output
```bash
pytest tests/ -v
```

## Current Test Coverage

### Phase 1 (Completed)
- **Unit Tests**: 52 tests
  - `test_crypto_utils.py`: 18 tests for the `rol()` function
  - `test_parse_args.py`: 21 tests for CLI argument parsing
  - `test_output.py`: 13 tests for output utilities (`error()`, `show_progress()`)
- **Coverage**: 100% on `dsconv/utils.py`
- **Status**: ✅ All tests passing

### Phase 2 (Planned)
- Integration tests for binary format validation
- Integration tests for encryption detection
- Integration tests for hash validation

### Phase 3 (Planned)
- End-to-end tests for successful conversions
- End-to-end tests for error scenarios
- End-to-end tests for CLI options

## Test Development Guidelines

### Best Practices Applied
1. **Isolation**: Tests are independent and don't rely on external state
2. **AAA Pattern**: Tests follow Arrange-Act-Assert structure
3. **Parametrization**: Use `@pytest.mark.parametrize` for testing multiple scenarios
4. **Fixtures**: Use pytest fixtures for shared setup (see `conftest.py`)
5. **Mocking**: Use `monkeypatch` and `capsys` for testing side effects
6. **Descriptive Names**: Test names clearly describe what is being tested

### Writing New Tests
1. Create test file in appropriate directory (`unit/`, `integration/`, or `e2e/`)
2. Follow naming convention: `test_*.py`
3. Use test classes for grouping related tests: `class TestFeatureName:`
4. Use descriptive test method names: `def test_specific_behavior():`
5. Include docstrings explaining what the test verifies
6. Use fixtures from `conftest.py` when applicable

## Dependencies
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting

## Notes
- The `dsconv/utils.py` module was created to extract testable functions from `3dsconv.py`
- Some functions like `print_v()` and `v()` depend on global state and are deferred to later phases
- Test data fixtures for binary files will be added in Phase 2

## Resources
- [Test Automation Plan](../Test-Automation-Plan.md) - Complete test strategy and roadmap
- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
