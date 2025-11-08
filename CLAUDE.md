# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# 3dsconv - Architecture Overview

**Related Documentation:**
- **[README.md](README.md)** - User-facing documentation and usage
- **[agents.md](agents.md)** - Complete project context for AI assistants (more detailed)
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development workflow
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - AI coding assistant guidance
- **[docs/adr/](docs/adr/)** - Architecture Decision Records

> This CLAUDE.md provides a high-level architecture overview. For comprehensive details, see agents.md.

## Quick Start for Claude Code

**Most common commands you'll need:**
```bash
# Setup
pip install -e ".[dev]"

# Before making changes
pytest                    # Ensure all tests pass

# Development cycle
# 1. Make changes to code
# 2. Run relevant tests
pytest tests/unit/models/  # If you modified models
# 3. Format and lint
black dsconv/ && ruff check --fix dsconv/
# 4. Run all tests
pytest

# Before committing
black dsconv/ && ruff check dsconv/ && mypy dsconv/ && pytest
```

**Key files to understand:**
1. [dsconv/models/](dsconv/models/) - Start here (clean, well-tested)
2. [dsconv/utils.py](dsconv/utils.py) - Helper functions
3. [dsconv/3dsconv.py](dsconv/3dsconv.py) - Main conversion logic (complex, being refactored)

## Project Purpose

**3dsconv** is a Python command-line tool that converts Nintendo 3DS game cartridge images (CCI/3DS format) into installable CIA archives. It handles the complex task of:

- Reading and parsing Nintendo 3DS binary file formats (NCSD containers and NCCH partitions)
- Detecting and handling various encryption schemes (decrypted, zerokey, and Original NCCH slot 0x2C)
- Extracting game executable, manual, and download play components
- Repackaging them into the CIA (CTR Importable Archive) format used for installation on 3DS systems

While modern tools like Decrypt9WIP and GodMode9 can now dump games directly to CIA format, 3dsconv remains useful for converting existing game dumps.

## High-Level Architecture

### Architecture Style
This project follows a **script-based architecture** with recent evolution toward a **modular, testable design**:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Entry Point                         │
│               (dsconv/__main__.py)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Main Conversion Script                        │
│              (dsconv/3dsconv.py - ~737 lines)               │
│  • Argument parsing                                          │
│  • Binary format reading/writing                            │
│  • Encryption key derivation                                │
│  • CCI → CIA conversion logic                               │
└─────────┬────────────────────────────────────┬──────────────┘
          │                                    │
          ▼                                    ▼
┌──────────────────────┐           ┌──────────────────────────┐
│   Utilities Module   │           │   Domain Models          │
│   (dsconv/utils.py)  │           │   (dsconv/models/)       │
│                      │           │                          │
│ • parse_args()       │           │ • NCSDContainer          │
│ • rol() crypto       │           │ • NCSDPartition          │
│ • prod.keys parser   │           │ • NCCHHeader             │
│ • Output helpers     │           │ • CIAHeader              │
│                      │           │ • CIAContent             │
│                      │           │ • EncryptionContext      │
└──────────────────────┘           │ • EncryptionType         │
                                   └──────────────────────────┘
                                              │
                                              ▼
                                   ┌──────────────────────────┐
                                   │   External Dependencies  │
                                   │                          │
                                   │ • pyaes (AES crypto)     │
                                   │ • prod.keys file         │
                                   │ • boot9.bin (optional)   │
                                   └──────────────────────────┘
