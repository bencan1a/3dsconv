# 3dsconv Test Automation Plan

## Executive Summary

**Current State:** No automated tests exist  
**Target Coverage:** 80% line coverage, 70% branch coverage  
**Priority:** Focus on critical paths (encryption, validation, CIA structure)  
**Challenges:** Binary format testing, global state, crypto dependencies  

---

## Code Analysis Against Best Practices

### Current Issues
1. **Global State** – Heavy use of module-level globals (`args`, `keys_set`, `orig_ncch_key`, etc.)  
2. **No Separation** – All logic in one 676-line script with nested functions  
3. **Side Effects** – File I/O, printing, and `sys.exit()` throughout main execution path  
4. **Crypto Dependencies** – Requires `pyaes` and `boot9.bin` for encryption tests  
5. **No Testable Units** – Main processing loop (lines 313–665) is monolithic  

### Testable Functions (Pure/Near–Pure)

- `parse_args()` – Returns `argparse.Namespace`, has `sys.argv` dependency  
- `rol()` – Pure function for bit rotation  
- `show_progress()` – Side effect (stdout), but logic testable  
- `error()` – Simple wrapper (low priority)  
- `print_v()`, `v()` – Depends on global `args` (mock needed)  

### Non-Testable Without Refactoring
- Main conversion loop (lines 313–665) – Tightly coupled file I/O  
- Key loading logic (lines 261–298) – Nested functions with global state  
- Dev certchain loading (lines 215–230) – Nested function with global state  

---

## Test Strategy

### Phase 1: Unit Tests (Foundation)

**Goal:** Test isolated functions and utilities  
**Timeline:** 2–3 days  
**Coverage Target:** ~30%  

#### 1.1 Pure Functions
```
tests/unit/test_crypto_utils.py
├─ test_rol_basic_rotation
├─ test_rol_zero_bits
├─ test_rol_full_rotation
├─ test_rol_128bit_values
└─ test_rol_edge_cases
```
**Rationale:** `rol()` is critical for key derivation, pure function, easy to test.

#### 1.2 CLI Argument Parsing
```
tests/unit/test_parse_args.py
├─ test_parse_args_minimal_required
├─ test_parse_args_all_options
├─ test_parse_args_short_flags
├─ test_parse_args_long_flags
├─ test_parse_args_no_args_exits
├─ test_parse_args_boot9_env_var
├─ test_parse_args_deprecated_options
└─ test_parse_args_multiple_games
```
**Rationale:** CLI is entry point, well-isolated, uses standard `argparse`.

**Implementation Notes:**
- Mock `sys.argv` with `monkeypatch`
- Test `sys.exit()` with `pytest.raises(SystemExit)`
- Capture stderr with `capsys` for help message
- Mock `os.environ` for `BOOT9_PATH` tests

#### 1.3 Output Utilities (Low Priority)
```
tests/unit/test_output.py
├─ test_error_prints_with_prefix
├─ test_show_progress_formatting
├─ test_print_v_when_verbose
└─ test_v_returns_empty_when_not_verbose
```
**Rationale:** Low value but easy wins for coverage.

---

## Phase 2: Integration Tests (Critical Paths)

**Goal:** Test conversion with minimal test files  
**Timeline:** 4–5 days  
**Coverage Target:** ~60% (cumulative)

#### 2.1 Binary Format Validation
```
tests/integration/test_format_validation.py
├─ test_valid_ncsd_magic_accepted
├─ test_invalid_ncsd_magic_rejected
├─ test_valid_ncch_magic_accepted
├─ test_invalid_ncch_magic_rejected
├─ test_extracts_title_id_correctly
├─ test_extracts_partition_sizes
└─ test_handles_missing_partitions
```
**Test Data Strategy:**
- Create minimal CCI files (< 1 KB) with valid NCSD/NCCH magic, minimal partition table, and mock ExeFS with icon.
- Store in `tests/fixtures/minimal_*.cci`

**Implementation Notes:**
- Use `tmp_path` fixture for output
- Mock or bypass encryption (focus on format parsing)
- Use `bytes.fromhex()` for readable test data

#### 2.2 Encryption Detection & Key Derivation
```
tests/integration/test_encryption.py
├─ test_detects_decrypted_rom
├─ test_detects_zerokey_encryption
├─ test_detects_original_ncch_encryption
├─ test_ignore_encryption_flag
├─ test_key_derivation_with_mock_boot9
└─ test_missing_boot9_fails_gracefully
```
**Implementation Notes:**
- Mock `pyaes` for unit-level tests
- Create mock `boot9.bin` with known key
- Test each encryption path independently
- Use `monkeypatch` to simulate missing dependencies

