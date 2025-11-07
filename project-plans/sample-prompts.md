# Sample Prompts for Refactoring Tasks

This document provides example prompts you can give to Copilot (or other agents) to execute specific tasks from the refactoring plan. Each prompt is designed to leverage the comprehensive guidance in the planning documents.

---

## General Prompt Template

```
I need you to implement [Task X.Y: Task Name] from the refactoring plan located in project-plans/refactoring-plan.md.

Before starting:
1. Read project-plans/refactoring-plan.md and locate the task description
2. Review the code patterns in project-plans/implementation-guide.md
3. Follow the step-by-step workflow in the implementation guide
4. Use project-plans/quick-reference.md for commands

Requirements:
- Follow all acceptance criteria listed in the task
- Achieve 100% test coverage for new code
- Use the code patterns from the implementation guide
- Run tests, linting, and formatting before completion
- Verify against the quality checklist

The task is complete when all acceptance criteria are met and the quality checklist passes.
```

---

## Example 1: Phase 1, Task 1.1 (Simple - Good Starting Point)

### Prompt

```
I need you to implement Task 1.1: Create NCCH Header Model from the refactoring plan.

Context:
- This is Phase 1 (Extract Domain Models), Task 1.1
- Review project-plans/refactoring-plan.md for the complete task description
- Follow the code patterns in project-plans/implementation-guide.md
- The implementation guide includes a complete worked example for this exact task

Requirements from the task:
1. Create file: dsconv/models/ncch.py
2. Create a dataclass called NCCHHeader with all NCCH header fields
3. Add type hints on all fields
4. Include property methods for:
   - is_encrypted (check encryption flags)
   - uses_zerokey (check zerokey flag)
   - size_bytes (convert media units to bytes)
5. Add __post_init__ validation
6. Add from_bytes() classmethod for parsing binary data
7. No I/O operations - pure data model

Testing requirements:
1. Create tests in tests/unit/models/test_ncch.py
2. Test valid data creation
3. Test validation (invalid magic, wrong sizes)
4. Test all properties with various flag combinations
5. Test from_bytes() with valid and invalid data
6. Use parametrized tests for flag combinations
7. Achieve 100% coverage

Steps to follow:
1. Read the worked example in project-plans/implementation-guide.md (Section: "Example: Implementing Task 1.1")
2. Create the directory: mkdir -p dsconv/models
3. Create the model file following the dataclass pattern
4. Create the test file following the test pattern
5. Run: pytest tests/unit/models/test_ncch.py --cov=dsconv.models.ncch --cov-report=term-missing
6. Format: black dsconv/models/ncch.py
7. Lint: ruff check dsconv/models/ncch.py
8. Update dsconv/models/__init__.py to export NCCHHeader

Acceptance criteria checklist:
- [ ] Dataclass with all NCCH header fields
- [ ] Type hints on all fields
- [ ] Property methods for computed values
- [ ] No I/O operations
- [ ] 100% test coverage
- [ ] All tests pass
- [ ] Code formatted with black
- [ ] Linting passes with ruff
- [ ] Module exports updated

Reference the implementation guide for the complete code example.
```

---

## Example 2: Phase 2, Task 2.3 (Medium Complexity)

### Prompt