```

> **Note:** Line numbers in this document are approximate and may shift as code evolves. Use them as general guidance.

### Architectural Evolution

The project is undergoing a modernization effort:

**Legacy Design (Original):**
- Single monolithic script (`3dsconv.py`)
- Global state management
- Difficult to test

**Current Design (Transitional):**
- **Domain Models** (`dsconv/models/`) - Clean, testable data structures
- **Utils Module** (`dsconv/utils.py`) - Extracted pure functions for testing
- **Main Script** (`dsconv/3dsconv.py`) - Still contains core logic, being gradually refactored
- **Comprehensive Testing** - Growing test suite with focus on model layer

**Target Design (Future):**
- Service layer for conversion logic
- Dependency injection for encryption services
- Complete separation of concerns

## Code Organization

### Directory Structure

```
3dsconv/
├── dsconv/                      # Main package (named to avoid Python digit-prefix issue)
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # CLI entry point (exec wrapper)
│   ├── 3dsconv.py              # Main conversion script (~737 lines)
│   ├── utils.py                # Testable utility functions
│   └── models/                 # Domain model layer (NEW)
│       ├── __init__.py         # Model exports
│       ├── ncsd.py             # NCSD container/partition models
│       ├── ncch.py             # NCCH header models
│       ├── cia.py              # CIA header/content models
│       └── encryption.py       # Encryption state models
│
├── tests/                      # Test suite (pytest-based)
│   ├── conftest.py            # Shared pytest fixtures
│   ├── README.md              # Test documentation
│   ├── unit/                  # Unit tests (fast, isolated)
│   │   ├── test_crypto_utils.py
│   │   ├── test_parse_args.py
│   │   ├── test_output.py
│   │   ├── test_prod_keys.py
│   │   └── models/            # Model tests (comprehensive)
│   │       ├── test_ncsd.py   # NCSD model tests
│   │       ├── test_ncch.py   # NCCH model tests
│   │       ├── test_cia.py    # CIA model tests
│   │       └── test_encryption.py  # Encryption model tests
│   ├── integration/           # Integration tests (planned)
│   └── e2e/                   # End-to-end tests (planned)
│
├── docs/                      # Documentation
│   ├── DEVELOPMENT.md         # Development workflow guide
│   └── adr/                   # Architecture Decision Records
│       ├── README.md          # ADR index
│       ├── 001-package-naming.md
│       ├── 002-modern-packaging.md
│       └── 003-test-automation-strategy.md
│
├── .github/                   # GitHub configuration
│   ├── workflows/             # CI/CD pipelines
│   ├── copilot-instructions.md  # AI assistant context
│   └── PULL_REQUEST_TEMPLATE.md
│
├── pyproject.toml            # Modern Python packaging config
├── setup.py                  # Legacy setup (kept for compatibility)
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── README.md                 # User documentation
├── CONTRIBUTING.md           # Contribution guidelines
└── agents.md                 # Complete project context for AI
```

### Why "dsconv" Package Name?

Python module names cannot start with digits, so while the project is called "3dsconv" and distributed as `3dsconv` on PyPI, the internal package is named `dsconv`. This is documented in [ADR-001](docs/adr/001-package-naming.md).

## Key Modules and Components

### 1. Domain Models Layer (`dsconv/models/`)

**Purpose:** Clean, testable representations of Nintendo 3DS binary file formats.

#### NCSD Models (`ncsd.py`)
- **`NCSDContainer`** - Represents a CCI file structure
  - Parses NCSD header at offset 0x100
  - Contains title ID and partition table (up to 8 partitions)
  - Methods: `get_game_partition()`, `get_partition_by_type()`

- **`NCSDPartition`** - Individual partition within a container
  - Stores offset/size in media units (0x200 bytes)
  - Type classification: game, manual, dlpchild, unknown
  - Properties: `offset_bytes`, `size_bytes`

#### NCCH Models (`ncch.py`)
- **`NCCHHeader`** - Nintendo Content Container header (0x200 bytes)
  - Parses content metadata, encryption flags, program ID
  - Properties: `is_encrypted`, `uses_zerokey`, `size_bytes`, `title_id`
  - Only includes fields needed for conversion (omits RomFS/logo regions)

#### CIA Models (`cia.py`)
- **`CIAHeader`** - CIA archive header (0x2020 bytes)
  - Defines sizes of cert chain, ticket, TMD, meta, content sections
  - Properties: `num_contents`, offset getters for each section
  - Helper: `_align_offset()` for 64-byte alignment

- **`CIAContent`** - Individual content record in CIA TMD
  - Describes content ID, index, size, hash
  - Properties: `is_encrypted`, `is_optional`, `is_shared`

#### Encryption Models (`encryption.py`)
- **`EncryptionType`** - Enum for encryption schemes
  - `DECRYPTED` - No encryption
  - `ZEROKEY` - Zero-key encryption
  - `ORIGINAL_NCCH` - Slot 0x2C encryption (requires key derivation)

- **`EncryptionContext`** - Encryption state container
  - Stores encryption type, derived keys, title ID
  - Properties: `needs_decryption`, `is_decrypted`, `is_zerokey`, `is_original_ncch`

#### Model Design Principles

All models follow these conventions:

**Immutability:**
- Use `@dataclass(frozen=True)` for immutable models where possible
- No setter methods, only computed properties

**Validation:**
- All validation in `__post_init__()` method
- Raise `ValueError` with descriptive messages for invalid data
- Check magic numbers, sizes, and structural invariants

**Parsing:**
- Use `@classmethod` `from_bytes(data: bytes)` factory pattern
- Handle struct unpacking centrally
- Document byte offsets and field sizes in docstrings

**Example Pattern:**
```python
from dataclasses import dataclass
import struct