#### 2.3 Hash Validation
```
tests/integration/test_hash_validation.py
├─ test_valid_extheader_hash_passes
├─ test_invalid_extheader_hash_fails
├─ test_ignore_bad_hashes_flag
├─ test_content_chunk_hashes
└─ test_info_records_hash
```
**Implementation Notes:**
- Pre-compute SHA-256 hashes for test data
- Test both success and failure paths
- Verify `--ignore-bad-hashes` behavior

---

### Phase 3: End-to-End Tests (Full Workflow)

**Goal:** Test complete conversion workflows  
**Timeline:** 3–4 days  
**Coverage Target:** 80% (cumulative)

#### 3.1 Successful Conversions
```
tests/e2e/test_conversion_success.py
├─ test_convert_decrypted_cci_to_cia
├─ test_convert_with_manual_cfa
├─ test_convert_with_dlp_child
├─ test_convert_multiple_files
├─ test_overwrite_existing_cia
└─ test_custom_output_directory
```

#### 3.2 Error Scenarios
```
tests/e2e/test_conversion_errors.py
├─ test_missing_input_file
├─ test_encrypted_without_keys
├─ test_corrupt_cci_file
├─ test_existing_output_no_overwrite
└─ test_invalid_file_format
```

#### 3.3 CLI Options
```
tests/e2e/test_cli_options.py
├─ test_verbose_output
├─ test_dev_keys_mode
├─ test_ignore_encryption
├─ test_ignore_bad_hashes
└─ test_deprecated_options_warning
```

---

## Test Infrastructure

### Directory Structure
```
tests/
├─ conftest.py
├─ fixtures/
│  ├─ minimal_decrypted.cci
│  ├─ minimal_encrypted.cci
│  ├─ mock_boot9.bin
│  ├─ invalid_ncsd.bin
│  └─ certchain-dev.bin
├─ unit/
│  ├─ test_crypto_utils.py
│  ├─ test_parse_args.py
│  └─ test_output.py
├─ integration/
│  ├─ test_format_validation.py
│  ├─ test_encryption.py
│  └─ test_hash_validation.py
└─ e2e/
   ├─ test_conversion_success.py
   ├─ test_conversion_errors.py
   └─ test_cli_options.py
```

### Shared Fixtures (`conftest.py`)
```python
@pytest.fixture
def minimal_cci_decrypted(tmp_path): ...
@pytest.fixture
def minimal_cci_encrypted(tmp_path): ...
@pytest.fixture
def mock_boot9(tmp_path): ...
@pytest.fixture
def mock_args(): ...
@pytest.fixture
def clean_output_dir(tmp_path): ...
```

### Mocking Strategy
- Mock `pyaes`, `boot9.bin`, file I/O, and `sys.stdout/stderr` using `mocker` and `capsys`
- Patch global state (`args`, `pyaes_found`, `keys_set`) using `mocker.patch`

### Parametrization Examples
```python
@pytest.mark.parametrize("encryption_type, bitmask", [
    ("decrypted", 0x04),
    ("zerokey", 0x01),
    ("original_ncch", 0x00),
])
def test_encryption_detection(encryption_type, bitmask):
    # Test each encryption path
```

---

### CLI Flag Parametrization
```python
@pytest.mark.parametrize("flag, attr, expected", [
    ("-v", "verbose", True),
    ("--verbose", "verbose", True),
    ("-o outdir", "output", "outdir"),
    ("--output outdir", "output", "outdir"),
])
def test_cli_flags(flag, attr, expected):
    # Test flag parsing
```

---

## Coverage Exclusions
- Embedded constants (no logic)
- Print statements (formatting only)
- Progress bar rendering
- Module-level initialization

## Success Metrics
- **Line Coverage:** 80%
- **Branch Coverage:** 70%
- **Function Coverage:** 90%
- **Quality Gates:** Fast, deterministic, CI/CD ready

## Refactoring Recommendations
- Extract pure functions (`extract_title_id`, etc.)
- Introduce dependency injection
- Create `CCIConverter` class
- Separate I/O from logic (`CCIReader`, `CIAWriter`)

---

## Implementation Order

### Week 1: Foundation
1. Setup infrastructure, fixtures, and unit tests

### Week 2: Critical Path
2. Implement validation, encryption, and hash tests

### Week 3: End-to-End
3. Add success/error/CLI E2E tests

### Week 4: Polish
4. Achieve 80% coverage and add CI/CD pipeline

---

## Risk Assessment

| Risk Level | Area | Mitigation |
|-------------|-------|-------------|
| **High** | Binary data complexity | Use minimal test files, hex literals |
| **High** | Crypto dependencies | Mock `pyaes`, use test keys |
| **High** | Global state pollution | Mocking and isolation |
| **Medium** | Large file handling | Test small chunks, mock reads |
| **Medium** | Fixture creation time | Start simple, iterate |
| **Low** | Pure function tests | Quick to implement |
| **Low** | CLI testing | Standard pytest pattern |

---

**Plan Version:** 1.0  
**Created:** 2025-11-07  
**Next Review:** After Phase 1 completion
