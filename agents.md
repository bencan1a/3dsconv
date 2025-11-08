# Agent Context: 3dsconv Project

## Project Overview

**3dsconv** is a Python 3 command-line tool that converts Nintendo 3DS CTR Cart Image files (CCI, ".cci", ".3ds") to the CTR Importable Archive format (CIA). This tool is useful for working with existing game dumps, though modern tools like Decrypt9WIP and GodMode9 can now dump game cards directly to CIA format.

**Version:** 4.21
**License:** MIT
**Repository:** https://github.com/ihaveamac/3dsconv
**Author:** Ian (ihaveamac)

## Project Structure

```
3dsconv/
├── dsconv/                  # Main package (renamed from "3dsconv" for Python compatibility)
│   ├── 3dsconv.py          # Main conversion script (676 lines)
│   ├── __main__.py         # Entry point for CLI and module execution
│   └── __init__.py         # Package initialization
├── tests/                   # Test suite
│   ├── unit/               # Unit tests (52+ tests)
│   ├── integration/        # Integration tests
│   ├── e2e/                # End-to-end tests (planned)
│   ├── fixtures/           # Test data files
│   └── conftest.py         # Shared pytest fixtures
├── examples/                # Example and test files
│   ├── test-ccis/          # Test CCI/CIA files for conversion testing
│   │   ├── README.md       # Detailed documentation of test files
│   │   ├── test-01-nocrypt.{cci,cia}        # No encryption
│   │   ├── test-02-ncch-original.{cci,cia}  # NCCH slot 0x2C
│   │   ├── test-03-ncch-7x.{cci,cia}        # NCCH slot 0x25
│   │   ├── test-04-fixed-key.{cci,cia}      # Fixed key encryption
│   │   ├── test-05-compressed.{cci,cia}     # LZ77 compressed ExeFS
│   │   └── test-06-new3ds.{cci,cia}         # New3DS optimized
│   └── rsf templates/      # RSF template files for test file generation
│       ├── basic-nocrypt.rsf
│       ├── basic-ncch-original.rsf
│       ├── basic-ncch-7x.rsf
│       ├── basic-fixed-key.rsf
│       ├── basic-compressed.rsf
│       └── basic-new3ds.rsf
├── context_portal/         # Context management system for AI agents
│   ├── alembic/           # Database migrations
│   │   ├── versions/
│   │   │   └── 2025_06_17_initial_schema.py
│   │   └── env.py
│   ├── alembic.ini        # Alembic configuration
│   ├── context.db         # SQLite database for context tracking
│   └── logs/              # Log files
├── venv/                   # Python virtual environment (gitignored)
├── pyproject.toml          # Modern Python project configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.py               # Legacy setup file (kept for compatibility)
├── .python-version        # Python version specification (3.10)
├── README.md              # User documentation
├── LICENSE.md             # MIT License
└── .gitignore             # Git ignore patterns
```

**Note on Package Naming:** The package directory is named `dsconv` (not `3dsconv`) because Python module names cannot start with digits. The distribution name remains `3dsconv` for PyPI compatibility.

## Core Functionality

### Main Script: [dsconv/3dsconv.py](dsconv/3dsconv.py)

The main conversion logic handles:
- **File format validation**: Checks for NCSD and NCCH magic values
- **Encryption detection**: Supports decrypted, Original NCCH (slot 0x2C), and zerokey encryption
- **Decryption**: Uses pyaes library and ARM9 bootROM for decryption
- **Conversion**: Extracts and repackages components into CIA format
- **Components handled**:
  - Game Executable CXI
  - Manual CFA
  - Download Play child container CFA

### Key Technical Details

#### Dependencies
- **Python 3.10+**: Core runtime (tested with 3.10, 3.11, 3.12, 3.13)
- **pyaes >= 1.6.1**: AES encryption/decryption for handling encrypted ROMs
- **ARM9 bootROM**: Required for decrypting Original NCCH encrypted files
  - File: `boot9.bin` (full) or `boot9_prot.bin` (protected)
  - Locations checked: `--boot9` arg, current dir, `~/.3ds/`
  - SHA256 (boot9): `2f88744feed717856386400a44bba4b9ca62e76a32c715d4f309c399bf28166f`
  - SHA256 (boot9_prot): `7331f7edece3dd33f2ab4bd0b3a5d607229fd19212c10b734cedcaf78c1a7b98`

