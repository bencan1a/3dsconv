# GitHub Copilot Instructions for 3dsconv

## Project Overview

**3dsconv** is a Python 3 command-line tool that converts Nintendo 3DS CTR Cart Image files (CCI, ".cci", ".3ds") to the CTR Importable Archive format (CIA).

- **Version:** 4.21
- **Language:** Python 3.10+
- **License:** MIT
- **Main Module:** `dsconv/3dsconv.py` (676 lines)
- **Package Name:** `dsconv` (distribution name: `3dsconv`)

## Quick Start for Copilot

### Essential Context Files
1. **[agents.md](../agents.md)** - Complete project context and architecture
2. **[README.md](../README.md)** - User documentation and usage
3. **[Test-Automation-Plan.md](../Test-Automation-Plan.md)** - Testing strategy and roadmap
4. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Development guidelines

### Key Commands
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Development
black dsconv/              # Format code
ruff check --fix dsconv/   # Lint and fix
mypy dsconv/               # Type check
pytest                     # Run tests

# Run tool
3dsconv [options] game.3ds
python -m dsconv [options] game.3ds
```

## Code Structure & Critical Paths

### Package Layout
```
dsconv/
├── __init__.py           # Package initialization
├── __main__.py          # CLI entry point
├── 3dsconv.py           # Main conversion logic (676 lines)
└── utils.py             # Testable utility functions
```

### Critical Functions & Line Numbers

**Argument Parsing (3dsconv.py:24-104)**
- `parse_args()` - CLI argument parsing using argparse
- Environment variables: `BOOT9_PATH`

**Encryption Handling (3dsconv.py:117-312)**
- Load ARM9 bootROM (lines 261-298)
- Load dev certchain (lines 215-230)
- Key derivation using `rol()` function (lines 379-393)

**Main Conversion Loop (3dsconv.py:314-672)**
- NCSD validation (line ~325)
- Encryption detection (lines 363-368)
- ExtHeader decryption (lines 407-412)
- ExeFS decryption (lines 464-468)
- CIA structure building (lines 511-670)

### Constants & Configuration
```python
mu = 0x200              # Media unit size
read_size = 0x800000    # Read buffer size (8MB)
zerokey = bytes(0x10)   # Zero key for zerokey encryption
```

## Coding Conventions

### Python Style
- **Python Version:** 3.10+ (tested with 3.10-3.13)
- **Line Length:** 100 characters
- **Indentation:** 4 spaces
- **Naming:**
  - Functions/Variables: `snake_case` (e.g., `parse_args`, `title_id_hex`)
  - Constants: `snake_case` (e.g., `read_size`, `mu`)
- **Type Hints:** Encouraged for new code (existing: `parse_args() -> argparse.Namespace`)
- **Formatter:** black (configured in pyproject.toml)
- **Linter:** ruff (configured in pyproject.toml)

### Code Patterns to Follow

#### 1. Binary Format Parsing
```python
# Use struct module with little-endian format
title_id = struct.unpack('<Q', f.read(8))[0]
partition_sizes = struct.unpack('<IIIIIIII', f.read(0x20))
```

#### 2. Progress Reporting
```python
# For long operations, use show_progress
show_progress(current, total, "Copying Game Executable CXI")
```

#### 3. Verbose Output
```python
# Use print_v() or v() for verbose messages
print_v(f"Title ID: {title_id_hex}")
content_size = 0x20 + len(v('\\nBuilding CIA...'))
```

#### 4. Error Handling
```python
# Use error() for error messages, continue for file-level errors
error(f"Failed to process {filename}: {reason}")
continue  # Process next file
```

### Global State (Important)
The script uses module-level globals:
- `args` - Parsed command-line arguments
- `pyaes_found` - Boolean for pyaes availability
- `keys_set`, `orig_ncch_key` - Encryption keys
- `total_files`, `processed_files` - Counters

**When modifying:** Be careful with global state. Consider refactoring to class-based approach for new features.

## Testing Guidelines

### Test Structure
```
tests/
├── unit/                # Pure function tests
├── integration/         # Format validation, encryption tests
├── e2e/                # Full workflow tests
├── fixtures/           # Test data files
└── conftest.py         # Shared fixtures
```

### Writing Tests
```python
# Follow AAA pattern: Arrange, Act, Assert
def test_rol_basic_rotation():
    """Test basic rotate-left operation."""
    # Arrange
    value = 0b10110001
    bits = 3
    
    # Act
    result = rol(value, bits)
    
    # Assert
    assert result == 0b10001101