```
I need you to implement Task 2.3: Create Key Provider Service from Phase 2 of the refactoring plan.

Context:
- This is Phase 2 (Extract Crypto Services), Task 2.3
- Dependencies: Phase 1 models must be complete
- Review project-plans/refactoring-plan.md for complete task description
- Use the Service Pattern from project-plans/implementation-guide.md

Task description from plan:
Create an abstract interface IKeyProvider and two concrete implementations:
1. ProdKeysKeyProvider - loads keys from prod.keys file
2. Boot9KeyProvider - loads keys from boot9.bin file

Requirements:
1. Create file: dsconv/crypto/key_provider.py
2. Define IKeyProvider abstract interface with method: get_original_ncch_key() -> int
3. Implement ProdKeysKeyProvider using dsconv.utils.get_slot0x2c_key_from_prod_keys()
4. Implement Boot9KeyProvider with boot9.bin parsing logic
5. Both implementations should handle file not found and validation errors
6. All dependencies injected (file paths via constructor)
7. No global state

Testing requirements:
1. Create tests in tests/unit/crypto/test_key_provider.py
2. Mock file system access (use tmp_path fixture)
3. Test both implementations with valid and invalid files
4. Test error handling (file not found, corrupt data, wrong hash)
5. Create a MockKeyProvider for use in other tests
6. Achieve 100% coverage

Code patterns to use:
- Abstract interface pattern (see implementation-guide.md)
- Service pattern with dependency injection
- Proper exception handling with specific error messages

Steps:
1. Create directory: mkdir -p dsconv/crypto
2. Review the "Abstract Interface Pattern" in implementation-guide.md
3. Create the key_provider.py file
4. Create comprehensive tests
5. Run: pytest tests/unit/crypto/test_key_provider.py -v
6. Check coverage: pytest tests/unit/crypto/test_key_provider.py --cov=dsconv.crypto.key_provider
7. Format and lint
8. Update dsconv/crypto/__init__.py exports

The boot9 parsing logic should:
- Calculate offset based on file size (0x8000 for full, 0 for protected)
- Add 0x400 offset for dev keys if dev_keys=True
- Read key at offset 0x59D0 + calculated offset
- Validate MD5 hash matches expected value
- Convert bytes to int (big-endian)

Acceptance criteria:
- [ ] IKeyProvider interface defined
- [ ] Two concrete implementations
- [ ] Proper error handling with specific exceptions
- [ ] Mock provider for testing
- [ ] 100% test coverage
- [ ] All quality checks pass
```

---

## Example 3: Phase 6, Task 6.3 (Complex Integration)

### Prompt

```
I need you to implement Task 6.3: Create Conversion Service (Main Orchestration) from Phase 6.

IMPORTANT: This is a complex integration task. Ensure all previous phases are complete before starting.

Dependencies check:
- Phase 1: Domain models (NCCH, NCSD, CIA, Encryption)
- Phase 2: Crypto services (key providers, decryption)
- Phase 3: File readers (NCSD, NCCH, ExeFS)
- Phase 4: Validation services
- Phase 5: File writers (CIA)

Context:
- This is the main orchestration service that coordinates the entire conversion workflow
- Review the complete task in project-plans/refactoring-plan.md
- Follow the Service Pattern in project-plans/implementation-guide.md
- This service uses dependency injection for ALL dependencies

Requirements:
1. Create file: dsconv/services/conversion_service.py
2. Create ConversionService class with constructor accepting:
   - ncsd_reader: NCSDReader
   - ncch_reader: NCCHReader
   - exefs_reader: ExeFSReader
   - cia_writer: CIAWriter
   - decryption_service: DecryptionService | None
   - hash_validator: HashValidator
   - progress_reporter: IProgressReporter
3. Implement convert() method with these stages:
   - Stage 1: Read and validate CCI structure
   - Stage 2: Read NCCH header and determine encryption
   - Stage 3: Read and validate extended header
   - Stage 4: Extract icon from ExeFS
   - Stage 5: Write CIA
4. Extract helper methods:
   - _determine_encryption()
   - _read_and_validate_extheader()
   - _extract_icon()
   - _write_cia()
5. All methods should use injected dependencies (no direct file I/O)
6. Report progress at each stage

Testing strategy:
1. Create tests in tests/unit/services/test_conversion_service.py
2. Mock ALL dependencies (readers, writers, validators)
3. Test successful conversion flow
4. Test error handling (invalid magic, bad hash, missing icon)
5. Test with encrypted and decrypted content
6. Verify correct calls to dependencies
7. Achieve 100% coverage

Integration testing:
1. Also create tests/integration/test_conversion_integration.py
2. Use minimal test fixtures (create small valid CCI structure)
3. Test end-to-end flow with real (minimal) data
4. Verify CIA output structure

Code pattern example structure:
```python
class ConversionService:
    def __init__(self, ncsd_reader, ncch_reader, ...):
        # Store all dependencies
        
    def convert(self, config: ConversionConfig) -> None:
        # Stage 1: Read CCI
        self.progress_reporter.report_stage("Reading CCI structure")
        container = self.ncsd_reader.read_container()
        
        # Stage 2: Analyze encryption
        # ... use injected services
        
        # Continue for all stages
