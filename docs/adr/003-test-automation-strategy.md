# 3. Three-Phase Test Automation Strategy

**Date:** 2025-11-07  
**Status:** Accepted (Phase 1 Complete)  
**Deciders:** Project maintainers  
**Tags:** testing, quality-assurance, automation

## Context

The project had **no automated tests** despite being a critical tool that handles:
- Binary file parsing (CCI/CIA formats)
- Cryptographic operations (AES decryption, key derivation)
- File format validation (hashes, magic numbers)
- Multiple encryption types (decrypted, original NCCH, zerokey)

**Challenges:**
- Main logic is monolithic (676-line script with global state)
- Binary data testing requires fixtures
- Crypto dependencies (pyaes, boot9.bin)
- File I/O tightly coupled with business logic
- No existing test infrastructure

**Requirements:**
- 80% line coverage, 70% branch coverage
- Fast, deterministic tests
- CI/CD ready
- Support multiple Python versions (3.10-3.13)

## Decision

**Implement a three-phase test automation strategy:**

### Phase 1: Unit Tests (Foundation)
**Timeline:** 2-3 days  
**Coverage Target:** ~30%  
**Focus:** Pure and near-pure functions

**What to test:**
- `rol()` - Cryptographic rotate-left function
- `parse_args()` - CLI argument parsing
- `error()`, `show_progress()` - Output utilities

**Approach:**
- Create `dsconv/utils.py` for testable functions
- Use pytest with standard fixtures
- Mock side effects (stdout, sys.argv, environment)
- Parametrize test cases for multiple scenarios

### Phase 2: Integration Tests
**Timeline:** 4-5 days  
**Coverage Target:** ~60% (cumulative)  
**Focus:** Multi-component interactions

**What to test:**
- Binary format validation (NCSD/NCCH magic)
- Encryption detection logic
- Hash validation (SHA-256, MD5)
- Key derivation process

**Approach:**
- Create minimal test CCI files (<1KB)
- Mock pyaes and boot9.bin
- Test each encryption path independently
- Focus on format parsing, not full conversion

### Phase 3: End-to-End Tests
**Timeline:** 3-4 days  
**Coverage Target:** 80% (cumulative)  
**Focus:** Complete workflows

**What to test:**
- Full CCI to CIA conversion
- Error scenarios (missing files, bad encryption)
- CLI option combinations
- Multiple file processing

**Approach:**
- Small but complete test files
- Test success and failure paths
- Verify output file structure
- Test backward compatibility

## Consequences

### Positive Consequences

- ✅ **Quality assurance** - Catch regressions early
- ✅ **Confidence in changes** - Safe refactoring
- ✅ **Documentation** - Tests serve as examples
- ✅ **CI/CD integration** - Automated quality gates
- ✅ **Contributor onboarding** - Tests show how code works
- ✅ **Fast feedback** - Unit tests run in milliseconds
- ✅ **Incremental approach** - Can deliver value early

### Negative Consequences

- ⚠️ **Initial time investment** - 2-3 weeks for full implementation
- ⚠️ **Test maintenance** - Tests need updating with code
- ⚠️ **Fixture complexity** - Binary test data can be hard to create
- ⚠️ **Mock complexity** - Crypto dependencies require mocking

### Neutral Consequences

- ℹ️ **Code refactoring needed** - Extract testable functions
- ℹ️ **Test infrastructure** - New directories, fixtures, configs
- ℹ️ **Coverage tools** - pytest-cov for coverage reporting

## Alternatives Considered

### Alternative 1: Big Bang Testing (All at Once)

**Description:** Write all tests (unit, integration, e2e) before proceeding

**Pros:**
- Complete coverage from day one
- No incremental planning needed
- Everything tested together

**Cons:**
- Long delay before any tests available
- Higher risk of scope creep
- Harder to debug issues
- No early value delivery

**Why rejected:** Too risky, no early feedback, violates agile principles

### Alternative 2: E2E Tests Only

**Description:** Focus only on end-to-end workflow tests

**Pros:**
- Tests real user scenarios
- Simpler test structure
- Fewer total tests needed

**Cons:**
- Slow test execution
- Hard to isolate failures
- Poor coverage of edge cases
- Difficult to debug
- Fragile (many moving parts)

**Why rejected:** Too slow, hard to maintain, doesn't catch low-level bugs

### Alternative 3: Manual Testing Only

**Description:** Continue with manual testing, no automation

**Pros:**
- No test writing effort
- No test maintenance
- Flexible testing approach

**Cons:**
- No regression detection
- Can't run in CI/CD
- Inconsistent coverage
- Time-consuming for developers
- Error-prone

**Why rejected:** Unsustainable for quality project, blocks CI/CD

## Implementation Notes

### Phase 1 Results (Completed - as of 2025-11-07)

**Created:**
- `dsconv/utils.py` - Testable utilities module
- `tests/unit/test_crypto_utils.py` - Tests for `rol()` function
- `tests/unit/test_parse_args.py` - Tests for CLI parsing
- `tests/unit/test_output.py` - Tests for output functions
- `tests/unit/test_prod_keys.py` - Tests for prod.keys parsing
- `tests/conftest.py` - Shared pytest fixtures
- `tests/README.md` - Test documentation

**Results (Phase 1 snapshot):**
- **Total tests:** 74 (52 initially, expanded with prod.keys tests)
- **Pass rate:** 100%
- **Coverage:** 100% on `dsconv/utils.py`
- **Speed:** <0.1s per test (all unit tests complete in <0.5s)

**Note:** These metrics represent the Phase 1 baseline. Test counts will increase as Phase 2 and 3 are implemented. See [PHASE1_SUMMARY.md](../../PHASE1_SUMMARY.md) for detailed Phase 1 completion report.

### Test Infrastructure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, isolated tests
├── integration/         # Multi-component tests
├── e2e/                # Full workflow tests
├── fixtures/           # Binary test data
└── README.md           # Documentation
```

### Tool Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--verbose", "--cov=dsconv", "--cov-report=term-missing"]
```

### CI/CD Integration

Tests run automatically on:
- Every push to main branches
- Every pull request
- Multiple Python versions (3.10-3.13)
- Multiple operating systems (Linux, Windows, macOS)

## References

- [Test-Automation-Plan.md](../../Test-Automation-Plan.md) - Detailed test plan
- [PHASE1_SUMMARY.md](../../PHASE1_SUMMARY.md) - Phase 1 completion report
- [pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Related Decisions

- [ADR-002: Modern Python Packaging](002-modern-packaging.md) - Pytest configuration in pyproject.toml
- Related to CI/CD workflow configuration

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-11-07 | AI Agent | Initial documentation with Phase 1 complete |