```

### Test Coverage Goals
- **Phase 1 (Completed):** 52 unit tests, 100% coverage on utils.py
- **Phase 2 (In Progress):** Integration tests for validation, encryption, hashes
- **Phase 3 (Planned):** E2E tests for complete workflows
- **Target:** 80% line coverage, 70% branch coverage

### Running Tests
```bash
pytest tests/                    # All tests
pytest tests/unit/              # Unit tests only
pytest -k "test_parse_args"     # Specific test pattern
pytest --cov=dsconv             # With coverage
```

## Common Tasks & Solutions

### Adding a New CLI Option

1. **Update parse_args() in dsconv/utils.py**
   ```python
   parser.add_argument('--new-option', action='store_true',
                      help='Description of new option')
   ```

2. **Use in conversion loop (dsconv/3dsconv.py)**
   ```python
   if args.new_option:
       # Implementation
   ```

3. **Add tests in tests/unit/test_parse_args.py**
   ```python
   def test_parse_args_new_option():
       args = parse_args(['--new-option', 'game.3ds'])
       assert args.new_option is True
   ```

4. **Update README.md** with documentation

### Modifying Encryption Handling

⚠️ **Crypto is Complex** - Test thoroughly with all encryption types:
- Decrypted (bitmask 0x04)
- Zerokey (bitmask 0x01)
- Original NCCH (bitmask 0x00)

**Key locations:**
- Encryption detection: lines 363-368
- Key derivation: lines 379-393
- ExtHeader decrypt: lines 407-412
- ExeFS decrypt: lines 464-468

### Working with Binary Formats

**Nintendo 3DS file structure:**
- **Magic values:** `NCSD` at 0x100, `NCCH` at game_cxi_offset + 0x100
- **Sizes:** Media units (0x200 bytes)
- **Endianness:** Little-endian for most fields, big-endian for crypto
- **Hashes:** SHA-256 throughout, verified during conversion

**Resources:**
- 3DBrew wiki for format specs
- Existing code comments for field offsets

### Refactoring Recommendations

Current code is monolithic. Consider:

1. **Extract pure functions** from main loop
   ```python
   def extract_title_id(f: BinaryIO) -> int:
       """Extract title ID from NCSD header."""
       f.seek(0x108)
       return struct.unpack('<Q', f.read(8))[0]
   ```

2. **Create converter class**
   ```python
   class CCIConverter:
       def __init__(self, args: argparse.Namespace):
           self.args = args
           # Initialize state
       
       def convert(self, input_path: str) -> str:
           # Conversion logic
   ```

3. **Separate I/O from logic**
   ```python
   class CCIReader:
       def read_partition_table(self) -> List[int]: ...
   
   class CIAWriter:
       def write_header(self, header_data: bytes): ...
   ```

## Security & Legal Considerations

⚠️ **Important:**
- Works with copyrighted Nintendo 3DS content
- ARM9 bootROM is proprietary Nintendo code
- Users must own games they convert
- Personal backup/archival purposes only

**When adding features:**
- Don't bypass copy protection for unauthorized use
- Respect Nintendo's intellectual property
- Follow existing security patterns

## Dependency Management

### Production Dependencies
- **pyaes >= 1.6.1:** AES encryption/decryption

### Development Dependencies
- **pytest >= 7.0.0:** Testing framework
- **pytest-cov >= 4.0.0:** Coverage reporting
- **black >= 23.0.0:** Code formatter
- **ruff >= 0.1.0:** Linter
- **mypy >= 1.0.0:** Type checker

### Adding New Dependencies
1. Check security vulnerabilities first
2. Update pyproject.toml
3. Test with multiple Python versions (3.10-3.13)
4. Document in README.md if user-facing

## Performance Considerations

- **Large file handling:** Read in chunks (read_size = 8MB)
- **Hash calculations:** Updated incrementally, not all at once
- **Encryption:** Counter mode with minimal overhead
- **Progress reporting:** Only for operations > 1MB

## Debugging Tips

### Common Issues

**"NCSD magic not found"**
- File is not a valid CCI
- Check file offset 0x100

**"pyaes not found"**
- Install with `pip install pyaes`
- Check encryption detection logic

**Hash validation fails**
- Check encryption detection (lines 363-368)
- Verify correct key derivation (lines 379-393)
- Use `--ignore-bad-hashes` for testing only

### Debug Output
```bash
# Enable verbose mode
3dsconv -v game.3ds

# Check what's happening
python -m pdb -m dsconv game.3ds
```

## Copilot-Specific Tips

### When Writing Code
- **Reference line numbers:** Use `dsconv/3dsconv.py:123` format
- **Check existing patterns:** Look at similar code first
- **Use type hints:** Add for new functions
- **Follow conventions:** Match existing style exactly

### When Suggesting Changes
- **Minimal changes:** Only modify what's necessary
- **Backward compatible:** Don't break existing behavior
- **Test coverage:** Add tests for new code
- **Documentation:** Update README.md if user-facing

### When Reviewing Code
- **Check binary offsets:** Off-by-one errors are common
- **Verify encryption paths:** Test all three types
- **Validate hashes:** Ensure calculations match format
- **Test edge cases:** Missing partitions, corrupt files

## Resources & References

### Documentation
- **3DBrew Wiki:** Nintendo 3DS format specifications
- **3DS Guide:** https://3ds.guide/ (obtaining boot9)
- **pyaes:** https://github.com/ricmoo/pyaes

### Related Tools
- **Decrypt9WIP:** https://github.com/d0k3/Decrypt9WIP
- **GodMode9:** https://github.com/d0k3/GodMode9

### File Extensions Quick Reference
- `.3ds`, `.cci` - CTR Cart Image (input)
- `.cia` - CTR Importable Archive (output)
- `.cxi` - CTR eXecutable Image (game executable)
- `.cfa` - CTR File Archive (manual, DLP child)
- `.bin` - Binary files (boot9, certchain, etc.)

## Architecture Decisions

Refer to [agents.md](../agents.md) for complete architectural context including:
- Package naming rationale (dsconv vs 3dsconv)
- Encryption type handling
- CIA structure building
- Context Portal system (for AI agents)

## Getting Help

1. **Check agents.md first** - Contains complete project context
2. **Review Test-Automation-Plan.md** - For testing questions
3. **Read existing code** - Many answers in comments
4. **Check git history** - Recent commits show patterns

---

**Last Updated:** 2025-11-07  
**For:** GitHub Copilot, Claude Code, Cursor, and other AI coding assistants  
**Maintained By:** Project contributors