```

Steps:
1. Review the complete code example in project-plans/refactoring-plan.md (Task 6.3)
2. Create the service following dependency injection pattern
3. Write comprehensive unit tests with mocks
4. Write integration tests with fixtures
5. Run all tests: pytest tests/unit/services/ tests/integration/ -v
6. Verify coverage: pytest --cov=dsconv.services.conversion_service
7. Format and lint

Acceptance criteria:
- [ ] All dependencies injected
- [ ] Clear workflow stages
- [ ] Error handling for each stage
- [ ] Integration tests with mocks
- [ ] End-to-end integration tests
- [ ] 100% unit test coverage
- [ ] All quality checks pass
```

---

## Example 4: Quick Task - Validation Service (Easy Win)

### Prompt

```
Quick task - implement Task 4.1: Create Hash Validator from Phase 4.

This is a simple, pure validation service - good for a quick win.

Requirements:
1. Create file: dsconv/validation/hash_validator.py
2. Create HashValidator class with constructor accepting ignore_bad_hashes: bool
3. Implement methods:
   - validate_extheader_hash(extheader: bytes, expected_hash: bytes) -> bool
   - compute_content_hash(content: bytes) -> bytes
4. If ignore_bad_hashes=True, validation always returns True
5. Use hashlib.sha256 for hashing

Testing:
1. Create tests/unit/validation/test_hash_validator.py
2. Test with known hash values
3. Test with ignore_bad_hashes=True and False
4. Test both success and failure cases
5. Parametrize tests for different inputs

This is a pure function service - should take about 30 minutes.

Follow the pattern in project-plans/implementation-guide.md Section "Service Pattern".

Run: pytest tests/unit/validation/test_hash_validator.py --cov=dsconv.validation.hash_validator
```

---

## Example 5: Using Multiple Documents

### Prompt

```
Implement Task 3.2: Create NCSD Reader from Phase 3.

Preparation:
1. Read the task details in project-plans/refactoring-plan.md (search for "Task 3.2")
2. Review the "Reader/Writer Pattern" in project-plans/implementation-guide.md
3. Check project-plans/quick-reference.md for commands

Before coding:
- Ensure Phase 1 (models) is complete - you'll need NCSDContainer and NCSDPartition
- Ensure Task 3.1 (BinaryReader) is complete - you'll use this as a dependency

Implementation:
1. Create file: dsconv/io/ncsd_reader.py
2. Create NCSDReader class with BinaryReader as dependency
3. Implement read_container() method that:
   - Reads magic at offset 0x100
   - Validates magic == b'NCSD'
   - Reads title ID at offset 0x108
   - Reads partition table starting at 0x120
   - Returns NCSDContainer model
4. Add _read_partitions() private method
5. Raise ValueError for invalid magic

Testing:
1. Create tests/unit/io/test_ncsd_reader.py
2. Use BytesIO for in-memory file (no real files)
3. Test valid NCSD structure
4. Test invalid magic bytes
5. Test partition parsing
6. Mock BinaryReader if needed
7. 100% coverage

Commands (from quick-reference.md):
```bash
mkdir -p dsconv/io tests/unit/io
pytest tests/unit/io/test_ncsd_reader.py -v
pytest tests/unit/io/test_ncsd_reader.py --cov=dsconv.io.ncsd_reader --cov-report=term-missing
black dsconv/io/ncsd_reader.py
ruff check dsconv/io/ncsd_reader.py
```

Reference the example in implementation-guide.md for the exact pattern.
```

---

## Tips for Writing Effective Prompts

### 1. Always Reference the Documentation
```
Read project-plans/refactoring-plan.md for [Task X.Y]
Follow patterns in project-plans/implementation-guide.md
Use commands from project-plans/quick-reference.md
```

### 2. Be Specific About Files
```
Create file: dsconv/models/ncch.py
Create tests: tests/unit/models/test_ncch.py
Update exports: dsconv/models/__init__.py
```

### 3. Include Acceptance Criteria
```
Acceptance criteria (from the plan):
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] 100% test coverage
```

### 4. Specify Dependencies
```
Dependencies:
- Phase 1 models must be complete
- Requires NCCHHeader from models/ncch.py
```

### 5. Include Quality Checks
```
Quality checks:
- Run: pytest tests/unit/... -v
- Coverage: pytest --cov=dsconv.module --cov-report=term-missing
- Format: black dsconv/module.py
- Lint: ruff check dsconv/module.py
```