@dataclass
class MyHeader:
    magic: bytes
    size: int

    @classmethod
    def from_bytes(cls, data: bytes) -> 'MyHeader':
        if len(data) < 8:
            raise ValueError("Insufficient data")
        magic, size = struct.unpack('<4sI', data[:8])
        return cls(magic=magic, size=size)

    def __post_init__(self):
        if self.magic != b'MGIC':
            raise ValueError(f"Invalid magic: {self.magic}")
        if self.size < 0:
            raise ValueError(f"Invalid size: {self.size}")
```

### 2. Utilities Module (`dsconv/utils.py`)

**Purpose:** Testable helper functions extracted from the main script.

- **`parse_args()`** - CLI argument parsing with argparse
- **`rol()`** - Bitwise rotation for key derivation
- **`error()`** - Error message formatting
- **`show_progress()`** - Progress bar display
- **`parse_prod_keys()`** - Parse prod.keys file format
- **`get_slot0x2c_key_from_prod_keys()`** - Extract encryption key

**Design Principle:** These are **pure or near-pure functions** that can be tested independently without executing the main conversion logic.

### 3. Main Conversion Script (`dsconv/3dsconv.py`)

**Purpose:** Orchestrates the entire conversion process.

**Key Sections:**

1. **Initialization (roughly lines 1-250)**
   - Import dependencies (pyaes for encryption)
   - Embedded data (retail cert chain, ticket/TMD templates)
   - Argument parsing and validation
   - Boot9/prod.keys loading
   - Dev certchain handling (for dev-unit conversions)

2. **Conversion Loop (roughly lines 250-737)**
   - File validation and preparation
   - NCSD header parsing
   - Encryption detection
   - Key derivation (using ARM9 bootROM or prod.keys)
   - Content extraction (game, manual, download play)
   - CIA structure assembly
   - Binary writing with progress tracking

**Critical Functions:**
- Encryption detection logic
- ExeFS/ExtHeader decryption
- CIA header construction
- Content chunk handling

### 4. Entry Point (`dsconv/__main__.py`)

**Purpose:** Enables both CLI (`3dsconv`) and module execution (`python -m dsconv`).

Uses `exec()` to run `3dsconv.py` because the filename starts with a digit and can't be imported normally in Python.

## Key Patterns and Conventions

### Design Patterns

1. **Factory Pattern**
   - All model classes use `from_bytes(data)` class methods for construction
   - Example: `NCSDContainer.from_bytes(header_data)`

2. **Dataclass Pattern**
   - Models use `@dataclass` for automatic `__init__`, `__repr__`, etc.
   - Validation in `__post_init__()` ensures invariants

3. **Property Pattern**
   - Computed properties for derived values
   - Example: `partition.offset_bytes` computes from media units

4. **Enum Pattern**
   - Type-safe enumerations for constants
   - Example: `EncryptionType.ORIGINAL_NCCH`

5. **Builder Pattern (Implicit)**
   - CIA construction assembles sections incrementally
   - Alignment and padding handled automatically

### Coding Conventions

**Style:**
- **Line length:** 100 characters (enforced by Black)
- **Indentation:** 4 spaces
- **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `snake_case` (not UPPER_CASE)
- **Type hints:** Encouraged for new code (using modern `|` union syntax)

**Binary Format Handling:**
- **Media units:** 0x200 (512) bytes - standard for 3DS formats
- **Struct usage:** `struct.unpack()` for binary parsing (little-endian `<` or big-endian `>`)
- **Magic values:** Validated on parse (e.g., `b'NCSD'`, `b'NCCH'`)
- **Alignment:** CIA sections align to 64-byte boundaries

**Error Handling:**
- **Validation on parse:** Models raise `ValueError` for invalid data
- **Early exit:** Main script exits with error messages on critical failures
- **User-friendly errors:** Specific messages for common issues (missing keys, bad files)

### Testing Philosophy

**Current Approach ([ADR-003](docs/adr/003-test-automation-strategy.md)):**

**Phase 1: Unit Tests (Completed)**
- Model layer: 100% coverage
- Utils functions: 100% coverage
- Fast, isolated tests using pytest

**Phase 2: Integration Tests (Planned)**
- Binary format validation
- Encryption detection
- Hash validation

**Phase 3: E2E Tests (Planned)**
- Full conversion workflows
- CLI option testing
- Error scenario testing

**Test Structure:**
- **AAA Pattern:** Arrange-Act-Assert
- **Parametrization:** `@pytest.mark.parametrize` for multiple cases
- **Fixtures:** Shared test data in `conftest.py`
- **Coverage:** `pytest-cov` with HTML reports

## Common Pitfalls

### Binary Format Issues
- **Off-by-one errors:** Media unit calculations are especially prone to this
- **Endianness:** Little-endian (`<`) for most fields, big-endian (`>`) for crypto operations
- **Alignment:** CIA sections must be 64-byte aligned, use `_align_offset()` helper

### Encryption Detection
- Check encryption flags correctly: `flags[7]` byte contains encryption bits
- Bit 2 (0x04): Decrypted
- Bit 0 (0x01): Zerokey
- Neither: Original NCCH (slot 0x2C)

### Global State
- The main script uses global variables (`args`, `keys_set`, etc.)
- When refactoring, be careful about state dependencies
- New code should avoid globals and use dependency injection

### Testing
- Always test with all three encryption types
- Use `tmp_path` fixture for file I/O in tests, never write to project directory
- Mock `pyaes` when testing encryption detection to avoid dependency

## Important Technical Concepts

### Nintendo 3DS File Formats

**CCI (CTR Cart Image):**
- Game cartridge dump format (`.3ds`, `.cci` files)
- Structure: NCSD container → NCCH partitions
- Contains: game executable, manual, download play child

**NCSD (Nintendo Content Storage Device):**
- Container format at file offset 0x100
- Header: magic, title ID, partition table (8 entries)
- Each partition: offset + size in media units

**NCCH (Nintendo Content Container Header):**
- Individual content header (0x200 bytes)
- Contains: program ID, encryption flags, ExeFS/ExtHeader offsets
- Three encryption states: decrypted, zerokey, original NCCH

**CIA (CTR Importable Archive):**
- Installable format for 3DS systems
- Structure: [Header][Cert][Ticket][TMD][Content][Meta]
- Header: 0x2020 bytes with section sizes
- All sections 64-byte aligned

### Encryption Handling

**Three Encryption Types:**

1. **Decrypted** (bit 2 set in flags[7])
   - No decryption needed
   - Direct copy to CIA

2. **Zerokey** (bit 0 set in flags[7])
   - Encrypted with all-zero key
   - Simple AES-CTR decryption

3. **Original NCCH** (slot 0x2C)
   - Requires key derivation from:
     - ARM9 bootROM (`boot9.bin`) OR
     - prod.keys file (`slot0x2CKey`)
   - Key derivation: bootROM extraction + ROL operations
   - Most complex case

**Key Derivation:**
```
bootROM → extract slot 0x2C keyX → apply ROL with title ID → derive normal key → decrypt
```

#### Encryption Keys: prod.keys vs boot9

**Search Order (when --prod-keys not specified):**
1. `./prod.keys` (current directory)
2. `~/.3ds/prod.keys`
3. Falls back to boot9 search if no prod.keys found

**Search Order for boot9 (when --boot9 not specified):**
1. `./boot9.bin` (full bootROM)
2. `./boot9_prot.bin` (protected bootROM)
3. `~/.3ds/boot9.bin`
4. `~/.3ds/boot9_prot.bin`

**Recommendation:** Use prod.keys method (simpler, more portable).

### Development Workflow

**Setup:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**Development Loop:**
```bash
# Testing
pytest                              # All tests with coverage
pytest tests/unit/                  # Unit tests only
pytest tests/unit/models/           # Model tests only
pytest -k "test_ncsd"               # Run specific test pattern
pytest -k "test_parse_args"         # Run tests matching pattern
pytest -v                           # Verbose output
pytest --cov-report=html            # Generate HTML coverage report