#### Development Dependencies
- **pytest >= 7.0.0**: Testing framework
- **pytest-cov >= 4.0.0**: Code coverage reporting
- **black >= 23.0.0**: Code formatter (line length: 100)
- **ruff >= 0.1.0**: Fast Python linter
- **mypy >= 1.0.0**: Static type checker

#### Command-Line Interface ([dsconv/3dsconv.py:24-104](dsconv/3dsconv.py#L24-L104))

The tool uses argparse for CLI with these options:
- `-o, --output`: Output directory (default: current directory)
- `-b, --boot9`: Path to ARM9 bootROM
- `--overwrite`: Overwrite existing files
- `--ignore-bad-hashes`: Convert despite invalid hashes
- `--ignore-encryption`: Assume ROM is unencrypted
- `-v, --verbose`: Print detailed information
- `--dev-keys`: Use developer-unit keys
- Positional: `game [game ...]` - Input CCI files

#### Constants and Configuration ([dsconv/3dsconv.py:166-168](dsconv/3dsconv.py#L166-L168))
```python
mu = 0x200              # Media unit size
read_size = 0x800000    # Read buffer size (8MB)
zerokey = bytes(0x10)   # Zero key for zerokey encryption
```

#### Embedded Data
The script contains base64-encoded, zlib-compressed binary data for:
- Retail CIA certificate chain ([dsconv/3dsconv.py:123-158](dsconv/3dsconv.py#L123-L158))
- Ticket and TMD templates ([dsconv/3dsconv.py:162-164](dsconv/3dsconv.py#L162-L164))

### Conversion Process Flow

1. **Parse arguments and validate environment** ([dsconv/3dsconv.py:117-312](dsconv/3dsconv.py#L117-L312))
   - Check for pyaes availability
   - Load ARM9 bootROM if needed
   - Load dev certchain if `--dev-keys` used
   - Validate input files and output paths

2. **For each input file** ([dsconv/3dsconv.py:314-672](dsconv/3dsconv.py#L314-L672)):
   - Validate NCSD magic
   - Read title ID and partition sizes
   - Validate NCCH magic
   - Detect encryption type
   - Decrypt and verify ExtHeader
   - Patch ExtHeader for SD title
   - Extract icon from ExeFS
   - Build CIA structure:
     - Write CIA header
     - Write certificate chain
     - Write ticket and TMD
     - Write Game Executable CXI
     - Write Manual CFA (if present)
     - Write Download Play child CFA (if present)
     - Update content hashes
     - Write Meta region

3. **Output**: CIA file ready for installation on 3DS

## Context Portal System

The [context_portal/](context_portal/) directory contains a sophisticated context management system for AI agents working on this project. It uses SQLite with Alembic migrations.

### Database Schema

**Tables:**
- `active_context`: Current session context
- `active_context_history`: Historical context snapshots
- `product_context`: Product-level information
- `product_context_history`: Product context history
- `decisions`: Architectural and implementation decisions (with FTS5 full-text search)
- `system_patterns`: Reusable patterns and practices
- `progress_entries`: Task progress tracking (hierarchical with parent_id)
- `context_links`: Relationships between context items
- `custom_data`: Key-value storage by category (with FTS5)

### FTS5 Full-Text Search
The database includes SQLite FTS5 virtual tables for:
- `decisions_fts`: Full-text search on decisions
- `custom_data_fts`: Full-text search on custom data

These are kept in sync with triggers on the main tables.

## Installation

### Modern Setup (Recommended)

#### 1. Set up virtual environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install package
```bash
# For users (production)
pip install -e .

# For developers (with dev tools)
pip install -e ".[dev]"
```

#### 3. Run the tool
```bash
# As a command
3dsconv [options] game.3ds

# As a module
python -m dsconv [options] game.3ds

# Direct script execution (backward compatible)
python dsconv/3dsconv.py [options] game.3ds
```

### Legacy Setup (Old Method)

```bash
# Using old setup.py
python3 setup.py install

# Or as a script without installation
python3 dsconv/3dsconv.py [options] game.3ds
```

### Requirements Files

The project now includes modern requirements files:
- `requirements.txt` - Production dependencies (pyaes)
- `requirements-dev.txt` - Development tools (pytest, black, ruff, mypy)

Install requirements directly:
```bash
pip install -r requirements.txt           # Production only
pip install -r requirements-dev.txt       # Includes dev tools
```

## Code Conventions & Style

### Python Style
- **Python Version**: 3.10+ (tested with 3.10, 3.11, 3.12, 3.13)
- **Indentation**: 4 spaces
- **Line length**: 100 characters (configured in black and ruff)
- **Naming**:
  - Functions: `snake_case` (e.g., `parse_args`, `show_progress`)
  - Variables: `snake_case` (e.g., `game_cxi_offset`, `title_id_hex`)
  - Constants: `snake_case` (e.g., `read_size`, `mu`)
- **Comments**: Inline comments for complex logic, especially cryptographic operations
- **Type Hints**: Present in some functions (e.g., `parse_args() -> argparse.Namespace`)

### Development Tools

The project uses modern Python development tools:

- **black**: Code formatter (line-length: 100, target: py310+)
  ```bash
  black dsconv/
  ```

- **ruff**: Fast Python linter (replaces flake8, isort, etc.)
  ```bash
  ruff check dsconv/
  ruff check --fix dsconv/  # Auto-fix issues
  ```

- **mypy**: Static type checker
  ```bash
  mypy dsconv/
  ```

- **pytest**: Testing framework
  ```bash
  pytest                    # Run tests
  pytest --cov=dsconv      # With coverage
  ```

All tool configurations are in [pyproject.toml](pyproject.toml).

### Global State
The script uses some module-level global variables:
- `args`: Parsed command-line arguments
- `pyaes_found`: Boolean for pyaes availability
- `version`: Current version string
- `total_files`, `processed_files`: File processing counters
- `certchain_dev`: Developer certificate chain
- `keys_set`, `orig_ncch_key`: Encryption keys

### Error Handling
- Uses `error()` function ([dsconv/3dsconv.py:192-193](dsconv/3dsconv.py#L192-L193)) to print errors
- `continue` on file-level errors to process remaining files
- `sys.exit(1)` for fatal errors

## Working with This Codebase

### When Adding Features
1. **Read the README first**: Understand the tool's purpose and limitations
2. **Check the conversion flow**: Most changes will affect the file processing loop
3. **Test with different encryption types**: Decrypted, Original NCCH, zerokey
4. **Verify hash calculations**: The tool validates hashes throughout the process
5. **Consider backward compatibility**: Many users rely on this tool

### When Fixing Bugs
1. **Check hash validation logic**: Many issues relate to encryption detection
2. **Verify file offsets**: Off-by-one errors are common with binary formats
3. **Test with real CCI files**: The format is complex with edge cases
4. **Check encryption paths**: Different code paths for encrypted vs decrypted

### When Refactoring
1. **The main loop is long**: Consider extracting functions for clarity
2. **Global state**: Could be encapsulated in a class
3. **Error handling**: Could be more consistent
4. **Type hints**: Could be added for better IDE support (some exist in `parse_args`)

### Testing Considerations
- **Automated tests**: The repository includes a comprehensive pytest test suite in `tests/`
  - Unit tests: 52+ tests with 100% coverage on utils.py
  - Integration tests: Format validation, encryption, hash verification
  - End-to-end tests: Full conversion workflows (planned)
- **Test CCI/CIA files**: Available in `examples/test-ccis/`
  - 6 test CCI files + 6 matching canonical CIA files
  - Cover all encryption scenarios: no encryption, NCCH original (0x2C), NCCH 7.x (0x25), fixed key, compressed ExeFS, New3DS
  - Small size (~93KB each) for fast testing
  - Detailed documentation in [examples/test-ccis/README.md](examples/test-ccis/README.md)
- **RSF templates**: Available in `examples/rsf templates/`
  - 6 RSF files corresponding to each test scenario
  - Used to regenerate test files with makerom if needed
  - Files: basic-nocrypt.rsf, basic-ncch-original.rsf, basic-ncch-7x.rsf, basic-fixed-key.rsf, basic-compressed.rsf, basic-new3ds.rsf
- Manual testing with user-provided files (ROMs) should also be performed
- Test with: games with/without manual, with/without DLP child

## Important Notes for AI Agents

### Security & Legal Considerations
- This tool works with copyrighted Nintendo 3DS content
- The ARM9 bootROM is proprietary Nintendo code
- Users must own the games they convert
- This is for personal backup/archival purposes only

### Encryption Complexity
- Three encryption types: decrypted, Original NCCH, zerokey
- Keys derived from ARM9 bootROM using complex bit rotation
- Counter mode (CTR) encryption with title ID-based IVs
- Different counters for different sections (ExtHeader, ExeFS, etc.)

### Binary Format Handling
- Uses struct module for binary parsing
- Little-endian format for most fields (`<I`, `<III`, etc.)
- Big-endian for some crypto operations (`>I`, `>III`)
- Media units (0x200 bytes) for size calculations
- Hash calculations throughout (SHA-256, MD5)

### Progress Reporting
- Uses `show_progress()` ([dsconv/3dsconv.py:197-203](dsconv/3dsconv.py#L197-L203)) for large operations
- Verbose output controlled by `args.verbose`
- Helper functions `print_v()` and `v()` for conditional output

### File Processing
- Reads in chunks (`read_size = 0x800000`)
- Seeks to specific offsets frequently
- Hash calculations updated incrementally
- Multiple writes to same CIA file at different offsets

## Common Tasks

### Adding a New Command-Line Option
1. Add to `parse_args()` function
2. Use `args.your_option` in processing loop
3. Update README.md documentation
4. Consider backward compatibility

### Changing Encryption Handling
1. Find encryption detection at [dsconv/3dsconv.py:363-368](dsconv/3dsconv.py#L363-L368)
2. Key derivation at [dsconv/3dsconv.py:379-393](dsconv/3dsconv.py#L379-L393)
3. Decryption of ExtHeader at [dsconv/3dsconv.py:407-412](dsconv/3dsconv.py#L407-L412)
4. Decryption of ExeFS at [dsconv/3dsconv.py:464-468](dsconv/3dsconv.py#L464-L468)
5. Test thoroughly - crypto bugs are hard to debug

### Modifying CIA Structure
1. Find CIA header creation at [dsconv/3dsconv.py:511-547](dsconv/3dsconv.py#L511-L547)
2. Content writing at [dsconv/3dsconv.py:566-646](dsconv/3dsconv.py#L566-L646)
3. Hash updates at [dsconv/3dsconv.py:649-663](dsconv/3dsconv.py#L649-L663)
4. Meta region at [dsconv/3dsconv.py:666-670](dsconv/3dsconv.py#L666-L670)
5. Consult Nintendo 3DS documentation for format details

## Git Information

**Current Branch:** master
**Main Branch:** master
**Status:** Clean working directory

**Recent Commits:**
- `50a30d2` - Merge pull request #33 from wizerdwolf/use-argparse
- `552f434` - Use argparse for argument parsing
- `bde8c8f` - correctly use global
- `6f97664` - Merge pull request #22 from TanyaEleventhGoddess/master
- `9e81835` - use global

Recent work has focused on modernizing argument parsing using argparse.

## Resources

- **3DS Format Documentation**: Search for "3DBrew" wiki for detailed format specs
- **pyaes Documentation**: https://github.com/ricmoo/pyaes
- **3DS Guide**: https://3ds.guide/ (for obtaining boot9)
- **Decrypt9WIP**: https://github.com/d0k3/Decrypt9WIP
- **GodMode9**: https://github.com/d0k3/GodMode9

## Pytest Best Practices & Anti-Patterns

### Critical Best Practices

**Fixture Management**
- Use `conftest.py` for shared fixtures across test files
- Scope fixtures appropriately: `function` (default), `class`, `module`, `session`
- Use `tmp_path` (function-scoped) or `tmp_path_factory` (session-scoped) for temp files, NOT manual cleanup
- Name fixtures descriptively: `sample_cci_file`, `mock_boot9`, not `fixture1`

**Test Structure**
- Follow Arrange-Act-Assert (AAA) pattern religiously
- One logical assertion per test (multiple asserts OK if testing same concept)
- Name tests: `test_<function>_<scenario>_<expected>` (e.g., `test_parse_args_no_args_shows_help`)
- Keep tests under 20 lines; extract setup to fixtures if longer

**Mocking & Patching**
- Mock at the boundary: patch where imported, not where defined
- Use `mocker.patch()` (pytest-mock) over `unittest.mock.patch` for auto-cleanup
- Mock file I/O for unit tests; use real files for integration tests with `tmp_path`
- Verify mock calls with `assert_called_once_with()`, not `assert called`

**Parametrization**
- Use `@pytest.mark.parametrize` for multiple input scenarios
- Name parameters clearly: `@pytest.mark.parametrize("input_val,expected", [...])`
- Test edge cases: empty, None, zero, negative, max values, malformed input

**Binary & Crypto Testing**
- Use `bytes.fromhex()` for readable binary test data
- Store test binary files in `tests/fixtures/` directory
- Test crypto with known good input/output pairs from reference implementations
- Verify hash calculations against pre-computed values

### Critical Anti-Patterns (NEVER DO)

**DON'T: Use global state or modify module globals in tests**
```python
# WRONG
def test_conversion():
    global args
    args = parse_args()  # Pollutes global state
```
Fix: Mock or pass as parameter

**DON'T: Test implementation details**
```python
# WRONG
def test_internal_hash_var():
    assert obj._internal_hash == "abc"  # Tests private implementation
```
Fix: Test public behavior and outputs

**DON'T: Use `assert True` or empty assertions**
```python
# WRONG
def test_parse():
    parse_args()
    assert True  # Meaningless
```
Fix: Assert specific behavior or use `with pytest.raises()` for error tests

**DON'T: Ignore test failures with bare `except` or `pass`**
```python
# WRONG
def test_convert():
    try:
        convert()
    except:
        pass  # Silently fails
```
Fix: Let exceptions propagate or use `pytest.raises(SpecificException)`

**DON'T: Share state between tests**
```python
# WRONG
class TestConversion:
    def setup_class(cls):
        cls.output_file = "test.cia"  # Shared across all tests
```
Fix: Use `setup_method()` or function-scoped fixtures

**DON'T: Hardcode paths or use current directory**
```python
# WRONG
def test_output():
    with open("output.txt", "w") as f:  # Pollutes project dir
```
Fix: Use `tmp_path` fixture

**DON'T: Create tests that depend on execution order**
```python
# WRONG - test_b depends on test_a running first
def test_a_create_file():
    Path("data.txt").write_text("test")

def test_b_read_file():
    assert Path("data.txt").read_text() == "test"
```
Fix: Make tests independent with fixtures

### Project-Specific Testing Guidelines

**For 3dsconv Binary Format Tests**
- Create minimal valid CCI/NCCH test files (< 1KB) with proper magic values
- Test each encryption path separately: decrypted, Original NCCH, zerokey
- Use `monkeypatch` to simulate missing boot9/pyaes scenarios
- Mock `struct.unpack()` returns for boundary testing without large files

**For CLI Argument Tests**
- Capture stdout/stderr with `capsys` fixture
- Test `sys.exit()` calls with `pytest.raises(SystemExit)`
- Use `monkeypatch.setattr("sys.argv", [...])` for argv testing
- Test both short (`-v`) and long (`--verbose`) option forms

**For File I/O Heavy Code**
- Integration tests: Use `tmp_path` with real but minimal test files
- Unit tests: Mock `open()`, `seek()`, `read()`, `write()` calls
- Test chunk reading with controlled `read_size` values
- Verify file handles are closed (use context managers)

**Coverage Requirements**
- Aim for 80%+ line coverage, 70%+ branch coverage
- Focus on critical paths: encryption, hash validation, CIA structure
- Don't test embedded data (certchain, ticket_tmd constants)
- Skip coverage for error messages and verbose output formatting

## Quick Reference

### File Extensions
- `.3ds`, `.cci` - CTR Cart Image (input)
- `.cia` - CTR Importable Archive (output)
- `.cxi` - CTR eXecutable Image (game executable)
- `.cfa` - CTR File Archive (manual, DLP child)
- `.bin` - Various binary files (boot9, certchain, etc.)

### Magic Values
- `NCSD` at 0x100 - Cart Image header
- `NCCH` at game_cxi_offset + 0x100 - NCCH header

### Important Hashes
All hashes verified during conversion:
- ExtHeader SHA-256
- Content chunk SHA-256 (for each CXI/CFA)
- Content info records SHA-256
- Key Y and Normal Key verification via MD5

---

**Last Updated:** 2025-11-07
**For:** AI Coding Agents (Claude Code, GitHub Copilot, Cursor, etc.)
