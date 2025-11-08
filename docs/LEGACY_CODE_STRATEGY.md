# Legacy Code Strategy

## Overview

The 3dsconv project maintains **two implementations** side-by-side:

1. **Refactored Implementation** (default) - Modular, testable, clean architecture
2. **Legacy Implementation** (reference) - Original monolithic code, preserved for validation

This dual-implementation strategy ensures correctness while enabling modernization.

## Why Keep Legacy Code?

### 1. Validation & Correctness
The legacy implementation serves as a **reference oracle** for validating the refactored version:
- Byte-for-byte output comparison
- Ensures identical behavior
- Catches regression bugs immediately

### 2. Debugging & Understanding
When investigating issues:
- Compare implementations side-by-side
- Understand original intent
- Reference for complex cryptographic operations

### 3. Performance Baseline
Measure impact of architectural changes:
- Execution time comparison
- Memory usage tracking
- Identify optimization opportunities

### 4. Fallback Option
If critical issues are discovered:
- Users can switch to `--legacy` mode
- Minimal disruption
- Time to fix refactored implementation

### 5. Regression Testing
Automated CI/CD validation:
- Test both implementations on same inputs
- Alert on any differences
- Prevent behavioral changes

## Usage Guide

### Running the Refactored Implementation (Default)

```bash
# Standard usage - uses refactored modular implementation
python -m dsconv input.cci -o output/

# With options
python -m dsconv input.cci -o output/ -b boot9.bin -v
```

### Running the Legacy Implementation

```bash
# Using --legacy flag
python -m dsconv --legacy input.cci -o output/

# Or directly
python -m dsconv.legacy input.cci -o output/
```

### Validating Implementations

Compare outputs from both implementations:

```bash
# Validate a single file
python scripts/validate_refactor.py input.cci

# Validate multiple files
python scripts/validate_refactor.py examples/test-ccis/*.cci -o validation_results/
```

The validation script will:
- Run both implementations on same input
- Compare file sizes, MD5, and SHA256 hashes
- Report byte-by-byte differences if any
- Exit with code 0 if outputs match, 1 if they differ

## Architecture Comparison

### Legacy Implementation (`dsconv/legacy.py`)

**Characteristics:**
- **Structure**: Single 777-line monolithic file
- **State**: Module-level global variables (`args`, `keys_set`, `orig_ncch_key`)
- **Functions**: Nested functions with closures for key loading
- **I/O**: Direct file operations throughout
- **Testing**: No unit tests, minimal test coverage
- **Coupling**: Tight coupling between concerns

**Pros:**
- Simple to understand as a linear script
- Proven to work correctly
- No dependency injection complexity

**Cons:**
- Difficult to test in isolation
- Hard to extend with new features
- Global state makes reasoning difficult
- Mixed concerns (I/O, crypto, validation)

### Refactored Implementation (`dsconv/cli/`, `dsconv/services/`, etc.)

**Characteristics:**
- **Structure**: ~20 focused modules with clear responsibilities
- **State**: No global state, all dependencies injected
- **Functions**: Dedicated classes with single responsibilities
- **I/O**: Separate readers/writers with abstractions
- **Testing**: 100% test coverage with unit and integration tests
- **Coupling**: Loose coupling via dependency injection

**Pros:**
- Easy to test with mocks
- Clear separation of concerns
- Extensible for new features
- Maintainable and readable

**Cons:**
- More files to navigate
- Requires understanding of dependency injection
- More complex initial setup

## Development Guidelines

### For New Features

**✅ DO: Add features to refactored implementation**

Modify code in:
- `dsconv/models/` - Data structures (NCCH, NCSD, CIA, encryption models)
- `dsconv/crypto/` - Encryption services (AES, key derivation, key providers)
- `dsconv/io/` - File I/O (readers, writers, binary utilities)
- `dsconv/validation/` - Validation logic (hash validators, format validators)
- `dsconv/services/` - Business logic (conversion service, configuration)
- `dsconv/cli/` - Command-line interface (argument mapping)