# Code Quality
black dsconv/                       # Format code
ruff check dsconv/                  # Check for issues
ruff check --fix dsconv/            # Auto-fix issues
mypy dsconv/                        # Type check

# Running Single Tests
pytest tests/unit/test_parse_args.py::test_parse_args_basic  # Specific test function
pytest tests/unit/models/test_ncsd.py  # Specific test file
```

**Viewing Test Coverage:**
```bash
pytest --cov=dsconv --cov-report=html  # Generate HTML coverage
open htmlcov/index.html                # macOS
xdg-open htmlcov/index.html            # Linux
start htmlcov/index.html               # Windows
```

**Running Tool:**
```bash
3dsconv game.3ds                            # Installed command
python -m dsconv game.3ds                   # Module execution
3dsconv --prod-keys prod.keys game.3ds     # With encryption keys
```

## CI/CD

Tests run automatically via GitHub Actions on:
- Every push to main branches
- Every pull request
- Python versions: 3.10, 3.11, 3.12, 3.13
- Operating systems: Linux, Windows, macOS

Check [.github/workflows/](.github/workflows/) for workflow configurations.

## Architecture Decision Records (ADRs)

Key architectural decisions documented in [docs/adr/](docs/adr/):

**[ADR-001: Package Naming](docs/adr/001-package-naming.md)**
- Decision: Use `dsconv` as package name
- Reason: Python modules can't start with digits
- Status: Accepted

**[ADR-002: Modern Python Packaging](docs/adr/002-modern-packaging.md)**
- Decision: Migrate to pyproject.toml
- Reason: Modern Python packaging standards
- Status: Accepted

**[ADR-003: Test Automation Strategy](docs/adr/003-test-automation-strategy.md)**
- Decision: Three-phase testing (unit → integration → e2e)
- Reason: Incremental quality improvement
- Status: Accepted

## Configuration Files

### Build/Package Configuration

**`pyproject.toml`** (Modern Python packaging)
- Project metadata: name, version, description, dependencies
- Build system: setuptools with wheel
- Tool configs: black, ruff, mypy, pytest
- Entry point: `3dsconv` console script → `dsconv.__main__:main`

**`setup.py`** (Legacy)
- Kept for backward compatibility
- Minimal configuration, pyproject.toml is authoritative

### Development Tools

**Black** (formatter)
- Line length: 100
- Target: Python 3.10-3.12

**Ruff** (linter)
- Select: E, W, F, I, B, C4, UP
- Ignore: E501 (line length - handled by Black)

**Mypy** (type checker)
- Python version: 3.10
- Basic checking mode
- Excludes: venv, context_portal, build, dist

**Pytest**
- Test paths: `tests/`
- Coverage: enabled with term-missing and HTML reports
- Verbose output by default

### Runtime Configuration

**`.python-version`**
- Specifies Python 3.10 (minimum)

**`prod.keys` (optional)**
- User-provided encryption keys
- Format: `key=hexvalue` (one per line)
- Required key: `slot0x2CKey`

## Dependencies

### Production Dependencies
- **pyaes >= 1.6.1** - Pure Python AES implementation for encryption/decryption

### Development Dependencies
- **pytest >= 7.0.0** - Testing framework
- **pytest-cov >= 4.0.0** - Code coverage
- **black >= 23.0.0** - Code formatter
- **ruff >= 0.1.0** - Linter
- **mypy >= 1.0.0** - Type checker

### External Files (User-Provided)
- **boot9.bin** - ARM9 bootROM for key derivation (optional)
- **prod.keys** - Encryption keys file (optional alternative to boot9)
- **certchain-dev.bin** - Dev certificate chain (only for `--dev-keys`)

## Special Considerations

### Package Naming Quirk
The package is named `dsconv` internally but distributed as `3dsconv`. This is because:
- Python modules can't start with digits
- PyPI allows digit-prefixed distribution names
- The `3dsconv` command works correctly via entry_points

### Binary Data Embedding
The script embeds base64-encoded, zlib-compressed binary data:
- **`certchain_retail`** - Retail CIA certificate chain (0xA00 bytes)
- **`ticket_tmd`** - Template ticket and TMD signature structures

This avoids needing external data files for standard conversions.

### Progress Tracking
The tool shows progress during conversion:
- File-level: "Processing X of Y files"
- Byte-level: Progress bar during content copy
- Uses `sys.stdout.write()` for real-time updates

### Backward Compatibility
The tool maintains compatibility with older usage patterns:
- Deprecated options (--gen-ncchinfo, --xorpads) print warnings
- Legacy boot9 search paths still supported
- Both setup.py and pyproject.toml maintained

## Getting Started as a New Developer

### Understanding the Conversion Flow

1. **Input Validation**
   - Check file exists and is readable
   - Verify NCSD magic at offset 0x100

2. **Format Parsing**
   - Parse NCSD container → get partitions
   - Parse NCCH headers → get encryption state
   - Extract title ID, program ID

3. **Encryption Handling**
   - Detect encryption type from flags
   - Load keys (boot9 or prod.keys)
   - Derive decryption keys if needed

4. **Content Extraction**
   - Read game partition (required)
   - Read manual partition (optional)
   - Read download play child (optional)
   - Decrypt on-the-fly if encrypted

5. **CIA Assembly**
   - Build CIA header with section sizes
   - Write cert chain (retail or dev)
   - Write ticket and TMD (from templates)
   - Write content chunks
   - Write meta section
   - Apply 64-byte alignment between sections

### Key Files to Read First

1. **[README.md](README.md)** - User perspective, features, usage
2. **This file (CLAUDE.md)** - Architecture overview
3. **[dsconv/models/](dsconv/models/)** - Start with clean, well-tested models
4. **[tests/unit/models/](tests/unit/models/)** - See how models are used
5. **[dsconv/utils.py](dsconv/utils.py)** - Utility functions with tests
6. **[dsconv/3dsconv.py](dsconv/3dsconv.py)** - Main logic (read incrementally)

### Testing Your Changes

Always add tests for new code:
- Models: Add to `tests/unit/models/`
- Utils: Add to `tests/unit/`
- Integration: Add to `tests/integration/` (when available)

Run tests frequently during development:
```bash
pytest tests/unit/  # Fast unit tests
pytest              # Full test suite
```

### Common Contribution Areas

1. **Model layer expansion** - Add more format parsing
2. **Service layer extraction** - Move logic from main script to services
3. **Integration tests** - Test with real binary data
4. **Error handling improvements** - More specific error messages
5. **Performance optimizations** - Profile and optimize hot paths
6. **Documentation** - Code comments, docstrings, user guides

## Resources

**Documentation:**
- [README.md](README.md) - User documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development workflow
- [docs/adr/](docs/adr/) - Architecture decisions
- [agents.md](agents.md) - Complete project context for AI assistants

**External References:**
- [3dbrew.org](https://www.3dbrew.org/) - Nintendo 3DS technical documentation
- [NCSD Format](https://www.3dbrew.org/wiki/NCSD)
- [NCCH Format](https://www.3dbrew.org/wiki/NCCH)
- [CIA Format](https://www.3dbrew.org/wiki/CIA)
- [Title Metadata](https://www.3dbrew.org/wiki/Title_metadata)

**Community:**
- GitHub Issues - Bug reports, feature requests
- GitHub Discussions - Questions and help

---

**Last Updated:** 2025-11-08
**Project Version:** 4.21
**Python Version:** 3.10+