### 6. Reference Examples
```
See the worked example in implementation-guide.md Section "Example: Implementing Task 1.1"
Follow the pattern in implementation-guide.md Section "Service Pattern"
```

---

## Recommended Task Order for Learning

Start with these tasks to build confidence:

1. **Task 1.1** (NCCH Header Model) - Has complete worked example
2. **Task 4.1** (Hash Validator) - Simple pure logic
3. **Task 1.2** (NCSD Container Model) - Similar to 1.1
4. **Task 3.1** (Binary Reader) - Simple utility
5. **Task 2.1** (AES Adapter) - Interface practice

---

## Common Patterns to Reference

When writing prompts, point to these sections:

- **Dataclass Pattern**: implementation-guide.md → "1. Dataclass Pattern for Models"
- **Service Pattern**: implementation-guide.md → "2. Service Pattern with Dependency Injection"
- **Interface Pattern**: implementation-guide.md → "3. Abstract Interface Pattern"
- **Reader/Writer**: implementation-guide.md → "4. Reader/Writer Pattern"
- **Testing**: implementation-guide.md → "Testing Patterns"
- **Commands**: quick-reference.md → "Command Cheat Sheet"

---

## Verification Checklist Template

Include this in every prompt:

```
Before marking complete, verify:
- [ ] Code follows patterns in implementation-guide.md
- [ ] All public methods have type hints
- [ ] All classes/methods have docstrings
- [ ] No global state introduced
- [ ] Dependencies are injected
- [ ] Unit tests achieve 100% coverage
- [ ] Tests follow AAA pattern
- [ ] All tests pass: pytest tests/ -v
- [ ] Linting passes: ruff check dsconv/
- [ ] Formatting applied: black dsconv/
- [ ] Module exports updated in __init__.py
```

---

## Example: Chaining Multiple Tasks

```
I need to implement Tasks 1.1, 1.2, and 1.3 from Phase 1 (Extract Domain Models).

These are the three domain model tasks that have no dependencies on each other.

For each task:
1. Read the task description in project-plans/refactoring-plan.md
2. Follow the dataclass pattern in project-plans/implementation-guide.md
3. Create model file in dsconv/models/
4. Create test file in tests/unit/models/
5. Achieve 100% coverage
6. Run all quality checks

Tasks:
- Task 1.1: NCCHHeader (see worked example in implementation-guide.md)
- Task 1.2: NCSDContainer and NCSDPartition
- Task 1.3: CIAHeader and CIAContent

Complete them in order: 1.1 first (has example), then 1.2, then 1.3.

After all three are complete:
- Update dsconv/models/__init__.py to export all models
- Run: pytest tests/unit/models/ -v --cov=dsconv.models
- Verify all three pass with 100% coverage
```

---

## Troubleshooting Prompts

If Copilot gets stuck, try these:

### "Not Following the Pattern"
```
Stop. Before continuing, please:
1. Read the code pattern in project-plans/implementation-guide.md Section "[Pattern Name]"
2. Show me the pattern you're using
3. Confirm it matches the guide

Then continue with the implementation.
```

### "Tests Not Comprehensive"
```
The tests need more coverage. Review project-plans/implementation-guide.md Section "Testing Patterns" and add:
1. Parametrized tests for multiple scenarios
2. Error case testing
3. Edge case testing

Current coverage is [X]%, need 100%.
```

### "Import Errors"
```
There's an import issue. Review project-plans/implementation-guide.md Section "Common Pitfalls - Circular Imports" and fix using TYPE_CHECKING pattern.
```

---

## Final Notes

1. **Always reference the three core documents**:
   - refactoring-plan.md for task details
   - implementation-guide.md for patterns
   - quick-reference.md for commands

2. **Start simple**: Begin with Phase 1 tasks (models) - they're the easiest

3. **Use the worked example**: Task 1.1 has a complete implementation in the guide

4. **Check dependencies**: Some tasks require others to be complete first

5. **Quality first**: 100% coverage and all checks passing before moving on

6. **Incremental progress**: Complete one task at a time, verify, then move to next

---

**Document Version**: 1.0  
**Created**: 2025-11-07  
**Purpose**: Help agents execute refactoring tasks using the comprehensive planning documents