**❌ DON'T: Modify legacy implementation**

The legacy code is **FROZEN**. Only modify for critical bug fixes that affect validation.

### For Bug Fixes

**If bug affects both implementations:**
1. Fix in refactored implementation first
2. Validate outputs still match
3. If they don't match due to the fix, update legacy too
4. Document the change

**If bug only affects refactored implementation:**
1. Fix the bug
2. Add regression test
3. Validate outputs match legacy

**If bug only affects legacy implementation:**
1. Consider if it's critical
2. If not critical, document and move on
3. If critical, fix and note in documentation

## Validation Strategy

### Manual Validation

```bash
# Before releasing new version
python scripts/validate_refactor.py examples/test-ccis/*.cci

# Should see:
# ✅ MATCH: Outputs are identical (for all files)
```

### Automated Validation (CI/CD)

Currently not implemented in CI, but can be added:

```yaml
validate-refactor:
  name: Validate Refactored vs Legacy
  runs-on: ubuntu-latest
  needs: test
  
  steps:
  - name: Checkout code
    uses: actions/checkout@v4
  
  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.12'
  
  - name: Install dependencies
    run: pip install -e ".[dev]"
  
  - name: Run validation
    run: |
      if [ -d "examples/test-ccis" ]; then
        python scripts/validate_refactor.py examples/test-ccis/*.cci
      fi
```

## Migration Timeline

### Phase 1-7: Refactoring (Completed)
- ✅ Extract domain models
- ✅ Extract crypto services
- ✅ Extract I/O layer
- ✅ Extract validation services
- ✅ Create application services
- ✅ Refactor CLI layer
- ✅ Preserve legacy implementation

### Phase 8: Validation (Current)
- ✅ Task 8.1: Run comprehensive validation
- ✅ Task 8.2: Extract certificate chain loading
- ✅ **Task 8.3: Document legacy code strategy** (this document)
- ⏳ Task 8.4: Add validation to CI/CD

### Future: Deprecation (TBD)

The legacy implementation will be kept indefinitely as:
1. A reference implementation for correctness
2. A fallback for critical issues
3. Historical reference for understanding original design

**No current plans to remove the legacy implementation.**

## Troubleshooting

### Outputs Don't Match

If validation fails:

1. **Check file sizes first**
   ```bash
   ls -lh validation_output/legacy/*.cia
   ls -lh validation_output/refactored/*.cia
   ```

2. **Compare hashes**
   ```bash
   md5sum validation_output/legacy/*.cia
   md5sum validation_output/refactored/*.cia
   ```

3. **Find first difference**
   The validation script reports the first byte offset where files differ

4. **Investigate the difference**
   - Was there a recent change to refactored code?
   - Is this an intentional improvement?
   - Is this a regression bug?

### Performance Differences

If refactored version is slower:

1. **Profile both implementations**
   ```bash
   python -m cProfile -o legacy.prof -m dsconv.legacy input.cci
   python -m cProfile -o refactored.prof -m dsconv input.cci
   ```

2. **Identify bottlenecks**
   ```bash
   python -m pstats legacy.prof
   python -m pstats refactored.prof
   ```

3. **Optimize hot paths** in refactored implementation while maintaining correctness

## References

- **Refactoring Plan**: `project-plans/refactoring-plan.md`
- **Implementation Guide**: `project-plans/implementation-guide.md`
- **Legacy Code**: `dsconv/legacy.py`
- **Refactored Entry Point**: `dsconv/cli/main.py`
- **Validation Script**: `scripts/validate_refactor.py`
- **Test Suite**: `tests/`

## Questions?

For questions about:
- **Using the tool**: See `README.md`
- **Contributing**: See `CONTRIBUTING.md`
- **Development**: See `docs/DEVELOPMENT.md`
- **Refactoring plan**: See `project-plans/refactoring-plan.md`
- **Testing**: See `project-plans/Test-Automation-Plan.md`

---

**Last Updated**: 2025-11-08  
**Status**: Active - Legacy strategy in effect  
**Maintainer**: 3dsconv contributors
